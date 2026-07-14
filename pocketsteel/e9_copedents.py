"""Deterministic E9 copedent selector and chart data.

This module is intentionally independent from RAG/corpus retrieval. It models
small app-supported E9 setup profiles that can drive Explorer chart rendering
and pedal/lever impact previews.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pocketsteel.user_copedent import CopedentState, StringChange, USER_E9_COPEDENT


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

E9_OPEN_STRING_PITCH_VALUES: dict[int, int] = {
    1: 66,  # F#4
    2: 63,  # D#4
    3: 68,  # G#4
    4: 64,  # E4
    5: 59,  # B3
    6: 56,  # G#3
    7: 54,  # F#3
    8: 52,  # E3
    9: 50,  # D3
    10: 47,  # B2
}

DEFAULT_COPEDENT_ID = "emmons-e9-basic"
DAY_COPEDENT_ID = "day-e9-basic"
CUSTOM_LKV_COPEDENT_ID = "custom-e9-lkv"
MY_COPEDENT_ID = "my-copedent-e9"
SOURCE_ABC_DEFG_COPEDENT_ID = "source-e9-abc-defg-v1"

ControlType = Literal["pedal", "lever"]
ProfileStatus = Literal["app-default", "enabled", "disabled", "source"]

NOTE_TO_SEMITONE: dict[str, int] = {
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


def scientific_pitch_for_value(pitch_value: int) -> str:
    """Return scientific pitch notation where middle C is C4."""
    value = int(pitch_value)
    return f"{CANONICAL_NOTES[value % 12]}{(value // 12) - 1}"


def octave_band_for_value(pitch_value: int) -> str:
    """Return a compact player-facing register band for standard E9."""
    value = int(pitch_value)
    if value <= 54:
        return "lower"
    if value <= 64:
        return "middle"
    return "upper"


@dataclass(frozen=True)
class E9CopedentChange:
    string: int
    from_note: str
    to_note: str
    notes: str = ""

    @property
    def semitones(self) -> int:
        delta = (_note_to_semitone(self.to_note) - _note_to_semitone(self.from_note)) % 12
        if delta > 6:
            delta -= 12
        return delta

    @property
    def direction(self) -> str:
        if self.semitones > 0:
            return "raise"
        if self.semitones < 0:
            return "lower"
        return "none"

    @property
    def arrow(self) -> str:
        if self.semitones > 0:
            return "up"
        if self.semitones < 0:
            return "down"
        return "none"

    @property
    def string_action_description(self) -> str:
        direction = {
            "raise": "raises",
            "lower": "lowers",
        }.get(self.direction, "keeps")
        interval = abs(self.semitones)
        unit = "semitone" if interval == 1 else "semitones"
        if self.direction == "none":
            return f"String {self.string}: {self.from_note} stays {self.to_note}."
        return f"String {self.string}: {direction} {self.from_note} to {self.to_note} ({interval} {unit})."

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "string": self.string,
            "from": self.from_note,
            "to": self.to_note,
            "semitones": self.semitones,
            "direction": self.direction,
            "arrow": self.arrow,
        }
        if self.notes:
            payload["notes"] = self.notes
        return payload

    def string_action(self) -> dict[str, object]:
        payload = self.to_dict()
        payload["description"] = self.string_action_description
        return payload


@dataclass(frozen=True)
class E9CopedentControl:
    id: str
    label: str
    control_type: ControlType
    physical_position: str
    changes: tuple[E9CopedentChange, ...]
    mechanical_name: str = ""
    notes: str = ""
    player_shorthand: tuple[str, ...] = ()
    compatibility_aliases: tuple[str, ...] = ()
    travel: str = ""
    change_type: str = ""

    @property
    def affected_strings(self) -> tuple[int, ...]:
        return tuple(change.string for change in self.changes)

    @property
    def stable_id(self) -> str:
        return self.id

    @property
    def display_label(self) -> str:
        return self.label

    @property
    def resolved_change_type(self) -> str:
        if self.change_type:
            return self.change_type
        directions = {change.direction for change in self.changes if change.direction != "none"}
        if not directions:
            return "none"
        if len(directions) == 1:
            return directions.pop()
        return "mixed"

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.id,
            "stable_id": self.stable_id,
            "label": self.label,
            "display_label": self.display_label,
            "control_type": self.control_type,
            "physical_position": self.physical_position,
            "player_shorthand": list(self.player_shorthand),
            "compatibility_aliases": list(self.compatibility_aliases),
            "travel": self.travel,
            "change_type": self.resolved_change_type,
            "affected_strings": list(self.affected_strings),
            "changes": [change.to_dict() for change in self.changes],
            "string_actions": [change.string_action() for change in self.changes],
        }
        if self.mechanical_name:
            payload["mechanical_name"] = self.mechanical_name
        if self.notes:
            payload["notes"] = self.notes
        return payload


@dataclass(frozen=True)
class E9CopedentProfile:
    id: str
    label: str
    status: ProfileStatus
    pedal_order: tuple[str, ...]
    controls: tuple[E9CopedentControl, ...]
    disabled_reason: str = ""
    notes: str = ""
    open_notes: tuple[tuple[int, str], ...] = ()
    open_pitch_values: tuple[tuple[int, int], ...] = ()

    @property
    def instrument(self) -> str:
        return "E9"

    @property
    def strings(self) -> tuple[dict[str, object], ...]:
        open_notes = self.open_notes_by_string()
        open_pitches = self.open_pitch_values_by_string()
        return tuple(
            {
                "string": string,
                "open_note": open_notes[string],
                "open_pitch_value": open_pitches[string],
                "open_scientific_pitch": scientific_pitch_for_value(open_pitches[string]),
                "open_octave_band": octave_band_for_value(open_pitches[string]),
            }
            for string in sorted(open_notes)
        )

    def open_notes_by_string(self) -> dict[int, str]:
        return dict(self.open_notes) if self.open_notes else dict(E9_OPEN_STRINGS)

    def open_pitch_values_by_string(self) -> dict[int, int]:
        return dict(self.open_pitch_values) if self.open_pitch_values else dict(E9_OPEN_STRING_PITCH_VALUES)

    @property
    def enabled(self) -> bool:
        return self.status != "disabled"

    @property
    def control_order(self) -> tuple[str, ...]:
        control_ids = {control.id for control in self.controls}
        pedal_ids = tuple(control for control in self.pedal_order if control in control_ids)
        non_pedals = tuple(control.id for control in self.controls if control.id not in self.pedal_order)
        return pedal_ids + non_pedals

    def controls_by_id(self) -> dict[str, E9CopedentControl]:
        return {control.id: control for control in self.controls}

    def ordered_controls(self) -> tuple[E9CopedentControl, ...]:
        by_id = self.controls_by_id()
        return tuple(by_id[control_id] for control_id in self.control_order if control_id in by_id)

    def selector_option(self) -> dict[str, object]:
        option: dict[str, object] = {
            "id": self.id,
            "label": self.label,
            "status": "disabled" if not self.enabled else "enabled",
        }
        if self.disabled_reason:
            option["disabled_reason"] = self.disabled_reason
        return option

    def chart(self) -> dict[str, object]:
        controls = self.ordered_controls()
        open_notes = self.open_notes_by_string()
        rows: list[dict[str, object]] = []
        for string in sorted(open_notes):
            cells: dict[str, dict[str, object] | None] = {}
            for control in controls:
                change = next((candidate for candidate in control.changes if candidate.string == string), None)
                cells[control.id] = chart_cell_for_change(change) if change else None
            rows.append(
                {
                    "string": string,
                    "open_note": open_notes[string],
                    "cells": cells,
                }
            )
        return {
            "rows": rows,
            "columns": [
                {
                    "id": control.id,
                    "stable_id": control.stable_id,
                    "label": control.label,
                    "display_label": control.display_label,
                    "control_type": control.control_type,
                    "physical_position": control.physical_position,
                    "mechanical_name": control.mechanical_name,
                    "player_shorthand": list(control.player_shorthand),
                    "compatibility_aliases": list(control.compatibility_aliases),
                    "travel": control.travel,
                    "change_type": control.resolved_change_type,
                    "affected_strings": list(control.affected_strings),
                    "string_actions": [change.string_action() for change in control.changes],
                }
                for control in controls
            ],
        }

    def to_dict(self, *, include_options: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.id,
            "label": self.label,
            "instrument": self.instrument,
            "status": self.status,
            "pedal_order": list(self.pedal_order),
            "strings": list(self.strings),
            "controls": [control.to_dict() for control in self.ordered_controls()],
            "chart": self.chart(),
            "source_context": SOURCE_CONTEXT,
            "warnings": [
                "Copedents vary. This chart shows the setup currently used for guidance.",
            ],
        }
        if self.disabled_reason:
            payload["disabled_reason"] = self.disabled_reason
        if self.notes:
            payload["notes"] = self.notes
        if include_options:
            payload["available_options"] = [profile.selector_option() for profile in available_e9_copedents()]
        return payload


SOURCE_CONTEXT: list[dict[str, str]] = []


def _note_to_semitone(note: str) -> int:
    root = str(note or "").split("/", 1)[0].strip()
    if root not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported copedent note: {note}")
    return NOTE_TO_SEMITONE[root]


def chart_cell_for_change(change: E9CopedentChange | None) -> dict[str, object] | None:
    if change is None:
        return None
    return {
        "from": change.from_note,
        "to": change.to_note,
        "label": f"{change.from_note} -> {change.to_note}",
        "semitones": change.semitones,
        "direction": change.direction,
        "arrow": change.arrow,
    }


def standard_e9_controls_for_positions(physical_positions: dict[str, str]) -> tuple[E9CopedentControl, ...]:
    return (
        E9CopedentControl(
            id="A",
            label="A pedal",
            control_type="pedal",
            physical_position=physical_positions["A"],
            mechanical_name="B-to-C# raise on strings 5 and 10",
            player_shorthand=("A",),
            compatibility_aliases=(physical_positions["A"],),
            travel="pedal",
            change_type="raise",
            changes=(
                E9CopedentChange(5, "B", "C#"),
                E9CopedentChange(10, "B", "C#"),
            ),
        ),
        E9CopedentControl(
            id="B",
            label="B pedal",
            control_type="pedal",
            physical_position=physical_positions["B"],
            mechanical_name="G#-to-A raise on strings 3 and 6",
            player_shorthand=("B",),
            compatibility_aliases=(physical_positions["B"],),
            travel="pedal",
            change_type="raise",
            changes=(
                E9CopedentChange(3, "G#", "A"),
                E9CopedentChange(6, "G#", "A"),
            ),
        ),
        E9CopedentControl(
            id="C",
            label="C pedal",
            control_type="pedal",
            physical_position=physical_positions["C"],
            mechanical_name="E-to-F# and B-to-C# raise on strings 4 and 5",
            player_shorthand=("C",),
            compatibility_aliases=(physical_positions["C"],),
            travel="pedal",
            change_type="raise",
            changes=(
                E9CopedentChange(4, "E", "F#"),
                E9CopedentChange(5, "B", "C#"),
            ),
        ),
        E9CopedentControl(
            id="E-raise",
            label="E raise (F lever)",
            control_type="lever",
            physical_position="LKL",
            mechanical_name="E-to-F raise on strings 4 and 8",
            player_shorthand=("F", "F lever"),
            compatibility_aliases=("E-raise", "E raise", "LKL"),
            travel="full",
            change_type="raise",
            changes=(
                E9CopedentChange(4, "E", "F"),
                E9CopedentChange(8, "E", "F"),
            ),
            notes="Physical knee label varies; mechanical E-raise is the source of truth.",
        ),
        E9CopedentControl(
            id="E-lower",
            label="E-lower lever",
            control_type="lever",
            physical_position="LKR",
            mechanical_name="E-to-Eb/D# lower on strings 4 and 8",
            player_shorthand=("E", "E lever"),
            compatibility_aliases=("E-lower", "E lower", "LKR"),
            travel="full",
            change_type="lower",
            changes=(
                E9CopedentChange(4, "E", "Eb/D#"),
                E9CopedentChange(8, "E", "Eb/D#"),
            ),
            notes="Physical knee label varies; mechanical E-lower is the source of truth.",
        ),
        E9CopedentControl(
            id="D-lower",
            label="D lower half-stop",
            control_type="lever",
            physical_position="RKR",
            mechanical_name="D#-to-D half-stop on string 2 plus D-to-C# lower on string 9",
            player_shorthand=("D-", "D half-stop"),
            compatibility_aliases=("D-lower", "RKR"),
            travel="half-stop",
            change_type="lower",
            changes=(
                E9CopedentChange(2, "D#", "D", notes="Half-stop representation; full-stop C# varies by setup."),
                E9CopedentChange(9, "D", "C#"),
            ),
        ),
        E9CopedentControl(
            id="G-lower",
            label="RKL G raise/lower",
            control_type="lever",
            physical_position="RKL",
            mechanical_name="string 1 F#-to-G raise plus string 6 G#-to-F# lower",
            player_shorthand=("G+", "G-", "RKL"),
            compatibility_aliases=("G-lower", "RKL"),
            travel="full",
            change_type="mixed",
            changes=(
                E9CopedentChange(1, "F#", "G"),
                E9CopedentChange(6, "G#", "F#"),
            ),
            notes="Right-knee changes vary. This app profile makes the represented change explicit.",
        ),
    )


def _user_string_change_to_e9(change: StringChange) -> E9CopedentChange:
    return E9CopedentChange(
        string=change.string,
        from_note=change.from_note,
        to_note=change.to_note,
        notes=change.note,
    )


def _user_control(
    state: CopedentState,
    *,
    control_id: str,
    label: str,
    control_type: ControlType,
    mechanical_name: str,
    player_shorthand: tuple[str, ...] = (),
    compatibility_aliases: tuple[str, ...] = (),
    travel: str = "",
    change_type: str = "",
) -> E9CopedentControl:
    return E9CopedentControl(
        id=control_id,
        label=label,
        control_type=control_type,
        physical_position=state.physical_control,
        mechanical_name=mechanical_name,
        player_shorthand=player_shorthand,
        compatibility_aliases=compatibility_aliases,
        travel=travel or state.travel,
        change_type=change_type,
        changes=tuple(_user_string_change_to_e9(change) for change in state.changes),
        notes=state.notes,
    )


def custom_lkv_controls() -> tuple[E9CopedentControl, ...]:
    states = {state.id: state for state in USER_E9_COPEDENT.states}
    ordered_states: tuple[tuple[str, str, str, ControlType, str, tuple[str, ...], tuple[str, ...], str, str], ...] = (
        ("P1", "A", "A pedal", "pedal", "B-to-C# raise on strings 5 and 10", ("A",), ("P1",), "pedal", "raise"),
        ("P2", "B", "B pedal", "pedal", "G#-to-A raise on strings 3 and 6", ("B",), ("P2",), "pedal", "raise"),
        ("P3", "C", "C pedal", "pedal", "E-to-F# and B-to-C# raise on strings 4 and 5", ("C",), ("P3",), "pedal", "raise"),
        ("LKL", "E-raise", "E raise (F lever)", "lever", "E-to-F raise on strings 4 and 8", ("F", "F lever"), ("LKL",), "full", "raise"),
        ("LKR", "E-lower", "E-lower lever", "lever", "E-to-Eb/D# lower on strings 4 and 8", ("E", "E lever"), ("LKR",), "full", "lower"),
        ("LKV", "B-to-Bb", "B-to-Bb vertical", "lever", "B-to-Bb/A# lower on strings 5 and 10", ("V", "vertical", "LKV"), ("B-to-A#", "LKV"), "full", "lower"),
        ("RKL.half", "RKL-half", "RKL half-stop", "lever", "string 1 F#-to-G raise plus string 6 G#-to-G lower", ("G+", "RKL"), ("RKL", "RKL-half"), "half-stop", "mixed"),
        ("RKL.full", "G-lower", "RKL full-stop / G lower", "lever", "string 1 F#-to-G raise plus string 6 G#-to-F# lower", ("G+", "G-", "RKLL"), ("G-lower", "RKL.full", "RKLL"), "full-stop", "mixed"),
        ("RKR.half", "D-lower", "D lower half-stop", "lever", "D#-to-D half-stop on string 2 plus D-to-C# lower on string 9", ("D-", "RKR"), ("D-lower", "RKR.half"), "half-stop", "lower"),
        ("RKR.full", "RKR-full", "D lower full-stop", "lever", "D#-to-C# full-stop on string 2 plus D-to-C# lower on string 9", ("D--", "RKRR"), ("RKR-full", "RKR.full", "RKRR"), "full-stop", "lower"),
    )
    return tuple(
        _user_control(
            states[state_id],
            control_id=control_id,
            label=label,
            control_type=control_type,
            mechanical_name=mechanical_name,
            player_shorthand=player_shorthand,
            compatibility_aliases=compatibility_aliases,
            travel=travel,
            change_type=change_type,
        )
        for state_id, control_id, label, control_type, mechanical_name, player_shorthand, compatibility_aliases, travel, change_type in ordered_states
        if state_id in states
    )


EMMONS_E9 = E9CopedentProfile(
    id=DEFAULT_COPEDENT_ID,
    label="Emmons E9",
    status="app-default",
    pedal_order=("A", "B", "C"),
    controls=standard_e9_controls_for_positions({"A": "P1", "B": "P2", "C": "P3"}),
    notes="App default. Named A/B/C changes follow common E9 semantics; physical pedal order is A-B-C.",
)

DAY_E9 = E9CopedentProfile(
    id=DAY_COPEDENT_ID,
    label="Day E9",
    status="enabled",
    pedal_order=("C", "B", "A"),
    controls=standard_e9_controls_for_positions({"C": "P1", "B": "P2", "A": "P3"}),
    notes="Named A/B/C musical changes match Emmons E9; physical pedal order is C-B-A.",
)

CUSTOM_LKV_E9 = E9CopedentProfile(
    id=CUSTOM_LKV_COPEDENT_ID,
    label="Custom E9 (with LKV)",
    status="enabled",
    pedal_order=("A", "B", "C"),
    controls=custom_lkv_controls(),
    notes="Custom E9 setup with an LKV B-to-Bb vertical lever.",
)

MY_COPEDENT_E9 = E9CopedentProfile(
    id=MY_COPEDENT_ID,
    label="My Copedent (E9)",
    status="disabled",
    pedal_order=(),
    controls=(),
    disabled_reason="Coming soon in Backstage",
)


SOURCE_ABC_DEFG_E9 = E9CopedentProfile(
    id=SOURCE_ABC_DEFG_COPEDENT_ID,
    label="Source E9 A-B-C / D-E-F-G",
    status="source",
    pedal_order=("A", "B", "C"),
    controls=(
        E9CopedentControl(
            id="A",
            label="A pedal",
            control_type="pedal",
            physical_position="A",
            mechanical_name="B-to-C# raise on strings 5 and 10",
            changes=(E9CopedentChange(5, "B", "C#"), E9CopedentChange(10, "B", "C#")),
        ),
        E9CopedentControl(
            id="B",
            label="B pedal",
            control_type="pedal",
            physical_position="B",
            mechanical_name="G#-to-A raise on strings 3 and 6",
            changes=(E9CopedentChange(3, "G#", "A"), E9CopedentChange(6, "G#", "A")),
        ),
        E9CopedentControl(
            id="C",
            label="C pedal",
            control_type="pedal",
            physical_position="C",
            mechanical_name="E-to-F# and B-to-C# raise on strings 4 and 5",
            changes=(E9CopedentChange(4, "E", "F#"), E9CopedentChange(5, "B", "C#")),
        ),
        E9CopedentControl(
            id="D",
            label="D lever",
            control_type="lever",
            physical_position="D",
            mechanical_name="D#-to-D lower on string 2 only",
            changes=(E9CopedentChange(2, "D#", "D"),),
        ),
        E9CopedentControl(
            id="E",
            label="E lever",
            control_type="lever",
            physical_position="E",
            mechanical_name="E-to-Eb lower on strings 4 and 8",
            changes=(E9CopedentChange(4, "E", "Eb"), E9CopedentChange(8, "E", "Eb")),
        ),
        E9CopedentControl(
            id="F",
            label="F lever",
            control_type="lever",
            physical_position="F",
            mechanical_name="E-to-F raise on strings 4 and 8",
            changes=(E9CopedentChange(4, "E", "F"), E9CopedentChange(8, "E", "F")),
        ),
        E9CopedentControl(
            id="G",
            label="G lever",
            control_type="lever",
            physical_position="G",
            mechanical_name="F#-to-G raise on strings 1 and 7",
            changes=(E9CopedentChange(1, "F#", "G"), E9CopedentChange(7, "F#", "G")),
        ),
    ),
    notes=(
        "Reviewed source profile from the supplied floor-pedal and knee-lever chart. "
        "It is decoding evidence only and is never selected as the app default."
    ),
)


def available_e9_copedents() -> tuple[E9CopedentProfile, ...]:
    return (EMMONS_E9, DAY_E9, CUSTOM_LKV_E9, MY_COPEDENT_E9)


def known_e9_copedents() -> tuple[E9CopedentProfile, ...]:
    """Return app profiles plus source-only decoding profiles."""

    return (*available_e9_copedents(), SOURCE_ABC_DEFG_E9)


def selectable_e9_copedents() -> tuple[E9CopedentProfile, ...]:
    return tuple(profile for profile in available_e9_copedents() if profile.enabled)


def get_e9_copedent_profile(copedent_id: str | None = None) -> E9CopedentProfile:
    requested = copedent_id or DEFAULT_COPEDENT_ID
    for profile in known_e9_copedents():
        if profile.id == requested:
            if not profile.enabled:
                raise ValueError(f"E9 copedent profile is disabled: {requested}")
            return profile
    raise ValueError(f"Unsupported E9 copedent profile: {requested}")


def selected_copedent_payload(copedent_id: str | None = None) -> dict[str, object]:
    return get_e9_copedent_profile(copedent_id).to_dict(include_options=True)


def control_changes_for_profile(copedent_id: str | None = None) -> dict[str, dict[int, str]]:
    profile = get_e9_copedent_profile(copedent_id)
    return {
        control.id: {change.string: change.to_note for change in control.changes}
        for control in profile.controls
    }


def controls_by_id_for_profile(copedent_id: str | None = None) -> dict[str, E9CopedentControl]:
    return get_e9_copedent_profile(copedent_id).controls_by_id()


def control_labels_for_profile(copedent_id: str | None = None) -> dict[str, str]:
    profile = get_e9_copedent_profile(copedent_id)
    return {control.id: control.label for control in profile.controls}


def control_types_for_profile(copedent_id: str | None = None) -> dict[str, ControlType]:
    profile = get_e9_copedent_profile(copedent_id)
    return {control.id: control.control_type for control in profile.controls}


def control_order_for_profile(copedent_id: str | None = None) -> tuple[str, ...]:
    return get_e9_copedent_profile(copedent_id).control_order
