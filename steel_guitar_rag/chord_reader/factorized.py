"""Expanded, factorized chord reader used by the v9 architecture tournament.

The v8 student emits one of 49 joint root/quality states.  This module keeps
root, harmonic mode, quality structure, exact quality, inversion, and boundary
evidence in separate heads so adding a chord quality cannot steal probability
mass from an otherwise correct root.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable, Mapping, Sequence

from .artifact_integrity import validate_factorized_artifact_manifest
from .labels import (
    DOMINANT_FAMILY,
    MAJOR_FAMILY,
    MINOR_FAMILY,
    MINOR_SEVENTH_FAMILY,
    PITCH_CLASS,
    SHARP_NAMES,
    normalize_chord,
)
from .routing import FactorizedEvidence
from .segmental import (
    BEAT_GRID_SCHEMA,
    SEGMENTAL_SCHEMA,
    BeatGrid,
    SegmentalConfig,
    decode_factorized_segments,
    usable_beat_grid,
)
from .split_protocol import (
    SPLIT_PROTOCOL_SCHEMA,
    output_manifest_sha256,
    validate_split_protocol_manifest,
)
from .student import STUDENT_FEATURE_KINDS, STUDENT_FRAME_SECONDS, STUDENT_SAMPLE_RATE


FACTORIZED_SCHEMA = "chord_factorized_model_v2"
FACTORIZED_LABEL_SCHEMA = "chord_factorized_label_cache_v2"
FACTORIZED_TRAINING_CONTRACT_SCHEMA = "chord_factorized_training_contract_v1"
FACTORIZED_ENSEMBLE_SCHEMA = "chord_factorized_logit_ensemble_v1"
FACTORIZED_ENSEMBLE_DECODER_SCHEMA = "chord_factorized_ensemble_decoder_v1"
FACTORIZED_ENSEMBLE_PROVENANCE_SCHEMA = "chord_factorized_ensemble_provenance_v1"
FACTORIZED_OPTIONAL_HEADS_SCHEMA = "chord_factorized_optional_heads_v1"
JOINT_ROOT_PRODUCT_SCHEMA = "chord_joint_root_product_head_v1"
JOINT_ROOT_PRODUCT_CLASSES = 1 + 12 * 4

# These are exact normalized quality strings present in the public development
# corpora, plus common lesson-chart extensions. Unknown qualities remain valid
# for root/mode/structure training but are excluded from the exact-quality loss.
FACTORIZED_QUALITIES = (
    "maj",
    "min",
    "7",
    "min7",
    "maj7",
    "6",
    "maj6",
    "min6",
    "9",
    "min9",
    "maj9",
    "11",
    "min11",
    "maj11",
    "13",
    "min13",
    "maj13",
    "sus2",
    "sus4",
    "dim",
    "dim7",
    "hdim7",
    "aug",
    "5",
    "add9",
    "minmaj7",
    "7b5",
    "7b9",
    "7#9",
    "7#5",
    # Harte interval-list spellings found in AAM are retained exactly so the
    # detailed metric has a reachable target rather than silently simplifying.
    "3,5,b7,b9",
    "3,5,b9",
    "3,5,#6",
    "3,b5,b7",
    "b5,b7",
    "3,b5,b7,b9",
    "min*3",
    "4,5,b9",
    "3,#5,7",
    "b9",
    "3,b5,b9",
)
QUALITY_INDEX = {quality: index for index, quality in enumerate(FACTORIZED_QUALITIES)}

FACTORIZED_MODES = ("none", "major", "minor", "neutral")
MODE_INDEX = {mode: index for index, mode in enumerate(FACTORIZED_MODES)}

# The Play Along label is intentionally independent from the scientific rich
# label. A correct Cmaj7 may be shown as C even when the exact-quality head is
# uncertain; conversely, an over-eager seventh prediction must not corrupt an
# otherwise correct product chord.
FACTORIZED_PRODUCTS = ("none", "major", "minor", "dominant", "minor-seventh")
PRODUCT_INDEX = {product: index for index, product in enumerate(FACTORIZED_PRODUCTS)}

FACTORIZED_STRUCTURES = (
    "none",
    "triad",
    "seventh",
    "sixth",
    "ninth",
    "eleventh",
    "thirteenth",
    "suspended",
    "diminished",
    "augmented",
    "power",
    "added-tone",
    "other",
)
STRUCTURE_INDEX = {structure: index for index, structure in enumerate(FACTORIZED_STRUCTURES)}

ROOT_CLASSES = 13  # no-chord plus 12 pitch classes
MODE_CLASSES = len(FACTORIZED_MODES)
PRODUCT_CLASSES = len(FACTORIZED_PRODUCTS)
STRUCTURE_CLASSES = len(FACTORIZED_STRUCTURES)
QUALITY_CLASSES = len(FACTORIZED_QUALITIES)
BASS_CLASSES = 13  # no explicit inversion plus 12 pitch classes
BOUNDARY_CLASSES = 1
OUTPUT_WIDTH = (
    ROOT_CLASSES
    + MODE_CLASSES
    + PRODUCT_CLASSES
    + STRUCTURE_CLASSES
    + QUALITY_CLASSES
    + BASS_CLASSES
    + BOUNDARY_CLASSES
)
JOINT_ROOT_PRODUCT_OUTPUT_WIDTH = OUTPUT_WIDTH + JOINT_ROOT_PRODUCT_CLASSES


def joint_root_product_class(root: int, product: int) -> int:
    """Map N or one root/product pair into the optional 49-state head."""

    if root == 0 and product == PRODUCT_INDEX["none"]:
        return 0
    if not 1 <= root <= 12:
        raise ValueError("A joint chord state requires root class 1..12, or N/N.")
    if product not in {
        PRODUCT_INDEX["major"],
        PRODUCT_INDEX["minor"],
        PRODUCT_INDEX["dominant"],
        PRODUCT_INDEX["minor-seventh"],
    }:
        raise ValueError("A pitched joint chord state requires a Play Along product class.")
    return 1 + (product - 1) * 12 + (root - 1)


def joint_root_product_components(value: int) -> tuple[int, int]:
    """Invert :func:`joint_root_product_class`."""

    if value == 0:
        return 0, PRODUCT_INDEX["none"]
    if not 1 <= value < JOINT_ROOT_PRODUCT_CLASSES:
        raise ValueError(
            f"Joint root/product class must be from 0 to {JOINT_ROOT_PRODUCT_CLASSES - 1}."
        )
    encoded = value - 1
    return encoded % 12 + 1, encoded // 12 + 1


def transpose_joint_root_product_class(value: int, semitones: int) -> int:
    """Transpose only the root coordinate of one optional joint-head class."""

    root, product = joint_root_product_components(value)
    if root == 0:
        return 0
    return joint_root_product_class(1 + ((root - 1 + semitones) % 12), product)


def _joint_root_product_contract() -> dict[str, Any]:
    return {
        "schemaVersion": JOINT_ROOT_PRODUCT_SCHEMA,
        "classes": JOINT_ROOT_PRODUCT_CLASSES,
        "outputOffset": OUTPUT_WIDTH,
        "products": list(FACTORIZED_PRODUCTS[1:]),
        "roots": list(SHARP_NAMES),
        "classOrdering": "N; then listed product blocks, each in listed root order",
    }


def _factorized_output_width(joint_root_product: bool) -> int:
    return JOINT_ROOT_PRODUCT_OUTPUT_WIDTH if joint_root_product else OUTPUT_WIDTH


def _factorized_head_order(joint_root_product: bool) -> tuple[str, ...]:
    return _FACTORIZED_HEAD_ORDER + (("joint_root_product",) if joint_root_product else ())


def factorized_vocabulary_labels() -> tuple[str, ...]:
    """Return every rich label that the factorized decoder can emit.

    The compact prediction contract stores the quality list and inversion flag
    instead of repeating this expanded vocabulary in every per-track JSON.
    Evaluators may expand the same contract when calculating an exact ceiling.
    """

    values = ["N"]
    for root_index, root in enumerate(SHARP_NAMES):
        for quality in FACTORIZED_QUALITIES:
            values.append(f"{root}:{quality}")
            values.extend(
                f"{root}:{quality}/{bass}"
                for bass_index, bass in enumerate(SHARP_NAMES)
                if bass_index != root_index
            )
    return tuple(values)


def quality_mode(quality: str) -> str:
    """Map an exact quality to a coarse harmonic mode without losing detail."""

    if quality in MAJOR_FAMILY or quality in DOMINANT_FAMILY or quality.startswith(("maj", "3,")):
        return "major"
    if quality in MINOR_FAMILY or quality in MINOR_SEVENTH_FAMILY or quality.startswith("min"):
        return "minor"
    return "neutral"


def quality_structure(quality: str) -> str:
    """Map a normalized quality to the factorized structural family."""

    if quality in {"maj", "min"}:
        return "triad"
    if quality in {"7", "min7", "maj7", "minmaj7", "7b5", "7b9", "7#9", "7#5"}:
        return "seventh"
    if quality in {"6", "maj6", "min6"}:
        return "sixth"
    if quality in {"9", "min9", "maj9"}:
        return "ninth"
    if quality in {"11", "min11", "maj11"}:
        return "eleventh"
    if quality in {"13", "min13", "maj13"}:
        return "thirteenth"
    if quality in {"sus2", "sus4"}:
        return "suspended"
    if quality in {"dim", "dim7", "hdim7"} or "b5" in quality:
        return "diminished"
    if quality == "aug" or "#5" in quality:
        return "augmented"
    if quality == "5":
        return "power"
    if quality == "add9":
        return "added-tone"
    if quality in {"3,5,b7,b9", "3,5,b9", "3,5,#6", "min*3", "4,5,b9", "b9"}:
        return "other"
    return "other"


def product_class(symbol: str | None) -> int:
    """Return the independent five-way Play Along product family."""

    label = normalize_chord(symbol)
    if label.root is None:
        return PRODUCT_INDEX["none"]
    suffix = label.product_symbol[len(label.root) :]
    if suffix == "m7":
        return PRODUCT_INDEX["minor-seventh"]
    if suffix == "m":
        return PRODUCT_INDEX["minor"]
    if suffix == "7":
        return PRODUCT_INDEX["dominant"]
    return PRODUCT_INDEX["major"]


def product_symbol(root: int, product: int) -> str:
    if root == 0 or product == PRODUCT_INDEX["none"]:
        return "N.C."
    root_name = SHARP_NAMES[root - 1]
    suffix = {
        PRODUCT_INDEX["major"]: "",
        PRODUCT_INDEX["minor"]: "m",
        PRODUCT_INDEX["dominant"]: "7",
        PRODUCT_INDEX["minor-seventh"]: "m7",
    }.get(product)
    if suffix is None:
        raise ValueError(f"Unsupported product class {product}.")
    return root_name + suffix


def factorized_components(symbol: str | None) -> dict[str, int | bool | str]:
    """Return loss targets for one rich chord symbol."""

    label = normalize_chord(symbol)
    if label.root is None:
        supported = label.quality == "none"
        return {
            "root": 0,
            "mode": MODE_INDEX["none"],
            "product": PRODUCT_INDEX["none"],
            "structure": STRUCTURE_INDEX["none"],
            "quality": -1,
            "qualitySupported": supported,
            "bass": 0,
            "detailed": label.detailed_symbol,
        }
    quality = label.quality
    return {
        "root": PITCH_CLASS[label.root] + 1,
        "mode": MODE_INDEX[quality_mode(quality)],
        "product": product_class(symbol),
        "structure": STRUCTURE_INDEX[quality_structure(quality)],
        "quality": QUALITY_INDEX.get(quality, -1),
        "qualitySupported": quality in QUALITY_INDEX,
        "bass": 0 if label.bass is None else PITCH_CLASS[label.bass] + 1,
        "detailed": label.detailed_symbol,
    }


def factorized_symbol(root: int, quality: int, bass: int = 0) -> str:
    """Reconstruct a canonical detailed symbol from independent head classes."""

    if root == 0:
        return "N"
    if not 1 <= root <= 12:
        raise ValueError(f"Root class must be from 0 to 12, received {root}.")
    if not 0 <= quality < QUALITY_CLASSES:
        raise ValueError(f"Quality class must be from 0 to {QUALITY_CLASSES - 1}, received {quality}.")
    root_name = SHARP_NAMES[root - 1]
    symbol = f"{root_name}:{FACTORIZED_QUALITIES[quality]}"
    if bass:
        if not 1 <= bass <= 12:
            raise ValueError(f"Bass class must be from 0 to 12, received {bass}.")
        bass_name = SHARP_NAMES[bass - 1]
        if bass_name != root_name:
            symbol += f"/{bass_name}"
    return symbol


def _frame_component_labels(segments: Iterable[Mapping[str, Any]], frame_count: int, numpy: Any) -> dict[str, Any]:
    values = sorted(segments, key=lambda item: float(item["start"]))
    output = {
        "root": numpy.zeros(frame_count, dtype=numpy.int64),
        "mode": numpy.zeros(frame_count, dtype=numpy.int64),
        "product": numpy.zeros(frame_count, dtype=numpy.int64),
        "structure": numpy.zeros(frame_count, dtype=numpy.int64),
        "quality": numpy.full(frame_count, -1, dtype=numpy.int64),
        "bass": numpy.zeros(frame_count, dtype=numpy.int64),
        "label_valid": numpy.zeros(frame_count, dtype=numpy.bool_),
    }
    index = 0
    for frame in range(frame_count):
        center = frame * STUDENT_FRAME_SECONDS
        while index + 1 < len(values) and float(values[index]["end"]) <= center:
            index += 1
        if not values or not (float(values[index]["start"]) <= center < float(values[index]["end"])):
            continue
        components = factorized_components(str(values[index]["label"]))
        output["root"][frame] = int(components["root"])
        output["mode"][frame] = int(components["mode"])
        output["product"][frame] = int(components["product"])
        output["structure"][frame] = int(components["structure"])
        output["quality"][frame] = int(components["quality"])
        output["bass"][frame] = int(components["bass"])
        output["label_valid"][frame] = True
    boundary = numpy.zeros(frame_count, dtype=numpy.float32)
    if frame_count > 1:
        changed = (
            (output["root"][1:] != output["root"][:-1])
            | (output["quality"][1:] != output["quality"][:-1])
            | (output["bass"][1:] != output["bass"][:-1])
        )
        boundary[1:] = changed.astype(numpy.float32)
    output["boundary"] = boundary
    return output


def cache_factorized_labels(
    feature_manifest: Mapping[str, Any],
    track_manifests: Iterable[Mapping[str, Any]],
    output_root: Path,
) -> dict[str, Any]:
    """Attach rich sidecar targets to an existing frozen feature cache.

    Features are not copied. This preserves the exact existing-feature control
    used by the v9 architecture tournament while making the detailed labels
    independently auditable.
    """

    numpy = importlib.import_module("numpy")
    source_by_id: dict[str, Mapping[str, Any]] = {}
    for manifest in track_manifests:
        for track in manifest.get("tracks", []):
            identifier = str(track["id"])
            if identifier in source_by_id:
                raise ValueError(f"Duplicate source track {identifier!r}.")
            source_by_id[identifier] = track
    tracks: list[dict[str, Any]] = []
    unsupported_duration = total_duration = 0.0
    for item in feature_manifest.get("tracks", []):
        identifier = str(item["id"])
        source = source_by_id.get(identifier)
        if source is None:
            raise ValueError(f"No reference metadata was supplied for cached track {identifier!r}.")
        if str(source.get("datasetId")) != str(item.get("datasetId")):
            raise ValueError(f"Cached and source dataset ids disagree for {identifier!r}.")
        if str(source.get("split")) != str(item.get("split")):
            raise ValueError(f"Cached and source splits disagree for {identifier!r}.")
        with numpy.load(Path(item["path"])) as cached:
            frame_count = len(cached["features"])
        reference = json.loads(Path(source["referencePath"]).read_text(encoding="utf-8"))
        labels = _frame_component_labels(reference["segments"], frame_count, numpy)
        sidecar = output_root / str(item["split"]) / f"{identifier}.npz"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        numpy.savez_compressed(sidecar, **labels)
        for segment in reference["segments"]:
            duration = float(segment["end"]) - float(segment["start"])
            total_duration += duration
            if not bool(factorized_components(str(segment["label"]))["qualitySupported"]):
                unsupported_duration += duration
        identity = {
            name: source[name]
            for name in ("compositionId", "groupId", "splitGroup")
            if name in source
        }
        for name, value in identity.items():
            if name in item and item[name] != value:
                raise ValueError(
                    f"Cached and source {name} values disagree for {identifier!r}."
                )
        tracks.append(
            {
                **item,
                **identity,
                "factorizedLabelsPath": str(sidecar.resolve()),
            }
        )
    return {
        **feature_manifest,
        "schemaVersion": FACTORIZED_LABEL_SCHEMA,
        "factorizedVocabulary": {
            "qualities": list(FACTORIZED_QUALITIES),
            "modes": list(FACTORIZED_MODES),
            "products": list(FACTORIZED_PRODUCTS),
            "structures": list(FACTORIZED_STRUCTURES),
            "rootClasses": ROOT_CLASSES,
            "bassClasses": BASS_CLASSES,
        },
        "exactQualityVocabularyDurationSeconds": max(0.0, total_duration - unsupported_duration),
        "outOfVocabularyDurationSeconds": unsupported_duration,
        "exactQualityVocabularyCoverage": (total_duration - unsupported_duration) / max(1e-12, total_duration),
        "tracks": tracks,
    }


def _torch_modules() -> tuple[Any, Any, Any]:
    torch = importlib.import_module("torch")
    return torch, torch.nn, torch.nn.functional


def build_factorized_model(
    feature_count: int,
    architecture: str = "transformer",
    *,
    joint_root_product: bool = False,
) -> Any:
    """Build a shared temporal encoder with independent musical heads."""

    torch, nn, _functional = _torch_modules()
    if architecture not in {"tcn", "transformer"}:
        raise ValueError(f"Unsupported factorized architecture {architecture!r}.")

    class ResidualBlock(nn.Module):
        def __init__(self, channels: int, dilation: int) -> None:
            super().__init__()
            self.conv = nn.Conv1d(channels, channels, 5, padding=2 * dilation, dilation=dilation)
            self.norm = nn.GroupNorm(1, channels)

        def forward(self, inputs: Any) -> Any:
            return inputs + torch.nn.functional.gelu(self.norm(self.conv(inputs)))

    class FactorizedChordNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            channels = 128 if architecture == "transformer" else 96
            # Keep the temporal head matched across low-dimensional chroma/CQT
            # and high-dimensional pretrained embeddings. A five-tap input
            # convolution would give a 768-D SSL challenger roughly five times
            # the projection compute of the existing-feature control.
            self.input_norm = nn.LayerNorm(feature_count)
            self.input = nn.Linear(feature_count, channels)
            if architecture == "transformer":
                layer = nn.TransformerEncoderLayer(
                    d_model=channels,
                    nhead=4,
                    dim_feedforward=384,
                    dropout=0.1,
                    activation="gelu",
                    batch_first=True,
                    norm_first=False,
                )
                self.temporal = nn.TransformerEncoder(layer, num_layers=4)
            else:
                self.temporal = nn.Sequential(
                    *(ResidualBlock(channels, dilation) for dilation in (1, 2, 4, 8, 16))
                )
            self.root = nn.Linear(channels, ROOT_CLASSES)
            self.mode = nn.Linear(channels, MODE_CLASSES)
            self.product = nn.Linear(channels, PRODUCT_CLASSES)
            self.structure = nn.Linear(channels, STRUCTURE_CLASSES)
            self.quality = nn.Linear(channels, QUALITY_CLASSES)
            self.bass = nn.Linear(channels, BASS_CLASSES)
            self.boundary = nn.Linear(channels, BOUNDARY_CLASSES)
            self.joint_root_product = (
                nn.Linear(channels, JOINT_ROOT_PRODUCT_CLASSES)
                if joint_root_product
                else None
            )

        def forward(self, inputs: Any) -> Any:
            hidden = torch.nn.functional.gelu(self.input(self.input_norm(inputs)))
            if architecture == "transformer":
                hidden = self.temporal(hidden)
            else:
                hidden = self.temporal(hidden.transpose(1, 2)).transpose(1, 2)
            outputs = (
                self.root(hidden),
                self.mode(hidden),
                self.product(hidden),
                self.structure(hidden),
                self.quality(hidden),
                self.bass(hidden),
                self.boundary(hidden),
            )
            if self.joint_root_product is not None:
                outputs = (*outputs, self.joint_root_product(hidden))
            return torch.cat(outputs, dim=-1)

    return FactorizedChordNet()


def split_factorized_outputs(
    outputs: Any,
    *,
    joint_root_product: bool = False,
) -> dict[str, Any]:
    expected_width = _factorized_output_width(joint_root_product)
    if outputs.shape[-1] != expected_width:
        raise ValueError(
            f"Unexpected factorized output width {outputs.shape[-1]}; expected {expected_width}."
        )
    offset = 0
    result: dict[str, Any] = {}
    for name, width in (
        ("root", ROOT_CLASSES),
        ("mode", MODE_CLASSES),
        ("product", PRODUCT_CLASSES),
        ("structure", STRUCTURE_CLASSES),
        ("quality", QUALITY_CLASSES),
        ("bass", BASS_CLASSES),
        ("boundary", BOUNDARY_CLASSES),
    ):
        result[name] = outputs[..., offset : offset + width]
        offset += width
    if joint_root_product:
        result["joint_root_product"] = outputs[
            ..., offset : offset + JOINT_ROOT_PRODUCT_CLASSES
        ]
    return result


def _factorized_windows(
    tracks: Sequence[Mapping[str, Any]], window_frames: int, numpy: Any
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for item in tracks:
        with numpy.load(Path(item["path"])) as cached, numpy.load(Path(item["factorizedLabelsPath"])) as labels:
            features = cached["features"].astype(numpy.float32)
            weight = float(cached["training_weight"]) * float(item.get("trainingWeightOverride", 1))
            arrays = {
                name: labels[name]
                for name in (
                    "root",
                    "mode",
                    "product",
                    "structure",
                    "quality",
                    "bass",
                    "boundary",
                    "label_valid",
                )
            }
        if any(len(value) != len(features) for value in arrays.values()):
            raise ValueError(f"Factorized labels do not align with features for {item['id']!r}.")
        for start in range(0, len(features), window_frames):
            end = start + window_frames
            feature_chunk = features[start:end]
            chunks = {name: value[start:end] for name, value in arrays.items()}
            if len(feature_chunk) < window_frames:
                padding = window_frames - len(feature_chunk)
                feature_chunk = numpy.pad(feature_chunk, ((0, padding), (0, 0)))
                for name in chunks:
                    fill = -1 if name == "quality" else 0
                    chunks[name] = numpy.pad(chunks[name], (0, padding), constant_values=fill)
            windows.append(
                {
                    "id": str(item.get("id", "")),
                    "datasetId": str(item.get("datasetId", "")),
                    "split": str(item.get("split", "")),
                    "features": feature_chunk,
                    "weight": weight,
                    **chunks,
                }
            )
    return windows


def _dataset_balance_statistics(
    windows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """Equalize weighted valid-frame mass while preserving total train mass."""

    contributions: dict[str, list[float]] = {}
    for window in windows:
        if window.get("split") != "train":
            raise ValueError("Dataset balancing may inspect only training windows.")
        dataset_id = str(window.get("datasetId", "")).strip()
        if not dataset_id:
            raise ValueError("Every dataset-balanced training window needs a datasetId.")
        valid_frames = int(window["label_valid"].astype(bool).sum())
        mass = valid_frames * float(window["weight"])
        if not math.isfinite(mass) or mass < 0:
            raise ValueError("Training effective-frame mass must be finite and non-negative.")
        contributions.setdefault(dataset_id, []).append(mass)
    masses = {
        dataset_id: math.fsum(contributions[dataset_id])
        for dataset_id in sorted(contributions)
    }
    if not masses or any(mass <= 0 for mass in masses.values()):
        raise ValueError("Every balanced training dataset needs positive effective-frame mass.")
    target = sum(masses.values()) / len(masses)
    return {
        dataset_id: {
            "effectiveFrameMassBefore": masses[dataset_id],
            "scale": target / masses[dataset_id],
            "effectiveFrameMassAfter": target,
        }
        for dataset_id in sorted(masses)
    }


def _training_window_weight(
    window: Mapping[str, Any],
    dataset_balance: Mapping[str, Mapping[str, float]],
) -> float:
    if not dataset_balance:
        return float(window["weight"])
    dataset_id = str(window.get("datasetId", ""))
    try:
        scale = float(dataset_balance[dataset_id]["scale"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Dataset balance has no valid scale for {dataset_id!r}.") from exc
    return float(window["weight"]) * scale


def _balanced_class_weights(
    windows: Sequence[Mapping[str, Any]],
    key: str,
    classes: int,
    numpy: Any,
    *,
    dataset_balance: Mapping[str, Mapping[str, float]] | None = None,
) -> Any:
    counts = numpy.zeros(classes, dtype=numpy.float64)
    balance = dataset_balance or {}
    for window in windows:
        labels = window[key]
        mask = window["label_valid"].astype(bool) & (labels >= 0)
        if mask.any():
            counts += numpy.bincount(labels[mask], minlength=classes) * _training_window_weight(
                window,
                balance,
            )
    frequencies = counts / max(1e-12, counts.sum())
    weights = numpy.sqrt((1 / classes) / numpy.maximum(frequencies, 1e-7))
    weights = numpy.clip(weights, 0.35, 4.0)
    return (weights / weights.mean()).astype(numpy.float32)


def _augment_features(features: Any, semitones: int, feature_kind: str, numpy: Any) -> None:
    if not semitones:
        return
    if feature_kind == "harmonic_cqt_v3":
        for start in (0, 72):
            original = features[:, :, start : start + 72].copy()
            features[:, :, start : start + 72] = 0
            if semitones > 0:
                features[:, :, start + semitones : start + 72] = original[:, :, : 72 - semitones]
            else:
                features[:, :, start : start + 72 + semitones] = original[:, :, -semitones:]
        return
    if feature_kind not in {"multiband_chroma_v2", "worker_chroma_v1"}:
        raise ValueError(f"Pitch-roll augmentation is not defined for feature kind {feature_kind!r}.")
    chroma_features = 60 if feature_kind == "multiband_chroma_v2" else 12
    for start in range(0, chroma_features, 12):
        features[:, :, start : start + 12] = numpy.roll(
            features[:, :, start : start + 12], semitones, axis=2
        )


def _transpose_classes(values: Any, semitones: int, numpy: Any) -> Any:
    return numpy.where(values == 0, 0, 1 + ((values - 1 + semitones) % 12))


def _joint_root_product_targets(roots: Any, products: Any, numpy: Any) -> Any:
    """Vectorize the optional 49-state target without reading another split."""

    root_values = numpy.asarray(roots)
    product_values = numpy.asarray(products)
    if root_values.shape != product_values.shape:
        raise ValueError("Joint root/product target arrays must have matching shapes.")
    no_chord = (root_values == 0) & (product_values == PRODUCT_INDEX["none"])
    pitched = (
        (root_values >= 1)
        & (root_values <= 12)
        & (product_values >= PRODUCT_INDEX["major"])
        & (product_values <= PRODUCT_INDEX["minor-seventh"])
    )
    if not numpy.all(no_chord | pitched):
        raise ValueError("Joint root/product targets contain an invalid root/product pair.")
    return numpy.where(
        no_chord,
        0,
        1 + (product_values - 1) * 12 + (root_values - 1),
    ).astype(numpy.int64)


def _joint_root_product_class_weights(product_weights: Any, numpy: Any) -> Any:
    """Expand five train-only product weights across the 49-state vocabulary."""

    values = numpy.asarray(product_weights, dtype=numpy.float32)
    if values.shape != (PRODUCT_CLASSES,) or not numpy.isfinite(values).all():
        raise ValueError("Product class weights must be a finite five-value vector.")
    return numpy.concatenate(
        (values[:1], numpy.repeat(values[1:], 12)),
    ).astype(numpy.float32)


def _validated_joint_product_blend(value: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not 0 <= float(value) <= 1
    ):
        raise ValueError("joint_product_blend must be a finite value from zero to one.")
    return float(value)


def _validated_feature_contract(
    cache_manifest: Mapping[str, Any],
    *,
    augmentation: str,
) -> tuple[str, int, int, Mapping[str, Any] | None]:
    """Validate either a browser feature cache or the exact sealed Dasheng cache."""

    feature_kind = str(cache_manifest.get("featureKind") or "")
    feature_count = int(cache_manifest.get("featureCount", 0))
    sample_rate = int(cache_manifest.get("sampleRate", 0))
    frame_seconds = float(cache_manifest.get("frameSeconds", 0))
    if not math.isclose(frame_seconds, STUDENT_FRAME_SECONDS, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Factorized caches must use the exact 0.1-second frame grid.")
    known_count = STUDENT_FEATURE_KINDS.get(feature_kind)
    if known_count is not None:
        if feature_count != known_count or sample_rate != STUDENT_SAMPLE_RATE:
            raise ValueError("Factorized browser feature kind, count, and sample rate do not match.")
        policy = cache_manifest.get("augmentationPolicy")
        if policy is not None and str(policy) != augmentation:
            raise ValueError("Requested augmentation does not match the frozen feature-cache policy.")
        feature_spec_sha256 = cache_manifest.get("featureSpecSha256")
        if feature_spec_sha256 is not None and (
            not isinstance(feature_spec_sha256, str)
            or len(feature_spec_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in feature_spec_sha256
            )
        ):
            raise ValueError("Factorized browser feature-spec hash is invalid.")
        if "splitProtocol" in cache_manifest and feature_spec_sha256 is None:
            raise ValueError(
                "Strict factorized browser training requires a sealed feature-spec hash."
            )
        feature_spec = (
            {
                "schemaVersion": "chord_feature_spec_reference_v1",
                "featureSpecSha256": feature_spec_sha256,
            }
            if feature_spec_sha256 is not None
            else None
        )
        return feature_kind, feature_count, sample_rate, feature_spec
    if feature_kind != "dasheng_base_v1":
        raise ValueError(f"Unsupported factorized feature contract {feature_kind!r}.")

    from .dasheng import dasheng_feature_provenance, load_dasheng_contract
    from .dasheng_cache import dasheng_cache_feature_spec

    expected = dasheng_cache_feature_spec(
        dasheng_feature_provenance(load_dasheng_contract())
    )
    feature_spec = cache_manifest.get("featureSpec")
    if not isinstance(feature_spec, Mapping) or dict(feature_spec) != expected:
        raise ValueError("Factorized Dasheng training requires the exact sealed feature specification.")
    if (
        feature_count != int(expected["featureCount"])
        or sample_rate != int(expected["sampleRate"])
        or cache_manifest.get("featureSpecSha256") != expected["featureSpecSha256"]
        or cache_manifest.get("revision") != expected["revision"]
        or cache_manifest.get("weightSha256") != expected["weightSha256"]
    ):
        raise ValueError("Factorized Dasheng cache provenance does not match its feature specification.")
    if cache_manifest.get("augmentationPolicy") != "none" or augmentation != "none":
        raise ValueError("Dasheng embeddings are sealed to augmentation='none'.")
    for item in cache_manifest.get("tracks", []):
        if item.get("featureSpecSha256") != expected["featureSpecSha256"]:
            raise ValueError("A Dasheng cache track has mismatched feature provenance.")
    return feature_kind, feature_count, sample_rate, expected


def _split_protocol_training_provenance(
    cache_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed on a present protocol and disclose legacy absence."""

    protocol = cache_manifest.get("splitProtocol")
    cache_hash = output_manifest_sha256(cache_manifest)
    if "splitProtocol" not in cache_manifest:
        artifact_integrity = cache_manifest.get("artifactIntegrity")
        if artifact_integrity is not None:
            validate_factorized_artifact_manifest(cache_manifest, verify_files=True)
        return {
            "status": "absent",
            "schemaVersion": None,
            "cacheManifestSha256": cache_hash,
            "assignmentSha256": None,
            "trainSetSha256": None,
            "developmentSetSha256": None,
            "calibrationSetSha256": None,
            "outputManifestSha256": None,
            "artifactIntegrityStatus": (
                "validated" if artifact_integrity is not None else "absent"
            ),
            "artifactSetSha256": (
                artifact_integrity.get("artifactSetSha256")
                if isinstance(artifact_integrity, Mapping)
                else None
            ),
        }
    validate_split_protocol_manifest(cache_manifest)
    if not isinstance(cache_manifest.get("artifactIntegrity"), Mapping):
        raise ValueError(
            "Strict split-protocol training requires an artifactIntegrity seal."
        )
    # Validate the complete signed manifest and full artifact-set seal without
    # touching any partition's files.  File inspection is deliberately scoped
    # to the two partitions that training is permitted to consume below, so
    # the immutable calibration artifacts remain physically unopened.
    validate_factorized_artifact_manifest(cache_manifest, verify_files=False)
    training_partitions = _factorized_training_partitions(cache_manifest)
    verified_tracks = [
        *training_partitions["train"],
        *training_partitions["development"],
    ]
    # This is an artifact-verification projection, not a standalone signed
    # split manifest.  The complete signed protocol was validated above; the
    # artifact validator explicitly permits a selected subset when that signed
    # protocol is present, while retaining the complete seal metadata.
    training_projection = {**cache_manifest, "tracks": verified_tracks}
    validate_factorized_artifact_manifest(training_projection, verify_files=True)
    assert isinstance(protocol, Mapping)
    artifact_integrity = cache_manifest["artifactIntegrity"]
    assert isinstance(artifact_integrity, Mapping)
    partitions = protocol["partitions"]
    calibration = protocol["calibration"]
    return {
        "status": "validated",
        "schemaVersion": SPLIT_PROTOCOL_SCHEMA,
        "cacheManifestSha256": cache_hash,
        "sourceManifestSha256": protocol.get("sourceManifestSha256"),
        "assignmentSha256": protocol["assignmentSha256"],
        "trainSetSha256": partitions["train"]["tracksSha256"],
        "developmentSetSha256": partitions["development"]["tracksSha256"],
        "calibrationSetSha256": calibration["setSha256"],
        "outputManifestSha256": protocol["outputManifestSha256"],
        "artifactIntegrityStatus": "validated",
        "artifactSetSha256": artifact_integrity["artifactSetSha256"],
        "artifactFileVerification": {
            "metadataScope": "full sealed manifest and artifact set",
            "verifiedSplits": ["train", "development"],
            "verifiedTrackCount": len(verified_tracks),
            "calibrationFilesOpened": False,
        },
    }


def _factorized_training_partitions(
    cache_manifest: Mapping[str, Any],
) -> dict[str, list[Mapping[str, Any]]]:
    tracks = cache_manifest.get("tracks")
    if not isinstance(tracks, list):
        raise ValueError("Factorized training manifest tracks must be a list.")
    selected = {
        split: [item for item in tracks if item.get("split") == split]
        for split in ("train", "development")
    }
    if not selected["train"] or not selected["development"]:
        raise ValueError("Factorized training requires non-empty train and development splits.")
    return selected


def _development_counts(*, joint_root_product: bool = False) -> dict[str, int]:
    counts = {
        name: 0
        for name in (
            "total",
            "chord_total",
            "quality_total",
            "root",
            "mode",
            "product",
            "quality",
            "detailed",
            "boundary_tp",
            "boundary_pred",
            "boundary_ref",
        )
    }
    if joint_root_product:
        counts.update(
            {
                "joint_root_product": 0,
                "joint_conditioned_product": 0,
                "selection_product": 0,
            }
        )
    return counts


def _accumulate_development_counts(
    counts: dict[str, int],
    window: Mapping[str, Any],
    predicted: Mapping[str, Any],
    boundary_probabilities: Any,
    *,
    joint_targets: Any | None = None,
) -> None:
    valid_mask = window["label_valid"].astype(bool)
    chord_mask = valid_mask & (window["root"] != 0)
    quality_mask = chord_mask & (window["quality"] >= 0)
    counts["total"] += int(valid_mask.sum())
    counts["chord_total"] += int(chord_mask.sum())
    counts["quality_total"] += int(quality_mask.sum())
    counts["root"] += int(
        (predicted["root"][valid_mask] == window["root"][valid_mask]).sum()
    )
    counts["mode"] += int(
        (predicted["mode"][chord_mask] == window["mode"][chord_mask]).sum()
    )
    counts["product"] += int(
        (
            (predicted["root"][valid_mask] == window["root"][valid_mask])
            & (predicted["product"][valid_mask] == window["product"][valid_mask])
        ).sum()
    )
    if "joint_root_product" in counts:
        if joint_targets is None:
            raise ValueError("Joint development diagnostics require joint targets.")
        counts["joint_root_product"] += int(
            (
                predicted["joint_root_product"][valid_mask]
                == joint_targets[valid_mask]
            ).sum()
        )
        counts["joint_conditioned_product"] += int(
            (
                (predicted["root"][valid_mask] == window["root"][valid_mask])
                & (
                    predicted["joint_conditioned_product"][valid_mask]
                    == window["product"][valid_mask]
                )
            ).sum()
        )
        counts["selection_product"] += int(
            (
                (predicted["root"][valid_mask] == window["root"][valid_mask])
                & (
                    predicted["selection_product"][valid_mask]
                    == window["product"][valid_mask]
                )
            ).sum()
        )
    counts["quality"] += int(
        (predicted["quality"][quality_mask] == window["quality"][quality_mask]).sum()
    )
    detailed = (
        (predicted["root"] == window["root"])
        & (predicted["quality"] == window["quality"])
        & (predicted["bass"] == window["bass"])
    )
    counts["detailed"] += int(detailed[quality_mask].sum())
    reference = {
        index
        for index in range(1, len(boundary_probabilities))
        if valid_mask[index]
        and valid_mask[index - 1]
        and window["boundary"][index] > 0.5
    }
    found = {
        index
        for index in range(1, len(boundary_probabilities))
        if valid_mask[index]
        and valid_mask[index - 1]
        and boundary_probabilities[index] >= 0.5
    }
    matched: set[int] = set()
    for boundary in found:
        choices = [
            candidate
            for candidate in reference
            if candidate not in matched and abs(candidate - boundary) <= 2
        ]
        if choices:
            matched.add(min(choices, key=lambda candidate: abs(candidate - boundary)))
    counts["boundary_tp"] += len(matched)
    counts["boundary_pred"] += len(found)
    counts["boundary_ref"] += len(reference)


def _development_metrics(counts: Mapping[str, int]) -> dict[str, float]:
    boundary_precision = counts["boundary_tp"] / max(1, counts["boundary_pred"])
    boundary_recall = counts["boundary_tp"] / max(1, counts["boundary_ref"])
    metrics = {
        "rootAccuracy": counts["root"] / max(1, counts["total"]),
        "modeAccuracy": counts["mode"] / max(1, counts["chord_total"]),
        "productAccuracy": counts["product"] / max(1, counts["total"]),
        "qualityAccuracy": counts["quality"] / max(1, counts["quality_total"]),
        "detailedAccuracy": counts["detailed"] / max(1, counts["quality_total"]),
        "boundaryF1": 2
        * boundary_precision
        * boundary_recall
        / max(1e-12, boundary_precision + boundary_recall),
    }
    if "joint_root_product" in counts:
        metrics.update(
            {
                "jointRootProductAccuracy": counts["joint_root_product"]
                / max(1, counts["total"]),
                "jointConditionedProductAccuracy": counts[
                    "joint_conditioned_product"
                ]
                / max(1, counts["total"]),
                "selectionProductAccuracy": counts["selection_product"]
                / max(1, counts["total"]),
            }
        )
    return metrics


def _factorized_selection_score(
    metrics: Mapping[str, float],
    *,
    product_metric: str = "productAccuracy",
) -> float:
    return (
        0.25 * metrics["rootAccuracy"]
        + 0.3 * metrics[product_metric]
        + 0.1 * metrics["modeAccuracy"]
        + 0.25 * metrics["detailedAccuracy"]
        + 0.1 * metrics["boundaryF1"]
    )


def _aggregate_factorized_selection(
    micro_metrics: Mapping[str, float],
    dataset_metrics: Mapping[str, Mapping[str, float]],
    *,
    dataset_balance: bool,
    product_metric: str = "productAccuracy",
) -> tuple[float, dict[str, float]]:
    scores = {
        dataset_id: _factorized_selection_score(
            metrics,
            product_metric=product_metric,
        )
        for dataset_id, metrics in sorted(dataset_metrics.items())
    }
    if dataset_balance:
        if not scores:
            raise ValueError("Dataset-macro selection requires development datasets.")
        return sum(scores.values()) / len(scores), scores
    return (
        _factorized_selection_score(
            micro_metrics,
            product_metric=product_metric,
        ),
        scores,
    )


def _factorized_training_contract(
    *,
    protocol: Mapping[str, Any],
    dataset_balance: bool,
    dataset_statistics: Mapping[str, Mapping[str, float]],
    development_datasets: Sequence[str],
    feature_kind: str,
    feature_count: int,
    sample_rate: int,
    architecture: str,
    augmentation: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    window_frames: int,
    joint_root_product: bool = False,
    joint_root_product_loss_weight: float = 0.6,
    product_class_weighting: bool = False,
    joint_root_product_selection_blend: float = 0.5,
) -> dict[str, Any]:
    selection_blend = (
        _validated_joint_product_blend(joint_root_product_selection_blend)
        if joint_root_product
        else 0.0
    )
    contract = {
        "schemaVersion": FACTORIZED_TRAINING_CONTRACT_SCHEMA,
        "splitProtocol": dict(protocol),
        "partitionUse": {
            "train": "model fitting, training losses, and class weights only",
            "development": "epoch selection and reporting only",
            "calibration": "excluded from model fitting and epoch selection",
            "test": "excluded",
            "steel_test": "excluded",
        },
        "datasetBalance": {
            "enabled": dataset_balance,
            "scope": "train-only",
            "massDefinition": (
                "sum(valid frames * cached composition/training weight * "
                "trainingWeightOverride)"
            ),
            "normalization": "inverse mass scaled to preserve total train effective-frame mass",
            "lossNormalization": (
                "scaled numerator with original weighted-frame denominator"
                if dataset_balance
                else "original weighted numerator and denominator"
            ),
            "appliedTo": ["training losses", "training class-frequency weights"],
            "notAppliedTo": ["development metrics", "calibration", "test", "steel_test"],
            "datasets": {
                name: dict(dataset_statistics[name]) for name in sorted(dataset_statistics)
            },
        },
        "selection": {
            "split": "development",
            "aggregation": "dataset-macro" if dataset_balance else "frame-micro",
            "datasetIds": sorted(development_datasets),
            "score": {
                "rootAccuracy": 0.25,
                "productAccuracy": 0.3,
                "modeAccuracy": 0.1,
                "detailedAccuracy": 0.25,
                "boundaryF1": 0.1,
            },
        },
        "featureContract": {
            "featureKind": feature_kind,
            "featureCount": feature_count,
            "sampleRate": sample_rate,
            "frameSeconds": STUDENT_FRAME_SECONDS,
        },
        "optimization": {
            "architecture": architecture,
            "epochs": epochs,
            "batchSize": batch_size,
            "learningRate": learning_rate,
            "optimizer": "AdamW",
            "weightDecay": 1e-4,
            "gradientClipNorm": 5.0,
            "seed": seed,
            "windowFrames": window_frames,
            "augmentation": augmentation,
        },
        "loss": {
            "root": 1.0,
            "mode": 0.35,
            "product": 0.8,
            "structure": 0.35,
            "quality": 0.9,
            "bass": 0.2,
            "boundary": 0.35,
            "boundaryPositiveWeight": 8.0,
            "classWeightPolicy": "sqrt inverse frequency, clipped 0.35..4.0, mean normalized",
        },
    }
    if joint_root_product or product_class_weighting:
        contract["optionalExperiment"] = {
            "schemaVersion": FACTORIZED_OPTIONAL_HEADS_SCHEMA,
            "jointRootProduct": {
                **_joint_root_product_contract(),
                "enabled": joint_root_product,
                "lossWeight": (
                    joint_root_product_loss_weight if joint_root_product else 0.0
                ),
                "targetSource": "train-only root and product sidecar arrays",
                **(
                    {
                        "developmentSelectionBlend": selection_blend,
                    }
                    if joint_root_product
                    else {}
                ),
            },
            "productClassWeighting": {
                "enabled": product_class_weighting,
                "policy": (
                    "sqrt inverse frequency, clipped 0.35..4.0, mean normalized"
                    if product_class_weighting
                    else "none"
                ),
                "scope": "train-only direct product and optional joint target losses",
            },
        }
        contract["loss"]["jointRootProduct"] = (
            joint_root_product_loss_weight if joint_root_product else 0.0
        )
        contract["loss"]["productClassWeighting"] = product_class_weighting
    if joint_root_product:
        contract["selection"]["score"].pop("productAccuracy")
        contract["selection"]["score"]["selectionProductAccuracy"] = 0.3
        contract["selection"]["jointRootProduct"] = {
            "schemaVersion": "chord_joint_root_product_checkpoint_selection_v1",
            "metric": "selectionProductAccuracy",
            "diagnostics": [
                "productAccuracy",
                "jointRootProductAccuracy",
                "jointConditionedProductAccuracy",
                "selectionProductAccuracy",
            ],
            "rootAuthority": "independent root-head frame argmax",
            "noChordPolicy": "independent root N forces product N",
            "pitchedProductEvidence": (
                "four-class conditional direct/joint log-probability blend"
            ),
            "jointProductBlend": selection_blend,
        }
    return contract


def train_factorized_model(
    cache_manifest: Mapping[str, Any],
    output_root: Path,
    *,
    epochs: int = 20,
    batch_size: int = 12,
    learning_rate: float = 3e-4,
    device: str = "cpu",
    seed: int = 20260820,
    architecture: str = "transformer",
    augmentation: str = "none",
    dataset_balance: bool = False,
    joint_root_product: bool = False,
    joint_root_product_loss_weight: float = 0.6,
    product_class_weighting: bool = False,
    joint_root_product_selection_blend: float = 0.5,
) -> dict[str, Any]:
    """Train the existing-feature control for the v9 architecture tournament."""

    if cache_manifest.get("schemaVersion") != FACTORIZED_LABEL_SCHEMA:
        raise ValueError("Factorized training requires a factorized label cache manifest.")
    split_protocol = _split_protocol_training_provenance(cache_manifest)
    if augmentation not in {"none", "pitch-roll"}:
        raise ValueError("Factorized augmentation must be 'none' or 'pitch-roll'.")
    if joint_root_product and (
        isinstance(joint_root_product_loss_weight, bool)
        or not isinstance(joint_root_product_loss_weight, (int, float))
        or not math.isfinite(float(joint_root_product_loss_weight))
        or float(joint_root_product_loss_weight) <= 0
    ):
        raise ValueError("joint_root_product_loss_weight must be a positive finite value.")
    selection_blend = (
        _validated_joint_product_blend(joint_root_product_selection_blend)
        if joint_root_product
        else 0.0
    )
    feature_kind, feature_count, sample_rate, feature_spec = _validated_feature_contract(
        cache_manifest,
        augmentation=augmentation,
    )
    numpy = importlib.import_module("numpy")
    torch, _nn, functional = _torch_modules()
    random.seed(seed)
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    selected = _factorized_training_partitions(cache_manifest)
    window_frames = 256
    windows = {
        split: _factorized_windows(items, window_frames, numpy)
        for split, items in selected.items()
    }
    development_dataset_ids = sorted(
        {str(window["datasetId"]) for window in windows["development"]}
    )
    if dataset_balance and any(not dataset_id for dataset_id in development_dataset_ids):
        raise ValueError("Dataset-macro selection requires development datasetId values.")
    dataset_statistics = (
        _dataset_balance_statistics(windows["train"]) if dataset_balance else {}
    )
    class_weights = {
        "mode": _balanced_class_weights(
            windows["train"],
            "mode",
            MODE_CLASSES,
            numpy,
            dataset_balance=dataset_statistics,
        ),
        "structure": _balanced_class_weights(
            windows["train"],
            "structure",
            STRUCTURE_CLASSES,
            numpy,
            dataset_balance=dataset_statistics,
        ),
        "quality": _balanced_class_weights(
            windows["train"],
            "quality",
            QUALITY_CLASSES,
            numpy,
            dataset_balance=dataset_statistics,
        ),
        "bass": _balanced_class_weights(
            windows["train"],
            "bass",
            BASS_CLASSES,
            numpy,
            dataset_balance=dataset_statistics,
        ),
    }
    if product_class_weighting:
        class_weights["product"] = _balanced_class_weights(
            windows["train"],
            "product",
            PRODUCT_CLASSES,
            numpy,
            dataset_balance=dataset_statistics,
        )
    joint_class_weights = (
        _joint_root_product_class_weights(class_weights["product"], numpy)
        if joint_root_product and product_class_weighting
        else None
    )
    model = build_factorized_model(
        feature_count,
        architecture,
        joint_root_product=joint_root_product,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    best_score = -1.0
    best_state: dict[str, Any] | None = None
    best_metrics: dict[str, float] = {}
    best_dataset_metrics: dict[str, dict[str, float]] = {}
    history: list[dict[str, Any]] = []

    for epoch in range(1, epochs + 1):
        model.train()
        random.shuffle(windows["train"])
        losses: list[float] = []
        for offset in range(0, len(windows["train"]), batch_size):
            batch = windows["train"][offset : offset + batch_size]
            features = numpy.stack([item["features"] for item in batch])
            targets = {
                name: numpy.stack([item[name] for item in batch])
                for name in (
                    "root",
                    "mode",
                    "product",
                    "structure",
                    "quality",
                    "bass",
                    "boundary",
                )
            }
            valid = numpy.stack([item["label_valid"] for item in batch]).astype(numpy.float32)
            base_track_weights = numpy.asarray(
                [float(item["weight"]) for item in batch],
                dtype=numpy.float32,
            )
            track_weights = numpy.asarray(
                [
                    _training_window_weight(item, dataset_statistics)
                    for item in batch
                ],
                dtype=numpy.float32,
            )
            semitones = random.randint(-5, 5) if augmentation == "pitch-roll" else 0
            if semitones:
                _augment_features(features, semitones, feature_kind, numpy)
                targets["root"] = _transpose_classes(targets["root"], semitones, numpy)
                targets["bass"] = _transpose_classes(targets["bass"], semitones, numpy)
            if joint_root_product:
                targets["joint_root_product"] = _joint_root_product_targets(
                    targets["root"], targets["product"], numpy
                )

            inputs = torch.tensor(features, dtype=torch.float32, device=device)
            tensors = {
                name: torch.tensor(value, dtype=torch.float32 if name == "boundary" else torch.long, device=device)
                for name, value in targets.items()
            }
            sample_weights = (
                torch.tensor(track_weights, dtype=torch.float32, device=device)[:, None]
                * torch.tensor(valid, dtype=torch.float32, device=device)
            )
            normalization_weights = (
                torch.tensor(base_track_weights, dtype=torch.float32, device=device)[:, None]
                * torch.tensor(valid, dtype=torch.float32, device=device)
                if dataset_balance
                else sample_weights
            )
            optimizer.zero_grad(set_to_none=True)
            heads = split_factorized_outputs(
                model(inputs),
                joint_root_product=joint_root_product,
            )

            root_loss = functional.cross_entropy(
                heads["root"].reshape(-1, ROOT_CLASSES), tensors["root"].reshape(-1), reduction="none"
            ).reshape(len(batch), -1)
            mode_loss = functional.cross_entropy(
                heads["mode"].reshape(-1, MODE_CLASSES),
                tensors["mode"].reshape(-1),
                weight=torch.tensor(class_weights["mode"], device=device),
                reduction="none",
            ).reshape(len(batch), -1)
            product_loss = functional.cross_entropy(
                heads["product"].reshape(-1, PRODUCT_CLASSES),
                tensors["product"].reshape(-1),
                weight=(
                    torch.tensor(class_weights["product"], device=device)
                    if product_class_weighting
                    else None
                ),
                reduction="none",
            ).reshape(len(batch), -1)
            structure_loss = functional.cross_entropy(
                heads["structure"].reshape(-1, STRUCTURE_CLASSES),
                tensors["structure"].reshape(-1),
                weight=torch.tensor(class_weights["structure"], device=device),
                reduction="none",
            ).reshape(len(batch), -1)
            quality_targets = tensors["quality"]
            quality_loss = functional.cross_entropy(
                heads["quality"].reshape(-1, QUALITY_CLASSES),
                quality_targets.reshape(-1),
                weight=torch.tensor(class_weights["quality"], device=device),
                ignore_index=-1,
                reduction="none",
            ).reshape(len(batch), -1)
            bass_loss = functional.cross_entropy(
                heads["bass"].reshape(-1, BASS_CLASSES),
                tensors["bass"].reshape(-1),
                weight=torch.tensor(class_weights["bass"], device=device),
                reduction="none",
            ).reshape(len(batch), -1)
            chord_mask = (tensors["root"] != 0).to(torch.float32)
            quality_mask = (quality_targets >= 0).to(torch.float32)
            loss_values = (
                1.0 * root_loss
                + 0.35 * mode_loss
                + 0.8 * product_loss
                + 0.35 * structure_loss
                + 0.9 * quality_loss * quality_mask
                + 0.2 * bass_loss * chord_mask
            )
            if joint_root_product:
                joint_loss = functional.cross_entropy(
                    heads["joint_root_product"].reshape(
                        -1, JOINT_ROOT_PRODUCT_CLASSES
                    ),
                    tensors["joint_root_product"].reshape(-1),
                    weight=(
                        torch.tensor(joint_class_weights, device=device)
                        if joint_class_weights is not None
                        else None
                    ),
                    reduction="none",
                ).reshape(len(batch), -1)
                loss_values = (
                    loss_values
                    + float(joint_root_product_loss_weight) * joint_loss
                )
            loss = (loss_values * sample_weights).sum() / normalization_weights.sum().clamp_min(1)
            boundary_values = functional.binary_cross_entropy_with_logits(
                heads["boundary"].squeeze(-1),
                tensors["boundary"],
                reduction="none",
                pos_weight=torch.tensor(8.0, device=device),
            )
            boundary_weights = sample_weights * torch.cat(
                (torch.zeros_like(sample_weights[:, :1]), (sample_weights[:, :-1] > 0).to(torch.float32)), dim=1
            )
            boundary_normalization_weights = normalization_weights * torch.cat(
                (
                    torch.zeros_like(normalization_weights[:, :1]),
                    (normalization_weights[:, :-1] > 0).to(torch.float32),
                ),
                dim=1,
            )
            boundary_loss = (
                (boundary_values * boundary_weights).sum()
                / boundary_normalization_weights.sum().clamp_min(1)
            )
            loss = loss + 0.35 * boundary_loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            losses.append(float(loss.detach().cpu()))

        model.eval()
        counts = _development_counts(joint_root_product=joint_root_product)
        counts_by_dataset = {
            dataset_id: _development_counts(
                joint_root_product=joint_root_product,
            )
            for dataset_id in development_dataset_ids
        }
        with torch.no_grad():
            for window in windows["development"]:
                heads = split_factorized_outputs(
                    model(
                        torch.tensor(
                            window["features"][None],
                            dtype=torch.float32,
                            device=device,
                        )
                    ),
                    joint_root_product=joint_root_product,
                )
                predicted = {
                    name: value.argmax(dim=-1).cpu().numpy()[0]
                    for name, value in heads.items()
                    if name != "boundary"
                }
                joint_targets = None
                if joint_root_product:
                    roots = predicted["root"]
                    direct_logits = heads["product"][0].cpu().numpy()
                    joint_logits = heads["joint_root_product"][0].cpu().numpy()
                    predicted["joint_conditioned_product"] = (
                        _conditioned_product_predictions(
                            roots,
                            direct_logits,
                            joint_logits,
                            1.0,
                            numpy,
                        )
                    )
                    predicted["selection_product"] = _conditioned_product_predictions(
                        roots,
                        direct_logits,
                        joint_logits,
                        selection_blend,
                        numpy,
                    )
                    joint_targets = _joint_root_product_targets(
                        window["root"],
                        window["product"],
                        numpy,
                    )
                probabilities = torch.sigmoid(heads["boundary"][0, :, 0]).cpu().numpy()
                _accumulate_development_counts(
                    counts,
                    window,
                    predicted,
                    probabilities,
                    joint_targets=joint_targets,
                )
                _accumulate_development_counts(
                    counts_by_dataset[str(window["datasetId"])],
                    window,
                    predicted,
                    probabilities,
                    joint_targets=joint_targets,
                )
        metrics = _development_metrics(counts)
        dataset_metrics = {
            dataset_id: _development_metrics(dataset_counts)
            for dataset_id, dataset_counts in counts_by_dataset.items()
        }
        score, dataset_scores = _aggregate_factorized_selection(
            metrics,
            dataset_metrics,
            dataset_balance=dataset_balance,
            product_metric=(
                "selectionProductAccuracy"
                if joint_root_product
                else "productAccuracy"
            ),
        )
        history.append(
            {
                "epoch": epoch,
                "trainLoss": sum(losses) / max(1, len(losses)),
                "selectionScore": score,
                "selectionAggregation": (
                    "dataset-macro" if dataset_balance else "frame-micro"
                ),
                **(
                    {
                        "selectionProductMetric": "selectionProductAccuracy",
                        "jointRootProductSelectionBlend": selection_blend,
                    }
                    if joint_root_product
                    else {}
                ),
                "developmentByDataset": dataset_metrics,
                "developmentDatasetSelectionScores": dataset_scores,
                **metrics,
            }
        )
        if score > best_score:
            best_score = score
            best_metrics = metrics
            best_dataset_metrics = dataset_metrics
            best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}

    assert best_state is not None
    output_root.mkdir(parents=True, exist_ok=True)
    safetensors = importlib.import_module("safetensors.torch")
    weights_path = output_root / "chord-factorized-v2.safetensors"
    safetensors.save_file(best_state, str(weights_path))
    training_contract = _factorized_training_contract(
        protocol=split_protocol,
        dataset_balance=dataset_balance,
        dataset_statistics=dataset_statistics,
        development_datasets=development_dataset_ids,
        feature_kind=feature_kind,
        feature_count=feature_count,
        sample_rate=sample_rate,
        architecture=architecture,
        augmentation=augmentation,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        seed=seed,
        window_frames=window_frames,
        joint_root_product=joint_root_product,
        joint_root_product_loss_weight=float(joint_root_product_loss_weight),
        product_class_weighting=product_class_weighting,
        joint_root_product_selection_blend=selection_blend,
    )
    training_contract["loss"]["classWeights"] = {
        name: class_weights[name].tolist() for name in sorted(class_weights)
    }
    if joint_class_weights is not None:
        training_contract["loss"]["jointRootProductClassWeights"] = (
            joint_class_weights.tolist()
        )
    output_width = _factorized_output_width(joint_root_product)
    config = {
        "schemaVersion": FACTORIZED_SCHEMA,
        "sampleRate": sample_rate,
        "frameSeconds": STUDENT_FRAME_SECONDS,
        "featureKind": feature_kind,
        "featureCount": feature_count,
        "architecture": architecture,
        "windowFrames": window_frames if architecture == "transformer" else None,
        "vocabulary": {
            "qualities": list(FACTORIZED_QUALITIES),
            "modes": list(FACTORIZED_MODES),
            "products": list(FACTORIZED_PRODUCTS),
            "structures": list(FACTORIZED_STRUCTURES),
            "rootClasses": ROOT_CLASSES,
            "bassClasses": BASS_CLASSES,
        },
        "outputWidth": output_width,
        "seed": seed,
        "epochs": epochs,
        "augmentation": augmentation,
        "datasetBalance": dataset_balance,
        "selectionAggregation": (
            "dataset-macro" if dataset_balance else "frame-micro"
        ),
        "featureSpecSha256": (
            feature_spec.get("featureSpecSha256") if feature_spec is not None else None
        ),
        "featureSpec": dict(feature_spec) if feature_spec is not None else None,
        "bestSelectionScore": best_score,
        "bestDevelopment": best_metrics,
        "bestDevelopmentByDataset": best_dataset_metrics,
        "trainingContract": training_contract,
        "history": history,
        "weights": weights_path.name,
        "weightsSha256": hashlib.sha256(weights_path.read_bytes()).hexdigest(),
    }
    if joint_root_product or product_class_weighting:
        config["optionalHeads"] = {
            "schemaVersion": FACTORIZED_OPTIONAL_HEADS_SCHEMA,
            "jointRootProduct": {
                **_joint_root_product_contract(),
                "enabled": joint_root_product,
            },
        }
        config["productClassWeighting"] = product_class_weighting
        config["jointRootProductLossWeight"] = (
            float(joint_root_product_loss_weight) if joint_root_product else 0.0
        )
        if joint_root_product:
            config["jointRootProductSelectionBlend"] = selection_blend
    (output_root / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def _config_joint_root_product(config: Mapping[str, Any]) -> bool:
    optional = config.get("optionalHeads")
    if optional is None:
        if int(config.get("outputWidth", OUTPUT_WIDTH)) != OUTPUT_WIDTH:
            raise ValueError("A non-legacy output width requires an optional-head contract.")
        return False
    if not isinstance(optional, Mapping) or optional.get("schemaVersion") != FACTORIZED_OPTIONAL_HEADS_SCHEMA:
        raise ValueError("The factorized optional-head contract is invalid.")
    joint = optional.get("jointRootProduct")
    if not isinstance(joint, Mapping) or not isinstance(joint.get("enabled"), bool):
        raise ValueError("The joint root/product head contract is invalid.")
    enabled = bool(joint["enabled"])
    expected = _joint_root_product_contract()
    if enabled and any(joint.get(key) != value for key, value in expected.items()):
        raise ValueError("The joint root/product head contract is incompatible.")
    if int(config.get("outputWidth", -1)) != _factorized_output_width(enabled):
        raise ValueError("The factorized config output width contradicts its head contract.")
    return enabled


def export_factorized_onnx(model_root: Path, output: Path) -> dict[str, Any]:
    """Export the factorized model with enough metadata for local/browser runtimes."""

    torch, _nn, _functional = _torch_modules()
    safetensors = importlib.import_module("safetensors.torch")
    config = json.loads((model_root / "config.json").read_text(encoding="utf-8"))
    if config.get("schemaVersion") != FACTORIZED_SCHEMA:
        raise ValueError("Unsupported factorized model configuration.")
    feature_count = int(config["featureCount"])
    architecture = str(config["architecture"])
    joint_root_product = _config_joint_root_product(config)
    output_width = _factorized_output_width(joint_root_product)
    model = build_factorized_model(
        feature_count,
        architecture,
        joint_root_product=joint_root_product,
    )
    model.load_state_dict(safetensors.load_file(str(model_root / config["weights"])))
    model.eval()
    example = torch.zeros((1, 256, feature_count), dtype=torch.float32)
    output.parent.mkdir(parents=True, exist_ok=True)
    window_frames = 256 if architecture == "transformer" else None
    dynamic_axes = (
        {"features": {0: "batch"}, "outputs": {0: "batch"}}
        if window_frames
        else {"features": {0: "batch", 1: "frames"}, "outputs": {0: "batch", 1: "frames"}}
    )
    torch.onnx.export(
        model,
        example,
        str(output),
        input_names=["features"],
        output_names=["outputs"],
        dynamic_axes=dynamic_axes,
        opset_version=17,
        dynamo=False,
    )
    onnx = importlib.import_module("onnx")
    model_proto = onnx.load(str(output))
    metadata = {
        "chordReaderArchitecture": architecture,
        "chordReaderFeatureKind": str(config["featureKind"]),
        "chordReaderFactorizedSchema": FACTORIZED_SCHEMA,
        "chordReaderFrameSeconds": repr(STUDENT_FRAME_SECONDS),
        "chordReaderOutputWidth": str(output_width),
        "chordReaderQualities": json.dumps(list(FACTORIZED_QUALITIES)),
        "chordReaderModes": json.dumps(list(FACTORIZED_MODES)),
        "chordReaderProducts": json.dumps(list(FACTORIZED_PRODUCTS)),
        "chordReaderStructures": json.dumps(list(FACTORIZED_STRUCTURES)),
        "chordReaderFeatureCount": str(feature_count),
        "chordReaderSampleRate": str(config["sampleRate"]),
    }
    if config.get("featureSpecSha256"):
        metadata["chordReaderFeatureSpecSha256"] = str(config["featureSpecSha256"])
    if joint_root_product:
        metadata["chordReaderJointRootProduct"] = json.dumps(
            _joint_root_product_contract(),
            sort_keys=True,
            separators=(",", ":"),
        )
    if window_frames:
        metadata["chordReaderWindowFrames"] = str(window_frames)
    for key, value in metadata.items():
        entry = model_proto.metadata_props.add()
        entry.key = key
        entry.value = value
    onnx.save(model_proto, str(output))
    runtime = importlib.import_module("onnxruntime")
    session = runtime.InferenceSession(str(output), providers=["CPUExecutionProvider"])
    expected = model(example).detach().numpy()
    actual = session.run(None, {"features": example.numpy()})[0]
    numpy = importlib.import_module("numpy")
    maximum_error = float(numpy.max(numpy.abs(expected - actual)))
    if maximum_error > 1e-4:
        raise ValueError(f"Factorized ONNX parity failed with max error {maximum_error}.")
    report = {
        "schemaVersion": "chord_factorized_onnx_export_v2",
        "modelFile": output.name,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "bytes": output.stat().st_size,
        "opset": 17,
        "maximumAbsoluteError": maximum_error,
        "architecture": architecture,
        "featureKind": config["featureKind"],
        "featureCount": feature_count,
        "sampleRate": int(config["sampleRate"]),
        "frameSeconds": STUDENT_FRAME_SECONDS,
        "featureSpecSha256": config.get("featureSpecSha256"),
        "outputWidth": output_width,
        "windowFrames": window_frames,
    }
    if joint_root_product:
        report["jointRootProduct"] = _joint_root_product_contract()
    return report


def _log_softmax(values: Any, numpy: Any) -> Any:
    maximum = values.max(axis=-1, keepdims=True)
    return values - maximum - numpy.log(numpy.exp(values - maximum).sum(axis=-1, keepdims=True))


def _factorized_mode_path(
    root_logits: Any,
    mode_logits: Any,
    boundary_probabilities: Any,
    numpy: Any,
    *,
    boundary_scale: float = 1.0,
    boundary_bias: float = -1.5,
) -> list[int]:
    """Decode N plus 12 roots by three chord modes as a compact sequence."""

    root = _log_softmax(root_logits, numpy)
    mode = _log_softmax(mode_logits, numpy)
    emissions = [root[:, :1] + mode[:, :1]]
    for mode_index in (MODE_INDEX["major"], MODE_INDEX["minor"], MODE_INDEX["neutral"]):
        for root_index in range(1, ROOT_CLASSES):
            emissions.append(root[:, root_index : root_index + 1] + mode[:, mode_index : mode_index + 1])
    values = numpy.concatenate(emissions, axis=-1)
    state_count = values.shape[-1]
    transition = numpy.full((state_count, state_count), -1.25, dtype=numpy.float32)
    numpy.fill_diagonal(transition, 0)
    transition[0, :] = -0.8
    transition[:, 0] = -0.8
    for left in range(1, state_count):
        for right in range(1, state_count):
            if (left - 1) % 12 == (right - 1) % 12:
                transition[left, right] = -0.5
    scores = values[0]
    backpointers: list[Any] = []
    for frame in range(1, len(values)):
        probability = float(numpy.clip(boundary_probabilities[frame], 0.02, 0.98))
        change_evidence = boundary_scale * (math.log(probability / (1 - probability)) + boundary_bias)
        frame_transition = transition + change_evidence * (1 - numpy.eye(state_count, dtype=numpy.float32))
        candidates = scores[:, None] + frame_transition
        pointers = candidates.argmax(axis=0)
        scores = candidates[pointers, numpy.arange(state_count)] + values[frame]
        backpointers.append(pointers)
    path = [int(scores.argmax())]
    for pointers in reversed(backpointers):
        path.append(int(pointers[path[-1]]))
    return list(reversed(path))


def _state_root_mode(state: int) -> tuple[int, int]:
    if state == 0:
        return 0, MODE_INDEX["none"]
    value = state - 1
    return value % 12 + 1, (MODE_INDEX["major"], MODE_INDEX["minor"], MODE_INDEX["neutral"])[value // 12]


def _independent_path(
    logits: Any,
    boundary_probabilities: Any,
    numpy: Any,
    *,
    change_penalty: float,
    boundary_scale: float,
    boundary_bias: float,
) -> list[int]:
    """Decode one factor without allowing another head to alter it."""

    values = _log_softmax(logits, numpy)
    state_count = int(values.shape[-1])
    transition = numpy.full(
        (state_count, state_count), change_penalty, dtype=numpy.float32
    )
    numpy.fill_diagonal(transition, 0)
    scores = values[0]
    backpointers: list[Any] = []
    identity = numpy.eye(state_count, dtype=numpy.float32)
    for frame in range(1, len(values)):
        probability = float(numpy.clip(boundary_probabilities[frame], 0.02, 0.98))
        evidence = boundary_scale * (
            math.log(probability / (1 - probability)) + boundary_bias
        )
        candidates = scores[:, None] + transition + evidence * (1 - identity)
        pointers = candidates.argmax(axis=0)
        scores = candidates[pointers, numpy.arange(state_count)] + values[frame]
        backpointers.append(pointers)
    path = [int(scores.argmax())]
    for pointers in reversed(backpointers):
        path.append(int(pointers[path[-1]]))
    return list(reversed(path))


def _conditional_product_evidence(
    product_logits: Any,
    joint_root_product_logits: Any | None,
    root: int,
    blend: float,
    numpy: Any,
) -> Any:
    """Blend direct and joint product evidence after ``root`` is immutable."""

    weight = _validated_joint_product_blend(blend)
    direct = numpy.asarray(product_logits)
    if direct.ndim != 2 or direct.shape[-1] != PRODUCT_CLASSES:
        raise ValueError("Direct product logits must have shape (frames, 5).")
    if weight == 0:
        return direct[:, 1:]
    if joint_root_product_logits is None:
        raise ValueError("A nonzero joint product blend requires the optional joint head.")
    if not 1 <= root <= 12:
        raise ValueError("Joint conditional product evidence requires a pitched frozen root.")
    joint = numpy.asarray(joint_root_product_logits)
    if (
        joint.ndim != 2
        or joint.shape[0] != direct.shape[0]
        or joint.shape[-1] != JOINT_ROOT_PRODUCT_CLASSES
    ):
        raise ValueError("Joint root/product logits must have shape (frames, 49).")
    conditional = joint[:, 1:].reshape(len(joint), 4, 12)[:, :, root - 1]
    if weight == 1:
        return conditional
    return (1 - weight) * _log_softmax(direct[:, 1:], numpy) + weight * _log_softmax(
        conditional, numpy
    )


def _conditioned_product_predictions(
    roots: Any,
    product_logits: Any,
    joint_root_product_logits: Any,
    blend: float,
    numpy: Any,
) -> Any:
    """Decode frame products for fixed independent roots during checkpoint selection."""

    root_values = numpy.asarray(roots)
    direct = numpy.asarray(product_logits)
    joint = numpy.asarray(joint_root_product_logits)
    if root_values.ndim != 1:
        raise ValueError("Checkpoint-selection roots must be a one-dimensional array.")
    if direct.shape != (len(root_values), PRODUCT_CLASSES):
        raise ValueError("Checkpoint-selection direct product logits are misaligned.")
    if joint.shape != (len(root_values), JOINT_ROOT_PRODUCT_CLASSES):
        raise ValueError("Checkpoint-selection joint product logits are misaligned.")
    weight = _validated_joint_product_blend(blend)
    products = numpy.zeros(len(root_values), dtype=numpy.int64)
    for root in range(1, ROOT_CLASSES):
        mask = root_values == root
        if not mask.any():
            continue
        evidence = _conditional_product_evidence(
            direct[mask],
            joint[mask],
            root,
            weight,
            numpy,
        )
        products[mask] = evidence.argmax(axis=-1) + 1
    return products


def _hierarchical_product_path(
    root_logits: Any,
    product_logits: Any,
    boundary_probabilities: Any,
    numpy: Any,
    *,
    joint_root_product_logits: Any | None = None,
    joint_product_blend: float = 0.0,
) -> tuple[list[int], list[int]]:
    """Decode roots first, then products, so quality can never move a root."""

    blend = _validated_joint_product_blend(joint_product_blend)
    if blend > 0 and joint_root_product_logits is None:
        raise ValueError("A nonzero joint product blend requires the optional joint head.")
    roots = _independent_path(
        root_logits,
        boundary_probabilities,
        numpy,
        change_penalty=-1.25,
        boundary_scale=1.0,
        boundary_bias=-1.5,
    )
    products = [PRODUCT_INDEX["none"]] * len(roots)
    start = 0
    for frame in range(1, len(roots) + 1):
        if frame < len(roots) and roots[frame] == roots[start]:
            continue
        if roots[start] != 0:
            evidence = _conditional_product_evidence(
                product_logits[start:frame],
                (
                    joint_root_product_logits[start:frame]
                    if joint_root_product_logits is not None
                    else None
                ),
                roots[start],
                blend,
                numpy,
            )
            local = _independent_path(
                evidence,
                boundary_probabilities[start:frame],
                numpy,
                change_penalty=-0.75,
                boundary_scale=0.8,
                boundary_bias=-1.5,
            )
            products[start:frame] = [value + 1 for value in local]
        start = frame
    return roots, products


_FACTORIZED_HEAD_ORDER = (
    "root",
    "mode",
    "product",
    "structure",
    "quality",
    "bass",
    "boundary",
)
_FACTORIZED_CONDITIONAL_QUALITY_HEADS = (
    "mode",
    "product",
    "structure",
    "quality",
)


def _factorized_canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256_and_bytes(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def _factorized_metadata_vocabulary(
    metadata: Mapping[str, str],
    key: str,
    expected: Sequence[str],
) -> tuple[str, ...]:
    try:
        value = json.loads(metadata[key])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Factorized ONNX metadata {key!r} is missing or invalid.") from exc
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"Factorized ONNX metadata {key!r} must be a string list.")
    result = tuple(value)
    if result != tuple(expected):
        raise ValueError(f"Factorized ONNX metadata {key!r} has an incompatible vocabulary.")
    return result


def _factorized_metadata_joint_root_product(
    metadata: Mapping[str, str],
) -> bool:
    raw = metadata.get("chordReaderJointRootProduct")
    if raw is None:
        return False
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("The joint root/product ONNX metadata is invalid.") from exc
    if value != _joint_root_product_contract():
        raise ValueError("The joint root/product ONNX metadata is incompatible.")
    return True


def _factorized_onnx_runtime_contract(recognizer: FactorizedRecognizer) -> dict[str, Any]:
    """Return and validate the evidence contract exposed by one ONNX member."""

    metadata = recognizer.session.get_modelmeta().custom_metadata_map
    if metadata.get("chordReaderFactorizedSchema") != FACTORIZED_SCHEMA:
        raise ValueError("The ONNX member does not expose the supported factorized schema.")
    architecture = metadata.get("chordReaderArchitecture")
    if architecture not in {"tcn", "transformer"}:
        raise ValueError("The ONNX member has an unsupported factorized architecture.")
    try:
        feature_count = int(metadata["chordReaderFeatureCount"])
        sample_rate = int(metadata["chordReaderSampleRate"])
        output_width = int(metadata["chordReaderOutputWidth"])
        frame_seconds = float(
            metadata.get("chordReaderFrameSeconds", repr(STUDENT_FRAME_SECONDS))
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("The ONNX member has invalid numeric feature metadata.") from exc
    feature_kind = metadata.get("chordReaderFeatureKind", "")
    if not feature_kind or feature_count <= 0 or sample_rate <= 0:
        raise ValueError("The ONNX member has an incomplete feature contract.")
    joint_root_product = _factorized_metadata_joint_root_product(metadata)
    expected_output_width = _factorized_output_width(joint_root_product)
    if output_width != expected_output_width:
        raise ValueError(
            f"The ONNX member output width is {output_width}; expected {expected_output_width}."
        )
    if not math.isfinite(frame_seconds) or not math.isclose(
        frame_seconds,
        STUDENT_FRAME_SECONDS,
        rel_tol=0,
        abs_tol=1e-12,
    ):
        raise ValueError("The ONNX member does not use the exact factorized frame grid.")
    known_feature_count = STUDENT_FEATURE_KINDS.get(feature_kind)
    feature_spec_sha256 = metadata.get("chordReaderFeatureSpecSha256") or None
    if known_feature_count is not None:
        if feature_count != known_feature_count or sample_rate != STUDENT_SAMPLE_RATE:
            raise ValueError("The ONNX member browser-feature contract is inconsistent.")
    elif feature_kind == "dasheng_base_v1":
        if not isinstance(feature_spec_sha256, str) or len(feature_spec_sha256) != 64:
            raise ValueError("A Dasheng ONNX member requires its exact feature-spec hash.")
    else:
        raise ValueError(f"Unsupported factorized ONNX feature kind {feature_kind!r}.")

    vocabulary = {
        "qualities": list(
            _factorized_metadata_vocabulary(
                metadata, "chordReaderQualities", FACTORIZED_QUALITIES
            )
        ),
        "modes": list(
            _factorized_metadata_vocabulary(
                metadata, "chordReaderModes", FACTORIZED_MODES
            )
        ),
        "products": list(
            _factorized_metadata_vocabulary(
                metadata, "chordReaderProducts", FACTORIZED_PRODUCTS
            )
        ),
        "structures": list(
            _factorized_metadata_vocabulary(
                metadata, "chordReaderStructures", FACTORIZED_STRUCTURES
            )
        ),
        "rootClasses": ROOT_CLASSES,
        "bassClasses": BASS_CLASSES,
    }
    raw_window_frames = metadata.get("chordReaderWindowFrames")
    try:
        window_frames = int(raw_window_frames) if raw_window_frames else None
    except (TypeError, ValueError) as exc:
        raise ValueError("The ONNX member window contract is invalid.") from exc
    if architecture == "transformer" and window_frames != 256:
        raise ValueError("A transformer ONNX member must expose its exact 256-frame window.")
    if architecture == "tcn" and window_frames is not None:
        raise ValueError("A TCN ONNX member must expose a dynamic frame axis.")

    inputs = recognizer.session.get_inputs()
    outputs = recognizer.session.get_outputs()
    if len(inputs) != 1 or inputs[0].name != "features" or inputs[0].type != "tensor(float)":
        raise ValueError("The ONNX member must have one float input named 'features'.")
    if len(outputs) != 1 or outputs[0].name != "outputs" or outputs[0].type != "tensor(float)":
        raise ValueError("The ONNX member must have one float output named 'outputs'.")
    input_shape = inputs[0].shape
    output_shape = outputs[0].shape
    if len(input_shape) != 3 or input_shape[-1] != feature_count:
        raise ValueError("The ONNX member input shape contradicts its feature contract.")
    if len(output_shape) != 3 or output_shape[-1] != expected_output_width:
        raise ValueError("The ONNX member output shape contradicts its factorized contract.")
    if window_frames is not None and input_shape[1] != window_frames:
        raise ValueError("The ONNX member input shape contradicts its window contract.")

    head_widths = {
        "root": ROOT_CLASSES,
        "mode": MODE_CLASSES,
        "product": PRODUCT_CLASSES,
        "structure": STRUCTURE_CLASSES,
        "quality": QUALITY_CLASSES,
        "bass": BASS_CLASSES,
        "boundary": BOUNDARY_CLASSES,
    }
    if joint_root_product:
        head_widths["joint_root_product"] = JOINT_ROOT_PRODUCT_CLASSES
    contract = {
        "schemaVersion": "chord_factorized_onnx_runtime_contract_v1",
        "architecture": architecture,
        "windowFrames": window_frames,
        "feature": {
            "kind": feature_kind,
            "count": feature_count,
            "sampleRate": sample_rate,
            "frameSeconds": STUDENT_FRAME_SECONDS,
            "featureSpecSha256": feature_spec_sha256,
        },
        "vocabulary": vocabulary,
        "output": {
            "width": expected_output_width,
            "headOrder": list(_factorized_head_order(joint_root_product)),
            "headWidths": head_widths,
        },
    }
    if joint_root_product:
        contract["output"]["jointRootProduct"] = _joint_root_product_contract()
    return contract


def _factorized_ensemble_compatibility_contract(
    member_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Select fields that must match before factor evidence can be combined."""

    return {
        "feature": member_contract["feature"],
        "vocabulary": member_contract["vocabulary"],
        "output": member_contract["output"],
    }


def _factorized_ensemble_decoder_contract(
    *,
    bass_threshold: float,
    joint_root_product: bool = False,
    joint_product_blend: float = 0.0,
) -> dict[str, Any]:
    segmental = SegmentalConfig(bass_threshold=bass_threshold)
    segmental.validate()
    blend = _validated_joint_product_blend(joint_product_blend)
    if blend > 0 and not joint_root_product:
        raise ValueError("A nonzero joint product blend requires the optional joint head.")
    contract = {
        "schemaVersion": FACTORIZED_ENSEMBLE_DECODER_SCHEMA,
        "frameSeconds": STUDENT_FRAME_SECONDS,
        "aggregation": {
            "domain": "pre-decode logits",
            "root": "member-weighted arithmetic mean",
            "conditionalQualityHeads": list(_FACTORIZED_CONDITIONAL_QUALITY_HEADS),
            "conditionalQuality": "independent member-weighted arithmetic mean per head",
            "bass": "member-weighted arithmetic mean",
            "boundary": "member-weighted arithmetic mean before sigmoid",
            "decodedSegments": "never averaged or voted",
        },
        "hierarchicalDecoder": {
            "root": {
                "changePenalty": -1.25,
                "boundaryScale": 1.0,
                "boundaryBias": -1.5,
            },
            "productConditionedOnFixedRoot": {
                "changePenalty": -0.75,
                "boundaryScale": 0.8,
                "boundaryBias": -1.5,
            },
            "detailedQualityEvidence": {
                "structure": 0.25,
                "product": 0.35,
                "mode": 0.2,
            },
            "bassThreshold": bass_threshold,
        },
        "segmentalDecoder": {
            "schemaVersion": SEGMENTAL_SCHEMA,
            "beatGridSchemaVersion": BEAT_GRID_SCHEMA,
            "config": dict(segmental.__dict__),
        },
    }
    if joint_root_product:
        contract["aggregation"]["jointRootProduct"] = (
            "member-weighted arithmetic mean before frozen-root conditioning"
        )
        contract["hierarchicalDecoder"]["productConditionedOnFixedRoot"].update(
            {
                "jointRootProductSchemaVersion": JOINT_ROOT_PRODUCT_SCHEMA,
                "jointConditionalLogProbabilityBlend": blend,
                "rootAuthority": "independent root head is decoded and frozen first",
            }
        )
    return contract


def _factorized_single_decoder_contract(
    *,
    bass_threshold: float,
    joint_product_blend: float,
) -> dict[str, Any]:
    blend = _validated_joint_product_blend(joint_product_blend)
    return {
        "schemaVersion": "chord_factorized_joint_product_decoder_v1",
        "frameSeconds": STUDENT_FRAME_SECONDS,
        "root": {
            "authority": "independent root head",
            "changePenalty": -1.25,
            "boundaryScale": 1.0,
            "boundaryBias": -1.5,
        },
        "productConditionedOnFrozenRoot": {
            "directProductLogProbabilityWeight": 1 - blend,
            "jointConditionalLogProbabilityWeight": blend,
            "jointRootProductSchemaVersion": JOINT_ROOT_PRODUCT_SCHEMA,
            "changePenalty": -0.75,
            "boundaryScale": 0.8,
            "boundaryBias": -1.5,
        },
        "bassThreshold": bass_threshold,
    }


def _normalized_ensemble_weights(
    count: int,
    weights: Sequence[float] | None,
) -> tuple[float, ...]:
    if weights is None:
        return tuple(1.0 / count for _index in range(count))
    try:
        weight_count = len(weights)
    except TypeError as exc:
        raise ValueError(
            "Factorized ensemble weights must be a finite numeric sequence."
        ) from exc
    if isinstance(weights, (str, bytes)) or weight_count != count:
        raise ValueError("Factorized ensemble weights must match the model count.")
    if any(isinstance(value, bool) for value in weights):
        raise ValueError("Factorized ensemble weights must be finite numbers.")
    try:
        values = tuple(float(value) for value in weights)
    except (TypeError, ValueError) as exc:
        raise ValueError("Factorized ensemble weights must be finite numbers.") from exc
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Factorized ensemble weights must be finite and non-negative.")
    total = math.fsum(values)
    if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Factorized ensemble weights must be normalized to sum to one.")
    return tuple(0.0 if value == 0 else value / total for value in values)


def _combine_factorized_member_outputs(
    outputs: Sequence[Any],
    weights: Sequence[float],
    numpy: Any,
    *,
    joint_root_product: bool = False,
) -> Any:
    """Combine factor logits before one decode; never combine decoded segments."""

    if len(outputs) != len(weights) or len(outputs) < 2:
        raise ValueError("Factorized ensemble evidence and weights must have equal length >= 2.")
    arrays = [numpy.asarray(value) for value in outputs]
    expected_shape = arrays[0].shape
    expected_width = _factorized_output_width(joint_root_product)
    for array in arrays:
        if (
            array.ndim != 2
            or array.shape != expected_shape
            or array.shape[-1] != expected_width
        ):
            raise ValueError("Factorized ensemble members returned incompatible output shapes.")
        if array.dtype.kind != "f" or not numpy.isfinite(array).all():
            raise ValueError("Factorized ensemble members must return finite floating-point logits.")
    endpoint = [index for index, weight in enumerate(weights) if weight == 1.0]
    if len(endpoint) == 1 and all(
        weight == 0.0 or index == endpoint[0]
        for index, weight in enumerate(weights)
    ):
        return arrays[endpoint[0]].copy()

    member_heads = [
        split_factorized_outputs(
            array,
            joint_root_product=joint_root_product,
        )
        for array in arrays
    ]
    combined: list[Any] = []
    for name in _factorized_head_order(joint_root_product):
        evidence = numpy.zeros(member_heads[0][name].shape, dtype=numpy.float64)
        for weight, heads in zip(weights, member_heads, strict=True):
            evidence += weight * heads[name].astype(numpy.float64)
        if not numpy.isfinite(evidence).all():
            raise ValueError(f"Factorized ensemble produced invalid {name} evidence.")
        combined.append(evidence.astype(numpy.float32))
    return numpy.concatenate(combined, axis=-1)


class FactorizedRecognizer:
    """Run an exported expanded-vocabulary model and decode timed segments."""

    def __init__(
        self,
        model: Path,
        *,
        bass_threshold: float = 0.65,
        dasheng_snapshot_root: Path | None = None,
        joint_product_blend: float = 0.0,
    ) -> None:
        runtime = importlib.import_module("onnxruntime")
        self.numpy = importlib.import_module("numpy")
        self.session = runtime.InferenceSession(str(model), providers=["CPUExecutionProvider"])
        metadata = self.session.get_modelmeta().custom_metadata_map
        if metadata.get("chordReaderFactorizedSchema") != FACTORIZED_SCHEMA:
            raise ValueError("The ONNX file is not a supported factorized chord model.")
        self.model = model
        self.feature_kind = metadata["chordReaderFeatureKind"]
        self.feature_count = int(metadata["chordReaderFeatureCount"])
        self.sample_rate = int(metadata.get("chordReaderSampleRate", STUDENT_SAMPLE_RATE))
        self.feature_spec_sha256 = metadata.get("chordReaderFeatureSpecSha256")
        self.dasheng_snapshot_root = dasheng_snapshot_root
        self.window_frames = int(metadata["chordReaderWindowFrames"]) if metadata.get("chordReaderWindowFrames") else None
        self.bass_threshold = bass_threshold
        self.vocabulary_labels = factorized_vocabulary_labels()
        self.joint_root_product = _factorized_metadata_joint_root_product(metadata)
        self.output_width = _factorized_output_width(self.joint_root_product)
        if self.joint_root_product:
            _factorized_onnx_runtime_contract(self)
        self.joint_product_blend = _validated_joint_product_blend(
            joint_product_blend
        )
        if self.joint_product_blend > 0 and not self.joint_root_product:
            raise ValueError(
                "A nonzero joint product blend requires a model with the optional joint head."
            )
        if self.joint_root_product:
            self.decoder_contract = _factorized_single_decoder_contract(
                bass_threshold=self.bass_threshold,
                joint_product_blend=self.joint_product_blend,
            )
            self.decoder_contract_sha256 = _factorized_canonical_sha256(
                self.decoder_contract
            )

    def _outputs(self, features: Any) -> Any:
        if not self.window_frames:
            return self.session.run(None, {"features": features[None].astype(self.numpy.float32)})[0][0]
        chunks: list[Any] = []
        for start in range(0, len(features), self.window_frames):
            values = features[start : start + self.window_frames]
            valid = len(values)
            if valid < self.window_frames:
                values = self.numpy.pad(values, ((0, self.window_frames - valid), (0, 0)))
            outputs = self.session.run(None, {"features": values[None].astype(self.numpy.float32)})[0][0]
            chunks.append(outputs[:valid])
        return self.numpy.concatenate(chunks, axis=0)

    def _joint_prediction_metadata(self) -> dict[str, Any]:
        if not bool(getattr(self, "joint_root_product", False)):
            return {}
        contract = getattr(
            self,
            "decoder_contract",
            _factorized_single_decoder_contract(
                bass_threshold=self.bass_threshold,
                joint_product_blend=float(
                    getattr(self, "joint_product_blend", 0.0)
                ),
            ),
        )
        return {
            "jointRootProductHead": _joint_root_product_contract(),
            "jointProductBlend": float(
                getattr(self, "joint_product_blend", 0.0)
            ),
            "decoderContract": json.loads(json.dumps(contract, allow_nan=False)),
            "decoderContractSha256": _factorized_canonical_sha256(contract),
        }

    def _segmental_prediction(
        self,
        heads: Mapping[str, Any],
        duration: float,
        *,
        prediction_id: str,
        beat_grid: Mapping[str, Any],
        validated_beat_grid: BeatGrid,
        reference_boundaries_seconds: Iterable[float],
    ) -> dict[str, Any] | None:
        """Decode a validated rhythm challenger without changing the frozen fallback."""

        root_probabilities = self.numpy.exp(_log_softmax(heads["root"], self.numpy))
        mode_probabilities = self.numpy.exp(_log_softmax(heads["mode"], self.numpy))
        product_log = _log_softmax(heads["product"], self.numpy)
        product_probabilities = self.numpy.exp(product_log)
        quality_probabilities = self.numpy.exp(
            _log_softmax(heads["quality"], self.numpy)
        )
        bass_probabilities = self.numpy.exp(_log_softmax(heads["bass"], self.numpy))
        structure_log = _log_softmax(heads["structure"], self.numpy)
        mode_log = _log_softmax(heads["mode"], self.numpy)
        boundary_probabilities = 1 / (
            1 + self.numpy.exp(-heads["boundary"][:, 0])
        )

        # The segmental state space is intentionally compact (root + mode),
        # but Play Along product changes such as C -> C7 must still be viable.
        # Total-variation changes from every independent factor enrich the
        # boundary evidence without feeding product or quality back into roots.
        factor_boundary = boundary_probabilities.copy()
        for probabilities in (
            root_probabilities,
            mode_probabilities,
            product_probabilities,
            quality_probabilities,
            bass_probabilities,
        ):
            change = 0.5 * self.numpy.abs(
                probabilities[1:] - probabilities[:-1]
            ).sum(axis=1)
            factor_boundary[1:] = self.numpy.maximum(factor_boundary[1:], change)

        # Product evidence conditions detailed-quality evidence only inside a
        # fixed root path. This retains a same-root major/dominant boundary in
        # segmental post-processing while root probabilities remain untouched.
        quality_products = self.numpy.asarray(
            [product_class(f"C:{quality}") for quality in FACTORIZED_QUALITIES],
            dtype=self.numpy.int64,
        )
        segmental_quality = quality_probabilities * product_probabilities[
            :, quality_products
        ]
        segmental_quality /= self.numpy.maximum(
            1e-12, segmental_quality.sum(axis=1, keepdims=True)
        )
        evidence = FactorizedEvidence(
            root=root_probabilities,
            mode=mode_probabilities,
            quality=segmental_quality,
            bass=bass_probabilities,
            boundary=factor_boundary,
        )
        decoded = decode_factorized_segments(
            evidence,
            duration_seconds=duration,
            frame_seconds=STUDENT_FRAME_SECONDS,
            beat_grid=beat_grid,
            fallback_decoder=lambda: None,
            mode_indices=(
                MODE_INDEX["major"],
                MODE_INDEX["minor"],
                MODE_INDEX["neutral"],
            ),
            none_mode_index=MODE_INDEX["none"],
            quality_mode_indices=tuple(
                MODE_INDEX[quality_mode(quality)] for quality in FACTORIZED_QUALITIES
            ),
            config=SegmentalConfig(bass_threshold=self.bass_threshold),
            reference_boundaries_seconds=reference_boundaries_seconds,
        )
        if not isinstance(decoded, Mapping) or decoded.get("schemaVersion") != SEGMENTAL_SCHEMA:
            return None

        segments: list[dict[str, Any]] = []
        for span in decoded["spans"]:
            start = int(span["startFrame"])
            end = int(span["endFrame"])
            root = int(span["root"])
            if root == 0:
                symbol = "N"
                product = PRODUCT_INDEX["none"]
                confidence = float(root_probabilities[start:end, 0].mean())
                detailed_confidence = confidence
                play_along_symbol = "N.C."
            else:
                joint_product_blend = float(
                    getattr(self, "joint_product_blend", 0.0)
                )
                conditional_product = _conditional_product_evidence(
                    heads["product"][start:end],
                    (
                        heads["joint_root_product"][start:end]
                        if "joint_root_product" in heads
                        else None
                    ),
                    root,
                    joint_product_blend,
                    self.numpy,
                )
                product_scores = conditional_product.mean(axis=0)
                product = int(product_scores.argmax()) + 1
                allowed = [
                    index
                    for index, quality in enumerate(FACTORIZED_QUALITIES)
                    if product_class(f"C:{quality}") == product
                ]
                if not allowed:
                    allowed = list(range(QUALITY_CLASSES))
                quality_scores = (
                    heads["quality"][start:end, allowed].mean(axis=0).astype(float)
                )
                for candidate_index, quality_index in enumerate(allowed):
                    structure = STRUCTURE_INDEX[
                        quality_structure(FACTORIZED_QUALITIES[quality_index])
                    ]
                    quality_scores[candidate_index] += 0.25 * float(
                        structure_log[start:end, structure].mean()
                    )
                    candidate_product = product_class(
                        f"C:{FACTORIZED_QUALITIES[quality_index]}"
                    )
                    quality_scores[candidate_index] += 0.35 * float(
                        product_log[start:end, candidate_product].mean()
                    )
                    candidate_mode = MODE_INDEX[
                        quality_mode(FACTORIZED_QUALITIES[quality_index])
                    ]
                    quality_scores[candidate_index] += 0.2 * float(
                        mode_log[start:end, candidate_mode].mean()
                    )
                quality = allowed[int(quality_scores.argmax())]
                bass = int(span["bass"])
                symbol = factorized_symbol(root, quality, bass)
                root_confidence = float(root_probabilities[start:end, root].mean())
                if "joint_root_product" in heads:
                    product_head_confidence = float(
                        self.numpy.exp(
                            _log_softmax(conditional_product, self.numpy)
                        )[:, product - 1].mean()
                    )
                else:
                    product_head_confidence = float(
                        product_probabilities[start:end, product].mean()
                    )
                quality_confidence = float(
                    quality_probabilities[start:end, quality].mean()
                )
                confidence = math.sqrt(
                    max(0.0, root_confidence * product_head_confidence)
                )
                detailed_confidence = math.sqrt(
                    max(0.0, root_confidence * quality_confidence)
                )
                play_along_symbol = product_symbol(root, product)
            label = normalize_chord(symbol)
            segments.append(
                {
                    "start": float(span["startSeconds"]),
                    "end": float(span["endSeconds"]),
                    "label": label.detailed_symbol,
                    "productLabel": play_along_symbol,
                    "confidence": confidence,
                    "productConfidence": confidence,
                    "detailedConfidence": detailed_confidence,
                }
            )

        return {
            "schemaVersion": "chord_prediction_v1",
            "id": prediction_id,
            "engine": "chord-factorized-v9",
            "model": self.model.name,
            "featureKind": self.feature_kind,
            "durationSeconds": duration,
            "sampleRate": self.sample_rate,
            "frameSeconds": STUDENT_FRAME_SECONDS,
            "factorizedVocabulary": True,
            "vocabularySpecification": {
                "schemaVersion": "chord_factorized_vocabulary_v1",
                "qualities": list(FACTORIZED_QUALITIES),
                "supportsInversions": True,
            },
            "bassThreshold": self.bass_threshold,
            "beatAware": True,
            "beatGrid": {
                "schemaVersion": BEAT_GRID_SCHEMA,
                "source": validated_beat_grid.source,
                "confidence": validated_beat_grid.confidence,
                "beatCount": len(validated_beat_grid.beats),
                "meanDownbeatConfidence": validated_beat_grid.mean_downbeat_confidence,
            },
            "segmentalDiagnostics": decoded["diagnostics"],
            "segments": segments,
            **self._joint_prediction_metadata(),
        }

    def predict_features(
        self,
        features: Any,
        duration: float,
        *,
        prediction_id: str,
        beat_grid: Mapping[str, Any] | None = None,
        reference_boundaries_seconds: Iterable[float] = (),
    ) -> dict[str, Any]:
        """Decode frozen features, optionally enabling the rhythm challenger."""

        if getattr(features, "ndim", None) != 2 or int(features.shape[1]) != self.feature_count:
            raise ValueError(
                f"Factorized features must have shape (frames, {self.feature_count})."
            )
        joint_root_product = bool(getattr(self, "joint_root_product", False))
        joint_product_blend = float(getattr(self, "joint_product_blend", 0.0))
        heads = split_factorized_outputs(
            self._outputs(features),
            joint_root_product=joint_root_product,
        )
        validated_beat_grid = (
            usable_beat_grid(beat_grid, duration_seconds=duration)
            if beat_grid is not None
            else None
        )
        if validated_beat_grid is not None and beat_grid is not None:
            segmental = self._segmental_prediction(
                heads,
                duration,
                prediction_id=prediction_id,
                beat_grid=beat_grid,
                validated_beat_grid=validated_beat_grid,
                reference_boundaries_seconds=reference_boundaries_seconds,
            )
            if segmental is not None:
                return segmental
        boundary_probabilities = 1 / (1 + self.numpy.exp(-heads["boundary"][:, 0]))
        roots, products = _hierarchical_product_path(
            heads["root"],
            heads["product"],
            boundary_probabilities,
            self.numpy,
            joint_root_product_logits=heads.get("joint_root_product"),
            joint_product_blend=joint_product_blend,
        )
        root_probabilities = self.numpy.exp(_log_softmax(heads["root"], self.numpy))
        product_log = _log_softmax(heads["product"], self.numpy)
        product_probabilities = self.numpy.exp(product_log)
        quality_probabilities = self.numpy.exp(_log_softmax(heads["quality"], self.numpy))
        bass_probabilities = self.numpy.exp(_log_softmax(heads["bass"], self.numpy))
        structure_log = _log_softmax(heads["structure"], self.numpy)
        mode_log = _log_softmax(heads["mode"], self.numpy)

        segments: list[dict[str, Any]] = []
        start = 0
        for frame in range(1, len(roots) + 1):
            if (
                frame < len(roots)
                and roots[frame] == roots[start]
                and products[frame] == products[start]
            ):
                continue
            root = roots[start]
            product = products[start]
            if root == 0:
                symbol = "N"
                confidence = float(root_probabilities[start:frame, 0].mean())
                detailed_confidence = confidence
                play_along_symbol = "N.C."
            else:
                allowed = [
                    index
                    for index, quality in enumerate(FACTORIZED_QUALITIES)
                    if product_class(f"C:{quality}") == product
                ]
                if not allowed:
                    allowed = list(range(QUALITY_CLASSES))
                quality_scores = heads["quality"][start:frame, allowed].mean(axis=0).astype(float)
                for candidate_index, quality_index in enumerate(allowed):
                    structure = STRUCTURE_INDEX[quality_structure(FACTORIZED_QUALITIES[quality_index])]
                    quality_scores[candidate_index] += 0.25 * float(structure_log[start:frame, structure].mean())
                    candidate_product = product_class(
                        f"C:{FACTORIZED_QUALITIES[quality_index]}"
                    )
                    quality_scores[candidate_index] += 0.35 * float(
                        product_log[start:frame, candidate_product].mean()
                    )
                    candidate_mode = MODE_INDEX[
                        quality_mode(FACTORIZED_QUALITIES[quality_index])
                    ]
                    quality_scores[candidate_index] += 0.2 * float(
                        mode_log[start:frame, candidate_mode].mean()
                    )
                quality = allowed[int(quality_scores.argmax())]
                bass_mean = bass_probabilities[start:frame].mean(axis=0)
                bass = int(bass_mean.argmax())
                if bass == root or bass == 0 or float(bass_mean[bass]) < self.bass_threshold:
                    bass = 0
                symbol = factorized_symbol(root, quality, bass)
                root_confidence = float(root_probabilities[start:frame, root].mean())
                if joint_root_product:
                    conditional_product = _conditional_product_evidence(
                        heads["product"][start:frame],
                        (
                            heads["joint_root_product"][start:frame]
                            if "joint_root_product" in heads
                            else None
                        ),
                        root,
                        joint_product_blend,
                        self.numpy,
                    )
                    product_confidence = float(
                        self.numpy.exp(
                            _log_softmax(conditional_product, self.numpy)
                        )[:, product - 1].mean()
                    )
                else:
                    product_confidence = float(
                        product_probabilities[start:frame, product].mean()
                    )
                quality_confidence = float(quality_probabilities[start:frame, quality].mean())
                confidence = math.sqrt(max(0.0, root_confidence * product_confidence))
                detailed_confidence = math.sqrt(
                    max(0.0, root_confidence * quality_confidence)
                )
                play_along_symbol = product_symbol(root, product)
            end_seconds = duration if frame == len(roots) else min(duration, frame * STUDENT_FRAME_SECONDS)
            start_seconds = 0.0 if start == 0 else min(duration, start * STUDENT_FRAME_SECONDS)
            if end_seconds > start_seconds:
                label = normalize_chord(symbol)
                segments.append(
                    {
                        "start": start_seconds,
                        "end": end_seconds,
                        "label": label.detailed_symbol,
                        "productLabel": play_along_symbol,
                        "confidence": confidence,
                        "productConfidence": confidence,
                        "detailedConfidence": detailed_confidence,
                    }
                )
            start = frame
        return {
            "schemaVersion": "chord_prediction_v1",
            "id": prediction_id,
            "engine": "chord-factorized-v9",
            "model": self.model.name,
            "featureKind": self.feature_kind,
            "durationSeconds": duration,
            "sampleRate": self.sample_rate,
            "frameSeconds": STUDENT_FRAME_SECONDS,
            "factorizedVocabulary": True,
            "vocabularySpecification": {
                "schemaVersion": "chord_factorized_vocabulary_v1",
                "qualities": list(FACTORIZED_QUALITIES),
                "supportsInversions": True,
            },
            "bassThreshold": self.bass_threshold,
            "segments": segments,
            **self._joint_prediction_metadata(),
        }

    def predict(
        self,
        audio: Path,
        *,
        prediction_id: str | None = None,
        beat_grid: Mapping[str, Any] | None = None,
        reference_boundaries_seconds: Iterable[float] = (),
    ) -> dict[str, Any]:
        if self.feature_kind == "dasheng_base_v1":
            if self.dasheng_snapshot_root is None:
                raise ValueError(
                    "Dasheng audio inference requires an explicit verified snapshot root."
                )
            from .dasheng import extract_dasheng_features

            features, duration = extract_dasheng_features(
                audio,
                self.dasheng_snapshot_root,
            )
        else:
            from .student import extract_student_features

            features, duration = extract_student_features(audio, self.feature_kind)
        return self.predict_features(
            features,
            duration,
            prediction_id=prediction_id or audio.name,
            beat_grid=beat_grid,
            reference_boundaries_seconds=reference_boundaries_seconds,
        )


class FactorizedEnsembleRecognizer(FactorizedRecognizer):
    """Average compatible same-feature factor logits before one frozen decode."""

    def __init__(
        self,
        models: Sequence[Path],
        *,
        weights: Sequence[float] | None = None,
        bass_threshold: float = 0.65,
        dasheng_snapshot_root: Path | None = None,
        joint_product_blend: float = 0.0,
    ) -> None:
        try:
            model_count = len(models)
        except TypeError as exc:
            raise ValueError(
                "A factorized ensemble requires a sequence of model paths."
            ) from exc
        if isinstance(models, (str, bytes, Path)) or model_count < 2:
            raise ValueError("A factorized ensemble requires at least two model paths.")
        if (
            isinstance(bass_threshold, bool)
            or not isinstance(bass_threshold, (int, float))
            or not math.isfinite(float(bass_threshold))
            or not 0 <= float(bass_threshold) <= 1
        ):
            raise ValueError("Factorized ensemble bass_threshold must be from zero to one.")
        self.weights = _normalized_ensemble_weights(model_count, weights)
        self.numpy = importlib.import_module("numpy")
        members: list[FactorizedRecognizer] = []
        member_contracts: list[dict[str, Any]] = []
        provenance: list[dict[str, Any]] = []
        for ordinal, raw_path in enumerate(models):
            path = Path(raw_path)
            if not path.is_file():
                raise ValueError(f"Factorized ensemble model is not a file: {path}.")
            before_sha256, before_bytes = _file_sha256_and_bytes(path)
            member = FactorizedRecognizer(
                path,
                bass_threshold=float(bass_threshold),
                dasheng_snapshot_root=dasheng_snapshot_root,
            )
            contract = _factorized_onnx_runtime_contract(member)
            after_sha256, after_bytes = _file_sha256_and_bytes(path)
            if (before_sha256, before_bytes) != (after_sha256, after_bytes):
                raise ValueError("A factorized ensemble model changed while it was loaded.")
            contract_sha256 = _factorized_canonical_sha256(contract)
            members.append(member)
            member_contracts.append(contract)
            provenance.append(
                {
                    "ordinal": ordinal,
                    "fileName": path.name,
                    "sha256": after_sha256,
                    "bytes": after_bytes,
                    "runtimeContractSha256": contract_sha256,
                    "architecture": contract["architecture"],
                    "windowFrames": contract["windowFrames"],
                }
            )

        compatibility = _factorized_ensemble_compatibility_contract(
            member_contracts[0]
        )
        for index, contract in enumerate(member_contracts[1:], start=1):
            candidate = _factorized_ensemble_compatibility_contract(contract)
            if candidate != compatibility:
                raise ValueError(
                    f"Factorized ensemble member {index} has an incompatible feature, "
                    "frame, sample-rate, vocabulary, or output contract."
                )

        self.members = tuple(members)
        self.member_contracts = tuple(member_contracts)
        self.feature_kind = str(compatibility["feature"]["kind"])
        self.feature_count = int(compatibility["feature"]["count"])
        self.sample_rate = int(compatibility["feature"]["sampleRate"])
        self.feature_spec_sha256 = compatibility["feature"]["featureSpecSha256"]
        self.dasheng_snapshot_root = dasheng_snapshot_root
        self.window_frames = None
        self.bass_threshold = float(bass_threshold)
        self.vocabulary_labels = factorized_vocabulary_labels()
        self.output_width = int(compatibility["output"]["width"])
        self.joint_root_product = "joint_root_product" in compatibility["output"][
            "headOrder"
        ]
        self.joint_product_blend = _validated_joint_product_blend(
            joint_product_blend
        )
        if self.joint_product_blend > 0 and not self.joint_root_product:
            raise ValueError(
                "A nonzero joint product blend requires ensemble members with the optional joint head."
            )
        self.decoder_contract = _factorized_ensemble_decoder_contract(
            bass_threshold=self.bass_threshold,
            joint_root_product=self.joint_root_product,
            joint_product_blend=self.joint_product_blend,
        )
        self.decoder_contract_sha256 = _factorized_canonical_sha256(
            self.decoder_contract
        )
        specification = {
            "schemaVersion": FACTORIZED_ENSEMBLE_SCHEMA,
            "members": [
                {
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "runtimeContractSha256": item["runtimeContractSha256"],
                }
                for item in provenance
            ],
            "weights": list(self.weights),
            "compatibilityContractSha256": _factorized_canonical_sha256(
                compatibility
            ),
            "decoderContractSha256": self.decoder_contract_sha256,
        }
        self.ensemble_sha256 = _factorized_canonical_sha256(specification)
        self.ensemble_id = f"factorized-ensemble-{self.ensemble_sha256[:16]}"
        self.model = Path(self.ensemble_id)
        self.model_provenance = {
            "schemaVersion": FACTORIZED_ENSEMBLE_PROVENANCE_SCHEMA,
            "ensembleSha256": self.ensemble_sha256,
            "compatibilityContractSha256": specification[
                "compatibilityContractSha256"
            ],
            "decoderContractSha256": self.decoder_contract_sha256,
            "weights": list(self.weights),
            "members": provenance,
        }

    def _outputs(self, features: Any) -> Any:
        values = self.numpy.asarray(features)
        if (
            values.ndim != 2
            or values.shape[1] != self.feature_count
            or values.shape[0] <= 0
            or values.dtype.kind not in {"f", "i", "u"}
            or not self.numpy.isfinite(values).all()
        ):
            raise ValueError(
                "Factorized ensemble features must be a non-empty finite numeric "
                f"array with shape (frames, {self.feature_count})."
            )
        outputs = [member._outputs(values) for member in self.members]
        if any(output.shape[0] != values.shape[0] for output in outputs):
            raise ValueError(
                "A factorized ensemble member returned a different frame count."
            )
        return _combine_factorized_member_outputs(
            outputs,
            self.weights,
            self.numpy,
            joint_root_product=self.joint_root_product,
        )

    def predict_features(
        self,
        features: Any,
        duration: float,
        *,
        prediction_id: str,
        beat_grid: Mapping[str, Any] | None = None,
        reference_boundaries_seconds: Iterable[float] = (),
    ) -> dict[str, Any]:
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or not math.isfinite(float(duration))
            or float(duration) <= 0
        ):
            raise ValueError("Factorized ensemble duration must be a positive finite number.")
        prediction = super().predict_features(
            features,
            float(duration),
            prediction_id=prediction_id,
            beat_grid=beat_grid,
            reference_boundaries_seconds=reference_boundaries_seconds,
        )
        prediction["engine"] = "chord-factorized-logit-ensemble-v9"
        prediction["model"] = self.ensemble_id
        prediction["modelProvenance"] = json.loads(
            json.dumps(self.model_provenance, allow_nan=False)
        )
        prediction["ensembleDecoderContract"] = json.loads(
            json.dumps(self.decoder_contract, allow_nan=False)
        )
        prediction["ensembleDecoderContractSha256"] = self.decoder_contract_sha256
        return prediction
