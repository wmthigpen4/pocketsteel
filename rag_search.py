#!/usr/bin/env python3
"""Search the local Electronics Chroma vector store."""

from __future__ import annotations

import argparse
from typing import Any

from rag_common import (
    DEFAULT_EMBEDDING_MODEL,
    chroma_collection,
    excerpt,
    ollama_embed,
    parse_json_metadata,
    project_path,
)


DEFAULT_CHROMA = "rag-data/electronics/chroma"


def search_chunks(
    query: str,
    chroma_path: str = DEFAULT_CHROMA,
    collection_name: str = "electronics",
    model: str | None = None,
    top_k: int = 5,
    forum_name: str | None = None,
    thread_title: str | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    collection = chroma_collection(project_path(chroma_path), collection_name)
    query_embedding = ollama_embed([query], model=model)[0]
    where = {"forum_name": forum_name} if forum_name else None
    n_results = max(top_k * 4, top_k) if thread_title or date else top_k
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    rows: list[dict[str, Any]] = []
    for doc, metadata, distance in zip(
        results.get("documents", [[]])[0],
        results.get("metadatas", [[]])[0],
        results.get("distances", [[]])[0],
    ):
        metadata = {key: parse_json_metadata(value) for key, value in (metadata or {}).items()}
        if thread_title and thread_title.lower() not in (metadata.get("thread_title") or "").lower():
            continue
        if date and date not in " ".join(metadata.get("post_dates_raw") or [metadata.get("post_date_raw") or ""]):
            continue
        rows.append({"text": doc, "metadata": metadata, "distance": distance})
        if len(rows) >= top_k:
            break
    return rows


def print_results(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No chunks found.")
        return
    for index, row in enumerate(rows, 1):
        metadata = row["metadata"]
        title = metadata.get("thread_title") or "(untitled thread)"
        url = metadata.get("source_url") or metadata.get("thread_url") or ""
        username = metadata.get("username") or ""
        date = metadata.get("post_date") or metadata.get("post_date_raw") or ""
        print(f"\n{index}. {title}")
        print(f"   URL: {url}")
        if username or date:
            print(f"   Post: {username} {date}".strip())
        print(f"   Distance: {row['distance']:.4f}")
        print(f"   Excerpt: {excerpt(row['text'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--chroma", default=DEFAULT_CHROMA)
    parser.add_argument("--collection", default="electronics")
    parser.add_argument("--model", default=None, help=f"Embedding model; defaults to EMBEDDING_MODEL or {DEFAULT_EMBEDDING_MODEL}")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--forum-name")
    parser.add_argument("--thread-title")
    parser.add_argument("--date")
    args = parser.parse_args()

    rows = search_chunks(
        args.query,
        chroma_path=args.chroma,
        collection_name=args.collection,
        model=args.model,
        top_k=args.top_k,
        forum_name=args.forum_name,
        thread_title=args.thread_title,
        date=args.date,
    )
    print_results(rows)


if __name__ == "__main__":
    main()
