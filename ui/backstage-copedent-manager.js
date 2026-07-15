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
    libraryGroups: $("#copedent-library-groups"),
    activeBadge: $("#copedent-active-badge"),
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
    exportProfile: $("#export-copedent"),
    remove: $("#delete-copedent"),
    more: $("#copedent-more"),
    status: $("#copedent-save-status"),
    overview: $("#copedent-overview-summary"),
    overviewUpdated: $("#copedent-overview-updated"),
    overviewStatus: $("#overview-setup-status"),
    overviewStationStatus: $("#overview-station-setup-status"),
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
    controlReset: $("#copedent-control-reset"),
    controlApply: $("#copedent-control-apply"),
    stringDialog: $("#copedent-string-dialog"),
    stringTitle: $("#copedent-string-title"),
    stringNote: $("#copedent-string-note"),
    stringOctave: $("#copedent-string-octave"),
    stringGauge: $("#copedent-string-gauge"),
    stringNotes: $("#copedent-string-notes"),
    stringApply: $("#copedent-string-apply"),
    accountStatus: $("#copedent-account-status"),
    passLabel: $("#copedent-pass-label"),
    syncCopy: $("#copedent-sync-copy"),
    localImport: $("#copedent-local-import"),
    localImportList: $("#copedent-local-import-list"),
    importSelected: $("#copedent-import-selected"),
    importStatus: $("#copedent-import-status"),
    localEmpty: $("#copedent-local-empty"),
    plateName: $("#setup-nameplate-name"),
    activeStatus: $("#setup-active-status"),
    activeSync: $("#setup-active-sync"),
    activeValidation: $("#setup-active-validation"),
    activeRevision: $("#setup-active-revision"),
    activeSummary: $("#setup-active-summary"),
    editActive: $("#copedent-edit-active"),
    duplicateActive: $("#copedent-duplicate-active"),
    exportActive: $("#copedent-export-active"),
    workbenchTitle: $("#copedent-workbench-title"),
    workbenchMeta: $("#copedent-workbench-meta"),
    editNotice: $("#copedent-edit-notice"),
    editNoticeTitle: $("#copedent-edit-notice-title"),
    editNoticeCopy: $("#copedent-edit-notice-copy"),
    unsavedDialog: $("#copedent-unsaved-dialog"),
    unsavedKeep: $("#copedent-unsaved-keep"),
    unsavedDiscard: $("#copedent-unsaved-discard"),
    unsavedSave: $("#copedent-unsaved-save")
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
        control("A", "A", "pedal", pedalPosition.A, "pedal", [[5, "B", "C#"], [10, "B", "C#"]]),
        control("B", "B", "pedal", pedalPosition.B, "pedal", [[3, "G#", "A"], [6, "G#", "A"]]),
        control("C", "C", "pedal", pedalPosition.C, "pedal", [[4, "E", "F#"], [5, "B", "C#"]]),
        control("E-raise", "F", "lever", "LKL", "full", [[4, "E", "F"], [8, "E", "F"]]),
        control("E-lower", "E", "lever", "LKR", "full", [[4, "E", "Eb"], [8, "E", "Eb"]]),
        control("D-lower", "D", "lever", "RKR", "half-stop", [[2, "D#", "D"], [9, "D", "C#"]]),
        control("RKR-full", "DD", "lever", "RKR", "full-stop", [[2, "D#", "C#"], [9, "D", "C#"]]),
        control("RKL-half", "G", "lever", "RKL", "half-stop", [[1, "F#", "G"], [6, "G#", "G"]]),
        control("G-lower", "GG", "lever", "RKL", "full-stop", [[1, "F#", "G"], [6, "G#", "F#"]])
      ],
      notes: "Starter profile. Knee locations vary; copy it and edit the exact mechanics on your guitar."
    };
  }

  let catalog = new Map([
    ["emmons-e9-basic", fallbackProfile("emmons-e9-basic", false)],
    ["day-e9-basic", fallbackProfile("day-e9-basic", true)]
  ]);
  let selectedId = store.activeProfile().id;
  let selectionWasExplicit = false;
  let currentProfile = null;
  let currentView = null;
  let selectedMobileGroup = "";
  let activeCell = null;
  let selectedCellDelta = 0;
  let activeControlId = "";
  let activeStringNumber = 0;
  let returnFocus = null;
  let hasUnsavedChanges = false;
  let pendingExitResolution = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function escapeSelector(value) {
    return global.CSS?.escape ? global.CSS.escape(String(value)) : String(value).replace(/(["\\])/g, "\\$1");
  }

  function option(value, label, selected) {
    return `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }

  function profileName(profile) {
    return String(profile?.name || profile?.label || "Unnamed E9 setup");
  }

  function validationLabel(profile) {
    if (profile?.validationStatus === "needs_review") return "Needs review";
    if (profile?.validationStatus === "valid" || profile?.immutable) return "Validated";
    return "Draft";
  }

  function renderProfileEntry(profile, group, activeId) {
    const name = profileName(profile);
    const active = profile.id === activeId;
    const selected = profile.id === selectedId;
    const custom = !profile.immutable;
    const badge = active ? "Active" : (custom ? "Custom" : "Included");
    const meta = [
      `Revision ${Number(profile.revision || 1)}`,
      custom && accountState().enabled ? "Account-synced" : (custom ? "Saved on this device" : "Included setup"),
      validationLabel(profile)
    ].join(" · ");
    return `
      <button class="setup-library-entry" type="button" data-setup-profile="${escapeHtml(profile.id)}"
        aria-pressed="${String(selected)}" aria-label="Select ${escapeHtml(name)} from ${escapeHtml(group)}">
        <span class="setup-library-entry-name">${escapeHtml(name)}</span>
        <span class="setup-library-entry-badge${active ? " is-active" : (custom ? " is-custom" : "")}">${badge}</span>
        <span class="setup-library-entry-meta">${escapeHtml(meta)}</span>
      </button>`;
  }

  function renderProfileGroup(title, profiles, group, activeId, emptyCopy) {
    return `
      <section class="setup-library-group" aria-label="${escapeHtml(title)}">
        <h4>${escapeHtml(title)}</h4>
        <div class="setup-library-list">
          ${profiles.length ? profiles.map((profile) => renderProfileEntry(profile, group, activeId)).join("") : `<p class="setup-library-empty">${escapeHtml(emptyCopy)}</p>`}
        </div>
      </section>`;
  }

  function renderActiveSetup(active) {
    const account = accountState();
    const name = profileName(active);
    const validated = validationLabel(active);
    const ready = validated === "Validated";
    elements.plateName.textContent = name;
    elements.activeStatus.textContent = ready ? "In use" : "Needs attention";
    elements.activeStatus.classList.toggle("is-active", ready);
    elements.activeStatus.classList.toggle("is-warning", !ready);
    elements.activeValidation.textContent = ready
      ? "Ready for use — mechanical checks passed"
      : validated === "Needs review"
        ? "Needs review before the app can use it"
        : "Draft saved — validate before use";
    elements.activeRevision.textContent = `Revision ${Number(active.revision || 1)}`;
    elements.activeSync.textContent = active.immutable
      ? "Included with the app"
      : account.enabled && account.verified
        ? "Saved to your account"
        : "Saved on this device";
    elements.activeSummary.textContent = ready
      ? active.immutable
        ? "Included setup selected across the app."
        : account.enabled && account.verified
          ? "Saved to your account and used across Ask, Explorer, Lessons, and Melody Studio."
          : "Saved on this device and used across the app."
      : "This setup cannot be used across the app until its saved draft passes validation.";
    elements.editActive.querySelector("span").textContent = active.immutable ? "Copy and edit" : "Edit setup";
    elements.duplicateActive.disabled = Boolean(!account.canManageCustom && account.enabled);
    elements.exportActive.disabled = Boolean(active.immutable);
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

  function accountState() {
    return store.accountStatus?.() || { enabled: false, verified: true, canManageCustom: true, canUseCustom: true, passLabel: "Local preview" };
  }

  function customEditingLocked() {
    const account = accountState();
    return Boolean(account.enabled && !account.canManageCustom);
  }

  function showSubscription(message = "Session Pass is required to create and use a custom copedent. Checkout is not available in this beta yet.") {
    elements.status.textContent = message;
    doc.querySelector("#backstage-tab-pass")?.click();
  }

  function exportLocalProfile(profile) {
    const blob = new Blob([JSON.stringify(store.profileSnapshot(profile), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = doc.createElement("a");
    link.href = url;
    link.download = `${String(profile.name || "e9-copedent").replace(/[^a-z0-9_-]+/gi, "-").toLowerCase()}.json`;
    link.click();
    global.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function renderAccountStatus() {
    const account = accountState();
    if (!elements.accountStatus) return;
    elements.passLabel.textContent = account.enabled ? account.passLabel : "Local preview";
    if (!account.enabled) {
      elements.syncCopy.textContent = "Account copedent sync is off in this environment. The existing local editor remains available.";
    } else if (!account.verified) {
      elements.syncCopy.textContent = "Account verification failed. Personalized custom setups are unavailable; Emmons remains available.";
    } else if (account.passId === "creator") {
      elements.syncCopy.textContent = "Creator Access: custom setups synchronize to your verified account with no upgrade or payment prompt.";
    } else if (account.canManageCustom) {
      elements.syncCopy.textContent = "Custom setups synchronize to your verified account and follow you to another signed-in device.";
    } else {
      elements.syncCopy.textContent = "Emmons and Day synchronize with your account. Session Pass is required to create, import, edit, activate, or use custom setups.";
    }
    const localProfiles = account.enabled
      ? (store.localProfilesForImport?.() || []).filter((profile) => !profile.alreadyImported)
      : [];
    elements.localImport.hidden = !localProfiles.length;
    elements.localEmpty.hidden = true;
    elements.localEmpty.textContent = "";
    elements.localImportList.hidden = !localProfiles.length;
    if (!localProfiles.length) {
      elements.localImportList.innerHTML = "";
      elements.importSelected.disabled = true;
      elements.importSelected.textContent = "Nothing to import";
      return;
    }
    elements.localImportList.innerHTML = localProfiles.map((profile) => `
      <div class="setup-local-entry" data-local-profile="${escapeHtml(profile.id)}">
        <label><input type="checkbox" value="${escapeHtml(profile.id)}" ${!account.canManageCustom ? "disabled" : ""}> <span><strong>${escapeHtml(profile.name)}</strong><br><small>Local only · on this browser</small></span></label>
        <span class="setup-local-entry-actions">
          <button class="backstage-button" type="button" data-export-local="${escapeHtml(profile.id)}">Export</button>
          <button class="backstage-button" type="button" data-delete-local="${escapeHtml(profile.id)}" aria-label="Delete local copy of ${escapeHtml(profile.name)}">Delete</button>
        </span>
      </div>
    `).join("");
    elements.importSelected.disabled = Boolean(!account.enabled || !account.canManageCustom);
    elements.importSelected.textContent = account.canManageCustom ? "Import selected setups" : "Session Pass required to import";
  }

  function showEditNotice(state = "none") {
    if (!elements.editNotice) return;
    elements.editNotice.hidden = state === "none";
    elements.editNotice.dataset.state = state;
    if (state === "unsaved") {
      elements.editNoticeTitle.textContent = "Unsaved changes";
      elements.editNoticeCopy.textContent = "Save a draft to preserve them, or Validate and use when the setup matches your guitar.";
    } else if (state === "saved") {
      elements.editNoticeTitle.textContent = "Draft saved";
      elements.editNoticeCopy.textContent = "Validate and use before this setup is ready across the app.";
    }
  }

  function setUnsavedChanges(value) {
    hasUnsavedChanges = Boolean(value);
    if (hasUnsavedChanges) showEditNotice("unsaved");
  }

  function finishPendingExit(allowed) {
    const resolve = pendingExitResolution;
    pendingExitResolution = null;
    if (elements.unsavedDialog?.open) elements.unsavedDialog.close(allowed ? "continue" : "stay");
    resolve?.(Boolean(allowed));
  }

  function requestExit() {
    if (!hasUnsavedChanges) return Promise.resolve(true);
    if (pendingExitResolution) return Promise.resolve(false);
    return new Promise((resolve) => {
      pendingExitResolution = resolve;
      elements.unsavedDialog.showModal();
      elements.unsavedKeep.focus();
    });
  }

  async function runAfterSafeExit(action) {
    if (!await requestExit()) return false;
    await action();
    return true;
  }

  function markDraft(message) {
    if (!currentProfile?.immutable && currentProfile.validationStatus !== "needs_review") currentProfile.validationStatus = "draft";
    if (currentProfile && !currentProfile.immutable) {
      elements.activeBadge.textContent = validationLabel(currentProfile);
      elements.activeBadge.classList.remove("is-active");
    }
    setUnsavedChanges(true);
    if (message) elements.status.textContent = message;
  }

  function refreshLibrary() {
    const profiles = store.listProfiles();
    const common = profiles.filter((profile) => profile.immutable);
    const custom = profiles.filter((profile) => !profile.immutable);
    const activeId = store.activeProfile().id;
    elements.library.innerHTML = [
      `<optgroup label="Included setups">${common.map((profile) => option(profile.id, `${profile.label} · Included${activeId === profile.id ? " · Active" : ""}`, selectedId)).join("")}</optgroup>`,
      `<optgroup label="My custom setups">${custom.length ? custom.map((profile) => option(profile.id, `${profile.name}${activeId === profile.id ? " · Active" : ""}${customEditingLocked() ? " · Locked" : ""}`, selectedId)).join("") : '<option value="" disabled>No account-synced custom setups yet</option>'}</optgroup>`
    ].join("");
    elements.library.value = selectedId;
    const active = store.activeProfile();
    const label = active.name || active.label;
    elements.libraryGroups.innerHTML = [
      renderProfileGroup("Included setups", common.filter((profile) => profile.id !== activeId), "included setups", activeId, "No other included setups are available."),
      renderProfileGroup("Custom setups", custom.filter((profile) => profile.id !== activeId), "custom setups", activeId, "No account-backed custom setups yet.")
    ].join("");
    renderActiveSetup(active);
    elements.activeBadge.textContent = validationLabel(currentProfile || active);
    elements.overview.textContent = active.validationStatus === "needs_review" ? `${label} needs review` : `Using ${label}`;
    if (elements.overviewStatus) elements.overviewStatus.textContent = `Active · ${validationLabel(active)}`;
    if (elements.overviewStationStatus) elements.overviewStationStatus.textContent = `Active · ${validationLabel(active)}`;
    elements.overviewUpdated.textContent = active.updatedAt
      ? new Date(active.updatedAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
      : "Built-in profile";
    doc.querySelectorAll("[data-active-copedent]").forEach((element) => store.renderStatus(element));
    renderAccountStatus();
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

  function renderTabLabelHeaders(groups) {
    return groups.flatMap((group) => group.states.map((state) => `
      <th class="copedent-tab-label-head" data-control-group="${escapeHtml(group.key)}">
        <button class="copedent-header-button copedent-tab-label-button" type="button" data-control-id="${escapeHtml(state.id)}"
          title="${escapeHtml(controlAria(state))}" aria-label="Edit tab label ${escapeHtml(state.tabLabel)} for ${escapeHtml(state.physicalPosition)}">${escapeHtml(state.tabLabel)}</button>
      </th>
    `)).join("");
  }

  function renderTravelHeaders(groups) {
    return groups.flatMap((group) => group.states.map((state) => `
      <th class="copedent-state-head copedent-travel-head" data-control-group="${escapeHtml(group.key)}">
        <button class="copedent-header-button" type="button" data-control-id="${escapeHtml(state.id)}" title="${escapeHtml(controlAria(state))}" aria-label="Edit ${escapeHtml(state.physicalPosition)} ${escapeHtml(state.headerLabel)} travel details">${escapeHtml(state.headerLabel)}</button>
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
          ${currentProfile.immutable || customEditingLocked() ? "disabled" : ""}>${escapeHtml(label)}</button>
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
            <th class="copedent-row-label" colspan="2">Control family</th>
            ${superHeaders}
          </tr>
          <tr><th class="copedent-row-label" colspan="2">Physical control</th>${renderGroupHeaders(groups)}</tr>
          <tr><th class="copedent-row-label is-tab-label" colspan="2">Tab label</th>${renderTabLabelHeaders(groups)}</tr>
          <tr><th class="copedent-sticky-string">String</th><th class="copedent-sticky-open">Open</th>${renderTravelHeaders(groups)}</tr>
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
    const locked = customEditingLocked();
    const readOnly = immutable || locked;
    [elements.name, elements.guitar, elements.notes, elements.addControl, elements.save]
      .forEach((element) => { if (element) element.disabled = readOnly; });
    elements.clone.hidden = !immutable;
    elements.clone.textContent = locked ? "Session Pass required" : "Copy and edit";
    elements.create.textContent = locked ? "Session Pass required" : "New custom setup";
    elements.duplicate.disabled = immutable || locked;
    elements.exportProfile.disabled = immutable;
    elements.remove.disabled = immutable;
    elements.addFromStarter.disabled = immutable || locked;
    elements.reset.disabled = readOnly;
    elements.activateEdited.textContent = immutable ? "Use this setup" : "Validate and use";
    const activeId = store.activeProfile().id;
    elements.activate.textContent = activeId === selectedId ? "Active" : (!immutable && locked ? "Session Pass required" : "Use selected setup");
    elements.activate.disabled = activeId === selectedId;
    elements.activateEdited.disabled = Boolean(!immutable && locked);
  }

  function renderSelected(message = "") {
    const libraryProfile = store.profileById(selectedId) || store.activeProfile();
    selectedId = libraryProfile.id;
    currentProfile = editableProfile(libraryProfile);
    hasUnsavedChanges = false;
    refreshLibrary();
    elements.name.value = currentProfile.name || currentProfile.label || "";
    elements.family.value = "E9";
    elements.stringCount.value = "10";
    elements.guitar.value = currentProfile.guitar || "";
    elements.notes.value = currentProfile.notes || "";
    elements.workbenchTitle.textContent = profileName(currentProfile);
    elements.workbenchMeta.textContent = `${currentProfile.id === store.activeProfile().id ? "Current setup" : "Selected setup"} · Revision ${Number(currentProfile.revision || 1)}`;
    elements.activeBadge.textContent = validationLabel(currentProfile);
    elements.activeBadge.classList.toggle("is-active", validationLabel(currentProfile) === "Validated");
    const originId = String(currentProfile.origin || "").replace(/^clone:/, "");
    elements.template.value = catalog.has(currentProfile.id) ? currentProfile.id : (catalog.has(originId) ? originId : "emmons-e9-basic");
    const issues = currentProfile.reviewIssues || [];
    elements.reviewIssues.innerHTML = issues.length
      ? `<strong>Review required.</strong><ul>${issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}</ul>`
      : currentProfile.immutable
        ? "This starter is read-only. Its chart includes RKL and RKR. Choose Copy and edit to match your guitar."
        : `${accountState().enabled ? "Saved to your account" : "Saved locally"} · revision ${Number(currentProfile.revision || 1)} · ${escapeHtml(currentProfile.validationStatus || "draft")}`;
    renderGrid();
    setEditorState();
    elements.status.textContent = message || (issues[0]
      ? issues[0]
      : currentProfile.immutable
        ? "Read-only starter. Copy it before changing a cell or heading."
        : currentProfile.validationStatus === "valid"
          ? "Validated setup. Any edit returns it to draft until you validate again."
          : "Draft setup. Save it now or validate it when the chart matches your guitar.");
    showEditNotice(!currentProfile.immutable && currentProfile.validationStatus === "draft" ? "saved" : "none");
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
      if (customEditingLocked()) {
        showSubscription();
        return false;
      }
      currentProfile = await store.saveManagedProfile(profileFromEditor());
      selectedId = currentProfile.id;
      renderSelected(`${accountState().enabled ? "Draft synchronized to your account" : "Draft saved locally"}. Validate it before using it throughout the app.`);
      return true;
    } catch (error) {
      elements.status.textContent = error.message;
      setUnsavedChanges(true);
      return false;
    }
  }

  async function validateAndActivate() {
    const wasUnsaved = hasUnsavedChanges;
    try {
      if (currentProfile.immutable) {
        await store.activateProfile(currentProfile.id);
      } else {
        if (customEditingLocked()) return showSubscription();
        const candidate = profileFromEditor();
        elements.status.textContent = "Validating every open pitch, cell, and control state…";
        await validateProfile(candidate);
        candidate.validationStatus = "valid";
        candidate.reviewIssues = [];
        currentProfile = await store.saveManagedProfile(candidate);
        await store.activateProfile(currentProfile.id);
      }
      selectedId = currentProfile.id;
      selectionWasExplicit = false;
      renderSelected(`Using ${currentProfile.name || currentProfile.label} throughout the app.`);
      return true;
    } catch (error) {
      elements.status.textContent = error.message;
      if (wasUnsaved && !currentProfile?.immutable) setUnsavedChanges(true);
      return false;
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

  async function cloneSelected() {
    try {
      if (customEditingLocked()) return showSubscription();
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
      copy = await store.saveManagedProfile(copy);
      selectedId = copy.id;
      selectionWasExplicit = true;
      renderSelected("Editable copy created. Change the chart, then validate it when it matches your guitar.");
      elements.more.open = false;
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  async function createCustom() {
    try {
      if (customEditingLocked()) return showSubscription();
      const profile = await store.saveManagedProfile(store.blankProfile());
      selectedId = profile.id;
      selectionWasExplicit = true;
      renderSelected("Blank 10-string E9 setup created. Add the controls that are actually on this guitar.");
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  async function deleteCustom() {
    try {
      if (currentProfile.immutable) return;
      if (!global.confirm(`Delete ${currentProfile.name}? This removes this account-synced custom setup but does not delete any browser-local import copy.`)) return;
      await store.deleteManagedProfile(currentProfile.id);
      selectedId = store.activeProfile().id;
      selectionWasExplicit = false;
      renderSelected("Custom setup deleted. Your other setups were not changed.");
      elements.more.open = false;
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function addControlState() {
    if (currentProfile.immutable || customEditingLocked()) return;
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
    if (currentProfile.immutable || customEditingLocked()) return;
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
      elements.controlReset, elements.controlApply]
      .forEach((element) => { element.disabled = disabled; });
  }

  function resetControlFields() {
    const control = controlById();
    if (!control) return;
    elements.controlLabel.value = control.label || "";
    elements.controlPosition.value = control.physicalPosition || "";
    elements.controlType.value = control.type || "lever";
    elements.controlTravel.value = control.travel || (control.type === "pedal" ? "pedal" : "full");
    elements.controlAliases.value = (control.aliases || []).join(", ");
  }

  function openControlDialog(controlId, trigger) {
    const control = controlById(controlId);
    if (!control) return;
    activeControlId = String(control.id);
    returnFocus = trigger;
    elements.controlTitle.textContent = `${control.physicalPosition || control.label} details`;
    resetControlFields();
    setControlDialogDisabled(Boolean(currentProfile.immutable || customEditingLocked()));
    elements.controlDialog.showModal();
  }

  function applyControlFields() {
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
    elements.controlDialog.close("applied");
    renderGrid();
    global.setTimeout(() => elements.grid.querySelector(`[data-control-id="${escapeSelector(control.id)}"]`)?.focus(), 0);
    return control;
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
      .forEach((element) => { element.disabled = Boolean(currentProfile.immutable || customEditingLocked()); });
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
    if (!hasUnsavedChanges) renderSelected();
  }

  async function importSelectedLocalProfiles() {
    const account = accountState();
    if (!account.canManageCustom) return showSubscription("Your browser-local setups are still preserved. Session Pass is required to import them into your account; checkout is not available in this beta yet.");
    const localProfiles = store.localProfilesForImport?.() || [];
    const selected = new Set(Array.from(elements.localImportList.querySelectorAll('input[type="checkbox"]:checked')).map((input) => input.value));
    if (!selected.size) {
      elements.importStatus.textContent = "Choose at least one browser-local setup to import.";
      return;
    }
    elements.importSelected.disabled = true;
    try {
      let imported = null;
      for (const profile of localProfiles.filter((item) => selected.has(item.id) && !item.alreadyImported)) {
        imported = await store.importLocalProfile(profile);
      }
      if (imported) {
        selectedId = imported.id;
        selectionWasExplicit = true;
      }
      renderSelected(`${selected.size} browser-local setup${selected.size === 1 ? "" : "s"} imported. The original local copy was kept.`);
    } catch (error) {
      elements.importStatus.textContent = error.message;
    } finally {
      elements.importSelected.disabled = false;
    }
  }

  function selectProfile(profileId, { explicit = true, message = "" } = {}) {
    const profile = store.profileById(profileId);
    if (!profile) return false;
    selectedId = profile.id;
    selectionWasExplicit = explicit;
    renderSelected(message);
    return true;
  }

  async function editActiveSetup() {
    const active = store.activeProfile();
    if (!selectProfile(active.id, { explicit: true })) return;
    if (active.immutable) {
      await cloneSelected();
    } else {
      doc.querySelector(".setup-workbench-stage")?.scrollIntoView?.({ behavior: "smooth", block: "start" });
      global.setTimeout(() => elements.grid.querySelector("button:not(:disabled)")?.focus(), 0);
    }
  }

  async function duplicateActiveSetup() {
    const active = store.activeProfile();
    if (!selectProfile(active.id, { explicit: true })) return;
    await cloneSelected();
  }

  function exportActiveSetup() {
    const active = store.activeProfile();
    if (active?.immutable) return;
    exportLocalProfile(active);
    elements.status.textContent = `${profileName(active)} exported. No account data was deleted.`;
  }

  elements.library.addEventListener("change", async () => {
    const nextId = elements.library.value;
    if (!await requestExit()) {
      elements.library.value = selectedId;
      return;
    }
    selectedId = nextId;
    selectionWasExplicit = true;
    renderSelected();
  });
  elements.activate.addEventListener("click", validateAndActivate);
  elements.activateEdited.addEventListener("click", validateAndActivate);
  elements.clone.addEventListener("click", () => runAfterSafeExit(cloneSelected));
  elements.duplicate.addEventListener("click", () => runAfterSafeExit(cloneSelected));
  elements.exportProfile.addEventListener("click", () => {
    if (!currentProfile?.immutable) {
      exportLocalProfile(currentProfile);
      elements.status.textContent = `${currentProfile.name} exported. No account data was deleted.`;
    }
    elements.more.open = false;
  });
  elements.create.addEventListener("click", () => runAfterSafeExit(createCustom));
  elements.remove.addEventListener("click", () => runAfterSafeExit(deleteCustom));
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
  elements.controlApply.addEventListener("click", applyControlFields);
  elements.controlReset.addEventListener("click", resetControlFields);
  elements.stringApply.addEventListener("click", applyStringDetails);
  elements.importSelected?.addEventListener("click", () => runAfterSafeExit(importSelectedLocalProfiles));
  elements.libraryGroups?.addEventListener("click", async (event) => {
    const entry = event.target.closest("[data-setup-profile]");
    if (!entry || !await requestExit()) return;
    selectProfile(entry.dataset.setupProfile, { explicit: true, message: `${entry.querySelector(".setup-library-entry-name")?.textContent || "Setup"} selected for review.` });
  });
  elements.editActive?.addEventListener("click", () => runAfterSafeExit(editActiveSetup));
  elements.duplicateActive?.addEventListener("click", () => runAfterSafeExit(duplicateActiveSetup));
  elements.exportActive?.addEventListener("click", exportActiveSetup);
  elements.localImportList?.addEventListener("click", (event) => {
    const exportButton = event.target.closest("[data-export-local]");
    const deleteButton = event.target.closest("[data-delete-local]");
    const profileId = exportButton?.dataset.exportLocal || deleteButton?.dataset.deleteLocal;
    if (!profileId) return;
    const profile = store.localProfilesForImport().find((item) => item.id === profileId);
    if (!profile) return;
    if (exportButton) {
      exportLocalProfile(profile);
      elements.importStatus.textContent = `${profile.name} exported from this browser.`;
      return;
    }
    if (global.confirm(`Delete the browser-local copy of ${profile.name}? This does not delete an imported account copy.`)) {
      store.deleteProfile(profile.id);
      renderAccountStatus();
      elements.importStatus.textContent = `${profile.name} removed from this browser.`;
    }
  });
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

  elements.unsavedKeep.addEventListener("click", () => finishPendingExit(false));
  elements.unsavedDiscard.addEventListener("click", () => {
    renderSelected("Unsaved chart edits discarded.");
    finishPendingExit(true);
  });
  elements.unsavedSave.addEventListener("click", async () => {
    elements.unsavedSave.disabled = true;
    elements.unsavedKeep.disabled = true;
    elements.unsavedDiscard.disabled = true;
    const saved = await saveDraft();
    elements.unsavedSave.disabled = false;
    elements.unsavedKeep.disabled = false;
    elements.unsavedDiscard.disabled = false;
    if (saved) finishPendingExit(true);
  });
  elements.unsavedDialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    finishPendingExit(false);
  });

  global.addEventListener("beforeunload", (event) => {
    if (!hasUnsavedChanges) return;
    event.preventDefault();
    event.returnValue = "";
  });

  global.STEEL_RAG_BACKSTAGE_COPEDENT_GUARD = Object.freeze({
    hasUnsavedChanges: () => hasUnsavedChanges,
    requestExit
  });

  refreshLibrary();
  renderSelected();
  loadCatalog();
  function syncSelectedProfile() {
    if (hasUnsavedChanges) return;
    const activeId = store.activeProfile().id;
    if (!selectionWasExplicit || !store.profileById(selectedId)) selectedId = activeId;
    renderSelected();
  }
  store.subscribe(syncSelectedProfile);
  syncSelectedProfile();
})(globalThis);
