from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from steel_guitar_rag.amazing_tablature_model import (
    CANONICAL_FEATURE_NAMES,
    CANONICAL_FEATURE_SCHEMA_VERSION,
    CANONICAL_STYLE_FAMILIES,
    MODEL_ID,
    load_sanitized_ranker_artifact,
    model_metadata_payload,
)
from steel_guitar_rag.melody_ranker import FEATURE_NAMES


MODEL_ID_FIXTURE = "at-shadow-fixture"


def _artifact_payload() -> dict[str, object]:
    return {
        "schemaVersion": "amazing-tablature-training-v1",
        "modelId": MODEL_ID_FIXTURE,
        "status": "challenger",
        "featureSchemaVersion": CANONICAL_FEATURE_SCHEMA_VERSION,
        "featureNames": list(FEATURE_NAMES),
        "weightsByStyle": {
            style: {
                name: (style_index + 1) * (feature_index + 1) / 1000
                for feature_index, name in enumerate(FEATURE_NAMES)
            }
            for style_index, style in enumerate(CANONICAL_STYLE_FAMILIES)
        },
        "exampleCount": 702,
        "copedentNeutral": True,
        "privacy": {
            "containsSourceContent": False,
            "containsProfileSnapshots": False,
        },
    }


def _artifact_bytes(payload: dict[str, object] | None = None) -> bytes:
    return (
        json.dumps(
            payload or _artifact_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _load(payload: dict[str, object] | None = None):
    artifact = _artifact_bytes(payload)
    return load_sanitized_ranker_artifact(
        artifact,
        expected_model_id=MODEL_ID_FIXTURE,
        expected_sha256=hashlib.sha256(artifact).hexdigest(),
    )


def test_sanitized_artifact_loads_for_shadow_without_enabling_runtime() -> None:
    policy = _load()

    assert CANONICAL_FEATURE_NAMES == FEATURE_NAMES
    assert policy.model_id == MODEL_ID_FIXTURE
    assert policy.feature_names == FEATURE_NAMES
    assert tuple(policy.weights_by_style) == CANONICAL_STYLE_FAMILIES
    assert policy.example_count == 702
    assert policy.shadow_eligible is True
    assert policy.ranker_enabled is False
    assert policy.failure_reason is None
    assert model_metadata_payload()["modelId"] == MODEL_ID
    assert model_metadata_payload()["rankerEnabled"] is False


def test_artifact_digest_tampering_fails_closed() -> None:
    artifact = _artifact_bytes()
    policy = load_sanitized_ranker_artifact(
        artifact + b" ",
        expected_model_id=MODEL_ID_FIXTURE,
        expected_sha256=hashlib.sha256(artifact).hexdigest(),
    )

    assert policy.model_id == MODEL_ID
    assert policy.weights_by_style == {}
    assert policy.shadow_eligible is False
    assert policy.ranker_enabled is False
    assert policy.failure_reason == "artifact_digest_mismatch"


@pytest.mark.parametrize(
    ("mutate", "failure_reason"),
    [
        (
            lambda payload: payload.update(
                featureSchemaVersion="melody-ranker-features-v2"
            ),
            "feature_schema_mismatch",
        ),
        (
            lambda payload: payload["featureNames"].reverse(),
            "feature_names_mismatch",
        ),
        (
            lambda payload: payload["weightsByStyle"].pop("harmonized"),
            "style_family_mismatch",
        ),
        (
            lambda payload: payload["weightsByStyle"]["single_note_run"].pop(
                "cadence_arrival"
            ),
            "weight_feature_mismatch",
        ),
        (
            lambda payload: payload["weightsByStyle"]["single_note_run"].update(
                cadence_arrival=float("nan")
            ),
            "non_finite_weight",
        ),
        (
            lambda payload: payload.update(sourceActions=[]),
            "artifact_field_mismatch",
        ),
        (
            lambda payload: payload["privacy"].update(
                containsSourceContent=True
            ),
            "privacy_contract_failed",
        ),
    ],
)
def test_invalid_sanitized_artifacts_fail_closed(
    mutate,
    failure_reason: str,
) -> None:
    payload = deepcopy(_artifact_payload())
    mutate(payload)

    policy = _load(payload)

    assert policy.model_id == MODEL_ID
    assert policy.weights_by_style == {}
    assert policy.shadow_eligible is False
    assert policy.ranker_enabled is False
    assert policy.failure_reason == failure_reason
