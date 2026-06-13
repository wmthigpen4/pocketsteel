from __future__ import annotations

import json
from pathlib import Path

from scripts.normalize_source_inbox_text import normalize_caption_text, normalize_source_inbox, normalize_text_or_markdown


def write_provenance(path: Path, source_path: Path, **overrides: object) -> None:
    record = {
        "source_id": "lesson-001",
        "path": source_path.as_posix(),
        "title": "Private Lesson",
        "author_or_creator": "Teacher",
        "source_type": "lesson_transcript",
        "source_system": "private_lesson_transcript",
        "visibility": "private",
        "redistribution_allowed": False,
        "embedding_allowed": True,
        "answer_quote_allowed": "limited",
        "source_url": None,
        "notes": "Reviewed for private personal use.",
        "reviewed_at": "2026-05-29",
        "reviewed_by": "user",
    }
    record.update(overrides)
    path.write_text(json.dumps({"sources": [record]}), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_vtt_normalizer_removes_timestamps_and_repeated_caption_fragments() -> None:
    text = """WEBVTT

00:00:00.000 --> 00:00:02.000
Teacher: Start with the A pedal.

00:00:02.000 --> 00:00:04.000
Teacher: Start with the A pedal.

00:00:04.000 --> 00:00:06.000
Then add the F lever.
"""

    normalized = normalize_caption_text(text)

    assert "00:00" not in normalized
    assert "WEBVTT" not in normalized
    assert normalized.count("Teacher: Start with the A pedal.") == 1
    assert "Then add the F lever." in normalized


def test_text_normalizer_preserves_headings_and_normalizes_whitespace() -> None:
    text = "# Lesson Notes\n\nUse   the A pedal.\nThen   add the F lever.\n\nPractice slowly."

    normalized = normalize_text_or_markdown(text)

    assert normalized.startswith("# Lesson Notes")
    assert "Use the A pedal. Then add the F lever." in normalized
    assert "Practice slowly." in normalized


def test_text_normalizer_preserves_tab_heavy_spacing() -> None:
    text = "E9 tab\n\n3--5A--6\n4------6F\n5--5A--6A\n"

    normalized = normalize_text_or_markdown(text)

    assert "3--5A--6" in normalized
    assert "4------6F" in normalized
    assert "5--5A--6A" in normalized


def test_normalize_source_inbox_requires_provenance_and_skips_pdfs(tmp_path: Path) -> None:
    source_root = tmp_path / "source-inbox"
    transcripts = source_root / "transcripts"
    pdfs = source_root / "pdfs"
    transcripts.mkdir(parents=True)
    pdfs.mkdir(parents=True)
    (transcripts / "missing.txt").write_text("Private text without provenance.", encoding="utf-8")
    (pdfs / "manual.pdf").write_bytes(b"%PDF-1.7")

    output = tmp_path / "corpus-private/normalized/source-inbox-documents.jsonl"
    skipped_report = tmp_path / "corpus-private/reports/source-inbox-normalize-skipped.md"

    rows, skipped = normalize_source_inbox(
        source_root=source_root,
        provenance_path=source_root / "provenance.json",
        output_path=output,
        skipped_report_path=skipped_report,
    )

    assert rows == []
    assert output.exists()
    assert read_jsonl(output) == []
    reasons = {item.reason for item in skipped}
    assert "missing_provenance" in reasons
    assert "unsupported_for_text_normalizer" in reasons
    report = skipped_report.read_text(encoding="utf-8")
    assert "Private text without provenance." not in report
    assert "missing.txt" in report
    assert "manual.pdf" in report


def test_normalize_source_inbox_writes_private_jsonl_with_provenance(tmp_path: Path) -> None:
    source_root = tmp_path / "source-inbox"
    private_lessons = source_root / "private-lessons"
    private_lessons.mkdir(parents=True)
    lesson_path = private_lessons / "lesson.vtt"
    lesson_path.write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nTeacher: Pick softer.\n",
        encoding="utf-8",
    )
    provenance_path = source_root / "provenance.json"
    write_provenance(provenance_path, lesson_path)

    output = tmp_path / "corpus-private/normalized/source-inbox-documents.jsonl"
    skipped_report = tmp_path / "corpus-private/reports/source-inbox-normalize-skipped.md"

    rows, skipped = normalize_source_inbox(
        source_root=source_root,
        provenance_path=provenance_path,
        output_path=output,
        skipped_report_path=skipped_report,
    )

    assert skipped == []
    assert len(rows) == 1
    persisted = read_jsonl(output)
    assert persisted[0]["source_id"] == "lesson-001"
    assert persisted[0]["source_system"] == "private_lesson_transcript"
    assert persisted[0]["visibility"] == "private"
    assert persisted[0]["source_path"] == lesson_path.as_posix()
    assert persisted[0]["file_type"] == "vtt"
    assert persisted[0]["text"] == "Teacher: Pick softer."
    assert persisted[0]["provenance_status"] == "reviewed"
    assert persisted[0]["embedding_allowed"] is True
    assert persisted[0]["redistribution_allowed"] is False
    assert persisted[0]["answer_quote_allowed"] == "limited"


def test_normalize_source_inbox_skips_curated_source_candidates(tmp_path: Path) -> None:
    source_root = tmp_path / "source-inbox"
    curated = source_root / "curated-sources"
    curated.mkdir(parents=True)
    source_path = curated / "vendor.md"
    source_path.write_text("https://example.test/vendor", encoding="utf-8")
    provenance_path = source_root / "provenance.json"
    write_provenance(
        provenance_path,
        source_path,
        source_system="curated_source_candidate",
        source_type="curated_link_note",
        visibility="review",
    )

    output = tmp_path / "corpus-private/normalized/source-inbox-documents.jsonl"
    skipped_report = tmp_path / "corpus-private/reports/source-inbox-normalize-skipped.md"

    rows, skipped = normalize_source_inbox(
        source_root=source_root,
        provenance_path=provenance_path,
        output_path=output,
        skipped_report_path=skipped_report,
    )

    assert rows == []
    assert [item.reason for item in skipped] == ["belongs_in_curated_source_registry"]
