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


class QuarantinedAnswerProvider:
    def answer(self, request: Any, sources: list[dict[str, Any]]) -> str:
        del request, sources
        return "It seems that playing steel guitar has a lot in common with unrelated forum chatter."


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


class DegradedSearchIndex:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        del query, kwargs
        self.calls += 1
        return {
            "results": [{
                "score": 0.91,
                "excerpt": (
                    "Forum technicians reported that Webb amp speaker swaps can produce "
                    "a clearer high end when the replacement speaker suits the cabinet."
                ),
                "source_system": "sgf_phpbb_current",
                "forum_name": "Electronics",
                "thread_title": "Webb amp speaker swaps",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=399975",
                "chunk_id": "sgf:degraded:1",
                "post_uid": "sgf:post:degraded:1",
            }],
            "warnings": [],
        }


class FakeFrontierClient:
    def __init__(self, *, fail: bool = False, ready: bool = True) -> None:
        self.fail = fail
        self.ready = ready
        self.questions: list[str] = []
        self.contexts: list[list[str]] = []

    def readiness(self, *, timeout_seconds: float = 1.0) -> dict[str, Any]:
        del timeout_seconds
        return {
            "status": "ready" if self.ready else "not_ready",
            "reason": "ready" if self.ready else "provider_unavailable",
            "http_status": 200 if self.ready else 503,
        }

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
    request_overrides: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    request = {"question": question, "mode": "ask"}
    if conversation_context is not None:
        request["conversationContext"] = conversation_context
    request.update(request_overrides or {})
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


def call_get(app: Any, path: str) -> tuple[str, dict[str, Any]]:
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = headers

    response = b"".join(app({
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "wsgi.input": io.BytesIO(),
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


def test_result_validation_accepts_explicit_degraded_cards_only_state() -> None:
    value = FakeFrontierClient().answer("question")
    value["mode"] = "partial"
    value["answer"] = "Verified synthesis is unavailable; inspect the relevant source card."
    value["claims"] = []
    value["metadata"] = {"delivery_mode": "sgf_extractive_degraded", "cards_only": True}
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


def test_deterministic_miss_promotes_to_verified_frontier_without_old_retrieval(
    caplog: pytest.LogCaptureFixture,
) -> None:
    search = EmptySearchIndex()
    frontier = FakeFrontierClient()
    app = create_app(
        search,
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "How do E9 positions work?"

    with caplog.at_level(logging.INFO, logger="steel_guitar_rag.api"):
        status, payload = call_answer(app, question)

    assert status == "200 OK"
    assert frontier.questions == [question]
    assert search.calls == 0
    assert payload["sources"]
    route_record = next(
        record.message.removeprefix("answer route event: ")
        for record in caplog.records
        if record.message.startswith("answer route event: ")
    )
    trace = json.loads(route_record)
    assert trace["route"] == "source_backed_rag"
    assert trace["fallback"] == "deterministic_miss_to_source_backed"


def test_position_strategy_content_leads_without_frontier_or_legacy_retrieval() -> None:
    search = EmptySearchIndex()
    frontier = FakeFrontierClient()
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
        "How does a steel guitar player decide when to move frets? Why not just stay on one fret?",
    )

    assert status == "200 OK"
    assert "stay on one fret" in payload["answer"]
    assert "move the bar" in payload["answer"]
    assert "3rd fret" in payload["answer"]
    assert "8th fret" in payload["answer"]
    assert payload["sources"] == []
    assert frontier.questions == []
    assert search.calls == 0
    assert provider.calls == 0


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Where is a Zm chord?", "I don’t recognize “Zm” as a standard chord name."),
        ("Is this grip a full chord?", "I need the missing context"),
    ],
)
def test_frontier_enabled_never_suppresses_deterministic_authority(
    question: str,
    expected: str,
) -> None:
    frontier = FakeFrontierClient()
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert expected in payload["answer"]
    assert payload["sources"] == []
    assert payload["answer_provenance"]["kind"] in {
        "deterministic_e9_rules", "curated_local_guidance",
    }
    assert frontier.questions == []
    assert search.calls == 0


def test_provenance_followup_resolves_preceding_deterministic_chord_answer() -> None:
    frontier = FakeFrontierClient()
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    status, payload = call_answer(
        app,
        "What is your source of information for this?",
        conversation_context=[
            "User: Where can I play a G chord on E9?",
            "Assistant: Use the pitch-validated G positions shown above.",
        ],
    )
    assert status == "200 OK"
    assert "deterministic and curated rules layer" in payload["answer"]
    assert payload["answer_provenance"]["kind"] == "deterministic_e9_rules"
    assert frontier.questions == []


def test_provenance_followup_reuses_preceding_verified_source_cards_without_frontier_call() -> None:
    frontier = FakeFrontierClient()
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    status, payload = call_answer(
        app,
        "What is your source of information for this?",
        conversation_context=[
            "User: What did Forum users say about Webb amp speaker swaps?",
            "Assistant: Forum contributors reported that the speaker swap produced a clearer high end.",
        ],
        request_overrides={
            "isFollowup": True,
            "parentAnswerContext": {
                "question": "What did Forum users say about Webb amp speaker swaps?",
                "answer": "Forum contributors reported that the speaker swap produced a clearer high end.",
                "answerProvenance": {
                    "kind": "verified_sgf_synthesis",
                    "title": "Verified SGF synthesis",
                    "summary": "Terra claims verified by Luna.",
                },
                "sources": [{
                    "forum": "Electronics",
                    "title": "Webb speaker swaps",
                    "excerpt": "The replacement speaker made the high end clearer.",
                    "url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
                }],
            },
        },
    )

    assert status == "200 OK"
    assert "same displayed Steel Guitar Forum evidence" in payload["answer"]
    assert "did not run another retrieval or model request" in payload["answer"]
    assert payload["sources"] == [{
        "title": "Webb speaker swaps",
        "forumName": "Electronics",
        "url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
        "excerpt": "The replacement speaker made the high end clearer.",
        "score": 0.0,
        "chunkId": "",
        "postUid": None,
    }]
    assert payload["answer_provenance"]["kind"] == "verified_sgf_synthesis"
    assert frontier.questions == []
    assert search.calls == 0


def test_main_readiness_requires_exact_frontier_ready_but_reports_local_degraded() -> None:
    ready_app = create_app(
        EmptySearchIndex(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=FakeFrontierClient(ready=True),
    )
    status, payload = call_get(ready_app, "/health/ready")
    assert status == "200 OK"
    assert payload["status"] == "ready"

    degraded_app = create_app(
        EmptySearchIndex(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=FakeFrontierClient(ready=False),
    )
    status, payload = call_get(degraded_app, "/health/ready")
    assert status == "200 OK"
    assert payload["status"] == "degraded"
    assert payload["dependencies"] == {
        "local_answer_paths": "ready",
        "canonical_frontier": "not_ready",
    }


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


def test_complete_new_question_outranks_unrelated_conversation_context() -> None:
    frontier = FakeFrontierClient()
    app = create_app(
        EmptySearchIndex(),
        answer_provider=ExistingAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    context = [
        "User: Where can I play an F major 7?",
        "Assistant: Use strings 2, 3, 4, and 5 open at the first fret.",
    ]

    status, payload = call_answer(
        app,
        "What causes cabinet drop?",
        conversation_context=context,
    )

    assert status == "200 OK"
    assert frontier.questions == ["What causes cabinet drop?"]
    assert frontier.contexts == [context]
    assert payload["sources"]


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


def test_enabled_frontier_failure_checks_bounded_local_evidence_before_503() -> None:
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
    assert search.calls == 1
    assert provider.calls == 0
    assert "could not complete this answer" in payload["error"]
    assert "No generic answer was substituted" in payload["error"]


def test_enabled_frontier_failure_returns_bounded_local_extractive_evidence() -> None:
    search = DegradedSearchIndex()
    provider = ExistingAnswerProvider()
    app = create_app(
        search,
        answer_provider=provider,
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=FakeFrontierClient(fail=True),
    )
    status, payload = call_answer(
        app, "What did forum members report about Webb amp speaker swaps?"
    )
    assert status == "200 OK"
    assert search.calls == 1
    assert provider.calls == 0
    assert payload["sources"]
    assert payload["answer_provenance"]["kind"] == "sgf_extractive_degraded"
    assert payload["warnings"] == [
        "verified synthesis is unavailable; showing extractive SGF evidence"
    ]


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
    assert search.calls == 1
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
        "synthesis": "terra_complete",
        "traceId": trace["traceId"],
        "verification": "luna_claim_entailment",
    }
    assert len(trace["traceId"]) == 16


def test_route_diagnostics_name_the_generic_sgf_quarantine_fallback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app(
        EntitySearchIndex(),
        answer_provider=QuarantinedAnswerProvider(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=False,
    )

    with caplog.at_level(logging.INFO, logger="steel_guitar_rag.api"):
        status, payload = call_answer(app, "What is a useful steel guitar setup clue?")

    assert status == "200 OK"
    assert "I need a more specific steel-guitar question" in payload["answer"]
    route_record = next(
        record.message.removeprefix("answer route event: ")
        for record in caplog.records
        if record.message.startswith("answer route event: ")
    )
    trace = json.loads(route_record)
    assert trace["fallback"] == "sgf_quarantine_specificity_fallback"
