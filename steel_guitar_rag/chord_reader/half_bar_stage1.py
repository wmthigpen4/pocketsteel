"""Sealed development-only feasibility preflight for fixed half-bar cells.

This stage asks only whether a reference-free, target-player-compatible cell
partition makes enough correct chord support observable to justify a later
selector experiment.  It does not fit a selector, choose a cutoff, inspect a
protected split, or authorize calibration.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import tempfile
from typing import Any

from . import bar_examples as _examples
from . import bar_product as _bar_product
from . import bar_uncertainty as _bar_uncertainty
from .bar_promotion import benchmark_content_set_sha256, benchmark_track_set_sha256, canonical_sha256
from .bar_uncertainty import EXPLICIT_BAR_GRID_SCHEMA
from .runtime_bar_grid import validate_runtime_bar_grid_manifest
from .uncertainty import validate_factorized_uncertainty_contract
from .selector_readiness import (
    REVIEWED_DEVELOPMENT_GROUP_SHAPE,
    _absolute,
    _read_json as _sealed_read_json,
    _reject_symlink_components,
    _validate_reviewed_group_shape,
    _verify_input_unchanged,
)
from .selector_development import (
    _preflight_new_directory,
    _publish_json_and_summary_set,
    _require_disjoint_summary_root,
)


DEVELOPMENT_SPLIT = "development"
STAGE1_SCHEMA = "chord_fixed_half_bar_cell_stage1_preflight_v1"
CELL_SUMMARY_SCHEMA = "chord_fixed_half_bar_prediction_summary_v1"
CELL_TIMING_SCHEMA = "chord_fixed_half_bar_cell_timing_v1"
FUNNEL_SCHEMA = "chord_fixed_half_bar_observability_funnel_v1"
CONSTRUCTION_SCHEMA = "chord_fixed_half_bar_cell_construction_v1"
RUBRIC_SCHEMA = "chord_fixed_half_bar_cell_stage1_rubric_v1"

TARGET_PLAYER_HALF_SPLIT_CONTRACT: dict[str, Any] = {
    "schemaVersion": "chord_target_player_half_split_boundary_contract_v1",
    "sourcePath": "ui/practice-analysis-worker.js",
    "workerSha256": "ea148fd2355d493a94ec4253fadc2cacd198637b19d81bd7e5cf3576cf0407da",
    "eventBoundaryExpression": ("Math.round(bar.startMs + (bar.endMs - bar.startMs) * 0.5)"),
    "canonicalIntegerMillisecondEquivalent": "(startMs+endMs+1)//2",
    "outputTopology": (
        "the current worker emits two half-bar events only when its split condition passes; otherwise it emits one event"
    ),
    "oddMeterDisclaimer": (
        "the worker's evidence split is beat-index based (3/4 uses 2+1 beats), so this contract claims only the "
        "possible output-event boundary and not half-evidence equivalence"
    ),
    "challengerScope": "hypothetical fixed-two-cell structural challenger; no unchanged-current-UI claim",
}
TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256 = canonical_sha256(TARGET_PLAYER_HALF_SPLIT_CONTRACT)

CONSTRUCTION_POLICY: dict[str, Any] = {
    "schemaVersion": "chord_fixed_half_bar_cell_construction_policy_v1",
    "source": "validated deployable reference-free runtime bar starts only",
    "boundaryInputs": "runtime bar start and end after player-canonical integer-millisecond rounding",
    "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
    "cellsPerParentBar": 2,
    "minimumParentDurationMilliseconds": 2,
    "midpointRule": "midpointMs=(startMs+endMs+1)//2",
    "midpointSemantics": "matches JavaScript Math.round((startMs+endMs)/2) for nonnegative integer milliseconds",
    "claimScope": (
        "hypothetical fixed-two-cell challenger midpoint matches one possible target-player half-split event "
        "boundary only; it does not match the current worker's conditional two-half output topology or its "
        "odd-meter half-evidence assignment"
    ),
    "partitionRule": "[startMs,midpointMs) and [midpointMs,endMs); both cells must be nonempty",
    "prefixRule": "preserve the exact parent-grid canonical start and excluded-prefix certification",
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
    "schemaVersion": "chord_fixed_half_bar_cell_scoring_policy_v1",
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
    "schemaVersion": "chord_fixed_half_bar_official_structural_support_v1",
    "derivation": (
        "sum exact runtime-manifest parent barCount after joining each track to its exact group-manifest "
        "dataset and role; fixedCellCount=2*parentBarCount"
    ),
    "performanceExpectation": False,
    "aggregate": {"parentBarCount": 2919, "fixedCellCount": 5838},
    "datasets": [
        {"datasetId": "aam", "parentBarCount": 136, "fixedCellCount": 272},
        {"datasetId": "guitarset", "parentBarCount": 618, "fixedCellCount": 1236},
        {"datasetId": "idmt_guitar", "parentBarCount": 535, "fixedCellCount": 1070},
        {"datasetId": "nrgcp", "parentBarCount": 1009, "fixedCellCount": 2018},
        {"datasetId": "winterreise", "parentBarCount": 621, "fixedCellCount": 1242},
    ],
    "guitarsetRoles": [
        {"guitarsetRole": "comp", "parentBarCount": 253, "fixedCellCount": 506},
        {"guitarsetRole": "solo", "parentBarCount": 365, "fixedCellCount": 730},
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
    "operatingThreshold": None,
    "eligibility": deepcopy(_examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT),
    "eligibilitySha256": _examples.BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    "targetPlayerHalfSplitContract": deepcopy(TARGET_PLAYER_HALF_SPLIT_CONTRACT),
    "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
    "scoringPolicy": deepcopy(SCORING_POLICY),
    "scoringPolicySha256": SCORING_POLICY_SHA256,
    "funnelDefinitions": {
        "T": "all fixed half-bar cells",
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
    "schemaVersion": "chord_fixed_half_bar_stage1_official_source_contract_v1",
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
        "modelOrEnsembleSha256": "da73df511651230a5e8ef827c05aefb117710770ee4f994507354747058baedd",
    },
    "runtimeManifest": {
        "fileSha256": "9c7c171227610a6364f37888f33b3a98d5f8c16d95fe193416e5e4aee18a37f8",
        "manifestSha256": "e717f8b2c44f41fc7cd9557796b701225e82d3e2f5e40b66365a21b406f65ab1",
        "trackSetSha256": "a9ba75338abeb6fad9c6e91adb14f4be74dcdaac6a2241afcc7efddfbe6cd0cd",
        "analyzerContractSha256": "8e1df05daf18371899e06884006403b56a4228109687a6c7ca178f1621fef89e",
    },
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
        "schemaVersion": "chord_fixed_half_bar_prediction_runtime_binding_v1",
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


class HalfBarStage1Error(ValueError):
    """A fixed-cell Stage-1 input or invariant failed closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HalfBarStage1Error(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise HalfBarStage1Error(f"{name} must be an array.")
    return value


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise HalfBarStage1Error(f"{name} must be an integer of at least {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HalfBarStage1Error(f"{name} must be finite.")
    result = float(value)
    if not math.isfinite(result):
        raise HalfBarStage1Error(f"{name} must be finite.")
    return result


def _sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise HalfBarStage1Error(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _player_ms(seconds: Any, name: str) -> int:
    value = _finite(seconds, name)
    if value < 0:
        raise HalfBarStage1Error(f"{name} must be nonnegative.")
    return math.floor(value * 1000 + 0.5)


def _exact_ms(seconds: Any, name: str) -> int:
    value = _finite(seconds, name)
    if value < 0:
        raise HalfBarStage1Error(f"{name} must be nonnegative.")
    try:
        milliseconds = Decimal(str(seconds)) * Decimal(1000)
    except (InvalidOperation, ValueError) as error:
        raise HalfBarStage1Error(f"{name} must be an exact decimal millisecond boundary.") from error
    integral = milliseconds.to_integral_value()
    if milliseconds != integral:
        raise HalfBarStage1Error(f"{name} must already be an exact integer-millisecond boundary.")
    return int(integral)


def _self_hashed(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {**payload, field: canonical_sha256(payload)}


def _validate_self_hash(value: Mapping[str, Any], field: str, name: str) -> None:
    claimed = _sha(value.get(field), f"{name}.{field}")
    if canonical_sha256({key: item for key, item in value.items() if key != field}) != claimed:
        raise HalfBarStage1Error(f"{name} has a stale {field}.")


def _exact_fields(value: Mapping[str, Any], expected: set[str] | frozenset[str], name: str) -> None:
    if set(value) != set(expected):
        raise HalfBarStage1Error(f"{name} has unsupported or missing fields.")


def construct_half_bar_cells(
    timing: Mapping[str, Any],
    *,
    source_timing_file_sha256: str | None = None,
    manifest_timing_sha256: str | None = None,
    manifest_timing_contract_sha256: str | None = None,
    analyzer_timing_source_contract_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Derive exactly two nonempty canonical-ms cells from every parent bar."""

    source = _mapping(timing, "runtime timing")
    if source.get("schemaVersion") != EXPLICIT_BAR_GRID_SCHEMA:
        raise HalfBarStage1Error("Runtime timing must use the explicit bar-grid schema.")
    starts = list(_sequence(source.get("barStartsSeconds"), "runtime timing.barStartsSeconds"))
    if not starts:
        raise HalfBarStage1Error("Runtime timing must contain at least one parent bar.")
    duration_ms = _exact_ms(source.get("durationSeconds"), "runtime timing.durationSeconds")
    if duration_ms < 2:
        raise HalfBarStage1Error("Runtime duration must contain a nonempty two-cell parent bar.")
    parent_starts_ms = [
        _exact_ms(value, f"runtime timing.barStartsSeconds[{index}]") for index, value in enumerate(starts)
    ]
    if any(right <= left for left, right in zip(parent_starts_ms, parent_starts_ms[1:])):
        raise HalfBarStage1Error("Runtime parent boundaries are ambiguous after canonical-millisecond rounding.")
    if parent_starts_ms[-1] >= duration_ms:
        raise HalfBarStage1Error("Runtime final parent start must precede canonical duration.")
    parent_ends_ms = [*parent_starts_ms[1:], duration_ms]

    cells: list[dict[str, Any]] = []
    for parent_index, (start_ms, end_ms) in enumerate(zip(parent_starts_ms, parent_ends_ms, strict=True)):
        if end_ms - start_ms < 2:
            raise HalfBarStage1Error("Every runtime parent bar must be at least 2 canonical milliseconds.")
        midpoint_ms = (start_ms + end_ms + 1) // 2
        if not start_ms < midpoint_ms < end_ms:
            raise HalfBarStage1Error("A half-bar midpoint did not produce two nonempty cells.")
        for half_index, (cell_start, cell_end) in enumerate(((start_ms, midpoint_ms), (midpoint_ms, end_ms))):
            payload = {
                "cellIndex": len(cells),
                "parentBarIndex": parent_index,
                "halfIndex": half_index,
                "startMilliseconds": cell_start,
                "endMilliseconds": cell_end,
                "durationMilliseconds": cell_end - cell_start,
            }
            cells.append(_self_hashed(payload, "rowSha256"))

    if len(cells) != 2 * len(parent_starts_ms):
        raise RuntimeError("Internal half-bar construction did not emit exactly two cells per parent.")
    if sum(int(row["durationMilliseconds"]) for row in cells) != duration_ms - parent_starts_ms[0]:
        raise RuntimeError("Half-bar cell durations do not preserve the parent-grid duration.")
    source_timing_artifact_sha256 = canonical_sha256(source)
    embedded_contract_sha256 = _sha(source.get("contractSha256"), "runtime timing.contractSha256")
    provenance = _mapping(source.get("timingProvenance"), "runtime timing.timingProvenance")
    bar_source = _mapping(provenance.get("barStartsSeconds"), "runtime timing bar-start provenance")
    analyzer_contract_sha256 = _sha(
        analyzer_timing_source_contract_sha256 or bar_source.get("sourceContractSha256"),
        "analyzer timing source contract",
    )
    file_sha256 = _sha(
        source_timing_file_sha256 or source_timing_artifact_sha256,
        "source timing file SHA-256",
    )
    manifest_artifact_sha256 = _sha(
        manifest_timing_sha256 or source_timing_artifact_sha256,
        "manifest timing artifact SHA-256",
    )
    manifest_contract_sha256 = _sha(
        manifest_timing_contract_sha256 or embedded_contract_sha256,
        "manifest timing contract SHA-256",
    )
    if manifest_artifact_sha256 != source_timing_artifact_sha256:
        raise HalfBarStage1Error("Manifest timingSha256 disagrees with the source timing artifact.")
    if manifest_contract_sha256 != embedded_contract_sha256:
        raise HalfBarStage1Error("Manifest timingContractSha256 disagrees with the embedded timing contract.")
    if bar_source.get("sourceContractSha256") != analyzer_contract_sha256:
        raise HalfBarStage1Error("Analyzer timingSourceContractSha256 disagrees with timing provenance.")
    source_prefix = source.get("prefixExcludedSeconds")
    provenance_prefix = bar_source.get("prefixExcludedSeconds")
    if parent_starts_ms[0] > 0:
        if (
            _exact_ms(source_prefix, "runtime timing.prefixExcludedSeconds") != parent_starts_ms[0]
            or _exact_ms(provenance_prefix, "runtime timing provenance prefixExcludedSeconds") != parent_starts_ms[0]
        ):
            raise HalfBarStage1Error("Runtime timing prefix certification does not preserve the parent grid.")
    elif source_prefix is not None or provenance_prefix is not None:
        if (
            _exact_ms(source_prefix, "runtime timing.prefixExcludedSeconds") != 0
            or _exact_ms(provenance_prefix, "runtime timing provenance prefixExcludedSeconds") != 0
        ):
            raise HalfBarStage1Error("A zero-start parent grid may certify only a zero prefix.")

    construction_payload: dict[str, Any] = {
        "schemaVersion": CONSTRUCTION_SCHEMA,
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
        "timingFileSha256": file_sha256,
        "timingSha256": source_timing_artifact_sha256,
        "timingContractSha256": embedded_contract_sha256,
        "timingSourceContractSha256": analyzer_contract_sha256,
        "parentBarCount": len(parent_starts_ms),
        "cellCount": len(cells),
        "prefixMilliseconds": parent_starts_ms[0],
        "canonicalDurationMilliseconds": duration_ms,
        "coveredDurationMilliseconds": duration_ms - parent_starts_ms[0],
        "parentStartsMilliseconds": parent_starts_ms,
        "parentEndsMilliseconds": parent_ends_ms,
        "cells": cells,
        "cellSetSha256": canonical_sha256(cells),
        "identities": {
            "exactTwoCellsPerParent": True,
            "allCellsNonempty": True,
            "parentBoundariesPreserved": True,
            "prefixPreserved": True,
            "cellDurationSumEqualsCoveredParentDuration": True,
        },
    }
    derived_payload: dict[str, Any] = {
        "schemaVersion": CELL_TIMING_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "runtimeAnalyzerOutput": False,
        "timingFileSha256": file_sha256,
        "timingSha256": source_timing_artifact_sha256,
        "timingContractSha256": embedded_contract_sha256,
        "timingSourceContractSha256": analyzer_contract_sha256,
        "constructionPolicySha256": CONSTRUCTION_POLICY_SHA256,
        "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
        "canonicalDurationMilliseconds": duration_ms,
        "prefixMilliseconds": parent_starts_ms[0],
        "cellStartsMilliseconds": [int(row["startMilliseconds"]) for row in cells],
        "provenance": {
            "sourceClass": "derived-from-attested-runtime-parent-grid",
            "boundaryInputs": "parent start/end canonical milliseconds only",
            "midpointRule": CONSTRUCTION_POLICY["midpointRule"],
            "referenceFree": True,
            "claimScope": CONSTRUCTION_POLICY["claimScope"],
            "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
        },
    }
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
        or derived_timing.get("targetPlayerHalfSplitContractSha256") != TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256
        or derived_timing.get("contractSha256") != construction.get("derivedCellTimingContractSha256")
    ):
        raise HalfBarStage1Error("Derived cell timing does not bind the frozen construction.")
    duration = _finite(value.get("durationSeconds"), "prediction.durationSeconds")
    if duration <= 0:
        raise HalfBarStage1Error("Prediction duration must be positive.")
    segments = _bar_uncertainty._prediction_segments(value, duration)
    cells: list[dict[str, Any]] = []
    for index, raw_cell in enumerate(_sequence(construction.get("cells"), "construction.cells")):
        cell = _mapping(raw_cell, f"construction.cells[{index}]")
        start_ms = _integer(cell.get("startMilliseconds"), "cell.startMilliseconds")
        end_ms = _integer(cell.get("endMilliseconds"), "cell.endMilliseconds", minimum=1)
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
            raise HalfBarStage1Error(f"{name} does not satisfy the exact T/U/R/N/E/C/I partitions.")
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
        raise HalfBarStage1Error("Every prediction-identity row must be development-only.")
    if not isinstance(projection["id"], str) or not projection["id"]:
        raise HalfBarStage1Error("Prediction identity requires a nonempty id.")
    if not isinstance(projection["predictionFile"], str) or not projection["predictionFile"]:
        raise HalfBarStage1Error("Prediction identity requires predictionFile.")
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
            raise HalfBarStage1Error("Prediction-only report projection repeats a track id.")
        identities[track_id] = identity
    if len(identities) != STAGE1_SOURCE_CONTRACT["trackCount"]:
        raise HalfBarStage1Error("Prediction-only report projection must contain the official 246 tracks.")

    binding = dict(_mapping(experiment.get("binding"), "uncertaintyExperiment.binding"))
    if canonical_sha256(binding) != _sha(experiment.get("bindingSha256"), "uncertaintyExperiment.bindingSha256"):
        raise HalfBarStage1Error("Prediction-only report binding hash is stale.")
    members = list(_sequence(experiment.get("memberBinding"), "uncertaintyExperiment.memberBinding"))
    member_order_sha256 = _sha(binding.get("memberOrderSha256"), "report memberOrderSha256")
    if canonical_sha256(members) != member_order_sha256 or canonical_sha256(members) != _sha(
        experiment.get("memberBindingSha256"), "uncertaintyExperiment.memberBindingSha256"
    ):
        raise HalfBarStage1Error("Prediction-only report member binding is stale.")
    audio_lineage = dict(_mapping(experiment.get("audioLineage"), "uncertaintyExperiment.audioLineage"))
    if canonical_sha256({key: item for key, item in audio_lineage.items() if key != "bindingSha256"}) != _sha(
        audio_lineage.get("bindingSha256"), "uncertaintyExperiment.audioLineage.bindingSha256"
    ):
        raise HalfBarStage1Error("Prediction-only report audio-lineage binding is stale.")
    projection = dict(_mapping(audio_lineage.get("projection"), "uncertaintyExperiment.audioLineage.projection"))
    projection_sha256 = _sha(
        audio_lineage.get("projectionSha256"), "uncertaintyExperiment.audioLineage.projectionSha256"
    )
    if projection.get("projectionSha256") != projection_sha256:
        raise HalfBarStage1Error("Prediction-only report audio-lineage projection binding is stale.")
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
        raise HalfBarStage1Error("Every GuitarSet track must declare a comp or solo role.")
    lowered = raw_role.strip().lower()
    tokens = lowered.replace("/", ":").split(":")
    matches = [role for role in ("comp", "solo") if lowered == role or role in tokens]
    if len(matches) != 1:
        raise HalfBarStage1Error("Every GuitarSet role must identify exactly one of comp or solo.")
    return matches[0]


def _structural_support(
    rows: Sequence[tuple[str, str, str | None, int]],
) -> dict[str, Any]:
    """Derive fixed-cell structural denominators without opening labels or predictions."""

    dataset_ids = list(_examples.LABEL_DETERMINACY_DATASET_IDS)
    seen: set[str] = set()
    dataset_parent_counts = {dataset_id: 0 for dataset_id in dataset_ids}
    role_parent_counts = {role: 0 for role in ("comp", "solo")}
    aggregate_parent_count = 0
    for track_id, dataset_id, guitarset_role, raw_parent_count in rows:
        if not isinstance(track_id, str) or not track_id or track_id in seen:
            raise HalfBarStage1Error("Structural-support track identities must be nonempty and unique.")
        seen.add(track_id)
        if dataset_id not in dataset_parent_counts:
            raise HalfBarStage1Error("Structural support must use the exact five certification datasets.")
        parent_count = _integer(raw_parent_count, f"structural support {track_id!r}.parentBarCount", minimum=1)
        if dataset_id == "guitarset":
            if guitarset_role not in role_parent_counts:
                raise HalfBarStage1Error("Every GuitarSet structural-support row requires comp or solo.")
            role_parent_counts[str(guitarset_role)] += parent_count
        elif guitarset_role is not None:
            raise HalfBarStage1Error("Only GuitarSet structural-support rows may declare a GuitarSet role.")
        dataset_parent_counts[dataset_id] += parent_count
        aggregate_parent_count += parent_count

    payload = {
        "schemaVersion": _OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD["schemaVersion"],
        "derivation": _OFFICIAL_STRUCTURAL_SUPPORT_PAYLOAD["derivation"],
        "performanceExpectation": False,
        "aggregate": {
            "parentBarCount": aggregate_parent_count,
            "fixedCellCount": 2 * aggregate_parent_count,
        },
        "datasets": [
            {
                "datasetId": dataset_id,
                "parentBarCount": dataset_parent_counts[dataset_id],
                "fixedCellCount": 2 * dataset_parent_counts[dataset_id],
            }
            for dataset_id in dataset_ids
        ],
        "guitarsetRoles": [
            {
                "guitarsetRole": role,
                "parentBarCount": role_parent_counts[role],
                "fixedCellCount": 2 * role_parent_counts[role],
            }
            for role in ("comp", "solo")
        ],
    }
    return _self_hashed(payload, "supportSha256")


def _structural_support_from_sources(
    runtime_tracks: Mapping[str, Mapping[str, Any]],
    group_tracks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if set(runtime_tracks) != set(group_tracks):
        raise HalfBarStage1Error("Runtime and group manifests disagree on structural-support tracks.")
    rows = []
    for track_id in sorted(runtime_tracks):
        group = _mapping(group_tracks[track_id], f"group track {track_id!r}")
        dataset_id = str(group.get("datasetId"))
        rows.append(
            (
                track_id,
                dataset_id,
                _guitarset_role(dataset_id, group.get("role")),
                _integer(runtime_tracks[track_id].get("barCount"), f"runtime track {track_id!r}.barCount", minimum=1),
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
                _integer(row.get("parentBarCount"), "track.parentBarCount", minimum=1),
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
        raise HalfBarStage1Error("Official GuitarSet disclosure support must be exactly 18 comp and 18 solo tracks.")


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
        raise HalfBarStage1Error("Track role/group/reference metadata is not exactly source-bound.")
    return source_group


def _summary_filename(track_id: str, sidecar_sha256: str) -> str:
    return f"{canonical_sha256({'trackId': track_id})}-{_sha(sidecar_sha256, 'sidecarSha256')}.json"


def _validate_prediction_summary(summary: Mapping[str, Any], track_id: str) -> None:
    _validate_self_hash(summary, "summarySha256", f"prediction summary {track_id!r}")
    if summary.get("schemaVersion") != CELL_SUMMARY_SCHEMA:
        raise HalfBarStage1Error("Prediction cell summary uses an unsupported schemaVersion.")
    if (
        summary.get("trackId") != track_id
        or summary.get("referenceFree") is not True
        or summary.get("runtimeAnalyzerOutput") is not False
        or summary.get("promotionEligible") is not False
        or summary.get("scoringPolicySha256") != SCORING_POLICY_SHA256
    ):
        raise HalfBarStage1Error("Prediction cell summary is not a sealed reference-free development summary.")
    cells = list(_sequence(summary.get("cells"), "prediction cell summary.cells"))
    if canonical_sha256(cells) != summary.get("cellSetSha256"):
        raise HalfBarStage1Error("Prediction cell summary set hash is stale.")
    for index, raw in enumerate(cells):
        row = _mapping(raw, f"prediction cell summary.cells[{index}]")
        _exact_fields(
            row,
            {
                "cellIndex",
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
        if row.get("cellIndex") != index:
            raise HalfBarStage1Error("Prediction cell summary indices are stale.")
        start = _integer(row.get("startMilliseconds"), "prediction cell start")
        end = _integer(row.get("endMilliseconds"), "prediction cell end", minimum=1)
        if (
            end - start != row.get("durationMilliseconds")
            or row.get("interval") != "[startMilliseconds/1000,endMilliseconds/1000)"
        ):
            raise HalfBarStage1Error("Prediction cell summary duration is stale.")
        for field in ("predictionCoverage", "predictionDominance"):
            number = _finite(row.get(field), f"prediction cell summary.{field}")
            if not 0 <= number <= 1:
                raise HalfBarStage1Error("Prediction cell summary fractions must be in [0,1].")
        interval = (end - start) / 1000
        covered = _finite(row.get("predictionCoveredDurationSeconds"), "prediction covered duration")
        product_duration = _finite(row.get("predictionProductDurationSeconds"), "prediction product duration")
        if not 0 <= product_duration <= covered <= interval:
            raise HalfBarStage1Error("Prediction cell summary overlap durations are invalid.")
        if row.get("predictionCoverage") != min(1.0, max(0.0, covered / interval)) or row.get(
            "predictionDominance"
        ) != (min(1.0, max(0.0, product_duration / covered)) if covered > 1e-9 else 0.0):
            raise HalfBarStage1Error("Prediction cell summary overlap ratios are stale.")
        product = row.get("predictionProduct")
        if product is None:
            if covered != 0.0 or product_duration != 0.0:
                raise HalfBarStage1Error("A null prediction product cannot have positive overlap evidence.")
        elif (
            not isinstance(product, str)
            or not product
            or covered <= 0
            or product_duration <= 0
            or _bar_product._segment_product({"productLabel": product}) != product
        ):
            raise HalfBarStage1Error("A prediction product must be canonical and have positive overlap evidence.")


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
        raise HalfBarStage1Error(f"Prediction uncertainty hash mismatch for {track_id!r}.")
    core_payload = {
        key: item
        for key, item in value.items()
        if key not in {"uncertainty", "predictionCoreSha256", "uncertaintySha256"}
    }
    claimed_core = _sha(value.get("predictionCoreSha256"), "prediction predictionCoreSha256")
    if canonical_sha256(core_payload) != claimed_core or uncertainty.get("predictionCoreSha256") != claimed_core:
        raise HalfBarStage1Error(f"Prediction core hash mismatch for {track_id!r}.")
    if dict(_mapping(uncertainty.get("binding"), "prediction uncertainty binding")) != report_contract["binding"]:
        raise HalfBarStage1Error(f"Prediction binding mismatch for {track_id!r}.")
    if list(_sequence(uncertainty.get("members"), "prediction uncertainty members")) != report_contract["members"]:
        raise HalfBarStage1Error(f"Prediction member binding mismatch for {track_id!r}.")

    evidence = _bar_uncertainty._validate_prediction_uncertainty(value)
    duration = _finite(value.get("durationSeconds"), "prediction.durationSeconds")
    segments = _bar_uncertainty._prediction_segments(value, duration)
    _bar_uncertainty._validate_selected_class_alignment(evidence, segments)
    segment_identity = [{"start": row["start"], "end": row["end"], "product": row["product"]} for row in segments]
    audit_payload = {
        "schemaVersion": "chord_fixed_half_bar_prediction_validation_audit_v1",
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
        "schemaVersion": "chord_fixed_half_bar_prediction_runtime_binding_v1",
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
        raise HalfBarStage1Error("Cell exclusion reasons do not reconcile with U and N.")
    return _self_hashed(payload, "auditSha256")


def funnel_from_outcomes(outcomes: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reduce U/N/C/I terminal cell outcomes into both exact funnel measures."""

    counts = _empty_measure()
    durations = _empty_measure()
    for index, raw in enumerate(outcomes):
        row = _mapping(raw, f"outcomes[{index}]")
        classification = row.get("classification")
        if classification not in {"U", "N", "C", "I"}:
            raise HalfBarStage1Error("Every cell outcome must terminate in exactly U, N, C, or I.")
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
        raise HalfBarStage1Error(f"{name} must be an existing directory.") from error
    if not resolved.is_dir():
        raise HalfBarStage1Error(f"{name} must be an existing directory.")
    rendered = str(resolved)
    return {"path": rendered, "pathSha256": canonical_sha256(rendered)}


def _top_binding(
    path: Path,
    raw: bytes,
    value: Mapping[str, Any],
    claimed_field: str | None,
    name: str,
) -> dict[str, Any]:
    claimed: str | None = None
    if claimed_field is not None:
        _validate_self_hash(value, claimed_field, name)
        claimed = str(value[claimed_field])
    absolute = str(_absolute(path))
    return {
        "path": absolute,
        "pathSha256": canonical_sha256(absolute),
        "fileSha256": hashlib.sha256(raw).hexdigest(),
        "canonicalSha256": canonical_sha256(value),
        "claimedArtifactSha256": claimed,
    }


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
        raise HalfBarStage1Error("Benchmark prediction artifact/core/uncertainty set bindings are stale.")
    if len(set(values.values())) != 3:
        raise HalfBarStage1Error("Prediction artifact, core, and uncertainty set hashes must remain distinct.")
    return _self_hashed({**values, "allThreeDistinct": True}, "bindingsSha256")


def _validate_official_source_contract(
    report: Mapping[str, Any],
    report_raw: bytes,
    runtime: Mapping[str, Any],
    runtime_raw: bytes,
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
        raise HalfBarStage1Error("Benchmark report is not the exact official 246-track Stage-1 candidate.")

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
        raise HalfBarStage1Error("Runtime manifest is not the exact official Stage-1 candidate.")

    group_contract = _mapping(contract["groupManifest"], "source contract groupManifest")
    group_tracks = _examples._validate_group_manifest(groups)
    if (
        hashlib.sha256(groups_raw).hexdigest() != group_contract["fileSha256"]
        or groups.get("manifestSha256") != group_contract["manifestSha256"]
        or groups.get("trackSetSha256") != group_contract["trackSetSha256"]
    ):
        raise HalfBarStage1Error("Group manifest is not the exact official Stage-1 candidate.")
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
        raise HalfBarStage1Error("Audio lineage is not the exact official Stage-1 candidate.")

    id_sets = (
        {str(_mapping(row, "report track").get("id")) for row in report_tracks},
        {str(_mapping(row, "runtime track").get("trackId")) for row in runtime_track_rows},
        set(group_tracks),
        {str(_mapping(row, "audio-lineage track").get("trackId")) for row in audio_tracks},
    )
    if any(values != id_sets[0] for values in id_sets[1:]) or len(id_sets[0]) != contract["trackCount"]:
        raise HalfBarStage1Error("Official Stage-1 top-level track identities disagree.")
    runtime_tracks = {
        str(_mapping(row, "runtime track").get("trackId")): _mapping(row, "runtime track") for row in runtime_track_rows
    }
    structural_support = _structural_support_from_sources(runtime_tracks, group_tracks)
    if structural_support != contract.get("structuralSupport") or structural_support != OFFICIAL_STRUCTURAL_SUPPORT:
        raise HalfBarStage1Error("Official runtime/group structural denominators are not exact.")
    reviewed = _mapping(contract["reviewedDatasetShape"], "source contract reviewedDatasetShape")
    if reviewed.get("shape") != REVIEWED_DEVELOPMENT_GROUP_SHAPE or reviewed.get("shapeSha256") != canonical_sha256(
        REVIEWED_DEVELOPMENT_GROUP_SHAPE
    ):
        raise RuntimeError("Embedded Stage-1 reviewed dataset shape drifted.")


def _canonical_input(raw: bytes, value: Mapping[str, Any], name: str) -> None:
    rendered = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if rendered != raw:
        raise HalfBarStage1Error(f"{name} must use the exact canonical indented JSON rendering.")


def _target_player_worker_binding(
    runtime_manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], Path, bytes, os.stat_result]:
    """Bind the current target worker and its transitively sealed runtime receipt."""

    analyzer = _mapping(runtime_manifest.get("analyzerContract"), "runtime analyzerContract")
    implementation = _mapping(analyzer.get("implementation"), "runtime analyzer implementation")
    expected_worker_sha256 = TARGET_PLAYER_HALF_SPLIT_CONTRACT["workerSha256"]
    if implementation.get("workerSha256") != expected_worker_sha256:
        raise HalfBarStage1Error("Runtime analyzer does not bind the frozen target-player worker.")

    source_path = _absolute(Path(__file__).resolve().parents[2] / TARGET_PLAYER_HALF_SPLIT_CONTRACT["sourcePath"])
    _reject_symlink_components(source_path, "target-player worker source")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(source_path, flags)
    except OSError as error:
        raise HalfBarStage1Error("Target-player worker source must be an existing non-symlink file.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise HalfBarStage1Error("Target-player worker source must be a regular file.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(descriptor)
    try:
        visible = os.stat(source_path, follow_symlinks=False)
    except OSError as error:
        raise HalfBarStage1Error("Target-player worker source changed while it was read.") from error
    if (visible.st_dev, visible.st_ino) != (opened.st_dev, opened.st_ino):
        raise HalfBarStage1Error("Target-player worker source changed while it was read.")
    actual_worker_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_worker_sha256 != expected_worker_sha256:
        raise HalfBarStage1Error("Current target-player worker drifted from the frozen half-split contract.")
    rendered_path = str(source_path)
    payload = {
        "schemaVersion": "chord_target_player_half_split_source_binding_v1",
        "path": rendered_path,
        "pathSha256": canonical_sha256(rendered_path),
        "fileSha256": actual_worker_sha256,
        "runtimeAnalyzerContractSha256": analyzer.get("contractSha256"),
        "runtimeManifestWorkerSha256": implementation.get("workerSha256"),
        "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
    }
    return _self_hashed(payload, "bindingSha256"), source_path, raw, opened


def _preflight_new_output(path: Path) -> None:
    destination = _absolute(path)
    if destination.suffix.lower() != ".json":
        raise HalfBarStage1Error("Stage-1 output must use a new .json path.")
    if destination.exists() or destination.is_symlink():
        raise HalfBarStage1Error("Stage-1 output must use a new path.")


def _seal_prediction_records(
    *,
    track_ids: Sequence[str],
    prediction_identities: Mapping[str, Mapping[str, Any]],
    report_contract: Mapping[str, Any],
    runtime_tracks: Mapping[str, Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
    benchmark_root: Path,
    runtime_root: Path,
    summary_output_root: Path,
    summary_public_root: Path,
    runtime_analyzer_contract_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Finish and materialize every prediction-only record before references."""

    records: list[dict[str, Any]] = []
    shared_binding: dict[str, Any] | None = None
    for track_id in track_ids:
        identity = dict(_mapping(prediction_identities[track_id], f"prediction identity {track_id!r}"))
        _validate_self_hash(identity, "predictionIdentitySha256", f"prediction identity {track_id!r}")
        runtime_track = runtime_tracks[track_id]
        prediction_path = _examples._artifact_path(
            benchmark_root, identity["predictionFile"], f"prediction {track_id!r}"
        )
        prediction, prediction_raw = _examples._read_json(prediction_path, f"prediction {track_id!r}")
        if hashlib.sha256(prediction_raw).hexdigest() != identity["predictionSha256"]:
            raise HalfBarStage1Error(f"Prediction file hash mismatch for {track_id!r}.")
        if prediction.get("id") != track_id:
            raise HalfBarStage1Error(f"Prediction id mismatch for {track_id!r}.")
        for field in ("predictionCoreSha256", "uncertaintySha256"):
            if prediction.get(field) != identity[field]:
                raise HalfBarStage1Error(f"Prediction {field} mismatch for {track_id!r}.")
        prediction_validation, prediction_binding = _validate_prediction_for_cells(
            prediction, track_id, report_contract
        )

        timing_path = _examples._artifact_path(
            runtime_root, runtime_track["timingFile"], f"runtime timing {track_id!r}"
        )
        timing, timing_raw = _examples._read_json(timing_path, f"runtime timing {track_id!r}")
        if canonical_sha256(timing) != runtime_track["timingSha256"]:
            raise HalfBarStage1Error(f"Runtime timing hash mismatch for {track_id!r}.")
        if timing.get("contractSha256") != runtime_track["timingContractSha256"]:
            raise HalfBarStage1Error(f"Runtime timing contract mismatch for {track_id!r}.")
        if runtime_track.get("barCount") != len(_sequence(timing.get("barStartsSeconds"), "runtime starts")):
            raise HalfBarStage1Error(f"Runtime parent bar count mismatch for {track_id!r}.")
        _examples._require_runtime_selector_timing(timing, runtime_analyzer_contract_sha256)
        construction, derived_cell_timing = construct_half_bar_cells(
            timing,
            source_timing_file_sha256=hashlib.sha256(timing_raw).hexdigest(),
            manifest_timing_sha256=runtime_track["timingSha256"],
            manifest_timing_contract_sha256=runtime_track["timingContractSha256"],
            analyzer_timing_source_contract_sha256=runtime_track["timingSourceContractSha256"],
        )
        prediction_canonical_ms = _player_ms(
            prediction.get("durationSeconds"), f"prediction {track_id!r}.durationSeconds"
        )
        if not (
            prediction_canonical_ms
            == construction["canonicalDurationMilliseconds"]
            == identity["canonicalDurationMilliseconds"]
        ):
            raise HalfBarStage1Error(
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
            raise HalfBarStage1Error(f"Prediction summary cell count mismatch for {track_id!r}.")
        binding = {
            **prediction_binding,
            "timingSourceContractSha256": runtime_track["timingSourceContractSha256"],
        }
        if binding["timingSourceContractSha256"] != runtime_analyzer_contract_sha256:
            raise HalfBarStage1Error(f"Runtime timing source contract mismatch for {track_id!r}.")
        if shared_binding is None:
            shared_binding = binding
        elif shared_binding != binding:
            raise HalfBarStage1Error("All cell summaries must share one exact prediction/runtime binding.")

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
            raise HalfBarStage1Error(f"Materialized prediction-only cell summary changed for {track_id!r}.")
        records.append(
            {
                "trackId": track_id,
                "prediction": prediction,
                "derivedCellTiming": derived_cell_timing,
                "summary": summary,
                "construction": construction,
                "summaryPath": str(_absolute(public_summary_path)),
                "summaryArtifactSha256": sidecar["artifactSha256"],
                "predictionIdentitySha256": identity["predictionIdentitySha256"],
            }
        )
    if shared_binding is None:
        raise HalfBarStage1Error("At least one prediction record is required.")
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
        raise HalfBarStage1Error("Prediction duration and canonical runtime duration do not reconcile.")
    raw_segments = list(_sequence(reference.get("segments"), "reference.segments"))
    previous_end: float | None = None
    endpoints: list[tuple[float, float]] = []
    for index, raw in enumerate(raw_segments):
        segment = _mapping(raw, f"reference.segments[{index}]")
        start = _finite(segment.get("start"), f"reference.segments[{index}].start")
        end = _finite(segment.get("end"), f"reference.segments[{index}].end")
        if start < 0 or end <= start or (previous_end is not None and start < previous_end):
            raise HalfBarStage1Error("Reference segments must be ordered, nonoverlapping, and positive.")
        previous_end = end
        endpoints.append((start, end))
    segments = _bar_product._segments(raw_segments, prediction=False)
    runtime_duration = runtime_ms / 1000
    declared = reference.get("durationSeconds")
    if declared is not None:
        reference_duration = _finite(declared, "reference.durationSeconds")
        if reference_duration not in {prediction_duration, runtime_duration}:
            raise HalfBarStage1Error(
                "Reference duration must exactly equal prediction duration or canonical runtime duration."
            )
        if endpoints and max(end for _start, end in endpoints) > reference_duration:
            raise HalfBarStage1Error("Reference segments exceed the declared reference duration.")
    reconciliation: dict[str, Any] | None = None
    if declared is None and endpoints:
        original_end = max(end for _start, end in endpoints)
        if original_end > prediction_duration:
            terminal_index = len(endpoints) - 1
            overhang = [index for index, (_start, end) in enumerate(endpoints) if end > prediction_duration]
            maximum = [index for index, (_start, end) in enumerate(endpoints) if end == original_end]
            if overhang != [terminal_index] or maximum != [terminal_index]:
                raise HalfBarStage1Error("Only one unique terminal reference endpoint may exceed prediction duration.")
            if endpoints[terminal_index][0] >= prediction_duration:
                raise HalfBarStage1Error("Reconciled terminal reference evidence must begin before prediction end.")
            if _player_ms(original_end, "terminal reference end") != runtime_ms:
                raise HalfBarStage1Error("Terminal reference endpoint is outside the prediction canonical millisecond.")
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
        raise HalfBarStage1Error("Determinate reference product must be nonempty.")
    if not isinstance(prediction_product, str) or not prediction_product:
        raise HalfBarStage1Error("Eligible prediction product must be nonempty.")
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
        raise HalfBarStage1Error("Fixed-cell construction and prediction summary counts disagree.")
    outcomes: list[dict[str, Any]] = []
    for raw_cell, raw_summary in zip(cell_rows, summary_cells, strict=True):
        cell = _mapping(raw_cell, "constructed cell")
        summary = _mapping(raw_summary, "prediction summary cell")
        cell_index = _integer(cell.get("cellIndex"), "cell.cellIndex")
        if (
            summary.get("cellIndex") != cell_index
            or summary.get("startMilliseconds") != cell.get("startMilliseconds")
            or summary.get("endMilliseconds") != cell.get("endMilliseconds")
            or summary.get("durationMilliseconds") != cell.get("durationMilliseconds")
        ):
            raise HalfBarStage1Error("Constructed and summarized cell identity disagrees.")
        duration_ms = _integer(cell.get("durationMilliseconds"), "cell.durationMilliseconds", minimum=1)
        start = int(cell["startMilliseconds"]) / 1000
        end = int(cell["endMilliseconds"]) / 1000
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
            "parentBarIndex": cell["parentBarIndex"],
            "halfIndex": cell["halfIndex"],
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
            raise HalfBarStage1Error(f"Reference file hash mismatch for {track_id!r}.")
        if reference_sha256 != report_tracks[track_id]["referenceSha256"]:
            raise HalfBarStage1Error(f"Reference/report hash mismatch for {track_id!r}.")

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
                raise HalfBarStage1Error("Reference endpoint reconciliation disagrees with audio lineage.")
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
            "predictionIdentitySha256": record["predictionIdentitySha256"],
            "timingFileSha256": construction["timingFileSha256"],
            "timingSha256": construction["timingSha256"],
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
            "parentBarCount": construction["parentBarCount"],
            "cellCount": construction["cellCount"],
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
    track_rows: Sequence[Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
    audio_lineage_projection: Mapping[str, Any],
    audio_group_audit: Mapping[str, Any],
    reconciliation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    observed_dataset_ids = {str(row["datasetId"]) for row in track_rows}
    required_dataset_ids = set(_examples.LABEL_DETERMINACY_DATASET_IDS)
    if observed_dataset_ids != required_dataset_ids:
        raise HalfBarStage1Error("Stage-1 requires support from the exact five certification datasets.")
    guitar_roles = {str(row["guitarsetRole"]) for row in track_rows if row.get("datasetId") == "guitarset"}
    if guitar_roles != {"comp", "solo"}:
        raise HalfBarStage1Error("Stage-1 requires supported GuitarSet comp and solo disclosures.")
    _require_official_guitar_role_track_support(track_rows)
    structural_support = _structural_support_from_track_rows(track_rows)
    if structural_support != OFFICIAL_STRUCTURAL_SUPPORT:
        raise HalfBarStage1Error("Stage-1 track rows do not preserve the official structural denominators.")
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
        "operatingThreshold": None,
        "purpose": "fixed-cell structural observability and oracle correct-support feasibility only",
        "publication": dict(publication),
        "inputBindings": dict(input_bindings),
        "inputBindingsSha256": canonical_sha256(input_bindings),
        "sourceContract": deepcopy(STAGE1_SOURCE_CONTRACT),
        "sourceContractSha256": STAGE1_SOURCE_CONTRACT_SHA256,
        "targetPlayerHalfSplitContract": deepcopy(TARGET_PLAYER_HALF_SPLIT_CONTRACT),
        "targetPlayerHalfSplitContractSha256": TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256,
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


def _validate_construction(construction: Mapping[str, Any], name: str) -> None:
    _exact_fields(
        construction,
        {
            "schemaVersion",
            "constructionPolicySha256",
            "targetPlayerHalfSplitContractSha256",
            "timingFileSha256",
            "timingSha256",
            "timingContractSha256",
            "timingSourceContractSha256",
            "parentBarCount",
            "cellCount",
            "prefixMilliseconds",
            "canonicalDurationMilliseconds",
            "coveredDurationMilliseconds",
            "parentStartsMilliseconds",
            "parentEndsMilliseconds",
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
        raise HalfBarStage1Error(f"{name} uses an unsupported schemaVersion.")
    if construction.get("constructionPolicySha256") != CONSTRUCTION_POLICY_SHA256:
        raise HalfBarStage1Error(f"{name} changed the frozen construction policy.")
    if construction.get("targetPlayerHalfSplitContractSha256") != TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256:
        raise HalfBarStage1Error(f"{name} changed the target-player half-split contract.")
    for field in (
        "timingFileSha256",
        "timingSha256",
        "timingContractSha256",
        "timingSourceContractSha256",
        "derivedCellTimingContractSha256",
    ):
        _sha(construction.get(field), f"{name}.{field}")
    cells = list(_sequence(construction.get("cells"), f"{name}.cells"))
    if canonical_sha256(cells) != construction.get("cellSetSha256"):
        raise HalfBarStage1Error(f"{name}.cellSetSha256 is stale.")
    parent_count = _integer(construction.get("parentBarCount"), f"{name}.parentBarCount", minimum=1)
    if len(cells) != 2 * parent_count or construction.get("cellCount") != len(cells):
        raise HalfBarStage1Error(f"{name} does not contain exactly two cells per parent.")
    starts = list(_sequence(construction.get("parentStartsMilliseconds"), f"{name}.parentStartsMilliseconds"))
    ends = list(_sequence(construction.get("parentEndsMilliseconds"), f"{name}.parentEndsMilliseconds"))
    if len(starts) != parent_count or len(ends) != parent_count:
        raise HalfBarStage1Error(f"{name} parent boundary counts are stale.")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in [*starts, *ends]):
        raise HalfBarStage1Error(f"{name} parent boundaries must be exact integer milliseconds.")
    if any(int(ends[index]) != int(starts[index + 1]) for index in range(parent_count - 1)):
        raise HalfBarStage1Error(f"{name} parent bars do not preserve a contiguous grid.")
    if (
        starts[0] != construction.get("prefixMilliseconds")
        or ends[-1] != construction.get("canonicalDurationMilliseconds")
        or int(ends[-1]) - int(starts[0]) != construction.get("coveredDurationMilliseconds")
    ):
        raise HalfBarStage1Error(f"{name} prefix/duration identities are stale.")
    duration_sum = 0
    for index, raw in enumerate(cells):
        cell = _mapping(raw, f"{name}.cells[{index}]")
        _exact_fields(
            cell,
            {
                "cellIndex",
                "parentBarIndex",
                "halfIndex",
                "startMilliseconds",
                "endMilliseconds",
                "durationMilliseconds",
                "rowSha256",
            },
            f"{name}.cells[{index}]",
        )
        _validate_self_hash(cell, "rowSha256", f"{name}.cells[{index}]")
        if (
            cell.get("cellIndex") != index
            or cell.get("parentBarIndex") != index // 2
            or cell.get("halfIndex") != index % 2
        ):
            raise HalfBarStage1Error(f"{name} cell identity is stale.")
        start = _integer(cell.get("startMilliseconds"), "cell.startMilliseconds")
        end = _integer(cell.get("endMilliseconds"), "cell.endMilliseconds", minimum=1)
        duration = _integer(cell.get("durationMilliseconds"), "cell.durationMilliseconds", minimum=1)
        if end - start != duration:
            raise HalfBarStage1Error(f"{name} cell duration is stale.")
        parent_index = index // 2
        midpoint = (int(starts[parent_index]) + int(ends[parent_index]) + 1) // 2
        expected = (int(starts[parent_index]), midpoint) if index % 2 == 0 else (midpoint, int(ends[parent_index]))
        if (start, end) != expected:
            raise HalfBarStage1Error(f"{name} cell does not match the frozen midpoint rule.")
        duration_sum += duration
    if duration_sum != construction.get("coveredDurationMilliseconds"):
        raise HalfBarStage1Error(f"{name} cell durations do not preserve the covered parent duration.")
    identities = _mapping(construction.get("identities"), f"{name}.identities")
    _exact_fields(
        identities,
        {
            "exactTwoCellsPerParent",
            "allCellsNonempty",
            "parentBoundariesPreserved",
            "prefixPreserved",
            "cellDurationSumEqualsCoveredParentDuration",
        },
        f"{name}.identities",
    )
    if set(identities.values()) != {True}:
        raise HalfBarStage1Error(f"{name} construction identities are not all certified.")


def _validate_funnel(funnel: Mapping[str, Any], name: str) -> None:
    _validate_self_hash(funnel, "funnelSha256", name)
    expected = make_funnel(
        _mapping(funnel.get("counts"), f"{name}.counts"),
        _mapping(funnel.get("durationMilliseconds"), f"{name}.durationMilliseconds"),
    )
    if dict(funnel) != expected:
        raise HalfBarStage1Error(f"{name} rates or identities are stale.")


def _validate_outcome_evidence(outcome: Mapping[str, Any], cell: Mapping[str, Any], name: str) -> None:
    _exact_fields(
        outcome,
        {
            "cellIndex",
            "parentBarIndex",
            "halfIndex",
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
        outcome.get("cellIndex") != cell.get("cellIndex")
        or outcome.get("parentBarIndex") != cell.get("parentBarIndex")
        or outcome.get("halfIndex") != cell.get("halfIndex")
        or outcome.get("durationMilliseconds") != cell.get("durationMilliseconds")
    ):
        raise HalfBarStage1Error(f"{name} identity disagrees with its constructed cell.")
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
        raise HalfBarStage1Error(f"{name} overlap durations are outside the exact cell interval.")
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
            raise HalfBarStage1Error(f"{name}.{field} is stale.")
    for prefix, covered, product_duration in (
        ("reference", reference_covered, reference_product_duration),
        ("prediction", prediction_covered, prediction_product_duration),
    ):
        field = f"{prefix}Product"
        product = outcome.get(field)
        if product is None:
            if covered != 0.0 or product_duration != 0.0:
                raise HalfBarStage1Error(f"{name}.{field} cannot be null with positive overlap evidence.")
        else:
            if not isinstance(product, str) or not product:
                raise HalfBarStage1Error(f"{name}.{field} must be null or nonempty.")
            if covered <= 0 or product_duration <= 0:
                raise HalfBarStage1Error(f"{name}.{field} requires positive overlap evidence.")
            if _bar_product._segment_product({"productLabel": product}) != product:
                raise HalfBarStage1Error(f"{name}.{field} is not a canonical Play Along product.")
    expected_classification, expected_reason = _classification_from_evidence(outcome)
    if outcome.get("classification") != expected_classification or outcome.get("reason") != expected_reason:
        raise HalfBarStage1Error(f"{name} classification/reason is stale.")


def validate_half_bar_stage1_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed on any stale construction, outcome, funnel, stratum, or gate."""

    value = dict(_mapping(artifact, "Stage-1 artifact"))
    expected_top_fields = {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "selectorFitted",
        "operatingThreshold",
        "purpose",
        "publication",
        "inputBindings",
        "inputBindingsSha256",
        "sourceContract",
        "sourceContractSha256",
        "targetPlayerHalfSplitContract",
        "targetPlayerHalfSplitContractSha256",
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
        or value.get("operatingThreshold") is not None
        or value.get("purpose") != "fixed-cell structural observability and oracle correct-support feasibility only"
        or value.get("calibrationMayOpenOnce") is not False
        or value.get("calibrationStatus") != "closed"
    ):
        raise HalfBarStage1Error("Stage-1 envelope or closed-calibration contract is invalid.")
    if (
        value.get("constructionPolicy") != CONSTRUCTION_POLICY
        or value.get("constructionPolicySha256") != CONSTRUCTION_POLICY_SHA256
    ):
        raise HalfBarStage1Error("Stage-1 construction policy is not exact.")
    if (
        value.get("targetPlayerHalfSplitContract") != TARGET_PLAYER_HALF_SPLIT_CONTRACT
        or value.get("targetPlayerHalfSplitContractSha256") != TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256
    ):
        raise HalfBarStage1Error("Stage-1 target-player half-split contract is not exact.")
    if value.get("scoringPolicy") != SCORING_POLICY or value.get("scoringPolicySha256") != SCORING_POLICY_SHA256:
        raise HalfBarStage1Error("Stage-1 scoring policy is not exact.")
    if (
        value.get("sourceContract") != STAGE1_SOURCE_CONTRACT
        or value.get("sourceContractSha256") != STAGE1_SOURCE_CONTRACT_SHA256
    ):
        raise HalfBarStage1Error("Stage-1 official source contract is not exact.")
    if value.get("rubric") != STAGE1_RUBRIC or value.get("rubricSha256") != STAGE1_RUBRIC_SHA256:
        raise HalfBarStage1Error("Stage-1 rubric is not exact.")
    if canonical_sha256(value["inputBindings"]) != value.get("inputBindingsSha256"):
        raise HalfBarStage1Error("Stage-1 input bindings hash is stale.")
    input_bindings = _mapping(value["inputBindings"], "inputBindings")
    _validate_self_hash(input_bindings, "bindingsSha256", "inputBindings")
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
        raise HalfBarStage1Error("Stage-1 publication binding is stale or not an atomic disjoint new-path set.")
    report_binding = _mapping(input_bindings.get("benchmarkReport"), "inputBindings.benchmarkReport")
    if report_binding.get("claimedArtifactSha256") is not None:
        raise HalfBarStage1Error("Benchmark report must not invent a top-level self hash.")
    prediction_sets = _mapping(report_binding.get("predictionSets"), "benchmarkReport.predictionSets")
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
        raise HalfBarStage1Error("Benchmark prediction set bindings are aliased or stale.")
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
        raise HalfBarStage1Error("Benchmark input binding disagrees with the official source contract.")
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
            raise HalfBarStage1Error(f"{binding_name} binding disagrees with the official source contract.")
    runtime_binding = _mapping(input_bindings.get("runtimeManifest"), "inputBindings.runtimeManifest")
    group_binding = _mapping(input_bindings.get("groupManifest"), "inputBindings.groupManifest")
    audio_binding = _mapping(input_bindings.get("audioLineage"), "inputBindings.audioLineage")
    target_player_binding = _mapping(input_bindings.get("targetPlayerWorker"), "inputBindings.targetPlayerWorker")
    _exact_fields(
        target_player_binding,
        {
            "schemaVersion",
            "path",
            "pathSha256",
            "fileSha256",
            "runtimeAnalyzerContractSha256",
            "runtimeManifestWorkerSha256",
            "targetPlayerHalfSplitContractSha256",
            "bindingSha256",
        },
        "inputBindings.targetPlayerWorker",
    )
    _validate_self_hash(target_player_binding, "bindingSha256", "inputBindings.targetPlayerWorker")
    if (
        target_player_binding.get("schemaVersion") != "chord_target_player_half_split_source_binding_v1"
        or canonical_sha256(target_player_binding.get("path")) != target_player_binding.get("pathSha256")
        or target_player_binding.get("fileSha256") != TARGET_PLAYER_HALF_SPLIT_CONTRACT["workerSha256"]
        or target_player_binding.get("runtimeManifestWorkerSha256") != TARGET_PLAYER_HALF_SPLIT_CONTRACT["workerSha256"]
        or target_player_binding.get("runtimeAnalyzerContractSha256")
        != source_contract["runtimeManifest"]["analyzerContractSha256"]
        or target_player_binding.get("targetPlayerHalfSplitContractSha256") != TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256
    ):
        raise HalfBarStage1Error("Target-player worker input binding is stale.")
    if (
        runtime_binding.get("trackSetSha256") != source_contract["runtimeManifest"]["trackSetSha256"]
        or runtime_binding.get("analyzerContractSha256") != source_contract["runtimeManifest"]["analyzerContractSha256"]
        or group_binding.get("trackSetSha256") != source_contract["groupManifest"]["trackSetSha256"]
        or audio_binding.get("projectionSha256") != source_contract["audioLineage"]["projectionSha256"]
    ):
        raise HalfBarStage1Error("Manifest/projection identity binding disagrees with the source contract.")
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
        },
        "sharedPredictionRuntimeBinding",
    )
    if canonical_sha256(shared_binding) != value.get("sharedPredictionRuntimeBindingSha256"):
        raise HalfBarStage1Error("Stage-1 shared prediction/runtime binding hash is stale.")
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
    ):
        _sha(shared_binding.get(field), f"sharedPredictionRuntimeBinding.{field}")
    if (
        dict(shared_binding) != STAGE1_SOURCE_CONTRACT["sharedPredictionRuntimeBinding"]
        or shared_binding.get("schemaVersion") != "chord_fixed_half_bar_prediction_runtime_binding_v1"
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
        raise HalfBarStage1Error("Stage-1 shared prediction/runtime semantics are stale.")

    tracks = [dict(_mapping(row, f"tracks[{index}]")) for index, row in enumerate(_sequence(value["tracks"], "tracks"))]
    if tracks != sorted(tracks, key=lambda row: str(row["trackId"])) or len(
        {str(row["trackId"]) for row in tracks}
    ) != len(tracks):
        raise HalfBarStage1Error("Stage-1 tracks must be unique and sorted.")
    if canonical_sha256(tracks) != value.get("trackSetSha256"):
        raise HalfBarStage1Error("Stage-1 trackSetSha256 is stale.")
    _validate_reviewed_group_shape({str(row["trackId"]): row for row in tracks})
    if {str(row.get("datasetId")) for row in tracks} != set(_examples.LABEL_DETERMINACY_DATASET_IDS):
        raise HalfBarStage1Error("Stage-1 tracks do not cover the exact five certification datasets.")
    if {str(row.get("guitarsetRole")) for row in tracks if row.get("datasetId") == "guitarset"} != {"comp", "solo"}:
        raise HalfBarStage1Error("Stage-1 tracks do not support both GuitarSet role disclosures.")
    _require_official_guitar_role_track_support(tracks)

    projection = _mapping(value.get("sourceAudioLineageProjection"), "sourceAudioLineageProjection")
    _validate_self_hash(projection, "projectionSha256", "sourceAudioLineageProjection")
    if projection.get("projectionSha256") != value.get("sourceAudioLineageProjectionSha256"):
        raise HalfBarStage1Error("Audio-lineage projection top-level binding is stale.")
    if (
        projection.get("projectionSha256") != STAGE1_SOURCE_CONTRACT["audioLineage"]["projectionSha256"]
        or projection.get("trackCount") != STAGE1_SOURCE_CONTRACT["trackCount"]
    ):
        raise HalfBarStage1Error("Audio-lineage projection is not the official 246-track projection.")
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
        raise HalfBarStage1Error("Audio-lineage projection track identities are stale.")
    projection_tracks = {str(row["trackId"]): row for row in projection_rows}
    for row in tracks:
        projected = projection_tracks[str(row["trackId"])]
        track_construction = _mapping(row.get("construction"), "track construction")
        if row.get("datasetId") != projected.get("datasetId") or track_construction.get(
            "canonicalDurationMilliseconds"
        ) != projected.get("canonicalDurationMilliseconds"):
            raise HalfBarStage1Error("Track dataset/duration disagrees with audio-lineage projection.")
    group_projection = {str(row["trackId"]): {"confidenceGroupId": row["confidenceGroupId"]} for row in tracks}
    expected_audio_audit = _examples._audio_group_audit(
        [str(row["trackId"]) for row in tracks], group_projection, projection_tracks
    )
    if (
        value.get("audioGroupAudit") != expected_audio_audit
        or value.get("audioGroupAuditSha256") != expected_audio_audit["auditSha256"]
    ):
        raise HalfBarStage1Error("Audio duplicate-group audit is stale.")
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
                "predictionIdentitySha256",
                "timingFileSha256",
                "timingSha256",
                "timingContractSha256",
                "timingSourceContractSha256",
                "sourceReferenceSha256",
                "referenceEndpointReconciliationRowSha256",
                "predictionOnlySummary",
                "construction",
                "constructionSha256",
                "parentBarCount",
                "cellCount",
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
        construction = _mapping(row.get("construction"), f"tracks[{index}].construction")
        _validate_construction(construction, f"tracks[{index}].construction")
        if row.get("constructionSha256") != construction.get("constructionSha256") or row.get(
            "parentBarCount"
        ) != construction.get("parentBarCount"):
            raise HalfBarStage1Error("Track construction hash binding is stale.")
        for field in ("timingFileSha256", "timingSha256", "timingContractSha256", "timingSourceContractSha256"):
            if row.get(field) != construction.get(field):
                raise HalfBarStage1Error(f"Track {field} binding is stale.")
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
            raise HalfBarStage1Error("Track prediction-only summary path binding is stale.")
        outcomes = [
            dict(_mapping(item, f"tracks[{index}].cellOutcomes[{outcome_index}]"))
            for outcome_index, item in enumerate(_sequence(row.get("cellOutcomes"), "cellOutcomes"))
        ]
        if len(outcomes) != row.get("cellCount") or len(outcomes) != construction.get("cellCount"):
            raise HalfBarStage1Error("Track cell outcome count is stale.")
        for outcome_index, outcome in enumerate(outcomes):
            _validate_self_hash(outcome, "rowSha256", f"tracks[{index}].cellOutcomes[{outcome_index}]")
            cell = construction["cells"][outcome_index]
            _validate_outcome_evidence(outcome, cell, f"tracks[{index}].cellOutcomes[{outcome_index}]")
        if canonical_sha256(outcomes) != row.get("cellOutcomeSetSha256"):
            raise HalfBarStage1Error("Track cellOutcomeSetSha256 is stale.")
        expected_funnel, expected_exclusions = funnel_from_outcomes(outcomes)
        if row.get("funnel") != expected_funnel or row.get("funnelSha256") != expected_funnel["funnelSha256"]:
            raise HalfBarStage1Error("Track funnel is stale.")
        if (
            row.get("exclusionAudit") != expected_exclusions
            or row.get("exclusionAuditSha256") != expected_exclusions["auditSha256"]
        ):
            raise HalfBarStage1Error("Track exclusion audit is stale.")

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
        raise HalfBarStage1Error("Source group track-set binding is stale.")

    structural_support = _structural_support_from_track_rows(tracks)
    if (
        structural_support != OFFICIAL_STRUCTURAL_SUPPORT
        or value.get("structuralSupport") != structural_support
        or value.get("structuralSupportSha256") != structural_support["supportSha256"]
    ):
        raise HalfBarStage1Error("Official structural denominators are stale.")

    aggregate = _sum_funnels([_mapping(row["funnel"], "track funnel") for row in tracks])
    if value.get("aggregate") != aggregate or value.get("aggregateFunnelSha256") != aggregate["funnelSha256"]:
        raise HalfBarStage1Error("Aggregate Stage-1 funnel is stale.")
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
        raise HalfBarStage1Error("Reference endpoint reconciliation audit is stale.")
    audit_rows_by_sha = {str(row["rowSha256"]): row for row in expected_reference_audit["rows"]}
    track_reconciliation_shas = {
        str(row["referenceEndpointReconciliationRowSha256"])
        for row in tracks
        if row.get("referenceEndpointReconciliationRowSha256") is not None
    }
    if track_reconciliation_shas != set(audit_rows_by_sha):
        raise HalfBarStage1Error("Track reconciliation bindings do not exactly match the audit row set.")
    tracks_by_id = {str(row["trackId"]): row for row in tracks}
    for row in expected_reference_audit["rows"]:
        track = tracks_by_id.get(str(row["trackId"]))
        if track is None or (
            track.get("referenceEndpointReconciliationRowSha256") != row.get("rowSha256")
            or track.get("datasetId") != row.get("datasetId")
            or track.get("sourceReferenceSha256") != row.get("referenceSha256")
        ):
            raise HalfBarStage1Error("A reconciliation audit row is not exactly cross-bound to its track.")
    guitar_tracks = [row for row in tracks if row.get("datasetId") == "guitarset"]
    guitar_funnel = _sum_funnels([_mapping(row["funnel"], "GuitarSet track funnel") for row in guitar_tracks])
    guitar = _mapping(value.get("guitarset"), "guitarset")
    if (
        guitar.get("trackCount") != len(guitar_tracks)
        or guitar.get("funnel") != guitar_funnel
        or guitar.get("funnelSha256") != guitar_funnel["funnelSha256"]
        or guitar.get("roleSpecificGates") is not False
    ):
        raise HalfBarStage1Error("GuitarSet aggregate is stale.")
    expected_roles = _stratum_rows(guitar_tracks, "guitarsetRole", ("comp", "solo"))
    if guitar.get("compSolo") != expected_roles or guitar.get("compSoloSetSha256") != canonical_sha256(expected_roles):
        raise HalfBarStage1Error("GuitarSet comp/solo disclosure is stale.")

    dataset_rows = list(_sequence(value.get("datasets"), "datasets"))
    if [row.get("datasetId") for row in dataset_rows if isinstance(row, Mapping)] != list(
        _examples.LABEL_DETERMINACY_DATASET_IDS
    ):
        raise HalfBarStage1Error("Dataset disclosures must use the exact five-dataset order.")
    if canonical_sha256(dataset_rows) != value.get("datasetSetSha256"):
        raise HalfBarStage1Error("Dataset disclosure set hash is stale.")
    for index, raw_row in enumerate(dataset_rows):
        row = _mapping(raw_row, f"datasets[{index}]")
        _validate_self_hash(row, "rowSha256", f"datasets[{index}]")
        _validate_funnel(_mapping(row.get("funnel"), "dataset funnel"), f"datasets[{index}].funnel")
        selected = [track for track in tracks if track.get("datasetId") == row.get("datasetId")]
        if row.get("trackCount") != len(selected) or row.get("funnel") != _sum_funnels(
            [_mapping(track["funnel"], "track funnel") for track in selected]
        ):
            raise HalfBarStage1Error("Dataset disclosure does not sum its tracks.")

    gates = list(_sequence(value.get("gates"), "gates"))
    expected_gates = build_stage1_gates(aggregate, guitar_funnel)
    if gates != expected_gates or canonical_sha256(gates) != value.get("gateSetSha256"):
        raise HalfBarStage1Error("Stage-1 gates are stale or not the exact 13-gate rubric.")
    passed = all(bool(gate["passed"]) for gate in expected_gates)
    failed = [str(gate["gateId"]) for gate in expected_gates if not gate["passed"]]
    expected_decision_payload = {
        "stage1Passed": passed,
        "selectorStageMayRunInNewSealedDevelopmentCycle": passed,
        "failedGateIds": failed,
        "gateCount": 13,
        "passedGateCount": 13 - len(failed),
        "calibrationMayOpenOnce": False,
        "calibrationStatus": "closed",
        "promotionEligible": False,
    }
    expected_decision = _self_hashed(expected_decision_payload, "decisionSha256")
    if value.get("decision") != expected_decision or value.get("stage1Passed") is not passed:
        raise HalfBarStage1Error("Stage-1 decision is stale.")
    return deepcopy(value)


def _execute_stage1(
    benchmark_report: Mapping[str, Any],
    *,
    benchmark_root: Path,
    audio_lineage_manifest: Mapping[str, Any],
    runtime_manifest: Mapping[str, Any],
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
    groups = _mapping(group_manifest, "group manifest")

    # This must remain the first phase: no root resolution, nested leaf access,
    # or summary write may precede complete development-envelope rejection.
    _examples._validate_development_envelopes(report, runtime, groups, audio_lineage)
    validated_audio_lineage = _examples._validate_audio_lineage_preflight(audio_lineage)
    prediction_identities, prediction_report_contract = _prediction_only_report_projection(report)
    metadata_runtime = validate_runtime_bar_grid_manifest(runtime, artifact_root=None, verify_sources=False)
    runtime_tracks = {
        str(row["trackId"]): dict(row) for row in _sequence(metadata_runtime.get("tracks"), "validated runtime tracks")
    }
    track_ids = _examples._validate_same_track_set(prediction_identities, runtime_tracks)
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
        raise HalfBarStage1Error("Runtime manifest changed between metadata and strict source validation.")
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
            projection_tracks=projection_tracks,
            benchmark_root=benchmark_root,
            runtime_root=runtime_root,
            summary_output_root=summary_output_root,
            summary_public_root=summary_public_root,
            runtime_analyzer_contract_sha256=analyzer_contract_sha256,
        )

    label_phase: dict[str, Any] = {}

    def reference_phase(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        report_tracks, complete_report_contract = _examples._validate_report(report)
        if complete_report_contract != prediction_report_contract:
            raise HalfBarStage1Error("Full label-phase report validation changed the prediction-only contract.")
        group_tracks = _examples._validate_group_manifest(groups)
        _examples._validate_same_track_set(report_tracks, runtime_tracks, group_tracks, projection_tracks)
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
        track_rows=track_rows,
        projection_tracks=projection_tracks,
        audio_lineage_projection=audio_projection,
        audio_group_audit=audio_group_audit,
        reconciliation_rows=reconciliation_rows,
    )
    return validate_half_bar_stage1_artifact(artifact)


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

    with tempfile.TemporaryDirectory(prefix="chord-half-bar-stage1-summaries-") as temporary_root:
        staging_root = Path(temporary_root).resolve(strict=True)
        artifact = dict(_mapping(build(staging_root), "staged Stage-1 artifact"))
        precommit_check()
        _publish_json_and_summary_set(output_path, artifact, staging_root, summary_output_root)
        return artifact


def run_half_bar_stage1_preflight(
    benchmark_path: Path,
    *,
    benchmark_root: Path,
    audio_lineage_path: Path,
    runtime_manifest_path: Path,
    runtime_root: Path,
    group_manifest_path: Path,
    group_root: Path,
    summary_output_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Validate exact development sources and publish one new Stage-1 artifact."""

    report, report_raw, report_stat = _sealed_read_json(benchmark_path, "benchmark report")
    audio_lineage, audio_raw, audio_stat = _sealed_read_json(audio_lineage_path, "audio lineage")
    runtime, runtime_raw, runtime_stat = _sealed_read_json(runtime_manifest_path, "runtime manifest")
    groups, groups_raw, groups_stat = _sealed_read_json(group_manifest_path, "group manifest")

    # Reject protected envelopes before resolving any supplied artifact root.
    _examples._validate_development_envelopes(report, runtime, groups, audio_lineage)
    for raw, value, name in (
        (report_raw, report, "benchmark report"),
        (audio_raw, audio_lineage, "audio lineage"),
        (runtime_raw, runtime, "runtime manifest"),
        (groups_raw, groups, "group manifest"),
    ):
        _canonical_input(raw, value, name)
    _validate_official_source_contract(
        report,
        report_raw,
        runtime,
        runtime_raw,
        groups,
        groups_raw,
        audio_lineage,
        audio_raw,
    )
    target_player_binding, target_player_path, target_player_raw, target_player_stat = _target_player_worker_binding(
        runtime
    )
    _preflight_new_output(output_path)
    summary_public_root = _preflight_new_directory(summary_output_root, "Stage-1 summary output root")
    _require_disjoint_summary_root(
        summary_public_root,
        (
            ("benchmark_root", benchmark_root),
            ("runtime_root", runtime_root),
            ("group_root", group_root),
        ),
    )

    input_bindings_payload = {
        "schemaVersion": "chord_fixed_half_bar_stage1_input_bindings_v1",
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
            **_top_binding(audio_lineage_path, audio_raw, audio_lineage, "artifactSha256", "audio lineage"),
            "projectionSha256": _mapping(
                _mapping(report.get("uncertaintyExperiment"), "uncertaintyExperiment").get("audioLineage"),
                "uncertaintyExperiment.audioLineage",
            )["projectionSha256"],
        },
        "runtimeManifest": {
            **_top_binding(runtime_manifest_path, runtime_raw, runtime, "manifestSha256", "runtime manifest"),
            "trackSetSha256": runtime["trackSetSha256"],
            "analyzerContractSha256": _mapping(runtime["analyzerContract"], "runtime analyzerContract")[
                "contractSha256"
            ],
        },
        "runtimeRoot": _root_binding(runtime_root, "runtime root"),
        "groupManifest": {
            **_top_binding(group_manifest_path, groups_raw, groups, "manifestSha256", "group manifest"),
            "trackSetSha256": groups["trackSetSha256"],
        },
        "groupRoot": _root_binding(group_root, "group root"),
        "targetPlayerWorker": target_player_binding,
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
        _verify_input_unchanged(group_manifest_path, groups_stat, groups_raw, "group manifest")
        _verify_input_unchanged(
            target_player_path,
            target_player_stat,
            target_player_raw,
            "target-player worker source",
        )

    def build_in_staging(staging_root: Path) -> dict[str, Any]:
        return _execute_stage1(
            report,
            benchmark_root=benchmark_root,
            audio_lineage_manifest=audio_lineage,
            runtime_manifest=runtime,
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
        description="Run the sealed development-only fixed half-bar-cell Stage-1 feasibility preflight."
    )
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--audio-lineage", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--group-manifest", type=Path, required=True)
    parser.add_argument("--group-root", type=Path, required=True)
    parser.add_argument("--summary-output-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    artifact = run_half_bar_stage1_preflight(
        args.benchmark,
        benchmark_root=args.benchmark_root,
        audio_lineage_path=args.audio_lineage,
        runtime_manifest_path=args.runtime_manifest,
        runtime_root=args.runtime_root,
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
    "HalfBarStage1Error",
    "OFFICIAL_STRUCTURAL_SUPPORT",
    "STAGE1_RUBRIC",
    "STAGE1_RUBRIC_SHA256",
    "STAGE1_SCHEMA",
    "STAGE1_SOURCE_CONTRACT",
    "STAGE1_SOURCE_CONTRACT_SHA256",
    "TARGET_PLAYER_HALF_SPLIT_CONTRACT",
    "TARGET_PLAYER_HALF_SPLIT_CONTRACT_SHA256",
    "build_stage1_gates",
    "construct_half_bar_cells",
    "funnel_from_outcomes",
    "main",
    "make_funnel",
    "run_half_bar_stage1_preflight",
    "score_fixed_cells",
    "summarize_prediction_cells",
    "validate_half_bar_stage1_artifact",
]
