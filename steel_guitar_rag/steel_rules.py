"""Stable E9/copedent/theory rules for Steel Guitar RAG.

This module is intentionally separate from RAG retrieval and curated web
sources. It covers stable, high-confidence musical facts that should not depend
on old forum snippets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


STANDARD_E9_OPEN_STRINGS: dict[int, str] = {
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

STANDARD_E9_STRING_GAUGES: dict[int, str] = {
    10: ".036 wound",
}

STANDARD_EMMONS_CHANGES: dict[str, tuple[str, ...]] = {
    "a": ("raises 5 and 10 B to C#",),
    "b": ("raises 3 and 6 G# to A",),
    "c": ("raises 4 E to F#", "raises 5 B to C#"),
    "f": ("raises 4 and 8 E to F",),
    "f lever": ("raises 4 and 8 E to F",),
    "e-lower": ("lowers 4 and 8 E to D#",),
    "e lower": ("lowers 4 and 8 E to D#",),
    "2nd string lower": ("commonly lowers 2 D# to D/C#",),
    "9th lower": ("commonly lowers 9 D to C#",),
}

COMMON_E9_GRIPS: tuple[str, ...] = ("3-4-5", "4-5-6", "5-6-8", "6-8-10")

NUMBER_CHORDS: dict[tuple[str, str], tuple[str, str]] = {
    ("2m", "g"): ("Am", "A-C-E"),
    ("ii", "g"): ("Am", "A-C-E"),
}


@dataclass(frozen=True)
class RuleAnswer:
    intent: str
    answer: str


def explain_common_grips() -> str:
    return "Common E9 grips include " + ", ".join(COMMON_E9_GRIPS) + "."


def explain_triad(*, include_e9_grips: bool = True) -> str:
    lines = [
        "A triad is a three-note chord built from a root, a third, and a fifth.",
        "",
        "Examples:",
        "- Major triad: 1, 3, 5.",
        "- Minor triad: 1, b3, 5.",
    ]
    if include_e9_grips:
        lines.extend(["", f"On E9, {explain_common_grips().replace('Common E9 grips', 'common major-triad grips')}"])
    return "\n".join(lines)


def explain_number_chord(number: str, key: str) -> str | None:
    normalized_number = number.strip().lower().replace(" ", "")
    normalized_key = key.strip().lower()
    chord = NUMBER_CHORDS.get((normalized_number, normalized_key))
    if chord is None:
        return None
    name, tones = chord
    if normalized_number in {"2m", "ii"} and normalized_key == "g":
        return (
            f"In the key of G, the 2m chord is A minor ({name}): {tones}. "
            "Interval-wise, 2 minor means 1-b3-5 built on scale degree 2.\n\n"
            "Two practical E9 options:\n"
            "- 3rd fret with B+C pedals on strings 3-4-5: the notes outline A-C-E, with the chord tones in an inversion.\n"
            "- 8th fret with the A pedal on strings 5-6-8: string 5 gives A with the A pedal, string 6 gives E, and string 8 gives C.\n\n"
            "Hear it as the ii minor in G, then practice moving it toward D or D7, the 5-dominant chord in G, before resolving back to G."
        )
    return f"In the key of {key}, {number} is {name}: {tones}."


def explain_e9_change(name: str) -> str | None:
    key = re.sub(r"\s+", " ", name.strip().lower())
    if key in {"a+f", "a + f", "a pedal + f lever", "a pedal and f lever"}:
        return (
            "On standard E9, A+F means using the A pedal with the F lever to make a major-chord position three frets above the open major position.\n\n"
            "What changes\n"
            "- The A pedal raises the B strings to C#.\n"
            "- The F lever raises the E strings to F.\n"
            "- Together they give a major triad in the A+F position.\n\n"
            "Practical use\n"
            "- Use it to connect major chords smoothly without jumping straight to the A+B position.\n"
            "- Example: G major is available at the 6th fret with A pedal + F lever.\n"
            f"- Common grips include {', '.join(COMMON_E9_GRIPS)}, depending on your copedent."
        )
    changes = STANDARD_EMMONS_CHANGES.get(key)
    if changes is None:
        return None
    return f"On standard Emmons E9, {name} " + "; ".join(changes) + "."


def explain_tab_symbol(symbol: str) -> str | None:
    compact = symbol.strip().lower()
    if compact == "5^7":
        return (
            "5^7 is ambiguous without the surrounding line.\n\n"
            "Two common readings:\n"
            "- In chord-symbol or Nashville-number context, it may mean 5 dominant 7, also called V7.\n"
            "- In steel tab context, it may mean a move or slide from fret 5 to fret 7.\n\n"
            "Send the surrounding tab or chord line and I can tell which meaning fits."
        )
    return None


def explain_e9_string_gauge(string_number: int) -> str | None:
    note = STANDARD_E9_OPEN_STRINGS.get(string_number)
    gauge = STANDARD_E9_STRING_GAUGES.get(string_number)
    if note is None or gauge is None:
        return None
    return (
        f"On standard E9, the {ordinal(string_number)} string is {note}, and a common gauge is around {gauge}.\n\n"
        "Gauge caveat:\n"
        "- String sets vary by brand, scale length, and player preference.\n"
        "- Check the guitar or string-set chart if you are matching an existing setup."
    )


def answer_from_rules(question: str) -> RuleAnswer | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower()
    if not q:
        return None
    if re.search(r"\bwhat\s+is\s+(?:a\s+)?triad\b", q):
        return RuleAnswer(intent="copedent_fretboard", answer=explain_triad())
    if "common grip" in q or "common e9 grip" in q:
        return RuleAnswer(intent="copedent_fretboard", answer=explain_common_grips())
    if re.search(r"\b(?:what\s+does\s+)?a\s*\+\s*f\b", q) or (
        "a pedal" in q and "f lever" in q
    ):
        answer = explain_e9_change("A+F")
        return RuleAnswer(intent="copedent_fretboard", answer=answer) if answer else None
    if "gauge" in q and ("10th string" in q or "string 10" in q) and "e9" in q:
        answer = explain_e9_string_gauge(10)
        return RuleAnswer(intent="copedent_fretboard", answer=answer) if answer else None
    if re.search(r"\b(?:how\s+do\s+i\s+play\s+)?(?:a\s+)?2m\s+in\s+(?:the\s+key\s+of\s+)?g\b", q):
        answer = explain_number_chord("2m", "G")
        return RuleAnswer(intent="copedent_fretboard", answer=answer) if answer else None
    symbol = re.search(r"\b5\^7\b", q)
    if symbol:
        answer = explain_tab_symbol("5^7")
        return RuleAnswer(intent="copedent_fretboard", answer=answer) if answer else None
    return None


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"
