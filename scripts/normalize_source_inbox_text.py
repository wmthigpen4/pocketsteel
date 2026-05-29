#!/usr/bin/env python3
"""Normalize reviewed TXT/MD/VTT/SRT source-inbox files into private JSONL.

The script does not ingest PDFs, embed content, touch Chroma, or log private
source text. It requires provenance for every normalized source file.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".vtt", ".srt"}
SKIPPED_EXTENSIONS = {".pdf", ".docx"}
DEFAULT_SOURCE = Path("source-inbox")
DEFAULT_PROVENANCE = Path("source-inbox/provenance.json")
DEFAULT_OUTPUT = Path("corpus-private/normalized/source-inbox-documents.jsonl")
DEFAULT_SKIPPED = Path("corpus-private/reports/source-inbox-normalize-skipped.md")

VALID_VISIBILITY = {"private", "public", "review"}
VALID_EMBEDDING = {True, False, "review"}
VALID_REDISTRIBUTION = {True, False, "unknown"}
VALID_QUOTE = {True, False, "limited"}


@dataclass
class SkipRecord:
    path: str
    reason: str
    detail: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize reviewed source-inbox TXT/MD/VTT/SRT files into private JSONL."
    )
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Source inbox root.")
    parser.add_argument(
        "--provenance",
        default=str(DEFAULT_PROVENANCE),
        help="Reviewed provenance JSON path. Default: source-inbox/provenance.json",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Normalized JSONL output path under corpus-private/.",
    )
    parser.add_argument(
        "--skipped-report",
        default=str(DEFAULT_SKIPPED),
        help="Markdown skipped report output path under corpus-private/.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def normalize_path(path: str | Path) -> str:
    return Path(path).as_posix()


def load_provenance(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("sources", data if isinstance(data, list) else [])
    if not isinstance(records, list):
        raise ValueError("Provenance JSON must be a list or an object with a 'sources' list.")

    by_path: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        source_path = record.get("path")
        if source_path:
            by_path[normalize_path(source_path)] = record
    return by_path


def validate_provenance(record: dict[str, Any]) -> list[str]:
    required_fields = [
        "source_id",
        "path",
        "title",
        "author_or_creator",
        "source_type",
        "source_system",
        "visibility",
        "redistribution_allowed",
        "embedding_allowed",
        "answer_quote_allowed",
        "notes",
        "reviewed_at",
        "reviewed_by",
    ]
    missing = [field for field in required_fields if field not in record]
    errors = [f"missing:{field}" for field in missing]

    if record.get("visibility") not in VALID_VISIBILITY:
        errors.append("invalid:visibility")
    if record.get("embedding_allowed") not in VALID_EMBEDDING:
        errors.append("invalid:embedding_allowed")
    if record.get("redistribution_allowed") not in VALID_REDISTRIBUTION:
        errors.append("invalid:redistribution_allowed")
    if record.get("answer_quote_allowed") not in VALID_QUOTE:
        errors.append("invalid:answer_quote_allowed")
    if not record.get("reviewed_at") or not record.get("reviewed_by"):
        errors.append("missing:review")
    return errors


def should_skip_candidate(path: Path, source_root: Path) -> str | None:
    if path.name.startswith("."):
        return "hidden_or_placeholder"
    if path.name in {"README.md", "inventory.json", "provenance-template.json", "provenance.json"}:
        return "inbox_metadata"
    if not path.is_file():
        return "not_file"
    if not path.is_relative_to(source_root):
        return "outside_source_root"
    return None


def iter_source_files(source_root: Path) -> Iterable[Path]:
    yield from sorted(path for path in source_root.rglob("*") if path.is_file())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


TIMESTAMP_RE = re.compile(
    r"^\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[,.]\d{3}\s+-->\s+(?:\d{1,2}:)?\d{1,2}:\d{2}[,.]\d{3}.*$"
)
CUE_NUMBER_RE = re.compile(r"^\s*\d+\s*$")
WEBVTT_RE = re.compile(r"^\s*WEBVTT(?:\s+.*)?$", re.IGNORECASE)
VTT_NOTE_RE = re.compile(r"^\s*(?:NOTE|STYLE|REGION)(?:\s+.*)?$", re.IGNORECASE)
CAPTION_TAG_RE = re.compile(r"</?c(?:\.[^>]*)?>|</?v(?:\s+[^>]*)?>|<\d{1,2}:\d{2}:\d{2}\.\d{3}>")


def normalize_caption_text(text: str) -> str:
    lines: list[str] = []
    previous = ""
    skip_note_block = False

    for raw_line in text.replace("\ufeff", "").splitlines():
        line = raw_line.strip()
        if not line:
            skip_note_block = False
            continue
        if skip_note_block:
            continue
        if WEBVTT_RE.match(line) or TIMESTAMP_RE.match(line) or CUE_NUMBER_RE.match(line):
            continue
        if VTT_NOTE_RE.match(line):
            skip_note_block = True
            continue

        line = CAPTION_TAG_RE.sub("", line)
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line == previous:
            continue
        lines.append(line)
        previous = line

    return "\n".join(collapse_repeated_caption_fragments(lines))


def collapse_repeated_caption_fragments(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    for line in lines:
        if collapsed and (line == collapsed[-1] or line in collapsed[-1]):
            continue
        if collapsed and collapsed[-1] in line:
            collapsed[-1] = line
            continue
        collapsed.append(line)
    return collapsed


def looks_tab_heavy(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    tab_like = 0
    for line in lines:
        if re.search(r"\d+\s*(?:[ABCF][+]?|[~\-/\\^])", line):
            tab_like += 1
        elif line.count("-") >= 4 or line.count("|") >= 2:
            tab_like += 1
    return tab_like / max(len(lines), 1) >= 0.25


def normalize_text_or_markdown(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    if looks_tab_heavy(text):
        lines = [line.rstrip() for line in text.split("\n")]
        normalized = "\n".join(lines)
        return re.sub(r"\n{4,}", "\n\n\n", normalized).strip()

    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if line.startswith("#"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append(re.sub(r"\s+", " ", line))
            continue
        current.append(re.sub(r"\s+", " ", line))
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs).strip()


def normalize_file(path: Path) -> str:
    suffix = path.suffix.lower()
    text = read_text(path)
    if suffix in {".vtt", ".srt"}:
        return normalize_caption_text(text)
    return normalize_text_or_markdown(text)


def provenance_status(record: dict[str, Any]) -> str:
    if record.get("embedding_allowed") is True and record.get("reviewed_at") and record.get("reviewed_by"):
        return "reviewed"
    if record.get("embedding_allowed") == "review":
        return "review_required"
    return "not_allowed"


def build_normalized_row(
    path: Path,
    source_root: Path,
    record: dict[str, Any],
    document_index: int,
    created_at: str,
) -> dict[str, Any]:
    text = normalize_file(path)
    return {
        "source_id": record["source_id"],
        "source_system": record["source_system"],
        "visibility": record["visibility"],
        "source_path": normalize_path(path),
        "title": record["title"],
        "file_type": path.suffix.lower().lstrip("."),
        "document_index": document_index,
        "text": text,
        "metadata": {
            "author_or_creator": record["author_or_creator"],
            "source_type": record["source_type"],
            "source_url": record.get("source_url"),
            "notes": record.get("notes", ""),
            "relative_path": normalize_path(path.relative_to(source_root)),
        },
        "provenance_status": provenance_status(record),
        "embedding_allowed": record["embedding_allowed"],
        "redistribution_allowed": record["redistribution_allowed"],
        "answer_quote_allowed": record["answer_quote_allowed"],
        "created_at": created_at,
    }


def normalize_source_inbox(
    source_root: Path,
    provenance_path: Path,
    output_path: Path,
    skipped_report_path: Path,
) -> tuple[list[dict[str, Any]], list[SkipRecord]]:
    provenance = load_provenance(provenance_path)
    rows: list[dict[str, Any]] = []
    skipped: list[SkipRecord] = []
    created_at = now_iso()

    for path in iter_source_files(source_root):
        skip_reason = should_skip_candidate(path, source_root)
        if skip_reason:
            if skip_reason not in {"hidden_or_placeholder", "inbox_metadata"}:
                skipped.append(SkipRecord(normalize_path(path), skip_reason))
            continue

        suffix = path.suffix.lower()
        if suffix in SKIPPED_EXTENSIONS:
            skipped.append(SkipRecord(normalize_path(path), "unsupported_for_text_normalizer", "metadata only for now"))
            continue
        if suffix not in SUPPORTED_TEXT_EXTENSIONS:
            skipped.append(SkipRecord(normalize_path(path), "unsupported_file_type", suffix or "no extension"))
            continue

        source_path = normalize_path(path)
        record = provenance.get(source_path)
        if not record:
            skipped.append(SkipRecord(source_path, "missing_provenance"))
            continue

        errors = validate_provenance(record)
        if errors:
            skipped.append(SkipRecord(source_path, "invalid_provenance", ", ".join(errors)))
            continue

        if record["embedding_allowed"] is False:
            skipped.append(SkipRecord(source_path, "embedding_not_allowed"))
            continue

        if record.get("source_system") == "curated_source_candidate":
            skipped.append(SkipRecord(source_path, "belongs_in_curated_source_registry"))
            continue

        row = build_normalized_row(path, source_root, record, len(rows), created_at)
        if not row["text"]:
            skipped.append(SkipRecord(source_path, "empty_after_normalization"))
            continue
        rows.append(row)

    write_jsonl(output_path, rows)
    write_skipped_report(skipped_report_path, skipped, source_root, provenance_path, output_path)
    return rows, skipped


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_skipped_report(
    path: Path,
    skipped: list[SkipRecord],
    source_root: Path,
    provenance_path: Path,
    output_path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Source Inbox Normalize Skipped Report",
        "",
        "This report contains file paths and skip reasons only. It does not include private source content.",
        "",
        f"- Source root: `{normalize_path(source_root)}`",
        f"- Provenance file: `{normalize_path(provenance_path)}`",
        f"- Normalized output: `{normalize_path(output_path)}`",
        f"- Skipped files: `{len(skipped)}`",
        "",
        "| Path | Reason | Detail |",
        "| --- | --- | --- |",
    ]
    for item in skipped:
        lines.append(f"| {escape_md(item.path)} | {escape_md(item.reason)} | {escape_md(item.detail)} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> int:
    args = parse_args()
    rows, skipped = normalize_source_inbox(
        source_root=Path(args.source),
        provenance_path=Path(args.provenance),
        output_path=Path(args.output),
        skipped_report_path=Path(args.skipped_report),
    )
    print(f"Normalized {len(rows)} document(s).")
    print(f"Skipped {len(skipped)} file(s).")
    print(f"Wrote JSONL: {args.output}")
    print(f"Wrote skipped report: {args.skipped_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
