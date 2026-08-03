(function (global) {
  "use strict";

  const WORKER_URL = "/ui/practice-analysis-worker-key-regions-v6.js";

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

  function runWorker(message, transfer = [], onProgress = () => {}) {
    return new Promise((resolve, reject) => {
      const worker = new Worker(WORKER_URL);
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

  async function analyzeFile(file, options = {}, onProgress = () => {}, signal) {
    const decoded = await decodeAudio(file);
    const samples = monoSamples(decoded);
    const durationMs = Math.round(Number(decoded.duration) * 1000);
    const analysis = await runWorker({ type: "analyze", samples: samples.buffer, sampleRate: decoded.sampleRate, durationMs, options, signal }, [samples.buffer], onProgress);
    return { analysis, durationMs };
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

  global.STEEL_RAG_ANALYSIS_CLIENT = { WORKER_URL, decodeAudio, monoSamples, runWorker, analyzeFile, redecode, redecodeRegions };
})(window);
