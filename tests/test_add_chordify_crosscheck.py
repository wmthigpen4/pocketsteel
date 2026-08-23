from __future__ import annotations

import struct

from scripts.add_chordify_crosscheck import _compare, _midi_segments, _product


def _vlq(value: int) -> bytes:
    parts = [value & 0x7F]
    value >>= 7
    while value:
        parts.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(parts))


def _track(events: bytes) -> bytes:
    return b"MTrk" + struct.pack(">I", len(events)) + events


def test_midi_parser_recovers_time_aligned_major_and_minor_products(tmp_path) -> None:
    tempo = b"\x00\xff\x51\x03\x07\xa1\x20\x00\xff\x2f\x00"
    chord = bytearray()
    for note in (60, 64, 67):
        chord += b"\x00\x90" + bytes((note, 100))
    chord += _vlq(480) + b"\x80\x3c\x00"
    for note in (64, 67):
        chord += b"\x00\x80" + bytes((note, 0))
    for note in (62, 65, 69):
        chord += b"\x00\x90" + bytes((note, 100))
    chord += _vlq(480) + b"\x80\x3e\x00"
    for note in (65, 69):
        chord += b"\x00\x80" + bytes((note, 0))
    chord += b"\x00\xff\x2f\x00"
    bass = b"\x00\x90\x30\x64" + _vlq(960) + b"\x80\x30\x00\x00\xff\x2f\x00"
    header = b"MThd" + struct.pack(">IHHH", 6, 1, 3, 480)
    path = tmp_path / "reference.mid"
    path.write_bytes(header + _track(tempo) + _track(bytes(chord)) + _track(bass))

    segments, bpm = _midi_segments(path)

    assert bpm == 120
    assert [item["productLabel"] for item in segments] == ["C", "Dm"]
    assert [(item["start"], item["end"]) for item in segments] == [(0.0, 0.5), (0.5, 1.0)]


def test_comparison_normalizes_enharmonics_and_prioritizes_disagreements() -> None:
    predicted = [
        {"start": 0.0, "end": 2.0, "productLabel": "G#", "confidence": 0.9},
        {"start": 2.0, "end": 4.0, "productLabel": "A#m", "confidence": 0.6},
    ]
    reference = [
        {"start": 0.0, "end": 2.0, "productLabel": "Ab"},
        {"start": 2.0, "end": 4.0, "productLabel": "A#"},
    ]

    comparison = _compare(predicted, reference)

    assert _product("Dbmaj7") == (1, "major")
    assert comparison["coveredSeconds"] == 4.0
    assert comparison["exactAgreementFraction"] == 0.5
    assert comparison["rootAgreementFraction"] == 1.0
    assert comparison["reviewWindows"] == [
        {
            "start": 2.0,
            "end": 4.0,
            "seconds": 2.0,
            "ourChord": "A#m",
            "referenceChord": "A#",
            "ourConfidence": 0.6,
        }
    ]
