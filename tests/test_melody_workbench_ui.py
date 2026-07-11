from __future__ import annotations

import subprocess
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_node(script: str) -> None:
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_melody_workbench_helpers_parse_validate_reorder_and_build_payloads() -> None:
    run_node(
        r"""
const assert = require("node:assert/strict");
const studio = require("./ui/melody-workbench.js");

assert.deepEqual(studio.parsePhraseInput("1 2, 3 | 5"), ["1", "2", "3", "5"]);
assert.deepEqual(studio.parsePhraseInput("g a b d"), ["G", "A", "B", "D"]);
assert.deepEqual(studio.parsePhraseInput("S4: 3 5 7 10"), ["G", "A", "B", "D"]);
assert.equal(studio.noteAtFret(4, 3), "G");
assert.equal(studio.noteAtFret(5, 1), "C");
assert.equal(studio.sectionCount(["1", "2", "3", "4", "5", "6", "7", "1", "2"]), 2);
assert.deepEqual(studio.reorderToken(["1", "2", "3"], 1, -1), ["2", "1", "3"]);
assert.equal(studio.validateTokens(["1", "2", "3"], "G").ok, true);
assert.equal(studio.validateTokens(["G", "A", "B", "D"], "G").ok, true);
assert.equal(studio.validateTokens(["F"], "G").ok, false);
assert.equal(studio.startingPointForKind("user_melody"), "phrase");
assert.equal(studio.startingPointForKind("artist_solo_lesson"), "recording");
assert.equal(studio.startingPointForKind("song_arrangement_lesson"), "recording");
assert.equal(studio.startingPointForKind("original_exercise"), "exercise");
assert.equal(studio.createInitialState().kind, "user_melody");
const literal = studio.parseSimpleTabEvents("S4: 3 5F 7");
assert.deepEqual(literal.map((event) => [event.string, event.fret, event.changes]), [[4, 3, []], [4, 5, ["F"]], [4, 7, []]]);
assert.deepEqual(studio.resolvePhrasePreview([{token: "5"}, {token: "6"}, {token: "1"}, {token: "3"}], "G").map((event) => event.pitch), ["D4", "E4", "G4", "B4"]);
assert.deepEqual(studio.resolvePhrasePreview([{token: "5"}, {token: "6"}, {token: "1", octaveShift: 1}, {token: "3"}], "G").map((event) => event.pitch), ["D4", "E4", "G5", "B4"]);

const artist = studio.createInitialState("artist_solo_lesson");
Object.assign(artist, {
  artist: "Example Artist",
  song: "Example Song",
  recording: "Studio version",
  sourceUrl: "https://example.test/recording",
  tokens: ["1", "2", "3"],
  sectionNumber: 2
});
const artistPayload = studio.buildMelodyRequest(artist);
assert.equal(artistPayload.kind, "artist_solo_lesson");
assert.equal(artistPayload.sectionNumber, 2);
assert.equal(artistPayload.material.artist, "Example Artist");
assert.equal(artistPayload.renderingMode, "transcription");
assert.equal(artistPayload.contourMode, "closest_playable");
assert.equal(artistPayload.texture, "both");

const original = studio.createInitialState("original_exercise");
Object.assign(original, { tokens: ["1", "3", "5"], artist: "Stale Artist", sourceUrl: "https://example.test/stale" });
const originalPayload = studio.buildMelodyRequest(original);
assert.equal("material" in originalPayload, false);
assert.deepEqual(originalPayload.melody, ["1", "3", "5"]);
assert.deepEqual(
  studio.eventStepPresentation({ step: 1, resolvedNote: "D", resolvedPitch: "D4", notes: [{ string: 5, fret: 3, changes: [] }] }),
  { note: "1. D4", position: "String 5 · Fret 3 · Open" }
);
assert.deepEqual(
  studio.eventStepPresentation({ step: 2, resolvedPitch: "E4", notes: [{ string: 4, fret: 3, changes: ["A"] }, { string: 6, fret: 3, changes: ["A"] }] }),
  { note: "2. E4", position: "Strings 4 + 6 · Fret 3 · A pedal" }
);
assert.deepEqual(
  studio.eventStepCompactPresentation({ resolvedPitch: "E4", notes: [{ string: 4, fret: 3, changes: ["A"] }, { string: 6, fret: 3, changes: ["A"] }] }),
  { note: "E4", position: "S4+6 · F3 · A" }
);
assert.equal(studio.routeButtonLabel({ recommended: true, label: "Recommended harmony" }), "Recommended harmony");
assert.equal(studio.scientificOctaveForEvent({ resolvedPitch: "D4", pitchValue: 62 }), 4);
assert.equal(studio.scientificOctaveForEvent({ resolvedPitch: "G5", pitchValue: 79 }), 5);
assert.equal(studio.scientificOctaveForEvent({ pitchValue: 47 }), 2);
assert.equal(studio.scientificOctaveForEvent({ resolvedPitch: "not-a-pitch", pitchValue: 64 }), 4);
assert.equal(studio.scientificOctaveForEvent({ resolvedPitch: "C7", pitchValue: 96 }), null);
assert.equal(studio.scientificOctaveForEvent({ resolvedPitch: "D4", notes: [{ scientificPitch: "B2" }, { scientificPitch: "D4" }] }), 4);
assert.equal(studio.scientificOctaveForEvent({ resolvedPitch: "", pitchValue: "bad" }), null);
assert.equal(studio.scientificOctaveLabel(4), "Octave 4 — C4 through B4");
assert.equal(studio.scientificOctaveLabel(7), "");
assert.equal(studio.scientificOctaveForTabNote({ string: 10, fret: 0, changes: [] }), 2);
assert.equal(studio.scientificOctaveForTabNote({ string: 5, fret: 3, changes: [] }), 4);
assert.equal(studio.scientificOctaveForTabNote({ string: 5, fret: 1, changes: ["A"] }), 4);
const octavePositions = studio.positionsWithScientificOctaves(
  [{ id: "event-1", label: "Your melody exercise in G — Single-note melody", strings: [5, 6] }],
  [{ step: 1, resolvedPitch: "D4", renderablePositionId: "event-1", notes: [{ string: 5, fret: 3, changes: ["A"] }, { string: 6, fret: 3, changes: ["B"] }] }]
);
assert.deepEqual(octavePositions[0].scientificOctavesByString, { 5: 4, 6: 4 });
assert.deepEqual(octavePositions[0].stringActionLabels, [{ string: 5, label: "5A" }, { string: 6, label: "6B" }]);
assert.equal(octavePositions[0].label, "D4");
assert.equal(octavePositions[0].role, "Melody note 1");
assert.doesNotMatch(octavePositions[0].label, /Your melody exercise/);
const fretboardOptions = studio.melodyFretboardOptions(
  { maxFret: 24, stringCount: 10, tuningLabels: [], positions: octavePositions, highlights: [], legend: [], query: {} },
  []
);
assert.equal(fretboardOptions.showScientificOctaveOverlay, true);
assert.equal(fretboardOptions.hidePositionTools, true);
const activeOnlyOptions = studio.melodyFretboardOptions(
  { maxFret: 24, stringCount: 10, tuningLabels: [], positions: [{id: "event-1", strings: [5]}, {id: "event-2", strings: [4]}], highlights: [], legend: [], query: {} },
  [
    {step: 1, resolvedPitch: "D4", renderablePositionId: "event-1", notes: [{string: 5, fret: 3, changes: []}]},
    {step: 2, resolvedPitch: "G4", renderablePositionId: "event-2", notes: [{string: 4, fret: 3, changes: []}]}
  ],
  1,
  {showNoteLabels: false, showStringLabels: true}
);
assert.deepEqual(activeOnlyOptions.positions.map((position) => position.id), ["event-2"]);
assert.equal(activeOnlyOptions.showHighlightLabels, false);
assert.equal(activeOnlyOptions.showStringActionLabels, true);
assert.equal(activeOnlyOptions.stringActionLabelMode, "all");
assert.equal(studio.createInitialState().showOctaveMap, true);
assert.equal(studio.createInitialState().showStringLabels, false);
assert.equal(studio.createInitialState().showNoteLabels, true);
assert.equal(studio.createInitialState().inputMethod, "phrase");
assert.equal(studio.youtubeVideoId("https://youtu.be/abc123?t=9"), "abc123");
assert.equal(studio.youtubeVideoId("https://www.youtube.com/watch?v=xyz789"), "xyz789");
assert.equal(studio.referenceEmbedUrl("https://youtube.com/watch?v=xyz789", 10, 20), "https://www.youtube-nocookie.com/embed/xyz789?rel=0&playsinline=1&start=10&end=20");
assert.equal(studio.youtubeVideoId("https://ultimate-guitar.com/tab/example"), "");
assert.equal(studio.fileSourceType({name: "page.webp", type: "image/webp"}), "image");
assert.equal(studio.fileSourceType({name: "song.mxl", type: ""}), "mxl");
assert.equal(studio.frequencyToMidi(440), 69);
assert.equal(studio.frequencyToMidiFloat(440), 69);
assert.equal(studio.quantizeTranscriptionBeats(0.5, 120), 1);
const audioSamples = [];
for (let index = 0; index < 10; index += 1) audioSamples.push({time: index * 0.05, midiFloat: 60.04 + (index % 2 ? 0.02 : -0.02)});
for (let index = 0; index < 10; index += 1) audioSamples.push({time: 1 + index * 0.05, midiFloat: 61.97 + (index % 2 ? 0.02 : -0.02)});
const transcription = studio.transcribePitchSamples(audioSamples, {bpm: 120});
assert.deepEqual(transcription.events.map((event) => event.rest ? ["rest", event.durationBeats] : [event.pitch, event.durationBeats]), [["C4", 1], ["rest", 1], ["D4", 1]]);
assert.equal(transcription.confidenceLabel, "medium");
assert.match(transcription.warnings[0], /confirm every note/i);
const transcriptionDraft = studio.createAudioTranscriptionDraft(audioSamples, {bpm: 120, key: "G", sourceType: "audio_file", title: "Test melody"});
assert.equal(transcriptionDraft.schemaVersion, "score_draft_v1");
assert.equal(transcriptionDraft.source.retained, false);
assert.equal(transcriptionDraft.review.status, "needs_review");
assert.equal(transcriptionDraft.transcription.audioRetained, false);
assert.deepEqual(transcriptionDraft.score.melody.map((event) => event.rest ? "rest" : event.pitch), ["C4", "rest", "D4"]);
const pcm = new Float32Array(4000);
for (let index = 0; index < pcm.length; index += 1) pcm[index] = 0.4 * Math.sin(2 * Math.PI * 440 * index / 8000);
const pcmSamples = studio.pitchSamplesFromPcm(pcm, 8000);
assert.ok(pcmSamples.length > 3);
assert.ok(Math.abs(pcmSamples.find((sample) => sample.midiFloat !== null).midiFloat - 69) < 0.5);
const audioState = studio.createInitialState("user_melody");
audioState.tokens = [{token: "C4", pitch: "C4", pitchValue: 60, confidence: 0.72}];
audioState.scoreDraft = {transcription: {engine: "on_device_monophonic_v1", confidence: 0.72, confidenceLabel: "medium", audioRetained: false}};
const audioRequest = studio.buildMelodyRequest(audioState);
assert.equal(audioRequest.accuracy, "approximate");
assert.equal(audioRequest.accuracyConfidence, "medium");
assert.equal(audioRequest.transcription.audioRetained, false);
assert.deepEqual(studio.chordPitchValues("G"), [55, 59, 62]);
assert.deepEqual(studio.chordPitchValues("Em7"), [52, 55, 59, 62]);
"""
    )


def test_score_draft_builder_reflows_edits_transposes_and_exports_musicxml() -> None:
    run_node(
        r"""
const assert = require("node:assert/strict");
const score = require("./ui/melody-score.js");

let draft = score.createDraft({key: "G", meter: "3/4", pickupBeats: 1, title: "Amazing Grace sketch"});
draft = score.addEvent(draft, {pitchValue: 62, durationBeats: 1});
draft = score.addEvent(draft, {pitchValue: 67, durationBeats: 2});
draft = score.addEvent(draft, {pitchValue: 71, durationBeats: 0.5});
assert.deepEqual(draft.score.melody.map((event) => [event.measure, event.beat]), [[1, 3], [2, 1], [2, 3]]);
draft = score.setChordAtEvent(draft, 1, "G");
draft = score.updateEvent(draft, 1, {lyric: "grace", tie: "start", articulation: "accent"});
assert.equal(score.chordForEvent(draft, draft.score.melody[2]), "G");
assert.equal(score.chordChangeAtEvent(draft, draft.score.melody[1]), "G");
assert.equal(score.chordChangeAtEvent(draft, draft.score.melody[2]), "");
assert.deepEqual(score.arrangementEvents(draft)[1], {
  token: "G4", pitch: "G4", pitchValue: 67, measure: 2, beat: 1,
  durationBeats: 2, origin: "user_edit", confidence: 1, tie: "start", lyric: "grace", articulation: "accent", chord: "G"
});
const transposed = score.transposeDraft(draft, -5);
assert.deepEqual(transposed.score.melody.map((event) => event.pitch), ["A3", "D4", "F#4"]);
const xml = score.musicXmlForDraft(draft);
assert.match(xml, /<work-title>Amazing Grace sketch<\/work-title>/);
assert.match(xml, /<time><beats>3<\/beats>/);
assert.match(xml, /<words>G<\/words>/);
assert.match(xml, /<lyric><text>grace<\/text><\/lyric>/);
assert.match(xml, /<articulations><accent\/><\/articulations>/);
assert.equal(score.removeEvent(draft, 0).score.melody.length, 2);
assert.equal(score.duplicatePhrase(draft).score.melody.length, 6);
assert.equal(score.clearMeasure(draft, 2).score.melody.length, 1);
let overfull = score.createDraft({key: "G", meter: "3/4"});
overfull = score.addEvent(overfull, {pitchValue: 67, durationBeats: 4});
assert.match(score.draftWarnings(overfull)[0], /Measure 1 has 4 beats but allows 3/);
"""
    )


def test_melody_workbench_has_direct_phrase_entry_and_compact_note_navigator() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")
    script = Path("ui/melody-workbench.js").read_text(encoding="utf-8")
    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids))

    assert "Turn a phrase into an E9 lesson." in html
    assert "Step 1 of 4" not in html
    assert 'data-studio-start="phrase"' in html
    assert 'data-studio-start="score"' in html
    assert 'data-studio-start="import"' in html
    assert 'data-studio-start="microphone"' in html
    assert 'data-studio-start="recording"' in html
    assert 'data-studio-start="catalog"' in html
    assert html.count("data-studio-start=") == 6
    assert "Enter notes or intervals" in html
    assert "Build a score" in html
    assert "Photo or music file" in html
    assert "Record or upload audio" in html
    assert "Use a recording" in html
    assert "Pick a song" in html
    assert 'data-source-treatment="artist_solo_lesson"' in html
    assert 'data-source-treatment="song_arrangement_lesson"' in html
    assert "Faithful solo passage" in html
    assert "Playable E9 arrangement" in html
    assert 'id="studio-material-fields" data-input-panel="recording" hidden' in html
    assert 'id="studio-presets" aria-label="Practice phrase presets" hidden' in html
    assert 'id="studio-palette"' in html
    assert 'id="studio-sequence"' in html
    assert 'data-preset="1-2-3-5"' in html
    assert 'id="studio-fretboard"' in html
    assert 'id="studio-octave-guide"' in html
    assert 'id="studio-octave-toggle" aria-pressed="true"' in html
    assert 'id="studio-string-label-toggle" aria-pressed="false"' in html
    assert 'id="studio-note-label-toggle" aria-pressed="true"' in html
    assert 'id="studio-octave-map-controls" hidden' in html
    assert 'aria-label="Octave 4 — C4 through B4"' in html
    assert 'data-scientific-octave="2"] { --octave-color: #b8a3ff;' in html
    assert 'data-scientific-octave="4"] { --octave-color: #58d6bd;' in html
    assert 'data-scientific-octave="6"] { --octave-color: #ff927d;' in html
    assert ".octave-map-controls { min-width: 0; display: flex;" in html
    assert ".register-stepper { grid-template-columns: 44px minmax(0, 1fr) 44px; }" in html
    assert "overflow-x: auto" in html
    assert ".event-step:focus-visible" in html
    assert 'id="studio-register-value"' in html
    assert 'aria-label="Lower selected note one octave"' in html
    assert 'aria-label="Raise selected note one octave"' in html
    assert 'id="studio-current-note" hidden' in html
    assert 'id="studio-note-progress"' in html
    assert 'class="note-navigator-row"' in html
    assert 'aria-label="Previous note">←</button>' in html
    assert 'aria-label="Next note">→</button>' in html
    assert '<span class="octave-toggle-mark" aria-hidden="true">✓</span>Octave colors</button>' in html
    assert '<span class="octave-toggle-mark" aria-hidden="true">✓</span>String labels</button>' in html
    assert '<span class="octave-toggle-mark" aria-hidden="true">✓</span>Note labels</button>' in html
    assert 'id="studio-contour"' in html
    assert 'id="studio-route-tabs"' in html
    assert 'id="studio-note-editor" hidden' in html
    assert 'id="studio-octave-down"' in html
    assert 'id="studio-octave-auto"' in html
    assert 'id="studio-octave-up"' in html
    assert 'id="studio-more-routes"' not in html
    assert 'id="studio-result-meta"' not in html
    assert "Practice the lesson" not in html
    assert 'id="studio-change-task"' not in html
    assert "activateRoute" in script
    assert "hideFilterControls: true" in script
    assert "hidePositionTools: true" in script
    assert "hideLegend: true" in script
    assert "Select a note below to change its octave" in html
    assert "Change the register for this note only" in html
    assert "state.selectedPhraseIndex" in script
    assert html.count("?v=melody-multi-input-20260711-3") == 2
    assert html.count("?v=melody-score-practice-20260711-3") == 1
    assert html.count("?v=melody-audio-transcription-20260711-2") == 1
    assert 'src="vendor/vexflow-5.0.0.js?v=5.0.0"' in html
    assert "VexFlow" in Path("ui/vendor/VEXFLOW-LICENSE.txt").read_text(encoding="utf-8")
    assert html.index('id="studio-fretboard"') < html.index('id="studio-tab"')
    assert 'id="studio-continue"' in html
    assert "Melody Studio never scrapes or copies its tab" in html
    assert "renderActiveFretboard" in script
    assert "Active tab note" not in script
    assert 'id="studio-active-tab-step"' not in html
    assert 'id="studio-event-detail"' not in html
    assert "Active step" not in script
    assert "eventStepCompactPresentation" in script
    assert "elements.routeTabs.appendChild(button)" in script
    assert "advancedRoutes" not in script
    assert "moreRoutes" not in script
    assert ".route-tabs { max-width: 100%; display: flex; flex-wrap: nowrap;" in html
    assert "Note ${state.activeEventIndex + 1} of ${events.length}" in script
    assert "button.dataset.scientificOctave" in script
    assert "elements.octaveGuide.hidden" in script
    assert "updateOctaveMapVisibility" in script
    assert "showScientificOctaveOverlay: true" in script
    assert "scientificOctavesByString" in script
    assert "requestPayload: { melodyRequest: buildMelodyRequest(state) }" in script
    assert "clearMaterial();" in script
    assert "sectionNumber" in script
    assert "[object Object]" not in html
    assert 'id="studio-score-canvas"' in html
    assert 'id="studio-score-download"' in html
    assert 'id="studio-import-file"' in html
    assert 'id="studio-microphone-start"' in html
    assert 'id="studio-audio-file"' in html
    assert 'id="studio-audio-analyze"' in html
    assert 'id="studio-transcription-tempo"' in html
    assert 'id="studio-score-confidence"' in html
    assert "audio is decoded in this browser" in html
    assert 'id="studio-youtube-frame"' in html
    assert 'id="studio-catalog-grid"' in html
    assert 'id="studio-result-score"' in html
    assert 'id="studio-score-articulation"' in html
    assert 'id="studio-practice-play"' in html
    assert 'id="studio-practice-tempo"' in html
    assert 'id="studio-practice-count-in"' in html
    assert 'id="studio-practice-chords"' in html
    assert 'id="studio-practice-loop-measure"' in html
    assert 'id="studio-practice-loop-start"' in html
    assert 'id="studio-practice-loop-end"' in html
    assert 'id="studio-result-print"' in html
    assert "addKeySignature" in Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert "generateBeams" in Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert "togglePractice" in script
    assert "schedulePitch" in script
    assert "session-only" in html.lower()


def test_melody_workbench_uses_explorer_background_without_turnaround_branding() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")

    assert "The Turnaround" not in html
    assert "steel-guitar-rag-landing-fallback-alpha.png" not in html
    assert "radial-gradient(circle at 52% 0%, rgba(221, 139, 45, 0.28), transparent 35%)" in html
    assert "linear-gradient(180deg, rgba(13, 10, 7, 0.96), #050403 72%)" in html
