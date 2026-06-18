"""Deterministic tab-example selection for answer responses.

The answer route may attach these short examples as supporting teaching
material, but the tab itself always comes from the rules-based tab engine.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable

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
        if example.matcher(normalized):
            return _payload_for_example(example)
    return None


def answer_body_for_tab_example(tab_example: dict[str, Any]) -> str | None:
    """Return direct answer prose for a selected deterministic tab example."""

    tab_id = str(tab_example.get("id") or "")
    for example in _answer_tab_examples():
        if example.id == tab_id:
            return example.answer_body
    return None


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
            matcher=lambda q: (
                (
                    _mentions_g_major(q)
                    and _has_any(q, (" grip", "4-5-6", "456", "strings 4 5 6", "strings 4-5-6"))
                )
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
                {"eventId": "g-to-c-2", "chord": "C", "byString": {"5": "1", "6": "5", "8": "3"}},
            ],
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
                "grip": "3-5-6",
            },
            intervals=[
                {"eventId": "a-b-pedal-major-1", "chord": "G", "byString": {"3": "1", "5": "3", "6": "5"}}
            ],
            matcher=lambda q: _mentions_ab_pedals(q) and _has_any(q, ("use", "example", "position", "show", "play")),
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
            matcher=lambda q: _mentions_e_lower(q) and _has_any(q, ("move", "example", "show", "color")),
        ),
        AnswerTabExample(
            id="beginner-g-two-event-lick",
            engine_example_id="beginner_lick",
            title="Beginner E9 lick in G",
            answer_body=(
                "Here is a short beginner-safe lick. "
                "Keep the timing slow, let the notes sustain, and focus on clean movement between events."
            ),
            explanation="A short original G lick: pick the grip, press into the C sound, then release back to G.",
            context={
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "4-5-6",
            },
            intervals=[
                {"eventId": "beginner-g-lick-1", "chord": "G", "byString": {"4": "1", "5": "5", "6": "3"}},
                {"eventId": "beginner-g-lick-2", "chord": "C", "byString": {"5": "1", "6": "5", "8": "3"}},
                {"eventId": "beginner-g-lick-3", "chord": "G", "byString": {"4": "1", "5": "5", "6": "3"}},
            ],
            matcher=lambda q: "lick" in q and _has_any(q, ("beginner", "simple", "country", "in g", "e9")),
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


def _mentions_ab_pedals(question: str) -> bool:
    return bool(
        re.search(r"\ba\s*\+\s*b\b", question)
        or re.search(r"\ba\s*&\s*b\b", question)
        or "a and b" in question
        or "ab pedals" in question
        or "a+b pedals" in question
    )


def _mentions_e_lower(question: str) -> bool:
    return "e-lower" in question or "e lower" in question or "lowering the e" in question or "e lever" in question


def _has_any(question: str, terms: tuple[str, ...]) -> bool:
    return any(term in question for term in terms)
