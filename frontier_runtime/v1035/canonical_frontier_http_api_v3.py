#!/usr/bin/env python3
"""Dependency-aware loopback boundary for canonical frontier v1035."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit

from canonical_frontier_degraded_v2 import degraded_response
from canonical_frontier_health_v2 import (
    FrontierHealthState,
    ProviderCallError,
    ProviderGateway,
)
from canonical_frontier_v1034_runtime_candidate import build_v1034_runtime


TOKEN_ENV = "STEEL_RAG_CANONICAL_FRONTIER_TOKEN"
BUNDLE_VERIFIED_ENV = "STEEL_RAG_FRONTIER_BUNDLE_VERIFIED"
MAX_BODY_BYTES = 65_536
WARMUP_QUERY = "How do players adjust a pedal steel split tuning?"


class CanonicalFrontierHttpApplication:
    def __init__(
        self,
        runtime: Any,
        gateway: ProviderGateway,
        health: FrontierHealthState,
        *,
        token: str,
        allow_unauthenticated_loopback: bool = False,
    ) -> None:
        if not token and not allow_unauthenticated_loopback:
            raise ValueError(f"{TOKEN_ENV} is required.")
        self.runtime = runtime
        self.gateway = gateway
        self.health = health
        self.token = token
        self.allow_unauthenticated_loopback = allow_unauthenticated_loopback

    def authorized(self, header: str) -> bool:
        if self.allow_unauthenticated_loopback and not self.token:
            return True
        supplied = header[len("Bearer "):] if header.startswith("Bearer ") else ""
        return bool(supplied) and hmac.compare_digest(supplied, self.token)

    def _error(self, code: str, *, retryable: bool, message: str) -> dict[str, Any]:
        return {"error": {"code": code, "message": message, "retryable": retryable}}

    def handle(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        raw_body: bytes,
    ) -> tuple[int, dict[str, Any]]:
        if path == "/health/live":
            return HTTPStatus.OK, {"status": "live"}
        if path == "/health/ready":
            snapshot = self.health.snapshot()
            return (
                HTTPStatus.OK if snapshot["status"] == "ready" else HTTPStatus.SERVICE_UNAVAILABLE,
                snapshot,
            )
        if path != "/v1/answer":
            return HTTPStatus.NOT_FOUND, self._error(
                "not_found", retryable=False, message="Not found."
            )
        if method != "POST":
            return HTTPStatus.METHOD_NOT_ALLOWED, self._error(
                "method_not_allowed", retryable=False, message="POST is required."
            )
        if not self.authorized(headers.get("authorization", "")):
            return HTTPStatus.UNAUTHORIZED, self._error(
                "unauthorized", retryable=False, message="Authorization is required."
            )
        try:
            question, context = self._parse_request(raw_body)
        except ValueError:
            return HTTPStatus.BAD_REQUEST, self._error(
                "invalid_request", retryable=False, message="The request envelope is invalid."
            )

        request_mode = self.health.request_mode()
        if request_mode == "degraded":
            return self._degraded(question)
        self.gateway.begin_trace()
        try:
            result = self.runtime.answer(question, conversation_context=context)
        except ProviderCallError as exc:
            self.health.open(exc.code)
            print(
                "canonical_frontier_provider_failed "
                f"stage={exc.stage} code={exc.code} status={exc.http_status or 0}",
                file=sys.stderr,
                flush=True,
            )
            return self._degraded(question, provider_trace=self._provider_trace())
        except Exception as exc:
            provider_stages = self.gateway.successful_stages()
            if provider_stages:
                # The request crossed the provider boundary, but the returned
                # structured object failed parsing or a contract check.  That
                # is a synthesis-layer failure, not a local-retrieval outage.
                self.health.open("provider_output_invalid")
                print(
                    "canonical_frontier_provider_output_invalid "
                    f"stages={','.join(provider_stages)} error_type={type(exc).__name__}",
                    file=sys.stderr,
                    flush=True,
                )
                return self._degraded(question, provider_trace=self._provider_trace())
            print(
                f"canonical_frontier_local_failed error_type={type(exc).__name__}",
                file=sys.stderr,
                flush=True,
            )
            return HTTPStatus.SERVICE_UNAVAILABLE, self._error(
                "local_retrieval_unavailable",
                retryable=True,
                message="The local steel-guitar evidence service is temporarily unavailable.",
            )
        provider_trace = self._provider_trace()
        metadata = result.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata["provider_trace"] = provider_trace
        self.health.provider_success(
            self.gateway.successful_stages(),
            was_probe=request_mode == "probe",
        )
        return HTTPStatus.OK, result

    def _provider_trace(self) -> dict[str, Any]:
        summary = getattr(self.gateway, "trace_summary", None)
        if callable(summary):
            return dict(summary())
        return {
            "responses_requests": len(self.gateway.successful_stages()),
            "stages": list(self.gateway.successful_stages()),
            "input_tokens": 0,
            "output_tokens": 0,
            "actual_cost_usd": 0.0,
            "pricing_known": True,
        }

    def _degraded(
        self,
        question: str,
        *,
        provider_trace: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        try:
            result = degraded_response(self.runtime, question)
        except Exception as exc:
            print(
                f"canonical_frontier_degraded_failed error_type={type(exc).__name__}",
                file=sys.stderr,
                flush=True,
            )
            result = None
        if result is None:
            return HTTPStatus.SERVICE_UNAVAILABLE, self._error(
                "no_safe_relevant_evidence",
                retryable=True,
                message="No safe relevant local evidence is available for this question.",
            )
        if provider_trace is not None:
            metadata = result.setdefault("metadata", {})
            if isinstance(metadata, dict):
                metadata["provider_trace"] = provider_trace
        return HTTPStatus.OK, result

    @staticmethod
    def _parse_request(raw_body: bytes) -> tuple[str, list[str]]:
        if len(raw_body) > MAX_BODY_BYTES:
            raise ValueError("request too large")
        try:
            value = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid JSON") from exc
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ValueError("invalid schema")
        question = value.get("question")
        context = value.get("conversation_context") or []
        if (
            not isinstance(question, str)
            or not question.strip()
            or len(question) > 8_000
            or not isinstance(context, list)
            or len(context) > 8
            or any(not isinstance(item, str) or len(item) > 8_000 for item in context)
        ):
            raise ValueError("invalid fields")
        return question, context


def handler_class(application: CanonicalFrontierHttpApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "CanonicalFrontier/3"

        def do_GET(self) -> None:  # noqa: N802
            self._handle(b"")

        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = MAX_BODY_BYTES + 1
            self._handle(self.rfile.read(min(length, MAX_BODY_BYTES + 1)))

        def _handle(self, raw_body: bytes) -> None:
            status, payload = application.handle(
                self.command,
                urlsplit(self.path).path,
                {key.lower(): value for key, value in self.headers.items()},
                raw_body,
            )
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            del format, args

    return Handler


def build_application(*, allow_unauthenticated_loopback: bool = False) -> CanonicalFrontierHttpApplication:
    health = FrontierHealthState(
        cooldown_seconds=float(os.environ.get("STEEL_RAG_FRONTIER_CIRCUIT_COOLDOWN_SECONDS", "30"))
    )
    if os.environ.get(BUNDLE_VERIFIED_ENV) != "1":
        raise RuntimeError("The immutable frontier bundle was not verified by the supervisor.")
    health.mark_local_verified()
    gateway = ProviderGateway()
    runtime = build_v1034_runtime(model_call=gateway)
    try:
        warm_sources, _latency = runtime.retriever.retrieve(WARMUP_QUERY, limit=10)
        warmup_passed = 0 < len(warm_sources) <= 10
    except Exception:
        warmup_passed = False
    health.mark_warmup(warmup_passed)
    if warmup_passed:
        health.run_startup_provider_checks()
    return CanonicalFrontierHttpApplication(
        runtime,
        gateway,
        health,
        token=os.environ.get(TOKEN_ENV, "").strip(),
        allow_unauthenticated_loopback=allow_unauthenticated_loopback,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8771)
    parser.add_argument("--allow-unauthenticated-loopback", action="store_true")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("The canonical frontier may bind only to loopback.")
    application = build_application(
        allow_unauthenticated_loopback=args.allow_unauthenticated_loopback
    )
    server = ThreadingHTTPServer((args.host, args.port), handler_class(application))
    print(f"Canonical frontier v3 listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever(poll_interval=0.25)


if __name__ == "__main__":
    main()
