"""Bounded wall-clock isolation for local runtime dependencies."""

from __future__ import annotations

import os
import queue
import threading
from collections.abc import Callable
from typing import Any, TypeVar, cast


ResultT = TypeVar("ResultT")


class DependencyTimeout(RuntimeError):
    """Raised when a dependency exceeds its caller-facing wall-clock budget."""


class DependencyRunnerBusy(RuntimeError):
    """Raised when all bounded dependency slots are already occupied."""


def bounded_env_float(
    name: str,
    default: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    try:
        value = float(os.environ.get(name) or default)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


class BoundedDependencyRunner:
    """Run dependencies on bounded daemon workers with a hard caller deadline.

    A timed-out dependency may finish in the background, but it continues to
    occupy its slot. This prevents repeated slow calls from creating an
    unbounded number of threads while allowing the API request to fail over.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max(1, min(int(max_workers), 16))
        self._slots = threading.BoundedSemaphore(self.max_workers)

    def run(self, operation: Callable[[], ResultT], *, timeout_seconds: float) -> ResultT:
        if not self._slots.acquire(blocking=False):
            raise DependencyRunnerBusy("dependency worker pool is busy")

        outcomes: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

        def invoke() -> None:
            try:
                outcomes.put((True, operation()))
            except Exception as exc:
                outcomes.put((False, exc))
            finally:
                self._slots.release()

        threading.Thread(target=invoke, name="bounded-dependency", daemon=True).start()
        try:
            succeeded, value = outcomes.get(timeout=max(0.001, float(timeout_seconds)))
        except queue.Empty as exc:
            raise DependencyTimeout("dependency exceeded its wall-clock budget") from exc
        if succeeded:
            return cast(ResultT, value)
        raise cast(Exception, value)
