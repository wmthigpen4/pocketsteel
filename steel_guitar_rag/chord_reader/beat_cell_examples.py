"""Label-blind beat-cell features and the sealed Stage-B examples join.

Stage A in this module accepts only a prediction-only Stage-1 sidecar and its
exact prediction leaf.  It has no report, group, reference, or outcome
parameter.  Stage B accepts the fully validated Stage-1 artifact only after a
complete feature-set manifest and every referenced feature summary have been
validated.  The separation is intentional and is part of the one-shot
development contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import ctypes
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import stat
from types import MappingProxyType
from typing import Any

from . import bar_examples as _bar_examples
from . import bar_uncertainty as _bar_uncertainty
from . import beat_cell_stage1 as _stage1
from . import runtime_bar_grid as _runtime_bar_grid
from . import runtime_beat_grid as _runtime_beat_grid
from .bar_promotion import canonical_sha256
from .audio_lineage import (
    project_development_audio_lineage,
    validate_development_audio_lineage,
)
from .beat_cell_stage2_contract import (
    BEAT_CELL_FEATURE_MATH_PROJECTION,
    BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    BEAT_CELL_FEATURE_SET_PUBLICATION_MODE,
    BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE,
    BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256,
    BEAT_CELL_STAGE2_SOURCE_INPUTS,
    BEAT_CELL_STAGE2_OUTPUT_PATHS,
    BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA,
    BEAT_CELL_STAGE_A_PROJECTION_SHA256,
    BEAT_CELL_STAGE_B_PROJECTION,
    BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    load_beat_cell_stage2_authority,
)
from .runtime_beat_grid import validate_runtime_beat_grid_receipt
from .selector_development import (
    _create_temporary_json,
    _directory_open_flags,
    _entry_stat,
    _identity as _publication_identity,
    _open_existing_directory,
    _open_or_create_directory,
    _preflight_new_directory,
    _preflight_new_json,
    _remove_owned_directory,
    _unlink_owned_entry,
    _verify_directory_path,
)


BEAT_CELL_FEATURE_ROW_SCHEMA = "chord_runtime_beat_cell_selector_feature_row_v1"
BEAT_CELL_FEATURE_SUMMARY_SCHEMA = "chord_runtime_beat_cell_selector_feature_summary_v1"
BEAT_CELL_FEATURE_SET_SCHEMA = "chord_runtime_beat_cell_selector_feature_set_v1"
BEAT_CELL_EXAMPLE_SCHEMA = "chord_runtime_beat_cell_selector_example_v1"
BEAT_CELL_EXAMPLES_SCHEMA = "chord_runtime_beat_cell_selector_examples_v1"
BEAT_CELL_EXAMPLE_KEY_SCHEMA = "chord_runtime_beat_cell_selector_example_key_v1"
BEAT_CELL_LABEL_AUDITS_SCHEMA = "chord_runtime_beat_cell_selector_label_audits_v1"
_OFFICIAL_FEATURE_PUBLICATION_POLICY = BEAT_CELL_FEATURE_SET_PUBLICATION_MODE
_OFFICIAL_SINGLE_JSON_PUBLICATION_POLICY = BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE
_OFFICIAL_PUBLICATION_POLICY_FIELDS = frozenset({"schemaVersion", "featureSet", "singleJson"})

FEATURE_NAMES = tuple(str(name) for name in BEAT_CELL_FEATURE_MATH_PROJECTION["featureNames"])
if FEATURE_NAMES != tuple(_bar_uncertainty.BAR_FEATURE_NAMES):
    raise RuntimeError("The Stage-2 feature-name authority is stale against bar_uncertainty.")
if _bar_uncertainty.BAR_FEATURE_CONTRACT_SHA256 != BEAT_CELL_FEATURE_MATH_PROJECTION["sourceBarFeatureContractSha256"]:
    raise RuntimeError("The Stage-2 bar-feature contract binding is stale.")

_HEX = frozenset("0123456789abcdef")
_EPSILON = float(BEAT_CELL_FEATURE_MATH_PROJECTION["epsilon"])
_DATASET_IDS = tuple(_bar_examples.LABEL_DETERMINACY_DATASET_IDS)

BEAT_CELL_FEATURE_ROW_FIELDS = frozenset(
    {
        "schemaVersion",
        "trackId",
        "cellIndex",
        "startMilliseconds",
        "endMilliseconds",
        "durationMilliseconds",
        "sourceBeatCellSha256",
        "predictionProduct",
        "predictionCoverage",
        "predictionDominance",
        "featureValues",
        "featureValuesSha256",
        "predictionIdentitySha256",
        "constructionSha256",
        "rowSha256",
    }
)
BEAT_CELL_FEATURE_SUMMARY_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "referenceFree",
        "trackId",
        "canonicalDurationMilliseconds",
        "coveredDurationMilliseconds",
        "predictionIdentity",
        "predictionIdentitySha256",
        "audioLineageRowSha256",
        "sourcePredictionCoreSha256",
        "sourceUncertaintySha256",
        "sourceStage1SidecarArtifactSha256",
        "sourceStage1PredictionSummarySha256",
        "sourceBeatReceiptTrackSha256",
        "constructionSha256",
        "stageAProjectionSha256",
        "featureMathProjectionSha256",
        "featureNames",
        "rows",
        "rowSetSha256",
        "artifactSha256",
    }
)
BEAT_CELL_FEATURE_SET_SUMMARY_FIELDS = frozenset(
    {
        "trackId",
        "path",
        "pathSha256",
        "fileSha256",
        "artifactSha256",
        "predictionIdentitySha256",
        "audioLineageRowSha256",
        "cellCount",
        "coveredDurationMilliseconds",
        "rowSetSha256",
        "rowSha256",
    }
)
BEAT_CELL_FEATURE_SET_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "referenceFree",
        "stageAComplete",
        "stageAProjectionSha256",
        "featureMathProjectionSha256",
        "authorityFileSha256",
        "authorityCanonicalSha256",
        "sourceStage1ReportPathSha256",
        "sourceStage1ReportFileSha256",
        "sourceStage1SummaryArtifactSetSha256",
        "sourceStage1SummaryFileSetSha256",
        "featureNames",
        "trackCount",
        "cellCount",
        "cellDurationMilliseconds",
        "summaries",
        "summarySetSha256",
        "featureRowSetSha256",
        "artifactSha256",
    }
)
BEAT_CELL_EXAMPLE_FIELDS = frozenset(
    {
        "schemaVersion",
        "exampleKey",
        "trackId",
        "cellIndex",
        "durationMilliseconds",
        "sourceBeatCellSha256",
        "predictionIdentitySha256",
        "featureRowSha256",
        "featureSummaryArtifactSha256",
        "featureSetArtifactSha256",
        "audioLineageRowSha256",
        "featureValues",
        "featureValuesSha256",
        "stage1OutcomeRowSha256",
        "stage1ArtifactSha256",
        "sourceGroupTrackRowSha256",
        "datasetId",
        "role",
        "guitarsetRole",
        "confidenceGroupId",
        "correct",
        "exampleSha256",
    }
)
BEAT_CELL_LABEL_AUDIT_ROW_FIELDS = frozenset(
    {
        "scope",
        "datasetId",
        "guitarsetRole",
        "trackCount",
        "exampleCount",
        "correctCount",
        "incorrectCount",
        "exampleDurationMilliseconds",
        "correctDurationMilliseconds",
        "incorrectDurationMilliseconds",
        "sourceFunnelSha256",
        "rowSha256",
    }
)
BEAT_CELL_GUITARSET_LABEL_AUDIT_FIELDS = frozenset({"aggregate", "roles", "roleSetSha256", "rowSha256"})
BEAT_CELL_LABEL_AUDITS_FIELDS = frozenset(
    {"schemaVersion", "aggregate", "datasets", "datasetSetSha256", "guitarset", "auditSha256"}
)
BEAT_CELL_EXAMPLES_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "referenceFree",
        "selectorTrainingInput",
        "stageBProjectionSha256",
        "featureMathProjectionSha256",
        "featureNames",
        "sourceStage1FileSha256",
        "sourceStage1CanonicalSha256",
        "sourceStage1ArtifactSha256",
        "sourceStage1DecisionSha256",
        "sourceStage1GateSetSha256",
        "sourceStage1TrackSetSha256",
        "sourceStage1SourceContractSha256",
        "sourceFeatureSetFileSha256",
        "sourceFeatureSetArtifactSha256",
        "sourceFeatureSummarySetSha256",
        "sourceFeatureRowSetSha256",
        "labelAudits",
        "labelAuditsSha256",
        "referenceEndpointReconciliationAudit",
        "referenceEndpointReconciliationAuditSha256",
        "trackCount",
        "confidenceGroupCount",
        "exampleCount",
        "exampleDurationMilliseconds",
        "examples",
        "exampleSetSha256",
        "artifactSha256",
    }
)

_STAGE1_SIDECAR_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "referenceFree",
        "trackId",
        "predictionIdentity",
        "predictionIdentitySha256",
        "sourceRuntimeTrackArtifactSha256",
        "sourceBeatReceiptTrack",
        "sourceBeatReceiptTrackSha256",
        "sourceAudioLineageRowSha256",
        "constructionPolicySha256",
        "scoringPolicySha256",
        "construction",
        "constructionSha256",
        "derivedCellTiming",
        "derivedCellTimingContractSha256",
        "predictionValidationAudit",
        "predictionValidationAuditSha256",
        "predictionSummary",
        "predictionSummarySha256",
        "artifactSha256",
    }
)
_REFERENCE_AUDIT_FIELDS = frozenset(
    {
        "schemaVersion",
        "policy",
        "sourceTrackCount",
        "reconciledTrackCount",
        "unreconciledTrackCount",
        "datasetCounts",
        "datasetCountSetSha256",
        "totalReconciledSeconds",
        "maximumReconciledSeconds",
        "rows",
        "rowSetSha256",
        "auditSha256",
    }
)
_REFERENCE_DATASET_FIELDS = frozenset({"datasetId", "sourceTrackCount", "reconciledTrackCount"})
_REFERENCE_ROW_FIELDS = frozenset(
    {
        "trackId",
        "datasetId",
        "referenceSha256",
        "originalEnd",
        "predictionDuration",
        "reconciledEnd",
        "reconciledSeconds",
        "canonicalMs",
        "rowSha256",
    }
)


class BeatCellExamplesError(ValueError):
    """A Stage-A feature or Stage-B example invariant failed closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BeatCellExamplesError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise BeatCellExamplesError(f"{name} must be an array.")
    return value


def _exact_fields(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise BeatCellExamplesError(f"{name} fields are not exact: missing={missing}, extra={extra}.")


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise BeatCellExamplesError(f"{name} must be a trimmed, nonempty string without NUL bytes.")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise BeatCellExamplesError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BeatCellExamplesError(f"{name} must be an integer >= {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BeatCellExamplesError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise BeatCellExamplesError(f"{name} must be a finite number.")
    return result


def _self_hash(value: Mapping[str, Any], field: str, name: str) -> str:
    claimed = _sha256(value.get(field), f"{name}.{field}")
    expected = canonical_sha256({key: item for key, item in value.items() if key != field})
    if claimed != expected:
        raise BeatCellExamplesError(f"{name}.{field} is stale.")
    return claimed


def _hashed(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    output = deepcopy(dict(payload))
    output[field] = canonical_sha256(output)
    return output


def _development_envelope(value: Mapping[str, Any], name: str) -> None:
    if (
        value.get("split") != "development"
        or value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
    ):
        raise BeatCellExamplesError(f"{name} must remain development-only and promotion-ineligible.")


def _validate_feature_values(value: Any, name: str) -> dict[str, float | int | None]:
    mapping = _mapping(value, name)
    if set(mapping) != set(FEATURE_NAMES):
        raise BeatCellExamplesError(f"{name} must contain the exact 48-feature key set.")
    output: dict[str, float | int | None] = {}
    for feature_name in FEATURE_NAMES:
        raw = mapping[feature_name]
        if raw is None:
            output[feature_name] = None
        else:
            _finite(raw, f"{name}.{feature_name}")
            output[feature_name] = raw
    transition = output["predictionTransitionCount"]
    if isinstance(transition, bool) or not isinstance(transition, int) or transition < 0:
        raise BeatCellExamplesError(f"{name}.predictionTransitionCount must be a nonnegative integer.")
    for feature_name in (
        "productFamilyNone",
        "productFamilyMajor",
        "productFamilyMinor",
        "productFamilyDominant",
        "productFamilyMinorSeventh",
    ):
        if output[feature_name] not in {0, 1} or isinstance(output[feature_name], bool):
            raise BeatCellExamplesError(f"{name}.{feature_name} must be the integer 0 or 1.")
    for feature_name in ("predictionCoverage", "predictionDominance"):
        number = _finite(output[feature_name], f"{name}.{feature_name}")
        if not 0 <= number <= 1:
            raise BeatCellExamplesError(f"{name}.{feature_name} must be in [0,1].")
    return output


def validate_beat_cell_feature_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one split-neutral feature row and return an unchanged deep copy."""

    value = deepcopy(dict(_mapping(row, "feature row")))
    _exact_fields(value, BEAT_CELL_FEATURE_ROW_FIELDS, "feature row")
    if value.get("schemaVersion") != BEAT_CELL_FEATURE_ROW_SCHEMA:
        raise BeatCellExamplesError("Feature row uses an unsupported schemaVersion.")
    _string(value.get("trackId"), "feature row.trackId")
    _integer(value.get("cellIndex"), "feature row.cellIndex")
    start = _integer(value.get("startMilliseconds"), "feature row.startMilliseconds")
    end = _integer(value.get("endMilliseconds"), "feature row.endMilliseconds", minimum=1)
    duration = _integer(value.get("durationMilliseconds"), "feature row.durationMilliseconds", minimum=1)
    if end <= start or end - start != duration:
        raise BeatCellExamplesError("Feature row millisecond interval is stale.")
    for field in (
        "sourceBeatCellSha256",
        "featureValuesSha256",
        "predictionIdentitySha256",
        "constructionSha256",
        "rowSha256",
    ):
        _sha256(value.get(field), f"feature row.{field}")
    product = value.get("predictionProduct")
    if product is not None:
        _string(product, "feature row.predictionProduct")
    for field in ("predictionCoverage", "predictionDominance"):
        number = _finite(value.get(field), f"feature row.{field}")
        if not 0 <= number <= 1:
            raise BeatCellExamplesError(f"Feature row {field} must be in [0,1].")
    feature_values = _validate_feature_values(value.get("featureValues"), "feature row.featureValues")
    if (
        value.get("featureValuesSha256") != canonical_sha256(feature_values)
        or feature_values["predictionCoverage"] != value.get("predictionCoverage")
        or feature_values["predictionDominance"] != value.get("predictionDominance")
    ):
        raise BeatCellExamplesError("Feature row feature-value binding is stale.")
    family_sum = sum(
        int(feature_values[name])
        for name in (
            "productFamilyNone",
            "productFamilyMajor",
            "productFamilyMinor",
            "productFamilyDominant",
            "productFamilyMinorSeventh",
        )
    )
    if family_sum != (0 if product is None else 1):
        raise BeatCellExamplesError("Feature row product-family one-hot values are stale.")
    _self_hash(value, "rowSha256", "feature row")
    return value


def validate_beat_cell_feature_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a complete prediction-only per-track Stage-A summary."""

    value = deepcopy(dict(_mapping(summary, "feature summary")))
    _exact_fields(value, BEAT_CELL_FEATURE_SUMMARY_FIELDS, "feature summary")
    if value.get("schemaVersion") != BEAT_CELL_FEATURE_SUMMARY_SCHEMA:
        raise BeatCellExamplesError("Feature summary uses an unsupported schemaVersion.")
    _development_envelope(value, "feature summary")
    if value.get("referenceFree") is not True:
        raise BeatCellExamplesError("Feature summary must be reference-free.")
    track_id = _string(value.get("trackId"), "feature summary.trackId")
    canonical_duration = _integer(
        value.get("canonicalDurationMilliseconds"),
        "feature summary.canonicalDurationMilliseconds",
        minimum=1,
    )
    covered_duration = _integer(
        value.get("coveredDurationMilliseconds"),
        "feature summary.coveredDurationMilliseconds",
        minimum=1,
    )
    if covered_duration > canonical_duration:
        raise BeatCellExamplesError("Feature summary covered duration exceeds canonical duration.")
    for field in (
        "predictionIdentitySha256",
        "audioLineageRowSha256",
        "sourcePredictionCoreSha256",
        "sourceUncertaintySha256",
        "sourceStage1SidecarArtifactSha256",
        "sourceStage1PredictionSummarySha256",
        "sourceBeatReceiptTrackSha256",
        "constructionSha256",
        "stageAProjectionSha256",
        "featureMathProjectionSha256",
        "rowSetSha256",
        "artifactSha256",
    ):
        _sha256(value.get(field), f"feature summary.{field}")
    if (
        value.get("stageAProjectionSha256") != BEAT_CELL_STAGE_A_PROJECTION_SHA256
        or value.get("featureMathProjectionSha256") != BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256
        or list(value.get("featureNames", [])) != list(FEATURE_NAMES)
    ):
        raise BeatCellExamplesError("Feature summary changed the frozen feature authority.")
    identity = _mapping(value.get("predictionIdentity"), "feature summary.predictionIdentity")
    try:
        expected_identity = _stage1._prediction_identity(identity)
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Feature summary prediction identity is invalid.") from error
    if (
        dict(identity) != expected_identity
        or identity.get("id") != track_id
        or identity.get("predictionIdentitySha256") != value.get("predictionIdentitySha256")
        or identity.get("predictionCoreSha256") != value.get("sourcePredictionCoreSha256")
        or identity.get("uncertaintySha256") != value.get("sourceUncertaintySha256")
        or identity.get("audioLineageRowSha256") != value.get("audioLineageRowSha256")
        or identity.get("canonicalDurationMilliseconds") != canonical_duration
    ):
        raise BeatCellExamplesError("Feature summary prediction identity binding is stale.")
    rows = [
        validate_beat_cell_feature_row(_mapping(row, f"feature summary.rows[{index}]"))
        for index, row in enumerate(_sequence(value.get("rows"), "feature summary.rows"))
    ]
    if not rows or [row["cellIndex"] for row in rows] != list(range(len(rows))):
        raise BeatCellExamplesError("Feature summary rows must be nonempty and contiguous by cellIndex.")
    if any(
        row["trackId"] != track_id
        or row["predictionIdentitySha256"] != value["predictionIdentitySha256"]
        or row["constructionSha256"] != value["constructionSha256"]
        for row in rows
    ):
        raise BeatCellExamplesError("Feature summary rows are not exactly track-bound.")
    if (
        math.fsum(int(row["durationMilliseconds"]) for row in rows) != covered_duration
        or rows[-1]["endMilliseconds"] != canonical_duration
        or canonical_sha256(rows) != value.get("rowSetSha256")
    ):
        raise BeatCellExamplesError("Feature summary row-set or duration binding is stale.")
    _self_hash(value, "artifactSha256", "feature summary")
    return value


def validate_beat_cell_feature_set_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the committed Stage-A manifest without opening its summaries."""

    value = deepcopy(dict(_mapping(manifest, "feature-set manifest")))
    _exact_fields(value, BEAT_CELL_FEATURE_SET_FIELDS, "feature-set manifest")
    if value.get("schemaVersion") != BEAT_CELL_FEATURE_SET_SCHEMA:
        raise BeatCellExamplesError("Feature-set manifest uses an unsupported schemaVersion.")
    _development_envelope(value, "feature-set manifest")
    if value.get("referenceFree") is not True or value.get("stageAComplete") is not True:
        raise BeatCellExamplesError("Feature-set manifest must seal a complete reference-free Stage A.")
    for field in (
        "stageAProjectionSha256",
        "featureMathProjectionSha256",
        "authorityFileSha256",
        "authorityCanonicalSha256",
        "sourceStage1ReportPathSha256",
        "sourceStage1ReportFileSha256",
        "sourceStage1SummaryArtifactSetSha256",
        "sourceStage1SummaryFileSetSha256",
        "summarySetSha256",
        "featureRowSetSha256",
        "artifactSha256",
    ):
        _sha256(value.get(field), f"feature-set manifest.{field}")
    if (
        value.get("stageAProjectionSha256") != BEAT_CELL_STAGE_A_PROJECTION_SHA256
        or value.get("featureMathProjectionSha256") != BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256
        or value.get("authorityFileSha256") != BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256
        or value.get("authorityCanonicalSha256") != BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256
        or list(value.get("featureNames", [])) != list(FEATURE_NAMES)
    ):
        raise BeatCellExamplesError("Feature-set manifest changed the committed authority.")
    track_count = _integer(value.get("trackCount"), "feature-set manifest.trackCount", minimum=1)
    cell_count = _integer(value.get("cellCount"), "feature-set manifest.cellCount", minimum=1)
    duration = _integer(
        value.get("cellDurationMilliseconds"),
        "feature-set manifest.cellDurationMilliseconds",
        minimum=1,
    )
    summaries: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(value.get("summaries"), "feature-set manifest.summaries")):
        row = deepcopy(dict(_mapping(raw, f"feature-set manifest.summaries[{index}]")))
        _exact_fields(row, BEAT_CELL_FEATURE_SET_SUMMARY_FIELDS, f"feature-set manifest.summaries[{index}]")
        _string(row.get("trackId"), f"feature-set manifest.summaries[{index}].trackId")
        path = _string(row.get("path"), f"feature-set manifest.summaries[{index}].path")
        for field in (
            "pathSha256",
            "fileSha256",
            "artifactSha256",
            "predictionIdentitySha256",
            "audioLineageRowSha256",
            "rowSetSha256",
            "rowSha256",
        ):
            _sha256(row.get(field), f"feature-set manifest.summaries[{index}].{field}")
        if canonical_sha256(path) != row.get("pathSha256"):
            raise BeatCellExamplesError("Feature-set summary path hash is stale.")
        _integer(row.get("cellCount"), "feature-set summary.cellCount", minimum=1)
        _integer(
            row.get("coveredDurationMilliseconds"),
            "feature-set summary.coveredDurationMilliseconds",
            minimum=1,
        )
        _self_hash(row, "rowSha256", f"feature-set manifest.summaries[{index}]")
        summaries.append(row)
    if (
        len(summaries) != track_count
        or summaries != sorted(summaries, key=lambda row: str(row["trackId"]))
        or len({str(row["trackId"]) for row in summaries}) != len(summaries)
        or sum(int(row["cellCount"]) for row in summaries) != cell_count
        or sum(int(row["coveredDurationMilliseconds"]) for row in summaries) != duration
        or canonical_sha256(summaries) != value.get("summarySetSha256")
    ):
        raise BeatCellExamplesError("Feature-set summary inventory is stale.")
    _self_hash(value, "artifactSha256", "feature-set manifest")
    return value


def _validate_reference_audit(value: Any) -> dict[str, Any]:
    audit = deepcopy(dict(_mapping(value, "referenceEndpointReconciliationAudit")))
    _exact_fields(audit, _REFERENCE_AUDIT_FIELDS, "referenceEndpointReconciliationAudit")
    if (
        audit.get("schemaVersion") != _bar_examples.REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA
        or audit.get("policy") != _bar_examples.REFERENCE_ENDPOINT_RECONCILIATION_POLICY
    ):
        raise BeatCellExamplesError("Reference endpoint reconciliation policy is stale.")
    source_count = _integer(audit.get("sourceTrackCount"), "reference audit.sourceTrackCount")
    reconciled_count = _integer(audit.get("reconciledTrackCount"), "reference audit.reconciledTrackCount")
    unreconciled_count = _integer(audit.get("unreconciledTrackCount"), "reference audit.unreconciledTrackCount")
    if source_count != reconciled_count + unreconciled_count:
        raise BeatCellExamplesError("Reference endpoint track counts do not reconcile.")
    dataset_counts: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(audit.get("datasetCounts"), "reference audit.datasetCounts")):
        row = deepcopy(dict(_mapping(raw, f"reference audit.datasetCounts[{index}]")))
        _exact_fields(row, _REFERENCE_DATASET_FIELDS, f"reference audit.datasetCounts[{index}]")
        _string(row.get("datasetId"), "reference audit datasetId")
        source = _integer(row.get("sourceTrackCount"), "reference audit dataset sourceTrackCount")
        reconciled = _integer(row.get("reconciledTrackCount"), "reference audit dataset reconciledTrackCount")
        if reconciled > source:
            raise BeatCellExamplesError("Reference audit reconciled dataset count exceeds source count.")
        dataset_counts.append(row)
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(audit.get("rows"), "reference audit.rows")):
        row = deepcopy(dict(_mapping(raw, f"reference audit.rows[{index}]")))
        _exact_fields(row, _REFERENCE_ROW_FIELDS, f"reference audit.rows[{index}]")
        _string(row.get("trackId"), "reference audit row.trackId")
        _string(row.get("datasetId"), "reference audit row.datasetId")
        _sha256(row.get("referenceSha256"), "reference audit row.referenceSha256")
        _integer(row.get("canonicalMs"), "reference audit row.canonicalMs", minimum=1)
        for field in ("originalEnd", "predictionDuration", "reconciledEnd", "reconciledSeconds"):
            _finite(row.get(field), f"reference audit row.{field}")
        _self_hash(row, "rowSha256", f"reference audit.rows[{index}]")
        rows.append(row)
    if (
        rows != sorted(rows, key=lambda row: str(row["trackId"]))
        or len({str(row["trackId"]) for row in rows}) != len(rows)
        or len(rows) != reconciled_count
        or sum(int(row["sourceTrackCount"]) for row in dataset_counts) != source_count
        or sum(int(row["reconciledTrackCount"]) for row in dataset_counts) != reconciled_count
        or canonical_sha256(dataset_counts) != audit.get("datasetCountSetSha256")
        or canonical_sha256(rows) != audit.get("rowSetSha256")
        or not math.isclose(
            math.fsum(float(row["reconciledSeconds"]) for row in rows),
            _finite(audit.get("totalReconciledSeconds"), "reference audit.totalReconciledSeconds"),
            rel_tol=0,
            abs_tol=1e-15,
        )
        or max((float(row["reconciledSeconds"]) for row in rows), default=0.0)
        != _finite(audit.get("maximumReconciledSeconds"), "reference audit.maximumReconciledSeconds")
    ):
        raise BeatCellExamplesError("Reference endpoint reconciliation audit is stale.")
    _self_hash(audit, "auditSha256", "referenceEndpointReconciliationAudit")
    return audit


def _validate_label_audit_row(value: Any, name: str) -> dict[str, Any]:
    row = deepcopy(dict(_mapping(value, name)))
    _exact_fields(row, BEAT_CELL_LABEL_AUDIT_ROW_FIELDS, name)
    scope = _string(row.get("scope"), f"{name}.scope")
    if scope not in {"aggregate", "dataset", "guitarset", "guitarsetRole"}:
        raise BeatCellExamplesError(f"{name}.scope is unsupported.")
    if row.get("datasetId") is not None:
        _string(row.get("datasetId"), f"{name}.datasetId")
    if row.get("guitarsetRole") is not None:
        if row.get("guitarsetRole") not in {"comp", "solo"}:
            raise BeatCellExamplesError(f"{name}.guitarsetRole is unsupported.")
    for field in (
        "trackCount",
        "exampleCount",
        "correctCount",
        "incorrectCount",
        "exampleDurationMilliseconds",
        "correctDurationMilliseconds",
        "incorrectDurationMilliseconds",
    ):
        _integer(row.get(field), f"{name}.{field}")
    if (
        row["exampleCount"] != row["correctCount"] + row["incorrectCount"]
        or row["exampleDurationMilliseconds"]
        != row["correctDurationMilliseconds"] + row["incorrectDurationMilliseconds"]
    ):
        raise BeatCellExamplesError(f"{name} count/duration partitions are stale.")
    _sha256(row.get("sourceFunnelSha256"), f"{name}.sourceFunnelSha256")
    _self_hash(row, "rowSha256", name)
    return row


def _validate_label_audits(value: Any, examples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    audits = deepcopy(dict(_mapping(value, "labelAudits")))
    _exact_fields(audits, BEAT_CELL_LABEL_AUDITS_FIELDS, "labelAudits")
    if audits.get("schemaVersion") != BEAT_CELL_LABEL_AUDITS_SCHEMA:
        raise BeatCellExamplesError("labelAudits uses an unsupported schemaVersion.")
    aggregate = _validate_label_audit_row(audits.get("aggregate"), "labelAudits.aggregate")
    if (aggregate["scope"], aggregate["datasetId"], aggregate["guitarsetRole"]) != (
        "aggregate",
        None,
        None,
    ):
        raise BeatCellExamplesError("labelAudits aggregate scope tuple is stale.")
    datasets = [
        _validate_label_audit_row(row, f"labelAudits.datasets[{index}]")
        for index, row in enumerate(_sequence(audits.get("datasets"), "labelAudits.datasets"))
    ]
    if [row["datasetId"] for row in datasets] != list(_DATASET_IDS):
        raise BeatCellExamplesError("labelAudits datasets must use the exact certification order.")
    if any(
        (row["scope"], row["datasetId"], row["guitarsetRole"]) != ("dataset", dataset_id, None)
        for row, dataset_id in zip(datasets, _DATASET_IDS, strict=True)
    ):
        raise BeatCellExamplesError("labelAudits dataset scope tuples are stale.")
    guitarset = deepcopy(dict(_mapping(audits.get("guitarset"), "labelAudits.guitarset")))
    _exact_fields(guitarset, BEAT_CELL_GUITARSET_LABEL_AUDIT_FIELDS, "labelAudits.guitarset")
    guitar_aggregate = _validate_label_audit_row(guitarset.get("aggregate"), "labelAudits.guitarset.aggregate")
    if (
        guitar_aggregate["scope"],
        guitar_aggregate["datasetId"],
        guitar_aggregate["guitarsetRole"],
    ) != ("guitarset", "guitarset", None):
        raise BeatCellExamplesError("labelAudits GuitarSet aggregate scope tuple is stale.")
    roles = [
        _validate_label_audit_row(row, f"labelAudits.guitarset.roles[{index}]")
        for index, row in enumerate(_sequence(guitarset.get("roles"), "labelAudits.guitarset.roles"))
    ]
    if [row["guitarsetRole"] for row in roles] != ["comp", "solo"]:
        raise BeatCellExamplesError("labelAudits GuitarSet roles must be ordered comp, solo.")
    if any(
        (row["scope"], row["datasetId"], row["guitarsetRole"]) != ("guitarsetRole", "guitarset", role)
        for row, role in zip(roles, ("comp", "solo"), strict=True)
    ):
        raise BeatCellExamplesError("labelAudits GuitarSet role scope tuples are stale.")
    if canonical_sha256(datasets) != audits.get("datasetSetSha256") or canonical_sha256(roles) != guitarset.get(
        "roleSetSha256"
    ):
        raise BeatCellExamplesError("labelAudits stratum-set hash is stale.")
    _self_hash(guitarset, "rowSha256", "labelAudits.guitarset")

    def observed(rows: Sequence[Mapping[str, Any]]) -> tuple[int, int, int, int, int, int, int]:
        track_ids = {str(row["trackId"]) for row in rows}
        correct = [row for row in rows if row["correct"] is True]
        incorrect = [row for row in rows if row["correct"] is False]
        return (
            len(track_ids),
            len(rows),
            len(correct),
            len(incorrect),
            sum(int(row["durationMilliseconds"]) for row in rows),
            sum(int(row["durationMilliseconds"]) for row in correct),
            sum(int(row["durationMilliseconds"]) for row in incorrect),
        )

    def claimed(row: Mapping[str, Any]) -> tuple[int, int, int, int, int, int, int]:
        return tuple(
            int(row[field])
            for field in (
                "trackCount",
                "exampleCount",
                "correctCount",
                "incorrectCount",
                "exampleDurationMilliseconds",
                "correctDurationMilliseconds",
                "incorrectDurationMilliseconds",
            )
        )

    if observed(examples) != claimed(aggregate):
        raise BeatCellExamplesError("labelAudits aggregate does not reconcile to examples.")
    for row in datasets:
        selected = [example for example in examples if example["datasetId"] == row["datasetId"]]
        if observed(selected) != claimed(row):
            raise BeatCellExamplesError("labelAudits dataset row does not reconcile to examples.")
    guitar_examples = [example for example in examples if example["datasetId"] == "guitarset"]
    if observed(guitar_examples) != claimed(guitar_aggregate):
        raise BeatCellExamplesError("labelAudits GuitarSet aggregate does not reconcile to examples.")
    for row in roles:
        selected = [example for example in guitar_examples if example["guitarsetRole"] == row["guitarsetRole"]]
        if observed(selected) != claimed(row):
            raise BeatCellExamplesError("labelAudits GuitarSet role does not reconcile to examples.")
    _self_hash(audits, "auditSha256", "labelAudits")
    return audits


def _example_key_payload(example: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": BEAT_CELL_EXAMPLE_KEY_SCHEMA,
        "trackId": example["trackId"],
        "cellIndex": example["cellIndex"],
        "durationMilliseconds": example["durationMilliseconds"],
        "sourceBeatCellSha256": example["sourceBeatCellSha256"],
        "predictionIdentitySha256": example["predictionIdentitySha256"],
        "featureRowSha256": example["featureRowSha256"],
        "featureSummaryArtifactSha256": example["featureSummaryArtifactSha256"],
        "featureSetArtifactSha256": example["featureSetArtifactSha256"],
        "audioLineageRowSha256": example["audioLineageRowSha256"],
    }


def _validate_example(row: Any, name: str) -> dict[str, Any]:
    value = deepcopy(dict(_mapping(row, name)))
    _exact_fields(value, BEAT_CELL_EXAMPLE_FIELDS, name)
    if value.get("schemaVersion") != BEAT_CELL_EXAMPLE_SCHEMA:
        raise BeatCellExamplesError(f"{name} uses an unsupported schemaVersion.")
    _string(value.get("trackId"), f"{name}.trackId")
    _integer(value.get("cellIndex"), f"{name}.cellIndex")
    _integer(value.get("durationMilliseconds"), f"{name}.durationMilliseconds", minimum=1)
    for field in (
        "exampleKey",
        "sourceBeatCellSha256",
        "predictionIdentitySha256",
        "featureRowSha256",
        "featureSummaryArtifactSha256",
        "featureSetArtifactSha256",
        "audioLineageRowSha256",
        "featureValuesSha256",
        "stage1OutcomeRowSha256",
        "stage1ArtifactSha256",
        "sourceGroupTrackRowSha256",
        "exampleSha256",
    ):
        _sha256(value.get(field), f"{name}.{field}")
    features = _validate_feature_values(value.get("featureValues"), f"{name}.featureValues")
    if canonical_sha256(features) != value.get("featureValuesSha256"):
        raise BeatCellExamplesError(f"{name} featureValuesSha256 is stale.")
    dataset_id = _string(value.get("datasetId"), f"{name}.datasetId")
    if dataset_id not in _DATASET_IDS:
        raise BeatCellExamplesError(f"{name}.datasetId is outside the frozen development dataset set.")
    _string(value.get("role"), f"{name}.role")
    _string(value.get("confidenceGroupId"), f"{name}.confidenceGroupId")
    guitar_role = value.get("guitarsetRole")
    if dataset_id == "guitarset":
        if guitar_role not in {"comp", "solo"}:
            raise BeatCellExamplesError(f"{name} must disclose an exact GuitarSet role.")
    elif guitar_role is not None:
        raise BeatCellExamplesError(f"{name} may not carry a GuitarSet role outside GuitarSet.")
    if not isinstance(value.get("correct"), bool):
        raise BeatCellExamplesError(f"{name}.correct must be boolean.")
    if canonical_sha256(_example_key_payload(value)) != value.get("exampleKey"):
        raise BeatCellExamplesError(f"{name}.exampleKey is stale or label-dependent.")
    _self_hash(value, "exampleSha256", name)
    return value


def validate_beat_cell_examples_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Strict standalone validation for selector/readiness consumers.

    The return is a deep copy with no normalization or reordering.  This
    function performs no file access.
    """

    value = deepcopy(dict(_mapping(artifact, "examples artifact")))
    _exact_fields(value, BEAT_CELL_EXAMPLES_FIELDS, "examples artifact")
    if value.get("schemaVersion") != BEAT_CELL_EXAMPLES_SCHEMA:
        raise BeatCellExamplesError("Examples artifact uses an unsupported schemaVersion.")
    _development_envelope(value, "examples artifact")
    if value.get("referenceFree") is not False or value.get("selectorTrainingInput") is not True:
        raise BeatCellExamplesError("Examples artifact must explicitly be a labeled selector-training input.")
    for field in (
        "stageBProjectionSha256",
        "featureMathProjectionSha256",
        "sourceStage1FileSha256",
        "sourceStage1CanonicalSha256",
        "sourceStage1ArtifactSha256",
        "sourceStage1DecisionSha256",
        "sourceStage1GateSetSha256",
        "sourceStage1TrackSetSha256",
        "sourceStage1SourceContractSha256",
        "sourceFeatureSetFileSha256",
        "sourceFeatureSetArtifactSha256",
        "sourceFeatureSummarySetSha256",
        "sourceFeatureRowSetSha256",
        "labelAuditsSha256",
        "referenceEndpointReconciliationAuditSha256",
        "exampleSetSha256",
        "artifactSha256",
    ):
        _sha256(value.get(field), f"examples artifact.{field}")
    if (
        value.get("stageBProjectionSha256") != BEAT_CELL_STAGE_B_PROJECTION_SHA256
        or value.get("featureMathProjectionSha256") != BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256
        or list(value.get("featureNames", [])) != list(FEATURE_NAMES)
    ):
        raise BeatCellExamplesError("Examples artifact changed the committed feature/Stage-B authority.")
    examples = [
        _validate_example(row, f"examples[{index}]")
        for index, row in enumerate(_sequence(value.get("examples"), "examples"))
    ]
    if (
        not examples
        or examples != sorted(examples, key=lambda row: str(row["exampleKey"]))
        or len({str(row["exampleKey"]) for row in examples}) != len(examples)
        or len({(str(row["trackId"]), int(row["cellIndex"])) for row in examples}) != len(examples)
        or any(
            row["featureSetArtifactSha256"] != value["sourceFeatureSetArtifactSha256"]
            or row["stage1ArtifactSha256"] != value["sourceStage1ArtifactSha256"]
            for row in examples
        )
        or canonical_sha256(examples) != value.get("exampleSetSha256")
    ):
        raise BeatCellExamplesError("Examples inventory/order/source binding is stale.")
    track_count = _integer(value.get("trackCount"), "examples artifact.trackCount", minimum=1)
    group_count = _integer(value.get("confidenceGroupCount"), "examples artifact.confidenceGroupCount", minimum=1)
    example_count = _integer(value.get("exampleCount"), "examples artifact.exampleCount", minimum=1)
    duration = _integer(
        value.get("exampleDurationMilliseconds"),
        "examples artifact.exampleDurationMilliseconds",
        minimum=1,
    )
    if (
        track_count != len({str(row["trackId"]) for row in examples})
        or group_count != len({str(row["confidenceGroupId"]) for row in examples})
        or example_count != len(examples)
        or duration != sum(int(row["durationMilliseconds"]) for row in examples)
    ):
        raise BeatCellExamplesError("Examples top-level counts or duration are stale.")
    audits = _validate_label_audits(value.get("labelAudits"), examples)
    if audits["auditSha256"] != value.get("labelAuditsSha256"):
        raise BeatCellExamplesError("Examples labelAudits binding is stale.")
    reference_audit = _validate_reference_audit(value.get("referenceEndpointReconciliationAudit"))
    if reference_audit["auditSha256"] != value.get("referenceEndpointReconciliationAuditSha256"):
        raise BeatCellExamplesError("Examples reference reconciliation binding is stale.")
    _self_hash(value, "artifactSha256", "examples artifact")
    return value


def validate_stage1_prediction_sidecar(sidecar: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact label-free Stage-1 sidecar shape used by Stage A."""

    value = deepcopy(dict(_mapping(sidecar, "Stage-1 prediction-only sidecar")))
    _exact_fields(value, _STAGE1_SIDECAR_FIELDS, "Stage-1 prediction-only sidecar")
    if value.get("schemaVersion") != _stage1.CELL_SUMMARY_SCHEMA:
        raise BeatCellExamplesError("Stage-1 sidecar uses an unsupported schemaVersion.")
    _development_envelope(value, "Stage-1 prediction-only sidecar")
    if value.get("referenceFree") is not True:
        raise BeatCellExamplesError("Stage-1 sidecar must remain reference-free.")
    track_id = _string(value.get("trackId"), "Stage-1 sidecar.trackId")
    for field in (
        "predictionIdentitySha256",
        "sourceRuntimeTrackArtifactSha256",
        "sourceBeatReceiptTrackSha256",
        "sourceAudioLineageRowSha256",
        "constructionPolicySha256",
        "scoringPolicySha256",
        "constructionSha256",
        "derivedCellTimingContractSha256",
        "predictionValidationAuditSha256",
        "predictionSummarySha256",
        "artifactSha256",
    ):
        _sha256(value.get(field), f"Stage-1 sidecar.{field}")
    if (
        value.get("constructionPolicySha256") != _stage1.CONSTRUCTION_POLICY_SHA256
        or value.get("scoringPolicySha256") != _stage1.SCORING_POLICY_SHA256
    ):
        raise BeatCellExamplesError("Stage-1 sidecar changed a frozen construction/scoring policy.")
    identity = _mapping(value.get("predictionIdentity"), "Stage-1 sidecar.predictionIdentity")
    try:
        expected_identity = _stage1._prediction_identity(identity)
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Stage-1 sidecar prediction identity is invalid.") from error
    if (
        dict(identity) != expected_identity
        or identity.get("id") != track_id
        or identity.get("predictionIdentitySha256") != value.get("predictionIdentitySha256")
        or identity.get("audioLineageRowSha256") != value.get("sourceAudioLineageRowSha256")
    ):
        raise BeatCellExamplesError("Stage-1 sidecar prediction identity binding is stale.")
    source_track = _mapping(value.get("sourceBeatReceiptTrack"), "Stage-1 sidecar.sourceBeatReceiptTrack")
    try:
        _stage1._validate_self_hash(
            source_track,
            "trackReceiptSha256",
            "Stage-1 sidecar source beat-receipt track",
        )
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Stage-1 sidecar beat-receipt track is invalid.") from error
    if source_track.get("trackId") != track_id or source_track.get("trackReceiptSha256") != value.get(
        "sourceBeatReceiptTrackSha256"
    ):
        raise BeatCellExamplesError("Stage-1 sidecar beat-receipt track binding is stale.")
    construction = _mapping(value.get("construction"), "Stage-1 sidecar.construction")
    try:
        _stage1._validate_construction(
            construction,
            "Stage-1 sidecar construction",
            source_receipt_track=source_track,
            expected_track_id=track_id,
        )
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Stage-1 sidecar construction is invalid.") from error
    if construction.get("constructionSha256") != value.get("constructionSha256"):
        raise BeatCellExamplesError("Stage-1 sidecar construction binding is stale.")
    derived = _mapping(value.get("derivedCellTiming"), "Stage-1 sidecar.derivedCellTiming")
    validation_audit = _mapping(value.get("predictionValidationAudit"), "Stage-1 sidecar.predictionValidationAudit")
    try:
        _stage1._validate_self_hash(derived, "contractSha256", "Stage-1 sidecar derived timing")
        _stage1._validate_self_hash(
            validation_audit,
            "auditSha256",
            "Stage-1 sidecar prediction-validation audit",
        )
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Stage-1 sidecar timing/validation audit is invalid.") from error
    if (
        derived.get("contractSha256") != value.get("derivedCellTimingContractSha256")
        or derived.get("contractSha256") != construction.get("derivedCellTimingContractSha256")
        or validation_audit.get("auditSha256") != value.get("predictionValidationAuditSha256")
        or validation_audit.get("trackId") != track_id
    ):
        raise BeatCellExamplesError("Stage-1 sidecar timing/validation binding is stale.")
    prediction_summary = _mapping(value.get("predictionSummary"), "Stage-1 sidecar.predictionSummary")
    try:
        _stage1._validate_prediction_summary(prediction_summary, track_id)
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Stage-1 sidecar prediction summary is invalid.") from error
    if (
        prediction_summary.get("summarySha256") != value.get("predictionSummarySha256")
        or prediction_summary.get("constructionSha256") != value.get("constructionSha256")
        or prediction_summary.get("derivedCellTimingContractSha256") != value.get("derivedCellTimingContractSha256")
        or prediction_summary.get("predictionValidationAuditSha256") != value.get("predictionValidationAuditSha256")
        or prediction_summary.get("sourcePredictionCoreSha256") != identity.get("predictionCoreSha256")
        or prediction_summary.get("sourceUncertaintySha256") != identity.get("uncertaintySha256")
        or prediction_summary.get("canonicalRuntimeDurationMilliseconds")
        != identity.get("canonicalDurationMilliseconds")
        or len(_sequence(prediction_summary.get("cells"), "Stage-1 prediction summary cells"))
        != construction.get("cellCount")
    ):
        raise BeatCellExamplesError("Stage-1 sidecar prediction summary binding is stale.")
    _self_hash(value, "artifactSha256", "Stage-1 prediction-only sidecar")
    return value


def _winner(
    overlaps: Mapping[str, float],
) -> tuple[str | None, float]:
    if not overlaps:
        return None, 0.0
    maximum = max(float(seconds) for seconds in overlaps.values())
    candidates = sorted(
        product
        for product, seconds in overlaps.items()
        if math.isclose(float(seconds), maximum, rel_tol=0, abs_tol=_EPSILON)
    )
    product = candidates[0]
    return product, float(overlaps[product])


def _winner_candidates(overlaps: Mapping[str, float]) -> tuple[str, ...]:
    if not overlaps:
        return ()
    maximum = max(float(seconds) for seconds in overlaps.values())
    return tuple(
        sorted(
            product
            for product, seconds in overlaps.items()
            if math.isclose(float(seconds), maximum, rel_tol=0, abs_tol=_EPSILON)
        )
    )


_PRODUCT_RECONCILIATION_POLICY_FIELDS = frozenset(
    {
        "schemaVersion",
        "sourceStage1ScoringPolicySha256",
        "predecessorFailure",
        "rule",
        "structuralIneligibility",
        "expectedCount",
        "expectedRows",
        "expectedRowSetSha256",
        "forbiddenDecisionInputs",
        "labelBlindSweep",
        "labelBlindSweepSha256",
        "postFreezeLabelBlindPreflight",
        "preCommitGovernanceIncidentDisclosure",
        "stageBAdmission",
    }
)
_PRODUCT_RECONCILIATION_ROW_FIELDS = frozenset(
    {
        "trackId",
        "cellIndex",
        "startMilliseconds",
        "endMilliseconds",
        "sourceBeatCellSha256",
        "featureProduct",
        "stage1Product",
        "featureCoverage",
        "stage1Coverage",
        "featureDominance",
        "stage1Dominance",
        "candidateProducts",
        "overlapSecondsByProduct",
    }
)
_STAGE_B_RECONCILIATION_FIELDS = (
    "trackId",
    "cellIndex",
    "startMilliseconds",
    "endMilliseconds",
    "sourceBeatCellSha256",
    "featureProduct",
    "stage1Product",
    "featureCoverage",
    "stage1Coverage",
    "featureDominance",
    "stage1Dominance",
)


def _validate_expected_product_reconciliation_row(
    row: Mapping[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    value = deepcopy(dict(_mapping(row, f"stage1ProductReconciliation.expectedRows[{index}]")))
    _exact_fields(
        value,
        _PRODUCT_RECONCILIATION_ROW_FIELDS,
        f"stage1ProductReconciliation.expectedRows[{index}]",
    )
    _string(value.get("trackId"), f"expectedRows[{index}].trackId")
    _sha256(value.get("sourceBeatCellSha256"), f"expectedRows[{index}].sourceBeatCellSha256")
    _integer(value.get("cellIndex"), f"expectedRows[{index}].cellIndex")
    start_ms = _integer(value.get("startMilliseconds"), f"expectedRows[{index}].startMilliseconds")
    end_ms = _integer(value.get("endMilliseconds"), f"expectedRows[{index}].endMilliseconds", minimum=1)
    if end_ms <= start_ms:
        raise BeatCellExamplesError("A product-reconciliation interval must be positive.")
    feature_product = _string(value.get("featureProduct"), f"expectedRows[{index}].featureProduct")
    stage1_product = _string(value.get("stage1Product"), f"expectedRows[{index}].stage1Product")
    if feature_product == stage1_product:
        raise BeatCellExamplesError("A product reconciliation must bind two unequal products.")

    raw_candidates = _sequence(value.get("candidateProducts"), f"expectedRows[{index}].candidateProducts")
    candidates = tuple(
        _string(product, f"expectedRows[{index}].candidateProducts[{candidate_index}]")
        for candidate_index, product in enumerate(raw_candidates)
    )
    if (
        candidates != tuple(sorted(set(candidates)))
        or feature_product not in candidates
        or stage1_product not in candidates
    ):
        raise BeatCellExamplesError("Product-reconciliation candidates are not exact sorted unique bindings.")
    raw_overlaps = _mapping(value.get("overlapSecondsByProduct"), f"expectedRows[{index}].overlapSecondsByProduct")
    overlaps = {
        _string(product, f"expectedRows[{index}].overlap product"): _finite(
            seconds,
            f"expectedRows[{index}].overlapSecondsByProduct[{product!r}]",
        )
        for product, seconds in raw_overlaps.items()
    }
    if not overlaps or any(seconds <= 0 for seconds in overlaps.values()):
        raise BeatCellExamplesError("Product-reconciliation overlaps must be positive and nonempty.")
    if _winner_candidates(overlaps) != candidates or _winner(overlaps)[0] != feature_product:
        raise BeatCellExamplesError("Product-reconciliation tolerant-winner evidence is stale.")
    exact_maximum = max(overlaps.values())
    exact_candidates = sorted(product for product, seconds in overlaps.items() if seconds == exact_maximum)
    if not exact_candidates or exact_candidates[0] != stage1_product:
        raise BeatCellExamplesError("Product-reconciliation Stage-1 exact winner is stale.")

    feature_coverage = _finite(value.get("featureCoverage"), f"expectedRows[{index}].featureCoverage")
    stage1_coverage = _finite(value.get("stage1Coverage"), f"expectedRows[{index}].stage1Coverage")
    feature_dominance = _finite(value.get("featureDominance"), f"expectedRows[{index}].featureDominance")
    stage1_dominance = _finite(value.get("stage1Dominance"), f"expectedRows[{index}].stage1Dominance")
    if any(
        observed < 0 or observed > 1
        for observed in (feature_coverage, stage1_coverage, feature_dominance, stage1_dominance)
    ):
        raise BeatCellExamplesError("Product-reconciliation coverage/dominance values must be within [0,1].")
    interval_seconds = (end_ms - start_ms) / 1000
    covered_seconds = min(interval_seconds, max(0.0, math.fsum(overlaps.values())))
    winner_seconds = min(covered_seconds, max(0.0, overlaps[feature_product]))
    expected_feature_coverage = min(1.0, max(0.0, covered_seconds / interval_seconds))
    expected_feature_dominance = (
        min(1.0, max(0.0, winner_seconds / covered_seconds)) if covered_seconds > _EPSILON else 0.0
    )
    if (
        feature_coverage != expected_feature_coverage
        or feature_dominance != expected_feature_dominance
        or not math.isclose(feature_coverage, stage1_coverage, rel_tol=0, abs_tol=_EPSILON)
        or not math.isclose(feature_dominance, stage1_dominance, rel_tol=0, abs_tol=_EPSILON)
        or not _prediction_is_structurally_ineligible(feature_product, feature_coverage, feature_dominance)
        or not _prediction_is_structurally_ineligible(stage1_product, stage1_coverage, stage1_dominance)
    ):
        raise BeatCellExamplesError("Product-reconciliation values do not prove dual structural ineligibility.")
    return value


def _expected_product_reconciliations() -> list[dict[str, Any]]:
    policy = _mapping(
        BEAT_CELL_FEATURE_MATH_PROJECTION.get("stage1ProductReconciliation"),
        "feature-math stage1ProductReconciliation",
    )
    _exact_fields(policy, _PRODUCT_RECONCILIATION_POLICY_FIELDS, "feature-math stage1ProductReconciliation")
    expected = [
        _validate_expected_product_reconciliation_row(row, index=index)
        for index, row in enumerate(_sequence(policy.get("expectedRows"), "stage1ProductReconciliation.expectedRows"))
    ]
    expected.sort(key=lambda row: (str(row.get("trackId")), int(row.get("cellIndex", -1))))
    structural = _mapping(policy.get("structuralIneligibility"), "stage1ProductReconciliation.structuralIneligibility")
    expected_structural = {
        "comparisonEpsilon": _stage1.SCORING_POLICY["comparisonEpsilon"],
        "expectedStage1Result": True,
        "expectedStageAResult": True,
        "formula": (
            "predictionProduct is null or predictionCoverage+comparisonEpsilon<predictionCoverageMinimum "
            "or predictionDominance+comparisonEpsilon<predictionDominanceMinimum"
        ),
        "predictionCoverageMinimum": _stage1.SCORING_POLICY["predictionCoverage"],
        "predictionDominanceMinimum": _stage1.SCORING_POLICY["predictionDominance"],
        "stage1Required": True,
        "stageARequired": True,
    }
    sweep = _mapping(policy.get("labelBlindSweep"), "stage1ProductReconciliation.labelBlindSweep")
    preflight = _mapping(
        policy.get("postFreezeLabelBlindPreflight"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight",
    )
    incident = _mapping(
        policy.get("preCommitGovernanceIncidentDisclosure"),
        "stage1ProductReconciliation.preCommitGovernanceIncidentDisclosure",
    )
    stage_b = _mapping(policy.get("stageBAdmission"), "stage1ProductReconciliation.stageBAdmission")
    projected = [{field: row.get(field) for field in _STAGE_B_RECONCILIATION_FIELDS} for row in expected]
    preflight_inventory = _mapping(
        preflight.get("inventoryPerRun"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.inventoryPerRun",
    )
    preflight_results = _mapping(
        preflight.get("requiredInMemoryResultsPerRun"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.requiredInMemoryResultsPerRun",
    )
    preflight_forbidden = _mapping(
        preflight.get("forbiddenOperationCounts"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.forbiddenOperationCounts",
    )
    preflight_boundary = _mapping(
        preflight.get("inputSnapshotBoundary"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.inputSnapshotBoundary",
    )
    preflight_delta = _mapping(
        preflight.get("deltaPolicy"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.deltaPolicy",
    )
    preflight_one_shot = _mapping(
        preflight.get("oneShotConsumption"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.oneShotConsumption",
    )
    preflight_builder = _mapping(
        preflight.get("productionBuilder"),
        "stage1ProductReconciliation.postFreezeLabelBlindPreflight.productionBuilder",
    )
    incident_decision = _mapping(
        incident.get("decisionIndependence"),
        "stage1ProductReconciliation.preCommitGovernanceIncidentDisclosure.decisionIndependence",
    )
    incident_indexed = _mapping(
        incident.get("indexedProtectedCollections"),
        "stage1ProductReconciliation.preCommitGovernanceIncidentDisclosure.indexedProtectedCollections",
    )
    incident_post = _mapping(
        incident.get("postIncidentParseCounts"),
        "stage1ProductReconciliation.preCommitGovernanceIncidentDisclosure.postIncidentParseCounts",
    )
    incident_retention = _mapping(
        incident.get("retention"),
        "stage1ProductReconciliation.preCommitGovernanceIncidentDisclosure.retention",
    )
    if (
        policy.get("schemaVersion") != "chord_runtime_beat_cell_stage2_product_reconciliation_v1"
        or BEAT_CELL_FEATURE_MATH_PROJECTION.get("sourceStage1ScoringPolicySha256") != _stage1.SCORING_POLICY_SHA256
        or policy.get("sourceStage1ScoringPolicySha256") != _stage1.SCORING_POLICY_SHA256
        or policy.get("expectedCount") != len(expected)
        or policy.get("expectedRowSetSha256") != canonical_sha256(expected)
        or dict(structural) != expected_structural
        or policy.get("labelBlindSweepSha256") != canonical_sha256(sweep)
        or sweep.get("schemaVersion") != "chord_runtime_beat_cell_stage2_product_reconciliation_sweep_v1"
        or sweep.get("labelBlind") is not True
        or sweep.get("trackCount") != BEAT_CELL_STAGE2_SOURCE_INPUTS["trackCount"]
        or sweep.get("cellCount") != BEAT_CELL_STAGE2_SOURCE_INPUTS["cellCount"]
        or sweep.get("predictionIdentitySetSha256") != BEAT_CELL_STAGE2_SOURCE_INPUTS["predictionIdentitySetSha256"]
        or sweep.get("stage1SummaryArtifactSetSha256")
        != BEAT_CELL_STAGE2_SOURCE_INPUTS["stage1SummaryArtifactSet"]["sha256"]
        or sweep.get("stage1SummaryFileSetSha256") != BEAT_CELL_STAGE2_SOURCE_INPUTS["stage1SummaryFileSet"]["sha256"]
        or sweep.get("tolerantWinnerStage1ProductMismatchCount") != len(expected)
        or sweep.get("expectedReconciliationCount") != len(expected)
        or sweep.get("coverageMismatchCountAtAbsoluteTolerance1e-9") != 0
        or sweep.get("dominanceMismatchCountAtAbsoluteTolerance1e-9") != 0
        or sweep.get("unexpectedReconciliationCount") != 0
        or preflight.get("schemaVersion") != "chord_runtime_beat_cell_stage2_post_freeze_label_blind_preflight_v2"
        or preflight.get("authorization")
        != "exactly-two-deterministic-in-memory-committed-production-builder-runs-only"
        or preflight.get("authorizedRunCount") != 2
        or preflight.get("executionPhase")
        != (
            "only-after-R4-authority-and-corrected-production-code-are-committed-at-one-clean-HEAD-and-all-"
            "authority-source-hashes-are-final"
        )
        or preflight_inventory.get("trackCount") != BEAT_CELL_STAGE2_SOURCE_INPUTS["trackCount"]
        or preflight_inventory.get("cellCount") != BEAT_CELL_STAGE2_SOURCE_INPUTS["cellCount"]
        or preflight_inventory.get("featureSummaryCount") != BEAT_CELL_STAGE2_SOURCE_INPUTS["trackCount"]
        or preflight_inventory.get("featureRowCount") != BEAT_CELL_STAGE2_SOURCE_INPUTS["cellCount"]
        or preflight_inventory.get("predictionIdentitySetSha256")
        != BEAT_CELL_STAGE2_SOURCE_INPUTS["predictionIdentitySetSha256"]
        or preflight_inventory.get("stage1SummaryArtifactSetSha256")
        != BEAT_CELL_STAGE2_SOURCE_INPUTS["stage1SummaryArtifactSet"]["sha256"]
        or preflight_inventory.get("stage1SummaryFileSetSha256")
        != BEAT_CELL_STAGE2_SOURCE_INPUTS["stage1SummaryFileSet"]["sha256"]
        or preflight_results.get("exactReconciliationCount") != len(expected)
        or preflight_results.get("exactReconciliationRowSetSha256") != canonical_sha256(expected)
        or preflight_results.get("unexpectedReconciliationCount") != 0
        or preflight_results.get("allFeatureSummariesAndRowsValidate") is not True
        or preflight_results.get("runOneAndRunTwoCanonicalSummaryInventoryEqual") is not True
        or not preflight_forbidden
        or any(value != 0 for value in preflight_forbidden.values())
        or preflight_boundary.get("fullDirectAndTransitiveStageAInputInventoryRequired") is not True
        or preflight_boundary.get("nofollowSealedReadsRequired") is not True
        or preflight_boundary.get("stage1ReportHandling")
        != "opaque raw bytes/hash/stat only; no JSON parse or traversal"
        or not preflight_delta
        or any(value != "block" for value in preflight_delta.values())
        or set(preflight_one_shot)
        != {
            "consumesOfficialInvocation",
            "consumesR4OneShot",
            "reason",
        }
        or preflight_one_shot.get("consumesOfficialInvocation") is not False
        or preflight_one_shot.get("consumesR4OneShot") is not False
        or preflight_builder.get("module") != "steel_guitar_rag/chord_reader/beat_cell_examples.py"
        or preflight_builder.get("callable") != "build_beat_cell_feature_summary"
        or preflight_builder.get("moduleFileSha256Source") != "featureMath.sourceStageAImplementationModuleFileSha256"
        or preflight_builder.get("exactCommittedModuleBytesRequired") is not True
        or preflight_builder.get("officialRunnerOrCliAllowed") is not False
        or incident.get("schemaVersion") != "chord_runtime_beat_cell_stage2_precommit_governance_incident_v1"
        or incident.get("docsAuditStage1ReportJsonLoadsCount") != 1
        or incident.get("canonicalTraversalCount") != 1
        or incident.get("attemptedPath")
        != "aggregate.funnel.counts (failed at aggregate.funnel before any duration expression evaluated)"
        or incident.get("terminalError") != "KeyError('funnel')"
        or incident.get("terminalErrorOccurredBeforeAttemptedPathOutput") is not True
        or incident.get("numericOrProtectedSemanticValuesEmittedCount") != 0
        or incident.get("numericOrProtectedSemanticValuesRetainedCount") != 0
        or incident_decision.get("usedAsDecisionInput") is not False
        or incident_decision.get("changedPolicyOrExpectedInventory") is not False
        or incident_decision.get("tolerantWinnerReconciliationPolicySelectedBeforeIncident") is not True
        or not incident_indexed
        or any(value != 0 for value in incident_indexed.values())
        or not incident_post
        or any(value != 0 for value in incident_post.values())
        or not incident_retention
        or any(value is not False for value in incident_retention.values())
        or stage_b.get("exactReconciliationProjectionFields") != list(_STAGE_B_RECONCILIATION_FIELDS)
        or stage_b.get("expectedReconciliationProjectionCount") != len(projected)
        or stage_b.get("expectedReconciliationProjectionSetSha256") != canonical_sha256(projected)
        or stage_b.get("requiredOutcomeClassificationSet") != ["U", "N"]
        or stage_b.get("exampleEmissionAllowed") is not False
        or stage_b.get("expectedExampleEmissionCount") != 0
        or stage_b.get("classificationMayChangeStageA") is not False
        or stage_b.get("classificationAccessPhase")
        != "StageB-only-after-complete-StageA-publication-and-independent-label-blind-audit"
        or stage_b.get("allOtherProductMismatches") != "fail-closed"
    ):
        raise BeatCellExamplesError("The Stage-A product-reconciliation authority is stale.")
    return expected


def _validate_product_reconciliation_inventory(
    rows: Sequence[Mapping[str, Any]],
    *,
    track_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    observed = [deepcopy(dict(_mapping(row, "Stage-A product reconciliation"))) for row in rows]
    observed.sort(key=lambda row: (str(row.get("trackId")), int(row.get("cellIndex", -1))))
    expected = _expected_product_reconciliations()
    if track_ids is not None:
        expected = [row for row in expected if str(row.get("trackId")) in track_ids]
    if observed != expected or canonical_sha256(observed) != canonical_sha256(expected):
        raise BeatCellExamplesError("Stage-A product-reconciliation inventory is not exact.")
    return observed


def _prediction_is_structurally_ineligible(
    product: str | None,
    coverage: float,
    dominance: float,
) -> bool:
    epsilon = float(_stage1.SCORING_POLICY["comparisonEpsilon"])
    return (
        product is None
        or coverage + epsilon < float(_stage1.SCORING_POLICY["predictionCoverage"])
        or dominance + epsilon < float(_stage1.SCORING_POLICY["predictionDominance"])
    )


def _product_reconciliation_row(
    *,
    track_id: str,
    cell_index: int,
    start_ms: int,
    end_ms: int,
    cell: Mapping[str, Any],
    overlaps: Mapping[str, float],
    feature_product: str | None,
    stage1_product: str | None,
    feature_coverage: float,
    stage1_coverage: float,
    feature_dominance: float,
    stage1_dominance: float,
) -> dict[str, Any]:
    return {
        "trackId": track_id,
        "cellIndex": cell_index,
        "startMilliseconds": start_ms,
        "endMilliseconds": end_ms,
        "sourceBeatCellSha256": canonical_sha256(cell),
        "featureProduct": feature_product,
        "stage1Product": stage1_product,
        "featureCoverage": feature_coverage,
        "stage1Coverage": stage1_coverage,
        "featureDominance": feature_dominance,
        "stage1Dominance": stage1_dominance,
        "candidateProducts": list(_winner_candidates(overlaps)),
        "overlapSecondsByProduct": {product: float(overlaps[product]) for product in sorted(overlaps)},
    }


def _reconcile_stage1_product(
    reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    row = deepcopy(dict(_mapping(reconciliation, "Stage-A product reconciliation")))
    feature_product = row.get("featureProduct")
    stage1_product = row.get("stage1Product")
    candidates = _sequence(row.get("candidateProducts"), "reconciliation candidateProducts")
    if (
        not isinstance(feature_product, str)
        or not isinstance(stage1_product, str)
        or feature_product == stage1_product
        or feature_product not in candidates
        or stage1_product not in candidates
        or not _prediction_is_structurally_ineligible(
            feature_product,
            _finite(row.get("featureCoverage"), "reconciliation featureCoverage"),
            _finite(row.get("featureDominance"), "reconciliation featureDominance"),
        )
        or not _prediction_is_structurally_ineligible(
            stage1_product,
            _finite(row.get("stage1Coverage"), "reconciliation stage1Coverage"),
            _finite(row.get("stage1Dominance"), "reconciliation stage1Dominance"),
        )
        or row not in _expected_product_reconciliations()
    ):
        raise BeatCellExamplesError("Stage-A prediction-product mismatch is not an exact ineligible reconciliation.")
    return row


def build_beat_cell_feature_summary(
    stage1_sidecar: Mapping[str, Any],
    prediction: Mapping[str, Any],
    *,
    prediction_file_sha256: str,
    product_reconciliations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one label-blind Stage-A feature summary.

    No Stage-1 report, outcome, group, or reference object can be supplied to
    this API.  ``prediction_file_sha256`` binds the already captured raw leaf
    bytes; the prediction mapping alone is insufficient for that identity.
    """

    sidecar = validate_stage1_prediction_sidecar(stage1_sidecar)
    prediction_value = deepcopy(dict(_mapping(prediction, "prediction leaf")))
    identity = _mapping(sidecar["predictionIdentity"], "Stage-1 sidecar prediction identity")
    raw_sha256 = _sha256(prediction_file_sha256, "prediction_file_sha256")
    if raw_sha256 != identity.get("predictionSha256"):
        raise BeatCellExamplesError("Prediction leaf raw-file hash disagrees with its Stage-1 identity.")
    if (
        prediction_value.get("id") != sidecar["trackId"]
        or prediction_value.get("predictionCoreSha256") != identity.get("predictionCoreSha256")
        or prediction_value.get("uncertaintySha256") != identity.get("uncertaintySha256")
    ):
        raise BeatCellExamplesError("Prediction leaf disagrees with the exact Stage-1 identity.")
    try:
        evidence = _bar_uncertainty._validate_prediction_uncertainty(prediction_value)
        duration = _finite(prediction_value.get("durationSeconds"), "prediction.durationSeconds")
        segments = _bar_uncertainty._prediction_segments(prediction_value, duration)
        _bar_uncertainty._validate_selected_class_alignment(evidence, segments)
        recomputed_stage1 = _stage1.summarize_prediction_cells(
            prediction_value,
            sidecar["construction"],
            sidecar["derivedCellTiming"],
            prediction_validation_audit_sha256=sidecar["predictionValidationAuditSha256"],
        )
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Prediction leaf failed frozen uncertainty/cell validation.") from error
    source_stage1_summary = sidecar["predictionSummary"]
    if recomputed_stage1 != source_stage1_summary or canonical_sha256(recomputed_stage1) != canonical_sha256(
        source_stage1_summary
    ):
        raise BeatCellExamplesError("Complete Stage-1 prediction-summary recomputation is not canonical-equal.")
    canonical_duration = _integer(
        sidecar["construction"].get("canonicalDurationMilliseconds"),
        "construction.canonicalDurationMilliseconds",
        minimum=1,
    )
    if identity.get("canonicalDurationMilliseconds") != canonical_duration:
        raise BeatCellExamplesError("Prediction identity changed canonical duration.")

    source_cells = list(_sequence(sidecar["construction"].get("cells"), "Stage-1 sidecar construction.cells"))
    stage1_cells = list(_sequence(source_stage1_summary.get("cells"), "Stage-1 sidecar predictionSummary.cells"))
    rows: list[dict[str, Any]] = []
    for index, (raw_cell, raw_stage1_row) in enumerate(zip(source_cells, stage1_cells, strict=True)):
        cell = _mapping(raw_cell, f"construction.cells[{index}]")
        stage1_row = _mapping(raw_stage1_row, f"predictionSummary.cells[{index}]")
        start_ms = _integer(cell.get("startMs"), f"construction.cells[{index}].startMs")
        end_ms = _integer(cell.get("endMs"), f"construction.cells[{index}].endMs", minimum=1)
        if end_ms <= start_ms:
            raise BeatCellExamplesError("Stage-A source cell interval must be positive.")
        start = start_ms / 1000
        end = end_ms / 1000
        overlaps, covered_seconds, sequence = _bar_uncertainty._overlap_by_product(segments, start, end)
        product, winner_seconds = _winner(overlaps)
        interval_seconds = (end_ms - start_ms) / 1000
        covered_seconds = min(interval_seconds, max(0.0, covered_seconds))
        winner_seconds = min(covered_seconds, max(0.0, winner_seconds))
        coverage = min(1.0, max(0.0, covered_seconds / interval_seconds))
        dominance = min(1.0, max(0.0, winner_seconds / covered_seconds)) if covered_seconds > _EPSILON else 0.0
        full_weights = _bar_uncertainty._frame_weights(
            int(evidence["frameCount"]),
            float(evidence["frameSeconds"]),
            float(evidence["duration"]),
            start,
            end,
        )
        winner_weights = _bar_uncertainty._frame_weights(
            int(evidence["frameCount"]),
            float(evidence["frameSeconds"]),
            float(evidence["duration"]),
            start,
            end,
            segments=segments,
            product=product,
        )
        feature_values = _bar_uncertainty._bar_features(
            evidence,
            full_weights,
            winner_weights,
            prediction_coverage=coverage,
            prediction_dominance=dominance,
            prediction_transition_count=max(0, len(sequence) - 1),
            prediction_product=product,
            bar_start=start,
            bar_end=end,
        )
        stage1_product = stage1_row.get("predictionProduct")
        stage1_coverage = _finite(stage1_row.get("predictionCoverage"), "Stage-1 predictionCoverage")
        stage1_dominance = _finite(stage1_row.get("predictionDominance"), "Stage-1 predictionDominance")
        product_matches = product == stage1_product
        reconciliation: dict[str, Any] | None = None
        if not product_matches:
            reconciliation = _reconcile_stage1_product(
                _product_reconciliation_row(
                    track_id=str(sidecar["trackId"]),
                    cell_index=index,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    cell=cell,
                    overlaps=overlaps,
                    feature_product=product,
                    stage1_product=stage1_product,
                    feature_coverage=coverage,
                    stage1_coverage=stage1_coverage,
                    feature_dominance=dominance,
                    stage1_dominance=stage1_dominance,
                )
            )
            product_matches = True
            if product_reconciliations is not None:
                product_reconciliations.append(reconciliation)
        if (
            tuple(feature_values) != FEATURE_NAMES
            or not product_matches
            or not math.isclose(
                coverage,
                stage1_coverage,
                rel_tol=0,
                abs_tol=_EPSILON,
            )
            or not math.isclose(
                dominance,
                stage1_dominance,
                rel_tol=0,
                abs_tol=_EPSILON,
            )
            or stage1_row.get("sourceBeatCellSha256") != canonical_sha256(cell)
            or stage1_row.get("cellIndex") != index
            or stage1_row.get("startMilliseconds") != start_ms
            or stage1_row.get("endMilliseconds") != end_ms
        ):
            raise BeatCellExamplesError("Stage-A feature math disagrees with the frozen Stage-1 cross-checks.")
        payload = {
            "schemaVersion": BEAT_CELL_FEATURE_ROW_SCHEMA,
            "trackId": sidecar["trackId"],
            "cellIndex": index,
            "startMilliseconds": start_ms,
            "endMilliseconds": end_ms,
            "durationMilliseconds": end_ms - start_ms,
            "sourceBeatCellSha256": canonical_sha256(cell),
            "predictionProduct": product,
            "predictionCoverage": coverage,
            "predictionDominance": dominance,
            "featureValues": feature_values,
            "featureValuesSha256": canonical_sha256(feature_values),
            "predictionIdentitySha256": sidecar["predictionIdentitySha256"],
            "constructionSha256": sidecar["constructionSha256"],
        }
        rows.append(validate_beat_cell_feature_row(_hashed(payload, "rowSha256")))
    payload = {
        "schemaVersion": BEAT_CELL_FEATURE_SUMMARY_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "trackId": sidecar["trackId"],
        "canonicalDurationMilliseconds": canonical_duration,
        "coveredDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in rows),
        "predictionIdentity": deepcopy(sidecar["predictionIdentity"]),
        "predictionIdentitySha256": sidecar["predictionIdentitySha256"],
        "audioLineageRowSha256": sidecar["sourceAudioLineageRowSha256"],
        "sourcePredictionCoreSha256": identity["predictionCoreSha256"],
        "sourceUncertaintySha256": identity["uncertaintySha256"],
        "sourceStage1SidecarArtifactSha256": sidecar["artifactSha256"],
        "sourceStage1PredictionSummarySha256": sidecar["predictionSummarySha256"],
        "sourceBeatReceiptTrackSha256": sidecar["sourceBeatReceiptTrackSha256"],
        "constructionSha256": sidecar["constructionSha256"],
        "stageAProjectionSha256": BEAT_CELL_STAGE_A_PROJECTION_SHA256,
        "featureMathProjectionSha256": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
        "featureNames": list(FEATURE_NAMES),
        "rows": rows,
        "rowSetSha256": canonical_sha256(rows),
    }
    return validate_beat_cell_feature_summary(_hashed(payload, "artifactSha256"))


def _render_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _feature_summary_filename(summary: Mapping[str, Any]) -> str:
    return f"{canonical_sha256({'trackId': summary['trackId']})}-{summary['artifactSha256']}.json"


def build_beat_cell_feature_set_manifest(
    summaries: Sequence[Mapping[str, Any]],
    *,
    summary_output_root: Path,
    source_stage1_report_path: Path,
    source_stage1_report_file_sha256: str,
    source_stage1_summary_artifact_set_sha256: str,
    source_stage1_summary_file_set_sha256: str,
) -> dict[str, Any]:
    """Seal a complete already-built Stage-A inventory into one manifest."""

    validated = [validate_beat_cell_feature_summary(summary) for summary in summaries]
    validated.sort(key=lambda summary: str(summary["trackId"]))
    if not validated or len({str(summary["trackId"]) for summary in validated}) != len(validated):
        raise BeatCellExamplesError("Feature-set summaries must be nonempty and unique by trackId.")
    root = Path(os.path.abspath(summary_output_root))
    manifest_rows: list[dict[str, Any]] = []
    global_rows: list[dict[str, Any]] = []
    for summary in validated:
        path = str(root / _feature_summary_filename(summary))
        summary_payload = {
            "trackId": summary["trackId"],
            "path": path,
            "pathSha256": canonical_sha256(path),
            "fileSha256": hashlib.sha256(_render_json(summary)).hexdigest(),
            "artifactSha256": summary["artifactSha256"],
            "predictionIdentitySha256": summary["predictionIdentitySha256"],
            "audioLineageRowSha256": summary["audioLineageRowSha256"],
            "cellCount": len(summary["rows"]),
            "coveredDurationMilliseconds": summary["coveredDurationMilliseconds"],
            "rowSetSha256": summary["rowSetSha256"],
        }
        manifest_rows.append(_hashed(summary_payload, "rowSha256"))
        global_rows.extend(
            {
                "trackId": summary["trackId"],
                "cellIndex": row["cellIndex"],
                "rowSha256": row["rowSha256"],
            }
            for row in summary["rows"]
        )
    report_path = str(Path(os.path.abspath(source_stage1_report_path)))
    payload = {
        "schemaVersion": BEAT_CELL_FEATURE_SET_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "stageAComplete": True,
        "stageAProjectionSha256": BEAT_CELL_STAGE_A_PROJECTION_SHA256,
        "featureMathProjectionSha256": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
        "authorityFileSha256": BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256,
        "authorityCanonicalSha256": BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
        "sourceStage1ReportPathSha256": canonical_sha256(report_path),
        "sourceStage1ReportFileSha256": _sha256(source_stage1_report_file_sha256, "source_stage1_report_file_sha256"),
        "sourceStage1SummaryArtifactSetSha256": _sha256(
            source_stage1_summary_artifact_set_sha256,
            "source_stage1_summary_artifact_set_sha256",
        ),
        "sourceStage1SummaryFileSetSha256": _sha256(
            source_stage1_summary_file_set_sha256,
            "source_stage1_summary_file_set_sha256",
        ),
        "featureNames": list(FEATURE_NAMES),
        "trackCount": len(validated),
        "cellCount": len(global_rows),
        "cellDurationMilliseconds": sum(int(summary["coveredDurationMilliseconds"]) for summary in validated),
        "summaries": manifest_rows,
        "summarySetSha256": canonical_sha256(manifest_rows),
        "featureRowSetSha256": canonical_sha256(global_rows),
    }
    return validate_beat_cell_feature_set_manifest(_hashed(payload, "artifactSha256"))


def validate_beat_cell_feature_set(
    manifest: Mapping[str, Any],
    summaries: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Cross-validate a manifest and every materialized summary in memory."""

    sealed_manifest = validate_beat_cell_feature_set_manifest(manifest)
    sealed_summaries = [validate_beat_cell_feature_summary(summary) for summary in summaries]
    sealed_summaries.sort(key=lambda summary: str(summary["trackId"]))
    bindings = {str(row["trackId"]): row for row in sealed_manifest["summaries"]}
    if [summary["trackId"] for summary in sealed_summaries] != list(bindings):
        raise BeatCellExamplesError("Feature summaries do not exactly cover the manifest track set.")
    global_rows: list[dict[str, Any]] = []
    for summary in sealed_summaries:
        binding = bindings[str(summary["trackId"])]
        if (
            binding["fileSha256"] != hashlib.sha256(_render_json(summary)).hexdigest()
            or binding["artifactSha256"] != summary["artifactSha256"]
            or binding["predictionIdentitySha256"] != summary["predictionIdentitySha256"]
            or binding["audioLineageRowSha256"] != summary["audioLineageRowSha256"]
            or binding["cellCount"] != len(summary["rows"])
            or binding["coveredDurationMilliseconds"] != summary["coveredDurationMilliseconds"]
            or binding["rowSetSha256"] != summary["rowSetSha256"]
        ):
            raise BeatCellExamplesError("A feature summary disagrees with its manifest binding.")
        global_rows.extend(
            {
                "trackId": summary["trackId"],
                "cellIndex": row["cellIndex"],
                "rowSha256": row["rowSha256"],
            }
            for row in summary["rows"]
        )
    if canonical_sha256(global_rows) != sealed_manifest["featureRowSetSha256"]:
        raise BeatCellExamplesError("Feature-set global feature-row projection is stale.")
    return sealed_manifest, sealed_summaries


def validate_beat_cell_feature_set_semantics(
    manifest: Mapping[str, Any],
    summaries: Sequence[Mapping[str, Any]],
    *,
    stage1_sidecars: Mapping[str, Mapping[str, Any]],
    predictions: Mapping[str, Mapping[str, Any]],
    prediction_file_sha256s: Mapping[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Recompute every committed feature from the exact label-blind leaves.

    This is the mandatory Stage-B pre-label barrier.  Mapping hashes alone do
    not prove feature semantics after a coherent reseal, so the exact Stage-1
    sidecar and prediction leaf for every track are required again.
    """

    sealed_manifest, sealed_summaries = validate_beat_cell_feature_set(manifest, summaries)
    expected_tracks = {str(summary["trackId"]) for summary in sealed_summaries}
    if (
        set(stage1_sidecars) != expected_tracks
        or set(predictions) != expected_tracks
        or set(prediction_file_sha256s) != expected_tracks
    ):
        raise BeatCellExamplesError("Semantic Stage-A validation requires the exact sidecar/prediction track set.")
    product_reconciliations: list[dict[str, Any]] = []
    for summary in sealed_summaries:
        track_id = str(summary["trackId"])
        sidecar = validate_stage1_prediction_sidecar(stage1_sidecars[track_id])
        if (
            sidecar["trackId"] != track_id
            or sidecar["artifactSha256"] != summary["sourceStage1SidecarArtifactSha256"]
            or sidecar["predictionIdentitySha256"] != summary["predictionIdentitySha256"]
        ):
            raise BeatCellExamplesError("Feature summary changed its exact Stage-1 sidecar binding.")
        recomputed = build_beat_cell_feature_summary(
            sidecar,
            predictions[track_id],
            prediction_file_sha256=prediction_file_sha256s[track_id],
            product_reconciliations=product_reconciliations,
        )
        if recomputed != summary or canonical_sha256(recomputed) != canonical_sha256(summary):
            raise BeatCellExamplesError(
                "A committed feature summary is not exact under label-blind semantic recomputation."
            )
    _validate_product_reconciliation_inventory(
        product_reconciliations,
        track_ids=expected_tracks,
    )
    return sealed_manifest, sealed_summaries


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
    return _hashed(payload, "rowSha256")


def _source_ci(funnel: Mapping[str, Any], name: str) -> tuple[int, int, int, int, int, int]:
    counts = _mapping(funnel.get("counts"), f"{name}.counts")
    duration = _mapping(funnel.get("durationMilliseconds"), f"{name}.durationMilliseconds")
    return tuple(
        _integer(source.get(field), f"{name}.{kind}.{field}")
        for kind, source in (("counts", counts), ("durationMilliseconds", duration))
        for field in ("C", "I", "E")
    )


def _build_label_audits(
    examples: Sequence[Mapping[str, Any]],
    stage1_artifact: Mapping[str, Any],
) -> dict[str, Any]:
    aggregate_funnel = _mapping(stage1_artifact.get("aggregate"), "Stage-1 aggregate")
    aggregate = _label_audit_row(
        examples,
        scope="aggregate",
        dataset_id=None,
        guitarset_role=None,
        source_funnel_sha256=str(aggregate_funnel["funnelSha256"]),
    )
    dataset_sources = {
        str(row["datasetId"]): row for row in _sequence(stage1_artifact.get("datasets"), "Stage-1 datasets")
    }
    datasets: list[dict[str, Any]] = []
    for dataset_id in _DATASET_IDS:
        source = _mapping(dataset_sources.get(dataset_id), f"Stage-1 dataset {dataset_id!r}")
        selected = [row for row in examples if row["datasetId"] == dataset_id]
        datasets.append(
            _label_audit_row(
                selected,
                scope="dataset",
                dataset_id=dataset_id,
                guitarset_role=None,
                source_funnel_sha256=str(source["funnelSha256"]),
            )
        )
    guitar_source = _mapping(stage1_artifact.get("guitarset"), "Stage-1 guitarset")
    guitar_examples = [row for row in examples if row["datasetId"] == "guitarset"]
    guitar_aggregate = _label_audit_row(
        guitar_examples,
        scope="guitarset",
        dataset_id="guitarset",
        guitarset_role=None,
        source_funnel_sha256=str(guitar_source["funnelSha256"]),
    )
    role_sources = {
        str(row["guitarsetRole"]): row for row in _sequence(guitar_source.get("compSolo"), "Stage-1 guitarset.compSolo")
    }
    roles: list[dict[str, Any]] = []
    for role in ("comp", "solo"):
        source = _mapping(role_sources.get(role), f"Stage-1 GuitarSet role {role!r}")
        selected = [row for row in guitar_examples if row["guitarsetRole"] == role]
        roles.append(
            _label_audit_row(
                selected,
                scope="guitarsetRole",
                dataset_id="guitarset",
                guitarset_role=role,
                source_funnel_sha256=str(source["funnelSha256"]),
            )
        )
    guitarset = _hashed(
        {
            "aggregate": guitar_aggregate,
            "roles": roles,
            "roleSetSha256": canonical_sha256(roles),
        },
        "rowSha256",
    )
    payload = {
        "schemaVersion": BEAT_CELL_LABEL_AUDITS_SCHEMA,
        "aggregate": aggregate,
        "datasets": datasets,
        "datasetSetSha256": canonical_sha256(datasets),
        "guitarset": guitarset,
    }
    audits = _hashed(payload, "auditSha256")

    # Independently bind each emitted C/I support total to Stage-1's exact
    # source funnel, for counts and canonical integer durations.
    comparisons: list[tuple[Mapping[str, Any], Mapping[str, Any], str]] = [
        (aggregate, aggregate_funnel, "aggregate"),
        *[
            (row, _mapping(dataset_sources[str(row["datasetId"])]["funnel"], "dataset funnel"), str(row["datasetId"]))
            for row in datasets
        ],
        (guitar_aggregate, _mapping(guitar_source["funnel"], "GuitarSet funnel"), "guitarset"),
        *[
            (row, _mapping(role_sources[str(row["guitarsetRole"])]["funnel"], "role funnel"), str(row["guitarsetRole"]))
            for row in roles
        ],
    ]
    for row, source_funnel, name in comparisons:
        c_count, i_count, e_count, c_ms, i_ms, e_ms = _source_ci(source_funnel, name)
        if (
            row["correctCount"] != c_count
            or row["incorrectCount"] != i_count
            or row["exampleCount"] != e_count
            or row["correctDurationMilliseconds"] != c_ms
            or row["incorrectDurationMilliseconds"] != i_ms
            or row["exampleDurationMilliseconds"] != e_ms
        ):
            raise BeatCellExamplesError(f"Examples do not reconcile to Stage-1 C/I support for {name}.")
    return _validate_label_audits(audits, examples)


def _stage_b_reconciliation_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    value = _mapping(row, "Stage-B product reconciliation")
    return {field: value.get(field) for field in _STAGE_B_RECONCILIATION_FIELDS}


def _validate_stage_b_product_reconciliations(
    rows: Sequence[Mapping[str, Any]],
    *,
    track_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    observed = [_stage_b_reconciliation_projection(row) for row in rows]
    observed.sort(key=lambda row: (str(row.get("trackId")), int(row.get("cellIndex", -1))))
    expected = [_stage_b_reconciliation_projection(row) for row in _expected_product_reconciliations()]
    if track_ids is not None:
        expected = [row for row in expected if str(row.get("trackId")) in track_ids]
    expected.sort(key=lambda row: (str(row.get("trackId")), int(row.get("cellIndex", -1))))
    if observed != expected or canonical_sha256(observed) != canonical_sha256(expected):
        raise BeatCellExamplesError("Stage-B ineligible product-reconciliation inventory is not exact.")
    return observed


def build_beat_cell_examples(
    stage1_artifact: Mapping[str, Any],
    feature_set_manifest: Mapping[str, Any],
    feature_summaries: Sequence[Mapping[str, Any]],
    *,
    stage1_sidecars: Mapping[str, Mapping[str, Any]],
    predictions: Mapping[str, Mapping[str, Any]],
    prediction_file_sha256s: Mapping[str, str],
    source_stage1_file_sha256: str,
    source_stage1_canonical_sha256: str,
    source_feature_set_file_sha256: str,
) -> dict[str, Any]:
    """Perform Stage B after semantic closure of the committed Stage-A set."""

    # Deliberately complete both structural and semantic Stage-A validation
    # before the first nested access to the labeled Stage-1 artifact.
    manifest, summaries = validate_beat_cell_feature_set_semantics(
        feature_set_manifest,
        feature_summaries,
        stage1_sidecars=stage1_sidecars,
        predictions=predictions,
        prediction_file_sha256s=prediction_file_sha256s,
    )
    stage1_mapping = _mapping(stage1_artifact, "Stage-1 artifact")
    try:
        stage1 = _stage1.validate_beat_cell_stage1_artifact(stage1_mapping)
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Stage-1 artifact failed full standalone validation.") from error
    stage1_file_sha256 = _sha256(source_stage1_file_sha256, "source_stage1_file_sha256")
    stage1_canonical_sha256 = _sha256(source_stage1_canonical_sha256, "source_stage1_canonical_sha256")
    feature_set_file_sha256 = _sha256(source_feature_set_file_sha256, "source_feature_set_file_sha256")
    if (
        canonical_sha256(stage1) != stage1_canonical_sha256
        or manifest["sourceStage1ReportFileSha256"] != stage1_file_sha256
        or stage1.get("stage1Passed") is not True
        or _mapping(stage1.get("decision"), "Stage-1 decision").get("selectorStageMayRunInNewSealedDevelopmentCycle")
        is not True
    ):
        raise BeatCellExamplesError("Stage B is not bound to one passed Stage-1 source.")
    summaries_by_id = {str(summary["trackId"]): summary for summary in summaries}
    tracks = list(_sequence(stage1.get("tracks"), "Stage-1 tracks"))
    if {str(track["trackId"]) for track in tracks} != set(summaries_by_id):
        raise BeatCellExamplesError("Stage-1 and feature-set track identities differ.")

    examples: list[dict[str, Any]] = []
    logical_keys: set[tuple[str, int]] = set()
    stage_b_product_reconciliations: list[dict[str, Any]] = []
    for raw_track in tracks:
        track = _mapping(raw_track, "Stage-1 track")
        track_id = str(track["trackId"])
        summary = summaries_by_id[track_id]
        sidecar = stage1_sidecars[track_id]
        if (
            track.get("predictionIdentitySha256") != summary["predictionIdentitySha256"]
            or track.get("predictionIdentitySha256") != sidecar["predictionIdentitySha256"]
            or _mapping(track.get("predictionOnlySummary"), "track.predictionOnlySummary").get("artifactSha256")
            != summary["sourceStage1SidecarArtifactSha256"]
            or track.get("constructionSha256") != summary["constructionSha256"]
            or _mapping(track.get("predictionIdentity"), "track.predictionIdentity").get("audioLineageRowSha256")
            != summary["audioLineageRowSha256"]
        ):
            raise BeatCellExamplesError("Stage-1 track is not exactly bound to its feature summary.")
        feature_rows = {int(row["cellIndex"]): row for row in summary["rows"]}
        outcomes = list(_sequence(track.get("cellOutcomes"), "Stage-1 track.cellOutcomes"))
        if len(feature_rows) != len(outcomes):
            raise BeatCellExamplesError("Feature and Stage-1 cell inventories differ.")
        for raw_outcome in outcomes:
            outcome = _mapping(raw_outcome, "Stage-1 cell outcome")
            classification = outcome.get("classification")
            cell_index = _integer(outcome.get("cellIndex"), "Stage-1 outcome.cellIndex")
            feature = feature_rows.get(cell_index)
            if feature is None:
                raise BeatCellExamplesError("A Stage-1 outcome has no exact feature row.")
            if feature["predictionProduct"] != outcome.get("predictionProduct"):
                reconciliation = {
                    "trackId": track_id,
                    "cellIndex": cell_index,
                    "startMilliseconds": feature["startMilliseconds"],
                    "endMilliseconds": feature["endMilliseconds"],
                    "sourceBeatCellSha256": feature["sourceBeatCellSha256"],
                    "featureProduct": feature["predictionProduct"],
                    "stage1Product": outcome.get("predictionProduct"),
                    "featureCoverage": feature["predictionCoverage"],
                    "stage1Coverage": outcome.get("predictionCoverage"),
                    "featureDominance": feature["predictionDominance"],
                    "stage1Dominance": outcome.get("predictionDominance"),
                }
                if (
                    classification not in {"U", "N"}
                    or feature["sourceBeatCellSha256"] != outcome.get("sourceBeatCellSha256")
                    or feature["durationMilliseconds"] != outcome.get("durationMilliseconds")
                    or not _prediction_is_structurally_ineligible(
                        feature["predictionProduct"],
                        float(feature["predictionCoverage"]),
                        float(feature["predictionDominance"]),
                    )
                    or not _prediction_is_structurally_ineligible(
                        outcome.get("predictionProduct"),
                        _finite(outcome.get("predictionCoverage"), "outcome.predictionCoverage"),
                        _finite(outcome.get("predictionDominance"), "outcome.predictionDominance"),
                    )
                    or _stage_b_reconciliation_projection(reconciliation)
                    not in [_stage_b_reconciliation_projection(row) for row in _expected_product_reconciliations()]
                ):
                    raise BeatCellExamplesError(
                        "A Stage-1/feature product mismatch is not an exact ineligible reconciliation."
                    )
                stage_b_product_reconciliations.append(reconciliation)
            if classification in {"U", "N"}:
                continue
            if classification not in {"C", "I"}:
                raise BeatCellExamplesError("Stage-1 outcome is not terminal U/N/C/I.")
            if (
                feature["sourceBeatCellSha256"] != outcome.get("sourceBeatCellSha256")
                or feature["durationMilliseconds"] != outcome.get("durationMilliseconds")
                or feature["predictionProduct"] != outcome.get("predictionProduct")
                or not math.isclose(
                    float(feature["predictionCoverage"]),
                    _finite(outcome.get("predictionCoverage"), "outcome.predictionCoverage"),
                    rel_tol=0,
                    abs_tol=_EPSILON,
                )
                or not math.isclose(
                    float(feature["predictionDominance"]),
                    _finite(outcome.get("predictionDominance"), "outcome.predictionDominance"),
                    rel_tol=0,
                    abs_tol=_EPSILON,
                )
            ):
                raise BeatCellExamplesError("Stage-1 outcome and label-blind feature row disagree.")
            logical_key = (track_id, cell_index)
            if logical_key in logical_keys:
                raise BeatCellExamplesError("Stage B repeated a logical (trackId,cellIndex).")
            logical_keys.add(logical_key)
            payload: dict[str, Any] = {
                "schemaVersion": BEAT_CELL_EXAMPLE_SCHEMA,
                "exampleKey": "",
                "trackId": track_id,
                "cellIndex": cell_index,
                "durationMilliseconds": feature["durationMilliseconds"],
                "sourceBeatCellSha256": feature["sourceBeatCellSha256"],
                "predictionIdentitySha256": summary["predictionIdentitySha256"],
                "featureRowSha256": feature["rowSha256"],
                "featureSummaryArtifactSha256": summary["artifactSha256"],
                "featureSetArtifactSha256": manifest["artifactSha256"],
                "audioLineageRowSha256": summary["audioLineageRowSha256"],
                "featureValues": deepcopy(feature["featureValues"]),
                "featureValuesSha256": feature["featureValuesSha256"],
                "stage1OutcomeRowSha256": outcome["rowSha256"],
                "stage1ArtifactSha256": stage1["artifactSha256"],
                "sourceGroupTrackRowSha256": track["sourceGroupTrackMetadataSha256"],
                "datasetId": track["datasetId"],
                "role": track["role"],
                "guitarsetRole": track["guitarsetRole"],
                "confidenceGroupId": track["confidenceGroupId"],
                "correct": classification == "C",
            }
            payload["exampleKey"] = canonical_sha256(_example_key_payload(payload))
            examples.append(_hashed(payload, "exampleSha256"))
    _validate_stage_b_product_reconciliations(
        stage_b_product_reconciliations,
        track_ids=set(summaries_by_id),
    )
    examples.sort(key=lambda row: str(row["exampleKey"]))
    label_audits = _build_label_audits(examples, stage1)
    reference_audit = deepcopy(stage1["referenceEndpointReconciliationAudit"])
    payload = {
        "schemaVersion": BEAT_CELL_EXAMPLES_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": False,
        "selectorTrainingInput": True,
        "stageBProjectionSha256": BEAT_CELL_STAGE_B_PROJECTION_SHA256,
        "featureMathProjectionSha256": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
        "featureNames": list(FEATURE_NAMES),
        "sourceStage1FileSha256": stage1_file_sha256,
        "sourceStage1CanonicalSha256": stage1_canonical_sha256,
        "sourceStage1ArtifactSha256": stage1["artifactSha256"],
        "sourceStage1DecisionSha256": stage1["decision"]["decisionSha256"],
        "sourceStage1GateSetSha256": stage1["gateSetSha256"],
        "sourceStage1TrackSetSha256": stage1["trackSetSha256"],
        "sourceStage1SourceContractSha256": stage1["sourceContractSha256"],
        "sourceFeatureSetFileSha256": feature_set_file_sha256,
        "sourceFeatureSetArtifactSha256": manifest["artifactSha256"],
        "sourceFeatureSummarySetSha256": manifest["summarySetSha256"],
        "sourceFeatureRowSetSha256": manifest["featureRowSetSha256"],
        "labelAudits": label_audits,
        "labelAuditsSha256": label_audits["auditSha256"],
        "referenceEndpointReconciliationAudit": reference_audit,
        "referenceEndpointReconciliationAuditSha256": reference_audit["auditSha256"],
        "trackCount": len({str(row["trackId"]) for row in examples}),
        "confidenceGroupCount": len({str(row["confidenceGroupId"]) for row in examples}),
        "exampleCount": len(examples),
        "exampleDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in examples),
        "examples": examples,
        "exampleSetSha256": canonical_sha256(examples),
    }
    return validate_beat_cell_examples_artifact(_hashed(payload, "artifactSha256"))


def _reject_constant(value: str) -> None:
    raise BeatCellExamplesError(f"JSON contains non-finite constant {value!r}.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise BeatCellExamplesError(f"JSON contains duplicate object key {key!r}.")
        output[key] = value
    return output


def _strict_json(raw: bytes, name: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BeatCellExamplesError(f"Could not parse {name} as strict UTF-8 JSON.") from error
    return deepcopy(dict(_mapping(value, name)))


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, name: str) -> None:
    absolute = _absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        try:
            metadata = os.lstat(current)
        except OSError as error:
            raise BeatCellExamplesError(f"Could not inspect {name} path component.") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise BeatCellExamplesError(f"{name} contains a symlinked path component.")


def _identity(metadata: os.stat_result) -> tuple[int, int]:
    return metadata.st_dev, metadata.st_ino


def _sealed_read(path: Path, name: str) -> tuple[bytes, tuple[int, int]]:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_descriptor = os.open(absolute.parent, parent_flags)
    except OSError as error:
        raise BeatCellExamplesError(f"Could not retain {name} parent directory.") from error
    try:
        try:
            descriptor = os.open(absolute.name, file_flags, dir_fd=parent_descriptor)
        except OSError as error:
            raise BeatCellExamplesError(f"Could not open {name} without following links.") from error
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise BeatCellExamplesError(f"{name} must be a regular file.")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(descriptor)
        visible = os.stat(absolute.name, dir_fd=parent_descriptor, follow_symlinks=False)
        if _identity(visible) != _identity(opened):
            raise BeatCellExamplesError(f"{name} changed while it was read.")
        return raw, _identity(opened)
    finally:
        os.close(parent_descriptor)


def _verify_snapshot(path: Path, raw: bytes, inode: tuple[int, int], name: str) -> None:
    current_raw, current_inode = _sealed_read(path, name)
    if current_inode != inode or current_raw != raw:
        raise BeatCellExamplesError(f"{name} changed before publication.")


def _capture_directory_identity(path: Path, name: str) -> tuple[int, int]:
    descriptor, inode = _open_existing_directory(path, name)
    try:
        _verify_directory_path(path, descriptor, inode, name)
        return inode
    finally:
        os.close(descriptor)


def _run_with_exact_directory(
    path: Path,
    expected_inode: tuple[int, int],
    name: str,
    action: Any,
) -> Any:
    """Hold one exact root open across an action and recheck its path after."""

    descriptor, inode = _open_existing_directory(path, name)
    try:
        if inode != expected_inode:
            raise BeatCellExamplesError(f"{name} inode changed before publication.")
        result = action()
        _verify_directory_path(path, descriptor, expected_inode, name)
        return result
    finally:
        os.close(descriptor)


def _capture_admitted_file_identity(path: Path, name: str) -> dict[str, Any]:
    """Capture a lexical entry and its resolved regular target without reading bytes."""

    absolute = _absolute(path)
    _reject_symlink_components(absolute.parent, f"{name} parent")
    try:
        lexical = os.lstat(absolute)
    except OSError as error:
        raise BeatCellExamplesError(f"Could not inspect {name} lexical entry.") from error
    if stat.S_ISLNK(lexical.st_mode):
        try:
            symlink_target: str | None = os.readlink(absolute)
            resolved = absolute.resolve(strict=True)
        except OSError as error:
            raise BeatCellExamplesError(f"Could not resolve {name} symlink.") from error
    elif stat.S_ISREG(lexical.st_mode):
        symlink_target = None
        resolved = absolute
    else:
        raise BeatCellExamplesError(f"{name} must be a regular file or a final-component symlink.")

    _reject_symlink_components(resolved, f"{name} resolved target")
    try:
        descriptor = os.open(resolved, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as error:
        raise BeatCellExamplesError(f"Could not open {name} resolved target.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise BeatCellExamplesError(f"{name} resolved target must be a regular file.")
    finally:
        os.close(descriptor)
    try:
        visible_target = os.stat(resolved, follow_symlinks=False)
        visible_lexical = os.lstat(absolute)
        current_symlink_target = os.readlink(absolute) if symlink_target is not None else None
        current_resolved = absolute.resolve(strict=True) if symlink_target is not None else absolute
    except OSError as error:
        raise BeatCellExamplesError(f"{name} changed while its identity was captured.") from error
    if (
        _identity(visible_target) != _identity(opened)
        or _identity(visible_lexical) != _identity(lexical)
        or stat.S_IFMT(visible_lexical.st_mode) != stat.S_IFMT(lexical.st_mode)
        or current_symlink_target != symlink_target
        or current_resolved != resolved
    ):
        raise BeatCellExamplesError(f"{name} changed while its identity was captured.")
    if symlink_target is None and _identity(lexical) != _identity(opened):
        raise BeatCellExamplesError(f"{name} changed while its identity was captured.")
    return {
        "path": str(absolute),
        "lexicalInode": _identity(lexical),
        "symlinkTarget": symlink_target,
        "resolvedPath": str(resolved),
        "resolvedInode": _identity(opened),
    }


def _capture_admitted_file_projection(paths: Sequence[Path], name: str) -> dict[str, dict[str, Any]]:
    absolute_paths = sorted({str(_absolute(path)) for path in paths})
    if not absolute_paths:
        raise BeatCellExamplesError(f"{name} must contain at least one file.")
    snapshots = {path: _capture_admitted_file_identity(Path(path), f"{name} {path!r}") for path in absolute_paths}
    # Close the collection window: an early entry may not change while later
    # entries are being captured.
    _verify_admitted_file_projection(snapshots, name)
    return snapshots


def _verify_admitted_file_projection(
    snapshots: Mapping[str, Mapping[str, Any]],
    name: str,
) -> None:
    for path in sorted(snapshots):
        current = _capture_admitted_file_identity(Path(path), f"{name} {path!r}")
        if current != snapshots[path]:
            raise BeatCellExamplesError(f"{name} file identity changed before publication: {path!r}.")


def _declared_repo_path(value: Any, name: str) -> Path:
    relative = Path(_string(value, name))
    if relative.is_absolute() or relative.name == "" or ".." in relative.parts:
        raise BeatCellExamplesError(f"{name} must be a repository-root-relative path without traversal.")
    path = _absolute(_runtime_beat_grid._REPO_ROOT / relative)
    try:
        path.relative_to(_absolute(_runtime_beat_grid._REPO_ROOT))
    except ValueError as error:  # pragma: no cover - lexical guard above is primary
        raise BeatCellExamplesError(f"{name} escapes the repository root.") from error
    return path


def _stage_a_admitted_file_paths(
    runtime: Mapping[str, Any],
    receipt: Mapping[str, Any],
    audio_lineage: Mapping[str, Any],
    runtime_root: Path,
    runtime_manifest_path: Path,
    receipt_path: Path,
    audio_lineage_path: Path,
) -> tuple[list[Path], Path]:
    """Project every filesystem leaf opened by the two strict Stage-A validators."""

    paths: list[Path] = [
        _absolute(runtime_root / "manifest.json"),
        _absolute(runtime_manifest_path),
        _absolute(receipt_path),
        _absolute(audio_lineage_path),
    ]
    for index, raw in enumerate(_sequence(runtime.get("timingArtifacts"), "runtime timingArtifacts")):
        row = _mapping(raw, f"runtime timingArtifacts[{index}]")
        filename = _string(row.get("timingFile"), f"runtime timingArtifacts[{index}].timingFile")
        if Path(filename).name != filename:
            raise BeatCellExamplesError("Runtime timing leaves must be flat filenames.")
        paths.append(_absolute(runtime_root / filename))

    paths.extend(
        (
            _runtime_bar_grid._CLIENT,
            _runtime_bar_grid._WORKER,
            _runtime_bar_grid._RUNNER,
            _runtime_bar_grid._GENERATOR,
            _runtime_bar_grid._BROWSER,
            _runtime_beat_grid._BASE_RUNNER,
            _runtime_beat_grid._GENERATOR,
            _runtime_beat_grid._CLIENT_ALIAS,
            _runtime_beat_grid._WORKER_ALIAS,
        )
    )
    node_location = shutil.which("node")
    if not node_location:
        raise BeatCellExamplesError("The pinned Node executable is unavailable.")
    node_path = _absolute(Path(node_location))
    paths.append(node_path)

    player = _mapping(receipt.get("playerReplayContract"), "beat receipt playerReplayContract")
    for index, raw in enumerate(_sequence(player.get("resources"), "player resources")):
        row = _mapping(raw, f"player resources[{index}]")
        paths.append(_declared_repo_path(row.get("repoRelativePath"), f"player resources[{index}].repoRelativePath"))
    for index, raw in enumerate(_sequence(player.get("documentLoads"), "player documentLoads")):
        row = _mapping(raw, f"player documentLoads[{index}]")
        paths.append(_declared_repo_path(row.get("documentPath"), f"player documentLoads[{index}].documentPath"))
        paths.append(_declared_repo_path(row.get("resourcePath"), f"player documentLoads[{index}].resourcePath"))

    bindings = _mapping(audio_lineage.get("manifestBindings"), "audio lineage manifestBindings")
    for field in ("winnerCacheManifest", "developmentSourceManifest", "dashengCacheManifest"):
        binding = _mapping(bindings.get(field), f"audio lineage manifestBindings.{field}")
        paths.append(Path(_string(binding.get("path"), f"audio lineage manifestBindings.{field}.path")))
    extractor = _mapping(audio_lineage.get("extractorContract"), "audio lineage extractorContract")
    for field in ("sourceFile", "dependencyLockFile"):
        paths.append(Path(_string(extractor.get(field), f"audio lineage extractorContract.{field}")))
    for index, raw in enumerate(_sequence(audio_lineage.get("tracks"), "audio lineage tracks")):
        row = _mapping(raw, f"audio lineage tracks[{index}]")
        paths.append(Path(_string(row.get("audioPath"), f"audio lineage tracks[{index}].audioPath")))
        paths.append(Path(_string(row.get("cachedFeaturePath"), f"audio lineage tracks[{index}].cachedFeaturePath")))
    return paths, node_path


def _capture_stage_a_admitted_inputs(
    runtime: Mapping[str, Any],
    receipt: Mapping[str, Any],
    audio_lineage: Mapping[str, Any],
    runtime_root: Path,
    runtime_manifest_path: Path,
    receipt_path: Path,
    audio_lineage_path: Path,
) -> dict[str, Any]:
    paths, node_path = _stage_a_admitted_file_paths(
        runtime,
        receipt,
        audio_lineage,
        runtime_root,
        runtime_manifest_path,
        receipt_path,
        audio_lineage_path,
    )
    return {
        "files": _capture_admitted_file_projection(paths, "Stage-A admitted input"),
        "nodeWhichPath": str(node_path),
    }


def _verify_stage_a_admitted_inputs(snapshot: Mapping[str, Any]) -> None:
    node_location = shutil.which("node")
    if not node_location or str(_absolute(Path(node_location))) != snapshot.get("nodeWhichPath"):
        raise BeatCellExamplesError("The pinned Node executable resolution changed before publication.")
    _verify_admitted_file_projection(
        _mapping(snapshot.get("files"), "Stage-A admitted input files"),
        "Stage-A admitted input",
    )


def _read_flat_directory(
    root: Path,
    name: str,
) -> tuple[dict[str, tuple[bytes, tuple[int, int]]], tuple[int, int]]:
    absolute = _absolute(root)
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise BeatCellExamplesError(f"{name} must be an existing non-symlink directory.") from error
    directory_inode = _identity(os.fstat(descriptor))
    snapshots: dict[str, tuple[bytes, tuple[int, int]]] = {}
    try:
        names = sorted(os.listdir(descriptor))
        if not names or any(Path(item).name != item or not item.endswith(".json") for item in names):
            raise BeatCellExamplesError(f"{name} must be a nonempty flat JSON-only directory.")
        for filename in names:
            try:
                file_descriptor = os.open(
                    filename,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except OSError as error:
                raise BeatCellExamplesError(f"Could not open {name}/{filename}.") from error
            try:
                opened = os.fstat(file_descriptor)
                if not stat.S_ISREG(opened.st_mode):
                    raise BeatCellExamplesError(f"{name}/{filename} must be a regular file.")
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(file_descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                raw = b"".join(chunks)
            finally:
                os.close(file_descriptor)
            visible = os.stat(filename, dir_fd=descriptor, follow_symlinks=False)
            if _identity(visible) != _identity(opened):
                raise BeatCellExamplesError(f"{name}/{filename} changed while it was read.")
            snapshots[filename] = (raw, _identity(opened))
        _verify_directory_path(absolute, descriptor, directory_inode, name)
        return snapshots, directory_inode
    finally:
        os.close(descriptor)


def _parse_flat_json_snapshots(
    snapshots: Mapping[str, tuple[bytes, tuple[int, int]]],
    name: str,
) -> dict[str, dict[str, Any]]:
    return {filename: _strict_json(snapshots[filename][0], f"{name}/{filename}") for filename in snapshots}


def _read_flat_json_directory(
    root: Path,
    name: str,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, tuple[bytes, tuple[int, int]]],
    tuple[int, int],
]:
    snapshots, directory_inode = _read_flat_directory(root, name)
    return _parse_flat_json_snapshots(snapshots, name), snapshots, directory_inode


def _verify_flat_directory(
    root: Path,
    snapshots: Mapping[str, tuple[bytes, tuple[int, int]]],
    directory_inode: tuple[int, int],
    name: str,
) -> None:
    absolute = _absolute(root)
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise BeatCellExamplesError(f"{name} changed before publication.") from error
    try:
        if _identity(os.fstat(descriptor)) != directory_inode or sorted(os.listdir(descriptor)) != sorted(snapshots):
            raise BeatCellExamplesError(f"{name} inventory changed before publication.")
        for filename, (expected_raw, expected_inode) in snapshots.items():
            try:
                file_descriptor = os.open(
                    filename,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except OSError as error:
                raise BeatCellExamplesError(f"{name}/{filename} changed before publication.") from error
            try:
                metadata = os.fstat(file_descriptor)
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(file_descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                if _identity(metadata) != expected_inode or b"".join(chunks) != expected_raw:
                    raise BeatCellExamplesError(f"{name}/{filename} changed before publication.")
            finally:
                os.close(file_descriptor)
        _verify_directory_path(absolute, descriptor, directory_inode, name)
    finally:
        os.close(descriptor)


def _sidecar_inventory(
    values: Mapping[str, Mapping[str, Any]],
    snapshots: Mapping[str, tuple[bytes, tuple[int, int]]],
) -> tuple[dict[str, dict[str, Any]], str, str]:
    sidecars: dict[str, dict[str, Any]] = {}
    artifact_projection: list[dict[str, Any]] = []
    for filename in sorted(values):
        sidecar = validate_stage1_prediction_sidecar(values[filename])
        track_id = str(sidecar["trackId"])
        if track_id in sidecars or filename != _stage1._summary_filename(track_id, str(sidecar["artifactSha256"])):
            raise BeatCellExamplesError("Stage-1 sidecar inventory has a duplicate or stale filename.")
        sidecars[track_id] = sidecar
        artifact_projection.append({"trackId": track_id, "artifactSha256": sidecar["artifactSha256"]})
    artifact_projection.sort(key=lambda row: str(row["trackId"]))
    file_projection = sorted(
        [
            {"name": filename, "fileSha256": hashlib.sha256(snapshots[filename][0]).hexdigest()}
            for filename in snapshots
        ],
        key=lambda row: str(row["name"]),
    )
    return sidecars, canonical_sha256(artifact_projection), canonical_sha256(file_projection)


def _flat_file_set_sha256(snapshots: Mapping[str, tuple[bytes, tuple[int, int]]]) -> str:
    return canonical_sha256(
        sorted(
            [
                {"name": filename, "fileSha256": hashlib.sha256(snapshots[filename][0]).hexdigest()}
                for filename in snapshots
            ],
            key=lambda row: str(row["name"]),
        )
    )


def _prediction_inputs(
    sidecars: Mapping[str, Mapping[str, Any]],
    benchmark_root: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, tuple[Path, bytes, tuple[int, int]]],
]:
    absolute_root = _absolute(benchmark_root)
    _reject_symlink_components(absolute_root, "benchmark root")
    predictions: dict[str, dict[str, Any]] = {}
    file_sha256s: dict[str, str] = {}
    snapshots: dict[str, tuple[Path, bytes, tuple[int, int]]] = {}
    for track_id in sorted(sidecars):
        identity = _mapping(sidecars[track_id]["predictionIdentity"], "prediction identity")
        relative = Path(_string(identity.get("predictionFile"), "prediction identity.predictionFile"))
        if relative.is_absolute() or ".." in relative.parts or relative.name == "":
            raise BeatCellExamplesError("Prediction identity path must be repository-root-relative without traversal.")
        path = _absolute(absolute_root / relative)
        try:
            path.relative_to(absolute_root)
        except ValueError as error:
            raise BeatCellExamplesError("Prediction identity path escapes the pinned benchmark root.") from error
        raw, inode = _sealed_read(path, f"prediction leaf {track_id!r}")
        file_sha256 = hashlib.sha256(raw).hexdigest()
        if file_sha256 != identity.get("predictionSha256"):
            raise BeatCellExamplesError("Prediction leaf raw-file hash is stale.")
        prediction = _strict_json(raw, f"prediction leaf {track_id!r}")
        predictions[track_id] = prediction
        file_sha256s[track_id] = file_sha256
        snapshots[track_id] = (path, raw, inode)
    return predictions, file_sha256s, snapshots


def _verify_prediction_inputs(snapshots: Mapping[str, tuple[Path, bytes, tuple[int, int]]]) -> None:
    for track_id, (path, raw, inode) in snapshots.items():
        _verify_snapshot(path, raw, inode, f"prediction leaf {track_id!r}")


def _official_label_blind_sources() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, Any],
]:
    source = BEAT_CELL_STAGE2_SOURCE_INPUTS
    summary_root = Path(str(source["stage1SummaryRoot"]))
    sidecar_snapshots, sidecar_root_inode = _read_flat_directory(summary_root, "Stage-1 prediction-only summary root")
    if (
        len(sidecar_snapshots) != source["trackCount"]
        or _flat_file_set_sha256(sidecar_snapshots) != source["stage1SummaryFileSet"]["sha256"]
    ):
        raise BeatCellExamplesError("Stage-1 sidecar raw-file inventory is not the exact preregistered set.")
    sidecar_values = _parse_flat_json_snapshots(sidecar_snapshots, "Stage-1 prediction-only summary root")
    sidecars, artifact_set_sha256, file_set_sha256 = _sidecar_inventory(sidecar_values, sidecar_snapshots)
    prediction_identity_set_sha256 = canonical_sha256(
        sorted(
            [
                {
                    "trackId": track_id,
                    "predictionIdentitySha256": sidecar["predictionIdentitySha256"],
                }
                for track_id, sidecar in sidecars.items()
            ],
            key=lambda row: str(row["trackId"]),
        )
    )
    if (
        len(sidecars) != source["trackCount"]
        or artifact_set_sha256 != source["stage1SummaryArtifactSet"]["sha256"]
        or file_set_sha256 != source["stage1SummaryFileSet"]["sha256"]
        or prediction_identity_set_sha256 != source["predictionIdentitySetSha256"]
    ):
        raise BeatCellExamplesError("Stage-1 sidecar inventory is not the exact preregistered set.")
    benchmark_root = Path(str(source["benchmarkRoot"]))
    benchmark_root_inode = _capture_directory_identity(benchmark_root, "benchmark root")
    predictions, prediction_sha256s, prediction_snapshots = _run_with_exact_directory(
        benchmark_root,
        benchmark_root_inode,
        "benchmark root",
        lambda: _prediction_inputs(sidecars, benchmark_root),
    )
    snapshot = {
        "summaryRoot": summary_root,
        "sidecars": sidecar_snapshots,
        "summaryRootInode": sidecar_root_inode,
        "benchmarkRoot": benchmark_root,
        "benchmarkRootInode": benchmark_root_inode,
        "predictions": prediction_snapshots,
    }
    return sidecars, predictions, prediction_sha256s, snapshot


def _verify_official_label_blind_sources(snapshot: Mapping[str, Any]) -> None:
    _verify_flat_directory(
        snapshot["summaryRoot"],
        snapshot["sidecars"],
        snapshot["summaryRootInode"],
        "Stage-1 prediction-only summary root",
    )
    _run_with_exact_directory(
        snapshot["benchmarkRoot"],
        snapshot["benchmarkRootInode"],
        "benchmark root",
        lambda: _verify_prediction_inputs(snapshot["predictions"]),
    )


def _crosscheck_stage_a_audio_projection(
    sidecars: Mapping[str, Mapping[str, Any]],
    audio_projection: Mapping[str, Any],
    expected_projection_sha256: str,
) -> None:
    """Bind every sidecar identity to the directly validated audio lineage."""

    audio_rows = {
        str(row["trackId"]): row for row in _sequence(audio_projection.get("tracks"), "audio-lineage projection.tracks")
    }
    if audio_projection.get("projectionSha256") != expected_projection_sha256 or set(audio_rows) != set(sidecars):
        raise BeatCellExamplesError("Audio-lineage projection is not the exact frozen Stage-1 projection.")
    for track_id, sidecar in sidecars.items():
        identity = _mapping(sidecar["predictionIdentity"], "sidecar prediction identity")
        audio_row = _mapping(audio_rows[track_id], "audio-lineage projection row")
        if (
            sidecar["sourceAudioLineageRowSha256"] != audio_row.get("rowSha256")
            or identity.get("audioLineageRowSha256") != audio_row.get("rowSha256")
            or identity.get("sourceAudioSha256") != audio_row.get("sourceAudioSha256")
            or identity.get("cachedFeatureArraySha256") != audio_row.get("cachedArraySha256")
            or identity.get("freshFeatureArraySha256") != audio_row.get("freshArraySha256")
            or identity.get("canonicalDurationMilliseconds") != audio_row.get("canonicalDurationMilliseconds")
        ):
            raise BeatCellExamplesError("A sidecar/prediction identity changed its audio-lineage row.")


def _verify_owned_json_entry(
    parent_descriptor: int,
    name: str,
    expected_inode: tuple[int, int],
) -> None:
    try:
        visible = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as error:
        raise BeatCellExamplesError("Published Stage-2 JSON output name changed during publication.") from error
    if not stat.S_ISREG(visible.st_mode) or _publication_identity(visible) != expected_inode:
        raise BeatCellExamplesError("Published Stage-2 JSON output name changed during publication.")


def _unlink_all_owned_json_entries(
    parent_descriptor: int,
    expected_inode: tuple[int, int],
) -> None:
    """Best-effort cleanup of every same-parent name for our output inode."""

    try:
        names = os.listdir(parent_descriptor)
    except OSError:
        return
    for name in names:
        _unlink_owned_entry(parent_descriptor, name, expected_inode)


def _remove_all_owned_directories(
    parent_descriptor: int,
    expected_inode: tuple[int, int],
) -> None:
    """Remove every safely empty same-parent name for an owned directory."""

    try:
        names = os.listdir(parent_descriptor)
    except OSError:
        return
    for name in names:
        _remove_owned_directory(parent_descriptor, name, expected_inode)


def _read_owned_json_entry(
    parent_descriptor: int,
    name: str,
    expected_inode: tuple[int, int],
) -> bytes:
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
    except OSError as error:
        raise BeatCellExamplesError("Could not reopen the owned Stage-2 JSON output.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _publication_identity(opened) != expected_inode:
            raise BeatCellExamplesError("Published Stage-2 JSON output inode changed during publication.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _publish_new_json_with_precommit(
    output_path: Path,
    artifact: Mapping[str, Any],
    precommit: Any,
) -> None:
    """Publish one new JSON only after the last possible source recheck."""

    output = _preflight_new_json(output_path, "beat-cell Stage-2 JSON output")
    parent_descriptor, parent_inode = _open_or_create_directory(output.parent, "beat-cell Stage-2 JSON output parent")
    temporary: tuple[str, tuple[int, int]] | None = None
    linked: tuple[str, tuple[int, int]] | None = None
    try:
        if _entry_stat(parent_descriptor, output.name) is not None:
            raise BeatCellExamplesError("Stage-2 JSON output appeared before publication.")
        rendered = _render_json(artifact)
        temporary = _create_temporary_json(parent_descriptor, output.name, rendered)
        temporary_name, temporary_inode = temporary
        # This callback is deliberately the final operation before link(2).
        # EEXIST from link(2) handles a destination created during the callback.
        precommit()
        try:
            os.link(
                temporary_name,
                output.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise BeatCellExamplesError("Stage-2 JSON output was concurrently created; refusing overwrite.") from error
        linked = (output.name, temporary_inode)
        # Close the link window before consuming or certifying the published
        # name.  The callback is required to be idempotent.
        precommit()
        _verify_owned_json_entry(parent_descriptor, output.name, temporary_inode)
        if _read_owned_json_entry(parent_descriptor, output.name, temporary_inode) != rendered:
            raise BeatCellExamplesError("Published Stage-2 JSON did not round-trip exactly.")
        _verify_owned_json_entry(parent_descriptor, output.name, temporary_inode)
        os.fsync(parent_descriptor)
        _verify_owned_json_entry(parent_descriptor, output.name, temporary_inode)
        _verify_directory_path(
            output.parent,
            parent_descriptor,
            parent_inode,
            "beat-cell Stage-2 JSON output parent",
        )
        _verify_owned_json_entry(parent_descriptor, output.name, temporary_inode)
        _unlink_owned_entry(parent_descriptor, temporary_name, temporary_inode)
        temporary = None
        os.fsync(parent_descriptor)
        _verify_directory_path(
            output.parent,
            parent_descriptor,
            parent_inode,
            "beat-cell Stage-2 JSON output parent",
        )
        _verify_owned_json_entry(parent_descriptor, output.name, temporary_inode)
    except BaseException:
        owned_inode = linked[1] if linked is not None else (temporary[1] if temporary is not None else None)
        if owned_inode is not None:
            _unlink_owned_entry(parent_descriptor, output.name, owned_inode)
            _unlink_all_owned_json_entries(parent_descriptor, owned_inode)
        raise
    finally:
        if temporary is not None:
            _unlink_owned_entry(parent_descriptor, temporary[0], temporary[1])
        os.close(parent_descriptor)


def _rename_directory_noreplace(
    parent_descriptor: int,
    source_name: str,
    destination_name: str,
    expected_source_inode: tuple[int, int],
) -> None:
    """Rename one owned directory within a retained parent without replacement."""

    _verify_owned_directory_entry(
        parent_descriptor,
        source_name,
        expected_source_inode,
        "private feature-set root",
    )

    library = ctypes.CDLL(None, use_errno=True)
    source = os.fsencode(source_name)
    destination = os.fsencode(destination_name)
    if hasattr(library, "renameatx_np"):
        rename = library.renameatx_np
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(
            parent_descriptor,
            source,
            parent_descriptor,
            destination,
            0x00000004,  # Darwin RENAME_EXCL.
        )
    elif hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(
            parent_descriptor,
            source,
            parent_descriptor,
            destination,
            0x00000001,  # Linux RENAME_NOREPLACE.
        )
    else:
        raise BeatCellExamplesError("This platform lacks a supported no-replace directory rename primitive.")
    if result == 0:
        _verify_owned_directory_entry(
            parent_descriptor,
            destination_name,
            expected_source_inode,
            "published complete feature-set root",
        )
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise BeatCellExamplesError("Feature-set directory was concurrently created; refusing overwrite.")
    raise BeatCellExamplesError(
        f"Could not atomically publish the complete feature-set directory: {os.strerror(error_number)}."
    )


def _verify_owned_directory_entry(
    parent_descriptor: int,
    name: str,
    expected_inode: tuple[int, int],
    label: str,
) -> None:
    current = _entry_stat(parent_descriptor, name)
    if current is None or not stat.S_ISDIR(current.st_mode) or _publication_identity(current) != expected_inode:
        raise BeatCellExamplesError(f"The {label} name changed during publication.")


def _create_owned_directory(
    parent_descriptor: int,
    name: str,
    mode: int,
    label: str,
) -> tuple[int, tuple[int, int]]:
    """Create, open, and bind one directory name to its just-created inode."""

    descriptor: int | None = None
    created_inode: tuple[int, int] | None = None
    try:
        os.mkdir(name, mode=mode, dir_fd=parent_descriptor)
        created = _entry_stat(parent_descriptor, name)
        if created is None or not stat.S_ISDIR(created.st_mode):
            raise BeatCellExamplesError(f"The {label} was not created as a directory.")
        created_inode = _publication_identity(created)
        descriptor = os.open(
            name,
            _directory_open_flags(),
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode) or _publication_identity(opened) != created_inode:
            raise BeatCellExamplesError(f"The {label} changed between creation and descriptor capture.")
        _verify_owned_directory_entry(parent_descriptor, name, created_inode, label)
        return descriptor, created_inode
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        if created_inode is not None:
            _remove_owned_directory(parent_descriptor, name, created_inode)
            _remove_all_owned_directories(parent_descriptor, created_inode)
        raise


def _directory_inventory(descriptor: int, label: str) -> set[str]:
    try:
        return set(os.listdir(descriptor))
    except OSError as error:
        raise BeatCellExamplesError(f"Could not inspect the {label} inventory.") from error


def _verify_exact_private_feature_tree(
    private_descriptor: int,
    summary_descriptor: int,
    manifest_name: str,
    manifest_inode: tuple[int, int],
    manifest_rendered: bytes,
    summary_directory_name: str,
    summary_inode: tuple[int, int],
    summary_entries: Mapping[str, tuple[tuple[int, int], bytes]],
) -> None:
    """Require the exact owned tree and bytes, with no additional entries."""

    expected_root_names = {manifest_name, summary_directory_name}
    expected_summary_names = set(summary_entries)
    if (
        _directory_inventory(private_descriptor, "private feature-set root") != expected_root_names
        or _directory_inventory(summary_descriptor, "private feature-summary root") != expected_summary_names
    ):
        raise BeatCellExamplesError("The private feature-set inventory changed during publication.")
    _verify_owned_directory_entry(
        private_descriptor,
        summary_directory_name,
        summary_inode,
        "private feature-summary root",
    )
    _verify_owned_json_entry(private_descriptor, manifest_name, manifest_inode)
    if _read_owned_json_entry(private_descriptor, manifest_name, manifest_inode) != manifest_rendered:
        raise BeatCellExamplesError("Private feature-set manifest bytes changed during publication.")
    _verify_owned_json_entry(private_descriptor, manifest_name, manifest_inode)
    for name, (owned_inode, expected_bytes) in summary_entries.items():
        _verify_owned_json_entry(summary_descriptor, name, owned_inode)
        if _read_owned_json_entry(summary_descriptor, name, owned_inode) != expected_bytes:
            raise BeatCellExamplesError("Private feature summary bytes changed during publication.")
        _verify_owned_json_entry(summary_descriptor, name, owned_inode)
    if (
        _directory_inventory(summary_descriptor, "private feature-summary root") != expected_summary_names
        or _directory_inventory(private_descriptor, "private feature-set root") != expected_root_names
    ):
        raise BeatCellExamplesError("The private feature-set inventory changed during publication.")


def _link_private_json(
    parent_descriptor: int,
    destination_name: str,
    rendered: bytes,
) -> tuple[int, int]:
    """Create one durable JSON entry inside an unpublished private tree."""

    temporary_name, temporary_inode = _create_temporary_json(
        parent_descriptor,
        destination_name,
        rendered,
    )
    try:
        os.link(
            temporary_name,
            destination_name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        _verify_owned_json_entry(parent_descriptor, destination_name, temporary_inode)
        if _read_owned_json_entry(parent_descriptor, destination_name, temporary_inode) != rendered:
            raise BeatCellExamplesError("A privately staged feature-set JSON did not round-trip.")
        _verify_owned_json_entry(parent_descriptor, destination_name, temporary_inode)
        return temporary_inode
    except FileExistsError as error:
        raise BeatCellExamplesError("A private feature-set staging entry was unexpectedly occupied.") from error
    except BaseException:
        _unlink_all_owned_json_entries(parent_descriptor, temporary_inode)
        raise
    finally:
        _unlink_owned_entry(parent_descriptor, temporary_name, temporary_inode)


def _freeze_feature_set_publication(
    artifact: Mapping[str, Any],
    summaries: Sequence[Mapping[str, Any]],
    summary_output_root: Path,
) -> tuple[bytes, Mapping[str, bytes]]:
    """Bind one manifest to immutable, exactly named in-memory summary bytes."""

    sealed_artifact, sealed_summaries = validate_beat_cell_feature_set(artifact, summaries)
    summary_output = _absolute(summary_output_root)
    bindings = {str(row["trackId"]): row for row in sealed_artifact["summaries"]}
    rendered: dict[str, bytes] = {}
    for summary in sealed_summaries:
        track_id = str(summary["trackId"])
        name = _feature_summary_filename(summary)
        raw = _render_json(summary)
        expected_path = str(summary_output / name)
        binding = bindings[track_id]
        if (
            Path(name).name != name
            or Path(name).suffix.lower() != ".json"
            or name in rendered
            or binding["path"] != expected_path
            or binding["pathSha256"] != canonical_sha256(expected_path)
            or binding["fileSha256"] != hashlib.sha256(raw).hexdigest()
            or binding["artifactSha256"] != summary["artifactSha256"]
        ):
            raise BeatCellExamplesError("A feature summary does not have one exact manifest-bound output name.")
        rendered[name] = raw
    if not rendered or len(rendered) != len(bindings):
        raise BeatCellExamplesError("Feature summary publication inventory is incomplete or duplicated.")
    return _render_json(sealed_artifact), MappingProxyType(rendered)


def _publish_rendered_feature_set_with_precommit(
    artifact_path: Path,
    artifact_rendered: bytes,
    rendered_summaries: Mapping[str, bytes],
    summary_output_root: Path,
    precommit: Any,
) -> None:
    """Publish already-bound bytes as one no-replace directory rename.

    The complete tree is built under an unpublished hidden sibling.  Therefore
    a crash before the single rename cannot expose a partial official summary
    root, while a crash after it can expose only the complete tree.
    """

    if not isinstance(artifact_rendered, bytes):
        raise BeatCellExamplesError("Rendered feature-set manifest must be immutable bytes.")
    staged_summaries: tuple[tuple[str, bytes], ...] = tuple(
        sorted(rendered_summaries.items(), key=lambda item: item[0])
    )
    if not staged_summaries or any(
        not isinstance(name, str)
        or Path(name).name != name
        or Path(name).suffix.lower() != ".json"
        or not isinstance(raw, bytes)
        for name, raw in staged_summaries
    ):
        raise BeatCellExamplesError("Rendered feature summaries must be a nonempty flat JSON byte mapping.")

    artifact_output = _absolute(artifact_path)
    summary_output = _absolute(summary_output_root)
    if artifact_output.name != "manifest.json" or summary_output.name != "summaries":
        raise BeatCellExamplesError(
            "Feature-set publication requires feature-set/manifest.json and feature-set/summaries."
        )
    feature_set_root = artifact_output.parent
    if summary_output.parent != feature_set_root:
        raise BeatCellExamplesError("Feature manifest and summaries must share one feature-set directory.")
    _preflight_new_directory(feature_set_root, "complete feature-set output")

    parent_descriptor: int | None = None
    parent_inode: tuple[int, int] | None = None
    private_descriptor: int | None = None
    private_inode: tuple[int, int] | None = None
    summary_descriptor: int | None = None
    summary_inode: tuple[int, int] | None = None
    private_name: str | None = None
    active_root_name: str | None = None
    manifest_inode: tuple[int, int] | None = None
    summary_entries: list[tuple[str, tuple[int, int]]] = []
    succeeded = False
    try:
        parent_descriptor, parent_inode = _open_or_create_directory(
            feature_set_root.parent,
            "feature-set output parent",
        )
        if _entry_stat(parent_descriptor, feature_set_root.name) is not None:
            raise BeatCellExamplesError("Feature-set output appeared before publication.")
        for _attempt in range(128):
            candidate = f".{feature_set_root.name}.{secrets.token_hex(16)}.tmp"
            try:
                private_descriptor, private_inode = _create_owned_directory(
                    parent_descriptor,
                    candidate,
                    0o700,
                    "private feature-set root",
                )
            except FileExistsError:
                continue
            private_name = candidate
            active_root_name = candidate
            break
        if private_name is None:
            raise BeatCellExamplesError("Could not reserve a private feature-set staging directory.")
        summary_descriptor, summary_inode = _create_owned_directory(
            private_descriptor,
            summary_output.name,
            0o755,
            "private feature-summary root",
        )

        manifest_inode = _link_private_json(
            private_descriptor,
            artifact_output.name,
            artifact_rendered,
        )
        for name, source_bytes in staged_summaries:
            summary_entries.append((name, _link_private_json(summary_descriptor, name, source_bytes)))
        summary_inode_by_name = dict(summary_entries)
        summary_entry_bindings = {
            name: (summary_inode_by_name[name], source_bytes) for name, source_bytes in staged_summaries
        }
        os.fsync(summary_descriptor)
        os.fsync(private_descriptor)
        os.fsync(parent_descriptor)

        # Barrier 1 is the final source operation before the sole publication
        # primitive.  It must be safe to replay at the post-publication barrier.
        precommit()
        _verify_directory_path(
            feature_set_root.parent,
            parent_descriptor,
            parent_inode,
            "feature-set output parent",
        )
        _verify_owned_directory_entry(
            parent_descriptor,
            private_name,
            private_inode,
            "private feature-set root",
        )
        _verify_exact_private_feature_tree(
            private_descriptor,
            summary_descriptor,
            artifact_output.name,
            manifest_inode,
            artifact_rendered,
            summary_output.name,
            summary_inode,
            summary_entry_bindings,
        )
        if _entry_stat(parent_descriptor, feature_set_root.name) is not None:
            raise BeatCellExamplesError("Feature-set output appeared before publication.")
        _rename_directory_noreplace(
            parent_descriptor,
            private_name,
            feature_set_root.name,
            private_inode,
        )
        active_root_name = feature_set_root.name
        os.fsync(parent_descriptor)

        _verify_directory_path(
            feature_set_root,
            private_descriptor,
            private_inode,
            "published complete feature-set root",
        )
        _verify_directory_path(
            summary_output,
            summary_descriptor,
            summary_inode,
            "published feature-summary root",
        )
        _verify_exact_private_feature_tree(
            private_descriptor,
            summary_descriptor,
            artifact_output.name,
            manifest_inode,
            artifact_rendered,
            summary_output.name,
            summary_inode,
            summary_entry_bindings,
        )

        # Barrier 2 closes the small rename/verification window.  Failure
        # rolls back only the directory inode created by this invocation.
        precommit()
        _verify_directory_path(
            feature_set_root.parent,
            parent_descriptor,
            parent_inode,
            "feature-set output parent",
        )
        _verify_directory_path(
            feature_set_root,
            private_descriptor,
            private_inode,
            "published complete feature-set root",
        )
        _verify_directory_path(
            summary_output,
            summary_descriptor,
            summary_inode,
            "published feature-summary root",
        )
        _verify_exact_private_feature_tree(
            private_descriptor,
            summary_descriptor,
            artifact_output.name,
            manifest_inode,
            artifact_rendered,
            summary_output.name,
            summary_inode,
            summary_entry_bindings,
        )
        _verify_directory_path(
            summary_output,
            summary_descriptor,
            summary_inode,
            "published feature-summary root",
        )
        _verify_directory_path(
            feature_set_root,
            private_descriptor,
            private_inode,
            "published complete feature-set root",
        )
        _verify_directory_path(
            feature_set_root.parent,
            parent_descriptor,
            parent_inode,
            "feature-set output parent",
        )
        succeeded = True
    finally:
        if not succeeded and private_descriptor is not None:
            owned_file_inodes = [inode for _name, inode in summary_entries]
            if manifest_inode is not None:
                owned_file_inodes.append(manifest_inode)
            for owned_inode in owned_file_inodes:
                _unlink_all_owned_json_entries(private_descriptor, owned_inode)
                if summary_descriptor is not None:
                    _unlink_all_owned_json_entries(summary_descriptor, owned_inode)
            if summary_descriptor is not None:
                os.close(summary_descriptor)
                summary_descriptor = None
            if summary_inode is not None:
                _remove_owned_directory(
                    private_descriptor,
                    summary_output.name,
                    summary_inode,
                )
                _remove_all_owned_directories(private_descriptor, summary_inode)
        if private_descriptor is not None:
            os.close(private_descriptor)
        if (
            not succeeded
            and parent_descriptor is not None
            and active_root_name is not None
            and private_inode is not None
        ):
            _remove_owned_directory(parent_descriptor, active_root_name, private_inode)
            _remove_all_owned_directories(parent_descriptor, private_inode)
            os.fsync(parent_descriptor)
        if summary_descriptor is not None:
            os.close(summary_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)


def _publish_complete_feature_set_with_precommit(
    artifact_path: Path,
    artifact: Mapping[str, Any],
    summaries: Sequence[Mapping[str, Any]],
    summary_output_root: Path,
    precommit: Any,
) -> None:
    """Validate, freeze, and publish the exact in-memory feature-set inventory."""

    artifact_rendered, rendered_summaries = _freeze_feature_set_publication(
        artifact,
        summaries,
        summary_output_root,
    )
    _publish_rendered_feature_set_with_precommit(
        artifact_path,
        artifact_rendered,
        rendered_summaries,
        summary_output_root,
        precommit,
    )


def _require_disjoint_paths(outputs: Sequence[Path], sources: Sequence[Path]) -> None:
    absolute_outputs = [_absolute(path) for path in outputs]
    if len(set(absolute_outputs)) != len(absolute_outputs):
        raise BeatCellExamplesError("Official Stage-2 output paths must be distinct.")
    for index, left in enumerate(absolute_outputs):
        for right in absolute_outputs[index + 1 :]:
            if left.is_relative_to(right) or right.is_relative_to(left):
                raise BeatCellExamplesError("Official Stage-2 outputs must be path-disjoint.")
        for source in sources:
            absolute_source = _absolute(source)
            if left == absolute_source or left.is_relative_to(absolute_source) or absolute_source.is_relative_to(left):
                raise BeatCellExamplesError("Official Stage-2 outputs must be disjoint from all sources.")


def _official_publication_policy() -> Mapping[str, Any]:
    publication = BEAT_CELL_STAGE2_OUTPUT_PATHS.get("publication")
    if (
        not isinstance(publication, Mapping)
        or set(publication) != _OFFICIAL_PUBLICATION_POLICY_FIELDS
        or publication.get("schemaVersion") != BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA
        or publication.get("featureSet") != _OFFICIAL_FEATURE_PUBLICATION_POLICY
        or publication.get("singleJson") != _OFFICIAL_SINGLE_JSON_PUBLICATION_POLICY
    ):
        raise BeatCellExamplesError("Official publication policy is not the exact frozen split policy.")
    return publication


def _preflight_official_feature_outputs() -> tuple[Path, Path]:
    if _official_publication_policy()["featureSet"] != _OFFICIAL_FEATURE_PUBLICATION_POLICY:
        raise BeatCellExamplesError("Official feature publication policy is not the exact frozen v2 policy.")
    output = Path(str(BEAT_CELL_STAGE2_OUTPUT_PATHS["featureSetManifest"]))
    summaries = Path(str(BEAT_CELL_STAGE2_OUTPUT_PATHS["featureSummaryRoot"]))
    feature_set_root = _absolute(output).parent
    if (
        _absolute(output).name != "manifest.json"
        or _absolute(summaries).name != "summaries"
        or _absolute(summaries).parent != feature_set_root
    ):
        raise BeatCellExamplesError(
            "Official outputs must be exact feature-set/manifest.json and feature-set/summaries paths."
        )
    _preflight_new_directory(feature_set_root, "official complete feature-set root")
    source = BEAT_CELL_STAGE2_SOURCE_INPUTS
    _require_disjoint_paths(
        [feature_set_root],
        [
            Path(str(source["stage1Report"]["path"])),
            Path(str(source["stage1SummaryRoot"])),
            Path(str(source["benchmarkRoot"])),
            Path(str(source["runtimeRoot"])),
            Path(str(source["beatReceipt"])),
            Path(str(source["audioLineage"])),
        ],
    )
    return output, summaries


def _preflight_official_examples_output() -> Path:
    if _official_publication_policy()["singleJson"] != _OFFICIAL_SINGLE_JSON_PUBLICATION_POLICY:
        raise BeatCellExamplesError("Official examples publication policy is not the exact frozen v1 policy.")
    output = Path(str(BEAT_CELL_STAGE2_OUTPUT_PATHS["examplesArtifact"]))
    _preflight_new_json(output, "official examples artifact")
    source = BEAT_CELL_STAGE2_SOURCE_INPUTS
    _require_disjoint_paths(
        [output],
        [
            Path(str(source["stage1Report"]["path"])),
            Path(str(source["stage1SummaryRoot"])),
            Path(str(source["benchmarkRoot"])),
            Path(str(BEAT_CELL_STAGE2_OUTPUT_PATHS["featureSetManifest"])),
            Path(str(BEAT_CELL_STAGE2_OUTPUT_PATHS["featureSummaryRoot"])),
        ],
    )
    return output


def _validate_official_runtime_manifest_binding(
    runtime_raw: bytes,
    runtime: Mapping[str, Any],
) -> None:
    runtime_contract = _mapping(
        _stage1.STAGE1_SOURCE_CONTRACT["runtimeManifest"],
        "frozen runtime-manifest contract",
    )
    runtime_analyzer_contract = _mapping(
        runtime.get("analyzerContract"),
        "runtime manifest analyzerContract",
    )
    if (
        hashlib.sha256(runtime_raw).hexdigest() != runtime_contract["fileSha256"]
        or runtime.get("manifestSha256") != runtime_contract["manifestSha256"]
        or runtime.get("trackSetSha256") != runtime_contract["trackSetSha256"]
        or runtime_analyzer_contract.get("contractSha256") != runtime_contract["analyzerContractSha256"]
    ):
        raise BeatCellExamplesError("Runtime manifest disagrees with the frozen Stage-1 source contract.")


def run_official_beat_cell_features() -> dict[str, Any]:
    """Run the one exact official Stage-A publication (no path overrides)."""

    load_beat_cell_stage2_authority()
    _expected_product_reconciliations()
    manifest_path, summary_root = _preflight_official_feature_outputs()
    source = BEAT_CELL_STAGE2_SOURCE_INPUTS
    outputs = BEAT_CELL_STAGE2_OUTPUT_PATHS

    # The Stage-1 report remains opaque in Stage A: only lstat/nofollow bytes
    # and its raw SHA-256 are captured.  It is never passed to json.loads.
    report_path = Path(str(source["stage1Report"]["path"]))
    report_raw, report_inode = _sealed_read(report_path, "opaque Stage-1 report")
    if hashlib.sha256(report_raw).hexdigest() != source["stage1Report"]["fileSha256"]:
        raise BeatCellExamplesError("Opaque Stage-1 report raw-file hash is stale.")

    runtime_path = Path(str(source["runtimeManifest"]))
    receipt_path = Path(str(source["beatReceipt"]))
    runtime_raw, runtime_inode = _sealed_read(runtime_path, "runtime manifest")
    receipt_raw, receipt_inode = _sealed_read(receipt_path, "beat receipt")
    runtime = _strict_json(runtime_raw, "runtime manifest")
    receipt = _strict_json(receipt_raw, "beat receipt")
    _validate_official_runtime_manifest_binding(runtime_raw, runtime)
    if hashlib.sha256(receipt_raw).hexdigest() != _stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["fileSha256"]:
        raise BeatCellExamplesError("Beat-receipt file hash is stale.")

    audio_path = Path(str(source["audioLineage"]))
    audio_raw, audio_inode = _sealed_read(audio_path, "audio lineage")
    audio_lineage = _strict_json(audio_raw, "audio lineage")
    audio_contract = _mapping(_stage1.STAGE1_SOURCE_CONTRACT["audioLineage"], "frozen audio-lineage contract")
    if (
        hashlib.sha256(audio_raw).hexdigest() != audio_contract["fileSha256"]
        or audio_lineage.get("artifactSha256") != audio_contract["artifactSha256"]
    ):
        raise BeatCellExamplesError("Audio lineage disagrees with the frozen Stage-1 source contract.")
    try:
        if validate_development_audio_lineage(audio_lineage, verify_files=False) != audio_lineage:
            raise BeatCellExamplesError("Audio lineage static validation changed its value.")
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Audio lineage failed static validation before path admission.") from error

    runtime_root = Path(str(source["runtimeRoot"]))
    runtime_root_inode = _capture_directory_identity(runtime_root, "runtime root")
    admitted_input_snapshot = _capture_stage_a_admitted_inputs(
        runtime,
        receipt,
        audio_lineage,
        runtime_root,
        runtime_path,
        receipt_path,
        audio_path,
    )
    try:
        strict_receipt = _run_with_exact_directory(
            runtime_root,
            runtime_root_inode,
            "runtime root",
            lambda: validate_runtime_beat_grid_receipt(
                receipt,
                parent_runtime_manifest=runtime,
                parent_runtime_root=runtime_root,
                receipt_path=receipt_path,
                verify_sources=True,
            ),
        )
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Beat receipt failed exact reference-free validation.") from error
    _verify_stage_a_admitted_inputs(admitted_input_snapshot)
    if (
        strict_receipt != receipt
        or receipt.get("referenceFree") is not True
        or receipt.get("receiptSha256") != source["beatReceiptArtifactSha256"]
        or receipt.get("trackSetSha256") != source["beatReceiptTrackSetSha256"]
        or receipt.get("receiptTotalsSha256") != source["beatReceiptTotalsSha256"]
    ):
        raise BeatCellExamplesError("Beat receipt disagrees with the Stage-2 authority.")

    try:
        strict_audio_lineage = validate_development_audio_lineage(
            audio_lineage,
            verify_files=True,
        )
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Audio lineage failed full file/re-extraction validation.") from error
    _verify_stage_a_admitted_inputs(admitted_input_snapshot)
    if strict_audio_lineage != audio_lineage:
        raise BeatCellExamplesError("Audio lineage disagrees with the frozen Stage-1 source contract.")

    sidecars, predictions, prediction_sha256s, label_blind_snapshot = _official_label_blind_sources()
    receipt_tracks = {str(row["trackId"]): row for row in _sequence(receipt.get("tracks"), "beat receipt.tracks")}
    if set(receipt_tracks) != set(sidecars) or any(
        sidecars[track_id]["sourceBeatReceiptTrack"] != receipt_tracks[track_id] for track_id in sidecars
    ):
        raise BeatCellExamplesError("Stage-1 sidecars do not embed the exact validated beat-receipt tracks.")
    try:
        audio_projection = project_development_audio_lineage(audio_lineage, sorted(sidecars))
    except (TypeError, ValueError) as error:
        raise BeatCellExamplesError("Could not project exact audio lineage for Stage A.") from error
    _crosscheck_stage_a_audio_projection(
        sidecars,
        audio_projection,
        str(audio_contract["projectionSha256"]),
    )
    product_reconciliations: list[dict[str, Any]] = []
    summaries = [
        build_beat_cell_feature_summary(
            sidecars[track_id],
            predictions[track_id],
            prediction_file_sha256=prediction_sha256s[track_id],
            product_reconciliations=product_reconciliations,
        )
        for track_id in sorted(sidecars)
    ]
    _validate_product_reconciliation_inventory(product_reconciliations)
    manifest = build_beat_cell_feature_set_manifest(
        summaries,
        summary_output_root=Path(str(outputs["featureSummaryRoot"])),
        source_stage1_report_path=report_path,
        source_stage1_report_file_sha256=hashlib.sha256(report_raw).hexdigest(),
        source_stage1_summary_artifact_set_sha256=source["stage1SummaryArtifactSet"]["sha256"],
        source_stage1_summary_file_set_sha256=source["stage1SummaryFileSet"]["sha256"],
    )
    if (
        manifest["trackCount"] != source["trackCount"]
        or manifest["cellCount"] != source["cellCount"]
        or manifest["cellDurationMilliseconds"] != receipt["receiptTotals"]["coveredDurationMilliseconds"]
    ):
        raise BeatCellExamplesError("Official Stage-A counts/duration changed before publication.")

    def precommit() -> None:
        _verify_snapshot(report_path, report_raw, report_inode, "opaque Stage-1 report")
        _verify_snapshot(runtime_path, runtime_raw, runtime_inode, "runtime manifest")
        _verify_snapshot(receipt_path, receipt_raw, receipt_inode, "beat receipt")
        _verify_snapshot(audio_path, audio_raw, audio_inode, "audio lineage")
        _verify_official_label_blind_sources(label_blind_snapshot)
        try:
            _verify_stage_a_admitted_inputs(admitted_input_snapshot)
            if (
                _run_with_exact_directory(
                    runtime_root,
                    runtime_root_inode,
                    "runtime root",
                    lambda: validate_runtime_beat_grid_receipt(
                        receipt,
                        parent_runtime_manifest=runtime,
                        parent_runtime_root=runtime_root,
                        receipt_path=receipt_path,
                        verify_sources=True,
                    ),
                )
                != receipt
            ):
                raise BeatCellExamplesError("Beat receipt changed before Stage-A publication.")
            _verify_stage_a_admitted_inputs(admitted_input_snapshot)
            if validate_development_audio_lineage(audio_lineage, verify_files=True) != audio_lineage:
                raise BeatCellExamplesError("Audio lineage changed before Stage-A publication.")
            _verify_stage_a_admitted_inputs(admitted_input_snapshot)
        except (TypeError, ValueError) as error:
            raise BeatCellExamplesError("Beat receipt or audio lineage changed before Stage-A publication.") from error
        _verify_snapshot(report_path, report_raw, report_inode, "opaque Stage-1 report")
        _verify_snapshot(runtime_path, runtime_raw, runtime_inode, "runtime manifest")
        _verify_snapshot(receipt_path, receipt_raw, receipt_inode, "beat receipt")
        _verify_snapshot(audio_path, audio_raw, audio_inode, "audio lineage")
        _verify_official_label_blind_sources(label_blind_snapshot)

    _publish_complete_feature_set_with_precommit(
        manifest_path,
        manifest,
        summaries,
        summary_root,
        precommit,
    )
    return deepcopy(manifest)


def _validate_official_feature_manifest_admission(
    manifest: Mapping[str, Any],
    feature_values: Mapping[str, Mapping[str, Any]],
    feature_snapshots: Mapping[str, tuple[bytes, tuple[int, int]]],
) -> None:
    """Bind a valid feature manifest to every frozen official Stage-A fact."""

    source = BEAT_CELL_STAGE2_SOURCE_INPUTS
    feature_root = _absolute(Path(str(BEAT_CELL_STAGE2_OUTPUT_PATHS["featureSummaryRoot"])))
    expected_names = {Path(str(row["path"])).name for row in _sequence(manifest["summaries"], "manifest summaries")}
    if (
        manifest["sourceStage1ReportPathSha256"]
        != canonical_sha256(str(_absolute(Path(str(source["stage1Report"]["path"])))))
        or manifest["sourceStage1ReportFileSha256"] != source["stage1Report"]["fileSha256"]
        or manifest["sourceStage1SummaryArtifactSetSha256"] != source["stage1SummaryArtifactSet"]["sha256"]
        or manifest["sourceStage1SummaryFileSetSha256"] != source["stage1SummaryFileSet"]["sha256"]
        or manifest["trackCount"] != source["trackCount"]
        or manifest["cellCount"] != source["cellCount"]
        or manifest["cellDurationMilliseconds"]
        != _stage1.OFFICIAL_BEAT_RECEIPT_CONTRACT["receiptTotals"]["coveredDurationMilliseconds"]
    ):
        raise BeatCellExamplesError("Committed feature-set manifest is not bound to official Stage-A authority.")
    if set(feature_values) != expected_names or set(feature_snapshots) != expected_names:
        raise BeatCellExamplesError("Committed feature-summary file inventory is not exact.")
    for row in manifest["summaries"]:
        name = Path(str(row["path"])).name
        summary = feature_values[name]
        if Path(str(row["path"])) != feature_root / _feature_summary_filename(summary):
            raise BeatCellExamplesError("Committed feature-summary path is not authority-deterministic.")
        if _render_json(summary) != feature_snapshots[name][0]:
            raise BeatCellExamplesError("Committed feature summary is not canonical JSON.")


def run_official_beat_cell_examples() -> dict[str, Any]:
    """Run the one exact official Stage-B join (no path overrides)."""

    load_beat_cell_stage2_authority()
    _expected_product_reconciliations()
    examples_output = _preflight_official_examples_output()
    source = BEAT_CELL_STAGE2_SOURCE_INPUTS
    outputs = BEAT_CELL_STAGE2_OUTPUT_PATHS

    # First deep-open and validate the already committed feature set.
    feature_manifest_path = Path(str(outputs["featureSetManifest"]))
    feature_manifest_raw, feature_manifest_inode = _sealed_read(feature_manifest_path, "committed feature-set manifest")
    feature_manifest = validate_beat_cell_feature_set_manifest(
        _strict_json(feature_manifest_raw, "committed feature-set manifest")
    )
    if _render_json(feature_manifest) != feature_manifest_raw:
        raise BeatCellExamplesError("Committed feature-set manifest is not canonical JSON.")
    feature_root = Path(str(outputs["featureSummaryRoot"]))
    feature_values, feature_snapshots, feature_root_inode = _read_flat_json_directory(
        feature_root, "committed feature-summary root"
    )
    feature_summaries = [validate_beat_cell_feature_summary(feature_values[name]) for name in sorted(feature_values)]
    manifest, feature_summaries = validate_beat_cell_feature_set(feature_manifest, feature_summaries)
    _validate_official_feature_manifest_admission(
        manifest,
        feature_values,
        feature_snapshots,
    )

    # Reopen every label-blind source and recompute all features before the
    # Stage-1 report is parsed for the first time in this process.
    sidecars, predictions, prediction_sha256s, label_blind_snapshot = _official_label_blind_sources()
    manifest, feature_summaries = validate_beat_cell_feature_set_semantics(
        manifest,
        feature_summaries,
        stage1_sidecars=sidecars,
        predictions=predictions,
        prediction_file_sha256s=prediction_sha256s,
    )

    report_path = Path(str(source["stage1Report"]["path"]))
    report_raw, report_inode = _sealed_read(report_path, "Stage-1 report")
    if hashlib.sha256(report_raw).hexdigest() != source["stage1Report"]["fileSha256"]:
        raise BeatCellExamplesError("Stage-1 report raw-file hash is stale.")
    stage1 = _strict_json(report_raw, "Stage-1 report")
    if canonical_sha256(stage1) != source["stage1Report"]["canonicalSha256"]:
        raise BeatCellExamplesError("Stage-1 report canonical hash is stale.")
    examples = build_beat_cell_examples(
        stage1,
        manifest,
        feature_summaries,
        stage1_sidecars=sidecars,
        predictions=predictions,
        prediction_file_sha256s=prediction_sha256s,
        source_stage1_file_sha256=hashlib.sha256(report_raw).hexdigest(),
        source_stage1_canonical_sha256=canonical_sha256(stage1),
        source_feature_set_file_sha256=hashlib.sha256(feature_manifest_raw).hexdigest(),
    )
    expected_stage1 = source["stage1Report"]
    if (
        examples["sourceStage1ArtifactSha256"] != expected_stage1["artifactSha256"]
        or examples["sourceStage1DecisionSha256"] != expected_stage1["decisionSha256"]
        or examples["sourceStage1GateSetSha256"] != expected_stage1["gateSetSha256"]
        or examples["sourceStage1TrackSetSha256"] != expected_stage1["trackSetSha256"]
        or examples["sourceStage1SourceContractSha256"] != expected_stage1["sourceContractSha256"]
        or examples["exampleCount"] != BEAT_CELL_STAGE_B_PROJECTION["expectedExampleCount"]
        or examples["exampleDurationMilliseconds"]
        != BEAT_CELL_STAGE_B_PROJECTION["expectedExampleDurationMilliseconds"]
    ):
        raise BeatCellExamplesError("Official Stage-B source hashes/counts/duration changed.")

    def precommit() -> None:
        _verify_flat_directory(
            feature_root,
            feature_snapshots,
            feature_root_inode,
            "committed feature-summary root",
        )
        _verify_snapshot(
            feature_manifest_path,
            feature_manifest_raw,
            feature_manifest_inode,
            "committed feature-set manifest",
        )
        _verify_official_label_blind_sources(label_blind_snapshot)
        _verify_snapshot(report_path, report_raw, report_inode, "Stage-1 report")
        try:
            if _stage1.validate_beat_cell_stage1_artifact(stage1) != stage1:
                raise BeatCellExamplesError("Stage-1 report changed before Stage-B publication.")
        except (TypeError, ValueError) as error:
            raise BeatCellExamplesError("Stage-1 report changed before Stage-B publication.") from error
        _verify_flat_directory(
            feature_root,
            feature_snapshots,
            feature_root_inode,
            "committed feature-summary root",
        )
        _verify_snapshot(
            feature_manifest_path,
            feature_manifest_raw,
            feature_manifest_inode,
            "committed feature-set manifest",
        )
        _verify_official_label_blind_sources(label_blind_snapshot)
        _verify_snapshot(report_path, report_raw, report_inode, "Stage-1 report")

    _publish_new_json_with_precommit(examples_output, examples, precommit)
    return deepcopy(examples)


__all__ = [
    "BEAT_CELL_EXAMPLE_FIELDS",
    "BEAT_CELL_EXAMPLE_KEY_SCHEMA",
    "BEAT_CELL_EXAMPLE_SCHEMA",
    "BEAT_CELL_EXAMPLES_FIELDS",
    "BEAT_CELL_EXAMPLES_SCHEMA",
    "BEAT_CELL_FEATURE_ROW_FIELDS",
    "BEAT_CELL_FEATURE_ROW_SCHEMA",
    "BEAT_CELL_FEATURE_SET_FIELDS",
    "BEAT_CELL_FEATURE_SET_SCHEMA",
    "BEAT_CELL_FEATURE_SUMMARY_FIELDS",
    "BEAT_CELL_FEATURE_SUMMARY_SCHEMA",
    "BEAT_CELL_GUITARSET_LABEL_AUDIT_FIELDS",
    "BEAT_CELL_LABEL_AUDITS_FIELDS",
    "BEAT_CELL_LABEL_AUDITS_SCHEMA",
    "BEAT_CELL_LABEL_AUDIT_ROW_FIELDS",
    "BeatCellExamplesError",
    "FEATURE_NAMES",
    "build_beat_cell_examples",
    "build_beat_cell_feature_set_manifest",
    "build_beat_cell_feature_summary",
    "run_official_beat_cell_examples",
    "run_official_beat_cell_features",
    "validate_beat_cell_examples_artifact",
    "validate_beat_cell_feature_row",
    "validate_beat_cell_feature_set",
    "validate_beat_cell_feature_set_manifest",
    "validate_beat_cell_feature_set_semantics",
    "validate_beat_cell_feature_summary",
    "validate_stage1_prediction_sidecar",
]
