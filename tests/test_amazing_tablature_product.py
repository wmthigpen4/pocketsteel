from __future__ import annotations

import pytest

from steel_guitar_rag.amazing_tablature_product import (
    ARRANGEMENT_RESPONSE_SCHEMA_VERSION,
    build_arrangement_contract,
    resolve_arrangement_preferences,
    route_signature,
)
from steel_guitar_rag.melody_assistant import melody_exercise_response


@pytest.mark.parametrize(
    ("voice_mode", "texture"),
    [
        ("single", "single_note"),
        ("two_voice", "automatic_harmony"),
        ("three_voice", "chord_melody"),
        ("mixed", "both"),
    ],
)
def test_public_voice_modes_map_to_existing_validated_arranger_textures(
    voice_mode: str,
    texture: str,
) -> None:
    preferences = resolve_arrangement_preferences(
        {"voiceMode": voice_mode, "movementMode": "best_fit"}
    )
    assert preferences.arranger_texture == texture


@pytest.mark.parametrize(
    ("movement_mode", "style"),
    [
        ("best_fit", "auto"),
        ("slides", "vocal_steel"),
        ("pedal_lever", "lever_driven"),
        ("compact_pocket", "fixed_pocket"),
        ("clean_repick", "single_note_run"),
    ],
)
def test_public_movement_modes_map_to_concrete_arranger_policies(
    movement_mode: str,
    style: str,
) -> None:
    preferences = resolve_arrangement_preferences(
        {"voiceMode": "mixed", "movementMode": movement_mode}
    )
    assert preferences.arranger_style == style


def test_contract_hides_exact_duplicate_routes_and_discloses_provenance() -> None:
    event = {"notes": [{"string": 4, "fret": 3, "changes": []}]}
    route = {
        "id": "recommended",
        "label": "Recommended",
        "harmonyType": "single_note",
        "recommended": True,
        "events": [event],
        "transitions": [],
        "tabExample": {"validation": {"ok": True, "eventCount": 1}},
    }
    duplicate = {
        **route,
        "id": "decorative-duplicate",
        "label": "Different label, same tab",
        "recommended": False,
    }
    preferences = resolve_arrangement_preferences(
        {"voiceMode": "single", "movementMode": "best_fit"}
    )
    routes, contract = build_arrangement_contract(
        [route, duplicate],
        preferences=preferences,
        model_metadata={"rankerEnabled": False, "modelId": "deterministic-fallback-v1"},
    )

    assert len(routes) == 1
    assert len({route_signature(item) for item in routes}) == 1
    assert contract["schemaVersion"] == ARRANGEMENT_RESPONSE_SCHEMA_VERSION
    assert contract["recommendedRouteId"] == "recommended"
    assert contract["alternatives"] == []
    assert contract["validation"]["ok"] is True
    assert contract["provenance"]["claim"].startswith("Verified E9 rules")


def test_mixed_best_fit_prefers_deterministic_key_harmony_over_learned_route() -> None:
    def route(
        route_id: str,
        harmony_type: str,
        *,
        fret: int,
        travel: int,
        engine_mode: str = "deterministic_rules",
    ) -> dict[str, object]:
        return {
            "id": route_id,
            "label": route_id,
            "harmonyType": harmony_type,
            "engineMode": engine_mode,
            "recommended": False,
            "pathSummary": {
                "totalBarTravel": travel,
                "harmonicFamilyChanges": 0,
                "stringGroupChanges": 0,
                "pedalFamilyChanges": 0,
                "maxBarTravel": travel,
            },
            "events": [
                {
                    "notes": [
                        {"string": 4, "fret": fret, "changes": []},
                        {"string": 6, "fret": fret, "changes": []},
                    ]
                }
            ],
            "transitions": [],
            "tabExample": {"validation": {"ok": True, "eventCount": 1}},
        }

    routes, contract = build_arrangement_contract(
        [
            route(
                "learned",
                "mixed_arrangement",
                fret=3,
                travel=0,
                engine_mode="private_learned_beta",
            ),
            route("thirds", "thirds", fret=4, travel=8),
            route("sixths", "sixths", fret=5, travel=3),
        ],
        preferences=resolve_arrangement_preferences(
            {"voiceMode": "mixed", "movementMode": "best_fit"}
        ),
        model_metadata={"rankerEnabled": True, "modelId": "at-test"},
    )

    assert contract["recommendedRouteId"] == "sixths"
    assert contract["requestedVoiceModeAvailable"] is True
    selected = next(item for item in routes if item["recommended"])
    assert selected["harmonyType"] == "sixths"
    assert selected["provenance"]["learnedPreferenceApplied"] is False


def test_chord_aware_harmony_stays_recommended_for_non_best_fit_movement() -> None:
    def route(
        route_id: str,
        harmony_type: str,
        *,
        fret: int,
        engine_mode: str = "deterministic_rules",
        recommended: bool = False,
    ) -> dict[str, object]:
        return {
            "id": route_id,
            "label": route_id,
            "harmonyType": harmony_type,
            "engineMode": engine_mode,
            "recommended": recommended,
            "events": [
                {
                    "notes": [
                        {"string": 4, "fret": fret, "changes": []},
                        {"string": 6, "fret": fret, "changes": []},
                    ]
                }
            ],
            "transitions": [],
            "tabExample": {"validation": {"ok": True, "eventCount": 1}},
        }

    routes, contract = build_arrangement_contract(
        [
            route(
                "learned",
                "mixed_arrangement",
                fret=5,
                engine_mode="private_learned_beta",
            ),
            route(
                "chord-aware",
                "chord_aware_harmony",
                fret=3,
                recommended=True,
            ),
        ],
        preferences=resolve_arrangement_preferences(
            {"voiceMode": "mixed", "movementMode": "slides"}
        ),
        model_metadata={"rankerEnabled": True, "modelId": "at-test"},
    )

    assert contract["recommendedRouteId"] == "chord-aware"
    selected = next(item for item in routes if item["recommended"])
    assert selected["harmonyType"] == "chord_aware_harmony"
    assert selected["provenance"]["learnedPreferenceApplied"] is False


@pytest.mark.parametrize(
    "key",
    ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
)
def test_amazing_tablature_arranges_major_scale_input_in_all_twelve_keys(
    key: str,
) -> None:
    result = melody_exercise_response(
        "Build",
        {
            "key": key,
            "melody": ["1", "2", "3", "5"],
            "voiceMode": "mixed",
            "movementMode": "best_fit",
        },
    )

    exercise = result["melody_exercise"]
    contract = exercise["arrangementContract"]
    assert exercise["input"]["key"] == key
    assert contract["validation"]["ok"] is True
    assert contract["validation"]["eventCount"] == 4
    assert contract["request"]["voiceMode"] == "mixed"
    selected = next(
        route for route in exercise["routes"] if route["id"] == exercise["selectedRouteId"]
    )
    assert selected["validation"]["ok"] is True
    assert len(selected["events"]) == len(selected["fretboard"]["positions"]) == 4


def test_three_voice_request_falls_back_honestly_without_chord_context() -> None:
    result = melody_exercise_response(
        "Build",
        {
            "key": "G",
            "melody": ["1", "2", "3"],
            "voiceMode": "three_voice",
            "movementMode": "best_fit",
        },
    )

    contract = result["melody_exercise"]["arrangementContract"]
    assert contract["requestedVoiceModeAvailable"] is False
    assert "closest valid texture" in contract["fallbackDisclosure"]
