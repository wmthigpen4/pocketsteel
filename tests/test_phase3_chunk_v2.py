from __future__ import annotations

import json
from pathlib import Path

from scripts.phase3_chunk_v2 import build_chunks, main


def classified_record(text: str, role: str = "answer_advice", **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "chunk_id": f"source-{role}-1",
        "source_system": "sgf_phpbb_current",
        "forum_name": "Electronics",
        "thread_id": "thread-1",
        "thread_title": "Amp hum",
        "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
        "post_uids": ["p1"],
        "answer_text": text,
        "chunk_role": role,
        "post_role": role,
        "detected_roles": [role],
        "quality_score": 0.8,
        "noise_score": 0.1,
        "cleanup_flags": [],
        "source_metadata_complete": True,
    }
    row.update(overrides)
    return row


def test_source_metadata_and_post_identity_are_preserved() -> None:
    records = [
        classified_record(
            "Check the ground because that can reduce hum.",
            post_uids=["p1", "p2"],
            source_url="https://example.test/source",
        )
    ]

    chunks = build_chunks(records)

    assert len(chunks) == 1
    assert chunks[0]["source_system"] == "sgf_phpbb_current"
    assert chunks[0]["forum_name"] == "Electronics"
    assert chunks[0]["thread_id"] == "thread-1"
    assert chunks[0]["thread_title"] == "Amp hum"
    assert chunks[0]["source_url"] == "https://example.test/source"
    assert chunks[0]["post_uids"] == ["p1", "p2"]
    assert chunks[0]["source_metadata_complete"] is True


def test_answer_advice_text_is_kept() -> None:
    records = [classified_record("Check the speaker cable because a loose plug can buzz.")]

    chunks = build_chunks(records)

    assert chunks[0]["chunk_role"] == "answer_advice"
    assert "Check the speaker cable" in chunks[0]["chunk_text"]


def test_question_only_chunks_are_not_promoted_as_answer_chunks() -> None:
    records = [classified_record("Does anyone know which speaker fits?", role="question")]

    chunks = build_chunks(records)

    assert len(chunks) == 1
    assert chunks[0]["chunk_role"] == "question"
    assert "question_unpaired" in chunks[0]["cleanup_flags"]


def test_question_can_pair_with_following_answer_intentionally() -> None:
    records = [
        classified_record("Does anyone know why this amp hums?", role="question", chunk_id="q1", post_uids=["p1"]),
        classified_record("Check the ground because a bad cable can cause hum.", chunk_id="a1", post_uids=["p2"]),
    ]

    chunks = build_chunks(records)

    assert len(chunks) == 1
    assert chunks[0]["chunk_role"] == "answer_advice"
    assert "Question:" in chunks[0]["chunk_text"]
    assert "Answer:" in chunks[0]["chunk_text"]
    assert "question_paired" in chunks[0]["cleanup_flags"]
    assert chunks[0]["post_role_summary"] == {"answer_advice": 1, "question": 1}


def test_contact_signature_and_link_only_records_are_excluded_from_answer_chunks() -> None:
    records = [
        classified_record("Email me at [contact removed].", role="contact_block", chunk_id="c1"),
        classified_record("Zum D-10, Nashville 400", role="gear_signature", chunk_id="g1"),
        classified_record("https://example.test", role="link_only", chunk_id="l1"),
        classified_record("Check the pot because a worn pot can scratch.", chunk_id="a1"),
    ]

    chunks = build_chunks(records)

    assert len(chunks) == 1
    assert chunks[0]["chunk_role"] == "answer_advice"
    assert "[contact removed]" not in chunks[0]["chunk_text"]
    assert "Zum D-10" not in chunks[0]["chunk_text"]
    assert "https://example.test" not in chunks[0]["chunk_text"]


def test_oversized_answer_chunks_split() -> None:
    long_text = " ".join(f"word{i}" for i in range(25))
    records = [classified_record(long_text)]

    chunks = build_chunks(records, target_words=10, max_words=10, min_words=3)

    assert len(chunks) == 3
    assert all("oversized_split" in chunk["cleanup_flags"] for chunk in chunks)


def test_tiny_junk_chunks_are_skipped() -> None:
    records = [
        classified_record("Thanks", role="joke_chatter", chunk_id="tiny"),
        classified_record("Try another cable because cables fail.", chunk_id="answer"),
    ]

    chunks = build_chunks(records)

    assert len(chunks) == 1
    assert chunks[0]["chunk_role"] == "answer_advice"
    assert "Thanks" not in chunks[0]["chunk_text"]


def test_mixed_topic_content_is_flagged() -> None:
    records = [
        classified_record(
            "Check the amp because it may be a ground issue, but the show is Saturday.",
            detected_roles=["answer_advice", "event"],
        )
    ]

    chunks = build_chunks(records)

    assert "mixed_topic_flagged" in chunks[0]["cleanup_flags"]
    assert "mixed_topic_quarantined" in chunks[0]["cleanup_flags"]
    assert chunks[0]["noise_score"] >= 0.65
    assert chunks[0]["quality_score"] <= 0.35


def test_quote_heavy_content_is_flagged() -> None:
    records = [
        classified_record(
            "Brad wrote: try another speaker. I would check the speaker because it can buzz.",
            cleanup_flags=["quote_marker_detected"],
        )
    ]

    chunks = build_chunks(records)

    assert "quote_heavy_flagged" in chunks[0]["cleanup_flags"]


def test_chunk_ids_are_stable_and_deterministic() -> None:
    records = [
        classified_record("Check the ground because that can reduce hum.", chunk_id="a1"),
        classified_record("Try a different cable because cables fail.", chunk_id="a2"),
    ]

    first = build_chunks(records)
    second = build_chunks(records)

    assert [chunk["chunk_id"] for chunk in first] == [chunk["chunk_id"] for chunk in second]


def test_cli_writes_sample_chunks_and_report(tmp_path: Path) -> None:
    input_path = tmp_path / "classified.jsonl"
    output_path = tmp_path / "chunks.jsonl"
    report_path = tmp_path / "report.md"
    rows = [
        classified_record("Does anyone know why this hums?", role="question", chunk_id="q1"),
        classified_record("Check the ground because a bad cable can hum.", chunk_id="a1"),
    ]
    with input_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    status = main(["--input", str(input_path), "--output", str(output_path), "--report", str(report_path)])

    output_rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert status == 0
    assert len(output_rows) == 1
    assert output_rows[0]["chunk_role"] == "answer_advice"
    assert report_path.exists()
    assert "Role Counts" in report_path.read_text(encoding="utf-8")
