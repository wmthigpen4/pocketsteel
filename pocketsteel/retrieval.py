"""Small local retrieval helpers for the Pocket Steel vertical slice."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

import numpy as np

from pocketsteel.text import shorten, split_sentences


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#'/-]*", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def hashing_embed_texts(texts: Sequence[str], dimensions: int = 1024) -> np.ndarray:
    vectors = np.zeros((len(texts), dimensions), dtype=np.float32)
    for row, text in enumerate(texts):
        tokens = tokenize(text)
        grams = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        for token in grams:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % dimensions
            sign = 1.0 if (value >> 63) == 0 else -1.0
            vectors[row, index] += sign
    return normalize_matrix(vectors)


def cosine_search(vectors: np.ndarray, query_vector: np.ndarray, top_k: int) -> list[tuple[int, float]]:
    if query_vector.ndim == 2:
        query_vector = query_vector[0]
    scores = vectors @ query_vector
    if len(scores) == 0:
        return []
    top_k = min(top_k, len(scores))
    indexes = np.argpartition(-scores, top_k - 1)[:top_k]
    ranked = sorted(((int(index), float(scores[index])) for index in indexes), key=lambda item: item[1], reverse=True)
    return ranked


def best_excerpt(text: str, query: str, max_chars: int = 550) -> str:
    query_terms = set(tokenize(query))
    sentences = split_sentences(text)
    if not sentences:
        return shorten(text, max_chars)

    def score(sentence: str) -> tuple[int, int]:
        terms = set(tokenize(sentence))
        return (len(terms & query_terms), min(len(sentence), max_chars))

    best = max(sentences, key=score)
    if score(best)[0] == 0 and len(sentences) > 1:
        best = " ".join(sentences[:2])
    return shorten(best, max_chars)

