(function (root) {
  "use strict";

  const CORE_GROUPS = new Set(["3-4-5", "4-5-6", "5-6-8", "6-8-10", "5-6-7", "6-7-10"]);
  const ADVANCED_GROUPS = new Set(["5-7-8"]);
  const TWO_STRING_GROUPS = new Set(["3-5", "3-6", "4-6", "4-8", "5-8", "5-9", "6-9", "6-10", "8-10", "5-6", "3-4"]);
  const FIVE_EIGHT_GROUPS = new Set(["5-8"]);
  const EXTENDED_VOICING_GRIPS = new Set(["4-6-10", "3-5-8", "5-6-9", "4-6-9", "3-5-6", "4-5-8", "5-8-10"]);
  const DOMINANT_9TH_GRIPS = new Set(["5-6-9", "4-6-9", "6-9", "5-9", "4-5-6-9"]);
  const TWO_STRING_DISPLAY_GROUPS = new Set([...TWO_STRING_GROUPS, ...FIVE_EIGHT_GROUPS]);
  const DEFAULT_E9_OPEN_STRINGS = {
    1: "F#",
    2: "D#",
    3: "G#",
    4: "E",
    5: "B",
    6: "G#",
    7: "F#",
    8: "E",
    9: "D",
    10: "B",
  };
  const DEFAULT_E9_OPEN_STRING_PITCH_VALUES = {
    1: 66,
    2: 63,
    3: 68,
    4: 64,
    5: 59,
    6: 56,
    7: 54,
    8: 52,
    9: 50,
    10: 47,
  };
  const DEFAULT_E9_CONTROL_CHANGES = {
    A: { 5: "C#", 10: "C#" },
    B: { 3: "A", 6: "A" },
    C: { 4: "F#", 5: "C#" },
    "E-raise": { 4: "F", 8: "F" },
    "E-lower": { 4: "Eb/D#", 8: "Eb/D#" },
    "D-lower": { 2: "D", 9: "C#" },
    "G-lower": { 1: "G", 6: "F#" },
  };
  const GRIP_REGISTRY = [
    { strings: "3-4-5", tier: "core", label: "Core grip", roles: ["melody_harmony", "chord_voicing"], note: "common high triad" },
    { strings: "4-5-6", tier: "core", label: "Core grip", roles: ["melody_harmony", "chord_voicing"], note: "common middle triad" },
    { strings: "5-6-8", tier: "core", label: "Core grip", roles: ["chord_voicing", "bass_root_support"], note: "common straight-bar support grip" },
    { strings: "6-8-10", tier: "core", label: "Core grip", roles: ["chord_voicing", "bass_root_support"], note: "common lower support grip" },
    { strings: "5-6-7", tier: "core", label: "Core grip", roles: ["melody_harmony", "chord_voicing"], note: "common A+B minor route" },
    { strings: "6-7-10", tier: "core", label: "Core grip", roles: ["chord_voicing", "bass_root_support"], note: "common lower A+B route" },
    { strings: "4-6-10", tier: "extended", label: "Extended grip", roles: ["chord_voicing", "bass_root_support"], note: "wide grip / tab vocabulary" },
    { strings: "3-5-8", tier: "extended", label: "Extended grip", roles: ["chord_voicing", "passing_color"], note: "wide grip / tab vocabulary" },
    { strings: "5-6-9", tier: "extended", label: "Extended grip", roles: ["dominant_color", "chord_voicing"], note: "9th-string color" },
    { strings: "4-6-9", tier: "extended", label: "Extended grip", roles: ["dominant_color", "chord_voicing"], note: "9th-string color" },
    { strings: "3-5-6", tier: "extended", label: "Extended grip", roles: ["melody_harmony", "passing_color"], note: "tab vocabulary" },
    { strings: "4-5-8", tier: "extended", label: "Extended grip", roles: ["chord_voicing", "passing_color"], note: "tab vocabulary" },
    { strings: "5-8-10", tier: "extended", label: "Extended grip", roles: ["chord_voicing", "bass_root_support", "pad_sustain"], note: "wide support grip; possible pad / sustain" },
    { strings: "3-5", tier: "two_string", label: "Two-string grip", roles: ["melody_harmony"], note: "dyad / melody harmony" },
    { strings: "3-6", tier: "two_string", label: "Two-string grip", roles: ["melody_harmony", "passing_color"], note: "dyad / passing color" },
    { strings: "4-6", tier: "two_string", label: "Two-string grip", roles: ["melody_harmony", "passing_color"], note: "dyad / melody harmony" },
    { strings: "4-8", tier: "two_string", label: "Two-string grip", roles: ["chord_voicing", "pad_sustain"], note: "dyad / possible pad / sustain" },
    { strings: "5-8", tier: "two_string", label: "Two-string grip", roles: ["melody_harmony", "pad_sustain"], note: "5&8 branch; possible pad / sustain" },
    { strings: "5-9", tier: "two_string", label: "Two-string grip", roles: ["dominant_color", "passing_color", "pad_sustain"], note: "9th-string color; possible pad / sustain" },
    { strings: "6-9", tier: "two_string", label: "Two-string grip", roles: ["dominant_color", "bass_root_support", "pad_sustain"], note: "9th-string color; possible pad / sustain" },
    { strings: "6-10", tier: "two_string", label: "Two-string grip", roles: ["bass_root_support", "pad_sustain"], note: "low dyad / possible pad / sustain" },
    { strings: "8-10", tier: "two_string", label: "Two-string grip", roles: ["bass_root_support", "pad_sustain"], note: "low dyad / possible pad / sustain" },
    { strings: "5-7-8", tier: "advanced", label: "Advanced grip", roles: ["passing_color", "chord_voicing"], note: "advanced E-lower pocket" },
    { strings: "4-5-6-9", tier: "advanced", label: "Advanced grip", roles: ["dominant_color", "chord_voicing"], note: "four-string 9th-string dominant color" },
  ];
  const NOTE_CONTROL_STATES = [
    { id: "open", label: "Open", controls: [] },
    { id: "A", label: "A", controls: ["A"] },
    { id: "B", label: "B", controls: ["B"] },
    { id: "AB", label: "A+B", controls: ["A", "B"] },
    { id: "BC", label: "B+C", controls: ["B", "C"] },
    { id: "E-raise", label: "E-raise", controls: ["E-raise"] },
    { id: "E-lower", label: "E-lower", controls: ["E-lower"] },
    { id: "D-lower", label: "D-lower", controls: ["D-lower"] },
    { id: "G-lower", label: "G-lower", controls: ["G-lower"] },
  ];
  const CHORD_QUALITY_PATTERNS = [
    { id: "major", label: "major", suffix: "", intervals: [0, 4, 7], required: [0, 4, 7] },
    { id: "minor", label: "minor", suffix: "m", intervals: [0, 3, 7], required: [0, 3, 7] },
    { id: "dominant7", label: "dominant 7", suffix: "7", intervals: [0, 4, 7, 10], required: [0, 4, 10] },
    { id: "major7", label: "major 7", suffix: "maj7", intervals: [0, 4, 7, 11], required: [0, 4, 11] },
    { id: "minor7", label: "minor 7", suffix: "m7", intervals: [0, 3, 7, 10], required: [0, 3, 10] },
    { id: "dominant9", label: "dominant 9", suffix: "9", intervals: [0, 2, 4, 7, 10], required: [2, 4, 10] },
    { id: "major9", label: "major 9", suffix: "maj9", intervals: [0, 2, 4, 7, 11], required: [2, 4, 11] },
    { id: "minor9", label: "minor 9", suffix: "m9", intervals: [0, 2, 3, 7, 10], required: [2, 3, 10] },
    { id: "minor7flat5", label: "minor 7 flat 5", suffix: "m7b5", intervals: [0, 3, 6, 10], required: [0, 3, 6, 10] },
    { id: "diminished", label: "diminished", suffix: "dim", intervals: [0, 3, 6], required: [0, 3, 6] },
    { id: "major6", label: "major 6", suffix: "6", intervals: [0, 4, 7, 9], required: [0, 4, 9] },
    { id: "minor6", label: "minor 6", suffix: "m6", intervals: [0, 3, 7, 9], required: [0, 3, 9] },
    { id: "sus2", label: "sus2", suffix: "sus2", intervals: [0, 2, 7], required: [0, 2, 7] },
    { id: "sus4", label: "sus4", suffix: "sus4", intervals: [0, 5, 7], required: [0, 5, 7] },
    { id: "fifth", label: "5/no third", suffix: "5", intervals: [0, 7], required: [0, 7] },
  ];
  const CHROMATIC_SHARP_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const CHROMATIC_FLAT_NOTES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
  const MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11];
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

  function normalizeIntervalToken(value) {
    return formatValue(value, "")
      .replace(/♭/g, "b")
      .replace(/♯/g, "#")
      .trim();
  }

  function formatTheoryText(value) {
    return formatValue(value, "")
      .replace(/bb(?=\d)/g, "𝄫")
      .replace(/b(?=\d)/g, "♭")
      .replace(/#(?=\d)/g, "♯");
  }

  function formatInterval(value) {
    return formatTheoryText(value);
  }

  function intervalAsNns(value) {
    const token = normalizeIntervalToken(value);
    const map = {
      "1": "1",
      b2: "2-",
      "2": "2",
      b3: "3-",
      "3": "3",
      "4": "4",
      "#4": "4+",
      b5: "5°",
      "b5/#11": "5°",
      "#11": "4+",
      "5": "5",
      b6: "6-",
      "6": "6",
      b7: "7-",
      "7": "7",
    };
    return map[token] || formatTheoryText(value);
  }

  function intervalAsRoman(value) {
    const token = normalizeIntervalToken(value);
    const map = {
      "1": "I",
      b2: "ii",
      "2": "II",
      b3: "iii",
      "3": "III",
      "4": "IV",
      "#4": "IV+",
      b5: "v°",
      "b5/#11": "v°",
      "#11": "IV+",
      "5": "V",
      b6: "vi",
      "6": "VI",
      b7: "vii",
      "7": "VII",
    };
    return map[token] || formatTheoryText(value);
  }

  function intervalAsNumberQuality(value) {
    const token = normalizeIntervalToken(value);
    const map = {
      "1": "1",
      b2: "2m",
      "2": "2",
      b3: "3m",
      "3": "3",
      "4": "4",
      "#4": "4aug",
      b5: "5dim",
      "b5/#11": "5dim",
      "#11": "4aug",
      "5": "5",
      b6: "6m",
      "6": "6",
      b7: "7m",
      "7": "7",
    };
    return map[token] || formatTheoryText(value);
  }

  function formatIntervalForNotation(value, notationMode = "notes") {
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

  function normalizePitchClass(pitchClass) {
    return ((Number(pitchClass) % 12) + 12) % 12;
  }

  function displayNoteForPitchClass(pitchClass, options = {}) {
    const normalized = normalizePitchClass(pitchClass);
    const scaleNote = toArray(options.scaleNotes).find((note) => noteAlternates(note)
      .map(pitchClassForNote)
      .some((candidate) => candidate === normalized));
    return scaleNote || CHROMATIC_SHARP_NOTES[normalized] || "";
  }

  function scientificPitchForValue(pitchValue) {
    const value = Number(pitchValue);
    if (!Number.isFinite(value)) {
      return "";
    }
    return `${CHROMATIC_SHARP_NOTES[normalizePitchClass(value)]}${Math.floor(value / 12) - 1}`;
  }

  function octaveBandForPitchValue(pitchValue) {
    const value = Number(pitchValue);
    if (!Number.isFinite(value)) {
      return "";
    }
    if (value <= 54) {
      return "lower";
    }
    if (value <= 64) {
      return "middle";
    }
    return "upper";
  }

  function pitchRegisterDetail({ stringNumber, fret, controls = [], pitchValue, note = "", displayNote = "", voiceRole = "" }) {
    const value = Number(pitchValue);
    return {
      string: Number(stringNumber),
      fret: Number(fret),
      active_controls: toArray(controls).map(String),
      pitch_class: note || displayNote,
      display_note: displayNote || note,
      scientific_pitch: scientificPitchForValue(value),
      pitch_value: value,
      octave: Number.isFinite(value) ? Math.floor(value / 12) - 1 : null,
      octave_band: octaveBandForPitchValue(value),
      voice_role: voiceRole,
    };
  }

  function prefersFlatSpelling(key = "") {
    return /b/.test(formatValue(key, "")) || ["F", "Bb", "Eb", "Ab", "Db", "Gb"].includes(formatValue(key, ""));
  }

  function displayNoteForPitchClassInKey(pitchClass, key = "") {
    const normalized = normalizePitchClass(pitchClass);
    const spellings = prefersFlatSpelling(key) ? CHROMATIC_FLAT_NOTES : CHROMATIC_SHARP_NOTES;
    return spellings[normalized] || CHROMATIC_SHARP_NOTES[normalized] || "";
  }

  function noteAtFret(openNote, fret, semitoneDelta = 0, options = {}) {
    const pitchClass = pitchClassForNote(openNote);
    const fretNumber = Number(fret);
    const delta = Number(semitoneDelta) || 0;
    if (pitchClass === null || !Number.isFinite(fretNumber)) {
      return "";
    }
    return displayNoteForPitchClass(pitchClass + fretNumber + delta, options);
  }

  function controlChangesForCopedent(copedent) {
    const controls = Array.isArray(copedent?.controls) ? copedent.controls : [];
    if (!controls.length) {
      return DEFAULT_E9_CONTROL_CHANGES;
    }
    return Object.fromEntries(controls.map((control) => [
      control.id,
      Object.fromEntries(toArray(control.changes).map((change) => [Number(change.string), change.to])),
    ]));
  }

  function openStringsForCopedent(copedent) {
    const strings = Array.isArray(copedent?.strings) ? copedent.strings : [];
    if (!strings.length) {
      return DEFAULT_E9_OPEN_STRINGS;
    }
    return Object.fromEntries(strings.map((entry) => [Number(entry.string), entry.open_note]));
  }

  function openPitchValuesForCopedent(copedent) {
    const strings = Array.isArray(copedent?.strings) ? copedent.strings : [];
    if (!strings.length) {
      return DEFAULT_E9_OPEN_STRING_PITCH_VALUES;
    }
    return Object.fromEntries(strings.map((entry) => [
      Number(entry.string),
      Number.isFinite(Number(entry.open_pitch_value))
        ? Number(entry.open_pitch_value)
        : DEFAULT_E9_OPEN_STRING_PITCH_VALUES[Number(entry.string)],
    ]));
  }

  function resolveE9Note({ stringNumber, fret, controls = [], copedent = null, scaleNotes = [] }) {
    const stringKey = Number(stringNumber);
    const openStrings = openStringsForCopedent(copedent);
    const openPitchValues = openPitchValuesForCopedent(copedent);
    const changes = controlChangesForCopedent(copedent);
    const openStringNote = openStrings[stringKey];
    const activeControls = toArray(controls).map(String);
    let changedOpenNote = openStringNote;
    const affectedControls = [];
    activeControls.forEach((controlId) => {
      const nextNote = changes[controlId]?.[stringKey];
      if (nextNote) {
        changedOpenNote = nextNote;
        affectedControls.push(controlId);
      }
    });
    const openPitchValue = Number(openPitchValues[stringKey]);
    const openPitchClass = pitchClassForNote(openStringNote);
    const changedPitchClass = pitchClassForNote(changedOpenNote);
    let pitchDelta = 0;
    if (openPitchClass !== null && changedPitchClass !== null) {
      pitchDelta = normalizePitchClass(changedPitchClass - openPitchClass);
      if (pitchDelta > 6) {
        pitchDelta -= 12;
      }
    }
    const fretNumber = Number(fret);
    const openPitchValueAtFret = openPitchValue + fretNumber;
    const finalPitchValue = openPitchValueAtFret + pitchDelta;
    const openNoteAtFret = noteAtFret(openStringNote, fret, 0, { scaleNotes });
    const finalNote = noteAtFret(changedOpenNote, fret, 0, { scaleNotes });
    return {
      stringNumber: stringKey,
      fret: fretNumber,
      openStringNote,
      changedOpenNote,
      openNoteAtFret,
      finalNote,
      openPitchValueAtFret,
      finalPitchValue,
      openScientificPitch: scientificPitchForValue(openPitchValueAtFret),
      finalScientificPitch: scientificPitchForValue(finalPitchValue),
      openOctaveBand: octaveBandForPitchValue(openPitchValueAtFret),
      finalOctaveBand: octaveBandForPitchValue(finalPitchValue),
      finalRegister: pitchRegisterDetail({
        stringNumber: stringKey,
        fret: fretNumber,
        controls: activeControls,
        pitchValue: finalPitchValue,
        note: finalNote,
      }),
      affectedControls,
    };
  }

  function scaleDegreeIndexForNote(note, scaleNotes = []) {
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

  function notationLabelForFinalNote(note, fallbackInterval = "", context = {}) {
    const displayNote = formatValue(note, "");
    if (context.notationMode === "notes" || !context.notationMode) {
      return displayNote;
    }
    const scaleIndex = scaleDegreeIndexForNote(displayNote, toArray(context.scaleNotes));
    const sequence = toArray(context.scaleSequence);
    if (scaleIndex >= 0 && sequence[scaleIndex]) {
      return sequence[scaleIndex];
    }
    return fallbackInterval ? formatIntervalForNotation(fallbackInterval, context.notationMode) : displayNote;
  }

  function intervalNameFromSemitones(semitones) {
    const normalized = normalizePitchClass(Number(semitones) || 0);
    const map = {
      0: "1",
      1: "b2",
      2: "2",
      3: "b3",
      4: "3",
      5: "4",
      6: "b5/#11",
      7: "5",
      8: "b6",
      9: "6",
      10: "b7",
      11: "7",
    };
    return map[normalized] || "";
  }

  function intervalLabelsAgainstRoot(notes, rootPitchClass) {
    return toArray(notes).map((note) => {
      const pitchClass = pitchClassForNote(note);
      if (pitchClass === null) {
        return "";
      }
      return intervalNameFromSemitones(pitchClass - rootPitchClass);
    }).filter(Boolean);
  }

  function intervalRoleLabel(interval) {
    const map = {
      0: "root",
      2: "9th",
      3: "minor 3rd",
      4: "3rd",
      5: "4th",
      6: "flat 5",
      7: "5th",
      9: "6th",
      10: "flat 7",
      11: "major 7th",
    };
    return map[interval] || formatInterval(intervalNameFromSemitones(interval));
  }

  function omittedIntervalLabel(interval) {
    return formatInterval(intervalNameFromSemitones(interval));
  }

  function chordQualityById(id) {
    return CHORD_QUALITY_PATTERNS.find((quality) => quality.id === id) || CHORD_QUALITY_PATTERNS[0];
  }

  function chordLabel(rootPitchClass, quality, context = {}) {
    const root = displayNoteForActiveKey(rootPitchClass, context);
    if (!quality || !quality.suffix) {
      return root;
    }
    return `${root}${quality.suffix}`;
  }

  function partialChordLabel(rootPitchClass, quality, missingIntervals, context = {}) {
    const base = chordLabel(rootPitchClass, quality, context);
    if (!missingIntervals.length) {
      return base;
    }
    return `${base}(${missingIntervals.map((interval) => `no${omittedIntervalLabel(interval)}`).join(", ")})`;
  }

  function isExtendedChordQuality(quality) {
    return ["dominant7", "major7", "minor7", "dominant9", "major9", "minor9", "minor7flat5", "major6", "minor6"].includes(quality?.id);
  }

  function extendedQualityGate(quality, intervals) {
    if (!isExtendedChordQuality(quality)) {
      return quality.required.every((interval) => intervals.includes(interval));
    }
    const extensionIntervals = {
      dominant7: [10],
      major7: [11],
      minor7: [10],
      dominant9: [10, 2],
      major9: [11, 2],
      minor9: [10, 2],
      minor7flat5: [10],
      major6: [9],
      minor6: [9],
    }[quality.id] || [];
    const hasExtension = extensionIntervals.some((interval) => intervals.includes(interval));
    const hasRootOrThird = intervals.includes(0) || intervals.includes(3) || intervals.includes(4);
    const hasEnoughNotes = intervals.length >= 3;
    return hasExtension && hasRootOrThird && hasEnoughNotes;
  }

  function chordConfidence(quality, exact, missingIntervals, intervals) {
    if (exact && !missingIntervals.length) {
      return "high";
    }
    if (!isExtendedChordQuality(quality)) {
      return "low";
    }
    const hasRoot = intervals.includes(0);
    const hasThird = intervals.includes(3) || intervals.includes(4);
    if (!hasRoot) {
      return "medium, context-dependent";
    }
    if (!hasThird) {
      return "medium";
    }
    return "medium-high";
  }

  function qualityPriority(quality) {
    const priorities = {
      major: 20,
      minor: 20,
      diminished: 18,
      dominant7: 14,
      major7: 14,
      minor7: 14,
      dominant9: 15,
      major9: 15,
      minor9: 15,
      minor7flat5: 13,
      major6: 10,
      minor6: 10,
      sus2: 8,
      sus4: 8,
      fifth: 2,
    };
    return priorities[quality?.id] || 0;
  }

  function voicingExplanation(label, quality, intervals, missingIntervals) {
    if (!missingIntervals.length) {
      return quality.id === "dominant7"
        ? `${label} spells a dominant-7 voicing: ${intervals.map(intervalRoleLabel).join(", ")}.`
        : `${label} matches the selected notes directly: ${intervals.map(intervalRoleLabel).join(", ")}.`;
    }
    const presentRoles = intervals.map(intervalRoleLabel).join(", ");
    const missingRoles = missingIntervals.map(intervalRoleLabel).join(", ");
    const partialKind = quality.id === "major7"
      ? "partial major-7"
      : quality.id === "dominant7"
        ? "partial dominant-7"
        : `partial ${quality.label}`;
    return `Likely voicing: ${label}. This is a ${partialKind} grip: it includes ${presentRoles}, but omits ${missingRoles}. On pedal steel, three-note grips often imply extended chords with one or more tones omitted.`;
  }

  function displayNoteForActiveKey(pitchClass, context = {}) {
    const scaleNote = toArray(context.scaleNotes).find((note) => pitchClassForNote(note) === normalizePitchClass(pitchClass));
    return scaleNote || displayNoteForPitchClass(pitchClass, { scaleNotes: context.scaleNotes });
  }

  function dominantRootPitchClass(key) {
    const keyPitchClass = pitchClassForNote(key);
    return keyPitchClass === null ? null : (keyPitchClass + 7) % 12;
  }

  function dominantTargetForKey(key, context = {}) {
    const rootPitchClass = dominantRootPitchClass(key);
    if (rootPitchClass === null) {
      return null;
    }
    const pitchClasses = [0, 4, 7, 10].map((interval) => (rootPitchClass + interval) % 12);
    const notes = pitchClasses.map((pitchClass) => displayNoteForPitchClass(pitchClass, { scaleNotes: context.scaleNotes }));
    const rootNote = displayNoteForPitchClass(rootPitchClass, { scaleNotes: context.scaleNotes });
    const label = context.notationMode === "roman" ? "V7" : context.notationMode === "notes" ? `${rootNote}7` : "5^7 / V7";
    return {
      rootPitchClass,
      pitchClasses,
      requiredPitchClasses: [(rootPitchClass + 4) % 12, (rootPitchClass + 10) % 12],
      rootNote,
      notes,
      label,
      description: `Dominant 7 / V7 in ${key}: ${notes.join(" - ")}. The flat 7 creates pull back to I.`,
    };
  }

  function voicingFunctionForRoot(rootPitchClass, quality, context = {}) {
    const rootNote = displayNoteForActiveKey(rootPitchClass, context);
    const degreeIndex = scaleDegreeIndexForNote(rootNote, toArray(context.scaleNotes));
    if (degreeIndex === -1) {
      return "outside the selected scale";
    }
    const sequenceSource = context.scaleType === "natural_minor" ? NATURAL_MINOR_SCALE_SEQUENCES.roman : MAJOR_SCALE_SEQUENCES.roman;
    const degree = sequenceSource[degreeIndex] || `degree ${degreeIndex + 1}`;
    if (quality?.id === "dominant7") {
      return degree === "V" ? `V7 in ${context.key}` : `${degree}7 dominant color in ${context.key}`;
    }
    return `${degree} function in ${context.key}`;
  }

  function dominantColorIdentity(notes, context = {}, fallbackLabel = "") {
    const target = dominantTargetForKey(context.key, context);
    if (!target) {
      return null;
    }
    const pitchClasses = Array.from(new Set(toArray(notes).map(pitchClassForNote).filter((value) => value !== null)));
    if (pitchClasses.length < 2 || !pitchClasses.every((pitchClass) => target.pitchClasses.includes(pitchClass))) {
      return null;
    }
    const hasRoot = pitchClasses.includes(target.rootPitchClass);
    const hasThird = pitchClasses.includes((target.rootPitchClass + 4) % 12);
    const hasFlatSeven = pitchClasses.includes((target.rootPitchClass + 10) % 12);
    const hasFifth = pitchClasses.includes((target.rootPitchClass + 7) % 12);
    if (!hasFlatSeven || (!hasRoot && !hasThird)) {
      return null;
    }
    const missingIntervals = [
      hasRoot ? "" : "1",
      hasThird ? "" : "3",
      hasFifth ? "" : "5",
      hasFlatSeven ? "" : "b7",
    ].filter(Boolean);
    const partial = missingIntervals.length > 0 || pitchClasses.length < 4;
    const label = partial
      ? `${target.rootNote}7 color / partial V7 in ${context.key}`
      : `${target.rootNote}7`;
    const explanation = partial
      ? `This points at ${target.rootNote}7, the V7 chord in ${context.key}. It includes ${hasRoot ? "the root" : "a chord tone"} and flat 7 color but omits ${missingIntervals.map(formatInterval).join(", ")}.`
      : `${target.notes.join("-")} spells ${target.rootNote} dominant 7, the V7 chord in ${context.key}.`;
    return {
      label,
      quality: partial ? "partial dominant 7" : "dominant 7",
      confidence: partial ? "medium" : "high",
      functionText: partial ? `V7 color in ${context.key}` : `V7 in ${context.key}`,
      alternates: fallbackLabel ? [fallbackLabel] : [],
      intervals: intervalLabelsAgainstRoot(notes, target.rootPitchClass),
      rootPitchClass: target.rootPitchClass,
      partial,
      missingIntervals,
      missingIntervalNames: missingIntervals,
      explanation,
    };
  }

  function identifyVoicing(notes, context = {}) {
    const pitchClasses = Array.from(new Set(toArray(notes).map(pitchClassForNote).filter((value) => value !== null)));
    if (pitchClasses.length < 2) {
      return {
        label: "Need at least two notes",
        quality: "incomplete",
        confidence: "low",
        functionText: "not enough notes to identify a voicing",
        alternates: [],
        intervals: [],
      };
    }
    const candidates = [];
    pitchClasses.forEach((rootPitchClass) => {
      CHORD_QUALITY_PATTERNS.forEach((quality) => {
        const intervals = pitchClasses
          .map((pitchClass) => ((pitchClass - rootPitchClass) % 12 + 12) % 12)
          .sort((a, b) => a - b);
        const allContained = intervals.every((interval) => quality.intervals.includes(interval));
        if (!allContained || !extendedQualityGate(quality, intervals)) {
          return;
        }
        const requiredPresent = quality.required.every((interval) => intervals.includes(interval));
        const missingIntervals = quality.intervals.filter((interval) => !intervals.includes(interval));
        const exact = intervals.length === quality.intervals.length && requiredPresent;
        const partial = missingIntervals.length > 0;
        const missingRootPenalty = missingIntervals.includes(0) ? 16 : 0;
        const missingThirdPenalty = missingIntervals.includes(3) || missingIntervals.includes(4) ? 14 : 0;
        const missingFifthPenalty = missingIntervals.includes(7) ? 3 : 0;
        const extensionBonus = isExtendedChordQuality(quality) ? 8 : 0;
        const score = (exact ? 120 : 82)
          + qualityPriority(quality)
          + extensionBonus
          - missingRootPenalty
          - missingThirdPenalty
          - missingFifthPenalty
          - Math.max(0, missingIntervals.length - 1) * 4;
        candidates.push({
          rootPitchClass,
          quality,
          intervals,
          missingIntervals,
          exact,
          partial,
          score,
        });
      });
    });
    candidates.sort((a, b) => b.score - a.score || String(a.quality.id).localeCompare(String(b.quality.id)));
    const best = candidates[0];
    const keyDominant = dominantColorIdentity(notes, context, best ? chordLabel(best.rootPitchClass, best.quality, context) : "");
    if (keyDominant && (!best || best.quality.id !== "dominant7" || best.partial)) {
      return keyDominant;
    }
    if (!best) {
      return {
        label: "Ambiguous voicing",
        quality: "ambiguous",
        confidence: "low",
        functionText: "not a clear common triad or seventh shape",
        alternates: [],
        intervals: toArray(notes).map((note) => notationLabelForFinalNote(note, "", context)),
      };
    }
    const label = partialChordLabel(best.rootPitchClass, best.quality, best.missingIntervals, context);
    const alternates = candidates
      .filter((candidate) => candidate !== best)
      .slice(0, 3)
      .map((candidate) => partialChordLabel(candidate.rootPitchClass, candidate.quality, candidate.missingIntervals, context));
    return {
      label,
      quality: best.partial ? `partial ${best.quality.label}` : best.quality.label,
      confidence: chordConfidence(best.quality, best.exact, best.missingIntervals, best.intervals),
      functionText: voicingFunctionForRoot(best.rootPitchClass, best.quality, context),
      alternates,
      intervals: intervalLabelsAgainstRoot(notes, best.rootPitchClass),
      rootPitchClass: best.rootPitchClass,
      partial: best.partial,
      missingIntervals: best.missingIntervals.map(omittedIntervalLabel),
      explanation: voicingExplanation(label, best.quality, best.intervals, best.missingIntervals),
    };
  }

  function chordFinderQualityGate(target, presentIntervals) {
    const hasRoot = presentIntervals.includes(0);
    const hasMajorThird = presentIntervals.includes(4);
    const hasMinorThird = presentIntervals.includes(3);
    const hasFlatSeven = presentIntervals.includes(10);
    const hasMajorSeven = presentIntervals.includes(11);
    const hasNinth = presentIntervals.includes(2);
    if (target.quality.id === "major7") {
      return hasMajorSeven && (hasRoot || hasMajorThird);
    }
    if (target.quality.id === "dominant7") {
      return hasFlatSeven && (hasRoot || hasMajorThird);
    }
    if (target.quality.id === "minor7") {
      return hasFlatSeven && (hasRoot || hasMinorThird);
    }
    if (target.quality.id === "major9") {
      return hasNinth && hasMajorSeven && (hasRoot || hasMajorThird);
    }
    if (target.quality.id === "dominant9") {
      return hasNinth && hasFlatSeven && (hasRoot || hasMajorThird);
    }
    if (target.quality.id === "minor9") {
      return hasNinth && hasFlatSeven && (hasRoot || hasMinorThird);
    }
    if (target.quality.id === "minor7flat5") {
      return hasFlatSeven && hasMinorThird && presentIntervals.includes(6);
    }
    if (target.quality.id === "diminished") {
      return hasMinorThird && presentIntervals.includes(6);
    }
    if (target.quality.id === "minor") {
      return hasRoot && hasMinorThird;
    }
    if (target.quality.id === "major") {
      return hasRoot && hasMajorThird;
    }
    return presentIntervals.length >= 2;
  }

  function chordFinderConfidence(target, presentIntervals, omittedIntervals) {
    if (!omittedIntervals.length) {
      return "high";
    }
    const missingThird = omittedIntervals.includes(3) || omittedIntervals.includes(4);
    const missingSeventh = omittedIntervals.includes(10) || omittedIntervals.includes(11);
    const missingNinth = target.quality.id.includes("9") && omittedIntervals.includes(2);
    if (missingThird || missingSeventh || missingNinth) {
      return "medium";
    }
    if (omittedIntervals.includes(0)) {
      return "medium, rootless";
    }
    return "medium-high";
  }

  function normalizeChordFinderText(value) {
    return formatValue(value, "")
      .replace(/♭/g, "b")
      .replace(/♯/g, "#")
      .replace(/Δ/g, "maj")
      .replace(/ø/g, "m7b5")
      .replace(/\s+/g, " ")
      .trim();
  }

  function parseChordFinderQuality(rawValue, options = {}) {
    const raw = normalizeChordFinderText(rawValue).toLowerCase().replace(/[-_]/g, " ");
    const compact = raw.replace(/\s+/g, "");
    const lowerDegree = Boolean(options.lowerDegree);
    if (!compact) {
      return chordQualityById(options.defaultQualityId || "major");
    }
    if (/^(maj9|major9)$/.test(compact)) {
      return chordQualityById("major9");
    }
    if (/^(m9|min9|minor9)$/.test(compact)) {
      return chordQualityById("minor9");
    }
    if (/^9$/.test(compact)) {
      return chordQualityById(lowerDegree ? "minor9" : "dominant9");
    }
    if (/^(maj7|major7)$/.test(compact)) {
      return chordQualityById("major7");
    }
    if (/^(m7b5|half diminished|halfdiminished)$/.test(raw) || /^m7b5$/.test(compact)) {
      return chordQualityById("minor7flat5");
    }
    if (/^(m7|min7|minor7)$/.test(compact)) {
      return chordQualityById("minor7");
    }
    if (/^7$/.test(compact)) {
      return chordQualityById(lowerDegree ? "minor7" : "dominant7");
    }
    if (/^(dim|diminished)$/.test(compact)) {
      return chordQualityById("diminished");
    }
    if (/^sus2$/.test(compact)) {
      return chordQualityById("sus2");
    }
    if (/^sus4$/.test(compact)) {
      return chordQualityById("sus4");
    }
    if (/^(m|min|minor)$/.test(compact)) {
      return chordQualityById("minor");
    }
    if (/^(maj|major)$/.test(compact)) {
      return chordQualityById("major");
    }
    return null;
  }

  function romanDegreeInfo(value) {
    const token = formatValue(value, "").trim();
    const lower = token.toLowerCase();
    const map = { i: 0, ii: 1, iii: 2, iv: 3, v: 4, vi: 5, vii: 6 };
    if (/^[1-7]$/.test(token)) {
      return { index: Number(token) - 1, lowerDegree: false, raw: token };
    }
    if (Object.prototype.hasOwnProperty.call(map, lower)) {
      return { index: map[lower], lowerDegree: token === lower, raw: token };
    }
    return null;
  }

  function defaultQualityForDegree(degree) {
    if (!degree) {
      return chordQualityById("major");
    }
    if (degree.index === 6) {
      return chordQualityById("diminished");
    }
    if (degree.lowerDegree || [1, 2, 5].includes(degree.index)) {
      return chordQualityById("minor");
    }
    return chordQualityById("major");
  }

  function buildChordFinderTarget(rootPitchClass, quality, options = {}) {
    const contextKey = options.contextKey || "G";
    const rootLabel = options.rootLabel || displayNoteForPitchClassInKey(rootPitchClass, contextKey);
    const intervals = Array.isArray(quality?.intervals) ? quality.intervals : [];
    const notes = intervals.map((interval) => displayNoteForPitchClassInKey(rootPitchClass + interval, contextKey));
    const toneLabels = intervals.map((interval, index) => ({
      interval,
      note: notes[index],
      role: intervalRoleLabel(interval),
    }));
    return {
      ok: true,
      source: options.source || "direct",
      input: options.input || "",
      contextKey,
      rootPitchClass,
      rootLabel,
      quality,
      label: `${rootLabel}${quality?.suffix || ""}`,
      notes,
      toneLabels,
      pitchClasses: intervals.map((interval) => normalizePitchClass(rootPitchClass + interval)),
      message: options.message || "",
    };
  }

  function parseFunctionChordFinderQuery(value) {
    const text = normalizeChordFinderText(value);
    const match = text.match(/^([ivIV]+|[1-7])\s*([A-Za-z0-9#b\s]*)\s+in\s+([A-G](?:#|b)?)/);
    if (!match) {
      return null;
    }
    const degree = romanDegreeInfo(match[1]);
    const contextKey = match[3];
    const keyPitchClass = pitchClassForNote(contextKey);
    if (!degree || keyPitchClass === null) {
      return {
        ok: false,
        message: "Use a function such as V7 in G, ii9 in Bb, Imaj7 in F, or vi minor 7 in G.",
      };
    }
    const quality = parseChordFinderQuality(match[2], {
      lowerDegree: degree.lowerDegree,
      defaultQualityId: defaultQualityForDegree(degree).id,
    });
    if (!quality) {
      return {
        ok: false,
        message: "I could not read that chord quality. Try Fmaj7, Cmin9, D7, V7 in G, or ii9 in Bb.",
      };
    }
    const rootPitchClass = normalizePitchClass(keyPitchClass + MAJOR_SCALE_INTERVALS[degree.index]);
    return buildChordFinderTarget(rootPitchClass, quality, {
      source: "function",
      input: value,
      contextKey,
      message: `${match[1]}${quality.suffix || ""} in ${contextKey} resolves to ${displayNoteForPitchClassInKey(rootPitchClass, contextKey)}${quality.suffix || ""}.`,
    });
  }

  function parseDirectChordFinderQuery(value, options = {}) {
    const text = normalizeChordFinderText(value);
    const match = text.match(/^([A-G](?:#|b)?)(.*)$/);
    if (!match) {
      return null;
    }
    const rootPitchClass = pitchClassForNote(match[1]);
    const quality = parseChordFinderQuality(match[2], { defaultQualityId: options.defaultQualityId || "major" });
    if (rootPitchClass === null || !quality) {
      return {
        ok: false,
        message: "I could not read that chord. Try Fmaj7, F major 7, Cmin9, Cm9, D7, G9, Bbmaj7, or V7 in G.",
      };
    }
    return buildChordFinderTarget(rootPitchClass, quality, {
      source: "direct",
      input: value,
      contextKey: match[1],
      rootLabel: displayNoteForPitchClassInKey(rootPitchClass, match[1]),
    });
  }

  function parseChordFinderQuery(value) {
    const text = normalizeChordFinderText(value);
    if (!text) {
      return {
        ok: false,
        message: "Enter a chord or function, such as Fmaj7, Cmin9, V7 in G, or ii9 in Bb.",
      };
    }
    return parseFunctionChordFinderQuery(text) || parseDirectChordFinderQuery(text) || {
      ok: false,
      message: "Try a chord symbol such as Fmaj7, Cmin9, D7, G9, Bbmaj7, or a function such as V7 in G.",
    };
  }

  function gripMetadata(group) {
    return GRIP_REGISTRY.find((entry) => entry.strings === group) || null;
  }

  function gripTierLabel(group) {
    const metadata = gripMetadata(group);
    if (metadata) {
      return metadata.label;
    }
    if (DOMINANT_9TH_GRIPS.has(group)) {
      return "9th-string color grip";
    }
    if (CORE_GROUPS.has(group)) {
      return "Core grip";
    }
    if (EXTENDED_VOICING_GRIPS.has(group)) {
      return "Extended grip";
    }
    if (TWO_STRING_GROUPS.has(group)) {
      return "Two-string grip";
    }
    return "Advanced grip";
  }

  const api = {
    ADVANCED_GROUPS,
    CHORD_QUALITY_PATTERNS,
    CHROMATIC_FLAT_NOTES,
    CHROMATIC_SHARP_NOTES,
    COMMON_VOICING_GRIPS: new Set([
      ...GRIP_REGISTRY.map((entry) => entry.strings),
      ...CORE_GROUPS,
      ...ADVANCED_GROUPS,
      ...TWO_STRING_GROUPS,
      ...FIVE_EIGHT_GROUPS,
      ...EXTENDED_VOICING_GRIPS,
      ...DOMINANT_9TH_GRIPS,
    ]),
    CORE_GROUPS,
    DEFAULT_E9_CONTROL_CHANGES,
    DEFAULT_E9_OPEN_STRING_PITCH_VALUES,
    DEFAULT_E9_OPEN_STRINGS,
    DOMINANT_9TH_GRIPS,
    EXTENDED_VOICING_GRIPS,
    FIVE_EIGHT_GROUPS,
    GRIP_REGISTRY,
    MAJOR_SCALE_INTERVALS,
    MAJOR_SCALE_SEQUENCES,
    NATURAL_MINOR_SCALE_SEQUENCES,
    NOTE_CONTROL_STATES,
    TWO_STRING_DISPLAY_GROUPS,
    TWO_STRING_GROUPS,
    buildChordFinderTarget,
    chordConfidence,
    chordFinderConfidence,
    chordFinderQualityGate,
    chordLabel,
    chordQualityById,
    defaultQualityForDegree,
    displayNoteForPitchClass,
    displayNoteForPitchClassInKey,
    dominantColorIdentity,
    dominantTargetForKey,
    extendedQualityGate,
    formatInterval,
    formatIntervalForNotation,
    formatTheoryText,
    gripMetadata,
    gripTierLabel,
    identifyVoicing,
    intervalAsNns,
    intervalAsNumberQuality,
    intervalAsRoman,
    intervalLabelsAgainstRoot,
    intervalNameFromSemitones,
    intervalRoleLabel,
    isExtendedChordQuality,
    normalizeChordFinderText,
    normalizeIntervalToken,
    notationLabelForFinalNote,
    noteAlternates,
    noteAtFret,
    octaveBandForPitchValue,
    omittedIntervalLabel,
    parseChordFinderQuality,
    parseChordFinderQuery,
    parseDirectChordFinderQuery,
    parseFunctionChordFinderQuery,
    partialChordLabel,
    pitchClassForNote,
    pitchRegisterDetail,
    prefersFlatSpelling,
    qualityPriority,
    resolveE9Note,
    romanDegreeInfo,
    scaleDegreeIndexForNote,
    scientificPitchForValue,
    voicingExplanation,
    voicingFunctionForRoot,
  };

  root.STEEL_RAG_E9_MUSIC_RULES = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
