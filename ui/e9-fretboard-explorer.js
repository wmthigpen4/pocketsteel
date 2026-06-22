(function () {
  "use strict";

  const payload = window.STEEL_RAG_E9_EXPLORER_PAYLOAD;
  const fretboardApi = window.STEEL_RAG_FRETBOARD;

  const CORE_GROUPS = new Set(["3-4-5", "4-5-6", "5-6-8", "6-8-10"]);
  const ADVANCED_GROUPS = new Set(["5-6-7", "6-7-10", "5-7-8"]);
  const TWO_STRING_GROUPS = new Set(["3-5", "5-6", "6-10", "4-6", "3-4"]);
  const HARMONY_LABELS = {
    two_string_harmonized: "2-string harmonized scale",
    three_string_diatonic: "3-string diatonic harmony",
  };

  const els = {
    key: document.getElementById("explorer-key"),
    scale: document.getElementById("explorer-scale"),
    harmony: document.getElementById("explorer-harmony"),
    stringGroup: document.getElementById("explorer-string-group"),
    scaleNotes: document.getElementById("explorer-scale-notes"),
    resultCount: document.getElementById("explorer-result-count"),
    fretboard: document.getElementById("explorer-fretboard"),
    rowList: document.getElementById("explorer-row-list"),
    empty: document.getElementById("explorer-empty"),
  };

  function toArray(value) {
    return Array.isArray(value) ? value.filter(Boolean) : [];
  }

  function formatValue(value, emptyText = "none") {
    if (value === null || value === undefined || value === "" || value === "not_found") {
      return emptyText;
    }
    if (Array.isArray(value)) {
      const rendered = value.map((item) => formatValue(item, "")).filter(Boolean);
      return rendered.length ? rendered.join(", ") : emptyText;
    }
    if (typeof value === "object") {
      const entries = Object.entries(value)
        .filter(([, entryValue]) => entryValue !== null && entryValue !== undefined && entryValue !== "")
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, entryValue]) => `${key}: ${formatValue(entryValue, "")}`)
        .filter((entry) => !entry.endsWith(": "));
      return entries.length ? entries.join("; ") : emptyText;
    }
    return String(value);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function normalizePedals(row) {
    return toArray(row.pedals).concat(toArray(row.levers));
  }

  function rowsForScale(scale) {
    return payload?.positions?.filter((row) => row.key === "G" && row.scale_type === scale) || [];
  }

  function rowMatchesHarmony(row, harmony) {
    if (harmony === "two_string_harmonized") {
      return row.harmony_type === "two_string_harmonized";
    }
    return row.harmony_type === "three_string_diatonic" || row.harmony_type === "advanced_pocket";
  }

  function rowsForScaleAndHarmony(scale, harmony) {
    return rowsForScale(scale).filter((row) => rowMatchesHarmony(row, harmony));
  }

  function availableHarmonies(scale) {
    return Object.keys(HARMONY_LABELS).filter((harmony) => rowsForScaleAndHarmony(scale, harmony).length > 0);
  }

  function uniqueGroups(rows, allowedGroups) {
    const present = new Set(rows.map((row) => row.string_group));
    return Array.from(allowedGroups).filter((group) => present.has(group));
  }

  function option(value, label, selectedValue) {
    return `<option value="${escapeHtml(value)}"${value === selectedValue ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }

  function optionGroup(label, groups, selectedValue) {
    if (!groups.length) {
      return "";
    }
    return `<optgroup label="${escapeHtml(label)}">${groups.map((group) => option(group, group, selectedValue)).join("")}</optgroup>`;
  }

  function updateHarmonyOptions() {
    const scale = els.scale.value;
    const validHarmonies = availableHarmonies(scale);
    Array.from(els.harmony.options).forEach((item) => {
      item.disabled = !validHarmonies.includes(item.value);
    });
    if (!validHarmonies.includes(els.harmony.value)) {
      els.harmony.value = validHarmonies[0] || "";
    }
  }

  function updateStringGroupOptions() {
    const scale = els.scale.value;
    const harmony = els.harmony.value;
    const rows = rowsForScaleAndHarmony(scale, harmony);
    const currentValue = els.stringGroup.value;
    const allLabel = harmony === "two_string_harmonized" ? "All 2-string groups" : "All 3-string groups";
    let html = option("all", allLabel, currentValue);

    if (harmony === "two_string_harmonized") {
      html += optionGroup("2-string groups", uniqueGroups(rows, TWO_STRING_GROUPS), currentValue);
    } else {
      html += optionGroup("Core grips", uniqueGroups(rows, CORE_GROUPS), currentValue);
      html += optionGroup("Advanced swaps", uniqueGroups(rows, ADVANCED_GROUPS), currentValue);
    }

    els.stringGroup.innerHTML = html;
    if (!Array.from(els.stringGroup.options).some((item) => item.value === currentValue)) {
      els.stringGroup.value = "all";
    }
  }

  function updateControls() {
    updateHarmonyOptions();
    updateStringGroupOptions();
  }

  function getRows() {
    if (!payload || !Array.isArray(payload.positions)) {
      return [];
    }

    const scale = els.scale.value;
    const harmony = els.harmony.value;
    const stringGroup = els.stringGroup.value;

    return payload.positions
      .filter((row) => row.key === "G")
      .filter((row) => row.scale_type === scale)
      .filter((row) => rowMatchesHarmony(row, harmony))
      .filter((row) => {
        if (stringGroup === "all") {
          return true;
        }
        return row.string_group === stringGroup;
      })
      .sort((a, b) => {
        const byFret = Number(a.fret || 0) - Number(b.fret || 0);
        if (byFret) {
          return byFret;
        }
        return String(a.id || "").localeCompare(String(b.id || ""));
      });
  }

  function getScaleNotes() {
    const notes = payload?.query?.display_scale_notes?.[els.scale.value];
    return Array.isArray(notes) ? notes.join(" ") : "Unavailable";
  }

  function isAdvanced(row) {
    return ADVANCED_GROUPS.has(row.string_group) || row.harmony_type === "advanced_pocket";
  }

  function groupLabel(row) {
    if (isAdvanced(row)) {
      return row.string_group === "5-7-8" ? "Advanced swap - E-lower pocket" : "Advanced swap";
    }
    if (CORE_GROUPS.has(row.string_group)) {
      return "Core grip";
    }
    if (TWO_STRING_GROUPS.has(row.string_group)) {
      return "2-string pair";
    }
    return "Explorer row";
  }

  function colorRoleForRow(row) {
    if (row.string_group === "5-7-8" || String(row.position_family || "").includes("e_lower")) {
      return "e-lower";
    }
    if (isAdvanced(row)) {
      return "advanced";
    }
    if (row.harmony_type === "two_string_harmonized") {
      return "alternate";
    }
    return "primary";
  }

  function labelForRow(row) {
    const chord = row.chord_name || row.chord_function || "Position";
    const summary = row.display_summary || "";
    return summary ? summary.replace(/\bat fret\b/i, "@ fret") : chord;
  }

  function asFretboardPosition(row) {
    return {
      ...row,
      id: row.id,
      label: labelForRow(row),
      fret: row.fret,
      strings: row.strings,
      grip: row.string_group,
      pedals: normalizePedals(row),
      levers: toArray(row.levers),
      notes: row.display_notes || row.notes,
      intervals: row.intervals,
      explanation: row.display_summary || row.explanation,
      colorRole: colorRoleForRow(row),
      visibleByDefault: true,
    };
  }

  function detailRow(label, value) {
    const rendered = formatValue(value);
    if (rendered === "none") {
      return "";
    }
    return `<div class="explorer-detail-row"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(rendered)}</dd></div>`;
  }

  function renderCards(rows) {
    els.rowList.innerHTML = rows
      .map((row) => {
        const cardClass = isAdvanced(row) ? " explorer-row-card--advanced" : "";
        const warnings = toArray(row.warnings);
        return `
          <article class="explorer-row-card${cardClass}" data-string-group="${escapeHtml(row.string_group)}" data-harmony-type="${escapeHtml(row.harmony_type)}">
            <div class="explorer-row-card__header">
              <span class="explorer-row-card__kind">${escapeHtml(groupLabel(row))}</span>
              <strong>${escapeHtml(formatValue(row.display_summary || row.chord_name || row.id))}</strong>
            </div>
            <dl class="explorer-detail-grid">
              ${detailRow("Display notes", row.display_notes)}
              ${detailRow("Top voice", row.display_top_voice)}
              ${detailRow("Fret", row.fret)}
              ${detailRow("String group", row.string_group)}
              ${detailRow("Pedals / levers", normalizePedals(row))}
              ${detailRow("Per-string changes", row.per_string_changes)}
              ${detailRow("Warnings", warnings)}
              ${detailRow("Pitch validated", row.pitch_validated === true ? "yes" : "no")}
            </dl>
          </article>
        `;
      })
      .join("");
  }

  function renderFretboard(rows) {
    if (!fretboardApi || typeof fretboardApi.mountPedalSteelFretboard !== "function") {
      els.fretboard.innerHTML = '<p class="explorer-empty">Fretboard renderer unavailable.</p>';
      return;
    }

    fretboardApi.mountPedalSteelFretboard(els.fretboard, {
      title: "Validated Explorer positions",
      description: "Deterministic E9 Explorer data. This is not corpus or RAG output.",
      positions: rows.map(asFretboardPosition),
      highlights: [],
      legend: payload.legend || [],
      query: payload.query || {},
      hideFilterControls: true,
      showHighlightLabels: false,
    });
  }

  function render() {
    const rows = getRows();
    els.scaleNotes.textContent = getScaleNotes();
    els.resultCount.textContent = `${rows.length} validated row${rows.length === 1 ? "" : "s"}`;
    els.empty.hidden = rows.length > 0;
    els.empty.textContent = rows.length
      ? ""
      : `No validated ${HARMONY_LABELS[els.harmony.value] || "Explorer"} rows are available for ${els.scale.options[els.scale.selectedIndex]?.text || "this scale"} yet.`;
    renderCards(rows);
    renderFretboard(rows);

    if (els.rowList.textContent.includes("[object Object]") || els.fretboard.textContent.includes("[object Object]")) {
      console.warn("Explorer rendered an unsafe object string.");
    }
  }

  function init() {
    if (!payload) {
      els.empty.hidden = false;
      els.empty.textContent = "Explorer data failed to load.";
      return;
    }

    els.scale.addEventListener("change", () => {
      updateControls();
      render();
    });
    els.harmony.addEventListener("change", () => {
      updateStringGroupOptions();
      render();
    });
    els.stringGroup.addEventListener("change", () => {
      render();
    });

    updateControls();
    render();
  }

  init();
  window.STEEL_RAG_E9_EXPLORER = {
    availableHarmonies,
    rowsForScaleAndHarmony,
    uniqueGroups,
  };
})();
