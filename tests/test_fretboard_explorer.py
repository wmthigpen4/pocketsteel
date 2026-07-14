from __future__ import annotations

import pytest

from pocketsteel.fretboard_explorer import (
    E9_OPEN_STRINGS,
    ExplorerCandidate,
    THREE_STRING_GRIP_VOCABULARY,
    all_three_string_grip_labels,
    build_control_impact_preview,
    build_explorer_payload,
    build_g_explorer_payload,
    explanation_for_explorer_row,
    explorer_rows,
    g_advanced_e_lower_pocket_rows,
    g_explorer_rows,
    g_five_eight_branch_rows,
    g_major_three_string_rows,
    g_major_two_string_rows,
    g_natural_minor_three_string_rows,
    grip_vocabulary_audit,
    grip_vocabulary_entry,
    normalize_explorer_key,
    SUPPORTED_EXPLORER_KEYS,
    validate_explorer_candidate,
    validate_explorer_payload,
)
from pocketsteel.e9_copedents import (
    CUSTOM_LKV_COPEDENT_ID,
    DAY_COPEDENT_ID,
    DEFAULT_COPEDENT_ID,
    available_e9_copedents,
    scientific_pitch_for_value,
    selected_copedent_payload,
)
from pocketsteel.fretboard_examples import absolute_pitch_for_string


REQUIRED_ROW_KEYS = {
    "id",
    "key",
    "scale_type",
    "harmony_type",
    "display_harmony_type",
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
    "control_impacts",
    "inversion",
    "voicing_status",
    "omitted_intervals",
    "position_family",
    "difficulty_tier",
    "availability_status",
    "pitch_validated",
    "copedent_profile",
    "note_registers",
    "notes_with_register",
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
    assert payload["copedent_profile"]["id"] == DEFAULT_COPEDENT_ID
    assert payload["selected_copedent"]["id"] == DEFAULT_COPEDENT_ID
    assert payload["selected_copedent"]["label"] == "Emmons E9 starter"
    assert payload["query"]["key"] == "G"
    assert payload["positions"]
    assert payload["control_impact_preview"]["type"] == "e9-pedal-lever-impact-preview"
    assert payload["control_impact_preview"]["key_context"]["key"] == "G"

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
    assert row["explanation_summary"]
    assert "validated E9 pitch logic" in row["explanation_summary"]
    assert "Teaching text explains the row; it does not choose the row" in row["explanation_summary"]
    assert isinstance(row["control_impacts"], list)
    assert set(row["note_registers"]) == {str(string) for string in row["strings"]}
    assert len(row["notes_with_register"]) == len(row["strings"])
    for register in row["notes_with_register"]:
        assert {
            "string",
            "fret",
            "active_controls",
            "pitch_class",
            "display_note",
            "scientific_pitch",
            "pitch_value",
            "octave",
            "octave_band",
            "voice_role",
        }.issubset(register)
        assert register["octave_band"] in {"lower", "middle", "upper"}


def test_three_string_grip_vocabulary_audits_all_possible_combinations() -> None:
    payload = build_g_explorer_payload()
    validate_explorer_payload(payload)

    assert len(all_three_string_grip_labels()) == 120
    assert all_three_string_grip_labels()[0] == "1-2-3"
    assert all_three_string_grip_labels()[-1] == "8-9-10"

    required = {
        "3-4-5",
        "4-5-6",
        "5-6-8",
        "6-8-10",
        "5-6-7",
        "6-7-10",
        "4-6-10",
        "3-5-8",
        "3-5-9",
        "4-6-9",
        "5-6-9",
        "3-5-6",
        "4-5-8",
        "5-8-10",
        "5-7-8",
    }
    assert required.issubset(set(THREE_STRING_GRIP_VOCABULARY))

    audit = grip_vocabulary_audit()
    assert audit["total_three_string_combinations"] == 120
    assert audit["registered_count"] == len(required)
    assert audit["unclassified_count"] == 120 - len(required)
    assert audit["known_required_present"] == {
        "5-7-8": True,
        "5-6-7": True,
        "6-7-10": True,
        "4-6-10": True,
        "3-5-9": True,
        "3-5-8": True,
    }
    assert "5-7-8" in audit["hidden_from_default"]
    assert "Calculate all 120 mechanical 3-string groups" in audit["policy"]
    assert payload["grip_vocabulary"]["three_string_audit"]["total_three_string_combinations"] == 120


def test_three_string_grip_vocabulary_classifies_required_extended_and_pocket_grips() -> None:
    assert grip_vocabulary_entry("3-4-5").tier == "core"
    assert grip_vocabulary_entry("5-6-7").tier == "path"
    assert grip_vocabulary_entry("6-7-10").tier == "path"
    assert grip_vocabulary_entry("4-6-10").tier == "extended"
    assert grip_vocabulary_entry("3-5-8").tier == "song-tab-vocabulary"
    assert grip_vocabulary_entry("3-5-9").tier == "song-tab-vocabulary"
    assert grip_vocabulary_entry("5-7-8").tier == "e-lower-pocket"
    assert grip_vocabulary_entry((5, 7, 8)).required_vocabulary == "e-lower-pockets"
    assert "E-lower pocket grip" in grip_vocabulary_entry("5-7-8").explanation
    assert "9th-string color is context-dependent" in grip_vocabulary_entry("3-5-9").watch_out
    assert grip_vocabulary_entry("1-2-3") is None


def test_control_impact_preview_contract_describes_standard_e9_changes_in_key_context() -> None:
    preview = build_control_impact_preview("G")

    assert preview["type"] == "e9-pedal-lever-impact-preview"
    assert preview["version"] == "1.0"
    assert preview["instrument"] == "E9"
    assert preview["copedent_profile"]["id"] == DEFAULT_COPEDENT_ID
    assert preview["selected_copedent_id"] == DEFAULT_COPEDENT_ID
    assert preview["key_context"]["key"] == "G"
    assert preview["key_context"]["major_scale"] == ["G", "A", "B", "C", "D", "E", "F#"]
    assert preview["key_context"]["natural_minor_scale"] == ["G", "A", "Bb", "C", "D", "Eb", "F"]

    controls = {control["id"]: control for control in preview["controls"]}
    assert set(controls) == {
        "A", "B", "C", "E-raise", "E-lower", "D-lower", "RKR-full", "RKL-half", "G-lower"
    }
    assert "B-to-Bb" not in controls

    a_pedal = controls["A"]
    assert a_pedal["label"] == "A pedal"
    assert a_pedal["stable_id"] == "A"
    assert a_pedal["display_label"] == "A pedal"
    assert a_pedal["mechanical_name"] == "B-to-C# raise on strings 5 and 10"
    assert a_pedal["player_shorthand"] == ["A"]
    assert a_pedal["change_type"] == "raise"
    assert a_pedal["travel"] == "pedal"
    assert a_pedal["control_type"] == "pedal"
    assert a_pedal["affected_strings"] == [5, 10]
    assert a_pedal["string_actions"][0]["description"] == "String 5: raises B to C# (2 semitones)."
    a_string_5 = next(impact for impact in a_pedal["string_impacts"] if impact["string"] == 5)
    assert a_string_5["before_note"] == "B"
    assert a_string_5["after_note"] == "C#"
    assert a_string_5["semitone_delta"] == 2
    assert a_string_5["interval_effect"] == "raises 2 semitones"
    assert a_string_5["before_key_context"]["major"]["scale_degree_label"] == "3"
    assert a_string_5["after_key_context"]["major"]["scale_degree_label"] == "outside"
    assert a_string_5["after_key_context"]["major"]["interval_to_key_root"] == "b5/#11"

    e_lower = controls["E-lower"]
    assert e_lower["label"] == "E-lower lever"
    assert e_lower["control_type"] == "lever"
    assert e_lower["affected_strings"] == [4, 8]
    e_lower_string_4 = next(impact for impact in e_lower["string_impacts"] if impact["string"] == 4)
    assert e_lower_string_4["before_note"] == "E"
    assert e_lower_string_4["after_note"] == "Eb/D#"
    assert e_lower_string_4["semitone_delta"] == -1
    assert e_lower_string_4["interval_effect"] == "lowers 1 semitone"
    assert e_lower_string_4["after_key_context"]["natural_minor"]["scale_degree_label"] == "6"
    assert e_lower_string_4["after_key_context"]["natural_minor"]["display_note"] == "Eb"
    assert "deterministic Emmons E9 starter 10-string E9 pitch logic" in preview["notes"][0]

    d_lower = controls["D-lower"]
    assert d_lower["label"] == "D lower half-stop"
    assert d_lower["display_label"] == "D lower half-stop"
    assert d_lower["mechanical_name"] == "D#-to-D half-stop on string 2 plus D-to-C# lower on string 9"
    assert d_lower["player_shorthand"] == ["D-", "D half-stop"]
    assert d_lower["change_type"] == "lower"
    assert d_lower["travel"] == "half-stop"
    assert d_lower["control_type"] == "lever"
    assert d_lower["affected_strings"] == [2, 9]
    d_lower_string_9 = next(impact for impact in d_lower["string_impacts"] if impact["string"] == 9)
    assert d_lower_string_9["before_note"] == "D"
    assert d_lower_string_9["after_note"] == "C#"
    assert d_lower_string_9["interval_effect"] == "lowers 1 semitone"

    g_control = controls["G-lower"]
    assert g_control["label"] == "RKL full-stop / G lower"
    assert g_control["travel"] == "full-stop"
    assert g_control["mechanical_name"] == "string 1 F#-to-G raise plus string 6 G#-to-F# lower"
    assert g_control["change_type"] == "mixed"
    assert g_control["affected_strings"] == [1, 6]
    assert g_control["string_actions"][0]["description"] == "String 1: raises F# to G (1 semitone)."
    assert g_control["string_actions"][1]["description"] == "String 6: lowers G# to F# (2 semitones)."

    assert controls["RKL-half"]["physical_position"] == g_control["physical_position"] == "RKL"
    assert controls["RKL-half"]["travel"] == "half-stop"
    assert controls["RKL-half"]["string_actions"][1]["description"] == "String 6: lowers G# to G (1 semitone)."
    assert controls["RKR-full"]["physical_position"] == d_lower["physical_position"] == "RKR"
    assert controls["RKR-full"]["travel"] == "full-stop"


def test_e9_copedent_selector_data_exposes_only_immutable_common_starters() -> None:
    options = [profile.selector_option() for profile in available_e9_copedents()]

    assert [option["id"] for option in options] == [
        DEFAULT_COPEDENT_ID,
        DAY_COPEDENT_ID,
    ]
    assert options[0] == {"id": DEFAULT_COPEDENT_ID, "label": "Emmons E9 starter", "status": "enabled"}
    assert options[1] == {"id": DAY_COPEDENT_ID, "label": "Day E9 starter", "status": "enabled"}
    assert not any("C6" in option["label"] for option in options)


def test_selected_copedent_chart_payload_is_visual_table_ready() -> None:
    payload = selected_copedent_payload()

    assert payload["id"] == DEFAULT_COPEDENT_ID
    assert payload["pedal_order"] == ["A", "B", "C"]
    assert [row["string"] for row in payload["strings"]] == list(range(1, 11))
    assert payload["strings"][0]["open_note"] == "F#"
    assert payload["strings"][0]["open_scientific_pitch"] == "F#4"
    assert payload["strings"][0]["open_pitch_value"] == 66
    assert payload["strings"][0]["open_octave_band"] == "upper"
    assert payload["strings"][3]["open_note"] == "E"
    assert payload["strings"][3]["open_scientific_pitch"] == "E4"
    assert payload["strings"][7]["open_note"] == "E"
    assert payload["strings"][7]["open_scientific_pitch"] == "E3"
    assert payload["strings"][8]["open_note"] == "D"
    assert payload["strings"][8]["open_scientific_pitch"] == "D3"

    chart = payload["chart"]
    assert len(chart["rows"]) == 10
    assert [column["id"] for column in chart["columns"]][:3] == ["A", "B", "C"]
    a_column = chart["columns"][0]
    assert a_column["stable_id"] == "A"
    assert a_column["display_label"] == "A pedal"
    assert a_column["mechanical_name"] == "B-to-C# raise on strings 5 and 10"
    assert a_column["player_shorthand"] == ["A"]
    assert a_column["affected_strings"] == [5, 10]
    assert a_column["change_type"] == "raise"
    assert a_column["string_actions"][0]["description"] == "String 5: raises B to C# (2 semitones)."
    assert "B-to-Bb" not in [column["id"] for column in chart["columns"]]
    row_5 = next(row for row in chart["rows"] if row["string"] == 5)
    assert row_5["open_note"] == "B"
    assert row_5["cells"]["A"]["label"] == "B -> C#"
    assert row_5["cells"]["A"]["direction"] == "raise"
    assert row_5["cells"]["B"] is None
    assert "B-to-Bb" not in row_5["cells"]


def test_standard_e9_absolute_pitch_register_map() -> None:
    payload = selected_copedent_payload()

    assert [item["open_scientific_pitch"] for item in payload["strings"]] == [
        "F#4",
        "D#4",
        "G#4",
        "E4",
        "B3",
        "G#3",
        "F#3",
        "E3",
        "D3",
        "B2",
    ]
    assert scientific_pitch_for_value(absolute_pitch_for_string(5, 3, ())) == "D4"
    assert scientific_pitch_for_value(absolute_pitch_for_string(5, 3, ("A",))) == "E4"
    assert scientific_pitch_for_value(absolute_pitch_for_string(3, 3, ())) == "B4"
    assert scientific_pitch_for_value(absolute_pitch_for_string(3, 3, ("B",))) == "C5"


def test_custom_lkv_copedent_extracts_user_specific_vertical_without_polluting_emmons() -> None:
    emmons_payload = selected_copedent_payload(DEFAULT_COPEDENT_ID)
    emmons_columns = [column["id"] for column in emmons_payload["chart"]["columns"]]
    assert "B-to-Bb" not in emmons_columns

    payload = selected_copedent_payload(CUSTOM_LKV_COPEDENT_ID)
    assert payload["id"] == CUSTOM_LKV_COPEDENT_ID
    assert payload["label"] == "Custom E9 (with LKV)"
    assert payload["pedal_order"] == ["A", "B", "C"]
    chart = payload["chart"]
    columns = [column["id"] for column in chart["columns"]]
    assert columns[:3] == ["A", "B", "C"]
    assert "B-to-Bb" in columns
    assert "RKL-half" in columns
    assert "RKR-full" in columns
    row_5 = next(row for row in chart["rows"] if row["string"] == 5)
    assert row_5["cells"]["B-to-Bb"]["label"] == "B -> Bb/A#"
    assert row_5["cells"]["B-to-Bb"]["direction"] == "lower"
    preview = build_control_impact_preview("G", copedent_id=CUSTOM_LKV_COPEDENT_ID)
    preview_controls = {control["id"]: control for control in preview["controls"]}
    assert "B-to-Bb" in preview_controls
    assert preview_controls["B-to-Bb"]["affected_strings"] == [5, 10]
    assert preview_controls["B-to-Bb"]["display_label"] == "B-to-Bb vertical"
    assert preview_controls["B-to-Bb"]["mechanical_name"] == "B-to-Bb/A# lower on strings 5 and 10"
    assert preview_controls["B-to-Bb"]["player_shorthand"] == ["V", "vertical", "LKV"]
    assert preview_controls["B-to-Bb"]["compatibility_aliases"] == ["B-to-A#", "LKV"]

    rkl_full = preview_controls["G-lower"]
    assert rkl_full["display_label"] == "RKL full-stop / G lower"
    assert rkl_full["change_type"] == "mixed"
    assert rkl_full["string_actions"][0]["description"] == "String 1: raises F# to G (1 semitone)."
    assert rkl_full["string_actions"][1]["description"] == "String 6: lowers G# to F# (2 semitones)."

    rkr_half = preview_controls["D-lower"]
    assert rkr_half["display_label"] == "D lower half-stop"
    assert rkr_half["mechanical_name"] == "D#-to-D half-stop on string 2 plus D-to-C# lower on string 9"
    assert any(action["string"] == 9 and action["to"] == "C#" for action in rkr_half["string_actions"])

    rkr_full = preview_controls["RKR-full"]
    assert rkr_full["display_label"] == "D lower full-stop"
    assert rkr_full["mechanical_name"] == "D#-to-C# full-stop on string 2 plus D-to-C# lower on string 9"
    assert any(action["string"] == 9 and action["from"] == "D" and action["to"] == "C#" for action in rkr_full["string_actions"])


def test_day_e9_changes_physical_pedal_order_but_not_named_pedal_changes() -> None:
    payload = build_explorer_payload("G", copedent_id=DAY_COPEDENT_ID)
    validate_explorer_payload(payload)

    selected = payload["selected_copedent"]
    assert selected["id"] == DAY_COPEDENT_ID
    assert selected["label"] == "Day E9 starter"
    assert selected["pedal_order"] == ["C", "B", "A"]
    assert [column["id"] for column in selected["chart"]["columns"]][:3] == ["C", "B", "A"]

    controls = {control["id"]: control for control in selected["controls"]}
    assert controls["A"]["physical_position"] == "P3"
    assert controls["A"]["display_label"] == "A pedal"
    assert controls["A"]["stable_id"] == "A"
    assert controls["A"]["mechanical_name"] == "B-to-C# raise on strings 5 and 10"
    assert controls["A"]["changes"] == [
        {"string": 5, "from": "B", "to": "C#", "semitones": 2, "direction": "raise", "arrow": "up"},
        {"string": 10, "from": "B", "to": "C#", "semitones": 2, "direction": "raise", "arrow": "up"},
    ]
    assert controls["C"]["physical_position"] == "P1"

    preview_control_order = [control["id"] for control in payload["control_impact_preview"]["controls"]]
    assert preview_control_order[:3] == ["C", "B", "A"]


def test_row_level_control_impacts_describe_selected_chord_context() -> None:
    row = next(
        row.to_dict()
        for row in g_major_three_string_rows()
        if row.string_group == "4-5-6" and row.chord_function == "ii"
    )

    assert row["chord_name"] == "A"
    assert row["pedals"] == ["B", "C"]
    assert row["levers"] == []
    impacts = {impact["id"]: impact for impact in row["control_impacts"]}
    assert set(impacts) == {"B", "C"}

    b_impact = impacts["B"]
    assert b_impact["label"] == "B pedal"
    assert b_impact["affected_strings"] == [6]
    b_string = b_impact["string_impacts"][0]
    assert b_string["string"] == 6
    assert b_string["before_open_note"] == "G#"
    assert b_string["after_open_note"] == "A"
    assert b_string["before_note"] == "B"
    assert b_string["after_note"] == "C"
    assert b_string["before_interval"] == "2/9"
    assert b_string["after_interval"] == "b3"
    assert b_string["interval_effect"] == "raises 1 semitone"
    assert b_impact["resulting_context"]["row_validates_as"] == "A minor"

    c_impact = impacts["C"]
    assert c_impact["label"] == "C pedal"
    assert c_impact["affected_strings"] == [4, 5]
    c_by_string = {impact["string"]: impact for impact in c_impact["string_impacts"]}
    assert c_by_string[4]["before_note"] == "G"
    assert c_by_string[4]["after_note"] == "A"
    assert c_by_string[4]["before_interval"] == "b7"
    assert c_by_string[4]["after_interval"] == "1"
    assert c_by_string[5]["before_note"] == "D"
    assert c_by_string[5]["after_note"] == "E"
    assert c_by_string[5]["before_interval"] == "4/11"
    assert c_by_string[5]["after_interval"] == "5"

    no_pedals_row = next(
        row.to_dict()
        for row in g_major_three_string_rows()
        if row.string_group == "4-5-6" and row.chord_function == "I"
    )
    assert no_pedals_row["control_impacts"] == []


def test_transposed_major_payloads_validate_for_representative_keys() -> None:
    expected_i_rows = {
        "C": (8, {"4": "C", "5": "G", "6": "E"}),
        "D": (10, {"4": "D", "5": "A", "6": "F#"}),
        "F": (1, {"4": "F", "5": "C", "6": "A"}),
        "Bb": (6, {"4": "Bb", "5": "F", "6": "D"}),
    }

    for key, (expected_fret, expected_display_notes) in expected_i_rows.items():
        payload = build_explorer_payload(key)
        validate_explorer_payload(payload)

        assert payload["query"]["key"] == key
        row = next(
            position
            for position in payload["positions"]
            if position["scale_type"] == "major"
            and position["harmony_type"] == "three_string_diatonic"
            and position["string_group"] == "4-5-6"
            and position["scale_degree"] == 1
            and position["chord_function"] == "I"
        )
        assert row["chord_name"] == key
        assert row["fret"] == expected_fret
        assert row["display_notes"] == expected_display_notes
        assert row["pitch_validated"] is True


def test_explorer_backend_payloads_validate_for_all_supported_key_spellings() -> None:
    unique_pitch_classes: set[int] = set()
    for key in SUPPORTED_EXPLORER_KEYS:
        payload = build_explorer_payload(key)
        validate_explorer_payload(payload)

        assert payload["query"]["key"] == key
        assert key in payload["filters"]["available_keys"]
        assert payload["positions"]
        unique_pitch_classes.add(next(row["fret"] for row in payload["positions"] if row["chord_function"] == "I") % 12)

    assert len(unique_pitch_classes) == 12


def test_explorer_key_normalization_accepts_unicode_accidentals() -> None:
    assert normalize_explorer_key("A♭") == "Ab"
    assert normalize_explorer_key("C♯") == "C#"


def test_transposed_natural_minor_payloads_use_key_aware_display_scale_notes() -> None:
    payload = build_explorer_payload("C")
    validate_explorer_payload(payload)

    assert payload["query"]["display_scale_notes"]["natural_minor"] == [
        "C",
        "D",
        "Eb",
        "F",
        "G",
        "Ab",
        "Bb",
    ]

    flat_display_values = {
        note
        for row in payload["positions"]
        if row["scale_type"] == "natural_minor"
        for note in row["display_notes"].values()
    }
    assert {"Eb", "Ab", "Bb"}.issubset(flat_display_values)
    assert "D#" not in flat_display_values
    assert "G#" not in flat_display_values
    assert "A#" not in flat_display_values


def test_flat_major_keys_prefer_flat_learner_display_spellings() -> None:
    payload = build_explorer_payload("Bb")
    validate_explorer_payload(payload)

    assert payload["query"]["display_scale_notes"]["major"] == ["Bb", "C", "D", "Eb", "F", "G", "A"]
    iv_row = next(
        position
        for position in payload["positions"]
        if position["scale_type"] == "major"
        and position["string_group"] == "4-5-6"
        and position["chord_function"] == "IV"
    )
    assert iv_row["chord_name"] == "Eb"
    assert iv_row["notes"] == {"4": "D#", "5": "A#", "6": "G"}
    assert iv_row["display_notes"] == {"4": "Eb", "5": "Bb", "6": "G"}


def test_sharp_major_keys_prefer_sharp_learner_display_spellings() -> None:
    payload = build_explorer_payload("C#")
    validate_explorer_payload(payload)

    assert payload["query"]["display_scale_notes"]["major"] == [
        "C#",
        "D#",
        "E#",
        "F#",
        "G#",
        "A#",
        "B#",
    ]
    i_row = next(
        position
        for position in payload["positions"]
        if position["scale_type"] == "major"
        and position["string_group"] == "4-5-6"
        and position["chord_function"] == "I"
    )
    assert i_row["chord_name"] == "C#"
    assert i_row["notes"] == {"4": "C#", "5": "G#", "6": "F"}
    assert i_row["display_notes"] == {"4": "C#", "5": "G#", "6": "E#"}

    f_sharp_payload = build_explorer_payload("F#")
    validate_explorer_payload(f_sharp_payload)
    assert f_sharp_payload["query"]["display_scale_notes"]["major"] == [
        "F#",
        "G#",
        "A#",
        "B",
        "C#",
        "D#",
        "E#",
    ]


def test_transposed_rows_keep_mode_and_advanced_grip_rules() -> None:
    rows = [row.to_dict() for row in explorer_rows("F")]
    validate_explorer_payload(build_explorer_payload("F"))

    assert {row["string_group"] for row in rows if row["harmony_type"] == "three_string_diatonic"}.issuperset(
        {"3-4-5", "4-5-6", "5-6-8", "6-8-10", "5-6-7", "6-7-10"}
    )
    assert {row["string_group"] for row in rows if row["harmony_type"] == "advanced_pocket"} == {"5-7-8"}
    assert all(row["harmony_type"] != "advanced_pocket" or row["difficulty_tier"] == "advanced" for row in rows)
    assert all(row["pitch_validated"] is True for row in rows)


def test_explanation_text_for_major_rows_is_deterministic_and_learner_facing() -> None:
    row = next(
        row
        for row in g_major_three_string_rows()
        if row.string_group == "4-5-6" and row.chord_function == "I"
    )
    explanation = row.explanation_summary

    assert "three-string diatonic-harmony row" in explanation
    assert "I" in explanation
    assert "degree 1 chord in G major" in explanation
    assert "validates as G major" in explanation
    assert "fret 3" in explanation
    assert "strings 4-5-6" in explanation
    assert "no pedals/no levers" in explanation
    assert "straight-bar reference" in explanation
    assert "G, D, B" in explanation
    assert "validated E9 pitch logic" in explanation
    assert "does not choose the row" in explanation


def test_explanation_text_for_natural_minor_rows_uses_key_aware_spellings() -> None:
    row = next(
        row
        for row in explorer_rows("C")
        if row.scale_type == "natural_minor"
        and row.string_group == "4-5-6"
        and row.chord_function == "i"
    )
    explanation = row.explanation_summary

    assert "degree 1 chord in C natural minor" in explanation
    assert "validates as C minor" in explanation
    assert "C, G, Eb" in explanation
    assert "D#" not in explanation


def test_explanation_text_for_two_string_rows_marks_partial_interval_pair() -> None:
    row = next(
        row
        for row in g_major_two_string_rows()
        if row.string_group == "4-6" and row.scale_degree == 1
    )
    explanation = row.explanation_summary

    assert "two-string harmonized-scale row" in explanation
    assert "degree 1 in G major" in explanation
    assert "partial interval pair" in explanation
    assert "not a full triad" in explanation
    assert "validated E9 pitch logic" in explanation


def test_explanation_text_for_advanced_e_lower_pocket_uses_mechanical_name() -> None:
    row = g_advanced_e_lower_pocket_rows()[0]
    explanation = row.explanation_summary

    assert "advanced 5-7-8 E-lower pocket" in explanation
    assert "G major" in explanation
    assert "E-lower lever" in explanation
    assert "mechanical E-lower lever name" in explanation
    assert "Grip vocabulary: E-lower pocket" in explanation
    assert "An E-lower pocket grip" in explanation
    assert "validated E9 pitch logic" in explanation


def test_explanation_text_for_b_plus_c_rows_includes_validation_caveat() -> None:
    row = next(
        row
        for row in g_major_three_string_rows()
        if row.string_group == "4-5-6" and row.chord_function == "ii"
    )
    explanation = row.explanation_summary

    assert "B pedal + C pedal" in explanation
    assert "B+C is validated for this exact row" in explanation
    assert "do not generalize B+C" in explanation


def test_explanation_text_for_partial_diminished_rows_avoids_full_m7b5_claim() -> None:
    row = next(
        row
        for row in g_major_three_string_rows()
        if row.string_group == "4-5-6" and row.chord_function == "vii° / partial viiø"
    )
    explanation = row.explanation_summary

    assert "validates as F# diminished" in explanation
    assert "omits b7" in explanation
    assert "partial half-diminished color" in explanation
    assert "not a full m7b5" in explanation
    assert "full m7b5" not in row.chord_name.lower()
    assert "full m7b5" not in row.display_summary.lower()


def test_explanation_helper_does_not_mutate_row_data_or_rely_on_rag_corpus() -> None:
    row = g_advanced_e_lower_pocket_rows()[0]
    before = row.to_dict()
    explanation = explanation_for_explorer_row(row)
    after = row.to_dict()

    assert before == after
    assert explanation == row.explanation_summary
    lower_explanation = explanation.lower()
    assert "rag" not in lower_explanation
    assert "corpus" not in lower_explanation
    assert "forum" not in lower_explanation
    assert "song" not in lower_explanation
    assert "buddy" not in lower_explanation
    assert "emmons" not in lower_explanation


@pytest.mark.parametrize("key", ["C", "D", "F", "Bb", "Eb"])
def test_expanded_key_payloads_keep_core_invariants(key: str) -> None:
    payload = build_explorer_payload(key)
    validate_explorer_payload(payload)
    rows = payload["positions"]

    assert payload["query"]["key"] == key
    assert all(row["pitch_validated"] is True for row in rows)
    assert all(0 <= row["fret"] <= 24 for row in rows)
    assert all(all(1 <= string <= 10 for string in row["strings"]) for row in rows)
    assert all(
        "rag" not in ref.lower() and "corpus" not in ref.lower() and "sgf" not in ref.lower()
        for row in rows
        for ref in row["source_guidance_refs"]
    )

    group_456_major = [
        row
        for row in rows
        if row["scale_type"] == "major"
        and row["harmony_type"] == "three_string_diatonic"
        and row["string_group"] == "4-5-6"
    ]
    group_456_minor = [
        row
        for row in rows
        if row["scale_type"] == "natural_minor"
        and row["harmony_type"] == "three_string_diatonic"
        and row["string_group"] == "4-5-6"
    ]
    assert [row["scale_degree"] for row in group_456_major[:8]] == [1, 2, 3, 4, 5, 6, 7, 1]
    assert [row["scale_degree"] for row in group_456_minor[:8]] == [1, 2, 3, 4, 5, 6, 7, 1]
    assert len(group_456_major) >= 8
    assert len(group_456_minor) >= 8

    advanced_578 = [row for row in rows if row["string_group"] == "5-7-8"]
    assert advanced_578
    assert all(row["harmony_type"] == "advanced_pocket" for row in advanced_578)
    assert all(row["difficulty_tier"] == "advanced" for row in advanced_578)
    assert all(row["position_family"] == "e_lower_pocket" for row in advanced_578)

    partial_diminished_rows = [
        row
        for row in rows
        if row["chord_quality"] == "diminished"
        and set(row["intervals"].values()) == {"1", "b3", "b5/#11"}
    ]
    assert partial_diminished_rows
    assert all(row["voicing_status"] == "partial" for row in partial_diminished_rows)
    assert all(row["omitted_intervals"] == ["b7"] for row in partial_diminished_rows)
    assert all("does not include the b7" in row["warnings"][0] for row in partial_diminished_rows)


def test_g_major_three_string_diatonic_harmony_core_grips() -> None:
    rows = g_major_three_string_rows()
    group_456 = by_group(rows, "4-5-6")

    assert [row["chord_function"] for row in group_456[:8]] == [
        "I",
        "ii",
        "iii",
        "IV",
        "V",
        "vi",
        "vii° / partial viiø",
        "I",
    ]
    assert [row["fret"] for row in group_456[:8]] == [3, 3, 5, 8, 10, 10, 13, 15]
    assert [row["chord_name"] for row in group_456[:8]] == ["G", "A", "B", "C", "D", "E", "F#", "G"]
    assert [row["fret"] for row in group_456[8:]] == [15, 17, 20, 22, 22]
    assert [row["chord_name"] for row in group_456[8:]] == ["A", "B", "C", "D", "E"]
    assert [row["chord_quality"] for row in group_456[:8]] == [
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


def test_g_major_single_grip_keeps_octave_equivalent_top_note_results() -> None:
    rows = g_major_three_string_rows()
    group_345 = by_group(rows, "3-4-5")
    top_g_bc = [
        row
        for row in group_345
        if row["display_top_voice"]["note"] == "G"
        and row["pedals"] == ["B", "C"]
        and row["levers"] == []
    ]

    assert [row["fret"] for row in top_g_bc] == [10, 22]
    assert all(row["intervals"] == {"3": "b3", "4": "1", "5": "5"} for row in top_g_bc)


def test_g_natural_minor_three_string_diatonic_harmony() -> None:
    rows = g_natural_minor_three_string_rows()
    group_456 = by_group(rows, "4-5-6")

    assert [row["chord_function"] for row in group_456[:8]] == [
        "i",
        "ii° / partial iiø",
        "III",
        "iv",
        "v",
        "VI",
        "VII",
        "i",
    ]
    assert [row["fret"] for row in group_456[:8]] == [1, 4, 6, 6, 8, 11, 13, 13]
    assert [row["chord_name"] for row in group_456[:8]] == ["G", "A", "Bb", "C", "D", "Eb", "F", "G"]
    assert [row["fret"] for row in group_456[8:]] == [16, 18, 18, 20, 23]
    assert [row["chord_name"] for row in group_456[8:]] == ["A", "Bb", "C", "D", "Eb"]
    assert [row["chord_quality"] for row in group_456[:8]] == [
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


def test_g_five_eight_branch_alternatives_keep_a_f_and_e_lower_routes() -> None:
    rows = [row.to_dict() for row in g_five_eight_branch_rows()]

    assert [row["harmony_type"] for row in rows] == ["five_eight_branch"] * 4
    assert [row["display_harmony_type"] for row in rows] == ["two_string_harmonized"] * 4
    assert [row["string_group"] for row in rows] == ["5-8"] * 4
    assert [row["fret"] for row in rows] == [6, 8, 11, 13]
    assert [row["chord_function"] for row in rows] == [
        "branch 4 minor/blue color",
        "branch 4 major color",
        "branch 7 minor/blue color",
        "branch 7 major color",
    ]

    branch_by_fret = {row["fret"]: row for row in rows}
    assert branch_by_fret[6]["pedals"] == ["A"]
    assert branch_by_fret[6]["levers"] == ["E-raise"]
    assert branch_by_fret[6]["notes"] == {"5": "G", "8": "B"}
    assert branch_by_fret[6]["intervals"] == {"5": "1", "8": "3"}
    assert branch_by_fret[6]["position_family"] == "five_eight_a_f_minor_blue"

    assert branch_by_fret[8]["pedals"] == []
    assert branch_by_fret[8]["levers"] == ["E-lower"]
    assert branch_by_fret[8]["notes"] == {"5": "G", "8": "B"}
    assert branch_by_fret[8]["intervals"] == {"5": "1", "8": "3"}
    assert branch_by_fret[8]["position_family"] == "five_eight_e_lower_major_color"

    assert branch_by_fret[11]["pedals"] == ["A"]
    assert branch_by_fret[11]["levers"] == ["E-raise"]
    assert branch_by_fret[11]["notes"] == {"5": "C", "8": "E"}
    assert branch_by_fret[11]["intervals"] == {"5": "1", "8": "3"}

    assert branch_by_fret[13]["pedals"] == []
    assert branch_by_fret[13]["levers"] == ["E-lower"]
    assert branch_by_fret[13]["notes"] == {"5": "C", "8": "E"}
    assert branch_by_fret[13]["intervals"] == {"5": "1", "8": "3"}
    assert "corrected" not in branch_by_fret[13]["display_summary"].lower()

    assert not any(row["fret"] == 11 and row["levers"] == ["E-lower"] for row in rows)
    assert all(row["voicing_status"] == "partial" for row in rows)
    assert all("both valid mechanical paths" in row["explanation_summary"] for row in rows)


def test_g_explorer_payload_includes_five_eight_branch_without_collapsing_routes() -> None:
    payload = build_g_explorer_payload()
    validate_explorer_payload(payload)

    branch_rows = [
        row
        for row in payload["positions"]
        if row["harmony_type"] == "five_eight_branch"
    ]
    assert len(branch_rows) == 4
    assert "five_eight_branch" in payload["query"]["harmony_types"]
    assert "five_eight_branch" in payload["filters"]["available_harmony_types"]
    assert "5-8" in payload["query"]["string_groups"]
    assert {row["display_harmony_type"] for row in branch_rows} == {"two_string_harmonized"}

    routes = {(tuple(row["pedals"]), tuple(row["levers"]), row["fret"]) for row in branch_rows}
    assert (("A",), ("E-raise",), 6) in routes
    assert ((), ("E-lower",), 8) in routes
    assert (("A",), ("E-raise",), 11) in routes
    assert ((), ("E-lower",), 13) in routes
    assert ((), ("E-lower",), 11) not in routes


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


def test_required_extended_grip_examples_are_pitch_validated_when_the_notes_fit() -> None:
    wide_ab = validate_explorer_candidate(
        ExplorerCandidate(
            key="F",
            scale_type="major",
            harmony_type="three_string_diatonic",
            scale_degree=5,
            chord_function="V",
            chord_name="C",
            chord_quality="major",
            fret=3,
            strings=(4, 6, 10),
            controls=("A", "B"),
            position_family="wide_ab",
            difficulty_tier="advanced",
        )
    ).to_dict()
    assert wide_ab["string_group"] == "4-6-10"
    assert wide_ab["notes"] == {"4": "G", "6": "C", "10": "E"}
    assert set(wide_ab["intervals"].values()) == {"1", "3", "5"}
    assert wide_ab["pedals"] == ["A", "B"]
    assert wide_ab["per_string_changes"] == {
        "6": {"from": "G#", "to": "A", "controls": "B"},
        "10": {"from": "B", "to": "C#", "controls": "A"},
    }
    assert "wide grip" in wide_ab["explanation_summary"]

    spread_bc = validate_explorer_candidate(
        ExplorerCandidate(
            key="F",
            scale_type="major",
            harmony_type="three_string_diatonic",
            scale_degree=5,
            chord_function="V",
            chord_name="C",
            chord_quality="major",
            fret=3,
            strings=(3, 5, 8),
            controls=("B", "C"),
            position_family="spread_bc",
            difficulty_tier="advanced",
        )
    ).to_dict()
    assert spread_bc["string_group"] == "3-5-8"
    assert spread_bc["notes"] == {"3": "C", "5": "E", "8": "G"}
    assert spread_bc["intervals"] == {"3": "1", "5": "3", "8": "5"}
    assert spread_bc["pedals"] == ["B", "C"]
    assert spread_bc["per_string_changes"] == {
        "3": {"from": "G#", "to": "A", "controls": "B"},
        "5": {"from": "B", "to": "C#", "controls": "C"},
    }
    assert "spread grip" in spread_bc["explanation_summary"]


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
