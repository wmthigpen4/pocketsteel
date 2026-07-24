"""Private-review curated guidance retrieval.

This module is deliberately separate from SGF/forum retrieval. It reads the
ignored local curated-guidance JSONL only when an explicit feature flag is set,
uses lightweight local scoring, and returns short excerpts rather than full
private-review bodies.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


DEFAULT_CURATED_GUIDANCE_JSONL = Path("corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl")
ENABLE_CURATED_GUIDANCE_ENV = "ENABLE_CURATED_GUIDANCE_RETRIEVAL"
EXCERPT_LIMIT = 500

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "for",
    "give",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "over",
    "show",
    "the",
    "to",
    "used",
    "using",
    "what",
    "with",
}
STEEL_QUERY_TERMS = {
    "a+b",
    "b+c",
    "bar",
    "blocking",
    "copedent",
    "dominant",
    "e9",
    "fret",
    "grip",
    "harmonized",
    "lever",
    "lick",
    "pedal",
    "pick",
    "scale",
    "split",
    "steel",
    "string",
    "tuning",
    "vertical",
}
EXCLUDE_FLAGS = {
    "body_under_100_words",
    "missing_topic_tags",
    "no_steel_specific_terms",
    "possible_transcript_residue",
}
DEMOTE_FLAGS = {
    "body_over_reasonable_chunk_size",
    "broad_combined_card",
    "contains_player_should_phrase",
    "first_person_instructor_phrasing",
    "possible_duplicate_files_by_hash",
}


@dataclass(frozen=True)
class CuratedGuidanceResult:
    title: str
    source_filename: str
    source_path: str
    content_layer: str
    visibility: str
    score: float
    quality_flags: tuple[str, ...]
    excerpt: str

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "source_filename": self.source_filename,
            "source_path": self.source_path,
            "content_layer": self.content_layer,
            "visibility": self.visibility,
            "score": self.score,
            "quality_flags": list(self.quality_flags),
            "excerpt": self.excerpt,
        }


def curated_guidance_retrieval_enabled(env: Mapping[str, str] | None = None) -> bool:
    value = (env or os.environ).get(ENABLE_CURATED_GUIDANCE_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z0-9+#]+(?:[-+][a-zA-Z0-9+#]+)*", text)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def phrase_variants(term: str) -> set[str]:
    lowered = term.lower()
    variants = {lowered, lowered.replace("-", " "), lowered.replace("+", " ")}
    if "b-to-bb" in lowered or "b to bb" in lowered:
        variants.update({"b to bb", "bb lever", "vertical"})
    if "split" in lowered:
        variants.update({"split tuning", "tune a split", "tuning splits"})
    if "pick blocking" in lowered:
        variants.update({"pick blocking", "blocking", "right hand"})
    if "string 6" in lowered:
        variants.update({"string 6", "6th string", "sixth string"})
    return {variant for variant in variants if variant}


def is_teaching_style_query(query: str) -> bool:
    lowered = query.lower()
    tokens = set(tokenize(lowered))
    if tokens & STEEL_QUERY_TERMS:
        return True
    return any(phrase in lowered for phrase in ("b-to-bb", "b to bb", "pick blocking", "b+c", "a+b"))


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            if row.get("content_layer") != "curated_guidance":
                raise ValueError(f"{path}:{line_number} content_layer is not curated_guidance")
            rows.append(row)
    return rows


def _is_broad_combined_card(row: Mapping[str, object]) -> bool:
    source_path = str(row.get("source_path") or "").lower()
    title = str(row.get("title") or "").lower()
    return (
        "pre_embedding_cleanup_confirmation" in source_path
        or "cleanup confirmation" in title
        or source_path.startswith("spec/")
    )


def _duplicate_hashes(rows: Iterable[Mapping[str, object]]) -> set[str]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        source_hash = str(row.get("source_sha256") or "")
        if source_hash:
            by_hash[source_hash].append(str(row.get("source_path") or ""))
    return {source_hash for source_hash, paths in by_hash.items() if len(paths) > 1}


def row_quality_flags(row: Mapping[str, object], duplicate_hashes: set[str] | None = None) -> tuple[str, ...]:
    flags = {str(flag) for flag in row.get("quality_flags") or []}
    if duplicate_hashes and str(row.get("source_sha256") or "") in duplicate_hashes:
        flags.add("possible_duplicate_files_by_hash")
    if _is_broad_combined_card(row):
        flags.add("broad_combined_card")
    return tuple(sorted(flags))


def row_is_retrievable(row: Mapping[str, object], duplicate_hashes: set[str] | None = None) -> bool:
    if row.get("content_layer") != "curated_guidance":
        return False
    if row.get("visibility") != "private_review":
        return False
    if row.get("needs_review") is not True:
        return False
    flags = set(row_quality_flags(row, duplicate_hashes))
    return not bool(flags & EXCLUDE_FLAGS)


def searchable_text(row: Mapping[str, object]) -> str:
    metadata_parts = [
        str(row.get("title") or ""),
        str(row.get("source_path") or ""),
        " ".join(str(item) for item in row.get("topics") or []),
        " ".join(str(item) for item in row.get("technique_tags") or []),
        " ".join(str(item) for item in row.get("pedals_levers") or []),
        " ".join(str(item) for item in row.get("strings") or []),
        " ".join(str(item) for item in row.get("keys") or []),
        str(row.get("instrument") or ""),
    ]
    return "\n".join(metadata_parts + [str(row.get("body") or "")])


def doc_term_counter(row: Mapping[str, object]) -> Counter[str]:
    title_path = f"{row.get('title', '')} {row.get('source_path', '')}"
    metadata = " ".join(
        [
            " ".join(str(item) for item in row.get("topics") or []),
            " ".join(str(item) for item in row.get("technique_tags") or []),
            " ".join(str(item) for item in row.get("pedals_levers") or []),
            str(row.get("instrument") or ""),
        ]
    )
    body = str(row.get("body") or "")
    counts: Counter[str] = Counter()
    counts.update({term: count * 4 for term, count in Counter(tokenize(title_path)).items()})
    counts.update({term: count * 3 for term, count in Counter(tokenize(metadata)).items()})
    counts.update(Counter(tokenize(body)))
    return counts


def build_idf(rows: list[Mapping[str, object]]) -> dict[str, float]:
    documents = [set(doc_term_counter(row)) for row in rows]
    doc_count = len(documents)
    term_doc_counts: Counter[str] = Counter()
    for terms in documents:
        term_doc_counts.update(terms)
    return {term: math.log((doc_count + 1) / (count + 0.5)) + 1.0 for term, count in term_doc_counts.items()}


def query_terms(query: str) -> list[str]:
    terms = tokenize(query)
    lowered = query.lower()
    for phrase in ("pick blocking", "b+c", "a+b", "b-to-bb", "b to bb", "string 6", "harmonized scale"):
        if phrase in lowered:
            terms.append(phrase)
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped


def phrase_match_score(row: Mapping[str, object], raw_terms: list[str]) -> tuple[float, list[str]]:
    text = searchable_text(row).lower()
    score = 0.0
    matches: list[str] = []
    for term in raw_terms:
        for variant in phrase_variants(term):
            if variant and variant in text:
                score += 2.5 if " " in variant or "+" in variant or "-" in variant else 1.0
                matches.append(term)
                break
    return score, sorted(set(matches))


def score_row(row: Mapping[str, object], query: str, idf: Mapping[str, float]) -> tuple[float, list[str]]:
    raw_terms = query_terms(query)
    counts = doc_term_counter(row)
    matched: set[str] = set()
    score = 0.0
    for term in raw_terms:
        if " " in term or term not in idf:
            continue
        count = counts.get(term, 0)
        if count:
            matched.add(term)
            score += idf.get(term, 1.0) * (1.0 + math.log1p(min(count, 12)))
    phrase_score, phrase_matches = phrase_match_score(row, raw_terms)
    matched.update(phrase_matches)
    score += phrase_score
    return score, sorted(matched)


def make_excerpt(body: str, matched_terms: list[str], *, limit: int = EXCERPT_LIMIT) -> str:
    normalized = re.sub(r"\s+", " ", body).strip()
    if not normalized:
        return ""
    if limit <= 3:
        return normalized[:limit]
    lowered = normalized.lower()
    index = -1
    for term in matched_terms:
        term_lower = term.lower().replace("\\+", "+")
        if len(term_lower) < 3:
            continue
        index = lowered.find(term_lower)
        if index >= 0:
            break
    if index < 0:
        excerpt = normalized[:limit]
    else:
        prefix = "..." if index > 180 else ""
        start = max(0, index - 180)
        excerpt_limit = limit - len(prefix)
        end = min(len(normalized), start + excerpt_limit)
        excerpt = normalized[start:end]
        if prefix:
            excerpt = prefix + excerpt
        if end < len(normalized):
            excerpt = excerpt[: limit - 3] + "..."
    return excerpt[:limit]


def search_rows(rows: list[dict[str, object]], query: str, *, top_k: int = 5) -> list[CuratedGuidanceResult]:
    if top_k <= 0 or not is_teaching_style_query(query):
        return []
    duplicate_hashes = _duplicate_hashes(rows)
    candidates = [row for row in rows if row_is_retrievable(row, duplicate_hashes)]
    if not candidates:
        return []
    idf = build_idf(candidates)
    scored: list[tuple[float, str, list[str], dict[str, object], tuple[str, ...]]] = []
    for row in candidates:
        score, matched_terms = score_row(row, query, idf)
        if score <= 0 or not matched_terms:
            continue
        flags = row_quality_flags(row, duplicate_hashes)
        if set(flags) & DEMOTE_FLAGS:
            score *= 0.72
        scored.append((round(score, 4), str(row.get("source_path") or ""), matched_terms, row, flags))

    results: list[CuratedGuidanceResult] = []
    for score, _, matched_terms, row, flags in sorted(scored, key=lambda item: (-item[0], item[1]))[:top_k]:
        results.append(
            CuratedGuidanceResult(
                title=str(row.get("title") or ""),
                source_filename=str(row.get("source_filename") or ""),
                source_path=str(row.get("source_path") or ""),
                content_layer=str(row.get("content_layer") or ""),
                visibility=str(row.get("visibility") or ""),
                score=score,
                quality_flags=flags,
                excerpt=make_excerpt(str(row.get("body") or ""), matched_terms),
            )
        )
    return results


def search_curated_guidance(
    query: str,
    *,
    input_path: Path = DEFAULT_CURATED_GUIDANCE_JSONL,
    top_k: int = 5,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, object]]:
    """Search private-review curated guidance only when the feature flag is enabled."""

    if not curated_guidance_retrieval_enabled(env):
        return []
    if not input_path.exists():
        return []
    rows = read_jsonl(input_path)
    return [result.as_dict() for result in search_rows(rows, query, top_k=top_k)]
