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
from .uncertainty import FACTORIZED_UNCERTAINTY_SCHEMA


GROUP_MANIFEST_SCHEMA = "chord_bar_selector_group_manifest_v1"
EXAMPLES_SCHEMA = "chord_bar_selector_examples_v1"
COMPACT_BAR_SUMMARY_SCHEMA = "chord_bar_selector_bar_summary_v1"
DEVELOPMENT_SPLIT = "development"
BAR_SCORE_SCHEMA = "chord_bar_product_confidence_v1"
BAR_OUTCOME_ELIGIBILITY_CONTRACT = {
    "schemaVersion": "chord_bar_selector_outcome_eligibility_contract_v1",
    "scoreSchemaVersion": BAR_SCORE_SCHEMA,
    "referenceDominance": DEFAULT_REFERENCE_DOMINANCE,
    "predictionCoverage": DEFAULT_PREDICTION_COVERAGE,
    "predictionDominance": DEFAULT_PREDICTION_DOMINANCE,
    "confidenceThresholds": [0.0],
    "barEndDurationRule": ("full-precision-prediction-after-exact-player-canonical-millisecond-runtime-join"),
    "inclusionRule": "scoreBar.eligible=true and scoreBar.correct is boolean",
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
        "examples",
        "exampleSetSha256",
        "artifactSha256",
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
) -> None:
    """Reject every non-development declaration before path resolution/read."""

    _split(report.get("split"), "benchmark report split")
    _split(runtime_manifest.get("split"), "runtime bar-grid manifest split")
    _split(group_manifest.get("split"), "group manifest split")
    for source_name, source in (
        ("benchmark report", report),
        ("runtime bar-grid manifest", runtime_manifest),
        ("group manifest", group_manifest),
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
        for field in ("predictionSha256", "predictionCoreSha256", "uncertaintySha256", "referenceSha256"):
            _required_sha256(track.get(field), f"report track {track_id!r} {field}")
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
        _required_string(track.get("datasetId"), f"group track {track_id!r} datasetId")
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
                "datasetId": _required_string(
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
            "Benchmark, runtime timing, and confidence-group manifests must bind the exact same track ids."
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
) -> dict[str, Any]:
    binding = _mapping(summary.get("binding"), "bar summary binding")
    feature_values = _mapping(bar.get("featureValues"), "bar featureValues")
    if tuple(feature_values) != BAR_FEATURE_NAMES:
        raise ValueError("Bar featureValues are not in the exact frozen feature order.")
    payload: dict[str, Any] = {
        "schemaVersion": COMPACT_BAR_SUMMARY_SCHEMA,
        "trackId": summary.get("trackId"),
        "sourceSummarySha256": summary.get("summarySha256"),
        "predictionCoreSha256": binding.get("predictionCoreSha256"),
        "uncertaintySha256": binding.get("uncertaintySha256"),
        "timingSha256": binding.get("timingSha256"),
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
        "featureValues": dict(feature_values),
    }
    if tuple(payload) != _COMPACT_BAR_KEYS:
        raise RuntimeError("Internal compact bar-summary field order drifted.")
    for name in (
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
        "barFeatureContractSha256",
        "sharedBindingsSha256",
    ):
        _required_sha256(payload[name], f"barSummary.{name}")
    _required_string(payload["trackId"], "barSummary.trackId")
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
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Align only the final bar end after proving the exact player-ms join."""

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
    canonical_prediction_duration = math.floor(prediction_duration * 1000 + 0.5) / 1000
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

    scoring_reference = dict(reference)
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
    scoring_reference["durationSeconds"] = prediction_duration
    scoring_timing: dict[str, Any] = {
        "durationSeconds": prediction_duration,
        "barStartsSeconds": list(_sequence(timing.get("barStartsSeconds"), "runtime timing barStartsSeconds")),
        "timingProvenance": dict(_mapping(timing.get("timingProvenance"), "runtime timing timingProvenance")),
    }
    if "prefixExcludedSeconds" in timing:
        scoring_timing["prefixExcludedSeconds"] = timing["prefixExcludedSeconds"]
    return scoring_reference, scoring_timing


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
    benchmark_root: Path,
    runtime_bar_grid_manifest: Mapping[str, Any],
    runtime_bar_grid_root: Path,
    group_manifest: Mapping[str, Any],
    group_manifest_root: Path,
    summary_output_root: Path,
) -> dict[str, Any]:
    """Join sealed development telemetry to one-bit bar correctness outcomes.

    The three JSON envelopes are already-parsed mappings so their split gates
    can be checked before this function touches any nested prediction, timing,
    or reference path.
    """

    report = _mapping(benchmark_report, "benchmark_report")
    runtime_manifest = _mapping(runtime_bar_grid_manifest, "runtime_bar_grid_manifest")
    groups = _mapping(group_manifest, "group_manifest")

    # This is intentionally the first validation phase. Do not move path work
    # above it: protected-split tests depend on zero nested artifact access.
    _validate_development_envelopes(report, runtime_manifest, groups)
    _preflight_summary_output_root(
        summary_output_root,
        benchmark_root=benchmark_root,
        runtime_bar_grid_root=runtime_bar_grid_root,
        group_manifest_root=group_manifest_root,
    )
    report_tracks, report_contract = _validate_report(report)
    validated_runtime_manifest = validate_runtime_bar_grid_manifest(
        runtime_manifest,
        artifact_root=runtime_bar_grid_root,
        verify_sources=True,
    )
    runtime_tracks = {
        str(track["trackId"]): dict(track)
        for track in _sequence(
            validated_runtime_manifest.get("tracks"),
            "validated runtime manifest tracks",
        )
    }
    group_tracks = _validate_group_manifest(groups)
    track_ids = _validate_same_track_set(report_tracks, runtime_tracks, group_tracks)
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
            }
        )

    if shared_bindings is None:
        raise RuntimeError("At least one shared selector binding is required.")

    # Reference phase. At this point all tracks, not merely the current track,
    # have complete and hash-stable prediction-only bar features in memory.
    examples: list[dict[str, Any]] = []
    for record in feature_records:
        track_id = str(record["trackId"])
        group_track = group_tracks[track_id]
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
        scoring_reference, scoring_timing = _frozen_bar_score_inputs(
            reference,
            record["prediction"],
            record["timing"],
            record["summary"],
        )
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
        if len(score_bars) != len(record["summaryBars"]):
            raise ValueError(f"Prediction summary and reference score bar counts disagree for {track_id!r}.")
        for summary_bar, compact_bar, raw_score_bar in zip(
            record["summaryBars"],
            record["compactBars"],
            score_bars,
            strict=True,
        ):
            score_bar = _mapping(raw_score_bar, "reference score bar")
            _aligned_score_bar(_mapping(summary_bar, "prediction summary bar"), score_bar)
            correct = score_bar.get("correct")
            # Under the existing bar-product contract, correct is boolean only
            # after both reference eligibility and prediction structure pass.
            if score_bar.get("eligible") is not True or not isinstance(correct, bool):
                continue
            example_payload: dict[str, Any] = {
                "trackId": track_id,
                "split": DEVELOPMENT_SPLIT,
                "confidenceGroupId": group_track["confidenceGroupId"],
                "barIndex": compact_bar["index"],
                "barSummary": compact_bar,
                "modelOrEnsembleSha256": shared_bindings["modelOrEnsembleSha256"],
                "decoderContractSha256": shared_bindings["decoderContractSha256"],
                "memberOrderSha256": shared_bindings["memberOrderSha256"],
                "outcome": {"correct": correct},
            }
            example = {**example_payload, "exampleSha256": canonical_sha256(example_payload)}
            _exact_keys(example, _EXAMPLE_KEYS, "selector example")
            examples.append(example)

    examples.sort(key=lambda value: (str(value["trackId"]), int(value["barIndex"])))
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
        "examples": examples,
        "exampleSetSha256": example_set_sha256,
    }
    output = {**output_payload, "artifactSha256": canonical_sha256(output_payload)}
    _exact_keys(output, _OUTPUT_KEYS, "selector examples artifact")
    return output


__all__ = [
    "BAR_OUTCOME_ELIGIBILITY_CONTRACT",
    "BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256",
    "COMPACT_BAR_SUMMARY_SCHEMA",
    "DEVELOPMENT_SPLIT",
    "EXAMPLES_SCHEMA",
    "GROUP_MANIFEST_SCHEMA",
    "build_bar_selector_group_manifest",
    "build_bar_selector_examples",
    "summary_artifact_filename",
]
