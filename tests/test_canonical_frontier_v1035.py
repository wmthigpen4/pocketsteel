from __future__ import annotations

import importlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "frontier_runtime/v1035"
REAL_SERVICE_ROOT = Path(
    os.environ.get(
        "STEEL_RAG_TEST_CANONICAL_FRONTIER_SERVICE_ROOT",
        Path.home() / ".steel-rag/services/canonical-frontier-v1034-fallback-20260806",
    )
).expanduser()


@pytest.fixture(autouse=True)
def frontier_paths() -> Any:
    additions = [str(OVERLAY)]
    if REAL_SERVICE_ROOT.is_dir():
        additions.append(str(REAL_SERVICE_ROOT))
    original = list(sys.path)
    sys.path[:0] = additions
    try:
        yield
    finally:
        sys.path[:] = original


def test_health_endpoint_state_is_read_only_and_dependency_aware() -> None:
    health_module = importlib.import_module("canonical_frontier_health_v2")
    state = health_module.FrontierHealthState(cooldown_seconds=1)
    assert state.snapshot()["status"] == "not_ready"
    state.mark_local_verified()
    state.mark_warmup(True)
    state.dependencies.update({
        "openai_credentials_present": True,
        "terra_structured_check_passed": True,
        "luna_structured_check_passed": True,
    })
    first = state.snapshot()
    second = state.snapshot()
    assert first == second
    assert first["status"] == "ready"


def test_circuit_allows_one_recovery_probe_after_cooldown() -> None:
    health_module = importlib.import_module("canonical_frontier_health_v2")
    state = health_module.FrontierHealthState(cooldown_seconds=1)
    state.open("provider_failure")
    state._open_until = 0.0
    state._probe_in_flight = True
    assert state.request_mode() == "normal"
    state._open_until = 1.0
    state._probe_in_flight = False
    assert state.request_mode() == "probe"
    assert state.request_mode() == "degraded"


@dataclass
class FakeSource:
    source_id: str
    text: str
    title: str
    source_system: str = "sgf_phpbb_current"
    url: str = "https://bb.steelguitarforum.com/viewtopic.php?t=1"
    author: str = "Test Author"
    date: str = ""
    fused_score: float = 0.5
    metadata: dict[str, Any] = field(default_factory=lambda: {"forum_name": "Pedal Steel"})


class FakeRetriever:
    def __init__(self, sources: list[FakeSource]) -> None:
        self.sources = sources
        self.limits: list[int] = []

    def retrieve(self, question: str, *, limit: int) -> tuple[list[FakeSource], float]:
        del question
        self.limits.append(limit)
        return self.sources[:limit], 1.0


def test_degraded_path_uses_same_top_ten_and_at_most_three_extracts() -> None:
    degraded_module = importlib.import_module("canonical_frontier_degraded_v2")
    sources = [
        FakeSource(
            source_id=f"steel-passage-v1:{index}",
            title=f"Wound sixth discussion {index}",
            text=(
                "A wound sixth string can require more changer travel when lowering G# to F#. "
                "The tradeoff depends on the guitar setup and desired tone."
            ),
        )
        for index in range(12)
    ]
    retriever = FakeRetriever(sources)
    runtime = type("Runtime", (), {
        "retriever": retriever,
        "architecture_name": "test-frontier",
    })()
    result = degraded_module.degraded_response(
        runtime, "What is the wound sixth string changer travel tradeoff?"
    )
    assert result is not None
    assert retriever.limits == [10]
    assert 1 <= len(result["claims"]) <= 3
    assert len(result["sources"]) == len(result["claims"])
    assert result["metadata"]["delivery_mode"] == "sgf_extractive_degraded"
    assert result["metadata"]["ranked_passage_limit"] == 10


def test_invalid_provider_output_opens_circuit_and_returns_local_evidence() -> None:
    api_module = importlib.import_module("canonical_frontier_http_api_v3")
    health_module = importlib.import_module("canonical_frontier_health_v2")
    source = FakeSource(
        source_id="steel-passage-v1:1",
        title="Wound sixth discussion",
        text=(
            "A wound sixth string can require more changer travel when lowering G# to F#. "
            "The tradeoff depends on the guitar setup and desired tone."
        ),
    )
    retriever = FakeRetriever([source])

    class InvalidOutputRuntime:
        architecture_name = "test-frontier"

        def __init__(self) -> None:
            self.retriever = retriever

        def answer(self, question: str, *, conversation_context: list[str]) -> dict[str, Any]:
            del question, conversation_context
            raise ValueError("invalid structured provider output")

    class CompletedTerraGateway:
        def begin_trace(self) -> None:
            return None

        def successful_stages(self) -> tuple[str, ...]:
            return ("primary",)

    health = health_module.FrontierHealthState(cooldown_seconds=1)
    health.mark_local_verified()
    health.mark_warmup(True)
    health.dependencies.update({
        "openai_credentials_present": True,
        "terra_structured_check_passed": True,
        "luna_structured_check_passed": True,
    })
    application = api_module.CanonicalFrontierHttpApplication(
        InvalidOutputRuntime(),
        CompletedTerraGateway(),
        health,
        token="test-token",
    )
    body = json.dumps({
        "schema_version": 1,
        "question": "What is the wound sixth string changer travel tradeoff?",
        "conversation_context": [],
    }).encode("utf-8")
    status, result = application.handle(
        "POST",
        "/v1/answer",
        {"authorization": "Bearer test-token"},
        body,
    )
    assert status == 200
    assert result["metadata"]["delivery_mode"] == "sgf_extractive_degraded"
    assert health.snapshot()["status"] == "not_ready"
    assert health.snapshot()["reason"] == "provider_output_invalid"


def _response(value: dict[str, Any], model: str) -> dict[str, Any]:
    return {
        "id": f"response-{model}",
        "model": model,
        "output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps(value)}],
        }],
    }


@pytest.mark.skipif(not REAL_SERVICE_ROOT.is_dir(), reason="frozen v1034 reference root unavailable")
@pytest.mark.parametrize("terra_abstains", [False, True])
def test_runtime_preserves_exact_top_ten_and_two_call_boundary(terra_abstains: bool) -> None:
    module = importlib.import_module("canonical_frontier_v1034_runtime_candidate")
    sources = [
        FakeSource(
            source_id=f"steel-passage-v1:{index}",
            title=f"Wound sixth discussion {index}",
            text="Test Author reported that a wound sixth string may need more changer travel.",
        )
        for index in range(10)
    ]
    retriever = FakeRetriever(sources)
    calls: list[tuple[str, dict[str, Any]]] = []

    def model_call(stage: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        del timeout
        calls.append((stage, payload))
        user = json.loads(str(payload["input"][1]["content"]))
        if stage == "primary":
            slots = user["query_contract"]["slots"]
            claim = {
                "claim_id": "c1",
                "subject": "a wound sixth string",
                "relation": "cause_effect",
                "object": "may need more changer travel",
                "qualifiers": [],
                "text": "Test Author reported that a wound sixth string may need more changer travel.",
                "exhaustive": False,
                "passage_ids": ["p001"],
            }
            value = {
                "case_id": user["case_id"],
                "mode": "abstain" if terra_abstains else "complete",
                "claims": [] if terra_abstains else [claim],
                "coverage": [{
                    "slot_id": slot["slot_id"],
                    "status": "unsupported" if terra_abstains else "supported",
                    "claim_ids": [] if terra_abstains else ["c1"],
                } for slot in slots],
                "response_note": "",
                "confidence": 0.0 if terra_abstains else 0.9,
                "ranked_passage_ids": [] if terra_abstains else ["p001"],
            }
            return _response(value, "gpt-5.6-terra")
        assert stage == "independent_relevance_entailment_verifier"
        value = {
            "batch_id": user["batch_id"],
            "verdicts": [{
                "pair_id": pair["pair_id"],
                "citation_entailed": True,
                "question_relevant": True,
                "confidence": 0.99,
            } for pair in user["pairs"]],
        }
        return _response(value, "gpt-5.6-luna")

    runtime = module.build_v1034_runtime(
        retriever=retriever,
        model_call=model_call,
        timeout_seconds=5,
    )
    result = runtime.answer("What causes extra changer travel with a wound sixth string?")
    assert retriever.limits == [10]
    terra_packet = json.loads(str(calls[0][1]["input"][1]["content"]))
    assert len(terra_packet["passages"]) == 10
    if terra_abstains:
        assert [stage for stage, _payload in calls] == ["primary"]
        assert result["claims"] == []
    else:
        assert [stage for stage, _payload in calls] == [
            "primary", "independent_relevance_entailment_verifier",
        ]
        assert result["claims"][0]["support_mode"] == (
            "independent_relevance_entailment_verifier"
        )
