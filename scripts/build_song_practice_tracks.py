#!/usr/bin/env python3
"""Render the three deterministic no-steel Song Practice preview masters."""

from __future__ import annotations

from array import array
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import wave


SAMPLE_RATE = 22_050
NOTE_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKS = (
    {
        "id": "amazing-grace-preview-v1",
        "filename": "amazing-grace-preview.mp3",
        "meter": 3,
        "bar_seconds": 2.1,
        "transpose": 0,
        "score_path": "pocketsteel/resources/public_domain_songs/amazing_grace_new_britain.json",
        "chords": ("G", "G", "D7", "G", "G", "G", "D7", "G", "G", "G", "G", "C", "G", "G", "D7", "G"),
    },
    {
        "id": "when-the-saints-preview-v1",
        "filename": "when-the-saints-preview.mp3",
        "meter": 4,
        "bar_seconds": 2.0,
        "transpose": 7,
        "songbook_id": "when-the-saints",
        "chords": ("G", "G", "G", "G", "G", "G", "G", "D7", "D7", "G", "G", "C", "C", "G", "D7", "G", "G"),
    },
    {
        "id": "oh-susanna-preview-v1",
        "filename": "oh-susanna-preview.mp3",
        "meter": 2,
        "bar_seconds": 1.9,
        "transpose": 0,
        "songbook_id": "oh-susanna",
        "chords": ("G", "G", "G", "G", "D7", "G", "G", "D7", "G C", "C", "G", "D7", "G", "G", "D7", "G"),
    },
)


def chord_spec(symbol: str) -> tuple[int, tuple[int, ...]]:
    suffix = ""
    root = symbol
    if symbol.endswith("m"):
        root, suffix = symbol[:-1], "m"
    elif symbol.endswith("7"):
        root, suffix = symbol[:-1], "7"
    intervals = (0, 3, 7) if suffix == "m" else (0, 4, 7, 10) if suffix == "7" else (0, 4, 7)
    return NOTE_PC[root], intervals


def frequency(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def load_score(track: dict[str, object]) -> dict[str, object]:
    if track.get("score_path"):
        payload = json.loads((REPO_ROOT / str(track["score_path"])).read_text(encoding="utf-8"))
        return dict(payload["score"])
    songbook = json.loads(
        (REPO_ROOT / "pocketsteel/resources/public_domain_songs/starter_songbook_v1.json").read_text(encoding="utf-8")
    )
    song = next(item for item in songbook["songs"] if item["source"]["catalogId"] == track["songbook_id"])
    return dict(song["score"])


def midi_for_note(note: str, transpose: int = 0) -> int:
    match = re.fullmatch(r"([A-G])([#b]?)(-?\d+)", note)
    if not match:
        raise ValueError(f"Unsupported melody pitch: {note}")
    pitch_class = NOTE_PC[f"{match.group(1)}{match.group(2)}"]
    return (int(match.group(3)) + 1) * 12 + pitch_class + transpose


def melody_events(track: dict[str, object]) -> list[tuple[float, float, int]]:
    meter = int(track["meter"])
    bar_seconds = float(track["bar_seconds"])
    beat_seconds = bar_seconds / meter
    count_in_seconds = bar_seconds
    score = load_score(track)
    measures = list(score["melodyMeasures"])
    chords = tuple(str(chord) for chord in track["chords"])
    if len(measures) != len(chords):
        raise ValueError(f"{track['id']} melody/chart length mismatch: {len(measures)} != {len(chords)}")
    events: list[tuple[float, float, int]] = []
    for measure_index, raw_measure in enumerate(measures):
        measure = [(str(note), float(beats)) for note, beats in raw_measure]
        total_beats = sum(beats for _note, beats in measure)
        scale = min(1.0, meter / total_beats) if total_beats else 1.0
        pickup_offset = max(0.0, meter - (total_beats * scale)) if measure_index == 0 else 0.0
        cursor = pickup_offset
        for note, beats in measure:
            scaled_beats = beats * scale
            start = count_in_seconds + (measure_index * bar_seconds) + (cursor * beat_seconds)
            end = start + max(0.04, scaled_beats * beat_seconds * 0.93)
            if note.lower() != "z":
                events.append((start, end, midi_for_note(note, int(track.get("transpose") or 0))))
            cursor += scaled_beats
    return events


def active_chord_symbol(chord_bar: str, within_bar: float, bar_seconds: float) -> str:
    choices = chord_bar.split()
    index = min(len(choices) - 1, int((within_bar / bar_seconds) * len(choices)))
    return choices[index]


def render_track(track: dict[str, object], output_dir: Path) -> None:
    meter = int(track["meter"])
    bar_seconds = float(track["bar_seconds"])
    chords = tuple(str(chord) for chord in track["chords"])
    beat_seconds = bar_seconds / meter
    count_in_seconds = bar_seconds
    duration = count_in_seconds + (len(chords) * bar_seconds) + 0.5
    events = melody_events(track)
    frame_count = round(duration * SAMPLE_RATE)
    frames = array("h")
    melody_index = 0
    for sample in range(frame_count):
        time_value = sample / SAMPLE_RATE
        value = 0.0
        if time_value < count_in_seconds:
            beat_age = time_value % beat_seconds
            beat = int(time_value / beat_seconds)
            click_frequency = 1_250 if beat == 0 else 950
            value = 0.17 * math.exp(-beat_age * 28.0) * math.sin(2 * math.pi * click_frequency * beat_age)
        else:
            song_time = time_value - count_in_seconds
            bar = min(int(song_time / bar_seconds), len(chords) - 1)
            within_bar = song_time - (bar * bar_seconds)
            beat = min(int(within_bar / beat_seconds), meter - 1)
            within_beat = within_bar - (beat * beat_seconds)
            chord_symbol = active_chord_symbol(chords[bar], within_bar, bar_seconds)
            root_pc, intervals = chord_spec(chord_symbol)

            # Gentle piano-like chord pulses and a warm bass downbeat. There is
            # deliberately no drum noise or steel-guitar timbre.
            chord_envelope = math.exp(-within_beat * 3.6)
            for interval in intervals[:3]:
                chord_midi = 55 + ((root_pc + interval - 7) % 12)
                phase = 2 * math.pi * frequency(chord_midi) * time_value
                value += 0.026 * chord_envelope * math.sin(phase)
                value += 0.007 * chord_envelope * math.sin(phase * 2)
            if beat == 0:
                bass_phase = 2 * math.pi * frequency(43 + ((root_pc - 7) % 12)) * time_value
                value += 0.10 * math.exp(-within_bar * 2.2) * math.sin(bass_phase)

        while melody_index < len(events) and time_value >= events[melody_index][1]:
            melody_index += 1
        if melody_index < len(events):
            note_start, note_end, note_midi = events[melody_index]
            if note_start <= time_value < note_end:
                age = time_value - note_start
                remaining = note_end - time_value
                envelope = min(1.0, age / 0.035, remaining / 0.09)
                phase = 2 * math.pi * frequency(note_midi) * time_value
                # A clear, mellow lead voice makes the public-domain tune
                # recognizable while leaving the chord-playing role to steel.
                value += envelope * (
                    0.22 * math.sin(phase)
                    + 0.055 * math.sin(phase * 2)
                    + 0.018 * math.sin(phase * 3)
                )

        if duration - time_value < 0.35:
            value *= max(0.0, (duration - time_value) / 0.35)
        frames.append(max(-32767, min(32767, round(value * 32767))))

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="song-practice-") as temp_dir:
        wav_path = Path(temp_dir) / "preview.wav"
        with wave.open(str(wav_path), "wb") as destination:
            destination.setnchannels(1)
            destination.setsampwidth(2)
            destination.setframerate(SAMPLE_RATE)
            destination.writeframes(frames.tobytes())
        output_path = output_dir / str(track["filename"])
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(wav_path),
                "-map_metadata",
                "-1",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "96k",
                str(output_path),
            ],
            check=True,
        )
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    print(f"{output_path.name} {output_path.stat().st_size} {digest}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("ui/assets/song-practice"))
    args = parser.parse_args()
    for track in TRACKS:
        render_track(track, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
