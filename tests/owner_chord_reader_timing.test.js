const test = require("node:test");
const assert = require("node:assert/strict");
const timing = require("../ui/chord-reader-owner-test/timing.js");

test("unresolved phase uses exact model transitions instead of bar aggregation", () => {
  const track = {
    rhythm: { phase: { status: "unresolved" } },
    segments: [
      { start: 0.4, end: 18, productLabel: "G#", confidence: 0.87 },
      { start: 18, end: 19.4, productLabel: "C#", confidence: 0.9 },
    ],
    bars: [
      { bar: 7, start: 17.345, end: 19.968, chordSymbols: ["C#"] },
    ],
  };

  const result = timing.itemsForTrack(track);
  assert.equal(result.mode, "exact-model-transitions");
  assert.equal(result.items[1].start, 18);
  assert.equal(timing.itemAt(result.items, 17.9).chordSymbols[0], "G#");
  assert.equal(timing.itemAt(result.items, 18).chordSymbols[0], "C#");
});

test("anchored phase keeps the validated bar display and switches split chords at midpoint", () => {
  const track = {
    rhythm: { phase: { status: "anchored" } },
    segments: [{ start: 0, end: 4, productLabel: "G#" }],
    bars: [{ bar: 9, start: 20, end: 24, chordSymbols: ["G#", "Fm"] }],
  };

  const result = timing.itemsForTrack(track);
  assert.equal(result.mode, "beat-aligned-bars");
  assert.equal(timing.chordAt(result.items[0], 21.99), "G#");
  assert.equal(timing.chordAt(result.items[0], 22), "Fm");
});
