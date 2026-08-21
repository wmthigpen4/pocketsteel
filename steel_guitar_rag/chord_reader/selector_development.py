"""Fail-closed orchestration for the development-only chord-bar selector.

This module connects the independently sealed audio-lineage, runtime timing,
bar-example, and grouped-selector components without making any of them a
production dependency.  It accepts only the frozen ``development`` partition,
publishes only new paths, and never selects an operating threshold.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import tempfile
from typing import Any

from .artifact_integrity import validate_factorized_artifact_manifest
from .audio_lineage import (
    AUDIO_LINEAGE_SCHEMA,
    DATASET_DESCRIPTOR_SCHEMA,
    build_development_audio_lineage,
    project_development_audio_lineage,
    validate_development_audio_lineage,
)
from .bar_examples import (
    DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
    EXAMPLES_SCHEMA,
    GROUP_MANIFEST_SCHEMA,
    LABEL_DETERMINACY_AUDIT_SCHEMA,
    build_bar_selector_examples,
    build_bar_selector_group_manifest,
)
from .bar_promotion import canonical_sha256
from .bar_selector import BAR_SELECTOR_ARTIFACT_SCHEMA, train_bar_selector
from .runtime_bar_grid import INPUT_MANIFEST_SCHEMA
from .split_protocol import validate_split_protocol_manifest
from .student import extract_student_features


DEVELOPMENT_SPLIT = "development"
DEVELOPMENT_INPUTS_SCHEMA = "chord_bar_selector_development_inputs_v1"
DERIVATIVE_REGISTRY_SCHEMA = "chord_bar_selector_derivative_registry_v1"
DERIVATIVE_MERGE_SCHEMA = "chord_bar_selector_derivative_merge_v1"
GROUPING_AUDIT_SCHEMA = "chord_bar_selector_grouping_audit_v1"
SOURCE_BINDINGS_SCHEMA = "chord_bar_selector_development_source_bindings_v1"
EXPECTED_DATASET_SHAPE_SCHEMA = "chord_bar_selector_expected_dataset_shape_v1"
PRODUCTION_EXTRACTOR_ENTRYPOINT = f"{extract_student_features.__module__}.{extract_student_features.__qualname__}"

_CERTIFICATION_DATASET_IDS = (
    "aam",
    "guitarset",
    "idmt_guitar",
    "nrgcp",
    "winterreise",
)
_SUPPORTED_DATASETS = frozenset(_CERTIFICATION_DATASET_IDS)
_REVIEWED_DATASET_BASE_GROUP_SIZES = (
    ("aam", (1, 1)),
    ("guitarset", (12, 12, 12)),
    ("idmt_guitar", (8, 8, 8, 8, 8, 8)),
    ("nrgcp", (1,) * 156),
    ("winterreise", (2, 2)),
)
_GUITARSET_PLAYERS = tuple(f"{index:02d}" for index in range(6))
_GUITARSET_ROLES = frozenset(
    f"guitarset:{performance}:player-{player}" for performance in ("comp", "solo") for player in _GUITARSET_PLAYERS
)
_RUNTIME_AUDIO_SUFFIXES = frozenset({".aac", ".m4a", ".mp3", ".wav"})
_HEX = frozenset("0123456789abcdef")
_GROUP_DESCRIPTOR_TRACK_FIELDS = frozenset(
    {
        "trackId",
        "split",
        "datasetId",
        "role",
        "confidenceGroupId",
        "referencePath",
    }
)
_GROUP_DESCRIPTOR_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "sourceBindings",
        "expectedDatasetShape",
        "expectedCounts",
        "actualCounts",
        "runtimeAudioManifestSha256",
        "groupingAudit",
        "tracks",
        "trackSetSha256",
        "manifestSha256",
    }
)
_EXPECTED_COUNT_FIELDS = frozenset({"trackCount", "baseGroupCount", "confidenceGroupCount"})
_SOURCE_BINDING_FIELDS = frozenset(
    {
        "schemaVersion",
        "winnerCache",
        "audioLineage",
        "developmentSource",
        "expectedDatasetShape",
        "derivativeRegistry",
        "bindingsSha256",
    }
)
_FILE_SOURCE_FIELDS = frozenset({"schemaVersion", "fileSha256", "canonicalSha256", "semanticSha256"})
_DERIVATIVE_SOURCE_FIELDS = frozenset(
    {
        "schemaVersion",
        "origin",
        "fileSha256",
        "canonicalSha256",
        "registrySha256",
    }
)
_DERIVATIVE_REGISTRY_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "merges",
        "mergeSetSha256",
        "registrySha256",
    }
)
_DERIVATIVE_MERGE_FIELDS = frozenset({"schemaVersion", "confidenceGroupId", "baseGroupIds", "mergeSha256"})
_GROUPING_AUDIT_FIELDS = frozenset(
    {
        "schemaVersion",
        "policy",
        "trackCount",
        "baseGroupCount",
        "confidenceGroupCount",
        "datasetCounts",
        "baseGroups",
        "auditSha256",
    }
)
_DATASET_COUNT_FIELDS = frozenset({"datasetId", "trackCount", "baseGroupCount", "confidenceGroupCount"})
_EXPECTED_DATASET_SHAPE_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "trackCount",
        "baseGroupCount",
        "datasets",
        "datasetSetSha256",
        "shapeSha256",
    }
)
_EXPECTED_DATASET_ROW_FIELDS = frozenset(
    {
        "datasetId",
        "trackCount",
        "baseGroupCount",
        "baseGroupSizeHistogram",
        "rowSha256",
    }
)
_BASE_GROUP_SIZE_FIELDS = frozenset({"baseGroupSize", "baseGroupCount"})
_LABEL_DETERMINACY_COUNT_FIELDS = (
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
_DATASET_LABEL_AUDIT_FIELDS = frozenset(
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
_DATASET_LABEL_AUDIT_ROW_FIELDS = frozenset(
    {
        "datasetId",
        *_LABEL_DETERMINACY_COUNT_FIELDS,
        "rowSha256",
    }
)
_BASE_GROUP_FIELDS = frozenset(
    {
        "baseGroupId",
        "confidenceGroupId",
        "datasetId",
        "compositionId",
        "trackIds",
        "roles",
        "trackCount",
        "baseGroupSha256",
    }
)


class SelectorDevelopmentError(ValueError):
    """A development-only selector orchestration contract failed closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SelectorDevelopmentError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise SelectorDevelopmentError(f"{name} must be an array.")
    return value


def _exact_fields(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise SelectorDevelopmentError(f"{name} does not match the exact schema: missing={missing}, extra={extra}.")


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or "\x00" in value:
        raise SelectorDevelopmentError(f"{name} must be a trimmed, nonempty string without NUL bytes.")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise SelectorDevelopmentError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SelectorDevelopmentError(f"{name} must be a positive integer.")
    return value


def _nonnegative_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SelectorDevelopmentError(f"{name} must be a nonnegative integer.")
    return value


def _development(value: Any, name: str) -> None:
    if value != DEVELOPMENT_SPLIT:
        raise SelectorDevelopmentError(
            f"{name} must be development; calibration, test, heldout, confirmation, "
            "training, and every other split are forbidden before nested paths are read."
        )


def _unsigned(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _manifest_relative_absolute(raw: str, manifest_path: Path, name: str) -> Path:
    candidate = Path(raw)
    if ".." in candidate.parts:
        raise SelectorDevelopmentError(f"{name} may not contain parent traversal.")
    if not candidate.is_absolute():
        candidate = _absolute(manifest_path).parent / candidate
    return _absolute(candidate)


def _reject_symlink_components(path: Path, name: str) -> None:
    absolute = _absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        if current.is_symlink():
            raise SelectorDevelopmentError(f"{name} may not contain symlinked path components.")


def _read_json(path: Path, name: str) -> tuple[dict[str, Any], bytes]:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    if absolute.is_symlink() or not absolute.is_file():
        raise SelectorDevelopmentError(f"{name} must be an existing non-symlink JSON file.")
    try:
        raw = absolute.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SelectorDevelopmentError(f"Could not read {name} as JSON.") from error
    return dict(_mapping(value, name)), raw


def _render_json(value: Mapping[str, Any]) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _preflight_new_json(path: Path, name: str) -> Path:
    absolute = _absolute(path)
    if absolute.suffix.lower() != ".json":
        raise SelectorDevelopmentError(f"{name} must be a JSON file.")
    _reject_symlink_components(absolute.parent, name)
    if absolute.is_symlink() or absolute.exists():
        raise SelectorDevelopmentError(f"{name} must be a new, non-symlink path.")
    return absolute


def _directory_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _file_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)


def _identity(stat_result: os.stat_result) -> tuple[int, int]:
    return stat_result.st_dev, stat_result.st_ino


def _open_or_create_directory(path: Path, name: str) -> tuple[int, tuple[int, int]]:
    """Open an absolute directory by walking retained no-follow dirfds."""

    absolute = _absolute(path)
    descriptor = os.open(absolute.anchor, _directory_open_flags())
    try:
        for component in absolute.parts[1:]:
            if component in {"", ".", ".."}:
                raise SelectorDevelopmentError(f"{name} contains an invalid path component.")
            try:
                os.mkdir(component, mode=0o755, dir_fd=descriptor)
            except FileExistsError:
                pass
            try:
                next_descriptor = os.open(component, _directory_open_flags(), dir_fd=descriptor)
            except OSError as error:
                raise SelectorDevelopmentError(f"{name} contains a symlink or non-directory component.") from error
            os.close(descriptor)
            descriptor = next_descriptor
        inode = _identity(os.fstat(descriptor))
        _verify_directory_path(absolute, descriptor, inode, name)
        return descriptor, inode
    except Exception:
        os.close(descriptor)
        raise


def _open_existing_directory(path: Path, name: str) -> tuple[int, tuple[int, int]]:
    absolute = _absolute(path)
    _reject_symlink_components(absolute, name)
    try:
        descriptor = os.open(absolute, _directory_open_flags())
    except OSError as error:
        raise SelectorDevelopmentError(f"{name} must be an existing non-symlink directory.") from error
    inode = _identity(os.fstat(descriptor))
    try:
        _verify_directory_path(absolute, descriptor, inode, name)
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, inode


def _verify_directory_path(
    path: Path,
    descriptor: int,
    inode: tuple[int, int],
    name: str,
) -> None:
    try:
        path_stat = os.stat(_absolute(path), follow_symlinks=False)
    except OSError as error:
        raise SelectorDevelopmentError(f"{name} path changed during publication.") from error
    if _identity(os.fstat(descriptor)) != inode or _identity(path_stat) != inode:
        raise SelectorDevelopmentError(f"{name} path changed during publication.")


def _entry_stat(parent_descriptor: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _create_temporary_json(
    parent_descriptor: int,
    destination_name: str,
    rendered: bytes,
) -> tuple[str, tuple[int, int]]:
    for _attempt in range(128):
        temporary_name = f".{destination_name}.{secrets.token_hex(16)}.tmp"
        try:
            descriptor = os.open(
                temporary_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=parent_descriptor,
            )
        except FileExistsError:
            continue
        inode = _identity(os.fstat(descriptor))
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            _unlink_owned_entry(parent_descriptor, temporary_name, inode)
            raise
        return temporary_name, inode
    raise SelectorDevelopmentError("Could not reserve a private JSON temporary file.")


def _read_entry(parent_descriptor: int, name: str) -> bytes:
    try:
        descriptor = os.open(name, _file_open_flags(), dir_fd=parent_descriptor)
    except OSError as error:
        raise SelectorDevelopmentError("Could not reopen a published regular file.") from error
    try:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _unlink_owned_entry(
    parent_descriptor: int,
    name: str,
    inode: tuple[int, int],
) -> None:
    """Unlink only when a retained dirfd still names the inode we created."""

    try:
        descriptor = os.open(name, _file_open_flags(), dir_fd=parent_descriptor)
    except FileNotFoundError:
        return
    except OSError:
        return
    try:
        if _identity(os.fstat(descriptor)) == inode:
            os.unlink(name, dir_fd=parent_descriptor)
    finally:
        os.close(descriptor)


def _remove_owned_directory(
    parent_descriptor: int,
    name: str,
    inode: tuple[int, int],
) -> None:
    """Remove an empty directory only while it is still the inode we made."""

    try:
        descriptor = os.open(name, _directory_open_flags(), dir_fd=parent_descriptor)
    except OSError:
        return
    try:
        if _identity(os.fstat(descriptor)) == inode:
            try:
                os.rmdir(name, dir_fd=parent_descriptor)
            except OSError:
                pass
    finally:
        os.close(descriptor)


def _atomic_publish_json_set(outputs: Mapping[Path, Mapping[str, Any]]) -> None:
    """Publish one or more new JSON files, rolling back links on any failure."""

    if not outputs:
        raise SelectorDevelopmentError("At least one JSON output is required.")
    normalized: dict[Path, Mapping[str, Any]] = {}
    for raw_path, value in outputs.items():
        path = _preflight_new_json(raw_path, "JSON output")
        if path in normalized:
            raise SelectorDevelopmentError("JSON output paths must be unique.")
        normalized[path] = value
    parents: dict[Path, tuple[int, tuple[int, int]]] = {}
    temporary_entries: dict[Path, tuple[int, str, tuple[int, int], bytes]] = {}
    linked: list[tuple[int, str, tuple[int, int]]] = []
    try:
        for parent_path in sorted({path.parent for path in normalized}, key=str):
            parents[parent_path] = _open_or_create_directory(parent_path, "JSON output parent")
        for path, value in normalized.items():
            parent_descriptor = parents[path.parent][0]
            if _entry_stat(parent_descriptor, path.name) is not None:
                raise SelectorDevelopmentError("A JSON output appeared before publication.")
            rendered = _render_json(value).encode("utf-8")
            temporary_name, temporary_inode = _create_temporary_json(
                parent_descriptor,
                path.name,
                rendered,
            )
            temporary_entries[path] = (
                parent_descriptor,
                temporary_name,
                temporary_inode,
                rendered,
            )
        for path in sorted(normalized, key=lambda item: str(item)):
            parent_descriptor, temporary_name, temporary_inode, _rendered = temporary_entries[path]
            if _entry_stat(parent_descriptor, path.name) is not None:
                raise SelectorDevelopmentError("A JSON output appeared before publication.")
            try:
                os.link(
                    temporary_name,
                    path.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as error:
                raise SelectorDevelopmentError("A JSON output was concurrently created; refusing overwrite.") from error
            # Ownership bookkeeping is deliberately the first nontrivial
            # operation after link(2); the inode was captured before linking.
            linked.append((parent_descriptor, path.name, temporary_inode))
        for path in normalized:
            parent_descriptor, _temporary_name, _temporary_inode, rendered = temporary_entries[path]
            if _read_entry(parent_descriptor, path.name) != rendered:
                raise SelectorDevelopmentError("Published JSON did not round-trip exactly.")
        for parent_path, (descriptor, inode) in parents.items():
            os.fsync(descriptor)
            _verify_directory_path(parent_path, descriptor, inode, "JSON output parent")
    except Exception:
        for parent_descriptor, name, inode in reversed(linked):
            _unlink_owned_entry(parent_descriptor, name, inode)
        raise
    finally:
        for parent_descriptor, name, inode, _rendered in temporary_entries.values():
            _unlink_owned_entry(parent_descriptor, name, inode)
        for descriptor, _inode in parents.values():
            os.close(descriptor)


def explicit_empty_derivative_registry() -> dict[str, Any]:
    """Return the sealed, explicit declaration that no derivative merges exist."""

    payload: dict[str, Any] = {
        "schemaVersion": DERIVATIVE_REGISTRY_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "merges": [],
        "mergeSetSha256": canonical_sha256([]),
    }
    return {**payload, "registrySha256": canonical_sha256(payload)}


def build_expected_dataset_shape(
    dataset_base_group_sizes: Mapping[str, Sequence[int]],
) -> dict[str, Any]:
    """Seal caller-reviewed per-dataset track and base-group cardinalities."""

    if not dataset_base_group_sizes:
        raise SelectorDevelopmentError("Expected dataset shape must name at least one dataset.")
    datasets: list[dict[str, Any]] = []
    for raw_dataset_id in sorted(dataset_base_group_sizes):
        dataset_id = _string(raw_dataset_id, "expected dataset shape datasetId")
        if dataset_id not in _SUPPORTED_DATASETS:
            raise SelectorDevelopmentError("Expected dataset shape contains an unsupported dataset.")
        raw_sizes = dataset_base_group_sizes[raw_dataset_id]
        sizes = [
            _positive_integer(value, f"expected dataset shape {dataset_id!r} base-group size")
            for value in _sequence(raw_sizes, f"expected dataset shape {dataset_id!r} base-group sizes")
        ]
        if not sizes:
            raise SelectorDevelopmentError("Every expected dataset must contain at least one base group.")
        histogram_counts: dict[int, int] = defaultdict(int)
        for size in sizes:
            histogram_counts[size] += 1
        histogram = [
            {
                "baseGroupSize": size,
                "baseGroupCount": histogram_counts[size],
            }
            for size in sorted(histogram_counts)
        ]
        row_payload = {
            "datasetId": dataset_id,
            "trackCount": sum(sizes),
            "baseGroupCount": len(sizes),
            "baseGroupSizeHistogram": histogram,
        }
        datasets.append({**row_payload, "rowSha256": canonical_sha256(row_payload)})
    payload = {
        "schemaVersion": EXPECTED_DATASET_SHAPE_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "trackCount": sum(int(row["trackCount"]) for row in datasets),
        "baseGroupCount": sum(int(row["baseGroupCount"]) for row in datasets),
        "datasets": datasets,
        "datasetSetSha256": canonical_sha256(datasets),
    }
    return {**payload, "shapeSha256": canonical_sha256(payload)}


def freeze_reviewed_expected_dataset_shape(output_path: Path) -> dict[str, Any]:
    """Publish the one independently reviewed 246-track/169-group shape."""

    shape = build_expected_dataset_shape(dict(_REVIEWED_DATASET_BASE_GROUP_SIZES))
    _atomic_publish_json_set(
        {
            _preflight_new_json(output_path, "expected dataset shape output"): shape,
        }
    )
    return deepcopy(shape)


def _validate_expected_dataset_shape(value: Any) -> Mapping[str, Any]:
    shape = _mapping(value, "expected dataset shape")
    # Reject protected partitions before inspecting the nested dataset rows.
    _development(shape.get("split"), "expected dataset shape split")
    _exact_fields(shape, _EXPECTED_DATASET_SHAPE_FIELDS, "expected dataset shape")
    if shape.get("schemaVersion") != EXPECTED_DATASET_SHAPE_SCHEMA:
        raise SelectorDevelopmentError("Expected dataset-shape schema is unsupported.")
    if shape.get("developmentOnly") is not True or shape.get("promotionEligible") is not False:
        raise SelectorDevelopmentError("Expected dataset shape must remain development-only and non-promotable.")
    track_count = _positive_integer(shape.get("trackCount"), "expected dataset shape trackCount")
    base_group_count = _positive_integer(
        shape.get("baseGroupCount"),
        "expected dataset shape baseGroupCount",
    )
    raw_datasets = list(_sequence(shape.get("datasets"), "expected dataset shape datasets"))
    if not raw_datasets:
        raise SelectorDevelopmentError("Expected dataset shape must contain datasets.")
    datasets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_row in enumerate(raw_datasets):
        row = _mapping(raw_row, f"expected dataset shape datasets[{index}]")
        _exact_fields(row, _EXPECTED_DATASET_ROW_FIELDS, f"expected dataset shape datasets[{index}]")
        dataset_id = _string(row.get("datasetId"), "expected dataset shape datasetId")
        if dataset_id not in _SUPPORTED_DATASETS or dataset_id in seen:
            raise SelectorDevelopmentError("Expected dataset shape has an unsupported or duplicate dataset.")
        seen.add(dataset_id)
        row_track_count = _positive_integer(row.get("trackCount"), f"expected {dataset_id} trackCount")
        row_base_count = _positive_integer(
            row.get("baseGroupCount"),
            f"expected {dataset_id} baseGroupCount",
        )
        raw_histogram = list(
            _sequence(
                row.get("baseGroupSizeHistogram"),
                f"expected {dataset_id} baseGroupSizeHistogram",
            )
        )
        if not raw_histogram:
            raise SelectorDevelopmentError("Expected dataset shape needs a base-group-size histogram.")
        histogram: list[dict[str, int]] = []
        for histogram_index, raw_bucket in enumerate(raw_histogram):
            bucket = _mapping(raw_bucket, f"expected {dataset_id} histogram[{histogram_index}]")
            _exact_fields(bucket, _BASE_GROUP_SIZE_FIELDS, f"expected {dataset_id} histogram[{histogram_index}]")
            histogram.append(
                {
                    "baseGroupSize": _positive_integer(
                        bucket.get("baseGroupSize"),
                        f"expected {dataset_id} baseGroupSize",
                    ),
                    "baseGroupCount": _positive_integer(
                        bucket.get("baseGroupCount"),
                        f"expected {dataset_id} baseGroupCount bucket",
                    ),
                }
            )
        sizes = [bucket["baseGroupSize"] for bucket in histogram]
        if sizes != sorted(set(sizes)):
            raise SelectorDevelopmentError("Expected dataset-shape histogram sizes must be sorted and unique.")
        if sum(bucket["baseGroupCount"] for bucket in histogram) != row_base_count:
            raise SelectorDevelopmentError("Expected dataset-shape base-group count disagrees with its histogram.")
        if sum(bucket["baseGroupSize"] * bucket["baseGroupCount"] for bucket in histogram) != row_track_count:
            raise SelectorDevelopmentError("Expected dataset-shape track count disagrees with its histogram.")
        normalized = {
            "datasetId": dataset_id,
            "trackCount": row_track_count,
            "baseGroupCount": row_base_count,
            "baseGroupSizeHistogram": histogram,
            "rowSha256": _sha256(row.get("rowSha256"), f"expected {dataset_id} rowSha256"),
        }
        if normalized["rowSha256"] != canonical_sha256(_unsigned(normalized, "rowSha256")):
            raise SelectorDevelopmentError("Expected dataset-shape row hash is stale.")
        datasets.append(normalized)
    if datasets != sorted(datasets, key=lambda row: row["datasetId"]):
        raise SelectorDevelopmentError("Expected dataset-shape rows must be sorted by datasetId.")
    if sum(row["trackCount"] for row in datasets) != track_count:
        raise SelectorDevelopmentError("Expected dataset-shape total track count is stale.")
    if sum(row["baseGroupCount"] for row in datasets) != base_group_count:
        raise SelectorDevelopmentError("Expected dataset-shape total base-group count is stale.")
    if shape.get("datasetSetSha256") != canonical_sha256(datasets):
        raise SelectorDevelopmentError("Expected dataset-shape dataset-set hash is stale.")
    if shape.get("shapeSha256") != canonical_sha256(_unsigned(shape, "shapeSha256")):
        raise SelectorDevelopmentError("Expected dataset-shape self hash is stale.")
    return shape


def _validate_derivative_registry(
    value: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, Any]]:
    # Split rejection deliberately precedes nested merge inspection.
    _development(value.get("split"), "derivative registry split")
    _exact_fields(value, _DERIVATIVE_REGISTRY_FIELDS, "derivative registry")
    if value.get("schemaVersion") != DERIVATIVE_REGISTRY_SCHEMA:
        raise SelectorDevelopmentError("Derivative registry schema is unsupported.")
    if value.get("developmentOnly") is not True or value.get("promotionEligible") is not False:
        raise SelectorDevelopmentError("Derivative registry must remain development-only and non-promotable.")
    raw_merges = list(_sequence(value.get("merges"), "derivative registry merges"))
    merges: list[dict[str, Any]] = []
    base_to_confidence: dict[str, str] = {}
    confidence_ids: set[str] = set()
    for index, raw_merge in enumerate(raw_merges):
        merge = _mapping(raw_merge, f"derivative registry merges[{index}]")
        _exact_fields(merge, _DERIVATIVE_MERGE_FIELDS, f"derivative registry merges[{index}]")
        if merge.get("schemaVersion") != DERIVATIVE_MERGE_SCHEMA:
            raise SelectorDevelopmentError("Derivative merge schema is unsupported.")
        confidence_id = _string(
            merge.get("confidenceGroupId"),
            f"derivative registry merges[{index}].confidenceGroupId",
        )
        if not confidence_id.startswith("derivative:"):
            raise SelectorDevelopmentError("Derivative confidenceGroupId values must use the 'derivative:' namespace.")
        if confidence_id in confidence_ids:
            raise SelectorDevelopmentError("Derivative confidenceGroupId values must be unique.")
        confidence_ids.add(confidence_id)
        base_ids = [
            _string(item, f"derivative registry merges[{index}].baseGroupIds")
            for item in _sequence(
                merge.get("baseGroupIds"),
                f"derivative registry merges[{index}].baseGroupIds",
            )
        ]
        if len(base_ids) < 2 or base_ids != sorted(set(base_ids)):
            raise SelectorDevelopmentError("Every derivative merge must name at least two sorted, unique baseGroupIds.")
        if any(not item.startswith("composition:") for item in base_ids):
            raise SelectorDevelopmentError("Derivative merges may name only complete composition base groups.")
        unsigned = _unsigned(merge, "mergeSha256")
        if merge.get("mergeSha256") != canonical_sha256(unsigned):
            raise SelectorDevelopmentError("Derivative merge hash is stale.")
        for base_id in base_ids:
            if base_id in base_to_confidence:
                raise SelectorDevelopmentError(
                    "A base composition group may participate in at most one derivative merge."
                )
            base_to_confidence[base_id] = confidence_id
        merges.append(deepcopy(dict(merge)))
    if merges != sorted(merges, key=lambda item: str(item["confidenceGroupId"])):
        raise SelectorDevelopmentError("Derivative merges must be sorted by confidenceGroupId.")
    if value.get("mergeSetSha256") != canonical_sha256(merges):
        raise SelectorDevelopmentError("Derivative merge-set hash is stale.")
    if value.get("registrySha256") != canonical_sha256(_unsigned(value, "registrySha256")):
        raise SelectorDevelopmentError("Derivative registry self hash is stale.")
    return base_to_confidence, deepcopy(dict(value))


def build_derivative_registry(
    merges: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a canonical registry containing whole-base-group merges only."""

    rows: list[dict[str, Any]] = []
    for raw in merges:
        value = _mapping(raw, "derivative merge")
        if set(value) != {"confidenceGroupId", "baseGroupIds"}:
            raise SelectorDevelopmentError(
                "Derivative merge inputs require exactly confidenceGroupId and baseGroupIds."
            )
        payload = {
            "schemaVersion": DERIVATIVE_MERGE_SCHEMA,
            "confidenceGroupId": _string(value["confidenceGroupId"], "confidenceGroupId"),
            "baseGroupIds": sorted(
                _string(item, "baseGroupId") for item in _sequence(value["baseGroupIds"], "baseGroupIds")
            ),
        }
        rows.append({**payload, "mergeSha256": canonical_sha256(payload)})
    rows.sort(key=lambda item: str(item["confidenceGroupId"]))
    payload = {
        "schemaVersion": DERIVATIVE_REGISTRY_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "merges": rows,
        "mergeSetSha256": canonical_sha256(rows),
    }
    result = {**payload, "registrySha256": canonical_sha256(payload)}
    _validate_derivative_registry(result)
    return result


def _preflight_development_tracks(value: Mapping[str, Any], name: str, *, id_field: str) -> None:
    tracks = _sequence(value.get("tracks"), f"{name}.tracks")
    if not tracks:
        raise SelectorDevelopmentError(f"{name}.tracks must be nonempty.")
    seen: set[str] = set()
    for index, raw_track in enumerate(tracks):
        track = _mapping(raw_track, f"{name}.tracks[{index}]")
        _development(track.get("split"), f"{name}.tracks[{index}].split")
        identifier = _string(track.get(id_field), f"{name}.tracks[{index}].{id_field}")
        if identifier in seen:
            raise SelectorDevelopmentError(f"{name} contains duplicate track id {identifier!r}.")
        seen.add(identifier)


def _production_role(source: Mapping[str, Any], track_id: str) -> str:
    dataset_id = _string(source.get("datasetId"), f"source track {track_id!r} datasetId")
    if dataset_id not in _SUPPORTED_DATASETS:
        raise SelectorDevelopmentError(
            f"Source track {track_id!r} uses unsupported dataset {dataset_id!r}; no role fallback exists."
        )
    if dataset_id == "guitarset":
        identifier = _string(track_id, "GuitarSet track id")
        player = _string(source.get("groupId"), f"source track {track_id!r} groupId")
        composition_id = _string(
            source.get("compositionId"),
            f"source track {track_id!r} compositionId",
        )
        split_group = _string(
            source.get("splitGroup"),
            f"source track {track_id!r} splitGroup",
        )
        if player not in _GUITARSET_PLAYERS:
            raise SelectorDevelopmentError("GuitarSet groupId must be player 00..05.")
        if split_group != composition_id:
            raise SelectorDevelopmentError("GuitarSet splitGroup must exactly equal compositionId.")
        matching_performances = [
            performance
            for performance in ("comp", "solo")
            if identifier == f"guitarset-{player}_{composition_id}_{performance}"
        ]
        if len(matching_performances) != 1:
            raise SelectorDevelopmentError(
                "GuitarSet track id must exactly bind groupId, compositionId, and comp/solo role."
            )
        performance = matching_performances[0]
        if "performanceRole" in source and source.get("performanceRole") != performance:
            raise SelectorDevelopmentError(
                "GuitarSet performanceRole contradicts the role encoded by the exact track id."
            )
        return f"guitarset:{performance}:player-{player}"
    if dataset_id == "aam":
        return "aam:mix"
    if dataset_id == "nrgcp":
        return "nrgcp:mix"
    if dataset_id == "idmt_guitar":
        capture = _string(source.get("groupId"), f"source track {track_id!r} groupId")
        speed = _string(
            source.get("performanceSpeed"),
            f"source track {track_id!r} performanceSpeed",
        )
        if any(character in capture or character in speed for character in ";=\n\r"):
            raise SelectorDevelopmentError("IDMT capture and speed metadata contain reserved characters.")
        return f"idmt_guitar:capture={capture};speed={speed}"
    performer = _string(source.get("groupId"), f"source track {track_id!r} groupId")
    if any(character in performer for character in ";=\n\r"):
        raise SelectorDevelopmentError("Winterreise performer metadata contain reserved characters.")
    return f"winterreise:performer={performer}"


def _validate_output_role(dataset_id: str, role: str) -> None:
    if dataset_id == "guitarset":
        if role not in _GUITARSET_ROLES:
            raise SelectorDevelopmentError("Group descriptor has an invalid GuitarSet role.")
        return
    exact = {"aam": "aam:mix", "nrgcp": "nrgcp:mix"}.get(dataset_id)
    if exact is not None:
        if role != exact:
            raise SelectorDevelopmentError("Group descriptor has an invalid dataset audit role.")
        return
    if dataset_id == "idmt_guitar":
        prefix = "idmt_guitar:capture="
        separator = ";speed="
        if not role.startswith(prefix) or role.count(separator) != 1:
            raise SelectorDevelopmentError("Group descriptor has an invalid IDMT audit role.")
        capture, speed = role[len(prefix) :].split(separator, 1)
        if not capture or not speed or any(character in capture or character in speed for character in ";=\n\r"):
            raise SelectorDevelopmentError("Group descriptor has an invalid IDMT audit role.")
        return
    prefix = "winterreise:performer="
    performer = role.removeprefix(prefix)
    if not role.startswith(prefix) or not performer or any(character in performer for character in ";=\n\r"):
        raise SelectorDevelopmentError("Group descriptor has an invalid Winterreise audit role.")


def _semantic_file_binding(
    value: Mapping[str, Any],
    raw: bytes,
    *,
    semantic_sha256: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": _string(value.get("schemaVersion"), "source schemaVersion"),
        "fileSha256": _file_sha256(raw),
        "canonicalSha256": canonical_sha256(value),
        "semanticSha256": _sha256(semantic_sha256, "source semanticSha256"),
    }


def _lineage_binding_matches_inputs(
    lineage: Mapping[str, Any],
    *,
    winner: Mapping[str, Any],
    winner_raw: bytes,
    winner_path: Path,
    source: Mapping[str, Any],
    source_raw: bytes,
    source_path: Path,
) -> None:
    bindings = _mapping(lineage.get("manifestBindings"), "audio lineage manifestBindings")
    for name, value, raw, supplied_path in (
        ("winnerCacheManifest", winner, winner_raw, winner_path),
        ("developmentSourceManifest", source, source_raw, source_path),
    ):
        binding = _mapping(bindings.get(name), f"audio lineage {name}")
        absolute_path = str(_absolute(supplied_path))
        if (
            binding.get("path") != absolute_path
            or binding.get("pathSha256") != canonical_sha256(absolute_path)
            or binding.get("fileSha256") != _file_sha256(raw)
            or binding.get("canonicalSha256") != canonical_sha256(value)
        ):
            raise SelectorDevelopmentError(f"Audio lineage does not bind the exact supplied {name}.")


def _source_bindings(
    *,
    winner: Mapping[str, Any],
    winner_raw: bytes,
    lineage: Mapping[str, Any],
    lineage_raw: bytes,
    source: Mapping[str, Any],
    source_raw: bytes,
    expected_dataset_shape: Mapping[str, Any],
    expected_dataset_shape_raw: bytes,
    registry: Mapping[str, Any],
    registry_raw: bytes | None,
) -> dict[str, Any]:
    protocol = _mapping(winner.get("splitProtocol"), "winner splitProtocol")
    integrity = _mapping(winner.get("artifactIntegrity"), "winner artifactIntegrity")
    lineage_payload = _unsigned(lineage, "artifactSha256")
    registry_source = {
        "schemaVersion": registry["schemaVersion"],
        "origin": "file" if registry_raw is not None else "embedded-explicit-empty-v1",
        "fileSha256": _file_sha256(registry_raw) if registry_raw is not None else None,
        "canonicalSha256": canonical_sha256(registry),
        "registrySha256": registry["registrySha256"],
    }
    payload = {
        "schemaVersion": SOURCE_BINDINGS_SCHEMA,
        "winnerCache": _semantic_file_binding(
            winner,
            winner_raw,
            semantic_sha256=_sha256(
                protocol.get("outputManifestSha256"),
                "winner outputManifestSha256",
            ),
        ),
        "audioLineage": _semantic_file_binding(
            lineage,
            lineage_raw,
            semantic_sha256=_sha256(lineage.get("artifactSha256"), "lineage artifactSha256"),
        ),
        "developmentSource": _semantic_file_binding(
            source,
            source_raw,
            semantic_sha256=canonical_sha256(source),
        ),
        "expectedDatasetShape": _semantic_file_binding(
            expected_dataset_shape,
            expected_dataset_shape_raw,
            semantic_sha256=_sha256(
                expected_dataset_shape.get("shapeSha256"),
                "expected dataset shape shapeSha256",
            ),
        ),
        "derivativeRegistry": registry_source,
    }
    if integrity.get("artifactSetSha256") is None or canonical_sha256(lineage_payload) != lineage.get("artifactSha256"):
        raise SelectorDevelopmentError("Winner or audio-lineage semantic seal is absent.")
    return {**payload, "bindingsSha256": canonical_sha256(payload)}


def _validate_source_bindings(value: Any) -> Mapping[str, Any]:
    binding = _mapping(value, "sourceBindings")
    _exact_fields(binding, _SOURCE_BINDING_FIELDS, "sourceBindings")
    if binding.get("schemaVersion") != SOURCE_BINDINGS_SCHEMA:
        raise SelectorDevelopmentError("Source-binding schema is unsupported.")
    for name in ("winnerCache", "audioLineage", "developmentSource", "expectedDatasetShape"):
        row = _mapping(binding.get(name), f"sourceBindings.{name}")
        _exact_fields(row, _FILE_SOURCE_FIELDS, f"sourceBindings.{name}")
        _string(row.get("schemaVersion"), f"sourceBindings.{name}.schemaVersion")
        for field in ("fileSha256", "canonicalSha256", "semanticSha256"):
            _sha256(row.get(field), f"sourceBindings.{name}.{field}")
    derivative = _mapping(binding.get("derivativeRegistry"), "sourceBindings.derivativeRegistry")
    _exact_fields(derivative, _DERIVATIVE_SOURCE_FIELDS, "sourceBindings.derivativeRegistry")
    if derivative.get("schemaVersion") != DERIVATIVE_REGISTRY_SCHEMA:
        raise SelectorDevelopmentError("Derivative source-binding schema is unsupported.")
    if derivative.get("origin") not in {"file", "embedded-explicit-empty-v1"}:
        raise SelectorDevelopmentError("Derivative source-binding origin is unsupported.")
    if derivative.get("origin") == "file":
        _sha256(derivative.get("fileSha256"), "derivativeRegistry.fileSha256")
    elif derivative.get("fileSha256") is not None:
        raise SelectorDevelopmentError("Embedded derivative registry may not claim file bytes.")
    for field in ("canonicalSha256", "registrySha256"):
        _sha256(derivative.get(field), f"derivativeRegistry.{field}")
    if binding.get("bindingsSha256") != canonical_sha256(_unsigned(binding, "bindingsSha256")):
        raise SelectorDevelopmentError("Source-binding self hash is stale.")
    return binding


def _grouping_audit(
    rows: Sequence[Mapping[str, str]],
    base_metadata: Mapping[str, tuple[str, str]],
) -> dict[str, Any]:
    by_base: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        by_base[row["baseGroupId"]].append(row)
    base_rows: list[dict[str, Any]] = []
    for base_id in sorted(by_base):
        tracks = sorted(by_base[base_id], key=lambda item: item["trackId"])
        dataset_id, composition_id = base_metadata[base_id]
        roles = sorted(str(item["role"]) for item in tracks)
        if len(roles) != len(set(roles)):
            raise SelectorDevelopmentError(f"Base group {base_id!r} contains duplicate audit roles.")
        if dataset_id == "guitarset" and set(roles) != _GUITARSET_ROLES:
            missing = sorted(_GUITARSET_ROLES - set(roles))
            extra = sorted(set(roles) - _GUITARSET_ROLES)
            raise SelectorDevelopmentError(
                f"GuitarSet base group {base_id!r} must contain exactly comp/solo for "
                f"players 00..05: missing={missing}, extra={extra}."
            )
        payload = {
            "baseGroupId": base_id,
            "confidenceGroupId": str(tracks[0]["confidenceGroupId"]),
            "datasetId": dataset_id,
            "compositionId": composition_id,
            "trackIds": [str(item["trackId"]) for item in tracks],
            "roles": roles,
            "trackCount": len(tracks),
        }
        if any(item["confidenceGroupId"] != payload["confidenceGroupId"] for item in tracks):
            raise SelectorDevelopmentError(
                f"Derivative mapping split base group {base_id!r}; whole-group merges are required."
            )
        base_rows.append({**payload, "baseGroupSha256": canonical_sha256(payload)})

    datasets = sorted({str(row["datasetId"]) for row in rows})
    dataset_counts: list[dict[str, Any]] = []
    for dataset_id in datasets:
        selected = [row for row in rows if row["datasetId"] == dataset_id]
        dataset_counts.append(
            {
                "datasetId": dataset_id,
                "trackCount": len(selected),
                "baseGroupCount": len({row["baseGroupId"] for row in selected}),
                "confidenceGroupCount": len({row["confidenceGroupId"] for row in selected}),
            }
        )
    payload = {
        "schemaVersion": GROUPING_AUDIT_SCHEMA,
        "policy": (
            "composition:<datasetId>:<compositionId>; exact dataset audit roles; "
            "explicit whole-base-group derivative merges only-v1"
        ),
        "trackCount": len(rows),
        "baseGroupCount": len(base_rows),
        "confidenceGroupCount": len({row["confidenceGroupId"] for row in rows}),
        "datasetCounts": dataset_counts,
        "baseGroups": base_rows,
    }
    return {**payload, "auditSha256": canonical_sha256(payload)}


def _dataset_shape_from_grouping_audit(audit: Mapping[str, Any]) -> dict[str, Any]:
    sizes: dict[str, list[int]] = defaultdict(list)
    for raw_row in _sequence(audit.get("baseGroups"), "grouping audit baseGroups"):
        row = _mapping(raw_row, "grouping audit base group")
        dataset_id = _string(row.get("datasetId"), "grouping audit base-group datasetId")
        sizes[dataset_id].append(_positive_integer(row.get("trackCount"), "grouping audit base-group trackCount"))
    return build_expected_dataset_shape(sizes)


def _validate_grouping_audit(
    value: Any,
    tracks: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    audit = _mapping(value, "groupingAudit")
    _exact_fields(audit, _GROUPING_AUDIT_FIELDS, "groupingAudit")
    if audit.get("schemaVersion") != GROUPING_AUDIT_SCHEMA:
        raise SelectorDevelopmentError("Grouping-audit schema is unsupported.")
    _string(audit.get("policy"), "groupingAudit.policy")
    for field in ("trackCount", "baseGroupCount", "confidenceGroupCount"):
        _positive_integer(audit.get(field), f"groupingAudit.{field}")
    dataset_rows = list(_sequence(audit.get("datasetCounts"), "groupingAudit.datasetCounts"))
    if not dataset_rows:
        raise SelectorDevelopmentError("Grouping audit needs dataset counts.")
    normalized_datasets: list[dict[str, Any]] = []
    for index, raw in enumerate(dataset_rows):
        row = _mapping(raw, f"groupingAudit.datasetCounts[{index}]")
        _exact_fields(row, _DATASET_COUNT_FIELDS, f"groupingAudit.datasetCounts[{index}]")
        dataset_id = _string(row.get("datasetId"), "dataset count datasetId")
        if dataset_id not in _SUPPORTED_DATASETS:
            raise SelectorDevelopmentError("Grouping audit contains an unsupported dataset.")
        normalized_datasets.append(dict(row))
    if normalized_datasets != sorted(normalized_datasets, key=lambda row: row["datasetId"]):
        raise SelectorDevelopmentError("Grouping-audit dataset counts must be sorted.")
    base_rows = list(_sequence(audit.get("baseGroups"), "groupingAudit.baseGroups"))
    if not base_rows:
        raise SelectorDevelopmentError("Grouping audit needs base groups.")
    seen_bases: set[str] = set()
    audited_track_ids: list[str] = []
    track_by_id = {str(track["trackId"]): track for track in tracks}
    for index, raw in enumerate(base_rows):
        row = _mapping(raw, f"groupingAudit.baseGroups[{index}]")
        _exact_fields(row, _BASE_GROUP_FIELDS, f"groupingAudit.baseGroups[{index}]")
        base_id = _string(row.get("baseGroupId"), "baseGroupId")
        if base_id in seen_bases or not base_id.startswith("composition:"):
            raise SelectorDevelopmentError("Grouping-audit base groups are invalid or duplicated.")
        seen_bases.add(base_id)
        if row.get("baseGroupSha256") != canonical_sha256(_unsigned(row, "baseGroupSha256")):
            raise SelectorDevelopmentError("Grouping-audit base-group hash is stale.")
        track_ids = [_string(item, "base group trackId") for item in _sequence(row.get("trackIds"), "trackIds")]
        roles = [_string(item, "base group role") for item in _sequence(row.get("roles"), "roles")]
        if track_ids != sorted(set(track_ids)) or roles != sorted(set(roles)):
            raise SelectorDevelopmentError("Grouping-audit track ids and roles must be sorted and unique.")
        if row.get("trackCount") != len(track_ids):
            raise SelectorDevelopmentError("Grouping-audit base-group track count is stale.")
        dataset_id = _string(row.get("datasetId"), "base group datasetId")
        composition_id = _string(row.get("compositionId"), "base group compositionId")
        confidence_group_id = _string(
            row.get("confidenceGroupId"),
            "base group confidenceGroupId",
        )
        if base_id != f"composition:{dataset_id}:{composition_id}":
            raise SelectorDevelopmentError("Grouping-audit base-group identity is stale.")
        selected_tracks = [track_by_id.get(track_id) for track_id in track_ids]
        if any(track is None for track in selected_tracks):
            raise SelectorDevelopmentError("Grouping audit names an unknown descriptor track.")
        if any(
            track.get("datasetId") != dataset_id or track.get("confidenceGroupId") != confidence_group_id
            for track in selected_tracks
            if track is not None
        ):
            raise SelectorDevelopmentError("Grouping audit disagrees with descriptor grouping metadata.")
        if roles != sorted(str(track["role"]) for track in selected_tracks if track is not None):
            raise SelectorDevelopmentError("Grouping audit disagrees with descriptor audit roles.")
        if dataset_id == "guitarset" and set(roles) != _GUITARSET_ROLES:
            raise SelectorDevelopmentError("Grouping audit has an incomplete GuitarSet composition.")
        audited_track_ids.extend(track_ids)
    if [row["baseGroupId"] for row in base_rows] != sorted(seen_bases):
        raise SelectorDevelopmentError("Grouping-audit base groups must be sorted.")
    bases_by_confidence: dict[str, list[str]] = defaultdict(list)
    for row in base_rows:
        bases_by_confidence[str(row["confidenceGroupId"])].append(str(row["baseGroupId"]))
    for confidence_group_id, base_ids in bases_by_confidence.items():
        if confidence_group_id.startswith("composition:"):
            if base_ids != [confidence_group_id]:
                raise SelectorDevelopmentError("An unmerged confidence group must equal its one complete base group.")
        elif not confidence_group_id.startswith("derivative:") or len(base_ids) < 2:
            raise SelectorDevelopmentError("Derivative confidence groups must merge at least two complete base groups.")
    track_ids = sorted(str(track["trackId"]) for track in tracks)
    if sorted(audited_track_ids) != track_ids:
        raise SelectorDevelopmentError("Grouping audit does not cover the exact descriptor tracks.")
    if audit.get("trackCount") != len(tracks):
        raise SelectorDevelopmentError("Grouping-audit track count is stale.")
    if audit.get("baseGroupCount") != len(base_rows):
        raise SelectorDevelopmentError("Grouping-audit base-group count is stale.")
    if audit.get("confidenceGroupCount") != len({str(track["confidenceGroupId"]) for track in tracks}):
        raise SelectorDevelopmentError("Grouping-audit confidence-group count is stale.")
    derived_dataset_counts: list[dict[str, Any]] = []
    for dataset_id in sorted({str(track["datasetId"]) for track in tracks}):
        selected = [track for track in tracks if track["datasetId"] == dataset_id]
        selected_ids = {str(track["trackId"]) for track in selected}
        selected_bases = [row for row in base_rows if any(track_id in selected_ids for track_id in row["trackIds"])]
        derived_dataset_counts.append(
            {
                "datasetId": dataset_id,
                "trackCount": len(selected),
                "baseGroupCount": len(selected_bases),
                "confidenceGroupCount": len({str(track["confidenceGroupId"]) for track in selected}),
            }
        )
    if normalized_datasets != derived_dataset_counts:
        raise SelectorDevelopmentError("Grouping-audit dataset counts are stale.")
    if audit.get("auditSha256") != canonical_sha256(_unsigned(audit, "auditSha256")):
        raise SelectorDevelopmentError("Grouping-audit self hash is stale.")
    return audit


def validate_development_group_descriptor(
    manifest: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate a sanitized prepared-input descriptor without opening references."""

    value = _mapping(manifest, "group descriptor manifest")
    _development(value.get("split"), "group descriptor split")
    raw_tracks = list(_sequence(value.get("tracks"), "group descriptor tracks"))
    _preflight_development_tracks(value, "group descriptor", id_field="trackId")
    _exact_fields(value, _GROUP_DESCRIPTOR_FIELDS, "group descriptor manifest")
    if value.get("schemaVersion") != DEVELOPMENT_INPUTS_SCHEMA:
        raise SelectorDevelopmentError("Group descriptor schema is unsupported.")
    if value.get("developmentOnly") is not True or value.get("promotionEligible") is not False:
        raise SelectorDevelopmentError("Group descriptor must remain development-only and non-promotable.")
    source_bindings = _validate_source_bindings(value.get("sourceBindings"))
    expected_shape = _validate_expected_dataset_shape(value.get("expectedDatasetShape"))
    expected_shape_binding = _mapping(
        source_bindings.get("expectedDatasetShape"),
        "sourceBindings.expectedDatasetShape",
    )
    if expected_shape_binding.get("canonicalSha256") != canonical_sha256(expected_shape) or expected_shape_binding.get(
        "semanticSha256"
    ) != expected_shape.get("shapeSha256"):
        raise SelectorDevelopmentError("Expected dataset shape disagrees with its sealed source binding.")
    expected = _mapping(value.get("expectedCounts"), "expectedCounts")
    actual = _mapping(value.get("actualCounts"), "actualCounts")
    _exact_fields(expected, _EXPECTED_COUNT_FIELDS, "expectedCounts")
    _exact_fields(actual, _EXPECTED_COUNT_FIELDS, "actualCounts")
    for name, counts in (("expectedCounts", expected), ("actualCounts", actual)):
        for field in _EXPECTED_COUNT_FIELDS:
            _positive_integer(counts.get(field), f"{name}.{field}")
    if dict(expected) != dict(actual):
        raise SelectorDevelopmentError("Prepared inputs do not match caller-frozen expected counts.")
    if expected.get("trackCount") != expected_shape.get("trackCount") or expected.get(
        "baseGroupCount"
    ) != expected_shape.get("baseGroupCount"):
        raise SelectorDevelopmentError("Caller-frozen counts disagree with the expected dataset shape.")
    _sha256(value.get("runtimeAudioManifestSha256"), "runtimeAudioManifestSha256")
    tracks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_tracks):
        track = _mapping(raw, f"group descriptor tracks[{index}]")
        _exact_fields(track, _GROUP_DESCRIPTOR_TRACK_FIELDS, f"group descriptor tracks[{index}]")
        track_id = _string(track.get("trackId"), f"group descriptor tracks[{index}].trackId")
        if track_id in seen:
            raise SelectorDevelopmentError("Group descriptor track ids must be unique.")
        seen.add(track_id)
        dataset_id = _string(track.get("datasetId"), f"group descriptor track {track_id!r} datasetId")
        if dataset_id not in _SUPPORTED_DATASETS:
            raise SelectorDevelopmentError("Group descriptor contains an unsupported dataset.")
        role = _string(track.get("role"), f"group descriptor track {track_id!r} role")
        _validate_output_role(dataset_id, role)
        _string(track.get("confidenceGroupId"), "confidenceGroupId")
        _string(track.get("referencePath"), "referencePath")
        tracks.append(dict(track))
    if [track["trackId"] for track in tracks] != sorted(seen):
        raise SelectorDevelopmentError("Group descriptor tracks must be sorted by trackId.")
    if value.get("trackSetSha256") != canonical_sha256(tracks):
        raise SelectorDevelopmentError("Group descriptor track-set hash is stale.")
    grouping_audit = _validate_grouping_audit(value.get("groupingAudit"), tracks)
    if _dataset_shape_from_grouping_audit(grouping_audit) != expected_shape:
        raise SelectorDevelopmentError("Prepared inputs do not match the caller-frozen per-dataset shape.")
    derived_counts = {
        "trackCount": len(tracks),
        "baseGroupCount": int(value["groupingAudit"]["baseGroupCount"]),
        "confidenceGroupCount": len({track["confidenceGroupId"] for track in tracks}),
    }
    if dict(actual) != derived_counts:
        raise SelectorDevelopmentError("Prepared-input actual counts are stale.")
    if value.get("manifestSha256") != canonical_sha256(_unsigned(value, "manifestSha256")):
        raise SelectorDevelopmentError("Group descriptor self hash is stale.")
    return manifest


def attest_development_lineage(
    winner_cache_manifest_path: Path,
    development_source_manifest_path: Path,
    dasheng_cache_manifest_path: Path,
    lineage_output_path: Path,
    projection_output_path: Path,
) -> dict[str, Any]:
    """Build one full production lineage and publish it with its projection."""

    lineage_output = _preflight_new_json(lineage_output_path, "audio lineage output")
    projection_output = _preflight_new_json(projection_output_path, "audio-lineage projection output")
    if lineage_output == projection_output:
        raise SelectorDevelopmentError("Lineage and projection outputs must be distinct.")
    with tempfile.TemporaryDirectory(prefix="chord-lineage-attestation-") as temporary_root:
        staging = Path(temporary_root) / "lineage.json"
        lineage = build_development_audio_lineage(
            winner_cache_manifest_path,
            development_source_manifest_path,
            dasheng_cache_manifest_path,
            staging,
        )
        validate_development_audio_lineage(lineage, verify_files=False)
        projection = project_development_audio_lineage(lineage)
        _atomic_publish_json_set(
            {
                lineage_output: lineage,
                projection_output: projection,
            }
        )
    return {
        "lineage": deepcopy(lineage),
        "projection": deepcopy(projection),
    }


def prepare_development_inputs(
    winner_cache_manifest_path: Path,
    audio_lineage_manifest_path: Path,
    development_source_manifest_path: Path,
    runtime_audio_output_path: Path,
    group_descriptor_output_path: Path,
    *,
    expected_track_count: int,
    expected_base_group_count: int,
    expected_confidence_group_count: int,
    expected_dataset_shape_path: Path,
    derivative_registry_path: Path | None = None,
    require_reviewed_dataset_shape: bool = False,
) -> dict[str, Any]:
    """Prepare exact runtime-audio and grouping inputs for the development set."""

    expected_counts = {
        "trackCount": _positive_integer(expected_track_count, "expected_track_count"),
        "baseGroupCount": _positive_integer(expected_base_group_count, "expected_base_group_count"),
        "confidenceGroupCount": _positive_integer(expected_confidence_group_count, "expected_confidence_group_count"),
    }
    runtime_output = _preflight_new_json(runtime_audio_output_path, "runtime audio output")
    descriptor_output = _preflight_new_json(
        group_descriptor_output_path,
        "group descriptor output",
    )
    if runtime_output == descriptor_output:
        raise SelectorDevelopmentError("Prepared output paths must be distinct.")

    winner, winner_raw = _read_json(winner_cache_manifest_path, "winner cache manifest")
    lineage, lineage_raw = _read_json(audio_lineage_manifest_path, "audio lineage manifest")
    source, source_raw = _read_json(
        development_source_manifest_path,
        "development source manifest",
    )
    expected_shape, expected_shape_raw = _read_json(
        expected_dataset_shape_path,
        "expected dataset shape",
    )
    if derivative_registry_path is None:
        registry = explicit_empty_derivative_registry()
        registry_raw = None
    else:
        registry, registry_raw = _read_json(
            derivative_registry_path,
            "derivative registry",
        )

    # All protected split gates precede validation that could ever be upgraded
    # to touch bound audio, cache, prediction, timing, or reference paths.
    if lineage.get("schemaVersion") != AUDIO_LINEAGE_SCHEMA:
        raise SelectorDevelopmentError("A full audio-lineage artifact is required, not a projection.")
    _development(lineage.get("split"), "audio lineage split")
    _development(expected_shape.get("split"), "expected dataset shape split")
    _preflight_development_tracks(lineage, "audio lineage", id_field="trackId")
    if source.get("schemaVersion") != DATASET_DESCRIPTOR_SCHEMA:
        raise SelectorDevelopmentError("Development source descriptor schema is unsupported.")
    _preflight_development_tracks(source, "development source", id_field="id")
    validated_expected_shape = _validate_expected_dataset_shape(expected_shape)
    if require_reviewed_dataset_shape and validated_expected_shape != build_expected_dataset_shape(
        dict(_REVIEWED_DATASET_BASE_GROUP_SIZES)
    ):
        raise SelectorDevelopmentError(
            "CLI preparation requires the exact independently reviewed 246-track/169-group dataset shape."
        )
    _validate_derivative_registry(registry)
    if (
        validated_expected_shape.get("trackCount") != expected_counts["trackCount"]
        or validated_expected_shape.get("baseGroupCount") != expected_counts["baseGroupCount"]
    ):
        raise SelectorDevelopmentError("Caller-frozen counts disagree with the supplied expected dataset shape.")

    try:
        validate_split_protocol_manifest(winner)
        validate_factorized_artifact_manifest(winner, verify_files=False)
        validate_development_audio_lineage(lineage, verify_files=False)
    except (TypeError, ValueError) as error:
        raise SelectorDevelopmentError("A sealed development input failed validation.") from error
    extractor = _mapping(lineage.get("extractorContract"), "audio lineage extractorContract")
    if extractor.get("entrypoint") != PRODUCTION_EXTRACTOR_ENTRYPOINT:
        raise SelectorDevelopmentError("Prepared inputs require lineage from the production feature extractor.")
    if lineage.get("developmentOnly") is not True or lineage.get("promotionEligible") is not False:
        raise SelectorDevelopmentError("Audio lineage is not development-only and non-promotable.")
    _lineage_binding_matches_inputs(
        lineage,
        winner=winner,
        winner_raw=winner_raw,
        winner_path=winner_cache_manifest_path,
        source=source,
        source_raw=source_raw,
        source_path=development_source_manifest_path,
    )

    winner_tracks = list(_sequence(winner.get("tracks"), "winner tracks"))
    development_winner: dict[str, Mapping[str, Any]] = {}
    for index, raw_track in enumerate(winner_tracks):
        track = _mapping(raw_track, f"winner tracks[{index}]")
        if track.get("split") != DEVELOPMENT_SPLIT:
            continue
        identifier = _string(track.get("id"), f"winner tracks[{index}].id")
        if identifier in development_winner:
            raise SelectorDevelopmentError("Winner development track ids must be unique.")
        development_winner[identifier] = track
    if not development_winner:
        raise SelectorDevelopmentError("Winner has no development tracks.")
    source_by_id = {str(track["id"]): _mapping(track, "development source track") for track in source["tracks"]}
    lineage_by_id = {str(track["trackId"]): _mapping(track, "audio lineage track") for track in lineage["tracks"]}
    exact_ids = set(development_winner)
    if set(source_by_id) != exact_ids or set(lineage_by_id) != exact_ids:
        raise SelectorDevelopmentError(
            "Winner, full audio lineage, and development source must bind the exact same track ids."
        )
    if len(exact_ids) != expected_counts["trackCount"]:
        raise SelectorDevelopmentError("Winner development track count does not match the caller-frozen expectation.")

    base_to_confidence, validated_registry = _validate_derivative_registry(registry)
    rows_with_base: list[dict[str, str]] = []
    base_metadata: dict[str, tuple[str, str]] = {}
    runtime_tracks: list[dict[str, str]] = []
    for track_id in sorted(exact_ids):
        winner_track = development_winner[track_id]
        source_track = source_by_id[track_id]
        lineage_track = lineage_by_id[track_id]
        dataset_id = _string(source_track.get("datasetId"), f"source track {track_id!r} datasetId")
        if winner_track.get("datasetId") != dataset_id or lineage_track.get("datasetId") != dataset_id:
            raise SelectorDevelopmentError(f"Dataset identity differs for track {track_id!r}.")
        composition_id = _string(
            source_track.get("compositionId"),
            f"source track {track_id!r} compositionId",
        )
        if winner_track.get("compositionId") != composition_id:
            raise SelectorDevelopmentError(f"Composition identity differs for track {track_id!r}.")
        raw_audio_path = _string(source_track.get("audioPath"), f"source track {track_id!r} audioPath")
        audio_path = _manifest_relative_absolute(
            raw_audio_path,
            development_source_manifest_path,
            f"source track {track_id!r} audioPath",
        )
        if audio_path.suffix.lower() not in _RUNTIME_AUDIO_SUFFIXES:
            raise SelectorDevelopmentError(
                f"Source audio for track {track_id!r} is not supported by the target runtime."
            )
        if str(audio_path) != lineage_track.get("audioPath"):
            raise SelectorDevelopmentError(f"Source audio path differs from lineage for track {track_id!r}.")
        raw_reference_path = _string(
            source_track.get("referencePath"),
            f"source track {track_id!r} referencePath",
        )
        reference_path = _manifest_relative_absolute(
            raw_reference_path,
            development_source_manifest_path,
            f"source track {track_id!r} referencePath",
        )
        if reference_path.suffix.lower() != ".json":
            raise SelectorDevelopmentError(f"Source reference for track {track_id!r} must be a JSON file.")
        role = _production_role(source_track, track_id)
        base_group_id = f"composition:{dataset_id}:{composition_id}"
        if base_group_id in base_to_confidence:
            confidence_group_id = base_to_confidence[base_group_id]
        else:
            confidence_group_id = base_group_id
        previous_metadata = base_metadata.setdefault(
            base_group_id,
            (dataset_id, composition_id),
        )
        if previous_metadata != (dataset_id, composition_id):
            raise SelectorDevelopmentError("A base group contains inconsistent composition metadata.")
        rows_with_base.append(
            {
                "trackId": track_id,
                "split": DEVELOPMENT_SPLIT,
                "datasetId": dataset_id,
                "role": role,
                "confidenceGroupId": confidence_group_id,
                "referencePath": str(reference_path),
                "baseGroupId": base_group_id,
            }
        )
        runtime_tracks.append(
            {
                "id": track_id,
                "split": DEVELOPMENT_SPLIT,
                "audioPath": str(audio_path),
            }
        )
    unknown_derivative_groups = sorted(set(base_to_confidence) - set(base_metadata))
    if unknown_derivative_groups:
        raise SelectorDevelopmentError(
            f"Derivative registry names base groups outside the exact development set: {unknown_derivative_groups}."
        )
    grouping_audit = _grouping_audit(rows_with_base, base_metadata)
    if _dataset_shape_from_grouping_audit(grouping_audit) != validated_expected_shape:
        raise SelectorDevelopmentError("Prepared inputs do not match the caller-frozen per-dataset shape.")
    actual_counts = {
        "trackCount": len(rows_with_base),
        "baseGroupCount": grouping_audit["baseGroupCount"],
        "confidenceGroupCount": grouping_audit["confidenceGroupCount"],
    }
    if actual_counts != expected_counts:
        raise SelectorDevelopmentError(
            f"Prepared counts {actual_counts} do not match caller-frozen counts {expected_counts}."
        )

    runtime_manifest = {
        "schemaVersion": INPUT_MANIFEST_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "tracks": runtime_tracks,
    }
    sanitized_tracks = [{key: row[key] for key in _GROUP_DESCRIPTOR_TRACK_FIELDS} for row in rows_with_base]
    sanitized_tracks.sort(key=lambda row: row["trackId"])
    bindings = _source_bindings(
        winner=winner,
        winner_raw=winner_raw,
        lineage=lineage,
        lineage_raw=lineage_raw,
        source=source,
        source_raw=source_raw,
        expected_dataset_shape=validated_expected_shape,
        expected_dataset_shape_raw=expected_shape_raw,
        registry=validated_registry,
        registry_raw=registry_raw,
    )
    descriptor_payload = {
        "schemaVersion": DEVELOPMENT_INPUTS_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "sourceBindings": bindings,
        "expectedDatasetShape": deepcopy(validated_expected_shape),
        "expectedCounts": expected_counts,
        "actualCounts": actual_counts,
        "runtimeAudioManifestSha256": canonical_sha256(runtime_manifest),
        "groupingAudit": grouping_audit,
        "tracks": sanitized_tracks,
        "trackSetSha256": canonical_sha256(sanitized_tracks),
    }
    descriptor = {
        **descriptor_payload,
        "manifestSha256": canonical_sha256(descriptor_payload),
    }
    validate_development_group_descriptor(descriptor)
    _atomic_publish_json_set(
        {
            runtime_output: runtime_manifest,
            descriptor_output: descriptor,
        }
    )
    return {
        "runtimeAudioManifest": deepcopy(runtime_manifest),
        "groupDescriptorManifest": deepcopy(descriptor),
    }


def build_development_groups(
    group_descriptor_manifest: Mapping[str, Any],
    *,
    reference_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Hash references and publish the exact group manifest for example building."""

    value = _mapping(group_descriptor_manifest, "group descriptor manifest")
    _development(value.get("split"), "group descriptor split")
    _preflight_development_tracks(value, "group descriptor", id_field="trackId")
    validate_development_group_descriptor(value)
    output = _preflight_new_json(output_path, "group manifest output")
    manifest = build_bar_selector_group_manifest(
        [dict(_mapping(track, "group descriptor track")) for track in value["tracks"]],
        reference_root=reference_root,
    )
    if manifest.get("schemaVersion") != GROUP_MANIFEST_SCHEMA:
        raise SelectorDevelopmentError("Group builder returned an unsupported schema.")
    expected = _mapping(value["expectedCounts"], "expectedCounts")
    tracks = list(_sequence(manifest.get("tracks"), "group manifest tracks"))
    if (
        len(tracks) != expected["trackCount"]
        or len({str(track["confidenceGroupId"]) for track in tracks}) != expected["confidenceGroupCount"]
    ):
        raise SelectorDevelopmentError("Built group manifest changed the frozen counts.")
    _atomic_publish_json_set({output: manifest})
    return deepcopy(manifest)


def _preflight_new_directory(path: Path, name: str) -> Path:
    absolute = _absolute(path)
    _reject_symlink_components(absolute.parent, name)
    if absolute.is_symlink() or absolute.exists():
        raise SelectorDevelopmentError(f"{name} must be a new, non-symlink path.")
    return absolute


def _require_disjoint_summary_root(
    output: Path,
    roots: Sequence[tuple[str, Path]],
) -> None:
    candidate = output.resolve(strict=False)
    for name, raw in roots:
        try:
            root = raw.resolve(strict=True)
        except OSError as error:
            raise SelectorDevelopmentError(f"{name} must resolve to an existing directory.") from error
        if not root.is_dir():
            raise SelectorDevelopmentError(f"{name} must resolve to an existing directory.")
        if candidate == root or candidate.is_relative_to(root) or root.is_relative_to(candidate):
            raise SelectorDevelopmentError(f"Summary output must be path-disjoint from {name}.")


def _publish_json_and_summary_set(
    artifact_path: Path,
    artifact: Mapping[str, Any],
    staging_summary_root: Path,
    summary_output_root: Path,
) -> None:
    """Publish a new summary directory and its only referencing JSON together."""

    artifact_output = _preflight_new_json(artifact_path, "selector examples output")
    summary_output = _preflight_new_directory(summary_output_root, "summary output root")
    if (
        artifact_output == summary_output
        or artifact_output.is_relative_to(summary_output)
        or summary_output.is_relative_to(artifact_output)
    ):
        raise SelectorDevelopmentError("Examples JSON and summary output root must be path-disjoint.")
    staging_descriptor, staging_inode = _open_existing_directory(
        staging_summary_root,
        "staging summary root",
    )
    artifact_parent_descriptor: int | None = None
    artifact_parent_inode: tuple[int, int] | None = None
    summary_parent_descriptor: int | None = None
    summary_parent_inode: tuple[int, int] | None = None
    summary_descriptor: int | None = None
    summary_inode: tuple[int, int] | None = None
    artifact_temporary: tuple[str, tuple[int, int]] | None = None
    summary_temporaries: list[tuple[str, tuple[int, int]]] = []
    linked_summaries: list[tuple[str, tuple[int, int]]] = []
    linked_artifact: tuple[str, tuple[int, int]] | None = None
    created_summary = False
    succeeded = False
    try:
        summary_names = sorted(os.listdir(staging_descriptor))
        if not summary_names:
            raise SelectorDevelopmentError("Staged summaries must be nonempty.")
        staged_summaries: list[tuple[str, bytes]] = []
        for name in summary_names:
            source_stat = _entry_stat(staging_descriptor, name)
            if source_stat is None or not stat.S_ISREG(source_stat.st_mode) or Path(name).suffix.lower() != ".json":
                raise SelectorDevelopmentError("Staged summaries must be a nonempty flat set of regular JSON files.")
            source_inode = _identity(source_stat)
            source_bytes = _read_entry(staging_descriptor, name)
            current_source = _entry_stat(staging_descriptor, name)
            if current_source is None or _identity(current_source) != source_inode:
                raise SelectorDevelopmentError("A staged summary changed while it was captured.")
            staged_summaries.append((name, source_bytes))
        _verify_directory_path(
            staging_summary_root,
            staging_descriptor,
            staging_inode,
            "staging summary root",
        )

        artifact_parent_descriptor, artifact_parent_inode = _open_or_create_directory(
            artifact_output.parent,
            "selector examples output parent",
        )
        summary_parent_descriptor, summary_parent_inode = _open_or_create_directory(
            summary_output.parent,
            "summary output parent",
        )
        if _entry_stat(artifact_parent_descriptor, artifact_output.name) is not None:
            raise SelectorDevelopmentError("Selector examples output appeared before publication.")
        if _entry_stat(summary_parent_descriptor, summary_output.name) is not None:
            raise SelectorDevelopmentError("Summary output root appeared before publication.")

        artifact_rendered = _render_json(artifact).encode("utf-8")
        artifact_temporary = _create_temporary_json(
            artifact_parent_descriptor,
            artifact_output.name,
            artifact_rendered,
        )
        try:
            os.mkdir(summary_output.name, mode=0o755, dir_fd=summary_parent_descriptor)
        except FileExistsError as error:
            raise SelectorDevelopmentError(
                "Summary output root was concurrently created; refusing overwrite."
            ) from error
        # Remember successful creation before any operation that could fail.
        created_summary = True
        try:
            summary_descriptor = os.open(
                summary_output.name,
                _directory_open_flags(),
                dir_fd=summary_parent_descriptor,
            )
        except OSError as error:
            raise SelectorDevelopmentError("Could not retain the new summary output directory.") from error
        summary_inode = _identity(os.fstat(summary_descriptor))

        for name, source_bytes in staged_summaries:
            temporary_name, temporary_inode = _create_temporary_json(
                summary_descriptor,
                name,
                source_bytes,
            )
            summary_temporaries.append((temporary_name, temporary_inode))
        for (name, _source_bytes), (temporary_name, temporary_inode) in zip(
            staged_summaries,
            summary_temporaries,
            strict=True,
        ):
            try:
                os.link(
                    temporary_name,
                    name,
                    src_dir_fd=summary_descriptor,
                    dst_dir_fd=summary_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as error:
                raise SelectorDevelopmentError(
                    "A summary output was concurrently created; refusing overwrite."
                ) from error
            # The inode was captured before link(2); record ownership before
            # any stat/read/failure point after the successful link.
            linked_summaries.append((name, temporary_inode))
        artifact_temporary_name, artifact_temporary_inode = artifact_temporary
        try:
            os.link(
                artifact_temporary_name,
                artifact_output.name,
                src_dir_fd=artifact_parent_descriptor,
                dst_dir_fd=artifact_parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise SelectorDevelopmentError("Examples output was concurrently created; refusing overwrite.") from error
        linked_artifact = (artifact_output.name, artifact_temporary_inode)

        if _read_entry(artifact_parent_descriptor, artifact_output.name) != artifact_rendered:
            raise SelectorDevelopmentError("Published selector examples did not round-trip.")
        for name, source_bytes in staged_summaries:
            if _read_entry(summary_descriptor, name) != source_bytes:
                raise SelectorDevelopmentError("Published summary did not round-trip.")

        for temporary_name, temporary_inode in summary_temporaries:
            _unlink_owned_entry(summary_descriptor, temporary_name, temporary_inode)
        summary_temporaries.clear()
        _unlink_owned_entry(
            artifact_parent_descriptor,
            artifact_temporary_name,
            artifact_temporary_inode,
        )
        artifact_temporary = None

        os.fsync(summary_descriptor)
        os.fsync(summary_parent_descriptor)
        if artifact_parent_descriptor != summary_parent_descriptor:
            os.fsync(artifact_parent_descriptor)
        _verify_directory_path(
            artifact_output.parent,
            artifact_parent_descriptor,
            artifact_parent_inode,
            "selector examples output parent",
        )
        _verify_directory_path(
            summary_output.parent,
            summary_parent_descriptor,
            summary_parent_inode,
            "summary output parent",
        )
        _verify_directory_path(
            summary_output,
            summary_descriptor,
            summary_inode,
            "summary output root",
        )
        succeeded = True
    except Exception:
        if linked_artifact is not None and artifact_parent_descriptor is not None:
            _unlink_owned_entry(
                artifact_parent_descriptor,
                linked_artifact[0],
                linked_artifact[1],
            )
        if summary_descriptor is not None:
            for name, inode in reversed(linked_summaries):
                _unlink_owned_entry(summary_descriptor, name, inode)
        raise
    finally:
        if summary_descriptor is not None:
            for name, inode in summary_temporaries:
                _unlink_owned_entry(summary_descriptor, name, inode)
        if artifact_temporary is not None and artifact_parent_descriptor is not None:
            _unlink_owned_entry(
                artifact_parent_descriptor,
                artifact_temporary[0],
                artifact_temporary[1],
            )
        if summary_descriptor is not None:
            os.close(summary_descriptor)
        if not succeeded and created_summary and summary_parent_descriptor is not None:
            if summary_inode is not None:
                _remove_owned_directory(
                    summary_parent_descriptor,
                    summary_output.name,
                    summary_inode,
                )
            else:
                try:
                    os.rmdir(summary_output.name, dir_fd=summary_parent_descriptor)
                except OSError:
                    pass
        if artifact_parent_descriptor is not None:
            os.close(artifact_parent_descriptor)
        if summary_parent_descriptor is not None:
            os.close(summary_parent_descriptor)
        os.close(staging_descriptor)


def _preflight_loaded_development_envelope(
    value: Mapping[str, Any],
    name: str,
    *,
    id_field: str,
) -> None:
    _development(value.get("split"), f"{name} split")
    _preflight_development_tracks(value, name, id_field=id_field)


def _require_certification_dataset_audit(artifact: Mapping[str, Any]) -> None:
    """Reject custom/generic dataset strata from the real experiment driver."""

    aggregate = _mapping(artifact.get("labelDeterminacyAudit"), "labelDeterminacyAudit")
    if aggregate.get("schemaVersion") != LABEL_DETERMINACY_AUDIT_SCHEMA:
        raise SelectorDevelopmentError("Examples label-determinacy audit schema is unsupported.")
    aggregate_sha256 = _sha256(
        aggregate.get("auditSha256"),
        "labelDeterminacyAudit.auditSha256",
    )
    if aggregate_sha256 != canonical_sha256(_unsigned(aggregate, "auditSha256")):
        raise SelectorDevelopmentError("Examples label-determinacy aggregate hash is stale.")
    if artifact.get("labelDeterminacyAuditSha256") != aggregate_sha256:
        raise SelectorDevelopmentError("Examples artifact label-determinacy binding is stale.")
    aggregate_counts = {
        field: _nonnegative_integer(
            aggregate.get(field),
            f"labelDeterminacyAudit.{field}",
        )
        for field in _LABEL_DETERMINACY_COUNT_FIELDS
    }

    audit = _mapping(
        artifact.get("datasetLabelDeterminacyAudit"),
        "datasetLabelDeterminacyAudit",
    )
    _exact_fields(audit, _DATASET_LABEL_AUDIT_FIELDS, "datasetLabelDeterminacyAudit")
    if audit.get("schemaVersion") != DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA:
        raise SelectorDevelopmentError("Dataset label-determinacy audit schema is unsupported.")
    expected_ids = list(_CERTIFICATION_DATASET_IDS)
    required_ids = [
        _string(value, "datasetLabelDeterminacyAudit.requiredDatasetIds")
        for value in _sequence(
            audit.get("requiredDatasetIds"),
            "datasetLabelDeterminacyAudit.requiredDatasetIds",
        )
    ]
    dataset_ids = [
        _string(value, "datasetLabelDeterminacyAudit.datasetIds")
        for value in _sequence(
            audit.get("datasetIds"),
            "datasetLabelDeterminacyAudit.datasetIds",
        )
    ]
    if (
        audit.get("strataMode") != "certification-datasets-only-v1"
        or required_ids != expected_ids
        or dataset_ids != expected_ids
    ):
        raise SelectorDevelopmentError(
            "Real selector examples require certification-only strata for the exact five reviewed datasets."
        )
    raw_rows = list(_sequence(audit.get("rows"), "datasetLabelDeterminacyAudit.rows"))
    rows: list[dict[str, Any]] = []
    for index, raw_row in enumerate(raw_rows):
        row = _mapping(raw_row, f"datasetLabelDeterminacyAudit.rows[{index}]")
        _exact_fields(
            row,
            _DATASET_LABEL_AUDIT_ROW_FIELDS,
            f"datasetLabelDeterminacyAudit.rows[{index}]",
        )
        normalized = {
            "datasetId": _string(row.get("datasetId"), "dataset label-determinacy datasetId"),
            **{
                field: _nonnegative_integer(
                    row.get(field),
                    f"datasetLabelDeterminacyAudit.rows[{index}].{field}",
                )
                for field in _LABEL_DETERMINACY_COUNT_FIELDS
            },
            "rowSha256": _sha256(
                row.get("rowSha256"),
                f"datasetLabelDeterminacyAudit.rows[{index}].rowSha256",
            ),
        }
        if normalized["rowSha256"] != canonical_sha256(_unsigned(normalized, "rowSha256")):
            raise SelectorDevelopmentError("Dataset label-determinacy row hash is stale.")
        rows.append(normalized)
    if [row["datasetId"] for row in rows] != expected_ids:
        raise SelectorDevelopmentError("Dataset label-determinacy rows must cover the exact five reviewed datasets.")
    for field in _LABEL_DETERMINACY_COUNT_FIELDS:
        if sum(int(row[field]) for row in rows) != aggregate_counts[field]:
            raise SelectorDevelopmentError(f"Dataset label-determinacy rows do not sum to aggregate {field}.")
    if audit.get("aggregateLabelDeterminacyAuditSha256") != aggregate_sha256:
        raise SelectorDevelopmentError("Dataset label-determinacy aggregate binding is stale.")
    if audit.get("rowSetSha256") != canonical_sha256(rows):
        raise SelectorDevelopmentError("Dataset label-determinacy row-set hash is stale.")
    audit_sha256 = _sha256(audit.get("auditSha256"), "datasetLabelDeterminacyAudit.auditSha256")
    if audit_sha256 != canonical_sha256(_unsigned(audit, "auditSha256")):
        raise SelectorDevelopmentError("Dataset label-determinacy audit hash is stale.")
    if artifact.get("datasetLabelDeterminacyAuditSha256") != audit_sha256:
        raise SelectorDevelopmentError("Examples artifact dataset-audit binding is stale.")


def build_development_examples(
    benchmark_report_path: Path,
    audio_lineage_manifest_path: Path,
    runtime_bar_grid_manifest_path: Path,
    group_manifest_path: Path,
    *,
    benchmark_root: Path,
    runtime_bar_grid_root: Path,
    group_manifest_root: Path,
    summary_output_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Join the required full development artifacts and publish examples."""

    output = _preflight_new_json(output_path, "selector examples output")
    summary_output = _preflight_new_directory(summary_output_root, "summary output root")
    report, _report_raw = _read_json(benchmark_report_path, "benchmark report")
    lineage, _lineage_raw = _read_json(audio_lineage_manifest_path, "audio lineage manifest")
    runtime, _runtime_raw = _read_json(
        runtime_bar_grid_manifest_path,
        "runtime bar-grid manifest",
    )
    groups, _groups_raw = _read_json(group_manifest_path, "group manifest")
    # Reject protected envelopes before the called join resolves any leaf path.
    _preflight_loaded_development_envelope(report, "benchmark report", id_field="id")
    _preflight_loaded_development_envelope(lineage, "audio lineage", id_field="trackId")
    _preflight_loaded_development_envelope(runtime, "runtime bar-grid manifest", id_field="trackId")
    _preflight_loaded_development_envelope(groups, "group manifest", id_field="trackId")
    if lineage.get("schemaVersion") != AUDIO_LINEAGE_SCHEMA:
        raise SelectorDevelopmentError("Example building requires the full audio-lineage artifact.")
    _require_disjoint_summary_root(
        summary_output,
        (
            ("benchmark_root", benchmark_root),
            ("runtime_bar_grid_root", runtime_bar_grid_root),
            ("group_manifest_root", group_manifest_root),
        ),
    )

    with tempfile.TemporaryDirectory(prefix="chord-selector-summary-build-") as temporary_root:
        staging_root = Path(temporary_root).resolve(strict=True)
        artifact = build_bar_selector_examples(
            report,
            audio_lineage_manifest=lineage,
            benchmark_root=benchmark_root,
            runtime_bar_grid_manifest=runtime,
            runtime_bar_grid_root=runtime_bar_grid_root,
            group_manifest=groups,
            group_manifest_root=group_manifest_root,
            summary_output_root=staging_root,
        )
        if artifact.get("schemaVersion") != EXAMPLES_SCHEMA:
            raise SelectorDevelopmentError("Example builder returned an unsupported schema.")
        if artifact.get("artifactSha256") != canonical_sha256(_unsigned(artifact, "artifactSha256")):
            raise SelectorDevelopmentError("Example builder returned an artifact with a stale self hash.")
        _require_certification_dataset_audit(artifact)
        _publish_json_and_summary_set(output, artifact, staging_root, summary_output)
    return deepcopy(artifact)


def train_development_selector(
    examples_artifact_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Train and persist a non-promotable selector from development examples."""

    output = _preflight_new_json(output_path, "selector artifact output")
    examples, _examples_raw = _read_json(examples_artifact_path, "selector examples")
    _development(examples.get("split"), "selector examples split")
    raw_examples = _sequence(examples.get("examples"), "selector examples.examples")
    if not raw_examples:
        raise SelectorDevelopmentError("Selector examples must be nonempty.")
    for index, raw_example in enumerate(raw_examples):
        example = _mapping(raw_example, f"selector examples.examples[{index}]")
        _development(
            example.get("split"),
            f"selector examples.examples[{index}].split",
        )
    _require_certification_dataset_audit(examples)
    artifact = train_bar_selector(examples)
    if artifact.get("schemaVersion") != BAR_SELECTOR_ARTIFACT_SCHEMA:
        raise SelectorDevelopmentError("Selector trainer returned an unsupported schema.")
    training = _mapping(artifact.get("training"), "selector artifact training")
    if training.get("split") != DEVELOPMENT_SPLIT:
        raise SelectorDevelopmentError("Selector trainer returned a non-development artifact.")
    if artifact.get("developmentOnly") is not True or artifact.get("promotionEligible") is not False:
        raise SelectorDevelopmentError("Selector artifact must be development-only and non-promotable.")
    _atomic_publish_json_set({output: artifact})
    return deepcopy(artifact)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sealed development-only chord-bar selector experiment artifacts."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    freeze_shape = commands.add_parser(
        "freeze-expected-shape",
        help="Publish the fixed reviewed 246-track/169-group dataset shape.",
    )
    freeze_shape.add_argument("--output", type=Path, required=True)

    attest = commands.add_parser("attest-lineage", help="Build full audio lineage and projection.")
    attest.add_argument("--winner-cache-manifest", type=Path, required=True)
    attest.add_argument("--development-source-manifest", type=Path, required=True)
    attest.add_argument("--dasheng-cache-manifest", type=Path, required=True)
    attest.add_argument("--lineage-output", type=Path, required=True)
    attest.add_argument("--projection-output", type=Path, required=True)

    prepare = commands.add_parser("prepare-inputs", help="Prepare runtime and grouping inputs.")
    prepare.add_argument("--winner-cache-manifest", type=Path, required=True)
    prepare.add_argument("--audio-lineage-manifest", type=Path, required=True)
    prepare.add_argument("--development-source-manifest", type=Path, required=True)
    prepare.add_argument("--expected-dataset-shape", type=Path, required=True)
    prepare.add_argument("--derivative-registry", type=Path)
    prepare.add_argument("--expected-track-count", type=int, required=True)
    prepare.add_argument("--expected-base-group-count", type=int, required=True)
    prepare.add_argument("--expected-confidence-group-count", type=int, required=True)
    prepare.add_argument("--runtime-audio-output", type=Path, required=True)
    prepare.add_argument("--group-descriptor-output", type=Path, required=True)

    groups = commands.add_parser("build-groups", help="Hash references and seal groups.")
    groups.add_argument("--group-descriptor", type=Path, required=True)
    groups.add_argument("--reference-root", type=Path, required=True)
    groups.add_argument("--output", type=Path, required=True)

    examples = commands.add_parser("build-examples", help="Join sealed development bar examples.")
    examples.add_argument("--benchmark-report", type=Path, required=True)
    examples.add_argument("--audio-lineage-manifest", type=Path, required=True)
    examples.add_argument("--runtime-bar-grid-manifest", type=Path, required=True)
    examples.add_argument("--group-manifest", type=Path, required=True)
    examples.add_argument("--benchmark-root", type=Path, required=True)
    examples.add_argument("--runtime-bar-grid-root", type=Path, required=True)
    examples.add_argument("--group-manifest-root", type=Path, required=True)
    examples.add_argument("--summary-output-root", type=Path, required=True)
    examples.add_argument("--output", type=Path, required=True)

    selector = commands.add_parser("train-selector", help="Train the grouped OOF selector.")
    selector.add_argument("--examples", type=Path, required=True)
    selector.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "freeze-expected-shape":
        result = freeze_reviewed_expected_dataset_shape(args.output)
        receipt = {
            "command": args.command,
            "shapeSha256": result["shapeSha256"],
        }
    elif args.command == "attest-lineage":
        result = attest_development_lineage(
            args.winner_cache_manifest,
            args.development_source_manifest,
            args.dasheng_cache_manifest,
            args.lineage_output,
            args.projection_output,
        )
        receipt = {
            "command": args.command,
            "lineageArtifactSha256": result["lineage"]["artifactSha256"],
            "projectionSha256": result["projection"]["projectionSha256"],
        }
    elif args.command == "prepare-inputs":
        result = prepare_development_inputs(
            args.winner_cache_manifest,
            args.audio_lineage_manifest,
            args.development_source_manifest,
            args.runtime_audio_output,
            args.group_descriptor_output,
            expected_track_count=args.expected_track_count,
            expected_base_group_count=args.expected_base_group_count,
            expected_confidence_group_count=args.expected_confidence_group_count,
            expected_dataset_shape_path=args.expected_dataset_shape,
            derivative_registry_path=args.derivative_registry,
            require_reviewed_dataset_shape=True,
        )
        receipt = {
            "command": args.command,
            "runtimeAudioManifestSha256": canonical_sha256(result["runtimeAudioManifest"]),
            "groupDescriptorManifestSha256": result["groupDescriptorManifest"]["manifestSha256"],
        }
    elif args.command == "build-groups":
        descriptor, _raw = _read_json(args.group_descriptor, "group descriptor")
        result = build_development_groups(
            descriptor,
            reference_root=args.reference_root,
            output_path=args.output,
        )
        receipt = {"command": args.command, "manifestSha256": result["manifestSha256"]}
    elif args.command == "build-examples":
        result = build_development_examples(
            args.benchmark_report,
            args.audio_lineage_manifest,
            args.runtime_bar_grid_manifest,
            args.group_manifest,
            benchmark_root=args.benchmark_root,
            runtime_bar_grid_root=args.runtime_bar_grid_root,
            group_manifest_root=args.group_manifest_root,
            summary_output_root=args.summary_output_root,
            output_path=args.output,
        )
        receipt = {"command": args.command, "artifactSha256": result["artifactSha256"]}
    else:
        result = train_development_selector(args.examples, args.output)
        receipt = {"command": args.command, "artifactSha256": result["artifactSha256"]}
    print(json.dumps(receipt, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0


__all__ = [
    "DERIVATIVE_REGISTRY_SCHEMA",
    "DEVELOPMENT_INPUTS_SCHEMA",
    "EXPECTED_DATASET_SHAPE_SCHEMA",
    "SelectorDevelopmentError",
    "attest_development_lineage",
    "build_expected_dataset_shape",
    "build_derivative_registry",
    "build_development_examples",
    "build_development_groups",
    "explicit_empty_derivative_registry",
    "freeze_reviewed_expected_dataset_shape",
    "main",
    "prepare_development_inputs",
    "train_development_selector",
    "validate_development_group_descriptor",
]
