from __future__ import annotations

import pocketsteel.melody_arranger as melody_arranger

from pocketsteel.copedent_transfer import (
    absolute_pitch_for_profile,
    control_tab_label,
    custom_e9_profile_from_payload,
    retarget_fretboard_payload,
    retarget_tab_example_payload,
    resolve_arranger_control,
    resolve_control,
    tab_profile_for_e9,
    transfer_controls,
)
from pocketsteel.e9_copedents import (
    DAY_E9,
    EMMONS_E9,
    CUSTOM_LKV_E9,
    SOURCE_ABC_DEFG_COPEDENT_ID,
    SOURCE_ABC_DEFG_E9,
    get_e9_copedent_profile,
)
from pocketsteel.melody_assistant import melody_exercise_response
from pocketsteel.melody_decision_rules import MODEL_VERSION, rule_contract_payload
from pocketsteel.melody_ranker import score_candidate, train_pairwise_ranker
from pocketsteel.answer_tab_examples import tab_example_payload_for_question
from pocketsteel.fretboard_examples import fretboard_payload_for_question
from pocketsteel.tab_engine import TabEvent, TabNote, render_tab


OPEN_STRINGS = [
    "F#",
    "D#",
    "G#",
    "E",
    "B",
    "G#",
    "F#",
    "E",
    "D",
    "B",
]


def saved_profile_payload(*, controls: list[dict] | None = None, name: str = "Test player's E9") -> dict:
    return {
        "id": "test-player-e9",
        "name": name,
        "tuningFamily": "E9",
        "stringCount": 10,
        "strings": [
            {"stringNumber": index, "openNote": note}
            for index, note in enumerate(OPEN_STRINGS, start=1)
        ],
        "controls": controls or [],
    }


def test_saved_copedent_position_catalog_is_enumerated_once_per_grip_size(monkeypatch) -> None:
    payload = saved_profile_payload(
        controls=[
            {
                "id": "first-floor",
                "label": "P1 B raise",
                "type": "pedal",
                "changes": [
                    {"stringNumber": 5, "fromNote": "B", "toNote": "C#"},
                    {"stringNumber": 10, "fromNote": "B", "toNote": "C#"},
                ],
            },
            {
                "id": "second-floor",
                "label": "P2 G# raise",
                "type": "pedal",
                "changes": [
                    {"stringNumber": 3, "fromNote": "G#", "toNote": "A"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "A"},
                ],
            },
        ]
    )
    calls: list[bool] = []
    original = melody_arranger._generic_harmony_catalog

    def counted_catalog(key, *, chord_melody, profile):
        calls.append(chord_melody)
        return original(key, chord_melody=chord_melody, profile=profile)

    monkeypatch.setattr(melody_arranger, "_generic_harmony_catalog", counted_catalog)
    result = melody_exercise_response(
        "Arrange a repeated phrase",
        {
            "key": "G",
            "targetCopedent": payload,
            "texture": "both",
            "melody": [
                {"pitch": pitch, "pitchValue": value, "chord": "G", "durationBeats": 1}
                for pitch, value in [("G4", 67), ("B4", 71), ("D4", 62), ("G4", 67)] * 2
            ],
        },
    )

    assert result is not None
    assert calls == [False, True]


def test_photographed_source_profile_preserves_exact_d_and_g_mechanics() -> None:
    profile = get_e9_copedent_profile(SOURCE_ABC_DEFG_COPEDENT_ID)
    assert profile is SOURCE_ABC_DEFG_E9

    d = resolve_control(profile, "D")
    g = resolve_control(profile, "G")

    assert [(change.string, change.semitones) for change in d.changes] == [(2, -1)]
    assert [(change.string, change.semitones) for change in g.changes] == [(1, 1), (7, 1)]
    assert absolute_pitch_for_profile(profile, 2, 0, ("D",)) == 62
    assert absolute_pitch_for_profile(profile, 7, 0, ("G",)) == 55

    rendered = render_tab(
        (
            TabEvent(notes=(TabNote(2, 0, ("D",)),)),
            TabEvent(notes=(TabNote(7, 0, ("G",)),)),
        ),
        profile=tab_profile_for_e9(profile),
    )
    assert rendered.ok is True
    assert "0D" in rendered.tab
    assert "0G" in rendered.tab


def test_extra_target_effect_is_safe_only_off_sounding_and_sustained_strings() -> None:
    safe_d = transfer_controls(
        SOURCE_ABC_DEFG_E9,
        ("D",),
        EMMONS_E9,
        sounding_strings=(2,),
    )
    unsafe_d = transfer_controls(
        SOURCE_ABC_DEFG_E9,
        ("D",),
        EMMONS_E9,
        sounding_strings=(2, 9),
    )

    assert safe_d.exact is True
    assert safe_d.target_controls == ("D-lower",)
    assert safe_d.extra_effect_strings == (9,)
    assert unsafe_d.exact is False


def test_core_source_actions_transfer_to_emmons_day_and_app_custom_profiles() -> None:
    for target in (EMMONS_E9, DAY_E9, CUSTOM_LKV_E9):
        transfer = transfer_controls(
            SOURCE_ABC_DEFG_E9,
            ("A", "B"),
            target,
            sounding_strings=(3, 5, 6),
        )
        assert transfer.exact is True, target.id
        assert set(transfer.target_controls) == {"A", "B"}


def test_differently_named_target_control_maps_by_effect_not_label() -> None:
    target = custom_e9_profile_from_payload(
        saved_profile_payload(
            controls=[
                {
                    "id": "right-knee-custom",
                    "label": "My high-string raise",
                    "type": "knee_lever",
                    "changes": [
                        {"stringNumber": 1, "fromNote": "F#", "toNote": "G"},
                        {"stringNumber": 6, "fromNote": "G#", "toNote": "F#"},
                    ],
                }
            ]
        )
    )

    string_one = transfer_controls(
        SOURCE_ABC_DEFG_E9,
        ("G",),
        target,
        sounding_strings=(1,),
    )
    string_seven = transfer_controls(
        SOURCE_ABC_DEFG_E9,
        ("G",),
        target,
        sounding_strings=(7,),
    )

    assert string_one.exact is True
    assert string_one.target_controls == ("right-knee-custom",)
    assert string_one.extra_effect_strings == (6,)
    assert string_seven.exact is False


def test_transfer_uses_stable_ids_when_player_g_label_collides_with_arranger_code() -> None:
    target = custom_e9_profile_from_payload(
        saved_profile_payload(
            controls=[
                {
                    "id": "RKL-half",
                    "label": "G",
                    "type": "lever",
                    "physicalPosition": "RKL",
                    "travel": "half-stop",
                    "changes": [
                        {"stringNumber": 1, "fromNote": "F#", "toNote": "G"},
                        {"stringNumber": 6, "fromNote": "G#", "toNote": "G"},
                    ],
                },
                {
                    "id": "G-lower",
                    "label": "GG",
                    "type": "lever",
                    "physicalPosition": "RKL",
                    "travel": "full-stop",
                    "changes": [
                        {"stringNumber": 1, "fromNote": "F#", "toNote": "G#"},
                        {"stringNumber": 6, "fromNote": "G#", "toNote": "F#"},
                    ],
                },
            ]
        )
    )

    transfer = transfer_controls(
        EMMONS_E9,
        ("G",),
        target,
        sounding_strings=(6,),
    )

    assert transfer.exact is True
    assert transfer.target_controls == ("G-lower",)
    assert resolve_control(target, transfer.target_controls[0]).label == "GG"
    assert resolve_arranger_control(target, "G").label == "GG"
    assert resolve_control(target, "RKL-half").label == "G"


def test_complete_song_arranges_when_player_uses_distinct_g_and_gg_labels() -> None:
    target_payload = saved_profile_payload(
        controls=[
            {
                "id": "A",
                "label": "A pedal",
                "type": "pedal",
                "physicalPosition": "P1",
                "aliases": ["A", "P1"],
                "changes": [
                    {"stringNumber": 5, "fromNote": "B", "toNote": "C#"},
                    {"stringNumber": 10, "fromNote": "B", "toNote": "C#"},
                ],
            },
            {
                "id": "B",
                "label": "B pedal",
                "type": "pedal",
                "physicalPosition": "P2",
                "aliases": ["B", "P2"],
                "changes": [
                    {"stringNumber": 3, "fromNote": "G#", "toNote": "A"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "A"},
                ],
            },
            {
                "id": "C",
                "label": "C pedal",
                "type": "pedal",
                "physicalPosition": "P3",
                "aliases": ["C", "P3"],
                "changes": [
                    {"stringNumber": 4, "fromNote": "E", "toNote": "F#"},
                    {"stringNumber": 5, "fromNote": "B", "toNote": "C#"},
                ],
            },
            {
                "id": "RKL-half",
                "label": "G",
                "type": "lever",
                "physicalPosition": "RKL",
                "travel": "half-stop",
                "changes": [
                    {"stringNumber": 1, "fromNote": "F#", "toNote": "G"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "G"},
                ],
            },
            {
                "id": "G-lower",
                "label": "GG",
                "type": "lever",
                "physicalPosition": "RKL",
                "travel": "full-stop",
                "changes": [
                    {"stringNumber": 1, "fromNote": "F#", "toNote": "G#"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "F#"},
                ],
            },
        ]
    )
    target = custom_e9_profile_from_payload(target_payload)
    melody = [
        {"token": note, "pitch": note, "measure": index // 4 + 1, "beat": index % 4 + 1}
        for index, note in enumerate(
            [
                "C4", "E4", "F4", "G4", "C4", "E4", "F4", "G4",
                "C4", "E4", "F4", "G4", "E4", "C4", "E4", "D4",
                "E4", "E4", "D4", "C4", "E4", "G4", "G4", "F4",
                "E4", "F4", "G4", "E4", "C4", "D4", "C4",
            ]
        )
    ]

    result = melody_exercise_response(
        "Arrange the complete song for E9",
        {
            "kind": "song_arrangement_lesson",
            "key": "C",
            "melody": melody,
            "wholeSong": True,
            "targetCopedent": target_payload,
            "targetCopedentId": target_payload["id"],
            "texture": "both",
        },
    )["melody_exercise"]

    assert result["status"] == "ready"
    assert result["section"]["eventEnd"] == len(melody)
    assert control_tab_label(target, "A") == "A"
    assert control_tab_label(target, "B") == "B"
    assert control_tab_label(target, "C") == "C"
    assert all(
        event["performanceControlLabels"] == [
            control_tab_label(target, control)
            for control in event["performanceControls"]
        ]
        for route in result["routes"]
        for event in route["events"]
    )
    rendered_tabs = "\n".join(route["tabExample"]["rendered_tab"] for route in result["routes"])
    assert "A pedal" not in rendered_tabs
    assert "B pedal" not in rendered_tabs
    assert "C pedal" not in rendered_tabs
    assert "A" in rendered_tabs


def test_answer_fretboard_and_tab_are_retargeted_with_user_labels() -> None:
    target = custom_e9_profile_from_payload(
        saved_profile_payload(
            name="Road setup",
            controls=[
                {
                    "id": "road-a",
                    "label": "Inside raise",
                    "type": "pedal",
                    "physicalPosition": "P3",
                    "changes": [
                        {"stringNumber": 5, "fromNote": "B", "toNote": "C#"},
                        {"stringNumber": 10, "fromNote": "B", "toNote": "C#"},
                    ],
                },
                {
                    "id": "road-b",
                    "label": "Middle raise",
                    "type": "pedal",
                    "physicalPosition": "P2",
                    "changes": [
                        {"stringNumber": 3, "fromNote": "G#", "toNote": "A"},
                        {"stringNumber": 6, "fromNote": "G#", "toNote": "A"},
                    ],
                },
                {
                    "id": "E-raise",
                    "label": "Road F",
                    "type": "lever",
                    "physicalPosition": "LKV",
                    "changes": [
                        {"stringNumber": 4, "fromNote": "E", "toNote": "F"},
                        {"stringNumber": 8, "fromNote": "E", "toNote": "F"},
                    ],
                },
            ],
        )
    )
    fretboard = retarget_fretboard_payload(fretboard_payload_for_question("How do I play a G chord on E9?"), target)
    tab = retarget_tab_example_payload(tab_example_payload_for_question("Show me a G to C move"), target)

    assert fretboard is not None
    assert fretboard["copedent"]["id"] == "saved:test-player-e9"
    assert all(position["targetCopedentId"] == "saved:test-player-e9" for position in fretboard["positions"])
    assert any("Inside raise (P3)" in position["pedals"] for position in fretboard["positions"])
    assert any("Road F (LKV)" in position["levers"] for position in fretboard["positions"])
    assert tab is not None
    assert tab["validation"]["profile"] == "saved:test-player-e9"
    assert "Inside raise (P3)" in tab["rendered_tab"]
    assert "Middle raise (P2)" in tab["rendered_tab"]
    assert tab["events"][1]["controlStates"][0]["physicalPosition"] == "P3"


def test_retarget_rejects_a_same_note_in_the_wrong_register() -> None:
    payload = saved_profile_payload()
    payload["strings"] = [
        {**row, **({"openPitchValue": 76} if row["stringNumber"] == 4 else {})}
        for row in payload["strings"]
    ]
    target = custom_e9_profile_from_payload(payload)
    fretboard = {
        "positions": [{"id": "open-e", "fret": 0, "strings": [4], "pedals": [], "levers": []}],
        "highlights": [{"id": "open-e", "fret": 0, "strings": [4], "pedals": [], "levers": []}],
    }

    assert retarget_fretboard_payload(fretboard, target) is None


def test_source_literal_is_decoded_then_rearranged_for_day_target() -> None:
    result = melody_exercise_response(
        "Transfer this reviewed source note",
        {
            "key": "G",
            "sourceCopedentId": SOURCE_ABC_DEFG_COPEDENT_ID,
            "targetCopedentId": DAY_E9.id,
            "melody": [{"string": 7, "fret": 0, "changes": ["G"]}],
        },
    )

    assert result is not None
    exercise = result["melody_exercise"]
    event = exercise["events"][0]
    assert exercise["sourceCopedentId"] == SOURCE_ABC_DEFG_COPEDENT_ID
    assert exercise["targetCopedentId"] == DAY_E9.id
    assert exercise["arrangedFor"] == "Day E9 starter"
    assert event["pitchValue"] == 55
    assert event["sourceAction"]["string"] == 7
    assert event["sourceAction"]["semitoneChange"] == 1
    assert event["targetCopedentId"] == DAY_E9.id
    assert 55 in event["mechanicalPitchesByString"].values()
    assert not any(note["string"] == 7 and "G" in note["changes"] for note in event["notes"])


def test_saved_user_profile_drives_runtime_labels_and_synchronized_pitches() -> None:
    payload = saved_profile_payload(
        name="Road guitar E9",
        controls=[
            {
                "id": "first-floor",
                "label": "P1 B raise",
                "type": "pedal",
                "changes": [
                    {"stringNumber": 5, "fromNote": "B", "toNote": "C#"},
                    {"stringNumber": 10, "fromNote": "B", "toNote": "C#"},
                ],
            },
            {
                "id": "second-floor",
                "label": "P2 G# raise",
                "type": "pedal",
                "changes": [
                    {"stringNumber": 3, "fromNote": "G#", "toNote": "A"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "A"},
                ],
            },
        ],
    )
    result = melody_exercise_response(
        "Arrange for my road guitar",
        {
            "key": "G",
            "targetCopedent": payload,
            "melody": [
                {"pitch": "E4", "pitchValue": 64, "chord": "C", "durationBeats": 2},
                {"pitch": "G4", "pitchValue": 67, "chord": "G", "durationBeats": 2},
            ],
        },
    )

    assert result is not None
    exercise = result["melody_exercise"]
    assert exercise["targetCopedentId"] == "saved:test-player-e9"
    assert exercise["arrangedFor"] == "Road guitar E9"
    assert "arranged for Road guitar E9" in result["answer"]
    for route in exercise["routes"]:
        assert route["targetCopedentId"] == "saved:test-player-e9"
        assert route["arrangedFor"] == "Road guitar E9"
        for event in route["events"]:
            assert event["pitchValue"] == max(event["mechanicalPitchesByString"].values())
            assert all("A pedal" not in label for label in event["performanceControlLabels"])
            assert "first-floor" not in event["movement"]
            assert "second-floor" not in event["movement"]
    labeled_route = next(route for route in exercise["routes"] if "P1 B raise" in route["tabExample"]["rendered_tab"])
    assert "first-floor" not in labeled_route["tabExample"]["rendered_tab"]
    assert any(
        note.get("changeLabels") == ["P1 B raise"]
        for event in labeled_route["events"]
        for note in event["notes"]
    )


def test_missing_target_harmony_falls_back_to_exact_single_melody_with_reason() -> None:
    payload = {
        **saved_profile_payload(name="Sparse test E9"),
        "strings": [
            {"stringNumber": index, "openNote": "C"}
            for index in range(1, 11)
        ],
    }
    result = melody_exercise_response(
        "Preserve this melody when harmony is unavailable",
        {
            "key": "G",
            "targetCopedent": payload,
            "melody": [{"pitch": "G4", "pitchValue": 67, "chord": "G", "durationBeats": 2}],
        },
    )

    mixed = next(
        route for route in result["melody_exercise"]["routes"]
        if route["harmonyType"] == "mixed_arrangement"
    )
    event = mixed["events"][0]
    assert len(event["notes"]) == 1
    assert event["pitchValue"] == 67 == max(event["mechanicalPitchesByString"].values())
    assert event["textureFallback"]["requestedVoices"] == 3
    assert event["textureFallback"]["realizedVoices"] == 1
    assert mixed["fallbacks"][0]["eventId"] == event["id"]


def test_rule_contract_is_versioned_and_documents_ordered_texture_fallback() -> None:
    contract = rule_contract_payload("vocal_steel")

    assert contract["modelVersion"] == MODEL_VERSION
    assert contract["modelVersion"] == "at-44c59f08724d501e"
    assert contract["modelStatus"] == "approved_beta"
    assert contract["modelMetadata"]["exampleCount"] == 45
    assert contract["modelMetadata"]["copedentNeutral"] is True
    assert contract["styleFamily"] == "vocal_steel"
    assert contract["fallbackOrder"][2] == "reduce_triad_to_dyad_to_single_melody"
    assert all(
        {
            "id",
            "musical_context",
            "kind",
            "source_evidence",
            "abstract_intent",
            "required_capabilities",
            "transfer_behavior",
            "fallback_behavior",
            "confidence",
            "model_version",
        }
        <= set(rule)
        for rule in contract["rules"]
    )


def test_style_family_changes_soft_texture_ranking_without_changing_melody() -> None:
    common = {
        "key": "G",
        "melody": [{"pitch": "G4", "pitchValue": 67, "chord": "G", "durationBeats": 2}],
    }
    auto = melody_exercise_response("Arrange", {**common, "styleFamily": "auto"})
    run = melody_exercise_response("Arrange", {**common, "styleFamily": "single_note_run"})
    auto_mixed = next(route for route in auto["melody_exercise"]["routes"] if route["harmonyType"] == "mixed_arrangement")
    run_mixed = next(route for route in run["melody_exercise"]["routes"] if route["harmonyType"] == "mixed_arrangement")

    assert len(auto_mixed["events"][0]["notes"]) == 3
    assert len(run_mixed["events"][0]["notes"]) == 1
    assert auto_mixed["events"][0]["pitchValue"] == run_mixed["events"][0]["pitchValue"] == 67


def test_private_ranker_learns_abstract_choice_without_copedent_labels() -> None:
    chosen = {
        "textureSize": 2,
        "barTravel": 0,
        "controlChanges": 0,
        "pocketChanges": 0,
        "voiceLeading": 1,
        "sustainedVoices": 2,
        "repickedVoices": 0,
        "phraseRole": "sustained_note",
    }
    rejected = {
        "textureSize": 3,
        "barTravel": 5,
        "controlChanges": 2,
        "pocketChanges": 1,
        "voiceLeading": 8,
        "sustainedVoices": 0,
        "repickedVoices": 3,
        "phraseRole": "sustained_note",
    }
    model = train_pairwise_ranker(
        [{"styleFamily": "vocal_steel", "chosen": chosen, "alternatives": [rejected]}],
        epochs=3,
    )
    weights = model.weights_by_style["vocal_steel"]

    assert model.example_count == 1
    assert score_candidate(chosen, weights) < score_candidate(rejected, weights)
    assert all("string" not in feature.lower() and "control_label" not in feature.lower() for feature in model.feature_names)
