"""Deterministic E9 fretboard logic for visualization payloads.

This module deliberately keeps the fretboard positions in the rules layer. It
uses the confirmed user E9 copedent and pitch math to emit render-safe
highlight data without relying on RAG snippets or hand-entered claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pocketsteel.fretboard_contracts import (
    AB_MAJOR_OFFSET,
    AF_MAJOR_OFFSET,
    CANONICAL_LEVER_LABELS,
    CANONICAL_NOTES,
    CANONICAL_PEDAL_LABELS,
    CHORD_ADDED_INTERVALS,
    CHORD_ALIASES,
    CHORD_INTERVALS,
    CHORD_ROOT_RE,
    COMMON_E9_VISUAL_GRIPS,
    DEFAULT_PEDAL_LEVER_LABELS as DEFAULT_PEDAL_LEVER_LABELS,
    E9_OPEN_STRINGS,
    E_LOWER_578_GRIP,
    E_LOWER_DOMINANT_GRIPS,
    E_LOWER_MAJOR_GRIPS,
    FRETBOARD_PAYLOAD_TYPE,
    FUNCTION_QUALITIES,
    INTERVAL_NAMES,
    MAJOR_SCALE_INTERVALS,
    NOTE_TO_SEMITONE,
    OPEN_MAJOR_ROOT,
    OPEN_STRING_ABSOLUTE_PITCHES,
    POSITION_COLORS,
    ROMAN_FUNCTIONS,
    ROOTLESS_CHORD_QUALITY_ALIASES,
    ChordConceptRequest,
    ChordSymbolGuardrailRequest,
    ELower578Request,
    ELowerGripRequest,
    FretStringPedalRequest,
    FretboardIntent,
    FunctionChordRequest,
    FunctionalPocketRequest,
    MajorChordLocationRequest,
    MinorChordLocationRequest,
    MultiChordLocationRequest,
    RootlessChordQualityRequest,
    SpecificMajorGripRequest,
    UnsupportedChordLocationRequest,
    display_major_key_for_request,
    display_minor_key_for_request,
)

from pocketsteel.music_text import normalize_accidental_symbols, normalize_spelled_accidentals
from pocketsteel.user_copedent import USER_E9_COPEDENT, apply_changes, supports_standard_major_position_changes
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
        voicing_metadata = voicing_metadata_for_position(self)
        payload: dict = {
            "id": self.id,
            "label": self.label,
            "chordRoot": self.root,
            "chordQuality": self.quality,
            "chordTones": voicing_metadata["chordTones"],
            "lowestSoundingNote": voicing_metadata["lowestSoundingNote"],
            "lowestChordToneRole": voicing_metadata["lowestChordToneRole"],
            "voicingType": voicing_metadata["voicingType"],
            "inversionLabel": voicing_metadata["inversionLabel"],
            "inversionExplanation": voicing_metadata["inversionExplanation"],
            "root": self.root,
            "quality": self.quality,
            "positionKind": self.position_kind,
            "fret": self.fret,
            "strings": list(self.strings),
            "grip": self.grip,
            "intervalsLowToHigh": voicing_metadata["intervalsLowToHigh"],
            "isRootPosition": voicing_metadata["isRootPosition"],
            "isInversion": voicing_metadata["isInversion"],
            "isPartialVoicing": voicing_metadata["isPartialVoicing"],
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
        controls = tuple(position.get("pedals", [])) + tuple(position.get("levers", []))
        if controls and not controls_affect_selected_strings(controls, tuple(strings)):
            raise ValueError(f"Fretboard position {position_id} has inert pedal/lever label")
        if position.get("color") not in POSITION_COLORS:
            raise ValueError(f"Fretboard position {position_id} has unknown color role")
        if not isinstance(position.get("family"), str) or not position.get("family"):
            raise ValueError(f"Fretboard position {position_id} is missing family")
        if not isinstance(position.get("root"), str) or not position.get("root"):
            raise ValueError(f"Fretboard position {position_id} is missing root")
        if not isinstance(position.get("quality"), str) or not position.get("quality"):
            raise ValueError(f"Fretboard position {position_id} is missing quality")
        if position.get("chordRoot") != position.get("root"):
            raise ValueError(f"Fretboard position {position_id} has inconsistent chordRoot")
        if position.get("chordQuality") != position.get("quality"):
            raise ValueError(f"Fretboard position {position_id} has inconsistent chordQuality")
        if not isinstance(position.get("chordTones"), list) or any(
            not isinstance(tone, str) for tone in position.get("chordTones", [])
        ):
            raise ValueError(f"Fretboard position {position_id} has invalid chordTones")
        if not isinstance(position.get("lowestSoundingNote"), str):
            raise ValueError(f"Fretboard position {position_id} has invalid lowestSoundingNote")
        if not isinstance(position.get("lowestChordToneRole"), str):
            raise ValueError(f"Fretboard position {position_id} has invalid lowestChordToneRole")
        if position.get("voicingType") not in {
            "root_position",
            "first_inversion",
            "second_inversion",
            "third_inversion",
            "partial",
            "rootless",
            "color_voicing",
        }:
            raise ValueError(f"Fretboard position {position_id} has invalid voicingType")
        if not isinstance(position.get("inversionLabel"), str) or not position.get("inversionLabel"):
            raise ValueError(f"Fretboard position {position_id} has invalid inversionLabel")
        if not isinstance(position.get("inversionExplanation"), str) or not position.get("inversionExplanation"):
            raise ValueError(f"Fretboard position {position_id} has invalid inversionExplanation")
        if not isinstance(position.get("intervalsLowToHigh"), list) or any(
            not isinstance(interval, str) for interval in position.get("intervalsLowToHigh", [])
        ):
            raise ValueError(f"Fretboard position {position_id} has invalid intervalsLowToHigh")
        if not isinstance(position.get("isRootPosition"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid isRootPosition")
        if not isinstance(position.get("isInversion"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid isInversion")
        if not isinstance(position.get("isPartialVoicing"), bool):
            raise ValueError(f"Fretboard position {position_id} has invalid isPartialVoicing")
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


def control_affects_selected_strings(label: str, strings: tuple[int, ...]) -> bool:
    """Return true when a displayed pedal/lever changes at least one played string."""
    changed_notes = notes_for_controls((label,))
    selected = set(strings)
    return any(
        string in selected
        and semitone_for_copedent_note(changed_notes[string]) != semitone_for_copedent_note(E9_OPEN_STRINGS[string])
        for string in E9_OPEN_STRINGS
    )


def controls_affect_selected_strings(controls: tuple[str, ...], strings: tuple[int, ...]) -> bool:
    return all(control_affects_selected_strings(control, strings) for control in controls)


def note_at_fret(open_note: str, fret: int) -> str:
    return note_name_for_pitch(semitone_for_copedent_note(open_note) + fret)


def interval_for_note(root: str, note: str) -> str:
    return INTERVAL_NAMES[(semitone_for_note(note) - semitone_for_note(root)) % 12]


def absolute_pitch_for_string(string: int, fret: int, controls: tuple[str, ...]) -> int:
    changed_notes = notes_for_controls(controls)
    open_pitch = OPEN_STRING_ABSOLUTE_PITCHES[string]
    open_pitch_class = semitone_for_copedent_note(E9_OPEN_STRINGS[string])
    changed_pitch_class = semitone_for_copedent_note(changed_notes[string])
    delta = (changed_pitch_class - open_pitch_class) % 12
    if delta > 6:
        delta -= 12
    return open_pitch + delta + fret


INTERVAL_ROLE_LABELS: dict[str, str] = {
    "1": "root",
    "b3": "minor 3rd",
    "3": "major 3rd",
    "5": "5th",
    "b7": "7th",
    "7": "7th",
    "2/9": "9th",
    "6/13": "13th",
}


def voicing_metadata_for_position(position: FretboardPosition) -> dict[str, object]:
    notes = dict(position.notes or {})
    intervals = dict(position.intervals or {})
    controls = tuple(position.pedals + position.levers)
    strings_low_to_high = sorted(
        position.strings,
        key=lambda string: (absolute_pitch_for_string(string, position.fret, controls), string),
    )
    intervals_low_to_high: list[str] = []
    lowest_interval = ""
    lowest_note = ""
    for string in strings_low_to_high:
        interval = intervals.get(str(string), "")
        note = notes.get(str(string), "")
        if interval and note:
            intervals_low_to_high.append(f"{interval} on string {string} ({note})")
            if not lowest_interval:
                lowest_interval = interval
                lowest_note = note

    required_intervals = chord_required_intervals(position.quality) if position.quality in CHORD_INTERVALS else tuple()
    chord_tones = [
        f"{interval} ({INTERVAL_ROLE_LABELS.get(interval, interval)})"
        for interval in required_intervals
        if interval in set(intervals.values())
    ]
    if not chord_tones:
        chord_tones = [
            f"{interval} ({INTERVAL_ROLE_LABELS.get(interval, interval)})"
            for interval in sorted(set(intervals.values()), key=lambda interval: intervals_low_to_high.index(next(item for item in intervals_low_to_high if item.startswith(interval + ' '))) if any(item.startswith(interval + " ") for item in intervals_low_to_high) else 99)
        ]

    voicing_type, inversion_label, is_root_position, is_inversion = classify_inversion_type(
        lowest_interval=lowest_interval,
        is_partial=position.is_partial,
        is_rootless=position.is_rootless,
        required_intervals=required_intervals,
    )
    lowest_role = INTERVAL_ROLE_LABELS.get(lowest_interval, lowest_interval or "unknown")
    return {
        "chordTones": chord_tones,
        "lowestSoundingNote": lowest_note,
        "lowestChordToneRole": lowest_role,
        "voicingType": voicing_type,
        "inversionLabel": inversion_label,
        "inversionExplanation": inversion_explanation(
            position=position,
            lowest_note=lowest_note,
            lowest_role=lowest_role,
            voicing_type=voicing_type,
        ),
        "intervalsLowToHigh": intervals_low_to_high,
        "isRootPosition": is_root_position,
        "isInversion": is_inversion,
        "isPartialVoicing": position.is_partial,
    }


def classify_inversion_type(
    *,
    lowest_interval: str,
    is_partial: bool,
    is_rootless: bool,
    required_intervals: tuple[str, ...],
) -> tuple[str, str, bool, bool]:
    if is_rootless:
        return "rootless", "Rootless voicing", False, False
    if is_partial:
        return "partial", "Partial voicing", False, False
    if lowest_interval == "1":
        return "root_position", "Root position", True, False
    if lowest_interval in {"3", "b3"}:
        return "first_inversion", "1st inversion", False, True
    if lowest_interval == "5":
        return "second_inversion", "2nd inversion", False, True
    if lowest_interval in {"b7", "7"} and any(interval in required_intervals for interval in ("b7", "7")):
        return "third_inversion", "3rd inversion", False, True
    return "color_voicing", "Color voicing", False, False


def inversion_explanation(
    *,
    position: FretboardPosition,
    lowest_note: str,
    lowest_role: str,
    voicing_type: str,
) -> str:
    quality_text = quality_label(position.quality) if position.quality in CHORD_INTERVALS else position.quality
    if voicing_type == "rootless":
        return (
            f"This {position.root} {quality_text} voicing omits the root, so it is labeled rootless rather than as an inversion."
        )
    if voicing_type == "partial":
        omitted = ", ".join(position.omitted_intervals) or "none"
        added = ", ".join(position.added_intervals) or "none"
        return (
            f"This is a partial {position.root} {quality_text} voicing; omitted interval(s): {omitted}; "
            f"added color(s): {added}."
        )
    if voicing_type == "root_position":
        return f"The chord root {lowest_note} is the lowest sounding chord tone."
    if voicing_type == "first_inversion":
        return f"The {lowest_role} ({lowest_note}) is the lowest sounding chord tone."
    if voicing_type == "second_inversion":
        return f"The 5th ({lowest_note}) is the lowest sounding chord tone."
    if voicing_type == "third_inversion":
        return f"The 7th ({lowest_note}) is the lowest sounding chord tone."
    return f"The lowest sounding chord tone is {lowest_role} ({lowest_note}); use this as a color voicing."


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
    if controls and not controls_affect_selected_strings(controls, strings):
        return None
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
    label = position_label_for_classification(
        key,
        quality_key,
        omitted_intervals=omitted_intervals,
        added_intervals=added_intervals,
        is_partial=is_partial,
        is_rootless=is_rootless,
    )
    if is_partial or is_rootless:
        color_role = "partial-rootless"
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
        label=label,
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
        "diminished": "diminished",
        "dominant7": "dominant 7",
        "dominant9": "dominant 9",
        "minor7": "minor 7",
    }.get(chord_quality_key(quality), quality)


def position_label_for_classification(
    root: str,
    quality: str,
    *,
    omitted_intervals: tuple[str, ...],
    added_intervals: tuple[str, ...],
    is_partial: bool,
    is_rootless: bool,
) -> str:
    if quality == "major" and (is_partial or is_rootless):
        omitted = set(omitted_intervals)
        added = set(added_intervals)
        if omitted == {"3"} and "2/9" in added:
            return f"{root}5/add9 (no 3rd)"
        if "3" in omitted and not is_rootless:
            return f"{root} major partial (no 3rd)"
        if is_rootless:
            return f"{root} major color (no root)"
        return f"{root} major partial"
    return f"{root} {quality_label(quality)}"


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
        r"^(?:show me|where are|give me)\s+(?P<function>v|5|five)(?:\s+chord)?\s+pockets?\s+in\s+(?P<key>[a-g](?:##|bb|#|b)?)$",
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
    match = re.search(r"\b(?:in\s+the\s+key\s+of|key\s+of|in)\s+([a-g](?:##|bb|#|b)?)\b", q)
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
    q = normalize_chord_intent_text(question)
    if not q:
        return None
    e9_context = chord_context_pattern()
    optional_context = rf"(?:\s+{e9_context})?"
    patterns = (
        rf"^where is (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chords?)?{optional_context}$",
        rf"^where are (?:some\s+)?(?:places\s+to\s+play\s+)?(?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chords?)?{optional_context}$",
        rf"^where can i (?:play|find) (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chords?)?{optional_context}$",
        rf"^how do (?:i|you) play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chord)?{optional_context}$",
        rf"^show me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chord| positions?)?{optional_context}$",
        r"^show me ([a-g](?:##|bb|#|b)?)(?:m|[- ]minor) on (?:the )?fretboard$",
        rf"^give me ([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chord)? positions{optional_context}$",
        rf"^positions for ([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chords?)?{optional_context}$",
        rf"^what frets give me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:m|[- ]minor)(?: chord)?{optional_context}$",
        rf"^what(?:'s| is) (?:a|an)?\s*([a-g](?:##|bb|#|b)?)\s+(?:minor|min|m)\s+look like{optional_context}$",
        rf"^what does (?:a|an)?\s*([a-g](?:##|bb|#|b)?)\s+(?:minor|min|m)\s+look like{optional_context}$",
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


def multi_chord_location_request_for_question(question: str) -> MultiChordLocationRequest | None:
    q = normalize_chord_intent_text(question)
    if not q:
        return None
    patterns = (
        r"^show me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)\s+major\s+and\s+(?:a|an)?\s*(?:\1\s+)?minor(?:\s+chords?)?(?:\s+on\s+(?:the\s+)?(?:e9|fretboard))?$",
        r"^show me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)\s+minor\s+and\s+(?:a|an)?\s*(?:\1\s+)?major(?:\s+chords?)?(?:\s+on\s+(?:the\s+)?(?:e9|fretboard))?$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            root = normalize_key(normalize_requested_root(match.group(1)))
            if "minor and" in q:
                return MultiChordLocationRequest(root=root, qualities=("minor", "major"))
            return MultiChordLocationRequest(root=root, qualities=("major", "minor"))
    return None


def multi_chord_payload_for_question(question: str) -> dict | None:
    request = multi_chord_location_request_for_question(question)
    if request is None:
        return None
    payloads = {
        "major": major_positions(request.root),
        "minor": minor_positions(request.root),
    }
    positions: list[FretboardPosition] = []
    for quality in request.qualities:
        positions.extend(payloads[quality].positions)
    return FretboardVisualizationPayload(
        title=f"{request.root} major and {request.root} minor positions on E9",
        subtitle=f"Combined pitch-validated {request.root} major and {request.root} minor positions.",
        key=request.root,
        positions=tuple(positions),
    ).to_payload()


def mixed_a_minor_c_major_payload_for_question(question: str) -> dict | None:
    q = normalize_chord_intent_text(question)
    if not re.search(r"\ba\s+minor\b", q) or not re.search(r"\bc\s+major\b", q):
        return None
    if not re.search(r"\b(?:show|where|play|chords?|positions?|fretboard)\b", q):
        return None
    positions = list(minor_positions("A").positions)
    positions.extend(major_positions("C").positions)
    return FretboardVisualizationPayload(
        title="A minor and C major positions on E9",
        subtitle="Combined pitch-validated A minor and C major positions.",
        key="A minor / C major",
        positions=tuple(positions),
    ).to_payload()


def mixed_a_minor_bflat_major_question(question: str) -> bool:
    q = normalize_chord_intent_text(question)
    return bool(
        re.search(r"\ba\s+minor\b", q)
        and re.search(r"\bbb(?:\s+major)?\b", q)
        and re.search(r"\b(?:show|where|play|chords?|positions?|fretboard)\b", q)
    )


def mixed_a_minor_bflat_major_payload_for_question(question: str) -> dict | None:
    if not mixed_a_minor_bflat_major_question(question):
        return None
    positions = list(minor_positions("A").positions)
    positions.extend(major_positions("Bb").positions)
    payload = FretboardVisualizationPayload(
        title="A minor and Bb major positions on E9",
        subtitle="Combined pitch-validated A minor and Bb major positions.",
        key="A minor / Bb major",
        positions=tuple(positions),
    ).to_payload()
    return payload


def mixed_a_minor_bflat_major_answer_for_question(question: str) -> str | None:
    if not mixed_a_minor_bflat_major_question(question):
        return None
    return (
        "I’m reading that as A minor and B-flat major.\n\n"
        "A minor = A-C-E: root, minor 3rd, and perfect 5th.\n\n"
        "B-flat major = Bb-D-F: root, major 3rd, and perfect 5th.\n\n"
        "The fretboard view can show supported E9 locations for those two sounds. Use the labels to keep the minor sound and the B-flat major sound separate."
    )


def multi_chord_answer_for_question(question: str) -> str | None:
    request = multi_chord_location_request_for_question(question)
    if request is None:
        return None
    root = request.root
    lines = [
        f"Here are both {root} major and {root} minor on E9.",
        "",
        f"{root} major means {root}-{transpose(root, 4)}-{transpose(root, 7)}: root, major 3rd, and perfect 5th.",
        f"{root} minor means {minor_triad_spelling_for_answer(root)}: root, minor 3rd, and perfect 5th.",
        "",
        f"Useful {root} major starter positions:",
    ]
    major_visible = [position for position in major_positions(root).to_payload()["positions"] if position["visibleByDefault"]]
    for position in major_visible:
        controls = " + ".join([*position["pedals"], *position["levers"]]) or "no pedals"
        lines.append(f"- {fret_label(position['fret'])} with {controls}: {position['role']}, grip {position['grip']}.")
    lines.extend(["", f"Useful {root} minor positions:"])
    minor_visible = [position for position in minor_positions(root).to_payload()["positions"] if position["visibleByDefault"]]
    for position in minor_visible:
        controls = " + ".join([*position["pedals"], *position["levers"]]) or "no pedals"
        lines.append(f"- {fret_label(position['fret'])} with {controls}: {position['role']}, grip {position['grip']}.")
    lines.extend(
        [
            "",
            "The fretboard combines the major and minor cards in one view here. Use the card labels to separate the two sounds.",
        ]
    )
    return "\n".join(lines)


def fret_string_pedal_request_for_question(question: str) -> FretStringPedalRequest | None:
    q = re.sub(r"\s+", " ", (question or "").strip().lower())
    if not q or "string" not in q or "fret" not in q:
        return None
    strings_match = re.search(r"\bstrings?\s+(?P<strings>\d{1,2}(?:\s*(?:-|,|and|\s)\s*\d{1,2})*)\b", q)
    if not strings_match:
        return None
    strings = parse_grip_strings(strings_match.group("strings"))
    if strings is None:
        return None
    fret_match = re.search(r"\b(?:on|at)\s+(?:the\s+)?(?P<fret>\d{1,2})(?:st|nd|rd|th)?\s+fret\b", q) or re.search(
        r"\bfret\s+(?P<fret>\d{1,2})\b", q
    )
    if not fret_match:
        return None
    fret = int(fret_match.group("fret"))
    if fret < 0 or fret > 24:
        return None
    pedals: list[str] = []
    levers: list[str] = []
    if re.search(r"\ba\s*(?:\+|&)\s*b\b|\ba\s+and\s+b\b|\ba\s+pedal\b.*\bb\s+pedal\b|\bb\s+pedal\b.*\ba\s+pedal\b", q):
        pedals.extend(["A", "B"])
    else:
        if re.search(r"\ba\s+pedal\b|\bpedal\s+a\b|\ba\s+engaged\b", q):
            pedals.append("A")
        if re.search(r"\bb\s+pedal\b|\bpedal\s+b\b|\bb\s+engaged\b", q):
            pedals.append("B")
    if re.search(r"\bb\s*(?:\+|&)\s*c\b|\bb\s+and\s+c\b", q):
        for pedal in ("B", "C"):
            if pedal not in pedals:
                pedals.append(pedal)
    elif re.search(r"\bc\s+pedal\b|\bpedal\s+c\b|\bc\s+engaged\b", q):
        pedals.append("C")
    if re.search(r"\be[-\s]?lower\b|\be\s+lowered\b|\blower(?:ed)?\s+e\b", q):
        levers.append("E")
    if re.search(r"\bf\s+lever\b|\be[-\s]?raise\b", q):
        levers.append("F")
    if re.search(r"\bvertical\b|\blkv\b|\bbb\s+lever\b", q):
        levers.append("V")
    return FretStringPedalRequest(
        fret=fret,
        strings=strings,
        pedals=tuple(dict.fromkeys(pedals)),
        levers=tuple(dict.fromkeys(levers)),
    )


def classify_notes_as_simple_chord(notes: dict[str, str]) -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    for root in CANONICAL_NOTES.values():
        for quality in ("major", "minor", "dominant7", "minor7"):
            classification = classify_voicing(root, quality, notes)
            if classification is None:
                continue
            present = set(classification["intervals"].values())  # type: ignore[union-attr]
            full_bonus = 100 if classification["is_full_chord"] else 0
            quality_bonus = {"major": 40, "minor": 40, "dominant7": 20, "minor7": 20}[quality]
            candidates.append(
                {
                    "root": root,
                    "quality": quality,
                    "score": full_bonus + quality_bonus + len(present),
                    **classification,
                }
            )
    if not candidates:
        return {"root": "", "quality": "unknown", "intervals": {}, "omitted_intervals": (), "is_full_chord": False}
    return sorted(candidates, key=lambda candidate: int(candidate["score"]), reverse=True)[0]


def diagnostic_root_display(root: str, quality: str) -> tuple[str, str]:
    if root == "D#" and quality == "major":
        return "Eb", "Eb major, also called D# major enharmonically"
    return root, f"{root} {quality_label(quality) if quality in CHORD_INTERVALS else quality}"


def diagnostic_spelling(root: str, quality: str) -> str:
    if root == "D#" and quality == "major":
        return "Eb-G-Bb"
    intervals = CHORD_INTERVALS.get(CHORD_ALIASES.get(quality, quality), ())
    if not intervals:
        return ""
    semitone_offsets = {"1": 0, "b3": 3, "3": 4, "5": 7, "b7": 10, "2/9": 2}
    return "-".join(transpose(root, semitone_offsets[interval]) for interval in intervals if interval in semitone_offsets)


def diagnostic_controls_text(request: FretStringPedalRequest) -> str:
    if request.pedals == ("B", "C") and not request.levers:
        return "B+C pedals"
    if request.pedals == ("A", "B") and not request.levers:
        return "A+B pedals"
    if len(request.pedals) == 1 and not request.levers:
        return f"{request.pedals[0]} pedal"
    return " + ".join((*request.pedals, *request.levers)) or "no pedals or levers"


def fret_string_pedal_position(request: FretStringPedalRequest) -> FretboardPosition:
    notes = resolve_grip_notes(request.fret, request.strings, request.controls)
    classification = classify_notes_as_simple_chord(notes)
    root = str(classification.get("root") or "unknown")
    quality = str(classification.get("quality") or "unknown")
    intervals = classification.get("intervals") if isinstance(classification.get("intervals"), dict) else {}
    omitted = classification.get("omitted_intervals") if isinstance(classification.get("omitted_intervals"), tuple) else tuple()
    added = classification.get("added_intervals") if isinstance(classification.get("added_intervals"), tuple) else tuple()
    _, display_label = diagnostic_root_display(root, quality)
    controls_text = diagnostic_controls_text(request)
    return FretboardPosition(
        id=f"diagnostic-{grip_label(request.strings)}-{request.fret}-{'-'.join(request.controls) or 'open'}".lower().replace("+", "plus"),
        label=display_label,
        root=root,
        quality=CHORD_ALIASES.get(quality, quality),
        position_kind="full_chord_position" if bool(classification.get("is_full_chord")) else "partial_chord_grip",
        fret=request.fret,
        strings=request.strings,
        grip=grip_label(request.strings),
        pedals=request.pedals,
        levers=request.levers,
        color="primary",
        role=f"Pitch check for strings {grip_label(request.strings)} at fret {request.fret}",
        function="diagnostic",
        key_context=root,
        notes=notes,
        intervals=intervals,  # type: ignore[arg-type]
        explanation=f"Strings {grip_label(request.strings)} at fret {request.fret} with {controls_text} resolve by pitch math to {display_label}.",
        family="fret_string_pedal_diagnostic",
        tier="reference",
        color_role="primary",
        visible_by_default=True,
        sort_order=10,
        omitted_intervals=omitted,  # type: ignore[arg-type]
        added_intervals=added,  # type: ignore[arg-type]
        is_full_chord=bool(classification.get("is_full_chord")),
        is_partial=bool(classification.get("is_partial")),
        is_rootless=bool(classification.get("is_rootless")),
        why_use_it="Use this card as a direct pitch check for the exact strings, fret, and controls in the question.",
        validation_status="pitch_validated",
    )


def fret_string_pedal_answer_for_question(question: str) -> str | None:
    request = fret_string_pedal_request_for_question(question)
    if request is None:
        return None
    position = fret_string_pedal_position(request)
    notes = position.notes or {}
    if position.root == "D#" and position.quality == "major":
        display_notes = {"D#": "Eb/D#", "A#": "Bb/A#", "G": "G"}
    else:
        display_notes = {}
    note_parts = [f"string {string} = {display_notes.get(note, note)}" for string, note in notes.items()]
    note_text = "; ".join(note_parts)
    display_root, display_label = diagnostic_root_display(position.root, position.quality)
    spelling = diagnostic_spelling(position.root, position.quality)
    controls_text = diagnostic_controls_text(request)
    voiced = "-".join(notes[str(string)] for string in request.strings)
    if position.root == "A" and position.quality == "minor":
        return (
            f"You get A minor: A-C-E, likely voiced as {voiced} across strings {grip_label(request.strings)}.\n\n"
            f"String check at the {fret_label(request.fret)} with {controls_text}:\n"
            + "\n".join(f"- {part}" for part in note_parts)
        )
    if position.root == "D#" and position.quality == "major":
        return (
            "You get Eb major, also called D# major enharmonically: Eb-G-Bb.\n\n"
            f"String check at the {fret_label(request.fret)} with {controls_text}:\n"
            + "\n".join(f"- {part}" for part in note_parts)
        )
    if spelling:
        return (
            f"You get {display_label}: {spelling}.\n\n"
            f"String check at the {fret_label(request.fret)} with {controls_text}:\n"
            + "\n".join(f"- {part}" for part in note_parts)
        )
    return (
        f"Those strings at fret {request.fret} with {controls_text} give these notes: {note_text}.\n\n"
        "I do not classify that exact grip as a simple major, minor, dominant, or minor-7 chord yet."
    )


def fret_string_pedal_payload_for_question(question: str) -> dict | None:
    request = fret_string_pedal_request_for_question(question)
    if request is None:
        return None
    position = fret_string_pedal_position(request)
    return FretboardVisualizationPayload(
        title=f"{position.label} pitch check on E9",
        subtitle=f"Strings {grip_label(request.strings)} at fret {request.fret}.",
        key=position.root,
        positions=(position,),
    ).to_payload()


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
    payload = minor_positions(request.normalized_key).to_payload()
    display_key = display_minor_key_for_request(request)
    if display_key != request.normalized_key:
        payload = dict(payload)
        payload["title"] = f"{display_key} minor positions on E9"
        payload["key"] = display_key
        payload["subtitle"] = str(payload.get("subtitle", "")).replace(request.normalized_key, display_key)
        payload["description"] = str(payload.get("description", "")).replace(request.normalized_key, display_key)
    return payload


def chord_concept_payload_for_question(question: str) -> dict | None:
    return None


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
    if rootless_chord_quality_request_for_question(question) is not None:
        return None
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
        r"^how do i play (?:a|an)?\s*(?P<symbol>[a-g][a-z#b/0-9/]+)$",
        r"^where is (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^what is (?:a|an)?\s*(?P<symbol>[a-z][a-z#b/0-9]*)\s+chord$",
        r"^what is (?P<symbol>[a-g][a-z#b/0-9/]+)$",
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
    if rest.startswith(("#", "b")):
        accidental = rest[:1]
        quality = rest[1:]
    else:
        accidental = ""
        quality = rest
        if len(symbol) == 2 and symbol[:1].lower() in "abcdefg" and symbol[1:].lower() in "abcdefg":
            return symbol.upper()
    quality_aliases = {
        "m": "m",
        "min": "m",
        "minor": "m",
        "maj": "maj",
        "major": "",
        "dim": "dim",
        "dim7": "dim7",
        "aug": "aug",
        "sus": "sus",
        "sus2": "sus2",
        "sus4": "sus4",
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


def normalize_rootless_chord_quality_alias(text: str) -> RootlessChordQualityRequest | None:
    q = (text or "").strip().lower().replace("♯", "#").replace("♭", "b")
    q = q.replace("’", "'")
    q = re.sub(r"\bseven\b", "7", q)
    q = re.sub(r"\bfive\b", "5", q)
    q = re.sub(r"\bseventh\b", "seventh", q)
    q = re.sub(r"\bchords?\b", "", q)
    q = re.sub(r"\bquality\b", "", q)
    q = re.sub(r"\bthe\b", "", q)
    q = re.sub(r"\ba(?:n)?\b", "", q)
    q = re.sub(r"\s*\^\s*", "^", q)
    q = re.sub(r"\s*\+\s*", "+", q)
    q = re.sub(r"[-_]+", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    compact = q.replace(" ", "")
    return ROOTLESS_CHORD_QUALITY_ALIASES.get(q) or ROOTLESS_CHORD_QUALITY_ALIASES.get(compact)


def rootless_chord_quality_request_for_question(question: str) -> RootlessChordQualityRequest | None:
    q = re.sub(r"[?!.,;:]+", " ", question or "")
    q = re.sub(r"\s+", " ", q).strip().lower()
    if not q:
        return None
    patterns = (
        r"^what(?:'s| is)\s+(?P<body>.+)$",
        r"^what\s+does\s+(?P<body>.+?)\s+mean$",
        r"^how\s+do\s+i\s+(?:play|make|use)\s+(?P<body>.+)$",
        r"^tell\s+me\s+about\s+(?P<body>.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        body = match.group("body").strip()
        body = re.sub(r"\bon\s+(?:e9|pedal\s+steel|the\s+e9)\b$", "", body).strip()
        request = normalize_rootless_chord_quality_alias(body)
        if request is not None:
            return request
    return normalize_rootless_chord_quality_alias(q)


def chord_quality_definition_lines(quality: str) -> list[str]:
    normalized = normalize_chord_quality(quality)
    if normalized in {"sus", "sus2", "sus4", "suspended"}:
        return [
            "A suspended chord replaces the 3rd with a suspended tone, so it has an unresolved sound.",
            "- sus4 = root, 4th, 5th.",
            "- sus2 = root, 2nd, 5th.",
            "- There is no 3rd, so the sound is neither plain major nor plain minor until it resolves.",
        ]
    if normalized in {"dominant7", "dominant 7"}:
        return [
            "A dominant 7 chord is built from root, major 3rd, perfect 5th, and flat 7th.",
            "In the key of G, D7 is the V7 chord: D-F#-A-C.",
            "On E9, dominant sounds can be full, partial, or rootless depending on the grip and pedal/lever setup, so the key/root matters before mapping positions.",
        ]
    if normalized == "diminished":
        return [
            "A diminished triad is built from root, flat 3rd, and flat 5th.",
            "Players often use diminished sounds as passing or tension chords because the flat 5 wants to resolve.",
        ]
    if normalized in {"diminished7", "diminished 7", "dim7"}:
        return [
            "A diminished 7 chord is built from root, flat 3rd, flat 5th, and double-flat 7th.",
            "That symmetrical tension makes diminished-7 sounds useful for passing movement and connecting nearby chord positions.",
        ]
    if normalized == "augmented":
        return [
            "An augmented chord is built from root, major 3rd, and sharp 5th.",
            "It creates tension and often leads by half-step motion into a more stable chord.",
        ]
    return []


def rootless_chord_quality_answer_for_question(question: str) -> str | None:
    request = rootless_chord_quality_request_for_question(question)
    if request is None:
        return None
    lines = chord_quality_definition_lines(request.quality)
    if not lines:
        return None
    if request.is_function:
        lines = [
            f"{request.label} means a dominant 7 chord built on scale degree 5.",
            *lines,
            "Give me the key before I map it to E9 positions; for example, in G the V7 is D7.",
        ]
    else:
        lines = [
            f"{request.label.capitalize()} is a standard chord quality.",
            *lines,
            "Give me a root or key before I map it to E9 positions, for example Gsus4, D7, or the V7 chord in G.",
        ]
    return "\n".join(lines)


def minor_chord_answer_for_question(question: str) -> str | None:
    request = minor_chord_location_request_for_question(question)
    if request is None:
        return None
    key = request.normalized_key
    display_key = display_minor_key_for_request(request)
    if request.requested_root == "D#":
        prefix = "D# minor is D#-F#-A#. You can also think of it as Eb minor: Eb-Gb-Bb."
    elif display_key != key:
        prefix = f"{display_key} minor is {minor_triad_spelling_for_answer(display_key)}: root, minor 3rd, and perfect 5th. You can also think of it as {key} minor on the pitch map."
    else:
        prefix = f"{key} minor is {minor_triad_spelling_for_answer(key)}: root, minor 3rd, and perfect 5th."
    return minor_position_answer(
        key,
        prefix=prefix,
    )


def chord_concept_request_for_question(question: str) -> ChordConceptRequest | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not q:
        return None
    root_pattern = r"(?P<root>[a-g](?:##|bb|#|b)?)"
    patterns = (
        rf"^what(?:'s|’s| is)\s+(?:a|an)?\s*{root_pattern}\s+(?P<quality>major|minor)?\s*chord\s+(?:even\s+)?mean$",
        rf"^what\s+does\s+(?:a|an)?\s*{root_pattern}\s+(?P<quality>major|minor)?\s*chord\s+mean$",
        rf"^what\s+notes\s+are\s+in\s+(?:a|an)?\s*{root_pattern}\s+(?P<quality>major|minor)?\s*chord$",
        rf"^what\s+notes\s+are\s+in\s+(?:a|an)?\s*{root_pattern}\s*(?P<quality>major|minor)?$",
        rf"^what\s+makes\s+(?:a|an)?\s*{root_pattern}\s+minor\s+chord\s+minor$",
        rf"^what\s+makes\s+(?:a|an)?\s*{root_pattern}\s+minor\s+minor$",
        rf"^what\s+makes\s+(?:a|an)?\s*{root_pattern}\s+major\s+chord\s+major$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            requested_root = normalize_requested_root(match.group("root"))
            quality = normalize_chord_quality(match.groupdict().get("quality") or "")
            if not quality and " minor chord" in q:
                quality = "minor"
            if not quality and re.search(r"\bminor\s+minor\b", q):
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
        prefix = (
            f"An {key} minor chord means the notes {minor_triad_spelling_for_answer(key)}: "
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
    if re.search(r"^why\s+(?:is|does)\s+a\+b\s+(?:make\s+)?a\s+chord$", q) or re.search(r"^what\s+does\s+a\+b\s+do$", q):
        return (
            "A+B is not a chord by itself; it is a pedal combination that can make a grip spell chord tones on E9. "
            "The A pedal raises the B strings to C#, and the B pedal raises the G# strings to A. "
            "At the right fret, those changed notes can line up as root, major 3rd, and perfect 5th.\n\n"
            "Example: on standard 10-string E9, A+B at the 10th fret gives a G major position on common grips such as 3-4-5, 4-5-6, 5-6-8, and 6-8-10. "
            "That works because the pedals change the intervals under the bar; the fret and grip tell you which chord those intervals spell."
        )
    return None


def minor_triad_spelling(root: str) -> str:
    return f"{normalize_key(root)}-{transpose(normalize_key(root), 3)}-{transpose(normalize_key(root), 7)}"


def minor_triad_spelling_for_answer(root: str) -> str:
    raw = (root or "").strip().replace("♭", "b").replace("♯", "#")
    flat_preferred = {
        "Db": "Db-Fb-Ab",
        "Eb": "Eb-Gb-Bb",
        "Gb": "Gb-Bbb-Db",
        "Ab": "Ab-Cb-Eb",
        "Bb": "Bb-Db-F",
    }
    if raw in flat_preferred:
        return flat_preferred[raw]
    key = normalize_key(root)
    preferred = {
        "C": "C-Eb-G",
        "C#": "C#-E-G#",
        "D": "D-F-A",
        "D#": "D#-F#-A#",
        "E": "E-G-B",
        "F": "F-Ab-C",
        "F#": "F#-A-C#",
        "G": "G-Bb-D",
        "G#": "G#-B-D#",
        "A": "A-C-E",
        "A#": "A#-C#-E#",
        "B": "B-D-F#",
    }
    return preferred.get(key, minor_triad_spelling(key))


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
            "The diagram shows only pitch-validated minor positions; it does not use forum snippets to decide the chord.",
        ]
    )
    return "\n".join(lines)


def fretboard_payload_for_question(question: str) -> dict | None:
    """Return MVP fretboard visualization data for a narrow curated question set."""
    q = normalize_chord_intent_text(question)
    if not q:
        return None
    diagnostic_payload = fret_string_pedal_payload_for_question(q)
    if diagnostic_payload is not None:
        return diagnostic_payload
    if re.search(r"\be[- ]?lower\b.*\bminor\s+sound\b", q):
        return get_fretboard_examples("minor_positions", "G#")
    if re.search(r"\be\s+minor\s+pocket\b", q):
        return get_fretboard_examples("minor_positions", "E")
    if re.search(r"\ba\s*\+\s*b\b.*\bd\s+major\b|\bd\s+major\b.*\ba\s*\+\s*b\b", q):
        return get_fretboard_examples("major_positions", "D")
    if re.search(r"\bg\s+a\s*\+\s*f\s+position\b|\bg\s+major\b.*\ba\s*\+\s*f\b|\ba\s*\+\s*f\b.*\bg\s+major\b", q):
        return get_fretboard_examples("major_positions", "G")
    if re.search(r"\bg\b.*\bharmonized[-\s]+scale\b.*\b(?:5\s*(?:&|and|-)\s*8|strings?\s+5\s+(?:and\s+)?8)\b", q):
        return g_five_eight_harmonized_scale_branches().to_payload()
    g_harmonized_payload = g_harmonized_scale_payload_for_question(q)
    if g_harmonized_payload is not None:
        return g_harmonized_payload
    mixed_a_minor_c_major_payload = mixed_a_minor_c_major_payload_for_question(q)
    if mixed_a_minor_c_major_payload is not None:
        return mixed_a_minor_c_major_payload
    mixed_a_minor_bflat_major_payload = mixed_a_minor_bflat_major_payload_for_question(q)
    if mixed_a_minor_bflat_major_payload is not None:
        return mixed_a_minor_bflat_major_payload
    multi_chord_payload = multi_chord_payload_for_question(q)
    if multi_chord_payload is not None:
        return multi_chord_payload
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
    if re.search(r"\bwhere\s+(?:should\s+i|do\s+i)\s+go\s+after\s+a\s*\+\s*b\s+in\s+g\b", q):
        return get_fretboard_examples("major_positions", "G")
    if re.search(r"\bgrips?\b.*\ba\s*\+\s*b\b.*\b10(?:th)?\s+fret\b", q):
        return get_fretboard_examples("major_positions", "G")
    if re.search(r"\bwhere\s+is\s+the\s+iv\s+chord\s+from\s+open\s+g\b", q):
        return get_fretboard_examples("major_positions", "C")
    function_chord_payload = function_chord_payload_for_question(q)
    if function_chord_payload is not None:
        return function_chord_payload
    minor_chord_payload = minor_chord_payload_for_question(q)
    if minor_chord_payload is not None:
        return minor_chord_payload
    specific_major_grip_payload = specific_major_grip_payload_for_question(q)
    if specific_major_grip_payload is not None:
        return specific_major_grip_payload
    chord_concept_payload = chord_concept_payload_for_question(q)
    if chord_concept_payload is not None:
        return chord_concept_payload
    major_request = major_chord_location_request_for_question(q)
    if major_request is not None:
        payload = get_fretboard_examples("major_positions", major_request.normalized_key)
        display_key = display_major_key_for_request(major_request)
        if display_key != major_request.normalized_key:
            payload = dict(payload)
            payload["title"] = f"{display_key} major positions on E9"
            payload["key"] = display_key
            payload["subtitle"] = str(payload.get("subtitle", "")).replace(major_request.normalized_key, display_key)
            payload["description"] = str(payload.get("description", "")).replace(
                major_request.normalized_key, display_key
            )
        return payload
    if q in {"show me the fretboard", "show the fretboard", "show me an e9 fretboard", "show me the e9 fretboard"}:
        return get_fretboard_examples("major_positions", "G")
    if q == "show me common grips for g":
        return get_fretboard_examples("common_grips", "G")
    unsupported_request = unsupported_chord_location_request_for_question(q)
    if unsupported_request is not None and unsupported_request.quality in {"dominant 7", "major 7"}:
        return get_fretboard_examples("major_positions", unsupported_request.normalized_key)
    return None


def major_chord_location_key_for_question(question: str) -> str | None:
    """Extract a deterministic major-key request from narrow location prompts."""
    request = major_chord_location_request_for_question(question)
    return request.normalized_key if request else None


def specific_major_grip_request_for_question(question: str) -> SpecificMajorGripRequest | None:
    q = normalize_chord_intent_text(question)
    if not q:
        return None
    patterns = (
        rf"^show me (?:a|an)?\s*(?P<grip>\d{{1,2}}\s*[-/ ]\s*\d{{1,2}}\s*[-/ ]\s*\d{{1,2}})\s+(?P<root>{CHORD_ROOT_RE})(?:\s+major)?\s+grip(?:\s+on\s+e9)?$",
        rf"^show me (?:a|an)?\s*(?P<root>{CHORD_ROOT_RE})(?:\s+major)?\s+(?:chord|grip)\s+on\s+strings?\s+(?P<grip>\d{{1,2}}\s*[-/ ]\s*\d{{1,2}}\s*[-/ ]\s*\d{{1,2}})(?:\s+on\s+e9)?$",
        rf"^where is (?:a|an)?\s*(?P<root>{CHORD_ROOT_RE})(?:\s+major)?\s+(?:chord|grip)\s+on\s+strings?\s+(?P<grip>\d{{1,2}}\s*[-/ ]\s*\d{{1,2}}\s*[-/ ]\s*\d{{1,2}})(?:\s+on\s+e9)?$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        strings = parse_grip_strings(match.group("grip"))
        if strings is None:
            continue
        if strings != E_LOWER_578_GRIP:
            continue
        requested_root = normalize_requested_root(match.group("root"))
        return SpecificMajorGripRequest(
            requested_root=requested_root,
            normalized_key=normalize_key(requested_root),
            strings=strings,
        )
    return None


def specific_major_grip_position(request: SpecificMajorGripRequest) -> FretboardPosition | None:
    key = request.normalized_key
    open_fret = open_major_fret(key)
    return major_position_candidate(
        key=key,
        suffix=f"grip-{grip_label(request.strings)}-{open_fret}",
        fret=open_fret,
        strings=request.strings,
        color="reference",
        role=f"Pitch-checked {grip_label(request.strings)} grip",
        family="specific_grip",
        tier="beginner" if request.strings != E_LOWER_578_GRIP else "advanced",
        color_role="reference",
        visible_by_default=True,
        sort_order=10,
        explanation=f"No-pedal fret {open_fret} is pitch-checked against {key} major on strings {grip_label(request.strings)}.",
        function="I",
        key_context=key,
        why_use_it="Use this focused card to check whether the requested grip is a complete major triad or a partial color.",
    )


def specific_major_grip_payload_for_question(question: str) -> dict | None:
    request = specific_major_grip_request_for_question(question)
    if request is None:
        return None
    position = specific_major_grip_position(request)
    if position is None:
        return None
    display_key = display_major_key_for_request(
        MajorChordLocationRequest(requested_root=request.requested_root, normalized_key=request.normalized_key)
    )
    if display_key != position.root:
        position = replace(
            position,
            root=display_key,
            label=position.label.replace(position.root, display_key, 1),
            key_context=display_key,
        )
    return FretboardVisualizationPayload(
        title=f"{display_key} grip {grip_label(request.strings)} on E9",
        subtitle=f"Pitch-checked static grip for {display_key} on strings {grip_label(request.strings)}.",
        key=display_key,
        positions=(position,),
    ).to_payload()


def specific_major_grip_answer_for_question(question: str) -> str | None:
    request = specific_major_grip_request_for_question(question)
    if request is None:
        return None
    position = specific_major_grip_position(request)
    if position is None:
        return None
    display_key = display_major_key_for_request(
        MajorChordLocationRequest(requested_root=request.requested_root, normalized_key=request.normalized_key)
    )
    note_text = ", ".join(
        f"string {string} = {note}" for string, note in sorted((position.notes or {}).items(), key=lambda item: int(item[0]))
    )
    interval_text = ", ".join(
        f"string {string} = {interval}"
        for string, interval in sorted((position.intervals or {}).items(), key=lambda item: int(item[0]))
    )
    if position.is_full_chord:
        return (
            f"Yes. On E9, strings {grip_label(request.strings)} at the {fret_label(position.fret)} with no pedals/no levers "
            f"spell a full {display_key} major grip.\n\n"
            f"Notes: {note_text}.\n"
            f"Intervals: {interval_text}."
        )
    omitted = ", ".join(position.omitted_intervals) or "none"
    added = ", ".join(position.added_intervals) or "none"
    return (
        f"Not as a full plain {display_key} major grip. On E9, strings {grip_label(request.strings)} at the "
        f"{fret_label(position.fret)} with no pedals/no levers are a partial/color sound, not a complete triad.\n\n"
        f"Notes: {note_text}.\n"
        f"Intervals: {interval_text}.\n"
        f"Omitted from the plain major triad: {omitted}. Added color: {added}.\n\n"
        f"For a beginner-safe full {display_key} major grip, start with 4-5-6, 5-6-8, or 6-8-10 at the same no-pedals fret."
    )


def major_chord_location_request_for_question(question: str) -> MajorChordLocationRequest | None:
    """Extract a deterministic major-chord request and preserve spelling."""
    q = normalize_chord_intent_text(question)
    if not q:
        return None
    e9_context = chord_context_pattern()
    optional_context = rf"(?:\s+{e9_context})?"
    patterns = (
        rf"^where are (?:some )?places to play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chords?|chords?))?{optional_context}$",
        rf"^where are (?:some\s+)?([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chords?|chords?))?{optional_context}$",
        rf"^where(?: all)? can i play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chords?|chords?))?{optional_context}$",
        rf"^where(?: all)? can i play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?{optional_context}$",
        rf"^where do i play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?{optional_context}$",
        rf"^where can i find (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chords?|chords?))?{optional_context}$",
        rf"^where can i find (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?{optional_context}$",
        rf"^where do i find (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chords?|chords?|positions?))?{optional_context}$",
        rf"^where do i find ([a-g](?:##|bb|#|b)?)\s+major\s+positions{optional_context}$",
        rf"^how do (?:i|you) play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?{optional_context}$",
        rf"^how do (?:i|you) play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?\s+(?:at|on)\s+(?:the\s+)?\d+(?:st|nd|rd|th)?\s+fret{optional_context}$",
        rf"^how do i plan (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord){optional_context}$",
        rf"^how do i make (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?{optional_context}$",
        rf"^where is ([a-g](?:##|bb|#|b)?) major{optional_context}$",
        rf"^where is ([a-g](?:##|bb|#|b)?)(?: major)?{optional_context}$",
        rf"^where is (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord){optional_context}$",
        rf"^where are (?:my\s+)?([a-g](?:##|bb|#|b)?) (?:major )?chord positions{optional_context}$",
        rf"^show me ([a-g](?:##|bb|#|b)?) (?:major )?positions{optional_context}$",
        rf"^show me ([a-g](?:##|bb|#|b)?) (?:major )?chord positions{optional_context}$",
        rf"^show me ([a-g](?:##|bb|#|b)?) major{optional_context}$",
        rf"^show me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+major)?\s+string\s+group(?:ing)?s?{optional_context}$",
        rf"^show me ([a-g](?:##|bb|#|b)?)\s+(?:major\s+)?(?:strings?|grips?)\s+group(?:ing)?s?{optional_context}$",
        rf"^show me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord){optional_context}$",
        rf"^give me ([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)? positions{optional_context}$",
        rf"^positions for ([a-g](?:##|bb|#|b)?)(?: (?:major )?chords?)?{optional_context}$",
        rf"^([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?{optional_context}$",
        r"^where is ([a-g](?:##|bb|#|b)?) on (?:the )?fretboard$",
        rf"^what frets give me (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chord|chord))?{optional_context}$",
        rf"^which frets are (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?:\s+(?:major|major chord|chord))?{optional_context}$",
        rf"^what is the location for (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?(?: with [a-g]\s*\+\s*[a-g])?{optional_context}$",
        rf"^what is the location of (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)?(?: with [a-g]\s*\+\s*[a-g])?{optional_context}$",
        rf"^show me places to play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: major)?(?: chord)?{optional_context}$",
        rf"^where are ([a-g](?:##|bb|#|b)?) major positions{optional_context}$",
        r"^how do (?:i|you) play (?:a|an)?\s*([a-g](?:##|bb|#|b)?)(?: (?:major )?chord)? across (?:the )?fretboard(?: of (?:the )?e9| on e9)?$",
        r"^([a-g](?:##|bb|#|b)?) major across (?:the )?e9 fretboard$",
        r"^([a-g](?:##|bb|#|b)?) (?:major )?chord across (?:the )?e9 fretboard$",
        r"^show me ([a-g](?:##|bb|#|b)?) major with a\+b$",
        r"^show me ([a-g](?:##|bb|#|b)?) major with a\+f$",
        r"^show me (?:more|advanced) ([a-g](?:##|bb|#|b)?) (?:major )?chord positions$",
        r"^show me ([a-g](?:##|bb|#|b)?) (?:major )?chord positions with levers$",
        r"^what grips can i use for ([a-g](?:##|bb|#|b)?) major$",
        r"^where the the ([a-g](?:##|bb|#|b)?) chords?$",
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


def normalize_chord_words_in_text(text: str) -> str:
    """Normalize spelled accidentals in user chord prompts before regex parsing."""
    return normalize_spelled_accidentals(text or "")


def normalize_chord_intent_text(text: str) -> str:
    """Normalize casual chord-position phrasing before deterministic parsing."""
    normalized = normalize_chord_words_in_text(text or "")
    normalized = normalized.replace("’", "'").replace("“", '"').replace("”", '"')
    normalized = normalized.lower()
    normalized = re.sub(r"[?!.,;:]+", " ", normalized)
    normalized = re.sub(r"\bcan you\b", " ", normalized)
    normalized = re.sub(r"\b(?:in\s+the\s+hell|the\s+hell|hell|heck|freaking)\b", " ", normalized)
    normalized = re.sub(r"\b(?:uh|um|er|please|just)\b", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def chord_context_pattern() -> str:
    return (
        r"(?:on|across|of|for)\s+(?:the\s+|my\s+)?"
        r"(?:e9(?:\s+(?:neck|pedal\s+steel|setup))?|pedal\s+steel(?:\s+e9)?|steel(?:\s+e9)?|neck|fretboard|guitar)"
    )


def unsupported_chord_location_request_for_question(question: str) -> UnsupportedChordLocationRequest | None:
    """Detect location-style chord questions with unsupported non-major qualities."""
    q = normalize_chord_intent_text(question)
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
        r"what is",
        r"what(?:'s|’s)",
    )
    prefix_match = re.match(rf"^(?P<prefix>{'|'.join(prefixes)})\s+(?:an|a)?\s*(?P<body>.+)$", q)
    if not prefix_match:
        return None
    prefix = prefix_match.group("prefix")
    if prefix.startswith("what") and not re.search(r"\b(?:where|play|positions?|frets?|fretboard)\b", q):
        return None
    body = prefix_match.group("body")
    body = re.sub(r"\bon e9\b$", "", body).strip()
    body = re.sub(r"\b(?:and\s+)?where\s+(?:do|can|should)\s+i\s+play\s+it$", "", body).strip()
    body = re.sub(r"\bpositions?\b$", "", body).strip()
    body = re.sub(r"\bchord\b$", "", body).strip()
    quality_match = re.match(
        r"^(?P<root>[a-g](?:##|bb|#|b)?)(?P<compact>m(?!ajor|aj)|maj7|7|dim7?|aug|sus(?:2|4)?)?(?:\s+(?P<quality>minor|minor\s+7|m7|dominant(?:\s+7)?|dom(?:\s+7)?|seventh|7|diminished(?:\s+7)?|dim7?|augmented|aug|sus(?:2|4)?|suspended(?:\s+[24])?|major\s+7th|major\s+seventh|major\s+7|maj\s+7|maj7))?$",
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
        "7th": "dominant 7",
        "seventh": "dominant 7",
        "dom": "dominant 7",
        "dom 7": "dominant 7",
        "dom7": "dominant 7",
        "dominant": "dominant 7",
        "dominant 7": "dominant 7",
        "dim": "diminished",
        "dim7": "diminished 7",
        "diminished7": "diminished 7",
        "diminished 7": "diminished 7",
        "aug": "augmented",
        "+": "augmented",
        "suspended": "sus",
        "suspended 2": "sus2",
        "suspended 4": "sus4",
        "maj 7": "major 7",
        "maj7": "major 7",
        "major 7": "major 7",
        "major 7th": "major 7",
        "major seventh": "major 7",
    }
    return aliases.get(q, q)


def normalize_requested_root(root: str) -> str:
    normalized = normalize_accidental_symbols(root or "").strip()
    if not normalized:
        raise ValueError(f"Unsupported key: {root}")
    letter = normalized[:1].upper()
    accidental = normalized[1:]
    if accidental not in {"", "#", "b", "##", "bb"}:
        raise ValueError(f"Unsupported key: {root}")
    display = f"{letter}{accidental}"
    if note_lookup_key(display) not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported key: {root}")
    return display


def note_lookup_key(note: str) -> str:
    return normalize_accidental_symbols(note or "").strip().upper()


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
            if candidate is not None and candidate.is_partial:
                candidate = replace(
                    candidate,
                    tier="advanced" if grip == E_LOWER_578_GRIP else candidate.tier,
                    sort_order=candidate.sort_order + 45,
                    why_use_it=f"Use this as a contextual {key} color grip only after you know the complete triad positions.",
                    caveats=tuple(
                        dict.fromkeys(
                            (
                                *candidate.caveats,
                                "This grip is a partial/color voicing, not a complete major triad.",
                            )
                        )
                    ),
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
                sort_order=420 + grip_index * 10 + octave_sort_offset,
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


def g_five_eight_harmonized_scale_branches() -> FretboardVisualizationPayload:
    """Return the validated G 5&8 A+F/E-lower branch alternatives."""
    specs: tuple[dict[str, object], ...] = (
        {
            "suffix": "five-eight-af-branch-4-6",
            "root": "G",
            "fret": 6,
            "pedals": ("A",),
            "levers": ("F",),
            "role": "5&8 A+F branch 4 minor/blue color",
            "family": "five_eight_a_f_minor_blue",
            "color": "secondary",
            "color_role": "secondary",
            "sort_order": 10,
            "explanation": (
                "Strings 5 and 8 at fret 6 with A pedal plus E-raise/F lever spell G and B. "
                "This is the branch-4 minor/blue-color route."
            ),
            "why_use_it": "Use this when you want the A+F branch color instead of collapsing the branch into E-lower.",
        },
        {
            "suffix": "five-eight-e-lower-branch-4-8",
            "root": "G",
            "fret": 8,
            "pedals": (),
            "levers": ("E",),
            "role": "5&8 E-lower branch 4 major color",
            "family": "five_eight_e_lower_major_color",
            "color": "reference",
            "color_role": "e-lower",
            "sort_order": 20,
            "explanation": (
                "Strings 5 and 8 at fret 8 with E-lower spell G and B. "
                "This is the branch-4 major-color route."
            ),
            "why_use_it": "Use this when you want the E-lower branch color and a connected lever path.",
        },
        {
            "suffix": "five-eight-af-branch-7-11",
            "root": "C",
            "fret": 11,
            "pedals": ("A",),
            "levers": ("F",),
            "role": "5&8 A+F branch 7 minor/blue color",
            "family": "five_eight_a_f_minor_blue",
            "color": "secondary",
            "color_role": "secondary",
            "sort_order": 30,
            "explanation": (
                "Strings 5 and 8 at fret 11 with A pedal plus E-raise/F lever spell C and E. "
                "This is the branch-7 minor/blue-color route."
            ),
            "why_use_it": "Use this as the A+F route to the C/E branch.",
        },
        {
            "suffix": "five-eight-e-lower-branch-7-13",
            "root": "C",
            "fret": 13,
            "pedals": (),
            "levers": ("E",),
            "role": "5&8 E-lower branch 7 major color",
            "family": "five_eight_e_lower_major_color",
            "color": "reference",
            "color_role": "e-lower",
            "sort_order": 40,
            "explanation": (
                "Strings 5 and 8 at fret 13 with E-lower spell C and E. "
                "This is the corrected branch-7 major-color route; the old 11th-fret E-lower wording was a typo."
            ),
            "why_use_it": "Use this as the corrected E-lower route to the C/E branch.",
        },
    )
    positions: list[FretboardPosition] = []
    for spec in specs:
        candidate = major_position_candidate(
            key=str(spec["root"]),
            suffix=str(spec["suffix"]),
            fret=int(spec["fret"]),
            strings=(5, 8),
            pedals=spec["pedals"],  # type: ignore[arg-type]
            levers=spec["levers"],  # type: ignore[arg-type]
            color=str(spec["color"]),
            role=str(spec["role"]),
            family=str(spec["family"]),
            tier="advanced",
            color_role=str(spec["color_role"]),
            visible_by_default=True,
            sort_order=int(spec["sort_order"]),
            explanation=str(spec["explanation"]),
            function="G harmonized 5&8 branch",
            key_context="G",
            why_use_it=str(spec["why_use_it"]),
            caveats=("This is a two-note branch color, not a complete triad by itself.",),
        )
        if candidate is None:
            raise ValueError(f"5&8 branch did not validate: {spec['role']}")
        positions.append(candidate)
    return FretboardVisualizationPayload(
        title="G harmonized scale 5&8 branches",
        subtitle="Pitch-validated A+F and E-lower branch alternatives on strings 5 and 8.",
        key="G",
        positions=tuple(positions),
    )


def _validated_harmonized_scale_position(
    *,
    root: str,
    quality: str,
    suffix: str,
    degree_label: str,
    fret: int,
    strings: tuple[int, ...],
    pedals: tuple[str, ...] = (),
    levers: tuple[str, ...] = (),
    family: str,
    color: str,
    color_role: str,
    sort_order: int,
    key_context: str,
    visible_by_default: bool = True,
    display_label: str | None = None,
    caveats: tuple[str, ...] = (),
) -> FretboardPosition:
    controls = " + ".join(pedals + levers) if pedals or levers else "no pedals/no levers"
    role = f"{degree_label}: {display_label or f'{root} {quality_label(quality)}'}"
    candidate = major_position_candidate(
        key=root,
        quality=quality,
        suffix=suffix,
        fret=fret,
        strings=strings,
        pedals=pedals,
        levers=levers,
        color=color,
        role=role,
        family=family,
        tier="starter" if visible_by_default else "advanced",
        color_role=color_role,
        visible_by_default=visible_by_default,
        sort_order=sort_order,
        explanation=(
            f"{role} validates on strings {grip_label(strings)} at fret {fret} with {controls}. "
            "The row is accepted only after pitch validation."
        ),
        function=degree_label,
        key_context=key_context,
        why_use_it=(
            f"Use this as a pitch-validated {degree_label} reference inside the {key_context} harmonized-scale map."
        ),
        caveats=caveats,
        allow_added_intervals=False,
    )
    if candidate is None:
        raise ValueError(f"Harmonized-scale candidate did not validate: {role}")
    if display_label is not None and candidate.label != display_label:
        candidate = replace(candidate, label=display_label)
    return candidate


def g_major_harmonized_scale_positions() -> FretboardVisualizationPayload:
    """Return a source-free G major harmonized-scale position map for answer payloads."""
    positions = [
        _validated_harmonized_scale_position(
            root="G",
            quality="major",
            suffix="harmonized-major-i-456-3",
            degree_label="I",
            fret=3,
            strings=(4, 5, 6),
            family="g_major_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=10,
            key_context="G major",
        ),
        _validated_harmonized_scale_position(
            root="A",
            quality="minor",
            suffix="harmonized-major-ii-456-3-bc",
            degree_label="ii",
            fret=3,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_major_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=20,
            key_context="G major",
        ),
        _validated_harmonized_scale_position(
            root="B",
            quality="minor",
            suffix="harmonized-major-iii-456-5-bc",
            degree_label="iii",
            fret=5,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_major_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=30,
            key_context="G major",
        ),
        _validated_harmonized_scale_position(
            root="C",
            quality="major",
            suffix="harmonized-major-iv-456-8",
            degree_label="IV",
            fret=8,
            strings=(4, 5, 6),
            family="g_major_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=40,
            key_context="G major",
        ),
        _validated_harmonized_scale_position(
            root="D",
            quality="major",
            suffix="harmonized-major-v-456-10",
            degree_label="V",
            fret=10,
            strings=(4, 5, 6),
            family="g_major_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=50,
            key_context="G major",
        ),
        _validated_harmonized_scale_position(
            root="E",
            quality="minor",
            suffix="harmonized-major-vi-456-10-bc",
            degree_label="vi",
            fret=10,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_major_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=60,
            key_context="G major",
        ),
        _validated_harmonized_scale_position(
            root="F#",
            quality="diminished",
            suffix="harmonized-major-vii-dim-456-13-f",
            degree_label="vii diminished",
            fret=13,
            strings=(4, 5, 6),
            levers=("F",),
            family="g_major_harmonized_scale_diminished",
            color="warning",
            color_role="diminished",
            sort_order=70,
            key_context="G major",
            caveats=("F#-A-C is a diminished triad. Do not call it full F#m7b5 unless E, the b7, is present.",),
        ),
        _validated_harmonized_scale_position(
            root="G",
            quality="major",
            suffix="harmonized-major-i-octave-456-15",
            degree_label="I octave",
            fret=15,
            strings=(4, 5, 6),
            family="g_major_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=80,
            key_context="G major",
        ),
    ]
    branch_positions = [
        replace(position, visible_by_default=False, sort_order=200 + position.sort_order)
        for position in g_five_eight_harmonized_scale_branches().positions
    ]
    return FretboardVisualizationPayload(
        title="G major harmonized scale on E9",
        subtitle="Pitch-validated G major harmonized-scale rows with 5&8 branch options.",
        key="G",
        positions=tuple(positions + branch_positions),
    )


def g_natural_minor_harmonized_scale_positions() -> FretboardVisualizationPayload:
    """Return a source-free G natural minor harmonized-scale position map for answer payloads."""
    positions = [
        _validated_harmonized_scale_position(
            root="G",
            quality="minor",
            suffix="harmonized-natural-minor-i-456-1-bc",
            degree_label="i",
            fret=1,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_natural_minor_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=10,
            key_context="G natural minor",
        ),
        _validated_harmonized_scale_position(
            root="A",
            quality="diminished",
            suffix="harmonized-natural-minor-ii-dim-456-4-f",
            degree_label="ii diminished",
            fret=4,
            strings=(4, 5, 6),
            levers=("F",),
            family="g_natural_minor_harmonized_scale_diminished",
            color="warning",
            color_role="diminished",
            sort_order=20,
            key_context="G natural minor",
            caveats=("A-C-Eb is a diminished triad. Do not call it full Am7b5 unless G, the b7, is present.",),
        ),
        _validated_harmonized_scale_position(
            root="A#",
            quality="major",
            suffix="harmonized-natural-minor-iii-456-6",
            degree_label="III",
            fret=6,
            strings=(4, 5, 6),
            family="g_natural_minor_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=30,
            key_context="G natural minor",
            display_label="Bb major",
        ),
        _validated_harmonized_scale_position(
            root="C",
            quality="minor",
            suffix="harmonized-natural-minor-iv-456-6-bc",
            degree_label="iv",
            fret=6,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_natural_minor_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=40,
            key_context="G natural minor",
        ),
        _validated_harmonized_scale_position(
            root="D",
            quality="minor",
            suffix="harmonized-natural-minor-v-456-8-bc",
            degree_label="v",
            fret=8,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_natural_minor_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=50,
            key_context="G natural minor",
        ),
        _validated_harmonized_scale_position(
            root="D#",
            quality="major",
            suffix="harmonized-natural-minor-vi-456-11",
            degree_label="VI",
            fret=11,
            strings=(4, 5, 6),
            family="g_natural_minor_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=60,
            key_context="G natural minor",
            display_label="Eb major",
        ),
        _validated_harmonized_scale_position(
            root="F",
            quality="major",
            suffix="harmonized-natural-minor-vii-456-13",
            degree_label="VII",
            fret=13,
            strings=(4, 5, 6),
            family="g_natural_minor_harmonized_scale_456",
            color="primary",
            color_role="primary",
            sort_order=70,
            key_context="G natural minor",
        ),
        _validated_harmonized_scale_position(
            root="G",
            quality="minor",
            suffix="harmonized-natural-minor-i-octave-456-13-bc",
            degree_label="i octave",
            fret=13,
            strings=(4, 5, 6),
            pedals=("B", "C"),
            family="g_natural_minor_harmonized_scale_456",
            color="secondary",
            color_role="secondary",
            sort_order=80,
            key_context="G natural minor",
        ),
    ]
    return FretboardVisualizationPayload(
        title="G natural minor harmonized scale on E9",
        subtitle="Pitch-validated G natural minor diatonic harmony rows.",
        key="G",
        positions=tuple(positions),
    )


def g_harmonized_scale_payload_for_question(question: str) -> dict | None:
    q = normalize_chord_intent_text(question)
    if not re.search(r"\b(?:show|where|position|fretboard)\b", q):
        return None
    if re.search(r"\bf#\s+diminished\b", q) and re.search(r"\bin\s+g\b", q):
        return FretboardVisualizationPayload(
            title="F# diminished position in G",
            subtitle="Pitch-validated vii diminished triad from G major.",
            key="G",
            positions=(g_major_harmonized_scale_positions().positions[6],),
        ).to_payload()
    if re.search(r"\ba\s+diminished\b", q) and re.search(r"\bin\s+g\s+minor\b", q):
        return FretboardVisualizationPayload(
            title="A diminished position in G natural minor",
            subtitle="Pitch-validated ii diminished triad from G natural minor.",
            key="G",
            positions=(g_natural_minor_harmonized_scale_positions().positions[1],),
        ).to_payload()
    if re.search(r"\bg\b", q) and re.search(r"\bnatural\s+minor\b", q) and re.search(r"\bharmonized[-\s]+scales?\b", q):
        return g_natural_minor_harmonized_scale_positions().to_payload()
    if re.search(r"\bg\b", q) and re.search(r"\bharmonized[-\s]+scales?\b", q):
        return g_major_harmonized_scale_positions().to_payload()
    return None


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
