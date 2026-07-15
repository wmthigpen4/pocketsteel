#!/usr/bin/env python3
"""Render the three deterministic no-steel Song Practice preview masters."""

from __future__ import annotations

from array import array
import argparse
import math
from pathlib import Path
import subprocess
import tempfile
import wave


SAMPLE_RATE = 22_050
NOTE_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
TRACKS = (
    {
        "filename": "amazing-grace-preview.mp3",
        "meter": 3,
        "bar_seconds": 2.05,
        "chords": ("G", "G", "C", "G", "G", "Em", "D7", "D7", "G", "G", "C", "G", "G", "D7", "G", "G"),
    },
    {
        "filename": "when-the-saints-preview.mp3",
        "meter": 4,
        "bar_seconds": 1.82,
        "chords": ("G", "G", "G", "G", "G", "G", "D7", "D7", "G", "G", "C", "C", "G", "D7", "G", "G"),
    },
    {
        "filename": "oh-susanna-preview.mp3",
        "meter": 4,
        "bar_seconds": 1.92,
        "chords": ("G", "G", "G", "D7", "D7", "D7", "G", "G", "G", "G", "C", "C", "G", "D7", "G", "G"),
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


def deterministic_noise(sample: int) -> float:
    value = (sample * 1_103_515_245 + 12_345) & 0x7FFFFFFF
    return (value / 0x3FFFFFFF) - 1.0


def render_track(track: dict[str, object], output_dir: Path) -> None:
    meter = int(track["meter"])
    bar_seconds = float(track["bar_seconds"])
    chords = tuple(str(chord) for chord in track["chords"])
    beat_seconds = bar_seconds / meter
    duration = len(chords) * bar_seconds + 0.35
    frame_count = round(duration * SAMPLE_RATE)
    frames = array("h")
    for sample in range(frame_count):
        time_value = sample / SAMPLE_RATE
        bar = min(int(time_value / bar_seconds), len(chords) - 1)
        within_bar = time_value - bar * bar_seconds
        beat = min(int(within_bar / beat_seconds), meter - 1)
        within_beat = within_bar - beat * beat_seconds
        root_pc, intervals = chord_spec(chords[bar])

        value = 0.0
        # A short, muted keyboard pulse: enough harmony to practice against,
        # but intentionally no slide, sustain, or steel-guitar timbre.
        keyboard_envelope = math.exp(-within_beat * 5.0)
        for interval in intervals[:3]:
            midi = 60 + ((root_pc + interval - 0) % 12)
            value += 0.075 * keyboard_envelope * math.sin(2 * math.pi * frequency(midi) * time_value)
            value += 0.018 * keyboard_envelope * math.sin(2 * math.pi * frequency(midi) * 2 * time_value)

        bass_age = within_bar if beat < 2 else within_bar - (2 * beat_seconds)
        if beat in {0, 2} and bass_age >= 0:
            bass_midi = 36 + root_pc
            value += 0.16 * math.exp(-bass_age * 2.8) * math.sin(2 * math.pi * frequency(bass_midi) * time_value)

        if beat in {0, 2}:
            kick_age = within_beat
            value += 0.22 * math.exp(-kick_age * 18.0) * math.sin(2 * math.pi * (68 - min(kick_age * 80, 28)) * time_value)
        if beat in {1, 3}:
            value += 0.08 * math.exp(-within_beat * 22.0) * deterministic_noise(sample)
        value += 0.018 * math.exp(-within_beat * 35.0) * deterministic_noise(sample + 97)
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
                "64k",
                str(output_path),
            ],
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("ui/assets/song-practice"))
    args = parser.parse_args()
    for track in TRACKS:
        render_track(track, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
