(function exposeChordPhaseAnchor(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.ChordPhaseAnchor = api;
})(typeof globalThis === "object" ? globalThis : this, function buildApi() {
  "use strict";

  const DEFAULTS = Object.freeze({
    minimumAnchors: 8,
    minimumMargin: 0.12,
    maximumBeatDistance: 0.38,
    minimumBeforeBeats: 0.8,
    minimumAfterBeats: 1.2,
    minimumConfidence: 0.62,
    introSeconds: 8,
    introBeats: 16,
  });

  function mod(value, divisor) {
    return ((value % divisor) + divisor) % divisor;
  }

  function median(values) {
    if (!values.length) return 0;
    const ordered = [...values].sort((left, right) => left - right);
    const middle = Math.floor(ordered.length / 2);
    return ordered.length % 2
      ? ordered[middle]
      : (ordered[middle - 1] + ordered[middle]) / 2;
  }

  function beatPeriod(beatTimes) {
    return median(
      beatTimes
        .slice(1)
        .map((time, index) => Number(time) - Number(beatTimes[index]))
        .filter((distance) => distance > 0.15 && distance < 2),
    );
  }

  function chordRoot(segment) {
    const symbol = String(
      segment?.productLabel || segment?.label || "",
    ).trim();
    if (/^(N\.?C\.?|N)$/iu.test(symbol)) return null;
    return symbol.match(/^([A-G](?:#|b)?)/u)?.[1] || null;
  }

  function nearestBeatIndex(beatTimes, seconds) {
    let bestIndex = -1;
    let bestDistance = Infinity;
    beatTimes.forEach((time, index) => {
      const distance = Math.abs(Number(time) - seconds);
      if (distance < bestDistance) {
        bestDistance = distance;
        bestIndex = index;
      }
    });
    return { index: bestIndex, distance: bestDistance };
  }

  function collectAnchors(segments, beatTimes, options = {}) {
    const settings = { ...DEFAULTS, ...options };
    const period = beatPeriod(beatTimes);
    if (!period || beatTimes.length < 8) return { anchors: [], period };
    const ignoreBefore = Math.max(
      settings.introSeconds,
      Number(beatTimes[0]) + settings.introBeats * period,
    );
    const anchors = [];
    for (let index = 1; index < segments.length; index += 1) {
      const before = segments[index - 1];
      const after = segments[index];
      const changeTime = Number(after.start);
      const beforeRoot = chordRoot(before);
      const afterRoot = chordRoot(after);
      if (
        changeTime < ignoreBefore ||
        !beforeRoot ||
        !afterRoot ||
        beforeRoot === afterRoot ||
        Number(before.confidence) < settings.minimumConfidence ||
        Number(after.confidence) < settings.minimumConfidence
      )
        continue;
      const beforeBeats =
        (Number(before.end) - Number(before.start)) / period;
      const afterBeats = (Number(after.end) - Number(after.start)) / period;
      if (
        beforeBeats < settings.minimumBeforeBeats ||
        afterBeats < settings.minimumAfterBeats
      )
        continue;
      const nearest = nearestBeatIndex(beatTimes, changeTime);
      const distanceBeats = nearest.distance / period;
      if (distanceBeats > settings.maximumBeatDistance) continue;
      anchors.push({
        segmentIndex: index,
        time: changeTime,
        beatIndex: nearest.index,
        distanceBeats,
        beforeRoot,
        afterRoot,
        weight:
          Math.min(4, afterBeats) *
          Math.min(Number(before.confidence), Number(after.confidence)) *
          Math.max(0, 1 - distanceBeats / settings.maximumBeatDistance),
      });
    }
    return { anchors, period };
  }

  function phaseScores(anchors, beatsPerBar) {
    const positionWeights = [1, -0.45, 0.35, -0.45];
    return Array.from({ length: beatsPerBar }, (_unused, phase) =>
      anchors.reduce((score, anchor) => {
        const position = mod(anchor.beatIndex - phase, beatsPerBar);
        return score +
          anchor.weight * (positionWeights[position] ?? -0.45);
      }, 0),
    );
  }

  function inferPhase(segments, beatTimes, beatsPerBar = 4, options = {}) {
    const settings = { ...DEFAULTS, ...options };
    const cleanBeats = beatTimes.map(Number).filter(Number.isFinite);
    const { anchors, period } = collectAnchors(segments, cleanBeats, settings);
    const scores = phaseScores(anchors, beatsPerBar);
    const ranked = scores
      .map((score, phase) => ({ phase, score }))
      .sort((left, right) => right.score - left.score);
    const totalWeight = anchors.reduce((sum, anchor) => sum + anchor.weight, 0);
    const margin = ranked.length > 1 ? ranked[0].score - ranked[1].score : 0;
    const normalizedMargin = totalWeight > 0 ? margin / totalWeight : 0;
    const accepted =
      anchors.length >= settings.minimumAnchors &&
      normalizedMargin >= settings.minimumMargin;
    return {
      source: "sustained-harmonic-anchors-v1",
      status: accepted ? "anchored" : "unresolved",
      downbeatOffsetBeats: accepted ? ranked[0]?.phase || 0 : 0,
      proposedOffsetBeats: ranked[0]?.phase || 0,
      anchorCount: anchors.length,
      confidence: normalizedMargin,
      scores,
      beatPeriodSeconds: period,
      thresholds: {
        minimumAnchors: settings.minimumAnchors,
        minimumMargin: settings.minimumMargin,
      },
    };
  }

  function completeBeatGrid(beatTimes, durationSeconds) {
    const beats = beatTimes.map(Number).filter(Number.isFinite);
    const period = beatPeriod(beats);
    let prependedCount = 0;
    if (period && beats.length) {
      for (let time = beats[0] - period; time >= 0.04; time -= period) {
        beats.unshift(time);
        prependedCount += 1;
      }
      const duration = Number(durationSeconds);
      if (Number.isFinite(duration))
        while (beats.at(-1) + period < duration - 0.04)
          beats.push(beats.at(-1) + period);
    }
    return { beats, period, prependedCount };
  }

  function downbeatTimes(
    beatTimes,
    prependedCount,
    downbeatOffsetBeats,
    beatsPerBar,
  ) {
    const phaseIndex = mod(
      Number(prependedCount) + Number(downbeatOffsetBeats),
      beatsPerBar,
    );
    return beatTimes.filter(
      (_time, index) => mod(index - phaseIndex, beatsPerBar) === 0,
    );
  }

  return {
    DEFAULTS,
    beatPeriod,
    collectAnchors,
    completeBeatGrid,
    downbeatTimes,
    inferPhase,
    mod,
    nearestBeatIndex,
    phaseScores,
  };
});
