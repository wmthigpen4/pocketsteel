"""Dependency-free baseline metrics for time-aligned chord segments."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .labels import PITCH_CLASS, ChordLabel, normalize_chord


def _segments(values: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in values:
        start = float(item["start"])
        end = float(item["end"])
        if end <= start:
            raise ValueError("Chord segment end must be greater than start.")
        output.append({"start": start, "end": end, "label": normalize_chord(str(item["label"]))})
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


def _levenshtein(left: list[str], right: list[str]) -> int:
    row = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        next_row = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            next_row.append(
                min(
                    next_row[-1] + 1,
                    row[right_index] + 1,
                    row[right_index - 1] + (left_value != right_value),
                )
            )
        row = next_row
    return row[-1]


def _collapsed_product_sequence(segments: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for segment in segments:
        label = segment["label"]
        if label.root is None:
            symbol = label.product_symbol
        else:
            suffix = label.product_symbol[len(label.root) :]
            symbol = f"{PITCH_CLASS[label.root]}:{suffix}"
        if not values or values[-1] != symbol:
            values.append(symbol)
    return values


def _boundary_f1(reference: list[dict[str, Any]], prediction: list[dict[str, Any]], tolerance: float) -> dict[str, float]:
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


def score_segments(
    reference_values: Iterable[Mapping[str, Any]],
    prediction_values: Iterable[Mapping[str, Any]],
    *,
    boundary_tolerance_seconds: float = 0.25,
) -> dict[str, Any]:
    reference = _segments(reference_values)
    prediction = _segments(prediction_values)
    if not reference or not prediction:
        raise ValueError("Reference and prediction must both contain chord segments.")

    boundaries = sorted(
        set(
            [value for item in reference for value in (item["start"], item["end"])]
            + [value for item in prediction for value in (item["start"], item["end"])]
        )
    )
    total = 0.0
    root_correct = 0.0
    majmin_correct = 0.0
    detailed_correct = 0.0
    ref_index = pred_index = 0
    for start, end in zip(boundaries, boundaries[1:]):
        midpoint = (start + end) / 2
        while ref_index + 1 < len(reference) and reference[ref_index]["end"] <= midpoint:
            ref_index += 1
        while pred_index + 1 < len(prediction) and prediction[pred_index]["end"] <= midpoint:
            pred_index += 1
        ref = reference[ref_index]
        pred = prediction[pred_index]
        if not (ref["start"] <= midpoint < ref["end"] and pred["start"] <= midpoint < pred["end"]):
            continue
        duration = end - start
        total += duration
        if _root_matches(ref["label"], pred["label"]):
            root_correct += duration
            if _majmin_class(ref["label"]) == _majmin_class(pred["label"]):
                majmin_correct += duration
        if _detailed_matches(ref["label"], pred["label"]):
            detailed_correct += duration

    reference_sequence = _collapsed_product_sequence(reference)
    prediction_sequence = _collapsed_product_sequence(prediction)
    edit_distance = _levenshtein(reference_sequence, prediction_sequence)
    return {
        "evaluatedDurationSeconds": total,
        "rootWeightedRecall": root_correct / max(1e-12, total),
        "majorMinorWeightedRecall": majmin_correct / max(1e-12, total),
        "detailedWeightedRecall": detailed_correct / max(1e-12, total),
        "boundary": _boundary_f1(reference, prediction, boundary_tolerance_seconds),
        "sequenceEditRate": edit_distance / max(1, len(reference_sequence)),
        "referenceChordCount": len(reference_sequence),
        "predictedChordCount": len(prediction_sequence),
    }
