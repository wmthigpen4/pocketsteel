from __future__ import annotations

from scripts.run_fixture_qna_campaign import campaign_questions, run_campaign


def test_fixture_campaign_is_frozen_at_752_prompts() -> None:
    rows = campaign_questions()
    assert len(rows) == 752
    assert len({row["id"] for row in rows}) == 752


def test_fixture_campaign_uses_no_network_and_keeps_terra_luna_paired() -> None:
    result = run_campaign()
    assert result["passed"] is True
    assert result["questions"] == 752
    assert result["status_counts"] == {200: 752}
    assert result["network_openai_requests"] == 0
    assert result["fixture_terra_calls"] == result["fixture_luna_calls"]
