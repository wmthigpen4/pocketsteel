"""Browser-sized supervised chord model trained on worker-compatible chroma."""

from __future__ import annotations

import importlib
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable, Mapping

from .labels import PITCH_CLASS, SHARP_NAMES, normalize_chord


STUDENT_SCHEMA = "chord_student_model_v1"
STUDENT_SAMPLE_RATE = 11025
STUDENT_FRAME_SECONDS = 0.1
STUDENT_FEATURES = 13
STUDENT_QUALITIES = ("maj", "min", "7", "min7")
STUDENT_CLASSES = 1 + 12 * len(STUDENT_QUALITIES)


def student_index(symbol: str | None) -> int:
    label = normalize_chord(symbol)
    if label.root is None:
        return 0
    quality = label.quality
    if quality in {"maj", "maj6", "6", "maj7", "maj9", "add9", "sus2", "sus4", "5"}:
        family = "maj"
    elif quality in {"min", "min6", "min9", "min11", "dim", "aug"}:
        family = "min"
    elif quality in {"min7", "min13", "minmaj7", "hdim7", "dim7"}:
        family = "min7"
    else:
        family = "7"
    root = PITCH_CLASS[label.root]
    return 1 + STUDENT_QUALITIES.index(family) * 12 + root


def student_label(index: int) -> str:
    if index == 0:
        return "N"
    value = index - 1
    quality = STUDENT_QUALITIES[value // 12]
    return f"{SHARP_NAMES[value % 12]}:{quality}"


def transpose_student_index(index: int, semitones: int) -> int:
    if index == 0:
        return index
    value = index - 1
    return 1 + (value // 12) * 12 + ((value % 12 + semitones) % 12)


def _worker_downsample(samples: Any, source_rate: int, numpy: Any) -> tuple[Any, int]:
    if source_rate <= STUDENT_SAMPLE_RATE:
        return samples.astype(numpy.float32, copy=False), source_rate
    ratio = source_rate / STUDENT_SAMPLE_RATE
    length = int(len(samples) / ratio)
    starts = numpy.floor(numpy.arange(length) * ratio).astype(numpy.int64)
    ends = numpy.maximum(starts + 1, numpy.floor((numpy.arange(length) + 1) * ratio).astype(numpy.int64))
    ends = numpy.minimum(ends, len(samples))
    cumulative = numpy.concatenate((numpy.zeros(1), numpy.cumsum(samples, dtype=numpy.float64)))
    output = (cumulative[ends] - cumulative[starts]) / numpy.maximum(1, ends - starts)
    return output.astype(numpy.float32), STUDENT_SAMPLE_RATE


def worker_compatible_features(audio: Path) -> tuple[Any, float]:
    """Match the browser worker's 4096-bin spectral chroma calculation."""

    numpy = importlib.import_module("numpy")
    librosa = importlib.import_module("librosa")
    samples, source_rate = librosa.load(str(audio), sr=None, mono=True)
    samples, sample_rate = _worker_downsample(samples, int(source_rate), numpy)
    duration = len(samples) / sample_rate
    frame_count = max(1, math.ceil(duration / STUDENT_FRAME_SECONDS))
    centers = numpy.arange(frame_count, dtype=numpy.float64) * STUDENT_FRAME_SECONDS
    size = 4096
    starts = numpy.clip(
        numpy.rint(centers * sample_rate - size / 2).astype(numpy.int64),
        0,
        max(0, len(samples) - size),
    )
    padded = numpy.pad(samples, (0, max(0, size - len(samples))))
    indices = starts[:, None] + numpy.arange(size)[None, :]
    frames = padded[indices]
    energy = numpy.sqrt(numpy.mean(frames * frames, axis=1))
    window = 0.5 - 0.5 * numpy.cos(2 * numpy.pi * numpy.arange(size) / (size - 1))
    spectrum = numpy.fft.rfft(frames * window[None, :], axis=1)
    frequencies = numpy.fft.rfftfreq(size, 1 / sample_rate)
    selected = (frequencies >= 55) & (frequencies <= 1760)
    frequency = frequencies[selected]
    midi = 69 + 12 * numpy.log2(frequency / 440)
    lower = numpy.floor(midi).astype(int)
    fraction = midi - lower
    magnitude = numpy.sqrt(numpy.abs(spectrum[:, selected]))
    magnitude *= numpy.clip(220 / frequency, 0.22, 3)[None, :]
    chroma = numpy.zeros((frame_count, 12), dtype=numpy.float64)
    for bin_index in range(len(frequency)):
        chroma[:, lower[bin_index] % 12] += magnitude[:, bin_index] * (1 - fraction[bin_index])
        chroma[:, (lower[bin_index] + 1) % 12] += magnitude[:, bin_index] * fraction[bin_index]
    chroma /= numpy.maximum(1e-12, chroma.sum(axis=1, keepdims=True))
    features = numpy.concatenate((chroma, energy[:, None]), axis=1).astype(numpy.float32)
    return features, duration


def frame_labels(segments: Iterable[Mapping[str, Any]], frame_count: int) -> list[int]:
    values = sorted(segments, key=lambda item: float(item["start"]))
    labels: list[int] = []
    index = 0
    for frame in range(frame_count):
        center = frame * STUDENT_FRAME_SECONDS
        while index + 1 < len(values) and float(values[index]["end"]) <= center:
            index += 1
        if values and float(values[index]["start"]) <= center < float(values[index]["end"]):
            labels.append(student_index(str(values[index]["label"])))
        else:
            labels.append(0)
    return labels


def cache_student_features(
    manifest: Mapping[str, Any],
    output_root: Path,
    *,
    splits: set[str] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    numpy = importlib.import_module("numpy")
    tracks = [track for track in manifest["tracks"] if splits is None or track["split"] in splits]
    if limit is not None:
        tracks = tracks[:limit]
    cached: list[dict[str, Any]] = []
    for track in tracks:
        features, duration = worker_compatible_features(Path(track["audioPath"]))
        reference = json.loads(Path(track["referencePath"]).read_text(encoding="utf-8"))
        labels = numpy.asarray(frame_labels(reference["segments"], len(features)), dtype=numpy.int64)
        path = output_root / track["split"] / f"{track['id']}.npz"
        path.parent.mkdir(parents=True, exist_ok=True)
        numpy.savez_compressed(
            path,
            features=features.astype(numpy.float16),
            labels=labels,
            training_weight=numpy.asarray(float(track.get("trainingWeight", 1)), dtype=numpy.float32),
        )
        cached.append(
            {
                "id": track["id"],
                "datasetId": track["datasetId"],
                "split": track["split"],
                "path": str(path.resolve()),
                "frames": len(features),
                "durationSeconds": duration,
            }
        )
    return {
        "schemaVersion": "chord_feature_cache_v1",
        "sampleRate": STUDENT_SAMPLE_RATE,
        "frameSeconds": STUDENT_FRAME_SECONDS,
        "featureCount": STUDENT_FEATURES,
        "tracks": cached,
    }


def _torch_modules() -> tuple[Any, Any, Any]:
    torch = importlib.import_module("torch")
    return torch, torch.nn, torch.nn.functional


def _hierarchical_logits(logits: Any, torch: Any) -> tuple[Any, Any, Any]:
    roots = [logits[..., :1]]
    for root in range(12):
        roots.append(torch.logsumexp(torch.stack([logits[..., 1 + quality * 12 + root] for quality in range(4)], dim=-1), dim=-1, keepdim=True))
    root_logits = torch.cat(roots, dim=-1)
    major = torch.logsumexp(
        torch.cat((logits[..., 1:13], logits[..., 25:37]), dim=-1),
        dim=-1,
        keepdim=True,
    )
    minor = torch.logsumexp(
        torch.cat((logits[..., 13:25], logits[..., 37:49]), dim=-1),
        dim=-1,
        keepdim=True,
    )
    major_minor_logits = torch.cat((logits[..., :1], major, minor), dim=-1)
    joint = [logits[..., :1]]
    for quality_indices in ((0, 2), (1, 3)):
        for root in range(12):
            joint.append(
                torch.logsumexp(
                    torch.stack([logits[..., 1 + quality * 12 + root] for quality in quality_indices], dim=-1),
                    dim=-1,
                    keepdim=True,
                )
            )
    return root_logits, major_minor_logits, torch.cat(joint, dim=-1)


def build_student_model() -> Any:
    torch, nn, _functional = _torch_modules()

    class ResidualBlock(nn.Module):
        def __init__(self, channels: int, dilation: int) -> None:
            super().__init__()
            self.conv = nn.Conv1d(channels, channels, 5, padding=2 * dilation, dilation=dilation)
            self.norm = nn.GroupNorm(1, channels)

        def forward(self, inputs: Any) -> Any:
            return inputs + torch.nn.functional.gelu(self.norm(self.conv(inputs)))

    class TemporalChordNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.input = nn.Conv1d(STUDENT_FEATURES, 64, 1)
            self.blocks = nn.Sequential(*(ResidualBlock(64, dilation) for dilation in (1, 2, 4, 8)))
            self.output = nn.Conv1d(64, STUDENT_CLASSES, 1)

        def forward(self, inputs: Any) -> Any:
            hidden = torch.nn.functional.gelu(self.input(inputs.transpose(1, 2)))
            return self.output(self.blocks(hidden)).transpose(1, 2)

    return TemporalChordNet()


def _cache_windows(paths: list[Path], window_frames: int, numpy: Any) -> list[tuple[Any, Any, Any, float]]:
    output: list[tuple[Any, Any, Any, float]] = []
    for path in paths:
        with numpy.load(path) as value:
            features = value["features"].astype(numpy.float32)
            labels = value["labels"].astype(numpy.int64)
            weight = float(value["training_weight"])
        for start in range(0, len(features), window_frames):
            chunk_features = features[start : start + window_frames]
            chunk_labels = labels[start : start + window_frames]
            valid = numpy.ones(len(chunk_features), dtype=numpy.float32)
            if len(chunk_features) < window_frames:
                padding = window_frames - len(chunk_features)
                chunk_features = numpy.pad(chunk_features, ((0, padding), (0, 0)))
                chunk_labels = numpy.pad(chunk_labels, (0, padding))
                valid = numpy.pad(valid, (0, padding))
            output.append((chunk_features, chunk_labels, valid, weight))
    return output


def train_student(
    cache_manifest: Mapping[str, Any],
    output_root: Path,
    *,
    epochs: int = 20,
    batch_size: int = 16,
    learning_rate: float = 3e-4,
    device: str = "cpu",
    seed: int = 20260820,
) -> dict[str, Any]:
    numpy = importlib.import_module("numpy")
    torch, _nn, functional = _torch_modules()
    random.seed(seed)
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    paths = {
        split: [Path(item["path"]) for item in cache_manifest["tracks"] if item["split"] == split]
        for split in ("train", "development")
    }
    if not paths["train"] or not paths["development"]:
        raise ValueError("Training requires non-empty train and development feature caches.")
    windows = {split: _cache_windows(value, 256, numpy) for split, value in paths.items()}
    model = build_student_model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    best_score = -1.0
    best_root_accuracy = 0.0
    best_major_minor_accuracy = 0.0
    best_state: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        random.shuffle(windows["train"])
        losses: list[float] = []
        for offset in range(0, len(windows["train"]), batch_size):
            batch = windows["train"][offset : offset + batch_size]
            augment = random.randint(-5, 5)
            feature_values = numpy.stack([item[0] for item in batch])
            label_values = numpy.stack([item[1] for item in batch])
            valid_values = numpy.stack([item[2] for item in batch])
            weights = numpy.asarray([item[3] for item in batch], dtype=numpy.float32)
            if augment:
                feature_values[:, :, :12] = numpy.roll(feature_values[:, :, :12], augment, axis=2)
                label_values = numpy.vectorize(
                    lambda value: transpose_student_index(int(value), augment),
                    otypes=[numpy.int64],
                )(label_values)
            inputs = torch.tensor(feature_values, dtype=torch.float32, device=device)
            targets = torch.tensor(label_values, dtype=torch.long, device=device)
            sample_weights = (
                torch.tensor(weights, dtype=torch.float32, device=device)[:, None]
                * torch.tensor(valid_values, dtype=torch.float32, device=device)
            )
            optimizer.zero_grad(set_to_none=True)
            logits = model(inputs)
            full_loss = functional.cross_entropy(
                logits.reshape(-1, STUDENT_CLASSES),
                targets.reshape(-1),
                reduction="none",
            ).reshape(len(batch), -1)
            root_targets = torch.where(targets == 0, 0, (targets - 1) % 12 + 1)
            quality = torch.where(targets == 0, -1, (targets - 1) // 12)
            major_minor_targets = torch.where(targets == 0, 0, torch.where((quality == 0) | (quality == 2), 1, 2))
            root_logits, major_minor_logits, joint_logits = _hierarchical_logits(logits, torch)
            root_loss = functional.cross_entropy(
                root_logits.reshape(-1, 13), root_targets.reshape(-1), reduction="none"
            ).reshape(len(batch), -1)
            major_minor_loss = functional.cross_entropy(
                major_minor_logits.reshape(-1, 3), major_minor_targets.reshape(-1), reduction="none"
            ).reshape(len(batch), -1)
            joint_targets = torch.where(
                targets == 0,
                0,
                1 + (targets - 1) % 12 + torch.where((quality == 1) | (quality == 3), 12, 0),
            )
            joint_loss = functional.cross_entropy(
                joint_logits.reshape(-1, 25), joint_targets.reshape(-1), reduction="none"
            ).reshape(len(batch), -1)
            loss_values = 0.15 * full_loss + 0.5 * root_loss + 0.2 * major_minor_loss + 1.2 * joint_loss
            loss = (loss_values * sample_weights).sum() / sample_weights.sum().clamp_min(1)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))

        model.eval()
        correct = root_correct = major_minor_correct = joint_correct = total = 0
        with torch.no_grad():
            for features, labels, valid, _weight in windows["development"]:
                logits = model(torch.tensor(features[None], dtype=torch.float32, device=device))
                predicted = logits.argmax(dim=-1).cpu().numpy()[0]
                mask = valid.astype(bool)
                correct += int((predicted[mask] == labels[mask]).sum())
                predicted_root = numpy.where(predicted == 0, 0, (predicted - 1) % 12 + 1)
                label_root = numpy.where(labels == 0, 0, (labels - 1) % 12 + 1)
                predicted_quality = numpy.where(predicted == 0, -1, (predicted - 1) // 12)
                label_quality = numpy.where(labels == 0, -1, (labels - 1) // 12)
                predicted_major_minor = numpy.where(predicted == 0, 0, numpy.where(numpy.isin(predicted_quality, (0, 2)), 1, 2))
                label_major_minor = numpy.where(labels == 0, 0, numpy.where(numpy.isin(label_quality, (0, 2)), 1, 2))
                root_correct += int((predicted_root[mask] == label_root[mask]).sum())
                major_minor_correct += int((predicted_major_minor[mask] == label_major_minor[mask]).sum())
                joint_correct += int(
                    ((predicted_root[mask] == label_root[mask]) & (predicted_major_minor[mask] == label_major_minor[mask])).sum()
                )
                total += int(mask.sum())
        accuracy = correct / max(1, total)
        root_accuracy = root_correct / max(1, total)
        major_minor_accuracy = major_minor_correct / max(1, total)
        joint_accuracy = joint_correct / max(1, total)
        score = 0.25 * root_accuracy + 0.75 * joint_accuracy
        history.append(
            {
                "epoch": epoch,
                "trainLoss": sum(losses) / max(1, len(losses)),
                "developmentFrameAccuracy": accuracy,
                "developmentRootAccuracy": root_accuracy,
                "developmentMajorMinorAccuracy": major_minor_accuracy,
                "developmentMajorMinorWcsrProxy": joint_accuracy,
                "selectionScore": score,
            }
        )
        if score > best_score:
            best_score = score
            best_root_accuracy = root_accuracy
            best_major_minor_accuracy = joint_accuracy
            best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
    assert best_state is not None
    model.load_state_dict(best_state)
    output_root.mkdir(parents=True, exist_ok=True)
    safetensors = importlib.import_module("safetensors.torch")
    weights_path = output_root / "chord-student-v1.safetensors"
    safetensors.save_file(best_state, str(weights_path))
    config = {
        "schemaVersion": STUDENT_SCHEMA,
        "sampleRate": STUDENT_SAMPLE_RATE,
        "frameSeconds": STUDENT_FRAME_SECONDS,
        "featureCount": STUDENT_FEATURES,
        "classCount": STUDENT_CLASSES,
        "qualities": list(STUDENT_QUALITIES),
        "seed": seed,
        "epochs": epochs,
        "bestDevelopmentRootAccuracy": best_root_accuracy,
        "bestDevelopmentMajorMinorWcsrProxy": best_major_minor_accuracy,
        "bestSelectionScore": best_score,
        "history": history,
        "weights": weights_path.name,
    }
    (output_root / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def export_student_onnx(model_root: Path, output: Path) -> dict[str, Any]:
    torch, _nn, _functional = _torch_modules()
    safetensors = importlib.import_module("safetensors.torch")
    model = build_student_model()
    model.load_state_dict(safetensors.load_file(str(model_root / "chord-student-v1.safetensors")))
    model.eval()
    example = torch.zeros((1, 256, STUDENT_FEATURES), dtype=torch.float32)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model,
        example,
        str(output),
        input_names=["features"],
        output_names=["logits"],
        dynamic_axes={"features": {0: "batch", 1: "frames"}, "logits": {0: "batch", 1: "frames"}},
        opset_version=17,
        dynamo=False,
    )
    runtime = importlib.import_module("onnxruntime")
    session = runtime.InferenceSession(str(output), providers=["CPUExecutionProvider"])
    expected = model(example).detach().numpy()
    actual = session.run(None, {"features": example.numpy()})[0]
    numpy = importlib.import_module("numpy")
    maximum_error = float(numpy.max(numpy.abs(expected - actual)))
    if maximum_error > 1e-4:
        raise ValueError(f"ONNX parity failed with max error {maximum_error}.")
    return {
        "schemaVersion": "chord_onnx_export_v1",
        "modelFile": output.name,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "bytes": output.stat().st_size,
        "opset": 17,
        "maximumAbsoluteError": maximum_error,
    }


def _viterbi_student(logits: Any, numpy: Any) -> list[int]:
    emissions = logits - numpy.log(numpy.exp(logits - logits.max(axis=1, keepdims=True)).sum(axis=1, keepdims=True))
    emissions -= logits.max(axis=1, keepdims=True)
    transition = numpy.full((STUDENT_CLASSES, STUDENT_CLASSES), -1.2, dtype=numpy.float32)
    numpy.fill_diagonal(transition, 0)
    transition[0, :] = -0.8
    transition[:, 0] = -0.8
    transition[0, 0] = 0
    for left in range(1, STUDENT_CLASSES):
        for right in range(1, STUDENT_CLASSES):
            if (left - 1) % 12 == (right - 1) % 12:
                transition[left, right] = -0.45
    scores = emissions[0]
    backpointers: list[Any] = []
    for frame in range(1, len(emissions)):
        candidates = scores[:, None] + transition
        pointers = candidates.argmax(axis=0)
        scores = candidates[pointers, numpy.arange(STUDENT_CLASSES)] + emissions[frame]
        backpointers.append(pointers)
    path = [int(scores.argmax())]
    for pointers in reversed(backpointers):
        path.append(int(pointers[path[-1]]))
    return list(reversed(path))


class StudentRecognizer:
    def __init__(self, model: Path) -> None:
        runtime = importlib.import_module("onnxruntime")
        self.numpy = importlib.import_module("numpy")
        self.session = runtime.InferenceSession(str(model), providers=["CPUExecutionProvider"])
        self.model = model

    def predict(self, audio: Path, *, prediction_id: str | None = None) -> dict[str, Any]:
        features, duration = worker_compatible_features(audio)
        logits = self.session.run(None, {"features": features[None].astype(self.numpy.float32)})[0][0]
        probabilities = self.numpy.exp(logits - logits.max(axis=1, keepdims=True))
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        indices = _viterbi_student(logits, self.numpy)
        confidences = [float(probabilities[index, value]) for index, value in enumerate(indices)]
        segments: list[dict[str, Any]] = []
        start = 0
        for frame in range(1, len(indices) + 1):
            if frame < len(indices) and indices[frame] == indices[start]:
                continue
            end_seconds = duration if frame == len(indices) else min(duration, frame * STUDENT_FRAME_SECONDS)
            start_seconds = 0.0 if start == 0 else min(duration, start * STUDENT_FRAME_SECONDS)
            label = normalize_chord(student_label(indices[start]))
            if end_seconds > start_seconds:
                segments.append(
                    {
                        "start": start_seconds,
                        "end": end_seconds,
                        "label": label.detailed_symbol,
                        "productLabel": label.product_symbol,
                        "confidence": sum(confidences[start:frame]) / (frame - start),
                    }
                )
            start = frame
        return {
            "schemaVersion": "chord_prediction_v1",
            "id": prediction_id or audio.name,
            "engine": "chord-student-v1",
            "model": self.model.name,
            "durationSeconds": duration,
            "sampleRate": STUDENT_SAMPLE_RATE,
            "frameSeconds": STUDENT_FRAME_SECONDS,
            "segments": segments,
        }
