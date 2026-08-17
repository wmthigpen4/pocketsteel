#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const analyzer = require(path.resolve(__dirname, "../ui/practice-analysis-worker.js"));
const authoring = require(path.resolve(__dirname, "lib/song_chart_authoring.js"));

function args(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 2) {
    if (!argv[index]?.startsWith("--") || argv[index + 1] === undefined) throw new Error("Expected --name value arguments.");
    values[argv[index].slice(2)] = argv[index + 1];
  }
  if (!values.audio) throw new Error("--audio is required.");
  return values;
}

function decode(file) {
  const result = spawnSync("ffmpeg", ["-v", "error", "-i", file, "-ac", "1", "-ar", "11025", "-f", "f32le", "pipe:1"], {
    encoding: null,
    maxBuffer: 256 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error("FFmpeg could not decode the primary backing track.");
  const raw = result.stdout.buffer.slice(result.stdout.byteOffset, result.stdout.byteOffset + result.stdout.byteLength);
  const samples = new Float32Array(raw);
  return { samples, durationMs: Math.round(samples.length / 11025 * 1000) };
}

function main() {
  const options = args(process.argv.slice(2));
  const decoded = decode(path.resolve(options.audio));
  const initial = analyzer.analyzePcm(decoded.samples, 11025, decoded.durationMs, {
    key: options.key || "D",
    keyMode: "major",
    meter: options.meter || "4/4",
  });
  const analysis = analyzer.redecodeAnalysis(initial, options.key || "D", "major", [{
    startBar: 1,
    endBar: Math.max(1, initial.analysisState.bars.length),
    key: options.key || "D",
    keyMode: "major",
    confidence: 1,
  }]);
  const chords = analysis.chords.length ? analysis.chords : [{ id: "unresolved", startMs: 0, confidence: 0 }];
  const chordTimeline = chords.map((chord, index) => {
    const claim = authoring.learnerClaimForAnalysisChord(chord);
    return {
      id: `chord-${String(index + 1).padStart(3, "0")}`,
      startMs: index === 0 ? 0 : Math.max(0, Math.round(Number(chord.startMs))),
      endMs: index + 1 < chords.length ? Math.max(1, Math.round(Number(chords[index + 1].startMs))) : decoded.durationMs,
      symbol: claim.symbol,
      nns: null,
      sectionLabel: `Bars ${Number(chord.bar || index + 1)}`,
      reviewStatus: claim.needsAttention ? "uncertain" : "generated_unconfirmed",
      confidence: claim.confidence,
      alternatives: chord.alternatives || [],
      provenance: "local_play_along_audio_reader",
    };
  });
  chordTimeline.forEach((chord, index) => {
    chord.startMs = index === 0 ? 0 : chordTimeline[index - 1].endMs;
    chord.endMs = index + 1 < chordTimeline.length ? Math.max(chord.startMs + 1, chordTimeline[index + 1].startMs) : decoded.durationMs;
  });
  process.stdout.write(JSON.stringify({
    schemaVersion: "travis_backing_track_analysis_v1",
    durationMs: decoded.durationMs,
    tempoBpm: analysis.tempo,
    meter: analysis.meter,
    key: analysis.key,
    analysisVersion: Number(analysis.analysisVersion),
    chordTimeline,
  }));
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
