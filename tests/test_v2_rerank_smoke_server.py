from __future__ import annotations

import io
import json
from typing import Any

from pocketsteel.access_control import DEV_ACCESS_ROLE_ENVIRON
from pocketsteel.chroma_search import SearchResponse
from pocketsteel.cloudflare_access import (
    CLOUDFLARE_ACCESS_JWT_ENVIRON,
    CloudflareAccessClaims,
    CloudflareAccessError,
)
from scripts.serve_v2_rerank_smoke import (
    RerankedSearchIndex,
    build_arg_parser,
    build_rerank_config,
    create_v2_api_app,
    local_preview_url,
)


def call_app(
    app: Any,
    path: str,
    *,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
    environ_extra: dict[str, str] | None = None,
) -> tuple[str, dict[str, str], dict[str, Any]]:
    captured: dict[str, Any] = {}
    body = json.dumps(json_body or {}).encode("utf-8") if json_body is not None else b""

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "REMOTE_ADDR": "127.0.0.1",
    }
    environ.update(environ_extra or {})
    response_body = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], json.loads(response_body)


class FakeV2SearchIndex:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        self.calls.append(
            {
                "query": query,
                "limit": limit,
                "source_system": source_system,
                "forum_name": forum_name,
            }
        )
        return SearchResponse(
            results=[
                {
                    "score": 0.9,
                    "excerpt": "The A pedal and F lever are used together for a major chord position.",
                    "forum_name": "Pedal Steel",
                    "thread_title": "A and F pedal positions",
                    "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
                    "chunk_id": "v2-test-chunk",
                    "post_uid": "v2-test-post",
                }
            ],
            warnings=[],
        )


class FakeCloudflareVerifier:
    def validate(self, token: str, config: Any) -> CloudflareAccessClaims:
        if token != "valid-beta":
            raise CloudflareAccessError("invalid test token")
        return CloudflareAccessClaims(
            email="beta@example.test",
            issuer=config.issuer,
            audience=(config.audience,),
            raw={"email": "beta@example.test", "iss": config.issuer, "aud": config.audience, "sub": "subject:beta"},
            subject="subject:beta",
        )


def configure_cloudflare_access_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_ISSUER", "https://steel.cloudflareaccess.com")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_AUD", "aud-tag")
    monkeypatch.setenv("STEEL_RAG_BETA_USER_EMAILS", "beta@example.test")
    monkeypatch.delenv("STEEL_RAG_ADMIN_EMAILS", raising=False)


def test_v2_local_dev_mode_still_allows_dev_smoke_access(monkeypatch: Any) -> None:
    monkeypatch.delenv("STEEL_RAG_AUTH_PROVIDER", raising=False)
    monkeypatch.delenv("STEEL_RAG_ANSWER_AUTH_MODE", raising=False)
    app = create_v2_api_app(FakeV2SearchIndex(), answer_auth_mode="local_dev", auth_provider="scaffold")

    status, _, payload = call_app(
        app,
        "/api/session",
        environ_extra={DEV_ACCESS_ROLE_ENVIRON: "beta_user"},
    )

    assert status == "200 OK"
    assert payload == {
        "authenticated": True,
        "role": "beta_user",
        "authProvider": "local_dev",
    }
    assert local_preview_url(host="127.0.0.1", port=8781, answer_auth_mode="local_dev").endswith(
        "?access=beta_user"
    )


def test_v2_production_cloudflare_access_session_reports_provider(monkeypatch: Any) -> None:
    configure_cloudflare_access_env(monkeypatch)
    app = create_v2_api_app(
        FakeV2SearchIndex(),
        answer_auth_mode="production",
        auth_provider="cloudflare-access",
        cloudflare_verifier=FakeCloudflareVerifier(),
    )

    status, _, payload = call_app(
        app,
        "/api/session",
        environ_extra={CLOUDFLARE_ACCESS_JWT_ENVIRON: "valid-beta"},
    )

    assert status == "200 OK"
    assert payload == {
        "authenticated": True,
        "role": "beta_user",
        "authProvider": "cloudflare_access",
    }
    assert "email" not in payload
    assert "access=beta_user" not in local_preview_url(
        host="127.0.0.1",
        port=8770,
        answer_auth_mode="production",
    )


def test_v2_production_cloudflare_access_blocks_local_anonymous_answer(monkeypatch: Any) -> None:
    configure_cloudflare_access_env(monkeypatch)
    app = create_v2_api_app(
        FakeV2SearchIndex(),
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        cloudflare_verifier=FakeCloudflareVerifier(),
    )

    status, _, payload = call_app(
        app,
        "/api/answer",
        method="POST",
        json_body={"question": "What does A+F do?"},
    )

    assert status == "401 Unauthorized"
    assert payload == {"error": "request requires Cloudflare Access identity"}


def test_v2_production_cloudflare_access_ignores_dev_role_headers(monkeypatch: Any) -> None:
    configure_cloudflare_access_env(monkeypatch)
    app = create_v2_api_app(
        FakeV2SearchIndex(),
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        cloudflare_verifier=FakeCloudflareVerifier(),
    )

    status, _, payload = call_app(
        app,
        "/api/answer",
        method="POST",
        json_body={"question": "What does A+F do?"},
        environ_extra={DEV_ACCESS_ROLE_ENVIRON: "beta_user"},
    )

    assert status == "401 Unauthorized"
    assert payload == {"error": "request requires Cloudflare Access identity"}


def test_v2_production_cloudflare_access_allows_valid_identity(monkeypatch: Any) -> None:
    configure_cloudflare_access_env(monkeypatch)
    search_index = FakeV2SearchIndex()
    app = create_v2_api_app(
        search_index,
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        cloudflare_verifier=FakeCloudflareVerifier(),
    )

    status, _, payload = call_app(
        app,
        "/api/answer",
        method="POST",
        json_body={"question": "What does A+F do?", "topK": 2},
        environ_extra={CLOUDFLARE_ACCESS_JWT_ENVIRON: "valid-beta"},
    )

    assert status == "200 OK"
    assert payload["sources"][0]["chunkId"] == "v2-test-chunk"
    assert search_index.calls[-1]["limit"] == 2


class FakeBaseSearchIndex:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        self.calls.append(
            {
                "query": query,
                "limit": limit,
                "source_system": source_system,
                "forum_name": forum_name,
            }
        )
        return SearchResponse(
            results=[
                {
                    "score": 0.5,
                    "excerpt": "Use the A pedal and F lever together.",
                    "thread_url": f"https://example.test/{index}",
                    "chunk_id": f"chunk-{index}",
                }
                for index in range(12)
            ],
            warnings=[],
        )


def test_v2_rerank_settings_are_applied_to_retrieval() -> None:
    args = build_arg_parser().parse_args(
        [
            "--candidate-k",
            "11",
            "--min-excerpt-chars",
            "22",
            "--no-dedupe-thread",
            "--question-only-penalty",
            "0.13",
        ]
    )
    config = build_rerank_config(args)
    base = FakeBaseSearchIndex()
    index = RerankedSearchIndex(base, config)

    response = index.search("What does A+F do?", limit=3, source_system="sgf_phpbb_current")

    assert base.calls[-1]["limit"] == 11
    assert base.calls[-1]["source_system"] == "sgf_phpbb_current"
    assert config.min_excerpt_chars == 22
    assert config.dedupe_thread is False
    assert config.question_only_penalty == 0.13
    assert len(response.results) == 3
