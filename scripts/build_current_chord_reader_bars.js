#!/usr/bin/env node
"use strict";

// Evaluation-only adapter for the pure bar-building behavior frozen in the
// Travis validation UI. Input and output are JSON on stdin/stdout so the
// development scorer can retain the repository's canonical Python chord
// normalization while executing phase-anchor.js directly.

const fs = require("fs");
const phaseAnchor = require(
  "../ui/chord-reader-travis-validation/phase-anchor.js",
);

function chordSymbol(segment) {
  return String(segment?.productLabel || segment?.label || "N.C.").trim();
}

function barConfidence(segments, sourceIndices, start, end) {
  let weighted = 0;
  let duration = 0;
  sourceIndices.forEach((index) => {
    const segment = segments[index];
    const overlap = Math.max(
      0,
      Math.min(end, Number(segment.end)) -
        Math.max(start, Number(segment.start)),
    );
    weighted += Number(segment.confidence) * overlap;
    duration += overlap;
  });
  return duration ? weighted / duration : 0;
}

function strongestChordInWindow(segments, sourceIndices, start, end) {
  const bySymbol = new Map();
  sourceIndices.forEach((index) => {
    const segment = segments[index];
    const overlap = Math.max(
      0,
      Math.min(end, Number(segment.end)) -
        Math.max(start, Number(segment.start)),
    );
    if (!overlap) return;
    const symbol = chordSymbol(segment);
    const current = bySymbol.get(symbol) || {
      symbol,
      overlap: 0,
      weightedConfidence: 0,
    };
    current.overlap += overlap;
    current.weightedConfidence += overlap * Number(segment.confidence);
    bySymbol.set(symbol, current);
  });
  const winner = [...bySymbol.values()].sort(
    (left, right) =>
      right.weightedConfidence - left.weightedConfidence ||
      right.overlap - left.overlap,
  )[0];
  if (!winner) return null;
  return {
    ...winner,
    confidence: winner.weightedConfidence / winner.overlap,
    coverage: winner.overlap / Math.max(0.001, end - start),
  };
}

function chordDecisionForBar(segments, sourceIndices, start, end) {
  const midpoint = start + (end - start) / 2;
  const full = strongestChordInWindow(segments, sourceIndices, start, end);
  const first = strongestChordInWindow(
    segments,
    sourceIndices,
    start,
    midpoint,
  );
  const second = strongestChordInWindow(
    segments,
    sourceIndices,
    midpoint,
    end,
  );
  const supportedSplit =
    first &&
    second &&
    first.symbol !== second.symbol &&
    first.coverage >= 0.6 &&
    second.coverage >= 0.6 &&
    first.confidence >= 0.64 &&
    second.confidence >= 0.64;
  const possibleSplit =
    first &&
    second &&
    first.symbol !== second.symbol &&
    first.coverage >= 0.6 &&
    second.coverage >= 0.6 &&
    Math.max(first.confidence, second.confidence) >= 0.55 &&
    Math.min(first.confidence, second.confidence) >= 0.2;
  const rawSymbols = new Set(
    sourceIndices.map((index) => chordSymbol(segments[index])),
  );
  const chordSymbols = possibleSplit
    ? [first.symbol, second.symbol]
    : [full?.symbol || "N.C."];
  return {
    chordSymbols,
    splitSupported: Boolean(supportedSplit),
    splitUncertain: Boolean(possibleSplit && !supportedSplit),
    aggregationUnstable: rawSymbols.size > chordSymbols.length,
  };
}

function segmentIndexAt(segments, time) {
  const exact = segments.findIndex(
    (segment) => Number(segment.start) <= time && Number(segment.end) > time,
  );
  if (exact >= 0) return exact;
  let best = 0;
  let distance = Infinity;
  segments.forEach((segment, index) => {
    const candidate = Math.min(
      Math.abs(Number(segment.start) - time),
      Math.abs(Number(segment.end) - time),
    );
    if (candidate < distance) {
      best = index;
      distance = candidate;
    }
  });
  return best;
}

function buildBars(track, requestedPhase) {
  const segments = track.segments;
  const completed = phaseAnchor.completeBeatGrid(
    track.beatTimesSeconds,
    track.durationSeconds,
  );
  const beats = completed.beats;
  const downbeats = phaseAnchor.downbeatTimes(
    beats,
    completed.prependedCount,
    requestedPhase,
    track.beatsPerBar,
  );
  if (!downbeats.length) return [];
  const meaningful = segments.find((segment) => {
    const duration = Number(segment.end) - Number(segment.start);
    return (
      !/^(N\.?C\.?|N)$/iu.test(chordSymbol(segment)) &&
      duration >= Math.max(0.35, completed.period * 0.5) &&
      Number(segment.confidence) >= 0.2
    );
  });
  const musicStart = Number(meaningful?.start || 0);
  const firstBarStart =
    downbeats.find(
      (time) => time >= musicStart - completed.period * 0.25,
    ) || downbeats[0];
  const barStarts = downbeats.filter((time) => time >= firstBarStart - 0.001);
  return barStarts.flatMap((start, barIndex) => {
    const end = Math.min(
      Number(track.durationSeconds),
      barStarts[barIndex + 1] || Number(track.durationSeconds),
    );
    if (end - start < 0.2) return [];
    const sourceIndices = segments
      .map((_segment, index) => index)
      .filter(
        (index) =>
          Number(segments[index].end) > start &&
          Number(segments[index].start) < end,
      );
    if (!sourceIndices.length)
      sourceIndices.push(segmentIndexAt(segments, start));
    return [
      {
        start,
        end,
        confidence: barConfidence(segments, sourceIndices, start, end),
        ...chordDecisionForBar(segments, sourceIndices, start, end),
      },
    ];
  });
}

function main() {
  const input = JSON.parse(fs.readFileSync(0, "utf8"));
  const tracks = input.tracks.map((track) => {
    const inferred = phaseAnchor.inferPhase(
      track.segments,
      track.beatTimesSeconds,
      track.beatsPerBar,
    );
    const appliedPhase =
      inferred.status === "anchored" ? inferred.downbeatOffsetBeats : 0;
    return {
      id: track.id,
      phase: inferred,
      appliedPhase,
      baselineBars: buildBars(track, 0),
      currentBars: buildBars(track, appliedPhase),
    };
  });
  process.stdout.write(`${JSON.stringify({ tracks })}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
}
