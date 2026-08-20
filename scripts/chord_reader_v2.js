#!/usr/bin/env node
"use strict";

// Development adapter: exact current Play Along v2 implementation in,
// normalized benchmark segment contract out. No model or network dependency.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const analyzer = require(path.resolve(__dirname, "../ui/practice-analysis-worker.js"));

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) throw new Error(`Unexpected argument ${key}.`);
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) throw new Error(`${key} needs a value.`);
    values[key.slice(2)] = value;
    index += 1;
  }
  if (!values.audio) throw new Error("--audio is required.");
  return values;
}

function decodeAudio(audioPath) {
  const result = spawnSync(
    "ffmpeg",
    ["-v", "error", "-i", audioPath, "-ac", "1", "-ar", "11025", "-f", "f32le", "pipe:1"],
    { encoding: null, maxBuffer: 512 * 1024 * 1024 },
  );
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`FFmpeg could not decode ${audioPath}.`);
  const bytes = result.stdout;
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const samples = new Float32Array(buffer);
  return { samples, durationMs: samples.length / 11025 * 1000 };
}

function analyzerOptions(values) {
  const options = {};
  if (values.key) options.key = values.key;
  if (values.mode) options.keyMode = values.mode;
  if (values.meter) options.meter = values.meter;
  if (values.tempo) options.tempoHint = Number(values.tempo);
  return options;
}

function normalizedSegments(analysis) {
  const durationSeconds = Number(analysis.durationMs) / 1000;
  const chords = [...(analysis.chords || [])].sort((left, right) => Number(left.startMs) - Number(right.startMs));
  if (!chords.length) return [{ start: 0, end: durationSeconds, label: "N.C.", confidence: 0 }];
  return chords.map((chord, index) => ({
    start: index === 0 ? 0 : Number(chord.startMs) / 1000,
    end: index + 1 < chords.length ? Number(chords[index + 1].startMs) / 1000 : durationSeconds,
    label: chord.symbol || chord.finalSymbol || "N.C.",
    confidence: Number(chord.confidence || 0),
    bar: Number(chord.bar || 0),
    startFraction: Number(chord.startFraction || 0),
  })).filter((segment) => segment.end > segment.start);
}

function main() {
  const values = parseArgs(process.argv.slice(2));
  const audioPath = path.resolve(values.audio);
  if (!fs.statSync(audioPath).isFile()) throw new Error("--audio must point to a file.");
  const decoded = decodeAudio(audioPath);
  const analysis = analyzer.analyzePcm(decoded.samples, 11025, decoded.durationMs, analyzerOptions(values));
  const result = {
    schemaVersion: "chord_prediction_v1",
    id: values.id || path.basename(audioPath),
    engine: "play-along-v2",
    analysisVersion: Number(analysis.analysisVersion),
    durationSeconds: Number(analysis.durationMs) / 1000,
    key: analysis.key,
    keyMode: analysis.keyMode,
    meter: analysis.meter,
    tempo: Number(analysis.tempo),
    beatTimesSeconds: (analysis.beatTimesMs || []).map((value) => Number(value) / 1000),
    barStartsSeconds: (analysis.barStartsMs || []).map((value) => Number(value) / 1000),
    segments: normalizedSegments(analysis),
  };
  const rendered = `${JSON.stringify(result, null, 2)}\n`;
  if (values.output) fs.writeFileSync(path.resolve(values.output), rendered);
  else process.stdout.write(rendered);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : error}\n`);
  process.exitCode = 1;
}
