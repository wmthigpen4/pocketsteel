"use strict";

// Deterministic, dependency-free, on-device chord analysis. Decoded mono PCM
// enters this worker; musical timing and harmony metadata leave it. There are
// deliberately no imports or network primitives in this file.
(function analysisModule(global) {
  const ANALYSIS_VERSION = 2;
  const NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
  const MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88];
  const MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17];
  const QUALITY_INTERVALS = {
    major: [[0, 1], [4, 0.88], [7, 0.72]],
    minor: [[0, 1], [3, 0.88], [7, 0.72]],
    "7": [[0, 1], [4, 0.82], [7, 0.64], [10, 0.76]],
    m7: [[0, 1], [3, 0.82], [7, 0.64], [10, 0.76]]
  };
  const QUALITY_CALIBRATION_VERSION = 7;
  const MIN_EXTENSION_GAIN = 0.09;
  const MIN_SEVENTH_CORE_RATIO = 0.8;
  const MIN_KEY_REGION_BARS = 6;
  const METER_OPTIONS = [
    { meter: "2/4", beats: 2 },
    { meter: "3/4", beats: 3 },
    { meter: "4/4", beats: 4 },
    { meter: "6/8", beats: 6 }
  ];

  function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }
  function round(value, places = 3) { const scale = 10 ** places; return Math.round(value * scale) / scale; }
  function mean(values) { return values.reduce((sum, value) => sum + Number(value || 0), 0) / Math.max(1, values.length); }
  function median(values) {
    if (!values.length) return 0;
    const sorted = [...values].sort((left, right) => left - right);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }
  function normalize(values) {
    const sum = values.reduce((total, value) => total + Math.max(0, value), 0) || 1;
    return values.map((value) => Math.max(0, value) / sum);
  }
  function cosine(left, right) {
    let dot = 0, leftSize = 0, rightSize = 0;
    for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
      dot += left[index] * right[index]; leftSize += left[index] ** 2; rightSize += right[index] ** 2;
    }
    return dot / Math.sqrt(Math.max(1e-12, leftSize * rightSize));
  }
  function medianChroma(items) {
    if (!items.length) return Array(12).fill(1 / 12);
    return normalize(Array.from({ length: 12 }, (_item, pc) => median(items.map((entry) => entry.chroma[pc]))));
  }

  function downsample(input, sampleRate, targetRate = 11025) {
    if (sampleRate <= targetRate) return { samples: input, sampleRate };
    const ratio = sampleRate / targetRate;
    const output = new Float32Array(Math.floor(input.length / ratio));
    for (let index = 0; index < output.length; index += 1) {
      const start = Math.floor(index * ratio);
      const end = Math.max(start + 1, Math.floor((index + 1) * ratio));
      let sum = 0;
      for (let source = start; source < end && source < input.length; source += 1) sum += input[source];
      output[index] = sum / Math.max(1, end - start);
    }
    return { samples: output, sampleRate: targetRate };
  }

  function onsetEnvelope(samples, sampleRate) {
    const hop = 256;
    const frame = 1024;
    const values = [];
    let previousEnergy = 0;
    for (let start = 0; start + frame <= samples.length; start += hop) {
      let energy = 0, difference = 0;
      for (let index = 0; index < frame; index += 1) {
        const value = samples[start + index];
        energy += value * value;
        if (index) difference += Math.abs(value - samples[start + index - 1]);
      }
      energy = Math.sqrt(energy / frame);
      const novelty = Math.max(0, energy - previousEnergy * 0.78) + 0.08 * difference / frame;
      values.push(novelty);
      previousEnergy = energy;
    }
    const baseline = median(values);
    const centered = values.map((value) => Math.max(0, value - baseline * 0.55));
    const peak = Math.max(...centered, 1e-9);
    return { values: centered.map((value) => value / peak), hop, sampleRate };
  }

  function tempoCandidates(envelope, preferredBpms = []) {
    const rate = envelope.sampleRate / envelope.hop;
    const values = envelope.values;
    const candidates = [];
    for (let bpm = 45; bpm <= 210; bpm += 1) {
      const lag = Math.max(2, Math.round(rate * 60 / bpm));
      let correlation = 0, norm = 0;
      for (let index = lag; index < values.length; index += 1) {
        correlation += values[index] * values[index - lag];
        norm += values[index] ** 2 + values[index - lag] ** 2;
      }
      let score = norm ? (2 * correlation / norm) : 0;
      const halfLag = Math.round(lag / 2);
      if (halfLag >= 2) {
        let subdivision = 0;
        for (let index = halfLag; index < values.length; index += 1) subdivision += values[index] * values[index - halfLag];
        score += 0.08 * subdivision / Math.max(1, values.length - halfLag);
      }
      candidates.push({ bpm, lag, score });
    }
    candidates.sort((left, right) => right.score - left.score);
    const distinct = [];
    for (const candidate of candidates) {
      if (distinct.every((item) => Math.abs(item.bpm - candidate.bpm) > 3)) distinct.push(candidate);
      if (distinct.length >= 8) break;
    }
    const best = distinct[0] || { bpm: 100, score: 0 };
    for (const multiplier of [0.5, 2]) {
      const bpm = Math.round(best.bpm * multiplier);
      if (bpm >= 45 && bpm <= 210 && distinct.every((item) => Math.abs(item.bpm - bpm) > 3)) {
        const nearest = candidates.reduce((picked, item) => Math.abs(item.bpm - bpm) < Math.abs(picked.bpm - bpm) ? item : picked, candidates[0]);
        distinct.push(nearest);
      }
    }
    preferredBpms.filter((bpm) => Number.isFinite(bpm) && bpm >= 45 && bpm <= 210).forEach((bpm) => {
      const nearest = candidates.reduce((picked, item) => Math.abs(item.bpm - bpm) < Math.abs(picked.bpm - bpm) ? item : picked, candidates[0]);
      if (nearest && distinct.every((item) => Math.abs(item.bpm - nearest.bpm) > 3)) distinct.push(nearest);
    });
    return distinct.sort((left, right) => right.score - left.score);
  }

  function pulsePhase(envelope, lag) {
    let best = { offset: 0, score: -Infinity };
    for (let offset = 0; offset < lag; offset += 1) {
      let score = 0, count = 0;
      for (let index = offset; index < envelope.values.length; index += lag) {
        score += envelope.values[index] || 0;
        count += 1;
      }
      score /= Math.max(1, count);
      if (score > best.score) best = { offset, score };
    }
    return best;
  }

  function trackDynamicBeats(envelope, candidate, durationMs) {
    const phase = pulsePhase(envelope, candidate.lag);
    const values = envelope.values;
    const nominal = candidate.lag;
    const frames = [];
    let predicted = phase.offset;
    let interval = nominal;
    while (predicted * envelope.hop / envelope.sampleRate * 1000 < durationMs && frames.length < 10000) {
      const radius = Math.max(1, Math.round(interval * 0.24));
      const low = Math.max(0, Math.round(predicted - radius));
      const high = Math.min(values.length - 1, Math.round(predicted + radius));
      let peakIndex = Math.round(predicted), peakValue = -Infinity;
      for (let index = low; index <= high; index += 1) {
        const closeness = 1 - Math.abs(index - predicted) / Math.max(1, radius);
        const score = (values[index] || 0) + 0.15 * closeness;
        if (score > peakValue) { peakValue = score; peakIndex = index; }
      }
      const tracked = frames.length ? Math.round(predicted * 0.42 + peakIndex * 0.58) : peakIndex;
      if (!frames.length || tracked > frames.at(-1)) frames.push(tracked);
      if (frames.length > 1) {
        const observed = frames.at(-1) - frames.at(-2);
        interval = clamp(interval * 0.82 + observed * 0.18, nominal * 0.78, nominal * 1.22);
      }
      predicted = tracked + interval;
    }
    const timesMs = frames.map((frame) => Math.round(frame * envelope.hop / envelope.sampleRate * 1000)).filter((time) => time < durationMs);
    return { ...candidate, phaseScore: phase.score, timesMs };
  }

  function fft(real, imag) {
    const size = real.length;
    for (let index = 1, swap = 0; index < size; index += 1) {
      let bit = size >> 1;
      for (; swap & bit; bit >>= 1) swap ^= bit;
      swap ^= bit;
      if (index < swap) { [real[index], real[swap]] = [real[swap], real[index]]; [imag[index], imag[swap]] = [imag[swap], imag[index]]; }
    }
    for (let length = 2; length <= size; length <<= 1) {
      const angle = -2 * Math.PI / length;
      for (let start = 0; start < size; start += length) {
        for (let index = 0; index < length / 2; index += 1) {
          const cosineValue = Math.cos(angle * index), sineValue = Math.sin(angle * index);
          const even = start + index, odd = even + length / 2;
          const realOdd = real[odd] * cosineValue - imag[odd] * sineValue;
          const imagOdd = real[odd] * sineValue + imag[odd] * cosineValue;
          real[odd] = real[even] - realOdd; imag[odd] = imag[even] - imagOdd;
          real[even] += realOdd; imag[even] += imagOdd;
        }
      }
    }
  }

  function spectralFrame(samples, sampleRate, centerSecond, tuningSemitones = 0) {
    const size = 4096;
    const start = clamp(Math.round(centerSecond * sampleRate - size / 2), 0, Math.max(0, samples.length - size));
    const real = new Float64Array(size), imag = new Float64Array(size), chroma = new Float64Array(12);
    let energy = 0;
    for (let index = 0; index < size; index += 1) {
      const sample = samples[start + index] || 0;
      energy += sample * sample;
      real[index] = sample * (0.5 - 0.5 * Math.cos(2 * Math.PI * index / (size - 1)));
    }
    fft(real, imag);
    for (let bin = 1; bin < size / 2; bin += 1) {
      const frequency = bin * sampleRate / size;
      if (frequency < 55 || frequency > 1760) continue;
      const midi = 69 + 12 * Math.log2(frequency / 440) - tuningSemitones;
      const lower = Math.floor(midi);
      const fraction = midi - lower;
      // Favor fundamentals and low chord tones over the dense upper harmonics
      // of vocals, organ, cymbals, and distorted guitars.
      const magnitude = Math.sqrt(Math.hypot(real[bin], imag[bin])) * clamp(220 / frequency, 0.22, 3);
      chroma[((lower % 12) + 12) % 12] += magnitude * (1 - fraction);
      chroma[(((lower + 1) % 12) + 12) % 12] += magnitude * fraction;
    }
    return { chroma: normalize(Array.from(chroma)), energy: Math.sqrt(energy / size) };
  }

  function estimateTuning(samples, sampleRate, durationMs) {
    const size = 4096;
    let sine = 0, cosineValue = 0, weightTotal = 0;
    const frameCount = clamp(Math.round(durationMs / 4000), 8, 48);
    for (let frame = 0; frame < frameCount; frame += 1) {
      const center = ((frame + 0.5) / frameCount) * durationMs / 1000;
      const start = clamp(Math.round(center * sampleRate - size / 2), 0, Math.max(0, samples.length - size));
      const real = new Float64Array(size), imag = new Float64Array(size);
      for (let index = 0; index < size; index += 1) real[index] = (samples[start + index] || 0) * (0.5 - 0.5 * Math.cos(2 * Math.PI * index / (size - 1)));
      fft(real, imag);
      for (let bin = 1; bin < size / 2; bin += 1) {
        const frequency = bin * sampleRate / size;
        if (frequency < 82 || frequency > 1320) continue;
        const midi = 69 + 12 * Math.log2(frequency / 440);
        const residual = midi - Math.round(midi);
        const weight = Math.hypot(real[bin], imag[bin]);
        const angle = residual * 2 * Math.PI;
        sine += Math.sin(angle) * weight;
        cosineValue += Math.cos(angle) * weight;
        weightTotal += weight;
      }
    }
    if (!weightTotal) return 0;
    return clamp(Math.atan2(sine, cosineValue) / (2 * Math.PI), -0.5, 0.5);
  }

  function beatChromas(samples, sampleRate, beatTimesMs, durationMs, tuningSemitones, frameFractions = [0.5]) {
    const fallbackBeatMs = beatTimesMs.length > 1 ? median(beatTimesMs.slice(1).map((time, index) => time - beatTimesMs[index])) : 500;
    return beatTimesMs.map((startMs, index) => {
      const endMs = Number(beatTimesMs[index + 1] ?? Math.min(durationMs, startMs + fallbackBeatMs));
      const centers = frameFractions.map((fraction) => (startMs + (endMs - startMs) * fraction) / 1000);
      const frames = centers.map((center) => spectralFrame(samples, sampleRate, center, tuningSemitones));
      return { startMs, endMs, chroma: medianChroma(frames), energy: median(frames.map((frame) => frame.energy)) };
    });
  }

  function profileScore(chroma, root, profile) {
    const rotated = Array.from({ length: 12 }, (_item, pc) => profile[(pc - root + 12) % 12]);
    return cosine(chroma, rotated);
  }

  function estimateKey(chromas, hint = {}) {
    const average = medianChroma(chromas.map((chroma) => ({ chroma })));
    const harmonicSamples = chromas.length > 160
      ? Array.from({ length: 160 }, (_item, index) => chromas[Math.floor(index * chromas.length / 160)])
      : chromas;
    const harmonicEvidence = harmonicSamples.map((chroma) => chordCandidates(chroma).candidates.slice(0, 8));
    const candidates = [];
    for (let root = 0; root < 12; root += 1) {
      for (const mode of ["major", "minor"]) {
        const key = { root, key: NOTE_NAMES[root], keyMode: mode };
        const contextFit = mean(harmonicEvidence.map((evidence) => Math.max(...evidence.map((candidate) => keyPrior(candidate.symbol, key)))));
        const primaryFit = mean(harmonicEvidence.map((evidence) => {
          const parsed = parseSymbol(evidence[0]?.symbol);
          if (parsed.root == null) return 0;
          const interval = degree(parsed.root, key.root);
          const quality = parsed.quality === "7" ? "major" : parsed.quality === "m7" ? "minor" : parsed.quality;
          if (mode === "major") return [0, 5, 7].includes(interval) && quality === "major" ? 1 : 0;
          return (interval === 0 || interval === 5) && quality === "minor" || interval === 7 && ["minor", "major"].includes(quality) ? 1 : 0;
        }));
        const hintBonus = hint.key === key.key && (!hint.keyMode || hint.keyMode === mode) ? 0.045 : 0;
        const profile = mode === "major" ? MAJOR_PROFILE : MINOR_PROFILE;
        candidates.push({ root, key: key.key, mode, score: profileScore(average, root, profile) + contextFit * 0.18 + primaryFit * 0.08 + hintBonus + (mode === "major" ? 0.008 : 0) });
      }
    }
    candidates.sort((left, right) => right.score - left.score);
    const best = candidates[0], runnerUp = candidates[1] || best;
    const confidence = clamp(0.35 + (best.score - runnerUp.score) * 5 + (best.score - 0.72) * 1.2, 0.05, 0.99);
    return { key: best.key, keyMode: best.mode, root: best.root, confidence: round(confidence), alternatives: candidates.slice(0, 4).map((item) => ({ key: item.key, mode: item.mode, score: round(item.score) })) };
  }

  function symbolFor(root, quality) {
    if (quality === "major") return NOTE_NAMES[root];
    if (quality === "minor") return `${NOTE_NAMES[root]}m`;
    return `${NOTE_NAMES[root]}${quality}`;
  }

  function parseSymbol(symbol) {
    if (symbol === "N.C.") return { root: null, quality: "none" };
    const match = /^([A-G](?:#|b)?)(m7|m|7)?$/.exec(String(symbol || ""));
    if (!match) return { root: null, quality: "unknown" };
    return { root: NOTE_NAMES.indexOf(match[1]), quality: match[2] === "m" ? "minor" : match[2] || "major" };
  }

  function calibrateExtendedQualities(candidates, chroma = []) {
    const rawScore = (candidate) => Number(candidate?.rawScore ?? candidate?.score ?? -0.4);
    return candidates.map((candidate) => {
      const parsed = parseSymbol(candidate.symbol);
      if (!["7", "m7"].includes(parsed.quality)) return { ...candidate, rawScore: rawScore(candidate) };
      const triadQuality = parsed.quality === "7" ? "major" : "minor";
      const triadSymbol = symbolFor(parsed.root, triadQuality);
      const triad = candidates.find((item) => item.symbol === triadSymbol);
      const extensionGain = rawScore(candidate) - rawScore(triad);
      const third = parsed.quality === "7" ? 4 : 3;
      const coreEvidence = mean([chroma[parsed.root], chroma[(parsed.root + third) % 12], chroma[(parsed.root + 7) % 12]].map(Number));
      const seventhEvidence = Number(chroma[(parsed.root + 10) % 12] || 0);
      const directEvidence = seventhEvidence >= Math.max(0.08, coreEvidence * MIN_SEVENTH_CORE_RATIO);
      const supported = extensionGain >= MIN_EXTENSION_GAIN && directEvidence;
      const score = supported ? rawScore(candidate) : Math.min(rawScore(candidate), rawScore(triad) - 0.05);
      return {
        ...candidate,
        rawScore: rawScore(candidate),
        score: round(score),
        extensionSupported: supported,
        extensionGain: round(extensionGain),
        seventhEvidence: round(seventhEvidence),
        seventhCoreRatio: round(seventhEvidence / Math.max(0.001, coreEvidence))
      };
    });
  }

  function calibrateRelativeMinorQualities(candidates, chroma = []) {
    const majorByRoot = new Map(candidates.filter((candidate) => parseSymbol(candidate.symbol).quality === "major").map((candidate) => [parseSymbol(candidate.symbol).root, candidate]));
    return candidates.map((candidate) => {
      const parsed = parseSymbol(candidate.symbol);
      if (!["minor", "m7"].includes(parsed.quality)) return candidate;
      const relativeMajorRoot = (parsed.root + 3) % 12;
      const relativeMajor = majorByRoot.get(relativeMajorRoot);
      if (!relativeMajor) return candidate;
      const minorRootEvidence = Number(chroma[parsed.root] || 0);
      const majorRootEvidence = Number(chroma[relativeMajorRoot] || 0);
      const rootSupportsMajor = majorRootEvidence >= Math.max(0.08, minorRootEvidence * 1.05);
      const harmonicallyAmbiguous = Number(relativeMajor.score) >= Number(candidate.score) - 0.3;
      if (!rootSupportsMajor || !harmonicallyAmbiguous) return candidate;
      return { ...candidate, score: round(Math.min(Number(candidate.score), Number(relativeMajor.score) - 0.025)), relativeMajorPreferred: true };
    });
  }

  function chordCandidates(chroma, energy = 1, silenceThreshold = 0) {
    let candidates = [];
    for (let root = 0; root < 12; root += 1) {
      for (const [quality, intervals] of Object.entries(QUALITY_INTERVALS)) {
        const template = Array(12).fill(0.035);
        intervals.forEach(([interval, weight]) => { template[(root + interval) % 12] = weight; });
        const fit = cosine(chroma, template);
        const chordTones = new Set(intervals.map(([interval]) => (root + interval) % 12));
        const outside = chroma.reduce((sum, value, pc) => sum + (chordTones.has(pc) ? 0 : value), 0);
        candidates.push({ symbol: symbolFor(root, quality), root, quality, score: fit - 0.16 * outside });
      }
    }
    const relativeEnergy = silenceThreshold > 0 ? energy / silenceThreshold : 10;
    candidates.push({ symbol: "N.C.", root: null, quality: "none", score: relativeEnergy < 1 ? 0.96 - 0.18 * relativeEnergy : Math.max(0.02, 0.24 / relativeEnergy) });
    candidates = calibrateRelativeMinorQualities(calibrateExtendedQualities(candidates, chroma), chroma);
    candidates.sort((left, right) => right.score - left.score);
    const top = candidates[0], next = candidates[1] || top;
    const confidence = clamp(0.28 + (top.score - next.score) * 3.8 + (top.score - 0.68) * 1.25, 0.05, 0.99);
    return { top, confidence: round(confidence), candidates: candidates.map((item) => ({ ...item, score: round(item.score) })) };
  }

  function degree(root, keyRoot) { return root == null ? null : (root - keyRoot + 12) % 12; }
  function keyPrior(symbol, key) {
    const parsed = parseSymbol(symbol);
    if (parsed.root == null) return symbol === "N.C." ? -0.02 : -0.5;
    const interval = degree(parsed.root, key.root);
    const quality = parsed.quality === "7" ? "major" : parsed.quality === "m7" ? "minor" : parsed.quality;
    if (key.keyMode === "minor") {
      const preferred = new Map([[0, ["minor"]], [3, ["major"]], [5, ["minor"]], [7, ["minor", "major"]], [8, ["major"]], [10, ["major"]]]);
      if (preferred.get(interval)?.includes(quality)) return interval === 0 ? 0.62 : [5, 7].includes(interval) ? 0.46 : 0.34;
      if (interval === 0 && quality === "major") return -0.28;
      return -0.12;
    }
    const preferred = new Map([[0, ["major"]], [2, ["minor"]], [4, ["minor"]], [5, ["major"]], [7, ["major"]], [9, ["minor"]], [10, ["major"]]]);
    if (preferred.get(interval)?.includes(quality)) {
      if (interval === 0) return 0.54;
      if (interval === 5) return 0.54;
      if (interval === 7) return 0.54;
      if (interval === 10) return 0.32;
      if (interval === 9) return 0.26;
      return interval === 2 ? 0.18 : 0.14;
    }
    if (interval === 0 && quality === "minor") return -0.68;
    return -0.16;
  }

  function transitionPrior(previousSymbol, symbol, key) {
    if (!previousSymbol) return 0;
    if (previousSymbol === symbol) return 0.22;
    if (previousSymbol === "N.C." || symbol === "N.C.") return -0.04;
    const previous = parseSymbol(previousSymbol), next = parseSymbol(symbol);
    const from = degree(previous.root, key.root), to = degree(next.root, key.root);
    const common = new Map([
      [0, new Set([5, 7, 9, 10])], [5, new Set([0, 7])], [7, new Set([0, 9])],
      [9, new Set([5, 7])], [10, new Set([0, 5])], [2, new Set([7])], [4, new Set([9, 5])]
    ]);
    if (common.get(from)?.has(to)) return 0.22;
    if (from === to && previous.quality !== next.quality) return -0.32;
    return -0.05;
  }

  function candidateScore(evidence, symbol) {
    const candidate = evidence.candidates.find((item) => item.symbol === symbol);
    if (candidate?.extensionSupported === false) return -1;
    return candidate?.score ?? -0.4;
  }

  function decodeSequence(evidences, key, repeatBonus = new Map()) {
    const states = ["N.C."];
    for (let root = 0; root < 12; root += 1) for (const quality of Object.keys(QUALITY_INTERVALS)) states.push(symbolFor(root, quality));
    const scores = [], paths = [];
    evidences.forEach((evidence, index) => {
      scores[index] = new Map(); paths[index] = new Map();
      for (const state of states) {
        const emission = 3.4 * candidateScore(evidence, state) + keyPrior(state, key) + Number(repeatBonus.get(`${index}:${state}`) || 0);
        if (!index) { scores[index].set(state, emission); paths[index].set(state, null); continue; }
        let bestScore = -Infinity, bestPrevious = null;
        for (const previous of states) {
          const score = scores[index - 1].get(previous) + transitionPrior(previous, state, key);
          if (score > bestScore) { bestScore = score; bestPrevious = previous; }
        }
        scores[index].set(state, emission + bestScore); paths[index].set(state, bestPrevious);
      }
    });
    if (!evidences.length) return [];
    let state = states.reduce((best, candidate) => scores.at(-1).get(candidate) > scores.at(-1).get(best) ? candidate : best, states[0]);
    const result = Array(evidences.length);
    for (let index = evidences.length - 1; index >= 0; index -= 1) { result[index] = state; state = paths[index].get(state); }
    return result;
  }

  function findRepeatedBars(bars) {
    const assignments = Array(bars.length).fill(null);
    let groupNumber = 0;
    const windowSize = bars.length >= 16 ? 4 : 2;
    for (let left = 0; left + windowSize <= bars.length; left += 1) {
      if (assignments[left]) continue;
      for (let right = left + windowSize; right + windowSize <= bars.length; right += 1) {
        if (Math.abs(right - left) < windowSize) continue;
        const similarity = mean(Array.from({ length: windowSize }, (_item, offset) => cosine(bars[left + offset].full.chroma, bars[right + offset].full.chroma)));
        const symbolsMatch = mean(Array.from({ length: windowSize }, (_item, offset) => bars[left + offset].full.scored.top.symbol === bars[right + offset].full.scored.top.symbol ? 1 : 0));
        if (similarity < 0.91 || symbolsMatch < 0.75) continue;
        for (let offset = 0; offset < windowSize; offset += 1) {
          const existing = assignments[left + offset];
          const group = existing || `repeat-${++groupNumber}`;
          assignments[left + offset] = group;
          assignments[right + offset] = group;
        }
      }
    }
    return assignments;
  }

  function repeatConsensusBonus(decoded, assignments) {
    const groups = new Map();
    assignments.forEach((group, barIndex) => {
      if (!group) return;
      const symbols = groups.get(group) || [];
      symbols.push(decoded[barIndex * 2], decoded[barIndex * 2 + 1]);
      groups.set(group, symbols);
    });
    const bonus = new Map();
    assignments.forEach((group, barIndex) => {
      if (!group) return;
      const counts = new Map();
      (groups.get(group) || []).forEach((symbol) => counts.set(symbol, (counts.get(symbol) || 0) + 1));
      const consensus = [...counts.entries()].sort((left, right) => right[1] - left[1])[0]?.[0];
      if (consensus) {
        bonus.set(`${barIndex * 2}:${consensus}`, 0.24);
        bonus.set(`${barIndex * 2 + 1}:${consensus}`, 0.24);
      }
    });
    return bonus;
  }

  function repeatBarConsensusBonus(decoded, assignments) {
    const groups = new Map();
    assignments.forEach((group, barIndex) => {
      if (!group) return;
      const symbols = groups.get(group) || [];
      symbols.push(decoded[barIndex]);
      groups.set(group, symbols);
    });
    const bonus = new Map();
    assignments.forEach((group, barIndex) => {
      if (!group) return;
      const counts = new Map();
      (groups.get(group) || []).forEach((symbol) => counts.set(symbol, (counts.get(symbol) || 0) + 1));
      const consensus = [...counts.entries()].sort((left, right) => right[1] - left[1])[0]?.[0];
      if (consensus) bonus.set(`${barIndex}:${consensus}`, 0.24);
    });
    return bonus;
  }

  function confidenceFor(evidence, finalSymbol, contextualAdjusted) {
    const sorted = [...evidence.candidates].sort((left, right) => right.score - left.score);
    const chosen = candidateScore(evidence, finalSymbol);
    const rival = sorted.find((candidate) => candidate.symbol !== finalSymbol)?.score ?? chosen;
    let confidence = 0.32 + (chosen - rival) * 2.8 + (sorted[0]?.score - 0.68) * 0.9;
    if (contextualAdjusted) confidence -= 0.12;
    return round(clamp(confidence, 0.05, 0.98));
  }

  function sequenceMarginConfidence(evidences, decoded, index, key) {
    const evidence = evidences[index];
    const selected = decoded[index];
    const previous = decoded[index - 1] || null;
    const next = decoded[index + 1] || null;
    const localScore = (symbol) => {
      let score = 3.4 * candidateScore(evidence, symbol) + keyPrior(symbol, key);
      if (previous) score += 0.72 * transitionPrior(previous, symbol, key);
      if (next) score += 0.72 * transitionPrior(symbol, next, key);
      return score;
    };
    const selectedScore = localScore(selected);
    const rivals = Array.from(new Set(evidence.candidates.slice(0, 18).map((candidate) => candidate.symbol).filter((symbol) => symbol !== selected)));
    const rivalScore = rivals.length ? Math.max(...rivals.map(localScore)) : selectedScore;
    const margin = selectedScore - rivalScore;
    return round(clamp(0.58 + margin * 0.78, 0.12, 0.97));
  }

  function barEvidence(beatEvidence, barStartsMs, durationMs, beatsPerBar, silenceThreshold) {
    return barStartsMs.map((startMs, barIndex) => {
      const endMs = Number(barStartsMs[barIndex + 1] ?? durationMs);
      const inside = beatEvidence.filter((beat) => beat.startMs < endMs && beat.endMs > startMs);
      const splitIndex = Math.max(1, Math.round(beatsPerBar / 2));
      const firstItems = inside.slice(0, splitIndex);
      const secondItems = inside.slice(splitIndex);
      const make = (items) => {
        const chroma = medianChroma(items);
        const energy = median(items.map((item) => item.energy));
        return { chroma, energy, scored: chordCandidates(chroma, energy, silenceThreshold) };
      };
      return { bar: barIndex + 1, startMs, endMs, full: make(inside), first: make(firstItems), second: make(secondItems.length ? secondItems : firstItems) };
    });
  }

  function keyState(root, keyMode = "major") {
    return { root, key: NOTE_NAMES[root], keyMode };
  }

  function keyEvidenceScore(bar, key) {
    const candidates = (bar.full.scored.candidates || []).filter((candidate) => candidate.symbol !== "N.C.").slice(0, 18);
    const chordFit = candidates.length ? Math.max(...candidates.map((candidate) => Number(candidate.score) + keyPrior(candidate.symbol, key) * 0.72)) : -0.4;
    const profile = key.keyMode === "minor" ? MINOR_PROFILE : MAJOR_PROFILE;
    return chordFit + profileScore(bar.full.chroma, key.root, profile) * 0.24;
  }

  function normalizeKeyRegions(regions, barCount, fallbackKey) {
    const clean = (Array.isArray(regions) ? regions : []).map((region) => ({
      startBar: Math.max(1, Math.min(barCount, Math.round(Number(region.startBar) || 1))),
      key: NOTE_NAMES.includes(region.key) ? region.key : fallbackKey.key,
      keyMode: region.keyMode === "minor" ? "minor" : "major",
      confidence: round(clamp(Number(region.confidence ?? 1), 0.05, 1)),
      source: region.source === "manual" ? "manual" : "detected"
    })).sort((left, right) => left.startBar - right.startBar).filter((region, index, items) => !index || region.startBar !== items[index - 1].startBar);
    if (!clean.length || clean[0].startBar !== 1) clean.unshift({ startBar: 1, key: fallbackKey.key, keyMode: fallbackKey.keyMode, confidence: Number(fallbackKey.confidence || 0.5), source: "detected" });
    return clean.map((region, index) => ({ ...region, endBar: (clean[index + 1]?.startBar || barCount + 1) - 1 }));
  }

  function detectKeyRegions(bars, startingKey, forceStartingKey = false) {
    if (!bars.length) return [];
    const states = [];
    const modes = forceStartingKey ? [startingKey.keyMode] : ["major", "minor"];
    for (let root = 0; root < 12; root += 1) for (const mode of modes) states.push(keyState(root, mode));
    const prefix = states.map(() => [0]);
    states.forEach((state, stateIndex) => bars.forEach((bar) => prefix[stateIndex].push(prefix[stateIndex].at(-1) + keyEvidenceScore(bar, state))));
    const segmentScore = (stateIndex, start, end) => prefix[stateIndex][end] - prefix[stateIndex][start];
    const bestAt = Array.from({ length: bars.length + 1 }, () => states.map(() => ({ score: -Infinity, previousEnd: null, previousState: null })));
    for (let end = MIN_KEY_REGION_BARS; end <= bars.length; end += 1) {
      states.forEach((state, stateIndex) => {
        const startMatches = !forceStartingKey || (state.key === startingKey.key && state.keyMode === startingKey.keyMode);
        if (startMatches) {
          const hint = state.key === startingKey.key && state.keyMode === startingKey.keyMode ? 0.32 : 0;
          bestAt[end][stateIndex] = { score: segmentScore(stateIndex, 0, end) + hint, previousEnd: 0, previousState: null };
        }
        for (let start = MIN_KEY_REGION_BARS; start <= end - MIN_KEY_REGION_BARS; start += 1) {
          states.forEach((_previous, previousState) => {
            const previous = bestAt[start][previousState];
            if (!Number.isFinite(previous.score) || previousState === stateIndex) return;
            const score = previous.score + segmentScore(stateIndex, start, end) - 0.72;
            if (score > bestAt[end][stateIndex].score) bestAt[end][stateIndex] = { score, previousEnd: start, previousState };
          });
        }
      });
    }
    const end = bars.length;
    let stateIndex = states.reduce((best, _state, index) => bestAt[end][index].score > bestAt[end][best].score ? index : best, 0);
    if (!Number.isFinite(bestAt[end][stateIndex].score)) return normalizeKeyRegions([], bars.length, startingKey);
    const reversed = [];
    let cursor = end;
    while (cursor > 0) {
      const node = bestAt[cursor][stateIndex];
      const start = Number(node.previousEnd || 0);
      const state = states[stateIndex];
      const ownAverage = segmentScore(stateIndex, start, cursor) / Math.max(1, cursor - start);
      const rivalAverage = Math.max(...states.map((_item, index) => index === stateIndex ? -Infinity : segmentScore(index, start, cursor) / Math.max(1, cursor - start)));
      reversed.push({ startBar: start + 1, endBar: cursor, key: state.key, keyMode: state.keyMode, confidence: round(clamp(0.5 + (ownAverage - rivalAverage) * 2.2, 0.35, 0.97)), source: "detected" });
      stateIndex = node.previousState;
      cursor = start;
    }
    return reversed.reverse();
  }

  function decodeRegion(bars, key, barStartsMs, durationMs) {
    const halfEvidence = bars.flatMap((bar) => [bar.first.scored, bar.second.scored]);
    const halfDecoded = decodeSequence(halfEvidence, key);
    const repeatGroups = findRepeatedBars(bars);
    const fullEvidence = bars.map((bar) => bar.full.scored);
    let decodedBars = decodeSequence(fullEvidence, key);
    decodedBars = decodeSequence(fullEvidence, key, repeatBarConsensusBonus(decodedBars, repeatGroups));
    const fullSequenceConfidence = decodedBars.map((_symbol, index) => sequenceMarginConfidence(fullEvidence, decodedBars, index, key));
    const halfSequenceConfidence = halfDecoded.map((_symbol, index) => sequenceMarginConfidence(halfEvidence, halfDecoded, index, key));
    const chords = [];
    bars.forEach((bar, barIndex) => {
      const firstSymbol = halfDecoded[barIndex * 2];
      const secondSymbol = halfDecoded[barIndex * 2 + 1];
      const fullSymbol = decodedBars[barIndex];
      const splitScore = candidateScore(bar.first.scored, firstSymbol) + candidateScore(bar.second.scored, secondSymbol);
      const wholeScore = candidateScore(bar.first.scored, fullSymbol) + candidateScore(bar.second.scored, fullSymbol);
      const split = firstSymbol !== secondSymbol && splitScore - wholeScore >= 0.2 && bar.first.scored.confidence >= 0.38 && bar.second.scored.confidence >= 0.38;
      const symbols = split ? [firstSymbol, secondSymbol] : [firstSymbol === secondSymbol ? firstSymbol : fullSymbol];
      symbols.forEach((symbol, chordIndex) => {
        const startFraction = split ? chordIndex * 0.5 : 0;
        const endFraction = split ? (chordIndex + 1) * 0.5 : 1;
        const evidence = split ? [bar.first.scored, bar.second.scored][chordIndex] : bar.full.scored;
        const rawCandidate = evidence.top.symbol;
        const contextualAdjusted = rawCandidate !== symbol;
        const selectedCandidate = evidence.candidates.find((candidate) => candidate.symbol === symbol);
        let confidence = confidenceFor(evidence, symbol, contextualAdjusted);
        const contextConfidence = split ? halfSequenceConfidence[barIndex * 2 + chordIndex] : fullSequenceConfidence[barIndex];
        confidence = Math.max(confidence, contextConfidence);
        if (!split && firstSymbol === secondSymbol) confidence += 0.1;
        if (repeatGroups[barIndex]) confidence += 0.06;
        if (keyPrior(symbol, key) >= 0.3) confidence += 0.06;
        const inKey = keyPrior(symbol, key) > 0;
        const stableInKey = firstSymbol === secondSymbol && inKey;
        if (!contextualAdjusted && stableInKey) confidence = Math.max(confidence, 0.8);
        if (contextualAdjusted && stableInKey) confidence = Math.max(confidence, repeatGroups[barIndex] ? 0.78 : 0.72);
        confidence = round(clamp(confidence, 0.05, 0.98));
        const reasons = [];
        if (contextualAdjusted) reasons.push(repeatGroups[barIndex] ? "Adjusted using the key and repeated section." : "Adjusted using the key and surrounding chords.");
        if (split) reasons.push("A supported chord change was found at the half-bar.");
        if (confidence < 0.68) reasons.push("Audio evidence is close between multiple chords.");
        if (!reasons.length) reasons.push("Strong audio and song-context agreement.");
        const startMs = Math.round(bar.startMs + (bar.endMs - bar.startMs) * startFraction);
        const endMs = Math.round(bar.startMs + (bar.endMs - bar.startMs) * endFraction);
        const reviewed = symbol === "N.C."
          ? confidence >= 0.82 && !contextualAdjusted
          : inKey
            ? confidence >= 0.78 || (stableInKey && confidence >= 0.72)
            : (!contextualAdjusted && confidence >= 0.84) || (contextConfidence >= 0.88 && confidence >= 0.82);
        chords.push({
          id: `detected-chord-${bar.bar}-${chordIndex + 1}`, bar: bar.bar, startFraction, startMs, endMs,
          symbol, rawCandidate, finalSymbol: symbol,
          alternatives: evidence.candidates.filter((candidate) => candidate.symbol !== symbol).slice(0, 3).map((candidate) => ({ symbol: candidate.symbol, score: candidate.score })),
          confidence, contextualAdjusted, sequenceConfidence: contextConfidence, reviewReasons: reasons, repeatedSectionGroup: repeatGroups[barIndex] || null,
          extensionSupported: selectedCandidate?.extensionSupported,
          extensionGain: selectedCandidate?.extensionGain,
          seventhCoreRatio: selectedCandidate?.seventhCoreRatio,
          reviewed, needsAttention: !reviewed
        });
      });
    });
    return { chords, repeatGroups };
  }

  function decodeBars(bars, key, barStartsMs, durationMs, requestedRegions = null, forceStartingKey = false) {
    const keyRegions = requestedRegions?.length
      ? normalizeKeyRegions(requestedRegions, bars.length, key)
      : detectKeyRegions(bars, key, forceStartingKey);
    const chords = [];
    const repeatGroups = [];
    keyRegions.forEach((region) => {
      const regionBars = bars.filter((bar) => bar.bar >= region.startBar && bar.bar <= region.endBar);
      const regionKey = { key: region.key, keyMode: region.keyMode, root: NOTE_NAMES.indexOf(region.key), confidence: region.confidence };
      const decoded = decodeRegion(regionBars, regionKey, barStartsMs, durationMs);
      decoded.chords.forEach((chord) => chords.push({ ...chord, activeKey: region.key, activeKeyMode: region.keyMode }));
      decoded.repeatGroups.forEach((group) => repeatGroups.push(group));
    });
    const possibleModulations = keyRegions.slice(1).map((region) => ({
      startBar: region.startBar,
      endBar: region.endBar,
      key: region.key,
      keyMode: region.keyMode,
      confidence: region.confidence,
      reason: `Key change to ${region.key} ${region.keyMode}.`
    }));
    return { chords: chords.sort((left, right) => left.bar - right.bar || left.startFraction - right.startFraction), repeatGroups, possibleModulations, keyRegions };
  }

  function scoreMeter(track, beatEvidence, option) {
    let best = { phase: 0, score: -Infinity };
    for (let phase = 0; phase < option.beats; phase += 1) {
      const downbeats = [], otherBeats = [], changes = [], otherChanges = [];
      beatEvidence.forEach((beat, index) => {
        if ((index - phase + option.beats) % option.beats === 0) {
          downbeats.push(beat.onset || 0);
          if (index) changes.push(1 - cosine(beatEvidence[index - 1].chroma, beat.chroma));
        } else {
          otherBeats.push(beat.onset || 0);
          if (index) otherChanges.push(1 - cosine(beatEvidence[index - 1].chroma, beat.chroma));
        }
      });
      const accent = mean(downbeats) - mean(otherBeats);
      const chordAlignment = mean(changes) - mean(otherChanges);
      const hintedCountryGrid = Number(track.hintBonus || 0) > 0;
      let metricalPrior = hintedCountryGrid
        ? (option.meter === "4/4" ? 0.026 : option.meter === "2/4" ? 0.02 : option.meter === "3/4" ? 0.004 : 0)
        : (option.meter === "3/4" ? 0.03 : option.meter === "4/4" ? 0.012 : option.meter === "2/4" ? 0.004 : 0);
      if (option.meter === "6/8") {
        const compoundAccents = beatEvidence.filter((_beat, index) => (index - phase + option.beats) % option.beats === 3).map((beat) => beat.onset || 0);
        const compoundOthers = beatEvidence.filter((_beat, index) => ![0, 3].includes((index - phase + option.beats) % option.beats)).map((beat) => beat.onset || 0);
        metricalPrior += clamp((mean(downbeats.concat(compoundAccents)) - mean(compoundOthers)) * 0.3, -0.05, 0.08);
        if (track.bpm < 100) metricalPrior -= 0.04;
      }
      const score = accent * 0.55 + chordAlignment * 0.65 + metricalPrior;
      if (score > best.score) best = { phase, score, accent, chordAlignment };
    }
    return { ...option, ...best, track };
  }

  function rhythmAnalysis(samples, sampleRate, durationMs, options = {}) {
    const envelope = onsetEnvelope(samples, sampleRate);
    const tempoHint = Number(options.tempoHint);
    const hintedTempos = Number.isFinite(tempoHint) ? [tempoHint, tempoHint * 2, tempoHint / 2] : [];
    const hintBonus = (bpm) => Number.isFinite(tempoHint)
      ? Math.max(...hintedTempos.map((target, index) => Math.max(0, (index === 1 ? 0.16 : 0.1) - Math.abs(bpm - target) * 0.008)))
      : 0;
    let candidates = tempoCandidates(envelope, hintedTempos).map((candidate) => ({ ...candidate, hintBonus: hintBonus(candidate.bpm) })).sort((left, right) => right.score + right.hintBonus - left.score - left.hintBonus).slice(0, 6);
    if (Number.isFinite(Number(options.tempo))) {
      const requested = Number(options.tempo);
      candidates = candidates.sort((left, right) => Math.abs(left.bpm - requested) - Math.abs(right.bpm - requested)).slice(0, 1);
    }
    const tuningSemitones = estimateTuning(samples, sampleRate, durationMs);
    const evaluated = [];
    candidates.slice(0, 3).forEach((candidate) => {
      const track = trackDynamicBeats(envelope, candidate, durationMs);
      const previewTimes = track.timesMs.slice(0, 192);
      const chromas = beatChromas(samples, sampleRate, previewTimes, durationMs, tuningSemitones);
      const beatEvidence = chromas.map((item, index) => ({ ...item, onset: envelope.values[Math.round(item.startMs / 1000 * envelope.sampleRate / envelope.hop)] || 0, beatIndex: index }));
      const meterOptions = options.meter ? METER_OPTIONS.filter((option) => option.meter === options.meter) : METER_OPTIONS;
      meterOptions.forEach((option) => {
        const meter = scoreMeter(track, beatEvidence, option);
        evaluated.push({ track, beatEvidence, meter, score: candidate.score + candidate.hintBonus + track.phaseScore * 0.18 + meter.score * 0.42 });
      });
    });
    const strongestBase = Math.max(...evaluated.map((candidate) => candidate.score));
    const slowTempos = Array.from(new Set(evaluated.map((candidate) => candidate.track.bpm).filter((bpm) => bpm < 86)));
    slowTempos.forEach((slowTempo) => {
      const doubled = evaluated.filter((other) => Math.abs(other.track.bpm - slowTempo * 2) <= 4);
      if (doubled.some((other) => strongestBase - other.score <= 0.14)) doubled.forEach((other) => { other.score += 0.11; });
    });
    evaluated.sort((left, right) => right.score - left.score);
    const best = evaluated[0];
    if (!best?.track?.timesMs?.length) throw new Error("A steady pulse could not be found in this recording.");
    const second = evaluated.find((candidate) => candidate.track.bpm !== best.track.bpm || candidate.meter.meter !== best.meter.meter) || best;
    const tempoRivals = evaluated.filter((candidate) => candidate.track.bpm !== best.track.bpm);
    const meterRivals = evaluated.filter((candidate) => candidate.meter.meter !== best.meter.meter);
    const tempoConfidence = clamp(0.45 + (best.score - (tempoRivals[0]?.score ?? best.score - 0.2)) * 2.4, 0.1, 0.98);
    const meterConfidence = clamp(0.42 + (best.score - (meterRivals[0]?.score ?? second.score)) * 2.8, 0.1, 0.98);
    const phase = best.meter.phase;
    let beatTimesMs = best.track.timesMs.slice(phase);
    if (!beatTimesMs.length) beatTimesMs = best.track.timesMs;
    const barStartsMs = beatTimesMs.filter((_time, index) => index % best.meter.beats === 0);
    if (barStartsMs.length > 1) {
      const typicalBarMs = median(barStartsMs.slice(1).map((time, index) => time - barStartsMs[index]));
      if (durationMs - barStartsMs.at(-1) < typicalBarMs * 0.4) barStartsMs.pop();
    }
    const fullBeatChromas = beatChromas(samples, sampleRate, beatTimesMs, durationMs, tuningSemitones, [0.28, 0.62]);
    const fullBeatEvidence = fullBeatChromas.map((item, index) => ({ ...item, onset: envelope.values[Math.round(item.startMs / 1000 * envelope.sampleRate / envelope.hop)] || 0, beatIndex: index }));
    return {
      tempo: best.track.bpm, tempoConfidence: round(tempoConfidence), meter: best.meter.meter, meterConfidence: round(meterConfidence),
      beatsPerBar: best.meter.beats, beatTimesMs, barStartsMs, beatEvidence: fullBeatEvidence, tuningSemitones,
      rhythmAlternatives: evaluated.slice(0, 5).map((candidate) => ({ tempo: candidate.track.bpm, meter: candidate.meter.meter, score: round(candidate.score) }))
    };
  }

  function retainedState(bars, rhythm, key, decoded) {
    return {
      version: ANALYSIS_VERSION,
      qualityCalibrationVersion: QUALITY_CALIBRATION_VERSION,
      tuningCents: Math.round(rhythm.tuningSemitones * 100),
      bars: bars.map((bar, index) => ({
        bar: bar.bar, startMs: bar.startMs, endMs: bar.endMs, repeatedSectionGroup: decoded.repeatGroups[index] || null,
        full: { chroma: bar.full.chroma.map((value) => round(value, 5)), energy: round(bar.full.energy, 6), candidates: bar.full.scored.candidates },
        first: { chroma: bar.first.chroma.map((value) => round(value, 5)), energy: round(bar.first.energy, 6), candidates: bar.first.scored.candidates },
        second: { chroma: bar.second.chroma.map((value) => round(value, 5)), energy: round(bar.second.energy, 6), candidates: bar.second.scored.candidates }
      })),
      keyAlternatives: key.alternatives,
      rhythmAlternatives: rhythm.rhythmAlternatives
    };
  }

  function hydrateRetainedBars(analysis) {
    return (analysis.analysisState?.bars || []).map((bar) => {
      const make = (item) => {
        const candidates = calibrateRelativeMinorQualities(calibrateExtendedQualities(item.candidates || [], item.chroma || []), item.chroma || []).sort((left, right) => right.score - left.score);
        const top = candidates[0] || { symbol: "N.C.", score: 0 };
        const next = candidates[1] || top;
        return { chroma: item.chroma, energy: item.energy, scored: { top, candidates, confidence: clamp(0.28 + (top.score - next.score) * 3.8, 0.05, 0.99) } };
      };
      return { bar: bar.bar, startMs: bar.startMs, endMs: bar.endMs, full: make(bar.full), first: make(bar.first), second: make(bar.second) };
    });
  }

  function redecodeAnalysis(analysis, requestedKey, requestedMode = "major", requestedRegions = null) {
    const keyRoot = NOTE_NAMES.indexOf(requestedKey);
    if (keyRoot < 0 || !analysis?.analysisState?.bars?.length) throw new Error("This project does not retain v2 chord candidates. Reanalyze the recording first.");
    const key = { key: requestedKey, keyMode: requestedMode === "minor" ? "minor" : "major", root: keyRoot, confidence: Number(analysis.keyConfidence || 0.5), alternatives: analysis.analysisState.keyAlternatives || [] };
    const bars = hydrateRetainedBars(analysis);
    const decoded = decodeBars(bars, key, analysis.barStartsMs, Number(analysis.durationMs || bars.at(-1)?.endMs || 0), requestedRegions, !requestedRegions?.length);
    const calibratedBars = analysis.analysisState.bars.map((bar, index) => ({
      ...bar,
      full: { ...bar.full, candidates: bars[index].full.scored.candidates },
      first: { ...bar.first, candidates: bars[index].first.scored.candidates },
      second: { ...bar.second, candidates: bars[index].second.scored.candidates }
    }));
    return {
      ...analysis,
      key: key.key,
      keyMode: key.keyMode,
      chords: decoded.chords,
      keyRegions: decoded.keyRegions,
      possibleModulations: decoded.possibleModulations,
      analysisState: { ...analysis.analysisState, qualityCalibrationVersion: QUALITY_CALIBRATION_VERSION, bars: calibratedBars }
    };
  }

  function analyzePcm(input, sampleRate, durationMs, options = {}, notify = () => {}) {
    notify("Detecting beats, meter, key, and chords", "Tracking the pulse and downbeats");
    const reduced = downsample(input, sampleRate);
    const rhythm = rhythmAnalysis(reduced.samples, reduced.sampleRate, durationMs, options);
    notify("Detecting beats, meter, key, and chords", "Measuring tuning and beat-synchronous harmony");
    const energies = rhythm.beatEvidence.map((item) => item.energy).filter((value) => value > 0);
    const silenceThreshold = Math.max(1e-6, median(energies) * 0.55);
    const bars = barEvidence(rhythm.beatEvidence, rhythm.barStartsMs, durationMs, rhythm.beatsPerBar, silenceThreshold);
    if (!bars.length) throw new Error("Song bars could not be aligned to the recording.");
    const startingKeyBars = bars.slice(0, Math.min(bars.length, 48, Math.max(MIN_KEY_REGION_BARS * 2, Math.ceil(bars.length / 3))));
    const key = options.key && NOTE_NAMES.includes(options.key)
      ? { key: options.key, keyMode: options.keyMode === "minor" ? "minor" : "major", root: NOTE_NAMES.indexOf(options.key), confidence: 1, alternatives: [] }
      : estimateKey(startingKeyBars.map((bar) => bar.full.chroma), { key: options.keyHint, keyMode: options.keyModeHint });
    notify("Detecting beats, meter, key, and chords", "Decoding the complete chord sequence");
    const decoded = decodeBars(bars, key, rhythm.barStartsMs, durationMs, null, true);
    const startingRegion = decoded.keyRegions[0] || { key: key.key, keyMode: key.keyMode, confidence: key.confidence };
    notify("Building the steel route", "Preparing the attention list and editable chord bars");
    const firstBarMs = rhythm.barStartsMs[0] || 0;
    const medianBarMs = rhythm.barStartsMs.length > 1 ? median(rhythm.barStartsMs.slice(1).map((time, index) => time - rhythm.barStartsMs[index])) : 0;
    const analysis = {
      analysisVersion: ANALYSIS_VERSION, durationMs, tempo: rhythm.tempo, tempoConfidence: rhythm.tempoConfidence,
      key: startingRegion.key, keyMode: startingRegion.keyMode, keyConfidence: startingRegion.confidence,
      meter: rhythm.meter, meterConfidence: rhythm.meterConfidence,
      beatTimesMs: rhythm.beatTimesMs, barStartsMs: rhythm.barStartsMs, chords: decoded.chords,
      authoredCountIn: Boolean(medianBarMs && firstBarMs > medianBarMs * 0.7), possibleModulations: decoded.possibleModulations, keyRegions: decoded.keyRegions,
      analysisState: null
    };
    analysis.analysisState = retainedState(bars, rhythm, key, decoded);
    return analysis;
  }

  const api = {
    ANALYSIS_VERSION, QUALITY_CALIBRATION_VERSION, NOTE_NAMES, downsample, onsetEnvelope, tempoCandidates, trackDynamicBeats,
    estimateTuning, spectralFrame, estimateKey, chordCandidates, keyPrior, transitionPrior,
    decodeSequence, findRepeatedBars, detectKeyRegions, normalizeKeyRegions, decodeRegion, decodeBars, confidenceFor, barEvidence, scoreMeter, rhythmAnalysis, analyzePcm, redecodeAnalysis
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  global.STEEL_RAG_ANALYSIS_V2 = api;

  if (typeof global.postMessage === "function") {
    global.onmessage = (event) => {
      if (event.data?.type === "cancel") { global.close(); return; }
      try {
        if (event.data?.type === "analyze") {
          const input = new Float32Array(event.data.samples);
          const analysis = analyzePcm(input, Number(event.data.sampleRate), Number(event.data.durationMs), event.data.options || {}, (stage, detail) => global.postMessage({ type: "progress", stage, detail }));
          global.postMessage({ type: "complete", analysis });
        } else if (event.data?.type === "redecode") {
          const analysis = redecodeAnalysis(event.data.analysis, event.data.key, event.data.keyMode, event.data.keyRegions || null);
          global.postMessage({ type: "complete", analysis });
        }
      } catch (error) {
        global.postMessage({ type: "error", message: error?.message || "The recording could not be analyzed." });
      }
    };
  }
})(typeof self !== "undefined" ? self : globalThis);
