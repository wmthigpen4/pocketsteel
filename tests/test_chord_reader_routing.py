from __future__ import annotations

import math

import numpy as np
import pytest

from steel_guitar_rag.chord_reader.routing import (
    ROUTER_FEATURE_NAMES,
    FactorizedEvidence,
    blend_factorized_evidence,
    continuous_ood_shrink,
    manifest_sha256,
    router_summary_features,
    router_utility,
    router_weight,
    routing_delta,
    train_dev_router,
)


def _evidence(*, alternate: bool = False) -> FactorizedEvidence:
    root = np.asarray(
        [[0.05, 0.90, 0.05], [0.05, 0.90, 0.05], [0.05, 0.05, 0.90]],
        dtype=np.float64,
    )
    mode = np.asarray(
        [[0.05, 0.90, 0.05], [0.05, 0.90, 0.05], [0.05, 0.90, 0.05]],
        dtype=np.float64,
    )
    quality = np.asarray(
        [[0.8, 0.2], [0.8, 0.2], [0.8, 0.2]],
        dtype=np.float64,
    )
    bass = np.asarray(
        [[0.9, 0.1, 0.0], [0.9, 0.1, 0.0], [0.9, 0.0, 0.1]],
        dtype=np.float64,
    )
    boundary = np.asarray([0.05, 0.2, 0.8], dtype=np.float64)
    if alternate:
        root = root[:, [0, 2, 1]]
        mode = mode[:, [0, 2, 1]]
        quality = quality[:, ::-1]
        bass = bass[:, [0, 2, 1]]
        boundary = 1 - boundary
    return FactorizedEvidence(
        root=root,
        mode=mode,
        quality=quality,
        bass=bass,
        boundary=boundary,
    )


def _metrics(value: float, *, edit_rate: float = 0.2) -> dict[str, float]:
    return {
        "rootWeightedRecall": value,
        "majorMinorWeightedRecall": value,
        "detailedWeightedRecall": value,
        "boundaryF1Macro": value,
        "sequenceEditRateMacro": edit_rate,
    }


def _router_features(marker: float = 0.0) -> dict[str, float]:
    return {name: marker + index / 100 for index, name in enumerate(ROUTER_FEATURE_NAMES)}


def test_factorized_evidence_normalizes_logits_and_rejects_bad_rows() -> None:
    evidence = FactorizedEvidence.from_logits(
        root=np.asarray([[2.0, 1.0], [0.0, 3.0]]),
        mode=np.asarray([[1.0, 0.0], [2.0, 1.0]]),
        quality=np.asarray([[0.0, 0.0], [1.0, 1.0]]),
        bass=np.asarray([[1.0, 2.0], [3.0, 0.0]]),
        boundary=np.asarray([0.0, 2.0]),
    )
    assert np.allclose(evidence.root.sum(axis=1), 1)
    assert np.allclose(evidence.mode.sum(axis=1), 1)
    assert np.allclose(evidence.quality.sum(axis=1), 1)
    assert np.allclose(evidence.bass.sum(axis=1), 1)
    assert evidence.boundary.tolist() == pytest.approx([0.5, 0.8807970779])

    with pytest.raises(ValueError, match="sum to one"):
        FactorizedEvidence(
            root=[[0.2, 0.2]],
            mode=[[1.0]],
            quality=[[1.0]],
            bass=[[1.0]],
            boundary=[0.5],
        )


def test_soft_blend_is_endpoint_exact_and_identical_evidence_is_invariant() -> None:
    expanded = _evidence()
    conservative = _evidence(alternate=True)

    assert blend_factorized_evidence(expanded, conservative, 0.0) is expanded
    assert blend_factorized_evidence(expanded, conservative, 1.0) is conservative
    assert blend_factorized_evidence(expanded, expanded, 0.37) is not expanded
    invariant = blend_factorized_evidence(expanded, expanded, 0.37)
    for name in ("root", "mode", "quality", "bass", "boundary"):
        assert np.array_equal(getattr(invariant, name), getattr(expanded, name))


def test_quality_only_blend_cannot_change_root_or_other_factor_paths() -> None:
    expanded = _evidence()
    conservative = _evidence(alternate=True)
    blended = blend_factorized_evidence(
        expanded,
        conservative,
        0.75,
        components=("quality",),
    )

    assert blended.root is expanded.root
    assert blended.mode is expanded.mode
    assert blended.bass is expanded.bass
    assert blended.boundary is expanded.boundary
    assert not np.array_equal(blended.quality, expanded.quality)
    assert np.array_equal(blended.root.argmax(axis=1), expanded.root.argmax(axis=1))


def test_router_failures_default_to_zero_and_ood_shrink_is_continuous() -> None:
    assert router_weight(None, None) == 0
    assert continuous_ood_shrink(float("nan"), 0) == 0
    assert continuous_ood_shrink(0.8, float("nan")) == 0
    assert continuous_ood_shrink(0.8, 0, strength=0.5) == pytest.approx(0.8)
    assert continuous_ood_shrink(0.8, 1, strength=0.5) == pytest.approx(0.8 * math.exp(-0.5))
    assert continuous_ood_shrink(0.8, 1.001, strength=0.5) < continuous_ood_shrink(
        0.8, 1, strength=0.5
    )


def test_router_utility_and_delta_use_the_audit_locked_formula() -> None:
    metrics = {
        "root": 0.8,
        "majorMinor": 0.7,
        "detailed": 0.6,
        "boundaryF1": 0.5,
        "editRate": 0.4,
    }
    assert router_utility(metrics) == pytest.approx(0.665)
    assert routing_delta(_metrics(0.4), _metrics(0.7)) == pytest.approx(0.285)
    capped = dict(metrics, editRate=5.0)
    assert router_utility(capped) == pytest.approx(0.635)


def test_router_summary_exposes_texture_disagreement_change_rhythm_and_ood() -> None:
    expanded = _evidence()
    conservative = _evidence(alternate=True)
    summary = router_summary_features(
        [index / 10 for index in range(14)],
        expanded,
        conservative,
        beat_confidence=0.81,
        downbeat_confidence=0.62,
        ood_distance=1.4,
    )

    assert tuple(summary) == ROUTER_FEATURE_NAMES
    assert summary["rootDisagreementRate"] == 1
    assert summary["modeDisagreementRate"] == 1
    assert summary["expandedChangeRate"] == pytest.approx(0.5)
    assert summary["boundaryDisagreement"] > 0
    assert summary["beatConfidence"] == 0.81
    assert summary["downbeatConfidence"] == 0.62
    assert summary["oodDistance"] == 1.4


def test_dev_router_trains_composition_grouped_oof_calibration_artifact() -> None:
    rows = []
    for index in range(8):
        conservative_wins = index >= 4
        rows.append(
            {
                "compositionId": f"composition-{index}",
                "split": "dev",
                "features": _router_features(1.0 if conservative_wins else -1.0),
                "expandedMetrics": _metrics(0.45 if conservative_wins else 0.8),
                "conservativeMetrics": _metrics(0.8 if conservative_wins else 0.45),
            }
        )

    artifact = train_dev_router(
        rows,
        manifest_hashes={"development": "a" * 64},
        folds=4,
        iterations=160,
        reliability_bin_count=5,
    )

    assert artifact["schemaVersion"] == "chord_soft_router_v1"
    assert artifact["decisionPolicy"] == "continuous-soft-blend"
    assert artifact["hardThreshold"] is None
    assert artifact["utility"]["sampleWeight"] == "abs(delta)"
    assert artifact["development"]["grouping"] == "compositionId"
    assert artifact["development"]["foldCount"] == 4
    assignments = artifact["development"]["foldAssignments"]
    assert len({item["compositionId"] for item in assignments}) == 8
    assert len(artifact["development"]["outOfFold"]["reliabilityBins"]) == 5
    assert artifact["development"]["outOfFold"]["weightedLogLoss"] >= 0
    assert 0 <= router_weight(_router_features(1.0), artifact) <= 1

    broken = dict(_router_features(1.0))
    del broken[ROUTER_FEATURE_NAMES[0]]
    assert router_weight(broken, artifact) == 0
    broken = _router_features(1.0)
    broken[ROUTER_FEATURE_NAMES[0]] = float("nan")
    assert router_weight(broken, artifact) == 0


def test_dev_router_rejects_test_rows_and_pins_canonical_manifest_hashes() -> None:
    row = {
        "compositionId": "sealed-song",
        "split": "test",
        "features": _router_features(),
        "expandedMetrics": _metrics(0.4),
        "conservativeMetrics": _metrics(0.6),
    }
    with pytest.raises(ValueError, match="development-only"):
        train_dev_router(
            [row, dict(row, compositionId="other")],
            manifest_hashes={"sealed": "b" * 64},
            folds=2,
            iterations=1,
        )

    left = {"tracks": [{"id": "a", "split": "dev"}]}
    right = {"tracks": [{"split": "dev", "id": "a"}]}
    assert manifest_sha256(left) == manifest_sha256(right)
