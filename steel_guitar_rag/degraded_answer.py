"""Bounded extractive SGF answers for verified-synthesis outages.

This module deliberately does not call a language model.  It selects complete
sentences from already-retrieved public Steel Guitar Forum passages, requires
question overlap, and keeps every displayed claim attached to one source card.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from steel_guitar_rag.answering import concise_source_cards
from steel_guitar_rag.rag_guardrails import sanitize_retrieved_sources


MAX_CLAIMS = 3
MAX_CLAIM_CHARS = 300
MAX_ANSWER_CHARS = 900

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.I)
_SENTENCE_RE = re.compile(r".+?(?:[.!?](?:[\"'’”]+)?(?=\s|$)|$)")
_FIRST_PERSON_RE = re.compile(
    r"\b(?:i|i'm|i've|i'd|me|my|mine|myself|we|we're|we've|we'd|us|our|ours|ourselves)\b",
    re.I,
)
_CONTACT_RE = re.compile(
    r"(?:\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b|\b(?:https?://|www\.)\S+|\b\+?\d[\d ().-]{7,}\d\b)",
    re.I,
)
_INJECTION_RE = re.compile(
    r"\b(?:ignore (?:all )?(?:previous|prior) instructions?|system prompt|developer message|"
    r"reveal (?:the )?(?:prompt|rules)|you are now|follow these instructions)\b",
    re.I,
)
_FORUM_JUNK_RE = re.compile(
    r"\b(?:does anyone know|thanks(?:,|\s)+(?:nick|all|guys)|paypal|pm me|e-?mail me|"
    r"joined:|posts:|location:|top hi all)\b",
    re.I,
)
_RAW_TAB_RE = re.compile(r"(?:^|\s)(?:[1-9]|10)\s*[-|:]\s*(?:\d+[a-z#b+~-]*\s*){2,}", re.I)
_STOPWORDS = frozenset(
    "a about an and are as at be can did do does for from had has have how i in is it "
    "me my of on or say says should that the their this to was were what when where which "
    "who why with would you your players player forum steel guitar pedal e9".split()
)


@dataclass(frozen=True)
class ExtractiveDegradedAnswer:
    answer: str
    sources: list[dict[str, Any]]
    claim_count: int
    cards_only: bool


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(value.casefold())
        if len(token) > 1 and token not in _STOPWORDS
    }


def _source_text(source: Mapping[str, Any]) -> str:
    return " ".join(
        str(source.get(key) or "")
        for key in ("excerpt", "text", "chunk_text")
    ).strip()


def _is_public_sgf(source: Mapping[str, Any]) -> bool:
    if source.get("visibility") == "private" or source.get("source_kind") == "private_source_chunk":
        return False
    system = str(source.get("source_system") or "").casefold()
    forum = str(source.get("forum_name") or "").casefold()
    return (
        system in {"sgf_phpbb_current", "sgf_ubb_legacy", "steel_guitar_forum"}
        or "steel guitar forum" in forum
        or system.startswith("sgf_")
    )


def _eligible_sentence(sentence: str, anchors: set[str]) -> bool:
    candidate = " ".join(sentence.split()).strip(" -•\t")
    if (
        len(candidate) < 35
        or len(candidate) > MAX_CLAIM_CHARS
        or candidate.endswith("?")
        or _FIRST_PERSON_RE.search(candidate)
        or _CONTACT_RE.search(candidate)
        or _INJECTION_RE.search(candidate)
        or _FORUM_JUNK_RE.search(candidate)
        or _RAW_TAB_RE.search(candidate)
    ):
        return False
    sentence_tokens = _tokens(candidate)
    if not sentence_tokens or not anchors:
        return False
    required = 1 if len(anchors) <= 2 else 2
    return len(sentence_tokens & anchors) >= required


def compose_extractive_degraded_answer(
    question: str,
    results: Sequence[Mapping[str, Any]],
) -> ExtractiveDegradedAnswer | None:
    """Return source-verifiable evidence, or ``None`` when no safe card exists."""

    public_rows = [dict(row) for row in results if _is_public_sgf(row)]
    sanitized = sanitize_retrieved_sources(public_rows)
    ranked = sorted(
        sanitized.sources,
        key=lambda row: float(row.get("score") or 0.0),
        reverse=True,
    )[:10]
    source_card_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for source in ranked:
        source_cards = concise_source_cards([source])
        if source_cards:
            source_card_pairs.append((source, source_cards[0]))
    if not source_card_pairs:
        return None

    anchors = _tokens(question)
    claims: list[str] = []
    claim_sources: list[dict[str, Any]] = []
    seen_sentences: set[str] = set()
    for source, card in source_card_pairs:
        for sentence in _SENTENCE_RE.findall(_source_text(source)):
            candidate = " ".join(sentence.split()).strip(" -•\t")
            key = candidate.casefold()
            if key in seen_sentences or not _eligible_sentence(candidate, anchors):
                continue
            seen_sentences.add(key)
            title = str(card.get("title") or "the cited Steel Guitar Forum passage")
            claim = f"From {title}: {candidate}"
            if len(claim) > MAX_CLAIM_CHARS:
                claim = candidate
            prospective = "\n\n".join([*claims, claim])
            if len(prospective) > MAX_ANSWER_CHARS:
                continue
            claims.append(claim)
            claim_sources.append(card)
            break
        if len(claims) >= MAX_CLAIMS:
            break

    if claims:
        return ExtractiveDegradedAnswer(
            answer="\n\n".join(claims),
            sources=claim_sources,
            claim_count=len(claims),
            cards_only=False,
        )
    return ExtractiveDegradedAnswer(
        answer=(
            "Verified synthesis is temporarily unavailable. I found relevant public Steel Guitar "
            "Forum source cards, but no sentence passed the strict extractive-evidence checks."
        ),
        sources=[card for _source, card in source_card_pairs[:3]],
        claim_count=0,
        cards_only=True,
    )


__all__ = [
    "ExtractiveDegradedAnswer",
    "compose_extractive_degraded_answer",
]
