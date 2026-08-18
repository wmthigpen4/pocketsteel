from __future__ import annotations

import pytest

from steel_guitar_rag.fretboard_examples import (
    CANONICAL_LEVER_LABELS,
    CANONICAL_PEDAL_LABELS,
    COMMON_E9_VISUAL_GRIPS,
    DEFAULT_PEDAL_LEVER_LABELS,
    E9_OPEN_STRINGS,
    FRETBOARD_PAYLOAD_TYPE,
    build_e9_major_chord_fretboard,
    chord_concept_answer_for_question,
    chord_concept_request_for_question,
    chord_symbol_from_chord_like_question,
    chord_symbol_guardrail_answer_for_question,
    e_lower_578_answer_for_question,
    e_lower_578_b9_answer_for_question,
    e_lower_578_position_at_fret,
    fretboard_payload_for_question,
    functional_pocket_answer_for_question,
    functional_pocket_payload_for_question,
    get_fretboard_examples,
    get_e9_major_chord_positions,
    e_lower_grip_answer_for_question,
    e_lower_grip_position_at_fret,
    major_chord_location_request_for_question,
    function_chord_request_for_question,
    minor_chord_answer_for_question,
    minor_chord_location_request_for_question,
    normalize_rootless_chord_quality_alias,
    rootless_chord_quality_answer_for_question,
    rootless_chord_quality_request_for_question,
    specific_major_grip_answer_for_question,
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
            "chordRoot",
            "chordQuality",
            "chordTones",
            "lowestSoundingNote",
            "lowestChordToneRole",
            "voicingType",
            "inversionLabel",
            "inversionExplanation",
            "root",
            "quality",
            "positionKind",
            "fret",
            "strings",
            "grip",
            "intervalsLowToHigh",
            "isRootPosition",
            "isInversion",
            "isPartialVoicing",
            "pedals",
            "levers",
            "color",
            "role",
            "function",
            "keyContext",
            "family",
            "tier",
            "colorRole",
            "visibleByDefault",
            "sortOrder",
            "notes",
            "intervals",
            "omittedIntervals",
            "addedIntervals",
            "isFullChord",
            "isPartial",
            "isRootless",
            "whyUseIt",
            "caveats",
            "validationStatus",
            "tierReason",
            "whenToUse",
            "soundCharacter",
            "movementUse",
            "resolutionUse",
            "forumEvidence",
            "forumEvidenceStatus",
            "explanationShort",
            "explanationLong",
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
        assert isinstance(position["function"], str)
        assert isinstance(position["keyContext"], str)
        assert position["root"]
        assert position["quality"]
        assert position["chordRoot"] == position["root"]
        assert position["chordQuality"] == position["quality"]
        assert isinstance(position["chordTones"], list)
        assert all(isinstance(item, str) for item in position["chordTones"])
        assert isinstance(position["lowestSoundingNote"], str)
        assert isinstance(position["lowestChordToneRole"], str)
        assert position["voicingType"] in {
            "root_position",
            "first_inversion",
            "second_inversion",
            "third_inversion",
            "partial",
            "rootless",
            "color_voicing",
        }
        assert isinstance(position["inversionLabel"], str) and position["inversionLabel"]
        assert isinstance(position["inversionExplanation"], str) and position["inversionExplanation"]
        assert isinstance(position["intervalsLowToHigh"], list)
        assert all(isinstance(item, str) for item in position["intervalsLowToHigh"])
        assert isinstance(position["isRootPosition"], bool)
        assert isinstance(position["isInversion"], bool)
        assert isinstance(position["isPartialVoicing"], bool)
        assert position["positionKind"]
        assert position["tier"] in {"beginner", "common", "alternate", "advanced", "reference"}
        assert position["colorRole"]
        assert isinstance(position["visibleByDefault"], bool)
        assert isinstance(position["sortOrder"], int)
        assert isinstance(position["notes"], dict)
        assert isinstance(position["intervals"], dict)
        assert isinstance(position["omittedIntervals"], list)
        assert isinstance(position["addedIntervals"], list)
        assert isinstance(position["isFullChord"], bool)
        assert isinstance(position["isPartial"], bool)
        assert isinstance(position["isRootless"], bool)
        assert isinstance(position["whyUseIt"], str)
        assert isinstance(position["caveats"], list)
        assert position["validationStatus"] == "pitch_validated"
        assert isinstance(position["tierReason"], str) and position["tierReason"]
        assert isinstance(position["whenToUse"], str) and position["whenToUse"]
        assert isinstance(position["soundCharacter"], str) and position["soundCharacter"]
        assert isinstance(position["movementUse"], str) and position["movementUse"]
        assert isinstance(position["resolutionUse"], str) and position["resolutionUse"]
        assert isinstance(position["forumEvidence"], list)
        assert all(isinstance(item, str) for item in position["forumEvidence"])
        assert position["forumEvidenceStatus"] in {"not_found", "found", "not_searched"}
        assert isinstance(position["explanationShort"], str) and position["explanationShort"]
        assert isinstance(position["explanationLong"], str) and position["explanationLong"]
        for value in position.values():
            if isinstance(value, dict):
                assert all(isinstance(child, str) for child in value.values())
            elif isinstance(value, list):
                assert all(not isinstance(child, dict) for child in value)
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
    assert by_id["g-open-3"]["positionKind"] == "full_chord_position"
    assert by_id["g-open-3"]["fret"] == 3
    assert by_id["g-open-3"]["strings"] == [4, 5, 6]
    assert by_id["g-open-3"]["pedals"] == []
    assert by_id["g-open-3"]["levers"] == []
    assert by_id["g-open-3"]["family"] == "open_no_pedals"
    assert by_id["g-open-3"]["function"] == "I"
    assert by_id["g-open-3"]["keyContext"] == "G"
    assert by_id["g-open-3"]["visibleByDefault"] is True
    assert by_id["g-open-3"]["notes"] == {"4": "G", "5": "D", "6": "B"}
    assert by_id["g-open-3"]["intervals"] == {"4": "1", "5": "5", "6": "3"}
    assert by_id["g-open-3"]["isFullChord"] is True
    assert by_id["g-open-3"]["isPartial"] is False
    assert by_id["g-open-3"]["isRootless"] is False
    assert by_id["g-open-3"]["addedIntervals"] == []
    assert by_id["g-open-3"]["whyUseIt"]
    assert "Starter" in by_id["g-open-3"]["tierReason"]
    assert "straight-bar" in by_id["g-open-3"]["whenToUse"]
    assert "Complete G major" in by_id["g-open-3"]["soundCharacter"]
    assert by_id["g-open-3"]["forumEvidenceStatus"] == "not_found"
    assert by_id["g-open-3"]["forumEvidence"] == []
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


def test_g_major_voicing_metadata_identifies_root_position_and_inversions_by_pitch_order() -> None:
    payload = get_fretboard_examples("major_positions", "G")
    by_id = {position["id"]: position for position in payload["positions"]}

    root_position = by_id["g-open-grip-5-6-8-3"]
    assert root_position["grip"] == "5-6-8"
    assert root_position["lowestSoundingNote"] == "G"
    assert root_position["lowestChordToneRole"] == "root"
    assert root_position["voicingType"] == "root_position"
    assert root_position["inversionLabel"] == "Root position"
    assert root_position["isRootPosition"] is True
    assert root_position["isInversion"] is False
    assert root_position["isPartialVoicing"] is False
    assert root_position["intervalsLowToHigh"] == [
        "1 on string 8 (G)",
        "3 on string 6 (B)",
        "5 on string 5 (D)",
    ]

    first_inversion = by_id["g-open-3"]
    assert first_inversion["grip"] == "4-5-6"
    assert first_inversion["lowestSoundingNote"] == "B"
    assert first_inversion["lowestChordToneRole"] == "major 3rd"
    assert first_inversion["voicingType"] == "first_inversion"
    assert first_inversion["inversionLabel"] == "1st inversion"
    assert first_inversion["isRootPosition"] is False
    assert first_inversion["isInversion"] is True

    second_inversion = by_id["g-open-grip-3-4-5-3"]
    assert second_inversion["grip"] == "3-4-5"
    assert second_inversion["lowestSoundingNote"] == "D"
    assert second_inversion["lowestChordToneRole"] == "5th"
    assert second_inversion["voicingType"] == "second_inversion"
    assert second_inversion["inversionLabel"] == "2nd inversion"
    assert second_inversion["isInversion"] is True


def test_partial_and_rootless_voicings_are_labeled_for_filtering() -> None:
    payload = get_fretboard_examples("major_positions", "B")
    by_id = {position["id"]: position for position in payload["positions"]}

    partial = by_id["b-open-grip-5-7-8-7"]
    assert partial["grip"] == "5-7-8"
    assert partial["isPartial"] is True
    assert partial["isPartialVoicing"] is True
    assert partial["isRootless"] is False
    assert partial["voicingType"] == "partial"
    assert partial["inversionLabel"] == "Partial voicing"
    assert partial["chordTones"] == ["1 (root)", "5 (5th)"]
    assert partial["omittedIntervals"] == ["3"]

    rootless = by_id["b-e-lower-dominant-4-5-6-10"]
    assert rootless["quality"] == "dominant9"
    assert rootless["isRootless"] is True
    assert rootless["voicingType"] == "rootless"
    assert rootless["inversionLabel"] == "Rootless voicing"
    assert rootless["isRootPosition"] is False
    assert rootless["isInversion"] is False
    assert "omits the root" in rootless["inversionExplanation"]

    g_payload = get_fretboard_examples("major_positions", "G")
    g_by_id = {position["id"]: position for position in g_payload["positions"]}
    g_578 = g_by_id["g-open-grip-5-7-8-3"]
    assert g_578["label"] == "G5/add9 (no 3rd)"
    assert g_578["notes"] == {"5": "D", "7": "A", "8": "G"}
    assert g_578["intervals"] == {"5": "5", "7": "2/9", "8": "1"}
    assert g_578["omittedIntervals"] == ["3"]
    assert g_578["addedIntervals"] == ["2/9"]
    assert g_578["isFullChord"] is False
    assert g_578["isPartial"] is True
    assert g_578["visibleByDefault"] is False
    assert g_578["colorRole"] == "partial-rootless"
    assert any("partial/color voicing" in caveat for caveat in g_578["caveats"])


def test_common_grip_labels_remain_available_in_canonical_order() -> None:
    payload = get_fretboard_examples("major_positions", "G")
    first_fret_family = [
        position["grip"]
        for position in payload["positions"]
        if position["fret"] == 3 and position["family"] in {"open_no_pedals", "open_grip"}
    ]

    assert first_fret_family == ["3-4-5", "4-5-6", "5-6-8", "5-7-8", "6-8-10"]
    assert all(max(position["strings"]) <= 10 for position in payload["positions"])
    assert not any("11" in position["grip"] or "12" in position["grip"] for position in payload["positions"])


def test_c_major_position_prompts_are_supported() -> None:
    expected_ids = ["c-open-8", "c-af-11", "c-ab-15"]

    assert set(expected_ids).issubset({position["id"] for position in fretboard_payload_for_question("Where can I play a C chord?")["positions"]})
    assert set(expected_ids).issubset({position["id"] for position in fretboard_payload_for_question("Where are some places to play C chords?")["positions"]})
    assert fretboard_payload_for_question("Where can I play C chord?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Where can I play C major?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Where is C major?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Show me C positions.")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("What frets give me a C chord?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("What frets give me C major?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Which frets are C major on E9?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("Where do I find C major positions?")["title"] == "C major positions on E9"


def test_d_major_across_fretboard_position_prompts_are_supported() -> None:
    expected_ids = {
        "d-open-10",
        "d-af-13",
        "d-ab-17",
        "d-ab-5-lower-octave",
        "d-e-lower-5-7-8-3",
    }

    for question in [
        "How do I play a D chord across the fretboard of the E9?",
        "Show me D chord positions on E9.",
        "Where are D chord positions on E9?",
        "D major across the E9 fretboard",
    ]:
        request = major_chord_location_request_for_question(question)
        payload = fretboard_payload_for_question(question)

        assert request is not None, question
        assert request.normalized_key == "D"
        assert payload is not None, question
        assert payload["title"] == "D major positions on E9"
        assert_valid_visualization_payload(payload)
        by_id = {position["id"]: position for position in payload["positions"]}
        assert expected_ids.issubset(by_id)
        assert by_id["d-open-10"]["fret"] == 10
        assert by_id["d-ab-5-lower-octave"]["fret"] == 5
        assert by_id["d-e-lower-5-7-8-3"]["levers"] == ["E"]


def test_smoke_ready_chord_position_prompt_variants_are_supported() -> None:
    cases = [
        ("How do I play a G chord on the E9?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("Where can I play a G major chord on standard E9?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("Where do I play a G chord on the E9?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("Where the the G chords?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("How do I play an E chord on the E9 neck?", "E", {"e-open-0", "e-af-3", "e-ab-7"}),
        ("How do I play a B-flat chord on the E9 pedal steel?", "A#", {"asharp-open-6", "asharp-af-9", "asharp-ab-13"}),
        ("How do I play a Bb chord on E9?", "A#", {"asharp-open-6", "asharp-af-9", "asharp-ab-13"}),
        ("Where can I find B flat chords?", "A#", {"asharp-open-6", "asharp-af-9", "asharp-ab-13"}),
        ("What is the location for a G chord with A+B?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("How do I play a G chord on the 6th fret?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("How do I play a G chord across the guitar?", "G", {"g-open-3", "g-af-6", "g-ab-10"}),
        ("How do I play an A chord?", "A", {"a-open-5", "a-af-8", "a-ab-12"}),
        ("How do I play a D chord?", "D", {"d-open-10", "d-af-13", "d-ab-17"}),
    ]

    for question, expected_key, expected_ids in cases:
        request = major_chord_location_request_for_question(question)
        payload = fretboard_payload_for_question(question)

        assert request is not None, question
        assert request.normalized_key == expected_key
        assert payload is not None, question
        if "flat" in question.lower() or "bb" in question.lower():
            assert payload["title"] == "Bb major positions on E9"
        else:
            assert payload["title"] == f"{expected_key} major positions on E9"
        assert_valid_visualization_payload(payload)
        assert expected_ids.issubset({position["id"] for position in payload["positions"]})


def test_show_me_the_fretboard_returns_default_e9_reference_payload() -> None:
    payload = fretboard_payload_for_question("Show me the fretboard")

    assert payload is not None
    assert payload["title"] == "G major positions on E9"
    assert_valid_visualization_payload(payload)
    assert {"g-open-3", "g-af-6", "g-ab-10"}.issubset({position["id"] for position in payload["positions"]})


def test_c_sharp_major_position_prompts_are_supported() -> None:
    expected_ids = ["csharp-open-9", "csharp-af-12", "csharp-ab-16"]

    assert set(expected_ids).issubset({position["id"] for position in fretboard_payload_for_question("How do I play a C#?")["positions"]})
    assert fretboard_payload_for_question("How do I play a C# chord?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Where can I play a C# chord?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Where is C# major?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me C# positions.")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me places to play C# major.")["title"] == "C# major positions on E9"


def test_plan_typo_major_position_prompt_routes_to_deterministic_fretboard() -> None:
    request = major_chord_location_request_for_question("How do I plan an F chord?")
    payload = fretboard_payload_for_question("How do I plan an F chord?")

    assert request is not None
    assert request.requested_root == "F"
    assert request.normalized_key == "F"
    assert payload["title"] == "F major positions on E9"
    by_id = {position["id"]: position for position in payload["positions"]}
    assert {"f-open-1", "f-af-4", "f-ab-8"}.issubset(by_id)
    assert by_id["f-open-1"]["fret"] == 1
    assert by_id["f-af-4"]["fret"] == 4
    assert by_id["f-ab-8"]["fret"] == 8
    assert fretboard_payload_for_question("How do I plan my practice tonight?") is None


def test_function_and_direct_minor_questions_route_to_e_minor_positions() -> None:
    function_request = function_chord_request_for_question("I am in the key of G. Where can I play a 6m chord?")
    vi_request = function_chord_request_for_question("Show me the vi chord in G")
    direct_minor_request = minor_chord_location_request_for_question("Where is Em on E9?")

    assert function_request is not None
    assert function_request.key == "G"
    assert function_request.degree == 6
    assert function_request.root == "E"
    assert function_request.quality == "minor"
    assert vi_request is not None
    assert vi_request.root == "E"
    assert vi_request.quality == "minor"
    assert direct_minor_request is not None
    assert direct_minor_request.normalized_key == "E"

    for question in [
        "I am in the key of G. Where can I play a 6m chord?",
        "In G, where is the 6 minor?",
        "Where can I play the vi chord in G?",
        "Show me the 6m in G.",
        "Where is Em on E9?",
    ]:
        payload = fretboard_payload_for_question(question)
        assert payload is not None, question
        assert_valid_visualization_payload(payload)
        assert payload["title"] == "E minor positions on E9"
        by_id = {position["id"]: position for position in payload["positions"]}
        assert {
            "e-minor-a_pedal_minor-4-5-6-3",
            "e-minor-e_lower_minor-4-5-6-8",
            "e-minor-b_c_minor-4-5-6-10",
        }.issubset(by_id)
        assert [position["id"] for position in payload["positions"] if position["visibleByDefault"]] == [
            "e-minor-a_pedal_minor-4-5-6-3",
            "e-minor-e_lower_minor-4-5-6-8",
            "e-minor-b_c_minor-4-5-6-10",
        ]
        for position in by_id.values():
            assert position["root"] == "E"
            assert position["quality"] == "minor"
            assert position["validationStatus"] == "pitch_validated"
            assert set(position["intervals"].values()) == {"1", "b3", "5"}


def test_hyphenated_minor_chord_questions_route_to_minor_positions() -> None:
    direct_minor_request = minor_chord_location_request_for_question("How do I play a G-minor chord?")

    assert direct_minor_request is not None
    assert direct_minor_request.normalized_key == "G"

    payload = fretboard_payload_for_question("How do I play a G-minor chord?")
    assert payload is not None
    assert payload["title"] == "G minor positions on E9"
    assert_valid_visualization_payload(payload)


def test_mixed_a_minor_c_major_payload_combines_pitch_validated_positions() -> None:
    payload = fretboard_payload_for_question("Show me A minor and C major chords.")

    assert payload is not None
    assert payload["title"] == "A minor and C major positions on E9"
    assert_valid_visualization_payload(payload)
    labels = " ".join(position["label"] for position in payload["positions"])
    assert "A minor" in labels
    assert "C major" in labels
    assert any(position["root"] == "A" and position["quality"] == "minor" for position in payload["positions"])
    assert any(position["root"] == "C" and position["quality"] == "major" for position in payload["positions"])


def test_natural_language_chord_intent_variants_route_to_pitch_payloads() -> None:
    major_cases = {
        "Where can I find D# chords on the pedal steel E9?": ("D#", "D# major positions on E9"),
        "Where can I find Eb chords on E9?": ("D#", "Eb major positions on E9"),
        "Where are D sharp chords on pedal steel?": ("D#", "D# major positions on E9"),
        "How in the hell do you play a C major chord?": ("C", "C major positions on E9"),
        "Show me C major.": ("C", "C major positions on E9"),
        "Give me C chord positions.": ("C", "C major positions on E9"),
        "Where is C on the fretboard?": ("C", "C major positions on E9"),
    }
    for question, (normalized_key, title) in major_cases.items():
        request = major_chord_location_request_for_question(question)
        payload = fretboard_payload_for_question(question)

        assert request is not None, question
        assert request.normalized_key == normalized_key
        assert payload is not None
        assert payload["title"] == title
        assert_valid_visualization_payload(payload)

    minor_cases = {
        "How do I play a D-sharp minor on E9?": ("D#", "D# minor positions on E9"),
        "How do I play D sharp minor?": ("D#", "D# minor positions on E9"),
        "How do I play uh A minor on E9?": ("A", "A minor positions on E9"),
        "What's a B minor look like?": ("B", "B minor positions on E9"),
        "What does B minor look like on E9?": ("B", "B minor positions on E9"),
    }
    for question, (normalized_key, title) in minor_cases.items():
        request = minor_chord_location_request_for_question(question)
        payload = fretboard_payload_for_question(question)

        assert request is not None, question
        assert request.normalized_key == normalized_key
        assert payload is not None
        assert payload["title"] == title
        assert_valid_visualization_payload(payload)


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


def test_g_major_expanded_catalog_includes_pitch_valid_common_grips_and_e_lower_positions() -> None:
    payload = fretboard_payload_for_question("Where all can I play a G chord?")
    positions = payload["positions"]
    by_id = {position["id"]: position for position in positions}

    assert {"g-open-3", "g-af-6", "g-ab-10"}.issubset(by_id)
    assert [position["id"] for position in positions if position["visibleByDefault"]] == [
        "g-open-3",
        "g-af-6",
        "g-ab-10",
    ]
    assert len(positions) > 3
    assert {"g-open-15-octave", "g-af-18-octave", "g-ab-22-octave"}.issubset(by_id)

    open_grips = [
        position["grip"]
        for position in positions
        if position["family"] in {"open_grip", "open_no_pedals"} and position["fret"] == 3
    ]
    assert open_grips == ["3-4-5", "4-5-6", "5-6-8", "5-7-8", "6-8-10"]
    assert not any(position["grip"] == "5-7-8" and position["pedals"] == ["A", "B"] for position in positions)
    g_578 = by_id["g-open-grip-5-7-8-3"]
    assert g_578["label"] == "G5/add9 (no 3rd)"
    assert g_578["isFullChord"] is False
    assert g_578["visibleByDefault"] is False
    assert g_578["omittedIntervals"] == ["3"]
    assert g_578["addedIntervals"] == ["2/9"]

    e_lower_full = {
        (position["fret"], position["grip"])
        for position in positions
        if position["family"] in {"e_lower_578", "e_lower_major"} and position["isFullChord"]
    }
    assert {
        (8, "5-7-8"),
        (8, "7-8-10"),
        (8, "4-5-7"),
        (8, "1-4-5"),
        (20, "5-7-8"),
        (20, "7-8-10"),
        (20, "4-5-7"),
        (20, "1-4-5"),
    } <= e_lower_full

    dominant_pockets = [
        position for position in positions if position["family"] == "e_lower_dominant_pocket"
    ]
    assert dominant_pockets
    assert all(position["positionKind"] == "rootless_voicing" for position in dominant_pockets)


def test_specific_g_578_static_grip_routes_as_partial_color_not_plain_major() -> None:
    for question in ["Show me a 5-7-8 G grip.", "Show me a G chord on strings 5-7-8."]:
        payload = fretboard_payload_for_question(question)
        answer = specific_major_grip_answer_for_question(question)

        assert answer is not None
        assert "Not as a full plain G major grip" in answer
        assert "partial/color sound" in answer
        assert "Omitted from the plain major triad: 3" in answer
        assert payload is not None
        assert payload["title"] == "G grip 5-7-8 on E9"
        position = payload["positions"][0]
        assert position["id"] == "g-grip-5-7-8-3"
        assert position["label"] == "G5/add9 (no 3rd)"
        assert position["notes"] == {"5": "D", "7": "A", "8": "G"}
        assert position["intervals"] == {"5": "5", "7": "2/9", "8": "1"}
        assert position["isFullChord"] is False
        assert position["isPartial"] is True
        assert position["omittedIntervals"] == ["3"]
        assert position["addedIntervals"] == ["2/9"]
        assert position["pedals"] == []
        assert position["levers"] == []


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
    assert "advanced" in position["tierReason"].lower()
    assert "E-lower pocket" in position["whenToUse"]
    assert "Complete D major" in position["soundCharacter"]
    assert position["forumEvidenceStatus"] == "not_found"


def test_e_lower_major_grip_families_are_classified_by_pitch_math() -> None:
    cases = [
        ((5, 7, 8), 3, "D", {"5": "D", "7": "A", "8": "F#"}, {"5": "1", "7": "5", "8": "3"}),
        ((7, 8, 10), 3, "D", {"7": "A", "8": "F#", "10": "D"}, {"7": "5", "8": "3", "10": "1"}),
        ((4, 5, 7), 3, "D", {"4": "F#", "5": "D", "7": "A"}, {"4": "3", "5": "1", "7": "5"}),
        ((1, 4, 5), 3, "D", {"1": "A", "4": "F#", "5": "D"}, {"1": "5", "4": "3", "5": "1"}),
    ]

    for grip, fret, root, notes, intervals in cases:
        position = e_lower_grip_position_at_fret(fret, grip)
        payload = position.to_position_payload()

        assert position.root == root
        assert position.quality == "major"
        assert position.is_full_chord is True
        assert position.is_partial is False
        assert position.is_rootless is False
        assert payload["notes"] == notes
        assert payload["intervals"] == intervals
        assert payload["tierReason"]
        assert payload["whenToUse"]
        assert payload["explanationLong"]
        assert payload["forumEvidenceStatus"] == "not_found"
        assert payload["forumEvidence"] == []


def test_twelve_e_strings_1_4_5_diagnostic_answer_is_pitch_math_only() -> None:
    payload = fretboard_payload_for_question("What is 12E on strings 1-4-5?")
    answer = e_lower_grip_answer_for_question("What is 12E on strings 1-4-5?")

    assert payload is not None
    assert answer is not None
    assert payload["title"] == "1-4-5 with E-lower at fret 12"
    position = payload["positions"][0]
    assert position["id"] == "b-e-lower-1-4-5-12"
    assert position["root"] == "B"
    assert position["quality"] == "major"
    assert position["fret"] == 12
    assert position["strings"] == [1, 4, 5]
    assert position["levers"] == ["E"]
    assert position["notes"] == {"1": "F#", "4": "D#", "5": "B"}
    assert position["intervals"] == {"1": "5", "4": "3", "5": "1"}
    assert position["isFullChord"] is True
    assert "B major" in answer
    assert "full B major" in answer
    assert "Use:" in answer


def test_e_lower_5_7_8_at_third_fret_is_not_misclassified_as_b9() -> None:
    position = e_lower_578_position_at_fret(3)
    answer = e_lower_578_answer_for_question("What does 5-7-8 with E lowered give me at the 3rd fret?")
    b9_answer = e_lower_578_b9_answer_for_question("Is 5-7-8 with E lowered a B9 pocket?")
    b9_payload = fretboard_payload_for_question("Is 5-7-8 with E lowered a B9 pocket?")

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
    assert b9_answer is not None
    assert "not a full B9 pocket" in b9_answer
    assert "D major" in b9_answer
    assert "rootless B minor 7 color" in b9_answer
    assert "frets 0, 12, 24" in b9_answer
    assert b9_payload is not None
    assert b9_payload["title"] == "5-7-8 E-lower B9 check"
    assert b9_payload["sourceContext"][0]["kind"] == "rule"
    assert b9_payload["sourceContext"][0]["sourceId"] == "steel_guitar_rag.fretboard_examples"
    assert len(b9_payload["positions"]) == 1
    b9_position = b9_payload["positions"][0]
    assert b9_position["id"] == "b9-check-e-lower-5-7-8-3"
    assert b9_position["root"] == "D"
    assert b9_position["quality"] == "major"
    assert b9_position["notes"] == {"5": "D", "7": "A", "8": "F#"}
    assert b9_position["intervals"] == {"5": "1", "7": "5", "8": "3"}
    assert b9_position["function"] == "B9 check"
    assert b9_position["family"] == "e_lower_578_b9_check"
    assert b9_position["visibleByDefault"] is True
    assert "[object Object]" not in str(b9_payload)


def test_v_chord_pockets_in_a_are_generated_from_e_pitch_math() -> None:
    payload = functional_pocket_payload_for_question("Show me V chord pockets in A.")
    answer = functional_pocket_answer_for_question("Show me V chord pockets in A.")

    assert payload is not None
    assert answer is not None
    assert_valid_visualization_payload(payload)
    assert payload["title"] == "V chord pockets in A (E)"
    assert "In A, the V chord is E" in answer
    assert "Dominant-color pockets" in answer
    assert "forum" not in answer.lower()

    positions = payload["positions"]
    by_id = {position["id"]: position for position in positions}
    assert {"a-v-e-open-0", "a-v-e-af-3", "a-v-e-ab-7"}.issubset(by_id)
    assert [position["id"] for position in positions if position["visibleByDefault"]] == [
        "a-v-e-open-0",
        "a-v-e-af-3",
        "a-v-e-ab-7",
    ]
    assert all(position["function"] == "V" for position in positions)
    assert all(position["keyContext"] == "A" for position in positions)
    dominant = [position for position in positions if position["family"] == "v_e_lower_dominant_pocket"]
    assert dominant
    assert all(position["positionKind"] == "rootless_voicing" for position in dominant)
    assert all(position["isPartial"] for position in dominant)


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
    assert fretboard_payload_for_question("How do you play a C chord?")["title"] == "C major positions on E9"
    assert fretboard_payload_for_question("How do I play a C#?")["title"] == "C# major positions on E9"
    assert fretboard_payload_for_question("Show me places to play an A major chord.")["title"] == "A major positions on E9"
    assert fretboard_payload_for_question("Show me places to play a G major chord.")["title"] == "G major positions on E9"
    assert fretboard_payload_for_question("Where are G major positions on E9?")["title"] == "G major positions on E9"
    assert fretboard_payload_for_question("Show me a 1-4-5 in G.")["title"] == "I-IV-V in G on E9"
    assert fretboard_payload_for_question("Show me common grips for G.")["title"] == "Common G major grips on E9"
    assert fretboard_payload_for_question("What are common Fender Steel King settings?") is None


def test_remaining_broad_p1_visual_prompts_get_fretboard_payloads() -> None:
    e_lower = fretboard_payload_for_question("Where does my E-lower position give me a minor sound?")
    assert e_lower is not None
    assert e_lower["title"] == "G# minor positions on E9"

    e_minor = fretboard_payload_for_question("Where is an E minor pocket on my E9?")
    assert e_minor is not None
    assert e_minor["title"] == "E minor positions on E9"

    d_ab = fretboard_payload_for_question("Where are A+B positions for D major?")
    assert d_ab is not None
    assert d_ab["title"] == "D major positions on E9"
    assert any(position["fret"] == 17 and "A" in position["pedals"] and "B" in position["pedals"] for position in d_ab["positions"])

    g_af = fretboard_payload_for_question("Show me a G A+F position.")
    assert g_af is not None
    assert g_af["title"] == "G major positions on E9"
    assert any(position["fret"] == 6 and "A" in position["pedals"] and "F" in position["levers"] for position in g_af["positions"])


def test_beginner_chord_concept_questions_route_to_deterministic_answers_without_payloads() -> None:
    g_request = chord_concept_request_for_question("What's a G chord even mean?")
    assert g_request is not None
    assert g_request.normalized_key == "G"
    assert g_request.quality == "major"
    g_answer = chord_concept_answer_for_question("What's a G chord even mean?")
    assert g_answer is not None
    assert "G-B-D" in g_answer
    assert "root, major 3rd, and perfect 5th" in g_answer
    assert "3rd fret" in g_answer
    assert "10th fret" in g_answer
    assert fretboard_payload_for_question("What's a G chord even mean?") is None

    c_answer = chord_concept_answer_for_question("What does a C chord mean?")
    assert c_answer is not None
    assert "C-E-G" in c_answer
    assert fretboard_payload_for_question("What does a C chord mean?") is None

    d_answer = chord_concept_answer_for_question("What notes are in a D chord?")
    assert d_answer is not None
    assert "D-F#-A" in d_answer
    assert fretboard_payload_for_question("What notes are in a D chord?") is None

    e_minor_request = chord_concept_request_for_question("What makes an E minor chord minor?")
    assert e_minor_request is not None
    assert e_minor_request.normalized_key == "E"
    assert e_minor_request.quality == "minor"
    e_minor_answer = chord_concept_answer_for_question("What makes an E minor chord minor?")
    assert e_minor_answer is not None
    assert "E-G-B" in e_minor_answer
    assert "minor 3rd" in e_minor_answer
    assert fretboard_payload_for_question("What makes an E minor chord minor?") is None


def test_invalid_chord_symbol_guardrail_clarifies_before_retrieval() -> None:
    assert chord_symbol_from_chord_like_question("how. do I play a GF chord?") == "GF"
    gf_answer = chord_symbol_guardrail_answer_for_question("how. do I play a GF chord?")
    assert gf_answer is not None
    assert "I don’t recognize “GF” as a standard chord name." in gf_answer
    assert "G/F" in gf_answer
    assert "say it with a slash" in gf_answer
    assert fretboard_payload_for_question("how. do I play a GF chord?") is None

    h_answer = chord_symbol_guardrail_answer_for_question("how do I play an H chord?")
    assert h_answer is not None
    assert "I don’t recognize “H” as a standard chord name." in h_answer
    assert "A through G" in h_answer

    assert chord_symbol_guardrail_answer_for_question("where is a Cmajorish chord?") is not None
    assert chord_symbol_guardrail_answer_for_question("what is a Zm chord?") is not None
    assert chord_symbol_guardrail_answer_for_question("show me a GmF chord") is not None


def test_rootless_chord_quality_aliases_bypass_invalid_symbol_guardrail() -> None:
    cases = {
        "sus": ("sus", False),
        "suspended": ("sus", False),
        "sus2": ("sus2", False),
        "sus4": ("sus4", False),
        "dominant": ("dominant7", False),
        "dom": ("dominant7", False),
        "dom7": ("dominant7", False),
        "dominant 7": ("dominant7", False),
        "7th": ("dominant7", False),
        "V7": ("dominant7", True),
        "5 dominant 7": ("dominant7", True),
        "5 dom 7": ("dominant7", True),
        "5^7": ("dominant7", True),
        "five dominant seven": ("dominant7", True),
        "dim": ("diminished", False),
        "diminished": ("diminished", False),
        "dim7": ("diminished7", False),
        "aug": ("augmented", False),
        "augmented": ("augmented", False),
        "+ chord": ("augmented", False),
    }

    for alias, (quality, is_function) in cases.items():
        request = normalize_rootless_chord_quality_alias(alias)
        assert request is not None, alias
        assert request.quality == quality
        assert request.is_function is is_function

        question = f"How do I play a {alias}?"
        answer = rootless_chord_quality_answer_for_question(question)
        assert answer is not None, question
        assert "Give me" in answer
        assert chord_symbol_guardrail_answer_for_question(question) is None
        assert fretboard_payload_for_question(question) is None


def test_rootless_chord_quality_answers_explain_without_fretboard() -> None:
    expected_phrases = {
        "What is a sus chord?": ("sus4 = root, 4th, 5th", "sus2 = root, 2nd, 5th", "no 3rd"),
        "How do I play a dominant 7 chord?": ("root, major 3rd, perfect 5th, and flat 7th", "D7 is the V7 chord"),
        "What is 5^7?": ("scale degree 5", "Give me the key"),
        "What is a dim7 chord?": ("root, flat 3rd, flat 5th, and double-flat 7th", "passing movement"),
        "How do I play an aug chord?": ("root, major 3rd, and sharp 5th", "half-step motion"),
    }

    for question, phrases in expected_phrases.items():
        answer = rootless_chord_quality_answer_for_question(question)
        assert answer is not None
        for phrase in phrases:
            assert phrase in answer
        assert "I don’t recognize" not in answer
        assert fretboard_payload_for_question(question) is None


def test_valid_chord_symbols_are_not_blocked_by_guardrail() -> None:
    for question in (
        "how do I play a G chord?",
        "how do I play an F chord?",
        "how do I play a Bb chord?",
        "how do I play a B-flat chord?",
        "how do I play an Em chord?",
        "how do I play a G7 chord?",
        "how do I play a B9 chord?",
    ):
        assert chord_symbol_guardrail_answer_for_question(question) is None

    slash_answer = chord_symbol_guardrail_answer_for_question("how do I play a G/F chord?")
    assert slash_answer is not None
    assert "G/F is a slash chord" in slash_answer
    assert "does not yet generate a separate bass-note/slash-chord diagram" in slash_answer
    assert fretboard_payload_for_question("how do I play a G/F chord?") is None


def test_natural_language_major_requests_route_for_every_chromatic_root() -> None:
    roots = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")

    for root in roots:
        question = f"How do I play a {root} major?"
        request = major_chord_location_request_for_question(question)
        payload = fretboard_payload_for_question(question)

        assert request is not None, question
        assert request.requested_root == root
        assert payload is not None, question
        assert payload["positions"], question


def test_natural_language_major_requests_accept_common_question_forms() -> None:
    questions = (
        "How do I play G major?",
        "How can I play a B-flat major?",
        "How should I play F-sharp major on E9?",
        "How would you play an Eb major chord on pedal steel?",
        "Show me how to play A major.",
        "What's the best way to play a C# major chord?",
    )

    for question in questions:
        request = major_chord_location_request_for_question(question)
        payload = fretboard_payload_for_question(question)

        assert request is not None, question
        assert payload is not None, question
        assert payload["positions"], question


def test_classic_country_move_payload_visualizes_all_three_pitch_checked_states() -> None:
    payload = fretboard_payload_for_question("Show me a classic country move.")

    assert payload is not None
    assert_valid_visualization_payload(payload)
    assert payload["title"] == "Classic-country pickup in G"
    assert [position["role"] for position in payload["positions"]] == [
        "Step 1 · Pick the tense double-stop",
        "Step 2 · Slide into the home fret",
        "Step 3 · Release A and land on G",
    ]
    assert [position["notes"] for position in payload["positions"]] == [
        {"4": "F", "5": "D"},
        {"4": "G", "5": "E"},
        {"4": "G", "5": "D", "6": "B"},
    ]


def test_b_flat_minor_preserves_flat_spelling_in_answer_and_payload() -> None:
    answer = minor_chord_answer_for_question("What does Bb minor look like?")
    payload = fretboard_payload_for_question("What does Bb minor look like?")

    assert answer is not None
    assert "Bb minor is Bb-Db-F" in answer
    assert "BB" not in answer
    assert payload is not None
    assert payload["title"] == "Bb minor positions on E9"


def test_validation_rejects_raw_geometry_and_unknown_labels() -> None:
    payload = get_fretboard_examples("major_positions", "G")
    payload["positions"][0]["x"] = 42
    with pytest.raises(ValueError, match="Raw geometry"):
        validate_fretboard_payload(payload)

    payload = get_fretboard_examples("major_positions", "G")
    payload["positions"][1]["levers"] = ["E-raise/F"]
    with pytest.raises(ValueError, match="unknown lever"):
        validate_fretboard_payload(payload)

    payload = get_fretboard_examples("major_positions", "G")
    partial_578 = next(position for position in payload["positions"] if position["id"] == "g-open-grip-5-7-8-3")
    partial_578["pedals"] = ["B"]
    with pytest.raises(ValueError, match="inert pedal/lever label"):
        validate_fretboard_payload(payload)
