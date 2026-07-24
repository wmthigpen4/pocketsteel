#!/usr/bin/env python3
"""Audit SGF scrape outputs without modifying raw files."""

from __future__ import annotations

import argparse
import glob
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from steel_guitar_rag.schema import (  # noqa: E402
    FIELD_ALIASES,
    TEXT_ALIASES,
    clean_sgf_post_text,
    first_value,
    is_structured_path,
    iter_post_records,
    iter_structured_records,
    normalize_posted_at,
    stringify_metadata,
)


def expand_all_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        literal = Path(pattern)
        if literal.is_dir():
            paths.extend(path for path in sorted(literal.rglob("*")) if path.is_file())
        elif literal.is_file():
            paths.append(literal)
        else:
            paths.extend(Path(match) for match in sorted(glob.glob(pattern)))
    return sorted(dict.fromkeys(paths))


def file_kind(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if is_structured_path(path):
        return "structured"
    if suffix == ".txt":
        return "txt_preview"
    if suffix in {".html", ".htm"} or name.endswith((".html.gz", ".htm.gz")):
        return "raw_html"
    if suffix in {".sqlite", ".db"} or ".sqlite-" in name or ".db-" in name:
        return "sqlite"
    if suffix == ".csv":
        return "csv"
    return suffix.lstrip(".") or "unknown"


def value_for(record: dict[str, Any], aliases: tuple[str, ...]) -> str:
    return stringify_metadata(first_value(record, aliases))


def record_issue(issue_samples: dict[str, list[str]], issue: str, detail: str, sample_limit: int) -> None:
    samples = issue_samples[issue]
    if len(samples) < sample_limit:
        samples.append(detail)


def audit_structured_file(
    path: Path,
    stats: Counter[str],
    forums: Counter[str],
    page_starts: Counter[str],
    seen_post_uids: dict[str, str],
    seen_hashes: dict[str, str],
    issue_samples: dict[str, list[str]],
    *,
    min_text_chars: int,
    sample_limit: int,
) -> None:
    try:
        raw_records = iter_structured_records(path)
        for record_number, raw_record in raw_records:
            stats["raw_records"] += 1
            for post_record in iter_post_records(raw_record):
                stats["candidate_posts"] += 1

                thread_id = value_for(post_record, FIELD_ALIASES["thread_id"])
                post_uid = value_for(post_record, FIELD_ALIASES["post_id"])
                forum = value_for(post_record, FIELD_ALIASES["forum"]) or "(missing)"
                posted_at_raw = first_value(post_record, FIELD_ALIASES["posted_at"])
                posted_at = normalize_posted_at(posted_at_raw)
                text = clean_sgf_post_text(post_record)
                location = f"{path}:{record_number}"

                forums[forum] += 1
                page_starts[str(post_record.get("thread_page_start", ""))] += 1

                if not thread_id:
                    stats["missing_thread_id"] += 1
                    record_issue(issue_samples, "missing_thread_id", location, sample_limit)
                if not post_uid:
                    stats["missing_post_uid"] += 1
                    record_issue(issue_samples, "missing_post_uid", location, sample_limit)
                if not value_for(post_record, FIELD_ALIASES["title"]):
                    stats["missing_thread_title"] += 1
                    record_issue(issue_samples, "missing_thread_title", location, sample_limit)
                if not value_for(post_record, FIELD_ALIASES["author"]):
                    stats["missing_username"] += 1
                    record_issue(issue_samples, "missing_username", location, sample_limit)
                if not first_value(post_record, TEXT_ALIASES):
                    stats["missing_text_field"] += 1
                    record_issue(issue_samples, "missing_text_field", location, sample_limit)
                if not posted_at:
                    stats["missing_or_unparsed_date"] += 1
                    record_issue(issue_samples, "missing_or_unparsed_date", location, sample_limit)
                if len("".join(text.split())) < min_text_chars:
                    stats["too_short_after_cleaning"] += 1
                    record_issue(issue_samples, "too_short_after_cleaning", f"{location} {post_uid}".strip(), sample_limit)
                else:
                    stats["cleanable_posts"] += 1

                if post_uid:
                    previous = seen_post_uids.get(post_uid)
                    if previous and previous != str(path):
                        stats["duplicate_post_uid"] += 1
                        record_issue(issue_samples, "duplicate_post_uid", f"{post_uid}: {previous} and {path}", sample_limit)
                    else:
                        seen_post_uids[post_uid] = str(path)

                content_hash = stringify_metadata(post_record.get("content_hash"))
                if content_hash:
                    previous = seen_hashes.get(content_hash)
                    if previous and previous != str(path):
                        stats["duplicate_content_hash"] += 1
                        record_issue(issue_samples, "duplicate_content_hash", f"{content_hash}: {previous} and {path}", sample_limit)
                    else:
                        seen_hashes[content_hash] = str(path)

    except (OSError, ValueError) as exc:
        stats["invalid_structured_files"] += 1
        record_issue(issue_samples, "invalid_structured_files", f"{path}: {exc}", sample_limit)


def print_counter(title: str, counter: Counter[str], *, limit: int = 12) -> None:
    if not counter:
        return
    print(f"\n{title}:")
    for key, value in counter.most_common(limit):
        print(f"  {key}: {value}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", nargs="+", required=True, help="SGF scrape files, folders, or globs.")
    parser.add_argument("--min-text-chars", type=int, default=40)
    parser.add_argument("--sample-limit", type=int, default=5)
    parser.add_argument("--max-structured-files", type=int, default=None, help="Optional cap for quick audits.")
    parser.add_argument(
        "--include-non-thread-json",
        action="store_true",
        help="Also audit structured files whose filename does not start with thread-.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    paths = expand_all_inputs(args.input)
    if not paths:
        raise SystemExit("No files matched.")

    stats: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    suffixes: Counter[str] = Counter()
    forums: Counter[str] = Counter()
    page_starts: Counter[str] = Counter()
    issue_samples: dict[str, list[str]] = defaultdict(list)
    seen_post_uids: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}

    structured_seen = 0
    for path in paths:
        kind = file_kind(path)
        kinds[kind] += 1
        suffixes[path.suffix.lower() or "(none)"] += 1
        stats["files_total"] += 1
        if kind != "structured":
            continue
        if not args.include_non_thread_json and not path.name.startswith("thread-"):
            stats["non_thread_structured_skipped"] += 1
            continue
        if args.max_structured_files is not None and structured_seen >= args.max_structured_files:
            stats["structured_files_skipped_by_limit"] += 1
            continue
        structured_seen += 1
        stats["structured_files"] += 1
        audit_structured_file(
            path,
            stats,
            forums,
            page_starts,
            seen_post_uids,
            seen_hashes,
            issue_samples,
            min_text_chars=args.min_text_chars,
            sample_limit=args.sample_limit,
        )

    print("SGF Scrape Audit")
    print("=" * 15)
    for key in (
        "files_total",
        "structured_files",
        "non_thread_structured_skipped",
        "structured_files_skipped_by_limit",
        "raw_records",
        "candidate_posts",
        "cleanable_posts",
        "too_short_after_cleaning",
        "invalid_structured_files",
        "missing_thread_id",
        "missing_post_uid",
        "missing_thread_title",
        "missing_username",
        "missing_text_field",
        "missing_or_unparsed_date",
        "duplicate_post_uid",
        "duplicate_content_hash",
    ):
        if stats[key]:
            print(f"{key}: {stats[key]}")

    print_counter("File kinds", kinds)
    print_counter("Suffixes", suffixes)
    print_counter("Forums", forums)
    print_counter("Thread page starts", page_starts)

    if issue_samples:
        print("\nIssue samples:")
        for issue, samples in sorted(issue_samples.items()):
            print(f"  {issue}:")
            for sample in samples:
                print(f"    {sample}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
