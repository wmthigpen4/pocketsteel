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
  let currentRows = [];

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
      pedals: dedupeValues(row.pedals),
      levers: dedupeValues(row.levers),
      notes: row.display_notes || row.notes,
      intervals: row.intervals,
      explanation: row.display_summary || row.explanation,
      colorRole: colorRoleForRow(row),
      visibleByDefault: true,
    };
  }

  function shortLabel(row) {
    const degree = row.chord_function || row.scale_degree || row.chord_name || "Position";
    const controls = normalizePedals(row);
    return `${row.fret} ${degree}${controls.length ? ` · ${controls.join("+")}` : ""}`;
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

  function controlImpactCardHtml(control) {
    const impacts = toArray(control.string_impacts);
    if (!impacts.length) {
      return "";
    }
    const affectedStrings = formatValue(control.affected_strings);
    return `
      <article class="explorer-control-impact-card" data-control-impact="${escapeHtml(control.id || control.label || "")}">
        <div class="explorer-control-impact-card__header">
          <strong>${escapeHtml(formatValue(control.label || control.id || "Control"))}</strong>
          <span>${escapeHtml(formatValue(control.control_type || "control"))}</span>
        </div>
        <p>Affects strings ${escapeHtml(affectedStrings)}.</p>
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
      return;
    }
    const key = preview?.key_context?.key || activeKey();
    els.controlPreview.hidden = false;
    els.controlPreview.innerHTML = `
      <div class="explorer-control-impact-preview__header">
        <div>
          <strong>Pedal and lever impact preview</strong>
          <p>See what the standard E9 controls change in the key of ${escapeHtml(key)} before choosing a position.</p>
        </div>
        <span>${escapeHtml(formatValue(preview?.copedent_profile?.label || "Standard E9"))}</span>
      </div>
      <div class="explorer-control-impact-preview__grid">
        ${controls.map((control) => controlImpactCardHtml(control)).join("")}
      </div>
    `;
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
        ${detailRow("Display notes", row.display_notes)}
        ${detailRow("Top voice", row.display_top_voice)}
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
  }

  function resultButtonHtml(row, dataAttributeName) {
    const buttonClass = isAdvanced(row) ? " explorer-active-result--advanced" : "";
    const isSelected = row.id === selectedRowId;
    return `
      <button class="explorer-active-result${buttonClass}${isSelected ? " is-selected" : ""}" type="button" ${dataAttributeName}="${escapeHtml(row.id)}" data-string-group="${escapeHtml(row.string_group)}" data-harmony-type="${escapeHtml(row.harmony_type)}" aria-pressed="${isSelected ? "true" : "false"}">
        <strong>${escapeHtml(shortLabel(row))}</strong>
        <span class="explorer-active-result__meta">${escapeHtml(row.string_group)} · ${escapeHtml(formatValue(row.display_notes))}</span>
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
      button.addEventListener("click", () => selectRow(button.getAttribute("data-active-result-row")));
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
            <span class="explorer-row-button__meta">${escapeHtml(row.string_group)} · ${escapeHtml(groupLabel(row))} · ${escapeHtml(formatValue(row.display_notes))}</span>
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
      `Notes: ${formatValue(row.display_notes)}`,
      `Pedals/levers: ${formatValue(controls)}`,
      warnings.length ? `Warning: ${formatValue(warnings)}` : "",
    ].filter(Boolean);
  }

  function tooltipHtml(row) {
    const lines = tooltipText(row);
    return `<strong>${escapeHtml(lines[0] || "Explorer position")}</strong>${lines.slice(1).map((line) => `<span>${escapeHtml(line)}</span>`).join("")}`;
  }

  function showTooltip(row, target) {
    if (!row || !els.tooltip) {
      return;
    }
    els.tooltip.innerHTML = tooltipHtml(row);
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

  function wireFretboardMarkers(rows) {
    const byId = new Map(rows.map((row) => [row.id, row]));
    Array.from(els.fretboard.querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]")).forEach((marker) => {
      const row = byId.get(marker.getAttribute("data-highlight-id"));
      if (!row) {
        return;
      }
      const text = tooltipText(row).join(". ");
      marker.setAttribute("tabindex", "0");
      marker.setAttribute("role", "button");
      marker.setAttribute("aria-label", text);
      marker.setAttribute("title", text);
      marker.addEventListener("mouseenter", () => showTooltip(row, marker));
      marker.addEventListener("focus", () => showTooltip(row, marker));
      marker.addEventListener("mouseleave", hideTooltip);
      marker.addEventListener("blur", hideTooltip);
      marker.addEventListener("click", () => {
        selectRow(row.id);
        showTooltip(row, marker);
      });
      marker.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectRow(row.id);
          showTooltip(row, marker);
        }
      });
    });
  }

  function renderFretboard(rows) {
    if (!fretboardApi || typeof fretboardApi.mountPedalSteelFretboard !== "function") {
      els.fretboard.innerHTML = '<p class="explorer-empty">Fretboard renderer unavailable.</p>';
      return;
    }
    fretboardApi.mountPedalSteelFretboard(els.fretboard, {
      title: "Validated Explorer positions",
      description: "Validated E9 positions for the selected filters.",
      positions: rows.map(asFretboardPosition),
      highlights: [],
      legend: activePayload()?.legend || [],
      query: activePayload()?.query || {},
      hideFilterControls: true,
      hidePositionTools: true,
      hideLegend: true,
      showHighlightLabels: false,
      emphasizeVisibleHighlights: true,
      highlightStyle: "prominent",
    });
    wireFretboardMarkers(rows);
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
    renderActiveResults(rows);
    renderCards(rows);
    renderFretboard(rows);
    renderSelectedDetail(rows.find((row) => row.id === selectedRowId));

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
    render();
  }

  init();
  window.STEEL_RAG_E9_EXPLORER = {
    availableHarmonies,
    rowsForScaleAndHarmony,
    uniqueGroups,
  };
})();
