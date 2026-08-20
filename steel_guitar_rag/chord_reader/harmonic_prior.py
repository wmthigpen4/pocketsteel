"""Train-only transposition-invariant harmonic transition and duration priors.

The builder accepts only a sealed factorized manifest carrying the v9 split
protocol.  It validates the complete signed metadata, re-verifies only the
training projection's cached files, and opens factorized-label sidecars only
for tracks whose derived partition is ``train``.  Development, calibration,
test, and steel-test labels are never learning inputs.

The emitted artifact is portable: model states contain product classes and
relative root motion, never dataset identifiers, absolute pitch names, or
filesystem paths.  Exact source identity remains tamper-evident through hashes
of the source manifest, split protocol, artifact seal, train partition, label
set, and vocabulary.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence
import uuid

from .artifact_integrity import (
    FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA,
    FactorizedArtifactIntegrityError,
    validate_factorized_artifact_manifest,
)
from .split_protocol import (
    FACTORIZED_LABEL_SCHEMA,
    SPLIT_PROTOCOL_SCHEMA,
    validate_split_protocol_manifest,
)


HARMONIC_PRIOR_SCHEMA = "chord_harmonic_prior_v1"
HARMONIC_TRANSITION_SCHEMA = "chord_relative_product_transition_v1"
HARMONIC_DURATION_SCHEMA = "chord_product_duration_histogram_v1"
HARMONIC_PRIOR_BUILDER = "steel_guitar_rag.chord_reader.harmonic_prior"
HARMONIC_PRIOR_BUILDER_VERSION = 1

FACTORIZED_PRODUCTS = ("none", "major", "minor", "dominant", "minor-seventh")
FRAME_SECONDS = 0.1
DEFAULT_SMOOTHING_ALPHA = 0.5
DEFAULT_MAX_DURATION_FRAMES = 160

_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_LABEL_ARRAYS = frozenset(
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
_TOP_LEVEL_FIELDS = frozenset(
    {
        "schemaVersion",
        "builder",
        "products",
        "frameSeconds",
        "smoothingAlpha",
        "maxDurationFrames",
        "provenance",
        "trainingSummary",
        "transitionModel",
        "durationModel",
        "artifactSha256",
    }
)
_PROVENANCE_FIELDS = frozenset(
    {
        "sourceManifestSha256",
        "splitManifestSha256",
        "splitAssignmentSha256",
        "trainPartitionSha256",
        "artifactSetSha256",
        "featureSpecSha256",
        "factorizedVocabularySha256",
        "trainFactorizedLabelSetSha256",
        "trainWeightInputSetSha256",
        "trainFactorizedLabelBytes",
        "trainTrackCount",
        "trainingWeightPolicy",
        "splitProtocolSchemaVersion",
        "artifactIntegritySchemaVersion",
    }
)

TRAINING_WEIGHT_POLICY = (
    "sealed_feature_training_weight_times_trainingWeightOverride_v1"
)


class HarmonicPriorError(ValueError):
    """Base class for harmonic-prior contract failures."""


class HarmonicPriorIntegrityError(HarmonicPriorError):
    """A source or emitted artifact failed integrity validation."""


class HarmonicPriorAccessError(HarmonicPriorError):
    """A caller attempted to read a non-training factorized sidecar."""


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
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior values must be canonical finite JSON."
        ) from exc


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value) <= _SHA256_CHARACTERS
    )


def _strict_int(value: Any, *, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HarmonicPriorIntegrityError(f"{label} must be an integer.")
    result = int(value)
    if minimum is not None and result < minimum:
        raise HarmonicPriorIntegrityError(f"{label} must be at least {minimum}.")
    return result


def _finite_float(
    value: Any,
    *,
    label: str,
    positive: bool = False,
    nonnegative: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HarmonicPriorIntegrityError(f"{label} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise HarmonicPriorIntegrityError(f"{label} must be finite.")
    if positive and result <= 0:
        raise HarmonicPriorIntegrityError(f"{label} must be positive.")
    if nonnegative and result < 0:
        raise HarmonicPriorIntegrityError(f"{label} must be non-negative.")
    return result


def _validated_build_parameters(
    smoothing_alpha: float,
    max_duration_frames: int,
) -> tuple[float, int]:
    alpha = _finite_float(
        smoothing_alpha,
        label="smoothing_alpha",
        positive=True,
    )
    maximum = _strict_int(
        max_duration_frames,
        label="max_duration_frames",
        minimum=1,
    )
    if maximum > 100_000:
        raise HarmonicPriorIntegrityError(
            "max_duration_frames is unreasonably large."
        )
    return alpha, maximum


def _validate_factorized_vocabulary(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    vocabulary = manifest.get("factorizedVocabulary")
    if not isinstance(vocabulary, Mapping):
        raise HarmonicPriorIntegrityError(
            "The factorized vocabulary contract is missing."
        )
    if vocabulary.get("products") != list(FACTORIZED_PRODUCTS):
        raise HarmonicPriorIntegrityError(
            "The factorized product vocabulary or ordering was changed."
        )
    if vocabulary.get("rootClasses") != 13:
        raise HarmonicPriorIntegrityError(
            "The harmonic prior requires the no-chord plus 12-root contract."
        )
    _canonical_json(vocabulary)
    return vocabulary


def _validated_manifest_metadata(manifest: Mapping[str, Any]) -> None:
    try:
        validate_split_protocol_manifest(manifest)
        validate_factorized_artifact_manifest(manifest, verify_files=False)
    except (ValueError, FactorizedArtifactIntegrityError) as exc:
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior input failed sealed split/artifact validation."
        ) from exc
    if manifest.get("schemaVersion") != FACTORIZED_LABEL_SCHEMA:
        raise HarmonicPriorIntegrityError(
            f"Harmonic-prior input must use {FACTORIZED_LABEL_SCHEMA}."
        )
    _validate_factorized_vocabulary(manifest)


def _train_tracks(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    tracks = manifest.get("tracks")
    if not isinstance(tracks, list):
        raise HarmonicPriorIntegrityError("The split manifest has no track list.")
    selected = [track for track in tracks if track.get("split") == "train"]
    if not selected:
        raise HarmonicPriorIntegrityError(
            "The sealed split protocol has no training tracks."
        )
    return sorted(selected, key=lambda track: str(track.get("id", "")))


def _sealed_tracks_by_id(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    integrity = manifest["artifactIntegrity"]
    tracks = integrity["tracks"]
    return {str(track["id"]): track for track in tracks}


def _manifest_provenance(manifest: Mapping[str, Any]) -> dict[str, Any]:
    protocol = manifest["splitProtocol"]
    integrity = manifest["artifactIntegrity"]
    selected = _train_tracks(manifest)
    sealed_by_id = _sealed_tracks_by_id(manifest)
    label_descriptors: list[dict[str, Any]] = []
    weight_input_descriptors: list[dict[str, Any]] = []
    total_bytes = 0
    for track in selected:
        identifier = str(track["id"])
        entry = sealed_by_id.get(identifier)
        if entry is None:
            raise HarmonicPriorIntegrityError(
                f"Training track {identifier!r} is absent from the artifact seal."
            )
        artifact = entry["factorizedLabelArtifact"]
        byte_count = int(artifact["bytes"])
        total_bytes += byte_count
        label_descriptors.append(
            {
                "id": identifier,
                "frames": int(entry["frames"]),
                "sha256": str(artifact["sha256"]),
                "bytes": byte_count,
            }
        )
        feature_artifact = entry["featureArtifact"]
        override = _finite_float(
            track.get("trainingWeightOverride", 1.0),
            label=f"Training track {identifier!r} trainingWeightOverride",
            nonnegative=True,
        )
        weight_input_descriptors.append(
            {
                "id": identifier,
                "featureSha256": str(feature_artifact["sha256"]),
                "featureBytes": int(feature_artifact["bytes"]),
                "trainingWeightOverride": override,
            }
        )
    provenance = {
        "sourceManifestSha256": protocol["sourceManifestSha256"],
        "splitManifestSha256": protocol["outputManifestSha256"],
        "splitAssignmentSha256": protocol["assignmentSha256"],
        "trainPartitionSha256": protocol["partitions"]["train"]["tracksSha256"],
        "artifactSetSha256": integrity["artifactSetSha256"],
        "featureSpecSha256": manifest["featureSpecSha256"],
        "factorizedVocabularySha256": _canonical_sha256(
            manifest["factorizedVocabulary"]
        ),
        "trainFactorizedLabelSetSha256": _canonical_sha256(label_descriptors),
        "trainWeightInputSetSha256": _canonical_sha256(weight_input_descriptors),
        "trainFactorizedLabelBytes": total_bytes,
        "trainTrackCount": len(selected),
        "trainingWeightPolicy": TRAINING_WEIGHT_POLICY,
        "splitProtocolSchemaVersion": protocol["schemaVersion"],
        "artifactIntegritySchemaVersion": integrity["schemaVersion"],
    }
    if set(provenance) != _PROVENANCE_FIELDS or any(
        not _is_sha256(provenance[name])
        for name in (
            "sourceManifestSha256",
            "splitManifestSha256",
            "splitAssignmentSha256",
            "trainPartitionSha256",
            "artifactSetSha256",
            "featureSpecSha256",
            "factorizedVocabularySha256",
            "trainFactorizedLabelSetSha256",
            "trainWeightInputSetSha256",
        )
    ):
        raise HarmonicPriorIntegrityError(
            "The sealed manifest has incomplete harmonic-prior provenance."
        )
    return provenance


def _verify_train_projection(manifest: Mapping[str, Any]) -> None:
    """Rehash files only for the derived training partition."""

    projection = deepcopy(dict(manifest))
    projection["tracks"] = [deepcopy(dict(track)) for track in _train_tracks(manifest)]
    try:
        validate_factorized_artifact_manifest(projection, verify_files=True)
    except (ValueError, FactorizedArtifactIntegrityError) as exc:
        raise HarmonicPriorIntegrityError(
            "Training artifacts changed after the factorized seal was frozen."
        ) from exc


def _read_sealed_train_artifact_bytes(
    track: Mapping[str, Any],
    sealed_entry: Mapping[str, Any],
    *,
    track_path_field: str,
    sealed_path_field: str,
    sealed_artifact_field: str,
    artifact_label: str,
) -> bytes:
    if track.get("split") != "train":
        raise HarmonicPriorAccessError(
            "Harmonic-prior learning may open only train cache artifacts."
        )
    path = Path(str(track.get(track_path_field, "")))
    expected_path = str(sealed_entry.get(sealed_path_field, ""))
    if not path.is_absolute() or str(path) != expected_path:
        raise HarmonicPriorIntegrityError(
            f"Training {artifact_label} path does not match its sealed identity."
        )
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise HarmonicPriorIntegrityError(
            f"A sealed training {artifact_label} cannot be opened."
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise HarmonicPriorIntegrityError(
                f"A training {artifact_label} is not a regular file."
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise HarmonicPriorIntegrityError(
            f"A training {artifact_label} changed while being read."
        )
    payload = b"".join(chunks)
    expected_artifact = sealed_entry[sealed_artifact_field]
    if (
        len(payload) != int(expected_artifact["bytes"])
        or hashlib.sha256(payload).hexdigest() != expected_artifact["sha256"]
    ):
        raise HarmonicPriorIntegrityError(
            f"A training {artifact_label} no longer matches its seal."
        )
    return payload


def _read_sealed_train_label_bytes(
    track: Mapping[str, Any],
    sealed_entry: Mapping[str, Any],
) -> bytes:
    return _read_sealed_train_artifact_bytes(
        track,
        sealed_entry,
        track_path_field="factorizedLabelsPath",
        sealed_path_field="factorizedLabelsPath",
        sealed_artifact_field="factorizedLabelArtifact",
        artifact_label="factorized-label sidecar",
    )


def _load_train_weight(
    track: Mapping[str, Any],
    sealed_entry: Mapping[str, Any],
) -> tuple[float, float, float]:
    """Return cached, override, and effective acoustic-training weights."""

    numpy = __import__("numpy")
    payload = _read_sealed_train_artifact_bytes(
        track,
        sealed_entry,
        track_path_field="path",
        sealed_path_field="featurePath",
        sealed_artifact_field="featureArtifact",
        artifact_label="feature cache",
    )
    try:
        with numpy.load(io.BytesIO(payload), allow_pickle=False) as archive:
            if "training_weight" not in archive.files:
                raise HarmonicPriorIntegrityError(
                    "A training feature cache has no sealed training_weight scalar."
                )
            training_weight = archive["training_weight"]
            if training_weight.shape != () or training_weight.dtype.hasobject:
                raise HarmonicPriorIntegrityError(
                    "A training feature cache has an invalid training_weight scalar."
                )
            cached = _finite_float(
                training_weight.item(),
                label="cached training_weight",
                nonnegative=True,
            )
    except HarmonicPriorIntegrityError:
        raise
    except (OSError, ValueError) as exc:
        raise HarmonicPriorIntegrityError(
            "A sealed training feature cache is unreadable."
        ) from exc
    override = _finite_float(
        track.get("trainingWeightOverride", 1.0),
        label="trainingWeightOverride",
        nonnegative=True,
    )
    effective = cached * override
    if not math.isfinite(effective):
        raise HarmonicPriorIntegrityError(
            "The effective acoustic-training weight is not finite."
        )
    return cached, override, effective


def _load_train_labels(
    track: Mapping[str, Any],
    sealed_entry: Mapping[str, Any],
) -> tuple[Any, Any, Any]:
    numpy = __import__("numpy")
    payload = _read_sealed_train_label_bytes(track, sealed_entry)
    try:
        with numpy.load(io.BytesIO(payload), allow_pickle=False) as archive:
            if frozenset(archive.files) != _LABEL_ARRAYS:
                raise HarmonicPriorIntegrityError(
                    "A training factorized-label sidecar changed its array allowlist."
                )
            root = archive["root"].copy()
            product = archive["product"].copy()
            label_valid = archive["label_valid"].copy()
    except HarmonicPriorIntegrityError:
        raise
    except (OSError, ValueError) as exc:
        raise HarmonicPriorIntegrityError(
            "A sealed training factorized-label sidecar is unreadable."
        ) from exc
    frames = int(sealed_entry["frames"])
    if (
        root.shape != (frames,)
        or product.shape != (frames,)
        or label_valid.shape != (frames,)
        or not numpy.issubdtype(root.dtype, numpy.integer)
        or not numpy.issubdtype(product.dtype, numpy.integer)
        or label_valid.dtype != numpy.bool_
    ):
        raise HarmonicPriorIntegrityError(
            "Training root/product/valid arrays violate the sealed frame contract."
        )
    return root, product, label_valid


def _validated_state(root: Any, product: Any) -> tuple[int, int]:
    root_value = _strict_int(root, label="root")
    product_value = _strict_int(product, label="product")
    if not 0 <= root_value <= 12 or not 0 <= product_value < len(FACTORIZED_PRODUCTS):
        raise HarmonicPriorIntegrityError(
            "A harmonic state is outside the root/product class contract."
        )
    no_chord = root_value == 0 and product_value == 0
    pitched = 1 <= root_value <= 12 and 1 <= product_value <= 4
    if not (no_chord or pitched):
        raise HarmonicPriorIntegrityError(
            "A harmonic state has an incoherent root/product pair."
        )
    return root_value, product_value


def _track_segments(root: Any, product: Any, label_valid: Any) -> list[list[tuple[int, int, int]]]:
    """Return contiguous labelled sequences as root/product/duration runs."""

    sequences: list[list[tuple[int, int, int]]] = []
    sequence: list[tuple[int, int, int]] = []
    current: tuple[int, int] | None = None
    duration = 0

    def finish_segment() -> None:
        nonlocal current, duration
        if current is not None:
            sequence.append((current[0], current[1], duration))
        current = None
        duration = 0

    def finish_sequence() -> None:
        nonlocal sequence
        finish_segment()
        if sequence:
            sequences.append(sequence)
        sequence = []

    for root_item, product_item, valid_item in zip(
        root.tolist(),
        product.tolist(),
        label_valid.tolist(),
    ):
        if not bool(valid_item):
            finish_sequence()
            continue
        state = _validated_state(root_item, product_item)
        if current == state:
            duration += 1
            continue
        finish_segment()
        current = state
        duration = 1
    finish_sequence()
    return sequences


def _transition_outcomes(previous_product: int) -> list[dict[str, Any]]:
    if previous_product == 0:
        return [
            {"rootRelation": "no-chord", "nextProduct": 0},
            *(
                {"rootRelation": "entry", "nextProduct": product}
                for product in range(1, len(FACTORIZED_PRODUCTS))
            ),
        ]
    return [
        {"rootRelation": "no-chord", "nextProduct": 0},
        *(
            {"rootRelation": delta, "nextProduct": product}
            for delta in range(12)
            for product in range(1, len(FACTORIZED_PRODUCTS))
        ),
    ]


def _transition_key(
    previous_root: int,
    previous_product: int,
    next_root: int,
    next_product: int,
) -> tuple[str | int, int]:
    if next_product == 0:
        return "no-chord", 0
    if previous_product == 0:
        return "entry", next_product
    return (next_root - previous_root) % 12, next_product


def _build_transition_model(
    counts: Mapping[tuple[int, str | int, int], int],
    weights: Mapping[tuple[int, str | int, int], float],
    *,
    alpha: float,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for previous_product in range(len(FACTORIZED_PRODUCTS)):
        descriptors = _transition_outcomes(previous_product)
        observed = sum(
            int(counts.get((previous_product, item["rootRelation"], item["nextProduct"]), 0))
            for item in descriptors
        )
        observed_weight = math.fsum(
            float(
                weights.get(
                    (
                        previous_product,
                        item["rootRelation"],
                        item["nextProduct"],
                    ),
                    0.0,
                )
            )
            for item in descriptors
        )
        denominator = observed_weight + alpha * len(descriptors)
        outcomes = []
        for descriptor in descriptors:
            count = int(
                counts.get(
                    (
                        previous_product,
                        descriptor["rootRelation"],
                        descriptor["nextProduct"],
                    ),
                    0,
                )
            )
            weight = float(
                weights.get(
                    (
                        previous_product,
                        descriptor["rootRelation"],
                        descriptor["nextProduct"],
                    ),
                    0.0,
                )
            )
            outcomes.append(
                {
                    **descriptor,
                    "count": count,
                    "weight": weight,
                    "logProbability": math.log((weight + alpha) / denominator),
                }
            )
        rows.append(
            {
                "previousProduct": previous_product,
                "observedTransitionCount": observed,
                "observedTransitionWeight": observed_weight,
                "outcomes": outcomes,
            }
        )
    return {
        "schemaVersion": HARMONIC_TRANSITION_SCHEMA,
        "conditioning": "previousProduct",
        "pitchedRootRelation": "(nextRoot-previousRoot) modulo 12",
        "noChordRootRelation": "no-chord",
        "noChordEntryRootRelation": "entry",
        "rows": rows,
    }


def _build_duration_model(
    durations: Mapping[int, Sequence[tuple[int, float]]],
    *,
    alpha: float,
    max_duration_frames: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    bins = max_duration_frames + 1
    for product in range(len(FACTORIZED_PRODUCTS)):
        observations = [
            (int(value), float(weight))
            for value, weight in durations.get(product, ())
        ]
        values = [value for value, _weight in observations]
        histogram = [0] * bins
        histogram_weight_values: list[list[float]] = [[] for _index in range(bins)]
        for value, weight in observations:
            index = min(value, max_duration_frames + 1) - 1
            histogram[index] += 1
            histogram_weight_values[index].append(weight)
        histogram_weights = [math.fsum(bucket) for bucket in histogram_weight_values]
        count = len(values)
        total = sum(values)
        sum_squares = sum(value * value for value in values)
        mean = total / count if count else 0.0
        variance = max(0.0, sum_squares / count - mean * mean) if count else 0.0
        segment_weight = math.fsum(weight for _value, weight in observations)
        weighted_total = math.fsum(value * weight for value, weight in observations)
        weighted_sum_squares = math.fsum(
            value * value * weight for value, weight in observations
        )
        weighted_mean = weighted_total / segment_weight if segment_weight else 0.0
        weighted_variance = (
            max(
                0.0,
                weighted_sum_squares / segment_weight
                - weighted_mean * weighted_mean,
            )
            if segment_weight
            else 0.0
        )
        denominator = segment_weight + alpha * bins
        rows.append(
            {
                "product": product,
                "segmentCount": count,
                "segmentWeight": segment_weight,
                "totalFrames": total,
                "sumSquaresFrames": sum_squares,
                "weightedTotalFrames": weighted_total,
                "weightedSumSquaresFrames": weighted_sum_squares,
                "minimumFrames": min(values) if values else None,
                "maximumFrames": max(values) if values else None,
                "meanFrames": mean,
                "populationVarianceFrames": variance,
                "weightedMeanFrames": weighted_mean,
                "weightedPopulationVarianceFrames": weighted_variance,
                "histogramCounts": histogram,
                "histogramWeights": histogram_weights,
                "logProbabilities": [
                    math.log((bin_weight + alpha) / denominator)
                    for bin_weight in histogram_weights
                ],
            }
        )
    return {
        "schemaVersion": HARMONIC_DURATION_SCHEMA,
        "unit": "frames",
        "frameSeconds": FRAME_SECONDS,
        "exactBinMaximumFrames": max_duration_frames,
        "overflowBinMinimumFrames": max_duration_frames + 1,
        "rows": rows,
    }


def _unsigned_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(artifact))
    value.pop("artifactSha256", None)
    return value


def build_harmonic_prior(
    split_manifest: Mapping[str, Any],
    *,
    smoothing_alpha: float = DEFAULT_SMOOTHING_ALPHA,
    max_duration_frames: int = DEFAULT_MAX_DURATION_FRAMES,
) -> dict[str, Any]:
    """Build a canonical prior from the sealed train partition only."""

    alpha, maximum = _validated_build_parameters(
        smoothing_alpha,
        max_duration_frames,
    )
    _validated_manifest_metadata(split_manifest)
    _verify_train_projection(split_manifest)
    selected = _train_tracks(split_manifest)
    sealed_by_id = _sealed_tracks_by_id(split_manifest)

    transition_counts: dict[tuple[int, str | int, int], int] = {}
    transition_weight_values: dict[tuple[int, str | int, int], list[float]] = {}
    durations: dict[int, list[tuple[int, float]]] = {
        product: [] for product in range(len(FACTORIZED_PRODUCTS))
    }
    frame_count = 0
    valid_frame_count = 0
    segment_count = 0
    transition_count = 0
    cached_track_weights: list[float] = []
    effective_track_weights: list[float] = []
    weighted_frame_values: list[float] = []
    weighted_invalid_frame_values: list[float] = []
    positive_weight_track_count = 0
    zero_weight_track_count = 0
    overridden_track_count = 0
    for track in selected:
        identifier = str(track["id"])
        entry = sealed_by_id[identifier]
        cached_weight, override, effective_weight = _load_train_weight(track, entry)
        root, product, label_valid = _load_train_labels(track, entry)
        cached_track_weights.append(cached_weight)
        effective_track_weights.append(effective_weight)
        overridden_track_count += int(not math.isclose(override, 1.0, rel_tol=0.0, abs_tol=0.0))
        if effective_weight > 0:
            positive_weight_track_count += 1
        else:
            zero_weight_track_count += 1
        frame_count += len(root)
        track_valid_frames = int(label_valid.sum())
        valid_frame_count += track_valid_frames
        weighted_frame_values.append(len(root) * effective_weight)
        weighted_invalid_frame_values.append(
            (len(root) - track_valid_frames) * effective_weight
        )
        for sequence in _track_segments(root, product, label_valid):
            segment_count += len(sequence)
            for _root, product_value, duration in sequence:
                durations[product_value].append((duration, effective_weight))
            for previous, following in zip(sequence, sequence[1:]):
                previous_root, previous_product, _previous_duration = previous
                next_root, next_product, _next_duration = following
                relation, product_value = _transition_key(
                    previous_root,
                    previous_product,
                    next_root,
                    next_product,
                )
                key = previous_product, relation, product_value
                transition_counts[key] = transition_counts.get(key, 0) + 1
                transition_weight_values.setdefault(key, []).append(effective_weight)
                transition_count += 1
    weighted_segment_mass = math.fsum(
        weight for observations in durations.values() for _duration, weight in observations
    )
    weighted_valid_frame_mass = math.fsum(
        duration * weight
        for observations in durations.values()
        for duration, weight in observations
    )
    weighted_transition_mass = math.fsum(
        weight for values in transition_weight_values.values() for weight in values
    )
    cached_track_weight_sum = math.fsum(cached_track_weights)
    effective_track_weight_sum = math.fsum(effective_track_weights)
    weighted_frame_mass = math.fsum(weighted_frame_values)
    weighted_invalid_frame_mass = math.fsum(weighted_invalid_frame_values)
    if (
        valid_frame_count <= 0
        or segment_count <= 0
        or weighted_valid_frame_mass <= 0
        or weighted_segment_mass <= 0
    ):
        raise HarmonicPriorIntegrityError(
            "The training partition contains no positive-weight harmonic segments."
        )

    transition_weights = {
        key: math.fsum(values) for key, values in transition_weight_values.items()
    }
    transition_model = _build_transition_model(
        transition_counts,
        transition_weights,
        alpha=alpha,
    )
    duration_model = _build_duration_model(
        durations,
        alpha=alpha,
        max_duration_frames=maximum,
    )
    config = {
        "schemaVersion": HARMONIC_PRIOR_SCHEMA,
        "products": list(FACTORIZED_PRODUCTS),
        "frameSeconds": FRAME_SECONDS,
        "smoothingAlpha": alpha,
        "maxDurationFrames": maximum,
        "transitionSchemaVersion": HARMONIC_TRANSITION_SCHEMA,
        "durationSchemaVersion": HARMONIC_DURATION_SCHEMA,
    }
    artifact: dict[str, Any] = {
        "schemaVersion": HARMONIC_PRIOR_SCHEMA,
        "builder": {
            "name": HARMONIC_PRIOR_BUILDER,
            "version": HARMONIC_PRIOR_BUILDER_VERSION,
            "configSha256": _canonical_sha256(config),
        },
        "products": list(FACTORIZED_PRODUCTS),
        "frameSeconds": FRAME_SECONDS,
        "smoothingAlpha": alpha,
        "maxDurationFrames": maximum,
        "provenance": _manifest_provenance(split_manifest),
        "trainingSummary": {
            "trackCount": len(selected),
            "frameCount": frame_count,
            "validFrameCount": valid_frame_count,
            "invalidFrameCount": frame_count - valid_frame_count,
            "segmentCount": segment_count,
            "transitionCount": transition_count,
            "cachedTrackWeightSum": cached_track_weight_sum,
            "effectiveTrackWeightSum": effective_track_weight_sum,
            "positiveWeightTrackCount": positive_weight_track_count,
            "zeroWeightTrackCount": zero_weight_track_count,
            "overriddenTrackCount": overridden_track_count,
            "weightedFrameMass": weighted_frame_mass,
            "weightedValidFrameMass": weighted_valid_frame_mass,
            "weightedInvalidFrameMass": weighted_invalid_frame_mass,
            "weightedSegmentMass": weighted_segment_mass,
            "weightedTransitionMass": weighted_transition_mass,
        },
        "transitionModel": transition_model,
        "durationModel": duration_model,
    }
    artifact["artifactSha256"] = _canonical_sha256(artifact)
    validate_harmonic_prior_artifact(
        artifact,
        expected_split_manifest=split_manifest,
    )
    return artifact


def _validate_transition_model(
    value: Any,
    *,
    alpha: float,
) -> tuple[int, float]:
    if not isinstance(value, Mapping) or set(value) != {
        "schemaVersion",
        "conditioning",
        "pitchedRootRelation",
        "noChordRootRelation",
        "noChordEntryRootRelation",
        "rows",
    }:
        raise HarmonicPriorIntegrityError(
            "The transition model has unexpected fields."
        )
    if value.get("schemaVersion") != HARMONIC_TRANSITION_SCHEMA:
        raise HarmonicPriorIntegrityError("Unsupported harmonic transition schema.")
    if (
        value.get("conditioning") != "previousProduct"
        or value.get("pitchedRootRelation")
        != "(nextRoot-previousRoot) modulo 12"
        or value.get("noChordRootRelation") != "no-chord"
        or value.get("noChordEntryRootRelation") != "entry"
    ):
        raise HarmonicPriorIntegrityError(
            "The transposition-invariant transition contract was changed."
        )
    rows = value.get("rows")
    if not isinstance(rows, list) or len(rows) != len(FACTORIZED_PRODUCTS):
        raise HarmonicPriorIntegrityError("The transition rows are incomplete.")
    total_observed = 0
    total_observed_weight = 0.0
    for previous_product, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {
            "previousProduct",
            "observedTransitionCount",
            "observedTransitionWeight",
            "outcomes",
        }:
            raise HarmonicPriorIntegrityError("A transition row is malformed.")
        if row.get("previousProduct") != previous_product:
            raise HarmonicPriorIntegrityError(
                "Transition rows are not in canonical product order."
            )
        outcomes = row.get("outcomes")
        expected = _transition_outcomes(previous_product)
        if not isinstance(outcomes, list) or len(outcomes) != len(expected):
            raise HarmonicPriorIntegrityError(
                "A transition row has the wrong outcome vocabulary."
            )
        observed = _strict_int(
            row.get("observedTransitionCount"),
            label="observedTransitionCount",
            minimum=0,
        )
        observed_weight = _finite_float(
            row.get("observedTransitionWeight"),
            label="observedTransitionWeight",
            nonnegative=True,
        )
        counts = 0
        weights: list[float] = []
        probabilities: list[float] = []
        denominator = observed_weight + alpha * len(expected)
        for descriptor, outcome in zip(expected, outcomes):
            if not isinstance(outcome, Mapping) or set(outcome) != {
                "rootRelation",
                "nextProduct",
                "count",
                "weight",
                "logProbability",
            }:
                raise HarmonicPriorIntegrityError(
                    "A transition outcome is malformed."
                )
            if (
                outcome.get("rootRelation") != descriptor["rootRelation"]
                or outcome.get("nextProduct") != descriptor["nextProduct"]
            ):
                raise HarmonicPriorIntegrityError(
                    "A transition outcome contains an absolute or reordered state."
                )
            count = _strict_int(
                outcome.get("count"),
                label="transition count",
                minimum=0,
            )
            weight = _finite_float(
                outcome.get("weight"),
                label="transition weight",
                nonnegative=True,
            )
            if count == 0 and weight != 0.0:
                raise HarmonicPriorIntegrityError(
                    "A transition outcome assigns weight to an unobserved event."
                )
            log_probability = _finite_float(
                outcome.get("logProbability"),
                label="transition logProbability",
            )
            expected_log_probability = math.log((weight + alpha) / denominator)
            if not math.isclose(
                log_probability,
                expected_log_probability,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise HarmonicPriorIntegrityError(
                    "A transition log probability does not match its smoothed weight."
                )
            counts += count
            weights.append(weight)
            probabilities.append(math.exp(log_probability))
        if (
            counts != observed
            or not math.isclose(
                math.fsum(weights),
                observed_weight,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or not math.isclose(
                math.fsum(probabilities),
                1.0,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise HarmonicPriorIntegrityError(
                "A transition row is not a normalized smoothed distribution."
            )
        total_observed += observed
        total_observed_weight += observed_weight
    return total_observed, total_observed_weight


def _validate_duration_model(
    value: Any,
    *,
    alpha: float,
    max_duration_frames: int,
) -> tuple[int, int, float, float]:
    if not isinstance(value, Mapping) or set(value) != {
        "schemaVersion",
        "unit",
        "frameSeconds",
        "exactBinMaximumFrames",
        "overflowBinMinimumFrames",
        "rows",
    }:
        raise HarmonicPriorIntegrityError("The duration model has unexpected fields.")
    if (
        value.get("schemaVersion") != HARMONIC_DURATION_SCHEMA
        or value.get("unit") != "frames"
        or value.get("frameSeconds") != FRAME_SECONDS
        or value.get("exactBinMaximumFrames") != max_duration_frames
        or value.get("overflowBinMinimumFrames") != max_duration_frames + 1
    ):
        raise HarmonicPriorIntegrityError("The duration-bin contract was changed.")
    rows = value.get("rows")
    if not isinstance(rows, list) or len(rows) != len(FACTORIZED_PRODUCTS):
        raise HarmonicPriorIntegrityError("The duration rows are incomplete.")
    total_segments = 0
    total_frames = 0
    total_segment_weight = 0.0
    total_weighted_frames = 0.0
    bins = max_duration_frames + 1
    for product, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {
            "product",
            "segmentCount",
            "segmentWeight",
            "totalFrames",
            "sumSquaresFrames",
            "weightedTotalFrames",
            "weightedSumSquaresFrames",
            "minimumFrames",
            "maximumFrames",
            "meanFrames",
            "populationVarianceFrames",
            "weightedMeanFrames",
            "weightedPopulationVarianceFrames",
            "histogramCounts",
            "histogramWeights",
            "logProbabilities",
        }:
            raise HarmonicPriorIntegrityError("A duration row is malformed.")
        if row.get("product") != product:
            raise HarmonicPriorIntegrityError(
                "Duration rows are not in canonical product order."
            )
        segment_count = _strict_int(
            row.get("segmentCount"),
            label="duration segmentCount",
            minimum=0,
        )
        segment_weight = _finite_float(
            row.get("segmentWeight"),
            label="duration segmentWeight",
            nonnegative=True,
        )
        frames = _strict_int(
            row.get("totalFrames"),
            label="duration totalFrames",
            minimum=0,
        )
        sum_squares = _strict_int(
            row.get("sumSquaresFrames"),
            label="duration sumSquaresFrames",
            minimum=0,
        )
        weighted_frames = _finite_float(
            row.get("weightedTotalFrames"),
            label="duration weightedTotalFrames",
            nonnegative=True,
        )
        weighted_sum_squares = _finite_float(
            row.get("weightedSumSquaresFrames"),
            label="duration weightedSumSquaresFrames",
            nonnegative=True,
        )
        minimum = row.get("minimumFrames")
        maximum = row.get("maximumFrames")
        if segment_count == 0:
            if (
                minimum is not None
                or maximum is not None
                or frames
                or sum_squares
                or segment_weight
                or weighted_frames
                or weighted_sum_squares
            ):
                raise HarmonicPriorIntegrityError(
                    "An empty duration row has non-empty statistics."
                )
        else:
            minimum = _strict_int(minimum, label="minimumFrames", minimum=1)
            maximum = _strict_int(maximum, label="maximumFrames", minimum=minimum)
            if frames < segment_count * minimum or frames > segment_count * maximum:
                raise HarmonicPriorIntegrityError(
                    "Duration extrema do not bound the recorded total."
                )
            if segment_weight > 0 and (
                weighted_frames < segment_weight
                or weighted_sum_squares < weighted_frames
            ):
                raise HarmonicPriorIntegrityError(
                    "Weighted duration statistics violate positive frame bounds."
                )
        mean = _finite_float(
            row.get("meanFrames"),
            label="duration meanFrames",
            nonnegative=True,
        )
        variance = _finite_float(
            row.get("populationVarianceFrames"),
            label="duration populationVarianceFrames",
            nonnegative=True,
        )
        weighted_mean = _finite_float(
            row.get("weightedMeanFrames"),
            label="duration weightedMeanFrames",
            nonnegative=True,
        )
        weighted_variance = _finite_float(
            row.get("weightedPopulationVarianceFrames"),
            label="duration weightedPopulationVarianceFrames",
            nonnegative=True,
        )
        expected_mean = frames / segment_count if segment_count else 0.0
        expected_variance = (
            max(0.0, sum_squares / segment_count - expected_mean * expected_mean)
            if segment_count
            else 0.0
        )
        expected_weighted_mean = (
            weighted_frames / segment_weight if segment_weight else 0.0
        )
        expected_weighted_variance = (
            max(
                0.0,
                weighted_sum_squares / segment_weight
                - expected_weighted_mean * expected_weighted_mean,
            )
            if segment_weight
            else 0.0
        )
        if (
            not math.isclose(mean, expected_mean, rel_tol=0.0, abs_tol=1e-12)
            or not math.isclose(
                variance,
                expected_variance,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or not math.isclose(
                weighted_mean,
                expected_weighted_mean,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or not math.isclose(
                weighted_variance,
                expected_weighted_variance,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise HarmonicPriorIntegrityError(
                "Duration moments do not match their raw and weighted sufficient statistics."
            )
        histogram = row.get("histogramCounts")
        histogram_weights = row.get("histogramWeights")
        log_probabilities = row.get("logProbabilities")
        if (
            not isinstance(histogram, list)
            or not isinstance(histogram_weights, list)
            or not isinstance(log_probabilities, list)
            or len(histogram) != bins
            or len(histogram_weights) != bins
            or len(log_probabilities) != bins
        ):
            raise HarmonicPriorIntegrityError(
                "A duration row has the wrong histogram shape."
            )
        counts = [
            _strict_int(item, label="duration histogram count", minimum=0)
            for item in histogram
        ]
        weights = [
            _finite_float(
                item,
                label="duration histogram weight",
                nonnegative=True,
            )
            for item in histogram_weights
        ]
        if any(count == 0 and weight != 0.0 for count, weight in zip(counts, weights)):
            raise HarmonicPriorIntegrityError(
                "A duration histogram assigns weight to an unobserved bin."
            )
        if sum(counts) != segment_count:
            raise HarmonicPriorIntegrityError(
                "Duration histogram counts do not match segmentCount."
            )
        if not math.isclose(
            math.fsum(weights),
            segment_weight,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise HarmonicPriorIntegrityError(
                "Duration histogram weights do not match segmentWeight."
            )
        denominator = segment_weight + alpha * bins
        probabilities: list[float] = []
        for weight, log_value in zip(weights, log_probabilities):
            probability = _finite_float(
                log_value,
                label="duration logProbability",
            )
            expected_probability = math.log((weight + alpha) / denominator)
            if not math.isclose(
                probability,
                expected_probability,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise HarmonicPriorIntegrityError(
                    "A duration log probability does not match its smoothed weight."
                )
            probabilities.append(math.exp(probability))
        if not math.isclose(
            math.fsum(probabilities),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise HarmonicPriorIntegrityError(
                "A duration row is not a normalized smoothed distribution."
            )
        total_segments += segment_count
        total_frames += frames
        total_segment_weight += segment_weight
        total_weighted_frames += weighted_frames
    return (
        total_segments,
        total_frames,
        total_segment_weight,
        total_weighted_frames,
    )


def validate_harmonic_prior_artifact(
    artifact: Mapping[str, Any],
    *,
    expected_split_manifest: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Validate the artifact hash, distributions, and optional source binding."""

    if not isinstance(artifact, Mapping) or set(artifact) != _TOP_LEVEL_FIELDS:
        raise HarmonicPriorIntegrityError(
            "The harmonic-prior artifact has unexpected top-level fields."
        )
    if artifact.get("schemaVersion") != HARMONIC_PRIOR_SCHEMA:
        raise HarmonicPriorIntegrityError("Unsupported harmonic-prior schema.")
    expected_hash = artifact.get("artifactSha256")
    actual_hash = _canonical_sha256(_unsigned_artifact(artifact))
    if not _is_sha256(expected_hash) or expected_hash != actual_hash:
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior artifact hash mismatch."
        )
    if artifact.get("products") != list(FACTORIZED_PRODUCTS):
        raise HarmonicPriorIntegrityError(
            "The harmonic-prior product vocabulary was changed."
        )
    if artifact.get("frameSeconds") != FRAME_SECONDS:
        raise HarmonicPriorIntegrityError(
            "The harmonic prior must retain the exact 0.1-second frame grid."
        )
    alpha, maximum = _validated_build_parameters(
        artifact.get("smoothingAlpha"),
        artifact.get("maxDurationFrames"),
    )
    config = {
        "schemaVersion": HARMONIC_PRIOR_SCHEMA,
        "products": list(FACTORIZED_PRODUCTS),
        "frameSeconds": FRAME_SECONDS,
        "smoothingAlpha": alpha,
        "maxDurationFrames": maximum,
        "transitionSchemaVersion": HARMONIC_TRANSITION_SCHEMA,
        "durationSchemaVersion": HARMONIC_DURATION_SCHEMA,
    }
    builder = artifact.get("builder")
    if not isinstance(builder, Mapping) or set(builder) != {
        "name",
        "version",
        "configSha256",
    }:
        raise HarmonicPriorIntegrityError("The harmonic-prior builder contract is missing.")
    if (
        builder.get("name") != HARMONIC_PRIOR_BUILDER
        or builder.get("version") != HARMONIC_PRIOR_BUILDER_VERSION
        or builder.get("configSha256") != _canonical_sha256(config)
    ):
        raise HarmonicPriorIntegrityError(
            "The harmonic-prior builder/config provenance does not match."
        )
    provenance = artifact.get("provenance")
    if not isinstance(provenance, Mapping) or set(provenance) != _PROVENANCE_FIELDS:
        raise HarmonicPriorIntegrityError("Harmonic-prior provenance is incomplete.")
    for name in (
        "sourceManifestSha256",
        "splitManifestSha256",
        "splitAssignmentSha256",
        "trainPartitionSha256",
        "artifactSetSha256",
        "featureSpecSha256",
        "factorizedVocabularySha256",
        "trainFactorizedLabelSetSha256",
        "trainWeightInputSetSha256",
    ):
        if not _is_sha256(provenance.get(name)):
            raise HarmonicPriorIntegrityError(
                f"Harmonic-prior provenance field {name!r} is not a SHA-256."
            )
    _strict_int(
        provenance.get("trainFactorizedLabelBytes"),
        label="trainFactorizedLabelBytes",
        minimum=1,
    )
    provenance_track_count = _strict_int(
        provenance.get("trainTrackCount"),
        label="trainTrackCount",
        minimum=1,
    )
    if (
        provenance.get("trainingWeightPolicy") != TRAINING_WEIGHT_POLICY
        or provenance.get("splitProtocolSchemaVersion") != SPLIT_PROTOCOL_SCHEMA
        or provenance.get("artifactIntegritySchemaVersion")
        != FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA
    ):
        raise HarmonicPriorIntegrityError(
            "The source protocol/integrity schema provenance was changed."
        )
    total_transitions, total_transition_weight = _validate_transition_model(
        artifact.get("transitionModel"),
        alpha=alpha,
    )
    (
        total_segments,
        total_valid_frames,
        total_segment_weight,
        total_weighted_valid_frames,
    ) = _validate_duration_model(
        artifact.get("durationModel"),
        alpha=alpha,
        max_duration_frames=maximum,
    )
    summary = artifact.get("trainingSummary")
    if not isinstance(summary, Mapping) or set(summary) != {
        "trackCount",
        "frameCount",
        "validFrameCount",
        "invalidFrameCount",
        "segmentCount",
        "transitionCount",
        "cachedTrackWeightSum",
        "effectiveTrackWeightSum",
        "positiveWeightTrackCount",
        "zeroWeightTrackCount",
        "overriddenTrackCount",
        "weightedFrameMass",
        "weightedValidFrameMass",
        "weightedInvalidFrameMass",
        "weightedSegmentMass",
        "weightedTransitionMass",
    }:
        raise HarmonicPriorIntegrityError("The training summary is malformed.")
    summary_counts = {
        name: _strict_int(summary.get(name), label=name, minimum=0)
        for name in (
            "trackCount",
            "frameCount",
            "validFrameCount",
            "invalidFrameCount",
            "segmentCount",
            "transitionCount",
            "positiveWeightTrackCount",
            "zeroWeightTrackCount",
            "overriddenTrackCount",
        )
    }
    summary_weights = {
        name: _finite_float(summary.get(name), label=name, nonnegative=True)
        for name in (
            "cachedTrackWeightSum",
            "effectiveTrackWeightSum",
            "weightedFrameMass",
            "weightedValidFrameMass",
            "weightedInvalidFrameMass",
            "weightedSegmentMass",
            "weightedTransitionMass",
        )
    }
    if (
        summary_counts["trackCount"] != provenance_track_count
        or summary_counts["trackCount"] < 1
        or summary_counts["frameCount"]
        != summary_counts["validFrameCount"] + summary_counts["invalidFrameCount"]
        or summary_counts["validFrameCount"] != total_valid_frames
        or summary_counts["segmentCount"] != total_segments
        or summary_counts["transitionCount"] != total_transitions
        or summary_counts["positiveWeightTrackCount"]
        + summary_counts["zeroWeightTrackCount"]
        != summary_counts["trackCount"]
        or summary_counts["positiveWeightTrackCount"] < 1
        or summary_counts["overriddenTrackCount"] > summary_counts["trackCount"]
        or summary_weights["effectiveTrackWeightSum"] <= 0
        or not math.isclose(
            summary_weights["weightedFrameMass"],
            summary_weights["weightedValidFrameMass"]
            + summary_weights["weightedInvalidFrameMass"],
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        or not math.isclose(
            summary_weights["weightedValidFrameMass"],
            total_weighted_valid_frames,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        or not math.isclose(
            summary_weights["weightedSegmentMass"],
            total_segment_weight,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        or not math.isclose(
            summary_weights["weightedTransitionMass"],
            total_transition_weight,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        or total_segments < 1
    ):
        raise HarmonicPriorIntegrityError(
            "The training summary does not match the learned sufficient statistics."
        )
    if expected_split_manifest is not None:
        _validated_manifest_metadata(expected_split_manifest)
        expected_provenance = _manifest_provenance(expected_split_manifest)
        if dict(provenance) != expected_provenance:
            raise HarmonicPriorIntegrityError(
                "Harmonic-prior provenance does not match the supplied sealed split."
            )
    return artifact


def canonical_harmonic_prior_json(artifact: Mapping[str, Any]) -> str:
    """Return the validated canonical JSON representation without a newline."""

    validate_harmonic_prior_artifact(artifact)
    return _canonical_json(artifact)


def write_harmonic_prior_artifact(
    artifact: Mapping[str, Any],
    output_path: Path,
) -> Path:
    """Atomically emit one validated canonical JSON artifact."""

    payload = (canonical_harmonic_prior_json(artifact) + "\n").encode("utf-8")
    output = Path(output_path)
    parent = output.parent
    if not parent.is_dir() or parent.is_symlink() or output.is_symlink():
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior output requires a real existing parent directory."
        )
    temporary = parent / f".{output.name}.{uuid.uuid4().hex}.tmp"
    descriptor: int | None = None
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o644,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    except OSError as exc:
        raise HarmonicPriorIntegrityError(
            "Could not atomically write the harmonic-prior artifact."
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()
    return output


def load_harmonic_prior_artifact(
    path: Path,
    *,
    expected_split_manifest: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Load canonical JSON and optionally bind it to one sealed split."""

    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior input must be a regular non-symlink file."
        )
    try:
        raw = source.read_text(encoding="utf-8")
        artifact = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior input is not readable canonical JSON."
        ) from exc
    if not isinstance(artifact, Mapping):
        raise HarmonicPriorIntegrityError("Harmonic-prior JSON must contain an object.")
    validate_harmonic_prior_artifact(
        artifact,
        expected_split_manifest=expected_split_manifest,
    )
    if raw != _canonical_json(artifact) + "\n":
        raise HarmonicPriorIntegrityError(
            "Harmonic-prior file bytes are not in canonical form."
        )
    return artifact


def _validated_weight(weight: Any) -> float:
    return _finite_float(weight, label="prior weight", nonnegative=True)


def _transition_outcome_index(
    previous_root: int,
    previous_product: int,
    next_root: int,
    next_product: int,
) -> int:
    if next_product == 0:
        return 0
    if previous_product == 0:
        return next_product
    delta = (next_root - previous_root) % 12
    return 1 + delta * 4 + (next_product - 1)


@dataclass(frozen=True)
class CompiledHarmonicPriorScorer:
    """Immutable, prevalidated constant-time prior lookup tables."""

    artifact_sha256: str
    max_duration_frames: int
    transition_log_probabilities: tuple[tuple[float, ...], ...]
    duration_log_probabilities: tuple[tuple[float, ...], ...]

    def score_transition(
        self,
        *,
        previous_root: int,
        previous_product: int,
        next_root: int,
        next_product: int,
        weight: float = 0.0,
    ) -> float:
        scale = _validated_weight(weight)
        if scale == 0.0:
            return 0.0
        previous_root, previous_product = _validated_state(
            previous_root,
            previous_product,
        )
        next_root, next_product = _validated_state(next_root, next_product)
        index = _transition_outcome_index(
            previous_root,
            previous_product,
            next_root,
            next_product,
        )
        return scale * self.transition_log_probabilities[previous_product][index]

    def score_duration(
        self,
        *,
        root: int,
        product: int,
        duration_frames: int,
        weight: float = 0.0,
    ) -> float:
        scale = _validated_weight(weight)
        if scale == 0.0:
            return 0.0
        _root, product = _validated_state(root, product)
        frames = _strict_int(
            duration_frames,
            label="duration_frames",
            minimum=1,
        )
        index = min(frames, self.max_duration_frames + 1) - 1
        return scale * self.duration_log_probabilities[product][index]

    def score_span(
        self,
        *,
        root: int,
        product: int,
        start_frame: int,
        end_frame: int,
        weight: float = 0.0,
    ) -> float:
        scale = _validated_weight(weight)
        if scale == 0.0:
            return 0.0
        start = _strict_int(start_frame, label="start_frame", minimum=0)
        end = _strict_int(end_frame, label="end_frame", minimum=1)
        if end <= start:
            raise HarmonicPriorIntegrityError(
                "A harmonic candidate span must have positive duration."
            )
        return self.score_duration(
            root=root,
            product=product,
            duration_frames=end - start,
            weight=scale,
        )


def compile_harmonic_prior_scorer(
    artifact: Mapping[str, Any],
    *,
    expected_split_manifest: Mapping[str, Any] | None = None,
) -> CompiledHarmonicPriorScorer:
    """Validate once and copy the decoder hot-path values into immutable tuples."""

    validate_harmonic_prior_artifact(
        artifact,
        expected_split_manifest=expected_split_manifest,
    )
    transition = tuple(
        tuple(float(outcome["logProbability"]) for outcome in row["outcomes"])
        for row in artifact["transitionModel"]["rows"]
    )
    duration = tuple(
        tuple(float(value) for value in row["logProbabilities"])
        for row in artifact["durationModel"]["rows"]
    )
    return CompiledHarmonicPriorScorer(
        artifact_sha256=str(artifact["artifactSha256"]),
        max_duration_frames=int(artifact["maxDurationFrames"]),
        transition_log_probabilities=transition,
        duration_log_probabilities=duration,
    )


def _compiled_scorer(
    source: Mapping[str, Any] | CompiledHarmonicPriorScorer,
) -> CompiledHarmonicPriorScorer:
    if isinstance(source, CompiledHarmonicPriorScorer):
        return source
    raise HarmonicPriorIntegrityError(
        "Non-zero harmonic-prior scoring requires a prevalidated compiled scorer."
    )


def score_harmonic_transition(
    artifact: Mapping[str, Any] | CompiledHarmonicPriorScorer,
    *,
    previous_root: int,
    previous_product: int,
    next_root: int,
    next_product: int,
    weight: float = 0.0,
) -> float:
    """Return ``weight * log P(relative root motion, product | product)``."""

    scale = _validated_weight(weight)
    if scale == 0.0:
        return 0.0
    return _compiled_scorer(artifact).score_transition(
        previous_root=previous_root,
        previous_product=previous_product,
        next_root=next_root,
        next_product=next_product,
        weight=scale,
    )


def score_harmonic_duration(
    artifact: Mapping[str, Any] | CompiledHarmonicPriorScorer,
    *,
    root: int,
    product: int,
    duration_frames: int,
    weight: float = 0.0,
) -> float:
    """Return a weighted product-conditioned span-duration log probability."""

    scale = _validated_weight(weight)
    if scale == 0.0:
        return 0.0
    return _compiled_scorer(artifact).score_duration(
        root=root,
        product=product,
        duration_frames=duration_frames,
        weight=scale,
    )


def score_harmonic_span(
    artifact: Mapping[str, Any] | CompiledHarmonicPriorScorer,
    *,
    root: int,
    product: int,
    start_frame: int,
    end_frame: int,
    weight: float = 0.0,
) -> float:
    """Score one half-open candidate span using its exact frame duration."""

    scale = _validated_weight(weight)
    if scale == 0.0:
        return 0.0
    return _compiled_scorer(artifact).score_span(
        root=root,
        product=product,
        start_frame=start_frame,
        end_frame=end_frame,
        weight=scale,
    )
