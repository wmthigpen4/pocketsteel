(function ownerChordTimingModule(root, factory) {
  "use strict";

  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.OwnerChordTiming = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function ownerChordTimingFactory() {
  "use strict";

  const number = (value) => Number(value) || 0;

  function exactChangeItems(track) {
    return (track.segments || []).map((segment, index) => ({
      id: `change-${index + 1}`,
      position: index + 1,
      kind: "change",
      start: number(segment.start),
      end: number(segment.end),
      confidence: number(segment.confidence),
      chordSymbols: [segment.productLabel || segment.label || "N.C."],
      splitUncertain: false,
    }));
  }

  function beatAlignedItems(track) {
    return (track.bars || []).map((bar, index) => ({
      ...bar,
      id: `bar-${bar.bar || index + 1}`,
      position: bar.bar || index + 1,
      kind: "bar",
      start: number(bar.start),
      end: number(bar.end),
      chordSymbols: bar.chordSymbols?.length ? bar.chordSymbols : ["N.C."],
    }));
  }

  function itemsForTrack(track) {
    const phaseAnchored = track.rhythm?.phase?.status === "anchored";
    if (phaseAnchored && track.bars?.length) {
      return { mode: "beat-aligned-bars", items: beatAlignedItems(track) };
    }
    return { mode: "exact-model-transitions", items: exactChangeItems(track) };
  }

  function chordIndexAt(item, seconds) {
    const symbols = item?.chordSymbols || [];
    if (symbols.length < 2) return 0;
    const midpoint = number(item.start) + (number(item.end) - number(item.start)) / 2;
    return Number(seconds) >= midpoint ? 1 : 0;
  }

  function chordAt(item, seconds) {
    const symbols = item?.chordSymbols || ["N.C."];
    return symbols[chordIndexAt(item, seconds)] || symbols[0] || "N.C.";
  }

  function itemAt(items, seconds) {
    const time = Number(seconds);
    return items.find((item) => time >= number(item.start) && time < number(item.end));
  }

  return { itemsForTrack, chordAt, chordIndexAt, itemAt };
});
