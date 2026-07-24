#!/usr/bin/env python3
"""Build clean JSONL rows from parsed Steel Guitar Forum scrape JSONL."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from steel_guitar_rag.schema import clean_sgf_post_text, stringify_metadata
from rag_common import forum_input_glob, project_path


OUTPUT_FIELDS = (
    "source",
    "forum_name",
    "forum_id",
    "thread_id",
    "thread_title",
    "thread_url",
    "post_uid",
    "username",
    "post_date_raw",
    "text",
    "links",
    "quotes",
)


def expand_input_paths(input_glob: str) -> list[Path]:
    return sorted(Path(path) for path in glob.glob(input_glob) if Path(path).is_file())


def normalize_forum_id(value: Any) -> int | str | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return stringify_metadata(value)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def read_jsonl(path: Path, stats: Counter[str]) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                stats["blank_lines"] += 1
                continue
            stats["input_rows"] += 1
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                stats["invalid_json"] += 1
                print(f"Skipping {path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                continue
            if not isinstance(row, dict):
                stats["non_object_rows"] += 1
                print(f"Skipping {path}:{line_number}: row is not a JSON object", file=sys.stderr)
                continue
            yield row


def clean_row(row: Mapping[str, Any], *, forum_id: int | None) -> tuple[dict[str, Any] | None, str | None]:
    row_forum_id = normalize_forum_id(row.get("forum_id"))
    if forum_id is not None and row_forum_id != forum_id:
        return None, "wrong_forum_id"

    text = clean_sgf_post_text(row)
    if not text:
        return None, "empty_text"

    clean = {
        "source": stringify_metadata(row.get("source")) or "Steel Guitar Forum",
        "forum_name": stringify_metadata(row.get("forum_name")),
        "forum_id": row_forum_id,
        "thread_id": stringify_metadata(row.get("thread_id")),
        "thread_title": stringify_metadata(row.get("thread_title")),
        "thread_url": stringify_metadata(row.get("thread_url")),
        "post_uid": stringify_metadata(row.get("post_uid")),
        "username": stringify_metadata(row.get("username")),
        "post_date_raw": stringify_metadata(row.get("post_date_raw")),
        "text": text,
        "links": as_list(row.get("links")),
        "quotes": as_list(row.get("quotes")),
    }

    if not clean["thread_id"]:
        return None, "missing_thread_id"
    if not clean["post_uid"]:
        return None, "missing_post_uid"

    return clean, None


def iter_clean_rows(
    input_paths: Iterable[Path],
    *,
    forum_id: int | None,
    limit_threads: int | None,
    sample_rows: int | None,
    stats: Counter[str],
) -> Iterable[dict[str, Any]]:
    seen_thread_ids: set[str] = set()
    written_thread_ids: set[str] = set()
    written_rows = 0

    for path in input_paths:
        stats["input_files"] += 1
        for row in read_jsonl(path, stats):
            row_forum_id = normalize_forum_id(row.get("forum_id"))
            if forum_id is not None and row_forum_id != forum_id:
                stats["skipped_wrong_forum_id"] += 1
                continue

            raw_thread_id = stringify_metadata(row.get("thread_id"))
            if raw_thread_id and raw_thread_id not in seen_thread_ids:
                if limit_threads is not None and len(seen_thread_ids) >= limit_threads:
                    stats["limit_threads_reached"] += 1
                    return
                seen_thread_ids.add(raw_thread_id)
                stats["threads_seen"] = len(seen_thread_ids)

            clean, reason = clean_row(row, forum_id=None)
            if reason:
                stats[f"skipped_{reason}"] += 1
                continue

            assert clean is not None
            yield {field: clean[field] for field in OUTPUT_FIELDS}
            if clean["thread_id"]:
                written_thread_ids.add(clean["thread_id"])
            written_rows += 1
            stats["written_rows"] = written_rows
            stats["threads_written"] = len(written_thread_ids)

            if sample_rows is not None and written_rows >= sample_rows:
                stats["sample_rows_reached"] += 1
                return


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forum-id", type=int, default=11, help="SGF forum ID to read and retain.")
    parser.add_argument("--limit-threads", type=int, help="Stop after this many distinct threads.")
    parser.add_argument("--output", required=True, help="Clean JSONL output path.")
    parser.add_argument(
        "--sample",
        nargs="?",
        const=25,
        type=int,
        help="Sample mode: optionally cap clean output rows. Defaults to 25 rows when passed without a value.",
    )
    parser.add_argument("--input-dir", help="Directory containing sgf-output/manifest.sqlite and jsonl/forum-{id}/.")
    parser.add_argument("--input-glob", help="Override parsed SGF JSONL glob.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.limit_threads is not None and args.limit_threads < 1:
        raise SystemExit("--limit-threads must be at least 1")
    if args.sample is not None and args.sample < 1:
        raise SystemExit("--sample must be at least 1 row")

    input_glob = args.input_glob or forum_input_glob(args.forum_id, args.input_dir)
    input_paths = expand_input_paths(input_glob)
    if not input_paths:
        raise SystemExit(f"No parsed SGF JSONL files matched: {input_glob}")

    output_path = project_path(args.output)
    stats: Counter[str] = Counter()
    rows = iter_clean_rows(
        input_paths,
        forum_id=args.forum_id,
        limit_threads=args.limit_threads,
        sample_rows=args.sample,
        stats=stats,
    )
    written = write_jsonl(output_path, rows)
    stats["written_rows"] = written

    print(f"Input glob: {input_glob}")
    print(f"Output: {output_path}")
    print("Row counts:")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
