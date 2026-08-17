"""Deterministic orchestration around local audio-analysis dependencies.

The analysis service produces review candidates only. Hard timing and E9
mechanical validation remains in the generic companion contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping, Protocol, Sequence
import wave

import numpy as np

from partner_companions.travis_tutorials import validate_companion_v3
from steel_guitar_rag.melody_assistant import melody_exercise_response
from steel_guitar_rag.melody_arranger import scientific_pitch_for_value


ANALYSIS_SCHEMA_VERSION = "travis_companion_analysis_v1"
DEFAULT_SAMPLE_RATE = 11_025
SCIENTIFIC_PITCH_RE = re.compile(r"^([A-G])([#b]?)(-?\d+)$")
PITCH_CLASSES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


class AnalysisError(RuntimeError):
    """Raised when no reviewable analysis artifact can be produced."""


@dataclass(frozen=True)
class AlignmentResult:
    status: str
    track_start_ms: int | None
    track_end_ms: int | None
    confidence: float
    method: str = "normalized_onset_correlation_v1"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "trackStartMs": self.track_start_ms,
            "trackEndMs": self.track_end_ms,
            "confidence": round(self.confidence, 6),
            "method": self.method,
        }


class NoteTranscriber(Protocol):
    model_id: str

    def transcribe(self, audio_path: Path) -> list[dict[str, Any]]: ...


class BasicPitchTranscriber:
    """Lazy Basic Pitch adapter kept out of the web/runtime dependency set."""

    model_id = "spotify-basic-pitch-0.4.0"

    def transcribe(self, audio_path: Path) -> list[dict[str, Any]]:
        try:
            from basic_pitch import ICASSP_2022_MODEL_PATH  # type: ignore[import-not-found]
            from basic_pitch.inference import predict  # type: ignore[import-not-found]
        except ImportError as exc:
            raise AnalysisError(
                "Basic Pitch is not installed in the isolated Travis analysis environment."
            ) from exc
        _model_output, _midi, note_events = predict(str(audio_path), ICASSP_2022_MODEL_PATH)
        events: list[dict[str, Any]] = []
        for index, event in enumerate(note_events, start=1):
            start, end, pitch, amplitude, bends = event
            events.append(
                {
                    "id": f"note-{index:04d}",
                    "startMs": round(float(start) * 1000),
                    "endMs": max(round(float(start) * 1000) + 1, round(float(end) * 1000)),
                    "pitchValue": int(pitch),
                    "confidence": max(0.0, min(1.0, float(amplitude))),
                    "pitchBends": [float(value) for value in bends],
                    "provenance": self.model_id,
                }
            )
        return events


def decode_audio(path: Path, *, sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "f32le",
        "pipe:1",
    ]
    result = subprocess.run(command, check=False, capture_output=True)
    if result.returncode != 0:
        raise AnalysisError("FFmpeg could not decode an uploaded companion asset.")
    return np.frombuffer(result.stdout, dtype=np.float32).copy()


def _onset_envelope(samples: np.ndarray, *, window: int = 1024, hop: int = 256) -> np.ndarray:
    if len(samples) < window:
        return np.zeros(1, dtype=np.float32)
    energies = np.array(
        [float(np.mean(np.square(samples[index : index + window]))) for index in range(0, len(samples) - window + 1, hop)],
        dtype=np.float32,
    )
    magnitude = np.sqrt(energies + 1e-12)
    flux = np.maximum(0.0, np.diff(magnitude, prepend=magnitude[0]))
    return flux


def align_passage_to_backing(
    passage_samples: np.ndarray,
    backing_samples: np.ndarray,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    minimum_confidence: float = 0.55,
) -> AlignmentResult:
    """Locate a selected performance passage inside its matching backing track."""

    if len(passage_samples) < sample_rate or len(backing_samples) < len(passage_samples):
        return AlignmentResult("manual_required", None, None, 0.0)
    window = 1024
    hop = 256
    needle = _onset_envelope(passage_samples, window=window, hop=hop)
    haystack = _onset_envelope(backing_samples, window=window, hop=hop)
    if len(needle) > len(haystack) or not np.any(needle):
        return AlignmentResult("manual_required", None, None, 0.0)
    needle_norm = float(np.linalg.norm(needle))
    window_norms = np.sqrt(np.convolve(np.square(haystack), np.ones(len(needle), dtype=np.float32), mode="valid"))
    denominator = np.maximum(window_norms * needle_norm, 1e-12)
    correlation = np.correlate(haystack, needle, mode="valid") / denominator
    best_index = int(np.argmax(correlation))
    confidence = float(max(0.0, min(1.0, correlation[best_index])))
    if confidence < minimum_confidence:
        return AlignmentResult("manual_required", None, None, confidence)
    start_ms = round((best_index * hop / sample_rate) * 1000)
    duration_ms = round((len(passage_samples) / sample_rate) * 1000)
    return AlignmentResult("aligned", start_ms, start_ms + duration_ms, confidence)


def subtract_backing(performance: np.ndarray, backing: np.ndarray) -> np.ndarray:
    """Return a conservative residual after least-squares backing cancellation."""

    length = min(len(performance), len(backing))
    if length == 0:
        return np.array([], dtype=np.float32)
    performance = performance[:length]
    backing = backing[:length]
    denominator = float(np.dot(backing, backing))
    gain = float(np.dot(performance, backing) / denominator) if denominator > 1e-9 else 0.0
    gain = max(0.0, min(2.0, gain))
    residual = performance - gain * backing
    peak = float(np.max(np.abs(residual))) if residual.size else 0.0
    if peak > 1.0:
        residual = residual / peak
    return residual.astype(np.float32)


def waveform_peaks(samples: np.ndarray, *, bins: int = 1_600) -> list[float]:
    if samples.size == 0:
        return []
    width = max(1, math.ceil(len(samples) / bins))
    return [round(float(np.max(np.abs(samples[index : index + width]))), 6) for index in range(0, len(samples), width)]


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    integer = (pcm * 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(integer.tobytes())


def _analyze_chords(audio_path: Path, *, node_script: Path, key: str, meter: str) -> dict[str, Any]:
    result = subprocess.run(
        ["node", str(node_script), "--audio", str(audio_path), "--key", key, "--meter", meter],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AnalysisError("The deterministic backing-track chord analyzer failed.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AnalysisError("The chord analyzer returned an invalid artifact.") from exc


def _pitch_value(label: str) -> int:
    match = SCIENTIFIC_PITCH_RE.match(label)
    if not match:
        raise AnalysisError(f"Invalid scientific pitch in Travis copedent: {label}")
    return (int(match.group(3)) + 1) * 12 + PITCH_CLASSES[f"{match.group(1)}{match.group(2)}"]


def _pitch_class(pitch_value: int) -> str:
    return re.sub(r"-?\d+$", "", scientific_pitch_for_value(pitch_value))


def _arranger_copedent(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    strings = []
    open_values: dict[int, int] = {}
    for item in snapshot.get("stringsHighToLow") or []:
        string = int(item["string"])
        pitch = _pitch_value(str(item["openPitch"]))
        open_values[string] = pitch
        strings.append({"stringNumber": string, "openNote": _pitch_class(pitch), "openPitchValue": pitch})
    controls = []
    for control in snapshot.get("controls") or []:
        code = str(control["code"])
        changes = []
        for change in control.get("changes") or []:
            string = int(change["string"])
            start = open_values[string]
            changes.append({
                "stringNumber": string,
                "fromNote": _pitch_class(start),
                "toNote": _pitch_class(start + int(change["semitones"])),
            })
        controls.append({
            "id": code,
            "label": str(control.get("label") or code),
            "type": str(control.get("type") or ("pedal" if code in {"A", "B", "C"} else "lever")),
            "physicalPosition": str(control.get("physicalPosition") or code),
            "changes": changes,
            "aliases": [code],
        })
    return {
        "id": str(snapshot.get("id") or "travis-e9"),
        "revision": int(snapshot.get("revision") or 1) if str(snapshot.get("revision") or "1").isdigit() else 1,
        "label": str(snapshot.get("label") or "Travis E9"),
        "tuningFamily": "E9",
        "strings": strings,
        "controls": controls,
    }


def _arrange_notes(
    note_events: Sequence[Mapping[str, Any]],
    *,
    key: str,
    copedent: Mapping[str, Any],
    chords: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    melody = [
        {
            "id": str(event["id"]),
            "pitchValue": int(event["pitchValue"]),
            "note": scientific_pitch_for_value(int(event["pitchValue"])),
            "durationBeats": max(0.125, (int(event["endMs"]) - int(event["startMs"])) / 500.0),
            "measure": 1,
            "beat": 1 + (int(event["startMs"]) / 500.0),
            "confidence": float(event.get("confidence") or 0),
        }
        for event in note_events
    ]
    chord_track = [
        {
            "startBeat": max(0.0, int(chord["startMs"]) / 500.0),
            "endBeat": max(0.125, int(chord["endMs"]) / 500.0),
            "symbol": chord.get("symbol") or "N.C.",
        }
        for chord in chords
    ]
    result = melody_exercise_response(
        "Arrange the normalized Travis lesson passage for E9.",
        {
            "key": key,
            "melody": melody,
            "chords": chord_track,
            "targetCopedent": _arranger_copedent(copedent),
            "targetCopedentId": copedent.get("id") or "travis-e9",
            "voiceMode": "mixed",
            "movementMode": "best_fit",
        },
    )
    if result is None:
        raise AnalysisError("No mechanically valid E9 route was found for the selected passage.")
    exercise = result["melody_exercise"]
    selected = next(route for route in exercise["routes"] if route["id"] == exercise["selectedRouteId"])
    return list(selected["events"])


def analyze_project(
    draft: Mapping[str, Any],
    *,
    video_path: Path,
    primary_track_path: Path,
    transcriber: NoteTranscriber | None = None,
    node_script: Path | None = None,
) -> dict[str, Any]:
    """Build a review-ready v3 candidate from private local media."""

    working = json.loads(json.dumps(draft))
    lesson = working["lesson"]
    root = Path(__file__).resolve().parents[2]
    chord_script = node_script or root / "scripts" / "analyze_travis_backing_track.js"
    chords = _analyze_chords(
        primary_track_path,
        node_script=chord_script,
        key=str(lesson.get("key") or "D"),
        meter=str(lesson.get("meter") or "4/4"),
    )
    working["songChordTimeline"] = chords["chordTimeline"]
    primary_id = working["primaryTrackId"]
    primary = next(track for track in working["media"]["backingTracks"] if track["assetId"] == primary_id)
    primary["durationMs"] = int(chords["durationMs"])

    sample_rate = DEFAULT_SAMPLE_RATE
    video_samples = decode_audio(video_path, sample_rate=sample_rate)
    backing_samples = decode_audio(primary_track_path, sample_rate=sample_rate)
    working["media"]["lessonVideo"]["durationMs"] = max(1, round(len(video_samples) * 1000 / sample_rate))
    note_reader = transcriber or BasicPitchTranscriber()
    for passage in working.get("passages") or []:
        video_range = passage["videoRange"]
        video_start = round(int(video_range["startMs"]) * sample_rate / 1000)
        video_end = round(int(video_range["endMs"]) * sample_rate / 1000)
        performance = video_samples[video_start:video_end]
        existing_track_range = passage.get("trackRange") or {}
        if int(existing_track_range.get("endMs") or 0) > int(existing_track_range.get("startMs") or 0):
            alignment = AlignmentResult(
                "manual",
                int(existing_track_range["startMs"]),
                int(existing_track_range["endMs"]),
                1.0,
                "manual_range_v1",
            )
        else:
            alignment = align_passage_to_backing(performance, backing_samples, sample_rate=sample_rate)
        passage["alignment"] = alignment.to_dict()
        if alignment.track_start_ms is None or alignment.track_end_ms is None:
            passage["tabEvents"] = []
            continue
        passage["trackRange"] = {"startMs": alignment.track_start_ms, "endMs": alignment.track_end_ms}
        track_start = round(alignment.track_start_ms * sample_rate / 1000)
        track_end = min(len(backing_samples), track_start + len(performance))
        residual = subtract_backing(performance[: track_end - track_start], backing_samples[track_start:track_end])
        with tempfile.TemporaryDirectory(prefix="travis-companion-analysis-") as temp_dir:
            residual_path = Path(temp_dir) / "steel-residual.wav"
            _write_wav(residual_path, residual, sample_rate)
            note_events = note_reader.transcribe(residual_path)
        local_chords = [
            {
                **chord,
                "startMs": max(0, int(chord["startMs"]) - alignment.track_start_ms),
                "endMs": min(alignment.track_end_ms - alignment.track_start_ms, int(chord["endMs"]) - alignment.track_start_ms),
            }
            for chord in working["songChordTimeline"]
            if int(chord["endMs"]) > alignment.track_start_ms and int(chord["startMs"]) < alignment.track_end_ms
        ]
        arranged = _arrange_notes(
            note_events,
            key=str(lesson.get("key") or "D"),
            copedent=working["copedentSnapshot"],
            chords=local_chords,
        )
        tab_events: list[dict[str, Any]] = []
        if len(arranged) != len(note_events):
            raise AnalysisError("Amazing Tablature did not return one route event per normalized note.")
        for index, (note_event, route_event) in enumerate(zip(note_events, arranged), start=1):
            absolute_start = alignment.track_start_ms + int(note_event["startMs"])
            absolute_end = min(alignment.track_end_ms, alignment.track_start_ms + int(note_event["endMs"]))
            notes = [
                {
                    "string": int(note["string"]),
                    "fret": int(note["fret"]),
                    "controls": list(note.get("controls") or note.get("changes") or []),
                    "pitchValue": int(note["destinationPitch"]),
                    "technique": str(route_event.get("technique") or "pick"),
                }
                for note in route_event.get("mechanicalActions") or []
            ]
            tab_events.append(
                {
                    "id": f"{passage['id']}-event-{index:04d}",
                    "startMs": absolute_start,
                    "endMs": max(absolute_start + 1, absolute_end),
                    "notes": notes,
                    "instruction": route_event.get("explanation") or "",
                    "reviewStatus": "generated_unconfirmed",
                    "confidence": note_event.get("confidence"),
                    "pitchBends": note_event.get("pitchBends") or [],
                    "routeAlternatives": route_event.get("alternatePositions") or [],
                    "provenance": note_reader.model_id,
                }
            )
        passage["tabEvents"] = tab_events

    working["state"] = "review_ready"
    working["analysis"] = {
        "schemaVersion": ANALYSIS_SCHEMA_VERSION,
        "status": "review_ready",
        "modelVersions": {
            "chords": chords.get("analysisVersion"),
            "notes": note_reader.model_id,
            "arranger": "steel-guitar-rag-amazing-tablature-v1",
        },
        "sourceHashes": {},
    }
    working["_derivedWaveform"] = {
        "schemaVersion": "travis_waveform_v1",
        "sampleRate": sample_rate,
        "durationMs": int(primary["durationMs"]),
        "peaks": waveform_peaks(backing_samples),
    }
    validate_companion_v3(working)
    return working
