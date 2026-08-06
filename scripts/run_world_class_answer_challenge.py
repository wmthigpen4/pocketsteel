#!/usr/bin/env python3
"""Capture and score the focused world-class Ask release challenge."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "evals/world_class_answer_challenge.yaml"
DEFAULT_FORBIDDEN = (
    "i need a more specific steel-guitar question",
    "no strong source match found",
    "[object object]",
    "deterministic map",
    "rules engine",
)
FIRST_PERSON_RE = re.compile(r"\b(?:I|I've|I'm|I'd|my|mine|we|we've|we're|our|ours)\b", re.I)


def load_cases(path: Path = DEFAULT_BANK) -> list[dict[str, Any]]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("challenge bank must be a version-1 mapping")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise ValueError("challenge bank must contain at least eight cases")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("every challenge case must be a mapping")
        missing = {"id", "question", "expected_route", "paid", "required_terms", "forbidden_terms"} - set(case)
        if missing:
            raise ValueError(f"challenge case missing fields: {sorted(missing)}")
        case_id = str(case["id"])
        if case_id in ids:
            raise ValueError(f"duplicate challenge id: {case_id}")
        ids.add(case_id)
    return cases


def score_case(case: dict[str, Any], status: int, payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    answer = str(payload.get("answer") or "")
    lowered = answer.lower()
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    if status != 200:
        failures.append(f"HTTP {status}: {payload.get('error') or 'request failed'}")
    for term in case.get("required_terms") or []:
        if str(term).lower() not in lowered:
            failures.append(f"missing required term: {term}")
    for term in (*DEFAULT_FORBIDDEN, *(case.get("forbidden_terms") or [])):
        if str(term).lower() in lowered:
            failures.append(f"forbidden term present: {term}")
    if case.get("require_fretboard") and not payload.get("fretboard"):
        failures.append("fretboard payload missing")
    if case.get("require_tab") and not (payload.get("tab_example") or payload.get("tabs")):
        failures.append("tablature payload missing")
    if case.get("require_sources") and not sources:
        failures.append("source cards missing")
    if case.get("require_sources") is False and sources:
        failures.append("unexpected source cards")
    if case.get("expected_route") in {"source_backed_rag", "hybrid"} and FIRST_PERSON_RE.search(answer):
        failures.append("source-backed answer contains first-person forum voice")
    return failures


def request_case(endpoint: str, case: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any], str, float]:
    body = json.dumps({
        "question": case["question"],
        "mode": "ask",
        "topK": 6,
        "conversationContext": list(case.get("conversation_context") or []),
    }).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Steel-Rag-Dev-Access-Role": "admin",
        },
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            trace_id = response.headers.get("X-Steel-Rag-Trace-Id", "")
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        status = exc.code
        trace_id = exc.headers.get("X-Steel-Rag-Trace-Id", "")
        payload = json.loads(exc.read().decode("utf-8"))
    return status, payload, trace_id, round(time.monotonic() - started, 3)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--endpoint", help="Optional /api/answer URL. Without it, only validate the bank.")
    parser.add_argument("--ids", nargs="*", help="Optional exact case ids to run.")
    parser.add_argument("--authorize-paid-cases", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=130.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    cases = load_cases(args.bank)
    if args.ids:
        requested = set(args.ids)
        cases = [case for case in cases if case["id"] in requested]
        missing = requested - {str(case["id"]) for case in cases}
        if missing:
            raise ValueError(f"unknown challenge ids: {sorted(missing)}")
    paid_count = sum(bool(case["paid"]) for case in cases)
    print(f"Validated {len(cases)} challenge cases ({paid_count} paid, {len(cases) - paid_count} local).")
    if not args.endpoint:
        return 0
    if paid_count > args.authorize_paid_cases:
        raise ValueError(
            f"run contains {paid_count} paid cases but only {args.authorize_paid_cases} were authorized"
        )

    results: list[dict[str, Any]] = []
    for case in cases:
        status, payload, trace_id, elapsed = request_case(args.endpoint, case, args.timeout)
        failures = score_case(case, status, payload)
        results.append({
            "id": case["id"],
            "expectedRoute": case["expected_route"],
            "paid": bool(case["paid"]),
            "status": "pass" if not failures else "fail",
            "httpStatus": status,
            "traceId": trace_id,
            "elapsedSeconds": elapsed,
            "failures": failures,
            "payload": payload,
        })
        print(f"{case['id']}: {'PASS' if not failures else 'FAIL'} ({elapsed:.3f}s)")

    report = {
        "schemaVersion": "world_class_answer_challenge_v1",
        "endpoint": args.endpoint,
        "caseCount": len(results),
        "paidCaseCount": paid_count,
        "passCount": sum(result["status"] == "pass" for result in results),
        "failCount": sum(result["status"] == "fail" for result in results),
        "results": results,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["failCount"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
