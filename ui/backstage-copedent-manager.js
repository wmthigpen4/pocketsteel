(function (global) {
  "use strict";

  const store = global.STEEL_RAG_COPEDENTS;
  const grid = global.STEEL_RAG_COPEDENT_GRID;
  const answerUi = typeof STEEL_RAG_ANSWER_UI !== "undefined" ? STEEL_RAG_ANSWER_UI : global.STEEL_RAG_ANSWER_UI;
  if (!store || !grid || !global.document) return;

  const doc = global.document;
  const $ = (selector) => doc.querySelector(selector);
  const elements = {
    library: $("#copedent-profile-library"),
    activeBadge: $("#copedent-active-badge"),
    libraryActive: $("#copedent-library-active"),
    reviewIssues: $("#copedent-review-issues"),
    name: $("#copedent-name"),
    family: $("#copedent-family"),
    stringCount: $("#copedent-string-count"),
    guitar: $("#copedent-guitar"),
    pedalOrder: $("#copedent-pedal-order"),
    notes: $("#copedent-notes"),
    template: $("#copedent-template"),
    grid: $("#copedent-grid"),
    addControl: $("#add-copedent-change"),
    save: $("#save-copedent"),
    reset: $("#reset-copedent"),
    activateEdited: $("#activate-edited-copedent"),
    compare: $("#compare-copedent"),
    addFromStarter: $("#add-copedent-from-starter"),
    activate: $("#activate-copedent"),
    clone: $("#clone-copedent"),
    create: $("#new-copedent"),
    duplicate: $("#duplicate-copedent"),
    remove: $("#delete-copedent"),
    more: $("#copedent-more"),
    status: $("#copedent-save-status"),
    overview: $("#copedent-overview-summary"),
    overviewUpdated: $("#copedent-overview-updated"),
    mobileGroup: $("#copedent-mobile-group"),
    mobilePrevious: $("#copedent-mobile-previous"),
    mobileNext: $("#copedent-mobile-next"),
    cellDialog: $("#copedent-cell-dialog"),
    cellContext: $("#copedent-cell-context"),
    deltaPicker: $("#copedent-delta-picker"),
    customDelta: $("#copedent-custom-delta"),
    cellPreview: $("#copedent-cell-preview"),
    cellApply: $("#copedent-cell-apply"),
    controlDialog: $("#copedent-control-dialog"),
    controlTitle: $("#copedent-control-title"),
    controlLabel: $("#copedent-control-label"),
    controlPosition: $("#copedent-control-position"),
    controlType: $("#copedent-control-type"),
    controlTravel: $("#copedent-control-travel"),
    controlAliases: $("#copedent-control-aliases"),
    controlPrevious: $("#copedent-control-previous"),
    controlNext: $("#copedent-control-next"),
    controlAddState: $("#copedent-control-add-state"),
    controlRemove: $("#copedent-control-remove"),
    controlApply: $("#copedent-control-apply"),
    stringDialog: $("#copedent-string-dialog"),
    stringTitle: $("#copedent-string-title"),
    stringNote: $("#copedent-string-note"),
    stringOctave: $("#copedent-string-octave"),
    stringGauge: $("#copedent-string-gauge"),
    stringNotes: $("#copedent-string-notes"),
    stringApply: $("#copedent-string-apply")
  };

  if (!elements.library || !elements.grid) return;

  const STANDARD_STRINGS = [
    [1, "F#", 66], [2, "D#", 63], [3, "G#", 68], [4, "E", 64], [5, "B", 59],
    [6, "G#", 56], [7, "F#", 54], [8, "E", 52], [9, "D", 50], [10, "B", 47]
  ];

  function fallbackProfile(id, day = false) {
    const pedalPosition = day ? { A: "P3", B: "P2", C: "P1" } : { A: "P1", B: "P2", C: "P3" };
    const control = (controlId, label, type, physical, travel, changes) => ({
      id: controlId,
      label,
      control_type: type,
      physical_position: physical,
      travel,
      player_shorthand: [],
      compatibility_aliases: [physical],
      changes: changes.map(([string, from, to]) => ({
        string,
        from,
        to,
      direction: grid.changeDirection(grid.semitoneDelta(from, to))
      }))
    });
    return {
      id,
      label: day ? "Day E9 starter" : "Emmons E9 starter",
      revision: 1,
      strings: STANDARD_STRINGS.map(([string, open_note, open_pitch_value]) => ({ string, open_note, open_pitch_value })),
      pedal_order: day ? ["C", "B", "A"] : ["A", "B", "C"],
      controls: [
        control("A", "A pedal", "pedal", pedalPosition.A, "pedal", [[5, "B", "C#"], [10, "B", "C#"]]),
        control("B", "B pedal", "pedal", pedalPosition.B, "pedal", [[3, "G#", "A"], [6, "G#", "A"]]),
        control("C", "C pedal", "pedal", pedalPosition.C, "pedal", [[4, "E", "F#"], [5, "B", "C#"]]),
        control("E-raise", "E raise (F lever)", "lever", "LKL", "full", [[4, "E", "F"], [8, "E", "F"]]),
        control("E-lower", "E-lower lever", "lever", "LKR", "full", [[4, "E", "Eb"], [8, "E", "Eb"]]),
        control("D-lower", "D lower half-stop", "lever", "RKR", "half-stop", [[2, "D#", "D"], [9, "D", "C#"]]),
        control("RKR-full", "D lower full-stop", "lever", "RKR", "full-stop", [[2, "D#", "C#"], [9, "D", "C#"]]),
        control("RKL-half", "RKL half-stop", "lever", "RKL", "half-stop", [[1, "F#", "G"], [6, "G#", "G"]]),
        control("G-lower", "RKL full-stop / G lower", "lever", "RKL", "full-stop", [[1, "F#", "G"], [6, "G#", "F#"]])
      ],
      notes: "Starter profile. Knee locations vary; copy it and edit the exact mechanics on your guitar."
    };
  }

  let catalog = new Map([
    ["emmons-e9-basic", fallbackProfile("emmons-e9-basic", false)],
    ["day-e9-basic", fallbackProfile("day-e9-basic", true)]
  ]);
  let selectedId = store.loadState().activeProfileId;
  let currentProfile = null;
  let currentView = null;
  let selectedMobileGroup = "";
  let activeCell = null;
  let selectedCellDelta = 0;
  let activeControlId = "";
  let activeStringNumber = 0;
  let returnFocus = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function escapeSelector(value) {
    return global.CSS?.escape ? global.CSS.escape(String(value)) : String(value).replace(/(["\\])/g, "\\$1");
  }

  function option(value, label, selected) {
    return `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }

  function editableProfile(profile) {
    if (!profile?.immutable) return store.normalizeProfile(profile);
    const payload = catalog.get(profile.id) || fallbackProfile(profile.id, profile.id === "day-e9-basic");
    const editable = store.editableFromBuiltIn(payload, payload.label);
    return {
      ...editable,
      id: profile.id,
      name: payload.label,
      label: payload.label,
      immutable: true,
      origin: "built_in",
      validationStatus: "valid"
    };
  }

  function markDraft(message) {
    if (!currentProfile?.immutable && currentProfile.validationStatus !== "needs_review") currentProfile.validationStatus = "draft";
    if (message) elements.status.textContent = message;
  }

  function refreshLibrary() {
    const state = store.loadState();
    const profiles = store.listProfiles();
    const common = profiles.filter((profile) => profile.immutable);
    const custom = profiles.filter((profile) => !profile.immutable);
    elements.library.innerHTML = [
      `<optgroup label="Common setups">${common.map((profile) => option(profile.id, `${profile.label}${state.activeProfileId === profile.id ? " · Active" : ""}`, selectedId)).join("")}</optgroup>`,
      `<optgroup label="My custom setups">${custom.length ? custom.map((profile) => option(profile.id, `${profile.name}${state.activeProfileId === profile.id ? " · Active" : ""}`, selectedId)).join("") : '<option value="" disabled>No custom setups yet</option>'}</optgroup>`
    ].join("");
    elements.library.value = selectedId;
    const active = store.activeProfile();
    const label = active.name || active.label;
    elements.libraryActive.textContent = `Active: ${label}`;
    elements.activeBadge.textContent = active.validationStatus === "needs_review" ? "Needs review" : `Using ${label}`;
    elements.overview.textContent = active.validationStatus === "needs_review" ? `${label} needs review` : `Using ${label}`;
    elements.overviewUpdated.textContent = active.updatedAt
      ? new Date(active.updatedAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
      : "Built-in profile";
    doc.querySelectorAll("[data-active-copedent]").forEach((element) => store.renderStatus(element));
  }

  function profileFromEditor() {
    if (!currentProfile) throw new Error("Choose a setup first.");
    return store.normalizeProfile({
      ...currentProfile,
      name: elements.name.value.trim() || "My E9 setup",
      label: elements.name.value.trim() || "My E9 setup",
      guitar: elements.guitar.value.trim(),
      strings: currentProfile.strings,
      controls: currentProfile.controls,
      pedalOrder: currentProfile.pedalOrder,
      notes: elements.notes.value.trim(),
      validationStatus: currentProfile.validationStatus === "needs_review" ? "needs_review" : "draft"
    });
  }

  function groupStateCount(groups) {
    return groups.reduce((total, group) => total + group.states.length, 0);
  }

  function controlAria(control) {
    return `${control.label}, ${control.physicalPosition}, ${control.travel}`;
  }

  function renderGroupHeaders(groups) {
    return groups.map((group) => `
      <th class="copedent-physical-head" colspan="${group.states.length}" data-control-group="${escapeHtml(group.key)}">
        <button class="copedent-header-button" type="button" data-control-id="${escapeHtml(group.states[0].id)}" aria-label="Edit ${escapeHtml(group.physicalPosition)} control details">${escapeHtml(group.physicalPosition)}</button>
      </th>
    `).join("");
  }

  function renderStateHeaders(groups) {
    return groups.flatMap((group) => group.states.map((state) => `
      <th class="copedent-state-head" data-control-group="${escapeHtml(group.key)}">
        <button class="copedent-header-button" type="button" data-control-id="${escapeHtml(state.id)}" title="${escapeHtml(controlAria(state))}" aria-label="Edit ${escapeHtml(controlAria(state))}">${escapeHtml(state.headerLabel)}</button>
      </th>
    `)).join("");
  }

  function renderCell(group, state, string) {
    const key = `${string.stringNumber}:${state.id}`;
    const cell = currentView.cells[key];
    const label = cell?.label || "";
    const movement = cell ? `${cell.direction} ${Math.abs(cell.delta)} semitone${Math.abs(cell.delta) === 1 ? "" : "s"}` : "no change";
    const sounding = cell ? `${cell.change.fromNote} to ${cell.change.toNote}, ${movement}` : `${string.openNote}, no change`;
    return `
      <td data-control-group="${escapeHtml(group.key)}">
        <button class="copedent-cell-button ${cell ? `is-${cell.direction}` : "is-empty"}" type="button"
          data-cell-control="${escapeHtml(state.id)}" data-cell-string="${Number(string.stringNumber)}"
          aria-label="${escapeHtml(state.label)}, string ${Number(string.stringNumber)}: ${sounding}"
          ${currentProfile.immutable ? "disabled" : ""}>${escapeHtml(label)}</button>
      </td>
    `;
  }

  function renderGrid() {
    currentView = grid.project(currentProfile);
    const groups = currentView.groups;
    elements.pedalOrder.value = currentProfile.pedalOrder.join(" – ");
    if (!groups.length) {
      elements.grid.innerHTML = '<div class="copedent-grid-empty">No pedals or knee levers are recorded yet. Choose <strong>Add control</strong> to create the first column.</div>';
      renderMobileSelector(groups);
      return;
    }
    const pedalCount = groupStateCount(currentView.pedalGroups);
    const leverCount = groupStateCount(currentView.leverGroups);
    const superHeaders = [
      pedalCount ? `<th class="copedent-superhead" colspan="${pedalCount}" data-control-family="pedal">Pedals</th>` : "",
      leverCount ? `<th class="copedent-superhead" colspan="${leverCount}" data-control-family="lever">Knee levers</th>` : ""
    ].join("");
    elements.grid.innerHTML = `
      <table class="copedent-table" aria-label="Editable E9 copedent chart">
        <thead>
          <tr>
            <th class="copedent-sticky-string" rowspan="3">String</th>
            <th class="copedent-sticky-open" rowspan="3">Open</th>
            ${superHeaders}
          </tr>
          <tr>${renderGroupHeaders(groups)}</tr>
          <tr>${renderStateHeaders(groups)}</tr>
        </thead>
        <tbody>
          ${currentView.strings.map((string) => `
            <tr>
              <td class="copedent-sticky-string"><button class="copedent-string-button" type="button" data-string-number="${Number(string.stringNumber)}" aria-label="Edit string ${Number(string.stringNumber)} details">${Number(string.stringNumber)}</button></td>
              <td class="copedent-sticky-open"><button class="copedent-string-button" type="button" data-string-number="${Number(string.stringNumber)}" aria-label="Edit string ${Number(string.stringNumber)}, open ${escapeHtml(string.openNote)}">${escapeHtml(string.openNote)}</button></td>
              ${groups.flatMap((group) => group.states.map((state) => renderCell(group, state, string))).join("")}
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
    renderMobileSelector(groups);
  }

  function renderMobileSelector(groups) {
    if (!groups.length) {
      elements.mobileGroup.innerHTML = '<option value="">No controls</option>';
      elements.mobilePrevious.disabled = true;
      elements.mobileNext.disabled = true;
      return;
    }
    if (!groups.some((group) => group.key === selectedMobileGroup)) selectedMobileGroup = groups[0].key;
    elements.mobileGroup.innerHTML = groups.map((group) => option(group.key, `${group.type === "pedal" ? "Pedal" : "Knee"} · ${group.physicalPosition}${group.states.length > 1 ? ` · ${group.states.length} states` : ""}`, selectedMobileGroup)).join("");
    elements.mobileGroup.value = selectedMobileGroup;
    elements.mobilePrevious.disabled = groups.length < 2;
    elements.mobileNext.disabled = groups.length < 2;
    applyMobileGroup();
  }

  function applyMobileGroup() {
    if (!currentView) return;
    const narrow = global.matchMedia?.("(max-width: 760px)")?.matches;
    elements.grid.querySelectorAll("[data-control-group]").forEach((element) => {
      element.hidden = Boolean(narrow && element.dataset.controlGroup !== selectedMobileGroup);
    });
    elements.grid.querySelectorAll("[data-control-family]").forEach((element) => {
      if (!narrow) {
        element.hidden = false;
        element.colSpan = groupStateCount(element.dataset.controlFamily === "pedal" ? currentView.pedalGroups : currentView.leverGroups);
        return;
      }
      const selected = currentView.groups.find((group) => group.key === selectedMobileGroup);
      element.hidden = !selected || element.dataset.controlFamily !== selected.type;
      if (!element.hidden) element.colSpan = selected.states.length;
    });
  }

  function setEditorState() {
    const immutable = Boolean(currentProfile?.immutable);
    [elements.name, elements.guitar, elements.notes, elements.addControl, elements.save]
      .forEach((element) => { if (element) element.disabled = immutable; });
    elements.clone.hidden = !immutable;
    elements.duplicate.disabled = immutable;
    elements.remove.disabled = immutable;
    elements.addFromStarter.disabled = immutable;
    elements.reset.disabled = immutable;
    elements.activateEdited.textContent = immutable ? "Use this setup" : "Validate and use";
    elements.activate.textContent = store.loadState().activeProfileId === selectedId ? "Active" : "Use this setup";
    elements.activate.disabled = store.loadState().activeProfileId === selectedId;
  }

  function renderSelected(message = "") {
    const libraryProfile = store.profileById(selectedId) || store.activeProfile();
    selectedId = libraryProfile.id;
    currentProfile = editableProfile(libraryProfile);
    refreshLibrary();
    elements.name.value = currentProfile.name || currentProfile.label || "";
    elements.family.value = "E9";
    elements.stringCount.value = "10";
    elements.guitar.value = currentProfile.guitar || "";
    elements.notes.value = currentProfile.notes || "";
    const originId = String(currentProfile.origin || "").replace(/^clone:/, "");
    elements.template.value = catalog.has(currentProfile.id) ? currentProfile.id : (catalog.has(originId) ? originId : "emmons-e9-basic");
    const issues = currentProfile.reviewIssues || [];
    elements.reviewIssues.innerHTML = issues.length
      ? `<strong>Review required.</strong><ul>${issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}</ul>`
      : currentProfile.immutable
        ? "This starter is read-only. Its chart includes RKL and RKR. Choose Copy and edit to match your guitar."
        : `Saved locally · revision ${Number(currentProfile.revision || 1)} · ${escapeHtml(currentProfile.validationStatus || "draft")}`;
    renderGrid();
    setEditorState();
    elements.status.textContent = message || (issues[0]
      ? issues[0]
      : currentProfile.immutable
        ? "Read-only starter. Copy it before changing a cell or heading."
        : currentProfile.validationStatus === "valid"
          ? "Validated setup. Any edit returns it to draft until you validate again."
          : "Draft setup. Save it now or validate it when the chart matches your guitar.");
  }

  function accessHeaders() {
    const queryRole = new URLSearchParams(global.location.search).get("access");
    let storedRole = "";
    try { storedRole = global.localStorage.getItem("steel-guitar-rag.mockAccessState.v1") || ""; } catch (_error) { storedRole = ""; }
    return { "Content-Type": "application/json", ...(answerUi?.devAccessHeaders?.(queryRole || storedRole) || {}) };
  }

  async function validateProfile(profile) {
    const response = await global.fetch("/api/copedents/validate", {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: accessHeaders(),
      body: JSON.stringify({ profile })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.valid) {
      const firstIssue = payload.issues?.[0]?.message || payload.issues?.[0] || payload.detail || payload.error;
      throw new Error(firstIssue || "This setup did not pass mechanical validation.");
    }
    return payload;
  }

  async function saveDraft() {
    try {
      if (currentProfile.immutable) throw new Error("Choose Copy and edit before changing this starter.");
      currentProfile = store.saveProfile(profileFromEditor());
      selectedId = currentProfile.id;
      renderSelected("Draft saved locally. Validate it before using it throughout the app.");
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  async function validateAndActivate() {
    try {
      if (currentProfile.immutable) {
        store.setActive(currentProfile.id);
      } else {
        currentProfile = store.saveProfile(profileFromEditor());
        elements.status.textContent = "Validating every open pitch, cell, and control state…";
        await validateProfile(currentProfile);
        currentProfile = store.markValidated(currentProfile.id);
        store.setActive(currentProfile.id);
      }
      selectedId = currentProfile.id;
      renderSelected(`Using ${currentProfile.name || currentProfile.label} throughout the app.`);
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function effectSignature(control) {
    return (control.changes || []).map((change) => `${change.stringNumber}:${change.fromNote}>${change.toNote}`).sort().join("|");
  }

  function missingStarterControls(profile) {
    const starterPayload = catalog.get(elements.template.value) || fallbackProfile(elements.template.value, elements.template.value === "day-e9-basic");
    const starter = store.editableFromBuiltIn(starterPayload, "comparison");
    const existing = new Set((profile.controls || []).map(effectSignature));
    return (starter.controls || []).filter((control) => !existing.has(effectSignature(control)));
  }

  function compareWithStarter() {
    try {
      const profile = currentProfile.immutable ? currentProfile : profileFromEditor();
      const missing = missingStarterControls(profile);
      const starterLabel = (catalog.get(elements.template.value) || {}).label || "starter";
      elements.status.textContent = missing.length
        ? `Compared mechanically with ${starterLabel}: missing ${missing.map((control) => `${control.label} (${control.physicalPosition})`).join(", ")}. Nothing was added.`
        : "Every starter mechanical effect is represented. Your names and physical positions may still differ.";
    } catch (error) {
      elements.status.textContent = error.message;
    }
    elements.more.open = false;
  }

  function addMissingFromStarter() {
    try {
      if (currentProfile.immutable) throw new Error("Copy this starter before adding states.");
      const profile = profileFromEditor();
      const missing = missingStarterControls(profile);
      if (!missing.length) {
        elements.status.textContent = "No starter states are missing.";
        return;
      }
      profile.controls.push(store.clone(missing[0]));
      currentProfile = store.normalizeProfile(profile);
      markDraft(`Added ${missing[0].label}. Review its column before saving or activating.`);
      renderGrid();
    } catch (error) {
      elements.status.textContent = error.message;
    }
    elements.more.open = false;
  }

  function cloneSelected() {
    const source = store.profileById(selectedId);
    let copy;
    if (source.immutable) {
      const payload = catalog.get(source.id) || fallbackProfile(source.id, source.id === "day-e9-basic");
      copy = store.editableFromBuiltIn(payload, `${source.label.replace(/ starter$/i, "")} custom`);
    } else {
      const blank = store.blankProfile(`${source.name} copy`);
      copy = store.normalizeProfile({
        ...store.clone(source),
        id: blank.id,
        name: blank.name,
        label: blank.name,
        origin: `clone:${source.id}`,
        revision: 1,
        validationStatus: "draft"
      });
    }
    copy = store.saveProfile(copy);
    selectedId = copy.id;
    renderSelected("Editable copy created. Change the chart, then validate it when it matches your guitar.");
    elements.more.open = false;
  }

  function createCustom() {
    const profile = store.saveProfile(store.blankProfile());
    selectedId = profile.id;
    renderSelected("Blank 10-string E9 setup created. Add the controls that are actually on this guitar.");
  }

  function deleteCustom() {
    if (currentProfile.immutable) return;
    if (!global.confirm(`Delete ${currentProfile.name}? This removes only this local custom setup.`)) return;
    store.deleteProfile(currentProfile.id);
    selectedId = store.loadState().activeProfileId;
    renderSelected("Custom setup deleted. Your other setups were not changed.");
    elements.more.open = false;
  }

  function addControlState() {
    if (currentProfile.immutable) return;
    const id = `control-${Date.now()}`;
    currentProfile.controls.push({
      id,
      label: "New lever",
      type: "lever",
      physicalPosition: "RKL",
      travel: "full",
      aliases: [],
      notes: "",
      changes: []
    });
    markDraft("New control added. Name it, place it, then select cells in its column.");
    renderGrid();
    openControlDialog(id, elements.addControl);
  }

  function setCellChoice(delta) {
    selectedCellDelta = Number(delta);
    elements.customDelta.value = Math.abs(selectedCellDelta) > 3 ? String(selectedCellDelta) : "";
    elements.deltaPicker.querySelectorAll("[data-cell-delta]").forEach((button) => {
      button.setAttribute("aria-pressed", String(Number(button.dataset.cellDelta) === selectedCellDelta));
    });
    updateCellPreview();
  }

  function updateCellPreview() {
    if (!activeCell) return;
    const string = currentProfile.strings.find((item) => Number(item.stringNumber) === activeCell.stringNumber);
    const from = string?.openNote || "?";
    if (!selectedCellDelta) {
      elements.cellPreview.textContent = `No change. The ${activeCell.control.label} cell on string ${activeCell.stringNumber} will be blank.`;
      return;
    }
    const to = grid.destinationForDelta(from, selectedCellDelta) || "?";
    const direction = selectedCellDelta > 0 ? "Raise" : "Lower";
    elements.cellPreview.textContent = `${from} → ${to}. ${direction} ${Math.abs(selectedCellDelta)} semitone${Math.abs(selectedCellDelta) === 1 ? "" : "s"}.`;
  }

  function openCellDialog(controlId, stringNumber, trigger) {
    if (currentProfile.immutable) return;
    const control = currentProfile.controls.find((item) => String(item.id) === String(controlId));
    const string = currentProfile.strings.find((item) => Number(item.stringNumber) === Number(stringNumber));
    if (!control || !string) return;
    const change = control.changes.find((item) => Number(item.stringNumber) === Number(stringNumber));
    activeCell = { control, stringNumber: Number(stringNumber) };
    returnFocus = trigger;
    elements.cellContext.textContent = `${control.label} · ${control.physicalPosition} · string ${stringNumber} (${string.openNote})`;
    setCellChoice(change ? grid.semitoneDelta(change.fromNote, change.toNote, change.changeType) : 0);
    elements.cellDialog.showModal();
  }

  function applyCellChange() {
    try {
      if (!activeCell) return;
      const controlId = activeCell.control.id;
      const stringNumber = activeCell.stringNumber;
      currentProfile = store.normalizeProfile(grid.setCell(currentProfile, controlId, stringNumber, selectedCellDelta));
      markDraft(`Updated ${activeCell.control.label} on string ${stringNumber}.`);
      elements.cellDialog.close("applied");
      renderGrid();
      global.setTimeout(() => elements.grid.querySelector(`[data-cell-control="${escapeSelector(controlId)}"][data-cell-string="${stringNumber}"]`)?.focus(), 0);
    } catch (error) {
      elements.cellPreview.textContent = error.message;
    }
  }

  function controlById(id = activeControlId) {
    return currentProfile.controls.find((control) => String(control.id) === String(id));
  }

  function setControlDialogDisabled(disabled) {
    [elements.controlLabel, elements.controlPosition, elements.controlType, elements.controlTravel, elements.controlAliases,
      elements.controlPrevious, elements.controlNext, elements.controlAddState, elements.controlRemove, elements.controlApply]
      .forEach((element) => { element.disabled = disabled; });
  }

  function openControlDialog(controlId, trigger) {
    const control = controlById(controlId);
    if (!control) return;
    activeControlId = String(control.id);
    returnFocus = trigger;
    elements.controlTitle.textContent = `${control.physicalPosition || control.label} details`;
    elements.controlLabel.value = control.label || "";
    elements.controlPosition.value = control.physicalPosition || "";
    elements.controlType.value = control.type || "lever";
    elements.controlTravel.value = control.travel || (control.type === "pedal" ? "pedal" : "full");
    elements.controlAliases.value = (control.aliases || []).join(", ");
    setControlDialogDisabled(Boolean(currentProfile.immutable));
    elements.controlPrevious.disabled = Boolean(currentProfile.immutable || control.type !== "pedal" || currentProfile.pedalOrder.indexOf(control.id) <= 0);
    elements.controlNext.disabled = Boolean(currentProfile.immutable || control.type !== "pedal" || currentProfile.pedalOrder.indexOf(control.id) >= currentProfile.pedalOrder.length - 1);
    elements.controlDialog.showModal();
  }

  function applyControlFields({ close = true } = {}) {
    const control = controlById();
    if (!control || currentProfile.immutable) return null;
    const wasPedal = control.type === "pedal";
    control.label = elements.controlLabel.value.trim() || control.label || "Unnamed control";
    control.physicalPosition = elements.controlPosition.value.trim() || control.physicalPosition || "Unplaced";
    control.type = elements.controlType.value;
    control.travel = control.type === "pedal" ? "pedal" : elements.controlTravel.value;
    control.aliases = elements.controlAliases.value.split(",").map((value) => value.trim()).filter(Boolean);
    if (control.type === "pedal" && !currentProfile.pedalOrder.includes(control.id)) currentProfile.pedalOrder.push(control.id);
    if (wasPedal && control.type !== "pedal") currentProfile.pedalOrder = currentProfile.pedalOrder.filter((id) => id !== control.id);
    currentProfile = store.normalizeProfile(currentProfile);
    markDraft(`Updated ${control.label}. Its stable control identity and string actions were preserved.`);
    if (close) {
      elements.controlDialog.close("applied");
      renderGrid();
      global.setTimeout(() => elements.grid.querySelector(`[data-control-id="${escapeSelector(control.id)}"]`)?.focus(), 0);
    }
    return control;
  }

  function movePedal(direction) {
    const control = applyControlFields({ close: false });
    if (!control || control.type !== "pedal") return;
    const index = currentProfile.pedalOrder.indexOf(control.id);
    const target = index + Number(direction);
    if (index < 0 || target < 0 || target >= currentProfile.pedalOrder.length) return;
    [currentProfile.pedalOrder[index], currentProfile.pedalOrder[target]] = [currentProfile.pedalOrder[target], currentProfile.pedalOrder[index]];
    markDraft(`Moved ${control.label} ${direction < 0 ? "left" : "right"} in the pedal order.`);
    elements.controlDialog.close("applied");
    renderGrid();
  }

  function addTravelState() {
    const source = applyControlFields({ close: false });
    if (!source) return;
    const id = `${source.id}-${Date.now()}`;
    const nextTravel = /half/i.test(source.travel) ? "full-stop" : "half-stop";
    const state = {
      ...store.clone(source),
      id,
      label: `${source.physicalPosition} ${nextTravel === "half-stop" ? "half" : "full"}`,
      travel: source.type === "pedal" ? "pedal" : nextTravel,
      changes: store.clone(source.changes || [])
    };
    currentProfile.controls.push(state);
    if (state.type === "pedal") {
      const sourceIndex = currentProfile.pedalOrder.indexOf(source.id);
      currentProfile.pedalOrder.splice(sourceIndex + 1, 0, state.id);
    }
    activeControlId = id;
    markDraft(`Added a separate ${state.travel} state for ${state.physicalPosition}. Review its cells.`);
    elements.controlDialog.close("applied");
    renderGrid();
    global.setTimeout(() => openControlDialog(id, elements.grid.querySelector(`[data-control-id="${escapeSelector(id)}"]`)), 0);
  }

  function removeControlState() {
    const control = controlById();
    if (!control || currentProfile.immutable) return;
    if (!global.confirm(`Remove the ${control.label} state and all of its changed cells?`)) return;
    currentProfile.controls = currentProfile.controls.filter((item) => item.id !== control.id);
    currentProfile.pedalOrder = currentProfile.pedalOrder.filter((id) => id !== control.id);
    markDraft(`${control.label} was removed from this draft.`);
    elements.controlDialog.close("removed");
    renderGrid();
  }

  function openStringDialog(stringNumber, trigger) {
    const string = currentProfile.strings.find((item) => Number(item.stringNumber) === Number(stringNumber));
    if (!string) return;
    activeStringNumber = Number(stringNumber);
    returnFocus = trigger;
    const scientific = grid.scientificPitch(string.openPitchValue, string.openNote);
    elements.stringTitle.textContent = `String ${activeStringNumber} details`;
    elements.stringNote.value = string.openNote || scientific.note;
    elements.stringOctave.value = scientific.octave;
    elements.stringGauge.value = string.gauge || "";
    elements.stringNotes.value = string.notes || "";
    [elements.stringNote, elements.stringOctave, elements.stringGauge, elements.stringNotes, elements.stringApply]
      .forEach((element) => { element.disabled = Boolean(currentProfile.immutable); });
    elements.stringDialog.showModal();
  }

  function applyStringDetails() {
    try {
      if (currentProfile.immutable) return;
      const string = currentProfile.strings.find((item) => Number(item.stringNumber) === activeStringNumber);
      const note = elements.stringNote.value.trim();
      const midi = grid.midiForPitch(note, Number(elements.stringOctave.value));
      if (midi == null) throw new Error("Enter a note such as F# and an octave from 0 through 8.");
      currentProfile.controls.forEach((control) => {
        (control.changes || []).forEach((change) => {
          if (Number(change.stringNumber) !== activeStringNumber) return;
          const delta = grid.semitoneDelta(change.fromNote, change.toNote, change.changeType);
          change.fromNote = note;
          change.toNote = grid.destinationForDelta(note, delta);
          change.changeType = grid.changeDirection(delta);
        });
      });
      string.openNote = note;
      string.openPitchValue = midi;
      string.gauge = elements.stringGauge.value.trim();
      string.notes = elements.stringNotes.value.trim();
      currentProfile = store.normalizeProfile(currentProfile);
      markDraft(`Updated string ${activeStringNumber}. Existing cell intervals were preserved from the new open pitch.`);
      elements.stringDialog.close("applied");
      renderGrid();
      global.setTimeout(() => elements.grid.querySelector(`[data-string-number="${activeStringNumber}"]`)?.focus(), 0);
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function stepMobileGroup(direction) {
    const groups = currentView?.groups || [];
    if (!groups.length) return;
    const index = Math.max(0, groups.findIndex((group) => group.key === selectedMobileGroup));
    selectedMobileGroup = groups[(index + Number(direction) + groups.length) % groups.length].key;
    elements.mobileGroup.value = selectedMobileGroup;
    applyMobileGroup();
  }

  async function loadCatalog() {
    try {
      const response = await global.fetch("/api/copedents/e9", { credentials: "same-origin", cache: "no-store", headers: accessHeaders() });
      const payload = await response.json().catch(() => ({}));
      if (response.ok && Array.isArray(payload.profiles)) catalog = new Map(payload.profiles.map((profile) => [profile.id, profile]));
    } catch (_error) {
      elements.status.textContent = "Using the offline starter charts. Live validation still requires a connection.";
    }
    renderSelected();
  }

  elements.library.addEventListener("change", () => {
    selectedId = elements.library.value;
    renderSelected();
  });
  elements.activate.addEventListener("click", validateAndActivate);
  elements.activateEdited.addEventListener("click", validateAndActivate);
  elements.clone.addEventListener("click", cloneSelected);
  elements.duplicate.addEventListener("click", cloneSelected);
  elements.create.addEventListener("click", createCustom);
  elements.remove.addEventListener("click", deleteCustom);
  elements.save.addEventListener("click", saveDraft);
  elements.reset.addEventListener("click", () => { renderSelected("Unsaved chart edits discarded."); elements.more.open = false; });
  elements.compare.addEventListener("click", compareWithStarter);
  elements.addFromStarter.addEventListener("click", addMissingFromStarter);
  elements.addControl.addEventListener("click", addControlState);
  [elements.name, elements.guitar, elements.notes].forEach((element) => element.addEventListener("input", () => markDraft("Unsaved profile detail changes.")));

  elements.grid.addEventListener("click", (event) => {
    const cell = event.target.closest("[data-cell-control]");
    if (cell) {
      openCellDialog(cell.dataset.cellControl, Number(cell.dataset.cellString), cell);
      return;
    }
    const control = event.target.closest("[data-control-id]");
    if (control) {
      openControlDialog(control.dataset.controlId, control);
      return;
    }
    const string = event.target.closest("[data-string-number]");
    if (string) openStringDialog(Number(string.dataset.stringNumber), string);
  });

  elements.deltaPicker.addEventListener("click", (event) => {
    const button = event.target.closest("[data-cell-delta]");
    if (button) setCellChoice(Number(button.dataset.cellDelta));
  });
  elements.customDelta.addEventListener("input", () => {
    if (elements.customDelta.value === "") return;
    selectedCellDelta = Number(elements.customDelta.value);
    elements.deltaPicker.querySelectorAll("[data-cell-delta]").forEach((button) => button.setAttribute("aria-pressed", "false"));
    updateCellPreview();
  });
  elements.cellApply.addEventListener("click", applyCellChange);
  elements.controlApply.addEventListener("click", () => applyControlFields());
  elements.controlPrevious.addEventListener("click", () => movePedal(-1));
  elements.controlNext.addEventListener("click", () => movePedal(1));
  elements.controlAddState.addEventListener("click", addTravelState);
  elements.controlRemove.addEventListener("click", removeControlState);
  elements.stringApply.addEventListener("click", applyStringDetails);
  elements.mobileGroup.addEventListener("change", () => { selectedMobileGroup = elements.mobileGroup.value; applyMobileGroup(); });
  elements.mobilePrevious.addEventListener("click", () => stepMobileGroup(-1));
  elements.mobileNext.addEventListener("click", () => stepMobileGroup(1));
  global.addEventListener("resize", applyMobileGroup);

  [elements.cellDialog, elements.controlDialog, elements.stringDialog].forEach((dialog) => {
    dialog.addEventListener("close", () => {
      if (dialog.returnValue !== "applied" && returnFocus?.isConnected) returnFocus.focus();
      returnFocus = null;
    });
  });

  refreshLibrary();
  renderSelected();
  loadCatalog();
  store.subscribe(() => refreshLibrary());
})(globalThis);
