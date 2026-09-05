from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from packages.song_model import (
    ChordBody,
    SelectionState,
    SteelBody,
    project_rag_song_practice,
    select_event,
    timeline_to_dict,
)
from packages.steel_theory import project_rag_copedent, standard_emmons_e9_basic
from steel_guitar_rag.e9_copedents import get_e9_copedent_profile
from steel_guitar_rag.song_practice import arrange_song_practice


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "platform_rag_contract_v1.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def build_plan() -> dict[str, Any]:
    fixture = load_fixture()
    return arrange_song_practice(
        fixture["syntheticInput"],
        copedent_profile=get_e9_copedent_profile(),
        copedent_revision=1,
    )


def test_rag_plan_projects_without_mutating_the_source_or_losing_product_metadata() -> None:
    plan = build_plan()
    original = deepcopy(plan)
    projection = project_rag_song_practice(plan, copedent=standard_emmons_e9_basic())

    assert projection.errors == ()
    assert projection.timeline is not None
    assert plan == original
    assert set(projection.product_metadata) == {
        "schemaVersion",
        "level",
        "targetCopedentLabel",
        "route",
        "provenance",
        "warnings",
        "events",
    }
    first_event = projection.product_metadata["events"][0]
    assert set(first_event) == {"id", "status", "alternatives", "position"}
    assert first_event["alternatives"] == plan["events"][0]["alternatives"]
    assert first_event["position"]["instruction"] == plan["events"][0]["position"]["instruction"]
    assert first_event["position"]["notes"][0] == {
        "string": 4,
        "changeLabels": [],
        "note": "G",
    }
    retained_paths = {
        item.path for item in projection.warnings if item.code == "product_field_retained"
    }
    assert {
        "$.schemaVersion",
        "$.level",
        "$.route",
        "$.provenance",
        "$.targetCopedentLabel",
        "$.warnings",
        "$.events[0].status",
        "$.events[0].alternatives",
        "$.events[0].position.instruction",
        "$.events[0].position.notes[0].note",
    } <= retained_paths


def test_rag_projection_has_deterministic_clocks_structures_events_and_positions() -> None:
    projection = project_rag_song_practice(build_plan(), copedent=standard_emmons_e9_basic())
    timeline = projection.timeline

    assert projection.errors == ()
    assert timeline is not None
    fixture = load_fixture()
    expected = fixture["expectedPlanProjection"]
    assert timeline.id == f"rag:song-practice:{expected['timelineHash']}"
    assert [(clock.id, clock.kind, clock.duration_ms) for clock in timeline.clocks] == [
        ("rag:media", "media", 2000)
    ]
    assert [(item.id, item.kind, item.start_ms, item.end_ms) for item in timeline.structures] == [
        ("rag:section:section-a", "section", 0, 2000),
        ("rag:measure:measure-1", "measure", 0, 2000),
    ]
    assert [event.id for event in timeline.events] == [
        "rag:chord:event-a",
        "rag:steel:event-a",
        "rag:chord:event-b",
        "rag:steel:event-b",
    ]
    assert [position.id for position in timeline.positions] == [
        "rag:position:song-position-1",
        "rag:position:song-position-2",
    ]

    first_chord, first_steel, second_chord, second_steel = timeline.events
    assert isinstance(first_chord.body, ChordBody)
    assert isinstance(first_steel.body, SteelBody)
    assert first_chord.body.symbol == "G"
    assert first_steel.body.chord_event_id == first_chord.id
    assert first_steel.body.position_id == first_chord.body.position_id
    assert isinstance(second_chord.body, ChordBody)
    assert isinstance(second_steel.body, SteelBody)
    assert second_chord.body.symbol == "C"
    assert [(note.string, note.fret, note.controls, note.label) for note in second_steel.body.notes] == [
        (4, 3, (), "G4"),
        (5, 3, ("A",), "E4"),
        (6, 3, ("B",), "C4"),
    ]
    assert all(note.articulations == () and note.transitions == () for note in second_steel.body.notes)
    assert timeline_to_dict(timeline)["schemaVersion"] == "steel_platform_timeline_v1"


def test_shared_selection_matches_rag_until_the_documented_post_roll_difference() -> None:
    fixture = load_fixture()
    projection = project_rag_song_practice(build_plan(), copedent=standard_emmons_e9_basic())
    timeline = projection.timeline

    assert timeline is not None
    expected = (
        SelectionState("pre-roll", None, "rag:steel:event-a"),
        SelectionState("active", "rag:steel:event-a", "rag:steel:event-b"),
        SelectionState("active", "rag:steel:event-a", "rag:steel:event-b"),
        SelectionState("active", "rag:steel:event-b", None),
        SelectionState("post-roll", None, None),
    )
    actual = tuple(
        select_event(
            timeline,
            clock_id="rag:media",
            track_id="steel-main",
            time_ms=item["timeMs"],
        )
        for item in fixture["playbackSelectionCases"]
    )
    assert actual == expected
    assert fixture["playbackSelectionCases"][-1]["currentId"] == "event-b"
    assert {item.code for item in projection.warnings} >= {
        "clock_duration_derived",
        "post_roll_selection_differs",
        "structure_range_derived",
    }


def test_profile_pitch_and_controls_must_match_exactly() -> None:
    profile_mismatch = build_plan()
    profile_mismatch["targetCopedentRevision"] = 2
    projection = project_rag_song_practice(
        profile_mismatch,
        copedent=standard_emmons_e9_basic(),
    )
    assert [item.code for item in projection.errors] == ["copedent_identity_mismatch"]

    bad_pitch = build_plan()
    bad_pitch["events"][0]["position"]["notes"][0]["pitch"] = 68
    projection = project_rag_song_practice(bad_pitch, copedent=standard_emmons_e9_basic())
    assert [item.code for item in projection.errors] == ["pitch_mismatch"]

    unknown_control = build_plan()
    unknown_control["events"][0]["position"]["controls"] = ["X"]
    unknown_control["events"][0]["position"]["notes"][0]["changes"] = ["X"]
    projection = project_rag_song_practice(
        unknown_control,
        copedent=standard_emmons_e9_basic(),
    )
    assert [item.code for item in projection.errors] == ["invalid_mechanical_state"]


def test_unresolved_events_and_same_track_overlap_fail_closed() -> None:
    unresolved = build_plan()
    unresolved["events"][0]["status"] = "manual_position_needed"
    unresolved["events"][0]["position"] = None
    projection = project_rag_song_practice(unresolved, copedent=standard_emmons_e9_basic())
    assert [item.code for item in projection.errors] == ["event_not_projectable"]

    overlap = build_plan()
    overlap["events"][1]["startMs"] = 500
    projection = project_rag_song_practice(overlap, copedent=standard_emmons_e9_basic())
    assert projection.timeline is None
    assert {item.code for item in projection.errors} == {"shared_event-overlap"}


def test_new_rag_only_fields_are_preserved_and_reported_without_entering_timeline() -> None:
    plan = build_plan()
    plan["newDisplayThing"] = {"mode": "future"}
    plan["events"][0]["newCue"] = "future"
    plan["events"][0]["position"]["newPalette"] = ["future"]
    plan["events"][0]["position"]["notes"][0]["newToken"] = "future"
    projection = project_rag_song_practice(plan, copedent=standard_emmons_e9_basic())

    assert projection.errors == ()
    assert projection.timeline is not None
    assert projection.product_metadata["newDisplayThing"] == {"mode": "future"}
    first_event = projection.product_metadata["events"][0]
    assert first_event["newCue"] == "future"
    assert first_event["position"]["newPalette"] == ["future"]
    assert first_event["position"]["notes"][0]["newToken"] == "future"
    retained_paths = {item.path for item in projection.warnings}
    assert {
        "$.newDisplayThing",
        "$.events[0].newCue",
        "$.events[0].position.newPalette",
        "$.events[0].position.notes[0].newToken",
    } <= retained_paths


def test_live_rag_copedent_projection_is_accepted_without_product_imports_in_adapter() -> None:
    copedent_projection = project_rag_copedent(
        get_e9_copedent_profile().to_dict(include_options=False)
    )
    assert copedent_projection.profile is not None

    projection = project_rag_song_practice(
        build_plan(),
        copedent=copedent_projection.profile,
    )

    assert projection.errors == ()
    adapter_source = (ROOT / "packages" / "song_model" / "rag_adapter.py").read_text(
        encoding="utf-8"
    )
    assert "steel_guitar_rag" not in adapter_source
