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

  function overlapMs(start, end, segment) {
    return Math.max(0, Math.min(end, Number(segment.endMs)) - Math.max(start, Number(segment.startMs)));
  }

  function dominantSegment(segments, start, end, symbolKey) {
    const values = new Map();
    (segments || []).forEach((segment) => {
      const duration = overlapMs(start, end, segment);
      if (!duration) return;
      const symbol = String(segment[symbolKey] || segment.symbol || segment.finalSymbol || "N.C.");
      const current = values.get(symbol) || { duration: 0, confidenceMass: 0 };
      current.duration += duration;
      current.confidenceMass += duration * Number(segment.confidence || 0);
      values.set(symbol, current);
    });
    if (!values.size) return null;
    const [symbol, value] = [...values.entries()].sort((left, right) => right[1].duration - left[1].duration)[0];
    return {
      symbol,
      coverage: value.duration / Math.max(1, end - start),
      confidence: value.confidenceMass / Math.max(1, value.duration)
    };
  }

  function hybridSegments(base, ml) {
    const durationMs = Number(base.durationMs);
    let leadingEnd = 0, leadingConfidenceMass = 0;
    for (const segment of [...(base.chords || [])].sort((left, right) => Number(left.startMs) - Number(right.startMs))) {
      const start = Number(segment.startMs), end = Number(segment.endMs), confidence = Number(segment.confidence || 0);
      if (start > leadingEnd + 50 || String(segment.symbol || segment.finalSymbol) !== "N.C." || confidence < 0.75) break;
      leadingConfidenceMass += (end - start) * confidence;
      leadingEnd = end;
    }
    let studentConfidenceMass = 0, studentDuration = 0;
    (ml.segments || []).forEach((segment) => {
      const duration = overlapMs(0, leadingEnd, segment);
      studentConfidenceMass += duration * Number(segment.confidence || 0);
      studentDuration += duration;
    });
    const studentMeanConfidence = studentConfidenceMass / Math.max(1, studentDuration);
    const noChord = leadingEnd >= 3000 && studentDuration > 0 && studentMeanConfidence <= 0.32
      ? [{ startMs: 0, endMs: leadingEnd, confidence: leadingConfidenceMass / Math.max(1, leadingEnd) }]
      : [];
    const boundaries = new Set([0, durationMs]);
    (ml.segments || []).forEach((segment) => { boundaries.add(Number(segment.startMs)); boundaries.add(Number(segment.endMs)); });
    noChord.forEach((segment) => { boundaries.add(Number(segment.startMs)); boundaries.add(Number(segment.endMs)); });
    const ordered = [...boundaries].filter((value) => value >= 0 && value <= durationMs).sort((left, right) => left - right);
    const output = [];
    for (let index = 0; index + 1 < ordered.length; index += 1) {
      const startMs = ordered[index], endMs = ordered[index + 1];
      if (endMs <= startMs) continue;
      const midpoint = startMs + (endMs - startMs) / 2;
      const silence = noChord.find((segment) => Number(segment.startMs) <= midpoint && midpoint < Number(segment.endMs));
      const student = dominantSegment(ml.segments, startMs, endMs, "symbol");
      const fallback = dominantSegment(base.chords, startMs, endMs, "symbol");
      const value = silence
        ? { symbol: "N.C.", confidence: Number(silence.confidence || 0), sourceEngine: "v2-no-chord" }
        : student
          ? { symbol: student.symbol, confidence: student.confidence, sourceEngine: "student" }
          : { symbol: fallback?.symbol || "N.C.", confidence: fallback?.confidence || 0, sourceEngine: "v2-fallback" };
      const previous = output.at(-1);
      if (previous && previous.symbol === value.symbol && previous.sourceEngine === value.sourceEngine) {
        const previousDuration = previous.endMs - previous.startMs, currentDuration = endMs - startMs;
        previous.confidence = (previous.confidence * previousDuration + value.confidence * currentDuration) / Math.max(1, previousDuration + currentDuration);
        previous.endMs = endMs;
      } else output.push({ startMs, endMs, ...value });
    }
    return output;
  }

  function mergeMlAnalysis(base, ml) {
    if (!Array.isArray(ml?.segments) || !ml.segments.length) throw new Error("The ML reader returned no chord segments.");
    const barStarts = Array.isArray(base.barStartsMs) ? base.barStartsMs.map(Number) : [];
    const chords = hybridSegments(base, ml).map((segment, index) => {
      let barIndex = 0;
      barStarts.forEach((start, candidate) => { if (start <= segment.startMs) barIndex = candidate; });
      const confidence = Number(segment.confidence || 0);
      const reviewed = segment.sourceEngine === "v2-no-chord" || confidence >= 0.8;
      const symbol = String(segment.symbol || "N.C.");
      return {
        id: `hybrid-chord-${index + 1}`,
        bar: barIndex + 1,
        startFraction: barStarts.length ? Math.max(0, Math.min(1, (segment.startMs - barStarts[barIndex]) / Math.max(1, Number(barStarts[barIndex + 1] ?? base.durationMs) - barStarts[barIndex]))) : 0,
        startMs: segment.startMs, endMs: segment.endMs, symbol, rawCandidate: symbol, finalSymbol: symbol,
        alternatives: [], confidence, contextualAdjusted: false, rootAdjusted: false, qualityAdjusted: false,
        rootStatus: symbol === "N.C." ? "no_chord" : "audio_supported",
        qualityStatus: "audio_supported", publicationSymbol: reviewed ? symbol : null,
        sequenceConfidence: confidence,
        reviewReasons: [segment.sourceEngine === "v2-no-chord" ? "The timing reader strongly supports a no-chord region." : reviewed ? "The supervised audio model strongly supports this bar-level chord." : "The supervised audio model is uncertain; review this bar-level chord."],
        reviewed, needsAttention: !reviewed, sourceEngine: segment.sourceEngine
      };
    });
    return { ...base, analysisVersion: 3, chordReaderEngine: "hybrid-v1", mlModel: ml.engine, chords };
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
    WORKER_URL, ML_WORKER_URL, ML_FEATURE_FLAG, decodeAudio, monoSamples, runWorker, mlEnabled, dominantSegment, hybridSegments, mergeMlAnalysis,
    analyzeFile, redecode, redecodeRegions
  };
})(window);
