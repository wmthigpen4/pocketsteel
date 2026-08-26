#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const analyzer = require(
  path.resolve(__dirname, "../ui/practice-analysis-worker.js"),
);
const repoRoot = path.resolve(__dirname, "..");

function argumentsFrom(argv) {
  const proofIndex = argv.indexOf("--proof");
  if (proofIndex < 0 || !argv[proofIndex + 1])
    throw new Error("--proof is required.");
  return { proof: path.resolve(argv[proofIndex + 1]) };
}

function decode(file) {
  const result = spawnSync(
    "ffmpeg",
    [
      "-v",
      "error",
      "-i",
      file,
      "-ac",
      "1",
      "-ar",
      "11025",
      "-f",
      "f32le",
      "pipe:1",
    ],
    { encoding: null, maxBuffer: 256 * 1024 * 1024 },
  );
  if (result.status !== 0)
    throw new Error(`FFmpeg could not decode ${path.basename(file)}.`);
  const raw = result.stdout.buffer.slice(
    result.stdout.byteOffset,
    result.stdout.byteOffset + result.stdout.byteLength,
  );
  const samples = new Float32Array(raw);
  return { samples, durationMs: Math.round((samples.length / 11025) * 1000) };
}

function roundSeconds(milliseconds) {
  return Math.round(Number(milliseconds) * 1000) / 1_000_000;
}

function reviewTempo(tempo) {
  let candidate = Number(tempo);
  while (candidate > 180) candidate /= 2;
  while (candidate < 70) candidate *= 2;
  return Math.round(candidate * 10) / 10;
}

function main() {
  const options = argumentsFrom(process.argv.slice(2));
  const proof = JSON.parse(fs.readFileSync(options.proof, "utf8"));
  proof.tracks.forEach((item, index) => {
    const audioPath = path.join(
      repoRoot,
      item.track.audioUrl.replace(/^\//u, ""),
    );
    process.stderr.write(
      `[${index + 1}/${proof.tracks.length}] ${item.track.title}\n`,
    );
    const decoded = decode(audioPath);
    const detected = analyzer.rhythmAnalysis(
      decoded.samples,
      11025,
      decoded.durationMs,
      {},
    );
    const tempoHint = reviewTempo(detected.tempo);
    const rhythm = analyzer.rhythmAnalysis(
      decoded.samples,
      11025,
      decoded.durationMs,
      { meter: "4/4", tempo: tempoHint, tempoHint },
    );
    item.track.rhythm = {
      tempoBpm: rhythm.tempo,
      tempoConfidence: rhythm.tempoConfidence,
      meter: rhythm.meter,
      meterConfidence: rhythm.meterConfidence,
      beatsPerBar: rhythm.beatsPerBar,
      beatTimesSeconds: rhythm.beatTimesMs.map(roundSeconds),
      barStartsSeconds: rhythm.barStartsMs.map(roundSeconds),
      alternatives: rhythm.rhythmAlternatives,
      detectedTempoBpm: detected.tempo,
      detectedMeter: detected.meter,
      detectedMeterConfidence: detected.meterConfidence,
      meterSource: "pilot-provisional-4-4",
      source: "practice-analysis-v2",
    };
  });
  const temporary = `${options.proof}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(proof, null, 2)}\n`);
  fs.renameSync(temporary, options.proof);
  process.stdout.write(
    `${JSON.stringify({ trackCount: proof.tracks.length, proof: options.proof })}\n`,
  );
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
