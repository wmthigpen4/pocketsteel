"""Fail-closed development readiness evaluation for the chord-bar selector.

This module consumes only the already sealed development examples, selector,
and confidence-group artifacts.  It reproduces the selector, verifies every
OOF join, evaluates one predeclared descriptive cutoff, and publishes a
development-only readiness artifact.  It never reads calibration, test,
confirmation, audio, reference, model, browser, or production inputs.
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

from .bar_examples import GROUP_MANIFEST_SCHEMA
from .bar_promotion import canonical_sha256
from .bar_selector import (
    BAR_SELECTOR_ARTIFACT_SCHEMA,
    DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
    LABEL_DETERMINACY_AUDIT_SCHEMA,
    LABEL_DETERMINACY_DATASET_IDS,
    OUTER_FOLD_COUNT,
    PRECISION_COVERAGE_TARGETS,
    PROBABILITY_FLOOR,
    REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA,
    REFERENCE_ENDPOINT_RECONCILIATION_POLICY,
    train_bar_selector,
    validate_bar_selector_artifact,
)
from .bar_uncertainty import BAR_FEATURE_NAMES


DEVELOPMENT_SPLIT = "development"
READINESS_SCHEMA = "chord_bar_selector_development_readiness_v1"
INPUT_BINDINGS_SCHEMA = "chord_bar_selector_readiness_input_bindings_v1"
RUBRIC_SCHEMA = "chord_bar_selector_development_readiness_rubric_v1"
JOINED_ROW_SCHEMA = "chord_bar_selector_readiness_joined_oof_row_v1"

FIXED_TARGET_COVERAGE = 0.50
WILSON_ONE_SIDED_Z_95 = 1.6448536269514722
RELIABILITY_BIN_COUNT = 10
PROBABILITY_QUANTILES = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)
ABSOLUTE_Z_QUANTILES = (0.0, 0.5, 0.9, 0.95, 0.99, 1.0)

REVIEWED_DEVELOPMENT_GROUP_SHAPE: dict[str, Any] = {
    "schemaVersion": "chord_bar_selector_readiness_reviewed_group_shape_v1",
    "trackCount": 246,
    "confidenceGroupCount": 169,
    "datasets": [
        {"datasetId": "aam", "trackCount": 2, "confidenceGroupSizes": [1, 1]},
        {"datasetId": "guitarset", "trackCount": 36, "confidenceGroupSizes": [12, 12, 12]},
        {
            "datasetId": "idmt_guitar",
            "trackCount": 48,
            "confidenceGroupSizes": [8, 8, 8, 8, 8, 8],
        },
        {"datasetId": "nrgcp", "trackCount": 156, "confidenceGroupSizes": [1] * 156},
        {"datasetId": "winterreise", "trackCount": 4, "confidenceGroupSizes": [2, 2]},
    ],
    "crossDatasetConfidenceGroupsAllowed": False,
}
REVIEWED_DEVELOPMENT_GROUP_SHAPE_SHA256 = canonical_sha256(REVIEWED_DEVELOPMENT_GROUP_SHAPE)

READINESS_RUBRIC: dict[str, Any] = {
    "schemaVersion": RUBRIC_SCHEMA,
    "split": DEVELOPMENT_SPLIT,
    "developmentOnly": True,
    "promotionEligible": False,
    "operatingThresholdSelection": None,
    "descriptiveCutoff": {
        "source": "selector.outOfFoldEvaluation.precisionCoverage[targetCoverage=0.50]",
        "targetCoverage": FIXED_TARGET_COVERAGE,
        "field": "minimumProbabilityAtDescriptivePoint",
        "acceptanceRule": "probability >= descriptive cutoff; include the complete tie block",
        "role": "development readiness diagnostic only; not a calibration or production threshold",
    },
    "precisionCoverageTargets": list(PRECISION_COVERAGE_TARGETS),
    "requiredDevelopmentGroupShape": deepcopy(REVIEWED_DEVELOPMENT_GROUP_SHAPE),
    "requiredDevelopmentGroupShapeSha256": REVIEWED_DEVELOPMENT_GROUP_SHAPE_SHA256,
    "countIdentity": {
        "T": "totalBarCount",
        "U": "excludedReferenceIndeterminateBarCount",
        "R": "referenceDeterminateBarCount = T - U",
        "N": "excludedPredictionNoneligibleBarCount",
        "E": "emittedExampleCount = R - N = joined OOF row count",
        "legacyConfidenceMissing": "audit-only subset inside E",
    },
    "minimumReferenceDeterminacyRate": 0.75,
    "aggregateGates": {
        "minimumAcceptedCount": 150,
        "minimumEndToEndMicroCoverage": 0.50,
        "minimumMicroPrecision": 0.98,
        "minimumOneSidedWilson95LowerBound": 0.98,
        "minimumGroupBalancedConditionalCoverage": 0.50,
        "minimumGroupBalancedPrecision": 0.98,
    },
    "guitarsetGates": {
        "minimumAcceptedCount": 30,
        "minimumEndToEndMicroCoverage": 0.25,
        "minimumMicroPrecision": 0.98,
        "minimumGroupBalancedConditionalCoverage": 0.25,
        "minimumGroupBalancedPrecision": 0.98,
        "wilson95LowerBoundRole": "mandatory disclosure only; not a gate",
    },
    "mandatoryDatasetDisclosures": ["aam", "idmt_guitar"],
    "mandatoryDiagnostics": {
        "reliability": "fixed probability deciles, micro and sealed group-weighted, with ECE",
        "oofMetrics": "log loss, Brier score, AURC, and every frozen tie-block precision curve point",
        "probabilityQuantiles": list(PROBABILITY_QUANTILES),
        "sliceMetrics": (
            "accepted support, precision, and conditional coverage by outer fold, dataset, and "
            "GuitarSet comp/solo; exact end-to-end coverage additionally where a sealed R stratum exists"
        ),
        "foldAndGuitarRoleEndToEndPolicy": (
            "unavailable because excluded reference-determinate bars have no sealed fold/role stratum; "
            "report unavailable explicitly and do not invent a denominator"
        ),
        "acceptedGroupConcentration": "unique groups, maximum accepted share, and effective group count",
        "featureDrift": (
            "missingness/allMissing plus final-refit standardized absolute-z quantiles and fractions >3 and >5; "
            "disclosure-only with no numeric drift cutoff"
        ),
        "legacyConfidenceMissing": "support, rate, OOF performance, and same-cutoff performance",
        "referenceEndpointReconciliation": (
            "label-side exact row/count/sum/maximum disclosure; never an estimator feature or readiness gate"
        ),
    },
    "diagnosticCompletenessGates": {
        "outerFolds": list(range(OUTER_FOLD_COUNT)),
        "guitarsetRoles": ["comp", "solo"],
        "numericDriftThreshold": None,
    },
    "decision": (
        "valid inputs and joins plus every aggregate/GuitarSet gate and complete mandatory diagnostics "
        "=> developmentReadinessPassed=true and calibrationMayOpenOnce=true; otherwise calibration remains closed"
    ),
}
READINESS_RUBRIC_SHA256 = canonical_sha256(READINESS_RUBRIC)

_HEX = frozenset("0123456789abcdef")
_GROUP_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "tracks",
        "trackSetSha256",
        "manifestSha256",
    }
)
_GROUP_TRACK_FIELDS = frozenset(
    {
        "trackId",
        "split",
        "datasetId",
        "role",
        "confidenceGroupId",
        "referenceFile",
        "referenceSha256",
        "trackMetadataSha256",
    }
)
_LABEL_COUNT_FIELDS = (
    "totalBarCount",
    "referenceDeterminateBarCount",
    "referenceMixedBarCount",
    "referenceUncoveredBarCount",
    "predictionMixedBarCount",
    "predictionUncoveredBarCount",
    "predictionConfidenceMissingBarCount",
    "predictionStructurallyScorableBarCount",
    "excludedReferenceIndeterminateBarCount",
    "excludedPredictionNoneligibleBarCount",
    "emittedExampleCount",
)
_LABEL_AUDIT_FIELDS = frozenset(
    {
        "schemaVersion",
        "estimand",
        "oofDenominator",
        *_LABEL_COUNT_FIELDS,
        "auditSha256",
    }
)
_DATASET_AUDIT_FIELDS = frozenset(
    {
        "schemaVersion",
        "strataMode",
        "requiredDatasetIds",
        "datasetIds",
        "aggregateLabelDeterminacyAuditSha256",
        "rows",
        "rowSetSha256",
        "auditSha256",
    }
)
_DATASET_AUDIT_ROW_FIELDS = frozenset({"datasetId", *_LABEL_COUNT_FIELDS, "rowSha256"})
_REFERENCE_ENDPOINT_RECONCILIATION_ROW_FIELDS = frozenset(
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
_REFERENCE_ENDPOINT_RECONCILIATION_DATASET_COUNT_FIELDS = frozenset(
    {
        "datasetId",
        "sourceTrackCount",
        "reconciledTrackCount",
    }
)
_REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_FIELDS = frozenset(
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


class SelectorReadinessError(ValueError):
    """A development selector readiness input or invariant failed closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SelectorReadinessError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise SelectorReadinessError(f"{name} must be an array.")
    return value


def _exact_fields(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise SelectorReadinessError(f"{name} has a noncanonical schema: missing={missing}, extra={extra}.")


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or "\x00" in value:
        raise SelectorReadinessError(f"{name} must be a trimmed, nonempty string without NUL bytes.")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise SelectorReadinessError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SelectorReadinessError(f"{name} must be an integer >= {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SelectorReadinessError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise SelectorReadinessError(f"{name} must be a finite number.")
    return result


def _unsigned(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _render_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


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
            raise SelectorReadinessError(f"{name} may not contain symlinked path components.")


def _reject_constant(value: str) -> None:
    raise SelectorReadinessError(f"JSON may not contain non-finite constant {value!r}.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise SelectorReadinessError(f"JSON contains duplicate object key {key!r}.")
        output[key] = value
    return output


def _read_json(path: Path, name: str) -> tuple[dict[str, Any], bytes, os.stat_result]:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise SelectorReadinessError(f"{name} must be an existing non-symlink JSON file.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise SelectorReadinessError(f"{name} must be a regular file.")
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
        raise SelectorReadinessError(f"{name} changed while it was read.") from error
    if (visible.st_dev, visible.st_ino) != (opened.st_dev, opened.st_ino):
        raise SelectorReadinessError(f"{name} changed while it was read.")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SelectorReadinessError(f"Could not decode {name} as exact UTF-8 JSON.") from error
    return dict(_mapping(value, name)), raw, opened


def _sealed_preflight(
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
    groups: Mapping[str, Any],
) -> None:
    """Reject every protected envelope before any nested artifact is inspected."""

    for value, name in ((examples, "examples"), (groups, "group manifest")):
        if (
            value.get("split") != DEVELOPMENT_SPLIT
            or value.get("developmentOnly") is not True
            or value.get("promotionEligible") is not False
        ):
            raise SelectorReadinessError(
                f"{name} must be development-only and promotion-ineligible before nested access."
            )
    if selector.get("developmentOnly") is not True or selector.get("promotionEligible") is not False:
        raise SelectorReadinessError("selector must be development-only and promotion-ineligible before nested access.")
    training = _mapping(selector.get("training"), "selector.training")
    if training.get("split") != DEVELOPMENT_SPLIT:
        raise SelectorReadinessError("selector.training.split must be development before OOF access.")


def _canonical_file(value: Mapping[str, Any], raw: bytes, name: str) -> None:
    if _render_json(value) != raw:
        raise SelectorReadinessError(f"{name} must use the exact canonical indented JSON rendering.")


def _validate_group_manifest(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    _exact_fields(manifest, _GROUP_FIELDS, "group manifest")
    if manifest.get("schemaVersion") != GROUP_MANIFEST_SCHEMA:
        raise SelectorReadinessError("group manifest uses an unsupported schemaVersion.")
    tracks: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for index, raw in enumerate(_sequence(manifest.get("tracks"), "group manifest.tracks")):
        row = dict(_mapping(raw, f"group manifest.tracks[{index}]"))
        _exact_fields(row, _GROUP_TRACK_FIELDS, f"group manifest.tracks[{index}]")
        track_id = _string(row.get("trackId"), f"group manifest.tracks[{index}].trackId")
        if row.get("split") != DEVELOPMENT_SPLIT:
            raise SelectorReadinessError("Every group-manifest track must be development.")
        if track_id in tracks:
            raise SelectorReadinessError("group manifest contains a duplicate trackId.")
        _string(row.get("datasetId"), f"group manifest track {track_id!r} datasetId")
        _string(row.get("role"), f"group manifest track {track_id!r} role")
        _string(row.get("confidenceGroupId"), f"group manifest track {track_id!r} confidenceGroupId")
        _string(row.get("referenceFile"), f"group manifest track {track_id!r} referenceFile")
        _sha256(row.get("referenceSha256"), f"group manifest track {track_id!r} referenceSha256")
        row_sha256 = _sha256(
            row.get("trackMetadataSha256"),
            f"group manifest track {track_id!r} trackMetadataSha256",
        )
        if row_sha256 != canonical_sha256(_unsigned(row, "trackMetadataSha256")):
            raise SelectorReadinessError("group manifest contains a stale trackMetadataSha256.")
        tracks[track_id] = row
        ordered_ids.append(track_id)
    if not tracks or ordered_ids != sorted(ordered_ids):
        raise SelectorReadinessError("group manifest tracks must be nonempty and canonically ordered.")
    track_set = [
        {"trackId": track_id, "trackMetadataSha256": tracks[track_id]["trackMetadataSha256"]}
        for track_id in sorted(tracks)
    ]
    if manifest.get("trackSetSha256") != canonical_sha256(track_set):
        raise SelectorReadinessError("group manifest trackSetSha256 is stale.")
    claimed = _sha256(manifest.get("manifestSha256"), "group manifest.manifestSha256")
    if claimed != canonical_sha256(_unsigned(manifest, "manifestSha256")):
        raise SelectorReadinessError("group manifest manifestSha256 is stale.")
    _validate_reviewed_group_shape(tracks)
    return tracks


def _validate_reviewed_group_shape(tracks: Mapping[str, Mapping[str, Any]]) -> None:
    if len(tracks) != REVIEWED_DEVELOPMENT_GROUP_SHAPE["trackCount"]:
        raise SelectorReadinessError("Group manifest does not contain the reviewed exact 246-track shape.")
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in tracks.values():
        groups[str(row["confidenceGroupId"])].append(row)
    if len(groups) != REVIEWED_DEVELOPMENT_GROUP_SHAPE["confidenceGroupCount"]:
        raise SelectorReadinessError("Group manifest does not contain the reviewed exact 169-group shape.")
    for group, members in groups.items():
        if len({str(row["datasetId"]) for row in members}) != 1:
            raise SelectorReadinessError(
                f"Reviewed explicit-empty derivative shape forbids cross-dataset confidence group {group!r}."
            )
    actual_dataset_ids = {str(row["datasetId"]) for row in tracks.values()}
    if actual_dataset_ids != set(LABEL_DETERMINACY_DATASET_IDS):
        raise SelectorReadinessError("Group manifest changed the exact certification dataset set.")
    for expected in REVIEWED_DEVELOPMENT_GROUP_SHAPE["datasets"]:
        dataset_id = str(expected["datasetId"])
        dataset_rows = [row for row in tracks.values() if row["datasetId"] == dataset_id]
        dataset_groups = [members for members in groups.values() if members[0]["datasetId"] == dataset_id]
        if len(dataset_rows) != expected["trackCount"] or sorted(len(members) for members in dataset_groups) != list(
            expected["confidenceGroupSizes"]
        ):
            raise SelectorReadinessError(
                f"Group manifest changed the reviewed track/group-size shape for {dataset_id}."
            )


def _validate_source_bindings(
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
    groups: Mapping[str, Any],
) -> None:
    examples_sha = _sha256(examples.get("artifactSha256"), "examples.artifactSha256")
    if examples_sha != canonical_sha256(_unsigned(examples, "artifactSha256")):
        raise SelectorReadinessError("examples artifactSha256 is stale.")
    example_set_sha = _sha256(examples.get("exampleSetSha256"), "examples.exampleSetSha256")
    if example_set_sha != canonical_sha256(_sequence(examples.get("examples"), "examples.examples")):
        raise SelectorReadinessError("examples exampleSetSha256 is stale.")
    selector_sha = _sha256(selector.get("artifactSha256"), "selector.artifactSha256")
    if selector_sha != canonical_sha256(_unsigned(selector, "artifactSha256")):
        raise SelectorReadinessError("selector artifactSha256 is stale.")
    training = _mapping(selector.get("training"), "selector.training")
    expected = {
        "sourceExamplesArtifactSha256": examples_sha,
        "sourceExampleSetSha256": example_set_sha,
        "sourceSharedBindingsSha256": examples.get("sharedBindingsSha256"),
        "sourceBenchmarkReportSha256": examples.get("sourceBenchmarkReportSha256"),
        "sourceRuntimeBarGridManifestSha256": examples.get("sourceRuntimeBarGridManifestSha256"),
        "sourceGroupManifestSha256": groups.get("manifestSha256"),
        "sourceAudioLineageSha256": examples.get("sourceAudioLineageSha256"),
        "sourceAudioLineageProjectionSha256": examples.get("sourceAudioLineageProjectionSha256"),
        "sourceBenchmarkAudioLineageBindingSha256": examples.get("sourceBenchmarkAudioLineageBindingSha256"),
        "sourceAudioGroupAuditSha256": examples.get("audioGroupAuditSha256"),
        "sourceReferenceEndpointReconciliationAuditSha256": examples.get("referenceEndpointReconciliationAuditSha256"),
        "sourceLabelDeterminacyAuditSha256": examples.get("labelDeterminacyAuditSha256"),
        "sourceDatasetLabelDeterminacyAuditSha256": examples.get("datasetLabelDeterminacyAuditSha256"),
    }
    for field, expected_value in expected.items():
        _sha256(expected_value, f"examples binding for {field}")
        actual = _sha256(training.get(field), f"selector.training.{field}")
        if actual != expected_value:
            raise SelectorReadinessError(f"selector.training.{field} disagrees with its exact source artifact.")
    if examples.get("sourceGroupManifestSha256") != groups.get("manifestSha256"):
        raise SelectorReadinessError("examples sourceGroupManifestSha256 disagrees with the group manifest.")


def _validate_reproduction(
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
    selector_raw: bytes,
) -> dict[str, Any]:
    # Full standalone validation must precede this module's direct OOF access.
    validate_bar_selector_artifact(selector)
    reproduced = train_bar_selector(deepcopy(dict(examples)))
    if reproduced != selector:
        raise SelectorReadinessError("Fresh selector reproduction differs from the supplied selector object.")
    if canonical_sha256(reproduced) != canonical_sha256(selector):
        raise SelectorReadinessError("Fresh selector reproduction differs canonically from the supplied selector.")
    if _render_json(reproduced) != selector_raw:
        raise SelectorReadinessError("Fresh selector reproduction differs byte-for-byte from the selector JSON.")
    return reproduced


def _label_counts(value: Mapping[str, Any], name: str) -> dict[str, int]:
    return {field: _integer(value.get(field), f"{name}.{field}") for field in _LABEL_COUNT_FIELDS}


def _validate_label_audits(
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    aggregate = _mapping(examples.get("labelDeterminacyAudit"), "examples.labelDeterminacyAudit")
    _exact_fields(aggregate, _LABEL_AUDIT_FIELDS, "examples.labelDeterminacyAudit")
    if aggregate.get("schemaVersion") != LABEL_DETERMINACY_AUDIT_SCHEMA:
        raise SelectorReadinessError("examples label-determinacy audit uses an unsupported schemaVersion.")
    aggregate_sha = _sha256(aggregate.get("auditSha256"), "examples.labelDeterminacyAudit.auditSha256")
    if aggregate_sha != canonical_sha256(_unsigned(aggregate, "auditSha256")):
        raise SelectorReadinessError("examples label-determinacy audit has a stale self hash.")
    if examples.get("labelDeterminacyAuditSha256") != aggregate_sha:
        raise SelectorReadinessError("examples labelDeterminacyAuditSha256 is stale.")
    counts = _label_counts(aggregate, "examples.labelDeterminacyAudit")
    t = counts["totalBarCount"]
    u = counts["excludedReferenceIndeterminateBarCount"]
    r = counts["referenceDeterminateBarCount"]
    n = counts["excludedPredictionNoneligibleBarCount"]
    e = counts["emittedExampleCount"]
    if (
        t <= 0
        or r != t - u
        or e != r - n
        or u != counts["referenceMixedBarCount"] + counts["referenceUncoveredBarCount"]
        or n != counts["predictionMixedBarCount"] + counts["predictionUncoveredBarCount"]
        or counts["predictionStructurallyScorableBarCount"] != e
        or counts["predictionConfidenceMissingBarCount"] > e
    ):
        raise SelectorReadinessError("Aggregate T/U/R/N/E label-determinacy counts do not reconcile.")

    audit = _mapping(
        examples.get("datasetLabelDeterminacyAudit"),
        "examples.datasetLabelDeterminacyAudit",
    )
    _exact_fields(audit, _DATASET_AUDIT_FIELDS, "examples.datasetLabelDeterminacyAudit")
    if (
        audit.get("schemaVersion") != DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA
        or audit.get("strataMode") != "certification-datasets-only-v1"
        or list(_sequence(audit.get("requiredDatasetIds"), "requiredDatasetIds")) != list(LABEL_DETERMINACY_DATASET_IDS)
        or list(_sequence(audit.get("datasetIds"), "datasetIds")) != list(LABEL_DETERMINACY_DATASET_IDS)
        or audit.get("aggregateLabelDeterminacyAuditSha256") != aggregate_sha
    ):
        raise SelectorReadinessError("Readiness requires the exact certification-only five-dataset audit.")
    rows = list(_sequence(audit.get("rows"), "examples.datasetLabelDeterminacyAudit.rows"))
    if len(rows) != len(LABEL_DETERMINACY_DATASET_IDS):
        raise SelectorReadinessError("Dataset label-determinacy audit must contain exactly five rows.")
    by_dataset: dict[str, dict[str, int]] = {}
    normalized_rows: list[dict[str, Any]] = []
    sums = {field: 0 for field in _LABEL_COUNT_FIELDS}
    for expected_dataset_id, raw in zip(LABEL_DETERMINACY_DATASET_IDS, rows, strict=True):
        row = dict(_mapping(raw, f"dataset audit {expected_dataset_id}"))
        _exact_fields(row, _DATASET_AUDIT_ROW_FIELDS, f"dataset audit {expected_dataset_id}")
        if row.get("datasetId") != expected_dataset_id:
            raise SelectorReadinessError("Dataset label-determinacy rows changed certification order.")
        row_sha = _sha256(row.get("rowSha256"), f"dataset audit {expected_dataset_id} rowSha256")
        if row_sha != canonical_sha256(_unsigned(row, "rowSha256")):
            raise SelectorReadinessError("Dataset label-determinacy row has a stale self hash.")
        row_counts = _label_counts(row, f"dataset audit {expected_dataset_id}")
        if (
            row_counts["referenceDeterminateBarCount"]
            != row_counts["totalBarCount"] - row_counts["excludedReferenceIndeterminateBarCount"]
            or row_counts["emittedExampleCount"]
            != row_counts["referenceDeterminateBarCount"] - row_counts["excludedPredictionNoneligibleBarCount"]
            or row_counts["excludedReferenceIndeterminateBarCount"]
            != row_counts["referenceMixedBarCount"] + row_counts["referenceUncoveredBarCount"]
            or row_counts["excludedPredictionNoneligibleBarCount"]
            != row_counts["predictionMixedBarCount"] + row_counts["predictionUncoveredBarCount"]
            or row_counts["predictionStructurallyScorableBarCount"] != row_counts["emittedExampleCount"]
            or row_counts["predictionConfidenceMissingBarCount"] > row_counts["emittedExampleCount"]
        ):
            raise SelectorReadinessError(f"Dataset counts do not reconcile for {expected_dataset_id}.")
        for field in _LABEL_COUNT_FIELDS:
            sums[field] += row_counts[field]
        by_dataset[expected_dataset_id] = row_counts
        normalized_rows.append(row)
    if sums != counts:
        raise SelectorReadinessError("Dataset label-determinacy counts do not sum to aggregate T/U/R/N/E.")
    if audit.get("rowSetSha256") != canonical_sha256(normalized_rows):
        raise SelectorReadinessError("Dataset label-determinacy rowSetSha256 is stale.")
    audit_sha = _sha256(audit.get("auditSha256"), "dataset label-determinacy auditSha256")
    if audit_sha != canonical_sha256(_unsigned(audit, "auditSha256")):
        raise SelectorReadinessError("Dataset label-determinacy auditSha256 is stale.")
    if examples.get("datasetLabelDeterminacyAuditSha256") != audit_sha:
        raise SelectorReadinessError("examples datasetLabelDeterminacyAuditSha256 is stale.")

    training = _mapping(selector.get("training"), "selector.training")
    if training.get("datasetLabelDeterminacyAudit") != audit:
        raise SelectorReadinessError("Selector did not retain the exact dataset label-determinacy audit.")
    for field, value in counts.items():
        if training.get(field) != value:
            raise SelectorReadinessError(f"selector.training.{field} disagrees with the sealed aggregate audit.")
    return counts, by_dataset


def _validate_reference_endpoint_reconciliation_audit(
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
    group_tracks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    name = "examples.referenceEndpointReconciliationAudit"
    audit = _mapping(examples.get("referenceEndpointReconciliationAudit"), name)
    _exact_fields(audit, _REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_FIELDS, name)
    if (
        audit.get("schemaVersion") != REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA
        or audit.get("policy") != REFERENCE_ENDPOINT_RECONCILIATION_POLICY
    ):
        raise SelectorReadinessError("Reference endpoint reconciliation policy changed.")
    audit_sha256 = _sha256(audit.get("auditSha256"), f"{name}.auditSha256")
    if canonical_sha256(_unsigned(audit, "auditSha256")) != audit_sha256:
        raise SelectorReadinessError("Reference endpoint reconciliation auditSha256 is stale.")
    if examples.get("referenceEndpointReconciliationAuditSha256") != audit_sha256:
        raise SelectorReadinessError("Examples reference endpoint reconciliation audit binding is stale.")

    source_track_count = _integer(audit.get("sourceTrackCount"), f"{name}.sourceTrackCount")
    reconciled_track_count = _integer(audit.get("reconciledTrackCount"), f"{name}.reconciledTrackCount")
    unreconciled_track_count = _integer(audit.get("unreconciledTrackCount"), f"{name}.unreconciledTrackCount")
    if (
        source_track_count != len(group_tracks)
        or reconciled_track_count + unreconciled_track_count != source_track_count
    ):
        raise SelectorReadinessError("Reference endpoint reconciliation track counts do not reconcile.")

    source_by_dataset = {
        dataset_id: sum(track["datasetId"] == dataset_id for track in group_tracks.values())
        for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    }
    dataset_counts = list(_sequence(audit.get("datasetCounts"), f"{name}.datasetCounts"))
    if len(dataset_counts) != len(LABEL_DETERMINACY_DATASET_IDS):
        raise SelectorReadinessError("Readiness requires exactly five reference reconciliation dataset counts.")
    normalized_dataset_counts: list[dict[str, Any]] = []
    reconciled_by_dataset: dict[str, int] = {}
    for index, (dataset_id, raw_row) in enumerate(zip(LABEL_DETERMINACY_DATASET_IDS, dataset_counts, strict=True)):
        row_name = f"{name}.datasetCounts[{index}]"
        row = _mapping(raw_row, row_name)
        _exact_fields(row, _REFERENCE_ENDPOINT_RECONCILIATION_DATASET_COUNT_FIELDS, row_name)
        reconciled_count = _integer(row.get("reconciledTrackCount"), f"{row_name}.reconciledTrackCount")
        if (
            row.get("datasetId") != dataset_id
            or row.get("sourceTrackCount") != source_by_dataset[dataset_id]
            or reconciled_count > source_by_dataset[dataset_id]
        ):
            raise SelectorReadinessError("Reference endpoint reconciliation dataset counts changed.")
        reconciled_by_dataset[dataset_id] = reconciled_count
        normalized_dataset_counts.append(dict(row))
    if sum(reconciled_by_dataset.values()) != reconciled_track_count or audit.get(
        "datasetCountSetSha256"
    ) != canonical_sha256(normalized_dataset_counts):
        raise SelectorReadinessError("Reference endpoint reconciliation dataset count set is stale.")

    projection = _mapping(
        examples.get("sourceAudioLineageProjection"),
        "examples.sourceAudioLineageProjection",
    )
    projection_rows = {
        str(row["trackId"]): _mapping(row, "source audio-lineage projection row")
        for row in _sequence(projection.get("tracks"), "sourceAudioLineageProjection.tracks")
    }
    rows = list(_sequence(audit.get("rows"), f"{name}.rows"))
    normalized_rows: list[dict[str, Any]] = []
    row_sha256_by_track: dict[str, str] = {}
    observed_track_ids: list[str] = []
    row_dataset_counts = {dataset_id: 0 for dataset_id in LABEL_DETERMINACY_DATASET_IDS}
    reconciled_values: list[float] = []
    for index, raw_row in enumerate(rows):
        row_name = f"{name}.rows[{index}]"
        row = _mapping(raw_row, row_name)
        _exact_fields(row, _REFERENCE_ENDPOINT_RECONCILIATION_ROW_FIELDS, row_name)
        track_id = str(row.get("trackId"))
        group_track = group_tracks.get(track_id)
        projection_row = projection_rows.get(track_id)
        row_sha256 = _sha256(row.get("rowSha256"), f"{row_name}.rowSha256")
        if canonical_sha256(_unsigned(row, "rowSha256")) != row_sha256:
            raise SelectorReadinessError("A reference endpoint reconciliation row hash is stale.")
        original_end = _finite(row.get("originalEnd"), f"{row_name}.originalEnd")
        prediction_duration = _finite(row.get("predictionDuration"), f"{row_name}.predictionDuration")
        reconciled_end = _finite(row.get("reconciledEnd"), f"{row_name}.reconciledEnd")
        reconciled_seconds = _finite(row.get("reconciledSeconds"), f"{row_name}.reconciledSeconds")
        canonical_milliseconds = _integer(
            row.get("canonicalMs"),
            f"{row_name}.canonicalMs",
            minimum=1,
        )
        if (
            group_track is None
            or projection_row is None
            or group_track.get("datasetId") != row.get("datasetId")
            or projection_row.get("datasetId") != row.get("datasetId")
            or group_track.get("referenceSha256") != row.get("referenceSha256")
            or projection_row.get("canonicalDurationMilliseconds") != canonical_milliseconds
            or track_id in row_sha256_by_track
            or original_end <= prediction_duration
            or prediction_duration <= 0
            or reconciled_end != prediction_duration
            or reconciled_seconds != original_end - prediction_duration
            or reconciled_seconds <= 0
            or math.floor(original_end * 1000 + 0.5) != canonical_milliseconds
            or math.floor(prediction_duration * 1000 + 0.5) != canonical_milliseconds
        ):
            raise SelectorReadinessError("A reference endpoint reconciliation row violates its exact source join.")
        dataset_id = str(row["datasetId"])
        row_dataset_counts[dataset_id] += 1
        observed_track_ids.append(track_id)
        row_sha256_by_track[track_id] = row_sha256
        reconciled_values.append(reconciled_seconds)
        normalized_rows.append(dict(row))
    if (
        observed_track_ids != sorted(observed_track_ids)
        or len(rows) != reconciled_track_count
        or row_dataset_counts != reconciled_by_dataset
        or audit.get("rowSetSha256") != canonical_sha256(normalized_rows)
        or audit.get("totalReconciledSeconds") != math.fsum(reconciled_values)
        or audit.get("maximumReconciledSeconds") != max(reconciled_values, default=0.0)
    ):
        raise SelectorReadinessError("Reference endpoint reconciliation rows, counts, sum, or maximum are stale.")

    for raw_example in _sequence(examples.get("examples"), "examples.examples"):
        example = _mapping(raw_example, "examples example")
        track_id = str(example.get("trackId"))
        if example.get("referenceEndpointReconciliationRowSha256") != row_sha256_by_track.get(track_id):
            raise SelectorReadinessError(
                "An example reference endpoint reconciliation row binding disagrees with its track audit."
            )
    training = _mapping(selector.get("training"), "selector.training")
    if (
        training.get("sourceReferenceEndpointReconciliationAuditSha256") != audit_sha256
        or training.get("referenceEndpointReconciliationAudit") != audit
    ):
        raise SelectorReadinessError("Selector did not retain the exact reference endpoint reconciliation audit.")
    forbidden_feature_names = {
        "referenceEndpointReconciliationRowSha256",
        "referenceEndpointReconciliationAuditSha256",
        "reconciledSeconds",
        "originalEnd",
        "reconciledEnd",
    }
    if forbidden_feature_names.intersection(BAR_FEATURE_NAMES) or any(
        any(key.startswith("referenceEndpointReconciliation") for key in row)
        for row in _sequence(training.get("oofAuditRows"), "selector.training.oofAuditRows")
        if isinstance(row, Mapping)
    ):
        raise SelectorReadinessError("Reference endpoint reconciliation leaked into estimator or OOF inputs.")
    disclosure_payload = {
        "schemaVersion": REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA,
        "policy": REFERENCE_ENDPOINT_RECONCILIATION_POLICY,
        "sourceAuditSha256": audit_sha256,
        "sourceTrackCount": source_track_count,
        "reconciledTrackCount": reconciled_track_count,
        "unreconciledTrackCount": unreconciled_track_count,
        "datasetCounts": deepcopy(normalized_dataset_counts),
        "totalReconciledSeconds": float(audit["totalReconciledSeconds"]),
        "maximumReconciledSeconds": float(audit["maximumReconciledSeconds"]),
        "labelSideAuditOnly": True,
        "estimatorFeature": False,
        "oofMetricInput": False,
        "countIdentityInput": False,
        "readinessGate": False,
    }
    return {**disclosure_payload, "disclosureSha256": canonical_sha256(disclosure_payload)}


def _example_key(example: Mapping[str, Any]) -> str:
    summary = _mapping(example.get("barSummary"), "example.barSummary")
    return canonical_sha256(
        {
            "trackId": example.get("trackId"),
            "barIndex": example.get("barIndex"),
            "barSummarySha256": summary.get("barSummarySha256"),
            "sourceSummarySha256": summary.get("sourceSummarySha256"),
            "predictionCoreSha256": summary.get("predictionCoreSha256"),
            "uncertaintySha256": summary.get("uncertaintySha256"),
            "timingSha256": summary.get("timingSha256"),
            "sourceAudioSha256": summary.get("sourceAudioSha256"),
            "cachedFeatureArraySha256": summary.get("cachedFeatureArraySha256"),
            "freshFeatureArraySha256": summary.get("freshFeatureArraySha256"),
            "canonicalDurationMilliseconds": summary.get("canonicalDurationMilliseconds"),
            "audioLineageRowSha256": summary.get("audioLineageRowSha256"),
            "audioLineageProjectionSha256": summary.get("audioLineageProjectionSha256"),
            "modelOrEnsembleSha256": example.get("modelOrEnsembleSha256"),
            "decoderContractSha256": example.get("decoderContractSha256"),
            "memberOrderSha256": example.get("memberOrderSha256"),
        }
    )


def _lineage_dataset_map(examples: Mapping[str, Any]) -> dict[str, str]:
    projection = _mapping(
        examples.get("sourceAudioLineageProjection"),
        "examples.sourceAudioLineageProjection",
    )
    output: dict[str, str] = {}
    for index, raw in enumerate(_sequence(projection.get("tracks"), "audio-lineage projection tracks")):
        row = _mapping(raw, f"audio-lineage projection tracks[{index}]")
        track_id = _string(row.get("trackId"), f"projection tracks[{index}].trackId")
        dataset_id = _string(row.get("datasetId"), f"projection tracks[{index}].datasetId")
        if track_id in output:
            raise SelectorReadinessError("Audio-lineage projection contains a duplicate trackId.")
        output[track_id] = dataset_id
    if not output:
        raise SelectorReadinessError("Audio-lineage projection must be nonempty.")
    return output


def _guitarset_role(role: str) -> str | None:
    parts = role.split(":")
    if len(parts) >= 2 and parts[0] == "guitarset" and parts[1] in {"comp", "solo"}:
        return parts[1]
    return None


def _join_oof_rows(
    examples: Mapping[str, Any],
    selector: Mapping[str, Any],
    group_tracks: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    lineage_dataset = _lineage_dataset_map(examples)
    if set(lineage_dataset) != set(group_tracks):
        raise SelectorReadinessError("Group manifest and audio-lineage projection track sets differ.")
    example_by_key: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(_sequence(examples.get("examples"), "examples.examples")):
        example = _mapping(raw, f"examples.examples[{index}]")
        key = _example_key(example)
        if key in example_by_key:
            raise SelectorReadinessError("Examples contain a duplicate derived exampleKey.")
        example_by_key[key] = example

    training = _mapping(selector.get("training"), "selector.training")
    raw_oof = _sequence(training.get("oofAuditRows"), "selector.training.oofAuditRows")
    if len(raw_oof) != len(example_by_key):
        raise SelectorReadinessError("OOF row count differs from the exact examples join.")
    joined: list[dict[str, Any]] = []
    public_rows: list[dict[str, Any]] = []
    oof_keys: set[str] = set()
    folds_by_group: dict[str, set[int]] = defaultdict(set)
    weight_by_group: dict[str, list[float]] = defaultdict(list)
    for index, raw in enumerate(raw_oof):
        oof = _mapping(raw, f"selector.training.oofAuditRows[{index}]")
        key = _sha256(oof.get("exampleKey"), f"OOF row {index} exampleKey")
        if key in oof_keys or key not in example_by_key:
            raise SelectorReadinessError("Each OOF exampleKey must join exactly once to one source example.")
        oof_keys.add(key)
        example = example_by_key[key]
        track_id = _string(example.get("trackId"), f"example {key} trackId")
        if track_id not in group_tracks or track_id not in lineage_dataset:
            raise SelectorReadinessError("An OOF example track is absent from group or lineage metadata.")
        group_track = group_tracks[track_id]
        dataset_id = lineage_dataset[track_id]
        role = _string(group_track.get("role"), f"group role for {track_id}")
        group = _string(group_track.get("confidenceGroupId"), f"group for {track_id}")
        correct = oof.get("correct")
        missing_confidence = oof.get("legacyProductConfidenceMissing")
        if not isinstance(correct, bool) or not isinstance(missing_confidence, bool):
            raise SelectorReadinessError("OOF correctness and missing-confidence fields must be boolean.")
        example_outcome = _mapping(example.get("outcome"), f"example {key} outcome")
        if (
            dataset_id != group_track.get("datasetId")
            or dataset_id != oof.get("datasetId")
            or group != example.get("confidenceGroupId")
            or group != oof.get("confidenceGroupId")
            or correct is not example_outcome.get("correct")
            or missing_confidence is not example.get("legacyProductConfidenceMissing")
        ):
            raise SelectorReadinessError("OOF/example/lineage/group metadata join is inconsistent.")
        fold = _integer(oof.get("outerFold"), f"OOF row {key} outerFold")
        if fold >= OUTER_FOLD_COUNT:
            raise SelectorReadinessError("OOF outerFold is outside the frozen five-fold range.")
        probability = _finite(oof.get("probability"), f"OOF row {key} probability")
        sample_weight = _finite(oof.get("sampleWeight"), f"OOF row {key} sampleWeight")
        if not 0 <= probability <= 1 or sample_weight <= 0:
            raise SelectorReadinessError("OOF probability/weight is outside its valid range.")
        summary = _mapping(example.get("barSummary"), f"example {key} barSummary")
        feature_values = _mapping(summary.get("featureValues"), f"example {key} featureValues")
        if set(feature_values) != set(BAR_FEATURE_NAMES) or len(feature_values) != len(BAR_FEATURE_NAMES):
            raise SelectorReadinessError("Example featureValues changed the exact selector feature key set.")
        features: list[float | None] = []
        for feature_name in BAR_FEATURE_NAMES:
            raw_feature = feature_values[feature_name]
            features.append(None if raw_feature is None else _finite(raw_feature, f"{key}.{feature_name}"))
        folds_by_group[group].add(fold)
        weight_by_group[group].append(sample_weight)
        internal = {
            "exampleKey": key,
            "exampleSha256": _sha256(example.get("exampleSha256"), f"example {key} exampleSha256"),
            "trackId": track_id,
            "datasetId": dataset_id,
            "role": role,
            "guitarsetRole": _guitarset_role(role) if dataset_id == "guitarset" else None,
            "confidenceGroupId": group,
            "outerFold": fold,
            "probability": probability,
            "correct": correct,
            "legacyProductConfidenceMissing": missing_confidence,
            "sampleWeight": sample_weight,
            "features": features,
            "featureValuesSha256": canonical_sha256(feature_values),
            "barSummarySha256": _sha256(summary.get("barSummarySha256"), f"example {key} barSummarySha256"),
        }
        joined.append(internal)
    if oof_keys != set(example_by_key):
        raise SelectorReadinessError("Examples and OOF rows do not form an exact one-to-one key set.")
    for group, folds in folds_by_group.items():
        if len(folds) != 1:
            raise SelectorReadinessError(f"Confidence group {group!r} crosses outer folds.")
        if not math.isclose(math.fsum(weight_by_group[group]), 1.0, rel_tol=0, abs_tol=1e-12):
            raise SelectorReadinessError(f"Confidence group {group!r} does not have total OOF weight one.")
    joined.sort(key=lambda row: row["exampleKey"])
    for row in joined:
        payload = {
            "schemaVersion": JOINED_ROW_SCHEMA,
            "exampleKey": row["exampleKey"],
            "exampleSha256": row["exampleSha256"],
            "barSummarySha256": row["barSummarySha256"],
            "featureValuesSha256": row["featureValuesSha256"],
            "trackId": row["trackId"],
            "datasetId": row["datasetId"],
            "role": row["role"],
            "guitarsetRole": row["guitarsetRole"],
            "confidenceGroupId": row["confidenceGroupId"],
            "outerFold": row["outerFold"],
            "probability": row["probability"],
            "correct": row["correct"],
            "legacyProductConfidenceMissing": row["legacyProductConfidenceMissing"],
            "sampleWeight": row["sampleWeight"],
        }
        public_rows.append({**payload, "rowSha256": canonical_sha256(payload)})
    diagnostic_reasons: list[str] = []
    present_folds = {int(row["outerFold"]) for row in joined}
    for fold in range(OUTER_FOLD_COUNT):
        if fold not in present_folds:
            diagnostic_reasons.append(f"diagnostics.outer-fold-{fold}-missing")
    guitar_roles = {row["guitarsetRole"] for row in joined if row["datasetId"] == "guitarset"}
    for role in ("comp", "solo"):
        if role not in guitar_roles:
            diagnostic_reasons.append(f"diagnostics.guitarset-{role}-role-missing")
    if any(row["datasetId"] == "guitarset" and row["guitarsetRole"] is None for row in joined):
        diagnostic_reasons.append("diagnostics.guitarset-role-unclassifiable")
    return joined, public_rows, sorted(set(diagnostic_reasons))


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:  # pragma: no cover - project dependency
        raise RuntimeError("Selector readiness requires NumPy.") from error
    return np


def _probability_blocks(
    probabilities: Any,
    labels: Any,
    weights: Any,
    keys: Sequence[str],
) -> list[dict[str, float]]:
    order = sorted(range(len(keys)), key=lambda index: (-float(probabilities[index]), keys[index]))
    blocks: list[dict[str, float]] = []
    for index in order:
        probability = float(probabilities[index])
        if not blocks or probability != blocks[-1]["probability"]:
            blocks.append({"probability": probability, "weight": 0.0, "correctWeight": 0.0})
        blocks[-1]["weight"] += float(weights[index])
        blocks[-1]["correctWeight"] += float(weights[index] * labels[index])
    return blocks


def _aurc(probabilities: Any, labels: Any, weights: Any, keys: Sequence[str]) -> float:
    total_weight = float(weights.sum())
    cumulative_weight = 0.0
    cumulative_error = 0.0
    area = 0.0
    for block in _probability_blocks(probabilities, labels, weights, keys):
        cumulative_weight += block["weight"]
        cumulative_error += block["weight"] - block["correctWeight"]
        risk = cumulative_error / cumulative_weight
        area += block["weight"] / total_weight * risk
    return area


def _precision_coverage(probabilities: Any, labels: Any, weights: Any, keys: Sequence[str]) -> list[dict[str, Any]]:
    blocks = _probability_blocks(probabilities, labels, weights, keys)
    total = float(weights.sum())
    output: list[dict[str, Any]] = []
    for target in PRECISION_COVERAGE_TARGETS:
        cumulative = 0.0
        correct = 0.0
        minimum_probability: float | None = None
        for block in blocks:
            cumulative += block["weight"]
            correct += block["correctWeight"]
            minimum_probability = block["probability"]
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


def _recomputed_evaluation(rows: Sequence[Mapping[str, Any]], counts: Mapping[str, int]) -> dict[str, Any]:
    np = _numpy()
    probabilities = np.asarray([row["probability"] for row in rows], dtype=np.float64)
    labels = np.asarray([1.0 if row["correct"] else 0.0 for row in rows], dtype=np.float64)
    weights = np.asarray([row["sampleWeight"] for row in rows], dtype=np.float64)
    keys = [str(row["exampleKey"]) for row in rows]
    clipped = np.clip(probabilities, PROBABILITY_FLOOR, 1.0 - PROBABILITY_FLOOR)
    losses = -(labels * np.log(clipped) + (1.0 - labels) * np.log(1.0 - clipped))
    log_loss = float((weights * losses).sum() / weights.sum())
    brier = float((weights * (probabilities - labels) ** 2).sum() / weights.sum())
    return {
        "estimand": None,  # populated from the stored artifact after numeric recomputation
        "denominator": None,
        "denominatorExampleCount": counts["emittedExampleCount"],
        "totalBarCount": counts["totalBarCount"],
        "excludedReferenceIndeterminateBarCount": counts["excludedReferenceIndeterminateBarCount"],
        "excludedPredictionNoneligibleBarCount": counts["excludedPredictionNoneligibleBarCount"],
        "predictionConfidenceMissingBarCount": counts["predictionConfidenceMissingBarCount"],
        "groupBalancedLogLoss": log_loss,
        "groupBalancedBrierScore": brier,
        "groupBalancedAreaUnderRiskCoverage": _aurc(probabilities, labels, weights, keys),
        "precisionCoveragePolicy": "fixed descriptive coverage targets; no operating threshold selected",
        "precisionCoverage": _precision_coverage(probabilities, labels, weights, keys),
    }


def _verify_stored_evaluation(
    selector: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    counts: Mapping[str, int],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    stored = dict(_mapping(selector.get("outOfFoldEvaluation"), "selector.outOfFoldEvaluation"))
    recomputed = _recomputed_evaluation(rows, counts)
    recomputed["estimand"] = stored.get("estimand")
    recomputed["denominator"] = stored.get("denominator")
    if canonical_sha256(recomputed) != canonical_sha256(stored):
        raise SelectorReadinessError(
            "Stored grouped log loss, Brier, AURC, or tie-block precision curve failed exact recomputation."
        )
    points = [
        point
        for point in _sequence(stored.get("precisionCoverage"), "precisionCoverage")
        if _finite(_mapping(point, "precisionCoverage point").get("targetCoverage"), "targetCoverage")
        == FIXED_TARGET_COVERAGE
    ]
    if len(points) != 1:
        raise SelectorReadinessError("Selector must contain exactly one fixed targetCoverage=0.50 point.")
    point = dict(_mapping(points[0], "fixed targetCoverage point"))
    tau = _finite(point.get("minimumProbabilityAtDescriptivePoint"), "fixed descriptive cutoff")
    if not 0 <= tau <= 1:
        raise SelectorReadinessError("Fixed descriptive cutoff lies outside [0, 1].")
    return stored, recomputed, point


def _quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise SelectorReadinessError("Cannot compute a required quantile from an empty sample.")
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
                max(PROBABILITY_FLOOR, row["probability"] if row["correct"] else 1.0 - row["probability"]),
            )
        )
        for row in rows
    ) / len(rows)


def _micro_brier(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    return math.fsum((row["probability"] - (1.0 if row["correct"] else 0.0)) ** 2 for row in rows) / len(rows)


def _micro_aurc(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    np = _numpy()
    probabilities = np.asarray([row["probability"] for row in rows], dtype=np.float64)
    labels = np.asarray([1.0 if row["correct"] else 0.0 for row in rows], dtype=np.float64)
    weights = np.ones(len(rows), dtype=np.float64)
    return _aurc(probabilities, labels, weights, [str(row["exampleKey"]) for row in rows])


def _reliability(rows: Sequence[Mapping[str, Any]], *, group_weighted: bool) -> dict[str, Any]:
    bins: list[list[Mapping[str, Any]]] = [[] for _ in range(RELIABILITY_BIN_COUNT)]
    for row in rows:
        index = min(int(float(row["probability"]) * RELIABILITY_BIN_COUNT), RELIABILITY_BIN_COUNT - 1)
        bins[index].append(row)
    output: list[dict[str, Any]] = []
    total_weight = math.fsum(float(row["sampleWeight"] if group_weighted else 1.0) for row in rows)
    ece = 0.0
    for index, members in enumerate(bins):
        weights = [float(row["sampleWeight"] if group_weighted else 1.0) for row in members]
        weight = math.fsum(weights)
        if weight:
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
                "upperExclusive": None if index == RELIABILITY_BIN_COUNT - 1 else (index + 1) / RELIABILITY_BIN_COUNT,
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


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


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
) -> dict[str, Any]:
    accepted = [row for row in rows if row["accepted"]]
    correct = sum(bool(row["correct"]) for row in accepted)
    emitted_weight = math.fsum(float(row["sampleWeight"]) for row in rows)
    accepted_weight = math.fsum(float(row["sampleWeight"]) for row in accepted)
    accepted_correct_weight = math.fsum(float(row["sampleWeight"]) for row in accepted if row["correct"])
    if reference_determinate_count is None:
        end_to_end_reason = (
            "unavailable: excluded reference-determinate bars have no sealed fold/role stratum; "
            "no denominator was inferred"
        )
    else:
        end_to_end_reason = None
    return {
        "sliceId": slice_id,
        "emittedExampleCount": len(rows),
        "acceptedCount": len(accepted),
        "acceptedCorrectCount": correct,
        "empiricalPrecision": _ratio(correct, len(accepted)),
        "conditionalCoverage": _ratio(len(accepted), len(rows)),
        "groupBalancedConditionalCoverage": _ratio(accepted_weight, emitted_weight),
        "groupBalancedPrecision": _ratio(accepted_correct_weight, accepted_weight),
        "endToEndCoverageAvailable": reference_determinate_count is not None,
        "referenceDeterminateBarCount": reference_determinate_count,
        "endToEndCoverage": (
            _ratio(len(accepted), reference_determinate_count) if reference_determinate_count is not None else None
        ),
        "endToEndCoverageUnavailableReason": end_to_end_reason,
        "oneSidedWilson95LowerBound": _wilson_lower(correct, len(accepted)),
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
    rows: Sequence[Mapping[str, Any]],
    selector: Mapping[str, Any],
) -> dict[str, Any]:
    estimator = _mapping(selector.get("estimator"), "selector.estimator")
    imputation = list(_sequence(estimator.get("imputationValues"), "estimator.imputationValues"))
    center = list(_sequence(estimator.get("center"), "estimator.center"))
    scale = list(_sequence(estimator.get("scale"), "estimator.scale"))
    if not (len(imputation) == len(center) == len(scale) == len(BAR_FEATURE_NAMES)):
        raise SelectorReadinessError("Final estimator preprocessing arrays have the wrong feature dimension.")
    imputation_values = [_finite(value, "estimator imputation") for value in imputation]
    center_values = [_finite(value, "estimator center") for value in center]
    scale_values = [_finite(value, "estimator scale") for value in scale]
    if any(value <= 0 for value in scale_values):
        raise SelectorReadinessError("Final estimator scale must be strictly positive.")
    declared_all_missing = list(_sequence(estimator.get("allMissingFeatureNames"), "estimator.allMissingFeatureNames"))
    missingness: list[dict[str, Any]] = []
    standardized: list[dict[str, Any]] = []
    all_absolute_z: list[float] = []
    actual_all_missing: list[str] = []
    for feature_index, feature_name in enumerate(BAR_FEATURE_NAMES):
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
            raise SelectorReadinessError("Standardized feature diagnostics produced a non-finite value.")
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
        raise SelectorReadinessError("Estimator allMissingFeatureNames disagrees with the exact examples matrix.")
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


def _missing_confidence_diagnostic(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    subset = [row for row in rows if row["legacyProductConfidenceMissing"]]
    accepted = [row for row in subset if row["accepted"]]
    return {
        "status": "observed" if subset else "no-observations",
        "count": len(subset),
        "rateWithinEmittedExamples": len(subset) / len(rows),
        "overallCorrectCount": sum(bool(row["correct"]) for row in subset),
        "overallEmpiricalCorrectness": _ratio(sum(bool(row["correct"]) for row in subset), len(subset)),
        "microLogLoss": _micro_log_loss(subset),
        "microBrierScore": _micro_brier(subset),
        "acceptedCount": len(accepted),
        "acceptedCorrectCount": sum(bool(row["correct"]) for row in accepted),
        "acceptedPrecision": _ratio(sum(bool(row["correct"]) for row in accepted), len(accepted)),
        "conditionalCoverage": _ratio(len(accepted), len(subset)),
    }


def _gate(
    gate_id: str,
    observed: float | int | None,
    operator: str,
    required: float | int,
) -> dict[str, Any]:
    if operator != ">=":  # pragma: no cover - frozen internal contract
        raise RuntimeError("Unsupported frozen readiness gate operator.")
    passed = observed is not None and float(observed) >= float(required)
    return {
        "gateId": gate_id,
        "observed": observed,
        "operator": operator,
        "required": required,
        "passed": passed,
    }


def _build_diagnostics(
    rows: Sequence[dict[str, Any]],
    selector: Mapping[str, Any],
    dataset_counts: Mapping[str, Mapping[str, int]],
    reference_endpoint_reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    folds = [
        _slice_metrics(
            f"outer-fold:{fold}",
            [row for row in rows if row["outerFold"] == fold],
            reference_determinate_count=None,
        )
        for fold in range(OUTER_FOLD_COUNT)
    ]
    datasets = [
        _slice_metrics(
            f"dataset:{dataset_id}",
            [row for row in rows if row["datasetId"] == dataset_id],
            reference_determinate_count=dataset_counts[dataset_id]["referenceDeterminateBarCount"],
        )
        for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    ]
    guitar_roles = [
        _slice_metrics(
            f"guitarset-role:{role}",
            [row for row in rows if row["datasetId"] == "guitarset" and row["guitarsetRole"] == role],
            reference_determinate_count=None,
        )
        for role in ("comp", "solo")
    ]
    correct_probabilities = [float(row["probability"]) for row in rows if row["correct"]]
    incorrect_probabilities = [float(row["probability"]) for row in rows if not row["correct"]]
    return {
        "reliability": {
            "micro": _reliability(rows, group_weighted=False),
            "groupBalanced": _reliability(rows, group_weighted=True),
        },
        "oofMetrics": {
            "microLogLoss": _micro_log_loss(rows),
            "microBrierScore": _micro_brier(rows),
            "microAreaUnderRiskCoverage": _micro_aurc(rows),
            "groupBalancedLogLoss": selector["outOfFoldEvaluation"]["groupBalancedLogLoss"],
            "groupBalancedBrierScore": selector["outOfFoldEvaluation"]["groupBalancedBrierScore"],
            "groupBalancedAreaUnderRiskCoverage": selector["outOfFoldEvaluation"]["groupBalancedAreaUnderRiskCoverage"],
            "tieBlockPrecisionCoverage": deepcopy(selector["outOfFoldEvaluation"]["precisionCoverage"]),
        },
        "probabilityQuantiles": {
            "correct": _quantile_report(correct_probabilities, PROBABILITY_QUANTILES),
            "incorrect": _quantile_report(incorrect_probabilities, PROBABILITY_QUANTILES),
        },
        "acceptedSlices": {
            "byOuterFold": folds,
            "byDataset": datasets,
            "guitarsetCompSolo": guitar_roles,
            "aamMandatoryDisclosure": next(row for row in datasets if row["sliceId"] == "dataset:aam"),
            "idmtGuitarMandatoryDisclosure": next(row for row in datasets if row["sliceId"] == "dataset:idmt_guitar"),
        },
        "acceptedGroupConcentration": _group_concentration(rows),
        "features": _feature_diagnostics(rows, selector),
        "missingLegacyConfidence": _missing_confidence_diagnostic(rows),
        "referenceEndpointReconciliation": deepcopy(dict(reference_endpoint_reconciliation)),
    }


def _source_binding(path: Path, raw: bytes, value: Mapping[str, Any], claimed_field: str) -> dict[str, Any]:
    absolute = str(_absolute(path))
    return {
        "path": absolute,
        "pathSha256": canonical_sha256(absolute),
        "fileSha256": hashlib.sha256(raw).hexdigest(),
        "canonicalSha256": canonical_sha256(value),
        "claimedArtifactSha256": _sha256(value.get(claimed_field), f"{path.name}.{claimed_field}"),
    }


def _directory_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _verify_directory_path(
    path: Path,
    descriptor: int,
    expected_inode: tuple[int, int],
) -> None:
    try:
        visible = os.stat(_absolute(path), follow_symlinks=False)
    except OSError as error:
        raise SelectorReadinessError("Readiness output parent path changed during publication.") from error
    if _identity(os.fstat(descriptor)) != expected_inode or _identity(visible) != expected_inode:
        raise SelectorReadinessError("Readiness output parent path changed during publication.")


def _open_or_create_directory(path: Path) -> tuple[int, tuple[int, int]]:
    absolute = _absolute(path)
    descriptor = os.open(absolute.anchor, _directory_open_flags())
    try:
        for component in absolute.parts[1:]:
            if component in {"", ".", ".."}:
                raise SelectorReadinessError("Readiness output parent contains an invalid path component.")
            try:
                os.mkdir(component, mode=0o755, dir_fd=descriptor)
            except FileExistsError:
                pass
            try:
                next_descriptor = os.open(component, _directory_open_flags(), dir_fd=descriptor)
            except OSError as error:
                raise SelectorReadinessError(
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


def _verify_input_unchanged(
    path: Path,
    expected_stat: os.stat_result,
    expected_raw: bytes,
    name: str,
) -> None:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise SelectorReadinessError(f"{name} changed before readiness publication.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(expected_stat):
            raise SelectorReadinessError(f"{name} changed before readiness publication.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if b"".join(chunks) != expected_raw:
            raise SelectorReadinessError(f"{name} changed before readiness publication.")
    finally:
        os.close(descriptor)
    try:
        visible = os.stat(absolute, follow_symlinks=False)
    except OSError as error:
        raise SelectorReadinessError(f"{name} changed before readiness publication.") from error
    if _identity(visible) != _identity(expected_stat):
        raise SelectorReadinessError(f"{name} changed before readiness publication.")


def _publish_new_json(
    path: Path,
    value: Mapping[str, Any],
    *,
    precommit_check: Any = None,
) -> None:
    destination = _absolute(path)
    if destination.suffix.lower() != ".json":
        raise SelectorReadinessError("Readiness output must be a JSON file.")
    file_read_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    parent_descriptor, parent_inode = _open_or_create_directory(destination.parent)
    temporary_name = f".{destination.name}.{secrets.token_hex(16)}.tmp"
    temporary_inode: tuple[int, int] | None = None
    linked_inode: tuple[int, int] | None = None
    rendered = _render_json(value)
    try:
        if os.stat(destination.name, dir_fd=parent_descriptor, follow_symlinks=False):
            raise SelectorReadinessError("Readiness output must be a new path.")
    except FileNotFoundError:
        pass
    try:
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_descriptor,
        )
        temporary_stat = os.fstat(descriptor)
        temporary_inode = (temporary_stat.st_dev, temporary_stat.st_ino)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(
                temporary_name,
                destination.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise SelectorReadinessError("Readiness output was concurrently created; refusing overwrite.") from error
        linked_inode = temporary_inode
        output_descriptor = os.open(destination.name, file_read_flags, dir_fd=parent_descriptor)
        try:
            opened_stat = os.fstat(output_descriptor)
            if (opened_stat.st_dev, opened_stat.st_ino) != linked_inode:
                raise SelectorReadinessError("Published readiness output inode changed.")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(output_descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if b"".join(chunks) != rendered:
                raise SelectorReadinessError("Published readiness output did not round-trip exactly.")
        finally:
            os.close(output_descriptor)
        if precommit_check is not None:
            precommit_check()
        os.fsync(parent_descriptor)
        _verify_directory_path(destination.parent, parent_descriptor, parent_inode)
    except Exception:
        if linked_inode is not None:
            _unlink_owned(parent_descriptor, destination.name, linked_inode)
        raise
    finally:
        if temporary_inode is not None:
            _unlink_owned(parent_descriptor, temporary_name, temporary_inode)
        os.close(parent_descriptor)


def evaluate_development_selector_readiness(
    examples_path: Path,
    selector_path: Path,
    group_manifest_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Validate, reproduce, evaluate, and atomically publish development readiness."""

    inputs = [_absolute(examples_path), _absolute(selector_path), _absolute(group_manifest_path)]
    output = _absolute(output_path)
    if len(set(inputs)) != len(inputs) or output in set(inputs):
        raise SelectorReadinessError("Examples, selector, group manifest, and output paths must be distinct.")
    if output.suffix.lower() != ".json":
        raise SelectorReadinessError("Readiness output must be a JSON file.")
    _reject_symlink_components(output.parent, "readiness output parent")
    if output.exists() or output.is_symlink():
        raise SelectorReadinessError("Readiness output must be a new, non-symlink path.")

    examples, examples_raw, examples_stat = _read_json(examples_path, "examples artifact")
    selector, selector_raw, selector_stat = _read_json(selector_path, "selector artifact")
    groups, groups_raw, groups_stat = _read_json(group_manifest_path, "group manifest")
    _sealed_preflight(examples, selector, groups)
    _canonical_file(examples, examples_raw, "examples artifact")
    _canonical_file(selector, selector_raw, "selector artifact")
    _canonical_file(groups, groups_raw, "group manifest")

    group_tracks = _validate_group_manifest(groups)
    if selector.get("schemaVersion") != BAR_SELECTOR_ARTIFACT_SCHEMA:
        raise SelectorReadinessError("Selector uses an unsupported schemaVersion.")
    _validate_reproduction(examples, selector, selector_raw)
    _validate_source_bindings(examples, selector, groups)
    counts, dataset_counts = _validate_label_audits(examples, selector)
    reference_endpoint_reconciliation = _validate_reference_endpoint_reconciliation_audit(
        examples,
        selector,
        group_tracks,
    )
    rows, public_rows, diagnostic_reasons = _join_oof_rows(examples, selector, group_tracks)
    if len(rows) != counts["emittedExampleCount"]:
        raise SelectorReadinessError("E does not equal the exact joined OOF row count.")
    if sum(row["legacyProductConfidenceMissing"] for row in rows) != counts["predictionConfidenceMissingBarCount"]:
        raise SelectorReadinessError("Missing legacy confidence is not an exact audit-only subset inside E.")
    emitted_by_dataset = {
        dataset_id: sum(row["datasetId"] == dataset_id for row in rows) for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    }
    if any(
        emitted_by_dataset[dataset_id] != dataset_counts[dataset_id]["emittedExampleCount"]
        for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    ):
        raise SelectorReadinessError("Joined OOF dataset counts disagree with the sealed dataset audit.")

    stored_evaluation, recomputed_evaluation, fixed_point = _verify_stored_evaluation(selector, rows, counts)
    tau = float(fixed_point["minimumProbabilityAtDescriptivePoint"])
    for row in rows:
        row["accepted"] = bool(row["probability"] >= tau)
    for public, internal in zip(public_rows, rows, strict=True):
        public_payload = _unsigned(public, "rowSha256")
        public_payload["acceptedAtFixedDevelopmentCutoff"] = internal["accepted"]
        public.clear()
        public.update({**public_payload, "rowSha256": canonical_sha256(public_payload)})

    aggregate = _slice_metrics(
        "aggregate",
        rows,
        reference_determinate_count=counts["referenceDeterminateBarCount"],
    )
    guitar_rows = [row for row in rows if row["datasetId"] == "guitarset"]
    guitar = _slice_metrics(
        "dataset:guitarset",
        guitar_rows,
        reference_determinate_count=dataset_counts["guitarset"]["referenceDeterminateBarCount"],
    )
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
        raise SelectorReadinessError("Same-cutoff accepted rows disagree with the fixed tie-block point.")

    reference_rate = counts["referenceDeterminateBarCount"] / counts["totalBarCount"]
    gates = [
        _gate("reference-determinacy-rate", reference_rate, ">=", 0.75),
        _gate("aggregate.accepted-count", aggregate["acceptedCount"], ">=", 150),
        _gate("aggregate.end-to-end-micro-coverage", aggregate["endToEndCoverage"], ">=", 0.50),
        _gate("aggregate.micro-precision", aggregate["empiricalPrecision"], ">=", 0.98),
        _gate(
            "aggregate.one-sided-wilson95-lower-bound",
            aggregate["oneSidedWilson95LowerBound"],
            ">=",
            0.98,
        ),
        _gate(
            "aggregate.group-balanced-conditional-coverage",
            aggregate["groupBalancedConditionalCoverage"],
            ">=",
            0.50,
        ),
        _gate("aggregate.group-balanced-precision", aggregate["groupBalancedPrecision"], ">=", 0.98),
        _gate("guitarset.accepted-count", guitar["acceptedCount"], ">=", 30),
        _gate("guitarset.end-to-end-micro-coverage", guitar["endToEndCoverage"], ">=", 0.25),
        _gate("guitarset.micro-precision", guitar["empiricalPrecision"], ">=", 0.98),
        _gate(
            "guitarset.group-balanced-conditional-coverage",
            guitar["groupBalancedConditionalCoverage"],
            ">=",
            0.25,
        ),
        _gate("guitarset.group-balanced-precision", guitar["groupBalancedPrecision"], ">=", 0.98),
    ]
    gate_failure_reasons = [f"gate.{gate['gateId']}" for gate in gates if not gate["passed"]]
    if not any(row["correct"] for row in rows):
        diagnostic_reasons.append("diagnostics.correct-probability-quantiles-missing")
    if not any(not row["correct"] for row in rows):
        diagnostic_reasons.append("diagnostics.incorrect-probability-quantiles-missing")

    diagnostics = _build_diagnostics(
        rows,
        selector,
        dataset_counts,
        reference_endpoint_reconciliation,
    )
    diagnostics_sha256 = canonical_sha256(diagnostics)
    failure_reasons = sorted(set(gate_failure_reasons + diagnostic_reasons))
    passed = not failure_reasons

    input_bindings_payload = {
        "schemaVersion": INPUT_BINDINGS_SCHEMA,
        "examples": _source_binding(examples_path, examples_raw, examples, "artifactSha256"),
        "selector": _source_binding(selector_path, selector_raw, selector, "artifactSha256"),
        "groupManifest": _source_binding(group_manifest_path, groups_raw, groups, "manifestSha256"),
        "referenceEndpointReconciliationAudit": {
            "examplesAuditSha256": examples["referenceEndpointReconciliationAuditSha256"],
            "selectorSourceAuditSha256": selector["training"]["sourceReferenceEndpointReconciliationAuditSha256"],
            "exactMatch": True,
        },
    }
    input_bindings = {
        **input_bindings_payload,
        "bindingsSha256": canonical_sha256(input_bindings_payload),
    }
    row_set_sha256 = canonical_sha256(public_rows)
    count_audit = {
        "T": counts["totalBarCount"],
        "U": counts["excludedReferenceIndeterminateBarCount"],
        "R": counts["referenceDeterminateBarCount"],
        "N": counts["excludedPredictionNoneligibleBarCount"],
        "E": counts["emittedExampleCount"],
        "referenceDeterminacyRate": reference_rate,
        "predictionConfidenceMissingInsideE": counts["predictionConfidenceMissingBarCount"],
        "identitiesReconciled": True,
        "auditSha256": canonical_sha256(
            {
                "T": counts["totalBarCount"],
                "U": counts["excludedReferenceIndeterminateBarCount"],
                "R": counts["referenceDeterminateBarCount"],
                "N": counts["excludedPredictionNoneligibleBarCount"],
                "E": counts["emittedExampleCount"],
                "referenceDeterminacyRate": reference_rate,
                "predictionConfidenceMissingInsideE": counts["predictionConfidenceMissingBarCount"],
                "identitiesReconciled": True,
            }
        ),
    }
    decision_payload = {
        "validationPassed": True,
        "allNumericGatesPassed": all(gate["passed"] for gate in gates),
        "mandatoryDiagnosticsComplete": not diagnostic_reasons,
        "failureReasons": failure_reasons,
        "developmentReadinessPassed": passed,
        "calibrationMayOpenOnce": passed,
        "calibrationStatus": "may-open-once" if passed else "closed",
        "promotionEligible": False,
    }
    decision = {**decision_payload, "decisionSha256": canonical_sha256(decision_payload)}
    output_path_text = str(output)
    artifact_payload: dict[str, Any] = {
        "schemaVersion": READINESS_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "operatingThreshold": None,
        "purpose": "development readiness only; not calibration, threshold selection, or promotion",
        "publication": {
            "mode": "atomic-new-path-only-local-v1",
            "outputPath": output_path_text,
            "outputPathSha256": canonical_sha256(output_path_text),
        },
        "inputBindings": input_bindings,
        "rubric": deepcopy(READINESS_RUBRIC),
        "rubricSha256": READINESS_RUBRIC_SHA256,
        "reproduction": {
            "selectorArtifactValidationPassed": True,
            "freshTrainingObjectEqual": True,
            "freshTrainingCanonicalEqual": True,
            "freshTrainingByteEqual": True,
            "reproducedSelectorSha256": selector["artifactSha256"],
            "sourceBindingsValidated": True,
            "groupManifestSelfHashValidated": True,
            "reviewedDevelopmentGroupShapeSha256": REVIEWED_DEVELOPMENT_GROUP_SHAPE_SHA256,
            "reproductionSha256": canonical_sha256(
                {
                    "selectorArtifactValidationPassed": True,
                    "freshTrainingObjectEqual": True,
                    "freshTrainingCanonicalEqual": True,
                    "freshTrainingByteEqual": True,
                    "reproducedSelectorSha256": selector["artifactSha256"],
                    "sourceBindingsValidated": True,
                    "groupManifestSelfHashValidated": True,
                    "reviewedDevelopmentGroupShapeSha256": REVIEWED_DEVELOPMENT_GROUP_SHAPE_SHA256,
                }
            ),
        },
        "countAudit": count_audit,
        "joinedOofRows": public_rows,
        "joinedOofRowSetSha256": row_set_sha256,
        "storedMetricRecomputation": {
            "storedEvaluationSha256": canonical_sha256(stored_evaluation),
            "recomputedEvaluationSha256": canonical_sha256(recomputed_evaluation),
            "exactCanonicalMatch": True,
        },
        "fixedDevelopmentCutoff": {
            "targetCoverage": FIXED_TARGET_COVERAGE,
            "minimumProbabilityAtDescriptivePoint": tau,
            "acceptanceRule": "probability >= minimumProbabilityAtDescriptivePoint; ties included",
            "isOperatingThreshold": False,
            "isPromotionDecision": False,
            "fixedPointSha256": canonical_sha256(fixed_point),
        },
        "aggregate": aggregate,
        "guitarset": {
            **guitar,
            "wilson95LowerBoundIsGate": False,
            "referenceDeterminateDenominatorSource": (
                "selector.training.datasetLabelDeterminacyAudit[guitarset].referenceDeterminateBarCount"
            ),
        },
        "gates": gates,
        "diagnostics": diagnostics,
        "diagnosticsSha256": diagnostics_sha256,
        "decision": decision,
        "developmentReadinessPassed": passed,
        "calibrationMayOpenOnce": passed,
    }
    artifact = {**artifact_payload, "artifactSha256": canonical_sha256(artifact_payload)}

    def verify_inputs_at_publication_commit() -> None:
        _verify_input_unchanged(examples_path, examples_stat, examples_raw, "examples artifact")
        _verify_input_unchanged(selector_path, selector_stat, selector_raw, "selector artifact")
        _verify_input_unchanged(group_manifest_path, groups_stat, groups_raw, "group manifest")

    _publish_new_json(output, artifact, precommit_check=verify_inputs_at_publication_commit)
    return deepcopy(artifact)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate one frozen development-only chord-bar selector readiness rubric."
    )
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--selector", type=Path, required=True)
    parser.add_argument("--group-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = evaluate_development_selector_readiness(
        args.examples,
        args.selector,
        args.group_manifest,
        args.output,
    )
    print(
        json.dumps(
            {
                "artifactSha256": result["artifactSha256"],
                "developmentReadinessPassed": result["developmentReadinessPassed"],
                "calibrationMayOpenOnce": result["calibrationMayOpenOnce"],
                "output": str(_absolute(args.output)),
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
    )
    return 0


__all__ = [
    "READINESS_RUBRIC",
    "READINESS_RUBRIC_SHA256",
    "READINESS_SCHEMA",
    "SelectorReadinessError",
    "evaluate_development_selector_readiness",
    "main",
]
