(function () {
  "use strict";

  const payloadsByKey = window.STEEL_RAG_E9_EXPLORER_PAYLOADS || {};
  const payloadsByCopedent = window.STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT || {};
  const fallbackPayload = window.STEEL_RAG_E9_EXPLORER_PAYLOAD;
  const explorerDataApi = window.STEEL_RAG_E9_EXPLORER_DATA;
  const fretboardApi = window.STEEL_RAG_FRETBOARD;
  const musicRules = window.STEEL_RAG_E9_MUSIC_RULES;

  if (!musicRules) {
    throw new Error("E9 music rules boundary is required before the Explorer script.");
  }
  const explorerConfig = window.STEEL_RAG_E9_EXPLORER_CONFIG;
  if (!explorerConfig) {
    throw new Error("Explorer configuration boundary is required before the Explorer script.");
  }
  const {
    GRIP_VOCABULARY_OPTIONS,
    GRIP_ROLE_OPTIONS,
    EXPLORE_MODES,
    PATH_FAMILIES,
    KEY_OPTIONS,
    HARMONY_LABELS,
    FRET_RANGE_OPTIONS,
    NOTATION_MODES,
    PITCH_REGISTER_MODES,
    NOTE_WORKFLOWS,
    NOTE_TARGET_MODES,
    CHORD_FINDER_ROOT_OPTIONS,
    CHORD_FINDER_QUALITY_LABELS,
    CHORD_FINDER_QUALITY_ORDER,
    CHORD_FINDER_CONTROL_SCOPES,
    TASK_CARD_META,
  } = explorerConfig;

  const DEFAULT_COPEDENT_ID = "emmons-e9-basic";
  const CORE_GROUPS = musicRules.CORE_GROUPS;
  const PATH_GROUPS = musicRules.PATH_GROUPS;
  const ADVANCED_GROUPS = musicRules.ADVANCED_GROUPS;
  const E_LOWER_POCKET_GROUPS = musicRules.E_LOWER_POCKET_GROUPS;
  const TWO_STRING_GROUPS = musicRules.TWO_STRING_GROUPS;
  const FIVE_EIGHT_GROUPS = musicRules.FIVE_EIGHT_GROUPS;
  const EXTENDED_VOICING_GRIPS = musicRules.EXTENDED_VOICING_GRIPS;
  const DOMINANT_9TH_GRIPS = musicRules.DOMINANT_9TH_GRIPS;
  const TWO_STRING_DISPLAY_GROUPS = musicRules.TWO_STRING_DISPLAY_GROUPS;
  const GRIP_REGISTRY = musicRules.GRIP_REGISTRY;
  const NOTE_CONTROL_STATES = musicRules.NOTE_CONTROL_STATES;
  const COMMON_VOICING_GRIPS = musicRules.COMMON_VOICING_GRIPS;
  const CHORD_QUALITY_PATTERNS = musicRules.CHORD_QUALITY_PATTERNS;
  const CHROMATIC_SHARP_NOTES = musicRules.CHROMATIC_SHARP_NOTES;
  const CHROMATIC_FLAT_NOTES = musicRules.CHROMATIC_FLAT_NOTES;
  const MAJOR_SCALE_INTERVALS = musicRules.MAJOR_SCALE_INTERVALS;
  const CHORD_FINDER_QUALITY_OPTIONS = CHORD_FINDER_QUALITY_ORDER
    .map((id) => chordQualityById(id))
    .filter(Boolean)
    .map((quality) => ({ id: quality.id, label: CHORD_FINDER_QUALITY_LABELS[quality.id] || quality.label }));
  const MAJOR_SCALE_SEQUENCES = musicRules.MAJOR_SCALE_SEQUENCES;
  const NATURAL_MINOR_SCALE_SEQUENCES = musicRules.NATURAL_MINOR_SCALE_SEQUENCES;

  const els = {
    key: document.getElementById("explorer-key"),
    copedent: document.getElementById("explorer-copedent"),
    exploreMode: document.getElementById("explorer-explore-mode"),
    taskCards: document.querySelectorAll("[data-explorer-task-card]"),
    modeTabs: document.querySelectorAll("[data-explorer-mode-tab]"),
    scale: document.getElementById("explorer-scale"),
    harmony: document.getElementById("explorer-harmony"),
    harmonyControl: document.getElementById("explorer-harmony-control"),
    contextStrip: document.getElementById("explorer-context-strip"),
    gripVocabulary: document.getElementById("explorer-grip-vocabulary"),
    gripVocabularyControl: document.getElementById("explorer-grip-vocabulary-control"),
    stringGroup: document.getElementById("explorer-string-group"),
    stringGroupControl: document.getElementById("explorer-string-group-control"),
    pathFamily: document.getElementById("explorer-path-family"),
    pathFamilyControl: document.getElementById("explorer-path-family-control"),
    scaleNotes: document.getElementById("explorer-scale-notes"),
    resultCount: document.getElementById("explorer-result-count"),
    notationModeButtons: document.querySelectorAll("[data-explorer-notation-mode]"),
    pitchRegisterButtons: document.querySelectorAll("[data-explorer-pitch-register]"),
    stringActionLabelToggle: document.getElementById("explorer-string-action-label-toggle"),
    topIntervalFilter: document.getElementById("explorer-top-interval-filter"),
    fretRangeFilter: document.getElementById("explorer-fret-range-filter"),
    copedentDialog: document.getElementById("explorer-copedent-dialog"),
    copedentOpen: document.getElementById("explorer-copedent-open"),
    copedentClose: document.getElementById("explorer-copedent-close"),
    glossaryDialog: document.getElementById("explorer-glossary-dialog"),
    glossaryOpen: document.getElementById("explorer-glossary-open"),
    glossaryClose: document.getElementById("explorer-glossary-close"),
    copedentChart: document.getElementById("explorer-copedent-chart"),
    controlPreview: document.getElementById("explorer-control-impact-preview"),
    noteFinder: document.getElementById("explorer-note-finder"),
    voicingIdentifier: document.getElementById("explorer-voicing-identifier"),
    chordFinder: document.getElementById("explorer-chord-finder"),
    activeResults: document.getElementById("explorer-active-results"),
    fretboard: document.getElementById("explorer-fretboard"),
    rowList: document.getElementById("explorer-row-list"),
    selectedDetail: document.getElementById("explorer-selected-detail"),
    empty: document.getElementById("explorer-empty"),
    tooltip: document.getElementById("explorer-tooltip"),
  };

  let selectedRowId = "";
  let selectedTaskCard = "explore-grip";
  let selectedImpactControlIds = new Set();
  let selectedTopFilter = "all";
  let selectedFretRange = "core";
  let selectedNoteControlStateId = "open";
  let selectedNoteTargetIndex = 0;
  let selectedNoteTargetMode = "scale";
  let selectedNoteWorkflow = "find";
  let selectedNoteStringFilter = "all";
  let selectedGripTargetId = "scale-triad";
  let selectedGripVocabulary = "core";
  let selectedSingleGripVocabulary = "core";
  let selectedGripRole = "all";
  let selectedGripCandidateId = "";
  let selectedSyncEventId = "s3-f3-open";
  let chordFinderQuery = "";

  let selectedChordRoot = "F";
  let selectedChordQuality = "major7";
  let selectedChordControlScope = "common";
  let selectedChordCandidateId = "";
  let selectedChordMapFilter = "all";
  let voicingFret = 3;
  let selectedVoicingStrings = [3, 4, 5];
  let selectedVoicingControlIds = new Set();
  let voicingUiWarning = "";
  let drillFeedback = null;
  let pinnedNoteCell = { stringNumber: 3, fret: 3 };
  let previewNoteCell = null;
  let notationMode = "notes";
  let pitchRegisterMode = "off";
  let showStringActionLabels = false;
  let lastCopedentDialogOpener = null;
  let lastGlossaryDialogOpener = null;
  let currentRows = [];
  let currentMarkerGroups = [];

  function createQueryParams(search) {
    const query = String(search || "").replace(/^\?/, "");
    if (typeof URLSearchParams !== "undefined") {
      return new URLSearchParams(query);
    }
    const values = {};
    if (query) {
      query.split("&").forEach((pair) => {
        const [rawKey, rawValue = ""] = pair.split("=");
        if (!rawKey) return;
        const key = decodeURIComponent(rawKey.replace(/\+/g, " "));
        values[key] = decodeURIComponent(rawValue.replace(/\+/g, " "));
      });
    }
    return {
      get(key) {
        return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null;
      },
      keys() {
        return Object.keys(values)[Symbol.iterator]();
      },
    };
  }

  function startupSearchParams() {
    try {
      return createQueryParams(window.location?.search || "");
    } catch (_error) {
      return createQueryParams("");
    }
  }

  function normalizeQueryKey(value) {
    const text = String(value || "").trim();
    const aliases = {
      "C#": "Db",
      "D#": "Eb",
      "F#": "Gb",
      "G#": "Ab",
      "A#": "Bb",
    };
    return aliases[text] || text;
  }

  function safeSelectValue(select, value) {
    if (!select || value === undefined || value === null || String(value).trim() === "") {
      return false;
    }
    const wanted = String(value).trim();
    const match = Array.from(select.options || []).find((item) => item.value === wanted && !item.disabled);
    if (!match) {
      return false;
    }
    select.value = wanted;
    Array.from(select.options || []).forEach((item) => {
      item.selected = item === match;
    });
    return true;
  }

  function queryModeValue(value) {
    const token = String(value || "").trim().toLowerCase();
    const aliases = {
      single: EXPLORE_MODES.single,
      "single-grip": EXPLORE_MODES.single,
      grip: EXPLORE_MODES.single,
      path: EXPLORE_MODES.path,
      "harmonized-scale-path": EXPLORE_MODES.path,
      movement: EXPLORE_MODES.path,
      note: EXPLORE_MODES.note,
      "single-note": EXPLORE_MODES.note,
      "single-note-finder": EXPLORE_MODES.note,
      voicing: EXPLORE_MODES.voicing,
      "voicing-identifier": EXPLORE_MODES.voicing,
      chord: EXPLORE_MODES.chord,
      "chord-finder": EXPLORE_MODES.chord,
      "chord-voicing-finder": EXPLORE_MODES.chord,
    };
    return aliases[token] || "";
  }

  function isValidExploreMode(value) {
    return Object.values(EXPLORE_MODES).includes(value);
  }

  function defaultTaskCardForMode(mode) {
    if (mode === EXPLORE_MODES.chord) {
      return "find-chord";
    }
    if (mode === EXPLORE_MODES.note) {
      return "find-note";
    }
    if (mode === EXPLORE_MODES.path) {
      return "walk-harmonized-scale";
    }
    if (mode === EXPLORE_MODES.voicing) {
      return "identify-voicing";
    }
    return "explore-grip";
  }

  function normalizeQueryQuality(value) {
    const token = String(value || "").trim().toLowerCase().replace(/[\s_-]+/g, "");
    const aliases = {
      major: "major",
      maj: "major",
      minor: "minor",
      min: "minor",
      dominant7: "dominant7",
      dom7: "dominant7",
      seven: "dominant7",
      "7": "dominant7",
      major7: "major7",
      maj7: "major7",
      minor7: "minor7",
      min7: "minor7",
      minor7flat5: "minor7flat5",
      m7b5: "minor7flat5",
      diminished: "diminished",
      dim: "diminished",
      augmented: "augmented",
      aug: "augmented",
      sus2: "sus2",
      sus4: "sus4",
      dominant9: "dominant9",
      minor9: "minor9",
      major9: "major9",
    };
    return aliases[token] || "";
  }

  function queryVocabularyForGrip(group) {
    const wanted = String(group || "").trim();
    if (!wanted) return "";
    return gripVocabularyOptions()
      .map((item) => item.id)
      .filter((id) => id !== "all")
      .find((id) => gripVocabularyGroups(id).has(wanted)) || "";
  }

  function applyExplorerQueryState() {
    const params = startupSearchParams();
    if (!Array.from(params.keys()).length) {
      return;
    }
    const mode = queryModeValue(params.get("mode"));
    if (mode && els.exploreMode) {
      els.exploreMode.value = mode;
      selectedTaskCard = params.get("source") === "movement-card" && mode === EXPLORE_MODES.path
        ? "study-movement-path"
        : defaultTaskCardForMode(mode);
    }
    const copedentId = String(params.get("copedent") || "").trim();
    if (copedentId && els.copedent) {
      safeSelectValue(els.copedent, copedentId);
    }
    const key = normalizeQueryKey(params.get("key") || params.get("root"));
    if (key) {
      safeSelectValue(els.key, key);
    }
    const quality = normalizeQueryQuality(params.get("quality"));
    if (params.get("root")) {
      const root = normalizeQueryKey(params.get("root"));
      if (CHORD_FINDER_ROOT_OPTIONS.includes(root)) {
        selectedChordRoot = root;
      }
    }
    if (quality) {
      selectedChordQuality = quality;
    }
    const grip = params.get("grip") || params.get("strings");
    const vocabulary = queryVocabularyForGrip(grip);
    if (vocabulary) {
      selectedSingleGripVocabulary = vocabulary;
      selectedGripVocabulary = vocabulary;
    }
    const fret = Number(params.get("fret"));
    if (Number.isFinite(fret) && fret > 15) {
      selectedFretRange = fret >= 10 ? "high" : "all";
    }
    updateControls();
    safeSelectValue(els.scale, params.get("scale"));
    if (grip) {
      safeSelectValue(els.stringGroup, grip);
    }
  }

  function availableKeys() {
    const manifestKeys = explorerDataApi?.keys?.(selectedCopedentId()) || [];
    const sourcePayloads = Object.keys(payloadsByKey).length ? payloadsByKey : payloadsForSelectedCopedent();
    const keys = manifestKeys.length ? manifestKeys : Object.keys(sourcePayloads);
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
    return els.copedent?.options?.[els.copedent.selectedIndex]?.value
      || els.copedent?.value
      || fallbackPayload?.selected_copedent?.id
      || DEFAULT_COPEDENT_ID;
  }

  function payloadsForSelectedCopedent() {
    const selectedId = selectedCopedentId();
    if (payloadsByCopedent[selectedId]) {
      return payloadsByCopedent[selectedId];
    }
    if (!explorerDataApi?.load || selectedId === DEFAULT_COPEDENT_ID) {
      return payloadsByKey;
    }
    return {};
  }

  function activePayload() {
    const payloads = payloadsForSelectedCopedent();
    const exactPayload = payloads[els.key.value]
      || (selectedCopedentId() === DEFAULT_COPEDENT_ID ? payloadsByKey[els.key.value] : null);
    if (exactPayload) {
      return exactPayload;
    }
    return (
      fallbackPayload?.query?.key === els.key.value
      && (!explorerDataApi?.load || selectedCopedentId() === DEFAULT_COPEDENT_ID)
    ) ? fallbackPayload : null;
  }

  function ensureSelectedPayload() {
    if (activePayload() || !explorerDataApi?.load) {
      return Boolean(activePayload());
    }
    els.key.disabled = true;
    if (els.copedent) {
      els.copedent.disabled = true;
    }
    els.empty.hidden = false;
    els.empty.textContent = "Loading validated Explorer data…";
    return explorerDataApi.load(selectedCopedentId(), els.key.value)
      .then(() => Boolean(activePayload()))
      .catch(() => {
        els.empty.textContent = "Explorer data could not be loaded for this key and copedent.";
        return false;
      })
      .finally(() => {
        els.key.disabled = false;
        if (els.copedent) {
          els.copedent.disabled = false;
        }
      });
  }

  function refreshAfterPayloadChange() {
    const pending = ensureSelectedPayload();
    if (pending === true) {
      updateControls();
      render();
      return;
    }
    if (pending && typeof pending.then === "function") {
      pending.then((loaded) => {
        if (loaded) {
          updateControls();
          render();
        }
      });
    }
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

  function controlDisplayLabel(control, emptyText = "Control") {
    return formatValue(control?.display_label || control?.label || control?.id, emptyText);
  }

  function formatInterval(value) {
    return musicRules.formatInterval(value);
  }

  function formatTheoryText(value) {
    return musicRules.formatTheoryText(value);
  }

  function normalizeIntervalToken(value) {
    return musicRules.normalizeIntervalToken(value);
  }

  function notationModeLabel() {
    return NOTATION_MODES.find((mode) => mode.id === notationMode)?.label || "Notes";
  }

  function activePitchRegisterMode() {
    return PITCH_REGISTER_MODES.some((mode) => mode.id === pitchRegisterMode) ? pitchRegisterMode : "off";
  }

  function pitchRegisterModeLabel() {
    return PITCH_REGISTER_MODES.find((mode) => mode.id === activePitchRegisterMode())?.label || "Off";
  }

  function registerLabelFor(register, fallbackNote = "") {
    const mode = activePitchRegisterMode();
    const note = formatValue(register?.display_note || register?.pitch_class || fallbackNote, "");
    if (mode === "scientific") {
      return formatValue(register?.scientific_pitch, note);
    }
    if (mode === "band") {
      return [note, formatValue(register?.octave_band, "")]
        .filter(Boolean)
        .join(" · ");
    }
    return note;
  }

  function registerRowsLowToHigh(registers) {
    return toArray(registers)
      .filter((entry) => entry && typeof entry === "object")
      .slice()
      .sort((a, b) => Number(a.pitch_value ?? 0) - Number(b.pitch_value ?? 0));
  }

  function notesWithRegisterForRow(row) {
    if (activePitchRegisterMode() === "off") {
      return [];
    }
    const rowRegisters = registerRowsLowToHigh(row?.notes_with_register);
    if (rowRegisters.length) {
      return rowRegisters.map((entry) => registerLabelFor(entry, entry.display_note || entry.pitch_class));
    }
    const registerMap = row?.note_registers;
    if (registerMap && typeof registerMap === "object" && !Array.isArray(registerMap)) {
      return registerRowsLowToHigh(Object.values(registerMap))
        .map((entry) => registerLabelFor(entry, entry.display_note || entry.pitch_class));
    }
    return [];
  }

  function notesWithRegisterText(row) {
    return formatValue(notesWithRegisterForRow(row), "");
  }

  function cellRegisterLabel(cell) {
    return registerLabelFor(cell?.finalRegister, cell?.finalNote);
  }

  function cellOpenRegisterLabel(cell) {
    if (activePitchRegisterMode() === "scientific") {
      return formatValue(cell?.openScientificPitch, cell?.openNoteAtFret);
    }
    if (activePitchRegisterMode() === "band") {
      return [formatValue(cell?.openNoteAtFret, ""), formatValue(cell?.openOctaveBand, "")]
        .filter(Boolean)
        .join(" · ");
    }
    return formatValue(cell?.openNoteAtFret, "");
  }

  function registerEntriesForCells(cells) {
    const sorted = toArray(cells)
      .filter((cell) => cell?.finalRegister)
      .slice()
      .sort((a, b) => Number(a.finalRegister.pitch_value ?? 0) - Number(b.finalRegister.pitch_value ?? 0));
    return sorted.map((cell, index) => {
      let voiceRole = "middle";
      if (sorted.length === 1) {
        voiceRole = "single";
      } else if (index === 0) {
        voiceRole = "bottom";
      } else if (index === sorted.length - 1) {
        voiceRole = "top";
      }
      return {
        ...cell.finalRegister,
        voice_role: voiceRole,
      };
    });
  }

  function noteRegistersByStringFromCells(cells) {
    return Object.fromEntries(registerEntriesForCells(cells).map((entry) => [String(entry.string), entry]));
  }

  function intervalAsNns(value) {
    return musicRules.intervalAsNns(value);
  }

  function intervalAsRoman(value) {
    return musicRules.intervalAsRoman(value);
  }

  function intervalAsNumberQuality(value) {
    return musicRules.intervalAsNumberQuality(value);
  }

  function formatIntervalForNotation(value) {
    return musicRules.formatIntervalForNotation(value, notationMode);
  }

  function activeScaleSequence() {
    if (notationMode === "notes") {
      return activeScaleNotes();
    }
    const source = els.scale.value === "natural_minor" ? NATURAL_MINOR_SCALE_SEQUENCES : MAJOR_SCALE_SEQUENCES;
    return source[notationMode] || [];
  }

  function activeScaleNotes() {
    const notes = activePayload()?.query?.display_scale_notes?.[els.scale.value];
    return Array.isArray(notes) ? notes : [];
  }

  function noteAlternates(note) {
    return musicRules.noteAlternates(note);
  }

  function pitchClassForNote(note) {
    return musicRules.pitchClassForNote(note);
  }

  function displayNoteForPitchClass(pitchClass) {
    return musicRules.displayNoteForPitchClass(pitchClass, { scaleNotes: activeScaleNotes() });
  }

  function prefersFlatSpelling(key = activeKey()) {
    return musicRules.prefersFlatSpelling ? musicRules.prefersFlatSpelling(key) : /b/.test(formatValue(key, ""));
  }

  function displayNoteForPitchClassInKey(pitchClass, key = activeKey()) {
    return musicRules.displayNoteForPitchClassInKey(pitchClass, key);
  }

  function noteAtFret(openNote, fret, semitoneDelta = 0) {
    return musicRules.noteAtFret(openNote, fret, semitoneDelta, { scaleNotes: activeScaleNotes() });
  }

  function scaleDegreeIndexForNote(note) {
    return musicRules.scaleDegreeIndexForNote(note, activeScaleNotes());
  }

  function notationLabelForFinalNote(note, fallbackInterval = "") {
    return musicRules.notationLabelForFinalNote(note, fallbackInterval, {
      notationMode,
      scaleNotes: activeScaleNotes(),
      scaleSequence: activeScaleSequence(),
    });
  }

  function activeCopedent() {
    return activePayload()?.selected_copedent || null;
  }

  function copedentChartRows() {
    return toArray(activeCopedent()?.chart?.rows)
      .slice()
      .sort((a, b) => Number(a.string || 0) - Number(b.string || 0));
  }

  function copedentControls() {
    return toArray(activeCopedent()?.controls);
  }

  function controlById(controlId) {
    return copedentControls().find((control) => control.id === controlId) || null;
  }

  function activeNoteControlState() {
    const state = NOTE_CONTROL_STATES.find((item) => item.id === selectedNoteControlStateId) || NOTE_CONTROL_STATES[0];
    const availableIds = new Set(copedentControls().map((control) => control.id));
    return {
      ...state,
      controls: state.controls.filter((controlId) => availableIds.has(controlId)),
    };
  }

  function noteControlLabel(controlId) {
    return controlDisplayLabel(controlById(controlId), controlId);
  }

  function noteControlLabels(controlIds) {
    return controlIds.length ? controlIds.map(noteControlLabel) : ["Open"];
  }

  function chartRowForString(stringNumber) {
    return copedentChartRows().find((row) => Number(row.string) === Number(stringNumber)) || null;
  }

  function controlCellForString(controlId, stringNumber) {
    const row = chartRowForString(stringNumber);
    return row?.cells?.[controlId] || null;
  }

  function noteControlCellsForString(stringNumber, controlIds = activeNoteControlState().controls) {
    return controlIds
      .map((controlId) => ({ controlId, control: controlById(controlId), cell: controlCellForString(controlId, stringNumber) }))
      .filter((item) => item.cell);
  }

  function noteControlDeltaForString(stringNumber, controlIds = activeNoteControlState().controls) {
    return noteControlCellsForString(stringNumber, controlIds)
      .reduce((total, item) => total + (Number(item.cell.semitones) || 0), 0);
  }

  function noteFinderTargets() {
    if (selectedNoteTargetMode === "intervals") {
      const rootPitchClass = pitchClassForNote(activeKey());
      const intervalLabels = ["1 (root)", "♭2 (b2)", "2", "♭3 (b3)", "3", "4", "♭5 / ♯4", "5", "♭6 (b6)", "6", "♭7 (b7)", "7"];
      return intervalLabels.map((label, index) => ({
        index,
        note: displayNoteForPitchClassInKey(rootPitchClass + index, activeKey()),
        label,
        pitchClass: ((rootPitchClass + index) % 12 + 12) % 12,
        interval: intervalNameFromSemitones(index),
      }));
    }
    const notes = activeScaleNotes();
    const labels = activeScaleSequence();
    return notes.map((note, index) => ({
      index,
      note,
      label: labels[index] || note,
      pitchClass: pitchClassForNote(note),
    }));
  }

  function selectedNoteFinderTarget() {
    return noteFinderTargets().find((target) => target.index === selectedNoteTargetIndex) || noteFinderTargets()[0] || null;
  }

  function activeNoteWorkflow() {
    return NOTE_WORKFLOWS.find((workflow) => workflow.id === selectedNoteWorkflow) || NOTE_WORKFLOWS[0];
  }

  function noteControlStateById(stateId) {
    return NOTE_CONTROL_STATES.find((item) => item.id === stateId) || NOTE_CONTROL_STATES[0];
  }

  function availableNoteControlStates() {
    const availableIds = new Set(copedentControls().map((control) => control.id));
    return NOTE_CONTROL_STATES
      .map((state) => ({
        ...state,
        controls: state.controls.filter((controlId) => availableIds.has(controlId)),
      }))
      .filter((state) => !state.controls.length || state.controls.length === NOTE_CONTROL_STATES.find((item) => item.id === state.id)?.controls.length);
  }

  function noteControlStateIdForControlIds(controlIds) {
    const wanted = new Set(toArray(controlIds).map(String));
    const match = availableNoteControlStates().find((state) => {
      if (state.controls.length !== wanted.size) {
        return false;
      }
      return state.controls.every((controlId) => wanted.has(controlId));
    });
    return match?.id || "open";
  }

  function noteStringFilterOptions() {
    return [{ value: "all", label: "All strings" }].concat(copedentChartRows().map((row) => ({
      value: String(row.string),
      label: `String ${row.string}`,
    })));
  }

  function noteMatchesStringFilter(cell) {
    return selectedNoteStringFilter === "all" || String(cell.stringNumber) === selectedNoteStringFilter;
  }

  function noteCellState(stringNumber, fret, controlState = activeNoteControlState()) {
    const row = chartRowForString(stringNumber);
    const openStringNote = formatValue(row?.open_note, "");
    const activeControls = controlState.controls;
    const affectedCells = noteControlCellsForString(stringNumber, activeControls);
    const delta = noteControlDeltaForString(stringNumber, activeControls);
    const resolved = musicRules.resolveE9Note({
      stringNumber,
      fret,
      controls: activeControls,
      copedent: activeCopedent(),
      scaleNotes: activeScaleNotes(),
    });
    const openNoteAtFret = resolved.openNoteAtFret || noteAtFret(openStringNote, fret, 0);
    const finalNote = resolved.finalNote || noteAtFret(openStringNote, fret, delta);
    const target = selectedNoteFinderTarget();
    const finalPitchClass = pitchClassForNote(finalNote);
    const isTargetMatch = target && target.pitchClass !== null && finalPitchClass === target.pitchClass;
    const direction = delta > 0 ? "raises" : delta < 0 ? "lowers" : "changes";
    let explanation = "Open position: no pedals or levers are active.";
    if (activeControls.length && affectedCells.length) {
      explanation = `${noteControlLabels(activeControls).join(" + ")} ${direction} this string from ${openNoteAtFret} to ${finalNote}.`;
    } else if (activeControls.length) {
      explanation = `Selected controls do not change this string; final note remains ${finalNote}.`;
    }
    return {
      stringNumber: Number(stringNumber),
      fret: Number(fret),
      openStringNote,
      openNoteAtFret,
      finalNote,
      openPitchValueAtFret: resolved.openPitchValueAtFret,
      finalPitchValue: resolved.finalPitchValue,
      openScientificPitch: resolved.openScientificPitch,
      finalScientificPitch: resolved.finalScientificPitch,
      openOctaveBand: resolved.openOctaveBand,
      finalOctaveBand: resolved.finalOctaveBand,
      finalRegister: resolved.finalRegister,
      activeControlIds: activeControls,
      activeControlLabel: controlState.label,
      affectedCells,
      isAffected: Boolean(activeControls.length && affectedCells.length),
      isTargetMatch,
      notationValue: notationLabelForFinalNote(finalNote),
      intervalFromKeyRoot: intervalNameFromSemitones(finalPitchClass - pitchClassForNote(activeKey())),
      explanation,
    };
  }

  function compactControlLetter(value) {
    const text = String(value || "").toLowerCase();
    if (!text || text.includes("no change")) {
      return "";
    }
    if (text.includes("b-to-bb") || text.includes("b to bb") || text.includes("b-to-b") || text.includes("lkv") || text.includes("vertical") || text === "v") {
      return "V";
    }
    if (/\ba\s*(pedal)?\b/.test(text) || text === "a") {
      return "A";
    }
    if (/\bb\s*(pedal)?\b/.test(text) || text === "b") {
      return "B";
    }
    if (/\bc\s*(pedal)?\b/.test(text) || text === "c") {
      return "C";
    }
    if (text.includes("e-raise") || text.includes("e raise") || text.includes("f lever") || text === "f") {
      return "F";
    }
    if (text.includes("e-lower") || text.includes("e lower") || text.includes("e lever") || text === "e") {
      return "E";
    }
    if (text.includes("d-lower") || text.includes("d lower") || text.includes("d lever") || text.includes("half-stop") || text === "d") {
      return "D";
    }
    if (text.includes("g-lower") || text.includes("g raise") || text.includes("g lever") || text.includes("raise/lower") || text === "g") {
      return "G";
    }
    return "";
  }

  function compactControlLettersForCell(cell) {
    return Array.from(new Set(toArray(cell.affectedCells)
      .map((entry) => compactControlLetter(entry.controlId || entry.control?.id || entry.control?.display_label || entry.control?.label))
      .filter(Boolean))).join("");
  }

  function markerLabelForCell(cell) {
    return `${cell.stringNumber}${cell.isAffected ? compactControlLettersForCell(cell) : ""}`;
  }

  function stringActionLabelsFromCells(cells) {
    return Object.fromEntries(cells.map((cell) => [cell.stringNumber, markerLabelForCell(cell)]));
  }

  function perStringChangesFromCells(cells, options = {}) {
    return Object.fromEntries(cells.map((cell) => [
      cell.stringNumber,
      options.useFromTo
        ? {
          from: cell.openNoteAtFret,
          to: cell.finalNote,
          controls: cell.isAffected ? cell.activeControlLabel : "no change",
        }
        : {
          open_at_fret: cell.openNoteAtFret,
          final_note: cell.finalNote,
          controls: cell.isAffected ? cell.activeControlLabel : "no change",
        },
    ]));
  }

  function displayNoteForActiveKey(pitchClass) {
    const scaleNote = activeScaleNotes().find((note) => pitchClassForNote(note) === pitchClass);
    return scaleNote || displayNoteForPitchClass(pitchClass);
  }

  function intervalNameFromSemitones(semitones) {
    return musicRules.intervalNameFromSemitones(semitones);
  }

  function intervalLabelsAgainstRoot(notes, rootPitchClass) {
    return musicRules.intervalLabelsAgainstRoot(notes, rootPitchClass);
  }

  function dominantRootPitchClass() {
    const target = musicRules.dominantTargetForKey(activeKey(), {
      notationMode,
      scaleNotes: activeScaleNotes(),
    });
    return target?.rootPitchClass ?? null;
  }

  function dominantTargetForActiveKey() {
    return musicRules.dominantTargetForKey(activeKey(), {
      notationMode,
      scaleNotes: activeScaleNotes(),
    });
  }

  function voicingFunctionForRoot(rootPitchClass, quality) {
    return musicRules.voicingFunctionForRoot(rootPitchClass, quality, {
      key: activeKey(),
      scaleType: els.scale.value,
      scaleNotes: activeScaleNotes(),
    });
  }

  function chordLabel(rootPitchClass, quality) {
    return musicRules.chordLabel(rootPitchClass, quality, {
      key: activeKey(),
      scaleType: els.scale.value,
      scaleNotes: activeScaleNotes(),
    });
  }

  function intervalRoleLabel(interval) {
    return musicRules.intervalRoleLabel(interval);
  }

  function omittedIntervalLabel(interval) {
    return musicRules.omittedIntervalLabel(interval);
  }

  function partialChordLabel(rootPitchClass, quality, missingIntervals) {
    return musicRules.partialChordLabel(rootPitchClass, quality, missingIntervals, {
      key: activeKey(),
      scaleType: els.scale.value,
      scaleNotes: activeScaleNotes(),
    });
  }

  function isExtendedChordQuality(quality) {
    return musicRules.isExtendedChordQuality(quality);
  }

  function extendedQualityGate(quality, intervals) {
    return musicRules.extendedQualityGate(quality, intervals);
  }

  function chordConfidence(quality, exact, missingIntervals, intervals) {
    return musicRules.chordConfidence(quality, exact, missingIntervals, intervals);
  }

  function qualityPriority(quality) {
    return musicRules.qualityPriority ? musicRules.qualityPriority(quality) : 0;
  }

  function voicingExplanation(label, quality, intervals, missingIntervals) {
    return musicRules.voicingExplanation(label, quality, intervals, missingIntervals);
  }

  function dominantColorIdentity(notes, fallbackLabel = "") {
    return musicRules.dominantColorIdentity(notes, {
      key: activeKey(),
      scaleType: els.scale.value,
      scaleNotes: activeScaleNotes(),
      notationMode,
    }, fallbackLabel);
  }

  function identifyVoicing(notes) {
    return musicRules.identifyVoicing(notes, {
      key: activeKey(),
      scaleType: els.scale.value,
      scaleNotes: activeScaleNotes(),
      scaleSequence: activeScaleSequence(),
      notationMode,
    });
  }

  function parseVoicingStrings(value) {
    const strings = Array.isArray(value)
      ? value.map(Number)
      : String(value || "")
        .split(/[,\s-]+/)
        .map((part) => part.trim())
        .filter(Boolean)
        .map(Number);
    const invalid = strings.filter((stringNumber) => !Number.isInteger(stringNumber) || stringNumber < 1 || stringNumber > 10);
    const seen = new Set();
    const duplicates = strings.filter((stringNumber) => {
      if (seen.has(stringNumber)) {
        return true;
      }
      seen.add(stringNumber);
      return false;
    });
    if (!strings.length) {
      return { strings: [], warning: "Select 1, 2, 3, or 4 strings to identify the voicing." };
    }
    if (invalid.length) {
      return { strings: [], warning: "Strings must be E9 string numbers from 1 through 10." };
    }
    if (duplicates.length) {
      return { strings: [], warning: "Each string can only appear once in the voicing." };
    }
    if (strings.length > 4) {
      return { strings: [], warning: "Choose no more than 4 strings for this identifier." };
    }
    return { strings: strings.sort((a, b) => a - b), warning: "" };
  }

  function voicingGripLabel(strings) {
    const grip = strings.join("-");
    if (strings.length === 1) {
      return "Single-string pitch check";
    }
    const metadata = gripMetadata(grip);
    if (metadata) {
      return metadata.label;
    }
    return "Not a common musical grip";
  }

  function voicingGripWarning(strings) {
    const grip = strings.join("-");
    if (COMMON_VOICING_GRIPS.has(grip) || strings.length === 1) {
      return "";
    }
    return "This is not a common musical grip on E9. The notes are still calculated, but treat the result as a pitch check rather than a standard voicing.";
  }

  function activeVoicingControlState() {
    const availableIds = new Set(copedentControls().map((control) => control.id));
    const orderedControls = copedentControls()
      .map((control) => control.id)
      .filter((controlId) => availableIds.has(controlId) && selectedVoicingControlIds.has(controlId));
    return {
      id: orderedControls.length ? orderedControls.join("+") : "open",
      label: noteControlLabels(orderedControls).join(" + "),
      controls: orderedControls,
    };
  }

  function voicingControlButtonsHtml() {
    const activeState = activeVoicingControlState();
    const buttons = copedentControls().map((control) => `
      <button
        class="explorer-voicing-identifier__chip${activeState.controls.includes(control.id) ? " is-selected" : ""}"
        type="button"
        data-voicing-control="${escapeHtml(control.id)}"
        aria-pressed="${activeState.controls.includes(control.id) ? "true" : "false"}"
      >${escapeHtml(controlDisplayLabel(control, "Control"))}</button>
    `);
    buttons.push(`
      <button
        class="explorer-voicing-identifier__chip${activeState.controls.length ? "" : " is-selected"}"
        type="button"
        data-voicing-control-clear
        aria-pressed="${activeState.controls.length ? "false" : "true"}"
      >Clear</button>
    `);
    return buttons.join("");
  }

  function voicingStringButtonsHtml() {
    return Array.from({ length: 10 }, (_, index) => index + 1).map((stringNumber) => `
      <button
        class="explorer-voicing-identifier__chip${selectedVoicingStrings.includes(stringNumber) ? " is-selected" : ""}"
        type="button"
        data-voicing-string="${escapeHtml(stringNumber)}"
        aria-pressed="${selectedVoicingStrings.includes(stringNumber) ? "true" : "false"}"
      >${escapeHtml(stringNumber)}</button>
    `).join("");
  }

  function voicingStringStates() {
    const fret = Number.parseInt(voicingFret, 10);
    const parsedStrings = parseVoicingStrings(selectedVoicingStrings);
    if (!Number.isInteger(fret) || fret < 1 || fret > 10) {
      return { warning: "Fret must be a whole number from 1 through 10.", strings: [], cells: [] };
    }
    if (parsedStrings.warning) {
      return { warning: parsedStrings.warning, strings: [], cells: [] };
    }
    const controlState = activeVoicingControlState();
    const cells = parsedStrings.strings.map((stringNumber) => noteCellState(stringNumber, fret, controlState));
    return {
      warning: "",
      fret,
      strings: parsedStrings.strings,
      gripLabel: voicingGripLabel(parsedStrings.strings),
      gripRoles: gripRoleText(parsedStrings.strings.join("-")),
      gripNote: gripMetadata(parsedStrings.strings.join("-"))?.note || "",
      gripExplanation: gripMetadata(parsedStrings.strings.join("-"))?.explanation || "",
      gripWatchOut: gripMetadata(parsedStrings.strings.join("-"))?.watchOut || "",
      gripWarning: voicingGripWarning(parsedStrings.strings),
      controlState,
      cells,
    };
  }

  function voicingSyntheticRow(result, identity) {
    const displayNotes = {};
    result.cells.forEach((cell) => {
      displayNotes[cell.stringNumber] = {
        note: cell.finalNote,
        interval: notationLabelForFinalNote(cell.finalNote),
      };
    });
    const topCell = result.cells[0];
    return {
      id: `voicing:${activeKey()}:${result.fret}:${result.strings.join("-")}:${result.controlState.id}`,
      key: activeKey(),
      scale_type: els.scale.value,
      harmony_type: "voicing_identifier",
      chord_name: identity.label,
      chord_function: identity.functionText,
      fret: result.fret,
      string_group: result.strings.join("-"),
      strings: result.strings,
      pedals: result.controlState.controls,
      levers: [],
      notes: result.cells.map((cell) => cell.finalNote),
      intervals: identity.intervals,
      display_notes: displayNotes,
      display_top_voice: {
        note: topCell?.finalNote || "",
        interval: topCell ? notationLabelForFinalNote(topCell.finalNote) : "",
        string: topCell?.stringNumber || "",
      },
      display_summary: `${identity.label} at fret ${result.fret} on strings ${result.strings.join("-")}`,
      explanation: `Computed from ${activeCopedent()?.label || "the selected copedent"}; no retrieval is used.`,
      voicing_status: identity.voicing_status,
      present_tones: identity.present_tones || [],
      omitted_tones: identity.omitted_tones || identity.missingIntervals || [],
      confidence: identity.confidence,
      alternate_readings: identity.alternate_readings || identity.alternates || [],
      warnings: identity.warnings || [],
      per_string_changes: perStringChangesFromCells(result.cells),
      string_action_labels: stringActionLabelsFromCells(result.cells),
    };
  }

  function decorateNoteCellForRender(cell, selectedGrip = selectedGripCandidate()) {
    const gripStrings = new Set(toArray(selectedGrip?.strings).map(Number));
    const isGripMatch = selectedGrip
      && Number(selectedGrip.fret) === Number(cell.fret)
      && gripStrings.has(Number(cell.stringNumber));
    return {
      ...cell,
      isTargetMatch: cell.isTargetMatch && noteMatchesStringFilter(cell),
      isGripMatch: Boolean(isGripMatch),
    };
  }

  function noteChangeRowsAtFret(fret = pinnedNoteCell.fret, controlState = activeNoteControlState()) {
    return copedentChartRows().map((row) => {
      const cell = noteCellState(row.string, fret, controlState);
      return {
        ...cell,
        row,
        controlChanges: noteControlCellsForString(row.string, controlState.controls),
      };
    });
  }

  function gripTargetOptions() {
    const notes = activeScaleNotes();
    const labels = activeScaleSequence();
    const triadNotes = [notes[0], notes[2], notes[4]].filter(Boolean);
    const triadLabels = [labels[0], labels[2], labels[4]].filter(Boolean);
    const selectedTarget = selectedNoteFinderTarget();
    const dominantTarget = dominantTargetForActiveKey();
    const options = [
      {
        id: "scale-triad",
        label: notationMode === "notes" ? triadNotes.join("-") : triadLabels.join("-"),
        description: "The 1-3-5 chord tones for the selected key and scale.",
        pitchClasses: triadNotes.map(pitchClassForNote).filter((value) => value !== null),
        preferFret: null,
      },
      {
        id: "near-fret-3",
        label: `${notationMode === "notes" ? triadNotes.join("-") : triadLabels.join("-")} near fret 3`,
        description: "A beginner-friendly nearby triad search.",
        pitchClasses: triadNotes.map(pitchClassForNote).filter((value) => value !== null),
        preferFret: 3,
      },
      {
        id: "current-target",
        label: `Target ${selectedTarget?.label || "note"}`,
        description: "Find grips that include the current target value.",
        pitchClasses: selectedTarget?.pitchClass === null || selectedTarget?.pitchClass === undefined ? [] : [selectedTarget.pitchClass],
        preferFret: null,
      },
    ];
    if (dominantTarget && ["extended", "all"].includes(selectedGripVocabulary)) {
      options.splice(1, 0, {
        id: "dominant-v7",
        label: `Dominant 7 / V7: ${dominantTarget.label}`,
        description: dominantTarget.description,
        pitchClasses: dominantTarget.pitchClasses,
        requiredPitchClasses: dominantTarget.requiredPitchClasses,
        rootPitchClass: dominantTarget.rootPitchClass,
        preferFret: null,
        kind: "dominant7",
      });
    }
    return options.filter((target) => target.pitchClasses.length);
  }

  function selectedGripTarget() {
    const options = gripTargetOptions();
    return options.find((option) => option.id === selectedGripTargetId) || options[0] || null;
  }

  function rowPitchClasses(row) {
    return rowNoteLabels(row)
      .map(pitchClassForNote)
      .filter((value) => value !== null);
  }

  function rowMatchesGripTarget(row, target) {
    const pitchClasses = rowPitchClasses(row);
    if (target?.kind === "dominant7") {
      return pitchClasses.length
        && pitchClasses.every((pitchClass) => target.pitchClasses.includes(pitchClass))
        && target.requiredPitchClasses.some((pitchClass) => pitchClasses.includes(pitchClass));
    }
    return target?.pitchClasses?.every((pitchClass) => pitchClasses.includes(pitchClass));
  }

  function gripMetadata(group) {
    return musicRules.gripMetadata(group);
  }

  function gripRoleLabel(roleId) {
    return GRIP_ROLE_OPTIONS.find((option) => option.id === roleId)?.label || roleId.replace(/_/g, " ");
  }

  function gripRoleText(group) {
    const roles = gripMetadata(group)?.roles || [];
    return roles.map(gripRoleLabel).join(", ");
  }

  function gripTierLabel(group) {
    return musicRules.gripTierLabel(group);
  }

  function gripHasRole(group, roleId) {
    if (roleId === "all") {
      return true;
    }
    return Boolean(gripMetadata(group)?.roles?.includes(roleId));
  }

  function gripVocabularyShowsRoleFilter(vocabularyId = selectedGripVocabulary) {
    return ["two_string", "all", "extended"].includes(vocabularyId);
  }

  function gripVocabularyGroups(vocabularyId = "core") {
    if (vocabularyId === "extended") {
      return new Set(GRIP_REGISTRY
        .filter((entry) => ["core", "path", "extended"].includes(entry.tier))
        .map((entry) => entry.strings));
    }
    if (vocabularyId === "song_tab") {
      return new Set(GRIP_REGISTRY
        .filter((entry) => ["core", "path", "extended", "song_tab_vocabulary"].includes(entry.tier))
        .map((entry) => entry.strings));
    }
    if (vocabularyId === "e_lower_pockets") {
      return new Set(GRIP_REGISTRY
        .filter((entry) => entry.tier === "e_lower_pocket")
        .map((entry) => entry.strings));
    }
    if (vocabularyId === "two_string") {
      return new Set(GRIP_REGISTRY
        .filter((entry) => entry.tier === "two_string")
        .map((entry) => entry.strings));
    }
    if (vocabularyId === "all") {
      return new Set(GRIP_REGISTRY.map((entry) => entry.strings));
    }
    return new Set(GRIP_REGISTRY
      .filter((entry) => entry.tier === "core")
      .map((entry) => entry.strings));
  }

  function gripTierSortValue(group) {
    const tierOrder = {
      core: 0,
      path: 1,
      extended: 2,
      song_tab_vocabulary: 3,
      e_lower_pocket: 4,
      two_string: 5,
      advanced: 6,
      heuristic: 7,
      unusual: 8,
    };
    return tierOrder[gripMetadata(group)?.tier || "unusual"] ?? 8;
  }

  function gripVocabularyLabel(vocabularyId = "core") {
    return gripVocabularyOptions().find((option) => option.id === vocabularyId)?.label || "Core";
  }

  function gripVocabularyOptions() {
    return GRIP_VOCABULARY_OPTIONS;
  }

  function syncGripRoleWithVocabulary() {
    if (!GRIP_ROLE_OPTIONS.some((option) => option.id === selectedGripRole)) {
      selectedGripRole = "all";
    }
    if (!gripVocabularyShowsRoleFilter(selectedGripVocabulary)) {
      selectedGripRole = "all";
      return;
    }
    if (selectedGripRole !== "all") {
      const groups = Array.from(gripVocabularyGroups(selectedGripVocabulary));
      if (!groups.some((group) => gripHasRole(group, selectedGripRole))) {
        selectedGripRole = "all";
      }
    }
  }

  function selectedGripVocabularyOption() {
    return gripVocabularyOptions().find((option) => option.id === selectedGripVocabulary) || gripVocabularyOptions()[0];
  }

  function allGripOptionLabel(vocabularyId, harmony) {
    if (harmony === "two_string_harmonized") {
      return "All 2-string groups";
    }
    const labels = {
      core: "All core grips",
      extended: "All extended grips",
      song_tab: "All song/tab vocabulary grips",
      e_lower_pockets: "All E-lower pocket grips",
      two_string: "All two-string grips",
      all: "All legitimate grips",
    };
    return labels[vocabularyId] || `All ${gripVocabularyLabel(vocabularyId).toLowerCase()} grips`;
  }

  function practicalGroupsForGripVocabulary() {
    return gripVocabularyGroups(selectedGripVocabulary);
  }

  function computedDominantGripRows(target) {
    if (target?.kind !== "dominant7") {
      return [];
    }
    const groups = Array.from(DOMINANT_9TH_GRIPS);
    const states = availableNoteControlStates();
    const frets = visibleNoteFinderFrets();
    const rows = [];
    groups.forEach((group) => {
      const strings = group.split("-").map(Number);
      states.forEach((state) => {
        frets.forEach((fret) => {
          const cells = strings.map((stringNumber) => noteCellState(stringNumber, fret, state));
          const pitchClasses = Array.from(new Set(cells.map((cell) => pitchClassForNote(cell.finalNote)).filter((value) => value !== null)));
          const allInsideDominant = pitchClasses.length && pitchClasses.every((pitchClass) => target.pitchClasses.includes(pitchClass));
          const hasFlatSeven = pitchClasses.includes((target.rootPitchClass + 10) % 12);
          const hasRootOrThird = pitchClasses.includes(target.rootPitchClass) || pitchClasses.includes((target.rootPitchClass + 4) % 12);
          if (!allInsideDominant || !hasFlatSeven || !hasRootOrThird) {
            return;
          }
          if (state.controls.length && !cells.some((cell) => cell.isAffected)) {
            return;
          }
          const identity = dominantColorIdentity(cells.map((cell) => cell.finalNote));
          if (!identity) {
            return;
          }
          const displayNotes = {};
          cells.forEach((cell) => {
            displayNotes[cell.stringNumber] = {
              note: cell.finalNote,
              interval: intervalNameFromSemitones(pitchClassForNote(cell.finalNote) - target.rootPitchClass),
            };
          });
          const topCell = cells[0];
          rows.push({
            id: `computed-v7:${activeKey()}:${group}:${fret}:${state.id}`,
            key: activeKey(),
            scale_type: els.scale.value,
            harmony_type: "dominant_v7_grip",
            chord_name: identity.label,
            chord_function: identity.functionText,
            fret,
            string_group: group,
            strings,
            pedals: state.controls,
            levers: [],
            notes: cells.map((cell) => cell.finalNote),
            intervals: identity.intervals,
            display_notes: displayNotes,
            display_top_voice: {
              note: topCell?.finalNote || "",
              interval: topCell ? notationLabelForFinalNote(topCell.finalNote) : "",
              string: topCell?.stringNumber || "",
            },
            display_summary: identity.label,
            explanation: identity.explanation || `Computed from ${activeCopedent()?.label || "the selected copedent"}; no retrieval is used.`,
            warnings: identity.partial ? [`Partial V7: missing ${identity.missingIntervals.map(formatInterval).join(", ") || "one or more chord tones"}.`] : [],
            per_string_changes: perStringChangesFromCells(cells),
            string_action_labels: stringActionLabelsFromCells(cells),
          });
        });
      });
    });
    return rows;
  }

  function computedPracticalGripRows(target, groups) {
    if (!target || target.kind === "dominant7") {
      return [];
    }
    const states = availableNoteControlStates();
    const frets = visibleNoteFinderFrets();
    const rows = [];
    Array.from(groups).forEach((group) => {
      const strings = group.split("-").map(Number).filter(Number.isFinite);
      if (!strings.length || strings.length > 4) {
        return;
      }
      states.forEach((state) => {
        frets.forEach((fret) => {
          const cells = strings.map((stringNumber) => noteCellState(stringNumber, fret, state));
          const pitchClasses = Array.from(new Set(cells.map((cell) => pitchClassForNote(cell.finalNote)).filter((value) => value !== null)));
          const completeMatch = target.pitchClasses.every((pitchClass) => pitchClasses.includes(pitchClass));
          const partialMatch = selectedGripRole !== "all" && pitchClasses.some((pitchClass) => target.pitchClasses.includes(pitchClass));
          if (!completeMatch && !partialMatch) {
            return;
          }
          if (state.controls.length && !cells.some((cell) => cell.isAffected)) {
            return;
          }
          const identity = identifyVoicing(cells.map((cell) => cell.finalNote));
          const displayNotes = {};
          cells.forEach((cell) => {
            displayNotes[cell.stringNumber] = {
              note: cell.finalNote,
              interval: notationLabelForFinalNote(cell.finalNote),
            };
          });
          const topCell = cells[0];
          rows.push({
            id: `computed-grip:${activeKey()}:${group}:${fret}:${state.id}`,
            key: activeKey(),
            scale_type: els.scale.value,
            harmony_type: "computed_practical_grip",
            chord_name: identity.label,
            chord_function: identity.functionText,
            fret,
            string_group: group,
            strings,
            pedals: state.controls,
            levers: [],
            notes: cells.map((cell) => cell.finalNote),
            intervals: identity.intervals,
            display_notes: displayNotes,
            display_top_voice: {
              note: topCell?.finalNote || "",
              interval: topCell ? notationLabelForFinalNote(topCell.finalNote) : "",
              string: topCell?.stringNumber || "",
            },
            display_summary: `${identity.label} on strings ${group}`,
            explanation: `Computed from ${activeCopedent()?.label || "the selected copedent"} practical grip vocabulary; no retrieval is used.`,
            warnings: completeMatch ? [] : ["Partial voicing: this grip contains part of the target sound, not every chord tone."],
            per_string_changes: perStringChangesFromCells(cells),
            string_action_labels: stringActionLabelsFromCells(cells),
          });
        });
      });
    });
    return rows;
  }

  function gripFinderCandidates() {
    const target = selectedGripTarget();
    if (!target) {
      return [];
    }
    const practicalGroups = practicalGroupsForGripVocabulary();
    const generatedRows = computedDominantGripRows(target).concat(computedPracticalGripRows(target, practicalGroups));
    return rowsForScale(els.scale.value)
      .filter((row) => practicalGroups.has(row.string_group))
      .filter((row) => gripHasRole(row.string_group, selectedGripRole))
      .filter((row) => rowInRange(row))
      .filter((row) => rowMatchesGripTarget(row, target))
      .concat(generatedRows)
      .filter((row) => gripHasRole(row.string_group, selectedGripRole))
      .sort((a, b) => {
        const aCore = gripTierSortValue(a.string_group);
        const bCore = gripTierSortValue(b.string_group);
        if (aCore !== bCore) {
          return aCore - bCore;
        }
        if (target.preferFret !== null) {
          const byDistance = Math.abs(Number(a.fret) - target.preferFret) - Math.abs(Number(b.fret) - target.preferFret);
          if (byDistance) {
            return byDistance;
          }
        }
        const byFret = Number(a.fret || 0) - Number(b.fret || 0);
        return byFret || String(a.id || "").localeCompare(String(b.id || ""));
      })
      .slice(0, 8);
  }

  function normalizeChordFinderText(value) {
    return musicRules.normalizeChordFinderText(value);
  }

  function chordQualityById(id) {
    return musicRules.chordQualityById(id);
  }

  function parseChordFinderQuality(rawValue, options = {}) {
    return musicRules.parseChordFinderQuality(rawValue, options);
  }

  function romanDegreeInfo(value) {
    return musicRules.romanDegreeInfo(value);
  }

  function defaultQualityForDegree(degree) {
    return musicRules.defaultQualityForDegree(degree);
  }

  function buildChordFinderTarget(rootPitchClass, quality, options = {}) {
    return musicRules.buildChordFinderTarget(rootPitchClass, quality, {
      input: chordFinderQuery,
      contextKey: activeKey(),
      ...options,
    });
  }

  function parseFunctionChordFinderQuery(value) {
    return musicRules.parseFunctionChordFinderQuery(value);
  }

  function parseDirectChordFinderQuery(value) {
    return musicRules.parseDirectChordFinderQuery(value);
  }

  function chordFinderQualityDisplayLabel(qualityOrId) {
    const id = typeof qualityOrId === "string" ? qualityOrId : qualityOrId?.id;
    return CHORD_FINDER_QUALITY_LABELS[id] || formatValue(qualityOrId?.label || id, "");
  }

  function selectedChordFinderTarget() {
    const rootPitchClass = pitchClassForNote(selectedChordRoot);
    const quality = chordQualityById(selectedChordQuality) || chordQualityById("major");
    if (rootPitchClass === null || !quality) {
      return {
        ok: false,
        message: "Choose a root and chord quality to search practical E9 voicings.",
      };
    }
    const rootLabel = displayNoteForPitchClassInKey(rootPitchClass, selectedChordRoot);
    return buildChordFinderTarget(rootPitchClass, quality, {
      source: "structured",
      input: `${rootLabel}${quality.suffix || ""}`,
      contextKey: selectedChordRoot,
      rootLabel,
      message: `Using ${rootLabel} ${chordFinderQualityDisplayLabel(quality)} from the structured chord picker.`,
    });
  }

  function parseChordFinderQuery(value) {
    if (arguments.length === 0) {
      return selectedChordFinderTarget();
    }
    return musicRules.parseChordFinderQuery(value);
  }

  function chordFinderRootOptionsHtml() {
    return CHORD_FINDER_ROOT_OPTIONS.map((note) => option(note, note, selectedChordRoot)).join("");
  }

  function chordFinderQualityOptionsHtml() {
    return CHORD_FINDER_QUALITY_OPTIONS.map((quality) => option(quality.id, quality.label, selectedChordQuality)).join("");
  }

  function chordFinderControlScopeOptionsHtml() {
    return CHORD_FINDER_CONTROL_SCOPES.map((scope) => option(scope.id, scope.label, selectedChordControlScope)).join("");
  }

  function controlStateForIds(ids) {
    const availableIds = new Set(copedentControls().map((control) => control.id));
    const controls = toArray(ids).filter((controlId) => availableIds.has(controlId));
    return {
      id: controls.length ? controls.join("+") : "open",
      label: noteControlLabels(controls).join(" + "),
      controls,
    };
  }

  function chordFinderControlStates() {
    const scope = CHORD_FINDER_CONTROL_SCOPES.find((item) => item.id === selectedChordControlScope) || CHORD_FINDER_CONTROL_SCOPES[1];
    const seen = new Set();
    return scope.controlCombos
      .map(controlStateForIds)
      .filter((state) => {
        if (seen.has(state.id)) {
          return false;
        }
        seen.add(state.id);
        return true;
      });
  }

  function chordFinderControlStatesForGroup(group) {
    const states = chordFinderControlStates();
    if (selectedChordControlScope !== "open" && E_LOWER_POCKET_GROUPS.has(group) && !states.some((state) => state.id === "E-lower")) {
      return [...states, controlStateForIds(["E-lower"])];
    }
    return states;
  }

  function chordTargetIntervalForPitchClass(pitchClass, target) {
    const normalized = ((Number(pitchClass) % 12) + 12) % 12;
    const match = target.toneLabels.find((tone) => ((target.rootPitchClass + tone.interval) % 12) === normalized);
    return match ? match.interval : null;
  }

  function chordFinderQualityGate(target, presentIntervals) {
    return musicRules.chordFinderQualityGate(target, presentIntervals);
  }

  function chordFinderConfidence(target, presentIntervals, omittedIntervals) {
    return musicRules.chordFinderConfidence(target, presentIntervals, omittedIntervals);
  }

  function chordFinderCandidateScore(row, target, presentIntervals, omittedIntervals) {
    const tierPenalty = gripTierSortValue(row.string_group) * 6;
    const controlPenalty = normalizePedals(row).length * 3;
    const missingPenalty = omittedIntervals.reduce((total, interval) => {
      if (interval === 7) {
        return total + 2;
      }
      if (interval === 0) {
        return total + 6;
      }
      if (interval === 3 || interval === 4) {
        return total + 14;
      }
      if (interval === 10 || interval === 11 || interval === 2) {
        return total + 12;
      }
      return total + 5;
    }, 0);
    const definitionBonus = presentIntervals.filter((interval) => target.quality.required.includes(interval)).length * 14;
    const completeBonus = omittedIntervals.length ? 0 : 48;
    return 100 + completeBonus + definitionBonus - missingPenalty - tierPenalty - controlPenalty - Math.abs(Number(row.fret) - 8) * 0.3;
  }

  function chordFinderCandidateSort(a, b) {
    return (b.chord_finder?.score || 0) - (a.chord_finder?.score || 0)
      || Number(a.fret || 0) - Number(b.fret || 0)
      || String(a.id || "").localeCompare(String(b.id || ""));
  }

  function chordFinderCandidateLimit(options = {}) {
    if (options.ignoreRange) {
      return 96;
    }
    return selectedGripVocabulary === "all" ? 48 : 24;
  }

  function chordFinderMustKeepCandidate(row) {
    const finder = row?.chord_finder || {};
    const tier = gripMetadata(row?.string_group)?.tier;
    const omitted = toArray(finder.omittedIntervals);
    return ["e_lower_pocket", "song_tab_vocabulary", "extended", "path"].includes(tier)
      && omitted.length === 0
      && String(finder.confidence || "").toLowerCase().startsWith("high");
  }

  function limitChordFinderCandidates(rows, options = {}) {
    const sorted = [...rows].sort(chordFinderCandidateSort);
    const limited = sorted.slice(0, chordFinderCandidateLimit(options));
    sorted
      .filter(chordFinderMustKeepCandidate)
      .forEach((row) => {
        if (!limited.some((candidate) => candidate.id === row.id)) {
          limited.push(row);
        }
      });
    return limited.sort(chordFinderCandidateSort);
  }

  function chordFinderRowFromCells(target, group, fret, controlState, cells) {
    const targetPitchClasses = new Set(target.pitchClasses);
    const entries = [];
    const intervals = [];
    const extraNotes = [];
    cells.forEach((cell) => {
      const pitchClass = pitchClassForNote(cell.finalNote);
      const interval = chordTargetIntervalForPitchClass(pitchClass, target);
      if (pitchClass === null || !targetPitchClasses.has(pitchClass) || interval === null) {
        extraNotes.push(cell.finalNote);
        return;
      }
      intervals.push(interval);
      entries.push({ cell, interval });
    });
    const presentIntervals = Array.from(new Set(intervals)).sort((a, b) => a - b);
    const omittedIntervals = target.quality.intervals.filter((interval) => !presentIntervals.includes(interval));
    if (extraNotes.length || presentIntervals.length < 2 || !chordFinderQualityGate(target, presentIntervals)) {
      return null;
    }
    const displayNotes = {};
    entries.forEach(({ cell, interval }) => {
      displayNotes[cell.stringNumber] = {
        note: cell.finalNote,
        interval: intervalNameFromSemitones(interval),
      };
    });
    const strings = group.split("-").map(Number).filter(Number.isFinite);
    const topCell = entries.find(({ cell }) => Number(cell.stringNumber) === strings[0])?.cell || entries[0]?.cell;
    const notesWithRegister = registerEntriesForCells(entries.map(({ cell }) => cell));
    const topRegister = notesWithRegister.find((entry) => Number(entry.string) === Number(topCell?.stringNumber));
    const row = {
      id: `chord-finder:${target.label}:${group}:${fret}:${controlState.id}`,
      key: activeKey(),
      scale_type: els.scale.value,
      harmony_type: "chord_voicing_finder",
      chord_name: omittedIntervals.length ? `${target.label}(${omittedIntervals.map((interval) => `no${omittedIntervalLabel(interval)}`).join(", ")})` : target.label,
      chord_function: target.source === "function" ? target.message : `${target.quality.label} target`,
      chord_quality: target.quality.label,
      fret,
      string_group: group,
      strings,
      pedals: controlState.controls,
      levers: [],
      notes: entries.map(({ cell }) => cell.finalNote),
      intervals: presentIntervals.map(intervalNameFromSemitones),
      display_notes: displayNotes,
      display_top_voice: {
        note: topCell?.finalNote || "",
        interval: topCell ? intervalNameFromSemitones(chordTargetIntervalForPitchClass(pitchClassForNote(topCell.finalNote), target)) : "",
        string: topCell?.stringNumber || "",
        scientific_pitch: topRegister?.scientific_pitch || "",
        pitch_value: topRegister?.pitch_value ?? "",
        octave_band: topRegister?.octave_band || "",
      },
      note_registers: noteRegistersByStringFromCells(entries.map(({ cell }) => cell)),
      notes_with_register: notesWithRegister,
      display_summary: `${omittedIntervals.length ? "Partial " : ""}${target.label} on strings ${group}`,
      explanation_summary: `${omittedIntervals.length ? "Partial voicing" : "Complete voicing"} for ${target.label}: present ${presentIntervals.map(intervalRoleLabel).join(", ")}${omittedIntervals.length ? `; omitted ${omittedIntervals.map(intervalRoleLabel).join(", ")}` : ""}.`,
      warnings: omittedIntervals.length ? [`Partial ${target.label}: omitted ${omittedIntervals.map(intervalRoleLabel).join(", ")}.`] : [],
      per_string_changes: perStringChangesFromCells(cells, { useFromTo: true }),
      string_action_labels: stringActionLabelsFromCells(cells),
      chord_finder: {
        target,
        presentIntervals,
        omittedIntervals,
        presentTones: presentIntervals.map((interval) => `${intervalRoleLabel(interval)} (${displayNoteForPitchClassInKey(target.rootPitchClass + interval, target.contextKey)})`),
        omittedTones: omittedIntervals.map((interval) => `${intervalRoleLabel(interval)} (${displayNoteForPitchClassInKey(target.rootPitchClass + interval, target.contextKey)})`),
        confidence: chordFinderConfidence(target, presentIntervals, omittedIntervals),
        gripTier: gripTierLabel(group),
        whyGrip: gripMetadata(group)?.explanation || "",
        gripWatchOut: gripMetadata(group)?.watchOut || "",
      },
    };
    row.chord_finder.score = chordFinderCandidateScore(row, target, presentIntervals, omittedIntervals);
    return row;
  }

  function chordFinderGroups() {
    const groups = new Set(gripVocabularyGroups(selectedGripVocabulary));
    return Array.from(groups)
      .filter((group) => group.split("-").filter(Boolean).length <= 4);
  }

  function chordFinderCandidates(target = parseChordFinderQuery(), options = {}) {
    if (!target?.ok) {
      return [];
    }
    const range = options.ignoreRange ? { min: 0, max: 24 } : activeRangeOption();
    const rows = [];
    chordFinderGroups().forEach((group) => {
      const strings = group.split("-").map(Number).filter(Number.isFinite);
      if (!strings.length) {
        return;
      }
      chordFinderControlStatesForGroup(group).forEach((state) => {
        for (let fret = range.min; fret <= range.max; fret += 1) {
          const cells = strings.map((stringNumber) => noteCellState(stringNumber, fret, state));
          if (state.controls.length && !cells.some((cell) => cell.isAffected)) {
            continue;
          }
          const row = chordFinderRowFromCells(target, group, fret, state, cells);
          if (row) {
            rows.push(row);
          }
        }
      });
    });
    return limitChordFinderCandidates(rows, options);
  }

  function selectedChordCandidate(rows = chordFinderCandidates()) {
    return rows.find((row) => row.id === selectedChordCandidateId) || rows[0] || null;
  }

  function chordFinderFretBucket(row) {
    const fret = Number(row?.fret);
    if (!Number.isFinite(fret)) {
      return "";
    }
    if (fret <= 4) {
      return "low";
    }
    if (fret <= 10) {
      return "mid";
    }
    return "high";
  }

  function chordFinderCompleteness(row) {
    const omitted = toArray(row?.chord_finder?.omittedIntervals);
    if (!omitted.length) {
      return "complete";
    }
    if (omitted.map(Number).includes(0)) {
      return "rootless";
    }
    return "partial";
  }

  function chordFinderControlFilter(row) {
    const controls = normalizePedals(row);
    if (!controls.length) {
      return "open";
    }
    return controls.some((control) => String(control).toLowerCase().includes("lower") || String(control).toLowerCase().includes("raise"))
      ? "levers"
      : "pedals";
  }

  function chordFinderTierFilter(row) {
    const tier = String(gripMetadata(row?.string_group)?.tier || "").toLowerCase();
    if (["core", "path", "extended", "song_tab_vocabulary", "e_lower_pocket", "two_string"].includes(tier)) {
      return tier;
    }
    return isAdvanced(row) ? "advanced" : "extended";
  }

  function chordFinderMapFilterOptions(rows) {
    const options = [
      { id: "all", label: "All" },
      { id: "open", label: "Open" },
      { id: "pedals", label: "Pedals" },
      { id: "levers", label: "Levers" },
      { id: "low", label: "Low frets" },
      { id: "mid", label: "Mid frets" },
      { id: "high", label: "High frets" },
      { id: "complete", label: "Complete" },
      { id: "partial", label: "Partial" },
      { id: "rootless", label: "Rootless" },
      { id: "core", label: "Core" },
      { id: "path", label: "Path" },
      { id: "extended", label: "Extended" },
      { id: "song_tab_vocabulary", label: "Song/tab" },
      { id: "e_lower_pocket", label: "E-lower" },
      { id: "two_string", label: "Two-string" },
    ];
    return options.map((item) => {
      const count = item.id === "all"
        ? rows.length
        : rows.filter((row) => chordFinderRowMatchesMapFilter(row, item.id)).length;
      return { ...item, count };
    }).filter((item) => item.id === "all" || item.count > 0);
  }

  function chordFinderRowMatchesMapFilter(row, filterId = selectedChordMapFilter) {
    if (!filterId || filterId === "all") {
      return true;
    }
    if (["open", "pedals", "levers"].includes(filterId)) {
      return chordFinderControlFilter(row) === filterId;
    }
    if (["low", "mid", "high"].includes(filterId)) {
      return chordFinderFretBucket(row) === filterId;
    }
    if (["complete", "partial", "rootless"].includes(filterId)) {
      return chordFinderCompleteness(row) === filterId;
    }
    if (["core", "path", "extended", "song_tab_vocabulary", "e_lower_pocket", "two_string"].includes(filterId)) {
      return chordFinderTierFilter(row) === filterId;
    }
    return true;
  }

  function chordFinderVisibleRows(rows) {
    return rows.filter((row) => chordFinderRowMatchesMapFilter(row));
  }

  function chordFinderRowsForMap(rows, selected) {
    if (!selected) {
      return rows;
    }
    return [
      selected,
      ...rows.filter((row) => row.id !== selected.id),
    ];
  }

  function selectedGripCandidate() {
    return gripFinderCandidates().find((row) => row.id === selectedGripCandidateId) || null;
  }

  function focusGripCandidate(row) {
    if (!row) {
      return;
    }
    selectedGripCandidateId = row.id || "";
    const strings = toArray(row.strings).map(Number).filter(Number.isFinite).sort((a, b) => a - b);
    pinnedNoteCell = {
      stringNumber: strings[0] || Number(row.string || 1),
      fret: Number(row.fret || 0),
    };
    selectedNoteControlStateId = noteControlStateIdForControlIds(normalizePedals(row));
    drillFeedback = null;
    previewNoteCell = null;
  }

  function syncEventOptions() {
    const events = [
      { id: "s3-f3-open", step: "1", label: "String 3 fret 3 open", stringNumber: 3, fret: 3, controlStateId: "open" },
      { id: "s3-f3-b", step: "2", label: "String 3 fret 3 with B pedal", stringNumber: 3, fret: 3, controlStateId: "B" },
      { id: "s5-f3-a", step: "3", label: "String 5 fret 3 with A pedal", stringNumber: 5, fret: 3, controlStateId: "A" },
    ];
    return events.map((event) => {
      const controlState = noteControlStateById(event.controlStateId);
      const cell = noteCellState(event.stringNumber, event.fret, controlState);
      return {
        ...event,
        controlState,
        cell,
      };
    });
  }

  function selectedSyncEvent() {
    return syncEventOptions().find((event) => event.id === selectedSyncEventId) || syncEventOptions()[0] || null;
  }

  function focusSyncEvent(event) {
    if (!event) {
      return;
    }
    selectedSyncEventId = event.id;
    selectedNoteControlStateId = event.controlStateId;
    pinnedNoteCell = { stringNumber: event.stringNumber, fret: event.fret };
    previewNoteCell = null;
    drillFeedback = null;
  }

  function syncNoteFinderSelections() {
    if (!NOTE_TARGET_MODES.some((mode) => mode.id === selectedNoteTargetMode)) {
      selectedNoteTargetMode = "scale";
    }
    if (!NOTE_WORKFLOWS.some((workflow) => workflow.id === selectedNoteWorkflow)) {
      selectedNoteWorkflow = "find";
    }
    if (!noteStringFilterOptions().some((option) => option.value === selectedNoteStringFilter)) {
      selectedNoteStringFilter = "all";
    }
    if (!noteFinderTargets().some((target) => target.index === selectedNoteTargetIndex)) {
      selectedNoteTargetIndex = 0;
    }
    if (!availableNoteControlStates().some((state) => state.id === selectedNoteControlStateId)) {
      selectedNoteControlStateId = "open";
    }
    if (!gripTargetOptions().some((target) => target.id === selectedGripTargetId)) {
      selectedGripTargetId = gripTargetOptions()[0]?.id || "scale-triad";
    }
    if (!gripVocabularyOptions().some((option) => option.id === selectedGripVocabulary)) {
      selectedGripVocabulary = "core";
    }
    syncGripRoleWithVocabulary();
  }

  function visibleNoteFinderFrets() {
    const range = activeRangeOption();
    const frets = [];
    for (let fret = range.min; fret <= range.max; fret += 1) {
      frets.push(fret);
    }
    return frets;
  }

  function visibleNoteCells() {
    const frets = visibleNoteFinderFrets();
    return copedentChartRows().flatMap((row) => frets.map((fret) => noteCellState(row.string, fret)));
  }

  function allNoteCells() {
    return copedentChartRows().flatMap((row) => {
      const cells = [];
      for (let fret = 0; fret <= 24; fret += 1) {
        cells.push(noteCellState(row.string, fret));
      }
      return cells;
    });
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
      return dedupeValues(intervals.map(formatInterval));
    }
    if (row?.intervals && typeof row.intervals === "object" && !Array.isArray(row.intervals)) {
      return dedupeValues(Object.values(row.intervals).map(formatInterval));
    }
    return dedupeValues(toArray(row.intervals).map(formatInterval));
  }

  function topVoice(row) {
    const topVoice = row?.display_top_voice;
    if (topVoice && typeof topVoice === "object" && !Array.isArray(topVoice)) {
      return {
        note: formatValue(topVoice.note, ""),
        interval: formatInterval(topVoice.interval),
        string: formatValue(topVoice.string, ""),
      };
    }
    const entries = displayNoteEntries(row);
    const topString = toArray(row?.strings).map(Number).filter(Number.isFinite).sort((a, b) => a - b)[0];
    const entry = entries.find((item) => Number(item.string) === topString) || entries[0];
    if (entry) {
      return {
        note: formatValue(entry.note, ""),
        interval: entry.interval ? formatInterval(entry.interval) : "",
        string: formatValue(entry.string, ""),
      };
    }
    return {
      note: rowNoteLabels(row)[0] || "",
      interval: rowIntervalLabels(row)[0] || "",
      string: topString ? String(topString) : "",
    };
  }

  function topVoiceLabel(row) {
    const voice = topVoice(row);
    if (voice.note || voice.interval || voice.string) {
      const intervalText = notationMode === "notes"
        ? `interval ${formatIntervalForNotation(voice.interval)}`
        : `${notationModeLabel()} ${formatIntervalForNotation(voice.interval)}`;
      return [voice.note, voice.interval ? intervalText : "", voice.string ? `string ${voice.string}` : ""]
        .filter(Boolean)
        .join(" · ");
    }
    return row?.display_top_voice;
  }

  function topNoteLabel(row) {
    return topVoice(row).note || rowNoteLabels(row)[0] || "Position";
  }

  function topIntervalLabel(row) {
    return topVoice(row).interval || rowIntervalLabels(row)[0] || "Position";
  }

  function activeTopLabel(row) {
    const voice = topVoice(row);
    return notationLabelForFinalNote(voice.note || topNoteLabel(row), voice.interval || topIntervalLabel(row));
  }

  function activeTopLabelName() {
    return notationMode === "notes" ? "Top note" : "Top note interval";
  }

  function harmonyIntervalText(row) {
    return formatValue(rowIntervalLabels(row).map(formatIntervalForNotation), "");
  }

  function activeLabelValues(row) {
    const label = activeTopLabel(row);
    return label ? [label] : [];
  }

  function activeLabelText(row) {
    return formatValue(activeLabelValues(row));
  }

  function primaryLabelForRow(row) {
    if (isPathMode()) {
      return `${degreeStepLabel(row)} — ${chordDisplayName(row)}`;
    }
    const label = notationMode === "notes" ? "Top note" : "Top note interval";
    return `${label}: ${activeTopLabel(row) || row.chord_function || row.scale_degree || row.chord_name || "Position"}`;
  }

  function activeRangeOption() {
    return FRET_RANGE_OPTIONS.find((option) => option.id === selectedFretRange) || FRET_RANGE_OPTIONS[0];
  }

  function isPathMode() {
    return els.exploreMode?.value === EXPLORE_MODES.path;
  }

  function isNoteFinderMode() {
    return els.exploreMode?.value === EXPLORE_MODES.note;
  }

  function isVoicingIdentifierMode() {
    return els.exploreMode?.value === EXPLORE_MODES.voicing;
  }

  function isChordFinderMode() {
    return els.exploreMode?.value === EXPLORE_MODES.chord;
  }

  function activeHarmonyValue() {
    return isPathMode() ? "three_string_diatonic" : els.harmony.value;
  }

  function activePathFamily() {
    return PATH_FAMILIES.find((family) => family.id === els.pathFamily?.value)
      || PATH_FAMILIES.find((family) => family.id === "low")
      || PATH_FAMILIES[0];
  }

  function degreeSequenceForPath() {
    return [1, 2, 3, 4, 5, 6, 7, 1];
  }

  function degreeStepLabel(row) {
    const sequence = activeScaleSequence();
    const index = Number(row?.scale_degree || 0) - 1;
    if (notationMode === "notes") {
      return formatValue(row?.chord_name, "");
    }
    return sequence[index] || formatValue(row?.chord_function || row?.scale_degree, "");
  }

  function pathStepNotationLabel(row) {
    const step = Number(row?.path_step || row?.scale_degree || 1);
    const sequence = activeScaleSequence();
    const index = Math.max(0, (step - 1) % 7);
    return sequence[index] || degreeStepLabel(row);
  }

  function chordDisplayName(row) {
    const name = formatValue(row?.chord_name, "");
    const quality = formatValue(row?.chord_quality, "").toLowerCase();
    const functionText = formatValue(row?.chord_function, "");
    if (!name) {
      return formatValue(row?.chord_function || "Chord", "Chord");
    }
    if (functionText.includes("ø") || quality.includes("half")) {
      return `${name} half-diminished`;
    }
    if (quality.includes("diminished")) {
      return `${name} diminished`;
    }
    if (quality === "minor") {
      return `${name}m`;
    }
    return name;
  }

  function rowInRange(row, range = activeRangeOption()) {
    const fret = Number(row?.fret);
    return Number.isFinite(fret) && fret >= range.min && fret <= range.max;
  }

  function notationModeNoun() {
    return notationModeLabel();
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
    if (isPathMode()) {
      const family = activePathFamily();
      return `${family.label} (${family.groups.join(" / ")})`;
    }
    const groups = selectedStringGroups();
    if (groups.length) {
      return groups.join(", ");
    }
    return activeHarmonyValue() === "two_string_harmonized" ? "all 2-string groups" : "all 3-string groups";
  }

  function syncExploreModeControls() {
    const pathMode = isPathMode();
    const noteMode = isNoteFinderMode();
    const voicingMode = isVoicingIdentifierMode();
    const chordMode = isChordFinderMode();
    if (els.stringGroupControl) {
      els.stringGroupControl.hidden = pathMode || noteMode || voicingMode || chordMode;
      els.stringGroupControl.setAttribute?.("aria-hidden", pathMode || noteMode || voicingMode || chordMode ? "true" : "false");
    }
    if (els.stringGroup) {
      els.stringGroup.disabled = pathMode || noteMode || voicingMode || chordMode;
    }
    if (els.pathFamilyControl) {
      els.pathFamilyControl.hidden = !pathMode;
      els.pathFamilyControl.setAttribute?.("aria-hidden", pathMode ? "false" : "true");
    }
    if (els.pathFamily) {
      els.pathFamily.disabled = !pathMode;
    }
    if (els.gripVocabularyControl) {
      els.gripVocabularyControl.hidden = pathMode || noteMode || voicingMode;
      els.gripVocabularyControl.setAttribute?.("aria-hidden", pathMode || noteMode || voicingMode ? "true" : "false");
    }
    if (els.gripVocabulary) {
      els.gripVocabulary.disabled = pathMode || noteMode || voicingMode;
      if (chordMode && gripVocabularyOptions().some((optionItem) => optionItem.id === selectedGripVocabulary)) {
        els.gripVocabulary.value = selectedGripVocabulary;
      }
    }
    if (els.harmonyControl) {
      els.harmonyControl.hidden = pathMode || noteMode || voicingMode || chordMode;
      els.harmonyControl.setAttribute?.("aria-hidden", pathMode || noteMode || voicingMode || chordMode ? "true" : "false");
    }
    if (els.harmony) {
      els.harmony.disabled = pathMode || noteMode || voicingMode || chordMode;
      if (pathMode) {
        els.harmony.value = "three_string_diatonic";
      }
    }
  }

  function updateExploreModeTabs() {
    const selectedMode = els.exploreMode?.value || EXPLORE_MODES.single;
    Array.from(els.modeTabs || []).forEach((button) => {
      const isSelected = button.getAttribute("data-explorer-mode-tab") === selectedMode;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-selected", isSelected ? "true" : "false");
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
      button.setAttribute("tabindex", isSelected ? "0" : "-1");
    });
  }

  function updateTaskCards() {
    const fallbackTask = defaultTaskCardForMode(els.exploreMode?.value || EXPLORE_MODES.single);
    const knownTask = Array.from(els.taskCards || []).some((button) => (
      button.getAttribute("data-explorer-task-card") === selectedTaskCard
    ));
    const activeTask = knownTask ? selectedTaskCard : fallbackTask;
    selectedTaskCard = activeTask;
    Array.from(els.taskCards || []).forEach((button) => {
      const isSelected = button.getAttribute("data-explorer-task-card") === activeTask;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
  }

  function activeTaskMeta() {
    const fallbackTask = defaultTaskCardForMode(els.exploreMode?.value || EXPLORE_MODES.single);
    return TASK_CARD_META[selectedTaskCard] || TASK_CARD_META[fallbackTask] || TASK_CARD_META["explore-grip"];
  }

  function contextStripChips(rows) {
    const chips = [
      `Key: ${activeKey()}`,
      `Copedent: ${selectedOptionLabel(els.copedent) || "Emmons E9"}`,
    ];
    if (isChordFinderMode()) {
      const target = selectedChordFinderTarget();
      chips.push(`Chord: ${target?.label || target?.rootLabel || selectedChordRoot}`);
      chips.push(`Grip vocabulary: ${selectedOptionLabel(els.gripVocabulary) || "Core"}`);
    } else if (isVoicingIdentifierMode()) {
      chips.push(`Fret: ${voicingFret}`);
      chips.push(`Strings: ${selectedVoicingStrings.join("-") || "choose strings"}`);
    } else if (isNoteFinderMode()) {
      chips.push(`Note: ${selectedNoteFinderTarget()?.note || activeKey()}`);
      chips.push(`Workflow: ${selectedNoteWorkflow === "build" ? "Build a grip" : "Find note"}`);
    } else if (isPathMode()) {
      chips.push(`Path: ${selectedOptionLabel(els.pathFamily) || selectedGroupLabel()}`);
      chips.push(`Scale: ${selectedOptionLabel(els.scale) || `${activeKey()} major`}`);
    } else {
      chips.push(`Scale: ${selectedOptionLabel(els.scale) || `${activeKey()} major`}`);
      chips.push(`String group: ${selectedOptionLabel(els.stringGroup) || "All groups"}`);
    }
    if (Array.isArray(rows)) {
      chips.push(`${rows.length} visible ${rows.length === 1 ? "card" : "cards"}`);
    }
    return chips.filter(Boolean);
  }

  function updateContextStrip(rows) {
    if (!els.contextStrip) {
      return;
    }
    const task = activeTaskMeta();
    els.contextStrip.innerHTML = `
      <div class="explorer-context-strip__label">
        <span>Current task</span>
        <strong>${escapeHtml(task.label)}</strong>
      </div>
      <div class="explorer-context-strip__body">
        ${contextStripChips(rows).map((chip) => `<span class="explorer-context-chip">${escapeHtml(chip)}</span>`).join("")}
      </div>
      <p class="explorer-context-strip__note">${escapeHtml(task.context)}</p>
    `;
  }

  function applyTaskCard(taskId) {
    const task = String(taskId || "explore-grip");
    const taskModeMap = {
      "find-chord": EXPLORE_MODES.chord,
      "find-note": EXPLORE_MODES.note,
      "explore-grip": EXPLORE_MODES.single,
      "walk-harmonized-scale": EXPLORE_MODES.path,
      "study-movement-path": EXPLORE_MODES.path,
      "identify-voicing": EXPLORE_MODES.voicing,
    };
    const nextMode = taskModeMap[task] || EXPLORE_MODES.single;
    selectedTaskCard = taskModeMap[task] ? task : "explore-grip";
    if (els.exploreMode) {
      els.exploreMode.value = nextMode;
    }
    selectedTopFilter = "all";
    selectedFretRange = "core";
    if (task === "find-chord") {
      selectedChordRoot = activeKey();
      selectedChordQuality = "major";
      selectedChordControlScope = "common";
      selectedChordCandidateId = "";
      selectedChordMapFilter = "all";
      selectedGripVocabulary = "core";
    } else if (task === "find-note") {
      selectedNoteWorkflow = "find";
      selectedNoteControlStateId = "open";
      selectedNoteStringFilter = "all";
      selectedNoteTargetIndex = 0;
      pinnedNoteCell = { stringNumber: 3, fret: 3 };
      previewNoteCell = null;
    } else if (task === "explore-grip") {
      selectedSingleGripVocabulary = "core";
    } else if (task === "walk-harmonized-scale") {
      safeSelectValue(els.pathFamily, "middle");
    } else if (task === "study-movement-path") {
      safeSelectValue(els.pathFamily, "low");
    } else if (task === "identify-voicing") {
      voicingFret = 3;
      selectedVoicingStrings = [3, 4, 5];
      selectedVoicingControlIds = new Set();
      voicingUiWarning = "";
    }
    updateExploreModeTabs();
    updateTaskCards();
    updateControls();
    render();
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
    const retiredCommonIds = new Set(["custom-e9-lkv", "my-copedent-e9"]);
    const combined = new Map((Array.isArray(options) ? options : [])
      .filter((item) => !retiredCommonIds.has(item.id))
      .map((item) => [item.id, item]));
    (window.STEEL_RAG_COPEDENTS?.listProfiles?.() || []).forEach((profile) => {
      combined.set(profile.id, {
        id: profile.id,
        label: profile.name || profile.label,
        status: profile.immutable || profile.validationStatus === "valid" ? "enabled" : "disabled",
        disabled_reason: profile.validationStatus === "needs_review" ? "Needs review in Backstage" : "Validate in Backstage"
      });
    });
    return Array.from(combined.values());
  }

  function updateCopedentOptions() {
    if (!els.copedent) {
      return;
    }
    const options = availableCopedents();
    if (!options.length) {
      return;
    }
    const payloadProfileId = String((activePayload() || fallbackPayload)?.selected_copedent?.id || "")
      .trim()
      .replace(/^saved:/, "");
    const activeProfileId = String(window.STEEL_RAG_COPEDENTS?.activeContext?.()?.profileId || "").trim();
    const currentValue = activeProfileId || payloadProfileId || els.copedent.value || DEFAULT_COPEDENT_ID;
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
    const harmony = activeHarmonyValue();
    const rows = rowsForScaleAndHarmony(scale, harmony);
    const vocabularyValue = isChordFinderMode() ? selectedGripVocabulary : selectedSingleGripVocabulary;
    if (els.gripVocabulary && gripVocabularyOptions().some((optionItem) => optionItem.id === vocabularyValue)) {
      els.gripVocabulary.value = vocabularyValue;
    }
    const registryGroups = gripVocabularyGroups(vocabularyValue);
    const validGroups = harmony === "two_string_harmonized"
      ? availableStringGroups(rows, harmony)
      : Array.from(registryGroups);
    const currentValues = selectedStringGroups().filter((group) => validGroups.includes(group));
    const allLabel = allGripOptionLabel(vocabularyValue, harmony);
    const selectedValues = currentValues.length ? currentValues : ["all"];
    let html = option("all", allLabel, selectedValues);

    if (harmony === "two_string_harmonized") {
      html += optionGroup("2-string groups", validGroups, selectedValues);
    } else {
      html += optionGroup("Core grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "core"), selectedValues);
      html += optionGroup("Path grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "path"), selectedValues);
      html += optionGroup("Extended grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "extended"), selectedValues);
      html += optionGroup("Song/tab vocabulary grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "song_tab_vocabulary"), selectedValues);
      html += optionGroup("E-lower pocket grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "e_lower_pocket"), selectedValues);
      html += optionGroup("Two-string grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "two_string"), selectedValues);
      html += optionGroup("Advanced grips", Array.from(registryGroups).filter((group) => gripMetadata(group)?.tier === "advanced"), selectedValues);
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
    syncExploreModeControls();
    updateHarmonyOptions();
    updateStringGroupOptions();
  }

  function getBaseRows() {
    const payload = activePayload();
    if (!payload || !Array.isArray(payload.positions)) {
      return [];
    }

    const key = activeKey();
    const scale = els.scale.value;
    const harmony = activeHarmonyValue();
    const stringGroups = selectedStringGroups();
    const matchingRows = payload.positions
      .filter((row) => row.key === key)
      .filter((row) => row.scale_type === scale)
      .filter((row) => rowMatchesHarmony(row, harmony));

    if (isPathMode()) {
      return pathRows(matchingRows);
    }

    return matchingRows
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

  function pathRows(rows) {
    const family = activePathFamily();
    const pathGroups = new Set(family.groups);
    const pathCandidates = rows
      .filter((row) => pathGroups.has(row.string_group))
      .filter((row) => row.harmony_type === "three_string_diatonic")
      .sort((a, b) => {
        const byDegree = Number(a.scale_degree || 0) - Number(b.scale_degree || 0);
        if (byDegree) {
          return byDegree;
        }
        const byFret = Number(a.fret || 0) - Number(b.fret || 0);
        return byFret || String(a.id || "").localeCompare(String(b.id || ""));
      });
    const steps = degreeSequenceForPath();
    const selected = [];
    steps.forEach((degree, index) => {
      const preferredGroup = family.pattern[index] || family.groups[0];
      const candidates = pathCandidates
        .filter((row) => Number(row.scale_degree) === degree)
        .filter((row) => row.string_group === preferredGroup);
      const fallbackCandidates = pathCandidates.filter((row) => Number(row.scale_degree) === degree);
      const source = candidates.length ? candidates : fallbackCandidates;
      if (!source.length) {
        return;
      }
      const sorted = [...source].sort((a, b) => Number(a.fret || 0) - Number(b.fret || 0));
      const row = index === steps.length - 1 ? sorted[sorted.length - 1] : sorted[0];
      selected.push({
        ...row,
        path_family: family.id,
        path_family_label: family.label,
        path_step: index + 1,
      });
    });
    return selected;
  }

  function intervalSortIndex(interval) {
    const order = ["1", "♭2", "2", "♭3", "3", "4", "♯4", "♭5", "5", "♭6", "6", "♭7", "7"];
    const found = order.indexOf(interval);
    return found === -1 ? 100 + interval.localeCompare("") : found;
  }

  function activeTopFilterLabel(row) {
    return activeTopLabel(row);
  }

  function topFilterSortIndex(label) {
    const sequenceIndex = activeScaleSequence().indexOf(label);
    if (sequenceIndex !== -1) {
      return sequenceIndex;
    }
    if (notationMode === "notes") {
      const scaleIndex = scaleDegreeIndexForNote(label);
      if (scaleIndex !== -1) {
        return scaleIndex;
      }
    }
    return 100 + intervalSortIndex(label);
  }

  function availableTopFilters(rows) {
    return dedupeValues(rows.map(activeTopFilterLabel))
      .sort((a, b) => {
        const byOrder = topFilterSortIndex(a) - topFilterSortIndex(b);
        return byOrder || a.localeCompare(b);
      });
  }

  function syncSelectedTopFilter(baseRows) {
    const available = new Set(availableTopFilters(baseRows));
    if (selectedTopFilter !== "all" && !available.has(selectedTopFilter)) {
      selectedTopFilter = "all";
    }
  }

  function getRows() {
    const baseRows = getBaseRows();
    if (isPathMode() && selectedTopFilter === "all") {
      return baseRows;
    }
    if (isPathMode()) {
      return baseRows.filter((row) => activeTopFilterLabel(row) === selectedTopFilter);
    }
    if (selectedTopFilter === "all") {
      return baseRows.filter((row) => rowInRange(row));
    }
    return baseRows
      .filter((row) => activeTopFilterLabel(row) === selectedTopFilter)
      .filter((row) => rowInRange(row));
  }

  function getRowsBeforeRange(baseRows) {
    if (isPathMode()) {
      return baseRows;
    }
    if (selectedTopFilter === "all") {
      return baseRows;
    }
    return baseRows.filter((row) => activeTopFilterLabel(row) === selectedTopFilter);
  }

  function getScaleNotes() {
    const values = activeScaleSequence();
    return values.length ? values.join(" - ") : "Unavailable";
  }

  function updateScaleNotes() {
    if (els.scaleNotes) {
      els.scaleNotes.textContent = getScaleNotes();
    }
  }

  function isAdvanced(row) {
    return ADVANCED_GROUPS.has(row.string_group) || row.harmony_type === "advanced_pocket";
  }

  function groupLabel(row) {
    if (isPathMode()) {
      return "Harmonized scale path";
    }
    if (row.harmony_type === "dominant_v7_grip") {
      return "Dominant 7 / V7 grip";
    }
    if (row.harmony_type === "chord_voicing_finder") {
      return row.chord_finder?.gripTier || "Chord / voicing finder";
    }
    if (row.harmony_type === "five_eight_branch" || row.string_group === "5-8") {
      return "5&8 branch";
    }
    const metadata = gripMetadata(row.string_group);
    if (metadata) {
      return metadata.label;
    }
    if (isAdvanced(row)) {
      return row.string_group === "5-7-8" ? "Advanced swap - E-lower pocket" : "Advanced swap";
    }
    return "Explorer row";
  }

  function pathChangeNote(row) {
    if (!isPathMode()) {
      return "";
    }
    const index = currentRows.findIndex((item) => item.id === row.id && item.path_step === row.path_step);
    const previous = index > 0 ? currentRows[index - 1] : null;
    const next = index >= 0 && index < currentRows.length - 1 ? currentRows[index + 1] : null;
    const changedFromPrevious = previous && previous.string_group !== row.string_group;
    const changesToNext = next && next.string_group !== row.string_group;
    if (!changedFromPrevious && !changesToNext) {
      return "";
    }
    const controls = normalizePedals(row);
    const reason = row.string_group.includes("7") && controls.includes("A") && controls.includes("B")
      ? "minor position uses this A+B string group in this path"
      : "this path changes string groups when the harmony requires it";
    const fromText = changedFromPrevious ? `from ${previous.string_group}` : "";
    const toText = changesToNext ? `to ${next.string_group}` : "";
    return ["String group changes", [fromText, toText].filter(Boolean).join(" and "), reason]
      .filter(Boolean)
      .join(": ");
  }

  function selectedPathIndex(rows = currentRows) {
    const index = rows.findIndex((row) => row.id === selectedRowId);
    return index === -1 ? 0 : index;
  }

  function pathControlText(row) {
    const controls = normalizePedals(row);
    return controls.length ? `With ${controls.join("+")}` : "Open";
  }

  function pathStepTitle(row) {
    return `${pathStepNotationLabel(row)} — ${chordDisplayName(row)}`;
  }

  function pathRowsForFretboard(rows) {
    return rows;
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
      intervals: rowIntervalLabels(row).map(formatIntervalForNotation),
      explanation: row.display_summary || row.explanation,
      colorRole: colorRoleForRow(row),
      visibleByDefault: true,
    };
  }

  function markerGroupKey(row) {
    const label = activeTopLabel(row) || row.chord_name || row.chord_function || row.scale_degree || "";
    return [
      "marker",
      row.fret,
      row.string_group,
      (row.strings || []).join("-"),
      label,
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

  function markerToneForIndex(index) {
    return String(((Number(index) || 1) - 1) % 8 + 1);
  }

  function markerToneForGroup(group) {
    return markerToneForIndex(group?.index || 1);
  }

  function markerToneForRow(row) {
    const group = currentMarkerGroups.find((item) => item.id === markerGroupKey(row));
    return group ? markerToneForGroup(group) : "1";
  }

  function markerLabelForGroup(group) {
    const labels = markerLabelValuesForGroup(group);
    if (!labels.length) {
      return "";
    }
    return labels.slice(0, 2).join(", ");
  }

  function markerLabelValuesForGroup(group) {
    return dedupeValues(group.rows.map(activeTopLabel));
  }

  function markerOverflowCountForGroup(group) {
    return Math.max(0, markerLabelValuesForGroup(group).length - 2);
  }

  function markerLabelForRow(row) {
    const group = currentMarkerGroups.find((item) => item.id === markerGroupKey(row));
    return group ? markerLabelForGroup(group) : "";
  }

  function asMarkerPosition(group) {
    const row = group.rows[0];
    const labelValues = markerLabelValuesForGroup(group);
    return {
      ...asFretboardPosition(row),
      id: group.id,
      label: markerLabelForGroup(group),
      labelValues,
      labelOverflowCount: markerOverflowCountForGroup(group),
      explanation: group.rows.length > 1
        ? `${group.rows.length} validated setups share this fret and string group.`
        : row.display_summary || row.explanation,
    };
  }

  function shortLabel(row) {
    const controls = normalizePedals(row);
    return `${primaryLabelForRow(row)}${controls.length ? ` · With ${controls.join("+")}` : " · Open"}`;
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
        <p>${escapeHtml(formatTheoryText(rendered))}</p>
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
          <strong>${escapeHtml(formatValue(selected.label || "E9 copedent"))}</strong>
          <p>Choose the copedent that matches your guitar. Emmons and Day mainly differ in pedal arrangement.</p>
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
                  <span>${escapeHtml(controlDisplayLabel(column, "Control"))}</span>
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
    const beforeInterval = impact.before_interval ? formatIntervalForNotation(impact.before_interval) : "";
    const afterInterval = impact.after_interval ? formatIntervalForNotation(impact.after_interval) : "";
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
    const rows = !isPathMode() && selectedGroups.length
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

  function controlImpactGroup(control) {
    const type = String(control?.control_type || "").toLowerCase();
    if (type === "pedal" || ["A", "B", "C"].includes(control?.id)) {
      return "pedals";
    }
    return "levers";
  }

  function controlImpactButtonLabel(control) {
    if (controlImpactGroup(control) === "pedals") {
      return control?.id || controlDisplayLabel(control, "Pedal").replace(/\s+pedal$/i, "");
    }
    const shortLabels = {
      "E-raise": "F",
      "E-lower": "E",
      "G-lower": "G",
      "D-lower": "D",
    };
    if (shortLabels[control?.id]) {
      return shortLabels[control.id];
    }
    return controlDisplayLabel(control, "Lever")
      .replace(/\s+\(F lever\)$/i, " (F)")
      .replace(/\s+lever$/i, "");
  }

  function sortImpactLevers(controls) {
    const order = ["E-raise", "E-lower", "G-lower", "D-lower"];
    return controls.slice().sort((a, b) => {
      const aIndex = order.indexOf(a?.id);
      const bIndex = order.indexOf(b?.id);
      if (aIndex !== -1 || bIndex !== -1) {
        return (aIndex === -1 ? order.length : aIndex) - (bIndex === -1 ? order.length : bIndex);
      }
      return controlDisplayLabel(a, "").localeCompare(controlDisplayLabel(b, ""));
    });
  }

  function controlImpactButtonHtml(control) {
    return `
      <button
        class="explorer-control-impact-tab${selectedImpactControlIds.has(control.id) ? " is-selected" : ""}"
        type="button"
        aria-pressed="${selectedImpactControlIds.has(control.id) ? "true" : "false"}"
        data-control-impact-tab="${escapeHtml(control.id || "")}"
      >${escapeHtml(controlImpactButtonLabel(control))}</button>
    `;
  }

  function controlImpactGroupsHtml(controls) {
    const pedals = controls.filter((control) => controlImpactGroup(control) === "pedals");
    const levers = sortImpactLevers(controls.filter((control) => controlImpactGroup(control) === "levers"));
    const groupHtml = [
      { label: "Pedals", controls: pedals },
      { label: "Levers", controls: levers },
    ].filter((group) => group.controls.length).map((group) => `
      <fieldset class="explorer-control-impact-group">
        <legend>${escapeHtml(group.label)}</legend>
        <div class="explorer-control-impact-tabs" role="group" aria-label="${escapeHtml(group.label)}">
          ${group.controls.map((control) => controlImpactButtonHtml(control)).join("")}
        </div>
      </fieldset>
    `).join("");
    return `
      <div class="explorer-control-impact-control-groups" role="group" aria-label="Pedal and lever controls">
        ${groupHtml}
        <button class="explorer-control-impact-tab explorer-control-impact-clear" type="button" data-control-impact-clear>Clear</button>
      </div>
    `;
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
          <strong>${escapeHtml(controlDisplayLabel(control, "Control"))}</strong>
          <p>No direct impact on the selected string group. This control affects strings ${escapeHtml(affectedStrings)}, but those strings are not active in the current view.</p>
        </article>
      `;
    }
    return `
      <article class="explorer-control-impact-detail" data-control-impact-detail="${escapeHtml(control.id || control.label || "")}">
        <strong>${escapeHtml(controlDisplayLabel(control, "Control"))}</strong>
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
    if (isNoteFinderMode() || isVoicingIdentifierMode()) {
      els.controlPreview.hidden = true;
      els.controlPreview.innerHTML = "";
      selectedImpactControlIds = new Set();
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
      </div>
      <div class="explorer-control-impact-preview__body">
        ${controlImpactGroupsHtml(controls)}
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

  function renderTopIntervalFilter(baseRows) {
    if (!els.topIntervalFilter) {
      return;
    }
    if (isNoteFinderMode() || isVoicingIdentifierMode() || isChordFinderMode()) {
      els.topIntervalFilter.hidden = true;
      els.topIntervalFilter.innerHTML = "";
      return;
    }
    const filters = availableTopFilters(baseRows);
    if (filters.length <= 1) {
      els.topIntervalFilter.hidden = true;
      els.topIntervalFilter.innerHTML = "";
      return;
    }
    els.topIntervalFilter.hidden = false;
    const allSelected = selectedTopFilter === "all";
    const filterNoun = notationMode === "notes" ? "top note" : `${notationModeLabel()} top label`;
    const chips = [
      `<button class="explorer-top-interval-filter__chip${allSelected ? " is-selected" : ""}" type="button" data-top-interval-filter="all" aria-pressed="${allSelected ? "true" : "false"}">All</button>`,
      ...filters.map((filter) => {
        const selected = selectedTopFilter === filter;
        return `<button class="explorer-top-interval-filter__chip${selected ? " is-selected" : ""}" type="button" data-top-interval-filter="${escapeHtml(filter)}" aria-pressed="${selected ? "true" : "false"}">${escapeHtml(filter)}</button>`;
      }),
    ];
    els.topIntervalFilter.innerHTML = `
      <div class="explorer-top-interval-filter__label">
        <strong>Find ${escapeHtml(filterNoun)}</strong>
        <span>The marker label follows the top string of each selected grip in ${escapeHtml(notationModeLabel())} mode.</span>
      </div>
      <div class="explorer-top-interval-filter__chips" role="group" aria-label="Filter by ${escapeHtml(filterNoun)}">
        ${chips.join("")}
      </div>
    `;
    Array.from(els.topIntervalFilter.querySelectorAll("[data-top-interval-filter]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedTopFilter = button.getAttribute("data-top-interval-filter") || "all";
        render();
      });
    });
  }

  function renderFretRangeFilter(rowsBeforeRange, rows) {
    if (!els.fretRangeFilter) {
      return;
    }
    if (isPathMode() || isVoicingIdentifierMode()) {
      els.fretRangeFilter.hidden = true;
      els.fretRangeFilter.innerHTML = "";
      return;
    }
    const outsideCount = Math.max(0, rowsBeforeRange.length - rows.length);
    const activeRange = activeRangeOption();
    const matchNoun = isNoteFinderMode() ? "note" : isChordFinderMode() ? "candidate" : "position";
    els.fretRangeFilter.hidden = false;
    els.fretRangeFilter.innerHTML = `
      <div class="explorer-fret-range-filter__label">
        <strong>Visible fret range</strong>
        <span>${outsideCount
          ? `${outsideCount} matching ${outsideCount === 1 ? `${matchNoun} is` : `${matchNoun}s are`} outside ${activeRange.description.toLowerCase()}.`
          : `Showing ${activeRange.description.toLowerCase()}.`}</span>
      </div>
      <div class="explorer-fret-range-filter__chips" role="group" aria-label="Choose visible fret range">
        ${FRET_RANGE_OPTIONS.map((range) => `
          <button
            class="explorer-fret-range-filter__chip${selectedFretRange === range.id ? " is-selected" : ""}"
            type="button"
            aria-pressed="${selectedFretRange === range.id ? "true" : "false"}"
            data-fret-range-filter="${escapeHtml(range.id)}"
          >
            <strong>${escapeHtml(range.label)}</strong>
            <span>${escapeHtml(range.description)}</span>
          </button>
        `).join("")}
      </div>
    `;
    Array.from(els.fretRangeFilter.querySelectorAll("[data-fret-range-filter]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedFretRange = button.getAttribute("data-fret-range-filter") || "core";
        render();
      });
    });
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

  function controlsForString(row, stringNumber) {
    const target = Number(stringNumber);
    const controls = [];
    toArray(row.control_impacts).forEach((impact) => {
      const hasString = toArray(impact.string_impacts).some((stringImpact) => Number(stringImpact.string) === target);
      if (hasString) {
        controls.push(formatValue(impact.id || impact.label, ""));
      }
    });
    const perString = row.per_string_changes?.[String(stringNumber)]?.controls;
    if (perString) {
      controls.push(perString);
    }
    return dedupeValues(controls);
  }

  function stringStateLabel(row, stringNumber) {
    const controls = controlsForString(row, stringNumber);
    return controls.length ? `S${stringNumber} ${controls.join("+")}` : `S${stringNumber}`;
  }

  function stringActionForEntry(row, entry) {
    const change = row.per_string_changes?.[String(entry.string)];
    const controls = controlsForString(row, entry.string);
    const role = notationLabelForFinalNote(entry.note, entry.interval);
    if (change) {
      return {
        string: entry.string,
        action: controls.length ? controls.join("+") : formatValue(change.controls, "changed"),
        change: `${formatValue(change.from, "")} -> ${formatValue(change.to, "")}`,
        role,
      };
    }
    return {
      string: entry.string,
      action: "no change",
      change: formatValue(entry.note, ""),
      role,
    };
  }

  function stringActionRowsHtml(row) {
    const entries = displayNoteEntries(row);
    if (!entries.length) {
      return "";
    }
    const rows = entries.map((entry) => stringActionForEntry(row, entry));
    return `
      <section class="explorer-string-actions" aria-label="String actions for selected position">
        <strong>String actions</strong>
        <div class="explorer-string-actions__grid">
          ${rows.map((entry) => `
            <div class="explorer-string-action">
              <span>String ${escapeHtml(entry.string)}</span>
              <b>${escapeHtml(entry.action)}</b>
              <em>${escapeHtml(entry.change)}${entry.role ? ` · role: ${escapeHtml(entry.role)}` : ""}</em>
            </div>
          `).join("")}
        </div>
      </section>
    `;
  }

  function topVoiceExplanationHtml(row) {
    const voice = topVoice(row);
    if (!voice.note && !voice.interval) {
      return "";
    }
    const stringText = voice.string ? `string ${voice.string}` : "the top string";
    const notationText = activeTopLabel(row);
    const noteText = voice.note ? `top note ${voice.note}` : "the top note";
    const scaleText = selectedOptionLabel(els.scale) || `${activeKey()} ${els.scale.value}`;
    return `
      <section class="explorer-top-voice-note" aria-label="Top-note interval explanation">
        <strong>Top-note focus</strong>
        <p>${escapeHtml(`This view indexes the grip by ${stringText}: final ${noteText} maps to ${notationModeLabel()} label ${notationText} in ${scaleText}. The other notes below it support the harmony (${harmonyIntervalText(row)}).`)}</p>
      </section>
    `;
  }

  function amazingTablatureHandoffHtml(notes, options = {}) {
    const melody = toArray(notes).map((note) => formatValue(note, "")).filter(Boolean);
    if (!melody.length) {
      return "";
    }
    const params = [
      ["kind", "user_melody"],
      ["key", options.key || activeKey()],
      ["notes", melody.join(" ")],
      ["voice", options.voice || "mixed"],
      ["movement", options.movement || (melody.length > 1 ? "slides" : "best_fit")],
      ["source", "fretboard-explorer"]
    ];
    if (options.chord) params.push(["chord", options.chord]);
    const query = params
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join("&");
    return `
      <section class="explorer-teaching-note" aria-label="Amazing Tablature handoff">
        <strong>Turn this into playable tab</strong>
        <p>Send the selected note${melody.length === 1 ? "" : " path"} to the same validated arranger used by Melody Studio and Q&amp;A. Choose one, two, three, or mixed voices there.</p>
        <a class="explorer-back" href="/ui/melody-workbench.html?${escapeHtml(query)}">Open in Amazing Tablature →</a>
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
    const selectedTitle = isPathMode()
      ? pathStepTitle(row)
      : formatTheoryText(row.display_summary || row.chord_name || row.id);
    els.selectedDetail.className = detailClass;
    els.selectedDetail.innerHTML = `
      <div class="explorer-selected-detail__header">
        <span class="explorer-selected-detail__kind">${escapeHtml(groupLabel(row))}</span>
        <strong>${escapeHtml(selectedTitle)}</strong>
      </div>
      ${topVoiceExplanationHtml(row)}
      ${teachingNoteHtml(row)}
      <dl class="explorer-detail-grid">
        ${detailRow(activeTopLabelName(), activeTopLabel(row))}
        ${detailRow("Path step", isPathMode() ? pathStepTitle(row) : "")}
        ${detailRow("Supporting harmony", harmonyIntervalText(row))}
        ${detailRow("Notes", rowNoteLabels(row))}
        ${detailRow("Notes with register", notesWithRegisterText(row))}
        ${detailRow("Chord intervals", rowIntervalLabels(row))}
        ${detailRow("Notation mode", notationModeLabel())}
        ${detailRow("Pitch register", activePitchRegisterMode() === "off" ? "" : pitchRegisterModeLabel())}
        ${detailRow("Top voice", topVoiceLabel(row))}
        ${detailRow("Fret", row.fret)}
        ${detailRow("String group", row.string_group)}
        ${detailRow("Pedals / levers", normalizePedals(row))}
        ${detailRow("Per-string changes", row.per_string_changes)}
        ${detailRow("Warnings", warnings)}
      </dl>
      ${stringActionRowsHtml(row)}
      ${rowControlImpactsHtml(row)}
      ${amazingTablatureHandoffHtml(
        isPathMode() ? currentRows.map((item) => topVoice(item).note) : [topVoice(row).note],
        {
          voice: isPathMode() ? "mixed" : ((toArray(row.strings).length >= 3) ? "three_voice" : (toArray(row.strings).length === 2 ? "two_voice" : "single")),
          movement: isPathMode() ? "slides" : "best_fit",
          chord: row.chord_name || ""
        }
      )}
    `;
  }

  function selectRow(rowId) {
    if (!currentRows.some((row) => row.id === rowId)) {
      selectedRowId = currentRows[0]?.id || "";
    } else {
      selectedRowId = rowId;
    }
    if (isChordFinderMode()) {
      selectedChordCandidateId = selectedRowId;
      renderChordFinderMode();
      return;
    }
    if (isVoicingIdentifierMode()) {
      renderVoicingIdentifierMode();
      return;
    }
    const selected = currentRows.find((row) => row.id === selectedRowId);
    renderSelectedDetail(selected);
    if (isPathMode()) {
      renderActiveResults(currentRows);
      renderFretboard(pathRowsForFretboard(currentRows));
    }
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
      Array.from(els.activeResults.querySelectorAll("[data-path-step]")).forEach((button) => {
        const isSelected = button.getAttribute("data-path-step") === selectedRowId;
        button.classList.toggle("is-selected", isSelected);
        button.setAttribute("aria-pressed", isSelected ? "true" : "false");
      });
      Array.from(els.activeResults.querySelectorAll("[data-path-compare-row]")).forEach((button) => {
        const isSelected = button.getAttribute("data-path-compare-row") === selectedRowId;
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
    const markerOverflowCount = markerOverflowCountForGroup(currentMarkerGroups.find((item) => item.id === markerGroupKey(row)) || { rows: [row] });
    const markerTone = markerToneForRow(row);
    const controls = normalizePedals(row);
    const controlText = controls.length ? `With ${controls.join("+")}` : "Open";
    return `
      <button class="explorer-active-result${buttonClass}${isSelected ? " is-selected" : ""}" type="button" ${dataAttributeName}="${escapeHtml(row.id)}" data-marker-id="${escapeHtml(markerGroupKey(row))}" data-marker-tone="${escapeHtml(markerTone)}" data-string-group="${escapeHtml(row.string_group)}" data-harmony-type="${escapeHtml(row.harmony_type)}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          ${markerLabel ? `<span class="explorer-active-result__marker" aria-label="Matching fretboard marker ${escapeHtml(markerLabel)}${markerOverflowCount ? ` plus ${markerOverflowCount} more` : ""}"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(markerLabel)}</span>${markerOverflowCount ? `<small aria-hidden="true">+${markerOverflowCount}</small>` : ""}</span>` : ""}
          <strong>${escapeHtml(primaryLabelForRow(row))}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Fret</b>${escapeHtml(formatValue(row.fret))}</span>
          <span><b>Strings</b>${escapeHtml(row.string_group)}</span>
          <span><b>Pedals/levers</b>${escapeHtml(controlText)}</span>
          <span><b>Harmony</b>${escapeHtml(harmonyIntervalText(row))}</span>
          ${activePitchRegisterMode() !== "off" ? `<span><b>Register</b>${escapeHtml(notesWithRegisterText(row))}</span>` : ""}
        </span>
      </button>
    `;
  }

  function pathStepButtonHtml(row, index) {
    const selected = row.id === selectedRowId;
    const markerTone = markerToneForRow(row);
    return `
      <button class="explorer-path-step${selected ? " is-selected" : ""}" type="button" data-path-step="${escapeHtml(row.id)}" data-marker-tone="${escapeHtml(markerTone)}" data-string-group="${escapeHtml(row.string_group)}" aria-pressed="${selected ? "true" : "false"}">
        <span class="explorer-path-step__number">${escapeHtml(String(index + 1))}</span>
        <span class="explorer-path-step__main">
          <strong>${escapeHtml(pathStepTitle(row))}</strong>
          <span>Fret ${escapeHtml(formatValue(row.fret))} · ${escapeHtml(row.string_group)} · ${escapeHtml(pathControlText(row))}</span>
        </span>
      </button>
    `;
  }

  function renderPathRail(rows) {
    const label = selectedGroupLabel();
    if (!rows.length) {
      els.activeResults.innerHTML = `
        <div class="explorer-active-results__header">
          <strong>No visible path steps for ${escapeHtml(label)}</strong>
          <span>Try a different path family or scale.</span>
        </div>
      `;
      return;
    }
    els.activeResults.innerHTML = `
      <div class="explorer-active-results__header explorer-path-rail__header">
        <div>
          <strong>${escapeHtml(label)}: Scale path rail</strong>
          <span>Each card has a matching full-grip marker on the fretboard. Same-fret grips are staggered so both colors remain visible.</span>
        </div>
      </div>
      <div class="explorer-path-rail" role="list" aria-label="Harmonized scale path">
        ${rows.map(pathStepButtonHtml).join("")}
      </div>
    `;
    Array.from(els.activeResults.querySelectorAll("[data-path-step]")).forEach((button) => {
      const rowId = button.getAttribute("data-path-step");
      button.addEventListener("click", () => selectRow(rowId));
      button.addEventListener("mouseenter", () => showMarkerForRow(rowId));
      button.addEventListener("focus", () => showMarkerForRow(rowId));
      button.addEventListener("mouseleave", clearMarkerHover);
      button.addEventListener("blur", clearMarkerHover);
    });
  }

  function renderActiveResults(rows) {
    if (!els.activeResults) {
      return;
    }
    if (isPathMode()) {
      renderPathRail(rows);
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
            <span class="explorer-row-button__meta">Fret: ${escapeHtml(formatValue(row.fret))} · Strings: ${escapeHtml(row.string_group)} · ${escapeHtml(groupLabel(row))} · Harmony: ${escapeHtml(harmonyIntervalText(row))}${pathChangeNote(row) ? ` · ${escapeHtml(pathChangeNote(row))}` : ""}</span>
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
    const stringActions = displayNoteEntries(row)
      .map((entry) => {
        const action = stringActionForEntry(row, entry);
        return `String ${action.string} - ${action.action} - ${action.change}${action.role ? ` - role: ${action.role}` : ""}`;
      })
      .join("; ");
    return [
      row.display_summary || row.chord_name || row.chord_function || row.id,
      `Fret ${row.fret} · strings ${row.string_group}`,
      `${activeTopLabelName()}: ${activeTopLabel(row)}`,
      `Top-note focus: string ${topVoice(row).string || "top"} final note ${topVoice(row).note || "unknown"} maps to ${activeTopLabel(row)} in ${activeKey()}`,
      `Notes: ${formatValue(rowNoteLabels(row))}`,
      `${notationModeLabel()} harmony: ${harmonyIntervalText(row)}`,
      `Pedals/levers: ${formatValue(controls)}`,
      pathChangeNote(row),
      stringActions ? `String actions: ${stringActions}` : "",
      warnings.length ? `Warning: ${formatValue(warnings)}` : "",
    ].filter(Boolean).map(formatTheoryText);
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
      const group = markerGroups.find((item) => item.id === marker.getAttribute("data-highlight-id"));
      const markerRows = byMarkerId.get(marker.getAttribute("data-highlight-id")) || [];
      if (!markerRows.length) {
        return;
      }
      marker.setAttribute("data-explorer-marker-label", markerLabelForGroup(group || { index: "", rows: markerRows }));
      marker.setAttribute("data-explorer-marker-tone", markerToneForGroup(group));
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

  function renderFretboard(rows, options = {}) {
    if (!fretboardApi || typeof fretboardApi.mountPedalSteelFretboard !== "function") {
      els.fretboard.innerHTML = '<p class="explorer-empty">Fretboard renderer unavailable.</p>';
      return;
    }
    const markerGroups = groupRowsForMarkers(rows);
    const selectedMarkerId = markerGroupKey(rows.find((row) => row.id === selectedRowId) || {});
    const stringActionLabelMode = "all";
    // SVG paints later groups on top, so the selected marker must render last.
    const sortedMarkerGroups = [
      ...markerGroups.filter((group) => group.id !== selectedMarkerId),
      ...markerGroups.filter((group) => group.id === selectedMarkerId),
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
      showHighlightLabels: options.showHighlightLabels !== false,
      showStringActionLabels,
      stringActionLabelMode,
      emphasizeVisibleHighlights: true,
      highlightStyle: "prominent",
    });
    wireFretboardMarkers(rows, markerGroups);
  }

  function noteCellKey(cell) {
    return `${cell.stringNumber}:${cell.fret}`;
  }

  function ensurePinnedNoteCellInRange() {
    const rows = copedentChartRows();
    const frets = visibleNoteFinderFrets();
    const validStrings = new Set(rows.map((row) => Number(row.string)));
    if (!validStrings.has(Number(pinnedNoteCell.stringNumber)) || !frets.includes(Number(pinnedNoteCell.fret))) {
      pinnedNoteCell = {
        stringNumber: validStrings.has(3) ? 3 : Number(rows[0]?.string || 1),
        fret: frets.includes(3) ? 3 : Number(frets[0] || 0),
      };
    }
  }

  function noteFinderControlButtonsHtml() {
    return availableNoteControlStates()
      .map((state) => `
        <button
          class="explorer-note-finder__chip${selectedNoteControlStateId === state.id ? " is-selected" : ""}"
          type="button"
          data-note-control-state="${escapeHtml(state.id)}"
          aria-pressed="${selectedNoteControlStateId === state.id ? "true" : "false"}"
        >${escapeHtml(state.label)}</button>
      `).join("");
  }

  function noteWorkflowButtonsHtml() {
    return NOTE_WORKFLOWS.map((workflow) => `
      <button
        class="explorer-note-finder__chip${selectedNoteWorkflow === workflow.id ? " is-selected" : ""}"
        type="button"
        data-note-workflow="${escapeHtml(workflow.id)}"
        aria-pressed="${selectedNoteWorkflow === workflow.id ? "true" : "false"}"
        title="${escapeHtml(workflow.description)}"
      >${escapeHtml(workflow.label)}</button>
    `).join("");
  }

  function noteTargetModeButtonsHtml() {
    return NOTE_TARGET_MODES.map((mode) => `
      <button
        class="explorer-note-finder__chip${selectedNoteTargetMode === mode.id ? " is-selected" : ""}"
        type="button"
        data-note-target-mode="${escapeHtml(mode.id)}"
        aria-pressed="${selectedNoteTargetMode === mode.id ? "true" : "false"}"
        title="${escapeHtml(mode.description)}"
      >${escapeHtml(mode.label)}</button>
    `).join("");
  }

  function noteFinderTargetButtonsHtml() {
    const target = selectedNoteFinderTarget();
    return noteFinderTargets().map((item) => `
      <button
        class="explorer-note-finder__chip${target && target.index === item.index ? " is-selected" : ""}"
        type="button"
        data-note-target="${escapeHtml(String(item.index))}"
        aria-pressed="${target && target.index === item.index ? "true" : "false"}"
      >${escapeHtml(item.label)}</button>
    `).join("");
  }

  function noteStringFilterButtonsHtml() {
    return noteStringFilterOptions().map((item) => `
      <button
        class="explorer-note-finder__chip${selectedNoteStringFilter === item.value ? " is-selected" : ""}"
        type="button"
        data-note-string-filter="${escapeHtml(item.value)}"
        aria-pressed="${selectedNoteStringFilter === item.value ? "true" : "false"}"
      >${escapeHtml(item.label)}</button>
    `).join("");
  }

  function noteFinderCellButtonHtml(cell) {
    const pinnedKey = `${pinnedNoteCell.stringNumber}:${pinnedNoteCell.fret}`;
    const key = noteCellKey(cell);
    const classes = [
      "explorer-note-cell",
      cell.isAffected ? "is-affected" : "",
      cell.isTargetMatch ? "is-result" : "",
      cell.isGripMatch ? "is-grip" : "",
      key === pinnedKey ? "is-selected" : "",
    ].filter(Boolean).join(" ");
    const resultAttribute = cell.isTargetMatch ? ` data-note-result="${escapeHtml(key)}"` : "";
    return `
      <button
        class="${classes}"
        type="button"
        data-note-cell="${escapeHtml(key)}"
        data-note-string="${escapeHtml(String(cell.stringNumber))}"
        data-note-fret="${escapeHtml(String(cell.fret))}"
        data-note-final-note="${escapeHtml(cell.finalNote)}"
        ${resultAttribute}
        aria-pressed="${key === pinnedKey ? "true" : "false"}"
        aria-label="${escapeHtml(`String ${cell.stringNumber}, fret ${cell.fret}: ${cellRegisterLabel(cell)} with ${cell.activeControlLabel}`)}"
      ><span>${cell.isTargetMatch ? escapeHtml(cellRegisterLabel(cell)) : ""}</span></button>
    `;
  }

  function noteFinderInstructionText(resultCount) {
    const workflow = activeNoteWorkflow();
    const target = selectedNoteFinderTarget();
    const activeControls = activeNoteControlState();
    if (workflow.id === "changes") {
      return `Comparing open/no-control notes against ${activeControls.label} at fret ${pinnedNoteCell.fret}. Changed strings are highlighted; unchanged strings are marked no change.`;
    }
    if (workflow.id === "reverse") {
      return `Reverse lookup for ${target?.label || "the selected target"} uses the selected string filter and all standard control states. Selecting a result focuses the matching cell.`;
    }
    if (workflow.id === "grip") {
      return "Grip finder searches validated Explorer rows and practical string groups only. It does not invent unsupported grips.";
    }
    if (workflow.id === "drill") {
      return `Practice prompt: find ${target?.label || "the selected target"} with ${activeControls.label} in the visible fret range.`;
    }
    if (workflow.id === "sync") {
      return "Event sync uses safe deterministic example events only in this slice. Each event focuses the matching string, fret, and control state.";
    }
    if (selectedNoteTargetMode === "intervals") {
      return `Finding ${target?.label || "an interval"} from the ${activeKey()} root${target?.note ? ` (${target.note})` : ""} with ${activeControls.label}. ${resultCount} visible matches use the selected fret range.`;
    }
    return `Finding ${target?.label || "scale tones"} with ${activeControls.label}. ${resultCount} visible matches use the selected notation mode and fret range.`;
  }

  function noteFinderResultButtonHtml(cell, options = {}) {
    const key = options.key || noteCellKey(cell);
    const isSelected = options.isSelected || key === `${pinnedNoteCell.stringNumber}:${pinnedNoteCell.fret}`;
    const dataAttribute = options.attribute || "data-note-result-card";
    return `
      <button class="explorer-active-result explorer-note-result-card${isSelected ? " is-selected" : ""}" type="button" ${dataAttribute}="${escapeHtml(key)}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          <span class="explorer-active-result__marker"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(cellRegisterLabel(cell))}</span></span>
          <strong>${escapeHtml(`String ${cell.stringNumber} · fret ${cell.fret}`)}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Open note</b>${escapeHtml(cellOpenRegisterLabel(cell))}</span>
          <span><b>Final note</b>${escapeHtml(cellRegisterLabel(cell))}</span>
          <span><b>Controls</b>${escapeHtml(cell.activeControlLabel)}</span>
          <span><b>${escapeHtml(notationModeLabel())}</b>${escapeHtml(cell.notationValue)}</span>
        </span>
      </button>
    `;
  }

  function noteFinderResultListHtml(cells, currentCell) {
    if (!cells.length) {
      return '<p class="explorer-empty">No notes match this target in the visible fret range. Try a different target, control state, string filter, or fret range.</p>';
    }
    return cells.map((cell) => `
      <button class="explorer-row-button${noteCellKey(cell) === noteCellKey(currentCell) ? " is-selected" : ""}" type="button" data-note-result-list="${escapeHtml(noteCellKey(cell))}">
        <strong>${escapeHtml(`String ${cell.stringNumber}, fret ${cell.fret}: ${cellRegisterLabel(cell)}`)}</strong>
        <span class="explorer-row-button__meta">Open note: ${escapeHtml(cellOpenRegisterLabel(cell))} · Final note: ${escapeHtml(cellRegisterLabel(cell))} · Controls: ${escapeHtml(cell.activeControlLabel)} · ${escapeHtml(notationModeLabel())}: ${escapeHtml(cell.notationValue)}</span>
      </button>
    `).join("");
  }

  function noteChangeRowsHtml(rows) {
    return rows.map((cell) => {
      const controlText = cell.controlChanges.length
        ? cell.controlChanges.map((change) => `${noteControlLabel(change.controlId)}: ${formatValue(change.cell.from, "")} -> ${formatValue(change.cell.to, "")}`).join(", ")
        : "No direct control change";
      return `
        <div class="explorer-note-change-row${cell.isAffected ? " is-affected" : " is-unchanged"}">
          <strong>${escapeHtml(`String ${cell.stringNumber}`)}</strong>
          <span>${escapeHtml(`${cellOpenRegisterLabel(cell)} -> ${cellRegisterLabel(cell)}`)}</span>
          <em>${escapeHtml(cell.isAffected ? controlText : `No change at fret ${cell.fret}`)}</em>
        </div>
      `;
    }).join("");
  }

  function renderFindAllPanel(resultCells) {
    const target = selectedNoteFinderTarget();
    const flatSevenLesson = selectedNoteTargetMode === "intervals" && target?.interval === "b7"
      ? `<section class="explorer-teaching-note" aria-label="Flat seven explanation"><strong>What ♭7 means</strong><p>In ${escapeHtml(activeKey())}, the ♭7 (also written b7) is ${escapeHtml(target.note)}. It is 10 semitones above the root—one semitone below the major 7.</p></section>`
      : "";
    return `
      <section class="explorer-note-workflow-panel" aria-label="Find all matching notes">
        <strong>Find all ${escapeHtml(target?.label || "target")} positions</strong>
        <p>Highlighted cells match the selected ${selectedNoteTargetMode === "intervals" ? "interval" : escapeHtml(notationModeLabel())} target after the active pedal or lever state is applied.</p>
        <p>${escapeHtml(`${resultCells.length} visible ${resultCells.length === 1 ? "match" : "matches"} in ${activeRangeOption().label}.`)}</p>
      </section>
      ${flatSevenLesson}
    `;
  }

  function reverseLookupCells() {
    const frets = visibleNoteFinderFrets();
    const rows = copedentChartRows();
    return availableNoteControlStates().flatMap((state) => rows.flatMap((row) => frets.map((fret) => ({
      ...noteCellState(row.string, fret, state),
      controlStateId: state.id,
    }))))
      .filter((cell) => cell.isTargetMatch && noteMatchesStringFilter(cell))
      .sort((a, b) => {
        const byFret = Number(a.fret) - Number(b.fret);
        if (byFret) {
          return byFret;
        }
        const byString = Number(a.stringNumber) - Number(b.stringNumber);
        if (byString) {
          return byString;
        }
        return String(a.controlStateId || "").localeCompare(String(b.controlStateId || ""));
      })
      .slice(0, 32);
  }

  function reverseLookupKey(cell) {
    return `${cell.controlStateId || "open"}:${cell.stringNumber}:${cell.fret}`;
  }

  function renderReverseLookupPanel() {
    const cells = reverseLookupCells();
    const target = selectedNoteFinderTarget();
    return `
      <section class="explorer-note-workflow-panel" aria-label="Reverse note lookup">
        <strong>How to get ${escapeHtml(target?.label || "target")}</strong>
        <p>These are deterministic ways to reach the target with standard control states in the visible fret range.</p>
        <div class="explorer-note-workflow-grid">
          ${cells.length ? cells.map((cell) => noteFinderResultButtonHtml(cell, {
            key: reverseLookupKey(cell),
            attribute: "data-note-reverse-result",
            isSelected: noteCellKey(cell) === `${pinnedNoteCell.stringNumber}:${pinnedNoteCell.fret}` && selectedNoteControlStateId === cell.controlStateId,
          })).join("") : '<p class="explorer-empty">No reverse-lookup matches for this target and string filter.</p>'}
        </div>
      </section>
    `;
  }

  function renderPedalChangesPanel(currentCell) {
    const rows = noteChangeRowsAtFret(currentCell?.fret || pinnedNoteCell.fret);
    const changedRows = rows.filter((cell) => cell.isAffected);
    const activeControls = activeNoteControlState();
    const activeControlText = noteControlLabels(activeControls.controls).join(" + ");
    const affected = changedRows.map((cell) => cell.stringNumber).join(", ");
    return `
      <section class="explorer-note-workflow-panel" aria-label="Pedal and lever before-after comparison">
        <strong>${escapeHtml(activeControlText)} affected strings</strong>
        <p>${activeControls.controls.length ? escapeHtml(`Affected strings: ${affected || "none"}. Pedals and levers change notes only on affected strings.`) : "Open state has no pedal or lever changes."}</p>
        <div class="explorer-note-change-list">${noteChangeRowsHtml(rows)}</div>
      </section>
    `;
  }

  function gripTargetButtonsHtml() {
    const options = gripTargetOptions();
    return options.map((target) => `
      <button
        class="explorer-note-finder__chip${selectedGripTarget()?.id === target.id ? " is-selected" : ""}"
        type="button"
        data-note-grip-target="${escapeHtml(target.id)}"
        aria-pressed="${selectedGripTarget()?.id === target.id ? "true" : "false"}"
        title="${escapeHtml(target.description)}"
      >${escapeHtml(target.label)}</button>
    `).join("");
  }

  function gripVocabularyButtonsHtml() {
    return gripVocabularyOptions().map((option) => `
      <button
        class="explorer-note-finder__chip${selectedGripVocabularyOption().id === option.id ? " is-selected" : ""}"
        type="button"
        data-note-grip-vocabulary="${escapeHtml(option.id)}"
        aria-pressed="${selectedGripVocabularyOption().id === option.id ? "true" : "false"}"
        title="${escapeHtml(option.description)}"
      >${escapeHtml(option.label)}</button>
    `).join("");
  }

  function gripRoleButtonsHtml() {
    if (!gripVocabularyShowsRoleFilter(selectedGripVocabulary)) {
      return "";
    }
    return `
      <div class="explorer-note-finder__chips" role="group" aria-label="Grip role">
        ${GRIP_ROLE_OPTIONS.map((option) => `
          <button
            class="explorer-note-finder__chip${selectedGripRole === option.id ? " is-selected" : ""}"
            type="button"
            data-note-grip-role="${escapeHtml(option.id)}"
            aria-pressed="${selectedGripRole === option.id ? "true" : "false"}"
            title="${escapeHtml(option.description)}"
          >${escapeHtml(option.label)}</button>
        `).join("")}
      </div>
    `;
  }

  function gripCandidateButtonHtml(row) {
    const isSelected = selectedGripCandidateId === row.id;
    const group = row.string_group || "";
    const roles = gripRoleText(group);
    const padText = gripHasRole(group, "pad_sustain")
      ? "Pad use: this dyad can be sustained as a support layer while another voice moves."
      : "";
    return `
      <button class="explorer-active-result explorer-note-grip-card${isSelected ? " is-selected" : ""}" type="button" data-note-grip-card="${escapeHtml(row.id || "")}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          <span class="explorer-active-result__marker"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(row.string_group)}</span></span>
          <strong>${escapeHtml(`${row.fret} ${normalizePedals(row).join("+") || "open"}`)}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Grip type</b>${escapeHtml(gripTierLabel(group))}</span>
          <span><b>Roles</b>${escapeHtml(roles || "Chord / voicing")}</span>
          <span><b>Strings</b>${escapeHtml(formatValue(row.strings))}</span>
          <span><b>Notes</b>${escapeHtml(formatValue(rowNoteLabels(row)))}</span>
          <span><b>Function</b>${escapeHtml(formatValue(row.chord_function || row.chord_name, ""))}</span>
          <span><b>${escapeHtml(notationModeLabel())}</b>${escapeHtml(formatValue(rowIntervalLabels(row).map(formatIntervalForNotation)))}</span>
          ${padText ? `<span><b>Pad use</b>${escapeHtml(padText)}</span>` : ""}
        </span>
      </button>
    `;
  }

  function renderGripFinderPanel() {
    const target = selectedGripTarget();
    const candidates = gripFinderCandidates();
    return `
      <section class="explorer-note-workflow-panel" aria-label="Build a grip from notes">
        <strong>Build a grip</strong>
        <p>${escapeHtml(`${selectedGripVocabularyOption().description} ${target?.description || "Choose a target note set."}`)}</p>
        <div class="explorer-note-finder__chips" role="group" aria-label="Grip vocabulary">
          ${gripVocabularyButtonsHtml()}
        </div>
        ${gripRoleButtonsHtml()}
        <div class="explorer-note-finder__chips" role="group" aria-label="Grip finder target">
          ${gripTargetButtonsHtml()}
        </div>
        <div class="explorer-note-workflow-grid">
          ${candidates.length ? candidates.map(gripCandidateButtonHtml).join("") : '<p class="explorer-empty">No practical validated grips match this target in the visible fret range.</p>'}
        </div>
      </section>
    `;
  }

  function renderDrillPanel(currentCell) {
    const target = selectedNoteFinderTarget();
    const feedbackClass = drillFeedback?.status === "correct" ? " explorer-note-feedback--correct" : drillFeedback ? " explorer-note-feedback--try" : "";
    return `
      <section class="explorer-note-workflow-panel" aria-label="Single note drill">
        <strong>${escapeHtml(`Drill: find ${target?.label || "the target"}`)}</strong>
        <p>Click a cell that matches the target with ${escapeHtml(activeNoteControlState().label)}. Use the highlighted matches as a hint if you need one.</p>
        ${drillFeedback ? `<div class="explorer-note-feedback${feedbackClass}"><strong>${escapeHtml(drillFeedback.status === "correct" ? "Correct" : "Try again")}</strong><span>${escapeHtml(drillFeedback.message)}</span></div>` : ""}
        <p class="explorer-note-finder__context">Current pinned cell: string ${escapeHtml(currentCell.stringNumber)}, fret ${escapeHtml(currentCell.fret)} gives ${escapeHtml(cellRegisterLabel(currentCell))}.</p>
      </section>
    `;
  }

  function syncEventButtonHtml(event) {
    const isSelected = selectedSyncEvent()?.id === event.id;
    return `
      <button class="explorer-active-result explorer-note-event-card${isSelected ? " is-selected" : ""}" type="button" data-note-sync-event="${escapeHtml(event.id)}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          <span class="explorer-active-result__marker"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(event.step)}</span></span>
          <strong>${escapeHtml(event.label)}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Final note</b>${escapeHtml(cellRegisterLabel(event.cell))}</span>
          <span><b>Controls</b>${escapeHtml(event.controlState.label)}</span>
          <span><b>${escapeHtml(notationModeLabel())}</b>${escapeHtml(event.cell.notationValue)}</span>
        </span>
      </button>
    `;
  }

  function renderEventSyncPanel() {
    const events = syncEventOptions();
    return `
      <section class="explorer-note-workflow-panel" aria-label="Deterministic event sync">
        <strong>Deterministic event sync demo</strong>
        <p>This uses safe built-in educational events only. Full tab/fretboard event sync should use shared backend event data when available.</p>
        <div class="explorer-note-workflow-grid">
          ${events.map(syncEventButtonHtml).join("")}
        </div>
      </section>
    `;
  }

  function renderNoteWorkflowPanel(resultCells, currentCell) {
    const workflow = activeNoteWorkflow();
    if (workflow.id === "reverse") {
      return renderReverseLookupPanel();
    }
    if (workflow.id === "changes") {
      return renderPedalChangesPanel(currentCell);
    }
    if (workflow.id === "grip") {
      return renderGripFinderPanel();
    }
    if (workflow.id === "drill") {
      return renderDrillPanel(currentCell);
    }
    if (workflow.id === "sync") {
      return renderEventSyncPanel();
    }
    return renderFindAllPanel(resultCells);
  }

  function renderNoteFinderGrid(cells) {
    const rows = copedentChartRows();
    const frets = visibleNoteFinderFrets();
    const byStringAndFret = new Map(cells.map((cell) => [noteCellKey(cell), cell]));
    const gridTemplate = `grid-template-columns: 54px repeat(${frets.length}, minmax(34px, 1fr));`;
    return `
      <div class="explorer-note-grid" style="${escapeHtml(gridTemplate)}" role="grid" aria-label="Single-note finder grid">
        <div class="explorer-note-grid__corner" aria-hidden="true"></div>
        ${frets.map((fret) => `<div class="explorer-note-grid__fret" role="columnheader">F${escapeHtml(fret)}</div>`).join("")}
        ${rows.map((row) => `
          <div class="explorer-note-grid__string" role="rowheader">
            <strong>${escapeHtml(row.string)}</strong>
            <span>${escapeHtml(formatValue(row.open_note, ""))}</span>
          </div>
          ${frets.map((fret) => noteFinderCellButtonHtml(byStringAndFret.get(`${Number(row.string)}:${fret}`))).join("")}
        `).join("")}
      </div>
    `;
  }

  function renderNoteFinderDetail(cell) {
    if (!cell) {
      els.selectedDetail.className = "explorer-selected-detail";
      els.selectedDetail.innerHTML = '<p class="explorer-empty">Choose a string and fret to inspect the note.</p>';
      return;
    }
    const scaleText = selectedOptionLabel(els.scale) || `${activeKey()} ${els.scale.value}`;
    els.selectedDetail.className = "explorer-selected-detail";
    els.selectedDetail.innerHTML = `
      <div class="explorer-selected-detail__header">
        <span class="explorer-selected-detail__kind">Single-note finder</span>
        <strong>${escapeHtml(`String ${cell.stringNumber}, fret ${cell.fret}: ${cellRegisterLabel(cell)}`)}</strong>
      </div>
      <section class="explorer-teaching-note" aria-label="Pedal and lever note change">
        <strong>What changed</strong>
        <p>${escapeHtml(cell.explanation)}</p>
      </section>
      <dl class="explorer-detail-grid">
        ${detailRow("String", cell.stringNumber)}
        ${detailRow("Fret", cell.fret)}
        ${detailRow("Active controls", cell.activeControlLabel)}
        ${detailRow("Open string", `${cell.openStringNote} on string ${cell.stringNumber}`)}
        ${detailRow("Open note at fret", cell.openNoteAtFret)}
        ${detailRow("Final note", cell.finalNote)}
        ${detailRow("Open note with register", activePitchRegisterMode() === "off" ? "" : cellOpenRegisterLabel(cell))}
        ${detailRow("Final note with register", activePitchRegisterMode() === "off" ? "" : cellRegisterLabel(cell))}
        ${detailRow(`${notationModeLabel()} in ${scaleText}`, cell.notationValue)}
        ${detailRow(`Interval from ${activeKey()} root`, formatInterval(cell.intervalFromKeyRoot))}
      </dl>
      ${amazingTablatureHandoffHtml([cell.finalNote], {voice: "single"})}
    `;
  }

  function renderNoteFinder() {
    if (!els.noteFinder) {
      return;
    }
    syncNoteFinderSelections();
    ensurePinnedNoteCellInRange();
    const selectedGrip = selectedGripCandidate();
    const cells = visibleNoteCells().map((cell) => decorateNoteCellForRender(cell, selectedGrip));
    const resultCells = cells.filter((cell) => cell.isTargetMatch);
    const target = selectedNoteFinderTarget();
    const currentCell = previewNoteCell
      ? noteCellState(previewNoteCell.stringNumber, previewNoteCell.fret)
      : noteCellState(pinnedNoteCell.stringNumber, pinnedNoteCell.fret);
    const activeControls = activeNoteControlState();
    const workflow = activeNoteWorkflow();
    els.noteFinder.hidden = false;
    els.noteFinder.innerHTML = `
      <div class="explorer-note-finder__header">
        <div>
          <strong>Single-note finder</strong>
          <p>Pedals and levers change the note on affected strings. Choose a control state, then hover or click a string/fret cell.</p>
        </div>
        <span>${escapeHtml(formatValue(activeCopedent()?.label || "E9 copedent"))}</span>
      </div>
      <div class="explorer-note-finder__controls">
        <div>
          <span class="explorer-note-finder__label">Workflow</span>
          <div class="explorer-note-finder__chips" role="group" aria-label="Single-note learning workflow">
            ${noteWorkflowButtonsHtml()}
          </div>
        </div>
        <div>
          <span class="explorer-note-finder__label">Active controls</span>
          <div class="explorer-note-finder__chips" role="group" aria-label="Single-note control state">
            ${noteFinderControlButtonsHtml()}
          </div>
        </div>
        <div>
          <span class="explorer-note-finder__label">Find by</span>
          <div class="explorer-note-finder__chips" role="group" aria-label="Choose notes or intervals">
            ${noteTargetModeButtonsHtml()}
          </div>
        </div>
        <div>
          <span class="explorer-note-finder__label">${selectedNoteTargetMode === "intervals" ? `Interval from ${escapeHtml(activeKey())}` : `Find by ${escapeHtml(notationModeLabel())}`}</span>
          <div class="explorer-note-finder__chips" role="group" aria-label="Find matching single notes">
            ${noteFinderTargetButtonsHtml()}
          </div>
        </div>
        <div>
          <span class="explorer-note-finder__label">String filter</span>
          <div class="explorer-note-finder__chips" role="group" aria-label="Single-note string filter">
            ${noteStringFilterButtonsHtml()}
          </div>
        </div>
      </div>
      <p class="explorer-note-finder__context">${escapeHtml(noteFinderInstructionText(resultCells.length))}</p>
      ${renderNoteWorkflowPanel(resultCells, currentCell)}
    `;

    els.activeResults.innerHTML = `
      <div class="explorer-active-results__header">
        <strong>${escapeHtml(`${workflow.label}: ${resultCells.length} visible ${resultCells.length === 1 ? "match" : "matches"} for ${target?.label || "target"}`)}</strong>
        <span>Cards and grid results use ${escapeHtml(activeControls.label)} unless the workflow card says otherwise.</span>
      </div>
      <div class="explorer-active-results__track">
        ${resultCells.map(noteFinderResultButtonHtml).join("")}
      </div>
    `;
    els.fretboard.innerHTML = renderNoteFinderGrid(cells);
    els.rowList.innerHTML = noteFinderResultListHtml(resultCells, currentCell);
    renderNoteFinderDetail(currentCell);

    const selectCell = (stringNumber, fret) => {
      const selectedCell = decorateNoteCellForRender(noteCellState(stringNumber, fret), selectedGripCandidate());
      pinnedNoteCell = { stringNumber: Number(stringNumber), fret: Number(fret) };
      previewNoteCell = null;
      if (selectedNoteWorkflow === "drill") {
        const targetLabel = selectedNoteFinderTarget()?.label || "the target";
        if (selectedCell.isTargetMatch) {
          drillFeedback = {
            status: "correct",
            message: `String ${selectedCell.stringNumber}, fret ${selectedCell.fret} gives ${selectedCell.finalNote}, which matches ${targetLabel}.`,
          };
        } else {
          drillFeedback = {
            status: "try",
            message: `String ${selectedCell.stringNumber}, fret ${selectedCell.fret} gives ${selectedCell.finalNote}. Try another cell for ${targetLabel}.`,
          };
        }
      }
      renderNoteFinder();
    };
    Array.from(els.noteFinder.querySelectorAll("[data-note-workflow]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedNoteWorkflow = button.getAttribute("data-note-workflow") || "find";
        if (selectedNoteWorkflow !== "grip") {
          selectedGripCandidateId = "";
        }
        drillFeedback = null;
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-control-state]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedNoteControlStateId = button.getAttribute("data-note-control-state") || "open";
        drillFeedback = null;
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-target-mode]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedNoteTargetMode = button.getAttribute("data-note-target-mode") || "scale";
        selectedNoteTargetIndex = 0;
        drillFeedback = null;
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-target]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedNoteTargetIndex = Number(button.getAttribute("data-note-target") || 0);
        drillFeedback = null;
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-string-filter]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedNoteStringFilter = button.getAttribute("data-note-string-filter") || "all";
        drillFeedback = null;
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-grip-target]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedGripTargetId = button.getAttribute("data-note-grip-target") || "scale-triad";
        selectedGripCandidateId = "";
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-grip-vocabulary]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedGripVocabulary = button.getAttribute("data-note-grip-vocabulary") || "core";
        selectedGripTargetId = gripTargetOptions()[0]?.id || "scale-triad";
        syncGripRoleWithVocabulary();
        selectedGripCandidateId = "";
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-grip-role]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedGripRole = button.getAttribute("data-note-grip-role") || "all";
        selectedGripCandidateId = "";
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-grip-card]")).forEach((button) => {
      button.addEventListener("click", () => {
        const rowId = button.getAttribute("data-note-grip-card") || "";
        const row = gripFinderCandidates().find((candidate) => candidate.id === rowId);
        focusGripCandidate(row);
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-sync-event]")).forEach((button) => {
      button.addEventListener("click", () => {
        const eventId = button.getAttribute("data-note-sync-event") || "";
        const event = syncEventOptions().find((item) => item.id === eventId);
        focusSyncEvent(event);
        renderNoteFinder();
      });
    });
    Array.from(els.noteFinder.querySelectorAll("[data-note-reverse-result]")).forEach((button) => {
      button.addEventListener("click", () => {
        const [stateId, stringNumber, fret] = (button.getAttribute("data-note-reverse-result") || "").split(":");
        selectedNoteControlStateId = stateId || "open";
        pinnedNoteCell = { stringNumber: Number(stringNumber), fret: Number(fret) };
        previewNoteCell = null;
        drillFeedback = null;
        renderNoteFinder();
      });
    });
    Array.from(els.fretboard.querySelectorAll("[data-note-cell]")).forEach((button) => {
      const stringNumber = button.getAttribute("data-note-string");
      const fret = button.getAttribute("data-note-fret");
      button.addEventListener("mouseenter", () => {
        previewNoteCell = { stringNumber: Number(stringNumber), fret: Number(fret) };
        renderNoteFinderDetail(noteCellState(stringNumber, fret));
      });
      button.addEventListener("mouseleave", () => {
        previewNoteCell = null;
        renderNoteFinderDetail(noteCellState(pinnedNoteCell.stringNumber, pinnedNoteCell.fret));
      });
      button.addEventListener("click", () => selectCell(stringNumber, fret));
    });
    const resultButtons = [
      ...Array.from(els.activeResults.querySelectorAll("[data-note-result-card]")),
      ...Array.from(els.rowList.querySelectorAll("[data-note-result-list]")),
    ];
    resultButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const raw = button.getAttribute("data-note-result-card") || button.getAttribute("data-note-result-list") || "";
        const [stringNumber, fret] = raw.split(":").map(Number);
        selectCell(stringNumber, fret);
      });
    });
  }

  function renderNoteFinderMode() {
    syncNoteFinderSelections();
    selectedRowId = "";
    currentRows = [];
    currentMarkerGroups = [];
    if (els.topIntervalFilter) {
      els.topIntervalFilter.hidden = true;
      els.topIntervalFilter.innerHTML = "";
    }
    renderFretRangeFilter(
      allNoteCells().map(decorateNoteCellForRender).filter((cell) => cell.isTargetMatch),
      visibleNoteCells().map(decorateNoteCellForRender).filter((cell) => cell.isTargetMatch),
    );
    updateScaleNotes();
    if (els.resultCount) {
      els.resultCount.textContent = "";
    }
    if (els.chordFinder) {
      els.chordFinder.hidden = true;
      els.chordFinder.innerHTML = "";
    }
    els.empty.hidden = true;
    els.empty.textContent = "";
    renderCopedentChart();
    renderControlImpactPreview();
    renderNoteFinder();
    updateContextStrip(visibleNoteCells().map(decorateNoteCellForRender).filter((cell) => cell.isTargetMatch));
    const renderedText = [
      els.noteFinder?.textContent || "",
      els.activeResults?.textContent || "",
      els.rowList?.textContent || "",
      els.selectedDetail?.textContent || "",
      els.fretboard?.textContent || "",
    ].join(" ");
    if (renderedText.includes("[object Object]")) {
      console.warn("Explorer rendered an unsafe object string.");
    }
  }

  function chordFinderTargetSummaryHtml(target) {
    if (!target?.ok) {
      return `<p class="explorer-voicing-identifier__warning">${escapeHtml(target?.message || "Choose a root and quality to search practical E9 voicings.")}</p>`;
    }
    const filterExplanation = chordFinderFilterExplanation(target);
    const flatSevenTeaching = target.quality?.intervals?.includes(10)
      ? chordFinderFlatSevenTeachingHtml(target)
      : "";
    return `
      <section class="explorer-voicing-summary explorer-chord-finder__summary" aria-label="Chord finder target">
        <strong>${escapeHtml(`Target: ${target.label} (${chordFinderQualityDisplayLabel(target.quality)})`)}</strong>
        <p>${escapeHtml(`${target.message ? `${target.message} ` : ""}Chord tones: ${target.toneLabels.map((tone) => `${tone.role} ${tone.note}`).join(", ")}.`)}</p>
        ${filterExplanation ? `<p>${escapeHtml(filterExplanation)}</p>` : ""}
      </section>
      ${flatSevenTeaching}
    `;
  }

  function chordFinderFlatSevenTeachingHtml(target) {
    const root = displayNoteForPitchClassInKey(target.rootPitchClass, target.contextKey);
    const flatSeven = displayNoteForPitchClassInKey(target.rootPitchClass + 10, target.contextKey);
    const majorSeven = displayNoteForPitchClassInKey(target.rootPitchClass + 11, target.contextKey);
    const formula = target.quality.intervals.map((interval) => formatInterval(intervalNameFromSemitones(interval))).join("–");
    return `
      <section class="explorer-teaching-note" aria-label="Flat seven chord-tone explanation">
        <strong>Where the ♭7 is</strong>
        <p>${escapeHtml(`${chordFinderQualityDisplayLabel(target.quality)} uses the formula ${formula}. In ${target.label}, ${flatSeven} is the ♭7 (also written b7) above ${root}. It is 10 semitones above the root—one semitone below the major 7 (${majorSeven}).`)}</p>
      </section>
    `;
  }

  function chordFinderFilterExplanation(target) {
    if (!target?.ok) {
      return "";
    }
    const isDMajor = target.quality?.id === "major" && target.rootPitchClass === pitchClassForNote("D");
    if (!isDMajor) {
      return "";
    }
    if (selectedChordControlScope === "open") {
      return "The 5-7-8 E-lower pocket is hidden in Open only because it requires the E-lower lever.";
    }
    if (!chordFinderGroups().includes("5-7-8")) {
      return "The 5-7-8 E-lower pocket is registered as E-lower pocket vocabulary; choose E-lower pockets or All legitimate to include it.";
    }
    const range = activeRangeOption();
    if (range.min > 3 || range.max < 3) {
      return "The 5-7-8 E-lower D major pocket is registered, but fret 3 is outside the selected fret range.";
    }
    return "";
  }

  function renderChordFinderPanel(target, candidates) {
    if (!els.chordFinder) {
      return;
    }
    els.chordFinder.hidden = false;
    els.chordFinder.innerHTML = `
      <div class="explorer-voicing-identifier__header">
        <div>
          <strong>Chord / Voicing Finder</strong>
          <p>Choose a root and quality, then filter the practical grip vocabulary, fret range, and pedal/lever scope.</p>
        </div>
        <span>${escapeHtml(`${candidates.length} ${candidates.length === 1 ? "candidate" : "candidates"}`)}</span>
      </div>
      <div class="explorer-voicing-identifier__controls explorer-chord-finder__controls">
        <div class="explorer-voicing-identifier__field">
          <label class="explorer-voicing-identifier__label" for="explorer-chord-root">Root</label>
          <select class="explorer-voicing-identifier__input" id="explorer-chord-root">${chordFinderRootOptionsHtml()}</select>
          <p class="explorer-voicing-identifier__context">Use the spelled root you want to search.</p>
        </div>
        <div class="explorer-voicing-identifier__field">
          <label class="explorer-voicing-identifier__label" for="explorer-chord-quality">Quality</label>
          <select class="explorer-voicing-identifier__input" id="explorer-chord-quality">${chordFinderQualityOptionsHtml()}</select>
          <p class="explorer-voicing-identifier__context">Examples: Major 7, Dominant 7, Minor 9.</p>
        </div>
        <div class="explorer-voicing-identifier__field">
          <label class="explorer-voicing-identifier__label" for="explorer-chord-control-scope">Pedals / levers scope</label>
          <select class="explorer-voicing-identifier__input" id="explorer-chord-control-scope">${chordFinderControlScopeOptionsHtml()}</select>
        </div>
      </div>
      ${chordFinderTargetSummaryHtml(target)}
    `;
    const rootInput = document.getElementById("explorer-chord-root");
    if (rootInput) {
      rootInput.addEventListener("change", () => {
        selectedChordRoot = rootInput.value || "F";
        selectedChordCandidateId = "";
        selectedChordMapFilter = "all";
        renderChordFinderMode();
      });
    }
    const qualityInput = document.getElementById("explorer-chord-quality");
    if (qualityInput) {
      qualityInput.addEventListener("change", () => {
        selectedChordQuality = qualityInput.value || "major7";
        selectedChordCandidateId = "";
        selectedChordMapFilter = "all";
        renderChordFinderMode();
      });
    }
    const scopeInput = document.getElementById("explorer-chord-control-scope");
    if (scopeInput) {
      scopeInput.addEventListener("change", () => {
        selectedChordControlScope = scopeInput.value || "common";
        selectedChordCandidateId = "";
        selectedChordMapFilter = "all";
        renderChordFinderMode();
      });
    }
  }

  function chordFinderResultCardHtml(row, dataAttributeName) {
    const isSelected = row.id === selectedRowId;
    const finder = row.chord_finder || {};
    const controls = normalizePedals(row);
    const present = formatValue(finder.presentTones, "");
    const omitted = formatValue(finder.omittedTones, "none");
    const markerLabel = markerLabelForRow(row);
    const markerOverflowCount = markerOverflowCountForGroup(currentMarkerGroups.find((item) => item.id === markerGroupKey(row)) || { rows: [row] });
    const markerTone = markerToneForRow(row);
    return `
      <button class="explorer-active-result explorer-chord-map-card${isAdvanced(row) ? " explorer-active-result--advanced" : ""}${isSelected ? " is-selected" : ""}" type="button" ${dataAttributeName}="${escapeHtml(row.id)}" data-chord-finder-result="${escapeHtml(row.id)}" data-marker-id="${escapeHtml(markerGroupKey(row))}" data-marker-tone="${escapeHtml(markerTone)}" data-string-group="${escapeHtml(row.string_group)}" data-chord-map-filter="${escapeHtml(chordFinderControlFilter(row))}" data-chord-completeness="${escapeHtml(chordFinderCompleteness(row))}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          ${markerLabel ? `<span class="explorer-active-result__marker" aria-label="Matching fretboard marker ${escapeHtml(markerLabel)}${markerOverflowCount ? ` plus ${markerOverflowCount} more` : ""}"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(markerLabel)}</span>${markerOverflowCount ? `<small aria-hidden="true">+${markerOverflowCount}</small>` : ""}</span>` : ""}
          <strong>${escapeHtml(row.chord_name || row.display_summary || "Chord finder result")}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Fret</b>${escapeHtml(formatValue(row.fret))}</span>
          <span><b>Strings</b>${escapeHtml(row.string_group)}</span>
          <span><b>Pedals/levers</b>${escapeHtml(controls.length ? `With ${controls.join("+")}` : "Open")}</span>
          <span><b>Grip</b>${escapeHtml(formatValue(finder.gripTier))}</span>
          ${finder.whyGrip ? `<span><b>Why</b>${escapeHtml(finder.whyGrip)}</span>` : ""}
          <span><b>Confidence</b>${escapeHtml(formatValue(finder.confidence))}</span>
          <span><b>Present</b>${escapeHtml(present)}</span>
          <span><b>Omitted</b>${escapeHtml(omitted)}</span>
        </span>
      </button>
    `;
  }

  function chordFinderMapFiltersHtml(allRows, visibleRows) {
    const options = chordFinderMapFilterOptions(allRows);
    return `
      <div class="explorer-chord-map-filters" role="group" aria-label="Filter chord candidates shown on the fretboard">
        ${options.map((item) => `
          <button class="explorer-chord-map-filter${selectedChordMapFilter === item.id ? " is-selected" : ""}" type="button" data-chord-map-filter-control="${escapeHtml(item.id)}" aria-pressed="${selectedChordMapFilter === item.id ? "true" : "false"}"${item.count ? "" : " disabled"}>
            <span>${escapeHtml(item.label)}</span>
            <small>${escapeHtml(String(item.count))}</small>
          </button>
        `).join("")}
      </div>
      <p class="explorer-chord-map-summary">${escapeHtml(`${visibleRows.length} of ${allRows.length} candidates shown on the fretboard. Cards and SVG markers use the same colors.`)}</p>
    `;
  }

  function renderChordFinderResults(target, rows, allRows = rows) {
    const selected = selectedChordCandidate(rows);
    const targetLabel = target?.ok ? target.label : "target";
    if (!rows.length) {
      const message = target?.ok
        ? allRows.length
          ? `No ${targetLabel} candidates match this card filter. Try All, a different fret bucket, or a broader pedals/levers scope.`
          : `No practical voicing found for ${targetLabel} with the current grip vocabulary, control scope, and fret range. Try All practical, Include levers, or All frets.`
        : target?.message || "Enter a chord target to search.";
      els.activeResults.innerHTML = `
        <div class="explorer-active-results__header">
          <strong>No Chord / Voicing Finder candidates</strong>
          <span>${escapeHtml(message)}</span>
        </div>
        ${allRows.length ? chordFinderMapFiltersHtml(allRows, rows) : ""}
      `;
      els.rowList.innerHTML = "";
      Array.from(els.activeResults.querySelectorAll("[data-chord-map-filter-control]")).forEach((button) => {
        button.addEventListener("click", () => {
          selectedChordMapFilter = button.getAttribute("data-chord-map-filter-control") || "all";
          selectedChordCandidateId = "";
          renderChordFinderMode();
        });
      });
      return;
    }
    els.activeResults.innerHTML = `
      <div class="explorer-active-results__header">
        <strong>${escapeHtml(`${targetLabel}: ${rows.length} mapped ${rows.length === 1 ? "candidate" : "candidates"}`)}</strong>
        <span>All visible cards are also visible on the SVG. Select any card or marker to inspect it.</span>
      </div>
      ${chordFinderMapFiltersHtml(allRows, rows)}
      <div class="explorer-active-results__track explorer-active-results__track--wrap">
        ${rows.map((row) => chordFinderResultCardHtml(row, "data-active-result-row")).join("")}
      </div>
    `;
    els.rowList.innerHTML = "";
    const wireButton = (button) => {
      const rowId = button.getAttribute("data-chord-finder-result") || button.getAttribute("data-active-result-row") || button.getAttribute("data-explorer-row") || "";
      button.addEventListener("click", () => {
        selectedChordCandidateId = rowId;
        selectRow(rowId);
      });
      button.addEventListener("mouseenter", () => showMarkerForRow(rowId));
      button.addEventListener("focus", () => showMarkerForRow(rowId));
      button.addEventListener("mouseleave", clearMarkerHover);
      button.addEventListener("blur", clearMarkerHover);
    };
    Array.from(els.activeResults.querySelectorAll("[data-chord-finder-result]")).forEach(wireButton);
    Array.from(els.activeResults.querySelectorAll("[data-chord-map-filter-control]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedChordMapFilter = button.getAttribute("data-chord-map-filter-control") || "all";
        selectedChordCandidateId = "";
        renderChordFinderMode();
      });
    });
    selectedChordCandidateId = selected?.id || "";
  }

  function renderChordFinderDetail(row) {
    if (!row) {
      els.selectedDetail.className = "explorer-selected-detail";
      els.selectedDetail.innerHTML = '<p class="explorer-empty">Choose a Chord / Voicing Finder candidate to inspect it.</p>';
      return;
    }
    const finder = row.chord_finder || {};
    const target = finder.target || {};
    els.selectedDetail.className = isAdvanced(row) ? "explorer-selected-detail explorer-selected-detail--advanced" : "explorer-selected-detail";
    els.selectedDetail.innerHTML = `
      <div class="explorer-selected-detail__header">
        <span class="explorer-selected-detail__kind">${escapeHtml(finder.gripTier || groupLabel(row))}</span>
        <strong>${escapeHtml(row.chord_name || row.display_summary || "Chord finder candidate")}</strong>
      </div>
      <section class="explorer-teaching-note" aria-label="Why this voicing matches">
        <strong>Why this voicing matches</strong>
        <p>${escapeHtml(formatTheoryText(row.explanation_summary || `This candidate matches ${target.label || "the target chord"} from deterministic E9 pitch logic.`))}</p>
      </section>
      <dl class="explorer-detail-grid">
        ${detailRow("Target", target.label)}
        ${detailRow("Fret", row.fret)}
        ${detailRow("String group", row.string_group)}
        ${detailRow("Grip type", finder.gripTier)}
        ${detailRow("Why use this grip", finder.whyGrip)}
        ${detailRow("Watch out", finder.gripWatchOut)}
        ${detailRow("Pedals / levers", normalizePedals(row))}
        ${detailRow("Notes", rowNoteLabels(row))}
        ${detailRow("Present chord tones", finder.presentTones)}
        ${detailRow("Omitted tones", finder.omittedTones)}
        ${detailRow("Confidence", finder.confidence)}
        ${detailRow("Notation mode", notationModeLabel())}
        ${detailRow("Warnings", row.warnings)}
      </dl>
      ${stringActionRowsHtml(row)}
      ${amazingTablatureHandoffHtml(
        [topVoice(row).note],
        {voice: "three_voice", movement: "best_fit", chord: target.label || row.chord_name || ""}
      )}
    `;
  }

  function renderChordFinderMode() {
    const target = parseChordFinderQuery();
    const rowsBeforeRange = chordFinderCandidates(target, { ignoreRange: true });
    const allRows = chordFinderCandidates(target);
    if (!chordFinderMapFilterOptions(allRows).some((item) => item.id === selectedChordMapFilter)) {
      selectedChordMapFilter = "all";
    }
    const rows = chordFinderVisibleRows(allRows);
    const selected = selectedChordCandidate(rows);
    selectedRowId = selected?.id || "";
    selectedChordCandidateId = selectedRowId;
    currentRows = rows;
    const rowsForMap = chordFinderRowsForMap(rows, selected);
    currentMarkerGroups = groupRowsForMarkers(rowsForMap);
    if (els.noteFinder) {
      els.noteFinder.hidden = true;
      els.noteFinder.innerHTML = "";
    }
    if (els.voicingIdentifier) {
      els.voicingIdentifier.hidden = true;
      els.voicingIdentifier.innerHTML = "";
    }
    if (els.topIntervalFilter) {
      els.topIntervalFilter.hidden = true;
      els.topIntervalFilter.innerHTML = "";
    }
    updateScaleNotes();
    if (els.resultCount) {
      els.resultCount.textContent = "";
    }
    els.empty.hidden = true;
    els.empty.textContent = "";
    renderCopedentChart();
    renderChordFinderPanel(target, rows);
    renderFretRangeFilter(rowsBeforeRange, rows);
    renderControlImpactPreview();
    updateContextStrip(rows);
    renderChordFinderResults(target, rows, allRows);
    renderFretboard(rowsForMap, { showHighlightLabels: false });
    renderChordFinderDetail(selected);
    syncSelectedState();
    const renderedText = [
      els.chordFinder?.textContent || "",
      els.activeResults?.textContent || "",
      els.rowList?.textContent || "",
      els.selectedDetail?.textContent || "",
      els.fretboard?.textContent || "",
    ].join(" ");
    if (renderedText.includes("[object Object]")) {
      console.warn("Explorer rendered an unsafe object string.");
    }
  }

  function voicingStringActionRowsHtml(cells) {
    if (!cells.length) {
      return "";
    }
    return `
      <section class="explorer-string-actions" aria-label="Voicing string actions">
        <strong>Per-string details</strong>
        ${cells.map((cell) => `
          <div class="explorer-string-action">
            <span>String ${escapeHtml(cell.stringNumber)}</span>
            <span>${escapeHtml(cellOpenRegisterLabel(cell))} -> ${escapeHtml(cellRegisterLabel(cell))}</span>
            <span>${escapeHtml(cell.isAffected ? cell.activeControlLabel : "no change")}</span>
            <span>${escapeHtml(`${notationModeLabel()}: ${cell.notationValue}`)}</span>
          </div>
        `).join("")}
      </section>
    `;
  }

  function renderVoicingIdentifierDetail(row, result, identity) {
    const controlText = result.controlState.label;
    const combinationText = result.controlState.controls.length > 1
      ? ` This combination was created by selecting ${noteControlLabels(result.controlState.controls).join(" and ")} individually.`
      : "";
    const alternateGripText = voicingIdentifierAlternateGripText(result);
    const gripWarningText = result.gripWarning ? ` ${result.gripWarning}` : "";
    const identityWarnings = toArray(identity.warnings);
    const keyLabelTitle = notationMode === "notes" ? "Selected-key note labels" : `${notationModeLabel()} against key`;
    const explanationText = identity.explanation || `${identity.label} is the best common-name match for ${result.cells.map((cell) => cell.finalNote).join(", ")}. Confidence is ${identity.confidence}. ${identity.partial ? "This is a partial or ambiguous voicing, so context matters." : "The selected notes match the chord tones directly."}`;
    els.selectedDetail.className = "explorer-selected-detail";
    els.selectedDetail.innerHTML = `
      <div class="explorer-selected-detail__header">
        <span class="explorer-selected-detail__kind">Voicing identifier</span>
        <strong>${escapeHtml(voicingIdentifierTitle(result, identity))}</strong>
      </div>
      <section class="explorer-teaching-note" aria-label="Voicing explanation">
        <strong>Why this name fits</strong>
        <p>${escapeHtml(`${explanationText}${combinationText}${alternateGripText}${gripWarningText}`)}</p>
        ${identityWarnings.length ? `<p>${escapeHtml(identityWarnings.join(" "))}</p>` : ""}
      </section>
      <dl class="explorer-detail-grid">
        ${detailRow("Voicing status", voicingStatusLabel(identity))}
        ${detailRow("Fret", result.fret)}
        ${detailRow("Strings", result.strings.join("-"))}
        ${detailRow("Grip type", result.gripLabel)}
        ${detailRow("Why use this grip", result.gripExplanation)}
        ${detailRow("Watch out", result.gripWatchOut)}
        ${detailRow("Pedals / levers", controlText)}
        ${detailRow("Notes", result.cells.map((cell) => cell.finalNote))}
        ${detailRow("Present tones", identity.present_tones || [])}
        ${detailRow("Notes with register", activePitchRegisterMode() === "off" ? "" : result.cells.map((cell) => cellRegisterLabel(cell)))}
        ${detailRow(keyLabelTitle, result.cells.map((cell) => cell.notationValue))}
        ${detailRow("Intervals in voicing", identity.intervals.map(formatInterval))}
        ${detailRow("Likely function", identity.functionText)}
        ${detailRow("Omitted tones", identity.omitted_tones || identity.missingIntervals?.map(formatInterval))}
        ${detailRow("Confidence", identity.confidence)}
        ${detailRow("Alternate readings", identity.alternate_readings || identity.alternates)}
        ${detailRow("Warnings", identityWarnings)}
      </dl>
      ${voicingStringActionRowsHtml(result.cells)}
      ${amazingTablatureHandoffHtml(
        [result.cells.at(-1)?.finalNote],
        {voice: result.strings.length >= 3 ? "three_voice" : "two_voice", chord: identity.label || ""}
      )}
    `;
  }

  function voicingIdentifierTitle(result, identity) {
    const status = String(identity.voicing_status || "").toLowerCase();
    const shouldSayChord = result.strings.length > 1 && !["color", "partial", "ambiguous", "unsupported", "rootless"].includes(status);
    const baseLabel = shouldSayChord ? `${identity.label} chord` : identity.label;
    return identity.functionText ? `${baseLabel} (${identity.functionText})` : baseLabel;
  }

  function voicingStatusLabel(identity) {
    const labels = {
      full: "Full chord",
      partial: "Partial voicing",
      color: "Color voicing / no 3rd",
      rootless: "Rootless voicing",
      ambiguous: "Ambiguous",
      unsupported: "Not enough notes",
    };
    const status = String(identity?.voicing_status || "").toLowerCase();
    return labels[status] || (identity?.partial ? "Partial voicing" : "Full chord");
  }

  function voicingIdentifierAlternateGripText(result) {
    if (result.strings.includes(4) && result.strings.includes(10) && !result.strings.includes(8)) {
      return " This is an alternate spread grip: it uses string 4 instead of string 8, so the upper voice sits higher than the common lower-string pocket.";
    }
    return "";
  }

  function voicingRootLabel(identity) {
    const label = formatValue(identity?.label || "", "");
    const match = label.match(/^([A-G](?:#|b)?)/);
    if (match) {
      return match[1];
    }
    if (Number.isFinite(identity?.rootPitchClass)) {
      return displayNoteForPitchClassInKey(identity.rootPitchClass);
    }
    return activeKey();
  }

  function voicingLearnerTitle(identity) {
    const status = String(identity?.voicing_status || "").toLowerCase();
    const root = voicingRootLabel(identity);
    if (status === "color") {
      return `${root} color voicing — no 3rd`;
    }
    if (status === "partial") {
      return `${identity.label} partial voicing`;
    }
    if (status === "rootless") {
      return `${identity.label} rootless voicing`;
    }
    if (status === "ambiguous") {
      return `${identity.label} ambiguous voicing`;
    }
    if (status === "unsupported") {
      return "Not enough notes to name a voicing";
    }
    return `${identity.label} chord`;
  }

  function voicingConfidenceLabel(identity) {
    const confidence = formatValue(identity?.confidence || "", "");
    return confidence ? confidence.charAt(0).toUpperCase() + confidence.slice(1) : "Unknown";
  }

  function parseToneLabel(tone) {
    const text = formatValue(tone, "");
    const match = text.match(/^(.+?)\s*\(([^)]+)\)$/);
    if (!match) {
      return { role: text, note: "" };
    }
    return { role: match[1].trim(), note: match[2].trim() };
  }

  function displayToneRole(role) {
    const normalized = formatValue(role, "").toLowerCase();
    if (normalized === "9th") {
      return "9th / 2nd";
    }
    if (normalized === "11th") {
      return "11th / 4th";
    }
    if (normalized === "13th") {
      return "13th / 6th";
    }
    return formatValue(role, "");
  }

  function toneRoleForCell(cell, identity) {
    const cellPitchClass = pitchClassForNote(cell.finalNote);
    const tone = toArray(identity.present_tones).map(parseToneLabel).find((candidate) => (
      candidate.note && pitchClassForNote(candidate.note) === cellPitchClass
    ));
    return tone ? displayToneRole(tone.role) : formatValue(cell.notationValue || cell.finalNote, "");
  }

  function chipListHtml(items, className = "explorer-voicing-chip") {
    return toArray(items).map((item) => `<span class="${className}">${escapeHtml(formatValue(item, ""))}</span>`).join("");
  }

  function voicingToneRowsHtml(result, identity) {
    return result.cells.map((cell) => `
      <li>
        <span>String ${escapeHtml(cell.stringNumber)}</span>
        <strong>${escapeHtml(cell.finalNote)}</strong>
        <span>= ${escapeHtml(toneRoleForCell(cell, identity))}</span>
      </li>
    `).join("");
  }

  function voicingUseNotes(result, identity) {
    const status = String(identity?.voicing_status || "").toLowerCase();
    if (status === "color") {
      return [
        "Use as a color/partial voicing, not as your main beginner major grip.",
        "Good for a suspended, open sound or a passing color.",
      ];
    }
    if (status === "partial" || status === "rootless") {
      return [
        "Use when the band, melody, or next grip supplies the missing chord tone.",
        "Treat it as context-dependent until the missing tone is clear.",
      ];
    }
    if (status === "ambiguous" || status === "unsupported") {
      return [
        "Use this as a pitch check first; add another chord tone before treating it as a named voicing.",
      ];
    }
    if (result.gripExplanation) {
      return [result.gripExplanation];
    }
    return ["Use this as a complete voicing for the selected fret, strings, and pedals/levers."];
  }

  function voicingCautionNotes(identity) {
    const status = String(identity?.voicing_status || "").toLowerCase();
    const root = voicingRootLabel(identity);
    const warnings = toArray(identity.warnings);
    const notes = [];
    if (status === "color" || toArray(identity.omitted_tones).some((tone) => /3rd/i.test(formatValue(tone, "")))) {
      notes.push(`This is not a complete ${root} major chord by itself.`);
      notes.push(`For a plain ${root} major grip, use a full triad such as 4-5-6, 5-6-8, or 6-8-10 where available.`);
    }
    warnings.forEach((warning) => {
      if (!notes.some((note) => note.toLowerCase() === formatValue(warning, "").toLowerCase())) {
        notes.push(warning);
      }
    });
    return notes;
  }

  function voicingIdentifierStructuredSummaryHtml(result, identity) {
    const omitted = identity.omitted_tones || identity.missingIntervals || [];
    const alternates = identity.alternate_readings || identity.alternates || [];
    const cautionNotes = voicingCautionNotes(identity);
    return `
      <section class="explorer-voicing-summary" aria-label="Identified voicing">
        <div class="explorer-voicing-summary__header">
          <div class="explorer-voicing-summary__title">
            <strong>${escapeHtml(voicingLearnerTitle(identity))}</strong>
            <span>Technical name: ${escapeHtml(identity.label)}</span>
          </div>
          <div class="explorer-voicing-summary__chips" aria-label="Voicing status">
            <span class="explorer-voicing-chip">${escapeHtml(voicingStatusLabel(identity))}</span>
            <span class="explorer-voicing-chip">Confidence: ${escapeHtml(voicingConfidenceLabel(identity))}</span>
            <span class="explorer-voicing-chip">Fret ${escapeHtml(result.fret)}</span>
            <span class="explorer-voicing-chip">strings ${escapeHtml(result.strings.join("-"))}</span>
            <span class="explorer-voicing-chip">${escapeHtml(result.controlState.label)}</span>
          </div>
        </div>
        <div class="explorer-voicing-summary__sections">
          <section class="explorer-voicing-summary__section">
            <h4>What notes are here</h4>
            <ul class="explorer-voicing-tone-list">${voicingToneRowsHtml(result, identity)}</ul>
          </section>
          <section class="explorer-voicing-summary__section">
            <h4>What is missing</h4>
            <div class="explorer-voicing-summary__chips">${chipListHtml(omitted)}</div>
            ${toArray(omitted).some((tone) => /3rd/i.test(formatValue(tone, ""))) ? "<p>Because there is no 3rd, this does not define major vs minor by itself.</p>" : ""}
          </section>
          <section class="explorer-voicing-summary__section">
            <h4>How to use it</h4>
            <ul>${voicingUseNotes(result, identity).map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>
          </section>
          ${toArray(alternates).length ? `
            <section class="explorer-voicing-summary__section">
              <h4>Alternate readings</h4>
              <div class="explorer-voicing-summary__chips">${chipListHtml(alternates)}</div>
            </section>
          ` : ""}
          ${cautionNotes.length ? `
            <section class="explorer-voicing-summary__section explorer-voicing-summary__section--warning">
              <h4>Warning / caution</h4>
              <ul>${cautionNotes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>
            </section>
          ` : ""}
        </div>
      </section>
    `;
  }

  function renderVoicingIdentifierPanel(result, identity) {
    if (!els.voicingIdentifier) {
      return;
    }
    els.voicingIdentifier.hidden = false;
    els.voicingIdentifier.innerHTML = `
      <div class="explorer-voicing-identifier__header">
        <div>
          <strong>Voicing identifier</strong>
          <p>Choose a fret, up to four strings, and any individual pedals/levers. The result is calculated from the selected copedent and key.</p>
        </div>
        <span>${escapeHtml(formatValue(activeCopedent()?.label || "E9 copedent"))}</span>
      </div>
      <div class="explorer-voicing-identifier__controls">
        <div class="explorer-voicing-identifier__field">
          <label class="explorer-voicing-identifier__label" for="explorer-voicing-fret">Fret</label>
          <select class="explorer-voicing-identifier__input" id="explorer-voicing-fret">
            ${Array.from({ length: 10 }, (_, index) => index + 1).map((fret) => `
              <option value="${escapeHtml(fret)}"${Number(voicingFret) === fret ? " selected" : ""}>${escapeHtml(fret)}</option>
            `).join("")}
          </select>
        </div>
        <div class="explorer-voicing-identifier__field">
          <span class="explorer-voicing-identifier__label">Strings</span>
          <div class="explorer-voicing-identifier__chips" role="group" aria-label="Voicing strings">${voicingStringButtonsHtml()}</div>
          <p class="explorer-voicing-identifier__context">Select 1, 2, 3, or 4 strings.</p>
        </div>
        <div class="explorer-voicing-identifier__field">
          <span class="explorer-voicing-identifier__label">Pedals / levers</span>
          <div class="explorer-voicing-identifier__chips" role="group" aria-label="Voicing pedal and lever controls">${voicingControlButtonsHtml()}</div>
        </div>
      </div>
      ${result.warning || voicingUiWarning || result.gripWarning ? `<p class="explorer-voicing-identifier__warning">${escapeHtml([result.warning, voicingUiWarning, result.gripWarning].filter(Boolean).join(" "))}</p>` : ""}
      ${result.warning ? "" : voicingIdentifierStructuredSummaryHtml(result, identity)}
    `;

    const fretInput = document.getElementById("explorer-voicing-fret");
    if (fretInput) {
      fretInput.addEventListener("change", () => {
        voicingFret = Number.parseInt(fretInput.value, 10) || 3;
        voicingUiWarning = "";
        renderVoicingIdentifierMode();
      });
    }
    Array.from(els.voicingIdentifier.querySelectorAll("[data-voicing-string]")).forEach((button) => {
      button.addEventListener("click", () => {
        const stringNumber = Number.parseInt(button.getAttribute("data-voicing-string") || "", 10);
        if (!Number.isInteger(stringNumber)) {
          return;
        }
        if (selectedVoicingStrings.includes(stringNumber)) {
          selectedVoicingStrings = selectedVoicingStrings.filter((item) => item !== stringNumber);
          voicingUiWarning = "";
        } else if (selectedVoicingStrings.length >= 4) {
          voicingUiWarning = "Choose up to 4 strings. Remove one string before adding another.";
        } else {
          selectedVoicingStrings = selectedVoicingStrings.concat(stringNumber).sort((a, b) => a - b);
          voicingUiWarning = "";
        }
        renderVoicingIdentifierMode();
      });
    });
    Array.from(els.voicingIdentifier.querySelectorAll("[data-voicing-control]")).forEach((button) => {
      button.addEventListener("click", () => {
        const controlId = button.getAttribute("data-voicing-control") || "";
        if (selectedVoicingControlIds.has(controlId)) {
          selectedVoicingControlIds.delete(controlId);
        } else {
          selectedVoicingControlIds.add(controlId);
        }
        voicingUiWarning = "";
        renderVoicingIdentifierMode();
      });
    });
    Array.from(els.voicingIdentifier.querySelectorAll("[data-voicing-control-clear]")).forEach((button) => {
      button.addEventListener("click", () => {
        selectedVoicingControlIds = new Set();
        voicingUiWarning = "";
        renderVoicingIdentifierMode();
      });
    });
  }

  function renderVoicingIdentifierMode() {
    const result = voicingStringStates();
    const identity = result.warning ? null : identifyVoicing(result.cells.map((cell) => cell.finalNote));
    if (/^dominant 7$/i.test(identity?.quality || "")) {
      result.gripLabel = "Dominant 7 / V7 grip";
    }
    const row = result.warning ? null : voicingSyntheticRow(result, identity);
    selectedRowId = row?.id || "";
    currentRows = row ? [row] : [];
    currentMarkerGroups = row ? groupRowsForMarkers([row]) : [];
    if (els.noteFinder) {
      els.noteFinder.hidden = true;
      els.noteFinder.innerHTML = "";
    }
    if (els.chordFinder) {
      els.chordFinder.hidden = true;
      els.chordFinder.innerHTML = "";
    }
    if (els.topIntervalFilter) {
      els.topIntervalFilter.hidden = true;
      els.topIntervalFilter.innerHTML = "";
    }
    if (els.fretRangeFilter) {
      els.fretRangeFilter.hidden = true;
      els.fretRangeFilter.innerHTML = "";
    }
    updateScaleNotes();
    if (els.resultCount) {
      els.resultCount.textContent = "";
    }
    els.empty.hidden = true;
    els.empty.textContent = "";
    renderCopedentChart();
    renderControlImpactPreview();
    renderVoicingIdentifierPanel(result, identity);
    updateContextStrip(currentRows);
    if (!row) {
      els.activeResults.innerHTML = '<p class="explorer-empty">Fix the fret or string entry to identify the voicing.</p>';
      els.rowList.innerHTML = "";
      els.fretboard.innerHTML = "";
      els.selectedDetail.innerHTML = '<p class="explorer-empty">No voicing result yet.</p>';
      return;
    }
    els.activeResults.innerHTML = `
      <div class="explorer-active-results__header">
        <strong>${escapeHtml(`Identified ${voicingIdentifierTitle(result, identity)}`)}</strong>
      </div>
      <div class="explorer-active-results__track">
        ${resultButtonHtml(row, "data-active-result-row")}
      </div>
    `;
    els.rowList.innerHTML = resultButtonHtml(row, "data-explorer-row");
    renderFretboard([row]);
    renderVoicingIdentifierDetail(row, result, identity);
    syncSelectedState();
    Array.from(els.activeResults.querySelectorAll("[data-active-result-row]")).forEach((button) => {
      button.addEventListener("click", () => selectRow(button.getAttribute("data-active-result-row")));
    });
    Array.from(els.rowList.querySelectorAll("[data-explorer-row]")).forEach((button) => {
      button.addEventListener("click", () => selectRow(button.getAttribute("data-explorer-row")));
    });
    const renderedText = [
      els.voicingIdentifier?.textContent || "",
      els.activeResults?.textContent || "",
      els.rowList?.textContent || "",
      els.selectedDetail?.textContent || "",
      els.fretboard?.textContent || "",
    ].join(" ");
    if (renderedText.includes("[object Object]")) {
      console.warn("Explorer rendered an unsafe object string.");
    }
  }

  function render() {
    if (isChordFinderMode()) {
      renderChordFinderMode();
      return;
    }
    if (isVoicingIdentifierMode()) {
      renderVoicingIdentifierMode();
      return;
    }
    if (isNoteFinderMode()) {
      renderNoteFinderMode();
      return;
    }
    if (els.noteFinder) {
      els.noteFinder.hidden = true;
      els.noteFinder.innerHTML = "";
    }
    if (els.voicingIdentifier) {
      els.voicingIdentifier.hidden = true;
      els.voicingIdentifier.innerHTML = "";
    }
    if (els.chordFinder) {
      els.chordFinder.hidden = true;
      els.chordFinder.innerHTML = "";
    }
    const baseRows = getBaseRows();
    syncSelectedTopFilter(baseRows);
    renderTopIntervalFilter(baseRows);
    const rowsBeforeRange = getRowsBeforeRange(baseRows);
    const rows = getRows();
    renderFretRangeFilter(rowsBeforeRange, rows);
    currentRows = rows;
    if (!rows.some((row) => row.id === selectedRowId)) {
      selectedRowId = rows[0]?.id || "";
    }
    updateScaleNotes();
    if (els.resultCount) {
      els.resultCount.textContent = "";
    }
    els.empty.hidden = rows.length > 0;
    els.empty.textContent = rows.length
      ? ""
      : `No validated ${isPathMode() ? "harmonized scale path" : (HARMONY_LABELS[activeHarmonyValue()] || "Explorer")} rows are available for ${els.scale.options[els.scale.selectedIndex]?.text || "this scale"} yet.`;
    renderCopedentChart();
    renderControlImpactPreview();
    currentMarkerGroups = groupRowsForMarkers(rows);
    updateContextStrip(rows);
    renderActiveResults(rows);
    renderCards(rows);
    renderFretboard(pathRowsForFretboard(rows));
    renderSelectedDetail(rows.find((row) => row.id === selectedRowId));
    syncSelectedState();

    const renderedText = [
      els.rowList.textContent,
      els.selectedDetail.textContent,
      els.copedentChart?.textContent || "",
      els.controlPreview?.textContent || "",
      els.topIntervalFilter?.textContent || "",
      els.fretRangeFilter?.textContent || "",
      els.fretboard.textContent,
      els.tooltip.textContent,
    ].join(" ");
    if (renderedText.includes("[object Object]")) {
      console.warn("Explorer rendered an unsafe object string.");
    }
  }

  function updateNotationModeButtons() {
    Array.from(els.notationModeButtons || []).forEach((button) => {
      const isSelected = button.getAttribute("data-explorer-notation-mode") === notationMode;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
  }

  function updatePitchRegisterButtons() {
    Array.from(els.pitchRegisterButtons || []).forEach((button) => {
      const isSelected = button.getAttribute("data-explorer-pitch-register") === activePitchRegisterMode();
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
  }

  function updateStringActionLabelToggle() {
    if (!els.stringActionLabelToggle) {
      return;
    }
    els.stringActionLabelToggle.classList.toggle("is-selected", showStringActionLabels);
    els.stringActionLabelToggle.setAttribute("aria-pressed", showStringActionLabels ? "true" : "false");
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
    updateKeyOptions();
    applyExplorerQueryState();
    if (!activePayload()) {
      els.empty.hidden = false;
      els.empty.textContent = "Explorer data failed to load.";
      return;
    }

    updateCopedentOptions();
    window.STEEL_RAG_COPEDENTS?.renderStatus?.(document.querySelector("[data-active-copedent]"));
    updateKeyOptions();
    if (els.copedent) {
      els.copedent.addEventListener("change", async () => {
        try {
          const activation = window.STEEL_RAG_COPEDENTS?.activateProfile?.(els.copedent.value);
          if (activation?.then) await activation;
          window.STEEL_RAG_COPEDENTS?.renderStatus?.(document.querySelector("[data-active-copedent]"));
          refreshAfterPayloadChange();
        } catch (error) {
          els.empty.hidden = false;
          els.empty.textContent = error?.message || "Review this copedent in Backstage before using it.";
          updateCopedentOptions();
        }
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
    Array.from(els.notationModeButtons || []).forEach((button) => {
      button.addEventListener("click", () => {
        const nextMode = button.getAttribute("data-explorer-notation-mode");
        notationMode = NOTATION_MODES.some((mode) => mode.id === nextMode) ? nextMode : "notes";
        selectedTopFilter = "all";
        updateNotationModeButtons();
        render();
      });
    });
    Array.from(els.pitchRegisterButtons || []).forEach((button) => {
      button.addEventListener("click", () => {
        const nextMode = button.getAttribute("data-explorer-pitch-register");
        pitchRegisterMode = PITCH_REGISTER_MODES.some((mode) => mode.id === nextMode) ? nextMode : "off";
        updatePitchRegisterButtons();
        render();
      });
    });
    if (els.stringActionLabelToggle) {
      updateStringActionLabelToggle();
      els.stringActionLabelToggle.addEventListener("click", () => {
        showStringActionLabels = !showStringActionLabels;
        updateStringActionLabelToggle();
        render();
      });
    }
    els.key.addEventListener("change", refreshAfterPayloadChange);
    els.scale.addEventListener("change", () => {
      updateControls();
      render();
    });
    els.harmony.addEventListener("change", () => {
      updateStringGroupOptions();
      render();
    });
    if (els.gripVocabulary) {
      els.gripVocabulary.addEventListener("change", () => {
        if (isChordFinderMode()) {
          selectedGripVocabulary = els.gripVocabulary.value || "core";
          selectedChordCandidateId = "";
        } else {
          selectedSingleGripVocabulary = els.gripVocabulary.value || "core";
        }
        updateStringGroupOptions();
        selectedTopFilter = "all";
        render();
      });
    }
    if (els.exploreMode) {
      els.exploreMode.addEventListener("change", () => {
        selectedTopFilter = "all";
        selectedTaskCard = defaultTaskCardForMode(els.exploreMode.value);
        updateExploreModeTabs();
        updateTaskCards();
        updateControls();
        render();
      });
    }
    Array.from(els.taskCards || []).forEach((button) => {
      button.addEventListener("click", () => {
        applyTaskCard(button.getAttribute("data-explorer-task-card"));
      });
    });
    Array.from(els.modeTabs || []).forEach((button) => {
      button.addEventListener("click", () => {
        const nextMode = button.getAttribute("data-explorer-mode-tab") || EXPLORE_MODES.single;
        const validMode = isValidExploreMode(nextMode) ? nextMode : EXPLORE_MODES.single;
        if (els.exploreMode) {
          els.exploreMode.value = validMode;
        }
        selectedTaskCard = defaultTaskCardForMode(validMode);
        selectedTopFilter = "all";
        updateExploreModeTabs();
        updateTaskCards();
        updateControls();
        render();
      });
    });
    if (els.pathFamily) {
      els.pathFamily.addEventListener("change", () => {
        selectedTopFilter = "all";
        render();
      });
    }
    els.stringGroup.addEventListener("change", () => {
      render();
    });

    const recordExplorerActivity = (event) => {
      const target = event.target.closest?.(
        "[data-path-step], [data-note-grip-card], [data-explorer-row], [data-control-impact-control], .explorer-control-impact-tab"
      );
      if (!target || !window.STEEL_RAG_ACCOUNT_ACTIVITY) return;
      if (target.hasAttribute("data-control-impact-clear")) return;
      let eventType = "explorer.position_selected";
      if (target.matches("[data-path-step]")) eventType = "explorer.scale_path_selected";
      else if (target.matches("[data-note-grip-card]")) eventType = "explorer.chord_grip_selected";
      else if (target.matches("[data-control-impact-control], .explorer-control-impact-tab")) eventType = "explorer.movement_compared";
      const key = [
        target.getAttribute("data-path-step"),
        target.getAttribute("data-note-grip-card"),
        target.getAttribute("data-explorer-row"),
        target.getAttribute("data-control-impact-control"),
        target.textContent
      ].find(Boolean);
      window.STEEL_RAG_ACCOUNT_ACTIVITY.track(eventType, { dedupeKey: key || eventType });
    };
    [els.activeResults, els.rowList, els.controlPreview, els.noteFinder]
      .filter(Boolean)
      .forEach((container) => container.addEventListener("click", recordExplorerActivity));

    updateControls();
    updateExploreModeTabs();
    updateTaskCards();
    updateNotationModeButtons();
    updatePitchRegisterButtons();
    render();
  }

  init();
  window.STEEL_RAG_E9_EXPLORER = {
    availableHarmonies,
    rowsForScaleAndHarmony,
    uniqueGroups,
    pathRows,
    parseChordFinderQuery,
    chordFinderCandidates,
  };
})();
