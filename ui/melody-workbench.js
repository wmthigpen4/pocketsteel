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
    const invalid = (tokens || []).filter((token) => !/^[1-7]$/.test(token) && !allowedNotes.has(normalizeToken(token)));
    if (!tokens?.length) return { ok: false, message: "Add at least one note, scale degree, or simple tab position." };
    if (invalid.length) {
      return { ok: false, message: `${invalid.join(", ")} ${invalid.length === 1 ? "is" : "are"} outside ${key} major in Melody Studio v0.` };
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
      sectionNumber: state.sectionNumber || 1
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
    taskCards: Array.from(doc.querySelectorAll("[data-studio-task]")),
    editor: $("#studio-editor"),
    editorTitle: $("#studio-editor-title"),
    materialFields: $("#studio-material-fields"),
    artist: $("#studio-artist"),
    song: $("#studio-song"),
    recording: $("#studio-recording"),
    section: $("#studio-section"),
    sourceUrl: $("#studio-source-url"),
    key: $("#studio-key"),
    phraseInput: $("#studio-phrase-input"),
    sequence: $("#studio-sequence"),
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
    state.tokens = parsePhraseInput(elements.phraseInput.value);
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
    state.tokens = (tokens || []).map(normalizeToken).filter(Boolean);
    elements.phraseInput.value = state.tokens.join(" ");
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
      button.addEventListener("click", () => setTokens([...state.tokens, value]));
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
    state.tokens.forEach((token, index) => {
      const chip = doc.createElement("div");
      chip.className = "sequence-chip";
      chip.dataset.sequenceIndex = String(index);
      const label = doc.createElement("strong");
      label.textContent = token;
      const left = doc.createElement("button");
      left.type = "button";
      left.textContent = "←";
      left.disabled = index === 0;
      left.setAttribute("aria-label", `Move ${token} earlier`);
      left.addEventListener("click", () => setTokens(reorderToken(state.tokens, index, -1)));
      const right = doc.createElement("button");
      right.type = "button";
      right.textContent = "→";
      right.disabled = index === state.tokens.length - 1;
      right.setAttribute("aria-label", `Move ${token} later`);
      right.addEventListener("click", () => setTokens(reorderToken(state.tokens, index, 1)));
      const remove = doc.createElement("button");
      remove.type = "button";
      remove.textContent = "×";
      remove.setAttribute("aria-label", `Remove ${token}`);
      remove.addEventListener("click", () => setTokens(state.tokens.filter((_, tokenIndex) => tokenIndex !== index)));
      chip.append(label, left, right, remove);
      elements.sequence.appendChild(chip);
    });
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
    elements.activeTabStep.textContent = `Active step ${event.step}: ${event.resolvedNote} · S${note.string} F${note.fret}`;
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
      button.textContent = `${event.step}. ${event.resolvedNote} · S${note.string} F${note.fret}`;
      button.addEventListener("click", () => selectEvent(index));
      elements.eventStrip.appendChild(button);
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
      elements.tabCode.textContent = response.tabs[0]?.tabText || "";
      elements.explanation.textContent = accuracy.note || "Practice one event at a time, then connect the phrase slowly.";
      selectEvent(0);
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
    elements.phraseInput.value = "";
    elements.editor.hidden = true;
    elements.result.hidden = true;
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
  elements.key.addEventListener("change", () => {
    state.key = elements.key.value;
    renderPalette();
    renderPhraseBuilder();
  });
  elements.phraseInput.addEventListener("input", () => {
    state.tokens = parsePhraseInput(elements.phraseInput.value);
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
