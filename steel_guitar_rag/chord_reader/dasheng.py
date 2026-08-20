"""Verified, offline Dasheng feature extraction for chord-reader experiments.

The upstream Hugging Face repository contains custom Python. This module never
uses ``trust_remote_code`` or a mutable model identifier. It first verifies the
complete runtime snapshot against the immutable manifest, then executes the
already-verified source bytes and deserializes only a safetensors checkpoint.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import importlib
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import resource
import socket
import sys
import tempfile
import threading
import time
import types
from typing import Any, Iterable, Iterator, Mapping
from unittest import mock


DASHENG_FEATURE_KIND = "dasheng_base_v1"
DASHENG_FEATURE_COUNT = 768
DASHENG_SAMPLE_RATE = 16_000
DASHENG_NATIVE_FRAME_SECONDS = 0.04
DASHENG_FRAME_SECONDS = 0.1
DASHENG_PILOT_LIMITS = frozenset({1, 10})
DASHENG_REQUIRED_FILES = frozenset(
    {
        "config.json",
        "configuration_dasheng.py",
        "feature_extraction_dasheng.py",
        "modeling_dasheng.py",
        "preprocessor_config.json",
        "model.safetensors",
    }
)
DEFAULT_DASHENG_CONTRACT = (
    Path(__file__).resolve().parents[2] / "chord_reader" / "models" / "dasheng-base.json"
)

_ACTIVE_SNAPSHOT_SUFFIXES = frozenset({".json", ".py", ".safetensors"})
_SHA256_HEX = frozenset("0123456789abcdef")
_OFFLINE_LOAD_LOCK = threading.Lock()
_EXTRACTOR_CACHE_LOCK = threading.Lock()
_EXTRACTOR_CACHE: dict[tuple[Path, Path], "DashengBaseFeatureExtractor"] = {}


class DashengSnapshotError(RuntimeError):
    """The local model snapshot does not match its sealed contract."""


class DashengDependencyError(RuntimeError):
    """The optional Dasheng extraction environment is not installed."""


@dataclass(frozen=True)
class VerifiedDashengSnapshot:
    """A snapshot whose executable files are retained as verified bytes."""

    root: Path
    contract: Mapping[str, Any]
    file_bytes: Mapping[str, bytes]

    @property
    def model_path(self) -> Path:
        return self.root / "model.safetensors"


@dataclass(frozen=True)
class DashengFeatureBatch:
    """One audio item's 0.1-second Dasheng feature grid and provenance."""

    features: Any
    timestamps_seconds: Any
    duration_seconds: float
    provenance: Mapping[str, Any]

    @property
    def feature_sha256(self) -> str:
        numpy = importlib.import_module("numpy")
        values = numpy.ascontiguousarray(self.features, dtype="<f4")
        return hashlib.sha256(values.tobytes()).hexdigest()


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _SHA256_HEX


def _is_git_revision(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and set(value) <= _SHA256_HEX


def _validate_contract(contract: Mapping[str, Any]) -> None:
    expected_scalars = {
        "schemaVersion": "chord_reader_dasheng_snapshot_v1",
        "featureKind": DASHENG_FEATURE_KIND,
        "modelId": "mispeech/dasheng-base",
        "sampleRate": DASHENG_SAMPLE_RATE,
        "nativeFrameSeconds": DASHENG_NATIVE_FRAME_SECONDS,
        "frameSeconds": DASHENG_FRAME_SECONDS,
        "featureCount": DASHENG_FEATURE_COUNT,
        "pooling": "interval_overlap_mean_v1",
        "timestampConvention": "left_edge_seconds_v1",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            raise DashengSnapshotError(f"Dasheng contract field {key!r} must be {expected!r}.")
    revision = contract.get("revision")
    if not _is_git_revision(revision):
        raise DashengSnapshotError("Dasheng revision must be a full lowercase 40-character Git SHA.")
    license_contract = contract.get("license")
    if not isinstance(license_contract, Mapping) or license_contract.get("spdx") != "Apache-2.0":
        raise DashengSnapshotError("Dasheng contract must retain its Apache-2.0 license evidence.")

    entries = contract.get("files")
    if not isinstance(entries, list):
        raise DashengSnapshotError("Dasheng contract files must be a list.")
    paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise DashengSnapshotError("Every Dasheng file entry must be an object.")
        relative = entry.get("path")
        if not isinstance(relative, str):
            raise DashengSnapshotError("Every Dasheng file entry needs a path.")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or len(pure.parts) != 1:
            raise DashengSnapshotError(f"Unsafe Dasheng snapshot path {relative!r}.")
        if relative in paths:
            raise DashengSnapshotError(f"Duplicate Dasheng snapshot path {relative!r}.")
        paths.add(relative)
        if not isinstance(entry.get("bytes"), int) or int(entry["bytes"]) <= 0:
            raise DashengSnapshotError(f"Dasheng snapshot path {relative!r} needs a positive byte size.")
        if not _is_sha256(entry.get("sha256")):
            raise DashengSnapshotError(f"Dasheng snapshot path {relative!r} needs a lowercase SHA-256.")
        source_url = entry.get("sourceUrl")
        if not isinstance(source_url, str) or f"/resolve/{revision}/" not in source_url:
            raise DashengSnapshotError(f"Dasheng snapshot path {relative!r} needs an immutable source URL.")
    if paths != DASHENG_REQUIRED_FILES:
        missing = sorted(DASHENG_REQUIRED_FILES - paths)
        unexpected = sorted(paths - DASHENG_REQUIRED_FILES)
        raise DashengSnapshotError(
            f"Dasheng runtime allowlist mismatch; missing={missing}, unexpected={unexpected}."
        )


def load_dasheng_contract(path: Path = DEFAULT_DASHENG_CONTRACT) -> dict[str, Any]:
    """Load and validate the immutable Dasheng snapshot contract."""

    try:
        contract = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DashengSnapshotError(f"Could not read Dasheng contract {path}: {exc}") from exc
    if not isinstance(contract, dict):
        raise DashengSnapshotError("Dasheng contract root must be an object.")
    _validate_contract(contract)
    return contract


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_model_semantics(file_bytes: Mapping[str, bytes]) -> None:
    try:
        config = json.loads(file_bytes["config.json"])
        preprocessor = json.loads(file_bytes["preprocessor_config.json"])
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DashengSnapshotError(f"Dasheng configuration JSON is invalid: {exc}") from exc
    encoder = config.get("encoder_kwargs", {})
    expected_encoder = {
        "embed_dim": DASHENG_FEATURE_COUNT,
        "patch_size": [64, 4],
        "patch_stride": [64, 4],
    }
    for key, expected in expected_encoder.items():
        if encoder.get(key) != expected:
            raise DashengSnapshotError(f"Dasheng encoder field {key!r} must be {expected!r}.")
    expected_preprocessor = {
        "sampling_rate": DASHENG_SAMPLE_RATE,
        "hop_size": 160,
        "feature_size": 64,
    }
    for key, expected in expected_preprocessor.items():
        if preprocessor.get(key) != expected:
            raise DashengSnapshotError(f"Dasheng preprocessor field {key!r} must be {expected!r}.")


def verify_dasheng_snapshot(
    snapshot_root: Path,
    contract_path: Path = DEFAULT_DASHENG_CONTRACT,
) -> VerifiedDashengSnapshot:
    """Verify every active snapshot file before any custom code is imported."""

    root = Path(snapshot_root)
    if root.is_symlink() or not root.is_dir():
        raise DashengSnapshotError(f"Dasheng snapshot root must be a real directory: {root}")
    contract = load_dasheng_contract(contract_path)
    entries = {str(entry["path"]): entry for entry in contract["files"]}

    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise DashengSnapshotError(f"Dasheng snapshots may not contain symlinks: {candidate}")
        if candidate.is_file() and candidate.suffix in _ACTIVE_SNAPSHOT_SUFFIXES:
            relative = candidate.relative_to(root).as_posix()
            if relative not in entries:
                raise DashengSnapshotError(f"Unallowlisted active Dasheng snapshot file: {relative}")

    retained: dict[str, bytes] = {}
    for relative in sorted(entries):
        entry = entries[relative]
        candidate = root / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise DashengSnapshotError(f"Missing regular Dasheng snapshot file: {relative}")
        stat = candidate.stat()
        if stat.st_size != int(entry["bytes"]):
            raise DashengSnapshotError(
                f"Dasheng snapshot size mismatch for {relative}: expected {entry['bytes']}, got {stat.st_size}."
            )
        if relative.endswith((".py", ".json")):
            payload = candidate.read_bytes()
            actual_sha256 = hashlib.sha256(payload).hexdigest()
            retained[relative] = payload
        else:
            actual_sha256 = _hash_file(candidate)
        if actual_sha256 != entry["sha256"]:
            raise DashengSnapshotError(
                f"Dasheng snapshot SHA-256 mismatch for {relative}: expected {entry['sha256']}, "
                f"got {actual_sha256}."
            )
    _validate_model_semantics(retained)
    return VerifiedDashengSnapshot(root=root.resolve(), contract=contract, file_bytes=retained)


def dasheng_feature_provenance(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the stable contract attached to every extracted feature matrix."""

    _validate_contract(contract)
    provenance = {
        "schemaVersion": "chord_reader_feature_provenance_v1",
        "featureKind": contract["featureKind"],
        "modelId": contract["modelId"],
        "revision": contract["revision"],
        "license": dict(contract["license"]),
        "sampleRate": contract["sampleRate"],
        "nativeFrameSeconds": contract["nativeFrameSeconds"],
        "frameSeconds": contract["frameSeconds"],
        "featureCount": contract["featureCount"],
        "pooling": contract["pooling"],
        "timestampConvention": contract["timestampConvention"],
        "fileSha256": {str(entry["path"]): str(entry["sha256"]) for entry in contract["files"]},
    }
    provenance["provenanceSha256"] = _canonical_sha256(provenance)
    return provenance


def pool_dasheng_embeddings(native_embeddings: Any, duration_seconds: float) -> tuple[Any, Any]:
    """Pool native 25 Hz embeddings onto the exact chord-reader 0.1 s grid.

    Native and target vectors represent left-aligned time intervals. A target
    vector is the overlap-weighted mean of all 40 ms native intervals touching
    its 100 ms interval. The final interval is clipped to the audio duration.
    """

    numpy = importlib.import_module("numpy")
    native = numpy.asarray(native_embeddings, dtype=numpy.float32)
    duration = float(duration_seconds)
    if native.ndim != 2 or native.shape[1] != DASHENG_FEATURE_COUNT or native.shape[0] < 1:
        raise ValueError(
            f"Native Dasheng embeddings must have shape (frames, {DASHENG_FEATURE_COUNT}) with at least one frame."
        )
    if not math.isfinite(duration) or duration < 0:
        raise ValueError("Dasheng audio duration must be a finite non-negative value.")
    if not numpy.isfinite(native).all():
        raise ValueError("Native Dasheng embeddings must contain only finite values.")

    frame_count = max(1, math.ceil(duration / DASHENG_FRAME_SECONDS))
    timestamps = numpy.arange(frame_count, dtype=numpy.float64) * DASHENG_FRAME_SECONDS
    output = numpy.empty((frame_count, DASHENG_FEATURE_COUNT), dtype=numpy.float32)
    available_end = native.shape[0] * DASHENG_NATIVE_FRAME_SECONDS
    for frame, start in enumerate(timestamps):
        requested_end = (frame + 1) * DASHENG_FRAME_SECONDS
        end = min(duration, requested_end) if duration > start else requested_end
        overlap_end = min(end, available_end)
        first = max(0, int(math.floor(start / DASHENG_NATIVE_FRAME_SECONDS)))
        stop = min(native.shape[0], int(math.ceil(overlap_end / DASHENG_NATIVE_FRAME_SECONDS)))
        if stop <= first or overlap_end <= start:
            output[frame] = native[min(first, native.shape[0] - 1)]
            continue
        indices = numpy.arange(first, stop)
        native_starts = indices * DASHENG_NATIVE_FRAME_SECONDS
        native_ends = native_starts + DASHENG_NATIVE_FRAME_SECONDS
        weights = numpy.maximum(0.0, numpy.minimum(overlap_end, native_ends) - numpy.maximum(start, native_starts))
        weight_sum = float(weights.sum())
        if weight_sum <= 0:
            output[frame] = native[min(first, native.shape[0] - 1)]
        else:
            output[frame] = numpy.average(native[first:stop], axis=0, weights=weights).astype(numpy.float32)
    return output, timestamps


@contextmanager
def _network_disabled() -> Iterator[None]:
    """Make accidental network access fail while verified modules and weights load."""

    keys = (
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
        "HF_HOME",
        "HF_HUB_CACHE",
        "HF_MODULES_CACHE",
        "TRANSFORMERS_CACHE",
    )
    previous = {key: os.environ.get(key) for key in keys}

    def reject_network(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("Network access is disabled while loading the sealed Dasheng snapshot.")

    with tempfile.TemporaryDirectory(prefix="pocket-steel-dasheng-cache-") as temporary:
        cache_root = Path(temporary)
        os.environ.update(
            {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HF_DATASETS_OFFLINE": "1",
                "HF_HOME": str(cache_root),
                "HF_HUB_CACHE": str(cache_root / "hub"),
                "HF_MODULES_CACHE": str(cache_root / "modules"),
                "TRANSFORMERS_CACHE": str(cache_root / "transformers"),
            }
        )
        try:
            with mock.patch.object(socket.socket, "connect", reject_network), mock.patch(
                "socket.create_connection", reject_network
            ):
                yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def _exec_verified_module(name: str, path: Path, payload: bytes, *, package: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = package
    sys.modules[name] = module
    try:
        exec(compile(payload, str(path), "exec"), module.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _load_verified_runtime(verified: VerifiedDashengSnapshot) -> tuple[Any, Any, Any]:
    package_name = f"_pocket_steel_dasheng_{verified.contract['revision']}"
    package = types.ModuleType(package_name)
    package.__path__ = []
    package.__package__ = package_name
    sys.modules[package_name] = package
    try:
        configuration = _exec_verified_module(
            f"{package_name}.configuration_dasheng",
            verified.root / "configuration_dasheng.py",
            verified.file_bytes["configuration_dasheng.py"],
            package=package_name,
        )
        feature_extraction = _exec_verified_module(
            f"{package_name}.feature_extraction_dasheng",
            verified.root / "feature_extraction_dasheng.py",
            verified.file_bytes["feature_extraction_dasheng.py"],
            package=package_name,
        )
        modeling = _exec_verified_module(
            f"{package_name}.modeling_dasheng",
            verified.root / "modeling_dasheng.py",
            verified.file_bytes["modeling_dasheng.py"],
            package=package_name,
        )
        torch = importlib.import_module("torch")
        safetensors_torch = importlib.import_module("safetensors.torch")
    except ModuleNotFoundError as exc:
        raise DashengDependencyError(
            "Install requirements/chord-reader-dasheng.in before loading Dasheng."
        ) from exc

    config_payload = json.loads(verified.file_bytes["config.json"])
    preprocessor_payload = json.loads(verified.file_bytes["preprocessor_config.json"])
    config = configuration.DashengConfig(**config_payload)
    feature_extractor = feature_extraction.DashengFeatureExtractor(**preprocessor_payload)
    model = modeling.DashengModel(config, outputdim=None)
    state_dict = safetensors_torch.load_file(str(verified.model_path), device="cpu")
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return torch, feature_extractor, model


class DashengBaseFeatureExtractor:
    """Deterministic 768-D extraction from a verified local Dasheng snapshot."""

    def __init__(
        self,
        snapshot_root: Path,
        *,
        contract_path: Path = DEFAULT_DASHENG_CONTRACT,
        device: str = "cpu",
    ) -> None:
        if device != "cpu":
            raise ValueError("dasheng_base_v1 is sealed to CPU inference for reproducible training features.")
        verified = verify_dasheng_snapshot(snapshot_root, contract_path)
        with _OFFLINE_LOAD_LOCK, _network_disabled():
            self._torch, self._upstream_extractor, self._model = _load_verified_runtime(verified)
        self._device = device
        self._model.to(device)
        self.contract = dict(verified.contract)
        self.provenance = dasheng_feature_provenance(self.contract)

    def extract_waveform(self, samples: Any, *, sampling_rate: int = DASHENG_SAMPLE_RATE) -> DashengFeatureBatch:
        numpy = importlib.import_module("numpy")
        waveform = numpy.asarray(samples, dtype=numpy.float32)
        if waveform.ndim != 1:
            raise ValueError("Dasheng waveform input must be mono and one-dimensional.")
        if not numpy.isfinite(waveform).all():
            raise ValueError("Dasheng waveform input must contain only finite values.")
        if sampling_rate <= 0:
            raise ValueError("Dasheng waveform sampling rate must be positive.")
        if sampling_rate != DASHENG_SAMPLE_RATE:
            librosa = importlib.import_module("librosa")
            waveform = librosa.resample(
                waveform,
                orig_sr=int(sampling_rate),
                target_sr=DASHENG_SAMPLE_RATE,
            ).astype(numpy.float32)
        duration = len(waveform) / DASHENG_SAMPLE_RATE
        model_waveform = waveform
        minimum_samples = round(DASHENG_NATIVE_FRAME_SECONDS * DASHENG_SAMPLE_RATE)
        if len(model_waveform) < minimum_samples:
            model_waveform = numpy.pad(model_waveform, (0, minimum_samples - len(model_waveform)))
        inputs = self._upstream_extractor(
            model_waveform,
            sampling_rate=DASHENG_SAMPLE_RATE,
            return_tensors="pt",
        )
        input_values = inputs["input_values"].to(self._device)
        with self._torch.inference_mode():
            hidden = self._model(input_values=input_values).hidden_states
        native = hidden[0].detach().cpu().to(self._torch.float32).numpy()
        features, timestamps = pool_dasheng_embeddings(native, duration)
        return DashengFeatureBatch(
            features=features,
            timestamps_seconds=timestamps,
            duration_seconds=duration,
            provenance=self.provenance,
        )

    def extract(self, audio: Path) -> DashengFeatureBatch:
        """Load a mono audio file at 16 kHz and extract its sealed feature grid."""

        librosa = importlib.import_module("librosa")
        samples, _sampling_rate = librosa.load(str(audio), sr=DASHENG_SAMPLE_RATE, mono=True)
        return self.extract_waveform(samples, sampling_rate=DASHENG_SAMPLE_RATE)


def get_dasheng_feature_extractor(
    snapshot_root: Path,
    *,
    contract_path: Path = DEFAULT_DASHENG_CONTRACT,
) -> DashengBaseFeatureExtractor:
    """Reuse one verified encoder instead of loading 342 MB for every track."""

    key = (Path(snapshot_root).resolve(), Path(contract_path).resolve())
    with _EXTRACTOR_CACHE_LOCK:
        extractor = _EXTRACTOR_CACHE.get(key)
        if extractor is None:
            extractor = DashengBaseFeatureExtractor(key[0], contract_path=key[1])
            _EXTRACTOR_CACHE[key] = extractor
        return extractor


def extract_dasheng_features(
    audio: Path,
    snapshot_root: Path,
    *,
    contract_path: Path = DEFAULT_DASHENG_CONTRACT,
) -> tuple[Any, float]:
    """Compatibility wrapper for the existing ``(features, duration)`` cache API."""

    result = get_dasheng_feature_extractor(snapshot_root, contract_path=contract_path).extract(audio)
    return result.features, result.duration_seconds


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def run_dasheng_pilot(
    tracks: Iterable[Mapping[str, Any]],
    *,
    limit: int,
    extractor: Any | None = None,
    snapshot_root: Path | None = None,
    contract_path: Path = DEFAULT_DASHENG_CONTRACT,
) -> dict[str, Any]:
    """Run the deliberately bounded one- or ten-track extraction pilot.

    This returns measurements and content hashes only; it does not create a
    feature cache and cannot be used to accidentally start the full corpus.
    """

    if limit not in DASHENG_PILOT_LIMITS:
        raise ValueError("Dasheng pilots are intentionally restricted to exactly 1 or 10 tracks.")
    selected = list(itertools.islice(tracks, limit))
    if len(selected) != limit:
        raise ValueError(f"Dasheng {limit}-track pilot received only {len(selected)} tracks.")
    if extractor is None:
        if snapshot_root is None:
            raise ValueError("Dasheng pilot needs either an extractor or a snapshot_root.")
        extractor = get_dasheng_feature_extractor(snapshot_root, contract_path=contract_path)

    peak_before = _peak_rss_bytes()
    started = time.perf_counter()
    total_audio_seconds = 0.0
    results: list[dict[str, Any]] = []
    provenance: Mapping[str, Any] | None = None
    for track in selected:
        track_started = time.perf_counter()
        batch = extractor.extract(Path(str(track["audioPath"])))
        elapsed = time.perf_counter() - track_started
        if provenance is None:
            provenance = batch.provenance
        elif batch.provenance.get("provenanceSha256") != provenance.get("provenanceSha256"):
            raise ValueError("Dasheng pilot tracks did not share one feature provenance contract.")
        total_audio_seconds += float(batch.duration_seconds)
        results.append(
            {
                "id": str(track.get("id", Path(str(track["audioPath"])).stem)),
                "audioPath": str(Path(str(track["audioPath"])).resolve()),
                "durationSeconds": float(batch.duration_seconds),
                "frames": int(len(batch.features)),
                "featureCount": int(batch.features.shape[1]),
                "featureSha256": batch.feature_sha256,
                "wallTimeSeconds": elapsed,
            }
        )
    wall_time = time.perf_counter() - started
    peak_after = _peak_rss_bytes()
    return {
        "schemaVersion": "chord_reader_dasheng_pilot_v1",
        "requestedTracks": limit,
        "processedTracks": len(results),
        "featureKind": DASHENG_FEATURE_KIND,
        "featureCount": DASHENG_FEATURE_COUNT,
        "frameSeconds": DASHENG_FRAME_SECONDS,
        "totalAudioSeconds": total_audio_seconds,
        "wallTimeSeconds": wall_time,
        "realTimeFactor": wall_time / total_audio_seconds if total_audio_seconds > 0 else None,
        "peakRssBytes": peak_after,
        "peakRssIncreaseBytes": max(0, peak_after - peak_before),
        "provenance": dict(provenance or {}),
        "tracks": results,
    }


def run_dasheng_one_track_pilot(tracks: Iterable[Mapping[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return run_dasheng_pilot(tracks, limit=1, **kwargs)


def run_dasheng_ten_track_pilot(tracks: Iterable[Mapping[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return run_dasheng_pilot(tracks, limit=10, **kwargs)


__all__ = [
    "DASHENG_FEATURE_COUNT",
    "DASHENG_FEATURE_KIND",
    "DASHENG_FRAME_SECONDS",
    "DASHENG_NATIVE_FRAME_SECONDS",
    "DASHENG_SAMPLE_RATE",
    "DEFAULT_DASHENG_CONTRACT",
    "DashengBaseFeatureExtractor",
    "DashengDependencyError",
    "DashengFeatureBatch",
    "DashengSnapshotError",
    "VerifiedDashengSnapshot",
    "dasheng_feature_provenance",
    "extract_dasheng_features",
    "get_dasheng_feature_extractor",
    "load_dasheng_contract",
    "pool_dasheng_embeddings",
    "run_dasheng_one_track_pilot",
    "run_dasheng_pilot",
    "run_dasheng_ten_track_pilot",
    "verify_dasheng_snapshot",
]
