from __future__ import annotations

import hashlib
import json

import pocketsteel.amazing_tablature_runtime as runtime
from pocketsteel.amazing_tablature_model import (
    CANONICAL_FEATURE_NAMES,
    CANONICAL_FEATURE_SCHEMA_VERSION,
    CANONICAL_STYLE_FAMILIES,
    MODEL_SCHEMA_VERSION,
    RuntimeRankerPolicy,
)
from pocketsteel.amazing_tablature_runtime import (
    ENABLE_PRIVATE_BETA_ENV,
    PRIVATE_MODEL_ID_ENV,
    PRIVATE_MODEL_PATH_ENV,
    PRIVATE_MODEL_SHA256_ENV,
    configured_private_ranker_policy,
    private_beta_model_metadata,
    sanitized_runtime_artifact,
)
from pocketsteel.e9_copedents import EMMONS_E9
from pocketsteel.melody_assistant import melody_exercise_response
from pocketsteel.melody_arranger import (
    _phrase_boundaries,
    _runtime_learned_penalty,
    choose_mixed_path,
    harmony_candidate_groups,
    mixed_candidate_groups,
    parse_melody_inputs,
    resolve_contour,
    single_note_candidates,
)


def _artifact_payload() -> dict[str, object]:
    return {
        "schemaVersion": MODEL_SCHEMA_VERSION,
        "modelId": "at-test-private-beta",
        "status": "challenger",
        "featureSchemaVersion": CANONICAL_FEATURE_SCHEMA_VERSION,
        "featureNames": list(CANONICAL_FEATURE_NAMES),
        "weightsByStyle": {
            style: {feature: 0.0 for feature in CANONICAL_FEATURE_NAMES}
            for style in CANONICAL_STYLE_FAMILIES
        },
        "exampleCount": 702,
        "copedentNeutral": True,
        "privacy": {
            "containsSourceContent": False,
            "containsProfileSnapshots": False,
        },
    }


def _policy() -> RuntimeRankerPolicy:
    payload = _artifact_payload()
    return RuntimeRankerPolicy(
        model_id=str(payload["modelId"]),
        status=str(payload["status"]),
        feature_schema_version=str(payload["featureSchemaVersion"]),
        feature_names=tuple(payload["featureNames"]),
        weights_by_style=dict(payload["weightsByStyle"]),
        example_count=int(payload["exampleCount"]),
        copedent_neutral=True,
        shadow_eligible=True,
    )


def _weighted_policy() -> RuntimeRankerPolicy:
    policy = _policy()
    weights = {
        feature: (index - 10) / 7.0
        for index, feature in enumerate(CANONICAL_FEATURE_NAMES)
    }
    return RuntimeRankerPolicy(
        model_id=policy.model_id,
        status=policy.status,
        feature_schema_version=policy.feature_schema_version,
        feature_names=policy.feature_names,
        weights_by_style={
            style: dict(weights)
            for style in CANONICAL_STYLE_FAMILIES
        },
        example_count=policy.example_count,
        copedent_neutral=policy.copedent_neutral,
        shadow_eligible=policy.shadow_eligible,
    )


def test_private_beta_configuration_defaults_off_and_fails_closed(tmp_path) -> None:
    assert configured_private_ranker_policy({}).failure_reason == "private_beta_disabled"

    artifact = sanitized_runtime_artifact(_artifact_payload())
    path = tmp_path / "runtime-model.json"
    path.write_bytes(artifact)
    policy = configured_private_ranker_policy(
        {
            ENABLE_PRIVATE_BETA_ENV: "true",
            PRIVATE_MODEL_PATH_ENV: str(path),
            PRIVATE_MODEL_ID_ENV: "at-test-private-beta",
            PRIVATE_MODEL_SHA256_ENV: "0" * 64,
        }
    )

    assert policy.shadow_eligible is False
    assert policy.model_id == "deterministic-fallback-v1"
    assert policy.failure_reason == "artifact_digest_mismatch"


def test_exact_sanitized_artifact_loads_without_source_fields(tmp_path) -> None:
    training_payload = {
        **_artifact_payload(),
        "sourceCopedentProfiles": {"must": "not escape"},
        "evidenceCounts": {"private": 12},
    }
    artifact = sanitized_runtime_artifact(training_payload)
    decoded = json.loads(artifact)
    assert set(decoded) == {
        "schemaVersion",
        "modelId",
        "status",
        "featureSchemaVersion",
        "featureNames",
        "weightsByStyle",
        "exampleCount",
        "copedentNeutral",
        "privacy",
    }
    path = tmp_path / "runtime-model.json"
    path.write_bytes(artifact)
    policy = configured_private_ranker_policy(
        {
            ENABLE_PRIVATE_BETA_ENV: "1",
            PRIVATE_MODEL_PATH_ENV: str(path),
            PRIVATE_MODEL_ID_ENV: "at-test-private-beta",
            PRIVATE_MODEL_SHA256_ENV: hashlib.sha256(artifact).hexdigest(),
        }
    )

    assert policy.shadow_eligible is True
    assert policy.model_id == "at-test-private-beta"
    assert len(policy.feature_names) == 21


def test_private_beta_returns_learned_and_deterministic_routes() -> None:
    result = melody_exercise_response(
        "Build a melody exercise",
        {
            "key": "G",
            "melody": ["1", "2", "3", "5", "3", "2", "1"],
            "styleFamily": "harmonized",
        },
        ranker_policy=_policy(),
    )
    assert result is not None
    exercise = result["melody_exercise"]
    learned = next(
        route for route in exercise["routes"]
        if route.get("engineMode") == "private_learned_beta"
    )
    deterministic = next(
        route for route in exercise["routes"]
        if route.get("engineMode") == "deterministic_comparison"
    )

    assert learned["recommended"] is True
    assert deterministic["recommended"] is False
    assert len(learned["events"]) == len(deterministic["events"]) == 7
    assert learned["tabExample"]["validation"]["ok"] is True
    assert deterministic["tabExample"]["validation"]["ok"] is True
    metadata = exercise["decisionRules"]["modelMetadata"]
    assert metadata == private_beta_model_metadata(
        _policy(),
        comparison_changed_events=learned["comparisonChangedEvents"],
        comparison_event_count=7,
    )
    assert metadata["rankerEnabled"] is True
    assert metadata["privateBeta"] is True
    assert metadata["featureCount"] == 21
    assert "weightsByStyle" not in metadata


def test_disabled_private_beta_keeps_deterministic_route_contract() -> None:
    result = melody_exercise_response(
        "Build a melody exercise",
        {"key": "G", "melody": ["1", "2", "3"], "styleFamily": "harmonized"},
    )
    assert result is not None
    exercise = result["melody_exercise"]
    assert not any(route.get("engineMode") for route in exercise["routes"])
    assert exercise["decisionRules"]["modelMetadata"]["rankerEnabled"] is False
    assert exercise["decisionRules"]["modelMetadata"]["privateBeta"] is False


def test_private_beta_builds_each_candidate_catalog_once(monkeypatch) -> None:
    original_harmony_groups = runtime.harmony_candidate_groups
    harmony_calls: list[str] = []

    def counted_harmony_groups(*args, **kwargs):
        harmony_calls.append(str(args[3]))
        return original_harmony_groups(*args, **kwargs)

    def unexpected_second_arranger_pass(*args, **kwargs):
        raise AssertionError(
            "active private beta must not rebuild the deterministic arranger"
        )

    monkeypatch.setattr(
        runtime,
        "harmony_candidate_groups",
        counted_harmony_groups,
    )
    monkeypatch.setattr(
        runtime,
        "arrange_melody_routes",
        unexpected_second_arranger_pass,
    )

    result = melody_exercise_response(
        "Build a melody exercise",
        {
            "key": "G",
            "melody": ["1", "2", "3", "5", "3", "2", "1"],
            "styleFamily": "harmonized",
        },
        ranker_policy=_policy(),
    )

    assert result is not None
    assert harmony_calls.count("automatic_harmony") == 1
    assert harmony_calls.count("chord_melody") == 1
    assert harmony_calls.count("thirds") == 1
    assert harmony_calls.count("sixths") == 1


def test_fast_private_path_matches_frozen_feature_scorer_and_search() -> None:
    inputs = parse_melody_inputs(
        ["1", "2", "3", "5"],
        "G",
        source_profile=EMMONS_E9,
        target_profile=EMMONS_E9,
    )
    pitches = resolve_contour(inputs, "closest_playable", profile=EMMONS_E9)
    single_groups = [
        single_note_candidates(item, pitch, profile=EMMONS_E9)
        for item, pitch in zip(inputs, pitches)
    ]
    generic_catalogs: dict[str, list] = {}
    dyad_groups = harmony_candidate_groups(
        inputs,
        pitches,
        "G",
        "automatic_harmony",
        profile=EMMONS_E9,
        generic_catalogs=generic_catalogs,
    )
    triad_groups = harmony_candidate_groups(
        inputs,
        pitches,
        "G",
        "chord_melody",
        profile=EMMONS_E9,
        generic_catalogs=generic_catalogs,
    )
    groups = mixed_candidate_groups(
        inputs,
        pitches,
        "G",
        profile=EMMONS_E9,
        single_groups=single_groups,
        dyad_groups=dyad_groups,
        triad_groups=triad_groups,
    )
    policy = _weighted_policy()
    weights = policy.weights_by_style["harmonized"]
    for previous in groups[0][:2]:
        for current in groups[1][:2]:
            for following in groups[2][:2]:
                fast = runtime._fast_ranker_penalty(
                    runtime._ranker_candidate_state(
                        current,
                        profile=EMMONS_E9,
                    ),
                    runtime._ranker_pair_state(
                        previous,
                        current,
                        runtime._ranker_candidate_state(
                            previous,
                            profile=EMMONS_E9,
                        ),
                        runtime._ranker_candidate_state(
                            current,
                            profile=EMMONS_E9,
                        ),
                        profile=EMMONS_E9,
                    ),
                    runtime._ranker_pair_state(
                        current,
                        following,
                        runtime._ranker_candidate_state(
                            current,
                            profile=EMMONS_E9,
                        ),
                        runtime._ranker_candidate_state(
                            following,
                            profile=EMMONS_E9,
                        ),
                        profile=EMMONS_E9,
                    ),
                    role="sustained_note",
                    weights=weights,
                )
                frozen = _runtime_learned_penalty(
                    previous,
                    current,
                    following,
                    role="sustained_note",
                    style_family="harmonized",
                    profile=EMMONS_E9,
                    shadow_ranker_policy=policy,
                )
                assert fast == frozen

    phrase_starts, phrase_ends = _phrase_boundaries(inputs, None)
    frozen_path = choose_mixed_path(
        groups,
        inputs=inputs,
        key="G",
        meter="4/4",
        pickup_beats=0.0,
        phrase_starts=phrase_starts,
        phrase_ends=phrase_ends,
        style_family="harmonized",
        profile=EMMONS_E9,
        shadow_ranker_policy=policy,
    )
    fast_path = runtime._choose_private_beta_path(
        groups,
        inputs=inputs,
        key="G",
        meter="4/4",
        pickup_beats=0.0,
        phrase_starts=phrase_starts,
        phrase_ends=phrase_ends,
        style_family="harmonized",
        profile=EMMONS_E9,
        policy=policy,
    )
    assert fast_path == frozen_path
