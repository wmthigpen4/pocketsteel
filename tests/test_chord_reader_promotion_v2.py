from __future__ import annotations

from copy import deepcopy

import pytest

from steel_guitar_rag.chord_reader.promotion import (
    calibrate_product_operating_point,
    evaluate_product_operating_point,
    evaluate_promotion,
)


def _curve_point(threshold: float, accepted: float, correct: float, total: float = 100.0) -> dict:
    return {
        "minimumConfidence": threshold,
        "acceptedDurationSeconds": accepted,
        "coverage": accepted / total,
        "productPrecision": correct / accepted if accepted else None,
        "productCorrectDurationSeconds": correct,
    }


def _report(
    *,
    split: str,
    engine: str = "factorized",
    curve: list[dict] | None = None,
    evaluated: float = 100.0,
    available: float | None = None,
) -> dict:
    available = evaluated if available is None else available
    aggregate = {
        "majorMinorWeightedRecall": 0.70 if engine == "baseline" else 0.79,
        "rootWeightedRecall": 0.70 if engine == "baseline" else 0.76,
        "boundaryF1Macro": 0.60,
        "elapsedSeconds": 5.0,
    }
    if curve is not None:
        aggregate["confidenceCoverage"] = {
            "available": available > 0,
            "evaluatedDurationSeconds": evaluated,
            "confidenceAvailableDurationSeconds": available,
            "confidenceMissingDurationSeconds": evaluated - available,
            "curve": curve,
        }
    return {
        "schemaVersion": "chord_benchmark_report_v1",
        "engine": engine,
        "split": split,
        "gitRevision": "abc123",
        "aggregate": aggregate,
        "strata": {"public": aggregate},
        "peakResidentMemoryBytes": 400_000_000,
        "tracks": [{"audioDurationSeconds": 240.0}],
    }


def _development_report() -> dict:
    return _report(
        split="dev",
        curve=[
            _curve_point(0.50, 90.0, 87.0),
            _curve_point(0.70, 80.0, 78.4),
            _curve_point(0.85, 50.0, 50.0),
        ],
    )


def _sealed_report(*, correct: float = 78.4, accepted: float = 80.0) -> dict:
    return _report(
        split="test",
        curve=[
            _curve_point(0.50, 90.0, 87.0),
            _curve_point(0.70, accepted, correct),
            _curve_point(0.85, 50.0, 50.0),
        ],
    )


def test_calibration_freezes_highest_coverage_development_threshold() -> None:
    operating_point = calibrate_product_operating_point(_development_report())

    assert operating_point["minimumConfidence"] == 0.70
    assert operating_point["targetPrecision"] == 0.98
    assert operating_point["frozen"] is True
    assert operating_point["calibration"]["productPrecision"] == pytest.approx(0.98)
    assert operating_point["calibration"]["acceptedDurationSeconds"] == 80.0
    assert operating_point["calibration"]["coverage"] == 0.80


def test_promotion_passes_product_precision_and_discloses_coverage_separately() -> None:
    operating_point = calibrate_product_operating_point(_development_report())
    baseline = _report(split="test", engine="baseline")
    challenger = _sealed_report()

    result = evaluate_promotion(baseline, challenger, operating_point=operating_point)
    gates = {gate["name"]: gate for gate in result["gates"]}

    assert result["passed"] is True
    assert result["schemaVersion"] == "chord_promotion_report_v2"
    assert gates["play-along-product-precision"]["passed"] is True
    assert gates["play-along-product-precision"]["actual"] == {
        "productPrecision": pytest.approx(0.98),
        "acceptedDurationSeconds": 80.0,
        "productCorrectDurationSeconds": 78.4,
        "coverage": 0.80,
    }
    assert result["playAlongOperatingPoint"]["coverage"] == 0.80
    assert result["playAlongOperatingPoint"]["acceptedDurationSeconds"] == 80.0
    # The pre-existing full-vocabulary scientific gates remain present.
    assert {"pooled-major-minor-wcsr", "pooled-root-wcsr", "boundary-f1"} <= set(gates)


def test_sealed_product_precision_below_98_percent_fails() -> None:
    operating_point = calibrate_product_operating_point(_development_report())

    result = evaluate_product_operating_point(
        _sealed_report(correct=77.6),
        operating_point,
    )

    assert result["passed"] is False
    assert result["productPrecision"] == pytest.approx(0.97)
    assert result["coverage"] == 0.80
    assert result["failureReasons"] == ["sealed-product-precision-below-target"]


def test_sealed_operating_point_with_zero_support_fails_closed() -> None:
    operating_point = calibrate_product_operating_point(_development_report())

    result = evaluate_product_operating_point(
        _sealed_report(correct=0.0, accepted=0.0),
        operating_point,
    )

    assert result["passed"] is False
    assert result["thresholdMatched"] is True
    assert result["supportAvailable"] is False
    assert result["acceptedDurationSeconds"] == 0.0
    assert "sealed-operating-point-zero-support" in result["failureReasons"]


def test_sealed_curve_must_contain_the_exact_frozen_threshold() -> None:
    operating_point = calibrate_product_operating_point(_development_report())
    sealed = _sealed_report()
    sealed["aggregate"]["confidenceCoverage"]["curve"][1]["minimumConfidence"] = 0.7000001

    result = evaluate_product_operating_point(sealed, operating_point)

    assert result["passed"] is False
    assert result["thresholdMatched"] is False
    assert result["supportAvailable"] is False
    assert "sealed-operating-point-threshold-missing" in result["failureReasons"]


def test_incomplete_sealed_confidence_fails_even_when_precision_is_high() -> None:
    operating_point = calibrate_product_operating_point(_development_report())
    sealed = _sealed_report(correct=80.0)
    sealed["aggregate"]["confidenceCoverage"]["confidenceAvailableDurationSeconds"] = 99.0
    sealed["aggregate"]["confidenceCoverage"]["confidenceMissingDurationSeconds"] = 1.0

    result = evaluate_product_operating_point(sealed, operating_point)

    assert result["passed"] is False
    assert result["productPrecision"] == 1.0
    assert result["confidenceComplete"] is False
    assert "confidence-incomplete" in result["failureReasons"]


def test_calibration_refuses_threshold_selection_on_sealed_test() -> None:
    sealed = deepcopy(_development_report())
    sealed["split"] = "test"

    with pytest.raises(ValueError, match="only be calibrated"):
        calibrate_product_operating_point(sealed)


def test_legacy_promotion_call_keeps_v1_contract_and_has_no_product_gate() -> None:
    baseline = _report(split="test", engine="baseline")
    challenger = _sealed_report()

    result = evaluate_promotion(baseline, challenger)

    assert result["schemaVersion"] == "chord_promotion_report_v1"
    assert result["passed"] is True
    assert "playAlongOperatingPoint" not in result
    assert not any(gate["name"].startswith("play-along-") for gate in result["gates"])
