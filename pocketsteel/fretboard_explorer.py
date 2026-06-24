"""Deterministic E9 Fretboard Explorer rows.

This module is intentionally independent from RAG/corpus retrieval. It uses
pitch math against a standard 10-string E9 copedent to generate validated
harmonized-scale and diatonic-harmony surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pocketsteel.fretboard_examples import (
    E9_OPEN_STRINGS,
    absolute_pitch_for_string,
    interval_for_note,
    note_at_fret,
    semitone_for_note,
)
from pocketsteel.e9_copedents import (
    DEFAULT_COPEDENT_ID,
    control_changes_for_profile,
    control_labels_for_profile,
    control_order_for_profile,
    control_types_for_profile,
    get_e9_copedent_profile,
    selected_copedent_payload,
)
from pocketsteel.music_text import normalize_spelled_accidentals


ExplorerScaleType = Literal["major", "natural_minor"]
ExplorerHarmonyType = Literal[
    "two_string_harmonized",
    "three_string_diatonic",
    "five_eight_branch",
    "advanced_pocket",
]
VoicingStatus = Literal["full", "partial", "implied", "unavailable"]

MVP_COPEDENT_ID = DEFAULT_COPEDENT_ID
MVP_COPEDENT_LABEL = "Emmons E9"

CORE_GRIPS: tuple[str, ...] = ("3-4-5", "4-5-6", "5-6-8", "6-8-10")
ADVANCED_GRIPS: tuple[str, ...] = ("5-6-7", "6-7-10", "5-7-8")
FIVE_EIGHT_BRANCH_GRIPS: tuple[str, ...] = ("5-8",)
SUPPORTED_GRIPS: tuple[str, ...] = CORE_GRIPS + ADVANCED_GRIPS + FIVE_EIGHT_BRANCH_GRIPS

G_MAJOR_SCALE_NOTES: tuple[str, ...] = ("G", "A", "B", "C", "D", "E", "F#")
G_NATURAL_MINOR_SCALE_NOTES: tuple[str, ...] = ("G", "A", "Bb", "C", "D", "Eb", "F")
SUPPORTED_EXPLORER_KEYS: tuple[str, ...] = (
    "C",
    "C#",
    "Db",
    "D",
    "D#",
    "Eb",
    "E",
    "F",
    "F#",
    "Gb",
    "G",
    "G#",
    "Ab",
    "A",
    "A#",
    "Bb",
    "B",
)

MAJOR_SCALE_INTERVALS: tuple[str, ...] = ("1", "2/9", "3", "4/11", "5", "6/13", "7")
NATURAL_MINOR_SCALE_INTERVALS: tuple[str, ...] = ("1", "2/9", "b3", "4/11", "5", "b6", "b7")

STANDARD_E9_CONTROL_CHANGES: dict[str, dict[int, str]] = control_changes_for_profile(MVP_COPEDENT_ID)
STANDARD_E9_CONTROL_ORDER: tuple[str, ...] = control_order_for_profile(MVP_COPEDENT_ID)
CONTROL_TYPE_LABELS: dict[str, str] = control_types_for_profile(MVP_COPEDENT_ID)
CONTROL_EXPLANATION_LABELS: dict[str, str] = control_labels_for_profile(MVP_COPEDENT_ID)

QUALITY_INTERVALS: dict[str, tuple[str, ...]] = {
    "major": ("1", "3", "5"),
    "minor": ("1", "b3", "5"),
    "diminished": ("1", "b3", "b5/#11"),
}

NATURAL_NOTE_PITCH_CLASSES: dict[str, int] = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

NOTE_LETTERS: tuple[str, ...] = ("C", "D", "E", "F", "G", "A", "B")

INTERVAL_TO_SEMITONES: dict[str, int] = {
    "1": 0,
    "b2": 1,
    "2/9": 2,
    "b3": 3,
    "3": 4,
    "4/11": 5,
    "b5/#11": 6,
    "5": 7,
    "b6": 8,
    "#5/b6": 8,
    "6/13": 9,
    "b7": 10,
    "7": 11,
}

INTERVAL_TO_LETTER_STEPS: dict[str, int] = {
    "1": 0,
    "b2": 1,
    "2/9": 1,
    "b3": 2,
    "3": 2,
    "4/11": 3,
    "b5/#11": 4,
    "5": 4,
    "b6": 5,
    "#5/b6": 5,
    "6/13": 5,
    "b7": 6,
    "7": 6,
}


@dataclass(frozen=True)
class ExplorerRow:
    id: str
    key: str
    scale_type: ExplorerScaleType
    harmony_type: ExplorerHarmonyType
    scale_degree: int
    chord_function: str
    chord_name: str
    chord_quality: str
    fret: int
    string_group: str
    strings: tuple[int, ...]
    notes: dict[str, str]
    intervals: dict[str, str]
    display_notes: dict[str, str]
    display_top_voice: dict[str, str | int] = field(default_factory=dict)
    display_summary: str = ""
    pedals: tuple[str, ...] = ()
    levers: tuple[str, ...] = ()
    per_string_changes: dict[str, dict[str, str]] = field(default_factory=dict)
    top_voice: dict[str, str | int] = field(default_factory=dict)
    control_impacts: tuple[dict[str, object], ...] = ()
    inversion: str = "not_classified"
    voicing_status: VoicingStatus = "full"
    omitted_intervals: tuple[str, ...] = ()
    position_family: str = "no_pedals_no_levers"
    difficulty_tier: str = "starter"
    availability_status: str = "available"
    pitch_validated: bool = True
    copedent_profile: str = MVP_COPEDENT_ID
    source_guidance_refs: tuple[str, ...] = ()
    explanation_summary: str = ""
    warnings: tuple[str, ...] = ()
    display_harmony_type: ExplorerHarmonyType = "two_string_harmonized"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "key": self.key,
            "scale_type": self.scale_type,
            "harmony_type": self.harmony_type,
            "display_harmony_type": self.display_harmony_type,
            "scale_degree": self.scale_degree,
            "chord_function": self.chord_function,
            "chord_name": self.chord_name,
            "chord_quality": self.chord_quality,
            "fret": self.fret,
            "string_group": self.string_group,
            "strings": list(self.strings),
            "notes": dict(self.notes),
            "intervals": dict(self.intervals),
            "display_notes": dict(self.display_notes),
            "display_top_voice": dict(self.display_top_voice),
            "display_summary": self.display_summary,
            "pedals": list(self.pedals),
            "levers": list(self.levers),
            "per_string_changes": dict(self.per_string_changes),
            "top_voice": dict(self.top_voice),
            "control_impacts": [dict(impact) for impact in self.control_impacts],
            "inversion": self.inversion,
            "voicing_status": self.voicing_status,
            "omitted_intervals": list(self.omitted_intervals),
            "position_family": self.position_family,
            "difficulty_tier": self.difficulty_tier,
            "availability_status": self.availability_status,
            "pitch_validated": self.pitch_validated,
            "copedent_profile": self.copedent_profile,
            "source_guidance_refs": list(self.source_guidance_refs),
            "explanation_summary": self.explanation_summary,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ExplorerCandidate:
    key: str
    scale_type: ExplorerScaleType
    harmony_type: ExplorerHarmonyType
    scale_degree: int
    chord_function: str
    chord_name: str
    chord_quality: str
    fret: int
    strings: tuple[int, ...]
    controls: tuple[str, ...] = ()
    position_family: str = "no_pedals_no_levers"
    difficulty_tier: str = "starter"
    source_guidance_refs: tuple[str, ...] = ()
    explanation_summary: str = ""


def grip_label(strings: tuple[int, ...]) -> str:
    return "-".join(str(string) for string in strings)


def normalize_explorer_key(key: str) -> str:
    normalized = normalize_spelled_accidentals(key or "").strip()
    if not normalized:
        raise ValueError("Explorer key is required")
    normalized = normalized[0].upper() + normalized[1:]
    if len(normalized) > 1:
        normalized = normalized[0] + normalized[1:].replace("♭", "b").replace("♯", "#")
    if normalized not in SUPPORTED_EXPLORER_KEYS:
        raise ValueError(f"Unsupported Explorer key: {key}")
    return normalized


def key_slug(key: str) -> str:
    normalized = normalize_explorer_key(key)
    return f"{normalized[0].lower()}{normalized[1:].replace('#', 'sharp').replace('b', 'flat')}"


def transpose_offset_from_g(key: str) -> int:
    offset = (semitone_for_note(key) - semitone_for_note("G")) % 12
    if offset > 6:
        offset -= 12
    return offset


def transpose_fret_from_g(g_fret: int, key: str) -> int:
    fret = g_fret + transpose_offset_from_g(key)
    if g_fret >= 12 and fret <= 12:
        fret += 12
    while fret > 24:
        fret -= 12
    while fret < 0:
        fret += 12
    return fret


def scale_notes_for_key(key: str, scale_type: ExplorerScaleType) -> tuple[str, ...]:
    root = normalize_explorer_key(key)
    intervals = MAJOR_SCALE_INTERVALS if scale_type == "major" else NATURAL_MINOR_SCALE_INTERVALS
    return tuple(spell_note_for_interval(root, interval) for interval in intervals)


def chord_name_for_scale_degree(key: str, scale_type: ExplorerScaleType, degree: int) -> str:
    scale_notes = scale_notes_for_key(key, scale_type)
    return scale_notes[(degree - 1) % 7]


def controls_to_pedals_levers(controls: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    pedals = tuple(control for control in controls if control in {"A", "B", "C"})
    levers = tuple(control for control in controls if control not in {"A", "B", "C"})
    return pedals, levers


def semitone_for_control_note(note: str) -> int:
    return semitone_for_note((note or "").split("/", 1)[0].strip())


def semitone_delta_for_change(before_note: str, after_note: str) -> int:
    delta = (semitone_for_control_note(after_note) - semitone_for_control_note(before_note)) % 12
    if delta > 6:
        delta -= 12
    return delta


def interval_effect_label(delta: int) -> str:
    if delta > 0:
        unit = "semitone" if delta == 1 else "semitones"
        return f"raises {delta} {unit}"
    if delta < 0:
        amount = abs(delta)
        unit = "semitone" if amount == 1 else "semitones"
        return f"lowers {amount} {unit}"
    return "no pitch change"


def standard_notes_for_controls(controls: tuple[str, ...]) -> dict[int, str]:
    notes = dict(E9_OPEN_STRINGS)
    for control in controls:
        if control not in STANDARD_E9_CONTROL_CHANGES:
            raise ValueError(f"Unsupported Explorer control: {control}")
        notes.update(STANDARD_E9_CONTROL_CHANGES[control])
    return notes


def per_string_changes(strings: tuple[int, ...], controls: tuple[str, ...]) -> dict[str, dict[str, str]]:
    changes: dict[str, dict[str, str]] = {}
    for string in strings:
        applied: list[str] = []
        from_note = E9_OPEN_STRINGS[string]
        to_note = from_note
        for control in controls:
            control_changes = STANDARD_E9_CONTROL_CHANGES[control]
            if string not in control_changes:
                continue
            applied.append(control)
            to_note = control_changes[string]
        if applied:
            changes[str(string)] = {
                "from": from_note,
                "to": to_note,
                "controls": "+".join(applied),
            }
    return changes


def validate_control_effects(strings: tuple[int, ...], controls: tuple[str, ...]) -> None:
    for control in controls:
        affected = set(STANDARD_E9_CONTROL_CHANGES[control])
        if not affected.intersection(strings):
            raise ValueError(f"{control} does not affect played strings {grip_label(strings)}")


def resolve_notes(fret: int, strings: tuple[int, ...], controls: tuple[str, ...]) -> dict[str, str]:
    changed_notes = standard_notes_for_controls(controls)
    return {str(string): note_at_fret(changed_notes[string], fret) for string in strings}


def note_in_scale(note: str, scale_notes: tuple[str, ...]) -> bool:
    note_pc = semitone_for_note(note)
    return note_pc in {semitone_for_note(scale_note) for scale_note in scale_notes}


def interval_label(root: str, note: str) -> str:
    return interval_for_note(root, note)


def note_root(note: str) -> str:
    if len(note) > 1 and note[1] in {"#", "b"}:
        return note[:2]
    return note[:1]


def note_letter(note: str) -> str:
    return note_root(note)[0].upper()


def letter_steps_from(root: str, steps: int) -> str:
    root_index = NOTE_LETTERS.index(note_letter(root))
    return NOTE_LETTERS[(root_index + steps) % len(NOTE_LETTERS)]


def spell_pitch_for_letter(pitch_class: int, target_letter: str) -> str:
    natural_pitch = NATURAL_NOTE_PITCH_CLASSES[target_letter]
    accidental_delta = (pitch_class - natural_pitch) % 12
    if accidental_delta > 6:
        accidental_delta -= 12
    accidentals = {
        -2: "bb",
        -1: "b",
        0: "",
        1: "#",
        2: "##",
    }
    if accidental_delta not in accidentals:
        return note_name_for_display_pitch(pitch_class)
    return f"{target_letter}{accidentals[accidental_delta]}"


def note_name_for_display_pitch(pitch_class: int) -> str:
    for scale_note in G_NATURAL_MINOR_SCALE_NOTES:
        if semitone_for_note(scale_note) == pitch_class:
            return scale_note
    for scale_note in G_MAJOR_SCALE_NOTES:
        if semitone_for_note(scale_note) == pitch_class:
            return scale_note
    return note_at_fret("C", pitch_class)


def spell_note_for_interval(root: str, interval: str) -> str:
    if interval not in INTERVAL_TO_SEMITONES or interval not in INTERVAL_TO_LETTER_STEPS:
        return note_name_for_display_pitch(semitone_for_note(root))
    pitch_class = (semitone_for_note(root) + INTERVAL_TO_SEMITONES[interval]) % 12
    target_letter = letter_steps_from(root, INTERVAL_TO_LETTER_STEPS[interval])
    return spell_pitch_for_letter(pitch_class, target_letter)


def display_note_for_scale(note: str, scale_notes: tuple[str, ...]) -> str:
    note_pitch = semitone_for_note(note)
    for scale_note in scale_notes:
        if semitone_for_note(scale_note) == note_pitch:
            return scale_note
    return note_name_for_display_pitch(note_pitch)


def scale_degree_context_for_note(key: str, scale_type: ExplorerScaleType, note: str) -> dict[str, object]:
    scale_notes = scale_notes_for_key(key, scale_type)
    interval_note = (note or "").split("/", 1)[0].strip()
    note_pitch = semitone_for_control_note(note)
    for index, scale_note in enumerate(scale_notes, start=1):
        if semitone_for_note(scale_note) == note_pitch:
            return {
                "scale_type": scale_type,
                "scale_degree": index,
                "scale_degree_label": str(index),
                "display_note": scale_note,
                "interval_to_key_root": interval_for_note(key, interval_note),
                "in_scale": True,
            }
    return {
        "scale_type": scale_type,
        "scale_degree": None,
        "scale_degree_label": "outside",
        "display_note": note_name_for_display_pitch(note_pitch),
        "interval_to_key_root": interval_for_note(key, interval_note),
        "in_scale": False,
    }


def key_context_for_note(key: str, note: str) -> dict[str, dict[str, object]]:
    return {
        "major": scale_degree_context_for_note(key, "major", note),
        "natural_minor": scale_degree_context_for_note(key, "natural_minor", note),
    }


def display_notes_for_row(
    *,
    key: str,
    chord_root: str,
    harmony_type: ExplorerHarmonyType,
    scale_type: ExplorerScaleType,
    notes: dict[str, str],
    intervals: dict[str, str],
) -> dict[str, str]:
    if harmony_type in {"two_string_harmonized", "five_eight_branch"}:
        scale_notes = scale_notes_for_key(key, scale_type)
        return {string: display_note_for_scale(note, scale_notes) for string, note in notes.items()}
    return {
        string: spell_note_for_interval(chord_root, intervals[string])
        for string in notes
    }


def display_top_voice_for(top_voice: dict[str, str | int], display_notes: dict[str, str]) -> dict[str, str | int]:
    string = str(top_voice["string"])
    return {
        **top_voice,
        "note": display_notes[string],
    }


def display_note_for_chord_interval(root: str, interval: str, raw_note: str) -> str:
    try:
        return spell_note_for_interval(root, interval)
    except Exception:
        return note_name_for_display_pitch(semitone_for_control_note(raw_note))


def display_summary_for(candidate: ExplorerCandidate, display_notes: dict[str, str]) -> str:
    note_list = ", ".join(display_notes[str(string)] for string in candidate.strings)
    return (
        f"{candidate.chord_name} on strings {grip_label(candidate.strings)} "
        f"at fret {candidate.fret}: {note_list}."
    )


def controls_for_teaching(controls: tuple[str, ...]) -> str:
    if not controls:
        return "no pedals/no levers"
    return " + ".join(CONTROL_EXPLANATION_LABELS.get(control, control) for control in controls)


def scale_label(key: str, scale_type: ExplorerScaleType) -> str:
    return f"{key} {'natural minor' if scale_type == 'natural_minor' else 'major'}"


def notes_for_teaching(strings: tuple[int, ...], values: dict[str, str]) -> str:
    return ", ".join(values[str(string)] for string in strings)


def row_teaching_explanation(
    *,
    key: str,
    scale_type: ExplorerScaleType,
    harmony_type: ExplorerHarmonyType,
    scale_degree: int,
    chord_function: str,
    chord_name: str,
    chord_quality: str,
    fret: int,
    strings: tuple[int, ...],
    controls: tuple[str, ...],
    display_notes: dict[str, str],
    intervals: dict[str, str],
    position_family: str,
    voicing_status: VoicingStatus,
    omitted_intervals: tuple[str, ...],
) -> str:
    string_group = grip_label(strings)
    scale = scale_label(key, scale_type)
    notes_text = notes_for_teaching(strings, display_notes)
    intervals_text = notes_for_teaching(strings, intervals)
    controls_text = controls_for_teaching(controls)

    if harmony_type == "two_string_harmonized":
        opening = (
            f"This two-string harmonized-scale row maps degree {scale_degree} in {scale}; "
            "it is a partial interval pair, not a full triad."
        )
    elif harmony_type == "five_eight_branch":
        branch_color = "major-color" if "e_lower" in position_family else "minor/blue-color"
        opening = (
            f"This 5&8 harmonized-scale branch maps branch {scale_degree} in {scale}; "
            f"it is the {branch_color} route, not a full triad."
        )
    elif harmony_type == "advanced_pocket":
        opening = (
            f"This advanced 5-7-8 E-lower pocket targets {chord_name} {chord_quality} "
            f"as {chord_function} in {scale}."
        )
    else:
        opening = (
            f"This three-string diatonic-harmony row targets {chord_function}, "
            f"the degree {scale_degree} chord in {scale}, and validates as "
            f"{chord_name} {chord_quality}."
        )

    sentences = [
        opening,
        (
            f"Use fret {fret} on strings {string_group} with {controls_text}; "
            f"the selected strings spell {notes_text} ({intervals_text} against {chord_name})."
        ),
    ]

    if not controls:
        sentences.append("No pedals/no levers marks this as a straight-bar reference position.")
    if "B" in controls and "C" in controls:
        sentences.append(
            "B+C is validated for this exact row; do not generalize B+C to other grips without checking the resulting notes."
        )
    if "E-lower" in controls or position_family == "e_lower_pocket":
        sentences.append("Use the mechanical E-lower lever name here; shorthand varies by copedent.")
    if "E-raise" in controls:
        sentences.append("Use the mechanical E-raise lever name here; shorthand varies by copedent.")
    if harmony_type == "five_eight_branch":
        sentences.append("Keep the A+F and E-lower routes separate; they are both valid mechanical paths for this branch.")
    if string_group in ADVANCED_GRIPS:
        sentences.append("This is an advanced swap, so compare it with the nearby core grip before treating it as a default.")
    if voicing_status == "partial" and "b7" in omitted_intervals:
        sentences.append(
            "Because this grip contains 1-b3-b5 and omits b7, label it as a diminished triad or partial half-diminished color, not a full m7b5."
        )

    sentences.append("This position is generated from validated E9 pitch logic. Teaching text explains the row; it does not choose the row.")
    return " ".join(sentences)


def explanation_for_explorer_row(row: ExplorerRow) -> str:
    controls = row.pedals + row.levers
    return row_teaching_explanation(
        key=row.key,
        scale_type=row.scale_type,
        harmony_type=row.harmony_type,
        scale_degree=row.scale_degree,
        chord_function=row.chord_function,
        chord_name=row.chord_name,
        chord_quality=row.chord_quality,
        fret=row.fret,
        strings=row.strings,
        controls=controls,
        display_notes=row.display_notes,
        intervals=row.intervals,
        position_family=row.position_family,
        voicing_status=row.voicing_status,
        omitted_intervals=row.omitted_intervals,
    )


def top_voice_for(strings: tuple[int, ...], fret: int, controls: tuple[str, ...], notes: dict[str, str], intervals: dict[str, str]) -> dict[str, str | int]:
    top_string = max(strings, key=lambda string: absolute_pitch_for_string(string, fret, controls))
    return {
        "string": top_string,
        "note": notes[str(top_string)],
        "interval": intervals[str(top_string)],
    }


def row_control_impacts(candidate: ExplorerCandidate) -> tuple[dict[str, object], ...]:
    impacts: list[dict[str, object]] = []
    chord_root = candidate.chord_name.rstrip("*")
    final_notes = resolve_notes(candidate.fret, candidate.strings, candidate.controls)
    final_intervals = {string: interval_label(chord_root, note) for string, note in final_notes.items()}
    for control in candidate.controls:
        affected_strings = tuple(
            string for string in candidate.strings if string in STANDARD_E9_CONTROL_CHANGES[control]
        )
        if not affected_strings:
            continue
        before_controls = tuple(active for active in candidate.controls if active != control)
        before_notes = resolve_notes(candidate.fret, affected_strings, before_controls)
        string_impacts: list[dict[str, object]] = []
        for string in affected_strings:
            string_key = str(string)
            before_note = before_notes[string_key]
            after_note = final_notes[string_key]
            before_interval = interval_label(chord_root, before_note)
            after_interval = final_intervals[string_key]
            before_open_note = standard_notes_for_controls(before_controls)[string]
            after_open_note = standard_notes_for_controls(candidate.controls)[string]
            delta = semitone_delta_for_change(before_open_note, after_open_note)
            string_impacts.append(
                {
                    "string": string,
                    "before_open_note": before_open_note,
                    "after_open_note": after_open_note,
                    "before_note": before_note,
                    "after_note": after_note,
                    "display_before_note": display_note_for_chord_interval(chord_root, before_interval, before_note),
                    "display_after_note": display_note_for_chord_interval(chord_root, after_interval, after_note),
                    "before_interval": before_interval,
                    "after_interval": after_interval,
                    "semitone_delta": delta,
                    "interval_effect": interval_effect_label(delta),
                }
            )
        before_intervals = [impact["before_interval"] for impact in string_impacts]
        after_intervals = [impact["after_interval"] for impact in string_impacts]
        impacts.append(
            {
                "id": control,
                "label": CONTROL_EXPLANATION_LABELS[control],
                "control_type": CONTROL_TYPE_LABELS[control],
                "affected_strings": list(affected_strings),
                "string_impacts": string_impacts,
                "resulting_context": {
                    "root": chord_root,
                    "quality": candidate.chord_quality,
                    "chord_function": candidate.chord_function,
                    "before_intervals": before_intervals,
                    "after_intervals": after_intervals,
                    "row_validates_as": f"{chord_root} {candidate.chord_quality}",
                },
                "validation_status": "deterministic_standard_e9",
            }
        )
    return tuple(impacts)


def classify_inversion(intervals: dict[str, str], strings: tuple[int, ...], *, voicing_status: VoicingStatus) -> str:
    if voicing_status != "full":
        return "partial_or_implied"
    lowest_string = max(strings, key=int)
    lowest_interval = intervals[str(lowest_string)]
    if lowest_interval == "1":
        return "root_position"
    if lowest_interval in {"3", "b3"}:
        return "first_inversion"
    if lowest_interval == "5":
        return "second_inversion"
    return "mixed_voicing"


def validate_explorer_candidate(candidate: ExplorerCandidate) -> ExplorerRow:
    key = normalize_explorer_key(candidate.key)
    if candidate.fret < 0 or candidate.fret > 24:
        raise ValueError("Explorer frets must be 0-24")
    if any(string < 1 or string > 10 for string in candidate.strings):
        raise ValueError("Explorer strings must be 1-10")
    if candidate.strings != tuple(sorted(candidate.strings)):
        raise ValueError("Explorer strings must be sorted")
    if grip_label(candidate.strings) not in SUPPORTED_GRIPS and candidate.harmony_type != "two_string_harmonized":
        raise ValueError(f"Unsupported Explorer string group: {grip_label(candidate.strings)}")
    validate_control_effects(candidate.strings, candidate.controls)

    notes = resolve_notes(candidate.fret, candidate.strings, candidate.controls)
    intervals = {string: interval_label(candidate.chord_name.rstrip("*"), note) for string, note in notes.items()}
    warnings: list[str] = []
    voicing_status: VoicingStatus = "full"
    omitted_intervals: tuple[str, ...] = ()

    if candidate.harmony_type in {"two_string_harmonized", "five_eight_branch"}:
        scale_notes = scale_notes_for_key(key, candidate.scale_type)
        if not all(note_in_scale(note, scale_notes) for note in notes.values()):
            raise ValueError("Two-string row contains notes outside the target scale")
        voicing_status = "partial"
        required = tuple()
    else:
        required = QUALITY_INTERVALS[candidate.chord_quality]
        present = set(intervals.values())
        if not present.issubset(set(required)):
            raise ValueError(
                f"Row notes {notes} do not validate as {candidate.chord_name} {candidate.chord_quality}"
            )
        omitted_intervals = tuple(interval for interval in required if interval not in present)
        if omitted_intervals:
            raise ValueError(f"Row omits required interval(s): {', '.join(omitted_intervals)}")
        if "partial" in candidate.chord_function:
            voicing_status = "partial"
            omitted_intervals = ("b7",)
            warnings.append(
                "This grip contains 1-b3-b5 only. It can imply half-diminished function, but it does not include the b7."
            )

    display_notes = display_notes_for_row(
        key=key,
        chord_root=candidate.chord_name.rstrip("*"),
        harmony_type=candidate.harmony_type,
        scale_type=candidate.scale_type,
        notes=notes,
        intervals=intervals,
    )
    top_voice = top_voice_for(candidate.strings, candidate.fret, candidate.controls, notes, intervals)
    display_top_voice = display_top_voice_for(top_voice, display_notes)
    display_summary = display_summary_for(candidate, display_notes)
    pedals, levers = controls_to_pedals_levers(candidate.controls)
    explanation_summary = row_teaching_explanation(
        key=key,
        scale_type=candidate.scale_type,
        harmony_type=candidate.harmony_type,
        scale_degree=candidate.scale_degree,
        chord_function=candidate.chord_function,
        chord_name=candidate.chord_name,
        chord_quality=candidate.chord_quality,
        fret=candidate.fret,
        strings=candidate.strings,
        controls=candidate.controls,
        display_notes=display_notes,
        intervals=intervals,
        position_family=candidate.position_family,
        voicing_status=voicing_status,
        omitted_intervals=omitted_intervals,
    )
    row_id = "-".join(
        [
            key_slug(key),
            candidate.scale_type.replace("_", "-"),
            candidate.harmony_type.replace("_", "-"),
            grip_label(candidate.strings),
            str(candidate.scale_degree),
            candidate.position_family,
            str(candidate.fret),
        ]
    ).lower()
    return ExplorerRow(
        id=row_id,
        key=key,
        scale_type=candidate.scale_type,
        harmony_type=candidate.harmony_type,
        display_harmony_type="two_string_harmonized"
        if candidate.harmony_type == "five_eight_branch"
        else candidate.harmony_type,
        scale_degree=candidate.scale_degree,
        chord_function=candidate.chord_function,
        chord_name=candidate.chord_name,
        chord_quality=candidate.chord_quality,
        fret=candidate.fret,
        string_group=grip_label(candidate.strings),
        strings=candidate.strings,
        notes=notes,
        intervals=intervals,
        display_notes=display_notes,
        display_top_voice=display_top_voice,
        display_summary=display_summary,
        pedals=pedals,
        levers=levers,
        per_string_changes=per_string_changes(candidate.strings, candidate.controls),
        top_voice=top_voice,
        control_impacts=row_control_impacts(candidate),
        inversion=classify_inversion(intervals, candidate.strings, voicing_status=voicing_status),
        voicing_status=voicing_status,
        omitted_intervals=omitted_intervals,
        position_family=candidate.position_family,
        difficulty_tier=candidate.difficulty_tier,
        source_guidance_refs=candidate.source_guidance_refs,
        explanation_summary=explanation_summary,
        warnings=tuple(warnings),
    )


def validate_unique_candidates(candidates: list[ExplorerCandidate] | tuple[ExplorerCandidate, ...]) -> list[ExplorerRow]:
    rows: list[ExplorerRow] = []
    row_ids: set[str] = set()
    for candidate in candidates:
        row = validate_explorer_candidate(candidate)
        if row.id in row_ids:
            continue
        row_ids.add(row.id)
        rows.append(row)
    return rows


def _major_candidate_rows_for_grip(strings: tuple[int, ...], *, key: str = "G") -> tuple[ExplorerCandidate, ...]:
    key = normalize_explorer_key(key)
    if strings in {(4, 5, 6), (3, 4, 5)}:
        minor_controls = ("B", "C")
        minor_strings = strings
    elif strings == (5, 6, 8):
        minor_controls = ("A", "B")
        minor_strings = (5, 6, 7)
    elif strings == (6, 8, 10):
        minor_controls = ("A", "B")
        minor_strings = (6, 7, 10)
    else:
        raise ValueError(f"Unsupported major grip: {strings}")
    base_ref = "e9-harmony-guidance:major-three-string"
    rows = [
        (1, "I", "major", 3, (), strings, "no_pedals_no_levers"),
        (2, "ii", "minor", 3, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
        (3, "iii", "minor", 5, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
        (4, "IV", "major", 8, (), strings, "no_pedals_no_levers"),
        (5, "V", "major", 10, (), strings, "no_pedals_no_levers"),
        (6, "vi", "minor", 10, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
        (7, "vii° / partial viiø", "diminished", 13, ("E-raise",), strings, "e_raise_diminished"),
        (1, "I", "major", 15, (), strings, "no_pedals_no_levers"),
    ]
    return tuple(
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="three_string_diatonic",
            scale_degree=degree,
            chord_function=function,
            chord_name=chord_name_for_scale_degree(key, "major", degree),
            chord_quality=quality,
            fret=transpose_fret_from_g(fret, key),
            strings=row_strings,
            controls=controls,
            position_family=family,
            difficulty_tier="advanced" if row_strings != strings else "starter",
            source_guidance_refs=(base_ref,),
        )
        for degree, function, quality, fret, controls, row_strings, family in rows
    )


def major_three_string_rows(key: str = "G") -> list[ExplorerRow]:
    candidates: list[ExplorerCandidate] = []
    for grip in ((3, 4, 5), (4, 5, 6), (5, 6, 8), (6, 8, 10)):
        candidates.extend(_major_candidate_rows_for_grip(grip, key=key))
    return validate_unique_candidates(candidates)


def g_major_three_string_rows() -> list[ExplorerRow]:
    return major_three_string_rows("G")


def _natural_minor_candidate_rows_for_grip(strings: tuple[int, ...], *, key: str = "G") -> tuple[ExplorerCandidate, ...]:
    key = normalize_explorer_key(key)
    if strings in {(4, 5, 6), (3, 4, 5)}:
        minor_controls = ("B", "C")
        minor_strings = strings
    elif strings == (5, 6, 8):
        minor_controls = ("A", "B")
        minor_strings = (5, 6, 7)
    elif strings == (6, 8, 10):
        minor_controls = ("A", "B")
        minor_strings = (6, 7, 10)
    else:
        raise ValueError(f"Unsupported natural minor grip: {strings}")
    base_ref = "e9-harmony-guidance:natural-minor-three-string"
    rows = [
        (1, "i", "minor", 1, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
        (2, "ii° / partial iiø", "diminished", 4, ("E-raise",), strings, "e_raise_diminished"),
        (3, "III", "major", 6, (), strings, "no_pedals_no_levers"),
        (4, "iv", "minor", 6, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
        (5, "v", "minor", 8, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
        (6, "VI", "major", 11, (), strings, "no_pedals_no_levers"),
        (7, "VII", "major", 13, (), strings, "no_pedals_no_levers"),
        (1, "i", "minor", 13, minor_controls, minor_strings, "bc_minor" if "C" in minor_controls else "ab_minor"),
    ]
    return tuple(
        ExplorerCandidate(
            key=key,
            scale_type="natural_minor",
            harmony_type="three_string_diatonic",
            scale_degree=degree,
            chord_function=function,
            chord_name=chord_name_for_scale_degree(key, "natural_minor", degree),
            chord_quality=quality,
            fret=transpose_fret_from_g(fret, key),
            strings=row_strings,
            controls=controls,
            position_family=family,
            difficulty_tier="advanced" if row_strings != strings else "starter",
            source_guidance_refs=(base_ref,),
        )
        for degree, function, quality, fret, controls, row_strings, family in rows
    )


def natural_minor_three_string_rows(key: str = "G") -> list[ExplorerRow]:
    candidates: list[ExplorerCandidate] = []
    for grip in ((3, 4, 5), (4, 5, 6), (5, 6, 8), (6, 8, 10)):
        candidates.extend(_natural_minor_candidate_rows_for_grip(grip, key=key))
    return validate_unique_candidates(candidates)


def g_natural_minor_three_string_rows() -> list[ExplorerRow]:
    return natural_minor_three_string_rows("G")


def _two_string_candidates(key: str = "G") -> tuple[ExplorerCandidate, ...]:
    key = normalize_explorer_key(key)
    rows: list[tuple[int, int, tuple[str, ...], tuple[int, ...], str]] = []
    for strings in ((3, 5), (5, 6), (6, 10)):
        rows.extend(
            [
                (3, 3, (), strings, "major_thirds_sixths"),
                (4, 3, ("A", "B"), strings, "major_thirds_sixths"),
                (5, 5, ("A", "B"), strings, "major_thirds_sixths"),
                (6, 8, (), strings, "major_thirds_sixths"),
                (7, 10, (), strings, "major_thirds_sixths"),
                (1, 10, ("A", "B"), strings, "major_thirds_sixths"),
                (2, 13, (), strings, "major_thirds_sixths"),
                (3, 15, (), strings, "major_thirds_sixths"),
            ]
        )
    rows.extend(
        [
            (1, 3, (), (4, 6), "e_raise_two_string"),
            (2, 4, ("E-raise",), (4, 6), "e_raise_two_string"),
            (3, 6, ("E-raise",), (4, 6), "e_raise_two_string"),
            (4, 8, (), (4, 6), "e_raise_two_string"),
            (5, 10, (), (4, 6), "e_raise_two_string"),
            (6, 11, ("E-raise",), (4, 6), "e_raise_two_string"),
            (7, 13, ("E-raise",), (4, 6), "e_raise_two_string"),
            (1, 15, (), (4, 6), "e_raise_two_string"),
            (1, 3, (), (3, 4), "bc_two_string"),
            (2, 3, ("B", "C"), (3, 4), "bc_two_string"),
            (3, 5, ("B", "C"), (3, 4), "bc_two_string"),
            (4, 8, (), (3, 4), "bc_two_string"),
            (5, 10, (), (3, 4), "bc_two_string"),
            (6, 10, ("B", "C"), (3, 4), "bc_two_string"),
            (7, 12, ("B", "C"), (3, 4), "bc_two_string"),
            (1, 15, (), (3, 4), "bc_two_string"),
        ]
    )
    return tuple(
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="two_string_harmonized",
            scale_degree=degree,
            chord_function=str(degree),
            chord_name=chord_name_for_scale_degree(key, "major", degree),
            chord_quality="dyad",
            fret=transpose_fret_from_g(fret, key),
            strings=strings,
            controls=controls,
            position_family=family,
            difficulty_tier="common",
            source_guidance_refs=("e9-harmony-guidance:major-two-string",),
        )
        for degree, fret, controls, strings, family in rows
    )


def major_two_string_rows(key: str = "G") -> list[ExplorerRow]:
    return validate_unique_candidates(_two_string_candidates(key))


def g_major_two_string_rows() -> list[ExplorerRow]:
    return major_two_string_rows("G")


def five_eight_branch_rows(key: str = "G") -> list[ExplorerRow]:
    """Return the G-only 5&8 A+F and E-lower branch alternatives.

    These rows are deliberately separate from the generic 2-string harmonized
    rows because the product decision treats A+F and E-lower as two valid
    branch routes that should not be collapsed into one canonical path.
    """
    key = normalize_explorer_key(key)
    if key != "G":
        return []
    candidates = [
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="five_eight_branch",
            scale_degree=4,
            chord_function="branch 4 minor/blue color",
            chord_name="G",
            chord_quality="dyad",
            fret=6,
            strings=(5, 8),
            controls=("A", "E-raise"),
            position_family="five_eight_a_f_minor_blue",
            difficulty_tier="advanced",
            source_guidance_refs=("e9-harmony-guidance:5-8-branch-a-f",),
        ),
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="five_eight_branch",
            scale_degree=4,
            chord_function="branch 4 major color",
            chord_name="G",
            chord_quality="dyad",
            fret=8,
            strings=(5, 8),
            controls=("E-lower",),
            position_family="five_eight_e_lower_major_color",
            difficulty_tier="advanced",
            source_guidance_refs=("e9-harmony-guidance:5-8-branch-e-lower",),
        ),
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="five_eight_branch",
            scale_degree=7,
            chord_function="branch 7 minor/blue color",
            chord_name="C",
            chord_quality="dyad",
            fret=11,
            strings=(5, 8),
            controls=("A", "E-raise"),
            position_family="five_eight_a_f_minor_blue",
            difficulty_tier="advanced",
            source_guidance_refs=("e9-harmony-guidance:5-8-branch-a-f",),
        ),
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="five_eight_branch",
            scale_degree=7,
            chord_function="branch 7 major color",
            chord_name="C",
            chord_quality="dyad",
            fret=13,
            strings=(5, 8),
            controls=("E-lower",),
            position_family="five_eight_e_lower_major_color",
            difficulty_tier="advanced",
            source_guidance_refs=("e9-harmony-guidance:5-8-branch-e-lower",),
        ),
    ]
    return validate_unique_candidates(candidates)


def g_five_eight_branch_rows() -> list[ExplorerRow]:
    return five_eight_branch_rows("G")


def advanced_e_lower_pocket_rows(key: str = "G") -> list[ExplorerRow]:
    key = normalize_explorer_key(key)
    candidates = [
        ExplorerCandidate(
            key=key,
            scale_type="major",
            harmony_type="advanced_pocket",
            scale_degree=1,
            chord_function="I",
            chord_name=key,
            chord_quality="major",
            fret=transpose_fret_from_g(fret, key),
            strings=(5, 7, 8),
            controls=("E-lower",),
            position_family="e_lower_pocket",
            difficulty_tier="advanced",
            source_guidance_refs=("e9-harmony-guidance:5-7-8-e-lower-pocket",),
            explanation_summary=(
                f"Advanced 5-7-8 E-lower {key} major pocket; validated by pitch math."
            ),
        )
        for fret in (8, 20)
    ]
    return validate_unique_candidates(candidates)


def g_advanced_e_lower_pocket_rows() -> list[ExplorerRow]:
    return advanced_e_lower_pocket_rows("G")


def g_explorer_rows() -> list[ExplorerRow]:
    return explorer_rows("G")


def explorer_rows(key: str = "G") -> list[ExplorerRow]:
    return [
        *major_two_string_rows(key),
        *major_three_string_rows(key),
        *natural_minor_three_string_rows(key),
        *five_eight_branch_rows(key),
        *advanced_e_lower_pocket_rows(key),
    ]


def build_g_explorer_payload() -> dict[str, object]:
    return build_explorer_payload("G")


def build_explorer_payload(key: str = "G", copedent_id: str | None = None) -> dict[str, object]:
    key = normalize_explorer_key(key)
    profile = get_e9_copedent_profile(copedent_id)
    rows = [row.to_dict() for row in explorer_rows(key)]
    return {
        "type": "e9-fretboard-explorer",
        "version": "1.0",
        "instrument": "E9",
        "copedent_profile": {
            "id": profile.id,
            "status": profile.status,
            "label": profile.label,
        },
        "selected_copedent": selected_copedent_payload(profile.id),
        "query": {
            "key": key,
            "scale_types": ["major", "natural_minor"],
            "display_scale_notes": {
                "major": list(scale_notes_for_key(key, "major")),
                "natural_minor": list(scale_notes_for_key(key, "natural_minor")),
            },
            "harmony_types": ["two_string_harmonized", "three_string_diatonic", "five_eight_branch", "advanced_pocket"],
            "string_groups": list(SUPPORTED_GRIPS),
        },
        "control_impact_preview": build_control_impact_preview(key, profile.id),
        "positions": rows,
        "filters": {
            "available_keys": list(SUPPORTED_EXPLORER_KEYS),
            "available_scale_types": ["major", "natural_minor"],
            "available_harmony_types": ["two_string_harmonized", "three_string_diatonic", "five_eight_branch", "advanced_pocket"],
            "available_string_groups": list(SUPPORTED_GRIPS),
            "available_copedents": selected_copedent_payload(profile.id)["available_options"],
        },
        "legend": [
            {"id": "starter", "label": "Starter"},
            {"id": "common", "label": "Common"},
            {"id": "advanced", "label": "Advanced"},
        ],
        "warnings": list(selected_copedent_payload(profile.id)["warnings"]),
    }


def build_control_impact_preview(key: str = "G", copedent_id: str | None = None) -> dict[str, object]:
    key = normalize_explorer_key(key)
    profile = get_e9_copedent_profile(copedent_id)
    control_changes = control_changes_for_profile(profile.id)
    control_labels = control_labels_for_profile(profile.id)
    control_types = control_types_for_profile(profile.id)
    controls: list[dict[str, object]] = []
    for control in control_order_for_profile(profile.id):
        changes = control_changes[control]
        string_impacts: list[dict[str, object]] = []
        for string in sorted(changes):
            before_note = E9_OPEN_STRINGS[string]
            after_note = changes[string]
            delta = semitone_delta_for_change(before_note, after_note)
            string_impacts.append(
                {
                    "string": string,
                    "before_note": before_note,
                    "after_note": after_note,
                    "semitone_delta": delta,
                    "interval_effect": interval_effect_label(delta),
                    "before_key_context": key_context_for_note(key, before_note),
                    "after_key_context": key_context_for_note(key, after_note),
                }
            )
        controls.append(
            {
                "id": control,
                "label": control_labels[control],
                "control_type": control_types[control],
                "affected_strings": sorted(changes),
                "string_impacts": string_impacts,
                "summary": control_impact_summary(key, control, string_impacts, profile.id),
                "validation_status": "deterministic_standard_e9",
            }
        )
    return {
        "type": "e9-pedal-lever-impact-preview",
        "version": "1.0",
        "instrument": "E9",
        "copedent_profile": {
            "id": profile.id,
            "status": profile.status,
            "label": profile.label,
        },
        "selected_copedent_id": profile.id,
        "key_context": {
            "key": key,
            "major_scale": list(scale_notes_for_key(key, "major")),
            "natural_minor_scale": list(scale_notes_for_key(key, "natural_minor")),
        },
        "controls": controls,
        "notes": [
            f"This preview is generated from deterministic {profile.label} 10-string E9 pitch logic.",
            "Scale-degree context is relative to the selected Explorer key; row-level impacts show the selected row's chord context.",
        ],
        "warnings": [],
    }


def control_impact_summary(
    key: str,
    control: str,
    string_impacts: list[dict[str, object]],
    copedent_id: str | None = None,
) -> str:
    strings = ", ".join(str(impact["string"]) for impact in string_impacts)
    first = string_impacts[0]
    before_major = first["before_key_context"]["major"]
    after_major = first["after_key_context"]["major"]
    control_labels = control_labels_for_profile(copedent_id)
    return (
        f"{control_labels[control]} affects strings {strings}; "
        f"against {key} major, the first affected string moves from "
        f"{first['before_note']} ({before_major['scale_degree_label']}) to "
        f"{first['after_note']} ({after_major['scale_degree_label']})."
    )


def validate_explorer_payload(payload: dict[str, object]) -> None:
    if payload.get("type") != "e9-fretboard-explorer":
        raise ValueError("Unsupported Explorer payload type")
    selected_copedent = payload.get("selected_copedent")
    if not isinstance(selected_copedent, dict):
        raise ValueError("Explorer payload requires selected_copedent")
    if selected_copedent.get("instrument") != "E9":
        raise ValueError("Explorer selected_copedent must be E9")
    strings = selected_copedent.get("strings")
    if not isinstance(strings, list) or [item.get("string") for item in strings if isinstance(item, dict)] != list(range(1, 11)):
        raise ValueError("Explorer selected_copedent requires string rows 1-10")
    chart = selected_copedent.get("chart")
    if not isinstance(chart, dict) or not isinstance(chart.get("rows"), list) or not isinstance(chart.get("columns"), list):
        raise ValueError("Explorer selected_copedent requires chart rows and columns")
    options = selected_copedent.get("available_options")
    if not isinstance(options, list) or not options:
        raise ValueError("Explorer selected_copedent requires available_options")
    if any(option.get("id") == "my-copedent-e9" and option.get("status") != "disabled" for option in options if isinstance(option, dict)):
        raise ValueError("My Copedent option must be disabled in this slice")
    positions = payload.get("positions")
    if not isinstance(positions, list) or not positions:
        raise ValueError("Explorer payload requires positions")
    impact_preview = payload.get("control_impact_preview")
    if not isinstance(impact_preview, dict) or impact_preview.get("type") != "e9-pedal-lever-impact-preview":
        raise ValueError("Explorer payload requires control_impact_preview")
    controls = impact_preview.get("controls")
    if not isinstance(controls, list) or not controls:
        raise ValueError("Explorer control_impact_preview requires controls")
    ids: set[str] = set()
    for position in positions:
        if not isinstance(position, dict):
            raise ValueError("Explorer position must be a dict")
        if position["id"] in ids:
            raise ValueError(f"Duplicate Explorer row id: {position['id']}")
        ids.add(str(position["id"]))
        normalize_explorer_key(str(position["key"]))
        if position["fret"] < 0 or position["fret"] > 24:
            raise ValueError("Explorer row fret out of range")
        strings = position["strings"]
        if not isinstance(strings, list) or not strings or any(string < 1 or string > 10 for string in strings):
            raise ValueError("Explorer row strings out of range")
        if position["string_group"] != grip_label(tuple(strings)):
            raise ValueError("Explorer row string_group mismatch")
        if position["pitch_validated"] is not True:
            raise ValueError("Explorer row must be pitch validated")
        if position["availability_status"] != "available":
            raise ValueError("Explorer row must be available for MVP display")
        display_notes = position.get("display_notes")
        if not isinstance(display_notes, dict) or set(display_notes) != {str(string) for string in strings}:
            raise ValueError("Explorer row display_notes must match played strings")
        control_impacts = position.get("control_impacts")
        if not isinstance(control_impacts, list):
            raise ValueError("Explorer row control_impacts must be a list")
