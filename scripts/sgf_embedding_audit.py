#!/usr/bin/env python3
"""Read-only audit for a completed Steel Guitar Forum Chroma embedding run."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CORPUS_ROOT = Path(os.environ.get("STEEL_RAG_CORPUS_ROOT", "corpus-unified"))
DEFAULT_CHROMA = Path(os.environ.get("STEEL_RAG_CHROMA_PATH", DEFAULT_CORPUS_ROOT / "vector-stores" / "chroma"))
DEFAULT_CHUNKS = Path(os.environ.get("STEEL_RAG_CHUNKS_PATH", DEFAULT_CORPUS_ROOT / "chunks.jsonl"))

CHROMA_REQUIRED_KEYS = ("forum_name", "thread_title", "thread_url", "post_uid", "chunk_id", "chroma:document")
CHUNK_REQUIRED_KEYS = ("forum_name", "thread_title", "thread_url", "post_uid", "post_uids", "chunk_id", "text", "chunk_text")


def nonempty(value: Any) -> bool:
    return value not in (None, "", [], {})


def sqlite_path(chroma_path: Path) -> Path:
    if chroma_path.is_file():
        return chroma_path
    return chroma_path / "chroma.sqlite3"


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    value = conn.execute(sql, params).fetchone()[0]
    return int(value or 0)


def audit_chroma(chroma_path: Path) -> dict[str, Any]:
    db_path = sqlite_path(chroma_path)
    if not db_path.exists():
        raise SystemExit(f"Chroma SQLite database not found: {db_path}")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        collections = [
            {"name": row[0], "id": row[1], "dimension": row[2]}
            for row in conn.execute("select name, id, dimension from collections order by name")
        ]
        metadata_counts = {
            row[0]: {"rows": int(row[1]), "nonempty": int(row[2] or 0)}
            for row in conn.execute(
                """
                select
                    key,
                    count(*) as rows,
                    sum(
                        case
                            when coalesce(
                                string_value,
                                cast(int_value as text),
                                cast(float_value as text),
                                cast(bool_value as text),
                                ''
                            ) <> ''
                            then 1
                            else 0
                        end
                    ) as nonempty
                from embedding_metadata
                group by key
                order by key
                """
            )
        }
        vector_count = scalar(conn, "select count(*) from embeddings")
        document_count = scalar(conn, "select count(*) from embedding_fulltext_search_content")
        sample_documents = [
            {"embedding_id": row[0], "excerpt": row[1]}
            for row in conn.execute(
                """
                select e.embedding_id, substr(f.c0, 1, 160)
                from embeddings e
                join embedding_fulltext_search_content f on f.id = e.id
                order by e.id
                limit 3
                """
            )
        ]
    finally:
        conn.close()

    required = {}
    for key in CHROMA_REQUIRED_KEYS:
        counts = metadata_counts.get(key, {"rows": 0, "nonempty": 0})
        required[key] = {
            "present": counts["rows"],
            "nonempty": counts["nonempty"],
            "missing": vector_count - counts["rows"],
        }

    return {
        "path": str(chroma_path),
        "sqlite": str(db_path),
        "collections": collections,
        "vector_count": vector_count,
        "document_count": document_count,
        "metadata_counts": metadata_counts,
        "required": required,
        "sample_documents": sample_documents,
    }


def audit_chunks(chunks_path: Path) -> dict[str, Any]:
    if not chunks_path.exists():
        raise SystemExit(f"Chunk JSONL not found: {chunks_path}")

    present = Counter()
    empty = Counter()
    source_systems = Counter()
    forums = Counter()
    rows = 0
    json_errors: list[str] = []
    samples: list[dict[str, Any]] = []

    with chunks_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                json_errors.append(f"{line_number}: {exc.msg}")
                continue
            rows += 1
            if not isinstance(record, dict):
                json_errors.append(f"{line_number}: row is not an object")
                continue
            source_systems[str(record.get("source_system") or "(missing)")] += 1
            forums[str(record.get("forum_name") or "(missing)")] += 1
            for key in CHUNK_REQUIRED_KEYS:
                if key in record:
                    present[key] += 1
                if not nonempty(record.get(key)):
                    empty[key] += 1
            if len(samples) < 3:
                samples.append(
                    {
                        "chunk_id": record.get("chunk_id"),
                        "forum_name": record.get("forum_name"),
                        "thread_title": record.get("thread_title"),
                        "thread_url": record.get("thread_url"),
                        "text_field": "chunk_text" if nonempty(record.get("chunk_text")) else "text" if nonempty(record.get("text")) else None,
                    }
                )

    return {
        "path": str(chunks_path),
        "rows": rows,
        "present": dict(present),
        "empty": dict(empty),
        "json_errors": json_errors[:20],
        "source_systems": dict(source_systems.most_common()),
        "forums": dict(forums.most_common()),
        "samples": samples,
    }


def compatible_count(chunks: dict[str, Any], *keys: str) -> int:
    rows = int(chunks["rows"])
    missing_all = min(int(chunks["empty"].get(key, rows)) for key in keys)
    return rows - missing_all


def markdown_report(chroma: dict[str, Any], chunks: dict[str, Any]) -> str:
    vector_count = chroma["vector_count"]
    chunk_count = chunks["rows"]
    count_match = vector_count == chunk_count
    collection_names = ", ".join(collection["name"] for collection in chroma["collections"]) or "(none)"
    lines = [
        "# SGF Embedding Audit",
        "",
        "## Summary",
        f"- Chroma path: `{chroma['path']}`",
        f"- Chroma SQLite: `{chroma['sqlite']}`",
        f"- Collection(s): `{collection_names}`",
        f"- Chunk file: `{chunks['path']}`",
        f"- Embedded vectors: `{vector_count:,}`",
        f"- Stored documents/excerpts: `{chroma['document_count']:,}`",
        f"- Chunk rows: `{chunk_count:,}`",
        f"- Vector/chunk count match: `{'yes' if count_match else 'no'}`",
        "",
        "## Chroma Metadata",
        "| key | present | nonempty | missing |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key in CHROMA_REQUIRED_KEYS:
        counts = chroma["required"][key]
        lines.append(f"| `{key}` | {counts['present']:,} | {counts['nonempty']:,} | {counts['missing']:,} |")

    lines.extend(
        [
            "",
            "## Chunk File Fields",
            "| key | present | empty/missing |",
            "| --- | ---: | ---: |",
        ]
    )
    for key in CHUNK_REQUIRED_KEYS:
        lines.append(
            f"| `{key}` | {chunks['present'].get(key, 0):,} | {chunks['empty'].get(key, 0):,} |"
        )

    source_text_count = compatible_count(chunks, "text", "chunk_text")
    post_identity_count = compatible_count(chunks, "post_uid", "post_uids")
    lines.extend(
        [
            "",
            "## Compatibility Checks",
            "| expectation | compatibility rule | passing rows | missing rows |",
            "| --- | --- | ---: | ---: |",
            (
                f"| post identity | scalar `post_uid` or nonempty `post_uids` | "
                f"{post_identity_count:,} | {chunk_count - post_identity_count:,} |"
            ),
            (
                f"| source text | `text`, `chunk_text`, or Chroma document content | "
                f"{max(source_text_count, chroma['document_count']):,} | "
                f"{chunk_count - max(source_text_count, chroma['document_count']):,} |"
            ),
            (
                f"| chunk identity | nonempty `chunk_id` | "
                f"{chunks['present'].get('chunk_id', 0) - chunks['empty'].get('chunk_id', 0):,} | "
                f"{chunks['empty'].get('chunk_id', 0):,} |"
            ),
        ]
    )

    lines.extend(
        [
            "",
            "## Source Systems",
        ]
    )
    for key, count in chunks["source_systems"].items():
        lines.append(f"- `{key}`: `{count:,}`")

    lines.extend(["", "## Metadata Notes"])
    notes = []
    if chroma["required"]["post_uid"]["present"] == 0 and chroma["required"]["chunk_id"]["present"] == vector_count:
        notes.append("Chroma metadata does not include scalar `post_uid`; approved compatibility treats `chunk_id` as the vector-level required identity.")
    if chunks["present"].get("post_uid", 0) == 0 and chunks["present"].get("post_uids", 0) == chunk_count:
        notes.append("Approved compatibility treats nonempty `post_uids` arrays as post identity when scalar `post_uid` is missing.")
    if chunks["present"].get("text", 0) == 0 and chunks["present"].get("chunk_text", 0) == chunk_count:
        notes.append("Approved compatibility treats `chunk_text` and Chroma document content as source text when `text` is missing.")
    if not notes:
        notes.append("No required metadata problems found.")
    lines.extend(f"- {note}" for note in notes)

    if chunks["json_errors"]:
        lines.extend(["", "## JSON Errors"])
        lines.extend(f"- `{error}`" for error in chunks["json_errors"])

    lines.append("")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chroma",
        type=Path,
        default=DEFAULT_CHROMA,
        help="Chroma directory or chroma.sqlite3 path. Defaults to STEEL_RAG_CHROMA_PATH or STEEL_RAG_CORPUS_ROOT/vector-stores/chroma.",
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS,
        help="Chunk JSONL used for embedding. Defaults to STEEL_RAG_CHUNKS_PATH or STEEL_RAG_CORPUS_ROOT/chunks.jsonl.",
    )
    parser.add_argument("--output", type=Path, help="Optional Markdown report path.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    chroma = audit_chroma(args.chroma)
    chunks = audit_chunks(args.chunks)
    report = markdown_report(chroma, chunks)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
