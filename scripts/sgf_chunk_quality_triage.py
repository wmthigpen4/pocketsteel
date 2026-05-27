#!/usr/bin/env python3
"""Read-only triage for unified SGF chunk-quality issue rows."""

from __future__ import annotations

import argparse
import csv
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_CORPUS_ROOT = Path(os.environ.get("STEEL_RAG_CORPUS_ROOT", "corpus-unified"))
DEFAULT_ISSUES = DEFAULT_CORPUS_ROOT / "reports" / "unified_chunk_issues.tsv"
DEFAULT_OUTPUT = Path("docs/chunk-quality-triage.md")

BUCKET_ORDER = (
    "false positives",
    "low-value tiny chunks",
    "oversized chunks",
    "duplicated/repeated text",
    "mostly quotes",
    "mostly links",
    "missing metadata",
    "possible mixed-topic chunks",
)


def word_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def ascii_safe(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def post_uid_count(value: str) -> int:
    return len([part for part in value.split(",") if part.strip()])


def url_count(text: str) -> int:
    return len(re.findall(r"https?://|www\.|click here", text.lower()))


def repeated_sentence_count(text: str) -> int:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if len(part.strip()) > 25]
    if len(sentences) < 2:
        return 0
    counts = Counter(sentences)
    return sum(count - 1 for count in counts.values() if count > 1)


def repeated_ngram_max(text: str, size: int = 8) -> int:
    words = word_tokens(text)
    if len(words) < size * 3:
        return 0
    ngrams = [" ".join(words[index : index + size]) for index in range(len(words) - size + 1)]
    return max(Counter(ngrams).values(), default=0)


def missing_metadata_fields(row: dict[str, str]) -> list[str]:
    required = ("chunk_id", "source_system", "forum_name", "thread_title", "thread_url", "post_uids")
    return [key for key in required if not row.get(key)]


def classify(row: dict[str, str]) -> tuple[str, str]:
    issue_type = row.get("issue_type", "")
    detail = row.get("detail", "").lower()
    excerpt = row.get("excerpt", "")
    lowered = excerpt.lower()
    tokens = word_tokens(excerpt)
    token_estimate = int(row.get("token_estimate") or 0)
    post_count = post_uid_count(row.get("post_uids", ""))

    missing = missing_metadata_fields(row)
    if missing:
        return "missing metadata", ", ".join(missing)

    links = url_count(excerpt)
    if links >= 3 or (tokens and links / len(tokens) > 0.03):
        return "mostly links", f"{links} link markers in excerpt"

    quote_markers = lowered.count(" wrote:") + lowered.count("<small>") + lowered.count("</small>") + lowered.count("quote:")
    if quote_markers >= 4:
        return "mostly quotes", f"{quote_markers} quote markers"

    repeated_sentences = repeated_sentence_count(excerpt)
    repeated_ngram = repeated_ngram_max(excerpt)
    if repeated_sentences >= 2 or repeated_ngram >= 4:
        return "duplicated/repeated text", f"repeated_sentences={repeated_sentences}, repeated_ngram_max={repeated_ngram}"

    if issue_type in {"tiny_chunk", "very_tiny_chunk"} or token_estimate < 120:
        low_value_markers = ("thanks", "bump", "sold", "click here", "not sure if anyone cares")
        if token_estimate < 80 or any(marker in detail for marker in low_value_markers) or any(marker in lowered for marker in low_value_markers):
            return "low-value tiny chunks", f"token_estimate={token_estimate}"
        return "false positives", "short but contains substantive source text"

    if issue_type == "huge_chunk" or token_estimate >= 1200:
        if post_count >= 8 or token_estimate >= 1400:
            return "possible mixed-topic chunks", f"token_estimate={token_estimate}, post_uids={post_count}"
        return "oversized chunks", f"token_estimate={token_estimate}"

    if issue_type == "junk_phrase":
        return "false positives", f"phrase `{detail}` appears inside a substantive chunk"

    return "false positives", "no high-confidence cleanup bucket matched"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sample_rows(rows: list[dict[str, str]], row_buckets: list[tuple[str, str]], limit: int) -> dict[str, list[dict[str, str]]]:
    samples: dict[str, list[dict[str, str]]] = {bucket: [] for bucket in BUCKET_ORDER}
    for row, (bucket, reason) in zip(rows, row_buckets):
        if len(samples[bucket]) >= limit:
            continue
        item = dict(row)
        item["triage_reason"] = reason
        samples[bucket].append(item)
    return samples


def markdown_report(rows: list[dict[str, str]], sample_limit: int) -> str:
    row_buckets: list[tuple[str, str]] = []
    bucket_counts = Counter()
    by_issue: dict[str, Counter[str]] = defaultdict(Counter)
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    by_forum: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        bucket, reason = classify(row)
        row_buckets.append((bucket, reason))
        bucket_counts[bucket] += 1
        by_issue[row.get("issue_type", "")][bucket] += 1
        by_source[row.get("source_system", "(missing)")][bucket] += 1
        by_forum[row.get("forum_name", "(missing)")][bucket] += 1

    lines = [
        "# Chunk Quality Triage",
        "",
        "Scope: read-only triage of `corpus-unified/reports/unified_chunk_issues.tsv`. No corpus files, vector data, embeddings, or scraper outputs were modified.",
        "",
        "Status: YELLOW - approved for retrieval/API integration with known risks, not production-quality signoff.",
        "",
        "## Summary",
        f"- Flagged issue rows: `{len(rows):,}`",
        "- Bucket method: heuristic classification from issue type, token estimate, metadata presence, post count, and excerpt patterns.",
        "- Bucket counts are primary buckets; each flagged issue row is assigned to one bucket.",
        "",
        "## Bucket Counts",
        "| bucket | count |",
        "| --- | ---: |",
    ]
    for bucket in BUCKET_ORDER:
        lines.append(f"| {bucket} | {bucket_counts.get(bucket, 0):,} |")

    lines.extend(["", "## Buckets By Original Issue Type", "| issue type | " + " | ".join(BUCKET_ORDER) + " |", "| --- | " + " | ".join("---:" for _ in BUCKET_ORDER) + " |"])
    for issue_type in sorted(by_issue):
        counts = by_issue[issue_type]
        lines.append("| " + issue_type + " | " + " | ".join(f"{counts.get(bucket, 0):,}" for bucket in BUCKET_ORDER) + " |")

    lines.extend(["", "## Buckets By Source System", "| source system | " + " | ".join(BUCKET_ORDER) + " |", "| --- | " + " | ".join("---:" for _ in BUCKET_ORDER) + " |"])
    for source_system in sorted(by_source):
        counts = by_source[source_system]
        lines.append("| " + source_system + " | " + " | ".join(f"{counts.get(bucket, 0):,}" for bucket in BUCKET_ORDER) + " |")

    lines.extend(["", "## Top Forums By Flagged Rows", "| forum | flagged rows |", "| --- | ---: |"])
    forum_totals = Counter({forum: sum(counts.values()) for forum, counts in by_forum.items()})
    for forum, count in forum_totals.most_common(12):
        lines.append(f"| {forum} | {count:,} |")

    samples = sample_rows(rows, row_buckets, sample_limit)
    lines.extend(["", "## Sample Rows"])
    for bucket in BUCKET_ORDER:
        lines.extend(["", f"### {bucket}"])
        for row in samples[bucket]:
            excerpt = re.sub(r"\s+", " ", row.get("excerpt", "")).strip()
            if len(excerpt) > 260:
                excerpt = excerpt[:257].rstrip() + "..."
            excerpt = ascii_safe(excerpt)
            lines.extend(
                [
                    f"- `{row.get('chunk_id')}`",
                    f"  - Original issue: `{row.get('issue_type')}` / `{row.get('detail')}`",
                    f"  - Forum: `{row.get('forum_name')}`",
                    f"  - Thread: `{row.get('thread_title')}`",
                    f"  - Reason: {row.get('triage_reason')}",
                    f"  - Excerpt: {excerpt}",
                ]
            )
        if not samples[bucket]:
            lines.append("- No rows assigned.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- Most `junk_phrase` flags are false positives because words such as `thanks`, `sold`, or `bump` appear inside otherwise substantive chunks.",
            "- The main cleanup candidates are low-value tiny chunks, oversized chunks, link-heavy rows, and possible mixed-topic chunks.",
            "- Phase 3 remains blocked: fixing these in the live index would require approved corpus/chunking changes and a later embedding refresh.",
            "",
        ]
    )
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--issues",
        type=Path,
        default=DEFAULT_ISSUES,
        help="Unified chunk issue TSV. Defaults to STEEL_RAG_CORPUS_ROOT/reports/unified_chunk_issues.tsv.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown triage report path.")
    parser.add_argument("--sample-limit", type=int, default=2, help="Sample rows per bucket.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    rows = read_rows(args.issues)
    report = markdown_report(rows, args.sample_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote triage for {len(rows):,} issue rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
