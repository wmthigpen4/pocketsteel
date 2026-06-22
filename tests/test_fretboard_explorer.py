from __future__ import annotations

import pytest

from pocketsteel.fretboard_explorer import (
    E9_OPEN_STRINGS,
    ExplorerCandidate,
    build_g_explorer_payload,
    g_advanced_e_lower_pocket_rows,
    g_explorer_rows,
    g_major_three_string_rows,
    g_major_two_string_rows,
    g_natural_minor_three_string_rows,
    validate_explorer_candidate,
    validate_explorer_payload,
)


REQUIRED_ROW_KEYS = {
    "id",
    "key",
    "scale_type",
    "harmony_type",
    "scale_degree",
    "chord_function",
    "chord_name",
    "chord_quality",
    "fret",
    "string_group",
    "strings",
    "notes",
    "intervals",
    "display_notes",
    "display_top_voice",
    "display_summary",
    "pedals",
    "levers",
    "per_string_changes",
    "top_voice",
    "inversion",
    "voicing_status",
    "omitted_intervals",
    "position_family",
    "difficulty_tier",
    "availability_status",
    "pitch_validated",
    "copedent_profile",
    "source_guidance_refs",
    "explanation_summary",
    "warnings",
}


def by_group(rows: list, group: str) -> list[dict[str, object]]:
    return [row.to_dict() for row in rows if row.string_group == group]


def test_g_explorer_payload_shape_and_row_model() -> None:
    payload = build_g_explorer_payload()
    validate_explorer_payload(payload)

    assert payload["type"] == "e9-fretboard-explorer"
    assert payload["copedent_profile"]["id"] == "mvp-e9-standard"
    assert payload["query"]["key"] == "G"
    assert payload["positions"]

    row = payload["positions"][0]
    assert REQUIRED_ROW_KEYS.issubset(row)
    assert row["key"] == "G"
    assert row["pitch_validated"] is True
    assert row["availability_status"] == "available"
    assert 0 <= row["fret"] <= 24
    assert all(1 <= string <= 10 for string in row["strings"])
    assert row["string_group"] == "-".join(str(string) for string in row["strings"])
    assert set(row["display_notes"]) == {str(string) for string in row["strings"]}
    assert row["display_summary"]


def test_g_major_three_string_diatonic_harmony_core_grips() -> None:
    rows = g_major_three_string_rows()
    group_456 = by_group(rows, "4-5-6")

    assert [row["chord_function"] for row in group_456] == [
        "I",
        "ii",
        "iii",
        "IV",
        "V",
        "vi",
        "vii° / partial viiø",
        "I",
    ]
    assert [row["fret"] for row in group_456] == [3, 3, 5, 8, 10, 10, 13, 15]
    assert [row["chord_name"] for row in group_456] == ["G", "A", "B", "C", "D", "E", "F#", "G"]
    assert [row["chord_quality"] for row in group_456] == [
        "major",
        "minor",
        "minor",
        "major",
        "major",
        "minor",
        "diminished",
        "major",
    ]

    ii = group_456[1]
    assert ii["notes"] == {"4": "A", "5": "E", "6": "C"}
    assert ii["display_notes"] == {"4": "A", "5": "E", "6": "C"}
    assert ii["intervals"] == {"4": "1", "5": "5", "6": "b3"}
    assert ii["pedals"] == ["B", "C"]
    assert ii["levers"] == []
    assert ii["per_string_changes"] == {
        "4": {"from": "E", "to": "F#", "controls": "C"},
        "5": {"from": "B", "to": "C#", "controls": "C"},
        "6": {"from": "G#", "to": "A", "controls": "B"},
    }

    groups = {row.string_group for row in rows}
    assert {"3-4-5", "4-5-6", "5-6-8", "6-8-10"}.issubset(groups)
    assert {"5-6-7", "6-7-10"}.issubset(groups)


def test_g_natural_minor_three_string_diatonic_harmony() -> None:
    rows = g_natural_minor_three_string_rows()
    group_456 = by_group(rows, "4-5-6")

    assert [row["chord_function"] for row in group_456] == [
        "i",
        "ii° / partial iiø",
        "III",
        "iv",
        "v",
        "VI",
        "VII",
        "i",
    ]
    assert [row["fret"] for row in group_456] == [1, 4, 6, 6, 8, 11, 13, 13]
    assert [row["chord_name"] for row in group_456] == ["G", "A", "Bb", "C", "D", "Eb", "F", "G"]
    assert [row["chord_quality"] for row in group_456] == [
        "minor",
        "diminished",
        "major",
        "minor",
        "minor",
        "major",
        "major",
        "minor",
    ]

    ii_dim = group_456[1]
    assert ii_dim["notes"] == {"4": "A", "5": "D#", "6": "C"}
    assert ii_dim["display_notes"] == {"4": "A", "5": "Eb", "6": "C"}
    assert ii_dim["display_top_voice"]["note"] == "A"
    assert "A, Eb, C" in ii_dim["display_summary"]
    assert set(ii_dim["intervals"].values()) == {"1", "b3", "b5/#11"}
    assert ii_dim["voicing_status"] == "partial"
    assert ii_dim["omitted_intervals"] == ["b7"]
    assert "does not include the b7" in ii_dim["warnings"][0]


def test_g_natural_minor_display_spellings_are_key_aware_without_changing_pitch_identity() -> None:
    payload = build_g_explorer_payload()
    assert payload["query"]["display_scale_notes"]["natural_minor"] == ["G", "A", "Bb", "C", "D", "Eb", "F"]

    natural_minor_rows = [
        row
        for row in payload["positions"]
        if row["scale_type"] == "natural_minor"
    ]
    assert natural_minor_rows

    display_values = {
        note
        for row in natural_minor_rows
        for note in row["display_notes"].values()
    }
    assert "Bb" in display_values
    assert "Eb" in display_values
    assert "A#" not in display_values
    assert "D#" not in display_values

    third_degree = next(
        row
        for row in natural_minor_rows
        if row["string_group"] == "4-5-6" and row["scale_degree"] == 3
    )
    assert third_degree["chord_name"] == "Bb"
    assert third_degree["notes"] == {"4": "A#", "5": "F", "6": "D"}
    assert third_degree["display_notes"] == {"4": "Bb", "5": "F", "6": "D"}

    sixth_degree = next(
        row
        for row in natural_minor_rows
        if row["string_group"] == "4-5-6" and row["scale_degree"] == 6
    )
    assert sixth_degree["chord_name"] == "Eb"
    assert sixth_degree["notes"] == {"4": "D#", "5": "A#", "6": "G"}
    assert sixth_degree["display_notes"] == {"4": "Eb", "5": "Bb", "6": "G"}


def test_e9_copedent_and_mechanical_labels_keep_sharp_oriented_spellings() -> None:
    assert E9_OPEN_STRINGS[1] == "F#"
    assert E9_OPEN_STRINGS[2] == "D#"
    assert E9_OPEN_STRINGS[3] == "G#"

    pocket_row = g_advanced_e_lower_pocket_rows()[0].to_dict()
    assert pocket_row["per_string_changes"] == {
        "8": {"from": "E", "to": "Eb/D#", "controls": "E-lower"}
    }


def test_g_major_two_string_harmonized_rows_are_pitch_validated() -> None:
    rows = g_major_two_string_rows()
    group_46 = by_group(rows, "4-6")

    assert [row["scale_degree"] for row in group_46] == [1, 2, 3, 4, 5, 6, 7, 1]
    assert [row["fret"] for row in group_46] == [3, 4, 6, 8, 10, 11, 13, 15]
    assert all(row["harmony_type"] == "two_string_harmonized" for row in group_46)
    assert all(row["voicing_status"] == "partial" for row in group_46)
    assert group_46[1]["levers"] == ["E-raise"]
    assert group_46[1]["notes"] == {"4": "A", "6": "C"}


def test_advanced_swaps_and_e_lower_pocket_are_explicit() -> None:
    rows = g_explorer_rows()
    groups = {row.string_group for row in rows}
    assert {"5-6-7", "6-7-10", "5-7-8"}.issubset(groups)

    pocket_rows = [row.to_dict() for row in g_advanced_e_lower_pocket_rows()]
    assert [row["fret"] for row in pocket_rows] == [8, 20]
    for row in pocket_rows:
        assert row["string_group"] == "5-7-8"
        assert row["difficulty_tier"] == "advanced"
        assert row["levers"] == ["E-lower"]
        assert row["position_family"] == "e_lower_pocket"
        assert row["chord_name"] == "G"
        assert row["chord_quality"] == "major"
        assert row["voicing_status"] == "full"
        assert set(row["intervals"].values()) == {"1", "3", "5"}
        assert row["per_string_changes"] == {
            "8": {"from": "E", "to": "Eb/D#", "controls": "E-lower"}
        }


def test_b_plus_c_rejects_unvalidated_string_groups() -> None:
    candidate = ExplorerCandidate(
        key="G",
        scale_type="major",
        harmony_type="three_string_diatonic",
        scale_degree=1,
        chord_function="I",
        chord_name="G",
        chord_quality="major",
        fret=3,
        strings=(6, 8, 10),
        controls=("B", "C"),
    )

    with pytest.raises(ValueError, match="C does not affect played strings 6-8-10"):
        validate_explorer_candidate(candidate)

    invalid_568 = ExplorerCandidate(
        key="G",
        scale_type="major",
        harmony_type="three_string_diatonic",
        scale_degree=1,
        chord_function="I",
        chord_name="G",
        chord_quality="major",
        fret=3,
        strings=(5, 6, 8),
        controls=("B", "C"),
    )
    with pytest.raises(ValueError, match="do not validate as G major"):
        validate_explorer_candidate(invalid_568)


def test_diminished_triads_are_not_labeled_full_m7b5() -> None:
    major_vii_rows = [
        row.to_dict()
        for row in g_major_three_string_rows()
        if row.chord_function == "vii° / partial viiø"
    ]
    minor_ii_rows = [
        row.to_dict()
        for row in g_natural_minor_three_string_rows()
        if row.chord_function == "ii° / partial iiø"
    ]

    assert major_vii_rows
    assert minor_ii_rows
    for row in major_vii_rows + minor_ii_rows:
        assert row["chord_quality"] == "diminished"
        assert "m7b5" not in row["chord_name"].lower()
        assert row["voicing_status"] == "partial"
        assert row["omitted_intervals"] == ["b7"]
        assert set(row["intervals"].values()) == {"1", "b3", "b5/#11"}


def test_per_string_pedal_and_lever_mechanics_are_local_to_affected_strings() -> None:
    ab_row = next(
        row.to_dict()
        for row in g_major_three_string_rows()
        if row.string_group == "5-6-7" and row.chord_name == "A"
    )
    assert ab_row["pedals"] == ["A", "B"]
    assert ab_row["per_string_changes"] == {
        "5": {"from": "B", "to": "C#", "controls": "A"},
        "6": {"from": "G#", "to": "A", "controls": "B"},
    }
    assert "7" not in ab_row["per_string_changes"]

    e_raise_row = next(
        row.to_dict()
        for row in g_major_three_string_rows()
        if row.string_group == "5-6-8" and row.chord_function == "vii° / partial viiø"
    )
    assert e_raise_row["levers"] == ["E-raise"]
    assert e_raise_row["per_string_changes"] == {
        "8": {"from": "E", "to": "F", "controls": "E-raise"}
    }


def test_deterministic_rows_do_not_depend_on_rag_or_corpus_sources() -> None:
    for row in g_explorer_rows():
        payload = row.to_dict()
        assert all("forum" not in ref.lower() for ref in payload["source_guidance_refs"])
        assert all("sgf" not in ref.lower() for ref in payload["source_guidance_refs"])
        assert all("rag" not in ref.lower() for ref in payload["source_guidance_refs"])
        assert all("corpus" not in ref.lower() for ref in payload["source_guidance_refs"])
        assert payload["pitch_validated"] is True
