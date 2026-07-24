from __future__ import annotations

import threading

import pytest

from steel_guitar_rag.runtime_dependencies import (
    BoundedDependencyRunner,
    DependencyRunnerBusy,
    DependencyTimeout,
    bounded_env_float,
)


def test_bounded_env_float_clamps_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_WALL_TIMEOUT", "500")
    assert bounded_env_float("TEST_WALL_TIMEOUT", 10.0, minimum=1.0, maximum=40.0) == 40.0
    monkeypatch.setenv("TEST_WALL_TIMEOUT", "invalid")
    assert bounded_env_float("TEST_WALL_TIMEOUT", 10.0, minimum=1.0, maximum=40.0) == 10.0


def test_dependency_timeout_keeps_worker_slot_bounded() -> None:
    runner = BoundedDependencyRunner(max_workers=1)
    release = threading.Event()

    with pytest.raises(DependencyTimeout):
        runner.run(lambda: release.wait(1.0), timeout_seconds=0.01)

    with pytest.raises(DependencyRunnerBusy):
        runner.run(lambda: "not reached", timeout_seconds=0.01)

    release.set()


def test_dependency_runner_returns_values_and_propagates_errors() -> None:
    runner = BoundedDependencyRunner(max_workers=1)

    assert runner.run(lambda: "ready", timeout_seconds=0.1) == "ready"
    with pytest.raises(ValueError, match="broken"):
        runner.run(lambda: (_ for _ in ()).throw(ValueError("broken")), timeout_seconds=0.1)
