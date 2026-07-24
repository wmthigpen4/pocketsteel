"""Deterministic exact-input parity audit for Amazing Tablature.

This module uses synthetic musical phrases only.  It proves that supported
structured entry formats normalize to the same pitch/rhythm events and reach
the same arranger behavior; it does not make a held-out accuracy claim.
"""

from __future__ import annotations

import hashlib
import json
import struct
from typing import Any, Mapping, Sequence

from steel_guitar_rag.melody_arranger import (
    arrange_melody_routes,
    parse_melody_inputs,
    resolve_contour,
)
from steel_guitar_rag.melody_import import parse_midi, parse_musicxml


INPUT_MODALITIES = (
    "typed_notes",
    "intervals",
    "musicxml",
    "midi",
    "normalized_events",
)


_FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "id": "g-ascending-scale",
        "key": "G",
        "notes": ("G", "A", "B", "C", "D"),
        "degrees": ("1", "2", "3", "4", "5"),
        "durations": (1.0, 0.5, 0.5, 1.0, 2.0),
        "contour": "ascending",
        "style": "single_note_run",
    },
    {
        "id": "g-descending-scale",
        "key": "G",
        "notes": ("D", "C", "B", "A", "G"),
        "degrees": ("5", "4", "3", "2", "1"),
        "durations": (1.0, 1.0, 0.5, 0.5, 2.0),
        "contour": "descending",
        "style": "lever_driven",
    },
    {
        "id": "g-repeated-pickup",
        "key": "G",
        "notes": ("G", "G", "A", "B"),
        "degrees": ("1", "1", "2", "3"),
        "durations": (0.5, 0.5, 1.0, 2.0),
        "contour": "closest_playable",
        "style": "single_note_run",
    },
    {
        "id": "g-triad-arc",
        "key": "G",
        "notes": ("G", "B", "D", "B", "G"),
        "degrees": ("1", "3", "5", "3", "1"),
        "durations": (1.0, 1.0, 2.0, 1.0, 2.0),
        "contour": "closest_playable",
        "style": "harmonized",
    },
    {
        "id": "c-ascending-scale",
        "key": "C",
        "notes": ("C", "D", "E", "F", "G", "A", "B"),
        "degrees": ("1", "2", "3", "4", "5", "6", "7"),
        "durations": (0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 2.0),
        "contour": "ascending",
        "style": "chord_melody",
    },
    {
        "id": "c-descending-scale",
        "key": "C",
        "notes": ("B", "A", "G", "F", "E", "D", "C"),
        "degrees": ("7", "6", "5", "4", "3", "2", "1"),
        "durations": (1.0, 0.5, 0.5, 1.0, 1.0, 1.0, 2.0),
        "contour": "descending",
        "style": "lever_driven",
    },
    {
        "id": "c-repeated-resolution",
        "key": "C",
        "notes": ("G", "F", "E", "E", "C"),
        "degrees": ("5", "4", "3", "3", "1"),
        "durations": (1.5, 0.5, 1.0, 1.0, 2.0),
        "contour": "closest_playable",
        "style": "harmonized",
    },
    {
        "id": "g-explicit-octave-lift",
        "key": "G",
        "notes": ("G", "B", "D", "G"),
        "degrees": ("1", "3", "5", "1"),
        "durations": (1.0, 1.0, 1.0, 2.0),
        "octaveShifts": (0, 0, 0, 1),
        "contour": "ascending",
        "style": "chord_melody",
    },
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _varlen(value: int) -> bytes:
    buffer = value & 0x7F
    encoded = bytearray((buffer,))
    while value > 0x7F:
        value >>= 7
        buffer = (value & 0x7F) | 0x80
        encoded.insert(0, buffer)
    return bytes(encoded)


def _midi_bytes(
    pitch_values: Sequence[int], durations: Sequence[float], *, key: str
) -> bytes:
    division = 480
    key_fifths = 1 if key == "G" else 0
    track = bytearray((0x00, 0xFF, 0x59, 0x02, key_fifths & 0xFF, 0x00))
    for pitch, duration in zip(pitch_values, durations, strict=True):
        ticks = max(1, round(float(duration) * division))
        track.extend((0x00, 0x90, int(pitch), 0x40))
        track.extend(_varlen(ticks))
        track.extend((0x80, int(pitch), 0x00))
    track.extend((0x00, 0xFF, 0x2F, 0x00))
    return (
        b"MThd"
        + struct.pack(">IHHH", 6, 0, 1, division)
        + b"MTrk"
        + struct.pack(">I", len(track))
        + bytes(track)
    )


def _pitch_parts(value: int) -> tuple[str, int, int]:
    names = (
        ("C", 0),
        ("C", 1),
        ("D", 0),
        ("D", 1),
        ("E", 0),
        ("F", 0),
        ("F", 1),
        ("G", 0),
        ("G", 1),
        ("A", 0),
        ("A", 1),
        ("B", 0),
    )
    step, alter = names[value % 12]
    return step, alter, value // 12 - 1


def _musicxml_bytes(
    pitch_values: Sequence[int], durations: Sequence[float], *, key: str
) -> bytes:
    divisions = 4
    measures: dict[int, list[str]] = {}
    for pitch, duration, timing in zip(
        pitch_values, durations, _event_timing(durations), strict=True
    ):
        step, alter, octave = _pitch_parts(int(pitch))
        alter_node = f"<alter>{alter}</alter>" if alter else ""
        measures.setdefault(int(timing["measure"]), []).append(
            "<note><pitch>"
            f"<step>{step}</step>{alter_node}<octave>{octave}</octave>"
            "</pitch>"
            f"<duration>{max(1, round(float(duration) * divisions))}</duration>"
            "</note>"
        )
    fifths = 1 if key == "G" else 0
    measure_nodes = []
    for measure, notes in sorted(measures.items()):
        attributes = (
            "<attributes>"
            f"<divisions>{divisions}</divisions><key><fifths>{fifths}</fifths></key>"
            "<time><beats>4</beats><beat-type>4</beat-type></time></attributes>"
            if measure == 1
            else ""
        )
        measure_nodes.append(
            f"<measure number='{measure}'>{attributes}{''.join(notes)}</measure>"
        )
    return (
        "<score-partwise><part-list><score-part id='P1'>"
        "<part-name>Melody</part-name></score-part></part-list>"
        "<part id='P1'>"
        + "".join(measure_nodes)
        + "</part></score-partwise>"
    ).encode("utf-8")


def _event_timing(durations: Sequence[float]) -> list[dict[str, float | int]]:
    start = 0.0
    result: list[dict[str, float | int]] = []
    for duration in durations:
        result.append(
            {
                "measure": int(start // 4) + 1,
                "beat": round((start % 4) + 1, 3),
            }
        )
        start += float(duration)
    return result


def _arrangement_signature(
    raw_events: Sequence[Any],
    *,
    fixture_id: str,
    key: str,
    contour: str,
    style: str,
) -> dict[str, Any]:
    routes, resolved = arrange_melody_routes(
        raw_events,
        key=key,
        contour_mode=contour,
        texture="both",
        route_id_prefix=f"parity-{fixture_id}",
        title="Structured input parity",
        style_family=style,
    )
    return {
        "resolved": [
            {
                "pitchValue": int(event["pitchValue"]),
                "durationBeats": float(event["durationBeats"]),
            }
            for event in resolved
        ],
        "routes": [
            {
                "harmonyType": route["harmonyType"],
                "events": [
                    {
                        "pitchValue": event["pitchValue"],
                        "durationBeats": event.get("durationBeats"),
                        "notes": event["notes"],
                        "performanceControls": event["performanceControls"],
                        "patternFamily": event["patternFamily"],
                        "canonicalGrip": event["canonicalGrip"],
                    }
                    for event in route["tabExample"]["events"]
                ],
            }
            for route in routes
        ],
    }


def structured_input_parity_report() -> dict[str, Any]:
    """Return a content-free receipt for exact structured-input equivalence."""

    fixture_results: list[dict[str, Any]] = []
    total_events = 0
    for fixture in _FIXTURES:
        notes = list(fixture["notes"])
        degrees = list(fixture["degrees"])
        durations = [float(value) for value in fixture["durations"]]
        octave_shifts = list(fixture.get("octaveShifts") or (0,) * len(notes))
        timings = _event_timing(durations)
        typed = [
            {
                "note": note,
                "durationBeats": duration,
                "octaveShift": octave_shift,
                **timing,
            }
            for note, duration, octave_shift, timing in zip(
                notes, durations, octave_shifts, timings, strict=True
            )
        ]
        intervals = [
            {
                "degree": degree,
                "durationBeats": duration,
                "octaveShift": octave_shift,
                **timing,
            }
            for degree, duration, octave_shift, timing in zip(
                degrees, durations, octave_shifts, timings, strict=True
            )
        ]
        typed_inputs = parse_melody_inputs(typed, str(fixture["key"]))
        interval_inputs = parse_melody_inputs(intervals, str(fixture["key"]))
        pitch_values = resolve_contour(typed_inputs, str(fixture["contour"]))
        interval_values = resolve_contour(
            interval_inputs, str(fixture["contour"])
        )
        normalized = [
            {
                "pitchValue": pitch,
                "durationBeats": duration,
                **timing,
            }
            for pitch, duration, timing in zip(
                pitch_values, durations, timings, strict=True
            )
        ]
        musicxml = parse_musicxml(
            _musicxml_bytes(pitch_values, durations, key=str(fixture["key"]))
        )["score"]["melody"]
        midi = parse_midi(
            _midi_bytes(pitch_values, durations, key=str(fixture["key"]))
        )["score"]["melody"]
        modality_events: dict[str, Sequence[Any]] = {
            "typed_notes": typed,
            "intervals": intervals,
            "musicxml": musicxml,
            "midi": midi,
            "normalized_events": normalized,
        }
        signatures = {
            modality: _arrangement_signature(
                raw_events,
                fixture_id=str(fixture["id"]),
                key=str(fixture["key"]),
                contour=str(fixture["contour"]),
                style=str(fixture["style"]),
            )
            for modality, raw_events in modality_events.items()
        }
        signature_digests = {
            modality: _digest(signature)
            for modality, signature in signatures.items()
        }
        pitch_parity = interval_values == pitch_values
        arrangement_parity = len(set(signature_digests.values())) == 1
        fixture_results.append(
            {
                "fixtureId": fixture["id"],
                "key": fixture["key"],
                "styleFamily": fixture["style"],
                "eventCount": len(pitch_values),
                "pitchParity": pitch_parity,
                "arrangementParity": arrangement_parity,
                "signatureDigest": (
                    next(iter(signature_digests.values()))
                    if arrangement_parity
                    else _digest(signature_digests)
                ),
            }
        )
        total_events += len(pitch_values)
    parity_passed = all(
        result["pitchParity"] and result["arrangementParity"]
        for result in fixture_results
    )
    core = {
        "schemaVersion": "amazing-tablature-structured-input-parity-v1",
        "modalities": list(INPUT_MODALITIES),
        "fixtureCount": len(fixture_results),
        "eventCountPerModality": total_events,
        "totalAdapterEvents": total_events * len(INPUT_MODALITIES),
        "fixtures": fixture_results,
        "parityPassed": parity_passed,
        "accuracyClaim": "none_adapter_equivalence_only",
        "validationAccessed": False,
        "sealedTestAccessed": False,
    }
    return {**core, "reportDigest": _digest(core)}


__all__ = ["INPUT_MODALITIES", "structured_input_parity_report"]
