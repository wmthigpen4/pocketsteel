from __future__ import annotations

from copy import deepcopy

import pytest

from steel_guitar_rag.chord_reader.bar_promotion import (
    benchmark_evaluation_hashes,
    calibrate_bar_product_operating_point,
)
from steel_guitar_rag.chord_reader.promotion import evaluate_promotion

from test_chord_reader_integrity_v2 import (
    REAL_CORPORA,
    _calibration_and_confirmation,
    _confirmation_identity,
    _digest,
)


def _baseline_for(confirmation: dict) -> dict:
    baseline = deepcopy(confirmation)
    baseline["engine"] = "legacy-baseline"
    baseline["aggregate"].update(
        {
            "rootWeightedRecall": 0.83,
            "majorMinorWeightedRecall": 0.82,
            "detailedWeightedRecall": 0.75,
            "boundaryF1Macro": 0.84,
        }
    )
    for corpus in REAL_CORPORA:
        baseline["strata"][corpus].update(
            {
                "rootWeightedRecall": 0.83,
                "majorMinorWeightedRecall": 0.82,
                "detailedWeightedRecall": 0.75,
                "boundaryF1Macro": 0.84,
            }
        )
    for track in baseline["tracks"]:
        track["predictionSha256"] = _digest(f"baseline:{track['id']}")
    recomputed = benchmark_evaluation_hashes(baseline["tracks"])
    baseline["provenance"]["evaluation"].update(recomputed)
    return baseline


def _operating_point() -> tuple[dict, dict, dict]:
    calibration, confirmation = _calibration_and_confirmation()
    baseline = _baseline_for(confirmation)
    operating_point = calibrate_bar_product_operating_point(
        calibration,
        confirmation_identity=_confirmation_identity(confirmation),
    )
    return baseline, confirmation, operating_point


def test_v9_promotion_requires_and_discloses_all_world_class_gates() -> None:
    baseline, challenger, operating_point = _operating_point()

    result = evaluate_promotion(
        baseline,
        challenger,
        bar_operating_point=operating_point,
    )
    gates = {gate["name"]: gate for gate in result["gates"]}

    assert result["schemaVersion"] == "chord_promotion_report_v9"
    assert result["passed"] is True
    assert result["absoluteMetrics"] == {
        "rootWeightedRecall": 0.92,
        "detailedWeightedRecall": 0.85,
        "boundaryF1Macro": 0.85,
        "barEligibility": 1.0,
    }
    assert result["predictionCoverage"]["predictionCoverage"] == 1.0
    assert gates["exact-comparison-identity"]["passed"] is True
    assert gates["distinct-prediction-identities"]["passed"] is True
    assert gates["absolute-root-wcsr"]["passed"] is True
    assert gates["absolute-detailed-wcsr"]["passed"] is True
    assert gates["absolute-boundary-f1"]["passed"] is True
    assert gates["absolute-bar-eligibility"]["passed"] is True
    assert gates["play-along-literal-bar-product-precision"]["passed"] is True
    assert result["playAlongBarOperatingPoint"]["wilsonLowerBound95"] >= 0.98


def test_v9_without_bar_operating_point_fails_closed() -> None:
    baseline, challenger, unused_operating_point = _operating_point()
    assert unused_operating_point["frozen"] is True

    result = evaluate_promotion(baseline, challenger)
    gates = {gate["name"]: gate for gate in result["gates"]}

    assert result["passed"] is False
    assert gates["v2-bar-operating-point-required"]["passed"] is False
    assert "playAlongBarOperatingPoint" not in result


def test_v9_rejects_noncomparable_confirmation_reference_identity() -> None:
    baseline, challenger, operating_point = _operating_point()
    baseline["tracks"][0]["referenceSha256"] = _digest("different-reference")
    baseline["provenance"]["evaluation"].update(benchmark_evaluation_hashes(baseline["tracks"]))

    result = evaluate_promotion(
        baseline,
        challenger,
        bar_operating_point=operating_point,
    )
    gates = {gate["name"]: gate for gate in result["gates"]}

    assert result["passed"] is False
    assert gates["exact-comparison-identity"]["passed"] is False


def test_v9_absolute_floor_and_duration_operating_point_fail_closed() -> None:
    baseline, challenger, operating_point = _operating_point()
    challenger["aggregate"]["detailedWeightedRecall"] = 0.79

    result = evaluate_promotion(
        baseline,
        challenger,
        bar_operating_point=operating_point,
    )
    gates = {gate["name"]: gate for gate in result["gates"]}
    assert result["passed"] is False
    assert gates["absolute-detailed-wcsr"]["passed"] is False

    with pytest.raises(ValueError, match="duration operating points are legacy-only"):
        evaluate_promotion(
            baseline,
            challenger,
            operating_point={"schemaVersion": "chord_product_operating_point_v1"},
        )


def test_promotion_never_silently_mixes_legacy_and_v2_reports() -> None:
    baseline, challenger, operating_point = _operating_point()
    baseline["schemaVersion"] = "chord_benchmark_report_v1"

    with pytest.raises(ValueError, match="same explicit benchmark"):
        evaluate_promotion(
            baseline,
            challenger,
            bar_operating_point=operating_point,
        )
