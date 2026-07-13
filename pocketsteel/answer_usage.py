"""Local request logging and rate-limit scaffold for /api/answer."""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Any, Deque

from pocketsteel.access_control import AccessRole

RATE_LIMIT_ENABLED_ENV = "STEEL_RAG_ANSWER_RATE_LIMIT_ENABLED"
RATE_LIMIT_MAX_REQUESTS_ENV = "STEEL_RAG_ANSWER_RATE_LIMIT_MAX_REQUESTS"
RATE_LIMIT_WINDOW_SECONDS_ENV = "STEEL_RAG_ANSWER_RATE_LIMIT_WINDOW_SECONDS"
RATE_LIMIT_MAX_KEYS_ENV = "STEEL_RAG_ANSWER_RATE_LIMIT_MAX_KEYS"

DEFAULT_RATE_LIMIT_MAX_REQUESTS = 120
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_RATE_LIMIT_MAX_KEYS = 10_000


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    key: str
    limit: int
    window_seconds: int
    retry_after_seconds: int = 0
    error: str = ""


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_positive_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, ""))
    except ValueError:
        return default
    return value if value > 0 else default


def answer_rate_limit_key(environ: dict[str, Any], role: AccessRole, *, identity_key: str = "") -> str:
    """Return the temporary in-memory quota key for the scaffold.

    TODO(production): store hashed verified-user keys in a persistent quota store.
    """

    if identity_key:
        return f"{role}:{identity_key}"
    remote_addr = str(environ.get("REMOTE_ADDR") or "local").strip() or "local"
    return f"{role}:{remote_addr}"


class InMemoryAnswerRateLimiter:
    """Simple process-local fixed-window limiter.

    TODO(production): replace this with a persistent usage store.
    TODO(production): enforce per-user quotas from verified identity.
    TODO(production): decide whether admins bypass quota or have a separate budget.
    TODO(production): add paid/free tier budgets once product tiers exist.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_requests: int = DEFAULT_RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        max_keys: int = DEFAULT_RATE_LIMIT_MAX_KEYS,
        time_func: Any = time.monotonic,
    ) -> None:
        self.enabled = enabled
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self.max_keys = max(100, int(max_keys))
        self.time_func = time_func
        self._attempts: OrderedDict[str, Deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "InMemoryAnswerRateLimiter":
        return cls(
            enabled=_env_flag(RATE_LIMIT_ENABLED_ENV, True),
            max_requests=_env_positive_int(RATE_LIMIT_MAX_REQUESTS_ENV, DEFAULT_RATE_LIMIT_MAX_REQUESTS),
            window_seconds=_env_positive_int(RATE_LIMIT_WINDOW_SECONDS_ENV, DEFAULT_RATE_LIMIT_WINDOW_SECONDS),
            max_keys=_env_positive_int(RATE_LIMIT_MAX_KEYS_ENV, DEFAULT_RATE_LIMIT_MAX_KEYS),
        )

    def check(self, key: str) -> RateLimitDecision:
        if not self.enabled:
            return RateLimitDecision(True, key=key, limit=self.max_requests, window_seconds=self.window_seconds)

        now = float(self.time_func())
        with self._lock:
            attempts = self._attempts.get(key)
            if attempts is None:
                while len(self._attempts) >= self.max_keys:
                    self._attempts.popitem(last=False)
                attempts = deque()
                self._attempts[key] = attempts
            else:
                self._attempts.move_to_end(key)

            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()

            if len(attempts) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - attempts[0])))
                return RateLimitDecision(
                    False,
                    key=key,
                    limit=self.max_requests,
                    window_seconds=self.window_seconds,
                    retry_after_seconds=retry_after,
                    error="/api/answer rate limit exceeded",
                )

            attempts.append(now)
            return RateLimitDecision(True, key=key, limit=self.max_requests, window_seconds=self.window_seconds)
