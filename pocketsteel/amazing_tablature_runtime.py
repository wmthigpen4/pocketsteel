"""Fail-closed private runtime adapter for an Amazing Tablature challenger.

The frozen arranger and ranker own feature calculation and hard mechanical
validation.  This module only loads a hash-pinned sanitized policy, asks the
frozen engine for a learned mixed path, and keeps the deterministic path beside
it for an honest private-beta comparison.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pocketsteel.amazing_tablature_model import (
    CANONICAL_STYLE_FAMILIES,
    RuntimeRankerPolicy,
    deterministic_fallback_policy,
    load_sanitized_ranker_artifact,
)
from pocketsteel.copedent_transfer import resolve_target_profile
from pocketsteel.e9_copedents import (
    DEFAULT_COPEDENT_ID,
    get_e9_copedent_profile,
    scientific_pitch_for_value,
)
from pocketsteel.melody_arranger import (
    _active_chords,
    _phrase_boundaries,
    _recommendation_for,
    arrange_melody_routes,
    build_route,
    choose_path,
    choose_mixed_path,
    harmony_candidate_groups,
    mixed_candidate_groups,
    parse_melody_inputs,
    resolve_contour,
    single_note_candidates,
)
from pocketsteel.melody_decision_rules import normalize_style_family
from pocketsteel.melody_models import SUPPORTED_CONTOURS, SUPPORTED_TEXTURES


ENABLE_PRIVATE_BETA_ENV = "STEEL_RAG_ENABLE_AMAZING_TABLATURE_BETA"
PRIVATE_MODEL_PATH_ENV = "STEEL_RAG_AMAZING_TABLATURE_MODEL_PATH"
PRIVATE_MODEL_ID_ENV = "STEEL_RAG_AMAZING_TABLATURE_MODEL_ID"
PRIVATE_MODEL_SHA256_ENV = "STEEL_RAG_AMAZING_TABLATURE_MODEL_SHA256"


def _enabled(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def configured_private_ranker_policy(
    env: Mapping[str, str] | None = None,
) -> RuntimeRankerPolicy:
    """Load the exact configured artifact or return deterministic fallback."""

    values = env or os.environ
    if not _enabled(values.get(ENABLE_PRIVATE_BETA_ENV)):
        return deterministic_fallback_policy("private_beta_disabled")
    model_path = str(values.get(PRIVATE_MODEL_PATH_ENV) or "").strip()
    model_id = str(values.get(PRIVATE_MODEL_ID_ENV) or "").strip()
    model_sha256 = str(values.get(PRIVATE_MODEL_SHA256_ENV) or "").strip().lower()
    if not model_path or not model_id or len(model_sha256) != 64:
        return deterministic_fallback_policy("private_beta_configuration_incomplete")
    path = Path(model_path).expanduser()
    if not path.is_absolute():
        return deterministic_fallback_policy("private_beta_path_not_absolute")
    try:
        artifact_bytes = path.read_bytes()
    except OSError:
        return deterministic_fallback_policy("private_beta_artifact_unreadable")
    return load_sanitized_ranker_artifact(
        artifact_bytes,
        expected_model_id=model_id,
        expected_sha256=model_sha256,
    )


def private_beta_enabled(policy: RuntimeRankerPolicy | None) -> bool:
    return bool(policy and policy.shadow_eligible and policy.failure_reason is None)


def private_beta_model_metadata(
    policy: RuntimeRankerPolicy | None,
    *,
    comparison_changed_events: int | None = None,
    comparison_event_count: int | None = None,
) -> dict[str, object]:
    """Return non-sensitive UI metadata for the active or fallback engine."""

    if not private_beta_enabled(policy):
        return {
            "modelId": "deterministic-fallback-v1",
            "status": "deterministic_fallback",
            "featureSchemaVersion": "none",
            "featureNames": [],
            "exampleCount": 0,
            "copedentNeutral": True,
            "policyMode": "deterministic_fallback",
            "rankerEnabled": False,
            "privateBeta": False,
            "comparisonMode": False,
            "inputScope": "normalized_score_events",
            "scoreImageRecognitionIncluded": False,
            "recognitionMode": "separate_review_required",
            "fallbackReason": getattr(policy, "failure_reason", None),
        }
    metadata: dict[str, object] = {
        "modelId": policy.model_id,
        "status": "private_beta",
        "sourceModelStatus": policy.status,
        "featureSchemaVersion": policy.feature_schema_version,
        "featureNames": list(policy.feature_names),
        "featureCount": len(policy.feature_names),
        "exampleCount": policy.example_count,
        "copedentNeutral": policy.copedent_neutral,
        "policyMode": "learned_with_deterministic_comparison",
        "rankerEnabled": True,
        "privateBeta": True,
        "comparisonMode": True,
        "supportedStyleFamilies": list(CANONICAL_STYLE_FAMILIES),
        "inputScope": "normalized_score_events",
        "scoreImageRecognitionIncluded": False,
        "recognitionMode": "separate_review_required",
    }
    if comparison_changed_events is not None:
        metadata["comparisonChangedEvents"] = comparison_changed_events
    if comparison_event_count is not None:
        metadata["comparisonEventCount"] = comparison_event_count
    return metadata


def _position_signature(event: Mapping[str, Any]) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            int(note["string"]),
            int(note["fret"]),
            tuple(sorted(str(change) for change in note.get("changes") or ())),
        )
        for note in event.get("notes") or ()
    )


def _changed_event_count(
    learned: Mapping[str, Any],
    deterministic: Mapping[str, Any],
) -> tuple[int, int]:
    learned_events = list(learned.get("events") or ())
    deterministic_events = list(deterministic.get("events") or ())
    total = max(len(learned_events), len(deterministic_events))
    changed = 0
    for index in range(total):
        learned_signature = (
            _position_signature(learned_events[index])
            if index < len(learned_events)
            else ()
        )
        deterministic_signature = (
            _position_signature(deterministic_events[index])
            if index < len(deterministic_events)
            else ()
        )
        changed += learned_signature != deterministic_signature
    return changed, total


def arrange_melody_routes_with_private_beta(
    raw_events: Sequence[Any],
    *,
    policy: RuntimeRankerPolicy | None,
    key: str,
    contour_mode: str = "closest_playable",
    texture: str = "both",
    route_id_prefix: str,
    title: str,
    event_start: int = 0,
    event_end: int | None = None,
    meter: str = "4/4",
    pickup_beats: float = 0.0,
    sections: Sequence[Mapping[str, Any]] | None = None,
    source_copedent_id: str | None = None,
    target_copedent_id: str | None = None,
    target_copedent: Mapping[str, Any] | None = None,
    style_family: str = "auto",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, object]]:
    """Return deterministic routes plus a validated learned comparison route."""

    arranger_kwargs = {
        "key": key,
        "contour_mode": contour_mode,
        "texture": texture,
        "route_id_prefix": route_id_prefix,
        "title": title,
        "event_start": event_start,
        "event_end": event_end,
        "meter": meter,
        "pickup_beats": pickup_beats,
        "sections": sections,
        "source_copedent_id": source_copedent_id,
        "target_copedent_id": target_copedent_id,
        "target_copedent": target_copedent,
        "style_family": style_family,
    }
    if not private_beta_enabled(policy) or texture not in {"both", "mixed_arrangement"}:
        routes, resolved = arrange_melody_routes(raw_events, **arranger_kwargs)
        return routes, resolved, private_beta_model_metadata(policy)

    try:
        contour = (
            contour_mode
            if contour_mode in SUPPORTED_CONTOURS
            else "closest_playable"
        )
        selected_texture = texture if texture in SUPPORTED_TEXTURES else "both"
        selected_style = normalize_style_family(style_family)
        target_profile = resolve_target_profile(target_copedent_id, target_copedent)
        source_profile = (
            get_e9_copedent_profile(source_copedent_id)
            if source_copedent_id
            else target_profile
        )
        all_inputs = parse_melody_inputs(
            raw_events,
            key,
            source_profile=source_profile,
            target_profile=target_profile,
        )
        all_pitches = resolve_contour(all_inputs, contour, profile=target_profile)
        inputs = all_inputs[event_start:event_end]
        resolved_pitches = all_pitches[event_start:event_end]
        phrase_starts, phrase_ends = _phrase_boundaries(inputs, sections)

        single_cache: dict[tuple[object, ...], list[Any]] = {}
        single_groups: list[list[Any]] = []
        for item, pitch in zip(inputs, resolved_pitches):
            literal_key = None
            if item.literal is not None:
                literal_key = (
                    item.literal.string,
                    item.literal.fret,
                    tuple(item.literal.changes),
                )
            cache_key = (item.note, item.degree, pitch, literal_key)
            candidates = single_cache.get(cache_key)
            if candidates is None:
                candidates = single_note_candidates(
                    item,
                    pitch,
                    profile=target_profile,
                )
                single_cache[cache_key] = candidates
            single_groups.append(candidates)
        single_path = choose_path(single_groups, inputs=inputs)
        if not single_path:
            raise ValueError(
                "The melody does not have a mechanically valid standard-E9 path."
            )

        route_specs: list[tuple[str, str, str]] = [
            ("single-note", "single_note", "Faithful melody")
        ]
        if selected_texture in {"both", "mixed_arrangement"}:
            route_specs.append(
                ("mixed-arrangement", "mixed_arrangement", "Recommended arrangement")
            )
        if selected_texture == "automatic_harmony":
            route_specs.append(
                (
                    "recommended-harmony",
                    "automatic_harmony",
                    "Recommended harmony",
                )
            )
        if selected_texture in {"both", "thirds"}:
            route_specs.append(("thirds", "thirds", "Diatonic thirds"))
        if selected_texture in {"both", "sixths"}:
            route_specs.append(("sixths", "sixths", "Diatonic sixths"))
        if selected_texture in {"both", "chord_melody"}:
            route_specs.append(
                ("chord-melody", "chord_melody", "Chord melody")
            )

        routes: list[dict[str, Any]] = [
            build_route(
                route_id=f"{route_id_prefix}-single-note",
                label=route_specs[0][2],
                harmony_type="single_note",
                recommendation=(
                    "Start here to hear and learn the melody contour cleanly."
                ),
                inputs=inputs,
                resolved_pitches=resolved_pitches,
                path=single_path,
                candidate_groups=single_groups,
                key=key,
                title=f"{title} — Single-note melody",
                recommended=False,
                meter=meter,
                pickup_beats=pickup_beats,
                phrase_starts=phrase_starts,
                phrase_ends=phrase_ends,
                target_profile=target_profile,
                source_profile=source_profile,
                style_family=selected_style,
            )
        ]

        harmony_groups: dict[str, list[list[Any]]] = {}
        generic_catalogs: dict[str, list[Any]] = {}

        def groups_for(harmony_type: str) -> list[list[Any]]:
            groups = harmony_groups.get(harmony_type)
            if groups is None:
                groups = harmony_candidate_groups(
                    inputs,
                    resolved_pitches,
                    key,
                    harmony_type,
                    profile=target_profile,
                    generic_catalogs=generic_catalogs,
                )
                harmony_groups[harmony_type] = groups
            return groups

        changed: int | None = None
        total: int | None = None
        for suffix, harmony_type, label in route_specs[1:]:
            if harmony_type == "chord_melody" and not any(
                _active_chords(inputs)
            ):
                continue
            if harmony_type == "mixed_arrangement":
                candidate_groups = mixed_candidate_groups(
                    inputs,
                    resolved_pitches,
                    key,
                    profile=target_profile,
                    single_groups=single_groups,
                    dyad_groups=groups_for("automatic_harmony"),
                    triad_groups=groups_for("chord_melody"),
                )
                deterministic_path = choose_mixed_path(
                    candidate_groups,
                    inputs=inputs,
                    key=key,
                    meter=meter,
                    pickup_beats=pickup_beats,
                    phrase_starts=phrase_starts,
                    phrase_ends=phrase_ends,
                    style_family=selected_style,
                    profile=target_profile,
                )
                learned_path = choose_mixed_path(
                    candidate_groups,
                    inputs=inputs,
                    key=key,
                    meter=meter,
                    pickup_beats=pickup_beats,
                    phrase_starts=phrase_starts,
                    phrase_ends=phrase_ends,
                    style_family=selected_style,
                    profile=target_profile,
                    shadow_ranker_policy=policy,
                )
                if not deterministic_path:
                    continue
                if (
                    target_profile.id == DEFAULT_COPEDENT_ID
                    and selected_style == "auto"
                    and all(
                        len(candidate.notes) == 1
                        for candidate in deterministic_path
                    )
                ):
                    continue
                deterministic = build_route(
                    route_id=f"{route_id_prefix}-{suffix}",
                    label=label,
                    harmony_type=harmony_type,
                    recommendation=_recommendation_for(harmony_type),
                    inputs=inputs,
                    resolved_pitches=resolved_pitches,
                    path=deterministic_path,
                    candidate_groups=candidate_groups,
                    key=key,
                    title=f"{title} — {label}",
                    recommended=True,
                    meter=meter,
                    pickup_beats=pickup_beats,
                    phrase_starts=phrase_starts,
                    phrase_ends=phrase_ends,
                    target_profile=target_profile,
                    source_profile=source_profile,
                    style_family=selected_style,
                )
                if not learned_path:
                    routes.append(deterministic)
                    continue
                learned = build_route(
                    route_id=f"{route_id_prefix}-learned-beta",
                    label="Learned beta recommendation",
                    harmony_type="mixed_arrangement",
                    recommendation=(
                        "Private learned ranking chose this path after the frozen "
                        "pitch, register, harmony, and mechanical gates passed."
                    ),
                    inputs=inputs,
                    resolved_pitches=resolved_pitches,
                    path=learned_path,
                    candidate_groups=candidate_groups,
                    key=key,
                    title=f"{title} — Learned beta recommendation",
                    recommended=True,
                    meter=meter,
                    pickup_beats=pickup_beats,
                    phrase_starts=phrase_starts,
                    phrase_ends=phrase_ends,
                    target_profile=target_profile,
                    source_profile=source_profile,
                    style_family=selected_style,
                )
                learned["engineMode"] = "private_learned_beta"
                learned["modelId"] = policy.model_id
                deterministic["label"] = "Deterministic comparison"
                deterministic["harmonyType"] = "deterministic_comparison"
                deterministic["recommended"] = False
                deterministic["engineMode"] = "deterministic_comparison"
                deterministic["comparisonModelId"] = policy.model_id
                changed, total = _changed_event_count(learned, deterministic)
                learned["comparisonRouteId"] = deterministic["id"]
                learned["comparisonChangedEvents"] = changed
                learned["comparisonEventCount"] = total
                deterministic["comparisonRouteId"] = learned["id"]
                deterministic["comparisonChangedEvents"] = changed
                deterministic["comparisonEventCount"] = total
                routes.extend((learned, deterministic))
                continue

            candidate_groups = groups_for(harmony_type)
            path = (
                choose_path(candidate_groups, inputs=inputs)
                if candidate_groups and all(candidate_groups)
                else []
            )
            if not path:
                continue
            routes.append(
                build_route(
                    route_id=f"{route_id_prefix}-{suffix}",
                    label=label,
                    harmony_type=harmony_type,
                    recommendation=_recommendation_for(harmony_type),
                    inputs=inputs,
                    resolved_pitches=resolved_pitches,
                    path=path,
                    candidate_groups=candidate_groups,
                    key=key,
                    title=f"{title} — {label}",
                    recommended=harmony_type
                    in {"mixed_arrangement", "automatic_harmony"},
                    meter=meter,
                    pickup_beats=pickup_beats,
                    phrase_starts=phrase_starts,
                    phrase_ends=phrase_ends,
                    target_profile=target_profile,
                    source_profile=source_profile,
                    style_family=selected_style,
                )
            )

        if len(routes) > 1 and not any(
            route["recommended"] for route in routes
        ):
            fallback = next(
                (
                    route
                    for route in routes
                    if route["harmonyType"]
                    not in {"single_note", "vocal_steel"}
                ),
                None,
            )
            if fallback is not None:
                fallback["recommended"] = True
                fallback["recommendation"] = (
                    "Recommended validated harmony route for this phrase."
                )

        resolved = [
            {
                "inputToken": item.token,
                "resolvedNote": item.note,
                "scaleDegree": str(item.degree),
                "pitch": scientific_pitch_for_value(pitch),
                "pitchValue": pitch,
                "direction": item.direction,
                "octaveShift": item.octave_shift,
                "literal": item.literal is not None,
                "durationBeats": item.duration_beats,
                "measure": item.measure,
                "beat": item.beat,
                "origin": item.origin,
                "tie": item.tie,
                "lyric": item.lyric,
                "chord": item.chord,
                "articulation": item.articulation,
                **(
                    {"sourceAction": item.source_action}
                    if item.source_action
                    else {}
                ),
            }
            for item, pitch in zip(inputs, resolved_pitches)
        ]
        return routes, resolved, private_beta_model_metadata(
            policy,
            comparison_changed_events=changed,
            comparison_event_count=total,
        )
    except (KeyError, TypeError, ValueError):
        # A private beta must never make a valid deterministic arrangement fail.
        routes, resolved = arrange_melody_routes(raw_events, **arranger_kwargs)
        return routes, resolved, private_beta_model_metadata(policy)


def sanitized_runtime_artifact(training_payload: Mapping[str, Any]) -> bytes:
    """Create the strict non-source runtime payload from a reviewed model."""

    fields = (
        "schemaVersion",
        "modelId",
        "status",
        "featureSchemaVersion",
        "featureNames",
        "weightsByStyle",
        "exampleCount",
        "copedentNeutral",
        "privacy",
    )
    import json

    return (
        json.dumps(
            {field: training_payload.get(field) for field in fields},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
