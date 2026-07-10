from __future__ import annotations

import pytest

from pocketsteel.melody_assistant import (
    MelodyExerciseError,
    configured_melody_exercise_enabled,
    is_melody_teaching_request,
    melody_exercise_response,
)


def test_feature_flag_defaults_off() -> None:
    assert configured_melody_exercise_enabled({}) is False
    assert configured_melody_exercise_enabled({"STEEL_RAG_ENABLE_MELODY_EXERCISE": "true"}) is True


def test_artist_solo_request_is_accepted_as_teaching_and_asks_for_source() -> None:
    result = melody_exercise_response("Tab the whole solo from Together Again.")

    assert result is not None
    assert result["melody_exercise"]["kind"] == "artist_solo_lesson"
    assert result["melody_exercise"]["status"] == "needs_source"
    assert result["melody_exercise"]["section"]["number"] == 1
    assert result["melody_exercise"]["section"]["hasMore"] is True
    assert "Yes—I can teach" in result["answer"]
    assert "send the recording or video link" in result["answer"]
    assert "copyrighted song tab" not in result["answer"].lower()
    assert "can’t provide" not in result["answer"].lower()


def test_structured_g_scale_degree_phrase_builds_synced_tab_and_fretboard() -> None:
    result = melody_exercise_response(
        "Build a melody exercise",
        {
            "kind": "user_melody",
            "key": "G",
            "melody": ["1", "2", "3", "5"],
            "renderingMode": "e9_adaptation",
        },
    )

    assert result is not None
    exercise = result["melody_exercise"]
    tab = result["tab_example"]
    fretboard = result["fretboard"]
    assert exercise["status"] == "ready"
    assert exercise["accuracy"]["label"] == "exact"
    assert [event["resolvedNote"] for event in exercise["events"]] == ["G", "A", "B", "D"]
    assert [event["notes"][0]["fret"] for event in exercise["events"]] == [3, 5, 7, 10]
    assert tab["validation"]["ok"] is True
    assert tab["validation"]["eventCount"] == 4
    assert len(tab["events"]) == len(fretboard["positions"]) == len(exercise["events"])
    assert [event["renderablePositionId"] for event in exercise["events"]] == [
        position["id"] for position in fretboard["positions"]
    ]
    assert result["sources"] == []


def test_c_major_note_names_use_valid_string_five_placement() -> None:
    result = melody_exercise_response(
        "Build my C phrase",
        {"kind": "original_exercise", "key": "C", "melody": ["C", "D", "E", "G"]},
    )

    assert result is not None
    events = result["melody_exercise"]["events"]
    assert [event["notes"][0]["string"] for event in events] == [5, 5, 5, 5]
    assert [event["notes"][0]["fret"] for event in events] == [1, 3, 5, 8]


def test_original_exercise_suppresses_supplied_recording_identity_and_sources() -> None:
    result = melody_exercise_response(
        "Build an original exercise",
        {
            "kind": "original_exercise",
            "key": "G",
            "melody": ["1", "2", "3", "5"],
            "material": {
                "artist": "Stale Artist",
                "song": "Stale Song",
                "sourceUrl": "https://example.test/stale",
            },
        },
    )

    assert result is not None
    assert result["melody_exercise"]["title"] == "Original melody exercise in G"
    assert result["melody_exercise"]["material"] == {}
    assert result["sources"] == []


def test_long_arrangement_is_sectioned_instead_of_blocked() -> None:
    melody = ["1", "2", "3", "4", "5", "6", "7", "1", "3", "2"]
    first = melody_exercise_response(
        "Teach the full arrangement",
        {"kind": "song_arrangement_lesson", "key": "G", "melody": melody, "sectionNumber": 1},
    )
    second = melody_exercise_response(
        "Teach the full arrangement",
        {"kind": "song_arrangement_lesson", "key": "G", "melody": melody, "sectionNumber": 2},
    )

    assert first is not None and second is not None
    assert len(first["melody_exercise"]["events"]) == 8
    assert first["melody_exercise"]["section"] == {
        "number": 1,
        "total": 2,
        "label": "Section 1",
        "hasMore": True,
        "nextSection": 2,
    }
    assert len(second["melody_exercise"]["events"]) == 2
    assert second["melody_exercise"]["section"]["hasMore"] is False


def test_exact_artist_claim_downgrades_without_identified_source() -> None:
    result = melody_exercise_response(
        "Teach an artist solo",
        {
            "kind": "artist_solo_lesson",
            "key": "G",
            "accuracy": "exact",
            "melody": ["1", "2", "3"],
            "material": {"artist": "Example Artist", "song": "Example Song"},
        },
    )

    assert result is not None
    accuracy = result["melody_exercise"]["accuracy"]
    assert accuracy["label"] == "approximate"
    assert "identified recording" in accuracy["note"]


def test_source_reference_is_preserved_for_recording_lesson() -> None:
    result = melody_exercise_response(
        "Teach this recording",
        {
            "kind": "artist_solo_lesson",
            "key": "G",
            "melody": ["1", "2", "3"],
            "material": {
                "artist": "Example Artist",
                "song": "Example Song",
                "recording": "Studio version",
                "sourceUrl": "https://example.test/recording",
            },
        },
    )

    assert result is not None
    assert result["melody_exercise"]["material"]["recording"] == "Studio version"
    assert result["sources"][0]["url"] == "https://example.test/recording"


def test_top_level_material_identity_and_tokens_are_supported() -> None:
    result = melody_exercise_response(
        "Teach this artist solo",
        {
            "kind": "artist_solo_lesson",
            "artist": "Example Artist",
            "song": "Example Song",
            "recording": "Studio version",
            "sourceUrl": "https://example.test/recording",
            "key": "G",
            "tokens": ["G", "A", "B", "D"],
        },
    )

    assert result is not None
    assert result["melody_exercise"]["status"] == "ready"
    assert result["melody_exercise"]["material"]["artist"] == "Example Artist"
    assert len(result["melody_exercise"]["events"]) == 4


@pytest.mark.parametrize(
    ("request_payload", "message"),
    [
        ({"key": "F", "melody": ["1", "2"]}, "keys of G and C"),
        ({"key": "G", "tuning": "C6", "melody": ["1", "2"]}, "E9 tuning only"),
        ({"key": "G", "melody": ["1", "b9"]}, "not in the selected major scale"),
    ],
)
def test_unsupported_structured_input_does_not_render(request_payload: dict[str, object], message: str) -> None:
    with pytest.raises(MelodyExerciseError, match=message):
        melody_exercise_response("Build a melody exercise", request_payload)


def test_unrelated_question_does_not_route_to_melody() -> None:
    assert melody_exercise_response("Why does my amp buzz?") is None
    assert is_melody_teaching_request("Why does my amp buzz?") is False
