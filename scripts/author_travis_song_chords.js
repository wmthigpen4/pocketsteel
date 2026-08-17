#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const analyzer = require(path.resolve(__dirname, "../ui/practice-analysis-worker.js"));
const songAuthoring = require(path.resolve(__dirname, "lib/song_chart_authoring.js"));
const NOTE_VALUES = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };
const MAJOR_DEGREES = ["I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII"];

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--") || index + 1 >= argv.length) throw new Error(`Expected a value after ${token}.`);
    args[token.slice(2)] = argv[index + 1];
    index += 1;
  }
  for (const required of ["audio", "companion", "output", "revision"]) {
    if (!args[required]) throw new Error(`Missing --${required}.`);
  }
  return args;
}

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function lowerRoman(value) {
  return value.replace(/[IV]+/g, (match) => match.toLowerCase());
}

function nnsForSymbol(symbol, key) {
  if (symbol === "N.C." || symbol === "—") return symbol;
  const match = String(symbol).match(/^([A-G](?:#|b)?)(.*)$/);
  if (!match || NOTE_VALUES[match[1]] === undefined || NOTE_VALUES[key] === undefined) {
    throw new Error(`Cannot derive NNS for ${symbol} in ${key}.`);
  }
  const offset = (NOTE_VALUES[match[1]] - NOTE_VALUES[key] + 12) % 12;
  const quality = match[2];
  const minorQuality = quality.startsWith("m") && !quality.startsWith("maj");
  const degree = minorQuality ? lowerRoman(MAJOR_DEGREES[offset]) : MAJOR_DEGREES[offset];
  if (quality === "m") return degree;
  if (quality === "m7") return `${degree}7`;
  return `${degree}${quality}`;
}

function barAt(barStartsMs, timeMs) {
  let bar = 1;
  for (let index = 0; index < barStartsMs.length; index += 1) {
    if (Number(barStartsMs[index]) > timeMs) break;
    bar = index + 1;
  }
  return bar;
}

function sectionForTime(sections, timeMs) {
  return sections.find((section) => timeMs >= Number(section.startMs) && timeMs < Number(section.endMs))
    || sections.at(-1)
    || null;
}

function detectedSegments(analysis, companion, sections = []) {
  const durationMs = Number(companion.media.scopes.fullSong.durationMs);
  const key = companion.display.key;
  return analysis.chords.map((chord, index, chords) => {
    const startMs = index === 0 ? 0 : Number(chord.startMs);
    const section = sectionForTime(sections, startMs);
    const claim = songAuthoring.learnerClaimForAnalysisChord(chord);
    const symbol = claim.symbol || "—";
    return {
      id: `detected-${chord.id}`,
      analysisEventId: chord.id,
      startMs,
      endMs: index + 1 < chords.length ? Number(chords[index + 1].startMs) : durationMs,
      barStart: Number(chord.bar),
      barEnd: Number(chord.bar),
      sectionId: section?.id || null,
      sectionLabel: section?.label || `Measure group ${Math.ceil(Number(chord.bar) / 8)}`,
      symbol,
      nns: nnsForSymbol(symbol, key),
      verified: false,
      needsAttention: claim.needsAttention,
      confidence: Number(claim.confidence),
      rawCandidate: chord.rawCandidate,
      alternatives: chord.alternatives || [],
      rootStatus: claim.rootStatus,
      qualityStatus: claim.qualityStatus,
      reviewReasons: claim.reviewReasons,
      sourceKind: "local_play_along_audio_reader",
      analysisVersion: Number(analysis.analysisVersion),
      status: claim.symbol
        ? "deterministic_audio_claim_review_required"
        : "deterministic_audio_claim_withheld_pending_review",
    };
  });
}

function taughtSoloSegments(companion, analysis, sections = []) {
  const soloScope = companion.media.scopes.taughtSolo;
  const key = companion.display.key;
  return companion.chordTimeline.map((chord) => {
    const startMs = Number(soloScope.startMs) + Number(chord.startMs);
    const endMs = Number(soloScope.startMs) + Number(chord.endMs);
    const songBar = barAt(analysis.barStartsMs, startMs);
    const section = sectionForTime(sections, startMs);
    return {
      id: `solo-${chord.id}`,
      analysisEventId: null,
      startMs,
      endMs,
      barStart: songBar,
      barEnd: barAt(analysis.barStartsMs, Math.max(startMs, endMs - 1)),
      soloBarStart: Number(chord.barStart),
      soloBarEnd: Number(chord.barEnd),
      sectionId: section?.id || null,
      sectionLabel: section?.label || "Taught solo",
      symbol: chord.symbol,
      nns: chord.nns || nnsForSymbol(chord.symbol, key),
      verified: false,
      needsAttention: true,
      confidence: null,
      rawCandidate: null,
      alternatives: [],
      reviewReasons: ["Uses the current lesson-solo chord event at its exact source-track position."],
      sourceKind: "taught_solo_chord_timeline",
      analysisVersion: Number(analysis.analysisVersion),
      status: "deterministic_lesson_solo_timeline_travis_review_required",
    };
  });
}

function buildSongChordTimeline(analysis, companion, authoredSegments = null, sections = []) {
  const durationMs = Number(companion.media.scopes.fullSong.durationMs);
  const solo = companion.media.scopes.taughtSolo;
  const detected = (authoredSegments || detectedSegments(analysis, companion, sections)).flatMap((segment) => {
    if (segment.endMs <= solo.startMs || segment.startMs >= solo.endMs) return [segment];
    const pieces = [];
    if (segment.startMs < solo.startMs) pieces.push({ ...segment, endMs: Number(solo.startMs) });
    if (segment.endMs > solo.endMs) pieces.push({ ...segment, startMs: Number(solo.endMs) });
    return pieces;
  });
  const timeline = detected.concat(taughtSoloSegments(companion, analysis, sections))
    .sort((left, right) => left.startMs - right.startMs || left.endMs - right.endMs);
  timeline.forEach((segment, index) => {
    segment.id = `song-chord-${String(index + 1).padStart(3, "0")}`;
    segment.startMs = index === 0 ? 0 : timeline[index - 1].endMs;
    segment.endMs = index + 1 < timeline.length ? timeline[index + 1].startMs : durationMs;
    if (segment.endMs <= segment.startMs) throw new Error(`Invalid full-song segment at index ${index}.`);
  });
  return timeline;
}

function decodeAudio(audioPath, expectedDurationMs) {
  const decoded = spawnSync("ffmpeg", [
    "-v", "error", "-i", audioPath, "-ac", "1", "-ar", "11025", "-f", "f32le", "pipe:1",
  ], { encoding: null, maxBuffer: 64 * 1024 * 1024 });
  if (decoded.status !== 0) throw new Error(`ffmpeg could not decode the backing track: ${String(decoded.stderr || "").trim()}`);
  const raw = decoded.stdout.buffer.slice(decoded.stdout.byteOffset, decoded.stdout.byteOffset + decoded.stdout.byteLength);
  const samples = new Float32Array(raw);
  const durationMs = Math.round(samples.length / 11025 * 1000);
  if (Math.abs(durationMs - expectedDurationMs) > 50) {
    throw new Error(`Decoded duration ${durationMs} ms does not match companion duration ${expectedDurationMs} ms.`);
  }
  return { samples, durationMs };
}

function analyzeSong(audioPath, companion, reference = null) {
  const expectedDurationMs = Number(companion.media.scopes.fullSong.durationMs);
  const decoded = decodeAudio(audioPath, expectedDurationMs);
  const teachingTempo = Number(companion.display.tempoBpm);
  const tempoHint = Number(reference?.tempoBpm || companion.songAnalysis?.tempoHintBpm || teachingTempo);
  const meter = reference?.meter || companion.songAnalysis?.meterHint || companion.display.meter;
  const key = companion.display.key;
  const initial = analyzer.analyzePcm(decoded.samples, 11025, decoded.durationMs, {
    tempoHint,
    meter,
    key,
    keyMode: "major",
  });
  const barCount = initial.analysisState.bars.length;
  return analyzer.redecodeAnalysis(initial, key, "major", [
    { startBar: 1, endBar: barCount, key, keyMode: "major", confidence: 1 },
  ]);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const companion = JSON.parse(fs.readFileSync(args.companion, "utf8"));
  const reference = args.reference ? JSON.parse(fs.readFileSync(args.reference, "utf8")) : null;
  const actualAudioHash = sha256(args.audio);
  if (actualAudioHash !== companion.media.audioSha256) throw new Error("Backing-track hash does not match the companion artifact.");
  if (!companion.media?.scopes?.fullSong || !companion.media?.scopes?.taughtSolo) throw new Error("The companion must define fullSong and taughtSolo media scopes.");
  if (reference) {
    songAuthoring.validateReference(reference);
    songAuthoring.applyScopeChordCorrections(companion, reference, nnsForSymbol);
  }
  const analysis = analyzeSong(args.audio, companion, reference);
  const authored = reference
    ? songAuthoring.alignReferenceChart(reference, companion, nnsForSymbol)
    : { timeline: null, sections: songAuthoring.inferRepeatedSections(analysis), alignment: null };
  const timeline = buildSongChordTimeline(analysis, companion, authored.timeline, authored.sections);
  companion.songChordTimeline = timeline;
  companion.songForm = authored.sections;
  companion.display.fullSongTempoBpm = Number(reference?.tempoBpm || analysis.tempo);
  companion.revision = args.revision;
  companion.contentStatus = "draft_review_required";
  companion.approvals.musical = false;
  companion.approvals.chords = false;
  companion.sourceEvidence.fullSongChordChart = {
    sourceKind: reference ? "aligned_multi_source_chart_reference" : "local_play_along_audio_reader",
    analysisVersion: Number(analysis.analysisVersion),
    keyConstraint: `${companion.display.key} major`,
    meterHint: companion.display.meter,
    teachingTempoBpm: Number(companion.display.tempoBpm),
    referenceTempoBpm: reference ? Number(reference.tempoBpm) : null,
    detectedTempoBpm: Number(analysis.tempo),
    rhythmAlternatives: analysis.analysisState?.rhythmAlternatives || [],
    detectedMeasureGrid: analysis.barStartsMs.length,
    learnerSectionCount: authored.sections.length,
    eventCount: timeline.length,
    attentionCount: timeline.filter((event) => event.needsAttention).length,
    contextRootConflictCount: analysis.chords.filter((event) => event.rootAdjusted).length,
    withheldAudioClaimCount: analysis.chords.filter((event) => !event.publicationSymbol).length,
    publicationMethod: reference
      ? "reviewed_reference_roots_aligned_to_recording_and_exact_lesson_scope"
      : "learner_safe_audio_claims_grouped_into_repeated_forms",
    alignment: authored.alignment,
    sources: reference?.sources || [],
    taughtSoloOverrideStartMs: Number(companion.media.scopes.taughtSolo.startMs),
    taughtSoloOverrideEndMs: Number(companion.media.scopes.taughtSolo.endMs),
    approvalState: "travis_review_required",
  };
  const outputPath = path.resolve(args.output);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const temporaryPath = `${outputPath}.tmp`;
  fs.writeFileSync(temporaryPath, `${JSON.stringify(companion, null, 2)}\n`);
  fs.renameSync(temporaryPath, outputPath);
  process.stdout.write(`${JSON.stringify({
    output: outputPath,
    revision: companion.revision,
    events: timeline.length,
    attention: timeline.filter((event) => event.needsAttention).length,
    tempo: analysis.tempo,
    referenceTempo: reference?.tempoBpm || null,
    meter: analysis.meter,
    key: analysis.key,
    sections: authored.sections.length,
  }, null, 2)}\n`);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

module.exports = { analyzeSong, buildSongChordTimeline, detectedSegments, nnsForSymbol };
