from __future__ import annotations

import json
from pathlib import Path

from scripts.private_source_embed_preflight import DEFAULT_COLLECTION, validate_chunks, write_report


def chunk(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "chunk_id": "private:lesson-001:doc-0:chunk-0000:abc123",
        "source_id": "lesson-001",
        "source_system": "private_lesson_transcript",
        "visibility": "private",
        "source_path": "source-inbox/private-lessons/lesson.txt",
        "title": "Private Lesson",
        "file_type": "txt",
        "text": "This is a reviewed private lesson chunk with enough useful content for retrieval preflight.",
        "provenance_status": "reviewed",
        "embedding_allowed": True,
        "redistribution_allowed": False,
        "answer_quote_allowed": "limited",
    }
    row.update(overrides)
    return row


def write_chunks(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_preflight_passes_valid_private_chunks(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    write_chunks(input_path, [chunk()])

    result = validate_chunks(
        input_path,
        vector_path=tmp_path / "corpus-private/vector-stores/chroma",
        collection=DEFAULT_COLLECTION,
    )

    assert result.ok is True
    assert result.chunk_count == 1
    assert result.failures == []
    assert result.source_system_counts["private_lesson_transcript"] == 1
    assert result.visibility_counts["private"] == 1
    assert result.source_id_counts["lesson-001"] == 1


def test_preflight_fails_missing_input(tmp_path: Path) -> None:
    result = validate_chunks(tmp_path / "missing.jsonl")

    assert result.ok is False
    assert result.chunk_count == 0
    assert any("Input file does not exist" in failure for failure in result.failures)


def test_preflight_fails_empty_input(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    input_path.write_text("", encoding="utf-8")

    result = validate_chunks(input_path)

    assert result.ok is False
    assert "Chunk count is 0." in result.failures


def test_preflight_fails_required_metadata_and_empty_text(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    bad = chunk(chunk_id="", source_id="", text="")
    write_chunks(input_path, [bad])

    result = validate_chunks(input_path)

    assert result.ok is False
    assert any("missing required fields" in failure for failure in result.failures)
    assert any("empty text" in failure for failure in result.failures)


def test_preflight_fails_embedding_false_and_tiny_chunks(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    write_chunks(input_path, [chunk(embedding_allowed=False, text="too short")])

    result = validate_chunks(input_path, tiny_threshold=80)

    assert result.ok is False
    assert any("embedding_allowed is false" in failure for failure in result.failures)
    assert any("tiny chunk under threshold" in failure for failure in result.failures)


def test_preflight_fails_pdf_docx_and_curated_candidates(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    write_chunks(
        input_path,
        [
            chunk(
                chunk_id="private:pdf",
                source_path="source-inbox/pdfs/manual.pdf",
                file_type="pdf",
            ),
            chunk(
                chunk_id="private:curated",
                source_id="curated-001",
                source_system="curated_source_candidate",
                source_path="source-inbox/curated-sources/vendor.md",
            ),
        ],
    )

    result = validate_chunks(input_path)

    assert result.ok is False
    assert any("unsupported PDF/DOCX" in failure for failure in result.failures)
    assert any("curated-source candidate" in failure for failure in result.failures)


def test_preflight_fails_non_private_vector_path_or_wrong_collection(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    write_chunks(input_path, [chunk()])

    result = validate_chunks(
        input_path,
        vector_path=tmp_path / "data/rag/chroma/private_sanitized_lessons",
        collection="wrong_collection",
    )

    assert result.ok is False
    assert any("Collection must be" in failure for failure in result.failures)
    assert any("Planned vector path" in failure for failure in result.failures)


def test_public_or_review_visibility_requires_reviewed_provenance(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    write_chunks(input_path, [chunk(visibility="review", provenance_status="review_required")])

    result = validate_chunks(input_path)

    assert result.ok is False
    assert any("requires reviewed provenance" in failure for failure in result.failures)


def test_write_report_includes_counts_failures_and_warnings(tmp_path: Path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    write_chunks(input_path, [chunk(redistribution_allowed=True)])
    result = validate_chunks(input_path, vector_path=tmp_path / "corpus-private/vector-stores/chroma")
    report_path = tmp_path / "report.md"

    write_report(report_path, result, input_path, tiny_threshold=80)

    report = report_path.read_text(encoding="utf-8")
    assert "Private Source Embed Preflight" in report
    assert "Status: `pass`" in report
    assert "`private_lesson_transcript`: 1" in report
    assert "redistribution_allowed=true" in report
