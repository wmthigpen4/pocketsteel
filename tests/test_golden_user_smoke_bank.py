from __future__ import annotations

import json

from scripts.run_golden_user_smoke_bank import (
    EXPECTED_GATES,
    DEFAULT_BANK,
    load_bank,
    mutate_prompt,
    score_payload,
    score_responses,
)


def test_golden_user_smoke_bank_loads_expected_prompt_range_and_categories() -> None:
    bank, prompts = load_bank(DEFAULT_BANK)

    categories = {prompt.category for prompt in prompts}
    assert 250 <= len(prompts) <= 300
    assert len(categories) == 20
    assert set(bank["global_rules"]["report_gates"]) >= EXPECTED_GATES
    assert all(prompt.allow_sgf_answer_body is False for prompt in prompts)


def test_golden_user_smoke_bank_rows_have_required_expectation_shape() -> None:
    _, prompts = load_bank(DEFAULT_BANK)

    for prompt in prompts:
        assert prompt.id.startswith("gus-")
        assert prompt.prompt
        assert prompt.expected_intent
        assert prompt.severity_if_fail in {"P1", "P2", "P3"}
        assert isinstance(prompt.direct_answer_required, bool)
        assert isinstance(prompt.requires_fretboard, bool)
        assert isinstance(prompt.allow_source_cards, bool)
        assert "deterministic map" in prompt.forbidden_terms
        assert "payload" in prompt.forbidden_terms


def test_mutation_generator_expands_natural_language_variants() -> None:
    variants = mutate_prompt("How do I play a C# chord?")

    assert "How do I play a C# chord?" in variants
    assert "how do i play a c# chord?" in variants
    assert "Where can I find a C# chord?" in variants
    assert any("please" in variant for variant in variants)
    assert any("sharp" in variant for variant in variants)


def test_gate_scoring_flags_sgf_primary_answer_leakage() -> None:
    _, prompts = load_bank(DEFAULT_BANK)
    prompt = next(item for item in prompts if item.prompt == "Show me the major scale in G")

    findings = score_payload(
        prompt,
        {
            "answer": "- I know when I first started, someone on the forum said to treat it as a clue rather than consensus.",
            "sources": [],
        },
    )

    gates = {finding.gate for finding in findings}
    assert "SGF leakage" in gates
    assert "intent recognition" in gates


def test_gate_scoring_flags_source_card_and_missing_fretboard_for_deterministic_prompt() -> None:
    _, prompts = load_bank(DEFAULT_BANK)
    prompt = next(item for item in prompts if item.prompt == "Where can I play a G chord on E9?")

    findings = score_payload(
        prompt,
        {
            "answer": "Play G on the 3rd fret, 6th fret with A+F, and 10th fret with A+B on strings 4, 5, and 6.",
            "sources": [{"title": "Forum source"}],
        },
    )

    gates = {finding.gate for finding in findings}
    assert "fretboard expected/present" in gates
    assert "source-card appropriateness" in gates


def test_gate_scoring_flags_internal_wording_and_directness() -> None:
    _, prompts = load_bank(DEFAULT_BANK)
    prompt = next(item for item in prompts if item.prompt == "What is a sus chord?")

    findings = score_payload(prompt, {"answer": "The retrieved material says the deterministic map payload explains sus chords."})

    gates = {finding.gate for finding in findings}
    assert "direct answer first" in gates
    assert "internal wording leakage" in gates
    assert "SGF leakage" in gates


def test_gate_scoring_accepts_clean_supported_response() -> None:
    _, prompts = load_bank(DEFAULT_BANK)
    prompt = next(item for item in prompts if item.prompt == "Where can I play a G chord on E9?")

    findings = score_payload(
        prompt,
        {
            "answer": "Play G at fret 3 open, fret 6 with A+F, and fret 10 with A+B on strings 4, 5, and 6.",
            "sources": [],
            "fretboard": {"positions": [{"fret": 3}, {"fret": 6}, {"fret": 10}]},
        },
    )

    assert findings == []


def test_response_file_gate_summary_shape(tmp_path) -> None:
    _, prompts = load_bank(DEFAULT_BANK)
    prompt = next(item for item in prompts if item.prompt == "What is the capital of France?")
    report = score_responses(
        [prompt],
        {
            prompt.id: {
                "answer": "The retrieved material says Paris. It includes source cards from a steel forum.",
                "sources": [{"title": "SGF"}],
            }
        },
    )

    output = tmp_path / "report.json"
    output.write_text(json.dumps(report), encoding="utf-8")
    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["total_scored"] == 1
    assert loaded["fail_count"] == 1
    assert "off-domain guardrail" in loaded["gate_counts"]
    assert "source-card appropriateness" in loaded["gate_counts"]
