"""Canonical rich labels and conservative Play Along chord simplification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re


SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
PITCH_CLASS = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}

NO_CHORD = {"", "n", "nc", "n.c", "n.c.", "no chord", "no_chord"}
ROOT_RE = re.compile(r"^([A-Ga-g])([#b]?)(.*)$")

QUALITY_ALIASES = {
    "": "maj",
    "major": "maj",
    "maj": "maj",
    "m": "min",
    "minor": "min",
    "min": "min",
    "-": "min",
    "dom7": "7",
    "dominant7": "7",
    "min7": "min7",
    "m7": "min7",
    "-7": "min7",
    "major7": "maj7",
    "ma7": "maj7",
    "M7": "maj7",
    "minor6": "min6",
    "m6": "min6",
    "minor9": "min9",
    "m9": "min9",
    "major9": "maj9",
    "ma9": "maj9",
    "dominant9": "9",
    "dom9": "9",
    "dominant11": "11",
    "dom11": "11",
    "dominant13": "13",
    "dom13": "13",
    "diminished": "dim",
    "diminished7": "dim7",
    "augmented": "aug",
    "+": "aug",
    "suspended2": "sus2",
    "suspended4": "sus4",
    "sus": "sus4",
}

MAJOR_FAMILY = {"maj", "maj6", "6", "maj7", "maj9", "add9"}
MINOR_FAMILY = {"min", "min6", "min9", "min11"}
MINOR_SEVENTH_FAMILY = {"min7", "min13"}
DOMINANT_FAMILY = {"7", "9", "11", "13", "7b9", "7#9", "7b5", "7#5"}
UNSUPPORTED_FAMILY = {"dim", "dim7", "hdim7", "aug", "sus2", "sus4", "5"}


@dataclass(frozen=True)
class ChordLabel:
    detailed_symbol: str
    product_symbol: str
    root: str | None
    quality: str
    bass: str | None
    simplified_from: str | None
    needs_attention: bool

    def to_dict(self) -> dict[str, str | bool | None]:
        return asdict(self)


def _note_name(letter: str, accidental: str) -> str:
    return f"{letter.upper()}{accidental}"


def _normalize_quality(raw: str) -> str:
    value = raw.strip()
    if value.startswith(":"):
        value = value[1:]
    value = value.replace("(", "").replace(")", "").replace(" ", "")
    if value in QUALITY_ALIASES:
        return QUALITY_ALIASES[value]
    lowered = value.lower()
    return QUALITY_ALIASES.get(lowered, lowered or "maj")


def normalize_chord(symbol: str | None) -> ChordLabel:
    """Normalize common chord spellings while retaining unsupported detail."""

    raw = str(symbol or "").strip()
    if raw.lower() in NO_CHORD:
        return ChordLabel("N", "N.C.", None, "none", None, None, False)
    if raw.lower() == "x":
        return ChordLabel("X", "N.C.", None, "unknown", None, "X", True)

    chord_part, slash, bass_part = raw.partition("/")
    match = ROOT_RE.match(chord_part.strip())
    if not match:
        raise ValueError(f"Unsupported chord root in {raw!r}.")
    root = _note_name(match.group(1), match.group(2))
    if root not in PITCH_CLASS:
        raise ValueError(f"Unsupported chord root {root!r}.")
    quality = _normalize_quality(match.group(3))

    bass = None
    if slash:
        bass_match = ROOT_RE.match(bass_part.strip())
        if not bass_match or bass_match.group(3):
            raise ValueError(f"Unsupported slash bass in {raw!r}.")
        bass = _note_name(bass_match.group(1), bass_match.group(2))
        if bass not in PITCH_CLASS:
            raise ValueError(f"Unsupported slash bass {bass!r}.")

    detailed = f"{root}:{quality}"
    if bass:
        detailed = f"{detailed}/{bass}"

    if quality in MAJOR_FAMILY:
        product = root
        attention = False
    elif quality in MINOR_FAMILY:
        product = f"{root}m"
        attention = False
    elif quality in MINOR_SEVENTH_FAMILY:
        product = f"{root}m7"
        attention = False
    elif quality in DOMINANT_FAMILY:
        product = f"{root}7"
        attention = False
    else:
        product = root
        attention = True

    product_quality = (
        "maj" if product == root else "min7" if product.endswith("m7") else "min" if product.endswith("m") else "7"
    )
    simplified = detailed if bass or quality != product_quality or quality in UNSUPPORTED_FAMILY else None
    return ChordLabel(detailed, product, root, quality, bass, simplified, attention)


def transpose_chord(symbol: str | None, semitones: int) -> ChordLabel:
    """Transpose root and slash bass while preserving detailed quality."""

    label = normalize_chord(symbol)
    if label.root is None:
        return label
    prefer_flats = "b" in label.root
    names = FLAT_NAMES if prefer_flats else SHARP_NAMES
    root = names[(PITCH_CLASS[label.root] + semitones) % 12]
    bass = None
    if label.bass:
        bass_names = FLAT_NAMES if "b" in label.bass else SHARP_NAMES
        bass = bass_names[(PITCH_CLASS[label.bass] + semitones) % 12]
    symbol_value = f"{root}:{label.quality}"
    if bass:
        symbol_value = f"{symbol_value}/{bass}"
    return normalize_chord(symbol_value)
