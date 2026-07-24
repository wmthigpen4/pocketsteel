"""Stable curated-answer contracts and compact reference facts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

CuratedConfidence = Literal["curated_high", "curated_medium", "rag_only"]
IntentMode = Literal[
    "instrument_visual",
    "scope_guardrail",
    "factual_biography",
    "sensitive_personal_attribute",
    "style_how_to",
    "safety_adjacent",
    "teach_me_something",
    "movement_request",
    "progression_intro_request",
    "pocket_request",
    "lick_request",
    "vague_learning_request",
    "frustrated_learning_request",
    "everyday_context",
    "technique_coach",
    "tone_coach",
    "practice_plan",
    "fretboard_concept",
    "movement_from_position",
    "missing_context_clarifier",
    "copedent_mismatch_guardrail",
    "gear_advice",
    "gig_advice",
    "forum_wisdom",
    "lesson_navigation",
    "tab_explainer",
    "history_player_context",
    "unknown_low_confidence",
]


@dataclass(frozen=True)
class CuratedAnswer:
    intent: str
    answer: str
    confidence: CuratedConfidence
    source_url: str | None = None
    source_cards: tuple[dict[str, Any], ...] = ()


WEAK_RETRIEVAL_WARNING = "curated answer used; source support was weak"
CURATED_FACT_WEAK_WARNING = "curated fact used; source support weak"

MAJOR_CHORD_SPELLINGS: dict[str, str] = {
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
PLAYER_BIOS = {
    "buddy emmons": (
        "Buddy Emmons was one of the most influential pedal steel guitarists in the instrument’s history. "
        "He is known for brilliant E9 and C6 playing, adventurous technique, and major contributions as both a player and a builder/designer influence. "
        "For many players, his recordings and ideas are central reference points for modern pedal steel."
    ),
    "lloyd green": (
        "Lloyd Green is one of the most influential pedal steel guitarists, especially associated with classic Nashville/session steel guitar. "
        "He is known for tasteful, melodic E9 playing, precise phrasing, and major recorded work in country music."
    ),
    "paul franklin": (
        "Paul Franklin is a major modern pedal steel guitarist and session player. "
        "He is known for highly polished E9 and C6 playing, broad Nashville recording work, and a teaching influence on modern pedal-steel technique."
    ),
    "jimmy day": (
        "Jimmy Day was an important pedal steel guitarist closely associated with classic country steel. "
        "He is known for expressive phrasing, touch, and recorded work that helped define the emotional vocabulary of the instrument."
    ),
    "ralph mooney": (
        "Ralph Mooney was an influential pedal steel guitarist known for a driving, bright West Coast country sound. "
        "His playing helped shape the Bakersfield side of pedal steel and remains a reference for rhythmic, vocal-like E9 phrasing."
    ),
    "curly chalker": (
        "Curly Chalker was a major steel guitarist known especially for powerful C6 playing, jazz harmony, and big chordal command. "
        "He is often cited by players for his technical authority, musical imagination, and distinctive tone."
    ),
    "john hughey": (
        "John Hughey was a pedal steel guitarist known for lyrical, singing E9 playing and emotional ballad work. "
        "Many players associate him with smooth sustain, expressive slides, and a highly vocal approach to the instrument."
    ),
    "tom brumley": (
        "Tom Brumley was an influential pedal steel guitarist best known for clean, memorable country steel parts. "
        "His playing is often cited for tone, restraint, melodic clarity, and its influence on classic country pedal steel."
    ),
    "maurice anderson": (
        "Maurice Anderson, often known as “Reece” Anderson, was a major steel guitarist and an important builder/player figure associated with MSA. "
        "He is known for advanced musicianship, jazz-influenced steel playing, and his role in the development and visibility of MSA guitars."
    ),
    "reece anderson": (
        "Reece Anderson, also known as Maurice “Reece” Anderson, was a major steel guitarist and an important builder/player figure associated with MSA. "
        "He is known for advanced musicianship, jazz-influenced steel playing, and his role in the development and visibility of MSA guitars."
    ),
    "sarah jory": (
        "Sarah Jory is a respected steel guitarist known for strong technique, showmanship, and modern country/steel-guitar performance. "
        "She is often mentioned as an example of a high-level contemporary player with a commanding stage and recording presence."
    ),
    "doug jernigan": (
        "Doug Jernigan is a highly respected pedal steel guitarist known for speed, precision, and strong jazz and country command. "
        "Players often cite him for advanced technique, clean execution, and broad musical vocabulary."
    ),
    "weldon myrick": (
        "Weldon Myrick was an important Nashville pedal steel guitarist and session player. "
        "He is known for tasteful recorded work, strong E9 musicianship, and his place among the classic generation of country steel players."
    ),
    "hal rugg": (
        "Hal Rugg was a major pedal steel guitarist and Nashville session player. "
        "He is known for clean, authoritative playing, strong C6 and E9 musicianship, and influential work in classic country settings."
    ),
    "pete drake": (
        "Pete Drake was a steel guitarist and producer associated with major Nashville recording work. "
        "He is known for memorable session playing and for popularizing vocal/talk-box-style steel sounds in addition to conventional steel parts."
    ),
}
