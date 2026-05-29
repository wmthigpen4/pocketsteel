#!/usr/bin/env python3
"""Chunk normalized private source-inbox documents without embedding them."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any, Iterable


DEFAULT_INPUT = Path("corpus-private/normalized/source-inbox-documents.jsonl")
DEFAULT_OUTPUT = Path("corpus-private/chunks/source-inbox-chunks.jsonl")
DEFAULT_REPORT = Path("corpus-private/reports/source-inbox-chunk-report.md")


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def stable_hash(*parts: object, length: int = 12) -> str:
    payload = "\u241f".join("" if part is None else str(part) for part in parts)
    return sha1(payload.encode("utf-8")).hexdigest()[:length]


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            yield value


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def embedding_allowed(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == "true")


def looks_tab_heavy(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    tab_like = 0
    for line in lines:
        if line.count("|") >= 2 or line.count("-") >= 4:
            tab_like += 1
        elif re.search(r"\b\d+(?:[ABCF]|~|/|\\|-|\^)\d*", line):
            tab_like += 1
    return tab_like / max(1, len(lines)) >= 0.25


def split_long_plain_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    pieces: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        next_len = current_len + len(word) + (1 if current else 0)
        if current and next_len > max_chars:
            pieces.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len
    if current:
        pieces.append(" ".join(current))
    return pieces


def split_long_preserving_lines(text: str, max_chars: int) -> list[str]:
    lines = text.splitlines()
    pieces: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        next_len = current_len + len(line) + (1 if current else 0)
        if current and next_len > max_chars:
            pieces.append("\n".join(current).rstrip())
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len = next_len
    if current:
        pieces.append("\n".join(current).rstrip())
    return [piece for piece in pieces if piece.strip()]


def split_units(text: str, *, tab_heavy: bool, max_chars: int) -> list[str]:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    blocks = re.split(r"\n{2,}", normalized)
    units: list[str] = []
    for block in blocks:
        block = block.rstrip()
        if not block.strip():
            continue
        if len(block) <= max_chars:
            units.append(block)
        elif tab_heavy:
            units.extend(split_long_preserving_lines(block, max_chars))
        else:
            units.extend(split_long_plain_text(block, max_chars))
    return units


def chunk_text(
    text: str,
    *,
    target_chars: int = 2400,
    max_chars: int = 3600,
    min_chars: int = 120,
) -> list[str]:
    tab_heavy = looks_tab_heavy(text)
    units = split_units(text, tab_heavy=tab_heavy, max_chars=max_chars)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    joiner = "\n\n"

    for unit in units:
        separator_len = len(joiner) if current else 0
        next_len = current_len + separator_len + len(unit)
        if current and next_len > target_chars:
            chunks.append(joiner.join(current).strip())
            current = [unit]
            current_len = len(unit)
        else:
            current.append(unit)
            current_len = next_len
    if current:
        chunks.append(joiner.join(current).strip())

    filtered = [chunk for chunk in chunks if len(re.sub(r"\s+", "", chunk)) >= min_chars]
    if not filtered and chunks:
        return [chunks[0]]
    return filtered


def repeated_line_ratio(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return 0.0
    counts = Counter(lines)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / len(lines)


def noise_score(text: str) -> int:
    if not text.strip():
        return 100
    score = 0
    if len(text.strip()) < 160:
        score += 25
    score += int(repeated_line_ratio(text) * 50)
    if re.search(r"\bWEBVTT\b|\d{1,2}:\d{2}[,.]\d{3}\s+-->", text, re.IGNORECASE):
        score += 25
    return max(0, min(100, score))


def quality_score(text: str) -> int:
    score = 100 - noise_score(text)
    if len(text.strip()) < 240:
        score -= 10
    return max(0, min(100, score))


def detect_chunk_role(row: dict[str, Any], text: str) -> str:
    source_system = str(row.get("source_system") or "")
    source_type = str((row.get("metadata") or {}).get("source_type") or "")
    if looks_tab_heavy(text):
        return "tab_or_exercise"
    if source_system == "personal_rules_note" or "rules" in source_type:
        return "rules_note"
    if "transcript" in source_system or "lesson" in source_system or "transcript" in source_type:
        return "lesson_or_transcript"
    return "private_source_document"


def make_chunk_id(row: dict[str, Any], chunk_index: int, text: str) -> str:
    source_id = row.get("source_id") or "source"
    document_index = row.get("document_index", 0)
    digest = stable_hash(source_id, document_index, chunk_index, text)
    return f"private:{source_id}:doc-{document_index}:chunk-{chunk_index:04d}:{digest}"


def make_chunks(
    rows: list[dict[str, Any]],
    *,
    target_chars: int = 2400,
    max_chars: int = 3600,
    min_chars: int = 120,
    created_at: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    created_at = created_at or now_iso()
    chunks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for row in rows:
        source_path = str(row.get("source_path") or "")
        if not embedding_allowed(row.get("embedding_allowed")):
            skipped.append({"source_path": source_path, "reason": "embedding_not_allowed"})
            continue
        text = str(row.get("text") or "")
        doc_chunks = chunk_text(text, target_chars=target_chars, max_chars=max_chars, min_chars=min_chars)
        if not doc_chunks:
            skipped.append({"source_path": source_path, "reason": "empty_text"})
            continue
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        for chunk_index, chunk in enumerate(doc_chunks):
            chunks.append(
                {
                    "chunk_id": make_chunk_id(row, chunk_index, chunk),
                    "source_id": row.get("source_id"),
                    "source_system": row.get("source_system"),
                    "visibility": row.get("visibility"),
                    "source_path": source_path,
                    "title": row.get("title"),
                    "file_type": row.get("file_type"),
                    "document_index": row.get("document_index"),
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "source_url": metadata.get("source_url") or row.get("source_url"),
                    "provenance_status": row.get("provenance_status"),
                    "redistribution_allowed": row.get("redistribution_allowed"),
                    "embedding_allowed": row.get("embedding_allowed"),
                    "answer_quote_allowed": row.get("answer_quote_allowed"),
                    "chunk_role": detect_chunk_role(row, chunk),
                    "quality_score": quality_score(chunk),
                    "noise_score": noise_score(chunk),
                    "char_count": len(chunk),
                    "token_estimate": max(1, len(chunk.split())),
                    "metadata": metadata,
                    "created_at": created_at,
                }
            )

    return chunks, skipped


def length_bucket(char_count: int) -> str:
    if char_count < 250:
        return "tiny_lt_250"
    if char_count < 750:
        return "short_250_749"
    if char_count < 1800:
        return "medium_750_1799"
    if char_count < 3600:
        return "target_1800_3599"
    return "large_3600_plus"


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items())]


def write_report(path: Path, input_count: int, chunks: list[dict[str, Any]], skipped: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    source_counts = Counter(str(chunk.get("source_system") or "") for chunk in chunks)
    visibility_counts = Counter(str(chunk.get("visibility") or "") for chunk in chunks)
    length_counts = Counter(length_bucket(int(chunk.get("char_count") or 0)) for chunk in chunks)
    tiny_chunks = [chunk for chunk in chunks if int(chunk.get("char_count") or 0) < 250]
    empty_chunks = [chunk for chunk in chunks if not str(chunk.get("text") or "").strip()]

    lines = [
        "# Source Inbox Chunk Report",
        "",
        "This report covers private source-inbox chunking only. No embeddings or Chroma writes were performed.",
        "",
        f"- Input documents: `{input_count}`",
        f"- Output chunks: `{len(chunks)}`",
        f"- Skipped documents: `{len(skipped)}`",
        "",
        "## Source System Counts",
        "",
        *render_counter(source_counts),
        "",
        "## Visibility Counts",
        "",
        *render_counter(visibility_counts),
        "",
        "## Chunk Length Distribution",
        "",
        *render_counter(length_counts),
        "",
        "## Warnings",
        "",
    ]
    if not tiny_chunks and not empty_chunks:
        lines.append("- None")
    for chunk in tiny_chunks[:25]:
        lines.append(f"- Tiny chunk `{chunk['chunk_id']}`: {chunk['char_count']} characters")
    for chunk in empty_chunks[:25]:
        lines.append(f"- Empty chunk `{chunk['chunk_id']}`")
    if skipped:
        lines.extend(["", "## Skipped Documents", "", "| Source path | Reason |", "| --- | --- |"])
        for item in skipped:
            lines.append(f"| {item.get('source_path', '')} | {item.get('reason', '')} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--target-chars", type=int, default=2400)
    parser.add_argument("--max-chars", type=int, default=3600)
    parser.add_argument("--min-chars", type=int, default=120)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    rows = list(read_jsonl(args.input))
    chunks, skipped = make_chunks(
        rows,
        target_chars=args.target_chars,
        max_chars=args.max_chars,
        min_chars=args.min_chars,
    )
    written = write_jsonl(args.output, chunks)
    write_report(args.report, len(rows), chunks, skipped)
    print(f"Read {len(rows)} normalized document(s).")
    print(f"Wrote {written} private chunk(s) to {args.output}.")
    print(f"Skipped {len(skipped)} document(s).")
    print(f"Wrote report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
