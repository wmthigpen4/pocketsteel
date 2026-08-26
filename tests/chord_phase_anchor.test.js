"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const phaseAnchor = require(
  "../ui/chord-reader-travis-validation/phase-anchor.js",
);

test("backsolves a repeated sustained-change phase", () => {
  const beats = Array.from({ length: 90 }, (_unused, index) => index * 0.5);
  const roots = ["C", "F", "G", "C", "F", "G", "C", "F", "G", "C", "F"];
  const starts = [0, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27];
  const segments = starts.map((start, index) => ({
    start,
    end: starts[index + 1] || 29,
    productLabel: roots[index],
    confidence: 0.91,
  }));
  const result = phaseAnchor.inferPhase(segments, beats, 4);
  assert.equal(result.status, "anchored");
  assert.equal(result.downbeatOffsetBeats, 2);
  assert.equal(result.anchorCount, 10);
});

test("refuses to force a phase when reliable anchors are sparse", () => {
  const beats = Array.from({ length: 40 }, (_unused, index) => index * 0.5);
  const segments = [
    { start: 0, end: 10, productLabel: "C", confidence: 0.9 },
    { start: 10, end: 15, productLabel: "F", confidence: 0.9 },
    { start: 15, end: 20, productLabel: "G", confidence: 0.9 },
  ];
  const result = phaseAnchor.inferPhase(segments, beats, 4);
  assert.equal(result.status, "unresolved");
  assert.equal(result.downbeatOffsetBeats, 0);
  assert.equal(result.anchorCount, 2);
});

test("backfills missing count-in pulses without changing raw phase meaning", () => {
  const completed = phaseAnchor.completeBeatGrid([1.25, 1.75, 2.25], 3);
  assert.equal(completed.prependedCount, 2);
  assert.deepEqual(
    phaseAnchor
      .downbeatTimes(completed.beats, completed.prependedCount, 2, 4)
      .map((value) => Number(value.toFixed(2))),
    [0.25, 2.25],
  );
});
