"""Sealed development examples for the bar-correctness selector.

This join is intentionally split into two phases. Every prediction-only bar
summary is validated, materialized, and hash-sealed before the first chord
reference is opened. Reference data contributes exactly one bit to an emitted
row: whether the structurally scorable predicted product is correct.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

from .audio_lineage import (
    AUDIO_LINEAGE_PROJECTION_SCHEMA,
    AUDIO_LINEAGE_SCHEMA,
    project_development_audio_lineage,
    validate_development_audio_lineage,
)
from .bar_product import (
    DEFAULT_PREDICTION_COVERAGE,
    DEFAULT_PREDICTION_DOMINANCE,
    DEFAULT_REFERENCE_DOMINANCE,
    score_bar_product_confidence,
)
from .bar_promotion import canonical_sha256
from .bar_uncertainty import (
    BAR_FEATURE_CONTRACT_SHA256,
    BAR_FEATURE_NAMES,
    BAR_UNCERTAINTY_SCHEMA,
    EXPLICIT_BAR_GRID_SCHEMA,
    summarize_prediction_bars,
)
from .benchmark import (
    BENCHMARK_REPORT_SCHEMA,
    UNCERTAINTY_DEVELOPMENT_EXPERIMENT_SCHEMA,
)
from .runtime_bar_grid import validate_runtime_bar_grid_manifest
from .student import extract_student_features
from .uncertainty import FACTORIZED_UNCERTAINTY_SCHEMA


GROUP_MANIFEST_SCHEMA = "chord_bar_selector_group_manifest_v1"
EXAMPLES_SCHEMA = "chord_bar_selector_examples_v1"
COMPACT_BAR_SUMMARY_SCHEMA = "chord_bar_selector_bar_summary_v1"
DEVELOPMENT_SPLIT = "development"
BAR_SCORE_SCHEMA = "chord_bar_product_confidence_v1"
BENCHMARK_AUDIO_LINEAGE_SCHEMA = "chord_benchmark_audio_lineage_v1"
AUDIO_GROUP_AUDIT_SCHEMA = "chord_bar_selector_audio_group_audit_v1"
LABEL_DETERMINACY_AUDIT_SCHEMA = "chord_bar_selector_label_determinacy_audit_v1"
DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA = "chord_bar_selector_dataset_label_determinacy_audit_v1"
REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA = "chord_bar_selector_reference_endpoint_reconciliation_audit_v1"
REFERENCE_ENDPOINT_RECONCILIATION_POLICY = (
    "undeclared-duration-unique-terminal-end-same-player-canonical-millisecond-clip-v1"
)
LABEL_DETERMINACY_DATASET_IDS = (
    "aam",
    "guitarset",
    "idmt_guitar",
    "nrgcp",
    "winterreise",
)
AUDIO_LINEAGE_VERIFICATION_MODE = "full-files-and-reextraction-v1"
FEATURE_ARRAY_VERIFICATION = "loaded-cache-contiguous-little-endian-float16-sha256-v1"
PRODUCTION_EXTRACTOR_ENTRYPOINT = f"{extract_student_features.__module__}.{extract_student_features.__qualname__}"
SELECTOR_ESTIMAND = (
    "P(predictionProductCorrect | referenceLabelDeterminate=true and predictionProduct!=null "
    "and predictionCoverage>=0.75 and predictionDominance>=0.75)"
)
OOF_DENOMINATOR = (
    "emitted development examples only; conditional on reference-label determinacy "
    "and predictionProduct non-null with coverage>=0.75 and dominance>=0.75; "
    "legacy product-confidence availability is audit-only"
)
BAR_OUTCOME_ELIGIBILITY_CONTRACT = {
    "schemaVersion": "chord_bar_selector_outcome_eligibility_contract_v1",
    "scoreSchemaVersion": BAR_SCORE_SCHEMA,
    "referenceDominance": DEFAULT_REFERENCE_DOMINANCE,
    "predictionCoverage": DEFAULT_PREDICTION_COVERAGE,
    "predictionDominance": DEFAULT_PREDICTION_DOMINANCE,
    "confidenceThresholds": [0.0],
    "confidenceThresholdRole": "legacy scorer consistency audit only; never label eligibility",
    "predictionStructuralEligibility": (
        "predictionProduct is non-null and predictionCoverage>=0.75 and predictionDominance>=0.75"
    ),
    "legacyProductConfidenceAvailability": "audit-only; never label eligibility or an estimator feature",
    "barEndDurationRule": ("full-precision-prediction-after-exact-player-canonical-millisecond-runtime-join"),
    "referenceEndpointReconciliationPolicy": REFERENCE_ENDPOINT_RECONCILIATION_POLICY,
    "inclusionRule": (
        "reference label determinate and frozen prediction structural eligibility passes; "
        "legacy product-confidence availability is ignored"
    ),
    "correctnessRule": "predictionProduct == referenceProduct",
}
BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256 = canonical_sha256(BAR_OUTCOME_ELIGIBILITY_CONTRACT)

_HEX = frozenset("0123456789abcdef")
_DEVELOPMENT_SPLITS = frozenset({"dev", DEVELOPMENT_SPLIT})
_GROUP_MANIFEST_KEYS = frozenset(
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
_GROUP_TRACK_KEYS = frozenset(
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
_GROUP_DESCRIPTOR_KEYS = frozenset(
    {
        "trackId",
        "split",
        "datasetId",
        "role",
        "confidenceGroupId",
        "referencePath",
    }
)
_COMPACT_BAR_KEYS = (
    "schemaVersion",
    "trackId",
    "sourceSummarySha256",
    "predictionCoreSha256",
    "uncertaintySha256",
    "timingSha256",
    "sourceAudioSha256",
    "cachedFeatureArraySha256",
    "freshFeatureArraySha256",
    "canonicalDurationMilliseconds",
    "audioLineageRowSha256",
    "audioLineageProjectionSha256",
    "barFeatureContractSha256",
    "sharedBindingsSha256",
    "index",
    "start",
    "end",
    "predictionProduct",
    "predictionProductDurationSeconds",
    "predictionCoverage",
    "predictionDominance",
    "predictionTransitionCount",
    "featureValues",
)
_EXAMPLE_KEYS = frozenset(
    {
        "trackId",
        "split",
        "confidenceGroupId",
        "barIndex",
        "barSummary",
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "canonicalDurationMilliseconds",
        "audioLineageRowSha256",
        "audioLineageProjectionSha256",
        "referenceEndpointReconciliationRowSha256",
        "legacyProductConfidenceMissing",
        "outcome",
        "exampleSha256",
    }
)
_SHARED_BINDING_KEYS = frozenset(
    {
        "barSummarySchemaVersion",
        "featureNames",
        "barFeatureContractSha256",
        "uncertaintySchemaVersion",
        "uncertaintyContractSha256",
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "sourceFeatureKind",
        "sourceFeatureSpecSha256",
        "observabilityProfileSchemaVersion",
        "timingSchemaVersion",
        "timingSourceClass",
        "timingSourceId",
        "timingSourceContractSha256",
        "barOutcomeEligibilityContract",
        "barOutcomeEligibilityContractSha256",
    }
)
_OUTPUT_KEYS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "sharedBindings",
        "sharedBindingsSha256",
        "sourceBenchmarkReportSha256",
        "sourceRuntimeBarGridManifestSha256",
        "sourceGroupManifestSha256",
        "sourceAudioLineageSha256",
        "sourceAudioLineageProjection",
        "sourceAudioLineageProjectionSha256",
        "sourceBenchmarkAudioLineageBindingSha256",
        "audioLineageVerificationMode",
        "featureArrayVerification",
        "audioGroupAudit",
        "audioGroupAuditSha256",
        "referenceEndpointReconciliationAudit",
        "referenceEndpointReconciliationAuditSha256",
        "labelDeterminacyAudit",
        "labelDeterminacyAuditSha256",
        "datasetLabelDeterminacyAudit",
        "datasetLabelDeterminacyAuditSha256",
        "examples",
        "exampleSetSha256",
        "artifactSha256",
    }
)
_LABEL_AUDIT_BASE_COUNT_FIELDS = (
    "totalBarCount",
    "referenceDeterminateBarCount",
    "referenceMixedBarCount",
    "referenceUncoveredBarCount",
    "predictionMixedBarCount",
    "predictionUncoveredBarCount",
    "predictionConfidenceMissingBarCount",
    "predictionStructurallyScorableBarCount",
)
_LABEL_AUDIT_COUNT_FIELDS = (
    *_LABEL_AUDIT_BASE_COUNT_FIELDS,
    "excludedReferenceIndeterminateBarCount",
    "excludedPredictionNoneligibleBarCount",
    "emittedExampleCount",
)
_DATASET_LABEL_AUDIT_ROW_KEYS = frozenset(
    {
        "datasetId",
        *_LABEL_AUDIT_COUNT_FIELDS,
        "rowSha256",
    }
)
_DATASET_LABEL_AUDIT_KEYS = frozenset(
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
_REFERENCE_ENDPOINT_RECONCILIATION_ROW_KEYS = frozenset(
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
_REFERENCE_ENDPOINT_RECONCILIATION_DATASET_COUNT_KEYS = frozenset(
    {
        "datasetId",
        "sourceTrackCount",
        "reconciledTrackCount",
    }
)
_REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_KEYS = frozenset(
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
_REPORT_AUDIO_LINEAGE_KEYS = frozenset(
    {
        "schemaVersion",
        "verificationMode",
        "sourceArtifactSha256",
        "projection",
        "projectionSha256",
        "featureArrayVerification",
        "bindingSha256",
    }
)
_PROJECTION_KEYS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "sourceAudioLineageSha256",
        "manifestBindingsSha256",
        "featureContractSha256",
        "trackCount",
        "tracks",
        "trackSetSha256",
        "projectionSha256",
    }
)
_PROJECTION_ROW_KEYS = frozenset(
    {
        "trackId",
        "datasetId",
        "sourceAudioSha256",
        "cachedArraySha256",
        "freshArraySha256",
        "canonicalDurationMilliseconds",
        "rowSha256",
    }
)
_EPSILON = 1e-9


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an array.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise ValueError(f"{name} fields do not match the sealed schema: missing={missing}, extra={extra}.")


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a nonempty string without surrounding whitespace.")
    return value


def _required_dataset_id(value: Any, name: str) -> str:
    return _required_string(value, name)


def _required_sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _strict_integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer of at least {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _split(value: Any, name: str) -> str:
    if value not in _DEVELOPMENT_SPLITS:
        raise ValueError(
            f"{name} must be development; calibration, test, heldout, confirmation, "
            "training, and other splits are forbidden before any artifact path is accessed."
        )
    return DEVELOPMENT_SPLIT


def _file_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path, name: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {name} as JSON.") from error
    return dict(_mapping(parsed, name)), raw


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    rendered = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    absolute_parent = Path(os.path.abspath(path.parent))
    destination = absolute_parent / path.name
    current = Path(absolute_parent.anchor)
    for part in absolute_parent.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"Summary output contains a symlinked path component: {current}.")
    absolute_parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise ValueError(f"Refusing a symlinked summary artifact {destination}.")
    if destination.exists():
        if not destination.is_file():
            raise ValueError(f"Existing summary artifact is not a regular file: {destination}.")
        try:
            existing = destination.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ValueError(f"Could not verify existing summary artifact {destination}.") from error
        if existing != rendered:
            raise ValueError(f"Refusing to overwrite mismatched summary artifact {destination}.")
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=absolute_parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(rendered)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.is_symlink() or not destination.is_file():
                raise ValueError(f"Summary artifact destination changed during materialization: {destination}.")
            try:
                existing = destination.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise ValueError(f"Could not verify raced summary artifact {destination}.") from error
            if existing != rendered:
                raise ValueError(f"Refusing to overwrite raced summary artifact {destination}.")
    finally:
        temporary.unlink(missing_ok=True)


def summary_artifact_filename(track_id: str, summary_sha256: str) -> str:
    """Return the path-safe, identity-bound filename for a full bar summary."""

    identifier = _required_string(track_id, "track_id")
    summary_digest = _required_sha256(summary_sha256, "summary_sha256")
    return f"{canonical_sha256({'trackId': identifier})}-{summary_digest}.json"


def _artifact_path(root: Path, relative: Any, name: str) -> Path:
    raw = _required_string(relative, name)
    candidate = Path(raw)
    if candidate.is_absolute() or "\x00" in raw:
        raise ValueError(f"{name} must be a relative artifact path.")
    try:
        resolved_root = root.resolve(strict=True)
        resolved = (resolved_root / candidate).resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise ValueError(f"{name} must resolve to a file beneath its declared root.") from error
    if not resolved.is_file():
        raise ValueError(f"{name} must resolve to a regular file.")
    return resolved


def _validate_development_envelopes(
    report: Mapping[str, Any],
    runtime_manifest: Mapping[str, Any],
    group_manifest: Mapping[str, Any],
    audio_lineage: Mapping[str, Any],
) -> None:
    """Reject every non-development declaration before path resolution/read."""

    _split(report.get("split"), "benchmark report split")
    _split(runtime_manifest.get("split"), "runtime bar-grid manifest split")
    _split(group_manifest.get("split"), "group manifest split")
    _split(audio_lineage.get("split"), "audio lineage split")
    for source_name, source in (
        ("benchmark report", report),
        ("runtime bar-grid manifest", runtime_manifest),
        ("group manifest", group_manifest),
        ("audio lineage", audio_lineage),
    ):
        tracks = _sequence(source.get("tracks"), f"{source_name}.tracks")
        if not tracks:
            raise ValueError(f"{source_name}.tracks must be nonempty.")
        for index, raw_track in enumerate(tracks):
            track = _mapping(raw_track, f"{source_name}.tracks[{index}]")
            _split(track.get("split"), f"{source_name}.tracks[{index}].split")


def _validate_report(report: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if report.get("schemaVersion") != BENCHMARK_REPORT_SCHEMA:
        raise ValueError("The uncertainty benchmark report uses an unsupported schema.")
    if report.get("engine") != "factorized":
        raise ValueError("Bar-selector examples require a factorized uncertainty benchmark.")
    if report.get("developmentOnlyExperiment") is not True or report.get("promotionEligible") is not False:
        raise ValueError("The uncertainty report must be development-only and promotion-ineligible.")
    if report.get("beatGridSource") != "none" or report.get("oracleTimingUsed") is not False:
        raise ValueError("The uncertainty benchmark itself must not use oracle or reference timing.")
    experiment = _mapping(report.get("uncertaintyExperiment"), "report.uncertaintyExperiment")
    if experiment.get("schemaVersion") != UNCERTAINTY_DEVELOPMENT_EXPERIMENT_SCHEMA:
        raise ValueError("The report uncertainty experiment uses an unsupported schema.")
    if experiment.get("referenceFree") is not True:
        raise ValueError("The report uncertainty experiment must declare referenceFree=true.")
    allowed_splits = _sequence(experiment.get("allowedSplits"), "uncertaintyExperiment.allowedSplits")
    if tuple(allowed_splits) != ("dev", "development"):
        raise ValueError("The uncertainty experiment must allow only dev/development splits.")
    if experiment.get("uncertaintySchemaVersion") != FACTORIZED_UNCERTAINTY_SCHEMA:
        raise ValueError("The report uncertainty experiment uses the wrong telemetry schema.")
    audio_lineage = _mapping(
        experiment.get("audioLineage"),
        "uncertaintyExperiment.audioLineage",
    )
    _exact_keys(audio_lineage, _REPORT_AUDIO_LINEAGE_KEYS, "uncertaintyExperiment.audioLineage")
    if audio_lineage.get("schemaVersion") != BENCHMARK_AUDIO_LINEAGE_SCHEMA:
        raise ValueError("The benchmark audio-lineage binding uses an unsupported schema.")
    if audio_lineage.get("verificationMode") != AUDIO_LINEAGE_VERIFICATION_MODE:
        raise ValueError("The benchmark did not use full file and fresh-extraction audio verification.")
    if audio_lineage.get("featureArrayVerification") != FEATURE_ARRAY_VERIFICATION:
        raise ValueError("The benchmark used the wrong cached feature-array verification mode.")
    source_audio_lineage_sha256 = _required_sha256(
        audio_lineage.get("sourceArtifactSha256"),
        "uncertaintyExperiment.audioLineage.sourceArtifactSha256",
    )
    projection = _mapping(
        audio_lineage.get("projection"),
        "uncertaintyExperiment.audioLineage.projection",
    )
    _exact_keys(projection, _PROJECTION_KEYS, "uncertaintyExperiment.audioLineage.projection")
    projection_sha256 = _required_sha256(
        audio_lineage.get("projectionSha256"),
        "uncertaintyExperiment.audioLineage.projectionSha256",
    )
    if projection.get("projectionSha256") != projection_sha256:
        raise ValueError("The benchmark audio-lineage projection hash fields disagree.")
    audio_lineage_binding_sha256 = _required_sha256(
        audio_lineage.get("bindingSha256"),
        "uncertaintyExperiment.audioLineage.bindingSha256",
    )
    if canonical_sha256({key: value for key, value in audio_lineage.items() if key != "bindingSha256"}) != (
        audio_lineage_binding_sha256
    ):
        raise ValueError("The benchmark audio-lineage binding hash is stale.")
    binding = dict(_mapping(experiment.get("binding"), "uncertaintyExperiment.binding"))
    model_sha256 = _required_sha256(binding.get("modelOrEnsembleSha256"), "report model binding")
    decoder_sha256 = _required_sha256(binding.get("decoderContractSha256"), "report decoder binding")
    member_order_sha256 = _required_sha256(binding.get("memberOrderSha256"), "report member-order binding")
    members = list(_sequence(experiment.get("memberBinding"), "uncertaintyExperiment.memberBinding"))
    if canonical_sha256(members) != member_order_sha256:
        raise ValueError("The report member binding does not match memberOrderSha256.")
    if canonical_sha256(binding) != _required_sha256(
        experiment.get("bindingSha256"), "uncertaintyExperiment.bindingSha256"
    ):
        raise ValueError("The report uncertainty binding hash is stale.")
    if canonical_sha256(members) != _required_sha256(
        experiment.get("memberBindingSha256"), "uncertaintyExperiment.memberBindingSha256"
    ):
        raise ValueError("The report memberBindingSha256 is stale.")

    tracks: dict[str, dict[str, Any]] = {}
    for index, raw_track in enumerate(_sequence(report.get("tracks"), "report.tracks")):
        track = dict(_mapping(raw_track, f"report.tracks[{index}]"))
        track_id = _required_string(track.get("id"), f"report.tracks[{index}].id")
        if track_id in tracks:
            raise ValueError(f"Duplicate uncertainty-report track id {track_id!r}.")
        _required_string(track.get("predictionFile"), f"report track {track_id!r} predictionFile")
        for field in (
            "predictionSha256",
            "predictionCoreSha256",
            "uncertaintySha256",
            "referenceSha256",
            "sourceAudioSha256",
            "cachedFeatureArraySha256",
            "freshFeatureArraySha256",
            "audioLineageRowSha256",
        ):
            _required_sha256(track.get(field), f"report track {track_id!r} {field}")
        _strict_integer(
            track.get("canonicalDurationMilliseconds"),
            f"report track {track_id!r} canonicalDurationMilliseconds",
            minimum=1,
        )
        tracks[track_id] = track
    if experiment.get("trackCount") != len(tracks):
        raise ValueError("The uncertainty experiment trackCount is stale.")
    core_set = canonical_sha256(
        [{"id": track_id, "sha256": tracks[track_id]["predictionCoreSha256"]} for track_id in sorted(tracks)]
    )
    uncertainty_set = canonical_sha256(
        [{"id": track_id, "sha256": tracks[track_id]["uncertaintySha256"]} for track_id in sorted(tracks)]
    )
    if core_set != _required_sha256(experiment.get("predictionCoreSetSha256"), "predictionCoreSetSha256"):
        raise ValueError("The report prediction-core set hash is stale.")
    if uncertainty_set != _required_sha256(experiment.get("uncertaintySetSha256"), "uncertaintySetSha256"):
        raise ValueError("The report uncertainty set hash is stale.")
    return tracks, {
        "binding": binding,
        "members": members,
        "uncertaintySchemaVersion": experiment.get("uncertaintySchemaVersion"),
        "uncertaintyContractSha256": _required_sha256(
            experiment.get("contractSha256"), "uncertaintyExperiment.contractSha256"
        ),
        "modelOrEnsembleSha256": model_sha256,
        "decoderContractSha256": decoder_sha256,
        "memberOrderSha256": member_order_sha256,
        "audioLineage": dict(audio_lineage),
        "sourceAudioLineageSha256": source_audio_lineage_sha256,
        "audioLineageProjection": dict(projection),
        "audioLineageProjectionSha256": projection_sha256,
        "audioLineageBindingSha256": audio_lineage_binding_sha256,
    }


def _validate_group_manifest(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    _exact_keys(manifest, _GROUP_MANIFEST_KEYS, "group manifest")
    if manifest.get("schemaVersion") != GROUP_MANIFEST_SCHEMA:
        raise ValueError("The confidence-group manifest uses an unsupported schema.")
    if manifest.get("developmentOnly") is not True or manifest.get("promotionEligible") is not False:
        raise ValueError("Confidence-group metadata must be development-only and promotion-ineligible.")
    tracks: dict[str, dict[str, Any]] = {}
    for index, raw_track in enumerate(_sequence(manifest.get("tracks"), "group manifest tracks")):
        track = dict(_mapping(raw_track, f"group manifest tracks[{index}]"))
        _exact_keys(track, _GROUP_TRACK_KEYS, f"group manifest tracks[{index}]")
        track_id = _required_string(track.get("trackId"), f"group track {index} trackId")
        if track_id in tracks:
            raise ValueError(f"Duplicate confidence-group track id {track_id!r}.")
        # These fields are audit metadata only. They are required, then discarded
        # before selector features are assembled.
        _required_dataset_id(
            track.get("datasetId"),
            f"group track {track_id!r} datasetId",
        )
        _required_string(track.get("role"), f"group track {track_id!r} role")
        _required_string(track.get("confidenceGroupId"), f"group track {track_id!r} confidenceGroupId")
        _required_string(track.get("referenceFile"), f"group track {track_id!r} referenceFile")
        _required_sha256(track.get("referenceSha256"), f"group track {track_id!r} referenceSha256")
        claimed_track_sha256 = _required_sha256(
            track.get("trackMetadataSha256"), f"group track {track_id!r} trackMetadataSha256"
        )
        if (
            canonical_sha256({key: value for key, value in track.items() if key != "trackMetadataSha256"})
            != claimed_track_sha256
        ):
            raise ValueError(f"Group track {track_id!r} has a stale trackMetadataSha256.")
        tracks[track_id] = track
    track_set = canonical_sha256(
        [
            {"trackId": track_id, "trackMetadataSha256": tracks[track_id]["trackMetadataSha256"]}
            for track_id in sorted(tracks)
        ]
    )
    if track_set != _required_sha256(manifest.get("trackSetSha256"), "group trackSetSha256"):
        raise ValueError("The confidence-group trackSetSha256 is stale.")
    claimed_manifest_sha256 = _required_sha256(manifest.get("manifestSha256"), "group manifestSha256")
    if (
        canonical_sha256({key: value for key, value in manifest.items() if key != "manifestSha256"})
        != claimed_manifest_sha256
    ):
        raise ValueError("The confidence-group manifestSha256 is stale.")
    return tracks


def _validate_audio_lineage_preflight(
    audio_lineage: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Reverify every bound lineage file with the production extractor."""

    validated = validate_development_audio_lineage(
        audio_lineage,
        verify_files=True,
        extractor=extract_student_features,
    )
    if validated.get("schemaVersion") != AUDIO_LINEAGE_SCHEMA:
        raise ValueError("The audio lineage uses an unsupported schema.")
    extractor_contract = _mapping(
        validated.get("extractorContract"),
        "audio lineage extractorContract",
    )
    if extractor_contract.get("entrypoint") != PRODUCTION_EXTRACTOR_ENTRYPOINT:
        raise ValueError(
            "Bar-selector examples require lineage produced by the production extract_student_features entrypoint."
        )
    return validated


def _validate_report_audio_lineage_binding(
    report_contract: Mapping[str, Any],
    audio_lineage: Mapping[str, Any],
    track_ids: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Mapping[str, Any]]]:
    """Require the benchmark projection to be exactly derived from the full lineage."""

    if report_contract.get("sourceAudioLineageSha256") != audio_lineage.get("artifactSha256"):
        raise ValueError("The benchmark report binds a different full audio-lineage artifact.")
    expected_projection = project_development_audio_lineage(audio_lineage, track_ids)
    report_projection = _mapping(
        report_contract.get("audioLineageProjection"),
        "benchmark audio-lineage projection",
    )
    if report_projection.get("schemaVersion") != AUDIO_LINEAGE_PROJECTION_SCHEMA:
        raise ValueError("The benchmark audio-lineage projection uses an unsupported schema.")
    if dict(report_projection) != expected_projection:
        raise ValueError("The benchmark report does not bind the exact requested audio-lineage projection.")
    projection_sha256 = _required_sha256(
        report_contract.get("audioLineageProjectionSha256"),
        "benchmark audio-lineage projectionSha256",
    )
    if projection_sha256 != expected_projection["projectionSha256"]:
        raise ValueError("The benchmark audio-lineage projectionSha256 is stale.")
    rows: dict[str, Mapping[str, Any]] = {}
    for index, raw_row in enumerate(_sequence(expected_projection.get("tracks"), "audio-lineage projection tracks")):
        row = _mapping(raw_row, f"audio-lineage projection tracks[{index}]")
        _exact_keys(row, _PROJECTION_ROW_KEYS, f"audio-lineage projection tracks[{index}]")
        identifier = _required_string(row.get("trackId"), f"audio-lineage projection tracks[{index}].trackId")
        rows[identifier] = row
    return expected_projection, rows


def _validate_cross_audio_bindings(
    track_ids: Sequence[str],
    report_tracks: Mapping[str, Mapping[str, Any]],
    runtime_tracks: Mapping[str, Mapping[str, Any]],
    group_tracks: Mapping[str, Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
) -> None:
    """Reject metadata-level audio/cache/duration splices before leaf artifacts."""

    for track_id in track_ids:
        report = report_tracks[track_id]
        runtime = runtime_tracks[track_id]
        group = group_tracks[track_id]
        projection = projection_tracks[track_id]
        dataset_id = _required_dataset_id(
            projection.get("datasetId"),
            f"audio-lineage track {track_id!r} datasetId",
        )
        expected_report = {
            "sourceAudioSha256": projection["sourceAudioSha256"],
            "cachedFeatureArraySha256": projection["cachedArraySha256"],
            "freshFeatureArraySha256": projection["freshArraySha256"],
            "canonicalDurationMilliseconds": projection["canonicalDurationMilliseconds"],
            "audioLineageRowSha256": projection["rowSha256"],
        }
        if any(report.get(field) != expected for field, expected in expected_report.items()):
            raise ValueError(f"Benchmark row and audio lineage disagree for track {track_id!r}.")
        if report.get("datasetId") != dataset_id or group.get("datasetId") != dataset_id:
            raise ValueError(
                f"Benchmark, confidence-group, and audio-lineage datasets disagree for track {track_id!r}."
            )
        audio_binding = _mapping(runtime.get("audioBinding"), f"runtime track {track_id!r} audioBinding")
        expected_audio_sha256 = projection["sourceAudioSha256"]
        expected_milliseconds = projection["canonicalDurationMilliseconds"]
        if (
            runtime.get("audioSha256") != expected_audio_sha256
            or audio_binding.get("sourceAudioSha256") != expected_audio_sha256
        ):
            raise ValueError(f"Runtime audio and audio lineage disagree for track {track_id!r}.")
        if audio_binding.get("canonicalDurationMilliseconds") != expected_milliseconds:
            raise ValueError(f"Runtime canonical milliseconds and audio lineage disagree for track {track_id!r}.")


def _audio_group_audit(
    track_ids: Sequence[str],
    group_tracks: Mapping[str, Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Seal the invariant that identical audio bytes cannot cross CV groups."""

    by_audio: dict[str, dict[str, Any]] = {}
    for track_id in track_ids:
        audio_sha256 = _required_sha256(
            projection_tracks[track_id].get("sourceAudioSha256"),
            f"audio-lineage track {track_id!r} sourceAudioSha256",
        )
        group_id = _required_string(
            group_tracks[track_id].get("confidenceGroupId"),
            f"group track {track_id!r} confidenceGroupId",
        )
        existing = by_audio.get(audio_sha256)
        if existing is None:
            by_audio[audio_sha256] = {
                "sourceAudioSha256": audio_sha256,
                "confidenceGroupId": group_id,
                "trackIds": [track_id],
            }
        elif existing["confidenceGroupId"] != group_id:
            raise ValueError(
                f"Identical source audio bytes must use one confidenceGroupId; audio {audio_sha256} crosses groups."
            )
        else:
            existing["trackIds"].append(track_id)
    rows: list[dict[str, Any]] = []
    for audio_sha256 in sorted(by_audio):
        row = by_audio[audio_sha256]
        track_list = sorted(str(item) for item in row["trackIds"])
        rows.append(
            {
                "sourceAudioSha256": audio_sha256,
                "confidenceGroupId": row["confidenceGroupId"],
                "trackIds": track_list,
                "trackCount": len(track_list),
            }
        )
    payload = {
        "schemaVersion": AUDIO_GROUP_AUDIT_SCHEMA,
        "policy": "identical-source-audio-must-share-one-confidence-group-v1",
        "trackCount": len(track_ids),
        "uniqueSourceAudioCount": len(rows),
        "duplicateSourceAudioCount": sum(row["trackCount"] > 1 for row in rows),
        "duplicateTrackCount": len(track_ids) - len(rows),
        "rows": rows,
    }
    return {**payload, "auditSha256": canonical_sha256(payload)}


def _empty_label_counts() -> dict[str, int]:
    return {name: 0 for name in _LABEL_AUDIT_BASE_COUNT_FIELDS}


def _complete_label_counts(
    base_counts: Mapping[str, Any],
    *,
    emitted_example_count: int,
    name: str,
) -> dict[str, int]:
    counts = {
        field: _strict_integer(base_counts.get(field), f"{name}.{field}") for field in _LABEL_AUDIT_BASE_COUNT_FIELDS
    }
    emitted = _strict_integer(emitted_example_count, f"{name}.emittedExampleCount")
    excluded_reference = counts["totalBarCount"] - counts["referenceDeterminateBarCount"]
    excluded_prediction = counts["referenceDeterminateBarCount"] - counts["predictionStructurallyScorableBarCount"]
    if (
        excluded_reference < 0
        or excluded_prediction < 0
        or counts["referenceMixedBarCount"] + counts["referenceUncoveredBarCount"] != excluded_reference
        or counts["predictionMixedBarCount"] + counts["predictionUncoveredBarCount"] != excluded_prediction
        or counts["predictionConfidenceMissingBarCount"] > counts["predictionStructurallyScorableBarCount"]
        or emitted != counts["predictionStructurallyScorableBarCount"]
    ):
        raise ValueError(f"{name} label-determinacy counts are internally inconsistent.")
    return {
        **counts,
        "excludedReferenceIndeterminateBarCount": excluded_reference,
        "excludedPredictionNoneligibleBarCount": excluded_prediction,
        "emittedExampleCount": emitted,
    }


def _dataset_label_determinacy_audit(
    counts_by_dataset: Mapping[str, Mapping[str, Any]],
    emitted_by_dataset: Mapping[str, int],
    *,
    aggregate_counts: Mapping[str, int],
    aggregate_audit_sha256: str,
) -> dict[str, Any]:
    required_ids = list(LABEL_DETERMINACY_DATASET_IDS)
    custom_ids = sorted(set(counts_by_dataset) - set(LABEL_DETERMINACY_DATASET_IDS))
    dataset_ids = [*required_ids, *custom_ids]
    rows: list[dict[str, Any]] = []
    for dataset_id in dataset_ids:
        counts = _complete_label_counts(
            counts_by_dataset[dataset_id],
            emitted_example_count=emitted_by_dataset.get(dataset_id, 0),
            name=f"datasetLabelDeterminacyAudit[{dataset_id!r}]",
        )
        row_payload = {"datasetId": dataset_id, **counts}
        row = {**row_payload, "rowSha256": canonical_sha256(row_payload)}
        _exact_keys(row, _DATASET_LABEL_AUDIT_ROW_KEYS, "dataset label-determinacy row")
        rows.append(row)
    for field in _LABEL_AUDIT_COUNT_FIELDS:
        if sum(int(row[field]) for row in rows) != int(aggregate_counts[field]):
            raise RuntimeError(f"Dataset label-determinacy rows do not sum to aggregate {field}.")
    payload = {
        "schemaVersion": DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
        "strataMode": ("certification-datasets-only-v1" if not custom_ids else "generic-with-custom-datasets-v1"),
        "requiredDatasetIds": required_ids,
        "datasetIds": dataset_ids,
        "aggregateLabelDeterminacyAuditSha256": aggregate_audit_sha256,
        "rows": rows,
        "rowSetSha256": canonical_sha256(rows),
    }
    audit = {**payload, "auditSha256": canonical_sha256(payload)}
    _exact_keys(audit, _DATASET_LABEL_AUDIT_KEYS, "dataset label-determinacy audit")
    return audit


def _reference_endpoint_reconciliation_audit(
    reconciliation_rows: Sequence[Mapping[str, Any]],
    projection_tracks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    rows = sorted((dict(row) for row in reconciliation_rows), key=lambda row: str(row["trackId"]))
    if len({str(row["trackId"]) for row in rows}) != len(rows):
        raise RuntimeError("Reference endpoint reconciliation audit repeats a track id.")
    for row in rows:
        _exact_keys(row, _REFERENCE_ENDPOINT_RECONCILIATION_ROW_KEYS, "reference endpoint reconciliation row")
        if canonical_sha256({key: value for key, value in row.items() if key != "rowSha256"}) != row["rowSha256"]:
            raise RuntimeError("Reference endpoint reconciliation row hash is stale.")

    source_by_dataset: dict[str, int] = {}
    for track in projection_tracks.values():
        dataset_id = _required_dataset_id(track.get("datasetId"), "audio-lineage projection datasetId")
        source_by_dataset[dataset_id] = source_by_dataset.get(dataset_id, 0) + 1
    reconciled_by_dataset: dict[str, int] = {}
    for row in rows:
        dataset_id = _required_dataset_id(row.get("datasetId"), "reference reconciliation datasetId")
        reconciled_by_dataset[dataset_id] = reconciled_by_dataset.get(dataset_id, 0) + 1
    custom_ids = sorted(set(source_by_dataset) - set(LABEL_DETERMINACY_DATASET_IDS))
    dataset_ids = [*LABEL_DETERMINACY_DATASET_IDS, *custom_ids]
    dataset_counts = [
        {
            "datasetId": dataset_id,
            "sourceTrackCount": source_by_dataset.get(dataset_id, 0),
            "reconciledTrackCount": reconciled_by_dataset.get(dataset_id, 0),
        }
        for dataset_id in dataset_ids
    ]
    for row in dataset_counts:
        _exact_keys(
            row,
            _REFERENCE_ENDPOINT_RECONCILIATION_DATASET_COUNT_KEYS,
            "reference endpoint reconciliation dataset count",
        )
        if row["reconciledTrackCount"] > row["sourceTrackCount"]:
            raise RuntimeError("Reference endpoint reconciliation dataset count exceeds its source tracks.")
    source_track_count = len(projection_tracks)
    reconciled_track_count = len(rows)
    if (
        sum(int(row["sourceTrackCount"]) for row in dataset_counts) != source_track_count
        or sum(int(row["reconciledTrackCount"]) for row in dataset_counts) != reconciled_track_count
    ):
        raise RuntimeError("Reference endpoint reconciliation dataset counts do not sum to their aggregates.")
    reconciled_values = [float(row["reconciledSeconds"]) for row in rows]
    payload = {
        "schemaVersion": REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA,
        "policy": REFERENCE_ENDPOINT_RECONCILIATION_POLICY,
        "sourceTrackCount": source_track_count,
        "reconciledTrackCount": reconciled_track_count,
        "unreconciledTrackCount": source_track_count - reconciled_track_count,
        "datasetCounts": dataset_counts,
        "datasetCountSetSha256": canonical_sha256(dataset_counts),
        "totalReconciledSeconds": math.fsum(reconciled_values),
        "maximumReconciledSeconds": max(reconciled_values, default=0.0),
        "rows": rows,
        "rowSetSha256": canonical_sha256(rows),
    }
    audit = {**payload, "auditSha256": canonical_sha256(payload)}
    _exact_keys(
        audit,
        _REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_KEYS,
        "reference endpoint reconciliation audit",
    )
    return audit


def build_bar_selector_group_manifest(
    track_descriptors: Sequence[Mapping[str, Any]],
    *,
    reference_root: Path,
) -> dict[str, Any]:
    """Seal explicit development grouping and reference metadata.

    Every descriptor is validated, including its split and explicit
    ``confidenceGroupId``, before the reference root or any reference path is
    resolved or opened. Reference paths may be absolute or relative on input,
    but every emitted ``referenceFile`` is relative to ``reference_root``.
    """

    descriptors = list(_sequence(track_descriptors, "track_descriptors"))
    if not descriptors:
        raise ValueError("At least one explicit development track descriptor is required.")
    validated: list[dict[str, str]] = []
    track_ids: set[str] = set()
    # Global no-I/O preflight. Keep all path resolution below this loop.
    for index, raw_descriptor in enumerate(descriptors):
        descriptor = _mapping(raw_descriptor, f"track_descriptors[{index}]")
        _exact_keys(descriptor, _GROUP_DESCRIPTOR_KEYS, f"track_descriptors[{index}]")
        _split(descriptor.get("split"), f"track_descriptors[{index}].split")
        track_id = _required_string(descriptor.get("trackId"), f"track_descriptors[{index}].trackId")
        if track_id in track_ids:
            raise ValueError(f"Duplicate group-manifest track id {track_id!r}.")
        track_ids.add(track_id)
        validated.append(
            {
                "trackId": track_id,
                "datasetId": _required_dataset_id(
                    descriptor.get("datasetId"),
                    f"track_descriptors[{index}].datasetId",
                ),
                "role": _required_string(
                    descriptor.get("role"),
                    f"track_descriptors[{index}].role",
                ),
                "confidenceGroupId": _required_string(
                    descriptor.get("confidenceGroupId"),
                    f"track_descriptors[{index}].confidenceGroupId",
                ),
                "referencePath": _required_string(
                    descriptor.get("referencePath"),
                    f"track_descriptors[{index}].referencePath",
                ),
            }
        )

    try:
        resolved_root = reference_root.resolve(strict=True)
    except OSError as error:
        raise ValueError("reference_root must resolve to an existing directory.") from error
    if not resolved_root.is_dir():
        raise ValueError("reference_root must resolve to an existing directory.")

    tracks: list[dict[str, Any]] = []
    for descriptor in validated:
        raw_path = Path(descriptor["referencePath"])
        candidate = raw_path if raw_path.is_absolute() else resolved_root / raw_path
        try:
            reference_path = candidate.resolve(strict=True)
            relative_path = reference_path.relative_to(resolved_root)
        except (OSError, ValueError) as error:
            raise ValueError(
                f"Reference for track {descriptor['trackId']!r} must resolve beneath reference_root."
            ) from error
        if not reference_path.is_file():
            raise ValueError(f"Reference for track {descriptor['trackId']!r} must be a regular file.")
        reference, reference_bytes = _read_json(
            reference_path,
            f"reference {descriptor['trackId']!r}",
        )
        if not isinstance(reference.get("segments"), Sequence) or isinstance(
            reference.get("segments"),
            (str, bytes, bytearray),
        ):
            raise ValueError(f"Reference for track {descriptor['trackId']!r} must contain segments.")
        track_payload: dict[str, Any] = {
            "trackId": descriptor["trackId"],
            "split": DEVELOPMENT_SPLIT,
            "datasetId": descriptor["datasetId"],
            "role": descriptor["role"],
            "confidenceGroupId": descriptor["confidenceGroupId"],
            "referenceFile": relative_path.as_posix(),
            "referenceSha256": _file_sha256(reference_bytes),
        }
        tracks.append(
            {
                **track_payload,
                "trackMetadataSha256": canonical_sha256(track_payload),
            }
        )
    tracks.sort(key=lambda value: str(value["trackId"]))
    manifest_payload: dict[str, Any] = {
        "schemaVersion": GROUP_MANIFEST_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "tracks": tracks,
        "trackSetSha256": canonical_sha256(
            [
                {
                    "trackId": track["trackId"],
                    "trackMetadataSha256": track["trackMetadataSha256"],
                }
                for track in tracks
            ]
        ),
    }
    return {
        **manifest_payload,
        "manifestSha256": canonical_sha256(manifest_payload),
    }


def _validate_same_track_set(*track_maps: Mapping[str, Any]) -> list[str]:
    expected = set(track_maps[0])
    if any(set(values) != expected for values in track_maps[1:]):
        raise ValueError(
            "Benchmark, runtime timing, confidence-group, and audio-lineage artifacts "
            "must bind the exact same track ids."
        )
    return sorted(expected)


def _preflight_summary_output_root(
    summary_output_root: Path,
    *,
    benchmark_root: Path,
    runtime_bar_grid_root: Path,
    group_manifest_root: Path,
) -> None:
    """Require a path-disjoint write root after resolving existing symlinks."""

    output = summary_output_root.resolve(strict=False)
    for name, raw_root in (
        ("benchmark_root", benchmark_root),
        ("runtime_bar_grid_root", runtime_bar_grid_root),
        ("group_manifest_root", group_manifest_root),
    ):
        root = raw_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError(f"{name} must resolve to an existing directory.")
        if output == root or output.is_relative_to(root) or root.is_relative_to(output):
            raise ValueError(
                "summary_output_root must be path-disjoint from benchmark, runtime, "
                f"and group artifact roots after symlink resolution; overlap with {name}."
            )


def _require_runtime_selector_timing(
    timing: Mapping[str, Any],
    analyzer_contract_sha256: str,
) -> None:
    if timing.get("schemaVersion") != EXPLICIT_BAR_GRID_SCHEMA:
        raise ValueError("Selector timing must use the explicit runtime bar-grid schema.")
    provenance = _mapping(timing.get("timingProvenance"), "runtime timing timingProvenance")
    bar_source = _mapping(
        provenance.get("barStartsSeconds"),
        "runtime timing barStartsSeconds provenance",
    )
    if bar_source.get("status") != "explicit":
        raise ValueError("Selector timing must have explicit bar-start provenance.")
    if bar_source.get("sourceClass") != "runtime":
        raise ValueError("Selector timing must come from the actual runtime source class.")
    if bar_source.get("deployable") is not True or bar_source.get("referenceFree") is not True:
        raise ValueError("Selector timing must be deployable and reference-free.")
    if (
        _required_sha256(
            bar_source.get("sourceContractSha256"),
            "runtime timing sourceContractSha256",
        )
        != analyzer_contract_sha256
    ):
        raise ValueError("Selector timing source contract does not match the runtime analyzer manifest.")


def _shared_binding(
    summary: Mapping[str, Any],
    prediction: Mapping[str, Any],
    report_contract: Mapping[str, Any],
) -> dict[str, Any]:
    summary_binding = _mapping(summary.get("binding"), "bar summary binding")
    summary_timing = _mapping(summary.get("timing"), "bar summary timing")
    uncertainty = _mapping(prediction.get("uncertainty"), "prediction uncertainty")
    uncertainty_binding = _mapping(uncertainty.get("binding"), "prediction uncertainty binding")
    result = {
        "barSummarySchemaVersion": COMPACT_BAR_SUMMARY_SCHEMA,
        "featureNames": list(BAR_FEATURE_NAMES),
        "barFeatureContractSha256": summary_binding.get("barFeatureContractSha256"),
        "uncertaintySchemaVersion": uncertainty.get("schemaVersion"),
        "uncertaintyContractSha256": summary_binding.get("uncertaintyContractSha256"),
        "modelOrEnsembleSha256": uncertainty_binding.get("modelOrEnsembleSha256"),
        "decoderContractSha256": uncertainty_binding.get("decoderContractSha256"),
        "memberOrderSha256": uncertainty_binding.get("memberOrderSha256"),
        "sourceFeatureKind": summary_binding.get("sourceFeatureKind"),
        "sourceFeatureSpecSha256": summary_binding.get("sourceFeatureSpecSha256"),
        "observabilityProfileSchemaVersion": summary_binding.get("observabilityProfileSchemaVersion"),
        "timingSchemaVersion": EXPLICIT_BAR_GRID_SCHEMA,
        "timingSourceClass": summary_timing.get("sourceClass"),
        "timingSourceId": summary_timing.get("sourceId"),
        "timingSourceContractSha256": summary_binding.get("timingSourceContractSha256"),
        "barOutcomeEligibilityContract": dict(BAR_OUTCOME_ELIGIBILITY_CONTRACT),
        "barOutcomeEligibilityContractSha256": BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    }
    _exact_keys(result, _SHARED_BINDING_KEYS, "sharedBindings")
    for name in (
        "barFeatureContractSha256",
        "uncertaintyContractSha256",
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "sourceFeatureSpecSha256",
        "timingSourceContractSha256",
        "barOutcomeEligibilityContractSha256",
    ):
        _required_sha256(result[name], f"sharedBindings.{name}")
    for name in (
        "barSummarySchemaVersion",
        "uncertaintySchemaVersion",
        "sourceFeatureKind",
        "observabilityProfileSchemaVersion",
        "timingSchemaVersion",
        "timingSourceClass",
        "timingSourceId",
    ):
        _required_string(result[name], f"sharedBindings.{name}")
    if result["barFeatureContractSha256"] != BAR_FEATURE_CONTRACT_SHA256:
        raise ValueError("The bar summary uses the wrong frozen feature contract.")
    if result["uncertaintySchemaVersion"] != FACTORIZED_UNCERTAINTY_SCHEMA:
        raise ValueError("The bar summary uses the wrong uncertainty schema.")
    if result["timingSourceClass"] != "runtime":
        raise ValueError("Selector examples require runtime timing.")
    if result["barOutcomeEligibilityContract"] != BAR_OUTCOME_ELIGIBILITY_CONTRACT:
        raise ValueError("The bar outcome/eligibility contract changed.")
    for name in ("uncertaintyContractSha256", "modelOrEnsembleSha256", "decoderContractSha256", "memberOrderSha256"):
        if result[name] != report_contract[name]:
            raise ValueError(f"Prediction bar summary disagrees with report {name}.")
    return result


def _compact_bar_summary(
    summary: Mapping[str, Any],
    bar: Mapping[str, Any],
    shared_bindings_sha256: str,
    audio_lineage_row: Mapping[str, Any],
    audio_lineage_projection_sha256: str,
) -> dict[str, Any]:
    binding = _mapping(summary.get("binding"), "bar summary binding")
    feature_values = _mapping(bar.get("featureValues"), "bar featureValues")
    # JSON object order is not semantic; normalize explicitly for in-memory
    # consumers before the publisher's sort_keys=True disk representation.
    if set(feature_values) != set(BAR_FEATURE_NAMES):
        raise ValueError("Bar featureValues do not contain the exact frozen feature key set.")
    payload: dict[str, Any] = {
        "schemaVersion": COMPACT_BAR_SUMMARY_SCHEMA,
        "trackId": summary.get("trackId"),
        "sourceSummarySha256": summary.get("summarySha256"),
        "predictionCoreSha256": binding.get("predictionCoreSha256"),
        "uncertaintySha256": binding.get("uncertaintySha256"),
        "timingSha256": binding.get("timingSha256"),
        "sourceAudioSha256": audio_lineage_row.get("sourceAudioSha256"),
        "cachedFeatureArraySha256": audio_lineage_row.get("cachedArraySha256"),
        "freshFeatureArraySha256": audio_lineage_row.get("freshArraySha256"),
        "canonicalDurationMilliseconds": audio_lineage_row.get("canonicalDurationMilliseconds"),
        "audioLineageRowSha256": audio_lineage_row.get("rowSha256"),
        "audioLineageProjectionSha256": audio_lineage_projection_sha256,
        "barFeatureContractSha256": binding.get("barFeatureContractSha256"),
        "sharedBindingsSha256": shared_bindings_sha256,
        "index": bar.get("index"),
        "start": bar.get("start"),
        "end": bar.get("end"),
        "predictionProduct": bar.get("predictionProduct"),
        "predictionProductDurationSeconds": bar.get("predictionProductDurationSeconds"),
        "predictionCoverage": bar.get("predictionCoverage"),
        "predictionDominance": bar.get("predictionDominance"),
        "predictionTransitionCount": bar.get("predictionTransitionCount"),
        "featureValues": {feature_name: feature_values[feature_name] for feature_name in BAR_FEATURE_NAMES},
    }
    if tuple(payload) != _COMPACT_BAR_KEYS:
        raise RuntimeError("Internal compact bar-summary field order drifted.")
    for name in (
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "audioLineageRowSha256",
        "audioLineageProjectionSha256",
        "barFeatureContractSha256",
        "sharedBindingsSha256",
    ):
        _required_sha256(payload[name], f"barSummary.{name}")
    _required_string(payload["trackId"], "barSummary.trackId")
    _strict_integer(
        payload["canonicalDurationMilliseconds"],
        "barSummary.canonicalDurationMilliseconds",
        minimum=1,
    )
    _strict_integer(payload["index"], "barSummary.index")
    for name in (
        "start",
        "end",
        "predictionProductDurationSeconds",
        "predictionCoverage",
        "predictionDominance",
    ):
        _finite(payload[name], f"barSummary.{name}")
    _strict_integer(payload["predictionTransitionCount"], "barSummary.predictionTransitionCount")
    if payload["predictionProduct"] is not None:
        _required_string(payload["predictionProduct"], "barSummary.predictionProduct")
    return {**payload, "barSummarySha256": canonical_sha256(payload)}


def _frozen_bar_score_inputs(
    reference: Mapping[str, Any],
    prediction: Mapping[str, Any],
    timing: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Align one undeclared unique terminal reference end after the exact player-ms join."""

    prediction_duration = _finite(
        prediction.get("durationSeconds"),
        "prediction durationSeconds for bar scoring",
    )
    runtime_duration = _finite(
        timing.get("durationSeconds"),
        "runtime timing durationSeconds for bar scoring",
    )
    summary_duration = _finite(
        summary.get("durationSeconds"),
        "bar summary durationSeconds for bar scoring",
    )
    if prediction_duration <= 0 or runtime_duration <= 0:
        raise ValueError("Bar scoring durations must be positive.")
    canonical_prediction_milliseconds = math.floor(prediction_duration * 1000 + 0.5)
    canonical_prediction_duration = canonical_prediction_milliseconds / 1000
    if runtime_duration != canonical_prediction_duration:
        raise ValueError(
            "Runtime bar scoring duration must exactly equal the player-canonical "
            "millisecond rounding of prediction duration."
        )
    if summary_duration != prediction_duration:
        raise ValueError("Bar summary duration must exactly equal full-precision prediction duration.")
    summary_timing = _mapping(summary.get("timing"), "bar summary timing for scoring")
    expected_alignment = "exact" if runtime_duration == prediction_duration else "player-canonical-millisecond"
    if (
        summary_timing.get("durationSeconds") != runtime_duration
        or summary_timing.get("predictionDurationSeconds") != prediction_duration
        or summary_timing.get("durationAlignment") != expected_alignment
    ):
        raise ValueError("Bar summary timing does not retain the exact frozen duration join.")

    raw_segments = list(_sequence(reference.get("segments"), "reference segments for bar scoring"))
    scoring_segments: list[dict[str, Any]] = []
    segment_endpoints: list[tuple[float, float]] = []
    previous_start: float | None = None
    previous_end: float | None = None
    for index, raw_segment in enumerate(raw_segments):
        segment = _mapping(raw_segment, f"reference segments for bar scoring[{index}]")
        start = _finite(segment.get("start"), f"reference segment {index} start")
        end = _finite(segment.get("end"), f"reference segment {index} end")
        if start < 0 or end <= start:
            raise ValueError("Reference segment endpoints must be nonnegative and strictly increasing.")
        if previous_start is not None and (start < previous_start or start < float(previous_end)):
            raise ValueError("Reference segments must already be chronologically ordered and nonoverlapping.")
        previous_start = start
        previous_end = end
        scoring_segments.append(dict(segment))
        segment_endpoints.append((start, end))

    scoring_reference = dict(reference)
    reconciliation: dict[str, Any] | None = None
    declared_reference_duration = reference.get("durationSeconds")
    if declared_reference_duration is not None:
        reference_duration = _finite(
            declared_reference_duration,
            "reference durationSeconds for bar scoring",
        )
        if reference_duration not in {prediction_duration, runtime_duration}:
            raise ValueError(
                "Reference duration must exactly equal either the full-precision prediction "
                "duration or its player-canonical millisecond duration."
            )
    elif segment_endpoints:
        original_end = max(end for _start, end in segment_endpoints)
        if original_end > prediction_duration:
            terminal_index = len(segment_endpoints) - 1
            overhanging_indices = [
                index for index, (_start, end) in enumerate(segment_endpoints) if end > prediction_duration
            ]
            maximum_indices = [index for index, (_start, end) in enumerate(segment_endpoints) if end == original_end]
            terminal_start = segment_endpoints[terminal_index][0]
            if overhanging_indices != [terminal_index] or maximum_indices != [terminal_index]:
                raise ValueError("Only one unique terminal reference segment end may exceed prediction duration.")
            if terminal_start >= prediction_duration:
                raise ValueError("The reconciled terminal reference segment must start before prediction duration.")
            canonical_reference_milliseconds = math.floor(original_end * 1000 + 0.5)
            if canonical_reference_milliseconds != canonical_prediction_milliseconds:
                raise ValueError(
                    "An undeclared reference endpoint may exceed prediction duration only inside the same "
                    "player-canonical millisecond."
                )
            scoring_segments[terminal_index]["end"] = prediction_duration
            reconciliation = {
                "originalEnd": original_end,
                "predictionDuration": prediction_duration,
                "reconciledEnd": prediction_duration,
                "reconciledSeconds": original_end - prediction_duration,
                "canonicalMs": canonical_prediction_milliseconds,
            }
    scoring_reference["segments"] = scoring_segments
    scoring_reference["durationSeconds"] = prediction_duration
    scoring_timing: dict[str, Any] = {
        "durationSeconds": prediction_duration,
        "barStartsSeconds": list(_sequence(timing.get("barStartsSeconds"), "runtime timing barStartsSeconds")),
        "timingProvenance": dict(_mapping(timing.get("timingProvenance"), "runtime timing timingProvenance")),
    }
    if "prefixExcludedSeconds" in timing:
        scoring_timing["prefixExcludedSeconds"] = timing["prefixExcludedSeconds"]
    return scoring_reference, scoring_timing, reconciliation


def _validate_frozen_bar_score(score: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if score.get("schemaVersion") != BAR_SCORE_SCHEMA:
        raise ValueError("Reference bar score uses an unsupported schemaVersion.")
    if dict(_mapping(score.get("configuration"), "reference bar score configuration")) != {
        "referenceDominance": BAR_OUTCOME_ELIGIBILITY_CONTRACT["referenceDominance"],
        "predictionCoverage": BAR_OUTCOME_ELIGIBILITY_CONTRACT["predictionCoverage"],
        "predictionDominance": BAR_OUTCOME_ELIGIBILITY_CONTRACT["predictionDominance"],
    }:
        raise ValueError("Reference bar score changed the frozen eligibility configuration.")
    curve = list(_sequence(score.get("curve"), "reference bar score curve"))
    if len(curve) != 1:
        raise ValueError("Reference bar score must contain exactly the frozen zero threshold.")
    point = _mapping(curve[0], "reference bar score curve[0]")
    minimum_confidence = _finite(
        point.get("minimumConfidence"),
        "reference bar score curve[0].minimumConfidence",
    )
    if (
        set(point)
        != {
            "minimumConfidence",
            "eligibleBarCount",
            "acceptedBarCount",
            "correctBarCount",
            "barPrecision",
            "barCoverage",
            "hasSupport",
        }
        or minimum_confidence != 0.0
    ):
        raise ValueError("Reference bar score curve changed the frozen zero threshold contract.")
    bars = [
        _mapping(row, f"reference bar score bars[{index}]")
        for index, row in enumerate(_sequence(score.get("bars"), "reference bar score bars"))
    ]
    if len(bars) != _strict_integer(score.get("totalBarCount"), "reference bar score totalBarCount"):
        raise ValueError("Reference bar score totalBarCount disagrees with its bar rows.")
    for index, row in enumerate(bars):
        if not isinstance(row.get("eligible"), bool) or (
            row.get("correct") is not None and not isinstance(row.get("correct"), bool)
        ):
            raise ValueError(
                f"Reference bar score bars[{index}] changed the frozen inclusion rule eligibility/outcome types."
            )
    included = [row for row in bars if row.get("eligible") is True and isinstance(row.get("correct"), bool)]
    eligible_count = _strict_integer(score.get("eligibleBarCount"), "reference bar score eligibleBarCount")
    scorable_count = _strict_integer(
        score.get("scorablePredictionBarCount"),
        "reference bar score scorablePredictionBarCount",
    )
    point_eligible_count = _strict_integer(
        point.get("eligibleBarCount"),
        "reference bar score curve[0].eligibleBarCount",
    )
    point_accepted_count = _strict_integer(
        point.get("acceptedBarCount"),
        "reference bar score curve[0].acceptedBarCount",
    )
    point_correct_count = _strict_integer(
        point.get("correctBarCount"),
        "reference bar score curve[0].correctBarCount",
    )
    if not isinstance(point.get("hasSupport"), bool):
        raise ValueError("Reference bar score curve hasSupport must be boolean.")
    if (
        point_eligible_count != eligible_count
        or eligible_count != sum(row["eligible"] is True for row in bars)
        or point_accepted_count != scorable_count
        or point_accepted_count != len(included)
        or point_correct_count != sum(bool(row["correct"]) for row in included)
        or point.get("hasSupport") is not bool(included)
    ):
        raise ValueError("Reference bar score curve disagrees with the frozen inclusion rule.")
    return bars


def _aligned_score_bar(summary_bar: Mapping[str, Any], score_bar: Mapping[str, Any]) -> None:
    if summary_bar.get("index") != score_bar.get("index"):
        raise ValueError("Bar summary and reference score indices disagree.")
    for name in ("start", "end"):
        left = _finite(summary_bar.get(name), f"summary bar {name}")
        right = _finite(score_bar.get(name), f"score bar {name}")
        if not math.isclose(left, right, rel_tol=0, abs_tol=_EPSILON):
            raise ValueError(f"Bar summary and reference score {name} disagree.")
    # The existing bar-product scorer intentionally does not inspect a
    # prediction when the reference bar is structurally ineligible.
    if score_bar.get("eligible") is True:
        for name in ("predictionCoverage", "predictionDominance"):
            left = _finite(summary_bar.get(name), f"summary bar {name}")
            right = _finite(score_bar.get(name), f"score bar {name}")
            if not math.isclose(left, right, rel_tol=0, abs_tol=_EPSILON):
                raise ValueError(f"Bar summary and reference score {name} disagree.")
        if summary_bar.get("predictionProduct") != score_bar.get("predictionProduct"):
            raise ValueError("Bar summary and reference score predicted products disagree.")


def build_bar_selector_examples(
    benchmark_report: Mapping[str, Any],
    *,
    audio_lineage_manifest: Mapping[str, Any],
    benchmark_root: Path,
    runtime_bar_grid_manifest: Mapping[str, Any],
    runtime_bar_grid_root: Path,
    group_manifest: Mapping[str, Any],
    group_manifest_root: Path,
    summary_output_root: Path,
) -> dict[str, Any]:
    """Join sealed development telemetry to one-bit bar correctness outcomes.

    The four JSON envelopes are already-parsed mappings so their split gates
    can be checked before this function touches any nested prediction, timing,
    or reference path.
    """

    report = _mapping(benchmark_report, "benchmark_report")
    runtime_manifest = _mapping(runtime_bar_grid_manifest, "runtime_bar_grid_manifest")
    groups = _mapping(group_manifest, "group_manifest")
    audio_lineage = _mapping(audio_lineage_manifest, "audio_lineage_manifest")

    # This is intentionally the first validation phase. Do not move path work
    # above it: protected-split tests depend on zero nested artifact access.
    _validate_development_envelopes(report, runtime_manifest, groups, audio_lineage)
    validated_audio_lineage = _validate_audio_lineage_preflight(audio_lineage)
    report_tracks, report_contract = _validate_report(report)
    metadata_runtime_manifest = validate_runtime_bar_grid_manifest(
        runtime_manifest,
        artifact_root=None,
        verify_sources=False,
    )
    runtime_tracks = {
        str(track["trackId"]): dict(track)
        for track in _sequence(
            metadata_runtime_manifest.get("tracks"),
            "validated runtime manifest tracks",
        )
    }
    group_tracks = _validate_group_manifest(groups)
    track_ids = _validate_same_track_set(report_tracks, runtime_tracks, group_tracks)
    audio_lineage_projection, projection_tracks = _validate_report_audio_lineage_binding(
        report_contract,
        validated_audio_lineage,
        track_ids,
    )
    _validate_same_track_set(report_tracks, projection_tracks)
    _validate_cross_audio_bindings(
        track_ids,
        report_tracks,
        runtime_tracks,
        group_tracks,
        projection_tracks,
    )
    audio_group_audit = _audio_group_audit(track_ids, group_tracks, projection_tracks)

    # Only after every split, lineage, cross-artifact audio/cache/duration, and
    # duplicate-audio grouping check passes may a prediction, timing, or
    # reference leaf be opened.
    _preflight_summary_output_root(
        summary_output_root,
        benchmark_root=benchmark_root,
        runtime_bar_grid_root=runtime_bar_grid_root,
        group_manifest_root=group_manifest_root,
    )
    validated_runtime_manifest = validate_runtime_bar_grid_manifest(
        runtime_manifest,
        artifact_root=runtime_bar_grid_root,
        verify_sources=True,
    )
    if validated_runtime_manifest != metadata_runtime_manifest:
        raise ValueError("Runtime manifest changed between metadata preflight and source verification.")
    runtime_analyzer_contract = _mapping(
        validated_runtime_manifest.get("analyzerContract"),
        "runtime analyzerContract",
    )
    runtime_analyzer_contract_sha256 = _required_sha256(
        runtime_analyzer_contract.get("contractSha256"),
        "runtime analyzer contractSha256",
    )

    feature_records: list[dict[str, Any]] = []
    shared_bindings: dict[str, Any] | None = None
    for track_id in track_ids:
        report_track = report_tracks[track_id]
        runtime_track = runtime_tracks[track_id]
        audio_lineage_row = projection_tracks[track_id]
        prediction_path = _artifact_path(
            benchmark_root,
            report_track["predictionFile"],
            f"report track {track_id!r} predictionFile",
        )
        prediction, prediction_bytes = _read_json(prediction_path, f"prediction {track_id!r}")
        if _file_sha256(prediction_bytes) != report_track["predictionSha256"]:
            raise ValueError(f"Prediction file hash mismatch for track {track_id!r}.")
        if prediction.get("id") != track_id:
            raise ValueError(f"Prediction id mismatch for track {track_id!r}.")
        for field in ("predictionCoreSha256", "uncertaintySha256"):
            if prediction.get(field) != report_track[field]:
                raise ValueError(f"Prediction {field} disagrees with its benchmark row for {track_id!r}.")
        uncertainty = _mapping(prediction.get("uncertainty"), f"prediction {track_id!r} uncertainty")
        if dict(_mapping(uncertainty.get("binding"), "prediction uncertainty binding")) != report_contract["binding"]:
            raise ValueError(f"Prediction uncertainty binding disagrees with the report for {track_id!r}.")
        if list(_sequence(uncertainty.get("members"), "prediction uncertainty members")) != report_contract["members"]:
            raise ValueError(f"Prediction uncertainty members disagree with the report for {track_id!r}.")

        timing_path = _artifact_path(
            runtime_bar_grid_root,
            runtime_track["timingFile"],
            f"runtime track {track_id!r} timingFile",
        )
        timing, _timing_bytes = _read_json(timing_path, f"runtime timing {track_id!r}")
        if canonical_sha256(timing) != runtime_track["timingSha256"]:
            raise ValueError(f"Runtime timing hash mismatch for track {track_id!r}.")
        if timing.get("contractSha256") != runtime_track["timingContractSha256"]:
            raise ValueError(f"Runtime timing contract mismatch for track {track_id!r}.")
        timing_duration = _finite(timing.get("durationSeconds"), "runtime timing durationSeconds")
        if not math.isclose(
            timing_duration,
            _finite(runtime_track.get("durationSeconds"), "runtime manifest durationSeconds"),
            rel_tol=0,
            abs_tol=_EPSILON,
        ):
            raise ValueError(f"Runtime timing duration disagrees with the manifest for track {track_id!r}.")
        if runtime_track.get("barCount") != len(
            _sequence(timing.get("barStartsSeconds"), "runtime timing barStartsSeconds")
        ):
            raise ValueError(f"Runtime timing bar count disagrees with the manifest for track {track_id!r}.")
        _require_runtime_selector_timing(timing, runtime_analyzer_contract_sha256)
        if prediction.get("decoderContractSha256") != report_contract["decoderContractSha256"]:
            raise ValueError(f"Prediction decoder contract disagrees with the report for {track_id!r}.")

        # This is the last prediction-only operation for the track. The complete
        # summary and every compact per-bar hash are frozen before references.
        summary = summarize_prediction_bars(prediction, timing)
        claimed_summary_sha256 = _required_sha256(summary.get("summarySha256"), "bar summarySha256")
        if (
            canonical_sha256({key: value for key, value in summary.items() if key != "summarySha256"})
            != claimed_summary_sha256
        ):
            raise ValueError(f"Prediction bar summary hash mismatch for track {track_id!r}.")
        if summary.get("schemaVersion") != BAR_UNCERTAINTY_SCHEMA:
            raise ValueError("Prediction bar summary uses an unsupported schema.")
        if summary.get("referenceFree") is not True or summary.get("selectorUseAllowed") is not True:
            raise ValueError("Prediction bar summaries must be reference-free and selector-enabled.")
        if summary.get("trackId") != track_id:
            raise ValueError(f"Prediction bar-summary track id mismatch for {track_id!r}.")
        binding = _shared_binding(summary, prediction, report_contract)
        if binding["timingSourceContractSha256"] != runtime_analyzer_contract_sha256:
            raise ValueError(f"Runtime timing source contract disagrees with its manifest for {track_id!r}.")
        if shared_bindings is None:
            shared_bindings = binding
        elif binding != shared_bindings:
            raise ValueError("All selector examples must share one exact model/feature/timing-source binding.")
        shared_bindings_sha256 = canonical_sha256(shared_bindings)
        summary_path = summary_output_root / summary_artifact_filename(
            track_id,
            claimed_summary_sha256,
        )
        _atomic_write_json(summary_path, summary)
        materialized_summary, _materialized_bytes = _read_json(
            summary_path,
            f"materialized prediction-only summary {track_id!r}",
        )
        if materialized_summary != summary:
            raise RuntimeError(f"Materialized prediction-only summary changed for track {track_id!r}.")
        summary_bars = list(_sequence(summary.get("bars"), f"bar summary {track_id!r} bars"))
        compact_bars = [
            _compact_bar_summary(
                summary,
                _mapping(bar, "bar summary row"),
                shared_bindings_sha256,
                audio_lineage_row,
                str(audio_lineage_projection["projectionSha256"]),
            )
            for bar in summary_bars
        ]
        feature_records.append(
            {
                "trackId": track_id,
                "prediction": prediction,
                "timing": timing,
                "summary": summary,
                "summaryBars": summary_bars,
                "compactBars": compact_bars,
                "audioLineageRow": audio_lineage_row,
            }
        )

    if shared_bindings is None:
        raise RuntimeError("At least one shared selector binding is required.")

    # Reference phase. At this point all tracks, not merely the current track,
    # have complete and hash-stable prediction-only bar features in memory.
    examples: list[dict[str, Any]] = []
    reference_endpoint_reconciliation_rows: list[dict[str, Any]] = []
    score_counts = _empty_label_counts()
    score_counts_by_dataset = {dataset_id: _empty_label_counts() for dataset_id in LABEL_DETERMINACY_DATASET_IDS}
    emitted_by_dataset = {dataset_id: 0 for dataset_id in LABEL_DETERMINACY_DATASET_IDS}

    def add_score_count(dataset_id: str, field: str, value: int = 1) -> None:
        count = _strict_integer(value, f"score {field}")
        score_counts_by_dataset.setdefault(dataset_id, _empty_label_counts())
        emitted_by_dataset.setdefault(dataset_id, 0)
        score_counts[field] += count
        score_counts_by_dataset[dataset_id][field] += count

    for record in feature_records:
        track_id = str(record["trackId"])
        group_track = group_tracks[track_id]
        dataset_id = _required_dataset_id(
            _mapping(record["audioLineageRow"], "audio-lineage row").get("datasetId"),
            f"audio-lineage track {track_id!r} datasetId",
        )
        reference_path = _artifact_path(
            group_manifest_root,
            group_track["referenceFile"],
            f"group track {track_id!r} referenceFile",
        )
        reference, reference_bytes = _read_json(reference_path, f"reference {track_id!r}")
        reference_sha256 = _file_sha256(reference_bytes)
        if reference_sha256 != group_track["referenceSha256"]:
            raise ValueError(f"Reference file hash mismatch for track {track_id!r}.")
        if reference_sha256 != report_tracks[track_id]["referenceSha256"]:
            raise ValueError(f"Reference hash disagrees with the benchmark row for track {track_id!r}.")
        scoring_reference, scoring_timing, endpoint_reconciliation = _frozen_bar_score_inputs(
            reference,
            record["prediction"],
            record["timing"],
            record["summary"],
        )
        reference_endpoint_reconciliation_row_sha256: str | None = None
        if endpoint_reconciliation is not None:
            canonical_milliseconds = _strict_integer(
                endpoint_reconciliation.get("canonicalMs"),
                "reference endpoint reconciliation canonicalMs",
                minimum=1,
            )
            audio_lineage_canonical_milliseconds = _strict_integer(
                _mapping(record["audioLineageRow"], "audio-lineage row").get("canonicalDurationMilliseconds"),
                "audio-lineage canonicalDurationMilliseconds",
                minimum=1,
            )
            if canonical_milliseconds != audio_lineage_canonical_milliseconds:
                raise ValueError(
                    "Reference endpoint reconciliation disagrees with the exact audio-lineage canonical millisecond."
                )
            reconciliation_payload = {
                "trackId": track_id,
                "datasetId": dataset_id,
                "referenceSha256": reference_sha256,
                **endpoint_reconciliation,
            }
            reconciliation_row = {
                **reconciliation_payload,
                "rowSha256": canonical_sha256(reconciliation_payload),
            }
            _exact_keys(
                reconciliation_row,
                _REFERENCE_ENDPOINT_RECONCILIATION_ROW_KEYS,
                "reference endpoint reconciliation row",
            )
            reference_endpoint_reconciliation_rows.append(reconciliation_row)
            reference_endpoint_reconciliation_row_sha256 = reconciliation_row["rowSha256"]
        score = score_bar_product_confidence(
            scoring_reference,
            record["prediction"],
            timing=scoring_timing,
            confidence_thresholds=tuple(BAR_OUTCOME_ELIGIBILITY_CONTRACT["confidenceThresholds"]),
            reference_dominance=float(BAR_OUTCOME_ELIGIBILITY_CONTRACT["referenceDominance"]),
            prediction_coverage=float(BAR_OUTCOME_ELIGIBILITY_CONTRACT["predictionCoverage"]),
            prediction_dominance=float(BAR_OUTCOME_ELIGIBILITY_CONTRACT["predictionDominance"]),
        )
        if score.get("available") is not True or score.get("explicitBarGrid") is not True:
            raise ValueError(f"Reference bar scoring is unavailable for track {track_id!r}.")
        score_bars = _validate_frozen_bar_score(score)
        add_score_count(
            dataset_id,
            "totalBarCount",
            _strict_integer(score.get("totalBarCount"), "score totalBarCount"),
        )
        add_score_count(
            dataset_id,
            "referenceDeterminateBarCount",
            score.get("eligibleBarCount"),
        )
        add_score_count(
            dataset_id,
            "referenceMixedBarCount",
            score.get("excludedMixedBarCount"),
        )
        add_score_count(
            dataset_id,
            "referenceUncoveredBarCount",
            score.get("excludedUncoveredBarCount"),
        )
        # Validate the legacy scorer's prediction audit counts, but compute the
        # selector denominator below from the exact application-time gates.
        # In particular, the legacy scorer's confidence availability is not a
        # selector label-eligibility condition.
        for name in (
            "predictionMixedBarCount",
            "predictionUncoveredBarCount",
            "confidenceMissingBarCount",
            "scorablePredictionBarCount",
        ):
            _strict_integer(score.get(name), f"score {name}")
        if len(score_bars) != len(record["summaryBars"]):
            raise ValueError(f"Prediction summary and reference score bar counts disagree for {track_id!r}.")
        for summary_bar, compact_bar, raw_score_bar in zip(
            record["summaryBars"],
            record["compactBars"],
            score_bars,
            strict=True,
        ):
            score_bar = _mapping(raw_score_bar, "reference score bar")
            prediction_bar = _mapping(summary_bar, "prediction summary bar")
            _aligned_score_bar(prediction_bar, score_bar)
            if score_bar.get("eligible") is not True:
                continue
            prediction_product = prediction_bar.get("predictionProduct")
            prediction_coverage = _finite(
                prediction_bar.get("predictionCoverage"),
                "prediction summary bar predictionCoverage",
            )
            prediction_dominance = _finite(
                prediction_bar.get("predictionDominance"),
                "prediction summary bar predictionDominance",
            )
            if (
                prediction_product is None
                or prediction_coverage < BAR_OUTCOME_ELIGIBILITY_CONTRACT["predictionCoverage"]
            ):
                add_score_count(dataset_id, "predictionUncoveredBarCount")
                continue
            if prediction_dominance < BAR_OUTCOME_ELIGIBILITY_CONTRACT["predictionDominance"]:
                add_score_count(dataset_id, "predictionMixedBarCount")
                continue
            prediction_product = _required_string(
                prediction_product,
                "prediction summary bar predictionProduct",
            )
            reference_product = _required_string(
                score_bar.get("referenceProduct"),
                "reference score bar referenceProduct",
            )
            add_score_count(dataset_id, "predictionStructurallyScorableBarCount")
            legacy_product_confidence_missing = (
                score_bar.get("predictionExclusionReason") == "prediction-confidence-missing"
            )
            if legacy_product_confidence_missing:
                add_score_count(dataset_id, "predictionConfidenceMissingBarCount")
            elif not isinstance(score_bar.get("correct"), bool):
                raise ValueError(
                    "A structurally eligible prediction without legacy confidence must be explicitly audited."
                )
            correct = prediction_product == reference_product
            if isinstance(score_bar.get("correct"), bool) and score_bar.get("correct") is not correct:
                raise ValueError("Reference score correctness disagrees with the frozen product equality rule.")
            example_payload: dict[str, Any] = {
                "trackId": track_id,
                "split": DEVELOPMENT_SPLIT,
                "confidenceGroupId": group_track["confidenceGroupId"],
                "barIndex": compact_bar["index"],
                "barSummary": compact_bar,
                "modelOrEnsembleSha256": shared_bindings["modelOrEnsembleSha256"],
                "decoderContractSha256": shared_bindings["decoderContractSha256"],
                "memberOrderSha256": shared_bindings["memberOrderSha256"],
                "sourceAudioSha256": compact_bar["sourceAudioSha256"],
                "cachedFeatureArraySha256": compact_bar["cachedFeatureArraySha256"],
                "freshFeatureArraySha256": compact_bar["freshFeatureArraySha256"],
                "canonicalDurationMilliseconds": compact_bar["canonicalDurationMilliseconds"],
                "audioLineageRowSha256": compact_bar["audioLineageRowSha256"],
                "audioLineageProjectionSha256": compact_bar["audioLineageProjectionSha256"],
                "referenceEndpointReconciliationRowSha256": (reference_endpoint_reconciliation_row_sha256),
                "legacyProductConfidenceMissing": legacy_product_confidence_missing,
                "outcome": {"correct": correct},
            }
            example = {**example_payload, "exampleSha256": canonical_sha256(example_payload)}
            _exact_keys(example, _EXAMPLE_KEYS, "selector example")
            examples.append(example)
            emitted_by_dataset[dataset_id] = emitted_by_dataset.get(dataset_id, 0) + 1

    examples.sort(key=lambda value: (str(value["trackId"]), int(value["barIndex"])))
    if score_counts["predictionStructurallyScorableBarCount"] != len(examples):
        raise ValueError("Emitted examples disagree with the frozen scorable-prediction denominator.")
    complete_score_counts = _complete_label_counts(
        score_counts,
        emitted_example_count=len(examples),
        name="aggregate",
    )
    label_audit_payload = {
        "schemaVersion": LABEL_DETERMINACY_AUDIT_SCHEMA,
        "estimand": SELECTOR_ESTIMAND,
        "oofDenominator": OOF_DENOMINATOR,
        **complete_score_counts,
    }
    label_determinacy_audit = {
        **label_audit_payload,
        "auditSha256": canonical_sha256(label_audit_payload),
    }
    dataset_label_determinacy_audit = _dataset_label_determinacy_audit(
        score_counts_by_dataset,
        emitted_by_dataset,
        aggregate_counts=complete_score_counts,
        aggregate_audit_sha256=label_determinacy_audit["auditSha256"],
    )
    reference_endpoint_reconciliation_audit = _reference_endpoint_reconciliation_audit(
        reference_endpoint_reconciliation_rows,
        projection_tracks,
    )
    example_set_sha256 = canonical_sha256(examples)
    output_payload: dict[str, Any] = {
        "schemaVersion": EXAMPLES_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "sharedBindings": shared_bindings,
        "sharedBindingsSha256": canonical_sha256(shared_bindings),
        "sourceBenchmarkReportSha256": canonical_sha256(report),
        "sourceRuntimeBarGridManifestSha256": validated_runtime_manifest["manifestSha256"],
        "sourceGroupManifestSha256": groups["manifestSha256"],
        "sourceAudioLineageSha256": validated_audio_lineage["artifactSha256"],
        "sourceAudioLineageProjection": audio_lineage_projection,
        "sourceAudioLineageProjectionSha256": audio_lineage_projection["projectionSha256"],
        "sourceBenchmarkAudioLineageBindingSha256": report_contract["audioLineageBindingSha256"],
        "audioLineageVerificationMode": AUDIO_LINEAGE_VERIFICATION_MODE,
        "featureArrayVerification": FEATURE_ARRAY_VERIFICATION,
        "audioGroupAudit": audio_group_audit,
        "audioGroupAuditSha256": audio_group_audit["auditSha256"],
        "referenceEndpointReconciliationAudit": reference_endpoint_reconciliation_audit,
        "referenceEndpointReconciliationAuditSha256": reference_endpoint_reconciliation_audit["auditSha256"],
        "labelDeterminacyAudit": label_determinacy_audit,
        "labelDeterminacyAuditSha256": label_determinacy_audit["auditSha256"],
        "datasetLabelDeterminacyAudit": dataset_label_determinacy_audit,
        "datasetLabelDeterminacyAuditSha256": dataset_label_determinacy_audit["auditSha256"],
        "examples": examples,
        "exampleSetSha256": example_set_sha256,
    }
    output = {**output_payload, "artifactSha256": canonical_sha256(output_payload)}
    _exact_keys(output, _OUTPUT_KEYS, "selector examples artifact")
    return output


__all__ = [
    "AUDIO_GROUP_AUDIT_SCHEMA",
    "AUDIO_LINEAGE_VERIFICATION_MODE",
    "BAR_OUTCOME_ELIGIBILITY_CONTRACT",
    "BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256",
    "BENCHMARK_AUDIO_LINEAGE_SCHEMA",
    "COMPACT_BAR_SUMMARY_SCHEMA",
    "DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA",
    "DEVELOPMENT_SPLIT",
    "EXAMPLES_SCHEMA",
    "FEATURE_ARRAY_VERIFICATION",
    "GROUP_MANIFEST_SCHEMA",
    "LABEL_DETERMINACY_AUDIT_SCHEMA",
    "LABEL_DETERMINACY_DATASET_IDS",
    "OOF_DENOMINATOR",
    "REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA",
    "REFERENCE_ENDPOINT_RECONCILIATION_POLICY",
    "SELECTOR_ESTIMAND",
    "build_bar_selector_group_manifest",
    "build_bar_selector_examples",
    "summary_artifact_filename",
]
