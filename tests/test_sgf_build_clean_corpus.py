from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from steel_guitar_rag.schema import read_jsonl
from scripts.sgf_build_clean_corpus import iter_clean_rows, main


def write_parsed_rows(path: Path) -> None:
    rows = [
        {
            "source": "Steel Guitar Forum",
            "forum_id": 5,
            "forum_name": "Pedal Steel",
            "thread_id": "100",
            "thread_title": "Thread one",
            "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=100",
            "post_uid": "p1",
            "username": "Alice",
            "post_date_raw": "1 Jan 2007 1:00 pm Body one.",
            "post_text_clean": "Alice\nThread one\nby\nAlice\n»\n1 Jan 2007 1:00 pm\nBody one.",
            "links": ["https://example.com"],
            "quotes": [],
        },
        {
            "source": "Steel Guitar Forum",
            "forum_id": 5,
            "forum_name": "Pedal Steel",
            "thread_id": "100",
            "thread_title": "Thread one",
            "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=100",
            "post_uid": "p2",
            "username": "Bob",
            "post_date_raw": "1 Jan 2007 1:15 pm Body two.",
            "post_text_clean": "Bob\nThread one\nby\nBob\n»\n1 Jan 2007 1:15 pm\nBody two.",
            "links": [],
            "quotes": [{"username": "Alice", "text": "Body one."}],
        },
        {
            "source": "Steel Guitar Forum",
            "forum_id": 5,
            "forum_name": "Pedal Steel",
            "thread_id": "101",
            "thread_title": "Thread two",
            "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=101",
            "post_uid": "p3",
            "username": "Carol",
            "post_date_raw": "2 Jan 2007 1:00 pm Body three.",
            "post_text_clean": "Carol\nThread two\nby\nCarol\n»\n2 Jan 2007 1:00 pm\nBody three.",
            "links": [],
            "quotes": [],
        },
    ]
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_iter_clean_rows_projects_expected_sgf_fields(tmp_path: Path) -> None:
    parsed = tmp_path / "thread-100.jsonl"
    write_parsed_rows(parsed)
    stats: Counter[str] = Counter()

    rows = list(iter_clean_rows([parsed], forum_id=5, limit_threads=None, sample_rows=None, stats=stats))

    assert len(rows) == 3
    assert list(rows[0]) == [
        "source",
        "forum_name",
        "forum_id",
        "thread_id",
        "thread_title",
        "thread_url",
        "post_uid",
        "username",
        "post_date_raw",
        "text",
        "links",
        "quotes",
    ]
    assert rows[0]["text"] == "Body one."
    assert rows[0]["links"] == ["https://example.com"]
    assert rows[1]["quotes"] == [{"username": "Alice", "text": "Body one."}]
    assert stats["input_rows"] == 3
    assert stats["written_rows"] == 3
    assert stats["threads_seen"] == 2


def test_main_writes_sample_and_honors_thread_limit(tmp_path: Path) -> None:
    parsed = tmp_path / "thread-100.jsonl"
    output = tmp_path / "clean.jsonl"
    write_parsed_rows(parsed)

    status = main(
        [
            "--input-glob",
            str(parsed),
            "--forum-id",
            "5",
            "--limit-threads",
            "1",
            "--sample",
            "10",
            "--output",
            str(output),
        ]
    )

    rows = [row for _, row in read_jsonl(output)]
    assert status == 0
    assert len(rows) == 2
    assert {row["thread_id"] for row in rows} == {"100"}
