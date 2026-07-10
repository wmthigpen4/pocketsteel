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

const original = studio.createInitialState("original_exercise");
Object.assign(original, { tokens: ["1", "3", "5"], artist: "Stale Artist", sourceUrl: "https://example.test/stale" });
const originalPayload = studio.buildMelodyRequest(original);
assert.equal("material" in originalPayload, false);
assert.deepEqual(originalPayload.melody, ["1", "3", "5"]);
"""
    )


def test_melody_workbench_has_guided_tasks_feature_state_and_fretboard_first_result() -> None:
    html = Path("ui/melody-workbench.html").read_text(encoding="utf-8")
    script = Path("ui/melody-workbench.js").read_text(encoding="utf-8")

    assert "Turn a phrase into an E9 lesson." in html
    assert html.index('data-studio-task="artist_solo_lesson"') < html.index('data-studio-task="original_exercise"')
    assert 'id="studio-material-fields" hidden' in html
    assert 'id="studio-palette"' in html
    assert 'id="studio-sequence"' in html
    assert 'data-preset="1-2-3-5"' in html
    assert 'id="studio-fretboard"' in html
    assert html.index('id="studio-fretboard"') < html.index('id="studio-tab"')
    assert 'id="studio-continue"' in html
    assert "does not listen to or extract notes from the link yet" in html
    assert "selectPedalSteelFretboardPosition" in script
    assert "requestPayload: { melodyRequest: buildMelodyRequest(state) }" in script
    assert "clearMaterial();" in script
    assert "sectionNumber" in script
    assert "[object Object]" not in html
