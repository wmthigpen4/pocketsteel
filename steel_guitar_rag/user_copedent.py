"""Structured private E9 copedent for the user's Emmons Lashley LeGrande.

This is private/user-specific music logic. It is safe to use for authorized
private-profile answers and for deterministic E9 mechanics, but it should not
be exposed as public source evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


COMMON_GRIPS: tuple[str, ...] = ("3-4-5", "4-5-6", "5-6-8", "5-7-8", "6-8-10")


@dataclass(frozen=True)
class StringChange:
    string: int
    from_note: str
    to_note: str
    direction: str = "raises"
    confidence: str = "confirmed"
    note: str = ""

    def phrase(self) -> str:
        return f"string {self.string} {self.from_note} to {self.to_note}"


@dataclass(frozen=True)
class CopedentState:
    id: str
    physical_control: str
    user_label: str
    mechanical_label: str
    travel: str
    changes: tuple[StringChange, ...]
    confidence: str = "confirmed"
    notes: str = ""

    @property
    def display_label(self) -> str:
        if self.mechanical_label == self.user_label:
            return self.user_label
        return f"{self.mechanical_label} / {self.user_label}"

    def change_summary(self) -> str:
        if not self.changes:
            return "no structured changes"
        by_target: dict[tuple[str, str, str], list[int]] = {}
        parts: list[str] = []
        for change in self.changes:
            key = (change.direction, change.from_note, change.to_note)
            by_target.setdefault(key, []).append(change.string)
        for (direction, from_note, to_note), strings in by_target.items():
            string_label = "string" if len(strings) == 1 else "strings"
            parts.append(f"{direction} {string_label} {format_string_list(strings)} {from_note} to {to_note}")
        summary = "; ".join(parts)
        if self.confidence != "confirmed":
            summary = f"{summary} ({self.confidence}: {self.notes})"
        return summary


@dataclass(frozen=True)
class UserE9Copedent:
    instrument_label: str
    open_strings: dict[int, str]
    states: tuple[CopedentState, ...]
    common_grips: tuple[str, ...]
    notes: tuple[str, ...] = ()


USER_E9_COPEDENT = UserE9Copedent(
    instrument_label="Emmons Lashley LeGrande E9",
    open_strings={
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
    },
    states=(
        CopedentState(
            id="P1",
            physical_control="P1",
            user_label="A pedal",
            mechanical_label="P1",
            travel="pedal",
            changes=(StringChange(5, "B", "C#"), StringChange(10, "B", "C#")),
        ),
        CopedentState(
            id="P2",
            physical_control="P2",
            user_label="B pedal",
            mechanical_label="P2",
            travel="pedal",
            changes=(StringChange(3, "G#", "A"), StringChange(6, "G#", "A")),
        ),
        CopedentState(
            id="P3",
            physical_control="P3",
            user_label="C pedal",
            mechanical_label="P3",
            travel="pedal",
            changes=(StringChange(4, "E", "F#"), StringChange(5, "B", "C#")),
        ),
        CopedentState(
            id="LKL",
            physical_control="LKL",
            user_label="F lever",
            mechanical_label="LKL",
            travel="full",
            changes=(StringChange(4, "E", "F"), StringChange(8, "E", "F")),
        ),
        CopedentState(
            id="LKR",
            physical_control="LKR",
            user_label="E-lower",
            mechanical_label="LKR",
            travel="full",
            changes=(StringChange(4, "E", "Eb/D#", "lowers"), StringChange(8, "E", "Eb/D#", "lowers")),
        ),
        CopedentState(
            id="LKV",
            physical_control="LKV",
            user_label="vertical/Bb",
            mechanical_label="LKV",
            travel="vertical",
            changes=(StringChange(5, "B", "Bb/A#", "lowers"), StringChange(10, "B", "Bb/A#", "lowers")),
        ),
        CopedentState(
            id="RKL.half",
            physical_control="RKL",
            user_label="RKL",
            mechanical_label="RKL",
            travel="half-stop / partial travel",
            changes=(StringChange(1, "F#", "G"), StringChange(6, "G#", "G", "lowers")),
            notes="User confirmed string 7 F# does not raise to G on RKL/RKLL.",
        ),
        CopedentState(
            id="RKL.full",
            physical_control="RKL",
            user_label="RKLL",
            mechanical_label="RKL",
            travel="full-travel / double-stop",
            changes=(
                StringChange(1, "F#", "G"),
                StringChange(6, "G#", "F#", "lowers"),
            ),
            notes="User confirmed string 7 F# does not raise to G on RKL/RKLL.",
        ),
        CopedentState(
            id="RKR.half",
            physical_control="RKR",
            user_label="RKR",
            mechanical_label="RKR",
            travel="half-stop / partial travel",
            changes=(StringChange(2, "D#", "D", "lowers"), StringChange(9, "D", "C#", "lowers")),
        ),
        CopedentState(
            id="RKR.full",
            physical_control="RKR",
            user_label="RKRR",
            mechanical_label="RKR",
            travel="full-travel / double-stop",
            changes=(StringChange(2, "D#", "C#", "lowers"), StringChange(9, "D", "C#", "lowers")),
            notes="User confirmed string 9 open D lowers to C# at both RKR half-stop and RKRR full-stop.",
        ),
    ),
    common_grips=COMMON_GRIPS,
    notes=(
        "RKL/RKLL are modeled as half/full states of the same physical RKL lever.",
        "RKR/RKRR are modeled as half/full states of the same physical RKR lever.",
        "String 7 F# does not raise to G on RKL/RKLL.",
    ),
)


CONTROL_ALIASES: dict[str, str] = {
    "a": "P1",
    "a pedal": "P1",
    "p1": "P1",
    "b": "P2",
    "b pedal": "P2",
    "p2": "P2",
    "c": "P3",
    "c pedal": "P3",
    "p3": "P3",
    "f": "LKL",
    "f lever": "LKL",
    "e-raise": "LKL",
    "e-raise/f": "LKL",
    "lkl": "LKL",
    "e": "LKR",
    "e-lower": "LKR",
    "e lower": "LKR",
    "lkr": "LKR",
    "vertical": "LKV",
    "vertical/bb": "LKV",
    "bb": "LKV",
    "lkv": "LKV",
    "rkl": "RKL.half",
    "rkll": "RKL.full",
    "rkl.half": "RKL.half",
    "rkl.full": "RKL.full",
    "6-lower": "RKL.full",
    "rkr": "RKR.half",
    "rkrr": "RKR.full",
    "rkr.half": "RKR.half",
    "rkr.full": "RKR.full",
    "2/9-lower": "RKR.full",
}


def open_strings_dict(copedent: UserE9Copedent = USER_E9_COPEDENT) -> dict[int, str]:
    return dict(copedent.open_strings)


def states_by_id(copedent: UserE9Copedent = USER_E9_COPEDENT) -> dict[str, CopedentState]:
    return {state.id: state for state in copedent.states}


def state_for_label(label: str, copedent: UserE9Copedent = USER_E9_COPEDENT) -> CopedentState:
    normalized = normalize_label(label)
    state_id = CONTROL_ALIASES.get(normalized, label)
    try:
        return states_by_id(copedent)[state_id]
    except KeyError as exc:
        raise ValueError(f"Unknown copedent control: {label}") from exc


def resolve_changes(labels: tuple[str, ...] | list[str] | str, copedent: UserE9Copedent = USER_E9_COPEDENT) -> tuple[StringChange, ...]:
    if isinstance(labels, str):
        labels = (labels,)
    changes: list[StringChange] = []
    for label in labels:
        changes.extend(state_for_label(label, copedent).changes)
    return tuple(changes)


def apply_changes(labels: tuple[str, ...] | list[str] | str, copedent: UserE9Copedent = USER_E9_COPEDENT) -> dict[int, str]:
    notes = open_strings_dict(copedent)
    for change in resolve_changes(labels, copedent):
        notes[change.string] = change.to_note
    return notes


def supports_standard_major_position_changes(copedent: UserE9Copedent = USER_E9_COPEDENT) -> bool:
    notes = apply_changes(("A", "B", "F"), copedent)
    return (
        notes[5] == "C#"
        and notes[10] == "C#"
        and notes[3] == "A"
        and notes[6] == "A"
        and notes[4] == "F"
        and notes[8] == "F"
    )


def format_common_grips_sentence(copedent: UserE9Copedent = USER_E9_COPEDENT) -> str:
    return (
        "For your saved 10-string E9 profile, your common grips are "
        + ", ".join(copedent.common_grips[:-1])
        + f", and {copedent.common_grips[-1]}."
    )


def format_user_copedent_markdown(copedent: UserE9Copedent = USER_E9_COPEDENT) -> str:
    pedals = [state for state in copedent.states if state.physical_control.startswith("P")]
    levers = [state for state in copedent.states if not state.physical_control.startswith("P")]
    return "\n".join(
        [
            "Your private profile describes a 10-string E9 setup.",
            "",
            "Open tuning",
            markdown_table(("String", "Note"), [(str(string), note) for string, note in copedent.open_strings.items()]),
            "",
            "Pedals",
            markdown_table(
                ("Pedal", "Change"),
                [(state.display_label, state.change_summary()) for state in pedals],
            ),
            "",
            "Levers",
            markdown_table(
                ("Lever", "Change"),
                [(lever_display_label(state), f"{state.travel}: {state.change_summary()}") for state in levers],
            ),
            "",
            "Common grips",
            "\n".join(f"- {grip}" for grip in copedent.common_grips),
        ]
    )


def format_levers_markdown(copedent: UserE9Copedent = USER_E9_COPEDENT) -> str:
    levers = [state for state in copedent.states if not state.physical_control.startswith("P")]
    return "\n".join(
        [
            "Your private E9 profile lists these knee levers and travel states:",
            markdown_table(
                ("Lever", "Change"),
                [(lever_display_label(state), f"{state.travel}: {state.change_summary()}") for state in levers],
            ),
        ]
    )


def format_control_answer(label: str, copedent: UserE9Copedent = USER_E9_COPEDENT) -> str:
    state = state_for_label(label, copedent)
    return f"On your saved 10-string E9 profile, {state.display_label} {state.change_summary()}."


def format_rkl_practice_answer(copedent: UserE9Copedent = USER_E9_COPEDENT) -> str:
    half = state_for_label("RKL", copedent)
    full = state_for_label("RKLL", copedent)
    return (
        f"On your saved 10-string E9 profile, {half.display_label} is the partial-travel RKL state and "
        f"{full.user_label} is the full-travel state.\n\n"
        "What it changes\n"
        f"- RKL: {half.change_summary()}.\n"
        f"- RKLL: {full.change_summary()}.\n\n"
        "Practice it this way\n"
        "- First isolate the string 1 raise so you can hear the half-stop/full-stop travel clearly.\n"
        "- Then add strings 4-5-6 or 5-6-8 and move slowly enough that the lever, bar, and blocking stay even.\n"
        "- Listen for the string 6 half-stop lower to G, then the full-stop lower to F#."
    )


def format_string_list(strings: list[int]) -> str:
    if len(strings) == 1:
        return str(strings[0])
    return ", ".join(str(string) for string in strings[:-1]) + f" and {strings[-1]}"


def lever_display_label(state: CopedentState) -> str:
    if state.id in {"RKL.half", "RKR.half"}:
        return f"{state.mechanical_label} / {state.user_label} half-stop"
    if state.id in {"RKL.full", "RKR.full"}:
        return f"{state.mechanical_label} / {state.user_label} full-stop"
    return state.display_label


def markdown_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", (label or "").strip().lower())
