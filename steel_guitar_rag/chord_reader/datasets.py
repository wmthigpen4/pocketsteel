"""Adapters from public chord datasets into the Chord Reader manifest contract."""

from __future__ import annotations

import csv
from fractions import Fraction
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import statistics
from typing import Any, Iterable
import wave

from .labels import normalize_chord
from .manifests import assign_group_splits


_TIMING_MANIFEST_KEYS = (
    "beatTimesSeconds",
    "downbeatTimesSeconds",
    "barStartsSeconds",
    "gridStartSeconds",
    "prefixExcludedSeconds",
    "timingProvenance",
)


def _strict_source_times(values: Iterable[float], *, name: str) -> list[float]:
    """Return source timestamps in strict order without rounding or inference."""

    output = sorted(float(value) for value in values)
    if any(not math.isfinite(value) or value < 0 for value in output):
        raise ValueError(f"{name} must contain finite, nonnegative source timestamps.")
    if any(right <= left for left, right in zip(output, output[1:])):
        raise ValueError(f"{name} must contain strictly increasing source timestamps.")
    return output


def _starts_at_zero(values: list[float]) -> bool:
    return bool(values) and math.isclose(values[0], 0.0, rel_tol=0, abs_tol=1e-9)


def _timing_manifest_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    """Copy only certified native timing fields into a prepared track row."""

    return {key: metadata[key] for key in _TIMING_MANIFEST_KEYS if key in metadata}


def _merge_frames(
    frames: Iterable[tuple[float, str]],
    end_seconds: float | None = None,
    *,
    normalize_labels: bool = True,
) -> list[dict[str, Any]]:
    values = sorted(
        (
            float(start),
            normalize_chord(label).detailed_symbol if normalize_labels else str(label).strip(),
        )
        for start, label in frames
    )
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
    data_markers = [index for index, line in enumerate(lines) if line.strip().lower() == "@data"]
    start = data_markers[0] + 1 if data_markers else 0
    data_lines = [
        line
        for line in lines[start:]
        if line.strip() and not line.lstrip().startswith(("@", "%"))
    ]
    rows = [row for row in csv.reader(data_lines, quotechar="'", skipinitialspace=True) if row]
    if not rows:
        raise ValueError(f"No ARFF data rows in {path}.")
    return rows


def parse_aam_beatinfo(path: Path, end_seconds: float | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _arff_rows(path)
    frames = [(float(row[0]), row[3]) for row in rows if len(row) >= 4 and row[3].strip()]
    segments = _merge_frames(frames, end_seconds=end_seconds)
    beat_times = _strict_source_times(
        (float(row[0]) for row in rows if len(row) >= 3),
        name="AAM beatTimesSeconds",
    )
    source_bar_starts = _strict_source_times(
        (
            float(row[0])
            for row in rows
            if len(row) >= 3 and math.isclose(float(row[2]), 1.0, rel_tol=0, abs_tol=1e-9)
        ),
        name="AAM barStartsSeconds",
    )
    tempo = None
    if len(beat_times) > 1:
        intervals = [right - left for left, right in zip(beat_times, beat_times[1:])]
        if intervals:
            tempo = 60 / statistics.median(intervals)
    provenance: dict[str, Any] = {
        "sourceFormat": "aam-beatinfo-arff",
        "beatTimesSeconds": {
            "status": "explicit",
            "sourceField": "column-0-seconds",
        },
        "barStartsSeconds": {
            "status": "explicit" if _starts_at_zero(source_bar_starts) else "uncertifiable",
            "sourceRule": "column-2-quarter-count-equals-1",
        },
    }
    if source_bar_starts and not _starts_at_zero(source_bar_starts):
        provenance["barStartsSeconds"]["reason"] = "first annotated downbeat is not at zero"
    metadata: dict[str, Any] = {
        "tempo": tempo,
        "meter": "4/4",
        "beatTimesSeconds": beat_times,
        "timingProvenance": provenance,
    }
    if _starts_at_zero(source_bar_starts):
        metadata["barStartsSeconds"] = source_bar_starts
    return segments, metadata


def _guitarset_chord_role(
    annotation: dict[str, Any],
    path: Path,
) -> tuple[str | None, str | None]:
    metadata = annotation.get("annotation_metadata") or {}
    sandbox = annotation.get("sandbox") or {}
    explicit: set[str] = set()
    for container in (annotation, metadata, sandbox):
        if not isinstance(container, dict):
            raise ValueError(f"Malformed GuitarSet chord annotation metadata in {path}.")
        for key in ("annotationRole", "annotation_role", "chordRole", "chord_role", "role"):
            if key not in container or container[key] in (None, ""):
                continue
            token = re.sub(r"[^a-z]+", " ", str(container[key]).lower()).strip()
            if token in {"instructed", "instructed chord", "instructed chords", "lead sheet"}:
                explicit.add("instructed")
            elif token in {"performed", "performed chord", "performed chords", "performance"}:
                explicit.add("performed")
            else:
                raise ValueError(f"Unsupported GuitarSet chord annotation role {container[key]!r} in {path}.")
    if len(explicit) > 1:
        raise ValueError(f"Conflicting GuitarSet chord annotation roles in {path}.")

    description = " ".join(
        str(metadata.get(key) or "")
        for key in ("annotation_rules", "data_source", "annotation_tools", "validation")
    ).lower()
    described = None
    if "note transcription" in description or "semi-automatic chord transcription" in description:
        described = "performed"
    elif "instructed chord" in description or "instructed lead sheet" in description:
        described = "instructed"
    if explicit and described and described not in explicit:
        raise ValueError(f"Conflicting GuitarSet chord annotation metadata in {path}.")
    if explicit:
        return next(iter(explicit)), "explicit-annotation-role"
    if described:
        return described, "annotation-metadata-description"
    return None, None


def _guitarset_chord_annotations(
    value: dict[str, Any],
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "chord"]
    if len(annotations) != 2:
        raise ValueError(
            f"GuitarSet requires exactly one instructed and one performed chord annotation in {path}; "
            f"found {len(annotations)}."
        )
    selected: dict[str, dict[str, Any]] = {}
    rules: dict[str, str] = {}
    unmarked: list[dict[str, Any]] = []
    for annotation in annotations:
        role, rule = _guitarset_chord_role(annotation, path)
        if role is None:
            unmarked.append(annotation)
        elif role in selected:
            raise ValueError(f"Multiple GuitarSet {role} chord annotations in {path}.")
        else:
            selected[role] = annotation
            rules[role] = str(rule)
    if set(selected) == {"performed"} and len(unmarked) == 1:
        selected["instructed"] = unmarked.pop()
        rules["instructed"] = "official-unmarked-lead-sheet-counterpart"
    if unmarked or set(selected) != {"instructed", "performed"}:
        raise ValueError(f"Ambiguous or missing GuitarSet chord annotation roles in {path}.")
    return selected["instructed"], selected["performed"], rules


def _guitarset_performance_role(value: dict[str, Any], path: Path) -> str:
    candidates: list[tuple[str, str]] = []
    for source, container in (
        ("file_metadata", value.get("file_metadata") or {}),
        ("sandbox", value.get("sandbox") or {}),
    ):
        if not isinstance(container, dict):
            raise ValueError(f"Malformed GuitarSet {source} in {path}.")
        for key in ("performanceRole", "performance_role"):
            if key in container and container[key] not in (None, ""):
                role = str(container[key]).lower().strip()
                if role not in {"comp", "solo"}:
                    raise ValueError(f"Unsupported GuitarSet performance role {container[key]!r} in {path}.")
                candidates.append((f"{source}.{key}", role))
    for source, identity in (
        ("file_metadata.title", (value.get("file_metadata") or {}).get("title")),
        ("annotation filename", path.stem),
    ):
        match = re.search(r"_(comp|solo)$", str(identity or ""), re.IGNORECASE)
        if match:
            candidates.append((source, match.group(1).lower()))
    if not candidates:
        raise ValueError(f"Missing GuitarSet comp/solo performance identity in {path}.")
    if len({role for _source, role in candidates}) != 1:
        details = ", ".join(f"{source}={role}" for source, role in candidates)
        raise ValueError(f"Conflicting GuitarSet comp/solo performance identity in {path}: {details}.")
    return candidates[0][1]


def _guitarset_chord_segments(
    annotation: dict[str, Any],
    duration: float,
    role: str,
    path: Path,
    *,
    normalize_labels: bool,
) -> tuple[list[dict[str, Any]], float]:
    segments: list[dict[str, Any]] = []
    explicit_end = duration
    for item in annotation.get("data", []):
        if not isinstance(item, dict):
            raise ValueError(f"Malformed GuitarSet {role} chord observation in {path}.")
        try:
            start = float(item["time"])
            item_duration = float(item["duration"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Malformed GuitarSet {role} chord interval in {path}."
            ) from exc
        if (
            not math.isfinite(start)
            or start < 0
            or not math.isfinite(item_duration)
            or item_duration <= 0
        ):
            raise ValueError(
                f"GuitarSet {role} chord intervals must be finite, nonnegative, and nonempty in {path}."
            )
        label = item.get("value")
        if isinstance(label, dict):
            label = label.get("label") or label.get("chord")
        if label in (None, ""):
            raise ValueError(f"Malformed GuitarSet {role} chord label in {path}.")
        end = start + item_duration
        if not math.isfinite(end):
            raise ValueError(f"Malformed GuitarSet {role} chord end in {path}.")
        symbol = (
            normalize_chord(str(label)).detailed_symbol
            if normalize_labels
            else str(label).strip()
        )
        segments.append({"start": start, "end": end, "label": symbol})
        explicit_end = max(explicit_end, end)
    if not segments:
        raise ValueError(f"No GuitarSet {role} chord data in {path}.")
    segments.sort(key=lambda item: (float(item["start"]), float(item["end"])))
    merged: list[dict[str, Any]] = []
    for segment in segments:
        if merged and float(segment["start"]) < float(merged[-1]["end"]):
            raise ValueError(f"Overlapping GuitarSet {role} chord intervals in {path}.")
        if (
            merged
            and segment["label"] == merged[-1]["label"]
            and float(segment["start"]) == float(merged[-1]["end"])
        ):
            merged[-1]["end"] = segment["end"]
        else:
            merged.append(segment)
    return merged, explicit_end


def parse_guitarset_jams(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    duration = float(value.get("file_metadata", {}).get("duration") or 0)
    if not math.isfinite(duration) or duration < 0:
        raise ValueError(f"Malformed GuitarSet file duration in {path}.")
    instructed, performed, chord_rules = _guitarset_chord_annotations(value, path)
    performance_role = _guitarset_performance_role(value, path)
    segments, explicit_end = _guitarset_chord_segments(
        instructed,
        duration,
        "instructed",
        path,
        normalize_labels=True,
    )
    performed_segments, performed_end = _guitarset_chord_segments(
        performed,
        duration,
        "performed",
        path,
        normalize_labels=False,
    )
    tempo_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "tempo"]
    beat_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "beat_position"]
    key_annotations = [item for item in value.get("annotations", []) if item.get("namespace") == "key_mode"]
    sandbox = value.get("sandbox", {})
    tempo = sandbox.get("tempo")
    if tempo_annotations and tempo_annotations[0].get("data"):
        tempo = tempo_annotations[0]["data"][0].get("value")
    meter = sandbox.get("time_signature")
    beat_times: list[float] = []
    downbeat_times: list[float] = []
    if beat_annotations and beat_annotations[0].get("data"):
        beat_data = beat_annotations[0]["data"]
        beat_times = _strict_source_times(
            (float(item["time"]) for item in beat_data),
            name="GuitarSet beatTimesSeconds",
        )
        for item in beat_data:
            beat_value = item.get("value")
            if not isinstance(beat_value, dict):
                raise ValueError(f"Malformed GuitarSet beat_position value in {path}.")
            try:
                position = float(beat_value["position"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Malformed GuitarSet beat position in {path}.") from exc
            if math.isclose(position, 1.0, rel_tol=0, abs_tol=1e-9):
                downbeat_times.append(float(item["time"]))
        downbeat_times = _strict_source_times(
            downbeat_times,
            name="GuitarSet downbeatTimesSeconds",
        )
        beat_value = beat_data[0].get("value", {})
        meter = f"{beat_value.get('num_beats')}/{beat_value.get('beat_units')}"
    key = None
    if key_annotations and key_annotations[0].get("data"):
        key = key_annotations[0]["data"][0].get("value")
    metadata: dict[str, Any] = {
        "tempo": tempo,
        "meter": meter,
        "key": key,
        "durationSeconds": explicit_end,
        "performanceRole": performance_role,
        "performedDurationSeconds": performed_end,
        "performedSegments": performed_segments,
        "chordProvenance": {
            "performanceRole": performance_role,
            "primaryReference": {
                "sourceFormat": "guitarset-jams",
                "sourceNamespace": "chord",
                "annotationRole": "instructed",
                "semanticTarget": "play-along-lead-sheet-harmony",
                "selectionRule": chord_rules["instructed"],
            },
            "performedReference": {
                "sourceFormat": "guitarset-jams",
                "sourceNamespace": "chord",
                "annotationRole": "performed",
                "semanticTarget": "chord-sheet-informed-performed-quality",
                "segmentationSource": "instructed-chord-sheet",
                "rootSource": "instructed-chord-sheet",
                "qualityEvidence": "separate-string-note-transcriptions",
                "labelEncoding": "guitarset-harte",
                "selectionRule": chord_rules["performed"],
            },
        },
        "timingProvenance": {
            "sourceFormat": "guitarset-jams",
            "instructedChordSegmentsSeconds": {
                "status": "explicit",
                "sourceNamespace": "chord",
                "annotationRole": "instructed",
                "sourceFields": ["data.time", "data.duration"],
            },
            "performedChordSegmentsSeconds": {
                "status": "explicit",
                "sourceNamespace": "chord",
                "annotationRole": "performed",
                "sourceFields": ["data.time", "data.duration"],
            },
        },
    }
    if beat_times:
        metadata["beatTimesSeconds"] = beat_times
        metadata["downbeatTimesSeconds"] = downbeat_times
        metadata["timingProvenance"].update(
            {
                "sourceFormat": "guitarset-jams-beat_position",
                "beatTimesSeconds": {
                    "status": "explicit",
                    "sourceNamespace": "beat_position",
                    "sourceField": "beat_position.data.time",
                },
                "downbeatTimesSeconds": {
                    "status": "explicit",
                    "sourceNamespace": "beat_position",
                    "sourceRule": "beat_position.value.position-equals-1",
                },
                "barStartsSeconds": {
                    "status": "explicit" if _starts_at_zero(downbeat_times) else "uncertifiable",
                    "sourceNamespace": "beat_position",
                    "sourceRule": "beat_position.value.position-equals-1",
                },
            }
        )
        if _starts_at_zero(downbeat_times):
            metadata["barStartsSeconds"] = downbeat_times
        elif downbeat_times:
            metadata["timingProvenance"]["barStartsSeconds"]["reason"] = (
                "first annotated downbeat is not at zero"
            )
    return segments, metadata


def parse_winterreise_chords(path: Path) -> list[dict[str, Any]]:
    """Read the dataset's audio-aligned semicolon chord tables."""

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    segments = [
        {
            "start": float(row["start"]),
            "end": float(row["end"]),
            "label": normalize_chord(row["shorthand"]).detailed_symbol,
        }
        for row in rows
        if row.get("start") and row.get("end") and row.get("shorthand")
    ]
    if not segments:
        raise ValueError(f"No chord rows in {path}.")
    return segments


def _idmt_chord_symbol(symbol: str) -> str:
    value = symbol.strip()
    if value.upper() == "NC":
        return "N"
    if value == "GB5":
        value = "Gb5"
    chord, slash, bass = value.partition("/")
    if slash and bass.startswith("7"):
        chord += "7"
        bass = bass[1:]
    match = re.match(r"^([A-G](?:b|#)?)(.*)$", chord)
    if not match:
        raise ValueError(f"Unsupported IDMT chord {symbol!r}.")
    root, quality = match.groups()
    quality_aliases = {
        "79": "9",
        "79b": "7b9",
        "713": "13",
        "713b": "13",
        "7913": "13",
        "913": "13",
        "1113": "13",
        "75b": "7b5",
        "min75b": "hdim7",
        "min79": "min9",
        "minmaj79": "minmaj7",
        "maj79": "maj9",
        "sus9": "sus2",
    }
    quality = quality_aliases.get(quality, quality)
    normalized = f"{root}:{quality or 'maj'}"
    if slash:
        normalized += f"/{bass}"
    return normalize_chord(normalized).detailed_symbol


def parse_idmt_chords(path: Path, end_seconds: float | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read beat-aligned IDMT dataset-4 chord changes and footer metadata."""

    frames: list[tuple[float, str]] = []
    beat_rows: list[tuple[float, int, int]] = []
    footer: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        value = line.strip()
        if not value:
            continue
        position, separator, payload = value.partition(",")
        beat_text, chord_separator, chord = payload.partition(":")
        beat_match = re.fullmatch(r"(\d+)\.(\d+)", beat_text.strip())
        if separator and beat_match:
            time_seconds = float(position)
            beat_rows.append(
                (time_seconds, int(beat_match.group(1)), int(beat_match.group(2)))
            )
            if chord_separator:
                frames.append((time_seconds, _idmt_chord_symbol(chord)))
        else:
            footer.append(value)
    if not frames:
        raise ValueError(f"No IDMT chord rows in {path}.")
    meter = None
    if footer:
        numerator, separator, denominator = footer[-1].partition(",")
        if separator:
            meter = f"{int(numerator)}/{int(denominator)}"
    tempo_match = re.search(r"_(\d+)BPM$", path.stem, flags=re.IGNORECASE)
    metadata: dict[str, Any] = {
        "tempo": float(tempo_match.group(1)) if tempo_match else None,
        "meter": meter,
    }
    beat_times = _strict_source_times(
        (time_seconds for time_seconds, _bar, _beat in beat_rows),
        name="IDMT beatTimesSeconds",
    )
    downbeat_times = _strict_source_times(
        (time_seconds for time_seconds, _bar, beat in beat_rows if beat == 1),
        name="IDMT barStartsSeconds",
    )
    # The filename BPM is useful scalar metadata, but it does not establish bar
    # phase. The bar.beat rows do: IDMT often places 1.1 after a count-in, so the
    # exact pre-roll is disclosed rather than shifting or discarding the grid.
    if beat_times and downbeat_times:
        grid_start = downbeat_times[0]
        metadata.update(
            {
                "beatTimesSeconds": beat_times,
                "downbeatTimesSeconds": downbeat_times,
                "barStartsSeconds": downbeat_times,
                "gridStartSeconds": grid_start,
                "prefixExcludedSeconds": grid_start,
                "timingProvenance": {
                    "sourceFormat": "idmt-dataset-4-chord-csv",
                    "beatTimesSeconds": {
                        "status": "explicit",
                        "sourceField": "bar.beat annotation rows",
                    },
                    "barStartsSeconds": {
                        "status": "explicit",
                        "sourceRule": "annotated beat-number-equals-1",
                        "gridStartSeconds": grid_start,
                        "prefixExcludedSeconds": grid_start,
                    },
                    "tempo": {
                        "status": "derived",
                        "sourceRule": "filename BPM suffix",
                        "establishesBarPhase": False,
                    },
                },
            }
        )
    return _merge_frames(frames, end_seconds=end_seconds), metadata


_MIDI_CHORD_TEMPLATES = {
    "maj": {0, 4, 7},
    "min": {0, 3, 7},
    "7": {0, 4, 7, 10},
    "min7": {0, 3, 7, 10},
    "maj7": {0, 4, 7, 11},
    "dim": {0, 3, 6},
    "aug": {0, 4, 8},
    "sus2": {0, 2, 7},
    "sus4": {0, 5, 7},
    "5": {0, 7},
}


def _midi_chord_label(notes: Iterable[int]) -> str | None:
    """Infer a deterministic Harte chord from simultaneous MIDI attacks."""

    pitches = [int(value) for value in notes]
    if len(set(pitches)) < 2:
        return None
    pitch_classes = {value % 12 for value in pitches}
    bass_candidates = [value for value in pitches if value < 48]
    bass = min(bass_candidates) % 12 if bass_candidates else None
    best: tuple[float, int, int, str, set[int]] | None = None
    for root in range(12):
        for quality, intervals in _MIDI_CHORD_TEMPLATES.items():
            template = {(root + interval) % 12 for interval in intervals}
            intersection = len(template & pitch_classes)
            score = 2 * intersection / (len(template) + len(pitch_classes))
            if template <= pitch_classes:
                score += 0.4
            score -= 0.03 * len(pitch_classes - template)
            if bass == root:
                score += 0.08
            candidate = (score, len(template), -root, quality, template)
            if best is None or candidate > best:
                best = candidate
    assert best is not None
    _score, _size, negative_root, quality, template = best
    root = -negative_root
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    symbol = f"{names[root]}:{quality}"
    if bass is not None and bass != root and bass in template:
        symbol += f"/{names[bass]}"
    return normalize_chord(symbol).detailed_symbol


def _certified_midi_bar_timing(
    *,
    ticks_per_beat: int,
    end_tick: int,
    tempo_events: list[tuple[int, int]],
    time_signature_events: list[tuple[int, int, int]],
) -> tuple[list[float] | None, dict[str, Any]]:
    """Certify MIDI bar phase only when every signature boundary is exact."""

    tempo_map = [
        {
            "tick": tick,
            "microsecondsPerQuarter": tempo,
            "timeSeconds": _tick_seconds(tick, ticks_per_beat, tempo_events),
        }
        for tick, tempo in tempo_events
    ]
    signature_map = [
        {"tick": tick, "numerator": numerator, "denominator": denominator}
        for tick, numerator, denominator in time_signature_events
    ]
    provenance: dict[str, Any] = {
        "sourceFormat": "standard-midi-file",
        "ticksPerQuarterNote": ticks_per_beat,
        "tempoMap": tempo_map,
        "timeSignatureMap": signature_map,
        "barStartsSeconds": {
            "status": "uncertifiable",
            "sourceRule": "MIDI ticks through explicit time-signature and tempo maps",
        },
    }

    def uncertifiable(reason: str) -> tuple[None, dict[str, Any]]:
        provenance["barStartsSeconds"]["reason"] = reason
        return None, provenance

    if ticks_per_beat <= 0 or end_tick <= 0:
        return uncertifiable("MIDI resolution or duration is not positive")
    if not time_signature_events or time_signature_events[0][0] != 0:
        return uncertifiable("no explicit time-signature event establishes bar phase at tick zero")
    if any(tempo <= 0 for _tick, tempo in tempo_events):
        return uncertifiable("tempo map contains a non-positive tempo")

    bar_ticks: list[int] = []
    previous_start: int | None = None
    previous_step: int | None = None
    for index, (start_tick, numerator, denominator) in enumerate(time_signature_events):
        if numerator <= 0 or denominator <= 0 or denominator & (denominator - 1):
            return uncertifiable("time-signature map contains an invalid signature")
        ticks_per_bar = Fraction(numerator * ticks_per_beat * 4, denominator)
        if ticks_per_bar.denominator != 1 or ticks_per_bar.numerator <= 0:
            return uncertifiable("time signature does not resolve to whole MIDI ticks per bar")
        if (
            previous_start is not None
            and previous_step is not None
            and (start_tick - previous_start) % previous_step
        ):
            return uncertifiable("a time-signature change occurs between certified bar boundaries")
        step = int(ticks_per_bar)
        next_tick = (
            time_signature_events[index + 1][0]
            if index + 1 < len(time_signature_events)
            else end_tick
        )
        if next_tick < start_tick:
            return uncertifiable("time-signature events are not monotonic")
        tick = start_tick
        while tick < min(next_tick, end_tick):
            bar_ticks.append(tick)
            tick += step
        previous_start = start_tick
        previous_step = step

    starts = _strict_source_times(
        (_tick_seconds(tick, ticks_per_beat, tempo_events) for tick in sorted(set(bar_ticks))),
        name="NRG-CP barStartsSeconds",
    )
    if not _starts_at_zero(starts):
        return uncertifiable("certified MIDI bar starts do not begin at zero")
    provenance["barStartsSeconds"] = {
        "status": "explicit",
        "sourceRule": "MIDI ticks through explicit time-signature and tempo maps",
        "barPhaseAnchorTick": 0,
    }
    return starts, provenance


def parse_nrgcp_midi(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive beat-aligned ground truth and certified native MIDI bar timing."""

    mido = importlib.import_module("mido")
    midi = mido.MidiFile(path)
    merged = list(mido.merge_tracks(midi.tracks))
    attacks: dict[int, list[int]] = {}
    absolute_tick = 0
    tempo_by_tick: dict[int, int] = {0: 500_000}
    signature_by_tick: dict[int, tuple[int, int]] = {}
    for message in merged:
        absolute_tick += int(message.time)
        if message.type == "set_tempo":
            tempo_by_tick[absolute_tick] = int(message.tempo)
        elif message.type == "time_signature":
            signature_by_tick[absolute_tick] = (
                int(message.numerator),
                int(message.denominator),
            )
        elif message.type == "note_on" and int(message.velocity) > 0:
            beat = absolute_tick // midi.ticks_per_beat
            attacks.setdefault(beat, []).append(int(message.note))
    if not attacks:
        raise ValueError(f"No note attacks in {path}.")
    end_tick = absolute_tick
    tempo_events = sorted(tempo_by_tick.items())
    signature_events = [
        (tick, numerator, denominator)
        for tick, (numerator, denominator) in sorted(signature_by_tick.items())
    ]
    last_beat = max(attacks)
    frames: list[tuple[float, str]] = []
    active: str | None = None
    for beat in range(last_beat + 1):
        inferred = _midi_chord_label(attacks.get(beat, ()))
        if inferred is not None:
            active = inferred
        if active is not None:
            frames.append(
                (
                    _tick_seconds(beat * midi.ticks_per_beat, midi.ticks_per_beat, tempo_events),
                    active,
                )
            )
    end_seconds = _tick_seconds(end_tick, midi.ticks_per_beat, tempo_events)
    bar_starts, timing_provenance = _certified_midi_bar_timing(
        ticks_per_beat=midi.ticks_per_beat,
        end_tick=end_tick,
        tempo_events=tempo_events,
        time_signature_events=signature_events,
    )
    tempo_values = {tempo for _tick, tempo in tempo_events}
    signature_values = {
        (numerator, denominator) for _tick, numerator, denominator in signature_events
    }
    metadata: dict[str, Any] = {
        "tempo": 60_000_000 / tempo_events[0][1] if len(tempo_values) == 1 else None,
        "meter": (
            f"{signature_events[0][1]}/{signature_events[0][2]}"
            if bar_starts is not None and len(signature_values) == 1 and signature_events
            else None
        ),
        "durationSeconds": end_seconds,
        "timingProvenance": timing_provenance,
    }
    if bar_starts is not None:
        metadata["barStartsSeconds"] = bar_starts
    return _merge_frames(frames, end_seconds=end_seconds), metadata


def _render_nrgcp_midi(path: Path, output: Path, *, sample_rate: int = 11_025) -> float:
    """Render a deterministic multi-harmonic training mix without external synthesizer state."""

    mido = importlib.import_module("mido")
    numpy = importlib.import_module("numpy")
    midi = mido.MidiFile(path)
    tempo = 500_000
    for track in midi.tracks:
        for message in track:
            if message.type == "set_tempo":
                tempo = int(message.tempo)
    absolute_tick = 0
    active: dict[tuple[int, int], tuple[int, int]] = {}
    notes: list[tuple[float, float, int, int]] = []
    for message in mido.merge_tracks(midi.tracks):
        absolute_tick += int(message.time)
        if message.type == "note_on" and int(message.velocity) > 0:
            active[(int(message.channel), int(message.note))] = (absolute_tick, int(message.velocity))
        elif message.type in {"note_off", "note_on"}:
            key = (int(message.channel), int(message.note))
            started = active.pop(key, None)
            if started is not None:
                start_tick, velocity = started
                start = mido.tick2second(start_tick, midi.ticks_per_beat, tempo)
                end = mido.tick2second(absolute_tick, midi.ticks_per_beat, tempo)
                notes.append((start, max(start + 0.04, end), int(message.note), velocity))
    duration = max(float(midi.length), max((end for _start, end, _note, _velocity in notes), default=0.0))
    audio = numpy.zeros(max(1, math.ceil((duration + 0.08) * sample_rate)), dtype=numpy.float32)
    variant = int(hashlib.sha256(path.stem.encode()).hexdigest()[:8], 16) % 3
    harmonic_sets = ((1.0, 0.45, 0.18), (1.0, 0.28, 0.12), (1.0, 0.55, 0.26))
    harmonics = harmonic_sets[variant]
    for start, end, note, velocity in notes:
        release = 0.06 if variant != 1 else 0.1
        start_sample = max(0, round(start * sample_rate))
        end_sample = min(len(audio), round((end + release) * sample_rate))
        times = numpy.arange(end_sample - start_sample, dtype=numpy.float32) / sample_rate
        frequency = 440 * 2 ** ((note - 69) / 12)
        attack = numpy.minimum(1, times / (0.012 if variant == 2 else 0.004))
        sustain_end = max(0.01, end - start)
        envelope = attack * numpy.where(
            times <= sustain_end,
            numpy.exp(-times * (1.8 if variant == 0 else 0.45)),
            numpy.exp(-sustain_end * (1.8 if variant == 0 else 0.45))
            * numpy.maximum(0, 1 - (times - sustain_end) / release),
        )
        phase = 2 * numpy.pi * frequency * times
        tone = sum(amplitude * numpy.sin((index + 1) * phase) for index, amplitude in enumerate(harmonics))
        bass_gain = 1.25 if note < 48 else 1.0
        audio[start_sample:end_sample] += tone * envelope * (velocity / 127) * bass_gain
    peak = float(numpy.max(numpy.abs(audio)))
    if peak:
        audio *= 0.9 / peak
    pcm = numpy.rint(audio * 32767).astype("<i2")
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
    return len(audio) / sample_rate


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


def _write_reference(
    path: Path,
    identifier: str,
    segments: list[dict[str, Any]],
    *,
    provenance: dict[str, Any] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value: dict[str, Any] = {
        "schemaVersion": "chord_reference_v1",
        "id": identifier,
        "segments": segments,
    }
    if provenance:
        value["provenance"] = provenance
    path.write_text(
        json.dumps(value, indent=2) + "\n",
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
        performed_identifier = f"{identifier}-performed"
        performed_reference = output_root / "references" / f"{performed_identifier}.json"
        _write_reference(reference, identifier, segments)
        _write_reference(
            performed_reference,
            performed_identifier,
            metadata["performedSegments"],
            provenance=metadata["chordProvenance"]["performedReference"],
        )
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
                "performedReferencePath": str(performed_reference.resolve()),
                "labelSource": "ground_truth",
                "labelSourceDetail": "guitarset:chord:instructed-lead-sheet",
                "labelSourceProvenance": metadata["chordProvenance"]["primaryReference"],
                "performedLabelSourceDetail": (
                    "guitarset:chord:sheet-informed-performed-quality"
                ),
                "performedLabelSourceProvenance": metadata["chordProvenance"]["performedReference"],
                "performanceRole": metadata["performanceRole"],
                "chordProvenance": metadata["chordProvenance"],
                "trainingWeight": 1.0,
                "durationSeconds": metadata["durationSeconds"],
                "tempo": metadata.get("tempo"),
                "meter": metadata.get("meter"),
                "key": metadata.get("key"),
                **_timing_manifest_fields(metadata),
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
                **_timing_manifest_fields(metadata),
            }
        )
    frozen = assign_group_splits(tracks, seed=seed)
    for track in frozen:
        if track["split"] == "test":
            track["trainingWeight"] = 0.0
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": frozen}


def prepare_winterreise(
    annotations_root: Path,
    audio_root: Path,
    output_root: Path,
    *,
    seed: str = "chord-reader-v3-split-1",
    max_tracks: int | None = None,
) -> dict[str, Any]:
    tracks: list[dict[str, Any]] = []
    for audio_path in sorted(audio_root.glob("Schubert_D911-*.wav")):
        if max_tracks is not None and len(tracks) >= max_tracks:
            break
        annotation = annotations_root / f"{audio_path.stem}.csv"
        if not annotation.is_file():
            continue
        segments = parse_winterreise_chords(annotation)
        identifier = f"winterreise-{audio_path.stem.lower()}"
        reference = output_root / "references" / f"{identifier}.json"
        _write_reference(reference, identifier, segments)
        composition = audio_path.stem.rsplit("_", 1)[0]
        performance = audio_path.stem.rsplit("_", 1)[1]
        tracks.append(
            {
                "id": identifier,
                "datasetId": "winterreise",
                "groupId": performance,
                "compositionId": composition,
                "audioPath": str(audio_path.resolve()),
                "referencePath": str(reference.resolve()),
                "labelSource": "ground_truth",
                "trainingWeight": 1.0,
            }
        )
    frozen = assign_group_splits(tracks, seed=seed)
    for track in frozen:
        if track["split"] == "test":
            track["trainingWeight"] = 0.0
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": frozen}


def prepare_idmt_guitar(
    annotations_root: Path,
    audio_root: Path,
    output_root: Path,
    *,
    seed: str = "chord-reader-v3-split-1",
    max_tracks: int | None = None,
) -> dict[str, Any]:
    """Normalize IDMT dataset 4 while grouping all renditions of one piece."""

    tracks: list[dict[str, Any]] = []
    for annotation in sorted(annotations_root.glob("**/annotation/chords/*.csv")):
        if max_tracks is not None and len(tracks) >= max_tracks:
            break
        relative = annotation.relative_to(annotations_root)
        setup, speed, genre = relative.parts[:3]
        audio_path = audio_root / setup / speed / genre / "audio" / f"{annotation.stem}.wav"
        if not audio_path.is_file():
            continue
        with wave.open(str(audio_path), "rb") as handle:
            duration = handle.getnframes() / handle.getframerate()
        segments, metadata = parse_idmt_chords(annotation, end_seconds=duration)
        slug = re.sub(r"[^a-z0-9]+", "-", f"{setup}-{speed}-{annotation.stem}".lower()).strip("-")
        identifier = f"idmt-guitar-{slug}"
        reference = output_root / "references" / f"{identifier}.json"
        _write_reference(reference, identifier, segments)
        composition = re.sub(r"_\d+BPM$", "", annotation.stem, flags=re.IGNORECASE)
        tracks.append(
            {
                "id": identifier,
                "datasetId": "idmt_guitar",
                "groupId": setup,
                "compositionId": composition,
                "audioPath": str(audio_path.resolve()),
                "referencePath": str(reference.resolve()),
                "labelSource": "ground_truth",
                "trainingWeight": 1.0,
                "durationSeconds": duration,
                "tempo": metadata["tempo"],
                "meter": metadata["meter"],
                "genre": genre,
                "performanceSpeed": speed,
                **_timing_manifest_fields(metadata),
            }
        )
    frozen = assign_group_splits(tracks, seed=seed)
    for track in frozen:
        if track["split"] == "test":
            track["trainingWeight"] = 0.0
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": frozen}


def prepare_nrgcp(
    annotations_root: Path,
    audio_root: Path,
    output_root: Path,
    *,
    seed: str = "chord-reader-v3-split-1",
    max_tracks: int | None = None,
    exclude_manifest: Path | None = None,
    evaluation_only: bool = False,
) -> dict[str, Any]:
    """Render and normalize a deterministic subset of CC BY NRG-CP MIDI progressions."""

    excluded_compositions: set[str] = set()
    if exclude_manifest:
        excluded_compositions = {
            str(track.get("compositionId") or "")
            for track in json.loads(exclude_manifest.read_text(encoding="utf-8")).get("tracks", [])
        }
    candidates = [
        path
        for path in sorted(
            annotations_root.glob("*.mid"),
            key=lambda path: hashlib.sha256(f"{seed}:{path.stem}".encode()).hexdigest(),
        )
        if path.stem not in excluded_compositions
    ]
    if max_tracks is not None:
        candidates = candidates[:max_tracks]
    tracks: list[dict[str, Any]] = []
    for midi_path in candidates:
        identifier = f"nrgcp-{midi_path.stem.removesuffix('_nrgcp_dataset')}"
        audio_path = audio_root / f"{identifier}.wav"
        segments, metadata = parse_nrgcp_midi(midi_path)
        duration = (
            metadata["durationSeconds"]
            if audio_path.is_file()
            else _render_nrgcp_midi(midi_path, audio_path)
        )
        reference = output_root / "references" / f"{identifier}.json"
        _write_reference(reference, identifier, segments)
        tracks.append(
            {
                "id": identifier,
                "datasetId": "nrgcp",
                "groupId": midi_path.stem,
                "compositionId": midi_path.stem,
                "audioPath": str(audio_path.resolve()),
                "referencePath": str(reference.resolve()),
                "labelSource": "symbolic_ground_truth",
                "trainingWeight": 0.35,
                "durationSeconds": duration,
                "tempo": metadata["tempo"],
                "meter": metadata["meter"],
                **_timing_manifest_fields(metadata),
            }
        )
    frozen = assign_group_splits(tracks, seed=seed)
    for track in frozen:
        if evaluation_only:
            track["split"] = "test"
            track["splitGroup"] = str(track["compositionId"])
            track["trainingWeight"] = 0.0
        elif track["split"] == "test":
            track["trainingWeight"] = 0.0
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": frozen}


def _tick_seconds(tick: int, ticks_per_beat: int, tempo_events: list[tuple[int, int]]) -> float:
    """Convert an absolute MIDI tick through a piecewise-constant tempo map."""

    elapsed = 0.0
    previous_tick = 0
    tempo = 500_000
    for event_tick, event_tempo in tempo_events:
        if event_tick > tick:
            break
        elapsed += (event_tick - previous_tick) * tempo / (1_000_000 * ticks_per_beat)
        previous_tick = event_tick
        tempo = event_tempo
    return elapsed + (tick - previous_tick) * tempo / (1_000_000 * ticks_per_beat)


def _midi_note_intervals(path: Path) -> tuple[int, list[tuple[int, int, int]], list[tuple[int, int]], str]:
    """Read note intervals and timing metadata without requiring a synthesizer."""

    mido = importlib.import_module("mido")
    midi = mido.MidiFile(path)
    absolute_tick = 0
    active: dict[tuple[int, int], list[int]] = {}
    intervals: list[tuple[int, int, int]] = []
    tempo_events: list[tuple[int, int]] = []
    meter = "4/4"
    for message in mido.merge_tracks(midi.tracks):
        absolute_tick += int(message.time)
        if message.type == "set_tempo":
            tempo_events.append((absolute_tick, int(message.tempo)))
        elif message.type == "time_signature":
            meter = f"{int(message.numerator)}/{int(message.denominator)}"
        elif message.type == "note_on" and int(message.velocity) > 0:
            active.setdefault((int(message.channel), int(message.note)), []).append(absolute_tick)
        elif message.type in {"note_off", "note_on"}:
            key = (int(message.channel), int(message.note))
            starts = active.get(key)
            if starts:
                start = starts.pop()
                intervals.append((start, max(start + 1, absolute_tick), key[1]))
    for (_channel, note), starts in active.items():
        intervals.extend((start, max(start + 1, absolute_tick), note) for start in starts)
    if not tempo_events or tempo_events[0][0] != 0:
        tempo_events.insert(0, (0, 500_000))
    deduplicated_tempos = list(dict(tempo_events).items())
    return midi.ticks_per_beat, intervals, deduplicated_tempos, meter


def _weighted_midi_chord_label(pitch_weights: dict[int, float], bass: int | None) -> str | None:
    """Template-match a score frame while allowing melody and doubled accompaniment notes."""

    weights = {pitch % 12: float(weight) for pitch, weight in pitch_weights.items() if weight > 0}
    if len(weights) < 2:
        return None
    total = sum(weights.values())
    maximum = max(weights.values())
    best: tuple[float, int, int, str, set[int]] | None = None
    for root in range(12):
        for quality, intervals in _MIDI_CHORD_TEMPLATES.items():
            template = {(root + interval) % 12 for interval in intervals}
            matched_weight = sum(weights.get(pitch, 0.0) for pitch in template)
            precision = matched_weight / total
            coverage = sum(min(1.0, weights.get(pitch, 0.0) / maximum) for pitch in template) / len(template)
            score = 0.58 * precision + 0.42 * coverage
            if bass == root:
                score += 0.1
            elif bass in template:
                score += 0.025
            if quality in {"7", "min7", "maj7"}:
                seventh = (root + {"7": 10, "min7": 10, "maj7": 11}[quality]) % 12
                if weights.get(seventh, 0.0) < 0.35 * maximum:
                    score -= 0.16
            candidate = (score, -len(template), -root, quality, template)
            if best is None or candidate > best:
                best = candidate
    assert best is not None
    score, _negative_size, negative_root, quality, template = best
    if score < 0.48:
        return None
    root = -negative_root
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    symbol = f"{names[root]}:{quality}"
    if bass is not None and bass != root and bass in template:
        symbol += f"/{names[bass]}"
    return normalize_chord(symbol).detailed_symbol


def parse_babyslakh_score(track_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive beat-aligned evaluation chords from BabySlakh's aligned stem MIDI scores."""

    yaml = importlib.import_module("yaml")
    metadata = yaml.safe_load((track_root / "metadata.yaml").read_text(encoding="utf-8"))
    harmonic_stems: list[list[tuple[int, int, int]]] = []
    bass_intervals: list[tuple[int, int, int]] = []
    ticks_per_beat = 0
    tempo_events: list[tuple[int, int]] = []
    meter = "4/4"
    for stem_id, stem in sorted(metadata["stems"].items()):
        midi_path = track_root / str(metadata.get("midi_dir") or "MIDI") / f"{stem_id}.mid"
        if not midi_path.is_file() or stem.get("is_drum"):
            continue
        instrument_class = str(stem.get("inst_class") or "")
        if instrument_class == "Sound Effects":
            continue
        stem_ticks, intervals, stem_tempos, stem_meter = _midi_note_intervals(midi_path)
        if ticks_per_beat and stem_ticks != ticks_per_beat:
            raise ValueError(f"Mismatched MIDI resolution in {track_root}.")
        ticks_per_beat = stem_ticks
        if not tempo_events:
            tempo_events, meter = stem_tempos, stem_meter
        if instrument_class == "Bass":
            bass_intervals.extend(intervals)
        else:
            harmonic_stems.append(intervals)
    if not harmonic_stems or not ticks_per_beat:
        raise ValueError(f"No harmonic MIDI stems in {track_root}.")
    maximum_tick = max(end for intervals in harmonic_stems for _start, end, _note in intervals)
    frames: list[tuple[float, str]] = []
    active_label = "N"
    for beat_tick in range(0, maximum_tick + 1, ticks_per_beat):
        midpoint = beat_tick + ticks_per_beat // 2
        pitch_weights: dict[int, float] = {}
        for intervals in harmonic_stems:
            pitches = {note % 12 for start, end, note in intervals if start <= midpoint < end}
            for pitch in pitches:
                pitch_weights[pitch] = pitch_weights.get(pitch, 0.0) + 1.0
        active_bass = [note for start, end, note in bass_intervals if start <= midpoint < end]
        bass = min(active_bass) % 12 if active_bass else None
        inferred = _weighted_midi_chord_label(pitch_weights, bass)
        if inferred is not None:
            active_label = inferred
        frames.append((_tick_seconds(beat_tick, ticks_per_beat, tempo_events), active_label))
    with wave.open(str(track_root / "mix.wav"), "rb") as handle:
        duration = handle.getnframes() / handle.getframerate()
    return _merge_frames(frames, end_seconds=duration), {
        "durationSeconds": duration,
        "meter": meter,
        "tempo": 60_000_000 / tempo_events[0][1],
        "harmonicStemCount": len(harmonic_stems),
    }


def prepare_babyslakh(
    annotations_root: Path,
    audio_root: Path,
    output_root: Path,
    *,
    seed: str = "chord-reader-v3-split-1",
    max_tracks: int | None = None,
) -> dict[str, Any]:
    """Build an evaluation-only manifest from BabySlakh mixes and aligned scores."""

    tracks: list[dict[str, Any]] = []
    track_roots = sorted(annotations_root.glob("Track*"))
    if max_tracks is not None:
        track_roots = track_roots[:max_tracks]
    for annotation_root in track_roots:
        audio_path = audio_root / annotation_root.name / "mix.wav"
        if not audio_path.is_file():
            continue
        segments, metadata = parse_babyslakh_score(annotation_root)
        identifier = f"babyslakh-{annotation_root.name.lower()}"
        reference = output_root / "references" / f"{identifier}.json"
        _write_reference(reference, identifier, segments)
        tracks.append(
            {
                "id": identifier,
                "datasetId": "babyslakh",
                "groupId": annotation_root.name,
                "compositionId": annotation_root.name,
                "audioPath": str(audio_path.resolve()),
                "referencePath": str(reference.resolve()),
                "labelSource": "aligned_symbolic_score",
                "trainingWeight": 0.0,
                "durationSeconds": metadata["durationSeconds"],
                "tempo": metadata["tempo"],
                "meter": metadata["meter"],
                "harmonicStemCount": metadata["harmonicStemCount"],
                "split": "test",
                "splitGroup": annotation_root.name,
            }
        )
    return {"schemaVersion": "chord_track_manifest_v1", "splitSeed": seed, "tracks": tracks}
