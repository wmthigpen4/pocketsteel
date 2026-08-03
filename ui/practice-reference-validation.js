(function (global) {
  "use strict";

  const ROOTS = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };
  const CANONICAL_ROOTS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
  const providers = new Map();

  function registerProvider(provider) {
    if (!provider?.id || typeof provider.loadReference !== "function") throw new Error("A reference provider requires an id and loadReference function.");
    providers.set(provider.id, Object.freeze({ ...provider }));
  }

  async function loadProviderReference(providerId, request) {
    const provider = providers.get(providerId);
    if (!provider) throw new Error(`Unknown chord reference provider: ${providerId}`);
    const result = await provider.loadReference(request || {});
    if (!result?.reference?.sequence?.length) throw new Error("The reference provider returned no chord symbols.");
    return result;
  }

  function normalizeChordSymbol(value) {
    const token = String(value || "")
      .trim()
      .replace(/[♯]/g, "#")
      .replace(/[♭]/g, "b")
      .replace(/^[\[({]+|[\])},.;:]+$/g, "");
    if (/^(?:N\.?C\.?|NC)$/i.test(token)) return "N.C.";
    const match = token.match(/^([A-Ga-g])([#b]?)(maj7|M7|min7|m7|maj|M|min|m|7)?(?:\/[A-Ga-g][#b]?)?$/);
    if (!match) return null;
    const root = `${match[1].toUpperCase()}${match[2] || ""}`;
    const pitchClass = ROOTS[root];
    if (!Number.isInteger(pitchClass)) return null;
    const qualityToken = match[3] || "";
    let quality = "";
    if (/^(?:min|m)$/i.test(qualityToken)) quality = "m";
    else if (/^(?:min7|m7)$/i.test(qualityToken)) quality = "m7";
    else if (qualityToken === "7") quality = "7";
    else if (/^(?:maj7|M7)$/.test(qualityToken)) quality = "maj7";
    return `${CANONICAL_ROOTS[pitchClass]}${quality}`;
  }

  function chordTokensForLine(line) {
    const bracketed = [...String(line || "").matchAll(/\[([^\]]+)\]/g)]
      .map((match) => normalizeChordSymbol(match[1]))
      .filter(Boolean);
    if (bracketed.length) return bracketed;
    const rawTokens = String(line || "").trim().split(/\s+/).filter(Boolean);
    const chordTokens = rawTokens.map(normalizeChordSymbol).filter(Boolean);
    const contentTokens = rawTokens.filter((token) => !/^[|/%:,-]+$/.test(token));
    if (!chordTokens.length) return [];
    if (chordTokens.length === contentTokens.length || chordTokens.length >= 2 && chordTokens.length / Math.max(1, contentTokens.length) >= 0.6) return chordTokens;
    return [];
  }

  function parseReferenceText(text) {
    const lines = String(text || "").split(/\r?\n/);
    const bars = [];
    let previousBar = [];
    lines.filter((line) => line.includes("|")).forEach((line) => {
      const segments = line.split("|");
      (line.trimStart().startsWith("|") ? segments.slice(1) : segments).forEach((segment) => {
        if (!segment.trim()) return;
        if (/^\s*%\s*$/.test(segment)) {
          if (previousBar.length) bars.push([...previousBar]);
          return;
        }
        const tokens = chordTokensForLine(segment).slice(0, 2);
        if (!tokens.length) return;
        previousBar = tokens;
        bars.push(tokens);
      });
    });
    const sequence = bars.length ? bars.flat() : lines.flatMap(chordTokensForLine);
    return { bars, sequence, vocabulary: [...new Set(sequence)] };
  }

  function referenceDigest(reference) {
    const canonical = JSON.stringify({ bars: reference.bars || [], sequence: reference.sequence || [] });
    let hash = 2166136261;
    for (let index = 0; index < canonical.length; index += 1) {
      hash ^= canonical.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return `chords-${(hash >>> 0).toString(16).padStart(8, "0")}`;
  }

  function eventsForBar(timeline, bar) {
    return (timeline.chords || []).filter((event) => Number(event.bar) === bar).sort((left, right) => Number(left.startFraction || 0) - Number(right.startFraction || 0));
  }

  function timelineBarCount(timeline) {
    return timeline.barStartsMs?.length || Math.max(0, ...(timeline.chords || []).map((event) => Number(event.bar || 0)));
  }

  function bestBarAlignment(timeline, referenceBars) {
    const count = timelineBarCount(timeline);
    if (!referenceBars.length || !count) return null;
    const candidates = [];
    for (let offset = -8; offset <= 8; offset += 1) {
      let compared = 0, matches = 0;
      referenceBars.forEach((symbols, referenceIndex) => {
        const bar = referenceIndex + 1 + offset;
        if (bar < 1 || bar > count) return;
        const events = eventsForBar(timeline, bar);
        if (!events.length || events.some((event) => event.needsAttention || Number(event.confidence || 0) < 0.78)) return;
        const detected = new Set(events.map((event) => normalizeChordSymbol(event.symbol)).filter(Boolean));
        const expected = symbols.map(normalizeChordSymbol).filter(Boolean);
        if (!expected.length) return;
        compared += 1;
        if (expected.some((symbol) => detected.has(symbol))) matches += 1;
      });
      const overlap = referenceBars.filter((_symbols, index) => index + 1 + offset >= 1 && index + 1 + offset <= count).length;
      const coverage = overlap / Math.max(referenceBars.length, count);
      candidates.push({ offset, compared, matches, score: compared ? matches / compared : 0, coverage });
    }
    candidates.sort((left, right) => right.score - left.score || right.compared - left.compared || right.coverage - left.coverage || Math.abs(left.offset) - Math.abs(right.offset));
    const best = candidates[0];
    const exactLength = referenceBars.length === count && best?.offset === 0;
    if (!best || !exactLength && (best.compared < 4 || best.score < 0.6 || best.coverage < 0.7)) return null;
    return { ...best, mode: exactLength ? "measure-exact" : "measure-offset" };
  }

  function addReason(event, reason) {
    event.reviewReasons = [...new Set([...(event.reviewReasons || []), reason])];
  }

  function validateTimeline(timeline, reference, options = {}) {
    const next = JSON.parse(JSON.stringify(timeline || {}));
    const alignment = bestBarAlignment(next, reference.bars || []);
    const vocabulary = new Set((reference.vocabulary || []).map(normalizeChordSymbol).filter(Boolean));
    const sourceLabel = String(options.sourceLabel || "User-supplied chart").slice(0, 120);
    const sourceUrl = String(options.sourceUrl || "").slice(0, 500);
    const digest = referenceDigest(reference);
    const summary = { alignment: alignment?.mode || "vocabulary-only", compared: 0, agreements: 0, corrections: 0, disagreements: 0, unresolved: 0 };

    for (let bar = 1; bar <= timelineBarCount(next); bar += 1) {
      const events = eventsForBar(next, bar);
      const expected = alignment ? (reference.bars[bar - alignment.offset - 1] || []).map(normalizeChordSymbol).filter(Boolean) : [];
      events.filter((event) => event.needsAttention || !event.reviewed).forEach((event, eventIndex) => {
        const detected = normalizeChordSymbol(event.symbol);
        if (!alignment) {
          if (detected && vocabulary.has(detected)) addReason(event, `${sourceLabel} includes this chord, but the reference has no measure alignment.`);
          summary.unresolved += 1;
          return;
        }
        summary.compared += 1;
        const eventExpected = expected.length === events.length ? [expected[eventIndex]] : expected;
        if (detected && eventExpected.includes(detected)) {
          event.confidence = Math.max(Number(event.confidence || 0), 0.84);
          event.reviewed = true;
          event.needsAttention = false;
          event.externalValidation = { provider: "user-supplied", sourceLabel, sourceUrl, referenceDigest: digest, result: "bar-agreement", originalSymbol: event.symbol };
          addReason(event, `Confirmed against ${sourceLabel} at this measure.`);
          summary.agreements += 1;
          return;
        }
        const alternatives = (event.alternatives || []).map((candidate) => ({ ...candidate, normalized: normalizeChordSymbol(candidate.symbol) })).filter((candidate) => candidate.normalized && eventExpected.includes(candidate.normalized));
        const strongestAlternative = Math.max(-Infinity, ...(event.alternatives || []).map((candidate) => Number(candidate.score || -Infinity)));
        alternatives.sort((left, right) => Number(right.score || 0) - Number(left.score || 0));
        const replacement = alternatives[0];
        if (replacement && Number(replacement.score || -Infinity) >= 0.55 && Number(replacement.score || -Infinity) >= strongestAlternative - 0.08 && Number(event.confidence || 0) < 0.78) {
          const originalSymbol = event.symbol;
          event.symbol = replacement.normalized;
          event.finalSymbol = replacement.normalized;
          event.confidence = Math.max(Number(event.confidence || 0), 0.8);
          event.contextualAdjusted = true;
          event.reviewed = true;
          event.needsAttention = false;
          event.externalValidation = { provider: "user-supplied", sourceLabel, sourceUrl, referenceDigest: digest, result: "close-audio-alternative", originalSymbol };
          addReason(event, `${sourceLabel} resolved a close audio alternative at this measure.`);
          summary.corrections += 1;
          return;
        }
        event.externalValidation = { provider: "user-supplied", sourceLabel, sourceUrl, referenceDigest: digest, result: "disagreement", originalSymbol: event.symbol };
        addReason(event, `${sourceLabel} disagrees with the detected chord at this measure.`);
        summary.disagreements += 1;
      });
    }
    next.externalValidation = { provider: "user-supplied", sourceLabel, sourceUrl, referenceDigest: digest, appliedAt: new Date().toISOString(), ...summary };
    return { timeline: next, summary };
  }

  registerProvider({
    id: "user-supplied",
    label: "User-supplied chart",
    networkAccess: false,
    loadReference: async ({ text, sourceUrl = "", sourceLabel = "User-supplied chart" }) => ({ reference: parseReferenceText(text), sourceUrl, sourceLabel })
  });

  const api = { normalizeChordSymbol, chordTokensForLine, parseReferenceText, referenceDigest, bestBarAlignment, validateTimeline, registerProvider, loadProviderReference };
  global.STEEL_RAG_REFERENCE_VALIDATION = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof self !== "undefined" ? self : globalThis);
