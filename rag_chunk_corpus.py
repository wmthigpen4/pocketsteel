#!/usr/bin/env python3
"""Chunk the clean Electronics corpus for The Turnaround RAG v0."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from typing import Any

from rag_common import count_tokens, jsonl_reader, normalize_space, project_path


DEFAULT_INPUT = "rag-data/electronics/clean_corpus.jsonl"
DEFAULT_OUTPUT = "rag-data/electronics/chunks.jsonl"
DEFAULT_REPORT = "rag-data/electronics/chunk_report.json"
TARGET_MIN = 500
TARGET_MAX = 1200
TARGET_IDEAL = 850
DATE_RE = re.compile(r"\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s+\d{1,2}:\d{2}\s+(?:am|pm)", re.IGNORECASE)


def display_date(raw_date: str) -> str:
    match = DATE_RE.search(raw_date or "")
    return match.group(0) if match else (raw_date or "")


def format_post(post: dict[str, Any], text: str | None = None) -> str:
    body = normalize_space(text if text is not None else post.get("text") or "")
    return f"{post.get('username') or 'Unknown'} ({display_date(post.get('post_date_raw') or '') or 'date unknown'}):\n{body}"


def split_long_text(text: str, max_tokens: int = TARGET_MAX) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if current:
            chunks.append(normalize_space("\n\n".join(current)))
            current = []
            current_tokens = 0

    for paragraph in paragraphs or [text]:
        paragraph_tokens = count_tokens(paragraph)
        if paragraph_tokens > max_tokens:
            flush()
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            sentence_group: list[str] = []
            sentence_tokens = 0
            for sentence in sentences:
                tokens = count_tokens(sentence)
                if tokens > max_tokens:
                    if sentence_group:
                        chunks.append(normalize_space(" ".join(sentence_group)))
                        sentence_group = []
                        sentence_tokens = 0
                    words = sentence.split()
                    for start in range(0, len(words), max_tokens):
                        chunks.append(normalize_space(" ".join(words[start : start + max_tokens])))
                    continue
                if sentence_group and sentence_tokens + tokens > max_tokens:
                    chunks.append(normalize_space(" ".join(sentence_group)))
                    sentence_group = []
                    sentence_tokens = 0
                sentence_group.append(sentence)
                sentence_tokens += tokens
            if sentence_group:
                chunks.append(normalize_space(" ".join(sentence_group)))
            continue
        if current and current_tokens + paragraph_tokens > max_tokens:
            flush()
        current.append(paragraph)
        current_tokens += paragraph_tokens
    flush()
    return chunks


def make_chunk(thread_id: str, chunk_index: int, posts: list[dict[str, Any]], text: str) -> dict[str, Any]:
    first = posts[0]
    usernames = [post.get("username", "") for post in posts if post.get("username")]
    post_dates = [post.get("post_date_raw", "") for post in posts if post.get("post_date_raw")]
    display_dates = [display_date(date) for date in post_dates if display_date(date)]
    chunk = {
        "chunk_id": f"electronics-{thread_id}-{chunk_index:04d}",
        "source": first.get("source"),
        "source_system": first.get("source_system"),
        "forum_id": first.get("forum_id"),
        "forum_name": first.get("forum_name"),
        "thread_id": thread_id,
        "thread_title": first.get("thread_title") or "",
        "source_url": first.get("thread_url") or "",
        "thread_url": first.get("thread_url") or "",
        "post_uids": [post.get("post_uid") for post in posts if post.get("post_uid")],
        "usernames": list(dict.fromkeys(usernames)),
        "post_dates": display_dates,
        "post_dates_raw": post_dates,
        "username": usernames[0] if len(set(usernames)) == 1 else (usernames[0] if usernames else ""),
        "post_date": display_dates[0] if display_dates else "",
        "post_date_raw": post_dates[0] if post_dates else "",
        "links": [link for post in posts for link in (post.get("links") or [])],
        "token_count": count_tokens(text),
        "text": text,
    }
    return chunk


def chunk_thread(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    if not posts:
        return chunks

    thread_id = str(posts[0]["thread_id"])
    current_posts: list[dict[str, Any]] = []
    current_texts: list[str] = []
    current_tokens = 0
    chunk_index = 1

    def flush() -> None:
        nonlocal current_posts, current_texts, current_tokens, chunk_index
        if not current_posts:
            return
        text = normalize_space("\n\n".join(current_texts))
        chunks.append(make_chunk(thread_id, chunk_index, current_posts, text))
        chunk_index += 1
        current_posts = []
        current_texts = []
        current_tokens = 0

    for post in posts:
        text = normalize_space(post.get("text") or "")
        formatted = format_post(post, text)
        tokens = count_tokens(formatted)
        if tokens > TARGET_MAX:
            flush()
            max_body_tokens = max(100, TARGET_MAX - count_tokens(format_post(post, "")) - 5)
            for part in split_long_text(text, max_tokens=max_body_tokens):
                part_post = dict(post)
                chunks.append(make_chunk(thread_id, chunk_index, [part_post], format_post(part_post, part)))
                chunk_index += 1
            continue

        if current_posts and current_tokens >= TARGET_MIN and current_tokens + tokens > TARGET_IDEAL:
            flush()
        elif current_posts and current_tokens + tokens > TARGET_MAX:
            flush()

        current_posts.append(post)
        current_texts.append(formatted)
        current_tokens += tokens

    flush()
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    args = parser.parse_args()

    input_path = project_path(args.input)
    output_path = project_path(args.output)
    report_path = project_path(args.report)

    by_thread: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in jsonl_reader(input_path):
        by_thread[str(row["thread_id"])].append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_count = 0
    token_counts: list[int] = []
    with output_path.open("w", encoding="utf-8") as handle:
        for thread_id in sorted(by_thread, key=lambda value: int(value) if value.isdigit() else value):
            for chunk in chunk_thread(by_thread[thread_id]):
                handle.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
                chunk_count += 1
                token_counts.append(chunk["token_count"])

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "threads": len(by_thread),
        "chunks": chunk_count,
        "target_tokens": {"min": TARGET_MIN, "max": TARGET_MAX, "ideal": TARGET_IDEAL},
        "token_count_min": min(token_counts) if token_counts else 0,
        "token_count_max": max(token_counts) if token_counts else 0,
        "token_count_avg": round(sum(token_counts) / len(token_counts), 2) if token_counts else 0,
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {chunk_count} chunks to {output_path}")
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
