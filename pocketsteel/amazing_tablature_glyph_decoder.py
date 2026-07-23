"""Precision-first discovery-only classifier for printed tab-cell glyphs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps


GLYPH_FEATURE_SCHEMA_VERSION = "amazing-tablature-glyph-centered-v2"
GLYPH_DECODER_SCHEMA_VERSION = "amazing-tablature-glyph-decoder-v3"
GLYPH_INPUT_MODE = "contact_sheet_token_crop"
GLYPH_NEIGHBOR_COUNT = 5
GLYPH_SIMILARITY_POWER = 2
DEFAULT_MINIMUM_LABEL_SUPPORT = 8
DEFAULT_MINIMUM_CV_PREDICTIONS = 30
DEFAULT_MINIMUM_CV_PRECISION = 0.995
_CONFIDENCE_THRESHOLDS = (
    1.0,
    0.999,
    0.995,
    0.99,
    0.98,
    0.97,
    0.95,
    0.90,
    0.85,
    0.80,
    0.75,
    0.70,
    0.65,
    0.60,
)


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


def contact_sheet_token_crops(
    image: Image.Image,
    labels: Sequence[str],
) -> dict[str, Image.Image]:
    """Return token-only crops using the exact validation card geometry."""

    if not labels:
        return {}
    source = image.convert("RGB")
    columns = 4
    rows = max(1, (len(labels) + columns - 1) // columns)
    card_width = source.width // columns
    card_height = source.height // rows
    patch_width = max(1, card_width - 120)
    patch_height = max(1, card_height - 42)
    return {
        str(label): source.crop(
            (
                (index % columns) * card_width + 90,
                (index // columns) * card_height + 30,
                min(
                    source.width,
                    (index % columns) * card_width + 90 + patch_width,
                ),
                min(
                    source.height,
                    (index // columns) * card_height + 30 + patch_height,
                ),
            )
        )
        for index, label in enumerate(labels)
    }


def glyph_feature_vector(image: Image.Image) -> list[float] | None:
    """Return centered raw-ink and HOG features for the target tab glyph."""

    prepared = ImageOps.autocontrast(image.convert("L"))
    gray_source = np.asarray(prepared, dtype=np.uint8)
    if not gray_source.size:
        return None
    _threshold, binary = cv2.threshold(
        gray_source,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    height, width = binary.shape
    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (max(12, width // 5), 1),
        ),
    )
    vertical = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, max(12, int(height * 0.65))),
        ),
    )
    glyph_ink = cv2.subtract(binary, cv2.max(horizontal, vertical))
    glyph_ink = cv2.morphologyEx(
        glyph_ink,
        cv2.MORPH_OPEN,
        np.ones((2, 2), dtype=np.uint8),
    )
    count, component_map, stats, centroids = (
        cv2.connectedComponentsWithStats(glyph_ink, 8)
    )
    components: list[dict[str, float | int]] = []
    for index in range(1, count):
        x, y, component_width, component_height, area = (
            int(value) for value in stats[index]
        )
        if (
            area < max(4, int(height * width * 0.0002))
            or component_height < max(3, int(height * 0.10))
            or component_width > component_height * 3.0
        ):
            continue
        components.append(
            {
                "index": index,
                "x": x,
                "y": y,
                "width": component_width,
                "height": component_height,
                "area": area,
                "centerX": float(centroids[index][0]),
                "centerY": float(centroids[index][1]),
            }
        )
    if not components:
        return None
    target_x = width / 2
    main = min(
        components,
        key=lambda item: (
            abs(float(item["centerX"]) - target_x)
            / max(1.0, float(width))
            - 0.20
            * float(item["height"])
            / max(1.0, float(height)),
            -int(item["area"]),
        ),
    )
    selected = {int(main["index"])}
    cluster_left = int(main["x"])
    cluster_right = cluster_left + int(main["width"])
    cluster_top = int(main["y"])
    cluster_bottom = cluster_top + int(main["height"])
    maximum_gap = max(4, int(main["height"]) // 2)
    for _pass in range(2):
        for component in components:
            index = int(component["index"])
            if index in selected:
                continue
            left = int(component["x"])
            right = left + int(component["width"])
            top = int(component["y"])
            bottom = top + int(component["height"])
            horizontal_gap = max(
                0,
                max(cluster_left, left) - min(cluster_right, right),
            )
            vertical_overlap = max(
                0,
                min(cluster_bottom, bottom) - max(cluster_top, top),
            )
            if (
                horizontal_gap <= maximum_gap
                and vertical_overlap
                >= min(
                    int(component["height"]),
                    cluster_bottom - cluster_top,
                )
                * 0.20
            ):
                selected.add(index)
                cluster_left = min(cluster_left, left)
                cluster_right = max(cluster_right, right)
                cluster_top = min(cluster_top, top)
                cluster_bottom = max(cluster_bottom, bottom)
    selected_ink = np.zeros_like(glyph_ink)
    selected_ink[np.isin(component_map, list(selected))] = 255
    padding = max(
        2,
        int(
            max(
                cluster_right - cluster_left,
                cluster_bottom - cluster_top,
            )
            * 0.10
        ),
    )
    left = max(0, cluster_left - padding)
    right = min(width, cluster_right + padding)
    top = max(0, cluster_top - padding)
    bottom = min(height, cluster_bottom + padding)
    isolated = selected_ink[top:bottom, left:right]
    if not isolated.size or not np.any(isolated):
        return None
    canvas = np.zeros((48, 96), dtype=np.uint8)
    scale = min(
        88 / max(1, isolated.shape[1]),
        42 / max(1, isolated.shape[0]),
    )
    resized = cv2.resize(
        isolated,
        (
            max(1, int(round(isolated.shape[1] * scale))),
            max(1, int(round(isolated.shape[0] * scale))),
        ),
        interpolation=cv2.INTER_AREA,
    )
    paste_y = (canvas.shape[0] - resized.shape[0]) // 2
    paste_x = (canvas.shape[1] - resized.shape[1]) // 2
    canvas[
        paste_y : paste_y + resized.shape[0],
        paste_x : paste_x + resized.shape[1],
    ] = resized
    gray = 1.0 - (canvas.astype(np.float32) / 255.0)
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
    raw = cv2.resize(
        canvas,
        (32, 16),
        interpolation=cv2.INTER_AREA,
    ).astype(np.float32)
    raw /= 255.0
    vector = np.concatenate(
        (
            raw.reshape(-1),
            np.asarray(features, dtype=np.float32),
        )
    )
    vector /= float(np.linalg.norm(vector)) + 1e-6
    return [round(float(value), 7) for value in vector]


def _predict(
    training: Sequence[Mapping[str, Any]],
    feature: Sequence[float],
    *,
    neighbor_count: int = GLYPH_NEIGHBOR_COUNT,
    similarity_power: int = GLYPH_SIMILARITY_POWER,
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
        votes[label] += max(0.0, similarity) ** similarity_power
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
    selected_labels: list[str] = []
    for threshold in _CONFIDENCE_THRESHOLDS:
        threshold_predictions = [
            row for row in predictions if float(row["confidence"]) >= threshold
        ]
        label_metrics: dict[str, dict[str, Any]] = {}
        for label in sorted(eligible_labels):
            label_rows = [
                row
                for row in threshold_predictions
                if row["predicted"] == label
            ]
            correct = sum(
                row["predicted"] == row["actual"]
                for row in label_rows
            )
            precision = (
                correct / len(label_rows) if label_rows else 0.0
            )
            label_metrics[label] = {
                "predictionCount": len(label_rows),
                "correctCount": correct,
                "precision": precision,
            }
        accepted_labels = sorted(
            label
            for label, metrics in label_metrics.items()
            if (
                int(metrics["predictionCount"])
                >= minimum_label_support
                and float(metrics["precision"])
                >= minimum_cv_precision
            )
        )
        selected = [
            row
            for row in threshold_predictions
            if row["predicted"] in accepted_labels
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
                "acceptedLabels": accepted_labels,
                "labelMetrics": label_metrics,
            }
        )
        if (
            len(selected) >= minimum_cv_predictions
            and precision >= minimum_cv_precision
        ):
            selected_threshold = threshold
            selected_labels = accepted_labels
    artifact_core = {
        "schemaVersion": GLYPH_DECODER_SCHEMA_VERSION,
        "featureSchemaVersion": GLYPH_FEATURE_SCHEMA_VERSION,
        "inputMode": GLYPH_INPUT_MODE,
        "classifier": {
            "kind": "weighted_cosine_nearest_neighbors",
            "neighborCount": GLYPH_NEIGHBOR_COUNT,
            "similarityPower": GLYPH_SIMILARITY_POWER,
        },
        "sourceCohortId": source_cohort_id,
        "policy": "semantic_glyph_or_abstain",
        "thresholds": {
            "minimumLabelSupport": minimum_label_support,
            "minimumCvPredictions": minimum_cv_predictions,
            "minimumCvPrecision": minimum_cv_precision,
            "selectedConfidence": selected_threshold,
        },
        "acceptedLabels": selected_labels,
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
    accepted_labels = {
        str(value) for value in decoder.get("acceptedLabels") or ()
    }
    feature = glyph_feature_vector(image)
    if threshold is None or not accepted_labels or feature is None:
        return {"decision": "unresolved", "reason": "decoder_not_eligible"}
    label, confidence = _predict(decoder.get("examples") or (), feature)
    if (
        label is None
        or label not in accepted_labels
        or confidence < float(threshold)
    ):
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
