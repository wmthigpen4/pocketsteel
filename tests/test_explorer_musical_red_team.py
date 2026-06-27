from __future__ import annotations

from pocketsteel.e9_copedents import (
    CUSTOM_LKV_COPEDENT_ID,
    DAY_COPEDENT_ID,
    DEFAULT_COPEDENT_ID,
    selected_copedent_payload,
)
from pocketsteel.fretboard_explorer import (
    build_control_impact_preview,
    interval_label,
    resolve_notes,
)


def test_red_team_string_pitch_math_and_string_aware_controls() -> None:
    assert resolve_notes(3, (3,), ()) == {"3": "B"}
    assert resolve_notes(3, (3,), ("B",)) == {"3": "C"}
    assert resolve_notes(3, (5,), ()) == {"5": "D"}
    assert resolve_notes(3, (5,), ("A",)) == {"5": "E"}
    assert resolve_notes(3, (9,), ()) == {"9": "F"}

    assert resolve_notes(3, (4, 6, 10), ("A", "B")) == {
        "4": "G",
        "6": "C",
        "10": "E",
    }


def test_red_team_major_seven_color_is_not_created_by_ninth_string_alone() -> None:
    five_six_nine = resolve_notes(3, (5, 6, 9), ("A", "B"))
    assert five_six_nine == {"5": "E", "6": "C", "9": "F"}
    assert {string: interval_label("F", note) for string, note in five_six_nine.items()} == {
        "5": "7",
        "6": "5",
        "9": "1",
    }

    five_seven_nine = resolve_notes(3, (5, 7, 9), ("A", "B"))
    assert five_seven_nine == {"5": "E", "7": "A", "9": "F"}
    assert {string: interval_label("F", note) for string, note in five_seven_nine.items()} == {
        "5": "7",
        "7": "3",
        "9": "1",
    }

    dominant_color = resolve_notes(1, (3, 4, 9), ())
    assert dominant_color == {"3": "A", "4": "F", "9": "D#"}
    assert {string: interval_label("F", note) for string, note in dominant_color.items()} == {
        "3": "3",
        "4": "1",
        "9": "b7",
    }


def test_red_team_control_impact_preview_keeps_changes_string_aware() -> None:
    preview = build_control_impact_preview("G")
    controls = {control["id"]: control for control in preview["controls"]}

    assert controls["A"]["affected_strings"] == [5, 10]
    assert controls["B"]["affected_strings"] == [3, 6]
    assert controls["C"]["affected_strings"] == [4, 5]
    assert controls["E-raise"]["affected_strings"] == [4, 8]
    assert controls["E-lower"]["affected_strings"] == [4, 8]
    assert controls["D-lower"]["affected_strings"] == [2, 9]
    assert controls["G-lower"]["affected_strings"] == [1, 6]

    assert {impact["string"] for impact in controls["A"]["string_impacts"]} == {5, 10}
    assert {impact["string"] for impact in controls["B"]["string_impacts"]} == {3, 6}
    assert {impact["string"] for impact in controls["E-raise"]["string_impacts"]} == {4, 8}


def test_red_team_copedent_profiles_keep_custom_lkv_isolated() -> None:
    emmons = selected_copedent_payload(DEFAULT_COPEDENT_ID)
    day = selected_copedent_payload(DAY_COPEDENT_ID)
    custom = selected_copedent_payload(CUSTOM_LKV_COPEDENT_ID)

    assert [column["id"] for column in day["chart"]["columns"][:3]] == ["C", "B", "A"]
    assert "B-to-Bb" not in [column["id"] for column in emmons["chart"]["columns"]]
    assert "B-to-Bb" not in [column["id"] for column in day["chart"]["columns"]]
    assert "B-to-Bb" in [column["id"] for column in custom["chart"]["columns"]]
