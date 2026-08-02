(function (global) {
  "use strict";

  const SCHEMA_VERSION = "song_project_v1";
  const REQUEST_SCHEMA = "song_practice_request_v1";
  const DB_NAME = "turnaround-melody-studio";
  const STORE_NAME = "songProjects";
  const NOTE_PCS = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };
  const SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
  const SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11];
  const MAX_CUE_LENGTH = 80;
  const REST_SYMBOL = "__REST__";

  function nowIso() {
    return new Date().toISOString();
  }

  function makeId(prefix) {
    const value = global.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return `${prefix}-${value}`;
  }

  function normalizeLetterChord(value) {
    const raw = String(value || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
    if (/^(?:N\.?C\.?|NO\s+CHORD|REST)$/i.test(raw)) return REST_SYMBOL;
    const match = raw.match(/^([A-Ga-g])([#b]?)([A-Za-z0-9()+#b°ø-]*)(?:\/([A-Ga-g])([#b]?))?$/);
    if (!match) return null;
    const root = `${match[1].toUpperCase()}${match[2]}`;
    const bass = match[4] ? `${match[4].toUpperCase()}${match[5]}` : "";
    if (!(root in NOTE_PCS) || (bass && !(bass in NOTE_PCS))) return null;
    return `${root}${match[3]}${bass ? `/${bass}` : ""}`;
  }

  function nashvilleToLetter(value, key) {
    const raw = String(value || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
    const match = raw.match(/^([b#]?)([1-7])([A-Za-z0-9()+#b°ø-]*)(?:\/([b#]?)([1-7]))?$/);
    const keyPc = NOTE_PCS[key];
    if (!match || !Number.isInteger(keyPc)) return null;
    const accidental = match[1] === "b" ? -1 : match[1] === "#" ? 1 : 0;
    const degree = Number(match[2]) - 1;
    const pc = (keyPc + SCALE_INTERVALS[degree] + accidental + 12) % 12;
    const names = /b/.test(key) || ["F", "Bb", "Eb", "Ab", "Db"].includes(key) ? FLAT_NAMES : SHARP_NAMES;
    let bass = "";
    if (match[5]) {
      const bassAccidental = match[4] === "b" ? -1 : match[4] === "#" ? 1 : 0;
      const bassPc = (keyPc + SCALE_INTERVALS[Number(match[5]) - 1] + bassAccidental + 12) % 12;
      bass = `/${names[bassPc]}`;
    }
    return `${names[pc]}${match[3]}${bass}`;
  }

  function parseSectionMarker(value) {
    const raw = String(value || "").trim();
    const [label, cue = ""] = raw.split(/\s+::\s+/, 2);
    return {
      label: label.trim() || "Song",
      cue: cue.trim().slice(0, MAX_CUE_LENGTH)
    };
  }

  function parseSongChart(chartText, options = {}) {
    const raw = String(chartText || "").trim();
    const mode = options.mode === "nashville" ? "nashville" : "letter";
    const key = String(options.key || "G");
    const meter = String(options.meter || "4/4");
    const errors = [];
    const warnings = [];
    if (!raw.includes("|")) errors.push("Separate every bar with | marks.");
    if (!(key in NOTE_PCS)) errors.push(`Unsupported key: ${key}`);

    let activeSection = { id: "section-1", label: "Song", cue: "", startMeasure: 1, endMeasure: 0 };
    const sections = [activeSection];
    const measures = [];
    const pieces = raw.split("|");
    pieces.forEach((piece) => {
      let content = piece.trim();
      const markers = Array.from(content.matchAll(/\[([^\]]+)\]/g));
      markers.forEach((marker) => {
        const parsed = parseSectionMarker(marker[1]);
        if (measures.length === 0 && sections.length === 1 && sections[0].label === "Song") {
          activeSection.label = parsed.label;
          activeSection.cue = parsed.cue;
        } else {
          activeSection.endMeasure = measures.length;
          activeSection = {
            id: `section-${sections.length + 1}`,
            label: parsed.label,
            cue: parsed.cue,
            startMeasure: measures.length + 1,
            endMeasure: measures.length
          };
          sections.push(activeSection);
        }
      });
      content = content.replace(/\[[^\]]+\]/g, "").replace(/^:+|:+$/g, "").trim();
      if (!content) return;
      let repeatCount = 1;
      const repeatMatch = content.match(/^(.*?)\s+(?:x|×|\*)\s*([2-8])$/i);
      if (repeatMatch) {
        content = repeatMatch[1].trim();
        repeatCount = Number(repeatMatch[2]);
      }
      if (content === "%") {
        const previous = measures.at(-1);
        if (!previous) {
          errors.push("% cannot repeat a bar before the first bar.");
          return;
        }
        content = previous.displayChords.join(" ");
      }
      const displayChords = content.split(/\s+/).filter(Boolean);
      const resolvedChords = displayChords.map((symbol) => mode === "nashville" ? nashvilleToLetter(symbol, key) : normalizeLetterChord(symbol));
      const invalid = displayChords.filter((_symbol, index) => resolvedChords[index] == null);
      if (invalid.length) {
        errors.push(`Bar ${measures.length + 1}: invalid chord symbol${invalid.length === 1 ? "" : "s"} ${invalid.join(", ")}.`);
        return;
      }
      for (let repeat = 0; repeat < repeatCount; repeat += 1) {
        const number = measures.length + 1;
        measures.push({
          id: `measure-${number}`,
          number,
          sectionId: activeSection.id,
          displayChords: [...displayChords],
          resolvedChords: [...resolvedChords],
          chordFractions: resolvedChords.map((_item, index) => index / resolvedChords.length),
          needsReview: resolvedChords.length > 1,
          role: resolvedChords.every((chord) => chord === REST_SYMBOL) ? "rest" : "comp"
        });
      }
    });
    activeSection.endMeasure = measures.length;
    if (!measures.length && !errors.length) errors.push("Add at least one chord bar.");
    if (measures.some((measure) => measure.needsReview)) warnings.push("Multi-chord bars were divided evenly and need timing review.");
    return { schemaVersion: "song_chart_v1", mode, key, meter, sections, measures, errors, warnings };
  }

  function buildTimedEvents(project) {
    const measures = Array.isArray(project?.measures) ? project.measures : [];
    const starts = Array.isArray(project?.barStartsMs) ? project.barStartsMs : [];
    const durationMs = Number(project?.audioRef?.durationMs || project?.durationMs || 0);
    if (!measures.length || starts.length !== measures.length || starts.some((value) => !Number.isFinite(value))) {
      throw new Error("Every bar needs a captured downbeat before arranging.");
    }
    const offset = Number(project.syncOffsetMs || 0);
    const events = [];
    measures.forEach((measure, measureIndex) => {
      const barStart = Math.max(0, Math.round(starts[measureIndex] + offset));
      const nextStart = measureIndex + 1 < starts.length ? starts[measureIndex + 1] + offset : durationMs + offset;
      const barEnd = Math.max(barStart + 1, Math.round(nextStart));
      const fractions = measure.chordFractions?.length === measure.resolvedChords.length
        ? measure.chordFractions
        : measure.resolvedChords.map((_item, index) => index / measure.resolvedChords.length);
      measure.resolvedChords.forEach((chord, chordIndex) => {
        const startFraction = Number(fractions[chordIndex] || 0);
        const endFraction = chordIndex + 1 < fractions.length ? Number(fractions[chordIndex + 1]) : 1;
        events.push({
          id: `${measure.id}-chord-${chordIndex + 1}`,
          measureId: measure.id,
          sectionId: measure.sectionId,
          chord: chord === REST_SYMBOL ? "" : chord,
          startMs: Math.round(barStart + ((barEnd - barStart) * startFraction)),
          endMs: Math.round(barStart + ((barEnd - barStart) * endFraction)),
          role: chord === REST_SYMBOL ? "rest" : (measure.role || "comp")
        });
      });
    });
    return events;
  }

  function activeTimelineState(events, timeMs) {
    const timeline = Array.isArray(events) ? events : [];
    const currentIndex = timeline.findIndex((event) => timeMs >= event.startMs && timeMs < event.endMs);
    if (currentIndex >= 0) return { currentIndex, current: timeline[currentIndex], next: timeline[currentIndex + 1] || null };
    const nextIndex = timeline.findIndex((event) => event.startMs > timeMs);
    if (nextIndex >= 0) return { currentIndex: -1, current: null, next: timeline[nextIndex] };
    return { currentIndex: timeline.length - 1, current: timeline.at(-1) || null, next: null };
  }

  function automaticBarStarts(measureCount, durationMs, leadInMs = 0) {
    const count = Number(measureCount);
    const duration = Number(durationMs);
    const leadIn = Math.max(0, Number(leadInMs || 0));
    if (!Number.isInteger(count) || count < 1 || !Number.isFinite(duration) || duration <= leadIn) return [];
    const usableDuration = duration - leadIn;
    return Array.from({ length: count }, (_item, index) => Math.round(leadIn + ((usableDuration * index) / count)));
  }

  function localAudioIdentity(file, durationMs) {
    return {
      filename: String(file?.name || ""),
      size: Number(file?.size || 0),
      lastModified: Number(file?.lastModified || 0),
      durationMs: Math.round(Number(durationMs || 0))
    };
  }

  function matchesLocalAudioIdentity(expected, actual, durationToleranceMs = 750) {
    return Boolean(expected && actual
      && expected.filename === actual.filename
      && Number(expected.size) === Number(actual.size)
      && Number(expected.lastModified) === Number(actual.lastModified)
      && Math.abs(Number(expected.durationMs) - Number(actual.durationMs)) <= durationToleranceMs);
  }

  function forbiddenRetainedAudioPath(value, path = "project") {
    if (!value || typeof value !== "object") return "";
    for (const [key, nested] of Object.entries(value)) {
      const normalized = key.toLowerCase().replace(/[^a-z0-9]/g, "");
      if (["audioblob", "audiobytes", "audiodata", "objecturl", "fileblob"].includes(normalized)) return `${path}.${key}`;
      const child = forbiddenRetainedAudioPath(nested, `${path}.${key}`);
      if (child) return child;
    }
    return "";
  }

  function sanitizeProjectForStorage(project) {
    const forbidden = forbiddenRetainedAudioPath(project);
    if (forbidden) throw new Error(`${forbidden} cannot be stored in a Song Project.`);
    const clone = JSON.parse(JSON.stringify(project));
    delete clone.audioUrl;
    delete clone.file;
    delete clone.audioElement;
    clone.schemaVersion = SCHEMA_VERSION;
    return clone;
  }

  function migrateProject(rawProject) {
    if (!rawProject || typeof rawProject !== "object") throw new Error("Song Project JSON must contain an object.");
    const project = JSON.parse(JSON.stringify(rawProject));
    if (project.schemaVersion === "song_project_v0") {
      project.barStartsMs = project.barStartsMs || project.barTimes || [];
      delete project.barTimes;
      project.schemaVersion = SCHEMA_VERSION;
    }
    if (project.schemaVersion !== SCHEMA_VERSION) throw new Error(`Unsupported Song Project schema: ${project.schemaVersion || "missing"}.`);
    if (!Array.isArray(project.measures) || !Array.isArray(project.sections)) throw new Error("Song Project measures and sections are required.");
    return sanitizeProjectForStorage(project);
  }

  function exportProjectJson(project) {
    return JSON.stringify(sanitizeProjectForStorage(project), null, 2);
  }

  function buildArrangePayload(project, copedentContext) {
    const events = buildTimedEvents(project);
    (project.authoredRoute || []).forEach((positionHint, index) => {
      if (events[index] && positionHint) events[index].positionHint = positionHint;
    });
    return {
      schemaVersion: REQUEST_SCHEMA,
      level: "chord_karaoke",
      key: project.key,
      meter: project.meter,
      style: project.style || "classic_country",
      events,
      copedentContext: copedentContext || { profileId: "emmons-e9-basic" }
    };
  }

  function openDatabase(indexedDb = global.indexedDB) {
    return new Promise((resolve, reject) => {
      if (!indexedDb) return reject(new Error("IndexedDB is unavailable in this browser."));
      const request = indexedDb.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(STORE_NAME)) request.result.createObjectStore(STORE_NAME, { keyPath: "id" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Could not open Song Project storage."));
    });
  }

  async function withStore(mode, callback) {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, mode);
      const request = callback(transaction.objectStore(STORE_NAME));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Song Project storage failed."));
      transaction.oncomplete = () => database.close();
      transaction.onabort = () => reject(transaction.error || new Error("Song Project storage was interrupted."));
    });
  }

  function saveProject(project) {
    return withStore("readwrite", (store) => store.put(sanitizeProjectForStorage(project)));
  }

  function loadProject(id) {
    return withStore("readonly", (store) => store.get(id));
  }

  function listProjects() {
    return withStore("readonly", (store) => store.getAll());
  }

  const api = {
    SCHEMA_VERSION,
    REQUEST_SCHEMA,
    MAX_CUE_LENGTH,
    normalizeLetterChord,
    nashvilleToLetter,
    parseSongChart,
    buildTimedEvents,
    activeTimelineState,
    automaticBarStarts,
    localAudioIdentity,
    matchesLocalAudioIdentity,
    forbiddenRetainedAudioPath,
    sanitizeProjectForStorage,
    migrateProject,
    exportProjectJson,
    buildArrangePayload,
    saveProject,
    loadProject,
    listProjects
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  global.STEEL_RAG_SONG_PROJECTS = api;
  if (!global.document) return;

  const doc = global.document;
  const $ = (selector) => doc.querySelector(selector);
  const elements = {
    workspace: $("#studio-song-project"), editor: $("#studio-editor"), close: $("#song-project-close"), builderDetails: $("#song-builder-details"),
    projectList: $("#song-project-list"), newProject: $("#song-project-new"), importButton: $("#song-project-import"), importFile: $("#song-project-import-file"),
    sourceButtons: Array.from(doc.querySelectorAll("[data-song-source]")), localSource: $("#song-local-source"), builtInSource: $("#song-built-in-source"),
    localFile: $("#song-local-file"), localStatus: $("#song-local-status"), pilotGrid: $("#song-pilot-grid"), rightsNotice: $("#song-rights-notice"),
    name: $("#song-project-name"), key: $("#song-project-key"), meter: $("#song-project-meter"), chartMode: $("#song-chart-mode"), style: $("#song-project-style"), chart: $("#song-chart"), parse: $("#song-parse-chart"), status: $("#song-project-status"),
    playerStage: $("#song-player-stage"), syncStage: $("#song-sync-stage"), editSync: $("#song-edit-sync"), audio: $("#song-audio"), rate: $("#song-playback-rate"), offset: $("#song-sync-offset"),
    playToggle: $("#song-play-toggle"), skipBack: $("#song-skip-back"), skipForward: $("#song-skip-forward"), tap: $("#song-tap-bar"), undo: $("#song-undo-tap"), retap: $("#song-retap-section"), nudgeBack: $("#song-nudge-back"), nudgeForward: $("#song-nudge-forward"),
    progress: $("#song-sync-progress"), selectedBar: $("#song-selected-bar"), audioTime: $("#song-audio-time"), nextTap: $("#song-next-tap"), measureList: $("#song-measure-list"),
    save: $("#song-save-project"), export: $("#song-export-project"), arrange: $("#song-arrange"),
    practiceStage: $("#song-practice-stage"), chordStrip: $("#song-chord-strip"), loopEnabled: $("#song-loop-enabled"), loopSection: $("#song-loop-section"), currentSection: $("#song-current-section"), nextSection: $("#song-next-section"), currentChord: $("#song-current-chord"), nextChord: $("#song-next-chord"), countdown: $("#song-countdown"), currentCue: $("#song-current-cue"), positionTitle: $("#song-position-title"), positionInstruction: $("#song-position-instruction"), alternatives: $("#song-alternatives"), fretboard: $("#song-fretboard"), warning: $("#song-practice-warning")
  };

  let session = null;
  let enabled = false;
  let catalog = [];
  let project = null;
  let objectUrl = "";
  let tapIndex = 0;
  let tapStartIndex = 0;
  let tapStopIndex = 0;
  let selectedMeasureId = "";
  let selectedPlanEventId = "";
  let animationFrame = 0;
  let bindingsReady = false;

  function blankProject() {
    const createdAt = nowIso();
    return {
      schemaVersion: SCHEMA_VERSION,
      id: makeId("song-project"),
      name: "",
      createdAt,
      updatedAt: createdAt,
      key: "G",
      meter: "4/4",
      chartMode: "letter",
      chartText: "[Verse 1] | G | C | G D7 | G |",
      style: "classic_country",
      sections: [],
      measures: [],
      barStartsMs: [],
      syncOffsetMs: 0,
      source: { type: "built_in", builtInTrackId: "" },
      audioRef: null,
      chosenPlan: null,
      provenance: { audioRetained: false, createdIn: "melody_studio_song_practice" },
      version: { appContract: SCHEMA_VERSION }
    };
  }

  function accessHeaders(json = false) {
    const headers = { Accept: "application/json" };
    if (json) headers["Content-Type"] = "application/json";
    if (["beta_user", "admin"].includes(session?.role)) headers["X-Steel-Rag-Dev-Access-Role"] = session.role;
    return headers;
  }

  function status(message, isError = false) {
    elements.status.textContent = message || "";
    elements.status.style.color = isError ? "#ffb1a8" : "";
  }

  function formatTime(ms) {
    const safe = Math.max(0, Number(ms || 0));
    const minutes = Math.floor(safe / 60000);
    const seconds = Math.floor((safe % 60000) / 1000);
    const millis = Math.floor(safe % 1000);
    return `${minutes}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
  }

  function revokeLocalAudio() {
    if (objectUrl) global.URL.revokeObjectURL(objectUrl);
    objectUrl = "";
  }

  function setAudioSource(url, local = false) {
    revokeLocalAudio();
    if (local) objectUrl = url;
    elements.audio.pause();
    if (url) elements.audio.src = url;
    else elements.audio.removeAttribute("src");
    elements.audio.load();
    elements.playerStage.hidden = !url;
  }

  function hasAudioSource() {
    return Boolean(elements.audio.getAttribute("src"));
  }

  function collectFields() {
    project.name = elements.name.value.trim().slice(0, 100);
    project.key = elements.key.value;
    project.meter = elements.meter.value;
    project.chartMode = elements.chartMode.value;
    project.style = elements.style.value;
    project.chartText = elements.chart.value;
    project.syncOffsetMs = Number(elements.offset.value || 0);
    project.updatedAt = nowIso();
  }

  function fillFields() {
    elements.name.value = project.name || "";
    elements.key.value = project.key || "G";
    elements.meter.value = project.meter || "4/4";
    elements.chartMode.value = project.chartMode || "letter";
    elements.style.value = project.style || "classic_country";
    elements.chart.value = project.chartText || "";
    elements.offset.value = String(project.syncOffsetMs || 0);
    selectSource(project.source?.type || "built_in", { preserve: true });
  }

  function selectSource(type, options = {}) {
    const nextType = type === "built_in" ? "built_in" : "local";
    project.source = project.source || {};
    if (!options.preserve && project.source.type !== nextType) {
      project.source = { type: nextType, builtInTrackId: "" };
      project.audioRef = null;
      project.barStartsMs = [];
      project.chosenPlan = null;
      setAudioSource("");
    }
    project.source.type = nextType;
    elements.localSource.hidden = nextType !== "local";
    elements.builtInSource.hidden = nextType !== "built_in";
    if (nextType === "local") elements.builderDetails.open = true;
    else elements.builderDetails.open = false;
    elements.sourceButtons.forEach((button) => {
      const selected = button.dataset.songSource === nextType;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    renderPilots();
  }

  function applyParsedChart(parsed, starts = null) {
    project.sections = parsed.sections;
    project.measures = parsed.measures;
    project.barStartsMs = starts && starts.length === parsed.measures.length ? [...starts] : Array(parsed.measures.length).fill(null);
    project.chosenPlan = null;
    const missingBarIndex = project.barStartsMs.findIndex((value) => !Number.isFinite(value));
    tapIndex = missingBarIndex < 0 ? project.measures.length : missingBarIndex;
    tapStartIndex = 0;
    tapStopIndex = project.measures.length;
    selectedMeasureId = project.measures[0]?.id || "";
    elements.syncStage.hidden = true;
    elements.editSync.hidden = false;
    elements.practiceStage.hidden = true;
    renderMeasures();
    renderLoopSections();
    status(parsed.warnings.join(" ") || `${parsed.measures.length} bars received. Timing is ready automatically.`);
  }

  function parseCurrentChart(starts = null) {
    collectFields();
    const parsed = parseSongChart(project.chartText, { mode: project.chartMode, key: project.key, meter: project.meter });
    if (parsed.errors.length) {
      status(parsed.errors.join(" "), true);
      return false;
    }
    const automaticStarts = starts || automaticBarStarts(parsed.measures.length, project.durationMs || project.audioRef?.durationMs || 0);
    if (!automaticStarts.length) {
      status("Choose a recording before creating the automatic practice track.", true);
      return false;
    }
    applyParsedChart(parsed, automaticStarts);
    if (!starts) {
      project.provenance = { ...(project.provenance || {}), timingMethod: "automatic_even_first_pass" };
      status(`${parsed.measures.length} bars aligned automatically. Press Play song; use advanced synchronization only if the changes are clearly early or late.`);
    }
    return true;
  }

  function renderPilots() {
    elements.pilotGrid.innerHTML = catalog.map((track) => `
      <button class="song-pilot${project?.source?.builtInTrackId === track.id ? " is-selected" : ""}" type="button" data-song-pilot="${track.id}">
        <strong>Practice ${escapeHtml(track.title)}</strong><small>${escapeHtml(track.key)} · ${escapeHtml(track.meter)} · recognizable melody · one-bar count-in · no steel</small>
      </button>`).join("");
    elements.pilotGrid.querySelectorAll("[data-song-pilot]").forEach((button) => button.addEventListener("click", () => selectPilot(button.dataset.songPilot).catch((error) => status(error.message, true))));
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
  }

  async function selectPilot(id, options = {}) {
    const track = catalog.find((item) => item.id === id);
    if (!track) return;
    project.source = { type: "built_in", builtInTrackId: track.id };
    project.audioRef = { kind: "built_in", trackId: track.id, durationMs: track.durationMs };
    project.durationMs = track.durationMs;
    setAudioSource(track.audioUrl);
    if (!options.preserveProject) {
      project.name = track.title;
      project.key = track.key;
      project.meter = track.meter;
      project.chartMode = "letter";
      project.chartText = track.chart;
      fillFields();
      if (!parseCurrentChart(track.barStartsMs)) return;
      elements.builderDetails.open = false;
      status(`Preparing ${track.title} for Chord Karaoke…`);
      await arrange();
    } else if (project.chosenPlan?.events?.length) {
      elements.practiceStage.hidden = false;
      renderPractice(true);
    }
    renderPilots();
  }

  async function loadCatalog() {
    const response = await fetch("/api/song-practice/catalog", { headers: accessHeaders() });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "Could not load the practice-track catalog.");
    catalog = payload.tracks || [];
    elements.rightsNotice.textContent = payload.rightsNotice || "";
    renderPilots();
    if (project?.source?.type === "built_in" && project.source.builtInTrackId) await selectPilot(project.source.builtInTrackId, { preserveProject: true });
  }

  function renderMeasures() {
    const starts = project.barStartsMs || [];
    const captured = starts.filter(Number.isFinite).length;
    elements.progress.textContent = `${captured} of ${project.measures.length} bars`;
    elements.nextTap.textContent = tapIndex < tapStopIndex ? `Bar ${tapIndex + 1}` : "Complete";
    const selectedIndex = Math.max(0, project.measures.findIndex((measure) => measure.id === selectedMeasureId));
    elements.selectedBar.textContent = project.measures[selectedIndex] ? `Bar ${selectedIndex + 1}` : "—";
    elements.measureList.innerHTML = project.measures.map((measure, index) => {
      const timestamp = starts[index];
      const section = project.sections.find((item) => item.id === measure.sectionId);
      const previous = Number.isFinite(starts[index - 1]) ? starts[index - 1] + 25 : 0;
      const next = Number.isFinite(starts[index + 1]) ? starts[index + 1] - 25 : Math.max(previous + 100, Number(project.audioRef?.durationMs || project.durationMs || 600000));
      const boundaries = measure.resolvedChords.slice(1).map((chord, boundaryIndex) => {
        const fractionIndex = boundaryIndex + 1;
        const value = Math.round(Number(measure.chordFractions[fractionIndex]) * 100);
        return `<label class="song-boundary"><span>${escapeHtml(measure.displayChords[boundaryIndex])} → ${escapeHtml(measure.displayChords[fractionIndex])}</span><input type="range" min="5" max="95" step="1" value="${value}" data-song-boundary="${measure.id}:${fractionIndex}"><output>${value}%</output></label>`;
      }).join("");
      const cue = section?.startMeasure === measure.number ? `<label class="song-cue-row">Short cue for ${escapeHtml(section.label)}<input maxlength="${MAX_CUE_LENGTH}" value="${escapeHtml(section.cue || "")}" data-song-cue="${section.id}" placeholder="Optional cue, not full lyrics"></label>` : "";
      return `<article class="song-measure-row${selectedMeasureId === measure.id ? " is-active" : ""}" data-song-measure-row="${measure.id}">
        <button class="secondary-action" type="button" data-song-select-bar="${measure.id}" aria-label="Select bar ${index + 1}">${index + 1}</button>
        <div><strong>${escapeHtml(measure.displayChords.join(" · "))}</strong><small>${escapeHtml(section?.label || "Song")}${measure.needsReview ? " · review split" : ""}</small></div>
        <label>Downbeat <input type="range" min="${Math.round(previous)}" max="${Math.round(Math.max(previous, next))}" step="25" value="${Number.isFinite(timestamp) ? Math.round(timestamp) : Math.round(previous)}" data-song-bar-time="${index}" ${Number.isFinite(timestamp) ? "" : "disabled"}><output>${Number.isFinite(timestamp) ? formatTime(timestamp) : "not tapped"}</output></label>
        ${boundaries ? `<div class="song-boundaries">${boundaries}</div>` : ""}${cue}
      </article>`;
    }).join("");
    elements.measureList.querySelectorAll("[data-song-select-bar]").forEach((button) => button.addEventListener("click", () => {
      selectedMeasureId = button.dataset.songSelectBar;
      renderMeasures();
    }));
    elements.measureList.querySelectorAll("[data-song-bar-time]").forEach((input) => input.addEventListener("change", () => {
      project.barStartsMs[Number(input.dataset.songBarTime)] = Number(input.value);
      renderMeasures();
    }));
    elements.measureList.querySelectorAll("[data-song-boundary]").forEach((input) => input.addEventListener("change", () => {
      const [measureId, fractionIndex] = input.dataset.songBoundary.split(":");
      const measure = project.measures.find((item) => item.id === measureId);
      if (!measure) return;
      const index = Number(fractionIndex);
      const lower = Number(measure.chordFractions[index - 1]) + 0.05;
      const upper = index + 1 < measure.chordFractions.length ? Number(measure.chordFractions[index + 1]) - 0.05 : 0.95;
      measure.chordFractions[index] = Math.min(upper, Math.max(lower, Number(input.value) / 100));
      measure.needsReview = false;
      renderMeasures();
    }));
    elements.measureList.querySelectorAll("[data-song-cue]").forEach((input) => input.addEventListener("input", () => {
      const section = project.sections.find((item) => item.id === input.dataset.songCue);
      if (section) section.cue = input.value.slice(0, MAX_CUE_LENGTH);
    }));
  }

  function tapBar() {
    if (tapIndex >= tapStopIndex) return status("The selected tap range is complete. Drag or nudge any marker that needs correction.");
    if (!hasAudioSource()) return status("Choose a recording before tapping bars.", true);
    const value = Math.round(elements.audio.currentTime * 1000);
    const previous = tapIndex > 0 ? project.barStartsMs[tapIndex - 1] : -1;
    if (Number.isFinite(previous) && value <= previous) return status("The next downbeat must come after the previous one.", true);
    project.barStartsMs[tapIndex] = value;
    selectedMeasureId = project.measures[tapIndex].id;
    tapIndex += 1;
    if (tapIndex >= tapStopIndex) status(tapStopIndex < project.measures.length ? "Selected section retapped." : "All bars captured.");
    renderMeasures();
  }

  function undoTap() {
    const last = tapIndex - 1;
    if (last < tapStartIndex || !Number.isFinite(project.barStartsMs[last])) return;
    project.barStartsMs[last] = null;
    tapIndex = last;
    selectedMeasureId = project.measures[last].id;
    renderMeasures();
  }

  function nudgeSelected(delta) {
    const index = project.measures.findIndex((measure) => measure.id === selectedMeasureId);
    if (index < 0 || !Number.isFinite(project.barStartsMs[index])) return;
    const lower = index ? project.barStartsMs[index - 1] + 25 : 0;
    const upper = index + 1 < project.barStartsMs.length && Number.isFinite(project.barStartsMs[index + 1]) ? project.barStartsMs[index + 1] - 25 : Infinity;
    project.barStartsMs[index] = Math.max(lower, Math.min(upper, project.barStartsMs[index] + delta));
    renderMeasures();
  }

  function retapSection() {
    const selected = project.measures.find((measure) => measure.id === selectedMeasureId) || project.measures[0];
    if (!selected) return;
    const sectionIndexes = project.measures.map((measure, index) => measure.sectionId === selected.sectionId ? index : -1).filter((index) => index >= 0);
    const index = sectionIndexes[0];
    tapStartIndex = index;
    tapStopIndex = sectionIndexes.at(-1) + 1;
    project.barStartsMs = project.barStartsMs.map((value, itemIndex) => itemIndex >= index && itemIndex < tapStopIndex ? null : value);
    tapIndex = index;
    selectedMeasureId = project.measures[index].id;
    if (Number.isFinite(project.barStartsMs[index - 1])) elements.audio.currentTime = project.barStartsMs[index - 1] / 1000;
    renderMeasures();
  }

  async function persistProject(options = {}) {
    collectFields();
    await saveProject(project);
    await refreshProjectList();
    if (!options.silent) status("Project metadata saved. Audio was not copied into browser storage.");
  }

  async function refreshProjectList() {
    const projects = (await listProjects()).sort((left, right) => String(right.updatedAt).localeCompare(String(left.updatedAt)));
    elements.projectList.innerHTML = `<option value="">Start a new song</option>${projects.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name || "Untitled song")} · ${escapeHtml(item.key || "")}</option>`).join("")}`;
    if (project && projects.some((item) => item.id === project.id)) elements.projectList.value = project.id;
  }

  async function reopenProject(id) {
    const stored = await loadProject(id);
    if (!stored) return;
    project = migrateProject(stored);
    selectedMeasureId = project.measures[0]?.id || "";
    tapIndex = project.barStartsMs.findIndex((value) => !Number.isFinite(value));
    if (tapIndex < 0) tapIndex = project.measures.length;
    tapStartIndex = 0;
    tapStopIndex = project.measures.length;
    fillFields();
    elements.syncStage.hidden = true;
    elements.editSync.hidden = !project.measures.length;
    elements.practiceStage.hidden = !project.chosenPlan?.events?.length;
    renderMeasures();
    renderLoopSections();
    if (project.source?.type === "built_in") {
      await selectPilot(project.source.builtInTrackId, { preserveProject: true });
      elements.builderDetails.open = false;
      status("Ready. Press Play song and follow the highlighted chord changes.");
    } else {
      setAudioSource("");
      elements.localStatus.textContent = `Relink ${project.audioRef?.filename || "the local recording"}. Filename, size, modified time, and duration must match.`;
      status("Project reopened. Choose the original local recording to relink it.");
    }
  }

  function exportCurrentProject() {
    collectFields();
    const blob = new Blob([exportProjectJson(project)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = doc.createElement("a");
    link.href = url;
    link.download = `${(project.name || "song-project").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase() || "song-project"}.json`;
    link.click();
    URL.revokeObjectURL(url);
    status("Project JSON exported without audio.");
  }

  async function importProjectFile(file) {
    const imported = migrateProject(JSON.parse(await file.text()));
    imported.id = makeId("song-project");
    imported.createdAt = imported.updatedAt = nowIso();
    await saveProject(imported);
    await refreshProjectList();
    await reopenProject(imported.id);
    status("Project imported. Local recordings still require relinking.");
  }

  async function arrange() {
    collectFields();
    if (!hasAudioSource()) return status("Choose or relink the recording before arranging.", true);
    let request;
    try {
      request = buildArrangePayload(project, global.STEEL_RAG_COPEDENTS?.activeContext?.() || { profileId: "emmons-e9-basic" });
    } catch (error) {
      return status(error.message, true);
    }
    elements.arrange.disabled = true;
    status("Building one coherent, validated E9 route…");
    try {
      const response = await fetch("/api/song-practice/arrange", { method: "POST", headers: accessHeaders(true), body: JSON.stringify(request) });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || "Could not build the chord route.");
      project.chosenPlan = payload;
      elements.practiceStage.hidden = false;
      selectedPlanEventId = "";
      renderPractice(true);
      await persistProject({ silent: true });
      status("Ready. Press Play song and follow the highlighted chord changes.");
      elements.playerStage.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      status(error.message, true);
    } finally {
      elements.arrange.disabled = false;
    }
  }

  function sectionForEvent(event) {
    return project.sections.find((section) => section.id === event?.sectionId) || null;
  }

  function renderLoopSections() {
    elements.loopSection.innerHTML = `<option value="all">Whole song</option>${(project.sections || []).map((section) => `<option value="${escapeHtml(section.id)}">${escapeHtml(section.label)}</option>`).join("")}`;
  }

  function loopBounds() {
    const events = project.chosenPlan?.events || [];
    const sectionId = elements.loopSection.value;
    const scoped = sectionId === "all" ? events : events.filter((event) => event.sectionId === sectionId);
    return scoped.length ? { startMs: scoped[0].startMs, endMs: scoped.at(-1).endMs } : null;
  }

  function renderFretboard(position) {
    if (!position || !global.STEEL_RAG_FRETBOARD?.mountPedalSteelFretboard) {
      elements.fretboard.innerHTML = "";
      return;
    }
    const notes = Object.fromEntries(position.notes.map((note) => [String(note.string), note.note]));
    const intervals = Object.fromEntries(position.notes.map((note) => [String(note.string), "chord tone"]));
    const display = {
      id: position.id, label: position.chord, root: position.root, quality: position.quality,
      positionKind: "song_practice", fret: position.fret, strings: position.strings, grip: position.grip,
      pedals: position.pedals || [], levers: position.levers || [], color: "primary", role: "Current chord", function: position.chord,
      keyContext: project.key, family: "song_practice", tier: "validated", colorRole: "primary",
      visibleByDefault: true, sortOrder: 10, notes, intervals,
      explanation: position.instruction, explanationShort: position.instruction, explanationLong: position.instruction,
      validationStatus: "pitch_validated"
    };
    global.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(elements.fretboard, {
      title: `${position.chord} on E9`, maxFret: 24, stringCount: 10,
      positions: [display], highlights: [{ id: position.id, label: position.chord, fret: position.fret, strings: position.strings, pedals: position.pedals || [], levers: position.levers || [] }],
      legend: [{ label: "Validated chord position", color: "primary" }], query: { key: project.key },
      selectedPositionId: position.id, hidePositionTools: true, showNoteLabels: true, showStringLabels: true
    });
  }

  function showPosition(event, position) {
    if (!event || event.status === "rest") {
      elements.positionTitle.textContent = "Rest";
      elements.positionInstruction.textContent = "Leave space.";
      elements.alternatives.innerHTML = "";
      renderFretboard(null);
      return;
    }
    if (!position) {
      elements.positionTitle.textContent = "Manual position needed";
      elements.positionInstruction.textContent = event.warning || "This chord stays in the chart, but the app will not invent an E9 grip.";
      elements.alternatives.innerHTML = "";
      renderFretboard(null);
      return;
    }
    elements.positionTitle.textContent = `${event.chord} · fret ${position.fret} · strings ${position.grip}`;
    elements.positionInstruction.textContent = position.instruction;
    const choices = [event.position, ...(event.alternatives || [])];
    const topNote = [...(position.notes || [])]
      .sort((left, right) => Number(right.pitch) - Number(left.pitch))[0]?.note || "";
    const arrangementParams = new URLSearchParams({
      kind: "user_melody",
      key: project.key || "G",
      notes: topNote,
      chord: event.chord || "",
      voice: "three_voice",
      movement: "best_fit",
      source: "song-practice"
    });
    elements.alternatives.innerHTML = [
      ...choices.map((choice, index) => `<button type="button" data-song-position-choice="${index}">${index === 0 ? "Recommended" : `Alternative ${index}`} · fret ${choice.fret}</button>`),
      topNote ? `<a class="secondary-action" href="/ui/melody-workbench.html?${escapeHtml(arrangementParams.toString())}">Arrange a melody over this chord →</a>` : ""
    ].join("");
    elements.alternatives.querySelectorAll("[data-song-position-choice]").forEach((button) => button.addEventListener("click", () => showPosition(event, choices[Number(button.dataset.songPositionChoice)])));
    renderFretboard(position);
  }

  function renderChordStrip(events, display) {
    const activeIndex = Math.max(0, events.indexOf(display));
    const start = Math.max(0, activeIndex - 1);
    elements.chordStrip.innerHTML = events.slice(start, start + 8).map((event, index) => {
      const isActive = start + index === activeIndex;
      return `<span class="${isActive ? "is-current" : ""}">${escapeHtml(event.chord || "Rest")}</span>`;
    }).join("");
  }

  function renderPractice(force = false) {
    const events = project?.chosenPlan?.events || [];
    if (!events.length) return;
    const timeMs = elements.audio.currentTime * 1000;
    const timeline = activeTimelineState(events, timeMs);
    const current = timeline.current;
    const next = timeline.next;
    const display = current || next;
    const displayStateId = display ? `${current ? "current" : "upcoming"}:${display.id}` : "";
    if (display && (force || selectedPlanEventId !== displayStateId)) {
      selectedPlanEventId = displayStateId;
      const currentSection = sectionForEvent(current);
      const nextSection = sectionForEvent(next);
      elements.currentSection.textContent = current ? (currentSection?.label || "Song") : "Get ready";
      elements.nextSection.textContent = nextSection?.label || "End";
      elements.currentChord.textContent = current ? (current.chord || "Rest") : "—";
      elements.nextChord.textContent = next?.chord || "End";
      elements.currentCue.textContent = (currentSection || nextSection)?.cue || "No cue";
      renderChordStrip(events, display);
      showPosition(display, display.position);
      elements.warning.hidden = display.status !== "manual_position_needed";
      elements.warning.textContent = display.warning || "";
    }
    const countdownTarget = current?.endMs ?? next?.startMs;
    elements.countdown.textContent = Number.isFinite(countdownTarget) ? `${Math.max(0, (countdownTarget - timeMs) / 1000).toFixed(1)} s` : "—";
    if (elements.loopEnabled.checked) {
      const bounds = loopBounds();
      if (bounds && timeMs >= bounds.endMs - 25) elements.audio.currentTime = Math.max(0, bounds.startMs / 1000);
    }
  }

  function animationTick() {
    elements.audioTime.textContent = formatTime(elements.audio.currentTime * 1000);
    elements.playToggle.textContent = elements.audio.paused ? "▶ Play song" : "Pause song";
    renderPractice();
    animationFrame = global.requestAnimationFrame(animationTick);
  }

  function startNewProject() {
    setAudioSource("");
    project = blankProject();
    tapIndex = 0;
    tapStartIndex = 0;
    tapStopIndex = 0;
    selectedMeasureId = "";
    elements.syncStage.hidden = true;
    elements.editSync.hidden = true;
    elements.practiceStage.hidden = true;
    elements.localFile.value = "";
    elements.localStatus.textContent = "The recording stays in this tab and is never uploaded. Paste a chord chart below; timing is created automatically.";
    fillFields();
    elements.projectList.value = "";
    status("");
  }

  function bind() {
    if (bindingsReady) return;
    bindingsReady = true;
    elements.close.addEventListener("click", () => api.close());
    elements.newProject.addEventListener("click", startNewProject);
    elements.sourceButtons.forEach((button) => button.addEventListener("click", () => selectSource(button.dataset.songSource)));
    elements.parse.addEventListener("click", async () => {
      if (parseCurrentChart()) await arrange();
    });
    elements.playToggle.addEventListener("click", async () => {
      if (!hasAudioSource()) return status("Choose or relink a recording before playback.", true);
      try {
        if (elements.audio.paused) await elements.audio.play();
        else elements.audio.pause();
        elements.playToggle.textContent = elements.audio.paused ? "▶ Play song" : "Pause song";
      } catch (_playbackError) {
        status("Playback could not start. Use the audio controls and try again.", true);
      }
    });
    elements.skipBack.addEventListener("click", () => {
      elements.audio.currentTime = Math.max(0, elements.audio.currentTime - 5);
      renderPractice(true);
    });
    elements.skipForward.addEventListener("click", () => {
      elements.audio.currentTime = Math.min(Number.isFinite(elements.audio.duration) ? elements.audio.duration : Infinity, elements.audio.currentTime + 5);
      renderPractice(true);
    });
    elements.tap.addEventListener("click", tapBar);
    elements.undo.addEventListener("click", undoTap);
    elements.retap.addEventListener("click", retapSection);
    elements.nudgeBack.addEventListener("click", () => nudgeSelected(-50));
    elements.nudgeForward.addEventListener("click", () => nudgeSelected(50));
    elements.editSync.addEventListener("click", () => {
      elements.builderDetails.open = true;
      elements.syncStage.hidden = false;
      elements.syncStage.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    elements.save.addEventListener("click", () => persistProject().catch((error) => status(error.message, true)));
    elements.export.addEventListener("click", exportCurrentProject);
    elements.arrange.addEventListener("click", arrange);
    elements.rate.addEventListener("change", () => {
      elements.audio.playbackRate = Number(elements.rate.value);
      elements.audio.preservesPitch = true;
      elements.audio.webkitPreservesPitch = true;
    });
    elements.offset.addEventListener("change", () => { project.syncOffsetMs = Number(elements.offset.value || 0); renderPractice(true); });
    elements.projectList.addEventListener("change", () => elements.projectList.value && reopenProject(elements.projectList.value).catch((error) => status(error.message, true)));
    elements.importButton.addEventListener("click", () => elements.importFile.click());
    elements.importFile.addEventListener("change", () => {
      const file = elements.importFile.files?.[0];
      if (file) importProjectFile(file).catch((error) => status(error.message, true));
      elements.importFile.value = "";
    });
    elements.localFile.addEventListener("change", () => {
      const file = elements.localFile.files?.[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      setAudioSource(url, true);
      elements.audio.addEventListener("loadedmetadata", () => {
        const identity = localAudioIdentity(file, elements.audio.duration * 1000);
        const expected = project.audioRef?.kind === "local" ? project.audioRef : null;
        if (expected && !matchesLocalAudioIdentity(expected, identity)) {
          setAudioSource("");
          elements.localStatus.textContent = "That file does not match the saved filename, size, modified time, and duration. Choose the original recording.";
          status("Local recording mismatch; relink was not accepted.", true);
          return;
        }
        project.source = { type: "local", builtInTrackId: "" };
        project.audioRef = { kind: "local", ...identity };
        project.durationMs = identity.durationMs;
        if (project.chosenPlan?.events?.length) {
          elements.practiceStage.hidden = false;
          renderPractice(true);
        }
        elements.localStatus.textContent = `${identity.filename} linked for this tab. Audio will not be saved or uploaded.`;
        elements.builderDetails.open = true;
        status("Local recording linked. Paste the chord chart, then choose Create practice track automatically. You do not need to tap every bar.");
      }, { once: true });
    });
    doc.addEventListener("keydown", (event) => {
      if (event.code !== "Space" || elements.workspace.hidden || elements.syncStage.hidden) return;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(doc.activeElement?.tagName)) return;
      event.preventDefault();
      tapBar();
    });
    global.addEventListener("beforeunload", revokeLocalAudio);
    animationFrame = global.requestAnimationFrame(animationTick);
  }

  api.configure = async function configure(options = {}) {
    session = options.session || session;
    enabled = Boolean(options.enabled);
    bind();
    startNewProject();
    try {
      await refreshProjectList();
    } catch (_storageError) {
      status("This browser cannot open IndexedDB right now. You can practice, but saving is unavailable until browser storage is restored.", true);
    }
    if (enabled) await loadCatalog();
    return { enabled, catalogCount: catalog.length };
  };

  api.open = function open() {
    if (!enabled) return false;
    elements.workspace.hidden = false;
    elements.editor.hidden = true;
    elements.workspace.scrollIntoView({ behavior: "smooth", block: "start" });
    return true;
  };

  api.close = function close() {
    elements.workspace.hidden = true;
    elements.editor.hidden = false;
    return true;
  };
})(typeof window !== "undefined" ? window : globalThis);
