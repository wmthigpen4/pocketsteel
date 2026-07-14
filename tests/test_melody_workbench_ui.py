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
assert.equal(studio.sectionCount(Array.from({ length: 17 }, () => "1")), 2);
assert.deepEqual(studio.reorderToken(["1", "2", "3"], 1, -1), ["2", "1", "3"]);
assert.equal(studio.validateTokens(["1", "2", "3"], "G").ok, true);
assert.equal(studio.validateTokens(["G", "A", "B", "D"], "G").ok, true);
assert.equal(studio.validateTokens(["F"], "G").ok, false);
assert.equal(studio.startingPointForKind("user_melody"), "phrase");
assert.equal(studio.startingPointForKind("artist_solo_lesson"), "recording");
assert.equal(studio.startingPointForKind("song_arrangement_lesson"), "recording");
assert.equal(studio.startingPointForKind("original_exercise"), "exercise");
assert.equal(studio.createInitialState().kind, "user_melody");
assert.equal(studio.createInitialState().inputMethod, "phrase");
assert.equal(studio.createInitialState().workflowPhase, "add");
assert.equal(studio.createInitialState().pendingReplacement, "");
assert.equal(studio.printableLessonTitle({title: "Amazing Grace — Complete E9 lesson", material: {song: "Amazing Grace"}}), "Amazing Grace");
assert.equal(studio.printableLessonTitle({title: "Example — Section 2 E9 lesson"}), "Example");
assert.equal(studio.printableLessonTitle({title: "Your melody exercise in G"}), "Your melody exercise in G");
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
artist.scoreDraft = {score: {sections: [{label: "Verse", startMeasure: 1, endMeasure: 4}]}};
assert.deepEqual(studio.buildMelodyRequest(artist).sections, [{label: "Verse", startMeasure: 1, endMeasure: 4}]);
assert.equal(studio.buildMelodyRequest(artist).wholeSong, true);
artist.scoreDraft.score.meter = "3/4";
artist.scoreDraft.score.pickupBeats = 1;
assert.equal(studio.buildMelodyRequest(artist).meter, "3/4");
assert.equal(studio.buildMelodyRequest(artist).pickupBeats, 1);

const original = studio.createInitialState("original_exercise");
Object.assign(original, { tokens: ["1", "3", "5"], artist: "Stale Artist", sourceUrl: "https://example.test/stale" });
const originalPayload = studio.buildMelodyRequest(original);
assert.equal("material" in originalPayload, false);
assert.deepEqual(originalPayload.melody, ["1", "3", "5"]);
const savedTarget = studio.savedE9TargetCopedent({getItem: () => JSON.stringify({
  id: "local-e9", name: "My road guitar", tuningFamily: "E9", stringCount: 10,
  strings: ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"].map((openNote, index) => ({stringNumber: index + 1, openNote, gauge: "private"})),
  controls: [{id: "my-a", label: "My A", type: "pedal", changes: [{stringNumber: 5, fromNote: "B", toNote: "C#", notes: "private"}]}],
  guitar: "private", notes: "private"
})});
assert.equal(savedTarget.name, "My road guitar");
assert.equal(savedTarget.guitar, undefined);
assert.equal(savedTarget.strings[0].gauge, undefined);
assert.equal(savedTarget.controls[0].changes[0].notes, undefined);
const personalized = studio.createInitialState("user_melody");
personalized.tokens = ["1"];
personalized.targetCopedent = savedTarget;
const personalizedPayload = studio.buildMelodyRequest(personalized);
assert.equal(personalizedPayload.targetCopedentId, "saved:local-e9");
assert.equal(personalizedPayload.targetCopedent.name, "My road guitar");
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
assert.equal(studio.routeButtonLabel({ recommended: true, label: "Recommended arrangement" }), "Recommended arrangement");
const recommendedRoute = { id: "mixed", harmonyType: "mixed_arrangement", label: "Recommended arrangement" };
const faithfulRoute = { id: "faithful", harmonyType: "single_note", label: "Faithful melody" };
assert.equal(studio.preferredStudioRoute({ selectedRouteId: "faithful", routes: [faithfulRoute, recommendedRoute] }), recommendedRoute);
assert.equal(studio.preferredStudioRoute({ selectedRouteId: "faithful", routes: [faithfulRoute] }), faithfulRoute);
assert.equal(studio.preferredStudioRoute({ selectedRouteId: "missing", routes: [faithfulRoute] }), faithfulRoute);
assert.equal(studio.preferredStudioRoute({ routes: [] }), null);
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
assert.equal(studio.pitchValueForTabNote({ string: 6, fret: 10, changes: ["B"] }), 67);
assert.deepEqual(studio.scorePitchesForEvent({
  pitchValue: 67,
  notes: [{string: 6, fret: 10, changes: ["B"]}, {string: 10, fret: 10, changes: ["A"]}]
}), [59, 67]);
assert.deepEqual(studio.scorePitchesForEvent({pitchValue: 67, notes: []}), [67]);
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
assert.equal(studio.createInitialState().showOctaveMap, false);
assert.equal(studio.readableEventPosition({notes: [
  {string: 10, fret: 10, changes: ["B"]},
  {string: 6, fret: 10, changes: ["A"]},
  {string: 7, fret: 10, changes: ["B"]}
]}), "Strings 6, 7 & 10 · Fret 10 · A+B");
assert.equal(studio.readableEventPosition({performanceControls: ["A", "B"], notes: [
  {string: 4, fret: 5, changes: []}, {string: 5, fret: 5, changes: ["A"]}, {string: 6, fret: 5, changes: ["B"]}
]}), "Strings 4, 5 & 6 · Fret 5 · A+B");
assert.equal(studio.hasChordContext([{resolvedPitch: "G4"}]), false);
assert.equal(studio.hasChordContext([{resolvedPitch: "G4", chord: "G"}]), true);
const transitionSource = {
  resolvedPitch: "A4",
  performanceControls: ["A", "B"],
  notes: [{string: 4, fret: 5, changes: []}, {string: 5, fret: 5, changes: ["A"]}, {string: 6, fret: 5, changes: ["B"]}]
};
const transitionTarget = {
  resolvedPitch: "G4",
  selectionReason: "Keeps the melody in the open G pocket.",
  patternFamily: "open-major",
  canonicalGrip: "4-5-6",
  chord: "G",
  performanceControls: [],
  notes: [{string: 4, fret: 3, changes: []}, {string: 5, fret: 3, changes: []}, {string: 6, fret: 3, changes: []}]
};
const semanticTransition = {
  kind: "bar_slide", scope: "melody_voice", fromFret: 5, toFret: 3,
  controlsBefore: ["A", "B"], controlsAfter: [],
  fromStrings: [4, 5, 6], toStrings: [4, 5, 6], sustainedStrings: [4], repickedStrings: [5, 6], releasedStrings: [5, 6],
  voiceActions: [{string: 4, action: "bar_slide"}, {string: 5, action: "repick"}, {string: 6, action: "repick"}]
};
assert.deepEqual(studio.transitionSustainedStrings(semanticTransition), [4]);
assert.deepEqual(studio.transitionGlidingStrings(semanticTransition), [4]);
assert.match(studio.transitionChoreography(semanticTransition, transitionSource, transitionTarget), /Pick strings 4, 5 & 6 at fret 5 with A\+B/);
assert.match(studio.transitionChoreography(semanticTransition, transitionSource, transitionTarget), /slide string 4 from fret 5 to fret 3/);
assert.match(studio.transitionChoreography(semanticTransition, transitionSource, transitionTarget), /release A\+B at the arrival/);
assert.match(studio.transitionChoreography(semanticTransition, transitionSource, transitionTarget), /block and release strings 5 & 6 before the slide/);
assert.match(studio.transitionChoreography(semanticTransition, transitionSource, transitionTarget), /repick strings 5 & 6 at the arrival/);
assert.deepEqual(studio.transitionScoreVoices(semanticTransition, transitionSource, transitionTarget), [
  {string: 4, action: "bar_slide", fromPitchValue: 69, toPitchValue: 67}
]);
for (const sourceFret of [5, 10]) {
  const fullGripSource = {
    resolvedPitch: sourceFret === 5 ? "A4" : "D5",
    pitchValue: sourceFret === 5 ? 69 : 74,
    performanceControls: ["A", "B"],
    notes: [
      {string: 4, fret: sourceFret, changes: []},
      {string: 5, fret: sourceFret, changes: ["A"]},
      {string: 6, fret: sourceFret, changes: ["B"]}
    ]
  };
  const fullGripTarget = {
    resolvedPitch: "G4", pitchValue: 67, performanceControls: [],
    notes: [{string: 4, fret: 3, changes: []}, {string: 5, fret: 3, changes: []}, {string: 6, fret: 3, changes: []}]
  };
  const fullGripTransition = {
    kind: "bar_slide", scope: "full_grip", fromFret: sourceFret, toFret: 3,
    controlsBefore: ["A", "B"], controlsAfter: [],
    fromStrings: [4, 5, 6], toStrings: [4, 5, 6], sustainedStrings: [4, 5, 6], repickedStrings: [], releasedStrings: [],
    voiceActions: [
      {string: 4, action: "bar_slide"},
      {string: 5, action: "bar_slide"},
      {string: 6, action: "bar_slide"}
    ]
  };
  const choreography = studio.transitionChoreography(fullGripTransition, fullGripSource, fullGripTarget);
  assert.match(choreography, new RegExp(`Attack the full grip: strings 4, 5 & 6 at fret ${sourceFret} with A\\+B`));
  assert.match(choreography, /keep all three strings ringing/);
  assert.match(choreography, new RegExp(`slide the grip from fret ${sourceFret} to fret 3`));
  assert.match(choreography, /release A\+B at the arrival/);
  assert.doesNotMatch(choreography, /repick/i);
  assert.deepEqual(studio.transitionSustainedStrings(fullGripTransition), [4, 5, 6]);
  assert.deepEqual(studio.transitionScoreVoices(fullGripTransition, fullGripSource, fullGripTarget).map((voice) => voice.string), [4, 5, 6]);
  assert.deepEqual(studio.transitionPlaybackPlan(fullGripSource, fullGripTarget, fullGripTransition).map((voice) => voice.action), ["glide", "glide", "glide"]);
  assert.deepEqual(studio.transitionPlaybackPlan(fullGripTarget, null, null, fullGripTransition).map((voice) => voice.action), ["continue", "continue", "continue"]);
}
assert.equal(studio.transitionControlAnnotation({kind: "bar_slide", controlsBefore: ["A", "B"], controlsAfter: []}), "release A+B");
assert.deepEqual(studio.gripRationale(transitionTarget), {
  reason: "Keeps the melody in the open G pocket.", pocket: "open-major", grip: "4-5-6", chord: "G"
});
const pedalTransition = {
  kind: "pedal_glide", controlsBefore: [], controlsAfter: ["A"], sustainedStrings: [5],
  voiceActions: [{string: 5, action: "pedal_glide"}]
};
assert.equal(studio.transitionControlAnnotation(pedalTransition), "press A");
assert.deepEqual(studio.transitionScoreVoices(pedalTransition, {
  notes: [{string: 5, fret: 3, changes: []}]
}, {
  notes: [{string: 5, fret: 3, changes: ["A"]}]
}), []);
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
assert.equal(studio.parseAudioTimecode("1:32.5"), 92.5);
assert.equal(studio.parseAudioTimecode("92.5"), 92.5);
assert.equal(studio.parseAudioTimecode("1:72"), null);
assert.equal(studio.formatAudioTimecode(92.5), "1:32.5");
assert.deepEqual(studio.audioWindowBounds(240, "1:32", 15), {start: 92, end: 107, duration: 15});
assert.deepEqual(studio.audioWindowBounds(100, "1:35", 15), {start: 95, end: 100, duration: 5});
assert.equal(studio.audioWindowBounds(100, "2:00", 15), null);
assert.equal(studio.quantizeTranscriptionBeats(0.5, 120), 1);
const audioSamples = [];
for (let index = 0; index < 10; index += 1) audioSamples.push({time: index * 0.05, midiFloat: 60.04 + (index % 2 ? 0.02 : -0.02)});
for (let index = 0; index < 10; index += 1) audioSamples.push({time: 1 + index * 0.05, midiFloat: 61.97 + (index % 2 ? 0.02 : -0.02)});
const transcription = studio.transcribePitchSamples(audioSamples, {bpm: 120});
assert.deepEqual(transcription.events.map((event) => event.rest ? ["rest", event.durationBeats] : [event.pitch, event.durationBeats]), [["C4", 1], ["rest", 1], ["D4", 1]]);
assert.equal(transcription.confidenceLabel, "medium");
assert.match(transcription.warnings[0], /confirm every note/i);
const transcriptionDraft = studio.createAudioTranscriptionDraft(audioSamples, {bpm: 120, key: "G", sourceType: "audio_file", title: "Test melody", sourceStartSeconds: 92, sourceEndSeconds: 107});
assert.equal(transcriptionDraft.schemaVersion, "score_draft_v1");
assert.equal(transcriptionDraft.source.retained, false);
assert.equal(transcriptionDraft.review.status, "needs_review");
assert.equal(transcriptionDraft.transcription.audioRetained, false);
assert.equal(transcriptionDraft.transcription.sourceStartSeconds, 92);
assert.equal(transcriptionDraft.score.melody[0].sourceStartSeconds, 92);
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

assert.deepEqual(score.scoreSystemLayout(16, 800), {width: 784, columns: 4, systems: 4, systemHeight: 190, height: 784});
assert.deepEqual(score.scoreSystemLayout(33, 360), {width: 344, columns: 2, systems: 17, systemHeight: 190, height: 3254});

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
const octaveUp = score.transposeDraft(draft, 12);
assert.deepEqual(octaveUp.score.melody.map((event) => event.pitch), ["D5", "G5", "B5"]);
assert.equal("pitches" in octaveUp.score.melody[0], false);
const chordEventDraft = score.reflowDraft({...draft, score: {...draft.score, melody: [{pitchValue: 67, pitches: [59, 67], durationBeats: 1}]}});
assert.deepEqual(chordEventDraft.score.melody[0].pitches, [59, 67]);
assert.deepEqual(score.transposeDraft(chordEventDraft, 12).score.melody[0].pitches, [71, 79]);
const reviewed = score.reflowDraft({...draft, score: {...draft.score, sections: [{label: "Phrase 1", startMeasure: 5, endMeasure: 8}], melody: [{pitchValue: 67, pitch: "G4", measure: 5, beat: 2, durationBeats: 1}]}});
assert.deepEqual(reviewed.score.melody.map((event) => [event.measure, event.beat]), [[5, 2]]);
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
    assert 'data-studio-start="catalog"' in html
    assert 'data-studio-start="import"' in html
    assert 'data-studio-start="microphone"' in html
    assert html.count("data-studio-start=") == 5
    assert "Add a melody" in html
    assert "Type or tap notes" in html
    assert "Import music" in html
    assert "Record or upload audio" in html
    start_options = re.search(r'id="studio-start-options".*?</div>', html, re.DOTALL).group(0)
    assert start_options.index('data-studio-start="catalog"') < start_options.index('data-studio-start="phrase"')
    assert start_options.index('data-studio-start="phrase"') < start_options.index('data-studio-start="microphone"')
    assert 'data-studio-start="phrase" data-default-label="Type or tap notes" aria-pressed="true"' in start_options
    assert 'id="studio-open-score"' not in html
    assert 'id="studio-add-recording"' in html
    assert 'id="studio-try-example"' not in html
    assert "Choose the easiest way to get the notes in." not in html
    assert 'data-source-treatment="artist_solo_lesson"' in html
    assert 'data-source-treatment="song_arrangement_lesson"' in html
    assert "Faithful solo passage" in html
    assert "Playable E9 arrangement" in html
    assert 'id="studio-material-fields" hidden' in html
    assert "A link identifies the source; Melody Studio does not automatically transcribe it." in html
    assert 'id="studio-presets" aria-label="Practice phrase presets" hidden' in html
    assert 'id="studio-palette"' in html
    assert 'id="studio-sequence"' in html
    assert 'data-preset="1-2-3-5"' in html
    assert 'id="studio-fretboard"' in html
    assert 'id="studio-octave-guide"' in html
    assert 'id="studio-octave-toggle" aria-pressed="false"' in html
    assert 'id="studio-octave-guide" aria-label="Scientific octave color guide" hidden' in html
    assert 'id="studio-string-label-toggle" aria-pressed="false"' in html
    assert 'id="studio-note-label-toggle" aria-pressed="true"' in html
    assert 'id="studio-octave-map-controls" hidden' in html
    assert 'aria-label="Octave 4 — C4 through B4"' in html
    assert 'data-scientific-octave="2"] { --octave-color: #b8a3ff;' in html
    assert 'data-scientific-octave="4"] { --octave-color: #58d6bd;' in html
    assert 'data-scientific-octave="6"] { --octave-color: #ff927d;' in html
    assert ".octave-map-controls { min-width: 0; display: flex;" in html
    assert ".register-stepper { grid-template-columns: 1fr; }" in html
    assert "overflow-x: auto" in html
    assert 'id="studio-register-value"' in html
    assert 'aria-label="Lower selected note one octave"' in html
    assert 'aria-label="Raise selected note one octave"' in html
    assert '>Lower octave</button>' in html
    assert '>Automatic</button>' in html
    assert '>Raise octave</button>' in html
    assert 'id="studio-current-note"' not in html
    assert 'id="studio-note-progress"' not in html
    assert 'class="note-navigator-row"' in html
    assert 'aria-label="Previous note">←</button>' in html
    assert 'aria-label="Next note">→</button>' in html
    assert '<span class="octave-toggle-mark" aria-hidden="true">✓</span>Octave colors</button>' in html
    assert '<span class="octave-toggle-mark" aria-hidden="true">✓</span>String labels</button>' in html
    assert '<span class="octave-toggle-mark" aria-hidden="true">✓</span>Note labels</button>' in html
    assert 'id="studio-contour"' in html
    assert 'id="studio-route-tabs"' in html
    assert html.index('id="studio-fretboard"') < html.index('id="studio-arrangement-choices"') < html.index('id="studio-tab"')
    assert 'id="studio-note-editor" hidden' in html
    assert 'id="studio-octave-down"' in html
    assert 'id="studio-octave-auto"' in html
    assert 'id="studio-octave-up"' in html
    assert 'id="studio-more-routes"' not in html
    assert 'id="studio-result-meta"' not in html
    assert "Practice the lesson" not in html
    assert 'id="studio-change-task"' not in html
    assert "activateRoute" in script
    assert "const selectedRoute = preferredStudioRoute(exercise);" in script
    assert "hideFilterControls: true" in script
    assert "hidePositionTools: true" in script
    assert "hideLegend: true" in script
    assert "Select a note below to change its octave" in html
    assert "Change the register for this note only" in html
    assert "state.selectedPhraseIndex" in script
    assert html.count("?v=module-boundaries-20260713") == 2
    assert html.count("?v=account-copedents-20260714-1") == 3
    assert 'elements.sectionNavigation.hidden = needsSource || Number(section.total || 0) <= 1;' in script
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
    assert "elements.routeTabs.appendChild(button)" in script
    assert "advancedRoutes" not in script
    assert "moreRoutes" not in script
    assert ".route-tabs { max-width: 100%; display: flex; flex-wrap: nowrap;" in html
    assert "Note ${state.activeEventIndex + 1} of ${events.length}" in script
    assert "card.dataset.scientificOctave" in script
    assert 'card.setAttribute("role", "status")' in script
    assert "readableEventPosition(event)" in script
    assert 'id="studio-practice-chord-option" hidden' in html
    assert "Play chord backing" in html
    assert "Hear chords" not in html
    assert "The notes match the structured input; fret and string placement is deterministic" not in html
    assert 'id="studio-explanation"' not in html
    assert "elements.octaveGuide.hidden" in script
    assert "updateOctaveMapVisibility" in script
    assert "showScientificOctaveOverlay: true" in script
    assert "scientificOctavesByString" in script
    assert "melodyRequest: buildMelodyRequest(state)" in script
    assert "copedentContext: global.STEEL_RAG_COPEDENTS.requestContext()" in script
    assert "clearMaterial();" in script
    assert "sectionNumber" in script
    assert "[object Object]" not in html
    assert 'id="studio-score-canvas"' in html
    assert 'id="studio-score-setup"' in html
    assert 'id="studio-selected-note-details"' in html
    assert 'id="studio-score-tools"' in html
    assert 'id="studio-score-download"' in html
    assert 'id="studio-import-file"' in html
    assert 'id="studio-microphone-start"' in html
    assert 'id="studio-audio-file"' in html
    assert 'id="studio-audio-analyze"' in html
    assert 'id="studio-audio-preview"' in html
    assert 'id="studio-audio-start"' in html
    assert 'id="studio-audio-length"' in html
    assert 'id="studio-audio-use-playhead"' in html
    assert 'id="studio-audio-file-controls" hidden' in html
    assert 'id="studio-audio-options"' in html
    assert 'id="studio-transcription-tempo"' in html
    assert 'id="studio-score-confidence"' in html
    assert 'id="studio-score-selection" hidden' in html
    assert 'id="studio-score-selection-summary"' in html
    assert 'id="studio-score-delete-selected"' in html
    assert 'id="studio-score-previous-note"' in html
    assert 'id="studio-score-next-note"' in html
    assert 'id="studio-score-octave-down"' in html
    assert 'id="studio-score-octave-up"' in html
    assert 'All notes down 1 semitone' in html
    assert 'All notes up 1 octave' in html
    assert '["Delete", "Backspace"].includes(event.key)' in script
    assert 'removeSelectedScoreEvent();' in script
    assert 'transposeWholeScore(12, "Moved every note up one octave.")' in script
    assert 'id="studio-score-arrange-status" role="status"' in html
    assert "audio is decoded in this browser" in html
    assert "Longer files are fine" in html
    assert "elements.scoreArrange.disabled = !draft.score.melody.some((item) => !item.rest) || unsupportedKey;" in script
    assert 'statusElement: elements.scoreArrangeStatus' in script
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
    assert 'id="studio-practice-loop-panel" hidden' in html
    assert '>Loop options</summary>' in html
    assert 'id="studio-print-tab"' in html
    assert '>Print</button>' in html
    assert html.index('id="studio-tab"') < html.index('id="studio-print-tab"')
    assert html.index('data-start-over') < html.index('id="studio-print-tab"')
    assert html.index('id="studio-fretboard"') < html.index('id="studio-octave-map-controls"') < html.index('id="studio-arrangement-choices"')
    assert 'id="studio-route-reason"' not in html
    assert 'id="studio-edit-top"' in html
    assert 'elements.hero.hidden = true;' in script
    assert 'elements.practiceLoopPanel.hidden = needsSource || (exercise?.events?.length || 0) < 8;' in script
    assert 'id="studio-print-route"' in html
    assert 'id="studio-print-sheet"' in html
    assert 'id="studio-print-title"' in html
    assert 'class="studio-print-brand">Melody Studio · Steel Guitar RAG</p>' in html
    assert 'class="studio-print-footer">www.steelguitarrag.com</footer>' in html
    assert 'id="studio-score-print"' not in html
    assert "Print score" not in html
    assert '@page { size: letter portrait;' in html
    assert 'body > :not(#studio-print-sheet) { display: none !important; }' in html
    assert 'font: 7.5pt/1.15 ui-monospace' in html
    print_sheet = re.search(r'<aside class="print-only" id="studio-print-sheet".*?</aside>', html, re.DOTALL).group(0)
    assert "Edit melody" not in print_sheet
    assert "Octave colors" not in print_sheet
    assert "String labels" not in print_sheet
    assert "Note labels" not in print_sheet
    assert "Open attribution source" not in print_sheet
    assert "Complete E9 lesson" not in print_sheet
    assert 'id="studio-result-score-stage" hidden' in html
    assert 'id="studio-score-lyric-cue" aria-live="polite" hidden' in html
    assert 'scoreSystemLayout' in Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert 'elements.scoreLyricText.textContent = activeSection?.label || "";' in script
    assert '#studio-whole-song-tab { display: block !important;' in html
    assert 'id="studio-section-navigation"' in html
    assert 'id="studio-section-previous"' in html
    assert 'id="studio-section-next"' in html
    assert 'id="studio-whole-song-tab-code"' in html
    assert 'state.scoreDraft?.score?.sections' in script
    assert 'async function printWholeSong()' in script
    assert 'elements.printRoute.textContent = `E9 tablature · ${routeButtonLabel(route)} · Arranged for ${route.arrangedFor || exercise.arrangedFor || "E9"}`;' in script
    assert "savedE9TargetCopedent" in script
    assert "Arranged for ${arrangedFor}" in script
    assert 'elements.printTitle.textContent = printableLessonTitle(exercise);' in script
    assert 'const sectionLabel = total > 1 ?' in script
    assert 'elements.printTab.addEventListener("click", printWholeSong);' in script
    assert "addKeySignature" in Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert "generateBeams" in Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert "togglePractice" in script
    assert "schedulePitch" in script
    assert "glideToPitch" in script
    assert 'id="studio-transition-key" hidden' in html
    assert '<code>~~~~~</code> audible slide or control glide' in html
    assert '<code>-----</code> held voice' in html
    assert 'id="studio-grip-rationale" hidden' in html
    assert '>Why this grip?</summary>' in html
    assert 'id="studio-grip-reason"' in html
    assert 'id="studio-grip-facts"' in html
    assert 'activeRoute?.harmonyType === "mixed_arrangement" ? gripRationale(event) : null' in script
    assert 'elements.gripRationale.open = false;' in script
    assert 'transitionChoreography(transition, previousEvent, event)' in script
    assert 'transitionSustainedStrings(transition)' in script
    assert 'data-highlight-dot][data-highlight-string]' in script
    assert 'route?.tab?.printTabText' in script
    assert "route.transitions" in script
    assert "transitionFromPrevious" in Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in script
    assert "scoreVoices: transitionScoreVoices" in script
    score_script = Path("ui/melody-score.js").read_text(encoding="utf-8")
    assert 'data-transition-string' in score_script
    assert 'score-control-annotation' in score_script
    assert 'transitionScoreVoices(target.event)' in score_script
    assert "session-only" in html.lower()
    assert 'id="studio-replace-confirmation" role="alert" hidden' in html
    assert 'id="studio-confirm-replace"' in html
    assert 'id="studio-keep-melody"' in html
    assert "state.pendingReplacement = startingPoint;" in script
    assert 'state.workflowPhase = "review"' in script
    assert 'state.workflowPhase = "result"' in script
    assert 'elements.audioFileControls.hidden = !state.sourceAudioUrl;' in script
    assert 'if (catalogChoice) catalogChoice.hidden = !catalogEnabled;' in script
    assert 'id="studio-catalog-search"' in html
    assert 'id="studio-catalog-difficulty"' in html
    assert 'id="studio-catalog-meter"' in html
    assert 'id="studio-catalog-feel"' in html
    assert '<strong>Browse songbook</strong>' in html
    assert 'session?.features?.melodyCatalog' in script
    assert 'sourceType: "catalog"' in script
    assert 'Source links identify the teaching version; they are not automatically transcribed.' in script


def test_melody_workbench_uses_explorer_background_without_turnaround_branding() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")

    assert "The Turnaround" not in html
    assert "steel-guitar-rag-landing-fallback-alpha.png" not in html
    assert "radial-gradient(circle at 52% 0%, rgba(221, 139, 45, 0.28), transparent 35%)" in html
    assert "linear-gradient(180deg, rgba(13, 10, 7, 0.96), #050403 72%)" in html
    assert 'aria-label="Back to Steel Guitar RAG home"' in html
    assert '<nav class="studio-nav" aria-label="Page navigation">' in html
    assert '<span>Home</span>' in html
    assert '<span>Go Backstage</span>' in html
    assert '<span>Explore</span>' not in html
    assert '<span>Arrange</span>' not in html
    assert '<span>Learn</span>' not in html
    assert html.count('<svg viewBox="0 0 24 24" aria-hidden="true">') == 2
    assert ".studio-nav svg { width: 18px; height: 18px;" in html
    assert 'font-family: "Gill Sans", "Gill Sans MT", "Avenir Next"' in html
    assert "font-weight: 600;" in html
    assert ".studio-nav a { min-height: 44px; padding: 0 11px; font-size: 12px; }" in html


def test_melody_unavailable_state_explains_that_mobile_is_supported() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")
    script = Path("ui/melody-workbench.js").read_text(encoding="utf-8")

    assert 'id="studio-unavailable-title"' in html
    assert 'id="studio-unavailable-copy"' in html
    assert "This is not a mobile limitation" in html
    assert "supports phones, tablets, and desktop browsers" in html
    assert 'elements.unavailableTitle.textContent = "Melody Studio is temporarily unavailable.";' in script
    assert "This preview did not enable Melody Studio" in script
    assert 'elements.unavailableTitle.textContent = "Melody Studio could not verify access.";' in script
    assert "The availability check did not complete" in script
