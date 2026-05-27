from __future__ import annotations

import io
import json
from typing import Any
from urllib.parse import urlencode

from pocketsteel import chroma_search
from pocketsteel.chroma_search import ChromaSearchIndex
from pocketsteel.api import create_app


def call_app(
    path: str,
    query: dict[str, str] | None = None,
    *,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
    search_index: Any | None = None,
    answer_provider: Any | None = None,
) -> tuple[str, dict[str, str], dict[str, Any]]:
    app = create_app(search_index or fake_search_index(), answer_provider=answer_provider or FakeAnswerProvider())
    captured: dict[str, Any] = {}
    body = json.dumps(json_body or {}).encode("utf-8") if json_body is not None else b""

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": urlencode(query or {}),
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    response_body = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], json.loads(response_body)


class FakeCollection:
    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self.result = result or {
            "ids": [["chroma-1"]],
            "documents": [["Document fallback text should not be needed."]],
            "metadatas": [
                [
                    {
                        "text": "Palm blocking and pick blocking both show up in older forum advice.",
                        "chunk_id": "chunk-1",
                        "post_uid": "p1011",
                        "forum_name": "Pedal Steel",
                        "thread_title": "Blocking practice",
                        "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=101",
                    }
                ]
            ],
            "distances": [[0.25]],
        }
        self.query_kwargs: dict[str, Any] | None = None

    def query(self, **kwargs: Any) -> dict[str, Any]:
        self.query_kwargs = kwargs
        return self.result


class FakeSearchIndex:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def search(self, query: str, **kwargs: Any) -> Any:
        self.calls.append({"query": query, **kwargs})
        return self.response


class FakeAnswerProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def answer(self, request: Any, sources: list[dict[str, Any]]) -> str:
        self.calls.append({"request": request, "sources": sources})
        if request.mode == "gear":
            return "Likely causes: check the cable, volume pedal, amp input, and grounding path. Diagnostic steps: change one thing at a time. [1]"
        if request.mode == "copedent":
            return "Interval-first: treat the change as moving from the 5th toward a 6th or dominant color, then map it to string 6, frets, pedals, and levers. [1]"
        if request.mode == "tab":
            return "I can explain chord tones and pedal purpose from the sources, but I should not generate copyrighted song tab. [1]"
        if request.mode == "practice":
            return "1. Isolate the move. 2. Repeat it slowly. 3. Move it to another fret. [1]"
        return "A source-backed answer grounded in the retrieved forum discussion. [1]"


def fake_search_index(collection: FakeCollection | None = None) -> ChromaSearchIndex:
    return ChromaSearchIndex(
        collection=collection or FakeCollection(),
        embedder=lambda texts, model=None: [[0.1, 0.2, 0.3] for _ in texts],
        model="test-embed",
    )


def required_search_fields(result: dict[str, Any]) -> dict[str, Any]:
    keys = {"score", "excerpt", "forum_name", "thread_title", "thread_url", "chunk_id", "post_uid", "warnings"}
    return {key: result[key] for key in keys}


def test_configured_chroma_path_prefers_environment(monkeypatch: Any, tmp_path: Any) -> None:
    configured = tmp_path / "external-chroma"
    monkeypatch.setenv(chroma_search.CHROMA_PATH_ENV, str(configured))

    assert chroma_search.configured_chroma_path() == configured


def test_configured_chroma_path_allows_explicit_override(monkeypatch: Any, tmp_path: Any) -> None:
    configured = tmp_path / "env-chroma"
    explicit = tmp_path / "explicit-chroma"
    monkeypatch.setenv(chroma_search.CHROMA_PATH_ENV, str(configured))

    assert chroma_search.configured_chroma_path(explicit) == explicit


def test_configured_chroma_path_falls_back_to_app_local(monkeypatch: Any) -> None:
    monkeypatch.delenv(chroma_search.CHROMA_PATH_ENV, raising=False)

    assert chroma_search.configured_chroma_path() == chroma_search.project_path(chroma_search.DEFAULT_CHROMA_PATH)


def test_configured_collection_name_prefers_environment(monkeypatch: Any) -> None:
    monkeypatch.setenv(chroma_search.CHROMA_COLLECTION_ENV, "custom_collection")

    assert chroma_search.configured_collection_name() == "custom_collection"


def test_chroma_search_uses_primary_metadata_fields() -> None:
    collection = FakeCollection()
    response = fake_search_index(collection).search("palm blocking")

    assert collection.query_kwargs == {
        "query_embeddings": [[0.1, 0.2, 0.3]],
        "n_results": 5,
        "include": ["documents", "metadatas", "distances"],
    }
    assert response.warnings == []
    assert required_search_fields(response.results[0]) == {
        "score": 0.8,
        "excerpt": "Palm blocking and pick blocking both show up in older forum advice.",
        "forum_name": "Pedal Steel",
        "thread_title": "Blocking practice",
        "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=101",
        "chunk_id": "chunk-1",
        "post_uid": "p1011",
        "warnings": [],
    }


def test_api_search_returns_query_and_results() -> None:
    status, headers, payload = call_app("/api/search", {"q": "palm blocking"})

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert payload["query"] == "palm blocking"
    assert payload["results"][0]["thread_title"] == "Blocking practice"
    assert payload["warnings"] == []
    assert {
        "score",
        "excerpt",
        "forum_name",
        "thread_title",
        "thread_url",
        "chunk_id",
        "post_uid",
        "warnings",
    }.issubset(payload["results"][0])


def test_chroma_search_handles_metadata_aliases_and_warns_on_fallbacks() -> None:
    collection = FakeCollection(
        {
            "ids": [["chroma-fallback-id"]],
            "documents": [["Document fallback text should not be used."]],
            "metadatas": [
                [
                    {
                        "chunk_text": "A 500K wah pot may not sweep correctly in some pedals.",
                        "post_uids": '["p872666", "p872667"]',
                        "forum_name": "Electronics",
                        "thread_title": "Need some wah wah advice.",
                        "source_url": "https://bb.steelguitarforum.com/viewtopic.php?t=100011",
                    }
                ]
            ],
            "distances": [[0.0]],
        }
    )

    response = fake_search_index(collection).search("wah pot")

    assert response.warnings == []
    assert required_search_fields(response.results[0]) == {
        "score": 1.0,
        "excerpt": "A 500K wah pot may not sweep correctly in some pedals.",
        "forum_name": "Electronics",
        "thread_title": "Need some wah wah advice.",
        "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=100011",
        "chunk_id": "chroma-fallback-id",
        "post_uid": "p872666",
        "warnings": [
            "used Chroma id as chunk_id",
            "used first post_uids item as post_uid",
            "used metadata.chunk_text as text",
            "used source_url as thread_url",
        ],
    }


def test_chroma_search_rejects_results_missing_text_or_url() -> None:
    collection = FakeCollection(
        {
            "ids": [["missing-text", "missing-url"]],
            "documents": [["", "This result has text but no URL."]],
            "metadatas": [[{"thread_url": "https://example.test/thread"}, {"chunk_id": "chunk-without-url"}]],
            "distances": [[0.1, 0.2]],
        }
    )

    response = fake_search_index(collection).search("amp buzz")

    assert response.results == []
    assert response.warnings == [
        "rejected result 0: missing usable text",
        "rejected result 1: missing source URL",
    ]


def test_api_search_empty_query_returns_no_results() -> None:
    status, _, payload = call_app("/api/search", {"q": ""})

    assert status == "200 OK"
    assert payload == {"query": "", "results": [], "warnings": []}


def test_api_answer_returns_frontend_contract() -> None:
    status, headers, payload = call_app(
        "/api/answer",
        method="POST",
        json_body={"question": "cabinet drop compensator", "mode": "ask", "topK": 6},
    )

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert payload["mode"] == "ask"
    assert "source-backed answer" in payload["answer"]
    assert payload["answer"].endswith("[1]")
    assert payload["sources"][0]["title"] == "Blocking practice"
    assert payload["sources"][0]["forumName"] == "Pedal Steel"
    assert payload["sources"][0]["url"] == "https://bb.steelguitarforum.com/viewtopic.php?t=101"
    assert payload["sources"][0]["chunkId"] == "chunk-1"
    assert payload["sources"][0]["postUid"] == "p1011"
    assert payload["warnings"] == []
    assert set(payload["sources"][0]) == {
        "score",
        "excerpt",
        "forumName",
        "title",
        "url",
        "chunkId",
        "postUid",
    }


def test_api_answer_missing_question_returns_validation_error() -> None:
    status, _, payload = call_app("/api/answer", method="POST", json_body={"question": ""})

    assert status == "400 Bad Request"
    assert payload == {"error": "question is required"}


def test_api_answer_empty_retrieval_returns_no_source_response() -> None:
    status, _, payload = call_app(
        "/api/answer",
        method="POST",
        json_body={"question": "does this exist"},
        search_index=FakeSearchIndex({"results": [], "warnings": []}),
    )

    assert status == "200 OK"
    assert payload["answer"] == "No strong source match found in the current corpus for that question."
    assert payload["sources"] == []
    assert "no strong source match" in payload["warnings"]


def test_api_answer_preserves_source_metadata_and_does_not_fake_urls() -> None:
    response = {
        "results": [
            {
                "score": 0.75,
                "excerpt": "Touching the changer can change the ground reference.",
                "forum_name": "Electronics",
                "thread_title": "Grounding a pedal steel",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
                "chunk_id": "chunk-ground",
                "post_uid": "p-ground",
                "source_system": "sgf_phpbb_current",
            }
        ],
        "warnings": [],
    }
    status, _, payload = call_app(
        "/api/answer",
        method="POST",
        json_body={"question": "why does touching the changer reduce hum"},
        search_index=FakeSearchIndex(response),
    )

    assert status == "200 OK"
    assert payload["sources"] == [
        {
            "title": "Grounding a pedal steel",
            "forumName": "Electronics",
            "url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
            "excerpt": "Touching the changer can change the ground reference.",
            "score": 0.75,
            "chunkId": "chunk-ground",
            "postUid": "p-ground",
        }
    ]
    assert payload["sources"][0]["url"].startswith("https://bb.steelguitarforum.com/")


def test_api_answer_passes_filters_and_top_k_to_search() -> None:
    search_index = FakeSearchIndex({"results": [], "warnings": []})
    call_app(
        "/api/answer",
        method="POST",
        json_body={
            "question": "Fender Steel King settings",
            "topK": 9,
            "sourceSystem": "sgf_phpbb_current",
            "forumName": "Electronics",
        },
        search_index=search_index,
    )

    assert search_index.calls[0] == {
        "query": "Fender Steel King settings",
        "limit": 9,
        "source_system": "sgf_phpbb_current",
        "forum_name": "Electronics",
    }


def mode_payload(mode: str) -> dict[str, Any]:
    status, _, payload = call_app(
        "/api/answer",
        method="POST",
        json_body={"question": "mode question", "mode": mode},
    )
    assert status == "200 OK"
    return payload


def test_gear_mode_returns_diagnostic_style_structure() -> None:
    payload = mode_payload("gear")
    assert payload["mode"] == "gear"
    assert "Likely causes" in payload["answer"]
    assert "Diagnostic steps" in payload["answer"]


def test_copedent_mode_preserves_interval_first_language() -> None:
    payload = mode_payload("copedent")
    assert payload["mode"] == "copedent"
    assert "Interval-first" in payload["answer"]
    assert "string 6" in payload["answer"]
    assert "frets, pedals, and levers" in payload["answer"]


def test_tab_mode_does_not_generate_copyrighted_song_tab() -> None:
    payload = mode_payload("tab")
    assert payload["mode"] == "tab"
    assert "should not generate copyrighted song tab" in payload["answer"]


def test_practice_mode_returns_steps() -> None:
    payload = mode_payload("practice")
    assert payload["mode"] == "practice"
    assert "1." in payload["answer"]
    assert "2." in payload["answer"]


def test_api_rejects_unknown_paths() -> None:
    status, _, payload = call_app("/health")

    assert status == "404 Not Found"
    assert payload == {"error": "not found"}
