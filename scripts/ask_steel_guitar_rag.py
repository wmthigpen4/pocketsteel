#!/usr/bin/env python3
"""Ask Steel Guitar RAG local vector index a source-grounded question."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from steel_guitar_rag.retrieval import best_excerpt, cosine_search, hashing_embed_texts, normalize_matrix
from steel_guitar_rag.schema import read_jsonl


def embed_query(question: str, manifest: dict[str, Any]) -> np.ndarray:
    backend = manifest["backend"]
    if backend == "hashing":
        dimensions = int(manifest["vector_dimensions"])
        return hashing_embed_texts([question], dimensions=dimensions)[0]

    if backend == "sentence-transformers":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise SystemExit(
                "sentence-transformers is not installed. Run `python -m pip install -e \".[rag]\"` "
                "or query an index built with `--backend hashing`."
            ) from exc
        model = SentenceTransformer(manifest["model_name"])
        vector = model.encode([question], normalize_embeddings=True)
        return np.asarray(vector, dtype=np.float32)[0]

    raise ValueError(f"Unsupported index backend: {backend}")


def load_index(index_dir: Path) -> tuple[dict[str, Any], np.ndarray, list[dict[str, Any]]]:
    with (index_dir / "manifest.json").open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    vectors = normalize_matrix(np.load(index_dir / manifest["files"]["vectors"]))
    chunks = [record for _, record in read_jsonl(index_dir / manifest["files"]["chunks"])]
    if len(chunks) != vectors.shape[0]:
        raise SystemExit("Index is inconsistent: chunk metadata count does not match vector count.")
    return manifest, vectors, chunks


def source_label(chunk: dict[str, Any]) -> str:
    title = chunk.get("title") or "Untitled SGF source"
    author = chunk.get("author")
    posted_at = chunk.get("posted_at")
    pieces = [title]
    if author:
        pieces.append(f"by {author}")
    if posted_at:
        pieces.append(str(posted_at))
    return " - ".join(pieces)


def render_answer(
    question: str,
    hits: list[tuple[dict[str, Any], float]],
    *,
    min_score: float,
    excerpt_chars: int,
) -> str:
    supported_hits = [(chunk, score) for chunk, score in hits if score >= min_score]
    if not supported_hits:
        supported_hits = hits[: min(3, len(hits))]
        status = "I do not have enough source support for a confident answer. Closest retrieved sources:"
    else:
        status = "Source-grounded answer:"

    lines = [f"Question: {question}", "", status]
    for index, (chunk, score) in enumerate(supported_hits, start=1):
        excerpt = best_excerpt(chunk["text"], question, max_chars=excerpt_chars)
        lines.append(f"{index}. {excerpt}")
        lines.append(f"   Source: {source_label(chunk)}")
        if chunk.get("url"):
            lines.append(f"   Link: {chunk['url']}")
        lines.append(f"   Score: {score:.3f}")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-dir", required=True, help="Directory created by build_vector_index.py.")
    parser.add_argument("--question", required=True, help="Question to ask.")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--min-score", type=float, default=0.15)
    parser.add_argument("--excerpt-chars", type=int, default=550)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    manifest, vectors, chunks = load_index(Path(args.index_dir))
    query_vector = embed_query(args.question, manifest)
    hits = [(chunks[index], score) for index, score in cosine_search(vectors, query_vector, args.top_k)]
    print(render_answer(args.question, hits, min_score=args.min_score, excerpt_chars=args.excerpt_chars))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
