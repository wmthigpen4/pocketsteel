"""Product-neutral pitch, copedent, chord, and grip rules for E9 steel."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Iterable


NOTE_TO_PITCH_CLASS: dict[str, int] = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "FB": 4,
    "E#": 5,
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
    "CB": 11,
}

CANONICAL_SHARP_NAMES: tuple[str, ...] = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)

CHORD_INTERVALS: dict[str, tuple[int, ...]] = {
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
    "diminished": (0, 3, 6),
    "dominant7": (0, 4, 7, 10),
}

QUALITY_ALIASES: dict[str, str] = {
    "major": "major",
    "maj": "major",
    "minor": "minor",
    "min": "minor",
    "m": "minor",
    "diminished": "diminished",
    "dim": "diminished",
    "dominant": "dominant7",
    "dominant 7": "dominant7",
    "dominant7": "dominant7",
    "dom": "dominant7",
    "dom7": "dominant7",
    "7": "dominant7",
}

MAJOR_SCALE_OFFSETS: tuple[int, ...] = (0, 2, 4, 5, 7, 9, 11)
MAJOR_SCALE_TRIAD_QUALITIES: tuple[str, ...] = (
    "major",
    "minor",
    "minor",
    "major",
    "major",
    "minor",
    "diminished",
)


@dataclass(frozen=True)
class StringTuning:
    string: int
    open_midi: int
    open_label: str


@dataclass(frozen=True)
class ControlChange:
    string: int
    semitones: int


@dataclass(frozen=True)
class CopedentControl:
    id: str
    changes: tuple[ControlChange, ...]


@dataclass(frozen=True)
class CopedentProfile:
    id: str
    revision: int
    tuning: str
    strings: tuple[StringTuning, ...]
    controls: tuple[CopedentControl, ...]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Copedent profile id is required")
        if self.revision < 1:
            raise ValueError("Copedent revision must be positive")
        if not self.tuning:
            raise ValueError("Copedent tuning is required")

        string_numbers = tuple(item.string for item in self.strings)
        if string_numbers != tuple(range(1, len(self.strings) + 1)):
            raise ValueError("Copedent strings must be unique and numbered high-to-low from 1")
        for item in self.strings:
            if midi_for_scientific_label(item.open_label) != item.open_midi:
                raise ValueError(f"Open pitch mismatch on string {item.string}")

        control_ids = tuple(control.id for control in self.controls)
        if len(set(control_ids)) != len(control_ids) or any(not control_id for control_id in control_ids):
            raise ValueError("Copedent control ids must be non-empty and unique")
        valid_strings = set(string_numbers)
        for control in self.controls:
            changed_strings = tuple(change.string for change in control.changes)
            if len(set(changed_strings)) != len(changed_strings):
                raise ValueError(f"Control {control.id} changes one string more than once")
            if any(change.string not in valid_strings for change in control.changes):
                raise ValueError(f"Control {control.id} changes an unknown string")
            if any(change.semitones == 0 for change in control.changes):
                raise ValueError(f"Control {control.id} contains a zero-semitone change")

    def strings_by_number(self) -> dict[int, StringTuning]:
        return {item.string: item for item in self.strings}

    def controls_by_id(self) -> dict[str, CopedentControl]:
        return {control.id: control for control in self.controls}


@dataclass(frozen=True)
class ResolvedNote:
    string: int
    fret: int
    controls: tuple[str, ...]
    midi: int
    label: str

    @property
    def pitch_class(self) -> int:
        return self.midi % 12


@dataclass(frozen=True)
class ChordIdentity:
    root: str
    quality: str


@dataclass(frozen=True)
class GripAnalysis:
    chord: ChordIdentity
    fret: int
    strings: tuple[int, ...]
    controls: tuple[str, ...]
    notes: tuple[ResolvedNote, ...]
    intervals: tuple[int, ...]
    missing_intervals: tuple[int, ...]
    extra_intervals: tuple[int, ...]

    @property
    def is_exact(self) -> bool:
        return not self.missing_intervals and not self.extra_intervals


@dataclass(frozen=True)
class GripFamily:
    id: str
    strings: tuple[int, ...]
    controls: tuple[str, ...]
    quality: str
    relation_to_open_major: int


BASIC_GRIP_FAMILIES: tuple[GripFamily, ...] = (
    GripFamily("open-major-456", (4, 5, 6), (), "major", 0),
    GripFamily("open-dominant7-4569", (4, 5, 6, 9), (), "dominant7", 0),
    GripFamily("two-minor-ab-567", (5, 6, 7), ("A", "B"), "minor", 2),
)


def normalize_note_name(note: str) -> str:
    normalized = (note or "").strip().replace("♯", "#").replace("♭", "b")
    if not re.fullmatch(r"[A-Ga-g](?:#|b)?", normalized):
        raise ValueError(f"Unsupported note name: {note}")
    return normalized[0].upper() + normalized[1:]


def pitch_class_for_note(note: str) -> int:
    normalized = normalize_note_name(note).upper()
    try:
        return NOTE_TO_PITCH_CLASS[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported note name: {note}") from exc


def normalize_quality(quality: str) -> str:
    normalized = re.sub(r"\s+", " ", (quality or "").strip().lower())
    try:
        return QUALITY_ALIASES[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported chord quality: {quality}") from exc


def midi_for_scientific_label(label: str) -> int:
    match = re.fullmatch(r"([A-Ga-g](?:#|b)?)(-?\d+)", (label or "").strip())
    if not match:
        raise ValueError(f"Unsupported scientific pitch: {label}")
    return 12 * (int(match.group(2)) + 1) + pitch_class_for_note(match.group(1))


def scientific_label_for_midi(midi: int) -> str:
    if not 0 <= midi <= 127:
        raise ValueError(f"MIDI pitch is out of range: {midi}")
    return f"{CANONICAL_SHARP_NAMES[midi % 12]}{midi // 12 - 1}"


def standard_emmons_e9_basic() -> CopedentProfile:
    return CopedentProfile(
        id="emmons-e9-basic",
        revision=1,
        tuning="E9",
        strings=(
            StringTuning(1, 66, "F#4"),
            StringTuning(2, 63, "D#4"),
            StringTuning(3, 68, "G#4"),
            StringTuning(4, 64, "E4"),
            StringTuning(5, 59, "B3"),
            StringTuning(6, 56, "G#3"),
            StringTuning(7, 54, "F#3"),
            StringTuning(8, 52, "E3"),
            StringTuning(9, 50, "D3"),
            StringTuning(10, 47, "B2"),
        ),
        controls=(
            CopedentControl("A", (ControlChange(5, 2), ControlChange(10, 2))),
            CopedentControl("B", (ControlChange(3, 1), ControlChange(6, 1))),
        ),
    )


def normalized_controls(profile: CopedentProfile, controls: Iterable[str]) -> tuple[str, ...]:
    requested = tuple(controls)
    if len(set(requested)) != len(requested):
        raise ValueError("Controls must not be repeated")
    by_id = profile.controls_by_id()
    unknown = [control_id for control_id in requested if control_id not in by_id]
    if unknown:
        raise ValueError(f"Unknown copedent control(s): {', '.join(unknown)}")
    requested_set = set(requested)
    return tuple(control.id for control in profile.controls if control.id in requested_set)


def resolve_note(
    profile: CopedentProfile,
    *,
    string: int,
    fret: int,
    controls: Iterable[str] = (),
) -> ResolvedNote:
    if not 0 <= fret <= 24:
        raise ValueError(f"Fret is out of range: {fret}")
    try:
        tuning = profile.strings_by_number()[string]
    except KeyError as exc:
        raise ValueError(f"String is not defined by the copedent: {string}") from exc

    control_ids = normalized_controls(profile, controls)
    change = 0
    controls_by_id = profile.controls_by_id()
    for control_id in control_ids:
        control = controls_by_id[control_id]
        change += next(
            (item.semitones for item in control.changes if item.string == string),
            0,
        )
    midi = tuning.open_midi + fret + change
    return ResolvedNote(
        string=string,
        fret=fret,
        controls=control_ids,
        midi=midi,
        label=scientific_label_for_midi(midi),
    )


def analyze_grip(
    profile: CopedentProfile,
    *,
    root: str,
    quality: str,
    fret: int,
    strings: Iterable[int],
    controls: Iterable[str] = (),
) -> GripAnalysis:
    normalized_root = normalize_note_name(root)
    normalized_quality = normalize_quality(quality)
    string_numbers = tuple(strings)
    if len(string_numbers) < 2 or len(set(string_numbers)) != len(string_numbers):
        raise ValueError("A grip requires at least two unique strings")
    control_ids = normalized_controls(profile, controls)
    notes = tuple(resolve_note(profile, string=string, fret=fret, controls=control_ids) for string in string_numbers)
    root_pitch_class = pitch_class_for_note(normalized_root)
    intervals = tuple((note.pitch_class - root_pitch_class) % 12 for note in notes)
    present = set(intervals)
    required = set(CHORD_INTERVALS[normalized_quality])
    return GripAnalysis(
        chord=ChordIdentity(normalized_root, normalized_quality),
        fret=fret,
        strings=string_numbers,
        controls=control_ids,
        notes=notes,
        intervals=intervals,
        missing_intervals=tuple(
            interval for interval in CHORD_INTERVALS[normalized_quality] if interval not in present
        ),
        extra_intervals=tuple(sorted(present - required)),
    )


def classify_exact_grip(
    profile: CopedentProfile,
    *,
    fret: int,
    strings: Iterable[int],
    controls: Iterable[str] = (),
) -> tuple[GripAnalysis, ...]:
    string_numbers = tuple(strings)
    control_ids = tuple(controls)
    matches: list[GripAnalysis] = []
    for root_pitch_class, root in enumerate(CANONICAL_SHARP_NAMES):
        for quality in CHORD_INTERVALS:
            analysis = analyze_grip(
                profile,
                root=root,
                quality=quality,
                fret=fret,
                strings=string_numbers,
                controls=control_ids,
            )
            if analysis.is_exact and pitch_class_for_note(root) == root_pitch_class:
                matches.append(analysis)
    return tuple(matches)


def find_exact_positions(
    profile: CopedentProfile,
    *,
    root: str,
    quality: str,
    grips: Iterable[Iterable[int]],
    control_sets: Iterable[Iterable[str]],
    frets: Iterable[int] = range(25),
) -> tuple[GripAnalysis, ...]:
    positions: list[GripAnalysis] = []
    grip_values = tuple(tuple(grip) for grip in grips)
    control_values = tuple(tuple(controls) for controls in control_sets)
    for fret in frets:
        for controls in control_values:
            for strings in grip_values:
                analysis = analyze_grip(
                    profile,
                    root=root,
                    quality=quality,
                    fret=fret,
                    strings=strings,
                    controls=controls,
                )
                if analysis.is_exact:
                    positions.append(analysis)
    return tuple(positions)


def major_key_degree(key: str, degree: int) -> ChordIdentity:
    if not 1 <= degree <= 7:
        raise ValueError(f"Major-key scale degree is out of range: {degree}")
    root_pitch_class = (pitch_class_for_note(key) + MAJOR_SCALE_OFFSETS[degree - 1]) % 12
    return ChordIdentity(
        root=CANONICAL_SHARP_NAMES[root_pitch_class],
        quality=MAJOR_SCALE_TRIAD_QUALITIES[degree - 1],
    )


def canonical_snapshot(profile: CopedentProfile) -> dict[str, object]:
    return {
        "tuning": profile.tuning,
        "stringOrder": "numbered-high-to-low",
        "strings": [
            {
                "string": item.string,
                "openPitch": {"midi": item.open_midi, "label": item.open_label},
            }
            for item in profile.strings
        ],
        "controls": [
            {
                "id": control.id,
                "changes": [{"string": change.string, "semitones": change.semitones} for change in control.changes],
            }
            for control in profile.controls
        ],
    }


def snapshot_digest(profile: CopedentProfile) -> str:
    payload = json.dumps(
        canonical_snapshot(profile),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
