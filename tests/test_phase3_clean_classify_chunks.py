from __future__ import annotations

import json
from pathlib import Path

from scripts.phase3_clean_classify_chunks import clean_and_classify_chunk, main


def base_chunk(text: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "chunk_id": "sgf:test:chunk-0001",
        "source_system": "sgf_phpbb_current",
        "forum_name": "Electronics",
        "forum_id": 11,
        "thread_id": "100",
        "thread_title": "Useful amp advice",
        "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=100",
        "post_uids": ["p1"],
        "usernames": ["Alice"],
        "chunk_text": text,
        "links": [],
    }
    row.update(overrides)
    return row


def test_top_artifacts_are_removed_and_duplicate_body_collapsed() -> None:
    row = base_chunk("Rick / 1 Jan 2007 1:00 pm Try a grounded outlet first. Top Try a grounded outlet first.")

    cleaned = clean_and_classify_chunk(row)

    assert "Top" not in cleaned["answer_text"]
    assert cleaned["answer_text"].count("Try a grounded outlet first.") == 1
    assert "top_removed" in cleaned["cleanup_flags"]
    assert "duplicate_sentence_removed" in cleaned["cleanup_flags"]


def test_email_contact_text_is_flagged_and_removed_from_answer_text() -> None:
    row = base_chunk("I can help with that repair. Email me at picker@example.com or call 615-555-1212.")

    cleaned = clean_and_classify_chunk(row)

    assert "picker@example.com" not in cleaned["answer_text"]
    assert "615-555-1212" not in cleaned["answer_text"]
    assert "[contact removed]" in cleaned["answer_text"]
    assert cleaned["chunk_role"] == "contact_block"
    assert "contact_block_removed" in cleaned["cleanup_flags"]


def test_signatures_are_flagged_without_destroying_answer_body() -> None:
    row = base_chunk(
        "Use a 500K pot if that is what the pedal expects.\n"
        "------------------\n"
        "Zum D-10, Nashville 400, Goodrich volume pedal"
    )

    cleaned = clean_and_classify_chunk(row)

    assert "Use a 500K pot" in cleaned["answer_text"]
    assert "Zum D-10" not in cleaned["answer_text"]
    assert "Zum D-10" in cleaned["signature_text"]
    assert cleaned["chunk_role"] == "answer_advice"
    assert "signature_removed" in cleaned["cleanup_flags"]


def test_question_only_chunks_are_classified() -> None:
    row = base_chunk("Does anyone know what speaker came in a Sho-Bud Compactra amp?")

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["chunk_role"] == "question"
    assert cleaned["answer_density"] < 0.3


def test_answer_advice_like_chunks_are_preserved() -> None:
    text = "Check the speaker connection first because a loose wire can buzz. Try another cable before replacing parts."
    row = base_chunk(text)

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["chunk_role"] == "answer_advice"
    assert cleaned["answer_text"] == text
    assert cleaned["answer_density"] > 0.3


def test_useful_advice_with_price_or_ebay_language_is_not_automatically_sale_wanted() -> None:
    row = base_chunk(
        "A used Dunlop pot might be $25 on eBay, but I would first check the sweep and use a 100K pot because "
        "that is what most wah pedals expect."
    )

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["chunk_role"] == "answer_advice"
    assert "sale_wanted" not in cleaned["detected_roles"]
    assert "use a 100K pot" in cleaned["answer_text"]


def test_contact_details_are_removed_while_useful_advice_is_preserved_when_possible() -> None:
    row = base_chunk(
        "Email me at picker@example.com if you want, but check the ground because a bad cable can hum. "
        "Try another cable before replacing the pickup."
    )

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["chunk_role"] == "answer_advice"
    assert "picker@example.com" not in cleaned["answer_text"]
    assert "[contact removed]" in cleaned["answer_text"]
    assert "check the ground" in cleaned["answer_text"]
    assert "contact_block" in cleaned["detected_roles"]


def test_inline_gear_signatures_are_removed_from_answer_advice_text() -> None:
    row = base_chunk(
        "Check the speaker connection first because a loose wire can buzz. "
        "Try another cable before replacing parts. "
        "Dave - Zum D-10, Nashville 400, Goodrich volume pedal, Hilton pedal"
    )

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["chunk_role"] == "answer_advice"
    assert "Check the speaker connection" in cleaned["answer_text"]
    assert "Zum D-10" not in cleaned["answer_text"]
    assert "Zum D-10" in cleaned["signature_text"]
    assert "inline_gear_signature_removed" in cleaned["cleanup_flags"]


def test_quote_heavy_advice_is_not_mislabeled_as_event_when_event_terms_do_not_dominate() -> None:
    row = base_chunk(
        "Brad wrote: this amp buzzed at the show. Dave wrote: I would check the speaker cable because "
        "a loose plug can buzz. Lee wrote: try another ground before replacing the amp."
    )

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["chunk_role"] == "answer_advice"
    assert "event" not in cleaned["detected_roles"]
    assert "quote_marker_detected" in cleaned["cleanup_flags"]


def test_source_metadata_and_post_identity_are_preserved_when_available() -> None:
    row = base_chunk("Try cleaning the jack before replacing the pickup.", post_uids=["p1", "p2"])

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["source_system"] == "sgf_phpbb_current"
    assert cleaned["forum_name"] == "Electronics"
    assert cleaned["thread_url"].startswith("https://")
    assert cleaned["source_metadata_complete"] is True
    assert cleaned["post_identity_complete"] is True
    assert cleaned["post_uids"] == ["p1", "p2"]


def test_missing_source_metadata_is_reported() -> None:
    row = base_chunk("Try another amp.", thread_url="")

    cleaned = clean_and_classify_chunk(row)

    assert cleaned["source_metadata_complete"] is False
    assert cleaned["missing_source_metadata"] == ["thread_url"]


def test_cleanup_is_non_destructive_to_raw_input() -> None:
    row = base_chunk("Top Contact me at picker@example.com")
    original = dict(row)

    cleaned = clean_and_classify_chunk(row)

    assert row == original
    assert cleaned["raw_text"] == original["chunk_text"]
    assert cleaned["raw_text"] != cleaned["answer_text"]


def test_cli_writes_sample_output_and_report(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.jsonl"
    output_path = tmp_path / "out.jsonl"
    report_path = tmp_path / "report.md"
    rows = [
        base_chunk("Top Does anyone know what this pickup is?"),
        base_chunk("Check the ground because that can reduce hum."),
        base_chunk("For sale: Goodrich pedal, $100."),
    ]
    with input_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    status = main(["--input", str(input_path), "--output", str(output_path), "--report", str(report_path)])

    output_rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert status == 0
    assert [row["chunk_role"] for row in output_rows] == ["question", "answer_advice", "sale_wanted"]
    assert report_path.exists()
    assert "Role Counts" in report_path.read_text(encoding="utf-8")
