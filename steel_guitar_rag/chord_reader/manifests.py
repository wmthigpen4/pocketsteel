"""Dataset catalog, immutable split, and weak-label admission contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Iterable, Mapping


CATALOG_SCHEMA = "chord_dataset_catalog_v1"
TRACK_MANIFEST_SCHEMA = "chord_track_manifest_v1"
VALID_SPLITS = {"train", "development", "test", "steel_test"}
VALID_LABEL_SOURCES = {"ground_truth", "synthetic_ground_truth", "weak_chart_alignment"}


@dataclass(frozen=True)
class WeakLabelDiagnostics:
    complete_coverage: bool
    monotonic_alignment: bool
    boundary_within_half_beat_fraction: float
    dual_reader_duration_agreement: float


def admit_weak_label(diagnostics: WeakLabelDiagnostics) -> dict[str, Any]:
    reasons: list[str] = []
    if not diagnostics.complete_coverage:
        reasons.append("reference chart does not cover the complete evaluated audio")
    if not diagnostics.monotonic_alignment:
        reasons.append("reference-to-audio alignment is not monotonic")
    if diagnostics.boundary_within_half_beat_fraction < 0.9:
        reasons.append("fewer than 90% of chart boundaries align within half a detected beat")
    if diagnostics.dual_reader_duration_agreement < 0.8:
        reasons.append("independent readers agree with the chart for less than 80% of labeled duration")
    return {
        "admitted": not reasons,
        "trainingWeight": 0.35 if not reasons else 0.0,
        "reasons": reasons,
        "diagnostics": asdict(diagnostics),
    }


def validate_catalog(catalog: Mapping[str, Any]) -> Mapping[str, Any]:
    if catalog.get("schemaVersion") != CATALOG_SCHEMA:
        raise ValueError(f"Catalog must use {CATALOG_SCHEMA}.")
    datasets = catalog.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("Catalog must contain at least one dataset.")
    identifiers: set[str] = set()
    for dataset in datasets:
        identifier = str(dataset.get("id", "")).strip()
        if not identifier or identifier in identifiers:
            raise ValueError("Dataset ids must be non-empty and unique.")
        identifiers.add(identifier)
        if not str(dataset.get("sourceUrl", "")).startswith("https://"):
            raise ValueError(f"Dataset {identifier} needs an HTTPS source URL.")
        if dataset.get("downloadMode") not in {"official_archive", "explicit_local_assets"}:
            raise ValueError(f"Dataset {identifier} has an invalid download mode.")
        if not dataset.get("annotationFormat"):
            raise ValueError(f"Dataset {identifier} needs an annotation format.")
    return catalog


def _split_for_key(key: str, seed: str, ratios: tuple[int, int, int]) -> str:
    value = int.from_bytes(hashlib.sha256(f"{seed}:{key}".encode()).digest()[:8], "big") % sum(ratios)
    if value < ratios[0]:
        return "train"
    if value < ratios[0] + ratios[1]:
        return "development"
    return "test"


def assign_group_splits(
    tracks: Iterable[Mapping[str, Any]],
    *,
    seed: str = "chord-reader-v3-split-1",
    ratios: tuple[int, int, int] = (70, 15, 15),
) -> list[dict[str, Any]]:
    if any(value <= 0 for value in ratios):
        raise ValueError("Split ratios must be positive.")
    assignments: dict[str, str] = {}
    output: list[dict[str, Any]] = []
    for track in tracks:
        item = dict(track)
        composition = str(item.get("compositionId") or "").strip()
        group = str(item.get("groupId") or "").strip()
        dataset = str(item.get("datasetId") or "").strip()
        if not dataset or not group:
            raise ValueError("Every track needs datasetId and groupId before splitting.")
        leakage_key = composition or f"{dataset}:{group}"
        split = assignments.setdefault(leakage_key, _split_for_key(leakage_key, seed, ratios))
        item["split"] = split
        item["splitGroup"] = leakage_key
        output.append(item)
    return output


def validate_track_manifest(manifest: Mapping[str, Any], dataset_ids: set[str] | None = None) -> Mapping[str, Any]:
    if manifest.get("schemaVersion") != TRACK_MANIFEST_SCHEMA:
        raise ValueError(f"Track manifest must use {TRACK_MANIFEST_SCHEMA}.")
    tracks = manifest.get("tracks")
    if not isinstance(tracks, list):
        raise ValueError("Track manifest tracks must be a list.")
    identifiers: set[str] = set()
    split_by_group: dict[str, str] = {}
    for track in tracks:
        identifier = str(track.get("id", "")).strip()
        if not identifier or identifier in identifiers:
            raise ValueError("Track ids must be non-empty and unique.")
        identifiers.add(identifier)
        dataset_id = str(track.get("datasetId", "")).strip()
        if dataset_ids is not None and dataset_id not in dataset_ids:
            raise ValueError(f"Track {identifier} references unknown dataset {dataset_id!r}.")
        split = track.get("split")
        if split not in VALID_SPLITS:
            raise ValueError(f"Track {identifier} has invalid split {split!r}.")
        split_group = str(track.get("splitGroup", "")).strip()
        if not split_group:
            raise ValueError(f"Track {identifier} needs a splitGroup.")
        previous = split_by_group.setdefault(split_group, split)
        if previous != split:
            raise ValueError(f"Split leakage: group {split_group!r} appears in {previous!r} and {split!r}.")
        label_source = track.get("labelSource")
        if label_source not in VALID_LABEL_SOURCES:
            raise ValueError(f"Track {identifier} has invalid labelSource {label_source!r}.")
        weight = float(track.get("trainingWeight", 0))
        if label_source == "weak_chart_alignment" and weight > 0.35:
            raise ValueError(f"Weak track {identifier} exceeds the 0.35 training-weight ceiling.")
        if split in {"test", "steel_test"} and weight != 0:
            raise ValueError(f"Held-out track {identifier} must have zero training weight.")
    return manifest
