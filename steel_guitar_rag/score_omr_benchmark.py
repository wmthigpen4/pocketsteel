"""Founder-reviewed acceptance metrics for printed-score recognition."""

from __future__ import annotations

import statistics
from typing import Any, Mapping, Sequence


FAILURE_LAYERS = {
    "document_intake",
    "staff_selection",
    "omr",
    "normalization",
    "arrangement",
    "rendering",
    "export",
}


def benchmark_score_omr(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compare candidate drafts with frozen reference drafts.

    Events are compared in score order because the acceptance corpus is
    founder-reviewed and carries exact expected event order.
    """

    total_events = 0
    exact_pitch = 0
    exact_rhythm = 0
    clean_pages = 0
    clean_pages_with_at_most_two_corrections = 0
    correction_ratios: list[float] = []
    silent_errors = 0
    failures_by_layer = {layer: 0 for layer in sorted(FAILURE_LAYERS)}
    case_results: list[dict[str, Any]] = []
    for case in cases:
        reference_events = _events(case.get("reference"))
        candidate_events = _events(case.get("candidate"))
        paired = list(zip(reference_events, candidate_events))
        pitch_matches = sum(
            int(reference.get("pitchValue") == candidate.get("pitchValue"))
            for reference, candidate in paired
        )
        rhythm_matches = sum(
            int(
                float(reference.get("beat") or 0) == float(candidate.get("beat") or 0)
                and float(reference.get("durationBeats") or 0) == float(candidate.get("durationBeats") or 0)
            )
            for reference, candidate in paired
        )
        total_events += len(reference_events)
        exact_pitch += pitch_matches
        exact_rhythm += rhythm_matches
        unmatched = abs(len(reference_events) - len(candidate_events))
        flagged_ids = set((case.get("candidate") or {}).get("review", {}).get("flaggedEventIds", []))
        mismatched_ids = {
            str(candidate.get("id"))
            for reference, candidate in paired
            if reference.get("pitchValue") != candidate.get("pitchValue")
            or float(reference.get("beat") or 0) != float(candidate.get("beat") or 0)
            or float(reference.get("durationBeats") or 0) != float(candidate.get("durationBeats") or 0)
        }
        case_silent_errors = len(mismatched_ids - flagged_ids) + unmatched
        silent_errors += case_silent_errors
        corrections = int(case.get("corrections") or 0)
        if case.get("clean") is True:
            clean_pages += 1
            clean_pages_with_at_most_two_corrections += int(corrections <= 2)
        manual_seconds = float(case.get("manualEntrySeconds") or 0)
        correction_seconds = float(case.get("correctionSeconds") or 0)
        if manual_seconds > 0:
            correction_ratios.append(correction_seconds / manual_seconds)
        layer = str(case.get("failureLayer") or "")
        if layer:
            if layer not in FAILURE_LAYERS:
                raise ValueError(f"Unknown failure layer: {layer}")
            failures_by_layer[layer] += 1
        case_results.append(
            {
                "id": str(case.get("id") or ""),
                "referenceEventCount": len(reference_events),
                "candidateEventCount": len(candidate_events),
                "exactPitchCount": pitch_matches,
                "exactRhythmCount": rhythm_matches,
                "corrections": corrections,
                "silentErrors": case_silent_errors,
                "failureLayer": layer or None,
            }
        )

    pitch_accuracy = exact_pitch / total_events if total_events else 0.0
    rhythm_accuracy = exact_rhythm / total_events if total_events else 0.0
    clean_two_correction_rate = (
        clean_pages_with_at_most_two_corrections / clean_pages if clean_pages else 0.0
    )
    median_correction_ratio = statistics.median(correction_ratios) if correction_ratios else None
    gates = {
        "pitchAccuracy": pitch_accuracy >= 0.98,
        "onsetDurationAccuracy": rhythm_accuracy >= 0.95,
        "cleanPagesAtMostTwoCorrections": clean_two_correction_rate >= 0.9,
        "correctionTime": median_correction_ratio is not None and median_correction_ratio < (1 / 3),
        "noSilentErrors": silent_errors == 0,
    }
    return {
        "schemaVersion": "score_omr_benchmark_v1",
        "caseCount": len(cases),
        "eventCount": total_events,
        "metrics": {
            "exactPitchAccuracy": round(pitch_accuracy, 6),
            "exactOnsetDurationAccuracy": round(rhythm_accuracy, 6),
            "cleanPagesAtMostTwoCorrectionsRate": round(clean_two_correction_rate, 6),
            "medianCorrectionToManualTimeRatio": (
                round(median_correction_ratio, 6) if median_correction_ratio is not None else None
            ),
            "silentErrorCount": silent_errors,
        },
        "gates": gates,
        "passed": all(gates.values()),
        "failuresByLayer": failures_by_layer,
        "cases": case_results,
    }


def _events(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Mapping):
        return []
    score = value.get("score")
    if not isinstance(score, Mapping):
        return []
    melody = score.get("melody")
    if not isinstance(melody, Sequence) or isinstance(melody, (str, bytes)):
        return []
    return [event for event in melody if isinstance(event, Mapping)]
