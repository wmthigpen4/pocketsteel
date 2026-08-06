from __future__ import annotations

from scripts.run_world_class_answer_challenge import DEFAULT_BANK, load_cases, score_case


def test_world_class_challenge_covers_required_release_routes() -> None:
    cases = load_cases(DEFAULT_BANK)

    assert len(cases) == 11
    assert {case["expected_route"] for case in cases} == {
        "deterministic",
        "source_backed_rag",
        "hybrid",
        "guardrail",
    }
    assert {case["id"] for case in cases} >= {
        "fmaj7-deterministic",
        "cabinet-drop-rag",
        "travis-toy-entity",
        "travis-toy-tutorials-entity",
        "followup-player-context",
        "followup-course-context",
        "obscure-player-entity",
        "gear-source-backed",
        "tab-deterministic",
    }


def test_challenge_score_requires_structured_deterministic_payload() -> None:
    case = next(case for case in load_cases(DEFAULT_BANK) if case["id"] == "fmaj7-deterministic")

    failures = score_case(
        case,
        200,
        {
            "answer": "Fmaj7 is F-A-C-E; strings 2-3-4-5 make a complete F major 7.",
            "sources": [],
        },
    )

    assert failures == ["fretboard payload missing"]


def test_challenge_score_rejects_old_generic_failure() -> None:
    case = next(case for case in load_cases(DEFAULT_BANK) if case["id"] == "travis-toy-entity")

    failures = score_case(
        case,
        200,
        {
            "answer": "I need a more specific steel-guitar question to give a useful answer.",
            "sources": [],
        },
    )

    assert "source cards missing" in failures
    assert any("forbidden term" in failure for failure in failures)
