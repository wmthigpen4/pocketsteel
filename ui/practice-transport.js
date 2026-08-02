(function (global) {
  "use strict";

  function usePracticeTransport(options) {
    const audio = options.audio;
    let track = options.track || null;
    let loopRange = null;
    let loopEnabled = false;
    let countIn = false;
    let metronome = false;
    let pendingTimers = [];
    let pendingPlay = false;
    let lastBeatIndex = -1;
    let context = null;

    function audioContext() { context ||= new (global.AudioContext || global.webkitAudioContext)(); return context; }
    function click(accent = false) {
      try {
        const ctx = audioContext(); const oscillator = ctx.createOscillator(); const gain = ctx.createGain();
        oscillator.frequency.value = accent ? 1320 : 880; gain.gain.setValueAtTime(0.0001, ctx.currentTime); gain.gain.exponentialRampToValueAtTime(accent ? 0.22 : 0.12, ctx.currentTime + 0.004); gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.055);
        oscillator.connect(gain).connect(ctx.destination); oscillator.start(); oscillator.stop(ctx.currentTime + 0.06);
      } catch (_error) { /* Audio playback remains usable if synthetic clicks are unavailable. */ }
    }
    function cancelPending() { pendingTimers.forEach(global.clearTimeout); pendingTimers = []; pendingPlay = false; }
    function beatTimes() { return global.STEEL_RAG_PRACTICE?.beatTimesForTrack(track) || []; }
    function beatsPerBar() { return global.STEEL_RAG_PRACTICE?.meterBeats(track) || 4; }
    function beatDurationMs() { const beats = beatTimes(); return beats.length > 1 ? Math.max(100, beats[1] - beats[0]) : 60000 / Math.max(40, Number(track?.tempo || 100)); }

    async function play({ automaticLoop = false } = {}) {
      cancelPending();
      const shouldCount = countIn && !automaticLoop && !track?.authoredCountIn && !Number(track?.countInBars || 0);
      if (!shouldCount) return audio.play();
      pendingPlay = true;
      const duration = beatDurationMs();
      for (let beat = 0; beat < beatsPerBar(); beat += 1) pendingTimers.push(global.setTimeout(() => click(beat === 0), beat * duration));
      return new Promise((resolve, reject) => {
        pendingTimers.push(global.setTimeout(() => { pendingPlay = false; audio.play().then(resolve, reject); }, beatsPerBar() * duration));
      });
    }
    function pause() { cancelPending(); audio.pause(); }
    function seek(ms) { cancelPending(); audio.currentTime = Math.max(0, Number(ms || 0)) / 1000; lastBeatIndex = -1; }
    function setRate(rate) { audio.playbackRate = Number(rate); audio.preservesPitch = true; }
    function setVolume(volume) { audio.volume = Number(volume); }
    function setLoop(range, enabled = true) { loopRange = range || null; loopEnabled = Boolean(enabled && range); }
    function setCountIn(enabled) { countIn = Boolean(enabled); if (!countIn) cancelPending(); }
    function setMetronome(enabled) { metronome = Boolean(enabled); lastBeatIndex = -1; }
    function update() {
      const timeMs = audio.currentTime * 1000;
      if (loopEnabled && loopRange && timeMs >= loopRange.endMs - 30) { seek(loopRange.startMs); if (audio.paused && !pendingPlay) play({ automaticLoop: true }).catch(() => {}); }
      if (metronome && !audio.paused) {
        const beats = beatTimes();
        const index = Math.max(-1, beats.findLastIndex((time) => time <= timeMs + 25));
        if (index >= 0 && index !== lastBeatIndex) { lastBeatIndex = index; click(index % beatsPerBar() === 0); }
      }
      return timeMs;
    }
    function load(source, nextTrack) { cancelPending(); track = nextTrack || track; audio.src = source; audio.load(); }
    function destroy() { cancelPending(); audio.pause(); if (context) context.close().catch(() => {}); }
    return { audio, load, play, pause, seek, setRate, setVolume, setLoop, setCountIn, setMetronome, update, cancelPending, destroy, get pendingCountIn() { return pendingPlay; } };
  }

  global.usePracticeTransport = usePracticeTransport;
  if (typeof module !== "undefined" && module.exports) module.exports = { usePracticeTransport };
})(typeof window !== "undefined" ? window : globalThis);
