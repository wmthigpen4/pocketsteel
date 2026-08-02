"use strict";

// Everything in this worker is deterministic and local. It deliberately has
// no imports or network primitives: decoded mono PCM enters, musical timing
// estimates leave, and the original recording never leaves the device.
const NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
const MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88];
const MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17];

function progress(stage, detail) { self.postMessage({ type: "progress", stage, detail }); }
function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }

function downsample(input, sampleRate, targetRate = 11025) {
  if (sampleRate <= targetRate) return { samples: input, sampleRate };
  const ratio = sampleRate / targetRate;
  const output = new Float32Array(Math.floor(input.length / ratio));
  for (let i = 0; i < output.length; i += 1) {
    const start = Math.floor(i * ratio);
    const end = Math.max(start + 1, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = start; j < end && j < input.length; j += 1) sum += input[j];
    output[i] = sum / (end - start);
  }
  return { samples: output, sampleRate: targetRate };
}

function onsetEnvelope(samples, sampleRate) {
  const hop = 512;
  const frame = 1024;
  const envelope = [];
  let previous = 0;
  for (let start = 0; start + frame <= samples.length; start += hop) {
    let energy = 0;
    for (let i = 0; i < frame; i += 1) energy += samples[start + i] * samples[start + i];
    energy = Math.sqrt(energy / frame);
    envelope.push(Math.max(0, energy - previous * 0.82));
    previous = energy;
  }
  const mean = envelope.reduce((sum, value) => sum + value, 0) / Math.max(1, envelope.length);
  return { values: envelope.map((value) => Math.max(0, value - mean * 0.45)), hop, sampleRate };
}

function estimateTempo(envelope) {
  const rate = envelope.sampleRate / envelope.hop;
  let best = { bpm: 100, score: -Infinity, lag: Math.round(rate * 0.6) };
  for (let bpm = 50; bpm <= 180; bpm += 1) {
    const lag = Math.round(rate * 60 / bpm);
    let score = 0;
    for (let i = lag; i < envelope.values.length; i += 1) score += envelope.values[i] * envelope.values[i - lag];
    if (score > best.score) best = { bpm, score, lag };
  }
  return best;
}

function strongestBeatOffset(envelope, lag) {
  let bestOffset = 0;
  let best = -Infinity;
  for (let offset = 0; offset < lag; offset += 1) {
    let score = 0;
    for (let index = offset; index < envelope.values.length; index += lag) score += envelope.values[index];
    if (score > best) { best = score; bestOffset = offset; }
  }
  return bestOffset * envelope.hop / envelope.sampleRate;
}

function estimateMeter(envelope, lag, offsetFrame) {
  const patterns = [3, 4, 6];
  let best = { beats: 4, score: -Infinity };
  patterns.forEach((beats) => {
    const accents = Array.from({ length: beats }, () => []);
    for (let index = offsetFrame, beat = 0; index < envelope.values.length; index += lag, beat += 1) accents[beat % beats].push(envelope.values[Math.round(index)] || 0);
    const averages = accents.map((items) => items.reduce((sum, value) => sum + value, 0) / Math.max(1, items.length));
    const score = averages[0] - averages.slice(1).reduce((sum, value) => sum + value, 0) / Math.max(1, beats - 1);
    if (score > best.score) best = { beats, score };
  });
  return best.beats;
}

function fft(real, imag) {
  const n = real.length;
  for (let i = 1, j = 0; i < n; i += 1) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [real[i], real[j]] = [real[j], real[i]]; [imag[i], imag[j]] = [imag[j], imag[i]]; }
  }
  for (let length = 2; length <= n; length <<= 1) {
    const angle = -2 * Math.PI / length;
    for (let start = 0; start < n; start += length) {
      for (let i = 0; i < length / 2; i += 1) {
        const cosine = Math.cos(angle * i), sine = Math.sin(angle * i);
        const even = start + i, odd = even + length / 2;
        const tr = real[odd] * cosine - imag[odd] * sine;
        const ti = real[odd] * sine + imag[odd] * cosine;
        real[odd] = real[even] - tr; imag[odd] = imag[even] - ti;
        real[even] += tr; imag[even] += ti;
      }
    }
  }
}

function chromaAt(samples, sampleRate, centerSecond) {
  const size = 4096;
  const start = clamp(Math.round(centerSecond * sampleRate - size / 2), 0, Math.max(0, samples.length - size));
  const real = new Float64Array(size), imag = new Float64Array(size), chroma = new Float64Array(12);
  for (let i = 0; i < size; i += 1) real[i] = (samples[start + i] || 0) * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (size - 1)));
  fft(real, imag);
  for (let bin = 1; bin < size / 2; bin += 1) {
    const frequency = bin * sampleRate / size;
    if (frequency < 55 || frequency > 1760) continue;
    const midi = Math.round(69 + 12 * Math.log2(frequency / 440));
    const magnitude = Math.hypot(real[bin], imag[bin]);
    chroma[((midi % 12) + 12) % 12] += Math.sqrt(magnitude);
  }
  const total = chroma.reduce((sum, value) => sum + value, 0) || 1;
  return Array.from(chroma, (value) => value / total);
}

function profileScore(chroma, root, profile) {
  let dot = 0, magnitude = 0;
  for (let pc = 0; pc < 12; pc += 1) { const weight = profile[(pc - root + 12) % 12]; dot += chroma[pc] * weight; magnitude += weight * weight; }
  return dot / Math.sqrt(magnitude || 1);
}

function detectChord(chroma) {
  const candidates = [];
  for (let root = 0; root < 12; root += 1) {
    const major = chroma[root] + 0.82 * chroma[(root + 4) % 12] + 0.72 * chroma[(root + 7) % 12] - 0.2 * chroma[(root + 3) % 12];
    const minor = chroma[root] + 0.82 * chroma[(root + 3) % 12] + 0.72 * chroma[(root + 7) % 12] - 0.2 * chroma[(root + 4) % 12];
    candidates.push({ symbol: NOTE_NAMES[root], score: major }, { symbol: `${NOTE_NAMES[root]}m`, score: minor });
  }
  candidates.sort((a, b) => b.score - a.score);
  const confidence = clamp((candidates[0].score - candidates[1].score) * 5 + candidates[0].score, 0, 1);
  return { symbol: candidates[0].symbol, confidence: Number(confidence.toFixed(2)) };
}

function estimateKey(chromas) {
  const average = Array.from({ length: 12 }, (_item, pc) => chromas.reduce((sum, item) => sum + item[pc], 0) / Math.max(1, chromas.length));
  const candidates = [];
  for (let root = 0; root < 12; root += 1) candidates.push({ key: NOTE_NAMES[root], score: profileScore(average, root, MAJOR_PROFILE) }, { key: `${NOTE_NAMES[root]}m`, score: profileScore(average, root, MINOR_PROFILE) });
  candidates.sort((a, b) => b.score - a.score);
  return candidates[0].key;
}

self.onmessage = (event) => {
  if (event.data?.type === "cancel") { self.close(); return; }
  if (event.data?.type !== "analyze") return;
  try {
    const input = new Float32Array(event.data.samples);
    const durationMs = Number(event.data.durationMs);
    progress("Detecting beats, meter, key, and chords", "Listening for the pulse");
    const reduced = downsample(input, Number(event.data.sampleRate));
    const envelope = onsetEnvelope(reduced.samples, reduced.sampleRate);
    const tempoEstimate = estimateTempo(envelope);
    const secondsPerBeat = 60 / tempoEstimate.bpm;
    const firstBeat = strongestBeatOffset(envelope, tempoEstimate.lag);
    const offsetFrame = Math.round(firstBeat * envelope.sampleRate / envelope.hop);
    const beatsPerBar = estimateMeter(envelope, tempoEstimate.lag, offsetFrame);
    const beatTimesMs = [];
    for (let second = firstBeat; second * 1000 < durationMs; second += secondsPerBeat) beatTimesMs.push(Math.round(second * 1000));
    if (!beatTimesMs.length || beatTimesMs[0] > secondsPerBeat * 750) beatTimesMs.unshift(0);
    const barStartsMs = beatTimesMs.filter((_time, index) => index % beatsPerBar === 0);
    if (!barStartsMs.length || barStartsMs[0] !== beatTimesMs[0]) barStartsMs.unshift(beatTimesMs[0] || 0);
    progress("Detecting beats, meter, key, and chords", "Identifying the harmony");
    const chromas = barStartsMs.map((start, index) => {
      const end = Number(barStartsMs[index + 1] ?? durationMs);
      return chromaAt(reduced.samples, reduced.sampleRate, ((start + end) / 2) / 1000);
    });
    const rawChords = chromas.map(detectChord);
    const chords = rawChords.map((chord, index) => {
      const previous = rawChords[index - 1], next = rawChords[index + 1];
      const smoothed = previous && next && previous.symbol === next.symbol && chord.confidence < 0.45 ? { ...chord, symbol: previous.symbol } : chord;
      return { id: `detected-chord-${index + 1}`, bar: index + 1, symbol: smoothed.symbol, startMs: barStartsMs[index], endMs: Number(barStartsMs[index + 1] ?? durationMs), confidence: smoothed.confidence, reviewed: false };
    });
    const key = estimateKey(chromas).replace(/m$/, "");
    progress("Building the steel route", "Preparing editable chord bars");
    self.postMessage({ type: "complete", analysis: { tempo: tempoEstimate.bpm, key, meter: `${beatsPerBar}/${beatsPerBar === 6 ? 8 : 4}`, beatTimesMs, barStartsMs, chords, authoredCountIn: firstBeat > secondsPerBeat * beatsPerBar * 0.7 } });
  } catch (error) {
    self.postMessage({ type: "error", message: error?.message || "The recording could not be analyzed." });
  }
};
