#!/usr/bin/env python3
"""Embed Electronics chunks into a local Chroma vector store using Ollama."""

from __future__ import annotations

import argparse
import os
import shutil
from itertools import islice
from pathlib import Path

from rag_common import (
    DEFAULT_EMBEDDING_MODEL,
    chroma_collection,
    jsonl_reader,
    metadata_for_chroma,
    ollama_embed,
    project_path,
)


DEFAULT_INPUT = "rag-data/electronics/chunks.jsonl"
DEFAULT_CHROMA = "rag-data/electronics/chroma"


def batched(iterator, size: int):
    while True:
        batch = list(islice(iterator, size))
        if not batch:
            return
        yield batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--chroma", default=DEFAULT_CHROMA)
    parser.add_argument("--collection", default="electronics")
    parser.add_argument("--model", default=None, help=f"Embedding model; defaults to EMBEDDING_MODEL or {DEFAULT_EMBEDDING_MODEL}")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--reset", action="store_true", help="Delete the existing Chroma directory before embedding.")
    args = parser.parse_args()

    input_path = project_path(args.input)
    chroma_path = project_path(args.chroma)
    model = args.model or os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    if args.reset and chroma_path.exists():
        shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)
    collection = chroma_collection(chroma_path, args.collection)

    total = 0
    for batch in batched(jsonl_reader(input_path), args.batch_size):
        ids = [row["chunk_id"] for row in batch]
        documents = [row["text"] for row in batch]
        metadatas = [metadata_for_chroma(row) for row in batch]
        embeddings = ollama_embed(documents, model=model)
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        total += len(batch)
        print(f"Embedded {total} chunks", flush=True)

    print(f"Chroma store ready at {Path(chroma_path)}")


if __name__ == "__main__":
    main()
