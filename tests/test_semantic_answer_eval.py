from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.run_semantic_answer_eval import evaluate_cases, load_cases
from steel_guitar_rag.semantic_answer_orchestrator import SemanticAnswerResult


BANK = Path("evals/semantic_answer_authority_v1.jsonl")


class EchoExpectedAnswerer:
    def __init__(self, cases: list[dict[str, Any]]) -> None:
        self.by_prompt = {case["prompt"]: case for case in cases}

    def answer(self, prompt: str, **_kwargs: Any) -> SemanticAnswerResult:
        case = self.by_prompt[prompt]
        route = case["expected_route"]
        tool_query = " ".join(case.get("tool_query_contains") or ())
        return SemanticAnswerResult(
            schema_version=1,
            route=route,
            domain="off_domain" if route == "guardrail" else "steel_guitar",
            intent="scope_guardrail" if route == "guardrail" else "conceptual_teaching",
            needs_sources=route in {"source_backed_rag", "hybrid"},
            needs_fretboard=route in {"deterministic", "hybrid"},
            needs_copedent=False,
            confidence="high",
            answer="",
            tool_query=tool_query,
            missing_context=(),
            reason_code="outside_product_scope" if route == "guardrail" else "general_teaching_is_source_free",
        )


def test_semantic_authority_bank_has_balanced_routes_and_unique_ids() -> None:
    cases = load_cases(BANK)
    ids = [case["id"] for case in cases]
    routes = {case["expected_route"] for case in cases}
    assert len(cases) >= 30
    assert len(ids) == len(set(ids))
    assert routes == {
        "semantic_teacher",
        "deterministic",
        "source_backed_rag",
        "hybrid",
        "clarify",
        "guardrail",
    }


def test_semantic_authority_evaluator_scores_routes_and_tool_restatenents() -> None:
    cases = load_cases(BANK)
    report = evaluate_cases(EchoExpectedAnswerer(cases), cases)
    assert report["case_count"] == len(cases)
    assert report["failed"] == 0
    assert report["pass_rate"] == 1.0
