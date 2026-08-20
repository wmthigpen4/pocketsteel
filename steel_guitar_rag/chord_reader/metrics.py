"""Dependency-free diagnostics for time-aligned chord segments."""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from .labels import PITCH_CLASS, SHARP_NAMES, ChordLabel, normalize_chord


CURRENT_49_STATE_VOCABULARY = tuple(
    ["N"] + [f"{root}:{quality}" for quality in ("maj", "min", "7", "min7") for root in SHARP_NAMES]
)
CONFIDENCE_THRESHOLDS = tuple(index / 100 for index in range(101))
CALIBRATION_BIN_COUNT = 10


def vocabulary_for_prediction(prediction: Mapping[str, Any]) -> tuple[str, ...] | None:
    """Return an exact emit-able vocabulary when the prediction declares or implies one."""

    explicit = prediction.get("vocabularyLabels")
    if isinstance(explicit, Sequence) and not isinstance(explicit, (str, bytes)):
        return tuple(str(value) for value in explicit)

    specification = prediction.get("vocabularySpecification")
    if isinstance(specification, Mapping) and specification.get("schemaVersion") == "chord_factorized_vocabulary_v1":
        qualities = specification.get("qualities")
        if not isinstance(qualities, Sequence) or isinstance(qualities, (str, bytes)):
            raise ValueError("Factorized vocabulary qualities must be a sequence.")
        supports_inversions = bool(specification.get("supportsInversions"))
        values = ["N"]
        for root_index, root in enumerate(SHARP_NAMES):
            for quality in qualities:
                values.append(f"{root}:{quality}")
                if supports_inversions:
                    values.extend(
                        f"{root}:{quality}/{bass}"
                        for bass_index, bass in enumerate(SHARP_NAMES)
                        if bass_index != root_index
                    )
        return tuple(values)

    # The in-browser v2 reader, all current student variants, and the hybrid
    # expose the same N + 4 qualities x 12 roots output contract. Named BTC
    # vocabularies are deliberately not guessed: exact labels must be supplied.
    engine = str(prediction.get("engine") or "").lower()
    model = str(prediction.get("model") or "").lower()
    if (
        engine in {"play-along-v2", "chord-hybrid-v1"}
        or "chord-student" in engine
        or "student" in model
        or "heterogeneous-boundary-guided-ensemble" in model
    ):
        return CURRENT_49_STATE_VOCABULARY
    return None


def _segments(values: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in values:
        start = float(item["start"])
        end = float(item["end"])
        if end <= start:
            raise ValueError("Chord segment end must be greater than start.")
        segment: dict[str, Any] = {
            "start": start,
            "end": end,
            "label": normalize_chord(str(item["label"])),
            "productLabel": normalize_chord(str(item.get("productLabel") or item["label"])),
            "confidence": None,
        }
        raw_confidence = item.get("productConfidence", item.get("confidence"))
        if not isinstance(raw_confidence, bool) and isinstance(raw_confidence, (int, float)):
            confidence = float(raw_confidence)
            if math.isfinite(confidence) and 0 <= confidence <= 1:
                segment["confidence"] = confidence
        output.append(segment)
    output.sort(key=lambda item: item["start"])
    for index, item in enumerate(output):
        if index and item["start"] < output[index - 1]["end"]:
            raise ValueError("Chord segments must not overlap.")
    return output


def _root_matches(left: ChordLabel, right: ChordLabel) -> bool:
    if left.root is None or right.root is None:
        return left.root == right.root
    return PITCH_CLASS[left.root] == PITCH_CLASS[right.root]


def _bass_matches(left: ChordLabel, right: ChordLabel) -> bool:
    if left.bass is None or right.bass is None:
        return left.bass == right.bass
    return PITCH_CLASS[left.bass] == PITCH_CLASS[right.bass]


def _detailed_matches(left: ChordLabel, right: ChordLabel) -> bool:
    if left.root is None or right.root is None:
        return left.detailed_symbol == right.detailed_symbol
    return _root_matches(left, right) and left.quality == right.quality and _bass_matches(left, right)


def _majmin_class(label: ChordLabel) -> str:
    if label.root is None:
        return "none"
    if label.product_symbol.endswith("m") or label.product_symbol.endswith("m7"):
        return "minor"
    return "major"


def _root_key(label: ChordLabel) -> str:
    if label.root is None:
        return "N" if label.quality == "none" else label.detailed_symbol
    return SHARP_NAMES[PITCH_CLASS[label.root]]


def _detailed_key(label: ChordLabel) -> str:
    if label.root is None:
        return "N" if label.quality == "none" else label.detailed_symbol
    value = f"{_root_key(label)}:{label.quality}"
    if label.bass is not None:
        value = f"{value}/{SHARP_NAMES[PITCH_CLASS[label.bass]]}"
    return value


def _levenshtein_edits(left: list[str], right: list[str]) -> dict[str, Any]:
    """Return one deterministic minimum edit script from reference to prediction."""

    matrix = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for left_index in range(len(left) + 1):
        matrix[left_index][0] = left_index
    for right_index in range(len(right) + 1):
        matrix[0][right_index] = right_index
    for left_index, left_value in enumerate(left, start=1):
        for right_index, right_value in enumerate(right, start=1):
            matrix[left_index][right_index] = min(
                matrix[left_index - 1][right_index] + 1,
                matrix[left_index][right_index - 1] + 1,
                matrix[left_index - 1][right_index - 1] + (left_value != right_value),
            )

    operations: list[dict[str, Any]] = []
    counts = {"insertions": 0, "deletions": 0, "substitutions": 0}
    left_index = len(left)
    right_index = len(right)
    while left_index or right_index:
        if (
            left_index
            and right_index
            and left[left_index - 1] == right[right_index - 1]
            and matrix[left_index][right_index] == matrix[left_index - 1][right_index - 1]
        ):
            left_index -= 1
            right_index -= 1
            continue
        if (
            left_index
            and right_index
            and matrix[left_index][right_index] == matrix[left_index - 1][right_index - 1] + 1
        ):
            operations.append(
                {
                    "operation": "substitute",
                    "referenceIndex": left_index - 1,
                    "predictionIndex": right_index - 1,
                    "reference": left[left_index - 1],
                    "prediction": right[right_index - 1],
                }
            )
            counts["substitutions"] += 1
            left_index -= 1
            right_index -= 1
            continue
        if left_index and matrix[left_index][right_index] == matrix[left_index - 1][right_index] + 1:
            operations.append(
                {
                    "operation": "delete",
                    "referenceIndex": left_index - 1,
                    "predictionIndex": right_index,
                    "reference": left[left_index - 1],
                    "prediction": None,
                }
            )
            counts["deletions"] += 1
            left_index -= 1
            continue
        operations.append(
            {
                "operation": "insert",
                "referenceIndex": left_index,
                "predictionIndex": right_index - 1,
                "reference": None,
                "prediction": right[right_index - 1],
            }
        )
        counts["insertions"] += 1
        right_index -= 1

    operations.reverse()
    return {
        "distance": matrix[-1][-1],
        "counts": counts,
        "operations": operations,
    }


def _product_key(label: ChordLabel) -> str:
    if label.root is None:
        return label.product_symbol
    suffix = label.product_symbol[len(label.root) :]
    return f"{SHARP_NAMES[PITCH_CLASS[label.root]]}{suffix}"


def _segment_product_key(segment: Mapping[str, Any]) -> str:
    return _product_key(segment["productLabel"])


def _collapsed_product_sequence(segments: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for segment in segments:
        symbol = _segment_product_key(segment)
        if not values or values[-1] != symbol:
            values.append(symbol)
    return values


def _collapsed_product_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse authored splits that do not represent a musical chord change."""

    output: list[dict[str, Any]] = []
    for segment in segments:
        key = _segment_product_key(segment)
        if (
            output
            and output[-1]["key"] == key
            and math.isclose(float(output[-1]["end"]), float(segment["start"]), abs_tol=1e-9)
        ):
            output[-1]["end"] = segment["end"]
        else:
            output.append({"start": segment["start"], "end": segment["end"], "key": key})
    return output


def _boundary_f1(
    reference: list[dict[str, Any]], prediction: list[dict[str, Any]], tolerance: float
) -> dict[str, float]:
    reference_boundaries = [item["start"] for item in reference[1:]]
    prediction_boundaries = [item["start"] for item in prediction[1:]]
    matched: set[int] = set()
    true_positive = 0
    for boundary in prediction_boundaries:
        choices = [
            (abs(boundary - candidate), index)
            for index, candidate in enumerate(reference_boundaries)
            if index not in matched and abs(boundary - candidate) <= tolerance
        ]
        if choices:
            _distance, index = min(choices)
            matched.add(index)
            true_positive += 1
    precision = true_positive / max(1, len(prediction_boundaries))
    recall = true_positive / max(1, len(reference_boundaries))
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def _confusion_report(cells: Mapping[tuple[str, str], float], total_duration: float) -> dict[str, Any]:
    return {
        "totalDurationSeconds": total_duration,
        "cells": [
            {
                "reference": reference,
                "prediction": prediction,
                "durationSeconds": duration,
            }
            for (reference, prediction), duration in sorted(cells.items())
        ],
    }


def _vocabulary_coverage(reference: list[dict[str, Any]], vocabulary_values: Iterable[str] | None) -> dict[str, Any]:
    reference_duration = sum(float(item["end"]) - float(item["start"]) for item in reference)
    if vocabulary_values is None:
        return {
            "available": False,
            "vocabularySize": None,
            "referenceDurationSeconds": reference_duration,
            "supportedDurationSeconds": None,
            "outOfVocabularyDurationSeconds": None,
            "exactDetailedWeightedRecallCeiling": None,
            "outOfVocabulary": [],
        }

    vocabulary = {_detailed_key(normalize_chord(value)) for value in vocabulary_values}
    supported_duration = 0.0
    out_of_vocabulary: dict[str, float] = {}
    for segment in reference:
        duration = float(segment["end"]) - float(segment["start"])
        label = _detailed_key(segment["label"])
        if label in vocabulary:
            supported_duration += duration
        else:
            out_of_vocabulary[label] = out_of_vocabulary.get(label, 0.0) + duration
    out_of_vocabulary_duration = reference_duration - supported_duration
    return {
        "available": True,
        "vocabularySize": len(vocabulary),
        "referenceDurationSeconds": reference_duration,
        "supportedDurationSeconds": supported_duration,
        "outOfVocabularyDurationSeconds": out_of_vocabulary_duration,
        "exactDetailedWeightedRecallCeiling": supported_duration / max(1e-12, reference_duration),
        "outOfVocabulary": [
            {"label": label, "durationSeconds": duration}
            for label, duration in sorted(out_of_vocabulary.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def _optional_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def _confidence_report(
    *,
    evaluated_duration: float,
    available_duration: float,
    curve_values: Mapping[float, Mapping[str, float]],
    calibration_bins: Sequence[Mapping[str, float]],
) -> dict[str, Any]:
    curve: list[dict[str, Any]] = []
    for threshold in CONFIDENCE_THRESHOLDS:
        values = curve_values[threshold]
        accepted = float(values["acceptedDurationSeconds"])
        curve.append(
            {
                "minimumConfidence": threshold,
                "acceptedDurationSeconds": accepted,
                "coverage": accepted / max(1e-12, evaluated_duration),
                "rootPrecision": _optional_ratio(float(values["rootCorrectDurationSeconds"]), accepted),
                "productPrecision": _optional_ratio(float(values["productCorrectDurationSeconds"]), accepted),
                "majorMinorPrecision": _optional_ratio(float(values["majorMinorCorrectDurationSeconds"]), accepted),
                "detailedPrecision": _optional_ratio(float(values["detailedCorrectDurationSeconds"]), accepted),
                "rootCorrectDurationSeconds": float(values["rootCorrectDurationSeconds"]),
                "productCorrectDurationSeconds": float(values["productCorrectDurationSeconds"]),
                "majorMinorCorrectDurationSeconds": float(values["majorMinorCorrectDurationSeconds"]),
                "detailedCorrectDurationSeconds": float(values["detailedCorrectDurationSeconds"]),
            }
        )

    bins: list[dict[str, Any]] = []
    ece = {"root": 0.0, "product": 0.0, "majorMinor": 0.0, "detailed": 0.0}
    for index, values in enumerate(calibration_bins):
        duration = float(values["durationSeconds"])
        mean_confidence = _optional_ratio(float(values["confidenceMassSeconds"]), duration)
        root_accuracy = _optional_ratio(float(values["rootCorrectDurationSeconds"]), duration)
        product_accuracy = _optional_ratio(float(values["productCorrectDurationSeconds"]), duration)
        major_minor_accuracy = _optional_ratio(float(values["majorMinorCorrectDurationSeconds"]), duration)
        detailed_accuracy = _optional_ratio(float(values["detailedCorrectDurationSeconds"]), duration)
        bins.append(
            {
                "minimumConfidence": index / CALIBRATION_BIN_COUNT,
                "maximumConfidence": (index + 1) / CALIBRATION_BIN_COUNT,
                "includesMaximum": index == CALIBRATION_BIN_COUNT - 1,
                "durationSeconds": duration,
                "confidenceMassSeconds": float(values["confidenceMassSeconds"]),
                "meanConfidence": mean_confidence,
                "rootAccuracy": root_accuracy,
                "productAccuracy": product_accuracy,
                "majorMinorAccuracy": major_minor_accuracy,
                "detailedAccuracy": detailed_accuracy,
                "rootCorrectDurationSeconds": float(values["rootCorrectDurationSeconds"]),
                "productCorrectDurationSeconds": float(values["productCorrectDurationSeconds"]),
                "majorMinorCorrectDurationSeconds": float(values["majorMinorCorrectDurationSeconds"]),
                "detailedCorrectDurationSeconds": float(values["detailedCorrectDurationSeconds"]),
            }
        )
        if duration and mean_confidence is not None:
            weight = duration / max(1e-12, available_duration)
            ece["root"] += weight * abs(mean_confidence - float(root_accuracy))
            ece["product"] += weight * abs(mean_confidence - float(product_accuracy))
            ece["majorMinor"] += weight * abs(mean_confidence - float(major_minor_accuracy))
            ece["detailed"] += weight * abs(mean_confidence - float(detailed_accuracy))

    return {
        "available": available_duration > 0,
        "evaluatedDurationSeconds": evaluated_duration,
        "confidenceAvailableDurationSeconds": available_duration,
        "confidenceMissingDurationSeconds": evaluated_duration - available_duration,
        "curve": curve,
        "calibration": {
            "binCount": CALIBRATION_BIN_COUNT,
            "expectedCalibrationError": ece
            if available_duration > 0
            else {
                "root": None,
                "product": None,
                "majorMinor": None,
                "detailed": None,
            },
            "bins": bins,
        },
    }


def score_segments(
    reference_values: Iterable[Mapping[str, Any]],
    prediction_values: Iterable[Mapping[str, Any]],
    *,
    boundary_tolerance_seconds: float = 0.25,
    vocabulary_values: Iterable[str] | None = CURRENT_49_STATE_VOCABULARY,
) -> dict[str, Any]:
    reference = _segments(reference_values)
    prediction = _segments(prediction_values)
    if not reference:
        raise ValueError("Reference must contain chord segments.")

    boundaries = sorted(
        set(
            [value for item in reference for value in (item["start"], item["end"])]
            + [value for item in prediction for value in (item["start"], item["end"])]
        )
    )
    # Scientific recall is defined over every reference-supported instant.  A
    # prediction gap is an abstention/error, not permission to remove a hard
    # interval from the denominator.
    total = 0.0
    prediction_covered = 0.0
    root_correct = 0.0
    product_correct = 0.0
    majmin_correct = 0.0
    detailed_correct = 0.0
    confusion_cells: dict[str, dict[tuple[str, str], float]] = {
        "root": {},
        "product": {},
        "majorMinor": {},
        "quality": {},
        "detailed": {},
    }
    confidence_available_duration = 0.0
    curve_values: dict[float, dict[str, float]] = {
        threshold: {
            "acceptedDurationSeconds": 0.0,
            "rootCorrectDurationSeconds": 0.0,
            "productCorrectDurationSeconds": 0.0,
            "majorMinorCorrectDurationSeconds": 0.0,
            "detailedCorrectDurationSeconds": 0.0,
        }
        for threshold in CONFIDENCE_THRESHOLDS
    }
    calibration_bins: list[dict[str, float]] = [
        {
            "durationSeconds": 0.0,
            "confidenceMassSeconds": 0.0,
            "rootCorrectDurationSeconds": 0.0,
            "productCorrectDurationSeconds": 0.0,
            "majorMinorCorrectDurationSeconds": 0.0,
            "detailedCorrectDurationSeconds": 0.0,
        }
        for _ in range(CALIBRATION_BIN_COUNT)
    ]
    ref_index = pred_index = 0
    for start, end in zip(boundaries, boundaries[1:]):
        midpoint = (start + end) / 2
        while ref_index + 1 < len(reference) and reference[ref_index]["end"] <= midpoint:
            ref_index += 1
        while pred_index + 1 < len(prediction) and prediction[pred_index]["end"] <= midpoint:
            pred_index += 1
        ref = reference[ref_index]
        pred = prediction[pred_index] if prediction else None
        if not (ref["start"] <= midpoint < ref["end"]):
            continue
        duration = end - start
        total += duration
        prediction_present = pred is not None and pred["start"] <= midpoint < pred["end"]
        if prediction_present:
            prediction_covered += duration
        root_match = prediction_present and _root_matches(ref["label"], pred["label"])
        product_match = prediction_present and (_segment_product_key(ref) == _segment_product_key(pred))
        major_minor_match = (
            prediction_present and root_match and (_majmin_class(ref["label"]) == _majmin_class(pred["label"]))
        )
        detailed_match = prediction_present and _detailed_matches(ref["label"], pred["label"])
        if root_match:
            root_correct += duration
        if product_match:
            product_correct += duration
        if major_minor_match:
            majmin_correct += duration
        if detailed_match:
            detailed_correct += duration

        confusion_keys = (
            {
                "root": (_root_key(ref["label"]), _root_key(pred["label"])),
                "product": (_segment_product_key(ref), _segment_product_key(pred)),
                "majorMinor": (
                    _majmin_class(ref["label"]),
                    _majmin_class(pred["label"]),
                ),
                "quality": (ref["label"].quality, pred["label"].quality),
                "detailed": (
                    _detailed_key(ref["label"]),
                    _detailed_key(pred["label"]),
                ),
            }
            if prediction_present
            else {
                "root": (_root_key(ref["label"]), "MISSING"),
                "product": (_segment_product_key(ref), "MISSING"),
                "majorMinor": (_majmin_class(ref["label"]), "missing"),
                "quality": (ref["label"].quality, "missing"),
                "detailed": (_detailed_key(ref["label"]), "MISSING"),
            }
        )
        for name, cell in confusion_keys.items():
            confusion_cells[name][cell] = confusion_cells[name].get(cell, 0.0) + duration

        confidence = pred["confidence"] if prediction_present else None
        if confidence is not None:
            confidence_available_duration += duration
            for threshold, values in curve_values.items():
                if confidence < threshold:
                    continue
                values["acceptedDurationSeconds"] += duration
                values["rootCorrectDurationSeconds"] += duration if root_match else 0.0
                values["productCorrectDurationSeconds"] += duration if product_match else 0.0
                values["majorMinorCorrectDurationSeconds"] += duration if major_minor_match else 0.0
                values["detailedCorrectDurationSeconds"] += duration if detailed_match else 0.0
            bin_index = min(CALIBRATION_BIN_COUNT - 1, int(confidence * CALIBRATION_BIN_COUNT))
            calibration_bin = calibration_bins[bin_index]
            calibration_bin["durationSeconds"] += duration
            calibration_bin["confidenceMassSeconds"] += confidence * duration
            calibration_bin["rootCorrectDurationSeconds"] += duration if root_match else 0.0
            calibration_bin["productCorrectDurationSeconds"] += duration if product_match else 0.0
            calibration_bin["majorMinorCorrectDurationSeconds"] += duration if major_minor_match else 0.0
            calibration_bin["detailedCorrectDurationSeconds"] += duration if detailed_match else 0.0

    reference_sequence = _collapsed_product_sequence(reference)
    prediction_sequence = _collapsed_product_sequence(prediction)
    sequence_edits = _levenshtein_edits(reference_sequence, prediction_sequence)
    return {
        "evaluatedDurationSeconds": total,
        "referenceSupportedDurationSeconds": total,
        "predictionCoveredDurationSeconds": prediction_covered,
        "predictionMissingDurationSeconds": max(0.0, total - prediction_covered),
        "predictionCoverage": prediction_covered / max(1e-12, total),
        "rootWeightedRecall": root_correct / max(1e-12, total),
        "productWeightedRecall": product_correct / max(1e-12, total),
        "majorMinorWeightedRecall": majmin_correct / max(1e-12, total),
        "detailedWeightedRecall": detailed_correct / max(1e-12, total),
        "boundary": _boundary_f1(
            _collapsed_product_segments(reference),
            _collapsed_product_segments(prediction),
            boundary_tolerance_seconds,
        ),
        "authoredSegmentBoundary": _boundary_f1(
            reference,
            prediction,
            boundary_tolerance_seconds,
        ),
        "sequenceEditRate": sequence_edits["distance"] / max(1, len(reference_sequence)),
        "referenceChordCount": len(reference_sequence),
        "predictedChordCount": len(prediction_sequence),
        "sequenceEdits": sequence_edits,
        "vocabularyCoverage": _vocabulary_coverage(reference, vocabulary_values),
        "confusion": {name: _confusion_report(cells, total) for name, cells in confusion_cells.items()},
        "confidenceCoverage": _confidence_report(
            evaluated_duration=total,
            available_duration=confidence_available_duration,
            curve_values=curve_values,
            calibration_bins=calibration_bins,
        ),
    }
