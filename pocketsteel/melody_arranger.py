"""Octave-aware deterministic melody and harmony routes for standard E9."""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, Sequence

from pocketsteel.answer_tab_examples import fretboard_payload_for_tab_example
from pocketsteel.e9_copedents import scientific_pitch_for_value
from pocketsteel.fretboard_examples import (
    absolute_pitch_for_string,
    control_affects_selected_strings,
    major_positions,
    note_name_for_pitch,
)
from pocketsteel.fretboard_explorer import ExplorerRow, major_three_string_rows, major_two_string_rows
from pocketsteel.melody_models import (
    DEFAULT_ANCHOR_PITCH,
    SUPPORTED_CONTOURS,
    SUPPORTED_TEXTURES,
    MelodyInput,
    PositionCandidate,
)
from pocketsteel.tab_engine import TabEvent, TabNote, default_e9_copedent_profile, render_tab


_CONTROL_STATES: tuple[tuple[str, ...], ...] = (
    (),
    ("A",),
    ("B",),
    ("C",),
    ("E",),
    ("F",),
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
    meter: str = "4/4",
    pickup_beats: float = 0.0,
    sections: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return render-ready routes and resolved phrase metadata."""

    contour = contour_mode if contour_mode in SUPPORTED_CONTOURS else "closest_playable"
    selected_texture = texture if texture in SUPPORTED_TEXTURES else "both"
    all_inputs = parse_melody_inputs(raw_events, key)
    all_resolved_pitches = resolve_contour(all_inputs, contour)
    inputs = all_inputs[event_start:event_end]
    resolved_pitches = all_resolved_pitches[event_start:event_end]
    phrase_starts, phrase_ends = _phrase_boundaries(inputs, sections)
    single_candidates = [single_note_candidates(item, pitch) for item, pitch in zip(inputs, resolved_pitches)]
    single_path = choose_path(single_candidates, inputs=inputs)
    if not single_path:
        raise ValueError("The melody does not have a mechanically valid standard-E9 path.")

    route_specs: list[tuple[str, str, str]] = [("single-note", "single_note", "Faithful melody")]
    if selected_texture in {"both", "mixed_arrangement"}:
        route_specs.append(("mixed-arrangement", "mixed_arrangement", "Recommended arrangement"))
    if selected_texture == "automatic_harmony":
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
            meter=meter,
            pickup_beats=pickup_beats,
            phrase_starts=phrase_starts,
            phrase_ends=phrase_ends,
        )
    )

    for suffix, harmony_type, label in route_specs[1:]:
        if harmony_type == "chord_melody" and not any(_active_chords(inputs)):
            continue
        if harmony_type == "mixed_arrangement":
            candidate_groups = mixed_candidate_groups(inputs, resolved_pitches, key)
            path = choose_mixed_path(
                candidate_groups,
                inputs=inputs,
                key=key,
                meter=meter,
                pickup_beats=pickup_beats,
                phrase_starts=phrase_starts,
                phrase_ends=phrase_ends,
            )
        else:
            candidate_groups = harmony_candidate_groups(inputs, resolved_pitches, key, harmony_type)
            path = choose_path(candidate_groups, inputs=inputs) if candidate_groups and all(candidate_groups) else []
        if not path:
            continue
        if harmony_type == "mixed_arrangement" and all(len(candidate.notes) == 1 for candidate in path):
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
                recommended=harmony_type in {"mixed_arrangement", "automatic_harmony"},
                meter=meter,
                pickup_beats=pickup_beats,
                phrase_starts=phrase_starts,
                phrase_ends=phrase_ends,
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
    active_chords = _active_chords(inputs)
    groups: list[list[PositionCandidate]] = []
    for item, target_pitch, active_chord in zip(inputs, resolved_pitches, active_chords):
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
        if active_chord and candidates:
            best_fit = min(_chord_fit_penalty(candidate, active_chord) for candidate in candidates)
            candidates = [candidate for candidate in candidates if _chord_fit_penalty(candidate, active_chord) == best_fit]
        groups.append(candidates)
    return groups


def mixed_candidate_groups(
    inputs: Sequence[MelodyInput],
    resolved_pitches: Sequence[int],
    key: str,
) -> list[list[PositionCandidate]]:
    """Combine scale rows with common chord grips and their playable subsets."""

    dyads = harmony_candidate_groups(inputs, resolved_pitches, key, "automatic_harmony")
    triads = harmony_candidate_groups(inputs, resolved_pitches, key, "chord_melody")
    active_chords = _active_chords(inputs)
    groups: list[list[PositionCandidate]] = []
    for index, (item, pitch) in enumerate(zip(inputs, resolved_pitches)):
        singles = single_note_candidates(item, pitch)
        if item.literal is not None:
            groups.append(singles)
            continue
        active_chord = active_chords[index]
        scale_dyads = [
            candidate for candidate in dyads[index]
            if not active_chord or _supporting_harmony_fits(candidate, active_chord)
        ]
        scale_triads = [
            candidate for candidate in triads[index]
            if active_chord
            and _melody_is_chord_tone(pitch, active_chord)
            and _supporting_harmony_fits(candidate, active_chord)
        ]
        chord_grips = _active_chord_candidates(item, pitch, active_chord)
        candidates = [*singles, *scale_dyads]
        for grip in (*scale_triads, *chord_grips):
            candidates.extend(_candidate_subsets(grip))
        groups.append(_dedupe_candidates(candidates))
    return groups


def choose_mixed_path(
    candidate_groups: Sequence[Sequence[PositionCandidate]],
    *,
    inputs: Sequence[MelodyInput],
    key: str = "G",
    meter: str = "4/4",
    pickup_beats: float = 0.0,
    phrase_starts: set[int] | None = None,
    phrase_ends: set[int] | None = None,
) -> list[PositionCandidate]:
    if not candidate_groups or any(not group for group in candidate_groups):
        return []
    active_chords = _active_chords(inputs)
    roles = _arrangement_roles(
        inputs,
        active_chords,
        meter=meter,
        pickup_beats=pickup_beats,
        phrase_starts=phrase_starts or {0},
        phrase_ends=phrase_ends or {len(inputs) - 1},
    )
    home_fret = 3 if key == "G" else 8
    states: list[dict[int, tuple[tuple[int, ...], int | None]]] = []
    first: dict[int, tuple[tuple[int, ...], int | None]] = {}
    for candidate_index, candidate in enumerate(candidate_groups[0]):
        first[candidate_index] = (
            _mixed_start_cost(candidate, inputs, 0, active_chords, roles, home_fret=home_fret),
            None,
        )
    states.append(first)
    for event_index in range(1, len(candidate_groups)):
        current: dict[int, tuple[tuple[int, ...], int | None]] = {}
        for current_index, candidate in enumerate(candidate_groups[event_index]):
            choices: list[tuple[tuple[int, ...], int]] = []
            for previous_index, (previous_cost, _parent) in states[-1].items():
                previous = candidate_groups[event_index - 1][previous_index]
                transition = _mixed_transition_cost(
                    previous,
                    candidate,
                    inputs,
                    event_index,
                    active_chords,
                    roles,
                    phrase_starts=phrase_starts or {0},
                    home_fret=home_fret,
                    key=key,
                )
                choices.append((_add_cost(previous_cost, transition), previous_index))
            current[current_index] = min(choices, key=lambda item: (item[0], item[1]))
        states.append(current)
    last_index = min(states[-1], key=lambda index: (states[-1][index][0], index))
    path: list[PositionCandidate] = []
    for event_index in range(len(states) - 1, -1, -1):
        path.append(candidate_groups[event_index][last_index])
        parent = states[event_index][last_index][1]
        if parent is not None:
            last_index = parent
    return list(reversed(path))


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


def build_expressive_transitions(
    *,
    route_id: str,
    inputs: Sequence[MelodyInput],
    path: Sequence[PositionCandidate],
) -> list[dict[str, Any]]:
    """Choose a sparse, mechanically checked set of audible steel transitions."""

    eligible: list[tuple[tuple[int, ...], int, dict[str, Any]]] = []
    active_chords = _active_chords(inputs)
    for target_index in range(1, len(path)):
        if inputs[target_index - 1].literal is not None or inputs[target_index].literal is not None:
            continue
        transition = _transition_between(route_id, target_index, path[target_index - 1], path[target_index])
        if transition is None:
            continue
        chord_change = bool(active_chords[target_index] and active_chords[target_index] != active_chords[target_index - 1])
        is_full_grip = transition["scope"] == "full_grip" and len(transition["sustainedStrings"]) >= 2
        if not is_full_grip:
            # Blocking a grip down to one moving voice is a useful exception, not
            # the default sound. Never generate the confusing one-note-into-grip
            # move that prompted this user-smoke correction.
            if min(len(path[target_index - 1].notes), len(path[target_index].notes)) < 2:
                continue
            if not chord_change and not (
                inputs[target_index].duration_beats >= 2 and float(inputs[target_index].beat) == 1
            ):
                continue
        priority = (
            0 if is_full_grip else 1,
            0 if chord_change else 1,
            0 if inputs[target_index].duration_beats >= 2 else 1,
            0 if float(inputs[target_index].beat) == 1 else 1,
            abs(path[target_index].fret - path[target_index - 1].fret),
            target_index,
        )
        eligible.append((priority, target_index, transition))
    selected: list[tuple[int, dict[str, Any]]] = []
    melody_only_count = 0
    cap = max(1, math.ceil(len(path) / 8))
    for _priority, target_index, transition in sorted(eligible, key=lambda item: item[0]):
        if any(abs(target_index - existing_index) <= 1 for existing_index, _item in selected):
            continue
        if transition["scope"] != "full_grip":
            if melody_only_count >= 1:
                continue
            melody_only_count += 1
        selected.append((target_index, transition))
        if len(selected) >= cap:
            break
    return [transition for _index, transition in sorted(selected, key=lambda item: item[0])]


def _transition_between(
    route_id: str,
    target_index: int,
    previous: PositionCandidate,
    current: PositionCandidate,
) -> dict[str, Any] | None:
    previous_top = _note_for_string(previous, previous.top_string)
    current_top = _note_for_string(current, current.top_string)
    if previous.top_string != current.top_string or previous_top is None or current_top is None:
        return None
    previous_strings = {note.string for note in previous.notes}
    current_strings = {note.string for note in current.notes}
    same_grip = (
        previous_strings == current_strings
        and len(previous.notes) == len(current.notes)
        and 2 <= len(current.notes) <= 3
        and (not previous.canonical_grip or not current.canonical_grip or previous.canonical_grip == current.canonical_grip)
    )
    scope = "full_grip" if same_grip else "melody_voice"
    kind = ""
    control = ""
    fret_distance = abs(current.fret - previous.fret)
    controls_compatible_with_slide = previous.controls == current.controls or _is_open_ab_exchange(
        previous.controls,
        current.controls,
    )
    max_slide_distance = 7 if scope == "full_grip" else 4
    if (
        1 <= fret_distance <= max_slide_distance
        and controls_compatible_with_slide
        and (scope == "full_grip" or previous.controls == current.controls)
    ):
        kind = "bar_slide"
        strings = sorted(previous_strings & current_strings) if scope == "full_grip" else [current.top_string]
    elif previous.fret == current.fret:
        changed = sorted(set(previous.controls) ^ set(current.controls))
        if len(changed) != 1:
            return None
        control = changed[0]
        if not control_affects_selected_strings(control, (current.top_string,)):
            return None
        if _absolute_pitch(current.top_string, previous.fret, previous.controls) != previous.top_pitch:
            return None
        if _absolute_pitch(current.top_string, current.fret, current.controls) != current.top_pitch:
            return None
        kind = "pedal_glide" if control in {"A", "B", "C"} else "lever_glide"
        strings = [current.top_string]
        scope = "full_grip" if scope == "full_grip" and all(
            _note_for_string(previous, string) and _note_for_string(current, string)
            for string in previous_strings
        ) else "melody_voice"
    else:
        return None
    sustained = sorted(previous_strings & current_strings) if scope == "full_grip" else [current.top_string]
    released = sorted(previous_strings - set(sustained))
    repicked = sorted(current_strings - set(sustained))
    voice_actions: list[dict[str, Any]] = []
    for string in sustained:
        if kind == "bar_slide":
            action = "bar_slide"
        elif control_affects_selected_strings(control, (string,)):
            action = kind
        else:
            action = "hold"
        voice_actions.append({"string": string, "action": action})
    for string in released:
        voice_actions.append({"string": string, "action": "release"})
    for string in repicked:
        voice_actions.append(
            {"string": string, "action": "add" if string not in previous_strings else "repick"}
        )
    label = _transition_instruction(
        previous,
        current,
        kind=kind,
        scope=scope,
        sustained=sustained,
        repicked=repicked,
        released=released,
    )
    return {
        "id": f"{route_id}-transition-{target_index}-{target_index + 1}",
        "kind": kind,
        "scope": scope,
        "fromEventId": f"{route_id}-step-{target_index}",
        "toEventId": f"{route_id}-step-{target_index + 1}",
        "strings": strings,
        "fromFret": previous.fret,
        "toFret": current.fret,
        "controlsBefore": list(previous.controls),
        "controlsAfter": list(current.controls),
        "direction": "up" if current.top_pitch > previous.top_pitch else "down",
        "playbackGlideFraction": 0.35,
        "label": label,
        "fromStrings": sorted(previous_strings),
        "toStrings": sorted(current_strings),
        "sustainedStrings": sustained,
        "repickedStrings": repicked,
        "releasedStrings": released,
        "voiceActions": voice_actions,
        "controlChanges": {
            "pressed": sorted(set(current.controls) - set(previous.controls)),
            "released": sorted(set(previous.controls) - set(current.controls)),
        },
    }


def _transition_instruction(
    previous: PositionCandidate,
    current: PositionCandidate,
    *,
    kind: str,
    scope: str,
    sustained: Sequence[int],
    repicked: Sequence[int],
    released: Sequence[int],
) -> str:
    before = _pick_instruction(previous)
    if kind == "bar_slide":
        moving = "strings " + ", ".join(str(string) for string in sustained)
        movement = f"slide {moving} to fret {current.fret}"
        control_action = _control_change_text(previous.controls, current.controls)
        if control_action:
            movement += f" while {control_action}"
    else:
        moving = "strings " + ", ".join(str(string) for string in sustained)
        control_action = _control_change_text(previous.controls, current.controls)
        movement = f"hold fret {current.fret} and {control_action} on {moving}"
    additions: list[str] = []
    if released:
        noun = "string" if len(released) == 1 else "strings"
        timing = "before the slide" if kind == "bar_slide" else "before the control change"
        additions.append(f"block {noun} " + ", ".join(str(string) for string in released) + f" {timing}")
    if repicked:
        previous_strings = {note.string for note in previous.notes}
        repicked_strings = sorted(set(repicked) & previous_strings)
        added_strings = sorted(set(repicked) - previous_strings)
        if repicked_strings:
            noun = "string" if len(repicked_strings) == 1 else "strings"
            additions.append(
                f"repick {noun} " + ", ".join(str(string) for string in repicked_strings) + " at the arrival"
            )
        if added_strings:
            noun = "string" if len(added_strings) == 1 else "strings"
            additions.append(
                f"add {noun} " + ", ".join(str(string) for string in added_strings) + " at the arrival"
            )
    suffix = ("; " + "; ".join(additions)) if additions else ""
    return f"{before}; {movement}{suffix}."


def _is_open_ab_exchange(previous_controls: Sequence[str], current_controls: Sequence[str]) -> bool:
    postures = {frozenset(previous_controls), frozenset(current_controls)}
    return postures == {frozenset(), frozenset({"A", "B"})}


def _control_change_text(previous_controls: Sequence[str], current_controls: Sequence[str]) -> str:
    previous = set(previous_controls)
    current = set(current_controls)
    parts: list[str] = []
    released = sorted(previous - current)
    pressed = sorted(current - previous)
    if released:
        parts.append("releasing " + "+".join(released))
    if pressed:
        parts.append("pressing " + "+".join(pressed))
    return " and ".join(parts)


def _pick_instruction(candidate: PositionCandidate) -> str:
    strings = ", ".join(str(note.string) for note in candidate.notes)
    controls = "+".join(candidate.controls) if candidate.controls else "open"
    return f"Pick strings {strings} at fret {candidate.fret} with {controls}"


def _note_for_string(candidate: PositionCandidate, string: int) -> TabNote | None:
    return next((note for note in candidate.notes if note.string == string), None)


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
    meter: str = "4/4",
    pickup_beats: float = 0.0,
    phrase_starts: set[int] | None = None,
    phrase_ends: set[int] | None = None,
) -> dict[str, Any]:
    profile = default_e9_copedent_profile()
    active_chords = _active_chords(inputs)
    roles = _arrangement_roles(
        inputs,
        active_chords,
        meter=meter,
        pickup_beats=pickup_beats,
        phrase_starts=phrase_starts or {0},
        phrase_ends=phrase_ends or ({len(inputs) - 1} if inputs else set()),
    )
    transitions = build_expressive_transitions(route_id=route_id, inputs=inputs, path=path) if harmony_type == "mixed_arrangement" else []
    transitions_by_target = {transition["toEventId"]: transition for transition in transitions}
    raw_events: list[TabEvent] = []
    intervals: list[dict[str, Any]] = []
    movements: list[str] = []
    previous_chord = ""
    for index, (item, candidate) in enumerate(zip(inputs, path), start=1):
        chord_change = item.chord if item.chord and item.chord != previous_chord else None
        event_id = f"{route_id}-step-{index}"
        transition = transitions_by_target.get(event_id)
        raw_events.append(
            TabEvent(
                notes=candidate.notes,
                chord=chord_change,
                comment=f"{scientific_pitch_for_value(resolved_pitches[index - 1])}; {label}",
                transition=transition,
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
    for index, (event, item, candidate, movement, role) in enumerate(
        zip(raw_events, inputs, path, movements, roles),
        start=1,
    ):
        payload = event.normalized(profile).to_dict()
        event_id = f"{route_id}-step-{index}"
        transition = transitions_by_target.get(event_id)
        payload.update(
            {
                "id": event_id,
                "step": index,
                "inputToken": item.token,
                "resolvedNote": item.note,
                "resolvedPitch": scientific_pitch_for_value(resolved_pitches[index - 1]),
                "pitchValue": resolved_pitches[index - 1],
                "scaleDegree": str(item.degree),
                "technique": "grip" if len(candidate.notes) > 1 else "pick",
                "texture": {1: "single_note", 2: "dyad", 3: "triad"}.get(len(candidate.notes), "grip"),
                "movement": transition["label"] if transition else movement,
                "explanation": _event_explanation(item, candidate, transition["label"] if transition else movement, resolved_pitches[index - 1]),
                "renderablePositionId": f"{route_id}-event-{index}",
                "durationBeats": item.duration_beats,
                "measure": item.measure,
                "beat": item.beat,
                "origin": item.origin,
                "arrangementRole": role,
                "performanceControls": list(candidate.controls),
                "patternFamily": candidate.pattern_family,
                "canonicalGrip": "-".join(
                    str(string) for string in (candidate.canonical_grip or tuple(note.string for note in candidate.notes))
                ),
                "selectionReason": _selection_reason(
                    item,
                    candidate,
                    role=role,
                    active_chord=active_chords[index - 1],
                ),
            }
        )
        if transition:
            payload["transitionFromPreviousId"] = transition["id"]
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
        "context": {
            "key": key,
            "tuning": "E9",
            "profile": profile.id,
            "harmonyType": harmony_type,
            "meter": meter,
            "pickupBeats": pickup_beats,
        },
        "rendered_tab": rendered.tab,
        "print_tab_text": _render_print_tab(raw_events, inputs),
        "validation": {"ok": True, "issues": [], "profile": profile.id, "eventCount": len(event_payloads)},
        "explanation": "Tab and fretboard share the same validated arranger events.",
        "intervals": intervals,
        "events": event_payloads,
    }
    fretboard = fretboard_payload_for_tab_example(tab_example)
    if fretboard is None:
        raise ValueError("A generated melody route could not produce a synchronized fretboard.")
    chord_symbols = list(dict.fromkeys(item.chord for item in inputs if item.chord))
    texture_summary = {
        "singleNotes": sum(1 for candidate in path if len(candidate.notes) == 1),
        "dyads": sum(1 for candidate in path if len(candidate.notes) == 2),
        "triads": sum(1 for candidate in path if len(candidate.notes) == 3),
        "barSlides": sum(1 for transition in transitions if transition["kind"] == "bar_slide"),
        "pedalGlides": sum(1 for transition in transitions if transition["kind"] == "pedal_glide"),
        "leverGlides": sum(1 for transition in transitions if transition["kind"] == "lever_glide"),
    }
    path_summary = _path_summary(path)
    return {
        "id": route_id,
        "label": label,
        "harmonyType": harmony_type,
        "recommended": recommended,
        "recommendation": recommendation + (f" Chord-aware ranking used: {', '.join(chord_symbols)}." if chord_symbols else ""),
        "chordContext": {"symbols": chord_symbols, "usedForRanking": bool(chord_symbols)},
        "movementSummary": " ".join(str(event.get("movement") or "") for event in event_payloads).strip(),
        "textureSummary": texture_summary,
        "pathSummary": path_summary,
        "transitions": transitions,
        "events": event_payloads,
        "tabExample": tab_example,
        "fretboard": fretboard,
    }


def _render_print_tab(
    events: Sequence[TabEvent],
    inputs: Sequence[MelodyInput],
    *,
    maximum_width: int = 112,
) -> str:
    """Wrap printable tab without splitting a source-transition-destination pair."""

    if not events:
        return ""
    semantic_keys = {
        "fromStrings",
        "toStrings",
        "sustainedStrings",
        "repickedStrings",
        "releasedStrings",
        "voiceActions",
    }
    units: list[tuple[list[TabEvent], list[MelodyInput]]] = []
    index = 0
    while index < len(events):
        if index + 1 < len(events):
            transition = events[index + 1].transition or {}
            if semantic_keys.intersection(transition):
                units.append(([events[index], events[index + 1]], [inputs[index], inputs[index + 1]]))
                index += 2
                continue
        units.append(([events[index]], [inputs[index]]))
        index += 1

    systems: list[tuple[list[TabEvent], list[MelodyInput]]] = []
    current_events: list[TabEvent] = []
    current_inputs: list[MelodyInput] = []
    for unit_events, unit_inputs in units:
        proposed_events = [*current_events, *unit_events]
        proposed = render_tab(tuple(proposed_events))
        proposed_width = max((len(line) for line in proposed.tab.splitlines()), default=0)
        if current_events and proposed_width > maximum_width:
            systems.append((current_events, current_inputs))
            current_events = list(unit_events)
            current_inputs = list(unit_inputs)
        else:
            current_events = proposed_events
            current_inputs.extend(unit_inputs)
    if current_events:
        systems.append((current_events, current_inputs))

    rendered_systems: list[str] = []
    for system_events, system_inputs in systems:
        measure_start = min(item.measure for item in system_inputs)
        measure_end = max(item.measure for item in system_inputs)
        heading = f"Measure {measure_start}" if measure_start == measure_end else f"Measures {measure_start}-{measure_end}"
        rendered_systems.append(f"{heading}\n{render_tab(tuple(system_events)).tab}")
    return "\n\n".join(rendered_systems)


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
        pattern_family=_pattern_family_for_grip(row.strings),
        canonical_grip=tuple(row.strings),
        difficulty=str(row.difficulty_tier or "common"),
    )


def _active_chord_candidates(item: MelodyInput, target_pitch: int, chord: str) -> list[PositionCandidate]:
    """Return common, pitch-validated major-position grips for the active chord."""

    root = _major_position_root(chord)
    if not root or not _melody_is_chord_tone(target_pitch, chord):
        return []
    candidates: list[PositionCandidate] = []
    for position in major_positions(root).positions:
        if not position.is_full_chord or str(position.tier) == "advanced":
            continue
        candidate = _candidate_for_fretboard_position(position)
        if candidate.top_pitch != target_pitch:
            continue
        if not _supporting_harmony_fits(candidate, chord):
            continue
        candidates.append(candidate)
    return _dedupe_candidates(candidates)


def _candidate_for_fretboard_position(position: Any) -> PositionCandidate:
    profile = default_e9_copedent_profile()
    controls = tuple(
        profile.normalize_change(control)
        for control in (*tuple(position.pedals), *tuple(position.levers))
        if profile.normalize_change(control)
    )
    notes: list[TabNote] = []
    note_names: list[str] = []
    intervals: list[str] = []
    for string in position.strings:
        relevant = tuple(control for control in controls if control_affects_selected_strings(control, (string,)))
        notes.append(TabNote(string=string, fret=position.fret, changes=relevant))
        note_names.append(str(position.notes.get(str(string), position.notes.get(string))))
        intervals.append(str(position.intervals.get(str(string), position.intervals.get(string))))
    pitches = [_absolute_pitch(note.string, position.fret, controls) for note in notes]
    return PositionCandidate(
        fret=position.fret,
        notes=tuple(notes),
        top_pitch=max(pitches),
        controls=controls,
        family=str(position.family),
        note_names=tuple(note_names),
        intervals=tuple(intervals),
        pattern_family=_pattern_family_for_grip(tuple(position.strings)),
        canonical_grip=tuple(position.strings),
        difficulty=str(position.tier or "common"),
    )


def _candidate_subsets(candidate: PositionCandidate) -> list[PositionCandidate]:
    """Keep a full grip's pocket identity on its melody, dyad, and triad forms."""

    top_string = candidate.top_string
    top_index = next(index for index, note in enumerate(candidate.notes) if note.string == top_string)
    support_indices = [index for index in range(len(candidate.notes)) if index != top_index]
    selections: list[tuple[int, ...]] = [(top_index,)]
    selections.extend(tuple(sorted((top_index, support_index))) for support_index in support_indices)
    selections.append(tuple(range(len(candidate.notes))))
    subsets: list[PositionCandidate] = []
    for selected in selections:
        subsets.append(
            PositionCandidate(
                fret=candidate.fret,
                notes=tuple(candidate.notes[index] for index in selected),
                top_pitch=candidate.top_pitch,
                controls=candidate.controls,
                family=candidate.family,
                note_names=tuple(candidate.note_names[index] for index in selected),
                intervals=tuple(candidate.intervals[index] for index in selected),
                pattern_family=candidate.pattern_family,
                canonical_grip=candidate.canonical_grip or tuple(note.string for note in candidate.notes),
                difficulty=candidate.difficulty,
            )
        )
    return subsets


def _pattern_family_for_grip(strings: Sequence[int]) -> str:
    """Name the transferable string lane independently from its pedal posture."""

    grip = tuple(int(string) for string in strings)
    canonical = {
        (5, 6, 7): (5, 6, 8),
        (6, 7, 10): (6, 8, 10),
    }.get(grip, grip)
    return f"{'-'.join(str(string) for string in canonical)} harmonic path"


def _major_position_root(chord: str) -> str:
    match = re.match(r"^\s*([A-Ga-g])([#b]?)([^/]*)", str(chord or ""))
    if not match:
        return ""
    quality = match.group(3).lower()
    if (quality.startswith("m") and not quality.startswith("maj")) or any(
        marker in quality for marker in ("dim", "°", "aug", "+", "sus")
    ):
        return ""
    return f"{match.group(1).upper()}{match.group(2)}"


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


def _active_chords(inputs: Sequence[MelodyInput]) -> list[str]:
    active = ""
    result: list[str] = []
    for item in inputs:
        if item.chord:
            active = item.chord
        result.append(active)
    return result


def _phrase_boundaries(
    inputs: Sequence[MelodyInput],
    sections: Sequence[Mapping[str, Any]] | None,
) -> tuple[set[int], set[int]]:
    if not inputs:
        return set(), set()
    starts = {0}
    ends = {len(inputs) - 1}
    for section in sections or ():
        try:
            start_measure = int(section.get("startMeasure"))
            end_measure = int(section.get("endMeasure"))
        except (TypeError, ValueError):
            continue
        start_index = next((index for index, item in enumerate(inputs) if item.measure >= start_measure), None)
        end_index = next(
            (index for index in range(len(inputs) - 1, -1, -1) if inputs[index].measure <= end_measure),
            None,
        )
        if start_index is not None:
            starts.add(start_index)
        if end_index is not None:
            ends.add(end_index)
    return starts, ends


def _arrangement_roles(
    inputs: Sequence[MelodyInput],
    active_chords: Sequence[str],
    *,
    meter: str,
    pickup_beats: float,
    phrase_starts: set[int],
    phrase_ends: set[int],
) -> list[str]:
    roles: list[str] = []
    beats_per_measure = 3 if str(meter).startswith("3/") else 4
    for index, item in enumerate(inputs):
        chord = active_chords[index]
        previous_chord = active_chords[index - 1] if index else ""
        chord_tones = _chord_pitch_classes(chord)
        melody_is_chord_tone = not chord_tones or item.pitch_class in chord_tones
        previous_was_tension = bool(roles and roles[-1] == "tension")
        first_pickup = index in phrase_starts and (
            (index == 0 and pickup_beats > 0)
            or (float(item.beat) > beats_per_measure - max(0.0, pickup_beats) and pickup_beats > 0)
        )
        if first_pickup:
            role = "pickup"
        elif previous_was_tension and melody_is_chord_tone:
            role = "resolution"
        elif chord and not melody_is_chord_tone:
            role = "tension"
        elif chord and (index == 0 or chord != previous_chord):
            role = "chord_arrival"
        elif index in phrase_ends:
            role = "cadence"
        elif item.duration_beats >= 1.5 or float(item.beat) == 1:
            role = "sustained_note"
        else:
            role = "passing_tone"
        roles.append(role)
    return roles


def _desired_texture_size(
    inputs: Sequence[MelodyInput],
    index: int,
    active_chords: Sequence[str],
    roles: Sequence[str] | None = None,
) -> int:
    role = roles[index] if roles else ""
    if role in {"pickup", "passing_tone", "tension"}:
        return 1
    if role in {"resolution", "chord_arrival", "cadence"} and active_chords[index]:
        return 3
    if role == "sustained_note":
        return 2
    item = inputs[index]
    if item.duration_beats <= 0.5 and float(item.beat) != 1:
        return 1
    return 2


def _texture_penalty(actual: int, desired: int) -> int:
    penalties = {
        1: {1: 0, 2: 3, 3: 8},
        2: {1: 2, 2: 0, 3: 4},
        3: {1: 5, 2: 2, 3: 0},
    }
    return penalties[desired].get(actual, 9)


def _mixed_start_cost(
    candidate: PositionCandidate,
    inputs: Sequence[MelodyInput],
    index: int,
    active_chords: Sequence[str],
    roles: Sequence[str],
    *,
    home_fret: int,
) -> tuple[int, ...]:
    desired = _desired_texture_size(inputs, index, active_chords, roles)
    return (
        _harmonic_correctness_penalty(candidate, active_chords[index]),
        _control_posture_tier(candidate, active_chords[index]),
        0,
        _harmonic_role_penalty(candidate, roles[index], active_chords[index]),
        _arrival_home_penalty(candidate, roles[index], home_fret),
        _home_pocket_penalty(candidate.fret, home_fret),
        0,
        0,
        0,
        len(candidate.controls),
        abs(candidate.fret - home_fret),
        0,
        _texture_penalty(len(candidate.notes), desired),
        _difficulty_penalty(candidate),
        abs(candidate.top_string - 5) + len(candidate.notes),
    )


def _mixed_transition_cost(
    previous: PositionCandidate,
    current: PositionCandidate,
    inputs: Sequence[MelodyInput],
    index: int,
    active_chords: Sequence[str],
    roles: Sequence[str],
    *,
    phrase_starts: set[int],
    home_fret: int,
    key: str,
) -> tuple[int, ...]:
    desired = _desired_texture_size(inputs, index, active_chords, roles)
    texture_change = abs(len(current.notes) - len(previous.notes))
    phrase_reset = index in phrase_starts
    return (
        _harmonic_correctness_penalty(current, active_chords[index]),
        _control_posture_transition_tier(previous, current, active_chords[index]),
        _slide_affinity_penalty(previous, current, roles[index], active_chords[index], key),
        _harmonic_role_penalty(current, roles[index], active_chords[index]),
        _arrival_home_penalty(current, roles[index], home_fret),
        _home_pocket_penalty(current.fret, home_fret) if phrase_reset else _pocket_change_penalty(previous, current),
        0 if phrase_reset else _family_change_penalty(previous, current),
        _voice_leading_cost(previous, current),
        _string_group_change_penalty(previous, current),
        _control_posture_penalty(previous, current),
        abs(current.fret - previous.fret),
        texture_change * 2,
        _texture_penalty(len(current.notes), desired),
        _difficulty_penalty(current),
        len(current.controls),
    )


def _melody_is_chord_tone(pitch: int, chord: str) -> bool:
    tones = _chord_pitch_classes(chord)
    return not tones or pitch % 12 in tones


def _supporting_harmony_fits(candidate: PositionCandidate, chord: str) -> bool:
    tones = _chord_pitch_classes(chord)
    if not tones or len(candidate.notes) == 1:
        return True
    top_string = candidate.top_string
    return all(
        _pitch_class(note_name) in tones
        for note, note_name in zip(candidate.notes, candidate.note_names)
        if note.string != top_string
    )


def _harmonic_correctness_penalty(candidate: PositionCandidate, chord: str) -> int:
    return 100 if chord and not _supporting_harmony_fits(candidate, chord) else 0


def _harmonic_role_penalty(candidate: PositionCandidate, role: str, chord: str) -> int:
    size = len(candidate.notes)
    if role == "tension":
        return {1: 0, 2: 0, 3: 8}.get(size, 10)
    if role in {"resolution", "chord_arrival"} and chord:
        return {1: 2, 2: 1, 3: 0}.get(size, 4)
    if role == "cadence":
        return {1: 1, 2: 0, 3: 0 if chord else 5}.get(size, 4)
    if role == "sustained_note":
        return {1: 1, 2: 0, 3: 0}.get(size, 3)
    return {1: 0, 2: 1, 3: 4}.get(size, 6)


def _control_posture_tier(candidate: PositionCandidate, chord: str) -> int:
    """Prefer the everyday open/A/B language; keep C as a real exception."""

    controls = set(candidate.controls)
    if not controls or controls <= {"A", "B"}:
        return 0
    if controls == {"B", "C"} and len(candidate.notes) == 3 and _is_minor_chord(chord):
        return 0
    if "C" in controls:
        return 2
    return 1


def _control_posture_transition_tier(
    previous: PositionCandidate,
    current: PositionCandidate,
    chord: str,
) -> int:
    """Do not force a player out of a validated lever pocket between notes.

    Starting a phrase still favors the familiar open/A/B vocabulary. Once the
    path is already using an F-lever or E-lower posture, however, retaining that
    posture is a normal pocket decision rather than a new complexity penalty.
    C-pedal restrictions remain unchanged.
    """

    tier = _control_posture_tier(current, chord)
    if tier != 1:
        return tier
    if current.controls == previous.controls:
        return 0
    return tier


def _is_minor_chord(chord: str) -> bool:
    match = re.match(r"^\s*[A-Ga-g][#b]?([^/]*)", str(chord or ""))
    quality = match.group(1).strip().lower() if match else ""
    return quality.startswith("m") and not quality.startswith("maj")


def _arrival_home_penalty(candidate: PositionCandidate, role: str, home_fret: int) -> int:
    return _home_pocket_penalty(candidate.fret, home_fret) if role in {"chord_arrival", "cadence"} else 0


def _slide_affinity_penalty(
    previous: PositionCandidate,
    current: PositionCandidate,
    role: str,
    chord: str,
    key: str,
) -> int:
    """Make familiar full-grip arrivals influence the route before ornaments are added."""

    if role not in {"resolution", "chord_arrival", "cadence"}:
        return 0
    if _major_position_root(chord).upper() != key.upper():
        return 0
    return 0 if _is_familiar_full_grip_slide(previous, current) else 1


def _is_familiar_full_grip_slide(previous: PositionCandidate, current: PositionCandidate) -> bool:
    previous_strings = {note.string for note in previous.notes}
    current_strings = {note.string for note in current.notes}
    if previous_strings != current_strings or not 2 <= len(current_strings) <= 3:
        return False
    if previous.canonical_grip and current.canonical_grip and previous.canonical_grip != current.canonical_grip:
        return False
    if not 1 <= abs(current.fret - previous.fret) <= 7:
        return False
    return previous.controls == current.controls or _is_open_ab_exchange(previous.controls, current.controls)


def _candidate_voice_pitches(candidate: PositionCandidate) -> tuple[int, ...]:
    return tuple(sorted(_absolute_pitch(note.string, candidate.fret, candidate.controls) for note in candidate.notes))


def _voice_leading_cost(previous: PositionCandidate, current: PositionCandidate) -> int:
    previous_pitches = _candidate_voice_pitches(previous)
    current_pitches = _candidate_voice_pitches(current)
    if not previous_pitches or not current_pitches:
        return 0
    return sum(min(abs(pitch - previous_pitch) for previous_pitch in previous_pitches) for pitch in current_pitches)


def _pocket_change_penalty(previous: PositionCandidate, current: PositionCandidate) -> int:
    fret_distance = abs(current.fret - previous.fret)
    if fret_distance == 0:
        return 0
    if fret_distance <= 2:
        return 1
    if fret_distance <= 4:
        return 2
    return 3


def _home_pocket_penalty(fret: int, home_fret: int) -> int:
    distance = abs(fret - home_fret)
    if distance == 0:
        return 0
    if distance <= 2:
        return 1
    if distance <= 4:
        return 2
    return 3


def _family_change_penalty(previous: PositionCandidate, current: PositionCandidate) -> int:
    if not previous.pattern_family or not current.pattern_family:
        return 0
    if previous.pattern_family == current.pattern_family:
        return 0
    return 1


def _string_group_change_penalty(previous: PositionCandidate, current: PositionCandidate) -> int:
    previous_grip = set(previous.canonical_grip or tuple(note.string for note in previous.notes))
    current_grip = set(current.canonical_grip or tuple(note.string for note in current.notes))
    return len(previous_grip ^ current_grip)


def _control_posture_penalty(previous: PositionCandidate, current: PositionCandidate) -> int:
    previous_controls = set(previous.controls)
    current_controls = set(current.controls)
    penalty = len(previous_controls ^ current_controls)
    if {"A", "B"} <= previous_controls and {"B", "C"} <= current_controls:
        penalty += 4
    if {"B", "C"} <= previous_controls and {"A", "B"} <= current_controls:
        penalty += 4
    return penalty


def _difficulty_penalty(candidate: PositionCandidate) -> int:
    return {
        "beginner": 0,
        "starter": 0,
        "common": 1,
        "alternate": 2,
        "advanced": 3,
    }.get(candidate.difficulty, 2)


def _dedupe_candidates(candidates: Sequence[PositionCandidate]) -> list[PositionCandidate]:
    unique: dict[tuple[Any, ...], PositionCandidate] = {}
    for candidate in candidates:
        key = (
            candidate.fret,
            tuple((note.string, note.fret, note.changes) for note in candidate.notes),
            candidate.top_pitch,
        )
        unique.setdefault(key, candidate)
    return list(unique.values())


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
    previous_controls = set(previous.controls)
    current_controls = set(current.controls)
    released = sorted(previous_controls - current_controls)
    pressed = sorted(current_controls - previous_controls)
    control_actions: list[str] = []
    if released:
        control_actions.append(f"release {'+'.join(released)}")
    if pressed:
        control_actions.append(f"press {'+'.join(pressed)}")
    control_text = f"; {'; '.join(control_actions)}" if control_actions else "; keep the controls steady"
    return f"{bar}{control_text}."


def _selection_reason(
    item: MelodyInput,
    candidate: PositionCandidate,
    *,
    role: str,
    active_chord: str,
) -> str:
    controls = "+".join(candidate.controls) if candidate.controls else "open"
    grip = "-".join(str(string) for string in (candidate.canonical_grip or tuple(note.string for note in candidate.notes)))
    root = _major_position_root(active_chord)
    if root and not candidate.controls and item.pitch_class == _pitch_class(root):
        four = note_name_for_pitch((_pitch_class(root) + 5) % 12)
        return (
            f"Keeps {active_chord} in the open-position pocket at fret {candidate.fret}. "
            f"A+B at this fret would produce {four} harmony, not {root}."
        )
    if role == "tension":
        return (
            f"Treats {item.note} as a melodic tension over {active_chord}; supporting voices stay inside the chord "
            "instead of forcing a temporary triad."
        )
    if role == "resolution" and active_chord:
        return f"Resolves the tension into {active_chord} on grip {grip} at fret {candidate.fret} with {controls}."
    if role == "chord_arrival" and active_chord:
        return f"Marks the {active_chord} arrival on grip {grip} at fret {candidate.fret} with {controls}."
    if role == "cadence" and active_chord:
        return f"Uses a stable {active_chord} cadence voicing on grip {grip} with {controls}."
    if role == "pickup":
        return f"Keeps the pickup light on string {candidate.top_string} before the phrase settles into a harmony pocket."
    if role == "passing_tone":
        return "Keeps this passing note light while preserving the surrounding fretboard pocket."
    return f"Sustains the melody in the current pocket on grip {grip} with {controls}."


def _path_summary(path: Sequence[PositionCandidate]) -> dict[str, int]:
    fret_moves = [abs(current.fret - previous.fret) for previous, current in zip(path, path[1:])]
    meaningful_families = [candidate.pattern_family for candidate in path if candidate.pattern_family]
    family_changes = sum(previous != current for previous, current in zip(meaningful_families, meaningful_families[1:]))
    meaningful_grips = [candidate.canonical_grip for candidate in path if candidate.canonical_grip]
    string_changes = sum(previous != current for previous, current in zip(meaningful_grips, meaningful_grips[1:]))
    pedal_changes = sum(
        1 for previous, current in zip(path, path[1:]) if previous.controls != current.controls
    )
    return {
        "totalBarTravel": sum(fret_moves),
        "maxBarTravel": max(fret_moves, default=0),
        "harmonicFamilyChanges": family_changes,
        "stringGroupChanges": string_changes,
        "pedalFamilyChanges": pedal_changes,
    }


def _event_explanation(item: MelodyInput, candidate: PositionCandidate, movement: str, pitch: int) -> str:
    grip = "-".join(str(note.string) for note in candidate.notes)
    controls = "+".join(candidate.controls) if candidate.controls else "no pedals or levers"
    return (
        f"{item.note} ({scientific_pitch_for_value(pitch)}), scale degree {item.degree}: "
        f"fret {candidate.fret}, strings {grip}, {controls}. {movement}"
    )


def _recommendation_for(harmony_type: str) -> str:
    return {
        "mixed_arrangement": "Recommended: balances single-note motion, diatonic pairs, chord-backed grips, and sparse validated steel movement.",
        "automatic_harmony": "Recommended: mixes validated diatonic thirds and sixths to keep the bar path smooth.",
        "thirds": "Keeps a diatonic third below the melody where a validated E9 grip exists.",
        "sixths": "Keeps a diatonic sixth below the melody where a validated E9 grip exists.",
        "chord_melody": "Uses validated three-note grips only when the resolved melody pitch remains the top voice.",
    }[harmony_type]
