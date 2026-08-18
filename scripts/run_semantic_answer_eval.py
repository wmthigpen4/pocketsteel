#!/usr/bin/env python3
"""Run the held-out semantic authority bank against the configured Responses model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from steel_guitar_rag.semantic_answer_orchestrator import (
    OpenAIResponsesSemanticAnswerer,
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
        result = answerer.answer(str(case["prompt"]), mode="ask", conversation_context=[])
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
            "passed": passed,
        })
    passed_count = sum(1 for row in rows if row["passed"])
    route_summary: dict[str, dict[str, int]] = {}
    for row in rows:
        route = str(row["expected_route"])
        summary = route_summary.setdefault(route, {"passed": 0, "total": 0})
        summary["total"] += 1
        summary["passed"] += int(bool(row["passed"]))
    return {
        "schema_version": 1,
        "case_count": len(rows),
        "passed": passed_count,
        "failed": len(rows) - passed_count,
        "pass_rate": passed_count / len(rows) if rows else 0.0,
        "route_summary": route_summary,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    report = evaluate_cases(OpenAIResponsesSemanticAnswerer.from_env(), load_cases(args.bank))
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
