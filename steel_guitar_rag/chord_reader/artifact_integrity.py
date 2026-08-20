"""Tamper-evident seals for factorized feature and label artifacts.

The seal reads only the cached NPZ files named by a factorized manifest.  It
never opens source audio, references, or any other provenance path.  Split
protocol manifests are signed separately, so a cache must be sealed first and
then repartitioned/frozen.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping
import zipfile


FACTORIZED_LABEL_SCHEMA = "chord_factorized_label_cache_v2"
FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA = "chord_factorized_artifact_integrity_v1"
FRAME_SECONDS = 0.1

_VALID_SPLITS = frozenset({"train", "development", "calibration", "test", "steel_test"})
_SHA256_HEX = frozenset("0123456789abcdef")
_BROWSER_FEATURE_ARRAYS = (
    frozenset({"features", "labels", "training_weight"}),
    frozenset({"features", "labels", "label_valid", "training_weight"}),
)
_DASHENG_FEATURE_ARRAYS = frozenset(
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
_FACTORIZED_LABEL_ARRAYS = frozenset(
    {
        "root",
        "mode",
        "product",
        "structure",
        "quality",
        "bass",
        "boundary",
        "label_valid",
    }
)
_FEATURE_CONTRACTS = {
    "worker_chroma_v1": (13, 11_025, _BROWSER_FEATURE_ARRAYS),
    "multiband_chroma_v2": (61, 11_025, _BROWSER_FEATURE_ARRAYS),
    "basic_pitch_v1": (177, 11_025, _BROWSER_FEATURE_ARRAYS),
    "harmonic_cqt_v3": (145, 11_025, _BROWSER_FEATURE_ARRAYS),
    "dasheng_base_v1": (768, 16_000, _DASHENG_FEATURE_ARRAYS),
}


class FactorizedArtifactIntegrityError(ValueError):
    """A factorized cache artifact violates its sealed file contract."""


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise FactorizedArtifactIntegrityError(
            "Factorized artifact metadata must be canonical JSON."
        ) from exc


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value) <= _SHA256_HEX
    )


def _manifest_contract(
    manifest: Mapping[str, Any],
    *,
    allow_missing_feature_spec: bool = False,
) -> dict[str, Any]:
    if manifest.get("schemaVersion") != FACTORIZED_LABEL_SCHEMA:
        raise FactorizedArtifactIntegrityError(
            f"Artifact sealing requires {FACTORIZED_LABEL_SCHEMA}."
        )
    feature_kind = str(manifest.get("featureKind", ""))
    if feature_kind not in _FEATURE_CONTRACTS:
        raise FactorizedArtifactIntegrityError(
            f"Unsupported factorized feature kind {feature_kind!r}."
        )
    expected_count, expected_rate, _arrays = _FEATURE_CONTRACTS[feature_kind]
    try:
        feature_count = int(manifest["featureCount"])
        sample_rate = int(manifest["sampleRate"])
        frame_seconds = float(manifest["frameSeconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FactorizedArtifactIntegrityError(
            "Factorized feature contract is incomplete."
        ) from exc
    if feature_count != expected_count or sample_rate != expected_rate:
        raise FactorizedArtifactIntegrityError(
            "Factorized feature count or sample rate does not match its feature kind."
        )
    if not math.isclose(frame_seconds, FRAME_SECONDS, rel_tol=0.0, abs_tol=1e-12):
        raise FactorizedArtifactIntegrityError(
            "Factorized artifacts must use the exact 0.1-second frame grid."
        )
    base_contract = {
        "schemaVersion": FACTORIZED_LABEL_SCHEMA,
        "featureKind": feature_kind,
        "featureCount": feature_count,
        "sampleRate": sample_rate,
        "frameSeconds": frame_seconds,
    }
    feature_spec_sha256 = manifest.get("featureSpecSha256")
    if feature_spec_sha256 is None and allow_missing_feature_spec:
        feature_spec_sha256 = _canonical_sha256(
            {"schemaVersion": "chord_feature_spec_v1", **base_contract}
        )
    if not _is_sha256(feature_spec_sha256):
        raise FactorizedArtifactIntegrityError(
            "Sealed factorized artifacts require an explicit featureSpecSha256."
        )
    return {**base_contract, "featureSpecSha256": feature_spec_sha256}


def _safe_path(value: Any, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise FactorizedArtifactIntegrityError(f"{label} path must be a non-empty string.")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise FactorizedArtifactIntegrityError(f"{label} path must be absolute and normalized.")
    absolute = Path(os.path.abspath(path))
    for component in (absolute, *absolute.parents):
        if component.is_symlink():
            raise FactorizedArtifactIntegrityError(
                f"{label} path contains a symlink: {component}"
            )
    if not absolute.is_file():
        raise FactorizedArtifactIntegrityError(
            f"{label} path must be a regular file: {absolute}"
        )
    return absolute


def _expected_array_sets(
    expected: frozenset[str] | tuple[frozenset[str], ...],
) -> tuple[frozenset[str], ...]:
    return expected if isinstance(expected, tuple) else (expected,)


def _archive_members(
    path: Path,
    expected: frozenset[str] | tuple[frozenset[str], ...],
    *,
    label: str,
) -> frozenset[str]:
    expected_sets = _expected_array_sets(expected)
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise FactorizedArtifactIntegrityError(f"{label} is not a valid NPZ: {path}") from exc
    names = [info.filename for info in infos]
    actual = frozenset(name.removesuffix(".npy") for name in names)
    valid_suffixes = all(name.endswith(".npy") for name in names)
    if (
        len(names) != len(set(names))
        or not valid_suffixes
        or actual not in expected_sets
    ):
        raise FactorizedArtifactIntegrityError(
            f"{label} has an unexpected, duplicate, or unsafe NPZ member allowlist."
        )
    for info in infos:
        if (
            info.flag_bits & 0x1
            or info.compress_type != zipfile.ZIP_DEFLATED
            or info.is_dir()
        ):
            raise FactorizedArtifactIntegrityError(
                f"{label} must contain only unencrypted DEFLATE NPY members."
            )
    return actual


def _load_arrays(
    path: Path,
    expected: frozenset[str] | tuple[frozenset[str], ...],
    *,
    label: str,
) -> dict[str, Any]:
    numpy = __import__("numpy")
    actual = _archive_members(path, expected, label=label)
    try:
        with numpy.load(path, allow_pickle=False) as archive:
            if set(archive.files) != set(actual):
                raise FactorizedArtifactIntegrityError(
                    f"{label} has an unexpected array allowlist."
                )
            arrays = {name: archive[name] for name in sorted(actual)}
    except FactorizedArtifactIntegrityError:
        raise
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        message = str(exc).lower()
        detail = "unsafe object array" if "object array" in message else "unreadable array"
        raise FactorizedArtifactIntegrityError(f"{label} contains an {detail}.") from exc
    if any(array.dtype.hasobject for array in arrays.values()):
        raise FactorizedArtifactIntegrityError(f"{label} contains an unsafe object array.")
    return arrays


def _scalar(array: Any, name: str, *, label: str) -> Any:
    if getattr(array, "shape", None) != ():
        raise FactorizedArtifactIntegrityError(f"{label} array {name!r} must be scalar.")
    return array.item()


def _finite_nonnegative(value: Any, *, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FactorizedArtifactIntegrityError(f"{label} must be numeric.") from exc
    if not math.isfinite(result) or result < 0:
        raise FactorizedArtifactIntegrityError(f"{label} must be finite and non-negative.")
    return result


def _expected_frames(duration: float) -> int:
    return max(1, math.ceil(duration / FRAME_SECONDS - 1e-12))


def _validate_feature_arrays(
    arrays: Mapping[str, Any],
    *,
    track: Mapping[str, Any],
    contract: Mapping[str, Any],
    label: str,
) -> int:
    numpy = __import__("numpy")
    identifier = str(track["id"])
    features = arrays["features"]
    if (
        features.dtype != numpy.dtype("float16")
        or features.ndim != 2
        or features.shape[0] < 1
        or features.shape[1] != int(contract["featureCount"])
    ):
        raise FactorizedArtifactIntegrityError(
            f"{label} features must be float16 with exact frame/feature dimensions."
        )
    if not numpy.isfinite(features).all():
        raise FactorizedArtifactIntegrityError(f"{label} features contain non-finite values.")
    frames = int(features.shape[0])
    if int(track.get("frames", -1)) != frames:
        raise FactorizedArtifactIntegrityError(
            f"Track {identifier!r} manifest frame count does not match its feature NPZ."
        )
    training_weight = _finite_nonnegative(
        _scalar(arrays["training_weight"], "training_weight", label=label),
        label=f"{label} training_weight",
    )
    if not math.isfinite(training_weight):  # pragma: no cover - guarded above
        raise FactorizedArtifactIntegrityError(f"{label} training weight is invalid.")

    if contract["featureKind"] == "dasheng_base_v1":
        if _scalar(arrays["schema_version"], "schema_version", label=label) != "chord_feature_cache_v1":
            raise FactorizedArtifactIntegrityError(f"{label} has the wrong cache schema.")
        if _scalar(arrays["track_id"], "track_id", label=label) != identifier:
            raise FactorizedArtifactIntegrityError(
                f"{label} belongs to a different track id (path swap)."
            )
        if _scalar(arrays["augmentation_policy"], "augmentation_policy", label=label) != "none":
            raise FactorizedArtifactIntegrityError(f"{label} has a non-none augmentation policy.")
        duration = _finite_nonnegative(
            _scalar(arrays["duration_seconds"], "duration_seconds", label=label),
            label=f"{label} duration_seconds",
        )
        if duration <= 0 or _expected_frames(duration) != frames:
            raise FactorizedArtifactIntegrityError(
                f"{label} duration does not align with its 10 Hz feature frames."
            )
        timestamps = arrays["timestamps_seconds"]
        expected_timestamps = numpy.arange(frames, dtype=numpy.float64) * FRAME_SECONDS
        if (
            timestamps.shape != (frames,)
            or not numpy.isfinite(timestamps).all()
            or not numpy.allclose(timestamps, expected_timestamps, rtol=0.0, atol=1e-9)
        ):
            raise FactorizedArtifactIntegrityError(
                f"{label} timestamps do not match the exact 10 Hz grid."
            )
        internal_feature_hash = str(
            _scalar(arrays["feature_sha256"], "feature_sha256", label=label)
        )
        actual_feature_hash = hashlib.sha256(
            numpy.ascontiguousarray(features, dtype="<f2").tobytes()
        ).hexdigest()
        if internal_feature_hash != actual_feature_hash:
            raise FactorizedArtifactIntegrityError(f"{label} internal feature hash is stale.")
        for name in (
            "source_audio_sha256",
            "source_feature_sha256",
            "feature_spec_sha256",
        ):
            if not _is_sha256(str(_scalar(arrays[name], name, label=label))):
                raise FactorizedArtifactIntegrityError(f"{label} has an invalid {name}.")
    else:
        if arrays["labels"].shape != (frames,) or not numpy.issubdtype(
            arrays["labels"].dtype,
            numpy.integer,
        ):
            raise FactorizedArtifactIntegrityError(
                f"{label} browser labels do not align with feature frames."
            )
        if "label_valid" in arrays and (
            arrays["label_valid"].shape != (frames,)
            or arrays["label_valid"].dtype != numpy.bool_
        ):
            raise FactorizedArtifactIntegrityError(
                f"{label} browser label mask does not align with feature frames."
            )

    duration_value = track.get("durationSeconds")
    if duration_value is not None:
        duration = _finite_nonnegative(
            duration_value,
            label=f"Track {identifier!r} durationSeconds",
        )
        if duration <= 0 or _expected_frames(duration) != frames:
            raise FactorizedArtifactIntegrityError(
                f"Track {identifier!r} duration does not match its feature frame count."
            )
    return frames


def _validate_factorized_label_arrays(
    arrays: Mapping[str, Any],
    *,
    frames: int,
    label: str,
) -> None:
    numpy = __import__("numpy")
    integer_ranges = {
        "root": (0, 12),
        "mode": (0, 3),
        "product": (0, 4),
        "structure": (0, 12),
        "quality": (-1, 40),
        "bass": (0, 12),
    }
    for name, (minimum, maximum) in integer_ranges.items():
        array = arrays[name]
        if array.shape != (frames,) or not numpy.issubdtype(array.dtype, numpy.integer):
            raise FactorizedArtifactIntegrityError(
                f"{label} array {name!r} does not align with feature frames."
            )
        if numpy.any(array < minimum) or numpy.any(array > maximum):
            raise FactorizedArtifactIntegrityError(
                f"{label} array {name!r} is outside its class contract."
            )
    boundary = arrays["boundary"]
    if (
        boundary.shape != (frames,)
        or not numpy.issubdtype(boundary.dtype, numpy.floating)
        or not numpy.isfinite(boundary).all()
        or numpy.any(boundary < 0)
        or numpy.any(boundary > 1)
    ):
        raise FactorizedArtifactIntegrityError(
            f"{label} boundary array violates its frame/probability contract."
        )
    if arrays["label_valid"].shape != (frames,) or arrays["label_valid"].dtype != numpy.bool_:
        raise FactorizedArtifactIntegrityError(
            f"{label} label_valid array does not align with feature frames."
        )


def _file_digest(path: Path, *, label: str) -> dict[str, Any]:
    before = path.stat(follow_symlinks=False)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_before != identity_after:
        raise FactorizedArtifactIntegrityError(f"{label} changed while it was being sealed.")
    return {"sha256": digest.hexdigest(), "bytes": before.st_size}


def _validated_track_metadata(track: Mapping[str, Any]) -> tuple[str, str, str]:
    identifier = str(track.get("id", "")).strip()
    dataset_id = str(track.get("datasetId", "")).strip()
    split = str(track.get("sourceSplit", track.get("split", ""))).strip()
    if not identifier or not dataset_id:
        raise FactorizedArtifactIntegrityError(
            "Every factorized artifact track needs non-empty id and datasetId values."
        )
    if split not in _VALID_SPLITS:
        raise FactorizedArtifactIntegrityError(
            f"Track {identifier!r} has unsupported split {split!r}."
        )
    return identifier, dataset_id, split


def _inspect_track(
    track: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    identifier, dataset_id, split = _validated_track_metadata(track)
    feature_path = _safe_path(track.get("path"), label=f"Track {identifier!r} feature")
    labels_path = _safe_path(
        track.get("factorizedLabelsPath"),
        label=f"Track {identifier!r} factorized-label",
    )
    expected_feature_arrays = _FEATURE_CONTRACTS[str(contract["featureKind"])][2]
    feature_arrays = _load_arrays(
        feature_path,
        expected_feature_arrays,
        label=f"Track {identifier!r} feature NPZ",
    )
    frames = _validate_feature_arrays(
        feature_arrays,
        track=track,
        contract=contract,
        label=f"Track {identifier!r} feature NPZ",
    )
    label_arrays = _load_arrays(
        labels_path,
        _FACTORIZED_LABEL_ARRAYS,
        label=f"Track {identifier!r} factorized-label NPZ",
    )
    _validate_factorized_label_arrays(
        label_arrays,
        frames=frames,
        label=f"Track {identifier!r} factorized-label NPZ",
    )
    return {
        "id": identifier,
        "datasetId": dataset_id,
        "split": split,
        "frames": frames,
        "featurePath": str(feature_path),
        "factorizedLabelsPath": str(labels_path),
        "featureArtifact": _file_digest(
            feature_path,
            label=f"Track {identifier!r} feature NPZ",
        ),
        "factorizedLabelArtifact": _file_digest(
            labels_path,
            label=f"Track {identifier!r} factorized-label NPZ",
        ),
    }


def _unsigned_integrity(integrity: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(integrity))
    value.pop("artifactSetSha256", None)
    return value


def seal_factorized_artifact_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy carrying hashes for every feature and factor-label NPZ."""

    if "splitProtocol" in manifest:
        raise FactorizedArtifactIntegrityError(
            "Refusing to mutate a signed split protocol; seal its source manifest, then refreeze."
        )
    provisional_contract = _manifest_contract(
        manifest,
        allow_missing_feature_spec=True,
    )
    output = deepcopy(dict(manifest))
    output["featureSpecSha256"] = provisional_contract["featureSpecSha256"]
    contract = _manifest_contract(output)
    tracks = manifest.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise FactorizedArtifactIntegrityError("Artifact sealing requires selected tracks.")
    entries: list[dict[str, Any]] = []
    ids: set[str] = set()
    for track in tracks:
        if not isinstance(track, Mapping):
            raise FactorizedArtifactIntegrityError("Factorized tracks must be objects.")
        entry = _inspect_track(track, contract)
        if entry["id"] in ids:
            raise FactorizedArtifactIntegrityError("Factorized track ids must be unique.")
        ids.add(entry["id"])
        entries.append(entry)
    entries.sort(key=lambda item: (item["datasetId"], item["id"]))
    integrity = {
        "schemaVersion": FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA,
        "manifestContract": contract,
        "trackCount": len(entries),
        "tracks": entries,
    }
    integrity["artifactSetSha256"] = _canonical_sha256(integrity)
    output["artifactIntegrity"] = integrity
    validate_factorized_artifact_manifest(output, verify_files=True)
    return output


def validate_factorized_artifact_manifest(
    manifest: Mapping[str, Any],
    verify_files: bool = True,
) -> Mapping[str, Any]:
    """Validate the canonical seal and optionally rehash every selected file."""

    contract = _manifest_contract(manifest)
    integrity = manifest.get("artifactIntegrity")
    if not isinstance(integrity, Mapping):
        raise FactorizedArtifactIntegrityError(
            "Strict factorized artifacts require an artifactIntegrity seal."
        )
    if set(integrity) != {
        "schemaVersion",
        "manifestContract",
        "trackCount",
        "tracks",
        "artifactSetSha256",
    }:
        raise FactorizedArtifactIntegrityError("Artifact integrity metadata has unexpected fields.")
    if integrity.get("schemaVersion") != FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA:
        raise FactorizedArtifactIntegrityError("Unsupported factorized artifact integrity schema.")
    if integrity.get("manifestContract") != contract:
        raise FactorizedArtifactIntegrityError("Sealed feature contract does not match the manifest.")
    expected_set_hash = str(integrity.get("artifactSetSha256", ""))
    actual_set_hash = _canonical_sha256(_unsigned_integrity(integrity))
    if not _is_sha256(expected_set_hash) or expected_set_hash != actual_set_hash:
        raise FactorizedArtifactIntegrityError("Factorized artifact-set hash mismatch.")
    sealed_tracks = integrity.get("tracks")
    if not isinstance(sealed_tracks, list) or int(integrity.get("trackCount", -1)) != len(
        sealed_tracks
    ):
        raise FactorizedArtifactIntegrityError("Sealed artifact track count is invalid.")
    sealed_by_id: dict[str, Mapping[str, Any]] = {}
    for entry in sealed_tracks:
        if not isinstance(entry, Mapping) or set(entry) != {
            "id",
            "datasetId",
            "split",
            "frames",
            "featurePath",
            "factorizedLabelsPath",
            "featureArtifact",
            "factorizedLabelArtifact",
        }:
            raise FactorizedArtifactIntegrityError("Sealed artifact track metadata is invalid.")
        identifier = str(entry.get("id", ""))
        if not identifier or identifier in sealed_by_id:
            raise FactorizedArtifactIntegrityError("Sealed artifact track ids are invalid.")
        for artifact_name in ("featureArtifact", "factorizedLabelArtifact"):
            artifact = entry[artifact_name]
            if (
                not isinstance(artifact, Mapping)
                or set(artifact) != {"sha256", "bytes"}
                or not _is_sha256(artifact.get("sha256"))
                or isinstance(artifact.get("bytes"), bool)
                or not isinstance(artifact.get("bytes"), int)
                or int(artifact["bytes"]) <= 0
            ):
                raise FactorizedArtifactIntegrityError(
                    f"Sealed {artifact_name} metadata is invalid."
                )
        sealed_by_id[identifier] = entry

    tracks = manifest.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise FactorizedArtifactIntegrityError("Factorized artifact manifest has no selected tracks.")
    selected_ids: set[str] = set()
    for track in tracks:
        if not isinstance(track, Mapping):
            raise FactorizedArtifactIntegrityError("Factorized tracks must be objects.")
        identifier, dataset_id, source_split = _validated_track_metadata(track)
        if identifier in selected_ids:
            raise FactorizedArtifactIntegrityError("Factorized selected track ids must be unique.")
        selected_ids.add(identifier)
        entry = sealed_by_id.get(identifier)
        if entry is None:
            raise FactorizedArtifactIntegrityError(
                f"Selected track {identifier!r} has no sealed artifacts."
            )
        expected_cross_fields = {
            "datasetId": dataset_id,
            "split": source_split,
            "frames": int(track.get("frames", -1)),
            "featurePath": str(track.get("path", "")),
            "factorizedLabelsPath": str(track.get("factorizedLabelsPath", "")),
        }
        if any(entry.get(name) != value for name, value in expected_cross_fields.items()):
            raise FactorizedArtifactIntegrityError(
                f"Selected track {identifier!r} does not match its sealed path/split/frame identity."
            )
        if verify_files:
            inspected = _inspect_track(track, contract)
            for name in ("featureArtifact", "factorizedLabelArtifact"):
                if inspected[name] != entry[name]:
                    raise FactorizedArtifactIntegrityError(
                        f"Selected track {identifier!r} {name} hash or byte count changed."
                    )
    if "splitProtocol" not in manifest and selected_ids != set(sealed_by_id):
        raise FactorizedArtifactIntegrityError(
            "Unsigned artifact manifests must seal exactly their selected track set."
        )
    return manifest
