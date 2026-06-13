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
    e_lower_578_answer_for_question,
    e_lower_578_position_at_fret,
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
            "root",
            "quality",
            "positionKind",
            "fret",
            "strings",
            "grip",
            "pedals",
            "levers",
            "color",
            "role",
            "family",
            "tier",
            "colorRole",
            "visibleByDefault",
            "sortOrder",
            "notes",
            "intervals",
            "omittedIntervals",
            "isFullChord",
            "isPartial",
            "isRootless",
            "caveats",
            "validationStatus",
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
        assert position["family"]
        assert position["root"]
        assert position["quality"]
        assert position["positionKind"]
        assert position["tier"] in {"beginner", "common", "alternate", "advanced", "reference"}
        assert position["colorRole"]
        assert isinstance(position["visibleByDefault"], bool)
        assert isinstance(position["sortOrder"], int)
        assert isinstance(position["notes"], dict)
        assert isinstance(position["intervals"], dict)
        assert isinstance(position["omittedIntervals"], list)
        assert isinstance(position["isFullChord"], bool)
        assert isinstance(position["isPartial"], bool)
        assert isinstance(position["isRootless"], bool)
        assert isinstance(position["caveats"], list)
        assert position["validationStatus"] == "pitch_validated"
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
    by_id = {position["id"]: position for position in payload["positions"]}

    assert payload["title"] == "G major positions on E9"
    assert {"g-open-3", "g-af-6", "g-ab-10"}.issubset(ids)
    assert by_id["g-open-3"]["label"] == "G major"
    assert by_id["g-open-3"]["root"] == "G"
    assert by_id["g-open-3"]["quality"] == "major"
    assert by_id["g-open-3"]["positionKind"] == "starter"
    assert by_id["g-open-3"]["fret"] == 3
    assert by_id["g-open-3"]["strings"] == [4, 5, 6]
    assert by_id["g-open-3"]["pedals"] == []
    assert by_id["g-open-3"]["levers"] == []
    assert by_id["g-open-3"]["family"] == "open_no_pedals"
    assert by_id["g-open-3"]["visibleByDefault"] is True
    assert by_id["g-open-3"]["notes"] == {"4": "G", "5": "D", "6": "B"}
    assert by_id["g-open-3"]["intervals"] == {"4": "1", "5": "5", "6": "3"}
    assert by_id["g-open-3"]["isFullChord"] is True
    assert by_id["g-open-3"]["isPartial"] is False
    assert by_id["g-open-3"]["isRootless"] is False
    assert by_id["g-af-6"]["fret"] == 6
    assert by_id["g-af-6"]["strings"] == [4, 5, 6]
    assert by_id["g-af-6"]["pedals"] == ["A"]
    assert by_id["g-af-6"]["levers"] == ["F"]
    assert by_id["g-af-6"]["role"] == "A+F position"
    assert by_id["g-ab-10"]["fret"] == 10
    assert by_id["g-ab-10"]["strings"] == [4, 5, 6]
    assert by_id["g-ab-10"]["pedals"] == ["A", "B"]
    assert by_id["g-ab-10"]["levers"] == []
    assert by_id["g-ab-10"]["role"] == "A+B position"
    assert by_id["g-e-lower-5-7-8-8"]["family"] == "e_lower_578"
    assert by_id["g-e-lower-5-7-8-8"]["visibleByDefault"] is False
    assert [highlight["id"] for highlight in payload["highlights"]] == ids


def test_major_chord_helper_functions_return_contract_data() -> None:
    positions = get_e9_major_chord_positions("G")
    payload = build_e9_major_chord_fretboard("G")

    assert {"g-open-3", "g-af-6", "g-ab-10"}.issubset({position["id"] for position in positions})
    assert {"g-open-3", "g-af-6", "g-ab-10"}.issubset({position["id"] for position in payload["positions"]})
    by_id = {position["id"]: position for position in payload["positions"]}
    assert by_id["g-af-6"]["levers"] == ["F"]
    assert by_id["g-ab-10"]["pedals"] == ["A", "B"]


def test_a_major_positions_are_transposed_safely() -> None:
    payload = get_fretboard_examples("major_positions", "A")
    by_id = {position["id"]: position for position in payload["positions"]}

    assert payload["title"] == "A major positions on E9"
    assert {"a-open-5", "a-af-8", "a-ab-12"}.issubset(by_id)
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
    assert by_id["a-e-lower-5-7-8-10"]["family"] == "e_lower_578"


def test_b_major_positions_are_transposed_safely() -> None:
    payload = get_fretboard_examples("major_positions", "B")
    by_id = {position["id"]: position for position in payload["positions"]}

    assert payload["title"] == "B major positions on E9"
    assert {"b-open-7", "b-af-10", "b-ab-14", "b-ab-2-lower-octave"}.issubset(by_id)
    assert by_id["b-open-7"]["fret"] == 7
    assert by_id["b-open-7"]["pedals"] == []
    assert by_id["b-open-7"]["levers"] == []
    assert by_id["b-af-10"]["fret"] == 10
    assert by_id["b-af-10"]["pedals"] == ["A"]
    assert by_id["b-af-10"]["levers"] == ["F"]
    assert by_id["b-ab-14"]["fret"] == 14
    assert by_id["b-ab-14"]["pedals"] == ["A", "B"]
    assert by_id["b-ab-2-lower-octave"]["fret"] == 2
    assert by_id["b-ab-2-lower-octave"]["pedals"] == ["A", "B"]
    assert by_id["b-ab-2-lower-octave"]["levers"] == []
    assert by_id["b-ab-2-lower-octave"]["tier"] == "alternate"
    assert by_id["b-ab-2-lower-octave"]["visibleByDefault"] is False
    assert by_id["b-e-lower-5-7-8-0"]["fret"] == 0
    assert by_id["b-e-lower-5-7-8-0"]["strings"] == [5, 7, 8]
    assert by_id["b-e-lower-5-7-8-0"]["levers"] == ["E"]
    assert by_id["b-e-lower-5-7-8-0"]["family"] == "e_lower_578"
    assert by_id["b-e-lower-5-7-8-0"]["tier"] == "advanced"
    assert by_id["b-e-lower-5-7-8-0"]["visibleByDefault"] is False
    assert [position["id"] for position in payload["positions"] if position["visibleByDefault"]] == [
        "b-open-7",
        "b-af-10",
        "b-ab-14",
    ]


def test_b_sharp_major_positions_normalize_to_c_major() -> None:
    request = major_chord_location_request_for_question("How do I play a B# chord?")
    assert request is not None
    assert request.requested_root == "B#"
    assert request.normalized_key == "C"
    assert request.is_enharmonic is True

    payload = fretboard_payload_for_question("How do I play a B# chord?")
    assert payload["title"] == "C major positions on E9"
    by_id = {position["id"]: position for position in payload["positions"]}
    assert {"c-open-8", "c-af-11", "c-ab-15"}.issubset(by_id)
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


@pytest.mark.parametrize(
    ("requested_key", "normalized_key", "expected"),
    [
        ("G", "G", {"open": ("g-open-3", 3, [], []), "af": ("g-af-6", 6, ["A"], ["F"]), "ab": ("g-ab-10", 10, ["A", "B"], [])}),
        ("A", "A", {"open": ("a-open-5", 5, [], []), "af": ("a-af-8", 8, ["A"], ["F"]), "ab": ("a-ab-12", 12, ["A", "B"], [])}),
        ("B", "B", {"open": ("b-open-7", 7, [], []), "af": ("b-af-10", 10, ["A"], ["F"]), "ab": ("b-ab-14", 14, ["A", "B"], [])}),
        ("C#", "C#", {"open": ("csharp-open-9", 9, [], []), "af": ("csharp-af-12", 12, ["A"], ["F"]), "ab": ("csharp-ab-16", 16, ["A", "B"], [])}),
        ("B#", "C", {"open": ("c-open-8", 8, [], []), "af": ("c-af-11", 11, ["A"], ["F"]), "ab": ("c-ab-15", 15, ["A", "B"], [])}),
    ],
)
def test_generated_major_positions_lock_requested_roots_metadata_and_pitch_annotations(
    requested_key: str,
    normalized_key: str,
    expected: dict[str, tuple[str, int, list[str], list[str]]],
) -> None:
    payload = get_fretboard_examples("major_positions", requested_key)
    by_id = {position["id"]: position for position in payload["positions"]}

    assert_valid_visualization_payload(payload)
    assert payload["key"] == normalized_key
    assert payload["title"] == f"{normalized_key} major positions on E9"

    visible_ids = [position["id"] for position in payload["positions"] if position["visibleByDefault"]]
    assert visible_ids == [expected["open"][0], expected["af"][0], expected["ab"][0]]

    for role, (position_id, fret, pedals, levers) in expected.items():
        position = by_id[position_id]
        assert position["root"] == normalized_key
        assert position["quality"] == "major"
        assert position["fret"] == fret
        assert position["strings"] == [4, 5, 6]
        assert position["pedals"] == pedals
        assert position["levers"] == levers
        assert position["notes"]
        assert set(position["intervals"].values()) == {"1", "3", "5"}
        assert position["omittedIntervals"] == []
        assert position["isFullChord"] is True
        assert position["isPartial"] is False
        assert position["isRootless"] is False
        assert position["validationStatus"] == "pitch_validated"
        assert position["family"] in {"open_no_pedals", "a_f", "a_b"}
        assert position["tier"] == "beginner"
        assert isinstance(position["sortOrder"], int)
        assert "x" not in position
        assert "y" not in position

    if requested_key == "B":
        alternate = by_id["b-ab-2-lower-octave"]
        assert alternate["fret"] == 2
        assert alternate["pedals"] == ["A", "B"]
        assert alternate["levers"] == []
        assert alternate["visibleByDefault"] is False
        assert alternate["sortOrder"] > by_id["b-ab-14"]["sortOrder"]


def test_c_major_position_prompts_are_supported() -> None:
    expected_ids = ["c-open-8", "c-af-11", "c-ab-15"]

    assert set(expected_ids).issubset({position["id"] for position in fretboard_payload_for_question("Where can I play a C chord?")["positions"]})
    assert fretboard_payload_for_question("Where is C major?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Show me C positions.")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("What frets give me a C chord?")["title"] == "C major positions on E9"


def test_c_sharp_major_position_prompts_are_supported() -> None:
    expected_ids = ["csharp-open-9", "csharp-af-12", "csharp-ab-16"]

    assert set(expected_ids).issubset({position["id"] for position in fretboard_payload_for_question("How do I play a C#?")["positions"]})
    assert fretboard_payload_for_question("How do I play a C# chord?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Where can I play a C# chord?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Where is C# major?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me C# positions.")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me places to play C# major.")["title"] == "C# major positions on E9"


def test_b_major_position_prompt_variants_are_supported() -> None:
    expected_ids = {"b-open-7", "b-af-10", "b-ab-14", "b-ab-2-lower-octave", "b-e-lower-5-7-8-0"}

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
        "Show me more B chord positions.",
        "Show me advanced B chord positions.",
        "Show me B chord positions with levers.",
        "What grips can I use for B major?",
    ]
    for question in variants:
        payload = fretboard_payload_for_question(question)
        assert payload["title"] == "B major positions on E9", question
        assert expected_ids.issubset({position["id"] for position in payload["positions"]})


def test_b_major_expanded_catalog_has_beginner_visible_defaults_and_hidden_alternate() -> None:
    payload = fretboard_payload_for_question("Where all can I play a B chord?")
    positions = payload["positions"]
    by_id = {position["id"]: position for position in positions}

    assert len(positions) > 3
    assert by_id["b-ab-2-lower-octave"]["fret"] == 2
    assert by_id["b-ab-2-lower-octave"]["pedals"] == ["A", "B"]
    assert by_id["b-ab-2-lower-octave"]["tier"] == "alternate"
    assert by_id["b-ab-2-lower-octave"]["visibleByDefault"] is False
    assert by_id["b-e-lower-5-7-8-0"]["fret"] == 0
    assert by_id["b-e-lower-5-7-8-0"]["grip"] == "5-7-8"
    assert by_id["b-e-lower-5-7-8-0"]["levers"] == ["E"]
    assert by_id["b-e-lower-5-7-8-0"]["family"] == "e_lower_578"
    assert by_id["b-e-lower-5-7-8-0"]["caveats"] == ["Assumes E-lower lowers strings 4 and 8 E to D#/Eb."]
    assert [(position["fret"], position["pedals"], position["levers"]) for position in positions if position["visibleByDefault"]] == [
        (7, [], []),
        (10, ["A"], ["F"]),
        (14, ["A", "B"], []),
    ]
    assert [position["sortOrder"] for position in positions] == sorted(position["sortOrder"] for position in positions)
    first_grip_order: list[str] = []
    for position in positions:
        if position["family"] not in {"open_grip", "open_no_pedals", "e_lower_578"}:
            continue
        if position["grip"] not in first_grip_order:
            first_grip_order.append(position["grip"])
    assert first_grip_order == ["3-4-5", "4-5-6", "5-6-8", "5-7-8", "6-8-10"]
    assert [position["fret"] for position in positions if position["family"] == "e_lower_578"] == [0, 12]


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

    assert COMMON_E9_VISUAL_GRIPS == ((3, 4, 5), (4, 5, 6), (5, 6, 8), (5, 7, 8), (6, 8, 10))
    assert strings == list(COMMON_E9_VISUAL_GRIPS)
    assert [position["id"] for position in payload["positions"]] == [
        "g-grip-3-4-5-3",
        "g-grip-4-5-6-3",
        "g-grip-5-6-8-3",
        "g-grip-5-7-8-3",
        "g-grip-6-8-10-3",
    ]


def test_e_lower_5_7_8_is_classified_by_pitch_math() -> None:
    payload = fretboard_payload_for_question("What does 5-7-8 with E lowered give me at the 3rd fret?")
    assert payload is not None
    assert payload["title"] == "5-7-8 with E-lower at fret 3"
    position = payload["positions"][0]

    assert position["id"] == "d-e-lower-5-7-8-3"
    assert position["root"] == "D"
    assert position["quality"] == "major"
    assert position["fret"] == 3
    assert position["strings"] == [5, 7, 8]
    assert position["grip"] == "5-7-8"
    assert position["levers"] == ["E"]
    assert position["notes"] == {"5": "D", "7": "A", "8": "F#"}
    assert position["intervals"] == {"5": "1", "7": "5", "8": "3"}
    assert position["omittedIntervals"] == []
    assert position["isFullChord"] is True
    assert position["isPartial"] is False
    assert position["isRootless"] is False
    assert position["validationStatus"] == "pitch_validated"


def test_e_lower_5_7_8_at_third_fret_is_not_misclassified_as_b9() -> None:
    position = e_lower_578_position_at_fret(3)
    answer = e_lower_578_answer_for_question("What does 5-7-8 with E lowered give me at the 3rd fret?")

    assert position.root == "D"
    assert position.quality == "major"
    assert position.notes == {"5": "D", "7": "A", "8": "F#"}
    assert position.intervals == {"5": "1", "7": "5", "8": "3"}
    assert position.omitted_intervals == ()
    assert position.is_full_chord is True
    assert position.is_partial is False
    assert position.is_rootless is False
    assert "D major" in answer
    assert "rootless B minor 7 color" in answer
    assert "B9" not in answer
    assert "dominant 9" not in answer
    assert fretboard_payload_for_question("Is 5-7-8 with E lowered a B9 pocket?") is None


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
    assert {"a-open-5", "a-af-8", "a-ab-12"}.issubset(
        {position["id"] for position in fretboard_payload_for_question("Where can I play an A chord?")["positions"]}
    )
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
