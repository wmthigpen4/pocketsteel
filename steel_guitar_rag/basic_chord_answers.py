"""Small deterministic chord/theory answers for answer-quality fallback.

These helpers intentionally live outside the fretboard position engine so the
SGF evidence gate can depend on basic theory without staging unrelated
fretboard-catalog work.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from steel_guitar_rag.fretboard_examples import (
    fret_label,
    minor_triad_spelling_for_answer,
    normalize_chord_words_in_text,
    normalize_key,
    normalize_requested_root,
    open_major_fret,
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
        "dom 7": "dominant 7",
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
        "maj 7": "major 7",
        "maj7": "major 7",
        "major 7": "major 7",
        "major 7th": "major 7",
        "major seventh": "major 7",
    }
    return aliases.get(q, q)


def basic_chord_theory_request_for_question(question: str) -> BasicChordTheoryRequest | None:
    q = normalize_chord_words_in_text(re.sub(r"\s+", " ", question or "").strip().lower())
    q = re.sub(r"[?!.,;:/]+$", "", q).strip()
    q = re.sub(
        r"(?:[?!.,;:]+|\s+and)\s+where\s+(?:(?:do|can|should)\s+i\s+play|can\s+i\s+find)\s+it(?:\s+on\s+(?:the\s+)?fretboard)?$",
        "",
        q,
    ).strip()
    if not q:
        return None
    root_pattern = r"(?P<root>[a-g](?:#|b)?)"
    quality_pattern = (
        r"(?P<quality>"
        r"major\s+7th|major\s+seventh|major\s+7|maj\s+7|maj7|"
        r"sus(?:2|4)?|suspended(?:\s+[24])?|"
        r"dim(?:inished)?7?|diminished(?:\s+7)?|"
        r"aug(?:mented)?|dominant(?:\s+7)?|dom(?:\s+7)?|7th|7|"
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
    key = display_key_for_answer(root)
    preferred = {
        "C": "C-E-G",
        "C#": "C#-E#-G#",
        "Db": "Db-F-Ab",
        "D": "D-F#-A",
        "D#": "D#-F##-A#",
        "Eb": "Eb-G-Bb",
        "E": "E-G#-B",
        "F": "F-A-C",
        "F#": "F#-A#-C#",
        "Gb": "Gb-Bb-Db",
        "G": "G-B-D",
        "G#": "G#-B#-D#",
        "Ab": "Ab-C-Eb",
        "A": "A-C#-E",
        "A#": "A#-C##-E#",
        "Bb": "Bb-D-F",
        "B": "B-D#-F#",
    }
    return preferred.get(key, f"{key}-{transpose(key, 4)}-{transpose(key, 7)}")


def major_seventh_spelling_for_answer(root: str) -> str:
    key = display_key_for_answer(root)
    preferred = {
        "C": "C-E-G-B",
        "Db": "Db-F-Ab-C",
        "D": "D-F#-A-C#",
        "Eb": "Eb-G-Bb-D",
        "E": "E-G#-B-D#",
        "F": "F-A-C-E",
        "Gb": "Gb-Bb-Db-F",
        "G": "G-B-D-F#",
        "Ab": "Ab-C-Eb-G",
        "A": "A-C#-E-G#",
        "Bb": "Bb-D-F-A",
        "B": "B-D#-F#-A#",
    }
    return preferred.get(key, f"{major_triad_spelling_for_answer(key)}-{transpose(key, 11)}")


def major_seventh_position_answer(root: str) -> str:
    """Explain the exact no-pedal major-seventh grip from the saved E9 copedent."""
    key = display_key_for_answer(root)
    normalized_key = normalize_key(root)
    fret = open_major_fret(normalized_key)
    octave_fret = fret + 12
    pedal_fret = (fret + 2) % 12
    pedal_octave_fret = pedal_fret + 12
    root_note, third, fifth, seventh = major_seventh_spelling_for_answer(key).split("-")
    octave_sentence = (
        f" The same grip repeats at the {fret_label(octave_fret)}."
        if octave_fret <= 24
        else ""
    )
    return (
        f"{key}maj7 is {major_seventh_spelling_for_answer(key)}: root, major 3rd, "
        "perfect 5th, and major 7th.\n\n"
        f"On your saved E9 copedent, play strings 2-3-4-5 at the {fret_label(fret)} with no "
        f"pedals or knee levers. From high to low, those strings sound "
        f"{seventh}-{third}-{root_note}-{fifth}. That is a complete {key} major 7 ({key}maj7), not "
        f"an approximation or an ordinary {key} major grip.{octave_sentence}\n\n"
        f"Pick it low to high as strings 5-4-3-2: {fifth}-{root_note}-{third}-{seventh}.\n\n"
        f"For a root-position alternative, go to the {fret_label(pedal_fret)}, press A+B, "
        f"and play strings 9-7-6-5 low to high: {root_note}-{third}-{fifth}-{seventh}. "
        f"That complete grip repeats at the {fret_label(pedal_octave_fret)}."
    )


def dominant_seventh_spelling_for_answer(root: str) -> str:
    key = display_key_for_answer(root)
    preferred = {
        "C": "C-E-G-Bb",
        "Db": "Db-F-Ab-Cb",
        "D": "D-F#-A-C",
        "Eb": "Eb-G-Bb-Db",
        "E": "E-G#-B-D",
        "F": "F-A-C-Eb",
        "Gb": "Gb-Bb-Db-Fb",
        "G": "G-B-D-F",
        "Ab": "Ab-C-Eb-Gb",
        "A": "A-C#-E-G",
        "Bb": "Bb-D-F-Ab",
        "B": "B-D#-F#-A",
    }
    return preferred.get(key, f"{major_triad_spelling_for_answer(key)}-{transpose(key, 10)}")


def display_key_for_answer(root: str) -> str:
    requested = normalize_requested_root(root)
    if requested.endswith("b") and requested not in {"Cb", "Fb"}:
        return requested
    return normalize_key(requested)


def suspended_spelling_for_answer(root: str, quality: str) -> tuple[str, str]:
    key = normalize_key(root)
    if quality == "sus2":
        return f"{key}-{transpose(key, 2)}-{transpose(key, 7)}", "root, 2nd, and perfect 5th"
    return f"{key}-{transpose(key, 5)}-{transpose(key, 7)}", "root, 4th, and perfect 5th"


def basic_chord_theory_answer_for_question(question: str) -> str | None:
    request = basic_chord_theory_request_for_question(question)
    if request is None:
        return None
    key = display_key_for_answer(request.requested_root)
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
        return major_seventh_position_answer(key)
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
            f"{key}sus usually means {key}sus4. {key}{spelling_quality} is a {key} suspended chord ({key} {spelling_quality}): {spelling}, built from {formula}.\n\n"
            f"{compact_formula}. It has no {transpose(key, 4)}, so it is neither plain major nor minor until it resolves. "
            f"{extra} On E9, start by thinking of the {key} major position, then look for a way to replace or avoid the 3rd with the suspended tone. "
            "I can explain the chord tones now; exact E9 sus-position mapping is still limited."
        )
    if quality == "dominant 7":
        spelling = dominant_seventh_spelling_for_answer(key)
        return (
            f"{key}7, or {key} dominant 7, is {spelling}: root, major 3rd, perfect 5th, and flat 7th.\n\n"
            f"On E9, a simple starting point is to think {key} major first, then add or imply the flat 7. "
            f"The chord tones you are looking for are {spelling}. "
            f"For example, {key}7 is the V7 chord in {transpose(key, 5)}. "
            "I can show the reliable major positions first, then explain where the flat 7 lives."
        )
    if quality == "diminished":
        return (
            f"{key} diminished is built from root, flat 3rd, and flat 5th.\n\n"
            "A clean exact E9 grip depends on which strings and pedals/levers you want to use, so I would spell the tones before mapping it."
        )
    if quality == "diminished 7":
        return (
            f"{key} diminished 7 is built from root, flat 3rd, flat 5th, and double-flat 7th.\n\n"
            "That symmetrical sound is useful for passing movement, but a clean exact E9 grip depends on which strings and pedals/levers you want to use."
        )
    if quality == "augmented":
        return (
            f"{key} augmented is built from root, major 3rd, and sharp 5th.\n\n"
            "A clean exact E9 grip depends on which strings and pedals/levers you want to use, so use the chord tones as the safe starting point."
        )
    return None


def sus_chord_usage_answer_for_question(question: str) -> str | None:
    q = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if not re.search(r"\bwhen\b.*\b(?:use|play)\b.*\bsus(?:pended)?\s+chord\b", q):
        return None
    return (
        "Use a sus chord when you want tension that wants to resolve.\n\n"
        "A sus4 replaces the 3rd with the 4th, so it sounds suspended until it resolves back to the major chord. "
        "For example, Gsus4 is G-C-D; resolving it to G major puts the B back in the chord.\n\n"
        "On pedal steel, that sound is useful on a held chord, an intro ending, a gospel-style lift, or a country phrase where you want the chord to lean for a moment before settling. "
        "Think of it as a musical “not yet” that resolves into the plain major chord."
    )


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
