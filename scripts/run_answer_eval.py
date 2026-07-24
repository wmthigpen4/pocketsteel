#!/usr/bin/env python3
"""Run a local answer-quality evaluation against POST /api/answer."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from steel_guitar_rag.answer_contracts import normalize_intent, validate_answer_against_contract


DEFAULT_BASE_URL = "http://127.0.0.1:8770"
DEFAULT_QUESTION_BANK = Path("tests/fixtures/user_question_bank.json")
DEFAULT_OUTPUT = Path("docs/answer-eval-report.md")
DEFAULT_JSON_OUTPUT = Path("/tmp/answer-eval-results.json")
DEFAULT_DEV_ACCESS_ROLE = "beta_user"

REPORT_GROUPS = [
    "likely_intent_mismatch",
    "likely_directness_failure",
    "likely routing failure",
    "likely formatting failure",
    "likely retrieval mismatch",
    "source weakness / no-source",
    "possible safety issue",
    "pass",
]

FORMAT_PATTERNS = [
    ("internal fallback language: cleanest source-backed answer", re.compile(r"\bThe cleanest source-backed answer\b", re.I)),
    ("internal fallback language: source cards as supporting evidence", re.compile(r"\bsource cards as supporting evidence\b", re.I)),
    ("internal fallback language: Useful distilled points", re.compile(r"\bUseful distilled points\b", re.I)),
    ("internal fallback language: related practical points", re.compile(r"\bI found a few related practical points\b", re.I)),
    ("internal fallback language: match is limited", re.compile(r"\bmatch is limited\b", re.I)),
    ("banned product template: retrieved sources discuss that product", re.compile(r"\bThe retrieved sources discuss that product\b", re.I)),
    (
        "banned product template: use source cards before buying",
        re.compile(r"\bUse the source cards for exact model/version details before buying\b", re.I),
    ),
    ("banned product template: positive owner/source impression", re.compile(r"\bpositive owner/source impression\b", re.I)),
    ("banned phrase: Concise answer:", re.compile(r"\bConcise answer:", re.I)),
    ("banned phrase: What multiple sources support", re.compile(r"\bWhat multiple sources support\b", re.I)),
    ("banned phrase: Source context:", re.compile(r"\bSource context:", re.I)),
    ("banned phrase: Forum-source context", re.compile(r"\bForum-source context\b", re.I)),
    ("banned phrase: For RAG answers", re.compile(r"\bFor RAG answers\b", re.I)),
    ("answer starts with Top", re.compile(r"^\s*Top\b", re.I)),
    ("banned phrase: spaced Top", re.compile(r"\sTop\s", re.I)),
    ("banned phrase: Top Does", re.compile(r"\bTop Does\b", re.I)),
    ("banned phrase: Anne Top", re.compile(r"\bAnne Top\b", re.I)),
    ("raw link share fragment: sp=sharing", re.compile(r"\bsp=sharing\b", re.I)),
    ("raw cleaned link marker", re.compile(r"\[link removed\]", re.I)),
    ("raw email address", re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)),
    ("raw e-mail contact", re.compile(r"\be-?mail\s+", re.I)),
    ("forum question fragment: Does anyone know", re.compile(r"\bDoes anyone know\b", re.I)),
    ("forum question fragment: Has anyone compared", re.compile(r"\bHas anyone compared\b", re.I)),
    ("forum tab request fragment", re.compile(r"\bI am looking for tablature\b", re.I)),
    ("raw forum junk: Thanks Nick", re.compile(r"\bThanks Nick\b", re.I)),
    ("raw forum junk: Top Hi All", re.compile(r"\bTop Hi All\b", re.I)),
    ("first-person forum statement as answer voice", re.compile(r"(?m)^\s*[-*]?\s*(?:I|My)\s+(?:play|use|had|never|rarely|usually|bought|think|guess)\b", re.I)),
    ("chopped first-person source fragment", re.compile(r"\bother hand I rarely\b", re.I)),
    ("raw PayPal/order fragment", re.compile(r"\b(?:PayPal|order\s+(?:form|page|link|online|through))\b", re.I)),
    ("raw live-sound chatter: tell the sound guy", re.compile(r"\btell\s+the\s+sound\s+guy\b", re.I)),
    ("raw live-sound chatter: bite ya", re.compile(r"\bbite\s+ya\b", re.I)),
    ("raw live-sound chatter: road-case/speaker/mic fragment", re.compile(r"\b(?:road\s+cases?|speakers?\s+stay\s+inside|with\s+mics?)\b", re.I)),
    ("blanket copyrighted-material refusal", re.compile(r"\b(?:cannot|can't|do not|won't)\s+(?:discuss|talk about|help with)\s+copyrighted\b", re.I)),
    ("orphan Practical answer heading", re.compile(r"(?m)^\s*Practical answer\s*:?\s*$", re.I)),
    (
        "empty heading: What players seem to like",
        re.compile(r"(?im)^\s*What players seem to like\s*:?\s*(?:\n\s*(?:$|#{1,6}\s|\w[^:\n]{0,80}:)|$)"),
    ),
    ("inline citation marker", re.compile(r"\[\d+\]")),
    (
        "username/date boilerplate",
        re.compile(
            r"\b[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){0,3}\s*/\s*\d{1,2}\s+"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}",
            re.I,
        ),
    ),
    (
        "date-like boilerplate",
        re.compile(
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}"
            r"(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)?",
            re.I,
        ),
    ),
    ("forum profile boilerplate", re.compile(r"\b(?:Posts|Joined|Location|State/Province|Country)\s*:", re.I)),
]

RANKING_TERMS = re.compile(r"\b(top|best|greatest|ranking|rankings|ranked|most influential|most important)\b", re.I)
RANKING_LANGUAGE = re.compile(r"\bRankings are subjective\b|\btop\s+\d+\b|\bbest steel players\b", re.I)
PLAYER_NAMES = re.compile(
    r"\b(Buddy Emmons|Lloyd Green|Paul Franklin|Jimmy Day|Ralph Mooney|Curly Chalker|John Hughey|"
    r"Tom Brumley|Maurice Anderson|Reece Anderson|Doug Jernigan|Weldon Myrick|Hal Rugg|Pete Drake)\b",
    re.I,
)
HOSTILE_QUESTION = re.compile(
    r"\bignore\s+(?:all\s+)?previous\s+instructions?\b|\breveal\s+(?:your\s+)?(?:prompt|hidden rules)\b|"
    r"\bprint\s+(?:your\s+)?system\s+prompt\b|\bfollow\s+this\s+link\b|\boverride\s+(?:your\s+)?rules?\b|"
    r"\byou\s+are\s+now\b|\boutput\s+only\b",
    re.I,
)
PRODUCT_VALUE_QUESTION = re.compile(r"\b(worth|worth buying|good value|should i buy|is .+ good|better)\b", re.I)
PLAYER_BRAND_USAGE_QUESTION = re.compile(
    r"\b(?:who|which)\s+(?:players?|people|pros|steel players?)\s+(?:play|plays|use|uses)\s+(?:an?\s+)?(?P<brand>[A-Z][A-Za-z0-9-]+)",
    re.I,
)
BUYING_QUESTION = re.compile(r"\bwhere\s+can\s+i\s+buy\b|\bwhat\s+brands\s+make\b", re.I)
BRAND_COMPARISON_QUESTION = re.compile(
    r"\b(?:is|are|should)\b.*\b(?P<a>Mullen|MSA|Emmons|Sho-Bud|ZumSteel|Carter|GFI|Sierra)\b.*\b(?:or|than|vs\.?|versus|and)\b.*\b(?P<b>Mullen|MSA|Emmons|Sho-Bud|ZumSteel|Carter|GFI|Sierra)\b",
    re.I,
)
COMPANY_STATUS_QUESTION = re.compile(r"\b(?:still\s+in\s+business|in business today|company status|operating today)\b", re.I)
PERSON_BIO_QUESTION = re.compile(r"^\s*who\s+is\s+[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)+\??\s*$", re.I)
TECHNIQUE_IMPROVEMENT_QUESTION = re.compile(
    r"\b(?:sound less mechanical|sounds mechanical|sound more musical|less stiff|fills? sound better|play with more feeling|sound less robotic)\b",
    re.I,
)
DIAGNOSTIC_TROUBLESHOOTING_QUESTION = re.compile(
    r"\b(?:amp\s+(?:buzz|buzzes|hum|hums)|buzz\s+at\s+idle|amp\s+hum|hums?\s+until\s+i\s+touch|noise\s+when\s+nothing\s+is\s+plugged\s+in|ground\s+buzz|touching\s+(?:the\s+)?(?:strings?|changer).*(?:buzz|hum))\b",
    re.I,
)
TONE_TOUCH_QUESTION = re.compile(
    r"\b(?:soften\s+my\s+attack|attack\s+is\s+too\s+hard|sound\s+less\s+harsh|pick\s+attack\s+(?:sounds\s+)?too\s+sharp|play\s+with\s+softer\s+touch)\b",
    re.I,
)
SONG_LEARNING_QUESTION = re.compile(
    r"\b(?:tab|tablature|lyrics?|approach playing|explain the style of|chord progression|original e9 lick|song arrangement|together again|amazing grace|slow country ballad)\b",
    re.I,
)
PRACTICE_QUESTION = re.compile(r"\bpractice\b|\bwhat should i work on\b", re.I)
COPEDENT_QUESTION = re.compile(r"\b(?:A\+B|B\+C|A\+F|pedal|lever|fret|chord|E9|copedent|string)\b", re.I)
MAINTENANCE_QUESTION = re.compile(r"\b(?:oil|lubricate|changer|pedal rods|nylon tuner|cabinet drop|adjust|clean|return)\b", re.I)
COMPANY_STATUS_LANGUAGE = re.compile(r"\b(company|co\.|guitar co|in business|operating|owner|website|factory|production|founded)\b", re.I)
PLAYER_USAGE_LANGUAGE = re.compile(r"\b(players?|users?|used by|played by|plays? (?:an? )?[A-Z][A-Za-z0-9-]+|uses? (?:an? )?[A-Z][A-Za-z0-9-]+)\b", re.I)
WEAK_SOURCE_LANGUAGE = re.compile(r"\b(source support is weak|sources are weak|not enough source|did not find strong|current players)\b", re.I)
VENDOR_LANGUAGE = re.compile(r"\b(buy|dealer|vendor|source|order|shop|store|classifieds?|for sale|used market|manufacturer|maker|contact|website|retailer|brand)\b", re.I)
GENERIC_PRODUCT_TEMPLATE = re.compile(
    r"\b(that product|retrieved sources discuss that product|exact model/version details|positive owner/source impression|"
    r"Conditionally: it may be worth considering|I did not find strong negative evidence)\b",
    re.I,
)
NO_UNIVERSAL_WINNER_LANGUAGE = re.compile(
    r"\b(no universal winner|depends|fit|condition|tone|mechanics|budget|support|copedent|try both|personal preference)\b",
    re.I,
)


@dataclass
class Failure:
    group: str
    reason: str


@dataclass
class EvalResult:
    id: str
    category: str
    question: str
    expected_intent: str
    expected_contract: str
    status_code: int
    answer: str
    warnings: list[str]
    source_count: int
    first_source_title: str = ""
    first_source_forum: str = ""
    first_source_url: str = ""
    failures: list[Failure] = field(default_factory=list)

    @property
    def group(self) -> str:
        if not self.failures:
            return "pass"
        priority = {group: index for index, group in enumerate(REPORT_GROUPS)}
        return min((failure.group for failure in self.failures), key=lambda group: priority.get(group, 99))


def load_question_bank(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list):
        raise ValueError(f"{path} must contain a questions list.")
    rows = []
    for index, item in enumerate(questions, 1):
        if not isinstance(item, dict) or not str(item.get("question") or "").strip():
            raise ValueError(f"{path}: invalid question row at {index}.")
        rows.append(
            {
                "id": str(item.get("id") or f"Q{index:03d}"),
                "category": str(item.get("category") or "uncategorized"),
                "question": str(item["question"]).strip(),
                "expected_intent": str(item.get("expected_intent") or "").strip(),
                "expected_contract": str(item.get("expected_contract") or "").strip(),
            }
        )
    return rows


def post_answer(base_url: str, question: str, *, dev_access_role: str = DEFAULT_DEV_ACCESS_ROLE) -> tuple[int, dict[str, Any]]:
    payload = json.dumps({"question": question}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/answer",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Steel-Rag-Dev-Access-Role": dev_access_role,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"error": body}
        return exc.code, payload
    except (TimeoutError, urllib.error.URLError) as exc:
        return 0, {"error": str(exc)}


def is_ranking_question(question: str) -> bool:
    return bool(RANKING_TERMS.search(question))


def add_failure(failures: list[Failure], group: str, reason: str) -> None:
    failures.append(Failure(group=group, reason=reason))


def has_practice_plan(answer: str) -> bool:
    return bool(re.search(r"\bpractice\b|\bplan\b|\broutine\b|\b\d+\.\s+\w+", answer, re.I))


def has_technique_improvement_guidance(answer: str) -> bool:
    return bool(
        re.search(
            r"\b(?:phrasing|timing|space|bar control|vibrato|blocking|volume[- ]pedal|dynamics|singer|backing track)\b",
            answer,
            re.I,
        )
    )


def has_diagnostic_troubleshooting_guidance(answer: str) -> bool:
    return bool(
        re.search(r"\b(?:nothing plugged in|signal chain|cable|volume pedal|effects?|one at a time|qualified amp tech|safety)\b", answer, re.I)
        and re.search(r"\b(?:step|check|test|isolate|swap|add|diagnostic)\b", answer, re.I)
    )


def has_tone_touch_guidance(answer: str) -> bool:
    concrete_terms = re.findall(
        r"\b(?:right-hand|pick force|pick attack|volume pedal|blocking|bar|vibrato|treble|presence|delay|reverb|practice)\b",
        answer,
        re.I,
    )
    return len({term.lower() for term in concrete_terms}) >= 2


def has_song_learning_guidance(answer: str) -> bool:
    return bool(
        re.search(
            r"\b(?:approach|style|chord|position|practice|public-domain|public domain|original|mini-tab|exercise|full note-for-note|full lyrics)\b",
            answer,
            re.I,
        )
    )


def mentions_a_pedal_and_f_lever(answer: str) -> bool:
    has_a = bool(re.search(r"\bA\s*(?:pedal|\+)", answer, re.I))
    has_f = bool(re.search(r"\bF\s*(?:lever|\+)", answer, re.I))
    return has_a and has_f


def infer_expected_intent(question: str, explicit_intent: str = "") -> str:
    if explicit_intent:
        return explicit_intent
    if PLAYER_BRAND_USAGE_QUESTION.search(question):
        return "player_brand_usage"
    if BUYING_QUESTION.search(question):
        return "vendor_buying_guidance"
    if BRAND_COMPARISON_QUESTION.search(question):
        return "brand_comparison"
    if COMPANY_STATUS_QUESTION.search(question):
        return "current_company_status"
    if PERSON_BIO_QUESTION.search(question):
        return "player_bio"
    if SONG_LEARNING_QUESTION.search(question):
        return "song_learning"
    if DIAGNOSTIC_TROUBLESHOOTING_QUESTION.search(question):
        return "diagnostic_troubleshooting"
    if TONE_TOUCH_QUESTION.search(question):
        return "tone_touch"
    if TECHNIQUE_IMPROVEMENT_QUESTION.search(question):
        return "technique_improvement"
    if PRACTICE_QUESTION.search(question):
        return "practice_plan"
    if COPEDENT_QUESTION.search(question):
        return "copedent_fretboard"
    if MAINTENANCE_QUESTION.search(question):
        return "maintenance_safety"
    if PRODUCT_VALUE_QUESTION.search(question):
        return "product_value"
    return ""


def mentioned_brands(question: str) -> list[str]:
    brands = re.findall(r"\b(Mullen|MSA|Emmons|Sho-Bud|ZumSteel|Carter|GFI|Sierra)\b", question, re.I)
    unique: list[str] = []
    for brand in brands:
        canonical = "MSA" if brand.lower() == "msa" else brand
        if canonical.lower() not in {item.lower() for item in unique}:
            unique.append(canonical)
    return unique


def has_meaningful_player_usage_answer(answer: str) -> bool:
    return bool(PLAYER_USAGE_LANGUAGE.search(answer) or WEAK_SOURCE_LANGUAGE.search(answer))


def answer_mentions_all_brands(answer: str, brands: list[str]) -> bool:
    return all(re.search(rf"\b{re.escape(brand)}\b", answer, re.I) for brand in brands)


def add_directness_failures(question: str, answer: str, expected_intent: str, failures: list[Failure]) -> None:
    brands = mentioned_brands(question)
    if expected_intent == "player_brand_usage":
        if COMPANY_STATUS_LANGUAGE.search(answer) and not has_meaningful_player_usage_answer(answer):
            add_failure(
                failures,
                "likely_intent_mismatch",
                "player-brand usage question answered as company status",
            )
        if not has_meaningful_player_usage_answer(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "player-brand usage answer did not mention players/users or weak current-player support",
            )
    elif expected_intent == "vendor_buying_guidance":
        if GENERIC_PRODUCT_TEMPLATE.search(answer):
            add_failure(failures, "likely_intent_mismatch", "buying/vendor question used product-value template")
        if not VENDOR_LANGUAGE.search(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "buying/vendor question did not give buying/source/vendor guidance",
            )
    elif expected_intent == "brand_comparison":
        if GENERIC_PRODUCT_TEMPLATE.search(answer):
            add_failure(failures, "likely_intent_mismatch", "brand comparison used generic product-value template")
        if len(brands) >= 2 and not answer_mentions_all_brands(answer, brands[:2]):
            add_failure(failures, "likely_directness_failure", "brand comparison did not mention both compared brands")
        if not NO_UNIVERSAL_WINNER_LANGUAGE.search(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "brand comparison did not say no universal winner or depends on fit/condition/tone/mechanics/budget/support/copedent",
            )
    elif expected_intent == "current_company_status":
        if not COMPANY_STATUS_LANGUAGE.search(answer):
            add_failure(failures, "likely_directness_failure", "company-status question did not answer current status")
    elif expected_intent == "player_bio":
        if RANKING_LANGUAGE.search(answer):
            add_failure(failures, "likely_intent_mismatch", "player bio question triggered ranking language")
    elif expected_intent == "practice_plan":
        if not has_practice_plan(answer):
            add_failure(failures, "likely_directness_failure", "practice-plan question missing plan/routine language")
        if RANKING_LANGUAGE.search(answer) or PLAYER_NAMES.search(answer):
            add_failure(failures, "likely_intent_mismatch", "practice-plan question returned rankings/player list")
    elif expected_intent == "technique_improvement":
        if not has_technique_improvement_guidance(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "technique-improvement question missing phrasing/timing/dynamics/bar/blocking/space guidance",
            )
        if re.search(r"\b(?:sound guy|bite ya|road cases?|speakers?\s+stay\s+inside|with\s+mics?)\b", answer, re.I):
            add_failure(failures, "likely formatting failure", "technique-improvement answer leaked live-sound forum chatter")
    elif expected_intent == "diagnostic_troubleshooting":
        if not has_diagnostic_troubleshooting_guidance(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "diagnostic troubleshooting answer missing isolation/signal-chain/safety steps",
            )
        if re.match(r"^\s*Does\s+the\b", answer, re.I):
            add_failure(failures, "likely formatting failure", "diagnostic answer opened as a forum question")
    elif expected_intent == "tone_touch":
        if not has_tone_touch_guidance(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "tone/touch answer missing concrete right-hand/volume-pedal/blocking/bar/EQ practice actions",
            )
    elif normalize_intent(expected_intent) == "song_learning":
        if not has_song_learning_guidance(answer):
            add_failure(
                failures,
                "likely_directness_failure",
                "song-learning answer missing approach/style/chord/practice/original/public-domain guidance",
            )


def evaluate_answer(
    question: str,
    answer: str,
    warnings: list[str],
    source_count: int,
    status_code: int,
    expected_intent: str = "",
    expected_contract: str = "",
) -> list[Failure]:
    failures: list[Failure] = []
    explicit_contract_intent = expected_contract or expected_intent
    expected_intent = normalize_intent(infer_expected_intent(question, expected_intent))

    if status_code != 200:
        add_failure(failures, "source weakness / no-source", f"HTTP status {status_code}")
    if source_count == 0 or re.search(r"\bno strong source match\b|\bdid not provide enough evidence\b", answer, re.I):
        add_failure(failures, "source weakness / no-source", "no source-backed answer")

    for reason, pattern in FORMAT_PATTERNS:
        if pattern.search(answer):
            add_failure(failures, "likely formatting failure", reason)

    if explicit_contract_intent:
        contract_validation = validate_answer_against_contract(answer, explicit_contract_intent)
        for violation in contract_validation.violations:
            group = "likely formatting failure" if re.search(r"\b(?:boilerplate|email|citation|context|fragment|template|Top|link|orphan)\b", violation, re.I) else "likely_directness_failure"
            add_failure(failures, group, f"contract {contract_validation.intent}: {violation}")

    if re.search(r"\bI did not find strong negative evidence\b", answer, re.I) and expected_intent != "product_value":
        add_failure(failures, "likely_intent_mismatch", "negative-evidence product-value language on non-product-value question")
    if re.search(r"\bConditionally: it may be worth considering\b", answer, re.I) and expected_intent != "product_value":
        add_failure(failures, "likely_intent_mismatch", "worth-considering product-value language on non-worth-buying question")

    add_directness_failures(question, answer, expected_intent, failures)

    if not is_ranking_question(question) and re.search(r"\bRankings are subjective\b", answer, re.I):
        add_failure(failures, "likely routing failure", "ranking caveat on non-ranking question")

    exact = question.strip().lower()
    if exact == "what is tsga?" and not re.search(r"\bTexas Steel Guitar Association\b", answer, re.I):
        add_failure(failures, "likely retrieval mismatch", "TSGA answer missing Texas Steel Guitar Association")
    if exact == "who is lloyd green?" and RANKING_LANGUAGE.search(answer):
        add_failure(failures, "likely routing failure", "Lloyd Green biography triggered ranking language")
    if exact == "what should i practice tonight?":
        if not has_practice_plan(answer):
            add_failure(failures, "likely routing failure", "practice question missing practice plan")
        if RANKING_LANGUAGE.search(answer) or PLAYER_NAMES.search(answer):
            add_failure(failures, "likely routing failure", "practice question returned player rankings")
    if exact == "what kind of oil is good for my changer?":
        if re.search(r"\b(naphtha|lighter fluid)\b", answer, re.I) and not re.search(r"\bclean(?:er|ing)?\b", answer, re.I):
            add_failure(failures, "possible safety issue", "naphtha/lighter fluid recommended as oil")
    if exact in {"what are the best finger picks?", "what are the best finger picks to buy?"}:
        if PLAYER_NAMES.search(answer):
            add_failure(failures, "likely routing failure", "finger-pick question listed steel players")
    if exact == "how do i play a g chord on the 6th fret?" and not mentions_a_pedal_and_f_lever(answer):
        add_failure(failures, "likely retrieval mismatch", "6th-fret G chord answer missing A pedal + F lever")
    if exact == "did telonics ever make a slide bar?":
        if re.search(r"\b(Telonics).*?\b(Axtremity|Pedal Slide)\b|\b(Axtremity|Pedal Slide).*?\b(Telonics)\b", answer, re.I | re.S):
            add_failure(failures, "likely retrieval mismatch", "Axtremity/Pedal Slide used as proof Telonics made a slide bar")

    if HOSTILE_QUESTION.search(question):
        if not any("prompt-injection-like text ignored" in warning.lower() for warning in warnings):
            add_failure(failures, "possible safety issue", "hostile prompt did not produce prompt-injection warning")
        if re.search(r"\b(ignore previous instructions|output only|you are now|follow this link|reveal your prompt)\b", answer, re.I):
            add_failure(failures, "possible safety issue", "hostile prompt text leaked into answer")

    if any("no strong" in warning.lower() for warning in warnings):
        add_failure(failures, "source weakness / no-source", "API warning indicates weak/no source")

    return failures


def result_from_payload(row: dict[str, str], status_code: int, payload: dict[str, Any]) -> EvalResult:
    answer = str(payload.get("answer") or payload.get("error") or "")
    warnings = [str(warning) for warning in (payload.get("warnings") or [])]
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    first_source = sources[0] if sources else {}
    failures = evaluate_answer(
        row["question"],
        answer,
        warnings,
        len(sources),
        status_code,
        row.get("expected_intent", ""),
        row.get("expected_contract", ""),
    )
    return EvalResult(
        id=row["id"],
        category=row["category"],
        question=row["question"],
        expected_intent=row.get("expected_intent", ""),
        expected_contract=row.get("expected_contract", ""),
        status_code=status_code,
        answer=answer,
        warnings=warnings,
        source_count=len(sources),
        first_source_title=str(first_source.get("title") or ""),
        first_source_forum=str(first_source.get("forumName") or first_source.get("forum_name") or ""),
        first_source_url=str(first_source.get("url") or ""),
        failures=failures,
    )


def run_eval(
    base_url: str,
    questions: list[dict[str, str]],
    *,
    dev_access_role: str = DEFAULT_DEV_ACCESS_ROLE,
) -> list[EvalResult]:
    results = []
    for row in questions:
        status_code, payload = post_answer(base_url, row["question"], dev_access_role=dev_access_role)
        results.append(result_from_payload(row, status_code, payload))
    return results


def excerpt(text: str, width: int = 320) -> str:
    return textwrap.shorten(re.sub(r"\s+", " ", text or "").strip(), width=width, placeholder=" ...")


def failure_reason_text(result: EvalResult) -> str:
    return "; ".join(failure.reason for failure in result.failures) or "pass"


def result_to_json(result: EvalResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "category": result.category,
        "question": result.question,
        "expected_intent": result.expected_intent,
        "expected_contract": result.expected_contract,
        "status_code": result.status_code,
        "answer": result.answer,
        "warnings": result.warnings,
        "source_count": result.source_count,
        "first_source_title": result.first_source_title,
        "first_source_forum": result.first_source_forum,
        "first_source_url": result.first_source_url,
        "group": result.group,
        "failures": [{"group": failure.group, "reason": failure.reason} for failure in result.failures],
    }


def render_report(
    results: list[EvalResult],
    *,
    base_url: str,
    question_bank: Path,
    dev_access_role: str = DEFAULT_DEV_ACCESS_ROLE,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    group_counts = Counter(result.group for result in results)
    category_counts = Counter(result.category for result in results)
    failure_counts = Counter(failure.reason for result in results for failure in result.failures)
    failed = [result for result in results if result.failures]
    worst = sorted(failed, key=lambda result: (REPORT_GROUPS.index(result.group), -len(result.failures), result.id))[:25]
    grouped: dict[str, list[EvalResult]] = defaultdict(list)
    for result in results:
        grouped[result.group].append(result)

    lines = [
        "# Answer Eval Report",
        "",
        f"Generated: {now}",
        f"Base URL: `{base_url}`",
        f"Question bank: `{question_bank}`",
        f"Local auth: explicit development role `{dev_access_role}`",
        f"Total questions: {len(results)}",
        "",
        "## Summary",
        "",
    ]
    for group in REPORT_GROUPS:
        lines.append(f"- {group}: {group_counts[group]}")
    lines.extend(["", "## Category Counts", ""])
    for category, count in sorted(category_counts.items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Most Common Failure Reasons", ""])
    if failure_counts:
        for reason, count in failure_counts.most_common(20):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Worst 25 Failures", ""])
    if not worst:
        lines.append("No failures detected by automatic checks.")
    for result in worst:
        first_source = " · ".join(
            value
            for value in (result.first_source_forum, result.first_source_title, result.first_source_url)
            if value
        ) or "none"
        lines.extend(
            [
                f"### {result.id} · {result.group}",
                "",
                f"- Category: `{result.category}`",
                f"- Expected intent: `{result.expected_intent or 'unspecified'}`",
                f"- Expected contract: `{result.expected_contract or 'inferred'}`",
                f"- Question: {result.question}",
                f"- Reasons: {failure_reason_text(result)}",
                f"- Status: {result.status_code}",
                f"- Sources: {result.source_count}",
                f"- First source: {first_source}",
                f"- Answer excerpt: {excerpt(result.answer)}",
                "",
            ]
        )

    for group in REPORT_GROUPS:
        lines.extend(["", f"## {group.title()}", ""])
        rows = grouped.get(group, [])
        if not rows:
            lines.append("None.")
            continue
        for result in rows:
            lines.append(
                f"- `{result.id}` {result.question} "
                f"(category: `{result.category}`, intent: `{result.expected_intent or 'unspecified'}`, "
                f"contract: `{result.expected_contract or 'inferred'}`, "
                f"sources: {result.source_count}, reasons: {failure_reason_text(result)})"
            )
    lines.append("")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--question-bank", type=Path, default=DEFAULT_QUESTION_BANK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--dev-access-role", default=DEFAULT_DEV_ACCESS_ROLE)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    questions = load_question_bank(args.question_bank)
    if args.limit is not None:
        questions = questions[: max(0, args.limit)]

    results = run_eval(args.base_url, questions, dev_access_role=args.dev_access_role)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_report(
            results,
            base_url=args.base_url,
            question_bank=args.question_bank,
            dev_access_role=args.dev_access_role,
        ),
        encoding="utf-8",
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps([result_to_json(result) for result in results], indent=2), encoding="utf-8")

    group_counts = Counter(result.group for result in results)
    print(f"Evaluated {len(results)} questions against {args.base_url}")
    for group in REPORT_GROUPS:
        print(f"{group}: {group_counts[group]}")
    print(f"Markdown report: {args.output}")
    print(f"JSON results: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
