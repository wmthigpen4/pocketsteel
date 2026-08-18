#!/usr/bin/env python3
"""Run the protected enabled-path semantic answer acceptance matrix."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "evals/semantic_answer_preview_smoke.yaml"
DEFAULT_ACCESS_JWT_ENV = "STEEL_RAG_PREVIEW_ACCESS_JWT"
AUTHORITIES = {
    "deterministic",
    "semantic_teacher",
    "source_backed_rag",
    "hybrid",
    "clarify",
    "guardrail",
}


def _validated_base_url(value: str) -> str:
    normalized = value.rstrip("/")
    parsed = urlsplit(normalized)
    loopback_http = parsed.scheme == "http" and parsed.hostname in {
        "127.0.0.1",
        "localhost",
        "::1",
    }
    if parsed.scheme != "https" and not loopback_http:
        raise ValueError("base URL must use HTTPS or loopback HTTP")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base URL must not contain credentials, query, or fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError("base URL must be an origin without a path")
    return normalized


def load_cases(path: Path = DEFAULT_BANK) -> list[dict[str, Any]]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("semantic preview bank must be a version-1 mapping")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise ValueError("semantic preview bank must contain at least eight cases")
    ids: set[str] = set()
    authorities: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("every semantic preview case must be a mapping")
        required = {
            "id",
            "authority",
            "question",
            "expect_sources",
            "expect_fretboard",
            "answer_min_chars",
            "required_terms",
            "forbidden_terms",
        }
        missing = required - set(case)
        if missing:
            raise ValueError(f"semantic preview case missing fields: {sorted(missing)}")
        case_id = str(case["id"])
        if case_id in ids:
            raise ValueError(f"duplicate semantic preview id: {case_id}")
        ids.add(case_id)
        authority = str(case["authority"])
        if authority not in AUTHORITIES:
            raise ValueError(f"unknown semantic authority: {authority}")
        authorities.add(authority)
        if case["expect_sources"] not in {"present", "absent"}:
            raise ValueError(f"invalid source expectation for {case_id}")
        if case["expect_fretboard"] not in {"present", "absent"}:
            raise ValueError(f"invalid fretboard expectation for {case_id}")
    if authorities != AUTHORITIES:
        raise ValueError(f"semantic preview bank must cover all authorities: {sorted(AUTHORITIES)}")
    return cases


def score_case(case: Mapping[str, Any], status: int, payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    answer = str(payload.get("answer") or "")
    lowered = answer.casefold()
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    fretboard_present = isinstance(payload.get("fretboard"), dict) and bool(payload["fretboard"])
    if status != 200:
        failures.append(f"HTTP {status}: {payload.get('error') or 'request failed'}")
    if len(answer) < int(case["answer_min_chars"]):
        failures.append(f"answer shorter than {case['answer_min_chars']} characters")
    if case["expect_sources"] == "present" and not sources:
        failures.append("source cards missing")
    if case["expect_sources"] == "absent" and sources:
        failures.append("unexpected source cards")
    if case["expect_fretboard"] == "present" and not fretboard_present:
        failures.append("fretboard payload missing")
    if case["expect_fretboard"] == "absent" and fretboard_present:
        failures.append("unexpected fretboard payload")
    if case.get("answer_must_end_with_question") and not answer.rstrip().endswith("?"):
        failures.append("answer is not a clarifying question")
    for term in case.get("required_terms") or ():
        if str(term).casefold() not in lowered:
            failures.append(f"missing required term: {term}")
    for term in case.get("forbidden_terms") or ():
        if str(term).casefold() in lowered:
            failures.append(f"forbidden term present: {term}")
    if "[object object]" in lowered:
        failures.append("object serialization leaked into answer")
    return failures


def _headers(
    *,
    auth_mode: str,
    access_jwt_env: str,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if auth_mode == "dev":
        headers["X-Steel-Rag-Dev-Access-Role"] = "admin"
        return headers
    values = env or os.environ
    token = str(values.get(access_jwt_env) or "").strip()
    if not token:
        raise ValueError(f"{access_jwt_env} is required for protected preview smoke")
    headers["Cf-Access-Jwt-Assertion"] = token
    return headers


def _request_json(
    url: str,
    *,
    headers: Mapping[str, str],
    timeout: float,
    payload: Mapping[str, Any] | None = None,
) -> tuple[int, dict[str, Any], str, int]:
    request_headers = dict(headers)
    body: bytes | None = None
    method = "GET"
    if payload is not None:
        method = "POST"
        request_headers["Content-Type"] = "application/json"
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    started = time.monotonic()
    response_body = b""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            trace_id = response.headers.get("X-Steel-Rag-Trace-Id", "")
            response_body = response.read(2_000_001)
    except urllib.error.HTTPError as exc:
        status = exc.code
        trace_id = exc.headers.get("X-Steel-Rag-Trace-Id", "")
        response_body = exc.read(2_000_001)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return (
            0,
            {"error": f"request failed: {type(exc).__name__}"},
            "",
            round((time.monotonic() - started) * 1000),
        )
    if len(response_body) > 2_000_000:
        response_payload: Any = {"error": "response exceeded two megabytes"}
    else:
        try:
            response_payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            response_payload = {"error": "endpoint returned invalid JSON"}
    if not isinstance(response_payload, dict):
        response_payload = {"error": "endpoint returned non-object JSON"}
    return status, response_payload, trace_id, round((time.monotonic() - started) * 1000)


def run_smoke(
    *,
    base_url: str,
    cases: list[dict[str, Any]],
    headers: Mapping[str, str],
    timeout: float,
) -> dict[str, Any]:
    normalized_base = _validated_base_url(base_url)
    session_status, session, _trace, session_latency = _request_json(
        f"{normalized_base}/api/session",
        headers=headers,
        timeout=timeout,
    )
    features_value = session.get("features")
    features: dict[str, Any] = features_value if isinstance(features_value, dict) else {}
    activation_failures: list[str] = []
    if session_status != 200:
        activation_failures.append(f"session HTTP {session_status}")
    if features.get("semanticAnswer") is not True:
        activation_failures.append("semanticAnswer feature is not active")
    if features.get("canonicalFrontier") is not True:
        activation_failures.append("canonicalFrontier feature is not active")
    if activation_failures:
        return {
            "schema_version": 1,
            "base_url": normalized_base,
            "activation": {
                "status": "fail",
                "latency_ms": session_latency,
                "features": {
                    "semanticAnswer": features.get("semanticAnswer") is True,
                    "canonicalFrontier": features.get("canonicalFrontier") is True,
                },
                "failures": activation_failures,
            },
            "requested_case_count": len(cases),
            "case_count": 0,
            "passed": 0,
            "failed": 1,
            "results": [],
        }

    results: list[dict[str, Any]] = []
    for case in cases:
        status, payload, trace_id, latency_ms = _request_json(
            f"{normalized_base}/api/answer",
            headers=headers,
            timeout=timeout,
            payload={
                "question": case["question"],
                "mode": "ask",
                "topK": 6,
                "conversationContext": list(case.get("conversation_context") or ()),
            },
        )
        failures = score_case(case, status, payload)
        results.append({
            "id": case["id"],
            "authority": case["authority"],
            "status": "pass" if not failures else "fail",
            "http_status": status,
            "trace_id": trace_id,
            "latency_ms": latency_ms,
            "failures": failures,
            "payload": payload,
        })
    failed_cases = sum(result["status"] == "fail" for result in results)
    return {
        "schema_version": 1,
        "base_url": normalized_base,
        "activation": {
            "status": "pass" if not activation_failures else "fail",
            "latency_ms": session_latency,
            "features": {
                "semanticAnswer": features.get("semanticAnswer") is True,
                "canonicalFrontier": features.get("canonicalFrontier") is True,
            },
            "failures": activation_failures,
        },
        "requested_case_count": len(cases),
        "case_count": len(results),
        "passed": len(results) - failed_cases,
        "failed": failed_cases + int(bool(activation_failures)),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--base-url", help="Protected or local app origin. Without it, validate only.")
    parser.add_argument("--auth-mode", choices=("access-jwt", "dev"), default="access-jwt")
    parser.add_argument("--access-jwt-env", default=DEFAULT_ACCESS_JWT_ENV)
    parser.add_argument("--authorize-answer-requests", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=140.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    cases = load_cases(args.bank)
    print(f"Validated {len(cases)} semantic preview cases across all six authorities.")
    if not args.base_url:
        return 0
    if args.authorize_answer_requests != len(cases):
        raise ValueError(
            f"smoke requires exact authorization for {len(cases)} answer requests; "
            f"received {args.authorize_answer_requests}"
        )
    headers = _headers(auth_mode=args.auth_mode, access_jwt_env=args.access_jwt_env)
    report = run_smoke(
        base_url=args.base_url,
        cases=cases,
        headers=headers,
        timeout=max(1.0, args.timeout),
    )
    for result in report["results"]:
        print(f"{result['id']}: {result['status'].upper()} ({result['latency_ms']}ms)")
    print(
        f"Activation: {report['activation']['status'].upper()}; "
        f"cases: {report['passed']} passed, {report['case_count'] - report['passed']} failed."
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
