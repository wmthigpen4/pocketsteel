"""Precision-first discovery-only classifier for printed tab-cell glyphs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from PIL import Image, ImageOps


GLYPH_FEATURE_SCHEMA_VERSION = "amazing-tablature-glyph-hog-v1"
GLYPH_DECODER_SCHEMA_VERSION = "amazing-tablature-glyph-decoder-v1"
DEFAULT_MINIMUM_LABEL_SUPPORT = 8
DEFAULT_MINIMUM_CV_PREDICTIONS = 30
DEFAULT_MINIMUM_CV_PRECISION = 0.95
_CONFIDENCE_THRESHOLDS = (0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60)


class GlyphDecoderError(ValueError):
    """Raised when glyph evidence violates the decoder contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def glyph_label(fret: int, controls: Sequence[str]) -> str:
    normalized_controls = "".join(sorted(str(value).upper() for value in controls))
    return f"{int(fret)}|{normalized_controls}"


def glyph_label_token(label: str) -> str:
    fret, separator, controls = str(label).partition("|")
    if not separator or not fret.isdigit():
        raise GlyphDecoderError("A glyph label must contain fret|controls.")
    return f"{int(fret)}{controls}"


def glyph_feature_vector(image: Image.Image) -> list[float] | None:
    """Return a normalized HOG vector after suppressing long tab-grid strokes."""

    prepared = ImageOps.autocontrast(image.convert("L")).resize(
        (96, 48),
        Image.Resampling.LANCZOS,
    )
    gray = np.asarray(prepared, dtype=np.float32) / 255.0
    ink = 1.0 - gray
    row_occupancy = np.mean(ink > 0.25, axis=1)
    gray[row_occupancy > 0.55, :] = 1.0
    gray[gray > 0.88] = 1.0
    gradient_x = np.zeros_like(gray)
    gradient_y = np.zeros_like(gray)
    gradient_x[:, 1:-1] = gray[:, :-2] - gray[:, 2:]
    gradient_y[1:-1, :] = gray[:-2, :] - gray[2:, :]
    magnitude = np.hypot(gradient_x, gradient_y)
    if float(np.sum(magnitude)) < 1e-6:
        return None
    angle = (np.arctan2(gradient_y, gradient_x) + np.pi) % np.pi
    features: list[float] = []
    for top in range(0, 48, 8):
        for left in range(0, 96, 8):
            cell_angles = angle[top : top + 8, left : left + 8]
            cell_magnitude = magnitude[top : top + 8, left : left + 8]
            bins = np.floor(cell_angles / (np.pi / 9)).astype(int)
            bins = np.clip(bins, 0, 8)
            histogram = np.asarray(
                [
                    float(np.sum(cell_magnitude[bins == bucket]))
                    for bucket in range(9)
                ],
                dtype=np.float32,
            )
            histogram /= float(np.linalg.norm(histogram)) + 1e-6
            features.extend(float(value) for value in histogram)
    vector = np.asarray(features, dtype=np.float32)
    vector /= float(np.linalg.norm(vector)) + 1e-6
    return [round(float(value), 7) for value in vector]


def _predict(
    training: Sequence[Mapping[str, Any]],
    feature: Sequence[float],
    *,
    neighbor_count: int = 9,
) -> tuple[str | None, float]:
    if not training:
        return None, 0.0
    query = np.asarray(feature, dtype=np.float32)
    scored = sorted(
        (
            (
                float(np.dot(query, np.asarray(row["feature"], dtype=np.float32))),
                str(row["label"]),
            )
            for row in training
        ),
        reverse=True,
    )[:neighbor_count]
    votes: dict[str, float] = defaultdict(float)
    for similarity, label in scored:
        votes[label] += max(0.0, similarity) ** 5
    total = sum(votes.values())
    if total <= 0:
        return None, 0.0
    label, vote = max(votes.items(), key=lambda value: (value[1], value[0]))
    return label, vote / total


def _grouped_cv_predictions(
    examples: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for group_id in sorted({str(row["contentUnitId"]) for row in examples}):
        training = [
            row for row in examples if str(row["contentUnitId"]) != group_id
        ]
        for row in examples:
            if str(row["contentUnitId"]) != group_id:
                continue
            predicted, confidence = _predict(training, row["feature"])
            predictions.append(
                {
                    "actual": str(row["label"]),
                    "predicted": predicted,
                    "confidence": confidence,
                }
            )
    return predictions


def train_glyph_decoder(
    examples: Sequence[Mapping[str, Any]],
    *,
    source_cohort_id: str,
    minimum_label_support: int = DEFAULT_MINIMUM_LABEL_SUPPORT,
    minimum_cv_predictions: int = DEFAULT_MINIMUM_CV_PREDICTIONS,
    minimum_cv_precision: float = DEFAULT_MINIMUM_CV_PRECISION,
) -> dict[str, Any]:
    """Train a private feature artifact and calibrate an abstention threshold."""

    if not source_cohort_id:
        raise GlyphDecoderError("A glyph decoder requires a source cohort.")
    counts = Counter(str(row.get("label") or "") for row in examples)
    eligible_labels = {
        label for label, count in counts.items() if label and count >= minimum_label_support
    }
    normalized = [
        {
            "contentUnitId": str(row.get("contentUnitId") or ""),
            "label": str(row.get("label") or ""),
            "feature": [float(value) for value in row.get("feature") or ()],
        }
        for row in examples
        if (
            str(row.get("contentUnitId") or "")
            and str(row.get("label") or "") in eligible_labels
            and row.get("feature")
        )
    ]
    predictions = _grouped_cv_predictions(normalized)
    calibration: list[dict[str, Any]] = []
    selected_threshold: float | None = None
    for threshold in _CONFIDENCE_THRESHOLDS:
        selected = [
            row for row in predictions if float(row["confidence"]) >= threshold
        ]
        correct = sum(row["predicted"] == row["actual"] for row in selected)
        precision = correct / len(selected) if selected else 0.0
        calibration.append(
            {
                "threshold": threshold,
                "predictionCount": len(selected),
                "correctCount": correct,
                "precision": precision,
                "coverage": len(selected) / len(predictions) if predictions else 0.0,
            }
        )
        if (
            len(selected) >= minimum_cv_predictions
            and precision >= minimum_cv_precision
        ):
            selected_threshold = threshold
    artifact_core = {
        "schemaVersion": GLYPH_DECODER_SCHEMA_VERSION,
        "featureSchemaVersion": GLYPH_FEATURE_SCHEMA_VERSION,
        "sourceCohortId": source_cohort_id,
        "policy": "semantic_glyph_or_abstain",
        "thresholds": {
            "minimumLabelSupport": minimum_label_support,
            "minimumCvPredictions": minimum_cv_predictions,
            "minimumCvPrecision": minimum_cv_precision,
            "selectedConfidence": selected_threshold,
        },
        "labelCounts": dict(sorted(counts.items())),
        "trainingExampleCount": len(normalized),
        "contentUnitCount": len(
            {str(row["contentUnitId"]) for row in normalized}
        ),
        "groupedCrossValidation": {
            "foldUnit": "content_unit",
            "foldCount": len(
                {str(row["contentUnitId"]) for row in normalized}
            ),
            "calibration": calibration,
        },
        "examples": normalized,
        "automationEligible": selected_threshold is not None,
        "validationDataUsed": False,
        "sealedTestDataUsed": False,
    }
    digest = _sha256_json(artifact_core)
    return {
        **artifact_core,
        "decoderId": f"atg-{digest[:16]}",
        "artifactDigest": digest,
    }


def classify_glyph(
    decoder: Mapping[str, Any],
    image: Image.Image,
) -> dict[str, Any]:
    """Classify one cell or explicitly abstain."""

    if decoder.get("schemaVersion") != GLYPH_DECODER_SCHEMA_VERSION:
        raise GlyphDecoderError("Unsupported glyph decoder schema.")
    threshold = (decoder.get("thresholds") or {}).get("selectedConfidence")
    feature = glyph_feature_vector(image)
    if threshold is None or feature is None:
        return {"decision": "unresolved", "reason": "decoder_not_eligible"}
    label, confidence = _predict(decoder.get("examples") or (), feature)
    if label is None or confidence < float(threshold):
        return {
            "decision": "unresolved",
            "reason": "confidence_below_discovery_calibration",
            "confidence": confidence,
        }
    return {
        "decision": "semantic_glyph",
        "token": glyph_label_token(label),
        "label": label,
        "confidence": confidence,
    }
