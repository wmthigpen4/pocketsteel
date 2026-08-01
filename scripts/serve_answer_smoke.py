#!/usr/bin/env python3
"""Serve the answer UI and API from one local origin for smoke testing."""

from __future__ import annotations

import argparse
import io
import json
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from steel_guitar_rag.api import SECURITY_RESPONSE_HEADERS, create_app
from steel_guitar_rag.access_control import ANSWER_AUTH_MODE_ENV, AUTH_PROVIDER_ENV, LOCAL_DEV_AUTH_MODE
from steel_guitar_rag.runtime_server import serve_runtime
from steel_guitar_rag.static_files import static_file_response


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiApp = Callable[[dict[str, Any], StartResponse], Iterable[bytes]]


def json_response(start_response: StartResponse, status: str, payload: dict[str, Any]) -> list[bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            *SECURITY_RESPONSE_HEADERS,
        ],
    )
    return [body]


def text_response(start_response: StartResponse, status: str, body: str) -> list[bytes]:
    encoded = body.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(encoded))),
            *SECURITY_RESPONSE_HEADERS,
        ],
    )
    return [encoded]


def redirect_response(start_response: StartResponse, location: str) -> list[bytes]:
    body = f"Redirecting to {location}\n".encode("utf-8")
    start_response(
        "302 Found",
        [
            ("Location", location),
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
            *SECURITY_RESPONSE_HEADERS,
        ],
    )
    return [body]


def read_json_body(environ: dict[str, Any]) -> dict[str, Any]:
    try:
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        content_length = 0
    if content_length <= 0:
        return {}

    try:
        payload = json.loads(environ["wsgi.input"].read(content_length).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def controlled_answer_response(environ: dict[str, Any], start_response: StartResponse) -> list[bytes] | None:
    if environ.get("REQUEST_METHOD") != "POST" or environ.get("PATH_INFO") != "/api/answer":
        return None

    payload = read_json_body(environ)
    question = str(payload.get("question") or "").lower()
    if "controlled no-source" in question or "controlled no source" in question:
        return json_response(
            start_response,
            "200 OK",
            {
                "answer": "No strong source match found for that question.",
                "mode": "ask",
                "sources": [],
                "warnings": ["no strong source match"],
                "sections": [
                    {
                        "title": "Answer",
                        "style": "lead",
                        "body": "No strong source match found for that question.",
                    }
                ],
            },
        )
    if "controlled error" in question:
        return json_response(start_response, "503 Service Unavailable", {"error": "controlled smoke error"})
    return None


def restore_wsgi_input(environ: dict[str, Any], payload: bytes) -> None:
    environ["wsgi.input"] = io.BytesIO(payload)
    environ["CONTENT_LENGTH"] = str(len(payload))


def build_app(
    *,
    api_app: WsgiApp,
    ui_root: Path,
    public_root: Path = Path("public"),
    controlled_states: bool = False,
) -> WsgiApp:
    resolved_ui_root = ui_root.resolve()
    resolved_public_root = public_root.resolve()

    def same_origin_app(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        path = environ.get("PATH_INFO", "") or "/"
        if path.startswith("/api/") or path.startswith("/health/"):
            if controlled_states:
                raw_body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH") or 0))
                restore_wsgi_input(environ, raw_body)
                controlled_response = controlled_answer_response(environ, start_response)
                if controlled_response is not None:
                    return controlled_response
                restore_wsgi_input(environ, raw_body)
            return api_app(environ, start_response)

        if path == "/":
            return redirect_response(start_response, "/ui/steel-guitar-rag-mock.html")
        if path in {"/songs", "/songs/"}:
            path = "/ui/songs.html"
        elif path.startswith("/play/") and len(path.removeprefix("/play/").strip("/")) > 0:
            path = "/ui/play-song.html"
        if path in {"/ui", "/ui/"}:
            path = "/ui/steel-guitar-rag-mock.html"
        if path.startswith("/brand/"):
            file_path = (resolved_public_root / path.removeprefix("/")).resolve()
            return static_file_response(
                environ,
                start_response,
                file_path=file_path,
                root=resolved_public_root,
                security_headers=SECURITY_RESPONSE_HEADERS,
            )
        if not path.startswith("/ui/"):
            return text_response(start_response, "404 Not Found", "not found")

        file_path = (resolved_ui_root / path.removeprefix("/ui/")).resolve()
        return static_file_response(
            environ,
            start_response,
            file_path=file_path,
            root=resolved_ui_root,
            security_headers=SECURITY_RESPONSE_HEADERS,
        )

    return same_origin_app


def resolved_answer_auth_mode(cli_value: str | None) -> str:
    return cli_value or os.environ.get(ANSWER_AUTH_MODE_ENV) or LOCAL_DEV_AUTH_MODE


def resolved_auth_provider(cli_value: str | None) -> str | None:
    return cli_value or os.environ.get(AUTH_PROVIDER_ENV)


def create_smoke_api_app(
    *,
    answer_auth_mode: str | None = None,
    auth_provider: str | None = None,
    search_index: Any | None = None,
) -> WsgiApp:
    return create_app(
        search_index,
        answer_auth_mode=resolved_answer_auth_mode(answer_auth_mode),
        auth_provider=resolved_auth_provider(auth_provider),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--ui-root", type=Path, default=Path("ui"))
    parser.add_argument(
        "--controlled-states",
        action="store_true",
        help="Intercept controlled no-source/error questions for UI state smoke testing.",
    )
    parser.add_argument(
        "--answer-auth-mode",
        choices=["production", "local-dev", "local_dev"],
        default=None,
        help=f"Auth mode for /api/answer. Defaults to ${ANSWER_AUTH_MODE_ENV}, then local_dev for smoke.",
    )
    parser.add_argument(
        "--auth-provider",
        choices=["scaffold", "cloudflare-access", "cloudflare_access"],
        default=None,
        help=f"Auth provider for /api/answer. Defaults to ${AUTH_PROVIDER_ENV}, then scaffold.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    app = build_app(
        api_app=create_smoke_api_app(
            answer_auth_mode=args.answer_auth_mode,
            auth_provider=args.auth_provider,
        ),
        ui_root=args.ui_root,
        controlled_states=args.controlled_states,
    )
    url = f"http://{args.host}:{args.port}/ui/steel-guitar-rag-mock.html"
    def on_ready(_server: object) -> None:
        print(f"Serving same-origin answer smoke UI at {url}", flush=True)
    serve_runtime(args.host, args.port, app, on_ready=on_ready)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
