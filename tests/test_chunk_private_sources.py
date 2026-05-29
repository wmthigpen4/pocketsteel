from __future__ import annotations

import json
from pathlib import Path

from scripts.chunk_private_sources import chunk_text, make_chunks, read_jsonl, write_report, write_jsonl


def normalized_row(text: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "source_id": "lesson-001",
        "source_system": "private_lesson_transcript",
        "visibility": "private",
        "source_path": "source-inbox/private-lessons/lesson.txt",
        "title": "Private Lesson",
        "file_type": "txt",
        "document_index": 0,
        "text": text,
        "metadata": {
            "author_or_creator": "Teacher",
            "source_type": "lesson_transcript",
            "source_url": None,
            "relative_path": "private-lessons/lesson.txt",
        },
        "provenance_status": "reviewed",
        "embedding_allowed": True,
        "redistribution_allowed": False,
        "answer_quote_allowed": "limited",
        "created_at": "2026-05-29T00:00:00+00:00",
    }
    row.update(overrides)
    return row


def test_chunk_text_preserves_tab_heavy_spacing() -> None:
    text = "\n\n".join(
        [
            "E9 exercise",
            "3--5A--6\n4------6F\n5--5A--6A",
            "Repeat slowly.",
        ]
    )

    chunks = chunk_text(text, target_chars=80, max_chars=120, min_chars=10)

    assert chunks
    joined = "\n\n".join(chunks)
    assert "3--5A--6\n4------6F\n5--5A--6A" in joined


def test_make_chunks_preserves_private_metadata_and_document_boundaries() -> None:
    rows = [
        normalized_row("First private lesson paragraph.\n\nSecond paragraph with enough detail for retrieval."),
        normalized_row(
            "Another document about rules.",
            source_id="rules-001",
            source_system="personal_rules_note",
            source_path="source-inbox/rules/rules.md",
            title="Rules Note",
            document_index=1,
            metadata={"source_type": "rules_note", "source_url": "https://example.test/rules"},
        ),
    ]

    chunks, skipped = make_chunks(rows, target_chars=120, max_chars=180, min_chars=10, created_at="now")

    assert skipped == []
    assert {chunk["source_id"] for chunk in chunks} == {"lesson-001", "rules-001"}
    assert all(chunk["visibility"] == "private" for chunk in chunks)
    assert all(chunk["embedding_allowed"] is True for chunk in chunks)
    assert chunks[0]["chunk_id"].startswith("private:lesson-001:doc-0:chunk-")
    assert chunks[-1]["chunk_role"] == "rules_note"
    assert chunks[-1]["source_url"] == "https://example.test/rules"


def test_make_chunks_skips_embedding_false_rows() -> None:
    rows = [
        normalized_row("Do not embed this.", embedding_allowed=False),
        normalized_row("Embed this reviewed private lesson.", source_id="lesson-002"),
    ]

    chunks, skipped = make_chunks(rows, created_at="now")

    assert len(chunks) == 1
    assert chunks[0]["source_id"] == "lesson-002"
    assert skipped == [{"source_path": "source-inbox/private-lessons/lesson.txt", "reason": "embedding_not_allowed"}]


def test_chunk_ids_are_stable_for_same_content() -> None:
    rows = [normalized_row("Stable content for deterministic private chunk ids.")]

    first, _ = make_chunks(rows, created_at="first")
    second, _ = make_chunks(rows, created_at="second")

    assert first[0]["chunk_id"] == second[0]["chunk_id"]
    assert first[0]["created_at"] == "first"
    assert second[0]["created_at"] == "second"


def test_write_report_includes_counts_and_warnings(tmp_path: Path) -> None:
    rows = [
        normalized_row("Short but useful.", source_id="short"),
        normalized_row("Do not embed this one.", source_id="skip", embedding_allowed=False),
    ]
    chunks, skipped = make_chunks(rows, min_chars=5, created_at="now")
    report_path = tmp_path / "report.md"

    write_report(report_path, len(rows), chunks, skipped)

    report = report_path.read_text(encoding="utf-8")
    assert "Input documents: `2`" in report
    assert "Output chunks: `1`" in report
    assert "Skipped documents: `1`" in report
    assert "Tiny chunk" in report
    assert "embedding_not_allowed" in report


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "chunks.jsonl"
    rows = [{"chunk_id": "one", "text": "Hello"}]

    written = write_jsonl(path, rows)
    loaded = list(read_jsonl(path))

    assert written == 1
    assert loaded == rows
