from __future__ import annotations

import io
import json
import logging
import urllib.request
from dataclasses import replace
from typing import Any

import pytest

from steel_guitar_rag.access_control import DEV_ACCESS_ROLE_ENVIRON
from steel_guitar_rag.api import create_app
from steel_guitar_rag.semantic_answer_orchestrator import (
    ENABLE_SEMANTIC_ANSWER_ENV,
    OPENAI_API_KEY_ENV,
    OpenAIResponsesSemanticAnswerer,
    SemanticAnswerMetrics,
    SemanticAnswerResult,
    SemanticAnswerUnavailable,
    configured_semantic_answer_enabled,
    validate_semantic_answer_result,
)


class EmptySearchIndex:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        self.calls.append(query)
        return {"results": [], "warnings": []}


class FakeSemanticAnswerer:
    def __init__(self, result: SemanticAnswerResult | None = None, *, fail: bool = False) -> None:
        self.result = result
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def answer(
        self,
        question: str,
        *,
        mode: str,
        conversation_context: list[str],
    ) -> SemanticAnswerResult:
        self.calls.append({"question": question, "mode": mode, "context": conversation_context})
        if self.fail:
            raise SemanticAnswerUnavailable("test planner outage")
        assert self.result is not None
        return self.result


class FakeFrontier:
    def __init__(self) -> None:
        self.questions: list[str] = []
        self.contexts: list[list[str]] = []

    def answer(self, question: str, *, conversation_context: list[str]) -> dict[str, Any]:
        self.questions.append(question)
        self.contexts.append(conversation_context)
        claim = "Players reported that the wound sixth string changes pedal feel and tone."
        return {
            "schema_version": 1,
            "mode": "complete",
            "answer": claim,
            "claims": [{
                "claim_id": "c1",
                "text": claim,
                "source_ids": ["sgf:1"],
                "support_mode": "independent_relevance_entailment_verifier",
            }],
            "sources": [{
                "source_id": "sgf:1",
                "chunk_id": "sgf:1",
                "post_uid": "sgf:post:1",
                "thread_title": "Wound sixth strings",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
                "forum_name": "Pedal Steel",
                "excerpt": "A wound sixth changed the pedal feel and tone on this E9 setup.",
                "score": 0.9,
            }],
        }


def result(
    route: str,
    *,
    domain: str = "steel_guitar",
    intent: str = "conceptual_teaching",
    answer: str = "",
    tool_query: str = "",
    needs_sources: bool = False,
    needs_fretboard: bool = False,
    needs_copedent: bool = False,
    missing_context: tuple[str, ...] = (),
    reason_code: str = "general_teaching_is_source_free",
) -> SemanticAnswerResult:
    return SemanticAnswerResult(
        schema_version=1,
        route=route,  # type: ignore[arg-type]
        domain=domain,
        intent=intent,
        needs_sources=needs_sources,
        needs_fretboard=needs_fretboard,
        needs_copedent=needs_copedent,
        confidence="high",
        answer=answer,
        tool_query=tool_query,
        missing_context=missing_context,
        reason_code=reason_code,
    )


def call_answer(
    app: Any,
    question: str,
    *,
    conversation_context: list[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    request: dict[str, Any] = {"question": question, "mode": "ask"}
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


def test_semantic_answer_flag_defaults_off() -> None:
    assert configured_semantic_answer_enabled({}) is False
    assert configured_semantic_answer_enabled({ENABLE_SEMANTIC_ANSWER_ENV: "0"}) is False
    assert configured_semantic_answer_enabled({ENABLE_SEMANTIC_ANSWER_ENV: "true"}) is True


def test_enabled_openai_answerer_requires_server_side_key() -> None:
    with pytest.raises(ValueError, match=OPENAI_API_KEY_ENV):
        OpenAIResponsesSemanticAnswerer.from_env({ENABLE_SEMANTIC_ANSWER_ENV: "1"})


def test_openai_answerer_uses_responses_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    teaching_answer = (
        "Treat the held chord as your harmonic boundary while the melody chooses chord tones for rest and "
        "nearby scale tones for motion. On pedal steel, let one picked grip imply the harmony, then move a "
        "single voice and block the strings you do not want. Practice over one sustained chord and resolve "
        "each short phrase to a chord tone."
    )
    plan = {
        "schema_version": 1,
        "route": "semantic_teacher",
        "domain": "steel_guitar",
        "intent": "conceptual_teaching",
        "needs_sources": False,
        "needs_fretboard": False,
        "needs_copedent": False,
        "confidence": "high",
        "answer": teaching_answer,
        "tool_query": "",
        "missing_context": [],
        "reason_code": "general_teaching_is_source_free",
    }
    response_body = json.dumps({
        "status": "completed",
        "model": "gpt-test-2026-08-01",
        "usage": {
            "input_tokens": 321,
            "input_tokens_details": {"cached_tokens": 120},
            "output_tokens": 87,
            "output_tokens_details": {"reasoning_tokens": 24},
            "total_tokens": 408,
        },
        "output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps(plan)}],
        }],
    }).encode("utf-8")
    captured: dict[str, Any] = {}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return response_body

    def urlopen(request: urllib.request.Request, timeout: float) -> Response:
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = json.loads(bytes(request.data or b"").decode("utf-8"))
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    answerer = OpenAIResponsesSemanticAnswerer(api_key="server-secret", model="gpt-test", timeout_seconds=7)
    parsed = answerer.answer("How do harmony and melody coexist on steel?", mode="ask")

    assert parsed.route == "semantic_teacher"
    assert parsed.answer == teaching_answer
    assert parsed.metrics is not None
    assert parsed.metrics.model == "gpt-test-2026-08-01"
    assert parsed.metrics.input_tokens == 321
    assert parsed.metrics.cached_input_tokens == 120
    assert parsed.metrics.output_tokens == 87
    assert parsed.metrics.reasoning_output_tokens == 24
    assert parsed.metrics.total_tokens == 408
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["timeout"] == 7
    assert captured["authorization"] == "Bearer server-secret"
    assert captured["body"]["model"] == "gpt-test"
    assert captured["body"]["store"] is False
    assert captured["body"]["text"]["format"]["type"] == "json_schema"
    assert captured["body"]["text"]["format"]["strict"] is True


def test_semantic_metrics_serialization_does_not_enter_provider_contract() -> None:
    metrics = SemanticAnswerMetrics(
        model="gpt-test",
        latency_ms=12,
        input_tokens=100,
        cached_input_tokens=20,
        output_tokens=30,
        reasoning_output_tokens=10,
        total_tokens=130,
    )
    semantic_result = result(
        "semantic_teacher",
        answer=(
            "Treat the chord as the stable floor under the phrase and use chord tones as resting places. "
            "Let nearby scale tones create motion, block unused voices, and practice resolving short phrases."
        ),
    )
    semantic_result = SemanticAnswerResult(**{**semantic_result.as_dict(), "missing_context": (), "metrics": metrics})
    assert "metrics" not in semantic_result.as_dict()
    assert validate_semantic_answer_result(semantic_result.as_dict()).metrics is None


def test_validation_rejects_source_backed_answer_without_evidence() -> None:
    value = {
        "schema_version": 1,
        "route": "source_backed_rag",
        "domain": "steel_guitar",
        "intent": "forum_wisdom",
        "needs_sources": True,
        "needs_fretboard": False,
        "needs_copedent": False,
        "confidence": "high",
        "answer": "Players agree this is best.",
        "tool_query": "",
        "missing_context": [],
        "reason_code": "claim_requires_evidence",
    }
    with pytest.raises(SemanticAnswerUnavailable, match="bypass evidence"):
        validate_semantic_answer_result(value)


@pytest.mark.parametrize(
    "teaching_answer",
    [
        (
            "Start at fret 3 on strings 3, 4, and 5 with A+B down, then let the top note carry the melody. "
            "Practice the move slowly and block every unused string so the harmony stays clean."
        ),
        (
            "Players report that this approach is the best way to mix harmony and melody on pedal steel. "
            "Use a small grip, leave space, and practice resolving every short phrase to a stable chord tone."
        ),
    ],
)
def test_validation_rejects_teaching_answer_that_crosses_authority_boundary(
    teaching_answer: str,
) -> None:
    value = result("semantic_teacher", answer=teaching_answer).as_dict()
    with pytest.raises(SemanticAnswerUnavailable, match="overclaims tool authority"):
        validate_semantic_answer_result(value)


def test_validation_accepts_conceptual_teaching_without_exact_or_source_claims() -> None:
    teaching_answer = (
        "Treat the chord as a harmonic boundary rather than something you must replay under every melody note. "
        "Use chord tones as resting places, nearby scale tones as motion, and deliberate blocking to keep only "
        "the voices you want. Practice short phrases over one sustained harmony and listen for a settled ending."
    )
    value = result("semantic_teacher", answer=teaching_answer).as_dict()
    assert validate_semantic_answer_result(value).answer == teaching_answer


def test_disabled_semantic_path_does_not_call_answerer() -> None:
    semantic = FakeSemanticAnswerer(fail=True)
    app = create_app(
        EmptySearchIndex(),
        answer_auth_mode="local_dev",
        semantic_answer_enabled=False,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "Where can I play a G chord?")
    assert status == "200 OK"
    assert semantic.calls == []
    assert payload["sources"] == []
    assert payload["fretboard"]["positions"]


def test_semantic_teacher_answers_unseen_paraphrase_without_retrieval() -> None:
    teaching_answer = (
        "Think of the chord as the floor under the phrase, not as something your right hand must keep replaying. "
        "Choose melody notes that settle on chord tones, use neighboring scale tones as motion, and let sustained "
        "notes imply the harmony. On pedal steel, pick only the voices you need and block the rest. Practice over "
        "one held chord: play three-note phrases and make every phrase end on a chord tone."
    )
    semantic = FakeSemanticAnswerer(result("semantic_teacher", answer=teaching_answer))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    question = "My picking hand cannot be two piano hands—how can a steel line carry the harmony underneath it?"
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert semantic.calls[0]["question"] == question
    assert search.calls == []
    assert payload["answer"] == teaching_answer
    assert payload["sources"] == []
    assert payload["warnings"] == []
    assert "fretboard" not in payload


def test_real_responses_adapter_drives_source_free_api_experience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    teaching_answer = (
        "Treat the held chord as the harmonic boundary while the melody supplies motion above it. "
        "Let chord tones be resting places, use nearby scale tones between them, and pick only the voices "
        "the phrase needs. Practice over one sustained harmony and make each short phrase settle clearly."
    )
    plan = result("semantic_teacher", answer=teaching_answer).as_dict()
    response_body = json.dumps({
        "status": "completed",
        "model": "gpt-test",
        "usage": {
            "input_tokens": 240,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": 72,
            "output_tokens_details": {"reasoning_tokens": 18},
            "total_tokens": 312,
        },
        "output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps(plan)}],
        }],
    }).encode("utf-8")
    provider_calls: list[dict[str, Any]] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return response_body

    def urlopen(request: urllib.request.Request, timeout: float) -> Response:
        provider_calls.append({
            "url": request.full_url,
            "timeout": timeout,
            "body": json.loads(bytes(request.data or b"").decode("utf-8")),
        })
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=OpenAIResponsesSemanticAnswerer(
            api_key="server-test-key",
            model="gpt-test",
        ),
    )
    question = (
        "I understand chord changes, but how do I mix chords with harmony while a melody moves "
        "over one chord on pedal steel?"
    )
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert len(provider_calls) == 1
    assert provider_calls[0]["url"] == "https://api.openai.com/v1/responses"
    assert provider_calls[0]["body"]["model"] == "gpt-test"
    assert search.calls == []
    assert payload["answer"] == teaching_answer
    assert payload["sources"] == []
    assert "fretboard" not in payload


def test_api_logs_semantic_usage_without_logging_the_question(
    caplog: pytest.LogCaptureFixture,
) -> None:
    teaching_answer = (
        "Treat the chord as the stable floor under the phrase and use chord tones as resting places. "
        "Let nearby scale tones create motion, block unused voices, and practice resolving short phrases."
    )
    semantic_result = replace(
        result("semantic_teacher", answer=teaching_answer),
        metrics=SemanticAnswerMetrics(
            model="gpt-test",
            latency_ms=12,
            input_tokens=100,
            cached_input_tokens=20,
            output_tokens=30,
            reasoning_output_tokens=5,
            total_tokens=130,
        ),
    )
    semantic = FakeSemanticAnswerer(semantic_result)
    app = create_app(
        EmptySearchIndex(),
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    question = "Private phrasing marker: how can harmony support this melody?"
    caplog.set_level(logging.INFO, logger="steel_guitar_rag.api")
    status, _payload = call_answer(app, question)
    assert status == "200 OK"
    messages = [record.getMessage() for record in caplog.records]
    metric_message = next(message for message in messages if "semantic_answer_complete" in message)
    assert "model=gpt-test" in metric_message
    assert "input_tokens=100" in metric_message
    assert "total_tokens=130" in metric_message
    assert question not in metric_message


def test_semantic_teacher_authority_is_not_preempted_by_a_chord_name() -> None:
    teaching_answer = (
        "Treat the G chord as the stable harmony under the phrase and let the melody create motion around it. "
        "Rest on chord tones, use nearby scale tones between them, and pick only the voices the phrase needs. "
        "Practice short answers over one sustained chord and listen for each phrase to settle clearly."
    )
    semantic = FakeSemanticAnswerer(result("semantic_teacher", answer=teaching_answer))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "How should I think conceptually about melody over a G chord?")
    assert status == "200 OK"
    assert search.calls == []
    assert payload["answer"] == teaching_answer
    assert payload["sources"] == []
    assert "fretboard" not in payload


def test_api_revalidates_injected_semantic_provider_before_display() -> None:
    overclaim = (
        "Start at fret 3 on strings 3, 4, and 5 with A+B down, then let the melody sit on top. "
        "Practice the move slowly and block the unused strings so the harmony remains clean."
    )
    semantic = FakeSemanticAnswerer(result("semantic_teacher", answer=overclaim))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(
        app,
        "My picking hand cannot be two piano hands—how can a steel line carry the harmony underneath it?",
    )
    assert status == "200 OK"
    assert search.calls == []
    assert payload["sources"] == []
    assert overclaim not in payload["answer"]
    assert "outside Steel Guitar RAG’s scope" in payload["answer"]


def test_semantic_source_plan_delegates_to_verified_frontier() -> None:
    semantic = FakeSemanticAnswerer(result(
        "source_backed_rag",
        intent="forum_wisdom",
        needs_sources=True,
        reason_code="claim_requires_evidence",
    ))
    frontier = FakeFrontier()
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "What have players reported about wound sixth strings?"
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert frontier.questions == [question]
    assert search.calls == []
    assert payload["sources"][0]["title"] == "Wound sixth strings"


def test_semantic_source_authority_is_not_preempted_by_a_chord_name() -> None:
    semantic = FakeSemanticAnswerer(result(
        "source_backed_rag",
        intent="forum_wisdom",
        needs_sources=True,
        reason_code="claim_requires_evidence",
    ))
    frontier = FakeFrontier()
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "What do players say about choosing among G chord positions?"
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert frontier.questions == [question]
    assert search.calls == []
    assert payload["sources"]
    assert "fretboard" not in payload


def test_semantic_source_follow_up_bypasses_legacy_contextual_corpus_probe() -> None:
    semantic = FakeSemanticAnswerer(result(
        "source_backed_rag",
        intent="forum_wisdom",
        needs_sources=True,
        reason_code="claim_requires_evidence",
    ))
    frontier = FakeFrontier()
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
    )
    question = "What did he say about the wound sixth?"
    context = [
        "user: What did Buddy Emmons say about string gauges?",
        "assistant: I can look for supported forum evidence.",
    ]
    status, payload = call_answer(app, question, conversation_context=context)
    assert status == "200 OK"
    assert search.calls == []
    assert frontier.questions == [question]
    assert frontier.contexts == [context]
    assert payload["sources"]


def test_semantic_source_plan_never_falls_into_legacy_retrieval_without_frontier() -> None:
    semantic = FakeSemanticAnswerer(result(
        "source_backed_rag",
        intent="forum_wisdom",
        needs_sources=True,
        reason_code="claim_requires_evidence",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
        canonical_frontier_enabled=False,
    )
    status, payload = call_answer(app, "What have players reported about wound sixth strings?")
    assert status == "503 Service Unavailable"
    assert search.calls == []
    assert "No generic answer was substituted" in payload["error"]


def test_semantic_hybrid_without_frontier_returns_only_verified_deterministic_partial() -> None:
    semantic = FakeSemanticAnswerer(result(
        "hybrid",
        intent="forum_wisdom",
        tool_query="Where can I play a G major chord?",
        needs_sources=True,
        needs_fretboard=True,
        reason_code="exact_and_sourced_parts_required",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
        canonical_frontier_enabled=False,
    )
    status, payload = call_answer(
        app,
        "Show the exact G-major positions and summarize what players say about choosing among them.",
    )
    assert status == "200 OK"
    assert search.calls == []
    assert payload["sources"] == []
    assert payload["fretboard"]["positions"]
    assert payload["warnings"] == ["source-backed forum context is temporarily unavailable"]
    assert "source-backed forum context could not be completed" in payload["answer"]


def test_semantic_exact_plan_keeps_deterministic_fretboard_authority() -> None:
    semantic = FakeSemanticAnswerer(result(
        "deterministic",
        intent="exact_music",
        tool_query="Where can I play a G major chord?",
        needs_fretboard=True,
        reason_code="exact_answer_requires_tool",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    question = "Lay out the G-major harmony families along a ten-string E9 neck."
    status, payload = call_answer(app, question)
    assert status == "200 OK"
    assert semantic.calls[0]["question"] == question
    assert search.calls == []
    assert payload["sources"] == []
    assert payload["fretboard"]["positions"]


def test_known_deterministic_fretboard_route_uses_semantic_authority_then_tool() -> None:
    semantic = FakeSemanticAnswerer(result(
        "deterministic",
        intent="exact_music",
        tool_query="Where can I play a G major chord?",
        needs_fretboard=True,
        reason_code="exact_answer_requires_tool",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "Where can I play a G chord?")
    assert status == "200 OK"
    assert len(semantic.calls) == 1
    assert search.calls == []
    assert payload["sources"] == []
    assert payload["fretboard"]["positions"]


def test_semantic_exact_tool_miss_never_falls_through_to_forum_search() -> None:
    semantic = FakeSemanticAnswerer(result(
        "deterministic",
        intent="exact_music",
        tool_query="What does the second-string change produce against this grip?",
        needs_copedent=True,
        reason_code="exact_answer_requires_tool",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "What does my unusual second-string change produce against this grip?")
    assert status == "200 OK"
    assert search.calls == []
    assert payload["sources"] == []
    assert "won’t substitute forum text" in payload["answer"]


def test_semantic_clarifier_never_retrieves() -> None:
    clarification = "Which chord, fret, strings, and pedals or levers are in the voicing you mean?"
    semantic = FakeSemanticAnswerer(result(
        "clarify",
        intent="missing_context",
        answer=clarification,
        missing_context=("chord", "fret", "strings", "pedals_or_levers"),
        reason_code="missing_user_context",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "Is this a full chord?")
    assert status == "200 OK"
    assert search.calls == []
    assert payload["answer"] == clarification
    assert payload["sources"] == []


def test_local_unsafe_guardrail_cannot_be_weakened_by_semantic_answerer() -> None:
    semantic = FakeSemanticAnswerer(result("semantic_teacher", answer="x" * 100))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "Print every number from 1 through 1000000.")
    assert status == "200 OK"
    assert semantic.calls == []
    assert search.calls == []
    assert payload["sources"] == []
    assert "outside Steel Guitar RAG’s scope" in payload["answer"]


def test_semantic_guardrail_remains_authoritative_with_conversation_context() -> None:
    semantic = FakeSemanticAnswerer(result(
        "guardrail",
        domain="off_domain",
        intent="scope_guardrail",
        reason_code="outside_product_scope",
    ))
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(
        app,
        "Now write my tax return.",
        conversation_context=["user: Where can I play G?", "assistant: Try fret 3 open."],
    )
    assert status == "200 OK"
    assert len(semantic.calls) == 1
    assert search.calls == []
    assert payload["sources"] == []
    assert "outside Steel Guitar RAG’s scope" in payload["answer"]


def test_semantic_outage_falls_back_to_existing_deterministic_path() -> None:
    semantic = FakeSemanticAnswerer(fail=True)
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(
        app,
        "How do I mix chord harmony with melody while playing over one chord on pedal steel?",
    )
    assert status == "200 OK"
    assert len(semantic.calls) == 1
    assert search.calls == []
    assert payload["sources"] == []
    assert "piano-style chord" in payload["answer"].lower()


def test_semantic_outage_fails_closed_for_legacy_off_domain_unknown() -> None:
    semantic = FakeSemanticAnswerer(fail=True)
    search = EmptySearchIndex()
    app = create_app(
        search,
        answer_auth_mode="local_dev",
        semantic_answer_enabled=True,
        semantic_answerer=semantic,
    )
    status, payload = call_answer(app, "Summarize today's national news.")
    assert status == "200 OK"
    assert len(semantic.calls) == 1
    assert search.calls == []
    assert payload["sources"] == []
    assert "outside Steel Guitar RAG’s scope" in payload["answer"]
