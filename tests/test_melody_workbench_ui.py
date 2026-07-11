from __future__ import annotations

import subprocess
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
  [{ id: "event-1", strings: [5, 6] }],
  [{ renderablePositionId: "event-1", notes: [{ string: 5, fret: 3, changes: [] }, { string: 6, fret: 3, changes: [] }] }]
);
assert.deepEqual(octavePositions[0].scientificOctavesByString, { 5: 4, 6: 3 });
const fretboardOptions = studio.melodyFretboardOptions(
  { maxFret: 24, stringCount: 10, tuningLabels: [], positions: octavePositions, highlights: [], legend: [], query: {} },
  []
);
assert.equal(fretboardOptions.showScientificOctaveOverlay, true);
assert.equal(fretboardOptions.hidePositionTools, true);
assert.equal(studio.createInitialState().showOctaveMap, true);
"""
    )


def test_melody_workbench_has_direct_phrase_entry_and_compact_note_navigator() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")
    script = Path("ui/melody-workbench.js").read_text(encoding="utf-8")

    assert "Turn a phrase into an E9 lesson." in html
    assert "Step 1 of 4" not in html
    assert 'data-studio-start="phrase"' in html
    assert 'data-studio-start="recording"' in html
    assert 'data-studio-start="exercise"' in html
    assert html.count("data-studio-start=") == 3
    assert "Enter my phrase" in html
    assert "A song or recording" in html
    assert "Give me an exercise" in html
    assert 'data-source-treatment="artist_solo_lesson"' in html
    assert 'data-source-treatment="song_arrangement_lesson"' in html
    assert "Faithful solo passage" in html
    assert "Playable E9 arrangement" in html
    assert 'id="studio-material-fields" hidden' in html
    assert 'id="studio-presets" aria-label="Practice phrase presets" hidden' in html
    assert 'id="studio-palette"' in html
    assert 'id="studio-sequence"' in html
    assert 'data-preset="1-2-3-5"' in html
    assert 'id="studio-fretboard"' in html
    assert 'id="studio-octave-guide"' in html
    assert 'id="studio-octave-toggle" aria-pressed="true"' in html
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
    assert html.count("?v=melody-route-row-20260711") == 3
    assert html.index('id="studio-fretboard"') < html.index('id="studio-tab"')
    assert 'id="studio-continue"' in html
    assert "does not listen to or extract notes from the link yet" in html
    assert "selectPedalSteelFretboardPosition" in script
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


def test_melody_workbench_uses_explorer_background_without_turnaround_branding() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")

    assert "The Turnaround" not in html
    assert "steel-guitar-rag-landing-fallback-alpha.png" not in html
    assert "radial-gradient(circle at 52% 0%, rgba(221, 139, 45, 0.28), transparent 35%)" in html
    assert "linear-gradient(180deg, rgba(13, 10, 7, 0.96), #050403 72%)" in html
