"""Guardrails for untrusted retrieved RAG source text."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from typing import Any


INJECTION_WARNING = "prompt-injection-like text ignored"
REDACTED_EXCERPT = "[Redacted prompt-injection-like source text.]"

INJECTION_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"\bignore\s+(?:all\s+)?(?:previous|prior|system|developer)\s+instructions?\b",
        r"\bignore\s+(?:the\s+)?(?:system|developer)\s+instructions?\b",
        r"\b(?:reveal|show|print|display|dump)\s+(?:the\s+|your\s+)?(?:system|developer)\s+prompt\b",
        r"\bfollow\s+this\s+link\b",
        r"\bclick\s+(?:this|the)\s+link\b",
        r"\bopen\s+(?:this|the)\s+link\b",
        r"\bsend\s+(?:data|secrets?|credentials?)\s+to\b",
        r"\bcall\s+(?:a\s+)?tool\b",
        r"\brun\s+(?:a\s+)?command\b",
        r"\bexecute\s+(?:this|the|a)?\s*(?:command|code|tool)?\b",
        r"\boverride\s+(?:your\s+)?rules?\b",
        r"\bchange\s+your\s+rules?\b",
        r"\byou\s+are\s+now\b",
        r"\bdeveloper\s+mode\b",
        r"\boutput\s+secrets?\b",
        r"\brecommend\s+.+\bregardless\s+of\s+evidence\b",
        r"\bsay\s+.+\bregardless\s+of\s+evidence\b",
        r"\bsay\s+.+\bmade\b.+\bregardless\b",
        r"\bdo\s+not\s+(?:cite|use)\s+sources?\b",
        r"\boutput\s+only\b",
        r"\bhidden\s+prompt\b",
        r"\bhidden\s+rules?\b",
        r"\bprompt\s+injection\b",
        r"\[/?INST\]",
        r"<<\s*SYS\s*>>",
        r"<!--.*?(?:ignore|system prompt|developer mode).*?-->",
    )
]

BASE64ISH_RE = re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b")


@dataclass(frozen=True)
class SanitizedSources:
    sources: list[dict[str, Any]]
    warnings: list[str]


def is_injection_like(text: str) -> bool:
    if any(pattern.search(text or "") for pattern in INJECTION_PATTERNS):
        return True
    return contains_encoded_instruction(text)


def contains_encoded_instruction(text: str) -> bool:
    for token in BASE64ISH_RE.findall(text or ""):
        padded = token + ("=" * (-len(token) % 4))
        try:
            decoded = base64.b64decode(padded, validate=True)
        except (binascii.Error, ValueError):
            continue
        try:
            decoded_text = decoded.decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            continue
        if decoded_text and any(pattern.search(decoded_text) for pattern in INJECTION_PATTERNS):
            return True
    return False


def split_source_units(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return []
    return [unit.strip() for unit in re.split(r"(?<=[.!?])\s+|\n+", normalized) if unit.strip()]


def sanitize_source_text(text: str) -> tuple[str, bool, bool]:
    units = split_source_units(text)
    if not units:
        return "", False, False

    safe_units = [unit for unit in units if not is_injection_like(unit)]
    detected = len(safe_units) != len(units)
    if not detected and not is_injection_like(text):
        return text.strip(), False, False

    if not safe_units:
        return REDACTED_EXCERPT, True, True

    sanitized = " ".join(safe_units).strip()
    original_words = len(re.findall(r"\w+", text))
    safe_words = len(re.findall(r"\w+", sanitized))
    mostly_malicious = safe_words < 8 or (original_words > 0 and safe_words / original_words < 0.35)
    if mostly_malicious:
        return REDACTED_EXCERPT, True, True
    return sanitized, True, False


def sanitize_retrieved_sources(sources: list[dict[str, Any]]) -> SanitizedSources:
    sanitized_sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    warned = False

    for source in sources:
        excerpt = str(source.get("excerpt") or "")
        sanitized_excerpt, detected, drop = sanitize_source_text(excerpt)
        if detected and not warned:
            warnings.append(INJECTION_WARNING)
            warned = True
        if drop:
            continue
        clean_source = dict(source)
        clean_source["excerpt"] = sanitized_excerpt
        sanitized_sources.append(clean_source)

    return SanitizedSources(sources=sanitized_sources, warnings=warnings)
