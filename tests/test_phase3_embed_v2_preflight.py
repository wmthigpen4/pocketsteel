from __future__ import annotations

import json
from pathlib import Path

from scripts.phase3_embed_v2_preflight import V1_CHROMA_PATH, evaluate_preflight, main


def chunk_record(text: str = "Check the ground because a bad cable can hum.", **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "chunk_id": "v2:thread-1:answer_advice:0001",
        "source_system": "sgf_phpbb_current",
        "forum_name": "Electronics",
        "thread_id": "thread-1",
        "thread_title": "Amp hum",
        "source_url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
        "post_uids": ["p1"],
        "chunk_text": text,
        "chunk_role": "answer_advice",
        "post_role_summary": {"answer_advice": 1},
        "quality_score": 0.8,
        "noise_score": 0.1,
        "cleanup_flags": [],
        "source_metadata_complete": True,
    }
    row.update(overrides)
    return row


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    return path


def test_safe_v2_paths_pass(tmp_path: Path) -> None:
    chunk_input = write_jsonl(tmp_path / "corpus-v2" / "chunks-v2.jsonl", [chunk_record()])

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
        planned_output_path=tmp_path / "corpus-v2" / "chunks-v2.jsonl",
    )

    assert result["passed"] is True
    assert result["total_chunks"] == 1
    assert result["answer_advice_chunk_count"] == 1
    assert result["embedding_commands_executed"] is False


def test_v1_chroma_path_collision_fails(tmp_path: Path) -> None:
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", [chunk_record()])

    result = evaluate_preflight(chunk_input=chunk_input, target_chroma_path=V1_CHROMA_PATH)

    assert result["passed"] is False
    assert any("v1 Chroma" in failure for failure in result["failures"])


def test_missing_metadata_fails(tmp_path: Path) -> None:
    chunk_input = write_jsonl(
        tmp_path / "chunks-v2.jsonl",
        [chunk_record(source_url="", source_metadata_complete=False)],
    )

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
    )

    assert result["passed"] is False
    assert any("metadata completeness" in failure for failure in result["failures"])


def test_missing_post_identity_fails(tmp_path: Path) -> None:
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", [chunk_record(post_uids=[])])

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
    )

    assert result["passed"] is False
    assert any("post identity completeness" in failure for failure in result["failures"])


def test_excessive_noise_fails(tmp_path: Path) -> None:
    rows = [
        chunk_record(noise_score=0.95, quality_score=0.2),
        chunk_record(chunk_id="v2:thread-1:answer_advice:0002", noise_score=0.95, quality_score=0.2),
    ]
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", rows)

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
        max_avg_noise_score=0.60,
    )

    assert result["passed"] is False
    assert any("average noise_score" in failure for failure in result["failures"])


def test_leakage_fails(tmp_path: Path) -> None:
    rows = [
        chunk_record("Email me at picker@example.com and check the ground."),
        chunk_record("Check the speaker cable because a loose plug can buzz.", chunk_id="v2:thread-1:answer_advice:0002"),
    ]
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", rows)

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
        max_leakage_rate=0.1,
    )

    assert result["passed"] is False
    assert any("leakage rate" in failure for failure in result["failures"])


def test_named_gear_signature_leakage_fails(tmp_path: Path) -> None:
    text = (
        "This amp is loud enough for rehearsal. "
        "Darvin Willhoite MSA Millennium, Legend, Studio Pro, Nashville 400, Goodrich pedal, Zum D10"
    )
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", [chunk_record(text)])

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
    )

    assert result["passed"] is False
    assert result["leakage_counts"]["signature"] == 1


def test_gear_rich_user_experience_is_not_signature_leakage(tmp_path: Path) -> None:
    text = (
        "My ZBs and Fenders sounded great through the amp. My Kline did not. "
        "The Sho-Bud sounded OK, and a Carter Starter sounded surprisingly good through the Nashville 112."
    )
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", [chunk_record(text)])

    result = evaluate_preflight(
        chunk_input=chunk_input,
        target_chroma_path=tmp_path / "corpus-v2" / "vector-stores" / "chroma",
    )

    assert result["passed"] is True
    assert result["leakage_counts"]["signature"] == 0


def test_cli_does_not_create_chroma_or_run_embeddings(tmp_path: Path) -> None:
    chunk_input = write_jsonl(tmp_path / "chunks-v2.jsonl", [chunk_record()])
    target_chroma = tmp_path / "corpus-v2" / "vector-stores" / "chroma"
    report = tmp_path / "report.md"

    status = main(
        [
            "--chunk-input",
            str(chunk_input),
            "--target-chroma-path",
            str(target_chroma),
            "--report",
            str(report),
        ]
    )

    assert status == 0
    assert report.exists()
    assert not target_chroma.exists()
    assert "Embedding commands executed: `False`" in report.read_text(encoding="utf-8")
