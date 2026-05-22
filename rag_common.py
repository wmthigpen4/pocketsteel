#!/usr/bin/env python3
"""Shared helpers for the Pocket Steel Electronics RAG v0 scripts."""

from __future__ import annotations

import json
import os
import re
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_FORUM_ID = 11
DEFAULT_FORUM_NAME = "Electronics"
DEFAULT_EMBEDDING_MODEL = "bge-m3"
DEFAULT_CHAT_MODEL = "qwen3:14b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+'_.-]*")


def project_path(path: str | Path) -> Path:
    path = Path(path).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def jsonl_reader(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def count_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(text or ""))


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def normalize_space(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def excerpt(text: str, width: int = 420) -> str:
    text = normalize_space(text).replace("\n", " ")
    return textwrap.shorten(text, width=width, placeholder=" ...")


def ollama_url() -> str:
    return os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")


def _post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Ollama at {url}: {exc}") from exc


def ollama_embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    model = model or os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    payload = {"model": model, "input": texts}
    response = _post_json(f"{ollama_url()}/api/embed", payload)
    embeddings = response.get("embeddings")
    if embeddings is not None:
        return embeddings

    single_embeddings: list[list[float]] = []
    for text in texts:
        legacy = _post_json(f"{ollama_url()}/api/embeddings", {"model": model, "prompt": text})
        embedding = legacy.get("embedding")
        if embedding is None:
            raise RuntimeError(f"Ollama did not return an embedding for model {model!r}.")
        single_embeddings.append(embedding)
    return single_embeddings


def ollama_chat(messages: list[dict[str, str]], model: str | None = None) -> str:
    model = model or os.environ.get("CHAT_MODEL", DEFAULT_CHAT_MODEL)
    response = _post_json(
        f"{ollama_url()}/api/chat",
        {"model": model, "messages": messages, "stream": False},
        timeout=300,
    )
    message = response.get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError(f"Ollama did not return chat content for model {model!r}.")
    return content.strip()


def require_chromadb():
    try:
        import chromadb  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: chromadb. Install it in this environment with `pip install chromadb`."
        ) from exc
    return chromadb


def chroma_collection(chroma_path: Path, collection_name: str = "electronics"):
    chromadb = require_chromadb()
    client = chromadb.PersistentClient(path=str(chroma_path))
    return client.get_or_create_collection(name=collection_name)


def metadata_for_chroma(row: dict[str, Any]) -> dict[str, str | int | float | bool | None]:
    metadata: dict[str, str | int | float | bool | None] = {}
    for key, value in row.items():
        if key == "text":
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            metadata[key] = value
        else:
            metadata[key] = json.dumps(value, ensure_ascii=False)
    return metadata


def parse_json_metadata(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if not value or value[0] not in "[{":
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value

