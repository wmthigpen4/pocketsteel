#!/usr/bin/env python3
"""Offline retrieval fixture for private-review curated guidance.

This intentionally uses lightweight local keyword/BM25-style scoring only. It
does not call hosted LLMs, touch Chroma, write embeddings, or wire curated
guidance into the production answer path.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl")
DEFAULT_OUTPUT = Path("corpus-private/reports/curated-guidance-retrieval-eval.md")
DEFAULT_JSON_OUTPUT = Path("corpus-private/reports/curated-guidance-retrieval-eval.json")
EXCERPT_LIMIT = 500
TOP_K = 5

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

TEST_QUERIES: tuple[dict[str, Any], ...] = (
    {
        "query": "How do I tune a split on string 6?",
        "expected_topics": ["split tuning", "string 6", "copedent"],
        "terms": ["split", "splits", "tune", "tuning", "string 6", "6th string", "copedent"],
    },
    {
        "query": "What is pick blocking?",
        "expected_topics": ["blocking", "right hand"],
        "terms": ["pick blocking", "blocking", "block", "right hand", "picking"],
    },
    {
        "query": "What are B+C pedals used for?",
        "expected_topics": ["B+C pedals", "pedal movement"],
        "terms": ["b+c", "b pedal", "c pedal", "pedals", "pedal movement"],
    },
    {
        "query": "Teach me a dominant lick on E9.",
        "expected_topics": ["dominant harmony", "licks", "E9"],
        "terms": ["dominant", "lick", "e9", "phrase", "solo"],
    },
    {
        "query": "How do I play a harmonized scale over a dominant chord?",
        "expected_topics": ["harmonized scale", "dominant harmony"],
        "terms": ["harmonized", "scale", "dominant", "chord", "harmony"],
    },
    {
        "query": "Show me a 1-6-2-5 style lick on E9.",
        "expected_topics": ["1-6-2-5", "licks", "E9"],
        "terms": ["1-6-2-5", "1 6 2 5", "one six two five", "lick", "e9"],
    },
    {
        "query": "Can I play the lick without a B-to-Bb lever?",
        "expected_topics": ["B-to-Bb", "levers", "licks"],
        "terms": ["b-to-bb", "b to bb", "bb lever", "vertical", "lever", "lick"],
    },
    {
        "query": "How do I practice right-hand blocking?",
        "expected_topics": ["blocking", "right hand", "practice"],
        "terms": ["right hand", "blocking", "practice", "exercise", "picking"],
    },
    {
        "query": "How do I use E raises in a harmonized scale?",
        "expected_topics": ["E raises", "harmonized scale", "F lever"],
        "terms": ["e raise", "e raises", "f lever", "harmonized", "scale"],
    },
    {
        "query": "Give me a practice exercise using strings, frets, and pedals.",
        "expected_topics": ["practice", "strings/frets/pedals"],
        "terms": ["practice", "exercise", "strings", "frets", "pedals", "drill"],
    },
)


@dataclass(frozen=True)
class ScoredResult:
    row: dict[str, Any]
    score: float
    matched_terms: list[str]
    useful: str
    excerpt: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate offline curated-guidance keyword retrieval.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Private curated-guidance JSONL path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Private markdown report path.")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT), help="Private JSON report path.")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="Results per query.")
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z0-9+#]+(?:[-+][a-zA-Z0-9+#]+)*", text)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def phrase_variants(term: str) -> set[str]:
    lowered = term.lower()
    variants = {lowered}
    variants.add(lowered.replace("-", " "))
    variants.add(lowered.replace("+", " "))
    variants.add(lowered.replace("+", "\\+"))
    if "b-to-bb" in lowered:
        variants.update({"b to bb", "bb lever", "vertical"})
    if "string 6" in lowered:
        variants.update({"6th string", "string six"})
    if "1-6-2-5" in lowered:
        variants.update({"1 6 2 5", "one six two five"})
    return {variant for variant in variants if variant}


def query_terms(query: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for source in (query["query"], " ".join(query["expected_topics"]), " ".join(query["terms"])):
        terms.extend(tokenize(source))
    terms.extend(str(term).lower() for term in query["terms"])
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def searchable_text(row: dict[str, Any]) -> str:
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


def doc_term_counter(row: dict[str, Any]) -> Counter[str]:
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


def build_idf(rows: list[dict[str, Any]]) -> dict[str, float]:
    documents = [set(doc_term_counter(row)) for row in rows]
    doc_count = len(documents)
    term_doc_counts: Counter[str] = Counter()
    for terms in documents:
        term_doc_counts.update(terms)
    return {term: math.log((doc_count + 1) / (count + 0.5)) + 1.0 for term, count in term_doc_counts.items()}


def phrase_match_score(row: dict[str, Any], raw_terms: list[str]) -> tuple[float, list[str]]:
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


def score_row(row: dict[str, Any], query: dict[str, Any], idf: dict[str, float]) -> tuple[float, list[str]]:
    raw_terms = query_terms(query)
    token_terms = [term for term in raw_terms if " " not in term and term in idf]
    counts = doc_term_counter(row)
    matched: set[str] = set()
    score = 0.0
    for term in token_terms:
        count = counts.get(term, 0)
        if count:
            matched.add(term)
            score += idf.get(term, 1.0) * (1.0 + math.log1p(min(count, 12)))
    phrase_score, phrase_matches = phrase_match_score(row, raw_terms)
    matched.update(phrase_matches)
    score += phrase_score

    flags = set(str(flag) for flag in row.get("quality_flags") or [])
    if "body_under_100_words" in flags or "no_steel_specific_terms" in flags:
        score *= 0.82
    if "body_over_reasonable_chunk_size" in flags:
        score *= 0.9
    return round(score, 4), sorted(matched)


def make_excerpt(body: str, matched_terms: list[str]) -> str:
    normalized = re.sub(r"\s+", " ", body).strip()
    if not normalized:
        return ""
    lowered = normalized.lower()
    index = -1
    for term in matched_terms:
        term_lower = term.lower().replace("\\+", "+")
        if not term_lower or len(term_lower) < 3:
            continue
        index = lowered.find(term_lower)
        if index >= 0:
            break
    if index < 0:
        excerpt = normalized[:EXCERPT_LIMIT]
    else:
        start = max(0, index - 180)
        end = min(len(normalized), start + EXCERPT_LIMIT)
        excerpt = normalized[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(normalized):
            excerpt += "..."
    return excerpt[: EXCERPT_LIMIT + 6]


def usefulness(row: dict[str, Any], score: float, matched_terms: list[str], query: dict[str, Any]) -> str:
    if score <= 0 or not matched_terms:
        return "no"
    flags = set(str(flag) for flag in row.get("quality_flags") or [])
    expected_blob = " ".join(query["expected_topics"] + query["terms"]).lower()
    title_path = f"{row.get('title', '')} {row.get('source_path', '')}".lower()
    matched_blob = " ".join(matched_terms).lower()
    topic_hit = any(term in matched_blob or term in title_path for term in tokenize(expected_blob))
    if topic_hit and not ({"body_under_100_words", "no_steel_specific_terms"} & flags):
        return "yes"
    if topic_hit:
        return "review"
    if score >= 10 and not flags:
        return "review"
    return "no"


def evaluate(rows: list[dict[str, Any]], *, top_k: int) -> list[dict[str, Any]]:
    idf = build_idf(rows)
    query_results: list[dict[str, Any]] = []
    for query in TEST_QUERIES:
        scored: list[ScoredResult] = []
        for row in rows:
            score, matched_terms = score_row(row, query, idf)
            if score <= 0:
                continue
            useful = usefulness(row, score, matched_terms, query)
            scored.append(
                ScoredResult(
                    row=row,
                    score=score,
                    matched_terms=matched_terms,
                    useful=useful,
                    excerpt=make_excerpt(str(row.get("body") or ""), matched_terms),
                )
            )
        top = sorted(scored, key=lambda item: (-item.score, str(item.row.get("source_path") or "")))[:top_k]
        query_results.append(
            {
                "query": query["query"],
                "expected_topics": query["expected_topics"],
                "results": [result_to_dict(result) for result in top],
            }
        )
    return query_results


def result_to_dict(result: ScoredResult) -> dict[str, Any]:
    row = result.row
    return {
        "title": row.get("title"),
        "source_filename": row.get("source_filename"),
        "source_path": row.get("source_path"),
        "score": result.score,
        "matched_terms": result.matched_terms,
        "content_layer": row.get("content_layer"),
        "visibility": row.get("visibility"),
        "quality_flags": row.get("quality_flags") or [],
        "useful": result.useful,
        "excerpt": result.excerpt,
    }


def summarize(query_results: list[dict[str, Any]]) -> dict[str, Any]:
    useful_counts: Counter[str] = Counter()
    topic_strength: dict[str, str] = {}
    for item in query_results:
        results = item["results"]
        top_useful = [result.get("useful") for result in results[:3]]
        useful_counts.update(top_useful)
        if any(value == "yes" for value in top_useful):
            topic_strength[item["query"]] = "strong"
        elif any(value == "review" for value in top_useful):
            topic_strength[item["query"]] = "review"
        else:
            topic_strength[item["query"]] = "weak"
    return {
        "query_count": len(query_results),
        "top3_usefulness_counts": dict(useful_counts),
        "topic_strength": topic_strength,
    }


def markdown_escape(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(input_path: Path, query_results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# Curated Guidance Retrieval Eval",
        "",
        "Private/local retrieval QA report for `content_layer=curated_guidance`. Do not commit this generated report unless explicitly approved.",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Input: `{input_path.as_posix()}`",
        f"- Queries: {summary['query_count']}",
        "",
        "## Summary",
        "",
        "This lightweight fixture uses local keyword/BM25-style matching only. It does not call hosted LLMs, write embeddings, touch Chroma, or wire curated guidance into app retrieval.",
        "",
        "Top-3 usefulness counts:",
        "",
    ]
    for key, value in sorted(summary["top3_usefulness_counts"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "Topic strength:", ""])
    for query, strength in summary["topic_strength"].items():
        lines.append(f"- `{strength}`: {query}")
    lines.extend(["", "## Query Results", ""])
    for item in query_results:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Expected topics: {', '.join(item['expected_topics'])}",
                "",
                "| Rank | Useful | Score | Title | Source filename | Matched terms | Content layer | Visibility | Quality flags | Excerpt |",
                "| ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for index, result in enumerate(item["results"], start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        markdown_escape(result["useful"]),
                        f"{result['score']:.4f}",
                        markdown_escape(result["title"]),
                        markdown_escape(result["source_filename"]),
                        markdown_escape(", ".join(result["matched_terms"])),
                        markdown_escape(result["content_layer"]),
                        markdown_escape(result["visibility"]),
                        markdown_escape(", ".join(result["quality_flags"]) or "none"),
                        markdown_escape(result["excerpt"]),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if args.top_k <= 0:
        raise SystemExit("--top-k must be greater than zero")
    if not input_path.exists():
        raise SystemExit(f"Input JSONL does not exist: {input_path}")

    rows = read_jsonl(input_path)
    query_results = evaluate(rows, top_k=args.top_k)
    summary = summarize(query_results)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": input_path.as_posix(),
        "summary": summary,
        "queries": query_results,
    }

    output_path = Path(args.output)
    json_output_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(input_path, query_results, summary), encoding="utf-8")
    json_output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evaluated {len(TEST_QUERIES)} curated guidance query fixture(s).")
    print(f"Rows searched: {len(rows)}")
    print(f"Wrote markdown report: {output_path}")
    print(f"Wrote JSON report: {json_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
