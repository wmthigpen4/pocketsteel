"""Deterministic E9 progression-route guide.

This module owns a small, validated set of beginner-safe progression routes.
It intentionally does not use retrieval, SGF/forum text, or song-specific
material as source of truth for fret/string/pedal choices.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from .fretboard_examples import (
    E9_OPEN_STRINGS,
    FRETBOARD_PAYLOAD_TYPE,
    FretboardPosition,
    grip_label,
    interval_for_note,
    note_at_fret,
    notes_for_controls,
    validate_fretboard_payload,
)


_EXPECTED_INTERVALS: dict[str, tuple[str, ...]] = {
    "major": ("1", "3", "5"),
    "minor": ("1", "b3", "5"),
    "dominant7": ("1", "3", "5", "b7"),
}

_INTERVAL_SORT = {
    "1": 0,
    "b2/b9": 1,
    "2/9": 2,
    "b3": 3,
    "3": 4,
    "4/11": 5,
    "b5/#11": 6,
    "5": 7,
    "#5/b13": 8,
    "6/13": 9,
    "b7": 10,
    "7": 11,
}

_BLOCKED_TAB_TERMS = (
    "full tab",
    "full modern",
    "modern copyrighted",
    "copyrighted song",
    "transcribe",
    "youtube",
    "recording",
    "whole solo",
    "full solo",
)


@dataclass(frozen=True)
class ProgressionEventTemplate:
    function: str
    chord_name: str
    root: str
    quality: str
    fret: int
    strings: tuple[int, ...]
    pedals: tuple[str, ...] = ()
    levers: tuple[str, ...] = ()
    route_reason: str = ""
    next_move: str = ""
    difficulty: str = "starter"
    route_family: str = "home_pocket"
    voicing_label: str = ""


@dataclass(frozen=True)
class RouteTemplate:
    route_id: str
    family: str
    label: str
    difficulty: str
    summary: str
    events: tuple[ProgressionEventTemplate, ...]


def progression_guide_for_question(question: str) -> dict[str, Any] | None:
    """Return a deterministic progression-guide response, or None.

    The parser is intentionally conservative. Two-chord movement prompts such
    as "Show me a G to C move" remain owned by the movement/tab route.
    """

    if not question or _looks_like_blocked_song_tab(question):
        return None

    routes = _routes_for_question(question)
    if not routes:
        return None

    key = _key_for_routes(routes)
    progression_label = _progression_label_for_routes(routes)
    chords = [event.chord_name for event in routes[0].events]
    route_payloads, positions = _build_route_payloads(routes)
    if not route_payloads or not positions:
        return None

    fretboard = _build_fretboard_payload(
        key=key,
        progression_label=progression_label,
        routes=route_payloads,
        positions=positions,
    )
    validate_fretboard_payload(fretboard)

    progression_guide = {
        "type": "e9-progression-guide-v0",
        "key": key,
        "progression": progression_label,
        "chords": chords,
        "recommendedRouteId": route_payloads[0]["id"],
        "recommendedRoute": route_payloads[0],
        "routes": route_payloads,
        "sourceContext": [
            {
                "kind": "rule",
                "label": "Validated E9 progression route",
                "sourceId": "pocketsteel.fretboard_examples",
                "description": (
                    "Progression-guide rows are generated from deterministic "
                    "E9 pitch logic; source material does not choose frets, "
                    "strings, pedals, or levers."
                ),
            }
        ],
    }

    return {
        "answer": _answer_text(key, progression_label, route_payloads),
        "progression_guide": progression_guide,
        "fretboard": fretboard,
    }


def _looks_like_blocked_song_tab(question: str) -> bool:
    normalized = question.lower()
    return any(term in normalized for term in _BLOCKED_TAB_TERMS)


def _routes_for_question(question: str) -> tuple[RouteTemplate, ...] | None:
    normalized = _normalize_text(question)

    key = _parse_key_context(normalized)
    if _looks_like_v7_to_i(normalized):
        return _v7_i_routes(key or "G")

    if _looks_like_i_iv_v_i(normalized) and not _looks_like_tab_movement_request(normalized):
        return _i_iv_v_i_routes(key or _parse_key_from_chord_sequence(question))

    if _looks_like_simple_song_progression_request(normalized):
        return _i_iv_v_i_routes(key or "G")

    symbols = _chord_symbols_from_question(question)
    if len(symbols) >= 3 and _looks_like_progression_route_request(normalized):
        return _routes_for_chord_symbols(symbols)

    return None


def _normalize_text(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def _parse_key_context(normalized: str) -> str | None:
    match = re.search(r"\b(?:in|key of|in the key of)\s+([a-g](?:#|b)?)\b", normalized)
    if not match:
        return None
    return _normalize_root(match.group(1))


def _parse_key_from_chord_sequence(question: str) -> str | None:
    symbols = _chord_symbols_from_question(question)
    if symbols:
        first = symbols[0]
        if _quality_for_symbol(first) == "major":
            return _root_for_symbol(first)
    return None


def _looks_like_v7_to_i(normalized: str) -> bool:
    return bool(
        re.search(r"\b(?:v7|5\s*7|five\s*7)\s*(?:to|->|-)\s*(?:i|1)\b", normalized)
        or re.search(r"\bmove\s+from\s+(?:v7|5\s*7)\s+to\s+(?:i|1)\b", normalized)
    )


def _looks_like_i_iv_v_i(normalized: str) -> bool:
    roman = bool(re.search(r"\b(?:i|1)\s+(?:iv|4)\s+(?:v|5)\s+(?:i|1)\b", normalized))
    phrase = "1 4 5 1" in normalized or "i iv v i" in normalized
    return roman or phrase


def _looks_like_tab_movement_request(normalized: str) -> bool:
    return bool(re.search(r"\bmove(?:ment)?\b", normalized))


def _looks_like_progression_route_request(normalized: str) -> bool:
    return bool(
        re.search(r"\b(?:progression|route|through|chord\s+route|chord\s+path)\b", normalized)
    )


def _looks_like_simple_song_progression_request(normalized: str) -> bool:
    if not re.search(r"\bprogression\b", normalized):
        return False
    if re.search(r"\b(?:minor|copyright|copyrighted|transcribe|youtube|recording|solo|full\s+tab)\b", normalized):
        return False
    return bool(
        re.search(r"\b(?:simple|beginner|basic|song|practice)\b", normalized)
        or re.search(r"\bmove\s+through\b", normalized)
    )


def _chord_symbols_from_question(question: str) -> list[str]:
    symbols: list[str] = []
    pattern = re.compile(r"\b([A-Ga-g](?:#|b)?(?:maj7|m7|m|7)?)\b")
    for match in pattern.finditer(question):
        token = match.group(1)
        if token == "a":
            continue
        symbol = _normalize_symbol(token)
        if symbol:
            symbols.append(symbol)
    return symbols


def _normalize_symbol(token: str) -> str | None:
    token = token.strip()
    match = re.fullmatch(r"([A-Ga-g])(#|b)?(maj7|m7|m|7)?", token)
    if not match:
        return None
    root = _normalize_root((match.group(1) + (match.group(2) or "")))
    suffix = match.group(3) or ""
    return f"{root}{suffix}"


def _normalize_root(root: str) -> str:
    root = root.strip()
    if not root:
        return root
    letter = root[0].upper()
    accidental = root[1:] if len(root) > 1 else ""
    return f"{letter}{accidental}"


def _root_for_symbol(symbol: str) -> str:
    match = re.match(r"([A-G](?:#|b)?)", symbol)
    return match.group(1) if match else symbol


def _quality_for_symbol(symbol: str) -> str:
    if symbol.endswith("maj7"):
        return "major7"
    if symbol.endswith("m7") or symbol.endswith("m"):
        return "minor"
    if symbol.endswith("7"):
        return "dominant7"
    return "major"


def _routes_for_chord_symbols(symbols: list[str]) -> tuple[RouteTemplate, ...] | None:
    labels = tuple(symbols)
    if labels == ("C", "F", "G", "C"):
        return _c_i_iv_v_i_routes()
    if labels == ("G", "C", "D", "G"):
        return _g_i_iv_v_i_routes()
    if labels == ("C", "Am", "Em", "F", "Dm", "G7", "C"):
        return (_c_diatonic_home_route(),)
    if labels == ("C", "Am", "F", "G"):
        return (_c_i_vi_iv_v_route(),)
    return None


def _i_iv_v_i_routes(key: str | None) -> tuple[RouteTemplate, ...] | None:
    key = key or "C"
    if key == "C":
        return _c_i_iv_v_i_routes()
    if key == "G":
        return _g_i_iv_v_i_routes()
    return None


def _v7_i_routes(key: str) -> tuple[RouteTemplate, ...] | None:
    if key == "G":
        return (
            RouteTemplate(
                route_id="g-v7-i-dominant-resolution",
                family="dominant_resolution",
                label="G key V7 to I shell resolution",
                difficulty="common",
                summary=(
                    "Use the E-lower dominant shell to hear D7 pull back "
                    "into G without leaving the pocket."
                ),
                events=(
                    ProgressionEventTemplate(
                        function="V7",
                        chord_name="D7",
                        root="D",
                        quality="dominant7",
                        fret=3,
                        strings=(10, 8, 6),
                        pedals=("B",),
                        levers=("E",),
                        route_reason="Dominant shell: root, 3rd, and b7 are present.",
                        next_move="Release the B pedal and E-lower lever to resolve to G.",
                        difficulty="common",
                        route_family="dominant_shell",
                        voicing_label="D7(no5) shell",
                    ),
                    ProgressionEventTemplate(
                        function="I",
                        chord_name="G",
                        root="G",
                        quality="major",
                        fret=3,
                        strings=(10, 8, 6),
                        route_reason="Same fret resolution into the I chord.",
                        next_move="Let the release create the resolution.",
                        difficulty="starter",
                        route_family="home_pocket",
                    ),
                ),
            ),
        )
    if key == "C":
        return (
            RouteTemplate(
                route_id="c-v7-i-dominant-resolution",
                family="dominant_resolution",
                label="C key V7 to I shell resolution",
                difficulty="common",
                summary="Use the G7 shell and resolve it at the same fret to C.",
                events=(
                    ProgressionEventTemplate(
                        function="V7",
                        chord_name="G7",
                        root="G",
                        quality="dominant7",
                        fret=8,
                        strings=(10, 8, 6),
                        pedals=("B",),
                        levers=("E",),
                        route_reason="Dominant shell: root, 3rd, and b7 are present.",
                        next_move="Release the B pedal and E-lower lever to resolve to C.",
                        difficulty="common",
                        route_family="dominant_shell",
                        voicing_label="G7(no5) shell",
                    ),
                    ProgressionEventTemplate(
                        function="I",
                        chord_name="C",
                        root="C",
                        quality="major",
                        fret=8,
                        strings=(10, 8, 6),
                        route_reason="Same fret resolution into the I chord.",
                        next_move="Let the release create the resolution.",
                        difficulty="starter",
                        route_family="home_pocket",
                    ),
                ),
            ),
        )
    return None


def _c_i_iv_v_i_routes() -> tuple[RouteTemplate, ...]:
    return (
        RouteTemplate(
            route_id="c-i-iv-v-i-home-pocket",
            family="home_pocket",
            label="C I-IV-V-I home-pocket route",
            difficulty="starter",
            summary="Stay near fret 8 and use A+B for IV, then move up two frets for V.",
            events=(
                ProgressionEventTemplate("I", "C", "C", "major", 8, (5, 6, 8), route_reason="Straight-bar home position for C.", next_move="Press A+B at the same fret for IV."),
                ProgressionEventTemplate("IV", "F", "F", "major", 8, (5, 6, 8), pedals=("A", "B"), route_reason="A+B gives the IV chord without moving the bar.", next_move="Slide up two frets with A+B down for V."),
                ProgressionEventTemplate("V", "G", "G", "major", 10, (5, 6, 8), pedals=("A", "B"), route_reason="Same grip and pedals, two frets higher.", next_move="Return to fret 8 and release pedals for I."),
                ProgressionEventTemplate("I", "C", "C", "major", 8, (5, 6, 8), route_reason="Release back to the home-position C.", next_move="Use this as the landing point."),
            ),
        ),
        RouteTemplate(
            route_id="c-i-iv-v-i-ascending-same-grip",
            family="ascending_same_grip",
            label="C I-IV-V-I ascending same-grip route",
            difficulty="common",
            summary="Keep the 5-6-8 grip and finish on the A plus E-raise C position.",
            events=(
                ProgressionEventTemplate("I", "C", "C", "major", 8, (5, 6, 8), route_reason="Straight-bar C reference.", next_move="Press A+B at the same fret for IV."),
                ProgressionEventTemplate("IV", "F", "F", "major", 8, (5, 6, 8), pedals=("A", "B"), route_reason="Same fret IV chord.", next_move="Slide to fret 10 with A+B for V."),
                ProgressionEventTemplate("V", "G", "G", "major", 10, (5, 6, 8), pedals=("A", "B"), route_reason="Pedals-down V chord.", next_move="Move to fret 11 with A plus E-raise for the final I."),
                ProgressionEventTemplate("I", "C", "C", "major", 11, (5, 6, 8), pedals=("A",), levers=("F",), route_reason="A pedal plus E-raise gives another C color.", next_move="Compare its color against the fret 8 no-pedals C."),
            ),
        ),
        RouteTemplate(
            route_id="c-i-iv-v-i-pedals-down",
            family="pedals_down",
            label="C I-IV-V-I pedals-down route",
            difficulty="common",
            summary="Use the fret 15 A+B C, then release into nearby no-pedals IV and V positions.",
            events=(
                ProgressionEventTemplate("I", "C", "C", "major", 15, (5, 6, 8), pedals=("A", "B"), route_reason="Pedals-down C position.", next_move="Release and move back two frets for F."),
                ProgressionEventTemplate("IV", "F", "F", "major", 13, (5, 6, 8), route_reason="No-pedals F sits below the pedals-down C.", next_move="Move up two frets for G."),
                ProgressionEventTemplate("V", "G", "G", "major", 15, (5, 6, 8), route_reason="No-pedals G at the same fret as the pedals-down C.", next_move="Press A+B to resolve to C."),
                ProgressionEventTemplate("I", "C", "C", "major", 15, (5, 6, 8), pedals=("A", "B"), route_reason="Press A+B for the I chord resolution.", next_move="Use the pedal change as the arrival."),
            ),
        ),
        RouteTemplate(
            route_id="c-i-iv-v-i-dominant-shell",
            family="dominant_shell",
            label="C I-IV-V-I dominant-shell route",
            difficulty="advanced",
            summary="Use lower strings and E-lower color to make the V7 pull clear.",
            events=(
                ProgressionEventTemplate("I", "C", "C", "major", 8, (6, 8, 10), route_reason="Lower-string C grip with no pedals/no levers.", next_move="Move to the E-lower IV color."),
                ProgressionEventTemplate("IV", "F", "F", "major", 6, (10, 8, 7), levers=("E",), route_reason="E-lower gives a compact F voicing.", next_move="Move to the G7 shell."),
                ProgressionEventTemplate("V7", "G7", "G", "dominant7", 8, (10, 8, 6), pedals=("B",), levers=("E",), route_reason="Dominant shell: root, 3rd, and b7 are present.", next_move="Release B and E-lower to resolve to C.", difficulty="advanced", route_family="dominant_shell", voicing_label="G7(no5) shell"),
                ProgressionEventTemplate("I", "C", "C", "major", 8, (10, 8, 6), route_reason="Same fret C resolution after the dominant shell.", next_move="Use the release as the cadence."),
            ),
        ),
    )


def _g_i_iv_v_i_routes() -> tuple[RouteTemplate, ...]:
    return (
        RouteTemplate(
            route_id="g-i-iv-v-i-home-pocket",
            family="home_pocket",
            label="G I-IV-V-I home-pocket route",
            difficulty="starter",
            summary="Stay near fret 3 and use A+B for IV, then move up two frets for V.",
            events=(
                ProgressionEventTemplate("I", "G", "G", "major", 3, (5, 6, 8), route_reason="Straight-bar home position for G.", next_move="Press A+B at the same fret for IV."),
                ProgressionEventTemplate("IV", "C", "C", "major", 3, (5, 6, 8), pedals=("A", "B"), route_reason="A+B gives the IV chord without moving the bar.", next_move="Slide up two frets with A+B down for V."),
                ProgressionEventTemplate("V", "D", "D", "major", 5, (5, 6, 8), pedals=("A", "B"), route_reason="Same grip and pedals, two frets higher.", next_move="Return to fret 3 and release pedals for I."),
                ProgressionEventTemplate("I", "G", "G", "major", 3, (5, 6, 8), route_reason="Release back to the home-position G.", next_move="Use this as the landing point."),
            ),
        ),
        RouteTemplate(
            route_id="g-i-iv-v-i-pedals-down",
            family="pedals_down",
            label="G I-IV-V-I pedals-down route",
            difficulty="common",
            summary="Use the fret 10 A+B G, then release into nearby no-pedals IV and V positions.",
            events=(
                ProgressionEventTemplate("I", "G", "G", "major", 10, (5, 6, 8), pedals=("A", "B"), route_reason="Pedals-down G position.", next_move="Release and move back two frets for C."),
                ProgressionEventTemplate("IV", "C", "C", "major", 8, (5, 6, 8), route_reason="No-pedals C sits below the pedals-down G.", next_move="Move up two frets for D."),
                ProgressionEventTemplate("V", "D", "D", "major", 10, (5, 6, 8), route_reason="No-pedals D at the same fret as the pedals-down G.", next_move="Press A+B to resolve to G."),
                ProgressionEventTemplate("I", "G", "G", "major", 10, (5, 6, 8), pedals=("A", "B"), route_reason="Press A+B for the I chord resolution.", next_move="Use the pedal change as the arrival."),
            ),
        ),
    )


def _c_diatonic_home_route() -> RouteTemplate:
    return RouteTemplate(
        route_id="c-diatonic-home-pocket",
        family="diatonic_home_pocket",
        label="C diatonic home-pocket route",
        difficulty="common",
        summary="A compact C major-family route for C, Am, Em, F, Dm, G7, and C.",
        events=(
            ProgressionEventTemplate("I", "C", "C", "major", 8, (8, 6, 5), route_reason="C major home grip.", next_move="Add the A pedal on lower strings for Am."),
            ProgressionEventTemplate("vi", "Am", "A", "minor", 8, (10, 8, 6), pedals=("A",), route_reason="A pedal supplies the A minor root on string 10.", next_move="Move to an E minor grip in the same pocket."),
            ProgressionEventTemplate("iii", "Em", "E", "minor", 8, (6, 5, 2), route_reason="Same fret E minor triad across 6-5-2.", next_move="Press A+B for F."),
            ProgressionEventTemplate("IV", "F", "F", "major", 8, (6, 5, 4), pedals=("A", "B"), route_reason="A+B produces F across 6-5-4.", next_move="Move to the D minor grip."),
            ProgressionEventTemplate("ii", "Dm", "D", "minor", 8, (7, 6, 5), pedals=("A", "B"), route_reason="A+B gives a D minor triad across 7-6-5.", next_move="Use the dominant shell to set up C."),
            ProgressionEventTemplate("V7", "G7", "G", "dominant7", 8, (10, 8, 6), pedals=("B",), levers=("E",), route_reason="Dominant shell: root, 3rd, and b7 are present.", next_move="Release B and E-lower to resolve.", difficulty="advanced", route_family="dominant_shell", voicing_label="G7(no5) shell"),
            ProgressionEventTemplate("I", "C", "C", "major", 8, (8, 6, 5), route_reason="Return to the C home grip.", next_move="Let the release make the cadence clear."),
        ),
    )


def _c_i_vi_iv_v_route() -> RouteTemplate:
    return RouteTemplate(
        route_id="c-i-vi-iv-v-home-pocket",
        family="home_pocket",
        label="C I-vi-IV-V beginner route",
        difficulty="starter",
        summary="A compact route through C, Am, F, and G near fret 8.",
        events=(
            ProgressionEventTemplate("I", "C", "C", "major", 8, (5, 6, 8), route_reason="Straight-bar C reference.", next_move="Move to the A pedal minor grip."),
            ProgressionEventTemplate("vi", "Am", "A", "minor", 8, (10, 8, 6), pedals=("A",), route_reason="A pedal supplies the A minor root.", next_move="Press A+B at fret 8 for F."),
            ProgressionEventTemplate("IV", "F", "F", "major", 8, (5, 6, 8), pedals=("A", "B"), route_reason="Same fret A+B IV chord.", next_move="Slide up two frets with A+B for G."),
            ProgressionEventTemplate("V", "G", "G", "major", 10, (5, 6, 8), pedals=("A", "B"), route_reason="Same grip and pedals, two frets higher.", next_move="Resolve back to C if you continue the loop."),
        ),
    )


def _key_for_routes(routes: tuple[RouteTemplate, ...]) -> str:
    first = routes[0].events[0]
    return first.root


def _progression_label_for_routes(routes: tuple[RouteTemplate, ...]) -> str:
    return "-".join(event.function for event in routes[0].events)


def _build_route_payloads(
    routes: tuple[RouteTemplate, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    route_payloads: list[dict[str, Any]] = []
    positions: list[dict[str, Any]] = []
    for route_index, route in enumerate(routes):
        event_payloads: list[dict[str, Any]] = []
        for event_index, event in enumerate(route.events, start=1):
            visible = route_index == 0
            position = _position_for_event(route, event, event_index, visible)
            position_payload = position.to_position_payload()
            positions.append(position_payload)
            event_payloads.append(_event_payload(event, position_payload, route, event_index))
        route_payloads.append(
            {
                "id": route.route_id,
                "family": route.family,
                "label": route.label,
                "difficulty": route.difficulty,
                "summary": route.summary,
                "events": event_payloads,
                "provenance": "deterministic_original_exercise",
            }
        )
    return route_payloads, positions


def _position_for_event(
    route: RouteTemplate,
    event: ProgressionEventTemplate,
    event_index: int,
    visible_by_default: bool,
) -> FretboardPosition:
    notes, intervals = _notes_and_intervals(event)
    expected = _EXPECTED_INTERVALS.get(event.quality, ("1", "3", "5"))
    present = tuple(_sort_intervals(set(intervals.values())))
    omitted = tuple(interval for interval in expected if interval not in present)
    added = tuple(interval for interval in present if interval not in expected)
    voicing_type = _voicing_type(event, omitted)
    is_full_chord = not omitted
    caveats = tuple(_event_caveats(event, omitted))
    label = event.voicing_label or f"{event.chord_name} {event.function}"
    route_slug = _slug(route.route_id)
    chord_slug = _slug(event.chord_name)
    return FretboardPosition(
        id=f"{route_slug}-{event_index}-{chord_slug}",
        label=label,
        root=event.root,
        quality=event.quality,
        fret=event.fret,
        strings=event.strings,
        grip=grip_label(event.strings),
        pedals=event.pedals,
        levers=event.levers,
        position_kind="progression_route_event",
        family=event.route_family,
        tier=event.difficulty,
        color_role=_color_role(event_index),
        visible_by_default=visible_by_default,
        sort_order=(1000 if visible_by_default else 2000) + event_index,
        notes=notes,
        intervals=intervals,
        omitted_intervals=omitted,
        added_intervals=added,
        is_full_chord=is_full_chord,
        is_partial=bool(omitted),
        is_rootless="1" in omitted,
        caveats=caveats,
        validation_status="pitch_validated",
        function=event.function,
        key_context=_key_for_routes((route,)),
        why_use_it=event.route_reason,
        explanation_short=_explanation_short(event, omitted),
        explanation_long=_explanation_long(event, omitted),
        tier_reason=_tier_reason(event),
        when_to_use=_when_to_use(event),
        sound_character=_sound_character(event, voicing_type),
        movement_use=event.next_move,
        resolution_use=event.next_move if event.function in {"V", "V7"} else "",
    )


def _notes_and_intervals(
    event: ProgressionEventTemplate,
) -> tuple[dict[str, str], dict[str, str]]:
    changed_notes = notes_for_controls(event.pedals + event.levers)
    notes: dict[str, str] = {}
    intervals: dict[str, str] = {}
    for string in event.strings:
        note = note_at_fret(changed_notes[string], event.fret)
        key = str(string)
        notes[key] = note
        intervals[key] = interval_for_note(event.root, note)
    return notes, intervals


def _sort_intervals(intervals: Iterable[str]) -> list[str]:
    return sorted(intervals, key=lambda interval: _INTERVAL_SORT.get(interval, 99))


def _voicing_type(event: ProgressionEventTemplate, omitted: tuple[str, ...]) -> str:
    if event.quality == "dominant7" and omitted == ("5",):
        return "dominant_shell"
    if omitted:
        return "partial"
    return "full_chord"


def _event_caveats(event: ProgressionEventTemplate, omitted: tuple[str, ...]) -> list[str]:
    caveats: list[str] = []
    if omitted:
        caveats.append(f"Omits {', '.join(omitted)}.")
    if event.quality == "dominant7" and omitted == ("5",):
        caveats.append("Dominant shell: root, 3rd, and b7 are present; the 5th is omitted.")
    return caveats


def _event_payload(
    event: ProgressionEventTemplate,
    position_payload: dict[str, Any],
    route: RouteTemplate,
    event_index: int,
) -> dict[str, Any]:
    contains = tuple(_sort_intervals(set(position_payload.get("intervals", {}).values())))
    omits = tuple(position_payload.get("omittedIntervals") or ())
    return {
        "id": f"{route.route_id}-event-{event_index}",
        "renderablePositionId": position_payload["id"],
        "function": event.function,
        "chordName": event.chord_name,
        "root": event.root,
        "quality": event.quality,
        "fret": event.fret,
        "strings": list(event.strings),
        "grip": grip_label(event.strings),
        "pedals": list(event.pedals),
        "levers": list(event.levers),
        "changes": _control_labels(event),
        "notes": position_payload.get("notes", {}),
        "intervals": position_payload.get("intervals", {}),
        "contains": list(contains),
        "omits": list(omits),
        "voicingType": _voicing_type(event, tuple(omits)),
        "isFullChord": bool(position_payload.get("isFullChord")),
        "isPartial": bool(position_payload.get("isPartial")),
        "routeReason": event.route_reason,
        "nextMove": event.next_move,
        "difficulty": event.difficulty,
        "routeFamily": event.route_family,
        "validationStatus": "pitch_validated",
        "provenance": "deterministic_original_exercise",
    }


def _control_labels(event: ProgressionEventTemplate) -> list[str]:
    labels = [f"{pedal} pedal" for pedal in event.pedals]
    for lever in event.levers:
        if lever == "E":
            labels.append("E-lower lever")
        elif lever == "F":
            labels.append("E-raise lever")
        else:
            labels.append(f"{lever} lever")
    return labels


def _build_fretboard_payload(
    *,
    key: str,
    progression_label: str,
    routes: list[dict[str, Any]],
    positions: list[dict[str, Any]],
) -> dict[str, Any]:
    highlights = [
        {
            "id": position["id"],
            "fret": position["fret"],
            "strings": list(position.get("strings", [])),
            "label": position["label"],
            "pedals": list(position.get("pedals", [])),
            "levers": list(position.get("levers", [])),
            "role": position.get("function", ""),
        }
        for position in positions
    ]
    return {
        "type": FRETBOARD_PAYLOAD_TYPE,
        "title": f"{key} {progression_label} progression route",
        "subtitle": "Validated E9 progression positions",
        "description": "Validated E9 progression positions",
        "tuning": "E9",
        "copedent": {
            "id": "standard-e9-progression-guide",
            "label": "Standard 10-string E9",
            "status": "deterministic_rule",
        },
        "key": key,
        "strings": {
            "count": 10,
            "labels": {str(string): note for string, note in E9_OPEN_STRINGS.items()},
        },
        "positions": positions,
        "highlights": highlights,
        "legend": [
            {"id": "primary", "label": "Start / home chord", "color": "primary"},
            {"id": "secondary", "label": "Middle chord", "color": "secondary"},
            {"id": "alternate", "label": "Resolution setup", "color": "alternate"},
            {"id": "reference", "label": "Return / reference", "color": "reference"},
        ],
        "query": {
            "kind": "progression_guide",
            "key": key,
            "progression": progression_label,
            "recommendedRouteId": routes[0]["id"] if routes else "",
        },
        "sourceContext": [
            {
                "kind": "rule",
                "label": "Validated E9 progression route",
                "sourceId": "pocketsteel.fretboard_examples",
                "description": "Positions are generated from deterministic pitch math.",
            }
        ],
    }


def _answer_text(key: str, progression_label: str, routes: list[dict[str, Any]]) -> str:
    recommended = routes[0]
    lines = [
        f"Here is a practical {key} {progression_label} route on E9.",
        "This is an original deterministic practice route, not a song transcription or source-backed arrangement.",
        recommended["summary"],
        "",
        "Recommended route:",
    ]
    for event in recommended["events"]:
        controls = _controls_text(event)
        omits = event.get("omits") or []
        voicing_note = ""
        if omits:
            voicing_note = f" ({event['voicingType']}; omits {', '.join(omits)})"
        lines.append(
            f"- {event['function']} - {event['chordName']}: fret {event['fret']}, "
            f"strings {event['grip']}, {controls}{voicing_note}. {event['routeReason']}"
        )
    if len(routes) > 1:
        lines.append("")
        lines.append(
            "Alternate routes are included in the progression guide so you can compare "
            "home-pocket, ascending, pedals-down, and dominant-shell choices."
        )
    lines.append("")
    lines.append(
        "Use this as a route map, not a song arrangement: pick one route, play each "
        "chord slowly, and listen to how the pedal or bar move sets up the next chord."
    )
    return "\n".join(lines)


def _controls_text(event: dict[str, Any]) -> str:
    changes = event.get("changes") or []
    if not changes:
        return "no pedals/no levers"
    return " + ".join(str(change) for change in changes)


def _explanation_short(event: ProgressionEventTemplate, omitted: tuple[str, ...]) -> str:
    if omitted:
        return f"{event.chord_name} {event.function} color; omits {', '.join(omitted)}."
    return f"{event.chord_name} {event.function} position validated by E9 pitch logic."


def _explanation_long(event: ProgressionEventTemplate, omitted: tuple[str, ...]) -> str:
    details = event.route_reason or "This row is part of the deterministic progression route."
    if omitted:
        details += f" It is labeled honestly because it omits {', '.join(omitted)}."
    return details


def _tier_reason(event: ProgressionEventTemplate) -> str:
    if event.difficulty == "starter":
        return "Starter route: compact grip, familiar home-pocket movement."
    if event.difficulty == "advanced":
        return "Advanced route: uses shell or lever color that needs slower checking."
    return "Common route: practical once the starter pocket is comfortable."


def _when_to_use(event: ProgressionEventTemplate) -> str:
    if event.function in {"V", "V7"}:
        return "Use it to set up the return to I."
    if event.function == "IV":
        return "Use it to move away from I without losing the pocket."
    return "Use it as a reference point for the progression."


def _sound_character(event: ProgressionEventTemplate, voicing_type: str) -> str:
    if voicing_type == "dominant_shell":
        return "dominant pull"
    if event.levers:
        return "lever color"
    if event.pedals:
        return "pedal color"
    return "straight-bar reference"


def _color_role(event_index: int) -> str:
    return ("primary", "secondary", "alternate", "reference")[(event_index - 1) % 4]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
