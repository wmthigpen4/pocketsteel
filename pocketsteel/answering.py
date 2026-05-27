"""Source-backed answer generation for the local API."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol, cast

from pocketsteel.api_contract import AnswerMode, SourceCitation

from pocketsteel.text import shorten


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
    return {
        "title": source.get("thread_title") or "Source thread",
        "forumName": source.get("forum_name") or "Steel Guitar Forum",
        "url": source.get("thread_url") or "",
        "excerpt": source.get("excerpt") or "",
        "score": float(source.get("score") or 0.0),
        "chunkId": source.get("chunk_id") or "",
        "postUid": source.get("post_uid") or None,
    }


def mode_guidance(mode: str) -> str:
    if mode == "gear":
        return "Emphasize likely causes, diagnostic steps, safety notes, and source-backed forum wisdom."
    if mode == "copedent":
        return "Use interval-first language. Include strings, frets, pedals, levers, and interval functions when the sources support them."
    if mode == "tab":
        return "Explain intervals, chord tones, pedal/lever purpose, and impossible combinations when relevant. Do not generate copyrighted song tab."
    if mode == "practice":
        return "Return practical numbered practice steps grounded in the retrieved sources."
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


class DeterministicAnswerProvider:
    """Offline provider used when no live LLM provider is configured."""

    def answer(self, request: AnswerRequest, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "No strong source match found in the current corpus for that question."

        intro_by_mode = {
            "gear": "The retrieved forum sources point to a diagnostic path rather than a single guaranteed fix.",
            "copedent": "The retrieved forum sources point to the change in terms of musical function first, then mechanics.",
            "tab": "The retrieved forum sources support an explanation of the move, not copyrighted song tab.",
            "practice": "Based on the retrieved forum sources, here is a practical way to work on it.",
            "ask": "The retrieved forum sources suggest this answer.",
        }
        lines = [intro_by_mode.get(request.mode, intro_by_mode["ask"])]

        if request.mode == "gear":
            lines.extend(
                [
                    "",
                    "1. Compare the symptom against the first source before replacing parts. [1]",
                    "2. Change one variable at a time: guitar, cable, pedal, amp, power, or room. [1]",
                    "3. If the source involves power, grounding, or amplifier internals, treat it as a safety issue and use a qualified tech. [1]",
                ]
            )
        elif request.mode == "copedent":
            lines.extend(
                [
                    "",
                    "Think interval-first: identify what scale degree or chord tone the change creates, then map it to the string, pedal, or lever named in the source. [1]",
                    "If several players describe different setups, treat that as guitar-dependent rather than one universal rule. [1]",
                ]
            )
        elif request.mode == "tab":
            lines.extend(
                [
                    "",
                    "I can explain the interval movement and pedal/lever purpose from the sources, but I should not generate copyrighted song tab. [1]",
                    "Use the source card to inspect the supported move and adapt it to your own phrase. [1]",
                ]
            )
        elif request.mode == "practice":
            lines.extend(
                [
                    "",
                    "1. Isolate the move or sound named in the strongest source. [1]",
                    "2. Practice it slowly enough to hear the interval or chord motion.",
                    "3. Move it to one nearby fretboard position before speeding up.",
                ]
            )
        else:
            lines.extend(["", f"The strongest source is “{sources[0].get('thread_title') or 'Source thread'}.” [1]"])

        for index, source in enumerate(sources[:3], 1):
            system = source_label(str(source.get("source_system") or ""))
            title = source.get("thread_title") or "Source thread"
            lines.append(f"- [{index}] {system}, {source.get('forum_name') or 'Steel Guitar Forum'}: {title}")
        return "\n".join(lines)


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
                    "Do not invent unsupported claims. Do not generate copyrighted song tab."
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
    return bool(re.search(r"\bno strong source match\b|\bnot answer this confidently\b", answer, re.I))


def concise_source_cards(sources: list[dict[str, Any]]) -> list[SourceCitation]:
    cards = []
    for source in sources:
        card = source_to_card(source)
        card["excerpt"] = shorten(card["excerpt"], 420)
        cards.append(card)
    return cards
