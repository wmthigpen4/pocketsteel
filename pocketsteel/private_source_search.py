"""Read-only private source retrieval adapter.

The app only uses this adapter when retrieval modes explicitly allow private
sources. It is intentionally separate from SGF Chroma retrieval so private
chunks cannot be mixed into public collections by accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from rag_common import DEFAULT_EMBEDDING_MODEL, parse_json_metadata, project_path
from pocketsteel.chroma_search import distance_to_score
from pocketsteel.retrieval_modes import DEFAULT_PRIVATE_CHROMA_PATH, DEFAULT_PRIVATE_COLLECTION
from pocketsteel.text import shorten


PRIVATE_VECTOR_FORBIDDEN_PARTS = (
    ("data", "rag", "chroma"),
    ("rag-data",),
    ("corpus-v2",),
    ("corpus-unified",),
    ("sgf-output",),
)


def _path_parts(path: Path) -> tuple[str, ...]:
    return tuple(part for part in path.as_posix().split("/") if part and part != ".")


def _contains_sequence(parts: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    if len(sequence) > len(parts):
        return False
    return any(parts[index : index + len(sequence)] == sequence for index in range(len(parts) - len(sequence) + 1))


def private_vector_path_is_safe(path: Path) -> bool:
    parts = _path_parts(path)
    return "corpus-private" in parts and not any(
        _contains_sequence(parts, sequence) for sequence in PRIVATE_VECTOR_FORBIDDEN_PARTS
    )


def _decoded_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return {key: parse_json_metadata(value) for key, value in (metadata or {}).items()}


def normalize_private_source_result(
    *,
    chroma_id: Any,
    document: Any,
    metadata: dict[str, Any] | None,
    distance: Any,
    excerpt_chars: int = 550,
) -> dict[str, Any] | None:
    decoded = _decoded_metadata(metadata)
    text = str(document or decoded.get("text") or "").strip()
    if not text:
        return None

    chunk_id = str(decoded.get("chunk_id") or chroma_id or "").strip()
    source_path = str(decoded.get("source_path") or "").strip()
    source_url = str(decoded.get("source_url") or "").strip()
    title = str(decoded.get("title") or "Private source").strip()

    return {
        "score": distance_to_score(distance),
        "excerpt": shorten(text, excerpt_chars),
        "source_system": str(decoded.get("source_system") or "private_source").strip(),
        "forum_name": "Private Sources",
        "thread_title": title,
        "thread_url": source_url or source_path,
        "chunk_id": chunk_id,
        "post_uid": chunk_id,
        "source_kind": "private_source_chunk",
        "forum_id": "",
        "legacy_forum_number": "",
        "thread_id": "",
        "legacy_thread_uid": "",
        "thread_category": "",
        "thread_quality_score": "",
        "chunk_index": decoded.get("chunk_index", ""),
        "warnings": [],
        "source_id": decoded.get("source_id"),
        "visibility": decoded.get("visibility"),
        "source_path": source_path,
        "provenance_status": decoded.get("provenance_status"),
        "answer_quote_allowed": decoded.get("answer_quote_allowed"),
        "embedding_allowed": decoded.get("embedding_allowed"),
    }


def get_private_collection(chroma_path: str | Path | None, collection_name: str | None):
    resolved_path = project_path(chroma_path or DEFAULT_PRIVATE_CHROMA_PATH)
    if not private_vector_path_is_safe(resolved_path):
        raise ValueError("Private source retrieval must use corpus-private/ and must not point at SGF Chroma paths.")
    if not resolved_path.exists():
        raise FileNotFoundError(f"Private Chroma index not found: {resolved_path}")

    try:
        import chromadb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing dependency: chromadb. Install the rag extra before using private Chroma search.") from exc

    client = chromadb.PersistentClient(path=str(resolved_path))
    return client.get_collection(name=collection_name or DEFAULT_PRIVATE_COLLECTION)


@dataclass
class PrivateSourceSearchIndex:
    collection: Any
    embedder: Callable[[list[str], str | None], list[list[float]]]
    model: str | None = None

    @classmethod
    def from_chroma(
        cls,
        *,
        chroma_path: str | Path | None = None,
        collection_name: str | None = None,
        model: str | None = None,
    ) -> "PrivateSourceSearchIndex":
        from rag_common import ollama_embed

        return cls(
            collection=get_private_collection(chroma_path, collection_name),
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
    ):
        from pocketsteel.chroma_search import SearchResponse

        query = query.strip()
        if not query or limit <= 0:
            return SearchResponse(results=[], warnings=[])

        embedding = self.embedder([query], self.model)[0]
        raw_results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        results: list[dict[str, Any]] = []
        row_count = max(len(ids), len(documents), len(metadatas), len(distances))
        for index in range(row_count):
            result = normalize_private_source_result(
                chroma_id=ids[index] if index < len(ids) else "",
                document=documents[index] if index < len(documents) else "",
                metadata=metadatas[index] if index < len(metadatas) else {},
                distance=distances[index] if index < len(distances) else None,
            )
            if result is None:
                continue
            if source_system and result.get("source_system") != source_system:
                continue
            if forum_name and result.get("forum_name") != forum_name:
                continue
            results.append(result)

        return SearchResponse(results=results, warnings=[])
