"use strict";

// Deterministic publication helpers for song charts.  The audio reader may
// propose harmony, but this layer decides what is safe to put in front of a
// learner and can align a separately supplied, rights-reviewed reference
// chart without making network requests.

const ROOT_PATTERN = /^([A-G](?:#|b)?)/;
const ROOT_VALUES = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };

function chordRoot(symbol) {
  if (symbol === "N.C." || symbol === "—" || !symbol) return symbol || null;
  return ROOT_PATTERN.exec(String(symbol))?.[1] || null;
}

function chordQuality(symbol) {
  const root = chordRoot(symbol);
  if (!root) return symbol === "N.C." ? "none" : "unknown";
  const suffix = String(symbol).slice(root.length);
  if (suffix === "m" || suffix === "m7") return suffix;
  if (suffix === "7" || suffix === "maj7" || suffix === "5") return suffix;
  return suffix ? "unknown" : "major";
}

function rootOnlySymbol(symbol) {
  if (symbol === "N.C.") return symbol;
  return chordRoot(symbol);
}

function learnerClaimForAnalysisChord(chord) {
  const rawSymbol = chord.rawCandidate || chord.symbol;
  const selectedRoot = chordRoot(chord.symbol);
  const rawRoot = chordRoot(rawSymbol);
  const rootAdjusted = chord.rootAdjusted ?? (
    Boolean(chord.contextualAdjusted) && selectedRoot !== rawRoot
  );
  const selectedQuality = chordQuality(chord.symbol);
  const rawQuality = chordQuality(rawSymbol);
  const qualityAdjusted = chord.qualityAdjusted ?? (
    Boolean(chord.contextualAdjusted) && !rootAdjusted && selectedQuality !== rawQuality
  );
  const confidence = Number(chord.confidence || 0);
  let symbol = chord.publicationSymbol || null;
  if (rootAdjusted || confidence < 0.68) symbol = null;
  if (!symbol && !rootAdjusted && selectedRoot && confidence >= 0.7) {
    symbol = selectedQuality === "m" || selectedQuality === "m7" ? `${selectedRoot}m` : selectedRoot;
  }
  if (chord.symbol === "N.C." && !chord.contextualAdjusted && confidence >= 0.82) symbol = "N.C.";
  return {
    symbol,
    root: selectedRoot,
    quality: symbol ? chordQuality(symbol) : "unresolved",
    rawSymbol,
    rootStatus: rootAdjusted ? "context_only" : chord.rootStatus || "audio_supported",
    qualityStatus: qualityAdjusted ? "context_only" : chord.qualityStatus || "audio_supported",
    confidence: rootAdjusted ? Math.min(confidence, 0.64) : qualityAdjusted ? Math.min(confidence, 0.74) : confidence,
    needsAttention: !symbol || rootAdjusted || qualityAdjusted || Boolean(chord.needsAttention),
    reviewReasons: Array.from(new Set([
      ...(chord.reviewReasons || []),
      ...(rootAdjusted ? ["The decoded root conflicts with the strongest audio candidate."] : []),
      ...(qualityAdjusted ? ["The chord quality is supplied by context rather than direct audio evidence."] : []),
    ])),
  };
}

function validateReference(reference) {
  if (!reference || reference.schemaVersion !== "song_chart_reference_v1") {
    throw new Error("The song reference must use song_chart_reference_v1.");
  }
  if (reference.gridUnit !== "quarter_note" || !Number.isInteger(reference.gridLength) || reference.gridLength < 1) {
    throw new Error("The song reference must define a positive quarter-note grid.");
  }
  if (!Number.isFinite(Number(reference.tempoBpm)) || Number(reference.tempoBpm) < 30) {
    throw new Error("The song reference must define a plausible tempo.");
  }
  if (!Array.isArray(reference.sources) || reference.sources.length < 1) {
    throw new Error("The song reference needs at least one named source.");
  }
  const runs = reference.runs || [];
  let cursor = 0;
  for (const run of runs) {
    if (
      Number(run.startBeat) !== cursor
      || !Number.isInteger(Number(run.endBeat))
      || Number(run.endBeat) <= Number(run.startBeat)
      || Number(run.endBeat) > reference.gridLength
      || !String(run.symbol || "").trim()
    ) throw new Error("Reference chord runs must be contiguous and cover the grid exactly.");
    cursor = Number(run.endBeat);
  }
  if (!runs.length || cursor !== reference.gridLength) {
    throw new Error("Reference chord runs must cover the complete grid.");
  }
  const sections = reference.sections || [];
  cursor = 0;
  for (const section of sections) {
    if (
      Number(section.startBeat) !== cursor
      || Number(section.endBeat) <= Number(section.startBeat)
      || Number(section.endBeat) > reference.gridLength
      || !String(section.id || "").trim()
      || !String(section.label || "").trim()
    ) throw new Error("Reference sections must be contiguous and cover the grid exactly.");
    cursor = Number(section.endBeat);
  }
  if (!sections.length || cursor !== reference.gridLength) {
    throw new Error("Reference sections must cover the complete grid.");
  }
  return reference;
}

function alignmentAnchors(reference, companion) {
  const durationMs = Number(companion.media.scopes.fullSong.durationMs);
  const anchors = [
    { beat: 0, ms: 0, source: "recording_start" },
    { beat: reference.gridLength, ms: durationMs, source: "recording_end" },
  ];
  const scopeMappings = reference.scopeMappings || {};
  Object.entries(scopeMappings).forEach(([scopeName, mapping]) => {
    const scope = companion.media.scopes[scopeName];
    if (!scope) throw new Error(`Reference scope ${scopeName} does not exist in the companion.`);
    anchors.push(
      { beat: Number(mapping.startBeat), ms: Number(scope.startMs), source: `${scopeName}_start` },
      { beat: Number(mapping.endBeat), ms: Number(scope.endMs), source: `${scopeName}_end` },
    );
  });
  const byBeat = new Map();
  anchors.forEach((anchor) => {
    if (!Number.isFinite(anchor.beat) || !Number.isFinite(anchor.ms)) throw new Error("Reference alignment anchors must be numeric.");
    if (byBeat.has(anchor.beat) && byBeat.get(anchor.beat).ms !== anchor.ms) {
      throw new Error(`Reference beat ${anchor.beat} has conflicting recording anchors.`);
    }
    byBeat.set(anchor.beat, anchor);
  });
  const sorted = [...byBeat.values()].sort((left, right) => left.beat - right.beat);
  sorted.forEach((anchor, index) => {
    if (index && anchor.ms <= sorted[index - 1].ms) throw new Error("Reference alignment anchors must increase in time.");
  });
  return sorted;
}

function timeAtReferenceBeat(beat, anchors) {
  const exact = anchors.find((anchor) => anchor.beat === beat);
  if (exact) return Math.round(exact.ms);
  let rightIndex = anchors.findIndex((anchor) => anchor.beat > beat);
  if (rightIndex < 0) rightIndex = anchors.length - 1;
  const right = anchors[rightIndex];
  const left = anchors[Math.max(0, rightIndex - 1)];
  const progress = (beat - left.beat) / Math.max(1, right.beat - left.beat);
  return Math.round(left.ms + (right.ms - left.ms) * progress);
}

function median(values) {
  const sorted = values.filter(Number.isFinite).sort((left, right) => left - right);
  if (!sorted.length) return 0;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function cosine(left, right) {
  let dot = 0;
  let leftSize = 0;
  let rightSize = 0;
  for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
    dot += Number(left[index] || 0) * Number(right[index] || 0);
    leftSize += Number(left[index] || 0) ** 2;
    rightSize += Number(right[index] || 0) ** 2;
  }
  return dot / Math.sqrt(Math.max(1e-12, leftSize * rightSize));
}

function rootFit(chroma, symbol) {
  const root = chordRoot(symbol);
  if (root === "N.C." || root === "—" || ROOT_VALUES[root] === undefined) return null;
  const value = ROOT_VALUES[root];
  return Number(chroma[value] || 0)
    + Number(chroma[(value + 7) % 12] || 0) * 0.48
    + Math.max(Number(chroma[(value + 3) % 12] || 0), Number(chroma[(value + 4) % 12] || 0)) * 0.24;
}

function transitionEvidenceScore(evidence, previousSymbol, nextSymbol) {
  if (!evidence) return 0;
  const beforePrevious = rootFit(evidence.beforeChroma || [], previousSymbol);
  const afterPrevious = rootFit(evidence.afterChroma || [], previousSymbol);
  const beforeNext = rootFit(evidence.beforeChroma || [], nextSymbol);
  const afterNext = rootFit(evidence.afterChroma || [], nextSymbol);
  const novelty = 1 - cosine(evidence.beforeChroma || [], evidence.afterChroma || []);
  if ([beforePrevious, afterPrevious, beforeNext, afterNext].every(Number.isFinite)) {
    return (beforePrevious - afterPrevious) + (afterNext - beforeNext) + novelty * 0.18;
  }
  if (previousSymbol === "N.C." && Number.isFinite(afterNext)) {
    return (Number(evidence.afterEnergy || 0) - Number(evidence.beforeEnergy || 0)) * 2 + afterNext * 0.2;
  }
  return novelty * 0.08;
}

function boundarySymbols(reference, beat) {
  const previous = reference.runs.find((run) => Number(run.endBeat) === Number(beat));
  const next = reference.runs.find((run) => Number(run.startBeat) === Number(beat));
  return { previousSymbol: previous?.symbol || null, nextSymbol: next?.symbol || null };
}

function globallyAlignedBoundaryTimes(reference, anchors, beatTimesInput, beatEvidenceInput) {
  const detectedBeats = [...new Set((beatTimesInput || []).map(Number).filter(Number.isFinite))]
    .sort((left, right) => left - right);
  const evidenceByTime = new Map((beatEvidenceInput || []).map((item) => [Number(item.timeMs), item]));
  const typicalBeatMs = median(detectedBeats.slice(1).map((time, index) => time - detectedBeats[index]));
  const boundaryBeats = [...new Set([
    ...reference.runs.flatMap((run) => [Number(run.startBeat), Number(run.endBeat)]),
    ...reference.sections.flatMap((section) => [Number(section.startBeat), Number(section.endBeat)]),
    ...anchors.map((anchor) => Number(anchor.beat)),
  ])].sort((left, right) => left - right);
  const anchorsByBeat = new Map(anchors.map((anchor) => [Number(anchor.beat), Number(anchor.ms)]));
  const candidateRadiusMs = typicalBeatMs ? typicalBeatMs * 1.08 : 0;
  const points = boundaryBeats.map((beat) => {
    const coarseMs = timeAtReferenceBeat(beat, anchors);
    if (anchorsByBeat.has(beat) || !detectedBeats.length) {
      return { beat, coarseMs, candidates: [{ timeMs: coarseMs, evidenceScore: 0, deviationMs: 0 }] };
    }
    const symbols = boundarySymbols(reference, beat);
    let candidates = detectedBeats.filter((timeMs) => Math.abs(timeMs - coarseMs) <= candidateRadiusMs);
    if (!candidates.length) {
      candidates = [detectedBeats.reduce((picked, timeMs) => (
        Math.abs(timeMs - coarseMs) < Math.abs(picked - coarseMs) ? timeMs : picked
      ), detectedBeats[0])];
    }
    return {
      beat,
      coarseMs,
      candidates: candidates.map((timeMs) => ({
        timeMs,
        deviationMs: timeMs - coarseMs,
        evidenceScore: transitionEvidenceScore(evidenceByTime.get(timeMs), symbols.previousSymbol, symbols.nextSymbol),
      })),
    };
  });
  const rows = [];
  points.forEach((point, pointIndex) => {
    const previousPoint = points[pointIndex - 1];
    const previousRow = rows[pointIndex - 1];
    const row = point.candidates.map((candidate) => {
      const normalizedDeviation = typicalBeatMs ? Math.abs(candidate.deviationMs) / typicalBeatMs : 0;
      const localCost = normalizedDeviation ** 2 * 0.24 - candidate.evidenceScore * 1.35;
      if (!previousRow) return { cost: localCost, previousIndex: -1 };
      let best = { cost: Infinity, previousIndex: -1 };
      previousRow.forEach((previous, previousIndex) => {
        const previousCandidate = previousPoint.candidates[previousIndex];
        if (candidate.timeMs <= previousCandidate.timeMs) return;
        const expectedInterval = point.coarseMs - previousPoint.coarseMs;
        const actualInterval = candidate.timeMs - previousCandidate.timeMs;
        const intervalPenalty = typicalBeatMs
          ? Math.abs(actualInterval - expectedInterval) / typicalBeatMs * 0.055
          : 0;
        const cost = previous.cost + localCost + intervalPenalty;
        if (cost < best.cost) best = { cost, previousIndex };
      });
      return best;
    });
    if (!row.some((item) => Number.isFinite(item.cost))) {
      throw new Error(`No monotonic audio-beat path reaches reference beat ${point.beat}.`);
    }
    rows.push(row);
  });
  let candidateIndex = rows.at(-1).reduce((bestIndex, item, index, items) => (
    item.cost < items[bestIndex].cost ? index : bestIndex
  ), 0);
  const selected = new Map();
  for (let pointIndex = points.length - 1; pointIndex >= 0; pointIndex -= 1) {
    const point = points[pointIndex];
    const candidate = point.candidates[candidateIndex];
    selected.set(point.beat, candidate);
    candidateIndex = rows[pointIndex][candidateIndex].previousIndex;
  }
  const selectedValues = [...selected.values()];
  const adjustments = selectedValues.filter((item) => item.deviationMs !== 0);
  const comparisons = points
    .filter((point) => !anchorsByBeat.has(point.beat))
    .map((point) => {
      const baseline = point.candidates.reduce((picked, candidate) => (
        Math.abs(candidate.deviationMs) < Math.abs(picked.deviationMs) ? candidate : picked
      ), point.candidates[0]);
      return { baseline, selected: selected.get(point.beat) };
    });
  const selectedScore = comparisons.reduce((total, item) => total + item.selected.evidenceScore, 0);
  const baselineScore = comparisons.reduce((total, item) => total + item.baseline.evidenceScore, 0);
  return {
    selected,
    diagnostics: {
      method: "global_harmonic_transition_constrained_beat_alignment",
      detectedBeatCount: detectedBeats.length,
      typicalBeatMs: Math.round(typicalBeatMs),
      alignedBoundaryCount: adjustments.length,
      meanAbsoluteAdjustmentMs: adjustments.length
        ? Math.round(adjustments.reduce((total, item) => total + Math.abs(item.deviationMs), 0) / adjustments.length)
        : 0,
      maxAbsoluteAdjustmentMs: adjustments.length
        ? Math.round(Math.max(...adjustments.map((item) => Math.abs(item.deviationMs))))
        : 0,
      musicallyScoredBoundaryCount: selectedValues.filter((item) => item.evidenceScore !== 0).length,
      neighboringBeatShiftCount: comparisons.filter((item) => item.selected.timeMs !== item.baseline.timeMs).length,
      harmonicEvidenceGain: Math.round((selectedScore - baselineScore) * 1000) / 1000,
    },
  };
}

function referenceTimeMapper(anchors, beatTimesInput = []) {
  const detectedBeats = [...new Set((beatTimesInput || []).map(Number).filter(Number.isFinite))]
    .sort((left, right) => left - right);
  const exactAnchorBeats = new Set(anchors.map((anchor) => Number(anchor.beat)));
  const typicalBeatMs = median(detectedBeats.slice(1).map((time, index) => time - detectedBeats[index]));
  const maxSnapDistanceMs = typicalBeatMs ? typicalBeatMs * 0.55 : 0;
  const adjustments = new Map();

  const nearestDetectedBeat = (timeMs) => {
    let low = 0;
    let high = detectedBeats.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (detectedBeats[middle] < timeMs) low = middle + 1;
      else high = middle;
    }
    const candidates = [detectedBeats[low - 1], detectedBeats[low]].filter(Number.isFinite);
    return candidates.sort((left, right) => Math.abs(left - timeMs) - Math.abs(right - timeMs))[0];
  };

  const timeAtBeat = (beat) => {
    const coarseMs = timeAtReferenceBeat(beat, anchors);
    if (!detectedBeats.length || exactAnchorBeats.has(Number(beat))) return coarseMs;
    const snappedMs = nearestDetectedBeat(coarseMs);
    const adjustmentMs = Number(snappedMs) - coarseMs;
    const accepted = Number.isFinite(snappedMs) && Math.abs(adjustmentMs) <= maxSnapDistanceMs;
    adjustments.set(Number(beat), { coarseMs, snappedMs, adjustmentMs, accepted });
    return accepted ? Math.round(snappedMs) : coarseMs;
  };

  const diagnostics = () => {
    const values = [...adjustments.values()];
    const accepted = values.filter((item) => item.accepted);
    const absolute = accepted.map((item) => Math.abs(item.adjustmentMs));
    return {
      detectedBeatCount: detectedBeats.length,
      typicalBeatMs: Math.round(typicalBeatMs),
      snappedBoundaryCount: accepted.length,
      unsnappedBoundaryCount: values.length - accepted.length,
      meanAbsoluteAdjustmentMs: absolute.length
        ? Math.round(absolute.reduce((total, value) => total + value, 0) / absolute.length)
        : 0,
      maxAbsoluteAdjustmentMs: absolute.length ? Math.round(Math.max(...absolute)) : 0,
    };
  };
  return { diagnostics, timeAtBeat };
}

function sectionAtBeat(reference, beat) {
  return reference.sections.find((section) => beat >= section.startBeat && beat < section.endBeat)
    || reference.sections.at(-1);
}

function splitReferenceRuns(reference) {
  const splitPoints = new Set(reference.sections.flatMap((section) => [section.startBeat, section.endBeat]));
  return reference.runs.flatMap((run) => {
    const points = [run.startBeat, ...[...splitPoints].filter((point) => point > run.startBeat && point < run.endBeat), run.endBeat]
      .sort((left, right) => left - right);
    return points.slice(0, -1).map((startBeat, index) => ({ ...run, startBeat, endBeat: points[index + 1] }));
  });
}

function alignReferenceChart(referenceInput, companion, nnsForSymbol, beatTimesMs = [], beatEvidence = []) {
  const reference = validateReference(referenceInput);
  const anchors = alignmentAnchors(reference, companion);
  const globalAlignment = beatEvidence.length
    ? globallyAlignedBoundaryTimes(reference, anchors, beatTimesMs, beatEvidence)
    : null;
  const timeMapper = globalAlignment
    ? {
      timeAtBeat: (beat) => globalAlignment.selected.get(Number(beat))?.timeMs ?? timeAtReferenceBeat(beat, anchors),
      diagnostics: () => globalAlignment.diagnostics,
    }
    : referenceTimeMapper(anchors, beatTimesMs);
  const corroboratedRoots = new Set(reference.corroboratedRoots || []);
  const useRootsOnly = reference.qualityPolicy === "roots_only";
  const timeline = splitReferenceRuns(reference).map((run) => {
    const section = sectionAtBeat(reference, run.startBeat);
    const observedSymbol = run.symbol;
    const symbol = useRootsOnly ? rootOnlySymbol(observedSymbol) : observedSymbol;
    const corroborated = symbol === "N.C." || corroboratedRoots.has(chordRoot(symbol));
    return {
      startMs: timeMapper.timeAtBeat(run.startBeat),
      endMs: timeMapper.timeAtBeat(run.endBeat),
      referenceStartBeat: Number(run.startBeat),
      referenceEndBeat: Number(run.endBeat),
      sectionId: section.id,
      sectionLabel: section.label,
      symbol: symbol || "—",
      observedSymbol,
      nns: symbol ? nnsForSymbol(symbol, companion.display.key) : "—",
      verified: false,
      needsAttention: !corroborated,
      confidence: corroborated ? 0.9 : 0.62,
      rootStatus: corroborated ? "multi_source_supported" : "single_source_only",
      qualityStatus: useRootsOnly ? "withheld" : "reference_supported",
      reviewReasons: corroborated
        ? ["The chord root appears in both reviewed public chart references."]
        : ["This chord claim appears in only one reviewed public chart reference."],
      sourceKind: "aligned_multi_source_chart_reference",
      status: "reference_consensus_review_required",
    };
  }).reduce((merged, event) => {
    const previous = merged.at(-1);
    if (previous && previous.symbol === event.symbol && previous.sectionId === event.sectionId) {
      previous.endMs = event.endMs;
      previous.referenceEndBeat = event.referenceEndBeat;
      previous.observedSymbols = [...new Set([...previous.observedSymbols, event.observedSymbol])];
      previous.needsAttention ||= event.needsAttention;
      previous.confidence = Math.min(previous.confidence, event.confidence);
      return merged;
    }
    merged.push({
      ...event,
      observedSymbols: [event.observedSymbol],
    });
    return merged;
  }, []).map((event, index) => ({
    ...event,
    id: `reference-chord-${String(index + 1).padStart(3, "0")}`,
  }));
  const sections = reference.sections.map((section) => ({
    id: section.id,
    label: section.label,
    startMs: timeMapper.timeAtBeat(section.startBeat),
    endMs: timeMapper.timeAtBeat(section.endBeat),
    referenceStartBeat: section.startBeat,
    referenceEndBeat: section.endBeat,
    sourceKind: "reviewed_public_song_form",
  }));
  return {
    timeline,
    sections,
    alignment: {
      method: globalAlignment
        ? "global_harmonic_transition_constrained_beat_alignment"
        : beatTimesMs.length
        ? "audio_beat_snapped_reference_grid_with_lesson_scope_anchors"
        : "piecewise_reference_grid_with_lesson_scope_anchors",
      anchors,
      beatSnap: timeMapper.diagnostics(),
      gridUnit: reference.gridUnit,
      gridLength: reference.gridLength,
      tempoBpm: Number(reference.tempoBpm),
      sources: reference.sources,
    },
  };
}

function applyScopeChordCorrections(companion, reference, nnsForSymbol) {
  for (const correction of reference.scopeChordCorrections || []) {
    const chord = companion.chordTimeline.find((item) => item.id === correction.chordId);
    if (!chord) throw new Error(`Scope chord correction ${correction.chordId} does not match the companion.`);
    if (!Array.isArray(correction.evidenceSourceIds) || correction.evidenceSourceIds.length < 2) {
      throw new Error(`Scope chord correction ${correction.chordId} needs two independent evidence sources.`);
    }
    const sourceIds = new Set(reference.sources.map((source) => source.id));
    if (correction.evidenceSourceIds.some((sourceId) => !sourceIds.has(sourceId))) {
      throw new Error(`Scope chord correction ${correction.chordId} cites an unknown source.`);
    }
    const oldId = chord.id;
    Object.assign(chord, correction.patch || {});
    chord.id = correction.newId || oldId;
    chord.symbol = correction.symbol;
    chord.nns = correction.nns || nnsForSymbol(correction.symbol, companion.display.key);
    chord.verified = false;
    chord.needsAttention = true;
    chord.status = "multi_source_correction_owner_review_required";
    chord.reviewReasons = ["Two independent public charts agree on this corrected chord root; partner approval is still required."];
    companion.events.forEach((event) => {
      if (event.chordEventId === oldId) event.chordEventId = chord.id;
    });
  }
}

function inferRepeatedSections(analysis, groupBars = 8) {
  const bars = analysis.analysisState?.bars || [];
  if (!bars.length) return [];
  const chordsByBar = new Map();
  (analysis.chords || []).forEach((chord) => {
    if (!chordsByBar.has(chord.bar)) chordsByBar.set(chord.bar, learnerClaimForAnalysisChord(chord).symbol || "—");
  });
  const signatures = new Map();
  let nextLabel = 0;
  const sections = [];
  for (let start = 0; start < bars.length; start += groupBars) {
    const end = Math.min(bars.length, start + groupBars);
    const signature = Array.from({ length: end - start }, (_item, index) => rootOnlySymbol(chordsByBar.get(start + index + 1)) || "—").join("|");
    if (!signatures.has(signature)) {
      signatures.set(signature, String.fromCharCode(65 + nextLabel));
      nextLabel += 1;
    }
    const formLabel = signatures.get(signature);
    const repeat = sections.some((section) => section.formLabel === formLabel);
    sections.push({
      id: `form-${String(sections.length + 1).padStart(2, "0")}`,
      label: repeat ? `Form ${formLabel} · repeat` : `Form ${formLabel}`,
      formLabel,
      startBar: start + 1,
      endBar: end,
      startMs: Number(bars[start].startMs),
      endMs: Number(bars[end - 1].endMs),
      sourceKind: "deterministic_repetition_group",
    });
  }
  return sections;
}

module.exports = {
  alignReferenceChart,
  applyScopeChordCorrections,
  chordQuality,
  chordRoot,
  inferRepeatedSections,
  learnerClaimForAnalysisChord,
  rootOnlySymbol,
  validateReference,
};
