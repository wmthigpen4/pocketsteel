from __future__ import annotations

import json
from pathlib import Path

from pocketsteel.curated_guidance_retriever import (
    ENABLE_CURATED_GUIDANCE_ENV,
    curated_guidance_retrieval_enabled,
    search_curated_guidance,
    search_rows,
)


def guidance_row(
    title: str,
    body: str,
    *,
    source_path: str | None = None,
    source_sha256: str | None = None,
    topics: list[str] | None = None,
    technique_tags: list[str] | None = None,
    quality_flags: list[str] | None = None,
) -> dict[str, object]:
    return {
        "content_layer": "curated_guidance",
        "visibility": "private_review",
        "source_path": source_path or f"summary-draft/{title.lower().replace(' ', '-')}.md",
        "source_filename": "guidance_draft.md",
        "source_sha256": source_sha256 or f"sha-{title.lower().replace(' ', '-')}",
        "title": title,
        "body": body,
        "word_count": len(body.split()),
        "topics": topics if topics is not None else ["practice"],
        "technique_tags": technique_tags if technique_tags is not None else [],
        "instrument": "E9",
        "strings": [],
        "pedals_levers": [],
        "frets": [],
        "keys": [],
        "difficulty": "intermediate",
        "needs_review": True,
        "quality_flags": quality_flags or [],
    }


def fixture_rows() -> list[dict[str, object]]:
    return [
        guidance_row(
            "Split Tuning On String 6",
            "Split tuning on string 6 is about tuning the combined lower and raise so the E9 copedent gives a usable pitch. "
            "Work slowly, check the pedal and lever together, then compare the split against nearby steel guitar chord tones.",
            topics=["split tuning", "copedent"],
            technique_tags=["pedal movement"],
        ),
        guidance_row(
            "Right Hand Pick Blocking",
            "Pick blocking is a right-hand muting approach where the same fingerpick that picked a string returns to stop it. "
            "Practice two strings at a time, listen for silence between notes, and keep the steel bar quiet.",
            topics=["blocking", "right hand"],
            technique_tags=["blocking", "right hand"],
        ),
        guidance_row(
            "B+C Pedal Uses",
            "B+C pedals are useful for connected melody, minor movement, and passing sounds on E9. "
            "Compare the B pedal and C pedal together against nearby A+B positions so the pedal movement feels musical.",
            topics=["B+C pedals", "pedal movement"],
            technique_tags=["pedal movement"],
        ),
        guidance_row(
            "B To Bb Lever Alternatives",
            "A lick that mentions the B-to-Bb lever can often be adapted with a vertical lever, a nearby fret, or a different grip. "
            "Keep the E9 chord tone target in mind and do not force the exact lever if your copedent lacks it.",
            topics=["B-to-Bb", "levers", "licks"],
            technique_tags=["pedal movement"],
        ),
        guidance_row(
            "Dominant Harmonized Scale",
            "A harmonized scale over a dominant chord needs the melody note and supporting chord tones to agree. "
            "On E9, test each grip by ear and by interval, especially when moving between pedals and levers.",
            topics=["harmonized scale", "dominant harmony"],
            technique_tags=["grips"],
        ),
    ]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def test_feature_flag_defaults_off() -> None:
    assert curated_guidance_retrieval_enabled({}) is False
    assert curated_guidance_retrieval_enabled({ENABLE_CURATED_GUIDANCE_ENV: "0"}) is False
    assert curated_guidance_retrieval_enabled({ENABLE_CURATED_GUIDANCE_ENV: "1"}) is True
    assert curated_guidance_retrieval_enabled({ENABLE_CURATED_GUIDANCE_ENV: "true"}) is True


def test_feature_flag_off_returns_no_results_even_when_jsonl_exists(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl"
    write_jsonl(input_path, fixture_rows())

    assert search_curated_guidance(
        "What is pick blocking?",
        input_path=input_path,
        env={ENABLE_CURATED_GUIDANCE_ENV: "0"},
    ) == []


def test_feature_flag_on_loads_local_private_review_jsonl(tmp_path: Path) -> None:
    input_path = tmp_path / "corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl"
    write_jsonl(input_path, fixture_rows())

    results = search_curated_guidance(
        "What is pick blocking?",
        input_path=input_path,
        env={ENABLE_CURATED_GUIDANCE_ENV: "1"},
        top_k=3,
    )

    assert results
    assert results[0]["content_layer"] == "curated_guidance"
    assert results[0]["visibility"] == "private_review"
    assert "Pick Blocking" in str(results[0]["title"])
    assert len(str(results[0]["excerpt"])) <= 500
    assert "full private" not in str(results[0]["excerpt"]).lower()


def test_quality_filtering_excludes_bad_rows_and_demotes_duplicates() -> None:
    rows = fixture_rows() + [
        guidance_row(
            "Bad Short Split",
            "split string 6",
            topics=["split tuning"],
            quality_flags=["body_under_100_words"],
        ),
        guidance_row(
            "No Topic Blocking",
            "Pick blocking right hand steel guitar practice with no topic metadata but plenty of words to search.",
            topics=[],
            quality_flags=["missing_topic_tags"],
        ),
        guidance_row(
            "Duplicate Split A",
            "Split tuning on string 6 is duplicated but still demoted if it appears in retrieval.",
            topics=["split tuning"],
            source_sha256="duplicate-hash",
        ),
        guidance_row(
            "Duplicate Split B",
            "Split tuning on string 6 is duplicated but still demoted if it appears in retrieval.",
            topics=["split tuning"],
            source_sha256="duplicate-hash",
        ),
    ]

    results = search_rows(rows, "How do I tune a split on string 6?", top_k=6)
    titles = [result.title for result in results]

    assert "Bad Short Split" not in titles
    assert "No Topic Blocking" not in titles
    duplicate_results = [result for result in results if result.title.startswith("Duplicate Split")]
    assert duplicate_results
    assert all("possible_duplicate_files_by_hash" in result.quality_flags for result in duplicate_results)
    assert results[0].title == "Split Tuning On String 6"


def test_retrieval_returns_useful_results_for_teaching_queries() -> None:
    cases = {
        "How do I tune a split on string 6?": "Split Tuning On String 6",
        "What is pick blocking?": "Right Hand Pick Blocking",
        "What are B+C pedals used for?": "B+C Pedal Uses",
        "Can I play the lick without a B-to-Bb lever?": "B To Bb Lever Alternatives",
        "How do I play a harmonized scale over a dominant chord?": "Dominant Harmonized Scale",
    }

    for query, expected_title in cases.items():
        results = search_rows(fixture_rows(), query, top_k=3)

        assert results, query
        assert results[0].title == expected_title
        assert results[0].content_layer == "curated_guidance"
        assert results[0].visibility == "private_review"
        assert results[0].score > 0
        assert len(results[0].excerpt) <= 500


def test_non_teaching_queries_do_not_search_curated_guidance() -> None:
    assert search_rows(fixture_rows(), "What is the capital of France?", top_k=3) == []
