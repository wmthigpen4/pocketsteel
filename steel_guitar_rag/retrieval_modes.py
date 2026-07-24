"""Retrieval mode configuration scaffold.

This module intentionally does not execute retrieval. It gives Steel Guitar RAG a
stable vocabulary for future SGF/private hybrid routing while keeping the
default behavior SGF-only and private-source-disabled.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping


RETRIEVAL_MODE_ENV = "STEEL_RAG_RETRIEVAL_MODE"
ENABLE_PRIVATE_SOURCES_ENV = "STEEL_RAG_ENABLE_PRIVATE_SOURCES"
PRIVATE_CHROMA_PATH_ENV = "STEEL_RAG_PRIVATE_CHROMA_PATH"
PRIVATE_COLLECTION_ENV = "STEEL_RAG_PRIVATE_CHROMA_COLLECTION"
SGF_V2_CHROMA_PATH_ENV = "STEEL_RAG_SGF_V2_CHROMA_PATH"
SGF_V2_COLLECTION_ENV = "STEEL_RAG_SGF_V2_COLLECTION"
RETRIEVAL_DEBUG_ENV = "STEEL_RAG_RETRIEVAL_DEBUG"

DEFAULT_SGF_V2_CHROMA_PATH = Path("corpus-v2/vector-stores/chroma")
DEFAULT_SGF_V2_COLLECTION = "steel_guitar_unified_v2"
DEFAULT_PRIVATE_CHROMA_PATH = Path("corpus-private/vector-stores/chroma")
DEFAULT_PRIVATE_COLLECTION = "steel_guitar_private_sources_v1"

PRIVATE_CAPABLE_ROLES = {"beta_user", "private_preview", "admin", "developer", "dev"}


class RetrievalMode(StrEnum):
    SGF_ONLY = "sgf_only"
    PRIVATE_ONLY = "private_only"
    HYBRID_PRIVATE_FIRST = "hybrid_private_first"
    HYBRID_SGF_FIRST = "hybrid_sgf_first"
    RULES_ONLY = "rules_only"
    CURATED_ONLY = "curated_only"


@dataclass(frozen=True)
class RetrievalModeConfig:
    requested_mode: RetrievalMode
    private_sources_enabled: bool
    sgf_chroma_path: Path
    sgf_collection: str
    private_chroma_path: Path
    private_collection: str
    expose_debug_metadata: bool = False


@dataclass(frozen=True)
class RetrievalPlan:
    selected_mode: RetrievalMode
    use_sgf: bool
    use_private: bool
    source_order: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    expose_debug_metadata: bool = False


def env_flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def normalize_retrieval_mode(value: str | RetrievalMode | None) -> RetrievalMode:
    if isinstance(value, RetrievalMode):
        return value
    if value in (None, ""):
        return RetrievalMode.SGF_ONLY
    normalized = str(value).strip().lower().replace("-", "_")
    try:
        return RetrievalMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in RetrievalMode)
        raise ValueError(f"Unknown retrieval mode {value!r}; expected one of: {allowed}") from exc


def configured_retrieval_mode_config(env: Mapping[str, str] | None = None) -> RetrievalModeConfig:
    env = env or os.environ
    return RetrievalModeConfig(
        requested_mode=normalize_retrieval_mode(env.get(RETRIEVAL_MODE_ENV)),
        private_sources_enabled=env_flag(env.get(ENABLE_PRIVATE_SOURCES_ENV)),
        sgf_chroma_path=Path(env.get(SGF_V2_CHROMA_PATH_ENV) or DEFAULT_SGF_V2_CHROMA_PATH),
        sgf_collection=env.get(SGF_V2_COLLECTION_ENV) or DEFAULT_SGF_V2_COLLECTION,
        private_chroma_path=Path(env.get(PRIVATE_CHROMA_PATH_ENV) or DEFAULT_PRIVATE_CHROMA_PATH),
        private_collection=env.get(PRIVATE_COLLECTION_ENV) or DEFAULT_PRIVATE_COLLECTION,
        expose_debug_metadata=env_flag(env.get(RETRIEVAL_DEBUG_ENV)),
    )


def private_sources_allowed(role: str | None, config: RetrievalModeConfig) -> bool:
    if not config.private_sources_enabled:
        return False
    normalized_role = (role or "anonymous").strip().lower()
    return normalized_role in PRIVATE_CAPABLE_ROLES


def retrieval_plan_for_role(
    role: str | None,
    *,
    requested_mode: RetrievalMode | str | None = None,
    config: RetrievalModeConfig | None = None,
) -> RetrievalPlan:
    config = config or configured_retrieval_mode_config()
    mode = normalize_retrieval_mode(requested_mode or config.requested_mode)
    private_allowed = private_sources_allowed(role, config)
    warnings: list[str] = []

    if mode == RetrievalMode.RULES_ONLY:
        return RetrievalPlan(
            selected_mode=mode,
            use_sgf=False,
            use_private=False,
            source_order=("rules",),
            expose_debug_metadata=config.expose_debug_metadata,
        )
    if mode == RetrievalMode.CURATED_ONLY:
        return RetrievalPlan(
            selected_mode=mode,
            use_sgf=False,
            use_private=False,
            source_order=("curated",),
            expose_debug_metadata=config.expose_debug_metadata,
        )
    if mode == RetrievalMode.SGF_ONLY:
        return RetrievalPlan(
            selected_mode=mode,
            use_sgf=True,
            use_private=False,
            source_order=("sgf_v2",),
            expose_debug_metadata=config.expose_debug_metadata,
        )

    if not private_allowed:
        warnings.append("private retrieval disabled or not allowed for role; using sgf_only")
        return RetrievalPlan(
            selected_mode=RetrievalMode.SGF_ONLY,
            use_sgf=True,
            use_private=False,
            source_order=("sgf_v2",),
            warnings=tuple(warnings),
            expose_debug_metadata=config.expose_debug_metadata,
        )

    if mode == RetrievalMode.PRIVATE_ONLY:
        return RetrievalPlan(
            selected_mode=mode,
            use_sgf=False,
            use_private=True,
            source_order=("private_sources",),
            expose_debug_metadata=config.expose_debug_metadata,
        )
    if mode == RetrievalMode.HYBRID_PRIVATE_FIRST:
        return RetrievalPlan(
            selected_mode=mode,
            use_sgf=True,
            use_private=True,
            source_order=("private_sources", "sgf_v2"),
            expose_debug_metadata=config.expose_debug_metadata,
        )
    if mode == RetrievalMode.HYBRID_SGF_FIRST:
        return RetrievalPlan(
            selected_mode=mode,
            use_sgf=True,
            use_private=True,
            source_order=("sgf_v2", "private_sources"),
            expose_debug_metadata=config.expose_debug_metadata,
        )

    raise AssertionError(f"Unhandled retrieval mode: {mode}")
