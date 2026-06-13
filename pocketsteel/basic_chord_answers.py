"""Small deterministic chord/theory answers for answer-quality fallback.

These helpers intentionally live outside the fretboard position engine so the
SGF evidence gate can depend on basic theory without staging unrelated
fretboard-catalog work.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pocketsteel.fretboard_examples import (
    minor_triad_spelling_for_answer,
    normalize_chord_words_in_text,
    normalize_key,
    normalize_requested_root,
    transpose,
)


@dataclass(frozen=True)
class BasicChordTheoryRequest:
    requested_root: str
    normalized_key: str
    quality: str


def _normalize_chord_quality(quality: str) -> str:
    q = re.sub(r"\s+", " ", (quality or "").strip().lower())
    aliases = {
        "m": "minor",
        "7": "dominant 7",
        "7th": "dominant 7",
        "seventh": "dominant 7",
        "dom": "dominant 7",
        "dom7": "dominant 7",
        "dominant": "dominant 7",
        "dominant 7": "dominant 7",
        "dim": "diminished",
        "dim7": "diminished 7",
        "diminished7": "diminished 7",
        "diminished 7": "diminished 7",
        "aug": "augmented",
        "+": "augmented",
        "suspended": "sus",
        "suspended 2": "sus2",
        "suspended 4": "sus4",
        "maj7": "major 7",
        "major 7": "major 7",
        "major 7th": "major 7",
        "major seventh": "major 7",
    }
    return aliases.get(q, q)


def basic_chord_theory_request_for_question(question: str) -> BasicChordTheoryRequest | None:
    q = normalize_chord_words_in_text(re.sub(r"\s+", " ", question or "").strip().lower())
    q = re.sub(r"[?!.,;:/]+$", "", q).strip()
    if not q:
        return None
    root_pattern = r"(?P<root>[a-g](?:#|b)?)"
    quality_pattern = (
        r"(?P<quality>"
        r"major\s+7th|major\s+seventh|major\s+7|maj7|"
        r"sus(?:2|4)?|suspended(?:\s+[24])?|"
        r"dim(?:inished)?7?|diminished(?:\s+7)?|"
        r"aug(?:mented)?|dominant(?:\s+7)?|dom7?|7th|7|"
        r"major|minor|m"
        r")"
    )
    e9_tail = r"(?:\s+on\s+(?:e9|the\s+e9|pedal\s+steel|steel))?"
    patterns = (
        rf"^what(?:'s|’s| is)\s+(?:(?:an|a)\s+)?{root_pattern}(?:[-\s]*{quality_pattern})?\s+chord{e9_tail}$",
        rf"^what\s+notes\s+are\s+in\s+(?:(?:an|a)\s+)?{root_pattern}(?:[-\s]*{quality_pattern})?\s+chord{e9_tail}$",
        rf"^what\s+notes\s+are\s+in\s+(?:(?:an|a)\s+)?{root_pattern}(?:[-\s]*{quality_pattern})?{e9_tail}$",
        rf"^what(?:'s|’s| is)\s+(?:(?:an|a)\s+)?{root_pattern}(?:[-\s]*{quality_pattern}){e9_tail}$",
        rf"^how\s+do\s+i\s+play\s+(?:(?:an|a)\s+)?{root_pattern}(?:[-\s]*{quality_pattern})?\s+chord/?{e9_tail}$",
        rf"^how\s+do\s+i\s+play\s+(?:(?:an|a)\s+)?{root_pattern}(?:[-\s]*{quality_pattern})/?{e9_tail}$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        raw_quality = match.groupdict().get("quality") or ""
        if not raw_quality and re.match(r"^how\s+do\s+i\s+play\b", q):
            return None
        quality = _normalize_chord_quality(raw_quality)
        if re.match(r"^how\s+do\s+i\s+play\b", q) and quality in {"major", "minor", "m"}:
            return None
        if not quality:
            quality = "major"
        if quality == "m":
            quality = "minor"
        if quality not in {
            "major",
            "minor",
            "major 7",
            "sus",
            "sus2",
            "sus4",
            "diminished",
            "diminished 7",
            "augmented",
            "dominant 7",
        }:
            return None
        requested_root = normalize_requested_root(match.group("root"))
        return BasicChordTheoryRequest(
            requested_root=requested_root,
            normalized_key=normalize_key(requested_root),
            quality=quality,
        )
    return None


def major_triad_spelling_for_answer(root: str) -> str:
    key = normalize_key(root)
    preferred = {
        "C": "C-E-G",
        "C#": "C#-E#-G#",
        "D": "D-F#-A",
        "D#": "D#-F##-A#",
        "E": "E-G#-B",
        "F": "F-A-C",
        "F#": "F#-A#-C#",
        "G": "G-B-D",
        "G#": "G#-B#-D#",
        "A": "A-C#-E",
        "A#": "A#-C##-E#",
        "B": "B-D#-F#",
    }
    return preferred.get(key, f"{key}-{transpose(key, 4)}-{transpose(key, 7)}")


def major_seventh_spelling_for_answer(root: str) -> str:
    key = normalize_key(root)
    preferred = {
        "C": "C-E-G-B",
        "D": "D-F#-A-C#",
        "E": "E-G#-B-D#",
        "F": "F-A-C-E",
        "G": "G-B-D-F#",
        "A": "A-C#-E-G#",
        "B": "B-D#-F#-A#",
    }
    return preferred.get(key, f"{major_triad_spelling_for_answer(key)}-{transpose(key, 11)}")


def suspended_spelling_for_answer(root: str, quality: str) -> tuple[str, str]:
    key = normalize_key(root)
    if quality == "sus2":
        return f"{key}-{transpose(key, 2)}-{transpose(key, 7)}", "root, 2nd, and perfect 5th"
    return f"{key}-{transpose(key, 5)}-{transpose(key, 7)}", "root, 4th, and perfect 5th"


def basic_chord_theory_answer_for_question(question: str) -> str | None:
    request = basic_chord_theory_request_for_question(question)
    if request is None:
        return None
    key = request.normalized_key
    quality = request.quality
    if quality == "major":
        return (
            f"A {key} major chord is {major_triad_spelling_for_answer(key)}: root, major 3rd, and perfect 5th.\n\n"
            "That is the basic chord spelling. Ask where to play it on E9 if you want fretboard positions."
        )
    if quality == "minor":
        return (
            f"A {key} minor chord is {minor_triad_spelling_for_answer(key)}: root, minor 3rd, and perfect 5th.\n\n"
            "That is the basic chord spelling. Ask where to play it on E9 if you want fretboard positions."
        )
    if quality == "major 7":
        return (
            f"{key}maj7 is {major_seventh_spelling_for_answer(key)}: root, major 3rd, perfect 5th, and major 7th. "
            f"{key} major 7 is the same chord label written out.\n\n"
            "The current deterministic E9 map does not yet claim exact major-7 positions for every grip. "
            "Start by spelling the chord tones, then ask for nearby major positions or a specific copedent context."
        )
    if quality in {"sus", "sus2", "sus4"}:
        spelling_quality = "sus4" if quality == "sus" else quality
        spelling, formula = suspended_spelling_for_answer(key, spelling_quality)
        compact_formula = "sus2 = root, 2nd, 5th" if spelling_quality == "sus2" else "sus4 = root, 4th, 5th"
        extra = (
            "sus4 is the usual default when someone just says sus."
            if quality == "sus"
            else "It leaves out the 3rd, so it wants to resolve."
        )
        return (
            f"{key}{spelling_quality} is a {key} suspended chord ({key} {spelling_quality}): {spelling}, built from {formula}.\n\n"
            f"{compact_formula}. {extra} The current deterministic E9 map does not yet claim exact suspended positions for every grip."
        )
    if quality == "dominant 7":
        return (
            f"{key}7 is {key} dominant 7: root, major 3rd, perfect 5th, and flat 7th.\n\n"
            f"For example, {key}7 is the V7 chord in the key a perfect 4th above {key}. "
            "On E9, dominant sounds can be full, partial, or rootless depending on the grip and pedal/lever setup, so give the key or position if you want a fretboard map."
        )
    if quality == "diminished":
        return (
            f"{key} diminished is built from root, flat 3rd, and flat 5th.\n\n"
            "The current deterministic E9 map does not yet claim exact diminished positions for every grip, so I would spell the tones before mapping it."
        )
    if quality == "diminished 7":
        return (
            f"{key} diminished 7 is built from root, flat 3rd, flat 5th, and double-flat 7th.\n\n"
            "That symmetrical sound is useful for passing movement, but the current deterministic E9 map does not yet claim exact diminished-7 positions for every grip."
        )
    if quality == "augmented":
        return (
            f"{key} augmented is built from root, major 3rd, and sharp 5th.\n\n"
            "The current deterministic E9 map does not yet claim exact augmented positions for every grip, so use the chord tones as the safe starting point."
        )
    return None


def chord_change_answer_for_question(question: str) -> str | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if re.search(r"^what(?:'s| is)\s+(?:a\s+)?chord\s+change$", q) or re.search(
        r"^what\s+does\s+chord\s+change\s+mean$", q
    ):
        return (
            "A chord change is when the harmony moves from one chord to another in a song or progression.\n\n"
            "Example: G to C is a chord change. A simple progression is G -> C -> D -> G.\n\n"
            "On pedal steel, you can practice chord changes by moving between fret/pedal families, but I would not show a fretboard unless you ask for a specific key or E9 position map."
        )
    if re.search(r"^what(?:'s| is)\s+(?:a\s+)?chord\s+progression$", q):
        return (
            "A chord progression is an ordered sequence of chord changes.\n\n"
            "Example: G -> C -> D -> G means the harmony starts at G, moves to C, moves to D, then resolves back to G.\n\n"
            "On E9, ask for a key if you want those changes mapped to frets, pedals, and grips."
        )
    return None
