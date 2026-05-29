#!/usr/bin/env python3
"""Search the source-inbox private Chroma collection without app wiring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_common import DEFAULT_EMBEDDING_MODEL, excerpt, ollama_embed, parse_json_metadata
from scripts.private_source_embed_preflight import DEFAULT_COLLECTION, DEFAULT_VECTOR_PATH, EXPECTED_COLLECTION, vector_path_is_private


METADATA_FIELDS = (
    "source_id",
    "source_system",
    "visibility",
    "title",
    "source_path",
    "provenance_status",
    "answer_quote_allowed",
    "embedding_allowed",
)


class QueryCollection(Protocol):
    def query(self, *, query_embeddings: list[list[float]], n_results: int, include: list[str]) -> dict[str, Any]:
        ...


def validate_private_search_destination(vector_path: Path, collection_name: str) -> None:
    if collection_name != EXPECTED_COLLECTION:
        raise SystemExit(f"collection name must be {EXPECTED_COLLECTION!r}")
    if not vector_path_is_private(vector_path):
        raise SystemExit("private source search must use corpus-private/ and must not point at SGF Chroma paths")


def decoded_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return {key: parse_json_metadata(value) for key, value in (metadata or {}).items()}


def get_private_collection(vector_path: Path, collection_name: str) -> QueryCollection:
    import chromadb  # type: ignore

    client = chromadb.PersistentClient(path=str(vector_path))
    return client.get_collection(collection_name)


def source_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {field: metadata.get(field) for field in METADATA_FIELDS}


def search_private_sources(
    query: str,
    *,
    vector_path: Path = DEFAULT_VECTOR_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    embedding_model: str | None = DEFAULT_EMBEDDING_MODEL,
    top_k: int = 5,
    collection: QueryCollection | None = None,
    embed_query: Callable[[list[str], str | None], list[list[float]]] | None = None,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise SystemExit("--query must not be empty")
    if top_k < 1:
        raise SystemExit("--top-k must be positive")
    validate_private_search_destination(vector_path, collection_name)

    collection = collection or get_private_collection(vector_path, collection_name)
    embedder = embed_query or ollama_embed
    query_embedding = embedder([query], embedding_model)[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    rows: list[dict[str, Any]] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0] if results.get("ids") else [""] * len(documents)
    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        decoded = decoded_metadata(metadata)
        rows.append(
            {
                "chunk_id": decoded.get("chunk_id") or chunk_id,
                "distance": distance,
                "metadata": source_metadata(decoded),
                "text": document or "",
            }
        )
    return rows


def print_results(rows: list[dict[str, Any]], *, show_excerpts: bool) -> None:
    if not rows:
        print("No private source chunks found.")
        return
    for rank, row in enumerate(rows, start=1):
        metadata = row["metadata"]
        print(f"\n{rank}. {metadata.get('title') or '(untitled private source)'}")
        print(f"   Chunk ID: {row.get('chunk_id') or ''}")
        print(f"   Source ID: {metadata.get('source_id') or ''}")
        print(f"   Source system: {metadata.get('source_system') or ''}")
        print(f"   Visibility: {metadata.get('visibility') or ''}")
        print(f"   Source path: {metadata.get('source_path') or ''}")
        print(f"   Provenance: {metadata.get('provenance_status') or ''}")
        print(f"   Answer quote allowed: {metadata.get('answer_quote_allowed')}")
        print(f"   Embedding allowed: {metadata.get('embedding_allowed')}")
        print(f"   Distance: {float(row['distance']):.4f}")
        if show_excerpts:
            print(f"   Excerpt: {excerpt(row.get('text') or '', width=360)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--vector-path", type=Path, default=DEFAULT_VECTOR_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--show-excerpts", action="store_true")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--json", action="store_true", help="Print JSON rows instead of human-readable output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = search_private_sources(
        args.query,
        vector_path=args.vector_path,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        top_k=args.top_k,
    )
    if args.json:
        payload = rows if args.show_excerpts else [{key: value for key, value in row.items() if key != "text"} for row in rows]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_results(rows, show_excerpts=args.show_excerpts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
