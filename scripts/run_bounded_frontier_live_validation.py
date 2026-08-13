#!/usr/bin/env python3
"""Run the six fixed frontier release scenarios under hard request/cost caps."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


OWNER_MAX_RESPONSES_REQUESTS = 20
OWNER_MAX_COST_USD = 2.50
# The frozen Terra/Luna prompts use 800/700 maximum output tokens and ten
# bounded passages.  Thirty cents is a deliberately loose per-scenario reserve
# for deciding whether another fixed validation case may start.
SCENARIO_COST_RESERVE_USD = 0.30


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    question: str
    context: tuple[str, ...] = ()
    expected_mode: str | None = None


SCENARIOS = (
    Scenario(
        "injected_provider_outage",
        "What is the changer-travel tradeoff when using a wound sixth string on E9?",
    ),
    Scenario(
        "single_recovery_probe",
        "What is the changer-travel tradeoff when using a wound sixth string on E9?",
    ),
    Scenario("source_backed_biography", "Who was Buddy Emmons?"),
    Scenario(
        "contextual_followup",
        "What was his E9 setup?",
        (
            "User: Who was Buddy Emmons?",
            "Assistant: Buddy Emmons was an influential pedal-steel guitarist.",
        ),
    ),
    Scenario(
        "source_backed_product",
        "What do Steel Guitar Forum contributors say about the Benado Steel Dream 2?",
    ),
    Scenario(
        "unsupported_abstention",
        "Which Steel Guitar Forum contributor documented a Zm chord at fret 47 on E9?",
        expected_mode="abstain",
    ),
)


Transport = Callable[[str, str, dict[str, Any] | None, str], tuple[int, dict[str, Any]]]


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    token: str,
) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            status = int(response.status)
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        value = json.loads(exc.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Frontier validation received a non-object response.")
    return status, value


def _trace(result: dict[str, Any]) -> dict[str, Any]:
    metadata = result.get("metadata") or {}
    trace = metadata.get("provider_trace") or {}
    if not isinstance(trace, dict):
        raise RuntimeError("Frontier provider trace is missing.")
    return trace


def run_validation(
    *,
    base_url: str,
    token: str,
    max_requests: int,
    max_cost_usd: float,
    recovery_wait_seconds: float,
    expect_injected_recovery: bool,
    transport: Transport = request_json,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if max_requests > OWNER_MAX_RESPONSES_REQUESTS or max_requests < 1:
        raise ValueError("Responses request cap exceeds the owner-authorized maximum.")
    if max_cost_usd > OWNER_MAX_COST_USD or max_cost_usd <= 0:
        raise ValueError("Cost cap exceeds the owner-authorized maximum.")
    if not expect_injected_recovery:
        raise ValueError("The protected live gate requires controlled recovery injection.")

    base = base_url.rstrip("/")
    status, health = transport("GET", f"{base}/health/ready", None, "")
    if status != 200 or health.get("status") != "ready":
        raise RuntimeError("Frontier must be exactly ready before live validation.")
    startup = health.get("startup_provider_validation") or {}
    responses_requests = int(startup.get("responses_requests") or 0)
    actual_cost_usd = float(startup.get("actual_cost_usd") or 0.0)
    if startup.get("pricing_known") is not True:
        raise RuntimeError("Startup provider pricing could not be verified.")
    if responses_requests > max_requests or actual_cost_usd > max_cost_usd:
        raise RuntimeError("Startup checks already exceeded the validation budget.")

    rows: list[dict[str, Any]] = []
    for index, scenario in enumerate(SCENARIOS):
        if responses_requests + 2 > max_requests:
            raise RuntimeError("The next scenario could exceed the Responses request cap.")
        if actual_cost_usd + SCENARIO_COST_RESERVE_USD > max_cost_usd:
            raise RuntimeError("The next scenario could exceed the cost cap.")
        payload = {
            "schema_version": 1,
            "question": scenario.question,
            "conversation_context": list(scenario.context),
        }
        answer_status, answer = transport(
            "POST", f"{base}/v1/answer", payload, token
        )
        if answer_status != 200:
            raise RuntimeError(
                f"Scenario {scenario.scenario_id} returned HTTP {answer_status}."
            )
        delivery_mode = str((answer.get("metadata") or {}).get("delivery_mode") or "")
        trace = _trace(answer)
        if trace.get("pricing_known") is not True:
            raise RuntimeError(f"Scenario {scenario.scenario_id} has unknown pricing.")
        scenario_requests = int(trace.get("responses_requests") or 0)
        scenario_cost = float(trace.get("actual_cost_usd") or 0.0)
        if scenario_requests > 2:
            raise RuntimeError("A frontier answer crossed the two-request boundary.")
        responses_requests += scenario_requests
        actual_cost_usd += scenario_cost
        if responses_requests > max_requests or actual_cost_usd > max_cost_usd:
            raise RuntimeError("Live validation exceeded its hard budget.")

        if index == 0:
            if delivery_mode != "sgf_extractive_degraded" or scenario_requests != 0:
                raise RuntimeError("Injected provider failure did not enter local degraded mode.")
            sleeper(recovery_wait_seconds)
        else:
            if delivery_mode == "sgf_extractive_degraded":
                raise RuntimeError(f"Scenario {scenario.scenario_id} remained degraded.")
            if not trace.get("stages") or trace["stages"][0] != "primary":
                raise RuntimeError("Terra was not the first provider stage.")
            if scenario.expected_mode and answer.get("mode") != scenario.expected_mode:
                raise RuntimeError(
                    f"Scenario {scenario.scenario_id} did not {scenario.expected_mode}."
                )
        rows.append({
            "scenario_id": scenario.scenario_id,
            "mode": answer.get("mode"),
            "delivery_mode": delivery_mode or "verified_synthesis",
            "responses_requests": scenario_requests,
            "actual_cost_usd": scenario_cost,
            "source_count": len(answer.get("sources") or []),
        })

        if index == 1:
            recovered_status, recovered = transport(
                "GET", f"{base}/health/ready", None, ""
            )
            if recovered_status != 200 or recovered.get("status") != "ready":
                raise RuntimeError("The single recovery probe did not close the circuit.")

    return {
        "status": "bounded_frontier_live_validation_passed",
        "scenarios": rows,
        "scenario_count": len(rows),
        "responses_requests": responses_requests,
        "actual_cost_usd": actual_cost_usd,
        "request_cap": max_requests,
        "cost_cap_usd": max_cost_usd,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8772")
    parser.add_argument("--max-requests", type=int, default=OWNER_MAX_RESPONSES_REQUESTS)
    parser.add_argument("--max-cost-usd", type=float, default=OWNER_MAX_COST_USD)
    parser.add_argument("--recovery-wait-seconds", type=float, default=2.0)
    parser.add_argument("--expect-injected-recovery", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("STEEL_RAG_CANONICAL_FRONTIER_TOKEN", "").strip()
    if not token:
        raise SystemExit("STEEL_RAG_CANONICAL_FRONTIER_TOKEN is required.")
    result = run_validation(
        base_url=args.base_url,
        token=token,
        max_requests=args.max_requests,
        max_cost_usd=args.max_cost_usd,
        recovery_wait_seconds=args.recovery_wait_seconds,
        expect_injected_recovery=args.expect_injected_recovery,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
