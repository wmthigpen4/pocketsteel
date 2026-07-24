"""Public Amazing Tablature product contract.

The private ranker may influence ordering, but this module exposes only
normalized musical controls and sanitized provenance.  It never weakens the
arranger's pitch, register, harmony, or mechanical validation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


ARRANGEMENT_REQUEST_SCHEMA_VERSION = "amazing_tablature_request_v1"
ARRANGEMENT_RESPONSE_SCHEMA_VERSION = "amazing_tablature_response_v1"

VOICE_MODES: tuple[dict[str, str], ...] = (
    {
        "id": "single",
        "label": "Single note",
        "description": "One clear melody voice with economical picking.",
    },
    {
        "id": "two_voice",
        "label": "Two note",
        "description": "Melody plus one validated harmony voice.",
    },
    {
        "id": "three_voice",
        "label": "Three note",
        "description": "Melody on top of a validated three-string grip when harmony permits.",
    },
    {
        "id": "mixed",
        "label": "Mixed",
        "description": "Moves between one, two, and three voices according to phrase role.",
    },
)

MOVEMENT_MODES: tuple[dict[str, str], ...] = (
    {
        "id": "best_fit",
        "label": "Best fit",
        "description": "Balances texture, travel, controls, phrase role, and the active copedent.",
    },
    {
        "id": "slides",
        "label": "Slides",
        "description": "Favors connected singing positions where a validated bar slide is available.",
    },
    {
        "id": "pedal_lever",
        "label": "Pedal & lever",
        "description": "Favors expressive pedal or lever motion under a steady bar.",
    },
    {
        "id": "compact_pocket",
        "label": "Stay in a pocket",
        "description": "Favors a compact fret and string-group neighborhood.",
    },
    {
        "id": "clean_repick",
        "label": "Clean repicks",
        "description": "Favors direct attacks and economical single-note movement.",
    },
)

_VOICE_TO_TEXTURE = {
    "single": "single_note",
    "two_voice": "automatic_harmony",
    "three_voice": "chord_melody",
    "mixed": "both",
}
_TEXTURE_TO_VOICE = {
    "single_note": "single",
    "automatic_harmony": "two_voice",
    "thirds": "two_voice",
    "sixths": "two_voice",
    "chord_melody": "three_voice",
    "mixed_arrangement": "mixed",
    "both": "mixed",
}
_MOVEMENT_TO_STYLE = {
    "best_fit": "auto",
    "slides": "vocal_steel",
    "pedal_lever": "lever_driven",
    "compact_pocket": "fixed_pocket",
    "clean_repick": "single_note_run",
}
_STYLE_TO_MOVEMENT = {
    "auto": "best_fit",
    "vocal_steel": "slides",
    "lever_driven": "pedal_lever",
    "fixed_pocket": "compact_pocket",
    "single_note_run": "clean_repick",
    "harmonized": "best_fit",
    "chord_melody": "best_fit",
}


@dataclass(frozen=True)
class ArrangementPreferences:
    voice_mode: str
    movement_mode: str
    arranger_texture: str
    arranger_style: str

    def to_dict(self) -> dict[str, str]:
        return {
            "voiceMode": self.voice_mode,
            "movementMode": self.movement_mode,
            "arrangerTexture": self.arranger_texture,
            "arrangerStyle": self.arranger_style,
        }


def resolve_arrangement_preferences(
    request: Mapping[str, Any] | None,
) -> ArrangementPreferences:
    """Resolve the public two-control contract and legacy request aliases."""

    payload = request or {}
    explicit_voice = payload.get("voiceMode") or payload.get("voice_mode")
    legacy_texture = str(payload.get("texture") or "").strip().lower()
    voice_mode = str(explicit_voice or _TEXTURE_TO_VOICE.get(legacy_texture) or "mixed").strip().lower()
    voice_mode = {
        "one": "single",
        "one_voice": "single",
        "single_note": "single",
        "two": "two_voice",
        "dyad": "two_voice",
        "three": "three_voice",
        "triad": "three_voice",
        "automatic": "mixed",
    }.get(voice_mode, voice_mode)
    if voice_mode not in _VOICE_TO_TEXTURE:
        raise ValueError("Voice mode must be single, two_voice, three_voice, or mixed.")

    explicit_movement = payload.get("movementMode") or payload.get("movement_mode")
    legacy_style = str(
        payload.get("styleFamily") or payload.get("style_family") or ""
    ).strip().lower()
    movement_mode = str(
        explicit_movement or _STYLE_TO_MOVEMENT.get(legacy_style) or "best_fit"
    ).strip().lower()
    movement_mode = {
        "pedals": "pedal_lever",
        "pedal_and_lever": "pedal_lever",
        "pocket": "compact_pocket",
        "repick": "clean_repick",
        "repicks": "clean_repick",
    }.get(movement_mode, movement_mode)
    if movement_mode not in _MOVEMENT_TO_STYLE:
        raise ValueError(
            "Movement mode must be best_fit, slides, pedal_lever, compact_pocket, or clean_repick."
        )

    arranger_style = (
        legacy_style
        if legacy_style and not explicit_movement
        else _MOVEMENT_TO_STYLE[movement_mode]
    )
    return ArrangementPreferences(
        voice_mode=voice_mode,
        movement_mode=movement_mode,
        arranger_texture=_VOICE_TO_TEXTURE[voice_mode],
        arranger_style=arranger_style,
    )


def arrangement_control_catalog() -> dict[str, list[dict[str, str]]]:
    return {
        "voiceModes": [dict(item) for item in VOICE_MODES],
        "movementModes": [dict(item) for item in MOVEMENT_MODES],
    }


def _event_signature(event: Mapping[str, Any]) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                int(note.get("string") or 0),
                int(note.get("fret") or 0),
                tuple(sorted(str(change) for change in note.get("changes") or ())),
            )
            for note in event.get("notes") or ()
        )
    )


def route_signature(route: Mapping[str, Any]) -> tuple[tuple[tuple[object, ...], ...], ...]:
    return tuple(_event_signature(event) for event in route.get("events") or ())


def _route_voice_mode(route: Mapping[str, Any]) -> str:
    sizes = {
        len(event.get("notes") or ())
        for event in route.get("events") or ()
        if event.get("notes")
    }
    if sizes == {1}:
        return "single"
    if sizes == {2}:
        return "two_voice"
    if sizes == {3}:
        return "three_voice"
    return "mixed"


def _movement_types(route: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for transition in route.get("transitions") or ():
        kind = str(transition.get("kind") or "").strip()
        if kind and kind not in values:
            values.append(kind)
    if not values:
        values.append("clean_attack")
    return values


def _difference_reasons(
    candidate: Mapping[str, Any],
    recommended: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    candidate_mode = _route_voice_mode(candidate)
    recommended_mode = _route_voice_mode(recommended)
    if candidate_mode != recommended_mode:
        reasons.append(f"changes texture from {recommended_mode} to {candidate_mode}")
    candidate_movements = _movement_types(candidate)
    recommended_movements = _movement_types(recommended)
    if candidate_movements != recommended_movements:
        reasons.append(
            "changes movement from "
            + ", ".join(recommended_movements)
            + " to "
            + ", ".join(candidate_movements)
        )
    changed_positions = sum(
        left != right
        for left, right in zip(
            route_signature(candidate),
            route_signature(recommended),
        )
    )
    changed_positions += abs(
        len(route_signature(candidate)) - len(route_signature(recommended))
    )
    if changed_positions:
        reasons.append(f"changes {changed_positions} tab position{'s' if changed_positions != 1 else ''}")
    return reasons


def _recommended_route(
    routes: Sequence[dict[str, Any]],
    preferences: ArrangementPreferences,
) -> dict[str, Any]:
    preferred_types = {
        "single": ("single_note",),
        "two_voice": ("automatic_harmony", "thirds", "sixths"),
        "three_voice": ("chord_melody",),
        "mixed": ("mixed_arrangement",),
    }[preferences.voice_mode]
    for engine_mode in ("private_learned_beta",):
        match = next(
            (
                route
                for route in routes
                if route.get("engineMode") == engine_mode
                and route.get("harmonyType") in preferred_types
            ),
            None,
        )
        if match is not None:
            return match
    match = next(
        (
            route
            for route in routes
            if route.get("harmonyType") in preferred_types
            and route.get("recommended")
        ),
        None,
    )
    if match is not None:
        return match
    match = next(
        (route for route in routes if route.get("harmonyType") in preferred_types),
        None,
    )
    return match or next(
        (route for route in routes if route.get("recommended")),
        routes[0],
    )


def _provenance(route: Mapping[str, Any]) -> dict[str, object]:
    engine_mode = str(route.get("engineMode") or "deterministic_rules")
    learned = engine_mode == "private_learned_beta"
    return {
        "selection": "learned_ranker_with_deterministic_gates" if learned else "deterministic_rules",
        "modelId": str(route.get("modelId") or "") or None,
        "learnedPreferenceApplied": learned,
        "hardValidation": [
            "melody_pitch",
            "scientific_register",
            "chord_context",
            "copedent_mechanics",
        ],
        "sourcePagesExposed": False,
    }


def build_arrangement_contract(
    routes: Sequence[dict[str, Any]],
    *,
    preferences: ArrangementPreferences,
    model_metadata: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deduplicate, annotate, and select honest public arrangement routes."""

    if not routes:
        raise ValueError("At least one validated arrangement route is required.")

    unique_routes: list[dict[str, Any]] = []
    seen: set[tuple[tuple[tuple[object, ...], ...], ...]] = set()
    for route in routes:
        signature = route_signature(route)
        if signature in seen:
            continue
        seen.add(signature)
        unique_routes.append(route)

    recommended = _recommended_route(unique_routes, preferences)
    requested_voice_available = (
        _route_voice_mode(recommended) == preferences.voice_mode
        or (
            preferences.voice_mode == "mixed"
            and recommended.get("harmonyType") == "mixed_arrangement"
        )
    )
    for route in unique_routes:
        route["recommended"] = route is recommended
        route["voiceMode"] = _route_voice_mode(route)
        route["movementMode"] = preferences.movement_mode
        route["movementTypes"] = _movement_types(route)
        route["arrangementPolicy"] = {
            "requestedVoiceMode": preferences.voice_mode,
            "realizedVoiceMode": route["voiceMode"],
            "movementMode": preferences.movement_mode,
        }
        route["provenance"] = _provenance(route)
        route["validation"] = dict(
            (route.get("tabExample") or {}).get("validation") or {"ok": False}
        )
        reasons = [] if route is recommended else _difference_reasons(route, recommended)
        route["materialDifferenceReasons"] = reasons
        route["materiallyDistinct"] = route is recommended or bool(reasons)

    visible_routes = [
        route for route in unique_routes if route.get("materiallyDistinct")
    ]
    route_catalog = [
        {
            "routeId": route["id"],
            "label": route["label"],
            "voiceMode": route["voiceMode"],
            "movementTypes": list(route["movementTypes"]),
            "recommended": bool(route["recommended"]),
            "differenceReasons": list(route["materialDifferenceReasons"]),
            "selectionProvenance": route["provenance"]["selection"],
        }
        for route in visible_routes
    ]
    contract = {
        "schemaVersion": ARRANGEMENT_RESPONSE_SCHEMA_VERSION,
        "requestSchemaVersion": ARRANGEMENT_REQUEST_SCHEMA_VERSION,
        "request": preferences.to_dict(),
        "controls": arrangement_control_catalog(),
        "recommendedRouteId": recommended["id"],
        "requestedVoiceModeAvailable": requested_voice_available,
        "fallbackDisclosure": (
            ""
            if requested_voice_available
            else "The requested texture was unavailable after pitch, harmony, and mechanical checks; the closest valid texture is shown."
        ),
        "routes": route_catalog,
        "alternatives": [
            item for item in route_catalog if not item["recommended"]
        ],
        "provenance": {
            "rankerEnabled": bool((model_metadata or {}).get("rankerEnabled")),
            "modelId": (model_metadata or {}).get("modelId"),
            "scoreImageRecognitionIncluded": False,
            "claim": (
                "Learned ranking chooses among candidates that already passed deterministic gates."
                if (model_metadata or {}).get("rankerEnabled")
                else "Verified E9 rules choose among candidates that passed deterministic gates."
            ),
        },
        "validation": {
            "ok": all(bool(route.get("validation", {}).get("ok")) for route in visible_routes),
            "routeCount": len(visible_routes),
            "eventCount": len(recommended.get("events") or ()),
            "checks": [
                "melody_pitch",
                "scientific_register",
                "chord_context",
                "copedent_mechanics",
                "synchronized_tab_and_fretboard",
            ],
        },
    }
    return visible_routes, contract
