"""Shared API response shapes for retrieval and answer endpoints."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

try:
    from typing import NotRequired
except ImportError:  # Python 3.9 compatibility.
    from typing_extensions import NotRequired


AnswerMode = Literal["ask", "gear", "copedent", "tab", "practice"]


class SearchResult(TypedDict):
    score: float
    excerpt: str
    source_system: str
    forum_name: str
    thread_title: str
    thread_url: str
    chunk_id: str
    post_uid: str
    source_kind: str
    forum_id: str
    legacy_forum_number: str
    thread_id: str
    legacy_thread_uid: str
    thread_category: str
    thread_quality_score: Any
    chunk_index: Any
    warnings: list[str]


class SourceCitation(TypedDict):
    title: str
    forumName: str
    url: str
    excerpt: str
    score: float
    chunkId: str
    postUid: str | None


class AnswerSection(TypedDict):
    title: str
    body: str
    style: NotRequired[str]


class AnswerResponse(TypedDict):
    answer: str
    mode: AnswerMode
    sources: list[SourceCitation]
    warnings: list[str]
    sections: list[AnswerSection]
