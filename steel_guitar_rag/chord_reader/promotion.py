"""Non-negotiable automated and Travis review promotion gates.

Explicit benchmark v1 reports retain their historical duration/bar behavior.
Benchmark v2 uses the v9 certification path: a literal-bar threshold selected
on calibration is applied verbatim to an identity-sealed confirmation set.
"""

from __future__ import annotations

from typing import Any, Mapping

from .bar_promotion import (
    BAR_OPERATING_POINT_SCHEMA,
    BAR_PRODUCT_PRECISION_TARGET,
    BENCHMARK_REPORT_SCHEMA,
    CERTIFICATION_MINIMUM_BAR_ELIGIBILITY,
    LEGACY_BENCHMARK_REPORT_SCHEMA,
    evaluate_bar_product_operating_point,
    validate_benchmark_v2_provenance,
)


MAJMIN_GAIN = 0.08
ROOT_GAIN = 0.05
STEEL_GAIN = 0.05
MAX_STRATUM_REGRESSION = 0.03
MAX_BOUNDARY_REGRESSION = 0.02
MAX_FOUR_MINUTE_SECONDS = 15.0
MAX_RESIDENT_MEMORY_BYTES = int(1.2 * 1024**3)
MIN_ABSOLUTE_ROOT_WEIGHTED_RECALL = 0.90
MIN_ABSOLUTE_DETAILED_WEIGHTED_RECALL = 0.80
MIN_ABSOLUTE_BOUNDARY_F1 = 0.80
PLAY_ALONG_PRODUCT_PRECISION_TARGET = 0.98
PRODUCT_OPERATING_POINT_SCHEMA = "chord_product_operating_point_v1"
PRODUCT_OPERATING_POINT_SELECTION = "highest-coverage-development-threshold-meeting-target"
_DEVELOPMENT_SPLITS = frozenset({"dev", "development", "val", "validation"})


def _gate(name: str, passed: bool, actual: Any, required: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "actual": actual, "required": required}


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _meets_precision_target(value: float, target: float) -> bool:
    return value + 1e-12 >= target


def _development_split(report: Mapping[str, Any]) -> str:
    split = str(report.get("split") or "").strip().lower()
    if split not in _DEVELOPMENT_SPLITS:
        raise ValueError("Product operating points may only be calibrated on a development/validation split.")
    return split


def _confidence_report(report: Mapping[str, Any]) -> Mapping[str, Any]:
    aggregate = report.get("aggregate")
    if not isinstance(aggregate, Mapping):
        raise ValueError("Benchmark report is missing aggregate metrics.")
    confidence = aggregate.get("confidenceCoverage")
    if not isinstance(confidence, Mapping):
        raise ValueError("Benchmark report is missing aggregate.confidenceCoverage.")
    return confidence


def _confidence_completeness(confidence: Mapping[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    evaluated = _finite_number(confidence.get("evaluatedDurationSeconds"))
    available = _finite_number(confidence.get("confidenceAvailableDurationSeconds"))
    missing = _finite_number(confidence.get("confidenceMissingDurationSeconds"))
    reasons: list[str] = []
    if confidence.get("available") is not True:
        reasons.append("confidence-unavailable")
    if evaluated is None or evaluated <= 0:
        reasons.append("evaluated-duration-missing-or-zero")
    if available is None or available < 0:
        reasons.append("confidence-available-duration-invalid")
    if missing is None or missing < -1e-9:
        reasons.append("confidence-missing-duration-invalid")
    if evaluated is not None and evaluated > 0 and available is not None and missing is not None:
        tolerance = max(1e-9, evaluated * 1e-9)
        if missing > tolerance or available < evaluated - tolerance:
            reasons.append("confidence-incomplete")
        if abs((available + missing) - evaluated) > tolerance:
            reasons.append("confidence-duration-accounting-mismatch")
    return (
        not reasons,
        {
            "evaluatedDurationSeconds": evaluated,
            "confidenceAvailableDurationSeconds": available,
            "confidenceMissingDurationSeconds": missing,
        },
        reasons,
    )


def _validated_curve_point(
    point: Mapping[str, Any],
    *,
    evaluated_duration: float,
) -> dict[str, Any]:
    threshold = _finite_number(point.get("minimumConfidence"))
    accepted = _finite_number(point.get("acceptedDurationSeconds"))
    correct = _finite_number(point.get("productCorrectDurationSeconds"))
    reported_precision = _finite_number(point.get("productPrecision"))
    if threshold is None or not 0 <= threshold <= 1:
        raise ValueError("Confidence curve contains an invalid minimumConfidence.")
    if accepted is None or accepted < 0 or accepted > evaluated_duration + 1e-9:
        raise ValueError("Confidence curve contains an invalid acceptedDurationSeconds.")
    if correct is None or correct < 0 or correct > accepted + 1e-9:
        raise ValueError("Confidence curve contains an invalid productCorrectDurationSeconds.")
    precision = correct / accepted if accepted > 0 else None
    if precision is None:
        if point.get("productPrecision") is not None:
            raise ValueError("A zero-support confidence point must have null productPrecision.")
    elif reported_precision is None or abs(reported_precision - precision) > 1e-9:
        raise ValueError("Confidence curve productPrecision does not match productCorrectDurationSeconds.")
    coverage = accepted / evaluated_duration
    reported_coverage = _finite_number(point.get("coverage"))
    if reported_coverage is None or abs(reported_coverage - coverage) > 1e-9:
        raise ValueError("Confidence curve coverage does not match accepted duration.")
    return {
        "minimumConfidence": threshold,
        "acceptedDurationSeconds": accepted,
        "productCorrectDurationSeconds": correct,
        "productPrecision": precision,
        "coverage": coverage,
    }


def calibrate_product_operating_point(
    development_report: Mapping[str, Any],
    *,
    target_precision: float = PLAY_ALONG_PRODUCT_PRECISION_TARGET,
) -> dict[str, Any]:
    """Freeze the highest-coverage development threshold meeting product precision.

    Calibration refuses sealed/test reports and incomplete confidence output.  A
    threshold with no accepted duration is never eligible, even if its precision
    field is malformed to look perfect.
    """

    if development_report.get("schemaVersion") != LEGACY_BENCHMARK_REPORT_SCHEMA:
        raise ValueError("Duration operating-point calibration is legacy-only and requires chord_benchmark_report_v1.")
    split = _development_split(development_report)
    target = _finite_number(target_precision)
    if target is None or not PLAY_ALONG_PRODUCT_PRECISION_TARGET <= target <= 1:
        raise ValueError(f"target_precision must be between {PLAY_ALONG_PRODUCT_PRECISION_TARGET:.2f} and 1.")
    confidence = _confidence_report(development_report)
    complete, durations, reasons = _confidence_completeness(confidence)
    if not complete:
        raise ValueError("Development confidence is incomplete: " + ", ".join(reasons))
    evaluated = float(durations["evaluatedDurationSeconds"])
    curve = confidence.get("curve")
    if not isinstance(curve, list) or not curve:
        raise ValueError("Development confidence curve is missing or empty.")

    points: list[dict[str, Any]] = []
    thresholds: set[float] = set()
    for raw_point in curve:
        if not isinstance(raw_point, Mapping):
            raise ValueError("Development confidence curve contains a non-object point.")
        point = _validated_curve_point(raw_point, evaluated_duration=evaluated)
        threshold = float(point["minimumConfidence"])
        if threshold in thresholds:
            raise ValueError("Development confidence curve contains duplicate thresholds.")
        thresholds.add(threshold)
        if (
            float(point["acceptedDurationSeconds"]) > 0
            and point["productPrecision"] is not None
            and _meets_precision_target(float(point["productPrecision"]), target)
        ):
            points.append(point)
    if not points:
        raise ValueError(f"No development confidence threshold has support at >= {target:.2%} product precision.")

    selected = max(
        points,
        key=lambda point: (
            float(point["coverage"]),
            float(point["acceptedDurationSeconds"]),
            -float(point["minimumConfidence"]),
        ),
    )
    return {
        "schemaVersion": PRODUCT_OPERATING_POINT_SCHEMA,
        "frozen": True,
        "metric": "productPrecision",
        "metricUnit": "duration-weighted accepted chord spans",
        "targetPrecision": target,
        "minimumConfidence": selected["minimumConfidence"],
        "selectionPolicy": PRODUCT_OPERATING_POINT_SELECTION,
        "calibration": {
            "engine": development_report.get("engine"),
            "split": split,
            "gitRevision": development_report.get("gitRevision"),
            "targetPrecision": target,
            "minimumConfidence": selected["minimumConfidence"],
            "evaluatedDurationSeconds": evaluated,
            "confidenceAvailableDurationSeconds": durations["confidenceAvailableDurationSeconds"],
            "acceptedDurationSeconds": selected["acceptedDurationSeconds"],
            "productCorrectDurationSeconds": selected["productCorrectDurationSeconds"],
            "productPrecision": selected["productPrecision"],
            "coverage": selected["coverage"],
            "curvePointCount": len(curve),
        },
    }


def evaluate_product_operating_point(
    sealed_report: Mapping[str, Any],
    operating_point: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate one frozen confidence threshold on a sealed report, failing closed."""

    reasons: list[str] = []
    if sealed_report.get("schemaVersion") != LEGACY_BENCHMARK_REPORT_SCHEMA:
        reasons.append("legacy-duration-operating-point-requires-benchmark-v1")
    target = _finite_number(operating_point.get("targetPrecision"))
    threshold = _finite_number(operating_point.get("minimumConfidence"))
    if operating_point.get("schemaVersion") != PRODUCT_OPERATING_POINT_SCHEMA:
        reasons.append("operating-point-schema-mismatch")
    if operating_point.get("frozen") is not True:
        reasons.append("operating-point-not-frozen")
    if operating_point.get("metric") != "productPrecision":
        reasons.append("operating-point-metric-mismatch")
    if operating_point.get("selectionPolicy") != PRODUCT_OPERATING_POINT_SELECTION:
        reasons.append("operating-point-selection-policy-mismatch")
    if target is None or not PLAY_ALONG_PRODUCT_PRECISION_TARGET <= target <= 1:
        reasons.append("operating-point-target-below-product-requirement")
    if threshold is None or not 0 <= threshold <= 1:
        reasons.append("operating-point-threshold-invalid")
    calibration = operating_point.get("calibration")
    if not isinstance(calibration, Mapping) or str(calibration.get("split") or "").lower() not in _DEVELOPMENT_SPLITS:
        reasons.append("operating-point-development-provenance-missing")
    elif (
        _finite_number(calibration.get("targetPrecision")) != target
        or _finite_number(calibration.get("minimumConfidence")) != threshold
    ):
        reasons.append("operating-point-calibration-mismatch")
    sealed_split = str(sealed_report.get("split") or "").strip().lower()
    if not sealed_split:
        reasons.append("sealed-split-missing")
    elif sealed_split in _DEVELOPMENT_SPLITS:
        reasons.append("sealed-report-uses-development-split")

    durations: dict[str, Any] = {
        "evaluatedDurationSeconds": None,
        "confidenceAvailableDurationSeconds": None,
        "confidenceMissingDurationSeconds": None,
    }
    confidence: Mapping[str, Any] | None = None
    try:
        confidence = _confidence_report(sealed_report)
    except ValueError:
        reasons.append("sealed-confidence-report-missing")
    confidence_complete = False
    if confidence is not None:
        confidence_complete, durations, completeness_reasons = _confidence_completeness(confidence)
        if not confidence_complete:
            reasons.extend(completeness_reasons)

    selected: dict[str, Any] | None = None
    threshold_matches = 0
    if confidence is not None and threshold is not None:
        curve = confidence.get("curve")
        if not isinstance(curve, list) or not curve:
            reasons.append("sealed-confidence-curve-missing")
        elif durations["evaluatedDurationSeconds"] is not None:
            for raw_point in curve:
                if not isinstance(raw_point, Mapping):
                    reasons.append("sealed-confidence-curve-malformed")
                    continue
                raw_threshold = _finite_number(raw_point.get("minimumConfidence"))
                if raw_threshold != threshold:
                    continue
                threshold_matches += 1
                try:
                    selected = _validated_curve_point(
                        raw_point,
                        evaluated_duration=float(durations["evaluatedDurationSeconds"]),
                    )
                except ValueError:
                    reasons.append("sealed-operating-point-malformed")
            if threshold_matches == 0:
                reasons.append("sealed-operating-point-threshold-missing")
            elif threshold_matches > 1:
                reasons.append("sealed-operating-point-threshold-duplicated")
    if selected is not None and float(selected["acceptedDurationSeconds"]) <= 0:
        reasons.append("sealed-operating-point-zero-support")

    precision = selected.get("productPrecision") if selected else None
    accepted = selected.get("acceptedDurationSeconds") if selected else 0.0
    correct = selected.get("productCorrectDurationSeconds") if selected else 0.0
    coverage = selected.get("coverage") if selected else 0.0
    precision_passed = (
        precision is not None and target is not None and _meets_precision_target(float(precision), float(target))
    )
    if selected is not None and float(selected["acceptedDurationSeconds"]) > 0 and not precision_passed:
        reasons.append("sealed-product-precision-below-target")
    reasons = list(dict.fromkeys(reasons))
    support_available = (
        selected is not None and threshold_matches == 1 and float(selected["acceptedDurationSeconds"]) > 0
    )
    return {
        "schemaVersion": "chord_product_operating_point_evaluation_v1",
        "passed": not reasons and precision_passed,
        "targetPrecision": target,
        "minimumConfidence": threshold,
        "thresholdMatched": threshold_matches == 1,
        "confidenceComplete": confidence_complete,
        "supportAvailable": support_available,
        "productPrecision": precision,
        "acceptedDurationSeconds": accepted,
        "productCorrectDurationSeconds": correct,
        "coverage": coverage,
        "evaluatedDurationSeconds": durations["evaluatedDurationSeconds"],
        "confidenceAvailableDurationSeconds": durations["confidenceAvailableDurationSeconds"],
        "confidenceMissingDurationSeconds": durations["confidenceMissingDurationSeconds"],
        "failureReasons": reasons,
    }


def _evaluate_promotion_v1(
    baseline: Mapping[str, Any],
    challenger: Mapping[str, Any],
    *,
    require_steel: bool = False,
    travis_review: Mapping[str, Any] | None = None,
    operating_point: Mapping[str, Any] | None = None,
    bar_operating_point: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if operating_point is not None and bar_operating_point is not None:
        raise ValueError("Supply either a duration or literal-bar operating point, not both.")
    base = baseline["aggregate"]
    candidate = challenger["aggregate"]
    majmin_gain = float(candidate["majorMinorWeightedRecall"]) - float(base["majorMinorWeightedRecall"])
    root_gain = float(candidate["rootWeightedRecall"]) - float(base["rootWeightedRecall"])
    boundary_change = float(candidate["boundaryF1Macro"]) - float(base["boundaryF1Macro"])
    audio_seconds = sum(float(item.get("audioDurationSeconds") or 0) for item in challenger.get("tracks", []))
    projected_four_minutes = float(candidate["elapsedSeconds"]) / max(1e-12, audio_seconds) * 240
    gates = [
        _gate("pooled-major-minor-wcsr", majmin_gain >= MAJMIN_GAIN, majmin_gain, f">= +{MAJMIN_GAIN:.2f}"),
        _gate("pooled-root-wcsr", root_gain >= ROOT_GAIN, root_gain, f">= +{ROOT_GAIN:.2f}"),
        _gate(
            "boundary-f1",
            boundary_change >= -MAX_BOUNDARY_REGRESSION,
            boundary_change,
            f">= -{MAX_BOUNDARY_REGRESSION:.2f}",
        ),
        _gate(
            "four-minute-runtime",
            projected_four_minutes <= MAX_FOUR_MINUTE_SECONDS,
            projected_four_minutes,
            f"<= {MAX_FOUR_MINUTE_SECONDS:.1f} seconds",
        ),
        _gate(
            "resident-memory",
            int(challenger.get("peakResidentMemoryBytes", 0)) <= MAX_RESIDENT_MEMORY_BYTES,
            int(challenger.get("peakResidentMemoryBytes", 0)),
            f"<= {MAX_RESIDENT_MEMORY_BYTES} bytes",
        ),
    ]
    shared = sorted(set(baseline.get("strata", {})) & set(challenger.get("strata", {})))
    regressions = {
        name: float(challenger["strata"][name]["majorMinorWeightedRecall"])
        - float(baseline["strata"][name]["majorMinorWeightedRecall"])
        for name in shared
    }
    gates.append(
        _gate(
            "no-stratum-regression",
            all(value >= -MAX_STRATUM_REGRESSION for value in regressions.values()),
            regressions,
            f"every stratum >= -{MAX_STRATUM_REGRESSION:.2f}",
        )
    )
    if require_steel:
        steel_base = baseline.get("strata", {}).get("sgf_steel_reference")
        steel_candidate = challenger.get("strata", {}).get("sgf_steel_reference")
        steel_gain = None
        if steel_base and steel_candidate:
            steel_gain = float(steel_candidate["majorMinorWeightedRecall"]) - float(
                steel_base["majorMinorWeightedRecall"]
            )
        gates.append(_gate("steel-wcsr", steel_gain is not None and steel_gain >= STEEL_GAIN, steel_gain, ">= +0.05"))
    if travis_review is not None:
        comparisons = list(travis_review.get("comparisons", []))
        preferred = sum(item.get("preferred") == "challenger" for item in comparisons)
        baseline_corrections = sum(int(item.get("baselineCorrections", 0)) for item in comparisons)
        challenger_corrections = sum(int(item.get("challengerCorrections", 0)) for item in comparisons)
        correction_reduction = 1 - challenger_corrections / max(1, baseline_corrections)
        gates.extend(
            [
                _gate("travis-preference", len(comparisons) == 10 and preferred >= 7, preferred, ">= 7 of 10"),
                _gate("travis-corrections", correction_reduction >= 0.3, correction_reduction, ">= 30% fewer"),
            ]
        )
    play_along = None
    play_along_bar = None
    if operating_point is not None:
        play_along = evaluate_product_operating_point(challenger, operating_point)
        requested_target = _finite_number(play_along["targetPrecision"])
        required_target = max(
            PLAY_ALONG_PRODUCT_PRECISION_TARGET,
            requested_target if requested_target is not None else 0.0,
        )
        operating_metrics = {
            "productPrecision": play_along["productPrecision"],
            "acceptedDurationSeconds": play_along["acceptedDurationSeconds"],
            "productCorrectDurationSeconds": play_along["productCorrectDurationSeconds"],
            "coverage": play_along["coverage"],
        }
        gates.extend(
            [
                _gate(
                    "play-along-confidence-complete",
                    play_along["confidenceComplete"],
                    {
                        "confidenceAvailableDurationSeconds": play_along["confidenceAvailableDurationSeconds"],
                        "confidenceMissingDurationSeconds": play_along["confidenceMissingDurationSeconds"],
                        "evaluatedDurationSeconds": play_along["evaluatedDurationSeconds"],
                    },
                    "confidence for 100% of evaluated duration",
                ),
                _gate(
                    "play-along-operating-point-support",
                    play_along["thresholdMatched"] and play_along["supportAvailable"],
                    {
                        "minimumConfidence": play_along["minimumConfidence"],
                        "thresholdMatched": play_along["thresholdMatched"],
                        "acceptedDurationSeconds": play_along["acceptedDurationSeconds"],
                        "coverage": play_along["coverage"],
                    },
                    "exact frozen threshold with accepted duration > 0",
                ),
                _gate(
                    "play-along-product-precision",
                    play_along["passed"],
                    operating_metrics,
                    (
                        f">= {required_target:.0%} duration-weighted product "
                        "precision at the frozen development threshold; coverage disclosed separately"
                    ),
                ),
            ]
        )
    if bar_operating_point is not None:
        play_along_bar = evaluate_bar_product_operating_point(
            challenger,
            bar_operating_point,
        )
        requested_target = _finite_number(play_along_bar["targetPrecision"])
        required_target = max(
            BAR_PRODUCT_PRECISION_TARGET,
            requested_target if requested_target is not None else 0.0,
        )
        gates.extend(
            [
                _gate(
                    "play-along-bar-evaluation-complete",
                    play_along_bar["barEvaluationComplete"],
                    {
                        "trackCount": play_along_bar["trackCount"],
                        "eligibleBarCount": play_along_bar["eligibleBarCount"],
                    },
                    "model-independent bar grids for every operating-point track",
                ),
                _gate(
                    "play-along-bar-operating-point-support",
                    (play_along_bar["thresholdMatched"] and play_along_bar["supportAvailable"]),
                    {
                        "minimumConfidence": play_along_bar["minimumConfidence"],
                        "acceptedBarCount": play_along_bar["acceptedBarCount"],
                        "barCoverage": play_along_bar["barCoverage"],
                    },
                    "exact frozen calibration threshold with at least one accepted bar",
                ),
                _gate(
                    "play-along-literal-bar-product-precision",
                    play_along_bar["passed"],
                    {
                        "barPrecision": play_along_bar["barPrecision"],
                        "acceptedBarCount": play_along_bar["acceptedBarCount"],
                        "correctBarCount": play_along_bar["correctBarCount"],
                        "barCoverage": play_along_bar["barCoverage"],
                    },
                    (
                        f">= {required_target:.0%} literal accepted-bar product precision "
                        "at the frozen calibration threshold; coverage disclosed separately"
                    ),
                ),
            ]
        )
    output = {
        "schemaVersion": (
            "chord_promotion_report_v3"
            if bar_operating_point is not None
            else "chord_promotion_report_v2"
            if operating_point is not None
            else "chord_promotion_report_v1"
        ),
        "passed": all(item["passed"] for item in gates),
        "baselineEngine": baseline.get("engine"),
        "challengerEngine": challenger.get("engine"),
        "gates": gates,
    }
    if play_along is not None:
        output["playAlongOperatingPoint"] = play_along
    if play_along_bar is not None:
        output["playAlongBarOperatingPoint"] = play_along_bar
    return output


def _prediction_coverage_disclosure(report: Mapping[str, Any]) -> dict[str, Any]:
    tracks = report.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        return {
            "complete": False,
            "referenceSupportedDurationSeconds": None,
            "predictionCoveredDurationSeconds": None,
            "predictionMissingDurationSeconds": None,
            "predictionCoverage": None,
            "failureReasons": ["prediction-coverage-tracks-missing"],
        }
    reference_duration = 0.0
    covered_duration = 0.0
    missing_duration = 0.0
    reasons: list[str] = []
    for track in tracks:
        if not isinstance(track, Mapping):
            reasons.append("prediction-coverage-track-malformed")
            continue
        metrics = track.get("metrics")
        if not isinstance(metrics, Mapping):
            reasons.append("prediction-coverage-metrics-missing")
            continue
        reference = _finite_number(metrics.get("referenceSupportedDurationSeconds"))
        covered = _finite_number(metrics.get("predictionCoveredDurationSeconds"))
        missing = _finite_number(metrics.get("predictionMissingDurationSeconds"))
        coverage = _finite_number(metrics.get("predictionCoverage"))
        if (
            reference is None
            or reference <= 0
            or covered is None
            or covered < 0
            or missing is None
            or missing < 0
            or coverage is None
            or not 0 <= coverage <= 1
        ):
            reasons.append("prediction-coverage-values-invalid")
            continue
        tolerance = max(1e-9, reference * 1e-9)
        if abs(covered + missing - reference) > tolerance or abs(coverage - covered / reference) > 1e-12:
            reasons.append("prediction-coverage-accounting-mismatch")
            continue
        reference_duration += reference
        covered_duration += covered
        missing_duration += missing
    reasons = list(dict.fromkeys(reasons))
    return {
        "complete": not reasons and reference_duration > 0,
        "referenceSupportedDurationSeconds": (reference_duration if reference_duration > 0 else None),
        "predictionCoveredDurationSeconds": (covered_duration if reference_duration > 0 else None),
        "predictionMissingDurationSeconds": (missing_duration if reference_duration > 0 else None),
        "predictionCoverage": (covered_duration / reference_duration if reference_duration > 0 else None),
        "failureReasons": reasons,
    }


def _evaluate_promotion_v9(
    baseline: Mapping[str, Any],
    challenger: Mapping[str, Any],
    *,
    require_steel: bool,
    travis_review: Mapping[str, Any] | None,
    bar_operating_point: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Evaluate a v2 challenger on exact confirmation identities and v9 floors."""

    gates: list[dict[str, Any]] = []
    baseline_provenance: Mapping[str, Any] | None = None
    challenger_provenance: Mapping[str, Any] | None = None
    provenance_errors: dict[str, str] = {}
    try:
        baseline_provenance = validate_benchmark_v2_provenance(baseline)
    except ValueError as exc:
        provenance_errors["baseline"] = str(exc)
    try:
        challenger_provenance = validate_benchmark_v2_provenance(challenger)
    except ValueError as exc:
        provenance_errors["challenger"] = str(exc)
    gates.append(
        _gate(
            "v2-certification-provenance",
            not provenance_errors,
            provenance_errors or "validated",
            "clean, recomputed v2 provenance for baseline and challenger",
        )
    )

    baseline_split = str(baseline.get("split") or "").strip().lower()
    challenger_split = str(challenger.get("split") or "").strip().lower()
    gates.append(
        _gate(
            "confirmation-split",
            baseline_split == challenger_split == "confirmation",
            {"baseline": baseline_split, "challenger": challenger_split},
            "both reports use the dedicated confirmation split",
        )
    )

    comparison_identity: dict[str, Any] = {}
    identities_match = False
    predictions_distinct = False
    if baseline_provenance is not None and challenger_provenance is not None:
        base_evaluation = baseline_provenance["evaluation"]
        candidate_evaluation = challenger_provenance["evaluation"]
        comparison_identity = {
            name: candidate_evaluation.get(name)
            for name in (
                "trackSetSha256",
                "referenceSetSha256",
                "timingSetSha256",
            )
        }
        identities_match = all(
            base_evaluation.get(name) == candidate_evaluation.get(name) for name in comparison_identity
        )
        predictions_distinct = base_evaluation.get("predictionSetSha256") != candidate_evaluation.get(
            "predictionSetSha256"
        )
    gates.extend(
        [
            _gate(
                "exact-comparison-identity",
                identities_match,
                comparison_identity,
                "identical track, reference, and timing set SHA-256 identities",
            ),
            _gate(
                "distinct-prediction-identities",
                predictions_distinct,
                (
                    {
                        "baseline": baseline_provenance["evaluation"].get("predictionSetSha256"),
                        "challenger": challenger_provenance["evaluation"].get("predictionSetSha256"),
                    }
                    if baseline_provenance is not None and challenger_provenance is not None
                    else None
                ),
                "different recomputed prediction-set SHA-256 identities",
            ),
        ]
    )

    base = baseline.get("aggregate")
    candidate = challenger.get("aggregate")
    if not isinstance(base, Mapping):
        base = {}
    if not isinstance(candidate, Mapping):
        candidate = {}
    base_majmin = _finite_number(base.get("majorMinorWeightedRecall"))
    candidate_majmin = _finite_number(candidate.get("majorMinorWeightedRecall"))
    base_root = _finite_number(base.get("rootWeightedRecall"))
    candidate_root = _finite_number(candidate.get("rootWeightedRecall"))
    candidate_detailed = _finite_number(candidate.get("detailedWeightedRecall"))
    base_boundary = _finite_number(base.get("boundaryF1Macro"))
    candidate_boundary = _finite_number(candidate.get("boundaryF1Macro"))
    majmin_gain = candidate_majmin - base_majmin if candidate_majmin is not None and base_majmin is not None else None
    root_gain = candidate_root - base_root if candidate_root is not None and base_root is not None else None
    boundary_change = (
        candidate_boundary - base_boundary if candidate_boundary is not None and base_boundary is not None else None
    )
    gates.extend(
        [
            _gate(
                "pooled-major-minor-wcsr",
                majmin_gain is not None and majmin_gain >= MAJMIN_GAIN,
                majmin_gain,
                f">= +{MAJMIN_GAIN:.2f}",
            ),
            _gate(
                "pooled-root-wcsr",
                root_gain is not None and root_gain >= ROOT_GAIN,
                root_gain,
                f">= +{ROOT_GAIN:.2f}",
            ),
            _gate(
                "boundary-f1-regression",
                boundary_change is not None and boundary_change >= -MAX_BOUNDARY_REGRESSION,
                boundary_change,
                f">= -{MAX_BOUNDARY_REGRESSION:.2f}",
            ),
            _gate(
                "absolute-root-wcsr",
                candidate_root is not None and candidate_root >= MIN_ABSOLUTE_ROOT_WEIGHTED_RECALL,
                candidate_root,
                f">= {MIN_ABSOLUTE_ROOT_WEIGHTED_RECALL:.2f}",
            ),
            _gate(
                "absolute-detailed-wcsr",
                candidate_detailed is not None and candidate_detailed >= MIN_ABSOLUTE_DETAILED_WEIGHTED_RECALL,
                candidate_detailed,
                f">= {MIN_ABSOLUTE_DETAILED_WEIGHTED_RECALL:.2f}",
            ),
            _gate(
                "absolute-boundary-f1",
                candidate_boundary is not None and candidate_boundary >= MIN_ABSOLUTE_BOUNDARY_F1,
                candidate_boundary,
                f">= {MIN_ABSOLUTE_BOUNDARY_F1:.2f}",
            ),
        ]
    )

    base_strata = baseline.get("strata")
    candidate_strata = challenger.get("strata")
    base_strata = base_strata if isinstance(base_strata, Mapping) else {}
    candidate_strata = candidate_strata if isinstance(candidate_strata, Mapping) else {}
    shared = sorted(set(base_strata) & set(candidate_strata))
    regressions: dict[str, float | None] = {}
    for name in shared:
        base_value = (
            _finite_number(base_strata[name].get("majorMinorWeightedRecall"))
            if isinstance(base_strata[name], Mapping)
            else None
        )
        candidate_value = (
            _finite_number(candidate_strata[name].get("majorMinorWeightedRecall"))
            if isinstance(candidate_strata[name], Mapping)
            else None
        )
        regressions[str(name)] = (
            candidate_value - base_value if candidate_value is not None and base_value is not None else None
        )
    gates.append(
        _gate(
            "no-stratum-regression",
            bool(regressions)
            and all(value is not None and value >= -MAX_STRATUM_REGRESSION for value in regressions.values()),
            regressions,
            f"every shared stratum >= -{MAX_STRATUM_REGRESSION:.2f}",
        )
    )

    audio_seconds = sum(
        float(item.get("audioDurationSeconds") or 0)
        for item in challenger.get("tracks", [])
        if isinstance(item, Mapping)
    )
    elapsed = _finite_number(candidate.get("elapsedSeconds"))
    projected_four_minutes = (
        elapsed / audio_seconds * 240 if elapsed is not None and elapsed >= 0 and audio_seconds > 0 else None
    )
    peak_memory = challenger.get("peakResidentMemoryBytes")
    peak_memory = peak_memory if isinstance(peak_memory, int) and not isinstance(peak_memory, bool) else None
    gates.extend(
        [
            _gate(
                "four-minute-runtime",
                projected_four_minutes is not None and projected_four_minutes <= MAX_FOUR_MINUTE_SECONDS,
                projected_four_minutes,
                f"<= {MAX_FOUR_MINUTE_SECONDS:.1f} seconds",
            ),
            _gate(
                "resident-memory",
                peak_memory is not None and peak_memory <= MAX_RESIDENT_MEMORY_BYTES,
                peak_memory,
                f"<= {MAX_RESIDENT_MEMORY_BYTES} bytes",
            ),
        ]
    )

    coverage = _prediction_coverage_disclosure(challenger)
    gates.append(
        _gate(
            "prediction-coverage-accounting",
            coverage["complete"],
            coverage,
            "full reference-duration prediction coverage/missing-time accounting",
        )
    )

    bar_report = candidate.get("barProductConfidence")
    bar_eligibility = _finite_number(bar_report.get("barEligibility")) if isinstance(bar_report, Mapping) else None
    gates.append(
        _gate(
            "absolute-bar-eligibility",
            bar_eligibility is not None and bar_eligibility >= CERTIFICATION_MINIMUM_BAR_ELIGIBILITY,
            bar_eligibility,
            f">= {CERTIFICATION_MINIMUM_BAR_ELIGIBILITY:.2f}",
        )
    )

    play_along_bar: Mapping[str, Any] | None = None
    strict_bar_schema = (
        isinstance(bar_operating_point, Mapping)
        and bar_operating_point.get("schemaVersion") == BAR_OPERATING_POINT_SCHEMA
    )
    gates.append(
        _gate(
            "v2-bar-operating-point-required",
            strict_bar_schema,
            (bar_operating_point.get("schemaVersion") if isinstance(bar_operating_point, Mapping) else None),
            BAR_OPERATING_POINT_SCHEMA,
        )
    )
    if isinstance(bar_operating_point, Mapping):
        play_along_bar = evaluate_bar_product_operating_point(challenger, bar_operating_point)
        gates.extend(
            [
                _gate(
                    "play-along-explicit-bar-evaluation",
                    bool(play_along_bar.get("barEvaluationComplete"))
                    and bool(play_along_bar.get("explicitBarGridOnly")),
                    {
                        "trackCount": play_along_bar.get("trackCount"),
                        "eligibleBarCount": play_along_bar.get("eligibleBarCount"),
                        "totalBarCount": play_along_bar.get("totalBarCount"),
                        "excludedPrefixDurationSeconds": play_along_bar.get("excludedPrefixDurationSeconds"),
                    },
                    "explicit reference bar grids for every confirmation track",
                ),
                _gate(
                    "play-along-bar-operating-point-support",
                    bool(play_along_bar.get("thresholdMatched")) and bool(play_along_bar.get("supportAvailable")),
                    {
                        "minimumConfidence": play_along_bar.get("minimumConfidence"),
                        "acceptedBarCount": play_along_bar.get("acceptedBarCount"),
                        "barCoverage": play_along_bar.get("barCoverage"),
                    },
                    "exact frozen threshold, >=150 accepted bars, and >=50% bar coverage",
                ),
                _gate(
                    "play-along-literal-bar-product-precision",
                    bool(play_along_bar.get("passed")),
                    {
                        "barPrecision": play_along_bar.get("barPrecision"),
                        "wilsonLowerBound95": play_along_bar.get("wilsonLowerBound95"),
                        "acceptedBarCount": play_along_bar.get("acceptedBarCount"),
                        "correctBarCount": play_along_bar.get("correctBarCount"),
                        "barCoverage": play_along_bar.get("barCoverage"),
                        "realCorpusSupport": play_along_bar.get("realCorpusSupport"),
                    },
                    ">=98% one-sided 95% Wilson lower bound plus frozen real-corpus support",
                ),
            ]
        )

    if require_steel:
        steel_base = base_strata.get("sgf_steel_reference")
        steel_candidate = candidate_strata.get("sgf_steel_reference")
        steel_base_value = (
            _finite_number(steel_base.get("majorMinorWeightedRecall")) if isinstance(steel_base, Mapping) else None
        )
        steel_candidate_value = (
            _finite_number(steel_candidate.get("majorMinorWeightedRecall"))
            if isinstance(steel_candidate, Mapping)
            else None
        )
        steel_gain = (
            steel_candidate_value - steel_base_value
            if steel_candidate_value is not None and steel_base_value is not None
            else None
        )
        gates.append(
            _gate(
                "steel-wcsr",
                steel_gain is not None and steel_gain >= STEEL_GAIN,
                steel_gain,
                f">= +{STEEL_GAIN:.2f}",
            )
        )
    if travis_review is not None:
        comparisons = list(travis_review.get("comparisons", []))
        preferred = sum(item.get("preferred") == "challenger" for item in comparisons)
        baseline_corrections = sum(int(item.get("baselineCorrections", 0)) for item in comparisons)
        challenger_corrections = sum(int(item.get("challengerCorrections", 0)) for item in comparisons)
        correction_reduction = 1 - challenger_corrections / max(1, baseline_corrections)
        gates.extend(
            [
                _gate(
                    "travis-preference",
                    len(comparisons) == 10 and preferred >= 7,
                    preferred,
                    ">= 7 of 10",
                ),
                _gate(
                    "travis-corrections",
                    correction_reduction >= 0.3,
                    correction_reduction,
                    ">= 30% fewer",
                ),
            ]
        )

    output: dict[str, Any] = {
        "schemaVersion": "chord_promotion_report_v9",
        "passed": all(item["passed"] for item in gates),
        "baselineEngine": baseline.get("engine"),
        "challengerEngine": challenger.get("engine"),
        "comparisonIdentity": comparison_identity,
        "absoluteMetrics": {
            "rootWeightedRecall": candidate_root,
            "detailedWeightedRecall": candidate_detailed,
            "boundaryF1Macro": candidate_boundary,
            "barEligibility": bar_eligibility,
        },
        "predictionCoverage": coverage,
        "gates": gates,
    }
    if play_along_bar is not None:
        output["playAlongBarOperatingPoint"] = play_along_bar
    return output


def evaluate_promotion(
    baseline: Mapping[str, Any],
    challenger: Mapping[str, Any],
    *,
    require_steel: bool = False,
    travis_review: Mapping[str, Any] | None = None,
    operating_point: Mapping[str, Any] | None = None,
    bar_operating_point: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch promotion only on explicit benchmark schemas."""

    baseline_schema = baseline.get("schemaVersion")
    challenger_schema = challenger.get("schemaVersion")
    if baseline_schema == LEGACY_BENCHMARK_REPORT_SCHEMA and challenger_schema == LEGACY_BENCHMARK_REPORT_SCHEMA:
        return _evaluate_promotion_v1(
            baseline,
            challenger,
            require_steel=require_steel,
            travis_review=travis_review,
            operating_point=operating_point,
            bar_operating_point=bar_operating_point,
        )
    if baseline_schema != BENCHMARK_REPORT_SCHEMA or challenger_schema != BENCHMARK_REPORT_SCHEMA:
        raise ValueError("Promotion requires both reports to use the same explicit benchmark v1 or v2 schema.")
    if operating_point is not None:
        raise ValueError(
            "Benchmark v2/v9 promotion requires literal-bar certification; duration operating points are legacy-only."
        )
    return _evaluate_promotion_v9(
        baseline,
        challenger,
        require_steel=require_steel,
        travis_review=travis_review,
        bar_operating_point=bar_operating_point,
    )
