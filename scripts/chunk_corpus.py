#!/usr/bin/env python3
"""Chunk The Turnaround clean corpus for retrieval."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pocketsteel.schema import read_jsonl, source_metadata, stable_hash, write_jsonl
from pocketsteel.text import normalize_text, split_paragraphs


def split_long_unit(unit: str, chunk_chars: int) -> list[str]:
    words = unit.split()
    pieces: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        next_len = current_len + len(word) + (1 if current else 0)
        if current and next_len > chunk_chars:
            pieces.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len
    if current:
        pieces.append(" ".join(current))
    return pieces


def overlap_tail(text: str, overlap_chars: int) -> str:
    if overlap_chars <= 0 or len(text) <= overlap_chars:
        return text if overlap_chars > 0 else ""
    tail = text[-overlap_chars:]
    return tail.split(" ", 1)[-1].strip()


def chunk_text(text: str, *, chunk_chars: int = 900, overlap_chars: int = 150) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    units: list[str] = []
    for paragraph in split_paragraphs(normalized):
        if len(paragraph) <= chunk_chars:
            units.append(paragraph)
        else:
            units.extend(split_long_unit(paragraph, chunk_chars))

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for unit in units:
        separator_len = 2 if current else 0
        next_len = current_len + len(unit) + separator_len
        if current and next_len > chunk_chars:
            chunk = "\n\n".join(current).strip()
            chunks.append(chunk)
            tail = overlap_tail(chunk, overlap_chars)
            current = [tail, unit] if tail else [unit]
            current_len = sum(len(part) for part in current) + (2 if len(current) > 1 else 0)
        else:
            current.append(unit)
            current_len = next_len

    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def make_chunks(
    records: list[dict[str, Any]],
    *,
    chunk_chars: int,
    overlap_chars: int,
    min_chunk_chars: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for record in records:
        doc_chunks = chunk_text(record.get("text", ""), chunk_chars=chunk_chars, overlap_chars=overlap_chars)
        kept_doc_chunks = [
            chunk for chunk in doc_chunks if len(re.sub(r"\s+", "", chunk)) >= min_chunk_chars
        ]
        if not kept_doc_chunks and doc_chunks:
            kept_doc_chunks = [doc_chunks[0]]

        for chunk_index, chunk in enumerate(kept_doc_chunks):
            chunk_id = f"{record['doc_id']}:chunk:{chunk_index:04d}:{stable_hash(chunk, length=8)}"
            chunk_record: dict[str, Any] = {
                "chunk_id": chunk_id,
                "doc_id": record["doc_id"],
                "chunk_index": chunk_index,
                "text": chunk,
                "char_count": len(chunk),
                "token_estimate": max(1, len(chunk.split())),
            }
            chunk_record.update(source_metadata(record))
            chunks.append(chunk_record)
    return chunks


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Clean corpus JSONL path.")
    parser.add_argument("--output", required=True, help="Chunk JSONL output path.")
    parser.add_argument("--chunk-chars", type=int, default=900, help="Target chunk size in characters.")
    parser.add_argument("--overlap-chars", type=int, default=150, help="Approximate character overlap between chunks.")
    parser.add_argument("--min-chunk-chars", type=int, default=80, help="Drop tiny chunks when a doc has other chunks.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    records = [record for _, record in read_jsonl(Path(args.input))]
    chunks = make_chunks(
        records,
        chunk_chars=args.chunk_chars,
        overlap_chars=args.overlap_chars,
        min_chunk_chars=args.min_chunk_chars,
    )
    written = write_jsonl(Path(args.output), chunks)
    print(f"Wrote {written} chunks to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
