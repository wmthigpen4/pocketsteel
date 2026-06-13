"""Deterministic E9 fretboard logic for visualization payloads.

This module deliberately keeps the fretboard positions in the rules layer. It
uses the confirmed user E9 copedent and pitch math to emit render-safe
highlight data without relying on RAG snippets or hand-entered claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
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

FretboardIntent = Literal["major_positions", "minor_grips", "i_iv_v", "common_grips"]


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
    notes: dict[str, str] | None = None
    intervals: dict[str, str] | None = None
    explanation: str = ""
    family: str = "major_position"
    tier: str = "beginner"
    color_role: str = ""
    visible_by_default: bool = True
    sort_order: int = 0
    omitted_intervals: tuple[str, ...] = ()
    is_full_chord: bool = False
    is_partial: bool = False
    is_rootless: bool = False
    validation_status: str = "pitch_validated"
    caveats: tuple[str, ...] = ()

    def to_position_payload(self) -> dict:
        color_role = self.color_role or self.color
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
            "family": self.family,
            "tier": self.tier,
            "colorRole": color_role,
            "visibleByDefault": self.visible_by_default,
            "sortOrder": self.sort_order,
            "omittedIntervals": list(self.omitted_intervals),
            "isFullChord": self.is_full_chord,
            "isPartial": self.is_partial,
            "isRootless": self.is_rootless,
            "validationStatus": self.validation_status,
            "caveats": list(self.caveats),
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


def classify_voicing(root: str, quality: str, notes: dict[str, str]) -> dict[str, object] | None:
    """Classify notes against a target chord quality without trusting labels."""
    required = chord_required_intervals(quality)
    allowed = set(required)
    intervals: dict[str, str] = {}
    for string, note in notes.items():
        interval = interval_for_note(root, note)
        if interval not in allowed:
            return None
        intervals[str(string)] = interval

    present = set(intervals.values())
    if len(present) < 2:
        return None

    omitted = tuple(interval for interval in required if interval not in present)
    is_full = not omitted
    return {
        "intervals": intervals,
        "omitted_intervals": omitted,
        "is_full_chord": is_full,
        "is_partial": not is_full,
        "is_rootless": "1" not in present,
    }


def classify_grip_against_root(
    root: str,
    quality: str,
    *,
    fret: int,
    strings: tuple[int, ...],
    controls: tuple[str, ...],
) -> tuple[dict[str, str], dict[str, str], tuple[str, ...], bool, bool, bool] | None:
    notes = resolve_grip_notes(fret, strings, controls)
    classification = classify_voicing(root, quality, notes)
    if classification is None:
        return None
    return (
        notes,
        classification["intervals"],  # type: ignore[return-value]
        classification["omitted_intervals"],  # type: ignore[return-value]
        bool(classification["is_full_chord"]),
        bool(classification["is_partial"]),
        bool(classification["is_rootless"]),
    )


def major_triad_match(key: str, fret: int, strings: tuple[int, ...], controls: tuple[str, ...]) -> tuple[dict[str, str], dict[str, str]] | None:
    """Return note/interval annotations when the candidate is a complete major triad."""
    classification = classify_grip_against_root(key, "major", fret=fret, strings=strings, controls=controls)
    if classification is None:
        return None
    notes, intervals, omitted, _, _, _ = classification
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
    caveats: tuple[str, ...] = (),
) -> FretboardPosition | None:
    controls = pedals + levers
    classification = classify_grip_against_root(key, quality, fret=fret, strings=strings, controls=controls)
    if classification is None:
        return None
    notes, intervals, omitted_intervals, is_full_chord, is_partial, is_rootless = classification
    return FretboardPosition(
        id=f"{slug(key)}-{suffix}",
        label=f"{key} {quality_label(quality)}",
        root=key,
        quality=chord_quality_key(quality),
        position_kind=position_kind_for_family(family, visible_by_default),
        fret=fret,
        strings=strings,
        grip=grip_label(strings),
        pedals=pedals,
        levers=levers,
        color=color,
        role=role,
        notes=notes,
        intervals=intervals,
        explanation=explanation,
        family=family,
        tier=tier,
        color_role=color_role,
        visible_by_default=visible_by_default,
        sort_order=sort_order,
        omitted_intervals=omitted_intervals,
        is_full_chord=is_full_chord,
        is_partial=is_partial,
        is_rootless=is_rootless,
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
    if normalized_intent == "minor_grips":
        return minor_grips(normalized_key).to_payload()
    if normalized_intent == "i_iv_v":
        return i_iv_v_examples(normalized_key).to_payload()
    if normalized_intent == "common_grips":
        return common_grip_examples(normalized_key).to_payload()
    raise ValueError(f"Unsupported fretboard example intent: {intent}")


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


def e_lower_578_position_at_fret(fret: int) -> FretboardPosition:
    classification = best_grip_classification(fret, E_LOWER_578_GRIP, ("E",))
    root = str(classification["root"] or "unknown")
    quality = str(classification["quality"] or "unknown")
    notes = classification["notes"]
    intervals = classification["intervals"]
    omitted = classification["omitted_intervals"]
    quality_text = quality_label(quality) if quality in CHORD_INTERVALS else quality
    if root == "unknown" or quality == "unknown":
        role = "Pitch-checked E-lower 5-7-8 grip"
        label = f"5-7-8 E-lower at fret {fret}"
        explanation = "Pitch math did not classify this grip as a simple supported chord quality."
    else:
        role = f"E-lower 5-7-8 {quality_text} grip"
        label = f"{root} {quality_text}"
        explanation = f"With E lowered at fret {fret}, strings 5-7-8 resolve by pitch math to a {root} {quality_text} grip."
    return FretboardPosition(
        id=f"{slug(root) if root != 'unknown' else 'unknown'}-e-lower-5-7-8-{fret}",
        label=label,
        root=root,
        quality=quality,
        position_kind="grip_analysis",
        fret=fret,
        strings=E_LOWER_578_GRIP,
        grip=grip_label(E_LOWER_578_GRIP),
        levers=("E",),
        color="reference",
        role=role,
        notes=notes if isinstance(notes, dict) else {},
        intervals=intervals if isinstance(intervals, dict) else {},
        explanation=explanation,
        family="e_lower_578",
        tier="advanced",
        color_role="reference",
        visible_by_default=True,
        sort_order=10,
        omitted_intervals=omitted if isinstance(omitted, tuple) else tuple(),
        is_full_chord=bool(classification["is_full_chord"]),
        is_partial=bool(classification["is_partial"]),
        is_rootless=bool(classification["is_rootless"]),
        validation_status="pitch_validated",
        caveats=("Assumes E-lower lowers strings 4 and 8 E to D#/Eb.",),
    )


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


def e_lower_578_answer_for_question(question: str) -> str | None:
    request = e_lower_578_request_for_question(question)
    if request is None:
        return None
    position = e_lower_578_position_at_fret(request.fret)
    notes = position.notes or {}
    intervals = position.intervals or {}
    note_list = ", ".join(f"string {string} = {note}" for string, note in notes.items())
    interval_list = ", ".join(f"string {string} = {interval}" for string, interval in intervals.items())
    if position.root == "unknown":
        return (
            f"At fret {request.fret} with E lowered, strings 5-7-8 resolve to: {note_list}. "
            "I do not classify that as a complete major, dominant, or minor-7 grip from the supported pitch rules."
        )
    quality_text = quality_label(position.quality) if position.quality in CHORD_INTERVALS else position.quality
    lines = [
        f"At fret {request.fret} with E lowered, strings 5-7-8 resolve to {position.root} {quality_text}.",
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
    if position.root == "D" and position.quality == "major":
        lines.append("- Against a B root, those notes can also sound like a rootless B minor 7 color because the B root is omitted.")
    return "\n".join(lines)


def fretboard_payload_for_question(question: str) -> dict | None:
    """Return MVP fretboard visualization data for a narrow curated question set."""
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    e_lower_payload = e_lower_578_payload_for_question(q)
    if e_lower_payload is not None:
        return e_lower_payload
    major_request = major_chord_location_request_for_question(q)
    if major_request is not None:
        return get_fretboard_examples("major_positions", major_request.normalized_key)
    if q == "show me a 1-4-5 in g":
        return get_fretboard_examples("i_iv_v", "G")
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
        r"^where(?: all)? can i play (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^where can i find (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^how do i play (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^how do i make (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^where is ([a-g](?:#|b)?) major$",
        r"^where is ([a-g](?:#|b)?)(?: major)? on e9$",
        r"^show me ([a-g](?:#|b)?) (?:major )?positions$",
        r"^what frets give me (?:a|an)?\s*([a-g](?:#|b)?)(?: (?:major )?chord)?$",
        r"^show me places to play (?:a|an)?\s*([a-g](?:#|b)?)(?: major)?(?: chord)?$",
        r"^where are ([a-g](?:#|b)?) major positions on e9$",
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
    caveats: tuple[str, ...] = (),
) -> FretboardPosition:
    controls = pedals + levers
    notes = resolve_grip_notes(fret, strings, controls)
    intervals = {string: interval_for_note(root, note) for string, note in notes.items()}
    required = CHORD_INTERVALS.get(CHORD_ALIASES.get(quality, quality), ())
    present = set(intervals.values())
    omitted = tuple(interval for interval in required if interval not in present)
    return FretboardPosition(
        id=position_id,
        label=label,
        root=root,
        quality=CHORD_ALIASES.get(quality, quality),
        position_kind=position_kind,
        fret=fret,
        strings=strings,
        grip=grip_label(strings),
        pedals=pedals,
        levers=levers,
        color=color,
        role=role,
        notes=notes,
        intervals=intervals,
        explanation=explanation,
        family=family,
        tier=tier,
        color_role=color_role,
        visible_by_default=visible_by_default,
        sort_order=sort_order,
        omitted_intervals=omitted,
        is_full_chord=bool(required) and not omitted,
        is_partial=bool(required) and bool(omitted),
        is_rootless=bool(required) and "1" not in present,
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
        lower_octave: bool = False,
        starter_visible_by_default: bool = True,
    ) -> None:
        for index, grip in enumerate(COMMON_E9_VISUAL_GRIPS):
            is_starter = grip == (4, 5, 6)
            lower_suffix = "-lower-octave" if lower_octave else ""
            suffix = f"{starter_suffix_prefix}-{fret}{lower_suffix}" if is_starter else f"{starter_suffix_prefix}-grip-{grip_label(grip)}-{fret}{lower_suffix}"
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
            lower_octave=True,
            starter_visible_by_default=False,
        )

    e_lower_fret = fret_for_root(key, NOTE_TO_SEMITONE["B"])
    for index, fret in enumerate((e_lower_fret, e_lower_fret + 12)):
        if fret > 24:
            continue
        e_lower = major_position_candidate(
            key=key,
            suffix=f"e-lower-5-7-8-{fret}",
            fret=fret,
            strings=E_LOWER_578_GRIP,
            levers=("E",),
            color="reference",
            role="E-lower 5-7-8 major color",
            family="e_lower_578",
            tier="advanced",
            color_role="reference",
            visible_by_default=False,
            sort_order=55 + index * 125,
            explanation=f"E-lower at fret {fret} gives a {key} major 5-7-8 grip when strings 4 and 8 lower from E to D#/Eb.",
            caveats=("Assumes E-lower lowers strings 4 and 8 E to D#/Eb.",),
        )
        if e_lower is not None:
            candidates.append(e_lower)

    positions = tuple(sorted(candidates, key=lambda position: position.sort_order))
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


def slug(key: str) -> str:
    return normalize_key(key).lower().replace("#", "sharp")
