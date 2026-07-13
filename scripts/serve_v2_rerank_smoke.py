#!/usr/bin/env python3
"""Serve the existing UI locally against v2 Chroma with reranked retrieval."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pocketsteel.api import create_app
from pocketsteel.chroma_search import ChromaSearchIndex
from pocketsteel.runtime_server import serve_runtime
from scripts.run_retrieval_ab_eval import RerankConfig
from scripts.run_v2_rerank_answer_eval import RerankedSearchIndex
from scripts.serve_answer_smoke import (
    build_app,
    resolved_answer_auth_mode,
    resolved_auth_provider,
)


DEFAULT_V2_CHROMA_PATH = Path("corpus-v2/vector-stores/chroma")
DEFAULT_V2_COLLECTION = "steel_guitar_unified_v2"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Local bind host. Keep this on 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8781)
    parser.add_argument("--ui-root", type=Path, default=Path("ui"))
    parser.add_argument("--v2-chroma-path", type=Path, default=DEFAULT_V2_CHROMA_PATH)
    parser.add_argument("--v2-collection", default=DEFAULT_V2_COLLECTION)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--min-excerpt-chars", type=int, default=80)
    parser.add_argument("--question-only-penalty", type=float, default=0.12)
    parser.add_argument("--mention-only-penalty", type=float, default=0.20)
    parser.add_argument("--answer-advice-boost", type=float, default=0.04)
    parser.add_argument("--quality-boost", type=float, default=0.04)
    parser.add_argument("--quality-threshold", type=float, default=0.70)
    parser.add_argument("--noise-penalty", type=float, default=0.06)
    parser.add_argument("--noise-threshold", type=float, default=0.60)
    parser.add_argument("--no-dedupe-thread", action="store_true", help="Disable per-thread dedupe for debugging.")
    parser.add_argument(
        "--answer-auth-mode",
        choices=["production", "local-dev", "local_dev"],
        default=None,
        help="Auth mode for /api/answer. Defaults to STEEL_RAG_ANSWER_AUTH_MODE, then local_dev.",
    )
    parser.add_argument(
        "--auth-provider",
        choices=["scaffold", "cloudflare-access", "cloudflare_access"],
        default=None,
        help="Auth provider for /api/answer. Defaults to STEEL_RAG_AUTH_PROVIDER, then scaffold.",
    )
    return parser


def build_rerank_config(args: argparse.Namespace) -> RerankConfig:
    if args.candidate_k <= 0:
        raise SystemExit("--candidate-k must be greater than zero")
    if args.min_excerpt_chars < 0:
        raise SystemExit("--min-excerpt-chars must be zero or greater")
    return RerankConfig(
        candidate_k=args.candidate_k,
        min_excerpt_chars=args.min_excerpt_chars,
        dedupe_thread=not args.no_dedupe_thread,
        question_only_penalty=args.question_only_penalty,
        mention_only_penalty=args.mention_only_penalty,
        answer_advice_boost=args.answer_advice_boost,
        quality_boost=args.quality_boost,
        quality_threshold=args.quality_threshold,
        noise_penalty=args.noise_penalty,
        noise_threshold=args.noise_threshold,
    )


def create_v2_api_app(
    search_index: object,
    *,
    answer_auth_mode: str | None = None,
    auth_provider: str | None = None,
    cloudflare_verifier: object | None = None,
) -> object:
    return create_app(
        search_index,
        answer_auth_mode=resolved_answer_auth_mode(answer_auth_mode),
        auth_provider=resolved_auth_provider(auth_provider),
        cloudflare_verifier=cloudflare_verifier,
    )


def local_preview_url(*, host: str, port: int, answer_auth_mode: str) -> str:
    base_url = f"http://{host}:{port}/ui/steel-guitar-rag-mock.html"
    if answer_auth_mode == "local_dev":
        return f"{base_url}?access=beta_user"
    return base_url


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.host != "127.0.0.1":
        raise SystemExit("v2 smoke server must bind to 127.0.0.1 only")

    answer_auth_mode = resolved_answer_auth_mode(args.answer_auth_mode)
    auth_provider = resolved_auth_provider(args.auth_provider) or "scaffold"
    rerank_config = build_rerank_config(args)
    search_index = RerankedSearchIndex(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.v2_chroma_path,
            collection_name=args.v2_collection,
        ),
        rerank_config,
    )
    api_app = create_v2_api_app(
        search_index,
        answer_auth_mode=answer_auth_mode,
        auth_provider=auth_provider,
    )
    app = build_app(api_app=api_app, ui_root=args.ui_root)
    url = local_preview_url(host=args.host, port=args.port, answer_auth_mode=answer_auth_mode)
    def on_ready(_server: object) -> None:
        print("Serving loopback-only v2 rerank UI.", flush=True)
        print(f"URL: {url}", flush=True)
        print("V2 Chroma path: configured for local process only", flush=True)
        print(f"V2 collection: {args.v2_collection}", flush=True)
        print(f"Answer auth mode: {answer_auth_mode}", flush=True)
        print(f"Auth provider: {auth_provider}", flush=True)
        print("This does not change app config, DNS, tunnel routing, or Chroma stores.", flush=True)
    serve_runtime(args.host, args.port, app, on_ready=on_ready)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
