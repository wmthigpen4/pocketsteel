"""Sealed development-only feasibility preflight for exact runtime beat cells.

This stage asks only whether the independently frozen, reference-free target-
browser beat cells make enough correct chord support observable to justify a
later selector experiment.  It does not derive or alter boundaries, fit a
selector, choose a cutoff, inspect a protected split, or authorize calibration.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import tempfile
from typing import Any

from . import bar_examples as _examples
from . import bar_product as _bar_product
from . import bar_uncertainty as _bar_uncertainty
from .bar_promotion import benchmark_content_set_sha256, benchmark_track_set_sha256, canonical_sha256
from .runtime_bar_grid import validate_runtime_bar_grid_manifest
from .runtime_beat_grid import OUTPUT_RECEIPT_SCHEMA, validate_runtime_beat_grid_receipt
from .uncertainty import validate_factorized_uncertainty_contract
from .selector_readiness import (
    REVIEWED_DEVELOPMENT_GROUP_SHAPE,
    _absolute,
    _read_json as _sealed_read_json,
    _validate_reviewed_group_shape,
    _verify_input_unchanged,
)
from .selector_development import (
    _preflight_new_directory,
    _publish_json_and_summary_set,
    _require_disjoint_summary_root,
)


DEVELOPMENT_SPLIT = "development"
STAGE1_SCHEMA = "chord_runtime_beat_cell_stage1_preflight_v1"
CELL_SUMMARY_SCHEMA = "chord_runtime_beat_cell_prediction_summary_v1"
CELL_TIMING_SCHEMA = "chord_runtime_beat_cell_timing_v1"
FUNNEL_SCHEMA = "chord_runtime_beat_cell_observability_funnel_v1"
CONSTRUCTION_SCHEMA = "chord_runtime_beat_cell_construction_v1"
RUBRIC_SCHEMA = "chord_runtime_beat_cell_stage1_rubric_v1"

OFFICIAL_BEAT_RECEIPT_CONTRACT: dict[str, Any] = {
    "schemaVersion": "chord_runtime_beat_cell_stage1_receipt_contract_v1",
    "receiptSchemaVersion": OUTPUT_RECEIPT_SCHEMA,
    "fileSha256": "be09f0973aa2ad12c626890f3c7015a50faf7ee24fefe4297ee44f14c79b2053",
    "receiptSha256": "4f14ed0a3b3436ea8cdd50ae5fef77d0b086efc96c4ec8ec8e7a9af11814834b",
    "trackSetSha256": "a2de02b7419753d41a0ad1e6e85ca14ae5877fc93c2dc7847508ccc7ac004602",
    "receiptTotalsSha256": "46c68e5de9b2cadbe7f0abc03e9a3faaf036d8b06db93f8998a1c0067c448e4a",
    "receiptTotals": {
        "trackCount": 246,
        "beatCellCount": 11234,
        "sourceDurationMilliseconds": 6443258,
        "coveredDurationMilliseconds": 6201472,
        "excludedPrefixDurationMilliseconds": 241786,
    },
    "beatAnalyzerContractSha256": "9f8477192a97ea7c5c40688fcbfb9a084bf852f6e4e36055497a2647961d9c7f",
    "playerReplayContractSha256": "d6ff183f534a36f54aa5623fb1057b42689823357b4aca56bac88e3b6d614ae8",
    "parentRuntimeManifestSha256": "e717f8b2c44f41fc7cd9557796b701225e82d3e2f5e40b66365a21b406f65ab1",
    "parentRuntimeTrackSetSha256": "a9ba75338abeb6fad9c6e91adb14f4be74dcdaac6a2241afcc7efddfbe6cd0cd",
    "referenceFree": True,
    "stage1UseAllowed": True,
    "selectorUseAllowed": False,
    "playerPlaybackUseAllowed": False,
}
OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256 = canonical_sha256(OFFICIAL_BEAT_RECEIPT_CONTRACT)

CONSTRUCTION_POLICY: dict[str, Any] = {
    "schemaVersion": "chord_runtime_beat_cell_construction_policy_v1",
    "source": "exact independently frozen reference-free runtime beat receipt beatCells",
    "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
    "boundaryInputs": "receipt beatCells startMs/endMs only; no seconds conversion and no recomputation",
    "cellsPerBeat": 1,
    "minimumCellDurationMilliseconds": 1,
    "identityRule": "copy every exact receipt beatCells row unchanged and bind its source row hash",
    "partitionRule": "one positive contiguous [startMs,endMs) cell per receipt beat through canonical duration",
    "prefixRule": "first cell starts at exact receipt prefixExcludedMilliseconds",
    "terminalRule": "last cell ends at exact receipt durationMilliseconds",
    "claimScope": (
        "development-only structural challenger using exact target-browser beat topology; receipt and current "
        "tracked player resources do not authorize playback or selector publication"
    ),
    "endpointRule": (
        "score every cell on exactly [startMs/1000,endMs/1000); clip excess evidence at cell end and count any "
        "rounded-up runtime tail without evidence as uncovered"
    ),
    "forbiddenBoundaryInputs": [
        "chord reference",
        "prediction segments",
        "uncertainty",
        "correctness",
        "selector output",
    ],
}
CONSTRUCTION_POLICY_SHA256 = canonical_sha256(CONSTRUCTION_POLICY)

SCORING_POLICY: dict[str, Any] = {
    "schemaVersion": "chord_runtime_beat_cell_scoring_policy_v1",
    "cellInterval": "[startMilliseconds/1000,endMilliseconds/1000)",
    "referenceDominance": 0.75,
    "predictionCoverage": 0.75,
    "predictionDominance": 0.75,
    "comparisonEpsilon": 1e-9,
    "eligibilityComparison": "observed + comparisonEpsilon < required => excluded",
    "overlap": "max(0,min(cellEnd,segmentEnd)-max(cellStart,segmentStart))",
    "overlapInclusion": "overlap <= comparisonEpsilon is ignored, matching the frozen bar-product helper",
    "coveredDuration": "sum of nonoverlapping segment overlap durations",
    "floatingPointClamp": "covered duration is clamped to [0,cellDuration], product duration to [0,covered], and ratios to [0,1]",
    "dominantProduct": "maximum summed product overlap; exact ties choose lexicographically smallest canonical product",
    "referenceDominanceDenominator": "full canonical-ms cell duration",
    "predictionDominanceDenominator": "covered prediction duration",
    "correctness": "predictionProduct == referenceProduct",
    "roundedEndpoint": (
        "terminal evidence is clipped by the exact cell interval; a rounded-up evidence-free tail is uncovered"
    ),
}
SCORING_POLICY_SHA256 = canonical_sha256(SCORING_POLICY)

_OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD: dict[str, Any] = {
    "schemaVersion": "chord_runtime_beat_cell_official_structural_support_v1",
    "derivation": (
        "sum exact frozen receipt beatCount and coveredDurationMilliseconds after joining each receipt track "
        "to its exact group-manifest dataset and role; computed before any reference leaf is opened"
    ),
    "performanceExpectation": False,
    "aggregate": {"fixedCellCount": 11234, "fixedCellDurationMilliseconds": 6201472},
    "datasets": [
        {"datasetId": "aam", "fixedCellCount": 545, "fixedCellDurationMilliseconds": 295509},
        {"datasetId": "guitarset", "fixedCellCount": 2392, "fixedCellDurationMilliseconds": 1133524},
        {"datasetId": "idmt_guitar", "fixedCellCount": 2231, "fixedCellDurationMilliseconds": 1293968},
        {"datasetId": "nrgcp", "fixedCellCount": 4203, "fixedCellDurationMilliseconds": 2368023},
        {"datasetId": "winterreise", "fixedCellCount": 1863, "fixedCellDurationMilliseconds": 1110448},
    ],
    "guitarsetRoles": [
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
    ],
}
OFFICIAL_STRUCTURAL_SUPPORT: dict[str, Any] = {
    **_OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD,
    "supportSha256": canonical_sha256(_OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD),
}

STAGE1_RUBRIC: dict[str, Any] = {
    "schemaVersion": RUBRIC_SCHEMA,
    "split": DEVELOPMENT_SPLIT,
    "developmentOnly": True,
    "promotionEligible": False,
    "selectorFitted": False,
    "selectorUseAllowed": False,
    "operatingThreshold": None,
    "eligibility": deepcopy(_examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT),
    "eligibilitySha256": _examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    "officialBeatReceiptContract": deepcopy(OFFICIAL_BEAT_RECEIPT_CONTRACT),
    "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
    "scoringPolicy": deepcopy(SCORING_POLICY),
    "scoringPolicySha256": SCORING_POLICY_SHA256,
    "funnelDefinitions": {
        "T": "all exact frozen runtime beat cells",
        "U": "reference-indeterminate cells",
        "R": "reference-determinate cells = T-U",
        "N": "prediction-noneligible cells within R",
        "E": "prediction-eligible cells = R-N",
        "C": "correct-product cells within E",
        "I": "incorrect-product cells within E = E-C",
        "partitions": ["T=U+R", "R=N+E", "E=C+I", "T=U+N+C+I"],
    },
    "rateDefinitions": {
        "referenceDeterminacy": "R/T",
        "predictionEligibility": "E/R",
        "oracleEndToEndCorrectSupportUpperBound": (
            "C/R; a structural upper bound on correct support for any later selector, never precision or deployable accuracy"
        ),
        "correctShareAmongEligibleDisclosure": "C/E; disclosure only and never a Stage-1 gate",
    },
    "gateArithmetic": "integer cross-products only; a zero denominator fails",
    "aggregate": {"R/T": "at least 3/4", "E/R": "at least 3/4", "C/R": "at least 1/2"},
    "guitarset": {
        "R/T": "at least 3/4",
        "E/R": "at least 3/4",
        "C/R": "at least 1/4",
        "minimumCorrectCellCount": 30,
    },
    "weightings": ["cell count", "canonical cell duration milliseconds"],
    "guitarsetCompSolo": "mandatory count-and-duration disclosure only; no role-specific gate",
    "decision": "all 13 fixed gates pass => Stage 2 may be proposed in a new sealed development cycle; calibration remains closed",
}
STAGE1_RUBRIC_SHA256 = canonical_sha256(STAGE1_RUBRIC)

STAGE1_SOURCE_CONTRACT: dict[str, Any] = {
    "schemaVersion": "chord_runtime_beat_cell_stage1_official_source_contract_v1",
    "split": DEVELOPMENT_SPLIT,
    "candidate": "winner-seven-selector-development-v1",
    "trackCount": 246,
    "confidenceGroupCount": 169,
    "benchmarkReport": {
        "fileSha256": "fd9dcf2d36214816fe86282a5dc1f0511b05e32a6eecb419fd710d45bba1ed31",
        "canonicalSha256": "225cbd84d8bccd3260c35ac94388079128ae287992e02e6b109bb04ec402cb14",
        "trackSetSha256": "ae899ddb197de35a63031a6d2a7d4becee76cbb43b697060369c2df9b3c0370e",
        "predictionArtifactSetSha256": "03f3995d16f37400d2ff7e88dea29780f962077205b17fd858770429fc9eb5d1",
        "predictionCoreSetSha256": "92c92e1ec13e2e3edf88fcb5ed41f9e92741a64654478665c049b535438750ae",
        "uncertaintySetSha256": "9d199449763d2206c404b753f8b4961388fd24400d4cc3cfb4dbf0d149342e5a",
        "predictionIdentitySetSha256": "aa6471a3de97ce33f4e2d8f7faaea3d6dd0197e49f2318e17a6917b4a5e38e8e",
        "modelOrEnsembleSha256": "da73df511651230a5e8ef827c05aefb117710770ee4f994507354747058baedd",
    },
    "runtimeManifest": {
        "fileSha256": "9c7c171227610a6364f37888f33b3a98d5f8c16d95fe193416e5e4aee18a37f8",
        "manifestSha256": "e717f8b2c44f41fc7cd9557796b701225e82d3e2f5e40b66365a21b406f65ab1",
        "trackSetSha256": "a9ba75338abeb6fad9c6e91adb14f4be74dcdaac6a2241afcc7efddfbe6cd0cd",
        "analyzerContractSha256": "8e1df05daf18371899e06884006403b56a4228109687a6c7ca178f1621fef89e",
    },
    "beatReceipt": deepcopy(OFFICIAL_BEAT_RECEIPT_CONTRACT),
    "groupManifest": {
        "fileSha256": "e33e2054c06fa04b8c7333708c73183731475a8d51e0ea6612390e27a201d558",
        "manifestSha256": "92ae8ad59468c46d469fd0040ccfda12ef6404aa20578715465fb812890f86a4",
        "trackSetSha256": "16bea714365fcfe5f1c317dbe69a51f51d47cb2cc3435577dc736a482a0e558c",
    },
    "audioLineage": {
        "fileSha256": "1e5665dca03f415d81026ba0ae4991d8c663c2d97f5ee4b1046f96ac738f3cd8",
        "artifactSha256": "0359c8eba22f62e7d3318b4bc677f4c6a3d87619dd053c1eeba737cfcfc70072",
        "projectionSha256": "d1f480348a13e358f66c6ce035eb004724c6ae1fb356afcbfe601753b5bb33d7",
    },
    "reviewedDatasetShape": {
        "sourceArtifactSha256": "f196611dcbf4cdc825fe1da83a6f552296d331845e8352dae6e293a385e5568e",
        "datasetSetSha256": "c1c0b99c817b41ea6e49ec86974d9eda8d4c0c11903b51ec0b84cb4af9c00e9c",
        "shape": deepcopy(REVIEWED_DEVELOPMENT_GROUP_SHAPE),
        "shapeSha256": canonical_sha256(REVIEWED_DEVELOPMENT_GROUP_SHAPE),
    },
    "structuralSupport": deepcopy(OFFICIAL_STRUCTURAL_SUPPORT),
    "sharedPredictionRuntimeBinding": {
        "schemaVersion": "chord_runtime_beat_cell_prediction_runtime_binding_v1",
        "uncertaintyContractSha256": "55dae3ecb81a97e725466b597aa892e031a33f6cbc7285a39bee1316af2d46b7",
        "modelOrEnsembleSha256": "da73df511651230a5e8ef827c05aefb117710770ee4f994507354747058baedd",
        "decoderContractSha256": "e27f1fb84b30c2c377ceaabae7fabf5015b10de641ce81ea679d87dd416890a9",
        "memberOrderSha256": "04abb855199e4b1358349a0ac220683a62a33467cc851f83f937b77a6071a4cc",
        "sourceFeatureKind": "multiband_chroma_v2",
        "sourceFeatureSpecSha256": "938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65",
        "observabilityProfileSchemaVersion": "chord_existing_feature_matrix_observability_v1",
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "scoringPolicySha256": SCORING_POLICY_SHA256,
        "barOutcomeEligibilityContractSha256": _examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
        "timingSourceContractSha256": "8e1df05daf18371899e06884006403b56a4228109687a6c7ca178f1621fef89e",
        "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
        "beatAnalyzerContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT["beatAnalyzerContractSha256"],
        "playerReplayContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT["playerReplayContractSha256"],
    },
}
STAGE1_SOURCE_CONTRACT_SHA256 = canonical_sha256(STAGE1_SOURCE_CONTRACT)

_FUNNEL_FIELDS = ("T", "U", "R", "N", "E", "C", "I")
_RATE_FIELDS = (
    ("referenceDeterminacy", "R", "T"),
    ("predictionEligibility", "E", "R"),
    ("oracleEndToEndCorrectSupportUpperBound", "C", "R"),
    ("correctShareAmongEligibleDisclosure", "C", "E"),
)
_HEX = frozenset("0123456789abcdef")


class BeatCellStage1Error(ValueError):
    """A fixed-cell Stage-1 input or invariant failed closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BeatCellStage1Error(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise BeatCellStage1Error(f"{name} must be an array.")
    return value


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BeatCellStage1Error(f"{name} must be an integer of at least {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BeatCellStage1Error(f"{name} must be finite.")
    result = float(value)
    if not math.isfinite(result):
        raise BeatCellStage1Error(f"{name} must be finite.")
    return result


def _sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise BeatCellStage1Error(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _player_ms(seconds: Any, name: str) -> int:
    value = _finite(seconds, name)
    if value < 0:
        raise BeatCellStage1Error(f"{name} must be nonnegative.")
    return math.floor(value * 1000 + 0.5)


def _exact_ms(seconds: Any, name: str) -> int:
    value = _finite(seconds, name)
    if value < 0:
        raise BeatCellStage1Error(f"{name} must be nonnegative.")
    try:
        milliseconds = Decimal(str(seconds)) * Decimal(1000)
    except (InvalidOperation, ValueError) as error:
        raise BeatCellStage1Error(f"{name} must be an exact decimal millisecond boundary.") from error
    integral = milliseconds.to_integral_value()
    if milliseconds != integral:
        raise BeatCellStage1Error(f"{name} must already be an exact integer-millisecond boundary.")
    return int(integral)


def _self_hashed(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {**payload, field: canonical_sha256(payload)}


def _validate_self_hash(value: Mapping[str, Any], field: str, name: str) -> None:
    claimed = _sha(value.get(field), f"{name}.{field}")
    if canonical_sha256({key: item for key, item in value.items() if key != field}) != claimed:
        raise BeatCellStage1Error(f"{name} has a stale {field}.")


def _exact_fields(value: Mapping[str, Any], expected: set[str] | frozenset[str], name: str) -> None:
    if set(value) != set(expected):
        raise BeatCellStage1Error(f"{name} has unsupported or missing fields.")


def _derived_timing_payload_from_construction(construction: Mapping[str, Any]) -> dict[str, Any]:
    cells = list(_sequence(construction.get("cells"), "construction.cells"))
    return {
        "schemaVersion": CELL_TIMING_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "runtimeAnalyzerOutput": False,
        "sourceBeatReceiptFileSha256": construction["sourceBeatReceiptFileSha256"],
        "sourceBeatReceiptSha256": construction["sourceBeatReceiptSha256"],
        "sourceTrackReceiptSha256": construction["sourceTrackReceiptSha256"],
        "sourceTopologySha256": construction["sourceTopologySha256"],
        "timingArtifactSha256": construction["timingArtifactSha256"],
        "timingContractSha256": construction["timingContractSha256"],
        "timingSourceContractSha256": construction["timingSourceContractSha256"],
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
        "canonicalDurationMilliseconds": construction["canonicalDurationMilliseconds"],
        "prefixMilliseconds": construction["prefixMilliseconds"],
        "cellStartsMilliseconds": [int(_mapping(row, "construction cell")["startMs"]) for row in cells],
        "provenance": {
            "sourceClass": "exact-copy-of-attested-runtime-beat-receipt-cells",
            "boundaryInputs": CONSTRUCTION_POLICY["boundaryInputs"],
            "identityRule": CONSTRUCTION_POLICY["identityRule"],
            "referenceFree": True,
            "claimScope": CONSTRUCTION_POLICY["claimScope"],
            "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
        },
    }


def construct_beat_cells(
    receipt_track: Mapping[str, Any],
    *,
    source_beat_receipt_file_sha256: str = OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"],
    source_beat_receipt_sha256: str = OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Copy one exact receipt beat cell per beat without recomputing boundaries."""

    source = _mapping(receipt_track, "beat receipt track")
    track_id = source.get("trackId")
    if not isinstance(track_id, str) or not track_id:
        raise BeatCellStage1Error("Beat receipt track requires a nonempty trackId.")
    source_receipt_file_sha256 = _sha(source_beat_receipt_file_sha256, "beat receipt file SHA-256")
    source_receipt_sha256 = _sha(source_beat_receipt_sha256, "beat receipt SHA-256")
    if (
        source_receipt_file_sha256 != OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"]
        or source_receipt_sha256 != OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"]
    ):
        raise BeatCellStage1Error("Beat construction is not bound to the exact official receipt.")
    duration_ms = _integer(source.get("durationMilliseconds"), "receipt track.durationMilliseconds", minimum=1)
    prefix_ms = _integer(source.get("prefixExcludedMilliseconds"), "receipt track.prefixExcludedMilliseconds")
    covered_ms = _integer(
        source.get("coveredDurationMilliseconds"), "receipt track.coveredDurationMilliseconds", minimum=1
    )
    raw_cells = list(_sequence(source.get("beatCells"), "receipt track.beatCells"))
    beat_count = _integer(source.get("beatCount"), "receipt track.beatCount", minimum=1)
    if len(raw_cells) != beat_count:
        raise BeatCellStage1Error("Receipt beatCount does not equal the exact beatCells length.")
    cells: list[dict[str, Any]] = []
    expected_fields = {
        "beatIndex",
        "retainedBarIndex",
        "pulseNumber",
        "downbeatCandidate",
        "startMs",
        "endMs",
        "durationMilliseconds",
    }
    previous_end: int | None = None
    for index, raw_cell in enumerate(raw_cells):
        cell = dict(_mapping(raw_cell, f"receipt track.beatCells[{index}]"))
        _exact_fields(cell, expected_fields, f"receipt track.beatCells[{index}]")
        start_ms = _integer(cell.get("startMs"), f"receipt beat cell {index}.startMs")
        end_ms = _integer(cell.get("endMs"), f"receipt beat cell {index}.endMs", minimum=1)
        if (
            cell.get("beatIndex") != index
            or isinstance(cell.get("downbeatCandidate"), bool) is False
            or _integer(cell.get("retainedBarIndex"), f"receipt beat cell {index}.retainedBarIndex") < 0
            or _integer(cell.get("pulseNumber"), f"receipt beat cell {index}.pulseNumber", minimum=1) < 1
            or end_ms <= start_ms
            or cell.get("durationMilliseconds") != end_ms - start_ms
            or (previous_end is not None and start_ms != previous_end)
        ):
            raise BeatCellStage1Error("Receipt beatCells are not exact positive contiguous source rows.")
        previous_end = end_ms
        cells.append(cell)
    if cells[0]["startMs"] != prefix_ms or cells[-1]["endMs"] != duration_ms:
        raise BeatCellStage1Error("Receipt beatCells do not preserve exact prefix-to-duration coverage.")
    if sum(int(row["durationMilliseconds"]) for row in cells) != covered_ms or covered_ms != duration_ms - prefix_ms:
        raise BeatCellStage1Error("Receipt beatCells do not preserve exact covered duration.")
    parent_timing = _mapping(source.get("parentTimingBinding"), "receipt track.parentTimingBinding")
    timing_artifact_sha256 = _sha(parent_timing.get("timingSha256"), "parent timingSha256")
    timing_contract_sha256 = _sha(parent_timing.get("timingContractSha256"), "parent timingContractSha256")
    timing_source_contract_sha256 = _sha(
        parent_timing.get("timingSourceContractSha256"), "parent timingSourceContractSha256"
    )
    source_track_receipt_sha256 = _sha(source.get("trackReceiptSha256"), "trackReceiptSha256")
    source_topology_sha256 = _sha(source.get("topologySha256"), "topologySha256")
    source_beat_analyzer_contract_sha256 = _sha(source.get("beatAnalyzerContractSha256"), "beatAnalyzerContractSha256")
    source_player_replay_contract_sha256 = _sha(source.get("playerReplayContractSha256"), "playerReplayContractSha256")
    if (
        source_beat_analyzer_contract_sha256 != OFFICIAL_BEAT_RECEIPT_CONTRACT["beatAnalyzerContractSha256"]
        or source_player_replay_contract_sha256 != OFFICIAL_BEAT_RECEIPT_CONTRACT["playerReplayContractSha256"]
    ):
        raise BeatCellStage1Error("Receipt track changed its exact analyzer/player replay binding.")

    construction_payload: dict[str, Any] = {
        "schemaVersion": CONSTRUCTION_SCHEMA,
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
        "sourceBeatReceiptFileSha256": source_receipt_file_sha256,
        "sourceBeatReceiptSha256": source_receipt_sha256,
        "sourceTrackReceiptSha256": source_track_receipt_sha256,
        "sourceTopologySha256": source_topology_sha256,
        "sourceBeatAnalyzerContractSha256": source_beat_analyzer_contract_sha256,
        "sourcePlayerReplayContractSha256": source_player_replay_contract_sha256,
        "timingArtifactSha256": timing_artifact_sha256,
        "timingContractSha256": timing_contract_sha256,
        "timingSourceContractSha256": timing_source_contract_sha256,
        "beatCount": beat_count,
        "cellCount": len(cells),
        "prefixMilliseconds": prefix_ms,
        "canonicalDurationMilliseconds": duration_ms,
        "coveredDurationMilliseconds": covered_ms,
        "cells": cells,
        "cellSetSha256": canonical_sha256(cells),
        "identities": {
            "exactSourceRowsPreserved": cells == raw_cells,
            "oneCellPerBeat": len(cells) == beat_count,
            "allCellsNonempty": True,
            "allCellsContiguous": True,
            "prefixPreserved": True,
            "terminalDurationPreserved": True,
            "cellDurationSumEqualsReceiptCoveredDuration": True,
        },
    }
    derived_payload = _derived_timing_payload_from_construction(construction_payload)
    derived_timing = _self_hashed(derived_payload, "contractSha256")

    construction_payload["derivedCellTimingContractSha256"] = derived_timing["contractSha256"]
    construction = _self_hashed(construction_payload, "constructionSha256")
    return construction, derived_timing


def summarize_prediction_cells(
    prediction: Mapping[str, Any],
    construction: Mapping[str, Any],
    derived_timing: Mapping[str, Any],
    *,
    prediction_validation_audit_sha256: str,
) -> dict[str, Any]:
    """Summarize predictions on exact canonical-ms intervals, without a bar-grid adapter."""

    value = _mapping(prediction, "prediction")
    _validate_construction(construction, "cell construction")
    _validate_self_hash(derived_timing, "contractSha256", "derived cell timing")
    if (
        derived_timing.get("schemaVersion") != CELL_TIMING_SCHEMA
        or derived_timing.get("runtimeAnalyzerOutput") is not False
        or derived_timing.get("referenceFree") is not True
        or derived_timing.get("constructionPolicySha256") != CONSTRUCTION_POLICY_SHA256
        or derived_timing.get("officialBeatReceiptContractSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256
        or derived_timing.get("contractSha256") != construction.get("derivedCellTimingContractSha256")
    ):
        raise BeatCellStage1Error("Derived cell timing does not bind the frozen construction.")
    duration = _finite(value.get("durationSeconds"), "prediction.durationSeconds")
    if duration <= 0:
        raise BeatCellStage1Error("Prediction duration must be positive.")
    segments = _bar_uncertainty._prediction_segments(value, duration)
    cells: list[dict[str, Any]] = []
    for index, raw_cell in enumerate(_sequence(construction.get("cells"), "construction.cells")):
        cell = _mapping(raw_cell, f"construction.cells[{index}]")
        start_ms = _integer(cell.get("startMs"), "cell.startMs")
        end_ms = _integer(cell.get("endMs"), "cell.endMs", minimum=1)
        start = start_ms / 1000
        end = end_ms / 1000
        overlaps, covered = _bar_product._overlap_by_product(segments, start, end)
        product, product_duration = _bar_product._dominant_product(overlaps)
        interval_duration = (end_ms - start_ms) / 1000
        covered = min(interval_duration, max(0.0, covered))
        product_duration = min(covered, max(0.0, product_duration))
        coverage = min(1.0, max(0.0, covered / interval_duration))
        dominance = min(1.0, max(0.0, product_duration / covered)) if covered > 1e-9 else 0.0
        payload = {
            "cellIndex": index,
            "sourceBeatCellSha256": canonical_sha256(cell),
            "startMilliseconds": start_ms,
            "endMilliseconds": end_ms,
            "durationMilliseconds": end_ms - start_ms,
            "interval": "[startMilliseconds/1000,endMilliseconds/1000)",
            "predictionProduct": product,
            "predictionCoveredDurationSeconds": covered,
            "predictionProductDurationSeconds": product_duration,
            "predictionCoverage": coverage,
            "predictionDominance": dominance,
        }
        cells.append(_self_hashed(payload, "rowSha256"))
    payload = {
        "schemaVersion": CELL_SUMMARY_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "runtimeAnalyzerOutput": False,
        "trackId": value.get("id"),
        "predictionDurationSeconds": duration,
        "canonicalRuntimeDurationMilliseconds": construction["canonicalDurationMilliseconds"],
        "sourcePredictionCoreSha256": _sha(value.get("predictionCoreSha256"), "predictionCoreSha256"),
        "sourceUncertaintySha256": _sha(value.get("uncertaintySha256"), "uncertaintySha256"),
        "predictionValidationAuditSha256": _sha(
            prediction_validation_audit_sha256, "prediction validation auditSha256"
        ),
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "scoringPolicySha256": SCORING_POLICY_SHA256,
        "constructionSha256": construction["constructionSha256"],
        "derivedCellTimingContractSha256": derived_timing["contractSha256"],
        "cells": cells,
        "cellSetSha256": canonical_sha256(cells),
    }
    return _self_hashed(payload, "summarySha256")


def _empty_measure() -> dict[str, int]:
    return {field: 0 for field in _FUNNEL_FIELDS}


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": None if denominator == 0 else numerator / denominator,
        "hasSupport": denominator > 0,
    }


def make_funnel(counts: Mapping[str, Any], duration_milliseconds: Mapping[str, Any]) -> dict[str, Any]:
    """Build a self-hashed count and exact-canonical-duration funnel."""

    measures: dict[str, dict[str, int]] = {}
    for name, raw in (("counts", counts), ("durationMilliseconds", duration_milliseconds)):
        source = _mapping(raw, name)
        values = {field: _integer(source.get(field), f"{name}.{field}") for field in _FUNNEL_FIELDS}
        if not (
            values["T"] == values["U"] + values["R"]
            and values["R"] == values["N"] + values["E"]
            and values["E"] == values["C"] + values["I"]
            and values["T"] == values["U"] + values["N"] + values["C"] + values["I"]
        ):
            raise BeatCellStage1Error(f"{name} does not satisfy the exact T/U/R/N/E/C/I partitions.")
        measures[name] = values
    rates = {
        weighting: {
            rate_name: _ratio(values[numerator], values[denominator])
            for rate_name, numerator, denominator in _RATE_FIELDS
        }
        for weighting, values in measures.items()
    }
    payload = {
        "schemaVersion": FUNNEL_SCHEMA,
        **measures,
        "rates": rates,
        "identitiesReconciled": True,
    }
    return _self_hashed(payload, "funnelSha256")


def _add_measure(target: dict[str, int], source: Mapping[str, Any]) -> None:
    for field in _FUNNEL_FIELDS:
        target[field] += _integer(source.get(field), f"funnel.{field}")


def _sum_funnels(funnels: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _empty_measure()
    duration = _empty_measure()
    for funnel in funnels:
        _add_measure(counts, _mapping(funnel.get("counts"), "funnel.counts"))
        _add_measure(duration, _mapping(funnel.get("durationMilliseconds"), "funnel.durationMilliseconds"))
    return make_funnel(counts, duration)


def _gate(
    gate_id: str,
    funnel: Mapping[str, Any],
    weighting: str,
    numerator: str,
    denominator: str,
    required_numerator: int,
    required_denominator: int,
) -> dict[str, Any]:
    measure = _mapping(funnel.get(weighting), f"funnel.{weighting}")
    observed_numerator = _integer(measure.get(numerator), f"{gate_id}.numerator")
    observed_denominator = _integer(measure.get(denominator), f"{gate_id}.denominator")
    left = required_denominator * observed_numerator
    right = required_numerator * observed_denominator
    payload = {
        "gateId": gate_id,
        "weighting": weighting,
        "ratio": f"{numerator}/{denominator}",
        "observedNumerator": observed_numerator,
        "observedDenominator": observed_denominator,
        "requiredNumerator": required_numerator,
        "requiredDenominator": required_denominator,
        "crossProductLeft": left,
        "crossProductRight": right,
        "passed": observed_denominator > 0 and left >= right,
    }
    return _self_hashed(payload, "gateSha256")


def build_stage1_gates(aggregate: Mapping[str, Any], guitarset: Mapping[str, Any]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    specifications = (
        ("aggregate", aggregate, "referenceDeterminacy", "R", "T", 3, 4),
        ("aggregate", aggregate, "predictionEligibility", "E", "R", 3, 4),
        ("aggregate", aggregate, "oracleCorrectSupportUpperBound", "C", "R", 1, 2),
        ("guitarset", guitarset, "referenceDeterminacy", "R", "T", 3, 4),
        ("guitarset", guitarset, "predictionEligibility", "E", "R", 3, 4),
        ("guitarset", guitarset, "oracleCorrectSupportUpperBound", "C", "R", 1, 4),
    )
    for scope, funnel, name, numerator, denominator, required_numerator, required_denominator in specifications:
        for weighting in ("counts", "durationMilliseconds"):
            gates.append(
                _gate(
                    f"{scope}.{weighting}.{name}",
                    funnel,
                    weighting,
                    numerator,
                    denominator,
                    required_numerator,
                    required_denominator,
                )
            )
    guitar_counts = _mapping(guitarset.get("counts"), "guitarset.counts")
    correct_count = _integer(guitar_counts.get("C"), "guitarset.counts.C")
    count_payload = {
        "gateId": "guitarset.counts.minimumCorrectCellCount",
        "weighting": "counts",
        "measure": "C",
        "observed": correct_count,
        "requiredMinimum": 30,
        "passed": correct_count >= 30,
    }
    gates.append(_self_hashed(count_payload, "gateSha256"))
    if len(gates) != 13:
        raise RuntimeError("Stage-1 rubric must contain exactly 13 gates.")
    return gates


def _prediction_identity(track: Mapping[str, Any]) -> dict[str, Any]:
    """Project the report row onto prediction identity, never report metrics."""

    fields = (
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
    )
    projection = {field: track.get(field) for field in fields}
    if projection["split"] not in {"dev", DEVELOPMENT_SPLIT}:
        raise BeatCellStage1Error("Every prediction-identity row must be development-only.")
    if not isinstance(projection["id"], str) or not projection["id"]:
        raise BeatCellStage1Error("Prediction identity requires a nonempty id.")
    if not isinstance(projection["predictionFile"], str) or not projection["predictionFile"]:
        raise BeatCellStage1Error("Prediction identity requires predictionFile.")
    for field in (
        "predictionSha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "audioLineageRowSha256",
    ):
        _sha(projection[field], f"predictionIdentity.{field}")
    _integer(projection["canonicalDurationMilliseconds"], "predictionIdentity.canonicalDurationMilliseconds", minimum=1)
    return _self_hashed(projection, "predictionIdentitySha256")


def _prediction_only_report_projection(
    report: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Project only prediction identities and shared prediction contracts before labels."""

    experiment = _mapping(report.get("uncertaintyExperiment"), "uncertaintyExperiment")
    identities: dict[str, dict[str, Any]] = {}
    for index, raw_track in enumerate(_sequence(report.get("tracks"), "benchmark report.tracks")):
        identity = _prediction_identity(_mapping(raw_track, f"benchmark report.tracks[{index}]"))
        track_id = str(identity["id"])
        if track_id in identities:
            raise BeatCellStage1Error("Prediction-only report projection repeats a track id.")
        identities[track_id] = identity
    if len(identities) != STAGE1_SOURCE_CONTRACT["trackCount"]:
        raise BeatCellStage1Error("Prediction-only report projection must contain the official 246 tracks.")
    identity_set_sha256 = canonical_sha256(
        sorted(
            [
                {"trackId": track_id, "predictionIdentitySha256": identity["predictionIdentitySha256"]}
                for track_id, identity in identities.items()
            ],
            key=lambda row: row["trackId"],
        )
    )
    if identity_set_sha256 != STAGE1_SOURCE_CONTRACT["benchmarkReport"]["predictionIdentitySetSha256"]:
        raise BeatCellStage1Error("Prediction-only report identities are not the exact frozen candidate set.")

    binding = dict(_mapping(experiment.get("binding"), "uncertaintyExperiment.binding"))
    if canonical_sha256(binding) != _sha(experiment.get("bindingSha256"), "uncertaintyExperiment.bindingSha256"):
        raise BeatCellStage1Error("Prediction-only report binding hash is stale.")
    members = list(_sequence(experiment.get("memberBinding"), "uncertaintyExperiment.memberBinding"))
    member_order_sha256 = _sha(binding.get("memberOrderSha256"), "report memberOrderSha256")
    if canonical_sha256(members) != member_order_sha256 or canonical_sha256(members) != _sha(
        experiment.get("memberBindingSha256"), "uncertaintyExperiment.memberBindingSha256"
    ):
        raise BeatCellStage1Error("Prediction-only report member binding is stale.")
    audio_lineage = dict(_mapping(experiment.get("audioLineage"), "uncertaintyExperiment.audioLineage"))
    if canonical_sha256({key: item for key, item in audio_lineage.items() if key != "bindingSha256"}) != _sha(
        audio_lineage.get("bindingSha256"), "uncertaintyExperiment.audioLineage.bindingSha256"
    ):
        raise BeatCellStage1Error("Prediction-only report audio-lineage binding is stale.")
    projection = dict(_mapping(audio_lineage.get("projection"), "uncertaintyExperiment.audioLineage.projection"))
    projection_sha256 = _sha(
        audio_lineage.get("projectionSha256"), "uncertaintyExperiment.audioLineage.projectionSha256"
    )
    if projection.get("projectionSha256") != projection_sha256:
        raise BeatCellStage1Error("Prediction-only report audio-lineage projection binding is stale.")
    report_contract = {
        "binding": binding,
        "members": members,
        "uncertaintySchemaVersion": experiment.get("uncertaintySchemaVersion"),
        "uncertaintyContractSha256": _sha(experiment.get("contractSha256"), "uncertaintyExperiment.contractSha256"),
        "modelOrEnsembleSha256": _sha(binding.get("modelOrEnsembleSha256"), "report model binding"),
        "decoderContractSha256": _sha(binding.get("decoderContractSha256"), "report decoder binding"),
        "memberOrderSha256": member_order_sha256,
        "audioLineage": audio_lineage,
        "sourceAudioLineageSha256": _sha(
            audio_lineage.get("sourceArtifactSha256"),
            "uncertaintyExperiment.audioLineage.sourceArtifactSha256",
        ),
        "audioLineageProjection": projection,
        "audioLineageProjectionSha256": projection_sha256,
        "audioLineageBindingSha256": _sha(
            audio_lineage.get("bindingSha256"), "uncertaintyExperiment.audioLineage.bindingSha256"
        ),
    }
    return identities, report_contract


def _guitarset_role(dataset_id: str, raw_role: Any) -> str | None:
    if dataset_id != "guitarset":
        return None
    if not isinstance(raw_role, str) or not raw_role.strip():
        raise BeatCellStage1Error("Every GuitarSet track must declare a comp or solo role.")
    lowered = raw_role.strip().lower()
    tokens = lowered.replace("/", ":").split(":")
    matches = [role for role in ("comp", "solo") if lowered == role or role in tokens]
    if len(matches) != 1:
        raise BeatCellStage1Error("Every GuitarSet role must identify exactly one of comp or solo.")
    return matches[0]


def _structural_support(
    rows: Sequence[tuple[str, str, str | None, int, int]],
) -> dict[str, Any]:
    """Derive fixed-cell structural denominators without opening labels or predictions."""

    dataset_ids = list(_examples.LABEL_DETERMINACY_DATASET_IDS)
    seen: set[str] = set()
    dataset_cell_counts = {dataset_id: 0 for dataset_id in dataset_ids}
    dataset_durations = {dataset_id: 0 for dataset_id in dataset_ids}
    role_cell_counts = {role: 0 for role in ("comp", "solo")}
    role_durations = {role: 0 for role in ("comp", "solo")}
    role_track_counts = {role: 0 for role in ("comp", "solo")}
    aggregate_cell_count = 0
    aggregate_duration = 0
    for track_id, dataset_id, guitarset_role, raw_cell_count, raw_duration in rows:
        if not isinstance(track_id, str) or not track_id or track_id in seen:
            raise BeatCellStage1Error("Structural-support track identities must be nonempty and unique.")
        seen.add(track_id)
        if dataset_id not in dataset_cell_counts:
            raise BeatCellStage1Error("Structural support must use the exact five certification datasets.")
        cell_count = _integer(raw_cell_count, f"structural support {track_id!r}.cellCount", minimum=1)
        duration = _integer(raw_duration, f"structural support {track_id!r}.duration", minimum=1)
        if dataset_id == "guitarset":
            if guitarset_role not in role_cell_counts:
                raise BeatCellStage1Error("Every GuitarSet structural-support row requires comp or solo.")
            role = str(guitarset_role)
            role_cell_counts[role] += cell_count
            role_durations[role] += duration
            role_track_counts[role] += 1
        elif guitarset_role is not None:
            raise BeatCellStage1Error("Only GuitarSet structural-support rows may declare a GuitarSet role.")
        dataset_cell_counts[dataset_id] += cell_count
        dataset_durations[dataset_id] += duration
        aggregate_cell_count += cell_count
        aggregate_duration += duration

    payload = {
        "schemaVersion": _OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD["schemaVersion"],
        "derivation": _OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD["derivation"],
        "performanceExpectation": False,
        "aggregate": {
            "fixedCellCount": aggregate_cell_count,
            "fixedCellDurationMilliseconds": aggregate_duration,
        },
        "datasets": [
            {
                "datasetId": dataset_id,
                "fixedCellCount": dataset_cell_counts[dataset_id],
                "fixedCellDurationMilliseconds": dataset_durations[dataset_id],
            }
            for dataset_id in dataset_ids
        ],
        "guitarsetRoles": [
            {
                "guitarsetRole": role,
                "trackCount": role_track_counts[role],
                "fixedCellCount": role_cell_counts[role],
                "fixedCellDurationMilliseconds": role_durations[role],
            }
            for role in ("comp", "solo")
        ],
    }
    return _self_hashed(payload, "supportSha256")


def _structural_support_from_sources(
    beat_tracks: Mapping[str, Mapping[str, Any]],
    group_tracks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if set(beat_tracks) != set(group_tracks):
        raise BeatCellStage1Error("Beat receipt and group manifest disagree on structural-support tracks.")
    rows = []
    for track_id in sorted(beat_tracks):
        group = _mapping(group_tracks[track_id], f"group track {track_id!r}")
        beat = _mapping(beat_tracks[track_id], f"beat receipt track {track_id!r}")
        dataset_id = str(group.get("datasetId"))
        rows.append(
            (
                track_id,
                dataset_id,
                _guitarset_role(dataset_id, group.get("role")),
                _integer(beat.get("beatCount"), f"beat receipt track {track_id!r}.beatCount", minimum=1),
                _integer(
                    beat.get("coveredDurationMilliseconds"),
                    f"beat receipt track {track_id!r}.coveredDurationMilliseconds",
                    minimum=1,
                ),
            )
        )
    return _structural_support(rows)


def _structural_support_from_track_rows(track_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return _structural_support(
        [
            (
                str(row.get("trackId")),
                str(row.get("datasetId")),
                row.get("guitarsetRole"),
                _integer(row.get("cellCount"), "track.cellCount", minimum=1),
                _integer(row.get("coveredDurationMilliseconds"), "track.coveredDurationMilliseconds", minimum=1),
            )
            for row in track_rows
        ]
    )


def _require_official_guitar_role_track_support(track_rows: Sequence[Mapping[str, Any]]) -> None:
    role_counts = {
        role: sum(row.get("datasetId") == "guitarset" and row.get("guitarsetRole") == role for row in track_rows)
        for role in ("comp", "solo")
    }
    if role_counts != {"comp": 18, "solo": 18}:
        raise BeatCellStage1Error("Official GuitarSet disclosure support must be exactly 18 comp and 18 solo tracks.")


def _validate_source_group_track_binding(row: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    source_group = _mapping(row.get("sourceGroupTrack"), f"{name}.sourceGroupTrack")
    _exact_fields(
        source_group,
        {
            "trackId",
            "split",
            "datasetId",
            "role",
            "confidenceGroupId",
            "referenceFile",
            "referenceSha256",
            "trackMetadataSha256",
        },
        f"{name}.sourceGroupTrack",
    )
    _validate_self_hash(source_group, "trackMetadataSha256", f"{name}.sourceGroupTrack")
    expected_guitarset_role = _guitarset_role(str(row.get("datasetId")), source_group.get("role"))
    if (
        row.get("split") != DEVELOPMENT_SPLIT
        or source_group.get("split") != DEVELOPMENT_SPLIT
        or row.get("guitarsetRole") != expected_guitarset_role
        or row.get("sourceGroupTrackMetadataSha256") != source_group.get("trackMetadataSha256")
        or any(
            row.get(output_field) != source_group.get(source_field)
            for output_field, source_field in (
                ("trackId", "trackId"),
                ("datasetId", "datasetId"),
                ("role", "role"),
                ("confidenceGroupId", "confidenceGroupId"),
                ("sourceReferenceSha256", "referenceSha256"),
            )
        )
    ):
        raise BeatCellStage1Error("Track role/group/reference metadata is not exactly source-bound.")
    return source_group


def _summary_filename(track_id: str, sidecar_sha256: str) -> str:
    return f"{canonical_sha256({'trackId': track_id})}-{_sha(sidecar_sha256, 'sidecarSha256')}.json"


def _validate_prediction_summary(summary: Mapping[str, Any], track_id: str) -> None:
    _validate_self_hash(summary, "summarySha256", f"prediction summary {track_id!r}")
    if summary.get("schemaVersion") != CELL_SUMMARY_SCHEMA:
        raise BeatCellStage1Error("Prediction cell summary uses an unsupported schemaVersion.")
    if (
        summary.get("trackId") != track_id
        or summary.get("referenceFree") is not True
        or summary.get("runtimeAnalyzerOutput") is not False
        or summary.get("promotionEligible") is not False
        or summary.get("scoringPolicySha256") != SCORING_POLICY_SHA256
    ):
        raise BeatCellStage1Error("Prediction cell summary is not a sealed reference-free development summary.")
    cells = list(_sequence(summary.get("cells"), "prediction cell summary.cells"))
    if canonical_sha256(cells) != summary.get("cellSetSha256"):
        raise BeatCellStage1Error("Prediction cell summary set hash is stale.")
    for index, raw in enumerate(cells):
        row = _mapping(raw, f"prediction cell summary.cells[{index}]")
        _exact_fields(
            row,
            {
                "cellIndex",
                "sourceBeatCellSha256",
                "startMilliseconds",
                "endMilliseconds",
                "durationMilliseconds",
                "interval",
                "predictionProduct",
                "predictionCoveredDurationSeconds",
                "predictionProductDurationSeconds",
                "predictionCoverage",
                "predictionDominance",
                "rowSha256",
            },
            f"prediction cell summary.cells[{index}]",
        )
        _validate_self_hash(row, "rowSha256", f"prediction cell summary.cells[{index}]")
        _sha(row.get("sourceBeatCellSha256"), f"prediction cell summary.cells[{index}].sourceBeatCellSha256")
        if row.get("cellIndex") != index:
            raise BeatCellStage1Error("Prediction cell summary indices are stale.")
        start = _integer(row.get("startMilliseconds"), "prediction cell start")
        end = _integer(row.get("endMilliseconds"), "prediction cell end", minimum=1)
        if (
            end - start != row.get("durationMilliseconds")
            or row.get("interval") != "[startMilliseconds/1000,endMilliseconds/1000)"
        ):
            raise BeatCellStage1Error("Prediction cell summary duration is stale.")
        for field in ("predictionCoverage", "predictionDominance"):
            number = _finite(row.get(field), f"prediction cell summary.{field}")
            if not 0 <= number <= 1:
                raise BeatCellStage1Error("Prediction cell summary fractions must be in [0,1].")
        interval = (end - start) / 1000
        covered = _finite(row.get("predictionCoveredDurationSeconds"), "prediction covered duration")
        product_duration = _finite(row.get("predictionProductDurationSeconds"), "prediction product duration")
        if not 0 <= product_duration <= covered <= interval:
            raise BeatCellStage1Error("Prediction cell summary overlap durations are invalid.")
        if row.get("predictionCoverage") != min(1.0, max(0.0, covered / interval)) or row.get(
            "predictionDominance"
        ) != (min(1.0, max(0.0, product_duration / covered)) if covered > 1e-9 else 0.0):
            raise BeatCellStage1Error("Prediction cell summary overlap ratios are stale.")
        product = row.get("predictionProduct")
        if product is None:
            if covered != 0.0 or product_duration != 0.0:
                raise BeatCellStage1Error("A null prediction product cannot have positive overlap evidence.")
        elif (
            not isinstance(product, str)
            or not product
            or covered <= 0
            or product_duration <= 0
            or _bar_product._segment_product({"productLabel": product}) != product
        ):
            raise BeatCellStage1Error("A prediction product must be canonical and have positive overlap evidence.")


def _validate_prediction_for_cells(
    prediction: Mapping[str, Any],
    track_id: str,
    report_contract: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate uncertainty, segments, hashes, and shared identity without any bar grid."""

    value = _mapping(prediction, f"prediction {track_id!r}")
    uncertainty = _mapping(value.get("uncertainty"), f"prediction {track_id!r}.uncertainty")
    validate_factorized_uncertainty_contract(uncertainty)
    claimed_uncertainty = _sha(value.get("uncertaintySha256"), "prediction uncertaintySha256")
    if canonical_sha256(uncertainty) != claimed_uncertainty:
        raise BeatCellStage1Error(f"Prediction uncertainty hash mismatch for {track_id!r}.")
    core_payload = {
        key: item
        for key, item in value.items()
        if key not in {"uncertainty", "predictionCoreSha256", "uncertaintySha256"}
    }
    claimed_core = _sha(value.get("predictionCoreSha256"), "prediction predictionCoreSha256")
    if canonical_sha256(core_payload) != claimed_core or uncertainty.get("predictionCoreSha256") != claimed_core:
        raise BeatCellStage1Error(f"Prediction core hash mismatch for {track_id!r}.")
    if dict(_mapping(uncertainty.get("binding"), "prediction uncertainty binding")) != report_contract["binding"]:
        raise BeatCellStage1Error(f"Prediction binding mismatch for {track_id!r}.")
    if list(_sequence(uncertainty.get("members"), "prediction uncertainty members")) != report_contract["members"]:
        raise BeatCellStage1Error(f"Prediction member binding mismatch for {track_id!r}.")

    evidence = _bar_uncertainty._validate_prediction_uncertainty(value)
    duration = _finite(value.get("durationSeconds"), "prediction.durationSeconds")
    segments = _bar_uncertainty._prediction_segments(value, duration)
    _bar_uncertainty._validate_selected_class_alignment(evidence, segments)
    segment_identity = [{"start": row["start"], "end": row["end"], "product": row["product"]} for row in segments]
    audit_payload = {
        "schemaVersion": "chord_runtime_beat_cell_prediction_validation_audit_v1",
        "trackId": track_id,
        "predictionCoreSha256": claimed_core,
        "uncertaintySha256": claimed_uncertainty,
        "uncertaintyContractSha256": evidence["uncertaintyContractSha256"],
        "durationSeconds": duration,
        "frameSeconds": evidence["frameSeconds"],
        "frameCount": evidence["frameCount"],
        "segmentCount": len(segments),
        "segmentSetSha256": canonical_sha256(segment_identity),
        "selectedClassAlignmentValidated": True,
        "parentBarSummaryUsed": False,
    }
    audit = _self_hashed(audit_payload, "auditSha256")
    shared_binding = {
        "schemaVersion": "chord_runtime_beat_cell_prediction_runtime_binding_v1",
        "uncertaintyContractSha256": evidence["uncertaintyContractSha256"],
        "modelOrEnsembleSha256": report_contract["modelOrEnsembleSha256"],
        "decoderContractSha256": report_contract["decoderContractSha256"],
        "memberOrderSha256": report_contract["memberOrderSha256"],
        "sourceFeatureKind": evidence["featureKind"],
        "sourceFeatureSpecSha256": evidence["featureSpecSha256"],
        "observabilityProfileSchemaVersion": evidence["observabilityProfileSchemaVersion"],
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "scoringPolicySha256": SCORING_POLICY_SHA256,
        "barOutcomeEligibilityContractSha256": _examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    }
    return audit, shared_binding


def _exclusion_audit(outcomes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    names = (
        "referenceMixed",
        "referenceUncovered",
        "predictionMixed",
        "predictionUncovered",
    )
    counts = {name: 0 for name in names}
    durations = {name: 0 for name in names}
    for row in outcomes:
        reason = row.get("reason")
        duration = _integer(row.get("durationMilliseconds"), "outcome.durationMilliseconds", minimum=1)
        if isinstance(reason, str) and reason in counts:
            counts[reason] += 1
            durations[reason] += duration
    payload = {
        "counts": counts,
        "durationMilliseconds": durations,
        "referencePartitionReconciled": counts["referenceMixed"] + counts["referenceUncovered"]
        == sum(row.get("classification") == "U" for row in outcomes),
        "predictionPartitionReconciled": counts["predictionMixed"] + counts["predictionUncovered"]
        == sum(row.get("classification") == "N" for row in outcomes),
    }
    if not payload["referencePartitionReconciled"] or not payload["predictionPartitionReconciled"]:
        raise BeatCellStage1Error("Cell exclusion reasons do not reconcile with U and N.")
    return _self_hashed(payload, "auditSha256")


def funnel_from_outcomes(outcomes: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reduce U/N/C/I terminal cell outcomes into both exact funnel measures."""

    counts = _empty_measure()
    durations = _empty_measure()
    for index, raw in enumerate(outcomes):
        row = _mapping(raw, f"outcomes[{index}]")
        classification = row.get("classification")
        if classification not in {"U", "N", "C", "I"}:
            raise BeatCellStage1Error("Every cell outcome must terminate in exactly U, N, C, or I.")
        duration = _integer(row.get("durationMilliseconds"), f"outcomes[{index}].durationMilliseconds", minimum=1)
        for target, amount in ((counts, 1), (durations, duration)):
            target["T"] += amount
            if classification == "U":
                target["U"] += amount
            else:
                target["R"] += amount
                if classification == "N":
                    target["N"] += amount
                else:
                    target["E"] += amount
                    target[classification] += amount
    return make_funnel(counts, durations), _exclusion_audit(outcomes)


def _root_binding(root: Path, name: str) -> dict[str, Any]:
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise BeatCellStage1Error(f"{name} must be an existing directory.") from error
    if not resolved.is_dir():
        raise BeatCellStage1Error(f"{name} must be an existing directory.")
    rendered = str(resolved)
    return {"path": rendered, "pathSha256": canonical_sha256(rendered)}


def _top_binding(
    path: Path,
    raw: bytes,
    value: Mapping[str, Any],
    claimed_field: str | None,
    name: str,
    *,
    include_canonical_sha256: bool = True,
) -> dict[str, Any]:
    claimed: str | None = None
    if claimed_field is not None:
        _validate_self_hash(value, claimed_field, name)
        claimed = str(value[claimed_field])
    absolute = str(_absolute(path))
    binding = {
        "path": absolute,
        "pathSha256": canonical_sha256(absolute),
        "fileSha256": hashlib.sha256(raw).hexdigest(),
        "claimedArtifactSha256": claimed,
    }
    if include_canonical_sha256:
        binding["canonicalSha256"] = canonical_sha256(value)
    return binding


def _report_prediction_set_bindings(report: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(report.get("provenance"), "benchmark report.provenance")
    evaluation = _mapping(provenance.get("evaluation"), "benchmark report.provenance.evaluation")
    experiment = _mapping(report.get("uncertaintyExperiment"), "benchmark report.uncertaintyExperiment")
    tracks = list(_sequence(report.get("tracks"), "benchmark report.tracks"))
    values = {
        "predictionArtifactSetSha256": _sha(
            evaluation.get("predictionSetSha256"), "provenance.evaluation.predictionSetSha256"
        ),
        "predictionCoreSetSha256": _sha(
            experiment.get("predictionCoreSetSha256"), "uncertaintyExperiment.predictionCoreSetSha256"
        ),
        "uncertaintySetSha256": _sha(
            experiment.get("uncertaintySetSha256"), "uncertaintyExperiment.uncertaintySetSha256"
        ),
    }
    recomputed = {
        "predictionArtifactSetSha256": benchmark_content_set_sha256(tracks, "predictionSha256"),
        "predictionCoreSetSha256": canonical_sha256(
            sorted(
                [
                    {"id": str(_mapping(row, "report track")["id"]), "sha256": row["predictionCoreSha256"]}
                    for row in tracks
                ],
                key=lambda row: row["id"],
            )
        ),
        "uncertaintySetSha256": canonical_sha256(
            sorted(
                [
                    {"id": str(_mapping(row, "report track")["id"]), "sha256": row["uncertaintySha256"]}
                    for row in tracks
                ],
                key=lambda row: row["id"],
            )
        ),
    }
    if values != recomputed:
        raise BeatCellStage1Error("Benchmark prediction artifact/core/uncertainty set bindings are stale.")
    if len(set(values.values())) != 3:
        raise BeatCellStage1Error("Prediction artifact, core, and uncertainty set hashes must remain distinct.")
    return _self_hashed({**values, "allThreeDistinct": True}, "bindingsSha256")


def _validate_official_source_contract(
    report: Mapping[str, Any],
    report_raw: bytes,
    runtime: Mapping[str, Any],
    runtime_raw: bytes,
    beat_receipt: Mapping[str, Any],
    beat_receipt_raw: bytes,
    groups: Mapping[str, Any],
    groups_raw: bytes,
    audio_lineage: Mapping[str, Any],
    audio_raw: bytes,
) -> None:
    """Reject any subset or candidate substitution before nested leaf access."""

    contract = STAGE1_SOURCE_CONTRACT
    report_contract = _mapping(contract["benchmarkReport"], "source contract benchmarkReport")
    report_tracks = list(_sequence(report.get("tracks"), "benchmark report.tracks"))
    prediction_sets = _report_prediction_set_bindings(report)
    report_binding = _mapping(
        _mapping(report.get("uncertaintyExperiment"), "uncertaintyExperiment").get("binding"),
        "uncertaintyExperiment.binding",
    )
    if (
        hashlib.sha256(report_raw).hexdigest() != report_contract["fileSha256"]
        or canonical_sha256(report) != report_contract["canonicalSha256"]
        or len(report_tracks) != contract["trackCount"]
        or benchmark_track_set_sha256(report_tracks) != report_contract["trackSetSha256"]
        or prediction_sets["predictionArtifactSetSha256"] != report_contract["predictionArtifactSetSha256"]
        or prediction_sets["predictionCoreSetSha256"] != report_contract["predictionCoreSetSha256"]
        or prediction_sets["uncertaintySetSha256"] != report_contract["uncertaintySetSha256"]
        or report_binding.get("modelOrEnsembleSha256") != report_contract["modelOrEnsembleSha256"]
    ):
        raise BeatCellStage1Error("Benchmark report is not the exact official 246-track Stage-1 candidate.")

    runtime_contract = _mapping(contract["runtimeManifest"], "source contract runtimeManifest")
    analyzer = _mapping(runtime.get("analyzerContract"), "runtime analyzerContract")
    runtime_track_rows = list(_sequence(runtime.get("tracks"), "runtime manifest.tracks"))
    if (
        hashlib.sha256(runtime_raw).hexdigest() != runtime_contract["fileSha256"]
        or runtime.get("manifestSha256") != runtime_contract["manifestSha256"]
        or runtime.get("trackSetSha256") != runtime_contract["trackSetSha256"]
        or analyzer.get("contractSha256") != runtime_contract["analyzerContractSha256"]
        or len(runtime_track_rows) != contract["trackCount"]
    ):
        raise BeatCellStage1Error("Runtime manifest is not the exact official Stage-1 candidate.")

    beat_contract = _mapping(contract["beatReceipt"], "source contract beatReceipt")
    beat_tracks = list(_sequence(beat_receipt.get("tracks"), "beat receipt.tracks"))
    analyzer_contract = _mapping(beat_receipt.get("analyzerContract"), "beat receipt.analyzerContract")
    player_contract = _mapping(beat_receipt.get("playerReplayContract"), "beat receipt.playerReplayContract")
    if (
        hashlib.sha256(beat_receipt_raw).hexdigest() != beat_contract["fileSha256"]
        or beat_receipt.get("schemaVersion") != beat_contract["receiptSchemaVersion"]
        or beat_receipt.get("receiptSha256") != beat_contract["receiptSha256"]
        or beat_receipt.get("trackSetSha256") != beat_contract["trackSetSha256"]
        or beat_receipt.get("receiptTotals") != beat_contract["receiptTotals"]
        or beat_receipt.get("receiptTotalsSha256") != beat_contract["receiptTotalsSha256"]
        or analyzer_contract.get("contractSha256") != beat_contract["beatAnalyzerContractSha256"]
        or player_contract.get("contractSha256") != beat_contract["playerReplayContractSha256"]
        or len(beat_tracks) != contract["trackCount"]
        or beat_receipt.get("referenceFree") is not beat_contract["referenceFree"]
        or beat_receipt.get("stage1UseAllowed") is not beat_contract["stage1UseAllowed"]
        or beat_receipt.get("selectorUseAllowed") is not beat_contract["selectorUseAllowed"]
        or beat_receipt.get("playerPlaybackUseAllowed") is not beat_contract["playerPlaybackUseAllowed"]
    ):
        raise BeatCellStage1Error("Beat receipt is not the exact independently frozen Stage-1 source.")
    parent_binding = _mapping(beat_receipt.get("parentRuntimeBinding"), "beat receipt.parentRuntimeBinding")
    if (
        parent_binding.get("manifestSha256") != beat_contract["parentRuntimeManifestSha256"]
        or parent_binding.get("trackSetSha256") != beat_contract["parentRuntimeTrackSetSha256"]
        or parent_binding.get("manifestSha256") != runtime_contract["manifestSha256"]
        or parent_binding.get("trackSetSha256") != runtime_contract["trackSetSha256"]
    ):
        raise BeatCellStage1Error("Beat receipt does not bind the exact parent runtime manifest.")

    group_contract = _mapping(contract["groupManifest"], "source contract groupManifest")
    group_tracks = _examples._validate_group_manifest(groups)
    if (
        hashlib.sha256(groups_raw).hexdigest() != group_contract["fileSha256"]
        or groups.get("manifestSha256") != group_contract["manifestSha256"]
        or groups.get("trackSetSha256") != group_contract["trackSetSha256"]
    ):
        raise BeatCellStage1Error("Group manifest is not the exact official Stage-1 candidate.")
    _validate_reviewed_group_shape(group_tracks)

    lineage_contract = _mapping(contract["audioLineage"], "source contract audioLineage")
    audio_tracks = list(_sequence(audio_lineage.get("tracks"), "audio lineage.tracks"))
    report_audio = _mapping(
        _mapping(report.get("uncertaintyExperiment"), "uncertaintyExperiment").get("audioLineage"),
        "uncertaintyExperiment.audioLineage",
    )
    if (
        hashlib.sha256(audio_raw).hexdigest() != lineage_contract["fileSha256"]
        or audio_lineage.get("artifactSha256") != lineage_contract["artifactSha256"]
        or report_audio.get("projectionSha256") != lineage_contract["projectionSha256"]
        or len(audio_tracks) != contract["trackCount"]
    ):
        raise BeatCellStage1Error("Audio lineage is not the exact official Stage-1 candidate.")

    id_sets = (
        {str(_mapping(row, "report track").get("id")) for row in report_tracks},
        {str(_mapping(row, "runtime track").get("trackId")) for row in runtime_track_rows},
        {str(_mapping(row, "beat receipt track").get("trackId")) for row in beat_tracks},
        set(group_tracks),
        {str(_mapping(row, "audio-lineage track").get("trackId")) for row in audio_tracks},
    )
    if any(values != id_sets[0] for values in id_sets[1:]) or len(id_sets[0]) != contract["trackCount"]:
        raise BeatCellStage1Error("Official Stage-1 top-level track identities disagree.")
    beat_tracks_by_id = {
        str(_mapping(row, "beat receipt track").get("trackId")): _mapping(row, "beat receipt track")
        for row in beat_tracks
    }
    structural_support = _structural_support_from_sources(beat_tracks_by_id, group_tracks)
    if structural_support != contract.get("structuralSupport") or structural_support != OFFICIAL_STRUCTURAL_SUPPORT:
        raise BeatCellStage1Error("Official beat-receipt/group structural denominators are not exact.")
    reviewed = _mapping(contract["reviewedDatasetShape"], "source contract reviewedDatasetShape")
    if reviewed.get("shape") != REVIEWED_DEVELOPMENT_GROUP_SHAPE or reviewed.get("shapeSha256") != canonical_sha256(
        REVIEWED_DEVELOPMENT_GROUP_SHAPE
    ):
        raise RuntimeError("Embedded Stage-1 reviewed dataset shape drifted.")


def _canonical_input(raw: bytes, value: Mapping[str, Any], name: str) -> None:
    rendered = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if rendered != raw:
        raise BeatCellStage1Error(f"{name} must use the exact canonical indented JSON rendering.")


def _preflight_new_output(path: Path) -> None:
    destination = _absolute(path)
    if destination.suffix.lower() != ".json":
        raise BeatCellStage1Error("Stage-1 output must use a new .json path.")
    if destination.exists() or destination.is_symlink():
        raise BeatCellStage1Error("Stage-1 output must use a new path.")


def _require_disjoint_output_path(output_path: Path, roots: Sequence[tuple[str, Path]]) -> None:
    destination = _absolute(output_path)
    for name, raw_root in roots:
        root = _absolute(raw_root)
        if destination == root or destination.is_relative_to(root):
            raise BeatCellStage1Error(f"Stage-1 output must be disjoint from {name}.")


def _seal_prediction_records(
    *,
    track_ids: Sequence[str],
    prediction_identities: Mapping[str, Mapping[str, Any]],
    report_contract: Mapping[str, Any],
    runtime_tracks: Mapping[str, Mapping[str, Any]],
    beat_tracks: Mapping[str, Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
    benchmark_root: Path,
    summary_output_root: Path,
    summary_public_root: Path,
    runtime_analyzer_contract_sha256: str,
    source_beat_receipt_file_sha256: str,
    source_beat_receipt_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Finish and materialize every prediction-only record before references."""

    records: list[dict[str, Any]] = []
    shared_binding: dict[str, Any] | None = None
    for track_id in track_ids:
        identity = dict(_mapping(prediction_identities[track_id], f"prediction identity {track_id!r}"))
        _validate_self_hash(identity, "predictionIdentitySha256", f"prediction identity {track_id!r}")
        runtime_track = runtime_tracks[track_id]
        beat_track = beat_tracks[track_id]
        prediction_path = _examples._artifact_path(
            benchmark_root, identity["predictionFile"], f"prediction {track_id!r}"
        )
        prediction, prediction_raw = _examples._read_json(prediction_path, f"prediction {track_id!r}")
        if hashlib.sha256(prediction_raw).hexdigest() != identity["predictionSha256"]:
            raise BeatCellStage1Error(f"Prediction file hash mismatch for {track_id!r}.")
        if prediction.get("id") != track_id:
            raise BeatCellStage1Error(f"Prediction id mismatch for {track_id!r}.")
        for field in ("predictionCoreSha256", "uncertaintySha256"):
            if prediction.get(field) != identity[field]:
                raise BeatCellStage1Error(f"Prediction {field} mismatch for {track_id!r}.")
        prediction_validation, prediction_binding = _validate_prediction_for_cells(
            prediction, track_id, report_contract
        )

        expected_parent_timing = {
            "timingFile": runtime_track["timingFile"],
            "timingSha256": runtime_track["timingSha256"],
            "timingContractSha256": runtime_track["timingContractSha256"],
            "timingSourceContractSha256": runtime_track["timingSourceContractSha256"],
            "barCount": runtime_track["barCount"],
        }
        if (
            beat_track.get("parentTrackArtifactSha256") != runtime_track.get("trackArtifactSha256")
            or beat_track.get("parentTimingBinding") != expected_parent_timing
            or beat_track.get("runtimeIdentity") != runtime_track.get("runtimeIdentity")
            or beat_track.get("audioBinding") != runtime_track.get("audioBinding")
        ):
            raise BeatCellStage1Error(f"Beat receipt/runtime source join mismatch for {track_id!r}.")
        construction, derived_cell_timing = construct_beat_cells(
            beat_track,
            source_beat_receipt_file_sha256=source_beat_receipt_file_sha256,
            source_beat_receipt_sha256=source_beat_receipt_sha256,
        )
        prediction_canonical_ms = _player_ms(
            prediction.get("durationSeconds"), f"prediction {track_id!r}.durationSeconds"
        )
        if not (
            prediction_canonical_ms
            == construction["canonicalDurationMilliseconds"]
            == identity["canonicalDurationMilliseconds"]
        ):
            raise BeatCellStage1Error(
                f"Prediction, runtime construction, and identity canonical duration disagree for {track_id!r}."
            )
        summary = summarize_prediction_cells(
            prediction,
            construction,
            derived_cell_timing,
            prediction_validation_audit_sha256=prediction_validation["auditSha256"],
        )
        _validate_prediction_summary(summary, track_id)
        if len(_sequence(summary.get("cells"), "prediction cell summary cells")) != construction["cellCount"]:
            raise BeatCellStage1Error(f"Prediction summary cell count mismatch for {track_id!r}.")
        binding = {
            **prediction_binding,
            "timingSourceContractSha256": runtime_track["timingSourceContractSha256"],
            "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
            "beatAnalyzerContractSha256": beat_track["beatAnalyzerContractSha256"],
            "playerReplayContractSha256": beat_track["playerReplayContractSha256"],
        }
        if binding["timingSourceContractSha256"] != runtime_analyzer_contract_sha256:
            raise BeatCellStage1Error(f"Runtime timing source contract mismatch for {track_id!r}.")
        if shared_binding is None:
            shared_binding = binding
        elif shared_binding != binding:
            raise BeatCellStage1Error("All cell summaries must share one exact prediction/runtime binding.")

        sidecar_payload = {
            "schemaVersion": CELL_SUMMARY_SCHEMA,
            "split": DEVELOPMENT_SPLIT,
            "developmentOnly": True,
            "promotionEligible": False,
            "referenceFree": True,
            "trackId": track_id,
            "predictionIdentity": identity,
            "predictionIdentitySha256": identity["predictionIdentitySha256"],
            "sourceRuntimeTrackArtifactSha256": runtime_track["trackArtifactSha256"],
            "sourceBeatReceiptTrack": deepcopy(beat_track),
            "sourceBeatReceiptTrackSha256": beat_track["trackReceiptSha256"],
            "sourceAudioLineageRowSha256": projection_tracks[track_id]["rowSha256"],
            "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
            "scoringPolicySha256": SCORING_POLICY_SHA256,
            "construction": construction,
            "constructionSha256": construction["constructionSha256"],
            "derivedCellTiming": derived_cell_timing,
            "derivedCellTimingContractSha256": derived_cell_timing["contractSha256"],
            "predictionValidationAudit": prediction_validation,
            "predictionValidationAuditSha256": prediction_validation["auditSha256"],
            "predictionSummary": summary,
            "predictionSummarySha256": summary["summarySha256"],
        }
        sidecar = _self_hashed(sidecar_payload, "artifactSha256")
        summary_path = summary_output_root / _summary_filename(track_id, sidecar["artifactSha256"])
        public_summary_path = summary_public_root / summary_path.name
        _examples._atomic_write_json(summary_path, sidecar)
        materialized, _materialized_raw = _examples._read_json(
            summary_path, f"materialized prediction-only cell summary {track_id!r}"
        )
        if materialized != sidecar:
            raise BeatCellStage1Error(f"Materialized prediction-only cell summary changed for {track_id!r}.")
        records.append(
            {
                "trackId": track_id,
                "prediction": prediction,
                "predictionIdentity": identity,
                "sourceBeatReceiptTrack": deepcopy(beat_track),
                "derivedCellTiming": derived_cell_timing,
                "summary": summary,
                "construction": construction,
                "summaryPath": str(_absolute(public_summary_path)),
                "summaryArtifactSha256": sidecar["artifactSha256"],
                "predictionIdentitySha256": identity["predictionIdentitySha256"],
            }
        )
    if shared_binding is None:
        raise BeatCellStage1Error("At least one prediction record is required.")
    return records, shared_binding


def _reference_segments_for_cells(
    reference: Mapping[str, Any],
    prediction: Mapping[str, Any],
    construction: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Validate the frozen endpoint policy without changing canonical cell ends."""

    prediction_duration = _finite(prediction.get("durationSeconds"), "prediction.durationSeconds")
    runtime_ms = _integer(
        construction.get("canonicalDurationMilliseconds"), "construction.canonicalDurationMilliseconds", minimum=1
    )
    if _player_ms(prediction_duration, "prediction.durationSeconds") != runtime_ms:
        raise BeatCellStage1Error("Prediction duration and canonical runtime duration do not reconcile.")
    raw_segments = list(_sequence(reference.get("segments"), "reference.segments"))
    previous_end: float | None = None
    endpoints: list[tuple[float, float]] = []
    for index, raw in enumerate(raw_segments):
        segment = _mapping(raw, f"reference.segments[{index}]")
        start = _finite(segment.get("start"), f"reference.segments[{index}].start")
        end = _finite(segment.get("end"), f"reference.segments[{index}].end")
        if start < 0 or end <= start or (previous_end is not None and start < previous_end):
            raise BeatCellStage1Error("Reference segments must be ordered, nonoverlapping, and positive.")
        previous_end = end
        endpoints.append((start, end))
    segments = _bar_product._segments(raw_segments, prediction=False)
    runtime_duration = runtime_ms / 1000
    declared = reference.get("durationSeconds")
    if declared is not None:
        reference_duration = _finite(declared, "reference.durationSeconds")
        if reference_duration not in {prediction_duration, runtime_duration}:
            raise BeatCellStage1Error(
                "Reference duration must exactly equal prediction duration or canonical runtime duration."
            )
        if endpoints and max(end for _start, end in endpoints) > reference_duration:
            raise BeatCellStage1Error("Reference segments exceed the declared reference duration.")
    reconciliation: dict[str, Any] | None = None
    if declared is None and endpoints:
        original_end = max(end for _start, end in endpoints)
        if original_end > prediction_duration:
            terminal_index = len(endpoints) - 1
            overhang = [index for index, (_start, end) in enumerate(endpoints) if end > prediction_duration]
            maximum = [index for index, (_start, end) in enumerate(endpoints) if end == original_end]
            if overhang != [terminal_index] or maximum != [terminal_index]:
                raise BeatCellStage1Error("Only one unique terminal reference endpoint may exceed prediction duration.")
            if endpoints[terminal_index][0] >= prediction_duration:
                raise BeatCellStage1Error("Reconciled terminal reference evidence must begin before prediction end.")
            if _player_ms(original_end, "terminal reference end") != runtime_ms:
                raise BeatCellStage1Error(
                    "Terminal reference endpoint is outside the prediction canonical millisecond."
                )
            reconciliation = {
                "originalEnd": original_end,
                "predictionDuration": prediction_duration,
                "reconciledEnd": prediction_duration,
                "reconciledSeconds": original_end - prediction_duration,
                "canonicalMs": runtime_ms,
            }
    clipped_segments: list[dict[str, Any]] = []
    for segment in segments:
        start = float(segment["start"])
        end = min(float(segment["end"]), prediction_duration)
        if start < prediction_duration and end > start:
            clipped_segments.append({**segment, "end": end})
    return clipped_segments, reconciliation


def _classification_from_evidence(evidence: Mapping[str, Any]) -> tuple[str, str | None]:
    epsilon = float(SCORING_POLICY["comparisonEpsilon"])
    reference_product = evidence.get("referenceProduct")
    reference_coverage = _finite(evidence.get("referenceCoverage"), "cell evidence.referenceCoverage")
    reference_dominance = _finite(evidence.get("referenceDominance"), "cell evidence.referenceDominance")
    if reference_product is None or reference_coverage + epsilon < float(SCORING_POLICY["referenceDominance"]):
        return "U", "referenceUncovered"
    if reference_dominance + epsilon < float(SCORING_POLICY["referenceDominance"]):
        return "U", "referenceMixed"
    prediction_product = evidence.get("predictionProduct")
    prediction_coverage = _finite(evidence.get("predictionCoverage"), "cell evidence.predictionCoverage")
    prediction_dominance = _finite(evidence.get("predictionDominance"), "cell evidence.predictionDominance")
    if prediction_product is None or prediction_coverage + epsilon < float(SCORING_POLICY["predictionCoverage"]):
        return "N", "predictionUncovered"
    if prediction_dominance + epsilon < float(SCORING_POLICY["predictionDominance"]):
        return "N", "predictionMixed"
    if not isinstance(reference_product, str) or not reference_product:
        raise BeatCellStage1Error("Determinate reference product must be nonempty.")
    if not isinstance(prediction_product, str) or not prediction_product:
        raise BeatCellStage1Error("Eligible prediction product must be nonempty.")
    return ("C" if prediction_product == reference_product else "I"), None


def score_fixed_cells(
    reference: Mapping[str, Any],
    prediction: Mapping[str, Any],
    construction: Mapping[str, Any],
    prediction_summary: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Classify exact canonical-ms cells with the frozen 0.75 dominance rules."""

    _validate_construction(construction, "cell construction")
    reference_segments, reconciliation = _reference_segments_for_cells(reference, prediction, construction)
    summary_cells = list(_sequence(prediction_summary.get("cells"), "prediction summary cells"))
    cell_rows = list(_sequence(construction.get("cells"), "constructed cells"))
    if len(summary_cells) != len(cell_rows):
        raise BeatCellStage1Error("Fixed-cell construction and prediction summary counts disagree.")
    outcomes: list[dict[str, Any]] = []
    for raw_cell, raw_summary in zip(cell_rows, summary_cells, strict=True):
        cell = _mapping(raw_cell, "constructed cell")
        summary = _mapping(raw_summary, "prediction summary cell")
        cell_index = _integer(cell.get("beatIndex"), "cell.beatIndex")
        if (
            summary.get("cellIndex") != cell_index
            or summary.get("sourceBeatCellSha256") != canonical_sha256(cell)
            or summary.get("startMilliseconds") != cell.get("startMs")
            or summary.get("endMilliseconds") != cell.get("endMs")
            or summary.get("durationMilliseconds") != cell.get("durationMilliseconds")
        ):
            raise BeatCellStage1Error("Constructed and summarized cell identity disagrees.")
        duration_ms = _integer(cell.get("durationMilliseconds"), "cell.durationMilliseconds", minimum=1)
        start = int(cell["startMs"]) / 1000
        end = int(cell["endMs"]) / 1000
        reference_overlaps, reference_covered = _bar_product._overlap_by_product(reference_segments, start, end)
        reference_product, reference_product_duration = _bar_product._dominant_product(reference_overlaps)
        interval_duration = duration_ms / 1000
        reference_covered = min(interval_duration, max(0.0, reference_covered))
        reference_product_duration = min(reference_covered, max(0.0, reference_product_duration))
        reference_coverage = min(1.0, max(0.0, reference_covered / interval_duration))
        reference_dominance = min(1.0, max(0.0, reference_product_duration / interval_duration))
        evidence = {
            "referenceProduct": reference_product,
            "referenceCoveredDurationSeconds": reference_covered,
            "referenceProductDurationSeconds": reference_product_duration,
            "referenceCoverage": reference_coverage,
            "referenceDominance": reference_dominance,
            "predictionProduct": summary.get("predictionProduct"),
            "predictionCoveredDurationSeconds": summary.get("predictionCoveredDurationSeconds"),
            "predictionProductDurationSeconds": summary.get("predictionProductDurationSeconds"),
            "predictionCoverage": summary.get("predictionCoverage"),
            "predictionDominance": summary.get("predictionDominance"),
        }
        classification, reason = _classification_from_evidence(evidence)
        payload = {
            "cellIndex": cell_index,
            "sourceBeatCellSha256": canonical_sha256(cell),
            "beatIndex": cell["beatIndex"],
            "retainedBarIndex": cell["retainedBarIndex"],
            "pulseNumber": cell["pulseNumber"],
            "downbeatCandidate": cell["downbeatCandidate"],
            "durationMilliseconds": duration_ms,
            **evidence,
            "classification": classification,
            "reason": reason,
        }
        outcomes.append(_self_hashed(payload, "rowSha256"))
    return outcomes, reconciliation


def _score_records(
    *,
    records: Sequence[Mapping[str, Any]],
    report_tracks: Mapping[str, Mapping[str, Any]],
    group_tracks: Mapping[str, Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
    group_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Open references only after prediction sealing, then score fixed cells."""

    track_rows: list[dict[str, Any]] = []
    reconciliation_rows: list[dict[str, Any]] = []
    for raw_record in records:
        record = _mapping(raw_record, "prediction record")
        track_id = str(record["trackId"])
        group_track = group_tracks[track_id]
        dataset_id = str(projection_tracks[track_id]["datasetId"])
        role = group_track["role"]
        guitar_role = _guitarset_role(dataset_id, role)

        reference_path = _examples._artifact_path(group_root, group_track["referenceFile"], f"reference {track_id!r}")
        reference, reference_raw = _examples._read_json(reference_path, f"reference {track_id!r}")
        reference_sha256 = hashlib.sha256(reference_raw).hexdigest()
        if reference_sha256 != group_track["referenceSha256"]:
            raise BeatCellStage1Error(f"Reference file hash mismatch for {track_id!r}.")
        if reference_sha256 != report_tracks[track_id]["referenceSha256"]:
            raise BeatCellStage1Error(f"Reference/report hash mismatch for {track_id!r}.")

        construction = _mapping(record.get("construction"), "cell construction")
        outcomes, reconciliation = score_fixed_cells(reference, record["prediction"], construction, record["summary"])
        reconciliation_row: dict[str, Any] | None = None
        if reconciliation is not None:
            expected_ms = _integer(
                projection_tracks[track_id].get("canonicalDurationMilliseconds"),
                f"audio-lineage {track_id!r} canonicalDurationMilliseconds",
                minimum=1,
            )
            if reconciliation.get("canonicalMs") != expected_ms:
                raise BeatCellStage1Error("Reference endpoint reconciliation disagrees with audio lineage.")
            reconciliation_payload = {
                "trackId": track_id,
                "datasetId": dataset_id,
                "referenceSha256": reference_sha256,
                **reconciliation,
            }
            reconciliation_row = _self_hashed(reconciliation_payload, "rowSha256")
            reconciliation_rows.append(reconciliation_row)

        funnel, exclusions = funnel_from_outcomes(outcomes)
        track_payload = {
            "trackId": track_id,
            "split": DEVELOPMENT_SPLIT,
            "datasetId": dataset_id,
            "role": role,
            "guitarsetRole": guitar_role,
            "confidenceGroupId": group_track["confidenceGroupId"],
            "sourceGroupTrack": dict(group_track),
            "sourceGroupTrackMetadataSha256": group_track["trackMetadataSha256"],
            "predictionIdentity": dict(_mapping(record["predictionIdentity"], "prediction identity")),
            "predictionIdentitySha256": record["predictionIdentitySha256"],
            "sourceBeatReceiptTrackSha256": construction["sourceTrackReceiptSha256"],
            "sourceTopologySha256": construction["sourceTopologySha256"],
            "timingArtifactSha256": construction["timingArtifactSha256"],
            "timingContractSha256": construction["timingContractSha256"],
            "timingSourceContractSha256": construction["timingSourceContractSha256"],
            "sourceReferenceSha256": reference_sha256,
            "referenceEndpointReconciliationRowSha256": (
                None if reconciliation_row is None else reconciliation_row["rowSha256"]
            ),
            "predictionOnlySummary": {
                "path": record["summaryPath"],
                "pathSha256": canonical_sha256(record["summaryPath"]),
                "artifactSha256": record["summaryArtifactSha256"],
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
        track_rows.append(_self_hashed(track_payload, "rowSha256"))
    track_rows.sort(key=lambda row: str(row["trackId"]))
    return track_rows, reconciliation_rows


def _stratum_rows(track_rows: Sequence[Mapping[str, Any]], field: str, values: Sequence[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values:
        selected = [row for row in track_rows if row.get(field) == value]
        funnel = _sum_funnels([_mapping(row.get("funnel"), "track funnel") for row in selected])
        payload = {
            field: value,
            "trackCount": len(selected),
            "funnel": funnel,
            "funnelSha256": funnel["funnelSha256"],
        }
        rows.append(_self_hashed(payload, "rowSha256"))
    return rows


def _build_artifact(
    *,
    input_bindings: Mapping[str, Any],
    publication: Mapping[str, Any],
    shared_binding: Mapping[str, Any],
    source_beat_receipt: Mapping[str, Any],
    track_rows: Sequence[Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
    audio_lineage_projection: Mapping[str, Any],
    audio_group_audit: Mapping[str, Any],
    reconciliation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    observed_dataset_ids = {str(row["datasetId"]) for row in track_rows}
    required_dataset_ids = set(_examples.LABEL_DETERMINACY_DATASET_IDS)
    if observed_dataset_ids != required_dataset_ids:
        raise BeatCellStage1Error("Stage-1 requires support from the exact five certification datasets.")
    guitar_roles = {str(row["guitarsetRole"]) for row in track_rows if row.get("datasetId") == "guitarset"}
    if guitar_roles != {"comp", "solo"}:
        raise BeatCellStage1Error("Stage-1 requires supported GuitarSet comp and solo disclosures.")
    _require_official_guitar_role_track_support(track_rows)
    structural_support = _structural_support_from_track_rows(track_rows)
    if structural_support != OFFICIAL_STRUCTURAL_SUPPORT:
        raise BeatCellStage1Error("Stage-1 track rows do not preserve the official structural denominators.")
    aggregate = _sum_funnels([_mapping(row.get("funnel"), "track funnel") for row in track_rows])
    guitar_tracks = [row for row in track_rows if row.get("datasetId") == "guitarset"]
    guitarset = _sum_funnels([_mapping(row.get("funnel"), "GuitarSet track funnel") for row in guitar_tracks])
    dataset_ids = list(_examples.LABEL_DETERMINACY_DATASET_IDS)
    dataset_rows = _stratum_rows(track_rows, "datasetId", dataset_ids)
    guitar_role_rows = _stratum_rows(guitar_tracks, "guitarsetRole", ("comp", "solo"))
    gates = build_stage1_gates(aggregate, guitarset)
    passed = all(bool(gate["passed"]) for gate in gates)
    failed_gate_ids = [str(gate["gateId"]) for gate in gates if not gate["passed"]]
    reference_reconciliation = _examples._reference_endpoint_reconciliation_audit(
        reconciliation_rows, projection_tracks
    )
    source_group_track_set_sha256 = canonical_sha256(
        [
            {
                "trackId": row["trackId"],
                "trackMetadataSha256": row["sourceGroupTrackMetadataSha256"],
            }
            for row in track_rows
        ]
    )
    decision_payload = {
        "stage1Passed": passed,
        "selectorStageMayRunInNewSealedDevelopmentCycle": passed,
        "selectorUseAllowed": False,
        "failedGateIds": failed_gate_ids,
        "gateCount": len(gates),
        "passedGateCount": len(gates) - len(failed_gate_ids),
        "calibrationMayOpenOnce": False,
        "calibrationStatus": "closed",
        "promotionEligible": False,
    }
    decision = _self_hashed(decision_payload, "decisionSha256")
    payload = {
        "schemaVersion": STAGE1_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "selectorFitted": False,
        "selectorUseAllowed": False,
        "operatingThreshold": None,
        "purpose": "exact-runtime-beat-cell structural observability and oracle correct-support feasibility only",
        "publication": dict(publication),
        "inputBindings": dict(input_bindings),
        "inputBindingsSha256": canonical_sha256(input_bindings),
        "sourceContract": deepcopy(STAGE1_SOURCE_CONTRACT),
        "sourceContractSha256": STAGE1_SOURCE_CONTRACT_SHA256,
        "officialBeatReceiptContract": deepcopy(OFFICIAL_BEAT_RECEIPT_CONTRACT),
        "officialBeatReceiptContractSha256": OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256,
        "sourceBeatReceipt": deepcopy(source_beat_receipt),
        "sourceBeatReceiptSha256": source_beat_receipt["receiptSha256"],
        "constructionPolicy": deepcopy(CONSTRUCTION_POLICY),
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "scoringPolicy": deepcopy(SCORING_POLICY),
        "scoringPolicySha256": SCORING_POLICY_SHA256,
        "rubric": deepcopy(STAGE1_RUBRIC),
        "rubricSha256": STAGE1_RUBRIC_SHA256,
        "sharedPredictionRuntimeBinding": dict(shared_binding),
        "sharedPredictionRuntimeBindingSha256": canonical_sha256(shared_binding),
        "sourceAudioLineageProjection": dict(audio_lineage_projection),
        "sourceAudioLineageProjectionSha256": audio_lineage_projection["projectionSha256"],
        "audioGroupAudit": dict(audio_group_audit),
        "audioGroupAuditSha256": audio_group_audit["auditSha256"],
        "referenceEndpointReconciliationAudit": reference_reconciliation,
        "referenceEndpointReconciliationAuditSha256": reference_reconciliation["auditSha256"],
        "tracks": [dict(row) for row in track_rows],
        "trackSetSha256": canonical_sha256(track_rows),
        "sourceGroupTrackSetSha256": source_group_track_set_sha256,
        "structuralSupport": structural_support,
        "structuralSupportSha256": structural_support["supportSha256"],
        "datasets": dataset_rows,
        "datasetSetSha256": canonical_sha256(dataset_rows),
        "aggregate": aggregate,
        "aggregateFunnelSha256": aggregate["funnelSha256"],
        "guitarset": {
            "trackCount": len(guitar_tracks),
            "funnel": guitarset,
            "funnelSha256": guitarset["funnelSha256"],
            "compSolo": guitar_role_rows,
            "compSoloSetSha256": canonical_sha256(guitar_role_rows),
            "roleSpecificGates": False,
        },
        "gates": gates,
        "gateSetSha256": canonical_sha256(gates),
        "decision": decision,
        "stage1Passed": passed,
        "calibrationMayOpenOnce": False,
        "calibrationStatus": "closed",
    }
    return _self_hashed(payload, "artifactSha256")


def _validate_construction(
    construction: Mapping[str, Any],
    name: str,
    *,
    source_receipt_track: Mapping[str, Any] | None = None,
    expected_track_id: str | None = None,
) -> None:
    _exact_fields(
        construction,
        {
            "schemaVersion",
            "constructionPolicySha256",
            "officialBeatReceiptContractSha256",
            "sourceBeatReceiptFileSha256",
            "sourceBeatReceiptSha256",
            "sourceTrackReceiptSha256",
            "sourceTopologySha256",
            "sourceBeatAnalyzerContractSha256",
            "sourcePlayerReplayContractSha256",
            "timingArtifactSha256",
            "timingContractSha256",
            "timingSourceContractSha256",
            "beatCount",
            "cellCount",
            "prefixMilliseconds",
            "canonicalDurationMilliseconds",
            "coveredDurationMilliseconds",
            "cells",
            "cellSetSha256",
            "identities",
            "derivedCellTimingContractSha256",
            "constructionSha256",
        },
        name,
    )
    _validate_self_hash(construction, "constructionSha256", name)
    if construction.get("schemaVersion") != CONSTRUCTION_SCHEMA:
        raise BeatCellStage1Error(f"{name} uses an unsupported schemaVersion.")
    if construction.get("constructionPolicySha256") != CONSTRUCTION_POLICY_SHA256:
        raise BeatCellStage1Error(f"{name} changed the frozen construction policy.")
    if construction.get("officialBeatReceiptContractSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256:
        raise BeatCellStage1Error(f"{name} changed the official beat-receipt contract.")
    for field in (
        "sourceBeatReceiptFileSha256",
        "sourceBeatReceiptSha256",
        "sourceTrackReceiptSha256",
        "sourceTopologySha256",
        "sourceBeatAnalyzerContractSha256",
        "sourcePlayerReplayContractSha256",
        "timingArtifactSha256",
        "timingContractSha256",
        "timingSourceContractSha256",
        "derivedCellTimingContractSha256",
    ):
        _sha(construction.get(field), f"{name}.{field}")
    cells = list(_sequence(construction.get("cells"), f"{name}.cells"))
    if canonical_sha256(cells) != construction.get("cellSetSha256"):
        raise BeatCellStage1Error(f"{name}.cellSetSha256 is stale.")
    beat_count = _integer(construction.get("beatCount"), f"{name}.beatCount", minimum=1)
    if len(cells) != beat_count or construction.get("cellCount") != len(cells):
        raise BeatCellStage1Error(f"{name} does not contain exactly one cell per beat.")
    prefix_ms = _integer(construction.get("prefixMilliseconds"), f"{name}.prefixMilliseconds")
    duration_ms = _integer(
        construction.get("canonicalDurationMilliseconds"), f"{name}.canonicalDurationMilliseconds", minimum=1
    )
    covered_ms = _integer(
        construction.get("coveredDurationMilliseconds"), f"{name}.coveredDurationMilliseconds", minimum=1
    )
    duration_sum = 0
    for index, raw in enumerate(cells):
        cell = _mapping(raw, f"{name}.cells[{index}]")
        _exact_fields(
            cell,
            {
                "beatIndex",
                "retainedBarIndex",
                "pulseNumber",
                "downbeatCandidate",
                "startMs",
                "endMs",
                "durationMilliseconds",
            },
            f"{name}.cells[{index}]",
        )
        if (
            cell.get("beatIndex") != index
            or isinstance(cell.get("downbeatCandidate"), bool) is False
            or _integer(cell.get("retainedBarIndex"), "cell.retainedBarIndex") < 0
            or _integer(cell.get("pulseNumber"), "cell.pulseNumber", minimum=1) < 1
        ):
            raise BeatCellStage1Error(f"{name} cell identity is stale.")
        start = _integer(cell.get("startMs"), "cell.startMs")
        end = _integer(cell.get("endMs"), "cell.endMs", minimum=1)
        duration = _integer(cell.get("durationMilliseconds"), "cell.durationMilliseconds", minimum=1)
        if end - start != duration or (index and start != cells[index - 1]["endMs"]):
            raise BeatCellStage1Error(f"{name} cell duration is stale.")
        duration_sum += duration
    if (
        cells[0]["startMs"] != prefix_ms
        or cells[-1]["endMs"] != duration_ms
        or duration_sum != covered_ms
        or covered_ms != duration_ms - prefix_ms
    ):
        raise BeatCellStage1Error(f"{name} cells do not preserve exact receipt prefix-to-duration coverage.")
    identities = _mapping(construction.get("identities"), f"{name}.identities")
    _exact_fields(
        identities,
        {
            "exactSourceRowsPreserved",
            "oneCellPerBeat",
            "allCellsNonempty",
            "allCellsContiguous",
            "prefixPreserved",
            "terminalDurationPreserved",
            "cellDurationSumEqualsReceiptCoveredDuration",
        },
        f"{name}.identities",
    )
    if set(identities.values()) != {True}:
        raise BeatCellStage1Error(f"{name} construction identities are not all certified.")
    expected_derived_contract_sha256 = canonical_sha256(_derived_timing_payload_from_construction(construction))
    if construction.get("derivedCellTimingContractSha256") != expected_derived_contract_sha256:
        raise BeatCellStage1Error(f"{name} derived cell-timing contract is stale.")
    if source_receipt_track is not None:
        source = _mapping(source_receipt_track, f"{name}.sourceReceiptTrack")
        claimed_track = _sha(source.get("trackReceiptSha256"), f"{name}.sourceReceiptTrack.trackReceiptSha256")
        if (
            canonical_sha256({key: item for key, item in source.items() if key != "trackReceiptSha256"})
            != claimed_track
        ):
            raise BeatCellStage1Error(f"{name} source receipt track hash is stale.")
        topology_payload = {
            "beatTimesMs": source.get("beatTimesMs"),
            "barStartsMs": source.get("barStartsMs"),
            "durationMilliseconds": source.get("durationMilliseconds"),
            "beatsPerBar": source.get("beatsPerBar"),
            "beatCells": source.get("beatCells"),
        }
        parent_timing = _mapping(source.get("parentTimingBinding"), f"{name}.sourceReceiptTrack.parentTimingBinding")
        if (
            construction.get("sourceBeatReceiptFileSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"]
            or construction.get("sourceBeatReceiptSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"]
        ):
            raise BeatCellStage1Error(f"{name} changed the exact official receipt binding.")
        if construction.get("sourceBeatAnalyzerContractSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT[
            "beatAnalyzerContractSha256"
        ] or construction.get("sourceBeatAnalyzerContractSha256") != source.get("beatAnalyzerContractSha256"):
            raise BeatCellStage1Error(f"{name} changed the exact beat-analyzer binding.")
        if construction.get("sourcePlayerReplayContractSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT[
            "playerReplayContractSha256"
        ] or construction.get("sourcePlayerReplayContractSha256") != source.get("playerReplayContractSha256"):
            raise BeatCellStage1Error(f"{name} changed the exact player-replay binding.")
        if (
            construction.get("timingArtifactSha256") != parent_timing.get("timingSha256")
            or construction.get("timingContractSha256") != parent_timing.get("timingContractSha256")
            or construction.get("timingSourceContractSha256") != parent_timing.get("timingSourceContractSha256")
        ):
            raise BeatCellStage1Error(f"{name} changed the exact parent timing receipt track binding.")
        if (
            list(_sequence(source.get("beatCells"), f"{name}.sourceReceiptTrack.beatCells")) != cells
            or canonical_sha256(topology_payload) != source.get("topologySha256")
            or (expected_track_id is not None and source.get("trackId") != expected_track_id)
            or claimed_track != construction.get("sourceTrackReceiptSha256")
            or source.get("topologySha256") != construction.get("sourceTopologySha256")
            or source.get("durationMilliseconds") != duration_ms
            or source.get("prefixExcludedMilliseconds") != prefix_ms
            or source.get("coveredDurationMilliseconds") != covered_ms
            or source.get("beatCount") != beat_count
        ):
            raise BeatCellStage1Error(f"{name} cells do not exactly bind their official receipt track.")


def _validate_funnel(funnel: Mapping[str, Any], name: str) -> None:
    _validate_self_hash(funnel, "funnelSha256", name)
    expected = make_funnel(
        _mapping(funnel.get("counts"), f"{name}.counts"),
        _mapping(funnel.get("durationMilliseconds"), f"{name}.durationMilliseconds"),
    )
    if dict(funnel) != expected:
        raise BeatCellStage1Error(f"{name} rates or identities are stale.")


def _validate_outcome_evidence(outcome: Mapping[str, Any], cell: Mapping[str, Any], name: str) -> None:
    _exact_fields(
        outcome,
        {
            "cellIndex",
            "sourceBeatCellSha256",
            "beatIndex",
            "retainedBarIndex",
            "pulseNumber",
            "downbeatCandidate",
            "durationMilliseconds",
            "referenceProduct",
            "referenceCoveredDurationSeconds",
            "referenceProductDurationSeconds",
            "referenceCoverage",
            "referenceDominance",
            "predictionProduct",
            "predictionCoveredDurationSeconds",
            "predictionProductDurationSeconds",
            "predictionCoverage",
            "predictionDominance",
            "classification",
            "reason",
            "rowSha256",
        },
        name,
    )
    if (
        outcome.get("cellIndex") != cell.get("beatIndex")
        or outcome.get("sourceBeatCellSha256") != canonical_sha256(cell)
        or outcome.get("beatIndex") != cell.get("beatIndex")
        or outcome.get("retainedBarIndex") != cell.get("retainedBarIndex")
        or outcome.get("pulseNumber") != cell.get("pulseNumber")
        or outcome.get("downbeatCandidate") != cell.get("downbeatCandidate")
        or outcome.get("durationMilliseconds") != cell.get("durationMilliseconds")
    ):
        raise BeatCellStage1Error(f"{name} identity disagrees with its constructed cell.")
    interval = _integer(cell.get("durationMilliseconds"), "cell.durationMilliseconds", minimum=1) / 1000
    reference_covered = _finite(outcome.get("referenceCoveredDurationSeconds"), f"{name}.referenceCovered")
    reference_product_duration = _finite(
        outcome.get("referenceProductDurationSeconds"), f"{name}.referenceProductDuration"
    )
    prediction_covered = _finite(outcome.get("predictionCoveredDurationSeconds"), f"{name}.predictionCovered")
    prediction_product_duration = _finite(
        outcome.get("predictionProductDurationSeconds"), f"{name}.predictionProductDuration"
    )
    if not (
        0 <= reference_product_duration <= reference_covered <= interval
        and 0 <= prediction_product_duration <= prediction_covered <= interval
    ):
        raise BeatCellStage1Error(f"{name} overlap durations are outside the exact cell interval.")
    expected_values = {
        "referenceCoverage": min(1.0, max(0.0, reference_covered / interval)),
        "referenceDominance": min(1.0, max(0.0, reference_product_duration / interval)),
        "predictionCoverage": min(1.0, max(0.0, prediction_covered / interval)),
        "predictionDominance": (
            min(1.0, max(0.0, prediction_product_duration / prediction_covered)) if prediction_covered > 1e-9 else 0.0
        ),
    }
    for field, expected in expected_values.items():
        if outcome.get(field) != expected:
            raise BeatCellStage1Error(f"{name}.{field} is stale.")
    for prefix, covered, product_duration in (
        ("reference", reference_covered, reference_product_duration),
        ("prediction", prediction_covered, prediction_product_duration),
    ):
        field = f"{prefix}Product"
        product = outcome.get(field)
        if product is None:
            if covered != 0.0 or product_duration != 0.0:
                raise BeatCellStage1Error(f"{name}.{field} cannot be null with positive overlap evidence.")
        else:
            if not isinstance(product, str) or not product:
                raise BeatCellStage1Error(f"{name}.{field} must be null or nonempty.")
            if covered <= 0 or product_duration <= 0:
                raise BeatCellStage1Error(f"{name}.{field} requires positive overlap evidence.")
            if _bar_product._segment_product({"productLabel": product}) != product:
                raise BeatCellStage1Error(f"{name}.{field} is not a canonical Play Along product.")
    expected_classification, expected_reason = _classification_from_evidence(outcome)
    if outcome.get("classification") != expected_classification or outcome.get("reason") != expected_reason:
        raise BeatCellStage1Error(f"{name} classification/reason is stale.")


def _validate_embedded_official_beat_receipt(receipt: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    """Rebuild the full exact receipt binding without filesystem or label access."""

    value = _mapping(receipt, "sourceBeatReceipt")
    expected_fields = {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "referenceFree",
        "runtimeAttested",
        "stage1UseAllowed",
        "selectorUseAllowed",
        "playerPlaybackUseAllowed",
        "confidenceUse",
        "publicationPolicy",
        "parentRuntimeBinding",
        "analyzerContract",
        "playerReplayContract",
        "sourceManifestSetSha256",
        "sourceManifests",
        "receiptTotals",
        "receiptTotalsSha256",
        "trackSetSha256",
        "tracks",
        "receiptSha256",
    }
    _exact_fields(value, expected_fields, "sourceBeatReceipt")
    contract = OFFICIAL_BEAT_RECEIPT_CONTRACT
    payload = {key: item for key, item in value.items() if key != "receiptSha256"}
    rendered = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    analyzer = _mapping(value.get("analyzerContract"), "sourceBeatReceipt.analyzerContract")
    player = _mapping(value.get("playerReplayContract"), "sourceBeatReceipt.playerReplayContract")
    parent = _mapping(value.get("parentRuntimeBinding"), "sourceBeatReceipt.parentRuntimeBinding")
    if (
        value.get("schemaVersion") != contract["receiptSchemaVersion"]
        or value.get("receiptSha256") != contract["receiptSha256"]
        or canonical_sha256(payload) != contract["receiptSha256"]
        or hashlib.sha256(rendered).hexdigest() != contract["fileSha256"]
        or value.get("trackSetSha256") != contract["trackSetSha256"]
        or value.get("receiptTotals") != contract["receiptTotals"]
        or value.get("receiptTotalsSha256") != contract["receiptTotalsSha256"]
        or canonical_sha256(value.get("receiptTotals")) != contract["receiptTotalsSha256"]
        or analyzer.get("contractSha256") != contract["beatAnalyzerContractSha256"]
        or player.get("contractSha256") != contract["playerReplayContractSha256"]
        or parent.get("manifestSha256") != contract["parentRuntimeManifestSha256"]
        or parent.get("trackSetSha256") != contract["parentRuntimeTrackSetSha256"]
        or value.get("split") != DEVELOPMENT_SPLIT
        or value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
        or value.get("referenceFree") is not True
        or value.get("runtimeAttested") is not True
        or value.get("stage1UseAllowed") is not True
        or value.get("selectorUseAllowed") is not False
        or value.get("playerPlaybackUseAllowed") is not False
    ):
        raise BeatCellStage1Error("Embedded beat receipt is not the exact independently frozen receipt.")
    tracks = [
        dict(_mapping(row, f"sourceBeatReceipt.tracks[{index}]"))
        for index, row in enumerate(_sequence(value.get("tracks"), "sourceBeatReceipt.tracks"))
    ]
    if len(tracks) != contract["receiptTotals"]["trackCount"] or tracks != sorted(
        tracks, key=lambda row: str(row.get("trackId"))
    ):
        raise BeatCellStage1Error("Embedded beat receipt track inventory is stale.")
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, track in enumerate(tracks):
        track_id = track.get("trackId")
        if not isinstance(track_id, str) or not track_id or track_id in by_id:
            raise BeatCellStage1Error("Embedded beat receipt track ids must be nonempty and unique.")
        claimed = _sha(track.get("trackReceiptSha256"), f"sourceBeatReceipt.tracks[{index}].trackReceiptSha256")
        if canonical_sha256({key: item for key, item in track.items() if key != "trackReceiptSha256"}) != claimed:
            raise BeatCellStage1Error("Embedded beat receipt track hash is stale.")
        by_id[track_id] = track
    track_set = canonical_sha256(
        [{"trackId": track["trackId"], "trackReceiptSha256": track["trackReceiptSha256"]} for track in tracks]
    )
    totals = {
        "trackCount": len(tracks),
        "beatCellCount": sum(_integer(track.get("beatCount"), "beatCount", minimum=1) for track in tracks),
        "sourceDurationMilliseconds": sum(
            _integer(track.get("durationMilliseconds"), "durationMilliseconds", minimum=1) for track in tracks
        ),
        "coveredDurationMilliseconds": sum(
            _integer(track.get("coveredDurationMilliseconds"), "coveredDurationMilliseconds", minimum=1)
            for track in tracks
        ),
        "excludedPrefixDurationMilliseconds": sum(
            _integer(track.get("prefixExcludedMilliseconds"), "prefixExcludedMilliseconds") for track in tracks
        ),
    }
    if track_set != contract["trackSetSha256"] or totals != contract["receiptTotals"]:
        raise BeatCellStage1Error("Embedded beat receipt track set or totals are stale.")
    return by_id


def validate_beat_cell_stage1_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed on any stale construction, outcome, funnel, stratum, or gate."""

    value = dict(_mapping(artifact, "Stage-1 artifact"))
    expected_top_fields = {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "selectorFitted",
        "selectorUseAllowed",
        "operatingThreshold",
        "purpose",
        "publication",
        "inputBindings",
        "inputBindingsSha256",
        "sourceContract",
        "sourceContractSha256",
        "officialBeatReceiptContract",
        "officialBeatReceiptContractSha256",
        "sourceBeatReceipt",
        "sourceBeatReceiptSha256",
        "constructionPolicy",
        "constructionPolicySha256",
        "scoringPolicy",
        "scoringPolicySha256",
        "rubric",
        "rubricSha256",
        "sharedPredictionRuntimeBinding",
        "sharedPredictionRuntimeBindingSha256",
        "sourceAudioLineageProjection",
        "sourceAudioLineageProjectionSha256",
        "audioGroupAudit",
        "audioGroupAuditSha256",
        "referenceEndpointReconciliationAudit",
        "referenceEndpointReconciliationAuditSha256",
        "tracks",
        "trackSetSha256",
        "sourceGroupTrackSetSha256",
        "structuralSupport",
        "structuralSupportSha256",
        "datasets",
        "datasetSetSha256",
        "aggregate",
        "aggregateFunnelSha256",
        "guitarset",
        "gates",
        "gateSetSha256",
        "decision",
        "stage1Passed",
        "calibrationMayOpenOnce",
        "calibrationStatus",
        "artifactSha256",
    }
    _exact_fields(value, expected_top_fields, "Stage-1 artifact")
    _validate_self_hash(value, "artifactSha256", "Stage-1 artifact")
    if (
        value.get("schemaVersion") != STAGE1_SCHEMA
        or value.get("split") != DEVELOPMENT_SPLIT
        or value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
        or value.get("selectorFitted") is not False
        or value.get("selectorUseAllowed") is not False
        or value.get("operatingThreshold") is not None
        or value.get("purpose")
        != "exact-runtime-beat-cell structural observability and oracle correct-support feasibility only"
        or value.get("calibrationMayOpenOnce") is not False
        or value.get("calibrationStatus") != "closed"
    ):
        raise BeatCellStage1Error("Stage-1 envelope or closed-calibration contract is invalid.")
    if (
        value.get("constructionPolicy") != CONSTRUCTION_POLICY
        or value.get("constructionPolicySha256") != CONSTRUCTION_POLICY_SHA256
    ):
        raise BeatCellStage1Error("Stage-1 construction policy is not exact.")
    if (
        value.get("officialBeatReceiptContract") != OFFICIAL_BEAT_RECEIPT_CONTRACT
        or value.get("officialBeatReceiptContractSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256
    ):
        raise BeatCellStage1Error("Stage-1 official beat-receipt contract is not exact.")
    source_beat_tracks = _validate_embedded_official_beat_receipt(
        _mapping(value.get("sourceBeatReceipt"), "sourceBeatReceipt")
    )
    if value.get("sourceBeatReceiptSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"]:
        raise BeatCellStage1Error("Stage-1 embedded beat-receipt hash is stale.")
    if value.get("scoringPolicy") != SCORING_POLICY or value.get("scoringPolicySha256") != SCORING_POLICY_SHA256:
        raise BeatCellStage1Error("Stage-1 scoring policy is not exact.")
    if (
        value.get("sourceContract") != STAGE1_SOURCE_CONTRACT
        or value.get("sourceContractSha256") != STAGE1_SOURCE_CONTRACT_SHA256
    ):
        raise BeatCellStage1Error("Stage-1 official source contract is not exact.")
    if value.get("rubric") != STAGE1_RUBRIC or value.get("rubricSha256") != STAGE1_RUBRIC_SHA256:
        raise BeatCellStage1Error("Stage-1 rubric is not exact.")
    if canonical_sha256(value["inputBindings"]) != value.get("inputBindingsSha256"):
        raise BeatCellStage1Error("Stage-1 input bindings hash is stale.")
    input_bindings = _mapping(value["inputBindings"], "inputBindings")
    _validate_self_hash(input_bindings, "bindingsSha256", "inputBindings")
    _exact_fields(
        input_bindings,
        {
            "schemaVersion",
            "benchmarkReport",
            "benchmarkRoot",
            "audioLineage",
            "runtimeManifest",
            "runtimeRoot",
            "beatReceipt",
            "groupManifest",
            "groupRoot",
            "summaryOutputRoot",
            "bindingsSha256",
        },
        "inputBindings",
    )
    if input_bindings.get("schemaVersion") != "chord_runtime_beat_cell_stage1_input_bindings_v1":
        raise BeatCellStage1Error("Stage-1 input bindings schema is not exact.")

    def validate_top_path_binding(
        binding: Mapping[str, Any],
        name: str,
        extras: set[str],
        *,
        canonical_required: bool,
    ) -> None:
        expected = {"path", "pathSha256", "fileSha256", "claimedArtifactSha256", *extras}
        if canonical_required:
            expected.add("canonicalSha256")
        _exact_fields(binding, expected, name)
        path = binding.get("path")
        if (
            not isinstance(path, str)
            or str(_absolute(Path(path))) != path
            or canonical_sha256(path) != binding.get("pathSha256")
        ):
            raise BeatCellStage1Error(f"{name} path binding is stale.")
        _sha(binding.get("fileSha256"), f"{name}.fileSha256")
        claimed = binding.get("claimedArtifactSha256")
        if claimed is not None:
            _sha(claimed, f"{name}.claimedArtifactSha256")
        if canonical_required:
            _sha(binding.get("canonicalSha256"), f"{name}.canonicalSha256")

    publication = _mapping(value.get("publication"), "publication")
    _exact_fields(
        publication,
        {
            "mode",
            "outputPath",
            "outputPathSha256",
            "summaryOutputRoot",
            "summaryOutputRootSha256",
        },
        "publication",
    )
    summary_output_binding = _mapping(input_bindings.get("summaryOutputRoot"), "inputBindings.summaryOutputRoot")
    _exact_fields(summary_output_binding, {"path", "pathSha256"}, "inputBindings.summaryOutputRoot")
    output_path = publication.get("outputPath")
    summary_output_root = publication.get("summaryOutputRoot")
    if (
        publication.get("mode") != "atomic-new-json-and-summary-directory-set-v1"
        or not isinstance(output_path, str)
        or not isinstance(summary_output_root, str)
        or str(_absolute(Path(output_path))) != output_path
        or str(_absolute(Path(summary_output_root))) != summary_output_root
        or Path(output_path).suffix.lower() != ".json"
        or canonical_sha256(output_path) != publication.get("outputPathSha256")
        or canonical_sha256(summary_output_root) != publication.get("summaryOutputRootSha256")
        or summary_output_binding.get("path") != summary_output_root
        or summary_output_binding.get("pathSha256") != publication.get("summaryOutputRootSha256")
        or canonical_sha256(summary_output_binding.get("path")) != summary_output_binding.get("pathSha256")
        or Path(output_path) == Path(summary_output_root)
        or Path(output_path).is_relative_to(Path(summary_output_root))
        or Path(summary_output_root).is_relative_to(Path(output_path))
    ):
        raise BeatCellStage1Error("Stage-1 publication binding is stale or not an atomic disjoint new-path set.")
    source_root_paths: dict[str, Path] = {}
    for root_name in ("benchmarkRoot", "runtimeRoot", "groupRoot"):
        root_binding = _mapping(input_bindings.get(root_name), f"inputBindings.{root_name}")
        _exact_fields(root_binding, {"path", "pathSha256"}, f"inputBindings.{root_name}")
        root_path = root_binding.get("path")
        if (
            not isinstance(root_path, str)
            or str(_absolute(Path(root_path))) != root_path
            or canonical_sha256(root_path) != root_binding.get("pathSha256")
            or Path(output_path).is_relative_to(Path(root_path))
            or Path(root_path).is_relative_to(Path(output_path))
            or Path(summary_output_root).is_relative_to(Path(root_path))
            or Path(root_path).is_relative_to(Path(summary_output_root))
        ):
            raise BeatCellStage1Error("Stage-1 publication paths must remain disjoint from every source root.")
        source_root_paths[root_name] = Path(root_path)
    report_binding = _mapping(input_bindings.get("benchmarkReport"), "inputBindings.benchmarkReport")
    validate_top_path_binding(
        report_binding,
        "inputBindings.benchmarkReport",
        {"trackSetSha256", "modelOrEnsembleSha256", "predictionSets"},
        canonical_required=True,
    )
    if report_binding.get("claimedArtifactSha256") is not None:
        raise BeatCellStage1Error("Benchmark report must not invent a top-level self hash.")
    prediction_sets = _mapping(report_binding.get("predictionSets"), "benchmarkReport.predictionSets")
    _exact_fields(
        prediction_sets,
        {
            "predictionArtifactSetSha256",
            "predictionCoreSetSha256",
            "uncertaintySetSha256",
            "allThreeDistinct",
            "bindingsSha256",
        },
        "benchmarkReport.predictionSets",
    )
    _validate_self_hash(prediction_sets, "bindingsSha256", "benchmarkReport.predictionSets")
    if (
        prediction_sets.get("allThreeDistinct") is not True
        or len(
            {
                prediction_sets.get("predictionArtifactSetSha256"),
                prediction_sets.get("predictionCoreSetSha256"),
                prediction_sets.get("uncertaintySetSha256"),
            }
        )
        != 3
    ):
        raise BeatCellStage1Error("Benchmark prediction set bindings are aliased or stale.")
    source_contract = STAGE1_SOURCE_CONTRACT
    if (
        report_binding.get("fileSha256") != source_contract["benchmarkReport"]["fileSha256"]
        or report_binding.get("canonicalSha256") != source_contract["benchmarkReport"]["canonicalSha256"]
        or report_binding.get("trackSetSha256") != source_contract["benchmarkReport"]["trackSetSha256"]
        or report_binding.get("modelOrEnsembleSha256") != source_contract["benchmarkReport"]["modelOrEnsembleSha256"]
        or prediction_sets.get("predictionArtifactSetSha256")
        != source_contract["benchmarkReport"]["predictionArtifactSetSha256"]
        or prediction_sets.get("predictionCoreSetSha256")
        != source_contract["benchmarkReport"]["predictionCoreSetSha256"]
        or prediction_sets.get("uncertaintySetSha256") != source_contract["benchmarkReport"]["uncertaintySetSha256"]
    ):
        raise BeatCellStage1Error("Benchmark input binding disagrees with the official source contract.")
    for binding_name, contract_name, claimed_field in (
        ("runtimeManifest", "runtimeManifest", "manifestSha256"),
        ("groupManifest", "groupManifest", "manifestSha256"),
        ("audioLineage", "audioLineage", "artifactSha256"),
    ):
        binding = _mapping(input_bindings.get(binding_name), f"inputBindings.{binding_name}")
        expected = _mapping(source_contract[contract_name], f"sourceContract.{contract_name}")
        if (
            binding.get("fileSha256") != expected["fileSha256"]
            or binding.get("claimedArtifactSha256") != expected[claimed_field]
        ):
            raise BeatCellStage1Error(f"{binding_name} binding disagrees with the official source contract.")
    runtime_binding = _mapping(input_bindings.get("runtimeManifest"), "inputBindings.runtimeManifest")
    group_binding = _mapping(input_bindings.get("groupManifest"), "inputBindings.groupManifest")
    audio_binding = _mapping(input_bindings.get("audioLineage"), "inputBindings.audioLineage")
    beat_binding = _mapping(input_bindings.get("beatReceipt"), "inputBindings.beatReceipt")
    validate_top_path_binding(
        runtime_binding,
        "inputBindings.runtimeManifest",
        {"trackSetSha256", "analyzerContractSha256"},
        canonical_required=False,
    )
    validate_top_path_binding(
        group_binding,
        "inputBindings.groupManifest",
        {"trackSetSha256"},
        canonical_required=False,
    )
    validate_top_path_binding(
        audio_binding,
        "inputBindings.audioLineage",
        {"projectionSha256"},
        canonical_required=False,
    )
    validate_top_path_binding(
        beat_binding,
        "inputBindings.beatReceipt",
        {
            "trackSetSha256",
            "receiptTotalsSha256",
            "beatAnalyzerContractSha256",
            "playerReplayContractSha256",
        },
        canonical_required=True,
    )
    if Path(str(runtime_binding.get("path"))) != source_root_paths["runtimeRoot"] / "manifest.json":
        raise BeatCellStage1Error("Runtime manifest path is not exact runtimeRoot/manifest.json.")
    if (
        beat_binding.get("fileSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"]
        or beat_binding.get("claimedArtifactSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"]
        or beat_binding.get("canonicalSha256") != canonical_sha256(value["sourceBeatReceipt"])
        or beat_binding.get("trackSetSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["trackSetSha256"]
        or beat_binding.get("receiptTotalsSha256") != OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptTotalsSha256"]
        or beat_binding.get("beatAnalyzerContractSha256")
        != OFFICIAL_BEAT_RECEIPT_CONTRACT["beatAnalyzerContractSha256"]
        or beat_binding.get("playerReplayContractSha256")
        != OFFICIAL_BEAT_RECEIPT_CONTRACT["playerReplayContractSha256"]
    ):
        raise BeatCellStage1Error("Beat-receipt input binding is stale.")
    if (
        runtime_binding.get("trackSetSha256") != source_contract["runtimeManifest"]["trackSetSha256"]
        or runtime_binding.get("analyzerContractSha256") != source_contract["runtimeManifest"]["analyzerContractSha256"]
        or group_binding.get("trackSetSha256") != source_contract["groupManifest"]["trackSetSha256"]
        or audio_binding.get("projectionSha256") != source_contract["audioLineage"]["projectionSha256"]
    ):
        raise BeatCellStage1Error("Manifest/projection identity binding disagrees with the source contract.")
    shared_binding = _mapping(value["sharedPredictionRuntimeBinding"], "sharedPredictionRuntimeBinding")
    _exact_fields(
        shared_binding,
        {
            "schemaVersion",
            "uncertaintyContractSha256",
            "modelOrEnsembleSha256",
            "decoderContractSha256",
            "memberOrderSha256",
            "sourceFeatureKind",
            "sourceFeatureSpecSha256",
            "observabilityProfileSchemaVersion",
            "constructionPolicySha256",
            "scoringPolicySha256",
            "barOutcomeEligibilityContractSha256",
            "timingSourceContractSha256",
            "officialBeatReceiptContractSha256",
            "beatAnalyzerContractSha256",
            "playerReplayContractSha256",
        },
        "sharedPredictionRuntimeBinding",
    )
    if canonical_sha256(shared_binding) != value.get("sharedPredictionRuntimeBindingSha256"):
        raise BeatCellStage1Error("Stage-1 shared prediction/runtime binding hash is stale.")
    for field in (
        "uncertaintyContractSha256",
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "sourceFeatureSpecSha256",
        "constructionPolicySha256",
        "scoringPolicySha256",
        "barOutcomeEligibilityContractSha256",
        "timingSourceContractSha256",
        "officialBeatReceiptContractSha256",
        "beatAnalyzerContractSha256",
        "playerReplayContractSha256",
    ):
        _sha(shared_binding.get(field), f"sharedPredictionRuntimeBinding.{field}")
    if (
        dict(shared_binding) != STAGE1_SOURCE_CONTRACT["sharedPredictionRuntimeBinding"]
        or shared_binding.get("schemaVersion") != "chord_runtime_beat_cell_prediction_runtime_binding_v1"
        or not isinstance(shared_binding.get("sourceFeatureKind"), str)
        or not shared_binding.get("sourceFeatureKind")
        or not isinstance(shared_binding.get("observabilityProfileSchemaVersion"), str)
        or not shared_binding.get("observabilityProfileSchemaVersion")
        or shared_binding.get("modelOrEnsembleSha256")
        != STAGE1_SOURCE_CONTRACT["benchmarkReport"]["modelOrEnsembleSha256"]
        or shared_binding.get("timingSourceContractSha256")
        != STAGE1_SOURCE_CONTRACT["runtimeManifest"]["analyzerContractSha256"]
        or shared_binding.get("constructionPolicySha256") != CONSTRUCTION_POLICY_SHA256
        or shared_binding.get("scoringPolicySha256") != SCORING_POLICY_SHA256
        or shared_binding.get("barOutcomeEligibilityContractSha256")
        != _examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256
    ):
        raise BeatCellStage1Error("Stage-1 shared prediction/runtime semantics are stale.")

    tracks = [dict(_mapping(row, f"tracks[{index}]")) for index, row in enumerate(_sequence(value["tracks"], "tracks"))]
    if tracks != sorted(tracks, key=lambda row: str(row["trackId"])) or len(
        {str(row["trackId"]) for row in tracks}
    ) != len(tracks):
        raise BeatCellStage1Error("Stage-1 tracks must be unique and sorted.")
    if canonical_sha256(tracks) != value.get("trackSetSha256"):
        raise BeatCellStage1Error("Stage-1 trackSetSha256 is stale.")
    if set(source_beat_tracks) != {str(row["trackId"]) for row in tracks}:
        raise BeatCellStage1Error("Stage-1 tracks do not exactly cover the embedded beat receipt.")
    _validate_reviewed_group_shape({str(row["trackId"]): row for row in tracks})
    if {str(row.get("datasetId")) for row in tracks} != set(_examples.LABEL_DETERMINACY_DATASET_IDS):
        raise BeatCellStage1Error("Stage-1 tracks do not cover the exact five certification datasets.")
    if {str(row.get("guitarsetRole")) for row in tracks if row.get("datasetId") == "guitarset"} != {"comp", "solo"}:
        raise BeatCellStage1Error("Stage-1 tracks do not support both GuitarSet role disclosures.")
    _require_official_guitar_role_track_support(tracks)

    projection = _mapping(value.get("sourceAudioLineageProjection"), "sourceAudioLineageProjection")
    _validate_self_hash(projection, "projectionSha256", "sourceAudioLineageProjection")
    if projection.get("projectionSha256") != value.get("sourceAudioLineageProjectionSha256"):
        raise BeatCellStage1Error("Audio-lineage projection top-level binding is stale.")
    if (
        projection.get("projectionSha256") != STAGE1_SOURCE_CONTRACT["audioLineage"]["projectionSha256"]
        or projection.get("trackCount") != STAGE1_SOURCE_CONTRACT["trackCount"]
    ):
        raise BeatCellStage1Error("Audio-lineage projection is not the official 246-track projection.")
    projection_rows = [
        dict(_mapping(row, f"sourceAudioLineageProjection.tracks[{index}]"))
        for index, row in enumerate(_sequence(projection.get("tracks"), "sourceAudioLineageProjection.tracks"))
    ]
    if (
        projection.get("trackCount") != len(projection_rows)
        or canonical_sha256(projection_rows) != projection.get("trackSetSha256")
        or [row.get("trackId") for row in projection_rows] != [row.get("trackId") for row in tracks]
        or len({row.get("trackId") for row in projection_rows}) != len(projection_rows)
    ):
        raise BeatCellStage1Error("Audio-lineage projection track identities are stale.")
    projection_tracks = {str(row["trackId"]): row for row in projection_rows}
    for row in tracks:
        projected = projection_tracks[str(row["trackId"])]
        track_construction = _mapping(row.get("construction"), "track construction")
        if row.get("datasetId") != projected.get("datasetId") or track_construction.get(
            "canonicalDurationMilliseconds"
        ) != projected.get("canonicalDurationMilliseconds"):
            raise BeatCellStage1Error("Track dataset/duration disagrees with audio-lineage projection.")
    group_projection = {str(row["trackId"]): {"confidenceGroupId": row["confidenceGroupId"]} for row in tracks}
    expected_audio_audit = _examples._audio_group_audit(
        [str(row["trackId"]) for row in tracks], group_projection, projection_tracks
    )
    if (
        value.get("audioGroupAudit") != expected_audio_audit
        or value.get("audioGroupAuditSha256") != expected_audio_audit["auditSha256"]
    ):
        raise BeatCellStage1Error("Audio duplicate-group audit is stale.")
    for index, row in enumerate(tracks):
        _exact_fields(
            row,
            {
                "trackId",
                "split",
                "datasetId",
                "role",
                "guitarsetRole",
                "confidenceGroupId",
                "sourceGroupTrack",
                "sourceGroupTrackMetadataSha256",
                "predictionIdentity",
                "predictionIdentitySha256",
                "sourceBeatReceiptTrackSha256",
                "sourceTopologySha256",
                "timingArtifactSha256",
                "timingContractSha256",
                "timingSourceContractSha256",
                "sourceReferenceSha256",
                "referenceEndpointReconciliationRowSha256",
                "predictionOnlySummary",
                "construction",
                "constructionSha256",
                "beatCount",
                "cellCount",
                "coveredDurationMilliseconds",
                "cellOutcomes",
                "cellOutcomeSetSha256",
                "funnel",
                "funnelSha256",
                "exclusionAudit",
                "exclusionAuditSha256",
                "rowSha256",
            },
            f"tracks[{index}]",
        )
        _validate_self_hash(row, "rowSha256", f"tracks[{index}]")
        for field in (
            "sourceGroupTrackMetadataSha256",
            "predictionIdentitySha256",
            "sourceBeatReceiptTrackSha256",
            "sourceTopologySha256",
            "sourceReferenceSha256",
            "constructionSha256",
            "cellOutcomeSetSha256",
            "funnelSha256",
            "exclusionAuditSha256",
        ):
            _sha(row.get(field), f"tracks[{index}].{field}")
        reconciliation_binding = row.get("referenceEndpointReconciliationRowSha256")
        if reconciliation_binding is not None:
            _sha(reconciliation_binding, f"tracks[{index}].referenceEndpointReconciliationRowSha256")
        _validate_source_group_track_binding(row, f"tracks[{index}]")
        prediction_identity = _mapping(row.get("predictionIdentity"), f"tracks[{index}].predictionIdentity")
        expected_prediction_identity = _prediction_identity(prediction_identity)
        if (
            dict(prediction_identity) != expected_prediction_identity
            or prediction_identity.get("id") != row.get("trackId")
            or prediction_identity.get("predictionIdentitySha256") != row.get("predictionIdentitySha256")
            or prediction_identity.get("sourceAudioSha256")
            != projection_tracks[str(row["trackId"])].get("sourceAudioSha256")
            or prediction_identity.get("audioLineageRowSha256")
            != projection_tracks[str(row["trackId"])].get("rowSha256")
        ):
            raise BeatCellStage1Error("Track prediction identity is not exactly cross-bound.")
        construction = _mapping(row.get("construction"), f"tracks[{index}].construction")
        source_beat_track = source_beat_tracks[str(row["trackId"])]
        _validate_construction(
            construction,
            f"tracks[{index}].construction",
            source_receipt_track=source_beat_track,
            expected_track_id=str(row["trackId"]),
        )
        if (
            row.get("constructionSha256") != construction.get("constructionSha256")
            or row.get("beatCount") != construction.get("beatCount")
            or row.get("cellCount") != construction.get("cellCount")
            or row.get("coveredDurationMilliseconds") != construction.get("coveredDurationMilliseconds")
            or row.get("sourceBeatReceiptTrackSha256") != source_beat_track.get("trackReceiptSha256")
            or row.get("sourceTopologySha256") != source_beat_track.get("topologySha256")
        ):
            raise BeatCellStage1Error("Track construction hash binding is stale.")
        for field in ("timingArtifactSha256", "timingContractSha256", "timingSourceContractSha256"):
            if row.get(field) != construction.get(field):
                raise BeatCellStage1Error(f"Track {field} binding is stale.")

        prediction_summary = _mapping(row.get("predictionOnlySummary"), "track.predictionOnlySummary")
        _exact_fields(
            prediction_summary,
            {"path", "pathSha256", "artifactSha256"},
            "track.predictionOnlySummary",
        )
        for field in ("pathSha256", "artifactSha256"):
            _sha(prediction_summary.get(field), f"track.predictionOnlySummary.{field}")
        expected_summary_path = str(
            _absolute(
                Path(str(summary_output_root))
                / _summary_filename(str(row["trackId"]), str(prediction_summary["artifactSha256"]))
            )
        )
        if prediction_summary.get("path") != expected_summary_path or canonical_sha256(
            prediction_summary.get("path")
        ) != prediction_summary.get("pathSha256"):
            raise BeatCellStage1Error("Track prediction-only summary path binding is stale.")
        outcomes = [
            dict(_mapping(item, f"tracks[{index}].cellOutcomes[{outcome_index}]"))
            for outcome_index, item in enumerate(_sequence(row.get("cellOutcomes"), "cellOutcomes"))
        ]
        if len(outcomes) != row.get("cellCount") or len(outcomes) != construction.get("cellCount"):
            raise BeatCellStage1Error("Track cell outcome count is stale.")
        for outcome_index, outcome in enumerate(outcomes):
            _validate_self_hash(outcome, "rowSha256", f"tracks[{index}].cellOutcomes[{outcome_index}]")
            cell = construction["cells"][outcome_index]
            _validate_outcome_evidence(outcome, cell, f"tracks[{index}].cellOutcomes[{outcome_index}]")
        if canonical_sha256(outcomes) != row.get("cellOutcomeSetSha256"):
            raise BeatCellStage1Error("Track cellOutcomeSetSha256 is stale.")
        expected_funnel, expected_exclusions = funnel_from_outcomes(outcomes)
        if row.get("funnel") != expected_funnel or row.get("funnelSha256") != expected_funnel["funnelSha256"]:
            raise BeatCellStage1Error("Track funnel is stale.")
        if (
            row.get("exclusionAudit") != expected_exclusions
            or row.get("exclusionAuditSha256") != expected_exclusions["auditSha256"]
        ):
            raise BeatCellStage1Error("Track exclusion audit is stale.")

    prediction_identity_sets = {
        "predictionArtifactSetSha256": canonical_sha256(
            sorted(
                [
                    {"id": str(row["trackId"]), "sha256": row["predictionIdentity"]["predictionSha256"]}
                    for row in tracks
                ],
                key=lambda item: item["id"],
            )
        ),
        "predictionCoreSetSha256": canonical_sha256(
            sorted(
                [
                    {"id": str(row["trackId"]), "sha256": row["predictionIdentity"]["predictionCoreSha256"]}
                    for row in tracks
                ],
                key=lambda item: item["id"],
            )
        ),
        "uncertaintySetSha256": canonical_sha256(
            sorted(
                [
                    {"id": str(row["trackId"]), "sha256": row["predictionIdentity"]["uncertaintySha256"]}
                    for row in tracks
                ],
                key=lambda item: item["id"],
            )
        ),
    }
    if prediction_identity_sets != {
        field: STAGE1_SOURCE_CONTRACT["benchmarkReport"][field] for field in prediction_identity_sets
    }:
        raise BeatCellStage1Error("Track prediction identities do not match the frozen candidate content sets.")
    prediction_identity_set_sha256 = canonical_sha256(
        sorted(
            [
                {
                    "trackId": str(row["trackId"]),
                    "predictionIdentitySha256": row["predictionIdentitySha256"],
                }
                for row in tracks
            ],
            key=lambda item: item["trackId"],
        )
    )
    if prediction_identity_set_sha256 != STAGE1_SOURCE_CONTRACT["benchmarkReport"]["predictionIdentitySetSha256"]:
        raise BeatCellStage1Error("Track prediction-identity set is not the exact frozen candidate set.")

    source_group_track_set_sha256 = canonical_sha256(
        [
            {
                "trackId": row["trackId"],
                "trackMetadataSha256": row["sourceGroupTrackMetadataSha256"],
            }
            for row in tracks
        ]
    )
    if (
        source_group_track_set_sha256 != value.get("sourceGroupTrackSetSha256")
        or source_group_track_set_sha256 != STAGE1_SOURCE_CONTRACT["groupManifest"]["trackSetSha256"]
    ):
        raise BeatCellStage1Error("Source group track-set binding is stale.")

    structural_support = _structural_support_from_track_rows(tracks)
    if (
        structural_support != OFFICIAL_STRUCTURAL_SUPPORT
        or value.get("structuralSupport") != structural_support
        or value.get("structuralSupportSha256") != structural_support["supportSha256"]
    ):
        raise BeatCellStage1Error("Official structural denominators are stale.")

    aggregate = _sum_funnels([_mapping(row["funnel"], "track funnel") for row in tracks])
    if value.get("aggregate") != aggregate or value.get("aggregateFunnelSha256") != aggregate["funnelSha256"]:
        raise BeatCellStage1Error("Aggregate Stage-1 funnel is stale.")
    reference_audit = _mapping(
        value.get("referenceEndpointReconciliationAudit"), "referenceEndpointReconciliationAudit"
    )
    expected_reference_audit = _examples._reference_endpoint_reconciliation_audit(
        list(_sequence(reference_audit.get("rows"), "referenceEndpointReconciliationAudit.rows")),
        projection_tracks,
    )
    if (
        reference_audit != expected_reference_audit
        or value.get("referenceEndpointReconciliationAuditSha256") != expected_reference_audit["auditSha256"]
    ):
        raise BeatCellStage1Error("Reference endpoint reconciliation audit is stale.")
    audit_rows_by_sha = {str(row["rowSha256"]): row for row in expected_reference_audit["rows"]}
    track_reconciliation_bindings = [
        (str(row["trackId"]), str(row["referenceEndpointReconciliationRowSha256"]))
        for row in tracks
        if row.get("referenceEndpointReconciliationRowSha256") is not None
    ]
    bound_shas = [sha256 for _track_id, sha256 in track_reconciliation_bindings]
    if len(bound_shas) != len(set(bound_shas)) or set(bound_shas) != set(audit_rows_by_sha):
        raise BeatCellStage1Error("Track reconciliation bindings do not exactly match the audit row set.")
    tracks_by_id = {str(row["trackId"]): row for row in tracks}
    for track_id, row_sha256 in track_reconciliation_bindings:
        track = tracks_by_id[track_id]
        audit_row = audit_rows_by_sha.get(row_sha256)
        if audit_row is None or (
            audit_row.get("trackId") != track_id
            or audit_row.get("datasetId") != track.get("datasetId")
            or audit_row.get("referenceSha256") != track.get("sourceReferenceSha256")
        ):
            raise BeatCellStage1Error("A track reconciliation binding is not one-to-one with its audit row.")
    for row in expected_reference_audit["rows"]:
        track = tracks_by_id.get(str(row["trackId"]))
        if track is None or (
            track.get("referenceEndpointReconciliationRowSha256") != row.get("rowSha256")
            or track.get("datasetId") != row.get("datasetId")
            or track.get("sourceReferenceSha256") != row.get("referenceSha256")
        ):
            raise BeatCellStage1Error("A reconciliation audit row is not exactly cross-bound to its track.")
    guitar_tracks = [row for row in tracks if row.get("datasetId") == "guitarset"]
    guitar_funnel = _sum_funnels([_mapping(row["funnel"], "GuitarSet track funnel") for row in guitar_tracks])
    guitar = _mapping(value.get("guitarset"), "guitarset")
    _exact_fields(
        guitar,
        {"trackCount", "funnel", "funnelSha256", "compSolo", "compSoloSetSha256", "roleSpecificGates"},
        "guitarset",
    )
    if (
        guitar.get("trackCount") != len(guitar_tracks)
        or guitar.get("funnel") != guitar_funnel
        or guitar.get("funnelSha256") != guitar_funnel["funnelSha256"]
        or guitar.get("roleSpecificGates") is not False
    ):
        raise BeatCellStage1Error("GuitarSet aggregate is stale.")
    expected_roles = _stratum_rows(guitar_tracks, "guitarsetRole", ("comp", "solo"))
    if guitar.get("compSolo") != expected_roles or guitar.get("compSoloSetSha256") != canonical_sha256(expected_roles):
        raise BeatCellStage1Error("GuitarSet comp/solo disclosure is stale.")

    dataset_rows = list(_sequence(value.get("datasets"), "datasets"))
    if [row.get("datasetId") for row in dataset_rows if isinstance(row, Mapping)] != list(
        _examples.LABEL_DETERMINACY_DATASET_IDS
    ):
        raise BeatCellStage1Error("Dataset disclosures must use the exact five-dataset order.")
    expected_dataset_rows = _stratum_rows(tracks, "datasetId", list(_examples.LABEL_DETERMINACY_DATASET_IDS))
    if dataset_rows != expected_dataset_rows or canonical_sha256(dataset_rows) != value.get("datasetSetSha256"):
        raise BeatCellStage1Error("Dataset disclosures are stale or do not exactly sum their tracks.")

    gates = list(_sequence(value.get("gates"), "gates"))
    expected_gates = build_stage1_gates(aggregate, guitar_funnel)
    if gates != expected_gates or canonical_sha256(gates) != value.get("gateSetSha256"):
        raise BeatCellStage1Error("Stage-1 gates are stale or not the exact 13-gate rubric.")
    passed = all(bool(gate["passed"]) for gate in expected_gates)
    failed = [str(gate["gateId"]) for gate in expected_gates if not gate["passed"]]
    expected_decision_payload = {
        "stage1Passed": passed,
        "selectorStageMayRunInNewSealedDevelopmentCycle": passed,
        "selectorUseAllowed": False,
        "failedGateIds": failed,
        "gateCount": 13,
        "passedGateCount": 13 - len(failed),
        "calibrationMayOpenOnce": False,
        "calibrationStatus": "closed",
        "promotionEligible": False,
    }
    expected_decision = _self_hashed(expected_decision_payload, "decisionSha256")
    if value.get("decision") != expected_decision or value.get("stage1Passed") is not passed:
        raise BeatCellStage1Error("Stage-1 decision is stale.")
    return deepcopy(value)


def _execute_stage1(
    benchmark_report: Mapping[str, Any],
    *,
    benchmark_root: Path,
    audio_lineage_manifest: Mapping[str, Any],
    runtime_manifest: Mapping[str, Any],
    beat_receipt: Mapping[str, Any],
    runtime_root: Path,
    group_manifest: Mapping[str, Any],
    group_root: Path,
    summary_output_root: Path,
    summary_public_root: Path,
    input_bindings: Mapping[str, Any],
    publication: Mapping[str, Any],
) -> dict[str, Any]:
    report = _mapping(benchmark_report, "benchmark report")
    audio_lineage = _mapping(audio_lineage_manifest, "audio lineage")
    runtime = _mapping(runtime_manifest, "runtime manifest")
    receipt = _mapping(beat_receipt, "beat receipt")
    groups = _mapping(group_manifest, "group manifest")

    # This must remain the first phase: no root resolution, nested leaf access,
    # or summary write may precede complete development-envelope rejection.
    _examples._validate_development_envelopes(report, runtime, groups, audio_lineage)
    if (
        receipt.get("split") != DEVELOPMENT_SPLIT
        or receipt.get("developmentOnly") is not True
        or receipt.get("referenceFree") is not True
        or receipt.get("stage1UseAllowed") is not True
        or receipt.get("selectorUseAllowed") is not False
        or receipt.get("playerPlaybackUseAllowed") is not False
    ):
        raise BeatCellStage1Error("Beat receipt changed its sealed development-only envelope.")
    validated_audio_lineage = _examples._validate_audio_lineage_preflight(audio_lineage)
    prediction_identities, prediction_report_contract = _prediction_only_report_projection(report)
    metadata_runtime = validate_runtime_bar_grid_manifest(runtime, artifact_root=None, verify_sources=False)
    runtime_tracks = {
        str(row["trackId"]): dict(row) for row in _sequence(metadata_runtime.get("tracks"), "validated runtime tracks")
    }
    beat_tracks = {
        str(row["trackId"]): dict(row) for row in _sequence(receipt.get("tracks"), "validated beat receipt tracks")
    }
    track_ids = _examples._validate_same_track_set(prediction_identities, runtime_tracks, beat_tracks)
    audio_projection, projection_tracks = _examples._validate_report_audio_lineage_binding(
        prediction_report_contract, validated_audio_lineage, track_ids
    )
    _examples._validate_same_track_set(prediction_identities, projection_tracks)

    _examples._preflight_summary_output_root(
        summary_output_root,
        benchmark_root=benchmark_root,
        runtime_bar_grid_root=runtime_root,
        group_manifest_root=group_root,
    )
    validated_runtime = validate_runtime_bar_grid_manifest(runtime, artifact_root=runtime_root, verify_sources=True)
    if validated_runtime != metadata_runtime:
        raise BeatCellStage1Error("Runtime manifest changed between metadata and strict source validation.")
    analyzer_contract = _mapping(validated_runtime.get("analyzerContract"), "runtime analyzerContract")
    analyzer_contract_sha256 = _sha(analyzer_contract.get("contractSha256"), "runtime analyzer contractSha256")

    # The construction phase receives only the strict prediction identity
    # projection. Full report hashes remain bound separately in inputBindings;
    # report reference fields are not consulted until _score_records.
    def seal_phase() -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return _seal_prediction_records(
            track_ids=track_ids,
            prediction_identities=prediction_identities,
            report_contract=prediction_report_contract,
            runtime_tracks=runtime_tracks,
            beat_tracks=beat_tracks,
            projection_tracks=projection_tracks,
            benchmark_root=benchmark_root,
            summary_output_root=summary_output_root,
            summary_public_root=summary_public_root,
            runtime_analyzer_contract_sha256=analyzer_contract_sha256,
            source_beat_receipt_file_sha256=OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"],
            source_beat_receipt_sha256=OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptSha256"],
        )

    label_phase: dict[str, Any] = {}

    def reference_phase(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        report_tracks, complete_report_contract = _examples._validate_report(report)
        if complete_report_contract != prediction_report_contract:
            raise BeatCellStage1Error("Full label-phase report validation changed the prediction-only contract.")
        group_tracks = _examples._validate_group_manifest(groups)
        _examples._validate_same_track_set(report_tracks, runtime_tracks, beat_tracks, group_tracks, projection_tracks)
        _examples._validate_cross_audio_bindings(
            track_ids, report_tracks, runtime_tracks, group_tracks, projection_tracks
        )
        label_phase["audioGroupAudit"] = _examples._audio_group_audit(track_ids, group_tracks, projection_tracks)
        return _score_records(
            records=records,
            report_tracks=report_tracks,
            group_tracks=group_tracks,
            projection_tracks=projection_tracks,
            group_root=group_root,
        )

    prediction_records, shared_binding, track_rows, reconciliation_rows = _run_ordered_phases(
        seal_phase, reference_phase
    )
    audio_group_audit = _mapping(label_phase.get("audioGroupAudit"), "label-phase audio group audit")
    artifact = _build_artifact(
        input_bindings=input_bindings,
        publication=publication,
        shared_binding=shared_binding,
        source_beat_receipt=receipt,
        track_rows=track_rows,
        projection_tracks=projection_tracks,
        audio_lineage_projection=audio_projection,
        audio_group_audit=audio_group_audit,
        reconciliation_rows=reconciliation_rows,
    )
    return validate_beat_cell_stage1_artifact(artifact)


def _run_ordered_phases(seal_phase: Any, reference_phase: Any) -> tuple[Any, Any, Any, Any]:
    """Make the all-predictions-before-any-reference barrier explicit and testable."""

    records, shared_binding = seal_phase()
    track_rows, reconciliation_rows = reference_phase(records)
    return records, shared_binding, track_rows, reconciliation_rows


def _stage_and_publish_summary_set(
    output_path: Path,
    summary_output_root: Path,
    build: Any,
    precommit_check: Any,
) -> dict[str, Any]:
    """Keep all partial summaries private and publish the complete set atomically."""

    with tempfile.TemporaryDirectory(prefix="chord-beat-cell-stage1-summaries-") as temporary_root:
        staging_root = Path(temporary_root).resolve(strict=True)
        artifact = dict(_mapping(build(staging_root), "staged Stage-1 artifact"))
        precommit_check()
        _publish_json_and_summary_set(output_path, artifact, staging_root, summary_output_root)
        return artifact


def run_beat_cell_stage1_preflight(
    benchmark_path: Path,
    *,
    benchmark_root: Path,
    audio_lineage_path: Path,
    runtime_manifest_path: Path,
    runtime_root: Path,
    beat_receipt_path: Path,
    group_manifest_path: Path,
    group_root: Path,
    summary_output_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Validate exact development sources and publish one new Stage-1 artifact."""

    report, report_raw, report_stat = _sealed_read_json(benchmark_path, "benchmark report")
    audio_lineage, audio_raw, audio_stat = _sealed_read_json(audio_lineage_path, "audio lineage")
    runtime, runtime_raw, runtime_stat = _sealed_read_json(runtime_manifest_path, "runtime manifest")
    beat_receipt, beat_receipt_raw, beat_receipt_stat = _sealed_read_json(beat_receipt_path, "beat receipt")
    groups, groups_raw, groups_stat = _sealed_read_json(group_manifest_path, "group manifest")

    # Reject protected envelopes before resolving any supplied artifact root.
    _examples._validate_development_envelopes(report, runtime, groups, audio_lineage)
    if (
        beat_receipt.get("split") != DEVELOPMENT_SPLIT
        or beat_receipt.get("developmentOnly") is not True
        or beat_receipt.get("referenceFree") is not True
        or beat_receipt.get("stage1UseAllowed") is not True
        or beat_receipt.get("selectorUseAllowed") is not False
        or beat_receipt.get("playerPlaybackUseAllowed") is not False
    ):
        raise BeatCellStage1Error("Beat receipt is not a sealed development-only Stage-1 source.")
    for raw, value, name in (
        (report_raw, report, "benchmark report"),
        (audio_raw, audio_lineage, "audio lineage"),
        (runtime_raw, runtime, "runtime manifest"),
        (beat_receipt_raw, beat_receipt, "beat receipt"),
        (groups_raw, groups, "group manifest"),
    ):
        _canonical_input(raw, value, name)
    _validate_official_source_contract(
        report,
        report_raw,
        runtime,
        runtime_raw,
        beat_receipt,
        beat_receipt_raw,
        groups,
        groups_raw,
        audio_lineage,
        audio_raw,
    )
    _preflight_new_output(output_path)
    summary_public_root = _preflight_new_directory(summary_output_root, "Stage-1 summary output root")
    source_roots = (
        ("benchmark_root", benchmark_root),
        ("runtime_root", runtime_root),
        ("group_root", group_root),
    )
    _require_disjoint_output_path(output_path, source_roots)
    _require_disjoint_summary_root(
        summary_public_root,
        source_roots,
    )
    strict_beat_receipt = validate_runtime_beat_grid_receipt(
        beat_receipt,
        parent_runtime_manifest=runtime,
        parent_runtime_root=runtime_root,
        receipt_path=beat_receipt_path,
        verify_sources=True,
    )
    if strict_beat_receipt != beat_receipt:
        raise BeatCellStage1Error("Strict beat-receipt validation changed the canonical input.")

    input_bindings_payload = {
        "schemaVersion": "chord_runtime_beat_cell_stage1_input_bindings_v1",
        "benchmarkReport": {
            **_top_binding(benchmark_path, report_raw, report, None, "benchmark report"),
            "trackSetSha256": benchmark_track_set_sha256(list(_sequence(report.get("tracks"), "report tracks"))),
            "modelOrEnsembleSha256": _mapping(
                _mapping(report.get("uncertaintyExperiment"), "uncertaintyExperiment").get("binding"),
                "uncertaintyExperiment.binding",
            )["modelOrEnsembleSha256"],
            "predictionSets": _report_prediction_set_bindings(report),
        },
        "benchmarkRoot": _root_binding(benchmark_root, "benchmark root"),
        "audioLineage": {
            **_top_binding(
                audio_lineage_path,
                audio_raw,
                audio_lineage,
                "artifactSha256",
                "audio lineage",
                include_canonical_sha256=False,
            ),
            "projectionSha256": _mapping(
                _mapping(report.get("uncertaintyExperiment"), "uncertaintyExperiment").get("audioLineage"),
                "uncertaintyExperiment.audioLineage",
            )["projectionSha256"],
        },
        "runtimeManifest": {
            **_top_binding(
                runtime_manifest_path,
                runtime_raw,
                runtime,
                "manifestSha256",
                "runtime manifest",
                include_canonical_sha256=False,
            ),
            "trackSetSha256": runtime["trackSetSha256"],
            "analyzerContractSha256": _mapping(runtime["analyzerContract"], "runtime analyzerContract")[
                "contractSha256"
            ],
        },
        "runtimeRoot": _root_binding(runtime_root, "runtime root"),
        "beatReceipt": {
            **_top_binding(beat_receipt_path, beat_receipt_raw, beat_receipt, "receiptSha256", "beat receipt"),
            "trackSetSha256": beat_receipt["trackSetSha256"],
            "receiptTotalsSha256": beat_receipt["receiptTotalsSha256"],
            "beatAnalyzerContractSha256": _mapping(beat_receipt["analyzerContract"], "beat receipt analyzerContract")[
                "contractSha256"
            ],
            "playerReplayContractSha256": _mapping(
                beat_receipt["playerReplayContract"], "beat receipt playerReplayContract"
            )["contractSha256"],
        },
        "groupManifest": {
            **_top_binding(
                group_manifest_path,
                groups_raw,
                groups,
                "manifestSha256",
                "group manifest",
                include_canonical_sha256=False,
            ),
            "trackSetSha256": groups["trackSetSha256"],
        },
        "groupRoot": _root_binding(group_root, "group root"),
        "summaryOutputRoot": {
            "path": str(_absolute(summary_output_root)),
            "pathSha256": canonical_sha256(str(_absolute(summary_output_root))),
        },
    }
    input_bindings = _self_hashed(input_bindings_payload, "bindingsSha256")
    output_text = str(_absolute(output_path))
    publication = {
        "mode": "atomic-new-json-and-summary-directory-set-v1",
        "outputPath": output_text,
        "outputPathSha256": canonical_sha256(output_text),
        "summaryOutputRoot": str(summary_public_root),
        "summaryOutputRootSha256": canonical_sha256(str(summary_public_root)),
    }

    def verify_inputs_at_commit() -> None:
        _verify_input_unchanged(benchmark_path, report_stat, report_raw, "benchmark report")
        _verify_input_unchanged(audio_lineage_path, audio_stat, audio_raw, "audio lineage")
        _verify_input_unchanged(runtime_manifest_path, runtime_stat, runtime_raw, "runtime manifest")
        _verify_input_unchanged(beat_receipt_path, beat_receipt_stat, beat_receipt_raw, "beat receipt")
        _verify_input_unchanged(group_manifest_path, groups_stat, groups_raw, "group manifest")
        if (
            validate_runtime_beat_grid_receipt(
                beat_receipt,
                parent_runtime_manifest=runtime,
                parent_runtime_root=runtime_root,
                receipt_path=beat_receipt_path,
                verify_sources=True,
            )
            != beat_receipt
        ):
            raise BeatCellStage1Error("Beat receipt changed before Stage-1 publication.")

    def build_in_staging(staging_root: Path) -> dict[str, Any]:
        return _execute_stage1(
            report,
            benchmark_root=benchmark_root,
            audio_lineage_manifest=audio_lineage,
            runtime_manifest=runtime,
            beat_receipt=beat_receipt,
            runtime_root=runtime_root,
            group_manifest=groups,
            group_root=group_root,
            summary_output_root=staging_root,
            summary_public_root=summary_public_root,
            input_bindings=input_bindings,
            publication=publication,
        )

    artifact = _stage_and_publish_summary_set(
        output_path,
        summary_public_root,
        build_in_staging,
        verify_inputs_at_commit,
    )
    return deepcopy(artifact)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the sealed development-only exact runtime beat-cell Stage-1 feasibility preflight."
    )
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--audio-lineage", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--beat-receipt", type=Path, required=True)
    parser.add_argument("--group-manifest", type=Path, required=True)
    parser.add_argument("--group-root", type=Path, required=True)
    parser.add_argument("--summary-output-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    artifact = run_beat_cell_stage1_preflight(
        args.benchmark,
        benchmark_root=args.benchmark_root,
        audio_lineage_path=args.audio_lineage,
        runtime_manifest_path=args.runtime_manifest,
        runtime_root=args.runtime_root,
        beat_receipt_path=args.beat_receipt,
        group_manifest_path=args.group_manifest,
        group_root=args.group_root,
        summary_output_root=args.summary_output_root,
        output_path=args.output,
    )
    print(
        json.dumps(
            {
                "artifactSha256": artifact["artifactSha256"],
                "stage1Passed": artifact["stage1Passed"],
                "calibrationMayOpenOnce": False,
                "output": str(_absolute(args.output)),
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
    )
    return 0


__all__ = [
    "CELL_SUMMARY_SCHEMA",
    "CELL_TIMING_SCHEMA",
    "CONSTRUCTION_POLICY",
    "CONSTRUCTION_POLICY_SHA256",
    "BeatCellStage1Error",
    "OFFICIAL_STRUCTURAL_SUPPORT",
    "STAGE1_RUBRIC",
    "STAGE1_RUBRIC_SHA256",
    "STAGE1_SCHEMA",
    "STAGE1_SOURCE_CONTRACT",
    "STAGE1_SOURCE_CONTRACT_SHA256",
    "OFFICIAL_BEAT_RECEIPT_CONTRACT",
    "OFFICIAL_BEAT_RECEIPT_CONTRACT_SHA256",
    "build_stage1_gates",
    "construct_beat_cells",
    "funnel_from_outcomes",
    "main",
    "make_funnel",
    "run_beat_cell_stage1_preflight",
    "score_fixed_cells",
    "summarize_prediction_cells",
    "validate_beat_cell_stage1_artifact",
]
