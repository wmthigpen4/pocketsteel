(function (global) {
  "use strict";

  const DEFAULT_E9_TUNING = ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"];
  const COMMON_FRET_MARKERS = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24];
  const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f";
  const DECORATIVE_BACKGROUND_BOX = {
    x: -139,
    y: -65,
    width: 1493,
    height: 442,
    opacity: 0.68,
    preserveAspectRatio: "none",
  };
  const SVG_WIDTH = 1200;
  const SVG_HEIGHT = 360;
  const PLAYABLE_NUT_X = 104;
  const PICKUP_START_X = 1055;
  const APPROVED_FRET_24_PICKUP_GAP_PX = 65;
  const PLAYABLE_BRIDGE_X = PLAYABLE_NUT_X + ((PICKUP_START_X - APPROVED_FRET_24_PICKUP_GAP_PX - PLAYABLE_NUT_X) / 0.75);
  const STRING_END_X = 1158;
  const HARDWARE_GAP_PX = 48;
  const LAYOUT = {
    left: PLAYABLE_NUT_X,
    right: SVG_WIDTH - STRING_END_X,
    nutX: PLAYABLE_NUT_X,
    bridgeX: PLAYABLE_BRIDGE_X,
    pickupStartX: PICKUP_START_X,
    stringEndX: STRING_END_X,
    hardwareGapPx: HARDWARE_GAP_PX,
    top: 56,
    bottom: 104,
  };

  const COLOR_ROLES = {
    open: {
      dot: "#f0bf69",
      glow: "rgba(240, 191, 105, 0.5)",
      band: "rgba(240, 191, 105, 0.16)",
      text: "#fff3d5",
    },
    "a-f": {
      dot: "#8fd5ff",
      glow: "rgba(143, 213, 255, 0.5)",
      band: "rgba(143, 213, 255, 0.15)",
      text: "#dff4ff",
    },
    "a-b": {
      dot: "#8de391",
      glow: "rgba(141, 227, 145, 0.48)",
      band: "rgba(141, 227, 145, 0.15)",
      text: "#def8df",
    },
    "e-lower": {
      dot: "#c7a5ff",
      glow: "rgba(199, 165, 255, 0.48)",
      band: "rgba(199, 165, 255, 0.15)",
      text: "#eee5ff",
    },
    dominant: {
      dot: "#ff9f7e",
      glow: "rgba(255, 159, 126, 0.46)",
      band: "rgba(255, 159, 126, 0.14)",
      text: "#ffe3d7",
    },
    "partial-rootless": {
      dot: "#f2a7c8",
      glow: "rgba(242, 167, 200, 0.42)",
      band: "rgba(242, 167, 200, 0.12)",
      text: "#ffe5f1",
    },
    advanced: {
      dot: "#aeb7c8",
      glow: "rgba(174, 183, 200, 0.42)",
      band: "rgba(174, 183, 200, 0.13)",
      text: "#edf1f8",
    },
    selected: {
      dot: "#fff0b5",
      glow: "rgba(255, 240, 181, 0.68)",
      band: "rgba(255, 240, 181, 0.18)",
      text: "#fff8df",
    },
  };
  const LEGACY_COLOR_ROLE_ALIASES = {
    primary: "open",
    secondary: "a-f",
    alternate: "a-b",
    movement: "advanced",
    reference: "advanced",
    warning: "advanced",
    "a+f": "a-f",
    "af": "a-f",
    "a_f": "a-f",
    "a+b": "a-b",
    "ab": "a-b",
    "a_b": "a-b",
    "e lower": "e-lower",
    "e_lower": "e-lower",
    elower: "e-lower",
    rootless: "partial-rootless",
    partial: "partial-rootless",
  };
  const VOICING_FILTER_OPTIONS = [
    { id: "recommended", label: "Recommended" },
    { id: "starter", label: "Starter" },
    { id: "full-chord", label: "Full chord" },
    { id: "root-position", label: "Root position" },
    { id: "inversions", label: "Inversions" },
    { id: "partial-rootless", label: "Partial/rootless" },
    { id: "dominant", label: "Dominant pockets" },
    { id: "all", label: "All positions" },
  ];
  const MAX_RECOMMENDED_VISIBLE_POSITIONS = 5;

  const STYLE_ID = "pedal-steel-fretboard-styles";
  const STYLE_TEXT = `
.pedal-steel-fretboard {
  color: #fff6df;
  font-family: inherit;
  margin: 0;
  max-width: 100%;
  min-width: 0;
  width: 100%;
}

.pedal-steel-fretboard__stage {
  border: 1px solid rgba(240, 191, 105, 0.28);
  border-radius: 18px;
  background:
    radial-gradient(circle at 50% 0%, rgba(240, 191, 105, 0.13), transparent 42%),
    linear-gradient(135deg, rgba(18, 17, 14, 0.96), rgba(7, 8, 8, 0.96));
  box-shadow:
    0 22px 48px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 232, 178, 0.06);
  overflow-x: auto;
  max-width: 100%;
  width: 100%;
  scrollbar-color: rgba(240, 191, 105, 0.35) rgba(255, 255, 255, 0.05);
}

.pedal-steel-fretboard__svg {
  display: block;
  min-width: 780px;
  width: 100%;
  height: auto;
}

.pedal-steel-background {
  pointer-events: none;
}

.pedal-steel-fretboard__legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.pedal-steel-fretboard__position-tools {
  display: grid;
  gap: 12px;
  margin: 14px 0 0;
}

.pedal-steel-fretboard__scale-strip {
  border: 1px solid rgba(240, 191, 105, 0.2);
  border-radius: 12px;
  color: rgba(255, 246, 223, 0.82);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 0;
  padding: 9px 11px;
}

.pedal-steel-fretboard__scale-item {
  background: rgba(255, 246, 223, 0.04);
  border-radius: 999px;
  padding: 5px 8px;
}

.pedal-steel-fretboard__scale-name {
  color: rgba(240, 191, 105, 0.78);
  font-weight: 800;
  text-transform: capitalize;
}

.pedal-steel-fretboard__filter-panel {
  display: grid;
  gap: 9px;
  margin: 0 0 12px;
}

.pedal-steel-fretboard__filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pedal-steel-fretboard__filter-label {
  align-self: center;
  color: rgba(240, 191, 105, 0.74);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  line-height: 1;
  margin-right: 2px;
  text-transform: uppercase;
}

.pedal-steel-fretboard__filter-button {
  border: 1px solid rgba(240, 191, 105, 0.32);
  border-radius: 8px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(255, 246, 223, 0.82);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  padding: 7px 10px;
}

.pedal-steel-fretboard__filter-button:hover,
.pedal-steel-fretboard__filter-button:focus-visible,
.pedal-steel-fretboard__filter-button.is-selected {
  border-color: rgba(240, 191, 105, 0.68);
  background: rgba(240, 191, 105, 0.12);
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__selector-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 9px;
}

.pedal-steel-fretboard__recommended-note {
  color: rgba(255, 246, 223, 0.66);
  font-size: 0.82rem;
  line-height: 1.4;
  margin: 0;
}

.pedal-steel-fretboard__show-all {
  justify-self: start;
  border: 1px solid rgba(240, 191, 105, 0.28);
  border-radius: 999px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(240, 191, 105, 0.88);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 750;
  padding: 7px 11px;
}

.pedal-steel-fretboard__show-all:hover,
.pedal-steel-fretboard__show-all:focus-visible {
  border-color: rgba(240, 191, 105, 0.64);
  background: rgba(240, 191, 105, 0.11);
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__show-all[hidden] {
  display: none;
}

.pedal-steel-fretboard__selector {
  min-height: 46px;
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.26));
  border-radius: 12px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(255, 246, 223, 0.82);
  cursor: pointer;
  display: grid;
  gap: 4px;
  grid-template-columns: auto minmax(0, 1fr);
  padding: 9px 11px;
  text-align: left;
}

.pedal-steel-fretboard__selector[hidden] {
  display: none;
}

.pedal-steel-fretboard__selector:hover,
.pedal-steel-fretboard__selector:focus-visible,
.pedal-steel-fretboard__selector.is-selected {
  border-color: var(--fretboard-swatch, rgba(240, 191, 105, 0.68));
  background:
    linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.12)), rgba(12, 12, 11, 0.62));
  box-shadow: 0 0 18px var(--fretboard-glow, rgba(240, 191, 105, 0.16));
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__selector-main {
  grid-column: 2;
  font-size: 0.98rem;
  font-weight: 800;
  line-height: 1.15;
}

.pedal-steel-fretboard__selector-sub {
  color: rgba(255, 246, 223, 0.62);
  font-size: 0.78rem;
  grid-column: 2;
  line-height: 1.25;
}

.pedal-steel-fretboard__selector-marker,
.pedal-steel-fretboard__detail-marker {
  background: var(--fretboard-swatch, #f0bf69);
  border-radius: 999px;
  box-shadow: 0 0 14px var(--fretboard-glow, rgba(240, 191, 105, 0.45));
  display: inline-block;
}

.pedal-steel-fretboard__selector-marker {
  align-self: center;
  grid-row: 1 / span 2;
  height: 11px;
  width: 11px;
}

.pedal-steel-fretboard__detail {
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.22));
  border-radius: 14px;
  background:
    linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.08)), rgba(8, 8, 7, 0.72) 46%);
  padding: 13px;
}

.pedal-steel-fretboard__detail[hidden] {
  display: none;
}

.pedal-steel-fretboard__detail-title {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 10px;
}

.pedal-steel-fretboard__detail-marker {
  flex: 0 0 auto;
  height: 12px;
  width: 12px;
}

.pedal-steel-fretboard__detail-title strong {
  color: #fff6df;
  font-size: 1rem;
}

.pedal-steel-fretboard__detail-title span {
  color: rgba(240, 191, 105, 0.82);
  font-size: 0.86rem;
  font-weight: 800;
}

.pedal-steel-fretboard__detail-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.pedal-steel-fretboard__technical {
  border-top: 1px solid rgba(255, 246, 223, 0.1);
  margin-top: 11px;
  padding-top: 10px;
}

.pedal-steel-fretboard__technical[hidden] {
  display: none;
}

.pedal-steel-fretboard__technical summary {
  color: rgba(240, 191, 105, 0.82);
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  list-style: none;
  text-transform: uppercase;
}

.pedal-steel-fretboard__technical summary::-webkit-details-marker {
  display: none;
}

.pedal-steel-fretboard__technical-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 9px;
}

.pedal-steel-fretboard__detail-item {
  border: 1px solid rgba(255, 246, 223, 0.08);
  border-radius: 10px;
  background: rgba(255, 246, 223, 0.035);
  min-width: 0;
  padding: 8px 9px;
}

.pedal-steel-fretboard__detail-item.is-wide {
  grid-column: span 2;
}

.pedal-steel-fretboard__detail-label {
  color: rgba(240, 191, 105, 0.76);
  display: block;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  line-height: 1.2;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.pedal-steel-fretboard__detail-value {
  color: rgba(255, 246, 223, 0.86);
  font-size: 0.9rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.pedal-steel-fretboard__highlight {
  opacity: 0.42;
  transition: opacity 140ms ease, filter 140ms ease;
}

.pedal-steel-fretboard__highlight.is-filter-hidden {
  display: none;
}

.pedal-steel-fretboard__highlight.is-selected {
  opacity: 1;
  filter: drop-shadow(0 0 12px var(--fretboard-glow, rgba(240, 191, 105, 0.46)));
}

.pedal-steel-fretboard__highlight.is-emphasized-visible {
  opacity: 0.9;
  filter: drop-shadow(0 0 10px var(--fretboard-glow, rgba(240, 191, 105, 0.34)));
}

.pedal-steel-fretboard__highlight.is-prominent-cluster {
  opacity: 1;
  filter:
    drop-shadow(0 0 14px var(--fretboard-glow, rgba(240, 191, 105, 0.46)))
    drop-shadow(0 0 3px rgba(255, 246, 223, 0.18));
}

.pedal-steel-fretboard__empty[hidden] {
  display: none;
}

.pedal-steel-fretboard__empty {
  border: 1px solid rgba(240, 191, 105, 0.2);
  border-radius: 12px;
  color: rgba(255, 246, 223, 0.68);
  margin: 0;
  padding: 10px 12px;
}

.pedal-steel-fretboard__legend-item {
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.25));
  border-radius: 12px;
  background:
    linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.08)), rgba(12, 12, 11, 0.8) 48%);
  color: rgba(255, 246, 223, 0.88);
  padding: 11px 12px;
}

.pedal-steel-fretboard__legend-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.pedal-steel-fretboard__legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--fretboard-swatch, #f0bf69);
  box-shadow: 0 0 14px var(--fretboard-glow, rgba(240, 191, 105, 0.45));
}

.pedal-steel-fretboard__legend-meta {
  color: rgba(255, 246, 223, 0.68);
  font-size: 0.88rem;
  line-height: 1.45;
  margin-top: 5px;
}

.answer-fretboard,
.fretboard-card,
.answer-fretboard-details,
.answer-fretboard-mount {
  max-width: 100%;
  min-width: 0;
}

.answer-fretboard-details {
  grid-template-columns: minmax(0, 1fr);
}

.answer-fretboard-mount {
  width: 100%;
}

@media (max-width: 640px) {
  .answer-fretboard-mount {
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-color: rgba(240, 191, 105, 0.35) rgba(255, 255, 255, 0.05);
  }

  .answer-fretboard-mount .pedal-steel-fretboard,
  .answer-fretboard-mount .pedal-steel-fretboard__stage {
    max-width: none;
    width: 700px;
  }

  .pedal-steel-fretboard__stage {
    border-radius: 14px;
  }

  .pedal-steel-fretboard__svg {
    min-width: 700px;
  }

  .pedal-steel-fretboard__legend {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__selector-list {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__detail-grid {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__technical-grid {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__detail-item.is-wide {
    grid-column: auto;
  }
}
`;

  function clampNumber(value, min, max) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return min;
    }
    return Math.min(max, Math.max(min, number));
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeSelectorValue(value) {
    if (global.CSS && typeof global.CSS.escape === "function") {
      return global.CSS.escape(String(value));
    }
    return String(value).replace(/["\\]/g, "\\$&");
  }

  function normalizedFretPosition(fret, maxFret = 24) {
    const safeMax = Math.max(1, Number(maxFret) || 24);
    const safeFret = clampNumber(fret, 0, safeMax);
    return 1 - Math.pow(2, -safeFret / 12);
  }

  function getColorRole(colorRole) {
    return COLOR_ROLES[colorRole] || COLOR_ROLES.open;
  }

  function normalizeColorRole(value, item = {}) {
    const rawRole = String(value || "").trim().toLowerCase();
    const aliasedRole = LEGACY_COLOR_ROLE_ALIASES[rawRole] || rawRole;
    if (COLOR_ROLES[aliasedRole] && !["reference", "movement", "warning"].includes(rawRole)) {
      return aliasedRole;
    }

    const family = normalizeMetadataText(item.family || item.positionFamily || item.position_family).toLowerCase();
    const positionKind = normalizeMetadataText(
      item.positionKind || item.position_kind || item.harmonyType || item.harmony_type
    ).toLowerCase();
    const role = normalizeMetadataText(item.role).toLowerCase();
    const tier = normalizeMetadataText(item.tier || item.difficultyTier || item.difficulty_tier).toLowerCase();
    const pedals = normalizeTextList(item.pedals).join("+").toLowerCase();
    const levers = normalizeTextList(item.levers).join("+").toLowerCase();
    const omittedIntervals = normalizeDetailList(item.omittedIntervals || item.omitted_intervals);
    const haystack = [family, positionKind, role, tier, pedals, levers].join(" ");

    if (haystack.includes("dominant") || /\bv(7|9|13)?\b/.test(haystack)) {
      return "dominant";
    }
    if (item.isRootless || item.is_rootless || item.isPartial || item.is_partial || omittedIntervals.length > 0 || haystack.includes("rootless") || haystack.includes("partial")) {
      return "partial-rootless";
    }
    if (family.includes("e_lower") || family.includes("e-lower") || haystack.includes("e lower") || haystack.includes("e-lower")) {
      return "e-lower";
    }
    if (tier === "advanced" || positionKind.includes("advanced")) {
      return "advanced";
    }
    if (pedals.includes("a") && pedals.includes("b")) {
      return "a-b";
    }
    if ((pedals.includes("a") && levers.includes("f")) || haystack.includes("a+f")) {
      return "a-f";
    }
    return "open";
  }

  function normalizeTuningLabels(tuningLabels, stringCount) {
    const source = Array.isArray(tuningLabels) && tuningLabels.length > 0 ? tuningLabels : DEFAULT_E9_TUNING;
    return Array.from({ length: stringCount }, (_, index) => source[index] || "");
  }

  function normalizeStringList(value, stringCount) {
    const source = Array.isArray(value)
      ? value
      : typeof value === "string"
        ? value.split(/[^0-9]+/).filter(Boolean)
        : [];
    const strings = source
      .map((stringNumber) => Number(stringNumber))
      .filter((stringNumber) => Number.isInteger(stringNumber) && stringNumber >= 1 && stringNumber <= stringCount);
    return Array.from(new Set(strings)).sort((a, b) => a - b);
  }

  function normalizeTextList(value) {
    if (!Array.isArray(value)) {
      return [];
    }
    return value.map(formatDetailValue).map((item) => item.trim()).filter(Boolean);
  }

  function normalizeDetailList(value) {
    if (Array.isArray(value)) {
      return normalizeTextList(value);
    }
    if (value && typeof value === "object") {
      return Object.entries(value)
        .sort(compareEntryKeys)
        .map(([key, detail]) => `String ${key}: ${formatDetailValue(detail)}`)
        .filter((item) => !item.endsWith(":"));
    }
    const text = String(value || "").trim();
    return text ? [text] : [];
  }

  function formatDetailValue(detail) {
    if (Array.isArray(detail)) {
      return detail.map(formatDetailValue).filter(Boolean).join(", ");
    }
    if (detail && typeof detail === "object") {
      const preferredKeys = ["note", "interval", "value", "label", "name", "summary"];
      const preferred = preferredKeys
        .map((key) => detail[key])
        .filter((item) => item !== undefined && item !== null)
        .map(formatDetailValue)
        .filter(Boolean);
      const remaining = Object.entries(detail)
        .filter(([key]) => !preferredKeys.includes(key))
        .sort(compareEntryKeys)
        .map(([key, value]) => `${key}: ${formatDetailValue(value)}`)
        .filter((item) => !item.endsWith(": "));
      return [...preferred, ...remaining].join(" / ");
    }
    return learnerFacingMetadataText(String(detail || "").trim());
  }

  function learnerFacingMetadataText(text) {
    return String(text || "")
      .replace(/\bfive_eight_branch\b/g, "5&8 branch");
  }

  function compareEntryKeys([left], [right]) {
    const leftNumber = Number(left);
    const rightNumber = Number(right);
    if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
      return leftNumber - rightNumber;
    }
    return String(left).localeCompare(String(right));
  }

  function normalizeMetadataText(value) {
    return formatDetailValue(value).trim();
  }

  function normalizeVisibleByDefault(value) {
    if (value === false || value === "false" || value === 0 || value === "0") {
      return false;
    }
    return true;
  }

  function normalizeBooleanFlag(value) {
    if (value === true || value === "true" || value === 1 || value === "1") {
      return true;
    }
    return false;
  }

  function normalizeTier(value) {
    const tier = normalizeMetadataText(value).toLowerCase();
    return tier || "starter";
  }

  function normalizeToken(value) {
    return normalizeMetadataText(value).toLowerCase().replace(/[\s_]+/g, "-");
  }

  function normalizeInversionLabel(item, voicingType) {
    const explicit = normalizeMetadataText(
      item.inversionLabel ||
      item.inversion_label ||
      item.inversion ||
      item.inversionType ||
      item.inversion_type
    );
    const number = Number(item.inversionNumber ?? item.inversion_number);
    const source = explicit || voicingType;
    const sourceToken = normalizeToken(source);
    if (number === 1 || sourceToken.includes("1st") || sourceToken.includes("first")) {
      return "1st inversion";
    }
    if (number === 2 || sourceToken.includes("2nd") || sourceToken.includes("second")) {
      return "2nd inversion";
    }
    if (number === 3 || sourceToken.includes("3rd") || sourceToken.includes("third")) {
      return "3rd inversion";
    }
    if (sourceToken.includes("rootless")) {
      return "Rootless";
    }
    if (sourceToken.includes("partial")) {
      return "Partial";
    }
    if (sourceToken.includes("root")) {
      return "Root position";
    }
    return explicit;
  }

  function voicingCategoryForPosition(highlight) {
    const voicingType = normalizeToken(highlight.voicingType);
    const inversionLabel = normalizeToken(highlight.inversionLabel);
    if (
      highlight.isRootless ||
      highlight.isPartialVoicing ||
      highlight.isPartial ||
      voicingType.includes("rootless") ||
      voicingType.includes("partial") ||
      inversionLabel.includes("rootless") ||
      inversionLabel.includes("partial")
    ) {
      return "partial-rootless";
    }
    if (
      highlight.isInversion ||
      voicingType.includes("inversion") ||
      inversionLabel.includes("inversion")
    ) {
      return "inversions";
    }
    if (
      highlight.isRootPosition ||
      voicingType.includes("root-position") ||
      voicingType === "root" ||
      inversionLabel.includes("root-position")
    ) {
      return "root-position";
    }
    return "";
  }

  function voicingExplanation(highlight) {
    const category = voicingCategoryForPosition(highlight);
    const inversionLabel = normalizeInversionLabel(highlight, highlight.voicingType);
    const normalizedLabel = normalizeToken(inversionLabel);
    if (category === "partial-rootless") {
      if (highlight.isRootless || normalizedLabel.includes("rootless")) {
        return "Rootless: root is omitted";
      }
      return "Partial: not all required chord tones are present";
    }
    if (category === "root-position") {
      return "Root position: root in the bass";
    }
    if (normalizedLabel.includes("1st") || normalizedLabel.includes("first")) {
      return "1st inversion: 3rd in the bass";
    }
    if (normalizedLabel.includes("2nd") || normalizedLabel.includes("second")) {
      return "2nd inversion: 5th in the bass";
    }
    if (normalizedLabel.includes("3rd") || normalizedLabel.includes("third")) {
      return "3rd inversion: 7th in the bass";
    }
    if (category === "inversions") {
      return inversionLabel || "Inversion";
    }
    return "";
  }

  function normalizeLegend(legend) {
    if (!Array.isArray(legend)) {
      return [];
    }
    return legend
      .map((item, index) => {
        const entry = item && typeof item === "object" ? item : {};
        const colorRole = normalizeColorRole(entry.colorRole || entry.color || entry.id, entry);
        const label = normalizeMetadataText(entry.label || entry.name || entry.id || `Legend ${index + 1}`);
        const description = normalizeMetadataText(entry.description || entry.body || entry.notes);
        if (!label) {
          return null;
        }
        return {
          id: normalizeMetadataText(entry.id || colorRole || `legend-${index + 1}`),
          label,
          description,
          colorRole,
        };
      })
      .filter(Boolean);
  }

  function normalizePosition(position, index, maxFret, stringCount, sourceType) {
    const item = position && typeof position === "object" ? position : {};
    const strings = normalizeStringList(item.strings, stringCount);
    const gripStrings = normalizeStringList(item.grip, stringCount);
    const uniqueStrings = strings.length ? strings : gripStrings;
    const grip = item.grip !== undefined
      ? Array.isArray(item.grip)
        ? gripStrings.join("-")
        : String(item.grip)
      : item.string_group !== undefined
        ? String(item.string_group)
      : uniqueStrings.join("-");
    const positionKind = normalizeMetadataText(item.positionKind || item.position_kind || item.harmonyType || item.harmony_type);
    const omittedIntervals = normalizeDetailList(item.omittedIntervals || item.omitted_intervals);
    const isPartial = Boolean(item.isPartial || item.is_partial);
    const isRootless = Boolean(item.isRootless || item.is_rootless);
    const voicingType = normalizeMetadataText(item.voicingType || item.voicing_type);
    const isRootPosition = normalizeBooleanFlag(item.isRootPosition || item.is_root_position);
    const isInversion = normalizeBooleanFlag(item.isInversion || item.is_inversion);
    const isPartialVoicing = normalizeBooleanFlag(item.isPartialVoicing || item.is_partial_voicing);
    const inversionLabel = normalizeInversionLabel(item, voicingType);
    const validationStatus = normalizeMetadataText(item.validationStatus || item.validation_status);
    const colorRole = normalizeColorRole(item.colorRole || item.color, item);
    return {
      id: String(item.id || `${sourceType}-${index + 1}`),
      label: String(item.label || `Position ${index + 1}`),
      fret: clampNumber(item.fret, 0, maxFret),
      strings: uniqueStrings,
      grip,
      pedals: normalizeTextList(item.pedals),
      levers: normalizeTextList(item.levers),
      role: String(item.role || item.chord_function || ""),
      notes: normalizeDetailList(item.displayNotes || item.display_notes || item.notes),
      topVoice: normalizeMetadataText(item.displayTopVoice || item.display_top_voice || item.topVoice || item.top_voice),
      explanation: normalizeMetadataText(item.explanation),
      explanationSummary: normalizeMetadataText(item.explanationSummary || item.explanation_summary),
      intervals: normalizeDetailList(item.intervals),
      omittedIntervals,
      caveats: normalizeDetailList(item.caveats),
      warnings: normalizeDetailList(item.warnings),
      perStringChanges: normalizeDetailList(item.perStringChanges || item.per_string_changes),
      displaySummary: normalizeMetadataText(item.displaySummary || item.display_summary),
      tierReason: normalizeMetadataText(item.tierReason || item.tier_reason),
      whenToUse: normalizeMetadataText(item.whenToUse || item.when_to_use),
      soundCharacter: normalizeMetadataText(item.soundCharacter || item.sound_character),
      movementUse: normalizeMetadataText(item.movementUse || item.movement_use),
      resolutionUse: normalizeMetadataText(item.resolutionUse || item.resolution_use),
      explanationShort: normalizeMetadataText(item.explanationShort || item.explanation_short),
      explanationLong: normalizeMetadataText(item.explanationLong || item.explanation_long),
      forumEvidenceStatus: normalizeMetadataText(item.forumEvidenceStatus || item.forum_evidence_status),
      positionKind,
      family: normalizeMetadataText(item.family || item.positionFamily || item.position_family),
      tier: normalizeTier(item.tier || item.difficultyTier || item.difficulty_tier),
      isPartial,
      isRootless,
      voicingType,
      isRootPosition,
      isInversion,
      isPartialVoicing,
      inversionLabel,
      validationStatus,
      visibleByDefault: normalizeVisibleByDefault(item.visibleByDefault),
      sortOrder: Number.isFinite(Number(item.sortOrder)) ? Number(item.sortOrder) : index + 1,
      sourceType,
      colorRole,
      hasFilterMetadata: Object.prototype.hasOwnProperty.call(item, "family") ||
        Object.prototype.hasOwnProperty.call(item, "positionFamily") ||
        Object.prototype.hasOwnProperty.call(item, "position_family") ||
        Object.prototype.hasOwnProperty.call(item, "tier") ||
        Object.prototype.hasOwnProperty.call(item, "difficultyTier") ||
        Object.prototype.hasOwnProperty.call(item, "difficulty_tier") ||
        Object.prototype.hasOwnProperty.call(item, "visibleByDefault") ||
        Object.prototype.hasOwnProperty.call(item, "displayNotes") ||
        Object.prototype.hasOwnProperty.call(item, "display_notes") ||
        Object.prototype.hasOwnProperty.call(item, "displayTopVoice") ||
        Object.prototype.hasOwnProperty.call(item, "display_top_voice") ||
        Object.prototype.hasOwnProperty.call(item, "displaySummary") ||
        Object.prototype.hasOwnProperty.call(item, "display_summary") ||
        Object.prototype.hasOwnProperty.call(item, "string_group") ||
        Object.prototype.hasOwnProperty.call(item, "perStringChanges") ||
        Object.prototype.hasOwnProperty.call(item, "per_string_changes") ||
        Object.prototype.hasOwnProperty.call(item, "voicingType") ||
        Object.prototype.hasOwnProperty.call(item, "voicing_type") ||
        Object.prototype.hasOwnProperty.call(item, "harmonyType") ||
        Object.prototype.hasOwnProperty.call(item, "harmony_type") ||
        Object.prototype.hasOwnProperty.call(item, "isRootPosition") ||
        Object.prototype.hasOwnProperty.call(item, "is_root_position") ||
        Object.prototype.hasOwnProperty.call(item, "isInversion") ||
        Object.prototype.hasOwnProperty.call(item, "is_inversion") ||
        Object.prototype.hasOwnProperty.call(item, "isPartialVoicing") ||
        Object.prototype.hasOwnProperty.call(item, "is_partial_voicing") ||
        Object.prototype.hasOwnProperty.call(item, "inversionLabel") ||
        Object.prototype.hasOwnProperty.call(item, "inversion_label") ||
        Object.prototype.hasOwnProperty.call(item, "inversion") ||
        Object.prototype.hasOwnProperty.call(item, "inversionType") ||
        Object.prototype.hasOwnProperty.call(item, "inversion_type") ||
        Object.prototype.hasOwnProperty.call(item, "inversionNumber") ||
        Object.prototype.hasOwnProperty.call(item, "inversion_number") ||
        Object.prototype.hasOwnProperty.call(item, "positionKind") ||
        Object.prototype.hasOwnProperty.call(item, "position_kind") ||
        Object.prototype.hasOwnProperty.call(item, "omittedIntervals") ||
        Object.prototype.hasOwnProperty.call(item, "omitted_intervals") ||
        Object.prototype.hasOwnProperty.call(item, "validationStatus") ||
        Object.prototype.hasOwnProperty.call(item, "validation_status") ||
        Object.prototype.hasOwnProperty.call(item, "tierReason") ||
        Object.prototype.hasOwnProperty.call(item, "tier_reason") ||
        Object.prototype.hasOwnProperty.call(item, "whenToUse") ||
        Object.prototype.hasOwnProperty.call(item, "when_to_use") ||
        Object.prototype.hasOwnProperty.call(item, "soundCharacter") ||
        Object.prototype.hasOwnProperty.call(item, "sound_character") ||
        Object.prototype.hasOwnProperty.call(item, "movementUse") ||
        Object.prototype.hasOwnProperty.call(item, "movement_use") ||
        Object.prototype.hasOwnProperty.call(item, "resolutionUse") ||
        Object.prototype.hasOwnProperty.call(item, "resolution_use") ||
        Object.prototype.hasOwnProperty.call(item, "explanationShort") ||
        Object.prototype.hasOwnProperty.call(item, "explanation_short") ||
        Object.prototype.hasOwnProperty.call(item, "explanationLong") ||
        Object.prototype.hasOwnProperty.call(item, "explanation_long") ||
        Object.prototype.hasOwnProperty.call(item, "forumEvidenceStatus") ||
        Object.prototype.hasOwnProperty.call(item, "forum_evidence_status") ||
        Object.prototype.hasOwnProperty.call(item, "warnings"),
    };
  }

  function normalizeDisplayScaleNotes(query) {
    const source = query && typeof query === "object"
      ? query.displayScaleNotes || query.display_scale_notes
      : null;
    if (!source || typeof source !== "object" || Array.isArray(source)) {
      return [];
    }
    return Object.entries(source)
      .sort(compareEntryKeys)
      .map(([scaleType, notes]) => {
        const noteList = Array.isArray(notes)
          ? notes.map(formatDetailValue).filter(Boolean)
          : normalizeDetailList(notes);
        if (!noteList.length) {
          return null;
        }
        return {
          scaleType: normalizeMetadataText(scaleType).replace(/_/g, " "),
          notes: noteList,
        };
      })
      .filter(Boolean);
  }

  function hasPositionMetadata(highlights) {
    return highlights.some((highlight) =>
      highlight.hasFilterMetadata ||
      highlight.caveats.length > 0
    );
  }

  function normalizedKindToken(value) {
    return normalizeMetadataText(value).toLowerCase().replace(/[\s-]+/g, "_");
  }

  function isFocusedPositionKind(positionKind) {
    const kind = normalizedKindToken(positionKind);
    return [
      "grip_analysis",
      "grip_diagnostic",
      "single_position",
      "single_position_explanation",
      "pocket_validation",
      "yes_no_pocket_validation",
      "yes_no_validation",
      "focused_answer",
    ].includes(kind);
  }

  function isFocusedPayload(highlights) {
    if (highlights.length <= 1) {
      return true;
    }
    return highlights.every((highlight) => isFocusedPositionKind(highlight.positionKind));
  }

  function isDominantPosition(highlight) {
    const text = [
      highlight.family,
      highlight.positionKind,
      highlight.role,
      highlight.tier,
      highlight.label,
      highlight.colorRole,
    ].join(" ").toLowerCase();
    return highlight.colorRole === "dominant" || text.includes("dominant") || /\bv(7|9|13)?\b/.test(text);
  }

  function isAdvancedPosition(highlight) {
    return highlight.tier === "advanced" ||
      highlight.colorRole === "advanced" ||
      normalizeMetadataText(highlight.positionKind).toLowerCase().includes("advanced");
  }

  function isStarterPosition(highlight) {
    const tier = normalizeTier(highlight.tier);
    const kind = normalizedKindToken(highlight.positionKind);
    if (tier === "beginner" || tier === "starter") {
      return highlight.visibleByDefault;
    }
    if (kind.includes("starter")) {
      return highlight.visibleByDefault;
    }
    return !highlight.hasFilterMetadata && highlight.visibleByDefault;
  }

  function isMorePosition(highlight) {
    return !isStarterPosition(highlight) && !isDominantPosition(highlight) && !isAdvancedPosition(highlight);
  }

  function isFullChordPosition(highlight) {
    return !highlight.isPartial &&
      !highlight.isRootless &&
      !highlight.isPartialVoicing &&
      voicingCategoryForPosition(highlight) !== "partial-rootless";
  }

  function positionReasonLabel(highlight) {
    if (isDominantPosition(highlight)) {
      return "dominant pocket";
    }
    if (isAdvancedPosition(highlight)) {
      return "advanced";
    }
    if (highlight.isPartial || highlight.isRootless || highlight.colorRole === "partial-rootless") {
      return "partial/rootless";
    }
    if (isStarterPosition(highlight)) {
      return "starter";
    }
    return highlight.tier || "position";
  }

  function fallbackPositionReason(highlight) {
    const controls = [...highlight.pedals, ...highlight.levers].join("+").toLowerCase();
    const omitted = highlight.omittedIntervals.length ? `omits ${highlight.omittedIntervals.join(", ")}` : "";
    if (isDominantPosition(highlight)) {
      return highlight.resolutionUse || "resolves to I";
    }
    if (highlight.isPartial || highlight.isRootless || highlight.colorRole === "partial-rootless") {
      return omitted || "partial color";
    }
    if (highlight.colorRole === "e-lower" || controls.includes("e lower") || controls.includes("e-lower")) {
      return omitted ? `E-lower color, ${omitted}` : "E-lower color";
    }
    if (highlight.colorRole === "a-f" || controls.includes("f")) {
      return "A+F pocket";
    }
    if (highlight.colorRole === "a-b" || (controls.includes("a") && controls.includes("b"))) {
      return "pedals-down pocket";
    }
    if (isStarterPosition(highlight)) {
      return "straight-bar reference";
    }
    return highlight.soundCharacter || highlight.role || "useful position";
  }

  function positionCardReason(highlight) {
    const label = positionReasonLabel(highlight);
    const reason = highlight.explanationShort ||
      highlight.tierReason ||
      highlight.soundCharacter ||
      highlight.whenToUse ||
      fallbackPositionReason(highlight);
    return `${label}: ${reason}`;
  }

  function classificationReason(highlight) {
    return highlight.tierReason ||
      highlight.explanationShort ||
      fallbackPositionReason(highlight);
  }

  function whenToUseReason(highlight) {
    return highlight.whenToUse ||
      highlight.movementUse ||
      highlight.resolutionUse ||
      highlight.soundCharacter ||
      "Use when this pocket matches the sound and movement you need.";
  }

  function omittedIntervalReason(highlight) {
    if (highlight.omittedIntervals.length) {
      return highlight.omittedIntervals;
    }
    if (highlight.isPartial || highlight.isRootless || highlight.colorRole === "partial-rootless") {
      return "not specified";
    }
    return "none";
  }

  function forumEvidenceReason(highlight) {
    return highlight.forumEvidenceStatus || "not yet linked";
  }

  function positionMatchesVoicing(highlight, voicingFilter) {
    if (!voicingFilter || voicingFilter === "all") {
      return true;
    }
    if (voicingFilter === "recommended") {
      return highlight.visibleByDefault;
    }
    if (voicingFilter === "starter") {
      return isStarterPosition(highlight);
    }
    if (voicingFilter === "full-chord") {
      return isFullChordPosition(highlight);
    }
    if (voicingFilter === "dominant") {
      return isDominantPosition(highlight);
    }
    return voicingCategoryForPosition(highlight) === voicingFilter;
  }

  function positionMatchesGrip(highlight, gripFilter) {
    if (Array.isArray(gripFilter)) {
      return gripFilter.length === 0 || gripFilter.includes(highlight.grip);
    }
    if (!gripFilter || gripFilter === "all") {
      return true;
    }
    return highlight.grip === gripFilter;
  }

  function normalizedControlName(value, { combo = false } = {}) {
    const text = normalizeMetadataText(value);
    const token = normalizeToken(text);
    if (!token) return "";
    if (
      token === "e" ||
      token === "e-lower" ||
      token === "e-lowered" ||
      token === "elower" ||
      token === "e-lower-lever" ||
      token.includes("e-lower")
    ) {
      return combo ? "E-lower" : "E-lower";
    }
    if (
      token === "f" ||
      token === "f-lever" ||
      token.includes("f-lever") ||
      token.includes("e-raise")
    ) {
      return combo ? "F" : "F lever";
    }
    if (token === "vertical" || token === "v" || token.includes("vertical")) {
      return "Vertical";
    }
    return text;
  }

  function pedalLeverOptionForPosition(highlight) {
    const controls = [
      ...highlight.pedals.map((control) => normalizedControlName(control, { combo: true })),
      ...highlight.levers.map((control) => normalizedControlName(control, { combo: highlight.pedals.length > 0 })),
    ].filter(Boolean);
    if (!controls.length) {
      return { key: "none", label: "No pedals/levers" };
    }
    const label = controls.join("+");
    return {
      key: normalizeToken(label),
      label,
    };
  }

  function uniquePedalLeverOptions(highlights) {
    const byKey = new Map();
    highlights.forEach((highlight) => {
      const option = pedalLeverOptionForPosition(highlight);
      if (!byKey.has(option.key)) {
        byKey.set(option.key, option);
      }
    });
    const priority = new Map([
      ["none", 0],
      ["a+b", 1],
      ["a+f", 2],
      ["e-lower", 3],
      ["f-lever", 4],
      ["b+c", 5],
      ["vertical", 6],
    ]);
    return Array.from(byKey.values()).sort((left, right) => {
      const leftPriority = priority.has(left.key) ? priority.get(left.key) : 50;
      const rightPriority = priority.has(right.key) ? priority.get(right.key) : 50;
      if (leftPriority !== rightPriority) {
        return leftPriority - rightPriority;
      }
      return left.label.localeCompare(right.label);
    });
  }

  function normalizePedalLeverFilters(value, pedalLeverOptions, hasPedalLeverControls) {
    if (!hasPedalLeverControls) {
      return [];
    }
    const validKeys = new Set(pedalLeverOptions.map((option) => option.key));
    const requestedValues = Array.isArray(value)
      ? value
      : String(value || "all").split(",");
    const normalizedValues = requestedValues
      .map((item) => normalizeToken(item || ""))
      .filter(Boolean);
    if (normalizedValues.length === 0 || normalizedValues.includes("all")) {
      return [];
    }
    return Array.from(new Set(normalizedValues.filter((item) => validKeys.has(item))));
  }

  function positionMatchesPedalLever(highlight, pedalLeverFilters) {
    if (!pedalLeverFilters || pedalLeverFilters.length === 0) {
      return true;
    }
    return pedalLeverFilters.includes(pedalLeverOptionForPosition(highlight).key);
  }

  function uniqueGripOptions(highlights) {
    return Array.from(new Set(
      highlights
        .map((highlight) => highlight.grip)
        .filter(Boolean)
    )).sort((left, right) => {
      const leftParts = left.split("-").map(Number);
      const rightParts = right.split("-").map(Number);
      for (let index = 0; index < Math.max(leftParts.length, rightParts.length); index += 1) {
        const leftValue = Number.isFinite(leftParts[index]) ? leftParts[index] : Infinity;
        const rightValue = Number.isFinite(rightParts[index]) ? rightParts[index] : Infinity;
        if (leftValue !== rightValue) {
          return leftValue - rightValue;
        }
      }
      return left.localeCompare(right);
    });
  }

  function voicingCategoryOptions(highlights) {
    return Array.from(new Set(
      highlights
        .map(voicingCategoryForPosition)
        .filter(Boolean)
    ));
  }

  function availableVoicingOptions(highlights) {
    if (!highlights.length) {
      return [];
    }
    return VOICING_FILTER_OPTIONS.filter((option) => {
      if (option.id === "all" || option.id === "recommended") {
        return true;
      }
      return highlights.some((highlight) => positionMatchesVoicing(highlight, option.id));
    });
  }

  function hasUsefulVoicingControls(highlights, options) {
    if (!highlights.length || options.length <= 2) {
      return false;
    }
    const hasSpecificVoicingBucket = options.some((option) => [
      "root-position",
      "inversions",
      "partial-rootless",
      "dominant",
    ].includes(option.id));
    const hasHiddenPositions = highlights.some((highlight) => !highlight.visibleByDefault);
    return hasSpecificVoicingBucket ||
      hasHiddenPositions ||
      highlights.length > MAX_RECOMMENDED_VISIBLE_POSITIONS;
  }

  function normalizeVoicingFilter(value, hasVoicingControls) {
    if (!hasVoicingControls) {
      return "all";
    }
    if (value === undefined || value === null || value === "") {
      return "recommended";
    }
    const requested = normalizeToken(value);
    if (!VOICING_FILTER_OPTIONS.some((option) => option.id === requested)) {
      return "recommended";
    }
    return requested;
  }

  function normalizeGripFilters(value, gripOptions, hasGripControls) {
    if (!hasGripControls) {
      return [];
    }
    const requestedValues = Array.isArray(value)
      ? value
      : String(value || "all").split(",");
    const normalizedValues = requestedValues
      .map((item) => normalizeMetadataText(item || ""))
      .filter(Boolean);
    if (normalizedValues.length === 0 || normalizedValues.includes("all")) {
      return [];
    }
    return Array.from(new Set(normalizedValues.filter((item) => gripOptions.includes(item))));
  }

  function normalizeHighlightStyle(value) {
    return normalizeToken(value) === "prominent" ? "prominent" : "standard";
  }

  function buildFretboardModel(options = {}) {
    const maxFret = Math.max(1, Math.floor(Number(options.maxFret) || 24));
    const stringCount = Math.max(1, Math.floor(Number(options.stringCount) || 10));
    const tuningLabels = normalizeTuningLabels(options.tuningLabels, stringCount);
    const fretboardWidth = LAYOUT.bridgeX - LAYOUT.nutX;
    const fretboardHeight = SVG_HEIGHT - LAYOUT.top - LAYOUT.bottom;
    const fretPositions = Array.from({ length: maxFret + 1 }, (_, fret) => ({
      fret,
      normalized: normalizedFretPosition(fret, maxFret),
      x: LAYOUT.nutX + normalizedFretPosition(fret, maxFret) * fretboardWidth,
    }));
    const stringSpacing = stringCount > 1 ? fretboardHeight / (stringCount - 1) : 0;
    const strings = Array.from({ length: stringCount }, (_, index) => ({
      number: index + 1,
      label: tuningLabels[index] || "",
      y: LAYOUT.top + index * stringSpacing,
    }));
    const hasContractPositions = Array.isArray(options.positions);
    const sourcePositions = hasContractPositions
      ? options.positions
      : Array.isArray(options.highlights)
        ? options.highlights
        : [];
    const positionSourceType = hasContractPositions ? "position" : "highlight";
    const allHighlights = sourcePositions
      .map((position, index) => normalizePosition(position, index, maxFret, stringCount, positionSourceType))
      .filter((highlight) => highlight.strings.length > 0)
      .sort((left, right) =>
        (left.sortOrder - right.sortOrder) ||
        (left.fret - right.fret) ||
        left.id.localeCompare(right.id)
      )
      .map((highlight) => ({
        ...highlight,
        x: LAYOUT.nutX + normalizedFretPosition(highlight.fret, maxFret) * fretboardWidth,
        stringYs: highlight.strings.map((stringNumber) => strings[stringNumber - 1].y),
      }));
    const hideFilterControls = options.hideFilterControls === true;
    const hasFilterControls = !hideFilterControls && hasPositionMetadata(allHighlights) && allHighlights.length > 1 && !isFocusedPayload(allHighlights);
    const voicingCategories = voicingCategoryOptions(allHighlights);
    const voicingOptions = hasFilterControls ? availableVoicingOptions(allHighlights) : [];
    const hasVoicingControls = hasFilterControls && hasUsefulVoicingControls(allHighlights, voicingOptions);
    const gripOptions = uniqueGripOptions(allHighlights);
    const hasGripControls = hasFilterControls && gripOptions.length > 1;
    const pedalLeverOptions = hasFilterControls ? uniquePedalLeverOptions(allHighlights) : [];
    const hasPedalLeverControls = hasFilterControls &&
      (hasVoicingControls || hasGripControls) &&
      pedalLeverOptions.length > 1;
    const voicingFilter = normalizeVoicingFilter(options.voicingFilter || options.voicingTypeFilter, hasVoicingControls);
    const gripFilters = normalizeGripFilters(options.gripFilters || options.gripFilter || options.grip, gripOptions, hasGripControls);
    const gripFilter = gripFilters[0] || "all";
    const pedalLeverFilters = normalizePedalLeverFilters(
      options.pedalLeverFilters || options.pedalLeverFilter || options.controlFilters || options.controlFilter,
      pedalLeverOptions,
      hasPedalLeverControls
    );
    const filteredHighlights = allHighlights.filter((highlight) =>
      positionMatchesVoicing(highlight, voicingFilter) &&
      positionMatchesGrip(highlight, gripFilters) &&
      positionMatchesPedalLever(highlight, pedalLeverFilters)
    );
    const hasRecommendedLimit = voicingFilter === "recommended" &&
      gripFilters.length === 0 &&
      pedalLeverFilters.length === 0 &&
      filteredHighlights.length > MAX_RECOMMENDED_VISIBLE_POSITIONS;
    const highlights = hasRecommendedLimit
      ? filteredHighlights.slice(0, MAX_RECOMMENDED_VISIBLE_POSITIONS)
      : filteredHighlights;
    const recommendedHiddenIds = new Set(filteredHighlights.slice(MAX_RECOMMENDED_VISIBLE_POSITIONS).map((highlight) => highlight.id));
    const selectedPositionId = highlights[0]?.id || "";

    return {
      width: SVG_WIDTH,
      height: SVG_HEIGHT,
      layout: { ...LAYOUT, scalePx: fretboardWidth },
      maxFret,
      stringCount,
      tuningLabels,
      fretPositions,
      strings,
      markers: COMMON_FRET_MARKERS.filter((fret) => fret <= maxFret),
      markerY: strings.length >= 6 ? (strings[4].y + strings[5].y) / 2 : LAYOUT.top + fretboardHeight / 2,
      filterMode: "all",
      tabMode: "all",
      voicingFilter,
      gripFilter,
      gripFilters,
      hasFilters: hasVoicingControls || hasGripControls || hasPedalLeverControls,
      hasVoicingControls,
      hasGripControls,
      hasPedalLeverControls,
      voicingCategories,
      voicingOptions,
      gripOptions,
      pedalLeverOptions,
      pedalLeverFilters,
      hasRecommendedLimit,
      hasRecommendedCapAvailable: hasRecommendedLimit,
      recommendedHiddenIds,
      selectedPositionId,
      allHighlights,
      highlights,
      emphasizeVisibleHighlights: options.emphasizeVisibleHighlights === true,
      highlightStyle: normalizeHighlightStyle(options.highlightStyle),
      legend: normalizeLegend(options.legend),
      displayScaleNotes: normalizeDisplayScaleNotes(options.query),
      showHighlightLabels: options.showHighlightLabels !== false,
      hidePositionTools: options.hidePositionTools === true,
      hideLegend: options.hideLegend === true,
    };
  }

  function renderFrets(model) {
    return model.fretPositions
      .map((position) => {
        const isNut = position.fret === 0;
        const stroke = isNut ? "rgba(255, 246, 223, 0.92)" : "rgba(255, 246, 223, 0.4)";
        const width = isNut ? 3.5 : 1.35;
        return `<line data-fret-line="${position.fret}" x1="${position.x.toFixed(3)}" y1="${LAYOUT.top - 24}" x2="${position.x.toFixed(3)}" y2="${SVG_HEIGHT - LAYOUT.bottom + 26}" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round" />`;
      })
      .join("");
  }

  function renderFretNumbers(model) {
    return model.fretPositions
      .filter((position) => position.fret > 0)
      .filter((position) => position.fret <= 12 || [15, 17, 19, 21, 24].includes(position.fret))
      .map((position) => {
        const isHighFret = position.fret > 12;
        const fontSize = isHighFret ? 16 : 20;
        const y = SVG_HEIGHT - 38;
        return `<text data-fret-number="${position.fret}" data-fret-number-density="${isHighFret ? "compact" : "standard"}" x="${position.x.toFixed(3)}" y="${y}" text-anchor="middle" fill="rgba(255, 246, 223, 0.72)" stroke="rgba(7, 8, 8, 0.76)" stroke-width="${isHighFret ? "2.4" : "1.6"}" paint-order="stroke fill" font-size="${fontSize}" font-weight="${isHighFret ? "700" : "600"}">${position.fret}</text>`;
      })
      .join("");
  }

  function fretX(model, fret) {
    return model.layout.nutX + normalizedFretPosition(fret, Math.max(model.maxFret, fret)) * model.layout.scalePx;
  }

  function markerX(model, fret) {
    return (fretX(model, fret - 1) + fretX(model, fret)) / 2;
  }

  function renderDiamond({ x, y, size, fret, index, isEmphasis }) {
    const points = [
      `${x.toFixed(3)},${(y - size).toFixed(3)}`,
      `${(x + size).toFixed(3)},${y.toFixed(3)}`,
      `${x.toFixed(3)},${(y + size).toFixed(3)}`,
      `${(x - size).toFixed(3)},${y.toFixed(3)}`,
    ].join(" ");
    return `<polygon data-fret-marker-diamond="${fret}" data-fret-marker-diamond-index="${index}" points="${points}" fill="rgba(255, 246, 223, 0.62)" stroke="rgba(240, 191, 105, 0.58)" stroke-width="${isEmphasis ? "1.8" : "1.55"}" opacity="${isEmphasis ? "0.58" : "0.46"}" />`;
  }

  function renderFretMarkerShape({ x, y, size, isEmphasis, fret }) {
    const offsets = isEmphasis ? [-19, 0, 19] : [0];
    const diamonds = offsets
      .map((offset, index) => renderDiamond({ x, y: y + offset, size, fret, index: index + 1, isEmphasis }))
      .join("");
    return `<g data-fret-marker="${fret}" data-fret-marker-emphasis="${isEmphasis ? "true" : "false"}" data-fret-marker-placement="space" data-fret-marker-position="between-strings-5-6" data-fret-marker-style="printed-diamond" data-fret-marker-y="${y.toFixed(3)}" transform="translate(0 0)">
      ${diamonds}
    </g>`;
  }

  function renderMarkers(model) {
    return model.markers
      .map((fret) => {
        const x = markerX(model, fret);
        const markerY = model.markerY;
        const isEmphasis = fret === 12 || fret === 24;
        const size = isEmphasis ? 8.8 : 10.8;
        return renderFretMarkerShape({ x, y: markerY, size, isEmphasis, fret });
      })
      .join("");
  }

  function renderStrings(model) {
    const startX = LAYOUT.nutX;
    const endX = LAYOUT.stringEndX;
    return model.strings
      .map((stringInfo) => {
        const strokeWidth = 1.2 + (stringInfo.number - 1) * 0.08;
        return [
          `<text data-string-label="${stringInfo.number}" x="${LAYOUT.left - 28}" y="${stringInfo.y + 6}" text-anchor="end" fill="rgba(255, 246, 223, 0.74)" font-size="20">${stringInfo.number}</text>`,
          `<text data-tuning-label="${stringInfo.number}" x="${LAYOUT.left - 14}" y="${stringInfo.y + 6}" text-anchor="start" fill="rgba(240, 191, 105, 0.85)" font-size="20">${escapeHtml(stringInfo.label)}</text>`,
          `<line data-fretboard-string="${stringInfo.number}" x1="${startX}" y1="${stringInfo.y.toFixed(3)}" x2="${endX}" y2="${stringInfo.y.toFixed(3)}" stroke="rgba(255, 246, 223, 0.58)" stroke-width="${strokeWidth.toFixed(2)}" stroke-linecap="round" />`,
        ].join("");
      })
      .join("");
  }

  function renderHighlight(highlight) {
    const color = getColorRole(highlight.colorRole);
    const colorStyle = `--fretboard-swatch: ${color.dot}; --fretboard-glow: ${color.glow}; --fretboard-band: ${color.band};`;
    const hiddenStyle = highlight.isHiddenByFilter ? " display: none;" : "";
    const voicingCategory = voicingCategoryForPosition(highlight);
    const pedalLeverOption = pedalLeverOptionForPosition(highlight);
    const minY = Math.min(...highlight.stringYs);
    const maxY = Math.max(...highlight.stringYs);
    const isProminent = highlight.highlightStyle === "prominent";
    const bandWidth = isProminent ? 52 : 36;
    const dotWidth = isProminent ? 42 : 30;
    const dotHeight = isProminent ? 24 : 18;
    const dotRx = dotHeight / 2;
    const bandHeight = Math.max(isProminent ? 46 : 34, maxY - minY + (isProminent ? 36 : 26));
    const bandY = minY - (isProminent ? 18 : 13);
    const labelY = Math.max(26, bandY - 12);
    const dataAttrs = `data-highlight-id="${escapeHtml(highlight.id)}" data-highlight-fret="${highlight.fret}" data-highlight-strings="${escapeHtml(highlight.strings.join(","))}" data-color-role="${escapeHtml(highlight.colorRole)}" data-highlight-cluster-style="${escapeHtml(highlight.highlightStyle)}"`;
    const band = highlight.strings.length > 1
      ? `<rect data-highlight-band ${dataAttrs} x="${(highlight.x - bandWidth / 2).toFixed(3)}" y="${bandY.toFixed(3)}" width="${bandWidth}" height="${bandHeight.toFixed(3)}" rx="${bandWidth / 2}" fill="${color.band}" stroke="${color.dot}" stroke-opacity="${isProminent ? "0.7" : "0.34"}" stroke-width="${isProminent ? "1.8" : "1"}" />`
      : "";
    const halos = isProminent
      ? highlight.stringYs
        .map((y, index) => {
          const stringNumber = highlight.strings[index];
          return `<rect data-highlight-halo ${dataAttrs} data-highlight-string="${stringNumber}" x="${(highlight.x - (dotWidth + 12) / 2).toFixed(3)}" y="${(y - (dotHeight + 10) / 2).toFixed(3)}" width="${dotWidth + 12}" height="${dotHeight + 10}" rx="${(dotHeight + 10) / 2}" fill="${color.glow}" opacity="0.42" filter="url(#fretboard-glow)" />`;
        })
        .join("")
      : "";
    const dots = highlight.stringYs
      .map((y, index) => {
        const stringNumber = highlight.strings[index];
        return `<rect data-highlight-dot ${dataAttrs} data-highlight-string="${stringNumber}" x="${(highlight.x - dotWidth / 2).toFixed(3)}" y="${(y - dotHeight / 2).toFixed(3)}" width="${dotWidth}" height="${dotHeight}" rx="${dotRx}" fill="${color.dot}" fill-opacity="${isProminent ? "1" : "0.95"}" stroke="#fff6df" stroke-opacity="${isProminent ? "0.72" : "0.38"}" stroke-width="${isProminent ? "1.8" : "1"}" filter="url(#fretboard-glow)" />`;
      })
      .join("");
    const label = highlight.showLabel === false
      ? ""
      : `<text data-highlight-label="${escapeHtml(highlight.id)}" x="${highlight.x.toFixed(3)}" y="${labelY.toFixed(3)}" text-anchor="middle" fill="${color.text}" font-size="18" font-weight="700">${escapeHtml(highlight.label)}</text>`;
    return `<g class="pedal-steel-fretboard__highlight${highlight.isSelected ? " is-selected" : ""}${highlight.isEmphasizedVisible ? " is-emphasized-visible" : ""}${isProminent ? " is-prominent-cluster" : ""}${highlight.isHiddenByFilter ? " is-filter-hidden" : ""}" ${dataAttrs} data-position-family="${escapeHtml(highlight.family)}" data-position-tier="${escapeHtml(highlight.tier)}" data-position-kind="${escapeHtml(highlight.positionKind)}" data-position-grip="${escapeHtml(highlight.grip)}" data-position-pedal-lever-key="${escapeHtml(pedalLeverOption.key)}" data-position-pedal-lever-label="${escapeHtml(pedalLeverOption.label)}" data-voicing-type="${escapeHtml(highlight.voicingType)}" data-voicing-category="${escapeHtml(voicingCategory)}" data-is-root-position="${highlight.isRootPosition ? "true" : "false"}" data-is-inversion="${highlight.isInversion ? "true" : "false"}" data-is-partial-voicing="${highlight.isPartialVoicing ? "true" : "false"}" data-is-rootless="${highlight.isRootless ? "true" : "false"}" data-visible-by-default="${highlight.visibleByDefault ? "true" : "false"}" data-has-levers="${highlight.levers.length ? "true" : "false"}" data-is-starter="${isStarterPosition(highlight) ? "true" : "false"}" data-is-full-chord="${isFullChordPosition(highlight) ? "true" : "false"}" data-is-dominant="${isDominantPosition(highlight) ? "true" : "false"}" data-is-advanced="${isAdvancedPosition(highlight) ? "true" : "false"}" data-is-more="${isMorePosition(highlight) ? "true" : "false"}" data-recommended-extra="${highlight.isRecommendedExtra ? "true" : "false"}" data-emphasized-visible="${highlight.isEmphasizedVisible ? "true" : "false"}" data-filter-visible="${highlight.isHiddenByFilter ? "false" : "true"}" style="${colorStyle}${hiddenStyle}"${highlight.isHiddenByFilter ? " hidden" : ""}>
      ${band}
      ${halos}
      ${dots}
      ${label}
    </g>`;
  }

  function renderHighlights(model) {
    const visibleIds = new Set(model.highlights.map((highlight) => highlight.id));
    return model.allHighlights.map((highlight) => renderHighlight({
      ...highlight,
      isSelected: model.highlights[0]?.id === highlight.id,
      isHiddenByFilter: !visibleIds.has(highlight.id),
      isEmphasizedVisible: model.emphasizeVisibleHighlights && visibleIds.has(highlight.id),
      isRecommendedExtra: model.recommendedHiddenIds.has(highlight.id),
      showLabel: model.showHighlightLabels,
      highlightStyle: model.highlightStyle,
    })).join("");
  }

  function controlLabel(highlight) {
    const controls = [...highlight.pedals, ...highlight.levers];
    return controls.length ? controls.join("+") : "open";
  }

  function positionSelectorLabel(highlight) {
    return `${highlight.fret} ${controlLabel(highlight)}`;
  }

  function valueOrDash(value) {
    const text = Array.isArray(value)
      ? value.map(formatDetailValue).filter(Boolean).join(", ")
      : formatDetailValue(value).trim();
    return text || "none";
  }

  function isEmptyLearnerValue(text) {
    const normalized = String(text || "").trim().toLowerCase().replace(/[_-]+/g, " ");
    return !normalized ||
      normalized === "none" ||
      normalized === "not found" ||
      normalized === "not specified" ||
      normalized === "not yet linked" ||
      normalized === "unknown";
  }

  function renderDetailItem(label, value, className = "", options = {}) {
    const displayValue = valueOrDash(value);
    if (options.hideEmpty !== false && isEmptyLearnerValue(displayValue)) {
      return "";
    }
    return `<div class="pedal-steel-fretboard__detail-item${className ? ` ${className}` : ""}">
      <span class="pedal-steel-fretboard__detail-label">${escapeHtml(label)}</span>
      <span class="pedal-steel-fretboard__detail-value">${escapeHtml(displayValue)}</span>
    </div>`;
  }

  function renderTechnicalDetails(items) {
    const content = items.filter(Boolean).join("");
    if (!content) {
      return "";
    }
    return `<details class="pedal-steel-fretboard__technical">
      <summary>Technical details</summary>
      <div class="pedal-steel-fretboard__technical-grid">
        ${content}
      </div>
    </details>`;
  }

  function renderPositionDetail(highlight, selectedPositionId, visibleIds) {
    const color = getColorRole(highlight.colorRole);
    const colorStyle = `--fretboard-swatch: ${color.dot}; --fretboard-glow: ${color.glow}; --fretboard-band: ${color.band}; --fretboard-card-border: ${color.dot};`;
    const isVisible = visibleIds.has(highlight.id);
    const isSelected = highlight.id === selectedPositionId;
    const voicingCategory = voicingCategoryForPosition(highlight);
    const pedalLeverOption = pedalLeverOptionForPosition(highlight);
    const hiddenStyle = isVisible && isSelected ? "" : " display: none;";
    const voicingValue = voicingExplanation(highlight) || highlight.voicingType || highlight.inversionLabel;
    const kindValue = [
      highlight.positionKind,
      highlight.isPartial ? "partial" : "",
      highlight.isRootless ? "rootless" : "",
    ].filter(Boolean).join(" · ");
    return `<section class="pedal-steel-fretboard__detail" data-position-detail="${escapeHtml(highlight.id)}" data-color-role="${escapeHtml(highlight.colorRole)}" data-position-family="${escapeHtml(highlight.family)}" data-position-tier="${escapeHtml(highlight.tier)}" data-position-kind="${escapeHtml(highlight.positionKind)}" data-position-grip="${escapeHtml(highlight.grip)}" data-position-pedal-lever-key="${escapeHtml(pedalLeverOption.key)}" data-position-pedal-lever-label="${escapeHtml(pedalLeverOption.label)}" data-voicing-type="${escapeHtml(highlight.voicingType)}" data-voicing-category="${escapeHtml(voicingCategory)}" data-is-root-position="${highlight.isRootPosition ? "true" : "false"}" data-is-inversion="${highlight.isInversion ? "true" : "false"}" data-is-partial-voicing="${highlight.isPartialVoicing ? "true" : "false"}" data-is-rootless="${highlight.isRootless ? "true" : "false"}" data-visible-by-default="${highlight.visibleByDefault ? "true" : "false"}" data-has-levers="${highlight.levers.length ? "true" : "false"}" data-is-starter="${isStarterPosition(highlight) ? "true" : "false"}" data-is-full-chord="${isFullChordPosition(highlight) ? "true" : "false"}" data-is-dominant="${isDominantPosition(highlight) ? "true" : "false"}" data-is-advanced="${isAdvancedPosition(highlight) ? "true" : "false"}" data-is-more="${isMorePosition(highlight) ? "true" : "false"}" data-filter-visible="${isVisible ? "true" : "false"}" style="${colorStyle}${hiddenStyle}" aria-live="polite"${isVisible && isSelected ? "" : " hidden"}>
      <p class="pedal-steel-fretboard__detail-title"><span class="pedal-steel-fretboard__detail-marker" data-color-role="${escapeHtml(highlight.colorRole)}" aria-hidden="true"></span><strong>${escapeHtml(highlight.label)}</strong><span>${escapeHtml(positionSelectorLabel(highlight))}</span></p>
      <div class="pedal-steel-fretboard__detail-grid">
        ${renderDetailItem("Fret", highlight.fret, "", { hideEmpty: false })}
        ${renderDetailItem("Grip", highlight.grip || highlight.strings.join("-"), "", { hideEmpty: false })}
        ${renderDetailItem("Pedals", highlight.pedals)}
        ${renderDetailItem("Levers", highlight.levers)}
        ${renderDetailItem("String changes", highlight.perStringChanges, "is-wide")}
        ${renderDetailItem("Notes", highlight.notes, "is-wide")}
        ${renderDetailItem("Top voice", highlight.topVoice, "is-wide")}
        ${renderDetailItem("Intervals", highlight.intervals, "is-wide")}
        ${renderDetailItem("When to use", whenToUseReason(highlight), "is-wide")}
        ${renderDetailItem("Short explanation", highlight.displaySummary || highlight.explanationShort || highlight.explanationSummary || highlight.explanation, "is-wide")}
        ${renderDetailItem("Warnings", highlight.warnings, "is-wide")}
      </div>
      ${renderTechnicalDetails([
        renderDetailItem("Validation status", highlight.validationStatus),
        renderDetailItem("Family", highlight.family),
        renderDetailItem("Tier", highlight.tier),
        renderDetailItem("Role", highlight.role),
        renderDetailItem("Position kind", kindValue),
        renderDetailItem("Why classified", classificationReason(highlight), "is-wide"),
        renderDetailItem("Forum usage evidence", forumEvidenceReason(highlight), "is-wide"),
        renderDetailItem("Omitted intervals", omittedIntervalReason(highlight), "is-wide"),
        renderDetailItem("Movement use", highlight.movementUse, "is-wide"),
        renderDetailItem("Resolution use", highlight.resolutionUse, "is-wide"),
        renderDetailItem("Extended explanation", highlight.explanationLong, "is-wide"),
        renderDetailItem("Caveats", highlight.caveats, "is-wide"),
        renderDetailItem("Voicing", voicingValue, "is-wide"),
        renderDetailItem("Sound character", highlight.soundCharacter, "is-wide"),
        renderDetailItem("What is omitted", omittedIntervalReason(highlight), "is-wide")
      ])}
    </section>`;
  }

  function renderFretboardFilterControls(model) {
    if (!model.hasVoicingControls && !model.hasGripControls && !model.hasPedalLeverControls) {
      return "";
    }
    const voicingControls = model.hasVoicingControls
      ? `<div class="pedal-steel-fretboard__filter-group" aria-label="Filter by voicing type">
        <span class="pedal-steel-fretboard__filter-label">Voicing</span>
        ${model.voicingOptions.map((option) => `<button class="pedal-steel-fretboard__filter-button${model.voicingFilter === option.id ? " is-selected" : ""}" type="button" data-voicing-filter="${option.id}" aria-pressed="${model.voicingFilter === option.id ? "true" : "false"}">${escapeHtml(option.label)}</button>`).join("")}
      </div>`
      : "";
    const gripControls = model.hasGripControls
      ? `<div class="pedal-steel-fretboard__filter-group" aria-label="Filter by grip">
        <span class="pedal-steel-fretboard__filter-label">Grip</span>
        <button class="pedal-steel-fretboard__filter-button${model.gripFilters.length === 0 ? " is-selected" : ""}" type="button" data-grip-filter="all" aria-pressed="${model.gripFilters.length === 0 ? "true" : "false"}">All grips</button>
        ${model.gripOptions.map((grip) => {
          const isSelected = model.gripFilters.includes(grip);
          return `<button class="pedal-steel-fretboard__filter-button${isSelected ? " is-selected" : ""}" type="button" data-grip-filter="${escapeHtml(grip)}" aria-pressed="${isSelected ? "true" : "false"}">${escapeHtml(grip)}</button>`;
        }).join("")}
      </div>`
      : "";
    const pedalLeverControls = model.hasPedalLeverControls
      ? `<div class="pedal-steel-fretboard__filter-group" aria-label="Filter by pedal and lever combination">
        <span class="pedal-steel-fretboard__filter-label">Pedals / Levers</span>
        <button class="pedal-steel-fretboard__filter-button${model.pedalLeverFilters.length === 0 ? " is-selected" : ""}" type="button" data-pedal-lever-filter="all" aria-pressed="${model.pedalLeverFilters.length === 0 ? "true" : "false"}">All</button>
        ${model.pedalLeverOptions.map((option) => {
          const isSelected = model.pedalLeverFilters.includes(option.key);
          return `<button class="pedal-steel-fretboard__filter-button${isSelected ? " is-selected" : ""}" type="button" data-pedal-lever-filter="${escapeHtml(option.key)}" aria-pressed="${isSelected ? "true" : "false"}">${escapeHtml(option.label)}</button>`;
        }).join("")}
      </div>`
      : "";
    return `<div class="pedal-steel-fretboard__filter-panel" data-fretboard-filter-panel>
      ${voicingControls}
      ${gripControls}
      ${pedalLeverControls}
    </div>`;
  }

  function renderScaleDisplay(model) {
    if (!model.displayScaleNotes.length) {
      return "";
    }
    const items = model.displayScaleNotes.map((item) =>
      `<span class="pedal-steel-fretboard__scale-item" data-scale-notes="${escapeHtml(item.scaleType)}"><span class="pedal-steel-fretboard__scale-name">${escapeHtml(item.scaleType)}</span>: ${escapeHtml(item.notes.join(" "))}</span>`
    ).join("");
    return `<div class="pedal-steel-fretboard__scale-strip" aria-label="Key-aware scale spellings">${items}</div>`;
  }

  function renderPositionTools(model) {
    if (model.allHighlights.length === 0) {
      return "";
    }
    const visibleIds = new Set(model.highlights.map((highlight) => highlight.id));
    const selectedPositionId = model.selectedPositionId;
    const buttons = model.allHighlights
      .map((highlight) => {
        const color = getColorRole(highlight.colorRole);
        const isVisible = visibleIds.has(highlight.id);
        const colorStyle = `--fretboard-swatch: ${color.dot}; --fretboard-glow: ${color.glow}; --fretboard-band: ${color.band}; --fretboard-card-border: ${color.dot};`;
        const hiddenStyle = isVisible ? "" : " display: none;";
        const isSelected = highlight.id === selectedPositionId;
        const isRecommendedExtra = model.recommendedHiddenIds.has(highlight.id);
        const voicingCategory = voicingCategoryForPosition(highlight);
        const pedalLeverOption = pedalLeverOptionForPosition(highlight);
        const voicingText = voicingExplanation(highlight);
        const controls = [...highlight.pedals, ...highlight.levers];
        const kindTags = [
          highlight.positionKind,
          voicingText,
          highlight.isPartial ? "partial" : "",
          highlight.isRootless ? "rootless" : "",
        ].filter(Boolean);
        const metaParts = [
          highlight.displaySummary,
          positionCardReason(highlight),
          highlight.grip ? `grip ${highlight.grip}` : `strings ${highlight.strings.join("-")}`,
          controls.length ? controls.join(" + ") : "no pedals/levers",
          kindTags.join(" · "),
        ].filter(Boolean);
        return `<button class="pedal-steel-fretboard__selector${isSelected ? " is-selected" : ""}" type="button" data-position-selector="${escapeHtml(highlight.id)}" data-color-role="${escapeHtml(highlight.colorRole)}" data-position-family="${escapeHtml(highlight.family)}" data-position-tier="${escapeHtml(highlight.tier)}" data-position-kind="${escapeHtml(highlight.positionKind)}" data-position-grip="${escapeHtml(highlight.grip)}" data-position-pedal-lever-key="${escapeHtml(pedalLeverOption.key)}" data-position-pedal-lever-label="${escapeHtml(pedalLeverOption.label)}" data-voicing-type="${escapeHtml(highlight.voicingType)}" data-voicing-category="${escapeHtml(voicingCategory)}" data-is-root-position="${highlight.isRootPosition ? "true" : "false"}" data-is-inversion="${highlight.isInversion ? "true" : "false"}" data-is-partial-voicing="${highlight.isPartialVoicing ? "true" : "false"}" data-is-rootless="${highlight.isRootless ? "true" : "false"}" data-visible-by-default="${highlight.visibleByDefault ? "true" : "false"}" data-has-levers="${highlight.levers.length ? "true" : "false"}" data-is-starter="${isStarterPosition(highlight) ? "true" : "false"}" data-is-full-chord="${isFullChordPosition(highlight) ? "true" : "false"}" data-is-dominant="${isDominantPosition(highlight) ? "true" : "false"}" data-is-advanced="${isAdvancedPosition(highlight) ? "true" : "false"}" data-is-more="${isMorePosition(highlight) ? "true" : "false"}" data-recommended-extra="${isRecommendedExtra ? "true" : "false"}" data-filter-visible="${isVisible ? "true" : "false"}" style="${colorStyle}${hiddenStyle}" aria-pressed="${isSelected ? "true" : "false"}"${isVisible ? "" : " hidden"}>
        <span class="pedal-steel-fretboard__selector-marker" data-color-role="${escapeHtml(highlight.colorRole)}" aria-hidden="true"></span>
        <span class="pedal-steel-fretboard__selector-main">${escapeHtml(positionSelectorLabel(highlight))}</span>
        <span class="pedal-steel-fretboard__selector-sub">${escapeHtml(metaParts.join(" · "))}</span>
      </button>`;
      })
      .join("");
    const details = model.allHighlights.map((highlight) => renderPositionDetail(highlight, selectedPositionId, visibleIds)).join("");
    const recommendedNote = model.hasRecommendedLimit
      ? `<p class="pedal-steel-fretboard__recommended-note" data-recommended-note>Showing ${Math.min(MAX_RECOMMENDED_VISIBLE_POSITIONS, model.highlights.length)} recommended positions first. Use the filters or all positions for the full map.</p>`
      : "";
    const showAllButton = model.hasRecommendedLimit
      ? `<button class="pedal-steel-fretboard__show-all" type="button" data-show-all-positions>All positions</button>`
      : "";
    return `<div class="pedal-steel-fretboard__position-tools" data-position-tools>
      ${recommendedNote}
      <div class="pedal-steel-fretboard__selector-list" aria-label="Choose a fretboard position">${buttons}</div>
      ${showAllButton}
      <p class="pedal-steel-fretboard__empty" data-position-empty${model.highlights.length ? " hidden" : ""}>No positions match these filters. Try All grips, All pedals/levers, or All positions.</p>
      ${details}
    </div>`;
  }

  function renderLegend(model) {
    if (model.highlights.length === 0 && model.legend.length === 0) {
      return "";
    }
    const legendItems = model.legend.length
      ? model.legend.map((item) => ({
        id: item.id,
        label: item.label,
        description: item.description,
        colorRole: item.colorRole,
      }))
      : model.highlights.map((highlight) => {
        const controls = [...highlight.pedals, ...highlight.levers];
        const metaParts = [
          `Fret ${highlight.fret}`,
          highlight.grip ? `grip ${highlight.grip}` : `strings ${highlight.strings.join("-")}`,
          controls.length ? controls.join(" + ") : "no pedals/levers",
          highlight.role,
          highlight.intervals.length ? `intervals ${highlight.intervals.join("; ")}` : "",
          highlight.notes.length ? highlight.notes.join("; ") : "",
          highlight.topVoice ? `top voice ${highlight.topVoice}` : "",
          highlight.displaySummary,
          highlight.explanation,
        ].filter(Boolean);
        return {
          id: highlight.id,
          label: highlight.label,
          description: metaParts.join(" · "),
          colorRole: highlight.colorRole,
        };
      });
    const items = legendItems.map((item) => {
      const colorRole = normalizeColorRole(item.colorRole, item);
      const color = getColorRole(colorRole);
      return `<li class="pedal-steel-fretboard__legend-item" data-legend-id="${escapeHtml(item.id)}" data-color-role="${escapeHtml(colorRole)}" style="--fretboard-swatch: ${color.dot}; --fretboard-glow: ${color.glow}; --fretboard-band: ${color.band}; --fretboard-card-border: ${color.dot};">
        <div class="pedal-steel-fretboard__legend-title"><span class="pedal-steel-fretboard__legend-swatch" data-color-role="${escapeHtml(colorRole)}" aria-hidden="true"></span><span>${escapeHtml(item.label)}</span></div>
        <div class="pedal-steel-fretboard__legend-meta">${escapeHtml(item.description)}</div>
      </li>`;
    }).join("");
    return `<ul class="pedal-steel-fretboard__legend" aria-label="Highlighted fretboard positions">${items}</ul>`;
  }

  function renderPedalSteelFretboard(options = {}) {
    const model = buildFretboardModel(options);
    const selectedPositionId = model.selectedPositionId;
    // Decorative underlay only. Functional strings, frets, fret markers, labels,
    // and interaction targets are drawn by SVG geometry below/above this layer.
    const html = `<figure class="pedal-steel-fretboard" data-component="PedalSteelFretboard" data-max-fret="${model.maxFret}" data-string-count="${model.stringCount}" data-spacing="equal-temperament" data-has-voicing-filters="${model.hasVoicingControls ? "true" : "false"}" data-has-grip-filters="${model.hasGripControls ? "true" : "false"}" data-has-pedal-lever-filters="${model.hasPedalLeverControls ? "true" : "false"}" data-active-grip-filters="${escapeHtml(model.gripFilters.join(","))}" data-active-pedal-lever-filters="${escapeHtml(model.pedalLeverFilters.join(","))}" data-recommended-limited="${model.hasRecommendedLimit ? "true" : "false"}" data-recommended-cap-available="${model.hasRecommendedCapAvailable ? "true" : "false"}" data-selected-position-id="${escapeHtml(selectedPositionId)}">
      ${renderFretboardFilterControls(model)}
      <div class="pedal-steel-fretboard__stage">
        <svg class="pedal-steel-fretboard__svg" viewBox="0 0 ${SVG_WIDTH} ${SVG_HEIGHT}" role="img" aria-label="10-string E9 pedal steel fretboard with highlighted positions" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <filter id="fretboard-glow" x="-80%" y="-80%" width="260%" height="260%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#f0bf69" flood-opacity="0.58" />
            </filter>
          </defs>
          <image href="${DECORATIVE_BACKGROUND_HREF}" x="${DECORATIVE_BACKGROUND_BOX.x}" y="${DECORATIVE_BACKGROUND_BOX.y}" width="${DECORATIVE_BACKGROUND_BOX.width}" height="${DECORATIVE_BACKGROUND_BOX.height}" opacity="${DECORATIVE_BACKGROUND_BOX.opacity}" preserveAspectRatio="${DECORATIVE_BACKGROUND_BOX.preserveAspectRatio}" class="pedal-steel-background" pointer-events="none" />
          <rect x="18" y="18" width="${SVG_WIDTH - 36}" height="${SVG_HEIGHT - 54}" rx="26" fill="rgba(9, 10, 10, 0.22)" stroke="rgba(240, 191, 105, 0.28)" />
          ${renderFrets(model)}
          ${renderMarkers(model)}
          ${renderStrings(model)}
          ${renderHighlights(model)}
          ${renderFretNumbers(model)}
        </svg>
      </div>
      ${renderScaleDisplay(model)}
      ${model.hidePositionTools ? "" : renderPositionTools(model)}
      ${model.hideLegend ? "" : renderLegend(model)}
    </figure>`;
    return guardRenderableHtml(html);
  }

  function guardRenderableHtml(html) {
    if (!html.includes("[object Object]")) {
      return html;
    }
    if (global.console && typeof global.console.warn === "function") {
      global.console.warn("PedalSteelFretboard blocked unsafe object string rendering.");
    }
    return html.replace(/\[object Object\]/g, "");
  }

  function selectPosition(figure, positionId) {
    if (!figure || !positionId) return;
    const selector = figure.querySelector(`[data-position-selector="${escapeSelectorValue(positionId)}"]`);
    if (selector?.hidden) return;
    figure.dataset.selectedPositionId = positionId;
    figure.querySelectorAll("[data-position-selector]").forEach((button) => {
      const isSelected = !button.hidden && button.getAttribute("data-position-selector") === positionId;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", String(isSelected));
    });
    figure.querySelectorAll("[data-position-detail]").forEach((detail) => {
      const visibleByFilter = detail.dataset.filterVisible !== "false";
      const isSelectedDetail = detail.getAttribute("data-position-detail") === positionId;
      detail.hidden = !visibleByFilter || !isSelectedDetail;
      detail.style.display = visibleByFilter && isSelectedDetail ? "" : "none";
    });
    figure.querySelectorAll(".pedal-steel-fretboard__highlight").forEach((highlight) => {
      const visibleByFilter = highlight.dataset.filterVisible !== "false";
      highlight.hidden = !visibleByFilter;
      highlight.style.display = visibleByFilter ? "" : "none";
      highlight.classList.toggle("is-filter-hidden", !visibleByFilter);
      highlight.classList.toggle("is-selected", visibleByFilter && highlight.getAttribute("data-highlight-id") === positionId);
    });
    figure.querySelectorAll("[data-legend-id]").forEach((legend) => {
      const legendId = legend.getAttribute("data-legend-id");
      const visiblePosition = figure.querySelector(`[data-position-selector="${escapeSelectorValue(legendId)}"]`);
      if (visiblePosition) {
        legend.hidden = visiblePosition.hidden;
        legend.style.display = visiblePosition.hidden ? "none" : "";
      }
    });
  }

  function readActiveVoicingFilter(figure) {
    if (figure?.dataset?.hasVoicingFilters !== "true") {
      return "all";
    }
    return figure.querySelector("[data-voicing-filter].is-selected")?.getAttribute("data-voicing-filter") || "all";
  }

  function readActiveGripFilter(figure) {
    return readActiveGripFilters(figure)[0] || "all";
  }

  function readActiveGripFilters(figure) {
    if (figure?.dataset?.hasGripFilters !== "true") {
      return [];
    }
    const selected = Array.from(figure.querySelectorAll("[data-grip-filter].is-selected"))
      .map((button) => button.getAttribute("data-grip-filter") || "")
      .filter((value) => value && value !== "all");
    return Array.from(new Set(selected));
  }

  function readActivePedalLeverFilters(figure) {
    if (figure?.dataset?.hasPedalLeverFilters !== "true") {
      return [];
    }
    const selected = Array.from(figure.querySelectorAll("[data-pedal-lever-filter].is-selected"))
      .map((button) => button.getAttribute("data-pedal-lever-filter") || "")
      .filter((value) => value && value !== "all");
    return Array.from(new Set(selected));
  }

  function positionElementMatchesVoicing(element, voicingFilter) {
    if (!voicingFilter || voicingFilter === "all") {
      return true;
    }
    if (voicingFilter === "recommended") {
      return element.getAttribute("data-visible-by-default") === "true";
    }
    if (voicingFilter === "starter") {
      return element.getAttribute("data-is-starter") === "true";
    }
    if (voicingFilter === "full-chord") {
      return element.getAttribute("data-is-full-chord") === "true";
    }
    if (voicingFilter === "dominant") {
      return element.getAttribute("data-is-dominant") === "true";
    }
    return element.getAttribute("data-voicing-category") === voicingFilter;
  }

  function positionElementMatchesGrip(element, gripFilter) {
    if (Array.isArray(gripFilter)) {
      return gripFilter.length === 0 || gripFilter.includes(element.getAttribute("data-position-grip"));
    }
    if (!gripFilter || gripFilter === "all") {
      return true;
    }
    return element.getAttribute("data-position-grip") === gripFilter;
  }

  function positionElementMatchesPedalLever(element, pedalLeverFilters) {
    if (!pedalLeverFilters || pedalLeverFilters.length === 0) {
      return true;
    }
    return pedalLeverFilters.includes(element.getAttribute("data-position-pedal-lever-key"));
  }

  function setPositionElementFilterVisibility(element, isVisible) {
    element.dataset.filterVisible = String(isVisible);
    element.hidden = !isVisible;
    element.style.display = isVisible ? "" : "none";
    element.classList.toggle("is-filter-hidden", !isVisible);
  }

  function syncPositionElementVisibility(figure, visibleIds) {
    figure.querySelectorAll("[data-position-selector]").forEach((selector) => {
      setPositionElementFilterVisibility(selector, visibleIds.has(selector.getAttribute("data-position-selector")));
    });
    figure.querySelectorAll("[data-position-detail]").forEach((detail) => {
      setPositionElementFilterVisibility(detail, visibleIds.has(detail.getAttribute("data-position-detail")));
    });
    figure.querySelectorAll(".pedal-steel-fretboard__highlight").forEach((highlight) => {
      setPositionElementFilterVisibility(highlight, visibleIds.has(highlight.getAttribute("data-highlight-id")));
    });
    figure.querySelectorAll("[data-legend-id]").forEach((legend) => {
      const legendId = legend.getAttribute("data-legend-id");
      const matchingSelector = legendId
        ? figure.querySelector(`[data-position-selector="${escapeSelectorValue(legendId)}"]`)
        : null;
      if (matchingSelector) {
        setPositionElementFilterVisibility(legend, visibleIds.has(legendId));
      }
    });
  }

  function updateSelectedFilterButton(figure, selector, attributeName, value) {
    const button = figure.querySelector(`[${attributeName}="${escapeSelectorValue(value)}"]`);
    if (!button) return;
    figure.querySelectorAll(selector).forEach((filterButton) => {
      const selected = filterButton === button;
      filterButton.classList.toggle("is-selected", selected);
      filterButton.setAttribute("aria-pressed", String(selected));
      if (filterButton.hasAttribute("role") && filterButton.getAttribute("role") === "tab") {
        filterButton.setAttribute("aria-selected", String(selected));
      }
    });
  }

  function updateSelectedGripFilterButtons(figure, changedGripFilter) {
    if (!changedGripFilter) return;
    const allButton = figure.querySelector('[data-grip-filter="all"]');
    const gripButtons = Array.from(figure.querySelectorAll('[data-grip-filter]:not([data-grip-filter="all"])'));
    if (changedGripFilter === "all") {
      gripButtons.forEach((button) => {
        button.classList.remove("is-selected");
        button.setAttribute("aria-pressed", "false");
      });
      allButton?.classList.add("is-selected");
      allButton?.setAttribute("aria-pressed", "true");
      return;
    }
    const changedButton = figure.querySelector(`[data-grip-filter="${escapeSelectorValue(changedGripFilter)}"]`);
    if (!changedButton) return;
    const nextSelected = !changedButton.classList.contains("is-selected");
    changedButton.classList.toggle("is-selected", nextSelected);
    changedButton.setAttribute("aria-pressed", String(nextSelected));
    const hasSelectedGrip = gripButtons.some((button) => button.classList.contains("is-selected"));
    if (allButton) {
      allButton.classList.toggle("is-selected", !hasSelectedGrip);
      allButton.setAttribute("aria-pressed", String(!hasSelectedGrip));
    }
  }

  function updateSelectedPedalLeverFilterButtons(figure, changedPedalLeverFilter) {
    if (!changedPedalLeverFilter) return;
    const allButton = figure.querySelector('[data-pedal-lever-filter="all"]');
    const pedalLeverButtons = Array.from(figure.querySelectorAll('[data-pedal-lever-filter]:not([data-pedal-lever-filter="all"])'));
    if (changedPedalLeverFilter === "all") {
      pedalLeverButtons.forEach((button) => {
        button.classList.remove("is-selected");
        button.setAttribute("aria-pressed", "false");
      });
      allButton?.classList.add("is-selected");
      allButton?.setAttribute("aria-pressed", "true");
      return;
    }
    const changedButton = figure.querySelector(`[data-pedal-lever-filter="${escapeSelectorValue(changedPedalLeverFilter)}"]`);
    if (!changedButton) return;
    const nextSelected = !changedButton.classList.contains("is-selected");
    changedButton.classList.toggle("is-selected", nextSelected);
    changedButton.setAttribute("aria-pressed", String(nextSelected));
    const hasSelectedPedalLever = pedalLeverButtons.some((button) => button.classList.contains("is-selected"));
    if (allButton) {
      allButton.classList.toggle("is-selected", !hasSelectedPedalLever);
      allButton.setAttribute("aria-pressed", String(!hasSelectedPedalLever));
    }
  }

  function updatePositionFilter(figure, changedVoicingFilter, changedGripFilter, changedPedalLeverFilter) {
    if (!figure) return;
    if (changedVoicingFilter) {
      updateSelectedFilterButton(figure, "[data-voicing-filter]", "data-voicing-filter", changedVoicingFilter);
      if (changedVoicingFilter === "all" && !changedGripFilter) {
        updateSelectedGripFilterButtons(figure, "all");
      }
      if (changedVoicingFilter === "all" && !changedPedalLeverFilter) {
        updateSelectedPedalLeverFilterButtons(figure, "all");
      }
    }
    if (changedGripFilter) {
      updateSelectedGripFilterButtons(figure, changedGripFilter);
    }
    if (changedPedalLeverFilter) {
      updateSelectedPedalLeverFilterButtons(figure, changedPedalLeverFilter);
    }
    const voicingFilter = readActiveVoicingFilter(figure);
    const gripFilters = readActiveGripFilters(figure);
    const pedalLeverFilters = readActivePedalLeverFilters(figure);
    figure.dataset.activeGripFilters = gripFilters.join(",");
    figure.dataset.activePedalLeverFilters = pedalLeverFilters.join(",");
    const limitRecommended = figure.dataset.recommendedCapAvailable === "true" &&
      voicingFilter === "recommended" &&
      gripFilters.length === 0 &&
      pedalLeverFilters.length === 0;
    figure.dataset.recommendedLimited = String(limitRecommended);
    const showAll = figure.querySelector("[data-show-all-positions]");
    if (showAll) {
      showAll.hidden = !limitRecommended;
    }
    const note = figure.querySelector("[data-recommended-note]");
    if (note) {
      note.hidden = !limitRecommended;
    }
    const visibleIds = new Set();
    figure.querySelectorAll("[data-position-selector]").forEach((item) => {
      const isVisible = positionElementMatchesVoicing(item, voicingFilter) &&
        positionElementMatchesGrip(item, gripFilters) &&
        positionElementMatchesPedalLever(item, pedalLeverFilters) &&
        !(limitRecommended && item.dataset.recommendedExtra === "true");
      if (isVisible) {
        visibleIds.add(item.getAttribute("data-position-selector"));
      }
    });
    syncPositionElementVisibility(figure, visibleIds);
    const emptyState = figure.querySelector("[data-position-empty]");
    const firstVisible = figure.querySelector("[data-position-selector]:not([hidden])");
    if (firstVisible) {
      if (emptyState) {
        emptyState.hidden = true;
      }
      selectPosition(figure, firstVisible.getAttribute("data-position-selector"));
    } else {
      if (emptyState) {
        emptyState.hidden = false;
      }
      figure.dataset.selectedPositionId = "";
    }
  }

  function showAllRecommendedPositions(figure) {
    if (!figure) return;
    updatePositionFilter(figure, "all", "all", "all");
  }

  function bindFretboardInteractions(figure) {
    if (!figure) return;
    const hasPositionSelectors = Boolean(figure.querySelector("[data-position-selector]"));
    figure.querySelector("[data-show-all-positions]")?.addEventListener("click", () => {
      showAllRecommendedPositions(figure);
    });
    figure.querySelectorAll("[data-voicing-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        updatePositionFilter(figure, button.getAttribute("data-voicing-filter") || "all", "");
      });
    });
    figure.querySelectorAll("[data-grip-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        updatePositionFilter(figure, "", button.getAttribute("data-grip-filter") || "all", "");
      });
    });
    figure.querySelectorAll("[data-pedal-lever-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        updatePositionFilter(figure, "", "", button.getAttribute("data-pedal-lever-filter") || "all");
      });
    });
    figure.querySelectorAll("[data-position-selector]").forEach((button) => {
      button.addEventListener("click", () => {
        selectPosition(figure, button.getAttribute("data-position-selector"));
      });
    });
    if (hasPositionSelectors) {
      updatePositionFilter(figure);
      selectPosition(figure, figure.dataset.selectedPositionId);
    }
  }

  function injectPedalSteelFretboardStyles(doc) {
    const targetDocument = doc || global.document;
    if (!targetDocument || targetDocument.getElementById(STYLE_ID)) {
      return;
    }
    const style = targetDocument.createElement("style");
    style.id = STYLE_ID;
    style.textContent = STYLE_TEXT;
    targetDocument.head.appendChild(style);
  }

  function mountPedalSteelFretboard(container, options = {}) {
    if (!container) {
      throw new Error("PedalSteelFretboard requires a container element.");
    }
    injectPedalSteelFretboardStyles(container.ownerDocument);
    container.innerHTML = renderPedalSteelFretboard(options);
    const figure = container.querySelector("[data-component='PedalSteelFretboard']");
    bindFretboardInteractions(figure);
    return figure;
  }

  const DEMO_HIGHLIGHTS = [
    {
      id: "g-major-open-3",
      label: "G major",
      fret: 3,
      strings: [4, 5, 6],
      role: "No-pedals position",
      colorRole: "open",
    },
    {
      id: "g-major-af-6",
      label: "G major",
      fret: 6,
      strings: [4, 5, 6],
      pedals: ["A"],
      levers: ["E raise/F lever"],
      role: "A+F position",
      colorRole: "a-f",
    },
    {
      id: "g-major-ab-10",
      label: "G major",
      fret: 10,
      strings: [4, 5, 6],
      pedals: ["A", "B"],
      role: "A+B position",
      colorRole: "a-b",
    },
  ];

  const DEMO_POSITIONS = [
    {
      id: "g-position-open-3",
      label: "G major",
      fret: 3,
      strings: [4, 5, 6],
      grip: [4, 5, 6],
      role: "No-pedals position",
      notes: "Open G pocket",
      intervals: ["1", "3", "5"],
      colorRole: "open",
      positionKind: "starter",
      validationStatus: "pitch_validated",
    },
    {
      id: "g-position-af-6",
      label: "G major",
      fret: 6,
      strings: [4, 5, 6],
      grip: [4, 5, 6],
      pedals: ["A"],
      levers: ["E raise/F lever"],
      role: "A+F position",
      explanation: "A pedal plus the E raise makes the G pocket at fret 6.",
      colorRole: "a-f",
      positionKind: "starter",
      validationStatus: "pitch_validated",
    },
    {
      id: "g-position-ab-10",
      label: "G major",
      fret: 10,
      strings: [4, 5, 6],
      grip: [4, 5, 6],
      pedals: ["A", "B"],
      role: "A+B position",
      explanation: "Pedals-down G position at fret 10.",
      colorRole: "a-b",
      positionKind: "starter",
      validationStatus: "pitch_validated",
    },
  ];

  const api = {
    COMMON_FRET_MARKERS,
    DEFAULT_E9_TUNING,
    DEMO_HIGHLIGHTS,
    DEMO_POSITIONS,
    STYLE_TEXT,
    buildFretboardModel,
    injectPedalSteelFretboardStyles,
    mountPedalSteelFretboard,
    normalizedFretPosition,
    renderPedalSteelFretboard,
  };

  global.STEEL_RAG_FRETBOARD = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
