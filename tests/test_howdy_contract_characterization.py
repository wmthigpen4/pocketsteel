from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "platform_howdy_contract_v1.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def item_at(items: list[dict[str, Any]], milliseconds: int) -> dict[str, Any]:
    return next(
        (
            item
            for item in items
            if milliseconds >= int(item["startMs"]) and milliseconds < int(item["endMs"])
        ),
        items[-1],
    )


def next_item(items: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any]:
    index = next(index for index, item in enumerate(items) if item["id"] == current["id"])
    return items[min(len(items) - 1, index + 1)]


def test_snapshot_has_immutable_source_and_integration_provenance() -> None:
    fixture = load_fixture()
    source = fixture["source"]
    integration = fixture["integration"]

    assert len(source["commit"]) == 40
    assert len(source["sha256"]) == 64
    assert source["ref"].startswith("preserve/")
    assert len(integration["baseCommit"]) == 40
    assert len(integration["governanceCommit"]) == 40
    assert integration["strategy"] == "selective_contract_port_without_legacy_history_merge"


def test_synthetic_contract_preserves_howdy_event_graph_invariants() -> None:
    data = load_fixture()["syntheticContract"]
    events = data["events"]
    phrases = data["phrases"]
    chords = data["chordTimeline"]
    scopes = data["media"]["scopes"]

    assert data["schemaVersion"] == "lesson_companion_v1"
    assert data["runtimeMode"] == "published_deterministic"
    assert data["modelCallsAllowed"] is False
    assert set(scopes) == {"fullSong", "taughtSolo"}
    assert scopes["fullSong"]["startMs"] == 0
    assert scopes["fullSong"]["endMs"] == data["media"]["durationMs"]
    assert scopes["taughtSolo"]["durationMs"] == scopes["taughtSolo"]["endMs"] - scopes["taughtSolo"]["startMs"]
    assert events[-1]["endMs"] == scopes["taughtSolo"]["durationMs"]

    event_ids = [event["id"] for event in events]
    assert len(event_ids) == len(set(event_ids))
    assert all(int(event["endMs"]) > int(event["startMs"]) for event in events)
    assert all(int(events[index]["startMs"]) >= int(events[index - 1]["endMs"]) for index in range(1, len(events)))

    phrase_ids = {phrase["id"] for phrase in phrases}
    chord_ids = {chord["id"] for chord in chords}
    assert all(event["phraseId"] in phrase_ids for event in events)
    assert all(event["chordEventId"] in chord_ids for event in events)
    assert [event_id for phrase in phrases for event_id in phrase["eventIds"]] == event_ids

    for event in events:
        assert event["tabNotes"]
        for note in event["tabNotes"]:
            assert 1 <= int(note["string"]) <= 10
            assert 0 <= int(note["fret"]) <= 24
            assert isinstance(note["controls"], list)

    for chord in chords:
        covered = [event for event in events if event["chordEventId"] == chord["id"]]
        assert covered
        assert int(chord["startMs"]) - 50 <= int(covered[0]["startMs"])
        assert int(covered[-1]["endMs"]) <= int(chord["endMs"]) + 50
        assert chord["tabNotes"]


def test_playback_selection_uses_inclusive_start_exclusive_end_and_saturates_next() -> None:
    fixture = load_fixture()
    events = fixture["syntheticContract"]["events"]
    chords = fixture["syntheticContract"]["chordTimeline"]

    for case in fixture["selectionCases"]:
        current = item_at(events, int(case["relativeMs"]))
        assert current["id"] == case["currentEventId"]
        assert next_item(events, current)["id"] == case["nextEventId"]
        assert item_at(chords, int(case["relativeMs"]))["id"] == case["chordId"]


def test_layer_selects_media_scope_and_maps_relative_to_absolute_time() -> None:
    fixture = load_fixture()
    scopes = fixture["syntheticContract"]["media"]["scopes"]

    for case in fixture["scopeCases"]:
        scope_name = "fullSong" if case["layerId"] == "play-along" else "taughtSolo"
        scope = scopes[scope_name]
        assert scope["id"] == case["scopeId"]
        assert int(scope["startMs"]) + int(case["relativeMs"]) == int(case["absoluteMs"])


def test_preserved_companion_source_matches_snapshot_when_supplied() -> None:
    source_path_value = os.environ.get("HOWDY_COMPANION_SOURCE")
    if not source_path_value:
        return

    fixture = load_fixture()
    observed = fixture["observedShape"]
    source_path = Path(source_path_value)
    source_bytes = source_path.read_bytes()
    data = json.loads(source_bytes)

    assert hashlib.sha256(source_bytes).hexdigest() == fixture["source"]["sha256"]
    assert data["schemaVersion"] == observed["schemaVersion"]
    assert sorted(data) == observed["topLevelFields"]
    assert len(data["events"]) == observed["counts"]["events"]
    assert len(data["phrases"]) == observed["counts"]["phrases"]
    assert len(data["chordTimeline"]) == observed["counts"]["chords"]
    assert sorted(data["events"][0]) == observed["eventFields"]
    assert sorted(data["events"][0]["tabNotes"][0]) == observed["tabNoteFields"]
    assert sorted(data["phrases"][0]) == observed["phraseFields"]
    assert sorted(data["chordTimeline"][0]) == observed["chordFields"]
