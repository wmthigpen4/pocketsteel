"""Small deterministic text normalizers for music symbols."""

from __future__ import annotations

import re


ACCIDENTAL_SYMBOL_TRANSLATION = str.maketrans(
    {
        "♭": "b",
        "♯": "#",
        "𝄫": "bb",
        "𝄪": "##",
    }
)


def normalize_accidental_symbols(text: str) -> str:
    """Normalize common Unicode accidental symbols to ASCII chord spelling."""

    return (text or "").translate(ACCIDENTAL_SYMBOL_TRANSLATION)


def normalize_spelled_accidentals(text: str) -> str:
    """Normalize note spellings like A-flat, C sharp, and B-double-flat."""

    normalized = normalize_accidental_symbols(text or "")
    normalized = re.sub(
        r"\b([a-gA-G])[\s-]+double[\s-]+sharp\b",
        lambda match: f"{match.group(1)}##",
        normalized,
        flags=re.I,
    )
    normalized = re.sub(
        r"\b([a-gA-G])[\s-]+double[\s-]+flat\b",
        lambda match: f"{match.group(1)}bb",
        normalized,
        flags=re.I,
    )
    normalized = re.sub(
        r"\b([a-gA-G])[\s-]+sharp\b",
        lambda match: f"{match.group(1)}#",
        normalized,
        flags=re.I,
    )
    normalized = re.sub(
        r"\b([a-gA-G])[\s-]+flat\b",
        lambda match: f"{match.group(1)}b",
        normalized,
        flags=re.I,
    )
    return normalized
