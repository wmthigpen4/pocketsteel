"""Command-line bootstrap for the retrieval API process."""

from __future__ import annotations

import argparse
from pathlib import Path

from pocketsteel.api import create_app
from pocketsteel.chroma_search import (
    CHROMA_COLLECTION_ENV,
    CHROMA_PATH_ENV,
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    ChromaSearchIndex,
)
from pocketsteel.retrieval_modes import (
    ENABLE_PRIVATE_SOURCES_ENV,
    PRIVATE_CHROMA_PATH_ENV,
    PRIVATE_COLLECTION_ENV,
    RETRIEVAL_DEBUG_ENV,
    RETRIEVAL_MODE_ENV,
    RetrievalModeConfig,
    configured_retrieval_mode_config,
    normalize_retrieval_mode,
)
from pocketsteel.runtime_server import serve_runtime


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve the steel-guitar retrieval API.")
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
        help="Auth mode. Defaults to STEEL_RAG_ANSWER_AUTH_MODE or production.",
    )
    parser.add_argument(
        "--auth-provider",
        choices=["scaffold", "cloudflare-access", "cloudflare_access"],
        default=None,
        help="Production auth provider. Defaults to STEEL_RAG_AUTH_PROVIDER.",
    )
    parser.add_argument(
        "--retrieval-mode",
        default=None,
        help=f"Search retrieval mode. Defaults to ${RETRIEVAL_MODE_ENV} or sgf_only.",
    )
    parser.add_argument(
        "--enable-private-sources",
        action="store_true",
        help=f"Allow private-source modes. Defaults to ${ENABLE_PRIVATE_SOURCES_ENV}=false.",
    )
    parser.add_argument(
        "--private-chroma",
        default=None,
        help=f"Private Chroma path. Defaults to ${PRIVATE_CHROMA_PATH_ENV} or corpus-private/vector-stores/chroma.",
    )
    parser.add_argument(
        "--private-collection",
        default=None,
        help=f"Private collection. Defaults to ${PRIVATE_COLLECTION_ENV} or steel_guitar_private_sources_v1.",
    )
    parser.add_argument(
        "--retrieval-debug",
        action="store_true",
        help=f"Expose retrieval metadata to admin/dev roles. Defaults to ${RETRIEVAL_DEBUG_ENV}=false.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    env_config = configured_retrieval_mode_config()
    retrieval_config = RetrievalModeConfig(
        requested_mode=(
            env_config.requested_mode
            if args.retrieval_mode is None
            else normalize_retrieval_mode(args.retrieval_mode)
        ),
        private_sources_enabled=args.enable_private_sources or env_config.private_sources_enabled,
        sgf_chroma_path=env_config.sgf_chroma_path,
        sgf_collection=env_config.sgf_collection,
        private_chroma_path=(
            env_config.private_chroma_path if args.private_chroma is None else Path(args.private_chroma)
        ),
        private_collection=args.private_collection or env_config.private_collection,
        expose_debug_metadata=args.retrieval_debug or env_config.expose_debug_metadata,
    )
    app = create_app(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.chroma,
            collection_name=args.collection,
            model=args.model,
        ),
        answer_auth_mode=args.answer_auth_mode,
        auth_provider=args.auth_provider,
        retrieval_config=retrieval_config,
    )

    def on_ready(_server: object) -> None:
        print(f"Serving local retrieval API at http://{args.host}:{args.port}")

    serve_runtime(args.host, args.port, app, on_ready=on_ready)
    return 0
