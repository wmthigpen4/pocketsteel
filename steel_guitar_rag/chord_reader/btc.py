"""Pinned, checksum-verified adapter for the pretrained BTC ISMIR 2019 model."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .labels import normalize_chord


MODEL_SCHEMA = "chord_model_source_v1"
MODEL_REGISTRY = Path(__file__).resolve().parents[2] / "chord_reader/models/btc-ismir19.json"
TIMESTEP = 108
FEATURE_SIZE = 144
SAMPLE_RATE = 22050
FRAME_SECONDS = 10.0 / TIMESTEP


def load_model_registry(path: Path = MODEL_REGISTRY) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != MODEL_SCHEMA:
        raise ValueError(f"Model registry must use {MODEL_SCHEMA}.")
    upstream = value.get("upstream", {})
    if not upstream.get("modelId") or not upstream.get("revision"):
        raise ValueError("Model registry must pin a model id and immutable revision.")
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Model registry must pin at least one file hash.")
    for relative, digest in files.items():
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"Unsafe model file path {relative!r}.")
        if len(str(digest)) != 64:
            raise ValueError(f"Model file {relative!r} needs a SHA-256 digest.")
    return value


def verify_model_snapshot(snapshot: Path, registry: Mapping[str, Any]) -> None:
    """Verify every executable/model artifact before importing or deserializing it."""

    failures: list[str] = []
    for relative, expected in registry["files"].items():
        path = snapshot / relative
        if not path.is_file():
            failures.append(f"missing {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(f"SHA-256 mismatch for {relative}: {actual}")
    if failures:
        raise ValueError("BTC snapshot verification failed: " + "; ".join(failures))


def resolve_model_snapshot(
    *,
    cache_dir: Path | None = None,
    local_files_only: bool = False,
    registry_path: Path = MODEL_REGISTRY,
) -> tuple[Path, dict[str, Any]]:
    """Resolve the immutable Hub snapshot, then enforce the tracked hashes."""

    registry = load_model_registry(registry_path)
    try:
        hub = importlib.import_module("huggingface_hub")
    except ModuleNotFoundError as error:
        raise RuntimeError("Install requirements/chord-reader.lock before using BTC.") from error
    upstream = registry["upstream"]
    snapshot = Path(
        hub.snapshot_download(
            repo_id=upstream["modelId"],
            revision=upstream["revision"],
            allow_patterns=list(registry["files"]),
            cache_dir=str(cache_dir) if cache_dir else None,
            local_files_only=local_files_only,
        )
    )
    verify_model_snapshot(snapshot, registry)
    return snapshot, registry


def _model_config(num_chords: int) -> dict[str, Any]:
    return {
        "feature_size": FEATURE_SIZE,
        "timestep": TIMESTEP,
        "input_dropout": 0.2,
        "layer_dropout": 0.2,
        "attention_dropout": 0.2,
        "relu_dropout": 0.2,
        "num_layers": 8,
        "num_heads": 4,
        "hidden_size": 128,
        "total_key_depth": 128,
        "total_value_depth": 128,
        "filter_size": 128,
        "loss": "ce",
        "probs_out": False,
        "num_chords": num_chords,
    }


def _load_checkpoint(torch: Any, numpy: Any, path: Path) -> dict[str, Any]:
    # The historical checkpoint contains a numpy scalar. Allow only that exact
    # legacy constructor while retaining PyTorch's weights-only unpickler.
    safe = [
        (numpy._core.multiarray.scalar, "numpy.core.multiarray.scalar"),
        numpy.dtype,
        type(numpy.dtype(numpy.float64)),
        type(numpy.dtype(numpy.float32)),
    ]
    with torch.serialization.safe_globals(safe):
        return torch.load(path, map_location="cpu", weights_only=True)


def _load_runtime(snapshot: Path, device: str) -> tuple[Any, Any, Any, dict[int, str], float, float, str]:
    try:
        numpy = importlib.import_module("numpy")
        torch = importlib.import_module("torch")
        importlib.import_module("librosa")
    except ModuleNotFoundError as error:
        raise RuntimeError("Install requirements/chord-reader.lock before using BTC.") from error

    if str(snapshot) not in sys.path:
        sys.path.insert(0, str(snapshot))
    model_module = importlib.import_module("btc_src.btc_model")
    features = importlib.import_module("btc_src.features")
    chord_map = features.idx2voca_chord()
    model = model_module.BTC_model(config=_model_config(len(chord_map)))
    checkpoint = _load_checkpoint(torch, numpy, snapshot / "btc_model_large_voca.pt")
    model.load_state_dict(checkpoint["model"])
    if device == "auto":
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    return numpy, torch, model, chord_map, float(checkpoint["mean"]), float(checkpoint["std"]), device


def _segments_from_frames(
    indices: list[int],
    confidences: list[float],
    chord_map: Mapping[int, str],
    duration_seconds: float,
) -> list[dict[str, Any]]:
    if not indices:
        return [{"start": 0.0, "end": duration_seconds, "label": "N", "productLabel": "N.C.", "confidence": 0.0}]
    segments: list[dict[str, Any]] = []
    start_frame = 0
    for frame in range(1, len(indices) + 1):
        if frame < len(indices) and indices[frame] == indices[start_frame]:
            continue
        raw = chord_map[indices[start_frame]]
        label = normalize_chord(raw)
        end = duration_seconds if frame == len(indices) else min(duration_seconds, frame * FRAME_SECONDS)
        start = 0.0 if start_frame == 0 else min(duration_seconds, start_frame * FRAME_SECONDS)
        if end > start:
            segments.append(
                {
                    "start": round(start, 6),
                    "end": round(end, 6),
                    "label": label.detailed_symbol,
                    "productLabel": label.product_symbol,
                    "rawLabel": raw,
                    "confidence": sum(confidences[start_frame:frame]) / (frame - start_frame),
                    "needsAttention": label.needs_attention,
                }
            )
        start_frame = frame
    return segments


class BTCRecognizer:
    """Reusable pretrained recognizer so a benchmark loads weights only once."""

    def __init__(
        self,
        *,
        device: str = "cpu",
        cache_dir: Path | None = None,
        local_files_only: bool = False,
    ) -> None:
        snapshot, self.registry = resolve_model_snapshot(
            cache_dir=cache_dir,
            local_files_only=local_files_only,
        )
        (
            self.numpy,
            self.torch,
            self.model,
            self.chord_map,
            self.mean,
            self.std,
            self.device,
        ) = _load_runtime(snapshot, device)
        self.librosa = importlib.import_module("librosa")
        self.features_module = importlib.import_module("btc_src.features")

    def predict(self, audio: Path, *, prediction_id: str | None = None) -> dict[str, Any]:
        waveform, _sample_rate = self.librosa.load(str(audio), sr=SAMPLE_RATE, mono=True)
        duration_seconds = len(waveform) / SAMPLE_RATE
        features = self.features_module.audio_to_features(waveform, sr_target=SAMPLE_RATE).T
        features = (features - self.mean) / self.std
        valid_frames = int(features.shape[0])
        padding = (-valid_frames) % TIMESTEP
        if padding:
            features = self.numpy.pad(features, ((0, padding), (0, 0)), mode="constant")

        frame_indices: list[int] = []
        frame_confidences: list[float] = []
        tensor = self.torch.tensor(features, dtype=self.torch.float32).unsqueeze(0).to(self.device)
        with self.torch.no_grad():
            for offset in range(0, features.shape[0], TIMESTEP):
                encoded, _weights = self.model.self_attn_layers(tensor[:, offset : offset + TIMESTEP, :])
                logits = self.model.output_layer.output_projection(encoded)
                probabilities = self.torch.softmax(logits, dim=-1)
                confidence, predicted = self.torch.max(probabilities, dim=-1)
                remaining = min(TIMESTEP, valid_frames - offset)
                frame_indices.extend(int(value) for value in predicted[0, :remaining].cpu().tolist())
                frame_confidences.extend(float(value) for value in confidence[0, :remaining].cpu().tolist())

        return {
            "schemaVersion": "chord_prediction_v1",
            "id": prediction_id or audio.name,
            "engine": "btc-ismir19-hf-baseline",
            "modelRevision": self.registry["upstream"]["revision"],
            "vocabulary": self.registry["vocabulary"],
            "durationSeconds": duration_seconds,
            "sampleRate": SAMPLE_RATE,
            "frameSeconds": FRAME_SECONDS,
            "segments": _segments_from_frames(
                frame_indices,
                frame_confidences,
                self.chord_map,
                duration_seconds,
            ),
        }


def predict_btc(
    audio: Path,
    *,
    prediction_id: str | None = None,
    device: str = "cpu",
    cache_dir: Path | None = None,
    local_files_only: bool = False,
) -> dict[str, Any]:
    """Run the pinned 170-class BTC checkpoint and emit benchmark segments."""

    return BTCRecognizer(
        device=device,
        cache_dir=cache_dir,
        local_files_only=local_files_only,
    ).predict(audio, prediction_id=prediction_id)
