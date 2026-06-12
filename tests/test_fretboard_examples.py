from __future__ import annotations

import pytest

from pocketsteel.fretboard_examples import (
    CANONICAL_LEVER_LABELS,
    CANONICAL_PEDAL_LABELS,
    COMMON_E9_VISUAL_GRIPS,
    DEFAULT_PEDAL_LEVER_LABELS,
    E9_OPEN_STRINGS,
    FRETBOARD_PAYLOAD_TYPE,
    build_e9_major_chord_fretboard,
    fretboard_payload_for_question,
    get_fretboard_examples,
    get_e9_major_chord_positions,
    major_chord_location_request_for_question,
    validate_fretboard_payload,
)


def assert_valid_visualization_payload(payload: dict) -> None:
    assert {
        "type",
        "title",
        "subtitle",
        "description",
        "tuning",
        "copedent",
        "key",
        "strings",
        "positions",
        "highlights",
        "legend",
        "notes",
        "warnings",
        "sourceContext",
    }.issubset(payload)
    assert payload["type"] == FRETBOARD_PAYLOAD_TYPE
    assert isinstance(payload["title"], str) and payload["title"]
    assert isinstance(payload["description"], str) and payload["description"]
    assert payload["description"] == payload["subtitle"]
    assert payload["tuning"] == "E9"
    assert payload["strings"]["count"] == 10
    assert payload["strings"]["labels"]["1"] == "F#"
    assert isinstance(payload["positions"], list)
    assert payload["positions"]
    assert isinstance(payload["highlights"], list)
    assert payload["highlights"]
    validate_fretboard_payload(payload)
    assert [position["id"] for position in payload["positions"]] == [
        highlight["id"] for highlight in payload["highlights"]
    ]
    for position in payload["positions"]:
        assert {
            "id",
            "label",
            "fret",
            "strings",
            "grip",
            "pedals",
            "levers",
            "color",
            "role",
        }.issubset(position)
        assert isinstance(position["id"], str) and position["id"]
        assert isinstance(position["label"], str) and position["label"]
        assert isinstance(position["role"], str)
        assert 0 <= position["fret"] <= 24
        assert position["strings"]
        assert all(1 <= string <= 10 for string in position["strings"])
        assert position["grip"] == "-".join(str(string) for string in position["strings"])
        assert all(label in CANONICAL_PEDAL_LABELS for label in position["pedals"])
        assert all(label in CANONICAL_LEVER_LABELS for label in position["levers"])
        assert "x" not in position
        assert "y" not in position
    for highlight in payload["highlights"]:
        assert set(highlight) == {"id", "label", "fret", "strings", "pedals", "levers", "role"}
        assert all(label in DEFAULT_PEDAL_LEVER_LABELS for label in highlight["pedals"])
        assert all(label in DEFAULT_PEDAL_LEVER_LABELS for label in highlight["levers"])


def test_e9_constants_and_user_facing_labels() -> None:
    assert E9_OPEN_STRINGS == {
        1: "F#",
        2: "D#",
        3: "G#",
        4: "E",
        5: "B",
        6: "G#",
        7: "F#",
        8: "E",
        9: "D",
        10: "B",
    }
    assert DEFAULT_PEDAL_LEVER_LABELS == (
        "A",
        "B",
        "C",
        "F",
        "E",
        "G+",
        "G-",
        "D-",
        "D--",
        "V",
    )


@pytest.mark.parametrize(
    ("intent", "key"),
    [
        ("major_positions", "G"),
        ("major_positions", "C"),
        ("major_positions", "C#"),
        ("minor_grips", "G"),
        ("i_iv_v", "G"),
        ("i_iv_v", "C"),
        ("i_iv_v", "C#"),
        ("common_grips", "G"),
    ],
)
def test_fretboard_examples_return_valid_payloads(intent: str, key: str) -> None:
    assert_valid_visualization_payload(get_fretboard_examples(intent, key))


def test_g_major_positions_have_stable_ids_and_roles() -> None:
    payload = get_fretboard_examples("major_positions", "G")
    ids = [position["id"] for position in payload["positions"]]

    assert payload["title"] == "G major positions on E9"
    assert ids == ["g-open-3", "g-af-6", "g-ab-10"]
    assert payload["positions"][0] == {
        "id": "g-open-3",
        "label": "G major",
        "fret": 3,
        "strings": [4, 5, 6],
        "grip": "4-5-6",
        "pedals": [],
        "levers": [],
        "color": "primary",
        "role": "Open position",
        "notes": {"4": "G", "5": "D", "6": "B"},
        "intervals": {"4": "1", "5": "5", "6": "3"},
        "explanation": "No-pedal fret 3 gives a G major grip on strings 4-5-6.",
    }
    assert payload["positions"][1]["fret"] == 6
    assert payload["positions"][1]["strings"] == [4, 5, 6]
    assert payload["positions"][1]["pedals"] == ["A"]
    assert payload["positions"][1]["levers"] == ["F"]
    assert payload["positions"][1]["role"] == "A+F position"
    assert payload["positions"][2]["fret"] == 10
    assert payload["positions"][2]["strings"] == [4, 5, 6]
    assert payload["positions"][2]["pedals"] == ["A", "B"]
    assert payload["positions"][2]["levers"] == []
    assert payload["positions"][2]["role"] == "A+B position"
    assert [highlight["id"] for highlight in payload["highlights"]] == ids


def test_major_chord_helper_functions_return_contract_data() -> None:
    positions = get_e9_major_chord_positions("G")
    payload = build_e9_major_chord_fretboard("G")

    assert [position["id"] for position in positions] == ["g-open-3", "g-af-6", "g-ab-10"]
    assert [position["id"] for position in payload["positions"]] == ["g-open-3", "g-af-6", "g-ab-10"]
    assert payload["positions"][1]["levers"] == ["F"]
    assert payload["positions"][2]["pedals"] == ["A", "B"]


def test_a_major_positions_are_transposed_safely() -> None:
    payload = get_fretboard_examples("major_positions", "A")
    by_id = {position["id"]: position for position in payload["positions"]}

    assert payload["title"] == "A major positions on E9"
    assert [position["id"] for position in payload["positions"]] == ["a-open-5", "a-af-8", "a-ab-12"]
    assert by_id["a-open-5"]["fret"] == 5
    assert by_id["a-open-5"]["strings"] == [4, 5, 6]
    assert by_id["a-open-5"]["pedals"] == []
    assert by_id["a-open-5"]["levers"] == []
    assert by_id["a-af-8"]["fret"] == 8
    assert by_id["a-af-8"]["strings"] == [4, 5, 6]
    assert by_id["a-af-8"]["pedals"] == ["A"]
    assert by_id["a-af-8"]["levers"] == ["F"]
    assert by_id["a-ab-12"]["fret"] == 12
    assert by_id["a-ab-12"]["strings"] == [4, 5, 6]
    assert by_id["a-ab-12"]["pedals"] == ["A", "B"]
    assert by_id["a-ab-12"]["levers"] == []


def test_b_major_positions_are_transposed_safely() -> None:
    payload = get_fretboard_examples("major_positions", "B")
    by_id = {position["id"]: position for position in payload["positions"]}

    assert payload["title"] == "B major positions on E9"
    assert [position["id"] for position in payload["positions"]] == ["b-open-7", "b-af-10", "b-ab-14"]
    assert by_id["b-open-7"]["fret"] == 7
    assert by_id["b-open-7"]["pedals"] == []
    assert by_id["b-open-7"]["levers"] == []
    assert by_id["b-af-10"]["fret"] == 10
    assert by_id["b-af-10"]["pedals"] == ["A"]
    assert by_id["b-af-10"]["levers"] == ["F"]
    assert by_id["b-ab-14"]["fret"] == 14
    assert by_id["b-ab-14"]["pedals"] == ["A", "B"]


def test_b_sharp_major_positions_normalize_to_c_major() -> None:
    request = major_chord_location_request_for_question("How do I play a B# chord?")
    assert request is not None
    assert request.requested_root == "B#"
    assert request.normalized_key == "C"
    assert request.is_enharmonic is True

    payload = fretboard_payload_for_question("How do I play a B# chord?")
    assert payload["title"] == "C major positions on E9"
    by_id = {position["id"]: position for position in payload["positions"]}
    assert [position["id"] for position in payload["positions"]] == ["c-open-8", "c-af-11", "c-ab-15"]
    assert by_id["c-open-8"]["fret"] == 8
    assert by_id["c-open-8"]["strings"] == [4, 5, 6]
    assert by_id["c-open-8"]["pedals"] == []
    assert by_id["c-open-8"]["levers"] == []
    assert by_id["c-af-11"]["fret"] == 11
    assert by_id["c-af-11"]["pedals"] == ["A"]
    assert by_id["c-af-11"]["levers"] == ["F"]
    assert by_id["c-ab-15"]["fret"] == 15
    assert by_id["c-ab-15"]["pedals"] == ["A", "B"]
    assert by_id["c-ab-15"]["levers"] == []


def test_c_major_position_prompts_are_supported() -> None:
    expected_ids = ["c-open-8", "c-af-11", "c-ab-15"]

    assert [position["id"] for position in fretboard_payload_for_question("Where can I play a C chord?")["positions"]] == expected_ids
    assert fretboard_payload_for_question("Where is C major?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Show me C positions.")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("What frets give me a C chord?")["title"] == "C major positions on E9"


def test_c_sharp_major_position_prompts_are_supported() -> None:
    expected_ids = ["csharp-open-9", "csharp-af-12", "csharp-ab-16"]

    assert [position["id"] for position in fretboard_payload_for_question("How do I play a C#?")["positions"]] == expected_ids
    assert fretboard_payload_for_question("How do I play a C# chord?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Where can I play a C# chord?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Where is C# major?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me C# positions.")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me places to play C# major.")["title"] == "C# major positions on E9"


def test_b_major_position_prompt_variants_are_supported() -> None:
    expected_ids = ["b-open-7", "b-af-10", "b-ab-14"]

    variants = [
        "Where can I play a B chord?",
        "Where all can I play a B chord?",
        "Where can I find B?",
        "Where is B major?",
        "How do I play a B chord?",
        "How do I make a B chord?",
        "Show me B positions.",
        "Show me places to play B major.",
        "What frets give me B?",
        "Where is B on E9?",
    ]
    for question in variants:
        payload = fretboard_payload_for_question(question)
        assert payload["title"] == "B major positions on E9", question
        assert [position["id"] for position in payload["positions"]] == expected_ids


def test_i_iv_v_examples_in_requested_keys_are_stable() -> None:
    g_payload = get_fretboard_examples("i_iv_v", "G")
    c_payload = get_fretboard_examples("i_iv_v", "C")
    csharp_payload = get_fretboard_examples("i_iv_v", "C#")

    assert [item["id"] for item in g_payload["positions"]] == [
        "g-i-open-3",
        "c-iv-ab-3",
        "d-v-ab-5",
    ]
    assert [item["label"] for item in c_payload["positions"]] == [
        "C major",
        "F major",
        "G major",
    ]
    assert [item["id"] for item in csharp_payload["positions"]] == [
        "csharp-i-open-9",
        "fsharp-iv-ab-9",
        "gsharp-v-ab-11",
    ]


def test_common_grips_match_mvp_list() -> None:
    payload = get_fretboard_examples("common_grips", "G")
    strings = [tuple(position["strings"]) for position in payload["positions"]]

    assert COMMON_E9_VISUAL_GRIPS == ((4, 5, 6), (3, 4, 5), (5, 6, 8), (6, 8, 10))
    assert strings == list(COMMON_E9_VISUAL_GRIPS)
    assert [position["id"] for position in payload["positions"]] == [
        "g-grip-4-5-6-3",
        "g-grip-3-4-5-3",
        "g-grip-5-6-8-3",
        "g-grip-6-8-10-3",
    ]


def test_aliases_and_validation_errors() -> None:
    assert get_fretboard_examples("major", "Gb")["title"] == "F# major positions on E9"
    assert get_fretboard_examples("1_4_5", "G")["title"] == "I-IV-V in G on E9"

    with pytest.raises(ValueError, match="Unsupported fretboard example intent"):
        get_fretboard_examples("full_chord_engine", "G")
    with pytest.raises(ValueError, match="Unsupported key"):
        get_fretboard_examples("major_positions", "H")


def test_fretboard_payload_for_question_matches_only_mvp_triggers() -> None:
    assert fretboard_payload_for_question("Where can I play a G chord?")["title"] == "G major positions on E9"
    assert fretboard_payload_for_question("Where can I play an A chord?")["title"] == "A major positions on E9"
    assert [position["id"] for position in fretboard_payload_for_question("Where can I play an A chord?")["positions"]] == [
        "a-open-5",
        "a-af-8",
        "a-ab-12",
    ]
    assert fretboard_payload_for_question("Where can I play an A major chord?")["title"] == "A major positions on E9"
    assert fretboard_payload_for_question("How do I play a C#?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me places to play an A major chord.")["title"] == "A major positions on E9"
    assert fretboard_payload_for_question("Show me places to play a G major chord.")["title"] == "G major positions on E9"
    assert fretboard_payload_for_question("Where are G major positions on E9?")["title"] == "G major positions on E9"
    assert fretboard_payload_for_question("Show me a 1-4-5 in G.")["title"] == "I-IV-V in G on E9"
    assert fretboard_payload_for_question("Show me common grips for G.")["title"] == "Common G major grips on E9"
    assert fretboard_payload_for_question("What are common Fender Steel King settings?") is None


def test_validation_rejects_raw_geometry_and_unknown_labels() -> None:
    payload = get_fretboard_examples("major_positions", "G")
    payload["positions"][0]["x"] = 42
    with pytest.raises(ValueError, match="Raw geometry"):
        validate_fretboard_payload(payload)

    payload = get_fretboard_examples("major_positions", "G")
    payload["positions"][1]["levers"] = ["E-raise/F"]
    with pytest.raises(ValueError, match="unknown lever"):
        validate_fretboard_payload(payload)
