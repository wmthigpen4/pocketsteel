"""Deterministic tab-example selection for answer responses.

The answer route may attach these short examples as supporting teaching
material, but the tab itself always comes from the rules-based tab engine.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable

from pocketsteel.fretboard_examples import (
    E9_OPEN_STRINGS,
    FRETBOARD_PAYLOAD_TYPE,
    FretboardPosition,
    grip_label,
    note_at_fret,
    notes_for_controls,
    validate_fretboard_payload,
)
from pocketsteel.tab_engine import default_e9_copedent_profile, render_example, tab_examples


Matcher = Callable[[str], bool]


@dataclass(frozen=True)
class AnswerTabExample:
    id: str
    engine_example_id: str
    title: str
    answer_body: str
    explanation: str
    context: dict[str, Any]
    intervals: list[dict[str, Any]]
    kind: str
    display_mode: str
    matcher: Matcher


def tab_example_payload_for_question(
    question: str,
    *,
    answer_intent: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return a validated tab example payload for safe, known prompts."""

    del answer_intent  # Reserved for the next slice without coupling to routing yet.
    normalized = _normalize_question(question)
    if not normalized or _is_blocked_tab_request(normalized):
        return None
    for example in _answer_tab_examples():
        if example.display_mode != "tab_and_fretboard":
            continue
        if example.matcher(normalized):
            return _payload_for_example(example)
    return None


def static_fretboard_payload_for_question(question: str) -> dict[str, Any] | None:
    """Return a fretboard-only payload for static grip/chord prompts."""

    normalized = _normalize_question(question)
    if not normalized or _is_blocked_tab_request(normalized):
        return None
    for example in _answer_tab_examples():
        if example.display_mode != "fretboard_only":
            continue
        if example.matcher(normalized):
            payload = _payload_for_example(example)
            if payload is None:
                return None
            return fretboard_payload_for_tab_example(payload)
    return None


def static_answer_body_for_question(question: str) -> str | None:
    """Return direct answer prose for static fretboard-first prompts."""

    normalized = _normalize_question(question)
    if not normalized or _is_blocked_tab_request(normalized):
        return None
    for example in _answer_tab_examples():
        if example.display_mode == "fretboard_only" and example.matcher(normalized):
            return example.answer_body
    return None


def answer_body_for_tab_example(tab_example: dict[str, Any]) -> str | None:
    """Return direct answer prose for a selected deterministic tab example."""

    tab_id = str(tab_example.get("id") or "")
    for example in _answer_tab_examples():
        if example.id == tab_id:
            return example.answer_body
    return None


def fretboard_payload_for_tab_example(tab_example: dict[str, Any]) -> dict[str, Any] | None:
    """Build a render-safe fretboard payload from validated tab-example events."""

    if not tab_example or tab_example.get("validation", {}).get("ok") is not True:
        return None

    positions: list[FretboardPosition] = []
    interval_rows = tab_example.get("intervals")
    if not isinstance(interval_rows, list):
        interval_rows = []

    for index, event in enumerate(tab_example.get("events") or (), start=1):
        if not isinstance(event, dict):
            return None
        notes = event.get("notes")
        if not isinstance(notes, list) or not notes:
            return None
        position = _position_for_tab_event(tab_example, event, interval_rows, index)
        if position is None:
            return None
        positions.append(position)

    if not positions:
        return None

    payload = {
        "type": FRETBOARD_PAYLOAD_TYPE,
        "title": f"{tab_example['title']} fretboard view",
        "subtitle": "Deterministic E9 states derived from the tab example.",
        "description": "The fretboard cards use the same frets, strings, pedals, and levers as the tab events.",
        "tuning": "E9",
        "copedent": {
            "id": "default_e9",
            "label": "Default 10-string E9",
            "status": "deterministic_tab_example",
        },
        "key": str(tab_example.get("context", {}).get("key") or "G"),
        "strings": {
            "count": 10,
            "labels": {str(string): note for string, note in E9_OPEN_STRINGS.items()},
        },
        "positions": [position.to_position_payload() for position in positions],
        "highlights": [position.to_highlight_payload() for position in positions],
        "legend": [
            {
                "id": "primary",
                "label": "Tab event",
                "color": "primary",
                "description": "A visible tab-example state.",
            },
            {
                "id": "secondary",
                "label": "Next tab event",
                "color": "secondary",
                "description": "A following state in the same tab example.",
            },
        ],
        "notes": [
            "This payload is derived from validated tab-example events.",
            "The UI owns fretboard geometry; this payload only provides musical state.",
        ],
        "warnings": [],
        "sourceContext": [
            {
                "kind": "rule",
                "label": "Deterministic tab example",
                "sourceId": "pocketsteel.answer_tab_examples",
            }
        ],
    }
    validate_fretboard_payload(payload)
    return payload


def _payload_for_example(example: AnswerTabExample) -> dict[str, Any] | None:
    result = render_example(example.engine_example_id)
    if not result.ok:
        return None

    events = tab_examples().get(example.engine_example_id)
    if events is None:
        return None
    profile = default_e9_copedent_profile()
    return {
        "id": example.id,
        "title": example.title,
        "kind": example.kind,
        "display_tab": example.display_mode == "tab_and_fretboard",
        "preferred_display": example.display_mode,
        "context": dict(example.context),
        "rendered_tab": result.tab,
        "validation": {
            "ok": True,
            "issues": [],
            "profile": str(result.metadata.get("profile") or profile.id),
            "eventCount": int(result.metadata.get("event_count") or len(events)),
        },
        "explanation": example.explanation,
        "intervals": list(example.intervals),
        "events": [event.normalized(profile).to_dict() for event in events],
    }


def _position_for_tab_event(
    tab_example: dict[str, Any],
    event: dict[str, Any],
    interval_rows: list[Any],
    index: int,
) -> FretboardPosition | None:
    notes = event.get("notes")
    if not isinstance(notes, list) or not notes:
        return None

    strings: list[int] = []
    frets: set[int] = set()
    pedals: set[str] = set()
    levers: set[str] = set()
    for note in notes:
        if not isinstance(note, dict):
            return None
        string = note.get("string")
        fret = note.get("fret")
        if not isinstance(string, int) or not isinstance(fret, int):
            return None
        strings.append(string)
        frets.add(fret)
        raw_changes = note.get("changes") or []
        if not isinstance(raw_changes, list):
            return None
        for change in raw_changes:
            label = _control_label_for_tab_change(str(change))
            if label in {"A", "B", "C"}:
                pedals.add(label)
            else:
                levers.add(label)

    if len(frets) != 1:
        return None

    fret = next(iter(frets))
    strings_tuple = tuple(strings)
    pedals_tuple = tuple(label for label in ("A", "B", "C") if label in pedals)
    levers_tuple = tuple(label for label in ("F", "E", "G+", "G-", "D-", "D--", "V") if label in levers)
    controls = pedals_tuple + levers_tuple
    changed_open_notes = notes_for_controls(controls)
    note_names = {
        str(string): note_at_fret(changed_open_notes[string], fret)
        for string in strings_tuple
    }
    intervals = _intervals_for_tab_event(interval_rows, index, strings_tuple)
    chord = str(event.get("chord") or tab_example.get("title") or "Tab event")
    root, quality = _root_quality_for_event(tab_example, chord)
    is_partial = len(strings_tuple) < 3 or "partial" in chord.lower()
    omitted = ("3",) if is_partial and root != "unknown" and len(strings_tuple) < 3 else ()
    title = str(tab_example.get("title") or "Tab example")
    explanation = (
        f"Event {index} from {title}: strings {grip_label(strings_tuple)} at fret {fret}"
        f"{_controls_sentence(controls)}."
    )
    return FretboardPosition(
        id=f"{tab_example['id']}-event-{index}",
        label=chord,
        root=root,
        quality=quality,
        position_kind="tab_example_event",
        fret=fret,
        strings=strings_tuple,
        grip=grip_label(strings_tuple),
        pedals=pedals_tuple,
        levers=levers_tuple,
        color="primary" if index == 1 else "secondary",
        role=f"Tab event {index}",
        function=chord,
        key_context=str(tab_example.get("context", {}).get("key") or root),
        notes=note_names,
        intervals=intervals,
        explanation=explanation,
        family="tab_example",
        tier=str(tab_example.get("context", {}).get("difficulty") or "beginner"),
        color_role="primary" if index == 1 else "secondary",
        visible_by_default=True,
        sort_order=index * 10,
        omitted_intervals=omitted,
        is_full_chord=not is_partial,
        is_partial=is_partial,
        why_use_it="Use this card to connect the rendered tab event to the same strings, fret, pedals, and levers on the fretboard.",
        caveats=("This is a compact partial grip, not a full three-note chord.",) if is_partial else (),
        tier_reason="Beginner-safe because it is a short deterministic tab event with validated string-aware pedal markings.",
        when_to_use="Use it while practicing the matching tab example slowly enough to hear each change.",
        sound_character="Direct E9 tab-example sound.",
        movement_use="Compare this event with the next or previous tab event.",
        resolution_use="Release back to the prior grip when the example resolves.",
        forum_evidence=(),
        forum_evidence_status="not_searched",
        explanation_short=explanation,
        explanation_long=(
            f"This fretboard card is generated from the validated tab event rather than from retrieved text. "
            f"It therefore matches the tab's strings, fret, and controls exactly."
        ),
    )


def _control_label_for_tab_change(change: str) -> str:
    labels = {
        "A": "A",
        "B": "B",
        "C": "C",
        "E": "E",
        "F": "F",
        "G": "G-",
        "D": "D-",
        "V": "V",
    }
    return labels.get(change.strip().upper(), change.strip().upper())


def _intervals_for_tab_event(interval_rows: list[Any], index: int, strings: tuple[int, ...]) -> dict[str, str]:
    row = interval_rows[index - 1] if index - 1 < len(interval_rows) else {}
    by_string = row.get("byString") if isinstance(row, dict) else {}
    if not isinstance(by_string, dict):
        by_string = {}
    return {
        str(string): str(by_string.get(str(string)) or "color")
        for string in strings
    }


def _root_quality_for_event(tab_example: dict[str, Any], chord: str) -> tuple[str, str]:
    lowered = chord.lower()
    context_key = str(tab_example.get("context", {}).get("key") or "G")
    if "a+b" in lowered or "e-lower" in lowered or "e lower" in lowered:
        return context_key, "color" if "e" in lowered else "major"
    for root in ("C", "G", "D", "A", "E", "F", "B"):
        if lowered.startswith(root.lower()):
            return root, "major"
    return context_key, "color"


def _controls_sentence(controls: tuple[str, ...]) -> str:
    if not controls:
        return " with no pedals or levers"
    return " with " + "+".join(controls)


def _answer_tab_examples() -> tuple[AnswerTabExample, ...]:
    return (
        AnswerTabExample(
            id="g-major-456-open",
            engine_example_id="g_major_open",
            title="G major 4-5-6 grip",
            answer_body=(
                "Here is a simple G major grip on E9. "
                "This keeps the bar movement minimal and uses a beginner-safe 4-5-6 grip."
            ),
            explanation="A simple G major grip at the 3rd fret on strings 4, 5, and 6.",
            context={
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "4-5-6",
            },
            intervals=[
                {"eventId": "g-major-456-open-1", "chord": "G", "byString": {"4": "1", "5": "5", "6": "3"}}
            ],
            kind="static_grip",
            display_mode="fretboard_only",
            matcher=lambda q: (
                _matches_g_major_grip_request(q)
                or _has_any(q, ("4-5-6 grip", "456 grip", "strings 4-5-6", "strings 4 5 6"))
                or "g major chord on e9" in q
            ),
        ),
        AnswerTabExample(
            id="g-to-c-456-beginner",
            engine_example_id="g_to_c",
            title="G to C beginner move",
            answer_body=(
                "Here is a simple G to C movement on E9. "
                "The example keeps the grip compact so you can hear the chord change without chasing the neck."
            ),
            explanation="Keep the bar at fret 3, then press A+B for a short G-to-C move.",
            context={
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "4-5-6",
            },
            intervals=[
                {"eventId": "g-to-c-1", "chord": "G", "byString": {"4": "1", "5": "5", "6": "3"}},
                {"eventId": "g-to-c-2", "chord": "C partial", "byString": {"5": "3", "6": "1"}},
            ],
            kind="movement",
            display_mode="tab_and_fretboard",
            matcher=lambda q: _has_any(q, ("g to c", "g-to-c", "i to iv", "1 to 4", "one to four")),
        ),
        AnswerTabExample(
            id="a-b-pedal-major-position",
            engine_example_id="ab_major",
            title="A+B pedal major position",
            answer_body=(
                "Here is a basic A+B pedal example. "
                "The pedals raise the chord tones into a familiar major-position sound while keeping the bar still."
            ),
            explanation="A compact A+B pedal-position example using string-aware pedal markings.",
            context={
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "3-4-5",
            },
            intervals=[
                {"eventId": "a-b-pedal-major-1", "chord": "G", "byString": {"3": "1", "4": "5", "5": "3"}}
            ],
            kind="pedal_move",
            display_mode="tab_and_fretboard",
            matcher=_matches_ab_tab_request,
        ),
        AnswerTabExample(
            id="e-lower-color-move",
            engine_example_id="e_lower_color",
            title="E-lower color move",
            answer_body=(
                "Here is a small E-lower color move. "
                "Listen for how the lever changes the color of the chord without requiring a large bar move."
            ),
            explanation="A short E-lower color example that keeps the bar still and changes the harmony with the lever.",
            context={
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "4-5-6",
            },
            intervals=[
                {"eventId": "e-lower-color-1", "chord": "E-lower", "byString": {"4": "color", "5": "5", "6": "3"}}
            ],
            kind="pedal_move",
            display_mode="tab_and_fretboard",
            matcher=lambda q: _mentions_e_lower(q) and _has_word_any(q, ("move", "example", "show", "color")),
        ),
        AnswerTabExample(
            id="beginner-g-two-event-lick",
            engine_example_id="beginner_lick",
            title="Beginner E9 lick in G",
            answer_body=(
                "Here is a short beginner-safe lick. "
                "Pick the 4-5-6 grip, then press A+B only on strings 5 and 6 before returning to the open grip."
            ),
            explanation=(
                "A short original G lick: pick the 4-5-6 grip, press A+B on strings 5 and 6 for a compact "
                "C partial, then release back to G."
            ),
            context={
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "4-5-6",
            },
            intervals=[
                {"eventId": "beginner-g-lick-1", "chord": "G", "byString": {"4": "1", "5": "5", "6": "3"}},
                {"eventId": "beginner-g-lick-2", "chord": "C partial", "byString": {"5": "3", "6": "1"}},
                {"eventId": "beginner-g-lick-3", "chord": "G", "byString": {"4": "1", "5": "5", "6": "3"}},
            ],
            kind="lick",
            display_mode="tab_and_fretboard",
            matcher=lambda q: "lick" in q and _has_any(q, ("beginner", "simple beginner")),
        ),
    )


def _normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", str(question or "").strip().lower())


def _is_blocked_tab_request(question: str) -> bool:
    blocked_phrases = (
        "copyrighted song",
        "full song",
        "whole song",
        "whole solo",
        "full solo",
        "entire solo",
        "note-for-note",
        "note for note",
        "transcribe",
        "recording",
        "from youtube",
        "from a video",
        "tab the",
        "tablature for",
        "tab for",
        "named song",
        "together again",
        "panhandle rag",
    )
    return any(phrase in question for phrase in blocked_phrases)


def _mentions_g_major(question: str) -> bool:
    return bool(re.search(r"\bg\s+(major\s+)?(chord|grip|position)", question) or "g major" in question)


def _matches_g_major_grip_request(question: str) -> bool:
    return bool(re.search(r"\b(show|give)\s+me\s+(a\s+)?g\s+(major\s+)?grip\b", question))


def _mentions_ab_pedals(question: str) -> bool:
    return bool(
        re.search(r"\ba\s*\+\s*b\b", question)
        or re.search(r"\ba\s*&\s*b\b", question)
        or "a and b" in question
        or "ab pedals" in question
        or "a+b pedals" in question
    )


def _matches_ab_tab_request(question: str) -> bool:
    if not _mentions_ab_pedals(question):
        return False
    return bool(
        re.search(r"\bhow do i use\b.*\ba\s*(?:\+|&|and)\s*b\b", question)
        or re.search(r"\bshow me\b.*\ba\s*(?:\+|&|and)\s*b\b.*\b(example|position)\b", question)
        or re.search(r"\bgive me\b.*\ba\s*(?:\+|&|and)\s*b\b.*\b(example|position)\b", question)
    )


def _mentions_e_lower(question: str) -> bool:
    return "e-lower" in question or "e lower" in question or "lowering the e" in question or "e lever" in question


def _has_any(question: str, terms: tuple[str, ...]) -> bool:
    return any(term in question for term in terms)


def _has_word_any(question: str, terms: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", question) for term in terms)
