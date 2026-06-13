"""Deterministic E9 fretboard logic for visualization payloads.

This module deliberately keeps the fretboard positions in the rules layer. It
uses the confirmed user E9 copedent and pitch math to emit render-safe
highlight data without relying on RAG snippets or hand-entered claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Literal

from pocketsteel.user_copedent import USER_E9_COPEDENT, apply_changes, open_strings_dict, supports_standard_major_position_changes


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

FretboardIntent = Literal["major_positions", "minor_positions", "minor_grips", "i_iv_v", "common_grips"]


@dataclass(frozen=True)
class MajorChordLocationRequest:
    requested_root: str
    normalized_key: str

    @property
    def is_enharmonic(self) -> bool:
        return self.requested_root != self.normalized_key


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
class ChordConceptRequest:
    requested_root: str
    normalized_key: str
    quality: str


@dataclass(frozen=True)
class ChordSymbolGuardrailRequest:
    symbol: str
    answer: str


NOTE_TO_SEMITONE: dict[str, int] = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "FB": 4,
    "F": 5,
    "E#": 5,
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

FLAT_NOTES: dict[int, str] = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}

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
    "minor": ("1", "b3", "5"),
    "dominant7": ("1", "3", "5", "b7"),
    "dominant9": ("1", "3", "5", "b7", "2/9"),
    "minor7": ("1", "b3", "5", "b7"),
}

CHORD_ADDED_INTERVALS: dict[str, tuple[str, ...]] = {
    "major": ("2/9", "6/13"),
    "minor": ("2/9", "4/11", "b7"),
    "dominant7": ("2/9", "6/13"),
    "dominant9": ("6/13",),
    "minor7": ("2/9", "4/11"),
}

CHORD_ALIASES: dict[str, str] = {
    "major": "major",
    "minor": "minor",
    "m": "minor",
    "dominant 7": "dominant7",
    "dominant7": "dominant7",
    "7": "dominant7",
    "dominant 9": "dominant9",
    "dominant9": "dominant9",
    "9": "dominant9",
    "minor 7": "minor7",
    "minor7": "minor7",
    "m7": "minor7",
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


@dataclass(frozen=True)
class FretboardPosition:
    id: str
    label: str
    root: str
    quality: str
    position_kind: str
    fret: int
    strings: tuple[int, ...]
    grip: str
    pedals: tuple[str, ...] = ()
    levers: tuple[str, ...] = ()
    color: str = "primary"
    role: str = ""
    function: str = ""
    key_context: str = ""
    notes: dict[str, str] | None = None
    intervals: dict[str, str] | None = None
    explanation: str = ""
    family: str = "major_position"
    tier: str = "beginner"
    color_role: str = ""
    visible_by_default: bool = True
    sort_order: int = 0
    omitted_intervals: tuple[str, ...] = ()
    added_intervals: tuple[str, ...] = ()
    is_full_chord: bool = False
    is_partial: bool = False
    is_rootless: bool = False
    why_use_it: str = ""
    validation_status: str = "pitch_validated"
    caveats: tuple[str, ...] = ()
    tier_reason: str = ""
    when_to_use: str = ""
    sound_character: str = ""
    movement_use: str = ""
    resolution_use: str = ""
    forum_evidence: tuple[str, ...] = ()
    forum_evidence_status: str = "not_found"
    explanation_short: str = ""
    explanation_long: str = ""

    def to_position_payload(self) -> dict:
        color_role = self.color_role or self.color
        tier_reason = self.tier_reason or default_tier_reason(self)
        when_to_use = self.when_to_use or default_when_to_use(self)
        sound_character = self.sound_character or default_sound_character(self)
        movement_use = self.movement_use or default_movement_use(self)
        resolution_use = self.resolution_use or default_resolution_use(self)
        explanation_short = self.explanation_short or default_explanation_short(self)
        explanation_long = self.explanation_long or default_explanation_long(self)
        payload: dict = {
            "id": self.id,
            "label": self.label,
            "root": self.root,
            "quality": self.quality,
            "positionKind": self.position_kind,
            "fret": self.fret,
            "strings": list(self.strings),
            "grip": self.grip,
            "pedals": list(self.pedals),
            "levers": list(self.levers),
            "color": self.color,
            "role": self.role,
            "function": self.function,
            "keyContext": self.key_context,
            "family": self.family,
            "tier": self.tier,
            "colorRole": color_role,
            "visibleByDefault": self.visible_by_default,
            "sortOrder": self.sort_order,
            "omittedIntervals": list(self.omitted_intervals),
            "addedIntervals": list(self.added_intervals),
            "isFullChord": self.is_full_chord,
            "isPartial": self.is_partial,
            "isRootless": self.is_rootless,
            "whyUseIt": self.why_use_it,
            "validationStatus": self.validation_status,
            "caveats": list(self.caveats),
            "tierReason": tier_reason,
            "whenToUse": when_to_use,
            "soundCharacter": sound_character,
            "movementUse": movement_use,
            "resolutionUse": resolution_use,
            "forumEvidence": list(self.forum_evidence),
            "forumEvidenceStatus": self.forum_evidence_status,
            "explanationShort": explanation_short,
            "explanationLong": explanation_long,
            "notes": dict(self.notes or {}),
            "intervals": dict(self.intervals or {}),
            "explanation": self.explanation,
        }
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
                "id": "user-emmons-lashley-legrande-e9",
                "label": "Emmons Lashley LeGrande E9",
                "status": "user_confirmed",
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
            "warnings": [],
            "sourceContext": [
                {
                    "kind": "rule",
                    "label": "Pitch-validated E9 copedent rule",
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
        if not isinstance(position.get("family"), str) or not position.get("family"):
            raise ValueError(f"Fretboard position {position_id} is missing family")
        if not isinstance(position.get("root"), str) or not position.get("root"):
            raise ValueError(f"Fretboard position {position_id} is missing root")
        if not isinstance(position.get("quality"), str) or not position.get("quality"):
            raise ValueError(f"Fretboard position {position_id} is missing quality")
        if not isinstance(position.get("positionKind"), str) or not position.get("positionKind"):
            raise ValueError(f"Fretboard position {position_id} is missing positionKind")
        if not isinstance(position.get("function"), str):
            raise ValueError(f"Fretboard position {position_id} has invalid function")
        if not isinstance(position.get("keyContext"), str):
            raise ValueError(f"Fretboard position {position_id} has invalid keyContext")
        if not isinstance(position.get("tier"), str) or not position.get("tier"):
            raise ValueError(f"Fretboard position {position_id} is missing tier")
        if not isinstance(position.get("colorRole"), str) or not position.get("colorRole"):
            raise ValueError(f"Fretboard position {position_id} is missing colorRole")
        if not isinstance(position.get("visibleByDefault"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid visibleByDefault")
        if not isinstance(position.get("sortOrder"), int):
            raise ValueError(f"Fretboard position {position_id} has invalid sortOrder")
        if not isinstance(position.get("omittedIntervals"), list):
            raise ValueError(f"Fretboard position {position_id} has invalid omittedIntervals")
        if not isinstance(position.get("addedIntervals"), list):
            raise ValueError(f"Fretboard position {position_id} has invalid addedIntervals")
        if not isinstance(position.get("isFullChord"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid isFullChord")
        if not isinstance(position.get("isPartial"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid isPartial")
        if not isinstance(position.get("isRootless"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid isRootless")
        if not isinstance(position.get("caveats"), list):
            raise ValueError(f"Fretboard position {position_id} has invalid caveats")
        if any(not isinstance(caveat, str) for caveat in position.get("caveats", [])):
            raise ValueError(f"Fretboard position {position_id} has non-string caveat")
        if position.get("validationStatus") != "pitch_validated":
            raise ValueError(f"Fretboard position {position_id} has invalid validationStatus")

        notes = position.get("notes")
        intervals = position.get("intervals")
        if not isinstance(notes, dict):
            raise ValueError(f"Fretboard position {position_id} has invalid notes")
        if not isinstance(intervals, dict):
            raise ValueError(f"Fretboard position {position_id} has invalid intervals")
        if not isinstance(position.get("explanation"), str):
            raise ValueError(f"Fretboard position {position_id} has invalid explanation")
        if not isinstance(position.get("whyUseIt"), str):
            raise ValueError(f"Fretboard position {position_id} has invalid whyUseIt")
        for key in (
            "tierReason",
            "whenToUse",
            "soundCharacter",
            "movementUse",
            "resolutionUse",
            "forumEvidenceStatus",
            "explanationShort",
            "explanationLong",
        ):
            if not isinstance(position.get(key), str):
                raise ValueError(f"Fretboard position {position_id} has invalid {key}")
        if position.get("forumEvidenceStatus") not in {"not_found", "found", "not_searched"}:
            raise ValueError(f"Fretboard position {position_id} has invalid forumEvidenceStatus")
        if not isinstance(position.get("forumEvidence"), list):
            raise ValueError(f"Fretboard position {position_id} has invalid forumEvidence")
        if any(not isinstance(evidence, str) for evidence in position.get("forumEvidence", [])):
            raise ValueError(f"Fretboard position {position_id} has non-string forumEvidence")
        for note_key, note_value in notes.items():
            if int(note_key) not in strings:
                raise ValueError(f"Fretboard position {position_id} has note outside strings")
            if not isinstance(note_value, str):
                raise ValueError(f"Fretboard position {position_id} has non-string note")
        for interval_key, interval_value in intervals.items():
            if int(interval_key) not in strings:
                raise ValueError(f"Fretboard position {position_id} has interval outside strings")
            if not isinstance(interval_value, str):
                raise ValueError(f"Fretboard position {position_id} has non-string interval")

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


def controls_text(position: FretboardPosition) -> str:
    controls = tuple(position.pedals) + tuple(position.levers)
    if not controls:
        return "no pedals or levers"
    return " + ".join(controls)


def position_notes_text(position: FretboardPosition) -> str:
    notes = position.notes or {}
    return ", ".join(f"string {string} = {note}" for string, note in sorted(notes.items(), key=lambda item: int(item[0])))


def position_intervals_text(position: FretboardPosition) -> str:
    intervals = position.intervals or {}
    return ", ".join(
        f"string {string} = {interval}" for string, interval in sorted(intervals.items(), key=lambda item: int(item[0]))
    )


def default_tier_reason(position: FretboardPosition) -> str:
    if position.tier == "beginner":
        return "Starter because it is a common home-position family with a complete, pitch-validated triad."
    if position.tier == "common":
        return "Common because the grip is pitch-valid in a familiar position family, but it is hidden by default to keep the starter view simple."
    if position.tier == "alternate":
        return "Alternate because it repeats the same chord color in another octave or register."
    if position.tier == "advanced":
        if position.is_rootless:
            return "Advanced because it is a partial/rootless lever pocket and needs musical context around it."
        return "Advanced because it uses a lever-family grip that is useful after the main open, A+F, and A+B positions are understood."
    return "Reference because it is included as a pitch-validated map point rather than a first-position recommendation."


def default_sound_character(position: FretboardPosition) -> str:
    quality_text = quality_label(position.quality) if position.quality in CHORD_INTERVALS else position.quality
    if position.is_full_chord and not position.added_intervals:
        return f"Complete {position.root} {quality_text} sound with the essential chord tones present."
    if position.is_rootless:
        omitted = ", ".join(position.omitted_intervals) or "the root"
        return f"Rootless {position.root} {quality_text} color; omitted interval(s): {omitted}."
    if position.is_partial:
        omitted = ", ".join(position.omitted_intervals) or "none"
        added = ", ".join(position.added_intervals) or "none"
        return f"Partial {position.root} {quality_text} color; omitted interval(s): {omitted}; added color(s): {added}."
    return "Pitch-checked color that should be treated as contextual until you hear it against the band or backing track."


def default_when_to_use(position: FretboardPosition) -> str:
    family = position.family.removeprefix("v_")
    if family in {"open_no_pedals", "open_grip", "open_octave", "open_octave_grip"}:
        return "Use it as the straight-bar reference for intonation, simple fills, and locating the chord quickly."
    if family in {"a_f", "a_f_grip", "a_f_octave", "a_f_octave_grip"}:
        return "Use it for smooth connected movement when the A pedal and F lever color helps the line sing into or out of a nearby chord."
    if family in {"a_b", "a_b_grip", "a_b_octave", "a_b_octave_grip", "a_b_lower_octave", "a_b_lower_octave_grip"}:
        return "Use it as the strong pedals-down home position or an octave/register alternate."
    if family in {"e_lower_578", "e_lower_major"}:
        return "Use it as an E-lower pocket when you want a connected lever sound or an upper/mixed-string voicing."
    if family == "e_lower_dominant_pocket":
        return "Use it as a dominant-color pocket only when the missing chord tones are supplied by context or another instrument."
    if position.function == "V":
        return f"Use it when you need the V sound in {position.key_context} and want a nearby visual pocket."
    if family in {"minor_grip", "grip_reference", "i_iv_v"}:
        return "Use it as a map point while practicing chord movement and grips."
    return position.why_use_it or position.explanation or "Use it as a pitch-validated position after checking the sound in context."


def default_movement_use(position: FretboardPosition) -> str:
    family = position.family.removeprefix("v_")
    if family.startswith("open"):
        return "Good for anchoring the bar before moving to A+F or A+B positions."
    if family.startswith("a_f"):
        return "Good for connected pedal/lever movement and passing between straight-bar positions."
    if family.startswith("a_b"):
        return "Good for pedals-down movement, octave alternates, and strong chord resolutions."
    if family.startswith("e_lower"):
        return "Good for lever-based movement and color tones when the phrase needs a more tucked-in sound."
    return "Use it as one stop in a local fretboard map, then compare it with adjacent position families."


def default_resolution_use(position: FretboardPosition) -> str:
    if position.quality in {"dominant7", "dominant9"} or "dominant" in position.family:
        target = position.key_context or position.root
        return f"Treat it as a tension color that usually wants to resolve toward {target} or a nearby tonic sound."
    if position.function == "V" and position.key_context:
        return f"Resolves naturally back toward the I chord in {position.key_context}."
    if position.is_full_chord:
        return "Stable enough to use as an arrival point."
    return "Works best when resolved into a fuller grip or supported by bass, melody, or another instrument."


def default_explanation_short(position: FretboardPosition) -> str:
    controls = controls_text(position)
    quality_text = quality_label(position.quality) if position.quality in CHORD_INTERVALS else position.quality
    if position.is_rootless:
        chord_text = f"implies a rootless {position.root} {quality_text} color"
    elif position.is_partial:
        chord_text = f"implies a partial {position.root} {quality_text} color"
    elif position.is_full_chord:
        chord_text = f"gives a full {position.root} {quality_text}"
    else:
        chord_text = f"is pitch-checked against {position.root} {quality_text}"
    return (
        f"{fret_label(position.fret)} with {controls} on grip {position.grip} {chord_text}."
    )


def default_explanation_long(position: FretboardPosition) -> str:
    notes = position_notes_text(position)
    intervals = position_intervals_text(position)
    omitted = ", ".join(position.omitted_intervals) or "none"
    added = ", ".join(position.added_intervals) or "none"
    return (
        f"{default_explanation_short(position)} Notes: {notes}. Intervals: {intervals}. "
        f"Omitted intervals: {omitted}. Added intervals: {added}. "
        f"{default_sound_character(position)} {default_when_to_use(position)}"
    )


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


def note_name_for_pitch(pitch: int) -> str:
    return CANONICAL_NOTES[pitch % 12]


def semitone_for_copedent_note(note: str) -> int:
    """Resolve a structured copedent note, including slash enharmonics."""
    first_spelling = (note or "").split("/", 1)[0].strip()
    return semitone_for_note(first_spelling)


def notes_for_controls(labels: tuple[str, ...]) -> dict[int, str]:
    return apply_changes(labels, USER_E9_COPEDENT)


def note_at_fret(open_note: str, fret: int) -> str:
    return note_name_for_pitch(semitone_for_copedent_note(open_note) + fret)


def interval_for_note(root: str, note: str) -> str:
    return INTERVAL_NAMES[(semitone_for_note(note) - semitone_for_note(root)) % 12]


def chord_quality_key(quality: str) -> str:
    normalized = re.sub(r"\s+", " ", (quality or "major").strip().lower())
    try:
        return CHORD_ALIASES[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported chord quality: {quality}") from exc


def chord_required_intervals(quality: str) -> tuple[str, ...]:
    return CHORD_INTERVALS[chord_quality_key(quality)]


def resolve_grip_notes(fret: int, strings: tuple[int, ...], controls: tuple[str, ...]) -> dict[str, str]:
    changed_notes = notes_for_controls(controls)
    notes: dict[str, str] = {}
    for string in strings:
        notes[str(string)] = note_at_fret(changed_notes[string], fret)
    return notes


def classify_voicing(
    root: str,
    quality: str,
    notes: dict[str, str],
    *,
    allow_added_intervals: bool = False,
) -> dict[str, object] | None:
    """Classify notes against a target chord quality without trusting labels."""
    quality_key = chord_quality_key(quality)
    required = chord_required_intervals(quality_key)
    allowed = set(required)
    if allow_added_intervals:
        allowed.update(CHORD_ADDED_INTERVALS.get(quality_key, ()))
    intervals: dict[str, str] = {}
    for string, note in notes.items():
        interval = interval_for_note(root, note)
        if interval not in allowed:
            return None
        intervals[str(string)] = interval

    present = set(intervals.values())
    if len(present) < 2:
        return None
    if not present.intersection(required):
        return None

    omitted = tuple(interval for interval in required if interval not in present)
    added = tuple(interval for interval in present if interval not in required)
    is_full = not omitted
    return {
        "intervals": intervals,
        "omitted_intervals": omitted,
        "added_intervals": added,
        "is_full_chord": is_full,
        "is_partial": not is_full or bool(added),
        "is_rootless": "1" not in present,
    }


def classify_grip_against_root(
    root: str,
    quality: str,
    *,
    fret: int,
    strings: tuple[int, ...],
    controls: tuple[str, ...],
    allow_added_intervals: bool = False,
) -> tuple[dict[str, str], dict[str, str], tuple[str, ...], tuple[str, ...], bool, bool, bool] | None:
    notes = resolve_grip_notes(fret, strings, controls)
    classification = classify_voicing(root, quality, notes, allow_added_intervals=allow_added_intervals)
    if classification is None:
        return None
    return (
        notes,
        classification["intervals"],  # type: ignore[return-value]
        classification["omitted_intervals"],  # type: ignore[return-value]
        classification["added_intervals"],  # type: ignore[return-value]
        bool(classification["is_full_chord"]),
        bool(classification["is_partial"]),
        bool(classification["is_rootless"]),
    )


def major_triad_match(key: str, fret: int, strings: tuple[int, ...], controls: tuple[str, ...]) -> tuple[dict[str, str], dict[str, str]] | None:
    """Return note/interval annotations when the candidate is a complete major triad."""
    classification = classify_grip_against_root(key, "major", fret=fret, strings=strings, controls=controls)
    if classification is None:
        return None
    notes, intervals, omitted, _, _, _, _ = classification
    if omitted:
        return None
    return notes, intervals


def best_grip_classification(fret: int, strings: tuple[int, ...], controls: tuple[str, ...]) -> dict[str, object]:
    """Classify a free-form grip by pitch math, preferring full simple chords."""
    notes = resolve_grip_notes(fret, strings, controls)
    candidates: list[dict[str, object]] = []
    for semitone, root in CANONICAL_NOTES.items():
        for quality in ("major", "dominant7", "dominant9", "minor7"):
            classification = classify_voicing(root, quality, notes)
            if classification is None:
                continue
            present_count = len(set(classification["intervals"].values()))  # type: ignore[union-attr]
            full_bonus = 100 if classification["is_full_chord"] else 0
            quality_bonus = {"major": 30, "dominant7": 20, "minor7": 15, "dominant9": 10}[quality]
            root_bonus = 5 if not classification["is_rootless"] else 0
            candidates.append(
                {
                    "root": root,
                    "quality": quality,
                    "notes": notes,
                    "score": full_bonus + quality_bonus + root_bonus + present_count,
                    **classification,
                }
            )
    if not candidates:
        return {
            "root": "",
            "quality": "unknown",
            "notes": notes,
            "intervals": {},
            "omitted_intervals": (),
            "added_intervals": (),
            "is_full_chord": False,
            "is_partial": False,
            "is_rootless": False,
            "score": 0,
        }
    return max(candidates, key=lambda candidate: int(candidate["score"]))


def major_position_candidate(
    *,
    key: str,
    quality: str = "major",
    suffix: str,
    fret: int,
    strings: tuple[int, ...],
    pedals: tuple[str, ...] = (),
    levers: tuple[str, ...] = (),
    color: str,
    role: str,
    family: str,
    tier: str,
    color_role: str,
    visible_by_default: bool,
    sort_order: int,
    explanation: str,
    function: str = "",
    key_context: str = "",
    why_use_it: str = "",
    caveats: tuple[str, ...] = (),
    allow_added_intervals: bool = True,
) -> FretboardPosition | None:
    controls = pedals + levers
    classification = classify_grip_against_root(
        key,
        quality,
        fret=fret,
        strings=strings,
        controls=controls,
        allow_added_intervals=allow_added_intervals,
    )
    if classification is None:
        return None
    notes, intervals, omitted_intervals, added_intervals, is_full_chord, is_partial, is_rootless = classification
    quality_key = chord_quality_key(quality)
    position_kind = position_kind_for_classification(
        family=family,
        quality=quality_key,
        is_full_chord=is_full_chord,
        is_partial=is_partial,
        is_rootless=is_rootless,
        added_intervals=added_intervals,
    )
    return FretboardPosition(
        id=f"{slug(key)}-{suffix}",
        label=f"{key} {quality_label(quality)}",
        root=key,
        quality=chord_quality_key(quality),
        position_kind=position_kind,
        fret=fret,
        strings=strings,
        grip=grip_label(strings),
        pedals=pedals,
        levers=levers,
        color=color,
        role=role,
        function=function,
        key_context=key_context,
        notes=notes,
        intervals=intervals,
        explanation=explanation,
        family=family,
        tier=tier,
        color_role=color_role,
        visible_by_default=visible_by_default,
        sort_order=sort_order,
        omitted_intervals=omitted_intervals,
        added_intervals=added_intervals,
        is_full_chord=is_full_chord,
        is_partial=is_partial,
        is_rootless=is_rootless,
        why_use_it=why_use_it or explanation,
        validation_status="pitch_validated",
        caveats=caveats,
    )


def require_major_position(candidate: FretboardPosition | None, *, key: str, role: str) -> FretboardPosition:
    if candidate is None:
        raise ValueError(f"Structured E9 copedent did not validate {key} {role} major position")
    return candidate


def quality_label(quality: str) -> str:
    return {
        "major": "major",
        "minor": "minor",
        "dominant7": "dominant 7",
        "dominant9": "dominant 9",
        "minor7": "minor 7",
    }.get(chord_quality_key(quality), quality)


def position_kind_for_classification(
    *,
    family: str,
    quality: str,
    is_full_chord: bool,
    is_partial: bool,
    is_rootless: bool,
    added_intervals: tuple[str, ...],
) -> str:
    if family in {"i_iv_v", "grip_reference", "minor_grip"}:
        return "movement_pocket"
    if quality in {"dominant7", "dominant9"}:
        return "rootless_voicing" if is_rootless else "dominant_pocket"
    if is_rootless:
        return "rootless_voicing"
    if is_full_chord and not is_partial and not added_intervals:
        return "full_chord_position"
    if is_partial:
        return "partial_chord_grip"
    return "uncertain_or_unvalidated"


def position_kind_for_family(family: str, visible_by_default: bool) -> str:
    if visible_by_default:
        return "starter"
    if family in {"open_grip", "a_f_grip", "a_b_grip"}:
        return "common_grip"
    if family == "a_b_lower_octave":
        return "alternate_octave"
    if family == "a_b_lower_octave_grip":
        return "alternate_grip"
    if family == "e_lower_578":
        return "advanced_lever"
    if family in {"minor_grip", "grip_reference", "i_iv_v"}:
        return "reference"
    return "validated_position"


def indefinite_article(term: str) -> str:
    return "an" if term[:1].upper() in {"A", "E", "F"} else "a"


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
    if normalized_intent == "minor_positions":
        return minor_positions(normalized_key).to_payload()
    if normalized_intent == "minor_grips":
        return minor_grips(normalized_key).to_payload()
    if normalized_intent == "i_iv_v":
        return i_iv_v_examples(normalized_key).to_payload()
    if normalized_intent == "common_grips":
        return common_grip_examples(normalized_key).to_payload()
    raise ValueError(f"Unsupported fretboard example intent: {intent}")


def parse_grip_strings(raw_grip: str) -> tuple[int, ...] | None:
    parts = re.findall(r"\d{1,2}", raw_grip or "")
    if not parts:
        return None
    strings = tuple(int(part) for part in parts)
    if len(strings) < 2 or len(set(strings)) != len(strings):
        return None
    if any(string < 1 or string > 10 for string in strings):
        return None
    return strings


def e_lower_grip_request_for_question(question: str) -> ELowerGripRequest | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    compact = re.search(
        r"^what\s+(?:is|are|does)\s+(?P<fret>\d{1,2})e\s+(?:on\s+)?strings?\s+(?P<grip>\d{1,2}\s*[-/ ]\s*\d{1,2}(?:\s*[-/ ]\s*\d{1,2})*)$",
        q,
    )
    if compact:
        strings = parse_grip_strings(compact.group("grip"))
        fret = int(compact.group("fret"))
        if strings is not None and 0 <= fret <= 24:
            return ELowerGripRequest(fret=fret, strings=strings)

    explicit = re.search(
        r"(?:what\s+(?:do i get|does|is)|what\s+are)\s+(?:at|on)\s+(?:the\s+)?(?:fret\s+)?(?P<fret>\d{1,2})(?:st|nd|rd|th)?(?:\s+fret)?\s+with\s+(?:my\s+)?(?:e[- ]?lower|e lowered|e's lowered|es lowered|lowered e)\s+(?:on\s+)?strings?\s+(?P<grip>\d{1,2}\s*[-/ ]\s*\d{1,2}(?:\s*[-/ ]\s*\d{1,2})*)",
        q,
    )
    if explicit:
        strings = parse_grip_strings(explicit.group("grip"))
        fret = int(explicit.group("fret"))
        if strings is not None and 0 <= fret <= 24:
            return ELowerGripRequest(fret=fret, strings=strings)

    legacy = re.search(
        r"\b(?P<grip>\d{1,2}\s*[-/ ]\s*\d{1,2}(?:\s*[-/ ]\s*\d{1,2})*)\b.*\b(?:e[- ]?lower|e lowered|e's lowered|es lowered|lowered e)\b.*\b(?:at|on)\s+(?:the\s+)?(?P<fret>\d{1,2})(?:st|nd|rd|th)?\s+fret\b",
        q,
    )
    if legacy:
        strings = parse_grip_strings(legacy.group("grip"))
        fret = int(legacy.group("fret"))
        if strings is not None and 0 <= fret <= 24:
            return ELowerGripRequest(fret=fret, strings=strings)
    return None


def e_lower_grip_usage_request_for_question(question: str) -> tuple[int, ...] | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    match = re.search(
        r"^(?:when would i use|how would i use|what is the use of)\s+(?P<grip>\d{1,2}\s*[-/ ]\s*\d{1,2}(?:\s*[-/ ]\s*\d{1,2})*)\s+with\s+(?:my\s+)?(?:e[- ]?lower|e lowered|lowered e)$",
        q,
    )
    if not match:
        return None
    return parse_grip_strings(match.group("grip"))


def e_lower_578_request_for_question(question: str) -> ELower578Request | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    if not re.search(r"\b5\s*[-/ ]\s*7\s*[-/ ]\s*8\b", q):
        return None
    if not re.search(r"\b(?:e[- ]?lower|e lowered|e's lowered|es lowered|lowered e)\b", q):
        return None
    match = re.search(r"\b(?:at|on)\s+(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+fret\b", q)
    if not match:
        return None
    fret = int(match.group(1))
    if not 0 <= fret <= 24:
        return None
    return ELower578Request(fret=fret)


def e_lower_grip_position_at_fret(fret: int, strings: tuple[int, ...]) -> FretboardPosition:
    classification = best_grip_classification(fret, strings, ("E",))
    root = str(classification["root"] or "unknown")
    quality = str(classification["quality"] or "unknown")
    notes = classification["notes"]
    intervals = classification["intervals"]
    omitted = classification["omitted_intervals"]
    added = classification.get("added_intervals", ())
    if not isinstance(added, tuple):
        added = tuple()
    quality_key = chord_quality_key(quality) if quality in CHORD_INTERVALS else quality
    quality_text = quality_label(quality) if quality in CHORD_INTERVALS else quality
    if root == "unknown" or quality == "unknown":
        role = f"Pitch-checked E-lower {grip_label(strings)} grip"
        label = f"{grip_label(strings)} E-lower at fret {fret}"
        explanation = "Pitch math did not classify this grip as a simple supported chord quality."
        position_kind = "uncertain_or_unvalidated"
    else:
        role = f"E-lower {grip_label(strings)} {quality_text} grip"
        label = f"{root} {quality_text}"
        explanation = f"With E lowered at fret {fret}, strings {grip_label(strings)} resolve by pitch math to a {root} {quality_text} grip."
        position_kind = position_kind_for_classification(
            family="e_lower_578" if strings == E_LOWER_578_GRIP else "e_lower_major",
            quality=quality_key,
            is_full_chord=bool(classification["is_full_chord"]),
            is_partial=bool(classification["is_partial"]),
            is_rootless=bool(classification["is_rootless"]),
            added_intervals=added,
        )
    family = "e_lower_578" if strings == E_LOWER_578_GRIP else "e_lower_major"
    return FretboardPosition(
        id=f"{slug(root) if root != 'unknown' else 'unknown'}-e-lower-{grip_label(strings)}-{fret}",
        label=label,
        root=root,
        quality=quality_key,
        position_kind=position_kind,
        fret=fret,
        strings=strings,
        grip=grip_label(strings),
        levers=("E",),
        color="reference",
        role=role,
        function="diagnostic",
        key_context=root if root != "unknown" else "",
        notes=notes if isinstance(notes, dict) else {},
        intervals=intervals if isinstance(intervals, dict) else {},
        explanation=explanation,
        family=family,
        tier="advanced",
        color_role="reference",
        visible_by_default=True,
        sort_order=10,
        omitted_intervals=omitted if isinstance(omitted, tuple) else tuple(),
        added_intervals=added,
        is_full_chord=bool(classification["is_full_chord"]),
        is_partial=bool(classification["is_partial"]),
        is_rootless=bool(classification["is_rootless"]),
        why_use_it=f"Use this as a focused pitch diagnostic for the {grip_label(strings)} grip and E-lower lever.",
        validation_status="pitch_validated",
        caveats=("Assumes E-lower lowers strings 4 and 8 E to D#/Eb.",),
    )


def e_lower_578_position_at_fret(fret: int) -> FretboardPosition:
    return e_lower_grip_position_at_fret(fret, E_LOWER_578_GRIP)


def e_lower_grip_payload_for_question(question: str) -> dict | None:
    request = e_lower_grip_request_for_question(question)
    if request is None:
        return None
    position = e_lower_grip_position_at_fret(request.fret, request.strings)
    root = position.root if position.root != "unknown" else "pitch-checked"
    return FretboardVisualizationPayload(
        title=f"{grip_label(request.strings)} with E-lower at fret {request.fret}",
        subtitle=f"Pitch-math classification for strings {grip_label(request.strings)} with E-lower at fret {request.fret}.",
        key=root,
        positions=(position,),
    ).to_payload()


def e_lower_578_payload_for_question(question: str) -> dict | None:
    request = e_lower_578_request_for_question(question)
    if request is None:
        return None
    position = e_lower_578_position_at_fret(request.fret)
    root = position.root if position.root != "unknown" else "pitch-checked"
    return FretboardVisualizationPayload(
        title=f"5-7-8 with E-lower at fret {request.fret}",
        subtitle=f"Pitch-math classification for strings 5-7-8 with E-lower at fret {request.fret}.",
        key=root,
        positions=(position,),
    ).to_payload()


def e_lower_578_b9_payload_for_question(question: str) -> dict | None:
    if not e_lower_578_b9_question(question):
        return None
    position = replace(
        e_lower_578_position_at_fret(3),
        id="b9-check-e-lower-5-7-8-3",
        role="B9 check: 5-7-8 with E-lower at fret 3",
        function="B9 check",
        key_context="B",
        family="e_lower_578_b9_check",
        color="warning",
        color_role="warning",
        sort_order=0,
        why_use_it=(
            "Use this focused pitch check to hear why the grip is D major at the 3rd fret, "
            "not a complete B9 pocket by itself."
        ),
        tier_reason="Diagnostic: this card verifies a named grip/fret claim by pitch math.",
        when_to_use="Use it when checking whether 5-7-8 with E-lower is really a B9 pocket.",
        sound_character="Complete D major at the 3rd fret; against B it can suggest rootless B minor 7 color, not B9.",
        movement_use="Useful as a named-pitch diagnostic before applying the grip in context.",
        resolution_use="Resolve by ear to a true B, B7, or B9 voicing if the song needs B as the harmonic center.",
        explanation_short="At fret 3, 5-7-8 with E-lower spells D major, not B9.",
        explanation_long=(
            "The confirmed E9 copedent lowers string 8 E to D#. At fret 3, strings 5, 7, and 8 become "
            "D, A, and F#, which are the root, fifth, and third of D major. Those notes omit the B root, "
            "b7, and 9 needed for a full B9 label."
        ),
    )
    return FretboardVisualizationPayload(
        title="5-7-8 E-lower B9 check",
        subtitle="Pitch-math check for whether 5-7-8 with E-lower is a B9 pocket.",
        key="B",
        positions=(position,),
    ).to_payload()


def e_lower_grip_answer_for_question(question: str) -> str | None:
    request = e_lower_grip_request_for_question(question)
    if request is None:
        return None
    position = e_lower_grip_position_at_fret(request.fret, request.strings)
    return e_lower_grip_answer(position, fret=request.fret)


def e_lower_grip_answer(position: FretboardPosition, *, fret: int) -> str:
    notes = position.notes or {}
    intervals = position.intervals or {}
    note_list = ", ".join(f"string {string} = {note}" for string, note in sorted(notes.items(), key=lambda item: int(item[0])))
    interval_list = ", ".join(
        f"string {string} = {interval}" for string, interval in sorted(intervals.items(), key=lambda item: int(item[0]))
    )
    if position.root == "unknown":
        return (
            f"At fret {fret} with E lowered, strings {position.grip} resolve to: {note_list}. "
            "I do not classify that as a complete major, dominant, or minor-7 grip from the supported pitch rules."
        )
    quality_text = quality_label(position.quality) if position.quality in CHORD_INTERVALS else position.quality
    lines = [
        f"At fret {fret} with E lowered, strings {position.grip} resolve to {position.root} {quality_text}.",
        "",
        f"- Notes: {note_list}.",
        f"- Intervals against {position.root}: {interval_list}.",
    ]
    if position.is_full_chord:
        lines.append(f"- Classification: full {position.root} {quality_text}.")
    elif position.is_rootless:
        omitted = ", ".join(position.omitted_intervals)
        lines.append(f"- Classification: rootless partial {position.root} {quality_text}; omitted interval(s): {omitted}.")
    else:
        omitted = ", ".join(position.omitted_intervals)
        lines.append(f"- Classification: partial {position.root} {quality_text}; omitted interval(s): {omitted}.")
    lines.append(f"- Use: {position.to_position_payload()['whenToUse']}")
    return "\n".join(lines)


def e_lower_578_answer_for_question(question: str) -> str | None:
    request = e_lower_578_request_for_question(question)
    if request is None:
        return None
    position = e_lower_578_position_at_fret(request.fret)
    lines = e_lower_grip_answer(position, fret=request.fret).splitlines()
    if position.root == "D" and position.quality == "major":
        lines.append("- Against a B root, those notes can also sound like a rootless B minor 7 color because the B root is omitted.")
    return "\n".join(lines)


def e_lower_grip_usage_answer_for_question(question: str) -> str | None:
    strings = e_lower_grip_usage_request_for_question(question)
    if strings is None:
        return None
    examples = [e_lower_grip_position_at_fret(fret, strings) for fret in (0, 3, 8, 12, 20)]
    classified = [position for position in examples if position.root != "unknown"]
    if not classified:
        return (
            f"I do not find a simple supported chord classification for {grip_label(strings)} with E-lower in the checked starter frets. "
            "Use it as an ear-check grip and give me a fret if you want an exact note calculation."
        )
    first = classified[0]
    lines = [
        f"Use {grip_label(strings)} with E-lower as an advanced lever-pocket grip, not as the only special E-lower option.",
        "",
        "Pitch-math examples",
    ]
    for position in classified:
        quality_text = quality_label(position.quality) if position.quality in CHORD_INTERVALS else position.quality
        lines.append(
            f"- {fret_label(position.fret)}: {position.root} {quality_text}; notes {position_notes_text(position)}; intervals {position_intervals_text(position)}."
        )
    lines.extend(
        [
            "",
            f"Musical use: {first.to_position_payload()['whenToUse']}",
            "Other E-lower grip families worth checking by pitch math are 7-8-10, 4-5-7, and 1-4-5; they should be labeled by what they actually spell at the fret, not by forum shorthand.",
        ]
    )
    return "\n".join(lines)


def e_lower_578_b9_question(question: str) -> bool:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return False
    return bool(
        re.search(r"\b5\s*[-/ ]\s*7\s*[-/ ]\s*8\b", q)
        and re.search(r"\b(?:e[- ]?lower|e lowered|e's lowered|es lowered|lowered e)\b", q)
        and re.search(r"\bb9\b", q)
    )


def e_lower_578_b9_answer_for_question(question: str) -> str | None:
    if not e_lower_578_b9_question(question):
        return None
    fret_three = e_lower_578_position_at_fret(3)
    b_major_frets: list[str] = []
    for fret in (0, 12, 24):
        position = e_lower_578_position_at_fret(fret)
        if position.root == "B" and position.quality == "major":
            b_major_frets.append(str(fret))
    b_major_text = ", ".join(b_major_frets)
    note_list = ", ".join(f"string {string} = {note}" for string, note in (fret_three.notes or {}).items())
    return (
        "No: 5-7-8 with E lowered is not a full B9 pocket by itself under the confirmed E9 copedent.\n\n"
        f"- At the 3rd fret it resolves to D major ({note_list}), not B9; against a B root, those notes can also sound like a rootless B minor 7 color because the B root is omitted.\n"
        f"- At frets {b_major_text}, the same grip spells B major, which can be a useful B pocket, but it omits the b7 and 9 that would make a full B9 sound.\n"
        "- So I would treat it as pitch-dependent: B major at the matching frets, D major at the 3rd fret, and not a complete B9 grip unless other notes supply the missing dominant color."
    )


def functional_pocket_request_for_question(question: str) -> FunctionalPocketRequest | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    match = re.search(
        r"^(?:show me|where are|give me)\s+(?P<function>v|5|five)(?:\s+chord)?\s+pockets?\s+in\s+(?P<key>[a-g](?:#|b)?)$",
        q,
    )
    if not match:
        return None
    key = normalize_key(match.group("key"))
    target_root = transpose(key, 7)
    return FunctionalPocketRequest(key=key, function="V", target_root=target_root)


def functional_pocket_positions(request: FunctionalPocketRequest) -> tuple[FretboardPosition, ...]:
    source = major_positions(request.target_root).positions
    allowed_families = {
        "open_no_pedals",
        "a_f",
        "a_b",
        "a_b_lower_octave",
        "e_lower_578",
        "e_lower_major",
        "e_lower_dominant_pocket",
    }
    positions: list[FretboardPosition] = []
    for index, position in enumerate(source):
        if position.family not in allowed_families:
            continue
        pocket_family = "v_" + position.family
        pocket_role = f"V chord in {request.key}: {position.role}"
        position_kind = position.position_kind
        if position.family == "e_lower_dominant_pocket":
            position_kind = "dominant_pocket" if not position.is_rootless else "rootless_voicing"
        positions.append(
            replace(
                position,
                id=f"{slug(request.key)}-v-{position.id}",
                role=pocket_role,
                function=request.function,
                key_context=request.key,
                family=pocket_family,
                position_kind=position_kind,
                sort_order=index * 10,
                why_use_it=(
                    f"Use this as a {request.target_root} V-chord pocket in {request.key}; "
                    "major positions give the stable V sound, while E-lower dominant pockets add partial/rootless dominant color."
                ),
            )
        )
    return tuple(positions)


def functional_pocket_payload_for_question(question: str) -> dict | None:
    request = functional_pocket_request_for_question(question)
    if request is None:
        return None
    return FretboardVisualizationPayload(
        title=f"V chord pockets in {request.key} ({request.target_root})",
        subtitle=(
            f"Pitch-validated {request.target_root} major and dominant-color pockets for the V chord in {request.key}."
        ),
        key=request.key,
        positions=functional_pocket_positions(request),
    ).to_payload()


def functional_pocket_answer_for_question(question: str) -> str | None:
    request = functional_pocket_request_for_question(question)
    if request is None:
        return None
    payload = functional_pocket_payload_for_question(question)
    if payload is None:
        return None
    visible = [position for position in payload["positions"] if position["visibleByDefault"]]
    dominant = [position for position in payload["positions"] if position["family"] == "v_e_lower_dominant_pocket"]
    lines = [
        f"In {request.key}, the V chord is {request.target_root}. Use these pitch-validated {request.target_root} pockets as a practical map.",
        "",
        "Starter V positions",
    ]
    for position in visible:
        controls = " + ".join([*position["pedals"], *position["levers"]]) or "no pedals"
        lines.append(f"- {fret_label(position['fret'])} with {controls}: {position['role'].split(': ', 1)[-1]}, grip {position['grip']}.")
    if dominant:
        lines.extend(["", "Dominant-color pockets"])
        for position in dominant[:4]:
            intervals = ", ".join(dict(position["intervals"]).values())
            omitted = ", ".join(position["omittedIntervals"]) or "none"
            lines.append(
                f"- {fret_label(position['fret'])} with E-lower on {position['grip']}: intervals {intervals}; omitted {omitted}."
            )
    lines.append("")
    lines.append("Treat the dominant pockets as partial/rootless colors unless the missing chord tones are supplied elsewhere.")
    return "\n".join(lines)


def key_context_for_question(question: str) -> str | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    match = re.search(r"\b(?:in\s+the\s+key\s+of|key\s+of|in)\s+([a-g](?:#|b)?)\b", q)
    if not match:
        return None
    return normalize_key(match.group(1))


def function_root_for_key(key: str, degree: int) -> str:
    return CANONICAL_NOTES[(semitone_for_note(normalize_key(key)) + MAJOR_SCALE_INTERVALS[degree]) % 12]


def function_token_to_degree_and_quality(token: str, explicit_quality: str = "") -> tuple[int, str] | None:
    normalized = re.sub(r"\s+", "", (token or "").strip().lower()).replace("º", "°")
    if not normalized:
        return None
    numeric = re.match(r"^([1-7])(?:(m|minor|dim|diminished))?$", normalized)
    if numeric:
        degree = int(numeric.group(1))
        quality = normalize_chord_quality(numeric.group(2) or explicit_quality or FUNCTION_QUALITIES[degree])
        return degree, quality
    roman = ROMAN_FUNCTIONS.get(normalized)
    if roman is None:
        return None
    return roman, FUNCTION_QUALITIES[roman]


def function_chord_request_for_question(question: str) -> FunctionChordRequest | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    if re.search(r"\b1\s*[-/]\s*4\s*[-/]\s*5\b", q):
        return None
    key = key_context_for_question(q)
    if key is None:
        return None
    numeric_match = re.search(
        r"\b(?P<token>[1-7]\s*(?:m|minor|dim|diminished)?)\b(?:\s*(?:chord|minor|major|diminished|dim))?",
        q,
    )
    roman_match = re.search(
        r"\b(?:the\s+)?(?P<token>vii°|viiº|viio|vii0|vii|vi|iii|ii|iv|v|i)\s+chord\b",
        q,
    ) or re.search(
        r"\bshow me\s+(?:the\s+)?(?P<token>vii°|viiº|viio|vii0|vii|vi|iii|ii|iv|v|i)\s+in\b",
        q,
    )
    function_match = numeric_match or roman_match
    if not function_match:
        return None
    requested = re.sub(r"\s+", "", function_match.group("token")).replace("º", "°")
    explicit_quality = ""
    trailing = q[function_match.end() : function_match.end() + 18]
    if "minor" in trailing:
        explicit_quality = "minor"
    elif "dim" in trailing or "diminished" in trailing:
        explicit_quality = "diminished"
    parsed = function_token_to_degree_and_quality(requested, explicit_quality)
    if parsed is None:
        return None
    degree, quality = parsed
    root = function_root_for_key(key, degree)
    return FunctionChordRequest(
        key=key,
        requested_function=requested,
        degree=degree,
        root=root,
        quality=quality,
    )


def minor_chord_location_request_for_question(question: str) -> MinorChordLocationRequest | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    patterns = (
        r"^where is ([a-g](?:#|b)?)(?:m|[- ]minor)(?: chord)?(?: on e9)?$",
        r"^where can i play (?:a|an)?\s*([a-g](?:#|b)?)(?:m|[- ]minor)(?: chord)?(?: on e9)?$",
        r"^how do i play (?:a|an)?\s*([a-g](?:#|b)?)(?:m|[- ]minor)(?: chord)?(?: on e9)?$",
        r"^show me ([a-g](?:#|b)?)(?:m|[- ]minor) positions$",
        r"^what frets give me (?:a|an)?\s*([a-g](?:#|b)?)(?:m|[- ]minor)(?: chord)?$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            requested_root = normalize_requested_root(match.group(1))
            return MinorChordLocationRequest(
                requested_root=requested_root,
                normalized_key=normalize_key(requested_root),
            )
    return None


def function_chord_payload_for_question(question: str) -> dict | None:
    request = function_chord_request_for_question(question)
    if request is None:
        return None
    if request.quality == "major":
        return major_positions(request.root).to_payload()
    if request.quality == "minor":
        return minor_positions(request.root).to_payload()
    return None


def minor_chord_payload_for_question(question: str) -> dict | None:
    request = minor_chord_location_request_for_question(question)
    if request is None:
        return None
    return minor_positions(request.normalized_key).to_payload()


def chord_concept_payload_for_question(question: str) -> dict | None:
    request = chord_concept_request_for_question(question)
    if request is None:
        return None
    if request.quality == "minor":
        return minor_positions(request.normalized_key).to_payload()
    return major_positions(request.normalized_key).to_payload()


def function_chord_answer_for_question(question: str) -> str | None:
    request = function_chord_request_for_question(question)
    if request is None:
        return None
    if request.quality == "major":
        positions = major_positions(request.root).to_payload()["positions"]
        visible = [position for position in positions if position["visibleByDefault"]]
        lines = [
            f"{request.requested_function} in {request.key} is {request.root} major.",
            "",
            f"Useful {request.root} major starter positions on E9:",
        ]
        for position in visible:
            controls = " + ".join([*position["pedals"], *position["levers"]]) or "no pedals"
            lines.append(f"- {fret_label(position['fret'])} with {controls}: {position['role']}.")
        return "\n".join(lines)
    if request.quality == "minor":
        if request.degree == 2:
            return two_minor_function_answer(request)
        return minor_position_answer(
            request.root,
            prefix=f"{request.requested_function} in {request.key} is {request.root} minor ({minor_triad_spelling(request.root)}).",
        )
    if request.quality == "diminished":
        return (
            f"{request.requested_function} in {request.key} is {request.root} diminished. "
            "The deterministic fretboard view currently supports major and minor position diagrams first, so I would not use SGF snippets for a diminished-position answer. "
            "Give me the exact strings/pedals/levers you want checked and I can calculate the notes directly."
        )
    return None


def chord_symbol_guardrail_answer_for_question(question: str) -> str | None:
    request = invalid_chord_symbol_request_for_question(question)
    return request.answer if request is not None else None


def invalid_chord_symbol_request_for_question(question: str) -> ChordSymbolGuardrailRequest | None:
    symbol = chord_symbol_from_chord_like_question(question)
    if symbol is None:
        return None
    normalized_symbol = symbol.strip().replace("♯", "#").replace("♭", "b")
    if not normalized_symbol:
        return None
    if "/" in normalized_symbol and is_supported_slash_chord_symbol(normalized_symbol):
        return ChordSymbolGuardrailRequest(
            symbol=normalized_symbol,
            answer=slash_chord_clarification_answer(normalized_symbol),
        )
    if is_supported_chord_symbol(normalized_symbol):
        return None
    return ChordSymbolGuardrailRequest(
        symbol=normalized_symbol,
        answer=invalid_chord_symbol_clarification_answer(normalized_symbol),
    )


def chord_symbol_from_chord_like_question(question: str) -> str | None:
    q = re.sub(r"[?!.,;:]+", " ", question or "")
    q = re.sub(r"\s+", " ", q).strip().lower()
    if not q:
        return None
    patterns = (
        r"^how do i (?:play|make|plan) (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^where is (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^what is (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^what(?:'s|’s) (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^show me (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^what does (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord mean$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return normalize_chord_symbol_display(match.group("symbol"))
    return None


def normalize_chord_symbol_display(symbol: str) -> str:
    symbol = (symbol or "").strip().replace("♯", "#").replace("♭", "b")
    if not symbol:
        return symbol
    if "/" in symbol:
        left, right = symbol.split("/", 1)
        return f"{normalize_chord_symbol_display(left)}/{normalize_chord_symbol_display(right)}"
    root = symbol[:1].upper()
    rest = symbol[1:]
    if len(symbol) == 2 and symbol[:1].lower() in "abcdefg" and symbol[1:].lower() in "abcdefg":
        return symbol.upper()
    if rest.startswith(("#", "b")):
        accidental = rest[:1]
        quality = rest[1:]
    else:
        accidental = ""
        quality = rest
    quality_aliases = {
        "m": "m",
        "min": "m",
        "minor": "m",
        "maj": "maj",
        "major": "",
        "dim": "dim",
        "aug": "aug",
        "sus": "sus",
    }
    quality = quality_aliases.get(quality.lower(), quality)
    return f"{root}{accidental}{quality}"


def is_supported_chord_symbol(symbol: str) -> bool:
    if "/" in symbol:
        return is_supported_slash_chord_symbol(symbol)
    match = re.match(r"^(?P<root>[A-G](?:#|b)?)(?P<quality>m|7|9|m7|maj7|dim|aug|sus2?|sus4?)?$", symbol)
    if not match:
        return False
    return note_lookup_key(match.group("root")) in NOTE_TO_SEMITONE


def is_supported_slash_chord_symbol(symbol: str) -> bool:
    parts = symbol.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return False
    chord, bass = parts
    if "/" in chord or "/" in bass:
        return False
    if not re.match(r"^[A-G](?:#|b)?(?:m|7|9|m7|maj7|dim|aug|sus2?|sus4?)?$", chord):
        return False
    if not re.match(r"^[A-G](?:#|b)?$", bass):
        return False
    return note_lookup_key(chord[:2] if len(chord) > 1 and chord[1] in "#b" else chord[:1]) in NOTE_TO_SEMITONE and note_lookup_key(bass) in NOTE_TO_SEMITONE


def invalid_chord_symbol_clarification_answer(symbol: str) -> str:
    if len(symbol) == 2 and symbol[0] in "ABCDEFG" and symbol[1] in "ABCDEFG":
        first, second = symbol[0], symbol[1]
        return (
            f"I don’t recognize “{symbol}” as a standard chord name.\n\n"
            "Did you mean:\n"
            f"- {first}\n"
            f"- {second}\n"
            f"- {first}/{second}, a {first} chord over a {second} bass note\n\n"
            f"If you meant {first}, I can show common {first} positions on E9. "
            f"If you meant {second}, I can show {second} positions. "
            f"If you meant {first}/{second}, say it with a slash."
        )
    if symbol[:1] not in "ABCDEFG":
        return (
            f"I don’t recognize “{symbol}” as a standard chord name. "
            "In this app, chord roots should use A through G, with optional sharps or flats, such as G, F, C#, Bb, Em, G7, or B9.\n\n"
            "Tell me the chord root you meant and I can map it to E9 positions."
        )
    return (
        f"I don’t recognize “{symbol}” as a standard chord name.\n\n"
        "Try a clearer chord symbol such as:\n"
        "- G\n"
        "- F\n"
        "- Em\n"
        "- G7\n"
        "- B9\n"
        "- G/F for a slash chord\n\n"
        "Once the chord name is clear, I can map it to E9 positions."
    )


def slash_chord_clarification_answer(symbol: str) -> str:
    chord, bass = symbol.split("/", 1)
    return (
        f"{symbol} is a slash chord: {chord} over a {bass} bass note.\n\n"
        "The current fretboard visualizer maps chord positions by the chord sound on the steel, but it does not yet generate a separate bass-note/slash-chord diagram. "
        f"If you want the chord part, ask for {chord} positions. If you need the bass-note function, say what key or progression you are in."
    )


def minor_chord_answer_for_question(question: str) -> str | None:
    request = minor_chord_location_request_for_question(question)
    if request is None:
        return None
    key = request.normalized_key
    return minor_position_answer(
        key,
        prefix=(
            f"A {key} minor chord means the notes {minor_triad_spelling_for_answer(key)}: "
            "root, minor 3rd, and perfect 5th."
        ),
    )


def chord_concept_request_for_question(question: str) -> ChordConceptRequest | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    root_pattern = r"(?P<root>[a-g](?:#|b)?)"
    patterns = (
        rf"^what(?:'s|’s| is)\s+(?:a|an)?\s*{root_pattern}\s+(?P<quality>major|minor)?\s*chord\s+(?:even\s+)?mean$",
        rf"^what\s+does\s+(?:a|an)?\s*{root_pattern}\s+(?P<quality>major|minor)?\s*chord\s+mean$",
        rf"^what\s+notes\s+are\s+in\s+(?:a|an)?\s*{root_pattern}\s+(?P<quality>major|minor)?\s*chord$",
        rf"^what\s+makes\s+(?:a|an)?\s*{root_pattern}\s+minor\s+chord\s+minor$",
        rf"^what\s+makes\s+(?:a|an)?\s*{root_pattern}\s+major\s+chord\s+major$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            requested_root = normalize_requested_root(match.group("root"))
            quality = normalize_chord_quality(match.groupdict().get("quality") or "")
            if not quality and " minor chord" in q:
                quality = "minor"
            if not quality and " major chord" in q:
                quality = "major"
            if not quality:
                quality = "major"
            if quality not in {"major", "minor"}:
                return None
            return ChordConceptRequest(
                requested_root=requested_root,
                normalized_key=normalize_key(requested_root),
                quality=quality,
            )
    return None


def chord_concept_answer_for_question(question: str) -> str | None:
    request = chord_concept_request_for_question(question)
    if request is None:
        return None
    key = request.normalized_key
    if request.quality == "minor":
        third = transpose(key, 3)
        fifth = transpose(key, 7)
        prefix = (
            f"An {key} minor chord means the notes {key}-{third}-{fifth}: "
            "root, minor 3rd, and perfect 5th. What makes it minor is the lowered 3rd."
        )
        return minor_position_answer(key, prefix=prefix)

    third = transpose(key, 4)
    fifth = transpose(key, 7)
    payload = major_positions(key).to_payload()
    visible = [position for position in payload["positions"] if position["visibleByDefault"]]
    lines = [
        f"A {key} major chord means the notes {key}-{third}-{fifth}: root, major 3rd, and perfect 5th.",
        "",
        f"On E9, common {key} major starter positions include:",
    ]
    for position in visible:
        controls = " + ".join([*position["pedals"], *position["levers"]]) or "no pedals"
        lines.append(f"- {fret_label(position['fret'])} with {controls}: {position['role']}, grip {position['grip']}.")
    lines.extend(
        [
            "",
            "Think of the chord name as the target sound; the fretboard positions are different ways to spell the same root-3rd-5th idea on the steel.",
        ]
    )
    return "\n".join(lines)


def generic_chord_concept_answer_for_question(question: str) -> str | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if re.search(r"^what\s+makes\s+(?:something|a chord)\s+(?:a\s+)?minor\s+chord(?:\s+minor)?$", q):
        return (
            "A minor chord is a three-note chord built from root, minor 3rd, and perfect 5th. "
            "The minor color comes from lowering the 3rd by one half-step compared with a major chord. "
            "For example, E minor is E-G-B, while E major is E-G#-B."
        )
    if re.search(r"^what(?:'s|’s| is)\s+(?:a\s+)?1\s+chord$", q):
        return (
            "A 1 chord is the home chord of the key, also called the tonic. "
            "In G, the 1 chord is G major; in C, it is C major. "
            "Give me the key and I can map the 1 chord to E9 fretboard positions."
        )
    if re.search(r"^why\s+is\s+a\+b\s+a\s+chord$", q):
        return (
            "A+B is not a chord by itself; it is a pedal combination that changes the notes under a grip. "
            "At the right fret, those changed notes can spell a major chord. "
            "For example, on standard E9, A+B at the 10th fret gives a G major position on common grips."
        )
    return None


def minor_triad_spelling(root: str) -> str:
    return f"{normalize_key(root)}-{transpose(normalize_key(root), 3)}-{transpose(normalize_key(root), 7)}"


def minor_triad_spelling_for_answer(root: str) -> str:
    key = normalize_key(root)
    minor_third = FLAT_NOTES[(semitone_for_note(key) + 3) % 12]
    fifth = CANONICAL_NOTES[(semitone_for_note(key) + 7) % 12]
    return f"{key}-{minor_third}-{fifth}"


def minor_position_answer(root: str, *, prefix: str | None = None) -> str:
    key = normalize_key(root)
    payload = minor_positions(key).to_payload()
    visible = [position for position in payload["positions"] if position["visibleByDefault"]]
    lines = [
        prefix or f"On E9, useful deterministic {key} minor positions include:",
    ]
    if prefix:
        lines.extend(["", f"Useful {key} minor positions on E9:"])
    for position in visible:
        controls = " + ".join([*position["pedals"], *position["levers"]]) or "no pedals"
        lines.append(f"- {fret_label(position['fret'])} with {controls}: {position['role']}, grip {position['grip']}.")
    lines.extend(
        [
            "",
            "Minor-position support is pitch-math based and still limited to validated common grips, so treat this as a practical map rather than every possible minor voicing.",
        ]
    )
    return "\n".join(lines)


def two_minor_function_answer(request: FunctionChordRequest) -> str:
    payload = minor_positions(request.root).to_payload()
    positions = payload["positions"]
    bc = next(
        (
            position
            for position in positions
            if position["family"] == "b_c_minor" and position["fret"] == 3 and position["grip"] == "4-5-6"
        ),
        None,
    )
    a_pedal = next(
        (
            position
            for position in positions
            if position["family"] == "a_pedal_minor" and position["fret"] == 8 and position["grip"] == "4-5-6"
        ),
        None,
    )
    five_dominant = transpose(request.key, 7)
    lines = [
        f"{request.requested_function} chord is {request.root} minor ({minor_triad_spelling(request.root)}).",
        f"A 2m is 1-b3-5 built on scale degree 2 in {request.key}.",
        "",
        "Practical E9 options:",
    ]
    if bc is not None:
        lines.append(f"- {fret_label(bc['fret'])} with B+C pedals: {request.root} minor on grip {bc['grip']}.")
    if a_pedal is not None:
        lines.append(f"- {fret_label(a_pedal['fret'])} with A pedal: {request.root} minor on grip {a_pedal['grip']}.")
    lines.extend(
        [
            f"- In {request.key}, this can connect into {five_dominant}7, the 5-dominant chord in {request.key}, for a 2m-to-5 movement.",
            "",
            "The fretboard payload shows only pitch-validated minor positions; it does not use SGF snippets to decide the chord.",
        ]
    )
    return "\n".join(lines)


def fretboard_payload_for_question(question: str) -> dict | None:
    """Return MVP fretboard visualization data for a narrow curated question set."""
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    b9_payload = e_lower_578_b9_payload_for_question(q)
    if b9_payload is not None:
        return b9_payload
    e_lower_grip_payload = e_lower_grip_payload_for_question(q)
    if e_lower_grip_payload is not None:
        return e_lower_grip_payload
    e_lower_payload = e_lower_578_payload_for_question(q)
    if e_lower_payload is not None:
        return e_lower_payload
    functional_payload = functional_pocket_payload_for_question(q)
    if functional_payload is not None:
        return functional_payload
    if q == "show me a 1-4-5 in g":
        return get_fretboard_examples("i_iv_v", "G")
    function_chord_payload = function_chord_payload_for_question(q)
    if function_chord_payload is not None:
        return function_chord_payload
    minor_chord_payload = minor_chord_payload_for_question(q)
    if minor_chord_payload is not None:
        return minor_chord_payload
    chord_concept_payload = chord_concept_payload_for_question(q)
    if chord_concept_payload is not None:
        return chord_concept_payload
    major_request = major_chord_location_request_for_question(q)
    if major_request is not None:
        return get_fretboard_examples("major_positions", major_request.normalized_key)
    if q == "show me common grips for g":
        return get_fretboard_examples("common_grips", "G")
    return None


def major_chord_location_key_for_question(question: str) -> str | None:
    """Extract a deterministic major-key request from narrow location prompts."""
    request = major_chord_location_request_for_question(question)
    return request.normalized_key if request else None


def major_chord_location_request_for_question(question: str) -> MajorChordLocationRequest | None:
    """Extract a deterministic major-chord request and preserve spelling."""
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    patterns = (
        r"^where are (?:some )?places to play (?:a|an)?\s*([a-g](?:#|b)?)(?:\s+(?:major|major chords?|chords?))?$",
        r"^where(?: all)? can i play (?:a|an)?\s*([a-g](?:#|b)?)(?:\s+(?:major|major chords?|chords?))?$",
        r"^where(?: all)? can i play (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^where can i find (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^how do i play (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^how do i play (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)? on e9$",
        r"^how do i plan (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)$",
        r"^how do i make (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^where is ([a-g](?:#|b)?) major$",
        r"^where is ([a-g](?:#|b)?)(?: major)? on e9$",
        r"^where is (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)(?: on e9)?$",
        r"^where are (?:my\s+)?([a-g](?:#|b)?) (?:major )?chord positions(?: on e9)?$",
        r"^show me ([a-g](?:#|b)?) (?:major )?positions$",
        r"^show me ([a-g](?:#|b)?) positions on e9$",
        r"^show me ([a-g](?:#|b)?) (?:major )?chord positions(?: on e9)?$",
        r"^show me (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)$",
        r"^what frets give me (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^show me places to play (?:a|an)?\s*([a-g](?:#|b)?)(?: major)?(?: chord)?$",
        r"^where are ([a-g](?:#|b)?) major positions on e9$",
        r"^how do i play (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)? across (?:the )?fretboard(?: of (?:the )?e9| on e9)?$",
        r"^([a-g](?:#|b)?) major across (?:the )?e9 fretboard$",
        r"^([a-g](?:#|b)?) (?:major )?chord across (?:the )?e9 fretboard$",
        r"^show me ([a-g](?:#|b)?) major with a\+b$",
        r"^show me ([a-g](?:#|b)?) major with a\+f$",
        r"^show me (?:more|advanced) ([a-g](?:#|b)?) (?:major )?chord positions$",
        r"^show me ([a-g](?:#|b)?) (?:major )?chord positions with levers$",
        r"^what grips can i use for ([a-g](?:#|b)?) major$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            requested_root = normalize_requested_root(match.group(1))
            return MajorChordLocationRequest(
                requested_root=requested_root,
                normalized_key=normalize_key(requested_root),
            )
    return None


def unsupported_chord_location_request_for_question(question: str) -> UnsupportedChordLocationRequest | None:
    """Detect location-style chord questions with unsupported non-major qualities."""
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    prefixes = (
        r"where(?: all)? can i play",
        r"where can i find",
        r"where is",
        r"how do i play",
        r"how do i plan",
        r"how do i make",
        r"show me places to play",
        r"show me",
        r"what frets give me",
    )
    prefix_match = re.match(rf"^(?:{'|'.join(prefixes)})\s+(?:a|an)?\s*(?P<body>.+)$", q)
    if not prefix_match:
        return None
    body = prefix_match.group("body")
    body = re.sub(r"\bon e9\b$", "", body).strip()
    body = re.sub(r"\bpositions?\b$", "", body).strip()
    body = re.sub(r"\bchord\b$", "", body).strip()
    quality_match = re.match(
        r"^(?P<root>[a-g](?:#|b)?)(?P<compact>m(?!ajor)|7|dim|aug)?(?:\s+(?P<quality>minor|minor\s+7|m7|dominant(?:\s+7)?|seventh|7|diminished|dim|augmented|aug|sus(?:2|4)?|major\s+7|maj7))?$",
        body,
    )
    if not quality_match:
        return None
    compact = quality_match.group("compact") or ""
    quality = quality_match.group("quality") or compact
    if not quality:
        return None
    requested_root = normalize_requested_root(quality_match.group("root"))
    return UnsupportedChordLocationRequest(
        requested_root=requested_root,
        normalized_key=normalize_key(requested_root),
        quality=normalize_chord_quality(quality),
    )


def normalize_chord_quality(quality: str) -> str:
    q = re.sub(r"\s+", " ", (quality or "").strip().lower())
    aliases = {
        "m": "minor",
        "m7": "minor 7",
        "7": "dominant 7",
        "seventh": "dominant 7",
        "dominant": "dominant 7",
        "dominant 7": "dominant 7",
        "dim": "diminished",
        "aug": "augmented",
        "maj7": "major 7",
    }
    return aliases.get(q, q)


def normalize_requested_root(root: str) -> str:
    normalized = (root or "").strip().replace("♯", "#").replace("♭", "b")
    if not normalized:
        raise ValueError(f"Unsupported key: {root}")
    letter = normalized[:1].upper()
    accidental = normalized[1:]
    if accidental not in {"", "#", "b"}:
        raise ValueError(f"Unsupported key: {root}")
    display = f"{letter}{accidental}"
    if note_lookup_key(display) not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported key: {root}")
    return display


def note_lookup_key(note: str) -> str:
    return (note or "").strip().replace("♯", "#").replace("♭", "b").upper().replace("B", "B", 1)


def semitone_for_note(note: str) -> int:
    return NOTE_TO_SEMITONE[note_lookup_key(note)]


def normalize_intent(intent: str) -> FretboardIntent:
    normalized = (intent or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "major": "major_positions",
        "major_chord": "major_positions",
        "major_chords": "major_positions",
        "positions": "major_positions",
        "minor_position": "minor_positions",
        "minor_positions": "minor_positions",
        "minor_chord": "minor_positions",
        "minor_chords": "minor_positions",
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
    if normalized not in {"major_positions", "minor_positions", "minor_grips", "i_iv_v", "common_grips"}:
        raise ValueError(f"Unsupported fretboard example intent: {intent}")
    return normalized  # type: ignore[return-value]


def normalize_key(key: str) -> str:
    normalized = normalize_requested_root(key or "G")
    return CANONICAL_NOTES[semitone_for_note(normalized)]


def reference_position(
    *,
    position_id: str,
    label: str,
    root: str,
    quality: str,
    position_kind: str,
    fret: int,
    strings: tuple[int, ...],
    pedals: tuple[str, ...] = (),
    levers: tuple[str, ...] = (),
    color: str,
    role: str,
    family: str,
    tier: str,
    color_role: str,
    visible_by_default: bool,
    sort_order: int,
    explanation: str,
    function: str = "",
    key_context: str = "",
    why_use_it: str = "",
    caveats: tuple[str, ...] = (),
) -> FretboardPosition:
    controls = pedals + levers
    notes = resolve_grip_notes(fret, strings, controls)
    intervals = {string: interval_for_note(root, note) for string, note in notes.items()}
    required = CHORD_INTERVALS.get(CHORD_ALIASES.get(quality, quality), ())
    present = set(intervals.values())
    omitted = tuple(interval for interval in required if interval not in present)
    added = tuple(interval for interval in present if interval not in required)
    quality_key = CHORD_ALIASES.get(quality, quality)
    return FretboardPosition(
        id=position_id,
        label=label,
        root=root,
        quality=quality_key,
        position_kind=position_kind
        if position_kind != "auto"
        else position_kind_for_classification(
            family=family,
            quality=quality_key,
            is_full_chord=bool(required) and not omitted and not added,
            is_partial=bool(required) and (bool(omitted) or bool(added)),
            is_rootless=bool(required) and "1" not in present,
            added_intervals=added,
        ),
        fret=fret,
        strings=strings,
        grip=grip_label(strings),
        pedals=pedals,
        levers=levers,
        color=color,
        role=role,
        function=function,
        key_context=key_context,
        notes=notes,
        intervals=intervals,
        explanation=explanation,
        family=family,
        tier=tier,
        color_role=color_role,
        visible_by_default=visible_by_default,
        sort_order=sort_order,
        omitted_intervals=omitted,
        added_intervals=added,
        is_full_chord=bool(required) and not omitted and not added,
        is_partial=bool(required) and (bool(omitted) or bool(added)),
        is_rootless=bool(required) and "1" not in present,
        why_use_it=why_use_it or explanation,
        validation_status="pitch_validated",
        caveats=caveats,
    )


def major_positions(key: str) -> FretboardVisualizationPayload:
    if not supports_standard_major_position_changes(USER_E9_COPEDENT):
        raise ValueError("Structured user E9 copedent does not support MVP major-position changes")
    key = normalize_key(key)
    open_fret = open_major_fret(key)
    af_fret = af_major_fret(key)
    ab_fret = ab_major_fret(key)
    candidates: list[FretboardPosition] = []

    def add_grip_family(
        *,
        fret: int,
        pedals: tuple[str, ...] = (),
        levers: tuple[str, ...] = (),
        starter_family: str,
        grip_family: str,
        starter_role: str,
        grip_role_prefix: str,
        color: str,
        color_role: str,
        sort_base: int,
        explanation_prefix: str,
        starter_suffix_prefix: str,
        tier: str = "beginner",
        grip_tier: str = "common",
        required_starter: bool = False,
        variant_suffix: str = "",
        starter_visible_by_default: bool = True,
    ) -> None:
        for index, grip in enumerate(COMMON_E9_VISUAL_GRIPS):
            is_starter = grip == (4, 5, 6)
            suffix = f"{starter_suffix_prefix}-{fret}{variant_suffix}" if is_starter else f"{starter_suffix_prefix}-grip-{grip_label(grip)}-{fret}{variant_suffix}"
            candidate = major_position_candidate(
                key=key,
                suffix=suffix,
                fret=fret,
                strings=grip,
                pedals=pedals,
                levers=levers,
                color=color if is_starter else "reference",
                role=starter_role if is_starter else f"{grip_role_prefix} grip {grip_label(grip)}",
                family=starter_family if is_starter else grip_family,
                tier=tier if is_starter else grip_tier,
                color_role=color_role if is_starter else "reference",
                visible_by_default=is_starter and starter_visible_by_default,
                sort_order=sort_base + index * 10,
                explanation=f"{explanation_prefix} on strings {grip_label(grip)}.",
                function="I",
                key_context=key,
                why_use_it=f"Use this as a {key} major grip in the {starter_role.lower()} family.",
            )
            if is_starter and required_starter:
                candidates.append(require_major_position(candidate, key=key, role=starter_role))
            elif candidate is not None:
                candidates.append(candidate)

    add_grip_family(
        fret=open_fret,
        starter_family="open_no_pedals",
        grip_family="open_grip",
        starter_role="Open position",
        grip_role_prefix="Open-position",
        color="primary",
        color_role="primary",
        sort_base=20,
        explanation_prefix=f"No-pedal fret {open_fret} gives {indefinite_article(key)} {key} major grip",
        starter_suffix_prefix="open",
        required_starter=True,
    )
    if open_fret + 12 <= 24:
        add_grip_family(
            fret=open_fret + 12,
            starter_family="open_octave",
            grip_family="open_octave_grip",
            starter_role="Open octave alternate",
            grip_role_prefix="Open-octave alternate",
            color="primary",
            color_role="primary",
            sort_base=70,
            explanation_prefix=f"No-pedal fret {open_fret + 12} gives an octave-up {key} major grip",
            starter_suffix_prefix="open",
            tier="alternate",
            grip_tier="alternate",
            variant_suffix="-octave",
            starter_visible_by_default=False,
        )
    add_grip_family(
        fret=af_fret,
        pedals=("A",),
        levers=("F",),
        starter_family="a_f",
        grip_family="a_f_grip",
        starter_role="A+F position",
        grip_role_prefix="A+F",
        color="secondary",
        color_role="secondary",
        sort_base=100,
        explanation_prefix=f"A+F at fret {af_fret} gives another {key} major grip",
        starter_suffix_prefix="af",
        required_starter=True,
    )
    if af_fret + 12 <= 24:
        add_grip_family(
            fret=af_fret + 12,
            pedals=("A",),
            levers=("F",),
            starter_family="a_f_octave",
            grip_family="a_f_octave_grip",
            starter_role="A+F octave alternate",
            grip_role_prefix="A+F octave alternate",
            color="secondary",
            color_role="secondary",
            sort_base=150,
            explanation_prefix=f"A+F at fret {af_fret + 12} gives an octave-up {key} major grip",
            starter_suffix_prefix="af",
            tier="alternate",
            grip_tier="alternate",
            variant_suffix="-octave",
            starter_visible_by_default=False,
        )
    add_grip_family(
        fret=ab_fret,
        pedals=("A", "B"),
        starter_family="a_b",
        grip_family="a_b_grip",
        starter_role="A+B position",
        grip_role_prefix="A+B",
        color="alternate",
        color_role="alternate",
        sort_base=180,
        explanation_prefix=f"A+B at fret {ab_fret} gives another {key} major grip",
        starter_suffix_prefix="ab",
        required_starter=True,
    )
    if ab_fret + 12 <= 24:
        add_grip_family(
            fret=ab_fret + 12,
            pedals=("A", "B"),
            starter_family="a_b_octave",
            grip_family="a_b_octave_grip",
            starter_role="A+B octave alternate",
            grip_role_prefix="A+B octave alternate",
            color="alternate",
            color_role="alternate",
            sort_base=230,
            explanation_prefix=f"A+B at fret {ab_fret + 12} gives an octave-up {key} major grip",
            starter_suffix_prefix="ab",
            tier="alternate",
            grip_tier="alternate",
            variant_suffix="-octave",
            starter_visible_by_default=False,
        )

    lower_octave_ab_fret = ab_fret % 12
    if lower_octave_ab_fret != ab_fret and lower_octave_ab_fret < ab_fret:
        add_grip_family(
            fret=lower_octave_ab_fret,
            pedals=("A", "B"),
            starter_family="a_b_lower_octave",
            grip_family="a_b_lower_octave_grip",
            starter_role="A+B lower-octave alternate",
            grip_role_prefix="A+B lower-octave alternate",
            color="alternate",
            color_role="alternate",
            sort_base=260,
            explanation_prefix=f"A+B at fret {lower_octave_ab_fret} gives a lower-octave {key} major alternate grip",
            starter_suffix_prefix="ab",
            tier="alternate",
            grip_tier="alternate",
            variant_suffix="-lower-octave",
            starter_visible_by_default=False,
        )

    e_lower_fret = fret_for_root(key, NOTE_TO_SEMITONE["B"])
    for index, fret in enumerate((e_lower_fret, e_lower_fret + 12)):
        if fret > 24:
            continue
        octave_sort_offset = index * 125
        for grip_index, grip in enumerate(E_LOWER_MAJOR_GRIPS):
            family = "e_lower_578" if grip == E_LOWER_578_GRIP else "e_lower_major"
            e_lower = major_position_candidate(
                key=key,
                suffix=f"e-lower-{grip_label(grip)}-{fret}",
                fret=fret,
                strings=grip,
                levers=("E",),
                color="reference",
                role=f"E-lower {grip_label(grip)} major color",
                family=family,
                tier="advanced",
                color_role="e-lower",
                visible_by_default=False,
                sort_order=55 + grip_index + octave_sort_offset,
                explanation=f"E-lower at fret {fret} gives a {key} major {grip_label(grip)} grip when strings 4 and 8 lower from E to D#/Eb.",
                function="I",
                key_context=key,
                why_use_it=f"Use this as an E-lower {key} major pocket after you know the starter positions.",
                caveats=("Assumes E-lower lowers strings 4 and 8 E to D#/Eb.",),
            )
            if e_lower is not None:
                candidates.append(e_lower)

    dominant_fret = (e_lower_fret - 2) % 12
    for octave_index, fret in enumerate((dominant_fret, dominant_fret + 12)):
        if fret > 24:
            continue
        for grip_index, grip in enumerate(E_LOWER_DOMINANT_GRIPS):
            dominant = major_position_candidate(
                key=key,
                quality="dominant9",
                suffix=f"e-lower-dominant-{grip_label(grip)}-{fret}",
                fret=fret,
                strings=grip,
                levers=("E",),
                color="reference",
                role=f"E-lower {grip_label(grip)} dominant color",
                family="e_lower_dominant_pocket",
                tier="advanced",
                color_role="dominant",
                visible_by_default=False,
                sort_order=500 + octave_index * 100 + grip_index * 10,
                explanation=f"E-lower at fret {fret} gives a rootless/partial {key} dominant-9 color on strings {grip_label(grip)}.",
                function="dominant",
                key_context=key,
                why_use_it=f"Use this as a dominant color that wants to resolve back toward {key} or a nearby tonic.",
                caveats=("This is a partial/rootless dominant color, not a full dominant chord by itself.",),
            )
            if dominant is not None:
                candidates.append(dominant)

    positions = tuple(sorted(candidates, key=lambda position: position.sort_order))
    return FretboardVisualizationPayload(
        title=f"{key} major positions on E9",
        subtitle=f"Common places to find {key} major.",
        key=key,
        positions=positions,
    )


def minor_positions(key: str) -> FretboardVisualizationPayload:
    """Return pitch-validated minor triad positions for a requested minor root."""
    key = normalize_key(key)
    family_specs = (
        ("a_pedal_minor", "A-pedal minor position", ("A",), (), "primary", "primary", 20),
        ("e_lower_minor", "E-lower minor position", (), ("E",), "secondary", "secondary", 120),
        ("b_c_minor", "B+C minor position", ("B", "C"), (), "alternate", "alternate", 220),
        ("open_minor", "Open minor grip", (), (), "reference", "reference", 320),
        ("a_b_minor", "A+B minor color", ("A", "B"), (), "reference", "reference", 420),
        ("a_f_minor", "A+F minor color", ("A",), ("F",), "reference", "reference", 520),
    )
    candidates: list[FretboardPosition] = []
    visible_families: set[str] = set()
    for family, role_prefix, pedals, levers, color, color_role, sort_base in family_specs:
        for fret in range(25):
            for grip_index, grip in enumerate(COMMON_E9_VISUAL_GRIPS):
                candidate = major_position_candidate(
                    key=key,
                    quality="minor",
                    suffix=f"minor-{family}-{grip_label(grip)}-{fret}",
                    fret=fret,
                    strings=grip,
                    pedals=pedals,
                    levers=levers,
                    color=color,
                    role=f"{role_prefix} {grip_label(grip)}",
                    family=family,
                    tier="common",
                    color_role=color_role,
                    visible_by_default=False,
                    sort_order=sort_base + fret * 10 + grip_index,
                    explanation=f"{role_prefix} at fret {fret} gives an {key} minor grip on strings {grip_label(grip)}.",
                    function="minor",
                    key_context=key,
                    why_use_it=f"Use this as a pitch-validated {key} minor grip.",
                    allow_added_intervals=False,
                )
                if candidate is None or not candidate.is_full_chord:
                    continue
                visible = (
                    family in {"a_pedal_minor", "e_lower_minor", "b_c_minor"}
                    and grip == (4, 5, 6)
                    and family not in visible_families
                )
                if visible:
                    visible_families.add(family)
                candidates.append(
                    replace(
                        candidate,
                        tier="beginner" if visible else "common",
                        visible_by_default=visible,
                        role=role_prefix if visible else f"{role_prefix} {grip_label(grip)}",
                        color=color if visible else "reference",
                        color_role=color_role if visible else "reference",
                        why_use_it=(
                            f"Use this as a starter {key} minor position."
                            if visible
                            else f"Use this as another pitch-validated {key} minor grip."
                        ),
                    )
                )

    positions = tuple(sorted(candidates, key=lambda position: position.sort_order))
    if not positions:
        raise ValueError(f"No pitch-validated {key} minor positions were generated")
    return FretboardVisualizationPayload(
        title=f"{key} minor positions on E9",
        subtitle=f"Pitch-validated common-grip positions for {key} minor.",
        key=key,
        positions=positions,
    )


def minor_grips(key: str) -> FretboardVisualizationPayload:
    key = normalize_key(key)
    relative_minor = CANONICAL_NOTES[(NOTE_TO_SEMITONE[key] + 9) % 12]
    open_fret = open_major_fret(key)
    positions = (
        reference_position(
            position_id=f"{slug(relative_minor)}m-relative-minor-{open_fret}",
            label=f"{relative_minor} minor",
            root=relative_minor,
            quality="minor",
            position_kind="reference",
            fret=open_fret,
            strings=(5, 6, 8),
            color="primary",
            role=f"Relative minor grip from {key} open position",
            family="minor_grip",
            tier="reference",
            color_role="primary",
            visible_by_default=True,
            sort_order=10,
            explanation=f"Strings 5-6-8 at fret {open_fret} are shown as a nearby minor-family reference grip.",
        ),
        reference_position(
            position_id=f"{slug(relative_minor)}m-e-lower-{open_fret}",
            label=f"{relative_minor} minor color",
            root=relative_minor,
            quality="minor",
            position_kind="reference",
            fret=open_fret,
            strings=(4, 5, 6),
            levers=("E",),
            color="secondary",
            role="E-lower minor-family color",
            family="minor_grip",
            tier="reference",
            color_role="secondary",
            visible_by_default=True,
            sort_order=20,
            explanation=f"E-lower at fret {open_fret} is shown as a minor-family reference color.",
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
    home_fret = open_major_fret(key)
    positions = (
        reference_position(
            position_id=f"{slug(key)}-i-open-{home_fret}",
            label=f"{key} major",
            root=key,
            quality="major",
            position_kind="starter",
            fret=home_fret,
            strings=(4, 5, 6),
            color="primary",
            role="I chord, open position",
            family="i_iv_v",
            tier="beginner",
            color_role="primary",
            visible_by_default=True,
            sort_order=10,
            explanation=f"{key} is the I chord at fret {home_fret} with no pedals.",
        ),
        reference_position(
            position_id=f"{slug(four)}-iv-ab-{home_fret}",
            label=f"{four} major",
            root=four,
            quality="major",
            position_kind="starter",
            fret=home_fret,
            strings=(4, 5, 6),
            pedals=("A", "B"),
            color="secondary",
            role="IV chord, A+B at the I fret",
            family="i_iv_v",
            tier="beginner",
            color_role="secondary",
            visible_by_default=True,
            sort_order=20,
            explanation=f"{four} is the IV chord at fret {home_fret} with A+B.",
        ),
        reference_position(
            position_id=f"{slug(five)}-v-ab-{home_fret + 2}",
            label=f"{five} major",
            root=five,
            quality="major",
            position_kind="starter",
            fret=home_fret + 2,
            strings=(4, 5, 6),
            pedals=("A", "B"),
            color="alternate",
            role="V chord, A+B two frets above I",
            family="i_iv_v",
            tier="beginner",
            color_role="alternate",
            visible_by_default=True,
            sort_order=30,
            explanation=f"{five} is the V chord two frets above the I position with A+B.",
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
        reference_position(
            position_id=f"{slug(key)}-grip-{grip_label(grip)}-{fret}",
            label=f"{key} major grip {grip_label(grip)}",
            root=key,
            quality="major",
            position_kind="grip_reference",
            fret=fret,
            strings=grip,
            color="reference",
            role="Common grip",
            family="grip_reference",
            tier="reference",
            color_role="reference",
            visible_by_default=True,
            sort_order=index * 10,
            explanation=f"Grip {grip_label(grip)} at fret {fret} is shown as a common E9 grip reference.",
        )
        for index, grip in enumerate(COMMON_E9_VISUAL_GRIPS)
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
    return open_major_fret(key) + AB_MAJOR_OFFSET


def af_major_fret(key: str) -> int:
    return open_major_fret(key) + AF_MAJOR_OFFSET


def fret_for_root(key: str, root_at_zero: int) -> int:
    return (semitone_for_note(normalize_key(key)) - root_at_zero) % 12


def transpose(key: str, semitones: int) -> str:
    return CANONICAL_NOTES[(semitone_for_note(normalize_key(key)) + semitones) % 12]


def fret_label(fret: int) -> str:
    if fret == 0:
        return "fret 0"
    suffix = "th"
    if fret % 100 not in {11, 12, 13}:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(fret % 10, "th")
    return f"{fret}{suffix} fret"


def slug(key: str) -> str:
    return normalize_key(key).lower().replace("#", "sharp")
