from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from steel_guitar_rag.access_control import DEV_ACCESS_ROLE_ENVIRON
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
    assert b'<script src="answer-client.js?v=amazing-tablature-product-v1-20260724-2"></script>' in html
    assert b'<script src="account-activity.js?v=plan-activity-20260714-1"></script>' in html
    assert b'<script src="pedal-steel-fretboard-styles.js?v=bubble-contrast-20260724"></script>' in html
    assert b'<script src="pedal-steel-fretboard.js?v=landing-bubble-labels-20260713"></script>' in html
    assert b'<script src="vendor/vexflow-5.0.0.js?v=5.0.0"></script>' in html
    assert b'<script src="melody-score.js?v=updated-score-artwork-20260714-1"></script>' in html
    assert b'<script src="landing-home.js?v=landing-bubble-labels-20260713"></script>' in html
    assert b'<link rel="stylesheet" href="workspace-shell.css?v=play-songs-home-20260801-1">' in html

    status, headers, score_asset = call_app(smoke_app(), "/ui/assets/landing/melody-score.png")
    assert status == "200 OK"
    assert headers["Content-Type"] == "image/png"
    assert score_asset.startswith(b"\x89PNG\r\n\x1a\n")

    status, headers, spotlight_asset = call_app(smoke_app(), "/ui/assets/landing/spotlight.png")
    assert status == "200 OK"
    assert headers["Content-Type"] == "image/png"
    assert spotlight_asset.startswith(b"\x89PNG\r\n\x1a\n")

    status, headers, landing_script = call_app(smoke_app(), "/ui/landing-home.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"mountExplorerPreview" in landing_script

    status, headers, activity_script = call_app(smoke_app(), "/ui/account-activity.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"/api/account/activity" in activity_script

    for asset_name in (
        "pass-ticket.png",
        "fretboard-activity.png",
        "melody-activity.png",
        "lessons-activity.png",
        "brain-activity.png",
        "connected-learning.png",
        "ai-assisted.png",
        "artist-credentials.png",
        "setup-nameplate.png",
        "overview-road-case.png",
    ):
        status, headers, asset = call_app(smoke_app(), f"/ui/assets/backstage/{asset_name}")
        assert status == "200 OK"
        assert headers["Content-Type"] == "image/png"
        assert asset.startswith(b"\x89PNG\r\n\x1a\n")

    status, headers, shell_css = call_app(smoke_app(), "/ui/workspace-shell.css")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/css; charset=utf-8"
    assert b".home-product-grid" in shell_css

    status, headers, sign_fallback = call_app(smoke_app(), "/ui/brand/steel-guitar-rag-landing-fallback-alpha.png")
    assert status == "200 OK"
    assert headers["Content-Type"] == "image/png"
    assert sign_fallback.startswith(b"\x89PNG\r\n\x1a\n")

    status, headers, mobile_sign = call_app(smoke_app(), "/ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png")
    assert status == "200 OK"
    assert headers["Content-Type"] == "image/png"
    assert mobile_sign.startswith(b"\x89PNG\r\n\x1a\n")

    status, headers, sign_video = call_app(smoke_app(), "/ui/brand/steel-guitar-rag-landing-alpha.webm")
    assert status == "200 OK"
    assert headers["Content-Type"] == "video/webm"
    assert sign_video.startswith(b"\x1aE\xdf\xa3")

    status, headers, studio = call_app(smoke_app(), "/ui/melody-workbench.html")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"What do you want to work on?" in studio
    assert b'<script src="melody-score.js?v=chord-aware-harmony-v1"></script>' in studio
    assert b'<script src="song-projects.js?v=amazing-tablature-product-v1-20260724-2"></script>' in studio
    assert b'<script src="melody-workbench.js?v=quick-score-bulk-octave-v2"></script>' in studio

    status, headers, studio_script = call_app(smoke_app(), "/ui/melody-workbench.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"buildMelodyRequest" in studio_script

    status, headers, song_projects_script = call_app(smoke_app(), "/ui/song-projects.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"song_project_v1" in song_projects_script

    for track_name in (
        "amazing-grace-2011-guide.mp3",
        "when-the-saints-preview.mp3",
        "oh-susanna-preview.mp3",
    ):
        status, headers, track = call_app(smoke_app(), f"/ui/assets/song-practice/{track_name}")
        assert status == "200 OK"
        assert headers["Content-Type"] in {"audio/mpeg", "audio/mp3"}
        assert track.startswith(b"ID3")

    status, headers, rights_document = call_app(
        smoke_app(),
        "/ui/assets/song-practice/amazing-grace-2011-guide.RIGHTS.md",
    )
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert b"Kevin MacLeod" in rights_document
    assert b"Creative Commons Attribution 3.0 Unported" in rights_document

    status, headers, songs = call_app(smoke_app(), "/songs")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Starter Songs" in songs
    assert b"My Tracks" in songs

    status, headers, player = call_app(smoke_app(), "/play/amazing-grace-guided")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Current and upcoming chord" in player
    assert b"pedal-steel-fretboard.js" in player

    status, headers, setup = call_app(smoke_app(), "/setup/local-example")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Review Song" in setup
    assert b"practice-reference-validation-v1.js" in setup
    assert b"setup-song-key-regions-v5.js" in setup
    assert b"play-song-key-regions-v1.js" in player
    assert b"play-songs-key-regions-v1.css" in player
    assert b"play-songs-key-regions-v1.css" in setup
    assert b"practice-tools-key-regions-v1.js" in setup

    for asset_path, marker in (
        ("/ui/play-songs.css", b".play-cue-deck"),
        ("/ui/songs.js", b"STEEL_RAG_ANALYSIS_CLIENT"),
        ("/ui/practice-analysis-client.js", b"practice-analysis-worker-seventh-evidence-v5.js"),
        ("/ui/practice-analysis-worker.js", b"ANALYSIS_VERSION = 2"),
        ("/ui/practice-reference-validation.js", b"loadProviderReference"),
        ("/ui/practice-tools.js", b"navigator.storage"),
        ("/ui/play-song.js", b"activeTimelineState"),
    ):
        status, _, asset = call_app(smoke_app(), asset_path)
        assert status == "200 OK"
        assert marker in asset

    status, headers, lessons = call_app(smoke_app(), "/ui/lesson-workbench.html")
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Choose a reviewed path or build a focused lesson" in lessons

    status, headers, lesson_script = call_app(smoke_app(), "/ui/lesson-workbench.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {
        "text/javascript; charset=utf-8",
        "application/javascript; charset=utf-8",
    }
    assert b"renderLesson" in lesson_script

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


def test_same_origin_server_delegates_health_checks() -> None:
    app = build_app(
        api_app=create_smoke_api_app(
            answer_auth_mode="local_dev",
            auth_provider="scaffold",
            search_index=object(),
        ),
        ui_root=Path("ui"),
    )

    live_status, live_headers, live_body = call_app(app, "/health/live")
    ready_status, ready_headers, ready_body = call_app(app, "/health/ready")

    assert live_status == "200 OK"
    assert json.loads(live_body) == {"status": "live"}
    assert ready_status == "200 OK"
    assert json.loads(ready_body) == {"status": "ready"}
    assert live_headers["X-Content-Type-Options"] == "nosniff"
    assert ready_headers["X-Content-Type-Options"] == "nosniff"


def test_same_origin_static_response_supports_etag_gzip_and_immutable_cache() -> None:
    app = smoke_app()
    status, headers, body = call_app(
        app,
        "/ui/e9-fretboard-explorer-loader.js",
        environ_extra={"QUERY_STRING": "v=runtime-test", "HTTP_ACCEPT_ENCODING": "gzip"},
    )

    assert status == "200 OK"
    assert headers["Content-Encoding"] == "gzip"
    assert headers["ETag"].startswith('W/"')
    assert headers["Last-Modified"]
    assert headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert headers["Content-Security-Policy-Report-Only"]
    assert body.startswith(b"\x1f\x8b")

    cached_status, cached_headers, cached_body = call_app(
        app,
        "/ui/e9-fretboard-explorer-loader.js",
        environ_extra={"HTTP_IF_NONE_MATCH": headers["ETag"], "HTTP_ACCEPT_ENCODING": "gzip"},
    )
    assert cached_status == "304 Not Modified"
    assert cached_headers["ETag"] == headers["ETag"]
    assert cached_body == b""


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
    assert json.loads(body) == {"error": "request requires Cloudflare Access identity"}


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
        "features": {"songPractice": True},
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
        "features": {"songPractice": True},
    }


def test_smoke_api_serves_reviewed_and_custom_lessons(monkeypatch: Any) -> None:
    monkeypatch.delenv("STEEL_RAG_AUTH_PROVIDER", raising=False)
    monkeypatch.delenv("STEEL_RAG_ANSWER_AUTH_MODE", raising=False)
    app = create_smoke_api_app(search_index=object())
    auth = {DEV_ACCESS_ROLE_ENVIRON: "beta_user"}

    status, headers, body = call_app(app, "/api/lessons/catalog", environ_extra=auth)
    catalog = json.loads(body)
    assert status == "200 OK"
    assert headers["Cache-Control"] == "no-store"
    assert catalog["schemaVersion"] == "lesson_catalog_v2"
    assert catalog["conceptCount"] >= 60
    assert len(catalog["paths"]) == 5

    status, headers, body = call_app(
        app,
        "/api/lessons/build",
        method="POST",
        json_body={"topic": "pick blocking", "level": "intermediate", "duration": "5_min"},
        environ_extra=auth,
    )
    payload = json.loads(body)
    assert payload["status"] == "ready"
    lesson = payload["lesson"]
    assert status == "200 OK"
    assert headers["Cache-Control"] == "no-store"
    assert lesson["schemaVersion"] == "lesson_v2"
    assert lesson["origin"] == "custom"
    assert len(lesson["exercises"]) == 2

    status, _, body = call_app(
        app,
        "/api/lessons/build",
        method="POST",
        json_body={"topic": "sevenths", "level": "intermediate", "duration": "15_min"},
        environ_extra=auth,
    )
    clarification = json.loads(body)
    assert status == "200 OK"
    assert clarification["status"] == "needs_clarification"
    assert clarification["clarification"]["id"] == "seventh-quality"

    status, _, body = call_app(
        app,
        "/api/lessons/build",
        method="POST",
        json_body={"topic": "teleportation theory", "level": "beginner", "duration": "15_min"},
        environ_extra=auth,
    )
    unavailable = json.loads(body)
    assert status == "200 OK"
    assert unavailable["status"] == "unavailable"


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
