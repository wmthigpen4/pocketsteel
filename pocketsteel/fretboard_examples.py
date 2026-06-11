"""Deterministic E9 fretboard seed data for visualization MVPs.

This is intentionally a small known-position library, not a full chord engine.
It returns structured highlight payloads that the frontend fretboard component
can render without needing RAG, embeddings, or live source lookup.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


E9_OPEN_STRINGS: dict[int, str] = {
    1: "F#",
    2: "D#",
    3: "G#",
    4: "E",
    5: "B",
    6: "G#",
    7: "F#",
    8: "E",
    9: "D",
    10: "B",
}

FRETBOARD_PAYLOAD_TYPE = "e9-fretboard-diagram"

CANONICAL_PEDAL_LABELS: tuple[str, ...] = ("A", "B", "C")

CANONICAL_LEVER_LABELS: tuple[str, ...] = ("F", "E", "G+", "G-", "D-", "D--", "V")

DEFAULT_PEDAL_LEVER_LABELS: tuple[str, ...] = CANONICAL_PEDAL_LABELS + CANONICAL_LEVER_LABELS

POSITION_COLORS: tuple[str, ...] = ("primary", "secondary", "alternate", "reference", "warning")

COMMON_E9_VISUAL_GRIPS: tuple[tuple[int, ...], ...] = (
    (4, 5, 6),
    (3, 4, 5),
    (5, 6, 8),
    (6, 8, 10),
)

FretboardIntent = Literal["major_positions", "minor_grips", "i_iv_v", "common_grips"]

NOTE_TO_SEMITONE: dict[str, int] = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

CANONICAL_NOTES: dict[int, str] = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}

OPEN_MAJOR_ROOT = NOTE_TO_SEMITONE["E"]
AB_MAJOR_ROOT = NOTE_TO_SEMITONE["A"]
AF_MAJOR_ROOT = NOTE_TO_SEMITONE["C#"]


@dataclass(frozen=True)
class FretboardPosition:
    id: str
    label: str
    fret: int
    strings: tuple[int, ...]
    grip: str
    pedals: tuple[str, ...] = ()
    levers: tuple[str, ...] = ()
    color: str = "primary"
    role: str = ""
    notes: dict[str, str] | None = None
    intervals: dict[str, str] | None = None
    explanation: str = ""

    def to_position_payload(self) -> dict:
        payload: dict = {
            "id": self.id,
            "label": self.label,
            "fret": self.fret,
            "strings": list(self.strings),
            "grip": self.grip,
            "pedals": list(self.pedals),
            "levers": list(self.levers),
            "color": self.color,
            "role": self.role,
        }
        if self.notes:
            payload["notes"] = dict(self.notes)
        if self.intervals:
            payload["intervals"] = dict(self.intervals)
        if self.explanation:
            payload["explanation"] = self.explanation
        return payload

    def to_highlight_payload(self) -> dict:
        """Return the legacy UI highlight shape while positions migrate."""
        return {
            "id": self.id,
            "label": self.label,
            "fret": self.fret,
            "strings": list(self.strings),
            "pedals": list(self.pedals),
            "levers": list(self.levers),
            "role": self.role,
        }


@dataclass(frozen=True)
class FretboardVisualizationPayload:
    title: str
    subtitle: str
    key: str
    positions: tuple[FretboardPosition, ...]

    def to_payload(self) -> dict:
        positions = [position.to_position_payload() for position in self.positions]
        payload = {
            "type": FRETBOARD_PAYLOAD_TYPE,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.subtitle,
            "tuning": "E9",
            "copedent": {
                "id": "mvp-e9-standard",
                "label": "MVP standard 10-string E9",
                "status": "assumed",
            },
            "key": self.key,
            "strings": {
                "count": 10,
                "labels": {str(string): note for string, note in E9_OPEN_STRINGS.items()},
            },
            "positions": positions,
            "highlights": [position.to_highlight_payload() for position in self.positions],
            "legend": [
                {
                    "id": "primary",
                    "label": "Open/no-pedal position",
                    "color": "primary",
                    "description": "A straight-bar position without pedals or levers.",
                },
                {
                    "id": "secondary",
                    "label": "A+F position",
                    "color": "secondary",
                    "description": "A pedal plus F lever.",
                },
                {
                    "id": "alternate",
                    "label": "A+B position",
                    "color": "alternate",
                    "description": "A and B pedals together.",
                },
            ],
            "notes": [
                "String 1 is the top/highest string; string 10 is the bottom/lowest string.",
                "Fret markers and geometry are supplied by the UI, not by this payload.",
            ],
            "warnings": ["This diagram assumes standard 10-string E9."],
            "sourceContext": [
                {
                    "kind": "rule",
                    "label": "MVP deterministic E9 known-position rule",
                    "sourceId": "pocketsteel.fretboard_examples",
                }
            ],
        }
        validate_fretboard_payload(payload)
        return payload


def grip_label(strings: tuple[int, ...]) -> str:
    return "-".join(str(string) for string in strings)


def validate_fretboard_payload(payload: dict) -> None:
    """Validate the MVP contract subset emitted by this deterministic module."""
    if payload.get("type") != FRETBOARD_PAYLOAD_TYPE:
        raise ValueError("Unsupported fretboard payload type")
    if payload.get("tuning") != "E9":
        raise ValueError("Unsupported fretboard tuning")
    if payload.get("strings", {}).get("count") != 10:
        raise ValueError("Unsupported fretboard string count")
    positions = payload.get("positions")
    if not isinstance(positions, list) or not positions:
        raise ValueError("Fretboard payload must include at least one position")

    ids: set[str] = set()
    for position in positions:
        _validate_no_geometry_fields(position)
        position_id = position.get("id")
        if not isinstance(position_id, str) or not position_id:
            raise ValueError("Fretboard position is missing a stable id")
        if position_id in ids:
            raise ValueError(f"Duplicate fretboard position id: {position_id}")
        ids.add(position_id)

        fret = position.get("fret")
        if not isinstance(fret, int) or not 0 <= fret <= 24:
            raise ValueError(f"Fretboard position {position_id} has invalid fret")

        strings = position.get("strings")
        if not isinstance(strings, list) or not strings:
            raise ValueError(f"Fretboard position {position_id} has invalid strings")
        if len(set(strings)) != len(strings) or any(not isinstance(string, int) or not 1 <= string <= 10 for string in strings):
            raise ValueError(f"Fretboard position {position_id} has out-of-range strings")

        expected_grip = "-".join(str(string) for string in strings)
        if position.get("grip") != expected_grip:
            raise ValueError(f"Fretboard position {position_id} has invalid grip")

        if any(pedal not in CANONICAL_PEDAL_LABELS for pedal in position.get("pedals", [])):
            raise ValueError(f"Fretboard position {position_id} has unknown pedal label")
        if any(lever not in CANONICAL_LEVER_LABELS for lever in position.get("levers", [])):
            raise ValueError(f"Fretboard position {position_id} has unknown lever label")
        if position.get("color") not in POSITION_COLORS:
            raise ValueError(f"Fretboard position {position_id} has unknown color role")

        for note_key in position.get("notes", {}):
            if int(note_key) not in strings:
                raise ValueError(f"Fretboard position {position_id} has note outside strings")
        for interval_key in position.get("intervals", {}):
            if int(interval_key) not in strings:
                raise ValueError(f"Fretboard position {position_id} has interval outside strings")

    _validate_no_geometry_fields(payload)


def _validate_no_geometry_fields(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            if normalized_key in {"x", "y", "cx", "cy"} or "coordinate" in normalized_key:
                raise ValueError(f"Raw geometry field is not allowed in fretboard payload: {key}")
            _validate_no_geometry_fields(child)
    elif isinstance(value, list):
        for item in value:
            _validate_no_geometry_fields(item)


def major_triad_annotations(key: str, *, inversion: str) -> tuple[dict[str, str], dict[str, str]]:
    third = transpose(key, 4)
    fifth = transpose(key, 7)
    if inversion == "open":
        return (
            {"4": key, "5": fifth, "6": third},
            {"4": "1", "5": "5", "6": "3"},
        )
    return (
        {"4": third, "5": key, "6": fifth},
        {"4": "3", "5": "1", "6": "5"},
    )


def get_e9_major_chord_positions(key: str = "G") -> list[dict]:
    """Return deterministic contract positions for a major chord key."""
    return major_positions(key).to_payload()["positions"]


def build_e9_major_chord_fretboard(key: str = "G") -> dict:
    """Build the full contract payload for known E9 major chord positions."""
    return major_positions(key).to_payload()


def get_fretboard_examples(intent: str, key: str = "G") -> dict:
    """Return known E9 fretboard highlights for a small MVP intent set."""
    normalized_intent = normalize_intent(intent)
    normalized_key = normalize_key(key)
    if normalized_intent == "major_positions":
        return major_positions(normalized_key).to_payload()
    if normalized_intent == "minor_grips":
        return minor_grips(normalized_key).to_payload()
    if normalized_intent == "i_iv_v":
        return i_iv_v_examples(normalized_key).to_payload()
    if normalized_intent == "common_grips":
        return common_grip_examples(normalized_key).to_payload()
    raise ValueError(f"Unsupported fretboard example intent: {intent}")


def fretboard_payload_for_question(question: str) -> dict | None:
    """Return MVP fretboard visualization data for a narrow curated question set."""
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    if q in {
        "where can i play a g chord",
        "show me places to play a g major chord",
        "where are g major positions on e9",
        "show me g major with a+b",
        "show me g major with a+f",
    }:
        return get_fretboard_examples("major_positions", "G")
    if q == "show me a 1-4-5 in g":
        return get_fretboard_examples("i_iv_v", "G")
    if q == "show me common grips for g":
        return get_fretboard_examples("common_grips", "G")
    return None


def normalize_intent(intent: str) -> FretboardIntent:
    normalized = (intent or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "major": "major_positions",
        "major_chord": "major_positions",
        "major_chords": "major_positions",
        "positions": "major_positions",
        "minor": "minor_grips",
        "minor_examples": "minor_grips",
        "145": "i_iv_v",
        "1_4_5": "i_iv_v",
        "i-iv-v": "i_iv_v",
        "i_iv_v_examples": "i_iv_v",
        "grips": "common_grips",
        "common_e9_grips": "common_grips",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"major_positions", "minor_grips", "i_iv_v", "common_grips"}:
        raise ValueError(f"Unsupported fretboard example intent: {intent}")
    return normalized  # type: ignore[return-value]


def normalize_key(key: str) -> str:
    normalized = (key or "G").strip().upper().replace("♯", "#").replace("♭", "B")
    if normalized not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported key: {key}")
    return CANONICAL_NOTES[NOTE_TO_SEMITONE[normalized]]


def major_positions(key: str) -> FretboardVisualizationPayload:
    key = normalize_key(key)
    open_notes, open_intervals = major_triad_annotations(key, inversion="open")
    pedals_notes, pedals_intervals = major_triad_annotations(key, inversion="pedals")
    positions = (
        FretboardPosition(
            id=f"{slug(key)}-open-{open_major_fret(key)}",
            label=f"{key} major",
            fret=open_major_fret(key),
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            color="primary",
            role="Open position",
            notes=open_notes,
            intervals=open_intervals,
            explanation=f"No-pedal fret {open_major_fret(key)} gives a {key} major grip on strings 4-5-6.",
        ),
        FretboardPosition(
            id=f"{slug(key)}-af-{af_major_fret(key)}",
            label=f"{key} major",
            fret=af_major_fret(key),
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            pedals=("A",),
            levers=("F",),
            color="secondary",
            role="A+F position",
            notes=pedals_notes,
            intervals=pedals_intervals,
            explanation=f"A+F at fret {af_major_fret(key)} gives another {key} major position on strings 4-5-6.",
        ),
        FretboardPosition(
            id=f"{slug(key)}-ab-{ab_major_fret(key)}",
            label=f"{key} major",
            fret=ab_major_fret(key),
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            pedals=("A", "B"),
            color="alternate",
            role="A+B position",
            notes=pedals_notes,
            intervals=pedals_intervals,
            explanation=f"A+B at fret {ab_major_fret(key)} gives another {key} major position on strings 4-5-6.",
        ),
    )
    return FretboardVisualizationPayload(
        title=f"{key} major positions on E9",
        subtitle=f"Common places to find {key} major.",
        key=key,
        positions=positions,
    )


def minor_grips(key: str) -> FretboardVisualizationPayload:
    key = normalize_key(key)
    relative_minor = CANONICAL_NOTES[(NOTE_TO_SEMITONE[key] + 9) % 12]
    open_fret = open_major_fret(key)
    positions = (
        FretboardPosition(
            id=f"{slug(relative_minor)}m-relative-minor-{open_fret}",
            label=f"{relative_minor} minor",
            fret=open_fret,
            strings=(5, 6, 8),
            grip=grip_label((5, 6, 8)),
            color="primary",
            role=f"Relative minor grip from {key} open position",
        ),
        FretboardPosition(
            id=f"{slug(relative_minor)}m-e-lower-{open_fret}",
            label=f"{relative_minor} minor color",
            fret=open_fret,
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            levers=("E",),
            color="secondary",
            role="E-lower minor-family color",
        ),
    )
    return FretboardVisualizationPayload(
        title=f"{relative_minor} minor examples near {key} on E9",
        subtitle="A few stable minor-family grips to visualize before adding more copedent detail.",
        key=key,
        positions=positions,
    )


def i_iv_v_examples(key: str) -> FretboardVisualizationPayload:
    key = normalize_key(key)
    four = transpose(key, 5)
    five = transpose(key, 7)
    positions = (
        FretboardPosition(
            id=f"{slug(key)}-i-open-{open_major_fret(key)}",
            label=f"{key} major",
            fret=open_major_fret(key),
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            color="primary",
            role="I chord, open position",
        ),
        FretboardPosition(
            id=f"{slug(four)}-iv-ab-{open_major_fret(key)}",
            label=f"{four} major",
            fret=open_major_fret(key),
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            pedals=("A", "B"),
            color="secondary",
            role="IV chord, A+B at the I fret",
        ),
        FretboardPosition(
            id=f"{slug(five)}-v-ab-{open_major_fret(key) + 2}",
            label=f"{five} major",
            fret=open_major_fret(key) + 2,
            strings=(4, 5, 6),
            grip=grip_label((4, 5, 6)),
            pedals=("A", "B"),
            color="alternate",
            role="V chord, A+B two frets above I",
        ),
    )
    return FretboardVisualizationPayload(
        title=f"I-IV-V in {key} on E9",
        subtitle=f"A compact I-IV-V path for {key} using open and A+B positions.",
        key=key,
        positions=positions,
    )


def common_grip_examples(key: str) -> FretboardVisualizationPayload:
    key = normalize_key(key)
    fret = open_major_fret(key)
    positions = tuple(
        FretboardPosition(
            id=f"{slug(key)}-grip-{grip_label(grip)}-{fret}",
            label=f"{key} major grip {grip_label(grip)}",
            fret=fret,
            strings=grip,
            grip=grip_label(grip),
            color="reference",
            role="Common grip",
        )
        for grip in COMMON_E9_VISUAL_GRIPS
    )
    return FretboardVisualizationPayload(
        title=f"Common {key} major grips on E9",
        subtitle=f"Stable grips at the {key} open-position fret.",
        key=key,
        positions=positions,
    )


def open_major_fret(key: str) -> int:
    return fret_for_root(key, OPEN_MAJOR_ROOT)


def ab_major_fret(key: str) -> int:
    return fret_for_root(key, AB_MAJOR_ROOT)


def af_major_fret(key: str) -> int:
    return fret_for_root(key, AF_MAJOR_ROOT)


def fret_for_root(key: str, root_at_zero: int) -> int:
    return (NOTE_TO_SEMITONE[normalize_key(key)] - root_at_zero) % 12


def transpose(key: str, semitones: int) -> str:
    return CANONICAL_NOTES[(NOTE_TO_SEMITONE[normalize_key(key)] + semitones) % 12]


def slug(key: str) -> str:
    return normalize_key(key).lower().replace("#", "sharp")
