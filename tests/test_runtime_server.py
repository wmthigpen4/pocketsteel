from __future__ import annotations

import json
import threading
import urllib.request
from typing import Any

from steel_guitar_rag.answering import DEFAULT_OLLAMA_TIMEOUT_SECONDS, OllamaAnswerProvider
from steel_guitar_rag.runtime_server import create_runtime_server


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


def test_ollama_dependency_timeout_is_bounded(monkeypatch: Any) -> None:
    monkeypatch.setenv("STEEL_RAG_OLLAMA_TIMEOUT_SECONDS", "900")
    assert OllamaAnswerProvider().timeout_seconds == 75.0

    monkeypatch.setenv("STEEL_RAG_OLLAMA_TIMEOUT_SECONDS", "not-a-number")
    assert OllamaAnswerProvider().timeout_seconds == DEFAULT_OLLAMA_TIMEOUT_SECONDS
