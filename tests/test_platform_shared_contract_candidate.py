from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "platform_shared_contract_v1_candidate.json"


def load_candidate() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def midi_label(value: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[value % 12]}{value // 12 - 1}"


def select_event(events: list[dict[str, Any]], time_ms: int) -> dict[str, Any]:
    ordered = sorted(events, key=lambda item: (item["startMs"], item["endMs"], item["id"]))
    if time_ms < ordered[0]["startMs"]:
        return {"phase": "pre-roll", "currentEventId": None, "nextEventId": ordered[0]["id"]}
    if time_ms >= ordered[-1]["endMs"]:
        return {"phase": "post-roll", "currentEventId": None, "nextEventId": None}

    for index, event in enumerate(ordered):
        if event["startMs"] <= time_ms < event["endMs"]:
            next_id = ordered[index + 1]["id"] if index + 1 < len(ordered) else None
            return {"phase": "active", "currentEventId": event["id"], "nextEventId": next_id}
        if time_ms < event["startMs"]:
            return {"phase": "active", "currentEventId": None, "nextEventId": event["id"]}
    raise AssertionError("selection must resolve before the end of the event range")


def test_candidate_has_the_bounded_v1_shape_and_no_product_metadata() -> None:
    candidate = load_candidate()

    assert set(candidate) == {
        "schemaVersion",
        "id",
        "revision",
        "clocks",
        "copedent",
        "positions",
        "structures",
        "events",
    }
    assert candidate["schemaVersion"] == "steel_platform_timeline_v1"
    assert candidate["revision"] > 0

    serialized = json.dumps(candidate)
    for product_only_field in (
        "approvals",
        "artifactSha256",
        "buildSha",
        "contentStatus",
        "modelCallsAllowed",
        "musicalVerified",
        "provenance",
        "release",
        "runtimeMode",
    ):
        assert f'"{product_only_field}"' not in serialized


def test_clock_graph_and_cross_clock_structure_ranges_are_valid() -> None:
    candidate = load_candidate()
    clocks = {clock["id"]: clock for clock in candidate["clocks"]}

    def root_range(clock_id: str, start_ms: int, end_ms: int) -> tuple[str, int, int]:
        seen: set[str] = set()
        while clocks[clock_id]["parentMapping"] is not None:
            assert clock_id not in seen
            seen.add(clock_id)
            mapping = clocks[clock_id]["parentMapping"]
            start_ms += mapping["parentStartMs"]
            end_ms += mapping["parentStartMs"]
            clock_id = mapping["parentClockId"]
        return clock_id, start_ms, end_ms

    assert set(clocks) == {"full-song", "taught-solo"}
    for clock in clocks.values():
        assert clock["durationMs"] > 0
        mapping = clock["parentMapping"]
        if mapping is None:
            assert clock["kind"] == "media"
            continue
        assert clock["kind"] == "window"
        parent = clocks[mapping["parentClockId"]]
        assert mapping["parentStartMs"] + clock["durationMs"] <= parent["durationMs"]

    events = {event["id"]: event for event in candidate["events"]}
    structures = {structure["id"]: structure for structure in candidate["structures"]}
    assert len(events) == len(candidate["events"])
    assert len(structures) == len(candidate["structures"])

    for structure in structures.values():
        structure_range = root_range(
            structure["clockId"], structure["startMs"], structure["endMs"]
        )
        for event_id in structure["eventIds"]:
            event = events[event_id]
            event_range = root_range(event["clockId"], event["startMs"], event["endMs"])
            assert event_range[0] == structure_range[0]
            assert structure_range[1] <= event_range[1] < event_range[2] <= structure_range[2]


def test_event_references_and_mechanical_pitch_state_are_consistent() -> None:
    candidate = load_candidate()
    events = {event["id"]: event for event in candidate["events"]}
    positions = {position["id"]: position for position in candidate["positions"]}
    structures = {structure["id"] for structure in candidate["structures"]}
    snapshot = candidate["copedent"]["snapshot"]
    strings = {item["string"]: item["openPitch"] for item in snapshot["strings"]}
    controls = {
        item["id"]: {change["string"]: change["semitones"] for change in item["changes"]}
        for item in snapshot["controls"]
    }

    assert [item["string"] for item in snapshot["strings"]] == list(range(1, 11))
    assert candidate["copedent"]["snapshotDigest"] == canonical_digest(snapshot)
    assert candidate["events"] == sorted(
        candidate["events"],
        key=lambda item: (
            item["clockId"],
            item["startMs"],
            item["endMs"],
            item["trackId"],
            item["id"],
        ),
    )

    def assert_note_state(note: dict[str, Any]) -> None:
        assert 1 <= note["string"] <= 10
        assert 0 <= note["fret"] <= 24
        assert note["controls"] == sorted(set(note["controls"]))
        midi = strings[note["string"]]["midi"] + note["fret"]
        for control_id in note["controls"]:
            midi += controls[control_id].get(note["string"], 0)
        assert note["pitch"] == {"midi": midi, "label": midi_label(midi)}

    assert len(positions) == len(candidate["positions"])
    for position in positions.values():
        assert position["validity"]["status"] == "valid"
        for note in position["notes"]:
            assert_note_state(note)

    previous_end_by_track: dict[tuple[str, str], int] = {}
    for event in candidate["events"]:
        assert event["clockId"] in {clock["id"] for clock in candidate["clocks"]}
        assert 0 <= event["startMs"] < event["endMs"]
        assert set(event["structureIds"]) <= structures
        track_key = (event["clockId"], event["trackId"])
        assert previous_end_by_track.get(track_key, 0) <= event["startMs"]
        previous_end_by_track[track_key] = event["endMs"]
        if event["kind"] == "chord":
            assert event["body"]["symbol"]
            assert event["body"]["positionId"] in positions
            continue

        assert event["kind"] == "steel"
        chord = events[event["body"]["chordEventId"]]
        assert chord["kind"] == "chord"
        assert chord["clockId"] == event["clockId"]
        assert chord["startMs"] <= event["startMs"] < event["endMs"] <= chord["endMs"]
        assert event["body"]["positionId"] in positions
        assert event["body"]["validity"]["status"] == "valid"

        for note in event["body"]["notes"]:
            assert_note_state(note)


def test_selection_is_nullable_at_boundaries_and_during_gaps() -> None:
    steel_events = [
        event
        for event in load_candidate()["events"]
        if event["clockId"] == "taught-solo" and event["trackId"] == "steel-main"
    ]

    assert select_event(steel_events, -1) == {
        "phase": "pre-roll",
        "currentEventId": None,
        "nextEventId": "steel-a",
    }
    assert select_event(steel_events, 0) == {
        "phase": "active",
        "currentEventId": "steel-a",
        "nextEventId": "steel-b",
    }
    assert select_event(steel_events, 1000) == {
        "phase": "active",
        "currentEventId": "steel-b",
        "nextEventId": None,
    }
    assert select_event(steel_events, 2000) == {
        "phase": "post-roll",
        "currentEventId": None,
        "nextEventId": None,
    }

    gapped = [
        {"id": "first", "startMs": 0, "endMs": 1000},
        {"id": "second", "startMs": 1500, "endMs": 2000},
    ]
    assert select_event(gapped, 1200) == {
        "phase": "active",
        "currentEventId": None,
        "nextEventId": "second",
    }
