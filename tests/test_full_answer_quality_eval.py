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


def fretboard_payload(key: str, frets: tuple[int, int, int]) -> dict[str, object]:
    open_fret, af_fret, ab_fret = frets
    slug = key.lower().replace("#", "sharp")
    positions: list[dict[str, object]] = [
        {
            "id": f"{slug}-open-{open_fret}",
            "label": f"{key} major",
            "fret": open_fret,
            "strings": [4, 5, 6],
            "grip": "4-5-6",
            "pedals": [],
            "levers": [],
            "role": "Open position",
            "family": "major_triad",
            "tier": "beginner",
            "colorRole": "primary",
            "visibleByDefault": True,
            "sortOrder": 10,
        },
        {
            "id": f"{slug}-af-{af_fret}",
            "label": f"{key} major",
            "fret": af_fret,
            "strings": [4, 5, 6],
            "grip": "4-5-6",
            "pedals": ["A"],
            "levers": ["F"],
            "role": "A+F position",
            "family": "major_triad",
            "tier": "beginner",
            "colorRole": "secondary",
            "visibleByDefault": True,
            "sortOrder": 20,
        },
        {
            "id": f"{slug}-ab-{ab_fret}",
            "label": f"{key} major",
            "fret": ab_fret,
            "strings": [4, 5, 6],
            "grip": "4-5-6",
            "pedals": ["A", "B"],
            "levers": [],
            "role": "A+B position",
            "family": "major_triad",
            "tier": "beginner",
            "colorRole": "alternate",
            "visibleByDefault": True,
            "sortOrder": 30,
        },
    ]
    if key == "B":
        positions.append(
            {
                "id": "b-ab-2-lower-octave",
                "label": "B major",
                "fret": 2,
                "strings": [4, 5, 6],
                "grip": "4-5-6",
                "pedals": ["A", "B"],
                "levers": [],
                "role": "A+B lower-octave alternate",
                "family": "major_triad",
                "tier": "alternate",
                "colorRole": "alternate",
                "visibleByDefault": False,
                "sortOrder": 40,
            }
        )
    return {
        "type": "e9-fretboard-diagram",
        "title": f"{key} major positions on E9",
        "tuning": "E9",
        "key": key,
        "strings": {"count": 10},
        "positions": positions,
    }


def starter_only_fretboard_payload(key: str, frets: tuple[int, int, int]) -> dict[str, object]:
    payload = fretboard_payload(key, frets)
    payload["positions"] = payload["positions"][:3]
    return payload


def payload(
    answer: str,
    *,
    sources: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
    fretboard: dict[str, object] | None = None,
) -> dict[str, object]:
    response: dict[str, object] = {
        "answer": answer,
        "mode": "ask",
        "sources": sources if sources is not None else [source_card()],
        "warnings": warnings or [],
        "sections": [{"title": "Answer", "style": "lead", "body": answer}],
    }
    if fretboard is not None:
        response["fretboard"] = fretboard
    return response


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


def test_quality_eval_flags_wrong_key_chord_position_leakage() -> None:
    result = evaluate_quality_result(
        row(question="Where can I play an A chord?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            (
                "For A, the source examples mention B7 at the 5th fret. "
                "A+F is a generic major-position idea, and a G major example sits at the 6th fret with A pedal and F lever."
            )
        ),
    )

    assert result.outcome == "fail"
    assert "wrong_key_chord_position_leakage" in finding_keys(result)
    assert "missing_fretboard_payload_for_chord_position" in finding_keys(result)


def test_quality_eval_flags_enharmonic_chord_position_failure() -> None:
    result = evaluate_quality_result(
        row(question="How do I play a B# chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "If you can lower the B's to Bb, use that with the G#>F# lower to get a II7 chord. "
                "Then play it with your middle finger as the horns descend."
            )
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "enharmonic_chord_position_failure" in keys
    assert "source_fragment_chord_answer_failure" in keys
    assert "missing_deterministic_chord_route" in keys


def test_quality_eval_flags_source_fragments_for_suffixless_chord_position_question() -> None:
    result = evaluate_quality_result(
        row(question="How do I play a C#?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "You either tune it and play it, or you don't. I've played it this way so long I can't imagine it any other way. "
                "Like your example, starting with the first string to the fifth string: C#,G#,F#,E,B."
            )
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "source_fragment_chord_answer_failure" in keys
    assert "missing_deterministic_chord_route" in keys


def test_quality_eval_flags_plan_typo_chord_position_fallback_fragments() -> None:
    result = evaluate_quality_result(
        row(question="How do I plan an F chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "Other chords based on an A root might also work with an F chord. "
                "F#7 > B7 > E7 > A7 comes from a Mel Bay chord chart."
            )
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "chord_position_typo_fallback_failure" in keys
    assert "missing_deterministic_chord_route" in keys


def test_quality_eval_flags_source_fragments_for_b_chord_position_question() -> None:
    result = evaluate_quality_result(
        row(question="Where all can I play a B chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "RKL fully engaged and B pedal pressed can help. "
                "You might use B7 in key of C, or a B9 chord if the tune needs it."
            )
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "source_fragment_chord_answer_failure" in keys
    assert "wrong_key_chord_position_leakage" in keys


def test_quality_eval_flags_sgf_sources_for_deterministic_chord_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="Where can I play a B chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful B major positions include the 7th fret with no pedals, "
                "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals. "
                "Try strings 4-5-6 first."
            ),
            sources=[source_card(forumName="Steel Guitar Forum", url="https://bb.steelguitarforum.com/viewtopic.php?t=999")],
            fretboard=fretboard_payload("B", (7, 10, 14)),
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "unrelated_sgf_sources_for_deterministic_answer" in keys
    assert "deterministic_chord_source_leakage" in keys


def test_quality_eval_flags_missing_fretboard_for_clean_chord_position_text() -> None:
    result = evaluate_quality_result(
        row(question="Where all can I play a B chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful B major positions include the 7th fret with no pedals, "
                "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals. "
                "Try strings 4-5-6 first."
            ),
            sources=[],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "missing_fretboard_payload_for_chord_position" in keys


def test_quality_eval_flags_weak_source_language_for_chord_position_question() -> None:
    result = evaluate_quality_result(
        row(question="What frets give me B?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            "Source support was weak, so use the source cards.",
            sources=[],
            warnings=["curated answer used; source support was weak"],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "missing_deterministic_chord_route" in keys
    assert "deterministic_chord_weak_warning" in keys


def test_quality_eval_flags_chord_position_typo_fallback_failure() -> None:
    result = evaluate_quality_result(
        row(question="How do I plan an F chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "Source support was weak, but a forum fragment says to plan around whatever F chord sounds right. "
                "Use the source cards for the rest."
            ),
            sources=[source_card()],
            warnings=["curated answer used; source support was weak"],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "chord_position_typo_fallback_failure" in keys
    assert "missing_fretboard_payload_for_chord_position" in keys
    assert "missing_deterministic_chord_route" in keys
    assert "deterministic_chord_weak_warning" in keys
    assert "deterministic_chord_source_leakage" in keys


def test_quality_eval_passes_clean_f_chord_typo_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="How do I plan an F chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful F major positions include the 1st fret with no pedals, "
                "the 4th fret with A pedal + F lever, and the 8th fret with A+B pedals. "
                "Use grips 4-5-6, 3-4-5, or 6-8-10 and move between the positions slowly."
            ),
            sources=[],
            fretboard=fretboard_payload("F", (1, 4, 8)),
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "pass"
    assert "chord_position_typo_fallback_failure" not in keys
    assert "missing_fretboard_payload_for_chord_position" not in keys
    assert "missing_deterministic_chord_route" not in keys


def test_quality_eval_flags_starter_only_b_payload_and_missing_alternate() -> None:
    result = evaluate_quality_result(
        row(question="Where all can I play a B chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful B major positions include the 7th fret with no pedals, "
                "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals."
            ),
            sources=[],
            fretboard=starter_only_fretboard_payload("B", (7, 10, 14)),
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "starter_only_fretboard_catalog" in keys
    assert "missing_alternate_position" in keys


def test_quality_eval_flags_missing_position_filter_metadata() -> None:
    result = evaluate_quality_result(
        row(question="Show me advanced B chord positions.", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful B major positions include the 7th fret with no pedals, "
                "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals."
            ),
            sources=[],
            fretboard={
                "type": "e9-fretboard-diagram",
                "title": "B major positions on E9",
                "tuning": "E9",
                "strings": {"count": 10},
                "positions": [
                    {
                        "id": "b-open-7",
                        "label": "B major",
                        "fret": 7,
                        "strings": [4, 5, 6],
                        "grip": "4-5-6",
                        "pedals": [],
                        "levers": [],
                        "role": "Open position",
                    },
                    {
                        "id": "b-af-10",
                        "label": "B major",
                        "fret": 10,
                        "strings": [4, 5, 6],
                        "grip": "4-5-6",
                        "pedals": ["A"],
                        "levers": ["F"],
                        "role": "A+F position",
                    },
                    {
                        "id": "b-ab-14",
                        "label": "B major",
                        "fret": 14,
                        "strings": [4, 5, 6],
                        "grip": "4-5-6",
                        "pedals": ["A", "B"],
                        "levers": [],
                        "role": "A+B position",
                    },
                    {
                        "id": "b-ab-2-lower-octave",
                        "label": "B major",
                        "fret": 2,
                        "strings": [4, 5, 6],
                        "grip": "4-5-6",
                        "pedals": ["A", "B"],
                        "levers": [],
                        "role": "A+B lower-octave alternate",
                    },
                ],
            },
        ),
    )

    assert result.outcome == "fail"
    assert "missing_fretboard_filters" in finding_keys(result)


def test_quality_eval_flags_object_object_rendering_failure() -> None:
    result = evaluate_quality_result(
        row(question="Where can I play a B chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful B major positions include the 7th fret with no pedals, "
                "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals. [object Object]"
            ),
            sources=[],
            fretboard=fretboard_payload("B", (7, 10, 14)),
        ),
    )

    assert result.outcome == "fail"
    assert "object_object_rendering_failure" in finding_keys(result)


def test_quality_eval_flags_b9_pocket_misclassification_without_rootless_disclosure() -> None:
    result = evaluate_quality_result(
        row(question="Is 5-7-8 with E lowered a B9 pocket?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            "Yes, 5-7-8 with E lowered is a B9 pocket at the 3rd fret. Use it as your B9 grip.",
            sources=[],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "e_lower_578_b9_misclassification" in keys
    assert "missing_rootless_partial_disclosure" in keys


def test_quality_eval_passes_clear_5_7_8_b9_negative_with_rootless_disclosure() -> None:
    result = evaluate_quality_result(
        row(question="Is 5-7-8 with E lowered a B9 pocket?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            (
                "No: at the 3rd fret with E lowered, strings 5-7-8 resolve to D major, not a B9 pocket. "
                "Use it as a pitch-checked D major grip; against a B root, those notes can also sound like "
                "a rootless B minor 7 color because the B root is omitted."
            ),
            sources=[
                source_card(
                    title="Pitch-rule source",
                    forumName="Rules",
                    url="https://example.test/pitch-rules/e-lower-578",
                    excerpt="Pitch rules classify 5-7-8 with E lowered at fret 3 as D major, with optional rootless B minor 7 color.",
                )
            ],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "pass"
    assert "e_lower_578_b9_misclassification" not in keys
    assert "missing_rootless_partial_disclosure" not in keys


def test_quality_eval_flags_unrequested_dominant_in_a_chord_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="Where can I play an A major chord?", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            "A major is at the 5th fret open, 8th fret with A+F, and 12th fret with A+B. You can also use B7 at the 5th fret."
        ),
    )

    assert result.outcome == "fail"
    assert "wrong_key_chord_position_leakage" in finding_keys(result)


def test_quality_eval_passes_clean_a_major_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="Show me places to play an A major chord.", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, play A major at the 5th fret with no pedals, "
                "the 8th fret with A pedal + F lever, and the 12th fret with A+B pedals. "
                "Use grips 4-5-6, 3-4-5, or 6-8-10 and move between the positions slowly."
            ),
            sources=[],
            fretboard=fretboard_payload("A", (5, 8, 12)),
        ),
    )

    assert result.outcome == "pass"
    assert "wrong_key_chord_position_leakage" not in finding_keys(result)


def test_quality_eval_passes_clean_b_sharp_as_c_major_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="How do I play a B# chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "B# is the same pitch as C. On E9, think of it as a C major chord. "
                "Useful C major positions include the 8th fret with no pedals, the 11th fret with A pedal + F lever, "
                "and the 15th fret with A+B pedals. Common grips to try include 4-5-6, 3-4-5, and 6-8-10."
            ),
            sources=[],
            fretboard=fretboard_payload("C", (8, 11, 15)),
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "pass"
    assert "enharmonic_chord_position_failure" not in keys
    assert "source_fragment_chord_answer_failure" not in keys
    assert "wrong_key_chord_position_leakage" not in keys


def test_quality_eval_passes_clean_c_sharp_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="How do I play a C#?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful C# major positions include the 9th fret with no pedals, "
                "the 12th fret with A pedal + F lever, and the 16th fret with A+B pedals. "
                "Common grips to try include 4-5-6, 3-4-5, and 6-8-10."
            ),
            sources=[],
            fretboard=fretboard_payload("C#", (9, 12, 16)),
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "pass"
    assert "source_fragment_chord_answer_failure" not in keys
    assert "wrong_key_chord_position_leakage" not in keys


def test_quality_eval_passes_clean_b_position_answer() -> None:
    result = evaluate_quality_result(
        row(question="Where all can I play a B chord?", category="e9_fretboard_copedent", expected_contract="copedent_fretboard"),
        status_code=200,
        payload=payload(
            (
                "On standard E9, useful B major positions include the 7th fret with no pedals, "
                "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals. "
                "Common grips to try include 4-5-6, 3-4-5, and 6-8-10."
            ),
            sources=[],
            fretboard=fretboard_payload("B", (7, 10, 14)),
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "pass"
    assert "source_fragment_chord_answer_failure" not in keys
    assert "wrong_key_chord_position_leakage" not in keys


def test_quality_eval_allows_dominants_for_i_iv_v_context() -> None:
    result = evaluate_quality_result(
        row(question="Show me a 1-4-5 in G.", category="e9_fretboard_copedent"),
        status_code=200,
        payload=payload(
            (
                "In a 1-4-5 in G, use G as I, C as IV, and D or D7 as the V chord. "
                "Practice the move slowly, then connect the positions with clean bar movement."
            )
        ),
    )

    assert "wrong_key_chord_position_leakage" not in finding_keys(result)


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
