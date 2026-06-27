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
  const EXPLORE_MODES = {
    single: "single",
    path: "path",
    note: "note",
  };
  const PATH_FAMILIES = [
    {
      id: "high",
      label: "High path",
      description: "Uses 3-4-5 and 4-5-6 where the harmony needs it.",
      groups: ["3-4-5", "4-5-6"],
      pattern: ["3-4-5", "4-5-6", "4-5-6", "3-4-5", "3-4-5", "4-5-6", "3-4-5", "3-4-5"],
    },
    {
      id: "middle",
      label: "Middle path",
      description: "Uses 5-6-8 for straight-bar shapes and 5-6-7 for A+B minor shapes.",
      groups: ["5-6-8", "5-6-7"],
      pattern: ["5-6-8", "5-6-7", "5-6-7", "5-6-8", "5-6-8", "5-6-7", "5-6-8", "5-6-8"],
    },
    {
      id: "low",
      label: "Low path",
      description: "Uses 6-8-10 for straight-bar shapes and 6-7-10 for A+B minor shapes.",
      groups: ["6-8-10", "6-7-10"],
      pattern: ["6-8-10", "6-7-10", "6-7-10", "6-8-10", "6-8-10", "6-7-10", "6-8-10", "6-8-10"],
    },
  ];
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
  const FRET_RANGE_OPTIONS = [
    { id: "core", label: "Core", description: "Frets 1-15", min: 1, max: 15 },
    { id: "low", label: "Low", description: "Frets 0-8", min: 0, max: 8 },
    { id: "high", label: "High", description: "Frets 10-24", min: 10, max: 24 },
    { id: "all", label: "All", description: "Frets 0-24", min: 0, max: 24 },
  ];
  const NOTATION_MODES = [
    { id: "notes", label: "Notes", description: "C - D - E" },
    { id: "nns", label: "NNS", description: "1 - 2-" },
    { id: "roman", label: "Roman", description: "I - ii" },
    { id: "numbers", label: "Numbers", description: "1 - 2m" },
  ];
  const NOTE_CONTROL_STATES = [
    { id: "open", label: "Open", controls: [] },
    { id: "A", label: "A", controls: ["A"] },
    { id: "B", label: "B", controls: ["B"] },
    { id: "AB", label: "A+B", controls: ["A", "B"] },
    { id: "BC", label: "B+C", controls: ["B", "C"] },
    { id: "E-raise", label: "E-raise", controls: ["E-raise"] },
    { id: "E-lower", label: "E-lower", controls: ["E-lower"] },
  ];
  const NOTE_WORKFLOWS = [
    { id: "find", label: "Find all", description: "Highlight every matching note or scale value in the visible fret range." },
    { id: "reverse", label: "Reverse lookup", description: "List ways to get the target note or notation value on selected strings." },
    { id: "changes", label: "Pedal changes", description: "Compare open/no-control notes against the active pedal or lever state." },
    { id: "grip", label: "Build grip", description: "Find practical validated grips that contain the selected note set." },
    { id: "drill", label: "Drill", description: "Click a matching cell and get deterministic practice feedback." },
    { id: "sync", label: "Event sync", description: "Step through safe deterministic events and focus the matching cell." },
  ];
  const CHROMATIC_SHARP_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const MAJOR_SCALE_SEQUENCES = {
    nns: ["1", "2-", "3-", "4", "5", "6-", "7°"],
    roman: ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
    numbers: ["1", "2m", "3m", "4", "5", "6m", "7dim"],
  };
  const NATURAL_MINOR_SCALE_SEQUENCES = {
    nns: ["1-", "2°", "3", "4-", "5-", "6", "7"],
    roman: ["i", "ii°", "III", "iv", "v", "VI", "VII"],
    numbers: ["1m", "2dim", "3", "4m", "5m", "6", "7"],
  };

  const els = {
    key: document.getElementById("explorer-key"),
    copedent: document.getElementById("explorer-copedent"),
    exploreMode: document.getElementById("explorer-explore-mode"),
    scale: document.getElementById("explorer-scale"),
    harmony: document.getElementById("explorer-harmony"),
    harmonyControl: document.getElementById("explorer-harmony-control"),
    stringGroup: document.getElementById("explorer-string-group"),
    stringGroupControl: document.getElementById("explorer-string-group-control"),
    pathFamily: document.getElementById("explorer-path-family"),
    pathFamilyControl: document.getElementById("explorer-path-family-control"),
    scaleNotes: document.getElementById("explorer-scale-notes"),
    resultCount: document.getElementById("explorer-result-count"),
    notationModeButtons: document.querySelectorAll("[data-explorer-notation-mode]"),
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
    activeResults: document.getElementById("explorer-active-results"),
    fretboard: document.getElementById("explorer-fretboard"),
    rowList: document.getElementById("explorer-row-list"),
    selectedDetail: document.getElementById("explorer-selected-detail"),
    empty: document.getElementById("explorer-empty"),
    tooltip: document.getElementById("explorer-tooltip"),
  };

  let selectedRowId = "";
  let selectedImpactControlIds = new Set();
  let selectedTopFilter = "all";
  let selectedFretRange = "core";
  let selectedNoteControlStateId = "open";
  let selectedNoteTargetIndex = 0;
  let selectedNoteWorkflow = "find";
  let selectedNoteStringFilter = "all";
  let selectedGripTargetId = "scale-triad";
  let selectedGripCandidateId = "";
  let selectedSyncEventId = "s3-f3-open";
  let drillFeedback = null;
  let pinnedNoteCell = { stringNumber: 3, fret: 3 };
  let previewNoteCell = null;
  let notationMode = "notes";
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

  function formatInterval(value) {
    return formatValue(value, "")
      .replace(/bb(?=\d)/g, "𝄫")
      .replace(/b(?=\d)/g, "♭")
      .replace(/#(?=\d)/g, "♯");
  }

  function formatTheoryText(value) {
    return formatValue(value, "")
      .replace(/bb(?=\d)/g, "𝄫")
      .replace(/b(?=\d)/g, "♭")
      .replace(/#(?=\d)/g, "♯");
  }

  function normalizeIntervalToken(value) {
    return formatValue(value, "")
      .replace(/♭/g, "b")
      .replace(/♯/g, "#")
      .trim();
  }

  function notationModeLabel() {
    return NOTATION_MODES.find((mode) => mode.id === notationMode)?.label || "Notes";
  }

  function intervalAsNns(value) {
    const token = normalizeIntervalToken(value);
    const map = {
      "1": "1",
      "b2": "2-",
      "2": "2",
      "b3": "3-",
      "3": "3",
      "4": "4",
      "#4": "4+",
      "b5": "5°",
      "b5/#11": "5°",
      "#11": "4+",
      "5": "5",
      "b6": "6-",
      "6": "6",
      "b7": "7-",
      "7": "7",
    };
    return map[token] || formatTheoryText(value);
  }

  function intervalAsRoman(value) {
    const token = normalizeIntervalToken(value);
    const map = {
      "1": "I",
      "b2": "ii",
      "2": "II",
      "b3": "iii",
      "3": "III",
      "4": "IV",
      "#4": "IV+",
      "b5": "v°",
      "b5/#11": "v°",
      "#11": "IV+",
      "5": "V",
      "b6": "vi",
      "6": "VI",
      "b7": "vii",
      "7": "VII",
    };
    return map[token] || formatTheoryText(value);
  }

  function intervalAsNumberQuality(value) {
    const token = normalizeIntervalToken(value);
    const map = {
      "1": "1",
      "b2": "2m",
      "2": "2",
      "b3": "3m",
      "3": "3",
      "4": "4",
      "#4": "4aug",
      "b5": "5dim",
      "b5/#11": "5dim",
      "#11": "4aug",
      "5": "5",
      "b6": "6m",
      "6": "6",
      "b7": "7m",
      "7": "7",
    };
    return map[token] || formatTheoryText(value);
  }

  function formatIntervalForNotation(value) {
    if (notationMode === "nns") {
      return intervalAsNns(value);
    }
    if (notationMode === "roman") {
      return intervalAsRoman(value);
    }
    if (notationMode === "numbers") {
      return intervalAsNumberQuality(value);
    }
    return formatTheoryText(value);
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
    return formatValue(note, "")
      .replace(/♭/g, "b")
      .replace(/♯/g, "#")
      .split("/")
      .map((part) => part.trim())
      .filter(Boolean);
  }

  function pitchClassForNote(note) {
    const match = /^([A-G])([b#]{0,2})/.exec(formatValue(note, "").replace(/♭/g, "b").replace(/♯/g, "#"));
    if (!match) {
      return null;
    }
    const base = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }[match[1]];
    const accidental = match[2].split("").reduce((total, symbol) => {
      if (symbol === "#") {
        return total + 1;
      }
      if (symbol === "b") {
        return total - 1;
      }
      return total;
    }, 0);
    return (base + accidental + 120) % 12;
  }

  function displayNoteForPitchClass(pitchClass) {
    const normalized = ((Number(pitchClass) % 12) + 12) % 12;
    const scaleNote = activeScaleNotes().find((note) => noteAlternates(note)
      .map(pitchClassForNote)
      .some((candidate) => candidate === normalized));
    return scaleNote || CHROMATIC_SHARP_NOTES[normalized] || "";
  }

  function noteAtFret(openNote, fret, semitoneDelta = 0) {
    const pitchClass = pitchClassForNote(openNote);
    const fretNumber = Number(fret);
    const delta = Number(semitoneDelta) || 0;
    if (pitchClass === null || !Number.isFinite(fretNumber)) {
      return "";
    }
    return displayNoteForPitchClass(pitchClass + fretNumber + delta);
  }

  function scaleDegreeIndexForNote(note) {
    const scaleNotes = activeScaleNotes();
    const candidates = noteAlternates(note);
    if (!scaleNotes.length || !candidates.length) {
      return -1;
    }
    const exactIndex = scaleNotes.findIndex((scaleNote) => {
      const scaleAlternates = noteAlternates(scaleNote);
      return candidates.some((candidate) => scaleAlternates.includes(candidate));
    });
    if (exactIndex !== -1) {
      return exactIndex;
    }
    const candidatePitchClasses = candidates
      .map(pitchClassForNote)
      .filter((value) => value !== null);
    if (!candidatePitchClasses.length) {
      return -1;
    }
    return scaleNotes.findIndex((scaleNote) => noteAlternates(scaleNote)
      .map(pitchClassForNote)
      .some((pitchClass) => candidatePitchClasses.includes(pitchClass)));
  }

  function notationLabelForFinalNote(note, fallbackInterval = "") {
    const displayNote = formatValue(note, "");
    if (notationMode === "notes") {
      return displayNote;
    }
    const scaleIndex = scaleDegreeIndexForNote(displayNote);
    const sequence = activeScaleSequence();
    if (scaleIndex >= 0 && sequence[scaleIndex]) {
      return sequence[scaleIndex];
    }
    return fallbackInterval ? formatIntervalForNotation(fallbackInterval) : displayNote;
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
    return controlById(controlId)?.label || controlId;
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
    const openNoteAtFret = noteAtFret(openStringNote, fret, 0);
    const finalNote = noteAtFret(openStringNote, fret, delta);
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
      activeControlIds: activeControls,
      activeControlLabel: controlState.label,
      affectedCells,
      isAffected: Boolean(activeControls.length && affectedCells.length),
      isTargetMatch,
      notationValue: notationLabelForFinalNote(finalNote),
      explanation,
    };
  }

  function decorateNoteCellForRender(cell) {
    const selectedGrip = selectedGripCandidate();
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
    return [
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
    ].filter((target) => target.pitchClasses.length);
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
    return target?.pitchClasses?.every((pitchClass) => pitchClasses.includes(pitchClass));
  }

  function gripFinderCandidates() {
    const target = selectedGripTarget();
    if (!target) {
      return [];
    }
    const practicalGroups = new Set([...CORE_GROUPS, ...ADVANCED_GROUPS]);
    return rowsForScale(els.scale.value)
      .filter((row) => practicalGroups.has(row.string_group))
      .filter((row) => rowInRange(row))
      .filter((row) => rowMatchesGripTarget(row, target))
      .sort((a, b) => {
        const aCore = CORE_GROUPS.has(a.string_group) ? 0 : 1;
        const bCore = CORE_GROUPS.has(b.string_group) ? 0 : 1;
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
    if (els.stringGroupControl) {
      els.stringGroupControl.hidden = pathMode || noteMode;
      els.stringGroupControl.setAttribute?.("aria-hidden", pathMode || noteMode ? "true" : "false");
    }
    if (els.stringGroup) {
      els.stringGroup.disabled = pathMode || noteMode;
    }
    if (els.pathFamilyControl) {
      els.pathFamilyControl.hidden = !pathMode;
      els.pathFamilyControl.setAttribute?.("aria-hidden", pathMode ? "false" : "true");
    }
    if (els.pathFamily) {
      els.pathFamily.disabled = !pathMode;
    }
    if (els.harmonyControl) {
      els.harmonyControl.hidden = pathMode || noteMode;
      els.harmonyControl.setAttribute?.("aria-hidden", pathMode || noteMode ? "true" : "false");
    }
    if (els.harmony) {
      els.harmony.disabled = pathMode || noteMode;
      if (pathMode) {
        els.harmony.value = "three_string_diatonic";
      }
    }
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
    const harmony = activeHarmonyValue();
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

  function isAdvanced(row) {
    return ADVANCED_GROUPS.has(row.string_group) || row.harmony_type === "advanced_pocket";
  }

  function groupLabel(row) {
    if (isPathMode()) {
      return "Harmonized scale path";
    }
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

  function impactContextSentence(controls) {
    const selectedGroups = selectedStringGroups();
    const groupText = !isPathMode() && selectedGroups.length ? selectedGroups.join(", ") : selectedGroupLabel();
    const harmonyText = isPathMode() ? "harmonized scale path" : (HARMONY_LABELS[activeHarmonyValue()] || selectedOptionLabel(els.harmony));
    const modeText = `${notationModeLabel()} notation`;
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
    if (isNoteFinderMode()) {
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

  function renderTopIntervalFilter(baseRows) {
    if (!els.topIntervalFilter) {
      return;
    }
    if (isNoteFinderMode()) {
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
    if (isPathMode()) {
      els.fretRangeFilter.hidden = true;
      els.fretRangeFilter.innerHTML = "";
      return;
    }
    const outsideCount = Math.max(0, rowsBeforeRange.length - rows.length);
    const activeRange = activeRangeOption();
    const matchNoun = isNoteFinderMode() ? "note" : "position";
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
        <strong>${escapeHtml(formatTheoryText(row.display_summary || row.chord_name || row.id))}</strong>
      </div>
      ${topVoiceExplanationHtml(row)}
      ${teachingNoteHtml(row)}
      <dl class="explorer-detail-grid">
        ${detailRow(activeTopLabelName(), activeTopLabel(row))}
        ${detailRow("Supporting harmony", harmonyIntervalText(row))}
        ${detailRow("Notes", rowNoteLabels(row))}
        ${detailRow("Chord intervals", rowIntervalLabels(row))}
        ${detailRow("Notation mode", notationModeLabel())}
        ${detailRow("Top voice", topVoiceLabel(row))}
        ${detailRow("Fret", row.fret)}
        ${detailRow("String group", row.string_group)}
        ${detailRow("Pedals / levers", normalizePedals(row))}
        ${detailRow("Per-string changes", row.per_string_changes)}
        ${detailRow("Warnings", warnings)}
      </dl>
      ${stringActionRowsHtml(row)}
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
        </span>
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
        <strong>${escapeHtml(label)}: ${rows.length} visible ${isPathMode() ? "scale degrees" : rows.length === 1 ? "position" : "positions"}</strong>
        <span>${isPathMode() ? "This path changes string groups when the harmony requires it." : "Cards match the SVG markers below."}</span>
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

  function renderFretboard(rows) {
    if (!fretboardApi || typeof fretboardApi.mountPedalSteelFretboard !== "function") {
      els.fretboard.innerHTML = '<p class="explorer-empty">Fretboard renderer unavailable.</p>';
      return;
    }
    const markerGroups = groupRowsForMarkers(rows);
    const selectedMarkerId = markerGroupKey(rows.find((row) => row.id === selectedRowId) || {});
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
      showHighlightLabels: true,
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
        aria-label="${escapeHtml(`String ${cell.stringNumber}, fret ${cell.fret}: ${cell.finalNote} with ${cell.activeControlLabel}`)}"
      ><span>${cell.isTargetMatch ? escapeHtml(cell.finalNote) : ""}</span></button>
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
    return `Finding ${target?.label || "scale tones"} with ${activeControls.label}. ${resultCount} visible matches use the selected notation mode and fret range.`;
  }

  function noteFinderResultButtonHtml(cell, options = {}) {
    const key = options.key || noteCellKey(cell);
    const isSelected = options.isSelected || key === `${pinnedNoteCell.stringNumber}:${pinnedNoteCell.fret}`;
    const dataAttribute = options.attribute || "data-note-result-card";
    return `
      <button class="explorer-active-result explorer-note-result-card${isSelected ? " is-selected" : ""}" type="button" ${dataAttribute}="${escapeHtml(key)}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          <span class="explorer-active-result__marker"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(cell.finalNote)}</span></span>
          <strong>${escapeHtml(`String ${cell.stringNumber} · fret ${cell.fret}`)}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Open note</b>${escapeHtml(cell.openNoteAtFret)}</span>
          <span><b>Final note</b>${escapeHtml(cell.finalNote)}</span>
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
        <strong>${escapeHtml(`String ${cell.stringNumber}, fret ${cell.fret}: ${cell.finalNote}`)}</strong>
        <span class="explorer-row-button__meta">Open note: ${escapeHtml(cell.openNoteAtFret)} · Final note: ${escapeHtml(cell.finalNote)} · Controls: ${escapeHtml(cell.activeControlLabel)} · ${escapeHtml(notationModeLabel())}: ${escapeHtml(cell.notationValue)}</span>
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
          <span>${escapeHtml(`${cell.openNoteAtFret} -> ${cell.finalNote}`)}</span>
          <em>${escapeHtml(cell.isAffected ? controlText : `No change at fret ${cell.fret}`)}</em>
        </div>
      `;
    }).join("");
  }

  function renderFindAllPanel(resultCells) {
    const target = selectedNoteFinderTarget();
    return `
      <section class="explorer-note-workflow-panel" aria-label="Find all matching notes">
        <strong>Find all ${escapeHtml(target?.label || "target")} positions</strong>
        <p>Highlighted cells match the selected ${escapeHtml(notationModeLabel())} target after the active pedal or lever state is applied.</p>
        <p>${escapeHtml(`${resultCells.length} visible ${resultCells.length === 1 ? "match" : "matches"} in ${activeRangeOption().label}.`)}</p>
      </section>
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

  function gripCandidateButtonHtml(row) {
    const isSelected = selectedGripCandidateId === row.id;
    return `
      <button class="explorer-active-result explorer-note-grip-card${isSelected ? " is-selected" : ""}" type="button" data-note-grip-card="${escapeHtml(row.id || "")}" aria-pressed="${isSelected ? "true" : "false"}">
        <span class="explorer-active-result__top">
          <span class="explorer-active-result__marker"><span class="explorer-marker-token" aria-hidden="true"></span><span>${escapeHtml(row.string_group)}</span></span>
          <strong>${escapeHtml(`${row.fret} ${normalizePedals(row).join("+") || "open"}`)}</strong>
        </span>
        <span class="explorer-active-result__fields">
          <span><b>Strings</b>${escapeHtml(formatValue(row.strings))}</span>
          <span><b>Notes</b>${escapeHtml(formatValue(rowNoteLabels(row)))}</span>
          <span><b>${escapeHtml(notationModeLabel())}</b>${escapeHtml(formatValue(rowIntervalLabels(row).map(formatIntervalForNotation)))}</span>
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
        <p>${escapeHtml(target?.description || "Choose a target note set.")}</p>
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
        <p class="explorer-note-finder__context">Current pinned cell: string ${escapeHtml(currentCell.stringNumber)}, fret ${escapeHtml(currentCell.fret)} gives ${escapeHtml(currentCell.finalNote)}.</p>
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
          <span><b>Final note</b>${escapeHtml(event.cell.finalNote)}</span>
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
        <strong>${escapeHtml(`String ${cell.stringNumber}, fret ${cell.fret}: ${cell.finalNote}`)}</strong>
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
        ${detailRow(`${notationModeLabel()} in ${scaleText}`, cell.notationValue)}
      </dl>
    `;
  }

  function renderNoteFinder() {
    if (!els.noteFinder) {
      return;
    }
    syncNoteFinderSelections();
    ensurePinnedNoteCellInRange();
    const cells = visibleNoteCells().map(decorateNoteCellForRender);
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
          <span class="explorer-note-finder__label">Find by ${escapeHtml(notationModeLabel())}</span>
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
      const selectedCell = decorateNoteCellForRender(noteCellState(stringNumber, fret));
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
    els.scaleNotes.textContent = getScaleNotes();
    if (els.resultCount) {
      els.resultCount.textContent = "";
    }
    els.empty.hidden = true;
    els.empty.textContent = "";
    renderCopedentChart();
    renderControlImpactPreview();
    renderNoteFinder();
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

  function render() {
    if (isNoteFinderMode()) {
      renderNoteFinderMode();
      return;
    }
    if (els.noteFinder) {
      els.noteFinder.hidden = true;
      els.noteFinder.innerHTML = "";
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
    els.scaleNotes.textContent = getScaleNotes();
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
    Array.from(els.notationModeButtons || []).forEach((button) => {
      button.addEventListener("click", () => {
        const nextMode = button.getAttribute("data-explorer-notation-mode");
        notationMode = NOTATION_MODES.some((mode) => mode.id === nextMode) ? nextMode : "notes";
        selectedTopFilter = "all";
        updateNotationModeButtons();
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
    if (els.exploreMode) {
      els.exploreMode.addEventListener("change", () => {
        selectedTopFilter = "all";
        updateControls();
        render();
      });
    }
    if (els.pathFamily) {
      els.pathFamily.addEventListener("change", () => {
        selectedTopFilter = "all";
        render();
      });
    }
    els.stringGroup.addEventListener("change", () => {
      render();
    });

    updateControls();
    updateNotationModeButtons();
    render();
  }

  init();
  window.STEEL_RAG_E9_EXPLORER = {
    availableHarmonies,
    rowsForScaleAndHarmony,
    uniqueGroups,
    pathRows,
  };
})();
