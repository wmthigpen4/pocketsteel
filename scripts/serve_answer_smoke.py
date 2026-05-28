#!/usr/bin/env python3
"""Serve the answer UI and API from one local origin for smoke testing."""

from __future__ import annotations

import argparse
import io
import json
import mimetypes
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from wsgiref.simple_server import make_server

from pocketsteel.api import create_app
from pocketsteel.access_control import ANSWER_AUTH_MODE_ENV, AUTH_PROVIDER_ENV, LOCAL_DEV_AUTH_MODE


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiApp = Callable[[dict[str, Any], StartResponse], Iterable[bytes]]


def json_response(start_response: StartResponse, status: str, payload: dict[str, Any]) -> list[bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
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
        ],
    )
    return [encoded]


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
                "answer": "No strong source match found in the current corpus for that question.",
                "mode": "ask",
                "sources": [],
                "warnings": ["no strong source match"],
                "sections": [
                    {
                        "title": "Answer",
                        "style": "lead",
                        "body": "No strong source match found in the current corpus for that question.",
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
    controlled_states: bool = False,
) -> WsgiApp:
    resolved_ui_root = ui_root.resolve()

    def same_origin_app(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        path = environ.get("PATH_INFO", "") or "/"
        if path.startswith("/api/"):
            if controlled_states:
                raw_body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH") or 0))
                restore_wsgi_input(environ, raw_body)
                controlled_response = controlled_answer_response(environ, start_response)
                if controlled_response is not None:
                    return controlled_response
                restore_wsgi_input(environ, raw_body)
            return api_app(environ, start_response)

        if path in {"/", "/ui", "/ui/"}:
            path = "/ui/steel-guitar-rag-mock.html"
        if not path.startswith("/ui/"):
            return text_response(start_response, "404 Not Found", "not found")

        file_path = (resolved_ui_root / path.removeprefix("/ui/")).resolve()
        try:
            file_path.relative_to(resolved_ui_root)
        except ValueError:
            return text_response(start_response, "403 Forbidden", "forbidden")
        if not file_path.is_file():
            return text_response(start_response, "404 Not Found", "not found")

        body = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type = f"{content_type}; charset=utf-8"
        start_response("200 OK", [("Content-Type", content_type), ("Content-Length", str(len(body)))])
        return [body]

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
    with make_server(args.host, args.port, app) as server:
        print(f"Serving same-origin answer smoke UI at {url}", flush=True)
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
