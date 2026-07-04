from __future__ import annotations

from typing import Any

from pocketsteel.fretboard_examples import validate_fretboard_payload
from pocketsteel.progression_guide import progression_guide_for_question


def _guide(question: str) -> dict[str, Any]:
    result = progression_guide_for_question(question)
    assert result is not None
    validate_fretboard_payload(result["fretboard"])
    return result


def _recommended_events(result: dict[str, Any]) -> list[dict[str, Any]]:
    return result["progression_guide"]["recommendedRoute"]["events"]


def _event_signature(event: dict[str, Any]) -> tuple[str, str, int, str, tuple[str, ...], tuple[str, ...]]:
    return (
        event["function"],
        event["chordName"],
        event["fret"],
        event["grip"],
        tuple(event["pedals"]),
        tuple(event["levers"]),
    )


def test_c_i_iv_v_i_progression_home_route_and_alternates_are_validated() -> None:
    result = _guide("Show me a C F G C progression on E9.")
    events = _recommended_events(result)

    assert result["progression_guide"]["key"] == "C"
    assert result["progression_guide"]["progression"] == "I-IV-V-I"
    assert [_event_signature(event) for event in events] == [
        ("I", "C", 8, "5-6-8", (), ()),
        ("IV", "F", 8, "5-6-8", ("A", "B"), ()),
        ("V", "G", 10, "5-6-8", ("A", "B"), ()),
        ("I", "C", 8, "5-6-8", (), ()),
    ]
    assert {route["family"] for route in result["progression_guide"]["routes"]} == {
        "home_pocket",
        "ascending_same_grip",
        "pedals_down",
        "dominant_shell",
    }
    renderable_ids = {
        event["renderablePositionId"]
        for route in result["progression_guide"]["routes"]
        for event in route["events"]
    }
    position_ids = {position["id"] for position in result["fretboard"]["positions"]}
    assert renderable_ids <= position_ids
    assert all(position["validationStatus"] == "pitch_validated" for position in result["fretboard"]["positions"])


def test_c_i_iv_v_i_roman_prompt_routes_to_same_validated_home_route() -> None:
    result = _guide("How do I play I IV V I in C on pedal steel?")
    events = _recommended_events(result)

    assert [_event_signature(event) for event in events] == [
        ("I", "C", 8, "5-6-8", (), ()),
        ("IV", "F", 8, "5-6-8", ("A", "B"), ()),
        ("V", "G", 10, "5-6-8", ("A", "B"), ()),
        ("I", "C", 8, "5-6-8", (), ()),
    ]
    assert "fret 8, strings 5-6-8" in result["answer"]


def test_g_i_iv_v_i_progression_transposes_home_and_pedals_down_routes() -> None:
    result = _guide("Give me a beginner route through G C D G.")
    events = _recommended_events(result)

    assert result["progression_guide"]["key"] == "G"
    assert [_event_signature(event) for event in events] == [
        ("I", "G", 3, "5-6-8", (), ()),
        ("IV", "C", 3, "5-6-8", ("A", "B"), ()),
        ("V", "D", 5, "5-6-8", ("A", "B"), ()),
        ("I", "G", 3, "5-6-8", (), ()),
    ]
    assert [route["family"] for route in result["progression_guide"]["routes"]] == [
        "home_pocket",
        "pedals_down",
    ]


def test_simple_song_progression_in_g_defaults_to_i_iv_v_i_route() -> None:
    result = _guide("How do I move through a simple song progression in G?")
    events = _recommended_events(result)

    assert result["progression_guide"]["key"] == "G"
    assert result["progression_guide"]["progression"] == "I-IV-V-I"
    assert "original deterministic practice route" in result["answer"]
    assert [_event_signature(event) for event in events] == [
        ("I", "G", 3, "5-6-8", (), ()),
        ("IV", "C", 3, "5-6-8", ("A", "B"), ()),
        ("V", "D", 5, "5-6-8", ("A", "B"), ()),
        ("I", "G", 3, "5-6-8", (), ()),
    ]


def test_c_diatonic_route_labels_minor_chords_and_dominant_shell_honestly() -> None:
    result = _guide("Show me C Am Em F Dm G7 C as a pedal steel progression.")
    events = _recommended_events(result)

    assert [event["chordName"] for event in events] == ["C", "Am", "Em", "F", "Dm", "G7", "C"]
    assert [_event_signature(event) for event in events[:5]] == [
        ("I", "C", 8, "8-6-5", (), ()),
        ("vi", "Am", 8, "10-8-6", ("A",), ()),
        ("iii", "Em", 8, "6-5-2", (), ()),
        ("IV", "F", 8, "6-5-4", ("A", "B"), ()),
        ("ii", "Dm", 8, "7-6-5", ("A", "B"), ()),
    ]
    g7 = events[5]
    assert g7["chordName"] == "G7"
    assert g7["quality"] == "dominant7"
    assert g7["voicingType"] == "dominant_shell"
    assert set(g7["contains"]) >= {"1", "3", "b7"}
    assert g7["omits"] == ["5"]
    assert "Dominant shell" in g7["routeReason"]


def test_progression_guide_preserves_tab_owned_two_chord_movement_prompts() -> None:
    assert progression_guide_for_question("Show me a G to C move.") is None
    assert progression_guide_for_question("Show me a G C D G movement.") is None


def test_progression_guide_does_not_handle_blocked_song_tab_requests() -> None:
    assert progression_guide_for_question("Give me the full tab for a modern copyrighted song.") is None
    assert progression_guide_for_question("Transcribe this YouTube recording into tab.") is None
