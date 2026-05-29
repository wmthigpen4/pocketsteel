from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.embed_private_sources_chroma import (
    DEFAULT_COLLECTION,
    embed_private_sources,
    eligible_chunks,
    metadata_for_chunk,
)


class FakeCollection:
    def __init__(self) -> None:
        self.upserts: list[dict[str, object]] = []

    def upsert(self, *, ids, documents, metadatas, embeddings):  # type: ignore[no-untyped-def]
        self.upserts.append(
            {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "embeddings": embeddings,
            }
        )

    def count(self) -> int:
        return sum(len(upsert["ids"]) for upsert in self.upserts)


def chunk(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "chunk_id": "private:lesson-001:doc-0:chunk-0000:abc123",
        "source_id": "lesson-001",
        "source_system": "private_lesson_transcript",
        "visibility": "private",
        "source_path": "source-inbox/private-lessons/lesson.txt",
        "title": "Private Lesson",
        "file_type": "txt",
        "document_index": 0,
        "chunk_index": 0,
        "text": (
            "Reviewed private lesson chunk with enough text for the preflight threshold, "
            "including practical steel guitar context and safe private-source metadata."
        ),
        "source_url": "",
        "provenance_status": "reviewed",
        "redistribution_allowed": False,
        "embedding_allowed": True,
        "answer_quote_allowed": "limited",
        "chunk_role": "lesson_or_transcript",
        "quality_score": 90,
        "noise_score": 0,
    }
    row.update(overrides)
    return row


def write_chunks(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_dry_run_does_not_create_chroma(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    vector_path = tmp_path / "corpus-private/vector-stores/chroma"
    report = tmp_path / "corpus-private/reports/private-source-embedding-report.md"
    write_chunks(input_path, [chunk()])

    result = embed_private_sources(
        input_path=input_path,
        vector_path=vector_path,
        collection_name=DEFAULT_COLLECTION,
        model="test-embed",
        batch_size=2,
        dry_run=True,
        confirm_preflight_pass=False,
        reset_private_collection=False,
        report_path=report,
    )

    assert result.dry_run is True
    assert result.chunks_embedded == 0
    assert result.chunks_eligible == 1
    assert report.exists()
    assert not vector_path.exists()


def test_refuses_sgf_v1_v2_vector_paths(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    write_chunks(input_path, [chunk()])

    with pytest.raises(SystemExit, match="target vector path"):
        embed_private_sources(
            input_path=input_path,
            vector_path=tmp_path / "corpus-v2/vector-stores/chroma",
            collection_name=DEFAULT_COLLECTION,
            model="test-embed",
            batch_size=1,
            dry_run=True,
            confirm_preflight_pass=False,
            reset_private_collection=False,
            report_path=tmp_path / "report.md",
        )


def test_real_embedding_requires_confirm_preflight_pass(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    write_chunks(input_path, [chunk()])

    with pytest.raises(SystemExit, match="confirm-preflight-pass"):
        embed_private_sources(
            input_path=input_path,
            vector_path=tmp_path / "corpus-private/vector-stores/chroma",
            collection_name=DEFAULT_COLLECTION,
            model="test-embed",
            batch_size=1,
            dry_run=False,
            confirm_preflight_pass=False,
            reset_private_collection=False,
            report_path=tmp_path / "report.md",
        )


def test_embeds_only_embedding_allowed_true_rows_in_temp_collection(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    allowed = chunk()
    disallowed = chunk(
        chunk_id="private:lesson-002:doc-0:chunk-0000:def456",
        source_id="lesson-002",
        text="This row should be filtered before upsert because embedding is not allowed.",
        embedding_allowed=False,
    )
    filtered, total, skipped = eligible_chunks([allowed, disallowed])
    assert total == 2
    assert skipped == 1
    assert filtered == [allowed]

    # The real embed input remains preflight-clean because false rows are
    # rejected before any vector write is allowed.
    write_chunks(input_path, [allowed])
    fake = FakeCollection()

    result = embed_private_sources(
        input_path=input_path,
        vector_path=tmp_path / "corpus-private/vector-stores/chroma",
        collection_name=DEFAULT_COLLECTION,
        model="test-embed",
        batch_size=1,
        dry_run=False,
        confirm_preflight_pass=True,
        reset_private_collection=False,
        report_path=tmp_path / "report.md",
        collection_factory=lambda _path, _name, _reset: fake,
        embed_texts=lambda texts, _model: [[float(len(text))] for text in texts],
    )

    assert result.chunks_embedded == 1
    assert fake.count() == 1
    assert fake.upserts[0]["ids"] == ["private:lesson-001:doc-0:chunk-0000:abc123"]
    assert fake.upserts[0]["documents"] == [allowed["text"]]


def test_metadata_is_preserved(tmp_path: Path) -> None:
    row = chunk(source_url="https://example.test/private-note", quality_score=88, noise_score=3)

    metadata = metadata_for_chunk(row)

    assert metadata["chunk_id"] == row["chunk_id"]
    assert metadata["source_id"] == row["source_id"]
    assert metadata["source_system"] == row["source_system"]
    assert metadata["visibility"] == "private"
    assert metadata["source_path"] == row["source_path"]
    assert metadata["title"] == row["title"]
    assert metadata["source_url"] == "https://example.test/private-note"
    assert metadata["quality_score"] == 88
    assert metadata["noise_score"] == 3


def test_reset_requires_explicit_flag(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    write_chunks(input_path, [chunk()])
    reset_values: list[bool] = []

    embed_private_sources(
        input_path=input_path,
        vector_path=tmp_path / "corpus-private/vector-stores/chroma",
        collection_name=DEFAULT_COLLECTION,
        model="test-embed",
        batch_size=1,
        dry_run=False,
        confirm_preflight_pass=True,
        reset_private_collection=False,
        report_path=tmp_path / "report.md",
        collection_factory=lambda _path, _name, reset: reset_values.append(reset) or FakeCollection(),
        embed_texts=lambda texts, _model: [[1.0] for _text in texts],
    )

    assert reset_values == [False]

    embed_private_sources(
        input_path=input_path,
        vector_path=tmp_path / "corpus-private/vector-stores/chroma",
        collection_name=DEFAULT_COLLECTION,
        model="test-embed",
        batch_size=1,
        dry_run=False,
        confirm_preflight_pass=True,
        reset_private_collection=True,
        report_path=tmp_path / "report.md",
        collection_factory=lambda _path, _name, reset: reset_values.append(reset) or FakeCollection(),
        embed_texts=lambda texts, _model: [[1.0] for _text in texts],
    )

    assert reset_values == [False, True]


def test_no_private_text_is_printed_in_logs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "corpus-private/chunks/source-inbox-chunks.jsonl"
    private_phrase = "secret private pedal move"
    write_chunks(
        input_path,
        [
            chunk(
                text=(
                    f"Reviewed chunk with {private_phrase} and enough length "
                    "to pass the private embedding preflight threshold safely."
                )
            )
        ],
    )

    embed_private_sources(
        input_path=input_path,
        vector_path=tmp_path / "corpus-private/vector-stores/chroma",
        collection_name=DEFAULT_COLLECTION,
        model="test-embed",
        batch_size=1,
        dry_run=True,
        confirm_preflight_pass=False,
        reset_private_collection=False,
        report_path=tmp_path / "report.md",
    )

    captured = capsys.readouterr()
    assert private_phrase not in captured.out
    assert private_phrase not in captured.err
