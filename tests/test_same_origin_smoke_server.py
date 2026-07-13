from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from pocketsteel.access_control import DEV_ACCESS_ROLE_ENVIRON
from scripts.serve_answer_smoke import build_app, create_smoke_api_app


def call_app(
    app: Any,
    path: str,
    *,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
    environ_extra: dict[str, str] | None = None,
) -> tuple[str, dict[str, str], bytes]:
    captured: dict[str, Any] = {}
    body = json.dumps(json_body or {}).encode("utf-8") if json_body is not None else b""

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    environ.update(environ_extra or {})
    response_body = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], response_body


def fake_api(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    content_length = int(environ.get("CONTENT_LENGTH") or 0)
    request_payload = json.loads(environ["wsgi.input"].read(content_length).decode("utf-8")) if content_length else {}
    payload = {
        "answer": "Fake source-backed answer. [1]",
        "question": request_payload.get("question", ""),
        "sources": [
            {
                "forumName": "Electronics",
                "title": "Steel King Settings",
                "excerpt": "Steel King settings excerpt.",
                "url": "https://example.test/source",
            }
        ],
        "sections": [{"title": "Answer", "style": "lead", "body": "Fake source-backed answer. [1]"}],
        "warnings": [],
    }
    body = json.dumps(payload).encode("utf-8")
    start_response("200 OK", [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]


def smoke_app(controlled_states: bool = False) -> Any:
    return build_app(api_app=fake_api, ui_root=Path("ui"), controlled_states=controlled_states)


def test_same_origin_server_serves_ui_and_answer_client() -> None:
    status, headers, html = call_app(smoke_app(), "/ui/steel-guitar-rag-mock.html")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b'<script src="answer-client.js?v=melody-exercise-v0-20260710"></script>' in html
    assert b'<script src="pedal-steel-fretboard.js?v=melody-studio-ux-20260710"></script>' in html

    status, headers, studio = call_app(smoke_app(), "/ui/melody-workbench.html")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Turn a phrase into an E9 lesson." in studio
    assert b'<script src="melody-score.js?v=pocket-arranger-20260712-1"></script>' in studio
    assert b'<script src="melody-workbench.js?v=pocket-arranger-20260712-1"></script>' in studio

    status, headers, studio_script = call_app(smoke_app(), "/ui/melody-workbench.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"buildMelodyRequest" in studio_script

    status, headers, score_script = call_app(smoke_app(), "/ui/melody-score.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"score_draft_v1" in score_script

    status, headers, vexflow = call_app(smoke_app(), "/ui/vendor/vexflow-5.0.0.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"VexFlow 5.0.0" in vexflow[:256]

    status, headers, script = call_app(smoke_app(), "/ui/answer-client.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b'const ANSWER_ENDPOINT = "/api/answer";' in script

    status, headers, script = call_app(smoke_app(), "/ui/pedal-steel-fretboard.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"PedalSteelFretboard" in script


def test_same_origin_server_redirects_root_to_ui_shell() -> None:
    status, headers, body = call_app(smoke_app(), "/")

    assert status == "302 Found"
    assert headers["Location"] == "/ui/steel-guitar-rag-mock.html"
    assert b"Redirecting to /ui/steel-guitar-rag-mock.html" in body


def test_same_origin_server_serves_public_fretboard_background() -> None:
    status, headers, body = call_app(smoke_app(), "/brand/pedal-steel-fretboard-background.svg")

    assert status == "200 OK"
    assert headers["Content-Type"] == "image/svg+xml; charset=utf-8"
    assert b'data-layer="headstock-keyhead-shell"' in body
    assert b'data-layer="10-tuning-keys"' in body


def test_same_origin_server_serves_cloudflare_login_brand_png() -> None:
    status, headers, body = call_app(smoke_app(), "/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png")

    assert status == "200 OK"
    assert headers["Content-Type"] == "image/png"
    assert body.startswith(b"\x89PNG\r\n\x1a\n")


def test_same_origin_server_delegates_answer_api() -> None:
    status, headers, body = call_app(
        smoke_app(),
        "/api/answer",
        method="POST",
        json_body={"question": "What are common Fender Steel King settings?"},
    )

    payload = json.loads(body)
    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert payload["sources"][0]["forumName"] == "Electronics"
    assert payload["sources"][0]["title"] == "Steel King Settings"
    assert payload["sources"][0]["excerpt"] == "Steel King settings excerpt."
    assert payload["sources"][0]["url"] == "https://example.test/source"


def test_same_origin_server_keeps_production_answer_api_protected() -> None:
    app = build_app(
        api_app=create_smoke_api_app(
            answer_auth_mode="production",
            auth_provider="cloudflare-access",
            search_index=object(),
        ),
        ui_root=Path("ui"),
    )

    status, headers, body = call_app(
        app,
        "/api/answer",
        method="POST",
        json_body={"question": "How do I play a G chord on the E9?"},
    )

    assert status == "401 Unauthorized"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert json.loads(body) == {"error": "/api/answer requires Cloudflare Access identity"}


def test_same_origin_server_can_control_no_source_and_error_states() -> None:
    app = smoke_app(controlled_states=True)

    status, _, body = call_app(
        app,
        "/api/answer",
        method="POST",
        json_body={"question": "Controlled no-source smoke"},
    )
    payload = json.loads(body)
    assert status == "200 OK"
    assert payload["sources"] == []
    assert payload["answer"] == "No strong source match found for that question."

    status, _, body = call_app(
        app,
        "/api/answer",
        method="POST",
        json_body={"question": "Controlled error smoke"},
    )
    assert status == "503 Service Unavailable"
    assert json.loads(body) == {"error": "controlled smoke error"}


def test_controlled_states_replays_real_answer_body_to_api() -> None:
    status, _, body = call_app(
        smoke_app(controlled_states=True),
        "/api/answer",
        method="POST",
        json_body={"question": "What are common Fender Steel King settings?"},
    )

    payload = json.loads(body)
    assert status == "200 OK"
    assert payload["question"] == "What are common Fender Steel King settings?"
    assert payload["sources"][0]["title"] == "Steel King Settings"


def test_smoke_api_honors_cloudflare_auth_env_for_session(monkeypatch: Any) -> None:
    monkeypatch.setenv("STEEL_RAG_AUTH_PROVIDER", "cloudflare_access")
    monkeypatch.setenv("STEEL_RAG_ANSWER_AUTH_MODE", "production")

    app = create_smoke_api_app(search_index=object())
    status, _, body = call_app(app, "/api/session")

    assert status == "200 OK"
    payload = json.loads(body)
    assert payload == {
        "authenticated": False,
        "role": "anonymous",
        "authProvider": "cloudflare_access",
    }


def test_smoke_api_cli_auth_aliases_report_cloudflare_session(monkeypatch: Any) -> None:
    monkeypatch.delenv("STEEL_RAG_AUTH_PROVIDER", raising=False)
    monkeypatch.delenv("STEEL_RAG_ANSWER_AUTH_MODE", raising=False)

    app = create_smoke_api_app(
        search_index=object(),
        answer_auth_mode="production",
        auth_provider="cloudflare-access",
    )
    status, _, body = call_app(app, "/api/session")

    assert status == "200 OK"
    payload = json.loads(body)
    assert payload["authenticated"] is False
    assert payload["role"] == "anonymous"
    assert payload["authProvider"] == "cloudflare_access"


def test_smoke_api_defaults_to_local_dev_when_auth_env_missing(monkeypatch: Any) -> None:
    monkeypatch.delenv("STEEL_RAG_AUTH_PROVIDER", raising=False)
    monkeypatch.delenv("STEEL_RAG_ANSWER_AUTH_MODE", raising=False)

    app = create_smoke_api_app(search_index=object())
    status, _, body = call_app(
        app,
        "/api/session",
        environ_extra={DEV_ACCESS_ROLE_ENVIRON: "beta_user"},
    )

    assert status == "200 OK"
    payload = json.loads(body)
    assert payload == {
        "authenticated": True,
        "role": "beta_user",
        "authProvider": "local_dev",
    }


def test_smoke_api_ignores_local_dev_mock_in_production_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("STEEL_RAG_AUTH_PROVIDER", "cloudflare_access")
    monkeypatch.setenv("STEEL_RAG_ANSWER_AUTH_MODE", "production")

    app = create_smoke_api_app(search_index=object())
    status, _, body = call_app(
        app,
        "/api/session",
        environ_extra={DEV_ACCESS_ROLE_ENVIRON: "beta_user"},
    )

    assert status == "200 OK"
    payload = json.loads(body)
    assert payload["authenticated"] is False
    assert payload["role"] == "anonymous"
    assert payload["authProvider"] == "cloudflare_access"
