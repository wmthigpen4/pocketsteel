from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pocketsteel.access_control import DEV_ACCESS_ROLE_ENVIRON
from pocketsteel.api import create_app
from pocketsteel.cloudflare_access import CLOUDFLARE_ACCESS_JWT_ENVIRON
from pocketsteel.retrieval_modes import RetrievalMode, RetrievalModeConfig
from tests.test_api_search import FakeCloudflareVerifier
import pytest


class FakeSearchIndex:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"query": query, **kwargs})
        return self.response


class FakeAnswerProvider:
    def answer(self, request: Any, sources: list[dict[str, Any]]) -> str:
        titles = ", ".join(source.get("thread_title") or "source" for source in sources)
        return f"Answer using: {titles}"


def retrieval_config(
    mode: str = "sgf_only",
    *,
    private_enabled: bool = False,
    debug: bool = False,
) -> RetrievalModeConfig:
    return RetrievalModeConfig(
        requested_mode=RetrievalMode(mode),
        private_sources_enabled=private_enabled,
        sgf_chroma_path=Path("corpus-v2/vector-stores/chroma"),
        sgf_collection="steel_guitar_unified_v2",
        private_chroma_path=Path("corpus-private/vector-stores/chroma"),
        private_collection="steel_guitar_private_sources_v1",
        expose_debug_metadata=debug,
    )


def sgf_response() -> dict[str, Any]:
    return {
        "results": [
            {
                "score": 0.82,
                "excerpt": "Common E9 grips include 3-4-5, 4-5-6, 5-6-8, and 6-8-10.",
                "source_system": "sgf_phpbb_current",
                "forum_name": "Pedal Steel",
                "thread_title": "Common E9 grips",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=100",
                "chunk_id": "sgf-grips-1",
                "post_uid": "p-sgf-grips",
                "source_kind": "forum_thread_chunk",
                "warnings": [],
            }
        ],
        "warnings": [],
    }


def private_response(answer_quote_allowed: str = "limited") -> dict[str, Any]:
    return {
        "results": [
            {
                "score": 0.95,
                "excerpt": "Private profile says the user's common grips are 3-4-5 and 5-6-8.",
                "source_system": "personal_rules_note",
                "forum_name": "Private Sources",
                "thread_title": "User E9 Copedent Profile",
                "thread_url": "source-inbox/rules/user-e9-copedent.txt",
                "chunk_id": "private:user-e9:doc-0:chunk-0001",
                "post_uid": "private:user-e9:doc-0:chunk-0001",
                "source_kind": "private_source_chunk",
                "warnings": [],
                "visibility": "private",
                "source_id": "user-e9-copedent-profile",
                "source_path": "source-inbox/rules/user-e9-copedent.txt",
                "provenance_status": "reviewed",
                "answer_quote_allowed": answer_quote_allowed,
            }
        ],
        "warnings": [],
    }


def call_answer(
    *,
    question: str = "What are my common grips?",
    query: dict[str, str] | None = None,
    search_index: FakeSearchIndex | None = None,
    private_search_index: FakeSearchIndex | None = None,
    config: RetrievalModeConfig | None = None,
    access_role: str | None = "beta_user",
    answer_auth_mode: str = "local_dev",
    auth_provider: str = "scaffold",
    cloudflare_token: str | None = None,
    cloudflare_verifier: Any = None,
) -> tuple[str, dict[str, Any]]:
    app = create_app(
        search_index or FakeSearchIndex(sgf_response()),
        answer_provider=FakeAnswerProvider(),
        answer_auth_mode=answer_auth_mode,
        auth_provider=auth_provider,
        cloudflare_verifier=cloudflare_verifier,
        private_search_index=private_search_index or FakeSearchIndex(private_response()),
        retrieval_config=config,
    )
    body = json.dumps({"question": question, "mode": "ask", "topK": 6}).encode("utf-8")
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status

    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/answer",
        "QUERY_STRING": urlencode(query or {}),
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    if access_role is not None:
        environ[DEV_ACCESS_ROLE_ENVIRON] = access_role
    if cloudflare_token is not None:
        environ[CLOUDFLARE_ACCESS_JWT_ENVIRON] = cloudflare_token
    payload = json.loads(b"".join(app(environ, start_response)))
    return captured["status"], payload


def test_default_api_answer_remains_sgf_only_private_disabled() -> None:
    sgf_index = FakeSearchIndex(sgf_response())
    private_index = FakeSearchIndex(private_response())

    status, payload = call_answer(search_index=sgf_index, private_search_index=private_index)

    assert status == "200 OK"
    assert sgf_index.calls
    assert private_index.calls == []
    assert payload["sources"][0]["title"] == "Common E9 grips"


def test_api_answer_private_disabled_even_when_mode_is_hybrid() -> None:
    sgf_index = FakeSearchIndex(sgf_response())
    private_index = FakeSearchIndex(private_response())

    status, payload = call_answer(
        search_index=sgf_index,
        private_search_index=private_index,
        config=retrieval_config("hybrid_private_first", private_enabled=False),
    )

    assert status == "200 OK"
    assert sgf_index.calls
    assert private_index.calls == []
    assert payload["sources"][0]["title"] == "Common E9 grips"


def test_anonymous_local_dev_answer_cannot_use_private_sources() -> None:
    sgf_index = FakeSearchIndex(sgf_response())
    private_index = FakeSearchIndex(private_response())

    status, payload = call_answer(
        search_index=sgf_index,
        private_search_index=private_index,
        config=retrieval_config("hybrid_private_first", private_enabled=True),
        access_role=None,
    )

    assert status == "401 Unauthorized"
    assert payload == {"error": "/api/answer requires authenticated beta_user or admin access"}
    assert sgf_index.calls == []
    assert private_index.calls == []


def test_production_cloudflare_answer_ignores_dev_query_and_mock_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_ISSUER", "https://steel.cloudflareaccess.com")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_AUD", "aud-tag")
    monkeypatch.setenv("STEEL_RAG_BETA_USER_EMAILS", "beta@example.test")
    sgf_index = FakeSearchIndex(sgf_response())
    private_index = FakeSearchIndex(private_response())

    status, payload = call_answer(
        query={"access": "beta_user"},
        search_index=sgf_index,
        private_search_index=private_index,
        config=retrieval_config("hybrid_private_first", private_enabled=True),
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        cloudflare_verifier=FakeCloudflareVerifier(),
        access_role="beta_user",
    )

    assert status == "401 Unauthorized"
    assert payload == {"error": "/api/answer requires Cloudflare Access identity"}
    assert sgf_index.calls == []
    assert private_index.calls == []


def test_beta_hybrid_answer_can_include_private_source_cards() -> None:
    private_index = FakeSearchIndex(private_response())

    status, payload = call_answer(
        private_search_index=private_index,
        config=retrieval_config("hybrid_private_first", private_enabled=True),
        access_role="beta_user",
    )

    assert status == "200 OK"
    assert private_index.calls
    assert payload["sources"][0]["title"] == "User E9 Copedent Profile"
    assert payload["sources"][0]["source_system"] == "personal_rules_note"
    assert payload["sources"][0]["visibility"] == "private"
    assert payload["sources"][0]["source_id"] == "user-e9-copedent-profile"
    assert payload["sources"][0]["provenance_status"] == "reviewed"
    assert payload["sources"][0]["answer_quote_allowed"] == "limited"


def test_private_source_card_contract_includes_private_metadata() -> None:
    status, payload = call_answer(
        config=retrieval_config("private_only", private_enabled=True),
        access_role="beta_user",
    )

    assert status == "200 OK"
    card = payload["sources"][0]
    assert {
        "source_system",
        "visibility",
        "source_id",
        "title",
        "provenance_status",
        "answer_quote_allowed",
    } <= set(card)
    assert card["visibility"] == "private"


def test_rules_layer_answer_wins_over_private_source_for_stable_e9_basics() -> None:
    status, payload = call_answer(
        question="What does A+F do?",
        config=retrieval_config("hybrid_private_first", private_enabled=True),
        access_role="beta_user",
    )

    assert status == "200 OK"
    assert "A pedal" in payload["answer"]
    assert "F lever" in payload["answer"]
    assert "major" in payload["answer"].lower()
    assert "Private profile says" not in payload["answer"]


def test_limited_private_quoting_is_not_copied_into_answer_body() -> None:
    private_index = FakeSearchIndex(private_response(answer_quote_allowed="limited"))

    status, payload = call_answer(
        private_search_index=private_index,
        config=retrieval_config("private_only", private_enabled=True),
        access_role="beta_user",
    )

    assert status == "200 OK"
    assert "Private profile says" not in payload["answer"]
    assert "user's common grips are 3-4-5 and 5-6-8" not in payload["answer"]


def test_private_answer_false_quote_permission_blanks_source_excerpt() -> None:
    private_index = FakeSearchIndex(private_response(answer_quote_allowed="false"))

    status, payload = call_answer(
        private_search_index=private_index,
        config=retrieval_config("private_only", private_enabled=True),
        access_role="beta_user",
    )

    assert status == "200 OK"
    assert payload["sources"][0]["answer_quote_allowed"] == "false"
    assert payload["sources"][0]["excerpt"] == ""


def test_production_cloudflare_valid_beta_can_use_private_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_ISSUER", "https://steel.cloudflareaccess.com")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_AUD", "aud-tag")
    monkeypatch.setenv("STEEL_RAG_BETA_USER_EMAILS", "beta@example.test")
    private_index = FakeSearchIndex(private_response())

    status, payload = call_answer(
        private_search_index=private_index,
        config=retrieval_config("hybrid_private_first", private_enabled=True),
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        cloudflare_token="valid-beta",
        cloudflare_verifier=FakeCloudflareVerifier(),
        access_role=None,
    )

    assert status == "200 OK"
    assert private_index.calls
    assert payload["sources"][0]["visibility"] == "private"


def test_unauthorized_answer_never_exposes_private_excerpt_or_metadata() -> None:
    status, payload = call_answer(
        query={"access": "anonymous"},
        config=retrieval_config("hybrid_private_first", private_enabled=True),
        access_role=None,
    )

    assert status == "401 Unauthorized"
    text = json.dumps(payload)
    assert "User E9 Copedent Profile" not in text
    assert "user-e9-copedent-profile" not in text
    assert "Private profile says" not in text
