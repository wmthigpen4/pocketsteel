"""Octave-aware deterministic melody and harmony routes for standard E9."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pocketsteel.answer_tab_examples import fretboard_payload_for_tab_example
from pocketsteel.e9_copedents import scientific_pitch_for_value
from pocketsteel.fretboard_examples import (
    absolute_pitch_for_string,
    control_affects_selected_strings,
    note_name_for_pitch,
)
from pocketsteel.fretboard_explorer import ExplorerRow, major_three_string_rows, major_two_string_rows
from pocketsteel.tab_engine import TabEvent, TabNote, default_e9_copedent_profile, render_tab


SUPPORTED_CONTOURS = {"closest_playable", "ascending", "descending", "preserve_input"}
SUPPORTED_TEXTURES = {"both", "single_note", "automatic_harmony", "thirds", "sixths", "chord_melody"}
DEFAULT_ANCHOR_PITCH = 67  # G4: a useful middle/upper E9 melody register.

_CONTROL_STATES: tuple[tuple[str, ...], ...] = (
    (),
    ("A",),
    ("B",),
    ("C",),
    ("E-lower",),
    ("F lever",),
)


@dataclass(frozen=True)
class MelodyInput:
    token: str
    note: str
    degree: int
    pitch_class: int
    direction: str = "auto"
    octave_shift: int = 0
    literal: TabNote | None = None
    forced_pitch: int | None = None
    duration_beats: float = 1.0
    measure: int = 1
    beat: float = 1.0
    origin: str = "user_edit"
    tie: str = ""
    lyric: str = ""
    chord: str = ""
    articulation: str = ""


@dataclass(frozen=True)
class PositionCandidate:
    fret: int
    notes: tuple[TabNote, ...]
    top_pitch: int
    controls: tuple[str, ...]
    family: str
    note_names: tuple[str, ...]
    intervals: tuple[str, ...]

    @property
    def top_string(self) -> int:
        return max(
            (note.string for note in self.notes),
            key=lambda string: _absolute_pitch(string, self.fret, self.controls),
        )


def arrange_melody_routes(
    raw_events: Sequence[Any],
    *,
    key: str,
    contour_mode: str = "closest_playable",
    texture: str = "both",
    route_id_prefix: str,
    title: str,
    event_start: int = 0,
    event_end: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return render-ready routes and resolved phrase metadata."""

    contour = contour_mode if contour_mode in SUPPORTED_CONTOURS else "closest_playable"
    selected_texture = texture if texture in SUPPORTED_TEXTURES else "both"
    all_inputs = parse_melody_inputs(raw_events, key)
    all_resolved_pitches = resolve_contour(all_inputs, contour)
    inputs = all_inputs[event_start:event_end]
    resolved_pitches = all_resolved_pitches[event_start:event_end]
    single_candidates = [single_note_candidates(item, pitch) for item, pitch in zip(inputs, resolved_pitches)]
    single_path = choose_path(single_candidates, inputs=inputs)
    if not single_path:
        raise ValueError("The melody does not have a mechanically valid standard-E9 path.")

    route_specs: list[tuple[str, str, str]] = [("single-note", "single_note", "Faithful melody")]
    if selected_texture in {"both", "automatic_harmony"}:
        route_specs.append(("recommended-harmony", "automatic_harmony", "Recommended harmony"))
    if selected_texture in {"both", "thirds"}:
        route_specs.append(("thirds", "thirds", "Diatonic thirds"))
    if selected_texture in {"both", "sixths"}:
        route_specs.append(("sixths", "sixths", "Diatonic sixths"))
    if selected_texture in {"both", "chord_melody"}:
        route_specs.append(("chord-melody", "chord_melody", "Chord melody"))

    routes: list[dict[str, Any]] = []
    routes.append(
        build_route(
            route_id=f"{route_id_prefix}-single-note",
            label=route_specs[0][2],
            harmony_type="single_note",
            recommendation="Start here to hear and learn the melody contour cleanly.",
            inputs=inputs,
            resolved_pitches=resolved_pitches,
            path=single_path,
            key=key,
            title=f"{title} — Single-note melody",
            recommended=False,
        )
    )

    vocal_route = build_vocal_steel_route(routes[0], inputs, key)
    if vocal_route is not None:
        routes.append(vocal_route)

    for suffix, harmony_type, label in route_specs[1:]:
        candidate_groups = harmony_candidate_groups(inputs, resolved_pitches, key, harmony_type)
        path = choose_path(candidate_groups, inputs=inputs) if candidate_groups and all(candidate_groups) else []
        if not path:
            continue
        routes.append(
            build_route(
                route_id=f"{route_id_prefix}-{suffix}",
                label=label,
                harmony_type=harmony_type,
                recommendation=_recommendation_for(harmony_type),
                inputs=inputs,
                resolved_pitches=resolved_pitches,
                path=path,
                key=key,
                title=f"{title} — {label}",
                recommended=harmony_type == "automatic_harmony",
            )
        )

    if len(routes) > 1 and not any(route["recommended"] for route in routes):
        fallback = next((route for route in routes if route["harmonyType"] not in {"single_note", "vocal_steel"}), None)
        if fallback is not None:
            fallback["recommended"] = True
            fallback["recommendation"] = "Recommended validated harmony route for this phrase."

    resolved = [
        {
            "inputToken": item.token,
            "resolvedNote": item.note,
            "scaleDegree": str(item.degree),
            "pitch": scientific_pitch_for_value(pitch),
            "pitchValue": pitch,
            "direction": item.direction,
            "octaveShift": item.octave_shift,
            "literal": item.literal is not None,
            "durationBeats": item.duration_beats,
            "measure": item.measure,
            "beat": item.beat,
            "origin": item.origin,
            "tie": item.tie,
            "lyric": item.lyric,
            "chord": item.chord,
            "articulation": item.articulation,
        }
        for item, pitch in zip(inputs, resolved_pitches)
    ]
    return routes, resolved


def parse_melody_inputs(raw_events: Sequence[Any], key: str) -> list[MelodyInput]:
    scale = _scale_notes(key)
    parsed: list[MelodyInput] = []
    for raw_index, raw in enumerate(raw_events):
        record = raw if isinstance(raw, Mapping) else {}
        literal_payload = record.get("position") if isinstance(record.get("position"), Mapping) else record
        literal = _literal_note(literal_payload) if isinstance(raw, Mapping) else None
        token = str(record.get("token") or record.get("note") or record.get("degree") or raw or "").strip()
        forced_pitch = _forced_pitch(record)
        if literal is not None:
            controls = tuple(literal.changes)
            pitch = _absolute_pitch(literal.string, literal.fret, controls)
            note = note_name_for_pitch(pitch)
            degree = _degree_for_note(note, scale)
            token = token if token and token != str(raw) else f"S{literal.string}:{literal.fret}"
        elif forced_pitch is not None:
            note = note_name_for_pitch(forced_pitch)
            degree = _degree_for_note(note, scale, allow_chromatic=True)
            token = token or scientific_pitch_for_value(forced_pitch)
            pitch = forced_pitch
        else:
            note, degree = _resolve_token(token, scale)
            pitch = _pitch_class(note)
        direction = str(record.get("direction") or "auto").strip().lower()
        if direction not in {"auto", "up", "down", "same"}:
            direction = "auto"
        try:
            octave_shift = max(-2, min(2, int(record.get("octaveShift", record.get("octave_shift", 0)) or 0)))
        except (TypeError, ValueError):
            octave_shift = 0
        parsed.append(
            MelodyInput(
                token=token,
                note=note,
                degree=degree,
                pitch_class=pitch % 12,
                direction=direction,
                octave_shift=octave_shift,
                literal=literal,
                forced_pitch=forced_pitch,
                duration_beats=_positive_float(record.get("durationBeats") or record.get("duration"), 1.0),
                measure=_positive_int(record.get("measure"), raw_index // 4 + 1),
                beat=_positive_float(record.get("beat"), raw_index % 4 + 1.0),
                origin=str(record.get("origin") or "user_edit")[:40],
                tie=str(record.get("tie") or "")[:20],
                lyric=str(record.get("lyric") or record.get("phraseLabel") or "")[:80],
                chord=str(record.get("chord") or "")[:24],
                articulation=str(record.get("articulation") or "")[:20],
            )
        )
    return parsed


def resolve_contour(inputs: Sequence[MelodyInput], contour_mode: str) -> list[int]:
    if not inputs:
        return []
    def solve(forced: Mapping[int, int] | None = None) -> list[int]:
        forced = forced or {}
        option_groups: list[list[int]] = []
        for index, item in enumerate(inputs):
            if index in forced:
                options = [forced[index]]
            elif item.forced_pitch is not None:
                options = [item.forced_pitch]
            elif item.literal is not None:
                options = [_absolute_pitch(item.literal.string, item.literal.fret, tuple(item.literal.changes))]
            else:
                options = _pitch_options(item.pitch_class)
            options = [pitch for pitch in options if 47 <= pitch <= 94]
            if not options:
                raise ValueError(f"{item.token!r} resolves outside the supported E9 register.")
            option_groups.append(sorted(set(options)))

        states: list[dict[int, tuple[tuple[int, int], int | None]]] = []
        first = {pitch: ((0, abs(pitch - DEFAULT_ANCHOR_PITCH)), None) for pitch in option_groups[0]}
        states.append(first)
        for index in range(1, len(inputs)):
            direction = inputs[index].direction
            if direction == "auto":
                direction = {"ascending": "up", "descending": "down"}.get(contour_mode, "nearest")
            current_states: dict[int, tuple[tuple[int, int], int | None]] = {}
            for pitch in option_groups[index]:
                choices: list[tuple[tuple[int, int], int]] = []
                for previous_pitch, (cost, _parent) in states[-1].items():
                    if direction == "up" and pitch < previous_pitch:
                        continue
                    if direction == "down" and pitch > previous_pitch:
                        continue
                    choices.append(((cost[0] + abs(pitch - previous_pitch), cost[1]), previous_pitch))
                if choices:
                    current_states[pitch] = min(choices, key=lambda value: (value[0], value[1]))
            if not current_states:
                raise ValueError(f"The requested {direction} contour exceeds the supported E9 register at {inputs[index].token!r}.")
            states.append(current_states)
        pitch = min(states[-1], key=lambda value: (states[-1][value][0], value))
        path: list[int] = []
        for index in range(len(states) - 1, -1, -1):
            path.append(pitch)
            parent = states[index][pitch][1]
            if parent is not None:
                pitch = parent
        return list(reversed(path))

    baseline = solve()
    adjusted = list(baseline)
    for index, item in enumerate(inputs):
        if not item.octave_shift:
            continue
        if item.literal is not None:
            raise ValueError("Literal tab fixes its octave; edit the entered string or fret instead.")
        adjusted[index] += item.octave_shift * 12
        if adjusted[index] < 47 or adjusted[index] > 94:
            raise ValueError(f"{item.token!r} resolves outside the supported E9 register.")
    return adjusted


def single_note_candidates(item: MelodyInput, target_pitch: int) -> list[PositionCandidate]:
    if item.literal is not None:
        controls = tuple(item.literal.changes)
        if _absolute_pitch(item.literal.string, item.literal.fret, controls) != target_pitch:
            return []
        return [
            PositionCandidate(
                fret=item.literal.fret,
                notes=(item.literal,),
                top_pitch=target_pitch,
                controls=controls,
                family="literal_tab",
                note_names=(item.note,),
                intervals=(str(item.degree),),
            )
        ]
    candidates: list[PositionCandidate] = []
    profile = default_e9_copedent_profile()
    for controls in _CONTROL_STATES:
        for string in range(1, 11):
            if controls and not all(control_affects_selected_strings(control, (string,)) for control in controls):
                continue
            for fret in range(25):
                pitch = _absolute_pitch(string, fret, controls)
                if pitch != target_pitch:
                    continue
                candidates.append(
                    PositionCandidate(
                        fret=fret,
                        notes=(TabNote(string=string, fret=fret, changes=tuple(profile.normalize_change(control) for control in controls)),),
                        top_pitch=pitch,
                        controls=controls,
                        family="single_note",
                        note_names=(item.note,),
                        intervals=(str(item.degree),),
                    )
                )
    return candidates


def harmony_candidate_groups(
    inputs: Sequence[MelodyInput],
    resolved_pitches: Sequence[int],
    key: str,
    harmony_type: str,
) -> list[list[PositionCandidate]]:
    rows = major_three_string_rows(key) if harmony_type == "chord_melody" else major_two_string_rows(key)
    scale = _scale_notes(key)
    groups: list[list[PositionCandidate]] = []
    for item, target_pitch in zip(inputs, resolved_pitches):
        candidates: list[PositionCandidate] = []
        if not 1 <= item.degree <= 7:
            groups.append(candidates)
            continue
        third_note = scale[(item.degree - 3) % 7]
        sixth_note = scale[(item.degree + 1) % 7]
        for row in rows:
            top_register = row.note_registers.get(str(row.top_voice.get("string"))) or {}
            if int(top_register.get("pitch_value", -1)) != target_pitch:
                continue
            other_notes = [note for string, note in row.notes.items() if string != str(row.top_voice.get("string"))]
            if harmony_type == "thirds" and third_note not in other_notes:
                continue
            if harmony_type == "sixths" and sixth_note not in other_notes:
                continue
            if harmony_type == "automatic_harmony" and not ({third_note, sixth_note} & set(other_notes)):
                continue
            candidates.append(_candidate_for_explorer_row(row))
        if item.chord and candidates:
            best_fit = min(_chord_fit_penalty(candidate, item.chord) for candidate in candidates)
            candidates = [candidate for candidate in candidates if _chord_fit_penalty(candidate, item.chord) == best_fit]
        groups.append(candidates)
    return groups


def choose_path(
    candidate_groups: Sequence[Sequence[PositionCandidate]],
    *,
    inputs: Sequence[MelodyInput] | None = None,
) -> list[PositionCandidate]:
    if not candidate_groups or any(not group for group in candidate_groups):
        return []
    states: list[dict[int, tuple[tuple[int, ...], int | None]]] = []
    first: dict[int, tuple[tuple[int, ...], int | None]] = {}
    for index, candidate in enumerate(candidate_groups[0]):
        first[index] = ((_start_cost(candidate, inputs[0] if inputs else None)), None)
    states.append(first)
    for event_index in range(1, len(candidate_groups)):
        current: dict[int, tuple[tuple[int, ...], int | None]] = {}
        for current_index, candidate in enumerate(candidate_groups[event_index]):
            choices: list[tuple[tuple[int, ...], int]] = []
            for previous_index, (previous_cost, _parent) in states[-1].items():
                previous = candidate_groups[event_index - 1][previous_index]
                transition = _transition_cost(previous, candidate, inputs[event_index] if inputs else None)
                choices.append((_add_cost(previous_cost, transition), previous_index))
            current[current_index] = min(choices, key=lambda item: (item[0], item[1]))
        states.append(current)
    last_index = min(states[-1], key=lambda index: (states[-1][index][0], index))
    path: list[PositionCandidate] = []
    for event_index in range(len(candidate_groups) - 1, -1, -1):
        path.append(candidate_groups[event_index][last_index])
        parent = states[event_index][last_index][1]
        if parent is not None:
            last_index = parent
    return list(reversed(path))


def build_route(
    *,
    route_id: str,
    label: str,
    harmony_type: str,
    recommendation: str,
    inputs: Sequence[MelodyInput],
    resolved_pitches: Sequence[int],
    path: Sequence[PositionCandidate],
    key: str,
    title: str,
    recommended: bool,
) -> dict[str, Any]:
    profile = default_e9_copedent_profile()
    raw_events: list[TabEvent] = []
    intervals: list[dict[str, Any]] = []
    movements: list[str] = []
    previous_chord = ""
    for index, (item, candidate) in enumerate(zip(inputs, path), start=1):
        chord_change = item.chord if item.chord and item.chord != previous_chord else None
        raw_events.append(
            TabEvent(
                notes=candidate.notes,
                chord=chord_change,
                comment=f"{scientific_pitch_for_value(resolved_pitches[index - 1])}; {label}",
            )
        )
        if item.chord:
            previous_chord = item.chord
        intervals.append(
            {
                "eventId": f"{route_id}-step-{index}",
                "chord": item.chord or item.note,
                "byString": {
                    str(note.string): interval
                    for note, interval in zip(candidate.notes, candidate.intervals)
                },
            }
        )
        movements.append(_movement_text(path[index - 2] if index > 1 else None, candidate))
    rendered = render_tab(tuple(raw_events))
    if not rendered.ok:
        raise ValueError("A generated melody route failed standard-E9 tab validation.")
    event_payloads: list[dict[str, Any]] = []
    for index, (event, item, candidate, movement) in enumerate(zip(raw_events, inputs, path, movements), start=1):
        payload = event.normalized(profile).to_dict()
        payload.update(
            {
                "id": f"{route_id}-step-{index}",
                "step": index,
                "inputToken": item.token,
                "resolvedNote": item.note,
                "resolvedPitch": scientific_pitch_for_value(resolved_pitches[index - 1]),
                "pitchValue": resolved_pitches[index - 1],
                "scaleDegree": str(item.degree),
                "technique": "grip" if len(candidate.notes) > 1 else "pick",
                "movement": movement,
                "explanation": _event_explanation(item, candidate, movement, resolved_pitches[index - 1]),
                "renderablePositionId": f"{route_id}-event-{index}",
                "durationBeats": item.duration_beats,
                "measure": item.measure,
                "beat": item.beat,
                "origin": item.origin,
            }
        )
        if item.tie:
            payload["tie"] = item.tie
        if item.lyric:
            payload["lyric"] = item.lyric
        if item.chord:
            payload["harmonySymbol"] = item.chord
        if item.articulation:
            payload["articulation"] = item.articulation
        event_payloads.append(payload)
    tab_example = {
        "id": route_id,
        "title": title,
        "kind": "melody_exercise",
        "display_tab": True,
        "preferred_display": "tab_and_fretboard",
        "context": {"key": key, "tuning": "E9", "profile": profile.id, "harmonyType": harmony_type},
        "rendered_tab": rendered.tab,
        "validation": {"ok": True, "issues": [], "profile": profile.id, "eventCount": len(event_payloads)},
        "explanation": "Tab and fretboard share the same validated arranger events.",
        "intervals": intervals,
        "events": event_payloads,
    }
    fretboard = fretboard_payload_for_tab_example(tab_example)
    if fretboard is None:
        raise ValueError("A generated melody route could not produce a synchronized fretboard.")
    chord_symbols = list(dict.fromkeys(item.chord for item in inputs if item.chord))
    return {
        "id": route_id,
        "label": label,
        "harmonyType": harmony_type,
        "recommended": recommended,
        "recommendation": recommendation + (f" Chord-aware ranking used: {', '.join(chord_symbols)}." if chord_symbols else ""),
        "chordContext": {"symbols": chord_symbols, "usedForRanking": bool(chord_symbols)},
        "movementSummary": " ".join(movements),
        "events": event_payloads,
        "tabExample": tab_example,
        "fretboard": fretboard,
    }


def build_vocal_steel_route(base_route: Mapping[str, Any], inputs: Sequence[MelodyInput], key: str) -> dict[str, Any] | None:
    """Return a faithful route with one mechanically checked slide-in suggestion.

    The suggested grace note is metadata rather than a source event, so turning
    this route on never alters or misattributes the imported melody.
    """
    scale_pitch_classes = {_pitch_class(note) for note in _scale_notes(key)}
    events = list(base_route.get("events") or [])
    suggestion: dict[str, Any] | None = None
    for index, event in enumerate(events):
        notes = event.get("notes") or []
        if len(notes) != 1:
            continue
        note = notes[0]
        try:
            string = int(note["string"])
            fret = int(note["fret"])
            changes = tuple(note.get("changes") or ())
        except (KeyError, TypeError, ValueError):
            continue
        if fret < 1 or changes:
            continue
        target_pitch = int(event.get("pitchValue") or 0)
        approach_pitch = _absolute_pitch(string, fret - 1, ())
        if approach_pitch != target_pitch - 1 or approach_pitch % 12 not in scale_pitch_classes:
            continue
        suggestion = {
            "kind": "slide_in",
            "origin": "generated_ornament",
            "targetEventId": event.get("id"),
            "targetStep": index + 1,
            "from": {"string": string, "fret": fret - 1, "changes": [], "pitch": scientific_pitch_for_value(approach_pitch)},
            "to": {"string": string, "fret": fret, "changes": [], "pitch": scientific_pitch_for_value(target_pitch)},
            "label": f"Optional slide into {scientific_pitch_for_value(target_pitch)} on string {string}, fret {fret - 1} to {fret}.",
        }
        break
    if suggestion is None:
        return None
    route = copy.deepcopy(dict(base_route))
    route["id"] = str(base_route.get("id") or "melody").replace("-single-note", "-vocal-steel")
    route["label"] = "Vocal steel"
    route["harmonyType"] = "vocal_steel"
    route["recommended"] = False
    route["generatedOrnaments"] = [suggestion]
    route["recommendation"] = suggestion["label"] + " The source melody remains unchanged."
    return route


def _literal_note(record: Mapping[str, Any]) -> TabNote | None:
    if "string" not in record or "fret" not in record:
        return None
    try:
        string = int(record.get("string"))
        fret = int(record.get("fret"))
    except (TypeError, ValueError):
        raise ValueError("Literal tab events require numeric string and fret values.")
    raw_changes = record.get("changes") or ()
    if isinstance(raw_changes, str):
        raw_changes = [raw_changes]
    profile = default_e9_copedent_profile()
    changes = tuple(profile.normalize_change(change) for change in raw_changes if profile.normalize_change(change))
    note = TabNote(string=string, fret=fret, changes=changes).normalized(profile)
    validation = render_tab((TabEvent(notes=(note,)),))
    if not validation.ok:
        raise ValueError(validation.issues[0].message)
    return note


def _candidate_for_explorer_row(row: ExplorerRow) -> PositionCandidate:
    profile = default_e9_copedent_profile()
    controls = tuple(profile.normalize_change(control) for control in (*row.pedals, *row.levers))
    notes: list[TabNote] = []
    note_names: list[str] = []
    intervals: list[str] = []
    for string in row.strings:
        relevant = tuple(control for control in controls if control_affects_selected_strings(control, (string,)))
        notes.append(TabNote(string=string, fret=row.fret, changes=relevant))
        note_names.append(row.notes[str(string)])
        intervals.append(row.intervals[str(string)])
    top_register = row.note_registers[str(row.top_voice["string"])]
    return PositionCandidate(
        fret=row.fret,
        notes=tuple(notes),
        top_pitch=int(top_register["pitch_value"]),
        controls=controls,
        family=row.position_family,
        note_names=tuple(note_names),
        intervals=tuple(intervals),
    )


def _scale_notes(key: str) -> tuple[str, ...]:
    return ("G", "A", "B", "C", "D", "E", "F#") if key == "G" else ("C", "D", "E", "F", "G", "A", "B")


def _resolve_token(token: str, scale: tuple[str, ...]) -> tuple[str, int]:
    normalized = token.strip().upper().replace("♯", "#").replace("♭", "B")
    if normalized.isdigit() and 1 <= int(normalized) <= 7:
        degree = int(normalized)
        return scale[degree - 1], degree
    display = normalized[0] + normalized[1:].replace("B", "b") if normalized else normalized
    for index, note in enumerate(scale, start=1):
        if display.upper() == note.upper():
            return note, index
    raise ValueError(f"{token!r} is not in the selected major scale.")


def _degree_for_note(note: str, scale: tuple[str, ...], *, allow_chromatic: bool = False) -> int:
    for index, scale_note in enumerate(scale, start=1):
        if _pitch_class(scale_note) == _pitch_class(note):
            return index
    if allow_chromatic:
        return 0
    raise ValueError(f"Literal tab note {note} is outside the selected major scale.")


def _forced_pitch(record: Mapping[str, Any]) -> int | None:
    raw_value = record.get("pitchValue") if "pitchValue" in record else record.get("pitch_value")
    if raw_value is not None and str(raw_value).strip() != "":
        try:
            return int(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Exact melody pitch values must be numeric.") from exc
    raw_pitch = str(record.get("pitch") or "").strip()
    match = re.match(r"^([A-Ga-g])([#b]?)(-?\d+)$", raw_pitch)
    if not match:
        return None
    step, accidental, octave = match.groups()
    pitch_class = _pitch_class(f"{step.upper()}{accidental}")
    return (int(octave) + 1) * 12 + pitch_class


def _positive_float(value: Any, default: float) -> float:
    try:
        return max(0.125, float(value))
    except (TypeError, ValueError):
        return default


def _positive_int(value: Any, default: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def _pitch_class(note: str) -> int:
    names = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11}
    return names[note.upper()]


def _pitch_options(pitch_class: int) -> list[int]:
    return [value for value in range(47, 95) if value % 12 == pitch_class]


def _absolute_pitch(string: int, fret: int, controls: tuple[str, ...]) -> int:
    aliases = {
        "E": "E-lower",
        "F": "F lever",
        "V": "vertical/Bb",
        "G": "RKL",
        "D": "RKRR",
    }
    return absolute_pitch_for_string(string, fret, tuple(aliases.get(control, control) for control in controls))


def _start_cost(candidate: PositionCandidate, item: MelodyInput | None = None) -> tuple[int, ...]:
    return (
        _chord_fit_penalty(candidate, item.chord) if item else 0,
        0,
        0,
        len(candidate.controls),
        abs(candidate.fret - 8) + abs(candidate.top_string - 5),
    )


def _transition_cost(
    previous: PositionCandidate,
    current: PositionCandidate,
    item: MelodyInput | None = None,
) -> tuple[int, ...]:
    control_changes = len(set(previous.controls) ^ set(current.controls))
    return (
        _chord_fit_penalty(current, item.chord) if item else 0,
        abs(current.fret - previous.fret),
        control_changes,
        abs(current.top_string - previous.top_string),
        len(current.controls),
    )


def _chord_fit_penalty(candidate: PositionCandidate, chord: str) -> int:
    tones = _chord_pitch_classes(chord)
    if not tones:
        return 0
    return sum(1 for note in candidate.note_names if _pitch_class(note) not in tones)


def _chord_pitch_classes(chord: str) -> set[int]:
    match = re.match(r"^\s*([A-Ga-g])([#b]?)([^/]*)", str(chord or ""))
    if not match:
        return set()
    root = _pitch_class(f"{match.group(1).upper()}{match.group(2)}")
    quality = match.group(3).lower()
    if "dim" in quality or "°" in quality:
        intervals = {0, 3, 6}
    elif "aug" in quality or "+" in quality:
        intervals = {0, 4, 8}
    elif quality.startswith("m") and not quality.startswith("maj"):
        intervals = {0, 3, 7}
    elif "sus2" in quality:
        intervals = {0, 2, 7}
    elif "sus" in quality:
        intervals = {0, 5, 7}
    else:
        intervals = {0, 4, 7}
    if "maj7" in quality:
        intervals.add(11)
    elif "7" in quality:
        intervals.add(10)
    if "6" in quality:
        intervals.add(9)
    return {(root + interval) % 12 for interval in intervals}


def _add_cost(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    width = max(len(left), len(right))
    return tuple((left[index] if index < len(left) else 0) + (right[index] if index < len(right) else 0) for index in range(width))


def _movement_text(previous: PositionCandidate | None, current: PositionCandidate) -> str:
    controls = "+".join(current.controls) if current.controls else "no pedals/levers"
    if previous is None:
        return f"Start at fret {current.fret} with {controls}."
    delta = current.fret - previous.fret
    bar = "stay at the same fret" if delta == 0 else f"move the bar {'up' if delta > 0 else 'down'} {abs(delta)} fret{'s' if abs(delta) != 1 else ''}"
    changed = sorted(set(previous.controls) ^ set(current.controls))
    control_text = f"; change {'+'.join(changed)}" if changed else "; keep the controls steady"
    return f"{bar}{control_text}."


def _event_explanation(item: MelodyInput, candidate: PositionCandidate, movement: str, pitch: int) -> str:
    grip = "-".join(str(note.string) for note in candidate.notes)
    controls = "+".join(candidate.controls) if candidate.controls else "no pedals or levers"
    return (
        f"{item.note} ({scientific_pitch_for_value(pitch)}), scale degree {item.degree}: "
        f"fret {candidate.fret}, strings {grip}, {controls}. {movement}"
    )


def _recommendation_for(harmony_type: str) -> str:
    return {
        "automatic_harmony": "Recommended: mixes validated diatonic thirds and sixths to keep the bar path smooth.",
        "thirds": "Keeps a diatonic third below the melody where a validated E9 grip exists.",
        "sixths": "Keeps a diatonic sixth below the melody where a validated E9 grip exists.",
        "chord_melody": "Uses validated three-note grips only when the resolved melody pitch remains the top voice.",
    }[harmony_type]
