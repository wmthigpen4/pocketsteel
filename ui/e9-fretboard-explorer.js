(function () {
  "use strict";

  const payloadsByKey = window.STEEL_RAG_E9_EXPLORER_PAYLOADS || {};
  const payloadsByCopedent = window.STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT || {};
  const fallbackPayload = window.STEEL_RAG_E9_EXPLORER_PAYLOAD;
  const fretboardApi = window.STEEL_RAG_FRETBOARD;

  const DEFAULT_COPEDENT_ID = "emmons-e9-basic";
  const CORE_GROUPS = new Set(["3-4-5", "4-5-6", "5-6-8", "6-8-10"]);
  const ADVANCED_GROUPS = new Set(["5-6-7", "6-7-10", "5-7-8"]);
  const TWO_STRING_GROUPS = new Set(["3-5", "5-6", "6-10", "4-6", "3-4"]);
  const FIVE_EIGHT_GROUPS = new Set(["5-8"]);
  const TWO_STRING_DISPLAY_GROUPS = new Set([...TWO_STRING_GROUPS, ...FIVE_EIGHT_GROUPS]);
  const KEY_OPTIONS = [
    { value: "C", label: "C" },
    { value: "Db", label: "C# (or D♭)" },
    { value: "D", label: "D" },
    { value: "Eb", label: "D# (or E♭)" },
    { value: "E", label: "E" },
    { value: "F", label: "F" },
    { value: "Gb", label: "F# (or G♭)" },
    { value: "G", label: "G" },
    { value: "Ab", label: "G# (or A♭)" },
    { value: "A", label: "A" },
    { value: "Bb", label: "A# (or B♭)" },
    { value: "B", label: "B" },
  ];
  const HARMONY_LABELS = {
    two_string_harmonized: "2-string harmonized scale",
    three_string_diatonic: "3-string diatonic harmony",
  };

  const els = {
    key: document.getElementById("explorer-key"),
    copedent: document.getElementById("explorer-copedent"),
    scale: document.getElementById("explorer-scale"),
    harmony: document.getElementById("explorer-harmony"),
    stringGroup: document.getElementById("explorer-string-group"),
    scaleNotes: document.getElementById("explorer-scale-notes"),
    resultCount: document.getElementById("explorer-result-count"),
    labelModeButtons: document.querySelectorAll("[data-explorer-label-mode]"),
    copedentDialog: document.getElementById("explorer-copedent-dialog"),
    copedentOpen: document.getElementById("explorer-copedent-open"),
    copedentClose: document.getElementById("explorer-copedent-close"),
    glossaryDialog: document.getElementById("explorer-glossary-dialog"),
    glossaryOpen: document.getElementById("explorer-glossary-open"),
    glossaryClose: document.getElementById("explorer-glossary-close"),
    copedentChart: document.getElementById("explorer-copedent-chart"),
    controlPreview: document.getElementById("explorer-control-impact-preview"),
    activeResults: document.getElementById("explorer-active-results"),
    fretboard: document.getElementById("explorer-fretboard"),
    rowList: document.getElementById("explorer-row-list"),
    selectedDetail: document.getElementById("explorer-selected-detail"),
    empty: document.getElementById("explorer-empty"),
    tooltip: document.getElementById("explorer-tooltip"),
  };

  let selectedRowId = "";
  let selectedImpactControlIds = new Set();
  let labelMode = "intervals";
  let lastCopedentDialogOpener = null;
  let lastGlossaryDialogOpener = null;
  let currentRows = [];
  let currentMarkerGroups = [];

  function availableKeys() {
    const sourcePayloads = Object.keys(payloadsByKey).length ? payloadsByKey : payloadsForSelectedCopedent();
    const keys = Object.keys(sourcePayloads);
    if (keys.length) {
      const visible = KEY_OPTIONS.filter((option) => keys.includes(option.value));
      const visibleValues = new Set(visible.map((option) => option.value));
      return visible.concat(keys
        .filter((key) => !visibleValues.has(key) && !["C#", "D#", "F#", "G#", "A#"].includes(key))
        .sort()
        .map((key) => ({ value: key, label: key })));
    }
    return fallbackPayload?.query?.key ? [{ value: fallbackPayload.query.key, label: fallbackPayload.query.key }] : [];
  }

  function selectedCopedentId() {
    return els.copedent?.value || fallbackPayload?.selected_copedent?.id || DEFAULT_COPEDENT_ID;
  }

  function payloadsForSelectedCopedent() {
    return payloadsByCopedent[selectedCopedentId()] || payloadsByKey;
  }

  function activePayload() {
    const payloads = payloadsForSelectedCopedent();
    return payloads[els.key.value] || payloadsByKey[els.key.value] || fallbackPayload || null;
  }

  function activeKey() {
    return activePayload()?.query?.key || els.key.value || "G";
  }

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

  function dedupeValues(values) {
    const seen = new Set();
    return toArray(values)
      .map((value) => String(value).trim())
      .filter((value) => {
        if (!value || seen.has(value)) {
          return false;
        }
        seen.add(value);
        return true;
      });
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
    return dedupeValues(toArray(row.pedals).concat(toArray(row.levers)));
  }

  function displayNoteEntries(row) {
    const notes = row?.display_notes;
    if (!notes || typeof notes !== "object" || Array.isArray(notes)) {
      return [];
    }
    return Object.entries(notes)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([string, value]) => ({
        string,
        note: typeof value === "object" && value !== null ? value.note : value,
        interval: typeof value === "object" && value !== null ? value.interval : "",
      }));
  }

  function rowNoteLabels(row) {
    const notes = displayNoteEntries(row).map((entry) => entry.note).filter(Boolean);
    if (notes.length) {
      return dedupeValues(notes);
    }
    if (row?.display_notes && typeof row.display_notes === "object" && !Array.isArray(row.display_notes)) {
      return dedupeValues(Object.values(row.display_notes));
    }
    return dedupeValues(toArray(row.notes));
  }

  function rowIntervalLabels(row) {
    const intervals = displayNoteEntries(row).map((entry) => entry.interval).filter(Boolean);
    if (intervals.length) {
      return dedupeValues(intervals);
    }
    if (row?.intervals && typeof row.intervals === "object" && !Array.isArray(row.intervals)) {
      return dedupeValues(Object.values(row.intervals));
    }
    return dedupeValues(toArray(row.intervals));
  }

  function topVoiceLabel(row) {
    const topVoice = row?.display_top_voice;
    if (topVoice && typeof topVoice === "object" && !Array.isArray(topVoice)) {
      return [topVoice.note, topVoice.interval ? `interval ${topVoice.interval}` : "", topVoice.string ? `string ${topVoice.string}` : ""]
        .filter(Boolean)
        .join(" · ");
    }
    return topVoice;
  }

  function activeLabelValues(row) {
    return labelMode === "notes" ? rowNoteLabels(row) : rowIntervalLabels(row);
  }

  function activeLabelText(row) {
    return formatValue(activeLabelValues(row));
  }

  function primaryLabelForRow(row) {
    const values = activeLabelValues(row);
    if (values.length) {
      return values[0];
    }
    return row.chord_function || row.scale_degree || row.chord_name || "Position";
  }

  function labelModeNoun() {
    return labelMode === "notes" ? "Notes" : "Intervals";
  }

  function rowsForScale(scale) {
    const payload = activePayload();
    const key = activeKey();
    return payload?.positions?.filter((row) => row.key === key && row.scale_type === scale) || [];
  }

  function rowMatchesHarmony(row, harmony) {
    if (harmony === "two_string_harmonized") {
      return row.harmony_type === "two_string_harmonized" || row.harmony_type === "five_eight_branch";
    }
    if (harmony === "three_string_diatonic") {
      return row.harmony_type === "three_string_diatonic" || row.harmony_type === "advanced_pocket";
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

  function availableStringGroups(rows, harmony) {
    if (harmony === "two_string_harmonized") {
      return uniqueGroups(rows, TWO_STRING_DISPLAY_GROUPS);
    }
    return uniqueGroups(rows, new Set([...CORE_GROUPS, ...ADVANCED_GROUPS]));
  }

  function option(value, label, selectedValues) {
    const values = Array.isArray(selectedValues) ? selectedValues : [selectedValues];
    return `<option value="${escapeHtml(value)}"${values.includes(value) ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }

  function copedentOption(copedent, selectedValue) {
    const disabled = copedent.status === "disabled";
    const disabledReason = formatValue(copedent.disabled_reason, "");
    const label = disabled && disabledReason
      ? `${copedent.label} - ${disabledReason}`
      : copedent.label;
    return `<option value="${escapeHtml(copedent.id)}"${copedent.id === selectedValue ? " selected" : ""}${disabled ? " disabled" : ""}>${escapeHtml(label)}</option>`;
  }

  function selectedOptionLabel(selectEl) {
    const optionEl = selectEl.options?.[selectEl.selectedIndex];
    return optionEl?.text || selectEl.value || "";
  }

  function optionGroup(label, groups, selectedValues) {
    if (!groups.length) {
      return "";
    }
    return `<optgroup label="${escapeHtml(label)}">${groups.map((group) => option(group, group, selectedValues)).join("")}</optgroup>`;
  }

  function selectedStringGroups() {
    const options = Array.from(els.stringGroup.options || []);
    const selected = options
      .filter((item) => item.selected && item.value !== "all")
      .map((item) => item.value);
    return selected.length ? selected : [];
  }

  function selectedGroupLabel() {
    const groups = selectedStringGroups();
    if (groups.length) {
      return groups.join(", ");
    }
    return els.harmony.value === "two_string_harmonized" ? "all 2-string groups" : "all 3-string groups";
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

  function updateKeyOptions() {
    const keyOptions = availableKeys();
    const currentValue = els.key.value || "G";
    if (!keyOptions.length) {
      return;
    }
    els.key.innerHTML = keyOptions.map((keyOption) => option(keyOption.value, keyOption.label, currentValue)).join("");
    if (!keyOptions.some((keyOption) => keyOption.value === currentValue)) {
      els.key.value = keyOptions.some((keyOption) => keyOption.value === "G") ? "G" : keyOptions[0].value;
    }
  }

  function availableCopedents() {
    const payload = activePayload() || fallbackPayload;
    const options = payload?.selected_copedent?.available_options || payload?.filters?.available_copedents;
    return Array.isArray(options) ? options : [];
  }

  function updateCopedentOptions() {
    if (!els.copedent) {
      return;
    }
    const options = availableCopedents();
    if (!options.length) {
      return;
    }
    const currentValue = els.copedent.value || DEFAULT_COPEDENT_ID;
    const enabledValues = new Set(options.filter((item) => item.status !== "disabled").map((item) => item.id));
    const selectedValue = enabledValues.has(currentValue) ? currentValue : DEFAULT_COPEDENT_ID;
    els.copedent.innerHTML = options.map((item) => copedentOption(item, selectedValue)).join("");
    els.copedent.value = selectedValue;
  }

  function updateScaleLabels() {
    const key = selectedOptionLabel(els.key) || activeKey();
    Array.from(els.scale.options).forEach((item) => {
      if (item.value === "major") {
        item.text = `${key} major`;
      }
      if (item.value === "natural_minor") {
        item.text = `${key} natural minor`;
      }
    });
  }

  function updateStringGroupOptions() {
    const scale = els.scale.value;
    const harmony = els.harmony.value;
    const rows = rowsForScaleAndHarmony(scale, harmony);
    const validGroups = availableStringGroups(rows, harmony);
    const currentValues = selectedStringGroups().filter((group) => validGroups.includes(group));
    const allLabel = harmony === "two_string_harmonized"
      ? "All 2-string groups"
      : "All 3-string groups";
    const selectedValues = currentValues.length ? currentValues : ["all"];
    let html = option("all", allLabel, selectedValues);

    if (harmony === "two_string_harmonized") {
      html += optionGroup("2-string groups", validGroups, selectedValues);
    } else {
      html += optionGroup("Core grips", uniqueGroups(rows, CORE_GROUPS), selectedValues);
      html += optionGroup("Advanced swaps", uniqueGroups(rows, ADVANCED_GROUPS), selectedValues);
    }

    els.stringGroup.innerHTML = html;
    const validSelected = selectedStringGroups();
    if (!validSelected.length) {
      const allOption = Array.from(els.stringGroup.options || []).find((item) => item.value === "all");
      if (allOption) {
        allOption.selected = true;
        els.stringGroup.value = "all";
      }
    }
  }

  function updateControls() {
    updateScaleLabels();
    updateHarmonyOptions();
    updateStringGroupOptions();
  }

  function getRows() {
    const payload = activePayload();
    if (!payload || !Array.isArray(payload.positions)) {
      return [];
    }

    const key = activeKey();
    const scale = els.scale.value;
    const harmony = els.harmony.value;
    const stringGroups = selectedStringGroups();

    return payload.positions
      .filter((row) => row.key === key)
      .filter((row) => row.scale_type === scale)
      .filter((row) => rowMatchesHarmony(row, harmony))
      .filter((row) => {
        if (!stringGroups.length) {
          return true;
        }
        return stringGroups.includes(row.string_group);
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
    const payload = activePayload();
    const notes = payload?.query?.display_scale_notes?.[els.scale.value];
    return Array.isArray(notes) ? notes.join(" ") : "Unavailable";
  }

  function isAdvanced(row) {
    return ADVANCED_GROUPS.has(row.string_group) || row.harmony_type === "advanced_pocket";
  }

  function groupLabel(row) {
    if (row.harmony_type === "five_eight_branch" || row.string_group === "5-8") {
      return "5&8 branch";
    }
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
    if (row.harmony_type === "five_eight_branch") {
      return "alternate";
    }
    if (row.harmony_type === "two_string_harmonized") {
      return "alternate";
    }
    return "primary";
  }

  function labelForRow(row) {
    const values = activeLabelValues(row);
    if (values.length) {
      return values.join(" ");
    }
    return row.chord_name || row.chord_function || "Position";
  }

  function asFretboardPosition(row) {
    return {
      ...row,
      id: row.id,
      label: labelForRow(row),
      fret: row.fret,
      strings: row.strings,
      grip: row.string_group,
      pedals: dedupeValues(row.pedals),
      levers: dedupeValues(row.levers),
      notes: rowNoteLabels(row),
      intervals: rowIntervalLabels(row),
      explanation: row.display_summary || row.explanation,
      colorRole: colorRoleForRow(row),
      visibleByDefault: true,
    };
  }

  function markerGroupKey(row) {
    return [
      "marker",
      row.fret,
      row.string_group,
      (row.strings || []).join("-"),
    ].join(":");
  }

  function groupRowsForMarkers(rows) {
    const groups = new Map();
    rows.forEach((row) => {
      const key = markerGroupKey(row);
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key).push(row);
    });
    return Array.from(groups.entries()).map(([id, groupRows], index) => ({ id, rows: groupRows, index: index + 1 }));
  }

  function markerLabelForGroup(group) {
    return `${group.index}${group.rows.length > 1 ? "+" : ""}`;
  }

  function markerLabelForRow(row) {
    const group = currentMarkerGroups.find((item) => item.id === markerGroupKey(row));
    return group ? markerLabelForGroup(group) : "";
  }

  function asMarkerPosition(group) {
    const row = group.rows[0];
    return {
      ...asFretboardPosition(row),
      id: group.id,
      label: markerLabelForGroup(group),
      explanation: group.rows.length > 1
        ? `${group.rows.length} validated setups share this fret and string group.`
        : row.display_summary || row.explanation,
    };
  }

  function shortLabel(row) {
    const chord = primaryLabelForRow(row);
    const controls = normalizePedals(row);
    return `${chord}${controls.length ? ` · ${controls.join("+")}` : ""}`;
  }

  function detailRow(label, value) {
    const rendered = formatValue(value);
    if (rendered === "none") {
      return "";
    }
    return `<div class="explorer-detail-row"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(rendered)}</dd></div>`;
  }

  function teachingNoteHtml(row) {
    const rendered = formatValue(row.explanation_summary, "");
    if (!rendered) {
      return "";
    }
    return `
      <section class="explorer-teaching-note" aria-label="Why this position works">
        <strong>Why this position works</strong>
        <p>${escapeHtml(rendered)}</p>
      </section>
    `;
  }

  function semitoneLabel(value) {
    const number = Number(value);
    if (!Number.isFinite(number) || number === 0) {
      return "";
    }
    return `${number > 0 ? "+" : ""}${number}`;
  }

  function directionLabel(value) {
    if (value === "raise") {
      return "raise";
    }
    if (value === "lower") {
      return "lower";
    }
    return "";
  }

  function copedentCellHtml(cell) {
    if (!cell) {
      return '<td class="explorer-copedent-chart__empty" aria-label="No change"></td>';
    }
    const direction = directionLabel(cell.direction);
    const delta = semitoneLabel(cell.semitones);
    const detail = [direction, delta].filter(Boolean).join(" ");
    return `
      <td class="explorer-copedent-chart__cell explorer-copedent-chart__cell--${escapeHtml(cell.direction || "change")}" data-copedent-direction="${escapeHtml(cell.direction || "change")}">
        <strong>${escapeHtml(formatValue(cell.label || `${cell.from} -> ${cell.to}`))}</strong>
        ${detail ? `<span>${escapeHtml(detail)}</span>` : ""}
      </td>
    `;
  }

  function renderCopedentChart() {
    if (!els.copedentChart) {
      return;
    }
    const selected = activePayload()?.selected_copedent;
    const rows = toArray(selected?.chart?.rows);
    const columns = toArray(selected?.chart?.columns);
    if (!selected || !rows.length || !columns.length) {
      els.copedentChart.hidden = true;
      els.copedentChart.innerHTML = "";
      return;
    }
    els.copedentChart.hidden = false;
    els.copedentChart.innerHTML = `
      <div class="explorer-copedent-chart__header">
        <div>
          <strong>${escapeHtml(formatValue(selected.label || "E9 setup"))}</strong>
          <p>Choose the E9 setup that matches your guitar. Emmons and Day mainly differ in pedal arrangement.</p>
          <p>Copedents vary; this chart shows the setup currently used for guidance.</p>
        </div>
        <span>${escapeHtml(formatValue(selected.status || "selected"))}</span>
      </div>
      <div class="explorer-copedent-chart__table-wrap">
        <table class="explorer-copedent-chart__table" aria-label="${escapeHtml(formatValue(selected.label || "E9"))} copedent chart">
          <thead>
            <tr>
              <th scope="col">String</th>
              <th scope="col">Open</th>
              ${columns.map((column) => `
                <th scope="col">
                  <span>${escapeHtml(formatValue(column.label || column.id))}</span>
                  <small>${escapeHtml(formatValue(column.physical_position || column.control_type, ""))}</small>
                </th>
              `).join("")}
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <th scope="row">${escapeHtml(formatValue(row.string))}</th>
                <td class="explorer-copedent-chart__open">${escapeHtml(formatValue(row.open_note))}</td>
                ${columns.map((column) => copedentCellHtml(row.cells?.[column.id])).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function noteChangeLabel(impact) {
    const before = formatValue(impact.display_before_note || impact.before_note, "");
    const after = formatValue(impact.display_after_note || impact.after_note, "");
    if (!before || !after) {
      return "";
    }
    return `${before} -> ${after}`;
  }

  function impactLineHtml(impact, includeChordIntervals = false) {
    const change = noteChangeLabel(impact);
    if (!change) {
      return "";
    }
    const stringNumber = formatValue(impact.string, "");
    const intervalEffect = formatValue(impact.interval_effect, "");
    const beforeInterval = formatValue(impact.before_interval, "");
    const afterInterval = formatValue(impact.after_interval, "");
    const intervalContext = includeChordIntervals && beforeInterval && afterInterval
      ? `; chord role ${beforeInterval} -> ${afterInterval}`
      : "";
    return `
      <li>
        <span>String ${escapeHtml(stringNumber)}</span>
        <strong>${escapeHtml(change)}</strong>
        ${intervalEffect ? `<em>${escapeHtml(intervalEffect + intervalContext)}</em>` : ""}
      </li>
    `;
  }

  function rowStringsForActiveContext() {
    const selectedGroups = selectedStringGroups();
    const sourceRows = currentRows.length ? currentRows : getRows();
    const rows = selectedGroups.length
      ? sourceRows.filter((row) => selectedGroups.includes(row.string_group))
      : sourceRows;
    const strings = new Set();
    rows.forEach((row) => toArray(row.strings).forEach((stringNumber) => strings.add(Number(stringNumber))));
    return Array.from(strings).filter(Number.isFinite).sort((a, b) => a - b);
  }

  function impactStringsForContext(control) {
    const activeStrings = rowStringsForActiveContext();
    const impacts = toArray(control.string_impacts);
    if (!activeStrings.length) {
      return impacts;
    }
    const activeSet = new Set(activeStrings);
    return impacts.filter((impact) => activeSet.has(Number(impact.string)));
  }

  function selectedControlObjects(controls) {
    return controls.filter((control) => selectedImpactControlIds.has(control.id));
  }

  function impactContextSentence(controls) {
    const selectedGroups = selectedStringGroups();
    const groupText = selectedGroups.length ? selectedGroups.join(", ") : selectedGroupLabel();
    const harmonyText = HARMONY_LABELS[els.harmony.value] || selectedOptionLabel(els.harmony);
    const modeText = labelMode === "notes" ? "note names" : "interval/NNS labels";
    if (!controls.length) {
      return `Choose one or more controls to preview changes for ${groupText} in ${harmonyText}. Showing ${modeText}.`;
    }
    return `Previewing ${controls.map((control) => control.label || control.id).join(" + ")} for ${groupText} in ${harmonyText}. Showing ${modeText}.`;
  }

  function combinedImpactCaution(controls) {
    const ids = new Set(controls.map((control) => control.id));
    const rows = currentRows.length ? currentRows : getRows();
    const selectedControlNames = Array.from(ids);
    const matchingRows = rows.filter((row) => {
      const rowControls = new Set(normalizePedals(row));
      return selectedControlNames.every((control) => rowControls.has(control));
    });
    const messages = [];
    if (ids.has("B") && !ids.has("A") && rows.some((row) => normalizePedals(row).includes("A") && normalizePedals(row).includes("B"))) {
      messages.push("B by itself may not match rows in this view that expect A+B together.");
    }
    if (controls.length && !matchingRows.length) {
      messages.push("No visible row uses exactly this selected control set; treat this as a mechanical preview, not a validated position.");
    }
    return messages;
  }

  function controlImpactDetailHtml(control) {
    const impacts = impactStringsForContext(control);
    const allImpacts = toArray(control.string_impacts);
    const affectedStrings = formatValue(control.affected_strings);
    if (!impacts.length) {
      return `
        <article class="explorer-control-impact-detail" data-control-impact-detail="${escapeHtml(control.id || control.label || "")}">
          <strong>${escapeHtml(formatValue(control.label || control.id || "Control"))}</strong>
          <p>No direct impact on the selected string group. This control affects strings ${escapeHtml(affectedStrings)}, but those strings are not active in the current view.</p>
        </article>
      `;
    }
    return `
      <article class="explorer-control-impact-detail" data-control-impact-detail="${escapeHtml(control.id || control.label || "")}">
        <strong>${escapeHtml(formatValue(control.label || control.id || "Control"))}</strong>
        <p>Affects strings ${escapeHtml(affectedStrings)}${impacts.length === allImpacts.length ? "." : "; direct changes in this view are shown below."}</p>
        <ul class="explorer-control-impact-list">
          ${impacts.map((impact) => impactLineHtml(impact)).join("")}
        </ul>
      </article>
    `;
  }

  function renderControlImpactPreview() {
    if (!els.controlPreview) {
      return;
    }
    const preview = activePayload()?.control_impact_preview;
    const controls = toArray(preview?.controls);
    if (!controls.length) {
      els.controlPreview.hidden = true;
      els.controlPreview.innerHTML = "";
      selectedImpactControlIds = new Set();
      return;
    }
    const key = preview?.key_context?.key || activeKey();
    const availableIds = new Set(controls.map((control) => control.id));
    selectedImpactControlIds = new Set(Array.from(selectedImpactControlIds).filter((id) => availableIds.has(id)));
    const selectedControls = selectedControlObjects(controls);
    const cautions = combinedImpactCaution(selectedControls);
    els.controlPreview.hidden = false;
    els.controlPreview.innerHTML = `
      <div class="explorer-control-impact-preview__header">
        <div>
          <strong>Pedal and lever impact</strong>
          <p>Select one or more controls to see what changes in ${escapeHtml(key)} for the current view.</p>
        </div>
        <span>${escapeHtml(formatValue(preview?.copedent_profile?.label || "Standard E9"))}</span>
      </div>
      <div class="explorer-control-impact-preview__body">
        <div class="explorer-control-impact-tabs" role="group" aria-label="Pedal and lever controls">
          ${controls.map((control) => `
            <button
              class="explorer-control-impact-tab${selectedImpactControlIds.has(control.id) ? " is-selected" : ""}"
              type="button"
              aria-pressed="${selectedImpactControlIds.has(control.id) ? "true" : "false"}"
              data-control-impact-tab="${escapeHtml(control.id || "")}"
            >${escapeHtml(formatValue(control.label || control.id || "Control"))}</button>
          `).join("")}
          <button class="explorer-control-impact-tab explorer-control-impact-clear" type="button" data-control-impact-clear>Clear</button>
        </div>
        <p class="explorer-control-impact-context">${escapeHtml(impactContextSentence(selectedControls))}</p>
        ${selectedControls.map((control) => controlImpactDetailHtml(control)).join("")}
        ${cautions.length ? `<p class="explorer-control-impact-context">${escapeHtml(cautions.join(" "))}</p>` : ""}
      </div>
    `;
    Array.from(els.controlPreview.querySelectorAll("[data-control-impact-tab]")).forEach((button) => {
      const selectControl = () => {
        const controlId = button.getAttribute("data-control-impact-tab") || "";
        const next = new Set(selectedImpactControlIds);
        if (next.has(controlId)) {
          next.delete(controlId);
        } else {
          next.add(controlId);
        }
        selectedImpactControlIds = next;
        renderControlImpactPreview();
      };
      button.addEventListener("click", selectControl);
    });
    const clearButton = typeof els.controlPreview.querySelector === "function"
      ? els.controlPreview.querySelector("[data-control-impact-clear]")
      : null;
    if (clearButton) {
      clearButton.addEventListener("click", () => {
        selectedImpactControlIds = new Set();
        renderControlImpactPreview();
      });
    }
  }

  function rowControlImpactsHtml(row) {
    const impacts = toArray(row.control_impacts);
    if (!impacts.length) {
      return "";
    }
    return `
      <section class="explorer-row-control-impacts" aria-label="Pedal and lever changes used here">
        <strong>Changes used here</strong>
        <div class="explorer-row-control-impacts__grid">
          ${impacts.map((impact) => `
            <article>
              <span>${escapeHtml(formatValue(impact.label || impact.id || "Control"))}</span>
              <ul class="explorer-control-impact-list explorer-control-impact-list--compact">
                ${toArray(impact.string_impacts).map((stringImpact) => impactLineHtml(stringImpact, true)).join("")}
              </ul>
            </article>
          `).join("")}
        </div>
      </section>
    `;
  }

  function renderSelectedDetail(row) {
    if (!row) {
      els.selectedDetail.className = "explorer-selected-detail";
      els.selectedDetail.innerHTML = '<p class="explorer-empty">Choose a marker or row to inspect one validated position.</p>';
      return;
    }

    const warnings = toArray(row.warnings);
    const detailClass = isAdvanced(row) ? "explorer-selected-detail explorer-selected-detail--advanced" : "explorer-selected-detail";
    els.selectedDetail.className = detailClass;
    els.selectedDetail.innerHTML = `
      <div class="explorer-selected-detail__header">
        <span class="explorer-selected-detail__kind">${escapeHtml(groupLabel(row))}</span>
        <strong>${escapeHtml(formatValue(row.display_summary || row.chord_name || row.id))}</strong>
      </div>
      ${teachingNoteHtml(row)}
      <dl class="explorer-detail-grid">
        ${detailRow("Notes", rowNoteLabels(row))}
        ${detailRow("Intervals", rowIntervalLabels(row))}
        ${detailRow("Top voice", topVoiceLabel(row))}
        ${detailRow("Fret", row.fret)}
        ${detailRow("String group", row.string_group)}
        ${detailRow("Pedals / levers", normalizePedals(row))}
        ${detailRow("Per-string changes", row.per_string_changes)}
        ${detailRow("Warnings", warnings)}
      </dl>
      ${rowControlImpactsHtml(row)}
    `;
  }

  function selectRow(rowId) {
    if (!currentRows.some((row) => row.id === rowId)) {
      selectedRowId = currentRows[0]?.id || "";
    } else {
      selectedRowId = rowId;
    }
    const selected = currentRows.find((row) => row.id === selectedRowId);
    renderSelectedDetail(selected);
    syncSelectedState();
  }

  function syncSelectedState() {
    Array.from(els.rowList.querySelectorAll("[data-explorer-row]")).forEach((button) => {
      const isSelected = button.getAttribute("data-explorer-row") === selectedRowId;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
    if (els.activeResults) {
      Array.from(els.activeResults.querySelectorAll("[data-active-result-row]")).forEach((button) => {
        const isSelected = button.getAttribute("data-active-result-row") === selectedRowId;
        button.classList.toggle("is-selected", isSelected);
        button.setAttribute("aria-pressed", isSelected ? "true" : "false");
      });
    }
    const selectedMarkerId = markerGroupKey(currentRows.find((row) => row.id === selectedRowId) || {});
    Array.from(els.fretboard.querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]")).forEach((marker) => {
      const isSelected = marker.getAttribute("data-highlight-id") === selectedMarkerId;
      marker.classList.toggle("is-explorer-selected-marker", isSelected);
      marker.setAttribute("data-explorer-selected-marker", isSelected ? "true" : "false");
    });
  }

  function resultButtonHtml(row, dataAttributeName) {
    const buttonClass = isAdvanced(row) ? " explorer-active-result--advanced" : "";
    const isSelected = row.id === selectedRowId;
    const markerLabel = markerLabelForRow(row);
    return `
      <button class="explorer-active-result${buttonClass}${isSelected ? " is-selected" : ""}" type="button" ${dataAttributeName}="${escapeHtml(row.id)}" data-marker-id="${escapeHtml(markerGroupKey(row))}" data-string-group="${escapeHtml(row.string_group)}" data-harmony-type="${escapeHtml(row.harmony_type)}" aria-pressed="${isSelected ? "true" : "false"}">
        ${markerLabel ? `<span class="explorer-active-result__marker">Marker ${escapeHtml(markerLabel)}</span>` : ""}
        <strong>${escapeHtml(shortLabel(row))}</strong>
        <span class="explorer-active-result__meta">Fret ${escapeHtml(formatValue(row.fret))} · ${escapeHtml(row.string_group)} · ${escapeHtml(labelModeNoun())}: ${escapeHtml(activeLabelText(row))}</span>
      </button>
    `;
  }

  function renderActiveResults(rows) {
    if (!els.activeResults) {
      return;
    }
    const label = selectedGroupLabel();
    if (!rows.length) {
      els.activeResults.innerHTML = `
        <div class="explorer-active-results__header">
          <strong>No visible positions for ${escapeHtml(label)}</strong>
          <span>Try all groups or a different view.</span>
        </div>
      `;
      return;
    }
    els.activeResults.innerHTML = `
      <div class="explorer-active-results__header">
        <strong>${escapeHtml(label)}: ${rows.length} visible ${rows.length === 1 ? "position" : "positions"}</strong>
        <span>Cards match the SVG markers below.</span>
      </div>
      <div class="explorer-active-results__track">
        ${rows.map((row) => resultButtonHtml(row, "data-active-result-row")).join("")}
      </div>
    `;
    Array.from(els.activeResults.querySelectorAll("[data-active-result-row]")).forEach((button) => {
      const rowId = button.getAttribute("data-active-result-row");
      button.addEventListener("click", () => selectRow(rowId));
      button.addEventListener("mouseenter", () => showMarkerForRow(rowId));
      button.addEventListener("focus", () => showMarkerForRow(rowId));
      button.addEventListener("mouseleave", clearMarkerHover);
      button.addEventListener("blur", clearMarkerHover);
    });
  }

  function renderCards(rows) {
    els.rowList.innerHTML = rows
      .map((row) => {
        const buttonClass = isAdvanced(row) ? " explorer-row-button--advanced" : "";
        const isSelected = row.id === selectedRowId;
        return `
          <button class="explorer-row-button${buttonClass}${isSelected ? " is-selected" : ""}" type="button" data-explorer-row="${escapeHtml(row.id)}" data-string-group="${escapeHtml(row.string_group)}" data-harmony-type="${escapeHtml(row.harmony_type)}" aria-pressed="${isSelected ? "true" : "false"}">
            <strong>${escapeHtml(shortLabel(row))}</strong>
            <span class="explorer-row-button__meta">Fret ${escapeHtml(formatValue(row.fret))} · ${escapeHtml(row.string_group)} · ${escapeHtml(groupLabel(row))} · ${escapeHtml(labelModeNoun())}: ${escapeHtml(activeLabelText(row))}</span>
          </button>
        `;
      })
      .join("");
    Array.from(els.rowList.querySelectorAll("[data-explorer-row]")).forEach((button) => {
      button.addEventListener("click", () => selectRow(button.getAttribute("data-explorer-row")));
    });
  }

  function tooltipText(row) {
    const warnings = toArray(row.warnings);
    const controls = normalizePedals(row);
    return [
      row.display_summary || row.chord_name || row.chord_function || row.id,
      `Fret ${row.fret} · strings ${row.string_group}`,
      `Notes: ${formatValue(rowNoteLabels(row))}`,
      `Intervals: ${formatValue(rowIntervalLabels(row))}`,
      `Pedals/levers: ${formatValue(controls)}`,
      warnings.length ? `Warning: ${formatValue(warnings)}` : "",
    ].filter(Boolean);
  }

  function tooltipHtml(row) {
    const lines = tooltipText(row);
    return `<strong>${escapeHtml(lines[0] || "Explorer position")}</strong>${lines.slice(1).map((line) => `<span>${escapeHtml(line)}</span>`).join("")}`;
  }

  function tooltipHtmlForRows(rows) {
    if (rows.length <= 1) {
      return tooltipHtml(rows[0]);
    }
    return `
      <strong>${escapeHtml(`${rows.length} positions at fret ${formatValue(rows[0]?.fret)} on ${formatValue(rows[0]?.string_group)}`)}</strong>
      ${rows.map((row) => {
        const lines = tooltipText(row);
        return `
          <span class="explorer-tooltip__item">
            <strong>${escapeHtml(lines[0] || "Explorer position")}</strong>
            ${lines.slice(1).map((line) => `<span>${escapeHtml(line)}</span>`).join("")}
          </span>
        `;
      }).join("")}
    `;
  }

  function tooltipTextForRows(rows) {
    if (rows.length <= 1) {
      return tooltipText(rows[0]).join(". ");
    }
    return [
      `${rows.length} positions at fret ${rows[0]?.fret} on ${rows[0]?.string_group}`,
      ...rows.map((row) => tooltipText(row).join(". ")),
    ].join(". ");
  }

  function showTooltipForRows(rows, target) {
    if (!rows.length || !els.tooltip) {
      return;
    }
    els.tooltip.innerHTML = tooltipHtmlForRows(rows);
    els.tooltip.hidden = false;
    const rect = target.getBoundingClientRect();
    const left = Math.min(window.innerWidth - 332, Math.max(12, rect.left + rect.width / 2 + 12));
    const top = Math.min(window.innerHeight - 150, Math.max(12, rect.top + 10));
    els.tooltip.style.left = `${left}px`;
    els.tooltip.style.top = `${top}px`;
  }

  function hideTooltip() {
    if (els.tooltip) {
      els.tooltip.hidden = true;
    }
  }

  function wireFretboardMarkers(rows, markerGroups) {
    const byMarkerId = new Map(markerGroups.map((group) => [group.id, group.rows]));
    Array.from(els.fretboard.querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]")).forEach((marker) => {
      const markerRows = byMarkerId.get(marker.getAttribute("data-highlight-id")) || [];
      if (!markerRows.length) {
        return;
      }
      marker.setAttribute("data-explorer-marker-label", markerLabelForGroup(markerGroups.find((group) => group.id === marker.getAttribute("data-highlight-id")) || { index: "", rows: markerRows }));
      const text = tooltipTextForRows(markerRows);
      marker.setAttribute("tabindex", "0");
      marker.setAttribute("role", "button");
      marker.setAttribute("aria-label", text);
      marker.setAttribute("title", text);
      marker.addEventListener("mouseenter", () => showTooltipForRows(markerRows, marker));
      marker.addEventListener("focus", () => showTooltipForRows(markerRows, marker));
      marker.addEventListener("mouseleave", hideTooltip);
      marker.addEventListener("blur", hideTooltip);
      marker.addEventListener("click", () => {
        selectRow(markerRows[0].id);
        showTooltipForRows(markerRows, marker);
      });
      marker.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectRow(markerRows[0].id);
          showTooltipForRows(markerRows, marker);
        }
      });
    });
    syncSelectedState();
  }

  function showMarkerForRow(rowId) {
    const row = currentRows.find((item) => item.id === rowId);
    if (!row) {
      return;
    }
    const markerId = markerGroupKey(row);
    const group = currentMarkerGroups.find((item) => item.id === markerId);
    const marker = els.fretboard.querySelector(`.pedal-steel-fretboard__highlight[data-highlight-id="${markerId}"]`);
    if (!group || !marker) {
      return;
    }
    Array.from(els.fretboard.querySelectorAll(".pedal-steel-fretboard__highlight.is-explorer-hover-marker")).forEach((item) => {
      item.classList.remove("is-explorer-hover-marker");
    });
    marker.classList.add("is-explorer-hover-marker");
    showTooltipForRows(group.rows, marker);
  }

  function clearMarkerHover() {
    Array.from(els.fretboard.querySelectorAll(".pedal-steel-fretboard__highlight.is-explorer-hover-marker")).forEach((item) => {
      item.classList.remove("is-explorer-hover-marker");
    });
    hideTooltip();
  }

  function renderFretboard(rows) {
    if (!fretboardApi || typeof fretboardApi.mountPedalSteelFretboard !== "function") {
      els.fretboard.innerHTML = '<p class="explorer-empty">Fretboard renderer unavailable.</p>';
      return;
    }
    const markerGroups = groupRowsForMarkers(rows);
    const selectedMarkerId = markerGroupKey(rows.find((row) => row.id === selectedRowId) || {});
    const sortedMarkerGroups = [
      ...markerGroups.filter((group) => group.id === selectedMarkerId),
      ...markerGroups.filter((group) => group.id !== selectedMarkerId),
    ];
    currentMarkerGroups = markerGroups;
    fretboardApi.mountPedalSteelFretboard(els.fretboard, {
      title: "Validated Explorer positions",
      description: "Validated E9 positions for the selected filters.",
      positions: sortedMarkerGroups.map(asMarkerPosition),
      highlights: [],
      legend: activePayload()?.legend || [],
      query: activePayload()?.query || {},
      hideFilterControls: true,
      hidePositionTools: true,
      hideLegend: true,
      showHighlightLabels: true,
      emphasizeVisibleHighlights: true,
      highlightStyle: "prominent",
    });
    wireFretboardMarkers(rows, markerGroups);
  }

  function render() {
    const rows = getRows();
    currentRows = rows;
    if (!rows.some((row) => row.id === selectedRowId)) {
      selectedRowId = rows[0]?.id || "";
    }
    els.scaleNotes.textContent = getScaleNotes();
    els.resultCount.textContent = "Showing validated positions";
    els.empty.hidden = rows.length > 0;
    els.empty.textContent = rows.length
      ? ""
      : `No validated ${HARMONY_LABELS[els.harmony.value] || "Explorer"} rows are available for ${els.scale.options[els.scale.selectedIndex]?.text || "this scale"} yet.`;
    renderCopedentChart();
    renderControlImpactPreview();
    currentMarkerGroups = groupRowsForMarkers(rows);
    renderActiveResults(rows);
    renderCards(rows);
    renderFretboard(rows);
    renderSelectedDetail(rows.find((row) => row.id === selectedRowId));
    syncSelectedState();

    const renderedText = [
      els.rowList.textContent,
      els.selectedDetail.textContent,
      els.copedentChart?.textContent || "",
      els.controlPreview?.textContent || "",
      els.fretboard.textContent,
      els.tooltip.textContent,
    ].join(" ");
    if (renderedText.includes("[object Object]")) {
      console.warn("Explorer rendered an unsafe object string.");
    }
  }

  function updateLabelModeButtons() {
    Array.from(els.labelModeButtons || []).forEach((button) => {
      const isSelected = button.getAttribute("data-explorer-label-mode") === labelMode;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
  }

  function openCopedentDialog() {
    if (!els.copedentDialog) {
      return;
    }
    lastCopedentDialogOpener = document.activeElement;
    if (typeof els.copedentDialog.showModal === "function") {
      els.copedentDialog.showModal();
    } else {
      els.copedentDialog.setAttribute("open", "");
    }
    els.copedentClose?.focus();
  }

  function closeCopedentDialog() {
    if (!els.copedentDialog?.open) {
      return;
    }
    if (typeof els.copedentDialog.close === "function") {
      els.copedentDialog.close();
    } else {
      els.copedentDialog.removeAttribute("open");
    }
  }

  function openGlossaryDialog() {
    if (!els.glossaryDialog) {
      return;
    }
    lastGlossaryDialogOpener = document.activeElement;
    if (typeof els.glossaryDialog.showModal === "function") {
      els.glossaryDialog.showModal();
    } else {
      els.glossaryDialog.setAttribute("open", "");
    }
    els.glossaryClose?.focus();
  }

  function closeGlossaryDialog() {
    if (!els.glossaryDialog?.open) {
      return;
    }
    if (typeof els.glossaryDialog.close === "function") {
      els.glossaryDialog.close();
    } else {
      els.glossaryDialog.removeAttribute("open");
    }
  }

  function init() {
    if (!activePayload()) {
      els.empty.hidden = false;
      els.empty.textContent = "Explorer data failed to load.";
      return;
    }

    updateCopedentOptions();
    updateKeyOptions();
    if (els.copedent) {
      els.copedent.addEventListener("change", () => {
        updateControls();
        render();
      });
    }
    if (els.copedentOpen) {
      els.copedentOpen.addEventListener("click", openCopedentDialog);
    }
    if (els.copedentClose) {
      els.copedentClose.addEventListener("click", closeCopedentDialog);
    }
    if (els.glossaryOpen) {
      els.glossaryOpen.addEventListener("click", openGlossaryDialog);
    }
    if (els.glossaryClose) {
      els.glossaryClose.addEventListener("click", closeGlossaryDialog);
    }
    if (els.copedentDialog) {
      els.copedentDialog.addEventListener("click", (event) => {
        if (event.target === els.copedentDialog) {
          closeCopedentDialog();
        }
      });
      els.copedentDialog.addEventListener("close", () => {
        if (lastCopedentDialogOpener && typeof lastCopedentDialogOpener.focus === "function") {
          lastCopedentDialogOpener.focus();
        }
        lastCopedentDialogOpener = null;
      });
    }
    if (els.glossaryDialog) {
      els.glossaryDialog.addEventListener("click", (event) => {
        if (event.target === els.glossaryDialog) {
          closeGlossaryDialog();
        }
      });
      els.glossaryDialog.addEventListener("close", () => {
        if (lastGlossaryDialogOpener && typeof lastGlossaryDialogOpener.focus === "function") {
          lastGlossaryDialogOpener.focus();
        }
        lastGlossaryDialogOpener = null;
      });
    }
    Array.from(els.labelModeButtons || []).forEach((button) => {
      button.addEventListener("click", () => {
        const nextMode = button.getAttribute("data-explorer-label-mode");
        labelMode = nextMode === "notes" ? "notes" : "intervals";
        updateLabelModeButtons();
        render();
      });
    });
    els.key.addEventListener("change", () => {
      updateControls();
      render();
    });
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
    updateLabelModeButtons();
    render();
  }

  init();
  window.STEEL_RAG_E9_EXPLORER = {
    availableHarmonies,
    rowsForScaleAndHarmony,
    uniqueGroups,
  };
})();
