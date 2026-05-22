#!/usr/bin/env python3
"""Normalize scraped SGF JSONL into a clean source corpus."""

from __future__ import annotations

import argparse
import glob
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pocketsteel.schema import is_structured_path, iter_post_records, iter_structured_records, normalize_record, write_jsonl


def expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        literal = Path(pattern)
        if literal.is_dir():
            paths.extend(path for path in sorted(literal.rglob("*")) if path.is_file() and is_structured_path(path))
        elif literal.is_file():
            if is_structured_path(literal):
                paths.append(literal)
        else:
            paths.extend(Path(match) for match in sorted(glob.glob(pattern)) if is_structured_path(Path(match)))
    return sorted(dict.fromkeys(paths))


def iter_clean_records(
    input_paths: list[Path],
    *,
    source: str,
    min_text_chars: int,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    stats: Counter[str] = Counter()
    output: list[dict[str, Any]] = []
    seen_doc_ids: set[str] = set()

    for path in input_paths:
        stats["files"] += 1
        try:
            raw_records = iter_structured_records(path)
            for record_number, value in raw_records:
                if limit is not None and len(output) >= limit:
                    return output, stats
                stats["raw_records"] += 1

                for post_record in iter_post_records(value):
                    stats["candidate_records"] += 1
                    clean = normalize_record(post_record, source=source, min_text_chars=min_text_chars)
                    if clean is None:
                        stats["too_short"] += 1
                        continue
                    if clean["doc_id"] in seen_doc_ids:
                        stats["duplicate_doc_ids"] += 1
                        clean["doc_id"] = f"{clean['doc_id']}:dup:{record_number}:{stats['duplicate_doc_ids']}"
                    seen_doc_ids.add(clean["doc_id"])
                    output.append(clean)
                    stats["clean_records"] += 1
        except (OSError, ValueError) as exc:
            stats["invalid_files"] += 1
            print(f"Skipping {path}: {exc}")

    return output, stats


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", nargs="+", required=True, help="Raw SGF JSON/JSONL files, directories, or globs.")
    parser.add_argument("--output", required=True, help="Clean corpus JSONL output path.")
    parser.add_argument("--source", default="sgf", help="Source label to store on each document.")
    parser.add_argument("--min-text-chars", type=int, default=40, help="Drop records with less text than this.")
    parser.add_argument("--limit", type=int, default=None, help="Optional max clean records for smoke tests.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    input_paths = expand_inputs(args.input)
    if not input_paths:
        raise SystemExit("No input JSON/JSONL files matched. Put raw files in data/raw/sgf/ or pass a quoted glob.")

    records, stats = iter_clean_records(
        input_paths,
        source=args.source,
        min_text_chars=args.min_text_chars,
        limit=args.limit,
    )
    written = write_jsonl(Path(args.output), records)
    print(f"Wrote {written} clean records to {args.output}")
    print("Stats:")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
