#!/usr/bin/env python3
"""Answer questions from local forum RAG stores."""

from __future__ import annotations

import argparse
import re
from typing import Any

from rag_common import (
    APP_DISPLAY_NAME,
    DEFAULT_CHAT_MODEL,
    DEFAULT_FORUM_ID,
    built_forum_stores,
    excerpt,
    forum_store_candidates,
    ollama_chat,
    project_path,
)
from rag_search import search_chunks, search_forum_stores


WEAK_OVERLAP_MIN = 2


SYSTEM_PROMPT = f"""You answer questions for {APP_DISPLAY_NAME} using only the retrieved Steel Guitar Forum sources.

Grounding rules:
- Answer only from retrieved sources. If the sources are thin, conflicting, or not on point, say that plainly.
- Use source language carefully: say "forum users suggested" or "one retrieved thread describes" unless the retrieved sources establish something more definite.
- Do not invent technical advice.

Electronics interpretation rules, when the retrieved sources involve electronics:
- Treat changer, strings, keyhead, legs, pickup, volume pedal, input jack, amp chassis, and power ground as distinct physical parts. The changer is part of the steel guitar, not the amp input jack or amp chassis.
- If a user says buzz changes when touching the changer, explain that touching metal on the guitar may be improving the ground path through the player's body.
- For buzz that changes when touching the changer, prefer possible guitar ground or string/changer-to-output-ground continuity issues, then isolate guitar, cable, volume pedal, and amp before naming any single failed part.
- Do not immediately blame one component unless the retrieved sources clearly support it.

For diagnostic troubleshooting questions, use this structure:
1. What the symptom usually suggests
2. Quick isolation tests
3. Likely causes from the retrieved sources
4. When to involve an amp/electronics tech
5. Sources

For opinion, comparison, or general-consideration questions, use a simpler synthesis instead of forcing the five-section diagnostic structure.

Electrical safety:
- Say not to defeat the ground prong.
- Say not to open tube amps unless qualified.
- Say not to poke around inside an amp because stored voltages can be dangerous.
- Keep user quick isolation tests outside amp internals: swap cables, bypass pedals, try another amp, test with no instrument connected, move away from lights/power supplies, or check external continuity only if safe.
- Treat amp-internal procedures such as chassis probing, freeze spray, chopstick testing, capacitor checks, tube amp inspection, or PCB reflow as amp/electronics-tech tasks, not player quick tests.

Citation rules:
- Put source numbers inline near the claims they support, like [1] or [2].
- Do not over-rely on one source when multiple retrieved sources are relevant.
- If a source is only loosely relevant, include it in Sources but do not use it for a strong claim.
- Do not use a loosely related amp, cable, or pedal source to strongly diagnose a guitar part, or vice versa. Say the source is analogous or only loosely relevant.

Keep the answer practical and concise."""


def query_terms(query: str) -> set[str]:
    return {
        term.lower()
        for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9+'-]{2,}", query)
        if term.lower()
        not in {
            "the",
            "and",
            "for",
            "with",
            "what",
            "why",
            "does",
            "should",
            "about",
            "common",
            "using",
            "players",
            "people",
        }
    }


def retrieval_is_weak(query: str, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return True
    terms = query_terms(query)
    if not terms:
        return False
    combined = " ".join(row["text"].lower() for row in rows[:3])
    overlap = sum(1 for term in terms if term in combined)
    return overlap < min(WEAK_OVERLAP_MIN, len(terms))


def format_context(rows: list[dict[str, Any]]) -> str:
    sections = []
    for index, row in enumerate(rows, 1):
        metadata = row["metadata"]
        forum = metadata.get("forum_name") or "(unknown forum)"
        title = metadata.get("thread_title") or "(untitled thread)"
        url = metadata.get("source_url") or metadata.get("thread_url") or ""
        user = metadata.get("username") or ""
        date = metadata.get("post_date") or metadata.get("post_date_raw") or ""
        sections.append(
            f"[{index}] Forum: {forum}\nThread: {title}\nURL: {url}\nUser/date: {user} {date}\nText:\n{row['text']}"
        )
    return "\n\n---\n\n".join(sections)


def answer_question(query: str, top_k: int = 6, chat_model: str | None = None, **search_kwargs) -> tuple[str, list[dict[str, Any]], bool]:
    rows = search_chunks(query, top_k=top_k, **search_kwargs)
    weak = retrieval_is_weak(query, rows)
    if weak:
        return (
            "The retrieved forum corpus did not provide enough evidence to answer that reliably.",
            rows,
            True,
        )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": f"Question: {query}\n\nRetrieved sources:\n{format_context(rows)}",
        },
    ]
    answer = ollama_chat(messages, model=chat_model)
    return answer, rows, False


def answer_from_rows(query: str, rows: list[dict[str, Any]], chat_model: str | None = None) -> tuple[str, bool]:
    weak = retrieval_is_weak(query, rows)
    if weak:
        return "The retrieved forum corpus did not provide enough evidence to answer that reliably.", True

    answer = ollama_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {query}\n\nRetrieved sources:\n{format_context(rows)}"},
        ],
        model=chat_model,
    )
    return answer, False


def print_answer(answer: str, rows: list[dict[str, Any]]) -> None:
    print(answer)
    print("\nSources:")
    if not rows:
        print("- No retrieved sources.")
        return
    for index, row in enumerate(rows, 1):
        metadata = row["metadata"]
        forum = metadata.get("forum_name") or "(unknown forum)"
        title = metadata.get("thread_title") or "(untitled thread)"
        url = metadata.get("source_url") or metadata.get("thread_url") or ""
        print(f"- [{index}] {forum} - {title} - {url}")
        print(f"  {excerpt(row['text'], width=220)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--chroma", default="rag-data/electronics/chroma")
    parser.add_argument("--collection", default="electronics")
    parser.add_argument("--collection-name", help="Alias for --collection.")
    parser.add_argument("--forum-id", type=int, default=DEFAULT_FORUM_ID)
    parser.add_argument("--slug")
    parser.add_argument("--input-dir", help="Accepted for pipeline symmetry; not used by answer.")
    parser.add_argument("--output-dir", help="Forum output directory; used with --slug when provided.")
    parser.add_argument("--all-built", action="store_true", help="Search every built forum store under rag-data/forums plus legacy Electronics.")
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--chat-model", default=None, help=f"Chat model; defaults to CHAT_MODEL or {DEFAULT_CHAT_MODEL}")
    parser.add_argument("--forum-name")
    parser.add_argument("--thread-title")
    parser.add_argument("--date")
    args = parser.parse_args()

    collection_name = args.collection_name or args.collection
    if args.all_built:
        rows = search_forum_stores(
            args.query,
            built_forum_stores(),
            model=args.embedding_model,
            top_k=args.top_k,
            forum_name=args.forum_name,
            thread_title=args.thread_title,
            date=args.date,
        )
        answer, _weak = answer_from_rows(args.query, rows, chat_model=args.chat_model)
    elif args.slug:
        stores = forum_store_candidates(args.slug)
        if args.output_dir:
            stores = [(args.slug, project_path(args.output_dir) / "chroma", args.collection_name or args.slug)]
        rows = search_forum_stores(
            args.query,
            stores,
            model=args.embedding_model,
            top_k=args.top_k,
            forum_name=args.forum_name,
            thread_title=args.thread_title,
            date=args.date,
        )
        answer, _weak = answer_from_rows(args.query, rows, chat_model=args.chat_model)
    else:
        answer, rows, _weak = answer_question(
            args.query,
            top_k=args.top_k,
            chroma_path=args.chroma,
            collection_name=collection_name,
            model=args.embedding_model,
            chat_model=args.chat_model,
            forum_name=args.forum_name,
            thread_title=args.thread_title,
            date=args.date,
        )
    print_answer(answer, rows)


if __name__ == "__main__":
    main()
