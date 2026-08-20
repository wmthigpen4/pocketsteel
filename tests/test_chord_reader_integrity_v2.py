from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from steel_guitar_rag.chord_reader.bar_product import (
    aggregate_bar_product_confidence,
    score_bar_product_confidence,
)
from steel_guitar_rag.chord_reader.bar_promotion import (
    BAR_OPERATING_POINT_SCHEMA,
    benchmark_evaluation_hashes,
    calibrate_bar_product_operating_point,
    evaluate_bar_product_operating_point,
)
from steel_guitar_rag.chord_reader.metrics import score_segments


REAL_CORPORA = ("aam", "guitarset", "idmt_guitar")
THRESHOLD = 0.90


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _curve_point(*, eligible: int, accepted: int, correct: int) -> dict:
    return {
        "minimumConfidence": THRESHOLD,
        "eligibleBarCount": eligible,
        "acceptedBarCount": accepted,
        "correctBarCount": correct,
        "barPrecision": correct / accepted if accepted else None,
        "barCoverage": accepted / eligible,
        "hasSupport": accepted > 0,
    }


def _track_bar(*, accepted: int, correct: int, prefix: float = 0.0) -> dict:
    starts = [prefix + float(index) for index in range(100)]
    bars = [
        {
            "index": index,
            "eligible": True,
            "productConfidence": 0.95 if index < accepted else 0.50,
            "correct": index < correct,
        }
        for index in range(100)
    ]
    grid = {
        "available": True,
        "provenance": "explicit-bar-starts",
        "source": "timing",
        "barStartsSeconds": starts,
        "barCount": 100,
        "durationSeconds": prefix + 100.0,
        "gridStartSeconds": prefix,
        "excludedPrefixDurationSeconds": prefix,
        "timingProvenanceStatus": "explicit" if prefix else None,
        "prefixExclusionCertified": bool(prefix),
    }
    return {
        "schemaVersion": "chord_bar_product_confidence_v1",
        "available": True,
        "grid": grid,
        "totalBarCount": 100,
        "eligibleBarCount": 100,
        "excludedMixedBarCount": 0,
        "excludedUncoveredBarCount": 0,
        "predictionMixedBarCount": 0,
        "predictionUncoveredBarCount": 0,
        "confidenceMissingBarCount": 0,
        "scorablePredictionBarCount": 100,
        "excludedPrefixDurationSeconds": prefix,
        "barEligibility": 1.0,
        "explicitBarGrid": True,
        "bars": bars,
        "curve": [_curve_point(eligible=100, accepted=accepted, correct=correct)],
    }


def _bar_aggregate(reports: list[dict]) -> dict:
    return aggregate_bar_product_confidence(reports)


def _report(
    *,
    split: str,
    correct_per_corpus: int = 100,
    accepted_per_corpus: int = 100,
    prediction_seed: str = "candidate",
    bar_eligible_set_sha256: str | None = None,
) -> dict:
    track_bars = [
        _track_bar(
            accepted=accepted_per_corpus,
            correct=correct_per_corpus,
            prefix=8.0 if corpus == "idmt_guitar" else 0.0,
        )
        for corpus in REAL_CORPORA
    ]
    tracks = []
    for corpus, track_bar in zip(REAL_CORPORA, track_bars, strict=True):
        identifier = f"{split}-{corpus}"
        tracks.append(
            {
                "id": identifier,
                "datasetId": corpus,
                "split": split,
                "referenceSha256": _digest(f"reference:{identifier}"),
                "predictionSha256": _digest(f"prediction:{prediction_seed}:{identifier}"),
                "timingSha256": _digest(f"timing:{identifier}"),
                "audioDurationSeconds": 100.0,
                "metrics": {
                    "referenceSupportedDurationSeconds": 100.0,
                    "predictionCoveredDurationSeconds": 100.0,
                    "predictionMissingDurationSeconds": 0.0,
                    "predictionCoverage": 1.0,
                    "barProductConfidence": track_bar,
                },
            }
        )
    evaluation = benchmark_evaluation_hashes(tracks)
    evaluation["decoderConfigSha256"] = _digest("decoder")
    bar_eligible_set_sha256 = (
        evaluation["trackSetSha256"] if bar_eligible_set_sha256 is None else bar_eligible_set_sha256
    )
    aggregate_bar = _bar_aggregate(track_bars)
    aggregate = {
        "rootWeightedRecall": 0.92,
        "majorMinorWeightedRecall": 0.91,
        "detailedWeightedRecall": 0.85,
        "boundaryF1Macro": 0.85,
        "elapsedSeconds": 1.0,
        "barProductConfidence": aggregate_bar,
    }
    strata = {
        corpus: {
            "rootWeightedRecall": 0.92,
            "majorMinorWeightedRecall": 0.91,
            "detailedWeightedRecall": 0.85,
            "boundaryF1Macro": 0.85,
            "elapsedSeconds": 1 / 3,
            "barProductConfidence": _bar_aggregate([track_bar]),
        }
        for corpus, track_bar in zip(REAL_CORPORA, track_bars, strict=True)
    }
    return {
        "schemaVersion": "chord_benchmark_report_v2",
        "engine": "factorized",
        "split": split,
        "gitRevision": "a" * 40,
        "promotionEligible": True,
        "oracleTimingUsed": False,
        "peakResidentMemoryBytes": 400_000_000,
        "provenance": {
            "schemaVersion": "chord_benchmark_provenance_v2",
            "sourceTree": {
                "revision": "a" * 40,
                "dirty": False,
                "diffSha256": hashlib.sha256(b"\0STATUS\0").hexdigest(),
            },
            "model": {"sha256": _digest("model"), "bytes": 123_456},
            "cache": {
                "manifestSha256": _digest("cache-manifest"),
                "featureSpecSha256": _digest("feature-spec"),
                "splitProtocol": {
                    "outputManifestSha256": _digest("split-output"),
                    "assignmentSha256": _digest("split-assignment"),
                    "calibrationSetSha256": _digest("calibration-set"),
                    "barEligibleSetSha256": bar_eligible_set_sha256,
                },
            },
            "evaluation": evaluation,
        },
        "aggregate": aggregate,
        "strata": strata,
        "tracks": tracks,
    }


def _confirmation_identity(report: dict) -> dict[str, str]:
    evaluation = report["provenance"]["evaluation"]
    return {
        name: evaluation[name]
        for name in (
            "trackSetSha256",
            "referenceSetSha256",
            "timingSetSha256",
        )
    }


def _calibration_and_confirmation(
    *,
    confirmation_correct: int = 100,
    confirmation_accepted: int = 100,
) -> tuple[dict, dict]:
    calibration = _report(split="calibration")
    bar_eligible = calibration["provenance"]["evaluation"]["trackSetSha256"]
    confirmation = _report(
        split="confirmation",
        correct_per_corpus=confirmation_correct,
        accepted_per_corpus=confirmation_accepted,
        bar_eligible_set_sha256=bar_eligible,
    )
    return calibration, confirmation


def test_prediction_gaps_count_against_full_reference_duration() -> None:
    result = score_segments(
        [{"start": 0.0, "end": 10.0, "label": "C:maj"}],
        [
            {
                "start": 0.0,
                "end": 5.0,
                "label": "C:maj",
                "confidence": 1.0,
            }
        ],
    )

    assert result["evaluatedDurationSeconds"] == 10.0
    assert result["referenceSupportedDurationSeconds"] == 10.0
    assert result["predictionCoveredDurationSeconds"] == 5.0
    assert result["predictionMissingDurationSeconds"] == 5.0
    assert result["predictionCoverage"] == 0.5
    assert result["rootWeightedRecall"] == 0.5
    assert result["productWeightedRecall"] == 0.5
    assert result["confidenceCoverage"]["confidenceMissingDurationSeconds"] == 5.0

    empty = score_segments(
        [{"start": 0.0, "end": 10.0, "label": "C:maj"}],
        [],
    )
    assert empty["predictionCoverage"] == 0.0
    assert empty["predictionMissingDurationSeconds"] == 10.0
    assert empty["rootWeightedRecall"] == 0.0


def test_positive_explicit_grid_start_excludes_only_certified_prefix() -> None:
    reference = {
        "durationSeconds": 6.0,
        "segments": [{"start": 0.0, "end": 6.0, "label": "C:maj"}],
    }
    prediction = {
        "durationSeconds": 6.0,
        "segments": [{"start": 0.0, "end": 6.0, "label": "C:maj", "confidence": 1.0}],
    }
    timing = {
        "durationSeconds": 6.0,
        "barStartsSeconds": [2.0, 4.0],
        "gridStartSeconds": 2.0,
        "prefixExcludedSeconds": 2.0,
        "timingProvenance": {
            "barStartsSeconds": {
                "status": "explicit",
                "gridStartSeconds": 2.0,
                "prefixExcludedSeconds": 2.0,
            }
        },
    }

    result = score_bar_product_confidence(reference, prediction, timing=timing, confidence_thresholds=[0.9])

    assert result["grid"]["barStartsSeconds"] == [2.0, 4.0]
    assert result["totalBarCount"] == 2
    assert result["excludedPrefixDurationSeconds"] == 2.0
    assert result["grid"]["prefixExclusionCertified"] is True

    timing["prefixExcludedSeconds"] = 1.0
    with pytest.raises(ValueError, match="prefixExcludedSeconds"):
        score_bar_product_confidence(reference, prediction, timing=timing)


def test_v2_bar_certification_binds_provenance_and_meaningful_confirmation() -> None:
    calibration, confirmation = _calibration_and_confirmation()
    operating_point = calibrate_bar_product_operating_point(
        calibration,
        confirmation_identity=_confirmation_identity(confirmation),
    )

    assert operating_point["schemaVersion"] == BAR_OPERATING_POINT_SCHEMA
    assert operating_point["calibration"]["acceptedBarCount"] == 300
    assert operating_point["calibration"]["wilsonLowerBound95"] >= 0.98
    assert set(operating_point["calibration"]["realCorpusSupport"]) == set(REAL_CORPORA)

    result = evaluate_bar_product_operating_point(confirmation, operating_point)

    assert result["passed"] is True
    assert result["acceptedBarCount"] == 300
    assert result["barCoverage"] == 1.0
    assert result["barEligibility"] == 1.0
    assert result["excludedPrefixDurationSeconds"] == 8.0


def test_raw_98_percent_is_not_a_98_percent_confidence_claim() -> None:
    calibration = _report(
        split="calibration",
        correct_per_corpus=98,
        accepted_per_corpus=100,
    )
    confirmation = _report(
        split="confirmation",
        bar_eligible_set_sha256=calibration["provenance"]["evaluation"]["trackSetSha256"],
    )

    with pytest.raises(ValueError, match="frozen 98% literal-bar"):
        calibrate_bar_product_operating_point(
            calibration,
            confirmation_identity=_confirmation_identity(confirmation),
        )


def test_confirmation_cannot_pass_on_one_bar_per_real_corpus() -> None:
    calibration, tiny_confirmation = _calibration_and_confirmation(
        confirmation_correct=1,
        confirmation_accepted=1,
    )
    operating_point = calibrate_bar_product_operating_point(
        calibration,
        confirmation_identity=_confirmation_identity(tiny_confirmation),
    )

    result = evaluate_bar_product_operating_point(tiny_confirmation, operating_point)

    assert result["passed"] is False
    assert result["acceptedBarCount"] == 3
    assert "sealed-bar-insufficient-support" in result["failureReasons"]
    assert "sealed-bar-real-corpus-support-failed" in result["failureReasons"]


def test_confirmation_model_and_prediction_hash_tampering_fail_closed() -> None:
    calibration, confirmation = _calibration_and_confirmation()
    operating_point = calibrate_bar_product_operating_point(
        calibration,
        confirmation_identity=_confirmation_identity(confirmation),
    )

    changed_model = deepcopy(confirmation)
    changed_model["provenance"]["model"]["sha256"] = _digest("other-model")
    result = evaluate_bar_product_operating_point(changed_model, operating_point)
    assert result["passed"] is False
    assert "confirmation-model-mismatch" in result["failureReasons"]

    changed_prediction = deepcopy(confirmation)
    changed_prediction["tracks"][0]["predictionSha256"] = _digest("tampered")
    result = evaluate_bar_product_operating_point(changed_prediction, operating_point)
    assert result["passed"] is False
    assert any(reason.startswith("sealed-certification-report-invalid:") for reason in result["failureReasons"])
