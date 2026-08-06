"""Stable value objects and constants for deterministic E9 fretboard services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from steel_guitar_rag.user_copedent import USER_E9_COPEDENT, open_strings_dict

E9_OPEN_STRINGS: dict[int, str] = open_strings_dict(USER_E9_COPEDENT)

FRETBOARD_PAYLOAD_TYPE = "e9-fretboard-diagram"

CANONICAL_PEDAL_LABELS: tuple[str, ...] = ("A", "B", "C")

CANONICAL_LEVER_LABELS: tuple[str, ...] = ("F", "E", "G+", "G-", "D-", "D--", "V")

DEFAULT_PEDAL_LEVER_LABELS: tuple[str, ...] = CANONICAL_PEDAL_LABELS + CANONICAL_LEVER_LABELS

POSITION_COLORS: tuple[str, ...] = ("primary", "secondary", "alternate", "reference", "warning")

COMMON_E9_VISUAL_GRIPS: tuple[tuple[int, ...], ...] = (
    (3, 4, 5),
    (4, 5, 6),
    (5, 6, 8),
    (5, 7, 8),
    (6, 8, 10),
)

E_LOWER_578_GRIP: tuple[int, ...] = (5, 7, 8)

E_LOWER_MAJOR_GRIPS: tuple[tuple[int, ...], ...] = (
    (5, 7, 8),
    (7, 8, 10),
    (4, 5, 7),
    (1, 4, 5),
)

E_LOWER_DOMINANT_GRIPS: tuple[tuple[int, ...], ...] = (
    (3, 4, 5),
    (4, 5, 6),
    (5, 6, 8),
    (6, 8, 10),
)

OPEN_STRING_ABSOLUTE_PITCHES: dict[int, int] = {
    1: 66,
    2: 63,
    3: 68,
    4: 64,
    5: 59,
    6: 56,
    7: 54,
    8: 52,
    9: 50,
    10: 47,
}

FretboardIntent = Literal["major_positions", "minor_positions", "minor_grips", "i_iv_v", "common_grips"]


@dataclass(frozen=True)
class MajorChordLocationRequest:
    requested_root: str
    normalized_key: str

    @property
    def is_enharmonic(self) -> bool:
        return self.requested_root != self.normalized_key


def display_major_key_for_request(request: MajorChordLocationRequest) -> str:
    """Choose the user-facing root spelling for a deterministic major request."""
    if request.requested_root.endswith("b") and request.requested_root not in {"Cb", "Fb"}:
        return request.requested_root
    return request.normalized_key


def display_minor_key_for_request(request: "MinorChordLocationRequest") -> str:
    """Choose the user-facing spelling for deterministic minor requests."""
    if request.requested_root.endswith("b") and request.requested_root not in {"Cb", "Fb"}:
        return request.requested_root
    return request.normalized_key


@dataclass(frozen=True)
class UnsupportedChordLocationRequest:
    requested_root: str
    normalized_key: str
    quality: str


@dataclass(frozen=True)
class ELower578Request:
    fret: int


@dataclass(frozen=True)
class ELowerGripRequest:
    fret: int
    strings: tuple[int, ...]


@dataclass(frozen=True)
class FretStringPedalRequest:
    fret: int
    strings: tuple[int, ...]
    pedals: tuple[str, ...]
    levers: tuple[str, ...]

    @property
    def controls(self) -> tuple[str, ...]:
        return self.pedals + self.levers


@dataclass(frozen=True)
class FunctionalPocketRequest:
    key: str
    function: str
    target_root: str


@dataclass(frozen=True)
class FunctionChordRequest:
    key: str
    requested_function: str
    degree: int
    root: str
    quality: str


@dataclass(frozen=True)
class MinorChordLocationRequest:
    requested_root: str
    normalized_key: str


@dataclass(frozen=True)
class MultiChordLocationRequest:
    root: str
    qualities: tuple[str, ...]


@dataclass(frozen=True)
class SpecificMajorGripRequest:
    requested_root: str
    normalized_key: str
    strings: tuple[int, ...]


@dataclass(frozen=True)
class ChordConceptRequest:
    requested_root: str
    normalized_key: str
    quality: str


@dataclass(frozen=True)
class RootlessChordQualityRequest:
    quality: str
    label: str
    is_function: bool = False


@dataclass(frozen=True)
class ChordSymbolGuardrailRequest:
    symbol: str
    answer: str


NOTE_TO_SEMITONE: dict[str, int] = {
    "C": 0,
    "B#": 0,
    "DBB": 0,
    "C#": 1,
    "B##": 1,
    "DB": 1,
    "D": 2,
    "C##": 2,
    "EBB": 2,
    "D#": 3,
    "FBB": 3,
    "EB": 3,
    "E": 4,
    "D##": 4,
    "FB": 4,
    "F": 5,
    "E#": 5,
    "GBB": 5,
    "F#": 6,
    "E##": 6,
    "GB": 6,
    "G": 7,
    "F##": 7,
    "ABB": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "G##": 9,
    "BBB": 9,
    "A#": 10,
    "CBB": 10,
    "BB": 10,
    "B": 11,
    "A##": 11,
    "CB": 11,
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

CHORD_ROOT_RE = r"[a-g](?:##|bb|#|b)?"

OPEN_MAJOR_ROOT = NOTE_TO_SEMITONE["E"]
AF_MAJOR_OFFSET = 3
AB_MAJOR_OFFSET = 7

INTERVAL_NAMES: dict[int, str] = {
    0: "1",
    1: "b2",
    2: "2/9",
    3: "b3",
    4: "3",
    5: "4/11",
    6: "b5/#11",
    7: "5",
    8: "#5/b13",
    9: "6/13",
    10: "b7",
    11: "7",
}

CHORD_INTERVALS: dict[str, tuple[str, ...]] = {
    "major": ("1", "3", "5"),
    "major7": ("1", "3", "5", "7"),
    "minor": ("1", "b3", "5"),
    "diminished": ("1", "b3", "b5/#11"),
    "dominant7": ("1", "3", "5", "b7"),
    "dominant9": ("1", "3", "5", "b7", "2/9"),
    "minor7": ("1", "b3", "5", "b7"),
}

CHORD_ADDED_INTERVALS: dict[str, tuple[str, ...]] = {
    "major": ("2/9", "6/13"),
    "major7": ("2/9", "6/13"),
    "minor": ("2/9", "4/11", "b7"),
    "diminished": (),
    "dominant7": ("2/9", "6/13"),
    "dominant9": ("6/13",),
    "minor7": ("2/9", "4/11"),
}

CHORD_ALIASES: dict[str, str] = {
    "major": "major",
    "major 7": "major7",
    "major7": "major7",
    "maj7": "major7",
    "minor": "minor",
    "m": "minor",
    "dominant": "dominant7",
    "dominant 7": "dominant7",
    "dominant7": "dominant7",
    "dom": "dominant7",
    "dom7": "dominant7",
    "7": "dominant7",
    "dominant 9": "dominant9",
    "dominant9": "dominant9",
    "9": "dominant9",
    "minor 7": "minor7",
    "minor7": "minor7",
    "m7": "minor7",
    "dim": "diminished",
    "diminished": "diminished",
}

ROOTLESS_CHORD_QUALITY_ALIASES: dict[str, RootlessChordQualityRequest] = {
    "sus": RootlessChordQualityRequest("sus", "suspended"),
    "sus2": RootlessChordQualityRequest("sus2", "sus2"),
    "sus4": RootlessChordQualityRequest("sus4", "sus4"),
    "suspended": RootlessChordQualityRequest("sus", "suspended"),
    "suspended 2": RootlessChordQualityRequest("sus2", "sus2"),
    "suspended 4": RootlessChordQualityRequest("sus4", "sus4"),
    "dominant": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "dom": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "dom7": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "dom 7": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "dominant 7": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "dominant seventh": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "7th": RootlessChordQualityRequest("dominant7", "dominant 7"),
    "v7": RootlessChordQualityRequest("dominant7", "V7", True),
    "5 dominant 7": RootlessChordQualityRequest("dominant7", "5 dominant 7", True),
    "5 dom 7": RootlessChordQualityRequest("dominant7", "5 dominant 7", True),
    "5^7": RootlessChordQualityRequest("dominant7", "5^7", True),
    "five dominant seven": RootlessChordQualityRequest("dominant7", "5 dominant 7", True),
    "dim": RootlessChordQualityRequest("diminished", "diminished"),
    "diminished": RootlessChordQualityRequest("diminished", "diminished"),
    "dim7": RootlessChordQualityRequest("diminished7", "diminished 7"),
    "dim 7": RootlessChordQualityRequest("diminished7", "diminished 7"),
    "diminished 7": RootlessChordQualityRequest("diminished7", "diminished 7"),
    "aug": RootlessChordQualityRequest("augmented", "augmented"),
    "augmented": RootlessChordQualityRequest("augmented", "augmented"),
    "+": RootlessChordQualityRequest("augmented", "augmented"),
}

MAJOR_SCALE_INTERVALS: dict[int, int] = {
    1: 0,
    2: 2,
    3: 4,
    4: 5,
    5: 7,
    6: 9,
    7: 11,
}

FUNCTION_QUALITIES: dict[int, str] = {
    1: "major",
    2: "minor",
    3: "minor",
    4: "major",
    5: "major",
    6: "minor",
    7: "diminished",
}

ROMAN_FUNCTIONS: dict[str, int] = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
    "v": 5,
    "vi": 6,
    "vii": 7,
    "vii°": 7,
    "viio": 7,
    "vii0": 7,
}
