from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from steel_guitar_rag.chord_reader import bar_examples
from steel_guitar_rag.chord_reader import beat_cell_stage1 as stage1
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _rehash(value: dict[str, Any], field: str) -> None:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})


def _beat_cells() -> list[dict[str, Any]]:
    return [
        {
            "beatIndex": 0,
            "retainedBarIndex": 0,
            "pulseNumber": 1,
            "downbeatCandidate": True,
            "startMs": 0,
            "endMs": 1000,
            "durationMilliseconds": 1000,
        },
        {
            "beatIndex": 1,
            "retainedBarIndex": 0,
            "pulseNumber": 2,
            "downbeatCandidate": False,
            "startMs": 1000,
            "endMs": 2000,
            "durationMilliseconds": 1000,
        },
    ]


def _beat_track(track_id: str) -> dict[str, Any]:
    cells = _beat_cells()
    timing = {
        "timingFile": f"timing-{track_id}.json",
        "timingSha256": _digest(f"timing:{track_id}"),
        "timingContractSha256": _digest(f"timing-contract:{track_id}"),
        "timingSourceContractSha256": _digest("runtime-analyzer"),
        "barCount": 1,
    }
    payload = {
        "trackId": track_id,
        "durationMilliseconds": 2000,
        "prefixExcludedMilliseconds": 0,
        "coveredDurationMilliseconds": 2000,
        "beatCount": 2,
        "beatTimesMs": [0, 1000],
        "barStartsMs": [0],
        "beatsPerBar": 2,
        "beatCells": cells,
        "parentTimingBinding": timing,
        "beatAnalyzerContractSha256": _digest("beat-analyzer"),
        "playerReplayContractSha256": _digest("player-replay"),
    }
    payload["topologySha256"] = canonical_sha256(
        {
            "beatTimesMs": payload["beatTimesMs"],
            "barStartsMs": payload["barStartsMs"],
            "durationMilliseconds": payload["durationMilliseconds"],
            "beatsPerBar": payload["beatsPerBar"],
            "beatCells": payload["beatCells"],
        }
    )
    return {**payload, "trackReceiptSha256": canonical_sha256(payload)}


def _receipt(tracks: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    totals = {
        "trackCount": len(tracks),
        "beatCellCount": sum(track["beatCount"] for track in tracks),
        "sourceDurationMilliseconds": sum(track["durationMilliseconds"] for track in tracks),
        "coveredDurationMilliseconds": sum(track["coveredDurationMilliseconds"] for track in tracks),
        "excludedPrefixDurationMilliseconds": sum(track["prefixExcludedMilliseconds"] for track in tracks),
    }
    payload = {
        "schemaVersion": "chord_runtime_beat_grid_receipt_v1",
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "runtimeAttested": True,
        "stage1UseAllowed": True,
        "selectorUseAllowed": False,
        "playerPlaybackUseAllowed": False,
        "confidenceUse": "disclosure-only",
        "publicationPolicy": {
            "mode": "relocatable-single-canonical-json",
            "pathBound": False,
            "commitPoint": "same-directory-hard-link-no-replace",
            "partialVisibleOutputAllowed": False,
        },
        "parentRuntimeBinding": {
            "manifestSha256": _digest("runtime-manifest"),
            "trackSetSha256": _digest("runtime-track-set"),
        },
        "analyzerContract": {"contractSha256": _digest("beat-analyzer")},
        "playerReplayContract": {"contractSha256": _digest("player-replay")},
        "sourceManifestSetSha256": canonical_sha256([]),
        "sourceManifests": [],
        "receiptTotals": totals,
        "receiptTotalsSha256": canonical_sha256(totals),
        "trackSetSha256": canonical_sha256(
            [{"trackId": row["trackId"], "trackReceiptSha256": row["trackReceiptSha256"]} for row in tracks]
        ),
        "tracks": tracks,
    }
    receipt = {**payload, "receiptSha256": canonical_sha256(payload)}
    raw = (json.dumps(receipt, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    return receipt, hashlib.sha256(raw).hexdigest()


def _install_synthetic_beat_contract(
    monkeypatch: pytest.MonkeyPatch,
    receipt: dict[str, Any],
    file_sha256: str,
) -> dict[str, Any]:
    contract = {
        "schemaVersion": "chord_runtime_beat_cell_stage1_receipt_contract_v1",
        "receiptSchemaVersion": receipt["schemaVersion"],
        "fileSha256": file_sha256,
        "receiptSha256": receipt["receiptSha256"],
        "trackSetSha256": receipt["trackSetSha256"],
        "receiptTotalsSha256": receipt["receiptTotalsSha256"],
        "receiptTotals": deepcopy(receipt["receiptTotals"]),
        "beatAnalyzerContractSha256": receipt["analyzerContract"]["contractSha256"],
        "playerReplayContractSha256": receipt["playerReplayContract"]["contractSha256"],
        "parentRuntimeManifestSha256": receipt["parentRuntimeBinding"]["manifestSha256"],
        "parentRuntimeTrackSetSha256": receipt["parentRuntimeBinding"]["trackSetSha256"],
        "referenceFree": True,
        "stage1UseAllowed": True,
        "selectorUseAllowed": False,
        "playerPlaybackUseAllowed": False,
    }
    contract_sha256 = canonical_sha256(contract)
    monkeypatch.setattr(stage1, "OFFICIAL_BEAT_RECEIPT_CONTRACT", contract)
    monkeypatch.setattr(stage1, "OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256", contract_sha256)
    construction_policy = deepcopy(stage1.CONSTRUCTION_POLICY)
    construction_policy["officialBeatReceiptContractSha256"] = contract_sha256
    monkeypatch.setattr(stage1, "CONSTRUCTION_POLICY", construction_policy)
    monkeypatch.setattr(stage1, "CONSTRUCTION_POLICY_SHA256", canonical_sha256(construction_policy))
    rubric = deepcopy(stage1.STAGE1_RUBRIC)
    rubric["officialBeatReceiptContract"] = deepcopy(contract)
    rubric["officialBeatReceiptContractSha256"] = contract_sha256
    monkeypatch.setattr(stage1, "STAGE1_RUBRIC", rubric)
    monkeypatch.setattr(stage1, "STAGE1_RUBRIC_SHA256", canonical_sha256(rubric))
    return contract


def test_frozen_official_receipt_and_structural_t_are_exact() -> None:
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"] == (
        "be09f0973aa2ad12c626890f3c7015a50faf7ee24fefe4297ee44f14c79b2053"
    )
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"] == (
        "4f14ed0a3b3436ea8cdd50ae5fef77d0b086efc96c4ec8ec8e7a9af11814834b"
    )
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["trackSetSha256"] == (
        "a2de02b7419753d41a0ad1e6e85ca14ae5877fc93c2dc7847508ccc7ac004602"
    )
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptTotalsSha256"] == (
        "46c68e5de9b2cadbe7f0abc03e9a3faaf036d8b06db93f8998a1c0067c448e4a"
    )
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["beatAnalyzerContractSha256"] == (
        "9f8477192a97ea7c5c40688fcbfb9a084bf852f6e4e36055497a2647961d9c7f"
    )
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["playerReplayContractSha256"] == (
        "d6ff183f534a36f54aa5623fb1057b42689823357b4aca56bac88e3b6d614ae8"
    )
    assert stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptTotals"] == {
        "trackCount": 246,
        "beatCellCount": 11234,
        "sourceDurationMilliseconds": 6443258,
        "coveredDurationMilliseconds": 6201472,
        "excludedPrefixDurationMilliseconds": 241786,
    }
    assert stage1.OFFICIAL_STRUCTURAL_SUPPORT["aggregate"] == {
        "fixedCellCount": 11234,
        "fixedCellDurationMilliseconds": 6201472,
    }
    assert stage1.OFFICIAL_STRUCTURAL_SUPPORT["datasets"] == [
        {"datasetId": "aam", "fixedCellCount": 545, "fixedCellDurationMilliseconds": 295509},
        {"datasetId": "guitarset", "fixedCellCount": 2392, "fixedCellDurationMilliseconds": 1133524},
        {"datasetId": "idmt_guitar", "fixedCellCount": 2231, "fixedCellDurationMilliseconds": 1293968},
        {"datasetId": "nrgcp", "fixedCellCount": 4203, "fixedCellDurationMilliseconds": 2368023},
        {"datasetId": "winterreise", "fixedCellCount": 1863, "fixedCellDurationMilliseconds": 1110448},
    ]
    assert stage1.OFFICIAL_STRUCTURAL_SUPPORT["guitarsetRoles"] == [
        {
            "guitarsetRole": "comp",
            "trackCount": 18,
            "fixedCellCount": 1039,
            "fixedCellDurationMilliseconds": 566668,
        },
        {
            "guitarsetRole": "solo",
            "trackCount": 18,
            "fixedCellCount": 1353,
            "fixedCellDurationMilliseconds": 566856,
        },
    ]
    assert stage1.STAGE1_SOURCE_CONTRACT["trackCount"] == 246
    assert stage1.STAGE1_SOURCE_CONTRACT["benchmarkReport"]["predictionIdentitySetSha256"] == (
        "aa6471a3de97ce33f4e2d8f7faaea3d6dd0197e49f2318e17a6917b4a5e38e8e"
    )


def test_constructor_copies_exact_receipt_cells_and_source_binds_lineage(monkeypatch: pytest.MonkeyPatch) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    contract = _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)

    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )

    assert construction["cells"] == track["beatCells"]
    assert construction["cells"] is not track["beatCells"]
    assert construction["sourceTrackReceiptSha256"] == track["trackReceiptSha256"]
    assert construction["sourceTopologySha256"] == track["topologySha256"]
    assert construction["coveredDurationMilliseconds"] == 2000
    assert construction["timingArtifactSha256"] == track["parentTimingBinding"]["timingSha256"]
    assert derived["cellStartsMilliseconds"] == [0, 1000]
    assert construction["officialBeatReceiptContractSha256"] == canonical_sha256(contract)
    stage1._validate_construction(
        construction,
        "construction",
        source_receipt_track=track,
        expected_track_id="synthetic",
    )


def test_constructor_rejects_covered_duration_and_contiguity_tamper(monkeypatch: pytest.MonkeyPatch) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    covered = deepcopy(track)
    covered["coveredDurationMilliseconds"] += 1
    with pytest.raises(stage1.BeatCellStage1Error, match="covered duration"):
        stage1.construct_beat_cells(
            covered,
            source_beat_receipt_file_sha256=file_sha256,
            source_beat_receipt_sha256=receipt["receiptSha256"],
        )
    gap = deepcopy(track)
    gap["beatCells"][1]["startMs"] += 1
    gap["beatCells"][1]["durationMilliseconds"] -= 1
    with pytest.raises(stage1.BeatCellStage1Error, match="contiguous"):
        stage1.construct_beat_cells(
            gap,
            source_beat_receipt_file_sha256=file_sha256,
            source_beat_receipt_sha256=receipt["receiptSha256"],
        )


def _summary_cell(cell: dict[str, Any], product: str | None) -> dict[str, Any]:
    duration = cell["durationMilliseconds"] / 1000
    return {
        "cellIndex": cell["beatIndex"],
        "sourceBeatCellSha256": canonical_sha256(cell),
        "startMilliseconds": cell["startMs"],
        "endMilliseconds": cell["endMs"],
        "durationMilliseconds": cell["durationMilliseconds"],
        "predictionProduct": product,
        "predictionCoveredDurationSeconds": 0.0 if product is None else duration,
        "predictionProductDurationSeconds": 0.0 if product is None else duration,
        "predictionCoverage": 0.0 if product is None else 1.0,
        "predictionDominance": 0.0 if product is None else 1.0,
    }


def test_scoring_uses_exact_beat_intervals_and_funnel_partitions(monkeypatch: pytest.MonkeyPatch) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    construction, _derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )
    outcomes, reconciliation = stage1.score_fixed_cells(
        {
            "durationSeconds": 2.0,
            "segments": [
                {"start": 0.0, "end": 1.0, "label": "C"},
                {"start": 1.0, "end": 2.0, "label": "D"},
            ],
        },
        {"durationSeconds": 2.0},
        construction,
        {"cells": [_summary_cell(construction["cells"][0], "C"), _summary_cell(construction["cells"][1], None)]},
    )
    assert reconciliation is None
    assert [(row["classification"], row["reason"]) for row in outcomes] == [("C", None), ("N", "predictionUncovered")]
    assert [row["beatIndex"] for row in outcomes] == [0, 1]
    funnel, _audit = stage1.funnel_from_outcomes(outcomes)
    assert funnel["counts"] == {"T": 2, "U": 0, "R": 2, "N": 1, "E": 1, "C": 1, "I": 0}
    assert funnel["durationMilliseconds"] == {
        "T": 2000,
        "U": 0,
        "R": 2000,
        "N": 1000,
        "E": 1000,
        "C": 1000,
        "I": 0,
    }


def test_prediction_summarizer_never_calls_parent_bar_summarizer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )

    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("parent-bar summarizer must never run")

    monkeypatch.setattr(stage1._bar_uncertainty, "summarize_prediction_bars", forbidden)
    summary = stage1.summarize_prediction_cells(
        {
            "id": "synthetic",
            "durationSeconds": 2.0,
            "segments": [
                {"start": 0.0, "end": 1.0, "label": "C", "productLabel": "C"},
                {"start": 1.0, "end": 2.0, "label": "D", "productLabel": "D"},
            ],
            "predictionCoreSha256": _digest("prediction-core"),
            "uncertaintySha256": _digest("uncertainty"),
        },
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("validation"),
    )
    assert [row["predictionProduct"] for row in summary["cells"]] == ["C", "D"]
    assert [row["sourceBeatCellSha256"] for row in summary["cells"]] == [
        canonical_sha256(row) for row in track["beatCells"]
    ]


@pytest.mark.parametrize(
    ("prediction_duration", "reference_end", "terminal_coverage"),
    [
        (1.9996, 1.99965, 0.9996),
        (2.0004, 2.00045, 1.0),
    ],
)
def test_player_rounded_up_and_down_terminal_endpoints_reconcile_within_exact_canonical_ms(
    monkeypatch: pytest.MonkeyPatch,
    prediction_duration: float,
    reference_end: float,
    terminal_coverage: float,
) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )
    prediction = {
        "id": "synthetic",
        "durationSeconds": prediction_duration,
        "segments": [{"start": 0.0, "end": prediction_duration, "label": "C", "productLabel": "C"}],
        "predictionCoreSha256": _digest("prediction-core"),
        "uncertaintySha256": _digest("uncertainty"),
    }
    summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("validation"),
    )
    outcomes, reconciliation = stage1.score_fixed_cells(
        {"segments": [{"start": 0.0, "end": reference_end, "label": "C"}]},
        prediction,
        construction,
        summary,
    )
    assert reconciliation == {
        "originalEnd": reference_end,
        "predictionDuration": prediction_duration,
        "reconciledEnd": prediction_duration,
        "reconciledSeconds": pytest.approx(reference_end - prediction_duration),
        "canonicalMs": 2000,
    }
    assert summary["cells"][-1]["predictionCoverage"] == pytest.approx(terminal_coverage)
    assert outcomes[-1]["classification"] == "C"


def test_endpoint_reconciliation_fails_closed_outside_player_canonical_millisecond(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )
    prediction = {
        "id": "synthetic",
        "durationSeconds": 1.9996,
        "segments": [{"start": 0.0, "end": 1.9996, "label": "C", "productLabel": "C"}],
        "predictionCoreSha256": _digest("prediction-core"),
        "uncertaintySha256": _digest("uncertainty"),
    }
    summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("validation"),
    )
    with pytest.raises(stage1.BeatCellStage1Error, match="outside the prediction canonical millisecond"):
        stage1.score_fixed_cells(
            {"segments": [{"start": 0.0, "end": 2.0006, "label": "C"}]},
            prediction,
            construction,
            summary,
        )


def test_lexical_ties_and_exact_or_sub_epsilon_overlap_slivers_are_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    track = _beat_track("synthetic")
    receipt, file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )
    summary = stage1.summarize_prediction_cells(
        {
            "id": "synthetic",
            "durationSeconds": 2.0,
            "segments": [
                {"start": 0.0, "end": 0.5, "label": "G", "productLabel": "G"},
                {"start": 0.5, "end": 1.0, "label": "C", "productLabel": "C"},
                {"start": 1.0, "end": 2.0, "label": "D", "productLabel": "D"},
            ],
            "predictionCoreSha256": _digest("prediction-core"),
            "uncertaintySha256": _digest("uncertainty"),
        },
        construction,
        derived,
        prediction_validation_audit_sha256=_digest("validation"),
    )
    assert summary["cells"][0]["predictionProduct"] == "C"
    assert stage1._bar_product._dominant_product({"G": 0.5, "C": 0.5}) == ("C", 0.5)
    for sliver, expected in ((0.9e-9, {}), (1e-9, {}), (1.1e-9, {"D": 1.1e-9})):
        overlaps, covered = stage1._bar_product._overlap_by_product(
            [{"start": 0.0, "end": sliver, "product": "D"}],
            0.0,
            1.0,
        )
        assert overlaps == expected
        assert covered == pytest.approx(sum(expected.values()))


@pytest.mark.parametrize(
    ("field", "delta", "expected"),
    [
        ("referenceCoverage", -1e-9, ("C", None)),
        ("referenceCoverage", -1.1e-9, ("U", "referenceUncovered")),
        ("referenceDominance", -1e-9, ("C", None)),
        ("referenceDominance", -1.1e-9, ("U", "referenceMixed")),
        ("predictionCoverage", -1e-9, ("C", None)),
        ("predictionCoverage", -1.1e-9, ("N", "predictionUncovered")),
        ("predictionDominance", -1e-9, ("C", None)),
        ("predictionDominance", -1.1e-9, ("N", "predictionMixed")),
    ],
)
def test_exact_epsilon_eligibility_floor(
    field: str,
    delta: float,
    expected: tuple[str, str | None],
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
    assert stage1._classification_from_evidence(evidence) == expected


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


def test_exact_thirteen_count_and_duration_gates_remain_frozen() -> None:
    aggregate, guitarset = _passing_funnels()
    gates = stage1.build_stage1_gates(aggregate, guitarset)
    assert len(gates) == 13
    assert all(gate["passed"] is True for gate in gates)
    assert gates[-1]["gateId"] == "guitarset.counts.minimumCorrectCellCount"
    empty = stage1.make_funnel(
        {field: 0 for field in stage1._FUNNEL_FIELDS},
        {field: 0 for field in stage1._FUNNEL_FIELDS},
    )
    assert not any(gate["passed"] for gate in stage1.build_stage1_gates(empty, empty))


def test_prediction_identity_projection_excludes_reference_and_metrics() -> None:
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
        "canonicalDurationMilliseconds": 2000,
        "audioLineageRowSha256": _digest("lineage"),
        "referenceSha256": _digest("reference"),
        "metrics": {"accuracy": 1.0},
    }
    identity = stage1._prediction_identity(source)
    assert "referenceSha256" not in identity
    assert "metrics" not in identity
    assert identity["id"] == "track-001"


def test_all_predictions_complete_before_reference_phase() -> None:
    events: list[str] = []

    def seal() -> tuple[list[str], dict[str, str]]:
        events.extend(["prediction:a", "prediction:b", "prediction:c"])
        return ["a", "b", "c"], {"binding": "sealed"}

    def references(records: list[str]) -> tuple[list[str], list[str]]:
        assert records == ["a", "b", "c"]
        assert events == ["prediction:a", "prediction:b", "prediction:c"]
        events.extend(["reference:a", "reference:b", "reference:c"])
        return records, []

    records, binding, rows, reconciliations = stage1._run_ordered_phases(seal, references)
    assert records == rows == ["a", "b", "c"]
    assert binding == {"binding": "sealed"}
    assert reconciliations == []
    assert events[:3] == ["prediction:a", "prediction:b", "prediction:c"]


def _all_correct_track(
    source_track: dict[str, Any],
    dataset_id: str,
    role: str,
    guitarset_role: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    track_id = source_track["trackId"]
    construction, _derived = stage1.construct_beat_cells(
        source_track,
        source_beat_receipt_file_sha256=stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"],
        source_beat_receipt_sha256=stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"],
    )
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
    outcomes = []
    for cell in construction["cells"]:
        seconds = cell["durationMilliseconds"] / 1000
        outcome = {
            "cellIndex": cell["beatIndex"],
            "sourceBeatCellSha256": canonical_sha256(cell),
            "beatIndex": cell["beatIndex"],
            "retainedBarIndex": cell["retainedBarIndex"],
            "pulseNumber": cell["pulseNumber"],
            "downbeatCandidate": cell["downbeatCandidate"],
            "durationMilliseconds": cell["durationMilliseconds"],
            "referenceProduct": "C",
            "referenceCoveredDurationSeconds": seconds,
            "referenceProductDurationSeconds": seconds,
            "referenceCoverage": 1.0,
            "referenceDominance": 1.0,
            "predictionProduct": "C",
            "predictionCoveredDurationSeconds": seconds,
            "predictionProductDurationSeconds": seconds,
            "predictionCoverage": 1.0,
            "predictionDominance": 1.0,
            "classification": "C",
            "reason": None,
        }
        outcomes.append(stage1._self_hashed(outcome, "rowSha256"))
    funnel, exclusions = stage1.funnel_from_outcomes(outcomes)
    summary_sha = _digest(f"summary:{track_id}")
    summary_path = str(Path("/sealed-beat-stage1-summaries") / stage1._summary_filename(track_id, summary_sha))
    projection_payload = {
        "trackId": track_id,
        "datasetId": dataset_id,
        "canonicalDurationMilliseconds": construction["canonicalDurationMilliseconds"],
        "sourceAudioSha256": _digest(f"audio:{track_id}"),
    }
    projection_row = stage1._self_hashed(projection_payload, "rowSha256")
    prediction_identity = stage1._self_hashed(
        {
            "id": track_id,
            "split": "development",
            "predictionFile": f"predictions/{track_id}.json",
            "predictionSha256": _digest(f"prediction-artifact:{track_id}"),
            "predictionCoreSha256": _digest(f"prediction-core:{track_id}"),
            "uncertaintySha256": _digest(f"uncertainty:{track_id}"),
            "sourceAudioSha256": projection_row["sourceAudioSha256"],
            "cachedFeatureArraySha256": _digest(f"cached-feature:{track_id}"),
            "freshFeatureArraySha256": _digest(f"fresh-feature:{track_id}"),
            "canonicalDurationMilliseconds": construction["canonicalDurationMilliseconds"],
            "audioLineageRowSha256": projection_row["rowSha256"],
        },
        "predictionIdentitySha256",
    )
    payload = {
        "trackId": track_id,
        "split": "development",
        "datasetId": dataset_id,
        "role": role,
        "guitarsetRole": guitarset_role,
        "confidenceGroupId": source_group["confidenceGroupId"],
        "sourceGroupTrack": source_group,
        "sourceGroupTrackMetadataSha256": source_group["trackMetadataSha256"],
        "predictionIdentity": prediction_identity,
        "predictionIdentitySha256": prediction_identity["predictionIdentitySha256"],
        "sourceBeatReceiptTrackSha256": source_track["trackReceiptSha256"],
        "sourceTopologySha256": source_track["topologySha256"],
        "timingArtifactSha256": construction["timingArtifactSha256"],
        "timingContractSha256": construction["timingContractSha256"],
        "timingSourceContractSha256": construction["timingSourceContractSha256"],
        "sourceReferenceSha256": source_group["referenceSha256"],
        "referenceEndpointReconciliationRowSha256": None,
        "predictionOnlySummary": {
            "path": summary_path,
            "pathSha256": canonical_sha256(summary_path),
            "artifactSha256": summary_sha,
        },
        "construction": construction,
        "constructionSha256": construction["constructionSha256"],
        "beatCount": construction["beatCount"],
        "cellCount": construction["cellCount"],
        "coveredDurationMilliseconds": construction["coveredDurationMilliseconds"],
        "cellOutcomes": outcomes,
        "cellOutcomeSetSha256": canonical_sha256(outcomes),
        "funnel": funnel,
        "funnelSha256": funnel["funnelSha256"],
        "exclusionAudit": exclusions,
        "exclusionAuditSha256": exclusions["auditSha256"],
    }
    return stage1._self_hashed(payload, "rowSha256"), projection_row


def _synthetic_valid_artifact(
    monkeypatch: pytest.MonkeyPatch,
    *,
    reconciliation_track_count: int = 0,
) -> dict[str, Any]:
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
    source_tracks = sorted((_beat_track(track_id) for track_id, *_rest in descriptors), key=lambda row: row["trackId"])
    receipt, file_sha256 = _receipt(source_tracks)
    beat_contract = _install_synthetic_beat_contract(monkeypatch, receipt, file_sha256)
    descriptor_by_id = {track_id: (dataset, role, guitar_role) for track_id, dataset, role, guitar_role in descriptors}
    pairs = [_all_correct_track(source, *descriptor_by_id[source["trackId"]]) for source in source_tracks]
    tracks = sorted((track for track, _projection in pairs), key=lambda row: row["trackId"])
    reconciliation_rows: list[dict[str, Any]] = []
    for track in tracks[:reconciliation_track_count]:
        reconciliation = stage1._self_hashed(
            {
                "trackId": track["trackId"],
                "datasetId": track["datasetId"],
                "referenceSha256": track["sourceReferenceSha256"],
                "originalEnd": 2.00045,
                "predictionDuration": 2.0004,
                "reconciledEnd": 2.0004,
                "reconciledSeconds": 0.00005,
                "canonicalMs": 2000,
            },
            "rowSha256",
        )
        track["referenceEndpointReconciliationRowSha256"] = reconciliation["rowSha256"]
        _rehash(track, "rowSha256")
        reconciliation_rows.append(reconciliation)
    projection_by_id = {row["trackId"]: row for _track, row in pairs}
    projection_rows = [projection_by_id[row["trackId"]] for row in tracks]
    projection = stage1._self_hashed(
        {
            "schemaVersion": "synthetic-audio-lineage-projection-v1",
            "trackCount": len(projection_rows),
            "tracks": projection_rows,
            "trackSetSha256": canonical_sha256(projection_rows),
        },
        "projectionSha256",
    )
    projection_tracks = {row["trackId"]: row for row in projection_rows}
    group_projection = {row["trackId"]: {"confidenceGroupId": row["confidenceGroupId"]} for row in tracks}
    audio_group_audit = bar_examples._audio_group_audit(
        [row["trackId"] for row in tracks], group_projection, projection_tracks
    )
    structural = stage1._structural_support_from_track_rows(tracks)
    monkeypatch.setattr(stage1, "OFFICIAL_STRUCTURAL_SUPPORT", structural)
    source_group_set = canonical_sha256(
        [{"trackId": row["trackId"], "trackMetadataSha256": row["sourceGroupTrackMetadataSha256"]} for row in tracks]
    )
    shared = deepcopy(stage1.STAGE1_SOURCE_CONTRACT["sharedPredictionRuntimeBinding"])
    shared.update(
        {
            "constructionPolicySha256": stage1.CONSTRUCTION_POLICY_SHA256,
            "officialBeatReceiptContractSha256": stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
            "beatAnalyzerContractSha256": beat_contract["beatAnalyzerContractSha256"],
            "playerReplayContractSha256": beat_contract["playerReplayContractSha256"],
            "timingSourceContractSha256": _digest("runtime-analyzer"),
        }
    )
    contract = deepcopy(stage1.STAGE1_SOURCE_CONTRACT)
    contract["trackCount"] = len(tracks)
    contract["beatReceipt"] = deepcopy(beat_contract)
    contract["structuralSupport"] = structural
    contract["sharedPredictionRuntimeBinding"] = shared
    contract["benchmarkReport"] = {
        "fileSha256": _digest("benchmark-file"),
        "canonicalSha256": _digest("benchmark-canonical"),
        "trackSetSha256": _digest("benchmark-track-set"),
        "predictionArtifactSetSha256": canonical_sha256(
            sorted(
                [{"id": row["trackId"], "sha256": row["predictionIdentity"]["predictionSha256"]} for row in tracks],
                key=lambda row: row["id"],
            )
        ),
        "predictionCoreSetSha256": canonical_sha256(
            sorted(
                [{"id": row["trackId"], "sha256": row["predictionIdentity"]["predictionCoreSha256"]} for row in tracks],
                key=lambda row: row["id"],
            )
        ),
        "uncertaintySetSha256": canonical_sha256(
            sorted(
                [{"id": row["trackId"], "sha256": row["predictionIdentity"]["uncertaintySha256"]} for row in tracks],
                key=lambda row: row["id"],
            )
        ),
        "predictionIdentitySetSha256": canonical_sha256(
            sorted(
                [
                    {
                        "trackId": row["trackId"],
                        "predictionIdentitySha256": row["predictionIdentitySha256"],
                    }
                    for row in tracks
                ],
                key=lambda row: row["trackId"],
            )
        ),
        "modelOrEnsembleSha256": shared["modelOrEnsembleSha256"],
    }
    contract["runtimeManifest"] = {
        "fileSha256": _digest("runtime-file"),
        "manifestSha256": receipt["parentRuntimeBinding"]["manifestSha256"],
        "trackSetSha256": receipt["parentRuntimeBinding"]["trackSetSha256"],
        "analyzerContractSha256": shared["timingSourceContractSha256"],
    }
    contract["groupManifest"] = {
        "fileSha256": _digest("group-file"),
        "manifestSha256": _digest("group-manifest"),
        "trackSetSha256": source_group_set,
    }
    contract["audioLineage"] = {
        "fileSha256": _digest("lineage-file"),
        "artifactSha256": _digest("lineage-artifact"),
        "projectionSha256": projection["projectionSha256"],
    }
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
    summary_root = "/sealed-beat-stage1-summaries"
    input_bindings = stage1._self_hashed(
        {
            "schemaVersion": "chord_runtime_beat_cell_stage1_input_bindings_v1",
            "benchmarkReport": {
                "path": "/sources/benchmark/report.json",
                "pathSha256": canonical_sha256("/sources/benchmark/report.json"),
                "fileSha256": contract["benchmarkReport"]["fileSha256"],
                "canonicalSha256": contract["benchmarkReport"]["canonicalSha256"],
                "claimedArtifactSha256": None,
                "trackSetSha256": contract["benchmarkReport"]["trackSetSha256"],
                "modelOrEnsembleSha256": contract["benchmarkReport"]["modelOrEnsembleSha256"],
                "predictionSets": prediction_sets,
            },
            "benchmarkRoot": {"path": "/sources/benchmark", "pathSha256": canonical_sha256("/sources/benchmark")},
            "runtimeManifest": {
                "path": "/sources/runtime/manifest.json",
                "pathSha256": canonical_sha256("/sources/runtime/manifest.json"),
                "fileSha256": contract["runtimeManifest"]["fileSha256"],
                "claimedArtifactSha256": contract["runtimeManifest"]["manifestSha256"],
                "trackSetSha256": contract["runtimeManifest"]["trackSetSha256"],
                "analyzerContractSha256": contract["runtimeManifest"]["analyzerContractSha256"],
            },
            "runtimeRoot": {"path": "/sources/runtime", "pathSha256": canonical_sha256("/sources/runtime")},
            "beatReceipt": {
                "path": "/sources/beat-receipt.json",
                "pathSha256": canonical_sha256("/sources/beat-receipt.json"),
                "fileSha256": beat_contract["fileSha256"],
                "canonicalSha256": canonical_sha256(receipt),
                "claimedArtifactSha256": beat_contract["receiptSha256"],
                "trackSetSha256": beat_contract["trackSetSha256"],
                "receiptTotalsSha256": beat_contract["receiptTotalsSha256"],
                "beatAnalyzerContractSha256": beat_contract["beatAnalyzerContractSha256"],
                "playerReplayContractSha256": beat_contract["playerReplayContractSha256"],
            },
            "groupManifest": {
                "path": "/sources/group-manifest.json",
                "pathSha256": canonical_sha256("/sources/group-manifest.json"),
                "fileSha256": contract["groupManifest"]["fileSha256"],
                "claimedArtifactSha256": contract["groupManifest"]["manifestSha256"],
                "trackSetSha256": contract["groupManifest"]["trackSetSha256"],
            },
            "groupRoot": {"path": "/sources/groups", "pathSha256": canonical_sha256("/sources/groups")},
            "audioLineage": {
                "path": "/sources/audio-lineage.json",
                "pathSha256": canonical_sha256("/sources/audio-lineage.json"),
                "fileSha256": contract["audioLineage"]["fileSha256"],
                "claimedArtifactSha256": contract["audioLineage"]["artifactSha256"],
                "projectionSha256": contract["audioLineage"]["projectionSha256"],
            },
            "summaryOutputRoot": {"path": summary_root, "pathSha256": canonical_sha256(summary_root)},
        },
        "bindingsSha256",
    )
    return stage1._build_artifact(
        input_bindings=input_bindings,
        publication={
            "mode": "atomic-new-json-and-summary-directory-set-v1",
            "outputPath": "/sealed-beat-stage1-output/artifact.json",
            "outputPathSha256": canonical_sha256("/sealed-beat-stage1-output/artifact.json"),
            "summaryOutputRoot": summary_root,
            "summaryOutputRootSha256": canonical_sha256(summary_root),
        },
        shared_binding=shared,
        source_beat_receipt=receipt,
        track_rows=tracks,
        projection_tracks=projection_tracks,
        audio_lineage_projection=projection,
        audio_group_audit=audio_group_audit,
        reconciliation_rows=reconciliation_rows,
    )


def test_standalone_validator_accepts_exact_resealed_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    assert stage1.validate_beat_cell_stage1_artifact(artifact) == artifact
    assert artifact["decision"]["gateCount"] == 13
    assert artifact["calibrationMayOpenOnce"] is False


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("sourceBeatReceiptSha256", "official receipt"),
        ("sourceBeatAnalyzerContractSha256", "analyzer"),
        ("sourcePlayerReplayContractSha256", "player"),
        ("timingArtifactSha256", "receipt track"),
    ],
)
def test_standalone_validator_rejects_refreshed_lineage_splices(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    message: str,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    track = tampered["tracks"][0]
    construction = track["construction"]
    construction[field] = _digest(f"tampered:{field}")
    if field in track:
        track[field] = construction[field]
    construction["derivedCellTimingContractSha256"] = canonical_sha256(
        stage1._derived_timing_payload_from_construction(construction)
    )
    _rehash(construction, "constructionSha256")
    track["constructionSha256"] = construction["constructionSha256"]
    _rehash(track, "rowSha256")
    tampered["trackSetSha256"] = canonical_sha256(tampered["tracks"])
    _rehash(tampered, "artifactSha256")
    with pytest.raises(stage1.BeatCellStage1Error, match=message):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def test_standalone_validator_rejects_rewritten_cells_after_outer_reseal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    track = tampered["tracks"][0]
    construction = track["construction"]
    construction["cells"][0]["retainedBarIndex"] = 7
    construction["cellSetSha256"] = canonical_sha256(construction["cells"])
    _rehash(construction, "constructionSha256")
    track["constructionSha256"] = construction["constructionSha256"]
    outcome = track["cellOutcomes"][0]
    outcome["retainedBarIndex"] = 7
    outcome["sourceBeatCellSha256"] = canonical_sha256(construction["cells"][0])
    _rehash(outcome, "rowSha256")
    track["cellOutcomeSetSha256"] = canonical_sha256(track["cellOutcomes"])
    _rehash(track, "rowSha256")
    tampered["trackSetSha256"] = canonical_sha256(tampered["tracks"])
    _rehash(tampered, "artifactSha256")
    with pytest.raises(stage1.BeatCellStage1Error, match="official receipt track"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def _reseal_input_bindings(artifact: dict[str, Any]) -> None:
    _rehash(artifact["inputBindings"], "bindingsSha256")
    artifact["inputBindingsSha256"] = canonical_sha256(artifact["inputBindings"])
    _rehash(artifact, "artifactSha256")


def _reseal_track_set(artifact: dict[str, Any], track: dict[str, Any]) -> None:
    _rehash(track, "rowSha256")
    artifact["trackSetSha256"] = canonical_sha256(artifact["tracks"])
    _rehash(artifact, "artifactSha256")


def test_standalone_validator_recomputes_derived_timing_digest_after_outer_reseal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    track = tampered["tracks"][0]
    construction = track["construction"]
    construction["derivedCellTimingContractSha256"] = _digest("replacement-derived-timing")
    _rehash(construction, "constructionSha256")
    track["constructionSha256"] = construction["constructionSha256"]
    _reseal_track_set(tampered, track)
    with pytest.raises(stage1.BeatCellStage1Error, match="derived cell-timing contract"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


@pytest.mark.parametrize("mutation", ("stale-path-hash", "extra-field"))
def test_standalone_validator_rejects_resealed_top_input_binding_shape_and_path_splices(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    binding = tampered["inputBindings"]["runtimeManifest"]
    if mutation == "stale-path-hash":
        binding["path"] = "/sources/runtime/resealed-manifest.json"
    else:
        binding["unsupportedSelectorClaim"] = True
    _reseal_input_bindings(tampered)
    with pytest.raises(stage1.BeatCellStage1Error, match="runtimeManifest"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def test_standalone_validator_rejects_bilateral_source_summary_root_nesting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    nested_runtime_root = "/sealed-beat-stage1-summaries/runtime-source"
    runtime_root = tampered["inputBindings"]["runtimeRoot"]
    runtime_root.update({"path": nested_runtime_root, "pathSha256": canonical_sha256(nested_runtime_root)})
    runtime_manifest_path = f"{nested_runtime_root}/manifest.json"
    runtime_manifest = tampered["inputBindings"]["runtimeManifest"]
    runtime_manifest.update({"path": runtime_manifest_path, "pathSha256": canonical_sha256(runtime_manifest_path)})
    _reseal_input_bindings(tampered)
    with pytest.raises(stage1.BeatCellStage1Error, match="disjoint from every source root"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


@pytest.mark.parametrize("mutation", ("extra-field", "funnel-digest"))
def test_standalone_validator_rejects_resealed_dataset_disclosure_splices(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    dataset = tampered["datasets"][0]
    if mutation == "extra-field":
        dataset["selectorEligible"] = True
    else:
        dataset["funnelSha256"] = _digest("replacement-dataset-funnel")
    _rehash(dataset, "rowSha256")
    tampered["datasetSetSha256"] = canonical_sha256(tampered["datasets"])
    _rehash(tampered, "artifactSha256")
    with pytest.raises(stage1.BeatCellStage1Error, match="Dataset disclosures"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def test_standalone_validator_rejects_duplicate_reconciliation_row_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch, reconciliation_track_count=2)
    assert stage1.validate_beat_cell_stage1_artifact(artifact) == artifact
    tampered = deepcopy(artifact)
    first, second = [row for row in tampered["tracks"] if row["referenceEndpointReconciliationRowSha256"] is not None]
    second["referenceEndpointReconciliationRowSha256"] = first["referenceEndpointReconciliationRowSha256"]
    _reseal_track_set(tampered, second)
    with pytest.raises(stage1.BeatCellStage1Error, match="exactly match the audit row set"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def test_standalone_validator_rejects_fully_resealed_prediction_identity_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    track = tampered["tracks"][0]
    identity = track["predictionIdentity"]
    identity["cachedFeatureArraySha256"] = _digest("substituted-cached-features")
    _rehash(identity, "predictionIdentitySha256")
    track["predictionIdentitySha256"] = identity["predictionIdentitySha256"]
    _reseal_track_set(tampered, track)
    with pytest.raises(stage1.BeatCellStage1Error, match="exact frozen candidate set"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def test_standalone_validator_rejects_resealed_guitarset_extra_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    tampered["guitarset"]["selectorCalibrationParity"] = True
    _rehash(tampered, "artifactSha256")
    with pytest.raises(stage1.BeatCellStage1Error, match="guitarset has unsupported or missing fields"):
        stage1.validate_beat_cell_stage1_artifact(tampered)


def test_selector_authorization_remains_false_at_every_stage1_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    assert stage1.STAGE1_RUBRIC["selectorUseAllowed"] is False
    assert artifact["selectorUseAllowed"] is False
    assert artifact["decision"]["selectorUseAllowed"] is False
    assert artifact["calibrationMayOpenOnce"] is False
    assert artifact["decision"]["calibrationMayOpenOnce"] is False


def test_top_binding_producer_omits_unsubstantiated_canonical_digest_when_requested() -> None:
    value = stage1._self_hashed({"schemaVersion": "synthetic"}, "manifestSha256")
    binding = stage1._top_binding(
        Path("/sources/runtime/manifest.json"),
        _canonical_raw(value),
        value,
        "manifestSha256",
        "runtime manifest",
        include_canonical_sha256=False,
    )
    assert set(binding) == {"path", "pathSha256", "fileSha256", "claimedArtifactSha256"}
    assert binding["pathSha256"] == canonical_sha256(binding["path"])


def _canonical_raw(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()


def _mock_top_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "benchmark report": {},
        "audio lineage": {},
        "runtime manifest": {},
        "group manifest": {},
        "beat receipt": {
            "split": "development",
            "developmentOnly": True,
            "referenceFree": True,
            "stage1UseAllowed": True,
            "selectorUseAllowed": False,
            "playerPlaybackUseAllowed": False,
        },
    }

    def read(_path: Path, name: str) -> tuple[dict[str, Any], bytes, object]:
        value = values[name]
        return deepcopy(value), _canonical_raw(value), object()

    monkeypatch.setattr(stage1, "_sealed_read_json", read)
    monkeypatch.setattr(stage1._examples, "_validate_development_envelopes", lambda *_args: None)
    monkeypatch.setattr(stage1, "_validate_official_source_contract", lambda *_args: None)


def test_output_inside_parent_runtime_root_fails_before_strict_leaf_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_top_inputs(monkeypatch)
    roots = [tmp_path / name for name in ("benchmark", "runtime", "group")]
    for root in roots:
        root.mkdir()
    strict_called = False

    def strict(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal strict_called
        strict_called = True
        return {}

    monkeypatch.setattr(stage1, "validate_runtime_beat_grid_receipt", strict)
    with pytest.raises(stage1.BeatCellStage1Error, match="disjoint from runtime_root"):
        stage1.run_beat_cell_stage1_preflight(
            tmp_path / "benchmark.json",
            benchmark_root=roots[0],
            audio_lineage_path=tmp_path / "audio.json",
            runtime_manifest_path=tmp_path / "runtime.json",
            runtime_root=roots[1],
            beat_receipt_path=tmp_path / "receipt.json",
            group_manifest_path=tmp_path / "group.json",
            group_root=roots[2],
            summary_output_root=tmp_path / "summaries",
            output_path=roots[1] / "new-stage1.json",
        )
    assert strict_called is False


def test_receipt_is_strictly_path_validated_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_top_inputs(monkeypatch)
    roots = [tmp_path / name for name in ("benchmark", "runtime", "group")]
    for root in roots:
        root.mkdir()
    receipt_path = tmp_path / "receipt.json"

    class StopAfterStrict(RuntimeError):
        pass

    def strict(receipt: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        assert kwargs["receipt_path"] == receipt_path
        assert kwargs["parent_runtime_root"] == roots[1]
        assert kwargs["verify_sources"] is True
        raise StopAfterStrict

    monkeypatch.setattr(stage1, "validate_runtime_beat_grid_receipt", strict)
    with pytest.raises(StopAfterStrict):
        stage1.run_beat_cell_stage1_preflight(
            tmp_path / "benchmark.json",
            benchmark_root=roots[0],
            audio_lineage_path=tmp_path / "audio.json",
            runtime_manifest_path=tmp_path / "runtime.json",
            runtime_root=roots[1],
            beat_receipt_path=receipt_path,
            group_manifest_path=tmp_path / "group.json",
            group_root=roots[2],
            summary_output_root=tmp_path / "summaries",
            output_path=tmp_path / "output" / "stage1.json",
        )


def test_atomic_summary_set_precommit_failure_leaves_no_visible_outputs(tmp_path: Path) -> None:
    output = tmp_path / "artifact.json"
    summaries = tmp_path / "summaries"

    def build(staging: Path) -> dict[str, Any]:
        (staging / "one.json").write_text("{}\n", encoding="utf-8")
        return {"schemaVersion": "synthetic"}

    def fail() -> None:
        raise RuntimeError("precommit")

    with pytest.raises(RuntimeError, match="precommit"):
        stage1._stage_and_publish_summary_set(output, summaries, build, fail)
    assert not output.exists()
    assert not summaries.exists()
