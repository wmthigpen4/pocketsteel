"""Corpus-first answer routing and route-level diagnostics.

The deterministic intent classifier deliberately stays side-effect free.  This
module is the control layer that can use public SGF search results to establish
steel-guitar context for an otherwise unknown entity, then select one of the
three product answer paths.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence


AnswerRoute = Literal["deterministic", "source_backed_rag", "hybrid", "guardrail"]

_ENTITY_QUESTION_RE = re.compile(
    r"^\s*(?:"
    r"who\b|"
    r"why\s+(?:is|was|are|were)|"
    r"what\s+(?:is|was|are|were)|"
    r"what\s+(?:do|did)\s+(?:players|people|sources|forum\s+members)|"
    r"what\s+(?:vendors?|brands?|products?|courses?|tutorials?|bars?|seats?|strings?)\b|"
    r"tell\s+me\s+about|"
    r"have\s+(?:players|people|forum\s+members)\s+(?:discussed|mentioned)|"
    r"where\s+can\s+i\s+(?:buy|find)|"
    r"are\s+.+?\s+(?:good|recommended|suitable)|"
    r"is\b"
    r")\b",
    re.I,
)
_PRIVATE_ENTITY_RE = re.compile(
    r"(?:<[^>]+>|\b(?:private|redacted|anonymous|unknown)\s+(?:person|player|identity)\b)",
    re.I,
)
_ENTITY_BOILERPLATE_RE = re.compile(
    r"\b(?:who|what|which|why|is|was|are|were|do|did|say|tell|me|about|have|has|had|players|"
    r"people|sources?|forum|members?|discussed|mentioned|the|a|an|of|to|for|and|or|"
    r"versus|vs|better|good|famous|known|still|in|business|today|please|steel|guitar|pedal)\b",
    re.I,
)
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.I)
_LESSON_ENTITY_RE = re.compile(r"\b(?:tutorials?|courses?|lessons?|manuals?|transcripts?)\b", re.I)
_SOURCE_CONTEXT_RE = re.compile(
    r"\b(?:what\s+(?:do|did)\s+(?:players|people|forum\s+members)|"
    r"players?\s+(?:say|report|describe|recommend)|forum\s+(?:wisdom|opinions?|reports?))\b",
    re.I,
)
_POSITION_REQUEST_RE = re.compile(
    r"\b(?:where|how\s+do\s+i\s+play|positions?|frets?|grips?|on\s+(?:the\s+)?e9)\b",
    re.I,
)
_CHORD_TOKEN_RE = re.compile(
    r"(?<![-\w])([a-g](?:##|bb|#|b)?\s*(?:maj(?:or)?\s*7|major\s+7(?:th)?|"
    r"dom(?:inant)?\s*7|m(?:inor)?\s*7|dim(?:inished)?|aug(?:mented)?|m|7|9|major|minor)?)(?![-\w])",
    re.I,
)
_STEEL_RESULT_CONTEXT_RE = re.compile(
    r"\b(?:pedal[-\s]?steel|steel\s+guitar|steel\s+player|copedent|e9|c6|"
    r"plays?\s+(?:pedal\s+)?steel|"
    r"pedals?|knee\s+levers?|fretboard|tablature|copedent|grips?|"
    r"steel\s+lessons?|steel\s+tutorials?|guitar\s+(?:company|builder|brand))\b",
    re.I,
)
_CONTEXTUAL_ENTITY_FOLLOWUP_RE = re.compile(
    r"\b(?:he|him|his|she|her|hers|they|them|their|it|its|that|those|"
    r"the\s+(?:player|course|product|song))\b",
    re.I,
)


@dataclass(frozen=True)
class CorpusEntityEvidence:
    candidate: bool
    strong: bool
    anchors: tuple[str, ...]
    matching_results: int
    distinct_threads: int
    reason: str


@dataclass
class AnswerRouteTrace:
    """A privacy-safe trace of the route stages for one Ask request."""

    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    classification: str = "pending"
    route: AnswerRoute = "guardrail"
    corpus_probe: str = "not_needed"
    retrieval: str = "not_started"
    evidence: str = "not_started"
    synthesis: str = "not_started"
    verification: str = "not_started"
    displayed_answer: str = "not_started"
    fallback: str = "none"

    def event(self) -> dict[str, str]:
        return {
            "traceId": self.trace_id,
            "classification": self.classification,
            "route": self.route,
            "corpusProbe": self.corpus_probe,
            "retrieval": self.retrieval,
            "evidence": self.evidence,
            "synthesis": self.synthesis,
            "verification": self.verification,
            "displayedAnswer": self.displayed_answer,
            "fallback": self.fallback,
        }


def is_corpus_entity_candidate(question: str, decision: Mapping[str, Any]) -> bool:
    """Return whether a guarded unknown may be established by public SGF evidence."""

    if decision.get("domain") != "off_domain":
        return False
    if decision.get("intent") != "unknown":
        return False
    if _PRIVATE_ENTITY_RE.search(question or ""):
        return False
    return _ENTITY_QUESTION_RE.search(question or "") is not None and bool(entity_anchors(question))


def entity_anchors(question: str) -> tuple[str, ...]:
    """Extract stable content words without maintaining a name/product whitelist."""

    stripped = _ENTITY_BOILERPLATE_RE.sub(" ", question or "")
    anchors: list[str] = []
    for token in _TOKEN_RE.findall(stripped.lower()):
        if len(token) < 2 or token in anchors:
            continue
        anchors.append(token)
    return tuple(anchors[:8])


def contextual_entity_probe_question(
    question: str,
    conversation_context: Sequence[str],
) -> str | None:
    """Return a prior user entity question for a referential follow-up.

    The caller still has to prove that prior question against public SGF
    results. Assistant text alone never establishes steel-guitar context.
    """

    if (
        not conversation_context
        or _CONTEXTUAL_ENTITY_FOLLOWUP_RE.search(question or "") is None
    ):
        return None
    for item in reversed(conversation_context):
        normalized = " ".join(str(item or "").split())
        if not normalized.casefold().startswith("user:"):
            continue
        prior_question = normalized.split(":", 1)[1].strip()
        if (
            _PRIVATE_ENTITY_RE.search(prior_question) is None
            and _ENTITY_QUESTION_RE.search(prior_question) is not None
            and entity_anchors(prior_question)
        ):
            return prior_question
        return None
    return None


def evaluate_corpus_entity_evidence(
    question: str,
    results: Sequence[Mapping[str, Any]],
) -> CorpusEntityEvidence:
    """Require repeat or exact SGF evidence before promoting an unknown entity."""

    anchors = entity_anchors(question)
    if not anchors:
        return CorpusEntityEvidence(True, False, anchors, 0, 0, "no_entity_anchors")

    matching = 0
    exact_match = False
    context_match = False
    threads: set[str] = set()
    anchor_phrase = " ".join(anchors)
    required = 1 if len(anchors) == 1 else max(2, (len(anchors) + 1) // 2)

    for result in results:
        if not _is_public_sgf_result(result):
            continue
        title = str(result.get("thread_title") or result.get("title") or "")
        excerpt = str(result.get("excerpt") or result.get("text") or "")
        haystack = " ".join(_TOKEN_RE.findall(f"{title} {excerpt}".lower()))
        result_has_context = _STEEL_RESULT_CONTEXT_RE.search(f"{title} {excerpt}") is not None
        if result_has_context:
            context_match = True
        covered = sum(1 for anchor in anchors if re.search(rf"\b{re.escape(anchor)}\b", haystack))
        if covered < required:
            continue
        matching += 1
        thread_key = str(
            result.get("thread_id")
            or result.get("thread_url")
            or result.get("url")
            or result.get("chunk_id")
            or matching
        )
        threads.add(thread_key)
        if anchor_phrase and anchor_phrase in haystack and result_has_context:
            exact_match = True

    distinct_threads = len(threads)
    strong = exact_match or (distinct_threads >= 2 and context_match)
    reason = "exact_sgf_match" if exact_match else "repeated_sgf_matches" if strong else "insufficient_sgf_matches"
    return CorpusEntityEvidence(True, strong, anchors, matching, distinct_threads, reason)


def corpus_promoted_decision(question: str) -> dict[str, Any]:
    """Build the source-backed classifier contract after the corpus proves context."""

    lesson_lookup = _LESSON_ENTITY_RE.search(question or "") is not None
    return {
        "domain": "steel_guitar",
        "intent": "lesson_lookup" if lesson_lookup else "forum_wisdom",
        "needs_sources": True,
        "needs_fretboard": False,
        "needs_copedent": False,
        "retrieval_allowed": True,
        "allowed_answer_shape": "source_backed",
    }


def select_answer_route(
    decision: Mapping[str, Any],
    *,
    deterministic_available: bool = False,
) -> AnswerRoute:
    """Select the public product route from the classifier contract."""

    source_backed = bool(decision.get("needs_sources") and decision.get("retrieval_allowed"))
    if source_backed and deterministic_available:
        return "hybrid"
    if source_backed:
        return "source_backed_rag"
    if decision.get("domain") == "steel_guitar" and decision.get("allowed_answer_shape") != "guardrail_refusal":
        return "deterministic"
    return "guardrail"


def deterministic_subquestion_for_hybrid(question: str) -> str | None:
    """Return a focused deterministic subquestion when a query asks for both paths."""

    if _SOURCE_CONTEXT_RE.search(question or "") is None:
        return None
    if _POSITION_REQUEST_RE.search(question or "") is None:
        return None
    chord_match = _CHORD_TOKEN_RE.search(question or "")
    if chord_match is None:
        return None
    chord = re.sub(r"\s+", "", chord_match.group(1))
    return f"Where can I play a {chord}?"


def hybrid_promoted_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Promote a deterministic chord decision when source context is also requested."""

    promoted = dict(decision)
    promoted.update(
        {
            "domain": "steel_guitar",
            "needs_sources": True,
            "needs_fretboard": True,
            "needs_copedent": True,
            "retrieval_allowed": True,
            "allowed_answer_shape": "source_backed",
        }
    )
    return promoted


def _is_public_sgf_result(result: Mapping[str, Any]) -> bool:
    url = str(result.get("thread_url") or result.get("url") or "").lower()
    source_system = str(result.get("source_system") or "").lower()
    source_kind = str(result.get("source_kind") or "").lower()
    return bool(
        "steelguitarforum.com" in url
        or source_system.startswith("sgf")
        or source_kind.startswith("forum")
    )
