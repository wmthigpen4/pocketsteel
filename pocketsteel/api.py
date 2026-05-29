"""Tiny local retrieval API for Steel Guitar RAG."""

from __future__ import annotations

import argparse
import hashlib
import logging
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from pocketsteel.answering import (
    AnswerProvider,
    answer_is_no_source,
    build_sections,
    concise_source_cards,
    configured_answer_provider,
    final_answer_quality_gate,
    parse_answer_request,
)
from pocketsteel.access_control import (
    AnswerAuthMode,
    AuthProvider,
    authorize_answer_request,
    configured_answer_auth_mode,
    configured_auth_provider,
    normalize_answer_auth_mode,
    normalize_auth_provider,
)
from pocketsteel.answer_usage import InMemoryAnswerRateLimiter, answer_rate_limit_key
from pocketsteel.api_contract import AnswerResponse
from pocketsteel.answer_contracts import enforce_answer_contract, infer_contract_intent
from pocketsteel.chroma_search import (
    CHROMA_COLLECTION_ENV,
    CHROMA_PATH_ENV,
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    ChromaSearchIndex,
    SearchResponse,
)
from pocketsteel.curated_answers import (
    CURATED_FACT_WEAK_WARNING,
    WEAK_RETRIEVAL_WARNING,
    lookup_curated_answer,
    retrieval_looks_weak_for_curated,
)
from pocketsteel.rag_guardrails import sanitize_retrieved_sources
from pocketsteel.rag_guardrails import is_injection_like

LOGGER = logging.getLogger(__name__)


class RetrievalApi:
    def __init__(
        self,
        search_index: Any,
        answer_provider: AnswerProvider | None = None,
        *,
        answer_auth_mode: AnswerAuthMode | None = None,
        auth_provider: AuthProvider | None = None,
        cloudflare_verifier: Any = None,
        answer_rate_limiter: InMemoryAnswerRateLimiter | None = None,
    ) -> None:
        self.search_index = search_index
        self.answer_provider = configured_answer_provider(answer_provider)
        self.answer_auth_mode = normalize_answer_auth_mode(answer_auth_mode or configured_answer_auth_mode())
        self.auth_provider = normalize_auth_provider(auth_provider or configured_auth_provider())
        self.cloudflare_verifier = cloudflare_verifier
        self.answer_rate_limiter = answer_rate_limiter or InMemoryAnswerRateLimiter.from_env()
        self.answer_request_log: list[dict[str, Any]] = []

    def __call__(self, environ: dict[str, Any], start_response: Any) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "")

        if path == "/api/search":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            params = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
            query = params.get("q", [""])[0]
            search_response = self._search(query)
            payload = {
                "query": query,
                "results": search_response.results,
                "warnings": search_response.warnings,
            }
            return self._json_response(start_response, "200 OK", payload)

        if path == "/api/session":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            access = authorize_answer_request(
                environ,
                self.answer_auth_mode,
                self.auth_provider,
                self.cloudflare_verifier,
            )
            auth_provider = "cloudflare_access" if self.auth_provider == "cloudflare_access" and self.answer_auth_mode != "local_dev" else "local_dev"
            payload = {
                "authenticated": access.allowed,
                "role": access.role if access.allowed else "anonymous",
                "authProvider": auth_provider,
            }
            return self._json_response(start_response, "200 OK", payload)

        if path == "/api/answer":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            request_payload = self._read_json_body(environ)
            access = authorize_answer_request(
                environ,
                self.answer_auth_mode,
                self.auth_provider,
                self.cloudflare_verifier,
            )
            if not access.allowed:
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="blocked",
                    authorized=False,
                    error_status=access.status,
                )
                return self._json_response(start_response, access.status, {"error": access.error})

            identity_key = self._identity_key(access.identity_email)
            rate_key = answer_rate_limit_key(environ, access.role, identity_key=identity_key)
            rate_limit = self.answer_rate_limiter.check(rate_key)
            if not rate_limit.allowed:
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="rate_limited",
                    authorized=True,
                    error_status="429 Too Many Requests",
                )
                return self._json_response(
                    start_response,
                    "429 Too Many Requests",
                    {"error": rate_limit.error, "retryAfterSeconds": rate_limit.retry_after_seconds},
                )

            answer_request, error = parse_answer_request(request_payload)
            if error or answer_request is None:
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    error_status="400 Bad Request",
                )
                return self._json_response(start_response, "400 Bad Request", {"error": error or "invalid request"})

            source_system = self._optional_string(request_payload.get("sourceSystem") or request_payload.get("source_system"))
            forum_name = self._optional_string(request_payload.get("forumName") or request_payload.get("forum_name"))
            search_response = self._search(
                answer_request.question,
                limit=answer_request.top_k,
                source_system=source_system,
                forum_name=forum_name,
            )
            warnings = list(search_response.warnings)
            user_prompt_injection = is_injection_like(answer_request.question)
            if user_prompt_injection:
                warnings.append("prompt-injection-like text ignored")
            strong_sources = [source for source in search_response.results if float(source.get("score") or 0.0) > 0.0]
            sanitized = sanitize_retrieved_sources(strong_sources)
            warnings.extend(sanitized.warnings)
            strong_sources = sanitized.sources
            curated_answer = lookup_curated_answer(answer_request.question, strong_sources)
            contract_intent = infer_contract_intent(answer_request.question, answer_request.mode)
            if curated_answer is not None:
                answer = curated_answer.answer
                contract_intent = curated_answer.intent
                if curated_answer.intent == "curated_fact_source_check":
                    warnings.append(CURATED_FACT_WEAK_WARNING)
                if retrieval_looks_weak_for_curated(answer_request.question, curated_answer, strong_sources):
                    warnings.append(WEAK_RETRIEVAL_WARNING)
                if answer_is_no_source(answer):
                    sources = []
                    warnings.append("no strong source match")
                else:
                    sources = concise_source_cards(strong_sources)
            elif user_prompt_injection:
                answer = (
                    "I can’t follow prompt-injection instructions. "
                    "Ask a steel-guitar question and I’ll answer from the available sources."
                )
                sources = concise_source_cards(strong_sources)
            elif not strong_sources:
                answer = "No strong source match found for that question."
                sources: list[dict[str, Any]] = []
                warnings.append("no strong source match")
            else:
                answer = self.answer_provider.answer(answer_request, strong_sources)
                if answer_is_no_source(answer):
                    sources = []
                    warnings.append("no strong source match")
                else:
                    sources = concise_source_cards(strong_sources)
            final_answer = final_answer_quality_gate(answer, answer_request.question)
            contract_validation = enforce_answer_contract(final_answer, contract_intent)
            if contract_validation.violations and contract_validation.answer != final_answer:
                warnings.append(f"answer contract enforced: {contract_validation.intent}")
            final_answer = contract_validation.answer
            payload: AnswerResponse = {
                "answer": final_answer,
                "mode": answer_request.mode,
                "sources": sources,
                "warnings": warnings,
                "sections": build_sections(final_answer),
            }
            self._log_answer_attempt(
                request_payload,
                role=access.role,
                identity_email=access.identity_email,
                access_status="authorized",
                authorized=True,
                source_count=len(sources),
                warning_count=len(warnings),
            )
            return self._json_response(start_response, "200 OK", payload)

        else:
            return self._json_response(start_response, "404 Not Found", {"error": "not found"})

    def _search(
        self,
        query: str,
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        try:
            response = self.search_index.search(
                query,
                limit=limit,
                source_system=source_system,
                forum_name=forum_name,
            )
        except TypeError:
            response = self.search_index.search(query)
        if isinstance(response, SearchResponse):
            return response
        if isinstance(response, dict):
            return SearchResponse(
                results=list(response.get("results") or []),
                warnings=list(response.get("warnings") or []),
            )
        return SearchResponse(results=list(response or []), warnings=[])

    @staticmethod
    def _read_json_body(environ: dict[str, Any]) -> dict[str, Any]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            content_length = 0
        if content_length <= 0:
            return {}

        raw_body = environ["wsgi.input"].read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _log_answer_attempt(
        self,
        request_payload: dict[str, Any],
        *,
        role: str,
        identity_email: str = "",
        access_status: str,
        authorized: bool,
        source_count: int | None = None,
        warning_count: int = 0,
        error_status: str = "",
    ) -> None:
        question = str(request_payload.get("question") or "")
        mode = str(request_payload.get("mode") or "ask")
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "identityKey": self._identity_key(identity_email),
            "accessStatus": access_status,
            "authorized": authorized,
            "blocked": not authorized or bool(error_status),
            "questionLength": len(question),
            "mode": mode,
            "sourceCount": source_count,
            "warningCount": warning_count,
            "errorStatus": error_status,
        }
        self.answer_request_log.append(event)
        LOGGER.info("answer request event: %s", json.dumps(event, sort_keys=True))

    @staticmethod
    def _identity_key(identity_email: str = "") -> str:
        normalized = str(identity_email or "").strip().lower()
        if not normalized:
            return ""
        digest = hashlib.sha256(f"steel-rag-access:{normalized}".encode("utf-8")).hexdigest()
        return f"email_sha256:{digest}"

    @staticmethod
    def _json_response(start_response: Any, status: str, payload: dict[str, Any]) -> list[bytes]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]


def create_app(
    search_index: Any | None = None,
    answer_provider: AnswerProvider | None = None,
    *,
    answer_auth_mode: AnswerAuthMode | None = None,
    auth_provider: AuthProvider | None = None,
    cloudflare_verifier: Any = None,
    answer_rate_limiter: InMemoryAnswerRateLimiter | None = None,
) -> RetrievalApi:
    return RetrievalApi(
        search_index or ChromaSearchIndex.from_chroma(),
        answer_provider=answer_provider,
        answer_auth_mode=answer_auth_mode,
        auth_provider=auth_provider,
        cloudflare_verifier=cloudflare_verifier,
        answer_rate_limiter=answer_rate_limiter,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local API server.")
    parser.add_argument("--port", type=int, default=8765, help="Port for the local API server.")
    parser.add_argument(
        "--chroma",
        default=None,
        help=f"Existing Chroma index path. Defaults to ${CHROMA_PATH_ENV} or {DEFAULT_CHROMA_PATH}.",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help=f"Existing Chroma collection name. Defaults to ${CHROMA_COLLECTION_ENV} or {DEFAULT_COLLECTION_NAME}.",
    )
    parser.add_argument("--model", default=None, help="Local embedding model for query embedding.")
    parser.add_argument(
        "--answer-auth-mode",
        choices=["production", "local-dev", "local_dev"],
        default=None,
        help="Auth scaffold mode for /api/answer. Defaults to STEEL_RAG_ANSWER_AUTH_MODE or production.",
    )
    parser.add_argument(
        "--auth-provider",
        choices=["scaffold", "cloudflare-access", "cloudflare_access"],
        default=None,
        help="Auth provider for production /api/answer requests. Defaults to STEEL_RAG_AUTH_PROVIDER or scaffold.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    app = create_app(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.chroma,
            collection_name=args.collection,
            model=args.model,
        ),
        answer_auth_mode=args.answer_auth_mode,
        auth_provider=args.auth_provider,
    )
    with make_server(args.host, args.port, app) as server:
        print(f"Serving local retrieval API at http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
