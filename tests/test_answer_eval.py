from __future__ import annotations

import json
from pathlib import Path

from scripts.run_answer_eval import (
    evaluate_answer,
    load_question_bank,
    render_report,
    result_from_payload,
)


def failure_reasons(question: str, answer: str, *, source_count: int = 1) -> set[str]:
    return {failure.reason for failure in evaluate_answer(question, answer, [], source_count, 200)}


def test_question_bank_has_large_representative_set() -> None:
    questions = load_question_bank(Path("tests/fixtures/user_question_bank.json"))

    assert len(questions) >= 150
    categories = {row["category"] for row in questions}
    assert "entity_player_biography" in categories
    assert "prompt_injection_hostile_retrieved_text" in categories
    assert any(row["question"] == "What are common Fender Steel King settings?" for row in questions)


def test_eval_flags_known_formatting_failures() -> None:
    reasons = failure_reasons(
        "What are common Fender Steel King settings?",
        "Concise answer: Bill Lowe / 16 Nov 2007 1:32 pm asked about settings. [1]\n\nSource context: raw forum text.",
    )

    assert "banned phrase: Concise answer:" in reasons
    assert "inline citation marker" in reasons
    assert "username/date boilerplate" in reasons
    assert "date-like boilerplate" in reasons
    assert "banned phrase: Source context:" in reasons


def test_eval_allows_clean_source_backed_heading() -> None:
    reasons = failure_reasons(
        "What are common Fender Steel King settings?",
        "Try a neutral amp setting first.\n\nUseful source-backed points:\n- Several sources mention backing off treble and adjusting mids by ear.",
    )

    assert "banned phrase: What multiple sources support" not in reasons
    assert "banned phrase: Source context:" not in reasons


def test_eval_flags_routing_and_category_specific_failures() -> None:
    assert "ranking caveat on non-ranking question" in failure_reasons(
        "Who is Lloyd Green?",
        "Rankings are subjective, but Lloyd Green is in the top 5.",
    )
    assert "practice question returned player rankings" in failure_reasons(
        "What should I practice tonight?",
        "Buddy Emmons, Lloyd Green, and Paul Franklin are top players.",
    )
    assert "finger-pick question listed steel players" in failure_reasons(
        "What are the best finger picks?",
        "Buddy Emmons and Paul Franklin are often mentioned.",
    )


def test_eval_flags_retrieval_and_safety_checks() -> None:
    assert "TSGA answer missing Texas Steel Guitar Association" in failure_reasons("What is TSGA?", "TSGA is a show.")
    assert "6th-fret G chord answer missing A pedal + F lever" in failure_reasons(
        "How do I play a G chord on the 6th fret?",
        "Use strings 3, 4, and 5.",
    )
    assert "naphtha/lighter fluid recommended as oil" in failure_reasons(
        "What kind of oil is good for my changer?",
        "Use lighter fluid as oil on the changer.",
    )
    assert "Axtremity/Pedal Slide used as proof Telonics made a slide bar" in failure_reasons(
        "Did Telonics ever make a slide bar?",
        "The Telonics Axtremity Pedal Slide proves it.",
    )


def test_result_capture_and_report_grouping() -> None:
    result = result_from_payload(
        {"id": "Q001", "category": "gear_effects_tone", "question": "What are common Fender Steel King settings?"},
        200,
        {
            "answer": "Practical answer\nSource context: raw forum text.",
            "warnings": ["weak retrieval"],
            "sources": [
                {
                    "title": "Steel King Settings",
                    "forumName": "Electronics",
                    "url": "https://example.test/thread",
                }
            ],
        },
    )

    assert result.source_count == 1
    assert result.first_source_title == "Steel King Settings"
    assert result.first_source_forum == "Electronics"
    assert result.group == "likely formatting failure"

    report = render_report([result], base_url="http://127.0.0.1:8770", question_bank=Path("bank.json"))
    assert "Worst 25 Failures" in report
    assert "likely formatting failure" in report
    assert "Steel King Settings" in report


def test_json_shape_for_fixture_is_valid() -> None:
    data = json.loads(Path("tests/fixtures/user_question_bank.json").read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert isinstance(data["questions"], list)
