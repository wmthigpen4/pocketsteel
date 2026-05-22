#!/usr/bin/env python3
"""Build a small local vector index from The Turnaround chunks."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from pocketsteel.retrieval import hashing_embed_texts, normalize_matrix
from pocketsteel.schema import read_jsonl, write_jsonl


def embed_sentence_transformers(texts: list[str], model_name: str, batch_size: int) -> np.ndarray:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "sentence-transformers is not installed. Run `python -m pip install -e \".[rag]\"` "
            "or use `--backend hashing` for an offline smoke index."
        ) from exc

    model = SentenceTransformer(model_name)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return np.asarray(vectors, dtype=np.float32)


def build_index(
    chunks_path: Path,
    output_dir: Path,
    *,
    backend: str,
    model_name: str,
    batch_size: int,
    dimensions: int,
) -> dict[str, Any]:
    chunks = [record for _, record in read_jsonl(chunks_path)]
    texts = [chunk["text"] for chunk in chunks]
    if not chunks:
        raise SystemExit(f"No chunks found in {chunks_path}")

    if backend == "sentence-transformers":
        vectors = embed_sentence_transformers(texts, model_name, batch_size)
    elif backend == "hashing":
        vectors = hashing_embed_texts(texts, dimensions=dimensions)
        model_name = f"hashing-{dimensions}"
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    vectors = normalize_matrix(np.asarray(vectors, dtype=np.float32))
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "vectors.npy", vectors)
    write_jsonl(output_dir / "chunks.jsonl", chunks)

    manifest = {
        "backend": backend,
        "model_name": model_name,
        "chunk_count": len(chunks),
        "vector_dimensions": int(vectors.shape[1]),
        "chunks_path": str(chunks_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            "vectors": "vectors.npy",
            "chunks": "chunks.jsonl",
        },
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", required=True, help="Chunk JSONL path.")
    parser.add_argument("--output-dir", required=True, help="Directory for vectors and metadata.")
    parser.add_argument(
        "--backend",
        choices=("sentence-transformers", "hashing"),
        default="sentence-transformers",
        help="Embedding backend. Use hashing for dependency-light smoke tests.",
    )
    parser.add_argument("--model-name", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--dimensions", type=int, default=1024, help="Hashing backend dimensions.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    manifest = build_index(
        Path(args.chunks),
        Path(args.output_dir),
        backend=args.backend,
        model_name=args.model_name,
        batch_size=args.batch_size,
        dimensions=args.dimensions,
    )
    print(f"Wrote {manifest['chunk_count']} vectors to {args.output_dir}")
    print(f"Backend: {manifest['backend']} ({manifest['model_name']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
