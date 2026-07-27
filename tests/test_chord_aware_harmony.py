from __future__ import annotations

import pytest

from steel_guitar_rag.melody_arranger import (
    _chord_pitch_classes,
    arrange_melody_routes,
)


PITCH_VALUES = {
    "D4": 62,
    "E4": 64,
    "F#4": 66,
    "G4": 67,
    "A4": 69,
    "B4": 71,
}


def _verification_events(*, basis: str = "user") -> list[dict[str, object]]:
    pitches = ("G4", "G4", "A4", "B4", "E4", "F#4", "F#4", "G4", "A4", "D4")
    chord_changes = {0: "G", 4: "C", 8: "D"}
    return [
        {
            "token": pitch,
            "pitch": pitch,
            "pitchValue": PITCH_VALUES[pitch],
            "measure": 1 + index // 4,
            "beat": 1 + index % 4,
            "durationBeats": 1,
            "chord": chord_changes.get(index, ""),
            "chordBasis": basis if index in chord_changes else "",
        }
        for index, pitch in enumerate(pitches)
    ]


def _routes(events: list[dict[str, object]], *, texture: str = "both") -> list[dict[str, object]]:
    routes, _resolved = arrange_melody_routes(
        events,
        key="G",
        texture=texture,
        route_id_prefix="chord-aware-verification",
        title="Chord-aware verification",
    )
    return routes


def test_frozen_g_c_d_harmonized_melody_uses_exact_verified_grips() -> None:
    route = next(
        route
        for route in _routes(_verification_events())
        if route["harmonyType"] == "chord_aware_harmony"
    )

    assert route["label"] == "Chord-aware harmony"
    assert route["harmonyBasis"] == "chord_track"
    assert route["recommended"] is True
    assert route["chordContext"] == {
        "symbols": ["G", "C", "D"],
        "usedForRanking": True,
    }

    expected = [
        ("G", "G4", ["B3"], (4, 6), 3, ()),
        ("G", "G4", ["B3"], (4, 6), 3, ()),
        ("G", "A4", ["C4"], (4, 6), 4, ("F",)),
        ("G", "B4", ["D4"], (4, 6), 6, ("F",)),
        ("C", "E4", ["C4"], (5, 6), 3, ("A", "B")),
        ("C", "F#4", ["D4"], (5, 6), 5, ("A", "B")),
        ("C", "F#4", ["D4"], (5, 6), 5, ("A", "B")),
        ("C", "G4", ["E4"], (4, 5), 3, ("A",)),
        ("D", "A4", ["F#4"], (5, 6), 10, ()),
        ("D", "D4", ["A3"], (6, 8), 5, ("B",)),
    ]
    actual = []
    for event in route["events"]:
        pitch_values = list(event["mechanicalPitchesByString"].values())
        actual.append(
            (
                event["activeChord"],
                event["resolvedPitch"],
                event["supportingPitches"],
                tuple(note["string"] for note in event["notes"]),
                event["notes"][0]["fret"],
                tuple(
                    [
                        *event["pedalControls"],
                        *event["leverControls"],
                    ]
                ),
            )
        )
        assert max(pitch_values) == event["pitchValue"]
        assert event["chordBasis"] == "user"
        assert len(event["notes"]) == 2

    assert actual == expected
    assert [event["harmonyFunction"] for event in route["events"]] == [
        "chord_tone",
        "chord_tone",
        "diatonic_passing",
        "chord_tone",
        "chord_tone",
        "diatonic_passing",
        "diatonic_passing",
        "chord_tone",
        "chord_tone",
        "chord_tone",
    ]
    assert route["fallbacks"] == []
    assert route["tabExample"]["validation"] == {
        "ok": True,
        "issues": [],
        "profile": "emmons-e9-basic",
        "eventCount": 10,
    }


def test_chord_aware_route_can_be_requested_directly() -> None:
    routes = _routes(_verification_events(), texture="chord_aware_harmony")

    assert [route["harmonyType"] for route in routes] == [
        "single_note",
        "chord_aware_harmony",
    ]


def test_suggested_chords_do_not_enable_a_chord_aware_claim() -> None:
    routes = _routes(_verification_events(basis="suggested"))

    assert "chord_aware_harmony" not in {
        route["harmonyType"] for route in routes
    }


def test_no_chord_track_exposes_explicitly_key_only_scale_harmonies() -> None:
    events = [
        {
            "token": pitch,
            "pitch": pitch,
            "pitchValue": PITCH_VALUES[pitch],
        }
        for pitch in ("G4", "A4", "B4")
    ]
    routes = _routes(events)
    labels = {route["harmonyType"]: route["label"] for route in routes}

    assert "chord_aware_harmony" not in labels
    assert labels["thirds"] == "Key-only harmonized thirds"
    assert labels["sixths"] == "Key-only harmonized sixths"


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("C", {0, 4, 7}),
        ("Cm", {0, 3, 7}),
        ("C7", {0, 4, 7, 10}),
        ("Cmaj7", {0, 4, 7, 11}),
        ("Cm7", {0, 3, 7, 10}),
        ("C6", {0, 4, 7, 9}),
        ("Cm6", {0, 3, 7, 9}),
        ("Cdim", {0, 3, 6}),
        ("Caug", {0, 4, 8}),
        ("Csus2", {0, 2, 7}),
        ("Csus4", {0, 5, 7}),
        ("C/E", {0, 4, 7}),
    ],
)
def test_supported_chord_symbols_resolve_to_their_harmonic_pitch_classes(
    symbol: str,
    expected: set[int],
) -> None:
    assert _chord_pitch_classes(symbol) == expected
