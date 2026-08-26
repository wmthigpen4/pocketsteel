#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const analyzer = require("../ui/practice-analysis-worker.js");
const phaseAnchor = require(
  "../ui/chord-reader-travis-validation/phase-anchor.js",
);

const repoRoot = path.resolve(__dirname, "..");

function option(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function decode(file) {
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", file, "-ac", "1", "-ar", "11025", "-f", "f32le", "pipe:1"],
    { encoding: null, maxBuffer: 256 * 1024 * 1024 },
  );
  if (result.status !== 0)
    throw new Error(`FFmpeg could not decode ${path.basename(file)}.`);
  const raw = result.stdout.buffer.slice(
    result.stdout.byteOffset,
    result.stdout.byteOffset + result.stdout.byteLength,
  );
  return new Float32Array(raw);
}

function anchorShares(anchors, phase, beatsPerBar) {
  const totals = anchors.reduce(
    (result, anchor) => {
      const position = phaseAnchor.mod(anchor.beatIndex - phase, beatsPerBar);
      result.weight += anchor.weight;
      if (position === 0) result.downbeat += anchor.weight;
      if (position === 0 || position === 2) result.strongBeat += anchor.weight;
      return result;
    },
    { weight: 0, downbeat: 0, strongBeat: 0 },
  );
  return totals;
}

function percent(numerator, denominator) {
  return denominator ? numerator / denominator : 0;
}

function evaluatePilot(proof) {
  const totals = {
    before: { weight: 0, downbeat: 0, strongBeat: 0 },
    after: { weight: 0, downbeat: 0, strongBeat: 0 },
  };
  const songs = proof.tracks.map((item) => {
    const rhythm = item.track.rhythm;
    const beatsPerBar = Number(rhythm.beatsPerBar || 4);
    const offset = Number(rhythm.gridOffsetSeconds || 0);
    const beats = rhythm.beatTimesSeconds.map((time) => Number(time) + offset);
    const inferred = phaseAnchor.inferPhase(
      item.prediction.segments,
      beats,
      beatsPerBar,
    );
    const phase = inferred.status === "anchored" ? inferred.downbeatOffsetBeats : 0;
    const { anchors } = phaseAnchor.collectAnchors(
      item.prediction.segments,
      beats,
    );
    const before = anchorShares(anchors, 0, beatsPerBar);
    const after = anchorShares(anchors, phase, beatsPerBar);
    for (const field of ["weight", "downbeat", "strongBeat"]) {
      totals.before[field] += before[field];
      totals.after[field] += after[field];
    }
    return {
      title: item.track.title,
      status: inferred.status,
      phase,
      anchorCount: inferred.anchorCount,
      margin: inferred.confidence,
      downbeatAnchorShareBefore: percent(before.downbeat, before.weight),
      downbeatAnchorShareAfter: percent(after.downbeat, after.weight),
      strongBeatAnchorShareBefore: percent(before.strongBeat, before.weight),
      strongBeatAnchorShareAfter: percent(after.strongBeat, after.weight),
    };
  });
  return {
    songCount: songs.length,
    anchoredSongs: songs.filter((song) => song.status === "anchored").length,
    unresolvedSongs: songs.filter((song) => song.status === "unresolved").length,
    shiftedSongs: songs.filter((song) => song.status === "anchored" && song.phase !== 0).length,
    weightedDownbeatAnchorShareBefore: percent(
      totals.before.downbeat,
      totals.before.weight,
    ),
    weightedDownbeatAnchorShareAfter: percent(
      totals.after.downbeat,
      totals.after.weight,
    ),
    weightedStrongBeatAnchorShareBefore: percent(
      totals.before.strongBeat,
      totals.before.weight,
    ),
    weightedStrongBeatAnchorShareAfter: percent(
      totals.after.strongBeat,
      totals.after.weight,
    ),
    songs,
  };
}

function nearestErrors(predicted, reference) {
  return reference.map((target) =>
    Math.min(...predicted.map((candidate) => Math.abs(candidate - target))),
  );
}

function summarizeErrors(errors) {
  const ordered = [...errors].sort((left, right) => left - right);
  const middle = Math.floor(ordered.length / 2);
  return {
    referenceBars: errors.length,
    within250ms: errors.filter((error) => error <= 0.25).length,
    within250msRate: percent(
      errors.filter((error) => error <= 0.25).length,
      errors.length,
    ),
    medianAbsoluteErrorMs: Math.round((ordered[middle] || 0) * 1000),
  };
}

function evaluatePublicTiming(publicProof, manifest) {
  const proofById = new Map(
    publicProof.tracks.map((item) => [item.track.id, item]),
  );
  const tracks = manifest.tracks.map((reference) => {
    process.stderr.write(`Timing check: ${reference.title}\n`);
    const proofTrack = proofById.get(reference.id);
    const samples = decode(path.join(repoRoot, reference.audioPath));
    const beatsPerBar = Number(reference.meter.split("/")[0]);
    const tempo =
      Number(reference.tempo) ||
      (60_000 * beatsPerBar) /
        (Number(reference.barStartsMs[1]) - Number(reference.barStartsMs[0]));
    const rhythm = analyzer.rhythmAnalysis(
      samples,
      11025,
      Math.round((samples.length / 11025) * 1000),
      { meter: reference.meter, tempo, tempoHint: tempo },
    );
    const beats = rhythm.beatTimesMs.map((time) => Number(time) / 1000);
    const inferred = phaseAnchor.inferPhase(
      proofTrack.engines.hybrid.segments,
      beats,
      beatsPerBar,
    );
    const completed = phaseAnchor.completeBeatGrid(
      beats,
      Number(proofTrack.track.durationSeconds),
    );
    const baselineDownbeats = phaseAnchor.downbeatTimes(
      completed.beats,
      completed.prependedCount,
      0,
      beatsPerBar,
    );
    const appliedPhase =
      inferred.status === "anchored" ? inferred.downbeatOffsetBeats : 0;
    const anchoredDownbeats = phaseAnchor.downbeatTimes(
      completed.beats,
      completed.prependedCount,
      appliedPhase,
      beatsPerBar,
    );
    const referenceDownbeats = reference.barStartsMs.map(
      (time) => Number(time) / 1000,
    );
    return {
      title: reference.title,
      status: inferred.status,
      phase: appliedPhase,
      anchorCount: inferred.anchorCount,
      before: summarizeErrors(nearestErrors(baselineDownbeats, referenceDownbeats)),
      after: summarizeErrors(nearestErrors(anchoredDownbeats, referenceDownbeats)),
    };
  });
  const beforeBars = tracks.reduce((sum, track) => sum + track.before.referenceBars, 0);
  const afterBars = tracks.reduce((sum, track) => sum + track.after.referenceBars, 0);
  const beforeHits = tracks.reduce((sum, track) => sum + track.before.within250ms, 0);
  const afterHits = tracks.reduce((sum, track) => sum + track.after.within250ms, 0);
  return {
    trackCount: tracks.length,
    before: {
      referenceBars: beforeBars,
      within250ms: beforeHits,
      within250msRate: percent(beforeHits, beforeBars),
    },
    after: {
      referenceBars: afterBars,
      within250ms: afterHits,
      within250msRate: percent(afterHits, afterBars),
    },
    tracks,
  };
}

function main() {
  const pilotPath = path.resolve(
    option("--pilot-proof", "ui/chord-reader-travis-validation/local-data/proof.json"),
  );
  const publicPath = path.resolve(
    option("--public-proof", "ui/chord-reader-proof/data/proof.json"),
  );
  const manifestPath = path.resolve(
    option("--manifest", "steel_guitar_rag/resources/song_practice_tracks/manifest.json"),
  );
  const report = {
    schemaVersion: "chord_reader_phase_alignment_evaluation_v1",
    thresholdsFixedBeforeEvaluation: {
      minimumAnchors: 8,
      minimumPhaseMargin: 0.12,
      groundTruthToleranceMs: 250,
    },
    chordLabelAccuracy: {
      changedByThisRun: false,
      heldOutFullCoverageAccuracy: 0.79936,
      selectivePrecision: 0.99597,
      selectiveCoverage: 0.39807,
      reason: "This run changes bar phase and reviewer controls, not chord labels.",
    },
    pilotProxy: evaluatePilot(JSON.parse(fs.readFileSync(pilotPath, "utf8"))),
    publicHandAuthoredTiming: evaluatePublicTiming(
      JSON.parse(fs.readFileSync(publicPath, "utf8")),
      JSON.parse(fs.readFileSync(manifestPath, "utf8")),
    ),
  };
  const output = option("--output", null);
  if (output) fs.writeFileSync(path.resolve(output), `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
}
