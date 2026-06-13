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
from scripts.serve_answer_smoke import resolved_answer_auth_mode, resolved_auth_provider


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
    required_answer_keys = {"answer", "mode", "sources", "warnings", "sections"}
    assert required_answer_keys.issubset(answer)
    assert set(answer).issubset(required_answer_keys | {"fretboard"})
    assert "fretboard" not in answer
    assert set(answer["sources"][0]) == {"title", "forumName", "url", "excerpt", "score", "chunkId", "postUid"}
    assert set(answer["sections"][0]) == {"title", "style", "body"}


def test_optional_fretboard_payload_contract_shape() -> None:
    answer = {
        "answer": "On standard E9, useful G major positions include 3rd fret open, 6th fret A+F, and 10th fret A+B.",
        "mode": "ask",
        "sources": [],
        "warnings": [],
        "sections": [{"title": "Answer", "style": "lead", "body": "On standard E9, useful G major positions include 3rd fret open."}],
        "fretboard": {
            "type": "e9-fretboard-diagram",
            "title": "G major positions on E9",
            "subtitle": "Common places to find G major.",
            "description": "Common places to find G major.",
            "tuning": "E9",
            "strings": {"count": 10},
            "positions": [
                {
                    "id": "g-open-3",
                    "label": "G major",
                    "root": "G",
                    "quality": "major",
                    "positionKind": "starter",
                    "fret": 3,
                    "strings": [4, 5, 6],
                    "grip": "4-5-6",
                    "pedals": [],
                    "levers": [],
                    "color": "primary",
                    "role": "Open position",
                    "function": "I",
                    "keyContext": "G",
                    "family": "major_triad",
                    "tier": "beginner",
                    "colorRole": "primary",
                    "visibleByDefault": True,
                    "sortOrder": 10,
                    "notes": {"4": "G", "5": "D", "6": "B"},
                    "intervals": {"4": "1", "5": "5", "6": "3"},
                    "omittedIntervals": [],
                    "addedIntervals": [],
                    "isFullChord": True,
                    "isPartial": False,
                    "isRootless": False,
                    "whyUseIt": "Use this as a G major starter position.",
                    "caveats": [],
                    "validationStatus": "pitch_validated",
                    "explanation": "No-pedal fret 3 gives a G major grip.",
                }
            ],
            "highlights": [
                {
                    "id": "g-open-3",
                    "label": "G major",
                    "fret": 3,
                    "strings": [4, 5, 6],
                    "pedals": [],
                    "levers": [],
                    "role": "Open position",
                }
            ],
        },
    }

    assert answer["mode"] in VALID_MODES
    fretboard = answer["fretboard"]
    assert {"type", "title", "description", "positions", "highlights"}.issubset(fretboard)
    assert fretboard["type"] == "e9-fretboard-diagram"
    assert fretboard["tuning"] == "E9"
    assert fretboard["strings"]["count"] == 10
    position = fretboard["positions"][0]
    assert set(position) == {
        "id",
        "label",
        "root",
        "quality",
        "positionKind",
        "fret",
        "strings",
        "grip",
        "pedals",
        "levers",
        "color",
        "role",
        "function",
        "keyContext",
        "family",
        "tier",
        "colorRole",
        "visibleByDefault",
        "sortOrder",
        "notes",
        "intervals",
        "omittedIntervals",
        "addedIntervals",
        "isFullChord",
        "isPartial",
        "isRootless",
        "whyUseIt",
        "caveats",
        "validationStatus",
        "explanation",
    }
    assert position["grip"] == "4-5-6"
    assert position["color"] == "primary"
    assert position["family"] == "major_triad"
    assert position["tier"] == "beginner"
    assert position["colorRole"] == "primary"
    assert position["visibleByDefault"] is True
    assert position["sortOrder"] == 10
    highlight = fretboard["highlights"][0]
    assert set(highlight) == {"id", "label", "fret", "strings", "pedals", "levers", "role"}
    assert 0 <= highlight["fret"] <= 24
    assert all(1 <= string <= 10 for string in highlight["strings"])


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


def test_answer_smoke_server_auth_config_contract(monkeypatch) -> None:
    monkeypatch.setenv("STEEL_RAG_AUTH_PROVIDER", "cloudflare_access")
    monkeypatch.setenv("STEEL_RAG_ANSWER_AUTH_MODE", "production")

    assert resolved_auth_provider(None) == "cloudflare_access"
    assert resolved_answer_auth_mode(None) == "production"
    assert resolved_auth_provider("scaffold") == "scaffold"
    assert resolved_answer_auth_mode("local_dev") == "local_dev"

    monkeypatch.delenv("STEEL_RAG_AUTH_PROVIDER", raising=False)
    monkeypatch.delenv("STEEL_RAG_ANSWER_AUTH_MODE", raising=False)
    assert resolved_auth_provider(None) is None
    assert resolved_answer_auth_mode(None) == "local_dev"
