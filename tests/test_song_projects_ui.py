from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_node(script: str) -> None:
    result = subprocess.run(["node", "-e", script], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_song_project_chart_sync_privacy_relink_and_api_helpers() -> None:
    run_node(
        r"""
const assert = require("node:assert/strict");
const songs = require("./ui/song-projects.js");

const letters = songs.parseSongChart("[Verse 1] | G | C | G D7 | % | Am x2 | [Chorus :: short cue] | Bb | G/B |", {mode: "letter", key: "G", meter: "4/4"});
assert.deepEqual(letters.errors, []);
assert.equal(letters.sections.length, 2);
assert.equal(letters.sections[1].label, "Chorus");
assert.equal(letters.sections[1].cue, "short cue");
assert.equal(letters.measures.length, 8);
assert.deepEqual(letters.measures[2].resolvedChords, ["G", "D7"]);
assert.deepEqual(letters.measures[2].chordFractions, [0, 0.5]);
assert.equal(letters.measures[2].needsReview, true);
assert.deepEqual(letters.measures[3].resolvedChords, ["G", "D7"]);
assert.deepEqual(letters.measures.slice(4, 6).map((measure) => measure.resolvedChords), [["Am"], ["Am"]]);
assert.equal(letters.measures.at(-1).resolvedChords[0], "G/B");

const nashville = songs.parseSongChart("[A] | 1 | 4 | 5 5/7 | b7 | #4m |", {mode: "nashville", key: "G", meter: "4/4"});
assert.deepEqual(nashville.errors, []);
assert.deepEqual(nashville.measures.map((measure) => measure.resolvedChords), [["G"], ["C"], ["D", "D/F#"], ["F"], ["C#m"]]);
assert.match(songs.parseSongChart("[A] G C", {mode: "letter", key: "G"}).errors[0], /\|/);
assert.match(songs.parseSongChart("[A] | H |", {mode: "letter", key: "G"}).errors[0], /invalid chord/);
assert.equal(songs.normalizeLetterChord("F♯m7"), "F#m7");
assert.equal(songs.normalizeLetterChord("G/B"), "G/B");
assert.deepEqual(songs.automaticBarStarts(4, 10000, 2000), [2000, 4000, 6000, 8000]);
assert.deepEqual(songs.automaticBarStarts(3, 9000), [0, 3000, 6000]);

const project = {
  schemaVersion: songs.SCHEMA_VERSION,
  id: "project-1", name: "Private title", key: "G", meter: "4/4", style: "classic_country",
  source: {type: "local"}, audioRef: {kind: "local", filename: "private.mp3", size: 100, lastModified: 200, durationMs: 4200},
  durationMs: 4200, syncOffsetMs: 100,
  sections: letters.sections, measures: letters.measures.slice(0, 3), barStartsMs: [0, 1000, 2200],
  provenance: {audioRetained: false}
};
project.measures[2].chordFractions = [0, 0.25];
const timed = songs.buildTimedEvents(project);
assert.deepEqual(timed.map((event) => [event.chord, event.startMs, event.endMs]), [
  ["G", 100, 1100], ["C", 1100, 2300], ["G", 2300, 2800], ["D7", 2800, 4300]
]);
assert.equal(songs.activeTimelineState(timed, 1200).current.chord, "C");
assert.equal(songs.activeTimelineState(timed, 50).next.chord, "G");
assert.equal(songs.activeTimelineState(timed, 5000).current.chord, "D7");
assert.equal(songs.activeTimelineState(timed, 1099).current.chord, "G");
assert.equal(songs.activeTimelineState(timed, 1100).current.chord, "C");
assert.equal(songs.activeTimelineState(timed, 1179).current.chord, "C");

const payload = songs.buildArrangePayload(project, {profileId: "day-e9-basic"});
assert.equal(payload.schemaVersion, songs.REQUEST_SCHEMA);
assert.equal(payload.copedentContext.profileId, "day-e9-basic");
assert.equal("name" in payload, false);
assert.equal("source" in payload, false);
assert.equal("audioRef" in payload, false);
assert.equal("sections" in payload, false);
assert.equal(JSON.stringify(payload).includes("Private title"), false);
assert.equal(JSON.stringify(payload).includes("private.mp3"), false);
assert.equal(JSON.stringify(payload).includes("short cue"), false);

const hintedPayload = songs.buildArrangePayload({...project, authoredRoute: [
  {fret: 3, strings: [4, 5, 6], controls: []},
  {fret: 8, strings: [4, 5, 6], controls: []}
]}, {profileId: "emmons-e9-basic"});
assert.deepEqual(hintedPayload.events[0].positionHint, {fret: 3, strings: [4, 5, 6], controls: []});
assert.deepEqual(hintedPayload.events[1].positionHint, {fret: 8, strings: [4, 5, 6], controls: []});

const exported = songs.exportProjectJson({...project, audioUrl: "blob:secret"});
assert.equal(exported.includes("blob:secret"), false);
assert.equal(exported.includes("private.mp3"), true);
assert.equal(exported.includes("audioRetained"), true);
assert.throws(() => songs.exportProjectJson({...project, audioBytes: "secret"}), /cannot be stored/);

const identity = songs.localAudioIdentity({name: "private.mp3", size: 100, lastModified: 200}, 4200.4);
assert.equal(songs.matchesLocalAudioIdentity(project.audioRef, identity), true);
assert.equal(songs.matchesLocalAudioIdentity(project.audioRef, {...identity, size: 101}), false);
assert.equal(songs.matchesLocalAudioIdentity(project.audioRef, {...identity, durationMs: 6000}), false);
assert.equal(songs.migrateProject({...project, schemaVersion: "song_project_v0", barStartsMs: undefined, barTimes: [0, 1000, 2200]}).schemaVersion, songs.SCHEMA_VERSION);
assert.throws(() => songs.migrateProject({...project, schemaVersion: "song_project_v9"}), /Unsupported/);
"""
    )


def test_song_project_controller_contains_local_only_and_practice_controls() -> None:
    source = (REPO_ROOT / "ui" / "song-projects.js").read_text(encoding="utf-8")
    html = (REPO_ROOT / "ui" / "melody-workbench.html").read_text(encoding="utf-8")

    assert "URL.createObjectURL(file)" in source
    assert "URL.revokeObjectURL(objectUrl)" in source
    assert "preservesPitch = true" in source
    assert 'fetch("/api/song-practice/arrange"' in source
    payload_source = source[source.index("function buildArrangePayload"):source.index("function openDatabase")]
    assert "filename" not in payload_source
    assert "audioRef" not in payload_source
    assert "cue" not in payload_source
    assert "What do you want to work on?" in html
    assert html.index('data-studio-start="song"') < html.index('data-studio-start="catalog"')
    assert 'maxlength="80"' in html or "MAX_CUE_LENGTH" in source
    assert 'id="song-loop-enabled"' in html
    assert 'id="song-play-toggle"' in html
    assert 'id="song-player-stage"' in html
    assert 'id="song-edit-sync"' in html
    assert 'id="song-builder-details"' in html
    assert "Your job is simple: play the chord shown on screen." in html
    assert "Edit synchronization (advanced)" in html
    assert "Tap every bar" not in html
    assert source.index("await arrange();") > source.index("async function selectPilot")
    assert 'id="song-skip-back"' in html
    assert 'id="song-skip-forward"' in html
    assert '["INPUT", "TEXTAREA", "SELECT"].includes(doc.activeElement?.tagName)' in source
    assert 'id="song-sync-offset"' in html
    assert 'id="song-fretboard"' in html
    assert "const timeMs = elements.audio.currentTime * 1000;" in source
    assert "elements.audio.currentTime = Math.max(0, bounds.startMs / 1000);" in source
    assert 'elements.currentSection.textContent = current ? (currentSection?.label || "Song") : "Get ready";' in source


def test_answer_client_preserves_song_practice_session_capability() -> None:
    run_node(
        r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = {window: {}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("ui/answer-client.js", "utf8"), sandbox);
const answer = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);
const session = answer.normalizeSessionResponse({
  authenticated: true,
  role: "beta_user",
  authProvider: "local_dev",
  features: {melodyExercise: true, songPractice: true}
});
assert.equal(JSON.stringify(session.features), JSON.stringify({melodyExercise: true, songPractice: true}));
"""
    )
