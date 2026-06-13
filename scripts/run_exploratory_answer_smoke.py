#!/usr/bin/env python3
"""Run exploratory local answer smoke checks against /api/answer."""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pocketsteel.fretboard_examples import (  # noqa: E402
    e_lower_grip_request_for_question,
    functional_pocket_request_for_question,
    get_e9_major_chord_positions,
    major_chord_location_request_for_question,
)
from pocketsteel.curated_source_registry import is_approved_curated_url  # noqa: E402


DEFAULT_API_URL = "http://127.0.0.1:8783/api/answer"
DEFAULT_OUTPUT = Path("corpus-private/reports/exploratory-answer-smoke.md")
DEFAULT_JSON_OUTPUT = Path("corpus-private/reports/exploratory-answer-smoke.json")
DEFAULT_ACCESS_ROLE = "beta_user"
DEFAULT_TOP_K = 6

Severity = Literal["warn", "fail"]
Outcome = Literal["pass", "warn", "fail"]

RAW_SGF_FRAGMENT_RE = re.compile(
    r"\b(?:Top Hi All|Thanks Nick|Does anyone know|Has anyone compared|I am looking for tablature|"
    r"Bill Lowe\s*/\s*\d{1,2}\s+\w+\s+\d{4}|RKL\s+fully\s+engaged|B9\s+chord|"
    r"You either tune it|I've played it this way|starting with the first string|G#>F#|"
    r"B's\s+to\s+Bb|with\s+your\s+middle\s+finger)\b",
    re.I,
)
MID_SENTENCE_START_RE = re.compile(r"^\s*(?:and|or|but|because|with|from|so|then|also|which|that|this)\b", re.I)
CONTACT_JUNK_RE = re.compile(
    r"\b(?:PayPal|sp=sharing|e-?mail|email|order\s+(?:form|page|link|online|through)|contact\s+me|"
    r"https?://\S+|www\.)\b|\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
    re.I,
)
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
INTERNAL_RETRIEVAL_RE = re.compile(r"\b(?:retrieved material|source cards|Useful distilled points|Useful source-backed points)\b", re.I)
WEAK_SOURCE_RE = re.compile(r"\b(?:source support was weak|source support is weak|curated answer used;\s*source support was weak)\b", re.I)
KEYED_MAJOR_RE = re.compile(r"\b(?P<key>[A-G](?:#|b)?)\s+(?:major|chord)\b", re.I)
DOMINANT_RE = re.compile(r"\b(?P<key>[A-G](?:#|b)?)(?:7|9)\b", re.I)
DOMINANT_CONTEXT_RE = re.compile(r"\b(?:I[- ]?IV[- ]?V|1[- ]?4[- ]?5|dominant|V\s+chord|key\s+of|progression|turnaround)\b", re.I)
PRIVATE_PROFILE_RE = re.compile(r"\b(?:your saved 10-string E9 profile|your private|your E9 profile|your setup|my common grips)\b", re.I)
MINOR_FUNCTION_RE = re.compile(
    r"\b(?:key\s+of\s+G\b.*\b(?:6m|vi)\s+chord\b|show\s+me\s+the\s+vi\s+chord\s+in\s+G\b|where\s+is\s+Em\s+on\s+E9\b)",
    re.I,
)
BEGINNER_MAJOR_CHORD_CONCEPT_RE = re.compile(
    r"\b(?:what(?:'s|\s+is)\s+(?:an?\s+)?(?P<what_key>[A-G](?:#|b)?)\s+chord(?:\s+even)?\s+mean|"
    r"what\s+does\s+(?:an?\s+)?(?P<does_key>[A-G](?:#|b)?)\s+chord\s+mean|"
    r"what\s+notes\s+are\s+in\s+(?:an?\s+)?(?P<notes_key>[A-G](?:#|b)?)\s+chord|"
    r"where\s+is\s+(?:an?\s+)?(?P<where_key>[A-G](?:#|b)?)\s+chord|"
    r"how\s+do\s+i\s+play\s+(?:an?\s+)?(?P<play_key>[A-G](?:#|b)?)\s+on\s+E9)\b",
    re.I,
)
BEGINNER_MINOR_CHORD_CONCEPT_RE = re.compile(
    r"\bwhat\s+makes\s+(?:an?\s+)?(?P<key>[A-G](?:#|b)?)\s+minor\s+chord\s+minor\b",
    re.I,
)
E_LOWER_578_B9_RE = re.compile(r"\b5[- ]7[- ]8\b.*\bE\s+lowered\b.*\bB9\s+pocket\b|\bB9\s+pocket\b.*\b5[- ]7[- ]8\b", re.I)
OBJECT_OBJECT_RE = re.compile(r"\[object Object\]", re.I)
PRACTICAL_ADVICE_QUESTION_RE = re.compile(
    r"\b(?:power\b.*\bStroboPlus\b|StroboPlus\b.*\b(?:gig|batter(?:y|ies)|power)|"
    r"broke\s+a\s+string|string\s+keeps\s+breaking|breaking\s+strings?\s+on\s+stage|"
    r"emergency\s+gig\s+kit|amp\s+hums?\b.*\bchanger|delay\s+go\s+before|"
    r"battery-powered\s+tuners?\s+live)\b",
    re.I,
)
ADVICE_ACTION_RE = re.compile(
    r"\b(?:check|carry|pack|bring|replace|swap|test|use|power|plug|charge|keep|change|"
    r"put|place|run|isolate|try|do\s+next|first|before\s+the\s+gig|during\s+the\s+show)\b",
    re.I,
)
ADVICE_FRAGMENT_RE = re.compile(
    r"\b(?:Has that happened to anyone else|What do players say|Somebody said|I remember when|"
    r"one time|years ago|on stage I|at a gig I|forum post|thread says|"
    r"Bill Lowe\s*/\s*\d{1,2}\s+\w+\s+\d{4})\b",
    re.I,
)
ADVICE_JOKE_ANECDOTE_RE = re.compile(
    r"\b(?:funny|joke|laugh|embarrass(?:ed|ing)?|blood|bleed(?:ing)?|gore|injur(?:y|ed)|"
    r"cut my finger|horror story|war story|everybody laughed)\b",
    re.I,
)
ACTION_RE = re.compile(
    r"\b(?:try|practice|play|check|test|listen|move|compare|start|use|repeat|isolate|adjust|"
    r"block|pick|fret|strings?|pedals?|levers?|grips?)\b",
    re.I,
)
QUOTE_LINE_RE = re.compile(r"(?m)^\s*(?:>|\"|').{12,}$")
CANONICAL_GRIP_ORDER = ("3-4-5", "4-5-6", "5-6-8", "5-7-8", "6-8-10")
CANONICAL_GRIP_INDEX = {grip: index for index, grip in enumerate(CANONICAL_GRIP_ORDER)}

STOPWORDS = {
    "about",
    "after",
    "again",
    "all",
    "and",
    "are",
    "can",
    "does",
    "from",
    "give",
    "have",
    "how",
    "major",
    "me",
    "play",
    "should",
    "show",
    "the",
    "this",
    "what",
    "where",
    "why",
    "with",
}


@dataclass(frozen=True)
class QuestionCase:
    id: str
    category: str
    question: str


@dataclass(frozen=True)
class Finding:
    severity: Severity
    key: str
    message: str


@dataclass
class SmokeResult:
    id: str
    category: str
    question: str
    status_code: int
    answer: str
    warnings: list[str]
    source_titles: list[str]
    source_excerpts: list[str]
    source_urls: list[str]
    source_systems: list[str]
    fretboard_exists: bool
    section_titles: list[str]
    findings: list[Finding] = field(default_factory=list)

    @property
    def outcome(self) -> Outcome:
        if any(finding.severity == "fail" for finding in self.findings):
            return "fail"
        if self.findings:
            return "warn"
        return "pass"


def chord_position_variants() -> list[QuestionCase]:
    roots = ("G", "A", "B", "C", "C#", "F#", "Bb", "B#")
    cases: list[QuestionCase] = []
    index = 1
    for root in roots:
        article = "an" if root[:1] in {"A", "E", "F"} else "a"
        for question in (
            f"Where can I play {article} {root} chord?",
            f"Where all can I play {article} {root} chord?",
            f"How do I play {article} {root}?",
            f"How do I play {article} {root} chord?",
            f"How do I make {article} {root} chord?",
            f"Show me {root} positions.",
            f"Where is {root} major?",
            f"What frets give me {root}?",
        ):
            cases.append(QuestionCase(f"A{index:03d}", "chord_position_fretboard", question))
            index += 1
    return cases


def built_in_questions() -> list[QuestionCase]:
    cases = chord_position_variants()
    beginner_concepts = [
        QuestionCase("BC001", "chord_position_fretboard", "What's a G chord even mean?"),
        QuestionCase("BC002", "chord_position_fretboard", "What does a C chord mean?"),
        QuestionCase("BC003", "chord_position_fretboard", "What notes are in a D chord?"),
        QuestionCase("BC004", "chord_position_fretboard", "Where is a G chord?"),
        QuestionCase("BC005", "chord_position_fretboard", "How do I play G on E9?"),
        QuestionCase("BC006", "deterministic_pocket_fretboard", "What makes an E minor chord minor?"),
        QuestionCase("BC007", "deterministic_pocket_fretboard", "What is the vi chord in G?"),
    ]
    cases.extend(beginner_concepts)
    routing_escapes = [
        QuestionCase("R001", "chord_position_fretboard", "Where are some places to play C chords?"),
        QuestionCase("R002", "chord_position_fretboard", "Where can I play C chord?"),
        QuestionCase("R003", "chord_position_fretboard", "How do I plan an F chord?"),
        QuestionCase("R004", "chord_position_fretboard", "How do I play an F chord?"),
        QuestionCase("R005", "chord_position_fretboard", "How do I make an F chord?"),
        QuestionCase("R006", "deterministic_pocket_fretboard", "I am in the key of G. Where can I play a 6m chord?"),
        QuestionCase("R007", "deterministic_pocket_fretboard", "Show me the vi chord in G."),
        QuestionCase("R008", "deterministic_pocket_fretboard", "Where is Em on E9?"),
        QuestionCase("R009", "deterministic_pocket_fretboard", "What does 5-7-8 with E lowered give me at the 3rd fret?"),
        QuestionCase("R010", "deterministic_pocket_fretboard", "Is 5-7-8 with E lowered a B9 pocket?"),
        QuestionCase("R011", "deterministic_pocket_fretboard", "Show me V chord pockets in A."),
    ]
    cases.extend(routing_escapes)
    groups: dict[str, list[str]] = {
        "progressions": [
            "Show me a 1-4-5 in G.",
            "Show me a 1-4-5 in C.",
            "How do I move from G to C to D?",
            "Show me nearby I IV V positions.",
            "Show me a 1-4-5 in A.",
            "How do I connect A to D to E on E9?",
            "Where are close I IV V sounds around the 5th fret?",
            "How do I practice G C D without jumping all over the neck?",
            "Show me a simple I IV V pocket.",
            "What is the V chord position from G open?",
            "How do I move from C to F to G?",
            "Show me nearby positions for A D E.",
        ],
        "grips": [
            "Show me common grips for G.",
            "What are 4-5-6 grips?",
            "What can I do with strings 5-6-8?",
            "Where are my 6-8-10 grips?",
            "What are common E9 major grips?",
            "How should I use strings 3-4-5?",
            "How do 4-5-6 and 5-6-8 feel different?",
            "What grips should I practice tonight?",
            "Show me grips around the 3rd fret.",
            "What is a good beginner grip set?",
            "How do I move grips without losing intonation?",
            "What strings make easy major triads?",
        ],
        "personal_setup": [
            "What is my copedent?",
            "What does my RKL do?",
            "What does my RKR do?",
            "What does my F lever do?",
            "What does A+F do on my guitar?",
            "What are my common grips?",
            "Which knee levers do I have?",
            "Show me my E9 setup.",
            "What pedals are on my setup?",
            "How should I practice my RKL?",
            "What does my E-lower do?",
            "List my levers.",
        ],
        "practice_technique": [
            "Teach me about pockets.",
            "What are good B+C pedal exercises?",
            "Give me a plan for learning B+C.",
            "Why do some people wear a 4th finger pick?",
            "How should I practice blocking?",
            "What is bar slanting?",
            "What should I practice tonight?",
            "Give me a 20-minute E9 practice plan.",
            "How should I practice bar control?",
            "How should I practice volume pedal?",
            "Help me sound less mechanical.",
            "How do I soften my attack?",
            "My pick attack sounds too sharp. What should I practice?",
            "How do I play with more feeling?",
            "How do I practice playing behind a singer?",
            "What should I work on if I am new to pedal steel?",
            "How do I practice intonation?",
            "How do I make my fills less busy?",
            "What should I practice if my bar movement is noisy?",
            "How do I use B+C in a musical way?",
        ],
        "gear_vendor_troubleshooting": [
            "What's a StroboPlus?",
            "What’s a StroboPlus?",
            "How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.",
            "I broke a string during a show. Has that happened to anyone else? What do people do?",
            "My 3rd string keeps breaking at gigs. What should I carry?",
            "What should be in a pedal steel emergency gig kit?",
            "My amp hums until I touch the changer. What should I check first?",
            "Should delay go before my volume pedal or after it?",
            "What do players say about breaking strings on stage?",
            "Do steel players use battery-powered tuners live?",
            "Where can I buy a slide bar?",
            "Why does my amp buzz?",
            "What is a good volume pedal?",
            "How do I diagnose hum that changes when I touch the changer?",
            "Why does my amp buzz at idle?",
            "Where can I buy a steel bar?",
            "What steel bar should I buy?",
            "What is a BJS bar?",
            "What is a good tuner for pedal steel?",
            "What is the Sarno Black Box?",
            "Is a Sarno Black Box useful for steel guitar?",
            "What is a Goodrich volume pedal?",
            "What is a Telonics volume pedal?",
            "What pickup should I use for E9?",
            "What are common Fender Steel King settings?",
            "Should I use a Peavey Nashville 112?",
            "Why does touching the strings reduce buzz?",
            "How do I fix a pedal that will not return?",
            "What kind of oil is good for my changer?",
            "Should I use WD-40 on my changer?",
            "How do I clean my pedal steel?",
        ],
        "player_history": [
            "Why was Jeff Newman famous?",
            "Who was Buddy Emmons?",
            "Why do people talk about Lloyd Green?",
            "Who is Paul Franklin?",
            "Who was Jimmy Day?",
            "Who was Ralph Mooney?",
            "Who is Sarah Jory?",
            "Who was Curly Chalker?",
            "Who is Doug Jernigan?",
            "Who was John Hughey?",
            "Who was Pete Drake?",
            "Who are the most influential E9 players?",
        ],
        "guardrail_song_tab": [
            "Give me tab for a current copyrighted song.",
            "Can you write the solo from Together Again?",
            "Help me understand how to approach a song without copying tab.",
            "Can you give me tab for Panhandle Rag?",
            "Give me the full lyrics to Crazy.",
            "How should I approach playing Together Again on E9?",
            "Can you write me an original E9 lick in the style of a slow country ballad?",
            "What chord progression is common in Amazing Grace?",
            "Can you give me tablature for a random song?",
            "How do I learn a song by ear on E9?",
            "Can you explain the style of a slow country ballad?",
            "Give me a safe public-domain E9 exercise.",
        ],
    }
    for category, questions in groups.items():
        for index, question in enumerate(questions, 1):
            prefix = {
                "progressions": "B",
                "grips": "C",
                "personal_setup": "D",
                "practice_technique": "E",
                "gear_vendor_troubleshooting": "F",
                "player_history": "G",
                "guardrail_song_tab": "H",
            }[category]
            cases.append(QuestionCase(f"{prefix}{index:03d}", category, question))
    return cases


def excerpt(text: str, width: int = 240) -> str:
    return textwrap.shorten(re.sub(r"\s+", " ", text or "").strip(), width=width, placeholder=" ...")


def add_finding(findings: list[Finding], severity: Severity, key: str, message: str) -> None:
    findings.append(Finding(severity=severity, key=key, message=message))


def post_answer(api_url: str, question: str, *, timeout: float, top_k: int, access_role: str) -> tuple[int, dict[str, Any]]:
    payload = json.dumps({"question": question, "mode": "ask", "topK": top_k}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Steel-Rag-Dev-Access-Role": access_role,
    }
    request = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}
    except (TimeoutError, urllib.error.URLError) as exc:
        return 0, {"error": str(exc)}


def normalize_terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9#]+", (text or "").lower())
        if len(word) > 2 and word not in STOPWORDS
    }


def source_fields(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str], list[str], list[str]]:
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    source_dicts = [source for source in sources if isinstance(source, dict)]
    titles = [str(source.get("title") or source.get("thread_title") or "").strip() for source in source_dicts]
    excerpts = [str(source.get("excerpt") or "").strip() for source in source_dicts]
    urls = [str(source.get("url") or source.get("thread_url") or "").strip() for source in source_dicts]
    systems = [str(source.get("source_system") or source.get("sourceSystem") or "").strip() for source in source_dicts]
    return source_dicts, titles, excerpts, urls, systems


def section_titles(payload: dict[str, Any]) -> list[str]:
    sections = payload.get("sections") if isinstance(payload.get("sections"), list) else []
    return [str(section.get("title") or "").strip() for section in sections if isinstance(section, dict)]


def fretboard_exists(payload: dict[str, Any]) -> bool:
    fretboard = payload.get("fretboard")
    if not isinstance(fretboard, dict):
        return False
    positions = fretboard.get("positions")
    return isinstance(positions, list) and bool(positions)


def fretboard_positions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fretboard = payload.get("fretboard")
    if not isinstance(fretboard, dict):
        return []
    positions = fretboard.get("positions")
    if not isinstance(positions, list):
        return []
    return [position for position in positions if isinstance(position, dict)]


def expected_chord_frets(question: str) -> list[int]:
    request = major_chord_location_request_for_question(question)
    if request is None:
        request = beginner_major_chord_concept_request(question)
    if request is None:
        return []
    return [
        position["fret"]
        for position in get_e9_major_chord_positions(request.normalized_key)
        if position["role"] in {"Open position", "A+F position", "A+B position"}
    ]


def answer_has_frets(answer: str, frets: list[int]) -> bool:
    return all(re.search(rf"\b{fret}(?:st|nd|rd|th)?\s+fret\b", answer, re.I) for fret in frets)


def is_minor_function_question(question: str) -> bool:
    return bool(MINOR_FUNCTION_RE.search(question or "") or BEGINNER_MINOR_CHORD_CONCEPT_RE.search(question or ""))


def beginner_major_chord_concept_request(question: str):
    match = BEGINNER_MAJOR_CHORD_CONCEPT_RE.search(question or "")
    if not match:
        return None
    key = next((value for value in match.groupdict().values() if value), "")
    if not key:
        return None
    try:
        return major_chord_location_request_for_question(f"Where can I play a {key} chord?")
    except ValueError:
        return None


def is_e_lower_578_question(question: str) -> bool:
    if E_LOWER_578_B9_RE.search(question or ""):
        return True
    request = e_lower_grip_request_for_question(question)
    return bool(request and request.strings == (5, 7, 8))


def is_functional_pocket_question(question: str) -> bool:
    return functional_pocket_request_for_question(question) is not None


def is_visualizable_deterministic_question(question: str) -> bool:
    return bool(
        expected_chord_frets(question)
        or is_minor_function_question(question)
        or is_e_lower_578_question(question)
        or is_functional_pocket_question(question)
    )


def is_deterministic_source_free_question(question: str) -> bool:
    return is_visualizable_deterministic_question(question)


def answer_mentions_expected_minor_function(answer: str) -> bool:
    return bool(re.search(r"\b(?:E\s+minor|Em)\b", answer or "", re.I))


def answer_has_beginner_chord_explanation(answer: str, question: str) -> bool:
    request = beginner_major_chord_concept_request(question)
    if request is not None:
        key = re.escape(request.normalized_key)
        if request.normalized_key == "G":
            tones = (r"\bG\b", r"\bB\b", r"\bD\b")
        elif request.normalized_key == "C":
            tones = (r"\bC\b", r"\bE\b", r"\bG\b")
        elif request.normalized_key == "D":
            tones = (r"\bD\b", r"(?<![A-G#b])F#(?![A-G#b])", r"\bA\b")
        else:
            tones = (rf"\b{key}\b",)
        return (
            all(re.search(tone, answer or "", re.I) for tone in tones)
            and bool(re.search(r"\b(?:root|1)\b", answer or "", re.I))
            and bool(re.search(r"\b(?:major\s+)?(?:third|3rd|3)\b", answer or "", re.I))
            and bool(re.search(r"\b(?:perfect\s+)?(?:fifth|5th|5)\b", answer or "", re.I))
            and bool(re.search(r"\b(?:E9|steel|fret|pedal|lever|grip)\b", answer or "", re.I))
        )
    if BEGINNER_MINOR_CHORD_CONCEPT_RE.search(question or ""):
        return (
            bool(re.search(r"\bE\b.*\bG\b.*\bB\b|\bE-G-B\b", answer or "", re.I | re.S))
            and bool(re.search(r"\bminor\b", answer or "", re.I))
            and bool(re.search(r"\b(?:flat|lowered)\s+(?:the\s+)?(?:third|3rd|3)\b|\bb3\b|\bminor\s+(?:third|3rd|3)\b", answer or "", re.I))
            and bool(re.search(r"\b(?:E9|steel|fret|pedal|lever|grip)\b", answer or "", re.I))
        )
    return True


def answer_mentions_expected_v_pocket(answer: str, question: str) -> bool:
    request = functional_pocket_request_for_question(question)
    if request is None:
        return True
    target = re.escape(request.target_root)
    return bool(
        re.search(rf"\b{target}\s+(?:major|dominant|V(?:\s+chord)?|pockets?)\b", answer or "", re.I)
        or re.search(rf"\bV\s+chord\s+is\s+{target}\b", answer or "", re.I)
    )


def answer_handles_e_lower_578(answer: str, question: str) -> bool:
    if not is_e_lower_578_question(question):
        return True
    if E_LOWER_578_B9_RE.search(question or ""):
        return bool(
            re.search(r"\bnot\s+(?:a\s+)?(?:full\s+)?B9\b|\bnot\s+B9\b", answer or "", re.I)
            and re.search(r"\bD\s+major\b", answer or "", re.I)
            and re.search(r"\brootless\b|\bomits?\s+the\s+B\s+root\b", answer or "", re.I)
        )
    return bool(re.search(r"\bD\s+major\b", answer or "", re.I))


def fretboard_has_bad_grip_order(payload: dict[str, Any]) -> bool:
    previous_by_group: dict[tuple[object, ...], int] = {}
    for position in fretboard_positions(payload):
        grip = str(position.get("grip") or "")
        if grip not in CANONICAL_GRIP_INDEX:
            continue
        group = (
            position.get("family"),
            position.get("fret"),
            tuple(position.get("pedals") or []),
            tuple(position.get("levers") or []),
        )
        current = CANONICAL_GRIP_INDEX[grip]
        previous = previous_by_group.get(group)
        if previous is not None and current < previous:
            return True
        previous_by_group[group] = current
    return False


def payload_contains_object_object(payload: dict[str, Any]) -> bool:
    return bool(OBJECT_OBJECT_RE.search(json.dumps(payload, ensure_ascii=False, default=str)))


def source_is_sgf(url: str, title: str, system: str) -> bool:
    haystack = f"{url} {title} {system}".lower()
    return bool(
        "steelguitarforum.com" in haystack
        or "steel guitar forum" in haystack
        or "sgf_" in haystack
        or "phpbb" in haystack
        or "ubb" in haystack
    )


def question_mentions_private_profile(question: str) -> bool:
    return bool(
        re.search(
            r"\bmy\s+(?:e9\s+)?(?:copedent|setup|rkl|rkr|f\s+lever|e-lower|guitar|levers?|pedals?(?!\s+steel)|common grips?)\b",
            question,
            re.I,
        )
    )


def category_allows_fretboard(category: str) -> bool:
    return category in {"chord_position_fretboard", "deterministic_pocket_fretboard", "progressions", "grips"}


def category_needs_teaching_value(category: str) -> bool:
    return category not in {"player_history"}


def chord_answer_mentions_unrelated(answer: str, question: str) -> bool:
    request = major_chord_location_request_for_question(question)
    if request is None:
        return False
    requested = request.normalized_key.upper()
    dominant_allowed = bool(DOMINANT_CONTEXT_RE.search(question))
    for match in KEYED_MAJOR_RE.finditer(answer):
        mentioned = match.group("key").upper()
        if mentioned != requested:
            return True
    if not dominant_allowed:
        for match in DOMINANT_RE.finditer(answer):
            if match.group(0).upper() != "E9":
                return True
    return False


def answer_mostly_fragments(answer: str) -> bool:
    stripped = (answer or "").strip()
    if len(stripped) < 80:
        return False
    if stripped.count("|") >= 8 and not RAW_SGF_FRAGMENT_RE.search(stripped):
        return False
    quote_lines = QUOTE_LINE_RE.findall(stripped)
    if len(quote_lines) >= 3:
        return True
    sentence_count = len(re.findall(r"[.!?](?:\s|$)", stripped))
    newline_chunks = [chunk for chunk in stripped.splitlines() if chunk.strip()]
    return sentence_count <= 1 and len(newline_chunks) >= 4


def is_practical_advice_question(question: str, category: str) -> bool:
    return bool(
        PRACTICAL_ADVICE_QUESTION_RE.search(question or "")
        or (
            category == "gear_vendor_troubleshooting"
            and re.search(r"\b(?:what should i|what do people do|what should i check|where should|should delay|what should be in)\b", question, re.I)
        )
    )


def question_needs_beginner_chord_explanation(question: str) -> bool:
    return bool(
        re.search(r"\b(?:what(?:'s|\s+is).+chord(?:\s+even)?\s+mean|what\s+does.+chord\s+mean|what\s+notes\s+are\s+in)\b", question or "", re.I)
        or BEGINNER_MINOR_CHORD_CONCEPT_RE.search(question or "")
    )


def advice_answer_has_practical_steps(answer: str) -> bool:
    if not ADVICE_ACTION_RE.search(answer or ""):
        return False
    return bool(
        re.search(
            r"\b(?:step|first|check|carry|pack|bring|spare|string|battery|power|adapter|cable|tuner|"
            r"volume pedal|delay|signal chain|ground|hum|kit|show|gig)\b",
            answer or "",
            re.I,
        )
    )


def advice_answer_addresses_question(answer: str, question: str) -> bool:
    text = answer or ""
    q = question or ""
    if re.search(r"\bStroboPlus\b.*\b(?:gig|batter(?:y|ies)|power)|\bpower\b.*\bStroboPlus\b", q, re.I):
        return bool(re.search(r"\b(?:batter(?:y|ies)|adapter|USB|power\s+supply|charger|outlet|external\s+power|fresh\s+batteries)\b", text, re.I))
    if re.search(r"\bbattery-powered\s+tuners?\s+live\b", q, re.I):
        return bool(re.search(r"\b(?:battery-powered|batter(?:y|ies)|adapter|USB|power|live|gig)\b", text, re.I))
    if re.search(r"\bbroke\s+a\s+string|string\s+keeps\s+breaking|breaking\s+strings?\s+on\s+stage\b", q, re.I):
        return bool(re.search(r"\b(?:spare\s+strings?|replace|carry|winder|cutters?|3rd\s+string|changer|finish\s+the\s+tune)\b", text, re.I))
    if re.search(r"\bemergency\s+gig\s+kit\b", q, re.I):
        return bool(re.search(r"\b(?:spare\s+strings?|winder|cutters?|bar|picks?|battery|cable|tuner|hex|kit)\b", text, re.I))
    if re.search(r"\bamp\s+hums?\b.*\bchanger\b", q, re.I):
        return bool(re.search(r"\b(?:ground|cable|outlet|amp|changer|touch|qualified|tech|unplug|isolate)\b", text, re.I))
    if re.search(r"\bdelay\s+go\s+before\b", q, re.I):
        return bool(re.search(r"\b(?:before|after|volume\s+pedal|delay|signal\s+chain|effects\s+loop)\b", text, re.I))
    return True


def advice_answer_is_background_only(answer: str) -> bool:
    text = answer or ""
    has_background = bool(re.search(r"\b(?:is a|is an|StroboPlus is|tuner is|delay is|volume pedal is)\b", text, re.I))
    return has_background and not advice_answer_has_practical_steps(text)


def evaluate_response(case: QuestionCase, status_code: int, payload: dict[str, Any]) -> SmokeResult:
    answer = str(payload.get("answer") or payload.get("error") or "")
    warnings = [str(warning) for warning in (payload.get("warnings") or [])]
    sources, titles, excerpts, urls, systems = source_fields(payload)
    has_fretboard = fretboard_exists(payload)
    findings: list[Finding] = []

    if status_code != 200:
        add_finding(findings, "fail", "http_error", f"HTTP status {status_code}")
    if not answer.strip():
        add_finding(findings, "fail", "empty_answer", "answer is empty")
    if status_code != 200 or not answer.strip():
        return SmokeResult(
            id=case.id,
            category=case.category,
            question=case.question,
            status_code=status_code,
            answer=answer,
            warnings=warnings,
            source_titles=titles,
            source_excerpts=excerpts,
            source_urls=urls,
            source_systems=systems,
            fretboard_exists=has_fretboard,
            section_titles=section_titles(payload),
            findings=findings,
        )
    if RAW_SGF_FRAGMENT_RE.search(answer):
        add_finding(findings, "fail", "raw_sgf_fragment_language", "answer contains raw SGF/forum fragment language")
    if MID_SENTENCE_START_RE.search(answer):
        add_finding(findings, "warn", "answer_starts_mid_sentence", "answer appears to start mid-sentence")
    if answer_mostly_fragments(answer):
        add_finding(findings, "fail", "answer_mostly_quotes_or_fragments", "answer looks mostly like quotes or fragments")
    if answer_contains_contact_or_unapproved_link_junk(answer):
        add_finding(findings, "fail", "contact_order_link_junk", "answer contains PayPal/contact/order/link junk")
    if INTERNAL_RETRIEVAL_RE.search(answer):
        add_finding(findings, "fail", "internal_retrieval_language", "answer exposes retrieved-material/source-card language")
    if WEAK_SOURCE_RE.search(answer) or any(WEAK_SOURCE_RE.search(warning) for warning in warnings):
        add_finding(findings, "fail", "visible_weak_source_language", "answer or warning visibly says source support was weak")
        add_finding(findings, "fail", "weak_source_leakage", "answer or warning visibly says source support was weak")
    if payload_contains_object_object(payload):
        add_finding(findings, "fail", "object_object_rendering_leakage", "answer payload contains [object Object]")
        add_finding(findings, "fail", "object_object_rendering", "answer payload contains [object Object]")

    frets = expected_chord_frets(case.question)
    is_chord_position = bool(frets)
    if is_chord_position:
        if not has_fretboard:
            add_finding(findings, "fail", "chord_position_missing_fretboard", "chord-position question lacks response.fretboard")
        if sources:
            add_finding(findings, "fail", "deterministic_answer_has_sources", "deterministic chord-position answer returned source cards")
        if any(source_is_sgf(url, title, system) for url, title, system in zip(urls, titles, systems)):
            add_finding(findings, "fail", "chord_position_has_sgf_source_cards", "deterministic chord-position answer returned SGF source cards")
        if not answer_has_frets(answer, frets):
            add_finding(findings, "fail", "chord_position_missing_expected_frets", f"answer lacks expected frets {frets}")
        if chord_answer_mentions_unrelated(answer, case.question):
            add_finding(findings, "fail", "chord_position_unrelated_chords_or_keys", "answer mentions unrelated chord/key material")
        if question_needs_beginner_chord_explanation(case.question) and beginner_major_chord_concept_request(case.question) and not answer_has_beginner_chord_explanation(answer, case.question):
            add_finding(findings, "fail", "beginner_chord_concept_router_escape", "beginner chord concept answer lacks chord tones, interval explanation, or steel-specific application")
    elif is_visualizable_deterministic_question(case.question):
        if not has_fretboard:
            add_finding(findings, "fail", "deterministic_visual_missing_fretboard", "visualizable deterministic chord/pocket/function question lacks response.fretboard")
        if is_deterministic_source_free_question(case.question) and sources:
            add_finding(findings, "fail", "deterministic_answer_has_sources", "deterministic chord/pocket/function answer returned source cards")
        if is_minor_function_question(case.question) and not answer_mentions_expected_minor_function(answer):
            add_finding(findings, "fail", "wrong_function_routing", "G vi/6m or Em question did not resolve to E minor")
        if is_functional_pocket_question(case.question) and not answer_mentions_expected_v_pocket(answer, case.question):
            add_finding(findings, "fail", "wrong_function_routing", "V-pocket question did not resolve to the requested V chord")
        if is_e_lower_578_question(case.question) and not answer_handles_e_lower_578(answer, case.question):
            add_finding(findings, "fail", "wrong_function_routing", "5-7-8 E-lower answer did not match pitch-engine classification")
        if question_needs_beginner_chord_explanation(case.question) and BEGINNER_MINOR_CHORD_CONCEPT_RE.search(case.question or "") and not answer_has_beginner_chord_explanation(answer, case.question):
            add_finding(findings, "fail", "beginner_chord_concept_router_escape", "beginner minor chord concept answer lacks chord tones, interval explanation, or steel-specific application")
    elif has_fretboard and not category_allows_fretboard(case.category):
        add_finding(findings, "fail", "non_position_question_has_fretboard", "non-position question returned a fretboard payload")

    if is_practical_advice_question(case.question, case.category):
        first = excerpt(answer, width=140)
        if (
            MID_SENTENCE_START_RE.search(answer)
            or first.startswith("-")
            or not advice_answer_has_practical_steps(answer)
            or not advice_answer_addresses_question(answer, case.question)
        ):
            add_finding(findings, "fail", "advice_question_must_answer_directly", "practical advice answer lacks direct actionable guidance")
        if RAW_SGF_FRAGMENT_RE.search(answer) or answer_mostly_fragments(answer) or ADVICE_FRAGMENT_RE.search(answer) or first.startswith("-"):
            add_finding(findings, "fail", "advice_question_raw_fragment_failure", "practical advice answer appears to be raw fragments or source snippets")
        if ADVICE_JOKE_ANECDOTE_RE.search(answer):
            add_finding(findings, "fail", "advice_question_joke_anecdote_failure", "practical advice answer leans on jokes, anecdotes, injury, or embarrassment stories")
        if advice_answer_is_background_only(answer):
            add_finding(findings, "fail", "gear_question_background_only_failure", "gear/gig advice answer gives background without practical next steps")

    if has_fretboard and fretboard_has_bad_grip_order(payload):
        add_finding(findings, "fail", "fretboard_grip_order_wrong", "fretboard payload exposes grips out of canonical order")

    private_question = question_mentions_private_profile(case.question)
    private_source_count = sum(1 for source in sources if str(source.get("visibility") or "").lower() == "private")
    if private_question and not private_source_count and not PRIVATE_PROFILE_RE.search(answer):
        add_finding(findings, "fail", "private_profile_ignored", "question asks about 'my' setup but answer did not use private profile evidence")
    if private_question and re.search(r"\b(?:copedent|setup|levers?|pedals?)\b", case.question, re.I):
        if not (re.search(r"\bE9\b", answer, re.I) and re.search(r"\b(?:RKL|RKR|F\s+lever|A\+B|A\+F|pedals?|levers?)\b", answer, re.I)):
            add_finding(findings, "fail", "missing_copedent_facts", "personal setup answer is missing concrete copedent facts")
    if not private_question and (private_source_count or PRIVATE_PROFILE_RE.search(answer)):
        add_finding(findings, "fail", "generic_answer_leaked_private_profile", "generic question pulled private setup facts")

    if category_needs_teaching_value(case.category) and len(answer.strip()) >= 40 and not ACTION_RE.search(answer):
        add_finding(findings, "warn", "low_teaching_value", "answer has low actionable teaching value")

    question_terms = normalize_terms(case.question)
    for index, source_excerpt in enumerate(excerpts, 1):
        if source_excerpt and len(source_excerpt) < 45:
            add_finding(findings, "warn", "source_excerpt_too_short", f"source excerpt {index} is too short")
        if source_excerpt and question_terms and not (question_terms & normalize_terms(source_excerpt)):
            add_finding(findings, "warn", "source_excerpt_unrelated", f"source excerpt {index} has low lexical overlap with question")

    deduped: list[Finding] = []
    seen: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding.severity, finding.key, finding.message)
        if key not in seen:
            seen.add(key)
            deduped.append(finding)

    return SmokeResult(
        id=case.id,
        category=case.category,
        question=case.question,
        status_code=status_code,
        answer=answer,
        warnings=warnings,
        source_titles=titles,
        source_excerpts=excerpts,
        source_urls=urls,
        source_systems=systems,
        fretboard_exists=has_fretboard,
        section_titles=section_titles(payload),
        findings=deduped,
    )


def answer_contains_contact_or_unapproved_link_junk(answer: str) -> bool:
    def scrub_approved_url(match: re.Match[str]) -> str:
        raw_url = match.group(0).rstrip(".,;)")
        normalized = f"https://{raw_url}" if raw_url.startswith("www.") else raw_url
        return "" if is_approved_curated_url(normalized) else match.group(0)

    scrubbed = URL_RE.sub(scrub_approved_url, answer or "")
    return bool(CONTACT_JUNK_RE.search(scrubbed))


def run_smoke(
    cases: list[QuestionCase],
    *,
    api_url: str,
    timeout: float,
    top_k: int,
    access_role: str,
    rate_limit_retries: int = 1,
) -> list[SmokeResult]:
    results: list[SmokeResult] = []
    for index, case in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] {case.id} {case.question}", flush=True)
        status_code, payload = post_answer(api_url, case.question, timeout=timeout, top_k=top_k, access_role=access_role)
        retry_count = 0
        while status_code == 429 and retry_count < rate_limit_retries:
            retry_after = int(payload.get("retryAfterSeconds") or 60) if isinstance(payload, dict) else 60
            wait_seconds = max(1, min(retry_after, 90))
            print(f"  rate limited; waiting {wait_seconds}s before retry", flush=True)
            time.sleep(wait_seconds)
            retry_count += 1
            status_code, payload = post_answer(api_url, case.question, timeout=timeout, top_k=top_k, access_role=access_role)
        results.append(evaluate_response(case, status_code, payload))
    return results


def summarize_results(results: list[SmokeResult]) -> dict[str, Any]:
    outcome_counts = Counter(result.outcome for result in results)
    category_counts: dict[str, Counter[str]] = defaultdict(Counter)
    finding_counts = Counter()
    for result in results:
        category_counts[result.category][result.outcome] += 1
        for finding in result.findings:
            finding_counts[f"{finding.severity}:{finding.key}"] += 1
    return {
        "total_questions": len(results),
        "outcome_counts": {key: outcome_counts[key] for key in ("pass", "warn", "fail")},
        "category_counts": {category: dict(counts) for category, counts in sorted(category_counts.items())},
        "finding_counts": dict(finding_counts.most_common()),
    }


def result_sort_key(result: SmokeResult) -> tuple[int, int, int, str]:
    outcome_rank = {"fail": 0, "warn": 1, "pass": 2}
    fail_count = sum(1 for finding in result.findings if finding.severity == "fail")
    warn_count = sum(1 for finding in result.findings if finding.severity == "warn")
    return (outcome_rank[result.outcome], -fail_count, -warn_count, result.id)


def backend_fix_recommendations(finding_counts: Counter[str]) -> list[str]:
    fixes: list[str] = []
    if any("chord_position_" in key for key in finding_counts):
        fixes.append("Route chord-position/location questions through deterministic E9 music logic before retrieval, require fretboard payloads, and suppress SGF source cards.")
    if any("raw_sgf_fragment_language" in key or "answer_mostly_quotes_or_fragments" in key for key in finding_counts):
        fixes.append("Strengthen answer synthesis and final gates against raw SGF fragments, copied quotes, and source-thread leftovers.")
    if any("private_profile" in key for key in finding_counts):
        fixes.append("Tighten private-profile routing so personal setup questions use private sources and generic questions never leak private facts.")
    if any("visible_weak_source_language" in key or "internal_retrieval_language" in key for key in finding_counts):
        fixes.append("Replace visible weak-source/internal retrieval language with user-facing fallback wording.")
    if any("low_teaching_value" in key for key in finding_counts):
        fixes.append("Improve teaching templates for practical questions so answers include concrete steps, strings, pedals, checks, or practice actions.")
    if not fixes:
        fixes.append("No dominant backend pattern detected; inspect warnings manually.")
    return fixes


def frontend_fix_recommendations(finding_counts: Counter[str]) -> list[str]:
    fixes: list[str] = []
    if any("chord_position_missing_fretboard" in key for key in finding_counts):
        fixes.append("Verify the UI clearly renders deterministic fretboard payloads and exposes missing-payload states during local smoke review.")
    if any("source_excerpt_too_short" in key or "source_excerpt_unrelated" in key for key in finding_counts):
        fixes.append("Review source-card excerpt display so weak/short cards are visually de-emphasized or hidden when backend marks them low value.")
    if any("non_position_question_has_fretboard" in key for key in finding_counts):
        fixes.append("Check frontend placement rules so fretboard cards appear only when the response payload is intentionally visual.")
    if not fixes:
        fixes.append("No frontend-specific pattern detected from this smoke run.")
    return fixes


def eval_addition_recommendations(finding_counts: Counter[str]) -> list[str]:
    additions: list[str] = []
    if any("chord_position_" in key for key in finding_counts):
        additions.append("Promote failing chord-position smoke questions into deterministic route unit tests and full answer-quality fixtures.")
    if any("private_profile" in key for key in finding_counts):
        additions.append("Add explicit private-profile positive/negative cases for every personal setup phrasing that failed.")
    if any("raw_sgf_fragment_language" in key for key in finding_counts):
        additions.append("Add the newly observed raw-fragment phrases to answer-quality regex buckets.")
    if any("source_excerpt_" in key for key in finding_counts):
        additions.append("Add source-card usefulness assertions for the offending source excerpts.")
    if not additions:
        additions.append("No immediate eval additions beyond manual review of warning samples.")
    return additions


def result_to_json(result: SmokeResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "category": result.category,
        "question": result.question,
        "status_code": result.status_code,
        "outcome": result.outcome,
        "answer": result.answer,
        "answer_excerpt": excerpt(result.answer),
        "warnings": result.warnings,
        "source_titles": result.source_titles,
        "source_excerpts": result.source_excerpts,
        "source_urls": result.source_urls,
        "source_systems": result.source_systems,
        "fretboard_exists": result.fretboard_exists,
        "section_titles": result.section_titles,
        "findings": [
            {"severity": finding.severity, "key": finding.key, "message": finding.message}
            for finding in result.findings
        ],
    }


def render_result_list(results: list[SmokeResult], *, limit: int) -> list[str]:
    lines: list[str] = []
    for result in results[:limit]:
        findings = "; ".join(f"{finding.severity}:{finding.key}" for finding in result.findings) or "pass"
        lines.extend(
            [
                f"### {result.id} - {result.outcome}",
                "",
                f"- Category: `{result.category}`",
                f"- Question: {result.question}",
                f"- Status: {result.status_code}",
                f"- Fretboard: `{result.fretboard_exists}`",
                f"- Sources: {len(result.source_titles)}",
                f"- Source titles: {', '.join(title for title in result.source_titles if title) or 'none'}",
                f"- Findings: {findings}",
                f"- Answer excerpt: {excerpt(result.answer)}",
                "",
            ]
        )
    return lines or ["None."]


def render_markdown_report(results: list[SmokeResult], *, api_url: str, config: dict[str, Any]) -> str:
    summary = summarize_results(results)
    finding_counter = Counter(summary["finding_counts"])
    worst = sorted([result for result in results if result.outcome != "pass"], key=result_sort_key)[:20]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Exploratory Answer Smoke",
        "",
        f"Generated: {now}",
        f"API URL: `{api_url}`",
        "",
        "## Configuration",
        "",
    ]
    for key, value in config.items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Total questions: {summary['total_questions']}",
            f"- Pass: {summary['outcome_counts']['pass']}",
            f"- Warn: {summary['outcome_counts']['warn']}",
            f"- Fail: {summary['outcome_counts']['fail']}",
            "",
            "## Failures By Category",
            "",
            "| Category | Pass | Warn | Fail |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for category, counts in summary["category_counts"].items():
        lines.append(f"| {category} | {counts.get('pass', 0)} | {counts.get('warn', 0)} | {counts.get('fail', 0)} |")

    lines.extend(["", "## Repeated Failure Patterns", ""])
    for key, count in finding_counter.most_common(30):
        lines.append(f"- {key}: {count}")
    if not finding_counter:
        lines.append("- none")

    lines.extend(["", "## Top 20 Worst Answers", ""])
    lines.extend(render_result_list(worst, limit=20))

    lines.extend(["", "## Recommended Backend Fixes", ""])
    for fix in backend_fix_recommendations(finding_counter):
        lines.append(f"- {fix}")

    lines.extend(["", "## Recommended Frontend Fixes", ""])
    for fix in frontend_fix_recommendations(finding_counter):
        lines.append(f"- {fix}")

    lines.extend(["", "## Recommended Eval Additions", ""])
    for addition in eval_addition_recommendations(finding_counter):
        lines.append(f"- {addition}")

    return "\n".join(lines) + "\n"


def write_reports(results: list[SmokeResult], *, output: Path, json_output: Path, api_url: str, config: dict[str, Any]) -> None:
    summary = summarize_results(results)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_report(results, api_url=api_url, config=config), encoding="utf-8")
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(
            {
                "summary": summary,
                "config": {key: str(value) for key, value in config.items()},
                "results": [result_to_json(result) for result in results],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", "--base-url", dest="api_url", default=DEFAULT_API_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--access-role", default=DEFAULT_ACCESS_ROLE)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--rate-limit-retries", type=int, default=2)
    parser.add_argument("--fail-on-findings", action="store_true", help="Exit nonzero if any smoke question fails.")
    return parser


def normalize_answer_api_url(url: str) -> str:
    stripped = (url or "").rstrip("/")
    if stripped.endswith("/api/answer"):
        return stripped
    return f"{stripped}/api/answer"


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.top_k <= 0:
        raise SystemExit("--top-k must be greater than zero")
    cases = built_in_questions()
    if len(cases) < 120:
        raise SystemExit("exploratory smoke question set must contain at least 120 questions")
    if args.limit is not None:
        cases = cases[: max(0, args.limit)]

    api_url = normalize_answer_api_url(args.api_url)
    results = run_smoke(
        cases,
        api_url=api_url,
        timeout=args.timeout,
        top_k=args.top_k,
        access_role=args.access_role,
        rate_limit_retries=args.rate_limit_retries,
    )
    config = {
        "access_role": args.access_role,
        "top_k": args.top_k,
        "timeout": args.timeout,
        "rate_limit_retries": args.rate_limit_retries,
        "question_count": len(cases),
    }
    write_reports(results, output=args.output, json_output=args.json_output, api_url=api_url, config=config)
    summary = summarize_results(results)
    print(f"Evaluated {summary['total_questions']} questions against {api_url}")
    print(f"pass: {summary['outcome_counts']['pass']}")
    print(f"warn: {summary['outcome_counts']['warn']}")
    print(f"fail: {summary['outcome_counts']['fail']}")
    print(f"Markdown report: {args.output}")
    print(f"JSON report: {args.json_output}")
    if args.fail_on_findings and summary["outcome_counts"]["fail"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
