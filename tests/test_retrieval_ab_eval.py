from __future__ import annotations

import pytest

from scripts.run_retrieval_ab_eval import build_arg_parser, main


def test_retrieval_ab_eval_help_mentions_safe_v2_gate() -> None:
    help_text = build_arg_parser().format_help()

    assert "--run-v1" in help_text
    assert "--run-v2" in help_text
    assert "--confirm-v2-ready" in help_text
    assert "--dry-run" in help_text


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
