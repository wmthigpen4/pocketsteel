from __future__ import annotations

from pathlib import Path

from steel_guitar_rag.schema import read_jsonl
from scripts.build_clean_corpus import expand_inputs, iter_clean_records


def test_clean_corpus_flattens_threads_and_strips_html() -> None:
    fixture = Path("tests/fixtures/raw_sgf_sample.jsonl")
    records, stats = iter_clean_records(expand_inputs([str(fixture)]), source="sgf", min_text_chars=10)

    assert stats["clean_records"] == 4
    assert len(records) == 4
    assert records[0]["title"] == "E9 9th string ideas"
    assert records[0]["url"].startswith("https://bb.steelguitarforum.com/")
    assert "<p>" not in records[0]["text"]
    assert "dominant 7th tone" in records[0]["text"]
    assert records[2]["author"] == "Carol"
    assert records[3]["post_id"] == "p1029"
    assert records[3]["posted_at"] == "5 Aug 2013 10:07 am"
    assert records[3]["url"].endswith("start=25#p1029")
    assert records[3]["text"] == "Cabinet drop can make the E strings sound sour. A compensator can help the return note settle."
    assert records[3]["source_policy_id"] is None
    assert records[3]["copyright_review_status"] is None
    assert records[3]["copyright_flags"] == []


def test_read_jsonl_roundtrip_fixture() -> None:
    rows = list(read_jsonl(Path("tests/fixtures/raw_sgf_sample.jsonl")))
    assert len(rows) == 3
    assert rows[0][0] == 1
