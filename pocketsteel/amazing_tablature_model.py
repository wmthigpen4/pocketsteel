"""Sanitized approved Amazing Tablature beta model.

This module contains only the copedent-neutral promotion artifact approved for
runtime use. Private annotations, source actions, profile snapshots, and source
content must never be added here.
"""

from __future__ import annotations

from typing import Final


MODEL_ID: Final = "at-44c59f08724d501e"
MODEL_STATUS: Final = "approved_beta"
MODEL_SCHEMA_VERSION: Final = "amazing-tablature-training-v1"
FEATURE_SCHEMA_VERSION: Final = "melody-ranker-features-v1"
EXAMPLE_COUNT: Final = 45
COPEDENT_NEUTRAL: Final = True
FEATURE_NAMES: Final = (
    "texture_1",
    "texture_2",
    "texture_3",
    "bar_travel",
    "control_changes",
    "pocket_changes",
    "voice_leading",
    "sustained_voices",
    "repicked_voices",
    "cadence_arrival",
)

WEIGHTS_BY_STYLE: Final = {
    "chord_melody": {
        "bar_travel": 0.05,
        "cadence_arrival": 0.0,
        "control_changes": 0.05,
        "pocket_changes": 0.05,
        "repicked_voices": 0.0,
        "sustained_voices": 0.0,
        "texture_1": 0.05,
        "texture_2": 0.0,
        "texture_3": -0.05,
        "voice_leading": 0.0,
    },
    "fixed_pocket": {
        "bar_travel": 0.05,
        "cadence_arrival": 0.0,
        "control_changes": 0.0,
        "pocket_changes": 0.05,
        "repicked_voices": 0.0,
        "sustained_voices": 0.0,
        "texture_1": 0.05,
        "texture_2": 0.0,
        "texture_3": -0.05,
        "voice_leading": 0.0,
    },
    "harmonized": {
        "bar_travel": 0.05,
        "cadence_arrival": 0.0,
        "control_changes": 0.05,
        "pocket_changes": 0.05,
        "repicked_voices": 0.0,
        "sustained_voices": 0.0,
        "texture_1": 0.05,
        "texture_2": -0.05,
        "texture_3": 0.0,
        "voice_leading": 0.0,
    },
    "lever_driven": {
        "bar_travel": 0.05,
        "cadence_arrival": 0.0,
        "control_changes": 0.0,
        "pocket_changes": 0.05,
        "repicked_voices": 0.0,
        "sustained_voices": 0.0,
        "texture_1": 0.05,
        "texture_2": 0.0,
        "texture_3": -0.05,
        "voice_leading": 0.0,
    },
    "single_note_run": {
        "bar_travel": 0.05,
        "cadence_arrival": 0.0,
        "control_changes": 0.0,
        "pocket_changes": 0.05,
        "repicked_voices": 0.0,
        "sustained_voices": 0.0,
        "texture_1": 0.0,
        "texture_2": 0.0,
        "texture_3": 0.0,
        "voice_leading": 0.0,
    },
    "vocal_steel": {
        "bar_travel": 0.05,
        "cadence_arrival": 0.0,
        "control_changes": 0.0,
        "pocket_changes": 0.05,
        "repicked_voices": 0.0,
        "sustained_voices": 0.0,
        "texture_1": 0.05,
        "texture_2": 0.0,
        "texture_3": -0.05,
        "voice_leading": 0.0,
    },
}


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
    }
