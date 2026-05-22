#!/usr/bin/env python3
"""Build the clean Electronics corpus for Pocket Steel RAG v0."""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from rag_common import (
    DEFAULT_FORUM_ID,
    DEFAULT_FORUM_NAME,
    normalize_space,
    project_path,
    word_count,
)


DEFAULT_INPUT_GLOB = "sgf-output/jsonl/forum-11/*.jsonl"
DEFAULT_OUTPUT = "rag-data/electronics/clean_corpus.jsonl"
DEFAULT_REPORT = "rag-data/electronics/clean_corpus_report.json"

DATE_LINE_RE = re.compile(
    r"^\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s+\d{1,2}:\d{2}\s+(?:am|pm)\b",
    re.IGNORECASE,
)
EDITED_RE = re.compile(r"\[(?:This message was edited by|Edited by).+?\]", re.IGNORECASE)
LAST_EDITED_RE = re.compile(r"^Last edited by .+? in total\.$", re.IGNORECASE)
FONT_EDIT_RE = re.compile(r"<font\b[^>]*>.*?</font>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")

PROFILE_PREFIXES = (
    "Posts:",
    "Joined:",
    "Location:",
    "State/Province:",
    "Country:",
)
OBVIOUS_BOILERPLATE_LINES = {
    "Top",
    "Back to top",
    "You do not have the required permissions to view the files attached to this post.",
}


def strip_header(lines: list[str], row: dict[str, Any]) -> list[str]:
    """Drop the phpBB author/profile wrapper while keeping the actual post."""
    marker_indexes = [index for index, line in enumerate(lines[:30]) if line == "»"]
    for marker in marker_indexes:
        for date_index in range(marker + 1, min(marker + 4, len(lines))):
            if DATE_LINE_RE.match(lines[date_index]):
                return lines[date_index + 1 :]

    for index, line in enumerate(lines[:35]):
        if DATE_LINE_RE.match(line):
            return lines[index + 1 :]

    username = (row.get("username") or "").strip()
    thread_title = (row.get("thread_title") or "").strip()
    trimmed: list[str] = []
    skipping_profile_value = False
    for index, line in enumerate(lines):
        if index < 18 and (
            line in {"by", username, thread_title, "»"}
            or line.startswith(PROFILE_PREFIXES)
            or skipping_profile_value
        ):
            skipping_profile_value = line.startswith(PROFILE_PREFIXES)
            continue
        skipping_profile_value = False
        trimmed.append(line)
    return trimmed


def clean_post_text(row: dict[str, Any]) -> str:
    raw_text = row.get("post_text_clean") or row.get("text") or ""
    raw_text = FONT_EDIT_RE.sub(" ", raw_text)
    raw_text = EDITED_RE.sub(" ", raw_text)
    raw_text = HTML_TAG_RE.sub(" ", raw_text)
    lines = [line.strip() for line in normalize_space(raw_text).splitlines()]
    lines = strip_header(lines, row)

    cleaned_lines: list[str] = []
    username = (row.get("username") or "").strip()
    for line in lines:
        line = line.strip()
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        if line in OBVIOUS_BOILERPLATE_LINES:
            continue
        if LAST_EDITED_RE.match(line):
            continue
        if line == username and len(cleaned_lines) < 2:
            continue
        cleaned_lines.append(line)

    return normalize_space("\n".join(cleaned_lines))


def skip_reason(text: str) -> str | None:
    if not text:
        return "empty_after_cleaning"
    words = word_count(text)
    if len(text) < 25 or words < 5:
        return "near_empty"
    return None


def clean_row(row: dict[str, Any], source_file: Path) -> tuple[dict[str, Any] | None, str | None]:
    if row.get("forum_id") != DEFAULT_FORUM_ID:
        return None, "wrong_forum_id"
    text = clean_post_text(row)
    reason = skip_reason(text)
    if reason:
        return None, reason

    clean = {
        "source": row.get("source") or "Steel Guitar Forum",
        "source_system": row.get("source_system") or "sgf",
        "forum_id": row.get("forum_id"),
        "forum_name": row.get("forum_name") or DEFAULT_FORUM_NAME,
        "thread_id": str(row.get("thread_id") or ""),
        "thread_title": row.get("thread_title") or "",
        "thread_url": row.get("thread_url") or "",
        "post_uid": row.get("post_uid") or "",
        "username": row.get("username") or "",
        "post_date_raw": row.get("post_date_raw") or "",
        "text": text,
        "links": row.get("links") or [],
    }
    if not clean["thread_id"] or not clean["post_uid"]:
        return None, "missing_required_metadata"
    clean["_source_file"] = str(source_file)
    return clean, None


def iter_clean_rows(input_glob: str, report: dict[str, Any]):
    files = sorted(Path(path) for path in glob.glob(input_glob))
    report["input_glob"] = input_glob
    report["input_files"] = len(files)
    skipped = Counter()
    total_rows = 0
    written_rows = 0

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    skipped["blank_jsonl_line"] += 1
                    continue
                total_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    skipped["invalid_json"] += 1
                    continue
                clean, reason = clean_row(row, path)
                if reason:
                    skipped[reason] += 1
                    continue
                written_rows += 1
                yield clean

    report["total_rows"] = total_rows
    report["written_rows"] = written_rows
    report["skipped_rows"] = sum(skipped.values())
    report["skipped_reasons"] = dict(sorted(skipped.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-glob", default=DEFAULT_INPUT_GLOB)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    args = parser.parse_args()

    output = project_path(args.output)
    report_path = project_path(args.report)
    input_glob = str(project_path(args.input_glob))
    output.parent.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "forum_id": DEFAULT_FORUM_ID,
        "forum_name": DEFAULT_FORUM_NAME,
        "output": str(output),
    }
    with output.open("w", encoding="utf-8") as handle:
        for row in iter_clean_rows(input_glob, report):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {report['written_rows']} clean posts to {output}")
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()

