from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_bounded_consensus_development.py"
SPEC = importlib.util.spec_from_file_location("bounded_consensus", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_candidate_contract_is_exactly_three_and_monotonic() -> None:
    core = ("one", "two")
    names = [MODULE._candidate_features(core, candidate) for candidate in MODULE.CANDIDATES]
    assert MODULE.CANDIDATES == (
        "engine-only",
        "engine-plus-btc",
        "engine-plus-btc-plus-nnls",
    )
    assert MODULE.MAX_CANDIDATE_FITS == 3
    assert names[0] == core
    assert names[1][:2] == core
    assert names[2][: len(names[1])] == names[1]
    assert len(names[0]) < len(names[1]) < len(names[2])
    assert MODULE.CORRECTION_CANDIDATES == (
        "engine-unchanged",
        "fixed-checker-consensus",
        "one-fit-source-selector",
    )
    assert MODULE.CORRECTION_MAX_FITS == 1


def test_retained_confidence_contract_matches_frozen_feature_lists() -> None:
    path = Path(__file__).resolve().parents[1] / "chord_reader/models/chord-consensus-confidence-v1.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract["status"] == "retained-development-confidence-features"
    assert contract["retainedFeatures"]["btc"] == list(MODULE.BTC_FEATURES)
    assert contract["retainedFeatures"]["nnlsChroma"] == list(MODULE.NNLS_FEATURES)
    assert contract["retainedFeatures"]["consensus"] == list(MODULE.CONSENSUS_FEATURES)
    assert contract["retainedFeatures"]["totalFeatureCount"] == 64
    assert contract["policy"] == {
        "confidenceOnly": True,
        "mayAbstain": True,
        "mayPrioritizeHumanReview": True,
        "mayRewriteChordLabels": False,
        "productionEnabled": False,
        "localhostProofEnabled": False,
        "promotionEligible": False,
        "calibrationMayOpen": False,
        "confirmationMayOpen": False,
        "newEvaluationAuthorized": False,
    }


def test_nnls_chroma_evidence_recovers_clear_major_and_minor_templates() -> None:
    features = np.zeros((2, 61), dtype=np.float32)
    features[0, [0, 4, 7]] = [1.0, 0.75, 0.6]
    features[0, [24, 28, 31]] = [1.0, 0.75, 0.6]
    features[1, [9, 0, 4]] = [1.0, 0.75, 0.6]
    features[1, [33, 24, 28]] = [1.0, 0.75, 0.6]
    evidence = MODULE.nnls_chroma_evidence(features)
    assert evidence["products"] == ["C", "Am"]
    assert all(value > 0.99 for value in evidence["confidences"])


def test_group_split_is_deterministic_and_holds_out_each_dataset() -> None:
    examples = [
        {"confidenceGroupId": f"composition:{dataset}:{index}"}
        for dataset in ("aam", "guitarset", "idmt_guitar")
        for index in range(5)
    ]
    first = MODULE._split_groups(examples)
    second = MODULE._split_groups(list(reversed(examples)))
    assert first == second
    for dataset in ("aam", "guitarset", "idmt_guitar"):
        roles = {role for group, role in first.items() if group.startswith(f"composition:{dataset}:")}
        assert roles == {"fit", "evaluation"}


def test_sealed_feature_binding_uses_track_identity_not_historical_role() -> None:
    sealed = {
        "tracks": [
            {"id": "development-example", "split": "train", "path": "/cache/example.npz"},
            {"id": "other", "split": "development", "path": "/cache/other.npz"},
        ]
    }
    paths = MODULE._sealed_feature_paths_by_id(sealed)
    assert paths["development-example"] == Path("/cache/example.npz")


def test_explicit_null_feature_is_forwarded_to_the_frozen_imputer() -> None:
    assert np.isnan(MODULE._numeric_feature_value(None))
    assert MODULE._numeric_feature_value(0) == 0.0
    assert MODULE._numeric_feature_value(0.25) == 0.25


def test_reference_bar_canonicalizes_enharmonic_products() -> None:
    reference = MODULE._reference_bar(
        [
            {"start": 0.0, "end": 0.8, "label": "Gb:min"},
            {"start": 0.8, "end": 1.0, "label": "A:maj"},
        ],
        0.0,
        1.0,
    )
    assert reference == {"product": "F#m", "coverage": 1.0, "dominance": 0.8}
    assert MODULE._canonical_product("Ab:min") == "G#m"


def test_correction_metrics_count_help_and_harm_without_hiding_full_coverage() -> None:
    engine = np.asarray(["C", "D", "E", "F"])
    reference = np.asarray(["C", "G", "E", "A"])
    prediction = np.asarray(["C", "G", "A", "G"])
    metrics = MODULE._correction_metrics(
        predictions=prediction,
        references=reference,
        engine=engine,
        confidence=np.asarray([0.99, 0.99, 0.99, 0.2]),
        selectively_eligible=np.asarray([True, True, True, False]),
    )
    assert metrics["fullCoverageCorrectCount"] == 2
    assert metrics["helpfulCorrectionCount"] == 1
    assert metrics["harmfulCorrectionCount"] == 1
    assert metrics["changedWrongToDifferentWrongCount"] == 1
    assert metrics["netCorrectGain"] == 0
    assert metrics["primaryOperatingPoint"] == {
        "minimumConfidence": 0.98,
        "acceptedCount": 3,
        "correctCount": 2,
        "precision": 2 / 3,
        "coverage": 0.75,
    }


def test_bar_evidence_features_capture_checker_consensus() -> None:
    example = {
        "barSummary": {
            "start": 0.0,
            "end": 1.0,
            "predictionProduct": "C",
        }
    }
    btc = {"segments": [{"start": 0.0, "end": 1.0, "productLabel": "G", "confidence": 0.9}]}
    nnls = {
        "products": ["G"] * 10,
        "confidences": [0.8] * 10,
        "margins": [0.6] * 10,
    }
    values = MODULE._evidence_features(example, btc, nnls)
    assert values["btcRootAgreement"] == 0.0
    assert values["nnlsRootAgreement"] == 0.0
    assert values["btcNnlsRootAgreement"] == 1.0
    assert values["checkersAgainstEngineRootShare"] == 1.0
