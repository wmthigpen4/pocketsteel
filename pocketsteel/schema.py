"""Schema normalization for scraped Steel Guitar Forum JSONL."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from pocketsteel.text import compact_text, normalize_text


STRUCTURED_SUFFIXES = {".json", ".jsonl"}

TEXT_ALIASES = (
    "text",
    "body",
    "content",
    "message",
    "post_text",
    "post_text_clean",
    "post_body",
    "html",
    "body_html",
    "content_html",
)

FIELD_ALIASES = {
    "title": ("title", "thread_title", "topic_title", "subject"),
    "url": ("url", "post_url", "source_url", "link", "permalink", "thread_url"),
    "forum": ("forum", "forum_name", "section", "category"),
    "thread_id": ("thread_id", "topic_id", "threadId", "topicId", "thread.id"),
    "post_id": ("post_id", "post_uid", "id", "postId", "message_id", "post.id"),
    "author": ("author", "username", "user", "poster", "member", "author.name", "user.name"),
    "posted_at": ("posted_at", "post_date", "post_date_raw", "date", "datetime", "created_at", "timestamp"),
}

EXTRA_FIELD_ALIASES = {
    "thread_url": ("thread_url", "topic_url"),
    "thread_page_start": ("thread_page_start", "page_start", "start"),
    "forum_id": ("forum_id",),
    "content_hash": ("content_hash",),
    "scraped_at": ("scraped_at",),
    "source_name": ("source",),
}

METADATA_FIELDS = (
    "source",
    "source_name",
    "title",
    "url",
    "thread_url",
    "thread_page_start",
    "forum",
    "forum_id",
    "thread_id",
    "post_id",
    "author",
    "posted_at",
    "content_hash",
    "scraped_at",
    "links",
    "quotes",
)

SGF_DATE_RE = re.compile(r"\b(\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s+\d{1,2}:\d{2}\s+[ap]m)\b")
SIGNATURE_MARKERS = {"------------------", "_________________"}


def stable_hash(*parts: object, length: int = 16) -> str:
    payload = "\u241f".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:length]


def read_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            yield line_number, value


def is_structured_path(path: Path) -> bool:
    return path.suffix.lower() in STRUCTURED_SUFFIXES


def iter_structured_records(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield raw records from JSONL files, JSON arrays, or single JSON objects."""
    if path.suffix.lower() == ".jsonl":
        yield from read_jsonl(path)
        return

    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        # Some scrapers use .json for newline-delimited JSON. Accept that too.
        yield from read_jsonl(path)
        return

    if isinstance(payload, list):
        for index, value in enumerate(payload, start=1):
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{index} is not a JSON object")
            yield index, value
        return

    if isinstance(payload, dict):
        for key in ("records", "items", "threads"):
            nested = payload.get(key)
            if isinstance(nested, list):
                base = {item_key: item_value for item_key, item_value in payload.items() if item_key != key}
                for index, value in enumerate(nested, start=1):
                    if not isinstance(value, dict):
                        raise ValueError(f"{path}:{key}[{index}] is not a JSON object")
                    merged = dict(base)
                    merged.update(value)
                    yield index, merged
                return
        yield 1, payload
        return

    raise ValueError(f"{path} is not a JSON object or array")


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def get_path(record: Mapping[str, Any], dotted_key: str) -> Any:
    current: Any = record
    for part in dotted_key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def stringify_metadata(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        for key in ("name", "username", "display_name", "title", "id"):
            if key in value and value[key] is not None:
                return compact_text(value[key])
        return compact_text(json.dumps(value, ensure_ascii=False, sort_keys=True))
    if isinstance(value, (list, tuple)):
        return compact_text(", ".join(stringify_metadata(item) for item in value))
    return compact_text(value)


def first_value(record: Mapping[str, Any], aliases: Iterable[str]) -> Any:
    for alias in aliases:
        value = get_path(record, alias)
        if value not in (None, ""):
            return value
    return None


def normalize_posted_at(value: Any) -> str:
    text = compact_text(value)
    match = SGF_DATE_RE.search(text)
    if match:
        return match.group(1)
    return text


def prune_sgf_body(text: str) -> str:
    lines = [line.strip() for line in normalize_text(text).splitlines()]
    filtered: list[str] = []
    for line in lines:
        if not line or line == "Top":
            continue
        if "[This message was edited by" in line:
            continue
        filtered.append(line)

    for index, line in enumerate(filtered):
        if line in SIGNATURE_MARKERS and len(" ".join(filtered[:index])) >= 80:
            filtered = filtered[:index]
            break

    return normalize_text("\n".join(filtered))


def clean_sgf_post_text(record: Mapping[str, Any]) -> str:
    raw_text = first_value(record, TEXT_ALIASES)
    text = normalize_text(raw_text)
    if not text:
        return ""

    if "post_text_clean" not in record:
        return prune_sgf_body(text)

    lines = text.splitlines()
    posted_at = normalize_posted_at(first_value(record, FIELD_ALIASES["posted_at"]))
    body_start: int | None = None

    if posted_at:
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped == posted_at:
                body_start = index + 1
            elif stripped.startswith(posted_at):
                remainder = stripped[len(posted_at) :].strip()
                body = "\n".join([remainder, *lines[index + 1 :]])
                return prune_sgf_body(body)

    if body_start is None:
        marker_indexes = [index for index, line in enumerate(lines) if line.strip() == "\u00bb"]
        if marker_indexes:
            marker_index = marker_indexes[-1]
            body_start = min(marker_index + 2, len(lines))

    body = "\n".join(lines[body_start:]) if body_start is not None else text
    return prune_sgf_body(body)


def build_source_url(record: Mapping[str, Any]) -> str:
    direct_url = stringify_metadata(first_value(record, ("post_url", "source_url", "permalink", "url", "link")))
    thread_url = stringify_metadata(first_value(record, ("thread_url", "topic_url")))
    url = direct_url or thread_url
    if not url:
        return ""

    post_uid = stringify_metadata(first_value(record, ("post_uid", "post_id", "id")))
    if post_uid and "#" in url:
        return url

    page_start_raw = first_value(record, ("thread_page_start", "page_start", "start"))
    try:
        page_start = int(page_start_raw or 0)
    except (TypeError, ValueError):
        page_start = 0

    if thread_url and page_start > 0 and "start=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}start={page_start}"

    if post_uid:
        url = f"{url}#{post_uid}"
    return url


def iter_post_records(record: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    posts = record.get("posts")
    if isinstance(posts, list):
        base = {key: value for key, value in record.items() if key != "posts"}
        for post in posts:
            if isinstance(post, Mapping):
                merged = dict(base)
                merged.update(post)
                yield merged
            else:
                merged = dict(base)
                merged["text"] = post
                yield merged
        return

    yield dict(record)


def make_doc_id(record: Mapping[str, Any], source: str, text: str) -> str:
    thread_id = stringify_metadata(first_value(record, FIELD_ALIASES["thread_id"]))
    post_id = stringify_metadata(first_value(record, FIELD_ALIASES["post_id"]))
    url = stringify_metadata(first_value(record, FIELD_ALIASES["url"]))
    title = stringify_metadata(first_value(record, FIELD_ALIASES["title"]))
    author = stringify_metadata(first_value(record, FIELD_ALIASES["author"]))
    posted_at = stringify_metadata(first_value(record, FIELD_ALIASES["posted_at"]))

    if post_id:
        return f"{source}:post:{stable_hash(thread_id, post_id, url)}"
    if url:
        return f"{source}:url:{stable_hash(url)}"
    return f"{source}:doc:{stable_hash(title, author, posted_at, text[:1000])}"


def normalize_record(
    record: Mapping[str, Any],
    *,
    source: str = "sgf",
    min_text_chars: int = 40,
) -> dict[str, Any] | None:
    text = clean_sgf_post_text(record)
    if len(re.sub(r"\s+", "", text)) < min_text_chars:
        return None

    normalized: dict[str, Any] = {
        "doc_id": make_doc_id(record, source, text),
        "source": source,
        "text": text,
    }

    for field_name, aliases in FIELD_ALIASES.items():
        if field_name == "url":
            normalized[field_name] = build_source_url(record)
        elif field_name == "posted_at":
            normalized[field_name] = normalize_posted_at(first_value(record, aliases))
        else:
            normalized[field_name] = stringify_metadata(first_value(record, aliases))

    for field_name, aliases in EXTRA_FIELD_ALIASES.items():
        normalized[field_name] = stringify_metadata(first_value(record, aliases))

    if "links" in record and isinstance(record["links"], list):
        normalized["links"] = record["links"]
    else:
        normalized["links"] = []

    if "quotes" in record and isinstance(record["quotes"], list):
        normalized["quotes"] = record["quotes"]
    else:
        normalized["quotes"] = []

    return normalized


def source_metadata(record: Mapping[str, Any]) -> dict[str, Any]:
    return {field: record.get(field, "") for field in METADATA_FIELDS}
