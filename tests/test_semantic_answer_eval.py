from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.run_semantic_answer_eval import evaluate_cases, load_cases
from dataclasses import replace

from steel_guitar_rag.semantic_answer_orchestrator import (
    SemanticAnswerMetrics,
    SemanticAnswerResult,
    SemanticAnswerUnavailable,
)


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


class OverclaimingTeacherAnswerer(EchoExpectedAnswerer):
    def answer(self, prompt: str, **kwargs: Any) -> SemanticAnswerResult:
        result = super().answer(prompt, **kwargs)
        if result.route != "semantic_teacher":
            return result
        return SemanticAnswerResult(
            **{
                **result.as_dict(),
                "answer": (
                    "Start at fret 3 on strings 3, 4, and 5, then resolve the melody there. "
                    "Practice slowly and block every unused voice so the harmony remains clear."
                ),
                "missing_context": (),
            }
        )


class MeteredAnswerer(EchoExpectedAnswerer):
    def answer(self, prompt: str, **kwargs: Any) -> SemanticAnswerResult:
        result = super().answer(prompt, **kwargs)
        return replace(
            result,
            metrics=SemanticAnswerMetrics(
                model="gpt-test",
                latency_ms=10,
                input_tokens=100,
                cached_input_tokens=20,
                output_tokens=30,
                reasoning_output_tokens=5,
                total_tokens=130,
            ),
        )


class OneUnavailableAnswerer(EchoExpectedAnswerer):
    def __init__(self, cases: list[dict[str, Any]]) -> None:
        super().__init__(cases)
        self.failed = False

    def answer(self, prompt: str, **kwargs: Any) -> SemanticAnswerResult:
        if not self.failed:
            self.failed = True
            raise SemanticAnswerUnavailable("test provider outage")
        return super().answer(prompt, **kwargs)


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
    assert report["route_summary"]["semantic_teacher"] == {"passed": 8, "total": 8}
    assert report["runtime_metrics"]["request_count"] == len(cases)
    assert report["runtime_metrics"]["provider_usage_reported_calls"] == 0


def test_semantic_authority_evaluator_fails_teacher_overreach() -> None:
    cases = load_cases(BANK)
    report = evaluate_cases(OverclaimingTeacherAnswerer(cases), cases)
    teacher_rows = [row for row in report["rows"] if row["expected_route"] == "semantic_teacher"]
    assert teacher_rows
    assert all(not row["passed"] for row in teacher_rows)
    assert all("exact fret coordinate" in row["authority_violations"] for row in teacher_rows)


def test_semantic_authority_evaluator_aggregates_provider_usage() -> None:
    cases = load_cases(BANK)
    report = evaluate_cases(MeteredAnswerer(cases), cases)
    metrics = report["runtime_metrics"]
    assert metrics["provider_usage_reported_calls"] == len(cases)
    assert metrics["models"] == ["gpt-test"]
    assert metrics["provider_latency_ms_total"] == len(cases) * 10
    assert metrics["input_tokens_total"] == len(cases) * 100
    assert metrics["cached_input_tokens_total"] == len(cases) * 20
    assert metrics["output_tokens_total"] == len(cases) * 30
    assert metrics["reasoning_output_tokens_total"] == len(cases) * 5
    assert metrics["tokens_total"] == len(cases) * 130


def test_semantic_authority_evaluator_records_expected_provider_failure_and_continues() -> None:
    cases = load_cases(BANK)
    report = evaluate_cases(OneUnavailableAnswerer(cases), cases)
    assert report["case_count"] == len(cases)
    assert report["failed"] == 1
    assert report["runtime_metrics"]["completed_count"] == len(cases) - 1
    assert report["rows"][0]["actual_route"] is None
    assert report["rows"][0]["error"] == "test provider outage"
