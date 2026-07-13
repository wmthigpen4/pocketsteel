from __future__ import annotations

import pytest

from pocketsteel.fretboard_examples import absolute_pitch_for_string, major_positions
from pocketsteel.melody_arranger import (
    MelodyInput,
    PositionCandidate,
    _candidate_for_fretboard_position,
    _transition_between,
    choose_mixed_path,
    single_note_candidates,
)
from pocketsteel.melody_assistant import (
    MelodyExerciseError,
    configured_melody_exercise_enabled,
    is_melody_teaching_request,
    melody_exercise_response,
)
from pocketsteel.melody_import import import_score_draft, public_song_catalog
from pocketsteel.tab_engine import TabNote


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
    assert exercise["input"]["meter"] == "4/4"
    assert exercise["input"]["pickupBeats"] == 0.0
    assert [route["harmonyType"] for route in exercise["routes"]] == [
        "single_note", "mixed_arrangement", "thirds", "sixths"
    ]
    tab = result["tab_example"]
    fretboard = result["fretboard"]
    assert exercise["status"] == "ready"
    assert exercise["accuracy"]["label"] == "exact"
    assert [event["resolvedNote"] for event in exercise["events"]] == ["G", "A", "B", "D"]
    assert [event["resolvedPitch"] for event in exercise["events"]] == ["G4", "A4", "B4", "D5"]
    assert all(0 <= event["notes"][0]["fret"] <= 24 for event in exercise["events"])
    assert tab["validation"]["ok"] is True
    assert tab["validation"]["eventCount"] == 4
    assert len(tab["events"]) == len(fretboard["positions"]) == len(exercise["events"])
    assert "Ly |" not in tab["rendered_tab"]
    assert all("lyric" not in event for event in tab["events"])
    assert all("chord" not in event for event in exercise["events"])
    assert "Ch |" not in tab["rendered_tab"]
    assert [(event["measure"], event["beat"]) for event in exercise["events"]] == [(1, 1.0), (1, 2.0), (1, 3.0), (1, 4.0)]
    assert [event["renderablePositionId"] for event in exercise["events"]] == [
        position["id"] for position in fretboard["positions"]
    ]
    assert result["sources"] == []


def test_on_device_audio_transcription_preserves_honest_accuracy_label() -> None:
    result = melody_exercise_response(
        "Arrange my recorded phrase",
        {
            "kind": "user_melody",
            "key": "G",
            "melody": [
                {"token": "G4", "pitch": "G4", "pitchValue": 67, "durationBeats": 1, "confidence": 0.74},
                {"token": "A4", "pitch": "A4", "pitchValue": 69, "durationBeats": 0.5, "confidence": 0.7},
            ],
            "accuracy": "approximate",
            "accuracyConfidence": "medium",
            "accuracyNote": "Pitch and rhythm came from on-device audio estimation and were opened for manual review before E9 arrangement.",
            "sourceProvided": True,
        },
    )

    assert result is not None
    accuracy = result["melody_exercise"]["accuracy"]
    assert accuracy == {
        "label": "approximate",
        "confidence": "medium",
        "note": "Pitch and rhythm came from on-device audio estimation and were opened for manual review before E9 arrangement.",
    }
    assert [event["durationBeats"] for event in result["melody_exercise"]["events"]] == [1, 0.5]


def test_amazing_grace_exact_score_events_keep_rhythm_chords_and_e9_route() -> None:
    draft = import_score_draft({"sourceType": "catalog", "catalogId": "amazing-grace-new-britain"})
    harmony = draft["score"]["harmony"]
    events = []
    for event in draft["score"]["melody"]:
        active = [
            item
            for item in harmony
            if (item["measure"], item["beat"]) <= (event["measure"], event["beat"])
        ]
        events.append({**event, "token": event["pitch"], "chord": active[-1]["symbol"] if active else ""})
    result = melody_exercise_response(
        "Arrange Amazing Grace",
        {
            "kind": "song_arrangement_lesson",
            "key": "G",
            "melody": events,
            "meter": draft["score"]["meter"],
            "pickupBeats": draft["score"]["pickupBeats"],
            "sections": draft["score"]["sections"],
            "material": {
                "song": "Amazing Grace",
                "section": "First phrase",
                "sourceUrl": draft["source"]["url"],
            },
        },
    )
    assert result is not None
    exercise = result["melody_exercise"]
    assert exercise["input"]["meter"] == "3/4"
    assert exercise["input"]["pickupBeats"] == 1.0
    assert [event["resolvedPitch"] for event in exercise["events"]] == ["D4", "G4", "B4", "G4", "B4", "A4", "G4", "E4"]
    assert [(event["notes"][0]["string"], event["notes"][0]["fret"], event["notes"][0]["changes"]) for event in exercise["events"]] == [
        (5, 3, []),
        (4, 3, []),
        (3, 3, []),
        (4, 3, []),
        (3, 3, []),
        (1, 3, []),
        (4, 3, []),
        (5, 3, ["A"]),
    ]
    assert [event["durationBeats"] for event in exercise["events"]] == [1, 2, 0.5, 0.5, 2, 1, 2, 1]
    assert [event["harmonySymbol"] for event in exercise["events"]] == [event["chord"] for event in events[:8]]
    previous_chord = ""
    expected_changes = []
    for event in events:
        expected_changes.append(event["chord"] if event["chord"] != previous_chord else None)
        previous_chord = event["chord"]
    assert [event.get("chord") for event in exercise["events"]] == expected_changes[:8]
    assert all(route["chordContext"]["usedForRanking"] for route in exercise["routes"])
    assert exercise["routes"][0]["chordContext"]["symbols"] == list(dict.fromkeys(event["chord"] for event in events[:8]))
    mixed = next(route for route in exercise["routes"] if route["harmonyType"] == "mixed_arrangement")
    assert {len(event["notes"]) for event in mixed["events"]} == {1, 2, 3}
    opening_g = mixed["events"][1]
    assert opening_g["performanceControls"] == []
    assert "A+B at this fret would produce C harmony, not G" in opening_g["selectionReason"]
    tension = mixed["events"][4]
    assert tension["arrangementRole"] == "tension"
    assert len(tension["notes"]) <= 2
    assert "C" not in tension["performanceControls"]
    resolution = mixed["events"][5]
    assert resolution["arrangementRole"] == "resolution"
    assert resolution["canonicalGrip"] == "4-5-6"
    assert resolution["performanceControls"] == ["A", "B"]
    assert [(note["string"], note["fret"]) for note in resolution["notes"]] == [(4, 5), (5, 5), (6, 5)]
    assert "press A+B" in resolution["movement"]
    assert all("C" not in event["performanceControls"] for event in mixed["events"])
    d_to_g = next(transition for transition in mixed["transitions"] if transition["toEventId"].endswith("-step-7"))
    assert d_to_g["kind"] == "bar_slide"
    assert d_to_g["scope"] == "full_grip"
    assert d_to_g["fromFret"] == 5 and d_to_g["toFret"] == 3
    assert d_to_g["controlsBefore"] == ["A", "B"] and d_to_g["controlsAfter"] == []
    assert d_to_g["sustainedStrings"] == [4, 5, 6]
    assert d_to_g["repickedStrings"] == d_to_g["releasedStrings"] == []
    assert mixed["pathSummary"]["maxBarTravel"] <= 2


def test_amazing_grace_c_arrival_stays_in_the_fret_three_ab_pocket() -> None:
    draft = import_score_draft({"sourceType": "catalog", "catalogId": "amazing-grace-new-britain"})
    harmony = draft["score"]["harmony"]
    events = []
    for event in draft["score"]["melody"]:
        active = [
            item for item in harmony
            if (item["measure"], item["beat"]) <= (event["measure"], event["beat"])
        ]
        events.append({**event, "token": event["pitch"], "chord": active[-1]["symbol"] if active else ""})
    result = melody_exercise_response(
        "Arrange all of Amazing Grace",
        {
            "kind": "song_arrangement_lesson",
            "key": "G",
            "melody": events,
            "meter": draft["score"]["meter"],
            "pickupBeats": draft["score"]["pickupBeats"],
            "sections": draft["score"]["sections"],
            "wholeSong": True,
        },
    )

    mixed = next(route for route in result["melody_exercise"]["routes"] if route["harmonyType"] == "mixed_arrangement")
    c_arrival = mixed["events"][23]
    assert c_arrival["resolvedPitch"] == "E4"
    assert c_arrival["harmonySymbol"] == "C"
    assert c_arrival["arrangementRole"] == "chord_arrival"
    assert c_arrival["canonicalGrip"] == "5-6-8"
    assert c_arrival["performanceControls"] == ["A", "B"]
    assert [(note["string"], note["fret"]) for note in c_arrival["notes"]] == [(5, 3), (6, 3), (8, 3)]
    assert all("C" not in event["performanceControls"] for event in mixed["events"])
    full_grip_targets = {
        int(transition["toEventId"].rsplit("-", 1)[-1]): transition
        for transition in mixed["transitions"]
        if transition["scope"] == "full_grip"
    }
    for target in (7, 35):
        transition = full_grip_targets[target]
        assert transition["fromFret"] == 5 and transition["toFret"] == 3
        assert transition["controlsBefore"] == ["A", "B"] and transition["controlsAfter"] == []
        assert transition["fromStrings"] == transition["toStrings"] == transition["sustainedStrings"] == [4, 5, 6]
    print_tab = mixed["tabExample"]["print_tab_text"]
    assert print_tab.count("Measure") >= 2
    assert all(len(line) <= 112 for line in print_tab.splitlines() if not line.startswith("Measure"))
    assert "~~~~~" in print_tab


def test_c_major_note_names_use_octave_aware_valid_e9_placement() -> None:
    result = melody_exercise_response(
        "Build my C phrase",
        {"kind": "original_exercise", "key": "C", "melody": ["C", "D", "E", "G"]},
    )

    assert result is not None
    events = result["melody_exercise"]["events"]
    assert [event["resolvedPitch"] for event in events] == ["C5", "D5", "E5", "G5"]
    assert all(1 <= event["notes"][0]["string"] <= 10 for event in events)


def test_closest_ascending_and_descending_contours_resolve_octave_direction() -> None:
    melody = ["5", "6", "1", "3", "2", "1", "3"]
    closest = melody_exercise_response("Build", {"key": "G", "melody": melody, "contourMode": "closest_playable"})
    ascending = melody_exercise_response("Build", {"key": "G", "melody": melody, "contourMode": "ascending"})
    descending = melody_exercise_response("Build", {"key": "G", "melody": melody, "contourMode": "descending"})

    assert closest is not None and ascending is not None and descending is not None
    assert [event["resolvedPitch"] for event in closest["melody_exercise"]["events"]] == ["D4", "E4", "G4", "B4", "A4", "G4", "B4"]
    ascending_values = [event["pitchValue"] for event in ascending["melody_exercise"]["events"]]
    descending_values = [event["pitchValue"] for event in descending["melody_exercise"]["events"]]
    assert ascending_values == sorted(ascending_values)
    assert descending_values == sorted(descending_values, reverse=True)


def test_structured_octave_override_and_literal_tab_are_preserved() -> None:
    shifted = melody_exercise_response(
        "Build",
        {"key": "G", "melody": [{"token": "5"}, {"token": "6"}, {"token": "1", "octaveShift": 1}, {"token": "3"}]},
    )
    literal = melody_exercise_response(
        "Build",
        {"key": "G", "melody": [{"string": 4, "fret": 3}, {"string": 4, "fret": 5}, {"string": 4, "fret": 7}]},
    )

    assert shifted is not None and literal is not None
    assert [event["resolvedPitch"] for event in shifted["melody_exercise"]["events"]] == ["D4", "E4", "G5", "B4"]
    assert [event["notes"][0] for event in literal["melody_exercise"]["events"]] == [
        {"string": 4, "fret": 3, "changes": []},
        {"string": 4, "fret": 5, "changes": []},
        {"string": 4, "fret": 7, "changes": []},
    ]


def test_octave_override_changes_only_selected_note() -> None:
    result = melody_exercise_response(
        "Build",
        {"key": "G", "melody": [{"token": "5"}, {"token": "6"}, {"token": "1", "octaveShift": 1}, {"token": "3"}]},
    )

    assert result is not None
    assert [event["resolvedPitch"] for event in result["melody_exercise"]["events"]] == ["D4", "E4", "G5", "B4"]


def test_literal_tab_rejects_octave_override_instead_of_moving_other_notes() -> None:
    with pytest.raises(MelodyExerciseError, match="Literal tab fixes its octave"):
        melody_exercise_response(
            "Build",
            {"key": "G", "melody": [{"string": 4, "fret": 3, "octaveShift": 1}]},
        )


def test_default_arranger_returns_faithful_and_recommended_mixed_routes() -> None:
    result = melody_exercise_response("Build", {"key": "G", "melody": ["5", "6", "1", "3", "2", "1", "3"]})

    assert result is not None
    routes = result["melody_exercise"]["routes"]
    assert routes[0]["harmonyType"] == "single_note"
    recommended = next(route for route in routes if route["recommended"])
    assert recommended["harmonyType"] == "mixed_arrangement"
    assert {len(event["notes"]) for event in recommended["events"]} == {1, 2}
    assert all(len(event["notes"]) < 3 for event in recommended["events"])
    assert all(
        max(
            absolute_pitch_for_string(note["string"], note["fret"], tuple(note["changes"]))
            for note in event["notes"]
        ) == event["pitchValue"]
        for event in recommended["events"]
    )
    assert [route["harmonyType"] for route in routes] == ["single_note", "mixed_arrangement", "thirds", "sixths"]
    for route in routes:
        assert len(route["events"]) == len(route["fretboard"]["positions"])
        assert [event["renderablePositionId"] for event in route["events"]] == [position["id"] for position in route["fretboard"]["positions"]]


@pytest.mark.parametrize(
    ("name", "source_pitch", "source_fret"),
    [("D to G", "A4", 5), ("G to G", "D5", 10)],
)
def test_mixed_arrangement_prioritizes_full_grip_ab_to_open_slides(
    name: str,
    source_pitch: str,
    source_fret: int,
) -> None:
    result = melody_exercise_response(
        name,
        {
            "key": "G",
            "meter": "4/4",
            "melody": [
                {"pitch": source_pitch, "durationBeats": 2, "measure": 1, "beat": 1, "chord": "D7" if source_fret == 5 else "G"},
                {"pitch": "G4", "durationBeats": 2, "measure": 1, "beat": 3, "chord": "G"},
            ],
        },
    )

    mixed = next(route for route in result["melody_exercise"]["routes"] if route["harmonyType"] == "mixed_arrangement")
    assert [(event["notes"][0]["fret"], event["canonicalGrip"], event["performanceControls"]) for event in mixed["events"]] == [
        (source_fret, "4-5-6", ["A", "B"]),
        (3, "4-5-6", []),
    ]
    transition = mixed["transitions"][0]
    assert transition["kind"] == "bar_slide"
    assert transition["scope"] == "full_grip"
    assert transition["fromFret"] == source_fret and transition["toFret"] == 3
    assert transition["controlsBefore"] == ["A", "B"] and transition["controlsAfter"] == []
    assert transition["fromStrings"] == transition["toStrings"] == transition["sustainedStrings"] == [4, 5, 6]
    assert transition["repickedStrings"] == transition["releasedStrings"] == []
    assert transition["voiceActions"] == [
        {"string": 4, "action": "bar_slide"},
        {"string": 5, "action": "bar_slide"},
        {"string": 6, "action": "bar_slide"},
    ]
    assert transition["controlChanges"] == {"pressed": [], "released": ["A", "B"]}
    assert "tabTokens" not in transition
    assert "releasing A+B" in transition["label"]


@pytest.mark.parametrize(
    ("current_controls", "expected_kind"),
    [((), "bar_slide"), (("F",), "lever_glide")],
)
def test_transition_contract_describes_complete_grip_choreography(
    current_controls: tuple[str, ...],
    expected_kind: str,
) -> None:
    source = PositionCandidate(
        fret=3,
        notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3)),
        top_pitch=67,
        controls=(),
        family="open_major",
        note_names=("G", "D", "B"),
        intervals=("1", "5", "3"),
        pattern_family="open_major",
        canonical_grip=(4, 5, 6),
    )
    if expected_kind == "bar_slide":
        target = PositionCandidate(
            fret=5,
            notes=(TabNote(4, 5), TabNote(5, 5), TabNote(6, 5)),
            top_pitch=69,
            controls=(),
            family="open_major",
            note_names=("A", "E", "C#"),
            intervals=("2", "6", "#4"),
            pattern_family="open_major",
            canonical_grip=(4, 5, 6),
        )
    else:
        target = PositionCandidate(
            fret=3,
            notes=(TabNote(4, 3, ("F",)), TabNote(5, 3), TabNote(6, 3)),
            top_pitch=68,
            controls=current_controls,
            family="a_f_major",
            note_names=("G#", "D", "B"),
            intervals=("#1", "5", "3"),
            pattern_family="a_f_major",
            canonical_grip=(4, 5, 6),
        )
    transition = _transition_between("route", 1, source, target)

    assert transition is not None
    assert transition["kind"] == expected_kind
    assert transition["scope"] == "full_grip"
    assert transition["fromStrings"] == transition["toStrings"] == [4, 5, 6]
    assert transition["sustainedStrings"] == [4, 5, 6]
    assert transition["repickedStrings"] == transition["releasedStrings"] == []
    assert "tabTokens" not in transition
    assert {action["action"] for action in transition["voiceActions"]} <= {
        expected_kind,
        "hold",
    }


@pytest.mark.parametrize(("source_fret", "source_pitch"), [(5, 69), (10, 74)])
def test_transition_contract_accepts_familiar_full_grip_ab_release_slides(
    source_fret: int,
    source_pitch: int,
) -> None:
    source = PositionCandidate(
        fret=source_fret,
        notes=(TabNote(4, source_fret), TabNote(5, source_fret, ("A",)), TabNote(6, source_fret, ("B",))),
        top_pitch=source_pitch,
        controls=("A", "B"),
        family="ab_major",
        note_names=("A", "F#", "D") if source_fret == 5 else ("D", "B", "G"),
        intervals=("5", "3", "1"),
        pattern_family="4-5-6 harmonic path",
        canonical_grip=(4, 5, 6),
    )
    target = PositionCandidate(
        fret=3,
        notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3)),
        top_pitch=67,
        controls=(),
        family="open_major",
        note_names=("G", "D", "B"),
        intervals=("1", "5", "3"),
        pattern_family="4-5-6 harmonic path",
        canonical_grip=(4, 5, 6),
    )

    transition = _transition_between("route", 1, source, target)

    assert transition is not None
    assert transition["kind"] == "bar_slide"
    assert transition["scope"] == "full_grip"
    assert transition["fromFret"] == source_fret and transition["toFret"] == 3
    assert transition["sustainedStrings"] == [4, 5, 6]
    assert transition["repickedStrings"] == transition["releasedStrings"] == []
    assert transition["controlChanges"] == {"pressed": [], "released": ["A", "B"]}
    assert "releasing A+B" in transition["label"]


def test_minor_chord_can_still_use_validated_bc_grip_when_it_is_the_harmonic_arrival() -> None:
    result = melody_exercise_response(
        "Arrange an A minor arrival",
        {"key": "G", "melody": [{"pitch": "A4", "durationBeats": 2, "measure": 1, "beat": 1, "chord": "Am"}]},
    )

    mixed = next(route for route in result["melody_exercise"]["routes"] if route["harmonyType"] == "mixed_arrangement")
    event = mixed["events"][0]
    assert event["canonicalGrip"] == "4-5-6"
    assert event["performanceControls"] == ["B", "C"]
    assert len(event["notes"]) == 3


def test_mixed_path_keeps_an_established_f_lever_pocket_instead_of_jumping_to_ab() -> None:
    """An established lever posture is pocket continuity, not new complexity."""

    candidates = [
        _candidate_for_fretboard_position(position)
        for position in major_positions("G").positions
        if position.is_full_chord
    ]

    def candidate(family: str, grip: tuple[int, ...], top_pitch: int) -> PositionCandidate:
        return next(
            item
            for item in candidates
            if item.family == family and item.canonical_grip == grip and item.top_pitch == top_pitch
        )

    nearby_f_lever = candidate("a_f", (4, 5, 6), 71)
    farther_ab = candidate("a_b_grip", (5, 6, 8), 71)
    inputs = [
        MelodyInput("B4", "B", 3, 11, forced_pitch=71, duration_beats=1, measure=1, beat=1, chord="G"),
        MelodyInput("B4", "B", 3, 11, forced_pitch=71, duration_beats=1, measure=1, beat=2, chord="G"),
    ]

    path = choose_mixed_path(
        [[nearby_f_lever], [nearby_f_lever, farther_ab]],
        inputs=inputs,
        key="G",
    )

    assert path[1].fret == 6
    assert path[1].controls == ("A", "F")
    assert path[1].canonical_grip == (4, 5, 6)


def test_single_note_candidates_use_the_same_canonical_lever_codes_as_grips() -> None:
    item = MelodyInput("G4", "G", 1, 7, forced_pitch=67)

    candidates = single_note_candidates(item, 67)
    f_lever = next(candidate for candidate in candidates if candidate.controls == ("F",))
    e_lower = next(candidate for candidate in candidates if candidate.controls == ("E",))

    assert f_lever.notes[0].changes == ("F",)
    assert e_lower.notes[0].changes == ("E",)
    assert all(
        "lever" not in control.lower() and "lower" not in control.lower()
        for candidate in candidates
        for control in candidate.controls
    )


def test_literal_c_pedal_tab_remains_fixed() -> None:
    result = melody_exercise_response(
        "Keep my literal position",
        {"key": "G", "melody": [{"string": 4, "fret": 5, "changes": ["C"]}]},
    )

    assert result["melody_exercise"]["events"][0]["notes"][0] == {"string": 4, "fret": 5, "changes": ["C"]}


def test_mixed_arrangement_limits_transitions_and_never_places_them_adjacent() -> None:
    melody = [
        {"token": token, "durationBeats": 2, "beat": 1, "chord": "G" if index < 8 else "D7"}
        for index, token in enumerate("1112211233116341")
    ]
    result = melody_exercise_response("Build", {"key": "G", "melody": melody, "wholeSong": True})
    mixed = next(route for route in result["melody_exercise"]["routes"] if route["harmonyType"] == "mixed_arrangement")
    target_steps = [int(transition["toEventId"].rsplit("-", 1)[-1]) for transition in mixed["transitions"]]
    assert len(target_steps) <= 2
    assert all(right - left > 1 for left, right in zip(target_steps, target_steps[1:]))


def test_chord_context_is_not_invented_and_ranks_chord_melody_grips() -> None:
    result = melody_exercise_response(
        "Build a chord-aware phrase",
        {
            "key": "G",
            "melody": [
                {"token": "1", "chord": "G"},
                {"token": "3", "chord": "G"},
                {"token": "5", "chord": "G"},
            ],
        },
    )

    assert result is not None
    exercise = result["melody_exercise"]
    assert [route["harmonyType"] for route in exercise["routes"]] == [
        "single_note", "mixed_arrangement", "thirds", "sixths", "chord_melody"
    ]
    assert [event["harmonySymbol"] for event in exercise["events"]] == ["G", "G", "G"]
    chord_route = next(route for route in exercise["routes"] if route["harmonyType"] == "chord_melody")
    assert chord_route["chordContext"] == {"symbols": ["G"], "usedForRanking": True}
    assert "Chord-aware ranking used: G" in chord_route["recommendation"]
    for event in chord_route["events"]:
        pitch_classes = {
            absolute_pitch_for_string(note["string"], note["fret"], tuple(note["changes"])) % 12
            for note in event["notes"]
        }
        assert pitch_classes <= {2, 7, 11}


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
    melody = ["1", "2", "3", "4", "5", "6", "7", "1"] * 2 + ["3", "2", "1", "7"]
    first = melody_exercise_response(
        "Teach the full arrangement",
        {"kind": "song_arrangement_lesson", "key": "G", "melody": melody, "sectionNumber": 1},
    )
    second = melody_exercise_response(
        "Teach the full arrangement",
        {"kind": "song_arrangement_lesson", "key": "G", "melody": melody, "sectionNumber": 2},
    )

    assert first is not None and second is not None
    assert len(first["melody_exercise"]["events"]) == 16
    assert first["melody_exercise"]["section"]["label"] == "Phrase 1"
    assert first["melody_exercise"]["section"]["total"] == 2
    assert first["melody_exercise"]["section"]["hasMore"] is True
    assert first["melody_exercise"]["section"]["previousSection"] is None
    assert first["melody_exercise"]["section"]["nextSection"] == 2
    assert len(second["melody_exercise"]["events"]) == 4
    assert second["melody_exercise"]["section"]["hasMore"] is False


def test_section_continuation_preserves_full_phrase_octave_contour() -> None:
    melody = ["5", "6", "1", "3", "2", "1", "3", "5"] * 2 + ["6"]
    second = melody_exercise_response(
        "Teach the full arrangement",
        {"kind": "song_arrangement_lesson", "key": "G", "melody": melody, "sectionNumber": 2},
    )

    assert second is not None
    assert [event["resolvedPitch"] for event in second["melody_exercise"]["events"]] == ["E6"]


def test_reviewed_measure_sections_use_phrase_labels_and_ranges() -> None:
    melody = [
        {"pitch": "G4", "measure": 1},
        {"pitch": "A4", "measure": 2},
        {"pitch": "B4", "measure": 5},
        {"pitch": "D5", "measure": 6},
    ]
    sections = [
        {"label": "Opening phrase", "startMeasure": 1, "endMeasure": 4},
        {"label": "Answer phrase", "startMeasure": 5, "endMeasure": 8},
    ]

    result = melody_exercise_response(
        "Teach the complete melody",
        {"kind": "song_arrangement_lesson", "key": "G", "melody": melody, "sections": sections, "sectionNumber": 2},
    )

    assert result is not None
    section = result["melody_exercise"]["section"]
    assert section["label"] == "Answer phrase"
    assert section["eventStart"] == 2
    assert section["eventEnd"] == 4
    assert section["measureStart"] == 5
    assert section["measureEnd"] == 8
    assert section["previousSection"] == 1


def test_every_songbook_complete_form_reaches_the_arranger_as_one_lesson() -> None:
    for card in public_song_catalog():
        draft = import_score_draft({"sourceType": "catalog", "catalogId": card["id"]})
        melody = [event for event in draft["score"]["melody"] if not event.get("rest")]
        result = melody_exercise_response(
            "Arrange this complete song",
            {
                "kind": "song_arrangement_lesson",
                "key": draft["score"]["arrangementKey"],
                "melody": melody,
                "sections": draft["score"]["sections"],
                "wholeSong": True,
            },
        )
        assert result is not None
        exercise = result["melody_exercise"]
        assert exercise["section"]["total"] == 1
        assert exercise["section"]["label"] == "Complete song"
        assert exercise["section"]["eventStart"] == 0
        assert exercise["section"]["eventEnd"] == len(melody)
        assert len(exercise["events"]) == len(melody)
        assert exercise["title"].endswith("Complete E9 lesson") or exercise["title"] == "Song arrangement lesson in G" or exercise["title"] == "Song arrangement lesson in C"


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
