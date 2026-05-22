from __future__ import annotations

from scripts.chunk_corpus import chunk_text, make_chunks


def test_chunk_text_keeps_overlap() -> None:
    text = "\n\n".join(
        [
            "The 9th string D is useful as a dominant seventh sound.",
            "Players also mention scale movement and passing notes.",
            "Another paragraph gives enough material to force a second chunk.",
        ]
    )

    chunks = chunk_text(text, chunk_chars=105, overlap_chars=30)

    assert len(chunks) >= 2
    assert "dominant seventh" in chunks[0]
    assert any("passing notes" in chunk for chunk in chunks)


def test_make_chunks_carries_source_metadata() -> None:
    records = [
        {
            "doc_id": "sgf:test",
            "source": "sgf",
            "title": "E9 9th string ideas",
            "url": "https://bb.steelguitarforum.com/viewtopic.php?p=1#1",
            "forum": "Pedal Steel",
            "thread_id": "1",
            "post_id": "1",
            "author": "Alice",
            "posted_at": "2002-01-01",
            "text": "The 9th string D is useful as a dominant 7th tone with E lowers.",
        }
    ]

    chunks = make_chunks(records, chunk_chars=900, overlap_chars=150, min_chunk_chars=10)

    assert len(chunks) == 1
    assert chunks[0]["doc_id"] == "sgf:test"
    assert chunks[0]["title"] == "E9 9th string ideas"
    assert chunks[0]["url"].startswith("https://")

