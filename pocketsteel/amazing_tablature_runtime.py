"""Fail-closed private runtime adapter for an Amazing Tablature challenger.

The frozen arranger and ranker own feature calculation and hard mechanical
validation.  This module only loads a hash-pinned sanitized policy, asks the
frozen engine for a learned mixed path, and keeps the deterministic path beside
it for an honest private-beta comparison.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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
    E9CopedentProfile,
    get_e9_copedent_profile,
    scientific_pitch_for_value,
)
from pocketsteel.melody_arranger import (
    _active_chords,
    _add_cost,
    _arrangement_roles,
    _learned_cost_component,
    _learned_style_for_role,
    _mixed_start_cost,
    _mixed_transition_cost,
    _phrase_boundaries,
    _ranker_candidate_is_hard_valid,
    _ranker_sustained_strings,
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
from pocketsteel.melody_models import (
    SUPPORTED_CONTOURS,
    SUPPORTED_TEXTURES,
    MelodyInput,
    PositionCandidate,
)
from pocketsteel.melody_ranker_adapter import actions_for_position


ENABLE_PRIVATE_BETA_ENV = "STEEL_RAG_ENABLE_AMAZING_TABLATURE_BETA"
PRIVATE_MODEL_PATH_ENV = "STEEL_RAG_AMAZING_TABLATURE_MODEL_PATH"
PRIVATE_MODEL_ID_ENV = "STEEL_RAG_AMAZING_TABLATURE_MODEL_ID"
PRIVATE_MODEL_SHA256_ENV = "STEEL_RAG_AMAZING_TABLATURE_MODEL_SHA256"


@dataclass(frozen=True)
class _RankerCandidateState:
    texture_size: int
    fret: int
    top_string: int
    pitches: tuple[int, ...]
    strings: frozenset[int]
    controls: frozenset[str]


@dataclass(frozen=True)
class _RankerPairState:
    bar_travel: int
    control_changes: int
    pocket_changes: int
    voice_leading: int
    sustained_voices: int
    repicked_voices: int
    incoming_string_distance: int
    outgoing_sustain_continuity: int
    fret_direction: int
    string_direction: int


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


def _direction(value: int) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def _ranker_candidate_state(
    candidate: PositionCandidate,
    *,
    profile: E9CopedentProfile,
) -> _RankerCandidateState:
    actions = actions_for_position(candidate, profile)
    top = max(actions, key=lambda action: int(action["soundingPitchValue"]))
    return _RankerCandidateState(
        texture_size=len(actions),
        fret=int(top["fret"]),
        top_string=int(top["string"]),
        pitches=tuple(int(action["soundingPitchValue"]) for action in actions),
        strings=frozenset(int(action["string"]) for action in actions),
        controls=frozenset(
            str(control)
            for action in actions
            for control in action.get("controls") or ()
        ),
    )


def _ranker_pair_state(
    previous: PositionCandidate,
    current: PositionCandidate,
    previous_state: _RankerCandidateState,
    current_state: _RankerCandidateState,
    *,
    profile: E9CopedentProfile,
) -> _RankerPairState:
    sustained = frozenset(
        _ranker_sustained_strings(previous, current, profile=profile)
    )
    attacked = current_state.strings - sustained
    common = previous_state.strings & current_state.strings
    bar_travel = abs(current_state.fret - previous_state.fret)
    control_changes = len(current_state.controls ^ previous_state.controls)
    return _RankerPairState(
        bar_travel=bar_travel,
        control_changes=control_changes,
        pocket_changes=int(current_state.fret != previous_state.fret),
        voice_leading=sum(
            min(abs(pitch - previous_pitch) for previous_pitch in previous_state.pitches)
            for pitch in current_state.pitches
        ),
        sustained_voices=len(current_state.strings & sustained),
        repicked_voices=len(common & attacked),
        incoming_string_distance=abs(
            current_state.top_string - previous_state.top_string
        ),
        outgoing_sustain_continuity=len(previous_state.strings & sustained),
        fret_direction=_direction(current_state.fret - previous_state.fret),
        string_direction=_direction(
            current_state.top_string - previous_state.top_string
        ),
    )


def _fast_ranker_penalty(
    current: _RankerCandidateState,
    incoming: _RankerPairState,
    outgoing: _RankerPairState | None,
    *,
    role: str,
    weights: Mapping[str, float],
) -> int:
    """Score the canonical 21 features without rebuilding action dictionaries."""

    score = 0.0
    score += float(weights.get(f"texture_{max(1, min(3, current.texture_size))}", 0.0))
    score += incoming.bar_travel * float(weights.get("bar_travel", 0.0))
    score += incoming.control_changes * float(
        weights.get("control_changes", 0.0)
    )
    score += incoming.pocket_changes * float(
        weights.get("pocket_changes", 0.0)
    )
    score += incoming.voice_leading * float(
        weights.get("voice_leading", 0.0)
    )
    score += incoming.sustained_voices * float(
        weights.get("sustained_voices", 0.0)
    )
    score += incoming.repicked_voices * float(
        weights.get("repicked_voices", 0.0)
    )
    if incoming.repicked_voices <= 0:
        score += incoming.bar_travel * float(
            weights.get("disconnected_bar_travel", 0.0)
        )
    if incoming.control_changes > 0 and incoming.pocket_changes > 0:
        score += float(weights.get("controlled_move", 0.0))
    score += incoming.incoming_string_distance * float(
        weights.get("incoming_string_distance", 0.0)
    )
    if outgoing is not None:
        score += outgoing.bar_travel * float(
            weights.get("outgoing_bar_travel", 0.0)
        )
        score += outgoing.control_changes * float(
            weights.get("outgoing_control_changes", 0.0)
        )
        score += outgoing.incoming_string_distance * float(
            weights.get("outgoing_string_distance", 0.0)
        )
        score += outgoing.outgoing_sustain_continuity * float(
            weights.get("outgoing_sustain_continuity", 0.0)
        )
        score += int(
            incoming.fret_direction * outgoing.fret_direction < 0
        ) * float(weights.get("fret_direction_reversal", 0.0))
        score += int(
            incoming.fret_direction != 0
            and incoming.fret_direction == outgoing.fret_direction
        ) * float(weights.get("fret_direction_continuation", 0.0))
        score += int(
            incoming.string_direction * outgoing.string_direction < 0
        ) * float(weights.get("string_direction_reversal", 0.0))
        score += int(
            incoming.string_direction != 0
            and incoming.string_direction == outgoing.string_direction
        ) * float(weights.get("string_direction_continuation", 0.0))
    if role in {"cadence", "chord_arrival", "resolution"}:
        score += float(weights.get("cadence_arrival", 0.0))
    return round(score * 1000)


def _choose_private_beta_path(
    candidate_groups: Sequence[Sequence[PositionCandidate]],
    *,
    inputs: Sequence[MelodyInput],
    key: str,
    meter: str,
    pickup_beats: float,
    phrase_starts: set[int],
    phrase_ends: set[int],
    style_family: str,
    profile: E9CopedentProfile,
    policy: RuntimeRankerPolicy,
) -> list[PositionCandidate]:
    """Run the frozen second-order search with cached, parity-tested features."""

    if not candidate_groups or any(not group for group in candidate_groups):
        return []
    active_chords = _active_chords(inputs)
    roles = _arrangement_roles(
        inputs,
        active_chords,
        meter=meter,
        pickup_beats=pickup_beats,
        phrase_starts=phrase_starts or {0},
        phrase_ends=phrase_ends or {len(inputs) - 1},
    )
    selected_style = normalize_style_family(style_family)
    learned_weights = [
        policy.weights_by_style.get(
            _learned_style_for_role(selected_style, role),
            {},
        )
        for role in roles
    ]
    if len(candidate_groups) < 2 or not any(learned_weights[1:]):
        return choose_mixed_path(
            candidate_groups,
            inputs=inputs,
            key=key,
            meter=meter,
            pickup_beats=pickup_beats,
            phrase_starts=phrase_starts,
            phrase_ends=phrase_ends,
            style_family=selected_style,
            profile=profile,
            shadow_ranker_policy=policy,
        )

    groups = [
        [
            candidate
            for candidate in group
            if _ranker_candidate_is_hard_valid(
                candidate,
                inputs[event_index],
                profile=profile,
            )
        ]
        for event_index, group in enumerate(candidate_groups)
    ]
    if any(not group for group in groups):
        return []

    state_cache: dict[int, _RankerCandidateState] = {}
    pair_cache: dict[tuple[int, int], _RankerPairState] = {}

    def candidate_state(candidate: PositionCandidate) -> _RankerCandidateState:
        key_id = id(candidate)
        state = state_cache.get(key_id)
        if state is None:
            state = _ranker_candidate_state(candidate, profile=profile)
            state_cache[key_id] = state
        return state

    def pair_state(
        previous: PositionCandidate,
        current: PositionCandidate,
    ) -> _RankerPairState:
        key_ids = (id(previous), id(current))
        state = pair_cache.get(key_ids)
        if state is None:
            state = _ranker_pair_state(
                previous,
                current,
                candidate_state(previous),
                candidate_state(current),
                profile=profile,
            )
            pair_cache[key_ids] = state
        return state

    home_fret = 3 if key == "G" else 8
    pair_states: list[
        dict[tuple[int, int], tuple[tuple[int, ...], int | None]]
    ] = [{} for _index in groups]
    for previous_index, previous in enumerate(groups[0]):
        start_cost = _mixed_start_cost(
            previous,
            inputs,
            0,
            active_chords,
            roles,
            home_fret=home_fret,
            style_family=selected_style,
        )
        for current_index, current in enumerate(groups[1]):
            transition = _mixed_transition_cost(
                previous,
                current,
                inputs,
                1,
                active_chords,
                roles,
                phrase_starts=phrase_starts or {0},
                home_fret=home_fret,
                key=key,
                style_family=selected_style,
            )
            pair_states[1][(previous_index, current_index)] = (
                _add_cost(start_cost, transition),
                None,
            )

    for event_index in range(2, len(groups)):
        current_layer: dict[
            tuple[int, int], tuple[tuple[int, ...], int | None]
        ] = {}
        for (previous_index, current_index), (
            previous_cost,
            _parent,
        ) in pair_states[event_index - 1].items():
            previous = groups[event_index - 2][previous_index]
            current = groups[event_index - 1][current_index]
            incoming = pair_state(previous, current)
            for following_index, following in enumerate(groups[event_index]):
                outgoing = pair_state(current, following)
                learned_penalty = _fast_ranker_penalty(
                    candidate_state(current),
                    incoming,
                    outgoing,
                    role=roles[event_index - 1],
                    weights=learned_weights[event_index - 1],
                )
                transition = _mixed_transition_cost(
                    current,
                    following,
                    inputs,
                    event_index,
                    active_chords,
                    roles,
                    phrase_starts=phrase_starts or {0},
                    home_fret=home_fret,
                    key=key,
                    style_family=selected_style,
                )
                total = _add_cost(
                    previous_cost,
                    _add_cost(
                        transition,
                        _learned_cost_component(learned_penalty),
                    ),
                )
                key_pair = (current_index, following_index)
                choice = (total, previous_index)
                existing = current_layer.get(key_pair)
                if existing is None or (choice[0], choice[1]) < (
                    existing[0],
                    int(existing[1] or 0),
                ):
                    current_layer[key_pair] = choice
        pair_states[event_index] = current_layer

    final_layer = pair_states[-1]
    ranked_finals: list[tuple[tuple[int, ...], tuple[int, int]]] = []
    for (previous_index, current_index), (cost, _parent) in final_layer.items():
        previous = groups[-2][previous_index]
        current = groups[-1][current_index]
        final_penalty = _fast_ranker_penalty(
            candidate_state(current),
            pair_state(previous, current),
            None,
            role=roles[-1],
            weights=learned_weights[-1],
        )
        ranked_finals.append(
            (
                _add_cost(cost, _learned_cost_component(final_penalty)),
                (previous_index, current_index),
            )
        )
    _final_cost, (previous_index, current_index) = min(
        ranked_finals,
        key=lambda item: (item[0], item[1]),
    )
    indices = [current_index, previous_index]
    for event_index in range(len(groups) - 1, 1, -1):
        parent = pair_states[event_index][
            (previous_index, current_index)
        ][1]
        if parent is None:
            raise ValueError("Learned path state lost its parent candidate.")
        current_index = previous_index
        previous_index = parent
        indices.append(previous_index)
    indices.reverse()
    return [
        groups[event_index][candidate_index]
        for event_index, candidate_index in enumerate(indices)
    ]


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
                learned_path = _choose_private_beta_path(
                    candidate_groups,
                    inputs=inputs,
                    key=key,
                    meter=meter,
                    pickup_beats=pickup_beats,
                    phrase_starts=phrase_starts,
                    phrase_ends=phrase_ends,
                    style_family=selected_style,
                    profile=target_profile,
                    policy=policy,
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
