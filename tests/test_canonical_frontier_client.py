from __future__ import annotations

import io
import json
import logging
from typing import Any

import pytest

from steel_guitar_rag.access_control import DEV_ACCESS_ROLE_ENVIRON
from steel_guitar_rag.api import create_app
from steel_guitar_rag.canonical_frontier_client import (
    CANONICAL_FRONTIER_TIMEOUT_ENV,
    CANONICAL_FRONTIER_TOKEN_ENV,
    ENABLE_CANONICAL_FRONTIER_ENV,
    CanonicalFrontierClient,
    CanonicalFrontierUnavailable,
    configured_canonical_frontier_enabled,
    validate_frontier_result,
)


class EmptySearchIndex:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        del query, kwargs
        self.calls += 1
        return {"results": [], "warnings": []}


class ExistingAnswerProvider:
    def __init__(self) -> None:
        self.calls = 0

    def answer(self, request: Any, sources: list[dict[str, Any]]) -> str:
        del request, sources
        self.calls += 1
        return "Existing answer path."


class EntitySearchIndex:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        self.calls.append(query)
        return {
            "results": [{
                "score": 0.91,
                "excerpt": f"Steel Guitar Forum members discussed {query.rstrip('?')} in pedal-steel context.",
                "source_system": "sgf_phpbb_current",
                "forum_name": "Steel Players",
                "thread_title": query.rstrip("?"),
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=399974",
                "chunk_id": "sgf:entity:1",
                "post_uid": "sgf:post:entity:1",
            }],
            "warnings": [],
        }


class FakeFrontierClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.questions: list[str] = []
        self.contexts: list[list[str]] = []

    def answer(
        self,
        question: str,
        *,
        conversation_context: list[str] | None = None,
    ) -> dict[str, Any]:
        self.questions.append(question)
        self.contexts.append(list(conversation_context or []))
        if self.fail:
            raise CanonicalFrontierUnavailable("test outage")
        return {
            "schema_version": 1,
            "mode": "complete",
            "answer": "Forum contributors reported that the speaker swap produced a clearer high end.",
            "claims": [{
                "claim_id": "c1",
                "text": "Forum contributors reported that the speaker swap produced a clearer high end.",
                "source_ids": ["sgf:passage:1"],
                "support_mode": "independent_semantic_verifier",
            }],
            "sources": [{
                "source_id": "sgf:passage:1",
                "chunk_id": "sgf:passage:1",
                "post_uid": "sgf:post:1",
                "thread_title": "Webb speaker swaps",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
                "forum_name": "Electronics",
                "excerpt": "The replacement speaker made the high end clearer.",
                "score": 0.9,
                "warnings": [],
            }],
            "coverage": [],
            "response_note": "",
            "metadata": {},
        }


def call_answer(
    app: Any,
    question: str,
    *,
    conversation_context: Any = None,
) -> tuple[str, dict[str, Any]]:
    request = {"question": question, "mode": "ask"}
    if conversation_context is not None:
        request["conversationContext"] = conversation_context
    body = json.dumps(request).encode("utf-8")
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = headers

    response = b"".join(app({
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/answer",
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        DEV_ACCESS_ROLE_ENVIRON: "beta_user",
    }, start_response))
    return captured["status"], json.loads(response)


def test_frontier_flag_defaults_off() -> None:
    assert configured_canonical_frontier_enabled({}) is False
    assert configured_canonical_frontier_enabled({ENABLE_CANONICAL_FRONTIER_ENV: "0"}) is False
    assert configured_canonical_frontier_enabled({ENABLE_CANONICAL_FRONTIER_ENV: "true"}) is True


def test_enabled_client_requires_server_side_token() -> None:
    with pytest.raises(ValueError, match=CANONICAL_FRONTIER_TOKEN_ENV):
        CanonicalFrontierClient.from_env({ENABLE_CANONICAL_FRONTIER_ENV: "1"})


def test_verified_frontier_allows_protected_ninety_second_timeout() -> None:
    client = CanonicalFrontierClient.from_env({
        CANONICAL_FRONTIER_TOKEN_ENV: "server-side-test-token",
        CANONICAL_FRONTIER_TIMEOUT_ENV: "90",
    })
    assert client.timeout_seconds == 90.0


def test_answer_runner_allows_protected_ninety_second_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STEEL_RAG_ANSWER_WALL_TIMEOUT_SECONDS", "90")
    app = create_app(EmptySearchIndex(), answer_auth_mode="local_dev")
    assert app._answer_wall_timeout == 90.0


def test_result_validation_rejects_uncited_claim() -> None:
    value = FakeFrontierClient().answer("question")
    value["claims"][0]["source_ids"] = ["missing"]
    with pytest.raises(CanonicalFrontierUnavailable, match="support"):
        validate_frontier_result(value)


def test_result_validation_accepts_v1034_relevance_entailment_support() -> None:
    value = FakeFrontierClient().answer("question")
    value["claims"][0]["support_mode"] = "independent_relevance_entailment_verifier"
    assert validate_frontier_result(value) is value


def test_disabled_frontier_preserves_existing_answer_path() -> None:
    search = EmptySearchIndex()
    provider = ExistingAnswerProvider()
    frontier = FakeFrontierClient()
    app = create_app(
        search,
        answer_provider=provider,
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=False,
        canonical_frontier_client=frontier,
    )
    status, _payload = call_answer(app, "What did forum members report about Webb amp speaker swaps?")
    assert status == "200 OK"
    assert frontier.questions == []
    assert search.calls == 1


def test_enabled_frontier_returns_verified_answer_without_old_retrieval() -> None:
    search = EmptySearchIndex()
    frontier = FakeFrontierClient()
    app = create_app(
        search,
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "What did forum members report about Webb amp speaker swaps?"
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert frontier.questions == [question]
    assert search.calls == 0
    assert payload["answer"] == "Forum contributors reported that the speaker swap produced a clearer high end."
    assert payload["sources"] == [{
        "title": "Webb speaker swaps",
        "forumName": "Electronics",
        "url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
        "excerpt": "The replacement speaker made the high end clearer.",
        "score": 0.9,
        "chunkId": "sgf:passage:1",
        "postUid": "sgf:post:1",
    }]


@pytest.mark.parametrize(
    "question",
    [
        "Who is Travis Toy?",
        "What is Travis Toy Tutorials?",
        "Who was Weldon Myrick?",
    ],
)
def test_corpus_established_entities_reach_source_backed_frontier(question: str) -> None:
    search = EntitySearchIndex()
    frontier = FakeFrontierClient()
    app = create_app(
        search,
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )

    status, payload = call_answer(app, question)

    assert status == "200 OK"
    assert frontier.questions == [question]
    assert search.calls == [question]
    assert payload["sources"]


def test_enabled_frontier_forwards_bounded_conversation_context() -> None:
    frontier = FakeFrontierClient()
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    context = [
        "User: I play a universal 12-string tuning.",
        "Assistant: Keep the universal tuning constraint in view.",
    ]
    status, _payload = call_answer(
        app,
        "How does that change the recommendation?",
        conversation_context=context,
    )
    assert status == "200 OK"
    assert frontier.contexts == [context]


def test_contextual_pronoun_followup_reaches_frontier_before_generic_intent_fallback() -> None:
    frontier = FakeFrontierClient()
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "Which of those players was identified as playing on the track discussed?"
    context = [
        "User: Who played steel guitar on John Prine's 1999 album In Spite of Ourselves?",
        "Assistant: Walter Stettner reported that Al Perkins, Buddy Emmons, and Dan Dugmore were featured.",
    ]
    status, payload = call_answer(app, question, conversation_context=context)
    assert status == "200 OK"
    assert frontier.questions == [question]
    assert frontier.contexts == [context]
    assert payload["sources"]


def test_contextual_unknown_entity_followup_is_proved_from_prior_user_question() -> None:
    search = EntitySearchIndex()
    frontier = FakeFrontierClient()
    app = create_app(
        search,
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "What is he especially known for?"
    context = [
        "User: Who is Travis Toy?",
        "Assistant: Travis Toy is a pedal-steel guitarist discussed by forum contributors.",
    ]

    status, payload = call_answer(app, question, conversation_context=context)

    assert status == "200 OK"
    assert search.calls == ["Who is Travis Toy?"]
    assert frontier.questions == [question]
    assert frontier.contexts == [context]
    assert payload["sources"]


@pytest.mark.parametrize(
    "context",
    ["not-a-list", ["ok"] * 9, [""], ["x" * 8_001]],
)
def test_answer_rejects_invalid_conversation_context(context: Any) -> None:
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=FakeFrontierClient(),
    )
    status, payload = call_answer(
        app,
        "How does that change the recommendation?",
        conversation_context=context,
    )
    assert status == "400 Bad Request"
    assert "conversationContext" in payload["error"]


def test_enabled_frontier_failure_is_honest_and_does_not_use_old_path() -> None:
    search = EmptySearchIndex()
    frontier = FakeFrontierClient(fail=True)
    provider = ExistingAnswerProvider()
    app = create_app(
        search,
        answer_provider=provider,
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    status, payload = call_answer(app, "What did forum members report about Webb amp speaker swaps?")
    assert status == "503 Service Unavailable"
    assert frontier.questions
    assert search.calls == 0
    assert provider.calls == 0
    assert "could not complete this answer" in payload["error"]
    assert "No generic answer was substituted" in payload["error"]


def test_hybrid_route_combines_deterministic_position_with_verified_forum_context() -> None:
    frontier = FakeFrontierClient()
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "What do players say about Fmaj7 and where can I play it?"

    status, payload = call_answer(app, question)

    assert status == "200 OK"
    assert frontier.questions == [question]
    assert payload["answer"].startswith("Deterministic E9 result:")
    assert "Fmaj7 is F-A-C-E" in payload["answer"]
    assert "Source-backed forum context:" in payload["answer"]
    assert payload["fretboard"]["title"] == "F major 7 positions on E9"
    assert payload["sources"]


def test_hybrid_frontier_failure_keeps_deterministic_result_with_explicit_warning() -> None:
    frontier = FakeFrontierClient(fail=True)
    search = EmptySearchIndex()
    provider = ExistingAnswerProvider()
    app = create_app(
        search,
        answer_provider=provider,
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )

    status, payload = call_answer(
        app,
        "What do players say about Fmaj7 and where can I play it?",
    )

    assert status == "200 OK"
    assert "Fmaj7 is F-A-C-E" in payload["answer"]
    assert "No forum summary was substituted" in payload["answer"]
    assert payload["warnings"] == ["source-backed forum context is temporarily unavailable"]
    assert payload["fretboard"]["title"] == "F major 7 positions on E9"
    assert search.calls == 0
    assert provider.calls == 0


def test_route_diagnostics_record_every_control_stage(caplog: pytest.LogCaptureFixture) -> None:
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=FakeFrontierClient(),
    )

    with caplog.at_level(logging.INFO, logger="steel_guitar_rag.api"):
        status, _payload = call_answer(
            app,
            "What did forum members report about Webb amp speaker swaps?",
        )

    assert status == "200 OK"
    route_records = [
        record.message.removeprefix("answer route event: ")
        for record in caplog.records
        if record.message.startswith("answer route event: ")
    ]
    assert len(route_records) == 1
    trace = json.loads(route_records[0])
    assert trace == {
        "classification": "steel_guitar:forum_wisdom",
        "corpusProbe": "not_needed",
        "displayedAnswer": "answer_with_sources",
        "evidence": "1_source_cards",
        "fallback": "none",
        "retrieval": "canonical_frontier_complete",
        "route": "source_backed_rag",
        "synthesis": "frontier_complete",
        "traceId": trace["traceId"],
        "verification": "frontier_contract_verified",
    }
    assert len(trace["traceId"]) == 16
