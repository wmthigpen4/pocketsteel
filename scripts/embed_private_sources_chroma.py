#!/usr/bin/env python3
"""Embed approved private source-inbox chunks into a private Chroma collection."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_common import DEFAULT_EMBEDDING_MODEL, ollama_embed
from scripts.private_source_embed_preflight import (
    DEFAULT_COLLECTION,
    DEFAULT_INPUT,
    DEFAULT_VECTOR_PATH,
    EXPECTED_COLLECTION,
    truthy_embedding,
    validate_chunks,
    vector_path_is_private,
)


DEFAULT_REPORT = Path("corpus-private/reports/private-source-embedding-report.md")
METADATA_FIELDS = (
    "chunk_id",
    "source_id",
    "source_system",
    "visibility",
    "source_path",
    "title",
    "file_type",
    "document_index",
    "chunk_index",
    "source_url",
    "provenance_status",
    "redistribution_allowed",
    "embedding_allowed",
    "answer_quote_allowed",
    "chunk_role",
    "quality_score",
    "noise_score",
)


class CollectionLike(Protocol):
    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, str | int | float | bool]],
        embeddings: list[list[float]],
    ) -> Any:
        ...

    def count(self) -> int:
        ...


@dataclass
class EmbedResult:
    dry_run: bool
    input_path: str
    vector_path: str
    collection: str
    model: str
    chunks_read: int
    chunks_eligible: int
    chunks_embedded: int
    skipped_embedding_false: int
    reset_private_collection: bool
    report_path: str


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            yield value


def batched(rows: Iterable[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    iterator = iter(rows)
    while True:
        batch = list(islice(iterator, size))
        if not batch:
            return
        yield batch


def metadata_value(value: Any) -> str | int | float | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def metadata_for_chunk(row: dict[str, Any]) -> dict[str, str | int | float | bool]:
    return {field: metadata_value(row.get(field)) for field in METADATA_FIELDS}


def eligible_chunks(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    eligible: list[dict[str, Any]] = []
    total = 0
    skipped = 0
    for row in rows:
        total += 1
        if truthy_embedding(row.get("embedding_allowed")):
            eligible.append(row)
        else:
            skipped += 1
    return eligible, total, skipped


def validate_embedding_destination(vector_path: Path, collection_name: str) -> None:
    if collection_name != EXPECTED_COLLECTION:
        raise SystemExit(f"collection name must be {EXPECTED_COLLECTION!r}")
    if not vector_path_is_private(vector_path):
        raise SystemExit("target vector path must be under corpus-private/ and separate from SGF Chroma paths")


def get_chroma_collection(vector_path: Path, collection_name: str, *, reset_private_collection: bool) -> CollectionLike:
    import chromadb  # type: ignore

    vector_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(vector_path))
    if reset_private_collection:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    return client.get_or_create_collection(collection_name)


def run_preflight_or_fail(input_path: Path, vector_path: Path, collection_name: str) -> None:
    result = validate_chunks(input_path, vector_path=vector_path, collection=collection_name)
    if not result.ok:
        raise SystemExit("private source embed preflight failed; run scripts/private_source_embed_preflight.py")


def embed_private_sources(
    *,
    input_path: Path,
    vector_path: Path,
    collection_name: str,
    model: str,
    batch_size: int,
    dry_run: bool,
    confirm_preflight_pass: bool,
    reset_private_collection: bool,
    report_path: Path,
    collection_factory: Callable[[Path, str, bool], CollectionLike] | None = None,
    embed_texts: Callable[[list[str], str | None], list[list[float]]] | None = None,
) -> EmbedResult:
    if batch_size < 1:
        raise SystemExit("--batch-size must be positive")
    validate_embedding_destination(vector_path, collection_name)
    run_preflight_or_fail(input_path, vector_path, collection_name)
    if not dry_run and not confirm_preflight_pass:
        raise SystemExit("refusing real private embedding without --confirm-preflight-pass")

    chunks, chunks_read, skipped_embedding_false = eligible_chunks(read_jsonl(input_path))
    result = EmbedResult(
        dry_run=dry_run,
        input_path=input_path.as_posix(),
        vector_path=vector_path.as_posix(),
        collection=collection_name,
        model=model,
        chunks_read=chunks_read,
        chunks_eligible=len(chunks),
        chunks_embedded=0,
        skipped_embedding_false=skipped_embedding_false,
        reset_private_collection=reset_private_collection,
        report_path=report_path.as_posix(),
    )

    if dry_run:
        write_report(report_path, result)
        return result

    factory = collection_factory or (
        lambda path, name, reset: get_chroma_collection(path, name, reset_private_collection=reset)
    )
    embedder = embed_texts or ollama_embed
    collection = factory(vector_path, collection_name, reset_private_collection)

    embedded = 0
    for batch in batched(chunks, batch_size):
        ids = [str(row["chunk_id"]) for row in batch]
        documents = [str(row["text"]) for row in batch]
        metadatas = [metadata_for_chunk(row) for row in batch]
        embeddings = embedder(documents, model)
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        embedded += len(batch)

    result.chunks_embedded = embedded
    write_report(report_path, result)
    return result


def write_report(path: Path, result: EmbedResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Private Source Embedding Report",
        "",
        "This report covers the private source-inbox embedding script. It does not include private source text.",
        "",
        f"- Created at: `{utc_now()}`",
        f"- Dry run: `{result.dry_run}`",
        f"- Input chunks: `{result.input_path}`",
        f"- Vector path: `{result.vector_path}`",
        f"- Collection: `{result.collection}`",
        f"- Embedding model: `{result.model}`",
        f"- Chunks read: `{result.chunks_read}`",
        f"- Eligible chunks: `{result.chunks_eligible}`",
        f"- Embedded chunks: `{result.chunks_embedded}`",
        f"- Skipped embedding_allowed=false: `{result.skipped_embedding_false}`",
        f"- Reset private collection: `{result.reset_private_collection}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--vector-path", type=Path, default=DEFAULT_VECTOR_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--model", default=os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-preflight-pass", action="store_true")
    parser.add_argument("--reset-private-collection", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = embed_private_sources(
        input_path=args.input,
        vector_path=args.vector_path,
        collection_name=args.collection,
        model=args.model,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        confirm_preflight_pass=args.confirm_preflight_pass,
        reset_private_collection=args.reset_private_collection,
        report_path=args.report,
    )
    print(f"Dry run: {result.dry_run}")
    print(f"Chunks read: {result.chunks_read}")
    print(f"Eligible chunks: {result.chunks_eligible}")
    print(f"Embedded chunks: {result.chunks_embedded}")
    print(f"Report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
