"""Sanitized Amazing Tablature runtime policy.

The superseded 51-image beta is deliberately not active. Until an exact
complete-discovery challenger passes the fixed held-out gates and receives
explicit promotion approval, Melody Studio uses its deterministic arranger
without a learned ranking penalty. Private annotations, source actions,
profile snapshots, and source content must never be added here.
"""

from __future__ import annotations

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
