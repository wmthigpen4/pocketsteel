from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from typing import Any

from steel_guitar_rag.answering import DEFAULT_OLLAMA_TIMEOUT_SECONDS, OllamaAnswerProvider
from steel_guitar_rag.runtime_server import (
    PACKAGE_LOGGER,
    configure_runtime_logging,
    create_runtime_server,
)


def _response(start_response: Any, payload: dict[str, Any]) -> list[bytes]:
    body = json.dumps(payload).encode("utf-8")
    start_response(
        "200 OK",
        [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
    )
    return [body]


def test_threaded_runtime_keeps_health_responsive_during_slow_work() -> None:
    slow_started = threading.Event()
    release_slow = threading.Event()

    def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        if environ.get("PATH_INFO") == "/slow":
            slow_started.set()
            assert release_slow.wait(timeout=5)
            return _response(start_response, {"status": "finished"})
        return _response(start_response, {"status": "live"})

    server = create_runtime_server("127.0.0.1", 0, app, max_workers=2, request_queue=8)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = server.server_address[1]
    slow_result: list[dict[str, Any]] = []

    def call_slow() -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/slow", timeout=5) as response:
            slow_result.append(json.loads(response.read()))

    slow_thread = threading.Thread(target=call_slow)
    slow_thread.start()
    assert slow_started.wait(timeout=2)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health/live", timeout=2) as response:
            assert json.loads(response.read()) == {"status": "live"}
    finally:
        release_slow.set()
        slow_thread.join(timeout=5)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)

    assert slow_result == [{"status": "finished"}]


def test_runtime_queues_short_bursts_instead_of_rejecting_at_worker_limit() -> None:
    active_lock = threading.Lock()
    active_workers = 0
    all_workers_started = threading.Event()
    release_slow = threading.Event()

    def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        nonlocal active_workers
        if environ.get("PATH_INFO") == "/slow":
            with active_lock:
                active_workers += 1
                if active_workers == 2:
                    all_workers_started.set()
            assert release_slow.wait(timeout=5)
        return _response(start_response, {"status": "finished"})

    server = create_runtime_server("127.0.0.1", 0, app, max_workers=2, request_queue=8)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = server.server_address[1]
    results: list[int] = []
    errors: list[str] = []

    def call_slow() -> None:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/slow", timeout=5) as response:
                response.read()
                results.append(response.status)
        except (OSError, urllib.error.HTTPError) as exc:
            errors.append(str(exc))

    active_threads = [threading.Thread(target=call_slow) for _ in range(2)]
    for thread in active_threads:
        thread.start()
    assert all_workers_started.wait(timeout=2)

    queued_thread = threading.Thread(target=call_slow)
    queued_thread.start()
    try:
        queued_thread.join(timeout=0.25)
        assert queued_thread.is_alive()
    finally:
        release_slow.set()
        for thread in [*active_threads, queued_thread]:
            thread.join(timeout=5)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)

    assert errors == []
    assert results == [200, 200, 200]


def test_ollama_dependency_timeout_is_bounded(monkeypatch: Any) -> None:
    monkeypatch.setenv("STEEL_RAG_OLLAMA_TIMEOUT_SECONDS", "900")
    assert OllamaAnswerProvider().timeout_seconds == 75.0

    monkeypatch.setenv("STEEL_RAG_OLLAMA_TIMEOUT_SECONDS", "not-a-number")
    assert OllamaAnswerProvider().timeout_seconds == DEFAULT_OLLAMA_TIMEOUT_SECONDS


def test_runtime_logging_captures_answer_route_diagnostics(
    monkeypatch: Any, tmp_path: Any
) -> None:
    original_handlers = list(PACKAGE_LOGGER.handlers)
    original_level = PACKAGE_LOGGER.level
    original_propagate = PACKAGE_LOGGER.propagate
    for handler in original_handlers:
        PACKAGE_LOGGER.removeHandler(handler)
    monkeypatch.setenv("STEEL_RAG_LOG_DIR", str(tmp_path))
    try:
        configure_runtime_logging()
        logging.getLogger("steel_guitar_rag.api").info(
            'answer route event: {"route":"deterministic"}'
        )
        for handler in PACKAGE_LOGGER.handlers:
            handler.flush()
        assert 'answer route event: {"route":"deterministic"}' in (
            tmp_path / "runtime.log"
        ).read_text(encoding="utf-8")
    finally:
        for handler in list(PACKAGE_LOGGER.handlers):
            handler.close()
            PACKAGE_LOGGER.removeHandler(handler)
        for handler in original_handlers:
            PACKAGE_LOGGER.addHandler(handler)
        PACKAGE_LOGGER.setLevel(original_level)
        PACKAGE_LOGGER.propagate = original_propagate
