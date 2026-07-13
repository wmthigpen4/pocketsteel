from __future__ import annotations

from typing import Any

import pytest

import rag_common


@pytest.mark.parametrize(
    ("configured", "expected"),
    [("1", 5.0), ("30", 30.0), ("300", 45.0), ("invalid", 25.0)],
)
def test_ollama_embed_uses_bounded_dependency_timeout(
    monkeypatch: pytest.MonkeyPatch,
    configured: str,
    expected: float,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_post_json(url: str, payload: dict[str, Any], timeout: float = 120.0) -> dict[str, Any]:
        calls.append({"url": url, "payload": payload, "timeout": timeout})
        return {"embeddings": [[0.1, 0.2, 0.3]]}

    monkeypatch.setenv(rag_common.OLLAMA_EMBED_TIMEOUT_ENV, configured)
    monkeypatch.setattr(rag_common, "_post_json", fake_post_json)

    assert rag_common.ollama_embed(["blocking"], "test-model") == [[0.1, 0.2, 0.3]]
    assert calls[0]["timeout"] == expected
