"""Copedent-neutral mechanics and source-to-target action transfer.

The arranger learns and ranks musical intent separately from the physical
labels on any one guitar.  This module is the deterministic boundary: it
resolves a profile's actual string changes, validates custom E9 profiles, and
maps source actions only when their effects are safe on every sounding or
sustained string.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import re
from typing import Any, Mapping, Sequence

from pocketsteel.e9_copedents import (
    CANONICAL_NOTES,
    DEFAULT_COPEDENT_ID,
    E9_OPEN_STRING_PITCH_VALUES,
    E9CopedentChange,
    E9CopedentControl,
    E9CopedentProfile,
    NOTE_TO_SEMITONE,
    get_e9_copedent_profile,
)
from pocketsteel.tab_engine import CopedentProfile, PedalLeverEffect


_CANONICAL_ARRANGER_CODES = {
    "E-raise": "F",
    "E-lower": "E",
    "B-to-Bb": "V",
    "G-lower": "G",
    "D-lower": "D",
}


@dataclass(frozen=True)
class TransferResult:
    source_controls: tuple[str, ...]
    target_controls: tuple[str, ...]
    protected_strings: tuple[int, ...]
    extra_effect_strings: tuple[int, ...]
    exact: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "sourceControls": list(self.source_controls),
            "targetControls": list(self.target_controls),
            "protectedStrings": list(self.protected_strings),
            "extraEffectStrings": list(self.extra_effect_strings),
            "exact": self.exact,
            "reason": self.reason,
        }


def _normalized_alias(value: object) -> str:
    return re.sub(r"[^a-z0-9#+-]+", "", str(value or "").strip().lower())


def arranger_code(control: E9CopedentControl) -> str:
    """Return the compact tab code while retaining the profile control identity."""

    return _CANONICAL_ARRANGER_CODES.get(control.id, control.id)


def _control_aliases(control: E9CopedentControl) -> set[str]:
    aliases = {
        control.id,
        control.label,
        control.physical_position,
        arranger_code(control),
        *control.player_shorthand,
        *control.compatibility_aliases,
    }
    return {_normalized_alias(alias) for alias in aliases if str(alias or "").strip()}


def resolve_control(profile: E9CopedentProfile, value: object) -> E9CopedentControl:
    requested = _normalized_alias(value)
    if not requested:
        raise ValueError("A copedent control label is required.")
    exact_id = next((control for control in profile.controls if _normalized_alias(control.id) == requested), None)
    if exact_id is not None:
        return exact_id
    matches = [control for control in profile.controls if requested in _control_aliases(control)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"Control {value!r} is not present on {profile.label}.")
    raise ValueError(f"Control {value!r} is ambiguous on {profile.label}.")


def normalize_controls(profile: E9CopedentProfile, controls: Sequence[object]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in controls:
        code = arranger_code(resolve_control(profile, value))
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def control_delta_for_string(profile: E9CopedentProfile, control_value: object, string: int) -> int:
    control = resolve_control(profile, control_value)
    return sum(change.semitones for change in control.changes if change.string == int(string))


def controls_delta_by_string(
    profile: E9CopedentProfile,
    controls: Sequence[object],
) -> dict[int, int]:
    deltas: dict[int, int] = {}
    for value in controls:
        control = resolve_control(profile, value)
        for change in control.changes:
            deltas[change.string] = deltas.get(change.string, 0) + change.semitones
    return {string: delta for string, delta in deltas.items() if delta}


def control_affects_string(profile: E9CopedentProfile, control: object, string: int) -> bool:
    return control_delta_for_string(profile, control, string) != 0


def absolute_pitch_for_profile(
    profile: E9CopedentProfile,
    string: int,
    fret: int,
    controls: Sequence[object] = (),
) -> int:
    open_pitches = profile.open_pitch_values_by_string()
    if int(string) not in open_pitches:
        raise ValueError(f"String {string} is not present on {profile.label}.")
    return int(open_pitches[int(string)]) + int(fret) + sum(
        control_delta_for_string(profile, control, int(string)) for control in controls
    )


def note_name_for_profile_position(
    profile: E9CopedentProfile,
    string: int,
    fret: int,
    controls: Sequence[object] = (),
) -> str:
    return CANONICAL_NOTES[absolute_pitch_for_profile(profile, string, fret, controls) % 12]


def control_display_label(profile: E9CopedentProfile, value: object) -> str:
    control = resolve_control(profile, value)
    physical = str(control.physical_position or "").strip()
    label = str(control.label or control.id).strip()
    if physical and _normalized_alias(physical) not in _normalized_alias(label):
        return f"{label} ({physical})"
    return label


def candidate_control_states(profile: E9CopedentProfile) -> tuple[tuple[str, ...], ...]:
    """Enumerate compact, non-inert control postures for arrangement search.

    The current Melody Studio vocabulary uses open, one-control, and common
    two-control postures.  Controls that move the same string are not combined
    because their chart deltas cannot safely be assumed additive.
    """

    controls = tuple(profile.ordered_controls())
    states: list[tuple[str, ...]] = [()]
    states.extend((arranger_code(control),) for control in controls)
    for left, right in combinations(controls, 2):
        if left.physical_position and left.physical_position == right.physical_position:
            continue
        if set(left.affected_strings).intersection(right.affected_strings):
            continue
        states.append((arranger_code(left), arranger_code(right)))
    return tuple(dict.fromkeys(states))


def tab_profile_for_e9(profile: E9CopedentProfile) -> CopedentProfile:
    changes: dict[str, PedalLeverEffect] = {}
    aliases: dict[str, str] = {}
    control_labels: dict[str, str] = {}
    for control in profile.controls:
        code = arranger_code(control)
        changes[code] = PedalLeverEffect(code, control_display_label(profile, control.id), control.affected_strings)
        control_labels[control.physical_position or code] = code
        for alias in _control_aliases(control):
            aliases[alias] = code
    return CopedentProfile(
        id=profile.id,
        label=profile.label,
        open_strings=profile.open_notes_by_string(),
        changes=changes,
        control_labels=control_labels,
        aliases=aliases,
    )


def normalized_mechanical_action(
    profile: E9CopedentProfile,
    *,
    string: int,
    fret: int,
    controls: Sequence[object],
) -> dict[str, object]:
    start_pitch = profile.open_pitch_values_by_string()[int(string)] + int(fret)
    destination_pitch = absolute_pitch_for_profile(profile, string, fret, controls)
    return {
        "copedentId": profile.id,
        "string": int(string),
        "fret": int(fret),
        "startPitch": start_pitch,
        "destinationPitch": destination_pitch,
        "semitoneChange": destination_pitch - start_pitch,
        "controls": list(normalize_controls(profile, controls)),
        "controlEffects": [
            {
                "controlId": resolve_control(profile, control).id,
                "string": change.string,
                "from": change.from_note,
                "to": change.to_note,
                "semitones": change.semitones,
            }
            for control in controls
            for change in resolve_control(profile, control).changes
        ],
    }


def transfer_controls(
    source_profile: E9CopedentProfile,
    source_controls: Sequence[object],
    target_profile: E9CopedentProfile,
    *,
    sounding_strings: Sequence[int],
    sustained_strings: Sequence[int] = (),
) -> TransferResult:
    """Map an action by effect, allowing extras only off protected strings."""

    protected = tuple(sorted({int(string) for string in (*sounding_strings, *sustained_strings)}))
    source_normalized = normalize_controls(source_profile, source_controls)
    required = controls_delta_by_string(source_profile, source_controls)
    required_on_protected = {string: required.get(string, 0) for string in protected}
    choices: list[tuple[tuple[int, int, tuple[str, ...]], tuple[str, ...], tuple[int, ...]]] = []
    for state in candidate_control_states(target_profile):
        target = controls_delta_by_string(target_profile, state)
        if any(target.get(string, 0) != delta for string, delta in required_on_protected.items()):
            continue
        if not state and any(required_on_protected.values()):
            continue
        extras = tuple(sorted(string for string, delta in target.items() if delta and string not in protected))
        choices.append(((len(state), len(extras), state), state, extras))
    if not choices:
        return TransferResult(
            source_controls=source_normalized,
            target_controls=(),
            protected_strings=protected,
            extra_effect_strings=(),
            exact=False,
            reason="No target control posture reproduces the required effects on every sounding or sustained string.",
        )
    _rank, target_controls, extras = min(choices, key=lambda item: item[0])
    return TransferResult(
        source_controls=source_normalized,
        target_controls=target_controls,
        protected_strings=protected,
        extra_effect_strings=extras,
        exact=True,
        reason=(
            "Equivalent mechanical effect; extra changes occur only on non-sounding, non-sustained strings."
            if extras
            else "Equivalent mechanical effect on the protected strings."
        ),
    )


def _note_pc(note: object) -> int:
    root = str(note or "").split("/", 1)[0].strip().replace("♯", "#").replace("♭", "b")
    if root not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported copedent note: {note}")
    return NOTE_TO_SEMITONE[root]


def _open_pitch_near_standard(string: int, note: str) -> int:
    standard = E9_OPEN_STRING_PITCH_VALUES[string]
    delta = (_note_pc(note) - (standard % 12) + 6) % 12 - 6
    return standard + delta


def custom_e9_profile_from_payload(payload: Mapping[str, Any]) -> E9CopedentProfile:
    """Validate the locally saved Backstage E9 profile for deterministic use."""

    family = str(payload.get("tuningFamily") or payload.get("tuning_family") or "").strip().upper()
    if family != "E9":
        raise ValueError("Melody Studio can use a saved profile only when its tuning family is E9.")
    raw_strings = payload.get("strings")
    if not isinstance(raw_strings, list) or len(raw_strings) != 10:
        raise ValueError("Melody Studio currently requires a 10-string saved E9 profile.")
    open_notes: dict[int, str] = {}
    open_pitches: dict[int, int] = {}
    for raw in raw_strings:
        if not isinstance(raw, Mapping):
            raise ValueError("Saved copedent strings must be structured records.")
        string = int(raw.get("stringNumber") or raw.get("string") or 0)
        if string not in range(1, 11) or string in open_notes:
            raise ValueError("Saved E9 strings must be numbered uniquely from 1 through 10.")
        note = str(raw.get("openNote") or raw.get("open_note") or "").strip()
        _note_pc(note)
        open_notes[string] = note
        open_pitches[string] = _open_pitch_near_standard(string, note)
    if set(open_notes) != set(range(1, 11)):
        raise ValueError("Saved E9 strings must include every string from 1 through 10.")

    raw_controls = payload.get("controls") or []
    if not isinstance(raw_controls, list):
        raise ValueError("Saved copedent controls must be a list.")
    if len(raw_controls) > 16:
        raise ValueError("Saved E9 profiles support at most 16 controls in Melody Studio.")
    controls: list[E9CopedentControl] = []
    used_ids: set[str] = set()
    for index, raw_control in enumerate(raw_controls):
        if not isinstance(raw_control, Mapping):
            raise ValueError("Saved copedent controls must be structured records.")
        label = str(raw_control.get("label") or f"Control {index + 1}").strip()[:48]
        control_id = str(raw_control.get("id") or label).strip()[:64]
        if not control_id or control_id in used_ids:
            raise ValueError("Saved copedent control IDs must be non-empty and unique.")
        used_ids.add(control_id)
        raw_type = str(raw_control.get("type") or "lever").lower()
        control_type = "pedal" if raw_type == "pedal" else "lever"
        raw_changes = raw_control.get("changes") or []
        if not isinstance(raw_changes, list) or not raw_changes:
            continue
        if len(raw_changes) > 10:
            raise ValueError(f"Saved control {label} has too many string changes.")
        changes: list[E9CopedentChange] = []
        for raw_change in raw_changes:
            if not isinstance(raw_change, Mapping):
                raise ValueError("Saved copedent changes must be structured records.")
            string = int(raw_change.get("stringNumber") or raw_change.get("string") or 0)
            if string not in open_notes:
                raise ValueError(f"Saved control {label} refers to an unavailable string.")
            from_note = str(raw_change.get("fromNote") or open_notes[string]).strip()
            to_note = str(raw_change.get("toNote") or "").strip()
            _note_pc(from_note)
            _note_pc(to_note)
            changes.append(
                E9CopedentChange(
                    string,
                    from_note,
                    to_note,
                    notes=str(raw_change.get("notes") or "")[:120],
                )
            )
        controls.append(
            E9CopedentControl(
                id=control_id,
                label=label,
                control_type=control_type,
                physical_position=label,
                changes=tuple(changes),
                mechanical_name="; ".join(
                    f"string {change.string} {change.from_note}-to-{change.to_note}" for change in changes
                ),
                compatibility_aliases=(label,),
            )
        )
    profile_id = str(payload.get("id") or "saved-user-e9").strip()[:80] or "saved-user-e9"
    label = str(payload.get("name") or payload.get("label") or "My saved E9").strip()[:80]
    return E9CopedentProfile(
        id=f"saved:{profile_id}",
        label=label,
        status="enabled",
        pedal_order=tuple(arranger_code(control) for control in controls if control.control_type == "pedal"),
        controls=tuple(controls),
        notes="Validated from the user's locally saved Backstage E9 profile.",
        open_notes=tuple(sorted(open_notes.items())),
        open_pitch_values=tuple(sorted(open_pitches.items())),
    )


def resolve_target_profile(
    target_copedent_id: str | None = None,
    target_copedent: Mapping[str, Any] | None = None,
) -> E9CopedentProfile:
    if target_copedent:
        return custom_e9_profile_from_payload(target_copedent)
    return get_e9_copedent_profile(target_copedent_id or DEFAULT_COPEDENT_ID)
