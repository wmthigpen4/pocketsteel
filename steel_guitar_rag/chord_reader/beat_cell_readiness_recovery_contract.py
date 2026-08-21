"""Exact authority for the one readiness-only recovery evaluation.

The source Stage-2 authority remains R4.  This module opens only tracked
governance files; it never opens experiment inputs or outputs.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Any, Mapping

from .bar_promotion import canonical_sha256
from .beat_cell_stage2_contract import (
    BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    BEAT_CELL_ONE_SHOT_PROJECTION_SHA256,
    BEAT_CELL_READINESS_PROJECTION_SHA256,
    BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
    BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE,
    BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_RELATIVE_PATH,
    BEAT_CELL_STAGE_A_PROJECTION_SHA256,
    BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    _sealed_read,
    _strict_json,
    load_beat_cell_stage2_authority,
)


READINESS_RECOVERY_AUTHORITY_SCHEMA = "chord_runtime_beat_cell_stage2_readiness_recovery_preregistration_v1"
READINESS_RECOVERY_ID = "beat-cell-stage2-r5-readiness-only"
READINESS_RECOVERY_AUTHORITY_RELATIVE_PATH = Path(
    "docs/handoffs/task-completions/2026-08-21-1244-20-beat-cell-stage2-r5-readiness-only-preregistration.json"
)
READINESS_RECOVERY_AUTHORITY_FILE_SHA256 = "ffac2f6208db2c837875c1568575fe482b5b372ed48f0af648e127cf93da07eb"
READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256 = "dc730b76e4dffa21e816ab484358dbbb14d8475ceca5f955d2c02ee1641d823d"
READINESS_RECOVERY_IMMUTABLE_INPUTS_SHA256 = "93cfebceb282eeebacc37436514165955d49198e58d3473a5fdba7eadc677985"
READINESS_RECOVERY_AUTHORIZATION_SCHEMA = (
    "chord_runtime_beat_cell_stage2_readiness_recovery_implementation_authorization_v1"
)
READINESS_RECOVERY_AUTHORIZATION_RELATIVE_PATH = Path(
    "docs/handoffs/task-completions/"
    "2026-08-21-1330-20-beat-cell-stage2-r5-readiness-only-implementation-authorization.json"
)
READINESS_RECOVERY_OUTPUT = Path(
    "/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/"
    "winner-seven-selector-development-v1/beat-cell-stage2-r5-readiness-only/readiness/report.json"
)
READINESS_RECOVERY_FAILURE_RECEIPT_RELATIVE_PATH = Path(
    "docs/handoffs/task-completions/2026-08-21-1243-20-beat-cell-stage2-r4-readiness-failure.md"
)
READINESS_RECOVERY_FAILURE_RECEIPT_FILE_SHA256 = "941d6d8b8248ca691255b9e015100974d411b80248901bbac0a0a974dae46c50"
READINESS_RECOVERY_IMPLEMENTATION_HANDOFF_RELATIVE_PATH = Path(
    "docs/handoffs/task-completions/2026-08-21-1329-20-beat-cell-stage2-r5-readiness-only-implementation.md"
)
READINESS_SOURCE_IMPLEMENTATION_HEAD = "edec952077c42c31bed280cb7e3994ec335a318e"
READINESS_SOURCE_INPUTS_PROJECTION_SHA256 = "d236e26249cfcf616e4ca95cb199f231b9509c212bdbdb27b947f32028a2c185"
READINESS_SOURCE_OUTPUT_PATHS_PROJECTION_SHA256 = "a8b3d76cd0adc5e656ce3f53466d352e83a3b048e78a645e72db0482413981ce"
READINESS_RECOVERY_RUBRIC_SHA256 = "5b5d25fae2271eed1283e2a5c17a3f77b1b0508a2ff330c85bdf1efc9c7a7236"

_TOP_LEVEL_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "recoveryId",
        "sourceCycle",
        "consumedFailure",
        "immutableInputs",
        "output",
        "frozenPolicy",
        "implementation",
        "oneShot",
        "forbiddenAccess",
    }
)
_SOURCE_PROJECTIONS = {
    "sourceInputs": READINESS_SOURCE_INPUTS_PROJECTION_SHA256,
    "outputPaths": READINESS_SOURCE_OUTPUT_PATHS_PROJECTION_SHA256,
    "stageA": BEAT_CELL_STAGE_A_PROJECTION_SHA256,
    "featureMath": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    "stageB": BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    "selectorCore": BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
    "readiness": BEAT_CELL_READINESS_PROJECTION_SHA256,
    "oneShot": BEAT_CELL_ONE_SHOT_PROJECTION_SHA256,
}
_IMMUTABLE_INPUT_FIELDS = frozenset({"stage1", "featureSet", "examples", "selector"})
_FORBIDDEN_FIELDS = frozenset(
    {
        "calibration",
        "test",
        "confirmation",
        "player",
        "publicSong",
        "browserRuntime",
        "travis",
        "thresholdSelection",
        "promotion",
        "deployment",
    }
)
_IMPLEMENTATION_FIELDS = frozenset(
    {
        "allowedChangedFiles",
        "permittedSemanticChange",
        "affectedIntegerFeatureNames",
        "fixOnlyReadinessModuleFileSha256",
        "fixOnlyReadinessTestFileSha256",
        "unchangedCliFileSha256",
        "finalReadinessModuleFileSha256",
        "finalRecoveryContractFileSha256",
        "finalReadinessTestFileSha256",
        "finalImplementationCommit",
        "executionAuthorized",
    }
)
_ONE_SHOT_FIELDS = frozenset(
    {
        "newCycle",
        "cumulativeIncludingConsumedR4",
        "immutableR4ArtifactsMustBeReused",
        "featureExamplesSelectorRegenerationAllowed",
        "stopAfterReadinessForIndependentAudit",
    }
)
_ALLOWED_CHANGED_FILES = [
    "steel_guitar_rag/chord_reader/beat_cell_readiness.py",
    "steel_guitar_rag/chord_reader/beat_cell_readiness_recovery_contract.py",
    "scripts/chord_beat_cell_readiness.py",
    "tests/test_chord_reader_beat_cell_readiness.py",
    "docs/handoffs/task-completions/2026-08-21-1243-20-beat-cell-stage2-r4-readiness-failure.md",
    "docs/handoffs/task-completions/2026-08-21-1244-20-beat-cell-stage2-r5-readiness-only-preregistration.json",
    "docs/handoffs/task-completions/2026-08-21-1329-20-beat-cell-stage2-r5-readiness-only-implementation.md",
    "docs/handoffs/task-completions/"
    "2026-08-21-1330-20-beat-cell-stage2-r5-readiness-only-implementation-authorization.json",
]
_AFFECTED_INTEGER_FEATURE_NAMES = [
    "predictionTransitionCount",
    "productFamilyNone",
    "productFamilyMajor",
    "productFamilyMinor",
    "productFamilyDominant",
    "productFamilyMinorSeventh",
]
_AUTHORIZATION_FIELDS = frozenset(
    {
        "schemaVersion",
        "recoveryId",
        "split",
        "executionAuthorized",
        "baseAuthority",
        "consumedFailure",
        "implementation",
        "scope",
        "forbiddenAccess",
        "independentAudit",
        "userAuthorization",
        "payloadSha256",
    }
)
_AUTHORIZATION_FILE_PATHS = [
    "steel_guitar_rag/chord_reader/beat_cell_readiness.py",
    "steel_guitar_rag/chord_reader/beat_cell_readiness_recovery_contract.py",
    "scripts/chord_beat_cell_readiness.py",
    "tests/test_chord_reader_beat_cell_readiness.py",
]


class BeatCellReadinessRecoveryContractError(ValueError):
    """The tracked readiness-only recovery authority is not exact."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def recovery_authority_path() -> Path:
    return _repo_root() / READINESS_RECOVERY_AUTHORITY_RELATIVE_PATH


def recovery_authorization_path() -> Path:
    return _repo_root() / READINESS_RECOVERY_AUTHORIZATION_RELATIVE_PATH


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BeatCellReadinessRecoveryContractError(f"{name} must be an object.")
    return value


def _exact(value: Mapping[str, Any], fields: set[str] | frozenset[str], name: str) -> None:
    if set(value) != set(fields):
        raise BeatCellReadinessRecoveryContractError(f"{name} fields are not exact.")


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise BeatCellReadinessRecoveryContractError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _validate_source_cycle(value: Mapping[str, Any], source_authority: Mapping[str, Any]) -> None:
    _exact(
        value,
        {
            "recoveryMode",
            "authorityPath",
            "authorityFileSha256",
            "authorityCanonicalSha256",
            "implementationHead",
            "projectionSha256",
        },
        "sourceCycle",
    )
    projections = _mapping(value.get("projectionSha256"), "sourceCycle.projectionSha256")
    _exact(projections, set(_SOURCE_PROJECTIONS), "sourceCycle.projectionSha256")
    observed = {name: canonical_sha256(source_authority[name]) for name in _SOURCE_PROJECTIONS}
    if (
        value.get("recoveryMode") != "reuse-immutable-r4-feature-examples-selector-no-regeneration"
        or value.get("authorityPath") != str(BEAT_CELL_STAGE2_AUTHORITY_RELATIVE_PATH)
        or value.get("authorityFileSha256") != BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256
        or value.get("authorityCanonicalSha256") != BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256
        or value.get("implementationHead") != READINESS_SOURCE_IMPLEMENTATION_HEAD
        or dict(projections) != _SOURCE_PROJECTIONS
        or observed != _SOURCE_PROJECTIONS
    ):
        raise BeatCellReadinessRecoveryContractError("sourceCycle does not bind the exact R4 source cycle.")


def _validate_failure(value: Mapping[str, Any]) -> None:
    _exact(
        value,
        {
            "receiptPath",
            "receiptFileSha256",
            "officialExitCode",
            "officialStdoutReceiptEmitted",
            "terminalError",
            "readinessEvaluationCount",
            "readinessReproductionRefitCount",
            "readinessReportPublished",
            "sameCycleRetryAllowed",
        },
        "consumedFailure",
    )
    receipt_path = _repo_root() / READINESS_RECOVERY_FAILURE_RECEIPT_RELATIVE_PATH
    receipt = _sealed_read(receipt_path, "R4 readiness failure receipt")
    if (
        value.get("receiptPath") != str(READINESS_RECOVERY_FAILURE_RECEIPT_RELATIVE_PATH)
        or value.get("receiptFileSha256") != READINESS_RECOVERY_FAILURE_RECEIPT_FILE_SHA256
        or hashlib.sha256(receipt).hexdigest() != READINESS_RECOVERY_FAILURE_RECEIPT_FILE_SHA256
        or value.get("officialExitCode") != 1
        or value.get("officialStdoutReceiptEmitted") is not False
        or value.get("terminalError") != "A joined row ordered feature vector disagrees with featureValuesSha256."
        or value.get("readinessEvaluationCount") != 1
        or value.get("readinessReproductionRefitCount") != 1
        or value.get("readinessReportPublished") is not False
        or value.get("sameCycleRetryAllowed") is not False
    ):
        raise BeatCellReadinessRecoveryContractError("consumedFailure is not the exact terminal R4 receipt.")


def _validate_immutable_inputs(value: Mapping[str, Any], source_authority: Mapping[str, Any]) -> None:
    _exact(value, _IMMUTABLE_INPUT_FIELDS, "immutableInputs")
    if canonical_sha256(value) != READINESS_RECOVERY_IMMUTABLE_INPUTS_SHA256:
        raise BeatCellReadinessRecoveryContractError("immutableInputs projection changed.")
    stage1 = _mapping(value.get("stage1"), "immutableInputs.stage1")
    _exact(stage1, {"path", "fileSha256", "canonicalSha256", "artifactSha256"}, "immutableInputs.stage1")
    source_stage1 = _mapping(source_authority["sourceInputs"]["stage1Report"], "source Stage-1")
    if dict(stage1) != {key: source_stage1[key] for key in ("path", "fileSha256", "canonicalSha256", "artifactSha256")}:
        raise BeatCellReadinessRecoveryContractError("immutable Stage-1 binding changed.")
    output_paths = _mapping(source_authority.get("outputPaths"), "source outputPaths")
    feature = _mapping(value.get("featureSet"), "immutableInputs.featureSet")
    _exact(
        feature,
        {
            "manifestPath",
            "manifestFileSha256",
            "manifestCanonicalSha256",
            "artifactSha256",
            "summarySetSha256",
            "featureRowSetSha256",
        },
        "immutableInputs.featureSet",
    )
    examples = _mapping(value.get("examples"), "immutableInputs.examples")
    _exact(
        examples,
        {"path", "fileSha256", "canonicalSha256", "artifactSha256", "exampleCount", "exampleDurationMilliseconds"},
        "immutableInputs.examples",
    )
    selector = _mapping(value.get("selector"), "immutableInputs.selector")
    _exact(selector, {"path", "fileSha256", "canonicalSha256", "artifactSha256"}, "immutableInputs.selector")
    if (
        feature.get("manifestPath") != output_paths.get("featureSetManifest")
        or examples.get("path") != output_paths.get("examplesArtifact")
        or selector.get("path") != output_paths.get("selectorArtifact")
        or examples.get("exampleCount") != 9376
        or examples.get("exampleDurationMilliseconds") != 5074349
    ):
        raise BeatCellReadinessRecoveryContractError("immutable R4 output paths or denominators changed.")
    for name, section in (("featureSet", feature), ("examples", examples), ("selector", selector)):
        for field, item in section.items():
            if field.endswith("Sha256"):
                _digest(item, f"immutableInputs.{name}.{field}")


def validate_readiness_recovery_authority(authority: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(authority, Mapping):
        raise BeatCellReadinessRecoveryContractError("Readiness recovery authority must be an object.")
    value = deepcopy(dict(authority))
    _exact(value, _TOP_LEVEL_FIELDS, "readiness recovery authority")
    if (
        value.get("schemaVersion") != READINESS_RECOVERY_AUTHORITY_SCHEMA
        or value.get("split") != "development"
        or value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
        or value.get("recoveryId") != READINESS_RECOVERY_ID
        or canonical_sha256(value) != READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256
    ):
        raise BeatCellReadinessRecoveryContractError("Readiness recovery envelope or canonical hash changed.")
    source_authority = load_beat_cell_stage2_authority()
    _validate_source_cycle(_mapping(value.get("sourceCycle"), "sourceCycle"), source_authority)
    _validate_failure(_mapping(value.get("consumedFailure"), "consumedFailure"))
    _validate_immutable_inputs(_mapping(value.get("immutableInputs"), "immutableInputs"), source_authority)

    output = _mapping(value.get("output"), "output")
    _exact(output, {"readinessReport", "publicationMode", "mustBeNew", "callerPathOverrideAllowed"}, "output")
    if (
        output.get("readinessReport") != str(READINESS_RECOVERY_OUTPUT)
        or output.get("publicationMode") != BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE
        or output.get("mustBeNew") is not True
        or output.get("callerPathOverrideAllowed") is not False
    ):
        raise BeatCellReadinessRecoveryContractError("Recovery output policy changed.")

    policy = _mapping(value.get("frozenPolicy"), "frozenPolicy")
    _exact(
        policy,
        {
            "readinessProjectionSha256",
            "oneShotProjectionSha256",
            "readinessRubricSha256",
            "fixedTargetCoverage",
            "gateCount",
            "gatePolicy",
            "cutoffPolicy",
            "featureFoldWeightDatasetSelectorChangeAllowed",
            "thresholdSelectionAllowed",
            "calibrationAccessDuringRecoveryAllowed",
        },
        "frozenPolicy",
    )
    if (
        policy.get("readinessProjectionSha256") != BEAT_CELL_READINESS_PROJECTION_SHA256
        or policy.get("oneShotProjectionSha256") != BEAT_CELL_ONE_SHOT_PROJECTION_SHA256
        or policy.get("readinessRubricSha256") != READINESS_RECOVERY_RUBRIC_SHA256
        or policy.get("fixedTargetCoverage") != 0.5
        or policy.get("gateCount") != 15
        or policy.get("gatePolicy") != "exact-r4-readiness-count-duration-group-balanced-wilson-gates-no-change"
        or policy.get("cutoffPolicy")
        != "minimumProbabilityAtDescriptivePoint-at-targetCoverage-0.50-inclusive-ties-not-operating-threshold"
        or policy.get("featureFoldWeightDatasetSelectorChangeAllowed") is not False
        or policy.get("thresholdSelectionAllowed") is not False
        or policy.get("calibrationAccessDuringRecoveryAllowed") is not False
    ):
        raise BeatCellReadinessRecoveryContractError("Frozen readiness policy changed.")

    implementation = _mapping(value.get("implementation"), "implementation")
    _exact(implementation, _IMPLEMENTATION_FIELDS, "implementation")
    if (
        implementation.get("allowedChangedFiles") != _ALLOWED_CHANGED_FILES
        or implementation.get("permittedSemanticChange")
        != "preserve-sealed-json-int-float-types-through-ordered-feature-vector-and-standalone-validation"
        or implementation.get("affectedIntegerFeatureNames") != _AFFECTED_INTEGER_FEATURE_NAMES
        or implementation.get("fixOnlyReadinessModuleFileSha256")
        != "225773bd6fc32c43b1308afa46b1648317b3200c1a5cb32c49ad18c584505306"
        or implementation.get("fixOnlyReadinessTestFileSha256")
        != "4bc06c16ef91bc166998af0531d68adf442e5536b8fa47e1f3b0a1b3e8a67d76"
        or implementation.get("unchangedCliFileSha256")
        != "cc0c68ff11b654f8e17f4dc9c8a746c88e543be14d8188e2cf1189304e9b77dd"
        or implementation.get("executionAuthorized") is not False
        or any(
            implementation.get(field) is not None
            for field in (
                "finalReadinessModuleFileSha256",
                "finalRecoveryContractFileSha256",
                "finalReadinessTestFileSha256",
                "finalImplementationCommit",
            )
        )
    ):
        raise BeatCellReadinessRecoveryContractError("Recovery implementation remains non-executable and exact.")

    one_shot = _mapping(value.get("oneShot"), "oneShot")
    _exact(one_shot, _ONE_SHOT_FIELDS, "oneShot")
    new_cycle = _mapping(one_shot.get("newCycle"), "oneShot.newCycle")
    cumulative = _mapping(one_shot.get("cumulativeIncludingConsumedR4"), "oneShot.cumulative")
    if dict(new_cycle) != {
        "featureSetBuildCount": 0,
        "examplesBuildCount": 0,
        "selectorCandidateCount": 0,
        "readinessEvaluationCount": 1,
        "readinessReproductionRefitCount": 1,
        "sameCycleRetryAllowed": False,
    } or dict(cumulative) != {
        "featureSetBuildCount": 1,
        "examplesBuildCount": 1,
        "selectorCandidateCount": 1,
        "readinessEvaluationCount": 2,
        "readinessReproductionRefitCount": 2,
    }:
        raise BeatCellReadinessRecoveryContractError("Recovery one-shot counts changed.")
    if (
        one_shot.get("immutableR4ArtifactsMustBeReused") is not True
        or one_shot.get("featureExamplesSelectorRegenerationAllowed") is not False
        or one_shot.get("stopAfterReadinessForIndependentAudit") is not True
    ):
        raise BeatCellReadinessRecoveryContractError("Recovery reuse or stop policy changed.")

    forbidden = _mapping(value.get("forbiddenAccess"), "forbiddenAccess")
    _exact(forbidden, _FORBIDDEN_FIELDS, "forbiddenAccess")
    if any(item is not False for item in forbidden.values()):
        raise BeatCellReadinessRecoveryContractError("A forbidden recovery surface was opened.")
    return value


def load_readiness_recovery_authority() -> dict[str, Any]:
    raw = _sealed_read(recovery_authority_path(), "readiness recovery authority")
    if hashlib.sha256(raw).hexdigest() != READINESS_RECOVERY_AUTHORITY_FILE_SHA256:
        raise BeatCellReadinessRecoveryContractError("Readiness recovery authority file hash changed.")
    return validate_readiness_recovery_authority(_strict_json(raw, "readiness recovery authority"))


def validate_readiness_recovery_authorization(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the separate, post-freeze execution receipt and live tracked bytes."""

    if not isinstance(receipt, Mapping):
        raise BeatCellReadinessRecoveryContractError("Readiness recovery authorization must be an object.")
    value = deepcopy(dict(receipt))
    _exact(value, _AUTHORIZATION_FIELDS, "readiness recovery authorization")
    payload = {key: item for key, item in value.items() if key != "payloadSha256"}
    if (
        value.get("schemaVersion") != READINESS_RECOVERY_AUTHORIZATION_SCHEMA
        or value.get("recoveryId") != READINESS_RECOVERY_ID
        or value.get("split") != "development"
        or value.get("executionAuthorized") is not True
        or value.get("payloadSha256") != canonical_sha256(payload)
    ):
        raise BeatCellReadinessRecoveryContractError("Readiness recovery authorization envelope is not exact.")

    base = _mapping(value.get("baseAuthority"), "authorization.baseAuthority")
    _exact(base, {"path", "fileSha256", "canonicalSha256"}, "authorization.baseAuthority")
    failure = _mapping(value.get("consumedFailure"), "authorization.consumedFailure")
    _exact(failure, {"path", "fileSha256"}, "authorization.consumedFailure")
    if dict(base) != {
        "path": str(READINESS_RECOVERY_AUTHORITY_RELATIVE_PATH),
        "fileSha256": READINESS_RECOVERY_AUTHORITY_FILE_SHA256,
        "canonicalSha256": READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256,
    } or dict(failure) != {
        "path": str(READINESS_RECOVERY_FAILURE_RECEIPT_RELATIVE_PATH),
        "fileSha256": READINESS_RECOVERY_FAILURE_RECEIPT_FILE_SHA256,
    }:
        raise BeatCellReadinessRecoveryContractError("Authorization changed a base governance binding.")

    implementation = _mapping(value.get("implementation"), "authorization.implementation")
    _exact(
        implementation,
        {"implementationCommit", "files", "handoffPath", "handoffFileSha256"},
        "authorization.implementation",
    )
    commit = implementation.get("implementationCommit")
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
    ):
        raise BeatCellReadinessRecoveryContractError("Authorization implementation commit is not exact.")
    files = implementation.get("files")
    if not isinstance(files, list) or len(files) != len(_AUTHORIZATION_FILE_PATHS):
        raise BeatCellReadinessRecoveryContractError("Authorization implementation file inventory changed.")
    observed_paths: list[str] = []
    for index, row_value in enumerate(files):
        row = _mapping(row_value, f"authorization.implementation.files[{index}]")
        _exact(row, {"path", "fileSha256"}, f"authorization.implementation.files[{index}]")
        expected_path = _AUTHORIZATION_FILE_PATHS[index]
        expected_digest = _digest(row.get("fileSha256"), f"authorization file {expected_path}")
        if row.get("path") != expected_path:
            raise BeatCellReadinessRecoveryContractError("Authorization implementation file order changed.")
        raw = _sealed_read(_repo_root() / expected_path, f"authorized implementation file {expected_path}")
        if hashlib.sha256(raw).hexdigest() != expected_digest:
            raise BeatCellReadinessRecoveryContractError("An authorized implementation file changed.")
        observed_paths.append(expected_path)
    if observed_paths != _AUTHORIZATION_FILE_PATHS or len(set(observed_paths)) != len(observed_paths):
        raise BeatCellReadinessRecoveryContractError("Authorization implementation files are not exact.")
    handoff_path = implementation.get("handoffPath")
    handoff_digest = _digest(implementation.get("handoffFileSha256"), "authorization handoffFileSha256")
    if handoff_path != str(READINESS_RECOVERY_IMPLEMENTATION_HANDOFF_RELATIVE_PATH):
        raise BeatCellReadinessRecoveryContractError("Authorization implementation handoff path changed.")
    handoff_raw = _sealed_read(
        _repo_root() / READINESS_RECOVERY_IMPLEMENTATION_HANDOFF_RELATIVE_PATH,
        "readiness recovery implementation handoff",
    )
    if hashlib.sha256(handoff_raw).hexdigest() != handoff_digest:
        raise BeatCellReadinessRecoveryContractError("Authorization implementation handoff changed.")

    scope = _mapping(value.get("scope"), "authorization.scope")
    _exact(
        scope,
        {
            "outputPath",
            "publicationMode",
            "newCycle",
            "cumulativeIncludingConsumedR4",
            "sameCycleRetryAllowed",
            "stopAfterReadinessForIndependentAudit",
        },
        "authorization.scope",
    )
    new_cycle = _mapping(scope.get("newCycle"), "authorization.scope.newCycle")
    cumulative = _mapping(
        scope.get("cumulativeIncludingConsumedR4"),
        "authorization.scope.cumulativeIncludingConsumedR4",
    )
    count_fields = {
        "featureSetBuildCount",
        "examplesBuildCount",
        "selectorCandidateCount",
        "readinessEvaluationCount",
        "readinessReproductionRefitCount",
    }
    _exact(new_cycle, count_fields, "authorization.scope.newCycle")
    _exact(cumulative, count_fields, "authorization.scope.cumulativeIncludingConsumedR4")
    if any(type(item) is not int for item in (*new_cycle.values(), *cumulative.values())):
        raise BeatCellReadinessRecoveryContractError("Authorization execution counts must be exact integers.")
    if (
        scope.get("outputPath") != str(READINESS_RECOVERY_OUTPUT)
        or scope.get("publicationMode") != BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE
        or dict(new_cycle)
        != {
            "featureSetBuildCount": 0,
            "examplesBuildCount": 0,
            "selectorCandidateCount": 0,
            "readinessEvaluationCount": 1,
            "readinessReproductionRefitCount": 1,
        }
        or dict(cumulative)
        != {
            "featureSetBuildCount": 1,
            "examplesBuildCount": 1,
            "selectorCandidateCount": 1,
            "readinessEvaluationCount": 2,
            "readinessReproductionRefitCount": 2,
        }
        or scope.get("sameCycleRetryAllowed") is not False
        or scope.get("stopAfterReadinessForIndependentAudit") is not True
    ):
        raise BeatCellReadinessRecoveryContractError("Authorization execution scope changed.")

    forbidden = _mapping(value.get("forbiddenAccess"), "authorization.forbiddenAccess")
    _exact(forbidden, _FORBIDDEN_FIELDS, "authorization.forbiddenAccess")
    if any(item is not False for item in forbidden.values()):
        raise BeatCellReadinessRecoveryContractError("Authorization opened a forbidden surface.")
    audit = _mapping(value.get("independentAudit"), "authorization.independentAudit")
    _exact(audit, {"verdict", "noP0P1", "qaPassed", "auditorCount"}, "authorization.independentAudit")
    if (
        audit.get("verdict") != "GO"
        or audit.get("noP0P1") is not True
        or audit.get("qaPassed") is not True
        or not isinstance(audit.get("auditorCount"), int)
        or isinstance(audit.get("auditorCount"), bool)
        or audit["auditorCount"] < 2
    ):
        raise BeatCellReadinessRecoveryContractError("Authorization lacks the required independent GO audit.")
    user = _mapping(value.get("userAuthorization"), "authorization.userAuthorization")
    _exact(
        user,
        {"explicitlyApproved", "approvalScope", "approvalRecordedAt"},
        "authorization.userAuthorization",
    )
    approved_at = user.get("approvalRecordedAt")
    try:
        parsed_approval = datetime.fromisoformat(approved_at) if isinstance(approved_at, str) else None
    except ValueError:
        parsed_approval = None
    if (
        user.get("explicitlyApproved") is not True
        or user.get("approvalScope") != "one-r5-readiness-only-evaluation-and-one-reproduction-refit-no-retry"
        or parsed_approval is None
        or parsed_approval.tzinfo is None
    ):
        raise BeatCellReadinessRecoveryContractError("Authorization lacks explicit scoped user approval.")
    return value


def load_readiness_recovery_authorization() -> dict[str, Any]:
    raw = _sealed_read(recovery_authorization_path(), "readiness recovery implementation authorization")
    return validate_readiness_recovery_authorization(
        _strict_json(raw, "readiness recovery implementation authorization")
    )


_AUTHORITY = load_readiness_recovery_authority()
READINESS_RECOVERY_AUTHORITY = deepcopy(_AUTHORITY)


__all__ = [
    "BeatCellReadinessRecoveryContractError",
    "READINESS_RECOVERY_AUTHORITY",
    "READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256",
    "READINESS_RECOVERY_AUTHORITY_FILE_SHA256",
    "READINESS_RECOVERY_AUTHORITY_RELATIVE_PATH",
    "READINESS_RECOVERY_AUTHORITY_SCHEMA",
    "READINESS_RECOVERY_AUTHORIZATION_RELATIVE_PATH",
    "READINESS_RECOVERY_AUTHORIZATION_SCHEMA",
    "READINESS_RECOVERY_ID",
    "READINESS_RECOVERY_IMMUTABLE_INPUTS_SHA256",
    "READINESS_RECOVERY_IMPLEMENTATION_HANDOFF_RELATIVE_PATH",
    "READINESS_RECOVERY_OUTPUT",
    "load_readiness_recovery_authority",
    "load_readiness_recovery_authorization",
    "recovery_authorization_path",
    "recovery_authority_path",
    "validate_readiness_recovery_authorization",
    "validate_readiness_recovery_authority",
]
