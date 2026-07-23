"""Sanitized Amazing Tablature runtime policy.

The superseded 51-image beta is deliberately not active. Until an exact
complete-discovery challenger passes the fixed held-out gates and receives
explicit promotion approval, Melody Studio uses its deterministic arranger
without a learned ranking penalty. Private annotations, source actions,
profile snapshots, and source content must never be added here.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

MODEL_ID: Final = "deterministic-fallback-v1"
MODEL_STATUS: Final = "deterministic_fallback"
MODEL_SCHEMA_VERSION: Final = "amazing-tablature-training-v1"
FEATURE_SCHEMA_VERSION: Final = "none"
EXAMPLE_COUNT: Final = 0
COPEDENT_NEUTRAL: Final = True
POLICY_MODE: Final = "deterministic_fallback"
RANKER_ENABLED: Final = False
INPUT_SCOPE: Final = "normalized_score_events"
SCORE_IMAGE_RECOGNITION_INCLUDED: Final = False
RETIRED_MODEL_ID: Final = "at-44c59f08724d501e"
FEATURE_NAMES: Final = ()
WEIGHTS_BY_STYLE: Final = {}
CANONICAL_FEATURE_SCHEMA_VERSION: Final = (
    "melody-ranker-features-v3-phrase-sequence"
)
CANONICAL_FEATURE_NAMES: Final = (
    "texture_1",
    "texture_2",
    "texture_3",
    "bar_travel",
    "control_changes",
    "pocket_changes",
    "voice_leading",
    "sustained_voices",
    "repicked_voices",
    "disconnected_bar_travel",
    "controlled_move",
    "incoming_string_distance",
    "outgoing_bar_travel",
    "outgoing_control_changes",
    "outgoing_string_distance",
    "outgoing_sustain_continuity",
    "fret_direction_reversal",
    "fret_direction_continuation",
    "string_direction_reversal",
    "string_direction_continuation",
    "cadence_arrival",
)
CANONICAL_STYLE_FAMILIES: Final = (
    "chord_melody",
    "harmonized",
    "lever_driven",
    "single_note_run",
)
_SANITIZED_ARTIFACT_FIELDS: Final = {
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
_SANITIZED_PRIVACY_FIELDS: Final = {
    "containsSourceContent",
    "containsProfileSnapshots",
}
_LOADABLE_MODEL_STATES: Final = {
    "challenger",
    "approved_beta",
    "approved_stable",
}


@dataclass(frozen=True)
class RuntimeRankerPolicy:
    """Validated shadow policy or deterministic fail-closed fallback."""

    model_id: str
    status: str
    feature_schema_version: str
    feature_names: tuple[str, ...]
    weights_by_style: dict[str, dict[str, float]]
    example_count: int
    copedent_neutral: bool
    shadow_eligible: bool
    ranker_enabled: bool = False
    failure_reason: str | None = None


def deterministic_fallback_policy(
    reason: str | None = None,
) -> RuntimeRankerPolicy:
    """Return the only policy permitted after an artifact validation failure."""

    return RuntimeRankerPolicy(
        model_id=MODEL_ID,
        status=MODEL_STATUS,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        feature_names=(),
        weights_by_style={},
        example_count=0,
        copedent_neutral=True,
        shadow_eligible=False,
        ranker_enabled=False,
        failure_reason=reason,
    )


def load_sanitized_ranker_artifact(
    artifact_bytes: bytes,
    *,
    expected_model_id: str,
    expected_sha256: str,
) -> RuntimeRankerPolicy:
    """Validate an exact sanitized model artifact for shadow-only scoring.

    The loader deliberately accepts bytes rather than a filesystem path so
    callers must resolve the exact artifact and expected digest outside the
    runtime policy boundary. Every validation failure returns the deterministic
    fallback; this function never enables live ranking.
    """

    try:
        actual_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
        if not hmac.compare_digest(actual_sha256, str(expected_sha256).lower()):
            return deterministic_fallback_policy("artifact_digest_mismatch")
        payload = json.loads(artifact_bytes.decode("utf-8"))
        if not isinstance(payload, Mapping):
            return deterministic_fallback_policy("artifact_not_object")
        if set(payload) != _SANITIZED_ARTIFACT_FIELDS:
            return deterministic_fallback_policy("artifact_field_mismatch")
        if payload.get("schemaVersion") != MODEL_SCHEMA_VERSION:
            return deterministic_fallback_policy("model_schema_mismatch")
        if payload.get("modelId") != expected_model_id:
            return deterministic_fallback_policy("model_id_mismatch")
        if payload.get("status") not in _LOADABLE_MODEL_STATES:
            return deterministic_fallback_policy("model_status_not_loadable")
        if (
            payload.get("featureSchemaVersion")
            != CANONICAL_FEATURE_SCHEMA_VERSION
        ):
            return deterministic_fallback_policy("feature_schema_mismatch")
        feature_names = payload.get("featureNames")
        if (
            not isinstance(feature_names, list)
            or tuple(feature_names) != CANONICAL_FEATURE_NAMES
        ):
            return deterministic_fallback_policy("feature_names_mismatch")
        if payload.get("copedentNeutral") is not True:
            return deterministic_fallback_policy("artifact_not_copedent_neutral")
        example_count = payload.get("exampleCount")
        if (
            isinstance(example_count, bool)
            or not isinstance(example_count, int)
            or example_count <= 0
        ):
            return deterministic_fallback_policy("invalid_example_count")
        privacy = payload.get("privacy")
        if (
            not isinstance(privacy, Mapping)
            or set(privacy) != _SANITIZED_PRIVACY_FIELDS
            or privacy.get("containsSourceContent") is not False
            or privacy.get("containsProfileSnapshots") is not False
        ):
            return deterministic_fallback_policy("privacy_contract_failed")
        raw_weights = payload.get("weightsByStyle")
        if (
            not isinstance(raw_weights, Mapping)
            or set(raw_weights) != set(CANONICAL_STYLE_FAMILIES)
        ):
            return deterministic_fallback_policy("style_family_mismatch")
        weights_by_style: dict[str, dict[str, float]] = {}
        for style in CANONICAL_STYLE_FAMILIES:
            row = raw_weights.get(style)
            if (
                not isinstance(row, Mapping)
                or set(row) != set(CANONICAL_FEATURE_NAMES)
            ):
                return deterministic_fallback_policy("weight_feature_mismatch")
            clean_row: dict[str, float] = {}
            for name in CANONICAL_FEATURE_NAMES:
                value = row.get(name)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                ):
                    return deterministic_fallback_policy("non_finite_weight")
                clean_row[name] = float(value)
            weights_by_style[style] = clean_row
        return RuntimeRankerPolicy(
            model_id=str(payload["modelId"]),
            status=str(payload["status"]),
            feature_schema_version=str(payload["featureSchemaVersion"]),
            feature_names=tuple(str(name) for name in feature_names),
            weights_by_style=weights_by_style,
            example_count=int(example_count),
            copedent_neutral=True,
            shadow_eligible=True,
            ranker_enabled=False,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        OverflowError,
        TypeError,
        ValueError,
    ):
        return deterministic_fallback_policy("artifact_parse_failed")


def model_metadata_payload() -> dict[str, object]:
    """Return public audit metadata without exposing mutable model internals."""

    return {
        "modelId": MODEL_ID,
        "status": MODEL_STATUS,
        "schemaVersion": MODEL_SCHEMA_VERSION,
        "featureSchemaVersion": FEATURE_SCHEMA_VERSION,
        "featureNames": list(FEATURE_NAMES),
        "exampleCount": EXAMPLE_COUNT,
        "copedentNeutral": COPEDENT_NEUTRAL,
        "policyMode": POLICY_MODE,
        "rankerEnabled": RANKER_ENABLED,
        "inputScope": INPUT_SCOPE,
        "scoreImageRecognitionIncluded": SCORE_IMAGE_RECOGNITION_INCLUDED,
        "recognitionMode": "separate_review_required",
        "lineage": {
            "retiredModelId": RETIRED_MODEL_ID,
            "retirementReason": "superseded_source_batch",
        },
    }
