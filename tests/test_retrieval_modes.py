from __future__ import annotations

import pytest

from pocketsteel.retrieval_modes import (
    DEFAULT_PRIVATE_CHROMA_PATH,
    DEFAULT_PRIVATE_COLLECTION,
    DEFAULT_SGF_V2_CHROMA_PATH,
    DEFAULT_SGF_V2_COLLECTION,
    RetrievalMode,
    configured_retrieval_mode_config,
    normalize_retrieval_mode,
    private_sources_allowed,
    retrieval_plan_for_role,
)


def test_default_config_is_sgf_only_and_private_disabled() -> None:
    config = configured_retrieval_mode_config({})

    assert config.requested_mode == RetrievalMode.SGF_ONLY
    assert config.private_sources_enabled is False
    assert config.sgf_chroma_path == DEFAULT_SGF_V2_CHROMA_PATH
    assert config.sgf_collection == DEFAULT_SGF_V2_COLLECTION
    assert config.private_chroma_path == DEFAULT_PRIVATE_CHROMA_PATH
    assert config.private_collection == DEFAULT_PRIVATE_COLLECTION


def test_normalize_retrieval_mode_accepts_dash_or_enum() -> None:
    assert normalize_retrieval_mode("hybrid-private-first") == RetrievalMode.HYBRID_PRIVATE_FIRST
    assert normalize_retrieval_mode(RetrievalMode.CURATED_ONLY) == RetrievalMode.CURATED_ONLY


def test_unknown_retrieval_mode_fails() -> None:
    with pytest.raises(ValueError, match="Unknown retrieval mode"):
        normalize_retrieval_mode("chaos_mode")


def test_private_retrieval_disabled_by_default_even_for_beta() -> None:
    config = configured_retrieval_mode_config({"STEEL_RAG_RETRIEVAL_MODE": "hybrid_private_first"})

    plan = retrieval_plan_for_role("beta_user", config=config)

    assert plan.selected_mode == RetrievalMode.SGF_ONLY
    assert plan.use_sgf is True
    assert plan.use_private is False
    assert plan.source_order == ("sgf_v2",)
    assert plan.warnings == ("private retrieval disabled or not allowed for role; using sgf_only",)


def test_public_anonymous_cannot_use_private_sources_even_when_enabled() -> None:
    config = configured_retrieval_mode_config(
        {
            "STEEL_RAG_RETRIEVAL_MODE": "private_only",
            "STEEL_RAG_ENABLE_PRIVATE_SOURCES": "true",
        }
    )

    assert private_sources_allowed("anonymous", config) is False
    plan = retrieval_plan_for_role("anonymous", config=config)

    assert plan.selected_mode == RetrievalMode.SGF_ONLY
    assert plan.use_private is False


def test_beta_can_use_private_when_explicitly_enabled() -> None:
    config = configured_retrieval_mode_config(
        {
            "STEEL_RAG_RETRIEVAL_MODE": "hybrid_private_first",
            "STEEL_RAG_ENABLE_PRIVATE_SOURCES": "1",
        }
    )

    plan = retrieval_plan_for_role("beta_user", config=config)

    assert plan.selected_mode == RetrievalMode.HYBRID_PRIVATE_FIRST
    assert plan.use_private is True
    assert plan.use_sgf is True
    assert plan.source_order == ("private_sources", "sgf_v2")


def test_admin_debug_metadata_flag_is_explicit() -> None:
    config = configured_retrieval_mode_config(
        {
            "STEEL_RAG_RETRIEVAL_MODE": "hybrid_sgf_first",
            "STEEL_RAG_ENABLE_PRIVATE_SOURCES": "true",
            "STEEL_RAG_RETRIEVAL_DEBUG": "yes",
        }
    )

    plan = retrieval_plan_for_role("admin", config=config)

    assert plan.selected_mode == RetrievalMode.HYBRID_SGF_FIRST
    assert plan.source_order == ("sgf_v2", "private_sources")
    assert plan.expose_debug_metadata is True


def test_rules_and_curated_modes_do_not_touch_sgf_or_private() -> None:
    config = configured_retrieval_mode_config({"STEEL_RAG_ENABLE_PRIVATE_SOURCES": "true"})

    rules = retrieval_plan_for_role("admin", requested_mode="rules_only", config=config)
    curated = retrieval_plan_for_role("admin", requested_mode="curated_only", config=config)

    assert rules.source_order == ("rules",)
    assert rules.use_sgf is False
    assert rules.use_private is False
    assert curated.source_order == ("curated",)
    assert curated.use_sgf is False
    assert curated.use_private is False
