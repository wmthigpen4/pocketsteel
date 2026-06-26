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

DEFAULT_COPEDENT_ID = "emmons-e9-basic"
DAY_COPEDENT_ID = "day-e9-basic"
CUSTOM_LKV_COPEDENT_ID = "custom-e9-lkv"
MY_COPEDENT_ID = "my-copedent-e9"

ControlType = Literal["pedal", "lever"]
ProfileStatus = Literal["app-default", "enabled", "disabled"]

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


@dataclass(frozen=True)
class E9CopedentControl:
    id: str
    label: str
    control_type: ControlType
    physical_position: str
    changes: tuple[E9CopedentChange, ...]
    mechanical_name: str = ""
    notes: str = ""

    @property
    def affected_strings(self) -> tuple[int, ...]:
        return tuple(change.string for change in self.changes)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.id,
            "label": self.label,
            "control_type": self.control_type,
            "physical_position": self.physical_position,
            "affected_strings": list(self.affected_strings),
            "changes": [change.to_dict() for change in self.changes],
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

    @property
    def instrument(self) -> str:
        return "E9"

    @property
    def strings(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {"string": string, "open_note": E9_OPEN_STRINGS[string]}
            for string in sorted(E9_OPEN_STRINGS)
        )

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
        rows: list[dict[str, object]] = []
        for string in sorted(E9_OPEN_STRINGS):
            cells: dict[str, dict[str, object] | None] = {}
            for control in controls:
                change = next((candidate for candidate in control.changes if candidate.string == string), None)
                cells[control.id] = chart_cell_for_change(change) if change else None
            rows.append(
                {
                    "string": string,
                    "open_note": E9_OPEN_STRINGS[string],
                    "cells": cells,
                }
            )
        return {
            "rows": rows,
            "columns": [
                {
                    "id": control.id,
                    "label": control.label,
                    "control_type": control.control_type,
                    "physical_position": control.physical_position,
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
            mechanical_name="B-to-C# raise",
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
            mechanical_name="G#-to-A raise",
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
            mechanical_name="E-to-F# and B-to-C# raise",
            changes=(
                E9CopedentChange(4, "E", "F#"),
                E9CopedentChange(5, "B", "C#"),
            ),
        ),
        E9CopedentControl(
            id="E-raise",
            label="E-raise lever",
            control_type="lever",
            physical_position="LKL",
            mechanical_name="E-to-F raise",
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
            mechanical_name="E-to-Eb/D# lower",
            changes=(
                E9CopedentChange(4, "E", "Eb/D#"),
                E9CopedentChange(8, "E", "Eb/D#"),
            ),
            notes="Physical knee label varies; mechanical E-lower is the source of truth.",
        ),
        E9CopedentControl(
            id="D-lower",
            label="D-lower lever",
            control_type="lever",
            physical_position="RKR",
            mechanical_name="2nd-string half/full stop and 9th-string lower",
            changes=(
                E9CopedentChange(2, "D#", "D", notes="Half-stop representation; full-stop C# varies by setup."),
                E9CopedentChange(9, "D", "C#"),
            ),
        ),
        E9CopedentControl(
            id="G-lower",
            label="G-lower lever",
            control_type="lever",
            physical_position="RKL",
            mechanical_name="6th-string G# lower family",
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


def _user_control(state: CopedentState, *, control_id: str, label: str, control_type: ControlType) -> E9CopedentControl:
    return E9CopedentControl(
        id=control_id,
        label=label,
        control_type=control_type,
        physical_position=state.mechanical_label,
        mechanical_name=state.display_label,
        changes=tuple(_user_string_change_to_e9(change) for change in state.changes),
        notes=state.notes,
    )


def custom_lkv_controls() -> tuple[E9CopedentControl, ...]:
    states = {state.id: state for state in USER_E9_COPEDENT.states}
    ordered_states: tuple[tuple[str, str, str, ControlType], ...] = (
        ("P1", "A", "A pedal", "pedal"),
        ("P2", "B", "B pedal", "pedal"),
        ("P3", "C", "C pedal", "pedal"),
        ("LKL", "E-raise", "E-raise / F lever", "lever"),
        ("LKR", "E-lower", "E-lower lever", "lever"),
        ("LKV", "B-to-Bb", "B-to-Bb vertical", "lever"),
        ("RKL.half", "RKL-half", "RKL half-stop", "lever"),
        ("RKL.full", "G-lower", "RKL full-stop / G-lower", "lever"),
        ("RKR.half", "D-lower", "D-lower half-stop", "lever"),
        ("RKR.full", "RKR-full", "RKR full-stop", "lever"),
    )
    return tuple(
        _user_control(states[state_id], control_id=control_id, label=label, control_type=control_type)
        for state_id, control_id, label, control_type in ordered_states
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


def available_e9_copedents() -> tuple[E9CopedentProfile, ...]:
    return (EMMONS_E9, DAY_E9, CUSTOM_LKV_E9, MY_COPEDENT_E9)


def selectable_e9_copedents() -> tuple[E9CopedentProfile, ...]:
    return tuple(profile for profile in available_e9_copedents() if profile.enabled)


def get_e9_copedent_profile(copedent_id: str | None = None) -> E9CopedentProfile:
    requested = copedent_id or DEFAULT_COPEDENT_ID
    for profile in available_e9_copedents():
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


def control_labels_for_profile(copedent_id: str | None = None) -> dict[str, str]:
    profile = get_e9_copedent_profile(copedent_id)
    return {control.id: control.label for control in profile.controls}


def control_types_for_profile(copedent_id: str | None = None) -> dict[str, ControlType]:
    profile = get_e9_copedent_profile(copedent_id)
    return {control.id: control.control_type for control in profile.controls}


def control_order_for_profile(copedent_id: str | None = None) -> tuple[str, ...]:
    return get_e9_copedent_profile(copedent_id).control_order
