#!/usr/bin/env python3
"""Shared helpers for Steel Guitar RAG forum RAG scripts."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_FORUM_ID = 11
DEFAULT_FORUM_NAME = "Electronics"
DEFAULT_FORUM_SLUG = "electronics"
DEFAULT_EMBEDDING_MODEL = "bge-m3"
DEFAULT_CHAT_MODEL = "qwen3:14b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
OLLAMA_EMBED_TIMEOUT_ENV = "STEEL_RAG_OLLAMA_EMBED_TIMEOUT_SECONDS"
DEFAULT_OLLAMA_EMBED_TIMEOUT_SECONDS = 25.0
APP_DISPLAY_NAME = "Steel Guitar RAG"
LEGACY_ELECTRONICS_DIR = "rag-data/electronics"
FORUMS_OUTPUT_ROOT = "rag-data/forums"

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+'_.-]*")


def project_path(path: str | Path) -> Path:
    path = Path(path).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or DEFAULT_FORUM_SLUG


def forum_output_dir(slug: str | None = None, output_dir: str | Path | None = None, legacy_default: bool = False) -> Path:
    if output_dir:
        return project_path(output_dir)
    if legacy_default and not slug:
        return project_path(LEGACY_ELECTRONICS_DIR)
    return project_path(FORUMS_OUTPUT_ROOT) / (slug or DEFAULT_FORUM_SLUG)


def resolve_sgf_output_dir(input_dir: str | Path | None = None) -> Path:
    if input_dir:
        return project_path(input_dir)

    env_dir = os.environ.get("SGF_OUTPUT_DIR")
    if env_dir:
        return project_path(env_dir)

    local = project_path("sgf-output")
    if (local / "manifest.sqlite").exists() or local.exists():
        return local

    for candidate in PROJECT_ROOT.parent.glob("*/sgf-output"):
        if (candidate / "manifest.sqlite").exists():
            return candidate

    return local


def forum_input_glob(forum_id: int, input_dir: str | Path | None = None) -> str:
    return str(resolve_sgf_output_dir(input_dir) / "jsonl" / f"forum-{forum_id}" / "*.jsonl")


def forum_store_candidates(slug: str) -> list[tuple[str, Path, str]]:
    stores: list[tuple[str, Path, str]] = []
    forum_dir = project_path(FORUMS_OUTPUT_ROOT) / slug
    stores.append((slug, forum_dir / "chroma", slug))
    if slug == DEFAULT_FORUM_SLUG:
        stores.append((slug, project_path(LEGACY_ELECTRONICS_DIR) / "chroma", DEFAULT_FORUM_SLUG))
    return stores


def built_forum_stores() -> list[tuple[str, Path, str]]:
    stores: list[tuple[str, Path, str]] = []
    forums_root = project_path(FORUMS_OUTPUT_ROOT)
    if forums_root.exists():
        for forum_dir in sorted(path for path in forums_root.iterdir() if path.is_dir()):
            chroma_path = forum_dir / "chroma"
            if chroma_path.exists():
                stores.append((forum_dir.name, chroma_path, forum_dir.name))

    legacy_chroma = project_path(LEGACY_ELECTRONICS_DIR) / "chroma"
    if legacy_chroma.exists() and not any(slug == DEFAULT_FORUM_SLUG for slug, _, _ in stores):
        stores.append((DEFAULT_FORUM_SLUG, legacy_chroma, DEFAULT_FORUM_SLUG))
    return stores


def load_forum_config(path: str | Path = "rag_forums.json") -> dict[str, dict[str, Any]]:
    config_path = project_path(path)
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {str(slug): value for slug, value in data.items()}


def manifest_forum_status(manifest_path: Path, forum_id: int) -> dict[str, int | str]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with sqlite3.connect(manifest_path) as conn:
        row = conn.execute(
            """
            select coalesce(max(forum_name), ''),
                   sum(case when status='scraped' then 1 else 0 end),
                   sum(case when status='discovered' then 1 else 0 end),
                   sum(case when status='error' then 1 else 0 end),
                   count(*)
            from threads
            where forum_id=?
            """,
            (forum_id,),
        ).fetchone()
    forum_name, scraped, discovered, errors, total = row or ("", 0, 0, 0, 0)
    return {
        "forum_id": forum_id,
        "forum_name": forum_name or "",
        "scraped": int(scraped or 0),
        "discovered": int(discovered or 0),
        "errors": int(errors or 0),
        "total": int(total or 0),
    }


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


def _post_json(url: str, payload: dict[str, Any], timeout: float = 120.0) -> dict[str, Any]:
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
    try:
        configured_timeout = float(
            os.environ.get(OLLAMA_EMBED_TIMEOUT_ENV) or DEFAULT_OLLAMA_EMBED_TIMEOUT_SECONDS
        )
    except (TypeError, ValueError):
        configured_timeout = DEFAULT_OLLAMA_EMBED_TIMEOUT_SECONDS
    timeout = max(5.0, min(configured_timeout, 45.0))
    response = _post_json(f"{ollama_url()}/api/embed", payload, timeout=timeout)
    embeddings = response.get("embeddings")
    if embeddings is not None:
        return embeddings

    single_embeddings: list[list[float]] = []
    for text in texts:
        legacy = _post_json(
            f"{ollama_url()}/api/embeddings",
            {"model": model, "prompt": text},
            timeout=timeout,
        )
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
