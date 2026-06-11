(function (global) {
  "use strict";

  const DEFAULT_E9_TUNING = ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"];
  const COMMON_FRET_MARKERS = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24];
  const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg";
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
    primary: {
      dot: "#f0bf69",
      glow: "rgba(240, 191, 105, 0.5)",
      band: "rgba(240, 191, 105, 0.16)",
      text: "#fff3d5",
    },
    alternate: {
      dot: "#d8a44d",
      glow: "rgba(216, 164, 77, 0.46)",
      band: "rgba(216, 164, 77, 0.14)",
      text: "#ffe5ad",
    },
    movement: {
      dot: "#8fd5ff",
      glow: "rgba(143, 213, 255, 0.34)",
      band: "rgba(143, 213, 255, 0.12)",
      text: "#d8f0ff",
    },
    warning: {
      dot: "#ff9f6e",
      glow: "rgba(255, 159, 110, 0.44)",
      band: "rgba(255, 159, 110, 0.14)",
      text: "#ffe1d0",
    },
  };

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

.pedal-steel-fretboard__legend-item {
  border: 1px solid rgba(240, 191, 105, 0.25);
  border-radius: 12px;
  background: rgba(12, 12, 11, 0.8);
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

  function normalizedFretPosition(fret, maxFret = 24) {
    const safeMax = Math.max(1, Number(maxFret) || 24);
    const safeFret = clampNumber(fret, 0, safeMax);
    return 1 - Math.pow(2, -safeFret / 12);
  }

  function getColorRole(colorRole) {
    return COLOR_ROLES[colorRole] || COLOR_ROLES.primary;
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
    return value.map(String).map((item) => item.trim()).filter(Boolean);
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
      : uniqueStrings.join("-");
    return {
      id: String(item.id || `${sourceType}-${index + 1}`),
      label: String(item.label || `Position ${index + 1}`),
      fret: clampNumber(item.fret, 0, maxFret),
      strings: uniqueStrings,
      grip,
      pedals: normalizeTextList(item.pedals),
      levers: normalizeTextList(item.levers),
      role: String(item.role || ""),
      notes: String(item.notes || ""),
      explanation: String(item.explanation || ""),
      intervals: normalizeTextList(item.intervals),
      sourceType,
      colorRole: COLOR_ROLES[item.colorRole] ? item.colorRole : index === 0 ? "primary" : index === 1 ? "alternate" : "movement",
    };
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
    const highlights = sourcePositions
      .map((position, index) => normalizePosition(position, index, maxFret, stringCount, positionSourceType))
      .filter((highlight) => highlight.strings.length > 0)
      .map((highlight) => ({
        ...highlight,
        x: LAYOUT.nutX + normalizedFretPosition(highlight.fret, maxFret) * fretboardWidth,
        stringYs: highlight.strings.map((stringNumber) => strings[stringNumber - 1].y),
      }));

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
      highlights,
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
    return (fretX(model, fret) + fretX(model, fret + 1)) / 2;
  }

  function renderFretMarkerShape({ x, y, size, isEmphasis, fret }) {
    const outer = [
      `${x.toFixed(3)},${(y - size).toFixed(3)}`,
      `${(x + size * 0.32).toFixed(3)},${(y - size * 0.32).toFixed(3)}`,
      `${(x + size).toFixed(3)},${y.toFixed(3)}`,
      `${(x + size * 0.32).toFixed(3)},${(y + size * 0.32).toFixed(3)}`,
      `${x.toFixed(3)},${(y + size).toFixed(3)}`,
      `${(x - size * 0.32).toFixed(3)},${(y + size * 0.32).toFixed(3)}`,
      `${(x - size).toFixed(3)},${y.toFixed(3)}`,
      `${(x - size * 0.32).toFixed(3)},${(y - size * 0.32).toFixed(3)}`,
    ].join(" ");
    const innerSize = size * 0.36;
    const inner = [
      `${x.toFixed(3)},${(y - innerSize).toFixed(3)}`,
      `${(x + innerSize).toFixed(3)},${y.toFixed(3)}`,
      `${x.toFixed(3)},${(y + innerSize).toFixed(3)}`,
      `${(x - innerSize).toFixed(3)},${y.toFixed(3)}`,
    ].join(" ");
    const fill = isEmphasis ? "rgba(255, 246, 223, 0.9)" : "rgba(255, 246, 223, 0.72)";
    const accent = isEmphasis ? "rgba(240, 191, 105, 0.64)" : "rgba(240, 191, 105, 0.38)";
    return `<g data-fret-marker="${fret}" data-fret-marker-emphasis="${isEmphasis ? "true" : "false"}" data-fret-marker-placement="space" data-fret-marker-style="printed-star" transform="translate(0 0)">
      <polygon data-fret-marker-star="${fret}" points="${outer}" fill="${fill}" stroke="rgba(7, 8, 8, 0.82)" stroke-width="${isEmphasis ? "2.1" : "1.6"}" opacity="${isEmphasis ? "0.92" : "0.72"}" />
      <polygon data-fret-marker-center="${fret}" points="${inner}" fill="${accent}" opacity="${isEmphasis ? "0.9" : "0.76"}" />
    </g>`;
  }

  function renderMarkers(model) {
    return model.markers
      .map((fret) => {
        const x = markerX(model, fret);
        const markerY = SVG_HEIGHT - 82;
        const isEmphasis = fret === 12 || fret === 24;
        const size = isEmphasis ? 9.5 : 6.2;
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
    const minY = Math.min(...highlight.stringYs);
    const maxY = Math.max(...highlight.stringYs);
    const bandHeight = Math.max(34, maxY - minY + 26);
    const bandY = minY - 13;
    const labelY = Math.max(26, bandY - 12);
    const dataAttrs = `data-highlight-id="${escapeHtml(highlight.id)}" data-highlight-fret="${highlight.fret}" data-highlight-strings="${escapeHtml(highlight.strings.join(","))}" data-color-role="${escapeHtml(highlight.colorRole)}"`;
    const band = highlight.strings.length > 1
      ? `<rect data-highlight-band ${dataAttrs} x="${(highlight.x - 18).toFixed(3)}" y="${bandY.toFixed(3)}" width="36" height="${bandHeight.toFixed(3)}" rx="18" fill="${color.band}" stroke="${color.dot}" stroke-opacity="0.34" />`
      : "";
    const dots = highlight.stringYs
      .map((y, index) => {
        const stringNumber = highlight.strings[index];
        return `<rect data-highlight-dot ${dataAttrs} data-highlight-string="${stringNumber}" x="${(highlight.x - 15).toFixed(3)}" y="${(y - 9).toFixed(3)}" width="30" height="18" rx="9" fill="${color.dot}" fill-opacity="0.95" stroke="#fff6df" stroke-opacity="0.38" filter="url(#fretboard-glow)" />`;
      })
      .join("");
    return `<g class="pedal-steel-fretboard__highlight" ${dataAttrs}>
      ${band}
      ${dots}
      <text data-highlight-label="${escapeHtml(highlight.id)}" x="${highlight.x.toFixed(3)}" y="${labelY.toFixed(3)}" text-anchor="middle" fill="${color.text}" font-size="18" font-weight="700">${escapeHtml(highlight.label)}</text>
    </g>`;
  }

  function renderHighlights(model) {
    return model.highlights.map(renderHighlight).join("");
  }

  function renderLegend(model) {
    if (model.highlights.length === 0) {
      return "";
    }
    const items = model.highlights
      .map((highlight) => {
        const color = getColorRole(highlight.colorRole);
        const controls = [...highlight.pedals, ...highlight.levers];
        const metaParts = [
          `Fret ${highlight.fret}`,
          highlight.grip ? `grip ${highlight.grip}` : `strings ${highlight.strings.join("-")}`,
          controls.length ? controls.join(" + ") : "no pedals/levers",
          highlight.role,
          highlight.intervals.length ? `intervals ${highlight.intervals.join("-")}` : "",
          highlight.notes,
          highlight.explanation,
        ].filter(Boolean);
        return `<li class="pedal-steel-fretboard__legend-item" data-legend-id="${escapeHtml(highlight.id)}" style="--fretboard-swatch: ${color.dot}; --fretboard-glow: ${color.glow};">
          <div class="pedal-steel-fretboard__legend-title"><span class="pedal-steel-fretboard__legend-swatch" aria-hidden="true"></span><span>${escapeHtml(highlight.label)}</span></div>
          <div class="pedal-steel-fretboard__legend-meta">${escapeHtml(metaParts.join(" · "))}</div>
        </li>`;
      })
      .join("");
    return `<ul class="pedal-steel-fretboard__legend" aria-label="Highlighted fretboard positions">${items}</ul>`;
  }

  function renderPedalSteelFretboard(options = {}) {
    const model = buildFretboardModel(options);
    // Decorative underlay only. Functional strings, frets, fret markers, labels,
    // and interaction targets are drawn by SVG geometry below/above this layer.
    return `<figure class="pedal-steel-fretboard" data-component="PedalSteelFretboard" data-max-fret="${model.maxFret}" data-string-count="${model.stringCount}" data-spacing="equal-temperament">
      <div class="pedal-steel-fretboard__stage">
        <svg class="pedal-steel-fretboard__svg" viewBox="0 0 ${SVG_WIDTH} ${SVG_HEIGHT}" role="img" aria-label="10-string E9 pedal steel fretboard with highlighted positions" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <filter id="fretboard-glow" x="-80%" y="-80%" width="260%" height="260%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#f0bf69" flood-opacity="0.58" />
            </filter>
          </defs>
          <image href="${DECORATIVE_BACKGROUND_HREF}" x="${DECORATIVE_BACKGROUND_BOX.x}" y="${DECORATIVE_BACKGROUND_BOX.y}" width="${DECORATIVE_BACKGROUND_BOX.width}" height="${DECORATIVE_BACKGROUND_BOX.height}" opacity="${DECORATIVE_BACKGROUND_BOX.opacity}" preserveAspectRatio="${DECORATIVE_BACKGROUND_BOX.preserveAspectRatio}" class="pedal-steel-background" pointer-events="none" />
          <rect x="18" y="18" width="${SVG_WIDTH - 36}" height="${SVG_HEIGHT - 54}" rx="26" fill="rgba(9, 10, 10, 0.22)" stroke="rgba(240, 191, 105, 0.28)" />
          <text x="${LAYOUT.left}" y="34" fill="rgba(240, 191, 105, 0.82)" font-size="18" font-weight="700" letter-spacing="3">E9 PEDAL STEEL</text>
          ${renderFrets(model)}
          ${renderMarkers(model)}
          ${renderStrings(model)}
          ${renderHighlights(model)}
          ${renderFretNumbers(model)}
        </svg>
      </div>
      ${renderLegend(model)}
    </figure>`;
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
    return container.querySelector("[data-component='PedalSteelFretboard']");
  }

  const DEMO_HIGHLIGHTS = [
    {
      id: "g-major-open-3",
      label: "G major",
      fret: 3,
      strings: [4, 5, 6],
      role: "No-pedals position",
      colorRole: "primary",
    },
    {
      id: "g-major-af-6",
      label: "G major",
      fret: 6,
      strings: [4, 5, 6],
      pedals: ["A"],
      levers: ["E raise/F lever"],
      role: "A+F position",
      colorRole: "alternate",
    },
    {
      id: "g-major-ab-10",
      label: "G major",
      fret: 10,
      strings: [4, 5, 6],
      pedals: ["A", "B"],
      role: "A+B position",
      colorRole: "movement",
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
      colorRole: "primary",
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
      colorRole: "alternate",
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
      colorRole: "movement",
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
