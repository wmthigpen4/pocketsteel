"""Development-only, byte-exact audio lineage for the frozen chord winner.

The attestor independently re-extracts the winner's multiband features from
source audio and compares the resulting little-endian float16 bytes with the
already-frozen feature cache.  It deliberately accepts only the development
partition.  Calibration, test, confirmation, and other protected partitions
are rejected from manifest metadata before an audio or feature-cache path is
resolved, statted, or opened.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from importlib import metadata as importlib_metadata
import io
import inspect
import json
import math
import os
from pathlib import Path
import platform
import secrets
import stat
import tempfile
from typing import Any
import zipfile

from .artifact_integrity import validate_factorized_artifact_manifest
from .bar_promotion import canonical_sha256
from .dasheng import DASHENG_REQUIRED_FILES
from .dasheng_cache import (
    DASHENG_CACHE_AUGMENTATION_POLICY,
    DASHENG_CACHE_SCHEMA,
    DASHENG_CACHE_STORAGE_DTYPE,
    DASHENG_FEATURE_SPEC_SCHEMA,
)
from .split_protocol import validate_split_protocol_manifest
from .student import extract_student_features


AUDIO_LINEAGE_SCHEMA = "chord_development_audio_lineage_v1"
AUDIO_LINEAGE_PROJECTION_SCHEMA = "chord_development_audio_lineage_projection_v1"
DATASET_DESCRIPTOR_SCHEMA = "chord_dataset_manifest_v1"
FEATURE_CONTRACT_SCHEMA = "chord_development_audio_feature_contract_v1"
EXTRACTOR_CONTRACT_SCHEMA = "chord_development_audio_extractor_contract_v1"
MANIFEST_BINDINGS_SCHEMA = "chord_development_audio_manifest_bindings_v1"
DEVELOPMENT_SPLIT = "development"
FEATURE_KIND = "multiband_chroma_v2"
FEATURE_COUNT = 61
SAMPLE_RATE = 11_025
FRAME_SECONDS = 0.1
STORAGE_DTYPE = "<f2"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DEPENDENCY_LOCK = _REPO_ROOT / "requirements" / "chord-reader.lock"
_HEX = frozenset("0123456789abcdef")
_AUDIO_SUFFIXES = frozenset({".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"})
_FEATURE_MEMBERS = (
    frozenset({"features", "labels", "training_weight"}),
    frozenset({"features", "labels", "label_valid", "training_weight"}),
)
_DASHENG_ROOT_KEYS = frozenset(
    {
        "schemaVersion",
        "sampleRate",
        "frameSeconds",
        "featureKind",
        "featureCount",
        "modelId",
        "revision",
        "weightSha256",
        "featureSpecSha256",
        "augmentationPolicy",
        "storageDtype",
        "selectedSplits",
        "heldOutExtractionAuthorized",
        "featureSpec",
        "sourceManifests",
        "datasets",
        "tracks",
    }
)
_DASHENG_TRACK_KEYS = frozenset(
    {
        "id",
        "datasetId",
        "split",
        "path",
        "frames",
        "durationSeconds",
        "audioPath",
        "sourceAudioSha256",
        "sourceFeatureSha256",
        "featureSha256",
        "featureSpecSha256",
    }
)
_DASHENG_FEATURE_SPEC_KEYS = frozenset(
    {
        "schemaVersion",
        "featureKind",
        "modelId",
        "revision",
        "weightSha256",
        "runtimeFileSha256",
        "sampleRate",
        "nativeFrameSeconds",
        "frameSeconds",
        "featureCount",
        "pooling",
        "timestampConvention",
        "storageDtype",
        "augmentationPolicy",
        "provenanceSha256",
        "featureSpecSha256",
    }
)
_FILE_BINDING_KEYS = frozenset(
    {
        "role",
        "schemaVersion",
        "path",
        "pathSha256",
        "fileSha256",
        "bytes",
        "canonicalSha256",
    }
)
_MANIFEST_BINDING_KEYS = frozenset(
    {
        "schemaVersion",
        "winnerCacheManifest",
        "developmentSourceManifest",
        "dashengCacheManifest",
        "winnerCacheOutputManifestSha256",
        "winnerCacheSourceManifestSha256",
        "winnerCacheArtifactSetSha256",
        "winnerCacheAudioBindingStatus",
        "dashengFeatureSpecSha256",
        "bindingsSha256",
    }
)
_FEATURE_CONTRACT_KEYS = frozenset(
    {
        "schemaVersion",
        "featureKind",
        "featureCount",
        "sampleRate",
        "frameSeconds",
        "storageDtype",
        "featureSpecSha256",
        "contractSha256",
    }
)
_EXTRACTOR_CONTRACT_KEYS = frozenset(
    {
        "schemaVersion",
        "entrypoint",
        "sourceFile",
        "sourceFilePathSha256",
        "sourceFileSha256",
        "sourceFileBytes",
        "functionSourceSha256",
        "dependencyLockFile",
        "dependencyLockPathSha256",
        "dependencyLockSha256",
        "dependencyLockBytes",
        "dependencies",
        "dependenciesSha256",
        "featureContractSha256",
        "contractSha256",
    }
)
_ROW_KEYS = frozenset(
    {
        "trackId",
        "datasetId",
        "split",
        "audioPath",
        "audioPathSha256",
        "sourceAudioSha256",
        "sourceAudioBytes",
        "cachedFeaturePath",
        "cachedFeaturePathSha256",
        "cachedFeatureArtifactSha256",
        "cachedFeatureArtifactBytes",
        "cachedArraySha256",
        "freshArraySha256",
        "frames",
        "featureCount",
        "elementCount",
        "cachedDurationSeconds",
        "freshDurationSeconds",
        "canonicalDurationMilliseconds",
        "winnerTrackSha256",
        "winnerArtifactEntrySha256",
        "sourceDescriptorSha256",
        "dashengTrackSha256",
        "sourceMetadataSha256",
        "rowSha256",
    }
)
_ROOT_KEYS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "featureContract",
        "extractorContract",
        "manifestBindings",
        "trackCount",
        "tracks",
        "trackSetSha256",
        "audioSetSha256",
        "arraySetSha256",
        "artifactSha256",
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


FeatureExtractor = Callable[[Path, str], tuple[Any, float]]


@dataclass(frozen=True)
class _LoadedJson:
    path: Path
    value: dict[str, Any]
    sha256: str
    bytes: int
    canonical_sha256: str


@dataclass(frozen=True)
class _StableFile:
    path: Path
    sha256: str
    bytes: int
    identity: tuple[int, int, int, int, int]
    captured: bytes | None = None


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
    if not isinstance(value, str) or not value.strip() or value != value.strip() or "\x00" in value:
        raise ValueError(f"{name} must be a trimmed, nonempty string.")
    return value


def _required_sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite positive number.")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be a finite positive number.")
    return result


def _lexical_absolute(raw: str | Path, *, base: Path | None = None, name: str) -> Path:
    value = os.fspath(raw)
    if not value or "\x00" in value:
        raise ValueError(f"{name} must be a nonempty local path.")
    source = Path(value)
    if ".." in source.parts:
        raise ValueError(f"{name} may not contain parent traversal.")
    if not source.is_absolute():
        if base is None:
            raise ValueError(f"{name} must be absolute.")
        source = base / source
    absolute = Path(os.path.abspath(source))
    if not absolute.is_absolute():  # pragma: no cover - os.path.abspath contract
        raise ValueError(f"{name} must be absolute.")
    return absolute


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _directory_flags() -> int:
    required = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, item) for item in required):  # pragma: no cover - supported deployment platforms
        raise ValueError("Secure no-follow directory access is unavailable on this platform.")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _file_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW"):  # pragma: no cover - supported deployment platforms
        raise ValueError("Secure no-follow file access is unavailable on this platform.")
    return os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _open_directory_fd(path: Path, name: str, *, create: bool = False) -> int:
    """Open an absolute directory through an anchored, no-follow component walk."""

    if not path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{name} must be an absolute traversal-free directory path.")
    flags = _directory_flags()
    try:
        current = os.open(path.anchor, flags)
    except OSError as error:  # pragma: no cover - an invalid filesystem root is platform failure
        raise ValueError(f"Could not securely open {name}.") from error
    try:
        for component in path.parts[1:]:
            try:
                following = os.open(component, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, mode=0o755, dir_fd=current)
                    os.fsync(current)
                except FileExistsError:
                    pass
                following = os.open(component, flags, dir_fd=current)
            os.close(current)
            current = following
        return current
    except FileNotFoundError:
        os.close(current)
        raise
    except Exception as error:
        os.close(current)
        if isinstance(error, ValueError):
            raise
        raise ValueError(f"Could not securely open {name} without following symlinks.") from error


def _write_all(descriptor: int, value: bytes) -> None:
    remaining = memoryview(value)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:  # pragma: no cover - os.write contract
            raise OSError("short write")
        remaining = remaining[written:]


def _require_regular_file(path: Path, name: str) -> None:
    parent = _open_directory_fd(path.parent, f"{name} parent")
    descriptor: int | None = None
    try:
        descriptor = os.open(path.name, _file_flags(), dir_fd=parent)
        value = os.fstat(descriptor)
        if not stat.S_ISREG(value.st_mode) or value.st_size <= 0:
            raise ValueError(f"{name} must be a nonempty regular, non-symlink file.")
        linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if _stat_identity(value) != _stat_identity(linked):
            raise ValueError(f"{name} changed during path preflight.")
    except ValueError:
        raise
    except OSError as error:
        raise ValueError(f"Could not securely preflight {name}.") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def _stable_file(
    path: Path,
    name: str,
    *,
    expected_suffixes: frozenset[str] | None = None,
    capture_bytes: bool = False,
    copy_to_fd: int | None = None,
) -> _StableFile:
    """Capture one regular file through one no-follow descriptor.

    Hashing, optional byte capture, and optional snapshot copying all consume the
    same descriptor stream.  The containing directory remains descriptor-bound
    until the final pathname-to-inode comparison, so a component swap cannot
    splice a different read into the attestation.
    """

    if expected_suffixes is not None and path.suffix.lower() not in expected_suffixes:
        raise ValueError(f"{name} uses an unsupported file suffix.")
    parent = _open_directory_fd(path.parent, f"{name} parent")
    descriptor: int | None = None
    try:
        descriptor = os.open(path.name, _file_flags(), dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"{name} must be a regular, non-symlink file: {path}.")
        if before.st_size <= 0:
            raise ValueError(f"{name} must not be empty.")
        digest = hashlib.sha256()
        captured: list[bytes] | None = [] if capture_bytes else None
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            if captured is not None:
                captured.append(chunk)
            if copy_to_fd is not None:
                _write_all(copy_to_fd, chunk)
        after = os.fstat(descriptor)
        try:
            linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError as error:
            raise ValueError(f"{name} changed while it was captured.") from error
        identity = _stat_identity(before)
        if identity != _stat_identity(after) or identity != _stat_identity(linked) or not stat.S_ISREG(linked.st_mode):
            raise ValueError(f"{name} changed while it was captured.")
        content = b"".join(captured) if captured is not None else None
        return _StableFile(path, digest.hexdigest(), before.st_size, identity, content)
    except ValueError:
        raise
    except OSError as error:
        raise ValueError(f"Could not securely capture {name}.") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def _assert_file_identity(identity: _StableFile, name: str) -> None:
    current = _stable_file(identity.path, name)
    if current.sha256 != identity.sha256 or current.bytes != identity.bytes or current.identity != identity.identity:
        raise ValueError(f"{name} changed after validation.")


def _load_json(path: Path, name: str) -> _LoadedJson:
    absolute = _lexical_absolute(path, name=name)
    identity = _stable_file(
        absolute,
        name,
        expected_suffixes=frozenset({".json"}),
        capture_bytes=True,
    )
    if identity.captured is None:  # pragma: no cover - capture contract
        raise ValueError(f"Could not capture {name} bytes.")
    try:
        parsed = json.loads(identity.captured)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not parse {name} as JSON.") from error
    value = dict(_mapping(parsed, name))
    # This also rejects NaN and non-JSON values in injected mapping subclasses.
    canonical = canonical_sha256(value)
    return _LoadedJson(absolute, value, identity.sha256, identity.bytes, canonical)


def _file_binding(role: str, loaded: _LoadedJson) -> dict[str, Any]:
    return {
        "role": role,
        "schemaVersion": _required_string(loaded.value.get("schemaVersion"), f"{role} schemaVersion"),
        "path": str(loaded.path),
        "pathSha256": canonical_sha256(str(loaded.path)),
        "fileSha256": loaded.sha256,
        "bytes": loaded.bytes,
        "canonicalSha256": loaded.canonical_sha256,
    }


def _validate_dataset_descriptor(value: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if value.get("schemaVersion") != DATASET_DESCRIPTOR_SCHEMA:
        raise ValueError(f"Development source manifest must use {DATASET_DESCRIPTOR_SCHEMA}.")
    tracks = _sequence(value.get("tracks"), "development source tracks")
    if not tracks:
        raise ValueError("Development source manifest must contain tracks.")
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, raw_track in enumerate(tracks):
        track = _mapping(raw_track, f"development source tracks[{index}]")
        identifier = _required_string(track.get("id"), f"development source tracks[{index}].id")
        if identifier in by_id:
            raise ValueError(f"Duplicate development source track id {identifier!r}.")
        if track.get("split") != DEVELOPMENT_SPLIT:
            raise ValueError(
                "The audio-lineage source must be development-only; calibration, test, "
                "heldout, confirmation, training, and every other split are forbidden "
                "before audio or feature-cache path access."
            )
        _required_string(track.get("datasetId"), f"source track {identifier!r} datasetId")
        audio_path = _required_string(track.get("audioPath"), f"source track {identifier!r} audioPath")
        if Path(audio_path).suffix.lower() not in _AUDIO_SUFFIXES:
            raise ValueError(f"Source track {identifier!r} audioPath uses an unsupported suffix.")
        for key, item in track.items():
            if key.lower().endswith("path") and item is not None:
                _required_string(item, f"source track {identifier!r} {key}")
            if key.lower().endswith("sha256") and item is not None:
                _required_sha256(item, f"source track {identifier!r} {key}")
        canonical_sha256(track)
        by_id[identifier] = track
    return by_id


def _validate_dasheng_manifest(value: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _exact_keys(value, _DASHENG_ROOT_KEYS, "Dasheng cache manifest")
    if value.get("schemaVersion") != DASHENG_CACHE_SCHEMA:
        raise ValueError(f"Dasheng cache must use {DASHENG_CACHE_SCHEMA}.")
    expected_scalars = {
        "sampleRate": 16_000,
        "frameSeconds": 0.1,
        "featureKind": "dasheng_base_v1",
        "featureCount": 768,
        "modelId": "mispeech/dasheng-base",
        "augmentationPolicy": DASHENG_CACHE_AUGMENTATION_POLICY,
        "storageDtype": DASHENG_CACHE_STORAGE_DTYPE,
        "heldOutExtractionAuthorized": False,
    }
    for key, expected in expected_scalars.items():
        if value.get(key) != expected:
            raise ValueError(f"Dasheng cache field {key!r} must be {expected!r}.")
    revision = value.get("revision")
    if not isinstance(revision, str) or len(revision) != 40 or any(character not in _HEX for character in revision):
        raise ValueError("Dasheng cache revision must be a full lowercase Git SHA.")
    weight_sha256 = _required_sha256(value.get("weightSha256"), "Dasheng weightSha256")
    feature_spec_sha256 = _required_sha256(value.get("featureSpecSha256"), "Dasheng featureSpecSha256")
    selected_splits = _sequence(value.get("selectedSplits"), "Dasheng selectedSplits")
    if not selected_splits or list(selected_splits) != sorted(set(selected_splits)):
        raise ValueError("Dasheng selectedSplits must be a sorted, unique, nonempty array.")
    if any(split not in {"train", "development"} for split in selected_splits):
        raise ValueError("Audio lineage forbids held-out Dasheng source splits.")

    spec = _mapping(value.get("featureSpec"), "Dasheng featureSpec")
    _exact_keys(spec, _DASHENG_FEATURE_SPEC_KEYS, "Dasheng featureSpec")
    if spec.get("schemaVersion") != DASHENG_FEATURE_SPEC_SCHEMA:
        raise ValueError("Dasheng featureSpec uses an unsupported schema.")
    claimed_spec_sha256 = _required_sha256(spec.get("featureSpecSha256"), "Dasheng featureSpec.featureSpecSha256")
    unsigned_spec = {key: item for key, item in spec.items() if key != "featureSpecSha256"}
    if canonical_sha256(unsigned_spec) != claimed_spec_sha256 or claimed_spec_sha256 != feature_spec_sha256:
        raise ValueError("Dasheng featureSpec hash is invalid.")
    cross_fields = {
        "featureKind": "dasheng_base_v1",
        "modelId": "mispeech/dasheng-base",
        "revision": revision,
        "weightSha256": weight_sha256,
        "sampleRate": 16_000,
        "frameSeconds": 0.1,
        "featureCount": 768,
        "storageDtype": DASHENG_CACHE_STORAGE_DTYPE,
        "augmentationPolicy": DASHENG_CACHE_AUGMENTATION_POLICY,
    }
    if any(spec.get(key) != expected for key, expected in cross_fields.items()):
        raise ValueError("Dasheng featureSpec does not match its manifest.")
    runtime_hashes = _mapping(spec.get("runtimeFileSha256"), "Dasheng runtimeFileSha256")
    if set(runtime_hashes) != set(DASHENG_REQUIRED_FILES) or any(
        not isinstance(item, str) or len(item) != 64 or any(character not in _HEX for character in item)
        for item in runtime_hashes.values()
    ):
        raise ValueError("Dasheng featureSpec does not bind the complete runtime file allowlist.")
    if runtime_hashes.get("model.safetensors") != weight_sha256:
        raise ValueError("Dasheng featureSpec weight hash is inconsistent.")
    _required_sha256(spec.get("provenanceSha256"), "Dasheng provenanceSha256")

    sources = _sequence(value.get("sourceManifests"), "Dasheng sourceManifests")
    if not sources:
        raise ValueError("Dasheng cache must bind its source manifests.")
    for index, raw_source in enumerate(sources):
        source = _mapping(raw_source, f"Dasheng sourceManifests[{index}]")
        if set(source) not in ({"sha256"}, {"sha256", "path"}):
            raise ValueError("Dasheng source manifest metadata has unexpected fields.")
        _required_sha256(source.get("sha256"), f"Dasheng sourceManifests[{index}].sha256")
        if "path" in source:
            _required_string(source["path"], f"Dasheng sourceManifests[{index}].path")

    tracks = _sequence(value.get("tracks"), "Dasheng tracks")
    if not tracks:
        raise ValueError("Dasheng cache must contain tracks.")
    by_id: dict[str, Mapping[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for index, raw_track in enumerate(tracks):
        track = _mapping(raw_track, f"Dasheng tracks[{index}]")
        _exact_keys(track, _DASHENG_TRACK_KEYS, f"Dasheng tracks[{index}]")
        identifier = _required_string(track.get("id"), f"Dasheng tracks[{index}].id")
        dataset_id = _required_string(track.get("datasetId"), f"Dasheng track {identifier!r} datasetId")
        if identifier in by_id:
            raise ValueError(f"Duplicate Dasheng track id {identifier!r}.")
        if track.get("split") not in selected_splits:
            raise ValueError(f"Dasheng track {identifier!r} has an unselected source split.")
        _required_string(track.get("path"), f"Dasheng track {identifier!r} path")
        _required_string(track.get("audioPath"), f"Dasheng track {identifier!r} audioPath")
        _positive_integer(track.get("frames"), f"Dasheng track {identifier!r} frames")
        _finite_positive(track.get("durationSeconds"), f"Dasheng track {identifier!r} durationSeconds")
        for name in ("sourceAudioSha256", "sourceFeatureSha256", "featureSha256"):
            _required_sha256(track.get(name), f"Dasheng track {identifier!r} {name}")
        if track.get("featureSpecSha256") != feature_spec_sha256:
            raise ValueError(f"Dasheng track {identifier!r} has a different feature specification.")
        canonical_sha256(track)
        by_id[identifier] = track
        order.append((dataset_id, identifier))
    if order != sorted(order):
        raise ValueError("Dasheng tracks must be canonically sorted by datasetId and id.")
    datasets = _sequence(value.get("datasets"), "Dasheng datasets")
    expected_datasets = sorted({dataset_id for dataset_id, _identifier in order})
    if list(datasets) != expected_datasets:
        raise ValueError("Dasheng dataset list does not match its tracks.")
    return by_id


def _feature_contract(cache: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "featureKind": FEATURE_KIND,
        "featureCount": FEATURE_COUNT,
        "sampleRate": SAMPLE_RATE,
        "frameSeconds": FRAME_SECONDS,
    }
    if any(cache.get(key) != value for key, value in expected.items()):
        raise ValueError("Winner cache is not the exact multiband_chroma_v2 feature contract.")
    feature_spec_sha256 = _required_sha256(cache.get("featureSpecSha256"), "winner cache featureSpecSha256")
    payload = {
        "schemaVersion": FEATURE_CONTRACT_SCHEMA,
        **expected,
        "storageDtype": STORAGE_DTYPE,
        "featureSpecSha256": feature_spec_sha256,
    }
    return {**payload, "contractSha256": canonical_sha256(payload)}


def _dependency_versions(
    supplied: Mapping[str, str] | None = None,
) -> dict[str, str]:
    if supplied is not None:
        values = dict(supplied)
        if set(values) != {"python", "librosa", "numpy", "scipy", "soundfile"} or any(
            not isinstance(item, str) or not item for item in values.values()
        ):
            raise ValueError("Injected extraction dependency versions are incomplete.")
        return values
    values = {"python": platform.python_version()}
    for distribution in ("librosa", "numpy", "scipy", "soundfile"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError as error:
            raise ValueError(f"Required extraction dependency {distribution!r} is unavailable.") from error
    return values


def _extractor_contract(
    extractor: FeatureExtractor,
    feature_contract: Mapping[str, Any],
    *,
    dependency_lock_path: Path,
    dependency_versions: Mapping[str, str] | None,
) -> dict[str, Any]:
    source_name = inspect.getsourcefile(extractor)
    if source_name is None:
        raise ValueError("Feature extractor must have a readable source module.")
    source_path = _lexical_absolute(source_name, name="extractor source file")
    lock_path = _lexical_absolute(dependency_lock_path, name="extractor dependency lock")
    source = _stable_file(source_path, "extractor source file")
    lock = _stable_file(lock_path, "extractor dependency lock")
    try:
        function_source = inspect.getsource(extractor).encode("utf-8")
    except (OSError, TypeError) as error:
        raise ValueError("Feature extractor source cannot be inspected.") from error
    dependencies = _dependency_versions(dependency_versions)
    payload = {
        "schemaVersion": EXTRACTOR_CONTRACT_SCHEMA,
        "entrypoint": f"{extractor.__module__}.{extractor.__qualname__}",
        "sourceFile": str(source.path),
        "sourceFilePathSha256": canonical_sha256(str(source.path)),
        "sourceFileSha256": source.sha256,
        "sourceFileBytes": source.bytes,
        "functionSourceSha256": hashlib.sha256(function_source).hexdigest(),
        "dependencyLockFile": str(lock.path),
        "dependencyLockPathSha256": canonical_sha256(str(lock.path)),
        "dependencyLockSha256": lock.sha256,
        "dependencyLockBytes": lock.bytes,
        "dependencies": dependencies,
        "dependenciesSha256": canonical_sha256(dependencies),
        "featureContractSha256": feature_contract["contractSha256"],
    }
    return {**payload, "contractSha256": canonical_sha256(payload)}


def _manifest_bindings(
    winner: _LoadedJson,
    source: _LoadedJson,
    dasheng: _LoadedJson,
) -> dict[str, Any]:
    protocol = _mapping(winner.value.get("splitProtocol"), "winner splitProtocol")
    integrity = _mapping(winner.value.get("artifactIntegrity"), "winner artifactIntegrity")
    payload = {
        "schemaVersion": MANIFEST_BINDINGS_SCHEMA,
        "winnerCacheManifest": _file_binding("winnerCacheManifest", winner),
        "developmentSourceManifest": _file_binding("developmentSourceManifest", source),
        "dashengCacheManifest": _file_binding("dashengCacheManifest", dasheng),
        "winnerCacheOutputManifestSha256": _required_sha256(
            protocol.get("outputManifestSha256"), "winner outputManifestSha256"
        ),
        "winnerCacheSourceManifestSha256": _required_sha256(
            protocol.get("sourceManifestSha256"), "winner sourceManifestSha256"
        ),
        "winnerCacheArtifactSetSha256": _required_sha256(
            integrity.get("artifactSetSha256"), "winner artifactSetSha256"
        ),
        "winnerCacheAudioBindingStatus": "absent_repaired_by_fresh_array_equality_v1",
        "dashengFeatureSpecSha256": _required_sha256(
            dasheng.value.get("featureSpecSha256"), "Dasheng featureSpecSha256"
        ),
    }
    return {**payload, "bindingsSha256": canonical_sha256(payload)}


def _canonical_milliseconds(duration: float) -> int:
    return int(math.floor(duration * 1000.0 + 0.5))


def _expected_frames(duration: float) -> int:
    return max(1, math.ceil(duration / FRAME_SECONDS - 1e-12))


def _feature_bytes(array: Any, name: str) -> tuple[Any, str]:
    numpy = __import__("numpy")
    try:
        raw = numpy.asarray(array)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} is not a numeric feature array.") from error
    if raw.ndim != 2 or raw.shape[0] < 1 or raw.shape[1] != FEATURE_COUNT:
        raise ValueError(f"{name} must have exact shape (frames, {FEATURE_COUNT}).")
    if not numpy.issubdtype(raw.dtype, numpy.number) or not numpy.isfinite(raw).all():
        raise ValueError(f"{name} must contain only finite numeric values.")
    if numpy.issubdtype(raw.dtype, numpy.complexfloating):
        raise ValueError(f"{name} must contain real-valued features.")
    cast = numpy.ascontiguousarray(raw, dtype=numpy.dtype(STORAGE_DTYPE))
    if cast.dtype.str != STORAGE_DTYPE or not cast.flags.c_contiguous or not numpy.isfinite(cast).all():
        raise ValueError(f"{name} could not be canonicalized to contiguous {STORAGE_DTYPE}.")
    digest = hashlib.sha256(cast.tobytes(order="C")).hexdigest()
    return cast, digest


def _load_cached_features(captured: bytes, name: str) -> Any:
    try:
        with zipfile.ZipFile(io.BytesIO(captured)) as archive:
            infos = archive.infolist()
    except (OSError, zipfile.BadZipFile) as error:
        raise ValueError(f"{name} is not a valid NPZ archive.") from error
    names = [item.filename for item in infos]
    members = frozenset(item.removesuffix(".npy") for item in names)
    if (
        len(names) != len(set(names))
        or not all(item.endswith(".npy") for item in names)
        or members not in _FEATURE_MEMBERS
    ):
        raise ValueError(f"{name} has an unexpected or duplicate NPZ member allowlist.")
    if any(item.flag_bits & 0x1 or item.compress_type != zipfile.ZIP_DEFLATED or item.is_dir() for item in infos):
        raise ValueError(f"{name} must contain only unencrypted DEFLATE NPY members.")
    numpy = __import__("numpy")
    try:
        with numpy.load(io.BytesIO(captured), allow_pickle=False) as archive:
            return archive["features"].copy()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        raise ValueError(f"{name} has an unreadable feature array.") from error


@contextmanager
def _private_audio_snapshot(
    path: Path,
    name: str,
) -> Iterator[tuple[_StableFile, Path]]:
    """Yield an exact, private, read-only copy of one securely captured audio file."""

    temporary_base = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(
        prefix="chord-audio-lineage-",
        dir=temporary_base,
    ) as temporary_name:
        temporary_root = Path(temporary_name)
        root_descriptor = _open_directory_fd(temporary_root, f"{name} snapshot directory")
        snapshot_name = f"source{path.suffix.lower()}"
        snapshot_path = temporary_root / snapshot_name
        snapshot_descriptor: int | None = None
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            snapshot_descriptor = os.open(snapshot_name, flags, 0o600, dir_fd=root_descriptor)
            identity = _stable_file(
                path,
                name,
                expected_suffixes=_AUDIO_SUFFIXES,
                copy_to_fd=snapshot_descriptor,
            )
            os.fsync(snapshot_descriptor)
            snapshot_stat = os.fstat(snapshot_descriptor)
            if not stat.S_ISREG(snapshot_stat.st_mode) or snapshot_stat.st_size != identity.bytes:
                raise ValueError(f"{name} private snapshot is incomplete.")
            os.fchmod(snapshot_descriptor, stat.S_IRUSR)
            os.fsync(snapshot_descriptor)
            os.close(snapshot_descriptor)
            snapshot_descriptor = None
            os.fsync(root_descriptor)
            linked = os.stat(snapshot_name, dir_fd=root_descriptor, follow_symlinks=False)
            snapshot_identity = _stat_identity(linked)
            if not stat.S_ISREG(linked.st_mode):  # pragma: no cover - exclusive creation contract
                raise ValueError(f"{name} private snapshot is not regular.")
            yield identity, snapshot_path
            after = os.stat(snapshot_name, dir_fd=root_descriptor, follow_symlinks=False)
            if _stat_identity(after) != snapshot_identity or not stat.S_ISREG(after.st_mode):
                raise ValueError(f"{name} private snapshot changed during extraction.")
        finally:
            if snapshot_descriptor is not None:
                os.close(snapshot_descriptor)
            try:
                os.unlink(snapshot_name, dir_fd=root_descriptor)
                os.fsync(root_descriptor)
            except FileNotFoundError:
                pass
            os.close(root_descriptor)


def _source_metadata_sha256(
    winner_track: Mapping[str, Any],
    artifact_entry: Mapping[str, Any],
    source_track: Mapping[str, Any],
    dasheng_track: Mapping[str, Any],
) -> tuple[str, str, str, str, str]:
    winner_sha = canonical_sha256(winner_track)
    artifact_sha = canonical_sha256(artifact_entry)
    source_sha = canonical_sha256(source_track)
    dasheng_sha = canonical_sha256(dasheng_track)
    combined = canonical_sha256(
        {
            "winnerTrackSha256": winner_sha,
            "winnerArtifactEntrySha256": artifact_sha,
            "sourceDescriptorSha256": source_sha,
            "dashengTrackSha256": dasheng_sha,
        }
    )
    return winner_sha, artifact_sha, source_sha, dasheng_sha, combined


def _preflight_inputs(
    winner: _LoadedJson,
    source: _LoadedJson,
    dasheng: _LoadedJson,
) -> tuple[
    dict[str, Any],
    list[tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Path, Path]],
]:
    # These validators are metadata-only in this mode.  In particular, they do
    # not stat or open a path named by any track.
    validate_split_protocol_manifest(winner.value)
    validate_factorized_artifact_manifest(winner.value, verify_files=False)
    feature_contract = _feature_contract(winner.value)
    source_by_id = _validate_dataset_descriptor(source.value)
    dasheng_by_id = _validate_dasheng_manifest(dasheng.value)

    raw_winner_tracks = _sequence(winner.value.get("tracks"), "winner cache tracks")
    development_tracks = [
        _mapping(track, "winner cache track") for track in raw_winner_tracks if track.get("split") == DEVELOPMENT_SPLIT
    ]
    if not development_tracks:
        raise ValueError("Winner cache has no development tracks.")
    development_tracks.sort(key=lambda item: str(item.get("id", "")))
    development_ids = [_required_string(track.get("id"), "winner development track id") for track in development_tracks]
    if len(development_ids) != len(set(development_ids)):
        raise ValueError("Winner development track ids must be unique.")
    expected_count = _mapping(
        _mapping(winner.value["splitProtocol"], "winner splitProtocol").get("partitions"),
        "winner partitions",
    ).get(DEVELOPMENT_SPLIT)
    expected_count = _mapping(expected_count, "winner development partition").get("trackCount")
    if expected_count != len(development_tracks):
        raise ValueError("Winner development count does not match its signed split protocol.")
    if set(source_by_id) != set(development_ids):
        raise ValueError("Development source ids must exactly match the signed winner development set.")
    missing_dasheng = sorted(set(development_ids) - set(dasheng_by_id))
    if missing_dasheng:
        raise ValueError(f"Dasheng cache is missing winner development ids: {missing_dasheng}.")

    integrity_tracks = _sequence(
        _mapping(winner.value.get("artifactIntegrity"), "winner artifactIntegrity").get("tracks"),
        "winner sealed artifact tracks",
    )
    artifact_by_id = {
        str(_mapping(item, "winner artifact entry").get("id")): _mapping(item, "winner artifact entry")
        for item in integrity_tracks
    }
    if len(artifact_by_id) != len(integrity_tracks):
        raise ValueError("Winner artifact entry ids must be unique.")

    prepared: list[tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Path, Path]] = []
    for winner_track in development_tracks:
        identifier = str(winner_track["id"])
        source_track = source_by_id[identifier]
        dasheng_track = dasheng_by_id[identifier]
        artifact_entry = artifact_by_id.get(identifier)
        if artifact_entry is None:
            raise ValueError(f"Winner development track {identifier!r} has no sealed artifact entry.")
        dataset_id = _required_string(winner_track.get("datasetId"), f"winner track {identifier!r} datasetId")
        if source_track.get("datasetId") != dataset_id or dasheng_track.get("datasetId") != dataset_id:
            raise ValueError(f"Track {identifier!r} datasetId differs across authoritative manifests.")
        source_audio = _lexical_absolute(
            str(source_track["audioPath"]),
            base=source.path.parent,
            name=f"source track {identifier!r} audioPath",
        )
        dasheng_audio = _lexical_absolute(
            str(dasheng_track["audioPath"]),
            base=dasheng.path.parent,
            name=f"Dasheng track {identifier!r} audioPath",
        )
        if source_audio != dasheng_audio:
            raise ValueError(f"Track {identifier!r} audioPath differs across authoritative manifests.")
        if source_audio.suffix.lower() not in _AUDIO_SUFFIXES:
            raise ValueError(f"Track {identifier!r} audio uses an unsupported suffix.")
        cache_path = _lexical_absolute(
            str(winner_track.get("path", "")),
            base=winner.path.parent,
            name=f"winner track {identifier!r} feature path",
        )
        if cache_path.suffix.lower() != ".npz":
            raise ValueError(f"Winner track {identifier!r} feature path must use NPZ.")
        if artifact_entry.get("featurePath") != str(winner_track.get("path")):
            raise ValueError(f"Winner track {identifier!r} feature path differs from its artifact seal.")
        _required_sha256(dasheng_track.get("sourceAudioSha256"), f"Dasheng track {identifier!r} sourceAudioSha256")
        _finite_positive(winner_track.get("durationSeconds"), f"winner track {identifier!r} durationSeconds")
        _positive_integer(winner_track.get("frames"), f"winner track {identifier!r} frames")
        prepared.append((winner_track, artifact_entry, source_track, dasheng_track, source_audio, cache_path))
    return feature_contract, prepared


def _build_row(
    prepared: tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Path, Path],
    extractor: FeatureExtractor,
) -> dict[str, Any]:
    winner_track, artifact_entry, source_track, dasheng_track, audio_path, cache_path = prepared
    identifier = str(winner_track["id"])
    audio_name = f"track {identifier!r} source audio"
    with _private_audio_snapshot(audio_path, audio_name) as (audio, audio_snapshot):
        corroborated_audio_sha256 = str(dasheng_track["sourceAudioSha256"])
        if audio.sha256 != corroborated_audio_sha256:
            raise ValueError(f"Track {identifier!r} source audio differs from its Dasheng corroboration.")

        feature_artifact = _mapping(
            artifact_entry.get("featureArtifact"), f"winner track {identifier!r} featureArtifact"
        )
        expected_cache_sha256 = _required_sha256(
            feature_artifact.get("sha256"), f"winner track {identifier!r} featureArtifact.sha256"
        )
        expected_cache_bytes = _positive_integer(
            feature_artifact.get("bytes"), f"winner track {identifier!r} featureArtifact.bytes"
        )
        cache = _stable_file(
            cache_path,
            f"track {identifier!r} frozen feature cache",
            expected_suffixes=frozenset({".npz"}),
            capture_bytes=True,
        )
        if cache.sha256 != expected_cache_sha256 or cache.bytes != expected_cache_bytes:
            raise ValueError(f"Track {identifier!r} frozen cache file differs from artifactIntegrity.")
        if cache.captured is None:  # pragma: no cover - capture contract
            raise ValueError(f"Track {identifier!r} frozen cache bytes were not captured.")
        cached_raw = _load_cached_features(cache.captured, f"track {identifier!r} frozen feature cache")
        _assert_file_identity(cache, f"track {identifier!r} frozen feature cache")

        try:
            fresh_raw, fresh_duration_raw = extractor(audio_snapshot, FEATURE_KIND)
        except Exception as error:
            raise ValueError(f"Track {identifier!r} fresh multiband extraction failed.") from error
        _assert_file_identity(audio, audio_name)
    cached, cached_sha256 = _feature_bytes(cached_raw, f"track {identifier!r} cached features")
    fresh, fresh_sha256 = _feature_bytes(fresh_raw, f"track {identifier!r} fresh features")
    if cached_sha256 != fresh_sha256 or cached.tobytes(order="C") != fresh.tobytes(order="C"):
        raise ValueError(f"Track {identifier!r} fresh and frozen feature array bytes differ.")

    frames = _positive_integer(winner_track.get("frames"), f"winner track {identifier!r} frames")
    if cached.shape != (frames, FEATURE_COUNT) or fresh.shape != (frames, FEATURE_COUNT):
        raise ValueError(f"Track {identifier!r} frame/shape metadata differs from feature arrays.")
    if artifact_entry.get("frames") != frames:
        raise ValueError(f"Track {identifier!r} frame count differs from artifactIntegrity.")
    cached_duration = _finite_positive(
        winner_track.get("durationSeconds"), f"winner track {identifier!r} cached duration"
    )
    fresh_duration = _finite_positive(fresh_duration_raw, f"track {identifier!r} fresh duration")
    cached_ms = _canonical_milliseconds(cached_duration)
    fresh_ms = _canonical_milliseconds(fresh_duration)
    if cached_ms != fresh_ms:
        raise ValueError(f"Track {identifier!r} fresh and frozen canonical durations differ.")
    if _expected_frames(cached_duration) != frames or _expected_frames(fresh_duration) != frames:
        raise ValueError(f"Track {identifier!r} duration does not align with its exact 10 Hz frame count.")

    winner_sha, artifact_sha, source_sha, dasheng_sha, metadata_sha = _source_metadata_sha256(
        winner_track,
        artifact_entry,
        source_track,
        dasheng_track,
    )
    payload = {
        "trackId": identifier,
        "datasetId": str(winner_track["datasetId"]),
        "split": DEVELOPMENT_SPLIT,
        "audioPath": str(audio.path),
        "audioPathSha256": canonical_sha256(str(audio.path)),
        "sourceAudioSha256": audio.sha256,
        "sourceAudioBytes": audio.bytes,
        "cachedFeaturePath": str(cache.path),
        "cachedFeaturePathSha256": canonical_sha256(str(cache.path)),
        "cachedFeatureArtifactSha256": cache.sha256,
        "cachedFeatureArtifactBytes": cache.bytes,
        "cachedArraySha256": cached_sha256,
        "freshArraySha256": fresh_sha256,
        "frames": frames,
        "featureCount": FEATURE_COUNT,
        "elementCount": frames * FEATURE_COUNT,
        "cachedDurationSeconds": cached_duration,
        "freshDurationSeconds": fresh_duration,
        "canonicalDurationMilliseconds": cached_ms,
        "winnerTrackSha256": winner_sha,
        "winnerArtifactEntrySha256": artifact_sha,
        "sourceDescriptorSha256": source_sha,
        "dashengTrackSha256": dasheng_sha,
        "sourceMetadataSha256": metadata_sha,
    }
    return {**payload, "rowSha256": canonical_sha256(payload)}


def _set_hashes(rows: Sequence[Mapping[str, Any]]) -> tuple[str, str, str]:
    track_set = canonical_sha256([{"trackId": row["trackId"], "rowSha256": row["rowSha256"]} for row in rows])
    audio_set = canonical_sha256(
        [
            {
                "trackId": row["trackId"],
                "audioPathSha256": row["audioPathSha256"],
                "sourceAudioSha256": row["sourceAudioSha256"],
                "sourceAudioBytes": row["sourceAudioBytes"],
            }
            for row in rows
        ]
    )
    array_set = canonical_sha256(
        [
            {
                "trackId": row["trackId"],
                "cachedArraySha256": row["cachedArraySha256"],
                "freshArraySha256": row["freshArraySha256"],
                "frames": row["frames"],
                "featureCount": row["featureCount"],
            }
            for row in rows
        ]
    )
    return track_set, audio_set, array_set


def _render_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"


def _preflight_output(path: Path) -> Path:
    absolute = _lexical_absolute(path, name="audio lineage output")
    if absolute.suffix.lower() != ".json":
        raise ValueError("Audio lineage output must be a JSON file.")
    try:
        parent = _open_directory_fd(absolute.parent, "audio lineage output parent")
    except FileNotFoundError:
        return absolute
    try:
        try:
            os.stat(absolute.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("Audio lineage output must be a new, non-symlink path.")
    finally:
        os.close(parent)
    return absolute


def _read_relative_file(parent: int, name: str, label: str) -> bytes:
    descriptor: int | None = None
    try:
        descriptor = os.open(name, _file_flags(), dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"{label} must be a regular file.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if _stat_identity(before) != _stat_identity(after) or _stat_identity(before) != _stat_identity(linked):
            raise ValueError(f"{label} changed while it was read.")
        return b"".join(chunks)
    except ValueError:
        raise
    except OSError as error:
        raise ValueError(f"Could not securely read {label}.") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _unlink_owned_link(parent: int, name: str, identity: tuple[int, int]) -> None:
    try:
        linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    if (linked.st_dev, linked.st_ino) == identity:
        os.unlink(name, dir_fd=parent)


def _publish_new_json(path: Path, value: Mapping[str, Any]) -> None:
    rendered = _render_json(value).encode("utf-8")
    parent = _open_directory_fd(path.parent, "audio lineage output parent", create=True)
    temporary_name: str | None = None
    temporary_identity: tuple[int, int] | None = None
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("Audio lineage output appeared before atomic publication.")

        descriptor: int | None = None
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        for _attempt in range(128):
            candidate = f".{path.name}.{secrets.token_hex(16)}.tmp"
            try:
                descriptor = os.open(candidate, flags, 0o600, dir_fd=parent)
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if descriptor is None or temporary_name is None:  # pragma: no cover - 2**128 collision space
            raise ValueError("Could not allocate an exclusive audio lineage temporary file.")
        try:
            _write_all(descriptor, rendered)
            os.fsync(descriptor)
            temporary_stat = os.fstat(descriptor)
            if not stat.S_ISREG(temporary_stat.st_mode) or temporary_stat.st_size != len(rendered):
                raise ValueError("Audio lineage temporary file is incomplete.")
            temporary_identity = (temporary_stat.st_dev, temporary_stat.st_ino)
        finally:
            os.close(descriptor)

        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=parent,
                dst_dir_fd=parent,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise ValueError("Audio lineage output was concurrently created; refusing overwrite.") from error
        os.fsync(parent)
        if _read_relative_file(parent, path.name, "published audio lineage") != rendered:
            raise ValueError("Published audio lineage did not round-trip exactly.")
        current_parent = _open_directory_fd(path.parent, "published audio lineage parent")
        try:
            if (os.fstat(current_parent).st_dev, os.fstat(current_parent).st_ino) != (
                os.fstat(parent).st_dev,
                os.fstat(parent).st_ino,
            ):
                raise ValueError("Audio lineage output parent changed during publication.")
        finally:
            os.close(current_parent)
    except Exception:
        if temporary_identity is not None:
            _unlink_owned_link(parent, path.name, temporary_identity)
            os.fsync(parent)
        raise
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent)
                os.fsync(parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def build_development_audio_lineage(
    winner_cache_manifest_path: Path,
    development_source_manifest_path: Path,
    dasheng_cache_manifest_path: Path,
    output_path: Path,
    *,
    extractor: FeatureExtractor = extract_student_features,
    dependency_lock_path: Path = _DEFAULT_DEPENDENCY_LOCK,
    dependency_versions: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build and atomically publish exact development audio/cache lineage.

    The three input manifest files are authoritative; their hashes are derived
    from the bytes read here rather than supplied by a caller.  Nothing is
    published until every selected development track re-extracts successfully
    and matches its frozen float16 feature bytes exactly.
    """

    if extractor is extract_student_features and dependency_versions is not None:
        raise ValueError("The production extractor must derive installed dependency versions directly.")
    destination = _preflight_output(output_path)
    winner = _load_json(winner_cache_manifest_path, "winner cache manifest")
    source = _load_json(development_source_manifest_path, "development source manifest")
    dasheng = _load_json(dasheng_cache_manifest_path, "Dasheng cache manifest")
    feature_contract, prepared = _preflight_inputs(winner, source, dasheng)
    extractor_contract = _extractor_contract(
        extractor,
        feature_contract,
        dependency_lock_path=dependency_lock_path,
        dependency_versions=dependency_versions,
    )

    # Only after every manifest, split, id, cross-field, and lexical path has
    # passed do we touch the selected audio and frozen feature-cache files.
    for winner_track, _artifact, _source, _dasheng, audio_path, cache_path in prepared:
        identifier = str(winner_track["id"])
        _require_regular_file(audio_path, f"track {identifier!r} audioPath")
        _require_regular_file(cache_path, f"track {identifier!r} cache path")

    rows = [_build_row(item, extractor) for item in prepared]
    rows.sort(key=lambda row: str(row["trackId"]))
    track_set_sha256, audio_set_sha256, array_set_sha256 = _set_hashes(rows)
    manifest_bindings = _manifest_bindings(winner, source, dasheng)
    for role in (
        "winnerCacheManifest",
        "developmentSourceManifest",
        "dashengCacheManifest",
    ):
        _verify_binding_file(_mapping(manifest_bindings[role], role), role)
    _verify_extractor_files(extractor_contract, extractor, dependency_versions)
    payload = {
        "schemaVersion": AUDIO_LINEAGE_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "featureContract": feature_contract,
        "extractorContract": extractor_contract,
        "manifestBindings": manifest_bindings,
        "trackCount": len(rows),
        "tracks": rows,
        "trackSetSha256": track_set_sha256,
        "audioSetSha256": audio_set_sha256,
        "arraySetSha256": array_set_sha256,
    }
    artifact = {**payload, "artifactSha256": canonical_sha256(payload)}
    validate_development_audio_lineage(artifact, verify_files=False)
    _publish_new_json(destination, artifact)
    return json.loads(json.dumps(artifact, ensure_ascii=False, allow_nan=False))


def _validate_file_binding(value: Any, role: str) -> Mapping[str, Any]:
    binding = _mapping(value, role)
    _exact_keys(binding, _FILE_BINDING_KEYS, role)
    if binding.get("role") != role:
        raise ValueError(f"{role} role is invalid.")
    _required_string(binding.get("schemaVersion"), f"{role} schemaVersion")
    path = _required_string(binding.get("path"), f"{role} path")
    if binding.get("pathSha256") != canonical_sha256(path):
        raise ValueError(f"{role} path hash is invalid.")
    _required_sha256(binding.get("fileSha256"), f"{role} fileSha256")
    _positive_integer(binding.get("bytes"), f"{role} bytes")
    _required_sha256(binding.get("canonicalSha256"), f"{role} canonicalSha256")
    _lexical_absolute(path, name=f"{role} path")
    return binding


def _validate_feature_contract(value: Any) -> Mapping[str, Any]:
    contract = _mapping(value, "featureContract")
    _exact_keys(contract, _FEATURE_CONTRACT_KEYS, "featureContract")
    unsigned = {key: item for key, item in contract.items() if key != "contractSha256"}
    if contract.get("schemaVersion") != FEATURE_CONTRACT_SCHEMA or contract.get("contractSha256") != canonical_sha256(
        unsigned
    ):
        raise ValueError("Feature contract schema or hash is invalid.")
    expected = {
        "featureKind": FEATURE_KIND,
        "featureCount": FEATURE_COUNT,
        "sampleRate": SAMPLE_RATE,
        "frameSeconds": FRAME_SECONDS,
        "storageDtype": STORAGE_DTYPE,
    }
    if any(contract.get(key) != item for key, item in expected.items()):
        raise ValueError("Feature contract does not describe exact multiband float16 features.")
    _required_sha256(contract.get("featureSpecSha256"), "featureContract featureSpecSha256")
    return contract


def _validate_extractor_contract(value: Any, feature_contract: Mapping[str, Any]) -> Mapping[str, Any]:
    contract = _mapping(value, "extractorContract")
    _exact_keys(contract, _EXTRACTOR_CONTRACT_KEYS, "extractorContract")
    unsigned = {key: item for key, item in contract.items() if key != "contractSha256"}
    if contract.get("schemaVersion") != EXTRACTOR_CONTRACT_SCHEMA or contract.get("contractSha256") != canonical_sha256(
        unsigned
    ):
        raise ValueError("Extractor contract schema or hash is invalid.")
    _required_string(contract.get("entrypoint"), "extractorContract entrypoint")
    for label, path_field, path_hash_field, file_hash_field, bytes_field in (
        ("sourceFile", "sourceFile", "sourceFilePathSha256", "sourceFileSha256", "sourceFileBytes"),
        (
            "dependencyLock",
            "dependencyLockFile",
            "dependencyLockPathSha256",
            "dependencyLockSha256",
            "dependencyLockBytes",
        ),
    ):
        path = _required_string(contract.get(path_field), f"extractorContract {label}")
        if contract.get(path_hash_field) != canonical_sha256(path):
            raise ValueError(f"Extractor {label} path hash is invalid.")
        _lexical_absolute(path, name=f"extractorContract {label}")
        _required_sha256(contract.get(file_hash_field), f"extractorContract {file_hash_field}")
        _positive_integer(contract.get(bytes_field), f"extractorContract {bytes_field}")
    _required_sha256(contract.get("functionSourceSha256"), "extractor functionSourceSha256")
    dependencies = _mapping(contract.get("dependencies"), "extractor dependencies")
    if set(dependencies) != {"python", "librosa", "numpy", "scipy", "soundfile"} or any(
        not isinstance(item, str) or not item for item in dependencies.values()
    ):
        raise ValueError("Extractor dependency versions are incomplete.")
    if contract.get("dependenciesSha256") != canonical_sha256(dependencies):
        raise ValueError("Extractor dependency hash is invalid.")
    if contract.get("featureContractSha256") != feature_contract["contractSha256"]:
        raise ValueError("Extractor does not bind the feature contract.")
    return contract


def _validate_manifest_bindings(value: Any, feature_contract: Mapping[str, Any]) -> Mapping[str, Any]:
    bindings = _mapping(value, "manifestBindings")
    _exact_keys(bindings, _MANIFEST_BINDING_KEYS, "manifestBindings")
    if bindings.get("schemaVersion") != MANIFEST_BINDINGS_SCHEMA:
        raise ValueError("Manifest bindings schema is invalid.")
    _validate_file_binding(bindings.get("winnerCacheManifest"), "winnerCacheManifest")
    source = _validate_file_binding(bindings.get("developmentSourceManifest"), "developmentSourceManifest")
    dasheng = _validate_file_binding(bindings.get("dashengCacheManifest"), "dashengCacheManifest")
    if source.get("schemaVersion") != DATASET_DESCRIPTOR_SCHEMA or dasheng.get("schemaVersion") != DASHENG_CACHE_SCHEMA:
        raise ValueError("Manifest binding source schemas are invalid.")
    for name in (
        "winnerCacheOutputManifestSha256",
        "winnerCacheSourceManifestSha256",
        "winnerCacheArtifactSetSha256",
        "dashengFeatureSpecSha256",
    ):
        _required_sha256(bindings.get(name), f"manifestBindings {name}")
    if bindings.get("winnerCacheAudioBindingStatus") != "absent_repaired_by_fresh_array_equality_v1":
        raise ValueError("Winner cache audio-binding gap is not explicitly disclosed.")
    if bindings.get("dashengFeatureSpecSha256") == feature_contract.get("featureSpecSha256"):
        # The two feature families must remain independently identified.
        raise ValueError("Dasheng and multiband feature-spec hashes must not be conflated.")
    unsigned = {key: item for key, item in bindings.items() if key != "bindingsSha256"}
    if bindings.get("bindingsSha256") != canonical_sha256(unsigned):
        raise ValueError("Manifest bindings hash is invalid.")
    return bindings


def _validate_row(value: Any, index: int) -> Mapping[str, Any]:
    row = _mapping(value, f"tracks[{index}]")
    _exact_keys(row, _ROW_KEYS, f"tracks[{index}]")
    identifier = _required_string(row.get("trackId"), f"tracks[{index}].trackId")
    _required_string(row.get("datasetId"), f"track {identifier!r} datasetId")
    if row.get("split") != DEVELOPMENT_SPLIT:
        raise ValueError(f"Track {identifier!r} is not development-only.")
    for field in ("audioPath", "cachedFeaturePath"):
        path = _required_string(row.get(field), f"track {identifier!r} {field}")
        _lexical_absolute(path, name=f"track {identifier!r} {field}")
        if row.get(f"{field}Sha256") != canonical_sha256(path):
            raise ValueError(f"Track {identifier!r} {field} hash is invalid.")
    for field in (
        "sourceAudioSha256",
        "cachedFeatureArtifactSha256",
        "cachedArraySha256",
        "freshArraySha256",
        "winnerTrackSha256",
        "winnerArtifactEntrySha256",
        "sourceDescriptorSha256",
        "dashengTrackSha256",
        "sourceMetadataSha256",
    ):
        _required_sha256(row.get(field), f"track {identifier!r} {field}")
    if row.get("cachedArraySha256") != row.get("freshArraySha256"):
        raise ValueError(f"Track {identifier!r} fresh and cached array hashes differ.")
    frames = _positive_integer(row.get("frames"), f"track {identifier!r} frames")
    if row.get("featureCount") != FEATURE_COUNT or row.get("elementCount") != frames * FEATURE_COUNT:
        raise ValueError(f"Track {identifier!r} feature dimensions are invalid.")
    _positive_integer(row.get("sourceAudioBytes"), f"track {identifier!r} sourceAudioBytes")
    _positive_integer(row.get("cachedFeatureArtifactBytes"), f"track {identifier!r} cachedFeatureArtifactBytes")
    cached_duration = _finite_positive(row.get("cachedDurationSeconds"), f"track {identifier!r} cachedDurationSeconds")
    fresh_duration = _finite_positive(row.get("freshDurationSeconds"), f"track {identifier!r} freshDurationSeconds")
    milliseconds = _positive_integer(
        row.get("canonicalDurationMilliseconds"), f"track {identifier!r} canonicalDurationMilliseconds"
    )
    if (
        _canonical_milliseconds(cached_duration) != milliseconds
        or _canonical_milliseconds(fresh_duration) != milliseconds
    ):
        raise ValueError(f"Track {identifier!r} canonical duration is invalid.")
    if _expected_frames(cached_duration) != frames or _expected_frames(fresh_duration) != frames:
        raise ValueError(f"Track {identifier!r} duration and frames disagree.")
    expected_metadata_sha256 = canonical_sha256(
        {
            "winnerTrackSha256": row["winnerTrackSha256"],
            "winnerArtifactEntrySha256": row["winnerArtifactEntrySha256"],
            "sourceDescriptorSha256": row["sourceDescriptorSha256"],
            "dashengTrackSha256": row["dashengTrackSha256"],
        }
    )
    if row.get("sourceMetadataSha256") != expected_metadata_sha256:
        raise ValueError(f"Track {identifier!r} source metadata hash is invalid.")
    unsigned = {key: item for key, item in row.items() if key != "rowSha256"}
    if row.get("rowSha256") != canonical_sha256(unsigned):
        raise ValueError(f"Track {identifier!r} row hash is invalid.")
    return row


def _verify_binding_file(binding: Mapping[str, Any], name: str) -> None:
    identity = _stable_file(
        _lexical_absolute(str(binding["path"]), name=f"{name} path"),
        name,
        expected_suffixes=frozenset({".json"}),
        capture_bytes=True,
    )
    if identity.sha256 != binding["fileSha256"] or identity.bytes != binding["bytes"]:
        raise ValueError(f"{name} file bytes changed.")
    if identity.captured is None:  # pragma: no cover - capture contract
        raise ValueError(f"{name} bytes were not captured.")
    try:
        parsed = json.loads(identity.captured)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{name} is no longer valid JSON.") from error
    if canonical_sha256(parsed) != binding["canonicalSha256"]:
        raise ValueError(f"{name} canonical content changed.")


def _verify_manifest_inputs(
    bindings: Mapping[str, Any],
    feature_contract: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    winner = _load_json(
        Path(str(_mapping(bindings["winnerCacheManifest"], "winnerCacheManifest")["path"])),
        "winner cache manifest",
    )
    source = _load_json(
        Path(
            str(
                _mapping(
                    bindings["developmentSourceManifest"],
                    "developmentSourceManifest",
                )["path"]
            )
        ),
        "development source manifest",
    )
    dasheng = _load_json(
        Path(str(_mapping(bindings["dashengCacheManifest"], "dashengCacheManifest")["path"])),
        "Dasheng cache manifest",
    )
    derived_feature_contract, prepared = _preflight_inputs(winner, source, dasheng)
    if dict(derived_feature_contract) != dict(feature_contract):
        raise ValueError("Bound manifests no longer derive the sealed feature contract.")
    if _manifest_bindings(winner, source, dasheng) != bindings:
        raise ValueError("Bound manifest bytes no longer derive the sealed manifest bindings.")
    prepared_by_id = {str(item[0]["id"]): item for item in prepared}
    if set(prepared_by_id) != {str(row["trackId"]) for row in rows}:
        raise ValueError("Bound manifest development ids no longer match lineage rows.")
    for row in rows:
        identifier = str(row["trackId"])
        winner_track, artifact_entry, source_track, dasheng_track, audio_path, cache_path = prepared_by_id[identifier]
        winner_sha, artifact_sha, source_sha, dasheng_sha, metadata_sha = _source_metadata_sha256(
            winner_track,
            artifact_entry,
            source_track,
            dasheng_track,
        )
        expected = {
            "datasetId": str(winner_track["datasetId"]),
            "audioPath": str(audio_path),
            "audioPathSha256": canonical_sha256(str(audio_path)),
            "sourceAudioSha256": str(dasheng_track["sourceAudioSha256"]),
            "cachedFeaturePath": str(cache_path),
            "cachedFeaturePathSha256": canonical_sha256(str(cache_path)),
            "cachedFeatureArtifactSha256": artifact_entry["featureArtifact"]["sha256"],
            "cachedFeatureArtifactBytes": artifact_entry["featureArtifact"]["bytes"],
            "frames": int(winner_track["frames"]),
            "cachedDurationSeconds": float(winner_track["durationSeconds"]),
            "winnerTrackSha256": winner_sha,
            "winnerArtifactEntrySha256": artifact_sha,
            "sourceDescriptorSha256": source_sha,
            "dashengTrackSha256": dasheng_sha,
            "sourceMetadataSha256": metadata_sha,
        }
        if any(row.get(key) != item for key, item in expected.items()):
            raise ValueError(f"Track {identifier!r} no longer matches its bound manifest metadata.")


def _verify_extractor_files(
    contract: Mapping[str, Any],
    extractor: FeatureExtractor,
    dependency_versions: Mapping[str, str] | None,
) -> None:
    expected_entrypoint = f"{extractor.__module__}.{extractor.__qualname__}"
    if contract.get("entrypoint") != expected_entrypoint:
        raise ValueError("Verification extractor does not match the sealed entrypoint.")
    for label, path_field, hash_field, bytes_field in (
        ("sourceFile", "sourceFile", "sourceFileSha256", "sourceFileBytes"),
        (
            "dependencyLock",
            "dependencyLockFile",
            "dependencyLockSha256",
            "dependencyLockBytes",
        ),
    ):
        path = _lexical_absolute(str(contract[path_field]), name=f"extractor {label}")
        identity = _stable_file(path, f"extractor {label}")
        if identity.sha256 != contract[hash_field] or identity.bytes != contract[bytes_field]:
            raise ValueError(f"Extractor {label} bytes changed.")
    try:
        function_hash = hashlib.sha256(inspect.getsource(extractor).encode("utf-8")).hexdigest()
    except (OSError, TypeError) as error:
        raise ValueError("Verification extractor source cannot be inspected.") from error
    if function_hash != contract["functionSourceSha256"]:
        raise ValueError("Verification extractor function source changed.")
    if _dependency_versions(dependency_versions) != contract["dependencies"]:
        raise ValueError("Extraction dependency versions changed.")


def _verify_row_files(row: Mapping[str, Any], extractor: FeatureExtractor) -> None:
    identifier = str(row["trackId"])
    audio_path = _lexical_absolute(str(row["audioPath"]), name=f"track {identifier!r} audioPath")
    audio_name = f"track {identifier!r} source audio"
    with _private_audio_snapshot(audio_path, audio_name) as (audio, audio_snapshot):
        if audio.sha256 != row["sourceAudioSha256"] or audio.bytes != row["sourceAudioBytes"]:
            raise ValueError(f"Track {identifier!r} source audio changed.")
        cache = _stable_file(
            _lexical_absolute(str(row["cachedFeaturePath"]), name=f"track {identifier!r} cachedFeaturePath"),
            f"track {identifier!r} frozen feature cache",
            expected_suffixes=frozenset({".npz"}),
            capture_bytes=True,
        )
        if cache.sha256 != row["cachedFeatureArtifactSha256"] or cache.bytes != row["cachedFeatureArtifactBytes"]:
            raise ValueError(f"Track {identifier!r} frozen feature cache changed.")
        if cache.captured is None:  # pragma: no cover - capture contract
            raise ValueError(f"Track {identifier!r} frozen cache bytes were not captured.")
        cached_raw = _load_cached_features(cache.captured, f"track {identifier!r} frozen feature cache")
        _assert_file_identity(cache, f"track {identifier!r} frozen feature cache")
        try:
            fresh_raw, fresh_duration_raw = extractor(audio_snapshot, FEATURE_KIND)
        except Exception as error:
            raise ValueError(f"Track {identifier!r} verification extraction failed.") from error
        _assert_file_identity(audio, audio_name)
    cached, cached_sha256 = _feature_bytes(cached_raw, f"track {identifier!r} cached features")
    fresh, fresh_sha256 = _feature_bytes(fresh_raw, f"track {identifier!r} fresh features")
    if (
        cached.shape != (row["frames"], FEATURE_COUNT)
        or fresh.shape != cached.shape
        or cached_sha256 != row["cachedArraySha256"]
        or fresh_sha256 != row["freshArraySha256"]
        or cached.tobytes(order="C") != fresh.tobytes(order="C")
    ):
        raise ValueError(f"Track {identifier!r} feature arrays no longer match lineage.")
    fresh_duration = _finite_positive(fresh_duration_raw, f"track {identifier!r} fresh duration")
    if _canonical_milliseconds(fresh_duration) != row["canonicalDurationMilliseconds"]:
        raise ValueError(f"Track {identifier!r} fresh duration no longer matches lineage.")


def validate_development_audio_lineage(
    artifact: Mapping[str, Any],
    *,
    verify_files: bool = False,
    extractor: FeatureExtractor = extract_student_features,
    dependency_versions: Mapping[str, str] | None = None,
) -> Mapping[str, Any]:
    """Strictly validate a lineage artifact, optionally rehashing/re-extracting files."""

    if extractor is extract_student_features and dependency_versions is not None:
        raise ValueError("The production extractor must verify installed dependency versions directly.")
    value = _mapping(artifact, "audio lineage artifact")
    _exact_keys(value, _ROOT_KEYS, "audio lineage artifact")
    if value.get("schemaVersion") != AUDIO_LINEAGE_SCHEMA:
        raise ValueError(f"Audio lineage must use {AUDIO_LINEAGE_SCHEMA}.")
    if value.get("split") != DEVELOPMENT_SPLIT or value.get("developmentOnly") is not True:
        raise ValueError("Audio lineage must remain development-only.")
    if value.get("promotionEligible") is not False:
        raise ValueError("Development audio lineage is never promotion evidence by itself.")
    feature_contract = _validate_feature_contract(value.get("featureContract"))
    extractor_contract = _validate_extractor_contract(value.get("extractorContract"), feature_contract)
    bindings = _validate_manifest_bindings(value.get("manifestBindings"), feature_contract)
    raw_rows = _sequence(value.get("tracks"), "audio lineage tracks")
    rows = [_validate_row(row, index) for index, row in enumerate(raw_rows)]
    ids = [str(row["trackId"]) for row in rows]
    if not rows or ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ValueError("Audio lineage tracks must be nonempty, unique, and sorted by trackId.")
    if value.get("trackCount") != len(rows):
        raise ValueError("Audio lineage track count is invalid.")
    track_set, audio_set, array_set = _set_hashes(rows)
    if value.get("trackSetSha256") != track_set:
        raise ValueError("Audio lineage track-set hash is invalid.")
    if value.get("audioSetSha256") != audio_set:
        raise ValueError("Audio lineage audio-set hash is invalid.")
    if value.get("arraySetSha256") != array_set:
        raise ValueError("Audio lineage array-set hash is invalid.")
    unsigned = {key: item for key, item in value.items() if key != "artifactSha256"}
    if value.get("artifactSha256") != canonical_sha256(unsigned):
        raise ValueError("Audio lineage artifact hash is invalid.")

    if verify_files:
        # Metadata and every split are validated above before the first bound
        # manifest, audio, or feature-cache file is touched here.
        for role in ("winnerCacheManifest", "developmentSourceManifest", "dashengCacheManifest"):
            _verify_binding_file(_mapping(bindings[role], role), role)
        _verify_manifest_inputs(bindings, feature_contract, rows)
        _verify_extractor_files(extractor_contract, extractor, dependency_versions)
        for row in rows:
            _verify_row_files(row, extractor)
    return artifact


def project_development_audio_lineage(
    artifact: Mapping[str, Any],
    track_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Return a compact, sealed identity projection for benchmark/example joins."""

    validate_development_audio_lineage(artifact, verify_files=False)
    all_rows = {str(row["trackId"]): row for row in artifact["tracks"]}
    if track_ids is None:
        selected_ids = sorted(all_rows)
    else:
        selected_ids = [_required_string(item, "projection track id") for item in track_ids]
        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("Projection track ids must be unique.")
        unknown = sorted(set(selected_ids) - set(all_rows))
        if unknown:
            raise ValueError(f"Projection contains unknown audio-lineage track ids: {unknown}.")
        selected_ids.sort()
    if not selected_ids:
        raise ValueError("Audio-lineage projection may not be empty.")
    rows: list[dict[str, Any]] = []
    for identifier in selected_ids:
        source = all_rows[identifier]
        row = {
            "trackId": identifier,
            "datasetId": source["datasetId"],
            "sourceAudioSha256": source["sourceAudioSha256"],
            "cachedArraySha256": source["cachedArraySha256"],
            "freshArraySha256": source["freshArraySha256"],
            "canonicalDurationMilliseconds": source["canonicalDurationMilliseconds"],
            "rowSha256": source["rowSha256"],
        }
        _exact_keys(row, _PROJECTION_ROW_KEYS, f"projection track {identifier!r}")
        rows.append(row)
    track_set_sha256 = canonical_sha256(rows)
    bindings = _mapping(artifact["manifestBindings"], "manifestBindings")
    feature_contract = _mapping(artifact["featureContract"], "featureContract")
    payload = {
        "schemaVersion": AUDIO_LINEAGE_PROJECTION_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "sourceAudioLineageSha256": artifact["artifactSha256"],
        "manifestBindingsSha256": bindings["bindingsSha256"],
        "featureContractSha256": feature_contract["contractSha256"],
        "trackCount": len(rows),
        "tracks": rows,
        "trackSetSha256": track_set_sha256,
    }
    projection = {**payload, "projectionSha256": canonical_sha256(payload)}
    _exact_keys(projection, _PROJECTION_KEYS, "audio-lineage projection")
    return deepcopy(projection)


__all__ = [
    "AUDIO_LINEAGE_PROJECTION_SCHEMA",
    "AUDIO_LINEAGE_SCHEMA",
    "DATASET_DESCRIPTOR_SCHEMA",
    "build_development_audio_lineage",
    "project_development_audio_lineage",
    "validate_development_audio_lineage",
]
