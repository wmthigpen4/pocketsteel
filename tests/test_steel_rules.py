from __future__ import annotations

from steel_guitar_rag.steel_rules import (
    COMMON_E9_GRIPS,
    STANDARD_E9_OPEN_STRINGS,
    STANDARD_EMMONS_CHANGES,
    answer_from_rules,
    explain_common_grips,
    explain_e9_change,
    explain_number_chord,
    explain_tab_symbol,
    explain_triad,
)


def test_standard_e9_open_strings_and_emmons_changes_are_declared() -> None:
    assert STANDARD_E9_OPEN_STRINGS == {
        1: "F#",
        2: "D#",
        3: "G#",
        4: "E",
        5: "B",
        6: "G#",
        7: "F#",
        8: "E",
        9: "D",
        10: "B",
    }
    assert STANDARD_EMMONS_CHANGES["a"] == ("raises 5 and 10 B to C#",)
    assert STANDARD_EMMONS_CHANGES["b"] == ("raises 3 and 6 G# to A",)
    assert STANDARD_EMMONS_CHANGES["c"] == ("raises 4 E to F#", "raises 5 B to C#")
    assert STANDARD_EMMONS_CHANGES["f lever"] == ("raises 4 and 8 E to F",)
    assert STANDARD_EMMONS_CHANGES["e-lower"] == ("lowers 4 and 8 E to D#",)
    assert STANDARD_EMMONS_CHANGES["2nd string lower"] == ("commonly lowers 2 D# to D/C#",)
    assert STANDARD_EMMONS_CHANGES["9th lower"] == ("commonly lowers 9 D to C#",)


def test_explain_triad_and_common_grips() -> None:
    answer = explain_triad()

    assert "root, a third, and a fifth" in answer
    assert "Major triad: 1, 3, 5" in answer
    assert "Minor triad: 1, b3, 5" in answer
    for grip in COMMON_E9_GRIPS:
        assert grip in answer
    assert explain_common_grips() == "Common E9 grips include 3-4-5, 4-5-6, 5-6-8, 6-8-10."


def test_explain_number_chord_two_minor_in_g() -> None:
    answer = explain_number_chord("2m", "G")

    assert answer is not None
    assert "2m chord is A minor (Am)" in answer
    assert "A-C-E" in answer
    assert "1-b3-5 built on scale degree 2" in answer
    assert "3rd fret with B+C pedals" in answer
    assert "8th fret" in answer
    assert "A pedal" in answer
    assert "strings 5-6-8" in answer
    assert "D7, the 5-dominant chord in G" in answer


def test_explain_e9_change_a_f() -> None:
    answer = explain_e9_change("A+F")

    assert answer is not None
    assert "A pedal with the F lever" in answer
    assert "three frets above the open major position" in answer
    assert "A pedal raises the B strings to C#" in answer
    assert "F lever raises the E strings to F" in answer
    assert "G major is available at the 6th fret" in answer


def test_explain_tab_symbol_5_to_7() -> None:
    answer = explain_tab_symbol("5^7")

    assert answer is not None
    assert "ambiguous" in answer
    assert "5 dominant 7" in answer
    assert "V7" in answer
    assert "slide from fret 5 to fret 7" in answer
    assert "surrounding tab or chord line" in answer


def test_answer_from_rules_for_smoke_questions() -> None:
    cases = {
        "What is a triad?": ("root, a third, and a fifth", "3-4-5"),
        "What does A+F do?": ("A pedal with the F lever", "major triad"),
        "What gauge is 10th string on E9?": ("10th string is B", ".036 wound"),
        "What is 2m in G?": ("2m chord is A minor (Am)", "B+C pedals", "A pedal"),
        "What is a 5^7?": ("5 dominant 7", "slide from fret 5 to fret 7"),
    }

    for question, required in cases.items():
        answer = answer_from_rules(question)
        assert answer is not None
        assert answer.intent == "copedent_fretboard"
        for text in required:
            assert text in answer.answer
