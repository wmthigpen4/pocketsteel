from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from packages.song_model import (
    SelectionState,
    TimelineValidationError,
    canonical_timeline_json,
    map_clock_range_to_root,
    select_event,
    timeline_digest,
    timeline_from_dict,
    timeline_to_dict,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "tests" / "fixtures" / "platform_shared_contract_v1_candidate.json"


def load_candidate() -> dict[str, Any]:
    return json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))


def issue_codes(exc: TimelineValidationError) -> set[str]:
    return {issue.code for issue in exc.issues}


def test_candidate_round_trips_without_product_metadata_or_aliases() -> None:
    source = load_candidate()
    timeline = timeline_from_dict(source)

    assert timeline_to_dict(timeline) == source
    assert json.loads(canonical_timeline_json(timeline)) == source
    assert timeline_digest(timeline).startswith("sha256:")
    assert len(timeline_digest(timeline)) == 71


def test_clock_ranges_map_from_the_taught_window_to_full_song_time() -> None:
    timeline = timeline_from_dict(load_candidate())

    assert map_clock_range_to_root(timeline, "full-song", 1000, 3000) == (
        "full-song",
        1000,
        3000,
    )
    assert map_clock_range_to_root(timeline, "taught-solo", 0, 2000) == (
        "full-song",
        1000,
        3000,
    )


@pytest.mark.parametrize(
    ("time_ms", "expected"),
    [
        (-1, SelectionState("pre-roll", None, "steel-a")),
        (0, SelectionState("active", "steel-a", "steel-b")),
        (999, SelectionState("active", "steel-a", "steel-b")),
        (1000, SelectionState("active", "steel-b", None)),
        (1999, SelectionState("active", "steel-b", None)),
        (2000, SelectionState("post-roll", None, None)),
    ],
)
def test_selection_uses_inclusive_start_and_exclusive_end(
    time_ms: int,
    expected: SelectionState,
) -> None:
    timeline = timeline_from_dict(load_candidate())

    assert select_event(
        timeline,
        clock_id="taught-solo",
        track_id="steel-main",
        time_ms=time_ms,
    ) == expected


def test_selection_keeps_current_nullable_during_a_gap() -> None:
    source = load_candidate()
    source["events"][3]["startMs"] = 1500
    source["structures"][0]["endMs"] = 3500
    timeline = timeline_from_dict(source)

    assert select_event(
        timeline,
        clock_id="taught-solo",
        track_id="steel-main",
        time_ms=1200,
    ) == SelectionState("active", None, "steel-b")


def test_unknown_schema_and_product_only_top_level_fields_fail_closed() -> None:
    unknown_version = load_candidate()
    unknown_version["schemaVersion"] = "steel_platform_timeline_v2"
    with pytest.raises(TimelineValidationError) as version_error:
        timeline_from_dict(unknown_version)
    assert issue_codes(version_error.value) == {"schema-version"}

    product_field = load_candidate()
    product_field["approvals"] = []
    with pytest.raises(TimelineValidationError) as field_error:
        timeline_from_dict(product_field)
    assert issue_codes(field_error.value) == {"unknown-field"}


def test_copedent_digest_and_resolved_pitch_mismatches_fail_closed() -> None:
    bad_digest = load_candidate()
    bad_digest["copedent"]["snapshotDigest"] = "sha256:wrong"
    with pytest.raises(TimelineValidationError) as digest_error:
        timeline_from_dict(bad_digest)
    assert issue_codes(digest_error.value) == {"digest"}

    bad_pitch = load_candidate()
    bad_pitch["events"][1]["body"]["notes"][0]["pitch"] = {
        "midi": 68,
        "label": "G#4",
    }
    with pytest.raises(TimelineValidationError) as pitch_error:
        timeline_from_dict(bad_pitch)
    assert issue_codes(pitch_error.value) == {"pitch"}


def test_clock_cycles_and_out_of_parent_windows_are_rejected() -> None:
    cycle = load_candidate()
    cycle["clocks"][0]["kind"] = "window"
    cycle["clocks"][0]["parentMapping"] = {
        "parentClockId": "taught-solo",
        "parentStartMs": 0,
    }
    with pytest.raises(TimelineValidationError) as cycle_error:
        timeline_from_dict(cycle)
    assert "clock-graph" in issue_codes(cycle_error.value)

    overflow = load_candidate()
    overflow["clocks"][1]["parentMapping"]["parentStartMs"] = 3000
    with pytest.raises(TimelineValidationError) as overflow_error:
        timeline_from_dict(overflow)
    assert "clock-window" in issue_codes(overflow_error.value)


def test_references_ranges_and_same_track_overlap_are_rejected() -> None:
    dangling = load_candidate()
    dangling["events"][1]["body"]["positionId"] = "missing-position"
    with pytest.raises(TimelineValidationError) as dangling_error:
        timeline_from_dict(dangling)
    assert "position-reference" in issue_codes(dangling_error.value)

    outside_chord = load_candidate()
    outside_chord["events"][1]["endMs"] = 1100
    with pytest.raises(TimelineValidationError) as chord_error:
        timeline_from_dict(outside_chord)
    assert "chord-range" in issue_codes(chord_error.value)

    overlap = load_candidate()
    overlap["events"][2]["startMs"] = 900
    overlap["events"][2]["endMs"] = 1100
    with pytest.raises(TimelineValidationError) as overlap_error:
        timeline_from_dict(overlap)
    assert "event-overlap" in issue_codes(overlap_error.value)


def test_separate_tracks_may_overlap_without_ambiguous_selection() -> None:
    source = load_candidate()
    harmony = deepcopy(source["events"][1])
    harmony["id"] = "steel-harmony-a"
    harmony["trackId"] = "steel-harmony"
    harmony["body"]["role"] = "harmony"
    harmony["structureIds"] = []
    source["events"].append(harmony)
    source["events"].sort(
        key=lambda item: (
            item["clockId"],
            item["startMs"],
            item["endMs"],
            item["trackId"],
            item["id"],
        )
    )
    timeline = timeline_from_dict(source)

    assert select_event(
        timeline,
        clock_id="taught-solo",
        track_id="steel-harmony",
        time_ms=0,
    ) == SelectionState("active", "steel-harmony-a", None)


def test_unknown_technique_vocabulary_and_unordered_controls_are_rejected() -> None:
    technique = load_candidate()
    technique["events"][1]["body"]["notes"][0]["articulations"][0]["kind"] = "guess-me"
    with pytest.raises(TimelineValidationError) as technique_error:
        timeline_from_dict(technique)
    assert issue_codes(technique_error.value) == {"enum"}

    controls = load_candidate()
    controls["events"][3]["body"]["notes"][1]["controls"] = ["B", "A"]
    with pytest.raises(TimelineValidationError) as controls_error:
        timeline_from_dict(controls)
    assert issue_codes(controls_error.value) == {"controls-order"}
