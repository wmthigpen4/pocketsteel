(function (global) {
  "use strict";

  const GRIP_VOCABULARY_OPTIONS = [
    { id: "core", label: "Core", description: "Common beginner-friendly string sets and harmonized-scale grips." },
    { id: "extended", label: "Extended", description: "Real-world tab and voicing-discovery grips, including wider and 9th-string color grips." },
    { id: "song_tab", label: "Song/tab vocabulary", description: "Context-dependent string sets seen in real playing and tab-like vocabulary." },
    { id: "e_lower_pockets", label: "E-lower pockets", description: "Lever-pocket grips that depend on the E-lower change, including 5-7-8." },
    { id: "two_string", label: "Two-string", description: "Dyads for harmony lines, partial voicings, passing color, and possible pad/sustain uses." },
    { id: "all", label: "All legitimate", description: "All registered core, path, extended, song/tab, E-lower, and two-string grip vocabulary." },
  ];
  const GRIP_ROLE_OPTIONS = [
    { id: "all", label: "All", description: "Show every role in the selected vocabulary." },
    { id: "harmonized_scale_path", label: "Scale path", description: "Used for connected harmonized-scale movement." },
    { id: "melody_harmony", label: "Melody harmony", description: "Useful for harmonized melody movement." },
    { id: "wide_voicing", label: "Wide voicing", description: "Spreads the chord across wider string gaps." },
    { id: "spread_voicing", label: "Spread voicing", description: "Keeps more space between chord tones." },
    { id: "chord_shell", label: "Chord shell", description: "A practical chord-tone subset or shell." },
    { id: "pad_sustain", label: "Pads", description: "Possible held support sounds; not every dyad is a pad." },
    { id: "chord_voicing", label: "Chord / voicing", description: "Useful for chord shapes and partial voicings." },
    { id: "dominant_color", label: "Dominant color", description: "Useful for V7 or flat-7 color." },
    { id: "major_7_color", label: "Major-7 color", description: "Useful when the notes support major-7 color." },
    { id: "minor_color", label: "Minor color", description: "Useful for minor pockets and relative-minor movement." },
    { id: "bass_root_support", label: "Bass/root support", description: "Useful when a low string supports the root or bass motion." },
    { id: "passing_color", label: "Passing color", description: "Useful for color tones between stronger chord positions." },
    { id: "lever_pocket", label: "Lever pocket", description: "Depends on a lever change for the pocket color." },
    { id: "alternate_position", label: "Alternate position", description: "A secondary way to find the same or related sound." },
    { id: "e_lower_pocket", label: "E-lower pocket", description: "Specifically uses E-lower pocket vocabulary." },
  ];
  const EXPLORE_MODES = {
    single: "single",
    path: "path",
    note: "note",
    voicing: "voicing",
    chord: "chord",
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
  const PITCH_REGISTER_MODES = [
    { id: "off", label: "Off" },
    { id: "scientific", label: "Scientific" },
    { id: "band", label: "Octave band" },
  ];
  const NOTE_WORKFLOWS = [
    { id: "find", label: "Find all", description: "Highlight every matching note or scale value in the visible fret range." },
    { id: "reverse", label: "Reverse lookup", description: "List ways to get the target note or notation value on selected strings." },
    { id: "changes", label: "Pedal changes", description: "Compare open/no-control notes against the active pedal or lever state." },
    { id: "grip", label: "Build grip", description: "Find practical validated grips that contain the selected note set." },
    { id: "drill", label: "Drill", description: "Click a matching cell and get deterministic practice feedback." },
    { id: "sync", label: "Event sync", description: "Step through safe deterministic events and focus the matching cell." },
  ];
  const CHORD_FINDER_ROOT_OPTIONS = [
    "C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B",
  ];
  const CHORD_FINDER_QUALITY_LABELS = {
    major: "Major",
    minor: "Minor",
    diminished: "Diminished",
    minor7flat5: "Half-diminished",
    sus2: "Sus2",
    sus4: "Sus4",
    dominant7: "Dominant 7",
    major7: "Major 7",
    minor7: "Minor 7",
    dominant9: "Dominant 9",
    minor9: "Minor 9",
    major9: "Major 9",
  };
  const CHORD_FINDER_QUALITY_ORDER = [
    "major",
    "minor",
    "diminished",
    "minor7flat5",
    "sus2",
    "sus4",
    "dominant7",
    "major7",
    "minor7",
    "dominant9",
    "minor9",
    "major9",
  ];
  const CHORD_FINDER_CONTROL_SCOPES = [
    { id: "open", label: "Open only", controlCombos: [[]] },
    { id: "common", label: "Common controls", controlCombos: [[], ["A"], ["B"], ["A", "B"], ["B", "C"]] },
    { id: "levers", label: "Include levers", controlCombos: [[], ["A"], ["B"], ["A", "B"], ["B", "C"], ["A", "E-raise"], ["E-raise"], ["E-lower"], ["D-lower"], ["G-lower"]] },
    { id: "all", label: "All practical", controlCombos: [[], ["A"], ["B"], ["A", "B"], ["B", "C"], ["A", "E-raise"], ["A", "B", "E-lower"], ["E-raise"], ["E-lower"], ["D-lower"], ["G-lower"]] },
  ];
  const TASK_CARD_META = {
    "find-chord": {
      label: "Find a chord",
      context: "Search practical chord pockets before choosing one on the fretboard.",
    },
    "find-note": {
      label: "Find a note",
      context: "Locate one note, then check which pedals or levers move it.",
    },
    "explore-grip": {
      label: "Explore a grip",
      context: "Start with one playable string set and compare validated pockets.",
    },
    "walk-harmonized-scale": {
      label: "Walk a harmonized scale",
      context: "Follow the scale path; each card maps to a visible fretboard marker.",
    },
    "study-movement-path": {
      label: "Study a movement path",
      context: "Compare nearby grips that connect one chord shape to another.",
    },
    "identify-voicing": {
      label: "Identify a voicing",
      context: "Choose fret, strings, and controls to name the shape.",
    },
  };
  const api = {
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
    CHORD_FINDER_ROOT_OPTIONS,
    CHORD_FINDER_QUALITY_LABELS,
    CHORD_FINDER_QUALITY_ORDER,
    CHORD_FINDER_CONTROL_SCOPES,
    TASK_CARD_META,
  };
  global.STEEL_RAG_E9_EXPLORER_CONFIG = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
