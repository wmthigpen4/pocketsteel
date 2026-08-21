"""One-shot development readiness evaluation for the frozen beat-cell selector.

The mapping evaluator in this module is intentionally file-system neutral so
synthetic tests can exercise the policy without opening any official leaf.
The file runner is deliberately different: it has no caller-supplied paths and
will read and publish only the exact paths sealed by the committed Stage-2
authority.  Neither entry point reads calibration, test, confirmation, player,
public-song, Travis, audio, prediction, or reference inputs.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import stat
from typing import Any

from .bar_promotion import canonical_sha256
from .beat_cell_examples import (
    BEAT_CELL_EXAMPLES_SCHEMA,
    BEAT_CELL_LABEL_AUDITS_SCHEMA,
    validate_beat_cell_examples_artifact,
)
from .beat_cell_selector import (
    BEAT_CELL_SELECTOR_SCHEMA,
    BEAT_CELL_SELECTOR_ESTIMAND,
    BEAT_CELL_SELECTOR_OOF_DENOMINATOR,
    train_beat_cell_selector,
    validate_beat_cell_selector_artifact,
)
from .beat_cell_stage1 import make_funnel, validate_beat_cell_stage1_artifact
from .beat_cell_readiness_recovery_contract import (
    READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256,
    READINESS_RECOVERY_AUTHORITY_FILE_SHA256,
    READINESS_RECOVERY_AUTHORITY_SCHEMA,
    READINESS_RECOVERY_AUTHORIZATION_SCHEMA,
    READINESS_RECOVERY_ID,
    load_readiness_recovery_authorization,
    load_readiness_recovery_authority,
    recovery_authorization_path,
    recovery_authority_path,
)
from .beat_cell_stage2_contract import (
    BEAT_CELL_FEATURE_SET_PUBLICATION_MODE,
    BEAT_CELL_ONE_SHOT_PROJECTION_SHA256,
    BEAT_CELL_READINESS_PROJECTION_SHA256,
    BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE,
    BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256,
    BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA,
    authority_path,
    load_beat_cell_stage2_authority,
)


DEVELOPMENT_SPLIT = "development"
BEAT_CELL_READINESS_SCHEMA = "chord_runtime_beat_cell_selector_development_readiness_v2"
BEAT_CELL_READINESS_RUBRIC_SCHEMA = "chord_runtime_beat_cell_selector_development_readiness_rubric_v1"
BEAT_CELL_READINESS_INPUT_BINDINGS_SCHEMA = "chord_runtime_beat_cell_selector_readiness_input_bindings_v2"
BEAT_CELL_READINESS_JOINED_ROW_SCHEMA = "chord_runtime_beat_cell_selector_readiness_joined_oof_row_v2"

AUTHORITY_FILE_SHA256 = BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256
AUTHORITY_CANONICAL_SHA256 = BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256
READINESS_PROJECTION_SHA256 = BEAT_CELL_READINESS_PROJECTION_SHA256
ONE_SHOT_PROJECTION_SHA256 = BEAT_CELL_ONE_SHOT_PROJECTION_SHA256
RECOVERY_AUTHORITY_FILE_SHA256 = READINESS_RECOVERY_AUTHORITY_FILE_SHA256
RECOVERY_AUTHORITY_CANONICAL_SHA256 = READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256
RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH = recovery_authorization_path()
IMPLEMENTATION_AUTHORITY_HEAD = "0933007489656500ec17fec1f64628031564214f"

FIXED_TARGET_COVERAGE = 0.50
WILSON_ONE_SIDED_Z_95 = 1.6448536269514722
RELIABILITY_BIN_COUNT = 10
PROBABILITY_FLOOR = 1e-12
PROBABILITY_QUANTILES = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)
ABSOLUTE_Z_QUANTILES = (0.0, 0.5, 0.9, 0.95, 0.99, 1.0)
INTEGER_COUNT_FEATURE_NAMES = frozenset({"predictionTransitionCount"})
INTEGER_FLAG_FEATURE_NAMES = frozenset(
    {
        "productFamilyNone",
        "productFamilyMajor",
        "productFamilyMinor",
        "productFamilyDominant",
        "productFamilyMinorSeventh",
    }
)
INTEGER_FEATURE_NAMES = INTEGER_COUNT_FEATURE_NAMES | INTEGER_FLAG_FEATURE_NAMES
DATASET_IDS = ("aam", "guitarset", "idmt_guitar", "nrgcp", "winterreise")
GUITARSET_ROLES = ("comp", "solo")
OUTER_FOLD_COUNT = 5
EXPECTED_DATASET_TRACK_COUNTS = {
    "aam": 2,
    "guitarset": 36,
    "idmt_guitar": 48,
    "nrgcp": 156,
    "winterreise": 4,
}
EXPECTED_GUITARSET_ROLE_TRACK_COUNTS = {"comp": 18, "solo": 18}
EXPECTED_GUITARSET_ROLE_REFERENCE_COUNTS = {"comp": 954, "solo": 1264}
EXPECTED_GUITARSET_ROLE_REFERENCE_DURATION_MS = {"comp": 513043, "solo": 521156}
EXPECTED_STAGE1_ADMISSION_PROJECTION_SHA256 = "9819e8a3c639179a04246c53e59ea85627178e33dd6a51d2e412a63082309be9"
READINESS_PURPOSE = "one-shot development readiness only; not calibration, promotion, or player authorization"
PUBLICATION_MODE = BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE
_PUBLICATION_POLICY_FIELDS = frozenset({"schemaVersion", "featureSet", "singleJson"})

EXPECTED_STAGE1_AGGREGATE_COUNT = {
    "T": 11234,
    "U": 1445,
    "R": 9789,
    "N": 413,
    "E": 9376,
    "C": 7352,
    "I": 2024,
}
EXPECTED_STAGE1_AGGREGATE_DURATION_MS = {
    "T": 6201472,
    "U": 885368,
    "R": 5316104,
    "N": 241755,
    "E": 5074349,
    "C": 4045887,
    "I": 1028462,
}
EXPECTED_STAGE1_GUITARSET_COUNT = {
    "T": 2392,
    "U": 174,
    "R": 2218,
    "N": 158,
    "E": 2060,
    "C": 921,
    "I": 1139,
}
EXPECTED_STAGE1_GUITARSET_DURATION_MS = {
    "T": 1133524,
    "U": 99325,
    "R": 1034199,
    "N": 83715,
    "E": 950484,
    "C": 437514,
    "I": 512970,
}

_COUNT_GATE_IDS = (
    "aggregate.accepted-count",
    "aggregate.end-to-end-micro-coverage",
    "aggregate.micro-precision",
    "aggregate.one-sided-wilson95-lower-bound",
    "aggregate.group-balanced-conditional-coverage",
    "aggregate.group-balanced-precision",
    "guitarset.accepted-count",
    "guitarset.end-to-end-micro-coverage",
    "guitarset.micro-precision",
    "guitarset.group-balanced-conditional-coverage",
    "guitarset.group-balanced-precision",
)
_DURATION_GATE_IDS = (
    "aggregate.duration-end-to-end-coverage",
    "aggregate.duration-micro-precision",
    "guitarset.duration-end-to-end-coverage",
    "guitarset.duration-micro-precision",
)

BEAT_CELL_READINESS_RUBRIC: dict[str, Any] = {
    "schemaVersion": BEAT_CELL_READINESS_RUBRIC_SCHEMA,
    "split": DEVELOPMENT_SPLIT,
    "developmentOnly": True,
    "promotionEligible": False,
    "implementationAuthorityHead": IMPLEMENTATION_AUTHORITY_HEAD,
    "authorityFileSha256": AUTHORITY_FILE_SHA256,
    "authorityCanonicalSha256": AUTHORITY_CANONICAL_SHA256,
    "readinessProjectionSha256": READINESS_PROJECTION_SHA256,
    "oneShotProjectionSha256": ONE_SHOT_PROJECTION_SHA256,
    "operatingThresholdSelection": None,
    "descriptiveCutoff": {
        "targetCoverage": FIXED_TARGET_COVERAGE,
        "source": "selector.outOfFoldEvaluation.precisionCoverage",
        "field": "minimumProbabilityAtDescriptivePoint",
        "acceptanceRule": "probability >= cutoff including the complete exact-equal tie block",
        "role": "development readiness diagnostic only; never calibration or production threshold",
    },
    "stage1Admissions": {
        "aggregateCounts": deepcopy(EXPECTED_STAGE1_AGGREGATE_COUNT),
        "aggregateDurationMilliseconds": deepcopy(EXPECTED_STAGE1_AGGREGATE_DURATION_MS),
        "guitarsetCounts": deepcopy(EXPECTED_STAGE1_GUITARSET_COUNT),
        "guitarsetDurationMilliseconds": deepcopy(EXPECTED_STAGE1_GUITARSET_DURATION_MS),
        "guitarsetRoleReferenceDeterminateCount": deepcopy(EXPECTED_GUITARSET_ROLE_REFERENCE_COUNTS),
        "guitarsetRoleReferenceDeterminateDurationMilliseconds": deepcopy(
            EXPECTED_GUITARSET_ROLE_REFERENCE_DURATION_MS
        ),
        "completeAdmissionProjectionSha256": EXPECTED_STAGE1_ADMISSION_PROJECTION_SHA256,
        "stage1GateCount": 13,
        "allStage1GatesMustRemainPassed": True,
        "standaloneValidationScope": (
            "the sealed readiness artifact exactly authenticates aggregate and GuitarSet admissions, "
            "all eligible C/I bindings, dataset/role partitions, and official structural denominators; "
            "full source authenticity additionally requires the official mapping evaluator's strict "
            "Stage-1 input validation"
        ),
    },
    "countGateIds": list(_COUNT_GATE_IDS),
    "durationGateIds": list(_DURATION_GATE_IDS),
    "durationWeightingScope": (
        "micro-time-exposure gates and disclosures only; never training, group-balanced metrics, "
        "Wilson, probability curves, cutoff, or model selection"
    ),
    "guitarsetRolePolicy": (
        "comp and solo count-and-duration disclosures required; no role gate and no solo authorization"
    ),
    "mandatoryDatasetDisclosures": list(DATASET_IDS),
    "mandatoryDiagnostics": [
        "fixed-probability-decile-micro-and-group-balanced-reliability-and-ECE",
        "micro-and-group-balanced-log-loss-Brier-AURC",
        "exact-tie-block-precision-coverage-curve",
        "correct-and-incorrect-probability-quantiles",
        "outer-fold-dataset-and-guitarset-role-slices",
        "accepted-group-concentration",
        "feature-missingness-allMissing-and-standardized-absolute-z-drift",
        "reference-endpoint-reconciliation",
    ],
    "decision": (
        "exact integrity and Stage1 admissions plus all 15 count/Wilson/group/duration gates and "
        "complete mandatory diagnostics may set calibrationMayOpenOnce; execution then stops"
    ),
}
BEAT_CELL_READINESS_RUBRIC_SHA256 = canonical_sha256(BEAT_CELL_READINESS_RUBRIC)

_HEX = frozenset("0123456789abcdef")
_FUNNEL_FIELDS = ("T", "U", "R", "N", "E", "C", "I")
_RECOVERY_NEW_CYCLE_COUNTS = {
    "featureSetBuildCount": 0,
    "examplesBuildCount": 0,
    "selectorCandidateCount": 0,
    "readinessEvaluationCount": 1,
    "readinessReproductionRefitCount": 1,
    "sameCycleRetryAllowed": False,
}
_RECOVERY_CUMULATIVE_COUNTS = {
    "featureSetBuildCount": 1,
    "examplesBuildCount": 1,
    "selectorCandidateCount": 1,
    "readinessEvaluationCount": 2,
    "readinessReproductionRefitCount": 2,
}


class BeatCellReadinessError(ValueError):
    """A frozen beat-cell readiness invariant failed closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BeatCellReadinessError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise BeatCellReadinessError(f"{name} must be an array.")
    return value


def _exact_fields(value: Mapping[str, Any], expected: frozenset[str] | set[str], name: str) -> None:
    if set(value) != set(expected):
        missing = sorted(set(expected) - set(value))
        extra = sorted(set(value) - set(expected))
        raise BeatCellReadinessError(f"{name} has a noncanonical schema: missing={missing}, extra={extra}.")


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or "\x00" in value:
        raise BeatCellReadinessError(f"{name} must be a trimmed nonempty string without NUL bytes.")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise BeatCellReadinessError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BeatCellReadinessError(f"{name} must be an integer >= {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BeatCellReadinessError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise BeatCellReadinessError(f"{name} must be a finite number.")
    return result


def _unsigned(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _render_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def _authority_publication_policy(authority: Mapping[str, Any]) -> Mapping[str, Any]:
    output_paths = _mapping(authority.get("outputPaths"), "authority.outputPaths")
    publication = _mapping(output_paths.get("publication"), "authority.outputPaths.publication")
    _exact_fields(publication, _PUBLICATION_POLICY_FIELDS, "authority.outputPaths.publication")
    if (
        publication.get("schemaVersion") != BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA
        or publication.get("featureSet") != BEAT_CELL_FEATURE_SET_PUBLICATION_MODE
        or publication.get("singleJson") != PUBLICATION_MODE
    ):
        raise BeatCellReadinessError("The authority publication policy is not the exact frozen split policy.")
    return publication


def _authority_contract() -> dict[str, Any]:
    """Load and re-pin the one committed machine authority before artifact access."""

    try:
        authority = dict(load_beat_cell_stage2_authority())
    except Exception as error:  # pragma: no cover - normalized at public boundary
        raise BeatCellReadinessError("The committed beat-cell Stage-2 authority failed validation.") from error
    if canonical_sha256(authority) != AUTHORITY_CANONICAL_SHA256:
        raise BeatCellReadinessError("The committed beat-cell Stage-2 authority canonical hash drifted.")
    _authority_publication_policy(authority)
    readiness = _mapping(authority.get("readiness"), "authority.readiness")
    one_shot = _mapping(authority.get("oneShot"), "authority.oneShot")
    if canonical_sha256(readiness) != READINESS_PROJECTION_SHA256:
        raise BeatCellReadinessError("The exact readiness projection drifted.")
    if canonical_sha256(one_shot) != ONE_SHOT_PROJECTION_SHA256:
        raise BeatCellReadinessError("The exact one-shot projection drifted.")
    if (
        readiness.get("fixedTargetCoverage") != FIXED_TARGET_COVERAGE
        or readiness.get("countGates") is None
        or len(_sequence(readiness["countGates"], "authority.readiness.countGates")) != 11
        or len(_sequence(readiness.get("durationGates"), "authority.readiness.durationGates")) != 4
        or one_shot.get("readinessEvaluationCount") != 1
        or one_shot.get("readinessReproductionRefitCount") != 1
        or one_shot.get("sameCycleRetryAllowed") is not False
    ):
        raise BeatCellReadinessError("The committed readiness/one-shot mechanics drifted.")
    return authority


def _recovery_contract() -> dict[str, Any]:
    """Load the distinct R5 authority and require its final execution receipt."""

    try:
        recovery = dict(load_readiness_recovery_authority())
    except Exception as error:  # pragma: no cover - normalized at public boundary
        raise BeatCellReadinessError("The committed readiness recovery authority failed validation.") from error
    if canonical_sha256(recovery) != RECOVERY_AUTHORITY_CANONICAL_SHA256:
        raise BeatCellReadinessError("The readiness recovery authority canonical hash drifted.")
    if (
        recovery.get("schemaVersion") != READINESS_RECOVERY_AUTHORITY_SCHEMA
        or recovery.get("split") != DEVELOPMENT_SPLIT
        or recovery.get("developmentOnly") is not True
        or recovery.get("promotionEligible") is not False
        or recovery.get("recoveryId") != READINESS_RECOVERY_ID
    ):
        raise BeatCellReadinessError("The readiness recovery authority envelope is not exact.")

    source_cycle = _mapping(recovery.get("sourceCycle"), "recovery.sourceCycle")
    if (
        source_cycle.get("authorityFileSha256") != AUTHORITY_FILE_SHA256
        or source_cycle.get("authorityCanonicalSha256") != AUTHORITY_CANONICAL_SHA256
        or _mapping(source_cycle.get("projectionSha256"), "recovery.sourceCycle.projectionSha256").get("readiness")
        != READINESS_PROJECTION_SHA256
        or source_cycle["projectionSha256"].get("oneShot") != ONE_SHOT_PROJECTION_SHA256
    ):
        raise BeatCellReadinessError("The recovery authority does not bind the exact R4 source authority.")

    output = _mapping(recovery.get("output"), "recovery.output")
    _exact_fields(
        output,
        {"readinessReport", "publicationMode", "mustBeNew", "callerPathOverrideAllowed"},
        "recovery.output",
    )
    if (
        output.get("publicationMode") != PUBLICATION_MODE
        or output.get("mustBeNew") is not True
        or output.get("callerPathOverrideAllowed") is not False
    ):
        raise BeatCellReadinessError("The recovery publication policy is not exact.")
    output_path = _string(output.get("readinessReport"), "recovery.output.readinessReport")
    immutable = _mapping(recovery.get("immutableInputs"), "recovery.immutableInputs")
    input_paths = {
        _string(_mapping(immutable.get(name), f"recovery.immutableInputs.{name}").get("path"), f"{name} path")
        for name in ("stage1", "examples", "selector")
    }
    if output_path in input_paths:
        raise BeatCellReadinessError("The recovery output overlaps an immutable R4 input.")

    frozen = _mapping(recovery.get("frozenPolicy"), "recovery.frozenPolicy")
    if (
        frozen.get("readinessProjectionSha256") != READINESS_PROJECTION_SHA256
        or frozen.get("oneShotProjectionSha256") != ONE_SHOT_PROJECTION_SHA256
        or frozen.get("readinessRubricSha256") != BEAT_CELL_READINESS_RUBRIC_SHA256
        or frozen.get("fixedTargetCoverage") != FIXED_TARGET_COVERAGE
        or frozen.get("gateCount") != 15
        or frozen.get("featureFoldWeightDatasetSelectorChangeAllowed") is not False
        or frozen.get("thresholdSelectionAllowed") is not False
        or frozen.get("calibrationAccessDuringRecoveryAllowed") is not False
    ):
        raise BeatCellReadinessError("The recovery authority changed the frozen R4 readiness policy.")

    one_shot = _mapping(recovery.get("oneShot"), "recovery.oneShot")
    if (
        dict(_mapping(one_shot.get("newCycle"), "recovery.oneShot.newCycle")) != _RECOVERY_NEW_CYCLE_COUNTS
        or dict(
            _mapping(
                one_shot.get("cumulativeIncludingConsumedR4"),
                "recovery.oneShot.cumulativeIncludingConsumedR4",
            )
        )
        != _RECOVERY_CUMULATIVE_COUNTS
        or one_shot.get("immutableR4ArtifactsMustBeReused") is not True
        or one_shot.get("featureExamplesSelectorRegenerationAllowed") is not False
        or one_shot.get("stopAfterReadinessForIndependentAudit") is not True
    ):
        raise BeatCellReadinessError("The recovery one-shot counts or immutable-reuse policy changed.")

    forbidden = _mapping(recovery.get("forbiddenAccess"), "recovery.forbiddenAccess")
    if not forbidden or any(value is not False for value in forbidden.values()):
        raise BeatCellReadinessError("The recovery authority opened a forbidden surface.")
    implementation = _mapping(recovery.get("implementation"), "recovery.implementation")
    if implementation.get("executionAuthorized") is not False or any(
        implementation.get(field) is not None
        for field in (
            "finalReadinessModuleFileSha256",
            "finalRecoveryContractFileSha256",
            "finalReadinessTestFileSha256",
            "finalImplementationCommit",
        )
    ):
        raise BeatCellReadinessError("The preregistration must remain non-executable and receipt-neutral.")
    return recovery


def _implementation_authorization_receipt() -> Mapping[str, Any]:
    """Load the separate fixed-path R5 implementation receipt or fail closed."""

    try:
        return dict(load_readiness_recovery_authorization())
    except Exception as error:  # pragma: no cover - exact causes belong to the contract loader
        raise BeatCellReadinessError(
            "The R5 readiness implementation authorization receipt is not installed or is invalid at its "
            f"fixed path {RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH}; execution remains closed."
            f" Required schema: {READINESS_RECOVERY_AUTHORIZATION_SCHEMA}."
        ) from error


def _sealed_preflight(stage1: Mapping[str, Any], examples: Mapping[str, Any], selector: Mapping[str, Any]) -> None:
    """Reject protected or promotion-capable envelopes before nested validation."""

    for value, name in ((stage1, "Stage-1"), (examples, "examples")):
        if (
            value.get("split") != DEVELOPMENT_SPLIT
            or value.get("developmentOnly") is not True
            or value.get("promotionEligible") is not False
        ):
            raise BeatCellReadinessError(f"{name} must be development-only and promotion-ineligible.")
    if stage1.get("stage1Passed") is not True or stage1.get("calibrationMayOpenOnce") is not False:
        raise BeatCellReadinessError("Stage-1 must be passed while calibration remains closed.")
    if (
        selector.get("developmentOnly") is not True
        or selector.get("promotionEligible") is not False
        or selector.get("operatingThreshold") is not None
    ):
        raise BeatCellReadinessError("Selector must be development-only with no operating threshold.")
    training = _mapping(selector.get("training"), "selector.training")
    if training.get("split") != DEVELOPMENT_SPLIT:
        raise BeatCellReadinessError("selector.training.split must be development.")


def _funnel_measure(funnel: Mapping[str, Any], field: str, name: str) -> dict[str, int]:
    measure = _mapping(funnel.get(field), f"{name}.{field}")
    result = {key: _integer(measure.get(key), f"{name}.{field}.{key}") for key in _FUNNEL_FIELDS}
    if not (
        result["T"] == result["U"] + result["R"]
        and result["R"] == result["N"] + result["E"]
        and result["E"] == result["C"] + result["I"]
    ):
        raise BeatCellReadinessError(f"{name}.{field} violates T/U/R/N/E/C/I partitions.")
    return result


def _stratum_funnel(row: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    return _mapping(row.get("funnel"), f"{name}.funnel")


def _validated_admission_funnel(value: Mapping[str, Any], name: str) -> dict[str, Any]:
    counts = _funnel_measure(value, "counts", name)
    duration = _funnel_measure(value, "durationMilliseconds", name)
    expected = make_funnel(counts, duration)
    if dict(value) != expected:
        raise BeatCellReadinessError(f"{name} is not the exact self-hashed Stage-1 funnel contract.")
    return expected


def _validate_stage1_admission(stage1: Mapping[str, Any], authority: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and reduce the one exact passed Stage-1 artifact."""

    try:
        validated = validate_beat_cell_stage1_artifact(stage1)
    except Exception as error:
        raise BeatCellReadinessError("The exact beat-cell Stage-1 artifact failed validation.") from error
    if validated != dict(stage1):
        raise BeatCellReadinessError("Stage-1 validation changed the supplied canonical object.")
    source = _mapping(
        _mapping(authority.get("sourceInputs"), "authority.sourceInputs").get("stage1Report"), "stage1 source"
    )
    exact_fields = {
        "artifactSha256": "artifactSha256",
        "gateSetSha256": "gateSetSha256",
        "trackSetSha256": "trackSetSha256",
        "sourceContractSha256": "sourceContractSha256",
    }
    for source_field, stage1_field in exact_fields.items():
        if stage1.get(stage1_field) != source.get(source_field):
            raise BeatCellReadinessError(f"Stage-1 {stage1_field} is not the exact admitted result.")
    if _mapping(stage1.get("decision"), "Stage-1 decision").get("decisionSha256") != source.get("decisionSha256"):
        raise BeatCellReadinessError("Stage-1 decisionSha256 is not the exact admitted result.")
    if canonical_sha256(stage1) != source.get("canonicalSha256"):
        raise BeatCellReadinessError("Stage-1 canonical object is not the exact admitted result.")
    if _sha256_bytes(_render_json(stage1)) != source.get("fileSha256"):
        raise BeatCellReadinessError("Stage-1 canonical rendered bytes are not the exact admitted file receipt.")
    decision = _mapping(stage1.get("decision"), "Stage-1 decision")
    gates = _sequence(stage1.get("gates"), "Stage-1 gates")
    if (
        decision.get("stage1Passed") is not True
        or decision.get("selectorStageMayRunInNewSealedDevelopmentCycle") is not True
        or decision.get("selectorUseAllowed") is not False
        or decision.get("gateCount") != 13
        or decision.get("passedGateCount") != 13
        or decision.get("failedGateIds") != []
        or len(gates) != 13
        or any(_mapping(gate, "Stage-1 gate").get("passed") is not True for gate in gates)
    ):
        raise BeatCellReadinessError("All 13 exact Stage-1 admissions must remain passed.")
    aggregate = _mapping(stage1.get("aggregate"), "Stage-1 aggregate")
    guitarset = _stratum_funnel(_mapping(stage1.get("guitarset"), "Stage-1 GuitarSet"), "Stage-1 GuitarSet")
    if (
        _funnel_measure(aggregate, "counts", "Stage-1 aggregate") != EXPECTED_STAGE1_AGGREGATE_COUNT
        or _funnel_measure(aggregate, "durationMilliseconds", "Stage-1 aggregate")
        != EXPECTED_STAGE1_AGGREGATE_DURATION_MS
        or _funnel_measure(guitarset, "counts", "Stage-1 GuitarSet") != EXPECTED_STAGE1_GUITARSET_COUNT
        or _funnel_measure(guitarset, "durationMilliseconds", "Stage-1 GuitarSet")
        != EXPECTED_STAGE1_GUITARSET_DURATION_MS
    ):
        raise BeatCellReadinessError("Stage-1 aggregate or GuitarSet count/duration admissions drifted.")

    dataset_rows = list(_sequence(stage1.get("datasets"), "Stage-1 datasets"))
    if [row.get("datasetId") for row in dataset_rows if isinstance(row, Mapping)] != list(DATASET_IDS):
        raise BeatCellReadinessError("Stage-1 dataset disclosures changed their exact five-dataset order.")
    guitar = _mapping(stage1.get("guitarset"), "Stage-1 GuitarSet")
    role_rows = list(_sequence(guitar.get("compSolo"), "Stage-1 GuitarSet compSolo"))
    if [row.get("guitarsetRole") for row in role_rows if isinstance(row, Mapping)] != list(GUITARSET_ROLES):
        raise BeatCellReadinessError("Stage-1 GuitarSet disclosures must retain comp then solo.")
    role_counts = {}
    role_durations = {}
    for raw in role_rows:
        row = _mapping(raw, "Stage-1 GuitarSet role")
        role = str(row["guitarsetRole"])
        funnel = _stratum_funnel(row, f"Stage-1 GuitarSet {role}")
        role_counts[role] = _funnel_measure(funnel, "counts", f"Stage-1 GuitarSet {role}")
        role_durations[role] = _funnel_measure(funnel, "durationMilliseconds", f"Stage-1 GuitarSet {role}")
    if {role: role_counts[role]["R"] for role in GUITARSET_ROLES} != EXPECTED_GUITARSET_ROLE_REFERENCE_COUNTS or {
        role: role_durations[role]["R"] for role in GUITARSET_ROLES
    } != EXPECTED_GUITARSET_ROLE_REFERENCE_DURATION_MS:
        raise BeatCellReadinessError("Stage-1 GuitarSet role denominators drifted.")

    eligible_outcome_bindings: list[dict[str, Any]] = []
    for raw_track in _sequence(stage1.get("tracks"), "Stage-1 tracks"):
        track = _mapping(raw_track, "Stage-1 track")
        prediction_identity = _mapping(track.get("predictionIdentity"), "Stage-1 predictionIdentity")
        for raw_outcome in _sequence(track.get("cellOutcomes"), "Stage-1 cellOutcomes"):
            outcome = _mapping(raw_outcome, "Stage-1 outcome")
            if outcome.get("classification") not in {"C", "I"}:
                continue
            eligible_outcome_bindings.append(
                {
                    "trackId": track["trackId"],
                    "cellIndex": outcome["cellIndex"],
                    "durationMilliseconds": outcome["durationMilliseconds"],
                    "sourceBeatCellSha256": outcome["sourceBeatCellSha256"],
                    "stage1OutcomeRowSha256": outcome["rowSha256"],
                    "classification": outcome["classification"],
                    "datasetId": track["datasetId"],
                    "role": track["role"],
                    "guitarsetRole": track["guitarsetRole"],
                    "confidenceGroupId": track["confidenceGroupId"],
                    "sourceGroupTrackRowSha256": track["sourceGroupTrackMetadataSha256"],
                    "predictionIdentitySha256": track["predictionIdentitySha256"],
                    "audioLineageRowSha256": prediction_identity["audioLineageRowSha256"],
                }
            )
    eligible_outcome_bindings.sort(key=lambda row: (str(row["trackId"]), int(row["cellIndex"])))
    if (
        len(eligible_outcome_bindings) != EXPECTED_STAGE1_AGGREGATE_COUNT["E"]
        or sum(int(row["durationMilliseconds"]) for row in eligible_outcome_bindings)
        != EXPECTED_STAGE1_AGGREGATE_DURATION_MS["E"]
    ):
        raise BeatCellReadinessError("Stage-1 eligible outcome binding inventory drifted.")

    payload = {
        "sourceStage1ArtifactSha256": stage1["artifactSha256"],
        "sourceStage1DecisionSha256": stage1["decision"]["decisionSha256"],
        "sourceStage1GateSetSha256": stage1["gateSetSha256"],
        "sourceStage1TrackSetSha256": stage1["trackSetSha256"],
        "sourceStage1SourceContractSha256": stage1["sourceContractSha256"],
        "allThirteenStage1GatesPassed": True,
        "eligibleOutcomeCount": len(eligible_outcome_bindings),
        "eligibleOutcomeDurationMilliseconds": sum(
            int(row["durationMilliseconds"]) for row in eligible_outcome_bindings
        ),
        "eligibleOutcomeBindingSetSha256": canonical_sha256(eligible_outcome_bindings),
        "aggregate": deepcopy(aggregate),
        "datasets": deepcopy(dataset_rows),
        "guitarset": deepcopy(guitar),
        "referenceEndpointReconciliationAudit": deepcopy(stage1["referenceEndpointReconciliationAudit"]),
        "referenceEndpointReconciliationAuditSha256": stage1["referenceEndpointReconciliationAuditSha256"],
    }
    admission = {**payload, "admissionSha256": canonical_sha256(payload)}
    if admission["admissionSha256"] != EXPECTED_STAGE1_ADMISSION_PROJECTION_SHA256:
        raise BeatCellReadinessError("The complete Stage-1 admission projection receipt drifted.")
    return admission


def _validate_examples_admission(
    examples: Mapping[str, Any],
    authority: Mapping[str, Any],
    stage1_admission: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    try:
        validated = validate_beat_cell_examples_artifact(examples)
    except Exception as error:
        raise BeatCellReadinessError("The sealed beat-cell examples artifact failed validation.") from error
    if validated != dict(examples):
        raise BeatCellReadinessError("Examples validation changed the supplied canonical object.")
    if examples.get("schemaVersion") != BEAT_CELL_EXAMPLES_SCHEMA:
        raise BeatCellReadinessError("Examples use an unsupported beat-cell schemaVersion.")
    stage1_source = _mapping(
        _mapping(authority.get("sourceInputs"), "authority.sourceInputs").get("stage1Report"),
        "authority.sourceInputs.stage1Report",
    )
    expected_source_fields = {
        "sourceStage1FileSha256": "fileSha256",
        "sourceStage1CanonicalSha256": "canonicalSha256",
        "sourceStage1ArtifactSha256": "artifactSha256",
        "sourceStage1DecisionSha256": "decisionSha256",
        "sourceStage1GateSetSha256": "gateSetSha256",
        "sourceStage1SourceContractSha256": "sourceContractSha256",
        "sourceStage1TrackSetSha256": "trackSetSha256",
    }
    for examples_field, authority_field in expected_source_fields.items():
        if examples.get(examples_field) != stage1_source.get(authority_field):
            raise BeatCellReadinessError(f"examples.{examples_field} is not the exact admitted Stage-1 source.")
    if examples.get("sourceStage1ArtifactSha256") != stage1_admission.get("sourceStage1ArtifactSha256"):
        raise BeatCellReadinessError("Examples and the admitted Stage-1 object disagree.")

    feature_names = list(_sequence(examples.get("featureNames"), "examples.featureNames"))
    expected_features = list(
        _sequence(
            _mapping(authority.get("featureMath"), "authority.featureMath").get("featureNames"),
            "authority.featureMath.featureNames",
        )
    )
    if feature_names != expected_features or len(feature_names) != 48 or len(set(feature_names)) != 48:
        raise BeatCellReadinessError("Examples changed the exact ordered 48-feature matrix contract.")
    raw_examples = list(_sequence(examples.get("examples"), "examples.examples"))
    expected_count = _integer(
        _mapping(authority.get("stageB"), "authority.stageB").get("expectedExampleCount"),
        "authority.stageB.expectedExampleCount",
        minimum=1,
    )
    expected_duration = _integer(
        _mapping(authority.get("stageB"), "authority.stageB").get("expectedExampleDurationMilliseconds"),
        "authority.stageB.expectedExampleDurationMilliseconds",
        minimum=1,
    )
    if len(raw_examples) != expected_count:
        raise BeatCellReadinessError("Examples changed the exact Stage-1 E count.")
    duration = math.fsum(
        _integer(_mapping(row, "example").get("durationMilliseconds"), "example.durationMilliseconds", minimum=1)
        for row in raw_examples
    )
    if duration != expected_duration:
        raise BeatCellReadinessError("Examples changed the exact Stage-1 E duration in canonical milliseconds.")
    return deepcopy(dict(examples)), [str(name) for name in feature_names]


def _label_audit_row(
    examples: Sequence[Mapping[str, Any]],
    *,
    scope: str,
    dataset_id: str | None,
    guitarset_role: str | None,
    source_funnel_sha256: str,
) -> dict[str, Any]:
    correct = [row for row in examples if row["correct"] is True]
    incorrect = [row for row in examples if row["correct"] is False]
    payload = {
        "scope": scope,
        "datasetId": dataset_id,
        "guitarsetRole": guitarset_role,
        "trackCount": len({str(row["trackId"]) for row in examples}),
        "exampleCount": len(examples),
        "correctCount": len(correct),
        "incorrectCount": len(incorrect),
        "exampleDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in examples),
        "correctDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in correct),
        "incorrectDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in incorrect),
        "sourceFunnelSha256": _sha256(source_funnel_sha256, "source funnel sha256"),
    }
    return {**payload, "rowSha256": canonical_sha256(payload)}


def _expected_label_audits(example_rows: Sequence[Mapping[str, Any]], stage1: Mapping[str, Any]) -> dict[str, Any]:
    aggregate_funnel = _mapping(stage1.get("aggregate"), "Stage-1 aggregate")
    aggregate = _label_audit_row(
        example_rows,
        scope="aggregate",
        dataset_id=None,
        guitarset_role=None,
        source_funnel_sha256=str(aggregate_funnel["funnelSha256"]),
    )
    stage1_datasets = {
        str(_mapping(row, "Stage-1 dataset")["datasetId"]): _mapping(row, "Stage-1 dataset")
        for row in _sequence(stage1.get("datasets"), "Stage-1 datasets")
    }
    datasets = []
    for dataset_id in DATASET_IDS:
        source = stage1_datasets[dataset_id]
        subset = [row for row in example_rows if row["datasetId"] == dataset_id]
        datasets.append(
            _label_audit_row(
                subset,
                scope="dataset",
                dataset_id=dataset_id,
                guitarset_role=None,
                source_funnel_sha256=str(source["funnelSha256"]),
            )
        )
    guitar_source = _mapping(stage1.get("guitarset"), "Stage-1 GuitarSet")
    guitar_examples = [row for row in example_rows if row["datasetId"] == "guitarset"]
    guitar_aggregate = _label_audit_row(
        guitar_examples,
        scope="guitarset",
        dataset_id="guitarset",
        guitarset_role=None,
        source_funnel_sha256=str(guitar_source["funnelSha256"]),
    )
    stage1_roles = {
        str(_mapping(row, "Stage-1 GuitarSet role")["guitarsetRole"]): _mapping(row, "Stage-1 GuitarSet role")
        for row in _sequence(guitar_source.get("compSolo"), "Stage-1 GuitarSet compSolo")
    }
    roles = []
    for role in GUITARSET_ROLES:
        subset = [row for row in guitar_examples if row["guitarsetRole"] == role]
        roles.append(
            _label_audit_row(
                subset,
                scope="guitarsetRole",
                dataset_id="guitarset",
                guitarset_role=role,
                source_funnel_sha256=str(stage1_roles[role]["funnelSha256"]),
            )
        )
    guitar_payload = {
        "aggregate": guitar_aggregate,
        "roles": roles,
        "roleSetSha256": canonical_sha256(roles),
    }
    guitarset = {**guitar_payload, "rowSha256": canonical_sha256(guitar_payload)}
    payload = {
        "schemaVersion": BEAT_CELL_LABEL_AUDITS_SCHEMA,
        "aggregate": aggregate,
        "datasets": datasets,
        "datasetSetSha256": canonical_sha256(datasets),
        "guitarset": guitarset,
    }
    return {**payload, "auditSha256": canonical_sha256(payload)}


def _crosscheck_examples_stage1(
    examples: Mapping[str, Any],
    stage1: Mapping[str, Any],
    stage1_admission: Mapping[str, Any],
) -> None:
    """Bind each C/I example to its exact Stage-1 outcome and track row."""

    tracks: dict[str, Mapping[str, Any]] = {}
    outcomes: dict[tuple[str, int], tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    eligible_keys: set[tuple[str, int]] = set()
    for raw_track in _sequence(stage1.get("tracks"), "Stage-1 tracks"):
        track = _mapping(raw_track, "Stage-1 track")
        track_id = _string(track.get("trackId"), "Stage-1 track.trackId")
        if track_id in tracks:
            raise BeatCellReadinessError("Stage-1 tracks contain a duplicate trackId.")
        tracks[track_id] = track
        for raw_outcome in _sequence(track.get("cellOutcomes"), f"Stage-1 track {track_id}.cellOutcomes"):
            outcome = _mapping(raw_outcome, f"Stage-1 track {track_id} outcome")
            cell_index = _integer(outcome.get("cellIndex"), "Stage-1 outcome.cellIndex")
            key = (track_id, cell_index)
            if key in outcomes:
                raise BeatCellReadinessError("Stage-1 contains a duplicate logical outcome key.")
            outcomes[key] = (track, outcome)
            if outcome.get("classification") in {"C", "I"}:
                eligible_keys.add(key)
    observed_keys: set[tuple[str, int]] = set()
    example_rows = [
        _mapping(raw, f"examples.examples[{index}]")
        for index, raw in enumerate(_sequence(examples.get("examples"), "examples.examples"))
    ]
    for example in example_rows:
        track_id = _string(example.get("trackId"), "example.trackId")
        cell_index = _integer(example.get("cellIndex"), "example.cellIndex")
        key = (track_id, cell_index)
        source = outcomes.get(key)
        if key in observed_keys or source is None:
            raise BeatCellReadinessError("An example does not join exactly once to a Stage-1 outcome.")
        observed_keys.add(key)
        track, outcome = source
        classification = outcome.get("classification")
        if classification not in {"C", "I"}:
            raise BeatCellReadinessError("Examples may contain only exact Stage-1 C/I outcomes.")
        prediction_identity = _mapping(track.get("predictionIdentity"), "Stage-1 predictionIdentity")
        expected_correct = classification == "C"
        if (
            example.get("stage1ArtifactSha256") != stage1.get("artifactSha256")
            or example.get("stage1OutcomeRowSha256") != outcome.get("rowSha256")
            or example.get("durationMilliseconds") != outcome.get("durationMilliseconds")
            or example.get("sourceBeatCellSha256") != outcome.get("sourceBeatCellSha256")
            or example.get("correct") is not expected_correct
            or example.get("datasetId") != track.get("datasetId")
            or example.get("role") != track.get("role")
            or example.get("guitarsetRole") != track.get("guitarsetRole")
            or example.get("confidenceGroupId") != track.get("confidenceGroupId")
            or example.get("sourceGroupTrackRowSha256") != track.get("sourceGroupTrackMetadataSha256")
            or example.get("predictionIdentitySha256") != track.get("predictionIdentitySha256")
            or example.get("audioLineageRowSha256") != prediction_identity.get("audioLineageRowSha256")
        ):
            raise BeatCellReadinessError(
                "An example was spliced across Stage-1 outcome, duration, beat, label, track, role, or group identity."
            )
    if observed_keys != eligible_keys:
        raise BeatCellReadinessError("Examples do not cover every and only Stage-1 C/I logical outcome.")

    expected_audits = _expected_label_audits(example_rows, stage1)
    if (
        examples.get("labelAudits") != expected_audits
        or examples.get("labelAuditsSha256") != expected_audits["auditSha256"]
    ):
        raise BeatCellReadinessError(
            "Examples labelAudits changed Stage-1 funnel hashes, scope semantics, counts, or durations."
        )
    if examples.get("referenceEndpointReconciliationAudit") != stage1_admission.get(
        "referenceEndpointReconciliationAudit"
    ) or examples.get("referenceEndpointReconciliationAuditSha256") != stage1_admission.get(
        "referenceEndpointReconciliationAuditSha256"
    ):
        raise BeatCellReadinessError("Examples endpoint reconciliation audit is not the admitted Stage-1 audit.")


def _validate_selector_and_reproduce(examples: Mapping[str, Any], selector: Mapping[str, Any]) -> dict[str, Any]:
    if selector.get("schemaVersion") != BEAT_CELL_SELECTOR_SCHEMA:
        raise BeatCellReadinessError("Selector uses an unsupported beat-cell schemaVersion.")
    try:
        validate_beat_cell_selector_artifact(selector, examples)
    except Exception as error:
        raise BeatCellReadinessError("The one sealed beat-cell selector failed validation.") from error

    # This is the only trainer call in this module.  It is a byte-identity
    # reproduction proof, not another candidate or another evaluation.
    try:
        reproduced = train_beat_cell_selector(deepcopy(dict(examples)))
    except Exception as error:
        raise BeatCellReadinessError("The exactly one readiness reproduction refit failed.") from error
    if reproduced != dict(selector):
        raise BeatCellReadinessError("The readiness reproduction refit was not object-identical.")
    if canonical_sha256(reproduced) != canonical_sha256(selector):
        raise BeatCellReadinessError("The readiness reproduction refit was not canonically identical.")
    if _render_json(reproduced) != _render_json(selector):
        raise BeatCellReadinessError("The readiness reproduction refit was not byte-identical.")
    payload = {
        "selectorArtifactValidationPassed": True,
        "readinessReproductionRefitCount": 1,
        "freshTrainingObjectEqual": True,
        "freshTrainingCanonicalEqual": True,
        "freshTrainingByteEqual": True,
        "reproducedSelectorSha256": _sha256(selector.get("artifactSha256"), "selector.artifactSha256"),
        "isAnotherCandidate": False,
        "sameCycleRetryAllowed": False,
    }
    return {**payload, "reproductionSha256": canonical_sha256(payload)}


def _feature_vector(
    example: Mapping[str, Any], feature_names: Sequence[str], example_key: str
) -> list[int | float | None]:
    values = _mapping(example.get("featureValues"), f"example {example_key} featureValues")
    if set(values) != set(feature_names) or len(values) != len(feature_names):
        raise BeatCellReadinessError("Example featureValues changed the exact feature-name key set.")
    if canonical_sha256(values) != example.get("featureValuesSha256"):
        raise BeatCellReadinessError("Example featureValuesSha256 is stale.")
    _validate_feature_value_types(values, feature_names, f"example {example_key}")
    output: list[int | float | None] = []
    # JSON object rendering is canonically key-sorted.  Estimator order comes
    # only from the separately sealed featureNames array.
    for name in feature_names:
        raw = values[name]
        if raw is not None:
            _finite(raw, f"example {example_key} feature {name}")
        output.append(raw)
    return output


def _validate_feature_value_types(
    values: Mapping[str, Any],
    feature_names: Sequence[str],
    name: str,
) -> None:
    """Preserve the exact sealed JSON numeric wire types, not only numeric values."""

    if not INTEGER_FEATURE_NAMES.issubset(feature_names):
        raise BeatCellReadinessError("The exact integer-valued feature inventory changed.")
    for feature_name in feature_names:
        value = values[feature_name]
        if feature_name in INTEGER_COUNT_FEATURE_NAMES:
            if type(value) is not int or value < 0:
                raise BeatCellReadinessError(f"{name} feature {feature_name} must remain a nonnegative JSON integer.")
        elif feature_name in INTEGER_FLAG_FEATURE_NAMES:
            if type(value) is not int or value not in (0, 1):
                raise BeatCellReadinessError(f"{name} feature {feature_name} must remain a JSON integer flag.")
        elif value is not None and type(value) is not float:
            raise BeatCellReadinessError(f"{name} feature {feature_name} must remain a JSON float or null.")


def _join_oof_rows(
    examples: Mapping[str, Any], selector: Mapping[str, Any], feature_names: Sequence[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    example_by_key: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(_sequence(examples.get("examples"), "examples.examples")):
        example = _mapping(raw, f"examples.examples[{index}]")
        key = _sha256(example.get("exampleKey"), f"examples.examples[{index}].exampleKey")
        if key in example_by_key:
            raise BeatCellReadinessError("Examples contain a duplicate exampleKey.")
        example_by_key[key] = example

    training = _mapping(selector.get("training"), "selector.training")
    raw_oof = _sequence(training.get("oofAuditRows"), "selector.training.oofAuditRows")
    if len(raw_oof) != len(example_by_key):
        raise BeatCellReadinessError("OOF row count differs from the exact examples join.")
    joined: list[dict[str, Any]] = []
    seen: set[str] = set()
    folds_by_group: dict[str, set[int]] = defaultdict(set)
    weights_by_group: dict[str, list[float]] = defaultdict(list)
    logical_keys: set[tuple[str, int]] = set()
    for index, raw in enumerate(raw_oof):
        oof = _mapping(raw, f"selector.training.oofAuditRows[{index}]")
        key = _sha256(oof.get("exampleKey"), f"OOF row {index} exampleKey")
        if key in seen or key not in example_by_key:
            raise BeatCellReadinessError("Each OOF exampleKey must join exactly once.")
        seen.add(key)
        example = example_by_key[key]
        track_id = _string(example.get("trackId"), f"example {key}.trackId")
        cell_index = _integer(example.get("cellIndex"), f"example {key}.cellIndex")
        logical_key = (track_id, cell_index)
        if logical_key in logical_keys:
            raise BeatCellReadinessError("Eligible examples contain a duplicate logical track/cell key.")
        logical_keys.add(logical_key)
        duration = _integer(example.get("durationMilliseconds"), f"example {key}.durationMilliseconds", minimum=1)
        dataset_id = _string(example.get("datasetId"), f"example {key}.datasetId")
        role = _string(example.get("role"), f"example {key}.role")
        guitarset_role = example.get("guitarsetRole")
        if guitarset_role is not None:
            guitarset_role = _string(guitarset_role, f"example {key}.guitarsetRole")
        group = _string(example.get("confidenceGroupId"), f"example {key}.confidenceGroupId")
        correct = example.get("correct")
        if not isinstance(correct, bool):
            raise BeatCellReadinessError("Example correctness must be boolean.")
        if (
            oof.get("trackId") != track_id
            or oof.get("cellIndex") != cell_index
            or oof.get("durationMilliseconds") != duration
            or oof.get("datasetId") != dataset_id
            or oof.get("role") != role
            or oof.get("guitarsetRole") != guitarset_role
            or oof.get("confidenceGroupId") != group
            or oof.get("correct") is not correct
        ):
            raise BeatCellReadinessError("OOF/example duration, outcome, dataset, role, or group metadata disagree.")
        if dataset_id not in DATASET_IDS:
            raise BeatCellReadinessError("OOF rows changed the exact certification dataset set.")
        if (dataset_id == "guitarset") != (guitarset_role in GUITARSET_ROLES):
            raise BeatCellReadinessError("GuitarSet role metadata is missing or leaked outside GuitarSet.")
        fold = _integer(oof.get("outerFold"), f"OOF row {key}.outerFold")
        if fold >= OUTER_FOLD_COUNT:
            raise BeatCellReadinessError("OOF outerFold is outside the frozen five-fold range.")
        probability = _finite(oof.get("probability"), f"OOF row {key}.probability")
        sample_weight = _finite(oof.get("sampleWeight"), f"OOF row {key}.sampleWeight")
        if not 0 <= probability <= 1 or sample_weight <= 0:
            raise BeatCellReadinessError("OOF probability or sampleWeight is outside its valid range.")
        folds_by_group[group].add(fold)
        weights_by_group[group].append(sample_weight)
        joined.append(
            {
                "exampleKey": key,
                "exampleSha256": _sha256(example.get("exampleSha256"), f"example {key}.exampleSha256"),
                "trackId": track_id,
                "cellIndex": cell_index,
                "durationMilliseconds": duration,
                "datasetId": dataset_id,
                "role": role,
                "guitarsetRole": guitarset_role,
                "confidenceGroupId": group,
                "outerFold": fold,
                "probability": probability,
                "correct": correct,
                "sampleWeight": sample_weight,
                "features": _feature_vector(example, feature_names, key),
                "featureValuesSha256": _sha256(
                    example.get("featureValuesSha256"), f"example {key}.featureValuesSha256"
                ),
                "sourceBeatCellSha256": _sha256(
                    example.get("sourceBeatCellSha256"), f"example {key}.sourceBeatCellSha256"
                ),
                "stage1OutcomeRowSha256": _sha256(
                    example.get("stage1OutcomeRowSha256"), f"example {key}.stage1OutcomeRowSha256"
                ),
                "sourceGroupTrackRowSha256": _sha256(
                    example.get("sourceGroupTrackRowSha256"), f"example {key}.sourceGroupTrackRowSha256"
                ),
                "predictionIdentitySha256": _sha256(
                    example.get("predictionIdentitySha256"), f"example {key}.predictionIdentitySha256"
                ),
                "audioLineageRowSha256": _sha256(
                    example.get("audioLineageRowSha256"), f"example {key}.audioLineageRowSha256"
                ),
            }
        )
    if seen != set(example_by_key):
        raise BeatCellReadinessError("Examples and OOF rows do not form an exact one-to-one key set.")
    for group, folds in folds_by_group.items():
        if len(folds) != 1:
            raise BeatCellReadinessError(f"Confidence group {group!r} crosses outer folds.")
        if not math.isclose(math.fsum(weights_by_group[group]), 1.0, rel_tol=0, abs_tol=1e-12):
            raise BeatCellReadinessError(f"Confidence group {group!r} does not have total OOF weight one.")
    joined.sort(key=lambda row: row["exampleKey"])
    public_rows: list[dict[str, Any]] = []
    for row in joined:
        payload = {
            "schemaVersion": BEAT_CELL_READINESS_JOINED_ROW_SCHEMA,
            "exampleKey": row["exampleKey"],
            "exampleSha256": row["exampleSha256"],
            "trackId": row["trackId"],
            "cellIndex": row["cellIndex"],
            "durationMilliseconds": row["durationMilliseconds"],
            "datasetId": row["datasetId"],
            "role": row["role"],
            "guitarsetRole": row["guitarsetRole"],
            "confidenceGroupId": row["confidenceGroupId"],
            "outerFold": row["outerFold"],
            "probability": row["probability"],
            "correct": row["correct"],
            "sampleWeight": row["sampleWeight"],
            "featureValuesSha256": row["featureValuesSha256"],
            "orderedFeatureValues": deepcopy(row["features"]),
            "sourceBeatCellSha256": row["sourceBeatCellSha256"],
            "stage1OutcomeRowSha256": row["stage1OutcomeRowSha256"],
            "sourceGroupTrackRowSha256": row["sourceGroupTrackRowSha256"],
            "predictionIdentitySha256": row["predictionIdentitySha256"],
            "audioLineageRowSha256": row["audioLineageRowSha256"],
        }
        public_rows.append({**payload, "rowSha256": canonical_sha256(payload)})
    diagnostic_reasons: list[str] = []
    present_folds = {row["outerFold"] for row in joined}
    diagnostic_reasons.extend(
        f"diagnostics.outer-fold-{fold}-missing" for fold in range(OUTER_FOLD_COUNT) if fold not in present_folds
    )
    present_datasets = {row["datasetId"] for row in joined}
    diagnostic_reasons.extend(
        f"diagnostics.dataset-{dataset_id}-missing" for dataset_id in DATASET_IDS if dataset_id not in present_datasets
    )
    present_roles = {row["guitarsetRole"] for row in joined if row["datasetId"] == "guitarset"}
    diagnostic_reasons.extend(
        f"diagnostics.guitarset-{role}-role-missing" for role in GUITARSET_ROLES if role not in present_roles
    )
    return joined, public_rows, sorted(set(diagnostic_reasons))


def _stage1_strata(
    stage1_admission: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    datasets = {
        str(_mapping(row, "Stage-1 dataset row")["datasetId"]): _stratum_funnel(
            _mapping(row, "Stage-1 dataset row"), "Stage-1 dataset row"
        )
        for row in _sequence(stage1_admission.get("datasets"), "Stage-1 admission datasets")
    }
    guitar = _mapping(stage1_admission.get("guitarset"), "Stage-1 admission GuitarSet")
    roles = {
        str(_mapping(row, "Stage-1 role row")["guitarsetRole"]): _stratum_funnel(
            _mapping(row, "Stage-1 role row"), "Stage-1 role row"
        )
        for row in _sequence(guitar.get("compSolo"), "Stage-1 admission GuitarSet compSolo")
    }
    return datasets, roles


def _crosscheck_joined_stage1(rows: Sequence[Mapping[str, Any]], stage1_admission: Mapping[str, Any]) -> None:
    aggregate = _mapping(stage1_admission.get("aggregate"), "Stage-1 admission aggregate")
    expected_count = _funnel_measure(aggregate, "counts", "Stage-1 admission aggregate")
    expected_duration = _funnel_measure(aggregate, "durationMilliseconds", "Stage-1 admission aggregate")
    if (
        len(rows) != expected_count["E"]
        or sum(bool(row["correct"]) for row in rows) != expected_count["C"]
        or math.fsum(int(row["durationMilliseconds"]) for row in rows) != expected_duration["E"]
        or math.fsum(int(row["durationMilliseconds"]) for row in rows if row["correct"]) != expected_duration["C"]
    ):
        raise BeatCellReadinessError("Joined OOF rows do not reproduce aggregate Stage-1 E/C count and duration.")
    datasets, roles = _stage1_strata(stage1_admission)
    for dataset_id in DATASET_IDS:
        subset = [row for row in rows if row["datasetId"] == dataset_id]
        count = _funnel_measure(datasets[dataset_id], "counts", f"Stage-1 {dataset_id}")
        duration = _funnel_measure(datasets[dataset_id], "durationMilliseconds", f"Stage-1 {dataset_id}")
        if (
            len(subset) != count["E"]
            or sum(bool(row["correct"]) for row in subset) != count["C"]
            or sum(int(row["durationMilliseconds"]) for row in subset) != duration["E"]
            or sum(int(row["durationMilliseconds"]) for row in subset if row["correct"]) != duration["C"]
        ):
            raise BeatCellReadinessError(f"Joined OOF rows do not reproduce Stage-1 {dataset_id} E/C audits.")
    for role in GUITARSET_ROLES:
        subset = [row for row in rows if row["datasetId"] == "guitarset" and row["guitarsetRole"] == role]
        count = _funnel_measure(roles[role], "counts", f"Stage-1 GuitarSet {role}")
        duration = _funnel_measure(roles[role], "durationMilliseconds", f"Stage-1 GuitarSet {role}")
        if (
            len(subset) != count["E"]
            or sum(bool(row["correct"]) for row in subset) != count["C"]
            or sum(int(row["durationMilliseconds"]) for row in subset) != duration["E"]
            or sum(int(row["durationMilliseconds"]) for row in subset if row["correct"]) != duration["C"]
        ):
            raise BeatCellReadinessError(f"Joined OOF rows do not reproduce Stage-1 GuitarSet {role} audits.")


def _probability_blocks(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    order = sorted(range(len(rows)), key=lambda index: (-float(rows[index]["probability"]), rows[index]["exampleKey"]))
    grouped: list[dict[str, Any]] = []
    for index in order:
        row = rows[index]
        probability = float(row["probability"])
        if not grouped or probability != grouped[-1]["probability"]:
            grouped.append(
                {
                    "probability": probability,
                    "weights": [],
                    "correctWeights": [],
                    "exampleCount": 0,
                }
            )
        grouped[-1]["weights"].append(float(row["sampleWeight"]))
        grouped[-1]["correctWeights"].append(float(row["sampleWeight"]) * (1.0 if row["correct"] else 0.0))
        grouped[-1]["exampleCount"] += 1
    return [
        {
            "probability": block["probability"],
            "weight": math.fsum(block["weights"]),
            "correctWeight": math.fsum(block["correctWeights"]),
            "exampleCount": block["exampleCount"],
        }
        for block in grouped
    ]


def _block_prefixes(blocks: Sequence[Mapping[str, Any]]) -> tuple[float, list[tuple[float, float]]]:
    weights = [float(block["weight"]) for block in blocks]
    correct_weights = [float(block["correctWeight"]) for block in blocks]
    total = math.fsum(weights)
    if total <= 0:
        raise BeatCellReadinessError("Probability curves require positive total sampleWeight.")
    return total, [
        (math.fsum(weights[: index + 1]), math.fsum(correct_weights[: index + 1])) for index in range(len(blocks))
    ]


def _precision_coverage(rows: Sequence[Mapping[str, Any]], targets: Sequence[float]) -> list[dict[str, Any]]:
    blocks = _probability_blocks(rows)
    if not blocks:
        raise BeatCellReadinessError("Precision/coverage requires at least one OOF row.")
    total, prefixes = _block_prefixes(blocks)
    output: list[dict[str, Any]] = []
    for raw_target in targets:
        target = _finite(raw_target, "precision/coverage target")
        if not 0 < target <= 1:
            raise BeatCellReadinessError("Precision/coverage targets must lie in (0,1].")
        cumulative = prefixes[-1][0]
        correct = prefixes[-1][1]
        minimum_probability: float | None = None
        for block, (candidate_cumulative, candidate_correct) in zip(blocks, prefixes, strict=True):
            cumulative = candidate_cumulative
            correct = candidate_correct
            minimum_probability = float(block["probability"])
            # Exact parity with the committed selector core.  This epsilon is
            # only a target-crossing comparison; tie membership remains exact.
            if cumulative / total + 1e-15 >= target:
                break
        output.append(
            {
                "targetCoverage": target,
                "realizableCoverage": cumulative / total,
                "groupBalancedPrecision": correct / cumulative,
                "groupBalancedRisk": 1.0 - correct / cumulative,
                "minimumProbabilityAtDescriptivePoint": minimum_probability,
            }
        )
    return output


def _aurc(rows: Sequence[Mapping[str, Any]], *, group_weighted: bool) -> float | None:
    if not rows:
        return None
    weighted_rows = [{**row, "sampleWeight": float(row["sampleWeight"]) if group_weighted else 1.0} for row in rows]
    blocks = _probability_blocks(weighted_rows)
    total, prefixes = _block_prefixes(blocks)
    return math.fsum(
        float(block["weight"]) / total * ((weight - correct) / weight)
        for block, (weight, correct) in zip(blocks, prefixes, strict=True)
    )


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:  # pragma: no cover - project dependency
        raise RuntimeError("Beat-cell readiness requires NumPy.") from error
    return np


def _group_log_loss(rows: Sequence[Mapping[str, Any]]) -> float:
    np = _numpy()
    probabilities = np.asarray([float(row["probability"]) for row in rows], dtype=np.float64)
    labels = np.asarray([1.0 if row["correct"] else 0.0 for row in rows], dtype=np.float64)
    weights = np.asarray([float(row["sampleWeight"]) for row in rows], dtype=np.float64)
    if float(weights.sum()) <= 0:
        raise BeatCellReadinessError("Group-balanced log loss requires positive sampleWeight.")
    clipped = np.clip(probabilities, PROBABILITY_FLOOR, 1.0 - PROBABILITY_FLOOR)
    losses = -(labels * np.log(clipped) + (1.0 - labels) * np.log(1.0 - clipped))
    return float((weights * losses).sum() / weights.sum())


def _group_brier(rows: Sequence[Mapping[str, Any]]) -> float:
    np = _numpy()
    probabilities = np.asarray([float(row["probability"]) for row in rows], dtype=np.float64)
    labels = np.asarray([1.0 if row["correct"] else 0.0 for row in rows], dtype=np.float64)
    weights = np.asarray([float(row["sampleWeight"]) for row in rows], dtype=np.float64)
    if float(weights.sum()) <= 0:
        raise BeatCellReadinessError("Group-balanced Brier score requires positive sampleWeight.")
    return float((weights * (probabilities - labels) ** 2).sum() / weights.sum())


def _verify_stored_evaluation(
    selector: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], authority: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    stored = dict(_mapping(selector.get("outOfFoldEvaluation"), "selector.outOfFoldEvaluation"))
    targets = list(
        _sequence(
            _mapping(authority.get("selectorCore"), "authority.selectorCore").get("precisionCoverageTargets"),
            "authority.selectorCore.precisionCoverageTargets",
        )
    )
    curve = _precision_coverage(rows, targets)
    if stored.get("precisionCoverage") != curve:
        raise BeatCellReadinessError("Stored selector tie-block precision/coverage curve failed exact recomputation.")
    if stored.get("denominatorExampleCount") != len(rows):
        raise BeatCellReadinessError("Stored selector evaluation changed its exact OOF count denominator.")
    if "denominatorDurationMilliseconds" in stored and stored.get("denominatorDurationMilliseconds") != sum(
        int(row["durationMilliseconds"]) for row in rows
    ):
        raise BeatCellReadinessError("Stored selector evaluation changed its exact OOF duration disclosure.")
    points = [point for point in curve if point["targetCoverage"] == FIXED_TARGET_COVERAGE]
    if len(points) != 1:
        raise BeatCellReadinessError("Selector must contain exactly one targetCoverage=0.50 point.")
    point = deepcopy(points[0])
    cutoff = _finite(point.get("minimumProbabilityAtDescriptivePoint"), "fixed descriptive cutoff")
    if not 0 <= cutoff <= 1:
        raise BeatCellReadinessError("Fixed descriptive cutoff lies outside [0,1].")
    recomputed = {
        "denominatorExampleCount": len(rows),
        "denominatorDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in rows),
        "groupBalancedLogLoss": _group_log_loss(rows),
        "groupBalancedBrierScore": _group_brier(rows),
        "groupBalancedAreaUnderRiskCoverage": _aurc(rows, group_weighted=True),
        "precisionCoverage": curve,
    }
    for field in (
        "groupBalancedLogLoss",
        "groupBalancedBrierScore",
        "groupBalancedAreaUnderRiskCoverage",
    ):
        if stored.get(field) != recomputed[field]:
            raise BeatCellReadinessError(f"Stored selector {field} failed exact joined-row recomputation.")
    return stored, recomputed, point


def _wilson_lower(correct: int, total: int) -> float | None:
    if total <= 0:
        return None
    proportion = correct / total
    z_squared = WILSON_ONE_SIDED_Z_95**2
    denominator = 1.0 + z_squared / total
    center = (proportion + z_squared / (2.0 * total)) / denominator
    half_width = (
        WILSON_ONE_SIDED_Z_95
        * math.sqrt(proportion * (1.0 - proportion) / total + z_squared / (4.0 * total * total))
        / denominator
    )
    return max(0.0, center - half_width)


def _slice_metrics(
    slice_id: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    reference_determinate_count: int | None,
    reference_determinate_duration_milliseconds: int | None,
) -> dict[str, Any]:
    accepted = [row for row in rows if row["accepted"]]
    accepted_correct = [row for row in accepted if row["correct"]]
    emitted_duration = sum(int(row["durationMilliseconds"]) for row in rows)
    accepted_duration = sum(int(row["durationMilliseconds"]) for row in accepted)
    accepted_correct_duration = sum(int(row["durationMilliseconds"]) for row in accepted_correct)
    emitted_weight = math.fsum(float(row["sampleWeight"]) for row in rows)
    accepted_weight = math.fsum(float(row["sampleWeight"]) for row in accepted)
    accepted_correct_weight = math.fsum(float(row["sampleWeight"]) for row in accepted_correct)
    has_end_to_end = reference_determinate_count is not None and reference_determinate_duration_milliseconds is not None
    if has_end_to_end and (reference_determinate_count <= 0 or reference_determinate_duration_milliseconds <= 0):
        raise BeatCellReadinessError("A declared end-to-end denominator must have positive count and duration.")
    return {
        "sliceId": slice_id,
        "emittedExampleCount": len(rows),
        "emittedDurationMilliseconds": emitted_duration,
        "acceptedCount": len(accepted),
        "acceptedCorrectCount": len(accepted_correct),
        "acceptedDurationMilliseconds": accepted_duration,
        "acceptedCorrectDurationMilliseconds": accepted_correct_duration,
        "empiricalPrecision": _ratio(len(accepted_correct), len(accepted)),
        "durationWeightedPrecision": _ratio(accepted_correct_duration, accepted_duration),
        "conditionalCoverage": _ratio(len(accepted), len(rows)),
        "durationConditionalCoverage": _ratio(accepted_duration, emitted_duration),
        "groupBalancedConditionalCoverage": _ratio(accepted_weight, emitted_weight),
        "groupBalancedPrecision": _ratio(accepted_correct_weight, accepted_weight),
        "endToEndCoverageAvailable": has_end_to_end,
        "referenceDeterminateCount": reference_determinate_count,
        "referenceDeterminateDurationMilliseconds": reference_determinate_duration_milliseconds,
        "endToEndCoverage": (
            _ratio(len(accepted), reference_determinate_count) if reference_determinate_count is not None else None
        ),
        "durationEndToEndCoverage": (
            _ratio(accepted_duration, reference_determinate_duration_milliseconds)
            if reference_determinate_duration_milliseconds is not None
            else None
        ),
        "endToEndCoverageUnavailableReason": (
            None if has_end_to_end else "no exact Stage-1 count-and-duration denominator for this diagnostic slice"
        ),
        "oneSidedWilson95LowerBound": _wilson_lower(len(accepted_correct), len(accepted)),
        "durationWilsonBound": None,
    }


def _integer_min_gate(gate_id: str, observed: int, required: int) -> dict[str, Any]:
    return {
        "gateId": gate_id,
        "kind": "integer-minimum",
        "observed": observed,
        "operator": ">=",
        "required": required,
        "passed": observed >= required,
    }


def _integer_ratio_gate(
    gate_id: str,
    *,
    numerator_name: str,
    numerator: int,
    denominator_name: str,
    denominator: int,
    required_numerator: int,
    required_denominator: int,
) -> dict[str, Any]:
    left = required_denominator * numerator
    right = required_numerator * denominator
    passed = denominator > 0 and left >= right
    return {
        "gateId": gate_id,
        "kind": "exact-integer-ratio",
        "ratio": f"{numerator_name}/{denominator_name}",
        "numerator": numerator,
        "denominator": denominator,
        "requiredNumerator": required_numerator,
        "requiredDenominator": required_denominator,
        "leftCrossProduct": left,
        "rightCrossProduct": right,
        "operator": ">=",
        "passed": passed,
    }


def _numeric_gate(gate_id: str, observed: float | None, required: float) -> dict[str, Any]:
    return {
        "gateId": gate_id,
        "kind": "finite-numeric-minimum",
        "observed": observed,
        "operator": ">=",
        "required": required,
        "passed": observed is not None and math.isfinite(observed) and observed >= required,
    }


def _build_readiness_gates(aggregate: Mapping[str, Any], guitarset: Mapping[str, Any]) -> list[dict[str, Any]]:
    aggregate_a = _integer(aggregate.get("acceptedCount"), "aggregate.acceptedCount")
    aggregate_ca = _integer(aggregate.get("acceptedCorrectCount"), "aggregate.acceptedCorrectCount")
    aggregate_r = _integer(aggregate.get("referenceDeterminateCount"), "aggregate.referenceDeterminateCount", minimum=1)
    aggregate_a_ms = _integer(aggregate.get("acceptedDurationMilliseconds"), "aggregate.acceptedDurationMilliseconds")
    aggregate_ca_ms = _integer(
        aggregate.get("acceptedCorrectDurationMilliseconds"),
        "aggregate.acceptedCorrectDurationMilliseconds",
    )
    aggregate_r_ms = _integer(
        aggregate.get("referenceDeterminateDurationMilliseconds"),
        "aggregate.referenceDeterminateDurationMilliseconds",
        minimum=1,
    )
    guitar_a = _integer(guitarset.get("acceptedCount"), "guitarset.acceptedCount")
    guitar_ca = _integer(guitarset.get("acceptedCorrectCount"), "guitarset.acceptedCorrectCount")
    guitar_r = _integer(guitarset.get("referenceDeterminateCount"), "guitarset.referenceDeterminateCount", minimum=1)
    guitar_a_ms = _integer(guitarset.get("acceptedDurationMilliseconds"), "guitarset.acceptedDurationMilliseconds")
    guitar_ca_ms = _integer(
        guitarset.get("acceptedCorrectDurationMilliseconds"),
        "guitarset.acceptedCorrectDurationMilliseconds",
    )
    guitar_r_ms = _integer(
        guitarset.get("referenceDeterminateDurationMilliseconds"),
        "guitarset.referenceDeterminateDurationMilliseconds",
        minimum=1,
    )
    gates = [
        _integer_min_gate("aggregate.accepted-count", aggregate_a, 150),
        _integer_ratio_gate(
            "aggregate.end-to-end-micro-coverage",
            numerator_name="A",
            numerator=aggregate_a,
            denominator_name="R",
            denominator=aggregate_r,
            required_numerator=1,
            required_denominator=2,
        ),
        _integer_ratio_gate(
            "aggregate.micro-precision",
            numerator_name="CA",
            numerator=aggregate_ca,
            denominator_name="A",
            denominator=aggregate_a,
            required_numerator=49,
            required_denominator=50,
        ),
        _numeric_gate(
            "aggregate.one-sided-wilson95-lower-bound",
            aggregate.get("oneSidedWilson95LowerBound"),
            0.98,
        ),
        _numeric_gate(
            "aggregate.group-balanced-conditional-coverage",
            aggregate.get("groupBalancedConditionalCoverage"),
            0.50,
        ),
        _numeric_gate("aggregate.group-balanced-precision", aggregate.get("groupBalancedPrecision"), 0.98),
        _integer_min_gate("guitarset.accepted-count", guitar_a, 30),
        _integer_ratio_gate(
            "guitarset.end-to-end-micro-coverage",
            numerator_name="A_G",
            numerator=guitar_a,
            denominator_name="R_G",
            denominator=guitar_r,
            required_numerator=1,
            required_denominator=4,
        ),
        _integer_ratio_gate(
            "guitarset.micro-precision",
            numerator_name="CA_G",
            numerator=guitar_ca,
            denominator_name="A_G",
            denominator=guitar_a,
            required_numerator=49,
            required_denominator=50,
        ),
        _numeric_gate(
            "guitarset.group-balanced-conditional-coverage",
            guitarset.get("groupBalancedConditionalCoverage"),
            0.25,
        ),
        _numeric_gate("guitarset.group-balanced-precision", guitarset.get("groupBalancedPrecision"), 0.98),
        _integer_ratio_gate(
            "aggregate.duration-end-to-end-coverage",
            numerator_name="A_ms",
            numerator=aggregate_a_ms,
            denominator_name="R_ms",
            denominator=aggregate_r_ms,
            required_numerator=1,
            required_denominator=2,
        ),
        _integer_ratio_gate(
            "aggregate.duration-micro-precision",
            numerator_name="CA_ms",
            numerator=aggregate_ca_ms,
            denominator_name="A_ms",
            denominator=aggregate_a_ms,
            required_numerator=49,
            required_denominator=50,
        ),
        _integer_ratio_gate(
            "guitarset.duration-end-to-end-coverage",
            numerator_name="A_G_ms",
            numerator=guitar_a_ms,
            denominator_name="R_G_ms",
            denominator=guitar_r_ms,
            required_numerator=1,
            required_denominator=4,
        ),
        _integer_ratio_gate(
            "guitarset.duration-micro-precision",
            numerator_name="CA_G_ms",
            numerator=guitar_ca_ms,
            denominator_name="A_G_ms",
            denominator=guitar_a_ms,
            required_numerator=49,
            required_denominator=50,
        ),
    ]
    if [gate["gateId"] for gate in gates] != [*_COUNT_GATE_IDS, *_DURATION_GATE_IDS]:
        raise BeatCellReadinessError("Internal readiness gate order drifted.")
    return gates


def _quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise BeatCellReadinessError("Cannot compute a required quantile from an empty sample.")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * quantile
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _quantile_report(values: Sequence[float], quantiles: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"status": "no-observations", "count": 0, "quantiles": []}
    return {
        "status": "observed",
        "count": len(values),
        "quantiles": [{"quantile": quantile, "value": _quantile(values, quantile)} for quantile in quantiles],
    }


def _micro_log_loss(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    return math.fsum(
        -math.log(
            min(
                1.0 - PROBABILITY_FLOOR,
                max(
                    PROBABILITY_FLOOR,
                    float(row["probability"]) if row["correct"] else 1.0 - float(row["probability"]),
                ),
            )
        )
        for row in rows
    ) / len(rows)


def _micro_brier(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    return math.fsum((float(row["probability"]) - (1.0 if row["correct"] else 0.0)) ** 2 for row in rows) / len(rows)


def _reliability(rows: Sequence[Mapping[str, Any]], *, group_weighted: bool) -> dict[str, Any]:
    bins: list[list[Mapping[str, Any]]] = [[] for _ in range(RELIABILITY_BIN_COUNT)]
    for row in rows:
        index = min(int(float(row["probability"]) * RELIABILITY_BIN_COUNT), RELIABILITY_BIN_COUNT - 1)
        bins[index].append(row)
    total_weight = math.fsum(float(row["sampleWeight"] if group_weighted else 1.0) for row in rows)
    if total_weight <= 0:
        raise BeatCellReadinessError("Reliability requires positive support.")
    output: list[dict[str, Any]] = []
    ece = 0.0
    for index, members in enumerate(bins):
        weights = [float(row["sampleWeight"] if group_weighted else 1.0) for row in members]
        weight = math.fsum(weights)
        if weight > 0:
            mean_probability = (
                math.fsum(
                    member_weight * float(row["probability"])
                    for member_weight, row in zip(weights, members, strict=True)
                )
                / weight
            )
            empirical_correctness = (
                math.fsum(
                    member_weight * (1.0 if row["correct"] else 0.0)
                    for member_weight, row in zip(weights, members, strict=True)
                )
                / weight
            )
            ece += weight / total_weight * abs(mean_probability - empirical_correctness)
            status = "observed"
        else:
            mean_probability = None
            empirical_correctness = None
            status = "empty-fixed-bin"
        output.append(
            {
                "binIndex": index,
                "lowerInclusive": index / RELIABILITY_BIN_COUNT,
                "upperExclusive": (None if index == RELIABILITY_BIN_COUNT - 1 else (index + 1) / RELIABILITY_BIN_COUNT),
                "includesProbabilityOne": index == RELIABILITY_BIN_COUNT - 1,
                "status": status,
                "exampleCount": len(members),
                "weight": weight,
                "meanPredictedProbability": mean_probability,
                "empiricalCorrectness": empirical_correctness,
            }
        )
    return {
        "weighting": "sealed-one-per-confidence-group" if group_weighted else "micro-one-per-example",
        "expectedCalibrationError": ece,
        "bins": output,
    }


def _group_concentration(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["accepted"]]
    counts: dict[str, int] = defaultdict(int)
    weighted_mass: dict[str, float] = defaultdict(float)
    for row in accepted:
        group = str(row["confidenceGroupId"])
        counts[group] += 1
        weighted_mass[group] += float(row["sampleWeight"])
    if not accepted:
        return {
            "status": "no-accepted-examples",
            "acceptedCount": 0,
            "uniqueAcceptedGroupCount": 0,
            "maximumMicroAcceptedShare": None,
            "effectiveMicroGroupCount": None,
            "maximumGroupWeightedAcceptedShare": None,
            "effectiveGroupWeightedGroupCount": None,
        }
    micro_shares = [count / len(accepted) for count in counts.values()]
    total_weight = math.fsum(weighted_mass.values())
    weighted_shares = [mass / total_weight for mass in weighted_mass.values()]
    return {
        "status": "observed",
        "acceptedCount": len(accepted),
        "uniqueAcceptedGroupCount": len(counts),
        "maximumMicroAcceptedShare": max(micro_shares),
        "effectiveMicroGroupCount": 1.0 / math.fsum(share * share for share in micro_shares),
        "maximumGroupWeightedAcceptedShare": max(weighted_shares),
        "effectiveGroupWeightedGroupCount": 1.0 / math.fsum(share * share for share in weighted_shares),
    }


def _feature_diagnostics(
    rows: Sequence[Mapping[str, Any]], selector: Mapping[str, Any], feature_names: Sequence[str]
) -> dict[str, Any]:
    estimator = _mapping(selector.get("estimator"), "selector.estimator")
    imputation = list(_sequence(estimator.get("imputationValues"), "selector.estimator.imputationValues"))
    center = list(_sequence(estimator.get("center"), "selector.estimator.center"))
    scale = list(_sequence(estimator.get("scale"), "selector.estimator.scale"))
    if not (len(imputation) == len(center) == len(scale) == len(feature_names)):
        raise BeatCellReadinessError("Final estimator preprocessing arrays have the wrong feature dimension.")
    imputation_values = [_finite(value, "estimator imputation") for value in imputation]
    center_values = [_finite(value, "estimator center") for value in center]
    scale_values = [_finite(value, "estimator scale") for value in scale]
    if any(value <= 0 for value in scale_values):
        raise BeatCellReadinessError("Final estimator scale must be strictly positive.")
    declared_all_missing = list(
        _sequence(estimator.get("allMissingFeatureNames"), "selector.estimator.allMissingFeatureNames")
    )
    missingness: list[dict[str, Any]] = []
    standardized: list[dict[str, Any]] = []
    all_absolute_z: list[float] = []
    actual_all_missing: list[str] = []
    for feature_index, feature_name in enumerate(feature_names):
        raw_values = [row["features"][feature_index] for row in rows]
        missing_count = sum(value is None for value in raw_values)
        all_missing = missing_count == len(rows)
        if all_missing:
            actual_all_missing.append(feature_name)
        missingness.append(
            {
                "featureName": feature_name,
                "missingCount": missing_count,
                "missingRate": missing_count / len(rows),
                "allMissing": all_missing,
                "estimatorDeclaredAllMissing": feature_name in declared_all_missing,
            }
        )
        absolute_z = [
            abs(
                ((imputation_values[feature_index] if value is None else float(value)) - center_values[feature_index])
                / scale_values[feature_index]
            )
            for value in raw_values
        ]
        if any(not math.isfinite(value) for value in absolute_z):
            raise BeatCellReadinessError("Standardized feature diagnostics produced a non-finite value.")
        all_absolute_z.extend(absolute_z)
        standardized.append(
            {
                "featureName": feature_name,
                "count": len(absolute_z),
                "absoluteZQuantiles": _quantile_report(absolute_z, ABSOLUTE_Z_QUANTILES)["quantiles"],
                "fractionAbove3": sum(value > 3.0 for value in absolute_z) / len(absolute_z),
                "fractionAbove5": sum(value > 5.0 for value in absolute_z) / len(absolute_z),
            }
        )
    if declared_all_missing != actual_all_missing:
        raise BeatCellReadinessError("Estimator allMissingFeatureNames disagrees with the exact examples matrix.")
    return {
        "numericDriftPolicy": "disclosure-only; no numeric readiness cutoff",
        "featureMissingness": missingness,
        "standardizedAbsoluteZ": {
            "preprocessing": "final all-development refit imputation, center, and scale",
            "aggregate": {
                "count": len(all_absolute_z),
                "absoluteZQuantiles": _quantile_report(all_absolute_z, ABSOLUTE_Z_QUANTILES)["quantiles"],
                "fractionAbove3": sum(value > 3.0 for value in all_absolute_z) / len(all_absolute_z),
                "fractionAbove5": sum(value > 5.0 for value in all_absolute_z) / len(all_absolute_z),
            },
            "byFeature": standardized,
        },
    }


def _build_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    selector: Mapping[str, Any],
    feature_names: Sequence[str],
    stage1_admission: Mapping[str, Any],
    precision_coverage: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    datasets, roles = _stage1_strata(stage1_admission)
    fold_slices = [
        _slice_metrics(
            f"outer-fold:{fold}",
            [row for row in rows if row["outerFold"] == fold],
            reference_determinate_count=None,
            reference_determinate_duration_milliseconds=None,
        )
        for fold in range(OUTER_FOLD_COUNT)
    ]
    dataset_slices = []
    for dataset_id in DATASET_IDS:
        counts = _funnel_measure(datasets[dataset_id], "counts", f"Stage-1 {dataset_id}")
        duration = _funnel_measure(datasets[dataset_id], "durationMilliseconds", f"Stage-1 {dataset_id}")
        dataset_slices.append(
            _slice_metrics(
                f"dataset:{dataset_id}",
                [row for row in rows if row["datasetId"] == dataset_id],
                reference_determinate_count=counts["R"],
                reference_determinate_duration_milliseconds=duration["R"],
            )
        )
    role_slices = []
    for role in GUITARSET_ROLES:
        counts = _funnel_measure(roles[role], "counts", f"Stage-1 GuitarSet {role}")
        duration = _funnel_measure(roles[role], "durationMilliseconds", f"Stage-1 GuitarSet {role}")
        role_slices.append(
            _slice_metrics(
                f"guitarset-role:{role}",
                [row for row in rows if row["datasetId"] == "guitarset" and row["guitarsetRole"] == role],
                reference_determinate_count=counts["R"],
                reference_determinate_duration_milliseconds=duration["R"],
            )
        )
    reconciliation = deepcopy(stage1_admission["referenceEndpointReconciliationAudit"])
    reconciliation_disclosure = {
        "sourceAudit": reconciliation,
        "sourceAuditSha256": stage1_admission["referenceEndpointReconciliationAuditSha256"],
        "labelSideAuditOnly": True,
        "estimatorFeature": False,
        "durationGateInput": False,
        "readinessGate": False,
    }
    return {
        "reliability": {
            "fixedProbabilityDeciles": True,
            "micro": _reliability(rows, group_weighted=False),
            "groupBalanced": _reliability(rows, group_weighted=True),
        },
        "oofPerformance": {
            "microLogLoss": _micro_log_loss(rows),
            "microBrierScore": _micro_brier(rows),
            "microAreaUnderRiskCoverage": _aurc(rows, group_weighted=False),
            "groupBalancedLogLoss": _group_log_loss(rows),
            "groupBalancedBrierScore": _group_brier(rows),
            "groupBalancedAreaUnderRiskCoverage": _aurc(rows, group_weighted=True),
            "precisionCoverage": deepcopy(list(precision_coverage)),
            "durationWeightingUsed": False,
        },
        "probabilityQuantiles": {
            "correct": _quantile_report(
                [float(row["probability"]) for row in rows if row["correct"]], PROBABILITY_QUANTILES
            ),
            "incorrect": _quantile_report(
                [float(row["probability"]) for row in rows if not row["correct"]], PROBABILITY_QUANTILES
            ),
        },
        "slices": {
            "outerFolds": fold_slices,
            "datasets": dataset_slices,
            "guitarsetRoles": role_slices,
        },
        "acceptedGroupConcentration": _group_concentration(rows),
        "featureDrift": _feature_diagnostics(rows, selector, feature_names),
        "referenceEndpointReconciliation": {
            **reconciliation_disclosure,
            "disclosureSha256": canonical_sha256(reconciliation_disclosure),
        },
    }


def _source_object_binding(path: str, value: Mapping[str, Any], artifact_field: str) -> dict[str, Any]:
    rendered = _render_json(value)
    payload = {
        "path": path,
        "pathSha256": canonical_sha256(path),
        "fileSha256": _sha256_bytes(rendered),
        "canonicalSha256": canonical_sha256(value),
        "artifactSha256": _sha256(value.get(artifact_field), f"source {artifact_field}"),
    }
    return {**payload, "bindingSha256": canonical_sha256(payload)}


def _validate_recovery_input_receipts(
    recovery: Mapping[str, Any],
    stage1: Mapping[str, Any],
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
) -> None:
    immutable = _mapping(recovery.get("immutableInputs"), "recovery.immutableInputs")
    for name, value in (("stage1", stage1), ("examples", examples), ("selector", selector)):
        expected = _mapping(immutable.get(name), f"recovery.immutableInputs.{name}")
        if (
            _sha256_bytes(_render_json(value)) != expected.get("fileSha256")
            or canonical_sha256(value) != expected.get("canonicalSha256")
            or value.get("artifactSha256") != expected.get("artifactSha256")
        ):
            raise BeatCellReadinessError(f"The immutable R4 {name} receipt changed in recovery.")

    example_rows = list(_sequence(examples.get("examples"), "examples.examples"))
    example_duration = sum(
        _integer(_mapping(row, "example").get("durationMilliseconds"), "example.durationMilliseconds", minimum=1)
        for row in example_rows
    )
    expected_examples = _mapping(immutable.get("examples"), "recovery.immutableInputs.examples")
    if len(example_rows) != expected_examples.get("exampleCount") or example_duration != expected_examples.get(
        "exampleDurationMilliseconds"
    ):
        raise BeatCellReadinessError("The immutable R4 example denominators changed in recovery.")

    feature = _mapping(immutable.get("featureSet"), "recovery.immutableInputs.featureSet")
    expected_feature_receipts = {
        "sourceFeatureSetFileSha256": feature.get("manifestFileSha256"),
        "sourceFeatureSetArtifactSha256": feature.get("artifactSha256"),
        "sourceFeatureSummarySetSha256": feature.get("summarySetSha256"),
        "sourceFeatureRowSetSha256": feature.get("featureRowSetSha256"),
    }
    if any(examples.get(field) != expected for field, expected in expected_feature_receipts.items()):
        raise BeatCellReadinessError("The examples artifact changed an immutable R4 feature-set receipt.")


def _build_source_authority_binding(authority: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "schemaVersion": _string(authority.get("schemaVersion"), "authority.schemaVersion"),
        "path": str(authority_path()),
        "pathSha256": canonical_sha256(str(authority_path())),
        "fileSha256": AUTHORITY_FILE_SHA256,
        "canonicalSha256": AUTHORITY_CANONICAL_SHA256,
        "readinessProjection": deepcopy(authority["readiness"]),
        "readinessProjectionSha256": READINESS_PROJECTION_SHA256,
        "oneShotProjection": deepcopy(authority["oneShot"]),
        "oneShotProjectionSha256": ONE_SHOT_PROJECTION_SHA256,
    }
    return {**payload, "bindingSha256": canonical_sha256(payload)}


def _build_recovery_authority_binding(recovery: Mapping[str, Any]) -> dict[str, Any]:
    output = deepcopy(dict(_mapping(recovery.get("output"), "recovery.output")))
    frozen = deepcopy(dict(_mapping(recovery.get("frozenPolicy"), "recovery.frozenPolicy")))
    implementation = deepcopy(dict(_mapping(recovery.get("implementation"), "recovery.implementation")))
    one_shot = deepcopy(dict(_mapping(recovery.get("oneShot"), "recovery.oneShot")))
    payload = {
        "schemaVersion": _string(recovery.get("schemaVersion"), "recovery.schemaVersion"),
        "recoveryId": _string(recovery.get("recoveryId"), "recovery.recoveryId"),
        "path": str(recovery_authority_path()),
        "pathSha256": canonical_sha256(str(recovery_authority_path())),
        "fileSha256": RECOVERY_AUTHORITY_FILE_SHA256,
        "canonicalSha256": RECOVERY_AUTHORITY_CANONICAL_SHA256,
        "sourceCycleSha256": canonical_sha256(recovery["sourceCycle"]),
        "consumedFailureSha256": canonical_sha256(recovery["consumedFailure"]),
        "immutableInputsSha256": canonical_sha256(recovery["immutableInputs"]),
        "output": output,
        "outputSha256": canonical_sha256(output),
        "frozenPolicy": frozen,
        "frozenPolicySha256": canonical_sha256(frozen),
        "implementation": implementation,
        "implementationSha256": canonical_sha256(implementation),
        "oneShotProjection": one_shot,
        "oneShotProjectionSha256": canonical_sha256(one_shot),
        "forbiddenAccessSha256": canonical_sha256(recovery["forbiddenAccess"]),
    }
    return {**payload, "bindingSha256": canonical_sha256(payload)}


def _build_implementation_authorization_binding(receipt: Mapping[str, Any]) -> dict[str, Any]:
    implementation = _mapping(receipt.get("implementation"), "authorization.implementation")
    files = list(_sequence(implementation.get("files"), "authorization.implementation.files"))
    payload = {
        "schemaVersion": _string(receipt.get("schemaVersion"), "authorization.schemaVersion"),
        "recoveryId": _string(receipt.get("recoveryId"), "authorization.recoveryId"),
        "path": str(RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH),
        "pathSha256": canonical_sha256(str(RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH)),
        "payloadSha256": _sha256(receipt.get("payloadSha256"), "authorization.payloadSha256"),
        "implementationCommit": _string(
            implementation.get("implementationCommit"),
            "authorization.implementation.implementationCommit",
        ),
        "implementationFileInventorySha256": canonical_sha256(files),
        "handoffFileSha256": _sha256(
            implementation.get("handoffFileSha256"),
            "authorization.implementation.handoffFileSha256",
        ),
        "scopeSha256": canonical_sha256(receipt["scope"]),
        "forbiddenAccessSha256": canonical_sha256(receipt["forbiddenAccess"]),
        "independentAuditSha256": canonical_sha256(receipt["independentAudit"]),
        "userAuthorizationSha256": canonical_sha256(receipt["userAuthorization"]),
    }
    return {**payload, "bindingSha256": canonical_sha256(payload)}


def _build_input_bindings(
    recovery: Mapping[str, Any],
    source_authority_binding: Mapping[str, Any],
    recovery_authority_binding: Mapping[str, Any],
    implementation_authorization_binding: Mapping[str, Any],
    stage1: Mapping[str, Any],
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
) -> dict[str, Any]:
    immutable = _mapping(recovery.get("immutableInputs"), "recovery.immutableInputs")
    stage1_path = _string(_mapping(immutable.get("stage1"), "immutable stage1").get("path"), "stage1 path")
    examples_path = _string(_mapping(immutable.get("examples"), "immutable examples").get("path"), "examples path")
    selector_path = _string(_mapping(immutable.get("selector"), "immutable selector").get("path"), "selector path")
    payload = {
        "schemaVersion": BEAT_CELL_READINESS_INPUT_BINDINGS_SCHEMA,
        "sourceAuthorityBindingSha256": _sha256(
            source_authority_binding.get("bindingSha256"), "source authority binding"
        ),
        "recoveryAuthorityBindingSha256": _sha256(
            recovery_authority_binding.get("bindingSha256"), "recovery authority binding"
        ),
        "implementationAuthorizationBindingSha256": _sha256(
            implementation_authorization_binding.get("bindingSha256"),
            "implementation authorization binding",
        ),
        "stage1": _source_object_binding(stage1_path, stage1, "artifactSha256"),
        "examples": _source_object_binding(examples_path, examples, "artifactSha256"),
        "selector": _source_object_binding(selector_path, selector, "artifactSha256"),
    }
    return {**payload, "bindingsSha256": canonical_sha256(payload)}


def _metrics_for_exact_strata(
    rows: Sequence[Mapping[str, Any]], stage1_admission: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    aggregate_funnel = _mapping(stage1_admission.get("aggregate"), "Stage-1 aggregate")
    aggregate_counts = _funnel_measure(aggregate_funnel, "counts", "Stage-1 aggregate")
    aggregate_duration = _funnel_measure(aggregate_funnel, "durationMilliseconds", "Stage-1 aggregate")
    aggregate = _slice_metrics(
        "aggregate",
        rows,
        reference_determinate_count=aggregate_counts["R"],
        reference_determinate_duration_milliseconds=aggregate_duration["R"],
    )
    datasets, roles = _stage1_strata(stage1_admission)
    dataset_disclosures: list[dict[str, Any]] = []
    for dataset_id in DATASET_IDS:
        counts = _funnel_measure(datasets[dataset_id], "counts", f"Stage-1 {dataset_id}")
        duration = _funnel_measure(datasets[dataset_id], "durationMilliseconds", f"Stage-1 {dataset_id}")
        dataset_disclosures.append(
            _slice_metrics(
                f"dataset:{dataset_id}",
                [row for row in rows if row["datasetId"] == dataset_id],
                reference_determinate_count=counts["R"],
                reference_determinate_duration_milliseconds=duration["R"],
            )
        )
    guitarset = deepcopy(dataset_disclosures[DATASET_IDS.index("guitarset")])
    role_disclosures: list[dict[str, Any]] = []
    for role in GUITARSET_ROLES:
        counts = _funnel_measure(roles[role], "counts", f"Stage-1 GuitarSet {role}")
        duration = _funnel_measure(roles[role], "durationMilliseconds", f"Stage-1 GuitarSet {role}")
        role_disclosures.append(
            _slice_metrics(
                f"guitarset-role:{role}",
                [row for row in rows if row["datasetId"] == "guitarset" and row["guitarsetRole"] == role],
                reference_determinate_count=counts["R"],
                reference_determinate_duration_milliseconds=duration["R"],
            )
        )
    guitarset.update(
        {
            "wilson95LowerBoundIsGate": False,
            "compSolo": role_disclosures,
            "roleSpecificGates": False,
            "soloDeploymentAuthorized": False,
        }
    )
    return aggregate, dataset_disclosures, guitarset


def _build_diagnostic_source(
    rows: Sequence[Mapping[str, Any]],
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
    feature_names: Sequence[str],
) -> dict[str, Any]:
    estimator = _mapping(selector.get("estimator"), "selector.estimator")
    preprocessing = {
        "imputationValues": deepcopy(list(_sequence(estimator.get("imputationValues"), "imputationValues"))),
        "allMissingFeatureNames": deepcopy(
            list(_sequence(estimator.get("allMissingFeatureNames"), "allMissingFeatureNames"))
        ),
        "center": deepcopy(list(_sequence(estimator.get("center"), "center"))),
        "scale": deepcopy(list(_sequence(estimator.get("scale"), "scale"))),
    }
    feature_projection = [
        {
            "exampleKey": row["exampleKey"],
            "featureValuesSha256": row["featureValuesSha256"],
            "orderedFeatureValues": deepcopy(row["features"]),
        }
        for row in rows
    ]
    payload = {
        "schemaVersion": "chord_runtime_beat_cell_readiness_diagnostic_source_v1",
        "sourceExamplesArtifactSha256": _sha256(examples.get("artifactSha256"), "examples.artifactSha256"),
        "sourceSelectorArtifactSha256": _sha256(selector.get("artifactSha256"), "selector.artifactSha256"),
        "featureNames": list(feature_names),
        "estimatorPreprocessing": preprocessing,
        "estimatorPreprocessingSha256": canonical_sha256(preprocessing),
        "joinedFeatureProjectionSetSha256": canonical_sha256(feature_projection),
    }
    return {**payload, "sourceSha256": canonical_sha256(payload)}


def evaluate_beat_cell_readiness(
    stage1_artifact: Mapping[str, Any],
    examples_artifact: Mapping[str, Any],
    selector_artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate exactly one frozen mapping-level beat-cell readiness candidate.

    This function performs no file I/O.  It is the only supported seam for
    synthetic fixtures.  Official execution must use ``run_beat_cell_readiness``.
    """

    authority = _authority_contract()
    recovery = _recovery_contract()
    implementation_authorization = dict(_implementation_authorization_receipt())
    if recovery["output"]["readinessReport"] == authority["outputPaths"]["readinessReport"]:
        raise BeatCellReadinessError("The R5 recovery output may not reuse the consumed R4 readiness path.")
    stage1 = dict(_mapping(stage1_artifact, "Stage-1 artifact"))
    examples = dict(_mapping(examples_artifact, "examples artifact"))
    selector = dict(_mapping(selector_artifact, "selector artifact"))
    _sealed_preflight(stage1, examples, selector)
    stage1_admission = _validate_stage1_admission(stage1, authority)
    examples, feature_names = _validate_examples_admission(examples, authority, stage1_admission)
    _crosscheck_examples_stage1(examples, stage1, stage1_admission)
    _validate_recovery_input_receipts(recovery, stage1, examples, selector)
    reproduction = _validate_selector_and_reproduce(examples, selector)
    rows, public_rows, diagnostic_reasons = _join_oof_rows(examples, selector, feature_names)
    _crosscheck_joined_stage1(rows, stage1_admission)

    stored_evaluation, recomputed_evaluation, fixed_point = _verify_stored_evaluation(selector, rows, authority)
    cutoff = float(fixed_point["minimumProbabilityAtDescriptivePoint"])
    for row in rows:
        row["accepted"] = bool(float(row["probability"]) >= cutoff)
    for public, internal in zip(public_rows, rows, strict=True):
        payload = _unsigned(public, "rowSha256")
        payload["acceptedAtFixedDevelopmentCutoff"] = internal["accepted"]
        public.clear()
        public.update({**payload, "rowSha256": canonical_sha256(payload)})

    aggregate, dataset_disclosures, guitarset = _metrics_for_exact_strata(rows, stage1_admission)
    if not math.isclose(
        float(aggregate["groupBalancedConditionalCoverage"] or 0.0),
        float(fixed_point["realizableCoverage"]),
        rel_tol=0,
        abs_tol=1e-12,
    ) or not math.isclose(
        float(aggregate["groupBalancedPrecision"] or 0.0),
        float(fixed_point["groupBalancedPrecision"]),
        rel_tol=0,
        abs_tol=1e-12,
    ):
        raise BeatCellReadinessError("Same-cutoff accepted rows disagree with the exact tie-block point.")

    gates = _build_readiness_gates(aggregate, guitarset)
    if not any(row["correct"] for row in rows):
        diagnostic_reasons.append("diagnostics.correct-probability-quantiles-missing")
    if not any(not row["correct"] for row in rows):
        diagnostic_reasons.append("diagnostics.incorrect-probability-quantiles-missing")
    diagnostics = _build_diagnostics(
        rows,
        selector,
        feature_names,
        stage1_admission,
        recomputed_evaluation["precisionCoverage"],
    )
    diagnostics_sha256 = canonical_sha256(diagnostics)
    diagnostic_source = _build_diagnostic_source(rows, examples, selector, feature_names)
    gate_failure_reasons = [f"gate.{gate['gateId']}" for gate in gates if gate["passed"] is not True]
    failure_reasons = sorted(set([*gate_failure_reasons, *diagnostic_reasons]))
    passed = not failure_reasons

    count_audit_payload = {
        "T": EXPECTED_STAGE1_AGGREGATE_COUNT["T"],
        "U": EXPECTED_STAGE1_AGGREGATE_COUNT["U"],
        "R": EXPECTED_STAGE1_AGGREGATE_COUNT["R"],
        "N": EXPECTED_STAGE1_AGGREGATE_COUNT["N"],
        "E": EXPECTED_STAGE1_AGGREGATE_COUNT["E"],
        "C": EXPECTED_STAGE1_AGGREGATE_COUNT["C"],
        "I": EXPECTED_STAGE1_AGGREGATE_COUNT["I"],
        "joinedOofRowCount": len(rows),
        "identitiesReconciled": True,
    }
    count_audit = {
        **count_audit_payload,
        "auditSha256": canonical_sha256(count_audit_payload),
    }
    duration_audit_payload = {
        "unit": "canonical-integer-milliseconds",
        "T": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["T"],
        "U": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["U"],
        "R": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["R"],
        "N": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["N"],
        "E": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["E"],
        "C": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["C"],
        "I": EXPECTED_STAGE1_AGGREGATE_DURATION_MS["I"],
        "joinedOofDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in rows),
        "durationNeverUsedForTrainingOrCutoff": True,
        "identitiesReconciled": True,
    }
    duration_audit = {
        **duration_audit_payload,
        "auditSha256": canonical_sha256(duration_audit_payload),
    }
    source_authority_binding = _build_source_authority_binding(authority)
    recovery_authority_binding = _build_recovery_authority_binding(recovery)
    implementation_authorization_binding = _build_implementation_authorization_binding(implementation_authorization)
    input_bindings = _build_input_bindings(
        recovery,
        source_authority_binding,
        recovery_authority_binding,
        implementation_authorization_binding,
        stage1,
        examples,
        selector,
    )
    publication_path = _string(
        _mapping(recovery.get("output"), "recovery.output").get("readinessReport"),
        "recovery.output.readinessReport",
    )
    publication = {
        "mode": recovery["output"]["publicationMode"],
        "outputPath": publication_path,
        "outputPathSha256": canonical_sha256(publication_path),
        "callerPathOverrideAllowed": False,
    }
    metric_recomputation_payload = {
        "selectorValidatorPassed": True,
        "storedEvaluation": deepcopy(stored_evaluation),
        "storedEvaluationSha256": canonical_sha256(stored_evaluation),
        "recomputedEvaluation": deepcopy(recomputed_evaluation),
        "recomputedEvaluationSha256": canonical_sha256(recomputed_evaluation),
        "denominatorsExact": True,
        "precisionCoverageCurveExact": stored_evaluation.get("precisionCoverage")
        == recomputed_evaluation["precisionCoverage"],
        "fixedPointSha256": canonical_sha256(fixed_point),
    }
    metric_recomputation = {
        **metric_recomputation_payload,
        "auditSha256": canonical_sha256(metric_recomputation_payload),
    }
    decision_payload = {
        "validationPassed": True,
        "allStage1AdmissionsPassed": True,
        "allNumericGatesPassed": all(gate["passed"] is True for gate in gates),
        "mandatoryDiagnosticsComplete": not diagnostic_reasons,
        "failureReasons": failure_reasons,
        "developmentReadinessPassed": passed,
        "calibrationMayOpenOnce": passed,
        "automaticCalibrationAccess": False,
        "calibrationStatus": "may-open-once-after-independent-audit" if passed else "closed",
        "promotionEligible": False,
        "playerPlaybackAuthorized": False,
        "stopForIndependentAudit": True,
    }
    decision = {**decision_payload, "decisionSha256": canonical_sha256(decision_payload)}
    one_shot_payload = {
        "policy": deepcopy(recovery["oneShot"]),
        "policySha256": canonical_sha256(recovery["oneShot"]),
        "newCycle": deepcopy(_RECOVERY_NEW_CYCLE_COUNTS),
        "cumulativeIncludingConsumedR4": deepcopy(_RECOVERY_CUMULATIVE_COUNTS),
        "sourceR4SameCycleRetryPerformed": False,
        "immutableR4ArtifactsReused": True,
        "sameCycleRetryAllowed": False,
        "stopAfterReadinessForIndependentAudit": True,
    }
    one_shot = {**one_shot_payload, "auditSha256": canonical_sha256(one_shot_payload)}
    artifact_payload: dict[str, Any] = {
        "schemaVersion": BEAT_CELL_READINESS_SCHEMA,
        "recoveryId": recovery["recoveryId"],
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "playerPlaybackAuthorized": False,
        "operatingThreshold": None,
        "purpose": READINESS_PURPOSE,
        "publication": publication,
        "sourceAuthorityBinding": source_authority_binding,
        "recoveryAuthorityBinding": recovery_authority_binding,
        "implementationAuthorizationBinding": implementation_authorization_binding,
        "inputBindings": input_bindings,
        "rubric": deepcopy(BEAT_CELL_READINESS_RUBRIC),
        "rubricSha256": BEAT_CELL_READINESS_RUBRIC_SHA256,
        "featureNames": list(feature_names),
        "oneShot": one_shot,
        "reproduction": reproduction,
        "stage1Admission": deepcopy(stage1_admission),
        "countAudit": count_audit,
        "durationAudit": duration_audit,
        "joinedOofRows": public_rows,
        "joinedOofRowSetSha256": canonical_sha256(public_rows),
        "storedMetricRecomputation": metric_recomputation,
        "diagnosticSource": diagnostic_source,
        "fixedDevelopmentCutoff": {
            "targetCoverage": FIXED_TARGET_COVERAGE,
            "minimumProbabilityAtDescriptivePoint": cutoff,
            "acceptanceRule": "probability >= minimumProbabilityAtDescriptivePoint; exact ties included",
            "isOperatingThreshold": False,
            "isPromotionDecision": False,
            "durationWeighted": False,
            "fixedPointSha256": canonical_sha256(fixed_point),
        },
        "aggregate": aggregate,
        "datasets": dataset_disclosures,
        "datasetSetSha256": canonical_sha256(dataset_disclosures),
        "guitarset": guitarset,
        "gates": gates,
        "gateSetSha256": canonical_sha256(gates),
        "diagnostics": diagnostics,
        "diagnosticsSha256": diagnostics_sha256,
        "decision": decision,
        "developmentReadinessPassed": passed,
        "calibrationMayOpenOnce": passed,
        "calibrationStatus": decision["calibrationStatus"],
    }
    artifact = {**artifact_payload, "artifactSha256": canonical_sha256(artifact_payload)}
    validate_beat_cell_readiness_artifact(artifact)
    return deepcopy(artifact)


_READINESS_ARTIFACT_FIELDS = frozenset(
    {
        "schemaVersion",
        "recoveryId",
        "split",
        "developmentOnly",
        "promotionEligible",
        "playerPlaybackAuthorized",
        "operatingThreshold",
        "purpose",
        "publication",
        "sourceAuthorityBinding",
        "recoveryAuthorityBinding",
        "implementationAuthorizationBinding",
        "inputBindings",
        "rubric",
        "rubricSha256",
        "featureNames",
        "oneShot",
        "reproduction",
        "stage1Admission",
        "countAudit",
        "durationAudit",
        "joinedOofRows",
        "joinedOofRowSetSha256",
        "storedMetricRecomputation",
        "diagnosticSource",
        "fixedDevelopmentCutoff",
        "aggregate",
        "datasets",
        "datasetSetSha256",
        "guitarset",
        "gates",
        "gateSetSha256",
        "diagnostics",
        "diagnosticsSha256",
        "decision",
        "developmentReadinessPassed",
        "calibrationMayOpenOnce",
        "calibrationStatus",
        "artifactSha256",
    }
)
_PUBLIC_ROW_FIELDS = frozenset(
    {
        "schemaVersion",
        "exampleKey",
        "exampleSha256",
        "trackId",
        "cellIndex",
        "durationMilliseconds",
        "datasetId",
        "role",
        "guitarsetRole",
        "confidenceGroupId",
        "outerFold",
        "probability",
        "correct",
        "sampleWeight",
        "featureValuesSha256",
        "orderedFeatureValues",
        "sourceBeatCellSha256",
        "stage1OutcomeRowSha256",
        "sourceGroupTrackRowSha256",
        "predictionIdentitySha256",
        "audioLineageRowSha256",
        "acceptedAtFixedDevelopmentCutoff",
        "rowSha256",
    }
)


def _validate_public_rows(
    artifact: Mapping[str, Any], cutoff: float, feature_names: Sequence[str]
) -> list[dict[str, Any]]:
    raw_rows = list(_sequence(artifact.get("joinedOofRows"), "readiness.joinedOofRows"))
    rows: list[dict[str, Any]] = []
    observed_keys: list[str] = []
    logical_keys: set[tuple[str, int]] = set()
    folds_by_group: dict[str, set[int]] = defaultdict(set)
    weights_by_group: dict[str, list[float]] = defaultdict(list)
    for index, raw in enumerate(raw_rows):
        row = dict(_mapping(raw, f"readiness.joinedOofRows[{index}]"))
        _exact_fields(row, _PUBLIC_ROW_FIELDS, f"readiness.joinedOofRows[{index}]")
        if row.get("schemaVersion") != BEAT_CELL_READINESS_JOINED_ROW_SCHEMA:
            raise BeatCellReadinessError("A joined OOF row uses an unsupported schemaVersion.")
        row_sha = _sha256(row.get("rowSha256"), f"joined row {index}.rowSha256")
        if row_sha != canonical_sha256(_unsigned(row, "rowSha256")):
            raise BeatCellReadinessError("A joined OOF row self-hash is stale.")
        key = _sha256(row.get("exampleKey"), f"joined row {index}.exampleKey")
        _sha256(row.get("exampleSha256"), f"joined row {index}.exampleSha256")
        track_id = _string(row.get("trackId"), f"joined row {index}.trackId")
        cell_index = _integer(row.get("cellIndex"), f"joined row {index}.cellIndex")
        logical = (track_id, cell_index)
        if logical in logical_keys:
            raise BeatCellReadinessError("Joined OOF rows repeat a logical track/cell key.")
        logical_keys.add(logical)
        duration = _integer(row.get("durationMilliseconds"), f"joined row {index}.durationMilliseconds", minimum=1)
        dataset_id = _string(row.get("datasetId"), f"joined row {index}.datasetId")
        role = _string(row.get("role"), f"joined row {index}.role")
        guitarset_role = row.get("guitarsetRole")
        if guitarset_role is not None:
            guitarset_role = _string(guitarset_role, f"joined row {index}.guitarsetRole")
        if dataset_id not in DATASET_IDS or (dataset_id == "guitarset") != (guitarset_role in GUITARSET_ROLES):
            raise BeatCellReadinessError("Joined OOF dataset/GuitarSet role metadata is invalid.")
        group = _string(row.get("confidenceGroupId"), f"joined row {index}.confidenceGroupId")
        fold = _integer(row.get("outerFold"), f"joined row {index}.outerFold")
        if fold >= OUTER_FOLD_COUNT:
            raise BeatCellReadinessError("A joined OOF outer fold lies outside [0,4].")
        probability = _finite(row.get("probability"), f"joined row {index}.probability")
        sample_weight = _finite(row.get("sampleWeight"), f"joined row {index}.sampleWeight")
        correct = row.get("correct")
        accepted = row.get("acceptedAtFixedDevelopmentCutoff")
        if (
            not 0 <= probability <= 1
            or sample_weight <= 0
            or not isinstance(correct, bool)
            or not isinstance(accepted, bool)
            or accepted is not (probability >= cutoff)
        ):
            raise BeatCellReadinessError("Joined OOF probability, weight, outcome, or inclusive cutoff is invalid.")
        for field in (
            "featureValuesSha256",
            "sourceBeatCellSha256",
            "stage1OutcomeRowSha256",
            "sourceGroupTrackRowSha256",
            "predictionIdentitySha256",
            "audioLineageRowSha256",
        ):
            _sha256(row.get(field), f"joined row {index}.{field}")
        raw_features = list(_sequence(row.get("orderedFeatureValues"), f"joined row {index}.orderedFeatureValues"))
        if len(raw_features) != len(feature_names):
            raise BeatCellReadinessError("A joined row changed the exact ordered feature dimension.")
        features: list[int | float | None] = []
        for item in raw_features:
            if item is not None:
                _finite(item, f"joined row {index}.orderedFeatureValues")
            features.append(item)
        feature_mapping = {feature_name: features[position] for position, feature_name in enumerate(feature_names)}
        _validate_feature_value_types(feature_mapping, feature_names, f"joined row {index}")
        if canonical_sha256(feature_mapping) != row.get("featureValuesSha256"):
            raise BeatCellReadinessError("A joined row ordered feature vector disagrees with featureValuesSha256.")
        observed_keys.append(key)
        folds_by_group[group].add(fold)
        weights_by_group[group].append(sample_weight)
        rows.append(
            {
                "exampleKey": key,
                "trackId": track_id,
                "cellIndex": cell_index,
                "durationMilliseconds": duration,
                "datasetId": dataset_id,
                "role": role,
                "guitarsetRole": guitarset_role,
                "confidenceGroupId": group,
                "outerFold": fold,
                "probability": probability,
                "correct": correct,
                "sampleWeight": sample_weight,
                "accepted": accepted,
                "features": features,
                "featureValuesSha256": row["featureValuesSha256"],
                "sourceBeatCellSha256": row["sourceBeatCellSha256"],
                "stage1OutcomeRowSha256": row["stage1OutcomeRowSha256"],
                "sourceGroupTrackRowSha256": row["sourceGroupTrackRowSha256"],
                "predictionIdentitySha256": row["predictionIdentitySha256"],
                "audioLineageRowSha256": row["audioLineageRowSha256"],
            }
        )
    if observed_keys != sorted(observed_keys) or len(observed_keys) != len(set(observed_keys)):
        raise BeatCellReadinessError("Joined OOF rows must be uniquely ordered by exampleKey.")
    if canonical_sha256(raw_rows) != artifact.get("joinedOofRowSetSha256"):
        raise BeatCellReadinessError("joinedOofRowSetSha256 is stale.")
    for group, folds in folds_by_group.items():
        if len(folds) != 1 or not math.isclose(math.fsum(weights_by_group[group]), 1.0, rel_tol=0, abs_tol=1e-12):
            raise BeatCellReadinessError(f"Joined confidence group {group!r} crosses folds or weight mass one.")
    return rows


def _validate_diagnostic_recomputation(
    diagnostics: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    stage1_admission: Mapping[str, Any],
    feature_names: Sequence[str],
    diagnostic_source: Mapping[str, Any],
) -> None:
    _exact_fields(
        diagnostics,
        {
            "reliability",
            "oofPerformance",
            "probabilityQuantiles",
            "slices",
            "acceptedGroupConcentration",
            "featureDrift",
            "referenceEndpointReconciliation",
        },
        "diagnostics",
    )
    reliability = _mapping(diagnostics.get("reliability"), "diagnostics.reliability")
    expected_reliability = {
        "fixedProbabilityDeciles": True,
        "micro": _reliability(rows, group_weighted=False),
        "groupBalanced": _reliability(rows, group_weighted=True),
    }
    if dict(reliability) != expected_reliability:
        raise BeatCellReadinessError("Reliability diagnostics failed exact joined-row recomputation.")
    performance = _mapping(diagnostics.get("oofPerformance"), "diagnostics.oofPerformance")
    expected_performance = {
        "microLogLoss": _micro_log_loss(rows),
        "microBrierScore": _micro_brier(rows),
        "microAreaUnderRiskCoverage": _aurc(rows, group_weighted=False),
        "groupBalancedLogLoss": _group_log_loss(rows),
        "groupBalancedBrierScore": _group_brier(rows),
        "groupBalancedAreaUnderRiskCoverage": _aurc(rows, group_weighted=True),
        "precisionCoverage": performance.get("precisionCoverage"),
        "durationWeightingUsed": False,
    }
    if dict(performance) != expected_performance:
        raise BeatCellReadinessError("OOF performance diagnostics failed exact joined-row recomputation.")
    quantiles = _mapping(diagnostics.get("probabilityQuantiles"), "diagnostics.probabilityQuantiles")
    if quantiles != {
        "correct": _quantile_report(
            [float(row["probability"]) for row in rows if row["correct"]], PROBABILITY_QUANTILES
        ),
        "incorrect": _quantile_report(
            [float(row["probability"]) for row in rows if not row["correct"]], PROBABILITY_QUANTILES
        ),
    }:
        raise BeatCellReadinessError("Probability quantile diagnostics failed exact recomputation.")
    if diagnostics.get("acceptedGroupConcentration") != _group_concentration(rows):
        raise BeatCellReadinessError("Accepted-group concentration failed exact recomputation.")
    _aggregate, dataset_slices, guitarset = _metrics_for_exact_strata(rows, stage1_admission)
    expected_slices = {
        "outerFolds": [
            _slice_metrics(
                f"outer-fold:{fold}",
                [row for row in rows if row["outerFold"] == fold],
                reference_determinate_count=None,
                reference_determinate_duration_milliseconds=None,
            )
            for fold in range(OUTER_FOLD_COUNT)
        ],
        "datasets": dataset_slices,
        "guitarsetRoles": guitarset["compSolo"],
    }
    if diagnostics.get("slices") != expected_slices:
        raise BeatCellReadinessError("Fold/dataset/GuitarSet-role slices failed exact recomputation.")
    preprocessing = _mapping(
        diagnostic_source.get("estimatorPreprocessing"),
        "diagnosticSource.estimatorPreprocessing",
    )
    expected_feature_drift = _feature_diagnostics(rows, {"estimator": preprocessing}, feature_names)
    if diagnostics.get("featureDrift") != expected_feature_drift:
        raise BeatCellReadinessError("Feature missingness or standardized-z diagnostics failed exact recomputation.")
    reconciliation = _mapping(
        diagnostics.get("referenceEndpointReconciliation"),
        "diagnostics.referenceEndpointReconciliation",
    )
    expected_reconciliation_disclosure = {
        "sourceAudit": deepcopy(stage1_admission["referenceEndpointReconciliationAudit"]),
        "sourceAuditSha256": stage1_admission["referenceEndpointReconciliationAuditSha256"],
        "labelSideAuditOnly": True,
        "estimatorFeature": False,
        "durationGateInput": False,
        "readinessGate": False,
    }
    expected_reconciliation = {
        **expected_reconciliation_disclosure,
        "disclosureSha256": canonical_sha256(expected_reconciliation_disclosure),
    }
    if dict(reconciliation) != expected_reconciliation:
        raise BeatCellReadinessError("Endpoint reconciliation disclosure is stale or leaked into readiness.")


def _validate_diagnostic_source(
    source: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    input_bindings: Mapping[str, Any],
) -> dict[str, Any]:
    _exact_fields(
        source,
        {
            "schemaVersion",
            "sourceExamplesArtifactSha256",
            "sourceSelectorArtifactSha256",
            "featureNames",
            "estimatorPreprocessing",
            "estimatorPreprocessingSha256",
            "joinedFeatureProjectionSetSha256",
            "sourceSha256",
        },
        "diagnosticSource",
    )
    if (
        source.get("schemaVersion") != "chord_runtime_beat_cell_readiness_diagnostic_source_v1"
        or source.get("sourceSha256") != canonical_sha256(_unsigned(source, "sourceSha256"))
        or source.get("featureNames") != list(feature_names)
        or source.get("sourceExamplesArtifactSha256")
        != _mapping(input_bindings.get("examples"), "inputBindings.examples").get("artifactSha256")
        or source.get("sourceSelectorArtifactSha256")
        != _mapping(input_bindings.get("selector"), "inputBindings.selector").get("artifactSha256")
    ):
        raise BeatCellReadinessError("Diagnostic source envelope or source artifacts are stale.")
    preprocessing = dict(_mapping(source.get("estimatorPreprocessing"), "diagnosticSource.estimatorPreprocessing"))
    _exact_fields(
        preprocessing,
        {"imputationValues", "allMissingFeatureNames", "center", "scale"},
        "diagnosticSource.estimatorPreprocessing",
    )
    if source.get("estimatorPreprocessingSha256") != canonical_sha256(preprocessing):
        raise BeatCellReadinessError("Diagnostic estimator preprocessing hash is stale.")
    feature_projection = [
        {
            "exampleKey": row["exampleKey"],
            "featureValuesSha256": row["featureValuesSha256"],
            "orderedFeatureValues": deepcopy(row["features"]),
        }
        for row in rows
    ]
    if source.get("joinedFeatureProjectionSetSha256") != canonical_sha256(feature_projection):
        raise BeatCellReadinessError("Diagnostic joined feature projection hash is stale.")
    return deepcopy(dict(source))


def validate_beat_cell_readiness_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed on a standalone beat-cell readiness report and return a copy."""

    authority = _authority_contract()
    recovery = _recovery_contract()
    implementation_authorization = dict(_implementation_authorization_receipt())
    value = dict(_mapping(artifact, "beat-cell readiness artifact"))
    _exact_fields(value, _READINESS_ARTIFACT_FIELDS, "beat-cell readiness artifact")
    claimed = _sha256(value.get("artifactSha256"), "readiness.artifactSha256")
    if claimed != canonical_sha256(_unsigned(value, "artifactSha256")):
        raise BeatCellReadinessError("Readiness artifactSha256 is stale.")
    if (
        value.get("schemaVersion") != BEAT_CELL_READINESS_SCHEMA
        or value.get("recoveryId") != recovery.get("recoveryId")
        or value.get("split") != DEVELOPMENT_SPLIT
        or value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
        or value.get("playerPlaybackAuthorized") is not False
        or value.get("operatingThreshold") is not None
        or value.get("purpose") != READINESS_PURPOSE
    ):
        raise BeatCellReadinessError("Readiness envelope is not sealed development-only/non-player state.")
    if (
        value.get("rubric") != BEAT_CELL_READINESS_RUBRIC
        or value.get("rubricSha256") != BEAT_CELL_READINESS_RUBRIC_SHA256
    ):
        raise BeatCellReadinessError("Readiness rubric or rubricSha256 drifted.")
    feature_names = list(_sequence(value.get("featureNames"), "readiness.featureNames"))
    if feature_names != list(authority["featureMath"]["featureNames"]):
        raise BeatCellReadinessError("Readiness featureNames changed the exact authority projection.")
    publication = _mapping(value.get("publication"), "readiness.publication")
    exact_output = recovery["output"]["readinessReport"]
    _exact_fields(
        publication,
        {"mode", "outputPath", "outputPathSha256", "callerPathOverrideAllowed"},
        "readiness.publication",
    )
    if (
        publication.get("mode") != PUBLICATION_MODE
        or publication.get("mode") != recovery["output"]["publicationMode"]
        or publication.get("outputPath") != exact_output
        or publication.get("outputPathSha256") != canonical_sha256(exact_output)
        or publication.get("callerPathOverrideAllowed") is not False
    ):
        raise BeatCellReadinessError("Readiness publication is not bound to the exact R5 recovery path.")
    source_authority_binding = _mapping(value.get("sourceAuthorityBinding"), "readiness.sourceAuthorityBinding")
    recovery_authority_binding = _mapping(value.get("recoveryAuthorityBinding"), "readiness.recoveryAuthorityBinding")
    implementation_authorization_binding = _mapping(
        value.get("implementationAuthorizationBinding"),
        "readiness.implementationAuthorizationBinding",
    )
    if dict(source_authority_binding) != _build_source_authority_binding(authority):
        raise BeatCellReadinessError("Readiness sourceAuthorityBinding is not the exact R4 authority.")
    if dict(recovery_authority_binding) != _build_recovery_authority_binding(recovery):
        raise BeatCellReadinessError("Readiness recoveryAuthorityBinding is not the exact R5 authority.")
    if dict(implementation_authorization_binding) != _build_implementation_authorization_binding(
        implementation_authorization
    ):
        raise BeatCellReadinessError("Readiness implementationAuthorizationBinding is not the exact execution receipt.")
    bindings = _mapping(value.get("inputBindings"), "readiness.inputBindings")
    _exact_fields(
        bindings,
        {
            "schemaVersion",
            "sourceAuthorityBindingSha256",
            "recoveryAuthorityBindingSha256",
            "implementationAuthorizationBindingSha256",
            "stage1",
            "examples",
            "selector",
            "bindingsSha256",
        },
        "readiness.inputBindings",
    )
    if bindings.get("schemaVersion") != BEAT_CELL_READINESS_INPUT_BINDINGS_SCHEMA:
        raise BeatCellReadinessError("Readiness input bindings use an unsupported schemaVersion.")
    if bindings.get("bindingsSha256") != canonical_sha256(_unsigned(bindings, "bindingsSha256")):
        raise BeatCellReadinessError("Readiness input bindings self-hash is stale.")
    if bindings.get("sourceAuthorityBindingSha256") != source_authority_binding.get("bindingSha256") or bindings.get(
        "recoveryAuthorityBindingSha256"
    ) != recovery_authority_binding.get("bindingSha256"):
        raise BeatCellReadinessError("Readiness input bindings do not link both exact authorities.")
    if bindings.get("implementationAuthorizationBindingSha256") != implementation_authorization_binding.get(
        "bindingSha256"
    ):
        raise BeatCellReadinessError("Readiness input bindings do not link the exact implementation authorization.")
    for name in ("stage1", "examples", "selector"):
        binding = _mapping(bindings.get(name), f"readiness.inputBindings.{name}")
        _exact_fields(
            binding,
            {
                "path",
                "pathSha256",
                "fileSha256",
                "canonicalSha256",
                "artifactSha256",
                "bindingSha256",
            },
            f"readiness.inputBindings.{name}",
        )
        if binding.get("bindingSha256") != canonical_sha256(_unsigned(binding, "bindingSha256")):
            raise BeatCellReadinessError(f"Readiness {name} source binding is stale.")
        for field in ("pathSha256", "fileSha256", "canonicalSha256", "artifactSha256"):
            _sha256(binding.get(field), f"readiness input {name}.{field}")
        if binding.get("pathSha256") != canonical_sha256(binding.get("path")):
            raise BeatCellReadinessError(f"Readiness {name} source path hash is stale.")
    immutable = _mapping(recovery.get("immutableInputs"), "recovery.immutableInputs")
    for name in ("stage1", "examples", "selector"):
        binding = bindings[name]
        expected = _mapping(immutable.get(name), f"recovery.immutableInputs.{name}")
        if any(
            binding.get(field) != expected.get(field)
            for field in ("path", "fileSha256", "canonicalSha256", "artifactSha256")
        ):
            raise BeatCellReadinessError(f"Readiness {name} binding changed an immutable R4 receipt.")

    admission = _mapping(value.get("stage1Admission"), "readiness.stage1Admission")
    _exact_fields(
        admission,
        {
            "sourceStage1ArtifactSha256",
            "sourceStage1DecisionSha256",
            "sourceStage1GateSetSha256",
            "sourceStage1TrackSetSha256",
            "sourceStage1SourceContractSha256",
            "allThirteenStage1GatesPassed",
            "eligibleOutcomeCount",
            "eligibleOutcomeDurationMilliseconds",
            "eligibleOutcomeBindingSetSha256",
            "aggregate",
            "datasets",
            "guitarset",
            "referenceEndpointReconciliationAudit",
            "referenceEndpointReconciliationAuditSha256",
            "admissionSha256",
        },
        "readiness.stage1Admission",
    )
    if (
        admission.get("admissionSha256") != canonical_sha256(_unsigned(admission, "admissionSha256"))
        or admission.get("admissionSha256") != EXPECTED_STAGE1_ADMISSION_PROJECTION_SHA256
    ):
        raise BeatCellReadinessError("Stage-1 admission self-hash is stale.")
    stage1_source = authority["sourceInputs"]["stage1Report"]
    if (
        admission.get("sourceStage1ArtifactSha256") != stage1_source["artifactSha256"]
        or admission.get("sourceStage1DecisionSha256") != stage1_source["decisionSha256"]
        or admission.get("sourceStage1GateSetSha256") != stage1_source["gateSetSha256"]
        or admission.get("sourceStage1TrackSetSha256") != stage1_source["trackSetSha256"]
        or admission.get("sourceStage1SourceContractSha256") != stage1_source["sourceContractSha256"]
        or admission.get("allThirteenStage1GatesPassed") is not True
        or admission.get("eligibleOutcomeCount") != EXPECTED_STAGE1_AGGREGATE_COUNT["E"]
        or admission.get("eligibleOutcomeDurationMilliseconds") != EXPECTED_STAGE1_AGGREGATE_DURATION_MS["E"]
    ):
        raise BeatCellReadinessError("Readiness changed exact Stage-1 admissions.")
    aggregate_admission = _validated_admission_funnel(
        _mapping(admission.get("aggregate"), "readiness Stage-1 aggregate"),
        "readiness Stage-1 aggregate",
    )
    if aggregate_admission != make_funnel(EXPECTED_STAGE1_AGGREGATE_COUNT, EXPECTED_STAGE1_AGGREGATE_DURATION_MS):
        raise BeatCellReadinessError("Readiness changed the exact aggregate Stage-1 funnel.")
    dataset_rows = list(_sequence(admission.get("datasets"), "readiness Stage-1 datasets"))
    if len(dataset_rows) != len(DATASET_IDS):
        raise BeatCellReadinessError("Readiness must retain exactly five Stage-1 dataset funnels.")
    dataset_count_sum = {field: 0 for field in _FUNNEL_FIELDS}
    dataset_duration_sum = {field: 0 for field in _FUNNEL_FIELDS}
    for dataset_id, raw_row in zip(DATASET_IDS, dataset_rows, strict=True):
        row = _mapping(raw_row, f"readiness Stage-1 dataset {dataset_id}")
        _exact_fields(
            row,
            {"datasetId", "trackCount", "funnel", "funnelSha256", "rowSha256"},
            f"readiness Stage-1 dataset {dataset_id}",
        )
        if (
            row.get("datasetId") != dataset_id
            or row.get("trackCount") != EXPECTED_DATASET_TRACK_COUNTS[dataset_id]
            or row.get("rowSha256") != canonical_sha256(_unsigned(row, "rowSha256"))
        ):
            raise BeatCellReadinessError(f"Readiness Stage-1 dataset {dataset_id} provenance is stale.")
        funnel = _validated_admission_funnel(
            _mapping(row.get("funnel"), f"readiness Stage-1 dataset {dataset_id}.funnel"),
            f"readiness Stage-1 dataset {dataset_id}.funnel",
        )
        if row.get("funnelSha256") != funnel["funnelSha256"]:
            raise BeatCellReadinessError(f"Readiness Stage-1 dataset {dataset_id} funnel hash is stale.")
        for field in _FUNNEL_FIELDS:
            dataset_count_sum[field] += int(funnel["counts"][field])
            dataset_duration_sum[field] += int(funnel["durationMilliseconds"][field])
    if make_funnel(dataset_count_sum, dataset_duration_sum) != aggregate_admission:
        raise BeatCellReadinessError("Stage-1 dataset funnels do not sum exactly to aggregate.")

    guitar_admission = _mapping(admission.get("guitarset"), "readiness Stage-1 GuitarSet")
    _exact_fields(
        guitar_admission,
        {
            "trackCount",
            "funnel",
            "funnelSha256",
            "compSolo",
            "compSoloSetSha256",
            "roleSpecificGates",
        },
        "readiness Stage-1 GuitarSet",
    )
    guitar_funnel = _validated_admission_funnel(
        _mapping(guitar_admission.get("funnel"), "readiness Stage-1 GuitarSet funnel"),
        "readiness Stage-1 GuitarSet funnel",
    )
    if (
        guitar_admission.get("trackCount") != EXPECTED_DATASET_TRACK_COUNTS["guitarset"]
        or guitar_admission.get("funnelSha256") != guitar_funnel["funnelSha256"]
        or guitar_admission.get("roleSpecificGates") is not False
        or guitar_funnel != make_funnel(EXPECTED_STAGE1_GUITARSET_COUNT, EXPECTED_STAGE1_GUITARSET_DURATION_MS)
    ):
        raise BeatCellReadinessError("Readiness changed the exact Stage-1 GuitarSet aggregate funnel.")
    role_rows = list(_sequence(guitar_admission.get("compSolo"), "readiness Stage-1 GuitarSet roles"))
    if len(role_rows) != 2 or guitar_admission.get("compSoloSetSha256") != canonical_sha256(role_rows):
        raise BeatCellReadinessError("Readiness Stage-1 GuitarSet role set is stale.")
    role_count_sum = {field: 0 for field in _FUNNEL_FIELDS}
    role_duration_sum = {field: 0 for field in _FUNNEL_FIELDS}
    for role, raw_row in zip(GUITARSET_ROLES, role_rows, strict=True):
        row = _mapping(raw_row, f"readiness Stage-1 GuitarSet {role}")
        _exact_fields(
            row,
            {"guitarsetRole", "trackCount", "funnel", "funnelSha256", "rowSha256"},
            f"readiness Stage-1 GuitarSet {role}",
        )
        if (
            row.get("guitarsetRole") != role
            or row.get("trackCount") != EXPECTED_GUITARSET_ROLE_TRACK_COUNTS[role]
            or row.get("rowSha256") != canonical_sha256(_unsigned(row, "rowSha256"))
        ):
            raise BeatCellReadinessError(f"Readiness Stage-1 GuitarSet {role} provenance is stale.")
        funnel = _validated_admission_funnel(
            _mapping(row.get("funnel"), f"readiness Stage-1 GuitarSet {role}.funnel"),
            f"readiness Stage-1 GuitarSet {role}.funnel",
        )
        if (
            row.get("funnelSha256") != funnel["funnelSha256"]
            or funnel["counts"]["R"] != EXPECTED_GUITARSET_ROLE_REFERENCE_COUNTS[role]
            or funnel["durationMilliseconds"]["R"] != EXPECTED_GUITARSET_ROLE_REFERENCE_DURATION_MS[role]
        ):
            raise BeatCellReadinessError(f"Readiness Stage-1 GuitarSet {role} denominator is stale.")
        for field in _FUNNEL_FIELDS:
            role_count_sum[field] += int(funnel["counts"][field])
            role_duration_sum[field] += int(funnel["durationMilliseconds"][field])
    if make_funnel(role_count_sum, role_duration_sum) != guitar_funnel:
        raise BeatCellReadinessError("Stage-1 GuitarSet role funnels do not sum exactly to GuitarSet.")
    reference_audit = _mapping(
        admission.get("referenceEndpointReconciliationAudit"),
        "readiness Stage-1 referenceEndpointReconciliationAudit",
    )
    if admission.get("referenceEndpointReconciliationAuditSha256") != reference_audit.get(
        "auditSha256"
    ) or reference_audit.get("auditSha256") != canonical_sha256(_unsigned(reference_audit, "auditSha256")):
        raise BeatCellReadinessError("Stage-1 endpoint reconciliation admission hash is stale.")
    cutoff_record = _mapping(value.get("fixedDevelopmentCutoff"), "readiness.fixedDevelopmentCutoff")
    cutoff = _finite(
        cutoff_record.get("minimumProbabilityAtDescriptivePoint"),
        "readiness fixed descriptive cutoff",
    )
    if (
        cutoff_record.get("targetCoverage") != FIXED_TARGET_COVERAGE
        or not 0 <= cutoff <= 1
        or cutoff_record.get("isOperatingThreshold") is not False
        or cutoff_record.get("durationWeighted") is not False
    ):
        raise BeatCellReadinessError("Readiness changed the fixed 0.50 descriptive cutoff policy.")
    rows = _validate_public_rows(value, cutoff, feature_names)
    diagnostic_source = _validate_diagnostic_source(
        _mapping(value.get("diagnosticSource"), "readiness.diagnosticSource"),
        rows,
        feature_names,
        bindings,
    )
    _crosscheck_joined_stage1(rows, admission)
    eligible_projection = sorted(
        [
            {
                "trackId": row["trackId"],
                "cellIndex": row["cellIndex"],
                "durationMilliseconds": row["durationMilliseconds"],
                "sourceBeatCellSha256": row["sourceBeatCellSha256"],
                "stage1OutcomeRowSha256": row["stage1OutcomeRowSha256"],
                "classification": "C" if row["correct"] else "I",
                "datasetId": row["datasetId"],
                "role": row["role"],
                "guitarsetRole": row["guitarsetRole"],
                "confidenceGroupId": row["confidenceGroupId"],
                "sourceGroupTrackRowSha256": row["sourceGroupTrackRowSha256"],
                "predictionIdentitySha256": row["predictionIdentitySha256"],
                "audioLineageRowSha256": row["audioLineageRowSha256"],
            }
            for row in rows
        ],
        key=lambda row: (str(row["trackId"]), int(row["cellIndex"])),
    )
    if (
        admission.get("eligibleOutcomeCount") != len(eligible_projection)
        or admission.get("eligibleOutcomeDurationMilliseconds")
        != sum(int(row["durationMilliseconds"]) for row in eligible_projection)
        or admission.get("eligibleOutcomeBindingSetSha256") != canonical_sha256(eligible_projection)
    ):
        raise BeatCellReadinessError("Joined OOF rows changed an exact Stage-1 per-cell outcome binding.")
    curve = _precision_coverage(rows, authority["selectorCore"]["precisionCoverageTargets"])
    points = [point for point in curve if point["targetCoverage"] == FIXED_TARGET_COVERAGE]
    if (
        len(points) != 1
        or points[0]["minimumProbabilityAtDescriptivePoint"] != cutoff
        or cutoff_record.get("fixedPointSha256") != canonical_sha256(points[0])
    ):
        raise BeatCellReadinessError("Readiness cutoff does not reproduce the exact 0.50 tie-block point.")
    expected_cutoff_record = {
        "targetCoverage": FIXED_TARGET_COVERAGE,
        "minimumProbabilityAtDescriptivePoint": cutoff,
        "acceptanceRule": "probability >= minimumProbabilityAtDescriptivePoint; exact ties included",
        "isOperatingThreshold": False,
        "isPromotionDecision": False,
        "durationWeighted": False,
        "fixedPointSha256": canonical_sha256(points[0]),
    }
    if cutoff_record != expected_cutoff_record:
        raise BeatCellReadinessError("Readiness fixed-cutoff record changed an exact policy field.")
    expected_recomputed_evaluation = {
        "denominatorExampleCount": len(rows),
        "denominatorDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in rows),
        "groupBalancedLogLoss": _group_log_loss(rows),
        "groupBalancedBrierScore": _group_brier(rows),
        "groupBalancedAreaUnderRiskCoverage": _aurc(rows, group_weighted=True),
        "precisionCoverage": curve,
    }
    expected_stored_evaluation = {
        "estimand": BEAT_CELL_SELECTOR_ESTIMAND,
        "denominator": BEAT_CELL_SELECTOR_OOF_DENOMINATOR,
        "denominatorExampleCount": len(rows),
        "denominatorDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in rows),
        "groupBalancedLogLoss": expected_recomputed_evaluation["groupBalancedLogLoss"],
        "groupBalancedBrierScore": expected_recomputed_evaluation["groupBalancedBrierScore"],
        "groupBalancedAreaUnderRiskCoverage": expected_recomputed_evaluation["groupBalancedAreaUnderRiskCoverage"],
        "precisionCoveragePolicy": "fixed descriptive coverage targets; no operating threshold selected",
        "precisionCoverage": curve,
    }
    expected_metric_payload = {
        "selectorValidatorPassed": True,
        "storedEvaluation": expected_stored_evaluation,
        "storedEvaluationSha256": canonical_sha256(expected_stored_evaluation),
        "recomputedEvaluation": expected_recomputed_evaluation,
        "recomputedEvaluationSha256": canonical_sha256(expected_recomputed_evaluation),
        "denominatorsExact": True,
        "precisionCoverageCurveExact": True,
        "fixedPointSha256": canonical_sha256(points[0]),
    }
    expected_metric_audit = {
        **expected_metric_payload,
        "auditSha256": canonical_sha256(expected_metric_payload),
    }
    if value.get("storedMetricRecomputation") != expected_metric_audit:
        raise BeatCellReadinessError("Stored selector metric recomputation audit is stale.")
    aggregate, datasets, guitarset = _metrics_for_exact_strata(rows, admission)
    if (
        value.get("aggregate") != aggregate
        or value.get("datasets") != datasets
        or value.get("datasetSetSha256") != canonical_sha256(datasets)
        or value.get("guitarset") != guitarset
    ):
        raise BeatCellReadinessError("Readiness count/duration dataset or GuitarSet disclosures are stale.")
    gates = _build_readiness_gates(aggregate, guitarset)
    if value.get("gates") != gates or value.get("gateSetSha256") != canonical_sha256(gates):
        raise BeatCellReadinessError("Readiness gates failed exact count/duration recomputation.")
    if len(gates) != 15 or any("role:" in str(gate["gateId"]) for gate in gates):
        raise BeatCellReadinessError("Readiness must contain exactly 15 overall gates and no role gate.")
    diagnostics = _mapping(value.get("diagnostics"), "readiness.diagnostics")
    if value.get("diagnosticsSha256") != canonical_sha256(diagnostics):
        raise BeatCellReadinessError("Readiness diagnosticsSha256 is stale.")
    performance = _mapping(diagnostics.get("oofPerformance"), "diagnostics.oofPerformance")
    if performance.get("precisionCoverage") != curve:
        raise BeatCellReadinessError("Diagnostic tie-block curve failed exact recomputation.")
    _validate_diagnostic_recomputation(diagnostics, rows, admission, feature_names, diagnostic_source)

    count_audit = _mapping(value.get("countAudit"), "readiness.countAudit")
    duration_audit = _mapping(value.get("durationAudit"), "readiness.durationAudit")
    expected_count_payload = {
        **EXPECTED_STAGE1_AGGREGATE_COUNT,
        "joinedOofRowCount": len(rows),
        "identitiesReconciled": True,
    }
    expected_count_audit = {
        **expected_count_payload,
        "auditSha256": canonical_sha256(expected_count_payload),
    }
    expected_duration_payload = {
        "unit": "canonical-integer-milliseconds",
        **EXPECTED_STAGE1_AGGREGATE_DURATION_MS,
        "joinedOofDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in rows),
        "durationNeverUsedForTrainingOrCutoff": True,
        "identitiesReconciled": True,
    }
    expected_duration_audit = {
        **expected_duration_payload,
        "auditSha256": canonical_sha256(expected_duration_payload),
    }
    if count_audit != expected_count_audit or duration_audit != expected_duration_audit:
        raise BeatCellReadinessError("Readiness count/duration audit is stale.")
    reproduction = _mapping(value.get("reproduction"), "readiness.reproduction")
    expected_reproduction_payload = {
        "selectorArtifactValidationPassed": True,
        "readinessReproductionRefitCount": 1,
        "freshTrainingObjectEqual": True,
        "freshTrainingCanonicalEqual": True,
        "freshTrainingByteEqual": True,
        "reproducedSelectorSha256": bindings["selector"]["artifactSha256"],
        "isAnotherCandidate": False,
        "sameCycleRetryAllowed": False,
    }
    expected_reproduction = {
        **expected_reproduction_payload,
        "reproductionSha256": canonical_sha256(expected_reproduction_payload),
    }
    if reproduction != expected_reproduction:
        raise BeatCellReadinessError("Readiness reproduction proof is stale or is not exactly one refit.")
    one_shot = _mapping(value.get("oneShot"), "readiness.oneShot")
    expected_one_shot_payload = {
        "policy": recovery["oneShot"],
        "policySha256": canonical_sha256(recovery["oneShot"]),
        "newCycle": deepcopy(_RECOVERY_NEW_CYCLE_COUNTS),
        "cumulativeIncludingConsumedR4": deepcopy(_RECOVERY_CUMULATIVE_COUNTS),
        "sourceR4SameCycleRetryPerformed": False,
        "immutableR4ArtifactsReused": True,
        "sameCycleRetryAllowed": False,
        "stopAfterReadinessForIndependentAudit": True,
    }
    expected_one_shot = {
        **expected_one_shot_payload,
        "auditSha256": canonical_sha256(expected_one_shot_payload),
    }
    if one_shot != expected_one_shot:
        raise BeatCellReadinessError("Readiness one-shot policy is stale.")
    diagnostic_reasons = []
    if not any(row["correct"] for row in rows):
        diagnostic_reasons.append("diagnostics.correct-probability-quantiles-missing")
    if not any(not row["correct"] for row in rows):
        diagnostic_reasons.append("diagnostics.incorrect-probability-quantiles-missing")
    present_folds = {row["outerFold"] for row in rows}
    diagnostic_reasons.extend(
        f"diagnostics.outer-fold-{fold}-missing" for fold in range(OUTER_FOLD_COUNT) if fold not in present_folds
    )
    present_datasets = {row["datasetId"] for row in rows}
    diagnostic_reasons.extend(
        f"diagnostics.dataset-{dataset}-missing" for dataset in DATASET_IDS if dataset not in present_datasets
    )
    present_roles = {row["guitarsetRole"] for row in rows if row["datasetId"] == "guitarset"}
    diagnostic_reasons.extend(
        f"diagnostics.guitarset-{role}-role-missing" for role in GUITARSET_ROLES if role not in present_roles
    )
    failure_reasons = sorted(
        {*(f"gate.{gate['gateId']}" for gate in gates if gate["passed"] is not True), *diagnostic_reasons}
    )
    passed = not failure_reasons
    decision = _mapping(value.get("decision"), "readiness.decision")
    expected_decision_payload = {
        "validationPassed": True,
        "allStage1AdmissionsPassed": True,
        "allNumericGatesPassed": all(gate["passed"] is True for gate in gates),
        "mandatoryDiagnosticsComplete": not diagnostic_reasons,
        "failureReasons": failure_reasons,
        "developmentReadinessPassed": passed,
        "calibrationMayOpenOnce": passed,
        "automaticCalibrationAccess": False,
        "calibrationStatus": "may-open-once-after-independent-audit" if passed else "closed",
        "promotionEligible": False,
        "playerPlaybackAuthorized": False,
        "stopForIndependentAudit": True,
    }
    expected_decision = {
        **expected_decision_payload,
        "decisionSha256": canonical_sha256(expected_decision_payload),
    }
    if (
        decision != expected_decision
        or value.get("developmentReadinessPassed") is not passed
        or value.get("calibrationMayOpenOnce") is not passed
        or value.get("calibrationStatus") != expected_decision_payload["calibrationStatus"]
    ):
        raise BeatCellReadinessError("Readiness decision is stale or opens unauthorized scope.")
    return deepcopy(value)


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, name: str) -> None:
    absolute = _absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise BeatCellReadinessError(f"{name} may not contain symlinked path components.")


def _reject_constant(value: str) -> None:
    raise BeatCellReadinessError(f"JSON may not contain non-finite constant {value!r}.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise BeatCellReadinessError(f"JSON contains duplicate object key {key!r}.")
        output[key] = value
    return output


def _read_json(path: Path, name: str) -> tuple[dict[str, Any], bytes, os.stat_result]:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise BeatCellReadinessError(f"{name} must be an existing non-symlink JSON file.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise BeatCellReadinessError(f"{name} must be a regular file.")
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
        visible = os.stat(absolute, follow_symlinks=False)
    except OSError as error:
        raise BeatCellReadinessError(f"{name} changed while it was read.") from error
    if (visible.st_dev, visible.st_ino) != (opened.st_dev, opened.st_ino):
        raise BeatCellReadinessError(f"{name} changed while it was read.")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BeatCellReadinessError(f"Could not decode {name} as exact UTF-8 JSON.") from error
    return dict(_mapping(value, name)), raw, opened


def _canonical_file(value: Mapping[str, Any], raw: bytes, name: str) -> None:
    if _render_json(value) != raw:
        raise BeatCellReadinessError(f"{name} must use the exact canonical indented JSON rendering.")


def _directory_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _verify_directory_path(path: Path, descriptor: int, expected_inode: tuple[int, int]) -> None:
    try:
        visible = os.stat(_absolute(path), follow_symlinks=False)
    except OSError as error:
        raise BeatCellReadinessError("Readiness output parent changed during publication.") from error
    if (
        not stat.S_ISDIR(visible.st_mode)
        or _identity(visible) != expected_inode
        or _identity(os.fstat(descriptor)) != expected_inode
    ):
        raise BeatCellReadinessError("Readiness output parent path changed during publication.")


def _open_or_create_directory(path: Path) -> tuple[int, tuple[int, int]]:
    absolute = _absolute(path)
    descriptor = os.open(absolute.anchor, _directory_open_flags())
    try:
        for component in absolute.parts[1:]:
            if component in {"", ".", ".."}:
                raise BeatCellReadinessError("Readiness output parent contains an invalid path component.")
            try:
                os.mkdir(component, mode=0o755, dir_fd=descriptor)
            except FileExistsError:
                pass
            try:
                next_descriptor = os.open(component, _directory_open_flags(), dir_fd=descriptor)
            except OSError as error:
                raise BeatCellReadinessError(
                    "Readiness output parent contains a symlink or non-directory component."
                ) from error
            os.close(descriptor)
            descriptor = next_descriptor
        inode = _identity(os.fstat(descriptor))
        _verify_directory_path(absolute, descriptor, inode)
        return descriptor, inode
    except Exception:
        os.close(descriptor)
        raise


def _unlink_owned(parent_descriptor: int, name: str, expected_inode: tuple[int, int]) -> None:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError:
        return
    try:
        if _identity(os.fstat(descriptor)) == expected_inode:
            os.unlink(name, dir_fd=parent_descriptor)
    finally:
        os.close(descriptor)


def _unlink_all_owned_entries(parent_descriptor: int, expected_inode: tuple[int, int]) -> None:
    """Best-effort cleanup of every retained-parent link to our private inode."""

    try:
        names = os.listdir(parent_descriptor)
    except OSError:
        return
    for name in names:
        _unlink_owned(parent_descriptor, name, expected_inode)


def _verify_owned_entry(parent_descriptor: int, name: str, expected_inode: tuple[int, int]) -> None:
    try:
        visible = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as error:
        raise BeatCellReadinessError("Published readiness output name changed during publication.") from error
    if not stat.S_ISREG(visible.st_mode) or _identity(visible) != expected_inode:
        raise BeatCellReadinessError("Published readiness output name changed during publication.")


def _verify_input_unchanged(path: Path, expected_stat: os.stat_result, expected_raw: bytes, name: str) -> None:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise BeatCellReadinessError(f"{name} changed before readiness publication.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(expected_stat):
            raise BeatCellReadinessError(f"{name} changed before readiness publication.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if b"".join(chunks) != expected_raw:
            raise BeatCellReadinessError(f"{name} changed before readiness publication.")
    finally:
        os.close(descriptor)
    try:
        visible = os.stat(absolute, follow_symlinks=False)
    except OSError as error:
        raise BeatCellReadinessError(f"{name} changed before readiness publication.") from error
    if _identity(visible) != _identity(expected_stat):
        raise BeatCellReadinessError(f"{name} changed before readiness publication.")


def _publish_new_json(path: Path, value: Mapping[str, Any], *, precommit_check: Any) -> None:
    destination = _absolute(path)
    if destination.suffix.lower() != ".json":
        raise BeatCellReadinessError("Readiness output must be a JSON file.")
    parent_descriptor, parent_inode = _open_or_create_directory(destination.parent)
    temporary_name = f".{destination.name}.{secrets.token_hex(16)}.tmp"
    temporary_inode: tuple[int, int] | None = None
    linked_inode: tuple[int, int] | None = None
    rendered = _render_json(value)
    try:
        try:
            os.stat(destination.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise BeatCellReadinessError("Readiness output must be a new path.")
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_descriptor,
        )
        temporary_stat = os.fstat(descriptor)
        temporary_inode = _identity(temporary_stat)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        precommit_check()
        try:
            os.link(
                temporary_name,
                destination.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise BeatCellReadinessError("Readiness output was concurrently created.") from error
        linked_inode = temporary_inode
        precommit_check()
        _verify_owned_entry(parent_descriptor, destination.name, linked_inode)
        output_descriptor = os.open(
            destination.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
        try:
            if _identity(os.fstat(output_descriptor)) != linked_inode:
                raise BeatCellReadinessError("Published readiness output inode changed.")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(output_descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if b"".join(chunks) != rendered:
                raise BeatCellReadinessError("Published readiness output did not round-trip exactly.")
        finally:
            os.close(output_descriptor)
        _verify_owned_entry(parent_descriptor, destination.name, linked_inode)
        os.fsync(parent_descriptor)
        _verify_owned_entry(parent_descriptor, destination.name, linked_inode)
        _verify_directory_path(destination.parent, parent_descriptor, parent_inode)
        _verify_owned_entry(parent_descriptor, destination.name, linked_inode)
        published_inode = linked_inode
        _unlink_owned(parent_descriptor, temporary_name, published_inode)
        temporary_inode = None
        os.fsync(parent_descriptor)
        _verify_directory_path(destination.parent, parent_descriptor, parent_inode)
        _verify_owned_entry(parent_descriptor, destination.name, published_inode)
    except BaseException:
        owned_inode = linked_inode if linked_inode is not None else temporary_inode
        if owned_inode is not None:
            _unlink_owned(parent_descriptor, destination.name, owned_inode)
            _unlink_all_owned_entries(parent_descriptor, owned_inode)
        raise
    finally:
        if temporary_inode is not None:
            _unlink_owned(parent_descriptor, temporary_name, temporary_inode)
        os.close(parent_descriptor)


def run_beat_cell_readiness() -> dict[str, Any]:
    """Read immutable R4 inputs and publish only the exact R5 recovery path."""

    authority = _authority_contract()
    recovery = _recovery_contract()
    implementation_authorization = dict(_implementation_authorization_receipt())
    authorization_path = Path(RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH)
    authorization_on_disk, authorization_raw, authorization_stat = _read_json(
        authorization_path,
        "exact R5 implementation authorization",
    )
    if authorization_on_disk != implementation_authorization:
        raise BeatCellReadinessError("The exact R5 implementation authorization changed during admission.")
    _canonical_file(
        authorization_on_disk,
        authorization_raw,
        "exact R5 implementation authorization",
    )
    immutable = recovery["immutableInputs"]
    stage1_path = Path(immutable["stage1"]["path"])
    examples_path = Path(immutable["examples"]["path"])
    selector_path = Path(immutable["selector"]["path"])
    output_path = Path(recovery["output"]["readinessReport"])
    consumed_r4_output = _absolute(Path(authority["outputPaths"]["readinessReport"]))
    inputs = [_absolute(stage1_path), _absolute(examples_path), _absolute(selector_path)]
    output = _absolute(output_path)
    if len(set(inputs)) != 3 or output in set(inputs) or output == consumed_r4_output:
        raise BeatCellReadinessError("Immutable R4 sources and the R5 destination must be mutually disjoint.")
    if consumed_r4_output.exists() or consumed_r4_output.is_symlink():
        raise BeatCellReadinessError("The consumed R4 readiness path must remain unpublished and untouched.")
    _reject_symlink_components(output.parent, "readiness output parent")
    if output.exists() or output.is_symlink():
        raise BeatCellReadinessError("Readiness output must be a new, non-symlink path.")

    stage1, stage1_raw, stage1_stat = _read_json(stage1_path, "exact Stage-1 artifact")
    examples, examples_raw, examples_stat = _read_json(examples_path, "exact examples artifact")
    selector, selector_raw, selector_stat = _read_json(selector_path, "exact selector artifact")
    _sealed_preflight(stage1, examples, selector)
    for value, raw, name in (
        (stage1, stage1_raw, "exact Stage-1 artifact"),
        (examples, examples_raw, "exact examples artifact"),
        (selector, selector_raw, "exact selector artifact"),
    ):
        _canonical_file(value, raw, name)
    for name, value, raw in (
        ("stage1", stage1, stage1_raw),
        ("examples", examples, examples_raw),
        ("selector", selector, selector_raw),
    ):
        expected = immutable[name]
        if (
            _sha256_bytes(raw) != expected["fileSha256"]
            or canonical_sha256(value) != expected["canonicalSha256"]
            or value.get("artifactSha256") != expected["artifactSha256"]
        ):
            raise BeatCellReadinessError(f"The exact immutable R4 {name} receipt drifted.")

    artifact = evaluate_beat_cell_readiness(stage1, examples, selector)
    if artifact["implementationAuthorizationBinding"] != _build_implementation_authorization_binding(
        implementation_authorization
    ):
        raise BeatCellReadinessError("The implementation authorization changed during readiness evaluation.")
    for name, raw in (
        ("stage1", stage1_raw),
        ("examples", examples_raw),
        ("selector", selector_raw),
    ):
        if artifact["inputBindings"][name]["fileSha256"] != _sha256_bytes(raw):
            raise BeatCellReadinessError(f"Readiness {name} raw-file binding drifted before publication.")

    def verify_inputs_at_commit() -> None:
        if consumed_r4_output.exists() or consumed_r4_output.is_symlink():
            raise BeatCellReadinessError("The consumed R4 readiness path changed before R5 publication.")
        if dict(_implementation_authorization_receipt()) != implementation_authorization:
            raise BeatCellReadinessError("The implementation authorization changed before R5 publication.")
        _verify_input_unchanged(
            authorization_path,
            authorization_stat,
            authorization_raw,
            "exact R5 implementation authorization",
        )
        _verify_input_unchanged(stage1_path, stage1_stat, stage1_raw, "exact Stage-1 artifact")
        _verify_input_unchanged(examples_path, examples_stat, examples_raw, "exact examples artifact")
        _verify_input_unchanged(selector_path, selector_stat, selector_raw, "exact selector artifact")

    _publish_new_json(output, artifact, precommit_check=verify_inputs_at_commit)
    return deepcopy(artifact)


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Run the one preregistered beat-cell R5 readiness-only recovery at exact committed paths. "
            "No input, output, cutoff, gate, fold, feature, dataset, or retry override is accepted."
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    _parser().parse_args(argv)
    artifact = run_beat_cell_readiness()
    print(
        json.dumps(
            {
                "artifactSha256": artifact["artifactSha256"],
                "developmentReadinessPassed": artifact["developmentReadinessPassed"],
                "calibrationMayOpenOnce": artifact["calibrationMayOpenOnce"],
                "automaticCalibrationAccess": False,
                "playerPlaybackAuthorized": False,
                "output": artifact["publication"]["outputPath"],
                "stopForIndependentAudit": True,
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
    )
    return 0


__all__ = [
    "BEAT_CELL_READINESS_RUBRIC",
    "BEAT_CELL_READINESS_RUBRIC_SHA256",
    "BEAT_CELL_READINESS_SCHEMA",
    "BeatCellReadinessError",
    "evaluate_beat_cell_readiness",
    "main",
    "run_beat_cell_readiness",
    "validate_beat_cell_readiness_artifact",
]
