"""Read-only Chroma retrieval and metadata normalization."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from rag_common import DEFAULT_EMBEDDING_MODEL, parse_json_metadata, project_path
from pocketsteel.api_contract import SearchResult
from pocketsteel.text import shorten


DEFAULT_CHROMA_PATH = "rag-data/electronics/chroma"
DEFAULT_COLLECTION_NAME = "steel_guitar_unified"
DEFAULT_FALLBACK_COLLECTION_NAME = "electronics"
CHROMA_PATH_ENV = "STEEL_RAG_CHROMA_PATH"
CHROMA_COLLECTION_ENV = "STEEL_RAG_CHROMA_COLLECTION"


@dataclass(frozen=True)
class NormalizedSearchResult:
    score: float
    excerpt: str
    source_system: str
    forum_name: str
    thread_title: str
    thread_url: str
    chunk_id: str
    post_uid: str
    source_kind: str
    forum_id: str
    legacy_forum_number: str
    thread_id: str
    legacy_thread_uid: str
    thread_category: str
    thread_quality_score: Any
    chunk_index: Any
    warnings: list[str]

    def to_dict(self) -> SearchResult:
        return {
            "score": self.score,
            "excerpt": self.excerpt,
            "source_system": self.source_system,
            "forum_name": self.forum_name,
            "thread_title": self.thread_title,
            "thread_url": self.thread_url,
            "chunk_id": self.chunk_id,
            "post_uid": self.post_uid,
            "source_kind": self.source_kind,
            "forum_id": self.forum_id,
            "legacy_forum_number": self.legacy_forum_number,
            "thread_id": self.thread_id,
            "legacy_thread_uid": self.legacy_thread_uid,
            "thread_category": self.thread_category,
            "thread_quality_score": self.thread_quality_score,
            "chunk_index": self.chunk_index,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class SearchResponse:
    results: list[dict[str, Any]]
    warnings: list[str]


def first_list_item(value: Any) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    return None


def normalize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return {key: parse_json_metadata(value) for key, value in (metadata or {}).items()}


def distance_to_score(distance: Any) -> float:
    try:
        value = float(distance)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value):
        return 0.0
    return round(1.0 / (1.0 + max(value, 0.0)), 6)


def normalize_chroma_result(
    *,
    chroma_id: Any,
    document: Any,
    metadata: dict[str, Any] | None,
    distance: Any,
    row_index: int,
    excerpt_chars: int = 550,
) -> tuple[dict[str, Any] | None, list[str]]:
    metadata = normalize_metadata(metadata)
    warnings: list[str] = []
    reject_warnings: list[str] = []

    chunk_id = str(metadata.get("chunk_id") or chroma_id or "").strip()
    if not metadata.get("chunk_id") and chunk_id:
        warnings.append("used Chroma id as chunk_id")

    post_uid_value = metadata.get("post_uid")
    if not post_uid_value:
        post_uid_value = first_list_item(metadata.get("post_uids"))
        if post_uid_value:
            warnings.append("used first post_uids item as post_uid")
    if not post_uid_value and chunk_id:
        post_uid_value = chunk_id
        warnings.append("used chunk_id as post_uid")
    post_uid = str(post_uid_value or "").strip()

    text_value = metadata.get("text")
    if not text_value:
        text_value = metadata.get("chunk_text")
        if text_value:
            warnings.append("used metadata.chunk_text as text")
    if not text_value:
        text_value = document
        if text_value:
            warnings.append("used Chroma document content as text")
    text = str(text_value or "").strip()

    thread_url_value = metadata.get("thread_url")
    if not thread_url_value:
        thread_url_value = metadata.get("source_url")
        if thread_url_value:
            warnings.append("used source_url as thread_url")
    thread_url = str(thread_url_value or "").strip()

    if not text:
        reject_warnings.append(f"rejected result {row_index}: missing usable text")
    if not thread_url:
        reject_warnings.append(f"rejected result {row_index}: missing source URL")
    if reject_warnings:
        return None, reject_warnings

    result = NormalizedSearchResult(
        score=distance_to_score(distance),
        excerpt=shorten(text, excerpt_chars),
        source_system=str(metadata.get("source_system") or "").strip(),
        forum_name=str(metadata.get("forum_name") or "").strip(),
        thread_title=str(metadata.get("thread_title") or "").strip(),
        thread_url=thread_url,
        chunk_id=chunk_id,
        post_uid=post_uid,
        source_kind=str(metadata.get("source_kind") or "").strip(),
        forum_id=str(metadata.get("forum_id") or "").strip(),
        legacy_forum_number=str(metadata.get("legacy_forum_number") or "").strip(),
        thread_id=str(metadata.get("thread_id") or "").strip(),
        legacy_thread_uid=str(metadata.get("legacy_thread_uid") or "").strip(),
        thread_category=str(metadata.get("thread_category") or "").strip(),
        thread_quality_score=metadata.get("thread_quality_score"),
        chunk_index=metadata.get("chunk_index"),
        warnings=warnings,
    )
    return result.to_dict(), []


def configured_chroma_path(chroma_path: str | Path | None = None) -> Path:
    configured = chroma_path or os.environ.get(CHROMA_PATH_ENV) or DEFAULT_CHROMA_PATH
    return project_path(configured)


def configured_collection_name(collection_name: str | None = None) -> str:
    return collection_name or os.environ.get(CHROMA_COLLECTION_ENV) or DEFAULT_COLLECTION_NAME


def get_read_only_collection(chroma_path: str | Path | None, collection_name: str | None):
    resolved_path = configured_chroma_path(chroma_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Chroma index not found: {resolved_path}")

    try:
        import chromadb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing dependency: chromadb. Install the rag extra before using Chroma search.") from exc

    client = chromadb.PersistentClient(path=str(resolved_path))
    resolved_collection_name = configured_collection_name(collection_name)
    try:
        return client.get_collection(name=resolved_collection_name)
    except Exception:
        if collection_name is not None or os.environ.get(CHROMA_COLLECTION_ENV):
            raise
        return client.get_collection(name=DEFAULT_FALLBACK_COLLECTION_NAME)


def build_where_filter(source_system: str | None = None, forum_name: str | None = None) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if source_system:
        clauses.append({"source_system": source_system})
    if forum_name:
        clauses.append({"forum_name": forum_name})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


class ChromaSearchIndex:
    def __init__(
        self,
        *,
        collection: Any,
        embedder: Callable[[list[str], str | None], list[list[float]]],
        model: str | None = None,
    ) -> None:
        self.collection = collection
        self.embedder = embedder
        self.model = model

    @classmethod
    def from_chroma(
        cls,
        *,
        chroma_path: str | Path | None = None,
        collection_name: str | None = None,
        model: str | None = None,
    ) -> "ChromaSearchIndex":
        from rag_common import ollama_embed

        return cls(
            collection=get_read_only_collection(chroma_path, collection_name),
            embedder=ollama_embed,
            model=model or DEFAULT_EMBEDDING_MODEL,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        query = query.strip()
        if not query or limit <= 0:
            return SearchResponse(results=[], warnings=[])

        embedding = self.embedder([query], self.model)[0]
        where = build_where_filter(source_system=source_system, forum_name=forum_name)
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where
        raw_results = self.collection.query(
            **query_kwargs,
        )
        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        results: list[dict[str, Any]] = []
        warnings: list[str] = []
        row_count = max(len(ids), len(documents), len(metadatas), len(distances))
        for index in range(row_count):
            normalized, row_warnings = normalize_chroma_result(
                chroma_id=ids[index] if index < len(ids) else "",
                document=documents[index] if index < len(documents) else "",
                metadata=metadatas[index] if index < len(metadatas) else {},
                distance=distances[index] if index < len(distances) else None,
                row_index=index,
            )
            warnings.extend(row_warnings)
            if normalized is not None:
                results.append(normalized)

        return SearchResponse(results=results, warnings=warnings)
