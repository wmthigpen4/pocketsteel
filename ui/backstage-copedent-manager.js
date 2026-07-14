(function (global) {
  "use strict";

  const store = global.STEEL_RAG_COPEDENTS;
  const answerUi = typeof STEEL_RAG_ANSWER_UI !== "undefined" ? STEEL_RAG_ANSWER_UI : global.STEEL_RAG_ANSWER_UI;
  if (!store || !global.document) return;
  const doc = global.document;
  const $ = (selector) => doc.querySelector(selector);

  function replaceNode(selector) {
    const current = $(selector);
    if (!current) return null;
    const replacement = current.cloneNode(true);
    current.replaceWith(replacement);
    return replacement;
  }

  const elements = {
    library: $("#copedent-profile-library"),
    activeBadge: $("#copedent-active-badge"),
    libraryActive: $("#copedent-library-active"),
    reviewIssues: $("#copedent-review-issues"),
    name: $("#copedent-name"),
    family: $("#copedent-family"),
    stringCount: replaceNode("#copedent-string-count"),
    customCount: replaceNode("#copedent-custom-count"),
    guitar: $("#copedent-guitar"),
    pedalOrder: $("#copedent-pedal-order"),
    notes: $("#copedent-notes"),
    template: replaceNode("#copedent-template"),
    strings: $("#copedent-strings"),
    changes: replaceNode("#copedent-changes"),
    addControl: replaceNode("#add-copedent-change"),
    save: replaceNode("#save-copedent"),
    reset: replaceNode("#reset-copedent"),
    activateEdited: $("#activate-edited-copedent"),
    compare: $("#compare-copedent"),
    addFromStarter: $("#add-copedent-from-starter"),
    activate: $("#activate-copedent"),
    clone: $("#clone-copedent"),
    create: $("#new-copedent"),
    duplicate: $("#duplicate-copedent"),
    remove: $("#delete-copedent"),
    status: $("#copedent-save-status"),
    overview: $("#copedent-overview-summary"),
    overviewUpdated: $("#copedent-overview-updated")
  };

  const STANDARD_STRINGS = [
    [1, "F#", 66], [2, "D#", 63], [3, "G#", 68], [4, "E", 64], [5, "B", 59],
    [6, "G#", 56], [7, "F#", 54], [8, "E", 52], [9, "D", 50], [10, "B", 47]
  ];
  const PITCH_CLASSES = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };

  function changeDirection(from, to) {
    const fromValue = PITCH_CLASSES[String(from || "").split("/", 1)[0]];
    const toValue = PITCH_CLASSES[String(to || "").split("/", 1)[0]];
    if (!Number.isInteger(fromValue) || !Number.isInteger(toValue)) return "raise";
    const delta = ((toValue - fromValue + 6) % 12) - 6;
    return delta < 0 ? "lower" : "raise";
  }

  function fallbackProfile(id, day = false) {
    const pedalPosition = day ? { A: "P3", B: "P2", C: "P1" } : { A: "P1", B: "P2", C: "P3" };
    const control = (controlId, label, type, physical, travel, changes) => ({
      id: controlId, label, control_type: type, physical_position: physical, travel,
      player_shorthand: [], compatibility_aliases: [physical],
      changes: changes.map(([string, from, to]) => ({ string, from, to, direction: changeDirection(from, to) }))
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
      notes: "Starter profile. Knee locations vary; clone and edit the exact mechanics on your guitar."
    };
  }

  let catalog = new Map([
    ["emmons-e9-basic", fallbackProfile("emmons-e9-basic", false)],
    ["day-e9-basic", fallbackProfile("day-e9-basic", true)]
  ]);
  let selectedId = store.loadState().activeProfileId;
  let currentProfile = null;

  function escapeHtml(value) {
    return String(value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function option(value, label, selected) {
    return `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }

  function editableProfile(profile) {
    if (!profile?.immutable) return store.normalizeProfile(profile);
    const payload = catalog.get(profile.id) || fallbackProfile(profile.id, profile.id === "day-e9-basic");
    const editable = store.editableFromBuiltIn(payload, payload.label);
    return { ...editable, id: profile.id, name: payload.label, label: payload.label, immutable: true, origin: "built_in", validationStatus: "valid" };
  }

  function refreshLibrary() {
    const state = store.loadState();
    const profiles = store.listProfiles();
    const common = profiles.filter((profile) => profile.immutable);
    const custom = profiles.filter((profile) => !profile.immutable);
    elements.library.innerHTML = [
      `<optgroup label="Common setups">${common.map((profile) => option(profile.id, `${profile.label}${state.activeProfileId === profile.id ? " · Active" : ""}`, selectedId)).join("")}</optgroup>`,
      `<optgroup label="My custom setups">${custom.length ? custom.map((profile) => option(profile.id, `${profile.name}${state.activeProfileId === profile.id ? " · Active" : ""}`, selectedId)).join("") : '<option value="" disabled>No custom profiles yet</option>'}</optgroup>`
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

  function renderStrings(profile) {
    const strings = profile.strings?.length ? profile.strings : store.blankProfile().strings;
    elements.strings.innerHTML = strings.map((item, index) => `
      <tr>
        <td><input data-field="stringNumber" type="number" min="1" max="10" value="${Number(item.stringNumber || index + 1)}"></td>
        <td><input data-field="openNote" type="text" value="${escapeHtml(item.openNote)}" placeholder="E"></td>
        <td><input data-field="openPitchValue" type="number" min="24" max="96" value="${Number(item.openPitchValue || 0)}" aria-label="Open pitch MIDI value"></td>
        <td><input data-field="gauge" type="text" value="${escapeHtml(item.gauge)}" placeholder=".011"></td>
        <td><input data-field="notes" type="text" value="${escapeHtml(item.notes)}" placeholder="Optional"></td>
      </tr>
    `).join("");
  }

  function renderChanges(profile) {
    const rows = [];
    (profile.controls || []).forEach((control) => {
      (control.changes || []).forEach((change, actionIndex) => rows.push({ control, change, actionIndex }));
    });
    elements.changes.innerHTML = rows.map(({ control, change, actionIndex }) => `
      <tr data-control-id="${escapeHtml(control.id)}" data-action-index="${actionIndex}">
        <td><input data-field="controlLabel" type="text" value="${escapeHtml(control.label)}" placeholder="RKL"></td>
        <td><select data-field="controlType"><option value="pedal"${control.type === "pedal" ? " selected" : ""}>Pedal</option><option value="lever"${control.type !== "pedal" ? " selected" : ""}>Lever</option></select></td>
        <td><input data-field="physicalPosition" type="text" value="${escapeHtml(control.physicalPosition)}" placeholder="RKL"></td>
        <td><select data-field="travel">${["pedal", "half-stop", "full", "full-stop", "vertical", "split"].map((value) => option(value, value, control.travel)).join("")}</select></td>
        <td><input data-field="stringNumber" type="number" min="1" max="10" value="${Number(change.stringNumber || 0) || ""}"></td>
        <td><input data-field="fromNote" type="text" value="${escapeHtml(change.fromNote)}" placeholder="G#"></td>
        <td><input data-field="toNote" type="text" value="${escapeHtml(change.toNote)}" placeholder="F#"></td>
        <td><select data-field="changeType">${["raise", "lower", "half-stop", "split"].map((value) => option(value, value, change.changeType)).join("")}</select></td>
        <td><input data-field="notes" type="text" value="${escapeHtml(change.notes)}" placeholder="Optional"></td>
        <td><button class="copedent-row-action" type="button" data-add-action aria-label="Add another string action">+</button><button class="copedent-row-action" type="button" data-remove-action aria-label="Remove string action">×</button></td>
      </tr>
    `).join("");
  }

  function setEditorDisabled(disabled) {
    [elements.name, elements.family, elements.stringCount, elements.guitar, elements.pedalOrder, elements.notes, elements.addControl, elements.save, elements.activateEdited, elements.addFromStarter]
      .filter(Boolean).forEach((element) => { element.disabled = disabled; });
    elements.strings.querySelectorAll("input, select").forEach((element) => { element.disabled = disabled; });
    elements.changes.querySelectorAll("input, select, button").forEach((element) => { element.disabled = disabled; });
    elements.clone.disabled = false;
    elements.duplicate.disabled = Boolean(currentProfile?.immutable);
    elements.remove.disabled = Boolean(currentProfile?.immutable);
  }

  function renderSelected() {
    const libraryProfile = store.profileById(selectedId) || store.activeProfile();
    selectedId = libraryProfile.id;
    currentProfile = editableProfile(libraryProfile);
    refreshLibrary();
    elements.name.value = currentProfile.name || currentProfile.label || "";
    elements.family.value = "E9";
    elements.stringCount.value = "10";
    elements.customCount.value = "10";
    elements.guitar.value = currentProfile.guitar || "";
    elements.pedalOrder.value = (currentProfile.pedalOrder || []).join(", ");
    elements.notes.value = currentProfile.notes || "";
    const originId = String(currentProfile.origin || "").replace(/^clone:/, "");
    elements.template.value = catalog.has(currentProfile.id) ? currentProfile.id : (catalog.has(originId) ? originId : "emmons-e9-basic");
    renderStrings(currentProfile);
    renderChanges(currentProfile);
    const issues = currentProfile.reviewIssues || [];
    elements.reviewIssues.innerHTML = issues.length
      ? `<strong>Review required.</strong><ul>${issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}</ul>`
      : currentProfile.immutable
        ? "This common profile is read-only. Its chart includes RKL and RKR; clone it to match your guitar exactly."
        : `Saved locally · revision ${Number(currentProfile.revision || 1)} · ${escapeHtml(currentProfile.validationStatus || "draft")}`;
    elements.status.textContent = "";
    setEditorDisabled(Boolean(currentProfile.immutable));
    elements.activate.textContent = store.loadState().activeProfileId === selectedId ? "Active" : "Make active";
    elements.activate.disabled = store.loadState().activeProfileId === selectedId;
  }

  function collectProfile() {
    if (currentProfile?.immutable) throw new Error("Clone this starter before editing it.");
    const strings = Array.from(elements.strings.querySelectorAll("tr")).map((row, index) => ({
      stringNumber: Number(row.querySelector('[data-field="stringNumber"]').value || index + 1),
      openNote: row.querySelector('[data-field="openNote"]').value.trim(),
      openPitchValue: Number(row.querySelector('[data-field="openPitchValue"]').value || 0),
      gauge: row.querySelector('[data-field="gauge"]').value.trim(),
      notes: row.querySelector('[data-field="notes"]').value.trim()
    }));
    const controls = new Map();
    Array.from(elements.changes.querySelectorAll("tr")).forEach((row) => {
      const id = row.dataset.controlId;
      if (!controls.has(id)) {
        controls.set(id, {
          id,
          label: row.querySelector('[data-field="controlLabel"]').value.trim() || "Unnamed control",
          type: row.querySelector('[data-field="controlType"]').value,
          physicalPosition: row.querySelector('[data-field="physicalPosition"]').value.trim(),
          travel: row.querySelector('[data-field="travel"]').value,
          aliases: currentProfile.controls?.find((control) => control.id === id)?.aliases || [],
          notes: currentProfile.controls?.find((control) => control.id === id)?.notes || "",
          changes: []
        });
      }
      controls.get(id).changes.push({
        stringNumber: Number(row.querySelector('[data-field="stringNumber"]').value || 0),
        fromNote: row.querySelector('[data-field="fromNote"]').value.trim(),
        toNote: row.querySelector('[data-field="toNote"]').value.trim(),
        changeType: row.querySelector('[data-field="changeType"]').value,
        notes: row.querySelector('[data-field="notes"]').value.trim()
      });
    });
    return store.normalizeProfile({
      ...currentProfile,
      name: elements.name.value.trim() || "My E9 setup",
      label: elements.name.value.trim() || "My E9 setup",
      guitar: elements.guitar.value.trim(),
      pedalOrder: elements.pedalOrder.value.split(",").map((value) => value.trim()).filter(Boolean),
      strings,
      controls: Array.from(controls.values()),
      notes: elements.notes.value.trim(),
      validationStatus: currentProfile.validationStatus === "needs_review" ? "needs_review" : "draft"
    });
  }

  function accessHeaders() {
    const queryRole = new URLSearchParams(global.location.search).get("access");
    let storedRole = "";
    try { storedRole = global.localStorage.getItem("steel-guitar-rag.mockAccessState.v1") || ""; } catch (_error) { storedRole = ""; }
    return { "Content-Type": "application/json", ...(answerUi?.devAccessHeaders?.(queryRole || storedRole) || {}) };
  }

  async function validateProfile(profile) {
    const response = await global.fetch("/api/copedents/validate", {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: accessHeaders(), body: JSON.stringify({ profile })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.valid) throw new Error(payload.error || "This profile did not pass mechanical validation.");
    return payload;
  }

  async function saveDraft() {
    try {
      currentProfile = store.saveProfile(collectProfile());
      selectedId = currentProfile.id;
      refreshLibrary();
      renderSelected();
      elements.status.textContent = "Draft saved locally. Validate it before making it active.";
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  async function validateAndActivate() {
    try {
      if (currentProfile.immutable) {
        store.setActive(currentProfile.id);
      } else {
        currentProfile = store.saveProfile(collectProfile());
        elements.status.textContent = "Validating every string and control state…";
        await validateProfile(currentProfile);
        currentProfile = store.markValidated(currentProfile.id);
        store.setActive(currentProfile.id);
      }
      selectedId = currentProfile.id;
      refreshLibrary();
      renderSelected();
      elements.status.textContent = `Using ${currentProfile.name || currentProfile.label} throughout the app.`;
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function effectSignature(control) {
    return (control.changes || []).map((change) => `${change.stringNumber}:${change.fromNote}>${change.toNote}`).sort().join("|");
  }

  function missingStarterControls(profile) {
    const starter = store.editableFromBuiltIn(catalog.get(elements.template.value), "comparison");
    const existing = new Set((profile.controls || []).map(effectSignature));
    return (starter.controls || []).filter((control) => !existing.has(effectSignature(control)));
  }

  function compareWithStarter() {
    try {
      const profile = currentProfile.immutable ? currentProfile : collectProfile();
      const missing = missingStarterControls(profile);
      elements.status.textContent = missing.length
        ? `Compared mechanically with ${catalog.get(elements.template.value).label}: missing ${missing.map((control) => `${control.label} (${control.physicalPosition})`).join(", ")}. Nothing was added.`
        : `Every starter mechanical effect is represented. Your labels and physical positions may still differ.`;
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function addMissingFromStarter() {
    try {
      const profile = collectProfile();
      const missing = missingStarterControls(profile);
      if (!missing.length) {
        elements.status.textContent = "No starter states are missing.";
        return;
      }
      profile.controls.push(...missing.map(store.clone));
      profile.validationStatus = "draft";
      currentProfile = store.saveProfile(profile);
      renderSelected();
      elements.status.textContent = `Added ${missing.length} explicitly selected starter state${missing.length === 1 ? "" : "s"}. Review before activating.`;
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function addControlState() {
    try {
      const profile = collectProfile();
      const control = {
        id: `control-${Date.now()}`, label: "", type: "lever", physicalPosition: "", travel: "full", aliases: [], notes: "",
        changes: [{ stringNumber: 0, fromNote: "", toNote: "", changeType: "raise", notes: "" }]
      };
      profile.controls.push(control);
      currentProfile = profile;
      renderChanges(currentProfile);
      setEditorDisabled(false);
      elements.status.textContent = "New control state added. Save when its mechanics are complete.";
    } catch (error) {
      elements.status.textContent = error.message;
    }
  }

  function addAction(row) {
    const profile = collectProfile();
    const control = profile.controls.find((item) => item.id === row.dataset.controlId);
    control.changes.splice(Number(row.dataset.actionIndex) + 1, 0, { stringNumber: 0, fromNote: "", toNote: "", changeType: "raise", notes: "" });
    currentProfile = profile;
    renderChanges(currentProfile);
  }

  function removeAction(row) {
    const profile = collectProfile();
    const control = profile.controls.find((item) => item.id === row.dataset.controlId);
    control.changes.splice(Number(row.dataset.actionIndex), 1);
    if (!control.changes.length) profile.controls = profile.controls.filter((item) => item.id !== control.id);
    currentProfile = profile;
    renderChanges(currentProfile);
  }

  function cloneSelected() {
    const source = store.profileById(selectedId);
    let copy;
    if (source.immutable) {
      copy = store.editableFromBuiltIn(catalog.get(source.id), `${source.label.replace(/ starter$/i, "")} custom`);
    } else {
      const blank = store.blankProfile(`${source.name} copy`);
      copy = store.normalizeProfile({ ...store.clone(source), id: blank.id, name: blank.name, label: blank.name, origin: `clone:${source.id}`, revision: 1, validationStatus: "draft" });
    }
    copy = store.saveProfile(copy);
    selectedId = copy.id;
    renderSelected();
    elements.status.textContent = "Editable copy created. Validate it after making changes.";
  }

  async function loadCatalog() {
    try {
      const response = await global.fetch("/api/copedents/e9", { credentials: "same-origin", cache: "no-store", headers: accessHeaders() });
      const payload = await response.json().catch(() => ({}));
      if (response.ok && Array.isArray(payload.profiles)) catalog = new Map(payload.profiles.map((profile) => [profile.id, profile]));
    } catch (_error) {
      elements.status.textContent = "Using the built-in offline profile definitions; live validation still requires a connection.";
    }
    renderSelected();
  }

  elements.library.addEventListener("change", () => { selectedId = elements.library.value; renderSelected(); });
  elements.activate.addEventListener("click", validateAndActivate);
  elements.activateEdited.addEventListener("click", validateAndActivate);
  elements.clone.addEventListener("click", cloneSelected);
  elements.duplicate.addEventListener("click", cloneSelected);
  elements.create.addEventListener("click", () => {
    const profile = store.saveProfile(store.blankProfile());
    selectedId = profile.id;
    renderSelected();
  });
  elements.remove.addEventListener("click", () => {
    if (currentProfile.immutable) return;
    if (!global.confirm(`Delete ${currentProfile.name}? This removes only the local custom copy.`)) return;
    store.deleteProfile(currentProfile.id);
    selectedId = store.loadState().activeProfileId;
    renderSelected();
  });
  elements.save.addEventListener("click", saveDraft);
  elements.reset.addEventListener("click", renderSelected);
  elements.compare.addEventListener("click", compareWithStarter);
  elements.addFromStarter.addEventListener("click", addMissingFromStarter);
  elements.addControl.addEventListener("click", addControlState);
  elements.changes.addEventListener("click", (event) => {
    const row = event.target.closest("tr");
    if (!row) return;
    if (event.target.closest("[data-add-action]")) addAction(row);
    if (event.target.closest("[data-remove-action]")) removeAction(row);
  });

  refreshLibrary();
  renderSelected();
  loadCatalog();
  store.subscribe(() => refreshLibrary());
})(globalThis);
