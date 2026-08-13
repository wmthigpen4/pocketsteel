#!/usr/bin/env python3
"""Dependency-aware readiness and provider circuit state for frontier v1035."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

TERRA_MODEL = "gpt-5.6-terra"
LUNA_MODEL = "gpt-5.6-luna"
_SAFE_CODE_RE = re.compile(r"\[([a-zA-Z0-9_-]{1,96})\]")
_PRICES_PER_TOKEN = {
    # (uncached input, cached input, cache write, output).  Cache writes are
    # 1.25x input.  These are the August 2026 official GPT-5.6 rates.
    TERRA_MODEL: (2.50e-6, 0.25e-6, 3.125e-6, 15.00e-6),
    LUNA_MODEL: (1.00e-6, 0.10e-6, 1.25e-6, 6.00e-6),
}


class ProviderCallError(RuntimeError):
    """A provider error stripped to bounded operational metadata."""

    def __init__(
        self,
        stage: str,
        *,
        code: str = "provider_request_failed",
        http_status: int | None = None,
        retryable: bool = True,
    ) -> None:
        super().__init__(f"Provider stage {stage} failed.")
        self.stage = stage
        self.code = code
        self.http_status = http_status
        self.retryable = retryable


def _safe_provider_error(stage: str, exc: BaseException) -> ProviderCallError:
    match = _SAFE_CODE_RE.search(str(exc))
    code = match.group(1) if match else "provider_request_failed"
    cause = getattr(exc, "__cause__", None)
    status = getattr(cause, "code", None)
    retryable = status is None or int(status) >= 500 or int(status) == 429
    return ProviderCallError(
        stage,
        code=code,
        http_status=int(status) if status is not None else None,
        retryable=retryable,
    )


def _usage_record(
    stage: str,
    response: dict[str, Any],
    *,
    requested_model: str = "",
) -> dict[str, Any]:
    model = str(response.get("model") or requested_model)
    pricing_model = model if model in _PRICES_PER_TOKEN else requested_model
    usage = response.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    details = usage.get("input_tokens_details") or {}
    cached_tokens = int(details.get("cached_tokens") or 0)
    cache_write_tokens = int(details.get("cache_write_tokens") or 0)
    uncached_tokens = max(0, input_tokens - cached_tokens - cache_write_tokens)
    if pricing_model not in _PRICES_PER_TOKEN:
        actual_cost = 0.0
    else:
        input_rate, cached_rate, cache_write_rate, output_rate = _PRICES_PER_TOKEN[
            pricing_model
        ]
        actual_cost = (
            uncached_tokens * input_rate
            + cached_tokens * cached_rate
            + cache_write_tokens * cache_write_rate
            + output_tokens * output_rate
        )
    return {
        "stage": stage,
        "model": model,
        "pricing_known": pricing_model in _PRICES_PER_TOKEN,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "actual_cost_usd": actual_cost,
    }


class ProviderGateway:
    """Wrap the existing Responses call without changing its request contract."""

    def __init__(self) -> None:
        self._local = threading.local()
        self._inject_first_failure = (
            os.environ.get("STEEL_RAG_FRONTIER_VALIDATION_FAIL_FIRST_PROVIDER_CALL") == "1"
        )
        self._injected = False

    def begin_trace(self) -> None:
        self._local.stages = []
        self._local.request_attempts = 0
        self._local.records = []

    def successful_stages(self) -> tuple[str, ...]:
        return tuple(getattr(self._local, "stages", ()))

    def trace_summary(self) -> dict[str, Any]:
        records = list(getattr(self._local, "records", ()))
        return {
            "responses_requests": int(getattr(self._local, "request_attempts", 0)),
            "stages": list(getattr(self._local, "stages", ())),
            "input_tokens": sum(int(row["input_tokens"]) for row in records),
            "output_tokens": sum(int(row["output_tokens"]) for row in records),
            "actual_cost_usd": sum(float(row["actual_cost_usd"]) for row in records),
            "pricing_known": all(bool(row["pricing_known"]) for row in records),
        }

    def __call__(self, stage: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        from project_answer_relation_openai_v2 import api_key, call_api

        if self._inject_first_failure and not self._injected and stage == "primary":
            self._injected = True
            raise ProviderCallError(
                stage,
                code="validation_injected_provider_failure",
                retryable=True,
            )
        self._local.request_attempts = int(
            getattr(self._local, "request_attempts", 0)
        ) + 1
        try:
            response = call_api(api_key(), payload, timeout=timeout)
        except (RuntimeError, OSError, TimeoutError) as exc:
            raise _safe_provider_error(stage, exc) from exc
        stages = list(getattr(self._local, "stages", ()))
        stages.append(stage)
        self._local.stages = stages
        records = list(getattr(self._local, "records", ()))
        records.append(
            _usage_record(
                stage,
                response,
                requested_model=str(payload.get("model") or ""),
            )
        )
        self._local.records = records
        return response


def _structured_check_payload(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "reasoning": {"effort": "none"},
        "store": False,
        "max_output_tokens": 32,
        "input": [{
            "role": "user",
            "content": "Return the readiness value required by the schema.",
        }],
        "text": {
            "verbosity": "low",
            "format": {
                "type": "json_schema",
                "name": "steel_rag_frontier_readiness",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"ok": {"type": "string", "enum": ["ok"]}},
                    "required": ["ok"],
                    "additionalProperties": False,
                },
            },
        },
    }


def minimal_provider_check(model: str, *, timeout: int = 30) -> dict[str, Any]:
    from project_answer_relation_openai_v2 import api_key, call_api, response_text

    stage = "terra_startup_check" if model == TERRA_MODEL else "luna_startup_check"
    try:
        response = call_api(api_key(), _structured_check_payload(model), timeout=timeout)
        value = json.loads(response_text(response))
    except (RuntimeError, OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise _safe_provider_error(stage, exc) from exc
    if value != {"ok": "ok"}:
        raise ProviderCallError(stage, code="provider_check_invalid", retryable=True)
    return _usage_record(stage, response, requested_model=model)


@dataclass
class FrontierHealthState:
    cooldown_seconds: float = 30.0
    dependencies: dict[str, bool] = field(default_factory=lambda: {
        "local_model_assets_loaded": False,
        "corpus_and_indices_verified": False,
        "retrieval_warmup_passed": False,
        "openai_credentials_present": False,
        "terra_structured_check_passed": False,
        "luna_structured_check_passed": False,
    })
    reason: str = "startup_incomplete"
    startup_provider_requests: int = 0
    startup_actual_cost_usd: float = 0.0
    startup_pricing_known: bool = True
    _open_until: float = 0.0
    _probe_in_flight: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def mark_local_verified(self) -> None:
        with self._lock:
            self.dependencies["local_model_assets_loaded"] = True
            self.dependencies["corpus_and_indices_verified"] = True

    def mark_warmup(self, passed: bool) -> None:
        with self._lock:
            self.dependencies["retrieval_warmup_passed"] = bool(passed)
            if not passed:
                self.reason = "retrieval_warmup_failed"

    def run_startup_provider_checks(
        self,
        check: Callable[[str], None] = minimal_provider_check,
    ) -> None:
        from project_answer_relation_openai_v2 import api_key

        try:
            present = bool(api_key())
        except RuntimeError:
            present = False
        with self._lock:
            self.dependencies["openai_credentials_present"] = present
        if not present:
            self.open("openai_credentials_unavailable")
            return
        for model, key in (
            (TERRA_MODEL, "terra_structured_check_passed"),
            (LUNA_MODEL, "luna_structured_check_passed"),
        ):
            with self._lock:
                self.startup_provider_requests += 1
            try:
                record = check(model)
            except ProviderCallError as exc:
                self.open(exc.code)
                return
            with self._lock:
                self.dependencies[key] = True
                if isinstance(record, dict):
                    self.startup_actual_cost_usd += float(
                        record.get("actual_cost_usd") or 0.0
                    )
                    self.startup_pricing_known = (
                        self.startup_pricing_known
                        and bool(record.get("pricing_known"))
                    )
        with self._lock:
            self.reason = "ready"
            self._open_until = 0.0

    def ready(self) -> bool:
        with self._lock:
            return all(self.dependencies.values()) and self._open_until == 0.0

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            ready = all(self.dependencies.values()) and self._open_until == 0.0
            return {
                "status": "ready" if ready else "not_ready",
                "reason": "ready" if ready else self.reason,
                "dependencies": {
                    key: "ready" if value else "not_ready"
                    for key, value in sorted(self.dependencies.items())
                },
                "circuit": "closed" if self._open_until == 0.0 else "open",
                "startup_provider_validation": {
                    "responses_requests": self.startup_provider_requests,
                    "actual_cost_usd": self.startup_actual_cost_usd,
                    "pricing_known": self.startup_pricing_known,
                },
            }

    def open(self, reason: str) -> None:
        with self._lock:
            self.reason = reason[:96]
            self._open_until = time.monotonic() + max(1.0, self.cooldown_seconds)
            self._probe_in_flight = False

    def request_mode(self) -> str:
        """Return normal, probe, or degraded with a single half-open probe."""

        with self._lock:
            if self._open_until == 0.0:
                return "normal"
            if time.monotonic() < self._open_until or self._probe_in_flight:
                return "degraded"
            self._probe_in_flight = True
            return "probe"

    def provider_success(self, stages: tuple[str, ...], *, was_probe: bool) -> None:
        if not was_probe:
            return
        has_terra = "primary" in stages
        has_luna = "independent_relevance_entailment_verifier" in stages
        with self._lock:
            self._probe_in_flight = False
            if has_terra:
                self.dependencies["terra_structured_check_passed"] = True
            if has_luna:
                self.dependencies["luna_structured_check_passed"] = True
            if has_terra and has_luna and all(self.dependencies.values()):
                self._open_until = 0.0
                self.reason = "ready"
            else:
                self._open_until = time.monotonic() + max(1.0, self.cooldown_seconds)
                self.reason = "recovery_probe_incomplete"


__all__ = [
    "FrontierHealthState",
    "LUNA_MODEL",
    "ProviderCallError",
    "ProviderGateway",
    "TERRA_MODEL",
    "minimal_provider_check",
]
