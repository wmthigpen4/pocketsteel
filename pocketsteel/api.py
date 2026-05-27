"""Tiny local retrieval API for The Turnaround."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from pocketsteel.answering import (
    AnswerProvider,
    answer_is_no_source,
    build_sections,
    concise_source_cards,
    configured_answer_provider,
    parse_answer_request,
)
from pocketsteel.api_contract import AnswerResponse
from pocketsteel.chroma_search import (
    CHROMA_COLLECTION_ENV,
    CHROMA_PATH_ENV,
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    ChromaSearchIndex,
    SearchResponse,
)


class RetrievalApi:
    def __init__(self, search_index: Any, answer_provider: AnswerProvider | None = None) -> None:
        self.search_index = search_index
        self.answer_provider = configured_answer_provider(answer_provider)

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

        if path == "/api/answer":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            request_payload = self._read_json_body(environ)
            answer_request, error = parse_answer_request(request_payload)
            if error or answer_request is None:
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
            strong_sources = [source for source in search_response.results if float(source.get("score") or 0.0) > 0.0]
            if not strong_sources:
                answer = "No strong source match found in the current corpus for that question."
                sources: list[dict[str, Any]] = []
                warnings.append("no strong source match")
            else:
                answer = self.answer_provider.answer(answer_request, strong_sources)
                sources = [] if answer_is_no_source(answer) else concise_source_cards(strong_sources)
            payload: AnswerResponse = {
                "answer": answer,
                "mode": answer_request.mode,
                "sources": sources,
                "warnings": warnings,
                "sections": build_sections(answer),
            }
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


def create_app(search_index: Any | None = None, answer_provider: AnswerProvider | None = None) -> RetrievalApi:
    return RetrievalApi(search_index or ChromaSearchIndex.from_chroma(), answer_provider=answer_provider)


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    app = create_app(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.chroma,
            collection_name=args.collection,
            model=args.model,
        )
    )
    with make_server(args.host, args.port, app) as server:
        print(f"Serving local retrieval API at http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
