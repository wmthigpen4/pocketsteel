#!/usr/bin/env python3
"""Attach private Chordify MIDI comparisons to a localhost song-test bundle."""

from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROOF = REPO_ROOT / "ui/chord-reader-proof/local-tests/proof.json"
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
ROOT_BY_NAME = {name: index for index, name in enumerate(NOTE_NAMES)}
ROOT_BY_NAME.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})
TEMPLATES = (
    ("7", "major", frozenset({0, 4, 7, 10})),
    ("maj7", "major", frozenset({0, 4, 7, 11})),
    ("m7", "minor", frozenset({0, 3, 7, 10})),
    ("m", "minor", frozenset({0, 3, 7})),
    ("", "major", frozenset({0, 4, 7})),
    ("dim", "other", frozenset({0, 3, 6})),
    ("aug", "other", frozenset({0, 4, 8})),
    ("sus2", "other", frozenset({0, 2, 7})),
    ("sus4", "other", frozenset({0, 5, 7})),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _vlq(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if offset >= len(data):
            raise ValueError("Truncated MIDI variable-length quantity.")
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, offset
    raise ValueError("MIDI variable-length quantity exceeds four bytes.")


def _track_events(data: bytes) -> tuple[list[tuple[int, bool, int]], list[tuple[int, int]]]:
    notes: list[tuple[int, bool, int]] = []
    tempos: list[tuple[int, int]] = []
    offset = 0
    tick = 0
    running_status: int | None = None
    while offset < len(data):
        delta, offset = _vlq(data, offset)
        tick += delta
        if offset >= len(data):
            raise ValueError("Truncated MIDI event.")
        byte = data[offset]
        if byte & 0x80:
            status = byte
            offset += 1
            if status < 0xF0:
                running_status = status
        elif running_status is not None:
            status = running_status
        else:
            raise ValueError("MIDI running status has no preceding channel status.")
        if status == 0xFF:
            running_status = None
            if offset >= len(data):
                raise ValueError("Truncated MIDI meta event.")
            meta_type = data[offset]
            offset += 1
            length, offset = _vlq(data, offset)
            payload = data[offset : offset + length]
            if len(payload) != length:
                raise ValueError("Truncated MIDI meta payload.")
            offset += length
            if meta_type == 0x51 and length == 3:
                tempos.append((tick, int.from_bytes(payload, "big")))
            if meta_type == 0x2F:
                break
            continue
        if status in (0xF0, 0xF7):
            running_status = None
            length, offset = _vlq(data, offset)
            offset += length
            if offset > len(data):
                raise ValueError("Truncated MIDI system-exclusive payload.")
            continue
        kind = status & 0xF0
        length = 1 if kind in (0xC0, 0xD0) else 2
        payload = data[offset : offset + length]
        if len(payload) != length:
            raise ValueError("Truncated MIDI channel event.")
        offset += length
        if kind in (0x80, 0x90):
            note = payload[0]
            is_on = kind == 0x90 and payload[1] > 0
            notes.append((tick, is_on, note))
    return notes, tempos


def _read_midi(path: Path) -> tuple[int, list[list[tuple[int, bool, int]]], list[tuple[int, int]]]:
    data = path.read_bytes()
    if len(data) < 14 or data[:4] != b"MThd":
        raise ValueError(f"{path} is not a Standard MIDI File.")
    header_length = int.from_bytes(data[4:8], "big")
    if header_length < 6 or len(data) < 8 + header_length:
        raise ValueError("Invalid MIDI header length.")
    _format, track_count, division = struct.unpack(">HHH", data[8:14])
    if division & 0x8000:
        raise ValueError("SMPTE-timed MIDI is not supported.")
    offset = 8 + header_length
    tracks: list[list[tuple[int, bool, int]]] = []
    tempos: list[tuple[int, int]] = []
    for _ in range(track_count):
        if data[offset : offset + 4] != b"MTrk" or offset + 8 > len(data):
            raise ValueError("Missing MIDI track chunk.")
        length = int.from_bytes(data[offset + 4 : offset + 8], "big")
        payload = data[offset + 8 : offset + 8 + length]
        if len(payload) != length:
            raise ValueError("Truncated MIDI track chunk.")
        notes, track_tempos = _track_events(payload)
        tracks.append(notes)
        tempos.extend(track_tempos)
        offset += 8 + length
    tempo_by_tick = {0: 500_000}
    tempo_by_tick.update(tempos)
    return division, tracks, sorted(tempo_by_tick.items())


def _tick_converter(division: int, tempos: Sequence[tuple[int, int]]):
    ticks = [item[0] for item in tempos]
    seconds = [0.0]
    for index in range(1, len(tempos)):
        previous_tick, previous_tempo = tempos[index - 1]
        seconds.append(seconds[-1] + (ticks[index] - previous_tick) * previous_tempo / 1_000_000 / division)

    def convert(tick: int) -> float:
        index = bisect_right(ticks, tick) - 1
        return seconds[index] + (tick - ticks[index]) * tempos[index][1] / 1_000_000 / division

    return convert


def _active_states(events: Sequence[tuple[int, bool, int]]) -> list[tuple[int, frozenset[int]]]:
    grouped: dict[int, list[tuple[bool, int]]] = {}
    for tick, is_on, note in events:
        grouped.setdefault(tick, []).append((is_on, note))
    active: set[int] = set()
    states: list[tuple[int, frozenset[int]]] = []
    for tick, changes in sorted(grouped.items()):
        for is_on, note in changes:
            if not is_on:
                active.discard(note)
        for is_on, note in changes:
            if is_on:
                active.add(note)
        states.append((tick, frozenset(active)))
    return states


def _classify_chord(notes: Iterable[int], bass_note: int | None = None) -> dict[str, Any] | None:
    pitch_classes = frozenset(note % 12 for note in notes)
    if len(pitch_classes) < 3:
        return None
    candidates: list[tuple[tuple[int, int, int, int], int, str, str]] = []
    bass_pitch = bass_note % 12 if bass_note is not None else None
    for root in range(12):
        relative = frozenset((pitch - root) % 12 for pitch in pitch_classes)
        for suffix, family, template in TEMPLATES:
            if template <= relative:
                score = (
                    len(relative - template),
                    0 if bass_pitch == root else 1,
                    -len(template),
                    root,
                )
                candidates.append((score, root, suffix, family))
    if not candidates:
        return None
    _score, root, suffix, family = min(candidates)
    product = NOTE_NAMES[root] + ("m" if family == "minor" else "" if family == "major" else suffix)
    display = NOTE_NAMES[root] + suffix
    if bass_pitch is not None and bass_pitch != root:
        display += f"/{NOTE_NAMES[bass_pitch]}"
    return {"label": display, "productLabel": product, "root": NOTE_NAMES[root], "family": family}


def _midi_segments(path: Path) -> tuple[list[dict[str, Any]], float | None]:
    division, tracks, tempos = _read_midi(path)
    note_tracks = [events for events in tracks if any(is_on for _tick, is_on, _note in events)]
    if not note_tracks:
        raise ValueError("Chordify MIDI contains no note-on events.")
    chord_events = max(
        note_tracks,
        key=lambda events: (
            len(events) / max(1, len({tick for tick, is_on, _note in events if is_on})),
            len(events),
        ),
    )
    bass_candidates = [events for events in note_tracks if events is not chord_events]
    bass_events = (
        min(bass_candidates, key=lambda events: sum(note for _tick, on, note in events if on))
        if bass_candidates
        else []
    )
    chord_states = _active_states(chord_events)
    bass_states = _active_states(bass_events)
    bass_ticks = [tick for tick, _notes in bass_states]
    convert = _tick_converter(division, tempos)
    segments: list[dict[str, Any]] = []
    for index, (tick, notes) in enumerate(chord_states[:-1]):
        end_tick = chord_states[index + 1][0]
        if end_tick <= tick:
            continue
        bass_note = None
        bass_index = bisect_right(bass_ticks, tick) - 1
        if bass_index >= 0 and bass_states[bass_index][1]:
            bass_note = min(bass_states[bass_index][1])
        chord = _classify_chord(notes, bass_note)
        if chord is None:
            continue
        segment = {"start": convert(tick), "end": convert(end_tick), **chord}
        if segments and all(segments[-1][key] == segment[key] for key in ("label", "productLabel")):
            segments[-1]["end"] = segment["end"]
        else:
            segments.append(segment)
    bpm = 60_000_000 / tempos[0][1] if tempos else None
    return segments, bpm


def _product(value: str | None) -> tuple[int, str] | None:
    if not value or value in {"N", "N.C."}:
        return None
    match = re.match(r"^([A-G])([#b]?)(.*)$", value)
    if not match:
        return None
    root = ROOT_BY_NAME.get(match.group(1) + match.group(2))
    if root is None:
        return None
    quality = match.group(3).lower()
    return root, "minor" if quality.startswith("m") and not quality.startswith("maj") else "major"


def _compare(
    predicted: Sequence[Mapping[str, Any]],
    reference: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    covered = exact = root_match = 0.0
    mismatches: list[dict[str, Any]] = []
    for ref in reference:
        reference_product = _product(str(ref.get("productLabel") or ref.get("label")))
        if reference_product is None:
            continue
        for ours in predicted:
            start = max(float(ref["start"]), float(ours["start"]))
            end = min(float(ref["end"]), float(ours["end"]))
            if end <= start:
                continue
            seconds = end - start
            ours_product = _product(str(ours.get("productLabel") or ours.get("label")))
            covered += seconds
            if ours_product == reference_product:
                exact += seconds
                root_match += seconds
                continue
            if ours_product is not None and ours_product[0] == reference_product[0]:
                root_match += seconds
            row = {
                "start": start,
                "end": end,
                "seconds": seconds,
                "ourChord": str(ours.get("productLabel") or ours.get("label") or "N.C."),
                "referenceChord": str(ref.get("productLabel") or ref.get("label") or "N.C."),
                "ourConfidence": float(ours.get("confidence", 0.0)),
            }
            if (
                mismatches
                and abs(mismatches[-1]["end"] - start) <= 1e-6
                and mismatches[-1]["ourChord"] == row["ourChord"]
                and mismatches[-1]["referenceChord"] == row["referenceChord"]
            ):
                previous = mismatches[-1]
                total = previous["seconds"] + seconds
                previous["ourConfidence"] = (
                    previous["ourConfidence"] * previous["seconds"] + row["ourConfidence"] * seconds
                ) / total
                previous["end"] = end
                previous["seconds"] = total
            else:
                mismatches.append(row)
    return {
        "coveredSeconds": covered,
        "exactAgreementFraction": exact / covered if covered else 0.0,
        "rootAgreementFraction": root_match / covered if covered else 0.0,
        "reviewWindows": sorted(mismatches, key=lambda row: (-row["seconds"], row["start"]))[:12],
    }


def add_crosschecks(payload: dict[str, Any], midi_by_track: Mapping[str, Path]) -> dict[str, Any]:
    tracks = {str(item["track"]["id"]): item for item in payload["tracks"]}
    missing = sorted(set(midi_by_track) - set(tracks))
    if missing:
        raise ValueError(f"Unknown track IDs: {', '.join(missing)}")
    for track_id, midi_path in midi_by_track.items():
        path = midi_path.expanduser().resolve(strict=True)
        segments, bpm = _midi_segments(path)
        comparison = _compare(tracks[track_id]["prediction"]["segments"], segments)
        tracks[track_id]["crossCheck"] = {
            "provider": "Chordify",
            "sourceKind": "user-authorized premium time-aligned MIDI export",
            "midiSha256": _sha256(path),
            "bpm": bpm,
            "segments": segments,
            **comparison,
            "disclosure": (
                "Agreement compares two automated chord systems after enharmonic and major/minor normalization. "
                "It is not ground-truth accuracy; listed disagreements are prioritized for human review."
            ),
        }
    payload["crossCheckMethodology"] = {
        "title": "What the public record says about Chordify",
        "summary": (
            "Chordify has publicly described separate neural networks for chord and beat recognition. Earlier papers "
            "describe Sonic Annotator/HarmTrace, and a later engineering report describes Kiss FFT features, a "
            "TensorFlow convolutional network, and HMM sequence selection. Public research code and datasets exist, "
            "but the current production model and weights are not publicly exposed."
        ),
        "sources": [
            {"label": "2012 ISMIR system paper", "url": "https://dreixel.net/research/pdf/cctfm.pdf"},
            {
                "label": "2017 Haskell engineering report",
                "url": "https://www.haskell.org/communities/05-2017/html/report.html",
            },
            {
                "label": "Chordify algorithm overview",
                "url": "https://chordify.net/pages/technology-algorithm-explained/",
            },
            {"label": "Chordify public GitHub", "url": "https://github.com/chordify"},
        ],
    }
    return payload


def _midi_argument(value: str) -> tuple[str, Path]:
    track_id, separator, path = value.partition("=")
    if not separator or not track_id or not path:
        raise argparse.ArgumentTypeError("Expected TRACK_ID=/absolute/path.mid")
    return track_id, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof", type=Path, default=DEFAULT_PROOF)
    parser.add_argument("--midi", action="append", type=_midi_argument, required=True)
    args = parser.parse_args()
    proof_path = args.proof.expanduser().resolve(strict=True)
    payload = json.loads(proof_path.read_text(encoding="utf-8"))
    add_crosschecks(payload, dict(args.midi))
    proof_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "proof": str(proof_path),
                "tracks": [
                    {
                        "trackId": item["track"]["id"],
                        "exactAgreementFraction": item["crossCheck"]["exactAgreementFraction"],
                        "rootAgreementFraction": item["crossCheck"]["rootAgreementFraction"],
                        "coveredSeconds": item["crossCheck"]["coveredSeconds"],
                    }
                    for item in payload["tracks"]
                    if "crossCheck" in item
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
