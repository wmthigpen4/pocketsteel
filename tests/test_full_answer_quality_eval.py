from __future__ import annotations

from pathlib import Path

from scripts.run_full_answer_quality_eval import (
    evaluate_quality_result,
    render_markdown_report,
    result_to_json,
    summarize_results,
)


def row(
    *,
    question: str = "What should I practice tonight?",
    category: str = "practice_plan_questions",
    expected_intent: str = "",
    expected_contract: str = "",
) -> dict[str, str]:
    return {
        "id": "T001",
        "category": category,
        "question": question,
        "expected_intent": expected_intent,
        "expected_contract": expected_contract,
    }


def source_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "title": "Practice source",
        "forumName": "Pedal Steel",
        "url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
        "excerpt": "A useful source excerpt with enough context to support the answer.",
        "score": 0.82,
        "chunkId": "v2:1:answer_advice:0001:abcd",
        "postUid": "p1",
    }
    card.update(overrides)
    return card


def payload(answer: str, *, sources: list[dict[str, object]] | None = None, warnings: list[str] | None = None) -> dict[str, object]:
    return {
        "answer": answer,
        "mode": "ask",
        "sources": sources if sources is not None else [source_card()],
        "warnings": warnings or [],
        "sections": [{"title": "Answer", "style": "lead", "body": answer}],
    }


def finding_keys(result) -> set[str]:
    return {finding.key for finding in result.findings}


def test_quality_eval_flags_internal_language_and_raw_junk() -> None:
    result = evaluate_quality_result(
        row(question="Where can I buy a slide bar?", category="targeted_directness_probes", expected_intent="vendor_buying_guidance"),
        status_code=200,
        payload=payload(
            "The retrieved material says to use the source cards. PayPal order link: email bob@example.test.",
            sources=[source_card(excerpt="Bob / 12 Jan 2020 10:00 AM e-mail me for PayPal order link.")],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "internal_implementation_language" in keys
    assert "raw_contact_order_link_junk" in keys
    assert "source_excerpt_junk" in keys


def test_quality_eval_allows_authorized_private_source_but_flags_unauthorized() -> None:
    private = source_card(
        url="source-inbox/rules/user-e9-copedent-profile.txt",
        forumName="Private Sources",
        source_system="personal_rules_note",
        visibility="private",
        source_id="user-e9-copedent-profile",
        source_path="source-inbox/rules/user-e9-copedent-profile.txt",
        provenance_status="reviewed",
        answer_quote_allowed="limited",
    )
    answer = "For your setup, practice grips 3-4-5, 4-5-6, 5-6-8, and 6-8-10 slowly tonight."
    authorized = evaluate_quality_result(
        row(question="What are my common grips?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(answer, sources=[private]),
        access_role="beta_user",
    )
    unauthorized = evaluate_quality_result(
        row(question="What are my common grips?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(answer, sources=[private]),
        access_role="anonymous",
    )

    assert "unauthorized_private_source" not in finding_keys(authorized)
    assert "unauthorized_private_source" in finding_keys(unauthorized)
    assert unauthorized.outcome == "fail"


def test_quality_eval_flags_non_actionable_practice_answer() -> None:
    result = evaluate_quality_result(
        row(),
        status_code=200,
        payload=payload("Buddy Emmons and Lloyd Green are important steel guitar players."),
    )

    assert result.outcome == "fail"
    assert "practice_not_actionable" in finding_keys(result)


def test_quality_summary_and_report_shape() -> None:
    passing = evaluate_quality_result(
        row(question="What does A+F do?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            "A+F means the A pedal and F lever give you a major-position sound, often used as a smooth movable position. Practice moving into it slowly from open position.",
        ),
    )
    failing = evaluate_quality_result(
        row(question="Where can I buy a slide bar?", category="targeted_directness_probes", expected_intent="vendor_buying_guidance"),
        status_code=200,
        payload=payload("The retrieved material says use the source cards. PayPal order link."),
    )

    summary = summarize_results([passing, failing])
    report = render_markdown_report(
        [passing, failing],
        question_bank=Path("tests/fixtures/user_question_bank.json"),
        base_url="http://127.0.0.1:9999",
        config={"retrieval_mode": "hybrid_private_first"},
    )
    encoded = result_to_json(failing)

    assert summary["total_questions"] == 2
    assert summary["outcome_counts"]["fail"] >= 1
    assert "Top 25 Worst Answers" in report
    assert "Private-Source Behavior" in report
    assert encoded["outcome"] == "fail"
    assert encoded["findings"]
