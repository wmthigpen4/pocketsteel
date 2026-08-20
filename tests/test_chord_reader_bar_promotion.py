from __future__ import annotations

from copy import deepcopy

import pytest

from steel_guitar_rag.chord_reader.bar_promotion import (
    calibrate_bar_product_operating_point,
    evaluate_bar_product_operating_point,
)


def _point(threshold: float, accepted: int, correct: int, eligible: int = 1_000) -> dict:
    return {
        "minimumConfidence": threshold,
        "eligibleBarCount": eligible,
        "acceptedBarCount": accepted,
        "correctBarCount": correct,
        "barPrecision": correct / accepted if accepted else None,
        "barCoverage": accepted / eligible,
        "hasSupport": accepted > 0,
    }


def _report(*, split: str, curve: list[dict], available: bool = True) -> dict:
    return {
        "schemaVersion": "chord_benchmark_report_v1",
        "engine": "factorized",
        "split": split,
        "gitRevision": "abc123",
        "aggregate": {
            "barProductConfidence": {
                "schemaVersion": "chord_bar_product_confidence_aggregate_v1",
                "available": available,
                "partiallyAvailable": not available,
                "trackCount": 50,
                "availableTrackCount": 50 if available else 49,
                "unavailableTrackCount": 0 if available else 1,
                "eligibleBarCount": 1_000,
                "curve": curve,
            }
        },
    }


def _calibration() -> dict:
    return _report(
        split="calibration",
        curve=[
            _point(0.80, 800, 775),
            _point(0.90, 400, 392),
            _point(0.95, 200, 200),
            _point(0.98, 20, 20),
        ],
    )


def test_bar_calibration_uses_dedicated_split_and_supported_broadest_point() -> None:
    operating_point = calibrate_bar_product_operating_point(_calibration())

    assert operating_point["minimumConfidence"] == 0.90
    assert operating_point["calibration"]["acceptedBarCount"] == 400
    assert operating_point["calibration"]["barPrecision"] == 0.98
    assert operating_point["metricUnit"] == "literal accepted bars"


def test_bar_calibration_rejects_architecture_development_and_partial_grids() -> None:
    development = deepcopy(_calibration())
    development["split"] = "development"
    with pytest.raises(ValueError, match="dedicated calibration"):
        calibrate_bar_product_operating_point(development)

    partial = deepcopy(_calibration())
    partial["aggregate"]["barProductConfidence"].update(
        {"available": False, "partiallyAvailable": True, "availableTrackCount": 49,
         "unavailableTrackCount": 1}
    )
    with pytest.raises(ValueError, match="every track"):
        calibrate_bar_product_operating_point(partial)


def test_tiny_perfect_slice_cannot_define_the_operating_point() -> None:
    calibration = _report(
        split="calibration",
        curve=[_point(0.98, 4, 4), _point(0.99, 0, 0)],
    )

    with pytest.raises(ValueError, match="sufficient literal-bar support"):
        calibrate_bar_product_operating_point(calibration)


def test_sealed_bar_evaluation_applies_exact_threshold_and_reports_counts() -> None:
    operating_point = calibrate_bar_product_operating_point(_calibration())
    sealed = _report(
        split="test",
        curve=[_point(0.80, 800, 760), _point(0.90, 300, 294), _point(0.95, 100, 100)],
    )

    result = evaluate_bar_product_operating_point(sealed, operating_point)

    assert result["passed"] is True
    assert result["thresholdMatched"] is True
    assert result["barPrecision"] == 0.98
    assert result["acceptedBarCount"] == 300
    assert result["correctBarCount"] == 294
    assert result["barCoverage"] == 0.30


def test_sealed_bar_evaluation_fails_precision_and_zero_support() -> None:
    operating_point = calibrate_bar_product_operating_point(_calibration())
    low = _report(split="test", curve=[_point(0.90, 300, 293)])
    result = evaluate_bar_product_operating_point(low, operating_point)
    assert result["passed"] is False
    assert result["failureReasons"] == ["sealed-bar-precision-below-target"]

    zero = _report(split="confirmation", curve=[_point(0.90, 0, 0)])
    result = evaluate_bar_product_operating_point(zero, operating_point)
    assert result["passed"] is False
    assert "sealed-bar-zero-support" in result["failureReasons"]


def test_sealed_report_cannot_be_the_calibration_split_or_change_threshold() -> None:
    operating_point = calibrate_bar_product_operating_point(_calibration())
    calibration = _report(split="calibration", curve=[_point(0.90, 300, 300)])
    result = evaluate_bar_product_operating_point(calibration, operating_point)
    assert result["passed"] is False
    assert "sealed-report-is-not-confirmation-data" in result["failureReasons"]

    missing = _report(split="test", curve=[_point(0.900001, 300, 300)])
    result = evaluate_bar_product_operating_point(missing, operating_point)
    assert result["thresholdMatched"] is False
    assert "sealed-bar-threshold-missing" in result["failureReasons"]
