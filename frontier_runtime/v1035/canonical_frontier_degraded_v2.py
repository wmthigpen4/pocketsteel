#!/usr/bin/env python3
"""No-model, bounded extractive responses from the frozen SGF top ten."""

from __future__ import annotations

import re
import time
from typing import Any


MAX_CLAIMS = 3
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.I)
_SENTENCE_RE = re.compile(r".+?(?:[.!?](?:[\"'’”]+)?(?=\s|$)|$)")
_FIRST_PERSON_RE = re.compile(
    r"\b(?:i|i'm|i've|i'd|me|my|mine|we|we're|we've|we'd|us|our|ours)\b",
    re.I,
)
_UNSAFE_RE = re.compile(
    r"(?:\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b|\b(?:https?://|www\.)\S+|"
    r"\b(?:ignore (?:all )?(?:previous|prior) instructions?|system prompt|developer message|"
    r"reveal (?:the )?(?:prompt|rules)|you are now|paypal|pm me|e-?mail me)\b)",
    re.I,
)
_STOPWORDS = frozenset(
    "a about an and are as at be can did do does for from had has have how in is it of on or "
    "should that the their this to was were what when where which who why with would you your "
    "players player forum steel guitar pedal e9".split()
)


def _tokens(value: str) -> set[str]:
    return {
        token for token in _TOKEN_RE.findall(value.casefold())
        if len(token) > 1 and token not in _STOPWORDS
    }


def _public_sgf(source: Any) -> bool:
    source_system = str(getattr(source, "source_system", "") or "").casefold()
    url = str(getattr(source, "url", "") or "").casefold()
    return source_system.startswith("sgf") or "steelguitarforum.com" in url


def _card(source: Any, excerpt: str) -> dict[str, Any]:
    metadata = getattr(source, "metadata", {}) or {}
    return {
        "source_id": str(source.source_id),
        "chunk_id": str(source.source_id),
        "post_uid": str(metadata.get("post_source_id") or source.source_id),
        "thread_title": str(getattr(source, "title", "") or "Steel Guitar Forum discussion"),
        "thread_url": str(getattr(source, "url", "") or ""),
        "forum_name": str(metadata.get("forum_name") or "Steel Guitar Forum"),
        "author": str(getattr(source, "author", "") or ""),
        "post_date": " ".join(str(getattr(source, "date", "") or "").split())[:128],
        "source_system": str(getattr(source, "source_system", "") or "steel_guitar_forum"),
        "excerpt": excerpt[:800],
        "score": float(metadata.get("semantic_score") or getattr(source, "fused_score", 0.0) or 0.0),
        "warnings": [],
    }


def _eligible(sentence: str, anchors: set[str]) -> bool:
    normalized = " ".join(sentence.split()).strip(" -•\t")
    if (
        len(normalized) < 35
        or len(normalized) > 300
        or normalized.endswith("?")
        or _FIRST_PERSON_RE.search(normalized)
        or _UNSAFE_RE.search(normalized)
    ):
        return False
    overlap = _tokens(normalized) & anchors
    return len(overlap) >= (1 if len(anchors) <= 2 else 2)


def degraded_response(runtime: Any, question: str) -> dict[str, Any] | None:
    """Rerun the same local retriever at limit ten and make no model calls."""

    started = time.perf_counter()
    sources, retrieval_latency_ms = runtime.retriever.retrieve(question, limit=10)
    ranked = [source for source in sources[:10] if _public_sgf(source)]
    if not ranked:
        return None
    anchors = _tokens(question)
    claims: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    answer_lines: list[str] = []
    seen: set[str] = set()
    for source in ranked:
        source_text = " ".join(str(getattr(source, "text", "") or "").split())
        for sentence in _SENTENCE_RE.findall(source_text):
            candidate = " ".join(sentence.split()).strip(" -•\t")
            key = candidate.casefold()
            if key in seen or not _eligible(candidate, anchors):
                continue
            seen.add(key)
            author = " ".join(str(getattr(source, "author", "") or "").split())
            attribution = author or "The cited Steel Guitar Forum passage"
            text = f"{attribution} reported: {candidate}"
            if len(text) > 380:
                text = candidate
            claim_id = f"extractive-{len(claims) + 1}"
            claims.append({
                "claim_id": claim_id,
                "text": text,
                "source_ids": [str(source.source_id)],
                "support_mode": "deterministic_entailment",
            })
            cards.append(_card(source, candidate))
            answer_lines.append(text)
            break
        if len(claims) >= MAX_CLAIMS:
            break

    cards_only = not claims
    if cards_only:
        cards = [_card(source, " ".join(str(source.text).split())[:800]) for source in ranked[:3]]
        answer = (
            "Verified synthesis is temporarily unavailable. Relevant public Steel Guitar "
            "Forum source cards were found, but no sentence passed the strict extractive checks."
        )
    else:
        answer = "\n\n".join(answer_lines)
    return {
        "schema_version": 1,
        "mode": "partial",
        "answer": answer,
        "claims": claims,
        "sources": cards,
        "coverage": [],
        "response_note": "Verified synthesis is temporarily unavailable.",
        "metadata": {
            "architecture": str(getattr(runtime, "architecture_name", "canonical-frontier-v1035")),
            "delivery_mode": "sgf_extractive_degraded",
            "primary_model": "",
            "verifier_model": "",
            "retrieval_latency_ms": float(retrieval_latency_ms),
            "generation_latency_ms": 0.0,
            "total_latency_ms": (time.perf_counter() - started) * 1000,
            "ranked_passage_limit": 10,
            "extractive_claims": len(claims),
            "cards_only": cards_only,
        },
    }


__all__ = ["degraded_response"]
