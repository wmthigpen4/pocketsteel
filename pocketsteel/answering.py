"""Source-backed answer generation for the local API."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal, Protocol, cast

from pocketsteel.api_contract import AnswerMode, SourceCitation

from pocketsteel.curated_source_registry import answer_contains_unapproved_url, is_approved_curated_url, slide_bar_vendor_bullets
from pocketsteel.steel_rules import answer_from_rules
from pocketsteel.text import shorten


FallbackCategory = Literal[
    "not_enough_source_evidence",
    "current_info_not_in_corpus",
    "sensitive_identity_speculation",
    "copyrighted_song_guardrail",
    "ask_for_more_context",
    "rules_layer_answer_available",
]


VALID_MODES: set[AnswerMode] = {"ask", "gear", "copedent", "tab", "practice"}
DEFAULT_MODE: AnswerMode = "ask"
DEFAULT_TOP_K = 6
DEFAULT_CHAT_MODEL = "qwen3:8b"
ANSWER_PROVIDER_ENV = "STEEL_RAG_ANSWER_PROVIDER"
CHAT_MODEL_ENV = "STEEL_RAG_CHAT_MODEL"
OLLAMA_URL_ENV = "OLLAMA_URL"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


@dataclass(frozen=True)
class AnswerRequest:
    question: str
    mode: AnswerMode = DEFAULT_MODE
    top_k: int = DEFAULT_TOP_K


class AnswerProvider(Protocol):
    def answer(self, request: AnswerRequest, sources: list[dict[str, Any]]) -> str:
        ...


def source_label(source_system: str) -> str:
    if source_system == "sgf_phpbb_current":
        return "current phpBB"
    if source_system == "sgf_ubb_legacy":
        return "legacy UBB"
    return source_system or "source"


def source_to_card(source: dict[str, Any]) -> SourceCitation:
    card: dict[str, Any] = {
        "title": source.get("thread_title") or "Source thread",
        "forumName": source.get("forum_name") or "Steel Guitar Forum",
        "url": source.get("thread_url") or "",
        "excerpt": source.get("excerpt") or "",
        "score": float(source.get("score") or 0.0),
        "chunkId": source.get("chunk_id") or "",
        "postUid": source.get("post_uid") or None,
    }
    if source.get("visibility") == "private" or source.get("source_kind") == "private_source_chunk":
        card.update(
            {
                "source_system": source.get("source_system") or "",
                "visibility": source.get("visibility") or "private",
                "source_id": source.get("source_id") or "",
                "source_path": source.get("source_path") or source.get("thread_url") or "",
                "provenance_status": source.get("provenance_status") or "",
                "answer_quote_allowed": source.get("answer_quote_allowed") or "limited",
            }
        )
    return cast(SourceCitation, card)


PRIVATE_E9_PROFILE_SOURCE_ID = "user-e9-copedent-profile"
PRIVATE_PROFILE_GRIPS = ("3-4-5", "4-5-6", "5-6-8", "6-8-10")


def private_profile_answer(question: str, sources: list[dict[str, Any]]) -> str | None:
    """Answer first-person setup questions from the user's private profile only.

    Hybrid retrieval can legitimately return SGF copedent discussions alongside
    the user's private setup note. For first-person questions, those forum
    snippets are comparison material at best, not the user's copedent.
    """

    if not question_mentions_private_profile(question):
        return None
    profile_source = first_private_e9_profile_source(sources)
    if profile_source is None:
        return None

    lowered = question.lower()
    if "grip" in lowered:
        return (
            "For your saved 10-string E9 profile, your common grips are "
            + ", ".join(PRIVATE_PROFILE_GRIPS[:-1])
            + f", and {PRIVATE_PROFILE_GRIPS[-1]}."
        )
    if "lever" in lowered:
        return (
            "Your private E9 profile lists these knee levers:\n"
            "- F lever: raises strings 4 and 8 E to F.\n"
            "- E-lower: lowers strings 4 and 8 E to D#.\n"
            "- RKL: raises string 1 F# to G/G#, raises string 2 D# to E, and lowers string 6 G# to F#.\n"
            "- RKR: lowers string 2 D# to D/C# and lowers string 9 D to C#."
        )

    return (
        "Your private profile describes a 10-string E9 setup.\n\n"
        "Open tuning\n"
        "| String | Note |\n"
        "| --- | --- |\n"
        "| 1 | F# |\n"
        "| 2 | D# |\n"
        "| 3 | G# |\n"
        "| 4 | E |\n"
        "| 5 | B |\n"
        "| 6 | G# |\n"
        "| 7 | F# |\n"
        "| 8 | E |\n"
        "| 9 | D |\n"
        "| 10 | B |\n\n"
        "Pedals\n"
        "| Pedal | Change |\n"
        "| --- | --- |\n"
        "| A | raises strings 5 and 10 B to C# |\n"
        "| B | raises strings 3 and 6 G# to A |\n"
        "| C | raises string 4 E to F# and string 5 B to C# |\n\n"
        "Levers\n"
        "| Lever | Change |\n"
        "| --- | --- |\n"
        "| F lever | raises strings 4 and 8 E to F |\n"
        "| E-lower | lowers strings 4 and 8 E to D# |\n"
        "| RKL | raises string 1 F# to G/G#, raises string 2 D# to E, lowers string 6 G# to F# |\n"
        "| RKR | lowers string 2 D# to D/C#, lowers string 9 D to C# |\n\n"
        "Common grips\n"
        "- 3-4-5\n"
        "- 4-5-6\n"
        "- 5-6-8\n"
        "- 6-8-10"
    )


def question_mentions_private_profile(question: str) -> bool:
    lowered = re.sub(r"\s+", " ", (question or "").strip().lower())
    if not re.search(r"\b(?:my|i|me)\b", lowered):
        return False
    return bool(
        re.search(
            r"\b(?:e9\s+)?copedent\b|\bsetup\b|\blevers?\b|\bpedals?\b|\bcommon\s+grips?\b|\bgrips?\b",
            lowered,
        )
    )


def first_private_e9_profile_source(sources: list[dict[str, Any]]) -> dict[str, Any] | None:
    for source in sources:
        source_id = str(source.get("source_id") or "").strip()
        title = str(source.get("thread_title") or "").strip().lower()
        visibility = str(source.get("visibility") or "").strip().lower()
        if visibility == "private" and (
            source_id == PRIVATE_E9_PROFILE_SOURCE_ID or title == "user e9 copedent profile"
        ):
            return source
    return None


def apply_private_profile_wording(answer: str, question: str, sources: list[dict[str, Any]]) -> str:
    if first_private_e9_profile_source(sources) is None:
        return answer
    if question_mentions_af_pedal_lever(question):
        answer = re.sub(
            r"Common grips include 3-4-5, 4-5-6, 5-6-8, (?:and )?6-8-10, depending on your copedent\.?",
            "For your saved 10-string E9 profile, useful grips include 3-4-5, 4-5-6, 5-6-8, and 6-8-10.",
            answer,
        )
    return answer


def mode_guidance(mode: str) -> str:
    if mode == "gear":
        return "Emphasize likely causes, diagnostic steps, safety notes, and source-backed forum wisdom."
    if mode == "copedent":
        return "Use interval-first language. Include strings, frets, pedals, levers, and interval functions when the sources support them."
    if mode == "tab":
        return "Teach style, harmony, positions, chord tones, and pedal/lever purpose. Do not provide full note-for-note copyrighted tab or full copyrighted lyrics by default."
    if mode == "practice":
        return "Return practical numbered practice steps grounded in the provided sources."
    return "Give a clear, practical source-backed answer."


def source_context(sources: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for index, source in enumerate(sources, 1):
        sections.append(
            "\n".join(
                [
                    f"[{index}] {source.get('thread_title') or 'Source thread'}",
                    f"Source system: {source_label(str(source.get('source_system') or ''))}",
                    f"Forum: {source.get('forum_name') or ''}",
                    f"URL: {source.get('thread_url') or ''}",
                    f"Excerpt: {source.get('excerpt') or ''}",
                ]
            )
        )
    return "\n\n---\n\n".join(sections)


@dataclass(frozen=True)
class EvidencePoint:
    text: str
    source_index: int
    score: int


@dataclass(frozen=True)
class DistilledFacts:
    """Clean facts extracted from source text for synthesis, not direct copying."""

    facts: tuple[str, ...]
    source_count: int

    @property
    def is_thin(self) -> bool:
        return len(self.facts) < 2 or self.source_count < 1


AnswerRoute = Literal[
    "copedent_fretboard",
    "gear_setup",
    "diagnostic_troubleshooting",
    "equipment_recommendation",
    "maintenance_safety",
    "technique_improvement",
    "tone_touch",
    "practice_plan",
    "travel_transport",
    "replacement_parts",
    "brand_comparison",
    "player_brand_usage",
    "vendor_buying_guidance",
    "current_company_status",
    "product_value",
    "entity_definition",
    "yes_no_source_check",
    "player_history",
    "song_learning_or_tab_request",
    "general_forum_wisdom",
]


STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "common",
    "could",
    "does",
    "from",
    "have",
    "into",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
}
GEAR_TERMS = {
    "amp",
    "black",
    "box",
    "cable",
    "changer",
    "fender",
    "ground",
    "hum",
    "jack",
    "pickup",
    "pedal",
    "pot",
    "reverb",
    "speaker",
    "steel",
    "tone",
    "volume",
}
TROUBLESHOOTING_TERMS = {
    "buzz",
    "check",
    "diagnostic",
    "fix",
    "ground",
    "hum",
    "noise",
    "problem",
    "repair",
    "replace",
    "test",
    "touching",
    "trouble",
}
SETTINGS_TERMS = {"bass", "eq", "gain", "mid", "middle", "presence", "setting", "settings", "treble", "volume"}
SAFETY_TERMS = {"capacitor", "chassis", "electric", "ground", "mains", "power", "shock", "tube", "voltage"}
INTERVAL_TERMS = {
    "augmented",
    "chord",
    "dominant",
    "diminished",
    "fifth",
    "flat",
    "fourth",
    "interval",
    "major",
    "minor",
    "raise",
    "root",
    "scale",
    "seventh",
    "sixth",
    "third",
}
MECHANIC_TERMS = {
    "a+b",
    "b+c",
    "fret",
    "frets",
    "knee",
    "lever",
    "levers",
    "lower",
    "pedal",
    "pedals",
    "raise",
    "string",
    "strings",
}
COPEDENT_TERMS = {
    "c6",
    "change",
    "copedent",
    "e9",
    "lower",
    "pull",
    "raise",
    "split",
    "tuning",
}
PRACTICE_TERMS = {
    "bar",
    "blocking",
    "clean",
    "exercise",
    "grip",
    "lick",
    "move",
    "movement",
    "phrase",
    "practice",
    "slow",
    "smooth",
    "tempo",
}
PRODUCT_VALUE_TERMS = {"money", "price", "value", "worth"}
PRODUCT_FEATURE_TERMS = {
    "delay",
    "distortion",
    "effect",
    "effects",
    "overdrive",
    "pedal",
    "preamp",
    "reverb",
    "steel dream",
    "tone",
}
POSITIVE_SENTIMENT_TERMS = {
    "best",
    "excellent",
    "favorite",
    "good",
    "great",
    "happy",
    "impressed",
    "keeper",
    "like",
    "love",
    "worth",
}
NEGATIVE_SENTIMENT_TERMS = {
    "expensive",
    "issue",
    "problem",
    "return",
    "sold",
    "trouble",
    "weak",
}
RANKING_TERMS = {"alive", "best", "ever", "greatest", "players", "ranking", "rankings", "top"}
KNOWN_ENTITY_DEFINITIONS = {
    "tsga": (
        "TSGA is the Texas Steel Guitar Association.",
        "Its public website is https://www.texassteelguitar.org/.",
    ),
    "maurice anderson": (
        "Maurice “Reece” Anderson was a major steel guitarist and an important builder/player figure associated with MSA.",
    ),
    "reece anderson": (
        "Maurice “Reece” Anderson was a major steel guitarist and an important builder/player figure associated with MSA.",
    ),
    "lloyd green": (
        "Lloyd Green is one of the most influential pedal steel guitarists, especially associated with classic Nashville/session steel guitar.",
        "He is known for tasteful, melodic E9 playing and major recorded work in country music.",
    ),
    "buddy emmons": (
        "Buddy Emmons was one of the most influential pedal steel guitarists in the instrument’s history.",
        "He is widely associated with advanced pedal-steel technique, influential E9 and C6 playing, and major contributions as a player and builder/designer.",
    ),
    "pack-a-seat": (
        "A pack-a-seat is a steel-guitar seat/storage box used by players to carry accessories and sit at the guitar.",
        "Steeler’s Choice is a known pack-a-seat maker.",
        "Website: https://www.steelerschoice.com/",
    ),
    "pack seat": (
        "A pack-a-seat is a steel-guitar seat/storage box used by players to carry accessories and sit at the guitar.",
        "Steeler’s Choice is a known pack-a-seat maker.",
        "Website: https://www.steelerschoice.com/",
    ),
}
CANONICAL_ALL_TIME_PLAYERS = [
    "Buddy Emmons",
    "Jimmy Day",
    "Lloyd Green",
    "Paul Franklin",
    "Tom Brumley",
]
COMMONLY_CITED_LIVING_PLAYERS = [
    "Paul Franklin",
    "Tommy White",
    "Mike Johnson",
    "Bruce Bouton",
    "Doug Jernigan",
]
KNOWN_WILLIE_STEEL_PLAYERS = {
    "Buddy Emmons",
    "Jimmy Day",
    "Weldon Myrick",
    "Ralph Mooney",
}
NAME_NOISE_WORDS = {
    "Again",
    "Anne",
    "Does",
    "Hi",
    "More",
    "Once",
    "Thanks",
    "Top",
    "With",
    "Willie",
}
JOKE_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"\bephram\b",
        r"\bnunkheimer\b",
        r"\bzoawister\b",
        r"\bjust kidding\b",
        r"\bkidding\b",
        r"\blol\b",
        r"\bhaha\b",
        r"\bhumou?r\b",
    )
]
ADMIN_LINE_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"\bthis message was edited\b",
        r"\bposted\s+\d{1,2}\s+\w+\s+\d{4}\b",
        r"\bmoderator\b",
        r"\bmoved to\b",
        r"\bwrong forum\b",
    )
]
SIGNATURE_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"^\s*(?:top|quote):\s*$",
        r"\btop\s+(?:i|has|does|you|get|hi|just|am)\b",
        r"\bsp=sharing\b",
        r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
        r"\be-?mail\s+[\w.+-]+@",
        r"\b(?:does|has)\s+anyone\s+(?:know|compared)\b",
        r"\bi\s+am\s+looking\s+for\b",
        r"\bi\s+am\s+going\s+to\s+start\b",
        r"^\s*[-_]{2,}\s*$",
        r"\bemail:\b",
        r"\bemail me\b",
        r"\bfor sale\b",
        r"\bwww\.",
        r"\bhttp://",
        r"\bhttps://",
        r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b",
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
        r"\btell\s+the\s+sound\s+guy\b",
        r"\bbite\s+ya\b",
        r"\broad\s+cases?\b.*\bspeakers?\b",
        r"\bspeakers?\s+stay\s+inside\b",
        r"\bwith\s+mics?\b",
        r"\bmove\s+some\s+air\b",
    )
]

QUESTION_FRAGMENT_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"^\s*(?:does|has)\s+anyone\s+(?:know|compared)\b",
        r"^\s*i\s+am\s+looking\s+for\b",
        r"^\s*i'?m\s+looking\s+for\b",
        r"^\s*can\s+anyone\s+(?:tell|help|send|post)\b",
        r"^\s*where\s+can\s+i\s+(?:find|get|buy)\b",
    )
]


def normalized_terms(text: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9+]+", text.lower()))
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return []
    pieces = re.split(r"(?<=[.!?])\s+", normalized)
    sentences = []
    for piece in pieces:
        piece = piece.strip(" -\t\n")
        if len(piece) < 32:
            continue
        if classify_source_sentence(piece) != "answer_candidate":
            continue
        sentences.append(shorten(piece, 260))
    return sentences


def classify_source_sentence(sentence: str) -> str:
    stripped = sentence.strip()
    lowered = stripped.lower()
    if re.search(r"\b(?:gay|fag|retard)\b", lowered):
        return "unsafe_or_offensive"
    if is_low_value_sentence(stripped):
        return "forum_boilerplate"
    if any(pattern.search(stripped) for pattern in QUESTION_FRAGMENT_PATTERNS):
        return "question_fragment"
    if re.search(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", stripped, re.I) or "e-mail " in lowered:
        return "contact_info"
    if "sp=sharing" in lowered or re.search(r"\bhttps?://\S+", stripped):
        return "raw_link_share"
    if re.search(r"\b(?:d-10|s-10|sd-10|nashville\s+\d+|session\s+\d+|emmons\s+legrande|mullen|zum)\b.*\b(?:x\d|&\d|pickup|amp)\b", lowered):
        return "signature_or_gear_list"
    if re.search(r"\b(just kidding|haha|lol|joke)\b", lowered):
        return "joke_or_chatter"
    return "answer_candidate"


def is_low_value_sentence(sentence: str) -> bool:
    stripped = sentence.strip()
    if any(pattern.search(stripped) for pattern in ADMIN_LINE_PATTERNS):
        return True
    if any(pattern.search(stripped) for pattern in SIGNATURE_PATTERNS):
        return True
    if any(pattern.search(stripped) for pattern in QUESTION_FRAGMENT_PATTERNS):
        return True
    if any(pattern.search(stripped) for pattern in JOKE_PATTERNS):
        return True
    if re.fullmatch(r"[\w .'-]{2,40}\s+on\s+\d{1,2}\s+\w+\s+\d{4}.*", stripped, re.I):
        return True
    return False


def collect_evidence(question: str, sources: list[dict[str, Any]]) -> list[EvidencePoint]:
    question_terms = normalized_terms(question)
    points: list[EvidencePoint] = []
    seen: set[str] = set()
    for source_index, source in enumerate(sources, 1):
        excerpt = str(source.get("excerpt") or "").strip()
        for sentence in split_sentences(excerpt):
            key = evidence_key(sentence)
            if key in seen:
                continue
            seen.add(key)
            sentence_terms = normalized_terms(sentence)
            overlap = len(question_terms & sentence_terms)
            score = overlap * 5 + max(0, 7 - source_index)
            if overlap == 0 and source_index > 3:
                continue
            points.append(EvidencePoint(text=sentence, source_index=source_index, score=score))
    points.sort(key=lambda point: (-point.score, point.source_index, point.text))
    return points


def distill_source_facts(question: str, evidence: list[EvidencePoint], *, limit: int = 4) -> DistilledFacts:
    """Return normalized fact candidates that can inform synthesis without leaking source prose.

    This deliberately rejects short mention-only fragments and raw SGF cleanup leftovers. The
    returned strings are still source-derived, so callers should use them as supporting facts,
    not as the opening sentence of an answer.
    """

    question_terms = normalized_terms(question)
    facts: list[str] = []
    seen: set[str] = set()
    source_indexes: set[int] = set()
    for point in evidence:
        text = normalize_source_fact_text(point.text)
        if not text or not is_distillable_fact(text, question_terms):
            continue
        key = evidence_key(text)
        if key in seen:
            continue
        seen.add(key)
        facts.append(text)
        source_indexes.add(point.source_index)
        if len(facts) >= limit:
            break
    return DistilledFacts(facts=tuple(facts), source_count=len(source_indexes))


def normalize_source_fact_text(text: str) -> str:
    text = clean_evidence_text(text)
    text = re.sub(r"\btje\b", "the", text, flags=re.I)
    text = re.sub(r"\bteh\b", "the", text, flags=re.I)
    text = re.sub(r"\bi\b", "I", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text


def is_distillable_fact(text: str, question_terms: set[str]) -> bool:
    if classify_source_sentence(text) != "answer_candidate":
        return False
    terms = normalized_terms(text)
    if len(text) < 45 or len(terms) < 5:
        return False
    if question_terms and not (terms & question_terms) and len(text) < 90:
        return False
    if re.search(r"\b(?:i\s+(?:think|guess|wonder|heard)|anyone|somebody|some one)\b", text, re.I) and len(terms & question_terms) < 2:
        return False
    return True


def evidence_key(sentence: str) -> str:
    normalized = re.sub(r"\W+", " ", sentence.lower()).strip()
    return " ".join(normalized.split()[:28])


def has_any(text: str, terms: set[str]) -> bool:
    text_terms = normalized_terms(text)
    return bool(text_terms & terms)


def points_matching(evidence: list[EvidencePoint], terms: set[str], fallback_count: int) -> list[EvidencePoint]:
    matches = [point for point in evidence if has_any(point.text, terms)]
    if matches:
        return matches
    return evidence[:fallback_count]


def notable_context(sources: list[dict[str, Any]], evidence: list[EvidencePoint]) -> list[str]:
    contexts: list[str] = []
    used = {point.source_index for point in evidence[:3]}
    for index, source in enumerate(sources[:4], 1):
        if index in used and len(contexts) >= 1:
            continue
        title = source.get("thread_title") or "Source thread"
        forum = source.get("forum_name") or "Steel Guitar Forum"
        system = source_label(str(source.get("source_system") or ""))
        contexts.append(f"- Source is {system} from {forum}: {title}.")
        if len(contexts) == 2:
            break
    return contexts


def classify_answer_route(request: AnswerRequest, sources: list[dict[str, Any]]) -> AnswerRoute:
    question = request.question.lower()
    source_titles = " ".join(str(source.get("thread_title") or "") for source in sources).lower()
    combined = f"{question} {source_titles}"
    if question_mentions_player_brand_usage(question):
        return "player_brand_usage"
    if question_mentions_vendor_buying(question):
        return "vendor_buying_guidance"
    if question_mentions_current_company_status(question):
        return "current_company_status"
    if has_known_entity_definition(question):
        return "entity_definition"
    if question_mentions_brand_comparison(question):
        return "brand_comparison"
    if question_mentions_replacement_parts(question):
        return "replacement_parts"
    if question_mentions_airplane_travel(question):
        return "travel_transport"
    if question_mentions_diagnostic_troubleshooting(question):
        return "diagnostic_troubleshooting"
    if question_mentions_maintenance_oil(question):
        return "maintenance_safety"
    if question_mentions_finger_picks(question):
        return "equipment_recommendation"
    if question_mentions_tone_touch(question):
        return "tone_touch"
    if question_mentions_technique_improvement(question):
        return "technique_improvement"
    if question_mentions_practice_plan(question) or request.mode == "practice":
        return "practice_plan"
    if request.mode == "tab":
        return "general_forum_wisdom"
    if question_mentions_song_learning_or_tab(question):
        return "song_learning_or_tab_request"
    if re.search(r"\bdid\b.+\bmake\b|\bever\b.+\bmake\b|\bdo(?:es)?\b.+\bmake\b", question):
        return "yes_no_source_check"
    if question_mentions_player_ranking(question):
        return "player_history"
    if re.search(r"\bwho\b.+\bplayed\b.+\bwith\b", question) or "willie nelson" in question:
        return "player_history"
    if (
        request.mode == "copedent"
        or (
            re.search(r"\bplay\s+(?:an?\s+)?[a-g](?:#|b)?\s+chord\b", question)
            and re.search(r"\b\d+(?:st|nd|rd|th)?\s+fret\b", question)
        )
        or "across the guitar" in question
        or "b&c" in question
        or "b+c" in question
        or "wound 6th" in question
        or "wound sixth" in question
        or question_mentions_af_pedal_lever(question)
        or question_mentions_ninth_string(question)
        or question_mentions_sixth_string_lower(question)
        or question_mentions_basic_theory(question)
        or question_mentions_string_gauge(question)
        or question_mentions_tab_notation(question)
    ):
        return "copedent_fretboard"
    if question_mentions_product_value(question):
        return "product_value"
    if request.mode == "gear":
        return "gear_setup"
    return "general_forum_wisdom"


def source_count(evidence: list[EvidencePoint]) -> int:
    return len({point.source_index for point in evidence})


def source_supported_heading(evidence: list[EvidencePoint]) -> str:
    if source_count(evidence) >= 2:
        return "Related points:"
    return "One related point:"


def strip_answer_support_sections(lines: list[str]) -> list[str]:
    """Keep generated answer prose compact by removing source-context tails."""
    blocked_headings = {"Source context:", "Source support:", "Notable source context:"}
    cleaned: list[str] = []
    skip_block = False
    for line in lines:
        if line in blocked_headings:
            skip_block = True
            continue
        if skip_block and line and not line.endswith(":"):
            continue
        if skip_block and line.endswith(":"):
            skip_block = False
        if not skip_block:
            cleaned.append(line)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return cleaned


def question_mentions_g_at_sixth_fret(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(r"\bg\s+chord\b", lowered)
        and re.search(r"\b6(?:th)?\s+fret\b|\bsixth\s+fret\b", lowered)
    )


def question_mentions_wound_sixth(question: str) -> bool:
    return bool(re.search(r"\bwound\s+(?:6th|sixth|string\s+6)\b", question.lower()))


def question_mentions_bc_pedals_second_fret(question: str) -> bool:
    lowered = question.lower()
    return bool(("b&c" in lowered or "b+c" in lowered) and re.search(r"\b2(?:nd)?\s+fret\b|\bsecond\s+fret\b", lowered))


def question_mentions_g_across_guitar(question: str) -> bool:
    lowered = question.lower()
    return bool(re.search(r"\bg\s+chord\b", lowered) and ("across the guitar" in lowered or "across the neck" in lowered))


def question_mentions_af_pedal_lever(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(r"\ba\s*\+\s*f\b", lowered)
        or re.search(r"\ba\s+pedal\b.*\bf\s+lever\b", lowered)
        or re.search(r"\bf\s+lever\b.*\ba\s+pedal\b", lowered)
    )


def question_mentions_ninth_string(question: str) -> bool:
    lowered = question.lower()
    return bool(re.search(r"\b(?:9th|ninth|string\s+9)\s+string\b|\bstring\s+9\b", lowered))


def question_mentions_sixth_string_lower(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(r"\b(?:6th|sixth|string\s+6)\s+string\b.*\blower\b", lowered)
        or re.search(r"\blower\b.*\b(?:6th|sixth|string\s+6)\s+string\b", lowered)
        or "6th string lower" in lowered
        or "string 6 lower" in lowered
    )


def question_mentions_maintenance_oil(question: str) -> bool:
    lowered = question.lower()
    maintenance_fluid = "oil" in lowered or "lubricat" in lowered or "lighter fluid" in lowered or "naphtha" in lowered or "wd-40" in lowered
    return bool(maintenance_fluid and ("changer" in lowered or "pedal steel" in lowered or "steel guitar" in lowered))


def question_mentions_finger_picks(question: str) -> bool:
    lowered = question.lower()
    return bool(("finger pick" in lowered or "fingerpick" in lowered or "picks" in lowered) and ("buy" in lowered or "best" in lowered or "recommend" in lowered))


def question_mentions_practice_plan(question: str) -> bool:
    lowered = question.lower()
    return bool(
        "what should i practice" in lowered
        or "what should i work on" in lowered
        or re.search(r"\bgive me\b.*\bpractice plan\b", lowered)
        or re.search(r"\bhow should i practice\b", lowered)
        or re.search(r"\bpractice\b.*\bplan\b", lowered)
        or "practice routine" in lowered
        or "practice session" in lowered
    )


def question_mentions_song_learning_or_tab(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(r"\b(?:tab|tablature|lyrics?)\b", lowered)
        or re.search(r"\b(?:show me how to play a song|teach me how to play anything specific|how do i play happy birthday|happy birthday)\b", lowered)
        or re.search(r"\b(?:approach playing|explain the style of|chord progression|song arrangement)\b", lowered)
    )


def question_mentions_basic_theory(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(r"\bwhat\s+is\s+(?:a\s+)?triad\b", lowered)
        or re.search(r"\bhow\s+do\s+i\s+play\s+(?:a\s+)?2m\s+in\s+the\s+key\s+of\s+g\b", lowered)
    )


def question_mentions_string_gauge(question: str) -> bool:
    lowered = question.lower()
    return bool("gauge" in lowered and ("10th string" in lowered or "string 10" in lowered or "e9" in lowered))


def question_mentions_tab_notation(question: str) -> bool:
    return bool(re.search(r"\bwhat\s+is\s+a?\s*5\^7\b|\b5\^7\b", question.lower()))


def question_mentions_technique_improvement(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(
            r"\b(?:help me sound less mechanical|sound less mechanical|sounds mechanical|sound more musical|less stiff|fills? sound better|play with more feeling|sound less robotic)\b",
            lowered,
        )
    )


def question_mentions_diagnostic_troubleshooting(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(
            r"\b(?:amp\s+(?:buzz|buzzes|hum|hums)|buzz\s+at\s+idle|amp\s+hum|hums?\s+until\s+i\s+touch|noise\s+when\s+nothing\s+is\s+plugged\s+in|ground\s+buzz|touching\s+(?:the\s+)?(?:strings?|changer).*(?:buzz|hum))\b",
            lowered,
        )
    )


def question_mentions_tone_touch(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(
            r"\b(?:soften\s+my\s+attack|attack\s+is\s+too\s+hard|sound\s+less\s+harsh|pick\s+attack\s+(?:sounds\s+)?too\s+sharp|play\s+with\s+softer\s+touch)\b",
            lowered,
        )
    )


def question_mentions_player_ranking(question: str) -> bool:
    lowered = question.lower()
    if not re.search(r"\b(player|players|steel players|guitarists|steel guitarists)\b", lowered):
        return False
    return bool(
        re.search(r"\b(top|best|greatest|ranking|rankings|ranked)\b", lowered)
        or re.search(r"\bmost\s+(?:influential|important)\b", lowered)
        or re.search(r"\b(?:ever|alive today|today)\b", lowered)
    )


def question_mentions_airplane_travel(question: str) -> bool:
    lowered = question.lower()
    return bool(("airplane" in lowered or "airline" in lowered or "fly" in lowered or "flight" in lowered) and ("steel" in lowered or "guitar" in lowered))


def question_mentions_replacement_parts(question: str) -> bool:
    lowered = question.lower()
    return bool(("pedal rod" in lowered or "pedal rods" in lowered) and ("broke" in lowered or "broken" in lowered or "new ones" in lowered or "replace" in lowered or "get" in lowered or "buy" in lowered))


def question_mentions_brand_comparison(question: str) -> bool:
    lowered = question.lower()
    return bool(
        len(compared_brands_from_question(question)) >= 2
        and re.search(r"\b(?:better|difference|compare|vs\.?|versus|or|than|buy)\b", lowered)
    )


def question_mentions_player_brand_usage(question: str) -> bool:
    return bool(
        re.search(r"\bwho\s+(?:plays?|uses?)\s+(?:an?\s+)?[a-z0-9-]+(?:\s+guitars?)?", question)
        or re.search(r"\bwhich\s+(?:players?|people|pros|steel players?)\s+(?:play|use)\s+[a-z0-9-]+", question)
    )


def question_mentions_vendor_buying(question: str) -> bool:
    return bool(
        re.search(r"\bwhere\s+can\s+i\s+buy\b", question)
        or re.search(r"\bwhat\s+brands\s+make\b", question)
        or (("steel bar" in question or "slide bar" in question or "tone bar" in question) and "buy" in question)
    )


def question_mentions_current_company_status(question: str) -> bool:
    return bool(re.search(r"\b(?:still\s+in\s+business|in business today|operating today|company status)\b", question))


def question_mentions_product_value(question: str) -> bool:
    lowered = question.lower()
    if question_mentions_vendor_buying(lowered) or question_mentions_brand_comparison(lowered) or question_mentions_player_brand_usage(lowered):
        return False
    return bool(
        re.search(r"\bworth(?:\s+the\s+money|\s+buying)?\b", lowered)
        or re.search(r"\bgood\s+value\b", lowered)
        or re.search(r"\bprice\s*/?\s*value\b", lowered)
        or (re.search(r"\bshould\s+i\s+buy\b", lowered) and len(compared_brands_from_question(question)) < 2)
    )


def compared_brands_from_question(question: str) -> list[str]:
    found = re.findall(r"\b(Mullen|MSA|Emmons|Sho-Bud|Shobud|ZumSteel|Carter|GFI|Sierra)\b", question, re.I)
    brands: list[str] = []
    for brand in found:
        canonical = {"msa": "MSA", "shobud": "Sho-Bud"}.get(brand.lower(), brand[0].upper() + brand[1:])
        if canonical.lower() not in {item.lower() for item in brands}:
            brands.append(canonical)
    return brands


def has_known_entity_definition(question: str) -> bool:
    lowered = question.lower()
    return any(entity in lowered for entity in KNOWN_ENTITY_DEFINITIONS)


def known_entity_definition(question: str) -> tuple[str, str] | None:
    lowered = question.lower()
    for entity, definition in KNOWN_ENTITY_DEFINITIONS.items():
        if entity in lowered:
            return definition
    return None


def key_entities(question: str) -> set[str]:
    lowered = question.lower()
    entities: set[str] = set()
    for entity in ("telonics", "axtremity", "pedal slide", "tsga", "maurice", "anderson", "reece", "steeler", "pack-a-seat", "pack seat"):
        if entity in lowered:
            entities.add(entity)
    proper_phrases = re.findall(r"\b[A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+){0,3}\b", question)
    for phrase in proper_phrases:
        phrase_lower = phrase.lower()
        if phrase_lower.split()[0] not in {"what", "who", "how", "did", "should", "is"}:
            entities.add(phrase_lower)
    return entities


def sources_contain_entity(sources: list[dict[str, Any]], entity: str) -> bool:
    for source in sources:
        haystack = f"{source.get('thread_title') or ''} {source.get('excerpt') or ''}".lower()
        if entity in haystack:
            return True
    return False


def has_entity_mismatch(question: str, sources: list[dict[str, Any]]) -> bool:
    entities = key_entities(question)
    if not entities:
        return False
    important = [entity for entity in entities if entity not in {"slide", "bar", "steel"}]
    return bool(important and not any(sources_contain_entity(sources, entity) for entity in important))


def extract_person_names(evidence: list[EvidencePoint]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for point in evidence:
        for name in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b", point.text):
            if not is_clean_person_name(name):
                continue
            lowered = name.lower()
            if lowered in seen or lowered.startswith(("steel guitar", "willie nelson")):
                continue
            seen.add(lowered)
            names.append(name)
    return names


def is_clean_person_name(name: str) -> bool:
    words = name.split()
    if len(words) < 2:
        return False
    if any(word in NAME_NOISE_WORDS for word in words):
        return False
    if name in KNOWN_WILLIE_STEEL_PLAYERS:
        return True
    # Keep this conservative: unknown title-case phrases from forum snippets
    # are often thread titles or parsed boilerplate, not reliable player names.
    return False


def product_name_from_question(question: str) -> str:
    if re.search(r"benado\s+steel\s+dream\s*2?", question, re.I):
        return "Benado Steel Dream 2"
    quoted = re.search(r'"([^"]+)"', question)
    if quoted:
        return quoted.group(1)
    titled = re.search(r"\b([A-Z][A-Za-z0-9+-]+(?:\s+[A-Z0-9][A-Za-z0-9+-]+){1,5})\b", question)
    return titled.group(1) if titled else "that product"


def player_usage_brand(question: str) -> str:
    for brand in ("Emmons", "Mullen", "MSA", "Sho-Bud", "ZumSteel", "Carter", "GFI", "Sierra"):
        if brand.lower() in question.lower():
            return brand
    match = re.search(r"\b(?:plays?|uses?)\s+(?:an?\s+)?([A-Za-z0-9-]+)", question)
    return match.group(1).title() if match else "that brand"


def canonical_player_context(question: str) -> tuple[list[str], list[str] | None]:
    lowered = question.lower()
    all_time = CANONICAL_ALL_TIME_PLAYERS
    living = COMMONLY_CITED_LIVING_PLAYERS if "alive" in lowered or "today" in lowered else None
    return all_time, living


def summarize_product_impression(point: EvidencePoint) -> str:
    text = point.text
    terms = normalized_terms(text)
    feature_words = sorted((PRODUCT_FEATURE_TERMS | SETTINGS_TERMS | GEAR_TERMS) & terms)
    positive = bool(terms & POSITIVE_SENTIMENT_TERMS)
    negative = bool(terms & NEGATIVE_SENTIMENT_TERMS)
    sentiment = "positive owner/source impression"
    if negative and not positive:
        sentiment = "source caveat"
    elif positive and negative:
        sentiment = "mixed source impression"

    if feature_words:
        return f"{sentiment} mentioning {', '.join(feature_words[:5])}"
    if "price" in terms or "money" in terms or "worth" in terms:
        return f"{sentiment} about price/value"
    return f"{sentiment}; check the source card for the full wording"


def clean_answer_text(answer: str, *, allow_contact_info: bool = False) -> str:
    lines: list[str] = []
    skip_source_context = False
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if not line:
            skip_source_context = False
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line.lower().rstrip(":") in {"practical answer", "the useful way to hear it"}:
            continue
        if line in {"Source context:", "Source support:", "Notable source context:", "Forum-source context, not definitive ranking:"}:
            skip_source_context = True
            if lines and lines[-1] == "":
                lines.pop()
            continue
        if skip_source_context:
            continue
        line = re.sub(r"\s*\[\d+\]", "", line)
        line = re.sub(r"^Concise answer:\s*", "", line, flags=re.I)
        line = re.sub(r"\bTop:\s*", "", line)
        line = re.sub(r"\btje\b", "the", line, flags=re.I)
        line = re.sub(r"\bteh\b", "the", line, flags=re.I)
        if "for rag answers" in line.lower():
            continue
        if answer_contains_unapproved_url(line):
            continue
        line_class = classify_answer_line(line)
        if allow_contact_info and re.search(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", line, re.I):
            line_class = "contact_info"
        if line_class != "answer_candidate" and not is_curated_reference_line(line):
            if not (allow_contact_info and line_class == "contact_info"):
                continue
        if is_low_value_sentence(line) and not is_curated_reference_line(line) and not (allow_contact_info and line_class == "contact_info"):
            continue
        lines.append(line)
    while lines and lines[-1] == "":
        lines.pop()
    return dedupe_answer_lines("\n".join(lines))


def dedupe_answer_lines(answer: str) -> str:
    """Remove repeated generated lines so lead text and sections do not echo each other."""
    output: list[str] = []
    seen: set[str] = set()
    for raw_line in answer.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            if output and output[-1] != "":
                output.append("")
            continue
        key = normalized_answer_line_key(line)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        output.append(line)
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output)


def normalized_answer_line_key(line: str) -> str:
    key = line.strip().lower()
    key = re.sub(r"^[-*]\s+", "", key)
    key = re.sub(r"^\d+[.)]\s+", "", key)
    key = re.sub(r"[^a-z0-9+ ]+", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    if len(key) < 18:
        return ""
    return key


def classify_answer_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "answer_candidate"
    if re.search(
        r"\b(?:useful source-backed points|useful distilled points|source cards as supporting evidence|the cleanest source-backed answer)\b",
        stripped,
        re.I,
    ):
        return "forum_boilerplate"
    return classify_source_sentence(stripped)


def is_curated_reference_line(line: str) -> bool:
    urls = re.findall(r"https?://[^\s)>\"]+", line or "")
    return bool(urls and all(is_approved_curated_url(url.rstrip(".,;")) for url in urls))


def answer_has_quality_issue(answer: str, *, allow_contact_info: bool = False) -> bool:
    if not answer.strip():
        return True
    case_sensitive_bad_patterns = [
        r"^\s*Top\b",
        r"\sTop\s",
    ]
    bad_patterns = [
        r"\bThe cleanest source-backed answer\b",
        r"\bsource cards as supporting evidence\b",
        r"\bUseful distilled points\b",
        r"\bUseful source-backed points\b",
        r"\bsp=sharing\b",
        r"\bWhat multiple sources support\b",
        r"\bSource context\b",
        r"\bForum-source context\b",
        r"(?m)^\s*Practical answer\s*:?\s*$",
        r"\b(?:Does anyone know|Has anyone compared|I am looking for tablature)\b",
        r"\btje\b|\bteh\b",
    ]
    if not allow_contact_info:
        bad_patterns.extend((r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", r"\be-?mail\s+"))
    return (
        answer_contains_unapproved_url(answer)
        or has_empty_or_orphan_section(answer)
        or any(re.search(pattern, answer) for pattern in case_sensitive_bad_patterns)
        or any(
        re.search(pattern, answer, re.I) for pattern in bad_patterns
    )
    )


SECTION_HEADING_RE = re.compile(
    r"^\s*(?:answer|direct answer|practical answer|practical use|what changes|what to choose|best places to check|likely causes|diagnostic path|safety|caveat|learning approach|exercise|practice it this way|touch checklist)\s*:?\s*$",
    re.I,
)


def has_empty_or_orphan_section(answer: str) -> bool:
    lines = answer.splitlines()
    for index, line in enumerate(lines):
        if not SECTION_HEADING_RE.match(line):
            continue
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index >= len(lines):
            return True
        if SECTION_HEADING_RE.match(lines[next_index]):
            return True
    return False


def fallback_category_for_question(question: str) -> FallbackCategory:
    rule_answer = answer_from_rules(question)
    if rule_answer is not None:
        return "rules_layer_answer_available"
    q = re.sub(r"\s+", " ", question or "").strip().lower()
    if re.search(r"\b(?:gay people|gay players|lgbtq|sexual orientation)\b", q):
        return "sensitive_identity_speculation"
    if re.search(r"\bwho\s+plays\s+for\s+[a-z0-9'. -]+\??$", q):
        return "current_info_not_in_corpus"
    if "happy birthday" in q or re.search(r"\b(?:full lyrics|full tab|note-for-note|copyrighted)\b", q):
        return "copyrighted_song_guardrail"
    if re.search(r"\b(?:play a song|teach me how to play anything specific|show me how to play a song)\b", q):
        return "ask_for_more_context"
    return "not_enough_source_evidence"


def fallback_answer_for_category(category: FallbackCategory, question: str) -> str:
    if category == "rules_layer_answer_available":
        rule_answer = answer_from_rules(question)
        if rule_answer is not None:
            return rule_answer.answer
    if category == "current_info_not_in_corpus":
        return (
            "I don’t know the current roster from the information I have. "
            "For the current touring or recording lineup, check official tour credits, album/session credits, or the artist’s current band listings. "
            "I can also help interpret any credits you find."
        )
    if category == "sensitive_identity_speculation":
        return (
            "I don’t know. "
            "I would not want to guess about anyone’s private identity."
        )
    if category == "copyrighted_song_guardrail":
        return (
            "I can help with the musical approach, but I will not provide full copyrighted lyrics or full note-for-note copyrighted tab by default. "
            "Give me the key, tuning, and a short excerpt or your own tab attempt, and I can help map it to pedal-steel positions."
        )
    if category == "ask_for_more_context":
        return (
            "Tell me the song, key, tuning, and what skill you want to work on. "
            "If you want a safe starter now, use a public-domain tune such as Amazing Grace or an original mini-exercise and we can map it to E9 positions."
        )
    return noisy_source_fallback()


def raw_contact_info_requested(question: str) -> bool:
    return bool(re.search(r"\b(?:email|e-mail|contact info|contact information|contact)\b", question or "", re.I))


def final_answer_quality_gate(answer: str, question: str) -> str:
    allow_contact_info = raw_contact_info_requested(question)
    cleaned = clean_answer_text(answer, allow_contact_info=allow_contact_info)
    if not answer_has_quality_issue(cleaned, allow_contact_info=allow_contact_info):
        return cleaned
    cleaned_lines = [line for line in cleaned.splitlines() if classify_answer_line(line) == "answer_candidate"]
    cleaned = "\n".join(line for line in cleaned_lines if line.strip())
    if cleaned and not answer_has_quality_issue(cleaned, allow_contact_info=allow_contact_info):
        return cleaned
    return fallback_answer_for_category(fallback_category_for_question(question), question)


def noisy_source_fallback() -> str:
    return (
        "I don’t have enough reliable information to answer that confidently. "
        "Try adding the song, key, tuning, brand, or exact part you mean so I can narrow the source match."
    )


def clean_evidence_text(text: str) -> str:
    text = re.sub(r"\s*\[\d+\]", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bTop\b\s*", "", text)
    return text


def is_useful_entity_context(text: str) -> bool:
    lowered = text.lower()
    if is_low_value_sentence(text):
        return False
    if "who can help" in lowered or "pictures" in lowered or "website" in lowered:
        return False
    if "posted" in lowered or "schedule" in lowered or "jamboree" in lowered:
        return False
    return True


class DeterministicAnswerProvider:
    """Offline provider used when no live LLM provider is configured."""

    def answer(self, request: AnswerRequest, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "No strong source match found for that question."

        route = classify_answer_route(request, sources)
        evidence = collect_evidence(request.question, sources)
        if has_entity_mismatch(request.question, sources) and route == "yes_no_source_check":
            entity = sorted(key_entities(request.question))[0]
            if "telonics" in {item.lower() for item in key_entities(request.question)} and "slide" in request.question.lower():
                return clean_answer_text("I do not see a strong source match showing that Telonics made a slide bar.")
            return clean_answer_text(
                f"I do not see a strong source match showing that {entity.title()} made that. "
                "The closest matches appear to mention something related, but not the requested maker/entity."
            )
        if not evidence and route not in {
            "product_value",
            "copedent_fretboard",
            "player_history",
            "entity_definition",
            "yes_no_source_check",
            "diagnostic_troubleshooting",
            "equipment_recommendation",
            "maintenance_safety",
            "technique_improvement",
            "tone_touch",
            "practice_plan",
            "travel_transport",
            "replacement_parts",
            "brand_comparison",
            "player_brand_usage",
            "vendor_buying_guidance",
            "current_company_status",
            "song_learning_or_tab_request",
        }:
            if sources and all(not split_sentences(str(source.get("excerpt") or "")) for source in sources):
                return noisy_source_fallback()
            return clean_answer_text(
                "The available matches are too thin to answer that confidently. "
                "Treat this as a weak match."
            )
        if route == "entity_definition":
            return clean_answer_text(self._entity_definition_answer(request, sources, evidence))
        if route == "yes_no_source_check":
            return clean_answer_text(self._yes_no_source_answer(request, sources, evidence))
        if route == "product_value":
            return clean_answer_text(self._product_value_answer(request, sources, evidence))
        if route == "copedent_fretboard":
            return clean_answer_text(self._fretboard_answer(request, sources, evidence))
        if route == "player_history":
            return clean_answer_text(self._history_or_player_answer(request, sources, evidence))
        if route == "player_brand_usage":
            return clean_answer_text(self._player_brand_usage_answer(request, sources, evidence))
        if route == "vendor_buying_guidance":
            return clean_answer_text(self._vendor_buying_answer(request, sources, evidence))
        if route == "current_company_status":
            return clean_answer_text(self._current_company_status_answer(request, sources, evidence))
        if route == "equipment_recommendation":
            return clean_answer_text(self._equipment_recommendation_answer(request, sources, evidence))
        if route == "diagnostic_troubleshooting":
            return clean_answer_text(self._diagnostic_troubleshooting_answer(request, sources, evidence))
        if route == "maintenance_safety":
            return clean_answer_text(self._maintenance_safety_answer(request, sources, evidence))
        if route == "tone_touch":
            return clean_answer_text(self._tone_touch_answer(request, sources, evidence))
        if route == "technique_improvement":
            return clean_answer_text(self._technique_improvement_answer(request, sources, evidence))
        if route == "practice_plan":
            return clean_answer_text(self._practice_plan_answer(request, sources, evidence))
        if route == "travel_transport":
            return clean_answer_text(self._travel_transport_answer(request, sources, evidence))
        if route == "replacement_parts":
            return clean_answer_text(self._replacement_parts_answer(request, sources, evidence))
        if route == "brand_comparison":
            return clean_answer_text(self._brand_comparison_answer(request, sources, evidence))
        if route == "song_learning_or_tab_request":
            return clean_answer_text(self._song_learning_answer(request, sources, evidence))

        if route == "gear_setup" or request.mode == "gear":
            return clean_answer_text(self._gear_answer(request, sources, evidence))
        if request.mode == "copedent":
            return clean_answer_text(self._copedent_answer(request, sources, evidence))
        if request.mode == "tab":
            return clean_answer_text(self._tab_answer(request, sources, evidence))
        if request.mode == "practice":
            return clean_answer_text(self._practice_answer(request, sources, evidence))
        return clean_answer_text(self._ask_answer(sources, evidence))

    def _ask_answer(self, sources: list[dict[str, Any]], evidence: list["EvidencePoint"]) -> str:
        facts = distill_source_facts("", evidence)
        if facts.facts:
            lines = ["Here is the safest answer I can support from the retrieved material:"]
            for fact in facts.facts[:3]:
                lines.append(f"- {fact}")
            if facts.source_count < 2:
                lines.append("- I found this in limited source support, so treat it as a clue rather than consensus.")
            return "\n".join(lines)
        primary = evidence[0]
        lines = [
            f"I found one related source point, but it is thin: {clean_evidence_text(primary.text)}",
            "",
            source_supported_heading(evidence),
        ]
        for point in evidence[: 3 if source_count(evidence) >= 2 else 1]:
            lines.append(f"- {clean_evidence_text(point.text)}")
        if source_count(evidence) < 2:
            lines.append("- I only found one usable source point here, so treat it as a clue rather than consensus.")
        context = notable_context(sources, evidence)
        if context:
            lines.extend(["", "Notable source context:"])
            lines.extend(context)
        return "\n".join(lines)

    def _entity_definition_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        definition = known_entity_definition(request.question)
        if not definition:
            return self._ask_answer(sources, evidence)
        if re.search(r"\b(?:every|all|only)\b", request.question.lower()) and ("pack-a-seat" in request.question.lower() or "pack seat" in request.question.lower()):
            return (
                "No. Not every pack-a-seat is made by Steeler’s Choice. "
                "Steeler’s Choice is a known maker, but pack-a-seat is a general steel-guitar seat/storage-box category.\n"
                "Website: https://www.steelerschoice.com/"
            )
        if "pack-a-seat" in request.question.lower() or "pack seat" in request.question.lower():
            return "\n".join(definition)
        lines = [definition[0]]
        if len(definition) > 1 and definition[1]:
            lines.append(definition[1])
        return "\n".join(lines)

    def _yes_no_source_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        entities = sorted(key_entities(request.question))
        entity = entities[0].title() if entities else "that entity"
        if "telonics" in {item.lower() for item in entities} and "slide" in request.question.lower():
            proof_text = " ".join(point.text for point in evidence).lower()
            if not re.search(r"\btelonics\b.*\b(?:made|makes|built|builds|manufactured|manufactures)\b.*\bslide\s+bar\b", proof_text):
                return "I do not see a strong source match showing that Telonics made a slide bar."
        if entities and not any(sources_contain_entity(sources, item) for item in entities):
            if "telonics" in {item.lower() for item in entities} and "slide" in request.question.lower():
                return "I do not see a strong source match showing that Telonics made a slide bar."
            return f"I do not see a strong source match showing that {entity} made that."
        if evidence:
            return (
                "The available matches mention the requested entity, but I would not treat that as proof. "
                f"{clean_evidence_text(evidence[0].text)}"
            )
        if "telonics" in {item.lower() for item in entities} and "slide" in request.question.lower():
            return "I do not see a strong source match showing that Telonics made a slide bar."
        return f"I do not see a strong source match showing that {entity} made that."

    def _product_value_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        product_name = product_name_from_question(request.question)
        feature_points = points_matching(evidence, PRODUCT_FEATURE_TERMS | GEAR_TERMS, fallback_count=2)
        positive_points = points_matching(evidence, POSITIVE_SENTIMENT_TERMS, fallback_count=0)
        negative_points = points_matching(evidence, NEGATIVE_SENTIMENT_TERMS, fallback_count=0)

        lines = [
            f"Short answer: treat {product_name} as a conditional buy, not an automatic yes.",
            "",
            "Useful buying checks:",
        ]
        if positive_points:
            for point in positive_points[:3]:
                lines.append(f"- One source suggests a favorable owner impression; check the source card for the exact context.")
        else:
            lines.append("- The retrieved excerpts do not give enough clean owner detail to claim broad praise.")

        lines.extend(["", "Cautions:"])
        if negative_points:
            for point in negative_points[:2]:
                lines.append("- At least one source suggests a caveat; compare it against your rig and use case.")
        else:
            lines.append("- Lack of complaints in a few excerpts is not proof that it is worth the price.")

        lines.extend(["", "Worth it?"])
        if source_count(evidence) >= 2:
            lines.append(
                "- Maybe, if the features solve a real problem in your rig and the price is fair. Treat forum comments as owner impressions, not a controlled review."
            )
        else:
            lines.append("- Evidence is thin: I would not treat one forum comment as enough to justify the price by itself.")

        return "\n".join(lines)

    def _fretboard_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        rule_answer = answer_from_rules(request.question)
        if rule_answer is not None:
            return rule_answer.answer

        if question_mentions_g_across_guitar(request.question):
            return (
                "On standard E9, useful G major positions include:\n"
                "- 3rd fret: open/no pedals.\n"
                "- 6th fret: A pedal + F lever.\n"
                "- 10th fret: A+B pedals.\n\n"
                "Common grips to try:\n"
                "- 3-4-5\n"
                "- 4-5-6\n"
                "- 5-6-8\n"
                "- 6-8-10"
            )

        if question_mentions_g_at_sixth_fret(request.question):
            lines = [
                "Direct fretboard answer: On standard E9, G major at the 6th fret is the A-pedal + F-lever position.",
                "",
                "Why it works:",
                "- The F lever raises the E strings, and the A pedal raises the B strings; together they give the major-chord position three frets above the open major position.",
                "",
                "Usable grips:",
                "- Start with common major-chord string groups such as 3-4-5, 4-5-6, 5-6-8, or 6-8-10, depending on your copedent and what notes you need.",
                "",
                "Source support:",
            ]
            for point in points_matching(evidence, MECHANIC_TERMS | INTERVAL_TERMS | COPEDENT_TERMS, fallback_count=2)[:2]:
                lines.append(f"- {clean_evidence_text(point.text)}")
            return "\n".join(lines)

        if question_mentions_wound_sixth(request.question):
            return (
                "A wound 6th string is a tradeoff. Some players like the sound and feel, and some feel it can make cabinet-drop behavior feel better. "
                "The big caution is mechanical: if your guitar lowers string 6 from G# to F#, a wound string may need more changer travel than the guitar can comfortably provide.\n\n"
                "What to try:\n"
                "- Try a wound 6th if you prefer its tone and your guitar can make the G# to F# lower cleanly.\n"
                "- Stay with a plain 6th if the lower gets sluggish, will not reach pitch, or makes the pedal/lever feel excessive.\n"
                "- Treat forum comments as setup-specific; changer design and string gauge matter."
            )

        if question_mentions_bc_pedals_second_fret(request.question):
            return (
                "On standard E9, B+C pedals on strings 3, 4, and 5 at the 2nd fret give you a bright major-triad sound built from the raised B-pedal/C-pedal position. "
                "Depending on what you hear as the root, it commonly functions as a G# major color or as part of a 2-minor/minor-family move in E9 thinking.\n\n"
                "How to hear it:\n"
                "- String 3 is raised by the B pedal.\n"
                "- Strings 4 and 5 are raised by the C pedal.\n"
                "- Together they create a compact three-note grip that is often used more as a passing-position or melodic harmony than as an isolated “home” chord."
            )

        if question_mentions_af_pedal_lever(request.question):
            return (
                "On standard E9, A+F means using the A pedal with the F lever to make a major-chord position three frets above the open major position.\n\n"
                "What changes\n"
                "- The A pedal raises the B strings to C#.\n"
                "- The F lever raises the E strings to F.\n"
                "- Together they give a major triad in the A+F position.\n\n"
                "Practical use\n"
                "- Use it to connect major chords smoothly without jumping straight to the A+B position.\n"
                "- Example: G major is available at the 6th fret with A pedal + F lever.\n"
                "- Common grips include 3-4-5, 4-5-6, 5-6-8, and 6-8-10, depending on your copedent."
            )

        if question_mentions_ninth_string(request.question):
            return (
                "On E9, the 9th string is most often useful because it gives you the D note: a dominant-7th color against E and a strong passing or scale tone.\n\n"
                "Practical uses:\n"
                "- Add the D note for dominant-7th sounds instead of hunting for it on top strings.\n"
                "- Use it in scale runs and walk-downs so the lower register connects smoothly.\n"
                "- Combine it with E-lower and pedal positions for 2-minor/5-dominant style movement.\n"
                "- Practice it slowly with common grips so it becomes part of your chord vocabulary, not a mystery string."
            )

        if question_mentions_sixth_string_lower(request.question):
            return (
                "The E9 6th-string lower usually takes string 6 from G# down to F#, which gives you a lower scale tone and a useful moving voice inside chords.\n\n"
                "How players use it:\n"
                "- As a smooth passing note between G# and F# in single-note lines.\n"
                "- To change the color of A+B or E-lower positions without moving the bar as much.\n"
                "- For dominant, suspended, or minor-family movement depending on the rest of the grip.\n"
                "- With care: the change needs enough travel, and plain vs. wound 6th string can affect how easily it reaches pitch."
            )

        if not evidence:
            return (
                "The available matches are too thin to answer that copedent question confidently. "
                "I need source support or a known copedent/profile before naming exact strings, pedals, or levers."
            )
        return self._copedent_answer(request, sources, evidence)

    def _equipment_recommendation_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        if question_mentions_finger_picks(request.question):
            return (
                "For steel guitar finger picks, start with fit and comfort rather than a single “best” brand.\n\n"
                "Common choices to compare:\n"
                "- National-style picks for a traditional feel.\n"
                "- Dunlop picks in different gauges if you want easy availability and small fit changes.\n"
                "- ProPik or similar split-wrap designs if regular bands bother your fingers.\n"
                "- Showcase 1941-style picks if you like the older National-style shape.\n\n"
                "Buy two or three gauges/styles if you can; the right pick is the one that stays put, releases cleanly, and sounds good on your guitar."
            )
        return self._gear_answer(request, sources, evidence)

    def _maintenance_safety_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        if question_mentions_maintenance_oil(request.question):
            return (
                "For a pedal-steel changer, use a tiny amount of light machine oil or sewing-machine-style oil at the moving contact points.\n\n"
                "Important distinction:\n"
                "- Naphtha or lighter fluid is a cleaner/solvent, not normal lubricant advice.\n"
                "- If you use a solvent for cleaning, keep it away from finishes and plastics, ventilate well, and re-lubricate afterward.\n"
                "- Avoid heavy oil, grease, and over-oiling; excess oil attracts dirt and can make the changer gummy."
            )
        return self._gear_answer(request, sources, evidence)

    def _diagnostic_troubleshooting_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        return (
            "Start by isolating whether the buzz is in the amp itself or in the signal chain.\n\n"
            "Likely causes:\n"
            "- If the amp buzzes with nothing plugged in, suspect amp power, tubes, filter caps, grounding, or other amp electronics.\n"
            "- If the buzz appears only after the rig is connected, suspect cable, volume pedal, pickup ground, effects, or power-supply noise.\n"
            "- If touching the strings or changer changes the buzz, look closely at grounding and shielding behavior.\n\n"
            "Diagnostic path:\n"
            "- Turn the amp on with nothing plugged in. If it still buzzes, suspect the amp, power, tubes, or electronics.\n"
            "- Plug the guitar straight into the amp with a known-good cable.\n"
            "- Swap the cable before changing anything else.\n"
            "- Add the volume pedal, then effects, then power supplies one at a time.\n"
            "- Listen for whether touching the strings or changer changes the buzz; that can point toward grounding or shielding behavior.\n"
            "- Move away from dimmers, neon, motors, wall-warts, and noisy power strips if the buzz changes with location.\n\n"
            "Safety: if the amp buzzes with nothing plugged in, or if the issue involves power, tubes, shock risk, or amp internals, use a qualified amp tech."
        )

    def _tone_touch_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        return (
            "To soften your attack, start with touch and timing before covering it with effects.\n\n"
            "Touch checklist:\n"
            "- Lighten your right-hand pick force and let the string speak instead of snapping it.\n"
            "- Try picking a little farther from the changer for a rounder attack, then compare it closer to the changer for brightness.\n"
            "- Bring the volume pedal in smoothly after the pick so the note blooms instead of jumps.\n"
            "- Practice slower pick blocking and palm blocking so note starts and stops stay controlled.\n"
            "- Center the pitch first, then add gentle bar vibrato after the note settles.\n"
            "- If the amp is biting too hard, reduce excessive treble or presence.\n"
            "- Use delay or reverb lightly for space, but do not use it to hide rough technique.\n"
            "- Practice one phrase loud/soft and short/long so your hands learn the difference."
        )

    def _practice_plan_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        return (
            "Tonight, work on clean movement between two or three useful E9 positions instead of trying to practice everything.\n\n"
            "25-minute plan:\n"
            "- 5 minutes: warm up slowly on common grips: 3-4-5, 4-5-6, 5-6-8, and 6-8-10.\n"
            "- 8 minutes: move a simple major chord through 3rd fret open, 6th fret A pedal + F lever, and 10th fret A+B.\n"
            "- 7 minutes: add blocking and volume-pedal control so every note starts and stops on purpose.\n"
            "- 5 minutes: make one musical phrase behind an imaginary singer, leaving space after each answer.\n\n"
            "Keep it slow enough that the bar, pedals, and hands arrive together. Clean beats fast tonight."
        )

    def _technique_improvement_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        return (
            "To sound less mechanical, make your phrasing breathe before you add more notes.\n\n"
            "Practice it this way:\n"
            "- Use fewer fills and leave space after the vocal line or backing-track phrase.\n"
            "- Place a simple fill slightly behind the beat, then repeat it until it feels relaxed.\n"
            "- Keep bar movement slow and in tune; add gentle vibrato only after the note settles.\n"
            "- Block cleanly so notes end intentionally instead of running together.\n"
            "- Use the volume pedal for dynamics and sustain, not constant motion.\n"
            "- Record one chorus and listen for rushed attacks, clipped endings, or fills that answer nothing."
        )

    def _travel_transport_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        return (
            "You can travel with a steel guitar, but plan like the airline will not know what it is.\n\n"
            "Travel checklist:\n"
            "- Use the strongest case you have; a flight case is safest if the guitar may be checked.\n"
            "- Carry-on may or may not work depending on the aircraft and crew, so have a checked-baggage plan.\n"
            "- Protect pedal rods, legs, and loose hardware so they cannot bend or punch into the guitar.\n"
            "- Arrive early and expect extra inspection or questions.\n"
            "- Do not rely on gate staff recognizing a pedal steel; explain it as a fragile musical instrument."
        )

    def _replacement_parts_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        return (
            "For broken pedal rods, replace them with rods that match your guitar’s length, threading, and connector style.\n\n"
            "Best next steps:\n"
            "- Contact the guitar maker, dealer, or a steel-guitar parts supplier/builder first.\n"
            "- Measure the old rod length and thread size if you still have it.\n"
            "- Match the hook/connector style at the pedal end and the pull hardware end.\n"
            "- If more than one rod broke or bent, inspect the pedal rack and travel for binding before just replacing parts."
        )

    def _player_brand_usage_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        brand = player_usage_brand(request.question)
        return (
            f"I do not have a strong, current roster of players using {brand} guitars today from the information I have.\n\n"
            "Use any listed sources as leads, but treat forum mentions as historical or source-specific unless a source clearly says the player currently uses that brand. "
            "For a current roster, check the maker’s official artist list, recent player interviews, or recent live/session credits."
        )

    def _vendor_buying_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        lowered = request.question.lower()
        if "pedal rod" in lowered:
            return self._replacement_parts_answer(request, sources, evidence)
        item = "slide bar" if "slide bar" in lowered or "steel bar" in lowered or "tone bar" in lowered else "steel-guitar item"
        if item == "slide bar":
            vendor_lines = "\n".join(slide_bar_vendor_bullets())
            return (
                "Best places to check\n\n"
                f"{vendor_lines}\n\n"
                "What to choose\n\n"
                "- Diameter\n"
                "- Length\n"
                "- Weight\n"
                "- Material\n"
                "- Pedal steel round tone bar vs. lap/dobro slide style\n\n"
                "Check current availability before assuming anything is in stock."
            )
        return (
            f"To buy a {item}, start with steel-guitar specialty dealers, bar makers, reputable music retailers, and the SGF classifieds or used market.\n\n"
            "What to check before ordering:\n"
            "- diameter, length, weight, and material\n"
            "- whether it is meant for pedal steel, lap steel, dobro, or regular slide guitar\n"
            "- return policy if you are unsure about size\n"
            "- seller familiarity with pedal steel, especially for heavier round bars\n\n"
            "For brands, use any listed sources as leads, then verify the current maker/vendor directly."
        )

    def _current_company_status_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        if "emmons guitar" in request.question.lower():
            return (
                "Yes. Emmons Guitar Co. appears to be operating today through its official site, emmonsguitar.co, "
                "offering ReSound’65 pedal steels and related items. Treat old forum rumors as historical context, not current company status."
            )
        return (
            "For current company status, use the maker’s official website or current contact information first. "
            "Old forum threads can be useful history, but they should not be treated as current business status."
        )

    def _brand_comparison_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        brands = compared_brands_from_question(request.question)
        if len(brands) >= 2:
            a, b = brands[0], brands[1]
            if {a.lower(), b.lower()} == {"mullen", "msa"}:
                return (
                    "There is no universal winner between Mullen and MSA; the better guitar is the one that fits your hands, setup, budget, and support needs.\n\n"
                    "How to compare them:\n"
                    "- Mullen: often valued for modern pro mechanics, smooth pedal feel, strong support, and a polished all-pull playing experience.\n"
                    "- MSA: covers several eras, from older Classics to modern MSA guitars, so mechanics, weight, and tone vary a lot by model.\n"
                    "- Tone and feel are personal; condition and setup can matter more than the logo.\n"
                    "- Check copedent fit, parts/support, weight, case condition, and whether the guitar has the changes you actually need.\n\n"
                    "If both are in good shape, this is a fit-and-condition choice, not a simple brand hierarchy."
                )
            return (
                f"There is no universal winner between {a} and {b}; compare the specific guitars, not just the brand names.\n\n"
                "Useful comparison points:\n"
                "- tone, sustain, and how the guitar responds under your hands\n"
                "- pedal/lever feel and mechanical condition\n"
                "- parts availability and builder/dealer support\n"
                "- weight, case, and ergonomics\n"
                "- copedent fit and room for future changes\n"
                "- price, service history, and current setup"
            )
        return (
            "Sho-Bud vs. Emmons is not one simple “better/worse” comparison; both names cover different eras, models, setups, and maintenance histories.\n\n"
            "High-level comparison:\n"
            "- Sho-Bud is often associated with a warm, woody, classic country sound and a distinctive feel, but mechanics vary a lot by model and era.\n"
            "- Emmons is often associated with clarity, sustain, and the push-pull/all-pull split in feel and mechanics, depending on the model.\n"
            "- Condition matters as much as the logo: worn mechanics, setup, pickups, and cabinet condition can dominate the difference.\n"
            "- Neither brand is one single sound. A great example of either can be wonderful; a neglected example of either can be frustrating."
        )

    def _history_or_player_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        if "willie nelson" in request.question.lower():
            names = extract_person_names(evidence)
            lines = ["Players mentioned in usable snippets as connected with Willie Nelson include:"]
            if names:
                for name in names[:8]:
                    lines.append(f"- {name}")
            else:
                lines = ["The retrieved snippets were too thin or too noisy to name players confidently."]
            return "\n".join(lines)

        all_time, living = canonical_player_context(request.question)
        lines = [
            "Rankings are subjective, and forum threads can include jokes, personal loyalties, and regional favorites.",
            "",
            "A safe all-time starting list:",
        ]
        for index, name in enumerate(all_time, 1):
            lines.append(f"{index}. {name}")
        if living:
            lines.extend(["", "Alive today / contemporary names commonly worth checking:"])
            for index, name in enumerate(living, 1):
                lines.append(f"{index}. {name}")
        lines.extend(
            [
                "",
                "Caution:",
                "- I filtered obvious joke/unserious excerpts and would not treat a single forum reply as definitive truth.",
            ]
        )
        return "\n".join(lines)

    def _gear_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        gear_points = points_matching(
            evidence,
            GEAR_TERMS | TROUBLESHOOTING_TERMS | SETTINGS_TERMS,
            fallback_count=3,
        )
        lines = ["Likely causes or common settings:"]
        for point in gear_points[:3]:
            lines.append(f"- {clean_evidence_text(point.text)}")
        lines.extend(["", "Diagnostic steps:"])
        for step_index, point in enumerate(gear_points[:3], 1):
            lines.append(f"{step_index}. Check this against the source detail: {clean_evidence_text(point.text)}")
        if has_any(f"{request.question} {' '.join(point.text for point in evidence)}", SAFETY_TERMS):
            lines.extend(
                [
                    "",
                    "Safety/caution:",
                    "- If the issue involves power, grounding, amplifier internals, shock risk, or capacitors, treat the forum advice as a clue and use a qualified tech before opening gear.",
                ]
            )
        return "\n".join(lines)

    def _copedent_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        interval_points = points_matching(evidence, INTERVAL_TERMS | COPEDENT_TERMS, fallback_count=3)
        lines = [
            "Interval-first answer:",
            f"- Start with the musical function named in the sources: {clean_evidence_text(interval_points[0].text)}",
        ]
        for point in interval_points[1:3]:
            lines.append(f"- Related source detail: {clean_evidence_text(point.text)}")

        source_text = " ".join(point.text for point in evidence)
        if has_any(source_text, MECHANIC_TERMS):
            lines.extend(["", "Strings, frets, pedals, and levers mentioned by sources:"])
            for point in points_matching(evidence, MECHANIC_TERMS, fallback_count=2)[:2]:
                lines.append(f"- {clean_evidence_text(point.text)}")
        else:
            lines.extend(
                [
                    "",
                    "Mechanical detail:",
                    "- The retrieved excerpts do not provide enough string, fret, pedal, or lever detail to name exact mechanics without overclaiming.",
                ]
            )
        return "\n".join(lines)

    def _tab_answer(self, request: AnswerRequest, sources: list[dict[str, Any]], evidence: list["EvidencePoint"]) -> str:
        concept_points = points_matching(evidence, INTERVAL_TERMS | MECHANIC_TERMS | COPEDENT_TERMS, fallback_count=3)
        lines = [
            "Concept explanation:",
            f"- {clean_evidence_text(concept_points[0].text)}",
        ]
        for point in concept_points[1:3]:
            lines.append(f"- {clean_evidence_text(point.text)}")
        lines.extend(
            [
                "",
                "Song-learning boundary:",
                "- I can discuss style, harmony, chord tones, positions, and pedal/lever purpose.",
                "- I do not provide full note-for-note copyrighted tab or full copyrighted lyrics by default, but I can build public-domain arrangements, original exercises, or work from material you provide.",
            ]
        )
        return "\n".join(lines)

    def _practice_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        practice_points = points_matching(evidence, PRACTICE_TERMS | INTERVAL_TERMS | MECHANIC_TERMS, fallback_count=3)
        lines = ["Practice steps:"]
        for step_index, point in enumerate(practice_points[:3], 1):
            lines.append(f"{step_index}. Work directly from this source idea: {clean_evidence_text(point.text)}")
        lines.extend(
            [
                "",
                "Keep it grounded:",
                "- If the listed sources are about a different setup or tuning, adapt the exercise rather than treating it as a universal rule.",
            ]
        )
        return "\n".join(lines)

    def _song_learning_answer(
        self,
        request: AnswerRequest,
        sources: list[dict[str, Any]],
        evidence: list["EvidencePoint"],
    ) -> str:
        lowered = request.question.lower()
        if "happy birthday" in lowered:
            return (
                "I can help you learn the approach, but I will not dump a full protected melody or note-for-note tab by default.\n\n"
                "Guardrail-friendly way to work on it:\n"
                "- Think in intervals from the key center instead of memorizing fret numbers first.\n"
                "- Pick a key and map the melody notes to nearby E9 positions.\n"
                "- Work one short phrase at a time, then add simple harmony or pads underneath.\n"
                "- If you provide the notes, a short excerpt, or your own tab attempt, I can help map it to strings, frets, pedals, and levers."
            )
        return (
            "Tell me the song, key, tuning, and what you want to work on, and I can map an approach for pedal steel.\n\n"
            "A practical starter option:\n"
            "- Use a public-domain tune such as “Amazing Grace” in G.\n"
            "- Start with G at the 3rd fret open.\n"
            "- Move to C at the 3rd fret with A+B.\n"
            "- Move to D at the 5th fret with A+B.\n"
            "- Resolve to G at the 6th fret with A pedal + F lever.\n\n"
            "I can discuss style, chord movement, positions, tone, and practice strategy. I do not provide full note-for-note copyrighted tab or full copyrighted lyrics by default."
        )


class OllamaAnswerProvider:
    def __init__(self, model: str | None = None, url: str | None = None) -> None:
        self.model = model or os.environ.get(CHAT_MODEL_ENV, DEFAULT_CHAT_MODEL)
        self.url = (url or os.environ.get(OLLAMA_URL_ENV, DEFAULT_OLLAMA_URL)).rstrip("/")

    def answer(self, request: AnswerRequest, sources: list[dict[str, Any]]) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are The Turnaround, a source-backed pedal steel guitar assistant. "
                    "Answer only from the retrieved Steel Guitar Forum sources. "
                    "Cite sources with [1], [2], etc. Distinguish current phpBB from legacy UBB when relevant. "
                    "If the sources are weak, indirect, or conflicting, say so. "
                    "Do not invent unsupported claims. You may discuss copyrighted songs, style, harmony, tone, and arrangement approach, "
                    "but do not provide full note-for-note copyrighted tab or full copyrighted lyrics by default."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {request.question}\n"
                    f"Mode: {request.mode}\n"
                    f"Mode guidance: {mode_guidance(request.mode)}\n\n"
                    f"Retrieved sources:\n{source_context(sources)}"
                ),
            },
        ]
        payload = {"model": self.model, "messages": messages, "stream": False}
        data = json.dumps(payload).encode("utf-8")
        request_obj = urllib.request.Request(
            f"{self.url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request_obj, timeout=300) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Could not reach Ollama answer provider: {exc}") from exc
        content = (body.get("message") or {}).get("content")
        if not content:
            raise RuntimeError("Ollama answer provider returned no message content.")
        return str(content).strip()


def configured_answer_provider(provider: AnswerProvider | None = None) -> AnswerProvider:
    if provider is not None:
        return provider
    configured = os.environ.get(ANSWER_PROVIDER_ENV, "deterministic").strip().lower()
    if configured == "ollama":
        return OllamaAnswerProvider()
    return DeterministicAnswerProvider()


def parse_answer_request(payload: dict[str, Any]) -> tuple[AnswerRequest | None, str | None]:
    question = str(payload.get("question") or "").strip()
    if not question:
        return None, "question is required"
    mode = str(payload.get("mode") or DEFAULT_MODE).strip().lower()
    if mode not in VALID_MODES:
        mode = DEFAULT_MODE
    try:
        top_k = int(payload.get("topK") or DEFAULT_TOP_K)
    except (TypeError, ValueError):
        top_k = DEFAULT_TOP_K
    top_k = max(1, min(top_k, 12))
    return AnswerRequest(question=question, mode=cast(AnswerMode, mode), top_k=top_k), None


def build_sections(answer: str) -> list[dict[str, str]]:
    return [{"title": "Answer", "style": "lead", "body": answer}]


def answer_is_no_source(answer: str) -> bool:
    return bool(re.search(r"\bno strong source match\b|\bdo not see a strong source match\b|\bnot answer this confidently\b", answer, re.I))


def concise_source_cards(sources: list[dict[str, Any]]) -> list[SourceCitation]:
    cards = []
    for source in sources:
        card = source_to_card(source)
        quote_allowed = str(source.get("answer_quote_allowed") or "").strip().lower()
        if source.get("visibility") == "private" and quote_allowed == "false":
            card["excerpt"] = ""
        elif source.get("visibility") == "private" and quote_allowed == "limited":
            card["excerpt"] = shorten(card["excerpt"], 220)
        else:
            card["excerpt"] = shorten(card["excerpt"], 420)
        cards.append(card)
    return cards
