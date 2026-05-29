"""Curated source registry helpers for answer guidance.

The registry is for explicit, human-reviewed buying/source suggestions. It is
not a scrape target and it does not imply current inventory.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parent.parent / "corpus_metadata" / "source_registry.json"


@lru_cache(maxsize=1)
def load_curated_vendor_sources() -> list[dict[str, Any]]:
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    sources = registry.get("curated_vendor_sources")
    if not isinstance(sources, list):
        return []
    return [source for source in sources if isinstance(source, dict)]


def vendor_sources_for_category(*categories: str) -> list[dict[str, Any]]:
    wanted = {category for category in categories if category}
    if not wanted:
        return load_curated_vendor_sources()
    return [source for source in load_curated_vendor_sources() if str(source.get("category") or "") in wanted]


def format_vendor_source_bullet(source: dict[str, Any]) -> str:
    name = str(source.get("name") or "").strip()
    url = str(source.get("url") or "").strip()
    description = str(source.get("short_description") or "").strip()
    caveat = str(source.get("caveat") or "").strip()
    pieces = [piece for piece in (description, caveat) if piece]
    detail = " ".join(pieces)
    if url:
        return f"- {name} — {url} — {detail}"
    return f"- {name} — {detail}"


def slide_bar_vendor_bullets() -> list[str]:
    ordered_names = {
        "Steel Guitar Shopper": 0,
        "BJS Steel Guitar Bars": 1,
        "Jim Dunlop Tonebars": 2,
        "Steel Guitar Forum Classifieds / Forum Store": 3,
    }
    sources = vendor_sources_for_category(
        "steel_guitar_accessories",
        "tone_bars",
        "used_market",
    )
    sources.sort(key=lambda source: ordered_names.get(str(source.get("name") or ""), 99))
    return [format_vendor_source_bullet(source) for source in sources]
