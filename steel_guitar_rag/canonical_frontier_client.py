"""Default-off client for the independently verified canonical frontier."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


ENABLE_CANONICAL_FRONTIER_ENV = "STEEL_RAG_CANONICAL_FRONTIER_ENABLED"
CANONICAL_FRONTIER_URL_ENV = "STEEL_RAG_CANONICAL_FRONTIER_URL"
CANONICAL_FRONTIER_TOKEN_ENV = "STEEL_RAG_CANONICAL_FRONTIER_TOKEN"
CANONICAL_FRONTIER_TIMEOUT_ENV = "STEEL_RAG_CANONICAL_FRONTIER_TIMEOUT_SECONDS"
DEFAULT_CANONICAL_FRONTIER_URL = "http://127.0.0.1:8771/v1/answer"
DEFAULT_CANONICAL_FRONTIER_TIMEOUT_SECONDS = 20.0
ALLOWED_MODES = {"complete", "partial", "clarify", "abstain"}


class CanonicalFrontierUnavailable(RuntimeError):
    """The candidate service was unavailable or returned an unsafe response."""


def _env_flag(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def configured_canonical_frontier_enabled(env: Mapping[str, str] | None = None) -> bool:
    values = env or os.environ
    return _env_flag(values.get(ENABLE_CANONICAL_FRONTIER_ENV))


def _configured_timeout(env: Mapping[str, str]) -> float:
    try:
        value = float(env.get(CANONICAL_FRONTIER_TIMEOUT_ENV) or DEFAULT_CANONICAL_FRONTIER_TIMEOUT_SECONDS)
    except (TypeError, ValueError):
        value = DEFAULT_CANONICAL_FRONTIER_TIMEOUT_SECONDS
    return max(1.0, min(value, 35.0))


def validate_frontier_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise CanonicalFrontierUnavailable("Canonical frontier response schema is invalid.")
    mode = value.get("mode")
    answer = value.get("answer")
    claims = value.get("claims")
    sources = value.get("sources")
    if mode not in ALLOWED_MODES or not isinstance(answer, str) or not answer.strip():
        raise CanonicalFrontierUnavailable("Canonical frontier answer envelope is invalid.")
    if not isinstance(claims, list) or not isinstance(sources, list):
        raise CanonicalFrontierUnavailable("Canonical frontier claims or sources are invalid.")
    if mode in {"clarify", "abstain"} and (claims or sources):
        raise CanonicalFrontierUnavailable("A non-answer response exposed claims or sources.")
    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise CanonicalFrontierUnavailable("Canonical frontier source is invalid.")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in source_ids:
            raise CanonicalFrontierUnavailable("Canonical frontier source IDs are invalid.")
        if not isinstance(source.get("excerpt"), str) or not source.get("excerpt", "").strip():
            raise CanonicalFrontierUnavailable("Canonical frontier source evidence is empty.")
        source_ids.add(source_id)
    claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise CanonicalFrontierUnavailable("Canonical frontier claim is invalid.")
        claim_id = claim.get("claim_id")
        text = claim.get("text")
        cited = claim.get("source_ids")
        support_mode = claim.get("support_mode")
        if (
            not isinstance(claim_id, str)
            or not claim_id
            or claim_id in claim_ids
            or not isinstance(text, str)
            or not text.strip()
            or text not in answer
            or not isinstance(cited, list)
            or not cited
            or any(not isinstance(item, str) or item not in source_ids for item in cited)
            or support_mode not in {"deterministic_entailment", "independent_semantic_verifier"}
        ):
            raise CanonicalFrontierUnavailable("Canonical frontier claim support is invalid.")
        claim_ids.add(claim_id)
    if mode in {"complete", "partial"} and not claims:
        raise CanonicalFrontierUnavailable("An answer response contained no verified claims.")
    return value


@dataclass(frozen=True)
class CanonicalFrontierClient:
    url: str
    token: str
    timeout_seconds: float = DEFAULT_CANONICAL_FRONTIER_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "CanonicalFrontierClient":
        values = env or os.environ
        url = str(values.get(CANONICAL_FRONTIER_URL_ENV) or DEFAULT_CANONICAL_FRONTIER_URL).strip()
        token = str(values.get(CANONICAL_FRONTIER_TOKEN_ENV) or "").strip()
        if not url.startswith(("http://127.0.0.1:", "http://localhost:", "https://")):
            raise ValueError("Canonical frontier URL must use HTTPS or an explicit loopback HTTP address.")
        if not token:
            raise ValueError(f"{CANONICAL_FRONTIER_TOKEN_ENV} is required when the frontier is enabled.")
        return cls(url=url, token=token, timeout_seconds=_configured_timeout(values))

    def answer(
        self,
        question: str,
        *,
        conversation_context: list[str] | None = None,
    ) -> dict[str, Any]:
        body = json.dumps({
            "schema_version": 1,
            "question": question,
            "conversation_context": list(conversation_context or [])[-8:],
        }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(1_048_577)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CanonicalFrontierUnavailable("Canonical frontier request failed.") from exc
        if len(raw) > 1_048_576:
            raise CanonicalFrontierUnavailable("Canonical frontier response is too large.")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CanonicalFrontierUnavailable("Canonical frontier returned invalid JSON.") from exc
        return validate_frontier_result(value)


__all__ = [
    "CANONICAL_FRONTIER_TIMEOUT_ENV",
    "CANONICAL_FRONTIER_TOKEN_ENV",
    "CANONICAL_FRONTIER_URL_ENV",
    "DEFAULT_CANONICAL_FRONTIER_URL",
    "ENABLE_CANONICAL_FRONTIER_ENV",
    "CanonicalFrontierClient",
    "CanonicalFrontierUnavailable",
    "configured_canonical_frontier_enabled",
    "validate_frontier_result",
]
