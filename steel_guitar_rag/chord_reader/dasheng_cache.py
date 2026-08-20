"""Restartable, provenance-sealed Dasheng feature caches.

The cache deliberately defaults to the training and development splits.  A
held-out split requires both an explicit split selection and
``allow_held_out=True`` so a routine training-cache command cannot silently
materialize test features.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Collection, Iterable, Mapping, TypeAlias
import zipfile

from .dasheng import (
    DASHENG_FEATURE_COUNT,
    DASHENG_FEATURE_KIND,
    DASHENG_FRAME_SECONDS,
    DASHENG_NATIVE_FRAME_SECONDS,
    DASHENG_REQUIRED_FILES,
    DASHENG_SAMPLE_RATE,
    DEFAULT_DASHENG_CONTRACT,
    DashengFeatureBatch,
    dasheng_feature_provenance,
    get_dasheng_feature_extractor,
    load_dasheng_contract,
)
from .manifests import VALID_SPLITS, validate_track_manifest


DASHENG_CACHE_SCHEMA = "chord_feature_cache_v1"
DASHENG_FEATURE_SPEC_SCHEMA = "chord_reader_dasheng_feature_spec_v1"
DASHENG_CACHE_DEFAULT_SPLITS = frozenset({"train", "development"})
DASHENG_CACHE_HELD_OUT_SPLITS = frozenset({"test", "steel_test"})
DASHENG_CACHE_AUGMENTATION_POLICY = "none"
DASHENG_CACHE_STORAGE_DTYPE = "float16"

_SHA256_HEX = frozenset("0123456789abcdef")
_CACHE_ARRAYS = frozenset(
    {
        "schema_version",
        "track_id",
        "features",
        "timestamps_seconds",
        "duration_seconds",
        "training_weight",
        "source_audio_sha256",
        "source_feature_sha256",
        "feature_sha256",
        "feature_spec_sha256",
        "augmentation_policy",
    }
)

ManifestSource: TypeAlias = Mapping[str, Any] | str | Path


class DashengCacheError(ValueError):
    """A source track or cached feature artifact violates the sealed contract."""


@dataclass(frozen=True)
class _LoadedManifest:
    value: Mapping[str, Any]
    base_dir: Path
    source_path: Path | None
    sha256: str


@dataclass(frozen=True)
class _SelectedTrack:
    value: Mapping[str, Any]
    base_dir: Path


@dataclass(frozen=True)
class _AudioIdentity:
    path: Path
    sha256: str
    device: int
    inode: int
    size: int
    modified_ns: int


@dataclass(frozen=True)
class _CacheExpectation:
    track_id: str
    source_audio_sha256: str
    feature_spec_sha256: str
    training_weight: float
    declared_duration_seconds: float | None


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DashengCacheError(f"Dasheng cache metadata is not canonical JSON: {exc}") from exc


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _SHA256_HEX


def _is_revision(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and set(value) <= _SHA256_HEX


def _validated_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(provenance, Mapping):
        raise DashengCacheError("Dasheng extraction provenance must be an object.")
    expected = {
        "schemaVersion": "chord_reader_feature_provenance_v1",
        "featureKind": DASHENG_FEATURE_KIND,
        "modelId": "mispeech/dasheng-base",
        "sampleRate": DASHENG_SAMPLE_RATE,
        "nativeFrameSeconds": DASHENG_NATIVE_FRAME_SECONDS,
        "frameSeconds": DASHENG_FRAME_SECONDS,
        "featureCount": DASHENG_FEATURE_COUNT,
        "pooling": "interval_overlap_mean_v1",
        "timestampConvention": "left_edge_seconds_v1",
    }
    for key, expected_value in expected.items():
        if provenance.get(key) != expected_value:
            raise DashengCacheError(
                f"Dasheng provenance field {key!r} must be {expected_value!r}."
            )
    if not _is_revision(provenance.get("revision")):
        raise DashengCacheError("Dasheng provenance revision must be a full lowercase Git SHA.")
    license_contract = provenance.get("license")
    if not isinstance(license_contract, Mapping) or license_contract.get("spdx") != "Apache-2.0":
        raise DashengCacheError("Dasheng cache provenance must retain Apache-2.0 license evidence.")
    file_hashes = provenance.get("fileSha256")
    if not isinstance(file_hashes, Mapping) or set(file_hashes) != set(DASHENG_REQUIRED_FILES):
        raise DashengCacheError("Dasheng provenance must hash the complete sealed runtime allowlist.")
    if any(not _is_sha256(value) for value in file_hashes.values()):
        raise DashengCacheError("Every Dasheng runtime file must have a lowercase SHA-256.")
    if not _is_sha256(file_hashes.get("model.safetensors")):
        raise DashengCacheError("Dasheng provenance must include the model.safetensors SHA-256.")

    plain = dict(provenance)
    claimed = plain.pop("provenanceSha256", None)
    if not _is_sha256(claimed) or _canonical_sha256(plain) != claimed:
        raise DashengCacheError("Dasheng provenanceSha256 does not match its canonical payload.")
    # A canonical JSON round trip detaches nested mutable mappings from an
    # injected extractor without permitting NaN or non-JSON values.
    return json.loads(_canonical_json(dict(provenance)))


def dasheng_cache_feature_spec(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Build the exact, hash-addressed representation consumed by training."""

    sealed = _validated_provenance(provenance)
    spec = {
        "schemaVersion": DASHENG_FEATURE_SPEC_SCHEMA,
        "featureKind": sealed["featureKind"],
        "modelId": sealed["modelId"],
        "revision": sealed["revision"],
        "weightSha256": sealed["fileSha256"]["model.safetensors"],
        "runtimeFileSha256": {
            key: sealed["fileSha256"][key] for key in sorted(sealed["fileSha256"])
        },
        "sampleRate": sealed["sampleRate"],
        "nativeFrameSeconds": sealed["nativeFrameSeconds"],
        "frameSeconds": sealed["frameSeconds"],
        "featureCount": sealed["featureCount"],
        "pooling": sealed["pooling"],
        "timestampConvention": sealed["timestampConvention"],
        "storageDtype": DASHENG_CACHE_STORAGE_DTYPE,
        "augmentationPolicy": DASHENG_CACHE_AUGMENTATION_POLICY,
        "provenanceSha256": sealed["provenanceSha256"],
    }
    spec["featureSpecSha256"] = _canonical_sha256(spec)
    return spec


def _load_manifest(source: ManifestSource) -> _LoadedManifest:
    if isinstance(source, Mapping):
        value = source
        source_path = None
        base_dir = Path.cwd()
    else:
        source_path = Path(source).expanduser().resolve()
        try:
            value = json.loads(source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DashengCacheError(f"Could not read track manifest {source_path}: {exc}") from exc
        if not isinstance(value, Mapping):
            raise DashengCacheError(f"Track manifest {source_path} must contain a JSON object.")
        base_dir = source_path.parent
    try:
        validate_track_manifest(value)
    except (TypeError, ValueError) as exc:
        label = str(source_path) if source_path is not None else "in-memory manifest"
        raise DashengCacheError(f"Invalid {label}: {exc}") from exc
    return _LoadedManifest(
        value=value,
        base_dir=base_dir,
        source_path=source_path,
        sha256=_canonical_sha256(value),
    )


def _load_manifests(sources: ManifestSource | Iterable[ManifestSource]) -> list[_LoadedManifest]:
    if isinstance(sources, (Mapping, str, Path)):
        materialized: list[ManifestSource] = [sources]
    else:
        materialized = list(sources)
    if not materialized:
        raise DashengCacheError("At least one Dasheng track manifest is required.")
    return [_load_manifest(source) for source in materialized]


def _requested_splits(
    splits: Collection[str] | None,
    *,
    allow_held_out: bool,
) -> frozenset[str]:
    selected = DASHENG_CACHE_DEFAULT_SPLITS if splits is None else frozenset(str(item) for item in splits)
    if not selected:
        raise DashengCacheError("Dasheng cache split selection may not be empty.")
    invalid = selected - VALID_SPLITS
    if invalid:
        raise DashengCacheError(f"Unknown Dasheng cache splits: {sorted(invalid)}.")
    held_out = selected & DASHENG_CACHE_HELD_OUT_SPLITS
    if held_out and not allow_held_out:
        raise DashengCacheError(
            "Held-out Dasheng extraction requires explicit splits and allow_held_out=True; "
            f"refusing {sorted(held_out)}."
        )
    return frozenset(selected)


def _select_tracks(
    manifests: Iterable[_LoadedManifest],
    splits: Collection[str],
) -> list[_SelectedTrack]:
    identifiers: set[str] = set()
    split_by_group: dict[str, str] = {}
    selected: list[_SelectedTrack] = []
    for manifest in manifests:
        for raw_track in manifest.value["tracks"]:
            identifier = str(raw_track["id"])
            if identifier in identifiers:
                raise DashengCacheError(f"Duplicate source track id {identifier!r} across manifests.")
            identifiers.add(identifier)
            group = str(raw_track["splitGroup"])
            split = str(raw_track["split"])
            previous = split_by_group.setdefault(group, split)
            if previous != split:
                raise DashengCacheError(
                    f"Cross-manifest split leakage: group {group!r} appears in {previous!r} and {split!r}."
                )
            if split in splits:
                selected.append(_SelectedTrack(value=raw_track, base_dir=manifest.base_dir))
    if not selected:
        raise DashengCacheError(f"No tracks matched requested splits {sorted(splits)}.")
    return sorted(selected, key=lambda item: (str(item.value["datasetId"]), str(item.value["id"])))


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _audio_identity(track: _SelectedTrack) -> _AudioIdentity:
    raw_path = str(track.value.get("audioPath", "")).strip()
    if not raw_path:
        raise DashengCacheError(f"Track {track.value['id']!r} has no audioPath.")
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = track.base_dir / candidate
    try:
        path = candidate.resolve(strict=True)
    except OSError as exc:
        raise DashengCacheError(f"Track {track.value['id']!r} audio is unavailable: {candidate}") from exc
    if not path.is_file():
        raise DashengCacheError(f"Track {track.value['id']!r} audio is not a regular file: {path}")
    before = path.stat()
    sha256 = _hash_file(path)
    after = path.stat()
    state_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    state_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if state_before != state_after:
        raise DashengCacheError(f"Track {track.value['id']!r} audio changed while it was hashed.")
    return _AudioIdentity(
        path=path,
        sha256=sha256,
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
        modified_ns=after.st_mtime_ns,
    )


def _assert_audio_unchanged(identity: _AudioIdentity, track_id: str) -> None:
    current = identity.path.stat()
    state = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
    expected = (identity.device, identity.inode, identity.size, identity.modified_ns)
    if state != expected:
        raise DashengCacheError(f"Track {track_id!r} audio changed during feature extraction.")


def _finite_positive(value: object, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DashengCacheError(f"{label} must be a finite positive number.") from exc
    if not math.isfinite(result) or result <= 0:
        raise DashengCacheError(f"{label} must be a finite positive number.")
    return result


def _training_weight(track: Mapping[str, Any]) -> float:
    try:
        weight = float(track.get("trainingWeight", 1.0))
    except (TypeError, ValueError) as exc:
        raise DashengCacheError(f"Track {track['id']!r} has an invalid trainingWeight.") from exc
    if not math.isfinite(weight) or weight < 0:
        raise DashengCacheError(f"Track {track['id']!r} trainingWeight must be finite and non-negative.")
    return weight


def _declared_duration(track: Mapping[str, Any]) -> float | None:
    value = track.get("durationSeconds")
    return None if value is None else _finite_positive(value, f"Track {track['id']!r} durationSeconds")


def _safe_track_filename(identifier: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", identifier).strip(".-_")[:72] or "track"
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:16]
    return f"{slug}-{digest}.npz"


def _scalar(array: Any, key: str) -> Any:
    if getattr(array, "shape", None) != ():
        raise DashengCacheError(f"Dasheng cache array {key!r} must be scalar.")
    return array.item()


def _validate_archive(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise DashengCacheError(f"Dasheng cache path must be a regular, non-symlink file: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise DashengCacheError(f"Dasheng cache is not a valid NPZ archive: {path}") from exc
    expected_names = {f"{name}.npy" for name in _CACHE_ARRAYS}
    names = [info.filename for info in infos]
    if len(names) != len(set(names)) or set(names) != expected_names:
        raise DashengCacheError(f"Dasheng cache {path} has unexpected or duplicate NPZ members.")
    for info in infos:
        if info.flag_bits & 0x1 or info.compress_type != zipfile.ZIP_DEFLATED:
            raise DashengCacheError(f"Dasheng cache {path} must use unencrypted DEFLATE members.")


def _validate_cached_npz(path: Path, expected: _CacheExpectation) -> dict[str, Any]:
    numpy = __import__("numpy")
    _validate_archive(path)
    try:
        with numpy.load(path, allow_pickle=False) as cached:
            if set(cached.files) != set(_CACHE_ARRAYS):
                raise DashengCacheError(f"Dasheng cache {path} has an unexpected array allowlist.")
            for name in cached.files:
                if cached[name].dtype.hasobject:
                    raise DashengCacheError(f"Dasheng cache {path} contains unsafe object array {name!r}.")
            if _scalar(cached["schema_version"], "schema_version") != DASHENG_CACHE_SCHEMA:
                raise DashengCacheError(f"Dasheng cache {path} has the wrong schema version.")
            if _scalar(cached["track_id"], "track_id") != expected.track_id:
                raise DashengCacheError(f"Dasheng cache {path} belongs to a different track.")
            if _scalar(cached["source_audio_sha256"], "source_audio_sha256") != expected.source_audio_sha256:
                raise DashengCacheError(f"Dasheng cache {path} was built from different audio bytes.")
            if _scalar(cached["feature_spec_sha256"], "feature_spec_sha256") != expected.feature_spec_sha256:
                raise DashengCacheError(f"Dasheng cache {path} uses a different feature specification.")
            if _scalar(cached["augmentation_policy"], "augmentation_policy") != DASHENG_CACHE_AUGMENTATION_POLICY:
                raise DashengCacheError(f"Dasheng cache {path} has a non-none augmentation policy.")

            features = cached["features"]
            if features.dtype != numpy.dtype("float16"):
                raise DashengCacheError(f"Dasheng cache {path} features must be float16.")
            if features.ndim != 2 or features.shape[1] != DASHENG_FEATURE_COUNT or features.shape[0] < 1:
                raise DashengCacheError(
                    f"Dasheng cache {path} features must have shape (frames, {DASHENG_FEATURE_COUNT})."
                )
            if not numpy.isfinite(features).all():
                raise DashengCacheError(f"Dasheng cache {path} features contain non-finite values.")
            duration = _finite_positive(
                _scalar(cached["duration_seconds"], "duration_seconds"),
                f"Dasheng cache {path} duration_seconds",
            )
            expected_frames = max(1, math.ceil(duration / DASHENG_FRAME_SECONDS))
            if len(features) != expected_frames:
                raise DashengCacheError(
                    f"Dasheng cache {path} has {len(features)} frames; duration requires {expected_frames}."
                )
            timestamps = cached["timestamps_seconds"]
            expected_timestamps = numpy.arange(expected_frames, dtype=numpy.float64) * DASHENG_FRAME_SECONDS
            if timestamps.shape != (expected_frames,) or not numpy.isfinite(timestamps).all():
                raise DashengCacheError(f"Dasheng cache {path} timestamps do not align with its frames.")
            if not numpy.allclose(timestamps, expected_timestamps, rtol=0.0, atol=1e-9):
                raise DashengCacheError(f"Dasheng cache {path} is not aligned to the exact 10 Hz grid.")
            if expected.declared_duration_seconds is not None and not math.isclose(
                duration,
                expected.declared_duration_seconds,
                rel_tol=0.0,
                abs_tol=DASHENG_FRAME_SECONDS + 1e-9,
            ):
                raise DashengCacheError(
                    f"Dasheng cache {path} audio duration differs from the track manifest by more than one frame."
                )
            training_weight = float(_scalar(cached["training_weight"], "training_weight"))
            if not math.isclose(training_weight, expected.training_weight, rel_tol=0.0, abs_tol=1e-6):
                raise DashengCacheError(f"Dasheng cache {path} has a stale training weight.")
            feature_sha256 = str(_scalar(cached["feature_sha256"], "feature_sha256"))
            actual_feature_sha256 = hashlib.sha256(
                numpy.ascontiguousarray(features, dtype="<f2").tobytes()
            ).hexdigest()
            if not _is_sha256(feature_sha256) or feature_sha256 != actual_feature_sha256:
                raise DashengCacheError(f"Dasheng cache {path} feature content hash does not match.")
            source_feature_sha256 = str(
                _scalar(cached["source_feature_sha256"], "source_feature_sha256")
            )
            if not _is_sha256(source_feature_sha256):
                raise DashengCacheError(f"Dasheng cache {path} has an invalid source feature hash.")
    except DashengCacheError:
        raise
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise DashengCacheError(f"Could not safely read Dasheng cache {path}: {exc}") from exc
    return {
        "frames": expected_frames,
        "durationSeconds": duration,
        "featureSha256": feature_sha256,
        "sourceFeatureSha256": source_feature_sha256,
    }


def _prepare_batch(
    batch: DashengFeatureBatch,
    *,
    expected_spec: Mapping[str, Any],
    expected: _CacheExpectation,
) -> dict[str, Any]:
    numpy = __import__("numpy")
    if not isinstance(batch, DashengFeatureBatch):
        raise DashengCacheError("Dasheng extractors must return DashengFeatureBatch.")
    batch_spec = dasheng_cache_feature_spec(batch.provenance)
    if batch_spec["featureSpecSha256"] != expected_spec["featureSpecSha256"]:
        raise DashengCacheError("A Dasheng batch did not match the cache feature specification.")
    duration = _finite_positive(batch.duration_seconds, f"Track {expected.track_id!r} extracted duration")
    if expected.declared_duration_seconds is not None and not math.isclose(
        duration,
        expected.declared_duration_seconds,
        rel_tol=0.0,
        abs_tol=DASHENG_FRAME_SECONDS + 1e-9,
    ):
        raise DashengCacheError(
            f"Track {expected.track_id!r} extracted duration differs from its manifest by more than one frame."
        )
    features = numpy.asarray(batch.features, dtype=numpy.float32)
    expected_frames = max(1, math.ceil(duration / DASHENG_FRAME_SECONDS))
    if features.shape != (expected_frames, DASHENG_FEATURE_COUNT):
        raise DashengCacheError(
            f"Track {expected.track_id!r} produced shape {features.shape}; "
            f"expected ({expected_frames}, {DASHENG_FEATURE_COUNT})."
        )
    if not numpy.isfinite(features).all():
        raise DashengCacheError(f"Track {expected.track_id!r} produced non-finite Dasheng features.")
    timestamps = numpy.asarray(batch.timestamps_seconds, dtype=numpy.float64)
    expected_timestamps = numpy.arange(expected_frames, dtype=numpy.float64) * DASHENG_FRAME_SECONDS
    if timestamps.shape != (expected_frames,) or not numpy.isfinite(timestamps).all():
        raise DashengCacheError(f"Track {expected.track_id!r} timestamps do not align with its features.")
    if not numpy.allclose(timestamps, expected_timestamps, rtol=0.0, atol=1e-9):
        raise DashengCacheError(f"Track {expected.track_id!r} is not on the exact 10 Hz timestamp grid.")
    with numpy.errstate(over="ignore", invalid="ignore"):
        stored_features = features.astype(numpy.float16)
    if not numpy.isfinite(stored_features).all():
        raise DashengCacheError(
            f"Track {expected.track_id!r} cannot be represented safely as float16 features."
        )
    source_feature_sha256 = hashlib.sha256(
        numpy.ascontiguousarray(features, dtype="<f4").tobytes()
    ).hexdigest()
    feature_sha256 = hashlib.sha256(
        numpy.ascontiguousarray(stored_features, dtype="<f2").tobytes()
    ).hexdigest()
    return {
        "schema_version": numpy.asarray(DASHENG_CACHE_SCHEMA),
        "track_id": numpy.asarray(expected.track_id),
        "features": stored_features,
        "timestamps_seconds": timestamps,
        "duration_seconds": numpy.asarray(duration, dtype=numpy.float64),
        "training_weight": numpy.asarray(expected.training_weight, dtype=numpy.float32),
        "source_audio_sha256": numpy.asarray(expected.source_audio_sha256),
        "source_feature_sha256": numpy.asarray(source_feature_sha256),
        "feature_sha256": numpy.asarray(feature_sha256),
        "feature_spec_sha256": numpy.asarray(expected.feature_spec_sha256),
        "augmentation_policy": numpy.asarray(DASHENG_CACHE_AUGMENTATION_POLICY),
    }


def _atomic_npz(path: Path, arrays: Mapping[str, Any], expected: _CacheExpectation) -> dict[str, Any]:
    numpy = __import__("numpy")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise DashengCacheError(f"Refusing to replace symlinked Dasheng cache path {path}.")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            numpy.savez_compressed(output, **arrays)
            output.flush()
            os.fsync(output.fileno())
        metadata = _validate_cached_npz(temporary, expected)
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return metadata
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise DashengCacheError(f"Refusing to replace symlinked Dasheng manifest path {path}.")
    payload = f"{json.dumps(value, indent=2, sort_keys=True, allow_nan=False)}\n".encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        # Fail before replacement if serialization somehow did not round-trip.
        parsed = json.loads(temporary.read_text(encoding="utf-8"))
        if parsed != value:
            raise DashengCacheError("Atomic Dasheng manifest did not round-trip exactly.")
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()


def cache_dasheng_features(
    track_manifests: ManifestSource | Iterable[ManifestSource],
    output_root: Path,
    *,
    splits: Collection[str] | None = None,
    allow_held_out: bool = False,
    overwrite: bool = False,
    extractor: Any | None = None,
    snapshot_root: Path | None = None,
    contract_path: Path = DEFAULT_DASHENG_CONTRACT,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Cache deterministic 10 Hz Dasheng features for one or more manifests.

    Valid existing track files are reused byte-for-byte.  A stale or damaged
    file fails closed unless ``overwrite=True``.  Each NPZ is validated before
    its atomic rename, and the JSON manifest is written only after every
    selected track is complete.  No model checkpoint is downloaded here;
    production extraction accepts only the separately verified local snapshot.
    """

    selected_splits = _requested_splits(splits, allow_held_out=allow_held_out)
    manifests = _load_manifests(track_manifests)
    tracks = _select_tracks(manifests, selected_splits)
    if extractor is not None and snapshot_root is not None:
        raise DashengCacheError("Provide either an injected extractor or snapshot_root, not both.")
    if extractor is None:
        provenance = dasheng_feature_provenance(load_dasheng_contract(contract_path))
    else:
        provenance = getattr(extractor, "provenance", None)
        if not isinstance(provenance, Mapping):
            raise DashengCacheError("An injected Dasheng extractor must expose sealed provenance.")
    feature_spec = dasheng_cache_feature_spec(provenance)

    root = Path(output_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    emitted_manifest_path = (
        root / "manifest.json"
        if manifest_path is None
        else Path(manifest_path).expanduser().resolve()
    )
    lazy_extractor = extractor
    cached_tracks: list[dict[str, Any]] = []
    for selected in tracks:
        track = selected.value
        identifier = str(track["id"])
        audio = _audio_identity(selected)
        weight = _training_weight(track)
        declared_duration = _declared_duration(track)
        expectation = _CacheExpectation(
            track_id=identifier,
            source_audio_sha256=audio.sha256,
            feature_spec_sha256=str(feature_spec["featureSpecSha256"]),
            training_weight=weight,
            declared_duration_seconds=declared_duration,
        )
        split_directory = root / str(track["split"])
        split_directory.mkdir(parents=True, exist_ok=True)
        if os.path.commonpath((str(root), str(split_directory.resolve()))) != str(root):
            raise DashengCacheError(f"Track {identifier!r} resolved outside the Dasheng cache root.")
        path = split_directory / _safe_track_filename(identifier)
        if path.exists() and not overwrite:
            try:
                metadata = _validate_cached_npz(path, expectation)
            except DashengCacheError as exc:
                raise DashengCacheError(
                    f"Existing Dasheng cache for {identifier!r} is stale or invalid; "
                    "rerun with overwrite=True only after reviewing the source change."
                ) from exc
        else:
            if lazy_extractor is None:
                if snapshot_root is None:
                    raise DashengCacheError(
                        "Dasheng extraction needs a verified snapshot_root when no extractor is injected."
                    )
                lazy_extractor = get_dasheng_feature_extractor(
                    Path(snapshot_root), contract_path=Path(contract_path)
                )
                live_spec = dasheng_cache_feature_spec(lazy_extractor.provenance)
                if live_spec["featureSpecSha256"] != feature_spec["featureSpecSha256"]:
                    raise DashengCacheError("Verified Dasheng snapshot does not match the requested contract.")
            batch = lazy_extractor.extract(audio.path)
            _assert_audio_unchanged(audio, identifier)
            arrays = _prepare_batch(batch, expected_spec=feature_spec, expected=expectation)
            metadata = _atomic_npz(path, arrays, expectation)
        cached_tracks.append(
            {
                "id": identifier,
                "datasetId": str(track["datasetId"]),
                "split": str(track["split"]),
                "path": str(path.resolve()),
                "frames": int(metadata["frames"]),
                "durationSeconds": float(metadata["durationSeconds"]),
                "audioPath": str(audio.path),
                "sourceAudioSha256": audio.sha256,
                "sourceFeatureSha256": str(metadata["sourceFeatureSha256"]),
                "featureSha256": str(metadata["featureSha256"]),
                "featureSpecSha256": str(feature_spec["featureSpecSha256"]),
            }
        )

    source_manifests = []
    for loaded in manifests:
        source_manifests.append(
            {
                "sha256": loaded.sha256,
                **(
                    {"path": str(loaded.source_path)}
                    if loaded.source_path is not None
                    else {}
                ),
            }
        )
    output = {
        "schemaVersion": DASHENG_CACHE_SCHEMA,
        "sampleRate": DASHENG_SAMPLE_RATE,
        "frameSeconds": DASHENG_FRAME_SECONDS,
        "featureKind": DASHENG_FEATURE_KIND,
        "featureCount": DASHENG_FEATURE_COUNT,
        "modelId": feature_spec["modelId"],
        "revision": feature_spec["revision"],
        "weightSha256": feature_spec["weightSha256"],
        "featureSpecSha256": feature_spec["featureSpecSha256"],
        "augmentationPolicy": DASHENG_CACHE_AUGMENTATION_POLICY,
        "storageDtype": DASHENG_CACHE_STORAGE_DTYPE,
        "selectedSplits": sorted(selected_splits),
        "heldOutExtractionAuthorized": bool(
            selected_splits & DASHENG_CACHE_HELD_OUT_SPLITS and allow_held_out
        ),
        "featureSpec": feature_spec,
        "sourceManifests": source_manifests,
        "datasets": sorted({str(item["datasetId"]) for item in cached_tracks}),
        "tracks": cached_tracks,
    }
    _atomic_json(emitted_manifest_path, output)
    return output


__all__ = [
    "DASHENG_CACHE_AUGMENTATION_POLICY",
    "DASHENG_CACHE_DEFAULT_SPLITS",
    "DASHENG_CACHE_HELD_OUT_SPLITS",
    "DASHENG_CACHE_SCHEMA",
    "DASHENG_CACHE_STORAGE_DTYPE",
    "DASHENG_FEATURE_SPEC_SCHEMA",
    "DashengCacheError",
    "cache_dasheng_features",
    "dasheng_cache_feature_spec",
]
