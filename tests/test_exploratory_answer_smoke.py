from __future__ import annotations

from pathlib import Path

from scripts.run_exploratory_answer_smoke import (
    QuestionCase,
    answer_contains_contact_or_unapproved_link_junk,
    built_in_questions,
    evaluate_response,
    render_markdown_report,
    summarize_results,
    write_reports,
)


def source_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "title": "Forum source",
        "forumName": "Steel Guitar Forum",
        "url": "https://bb.steelguitarforum.com/viewtopic.php?t=1",
        "excerpt": "A forum excerpt with enough words to look like a normal source card.",
        "source_system": "sgf_phpbb_current",
    }
    card.update(overrides)
    return card


def fretboard_payload(key: str, frets: tuple[int, int, int]) -> dict[str, object]:
    open_fret, af_fret, ab_fret = frets
    return {
        "type": "e9-fretboard-diagram",
        "title": f"{key} major positions on E9",
        "tuning": "E9",
        "positions": [
            {"id": f"{key}-open", "role": "Open position", "fret": open_fret, "strings": [4, 5, 6]},
            {"id": f"{key}-af", "role": "A+F position", "fret": af_fret, "strings": [4, 5, 6]},
            {"id": f"{key}-ab", "role": "A+B position", "fret": ab_fret, "strings": [4, 5, 6]},
        ],
    }


def grip_order_payload() -> dict[str, object]:
    return {
        "type": "e9-fretboard-diagram",
        "title": "Grip-order test",
        "tuning": "E9",
        "positions": [
            {
                "id": "bad-568",
                "role": "Open position",
                "family": "open_grip",
                "fret": 3,
                "grip": "5-6-8",
                "strings": [5, 6, 8],
                "pedals": [],
                "levers": [],
            },
            {
                "id": "bad-456",
                "role": "Open position",
                "family": "open_grip",
                "fret": 3,
                "grip": "4-5-6",
                "strings": [4, 5, 6],
                "pedals": [],
                "levers": [],
            },
        ],
    }


def minor_function_fretboard_payload() -> dict[str, object]:
    return {
        "type": "e9-fretboard-diagram",
        "title": "E minor on E9",
        "tuning": "E9",
        "positions": [
            {
                "id": "em-reference",
                "role": "E minor reference",
                "fret": 3,
                "grip": "5-6-8",
                "strings": [5, 6, 8],
                "pedals": [],
                "levers": [],
            }
        ],
    }


def payload(
    answer: str,
    *,
    sources: list[dict[str, object]] | None = None,
    fretboard: dict[str, object] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    response: dict[str, object] = {
        "answer": answer,
        "warnings": warnings or [],
        "sources": sources if sources is not None else [],
        "sections": [{"title": "Answer", "body": answer}],
    }
    if fretboard is not None:
        response["fretboard"] = fretboard
    return response


def finding_keys(result) -> set[str]:
    return {finding.key for finding in result.findings}


def test_approved_curated_vendor_links_are_not_contact_junk() -> None:
    assert not answer_contains_contact_or_unapproved_link_junk(
        "Best places to check\n\n- Steel Guitar Shopper — https://steelguitarshopper.com/accessories/ — steel guitar accessories."
    )
    assert answer_contains_contact_or_unapproved_link_junk("Order here: https://private.example.invalid/order-form")
    assert answer_contains_contact_or_unapproved_link_junk("PayPal accepted; email bob@example.test.")


def test_builtin_question_set_has_required_size_and_categories() -> None:
    questions = built_in_questions()
    categories = {case.category for case in questions}
    question_text = {case.question for case in questions}

    assert len(questions) >= 120
    assert {
        "chord_position_fretboard",
        "progressions",
        "grips",
        "personal_setup",
        "practice_technique",
        "gear_vendor_troubleshooting",
        "player_history",
        "guardrail_song_tab",
    } <= categories
    assert {
        "What's a G chord even mean?",
        "What does a C chord mean?",
        "What notes are in a D chord?",
        "Where is a G chord?",
        "How do I play G on E9?",
        "What makes an E minor chord minor?",
        "What is the vi chord in G?",
        "How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.",
        "I broke a string during a show. Has that happened to anyone else? What do people do?",
        "My 3rd string keeps breaking at gigs. What should I carry?",
        "What should be in a pedal steel emergency gig kit?",
        "My amp hums until I touch the changer. What should I check first?",
        "Should delay go before my volume pedal or after it?",
        "What do players say about breaking strings on stage?",
        "Do steel players use battery-powered tuners live?",
        "Where are some places to play C chords?",
        "I am in the key of G. Where can I play a 6m chord?",
        "How do I plan an F chord?",
        "How do I play an F chord?",
        "Where all can I play a G chord?",
        "Where all can I play a B chord?",
        "What does 5-7-8 with E lowered give me at the 3rd fret?",
        "Is 5-7-8 with E lowered a B9 pocket?",
        "Show me V chord pockets in A.",
        "What is my copedent?",
        "Teach me about pockets.",
        "What’s a StroboPlus?",
        "Where can I buy a slide bar?",
        "Why does my amp buzz?",
        "Can you write the solo from Together Again?",
    } <= question_text


def test_bad_b_chord_answer_is_flagged() -> None:
    result = evaluate_response(
        QuestionCase("T001", "chord_position_fretboard", "Where all can I play a B chord?"),
        200,
        payload(
            "RKL fully engaged gives one option, and you can use B7 or B9 chord fragments from the source.",
            sources=[source_card()],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "raw_sgf_fragment_language" in keys
    assert "chord_position_missing_fretboard" in keys
    assert "deterministic_answer_has_sources" in keys
    assert "chord_position_has_sgf_source_cards" in keys
    assert "chord_position_missing_expected_frets" in keys
    assert "chord_position_unrelated_chords_or_keys" in keys


def test_good_b_chord_answer_passes_without_sources() -> None:
    result = evaluate_response(
        QuestionCase("T002", "chord_position_fretboard", "Where all can I play a B chord?"),
        200,
        payload(
            "On standard E9, useful B major positions include the 7th fret with no pedals, "
            "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals. "
            "Try the 4-5-6 grip first.",
            sources=[],
            fretboard=fretboard_payload("B", (7, 10, 14)),
        ),
    )

    assert result.outcome == "pass"
    assert not result.findings


def test_good_b_sharp_answer_passes_with_c_positions() -> None:
    result = evaluate_response(
        QuestionCase("T003", "chord_position_fretboard", "How do I play a B# chord?"),
        200,
        payload(
            "B# is the same pitch as C. On E9, think of it as a C major sound: "
            "8th fret with no pedals, 11th fret with A pedal + F lever, and 15th fret with A+B pedals. "
            "Try strings 4-5-6 first.",
            sources=[],
            fretboard=fretboard_payload("C", (8, 11, 15)),
        ),
    )

    assert result.outcome == "pass"
    assert not result.findings


def test_beginner_chord_concept_fragment_answer_is_flagged() -> None:
    result = evaluate_response(
        QuestionCase("T004", "chord_position_fretboard", "What's a G chord even mean?"),
        200,
        payload(
            "I spell each chord from its tonic, and boy got to remember that 7th fret for the chord from the source.",
            sources=[source_card()],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "chord_position_missing_fretboard" in keys
    assert "deterministic_answer_has_sources" in keys
    assert "chord_position_missing_expected_frets" in keys
    assert "beginner_chord_concept_router_escape" in keys


def test_beginner_major_chord_concept_answer_passes() -> None:
    result = evaluate_response(
        QuestionCase("T005", "chord_position_fretboard", "What notes are in a D chord?"),
        200,
        payload(
            "A D major chord means the root D, the major third F#, and the fifth A. "
            "On E9, useful D major positions include the 10th fret with no pedals, "
            "the 13th fret with A pedal + F lever, and the 17th fret with A+B pedals. "
            "Try the 4-5-6 grip first.",
            sources=[],
            fretboard=fretboard_payload("D", (10, 13, 17)),
        ),
    )

    assert result.outcome == "pass"
    assert not result.findings


def test_beginner_minor_chord_concept_answer_passes() -> None:
    result = evaluate_response(
        QuestionCase("T006", "deterministic_pocket_fretboard", "What makes an E minor chord minor?"),
        200,
        payload(
            "E minor uses the root E, a flat third G, and the fifth B. "
            "On E9, use the fretboard payload as a visual reference and listen for that lowered-third minor color.",
            sources=[],
            fretboard=minor_function_fretboard_payload(),
        ),
    )

    assert result.outcome == "pass"
    assert not result.findings


def test_bad_router_escape_answer_is_flagged() -> None:
    result = evaluate_response(
        QuestionCase("T009", "chord_position_fretboard", "Where are some places to play C chords?"),
        200,
        payload(
            "The retrieved material says to use a G major example and source cards.",
            sources=[source_card()],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "chord_position_missing_fretboard" in keys
    assert "deterministic_answer_has_sources" in keys
    assert "chord_position_missing_expected_frets" in keys
    assert "chord_position_unrelated_chords_or_keys" in keys


def test_good_c_and_f_router_escape_answers_pass_without_sources() -> None:
    c_result = evaluate_response(
        QuestionCase("T010", "chord_position_fretboard", "Where can I play C chord?"),
        200,
        payload(
            "On standard E9, C major is at the 8th fret with no pedals, "
            "the 11th fret with A pedal + F lever, and the 15th fret with A+B pedals.",
            sources=[],
            fretboard=fretboard_payload("C", (8, 11, 15)),
        ),
    )
    f_result = evaluate_response(
        QuestionCase("T011", "chord_position_fretboard", "How do I plan an F chord?"),
        200,
        payload(
            "On standard E9, F major is at the 1st fret with no pedals, "
            "the 4th fret with A pedal + F lever, and the 8th fret with A+B pedals.",
            sources=[],
            fretboard=fretboard_payload("F", (1, 4, 8)),
        ),
    )

    assert c_result.outcome == "pass"
    assert f_result.outcome == "pass"


def test_minor_function_answer_must_resolve_to_e_minor_with_fretboard() -> None:
    bad = evaluate_response(
        QuestionCase("T012", "deterministic_pocket_fretboard", "I am in the key of G. Where can I play a 6m chord?"),
        200,
        payload("Use B7 and RKL fragments from the source cards.", sources=[source_card()]),
    )
    good = evaluate_response(
        QuestionCase("T013", "deterministic_pocket_fretboard", "Show me the vi chord in G."),
        200,
        payload(
            "In G, the vi chord is E minor (Em). Try a focused E minor reference grip and listen for the minor color.",
            sources=[],
            fretboard=minor_function_fretboard_payload(),
        ),
    )

    assert bad.outcome == "fail"
    assert "deterministic_visual_missing_fretboard" in finding_keys(bad)
    assert "deterministic_answer_has_sources" in finding_keys(bad)
    assert "wrong_function_routing" in finding_keys(bad)
    assert good.outcome == "pass"


def test_object_object_wrong_grip_order_and_unexpected_fretboard_are_flagged() -> None:
    object_leak = evaluate_response(
        QuestionCase("T014", "practice_technique", "Teach me about pockets."),
        200,
        payload("Start with [object Object] and practice slowly.", sources=[]),
    )
    bad_grips = evaluate_response(
        QuestionCase("T015", "chord_position_fretboard", "Where can I play a G chord?"),
        200,
        payload(
            "On standard E9, G major is at the 3rd fret with no pedals, "
            "the 6th fret with A pedal + F lever, and the 10th fret with A+B pedals.",
            sources=[],
            fretboard=grip_order_payload(),
        ),
    )
    unexpected = evaluate_response(
        QuestionCase("T016", "gear_vendor_troubleshooting", "What's a StroboPlus?"),
        200,
        payload(
            "A StroboPlus is a tuner. Compare presets and check the display before a gig.",
            sources=[],
            fretboard=fretboard_payload("G", (3, 6, 10)),
        ),
    )

    assert "object_object_rendering_leakage" in finding_keys(object_leak)
    assert "object_object_rendering" in finding_keys(object_leak)
    assert "fretboard_grip_order_wrong" in finding_keys(bad_grips)
    assert "non_position_question_has_fretboard" in finding_keys(unexpected)


def test_practical_advice_background_only_answer_is_flagged() -> None:
    result = evaluate_response(
        QuestionCase(
            "T018",
            "gear_vendor_troubleshooting",
            "How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.",
        ),
        200,
        payload(
            "A StroboPlus is a Peterson strobe-style tuner with sweetened temperaments for pedal steel.",
            sources=[],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "advice_question_must_answer_directly" in keys
    assert "gear_question_background_only_failure" in keys


def test_practical_advice_fragment_joke_answer_is_flagged() -> None:
    result = evaluate_response(
        QuestionCase(
            "T019",
            "gear_vendor_troubleshooting",
            "I broke a string during a show. Has that happened to anyone else? What do people do?",
        ),
        200,
        payload(
            "Has that happened to anyone else? One time at a gig I cut my finger and everybody laughed.",
            sources=[source_card()],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "advice_question_must_answer_directly" in keys
    assert "advice_question_raw_fragment_failure" in keys
    assert "advice_question_joke_anecdote_failure" in keys


def test_clean_practical_advice_answers_pass() -> None:
    tuner = evaluate_response(
        QuestionCase(
            "T020",
            "gear_vendor_troubleshooting",
            "How do people power their StroboPlus tuner when playing a gig? My batteries run out very fast.",
        ),
        200,
        payload(
            "For a gig, power the StroboPlus from a reliable adapter or fully charged supply, and keep fresh batteries as a backup. "
            "Before the gig, check the cable, confirm the tuner stays on for a full set, and carry spare batteries in your seat.",
            sources=[],
        ),
    )
    string = evaluate_response(
        QuestionCase(
            "T021",
            "gear_vendor_troubleshooting",
            "I broke a string during a show. Has that happened to anyone else? What do people do?",
        ),
        200,
        payload(
            "During the show, replace the broken string if there is a pause; otherwise finish the tune by avoiding that grip. "
            "Carry spare 3rd and 5th strings, a winder, cutters, and a small tuner, then check the changer finger after the set.",
            sources=[],
        ),
    )

    assert tuner.outcome == "pass"
    assert string.outcome == "pass"


def test_weak_source_wording_maps_to_requested_bucket() -> None:
    result = evaluate_response(
        QuestionCase("T022", "gear_vendor_troubleshooting", "Should delay go before my volume pedal or after it?"),
        200,
        payload(
            "Source support was weak, so use the source cards.",
            sources=[],
            warnings=["curated answer used; source support was weak"],
        ),
    )

    keys = finding_keys(result)
    assert result.outcome == "fail"
    assert "visible_weak_source_language" in keys
    assert "weak_source_leakage" in keys


def test_personal_setup_answer_requires_copedent_facts() -> None:
    result = evaluate_response(
        QuestionCase("T017", "personal_setup", "What is my copedent?"),
        200,
        payload(
            "Your private setup is available. Practice it slowly.",
            sources=[source_card(visibility="private", source_system="personal_rules_note")],
        ),
    )

    assert result.outcome == "fail"
    assert "missing_copedent_facts" in finding_keys(result)


def test_private_profile_failures_are_flagged() -> None:
    ignored = evaluate_response(
        QuestionCase("T004", "personal_setup", "What does my RKL do?"),
        200,
        payload("RKL can mean different things on different guitars. Check your copedent.", sources=[]),
    )
    leaked = evaluate_response(
        QuestionCase("T005", "practice_technique", "What should I practice tonight?"),
        200,
        payload(
            "Your saved 10-string E9 profile says your RKL lowers string 6, so practice that.",
            sources=[source_card(visibility="private", source_system="personal_rules_note")],
        ),
    )

    assert "private_profile_ignored" in finding_keys(ignored)
    assert ignored.outcome == "fail"
    assert "generic_answer_leaked_private_profile" in finding_keys(leaked)
    assert leaked.outcome == "fail"


def test_generic_my_pedal_steel_wording_is_not_private_profile() -> None:
    result = evaluate_response(
        QuestionCase("T008", "gear_vendor_troubleshooting", "How do I clean my pedal steel?"),
        200,
        payload(
            "Clean your pedal steel gently: wipe strings and metal parts, avoid flooding the changer, "
            "and use only small amounts of appropriate lubricant where the guitar maker recommends it.",
            sources=[],
        ),
    )

    assert "private_profile_ignored" not in finding_keys(result)


def test_report_rendering_and_json_output(tmp_path: Path) -> None:
    passing = evaluate_response(
        QuestionCase("T006", "chord_position_fretboard", "Where can I play a B chord?"),
        200,
        payload(
            "On standard E9, play B major at the 7th fret with no pedals, "
            "the 10th fret with A pedal + F lever, and the 14th fret with A+B pedals.",
            sources=[],
            fretboard=fretboard_payload("B", (7, 10, 14)),
        ),
    )
    failing = evaluate_response(
        QuestionCase("T007", "gear_vendor_troubleshooting", "Where can I buy a slide bar?"),
        200,
        payload("The retrieved material says use the source cards. PayPal order link."),
    )
    results = [passing, failing]
    report = render_markdown_report(results, api_url="http://127.0.0.1:8783/api/answer", config={"top_k": 6})
    summary = summarize_results(results)
    output = tmp_path / "smoke.md"
    json_output = tmp_path / "smoke.json"

    write_reports(results, output=output, json_output=json_output, api_url="http://127.0.0.1:8783/api/answer", config={"top_k": 6})

    assert summary["total_questions"] == 2
    assert summary["outcome_counts"]["pass"] == 1
    assert summary["outcome_counts"]["fail"] == 1
    assert "Top 20 Worst Answers" in report
    assert "Recommended Backend Fixes" in report
    assert output.exists()
    assert json_output.exists()
