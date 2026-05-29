from __future__ import annotations

from pocketsteel.answer_contracts import (
    CONTRACTS,
    contract_for_intent,
    infer_contract_intent,
    validate_answer_against_contract,
)


def test_explicit_contract_schemas_cover_core_answer_families() -> None:
    expected = {
        "player_bio",
        "copedent_fretboard",
        "diagnostic_troubleshooting",
        "vendor_buying_guidance",
        "brand_comparison",
        "song_learning",
        "current_roster",
        "sensitive_identity",
        "fallback_unknown",
    }

    assert expected <= set(CONTRACTS)
    assert contract_for_intent("song_learning_or_tab_request").intent == "song_learning"


def test_contract_routing_uses_canonical_intents() -> None:
    assert infer_contract_intent("Who is Buddy Emmons?") == "player_bio"
    assert infer_contract_intent("What does A+F do?") == "copedent_fretboard"
    assert infer_contract_intent("Why does my amp buzz at idle?") == "diagnostic_troubleshooting"
    assert infer_contract_intent("Where can I buy a slide bar?") == "vendor_buying_guidance"
    assert infer_contract_intent("Is Mullen or MSA better?") == "brand_comparison"
    assert infer_contract_intent("Show me how to play a song.") == "song_learning"
    assert infer_contract_intent("Who plays for Shania Twain?") == "current_roster"
    assert infer_contract_intent("Do any gay people play pedal steel?") == "sensitive_identity"


def test_player_bio_contract_requires_direct_identity_and_contribution() -> None:
    good = (
        "Buddy Emmons was an influential pedal steel guitarist known for extraordinary musical command.\n\n"
        "He mattered because his recorded work, style, and technical contribution shaped modern pedal steel playing."
    )
    bad = "Buddy Emmons was mentioned in a forum thread."

    assert validate_answer_against_contract(good, "player_bio").is_valid
    validation = validate_answer_against_contract(bad, "player_bio")
    assert not validation.is_valid
    assert any("why they matter" in violation or "style or contribution" in violation for violation in validation.violations)


def test_copedent_contract_requires_change_result_example_and_use() -> None:
    good = (
        "On E9, A+F means using the A pedal with the F lever to make a major-chord position.\n\n"
        "What changes\n\n"
        "- The A pedal raises B strings to C#.\n"
        "- The F lever raises E strings to F.\n"
        "- Together they give a major triad.\n\n"
        "Practical use\n\n"
        "- Use it at the 6th fret for G major and practice grips 3-4-5 or 5-6-8."
    )
    bad = "A+F is useful."

    assert validate_answer_against_contract(good, "copedent_fretboard").is_valid
    validation = validate_answer_against_contract(bad, "copedent_fretboard")
    assert not validation.is_valid
    assert any("missing" in violation for violation in validation.violations)


def test_diagnostic_contract_requires_sections_and_safety() -> None:
    good = (
        "Start by isolating whether the buzz is in the amp or the rig.\n\n"
        "Likely causes\n\n"
        "- If it appears only with the rig connected, suspect cable, volume pedal, effects, or pickup ground.\n\n"
        "Diagnostic path\n\n"
        "- Test with nothing plugged in, then guitar direct, then add each signal-chain piece one at a time.\n\n"
        "Safety\n\n"
        "- If the amp buzzes with nothing plugged in, use a qualified amp tech for electrical work."
    )
    bad = "Does the amp buzz with nothing connected?"

    assert validate_answer_against_contract(good, "diagnostic_troubleshooting").is_valid
    validation = validate_answer_against_contract(bad, "diagnostic_troubleshooting")
    assert not validation.is_valid
    assert "answer opens as forum question only" in validation.violations
    assert "missing section Likely causes" in validation.violations


def test_vendor_contract_requires_curated_sources_specs_and_availability() -> None:
    good = (
        "Best places to check\n\n"
        "- Steel Guitar Shopper — steel-guitar accessories.\n"
        "- BJS Steel Guitar Bars — dedicated steel bar maker.\n"
        "- Jim Dunlop Tonebars — mainstream tonebar options.\n\n"
        "What to choose\n\n"
        "- Diameter, length, weight, material, and pedal steel versus lap/dobro style.\n\n"
        "Check current availability before assuming anything is in stock."
    )
    bad = "Buy from https://steelguitarforum.com/Forum5/HTML/001234.html because that product has positive owner/source impression."

    assert validate_answer_against_contract(good, "vendor_buying_guidance").is_valid
    validation = validate_answer_against_contract(bad, "vendor_buying_guidance")
    assert not validation.is_valid
    assert any("random old forum vendor link" in violation for violation in validation.violations)
    assert any("generic product-value template" in violation for violation in validation.violations)


def test_brand_comparison_contract_requires_specific_dimensions_without_vendor_links() -> None:
    good = (
        "There is no universal winner between Mullen and MSA; the better guitar depends on the specific instrument and player fit.\n\n"
        "Compare mechanics and changer feel, parts/support, tone and sustain, weight/ergonomics, condition, setup, copedent fit, and budget."
    )
    bad = "Mullen is better. Buy it at https://example.com."

    assert validate_answer_against_contract(good, "brand_comparison").is_valid
    validation = validate_answer_against_contract(bad, "brand_comparison")
    assert not validation.is_valid
    assert any("vendor links in comparison" in violation for violation in validation.violations)
    assert any("missing no universal winner" in violation for violation in validation.violations)


def test_song_current_roster_sensitive_and_fallback_contracts_are_explicit() -> None:
    song = (
        "Tell me the song, key, tuning, and whether you have a chart or short excerpt.\n\n"
        "A safe path is a public-domain tune such as Amazing Grace or an original mini-tab exercise. "
        "I do not provide full note-for-note copyrighted tab or full copyrighted lyrics by default."
    )
    roster = (
        "I do not have a current, reliable source-backed roster for that artist in this corpus. "
        "Check official tour credits, album/session credits, or current band listings."
    )
    sensitive = (
        "I do not have a reliable source-backed roster for that, and it would not be appropriate to speculate about anyone’s sexual orientation. "
        "Pedal steel is played by people from many backgrounds."
    )
    fallback = (
        "I don’t have enough source-backed evidence in this corpus to answer that confidently. "
        "Try adding the song, key, tuning, brand, or exact part you mean so I can narrow the source match."
    )

    assert validate_answer_against_contract(song, "song_learning").is_valid
    assert validate_answer_against_contract(roster, "current_roster").is_valid
    assert validate_answer_against_contract(sensitive, "sensitive_identity").is_valid
    assert validate_answer_against_contract(fallback, "fallback_unknown").is_valid


def test_contract_lint_rejects_orphan_and_internal_implementation_language() -> None:
    bad = (
        "The cleanest source-backed answer is to treat the source cards as supporting evidence, not as a script to copy.\n\n"
        "Practical answer\n\n"
        "Useful distilled points: Top Has anyone compared this?"
    )

    validation = validate_answer_against_contract(bad, "fallback_unknown")
    assert not validation.is_valid
    assert "internal source-backed fallback language" in validation.violations
    assert "orphan Practical answer heading" in validation.violations
