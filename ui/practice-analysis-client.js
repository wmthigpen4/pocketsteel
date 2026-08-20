(function (global) {
  "use strict";

  const WORKER_URL = "/ui/practice-analysis-worker-audio-led-key-v11.js";
  const ML_WORKER_URL = "/ui/chord-reader-ml-worker.js";
  const ML_FEATURE_FLAG = "pocketSteel.chordReaderEngine";

  async function decodeAudio(file) {
    const bytes = await file.arrayBuffer();
    const context = new (global.AudioContext || global.webkitAudioContext)();
    try {
      return await context.decodeAudioData(bytes.slice(0));
    } catch (_error) {
      throw new Error("This recording could not be decoded. Try an MP3, M4A/AAC, or WAV file that plays normally on this device.");
    } finally {
      await context.close();
    }
  }

  function monoSamples(buffer) {
    const output = new Float32Array(buffer.length);
    for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) {
      const input = buffer.getChannelData(channel);
      for (let index = 0; index < output.length; index += 1) output[index] += input[index] / buffer.numberOfChannels;
    }
    return output;
  }

  function runWorkerAt(workerUrl, message, transfer = [], onProgress = () => {}) {
    return new Promise((resolve, reject) => {
      const worker = new Worker(workerUrl);
      const cancel = () => { worker.postMessage({ type: "cancel" }); worker.terminate(); reject(new DOMException("Local analysis was cancelled.", "AbortError")); };
      message.signal?.addEventListener("abort", cancel, { once: true });
      const payload = { ...message }; delete payload.signal;
      worker.onmessage = (event) => {
        if (event.data?.type === "progress") onProgress(event.data.stage, event.data.detail);
        if (event.data?.type === "complete") { worker.terminate(); resolve(event.data.analysis); }
        if (event.data?.type === "error") { worker.terminate(); reject(new Error(event.data.message)); }
      };
      worker.onerror = () => { worker.terminate(); reject(new Error("Local song analysis was interrupted. You can try the recording again.")); };
      worker.postMessage(payload, transfer);
    });
  }

  function runWorker(message, transfer = [], onProgress = () => {}) {
    return runWorkerAt(WORKER_URL, message, transfer, onProgress);
  }

  function mlEnabled(options = {}) {
    if (options.chordReaderEngine === "ml-v3") return true;
    try { return global.localStorage?.getItem(ML_FEATURE_FLAG) === "ml-v3"; } catch (_error) { return false; }
  }

  function nearestBeat(value, beatTimesMs) {
    if (!beatTimesMs.length) return value;
    const nearest = beatTimesMs.reduce((best, beat) => Math.abs(beat - value) < Math.abs(best - value) ? beat : best, beatTimesMs[0]);
    const intervals = beatTimesMs.slice(1).map((beat, index) => beat - beatTimesMs[index]).filter((interval) => interval > 0);
    const typical = intervals.length ? intervals.sort((left, right) => left - right)[Math.floor(intervals.length / 2)] : 500;
    return Math.abs(nearest - value) <= Math.max(120, typical * 0.48) ? nearest : value;
  }

  function mergeMlAnalysis(base, ml) {
    if (!Array.isArray(ml?.segments) || !ml.segments.length) throw new Error("The ML reader returned no chord segments.");
    const barStarts = Array.isArray(base.barStartsMs) ? base.barStartsMs : [];
    const beatTimes = Array.isArray(base.beatTimesMs) ? base.beatTimesMs : [];
    const snapped = ml.segments.map((segment) => ({ ...segment, startMs: nearestBeat(Number(segment.startMs), beatTimes) }));
    const chords = [];
    snapped.forEach((segment, index) => {
      let barIndex = barStarts.findIndex((start) => start > segment.startMs) - 1;
      if (barIndex < 0) barIndex = Math.max(0, barStarts.length - 1);
      if (barStarts.length && segment.startMs < barStarts[0]) barIndex = 0;
      const barStart = Number(barStarts[barIndex] ?? 0);
      const barEnd = Number(barStarts[barIndex + 1] ?? base.durationMs);
      const startMs = Math.max(barStart, Number(segment.startMs));
      const endMs = Math.max(startMs + 1, Math.min(Number(snapped[index + 1]?.startMs ?? segment.endMs), Number(base.durationMs)));
      const confidence = Number(segment.confidence || 0);
      const reviewed = confidence >= 0.8;
      const symbol = String(segment.symbol || "N.C.");
      const event = {
        id: `ml-chord-${barIndex + 1}-${index + 1}`,
        bar: barIndex + 1,
        startFraction: Math.max(0, Math.min(1, (startMs - barStart) / Math.max(1, barEnd - barStart))),
        startMs, endMs, symbol, rawCandidate: symbol, finalSymbol: symbol,
        alternatives: [], confidence, contextualAdjusted: false, rootAdjusted: false, qualityAdjusted: false,
        rootStatus: symbol === "N.C." ? "no_chord" : "audio_supported",
        qualityStatus: "audio_supported", publicationSymbol: reviewed ? symbol : null,
        sequenceConfidence: confidence,
        reviewReasons: [reviewed ? "The supervised audio model strongly supports this chord." : "The supervised audio model is uncertain; review this chord."],
        reviewed, needsAttention: !reviewed, sourceEngine: "chord-student-v1"
      };
      const previous = chords.at(-1);
      if (previous && previous.symbol === event.symbol && previous.bar === event.bar) previous.endMs = event.endMs;
      else chords.push(event);
    });
    return { ...base, analysisVersion: 3, chordReaderEngine: "ml-v3", mlModel: ml.engine, chords };
  }

  async function analyzeFile(file, options = {}, onProgress = () => {}, signal) {
    const decoded = await decodeAudio(file);
    const samples = monoSamples(decoded);
    const durationMs = Math.round(Number(decoded.duration) * 1000);
    if (!mlEnabled(options)) {
      const analysis = await runWorker({ type: "analyze", samples: samples.buffer, sampleRate: decoded.sampleRate, durationMs, options, signal }, [samples.buffer], onProgress);
      return { analysis, durationMs };
    }
    const mlSamples = samples.slice();
    const basePromise = runWorker(
      { type: "analyze", samples: samples.buffer, sampleRate: decoded.sampleRate, durationMs, options, signal },
      [samples.buffer],
      onProgress
    );
    const mlPromise = runWorkerAt(
      ML_WORKER_URL,
      { type: "analyze", samples: mlSamples.buffer, sampleRate: decoded.sampleRate, durationMs, signal },
      [mlSamples.buffer],
      onProgress
    ).then((value) => ({ value }), (error) => ({ error }));
    const analysis = await basePromise;
    const mlResult = await mlPromise;
    if (mlResult.error) return {
      analysis: { ...analysis, chordReaderEngine: "v2-fallback", mlFallbackReason: mlResult.error instanceof Error ? mlResult.error.message : String(mlResult.error) },
      durationMs
    };
    return { analysis: mergeMlAnalysis(analysis, mlResult.value), durationMs };
  }

  function redecode(analysis, key, keyMode, onProgress = () => {}) {
    onProgress("Updating chord context", `Rechecking the complete song in ${key} ${keyMode}`);
    return runWorker({ type: "redecode", analysis, key, keyMode }, [], onProgress);
  }

  function redecodeRegions(analysis, keyRegions, onProgress = () => {}) {
    const first = keyRegions?.[0] || { key: analysis.key, keyMode: analysis.keyMode };
    onProgress("Updating key regions", `Rechecking the song across ${keyRegions.length} key section${keyRegions.length === 1 ? "" : "s"}`);
    return runWorker({ type: "redecode", analysis, key: first.key, keyMode: first.keyMode, keyRegions }, [], onProgress);
  }

  global.STEEL_RAG_ANALYSIS_CLIENT = {
    WORKER_URL, ML_WORKER_URL, ML_FEATURE_FLAG, decodeAudio, monoSamples, runWorker, mlEnabled, mergeMlAnalysis,
    analyzeFile, redecode, redecodeRegions
  };
})(window);
