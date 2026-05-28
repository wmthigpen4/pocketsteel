from __future__ import annotations

import json
from pathlib import Path

from pocketsteel.access_control import (
    ACCESS_ROLES,
    ANSWER_AUTH_MODE_ENV,
    AUTH_PROVIDER_ENV,
    CLOUDFLARE_ACCESS_AUTH_PROVIDER,
    DEV_ACCESS_ROLE_HEADER,
    SCAFFOLD_AUTH_PROVIDER,
    TRUSTED_AUTH_ROLE_HEADER,
    can_call_live_answer,
    normalize_access_role,
)
from pocketsteel.answer_usage import (
    RATE_LIMIT_ENABLED_ENV,
    RATE_LIMIT_MAX_REQUESTS_ENV,
    RATE_LIMIT_WINDOW_SECONDS_ENV,
)
from pocketsteel.answering import VALID_MODES
from pocketsteel.cloudflare_access import (
    BETA_USER_EMAILS_ENV,
    ADMIN_EMAILS_ENV,
    CLOUDFLARE_ACCESS_AUD_ENV,
    CLOUDFLARE_ACCESS_ISSUER_ENV,
    CLOUDFLARE_ACCESS_JWKS_URL_ENV,
    CLOUDFLARE_ACCESS_JWT_HEADER,
)


FIXTURE = Path("tests/fixtures/api_contract_mock_response.json")


def test_api_contract_fixture_matches_required_shapes() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    search = payload["searchResponse"]
    answer = payload["answerResponse"]

    assert set(search) == {"query", "results", "warnings"}
    assert set(search["results"][0]) == {
        "score",
        "excerpt",
        "source_system",
        "forum_name",
        "thread_title",
        "thread_url",
        "chunk_id",
        "post_uid",
        "source_kind",
        "forum_id",
        "legacy_forum_number",
        "thread_id",
        "legacy_thread_uid",
        "thread_category",
        "thread_quality_score",
        "chunk_index",
        "warnings",
    }

    assert answer["mode"] in VALID_MODES
    assert set(answer) == {"answer", "mode", "sources", "warnings", "sections"}
    assert set(answer["sources"][0]) == {"title", "forumName", "url", "excerpt", "score", "chunkId", "postUid"}
    assert set(answer["sections"][0]) == {"title", "style", "body"}


def test_access_role_contract_gates_live_answer_access() -> None:
    assert ACCESS_ROLES == ("anonymous", "beta_user", "admin")
    assert TRUSTED_AUTH_ROLE_HEADER == "X-Steel-Rag-Access-Role"
    assert DEV_ACCESS_ROLE_HEADER == "X-Steel-Rag-Dev-Access-Role"
    assert ANSWER_AUTH_MODE_ENV == "STEEL_RAG_ANSWER_AUTH_MODE"
    assert "Turn" + "around" not in TRUSTED_AUTH_ROLE_HEADER
    assert "Turn" + "around" not in DEV_ACCESS_ROLE_HEADER
    assert "TURN" + "AROUND" not in ANSWER_AUTH_MODE_ENV
    assert normalize_access_role("member") == "beta_user"
    assert normalize_access_role("unknown") == "anonymous"
    assert can_call_live_answer("anonymous") is False
    assert can_call_live_answer("beta_user") is True
    assert can_call_live_answer("admin") is True
    assert RATE_LIMIT_ENABLED_ENV == "STEEL_RAG_ANSWER_RATE_LIMIT_ENABLED"
    assert RATE_LIMIT_MAX_REQUESTS_ENV == "STEEL_RAG_ANSWER_RATE_LIMIT_MAX_REQUESTS"
    assert RATE_LIMIT_WINDOW_SECONDS_ENV == "STEEL_RAG_ANSWER_RATE_LIMIT_WINDOW_SECONDS"
    assert AUTH_PROVIDER_ENV == "STEEL_RAG_AUTH_PROVIDER"
    assert SCAFFOLD_AUTH_PROVIDER == "scaffold"
    assert CLOUDFLARE_ACCESS_AUTH_PROVIDER == "cloudflare_access"
    assert CLOUDFLARE_ACCESS_JWT_HEADER == "Cf-Access-Jwt-Assertion"
    assert CLOUDFLARE_ACCESS_ISSUER_ENV == "STEEL_RAG_CF_ACCESS_ISSUER"
    assert CLOUDFLARE_ACCESS_AUD_ENV == "STEEL_RAG_CF_ACCESS_AUD"
    assert CLOUDFLARE_ACCESS_JWKS_URL_ENV == "STEEL_RAG_CF_ACCESS_JWKS_URL"
    assert BETA_USER_EMAILS_ENV == "STEEL_RAG_BETA_USER_EMAILS"
    assert ADMIN_EMAILS_ENV == "STEEL_RAG_ADMIN_EMAILS"
