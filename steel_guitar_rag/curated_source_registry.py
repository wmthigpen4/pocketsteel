"""Curated source registry helpers for answer guidance.

The registry is for explicit, human-reviewed links that may be mentioned in
answers for specific intents. It is not a scrape target, not RAG evidence, and
does not imply current inventory or current organization status unless the
entry says so.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from urllib.parse import urlparse
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parent.parent / "corpus_metadata" / "source_registry.json"


@lru_cache(maxsize=1)
def load_curated_sources() -> list[dict[str, Any]]:
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    sources = registry.get("curated_sources")
    if not isinstance(sources, list):
        sources = registry.get("curated_vendor_sources")
    if not isinstance(sources, list):
        return []
    return [normalize_curated_source(source) for source in sources if isinstance(source, dict)]


def normalize_curated_source(source: dict[str, Any]) -> dict[str, Any]:
    name = str(source.get("name") or "").strip()
    category = str(source.get("category") or "").strip()
    source_id = str(source.get("id") or "").strip() or slugify(f"{category}-{name}")
    description = str(source.get("description") or source.get("short_description") or "").strip()
    source_type = str(source.get("source_type") or "").strip()
    modes = source.get("allowed_answer_modes")
    tags = source.get("tags")
    return {
        "id": source_id,
        "name": name,
        "url": str(source.get("url") or "").strip(),
        "category": category,
        "source_type": source_type,
        "description": description,
        "short_description": description,
        "caveat": str(source.get("caveat") or "").strip(),
        "last_reviewed": str(source.get("last_reviewed") or "").strip(),
        "active": bool(source.get("active", True)),
        "allowed_answer_modes": [str(mode).strip() for mode in modes] if isinstance(modes, list) else [],
        "tags": [str(tag).strip() for tag in tags] if isinstance(tags, list) else [],
    }


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "curated_source"


def filter_active_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [source for source in sources if source.get("active") is True]


def get_curated_sources_for_intent(
    intent: str,
    *,
    categories: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    wanted_categories = {category for category in categories if category}
    wanted_tags = {tag for tag in tags if tag}
    results: list[dict[str, Any]] = []
    for source in filter_active_sources(load_curated_sources()):
        modes = set(source.get("allowed_answer_modes") or [])
        source_tags = set(source.get("tags") or [])
        source_category = str(source.get("category") or "")
        if intent and intent not in modes:
            continue
        if wanted_categories and source_category not in wanted_categories:
            continue
        if wanted_tags and not (wanted_tags & source_tags):
            continue
        results.append(source)
    return results


def load_curated_vendor_sources() -> list[dict[str, Any]]:
    return get_curated_sources_for_intent("vendor_buying_guidance")


def vendor_sources_for_category(*categories: str) -> list[dict[str, Any]]:
    wanted = {category for category in categories if category}
    if not wanted:
        return load_curated_vendor_sources()
    return [source for source in load_curated_vendor_sources() if str(source.get("category") or "") in wanted]


def format_curated_links(sources: list[dict[str, Any]]) -> list[str]:
    return [format_curated_source_bullet(source) for source in sources]


def format_curated_source_bullet(source: dict[str, Any]) -> str:
    name = str(source.get("name") or "").strip()
    url = str(source.get("url") or "").strip()
    description = str(source.get("description") or source.get("short_description") or "").strip()
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
    sources = get_curated_sources_for_intent(
        "vendor_buying_guidance",
        tags=("tone_bars", "used_market"),
    )
    sources.sort(key=lambda source: ordered_names.get(str(source.get("name") or ""), 99))
    return format_curated_links(sources)


def slide_bar_vendor_source_cards() -> list[dict[str, Any]]:
    ordered_names = {
        "Steel Guitar Shopper": 0,
        "BJS Steel Guitar Bars": 1,
        "Jim Dunlop Tonebars": 2,
        "Steel Guitar Forum Classifieds / Forum Store": 3,
    }
    sources = get_curated_sources_for_intent(
        "vendor_buying_guidance",
        tags=("tone_bars", "used_market"),
    )
    sources.sort(key=lambda source: ordered_names.get(str(source.get("name") or ""), 99))
    cards: list[dict[str, Any]] = []
    for source in sources:
        description = str(source.get("description") or source.get("short_description") or "").strip()
        caveat = str(source.get("caveat") or "").strip()
        excerpt = " ".join(piece for piece in (description, caveat) if piece)
        cards.append(
            {
                "thread_title": source.get("name") or "Curated source",
                "forum_name": "Steel Guitar RAG curated source",
                "thread_url": source.get("url") or "",
                "excerpt": excerpt,
                "score": 1.0,
                "chunk_id": source.get("id") or "",
                "post_uid": None,
                "source_system": "curated_source_registry",
            }
        )
    return cards


def approved_curated_domains() -> set[str]:
    domains: set[str] = set()
    for source in filter_active_sources(load_curated_sources()):
        parsed = urlparse(str(source.get("url") or ""))
        if parsed.hostname:
            domains.add(parsed.hostname.lower().removeprefix("www."))
    return domains


def is_approved_curated_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return bool(parsed.scheme in {"http", "https"} and host in approved_curated_domains())


def answer_contains_unapproved_url(answer: str) -> bool:
    for url in re.findall(r"https?://[^\s)>\"]+", answer or ""):
        if not is_approved_curated_url(url.rstrip(".,;")):
            return True
    return False
