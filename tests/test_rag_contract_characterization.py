from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from steel_guitar_rag.answer_tab_examples import static_fretboard_payload_for_question
from steel_guitar_rag.e9_copedents import get_e9_copedent_profile
from steel_guitar_rag.song_practice import arrange_song_practice
from steel_guitar_rag.tab_engine import TabEvent, TabNote


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "platform_rag_contract_v1.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def position_projection(position: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": position["id"],
        "fret": position["fret"],
        "strings": position["strings"],
        "grip": position["grip"],
        "controls": position["controls"],
        "validation": position["validation"],
        "notes": [
            {
                "string": note["string"],
                "fret": note["fret"],
                "changes": note["changes"],
                "pitchLabel": note["pitchLabel"],
            }
            for note in position["notes"]
        ],
    }


def test_rag_source_files_match_the_integration_base_snapshot() -> None:
    source = load_fixture()["source"]

    assert len(source["integrationBaseCommit"]) == 40
    for relative_path, expected_hash in source["files"].items():
        assert sha256(ROOT / relative_path) == expected_hash, relative_path


def test_song_practice_plan_matches_the_characterized_projection() -> None:
    fixture = load_fixture()
    plan = arrange_song_practice(
        fixture["syntheticInput"],
        copedent_profile=get_e9_copedent_profile(),
        copedent_revision=1,
    )
    observed = fixture["observedShape"]

    assert sorted(plan) == observed["planFields"]
    assert sorted(plan["events"][0]) == observed["eventFields"]
    assert sorted(plan["events"][0]["position"]) == observed["positionFields"]
    assert sorted(plan["events"][0]["position"]["notes"][0]) == observed["positionNoteFields"]

    projection = {
        "schemaVersion": plan["schemaVersion"],
        "level": plan["level"],
        "timelineHash": plan["timelineHash"],
        "targetCopedentId": plan["targetCopedentId"],
        "targetCopedentRevision": plan["targetCopedentRevision"],
        "route": {
            "coherentAcrossChart": plan["route"]["coherentAcrossChart"],
            "preference": plan["route"]["preference"],
            "homeFret": plan["route"]["homeFret"],
        },
        "provenance": plan["provenance"],
        "events": [
            {
                "id": event["id"],
                "measureId": event["measureId"],
                "sectionId": event["sectionId"],
                "chord": event["chord"],
                "startMs": event["startMs"],
                "endMs": event["endMs"],
                "role": event["role"],
                "status": event["status"],
                "position": position_projection(event["position"]),
            }
            for event in plan["events"]
        ],
    }
    assert projection == fixture["expectedPlanProjection"]


def test_tab_event_matches_the_characterized_projection() -> None:
    fixture = load_fixture()
    payload = TabEvent(
        notes=(TabNote(5, 3, ("A",), "slide-in"),),
        chord="G",
    ).to_dict()

    assert sorted(payload) == fixture["observedShape"]["tabEventFields"]
    assert sorted(payload["notes"][0]) == fixture["observedShape"]["tabNoteFields"]
    assert payload == fixture["expectedTabProjection"]


def test_static_fretboard_matches_the_characterized_projection() -> None:
    fixture = load_fixture()
    payload = static_fretboard_payload_for_question("Show me a G major grip.")

    assert payload is not None
    position = payload["positions"][0]
    projection = {
        "type": payload["type"],
        "tuning": payload["tuning"],
        "key": payload["key"],
        "copedent": {
            "id": payload["copedent"]["id"],
            "status": payload["copedent"]["status"],
        },
        "strings": {"count": payload["strings"]["count"]},
        "position": {
            "id": position["id"],
            "fret": position["fret"],
            "strings": position["strings"],
            "grip": position["grip"],
            "pedals": position["pedals"],
            "levers": position["levers"],
            "notes": position["notes"],
            "intervals": position["intervals"],
            "positionKind": position["positionKind"],
            "validationStatus": position["validationStatus"],
        },
    }
    assert projection == fixture["expectedFretboardProjection"]


def test_browser_playback_selection_and_loop_ranges_match_characterization() -> None:
    script = r"""
const fs = require("fs");
const songs = require("./ui/song-projects.js");
const practice = require("./ui/practice-tools.js");
const fixture = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
const events = fixture.syntheticInput.events;
const playbackSelectionCases = fixture.playbackSelectionCases.map((item) => {
  const state = songs.activeTimelineState(events, item.timeMs);
  return {
    timeMs: item.timeMs,
    currentIndex: state.currentIndex,
    currentId: state.current?.id || null,
    nextId: state.next?.id || null,
  };
});
const track = {barStartsMs: [0, 1000, 2000], durationMs: 3000};
const loopCases = fixture.loopCases.map((item) => ({
  startBar: item.startBar,
  endBar: item.endBar,
  expected: practice.barsToLoopRange(track, item.startBar, item.endBar),
}));
process.stdout.write(JSON.stringify({playbackSelectionCases, loopCases}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(FIXTURE_PATH)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(completed.stdout)
    fixture = load_fixture()

    assert actual["playbackSelectionCases"] == fixture["playbackSelectionCases"]
    assert actual["loopCases"] == fixture["loopCases"]
