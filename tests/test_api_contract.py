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
from pocketsteel.lesson_studio import build_lesson
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
    assert set(answer).issubset(required_answer_keys | {"fretboard", "tab_example", "progression_guide", "melody_exercise"})
    assert "fretboard" not in answer
    assert set(answer["sources"][0]) == {"title", "forumName", "url", "excerpt", "score", "chunkId", "postUid"}
    assert set(answer["sections"][0]) == {"title", "style", "body"}


def test_lesson_v2_contract_shape() -> None:
    lesson = build_lesson({"lessonId": "fundamentals-major-pocket"})

    assert lesson["schemaVersion"] == "lesson_v2"
    assert {
        "id",
        "origin",
        "pathId",
        "title",
        "topic",
        "level",
        "duration",
        "durationLabel",
        "goal",
        "explanation",
        "exercises",
        "whatToListenFor",
        "commonMistakes",
        "practiceChecklist",
        "nextStep",
        "links",
        "assumptions",
        "progressPersistence",
        "curriculumVersion",
        "conceptId",
        "generationMode",
        "whyItMatters",
        "workedExamples",
        "mechanics",
        "teachingSources",
        "reviewState",
    }.issubset(lesson)
    assert {"title", "timebox", "steps", "listenFor"} == set(lesson["exercises"][0])


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
                    "tierReason": "Starter because it is a common home-position family.",
                    "whenToUse": "Use it as the straight-bar reference.",
                    "soundCharacter": "Complete G major sound.",
                    "movementUse": "Good for anchoring the bar.",
                    "resolutionUse": "Stable enough to use as an arrival point.",
                    "forumEvidence": [],
                    "forumEvidenceStatus": "not_found",
                    "explanationShort": "3rd fret with no pedals gives G major.",
                    "explanationLong": "3rd fret with no pedals gives G major with notes G, D, and B.",
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
        "tierReason",
        "whenToUse",
        "soundCharacter",
        "movementUse",
        "resolutionUse",
        "forumEvidence",
        "forumEvidenceStatus",
        "explanationShort",
        "explanationLong",
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


def test_optional_tab_example_payload_contract_shape() -> None:
    answer = {
        "answer": "Try a simple G major grip at the 3rd fret on strings 4, 5, and 6.",
        "mode": "ask",
        "sources": [],
        "warnings": [],
        "sections": [
            {
                "title": "Answer",
                "style": "lead",
                "body": "Try a simple G major grip at the 3rd fret on strings 4, 5, and 6.",
            }
        ],
        "tab_example": {
            "id": "g-major-456-open",
            "title": "G major 4-5-6 grip",
            "context": {
                "key": "G",
                "tuning": "E9",
                "profile": "default_e9",
                "difficulty": "beginner",
                "grip": "4-5-6",
            },
            "rendered_tab": "Ch |G\n 4 |3\n 5 |3\n 6 |3",
            "validation": {
                "ok": True,
                "issues": [],
                "profile": "default_e9",
                "eventCount": 1,
            },
            "explanation": "A simple G major grip at fret 3.",
            "intervals": [
                {
                    "eventId": "g-major-456-open-1",
                    "chord": "G",
                    "byString": {"4": "1", "5": "5", "6": "3"},
                }
            ],
            "events": [
                {
                    "chord": "G",
                    "notes": [
                        {"string": 4, "fret": 3, "changes": []},
                        {"string": 5, "fret": 3, "changes": []},
                        {"string": 6, "fret": 3, "changes": []},
                    ],
                }
            ],
        },
    }

    assert answer["mode"] in VALID_MODES
    tab_example = answer["tab_example"]
    assert set(tab_example) == {
        "id",
        "title",
        "context",
        "rendered_tab",
        "validation",
        "explanation",
        "intervals",
        "events",
    }
    assert tab_example["context"]["tuning"] == "E9"
    assert tab_example["context"]["profile"] == "default_e9"
    assert tab_example["validation"] == {
        "ok": True,
        "issues": [],
        "profile": "default_e9",
        "eventCount": 1,
    }
    assert tab_example["rendered_tab"]
    note = tab_example["events"][0]["notes"][0]
    assert set(note) == {"string", "fret", "changes"}
    assert 1 <= note["string"] <= 10
    assert 0 <= note["fret"] <= 24


def test_optional_melody_exercise_payload_contract_shape() -> None:
    melody_exercise = {
        "schemaVersion": "melody_exercise_v0",
        "id": "melody-g-section-1",
        "status": "ready",
        "kind": "artist_solo_lesson",
        "title": "Artist — Song — Section 1 E9 lesson",
        "material": {
            "artist": "Artist",
            "song": "Song",
            "recording": "Studio version",
            "sourceUrl": "https://example.test/recording",
        },
        "renderingMode": "e9_adaptation",
        "accuracy": {"label": "approximate", "confidence": "medium", "note": "Checked against the supplied phrase."},
        "section": {"number": 1, "total": 2, "label": "Solo", "hasMore": True, "nextSection": 2},
        "events": [
            {
                "id": "melody-step-1",
                "step": 1,
                "inputToken": "1",
                "resolvedNote": "G",
                "scaleDegree": "1",
                "technique": "pick",
                "explanation": "Play G on string 4 at fret 3.",
                "notes": [{"string": 4, "fret": 3, "changes": []}],
            }
        ],
        "validation": {"ok": True, "mechanical": [], "musical": [], "steelPractical": [], "accuracy": []},
    }

    assert melody_exercise["kind"] in {
        "original_exercise",
        "user_melody",
        "artist_solo_lesson",
        "song_arrangement_lesson",
    }
    assert melody_exercise["renderingMode"] in {"transcription", "e9_adaptation", "teaching_simplification"}
    assert melody_exercise["accuracy"]["label"] in {"exact", "approximate", "interpretive"}
    assert melody_exercise["section"]["hasMore"] is True
    assert melody_exercise["events"][0]["notes"][0] == {"string": 4, "fret": 3, "changes": []}


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
