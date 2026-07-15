"""Copedent-neutral mechanics and source-to-target action transfer.

The arranger learns and ranks musical intent separately from the physical
labels on any one guitar.  This module is the deterministic boundary: it
resolves a profile's actual string changes, validates custom E9 profiles, and
maps source actions only when their effects are safe on every sounding or
sustained string.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import combinations
import re
from typing import Any, Mapping, Sequence

from pocketsteel.e9_copedents import (
    CANONICAL_NOTES,
    CUSTOM_LKV_COPEDENT_ID,
    DEFAULT_COPEDENT_ID,
    E9_OPEN_STRING_PITCH_VALUES,
    E9CopedentChange,
    E9CopedentControl,
    E9CopedentProfile,
    NOTE_TO_SEMITONE,
    get_e9_copedent_profile,
)
from pocketsteel.tab_engine import CopedentProfile, PedalLeverEffect, TabEvent, TabNote, render_tab


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


def resolve_arranger_control(profile: E9CopedentProfile, value: object) -> E9CopedentControl:
    """Resolve an internal arranger code without consulting player aliases first.

    Compact codes and player-facing labels occupy separate namespaces.  A
    player may legitimately label a half stop ``G`` and its full stop ``GG``
    while the canonical full-stop mechanic also renders with arranger code
    ``G``.  Internal render data must select the exact mechanic represented by
    that code instead of treating the code as an ambiguous user alias.
    """

    requested = _normalized_alias(value)
    matches = [
        control
        for control in profile.controls
        if _normalized_alias(arranger_code(control)) == requested
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Arranger control code {value!r} is ambiguous on {profile.label}.")
    return resolve_control(profile, value)


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


def control_tab_label(profile: E9CopedentProfile, value: object) -> str:
    """Return the player's concise label for generated tablature.

    Older saved copies of the included E9 profiles may retain descriptive
    control names such as ``A pedal`` while also retaining the player's tab
    shorthand ``A``.  Those descriptions are useful in prose, but generated
    tab must use the compact symbol.  All other custom labels remain exact.
    """

    control = resolve_control(profile, value)
    label = str(control.label or control.id).strip()
    code = arranger_code(control)
    if (
        control.control_type == "pedal"
        and _normalized_alias(label) == _normalized_alias(f"{code} pedal")
    ):
        shorthand = next(
            (
                str(value).strip()
                for value in control.player_shorthand
                if _normalized_alias(value) == _normalized_alias(code)
            ),
            "",
        )
        return shorthand or code
    return label


def candidate_control_states(profile: E9CopedentProfile) -> tuple[tuple[str, ...], ...]:
    """Enumerate compact, non-inert control postures for arrangement search.

    The current Melody Studio vocabulary uses open, one-control, and common
    two-control postures.  Controls that move the same string are not combined
    because their chart deltas cannot safely be assumed additive.
    """

    controls = tuple(profile.ordered_controls())
    states: list[tuple[str, ...]] = [()]
    # Keep stable control-state IDs throughout deterministic mechanics. Compact
    # tab codes are a rendering concern and may collide with a player's label
    # (for example, an RKL half-stop labeled G beside a full state labeled GG
    # whose canonical arranger code is also G).
    states.extend((control.id,) for control in controls)
    for left, right in combinations(controls, 2):
        if left.physical_position and left.physical_position == right.physical_position:
            continue
        if set(left.affected_strings).intersection(right.affected_strings):
            continue
        states.append((left.id, right.id))
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


def _same_sounding_pitches(
    source_profile: E9CopedentProfile,
    source_controls: Sequence[object],
    target_profile: E9CopedentProfile,
    target_controls: Sequence[object],
    *,
    strings: Sequence[int],
    fret: int,
) -> bool:
    return all(
        absolute_pitch_for_profile(source_profile, string, fret, source_controls)
        == absolute_pitch_for_profile(target_profile, string, fret, target_controls)
        for string in strings
    )


def retarget_fretboard_payload(
    payload: Mapping[str, Any] | None,
    target_profile: E9CopedentProfile,
    *,
    source_profile: E9CopedentProfile | None = None,
) -> dict[str, Any] | None:
    """Revalidate a deterministic fretboard payload against the active profile."""

    if not isinstance(payload, Mapping):
        return None
    source = source_profile or get_e9_copedent_profile(CUSTOM_LKV_COPEDENT_ID)
    result = deepcopy(dict(payload))
    positions: list[dict[str, Any]] = []
    by_position_id: dict[str, dict[str, Any]] = {}
    for raw_position in result.get("positions") or []:
        if not isinstance(raw_position, Mapping):
            continue
        position = deepcopy(dict(raw_position))
        strings = tuple(int(value) for value in position.get("strings") or [])
        fret = int(position.get("fret") or 0)
        source_controls = tuple([*(position.get("pedals") or []), *(position.get("levers") or [])])
        try:
            transfer = transfer_controls(source, source_controls, target_profile, sounding_strings=strings)
        except ValueError:
            continue
        if not transfer.exact or not _same_sounding_pitches(
            source,
            source_controls,
            target_profile,
            transfer.target_controls,
            strings=strings,
            fret=fret,
        ):
            continue
        controls = [resolve_control(target_profile, control_value) for control_value in transfer.target_controls]
        position["pedals"] = [
            control_display_label(target_profile, control.id)
            for control in controls
            if control.control_type == "pedal"
        ]
        position["levers"] = [
            control_display_label(target_profile, control.id)
            for control in controls
            if control.control_type == "lever"
        ]
        position["controlIds"] = [control.id for control in controls]
        position["controlStates"] = [
            {
                "id": control.id,
                "label": control.label,
                "physicalPosition": control.physical_position,
                "travel": control.travel,
            }
            for control in controls
        ]
        position["targetCopedentId"] = target_profile.id
        position["validationStatus"] = "target_copedent_pitch_validated"
        if transfer.extra_effect_strings:
            position["caveats"] = [*(position.get("caveats") or []), transfer.reason]
        positions.append(position)
        by_position_id[str(position.get("id") or "")] = position
    if not positions:
        return None
    result["positions"] = positions
    if isinstance(result.get("highlights"), list):
        highlights: list[dict[str, Any]] = []
        for raw_highlight in result["highlights"]:
            if not isinstance(raw_highlight, Mapping):
                continue
            position = by_position_id.get(str(raw_highlight.get("id") or ""))
            if position is None:
                continue
            highlight = deepcopy(dict(raw_highlight))
            highlight["pedals"] = list(position.get("pedals") or [])
            highlight["levers"] = list(position.get("levers") or [])
            highlight["controlIds"] = list(position.get("controlIds") or [])
            highlights.append(highlight)
        result["highlights"] = highlights
    result["strings"] = {
        "count": 10,
        "labels": {str(string): note for string, note in target_profile.open_notes_by_string().items()},
    }
    result["copedent"] = {
        "id": target_profile.id,
        "label": target_profile.label,
        "status": target_profile.validation_status,
    }
    result["targetCopedentId"] = target_profile.id
    result["targetCopedentRevision"] = target_profile.revision
    result["targetCopedentLabel"] = target_profile.label
    result["arrangedFor"] = target_profile.label
    return result


def retarget_tab_example_payload(
    payload: Mapping[str, Any] | None,
    target_profile: E9CopedentProfile,
    *,
    source_profile: E9CopedentProfile | None = None,
) -> dict[str, Any] | None:
    """Transfer structured tab events by effect and render with target labels."""

    if not isinstance(payload, Mapping):
        return None
    source = source_profile or get_e9_copedent_profile(CUSTOM_LKV_COPEDENT_ID)
    result = deepcopy(dict(payload))
    render_events: list[TabEvent] = []
    transferred_events: list[dict[str, Any]] = []
    for raw_event in result.get("events") or []:
        if not isinstance(raw_event, Mapping):
            return None
        event = deepcopy(dict(raw_event))
        raw_notes = event.get("notes") or []
        strings = tuple(int(note.get("string") or 0) for note in raw_notes if isinstance(note, Mapping))
        if not strings:
            return None
        source_controls = tuple(
            dict.fromkeys(
                change
                for note in raw_notes
                if isinstance(note, Mapping)
                for change in (note.get("changes") or [])
            )
        )
        try:
            transfer = transfer_controls(source, source_controls, target_profile, sounding_strings=strings)
        except ValueError:
            return None
        fret_values = {int(note.get("fret") or 0) for note in raw_notes if isinstance(note, Mapping)}
        if not transfer.exact or len(fret_values) != 1 or not _same_sounding_pitches(
            source,
            source_controls,
            target_profile,
            transfer.target_controls,
            strings=strings,
            fret=next(iter(fret_values)),
        ):
            return None
        controls = [resolve_control(target_profile, control_value) for control_value in transfer.target_controls]
        notes: list[dict[str, Any]] = []
        render_notes: list[TabNote] = []
        for raw_note in raw_notes:
            note = deepcopy(dict(raw_note))
            string = int(note.get("string") or 0)
            active_controls = [control for control in controls if control_affects_string(target_profile, control.id, string)]
            codes = tuple(arranger_code(control) for control in active_controls)
            labels = tuple(control_display_label(target_profile, control.id) for control in active_controls)
            note["changes"] = list(codes)
            note["changeLabels"] = list(labels)
            note["mechanicalAction"] = normalized_mechanical_action(
                target_profile,
                string=string,
                fret=int(note.get("fret") or 0),
                controls=[control.id for control in active_controls],
            )
            notes.append(note)
            render_notes.append(
                TabNote(
                    string=string,
                    fret=int(note.get("fret") or 0),
                    changes=codes,
                    articulation=note.get("articulation"),
                    display_changes=labels,
                )
            )
        event["notes"] = notes
        event["controlStates"] = [
            {
                "id": control.id,
                "label": control.label,
                "physicalPosition": control.physical_position,
                "travel": control.travel,
            }
            for control in controls
        ]
        event["targetCopedentId"] = target_profile.id
        transferred_events.append(event)
        render_events.append(
            TabEvent(
                notes=tuple(render_notes),
                chord=event.get("chord"),
                lyric=event.get("lyric"),
                comment=event.get("comment"),
                transition=event.get("transition"),
            )
        )
    rendered = render_tab(render_events, profile=tab_profile_for_e9(target_profile))
    if not rendered.ok:
        return None
    result["events"] = transferred_events
    result["rendered_tab"] = rendered.tab
    result["validation"] = {
        "ok": True,
        "issues": [],
        "profile": target_profile.id,
        "eventCount": len(transferred_events),
    }
    context = dict(result.get("context") or {})
    context.update({"profile": target_profile.id, "profileLabel": target_profile.label})
    result["context"] = context
    result["targetCopedentId"] = target_profile.id
    result["targetCopedentRevision"] = target_profile.revision
    result["targetCopedentLabel"] = target_profile.label
    result["arrangedFor"] = target_profile.label
    return result


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

    family = str(
        payload.get("tuningFamily")
        or payload.get("tuning_family")
        or payload.get("instrument")
        or payload.get("tuning")
        or ""
    ).strip().upper()
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
        raw_pitch = raw.get("openPitchValue")
        if raw_pitch is None:
            raw_pitch = raw.get("open_pitch_value")
        if raw_pitch is None:
            open_pitches[string] = _open_pitch_near_standard(string, note)
        else:
            pitch_value = int(raw_pitch)
            if not 24 <= pitch_value <= 96 or pitch_value % 12 != _note_pc(note):
                raise ValueError(f"Saved E9 string {string} has an inconsistent pitch register.")
            open_pitches[string] = pitch_value
    if set(open_notes) != set(range(1, 11)):
        raise ValueError("Saved E9 strings must include every string from 1 through 10.")

    raw_controls = payload.get("controls") or []
    if not isinstance(raw_controls, list):
        raise ValueError("Saved copedent controls must be a list.")
    if len(raw_controls) > 24:
        raise ValueError("Saved E9 profiles support at most 24 pedal or lever states.")
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
        raw_type = str(
            raw_control.get("type")
            or raw_control.get("controlType")
            or raw_control.get("control_type")
            or "lever"
        ).lower()
        control_type = "pedal" if raw_type == "pedal" else "lever"
        physical_position = str(
            raw_control.get("physicalPosition")
            or raw_control.get("physical_position")
            or label
        ).strip()[:48]
        travel = str(raw_control.get("travel") or ("pedal" if control_type == "pedal" else "full")).strip()[:48]
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
            if _note_pc(from_note) != _note_pc(open_notes[string]):
                raise ValueError(f"Saved control {label} starts string {string} from the wrong open pitch.")
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
                physical_position=physical_position,
                changes=tuple(changes),
                mechanical_name="; ".join(
                    f"string {change.string} {change.from_note}-to-{change.to_note}" for change in changes
                ),
                player_shorthand=tuple(
                    str(value).strip()[:48]
                    for value in (raw_control.get("aliases") or raw_control.get("playerShorthand") or [])
                    if str(value).strip()
                ),
                compatibility_aliases=tuple(
                    dict.fromkeys(
                        value
                        for value in (
                            label,
                            physical_position,
                            *(
                                str(alias).strip()[:48]
                                for alias in (raw_control.get("compatibilityAliases") or [])
                                if str(alias).strip()
                            ),
                        )
                        if value
                    )
                ),
                travel=travel,
                notes=str(raw_control.get("notes") or "")[:240],
            )
        )
    profile_id = str(payload.get("id") or "saved-user-e9").strip()[:80] or "saved-user-e9"
    label = str(payload.get("name") or payload.get("label") or "My saved E9").strip()[:80]
    requested_pedal_order = payload.get("pedalOrder") or payload.get("pedal_order") or []
    pedal_ids = [control.id for control in controls if control.control_type == "pedal"]
    pedal_order = tuple(
        [str(value) for value in requested_pedal_order if str(value) in pedal_ids]
        + [control_id for control_id in pedal_ids if control_id not in requested_pedal_order]
    )
    revision = max(1, int(payload.get("revision") or 1))
    runtime_id = profile_id if profile_id.startswith("saved:") else f"saved:{profile_id}"
    return E9CopedentProfile(
        id=runtime_id,
        label=label,
        status="enabled",
        pedal_order=pedal_order,
        controls=tuple(controls),
        notes="Validated from the user's locally saved Backstage E9 profile.",
        open_notes=tuple(sorted(open_notes.items())),
        open_pitch_values=tuple(sorted(open_pitches.items())),
        revision=revision,
        origin="custom",
        validation_status="valid",
    )


def resolve_copedent_context(context: Mapping[str, Any] | None) -> tuple[E9CopedentProfile, int]:
    """Resolve a built-in ID or validate a local custom profile snapshot."""

    if not context:
        profile = get_e9_copedent_profile(DEFAULT_COPEDENT_ID)
        return profile, profile.revision
    snapshot = context.get("profileSnapshot") or context.get("profile_snapshot")
    profile_id = str(context.get("profileId") or context.get("profile_id") or DEFAULT_COPEDENT_ID).strip()
    if snapshot is not None:
        if not isinstance(snapshot, Mapping):
            raise ValueError("copedentContext.profileSnapshot must be an object")
        profile = custom_e9_profile_from_payload(snapshot)
        expected = profile_id.removeprefix("saved:")
        actual = profile.id.removeprefix("saved:")
        if expected and expected != actual:
            raise ValueError("copedentContext profile ID does not match its custom snapshot")
    else:
        profile = get_e9_copedent_profile(profile_id)
        if profile.origin == "source":
            raise ValueError("Source-only copedents cannot be selected as a target profile")
    revision = max(1, int(context.get("profileRevision") or context.get("profile_revision") or profile.revision))
    return profile, revision


def copedent_context_metadata(profile: E9CopedentProfile, revision: int | None = None) -> dict[str, object]:
    return {
        "targetCopedentId": profile.id,
        "targetCopedentRevision": int(revision or profile.revision),
        "targetCopedentLabel": profile.label,
    }


def profile_control_answer(question: str, profile: E9CopedentProfile) -> str | None:
    """Answer direct questions about a control from the selected profile only."""

    lowered = str(question or "").lower()
    if not re.search(r"\b(?:my|active|this)\b", lowered):
        return None
    requested_match = re.search(r"\b(?:lkl|lkr|lkv|rkl|rkr|rkll|rkrr|p[1-9])\b", lowered)
    pedal_match = re.search(r"\b([abc])(?:\s+pedal)\b|\bpedal\s+([abc])\b", lowered)
    requested = (
        requested_match.group(0).upper()
        if requested_match
        else next((value.upper() for value in (pedal_match.groups() if pedal_match else ()) if value), "")
    )
    if not requested and "copedent" not in lowered and "setup" not in lowered:
        return None
    if requested:
        matching = [
            control
            for control in profile.controls
            if requested in {
                control.id.upper(),
                control.label.upper(),
                control.physical_position.upper(),
                *(alias.upper() for alias in control.player_shorthand),
                *(alias.upper() for alias in control.compatibility_aliases),
            }
            or (requested == "RKLL" and control.physical_position.upper() == "RKL" and "full" in control.travel.lower())
            or (requested == "RKRR" and control.physical_position.upper() == "RKR" and "full" in control.travel.lower())
        ]
        if not matching:
            return (
                f"Using {profile.label}, no {requested} state is recorded. "
                "Open Backstage to add it or confirm that your guitar does not have that movement."
            )
        lines = [f"Using {profile.label}, {requested} is recorded as:"]
        for control in matching:
            change_text = "; ".join(
                f"string {change.string} {change.from_note} to {change.to_note} ({change.direction} {abs(change.semitones)} semitone{'s' if abs(change.semitones) != 1 else ''})"
                for change in control.changes
            )
            state_label = f"{control.label} — {control.physical_position}, {control.travel or 'full'} travel"
            lines.append(f"- {state_label}: {change_text}.")
        lines.append("These mechanics come from the active profile, not from the lever name alone.")
        return "\n".join(lines)
    return (
        f"The active setup is {profile.label}. It has {len(profile.controls)} recorded pedal/lever states. "
        "Ask about a physical control such as RKL or open Backstage to review the complete chart."
    )


def resolve_target_profile(
    target_copedent_id: str | None = None,
    target_copedent: Mapping[str, Any] | None = None,
) -> E9CopedentProfile:
    if target_copedent:
        return custom_e9_profile_from_payload(target_copedent)
    return get_e9_copedent_profile(target_copedent_id or DEFAULT_COPEDENT_ID)
