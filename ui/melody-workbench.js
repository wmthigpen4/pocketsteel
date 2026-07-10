(function (global) {
  "use strict";

  const MAX_EVENTS_PER_SECTION = 8;
  const TASKS = {
    artist_solo_lesson: {
      title: "Learn an artist’s solo",
      shortTitle: "Artist solo",
      question: "Teach this artist solo as an E9 lesson.",
      renderingMode: "transcription",
      needsMaterial: true
    },
    song_arrangement_lesson: {
      title: "Build a song arrangement",
      shortTitle: "Song arrangement",
      question: "Build this song section as an E9 teaching arrangement.",
      renderingMode: "e9_adaptation",
      needsMaterial: true
    },
    user_melody: {
      title: "Map my own melody",
      shortTitle: "My melody",
      question: "Map my melody into a playable E9 lesson.",
      renderingMode: "e9_adaptation",
      needsMaterial: false
    },
    original_exercise: {
      title: "Make a practice phrase",
      shortTitle: "Practice phrase",
      question: "Build an original E9 practice phrase.",
      renderingMode: "teaching_simplification",
      needsMaterial: false
    }
  };
  const KEY_NOTES = {
    G: ["G", "A", "B", "C", "D", "E", "F#"],
    C: ["C", "D", "E", "F", "G", "A", "B"]
  };
  const E9_OPEN_NOTES = {
    1: "F#", 2: "D#", 3: "G#", 4: "E", 5: "B",
    6: "G#", 7: "F#", 8: "E", 9: "D", 10: "B"
  };
  const E9_OPEN_PITCHES = { 1: 66, 2: 63, 3: 68, 4: 64, 5: 59, 6: 56, 7: 54, 8: 52, 9: 50, 10: 47 };
  const E9_CHANGE_DELTAS = {
    A: { 5: 2, 10: 2 }, B: { 3: 1, 6: 1 }, C: { 4: 2, 5: 2 },
    E: { 4: -1, 8: -1 }, F: { 4: 1, 8: 1 }, V: { 5: -1, 10: -1 },
    G: { 1: 1, 6: -1 }, D: { 2: -2, 9: -1 }
  };
  const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const CHROMATIC_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const PRESETS = {
    "1-2-3-5": ["1", "2", "3", "5"],
    "1-3-5-3": ["1", "3", "5", "3"],
    "5-6-5-3": ["5", "6", "5", "3"]
  };

  function normalizeToken(value) {
    const raw = String(value || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
    if (/^[1-7]$/.test(raw)) return raw;
    const match = raw.match(/^([A-Ga-g])([#b]?)$/);
    return match ? `${match[1].toUpperCase()}${match[2]}` : raw;
  }

  function semitoneForNote(note) {
    const normalized = normalizeToken(note);
    const flats = { Db: "C#", Eb: "D#", Gb: "F#", Ab: "G#", Bb: "A#" };
    return CHROMATIC_SHARPS.indexOf(flats[normalized] || normalized);
  }

  function noteAtFret(stringNumber, fret) {
    const openNote = E9_OPEN_NOTES[Number(stringNumber)];
    const openSemitone = semitoneForNote(openNote);
    if (!openNote || openSemitone < 0 || !Number.isInteger(Number(fret)) || Number(fret) < 0 || Number(fret) > 24) {
      return "";
    }
    return CHROMATIC_SHARPS[(openSemitone + Number(fret)) % 12];
  }

  function parseSimpleTab(value) {
    const match = String(value || "").match(/(?:^|\n)\s*(?:S|string\s*)\s*(\d{1,2})\s*:\s*([^\n]+)/i);
    if (!match) return [];
    return (match[2].match(/\d{1,2}/g) || [])
      .map((fret) => noteAtFret(Number(match[1]), Number(fret)))
      .filter(Boolean);
  }

  function parseSimpleTabEvents(value) {
    const compact = Array.from(String(value || "").matchAll(/S(\d{1,2}):(\d{1,2})([A-Za-z](?:\+[A-Za-z])*)?/gi));
    if (compact.length) {
      return compact.map((match) => ({
        token: match[0].toUpperCase(),
        string: Number(match[1]),
        fret: Number(match[2]),
        changes: match[3] ? match[3].split("+").filter(Boolean).map((item) => item.toUpperCase()) : [],
        direction: "auto",
        octaveShift: 0
      }));
    }
    const match = String(value || "").match(/(?:^|\n)\s*(?:S|string\s*)\s*(\d{1,2})\s*:\s*([^\n]+)/i);
    if (!match) return [];
    const string = Number(match[1]);
    return (match[2].match(/\d{1,2}(?:[A-Za-z](?:\+[A-Za-z])*)?/g) || []).map((entry) => {
      const tokenMatch = entry.match(/^(\d{1,2})(.*)$/);
      const fret = Number(tokenMatch[1]);
      const changes = tokenMatch[2] ? tokenMatch[2].split("+").filter(Boolean).map((item) => item.toUpperCase()) : [];
      return { token: `S${string}:${fret}${changes.join("+")}`, string, fret, changes, direction: "auto", octaveShift: 0 };
    });
  }

  function phraseItem(value) {
    if (value && typeof value === "object") return { direction: "auto", octaveShift: 0, ...value };
    return { token: normalizeToken(value), direction: "auto", octaveShift: 0 };
  }

  function phraseItemLabel(value) {
    const item = phraseItem(value);
    return String(item.token || (item.string ? `S${item.string}:${item.fret}` : ""));
  }

  function parsePhraseEvents(value) {
    const literal = parseSimpleTabEvents(value);
    if (literal.length) return literal;
    return parsePhraseInput(value).map(phraseItem);
  }

  function pitchLabel(value) {
    return `${NOTE_NAMES[((value % 12) + 12) % 12]}${Math.floor(value / 12) - 1}`;
  }

  function resolvePhrasePreview(items, key, contourMode = "closest_playable") {
    const notes = KEY_NOTES[key] || [];
    const anchor = 67;
    const result = [];
    let previousBase = null;
    (items || []).forEach((raw) => {
      const item = phraseItem(raw);
      let basePitch;
      if (Number.isInteger(item.string) && Number.isInteger(item.fret)) {
        const changeDelta = (item.changes || []).reduce((sum, change) => sum + (E9_CHANGE_DELTAS[String(change).toUpperCase()]?.[item.string] || 0), 0);
        basePitch = (E9_OPEN_PITCHES[item.string] ?? 64) + item.fret + changeDelta;
      } else {
        const token = normalizeToken(item.token);
        const note = /^[1-7]$/.test(token) ? notes[Number(token) - 1] : token;
        const pitchClass = semitoneForNote(note);
        const options = Array.from({ length: 48 }, (_, offset) => 47 + offset).filter((value) => value % 12 === pitchClass);
        if (previousBase === null) basePitch = options.sort((a, b) => Math.abs(a - anchor) - Math.abs(b - anchor) || a - b)[0];
        else {
          const direction = item.direction !== "auto" ? item.direction : contourMode === "ascending" ? "up" : contourMode === "descending" ? "down" : "nearest";
          const directed = options.filter((value) => direction === "up" ? value >= previousBase : direction === "down" ? value <= previousBase : true);
          basePitch = (directed.length ? directed : options).sort((a, b) => Math.abs(a - previousBase) - Math.abs(b - previousBase) || a - b)[0];
        }
      }
      const pitch = basePitch + (Number.isInteger(item.string) ? 0 : Number(item.octaveShift || 0) * 12);
      result.push({ ...item, pitchValue: pitch, pitch: pitchLabel(pitch) });
      previousBase = basePitch;
    });
    return result;
  }

  function parsePhraseInput(value) {
    const tabNotes = parseSimpleTab(value);
    if (tabNotes.length) return tabNotes;
    return String(value || "")
      .split(/[\s,|]+/)
      .map(normalizeToken)
      .filter(Boolean);
  }

  function sectionCount(tokens) {
    return Math.max(1, Math.ceil((tokens?.length || 0) / MAX_EVENTS_PER_SECTION));
  }

  function validateTokens(tokens, key) {
    const allowedNotes = new Set(KEY_NOTES[key] || []);
    const invalid = (tokens || []).filter((raw) => {
      const item = phraseItem(raw);
      if (Number.isInteger(item.string) && Number.isInteger(item.fret)) return item.string < 1 || item.string > 10 || item.fret < 0 || item.fret > 24;
      const token = normalizeToken(item.token);
      return !/^[1-7]$/.test(token) && !allowedNotes.has(token);
    });
    if (!tokens?.length) return { ok: false, message: "Add at least one note, scale degree, or simple tab position." };
    if (invalid.length) {
      return { ok: false, message: `${invalid.map(phraseItemLabel).join(", ")} ${invalid.length === 1 ? "is" : "are"} outside ${key} major or the supported E9 tab range.` };
    }
    return { ok: true, message: "" };
  }

  function reorderToken(tokens, index, direction) {
    const next = [...(tokens || [])];
    const target = index + direction;
    if (index < 0 || target < 0 || index >= next.length || target >= next.length) return next;
    [next[index], next[target]] = [next[target], next[index]];
    return next;
  }

  function buildMelodyRequest(state) {
    const task = TASKS[state.kind];
    const request = {
      kind: state.kind,
      key: state.key,
      tuning: "E9",
      renderingMode: task.renderingMode,
      sectionNumber: state.sectionNumber || 1,
      contourMode: state.contourMode || "closest_playable",
      texture: "both"
    };
    if (state.tokens?.length) request.melody = [...state.tokens];
    if (task.needsMaterial) {
      request.material = {
        artist: state.artist || "",
        song: state.song || "",
        recording: state.recording || "",
        section: state.section || `Section ${state.sectionNumber || 1}`,
        sourceUrl: state.sourceUrl || ""
      };
    }
    return request;
  }

  function createInitialState(kind = "") {
    return {
      kind: TASKS[kind] ? kind : "",
      key: "G",
      paletteMode: "degrees",
      tokens: [],
      contourMode: "closest_playable",
      selectedPhraseIndex: 0,
      artist: "",
      song: "",
      recording: "",
      section: "",
      sourceUrl: "",
      sectionNumber: 1,
      activeEventIndex: 0,
      response: null
    };
  }

  const api = {
    MAX_EVENTS_PER_SECTION,
    TASKS,
    KEY_NOTES,
    PRESETS,
    createInitialState,
    parsePhraseInput,
    parseSimpleTab,
    parseSimpleTabEvents,
    parsePhraseEvents,
    resolvePhrasePreview,
    noteAtFret,
    sectionCount,
    validateTokens,
    reorderToken,
    buildMelodyRequest
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  global.STEEL_RAG_MELODY_STUDIO = api;

  if (!global.document) return;

  const doc = global.document;
  const $ = (selector) => doc.querySelector(selector);
  const answerUi = typeof STEEL_RAG_ANSWER_UI !== "undefined"
    ? STEEL_RAG_ANSWER_UI
    : global.STEEL_RAG_ANSWER_UI;
  let state = createInitialState(new URLSearchParams(global.location.search).get("kind") || "");
  let session = null;

  const elements = {
    unavailable: $("#studio-unavailable"),
    workflow: $("#studio-workflow"),
    taskPanel: $("#studio-task-panel"),
    taskCards: Array.from(doc.querySelectorAll("[data-studio-task]")),
    editor: $("#studio-editor"),
    editorTitle: $("#studio-editor-title"),
    changeTask: $("#studio-change-task"),
    materialFields: $("#studio-material-fields"),
    artist: $("#studio-artist"),
    song: $("#studio-song"),
    recording: $("#studio-recording"),
    section: $("#studio-section"),
    sourceUrl: $("#studio-source-url"),
    key: $("#studio-key"),
    contour: $("#studio-contour"),
    phraseInput: $("#studio-phrase-input"),
    sequence: $("#studio-sequence"),
    noteEditor: $("#studio-note-editor"),
    selectedNote: $("#studio-selected-note"),
    selectedPitch: $("#studio-selected-pitch"),
    octaveDown: $("#studio-octave-down"),
    octaveAuto: $("#studio-octave-auto"),
    octaveUp: $("#studio-octave-up"),
    noteEarlier: $("#studio-note-earlier"),
    noteLater: $("#studio-note-later"),
    noteRemove: $("#studio-note-remove"),
    sectionCount: $("#studio-section-count"),
    palette: $("#studio-palette"),
    paletteModeButtons: Array.from(doc.querySelectorAll("[data-palette-mode]")),
    presetButtons: Array.from(doc.querySelectorAll("[data-preset]")),
    error: $("#studio-error"),
    build: $("#studio-build"),
    result: $("#studio-result"),
    resultTitle: $("#studio-result-title"),
    resultMeta: $("#studio-result-meta"),
    resultSource: $("#studio-result-source"),
    routeTabs: $("#studio-route-tabs"),
    moreRoutes: $("#studio-more-routes"),
    advancedRoutes: $("#studio-advanced-routes"),
    routeReason: $("#studio-route-reason"),
    sourceNeeded: $("#studio-source-needed"),
    fretboard: $("#studio-fretboard"),
    transport: $("#studio-transport"),
    previous: $("#studio-previous"),
    next: $("#studio-next"),
    eventStrip: $("#studio-event-strip"),
    eventDetail: $("#studio-event-detail"),
    tab: $("#studio-tab"),
    tabCode: $("#studio-tab-code"),
    activeTabStep: $("#studio-active-tab-step"),
    explanation: $("#studio-explanation"),
    continueButton: $("#studio-continue"),
    edit: $("#studio-edit"),
  };

  function currentTask() {
    return TASKS[state.kind] || null;
  }

  function readAccessRole() {
    return answerUi.normalizeAccessRole(new URLSearchParams(global.location.search).get("access"));
  }

  function clearMaterial() {
    state.artist = "";
    state.song = "";
    state.recording = "";
    state.section = "";
    state.sourceUrl = "";
    [elements.artist, elements.song, elements.recording, elements.section, elements.sourceUrl].forEach((input) => {
      input.value = "";
    });
  }

  function syncStateFromFields() {
    state.key = elements.key.value;
    state.contourMode = elements.contour.value;
    const parsed = parsePhraseEvents(elements.phraseInput.value);
    const previous = state.tokens;
    state.tokens = parsed.map((item, index) => ({
      ...item,
      direction: previous[index]?.direction || item.direction || "auto",
      octaveShift: previous[index]?.octaveShift || item.octaveShift || 0
    }));
    if (currentTask()?.needsMaterial) {
      state.artist = elements.artist.value.trim();
      state.song = elements.song.value.trim();
      state.recording = elements.recording.value.trim();
      state.section = elements.section.value.trim();
      state.sourceUrl = elements.sourceUrl.value.trim();
    } else {
      clearMaterial();
    }
  }

  function setTokens(tokens) {
    state.tokens = (tokens || []).map(phraseItem).filter((item) => phraseItemLabel(item));
    state.selectedPhraseIndex = Math.max(0, Math.min(state.selectedPhraseIndex || 0, state.tokens.length - 1));
    elements.phraseInput.value = state.tokens.some((item) => Number.isInteger(item.string))
      ? state.tokens.map(phraseItemLabel).join("\n")
      : state.tokens.map(phraseItemLabel).join(" ");
    renderPhraseBuilder();
  }

  function renderPalette() {
    const values = state.paletteMode === "notes" ? KEY_NOTES[state.key] : ["1", "2", "3", "4", "5", "6", "7"];
    elements.palette.replaceChildren();
    values.forEach((value) => {
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "palette-note";
      button.textContent = value;
      button.setAttribute("aria-label", `Add ${value} to phrase`);
      button.addEventListener("click", () => setTokens([...state.tokens, phraseItem(value)]));
      elements.palette.appendChild(button);
    });
    elements.paletteModeButtons.forEach((button) => {
      const selected = button.dataset.paletteMode === state.paletteMode;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  }

  function renderPhraseBuilder() {
    elements.sequence.replaceChildren();
    if (!state.tokens.length) {
      const empty = doc.createElement("p");
      empty.className = "sequence-empty";
      empty.textContent = "Your phrase will appear here as you type or choose notes.";
      elements.sequence.appendChild(empty);
    }
    const previews = resolvePhrasePreview(state.tokens, state.key, state.contourMode);
    state.tokens.forEach((raw, index) => {
      const token = phraseItem(raw);
      const tokenLabel = phraseItemLabel(token);
      const chip = doc.createElement("button");
      chip.type = "button";
      chip.className = "sequence-chip";
      chip.classList.toggle("is-selected", index === state.selectedPhraseIndex);
      chip.setAttribute("aria-pressed", String(index === state.selectedPhraseIndex));
      chip.setAttribute("aria-label", `Select ${tokenLabel}, ${previews[index]?.pitch || "unresolved pitch"}`);
      chip.dataset.sequenceIndex = String(index);
      const label = doc.createElement("strong");
      label.textContent = tokenLabel;
      const pitch = doc.createElement("span");
      pitch.className = "sequence-pitch";
      pitch.textContent = previews[index]?.pitch || "";
      chip.addEventListener("click", () => {
        state.selectedPhraseIndex = index;
        renderPhraseBuilder();
      });
      chip.append(label, pitch);
      elements.sequence.appendChild(chip);
    });
    const selected = state.tokens[state.selectedPhraseIndex];
    elements.noteEditor.hidden = !selected;
    if (selected) {
      const selectedItem = phraseItem(selected);
      elements.selectedNote.textContent = `Selected: ${phraseItemLabel(selectedItem)}`;
      elements.selectedPitch.textContent = previews[state.selectedPhraseIndex]?.pitch || "";
      const literal = Number.isInteger(selectedItem.string) && Number.isInteger(selectedItem.fret);
      elements.octaveDown.disabled = literal;
      elements.octaveAuto.disabled = literal;
      elements.octaveUp.disabled = literal;
      elements.noteEarlier.disabled = state.selectedPhraseIndex === 0;
      elements.noteLater.disabled = state.selectedPhraseIndex === state.tokens.length - 1;
    }
    const count = sectionCount(state.tokens);
    elements.sectionCount.textContent = state.tokens.length
      ? `${state.tokens.length} notes · ${count} ${count === 1 ? "section" : "sections"}`
      : "Up to eight notes appear in each lesson section.";
  }

  function selectTask(kind) {
    const previousNeedsMaterial = currentTask()?.needsMaterial;
    state.kind = TASKS[kind] ? kind : "";
    state.sectionNumber = 1;
    state.response = null;
    if (previousNeedsMaterial || !currentTask()?.needsMaterial) clearMaterial();
    elements.taskCards.forEach((card) => {
      const selected = card.dataset.studioTask === state.kind;
      card.classList.toggle("is-selected", selected);
      card.setAttribute("aria-pressed", String(selected));
    });
    elements.editor.hidden = !currentTask();
    elements.taskPanel.hidden = Boolean(currentTask());
    if (!currentTask()) return;
    elements.editorTitle.textContent = currentTask().title;
    elements.materialFields.hidden = !currentTask().needsMaterial;
    elements.result.hidden = true;
    renderPalette();
    renderPhraseBuilder();
    elements.editor.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function questionForState() {
    const subject = [state.artist, state.song].filter(Boolean).join(" — ");
    return subject ? `${currentTask().question} Source: ${subject}.` : currentTask().question;
  }

  function showError(message) {
    elements.error.textContent = message || "";
    elements.error.hidden = !message;
  }

  function materialLabel(material) {
    return [material?.artist, material?.song, material?.recording, material?.section].filter(Boolean).join(" · ");
  }

  function selectEvent(index) {
    const exercise = state.response?.melodyExercise;
    const events = exercise?.events || [];
    if (!events.length) return;
    state.activeEventIndex = Math.max(0, Math.min(index, events.length - 1));
    const event = events[state.activeEventIndex];
    const note = event.notes?.[0] || {};
    elements.eventStrip.querySelectorAll("[data-event-index]").forEach((button) => {
      const selected = Number(button.dataset.eventIndex) === state.activeEventIndex;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    elements.eventDetail.textContent = event.explanation || `${event.resolvedNote} · string ${note.string} · fret ${note.fret}`;
    const grip = (event.notes || []).map((item) => `S${item.string} F${item.fret}${item.changes?.length ? ` ${item.changes.join("+")}` : ""}`).join(" · ");
    elements.activeTabStep.textContent = `Active step ${event.step}: ${event.resolvedNote}${event.resolvedPitch ? ` (${event.resolvedPitch})` : ""} · ${grip}`;
    elements.previous.disabled = state.activeEventIndex === 0;
    elements.next.disabled = state.activeEventIndex === events.length - 1;
    if (event.renderablePositionId) {
      global.STEEL_RAG_FRETBOARD?.selectPedalSteelFretboardPosition?.(elements.fretboard, event.renderablePositionId);
    }
  }

  function renderEvents(exercise) {
    elements.eventStrip.replaceChildren();
    (exercise.events || []).forEach((event, index) => {
      const note = event.notes?.[0] || {};
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "event-step";
      button.dataset.eventIndex = String(index);
      const grip = (event.notes || []).map((item) => `S${item.string}`).join("+");
      button.textContent = `${event.step}. ${event.resolvedNote}${event.resolvedPitch ? ` ${event.resolvedPitch}` : ""} · ${grip} F${note.fret}`;
      button.addEventListener("click", () => selectEvent(index));
      elements.eventStrip.appendChild(button);
    });
  }

  function activateRoute(routeId) {
    const exercise = state.response?.melodyExercise;
    const route = (exercise?.routes || []).find((item) => item.id === routeId);
    if (!route) return;
    exercise.events = route.events;
    exercise.selectedRouteId = route.id;
    state.activeEventIndex = 0;
    [...elements.routeTabs.querySelectorAll("[data-route-id]"), ...elements.advancedRoutes.querySelectorAll("[data-route-id]")].forEach((button) => {
      const selected = button.dataset.routeId === route.id;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    elements.routeReason.textContent = route.recommendation || route.movementSummary || "";
    if (route.fretboard) {
      global.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(elements.fretboard, {
        maxFret: route.fretboard.maxFret,
        stringCount: route.fretboard.stringCount,
        tuningLabels: route.fretboard.tuningLabels,
        positions: route.fretboard.positions,
        highlights: route.fretboard.highlights || [],
        legend: route.fretboard.legend,
        query: route.fretboard.query
      });
    }
    renderEvents(exercise);
    elements.tabCode.textContent = route.tab?.tabText || "";
    selectEvent(0);
  }

  function renderRoutes(exercise) {
    elements.routeTabs.replaceChildren();
    elements.advancedRoutes.replaceChildren();
    const routes = exercise?.routes || [];
    const primaryRoutes = routes.filter((route) => route.harmonyType === "single_note" || route.recommended);
    const advancedRoutes = routes.filter((route) => !primaryRoutes.includes(route));
    elements.routeTabs.hidden = primaryRoutes.length < 2;
    elements.moreRoutes.hidden = advancedRoutes.length === 0;
    elements.moreRoutes.open = false;
    routes.forEach((route) => {
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "route-tab";
      button.dataset.routeId = route.id;
      button.textContent = `${route.recommended ? "Recommended · " : ""}${route.label}`;
      button.addEventListener("click", () => activateRoute(route.id));
      (primaryRoutes.includes(route) ? elements.routeTabs : elements.advancedRoutes).appendChild(button);
    });
  }

  function renderResult(response) {
    state.response = response;
    state.activeEventIndex = 0;
    const exercise = response.melodyExercise;
    elements.editor.hidden = true;
    elements.result.hidden = false;
    elements.resultTitle.textContent = exercise?.title || "Melody lesson";
    const accuracy = exercise?.accuracy || {};
    const section = exercise?.section || {};
    elements.resultMeta.textContent = [
      accuracy.label && `${accuracy.label} · ${accuracy.confidence || ""} confidence`,
      section.total ? `Section ${section.number} of ${section.total}` : section.label
    ].filter(Boolean).join(" · ");
    const sourceLabel = materialLabel(exercise?.material);
    elements.resultSource.replaceChildren();
    if (sourceLabel) {
      elements.resultSource.append(doc.createTextNode(sourceLabel));
      if (exercise.material.sourceUrl) {
        const link = doc.createElement("a");
        link.href = exercise.material.sourceUrl;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Open attribution source";
        elements.resultSource.append(" · ", link);
      }
      elements.resultSource.hidden = false;
    } else {
      elements.resultSource.hidden = true;
    }
    const needsSource = exercise?.status === "needs_source";
    elements.sourceNeeded.hidden = !needsSource;
    elements.sourceNeeded.querySelector("p").textContent = needsSource
      ? "The recording identity is saved, but Melody Studio does not listen to the link yet. Paste notes, scale degrees, or simple one-string tab—or build the passage with the note palette—to render playable E9 positions."
      : "";
    elements.fretboard.hidden = needsSource || !response.fretboard;
    elements.transport.hidden = needsSource || !exercise?.events?.length;
    elements.tab.hidden = needsSource || !response.tabs?.length;
    elements.explanation.hidden = needsSource;
    elements.routeTabs.hidden = needsSource;
    elements.moreRoutes.hidden = needsSource;
    elements.routeReason.hidden = needsSource;
    if (!needsSource && response.fretboard) {
      global.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(elements.fretboard, {
        maxFret: response.fretboard.maxFret,
        stringCount: response.fretboard.stringCount,
        tuningLabels: response.fretboard.tuningLabels,
        positions: response.fretboard.positions,
        highlights: response.fretboard.highlights || [],
        legend: response.fretboard.legend,
        query: response.fretboard.query
      });
      renderEvents(exercise);
      renderRoutes(exercise);
      elements.tabCode.textContent = response.tabs[0]?.tabText || "";
      elements.explanation.textContent = accuracy.note || "Practice one event at a time, then connect the phrase slowly.";
      const selectedRoute = exercise.routes?.find((route) => route.id === exercise.selectedRouteId);
      if (selectedRoute) activateRoute(selectedRoute.id);
      else selectEvent(0);
    }
    elements.continueButton.hidden = !section.hasMore;
    elements.continueButton.textContent = section.nextSection ? `Continue to Section ${section.nextSection}` : "Continue";
    elements.continueButton.dataset.nextSection = String(section.nextSection || "");
    elements.result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function submitLesson(sectionNumber = 1) {
    syncStateFromFields();
    const task = currentTask();
    if (!task) return showError("Choose what you want to learn first.");
    const validation = validateTokens(state.tokens, state.key);
    if (!validation.ok && (!task.needsMaterial || state.tokens.length)) return showError(validation.message);
    if (state.sourceUrl) {
      try {
        const url = new URL(state.sourceUrl);
        if (!/^https?:$/.test(url.protocol)) throw new Error("protocol");
      } catch (_error) {
        return showError("Use a complete http:// or https:// attribution link.");
      }
    }
    showError("");
    state.sectionNumber = sectionNumber;
    elements.build.disabled = true;
    elements.build.textContent = "Building lesson…";
    try {
      const response = await answerUi.requestAnswer(questionForState(), {
        accessRole: session?.role || readAccessRole(),
        requestPayload: { melodyRequest: buildMelodyRequest(state) }
      });
      renderResult(response);
    } catch (error) {
      showError(error.message || "Melody Studio could not build this lesson.");
    } finally {
      elements.build.disabled = false;
      elements.build.textContent = "Build my E9 lesson";
    }
  }

  function editPhrase() {
    elements.result.hidden = true;
    elements.editor.hidden = false;
    elements.editor.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function startOver() {
    state = createInitialState();
    clearMaterial();
    elements.key.value = "G";
    elements.contour.value = "closest_playable";
    elements.phraseInput.value = "";
    elements.editor.hidden = true;
    elements.result.hidden = true;
    elements.taskPanel.hidden = false;
    elements.taskCards.forEach((card) => {
      card.classList.remove("is-selected");
      card.setAttribute("aria-pressed", "false");
    });
    renderPalette();
    renderPhraseBuilder();
    showError("");
    $("#studio-task-heading")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function bootstrap() {
    try {
      session = await answerUi.requestSession({ accessRole: readAccessRole() });
      const enabled = Boolean(session.features?.melodyExercise);
      elements.unavailable.hidden = enabled;
      elements.workflow.hidden = !enabled;
      if (!enabled) return;
      if (state.kind) selectTask(state.kind);
      renderPalette();
      renderPhraseBuilder();
    } catch (_error) {
      elements.unavailable.hidden = false;
      elements.workflow.hidden = true;
    }
  }

  elements.taskCards.forEach((card) => card.addEventListener("click", () => selectTask(card.dataset.studioTask)));
  elements.changeTask.addEventListener("click", () => {
    elements.editor.hidden = true;
    elements.result.hidden = true;
    elements.taskPanel.hidden = false;
    elements.taskPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  elements.octaveDown.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens[index] = { ...phraseItem(state.tokens[index]), octaveShift: Math.max(-2, Number(state.tokens[index]?.octaveShift || 0) - 1) };
    renderPhraseBuilder();
  });
  elements.octaveAuto.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens[index] = { ...phraseItem(state.tokens[index]), direction: "auto", octaveShift: 0 };
    renderPhraseBuilder();
  });
  elements.octaveUp.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens[index] = { ...phraseItem(state.tokens[index]), octaveShift: Math.min(2, Number(state.tokens[index]?.octaveShift || 0) + 1) };
    renderPhraseBuilder();
  });
  elements.noteEarlier.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.selectedPhraseIndex = Math.max(0, index - 1);
    setTokens(reorderToken(state.tokens, index, -1));
  });
  elements.noteLater.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.selectedPhraseIndex = Math.min(state.tokens.length - 1, index + 1);
    setTokens(reorderToken(state.tokens, index, 1));
  });
  elements.noteRemove.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens = state.tokens.filter((_item, itemIndex) => itemIndex !== index);
    state.selectedPhraseIndex = Math.max(0, Math.min(index, state.tokens.length - 1));
    setTokens(state.tokens);
  });
  elements.key.addEventListener("change", () => {
    state.key = elements.key.value;
    renderPalette();
    renderPhraseBuilder();
  });
  elements.contour.addEventListener("change", () => {
    state.contourMode = elements.contour.value;
    renderPhraseBuilder();
  });
  elements.phraseInput.addEventListener("input", () => {
    state.tokens = parsePhraseEvents(elements.phraseInput.value);
    renderPhraseBuilder();
  });
  elements.paletteModeButtons.forEach((button) => button.addEventListener("click", () => {
    state.paletteMode = button.dataset.paletteMode;
    renderPalette();
  }));
  elements.presetButtons.forEach((button) => button.addEventListener("click", () => setTokens(PRESETS[button.dataset.preset] || [])));
  elements.build.addEventListener("click", () => submitLesson(1));
  elements.previous.addEventListener("click", () => selectEvent(state.activeEventIndex - 1));
  elements.next.addEventListener("click", () => selectEvent(state.activeEventIndex + 1));
  elements.continueButton.addEventListener("click", () => submitLesson(Number(elements.continueButton.dataset.nextSection) || state.sectionNumber + 1));
  elements.edit.addEventListener("click", editPhrase);
  elements.sourceNeeded.querySelector("[data-edit-source]").addEventListener("click", editPhrase);
  elements.result.querySelector("[data-start-over]").addEventListener("click", startOver);

  bootstrap();
})(typeof window !== "undefined" ? window : globalThis);
