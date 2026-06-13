#!/usr/bin/env python3
"""Run a strict local answer-quality eval for the protected-preview stack."""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import threading
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from wsgiref.simple_server import WSGIServer, make_server

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pocketsteel.access_control import DEV_ACCESS_ROLE_HEADER
from pocketsteel.answer_contracts import normalize_intent
from pocketsteel.answer_usage import InMemoryAnswerRateLimiter
from pocketsteel.api import create_app
from pocketsteel.answering import question_mentions_private_profile
from pocketsteel.chroma_search import ChromaSearchIndex
from pocketsteel.fretboard_examples import get_e9_major_chord_positions, major_chord_location_request_for_question
from pocketsteel.private_source_search import PrivateSourceSearchIndex
from pocketsteel.retrieval_modes import (
    DEFAULT_PRIVATE_CHROMA_PATH,
    DEFAULT_PRIVATE_COLLECTION,
    DEFAULT_SGF_V2_CHROMA_PATH,
    DEFAULT_SGF_V2_COLLECTION,
    PRIVATE_CAPABLE_ROLES,
    RetrievalMode,
    RetrievalModeConfig,
)
from scripts.run_answer_eval import (
    DEFAULT_QUESTION_BANK,
    add_directness_failures,
    evaluate_answer,
    infer_expected_intent,
    load_question_bank,
)
from scripts.run_retrieval_ab_eval import RerankConfig
from scripts.run_v2_rerank_answer_eval import RerankedSearchIndex


DEFAULT_OUTPUT = Path("corpus-private/reports/full-answer-quality-eval.md")
DEFAULT_JSON_OUTPUT = Path("corpus-private/reports/full-answer-quality-eval.json")
DEFAULT_TOP_K = 6
DETERMINISTIC_CHORD_POSITION_FAILURE_BUCKETS = {
    "missing_deterministic_chord_route",
    "missing_fretboard_payload_for_chord_position",
    "wrong_key_chord_position_leakage",
    "source_fragment_chord_answer_failure",
    "unrelated_sgf_sources_for_deterministic_answer",
    "enharmonic_chord_position_failure",
    "starter_only_fretboard_catalog",
    "missing_alternate_position",
    "missing_fretboard_filters",
    "object_object_rendering_failure",
    "deterministic_chord_weak_warning",
    "deterministic_chord_source_leakage",
    "chord_position_typo_fallback_failure",
    "chord_position_router_escape",
    "beginner_chord_concept_router_escape",
    "deterministic_visual_missing_fretboard",
    "weak_source_leakage",
    "object_object_rendering",
}
ADVICE_FAILURE_BUCKETS = {
    "advice_question_must_answer_directly",
    "advice_question_raw_fragment_failure",
    "advice_question_joke_anecdote_failure",
    "gear_question_background_only_failure",
}

Outcome = Literal["pass", "warn", "fail"]
Severity = Literal["warn", "fail"]

INTERNAL_LANGUAGE_RE = re.compile(
    r"\b(?:retrieved material|source cards|Useful distilled points|Useful source-backed points|"
    r"cleanest source-backed answer|safest answer I can support|source context|forum-source context|"
    r"For RAG answers)\b",
    re.I,
)
RAW_JUNK_RE = re.compile(
    r"\b(?:PayPal|sp=sharing|e-?mail|order\s+(?:form|page|link|online|through)|"
    r"Does anyone know|Has anyone compared|Thanks Nick|Top Hi All|\[link removed\])\b|"
    r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
    re.I,
)
FORUM_FRAGMENT_RE = re.compile(
    r"\b[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){0,3}\s*/\s*\d{1,2}\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}",
    re.I,
)
DIRECTNESS_BAD_START_RE = re.compile(
    r"^\s*(?:Top\b|I found\b|The retrieved\b|Retrieved\b|Useful\b|Source\b|Forum\b|"
    r"Here is the safest\b|The cleanest source-backed\b|It depends\b)",
    re.I,
)
MECHANICS_RE = re.compile(
    r"\b(?:string|strings|fret|frets|pedal|pedals|lever|levers|A\+B|A\+F|B\+C|"
    r"E-lower|F lever|grip|grips|chord|major|minor|interval|scale|position)\b",
    re.I,
)
ACTION_RE = re.compile(
    r"\b(?:practice|try|play|check|test|listen|move|slow|repeat|work|isolate|compare|"
    r"start|use|set|adjust|swap|mute|block)\b",
    re.I,
)
TROUBLESHOOT_RE = re.compile(r"\b(?:check|test|swap|isolate|cable|ground|tech|safety|signal chain|amp)\b", re.I)
BRAND_COMPARE_RE = re.compile(r"\b(?:no universal winner|depends|fit|condition|tone|mechanics|budget|support|copedent)\b", re.I)
VENDOR_RE = re.compile(r"\b(?:buy|dealer|vendor|shop|store|classifieds|used market|maker|manufacturer|availability|current)\b", re.I)
SONG_GUARDRAIL_RE = re.compile(r"\b(?:approach|style|chord|progression|public domain|original|exercise|not provide full|cannot provide full)\b", re.I)
PRIVATE_PROFILE_RE = re.compile(r"\b(?:your saved 10-string E9 profile|your private|my common grips|your E9 copedent)\b", re.I)
SENSITIVE_IDENTITY_RE = re.compile(r"\b(?:gay|identity|private trait|orientation|race|religion|medical)\b", re.I)
CHORD_POSITION_LOCATION_RE = re.compile(
    r"\b(?:where\s+(?:all\s+)?can\s+i\s+play|where\s+can\s+i\s+find|how\s+do\s+i\s+play|how\s+do\s+i\s+plan|"
    r"how\s+do\s+i\s+make|show\s+me(?:\s+places\s+to\s+play)?|where\s+are|where\s+is|what\s+frets\s+give\s+me)\b"
    r".*?\b(?:an?\s+)?(?P<key>[A-G](?:#|b)?)(?:\s+(?:major\s+)?(?:chord|positions?)|\s+major\b|\b)",
    re.I,
)
GRIP_POSITION_LOCATION_RE = re.compile(r"\bwhat\s+grips\s+can\s+i\s+use\s+for\s+(?P<key>[A-G](?:#|b)?)\s+major\b", re.I)
CHORD_POSITION_TYPO_RE = re.compile(r"\bhow\s+do\s+i\s+plan\s+(?:an?\s+)?(?P<key>[A-G](?:#|b)?)(?:\s+(?:major\s+)?chord)?\b", re.I)
CHORD_POSITION_ROUTER_ESCAPE_RE = re.compile(
    r"\b(?:where\s+are\s+some\s+places\s+to\s+play|where\s+can\s+i\s+play|show\s+me|what\s+frets\s+give\s+me)\s+"
    r"(?P<key>[A-G](?:#|b)?)(?:\s+(?:major\s+)?(?:chords?|positions?))?\b",
    re.I,
)
MINOR_FUNCTION_ROUTER_ESCAPE_RE = re.compile(
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
KEYED_MAJOR_CHORD_RE = re.compile(r"\b(?P<key>[A-G](?:#|b)?)\s+(?:major|chord)\b", re.I)
DOMINANT_SEVENTH_CHORD_RE = re.compile(r"\b(?P<key>[A-G](?:#|b)?)7\b", re.I)
DOMINANT_CONTEXT_RE = re.compile(
    r"\b(?:I[- ]?IV[- ]?V|1[- ]?4[- ]?5|key\s+of|dominant|V\s+chord|turnaround|progression)\b",
    re.I,
)
A_MAJOR_WRONG_POSITION_RE = re.compile(
    r"(?:\b(?:3rd|third|6th|sixth|10th|tenth)\s+fret\b.*\b(?:A\+F|A\s+pedal\s+(?:and|\+)\s+F\s+lever|A\+B)|"
    r"\b(?:A\+F|A\s+pedal\s+(?:and|\+)\s+F\s+lever)\b.*\b(?:6th|sixth)\s+fret\b|"
    r"\bA\+B\b.*\b(?:10th|tenth)\s+fret\b)",
    re.I | re.S,
)
RAW_CHORD_FRAGMENT_RE = re.compile(
    r"\b(?:[A-G](?:#|b)?7\s*=|Example:\s+[A-G](?:#|b)?\s+major|"
    r"You can play\s+[A-G](?:#|b)?,\s+[A-G](?:#|b)?,\s+and\s+[A-G](?:#|b)?7|"
    r"G#>F#|B's\s+to\s+Bb|with\s+your\s+middle\s+finger|lowering\s+G#|"
    r"You either tune it|I've played it this way|starting with the first string|"
    r"RKL\s+fully\s+engaged|B9\s+chord)\b",
    re.I,
)
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
WEAK_SOURCE_CHORD_ROUTE_RE = re.compile(
    r"\b(?:source support was weak|source support is weak|curated answer used;\s*source support was weak|"
    r"API warning indicates weak/no source|no strong source match|retrieval match was weak|sources are weak)\b",
    re.I,
)
E_LOWER_578_B9_QUESTION_RE = re.compile(
    r"(?=.*\b5\s*[-/ ]\s*7\s*[-/ ]\s*8\b)(?=.*\bE[- ]?lower(?:ed)?\b)(?=.*\bB9\b)",
    re.I,
)
E_LOWER_578_DIAGNOSTIC_QUESTION_RE = re.compile(
    r"(?=.*\b5\s*[-/ ]\s*7\s*[-/ ]\s*8\b)(?=.*\bE[- ]?lower(?:ed)?\b)(?=.*\b(?:at|on)\s+(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\s+fret\b)",
    re.I,
)
FUNCTIONAL_POCKET_QUESTION_RE = re.compile(
    r"\b(?:show me|where are|give me)\s+(?:v|5|five)(?:\s+chord)?\s+pockets?\s+in\s+[A-G](?:#|b)?\b",
    re.I,
)
B9_NEGATION_RE = re.compile(
    r"\b(?:not|isn't|is\s+not|no)\b.{0,80}\bB9\b|\bB9\b.{0,80}\b(?:not|isn't|is\s+not)\b",
    re.I | re.S,
)
E_LOWER_578_DISCLOSURE_RE = re.compile(
    r"\bD\s+major\b.*\brootless\s+B\s+minor\s+7\b|\brootless\s+B\s+minor\s+7\b.*\bD\s+major\b",
    re.I | re.S,
)

FALLBACK_CATEGORIES = {
    "source_mismatch_no_source",
    "prompt_injection_hostile_retrieved_text",
}

MAINTENANCE_DIAGNOSTIC_RE = re.compile(
    r"\b(?:fix|will not|won't|not return|cabinet drop|buzz|causes|string will not|what do i do if)\b",
    re.I,
)
MAINTENANCE_ACTION_RE = re.compile(
    r"\b(?:check|test|adjust|measure|match|replace|contact|clean|lubricat|oil|avoid|caution|sparingly|tune|thread|connector|qualified|tech)\b",
    re.I,
)


@dataclass(frozen=True)
class QualityFinding:
    severity: Severity
    key: str
    message: str


@dataclass
class QualityResult:
    id: str
    category: str
    category_family: str
    question: str
    expected_intent: str
    expected_contract: str
    status_code: int
    answer: str
    warnings: list[str]
    sources: list[dict[str, Any]]
    findings: list[QualityFinding] = field(default_factory=list)

    @property
    def outcome(self) -> Outcome:
        if any(finding.severity == "fail" for finding in self.findings):
            return "fail"
        if self.findings:
            return "warn"
        return "pass"

    @property
    def private_source_count(self) -> int:
        return sum(1 for source in self.sources if is_private_source_card(source))


def category_family(row: dict[str, str]) -> str:
    category = row.get("category", "")
    expected = normalize_intent(row.get("expected_contract") or row.get("expected_intent") or "")
    if category == "entity_player_biography":
        return "player/teacher bio"
    if category == "rankings_subjective_players":
        return "subjective ranking"
    if category == "e9_fretboard_copedent" or expected in {"copedent_fretboard", "right_hand_technique"}:
        return "copedent/fretboard"
    if category == "practice_plan_questions" or expected == "practice_plan":
        return "practice/exercises"
    if category == "gear_effects_tone" or expected in {"tone_touch", "technique_improvement"}:
        return "gear/tone"
    if category in {"maintenance_parts_safety", "diagnostic_troubleshooting"} or expected == "diagnostic_troubleshooting":
        return "maintenance/troubleshooting"
    if category == "brands_comparisons" or expected == "brand_comparison":
        return "brand comparison"
    if category == "accessories_products" or expected == "vendor_buying_guidance":
        return "vendor/buying"
    if category == "song_learning_or_tab_request" or expected == "song_learning":
        return "song/tab/guardrail"
    if category in {"source_mismatch_no_source", "prompt_injection_hostile_retrieved_text"}:
        return "fallback/guardrail"
    if category == "latest_frontend_failures" and SENSITIVE_IDENTITY_RE.search(row.get("question", "")):
        return "sensitive identity/current roster"
    if question_mentions_private_profile(row.get("question", "")):
        return "private-profile/personal setup"
    return category or "uncategorized"


def first_sentence(answer: str) -> str:
    text = re.sub(r"\s+", " ", answer or "").strip()
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s+", text)
    return text[: match.start()].strip() if match else text


def excerpt(text: str, width: int = 260) -> str:
    return textwrap.shorten(re.sub(r"\s+", " ", text or "").strip(), width=width, placeholder=" ...")


def add_finding(findings: list[QualityFinding], severity: Severity, key: str, message: str) -> None:
    findings.append(QualityFinding(severity=severity, key=key, message=message))


def normalize_chord_key(key: str) -> str:
    return (key or "").strip().replace("♯", "#").replace("♭", "b").upper()


def requested_chord_position_request(question: str) -> Any | None:
    if MINOR_FUNCTION_ROUTER_ESCAPE_RE.search(question or ""):
        return None
    request = major_chord_location_request_for_question(question)
    if request is not None:
        return request
    request = beginner_major_chord_concept_request(question)
    if request is not None:
        return request
    match = (
        CHORD_POSITION_LOCATION_RE.search(question or "")
        or CHORD_POSITION_ROUTER_ESCAPE_RE.search(question or "")
        or GRIP_POSITION_LOCATION_RE.search(question or "")
    )
    if not match:
        return None
    try:
        return major_chord_location_request_for_question(f"where can i play a {match.group('key')} chord")
    except ValueError:
        return None


def is_deterministic_chord_position_question(question: str) -> bool:
    return requested_chord_position_request(question) is not None


def is_chord_position_typo_question(question: str) -> bool:
    return bool(CHORD_POSITION_TYPO_RE.search(question or ""))


def is_chord_position_router_escape_question(question: str) -> bool:
    return bool(
        CHORD_POSITION_ROUTER_ESCAPE_RE.search(question or "")
        or MINOR_FUNCTION_ROUTER_ESCAPE_RE.search(question or "")
    )


def is_beginner_chord_concept_question(question: str) -> bool:
    return bool(
        BEGINNER_MAJOR_CHORD_CONCEPT_RE.search(question or "")
        or BEGINNER_MINOR_CHORD_CONCEPT_RE.search(question or "")
    )


def is_deterministic_pitch_rule_question(question: str) -> bool:
    return bool(
        is_deterministic_chord_position_question(question)
        or is_chord_position_router_escape_question(question)
        or is_beginner_chord_concept_question(question)
        or E_LOWER_578_DIAGNOSTIC_QUESTION_RE.search(question or "")
        or E_LOWER_578_B9_QUESTION_RE.search(question or "")
        or FUNCTIONAL_POCKET_QUESTION_RE.search(question or "")
    )


def requested_chord_position_key(question: str) -> str:
    request = requested_chord_position_request(question)
    return request.normalized_key if request else ""


def beginner_major_chord_concept_request(question: str) -> Any | None:
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


def answer_mentions_required_major_positions(answer: str, key: str) -> bool:
    try:
        required_frets = [
            position["fret"]
            for position in get_e9_major_chord_positions(key)
            if position["role"] in {"Open position", "A+F position", "A+B position"}
        ]
    except ValueError:
        return True
    return all(
        re.search(rf"\b{fret}(?:st|nd|rd|th)?\s+fret\b", answer, re.I)
        for fret in required_frets
    )


def answer_has_beginner_chord_explanation(answer: str, question: str) -> bool:
    request = beginner_major_chord_concept_request(question)
    if request is not None:
        expected_tones = {
            "G": (r"\bG\b", r"\bB\b", r"\bD\b"),
            "C": (r"\bC\b", r"\bE\b", r"\bG\b"),
            "D": (r"\bD\b", r"(?<![A-G#b])F#(?![A-G#b])", r"\bA\b"),
        }.get(request.normalized_key, (rf"\b{re.escape(request.normalized_key)}\b",))
        return (
            all(re.search(tone, answer or "", re.I) for tone in expected_tones)
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


def is_practical_advice_question(question: str, category: str) -> bool:
    return bool(
        PRACTICAL_ADVICE_QUESTION_RE.search(question or "")
        or (
            category in {"gear_effects_tone", "maintenance_parts_safety", "diagnostic_troubleshooting"}
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


def expected_chord_position_frets(key: str) -> list[int]:
    return [
        position["fret"]
        for position in get_e9_major_chord_positions(key)
        if position["role"] in {"Open position", "A+F position", "A+B position"}
    ]


def has_fretboard_payload(payload: dict[str, Any]) -> bool:
    fretboard = payload.get("fretboard")
    if not isinstance(fretboard, dict):
        return False
    positions = fretboard.get("positions")
    return isinstance(positions, list) and bool(positions)


def fretboard_payload_has_expected_chord_positions(payload: dict[str, Any], key: str) -> bool:
    fretboard = payload.get("fretboard")
    if not isinstance(fretboard, dict):
        return False
    positions = fretboard.get("positions")
    if not isinstance(positions, list):
        return False
    expected = set(expected_chord_position_frets(key))
    actual = {
        position.get("fret")
        for position in positions
        if isinstance(position, dict)
        and position.get("role") in {"Open position", "A+F position", "A+B position"}
        and position.get("strings") == [4, 5, 6]
    }
    return expected <= actual


def fretboard_positions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fretboard = payload.get("fretboard")
    if not isinstance(fretboard, dict):
        return []
    positions = fretboard.get("positions")
    if not isinstance(positions, list):
        return []
    return [position for position in positions if isinstance(position, dict)]


def has_expanded_catalog_intent(question: str, key: str) -> bool:
    return key == "B" and bool(re.search(r"\b(?:all|more|advanced|with\s+levers|grips?)\b", question or "", re.I))


def position_has_required_filter_metadata(position: dict[str, Any]) -> bool:
    return (
        isinstance(position.get("family"), str)
        and bool(position.get("family"))
        and isinstance(position.get("tier"), str)
        and bool(position.get("tier"))
        and isinstance(position.get("colorRole"), str)
        and bool(position.get("colorRole"))
        and isinstance(position.get("visibleByDefault"), bool)
        and isinstance(position.get("sortOrder"), int)
    )


def has_b_fret_two_ab_alternate(positions: list[dict[str, Any]]) -> bool:
    return any(
        position.get("fret") == 2
        and position.get("pedals") == ["A", "B"]
        and position.get("strings") == [4, 5, 6]
        for position in positions
    )


def is_sgf_forum_source(source: dict[str, Any]) -> bool:
    if is_private_source_card(source):
        return False
    haystack = " ".join(
        str(source.get(field) or "")
        for field in ("url", "thread_url", "forumName", "forum_name", "source_system", "sourceSystem")
    ).lower()
    return bool(
        "steelguitarforum.com" in haystack
        or "steel guitar forum" in haystack
        or "sgf_" in haystack
        or "phpbb" in haystack
        or "ubb" in haystack
    )


def evaluate_chord_position_key_leakage(question: str, answer: str, findings: list[QualityFinding]) -> None:
    request = requested_chord_position_request(question)
    if not request:
        return
    requested_key = request.normalized_key

    dominant_context_allowed = bool(DOMINANT_CONTEXT_RE.search(question))
    for match in KEYED_MAJOR_CHORD_RE.finditer(answer):
        mentioned_key = normalize_chord_key(match.group("key"))
        if mentioned_key and mentioned_key != requested_key:
            add_finding(
                findings,
                "fail",
                "wrong_key_chord_position_leakage",
                f"chord-position answer for {requested_key} leaked {mentioned_key} major/chord material",
            )
            break

    if not dominant_context_allowed:
        dominant_match = DOMINANT_SEVENTH_CHORD_RE.search(answer)
        if dominant_match:
            add_finding(
                findings,
                "fail",
                "wrong_key_chord_position_leakage",
                f"chord-position answer for {requested_key} leaked unrelated dominant material ({dominant_match.group(0)})",
            )

    if requested_key == "A" and A_MAJOR_WRONG_POSITION_RE.search(answer):
        add_finding(
            findings,
            "fail",
            "wrong_key_chord_position_leakage",
            "chord-position answer appears to reuse wrong-key E9 major-position examples",
        )
    if RAW_CHORD_FRAGMENT_RE.search(answer):
        add_finding(
            findings,
            "fail",
            "source_fragment_chord_answer_failure",
            "plain chord-position answer appears to reuse raw source fragments",
        )
    if request.is_enharmonic and not re.search(
        rf"(?<!\w){re.escape(request.requested_root)}(?!\w).*?\b(?:same pitch as|enharmonic|think of it as)\b.*?(?<!\w){re.escape(request.normalized_key)}(?!\w)",
        answer,
        re.I | re.S,
    ):
        add_finding(
            findings,
            "fail",
            "enharmonic_chord_position_failure",
            f"enharmonic chord-position answer did not explain {request.requested_root} as {request.normalized_key}",
        )
    if not answer_mentions_required_major_positions(answer, requested_key):
        required = ", ".join(f"{fret}th" if fret not in {1, 2, 3} else f"{fret}{'st' if fret == 1 else 'nd' if fret == 2 else 'rd'}" for fret in expected_chord_position_frets(requested_key))
        add_finding(
            findings,
            "fail",
            "missing_deterministic_chord_route",
            f"{requested_key} chord-position answer did not provide the deterministic {required} fret positions",
        )


def evaluate_deterministic_chord_position_response(
    *,
    question: str,
    answer: str,
    warnings: list[str],
    sources: list[dict[str, Any]],
    payload: dict[str, Any],
    findings: list[QualityFinding],
) -> None:
    request = requested_chord_position_request(question)
    if request is None:
        return
    typo_question = is_chord_position_typo_question(question)
    router_escape_question = is_chord_position_router_escape_question(question)
    beginner_concept_question = beginner_major_chord_concept_request(question) is not None
    beginner_theory_question = question_needs_beginner_chord_explanation(question)
    if not answer_mentions_required_major_positions(answer, request.normalized_key):
        add_finding(
            findings,
            "fail",
            "missing_deterministic_chord_route",
            f"{request.normalized_key} chord-position answer did not route to deterministic E9 frets",
        )
        if typo_question:
            add_finding(
                findings,
                "fail",
                "chord_position_typo_fallback_failure",
                "typo chord-position answer did not route to deterministic E9 frets",
            )
        if router_escape_question:
            add_finding(
                findings,
                "fail",
                "chord_position_router_escape",
                "router-escape chord-position answer did not route to deterministic E9 frets",
            )
        if beginner_concept_question:
            add_finding(
                findings,
                "fail",
                "beginner_chord_concept_router_escape",
                "beginner chord concept answer did not route to deterministic E9 frets",
            )
    if beginner_theory_question and beginner_concept_question and not answer_has_beginner_chord_explanation(answer, question):
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner chord concept answer lacks chord tones, interval explanation, or steel-specific application",
        )
    if WEAK_SOURCE_CHORD_ROUTE_RE.search(answer) or any(WEAK_SOURCE_CHORD_ROUTE_RE.search(warning) for warning in warnings):
        add_finding(
            findings,
            "fail",
            "missing_deterministic_chord_route",
            "deterministic chord-position answer exposed weak/no-source retrieval fallback language",
        )
        add_finding(
            findings,
            "fail",
            "deterministic_chord_weak_warning",
            "deterministic chord-position answer exposed weak-source warning language",
        )
        if typo_question:
            add_finding(
                findings,
                "fail",
                "chord_position_typo_fallback_failure",
                "typo chord-position answer exposed weak-source fallback language",
            )
        if router_escape_question:
            add_finding(
                findings,
                "fail",
                "chord_position_router_escape",
                "router-escape chord-position answer exposed weak-source fallback language",
            )
        if beginner_concept_question:
            add_finding(
                findings,
                "fail",
                "beginner_chord_concept_router_escape",
                "beginner chord concept answer exposed weak-source fallback language",
            )
    if "[object Object]" in answer:
        add_finding(
            findings,
            "fail",
            "object_object_rendering_failure",
            "answer rendered an object as [object Object]",
        )
    if not has_fretboard_payload(payload):
        add_finding(
            findings,
            "fail",
            "missing_fretboard_payload_for_chord_position",
            "deterministic chord-position answer did not include response.fretboard",
        )
        if typo_question:
            add_finding(
                findings,
                "fail",
                "chord_position_typo_fallback_failure",
                "typo chord-position answer did not include response.fretboard",
            )
        if router_escape_question:
            add_finding(
                findings,
                "fail",
                "chord_position_router_escape",
                "router-escape chord-position answer did not include response.fretboard",
            )
        if beginner_concept_question:
            add_finding(
                findings,
                "fail",
                "beginner_chord_concept_router_escape",
                "beginner chord concept answer did not include response.fretboard",
            )
    elif not fretboard_payload_has_expected_chord_positions(payload, request.normalized_key):
        add_finding(
            findings,
            "fail",
            "missing_fretboard_payload_for_chord_position",
            "response.fretboard did not contain the expected deterministic chord positions",
        )
        if typo_question:
            add_finding(
                findings,
                "fail",
                "chord_position_typo_fallback_failure",
                "typo chord-position fretboard omitted expected positions",
            )
        if router_escape_question:
            add_finding(
                findings,
                "fail",
                "chord_position_router_escape",
                "router-escape chord-position fretboard omitted expected positions",
            )
        if beginner_concept_question:
            add_finding(
                findings,
                "fail",
                "beginner_chord_concept_router_escape",
                "beginner chord concept fretboard omitted expected positions",
            )
    positions = fretboard_positions(payload)
    if positions and not all(position_has_required_filter_metadata(position) for position in positions):
        add_finding(
            findings,
            "fail",
            "missing_fretboard_filters",
            "response.fretboard positions are missing metadata required for frontend filters",
        )
    if has_expanded_catalog_intent(question, request.normalized_key):
        if positions and len(positions) <= 3:
            add_finding(
                findings,
                "fail",
                "starter_only_fretboard_catalog",
                "expanded chord-position question returned only starter positions",
            )
        if positions and not has_b_fret_two_ab_alternate(positions):
            add_finding(
                findings,
                "fail",
                "missing_alternate_position",
                "expanded B major payload omitted fret 2 A+B alternate",
            )
    if any(is_sgf_forum_source(source) for source in sources):
        add_finding(
            findings,
            "fail",
            "unrelated_sgf_sources_for_deterministic_answer",
            "deterministic chord-position answer returned top-level SGF source cards",
        )
        add_finding(
            findings,
            "fail",
            "deterministic_chord_source_leakage",
            "deterministic chord-position answer returned SGF source cards",
        )
    if typo_question and sources:
        add_finding(
            findings,
            "fail",
            "chord_position_typo_fallback_failure",
            "typo chord-position answer returned source cards instead of a deterministic no-source answer",
        )
    if router_escape_question and sources:
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            "router-escape chord-position answer returned source cards instead of a deterministic no-source answer",
        )
    if beginner_concept_question and sources:
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner chord concept answer returned source cards instead of a deterministic no-source answer",
        )


def evaluate_beginner_minor_chord_concept_response(
    *,
    question: str,
    answer: str,
    warnings: list[str],
    sources: list[dict[str, Any]],
    payload: dict[str, Any],
    findings: list[QualityFinding],
) -> None:
    if not question_needs_beginner_chord_explanation(question) or not BEGINNER_MINOR_CHORD_CONCEPT_RE.search(question or ""):
        return
    if not answer_has_beginner_chord_explanation(answer, question):
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner minor chord concept answer lacks chord tones, flat-third explanation, or steel-specific application",
        )
    if WEAK_SOURCE_CHORD_ROUTE_RE.search(answer) or any(WEAK_SOURCE_CHORD_ROUTE_RE.search(warning) for warning in warnings):
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner minor chord concept answer exposed weak-source fallback language",
        )
    if RAW_CHORD_FRAGMENT_RE.search(answer) or INTERNAL_LANGUAGE_RE.search(answer) or FORUM_FRAGMENT_RE.search(answer):
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner minor chord concept answer appears to contain SGF/source fragment text",
        )
    if sources:
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner minor chord concept answer returned source cards instead of a deterministic no-source answer",
        )
    if not has_fretboard_payload(payload):
        add_finding(
            findings,
            "fail",
            "beginner_chord_concept_router_escape",
            "beginner minor chord concept answer did not include response.fretboard",
        )


def evaluate_practical_advice_response(
    *,
    row: dict[str, str],
    answer: str,
    warnings: list[str],
    findings: list[QualityFinding],
) -> None:
    question = row.get("question", "")
    if not is_practical_advice_question(question, row.get("category", "")):
        return
    first = first_sentence(answer)
    if (
        not first
        or first.startswith("-")
        or DIRECTNESS_BAD_START_RE.search(first)
        or not advice_answer_has_practical_steps(answer)
        or not advice_answer_addresses_question(answer, question)
    ):
        add_finding(
            findings,
            "fail",
            "advice_question_must_answer_directly",
            "practical advice answer lacks direct actionable guidance",
        )
    if RAW_CHORD_FRAGMENT_RE.search(answer) or FORUM_FRAGMENT_RE.search(answer) or ADVICE_FRAGMENT_RE.search(answer) or first.startswith("-"):
        add_finding(
            findings,
            "fail",
            "advice_question_raw_fragment_failure",
            "practical advice answer appears to be raw fragments or source snippets",
        )
    if ADVICE_JOKE_ANECDOTE_RE.search(answer):
        add_finding(
            findings,
            "fail",
            "advice_question_joke_anecdote_failure",
            "practical advice answer leans on jokes, anecdotes, injury, or embarrassment stories",
        )
    if advice_answer_is_background_only(answer):
        add_finding(
            findings,
            "fail",
            "gear_question_background_only_failure",
            "gear/gig advice answer gives background without practical next steps",
        )
    if WEAK_SOURCE_CHORD_ROUTE_RE.search(answer) or any(WEAK_SOURCE_CHORD_ROUTE_RE.search(warning) for warning in warnings):
        add_finding(
            findings,
            "fail",
            "weak_source_leakage",
            "practical advice answer exposed weak-source wording",
        )


def is_private_source_card(source: dict[str, Any]) -> bool:
    return str(source.get("visibility") or "").lower() == "private" or str(source.get("source_system") or "").startswith("private")


def fallback_expected(row: dict[str, str]) -> bool:
    question = row.get("question", "")
    return (
        row.get("category") in FALLBACK_CATEGORIES
        or bool(SENSITIVE_IDENTITY_RE.search(question))
        or "current" in normalize_intent(row.get("expected_intent") or "")
    )


def fallback_quality_is_good(answer: str) -> bool:
    return bool(
        re.search(r"\b(?:do not|don't|cannot|can't|not enough|no strong|not safe|ignore|check current|verify current)\b", answer, re.I)
        and not RAW_JUNK_RE.search(answer)
    )


def answer_mentions_question_subject(question: str, answer: str) -> bool:
    who = re.match(r"^\s*Who is\s+(.+?)\??\s*$", question, re.I)
    if who:
        name = who.group(1).strip()
        return bool(re.search(rf"\b{re.escape(name)}\b", answer, re.I))
    brands = re.findall(r"\b(Mullen|MSA|Emmons|Sho-Bud|ZumSteel|Carter|GFI|Sierra|Telonics|Benado|Sarno|Goodrich|BJS)\b", question, re.I)
    return all(re.search(rf"\b{re.escape(brand)}\b", answer, re.I) for brand in set(brands)) if brands else True


def evaluate_source_cards(
    *,
    row: dict[str, str],
    sources: list[dict[str, Any]],
    access_role: str,
    findings: list[QualityFinding],
) -> None:
    if not sources:
        if is_deterministic_pitch_rule_question(row.get("question", "")):
            return
        if fallback_expected(row):
            add_finding(findings, "warn", "no_source_fallback", "answer used fallback/no-source path; review fallback quality")
        else:
            add_finding(findings, "fail", "missing_sources", "answer has no source cards for a source-backed question")
        return

    private_allowed = access_role in PRIVATE_CAPABLE_ROLES
    private_count = 0
    public_url_count = 0
    useful_count = 0
    for index, source in enumerate(sources, 1):
        title = str(source.get("title") or "").strip()
        url = str(source.get("url") or "").strip()
        excerpt_text = str(source.get("excerpt") or "").strip()
        private = is_private_source_card(source)
        if private:
            private_count += 1
            if not private_allowed:
                add_finding(findings, "fail", "unauthorized_private_source", "private source card returned to unauthorized role")
        elif url:
            public_url_count += 1

        if not title:
            add_finding(findings, "fail", "source_missing_title", f"source card {index} is missing a title")
        if not private and not url:
            add_finding(findings, "fail", "source_missing_url", f"public source card {index} is missing a URL")
        if private and not (source.get("source_id") or source.get("source_path")):
            add_finding(findings, "warn", "private_source_missing_identity", f"private source card {index} lacks source_id/source_path")
        if excerpt_text and len(excerpt_text) >= 45:
            useful_count += 1
        elif str(source.get("answer_quote_allowed") or "").lower() != "false":
            add_finding(findings, "warn", "source_excerpt_too_short", f"source card {index} excerpt is too short")
        if RAW_JUNK_RE.search(excerpt_text) or FORUM_FRAGMENT_RE.search(excerpt_text):
            add_finding(findings, "warn", "source_excerpt_junk", f"source card {index} excerpt contains raw forum/contact/order junk")

    if not private_count and not public_url_count:
        add_finding(findings, "fail", "no_clickable_public_source", "source cards lack public URLs and no private source identity is present")
    if useful_count == 0:
        add_finding(findings, "warn", "weak_source_card_usefulness", "no source card has a useful excerpt")


def evaluate_category_specific(row: dict[str, str], answer: str, sources: list[dict[str, Any]], findings: list[QualityFinding]) -> None:
    question = row["question"]
    family = category_family(row)
    first = first_sentence(answer)
    lower_answer = answer.lower()

    evaluate_chord_position_key_leakage(question, answer, findings)
    evaluate_e_lower_578_b9_disclosure(question, answer, findings)

    if family == "player/teacher bio":
        if not answer_mentions_question_subject(question, answer):
            add_finding(findings, "fail", "bio_missing_subject", "player/teacher bio does not mention the requested person")
        if re.search(r"\brankings are subjective\b|\btop\s+\d+\b", answer, re.I):
            add_finding(findings, "fail", "bio_routed_as_ranking", "player/teacher bio used ranking language")
        if not re.search(r"\b(?:player|steel guitarist|pedal steel|recording|session|teacher|innovator)\b", answer, re.I):
            add_finding(findings, "warn", "bio_too_thin", "bio lacks a basic role/contribution statement")

    elif family == "subjective ranking":
        player_mentions = len(set(re.findall(r"\b(Buddy Emmons|Lloyd Green|Paul Franklin|Jimmy Day|Ralph Mooney|Curly Chalker|John Hughey|Tom Brumley|Doug Jernigan|Hal Rugg|Pete Drake)\b", answer, re.I)))
        if player_mentions < 3:
            add_finding(findings, "warn", "ranking_too_few_examples", "subjective ranking answer names too few players")
        if not re.search(r"\b(?:subjective|depends|one way to frame|not definitive|criteria)\b", answer, re.I):
            add_finding(findings, "warn", "ranking_missing_subjectivity", "ranking answer should frame the list as subjective")

    elif family == "copedent/fretboard":
        if not MECHANICS_RE.search(answer):
            add_finding(findings, "fail", "missing_mechanics", "copedent/fretboard answer lacks strings, frets, pedals, levers, or chord-function language")
        if re.search(r"\bA\+F|A pedal and F lever|A pedal.*F lever\b", question, re.I):
            if not (re.search(r"\bA\s*(?:pedal|\+)", answer, re.I) and re.search(r"\bF\s*(?:lever|\+)", answer, re.I) and re.search(r"\bmajor\b", answer, re.I)):
                add_finding(findings, "fail", "af_mechanics_incomplete", "A+F answer should mention A pedal, F lever, and the major-position function")
        if "unsupported exact mechanics" in lower_answer:
            add_finding(findings, "fail", "unsupported_exact_mechanics", "answer admits unsupported exact mechanics")

    elif family == "practice/exercises":
        if not re.search(r"\b(?:minute|day|routine|exercise|step|practice|repeat|tempo|slow)\b", answer, re.I):
            add_finding(findings, "fail", "practice_not_actionable", "practice answer lacks a concrete routine, exercise, or practice step")
        if not ACTION_RE.search(answer):
            add_finding(findings, "warn", "practice_low_teaching_value", "practice answer has low actionable teaching value")

    elif family == "gear/tone":
        if RAW_JUNK_RE.search(answer):
            add_finding(findings, "fail", "gear_contact_order_junk", "gear/tone answer contains contact, PayPal, order, or raw-link junk")
        if re.search(r"\bworth|buy|best|where can i buy\b", question, re.I) and not re.search(r"\b(?:condition|availability|try|current|dealer|used|budget|fit|need)\b", answer, re.I):
            add_finding(findings, "warn", "gear_buying_context_missing", "gear/buying answer lacks current availability, condition, budget, or fit caveats")

    elif family == "maintenance/troubleshooting":
        if MAINTENANCE_DIAGNOSTIC_RE.search(question):
            if not TROUBLESHOOT_RE.search(answer):
                add_finding(findings, "fail", "troubleshooting_not_diagnostic", "maintenance/troubleshooting answer lacks check/test/isolate/safety guidance")
        elif not MAINTENANCE_ACTION_RE.search(answer):
            add_finding(findings, "warn", "maintenance_action_missing", "maintenance answer lacks concrete action or safety guidance")
        if re.search(r"\b(?:amp|hum|buzz|electrical)\b", question, re.I) and not re.search(r"\b(?:qualified|tech|safety|danger|unplug|ground|cable|outlet)\b", answer, re.I):
            add_finding(findings, "warn", "amp_safety_context_missing", "amp/electrical troubleshooting should mention safe isolation or qualified tech help")

    elif family == "brand comparison":
        if not BRAND_COMPARE_RE.search(answer):
            add_finding(findings, "fail", "brand_comparison_too_absolute", "brand comparison should avoid a universal winner and compare fit/condition/tone/mechanics/support")

    elif family == "vendor/buying":
        if not VENDOR_RE.search(answer):
            add_finding(findings, "fail", "vendor_guidance_missing", "vendor/buying answer lacks dealer/vendor/current availability guidance")
        if RAW_JUNK_RE.search(answer):
            add_finding(findings, "fail", "vendor_contact_order_junk", "vendor/buying answer contains contact, PayPal, order, or raw-link junk")

    elif family == "song/tab/guardrail":
        if re.search(r"\bfull lyrics\b", question, re.I) and not re.search(r"\b(?:can't|cannot|not provide|won't provide|summary)\b", answer, re.I):
            add_finding(findings, "fail", "lyrics_guardrail_missing", "lyrics request did not clearly avoid providing full lyrics")
        if not SONG_GUARDRAIL_RE.search(answer):
            add_finding(findings, "warn", "song_learning_low_guidance", "song/tab answer lacks approach, style, chord, original exercise, or public-domain guidance")

    elif family == "sensitive identity/current roster":
        if SENSITIVE_IDENTITY_RE.search(question) and not re.search(r"\b(?:don't use|avoid|not appropriate|focus on|instrument|color|gear)\b", answer, re.I):
            add_finding(findings, "fail", "sensitive_identity_not_handled", "sensitive identity phrasing was not redirected safely")

    if question_mentions_private_profile(question):
        if not any(is_private_source_card(source) for source in sources) and not PRIVATE_PROFILE_RE.search(answer):
            add_finding(findings, "warn", "personal_setup_without_private_source", "personal setup question did not use private profile/source evidence")
    elif PRIVATE_PROFILE_RE.search(answer):
        add_finding(findings, "warn", "unrelated_private_profile_fact", "answer mentions private profile facts for a non-personal question")

    if first and len(first.split()) > 55:
        add_finding(findings, "warn", "first_sentence_too_long", "first sentence is too long for a direct answer")


def evaluate_e_lower_578_b9_disclosure(question: str, answer: str, findings: list[QualityFinding]) -> None:
    if not E_LOWER_578_B9_QUESTION_RE.search(question or ""):
        return
    if not B9_NEGATION_RE.search(answer or ""):
        add_finding(
            findings,
            "fail",
            "e_lower_578_b9_misclassification",
            "5-7-8 E-lower B9-pocket answer did not clearly reject B9 classification under current pitch rules",
        )
    if not E_LOWER_578_DISCLOSURE_RE.search(answer or ""):
        add_finding(
            findings,
            "fail",
            "missing_rootless_partial_disclosure",
            "5-7-8 E-lower B9-pocket answer should disclose D major plus rootless B minor 7 color",
        )


def answer_mentions_expected_minor_function(answer: str) -> bool:
    return bool(re.search(r"\b(?:E\s+minor|Em)\b", answer or "", re.I))


def evaluate_chord_position_router_escape_response(
    *,
    question: str,
    answer: str,
    warnings: list[str],
    sources: list[dict[str, Any]],
    payload: dict[str, Any],
    findings: list[QualityFinding],
) -> None:
    if not is_chord_position_router_escape_question(question):
        return

    if WEAK_SOURCE_CHORD_ROUTE_RE.search(answer) or any(WEAK_SOURCE_CHORD_ROUTE_RE.search(warning) for warning in warnings):
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            "router-escape answer exposed weak-source fallback language",
        )
    if RAW_CHORD_FRAGMENT_RE.search(answer) or INTERNAL_LANGUAGE_RE.search(answer) or FORUM_FRAGMENT_RE.search(answer):
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            "router-escape answer appears to contain SGF/source fragment text",
        )
    if sources:
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            "router-escape answer returned source cards instead of a deterministic no-source answer",
        )
    if not has_fretboard_payload(payload):
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            "router-escape visualizable chord/function answer did not include response.fretboard",
        )

    if MINOR_FUNCTION_ROUTER_ESCAPE_RE.search(question or ""):
        if not answer_mentions_expected_minor_function(answer):
            add_finding(
                findings,
                "fail",
                "chord_position_router_escape",
                "router-escape function/minor answer did not resolve the request to E minor",
            )
        return

    request = requested_chord_position_request(question)
    if request is None:
        return
    if not answer_mentions_required_major_positions(answer, request.normalized_key):
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            f"router-escape {request.normalized_key} chord answer did not include deterministic fret positions",
        )
    if has_fretboard_payload(payload) and not fretboard_payload_has_expected_chord_positions(payload, request.normalized_key):
        add_finding(
            findings,
            "fail",
            "chord_position_router_escape",
            f"router-escape fretboard omitted expected {request.normalized_key} positions",
        )


def evaluate_quality_result(
    row: dict[str, str],
    *,
    status_code: int,
    payload: dict[str, Any],
    access_role: str = "beta_user",
) -> QualityResult:
    answer = str(payload.get("answer") or payload.get("error") or "")
    warnings = [str(warning) for warning in (payload.get("warnings") or [])]
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    sources = [source for source in sources if isinstance(source, dict)]
    expected_intent = normalize_intent(infer_expected_intent(row["question"], row.get("expected_intent", "")))
    findings: list[QualityFinding] = []

    if status_code != 200:
        add_finding(findings, "fail", "http_error", f"HTTP status {status_code}")
    if not answer.strip():
        add_finding(findings, "fail", "empty_answer", "answer body is empty")
    if answer and len(answer.strip()) < 80 and not fallback_expected(row):
        add_finding(findings, "warn", "answer_too_short", "answer is too short for a useful product answer")

    first = first_sentence(answer)
    if not first:
        add_finding(findings, "fail", "missing_direct_first_sentence", "answer lacks a direct first sentence")
    elif DIRECTNESS_BAD_START_RE.search(first):
        add_finding(findings, "warn", "weak_direct_first_sentence", "first sentence starts with caveat/internal/source framing")
    if not answer_mentions_question_subject(row["question"], answer):
        add_finding(findings, "warn", "subject_not_named", "answer does not clearly name the asked-about subject")

    if INTERNAL_LANGUAGE_RE.search(answer):
        add_finding(findings, "fail", "internal_implementation_language", "answer exposes internal retrieval/source-card language")
    if RAW_JUNK_RE.search(answer):
        add_finding(findings, "fail", "raw_contact_order_link_junk", "answer contains PayPal/contact/order/raw-link junk")
    if FORUM_FRAGMENT_RE.search(answer):
        add_finding(findings, "fail", "raw_forum_fragment", "answer contains username/date forum fragment")
    if WEAK_SOURCE_CHORD_ROUTE_RE.search(answer) or any(WEAK_SOURCE_CHORD_ROUTE_RE.search(warning) for warning in warnings):
        add_finding(findings, "fail", "weak_source_leakage", "answer or warning visibly says source support was weak")
    if "[object Object]" in answer:
        add_finding(findings, "fail", "object_object_rendering_failure", "answer rendered an object as [object Object]")
        add_finding(findings, "fail", "object_object_rendering", "answer rendered an object as [object Object]")
    if re.search(r"\[\d+\]", answer):
        add_finding(findings, "warn", "inline_citation_marker", "answer contains inline numeric citation markers")
    if not fallback_expected(row) and not ACTION_RE.search(answer) and category_family(row) not in {"player/teacher bio", "subjective ranking"}:
        add_finding(findings, "warn", "low_actionable_teaching_value", "answer has low actionable teaching value")

    legacy_failures = evaluate_answer(
        row["question"],
        answer,
        warnings,
        len(sources),
        status_code,
        row.get("expected_intent", ""),
        row.get("expected_contract", ""),
    )
    for legacy in legacy_failures:
        severity: Severity = "fail"
        if legacy.group == "source weakness / no-source" and fallback_expected(row) and fallback_quality_is_good(answer):
            severity = "warn"
        if legacy.group == "source weakness / no-source" and is_deterministic_pitch_rule_question(row["question"]):
            continue
        add_finding(findings, severity, f"legacy_{legacy.group.replace(' ', '_').replace('/', '_')}", legacy.reason)

    directness_findings: list[Any] = []
    add_directness_failures(row["question"], answer, expected_intent, directness_findings)
    for directness in directness_findings:
        add_finding(findings, "fail", f"directness_{directness.group.replace(' ', '_').replace('/', '_')}", directness.reason)

    evaluate_deterministic_chord_position_response(
        question=row["question"],
        answer=answer,
        warnings=warnings,
        sources=sources,
        payload=payload,
        findings=findings,
    )
    evaluate_chord_position_router_escape_response(
        question=row["question"],
        answer=answer,
        warnings=warnings,
        sources=sources,
        payload=payload,
        findings=findings,
    )
    evaluate_beginner_minor_chord_concept_response(
        question=row["question"],
        answer=answer,
        warnings=warnings,
        sources=sources,
        payload=payload,
        findings=findings,
    )
    if is_deterministic_pitch_rule_question(row["question"]) and not has_fretboard_payload(payload):
        add_finding(
            findings,
            "fail",
            "deterministic_visual_missing_fretboard",
            "visualizable deterministic question did not include response.fretboard",
        )
    evaluate_practical_advice_response(
        row=row,
        answer=answer,
        warnings=warnings,
        findings=findings,
    )
    evaluate_source_cards(row=row, sources=sources, access_role=access_role, findings=findings)
    evaluate_category_specific(row, answer, sources, findings)

    deduped: list[QualityFinding] = []
    seen: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding.severity, finding.key, finding.message)
        if key not in seen:
            seen.add(key)
            deduped.append(finding)

    return QualityResult(
        id=row["id"],
        category=row["category"],
        category_family=category_family(row),
        question=row["question"],
        expected_intent=row.get("expected_intent", ""),
        expected_contract=row.get("expected_contract", ""),
        status_code=status_code,
        answer=answer,
        warnings=warnings,
        sources=sources,
        findings=deduped,
    )


def post_answer(base_url: str, question: str, *, top_k: int, access_role: str) -> tuple[int, dict[str, Any]]:
    payload = json.dumps({"question": question, "mode": "ask", "topK": top_k}).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if access_role:
        headers[DEV_ACCESS_ROLE_HEADER] = access_role
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/answer",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}
    except (TimeoutError, urllib.error.URLError) as exc:
        return 0, {"error": str(exc)}


def run_http_eval(base_url: str, questions: list[dict[str, str]], *, top_k: int, access_role: str) -> list[QualityResult]:
    results: list[QualityResult] = []
    for index, row in enumerate(questions, 1):
        print(f"[{index}/{len(questions)}] {row['id']} {row['question']}", flush=True)
        status_code, payload = post_answer(base_url, row["question"], top_k=top_k, access_role=access_role)
        results.append(evaluate_quality_result(row, status_code=status_code, payload=payload, access_role=access_role))
    return results


def build_protected_preview_app(args: argparse.Namespace) -> Any:
    rerank_config = RerankConfig(
        candidate_k=args.candidate_k,
        min_excerpt_chars=args.min_excerpt_chars,
        dedupe_thread=not args.no_dedupe_thread,
        question_only_penalty=args.question_only_penalty,
        mention_only_penalty=args.mention_only_penalty,
        answer_advice_boost=args.answer_advice_boost,
        quality_boost=args.quality_boost,
        quality_threshold=args.quality_threshold,
        noise_penalty=args.noise_penalty,
        noise_threshold=args.noise_threshold,
    )
    sgf_index = RerankedSearchIndex(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.sgf_chroma_path,
            collection_name=args.sgf_collection,
        ),
        rerank_config,
    )
    private_index = PrivateSourceSearchIndex.from_chroma(
        chroma_path=args.private_chroma_path,
        collection_name=args.private_collection,
    )
    retrieval_config = RetrievalModeConfig(
        requested_mode=RetrievalMode.HYBRID_PRIVATE_FIRST,
        private_sources_enabled=True,
        sgf_chroma_path=args.sgf_chroma_path,
        sgf_collection=args.sgf_collection,
        private_chroma_path=args.private_chroma_path,
        private_collection=args.private_collection,
        expose_debug_metadata=False,
    )
    return create_app(
        sgf_index,
        answer_auth_mode="local_dev",
        auth_provider="scaffold",
        answer_rate_limiter=InMemoryAnswerRateLimiter(enabled=False),
        private_search_index=private_index,
        retrieval_config=retrieval_config,
    )


def result_sort_key(result: QualityResult) -> tuple[int, int, str]:
    outcome_rank = {"fail": 0, "warn": 1, "pass": 2}
    fail_count = sum(1 for finding in result.findings if finding.severity == "fail")
    return (outcome_rank[result.outcome], -fail_count, result.id)


def summarize_results(results: list[QualityResult]) -> dict[str, Any]:
    outcome_counts = Counter(result.outcome for result in results)
    category_counts: dict[str, Counter[str]] = defaultdict(Counter)
    family_counts: dict[str, Counter[str]] = defaultdict(Counter)
    finding_counts = Counter()
    private_cards = 0
    unauthorized_private = 0
    private_rows = 0
    no_source_rows = 0
    for result in results:
        category_counts[result.category][result.outcome] += 1
        family_counts[result.category_family][result.outcome] += 1
        no_source_rows += int(len(result.sources) == 0)
        private_cards += result.private_source_count
        if result.private_source_count:
            private_rows += 1
        for finding in result.findings:
            finding_counts[f"{finding.severity}:{finding.key}"] += 1
            if finding.key == "unauthorized_private_source":
                unauthorized_private += 1

    return {
        "total_questions": len(results),
        "outcome_counts": {key: outcome_counts[key] for key in ("pass", "warn", "fail")},
        "category_counts": {category: dict(counts) for category, counts in sorted(category_counts.items())},
        "category_family_counts": {family: dict(counts) for family, counts in sorted(family_counts.items())},
        "finding_counts": dict(finding_counts.most_common()),
        "private_source_behavior": {
            "private_source_cards": private_cards,
            "answers_with_private_sources": private_rows,
            "unauthorized_private_source_findings": unauthorized_private,
            "no_source_answers": no_source_rows,
            "behaved_correctly": unauthorized_private == 0,
        },
    }


def recommended_fixes(finding_counts: Counter[str]) -> list[str]:
    fixes: list[str] = []
    if any("unrelated_private_profile_fact" in key for key in finding_counts):
        fixes.append("Tighten hybrid routing so private E9 profile facts appear only for personal setup questions or clearly labeled personalization.")
    if any("source_excerpt_junk" in key or "raw_contact_order_link_junk" in key for key in finding_counts):
        fixes.append("Strengthen final answer/source-card cleanup for contact, PayPal, order, raw-link, and username/date fragments.")
    if any("missing_sources" in key or "weak_source_card_usefulness" in key for key in finding_counts):
        fixes.append("Improve retrieval/rerank thresholds for source-card usefulness before answer generation.")
    if any("bio_too_thin" in key or "bio_missing_subject" in key for key in finding_counts):
        fixes.append("Add player/teacher bio routing or curated public registry entries for thin biography answers.")
    if any("practice_not_actionable" in key or "low_actionable_teaching_value" in key for key in finding_counts):
        fixes.append("Strengthen practice and teaching templates to produce concrete steps without exposing internal source language.")
    if any("vendor_guidance_missing" in key or "gear_buying_context_missing" in key for key in finding_counts):
        fixes.append("Route buying/vendor questions to curated current-source guidance and avoid stale forum sales fragments.")
    if any(any(bucket in key for bucket in DETERMINISTIC_CHORD_POSITION_FAILURE_BUCKETS) for key in finding_counts):
        fixes.append("Route chord-position/location questions through deterministic key-aware E9 positions before retrieval, require fretboard payloads, and suppress SGF source cards.")
    if not fixes:
        fixes.append("Review warning samples manually; no dominant automatic failure pattern exceeded the strict checks.")
    return fixes


def result_to_json(result: QualityResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "category": result.category,
        "category_family": result.category_family,
        "question": result.question,
        "expected_intent": result.expected_intent,
        "expected_contract": result.expected_contract,
        "status_code": result.status_code,
        "outcome": result.outcome,
        "answer": result.answer,
        "answer_excerpt": excerpt(result.answer),
        "warnings": result.warnings,
        "source_count": len(result.sources),
        "private_source_count": result.private_source_count,
        "sources": result.sources,
        "findings": [
            {"severity": finding.severity, "key": finding.key, "message": finding.message}
            for finding in result.findings
        ],
    }


def render_result_list(results: list[QualityResult], *, limit: int) -> list[str]:
    lines: list[str] = []
    for result in results[:limit]:
        reasons = "; ".join(f"{finding.severity}:{finding.message}" for finding in result.findings) or "pass"
        first_source = result.sources[0] if result.sources else {}
        lines.extend(
            [
                f"### {result.id} · {result.outcome}",
                "",
                f"- Category: `{result.category}` / `{result.category_family}`",
                f"- Question: {result.question}",
                f"- Status: {result.status_code}",
                f"- Sources: {len(result.sources)} (private: {result.private_source_count})",
                f"- First source: {first_source.get('forumName') or ''} · {first_source.get('title') or ''} · {first_source.get('url') or ''}",
                f"- Findings: {reasons}",
                f"- Answer excerpt: {excerpt(result.answer)}",
                "",
            ]
        )
    if not lines:
        lines.append("None.")
    return lines


def render_markdown_report(
    results: list[QualityResult],
    *,
    question_bank: Path,
    base_url: str,
    config: dict[str, Any],
) -> str:
    summary = summarize_results(results)
    finding_counter = Counter(summary["finding_counts"])
    worst_failures = sorted([result for result in results if result.outcome == "fail"], key=result_sort_key)[:25]
    top_warnings = sorted([result for result in results if result.outcome == "warn"], key=lambda result: (-len(result.findings), result.id))[:25]
    excellent = [
        result
        for result in results
        if result.outcome == "pass" and len(result.answer) >= 160 and result.sources and not result.warnings
    ][:25]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Full Answer Quality Eval",
        "",
        f"Generated: {now}",
        f"Question bank: `{question_bank}`",
        f"Local base URL: `{base_url}`",
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
            f"- Answers with no source cards: {summary['private_source_behavior']['no_source_answers']}",
            f"- Answers with private source cards: {summary['private_source_behavior']['answers_with_private_sources']}",
            f"- Private source cards: {summary['private_source_behavior']['private_source_cards']}",
            f"- Unauthorized private-source findings: {summary['private_source_behavior']['unauthorized_private_source_findings']}",
            f"- Private-source behavior correct: `{summary['private_source_behavior']['behaved_correctly']}`",
            "",
            "## Failures By Category",
            "",
            "| Category | Pass | Warn | Fail |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for category, counts in summary["category_counts"].items():
        lines.append(f"| {category} | {counts.get('pass', 0)} | {counts.get('warn', 0)} | {counts.get('fail', 0)} |")

    lines.extend(["", "## Failures By Category Family", "", "| Family | Pass | Warn | Fail |", "| --- | ---: | ---: | ---: |"])
    for family, counts in summary["category_family_counts"].items():
        lines.append(f"| {family} | {counts.get('pass', 0)} | {counts.get('warn', 0)} | {counts.get('fail', 0)} |")

    lines.extend(["", "## Repeated Failure Patterns", ""])
    for key, count in finding_counter.most_common(30):
        lines.append(f"- {key}: {count}")
    if not finding_counter:
        lines.append("- none")

    lines.extend(["", "## Top 25 Worst Answers", ""])
    lines.extend(render_result_list(worst_failures, limit=25))

    lines.extend(["", "## Top 25 Warnings", ""])
    lines.extend(render_result_list(top_warnings, limit=25))

    lines.extend(["", "## Examples Of Excellent Answers", ""])
    lines.extend(render_result_list(excellent, limit=25))

    lines.extend(["", "## Recommended Next Fixes", ""])
    for fix in recommended_fixes(finding_counter):
        lines.append(f"- {fix}")

    lines.extend(
        [
            "",
            "## Private-Source Behavior",
            "",
            (
                "Private-source cards behaved correctly under this local-dev authorized run."
                if summary["private_source_behavior"]["behaved_correctly"]
                else "Private-source authorization findings were detected and need review before broader testing."
            ),
            "",
            "This eval started a loopback-only local app in `local_dev` mode with `beta_user` access and did not change production/private-preview auth configuration.",
            "",
        ]
    )
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Loopback port. 0 chooses a free ephemeral port.")
    parser.add_argument("--question-bank", type=Path, default=DEFAULT_QUESTION_BANK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--access-role", default="beta_user", choices=["beta_user", "admin"])
    parser.add_argument("--sgf-chroma-path", type=Path, default=DEFAULT_SGF_V2_CHROMA_PATH)
    parser.add_argument("--sgf-collection", default=DEFAULT_SGF_V2_COLLECTION)
    parser.add_argument("--private-chroma-path", type=Path, default=DEFAULT_PRIVATE_CHROMA_PATH)
    parser.add_argument("--private-collection", default=DEFAULT_PRIVATE_COLLECTION)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--min-excerpt-chars", type=int, default=80)
    parser.add_argument("--no-dedupe-thread", action="store_true")
    parser.add_argument("--question-only-penalty", type=float, default=0.12)
    parser.add_argument("--mention-only-penalty", type=float, default=0.20)
    parser.add_argument("--answer-advice-boost", type=float, default=0.04)
    parser.add_argument("--quality-boost", type=float, default=0.04)
    parser.add_argument("--quality-threshold", type=float, default=0.70)
    parser.add_argument("--noise-penalty", type=float, default=0.06)
    parser.add_argument("--noise-threshold", type=float, default=0.60)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.host != "127.0.0.1":
        raise SystemExit("full answer-quality eval must bind to 127.0.0.1 only")
    if args.top_k <= 0:
        raise SystemExit("--top-k must be greater than zero")
    if args.candidate_k <= 0:
        raise SystemExit("--candidate-k must be greater than zero")
    if args.min_excerpt_chars < 0:
        raise SystemExit("--min-excerpt-chars must be zero or greater")

    questions = load_question_bank(args.question_bank)
    if args.limit is not None:
        questions = questions[: max(0, args.limit)]

    app = build_protected_preview_app(args)
    server: WSGIServer = make_server(args.host, args.port, app)
    host, port = server.server_address[:2]
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        results = run_http_eval(base_url, questions, top_k=args.top_k, access_role=args.access_role)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    config = {
        "sgf_chroma_path": args.sgf_chroma_path,
        "sgf_collection": args.sgf_collection,
        "private_chroma_path": args.private_chroma_path,
        "private_collection": args.private_collection,
        "retrieval_mode": "hybrid_private_first",
        "answer_auth_mode": "local_dev",
        "access_role": args.access_role,
        "top_k": args.top_k,
        "candidate_k": args.candidate_k,
        "min_excerpt_chars": args.min_excerpt_chars,
        "dedupe_thread": not args.no_dedupe_thread,
    }
    summary = summarize_results(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_markdown_report(results, question_bank=args.question_bank, base_url=base_url, config=config),
        encoding="utf-8",
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
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

    print(f"Evaluated {len(results)} questions against local protected-preview stack at {base_url}")
    for outcome in ("pass", "warn", "fail"):
        print(f"{outcome}: {summary['outcome_counts'][outcome]}")
    print(f"Private-source behavior correct: {summary['private_source_behavior']['behaved_correctly']}")
    print(f"Markdown report: {args.output}")
    print(f"JSON report: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
