#!/usr/bin/env python3
"""Run the held-out semantic authority bank against the configured Responses model."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import time
from typing import Any, Iterable

from steel_guitar_rag.semantic_answer_orchestrator import (
    OpenAIResponsesSemanticAnswerer,
    SemanticAnswerUnavailable,
    semantic_teacher_authority_violations,
)


DEFAULT_BANK = Path("evals/semantic_answer_authority_v1.jsonl")


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        value = json.loads(raw_line)
        if not isinstance(value, dict) or not all(value.get(field) for field in ("id", "prompt", "expected_route")):
            raise ValueError(f"Invalid semantic eval row at {path}:{line_number}")
        cases.append(value)
    return cases


def evaluate_cases(answerer: Any, cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        started = time.monotonic()
        try:
            result = answerer.answer(
                str(case["prompt"]),
                mode="ask",
                conversation_context=[str(item) for item in case.get("conversation_context") or ()],
            )
        except SemanticAnswerUnavailable as exc:
            rows.append({
                "id": case["id"],
                "expected_route": case["expected_route"],
                "actual_route": None,
                "reason_code": None,
                "missing_tool_terms": list(case.get("tool_query_contains") or ()),
                "authority_violations": [],
                "latency_ms": round((time.monotonic() - started) * 1000),
                "provider_metrics": None,
                "error": str(exc),
                "passed": False,
            })
            continue
        elapsed_ms = round((time.monotonic() - started) * 1000)
        missing_tool_terms = [
            str(term)
            for term in case.get("tool_query_contains") or ()
            if str(term).casefold() not in result.tool_query.casefold()
        ]
        authority_violations = (
            list(semantic_teacher_authority_violations(result.answer))
            if result.route == "semantic_teacher"
            else []
        )
        passed = (
            result.route == case["expected_route"]
            and not missing_tool_terms
            and not authority_violations
        )
        rows.append({
            "id": case["id"],
            "expected_route": case["expected_route"],
            "actual_route": result.route,
            "reason_code": result.reason_code,
            "missing_tool_terms": missing_tool_terms,
            "authority_violations": authority_violations,
            "latency_ms": elapsed_ms,
            "provider_metrics": result.metrics.as_dict() if result.metrics is not None else None,
            "error": None,
            "passed": passed,
        })
    passed_count = sum(1 for row in rows if row["passed"])
    route_summary: dict[str, dict[str, int]] = {}
    for row in rows:
        route = str(row["expected_route"])
        summary = route_summary.setdefault(route, {"passed": 0, "total": 0})
        summary["total"] += 1
        summary["passed"] += int(bool(row["passed"]))
    latencies = sorted(int(row["latency_ms"]) for row in rows)
    provider_metrics = [
        row["provider_metrics"]
        for row in rows
        if isinstance(row.get("provider_metrics"), dict)
    ]

    def token_total(field: str) -> int | None:
        values = [metrics.get(field) for metrics in provider_metrics]
        if not values or any(type(value) is not int for value in values):
            return None
        return sum(values)

    runtime_metrics = {
        "request_count": len(rows),
        "completed_count": sum(1 for row in rows if row["actual_route"] is not None),
        "provider_usage_reported_calls": len(provider_metrics),
        "models": sorted({str(metrics["model"]) for metrics in provider_metrics}),
        "evaluation_wall_latency_ms_total": sum(latencies),
        "evaluation_wall_latency_ms_median": (
            round(statistics.median(latencies)) if latencies else None
        ),
        "evaluation_wall_latency_ms_p95": (
            latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)] if latencies else None
        ),
        "provider_latency_ms_total": token_total("latency_ms"),
        "input_tokens_total": token_total("input_tokens"),
        "cached_input_tokens_total": token_total("cached_input_tokens"),
        "output_tokens_total": token_total("output_tokens"),
        "reasoning_output_tokens_total": token_total("reasoning_output_tokens"),
        "tokens_total": token_total("total_tokens"),
    }
    return {
        "schema_version": 1,
        "case_count": len(rows),
        "passed": passed_count,
        "failed": len(rows) - passed_count,
        "pass_rate": passed_count / len(rows) if rows else 0.0,
        "route_summary": route_summary,
        "runtime_metrics": runtime_metrics,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Run only the named case; repeat to select more than one.",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    cases = load_cases(args.bank)
    if args.case_id:
        selected_ids = set(args.case_id)
        cases = [case for case in cases if case["id"] in selected_ids]
        missing_ids = selected_ids - {str(case["id"]) for case in cases}
        if missing_ids:
            parser.error(f"unknown case id(s): {', '.join(sorted(missing_ids))}")
    report = evaluate_cases(OpenAIResponsesSemanticAnswerer.from_env(), cases)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
