from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from steel_guitar_rag.chord_reader import bar_examples
from steel_guitar_rag.chord_reader import half_bar_stage1 as stage1
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.bar_uncertainty import EXPLICIT_BAR_GRID_SCHEMA


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _rehash(value: dict[str, Any], field: str) -> None:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})


def _timing(
    starts: list[float],
    duration: float,
    *,
    prefix: float | None = None,
) -> dict[str, Any]:
    source_contract_sha256 = _digest("runtime-analyzer")
    bar_provenance: dict[str, Any] = {
        "status": "explicit",
        "sourceContractSha256": source_contract_sha256,
    }
    timing: dict[str, Any] = {
        "schemaVersion": EXPLICIT_BAR_GRID_SCHEMA,
        "durationSeconds": duration,
        "barStartsSeconds": starts,
        "contractSha256": _digest("runtime-timing-contract"),
        "timingProvenance": {"barStartsSeconds": bar_provenance},
    }
    if prefix is not None:
        timing["prefixExcludedSeconds"] = prefix
        bar_provenance["prefixExcludedSeconds"] = prefix
    return timing


def _construction(
    starts: list[float],
    duration: float,
    *,
    prefix: float | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    timing = _timing(starts, duration, prefix=prefix)
    return stage1.construct_half_bar_cells(
        timing,
        source_timing_file_sha256=_digest("runtime-timing-file"),
        manifest_timing_sha256=canonical_sha256(timing),
        manifest_timing_contract_sha256=timing["contractSha256"],
        analyzer_timing_source_contract_sha256=timing["timingProvenance"]["barStartsSeconds"]["sourceContractSha256"],
    )


def _prediction(duration: float, segments: list[tuple[float, float, str]]) -> dict[str, Any]:
    return {
        "id": "synthetic-track",
        "durationSeconds": duration,
        "segments": [
            {"start": start, "end": end, "label": product, "productLabel": product} for start, end, product in segments
        ],
        "predictionCoreSha256": _digest("prediction-core"),
        "uncertaintySha256": _digest("prediction-uncertainty"),
    }


def _summary_cell(
    cell: dict[str, Any],
    product: str | None,
    covered: float,
    product_duration: float,
) -> dict[str, Any]:
    duration = cell["durationMilliseconds"] / 1000
    return {
        "cellIndex": cell["cellIndex"],
        "startMilliseconds": cell["startMilliseconds"],
        "endMilliseconds": cell["endMilliseconds"],
        "durationMilliseconds": cell["durationMilliseconds"],
        "predictionProduct": product,
        "predictionCoveredDurationSeconds": covered,
        "predictionProductDurationSeconds": product_duration,
        "predictionCoverage": covered / duration,
        "predictionDominance": product_duration / covered if covered > 1e-9 else 0.0,
    }


def _passing_funnels() -> tuple[dict[str, Any], dict[str, Any]]:
    aggregate = stage1.make_funnel(
        {"T": 64, "U": 16, "R": 48, "N": 12, "E": 36, "C": 24, "I": 12},
        {"T": 640, "U": 160, "R": 480, "N": 120, "E": 360, "C": 240, "I": 120},
    )
    guitarset = stage1.make_funnel(
        {"T": 160, "U": 40, "R": 120, "N": 30, "E": 90, "C": 30, "I": 60},
        {"T": 1600, "U": 400, "R": 1200, "N": 300, "E": 900, "C": 300, "I": 600},
    )
    return aggregate, guitarset


def test_constructs_exact_player_midpoint_and_preserves_prefix_and_source_receipts() -> None:
    timing = _timing([2.810], 4.099, prefix=2.810)
    timing_file_sha256 = _digest("physical-timing-file")
    timing_sha256 = canonical_sha256(timing)

    construction, derived = stage1.construct_half_bar_cells(
        timing,
        source_timing_file_sha256=timing_file_sha256,
        manifest_timing_sha256=timing_sha256,
        manifest_timing_contract_sha256=timing["contractSha256"],
        analyzer_timing_source_contract_sha256=timing["timingProvenance"]["barStartsSeconds"]["sourceContractSha256"],
    )

    assert [(row["startMilliseconds"], row["endMilliseconds"]) for row in construction["cells"]] == [
        (2810, 3455),
        (3455, 4099),
    ]
    assert [row["durationMilliseconds"] for row in construction["cells"]] == [645, 644]
    assert construction["prefixMilliseconds"] == 2810
    assert construction["coveredDurationMilliseconds"] == 1289
    assert construction["timingFileSha256"] == timing_file_sha256
    assert construction["timingSha256"] == timing_sha256
    assert construction["timingFileSha256"] != construction["timingSha256"]
    assert construction["timingContractSha256"] == timing["contractSha256"]
    assert construction["timingSourceContractSha256"] != timing["contractSha256"]
    assert construction["targetPlayerHalfSplitContractSha256"] == stage1.TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256
    assert derived["schemaVersion"] == stage1.CELL_TIMING_SCHEMA
    assert derived["runtimeAnalyzerOutput"] is False
    assert derived["referenceFree"] is True
    assert derived["cellStartsMilliseconds"] == [2810, 3455]
    stage1._validate_construction(construction, "construction")


@pytest.mark.parametrize(
    ("starts", "duration", "prefix", "message"),
    [
        ([0.0], 1.0004, None, "exact integer-millisecond"),
        ([0.0004], 1.001, 0.0004, "exact integer-millisecond"),
        ([0.0, 0.001], 0.002, None, "at least 2 canonical milliseconds"),
    ],
)
def test_construction_rejects_nonmillisecond_and_one_millisecond_parent_inputs(
    starts: list[float],
    duration: float,
    prefix: float | None,
    message: str,
) -> None:
    with pytest.raises(stage1.HalfBarStage1Error, match=message):
        stage1.construct_half_bar_cells(_timing(starts, duration, prefix=prefix))


def test_construction_rejects_manifest_and_analyzer_contract_splices() -> None:
    timing = _timing([0.0], 2.0)
    with pytest.raises(stage1.HalfBarStage1Error, match="Manifest timingSha256"):
        stage1.construct_half_bar_cells(timing, manifest_timing_sha256=_digest("wrong-timing"))
    with pytest.raises(stage1.HalfBarStage1Error, match="Analyzer timingSourceContractSha256"):
        stage1.construct_half_bar_cells(
            timing,
            analyzer_timing_source_contract_sha256=_digest("wrong-analyzer"),
        )


def test_construction_validator_recomputes_midpoint_instead_of_trusting_fresh_hashes() -> None:
    construction, _derived = _construction([0.0], 2.001)
    tampered = deepcopy(construction)
    first = tampered["cells"][0]
    first["endMilliseconds"] -= 1
    first["durationMilliseconds"] -= 1
    _rehash(first, "rowSha256")
    tampered["cellSetSha256"] = canonical_sha256(tampered["cells"])
    _rehash(tampered, "constructionSha256")

    with pytest.raises(stage1.HalfBarStage1Error, match="frozen midpoint rule"):
        stage1._validate_construction(tampered, "construction")


def test_rounded_runtime_tail_is_uncovered_and_unique_terminal_reference_is_reconciled() -> None:
    construction, derived = _construction([0.0], 1.001)
    prediction = _prediction(1.0006, [(0.0, 1.0006, "C")])
    summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("prediction-validation"),
    )

    terminal_prediction = summary["cells"][1]
    assert terminal_prediction["startMilliseconds"] == 501
    assert terminal_prediction["endMilliseconds"] == 1001
    assert terminal_prediction["predictionCoveredDurationSeconds"] == pytest.approx(0.4996)
    assert terminal_prediction["predictionCoverage"] == pytest.approx(0.9992)
    assert terminal_prediction["predictionCoverage"] < 1.0

    outcomes, reconciliation = stage1.score_fixed_cells(
        {"segments": [{"start": 0.0, "end": 1.00065, "label": "C"}]},
        prediction,
        construction,
        summary,
    )

    assert reconciliation == {
        "originalEnd": 1.00065,
        "predictionDuration": 1.0006,
        "reconciledEnd": 1.0006,
        "reconciledSeconds": pytest.approx(0.00005),
        "canonicalMs": 1001,
    }
    assert outcomes[1]["referenceCoveredDurationSeconds"] == pytest.approx(0.4996)
    assert outcomes[1]["referenceCoverage"] == pytest.approx(0.9992)
    assert outcomes[1]["classification"] == "C"


def test_scoring_clamps_prefix_and_rounded_tail_to_exact_2810_4099_cell_partition() -> None:
    construction, derived = _construction([2.810], 4.099, prefix=2.810)
    prediction = _prediction(4.0986, [(0.0, 4.0986, "C")])
    summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("prediction-validation"),
    )

    assert [(row["startMilliseconds"], row["endMilliseconds"]) for row in summary["cells"]] == [
        (2810, 3455),
        (3455, 4099),
    ]
    assert sum(row["durationMilliseconds"] for row in summary["cells"]) == 1289
    assert sum(row["predictionCoveredDurationSeconds"] for row in summary["cells"]) == pytest.approx(1.2886)
    assert summary["cells"][0]["predictionCoveredDurationSeconds"] == pytest.approx(0.645)
    assert summary["cells"][1]["predictionCoveredDurationSeconds"] == pytest.approx(0.6436)
    assert summary["cells"][1]["predictionCoverage"] < 1.0


def test_endpoint_reconciliation_fails_closed_outside_same_player_millisecond() -> None:
    construction, derived = _construction([0.0], 1.001)
    prediction = _prediction(1.0006, [(0.0, 1.0006, "C")])
    summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("prediction-validation"),
    )
    with pytest.raises(stage1.HalfBarStage1Error, match="outside the prediction canonical millisecond"):
        stage1.score_fixed_cells(
            {"segments": [{"start": 0.0, "end": 1.0016, "label": "C"}]},
            prediction,
            construction,
            summary,
        )


@pytest.mark.parametrize(
    ("field", "delta", "classification", "reason"),
    [
        ("referenceCoverage", -1e-9, "C", None),
        ("referenceCoverage", -1.1e-9, "U", "referenceUncovered"),
        ("referenceDominance", -1e-9, "C", None),
        ("referenceDominance", -1.1e-9, "U", "referenceMixed"),
        ("predictionCoverage", -1e-9, "C", None),
        ("predictionCoverage", -1.1e-9, "N", "predictionUncovered"),
        ("predictionDominance", -1e-9, "C", None),
        ("predictionDominance", -1.1e-9, "N", "predictionMixed"),
    ],
)
def test_epsilon_boundary_is_inclusive_and_larger_deficit_fails(
    field: str,
    delta: float,
    classification: str,
    reason: str | None,
) -> None:
    evidence = {
        "referenceProduct": "C",
        "referenceCoverage": 1.0,
        "referenceDominance": 1.0,
        "predictionProduct": "C",
        "predictionCoverage": 1.0,
        "predictionDominance": 1.0,
    }
    evidence[field] = 0.75 + delta
    assert stage1._classification_from_evidence(evidence) == (classification, reason)


def test_ties_are_lexical_and_sub_epsilon_slivers_are_ignored() -> None:
    construction, derived = _construction([0.0], 2.0)
    prediction = _prediction(
        2.0,
        [(0.0, 0.5, "G"), (0.5, 1.0, "C"), (1.0, 2.0, "D")],
    )
    summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("prediction-validation"),
    )
    assert summary["cells"][0]["predictionProduct"] == "C"
    assert summary["cells"][0]["predictionDominance"] == pytest.approx(0.5)

    overlaps, covered = stage1._bar_product._overlap_by_product(
        [
            {"start": 0.0, "end": 0.5, "product": "C"},
            {"start": 0.5, "end": 0.5 + 0.9e-9, "product": "D"},
        ],
        0.0,
        1.0,
    )
    assert overlaps == {"C": 0.5}
    assert covered == 0.5
    boundary_overlaps, boundary_covered = stage1._bar_product._overlap_by_product(
        [{"start": 0.0, "end": 1e-9, "product": "D"}],
        0.0,
        1.0,
    )
    assert boundary_overlaps == {}
    assert boundary_covered == 0.0
    super_epsilon_overlaps, super_epsilon_covered = stage1._bar_product._overlap_by_product(
        [{"start": 0.0, "end": 1.1e-9, "product": "D"}],
        0.0,
        1.0,
    )
    assert super_epsilon_overlaps == {"D": 1.1e-9}
    assert super_epsilon_covered == 1.1e-9
    assert stage1._bar_product._dominant_product({"G": 0.5, "C": 0.5}) == ("C", 0.5)


def test_score_and_funnel_reconcile_all_four_terminal_outcomes() -> None:
    construction, _derived = _construction([0.0, 2.0], 4.0)
    cells = construction["cells"]
    prediction_summary = {
        "cells": [
            _summary_cell(cells[0], "C", 1.0, 1.0),
            _summary_cell(cells[1], None, 0.0, 0.0),
            _summary_cell(cells[2], "D", 1.0, 1.0),
            _summary_cell(cells[3], "F", 1.0, 1.0),
        ]
    }
    reference = {
        "durationSeconds": 4.0,
        "segments": [
            {"start": 0.0, "end": 0.7, "label": "C"},
            {"start": 1.0, "end": 2.0, "label": "C"},
            {"start": 2.0, "end": 3.0, "label": "D"},
            {"start": 3.0, "end": 4.0, "label": "E"},
        ],
    }

    outcomes, reconciliation = stage1.score_fixed_cells(
        reference,
        {"durationSeconds": 4.0},
        construction,
        prediction_summary,
    )
    assert reconciliation is None
    assert [(row["classification"], row["reason"]) for row in outcomes] == [
        ("U", "referenceUncovered"),
        ("N", "predictionUncovered"),
        ("C", None),
        ("I", None),
    ]
    funnel, exclusions = stage1.funnel_from_outcomes(outcomes)
    expected = {"T": 4, "U": 1, "R": 3, "N": 1, "E": 2, "C": 1, "I": 1}
    assert funnel["counts"] == expected
    assert funnel["durationMilliseconds"] == {field: value * 1000 for field, value in expected.items()}
    assert exclusions["counts"] == {
        "referenceMixed": 0,
        "referenceUncovered": 1,
        "predictionMixed": 0,
        "predictionUncovered": 1,
    }


def test_funnel_rejects_broken_partitions_and_discloses_c_over_e_without_gating_it() -> None:
    with pytest.raises(stage1.HalfBarStage1Error, match="exact T/U/R/N/E/C/I partitions"):
        stage1.make_funnel(
            {"T": 4, "U": 1, "R": 3, "N": 1, "E": 2, "C": 2, "I": 1},
            {"T": 4, "U": 1, "R": 3, "N": 1, "E": 2, "C": 1, "I": 1},
        )

    aggregate, _guitarset = _passing_funnels()
    disclosure = aggregate["rates"]["counts"]["correctShareAmongEligibleDisclosure"]
    upper_bound = aggregate["rates"]["counts"]["oracleEndToEndCorrectSupportUpperBound"]
    assert disclosure == {"numerator": 24, "denominator": 36, "value": 2 / 3, "hasSupport": True}
    assert upper_bound == {"numerator": 24, "denominator": 48, "value": 0.5, "hasSupport": True}


def test_exact_thirteen_gates_pass_inclusively_at_the_frozen_boundaries() -> None:
    aggregate, guitarset = _passing_funnels()
    gates = stage1.build_stage1_gates(aggregate, guitarset)

    assert len(gates) == 13
    assert all(gate["passed"] is True for gate in gates)
    assert gates[0]["gateId"] == "aggregate.counts.referenceDeterminacy"
    assert gates[4]["gateId"] == "aggregate.counts.oracleCorrectSupportUpperBound"
    assert gates[-1]["gateId"] == "guitarset.counts.minimumCorrectCellCount"
    assert gates[0]["crossProductLeft"] == gates[0]["crossProductRight"]
    assert gates[4]["crossProductLeft"] == gates[4]["crossProductRight"]


def test_zero_denominators_fail_and_minimum_correct_count_is_an_independent_gate() -> None:
    empty = stage1.make_funnel(
        {field: 0 for field in stage1._FUNNEL_FIELDS},
        {field: 0 for field in stage1._FUNNEL_FIELDS},
    )
    assert not any(gate["passed"] for gate in stage1.build_stage1_gates(empty, empty))

    aggregate, _guitarset = _passing_funnels()
    guitarset = stage1.make_funnel(
        {"T": 120, "U": 30, "R": 90, "N": 22, "E": 68, "C": 29, "I": 39},
        {"T": 1200, "U": 300, "R": 900, "N": 220, "E": 680, "C": 290, "I": 390},
    )
    gates = stage1.build_stage1_gates(aggregate, guitarset)
    assert [gate["gateId"] for gate in gates if not gate["passed"]] == ["guitarset.counts.minimumCorrectCellCount"]


def test_prediction_identity_is_a_strict_reference_free_allowlist() -> None:
    source = {
        "id": "track-001",
        "split": "development",
        "predictionFile": "predictions/track-001.json",
        "predictionSha256": _digest("prediction-file"),
        "predictionCoreSha256": _digest("prediction-core"),
        "uncertaintySha256": _digest("uncertainty"),
        "sourceAudioSha256": _digest("audio"),
        "cachedFeatureArraySha256": _digest("cached"),
        "freshFeatureArraySha256": _digest("fresh"),
        "canonicalDurationMilliseconds": 1000,
        "audioLineageRowSha256": _digest("lineage-row"),
        "referenceSha256": _digest("reference"),
        "correctBarCount": 999,
        "metrics": {"accuracy": 1.0},
    }
    identity = stage1._prediction_identity(source)
    assert set(identity) == {
        "id",
        "split",
        "predictionFile",
        "predictionSha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "canonicalDurationMilliseconds",
        "audioLineageRowSha256",
        "predictionIdentitySha256",
    }
    assert "referenceSha256" not in identity
    assert "metrics" not in identity
    assert "correctBarCount" not in identity


def test_group_role_reference_binding_rejects_a_freshly_rehashed_splice() -> None:
    group_payload = {
        "trackId": "guitarset-track",
        "split": "development",
        "datasetId": "guitarset",
        "role": "guitarset:comp:player-00",
        "confidenceGroupId": "composition:guitarset:00",
        "referenceFile": "references/guitarset-track.json",
        "referenceSha256": _digest("reference"),
    }
    source_group = {**group_payload, "trackMetadataSha256": canonical_sha256(group_payload)}
    row = {
        "trackId": source_group["trackId"],
        "split": "development",
        "datasetId": source_group["datasetId"],
        "role": source_group["role"],
        "guitarsetRole": "comp",
        "confidenceGroupId": source_group["confidenceGroupId"],
        "sourceReferenceSha256": source_group["referenceSha256"],
        "sourceGroupTrackMetadataSha256": source_group["trackMetadataSha256"],
        "sourceGroupTrack": source_group,
    }
    assert stage1._validate_source_group_track_binding(row, "track") == source_group

    tampered = deepcopy(row)
    tampered["sourceGroupTrack"]["role"] = "guitarset:solo:player-00"
    _rehash(tampered["sourceGroupTrack"], "trackMetadataSha256")
    tampered["sourceGroupTrackMetadataSha256"] = tampered["sourceGroupTrack"]["trackMetadataSha256"]
    with pytest.raises(stage1.HalfBarStage1Error, match="not exactly source-bound"):
        stage1._validate_source_group_track_binding(tampered, "track")


def test_official_shape_and_exact_guitarset_role_track_support_are_frozen() -> None:
    assert stage1.STAGE1_SOURCE_CONTRACT["trackCount"] == 246
    assert stage1.STAGE1_SOURCE_CONTRACT["confidenceGroupCount"] == 169
    reviewed = stage1.REVIEWED_DEVELOPMENT_GROUP_SHAPE
    assert reviewed["trackCount"] == sum(row["trackCount"] for row in reviewed["datasets"]) == 246
    assert (
        reviewed["confidenceGroupCount"] == sum(len(row["confidenceGroupSizes"]) for row in reviewed["datasets"]) == 169
    )
    assert next(row for row in reviewed["datasets"] if row["datasetId"] == "guitarset")["trackCount"] == 36
    assert stage1.OFFICIAL_STRUCTURAL_SUPPORT["aggregate"] == {
        "parentBarCount": 2919,
        "fixedCellCount": 5838,
    }
    rows = [{"datasetId": "guitarset", "guitarsetRole": role} for role in ("comp", "solo") for _index in range(18)]
    stage1._require_official_guitar_role_track_support(rows)
    rows[-1]["guitarsetRole"] = "comp"
    with pytest.raises(stage1.HalfBarStage1Error, match="exactly 18 comp and 18 solo"):
        stage1._require_official_guitar_role_track_support(rows)


def test_target_player_worker_is_transitively_hash_bound_before_cell_work(monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer_sha256 = _digest("runtime-analyzer-contract")
    runtime = {
        "analyzerContract": {
            "contractSha256": analyzer_sha256,
            "implementation": {"workerSha256": stage1.TARGET_PLAYER_HALF_SPLIT_CONTRACT["workerSha256"]},
        }
    }
    binding, source_path, raw, _stat = stage1._target_player_worker_binding(runtime)
    assert source_path.name == "practice-analysis-worker.js"
    assert hashlib.sha256(raw).hexdigest() == binding["fileSha256"]
    assert binding["runtimeAnalyzerContractSha256"] == analyzer_sha256
    assert binding["targetPlayerHalfSplitContractSha256"] == stage1.TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256

    opened = False

    def unexpected_open(*_args: Any, **_kwargs: Any) -> int:
        nonlocal opened
        opened = True
        raise AssertionError("worker file must not be opened after a manifest binding failure")

    monkeypatch.setattr(stage1.os, "open", unexpected_open)
    bad_runtime = deepcopy(runtime)
    bad_runtime["analyzerContract"]["implementation"]["workerSha256"] = _digest("wrong-worker")
    with pytest.raises(stage1.HalfBarStage1Error, match="does not bind"):
        stage1._target_player_worker_binding(bad_runtime)
    assert opened is False


def _all_correct_track(
    track_id: str,
    dataset_id: str,
    role: str,
    guitarset_role: str | None,
    construction: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    group_payload = {
        "trackId": track_id,
        "split": "development",
        "datasetId": dataset_id,
        "role": role,
        "confidenceGroupId": f"composition:{track_id}",
        "referenceFile": f"references/{track_id}.json",
        "referenceSha256": _digest(f"reference:{track_id}"),
    }
    source_group = {**group_payload, "trackMetadataSha256": canonical_sha256(group_payload)}
    outcomes: list[dict[str, Any]] = []
    for cell in construction["cells"]:
        duration = cell["durationMilliseconds"] / 1000
        outcome_payload = {
            "cellIndex": cell["cellIndex"],
            "parentBarIndex": cell["parentBarIndex"],
            "halfIndex": cell["halfIndex"],
            "durationMilliseconds": cell["durationMilliseconds"],
            "referenceProduct": "C",
            "referenceCoveredDurationSeconds": duration,
            "referenceProductDurationSeconds": duration,
            "referenceCoverage": 1.0,
            "referenceDominance": 1.0,
            "predictionProduct": "C",
            "predictionCoveredDurationSeconds": duration,
            "predictionProductDurationSeconds": duration,
            "predictionCoverage": 1.0,
            "predictionDominance": 1.0,
            "classification": "C",
            "reason": None,
        }
        outcomes.append(stage1._self_hashed(outcome_payload, "rowSha256"))
    funnel, exclusion_audit = stage1.funnel_from_outcomes(outcomes)
    summary_artifact_sha256 = _digest(f"prediction-summary:{track_id}")
    summary_path = str(Path("/sealed-stage1-summaries") / stage1._summary_filename(track_id, summary_artifact_sha256))
    track_payload = {
        "trackId": track_id,
        "split": "development",
        "datasetId": dataset_id,
        "role": role,
        "guitarsetRole": guitarset_role,
        "confidenceGroupId": source_group["confidenceGroupId"],
        "sourceGroupTrack": source_group,
        "sourceGroupTrackMetadataSha256": source_group["trackMetadataSha256"],
        "predictionIdentitySha256": _digest(f"prediction-identity:{track_id}"),
        "timingFileSha256": construction["timingFileSha256"],
        "timingSha256": construction["timingSha256"],
        "timingContractSha256": construction["timingContractSha256"],
        "timingSourceContractSha256": construction["timingSourceContractSha256"],
        "sourceReferenceSha256": source_group["referenceSha256"],
        "referenceEndpointReconciliationRowSha256": None,
        "predictionOnlySummary": {
            "path": summary_path,
            "pathSha256": canonical_sha256(summary_path),
            "artifactSha256": summary_artifact_sha256,
        },
        "construction": construction,
        "constructionSha256": construction["constructionSha256"],
        "parentBarCount": construction["parentBarCount"],
        "cellCount": construction["cellCount"],
        "cellOutcomes": outcomes,
        "cellOutcomeSetSha256": canonical_sha256(outcomes),
        "funnel": funnel,
        "funnelSha256": funnel["funnelSha256"],
        "exclusionAudit": exclusion_audit,
        "exclusionAuditSha256": exclusion_audit["auditSha256"],
    }
    track = stage1._self_hashed(track_payload, "rowSha256")
    projection_payload = {
        "trackId": track_id,
        "datasetId": dataset_id,
        "canonicalDurationMilliseconds": construction["canonicalDurationMilliseconds"],
        "sourceAudioSha256": _digest(f"audio:{track_id}"),
    }
    projection = stage1._self_hashed(projection_payload, "rowSha256")
    return track, projection


def _synthetic_valid_artifact(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    construction, _derived = _construction([0.0], 2.0)
    descriptors: list[tuple[str, str, str, str | None]] = [
        ("aam-00", "aam", "aam:mix:00", None),
        ("idmt-00", "idmt_guitar", "idmt_guitar:mix:00", None),
        ("nrgcp-00", "nrgcp", "nrgcp:mix:00", None),
        ("winterreise-00", "winterreise", "winterreise:mix:00", None),
    ]
    descriptors.extend(
        (f"guitarset-comp-{index:02d}", "guitarset", f"guitarset:comp:player-{index:02d}", "comp")
        for index in range(18)
    )
    descriptors.extend(
        (f"guitarset-solo-{index:02d}", "guitarset", f"guitarset:solo:player-{index:02d}", "solo")
        for index in range(18)
    )
    pairs = [
        _all_correct_track(track_id, dataset_id, role, guitarset_role, construction)
        for track_id, dataset_id, role, guitarset_role in descriptors
    ]
    tracks = sorted((track for track, _projection in pairs), key=lambda row: row["trackId"])
    projections_by_id = {projection["trackId"]: projection for _track, projection in pairs}
    projection_rows = [projections_by_id[track["trackId"]] for track in tracks]
    projection_payload = {
        "schemaVersion": "synthetic-audio-lineage-projection-v1",
        "trackCount": len(projection_rows),
        "tracks": projection_rows,
        "trackSetSha256": canonical_sha256(projection_rows),
    }
    projection = stage1._self_hashed(projection_payload, "projectionSha256")
    projection_tracks = {row["trackId"]: row for row in projection_rows}
    group_projection = {row["trackId"]: {"confidenceGroupId": row["confidenceGroupId"]} for row in tracks}
    audio_group_audit = bar_examples._audio_group_audit(
        [row["trackId"] for row in tracks], group_projection, projection_tracks
    )
    structural_support = stage1._structural_support_from_track_rows(tracks)
    source_group_set_sha256 = canonical_sha256(
        [
            {
                "trackId": row["trackId"],
                "trackMetadataSha256": row["sourceGroupTrackMetadataSha256"],
            }
            for row in tracks
        ]
    )

    contract = deepcopy(stage1.STAGE1_SOURCE_CONTRACT)
    shared_binding = deepcopy(contract["sharedPredictionRuntimeBinding"])
    contract["trackCount"] = len(tracks)
    contract["benchmarkReport"] = {
        "fileSha256": _digest("benchmark-file"),
        "canonicalSha256": _digest("benchmark-canonical"),
        "trackSetSha256": _digest("benchmark-track-set"),
        "predictionArtifactSetSha256": _digest("prediction-artifact-set"),
        "predictionCoreSetSha256": _digest("prediction-core-set"),
        "uncertaintySetSha256": _digest("uncertainty-set"),
        "modelOrEnsembleSha256": shared_binding["modelOrEnsembleSha256"],
    }
    contract["runtimeManifest"] = {
        "fileSha256": _digest("runtime-file"),
        "manifestSha256": _digest("runtime-manifest"),
        "trackSetSha256": _digest("runtime-track-set"),
        "analyzerContractSha256": shared_binding["timingSourceContractSha256"],
    }
    contract["groupManifest"] = {
        "fileSha256": _digest("group-file"),
        "manifestSha256": _digest("group-manifest"),
        "trackSetSha256": source_group_set_sha256,
    }
    contract["audioLineage"] = {
        "fileSha256": _digest("audio-lineage-file"),
        "artifactSha256": _digest("audio-lineage-artifact"),
        "projectionSha256": projection["projectionSha256"],
    }
    contract["structuralSupport"] = structural_support
    monkeypatch.setattr(stage1, "OFFICIAL_STRUCTURAL_SUPPORT", structural_support)
    monkeypatch.setattr(stage1, "STAGE1_SOURCE_CONTRACT", contract)
    monkeypatch.setattr(stage1, "STAGE1_SOURCE_CONTRACT_SHA256", canonical_sha256(contract))
    monkeypatch.setattr(stage1, "_validate_reviewed_group_shape", lambda _tracks: None)

    prediction_sets = stage1._self_hashed(
        {
            "predictionArtifactSetSha256": contract["benchmarkReport"]["predictionArtifactSetSha256"],
            "predictionCoreSetSha256": contract["benchmarkReport"]["predictionCoreSetSha256"],
            "uncertaintySetSha256": contract["benchmarkReport"]["uncertaintySetSha256"],
            "allThreeDistinct": True,
        },
        "bindingsSha256",
    )
    target_path = "/sealed/ui/practice-analysis-worker.js"
    target_player = stage1._self_hashed(
        {
            "schemaVersion": "chord_target_player_half_split_source_binding_v1",
            "path": target_path,
            "pathSha256": canonical_sha256(target_path),
            "fileSha256": stage1.TARGET_PLAYER_HALF_SPLIT_CONTRACT["workerSha256"],
            "runtimeAnalyzerContractSha256": contract["runtimeManifest"]["analyzerContractSha256"],
            "runtimeManifestWorkerSha256": stage1.TARGET_PLAYER_HALF_SPLIT_CONTRACT["workerSha256"],
            "targetPlayerHalfSplitContractSha256": stage1.TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
        },
        "bindingSha256",
    )
    output_path = "/sealed-stage1-output/artifact.json"
    summary_output_root = "/sealed-stage1-summaries"
    input_bindings = stage1._self_hashed(
        {
            "schemaVersion": "chord_fixed_half_bar_stage1_input_bindings_v1",
            "benchmarkReport": {
                "fileSha256": contract["benchmarkReport"]["fileSha256"],
                "canonicalSha256": contract["benchmarkReport"]["canonicalSha256"],
                "claimedArtifactSha256": None,
                "trackSetSha256": contract["benchmarkReport"]["trackSetSha256"],
                "modelOrEnsembleSha256": contract["benchmarkReport"]["modelOrEnsembleSha256"],
                "predictionSets": prediction_sets,
            },
            "runtimeManifest": {
                "fileSha256": contract["runtimeManifest"]["fileSha256"],
                "claimedArtifactSha256": contract["runtimeManifest"]["manifestSha256"],
                "trackSetSha256": contract["runtimeManifest"]["trackSetSha256"],
                "analyzerContractSha256": contract["runtimeManifest"]["analyzerContractSha256"],
            },
            "groupManifest": {
                "fileSha256": contract["groupManifest"]["fileSha256"],
                "claimedArtifactSha256": contract["groupManifest"]["manifestSha256"],
                "trackSetSha256": contract["groupManifest"]["trackSetSha256"],
            },
            "audioLineage": {
                "fileSha256": contract["audioLineage"]["fileSha256"],
                "claimedArtifactSha256": contract["audioLineage"]["artifactSha256"],
                "projectionSha256": contract["audioLineage"]["projectionSha256"],
            },
            "targetPlayerWorker": target_player,
            "summaryOutputRoot": {
                "path": summary_output_root,
                "pathSha256": canonical_sha256(summary_output_root),
            },
        },
        "bindingsSha256",
    )
    artifact = stage1._build_artifact(
        input_bindings=input_bindings,
        publication={
            "mode": "atomic-new-json-and-summary-directory-set-v1",
            "outputPath": output_path,
            "outputPathSha256": canonical_sha256(output_path),
            "summaryOutputRoot": summary_output_root,
            "summaryOutputRootSha256": canonical_sha256(summary_output_root),
        },
        shared_binding=shared_binding,
        track_rows=tracks,
        projection_tracks=projection_tracks,
        audio_lineage_projection=projection,
        audio_group_audit=audio_group_audit,
        reconciliation_rows=[],
    )
    return artifact


def test_artifact_validator_accepts_a_fully_reconciled_synthetic_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    assert stage1.validate_half_bar_stage1_artifact(artifact) == artifact
    assert artifact["guitarset"]["trackCount"] == 36
    assert [row["trackCount"] for row in artifact["guitarset"]["compSolo"]] == [18, 18]
    assert artifact["decision"]["gateCount"] == 13
    assert artifact["calibrationMayOpenOnce"] is False


def test_artifact_validator_rejects_deep_tampering_even_after_all_outer_hashes_are_refreshed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    track = tampered["tracks"][0]
    outcome = track["cellOutcomes"][0]
    outcome["classification"] = "I"
    _rehash(outcome, "rowSha256")
    track["cellOutcomeSetSha256"] = canonical_sha256(track["cellOutcomes"])
    _rehash(track, "rowSha256")
    tampered["trackSetSha256"] = canonical_sha256(tampered["tracks"])
    _rehash(tampered, "artifactSha256")
    with pytest.raises(stage1.HalfBarStage1Error, match="classification/reason is stale"):
        stage1.validate_half_bar_stage1_artifact(tampered)


def test_artifact_validator_rejects_source_contract_and_reconciliation_audit_rewrites(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)

    contract_tamper = deepcopy(artifact)
    contract_tamper["sourceContract"]["trackCount"] += 1
    contract_tamper["sourceContractSha256"] = canonical_sha256(contract_tamper["sourceContract"])
    _rehash(contract_tamper, "artifactSha256")
    with pytest.raises(stage1.HalfBarStage1Error, match="official source contract is not exact"):
        stage1.validate_half_bar_stage1_artifact(contract_tamper)

    reconciliation_tamper = deepcopy(artifact)
    audit = reconciliation_tamper["referenceEndpointReconciliationAudit"]
    audit["unreconciledTrackCount"] -= 1
    _rehash(audit, "auditSha256")
    reconciliation_tamper["referenceEndpointReconciliationAuditSha256"] = audit["auditSha256"]
    _rehash(reconciliation_tamper, "artifactSha256")
    with pytest.raises(stage1.HalfBarStage1Error, match="reconciliation audit is stale"):
        stage1.validate_half_bar_stage1_artifact(reconciliation_tamper)


def test_artifact_validator_rejects_resealed_shared_publication_and_summary_path_splices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)

    shared_tamper = deepcopy(artifact)
    shared_tamper["sharedPredictionRuntimeBinding"]["sourceFeatureKind"] = ""
    shared_tamper["sharedPredictionRuntimeBindingSha256"] = canonical_sha256(
        shared_tamper["sharedPredictionRuntimeBinding"]
    )
    _rehash(shared_tamper, "artifactSha256")
    with pytest.raises(stage1.HalfBarStage1Error, match="shared prediction/runtime semantics are stale"):
        stage1.validate_half_bar_stage1_artifact(shared_tamper)

    publication_tamper = deepcopy(artifact)
    publication_tamper["publication"]["outputPath"] = (
        f"{publication_tamper['publication']['summaryOutputRoot']}/artifact.json"
    )
    publication_tamper["publication"]["outputPathSha256"] = canonical_sha256(
        publication_tamper["publication"]["outputPath"]
    )
    _rehash(publication_tamper, "artifactSha256")
    with pytest.raises(stage1.HalfBarStage1Error, match="atomic disjoint new-path set"):
        stage1.validate_half_bar_stage1_artifact(publication_tamper)

    path_tamper = deepcopy(artifact)
    track = path_tamper["tracks"][0]
    track["predictionOnlySummary"]["path"] = str(
        Path(path_tamper["publication"]["summaryOutputRoot"]) / "wrong-but-resealed.json"
    )
    track["predictionOnlySummary"]["pathSha256"] = canonical_sha256(track["predictionOnlySummary"]["path"])
    _rehash(track, "rowSha256")
    path_tamper["trackSetSha256"] = canonical_sha256(path_tamper["tracks"])
    _rehash(path_tamper, "artifactSha256")
    with pytest.raises(stage1.HalfBarStage1Error, match="summary path binding is stale"):
        stage1.validate_half_bar_stage1_artifact(path_tamper)


@pytest.mark.parametrize(
    "field",
    (
        "uncertaintyContractSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "sourceFeatureSpecSha256",
    ),
)
def test_artifact_validator_rejects_resealed_shared_identity_hash_splices(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    artifact["sharedPredictionRuntimeBinding"][field] = _digest(f"spliced:{field}")
    artifact["sharedPredictionRuntimeBindingSha256"] = canonical_sha256(artifact["sharedPredictionRuntimeBinding"])
    _rehash(artifact, "artifactSha256")

    with pytest.raises(stage1.HalfBarStage1Error, match="shared prediction/runtime semantics are stale"):
        stage1.validate_half_bar_stage1_artifact(artifact)


def test_prediction_phase_finishes_before_reference_phase_and_failures_preserve_barrier() -> None:
    events: list[str] = []

    def seal() -> tuple[list[str], dict[str, str]]:
        events.extend(["seal:first", "seal:last"])
        return ["first", "last"], {"binding": "sealed"}

    def references(records: list[str]) -> tuple[list[str], list[str]]:
        assert records == ["first", "last"]
        assert events == ["seal:first", "seal:last"]
        events.append("reference:first")
        return ["scored"], ["reconciled"]

    result = stage1._run_ordered_phases(seal, references)
    assert result == (["first", "last"], {"binding": "sealed"}, ["scored"], ["reconciled"])
    assert events == ["seal:first", "seal:last", "reference:first"]

    reference_called = False

    def mismatched_duration() -> tuple[list[str], dict[str, str]]:
        raise stage1.HalfBarStage1Error("Prediction, runtime construction, and identity canonical duration disagree")

    def forbidden_reference(_records: list[str]) -> tuple[list[str], list[str]]:
        nonlocal reference_called
        reference_called = True
        return [], []

    with pytest.raises(stage1.HalfBarStage1Error, match="canonical duration disagree"):
        stage1._run_ordered_phases(mismatched_duration, forbidden_reference)
    assert reference_called is False


def test_summary_set_publication_is_atomic_and_precommit_failure_leaves_no_outputs(tmp_path: Path) -> None:
    output_path = tmp_path / "stage1.json"
    summary_root = tmp_path / "summaries"

    def build(staging_root: Path) -> dict[str, Any]:
        (staging_root / "summary.json").write_text('{"sealed": true}\n', encoding="utf-8")
        return {"schemaVersion": "synthetic-stage1-v1", "sealed": True}

    artifact = stage1._stage_and_publish_summary_set(
        output_path,
        summary_root,
        build,
        lambda: None,
    )
    assert json.loads(output_path.read_text(encoding="utf-8")) == artifact
    assert json.loads((summary_root / "summary.json").read_text(encoding="utf-8")) == {"sealed": True}

    failed_output = tmp_path / "failed-stage1.json"
    failed_summaries = tmp_path / "failed-summaries"

    def fail_precommit() -> None:
        raise stage1.HalfBarStage1Error("source changed before commit")

    with pytest.raises(stage1.HalfBarStage1Error, match="source changed before commit"):
        stage1._stage_and_publish_summary_set(
            failed_output,
            failed_summaries,
            build,
            fail_precommit,
        )
    assert not failed_output.exists()
    assert not failed_summaries.exists()


@pytest.mark.parametrize("failed_phase", ("prediction", "reference"))
def test_prediction_or_reference_build_fault_leaves_no_partial_publication(
    tmp_path: Path,
    failed_phase: str,
) -> None:
    output_path = tmp_path / f"{failed_phase}-failed-stage1.json"
    summary_root = tmp_path / f"{failed_phase}-failed-summaries"

    def build(staging_root: Path) -> dict[str, Any]:
        if failed_phase == "reference":
            (staging_root / "sealed-prediction.json").write_text('{"referenceFree": true}\n', encoding="utf-8")
        raise stage1.HalfBarStage1Error(f"{failed_phase} phase failed")

    with pytest.raises(stage1.HalfBarStage1Error, match=f"{failed_phase} phase failed"):
        stage1._stage_and_publish_summary_set(output_path, summary_root, build, lambda: None)
    assert not output_path.exists()
    assert not summary_root.exists()


def test_invalid_staged_summary_set_leaves_no_partial_publication(tmp_path: Path) -> None:
    output_path = tmp_path / "stage1.json"
    summary_root = tmp_path / "summaries"

    def build(staging_root: Path) -> dict[str, Any]:
        (staging_root / "not-json.txt").write_text("invalid", encoding="utf-8")
        return {"schemaVersion": "synthetic-stage1-v1"}

    with pytest.raises(Exception, match="flat set of regular JSON files"):
        stage1._stage_and_publish_summary_set(output_path, summary_root, build, lambda: None)
    assert not output_path.exists()
    assert not summary_root.exists()
