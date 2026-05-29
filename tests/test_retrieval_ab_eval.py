from __future__ import annotations

import pytest

from scripts.run_retrieval_ab_eval import RerankConfig, analyze_sources, build_arg_parser, main, rerank_sources


def test_retrieval_ab_eval_help_mentions_safe_v2_gate() -> None:
    help_text = build_arg_parser().format_help()

    assert "--run-v1" in help_text
    assert "--run-v2" in help_text
    assert "--confirm-v2-ready" in help_text
    assert "--dry-run" in help_text
    assert "--candidate-k" in help_text
    assert "--dedupe-thread" in help_text
    assert "--min-excerpt-chars" in help_text


def test_retrieval_ab_eval_dry_run_does_not_open_chroma(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--dry-run",
            "--question-bank",
            "tests/fixtures/user_question_bank.json",
            "--top-k",
            "3",
            "--limit",
            "2",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Retrieval A/B eval dry run" in captured.out
    assert "Questions: 2" in captured.out
    assert "Top K: 3" in captured.out
    assert "Dry run did not open Chroma." in captured.out


def test_retrieval_ab_eval_requires_confirmation_before_v2() -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "--dry-run",
                "--run-v2",
                "--question-bank",
                "tests/fixtures/user_question_bank.json",
            ]
        )


def test_v2_alias_metadata_counts_as_complete() -> None:
    metrics = analyze_sources(
        [
            {
                "source_system": "sgf_phpbb_current",
                "forum_name": "Steel Players",
                "thread_title": "Buddy Emmons",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
                "chunk_id": "v2:1:answer_advice:0001:abc",
                "thread_id": "1",
                "chunk_role": "answer_advice",
                "quality_score": 0.8,
                "noise_score": 0.1,
                "source_metadata_complete": True,
                "post_uids": ["p1"],
                "post_uid": "p1",
                "excerpt": "Buddy Emmons was discussed in a useful biographical source.",
                "score": 0.7,
            }
        ]
    )

    assert metrics["metadata_completeness_rate"] == 1.0
    assert metrics["post_identity_completeness_rate"] == 1.0


def test_v1_metadata_scoring_remains_compatible() -> None:
    metrics = analyze_sources(
        [
            {
                "source_system": "sgf_phpbb_current",
                "forum_name": "Pedal Steel",
                "thread_title": "Blocking practice",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=101",
                "chunk_id": "chunk-1",
                "post_uid": "chunk-1",
                "source_kind": "forum_thread_chunk",
                "forum_id": "5",
                "legacy_forum_number": "",
                "thread_id": "101",
                "legacy_thread_uid": "",
                "thread_category": "technique",
                "chunk_index": 1,
                "excerpt": "Palm blocking and pick blocking both show up in older forum advice.",
                "score": 0.8,
            }
        ]
    )

    assert metrics["metadata_completeness_rate"] < 1.0
    assert metrics["metadata_completeness_rate"] > 0.8


def test_short_mention_fragment_can_be_downranked() -> None:
    sources = [
        {
            "score": 0.7,
            "excerpt": "likes Buddy Emmons.",
            "thread_url": "https://example.test/mention",
            "chunk_role": "answer_advice",
        },
        {
            "score": 0.62,
            "excerpt": "Buddy Emmons was described as an influential player, builder, and musical reference point in this thread.",
            "thread_url": "https://example.test/bio",
            "chunk_role": "answer_advice",
        },
    ]

    ranked = rerank_sources(
        sources,
        limit=2,
        config=RerankConfig(candidate_k=2, min_excerpt_chars=80, mention_only_penalty=0.2),
    )

    assert ranked[0]["thread_url"] == "https://example.test/bio"
    assert "mention_only" in ranked[1]["rerank_flags"]


def test_per_thread_dedupe_prefers_unique_threads() -> None:
    sources = [
        {"score": 0.9, "excerpt": "First useful source.", "thread_url": "https://example.test/thread-a"},
        {"score": 0.8, "excerpt": "Second source from same thread.", "thread_url": "https://example.test/thread-a"},
        {"score": 0.7, "excerpt": "Different thread source.", "thread_url": "https://example.test/thread-b"},
    ]

    ranked = rerank_sources(sources, limit=2, config=RerankConfig(candidate_k=3, dedupe_thread=True))

    assert [source["thread_url"] for source in ranked] == [
        "https://example.test/thread-a",
        "https://example.test/thread-b",
    ]


def test_high_quality_answer_advice_outranks_question_only_fragment() -> None:
    sources = [
        {
            "score": 0.72,
            "excerpt": "What should I practice?",
            "thread_url": "https://example.test/question",
            "chunk_role": "question",
            "quality_score": 0.4,
            "noise_score": 0.2,
        },
        {
            "score": 0.68,
            "excerpt": "Practice bar control slowly, then add pedals and levers once the movement is clean.",
            "thread_url": "https://example.test/advice",
            "chunk_role": "answer_advice",
            "quality_score": 0.8,
            "noise_score": 0.1,
        },
    ]

    ranked = rerank_sources(
        sources,
        limit=2,
        config=RerankConfig(
            candidate_k=2,
            question_only_penalty=0.12,
            answer_advice_boost=0.04,
            quality_boost=0.04,
            quality_threshold=0.7,
        ),
    )

    assert ranked[0]["thread_url"] == "https://example.test/advice"
