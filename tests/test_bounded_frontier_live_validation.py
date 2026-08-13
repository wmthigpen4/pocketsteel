from __future__ import annotations

import copy
from typing import Any

import pytest

from scripts.run_bounded_frontier_live_validation import (
    OWNER_MAX_COST_USD,
    OWNER_MAX_RESPONSES_REQUESTS,
    SCENARIOS,
    run_validation,
)


def test_fixed_live_gate_is_six_scenarios_and_enforces_owner_caps() -> None:
    assert len(SCENARIOS) == 6
    with pytest.raises(ValueError, match="request cap"):
        run_validation(
            base_url="http://127.0.0.1:1",
            token="test",
            max_requests=OWNER_MAX_RESPONSES_REQUESTS + 1,
            max_cost_usd=OWNER_MAX_COST_USD,
            recovery_wait_seconds=0,
            expect_injected_recovery=True,
        )
    with pytest.raises(ValueError, match="Cost cap"):
        run_validation(
            base_url="http://127.0.0.1:1",
            token="test",
            max_requests=OWNER_MAX_RESPONSES_REQUESTS,
            max_cost_usd=OWNER_MAX_COST_USD + 0.01,
            recovery_wait_seconds=0,
            expect_injected_recovery=True,
        )


def test_fixed_live_gate_accounts_startup_recovery_and_no_third_calls() -> None:
    ready = {
        "status": "ready",
        "startup_provider_validation": {
            "responses_requests": 2,
            "actual_cost_usd": 0.001,
            "pricing_known": True,
        },
    }
    calls: list[str] = []
    answer_index = 0

    def transport(
        method: str,
        url: str,
        payload: dict[str, Any] | None,
        token: str,
    ) -> tuple[int, dict[str, Any]]:
        nonlocal answer_index
        del payload, token
        calls.append(f"{method} {url}")
        if method == "GET":
            return 200, copy.deepcopy(ready)
        scenario = SCENARIOS[answer_index]
        answer_index += 1
        if scenario.scenario_id == "injected_provider_outage":
            return 200, {
                "mode": "partial",
                "sources": [{"source_id": "p1"}],
                "metadata": {
                    "delivery_mode": "sgf_extractive_degraded",
                    "provider_trace": {
                        "responses_requests": 0,
                        "stages": [],
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "actual_cost_usd": 0.0,
                        "pricing_known": True,
                    },
                },
            }
        expected_mode = scenario.expected_mode or "complete"
        stages = ["primary"] if expected_mode == "abstain" else [
            "primary",
            "independent_relevance_entailment_verifier",
        ]
        degraded_abstention = expected_mode == "abstain"
        return 200, {
            "mode": "partial" if degraded_abstention else expected_mode,
            "sources": [{"source_id": "p1"}],
            "metadata": {
                "delivery_mode": (
                    "sgf_extractive_degraded" if degraded_abstention else ""
                ),
                "provider_trace": {
                    "responses_requests": len(stages),
                    "stages": stages,
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "actual_cost_usd": 0.01,
                    "pricing_known": True,
                },
            },
        }

    result = run_validation(
        base_url="http://127.0.0.1:8772",
        token="test-token",
        max_requests=OWNER_MAX_RESPONSES_REQUESTS,
        max_cost_usd=OWNER_MAX_COST_USD,
        recovery_wait_seconds=0,
        expect_injected_recovery=True,
        transport=transport,
        sleeper=lambda _seconds: None,
    )
    assert result["status"] == "bounded_frontier_live_validation_passed"
    assert result["scenario_count"] == 6
    assert result["responses_requests"] == 11
    assert result["actual_cost_usd"] == pytest.approx(0.051)
    assert result["scenarios"][-1]["safe_degraded_abstention"] is True
    assert answer_index == 6
    assert sum(call.startswith("GET ") for call in calls) == 2
