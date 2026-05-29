from __future__ import annotations

from pathlib import Path

import pytest

from scripts.search_private_sources import DEFAULT_COLLECTION, print_results, search_private_sources


class FakeCollection:
    def __init__(self) -> None:
        self.last_query: dict[str, object] | None = None

    def query(self, *, query_embeddings, n_results, include):  # type: ignore[no-untyped-def]
        self.last_query = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "include": include,
        }
        return {
            "ids": [["private:e9:doc-0:chunk-0000:abc"]],
            "documents": [["Private text about the E9 copedent should stay hidden unless excerpts are requested."]],
            "metadatas": [
                [
                    {
                        "chunk_id": "private:e9:doc-0:chunk-0000:abc",
                        "source_id": "e9-rules-seed",
                        "source_system": "personal_rules_note",
                        "visibility": "private",
                        "title": "E9 Rules Seed",
                        "source_path": "source-inbox/rules/e9.txt",
                        "provenance_status": "reviewed",
                        "answer_quote_allowed": "limited",
                        "embedding_allowed": True,
                        "extra_field": "ignored",
                    }
                ]
            ],
            "distances": [[0.1234]],
        }


def test_search_private_sources_returns_preserved_metadata() -> None:
    collection = FakeCollection()

    rows = search_private_sources(
        "What is my E9 copedent?",
        vector_path=Path("corpus-private/vector-stores/chroma"),
        collection_name=DEFAULT_COLLECTION,
        top_k=3,
        collection=collection,
        embed_query=lambda texts, _model: [[float(len(texts[0]))]],
    )

    assert collection.last_query is not None
    assert collection.last_query["n_results"] == 3
    assert collection.last_query["include"] == ["documents", "metadatas", "distances"]
    assert rows[0]["chunk_id"] == "private:e9:doc-0:chunk-0000:abc"
    assert rows[0]["distance"] == 0.1234
    assert rows[0]["metadata"] == {
        "source_id": "e9-rules-seed",
        "source_system": "personal_rules_note",
        "visibility": "private",
        "title": "E9 Rules Seed",
        "source_path": "source-inbox/rules/e9.txt",
        "provenance_status": "reviewed",
        "answer_quote_allowed": "limited",
        "embedding_allowed": True,
    }


def test_search_refuses_sgf_v1_v2_paths() -> None:
    with pytest.raises(SystemExit, match="must not point at SGF"):
        search_private_sources(
            "What does A+F do?",
            vector_path=Path("corpus-v2/vector-stores/chroma"),
            collection_name=DEFAULT_COLLECTION,
            collection=FakeCollection(),
            embed_query=lambda _texts, _model: [[1.0]],
        )


def test_search_refuses_wrong_collection() -> None:
    with pytest.raises(SystemExit, match="collection name must be"):
        search_private_sources(
            "What is the 10th string on E9?",
            vector_path=Path("corpus-private/vector-stores/chroma"),
            collection_name="steel_guitar_unified_v2",
            collection=FakeCollection(),
            embed_query=lambda _texts, _model: [[1.0]],
        )


def test_print_results_hides_private_text_without_show_excerpts(capsys: pytest.CaptureFixture[str]) -> None:
    rows = search_private_sources(
        "What are my common grips?",
        vector_path=Path("corpus-private/vector-stores/chroma"),
        collection_name=DEFAULT_COLLECTION,
        collection=FakeCollection(),
        embed_query=lambda _texts, _model: [[1.0]],
    )

    print_results(rows, show_excerpts=False)

    output = capsys.readouterr().out
    assert "E9 Rules Seed" in output
    assert "e9-rules-seed" in output
    assert "Private text about the E9 copedent" not in output
    assert "Excerpt:" not in output


def test_print_results_shows_excerpts_only_when_requested(capsys: pytest.CaptureFixture[str]) -> None:
    rows = search_private_sources(
        "What are my common grips?",
        vector_path=Path("corpus-private/vector-stores/chroma"),
        collection_name=DEFAULT_COLLECTION,
        collection=FakeCollection(),
        embed_query=lambda _texts, _model: [[1.0]],
    )

    print_results(rows, show_excerpts=True)

    output = capsys.readouterr().out
    assert "Excerpt:" in output
    assert "Private text about the E9 copedent" in output


def test_search_rejects_empty_query() -> None:
    with pytest.raises(SystemExit, match="query"):
        search_private_sources(
            "",
            vector_path=Path("corpus-private/vector-stores/chroma"),
            collection_name=DEFAULT_COLLECTION,
            collection=FakeCollection(),
            embed_query=lambda _texts, _model: [[1.0]],
        )
