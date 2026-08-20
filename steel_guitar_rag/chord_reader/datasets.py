"""Adapters from public chord datasets into the Chord Reader manifest contract."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import statistics
from typing import Any, Iterable

from .labels import normalize_chord
from .manifests import assign_group_splits


def _merge_frames(frames: Iterable[tuple[float, str]], end_seconds: float | None = None) -> list[dict[str, Any]]:
    values = sorted((float(start), normalize_chord(label).detailed_symbol) for start, label in frames)
    if not values:
        return []
    if end_seconds is None:
        intervals = [right[0] - left[0] for left, right in zip(values, values[1:]) if right[0] > left[0]]
        end_seconds = values[-1][0] + (statistics.median(intervals) if intervals else 0.1)
    output: list[dict[str, Any]] = []
    group_start = values[0][0]
    group_label = values[0][1]
    for start, label in values[1:]:
        if label == group_label:
            continue
        if start > group_start:
            output.append({"start": group_start, "end": start, "label": group_label})
        group_start, group_label = start, label
    if end_seconds > group_start:
        output.append({"start": group_start, "end": end_seconds, "label": group_label})
    return output


def _arff_rows(path: Path) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip().lower() == "@data") + 1
    except StopIteration as error:
        raise ValueError(f"No @DATA section in {path}.") from error
    return [row for row in csv.reader(lines[start:], quotechar="'", skipinitialspace=True) if row]


def parse_aam_beatinfo(path: Path, end_seconds: float | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _arff_rows(path)
    frames = [(float(row[0]), row[3]) for row in rows if len(row) >= 4 and row[3].strip()]
    segments = _merge_frames(frames, end_seconds=end_seconds)
    tempo = None
    if len(frames) > 1:
        intervals = [right[0] - left[0] for left, right in zip(frames, frames[1:]) if right[0] > left[0]]
        if intervals:
            tempo = 60 / statistics.median(intervals)
    return segments, {"tempo": tempo, "meter": "4/4"}


def parse_guitarset_jams(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    duration = float(value.get("file_metadata", {}).get("duration") or 0)
    chord_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "chord"]
    if not chord_annotations:
        raise ValueError(f"No chord annotation in {path}.")
    frames: list[tuple[float, str]] = []
    explicit_end = duration
    for item in chord_annotations[0].get("data", []):
        start = float(item["time"])
        item_duration = float(item.get("duration") or 0)
        label = item.get("value")
        if isinstance(label, dict):
            label = label.get("label") or label.get("chord")
        frames.append((start, str(label)))
        explicit_end = max(explicit_end, start + item_duration)
    segments = _merge_frames(frames, end_seconds=explicit_end or None)
    tempo_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "tempo"]
    beat_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "beat_position"]
    key_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "key_mode"]
    sandbox = value.get("sandbox", {})
    tempo = sandbox.get("tempo")
    if tempo_annotations and tempo_annotations[0].get("data"):
        tempo = tempo_annotations[0]["data"][0].get("value")
    meter = sandbox.get("time_signature")
    if beat_annotations and beat_annotations[0].get("data"):
        beat_value = beat_annotations[0]["data"][0].get("value", {})
        meter = f"{beat_value.get('num_beats')}/{beat_value.get('beat_units')}"
    key = None
    if key_annotations and key_annotations[0].get("data"):
        key = key_annotations[0]["data"][0].get("value")
    return segments, {
        "tempo": tempo,
        "meter": meter,
        "key": key,
        "durationSeconds": explicit_end,
    }


def _audio_index(audio_root: Path) -> dict[str, Path]:
    extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    output: dict[str, Path] = {}
    for path in audio_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        output[path.stem] = path.resolve()
        if path.stem.endswith("_mix"):
            output[path.stem.removesuffix("_mix")] = path.resolve()
    return output


def _write_reference(path: Path, identifier: str, segments: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schemaVersion": "chord_reference_v1", "id": identifier, "segments": segments}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def prepare_guitarset(
    annotations_root: Path,
    audio_root: Path,
    output_root: Path,
    *,
    seed: str = "chord-reader-v3-split-1",
    max_tracks: int | None = None,
) -> dict[str, Any]:
    audio = _audio_index(audio_root)
    tracks: list[dict[str, Any]] = []
    for annotation in sorted(annotations_root.rglob("*.jams")):
        if max_tracks is not None and len(tracks) >= max_tracks:
            break
        audio_path = audio.get(annotation.stem)
        if audio_path is None:
            continue
        segments, metadata = parse_guitarset_jams(annotation)
        identifier = f"guitarset-{annotation.stem}"
        reference = output_root / "references" / f"{identifier}.json"
        _write_reference(reference, identifier, segments)
        player = annotation.stem.split("_")[0]
        composition = re.sub(r"_(?:comp|solo)$", "", re.sub(r"^\d+_", "", annotation.stem))
        tracks.append(
            {
                "id": identifier,
                "datasetId": "guitarset",
                "groupId": player,
                "compositionId": composition,
                "audioPath": str(audio_path),
                "referencePath": str(reference.resolve()),
                "labelSource": "ground_truth",
                "trainingWeight": 1.0,
                "durationSeconds": metadata["durationSeconds"],
                "tempo": metadata.get("tempo"),
                "meter": metadata.get("meter"),
                "key": metadata.get("key"),
            }
        )
    frozen = assign_group_splits(tracks, seed=seed)
    for track in frozen:
        if track["split"] == "test":
            track["trainingWeight"] = 0.0
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": frozen}


def prepare_aam(
    annotations_root: Path,
    audio_root: Path,
    output_root: Path,
    *,
    seed: str = "chord-reader-v3-split-1",
    max_tracks: int | None = None,
) -> dict[str, Any]:
    audio = _audio_index(audio_root)
    tracks: list[dict[str, Any]] = []
    for annotation in sorted(annotations_root.glob("*_beatinfo.arff")):
        if max_tracks is not None and len(tracks) >= max_tracks:
            break
        source_id = annotation.name.split("_", 1)[0]
        candidates = [audio.get(source_id), audio.get(f"{source_id}_mix"), audio.get(f"{source_id}-mix")]
        audio_path = next((item for item in candidates if item is not None), None)
        if audio_path is None:
            continue
        segments, metadata = parse_aam_beatinfo(annotation)
        identifier = f"aam-{source_id}"
        reference = output_root / "references" / f"{identifier}.json"
        _write_reference(reference, identifier, segments)
        tracks.append(
            {
                "id": identifier,
                "datasetId": "aam",
                "groupId": source_id,
                "compositionId": source_id,
                "audioPath": str(audio_path),
                "referencePath": str(reference.resolve()),
                "labelSource": "synthetic_ground_truth",
                "trainingWeight": 1.0,
                "tempo": metadata["tempo"],
                "meter": metadata["meter"],
            }
        )
    frozen = assign_group_splits(tracks, seed=seed)
    for track in frozen:
        if track["split"] == "test":
            track["trainingWeight"] = 0.0
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": frozen}
