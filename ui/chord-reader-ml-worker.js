"use strict";

// Feature-flagged, same-origin ONNX chord challenger. The existing v2 worker
// remains authoritative and is returned unchanged if this worker cannot load.
(function chordReaderMlWorker(global) {
  const SAMPLE_RATE = 11025;
  const FRAME_SECONDS = 0.1;
  const FRAME_SIZE = 4096;
  const CLASS_COUNT = 49;
  const QUALITIES = ["major", "minor", "7", "m7"];
  const NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
  const MODEL_URL = "/ui/models/chord-student-v1.onnx";
  const RUNTIME_URL = "/ui/vendor/onnxruntime-web/ort.wasm.min.js";
  const WASM_URL = "/ui/vendor/onnxruntime-web/";
  let sessionPromise = null;
  let cancelled = false;

  function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }

  function downsample(input, sampleRate, targetRate = SAMPLE_RATE) {
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
          const cosine = Math.cos(angle * index), sine = Math.sin(angle * index);
          const even = start + index, odd = even + length / 2;
          const realOdd = real[odd] * cosine - imag[odd] * sine;
          const imagOdd = real[odd] * sine + imag[odd] * cosine;
          real[odd] = real[even] - realOdd; imag[odd] = imag[even] - imagOdd;
          real[even] += realOdd; imag[even] += imagOdd;
        }
      }
    }
  }

  function spectralFeatures(samples, sampleRate, durationMs, notify = () => {}) {
    const frameCount = Math.max(1, Math.ceil(durationMs / 1000 / FRAME_SECONDS));
    const output = new Float32Array(frameCount * 13);
    for (let frame = 0; frame < frameCount; frame += 1) {
      if (cancelled) throw new DOMException("Local analysis was cancelled.", "AbortError");
      const centerSecond = frame * FRAME_SECONDS;
      const start = clamp(Math.round(centerSecond * sampleRate - FRAME_SIZE / 2), 0, Math.max(0, samples.length - FRAME_SIZE));
      const real = new Float64Array(FRAME_SIZE), imag = new Float64Array(FRAME_SIZE), chroma = new Float64Array(12);
      let energy = 0;
      for (let index = 0; index < FRAME_SIZE; index += 1) {
        const sample = samples[start + index] || 0;
        energy += sample * sample;
        real[index] = sample * (0.5 - 0.5 * Math.cos(2 * Math.PI * index / (FRAME_SIZE - 1)));
      }
      fft(real, imag);
      for (let bin = 1; bin < FRAME_SIZE / 2; bin += 1) {
        const frequency = bin * sampleRate / FRAME_SIZE;
        if (frequency < 55 || frequency > 1760) continue;
        const midi = 69 + 12 * Math.log2(frequency / 440);
        const lower = Math.floor(midi), fraction = midi - lower;
        const magnitude = Math.sqrt(Math.hypot(real[bin], imag[bin])) * clamp(220 / frequency, 0.22, 3);
        chroma[((lower % 12) + 12) % 12] += magnitude * (1 - fraction);
        chroma[(((lower + 1) % 12) + 12) % 12] += magnitude * fraction;
      }
      const total = chroma.reduce((sum, value) => sum + Math.max(0, value), 0) || 1;
      for (let pitch = 0; pitch < 12; pitch += 1) output[frame * 13 + pitch] = Math.max(0, chroma[pitch]) / total;
      output[frame * 13 + 12] = Math.sqrt(energy / FRAME_SIZE);
      if (frame && frame % 200 === 0) notify("Running the ML chord reader", `${Math.round(frame / frameCount * 100)}%`);
    }
    return { values: output, frameCount };
  }

  function transitionScore(left, right) {
    if (left === right) return 0;
    if (!left || !right) return -0.8;
    return (left - 1) % 12 === (right - 1) % 12 ? -0.45 : -1.2;
  }

  function viterbi(logits, frameCount) {
    let scores = Array.from({ length: CLASS_COUNT }, (_item, state) => logits[state]);
    const backpointers = [];
    for (let frame = 1; frame < frameCount; frame += 1) {
      const pointers = new Int16Array(CLASS_COUNT), next = new Float64Array(CLASS_COUNT);
      for (let right = 0; right < CLASS_COUNT; right += 1) {
        let best = -Infinity, bestLeft = 0;
        for (let left = 0; left < CLASS_COUNT; left += 1) {
          const score = scores[left] + transitionScore(left, right);
          if (score > best) { best = score; bestLeft = left; }
        }
        pointers[right] = bestLeft;
        next[right] = best + logits[frame * CLASS_COUNT + right];
      }
      backpointers.push(pointers); scores = Array.from(next);
    }
    const path = new Int16Array(frameCount);
    path[frameCount - 1] = scores.indexOf(Math.max(...scores));
    for (let frame = frameCount - 2; frame >= 0; frame -= 1) path[frame] = backpointers[frame][path[frame + 1]];
    return path;
  }

  function symbolFor(index) {
    if (!index) return "N.C.";
    const value = index - 1;
    const root = NOTE_NAMES[value % 12], quality = QUALITIES[Math.floor(value / 12)];
    return quality === "major" ? root : quality === "minor" ? `${root}m` : `${root}${quality}`;
  }

  function confidenceFor(logits, frame, selected) {
    let maximum = -Infinity;
    for (let state = 0; state < CLASS_COUNT; state += 1) maximum = Math.max(maximum, logits[frame * CLASS_COUNT + state]);
    let total = 0;
    for (let state = 0; state < CLASS_COUNT; state += 1) total += Math.exp(logits[frame * CLASS_COUNT + state] - maximum);
    return Math.exp(logits[frame * CLASS_COUNT + selected] - maximum) / Math.max(1e-12, total);
  }

  function segmentsFromLogits(logits, frameCount, durationMs) {
    const path = viterbi(logits, frameCount), output = [];
    let start = 0;
    for (let frame = 1; frame <= frameCount; frame += 1) {
      if (frame < frameCount && path[frame] === path[start]) continue;
      let confidence = 0;
      for (let cursor = start; cursor < frame; cursor += 1) confidence += confidenceFor(logits, cursor, path[start]);
      output.push({
        startMs: Math.round(start * FRAME_SECONDS * 1000),
        endMs: frame === frameCount ? durationMs : Math.min(durationMs, Math.round(frame * FRAME_SECONDS * 1000)),
        symbol: symbolFor(path[start]),
        confidence: confidence / Math.max(1, frame - start)
      });
      start = frame;
    }
    return output.filter((segment) => segment.endMs > segment.startMs);
  }

  async function ensureSession() {
    if (!sessionPromise) sessionPromise = (async () => {
      if (!global.ort && typeof importScripts === "function") importScripts(RUNTIME_URL);
      if (!global.ort) throw new Error("The local ONNX runtime is unavailable.");
      global.ort.env.wasm.wasmPaths = WASM_URL;
      global.ort.env.wasm.numThreads = 1;
      return global.ort.InferenceSession.create(MODEL_URL, { executionProviders: ["wasm"] });
    })();
    return sessionPromise;
  }

  async function analyzePcm(input, sampleRate, durationMs, notify = () => {}) {
    cancelled = false;
    notify("Running the ML chord reader", "Preparing worker-compatible spectral features");
    const reduced = downsample(input, sampleRate);
    const features = spectralFeatures(reduced.samples, reduced.sampleRate, durationMs, notify);
    const session = await ensureSession();
    const tensor = new global.ort.Tensor("float32", features.values, [1, features.frameCount, 13]);
    const result = await session.run({ features: tensor });
    return {
      analysisVersion: 3,
      engine: "chord-student-v1",
      durationMs,
      frameSeconds: FRAME_SECONDS,
      segments: segmentsFromLogits(result.logits.data, features.frameCount, durationMs)
    };
  }

  const api = { SAMPLE_RATE, FRAME_SECONDS, CLASS_COUNT, downsample, fft, spectralFeatures, viterbi, symbolFor, segmentsFromLogits, analyzePcm };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (global && typeof global.postMessage === "function") {
    global.onmessage = async (event) => {
      if (event.data?.type === "cancel") { cancelled = true; return; }
      if (event.data?.type !== "analyze") return;
      try {
        const analysis = await analyzePcm(
          new Float32Array(event.data.samples),
          Number(event.data.sampleRate),
          Number(event.data.durationMs),
          (stage, detail) => global.postMessage({ type: "progress", stage, detail })
        );
        global.postMessage({ type: "complete", analysis });
      } catch (error) {
        global.postMessage({ type: "error", message: error instanceof Error ? error.message : String(error) });
      }
    };
  }
})(typeof self !== "undefined" ? self : globalThis);
