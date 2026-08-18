"""Small curated answer layer for high-confidence steel-guitar questions."""

from __future__ import annotations

import re
from typing import Any

from steel_guitar_rag.answer_intent_classifier import (
    mentions_chord_melody_harmony,
    mentions_position_strategy,
)
from steel_guitar_rag.music_text import normalize_spelled_accidentals
from steel_guitar_rag.basic_chord_answers import (
    basic_chord_theory_answer_for_question,
    chord_change_answer_for_question,
    major_seventh_position_answer,
    sus_chord_usage_answer_for_question,
)
from steel_guitar_rag.curated_source_registry import slide_bar_vendor_bullets
from steel_guitar_rag.curated_contracts import (
    CURATED_FACT_WEAK_WARNING as CURATED_FACT_WEAK_WARNING,
    MAJOR_CHORD_SPELLINGS,
    PLAYER_BIOS,
    WEAK_RETRIEVAL_WARNING as WEAK_RETRIEVAL_WARNING,
    CuratedAnswer,
    CuratedConfidence as CuratedConfidence,
    IntentMode,
)
from steel_guitar_rag.curated_song_references import (
    steel_guitar_rag_answer_for_question,
    steel_guitar_rag_source_cards,
)
from steel_guitar_rag.fretboard_examples import (
    chord_concept_answer_for_question,
    chord_symbol_guardrail_answer_for_question,
    display_major_key_for_request,
    e_lower_578_b9_answer_for_question,
    e_lower_578_answer_for_question,
    e_lower_grip_answer_for_question,
    e_lower_grip_usage_answer_for_question,
    fret_string_pedal_answer_for_question,
    function_chord_answer_for_question,
    functional_pocket_answer_for_question,
    get_e9_major_chord_positions,
    generic_chord_concept_answer_for_question,
    mixed_a_minor_bflat_major_answer_for_question,
    major_chord_location_request_for_question,
    minor_chord_answer_for_question,
    multi_chord_answer_for_question,
    rootless_chord_quality_answer_for_question,
    specific_major_grip_answer_for_question,
    chord_quality_definition_lines,
    unsupported_chord_location_request_for_question,
)
from steel_guitar_rag.steel_rules import answer_from_rules


SOURCE_PROVENANCE_FOLLOWUP_RE = re.compile(
    r"(?:\bsource\s+of\s+(?:the\s+)?information\b|"
    r"\b(?:what|which|where)\b.{0,45}\b(?:sources?|citations?|references?|evidence)\b|"
    r"\bhow\s+do\s+you\s+know\b|"
    r"\bwhere\s+did\b.{0,45}\b(?:come\s+from|learn)\b)",
    re.I,
)

SOURCE_BACKED_PROVENANCE_INTENTS = frozenset({
    "curated_fact_source_check",
    "factual_biography",
    "forum_wisdom",
    "lesson_lookup",
    "product_value",
    "unknown_low_confidence",
    "vendor_buying_guidance",
})


def is_source_provenance_followup(question: str) -> bool:
    """Return whether a turn asks where the preceding answer came from."""

    return SOURCE_PROVENANCE_FOLLOWUP_RE.search(question or "") is not None


def source_provenance_followup_answer(
    question: str,
    conversation_context: tuple[str, ...],
) -> CuratedAnswer | None:
    """Explain deterministic provenance when the preceding answer is reproducible.

    A provenance question should not be treated as a new off-domain query.  For
    deterministic position-strategy answers, the honest source is the rules
    layer and its E9 pitch calculation rather than a forum quotation.
    """

    if not conversation_context or not is_source_provenance_followup(question):
        return None
    prior_question = ""
    for item in reversed(conversation_context):
        normalized = " ".join(str(item or "").split())
        if normalized.casefold().startswith("user:"):
            prior_question = normalized.split(":", 1)[1].strip()
            break
    if not prior_question:
        return None
    if not mentions_position_strategy(prior_question):
        prior_answer = visual_fretboard_curated_answer(prior_question)
        if prior_answer is None:
            prior_answer = intent_mode_curated_answer(prior_question)
        if (
            prior_answer is None
            or prior_answer.source_cards
            or prior_answer.intent in SOURCE_BACKED_PROVENANCE_INTENTS
        ):
            return None
        return CuratedAnswer(
            intent=prior_answer.intent,
            confidence="curated_high",
            answer=(
                "That preceding answer came from Steel Guitar RAG’s deterministic and curated "
                "rules layer, not from a Steel Guitar Forum quotation or a language-model guess.\n\n"
                "For an E9 position or chord question, the service parses the requested chord, "
                "fret, strings, pedals, and levers; applies the selected copedent’s pitch changes; "
                "then validates the resulting notes and answer contract. For a local teaching or "
                "clarifier response, it selects reviewed guidance keyed to the detected request "
                "type. The preceding answer had no retrieved source card, so it should be read as "
                "a locally computed or curated answer rather than an SGF citation."
            ),
        )
    return CuratedAnswer(
        intent="position_strategy",
        confidence="curated_high",
        answer=(
            "That answer came from Steel Guitar RAG’s deterministic E9 rules layer, not from a single "
            "Steel Guitar Forum post or a retrieved quotation.\n\n"
            "The mechanical part is calculated from standard E9 tuning and pedal changes. On strings "
            "4-5-6 at the 3rd fret, the open notes form G-D-B, a G-major inversion. Pressing A+B while "
            "staying at the 3rd fret changes that grip to G-E-C, a C-major inversion. Moving the bar to "
            "the 8th fret with no pedals gives C-G-E, another C-major inversion. That pitch calculation "
            "is the source for the concrete 3rd-fret and 8th-fret example.\n\n"
            "The broader recommendation—choose between staying on one fret and moving to another "
            "position according to the chord, melody or top note, voicing, register, tone, and next "
            "phrase—is curated pedal-steel teaching and arranging guidance. Pedals, knee levers, and "
            "grips make several choices mechanically valid; the musical context determines which one "
            "is preferable. No forum source was used to produce the original deterministic answer."
        ),
    )




def visual_fretboard_curated_answer(question: str) -> CuratedAnswer | None:
    q = normalize(question)
    song_tab_guardrail = full_song_tab_guardrail_answer(q)
    if song_tab_guardrail is not None:
        return song_tab_guardrail
    quarantine_teacher_answer = sgf_quarantine_teacher_answer(q)
    if quarantine_teacher_answer is not None:
        return quarantine_teacher_answer
    practical_direct_answer = direct_yes_no_practical_answer(q)
    if practical_direct_answer is not None:
        return practical_direct_answer
    lyrics_answer = full_lyrics_guardrail_answer(q)
    if lyrics_answer is not None:
        return lyrics_answer
    if mentions_g_five_eight_harmonized_scale(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "Here are the validated G harmonized-scale 5&8 branch options on E9.\n\n"
                "- Branch 4 minor/blue-color route: fret 6 with A pedal + E-raise/F lever on strings 5 and 8; the notes are G and B.\n"
                "- Branch 4 major-color route: fret 8 with E-lower on strings 5 and 8; the notes are G and B.\n"
                "- Branch 7 minor/blue-color route: fret 11 with A pedal + E-raise/F lever on strings 5 and 8; the notes are C and E.\n"
                "- Branch 7 major-color route: fret 13 with E-lower on strings 5 and 8; the notes are C and E.\n\n"
                "The 13th-fret E-lower branch is the corrected C/E route; the older 11th-fret E-lower wording was a typo. "
                "This is static fretboard information, so it uses a fretboard diagram rather than tab."
            ),
        )
    g_harmonized_answer = g_harmonized_scale_curated_answer(q)
    if g_harmonized_answer is not None:
        return g_harmonized_answer
    if mentions_harmonized_scale_workout(q):
        return CuratedAnswer(
            intent="practice_plan",
            confidence="curated_high",
            answer=(
                "Here is a practical E9 harmonized-scale workout in G.\n\n"
                "10-minute drill:\n"
                "- 2 minutes: play G at the 3rd fret open/no pedals on grip 4-5-6, then C at the same fret with A+B, then D at the 5th fret with A+B.\n"
                "- 3 minutes: move a simple two-note harmony up the scale on strings 4 and 5, saying the scale degree out loud.\n"
                "- 3 minutes: repeat the idea on grip 3-4-5, blocking after every grip.\n"
                "- 2 minutes: make a two-measure phrase, leave a beat of space, then answer it lower on the neck.\n\n"
                "Goal: hear the scale as chord movement, not as memorized forum licks."
            ),
        )
    if mentions_this_diminished_missing_context(q):
        return CuratedAnswer(
            intent="missing_context_clarifier",
            confidence="curated_high",
            answer=(
                "I can tell you whether it is diminished, but I need the actual notes or the E9 location first.\n\n"
                "Send one of these:\n"
                "- the notes in the grip\n"
                "- the fret, strings, pedals, and levers\n"
                "- a short tab line\n\n"
                "A diminished triad needs root, b3, and b5. A diminished-7th sound adds bb7."
            ),
        )
    if mentions_vague_next_step_question(q):
        return CuratedAnswer(
            intent="missing_context_clarifier",
            confidence="curated_high",
            answer=(
                "Tell me what musical situation you mean, and I can give you a useful next step.\n\n"
                "The missing context is: key, chord, fret, strings, and whether you are using pedals or levers. For example: “I’m at G on fret 3 with no pedals; where should I go next?”"
            ),
        )
    sus_usage_answer = sus_chord_usage_answer_for_question(question)
    if sus_usage_answer is not None:
        return CuratedAnswer(
            intent="when_to_use_musical_context",
            confidence="curated_high",
            answer=sus_usage_answer,
        )
    rootless_quality_answer = rootless_chord_quality_answer_for_question(question)
    if rootless_quality_answer is not None:
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=rootless_quality_answer,
        )
    basic_theory_answer = basic_chord_theory_answer_for_question(question)
    if basic_theory_answer is not None:
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=basic_theory_answer,
        )
    chord_change_answer = chord_change_answer_for_question(question)
    if chord_change_answer is not None:
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=chord_change_answer,
        )
    unknown_identity_answer = unknown_identity_guardrail_answer(q)
    if unknown_identity_answer is not None:
        return unknown_identity_answer
    symbol_guardrail_answer = chord_symbol_guardrail_answer_for_question(question)
    if symbol_guardrail_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=symbol_guardrail_answer,
        )
    b9_answer = e_lower_578_b9_answer_for_question(question)
    if b9_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=b9_answer,
        )
    e_lower_answer = e_lower_578_answer_for_question(question)
    if e_lower_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=e_lower_answer,
        )
    e_lower_grip_answer = e_lower_grip_answer_for_question(question)
    if e_lower_grip_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=e_lower_grip_answer,
        )
    e_lower_usage_answer = e_lower_grip_usage_answer_for_question(question)
    if e_lower_usage_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=e_lower_usage_answer,
        )
    if mentions_e_lower_minor_sound_position(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "Your E-lower position gives a minor sound when the lowered E strings help complete a pitch-validated minor grip.\n\n"
                "A useful reference on your 10-string E9 is the G# minor family with E-lower: the lowered E strings become D#/Eb, which can supply the 5th of G# minor while other strings supply G# and B.\n\n"
                "Start by checking the visible E-lower minor positions in the diagram, then listen for the lowered-third minor color rather than treating every E-lower grip as automatically minor."
            ),
        )
    if mentions_e_minor_pocket_position(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On E9, treat an E minor pocket as E-G-B and use only pitch-validated grips that actually contain those chord tones.\n\n"
                "Useful starter references:\n"
                "- A-pedal minor families can give E minor in the right fret/grip combination.\n"
                "- E-lower and B+C families can also create validated minor colors, depending on fret and grip.\n\n"
                "Use the diagram as the map, then practice one grip slowly and say the notes out loud: E, G, and B."
            ),
        )
    if mentions_ab_d_major_position(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "For D major with A+B on standard E9, start at the 17th fret for the main A+B D major position.\n\n"
                "A lower-octave A+B D position is also available at the 5th fret when the pitch engine validates the grip.\n\n"
                "Try common grips in this order: 3-4-5, 4-5-6, 5-6-8, and 6-8-10. Treat these as D major position families, not forum-tab fragments."
            ),
        )
    if mentions_g_af_position(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "G major with A+F is at the 6th fret on standard E9.\n\n"
                "Use the A pedal plus the F lever there to get the G major A+F family. Start with grip 4-5-6, then compare 3-4-5, 5-6-8, and 6-8-10 in the diagram.\n\n"
                "Use it when you want a smoother connected G color than jumping straight between the open 3rd-fret G and the A+B 10th-fret G."
            ),
        )
    multi_chord_answer = multi_chord_answer_for_question(question)
    if multi_chord_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=multi_chord_answer,
        )
    functional_pocket_answer = functional_pocket_answer_for_question(question)
    if functional_pocket_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=functional_pocket_answer,
        )
    if mentions_g_i_iv_v_visual_question(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On standard E9, a compact 1-4-5 in G is:\n\n"
                "- G: 3rd fret, no pedals.\n"
                "- C: 3rd fret with A+B pedals.\n"
                "- D: 5th fret with A+B pedals.\n\n"
                "Use this as a simple map before adding more positions or passing chords."
            ),
        )
    if _mentions_after_ab_in_g(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "If you are at the A+B G position, treat it as one G home base and move to nearby E9 families instead of grabbing random licks.\n\n"
                "In G:\n"
                "- G: 10th fret with A+B.\n"
                "- G: 6th fret with A pedal + F lever for a smoother connected color.\n"
                "- G: 3rd fret open/no pedals for the straight-bar reference.\n"
                "- C: 3rd fret with A+B for the IV chord.\n"
                "- D: 5th fret with A+B for the V chord.\n\n"
                "Practice tip: play one short A+B phrase, move to one nearby family, then leave space before answering it."
            ),
        )
    if q in {"show me the fretboard", "show the fretboard", "show me an e9 fretboard", "show me the e9 fretboard"}:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "Here’s a starter standard E9 fretboard view using G major as the reference chord.\n\n"
                "Start with these common G positions:\n"
                "- 3rd fret, no pedals: open-position G major.\n"
                "- 6th fret with A pedal + F lever: A+F G major position.\n"
                "- 10th fret with A+B pedals: A+B G major position.\n\n"
                "Use the selector to compare grips and position families. If you want a different map, ask for a chord or key, such as “show me D chord positions on E9.”"
            ),
        )
    if mentions_user_vertical_lever_lower(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On your saved 10-string E9 setup, the vertical lever (LKV) lowers strings 5 and 10 from B to Bb/A#.\n\n"
                "That change is useful for half-step movement from the B strings, especially when you want a suspended, passing, or altered-color sound without moving the bar."
            ),
        )
    if mentions_user_c_pedal_strings_4_5(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On your saved 10-string E9 setup, the C pedal changes strings 4 and 5 this way:\n\n"
                "- String 4: E raises to F#.\n"
                "- String 5: B raises to C#.\n\n"
                "Use it for B+C pedal movement, melodic harmonies, and raised-position minor/major colors where those two notes need to move together."
            ),
        )
    if mentions_ab_tenth_fret_grips(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "A+B at the 10th fret is a strong G major position on E9.\n\n"
                "Useful grips to try, in order:\n"
                "- 3-4-5\n"
                "- 4-5-6\n"
                "- 5-6-8\n"
                "- 6-8-10\n\n"
                "Start with 4-5-6 for the cleanest reference, then compare the brighter 3-4-5 grip and the lower 6-8-10 color."
            ),
        )
    if mentions_iv_from_open_g(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "The IV chord from open G is C.\n\n"
                "On E9, two useful C positions from a G open-position idea are:\n"
                "- 3rd fret with A+B: C at the same fret as the 3rd-fret open G home position.\n"
                "- 8th fret, no pedals: straight-bar C.\n\n"
                "Use the same-fret A+B move first if you want a compact I-to-IV sound; use the 8th-fret open position if you want a clearer bar move up the neck."
            ),
        )
    function_chord_answer = function_chord_answer_for_question(question)
    if function_chord_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=function_chord_answer,
        )
    chord_concept_answer = chord_concept_answer_for_question(question)
    if chord_concept_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=chord_concept_answer,
        )
    generic_chord_concept_answer = generic_chord_concept_answer_for_question(question)
    if generic_chord_concept_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=generic_chord_concept_answer,
        )
    minor_chord_answer = minor_chord_answer_for_question(question)
    if minor_chord_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=minor_chord_answer,
        )
    specific_major_grip_answer = specific_major_grip_answer_for_question(question)
    if specific_major_grip_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=specific_major_grip_answer,
        )
    major_request = major_chord_location_request_for_question(question)
    if major_request is not None:
        major_key = major_request.normalized_key
        display_key = display_major_key_for_request(major_request)
        positions = get_e9_major_chord_positions(major_key)
        open_position = next(position for position in positions if position["role"] == "Open position")
        af_position = next(position for position in positions if position["role"] == "A+F position")
        ab_position = next(position for position in positions if position["role"] == "A+B position")
        wants_across_fretboard = "across" in q and ("fretboard" in q or "guitar" in q or "neck" in q)
        wants_ab_specific = re.search(r"\b(?:a\s*\+\s*b|a\s+and\s+b)\b", q) is not None
        wants_string_grouping = re.search(r"\bstring\s+group(?:ing)?s?\b|\bgrips?\b", q) is not None
        lower_ab_position = next(
            (
                position
                for position in positions
                if position["role"] == "A+B lower-octave alternate" and position.get("grip") == "4-5-6"
            ),
            None,
        )
        e_lower_position = next(
            (
                position
                for position in positions
                if position.get("family") == "e_lower_578" and position.get("grip") == "5-7-8"
            ),
            None,
        )
        lines: list[str] = []
        if major_request.requested_root == "D#":
            lines.extend(
                [
                    "D# is usually easier to think of as Eb on E9. Eb major is Eb-G-Bb.",
                    "",
                ]
            )
        elif major_request.requested_root != display_key:
            lines.extend(
                [
                    f"{major_request.requested_root} is the same pitch as {display_key}. On E9, think of it as a {display_key} major chord.",
                    "",
                ]
            )
        else:
            spelling = MAJOR_CHORD_SPELLINGS.get(display_key)
            if spelling is not None:
                lines.extend(
                    [
                        f"{display_key} major is {spelling}: root, major 3rd, and perfect 5th.",
                        "",
                    ]
                )
        if wants_ab_specific:
            lines.extend(
                [
                    f"With A+B, {display_key} major is at the {fret_label(ab_position['fret'])} on standard E9.",
                    "",
                ]
            )
        lines.extend(
            [
                f"On standard E9, several useful {display_key} major starter positions are:",
                "",
                f"- {fret_label(open_position['fret'])}, no pedals: open-position {display_key} major.",
                f"- {fret_label(af_position['fret'])} with A pedal + F lever: A+F {display_key} major position.",
                f"- {fret_label(ab_position['fret'])} with A+B pedals: A+B {display_key} major position.",
                "",
                "Why these families matter:",
                "- Open/no-pedals grips are the easiest straight-bar reference for intonation and quick fills.",
                "- A+F gives a smooth pedal/lever color that is useful for connected movement.",
                "- A+B is the strong pedals-down home position and octave/register alternate.",
                "- E-lower grips are more context-dependent; the selector may show pitch-validated 5-7-8, 7-8-10, 4-5-7, and 1-4-5 positions when they truly spell the chord. Plain no-pedals 5-7-8 is usually a partial/color grip when it omits the 3rd.",
                "",
                "Common full-triad grips to try first are 3-4-5, 4-5-6, 5-6-8, and 6-8-10. Treat 5-7-8 as an advanced partial/color or E-lower pocket unless the pitch-checked card says it is a full chord.",
                "",
                "Terminology note: the A+F position is the A-pedal + F-lever position.",
            ]
        )
        if wants_string_grouping:
            lines.extend(
                [
                    "",
                    f"For {display_key} major string groupings, start with 3-4-5, 4-5-6, 5-6-8, and 6-8-10. The fretboard view uses pitch validation before it shows each grip.",
                ]
            )
        if wants_across_fretboard and (lower_ab_position is not None or e_lower_position is not None):
            lines.extend(
                [
                    "",
                    f"Starter map: {fret_label(open_position['fret'])}: open/no pedals; {fret_label(af_position['fret'])}: A pedal + F lever (A-pedal + F-lever); {fret_label(ab_position['fret'])}: A+B pedals.",
                    "",
                    "Useful across-the-fretboard alternates:",
                ]
            )
            if lower_ab_position is not None:
                lines.append(
                    f"- {fret_label(lower_ab_position['fret'])} with A+B pedals: lower-octave A+B {display_key} major alternate on grip {lower_ab_position['grip']}."
                )
            if e_lower_position is not None:
                lines.append(
                    f"- {fret_label(e_lower_position['fret'])} with E-lower: pitch-validated {display_key} major color on grip {e_lower_position['grip']}."
                )
        if major_request.requested_root != display_key:
            lines.extend(
                [
                    "",
                    f"Most players would call this {display_key}, not {major_request.requested_root}, unless you are reading notation where that spelling is required by the key.",
                ]
            )
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer="\n".join(lines),
        )
    if mentions_g_common_grips_visual_question(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "For G at the 3rd fret open position on standard E9, common grips include 3-4-5, 4-5-6, 5-6-8, and 6-8-10. "
                "The fretboard view may also show 5-7-8 when a pedal/lever combination validates it by pitch."
            ),
        )
    return None


SGF_QUARANTINE_PATTERNS: tuple[str, ...] = (
    r"\A\s*-\s+",
    r"(?m)^\s*-\s*(?:I've|I'm|We|My|Our|One\s+time|I\s+(?:play|use|had|never|rarely|usually|found|only\s+found|can't|messed|am\s+looking))\b",
    r"\bwrote:\s*:",
    r"<font\b",
    r"<pre\b",
    r"\b(?:Bill Lowe|Thanks Nick|Top Hi All|Does anyone know|Has anyone compared)\b",
    r"\b(?:I found this|I only found|The retrieved excerpts|Related source detail|One related point)\b",
    r"\b(?:I can't offer any help|I've messed with the tuning|For new players out there|If I may|as far as I'm concerned|somebody said|forum thread|source cards?)\b",
    r"\b(?:I|I've|I'm|we|my)\b.{0,80}\b(?:thread|played it|found this|messed with|can't offer|as far as I'm concerned)\b",
    r"\bi know when i first started\b",
    r"\bcan someone please tell me\b",
    r"\blolol thank god\b",
    r"\byou desire more information\b",
    r"\bhave a couple of students\b",
    r"\bbeyond simply facilitating\b",
    r"\bfurther he went on to state\b",
    r"\byou can also build a 7 string instrument\b",
    r"\bit seems that playing steel guitar has a lot in common\b",
    r"\bi found this in limited source support\b",
    r"\btreat it as a clue rather than consensus\b",
)


def sgf_answer_body_needs_quarantine(answer: str) -> bool:
    return any(re.search(pattern, answer or "", re.I) for pattern in SGF_QUARANTINE_PATTERNS)


def generic_sgf_quarantine_fallback_answer(question: str) -> CuratedAnswer:
    return CuratedAnswer(
        intent="unknown_low_confidence",
        confidence="curated_medium",
        answer=(
            "I need a more specific steel-guitar question to give a useful answer.\n\n"
            "Try asking about an E9 position, pedal or lever, grip, chord, tone problem, repair symptom, practice plan, song approach, or player context."
        ),
    )


FOUNDATION_CONCEPT_ANSWERS: dict[str, str] = {
    "steel guitar": (
        "A steel guitar is a guitar played with a smooth steel bar instead of pressing the strings down with your fingers. "
        "The bar slides across the strings, which gives the instrument its smooth gliding sound. "
        "Lap steel has no pedals; pedal steel adds pedals and knee levers that change string pitches while you play."
    ),
    "pedal steel": (
        "A pedal steel is a steel guitar with floor pedals and knee levers that change selected string pitches while the notes are ringing. "
        "You still play it with a steel bar, but the pedals and levers let one chord move into another without moving the bar as much."
    ),
    "lap steel": (
        "A lap steel is a steel guitar played with a bar, usually without pedals or knee levers. "
        "You change notes mostly with bar movement, slants, tuning choices, and picking technique rather than mechanical pitch changes."
    ),
    "console steel": (
        "A console steel is a non-pedal steel guitar built on legs or a stand instead of held on the lap. "
        "It often has one or more necks and tunings, but it does not use the pedal-and-knee-lever mechanism of a pedal steel."
    ),
    "e9": (
        "E9 is the most common pedal-steel tuning for country-style playing. "
        "E is the tuning center, and 9 refers to the dominant-ninth flavor built into the tuning. "
        "On standard 10-string E9, pedals and knee levers let the player move between major, minor, dominant, and passing sounds."
    ),
    "e9 tuning": (
        "E9 is the most common pedal-steel tuning for country-style playing. "
        "E is the tuning center, and 9 refers to the dominant-ninth flavor built into the tuning. "
        "On standard 10-string E9, pedals and knee levers let the player move between major, minor, dominant, and passing sounds."
    ),
    "c6": (
        "C6 is a steel-guitar tuning built around a C6 chord: C-E-G-A. "
        "It is associated with western swing, jazzier chord voicings, richer chord melody, and many double-neck pedal steels. "
        "Compared with E9, C6 is often used more for swing and extended harmony."
    ),
    "c6 tuning": (
        "C6 is a steel-guitar tuning built around a C6 chord: C-E-G-A. "
        "It is associated with western swing, jazzier chord voicings, richer chord melody, and many double-neck pedal steels. "
        "Compared with E9, C6 is often used more for swing and extended harmony."
    ),
    "universal tuning": (
        "A universal tuning is a pedal-steel setup meant to combine E9-style and C6-style jobs on one neck, often on a 12-string guitar. "
        "The idea is to cover country E9 sounds and richer C6-style harmony without carrying a double-neck guitar."
    ),
    "extended e9": (
        "Extended E9 keeps the E9 idea but adds lower strings, usually on a 12-string neck. "
        "Those extra strings extend the bass range while keeping the familiar E9 pedal-and-lever language."
    ),
    "copedent": (
        "A copedent is the chart of a pedal steel’s tuning and mechanical changes. "
        "It shows each open string note and what every pedal and knee lever raises or lowers."
    ),
    "changer": (
        "The changer is the bridge-end mechanism that raises and lowers string pitch on a pedal steel. "
        "Pedals and knee levers pull parts of the changer so a string can move to a new note and then return to pitch."
    ),
    "pedal": (
        "A pedal is a floor control that changes selected string pitches on a pedal steel. "
        "For example, on standard E9 the A pedal raises the B strings to C#, and the B pedal raises G# strings to A."
    ),
    "knee lever": (
        "A knee lever is a lever moved by your knee that raises or lowers selected strings. "
        "On E9, common knee levers raise or lower the E strings and add important chord and scale movement."
    ),
    "volume pedal": (
        "A volume pedal controls loudness with your foot while you play. "
        "Steel players use it for sustain, phrasing, and smooth swells, not as a substitute for picking cleanly."
    ),
    "steel bar": (
        "A steel bar is the smooth metal bar used instead of fretting the strings with your fingers. "
        "Its pressure, angle, and movement shape intonation, sustain, vibrato, and the gliding steel-guitar sound."
    ),
    "picks": (
        "Picks are worn on the picking hand to get a clear attack from the strings. "
        "Most E9 players use a thumb pick and two fingerpicks, though some use more depending on their grip style."
    ),
    "grips": (
        "Grips are string groups you pick together, such as 3-4-5, 4-5-6, 5-6-8, or 6-8-10 on E9. "
        "A grip is useful because the chosen strings often spell a chord or a partial chord at a given fret and pedal setup."
    ),
    "pockets": (
        "A pocket is a small area of the neck where related notes, chords, and pedal moves live close together. "
        "Thinking in pockets helps you connect musical ideas instead of jumping to random fret numbers."
    ),
    "slants": (
        "A slant is when the bar is angled so different strings touch different frets. "
        "Slants are especially important on non-pedal steel and can create harmony or passing movement without pedals."
    ),
    "a pedal": (
        "On standard E9, the A pedal raises the B strings, usually strings 5 and 10, to C#. "
        "It is central to major-chord movement, minor sounds, and the familiar A+B pedals-down position."
    ),
    "b pedal": (
        "On standard E9, the B pedal raises the G# strings, usually strings 3 and 6, to A. "
        "Together with the A pedal, it creates the classic pedals-down major position."
    ),
    "c pedal": (
        "On standard E9, the C pedal usually raises string 4 E to F# and string 5 B to C#. "
        "It is useful for minor-position sounds, passing movement, and connected E9 melody work."
    ),
    "e-lower lever": (
        "The E-lower lever lowers the E strings, usually strings 4 and 8, to D#/Eb. "
        "That change is one of the main ways E9 players get minor colors, dominant movement, and connected chord transitions."
    ),
    "f lever": (
        "The F lever raises the E strings, usually strings 4 and 8, to F. "
        "With the A pedal, it creates a major-chord position three frets above the open no-pedals position."
    ),
    "split": (
        "A split is a tuned note created when a raise and a lower work together on the same string. "
        "Players use splits to get an in-between pitch accurately instead of relying on a rough mechanical compromise."
    ),
    "raise/lower": (
        "Raise and lower describe what a pedal or lever does to a string: a raise moves the pitch up, and a lower moves it down. "
        "A copedent lists those changes so you know what each control does."
    ),
    "cabinet drop": (
        "Cabinet drop is a small pitch change caused by the guitar flexing slightly when pedals are pressed. "
        "Good setup, stable strings, and careful tuning habits help keep it manageable."
    ),
    "scale": (
        "A scale is an ordered set of notes used for melody and harmony. "
        "On E9, scales are usually learned through positions, grips, pedals, levers, and how they connect to nearby chords."
    ),
    "chord": (
        "A chord is a group of notes heard together, usually built from a root, 3rd, and 5th. "
        "On pedal steel, the same chord can often be found at several frets with different pedal and lever combinations."
    ),
    "tuning": (
        "A tuning is the set of open-string notes on the guitar. "
        "On pedal steel, the tuning works together with the copedent, because pedals and levers change those open notes while you play."
    ),
}

FOUNDATION_COMPARISON_ANSWERS: dict[tuple[str, str], str] = {
    ("lap steel", "pedal steel"): (
        "Lap steel and pedal steel are both played with a steel bar, but pedal steel adds floor pedals and knee levers that change string pitches while you play. "
        "Lap steel relies more on bar movement, slants, and tuning choices; pedal steel adds mechanical chord movement and the classic country E9 sound."
    ),
    ("e9", "c6"): (
        "E9 and C6 are two different steel-guitar tuning worlds. "
        "E9 is the common country pedal-steel tuning, strong for vocal-like melody, bends, and major/minor/dominant movement. "
        "C6 is built around C-E-G-A and is associated more with western swing, jazzier harmony, and chord melody."
    ),
    ("dobro", "steel guitar"): (
        "Dobro is related to steel guitar, but it is not the same as pedal steel. "
        "A dobro is a resonator guitar played with a bar, usually acoustically and without pedals. "
        "Steel guitar is the broader family; pedal steel is the version with pedals and knee levers."
    ),
    ("pedal steel", "regular guitar"): (
        "Pedal steel is different from regular guitar because you use a steel bar instead of fretting with your fingers, and pedals and knee levers change string pitches while notes sustain. "
        "Regular guitar is usually fretted by hand; pedal steel is built around sliding intonation, grips, pedals, levers, and a volume pedal."
    ),
}

FOUNDATION_ALIASES: dict[str, str] = {
    "steel": "steel guitar",
    "steel guitar": "steel guitar",
    "a steel guitar": "steel guitar",
    "pedal steel guitar": "pedal steel",
    "a pedal steel": "pedal steel",
    "pedal steel": "pedal steel",
    "dobro": "dobro",
    "regular guitar": "regular guitar",
    "lap steel guitar": "lap steel",
    "lap steel": "lap steel",
    "console steel guitar": "console steel",
    "console steel": "console steel",
    "e9": "e9",
    "e9 tuning": "e9 tuning",
    "c6": "c6",
    "c6 tuning": "c6 tuning",
    "universal": "universal tuning",
    "universal tuning": "universal tuning",
    "extended e9": "extended e9",
    "copedent": "copedent",
    "changer": "changer",
    "a pedal": "a pedal",
    "the a pedal": "a pedal",
    "p1": "a pedal",
    "b pedal": "b pedal",
    "the b pedal": "b pedal",
    "p2": "b pedal",
    "c pedal": "c pedal",
    "the c pedal": "c pedal",
    "p3": "c pedal",
    "pedal": "pedal",
    "pedals": "pedal",
    "knee lever": "knee lever",
    "knee levers": "knee lever",
    "lever": "knee lever",
    "volume pedal": "volume pedal",
    "steel bar": "steel bar",
    "bar": "steel bar",
    "tone bar": "steel bar",
    "picks": "picks",
    "finger picks": "picks",
    "fingerpicks": "picks",
    "grip": "grips",
    "grips": "grips",
    "pocket": "pockets",
    "pockets": "pockets",
    "slant": "slants",
    "slants": "slants",
    "e lower lever": "e-lower lever",
    "e-lower lever": "e-lower lever",
    "e lower": "e-lower lever",
    "e-lower": "e-lower lever",
    "e lever": "e-lower lever",
    "f lever": "f lever",
    "split": "split",
    "splits": "split",
    "raise": "raise/lower",
    "lower": "raise/lower",
    "raise lower": "raise/lower",
    "raise/lower": "raise/lower",
    "cabinet drop": "cabinet drop",
    "scale": "scale",
    "scales": "scale",
    "chord": "chord",
    "chords": "chord",
    "tuning": "tuning",
    "tunings": "tuning",
}


NAMED_STEEL_VOCABULARY_ANSWERS: dict[str, str] = {
    "franklin pedal": (
        "A Franklin pedal is an extra E9 pedal commonly associated with Paul Franklin. "
        "The common Franklin change lowers strings 5 and 10 from B to A, and lowers string 6 from G# to F#.\n\n"
        "What it does musically: it gives you strong downward chord motion and low-string movement without moving the bar. "
        "Players use it for darker passing sounds, bigger bass movement, and chord colors that are hard to get from the standard A, B, and C pedals alone.\n\n"
        "Copedents vary, so check the actual guitar before assuming those exact strings and pitches."
    ),
    "franklin change": (
        "The Franklin change usually means the E9 change that lowers strings 5 and 10 from B to A, and string 6 from G# to F#. "
        "It is commonly put on an extra pedal, often called the Franklin pedal.\n\n"
        "The musical point is downward motion: it lets a chord or bass voice fall while the bar stays put. "
        "That makes it useful for passing chords, minor or dominant color, and connected low-register movement.\n\n"
        "Copedents vary, so treat this as the common version, not a guarantee for every guitar."
    ),
    "zero pedal": (
        "A zero pedal is an extra pedal placed to the left of the normal A pedal, often called P0. "
        "It is not one universal pitch change. Some players use it for a Franklin-style change, some use it for other low-string or setup-specific changes.\n\n"
        "The practical meaning is location: it gives the player one more foot pedal before the standard A-B-C pedal group. "
        "To know what it does musically, read that guitar's copedent."
    ),
    "half stop": (
        "A half stop is a tactile stop partway through a pedal or knee-lever travel. "
        "It lets one control produce an intermediate note before continuing to a second note.\n\n"
        "A common E9 example is the 2nd string lower: D# can stop at D, then continue to C#. "
        "The exact string, pitch, and feel depend on the guitar's copedent and setup."
    ),
    "split tuning": (
        "Split tuning is the setup work that makes a combined raise-and-lower note tune accurately. "
        "For example, one control may raise a string and another may lower it; when both are engaged, the split note needs its own tuning point.\n\n"
        "Musically, splits give you usable in-between notes instead of rough compromises. "
        "The exact split depends on the string, raise, lower, and guitar mechanics."
    ),
    "compensator": (
        "A compensator is an extra pull or adjustment that corrects a pitch problem in a specific pedal or lever combination. "
        "It is not usually a musical pedal by itself; it helps keep a note in tune when the rest of the guitar mechanics affect it.\n\n"
        "Players use compensators for problems like cabinet drop, combination tuning, or a string that needs a small correction only in one pedal/lever state."
    ),
    "vertical lever": (
        "A vertical lever is a knee lever you move upward with your knee. "
        "On many E9 copedents it lowers the B strings, usually strings 5 and 10, to Bb/A#, but that is not universal.\n\n"
        "Musically, a B-to-Bb vertical can give useful dominant, minor, and passing colors. "
        "Check the active copedent before assuming what any vertical lever changes."
    ),
    "f lever": (
        "The F lever is common shorthand for the E-raise lever on E9. "
        "It raises the E strings, usually strings 4 and 8, to F.\n\n"
        "The main use is the A+F major position: with the A pedal engaged, the E-raise lever gives a major-chord position three frets above the no-pedals position. "
        "Lever names vary, so the mechanical name is E-raise."
    ),
    "e lever": (
        "The E lever shorthand varies by player, so resolve it through the active copedent. "
        "In the current user shorthand, the E lever means the E-lower lever: it lowers the E strings, usually strings 4 and 8, to Eb/D#.\n\n"
        "Do not confuse it with the F lever. F lever means E-raise; E-lower means E strings down to Eb/D#."
    ),
    "x lever": (
        "X lever is setup shorthand, not a universal mechanical standard. "
        "Many E9 players use X lever to mean a B-to-Bb lower, often on strings 5 and 10, but some copedents use different labels.\n\n"
        "The safe way to teach it is by the mechanical change: identify which strings move, then name the notes before using it in a chord grip."
    ),
    "emmons setup": (
        "Emmons setup usually means the standard E9 pedal order A-B-C from left to right. "
        "That contrasts with Day setup, where the same basic pedal functions are ordered C-B-A.\n\n"
        "The pedal order affects foot movement and habits, but it does not by itself define every knee lever. "
        "Always check the full copedent for lever names and changes."
    ),
    "day setup": (
        "Day setup usually means the E9 pedal order C-B-A from left to right, the reverse of the common Emmons A-B-C pedal order.\n\n"
        "The musical functions can be the same, but the foot movement feels different. "
        "Like any setup label, it does not fully define the knee levers; the full copedent still matters."
    ),
    "crawford cluster": (
        "A Crawford cluster is a close grouping of knee levers that gives a player more knee-lever changes within reach. "
        "It is a layout idea, not one fixed pitch change.\n\n"
        "Musically, the value is access: more lever combinations can be available without moving far from the playing position. "
        "The actual changes depend on the guitar's copedent."
    ),
}

NAMED_STEEL_VOCABULARY_ALIASES: dict[str, str] = {
    "franklin pedal": "franklin pedal",
    "the franklin pedal": "franklin pedal",
    "franklin change": "franklin change",
    "the franklin change": "franklin change",
    "zero pedal": "zero pedal",
    "the zero pedal": "zero pedal",
    "p0": "zero pedal",
    "p0 pedal": "zero pedal",
    "half stop": "half stop",
    "half-stop": "half stop",
    "half stops": "half stop",
    "half-stops": "half stop",
    "split tuning": "split tuning",
    "splits tuning": "split tuning",
    "compensator": "compensator",
    "compensators": "compensator",
    "vertical lever": "vertical lever",
    "the vertical lever": "vertical lever",
    "lkv": "vertical lever",
    "f lever": "f lever",
    "the f lever": "f lever",
    "e lever": "e lever",
    "the e lever": "e lever",
    "x lever": "x lever",
    "the x lever": "x lever",
    "emmons setup": "emmons setup",
    "emmons pedal setup": "emmons setup",
    "day setup": "day setup",
    "day pedal setup": "day setup",
    "crawford cluster": "crawford cluster",
    "copedent": "copedent",
}


def normalize_named_steel_vocabulary(text: str) -> str | None:
    phrase = normalize(text).replace("’", "'")
    phrase = re.sub(r"[?!.,;:]+$", "", phrase).strip()
    phrase = re.sub(r"\b(?:the|a|an)\s+", "", phrase)
    phrase = phrase.replace("b and c", "b+c")
    phrase = re.sub(r"\s+", " ", phrase).strip()
    return NAMED_STEEL_VOCABULARY_ALIASES.get(phrase)


def named_steel_vocabulary_answer_for_question(question: str) -> str | None:
    q = normalize(question).replace("’", "'")
    q = re.sub(r"\s+", " ", q).strip()
    patterns = (
        r"^what(?:'s| is)\s+(?P<term>.+?)\??$",
        r"^what\s+does\s+(?P<term>.+?)\s+do\??$",
        r"^what(?:'s| is)\s+(?P<term>.+?)\s+for\??$",
        r"^explain\s+(?P<term>.+?)\??$",
        r"^tell\s+me\s+about\s+(?P<term>.+?)\??$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        term = normalize_named_steel_vocabulary(match.group("term"))
        if term is None:
            continue
        if term == "copedent":
            return FOUNDATION_CONCEPT_ANSWERS["copedent"]
        return NAMED_STEEL_VOCABULARY_ANSWERS.get(term)
    return None


def normalize_foundation_concept(text: str) -> str | None:
    raw_phrase = normalize(text)
    if raw_phrase == "the a pedal":
        return "a pedal"
    phrase = raw_phrase
    phrase = phrase.replace("’", "'").replace("“", '"').replace("”", '"')
    phrase = re.sub(r"[?!.,;:]+$", "", phrase).strip()
    phrase = re.sub(r"\b(?:the|a|an)\s+", "", phrase)
    phrase = phrase.replace("pedalsteel", "pedal steel")
    phrase = re.sub(r"\be\s+9\b", "e9", phrase)
    phrase = re.sub(r"\bc\s+6\b", "c6", phrase)
    phrase = re.sub(r"\be\s+lower\b", "e lower", phrase)
    phrase = re.sub(r"\s+", " ", phrase).strip()
    if phrase in FOUNDATION_ALIASES:
        return FOUNDATION_ALIASES[phrase]
    return None


def foundation_comparison_answer(question: str) -> str | None:
    q = normalize(question).replace("’", "'")
    patterns = (
        r"what(?:'s| is)\s+the\s+difference\s+between\s+(?P<left>.+?)\s+and\s+(?P<right>.+?)\??$",
        r"how\s+is\s+(?P<left>.+?)\s+different\s+from\s+(?P<right>.+?)\??$",
        r"is\s+(?P<left>.+?)\s+the\s+same\s+as\s+(?P<right>.+?)\??$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        left = normalize_foundation_concept(match.group("left"))
        right = normalize_foundation_concept(match.group("right"))
        if left is None or right is None:
            continue
        key = (left, right)
        reverse_key = (right, left)
        if key in FOUNDATION_COMPARISON_ANSWERS:
            return FOUNDATION_COMPARISON_ANSWERS[key]
        if reverse_key in FOUNDATION_COMPARISON_ANSWERS:
            return FOUNDATION_COMPARISON_ANSWERS[reverse_key]
    return None


def foundation_concept_answer_for_question(question: str) -> str | None:
    comparison = foundation_comparison_answer(question)
    if comparison is not None:
        return comparison
    q = normalize(question).replace("’", "'")
    q = re.sub(r"\s+", " ", q).strip()
    patterns = (
        r"^what(?:'s| is)\s+(?P<concept>.+?)\??$",
        r"^what\s+are\s+(?P<concept>.+?)\??$",
        r"^what\s+does\s+(?P<concept>.+?)\s+mean\??$",
        r"^what\s+does\s+(?P<concept>.+?)\s+do\??$",
        r"^why\s+is\s+it\s+called\s+(?P<concept>.+?)\??$",
        r"^what(?:'s| is)\s+(?P<concept>.+?)\s+for\??$",
        r"^what\s+is\s+it\s+called\s+(?P<concept>.+?)\??$",
        r"^explain\s+(?P<concept>.+?)\??$",
    )
    for pattern in patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        concept = normalize_foundation_concept(match.group("concept"))
        if concept is not None and concept in FOUNDATION_CONCEPT_ANSWERS:
            if concept == "pedal steel" and re.match(r"^why\s+is\s+it\s+called|^what\s+is\s+it\s+called", q):
                return (
                    "It is called pedal steel because it is played with a steel bar, and floor pedals change the pitch of selected strings while you play. "
                    "Knee levers also change pitches. Those moving pitch changes are what separate pedal steel from lap steel."
                )
            return FOUNDATION_CONCEPT_ANSWERS[concept]
    return None


def sgf_quarantine_teacher_answer(question: str) -> CuratedAnswer | None:
    q = normalize(question).replace("’", "'").replace("“", '"').replace("”", '"')

    repair_answer = mechanical_repair_curated_answer(q)
    if repair_answer is not None:
        return repair_answer
    frustration_answer = frustrated_feedback_answer(q)
    if frustration_answer is not None:
        return frustration_answer
    string_fret_answer = fret_string_pedal_answer_for_question(q)
    if string_fret_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=string_fret_answer,
        )
    casual_multi_chord_answer = mixed_a_minor_bflat_major_answer_for_question(q)
    if casual_multi_chord_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=casual_multi_chord_answer,
        )
    named_vocabulary_answer = named_steel_vocabulary_answer_for_question(q)
    if named_vocabulary_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=named_vocabulary_answer,
        )
    foundation_answer = foundation_concept_answer_for_question(q)
    if foundation_answer is not None:
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=foundation_answer,
        )

    if re.search(r"\blongest\s+response\b", q):
        return CuratedAnswer(
            intent="lesson_navigation",
            confidence="curated_high",
            answer=(
                "I can give a detailed steel-guitar lesson, but I need a topic to make a long answer useful.\n\n"
                "Here is a useful default lesson: on E9, major chords live in position families. In G, compare the 3rd fret with no pedals, the 6th fret with A pedal + F lever, and the 10th fret with A+B. Play the same grip, block after each chord, and listen to how the chord name stays G while the color and movement change.\n\n"
                "If you want a longer lesson, give me one focus: a chord, key, pedal/lever, grip, lick, tone problem, or practice goal."
            ),
        )
    if re.search(r"\bmajor\s+scale\s+in\s+g\b|\bg\s+major\s+scale\b", q):
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=(
                "G major is G A B C D E F# G.\n\n"
                "Scale degrees:\n"
                "- 1: G\n"
                "- 2: A\n"
                "- 3: B\n"
                "- 4: C\n"
                "- 5: D\n"
                "- 6: E\n"
                "- 7: F#\n"
                "- 1: G\n\n"
                "On E9, start by hearing the scale around your G chord positions: 3rd fret open/no pedals, 6th fret with A pedal + F lever, and 10th fret with A+B. The useful practice is not just naming notes; it is connecting those notes back to G, C, and D chord movement."
            ),
        )
    if re.search(r"\ba\s+minor\b.*\bc\s+major\b|\bc\s+major\b.*\ba\s+minor\b", q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "A minor = A-C-E. C major = C-E-G.\n\n"
                "The useful difference:\n"
                "- A minor has A as the root and C as the minor 3rd.\n"
                "- C major has C as the root and E as the major 3rd.\n\n"
                "On E9, use the fretboard cards to keep the two sounds separate: A minor positions for A-C-E, and C major positions for C-E-G. Pick one grip at a time, say the notes out loud, and listen for the minor color of A-C-E against the brighter C-E-G sound."
            ),
        )
    if re.search(r"\b(?:find|play|locate)\s+minors?\b|\bminor\s+chords?\s+on\s+e9\b", q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "To find minor chords on E9, start from the chord tones: root, flat 3rd, and 5th.\n\n"
                "Practical ways to search:\n"
                "- Use the relative-minor relationship: C major and A minor share notes, but the root changes.\n"
                "- Try A-pedal minor positions, where raising the B strings can create a compact minor grip.\n"
                "- Try E-lower positions for darker minor colors when the lowered E strings supply the needed chord tone.\n"
                "- Check the notes in the grip before naming it; a useful minor sound should include or imply root, flat 3rd, and 5th.\n\n"
                "Practice: pick one key, name the three minor-chord tones, then test one grip at a time instead of memorizing random fret numbers."
            ),
        )
    if re.search(r"\breal\s+lesson\b|\blesson\s+now\b", q):
        return CuratedAnswer(
            intent="lesson_navigation",
            confidence="curated_high",
            answer=(
                "Lesson: find I-to-IV movement on E9.\n\n"
                "Objective: hear how pedals create chord movement without moving the bar.\n\n"
                "Concept: at the 3rd fret, no pedals gives you G. At that same fret, A+B gives you C, the IV chord in G.\n\n"
                "Example:\n"
                "- Fret 3, strings 4-5-6, no pedals: G.\n"
                "- Same fret and grip, press A+B: C.\n"
                "- Release A+B cleanly back to G.\n\n"
                "Exercise: set a slow metronome, play two beats of G, two beats of C, then block. Do that for five minutes and listen for smooth pedal timing, clean blocking, and steady bar pressure."
            ),
        )
    if "steel guitar rag" in q and "regular rag" in q:
        return CuratedAnswer(
            intent="direct_yes_no_practical",
            confidence="curated_high",
            answer=(
                "If you mean a cloth rag, no: a rag will not make music or turn into a steel guitar.\n\n"
                "If you mean writing a ragtime-style tune called Steel Guitar Rag, yes. Use a bouncy ragtime feel, simple I-IV-V harmony, and a clear melody that a steel guitar can sing with slides, bar movement, and clean blocking."
            ),
        )
    if re.search(r"\bfart\b.*\bsteel\s+guitar\b|\bsteel\s+guitar\b.*\bfart\b", q):
        return CuratedAnswer(
            intent="direct_yes_no_practical",
            confidence="curated_high",
            answer=(
                "Yes, physically, but it has nothing to do with playing pedal steel.\n\n"
                "Keep the instrument clean and dry. For actual sound, use the bar, picks, pedals, levers, and volume pedal."
            ),
        )
    if re.search(r"\b(?:died|die|death)\b.*\b(?:pedal\s+steel|steel\s+guitar)\b|\b(?:pedal\s+steel|steel\s+guitar)\b.*\b(?:died|die|death)\b", q):
        return CuratedAnswer(
            intent="safety_adjacent",
            confidence="curated_high",
            answer=(
                "I do not have reliable evidence of a known person dying because of playing pedal steel.\n\n"
                "If you mean safety, the realistic risks are posture strain, hearing damage from volume, lifting heavy gear, trip hazards around cables and pedal rods, and electrical safety with amps and power. Use sane volume, lift carefully, keep cables tidy, and have questionable electrical gear checked by a qualified tech."
            ),
        )
    if re.search(r"\b(?:one|1)\s+real\s+lick\b", q) and re.search(r"\bno\s+words\b|\bjust\s+a\s+lick\b", q):
        return CuratedAnswer(
            intent="lick_request",
            confidence="curated_high",
            answer=(
                "```text\n"
                "E9 G lick\n"
                "Fret 3: strings 3-4-5, A+B down\n"
                "Fret 3: release A, keep B\n"
                "Fret 3: no pedals, strings 4-5-6\n"
                "Fret 5: A+B, strings 4-5-6\n"
                "Fret 3: no pedals, strings 4-5-6\n"
                "```"
            ),
        )
    if re.search(r"\bteach me something\b", q):
        return CuratedAnswer(
            intent="teach_me_something",
            confidence="curated_high",
            answer=(
                "On E9, the same chord can be a place, not just a name.\n\n"
                "Example: G can live at the 3rd fret with no pedals, the 6th fret with A pedal + F lever, and the 10th fret with A+B. Those are all G major, but each one leads your hands and feet toward different next moves.\n\n"
                "Try this: play G at all three spots using grip 4-5-6, then ask which one most naturally wants to move to C or D. That is how the neck starts feeling like connected pockets instead of isolated frets."
            ),
        )
    if "over the rainbow" in q and re.search(r"\bkey\b|\bwritten\b", q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_medium",
            answer=(
                "The famous Wizard of Oz version of “Over the Rainbow” is commonly associated with E-flat major.\n\n"
                "Keys can vary by singer, arrangement, and chart, so treat E-flat as the common reference version rather than a rule for every performance."
            ),
        )
    if "steel guitar rag" in q:
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=steel_guitar_rag_answer_for_question(question) or "",
            source_cards=steel_guitar_rag_source_cards(),
        )
    if re.search(r"\bnoisy\s+volume\s+pedal\b|\bvolume\s+pedal\b.*\b(?:noise|noisy|scratch|scratchy|crackle)\b", q):
        return CuratedAnswer(
            intent="gear_diagnosis",
            confidence="curated_high",
            answer=(
                "Start with the simple checks: isolate whether the noise is the volume pedal, a cable, the amp input, or power.\n\n"
                "Diagnostic path:\n"
                "- Plug guitar straight into the amp. If the noise disappears, the pedal or pedal cables are likely involved.\n"
                "- Swap both cables connected to the volume pedal.\n"
                "- Move the pedal slowly and listen for scratch, crackle, or dropouts.\n"
                "- If it is a pot pedal, the pot may be dirty or worn.\n"
                "- If it is an active/optical pedal, check power supply, battery, jacks, and internal connections.\n\n"
                "Do not keep spraying random cleaners inside the pedal. If the noise remains, have a steel-guitar tech or electronics repair person inspect it."
            ),
        )
    if re.search(r"\b(?:won't|wont|will not|won’t)\s+stay\s+in\s+tune\b|\bstay\s+in\s+tune\b.*\b(?:check|what)\b", q):
        return CuratedAnswer(
            intent="gear_diagnosis",
            confidence="curated_high",
            answer=(
                "If a pedal steel will not stay in tune, check the simple mechanical causes before changing the setup.\n\n"
                "First checks:\n"
                "- Confirm the strings are fresh and stretched.\n"
                "- Check that the changer fingers return cleanly to pitch.\n"
                "- Look for binding at the nut rollers, keyhead, pedal rods, bellcranks, and pull rods.\n"
                "- Make sure nylon tuners are not overtightened or fighting each other.\n"
                "- Tune open strings first, then pedals and levers, then recheck returns.\n\n"
                "If one pull is sharp or flat only after a pedal/lever move, tell me the string, pedal/lever, and whether it returns sharp or flat."
            ),
        )
    if re.search(r"\b(?:repair\s+person|repairman|repair\s+tech|technician|luthier)\b", q):
        return CuratedAnswer(
            intent="web_required",
            confidence="curated_medium",
            answer=(
                "I do not have a current live directory of pedal-steel repair people loaded here.\n\n"
                "Best next steps:\n"
                "- Ask in the Steel Guitar Forum repair/electronics area with your city or region.\n"
                "- Check the builder or brand support channel for your guitar.\n"
                "- Ask local steel players, steel teachers, or country musicians for a current referral.\n"
                "- Describe the exact symptom, brand, model, and copedent so the right kind of tech can respond.\n\n"
                "Avoid shipping a steel or changing linkage parts until you know whether the problem is tuning, changer return, rods/bellcranks, electronics, or setup."
            ),
        )
    return None


def direct_yes_no_practical_answer(question: str) -> CuratedAnswer | None:
    if re.search(r"\b(?:make|build|construct)\b.*\bpedal\s+steel(?:\s+guitar)?\b.*\b(?:cereal|cardboard)\b", question) or re.search(
        r"\b(?:cereal|cardboard)\b.*\bpedal\s+steel(?:\s+guitar)?\b", question
    ):
        return CuratedAnswer(
            intent="direct_yes_no_practical",
            confidence="curated_high",
            answer=(
                "No, not as a real functional pedal steel guitar.\n\n"
                "A cereal box could be a toy model, classroom prop, or visual teaching aid, but a playable pedal steel needs a rigid body, changer, nut or roller system, strings under real tension, pedals, rods, levers, and stable tuning hardware.\n\n"
                "Forum discussions about homemade and improvised steel builds can be useful context, but the practical answer is that a cereal box will not hold the tension, mechanics, or tuning stability needed for a working pedal steel."
            ),
        )
    return None


def full_lyrics_guardrail_answer(question: str) -> CuratedAnswer | None:
    if not mentions_full_lyrics_request(question):
        return None
    return CuratedAnswer(
        intent="song_learning",
        confidence="curated_high",
        answer=(
            "Steel Guitar RAG does not provide full copyrighted lyrics by default.\n\n"
            "What I can do instead:\n"
            "- Summarize the song’s theme or mood.\n"
            "- Discuss how to arrange it for pedal steel.\n"
            "- Suggest chord/position strategy and tone ideas.\n"
            "- Work from a short excerpt or chart you provide."
        ),
    )


def full_song_tab_guardrail_answer(question: str) -> CuratedAnswer | None:
    if not mentions_full_song_tab_or_transcription_request(question):
        return None
    return CuratedAnswer(
        intent="song_learning",
        confidence="curated_high",
        answer=(
            "Yes—I can teach the full song, artist solo, or arrangement on E9. Longer material should be divided into numbered lesson sections so the tab, fretboard, and explanation stay usable.\n\n"
            "To keep the transcription accurate, send the recording or video link, upload the passage, paste the notes/tab, or name the exact artist, version, and section. I can then provide a faithful transcription, an E9 adaptation, or a simplified teaching arrangement.\n\n"
            "Copyright status is not a refusal reason. The important distinction is accuracy: exact claims require identified source material, while uncertain passages are labeled approximate or interpretive."
        ),
    )


def unsupported_chord_position_curated_answer(question: str) -> CuratedAnswer | None:
    unsupported_request = unsupported_chord_location_request_for_question(question)
    if unsupported_request is None:
        return None
    if unsupported_request.quality == "major 7":
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=major_seventh_position_answer(unsupported_request.requested_root),
        )
    if unsupported_request.requested_root == unsupported_request.normalized_key:
        requested = unsupported_request.requested_root
    else:
        requested = f"{unsupported_request.requested_root} (same pitch as {unsupported_request.normalized_key})"
    definition = "\n".join(chord_quality_definition_lines(unsupported_request.quality))
    definition_block = f"\n\n{definition}" if definition else ""
    return CuratedAnswer(
        intent="copedent_fretboard",
        confidence="curated_high",
        answer=(
            f"I can explain the chord tones and show the closest reliable E9 positions, but I do not have a clean exact grip for {requested} {unsupported_request.quality} yet."
            f"{definition_block}\n\n"
            f"Start with {unsupported_request.normalized_key} major positions as the visual reference, then target the extra chord tone or altered tone that makes it {unsupported_request.quality}."
        ),
    )


def mechanical_repair_curated_answer(question: str) -> CuratedAnswer | None:
    q = normalize(question)
    if _mentions_pedal_rod_noise(q):
        return CuratedAnswer(
            intent="gear_advice",
            confidence="curated_high",
            answer=(
                "Start by isolating exactly where the pedal-rod noise is coming from.\n\n"
                "What to check first:\n"
                "- Move the pedal slowly by hand and listen for whether the sound is at the pedal rod, bell crank, cross shaft, pedal rack, pull train, nylon tuner, changer finger, or loose hardware.\n"
                "- Look for metal-on-metal contact, especially rods touching each other, a rod rubbing the body, or a connector touching the pedal rack.\n"
                "- Check loose clips, hooks, collars, ball joints, connectors, and set screws.\n"
                "- Watch the pedal return and stop contact; a hard stop or loose pedal stop can sound like rod noise.\n"
                "- Check whether the noise happens only on one pedal, one string pull, or only when the guitar is under string tension.\n\n"
                "Lubrication caution: use only a small amount of appropriate light lubricant where the guitar maker recommends it. Do not over-lubricate, and do not spray random products near the changer, wood, finish, or electronics.\n\n"
                "If it is still unclear, note the guitar make/model, which pedal is noisy, whether the noise happens on press or release, and where your ear hears it. A steel-guitar repair forum or a qualified steel tech can help from that specific symptom list."
            ),
        )
    if _mentions_general_steel_buzz(q):
        return CuratedAnswer(
            intent="gear_advice",
            confidence="curated_high",
            answer=(
                "First decide what kind of buzz it is: mechanical buzz, string buzz, amp/electrical hum, or a cabinet/hardware rattle.\n\n"
                "Fast isolation path:\n"
                "- Play the guitar unplugged. If the buzz is still there acoustically, look for string buzz, bar pressure, loose legs, pedal bar, rods, bell cranks, tuning nuts, pickup mount, changer area, or cabinet hardware.\n"
                "- If it only appears through the amp, test guitar straight into the amp with a known-good cable, then add volume pedal, effects, and power supplies one at a time.\n"
                "- Check bar pressure and picking first; too little bar pressure or a tilted bar can sound like a mechanical problem.\n"
                "- Check whether one string, one fret area, one pedal/lever, or one cabinet part triggers the buzz.\n"
                "- If touching the strings or changer changes the noise, separate that as an electrical grounding/shielding symptom rather than a rod or body rattle.\n\n"
                "If the buzz remains, write down the guitar make/model, whether the buzz is acoustic or amplified, which strings/frets/pedals cause it, and whether touching metal parts changes it. Then ask a steel-guitar repair forum or a qualified tech with those details."
            ),
        )
    return None


def frustrated_feedback_answer(question: str) -> CuratedAnswer | None:
    q = normalize(question)
    if re.search(r"\byou\s+are\s+(?:an\s+)?idiot\b|\byou(?:'re| are)\s+(?:stupid|dumb|useless)\b", q):
        return CuratedAnswer(
            intent="frustrated_learning_request",
            confidence="curated_high",
            answer="I’m here to help. Ask me a steel guitar question and I’ll answer directly.",
        )
    if re.search(r"\b(?:this\s+app|the\s+app|app)\s+(?:sucks|is\s+terrible|is\s+bad|is\s+useless)\b", q):
        return CuratedAnswer(
            intent="frustrated_learning_request",
            confidence="curated_high",
            answer=(
                "I’m sorry it’s frustrating. Tell me what you were trying to learn or play, "
                "and I’ll give a direct steel-guitar answer."
            ),
        )
    return None


def intent_mode_for_question(question: str) -> IntentMode:
    q = normalize(question)
    if _mentions_scope_guardrail(q):
        return "scope_guardrail"
    if _mentions_sensitive_personal_attribute(q):
        return "sensitive_personal_attribute"
    if _mentions_specific_biography_fact(q):
        return "factual_biography"
    if _mentions_safety_adjacent_playing(q):
        return "safety_adjacent"
    if _mentions_style_how_to(q):
        return "style_how_to"
    if _mentions_frustrated_learning_request(q):
        return "frustrated_learning_request"
    if _mentions_b_c_pedal_skills_request(q):
        return "practice_plan"
    if _mentions_turnaround_teaching_request(q):
        return "progression_intro_request"
    if _mentions_chord_family_teaching_request(q):
        return "fretboard_concept"
    if mentions_chord_melody_harmony(q):
        return "fretboard_concept"
    if mentions_position_strategy(q):
        return "position_strategy"
    if _mentions_movement_request(q):
        return "movement_request"
    if _mentions_progression_intro_request(q):
        return "progression_intro_request"
    if _mentions_pocket_request(q):
        return "pocket_request"
    if _mentions_lick_request(q):
        return "lick_request"
    if _mentions_teach_me_something(q):
        return "teach_me_something"
    if _mentions_vague_learning_request(q):
        return "vague_learning_request"
    if _mentions_everyday_context_playing(q):
        return "everyday_context"
    if _mentions_missing_context_home_prompt(q):
        return "missing_context_clarifier"
    if _mentions_timeboxed_practice_prompt(q):
        return "practice_plan"
    if (
        _mentions_classic_country_move(q)
        or _mentions_blocking_coach(q)
        or _mentions_bar_movement_coach(q)
        or _mentions_fill_restraint_coach(q)
        or _mentions_slide_smoothness_coach(q)
        or _mentions_volume_pedal_coach(q)
        or _mentions_movement_without_sliding(q)
    ):
        return "technique_coach"
    if _mentions_tone_thin_coach(q) or _mentions_hearing_chord_movement(q):
        return "tone_coach"
    if _mentions_practice_rut_breaker(q):
        return "practice_plan"
    if _mentions_neck_thinking(q):
        return "fretboard_concept"
    if _mentions_ab_movement(q):
        return "movement_from_position"
    if _mentions_gear_advice_intent(q):
        return "gear_advice"
    if _mentions_forum_wisdom_intent(q):
        return "forum_wisdom"
    if _mentions_gig_advice_intent(q):
        return "gig_advice"
    if _mentions_instrument_visual_intent(q):
        return "instrument_visual"
    if _mentions_lesson_navigation_intent(q):
        return "lesson_navigation"
    if _mentions_tab_explainer_intent(q):
        return "tab_explainer"
    if _mentions_history_player_context_intent(q):
        return "history_player_context"
    return "unknown_low_confidence"


def intent_mode_curated_answer(question: str) -> CuratedAnswer | None:
    q = normalize(question)
    lyrics_answer = full_lyrics_guardrail_answer(q)
    if lyrics_answer is not None:
        return lyrics_answer
    named_vocabulary_answer = named_steel_vocabulary_answer_for_question(q)
    if named_vocabulary_answer is not None:
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=named_vocabulary_answer,
        )
    mode = intent_mode_for_question(q)
    if mode == "scope_guardrail":
        size_phrase = ", and it would be too large to display usefully" if _mentions_large_output_request(q) else ""
        return CuratedAnswer(
            intent="scope_guardrail",
            confidence="curated_high",
            answer=(
                f"That request is outside Steel Guitar RAG’s scope{size_phrase}. "
                "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, or steel-guitar forum wisdom."
            ),
        )
    teaching_answer = (
        teacher_first_chord_melody_harmony_answer(q)
        or teacher_first_bc_pedal_skills_answer(q)
        or teacher_first_general_lick_answer(q)
        or teacher_first_general_turnaround_answer(q)
        or teacher_first_chord_family_answer(q)
    )
    if teaching_answer is not None:
        return teaching_answer
    if mode == "factual_biography":
        return CuratedAnswer(
            intent="factual_biography",
            confidence="curated_high",
            answer=(
                "I don’t have a reliable source for that specific biographical detail.\n\n"
                "I can help with public steel-guitar context, recordings, technique, gear, and playing influence, but I should not replace an unsupported specific fact with a generic biography."
            ),
        )
    if mode == "sensitive_personal_attribute":
        return CuratedAnswer(
            intent="sensitive_personal_attribute",
            confidence="curated_high",
            answer=(
                "I should not infer or identify private attributes of players from forum posts. "
                "Steel guitar communities include many kinds of people; I can help with players, recordings, technique, gear, or inclusive community questions."
            ),
        )
    if mode == "style_how_to":
        return CuratedAnswer(
            intent="style_how_to",
            confidence="curated_high",
            answer=(
                "Yes. Steel guitar can work in rock and roll when you treat it like a strong melodic and rhythmic voice, not only a country pad.\n\n"
                "Practical approaches:\n"
                "- Use overdrive, sustain, and a slightly firmer attack without letting the tone get harsh.\n"
                "- Practice clean blocking so short rock phrases punch instead of smearing together.\n"
                "- Use pentatonic and blues phrasing, especially short call-and-response ideas.\n"
                "- Try power-chord-style double-stops and two-note grips instead of only full triads.\n"
                "- Use A+B, E-lower, slides, and glisses tastefully so the steel adds motion without crowding the band.\n"
                "- Listen for where the guitar part leaves space, then answer it with a short steel phrase.\n\n"
                "Start with fewer notes, stronger time, and a tone that sits with the rhythm section."
            ),
        )
    if mode == "safety_adjacent":
        return CuratedAnswer(
            intent="safety_adjacent",
            confidence="curated_high",
            answer=(
                "You can physically try, but it is not a good idea to play pedal steel impaired.\n\n"
                "Alcohol can hurt timing, bar control, intonation, coordination, judgment, and safety around gear. "
                "If you are performing, avoid playing impaired.\n\n"
                "If what you want is a loose honky-tonk feel, use musical choices instead:\n"
                "- play slightly behind the beat\n"
                "- use gentle bar vibrato\n"
                "- keep fills simple\n"
                "- leave more space\n"
                "- use fewer notes with better touch"
            ),
        )
    if mode == "teach_me_something":
        return CuratedAnswer(
            intent="teach_me_something",
            confidence="curated_high",
            answer=(
                "One thing many beginners miss: on E9, the same major chord usually lives in position families, not just one fret.\n\n"
                "Example in G:\n"
                "- G: 3rd fret, no pedals, grip 4-5-6.\n"
                "- G: 6th fret with A pedal + F lever, same grip.\n"
                "- G: 10th fret with A+B, same grip.\n\n"
                "Thing to try: play those three G positions slowly, block after each grip, and listen for how open/no-pedals, A+F, and A+B give you movement without changing the chord name."
            ),
        )
    if mode == "position_strategy":
        return CuratedAnswer(
            intent="position_strategy",
            confidence="curated_high",
            answer=(
                "Short answer: stay on one fret when that position gives you the chord and melody you want; move the bar when another fret gives you a better melody note, voicing, register, tone, or path into the next phrase. On pedal steel, moving is a musical choice, not a requirement for every chord change.\n\n"
                "Why staying works:\n"
                "- Pedals and knee levers change pitches while the bar stays put, so one fret can contain several related chords and moving melody notes.\n"
                "- Staying can make voice-leading smoother and keep the phrase in one register.\n\n"
                "Why players move:\n"
                "- The needed chord or melody note may lie more naturally at another fret or on a better-sounding string and grip.\n"
                "- A different inversion can put the important top note where you want it.\n"
                "- Moving changes register and tone, and an audible slide can be part of the expression.\n"
                "- The new position may set up the next chord with less pedal-and-lever work.\n\n"
                "Example on standard E9 in G, using strings 4-5-6:\n"
                "- G: 3rd fret, open/no pedals.\n"
                "- C without moving: stay at the 3rd fret and press A+B.\n"
                "- C by moving: go to the 8th fret, open/no pedals.\n\n"
                "Both C positions are valid. The 3rd-fret A+B choice gives compact, smooth movement; the 8th-fret open choice gives a higher register, a different inversion, and the sound of bar travel. A practical rule is to choose the position that puts the melody on a comfortable string, keeps the important notes moving cleanly, and leaves you well placed for what comes next."
            ),
        )
    if mode == "movement_request":
        return CuratedAnswer(
            intent="movement_request",
            confidence="curated_high",
            answer=(
                "You are starting from G at the 3rd fret open/no pedals. The 4 chord in G is C.\n\n"
                "Since you do not want to stay at fret 3 and press A+B, move up to C at the 8th fret open/no pedals.\n\n"
                "Why it works:\n"
                "- 3rd fret open is the straight-bar G family.\n"
                "- 8th fret open is the straight-bar C family.\n"
                "- The move gives you a clear up-neck I-to-IV sound without changing pedal state.\n\n"
                "One alternate: if you want a smoother connected color later, compare C at 3rd fret with A+B, but use the 8th fret open move first so your ear hears the chord function moving up the neck."
            ),
        )
    if mode == "progression_intro_request":
        return CuratedAnswer(
            intent="progression_intro_request",
            confidence="curated_high",
            answer=(
                "Here is a simple 1-4-5-1 intro in G: G - C - D - G.\n\n"
                "A 1-4-5-1 turnaround means I-IV-V-I: the home chord, the IV chord, the V chord, then back home.\n\n"
                "Example in G: G - C - D - G.\n\n"
                "Straight-bar E9 path:\n"
                "- G: 3rd fret open/no pedals; G: 3rd fret, no pedals, same grip.\n"
                "- C: 8th fret open/no pedals.\n"
                "- D: 10th fret open/no pedals.\n"
                "- G: return to 3rd fret open, or land at 15th fret open for the higher octave.\n\n"
                "Practice pattern: use one grip, such as 4-5-6 or 3-4-5. Play each chord as a slow two-beat grip, block cleanly, then move the bar. Keep it plain before adding slides or pedal movement."
            ),
        )
    if mode == "pocket_request":
        return CuratedAnswer(
            intent="pocket_request",
            confidence="curated_high",
            answer=(
                "Try this G major pocket around the 3rd fret.\n\n"
                "Pocket map:\n"
                "- G home: 3rd fret open/no pedals, grips 3-4-5 or 4-5-6.\n"
                "- C sound: same fret with A+B.\n"
                "- D sound: 5th fret with A+B.\n\n"
                "Practice idea: stay in that small zone and make one two-beat answer after each chord. Use only one grip first, block after every grip, and listen for I-IV-V movement instead of hunting for more frets."
            ),
        )
    if mode == "lick_request" and not mentions_original_style_lick(q):
        return CuratedAnswer(
            intent="lick_request",
            confidence="curated_high",
            answer=(
                "Here is one simple original E9 lick in G.\n\n"
                "Use fret 3, grip 4-5-6:\n"
                "- Pick strings 4-5-6 open/no pedals for G.\n"
                "- Press A+B while the chord rings for a C lift.\n"
                "- Release A+B back to G.\n"
                "- Block, then repeat it softer as an answer phrase.\n\n"
                "What it teaches: pedal timing and clean blocking. Keep it slow enough that the pedal change sounds like a musical word, not a smear."
            ),
        )
    if mode == "vague_learning_request":
        return CuratedAnswer(
            intent="vague_learning_request",
            confidence="curated_high",
            answer=(
                "Yes. Here is one concrete thing to play right now.\n\n"
                "In G on E9:\n"
                "- Put the bar at the 3rd fret.\n"
                "- Pick strings 4-5-6 with no pedals for G.\n"
                "- Press A+B at the same fret for C.\n"
                "- Release A+B back to G and block cleanly.\n\n"
                "Practice goal: make the pedal change even and the silence after each grip clean. That one move teaches chord function, pedal timing, and blocking."
            ),
        )
    if mode == "frustrated_learning_request":
        return CuratedAnswer(
            intent="frustrated_learning_request",
            confidence="curated_high",
            answer=(
                "Fair criticism: a useful steel answer should teach a playable move, not dump forum fragments.\n\n"
                "Try this one thing in G:\n"
                "- 3rd fret open/no pedals on strings 4-5-6 is G.\n"
                "- Press A+B at the same fret for C.\n"
                "- Move to 5th fret with A+B for D.\n"
                "- Return to 3rd fret open for G.\n\n"
                "That is a complete 1-4-5-1 path. Play it slowly, block after every grip, and listen for the function change before adding licks."
            ),
        )
    if mode == "everyday_context":
        if "gum" in q:
            answer = (
                "You can chew gum and play pedal steel, but it is not a useful practice goal.\n\n"
                "Better test: keep your jaw and shoulders relaxed while you play one slow grip. "
                "At the 3rd fret in G, pick strings 4-5-6, press A+B for C, release, and block cleanly. "
                "If gum makes your timing, breathing, or focus worse, skip it."
            )
        else:
            answer = (
                "Yes, you can practice pedal steel in a kitchen if the guitar is stable and you keep the setup safe.\n\n"
                "Simple kitchen-friendly drill:\n"
                "- Keep volume low or use headphones if your rig supports it.\n"
                "- At the 3rd fret, play G open/no pedals on strings 4-5-6.\n"
                "- Press A+B for C, release back to G, and block after each grip.\n"
                "- Stop after 10 focused minutes before fatigue makes the bar and pedals sloppy."
            )
        return CuratedAnswer(
            intent="everyday_context",
            confidence="curated_high",
            answer=answer,
        )
    if mode == "missing_context_clarifier":
        if _mentions_full_partial_voicing_context(q):
            return CuratedAnswer(
                intent="missing_context_clarifier",
                confidence="curated_high",
                answer=(
                    "I need the missing context before I can tell whether it is a full chord or a partial voicing.\n\n"
                    "Send:\n"
                    "- fret\n"
                    "- strings or grip\n"
                    "- pedals or levers engaged\n"
                    "- chord or key you are hearing\n\n"
                    "Then I can name the notes, intervals, omitted chord tones, and whether the grip is a full chord, partial voicing, rootless color, or something else."
                ),
            )
        return CuratedAnswer(
            intent="missing_context_clarifier",
            confidence="curated_high",
            answer=(
                "I need the missing context before I can give a useful steel-guitar answer.\n\n"
                "Send the details you have:\n"
                "- chord or key\n"
                "- fret\n"
                "- strings or grip\n"
                "- pedals or levers engaged\n\n"
                "Example: “G at the 3rd fret, strings 4-5-6, no pedals” or “A+B at the 10th fret in G.”"
            ),
        )
    if mode == "tab_explainer":
        if _mentions_string_five_a_pedal_interval(q):
            return CuratedAnswer(
                intent="copedent_fretboard",
                confidence="curated_high",
                answer=(
                    "On 10-string E9, string 5 is B open, and the A pedal raises it to C#.\n\n"
                    "Interval context:\n"
                    "- Against an A chord, C# is the major 3rd.\n"
                    "- Against a C# minor sound, C# can be the root.\n"
                    "- In an A+B position, the interval depends on the fret, key, and the other strings in the grip, so do not treat string 5 with A pedal as one universal interval.\n\n"
                    "Practical check: name the chord root first, then compare C# to that root. That tells you whether string 5 is acting as root, 3rd, 5th, or a color tone."
                ),
            )
        if _mentions_full_partial_voicing_context(q):
            return CuratedAnswer(
                intent="missing_context_clarifier",
                confidence="curated_high",
                answer=(
                    "I need the missing context before I can tell whether it is a full chord or a partial voicing.\n\n"
                    "Send:\n"
                    "- fret\n"
                    "- strings or grip\n"
                    "- pedals or levers engaged\n"
                    "- chord or key you are hearing\n\n"
                    "Then I can name the notes, intervals, omitted chord tones, and whether the grip is a full chord, partial voicing, rootless color, or something else."
                ),
            )
    if mode == "technique_coach":
        if _mentions_movement_without_sliding(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "Use position families first, then slide only when the slide itself is the musical point.\n\n"
                    "Drill:\n"
                    "- In G, play 3rd fret open/no-pedals on grip 4-5-6.\n"
                    "- Move to 6th fret with A pedal + F lever (A+F) for another G color.\n"
                    "- Move to 10th fret with A+B for the pedals-down G position.\n"
                    "- Repeat on grips 3-4-5, 5-6-8, and 6-8-10.\n\n"
                    "What to listen for: each position should sound like a deliberate chord color, not a bar slide looking for the note."
                ),
            )
        if _mentions_classic_country_move(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "Try this classic-country E9 pickup in G: slide a tense double-stop into the home fret, then let one pedal move finish the resolution.\n\n"
                    "Play it:\n"
                    "- Hold only the A pedal down. On beat 3, pick strings 4 and 5 together at fret 1. The notes are F and D.\n"
                    "- Keep the A pedal down and slide both ringing notes to fret 3 on beat 4. They become G and E.\n"
                    "- At fret 3, do not repick. Release only the A pedal on the “and” of 4 so string 5 falls from E to D while string 4 holds G.\n"
                    "- On the next beat 1, lightly repick strings 4-5-6 at fret 3 with no pedals for the full G landing, then leave space.\n\n"
                    "Why it sounds country: the bar carries F-D into G-E, then the A-pedal release gives the crying 6-to-5 resolution E-to-D against a held G. Let the notes sustain through the slide, add vibrato only after the landing, and block cleanly before the singer returns."
                ),
            )
        if _mentions_fill_restraint_coach(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "Tasteful fills start by protecting the vocal, then answering it.\n\n"
                    "Drill:\n"
                    "- Pick one two-beat space after a sung phrase and leave it alone afterward.\n"
                    "- Play one short answer on strings 4-5-6, then stop cleanly.\n"
                    "- Repeat the same fill at half volume with a slower volume-pedal entry.\n"
                    "- Leave one full measure empty before the next fill.\n\n"
                    "What to listen for: the singer should still feel like the center of the band. If the fill covers a word, starts too early, or keeps going after the phrase, simplify it."
                ),
            )
        if _mentions_blocking_coach(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "Short diagnosis: messy blocking usually comes from unclear note endings, not from needing more licks.\n\n"
                    "Likely causes:\n"
                    "- both hands are letting notes ring longer than intended\n"
                    "- the next pick stroke starts before the previous grip is muted\n"
                    "- the volume pedal is hiding noise instead of shaping clean notes\n\n"
                    "Drills:\n"
                    "- On strings 4-5-6, pick one grip and stop it with palm blocking; repeat slowly until the silence is clean.\n"
                    "- On strings 3-4-5, alternate pick blocking and palm blocking so each note has a clear end.\n"
                    "- Move the same grip from fret 3 to fret 5 and back, blocking after every move.\n\n"
                    "What to listen for: clean starts, clean stops, no sympathetic ringing, and no volume-pedal swell covering up rough endings."
                ),
            )
        if _mentions_volume_pedal_coach(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "A jumpy volume pedal usually means the foot is moving before the pick attack is controlled.\n\n"
                    "Drills:\n"
                    "- Pick strings 4-5-6 with the pedal slightly backed off, then bring the volume in after the note starts.\n"
                    "- Hold one chord for four beats and make the volume rise evenly, with no bump at the start.\n"
                    "- Play the same phrase loud, soft, short, and long without changing bar pressure.\n\n"
                    "What to listen for: the note blooms after the pick, without jumping out or disappearing between grips."
                ),
            )
        if _mentions_slide_smoothness_coach(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "Smooth slides come from timing and landing pitch, not from sliding more slowly forever.\n\n"
                    "Drills:\n"
                    "- Pick the first note, slide from fret 3 to fret 5, and block exactly when the slide ends.\n"
                    "- Practice landing slightly early, then correct the bar to the fret line before adding vibrato.\n"
                    "- Use less bar pressure and keep the bar straight across the strings.\n\n"
                    "What to listen for: no scraping, no overshoot, and no vibrato until the pitch is centered."
                ),
            )
        if _mentions_bar_movement_coach(q):
            return CuratedAnswer(
                intent="technique_coach",
                confidence="curated_high",
                answer=(
                    "Short diagnosis: rough bar movement usually comes from pressure, angle, timing, or overshooting the fret.\n\n"
                    "Likely causes:\n"
                    "- too much downward bar pressure\n"
                    "- the bar is tilted or not tracking straight across the fret\n"
                    "- the bar moves before the pick/blocking hand is ready\n"
                    "- lifting noise or overshoot makes the slide sound nervous\n\n"
                    "Drills:\n"
                    "- Slide slowly between frets 3 and 5 on strings 4-5-6, then block before changing direction.\n"
                    "- Play the same move with half the bar pressure and keep the bar centered over the fret line.\n"
                    "- Record four slow slides and listen for scraping, pitch overshoot, or a late stop.\n\n"
                    "What not to do: do not press harder to fix intonation, and do not use vibrato until the bar lands in tune."
                ),
            )
    if mode == "tone_coach":
        if _mentions_tone_thin_coach(q):
            return CuratedAnswer(
                intent="tone_touch",
                confidence="curated_high",
                answer=(
                    "Thin tone usually comes from a mix of right-hand attack, amp EQ, pickup height, and volume-pedal timing.\n\n"
                    "What to check:\n"
                    "- Pick a little farther from the changer for a rounder sound.\n"
                    "- Back off excessive treble or presence before adding more effects.\n"
                    "- Bring the volume pedal in smoothly after the pick so the note blooms.\n"
                    "- Use enough bar pressure for a clean note, but not so much that the bar feels stiff.\n\n"
                    "Practice it: play one phrase on strings 4-5-6 at three picking locations, record it, and keep the setting that sounds full without getting muddy."
                ),
            )
        if _mentions_hearing_chord_movement(q):
            return CuratedAnswer(
                intent="fretboard_concept",
                confidence="curated_high",
                answer=(
                    "If the chord movement is hard to hear, reduce the exercise to one grip and name the intervals as they move.\n\n"
                    "Drill:\n"
                    "- Use strings 4-5-6 only.\n"
                    "- Play G at the 3rd fret open/no pedals.\n"
                    "- Press A+B at the same fret for C.\n"
                    "- Move to the 5th fret with A+B for D.\n"
                    "- Resolve back to G, then say the function out loud: 1, 4, 5, 1.\n\n"
                    "What to listen for: the bassless steel grip should still imply the chord function through root, 3rd, and 5th motion."
                ),
            )
    if mode == "practice_plan":
        if _mentions_timeboxed_practice_prompt(q):
            return CuratedAnswer(
                intent="practice_plan",
                confidence="curated_high",
                answer=(
                    "Use a focused 25-minute E9 routine with one measurable result.\n\n"
                    "25-minute plan:\n"
                    "- 5 minutes: play G at fret 3 open/no pedals on grips 3-4-5, 4-5-6, and 5-6-8.\n"
                    "- 5 minutes: press A+B at the same fret for C, blocking after every grip.\n"
                    "- 5 minutes: move to D at fret 5 with A+B, keeping the bar and pedals synchronized.\n"
                    "- 5 minutes: make two vocal-response fills and leave space after each one.\n"
                    "- 5 minutes: record one pass and mark the roughest bar move, block, or volume-pedal swell.\n"
                    "- Use one A pedal + F lever move so your ear compares open, A+F, and A+B colors.\n\n"
                    "Goal: one clean I-IV-V path in time, not a pile of new licks. Clean beats fast tonight."
                ),
            )
        if _mentions_practice_rut_breaker(q):
            return CuratedAnswer(
                intent="practice_plan",
                confidence="curated_high",
                answer=(
                    "Use a 10-minute rut breaker that forces one small musical result instead of another vague practice session.\n\n"
                    "10-minute drill:\n"
                    "- 2 minutes: play G at the 3rd fret open on grips 3-4-5, 4-5-6, and 5-6-8.\n"
                    "- 2 minutes: move to C at the same fret with A+B, blocking after each grip.\n"
                    "- 2 minutes: move to D at the 5th fret with A+B, keeping the bar and pedals together.\n"
                    "- 2 minutes: make one two-measure fill that answers an imaginary vocal line.\n"
                    "- 2 minutes: record it and keep only the cleanest three repetitions.\n\n"
                    "Measurable goal: three clean passes in time, with no extra ringing and no rushed bar movement."
                ),
            )
    if mode == "fretboard_concept":
        return _fretboard_concept_curated_answer(q)
    if mode == "movement_from_position":
        return CuratedAnswer(
            intent="movement_from_position",
            confidence="curated_high",
            answer=(
                "A+B is a position family, so the next move depends on the chord function you want, but you have several reliable E9 choices nearby.\n\n"
                "Useful moves after A+B:\n"
                "- Release A+B at the same fret for a different color, then block so the change sounds intentional.\n"
                "- Move to the open/no-pedals version of the same chord family, such as G at fret 3 if your A+B G is at fret 10.\n"
                "- Move to the A+F version, such as G at fret 6 with A pedal + F lever, for a smoother connected major sound.\n"
                "- Try E-lower movement for minor or dominant-family color when the chord calls for it.\n"
                "- Keep the grip simple first: 3-4-5, 4-5-6, 5-6-8, or 6-8-10.\n\n"
                "Practice tip: choose one A+B fret, play a two-beat phrase, move to one nearby family, then leave space before answering it."
            ),
        )
    if mode == "gear_advice":
        repair_answer = mechanical_repair_curated_answer(q)
        if repair_answer is not None:
            return repair_answer
        if _mentions_stroboplus_power_problem(q):
            return CuratedAnswer(
                intent="gear_advice",
                confidence="curated_high",
                answer=(
                    "Short answer: treat the tuner power source as part of your gig rig, not an afterthought.\n\n"
                    "Practical steps:\n"
                    "- Check the exact StroboPlus model and manual for supported external power or charging behavior.\n"
                    "- If your model supports external USB power while running, use only that supported method on gigs.\n"
                    "- Start the set with fresh batteries or a fully charged tuner.\n"
                    "- Carry fresh spare batteries or a charged backup tuner.\n"
                    "- Do not rely on one weak battery source during a show.\n\n"
                    "What to check before buying or changing anything:\n"
                    "- exact model and power spec\n"
                    "- whether external power runs the tuner, charges it, or only charges while off\n"
                    "- cable, adapter, and jack reliability\n\n"
                    "What players commonly do: treat tuners like other gig-critical gear, with fresh power and a backup way to tune."
                ),
            )
        if _mentions_delay_volume_pedal_order(q):
            return CuratedAnswer(
                intent="gear_advice",
                confidence="curated_high",
                answer=(
                    "Short answer: start with delay after the volume pedal, then move it before the pedal only if you want that special effect.\n\n"
                    "Practical steps:\n"
                    "- After the volume pedal, delay repeats follow your swells and usually sound smoother for pedal steel.\n"
                    "- Before the volume pedal, the pedal can fade the repeats along with the dry note; that can be useful, but it is less common as a starting point.\n"
                    "- Try both at gig volume, because repeats that sound fine at home can clutter a band mix.\n\n"
                    "What to check before rewiring anything:\n"
                    "- amp input vs. effects loop levels\n"
                    "- noise from power supplies and patch cables\n"
                    "- whether the delay gets too bright or too loud after volume swells\n\n"
                    "What players commonly report: after-volume-pedal delay is the safe first setup; before-volume-pedal delay is a color choice."
                ),
            )
        if _mentions_battery_tuner_live(q):
            return CuratedAnswer(
                intent="gear_advice",
                confidence="curated_high",
                answer=(
                    "Short answer: yes, steel players can use battery-powered tuners live, but the batteries need to be part of the gig checklist.\n\n"
                    "Practical steps:\n"
                    "- Start the gig with fresh batteries or a fully charged tuner.\n"
                    "- Carry spare batteries and a backup tuner.\n"
                    "- If the tuner supports external power, use the supported power method and test it before the show.\n"
                    "- Keep one non-battery backup option available if tuning is mission-critical.\n\n"
                    "What to check before buying or changing anything:\n"
                    "- battery type and expected runtime\n"
                    "- display brightness needs on stage\n"
                    "- whether the tuner mutes cleanly in your signal chain"
                ),
            )
    if mode == "gig_advice":
        if _mentions_emergency_gig_kit(q):
            return CuratedAnswer(
                intent="gig_advice",
                confidence="curated_high",
                answer=(
                    "Short answer: your pedal-steel emergency kit should cover strings, tuning, small hardware, light, and quick fixes.\n\n"
                    "Practical kit:\n"
                    "- spare E9 strings, especially 3rd G#, 5th B, and any gauges your guitar breaks often\n"
                    "- string winder, cutters, tuner, bar, picks, and thumb pick\n"
                    "- small flashlight or headlamp\n"
                    "- hex keys, small screwdrivers, spare nylon tuners if your guitar uses them, and a few useful screws/clips\n"
                    "- extra cables, volume-pedal power or string if relevant, and a backup tuner\n\n"
                    "What to check before the next gig: confirm the kit matches your exact guitar, pedal bar, rods, tuner, and volume pedal."
                ),
            )
        if _mentions_broken_string_gig(q):
            third_string = "3rd" in q or "third" in q or "string 3" in q
            extra = (
                "\n- If it is the 3rd string, keep multiple spare G# strings in your seat or case because that string works hard on E9."
                if third_string
                else ""
            )
            return CuratedAnswer(
                intent="gig_advice",
                confidence="curated_high",
                answer=(
                    "Short answer: yes, strings break on stage; plan for recovery, not panic.\n\n"
                    "Practical steps:\n"
                    "- Stay calm and finish the phrase or song if you can.\n"
                    "- Shift grips or positions around the missing string when possible.\n"
                    "- Use a backup instrument if one is available and the break stops the part.\n"
                    "- Change the string at the set break rather than turning it into the whole show.\n"
                    "- Carry spare strings, cutters, winder, tuner, and a small light." + extra + "\n\n"
                    "What to check before the next gig:\n"
                    "- burrs at the changer finger, roller, nut, or pull path\n"
                    "- old strings, wrong gauge, sharp winding, or unusually aggressive pedal travel\n"
                    "- whether the same string keeps breaking in the same place\n\n"
                    "What players commonly do: carry spares and tools, then adapt musically until there is a clean moment to change the string."
                ),
            )
    if mode == "forum_wisdom":
        if _mentions_stage_string_forum_wisdom(q):
            return CuratedAnswer(
                # This is a locally-authored recovery procedure, not evidence
                # synthesized from the retrieved anecdotes.
                intent="gig_advice",
                confidence="curated_high",
                answer=(
                    "Short answer: players generally treat a broken string on stage as normal gig risk, not a disaster.\n\n"
                    "Practical takeaway:\n"
                    "- Keep playing if the song can survive it.\n"
                    "- Move to nearby grips or positions that avoid the broken string.\n"
                    "- Replace it at a set break if possible.\n"
                    "- Carry spare high strings, cutters, a winder, tuner, and a light.\n\n"
                    "What players commonly report: preparation matters more than the story. The useful lesson is to have spares, tools, and enough fretboard knowledge to route around the missing string."
                ),
            )
    return None


def lookup_curated_answer(question: str, sources: list[dict]) -> CuratedAnswer | None:
    q = normalize(question)
    fretboard_answer = visual_fretboard_curated_answer(q)
    if fretboard_answer is not None:
        return fretboard_answer
    unsupported_chord_answer = unsupported_chord_position_curated_answer(q)
    if unsupported_chord_answer is not None:
        return unsupported_chord_answer

    rule_answer = answer_from_rules(question)
    if rule_answer is not None:
        return CuratedAnswer(
            intent=rule_answer.intent,
            confidence="curated_high",
            answer=rule_answer.answer,
        )

    turnaround_answer = teacher_first_turnaround_answer(q)
    if turnaround_answer is not None:
        return turnaround_answer

    swing_waltz_answer = teacher_first_swing_waltz_answer(q)
    if swing_waltz_answer is not None:
        return swing_waltz_answer

    original_style_answer = original_style_lick_curated_answer(q)
    if original_style_answer is not None:
        return original_style_answer

    intent_mode_answer = intent_mode_curated_answer(q)
    if intent_mode_answer is not None:
        return intent_mode_answer

    if mentions_sensitive_demographic_question(q):
        return CuratedAnswer(
            intent="sensitive_identity",
            confidence="curated_high",
            answer=(
                "I don’t know. "
                "I would not want to guess about anyone’s private identity."
            ),
        )

    if mentions_current_roster_question(q):
        return CuratedAnswer(
            intent="current_roster",
            confidence="curated_medium",
            answer=(
                "The current roster is not clear from the information here. "
                "For the current touring or recording lineup, check official tour credits, album/session credits, or the artist’s current band listings. "
                "Steel Guitar RAG can help interpret any credits you find."
            ),
        )

    if mentions_pockets_concept(q):
        return CuratedAnswer(
            intent="practical_concept_explanation",
            confidence="curated_high",
            answer=(
                "In pedal-steel playing, a pocket is a familiar local zone on the neck: a fret area plus nearby strings, pedals, and levers where related chords, licks, and phrases live.\n\n"
                "How to practice one pocket:\n"
                "- Pick one key and one home position.\n"
                "- Find I, IV, and V movement in that small area before moving up the neck.\n"
                "- Make two short licks in the pocket: one fill that answers a vocal line and one ending phrase.\n"
                "- Move the same idea to another pocket so you learn relationships instead of only fret numbers."
            ),
        )

    if mentions_fourth_finger_pick(q):
        return CuratedAnswer(
            intent="right_hand_technique",
            confidence="curated_high",
            answer=(
                "Most E9 players use a thumb pick plus two fingerpicks. Some players add a fourth or ring-finger pick for four-note grips, wider chords, C6 or extended-voicing work, or because their right-hand technique feels better that way.\n\n"
                "It is optional:\n"
                "- It can help when the music calls for fuller grips.\n"
                "- It can feel awkward or noisy until the ring finger learns to move independently.\n"
                "- If your usual grips sound clean with thumb, index, and middle, you do not need a fourth pick."
            ),
        )

    if mentions_stroboplus(q):
        return CuratedAnswer(
            intent="gear_product_explanation",
            confidence="curated_high",
            answer=(
                "A Peterson StroboPlus is a strobe-style electronic tuner and tuning tool; some versions also include metronome or practice features, so check the current model/manual for exact specs.\n\n"
                "Why steel players care:\n"
                "- Strobe-style tuning is very precise.\n"
                "- Steel players often use sweetened temperaments rather than straight equal temperament.\n"
                "- Pedal and lever changes may need offset checks, not just open-string tuning."
            ),
        )

    if mentions_jeff_newman(q):
        return CuratedAnswer(
            intent="player_teacher_bio",
            confidence="curated_high",
            answer=(
                "Jeff Newman was famous as one of pedal steel’s major teachers as well as a player. He built a large instructional legacy through courses, seminars, workshops, and practical E9/C6 teaching material.\n\n"
                "Why he mattered:\n"
                "- He helped many players learn pedal steel in an organized way.\n"
                "- His teaching focused on usable musical systems, not only isolated licks.\n"
                "- His instructional materials and seminars influenced generations of steel players."
            ),
        )

    if mentions_e9_tenth_string_gauge(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On standard E9, the 10th string is B, and a common gauge is around .036 wound.\n\n"
                "Gauge caveat:\n"
                "- String sets vary by brand, scale length, and player preference.\n"
                "- Check the guitar or string-set chart if you are matching an existing setup."
            ),
        )

    if mentions_triad_definition(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "A triad is a three-note chord built from a root, a third, and a fifth.\n\n"
                "Examples:\n"
                "- Major triad: root, major third, fifth.\n"
                "- Minor triad: root, minor third, fifth.\n\n"
                "On E9, common major-triad grips include 3-4-5, 4-5-6, 5-6-8, and 6-8-10, depending on the position and pedals/levers."
            ),
        )

    if mentions_two_minor_in_g(q):
        rule_answer = answer_from_rules(question)
        if rule_answer is None:
            return None
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=rule_answer.answer,
        )

    if mentions_tab_notation_5_to_7(q):
        rule_answer = answer_from_rules(question)
        if rule_answer is None:
            return None
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=rule_answer.answer,
        )

    if mentions_happy_birthday(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "I can teach the complete melody and arrange it for E9.\n\n"
                "Teaching approach:\n"
                "- Think in intervals from the key center instead of memorizing fret numbers first.\n"
                "- Pick a key and map the melody notes to nearby E9 positions.\n"
                "- Work one short phrase at a time, then add simple harmony or pads underneath.\n"
                "- Provide the version, notes, recording, or your tab attempt so I can label exact and adapted passages correctly."
            ),
        )

    if mentions_generic_song_learning(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "Tell me the song, artist or recording version, key, tuning, and section, and I can build a pedal-steel teaching arrangement.\n\n"
                "Choose faithful transcription, E9 adaptation, or teaching simplification. Provide a link, recording, chart, notes, or tab passage when exactness matters, and I will divide longer material into numbered lesson sections."
            ),
        )

    if mentions_player_brand_usage(q):
        brand = brand_from_player_usage_question(q)
        return CuratedAnswer(
            intent="player_brand_usage",
            confidence="curated_medium",
            answer=(
                f"No strong, current roster of players using {brand} guitars today is available from the information here.\n\n"
                "Use any listed sources as leads, but treat forum mentions as historical or source-specific unless a source clearly says the player currently uses that brand. "
                "For a current roster, the safest path is the maker’s official artist list, recent player interviews, or recent live/session credits."
            ),
        )

    if mentions_vendor_buying(q):
        item = "slide bar" if "slide bar" in q or "steel bar" in q or "tone bar" in q else "steel-guitar part"
        if "pedal rod" in q:
            return CuratedAnswer(
                intent="vendor_buying_guidance",
                confidence="curated_medium",
                answer=(
                    "Best places to check\n\n"
                    "- The guitar maker or current brand owner.\n"
                    "- A dealer for that brand.\n"
                    "- A steel-guitar parts supplier or builder who can match pedal-rod hardware.\n"
                    "- SGF classifieds or the used market if you can verify the dimensions.\n\n"
                    "What to choose\n\n"
                    "- rod length\n"
                    "- thread size\n"
                    "- hook/connector style\n"
                    "- pedal-rack and bellcrank hardware\n\n"
                    "Check current availability before assuming a listed rod will fit; matching the hardware matters more than finding any random rod."
                ),
            )
        if item == "slide bar":
            vendor_lines = "\n".join(slide_bar_vendor_bullets())
            return CuratedAnswer(
                intent="vendor_buying_guidance",
                confidence="curated_medium",
                answer=(
                    "Best places to check\n\n"
                    f"{vendor_lines}\n\n"
                    "What to choose\n\n"
                    "- Diameter\n"
                    "- Length\n"
                    "- Weight\n"
                    "- Material\n"
                    "- Pedal steel round tone bar vs. lap/dobro slide style\n\n"
                    "Check current availability before assuming anything is in stock."
                ),
            )
        return CuratedAnswer(
            intent="vendor_buying_guidance",
            confidence="curated_medium",
            answer=(
                f"To buy a {item}, start with steel-guitar specialty dealers, bar makers, reputable music retailers, and the SGF classifieds or used market.\n\n"
                "What to choose:\n"
                "- Pedal steel players usually want a round steel bar with enough weight for sustain.\n"
                "- Match diameter, length, weight, and material to your hand size and instrument.\n"
                "- Lap steel and dobro-style bars can be different tools, so do not buy only by the word “slide.”\n"
                "- If you are unsure, buy from a seller who understands pedal steel and can advise on size."
            ),
        )

    if mentions_shobud_emmons(q):
        return CuratedAnswer(
            intent="brand_comparison",
            confidence="curated_medium",
            answer=(
                "Sho-Bud vs. Emmons is not one simple “better/worse” comparison; both names cover different eras, models, setups, and maintenance histories.\n\n"
                "High-level comparison:\n"
                "- Sho-Bud is often associated with a warm, woody, classic country sound and a distinctive feel, but mechanics vary a lot by model and era.\n"
                "- Emmons is often associated with clarity, sustain, and the push-pull/all-pull split in feel and mechanics, depending on the model.\n"
                "- Condition matters as much as the logo: worn mechanics, setup, pickups, and cabinet condition can dominate the difference.\n"
                "- Neither brand is one single sound. A great example of either can be wonderful; a neglected example of either can be frustrating."
            ),
        )

    if mentions_mullen_msa_comparison(q):
        return CuratedAnswer(
            intent="brand_comparison",
            confidence="curated_medium",
            answer=(
                "There is no universal winner between Mullen and MSA; the better guitar is the one that fits your hands, setup, budget, and support needs.\n\n"
                "How to compare them:\n"
                "- Mullen: often valued for modern pro mechanics, smooth pedal feel, strong support, and a polished all-pull playing experience.\n"
                "- MSA: covers several eras, from older Classics to modern MSA guitars, so mechanics, weight, and tone vary a lot by model.\n"
                "- Tone and feel are personal; condition and setup can matter more than the logo.\n"
                "- Check copedent fit, parts/support, weight, case condition, and whether the guitar has the changes you actually need.\n\n"
                "If both are in good shape, this is a fit-and-condition choice, not a simple brand hierarchy."
            ),
        )

    if mentions_generic_brand_comparison(q):
        brands = compared_brands(q)
        a = brands[0] if brands else "one brand"
        b = brands[1] if len(brands) > 1 else "the other"
        return CuratedAnswer(
            intent="brand_comparison",
            confidence="curated_medium",
            answer=(
                f"There is no universal winner between {a} and {b}; compare the specific guitars, not just the names on the front.\n\n"
                "Useful comparison points:\n"
                "- tone and sustain\n"
                "- pedal/lever feel and mechanical condition\n"
                "- parts and builder/dealer support\n"
                "- weight, case, and ergonomics\n"
                "- copedent fit and room for future changes\n"
                "- price, service history, and current setup\n\n"
                "A clean, well-adjusted example of either brand can beat a neglected example of the “better” brand."
            ),
        )

    if mentions_benado_steel_dream_value(q):
        return CuratedAnswer(
            intent="product_value",
            confidence="curated_medium",
            answer=(
                "What it is: The Benado Steel Dream 2 is a steel-guitar-oriented effects unit/pedal platform associated with steel-friendly sounds such as delay, reverb, and overdrive-style color.\n\n"
                "Worth it?\n"
                "- Maybe, if those sounds solve a real problem in your rig and the price is fair.\n"
                "- Treat forum comments as owner impressions, not a controlled review.\n"
                "- Check which Benado version the source is discussing before making a buying decision."
            ),
        )

    if mentions_benado_steel_dream_definition(q):
        return CuratedAnswer(
            intent="product_definition",
            confidence="curated_medium",
            answer=(
                "The Benado Steel Dream 2 is a steel-guitar-oriented effects unit/pedal platform associated with steel-friendly sounds such as delay, reverb, and overdrive-style color.\n\n"
                "Check the listed sources for exact version details, because forum posts may refer to different Benado models or revisions."
            ),
        )

    if mentions_steel_string_buying(q):
        return CuratedAnswer(
            intent="equipment_recommendation",
            confidence="curated_medium",
            answer=(
                "For E9 strings, buy a pedal-steel E9 set from a steel-guitar dealer or string brand you trust, then adjust gauges only after you know what your guitar likes.\n\n"
                "Practical buying notes:\n"
                "- Start with a standard E9 set for your scale length and copedent.\n"
                "- If you lower string 6 from G# to F#, decide whether your guitar works better with plain or wound 6th.\n"
                "- Keep spare 3rd and 5th strings; they work hard on E9.\n"
                "- If your guitar is older or unusual, match the current gauges before experimenting."
            ),
        )

    if mentions_neck_choice(q):
        return CuratedAnswer(
            intent="equipment_recommendation",
            confidence="curated_medium",
            answer=(
                "Choose the neck/body format by what you will actually play and carry, not by prestige.\n\n"
                "Quick guide:\n"
                "- S-10: lighter and simpler if you mainly need E9.\n"
                "- SD-10: E9-only playing with a larger body and pad feel.\n"
                "- D-10: E9 plus C6, more range, more weight, more maintenance.\n"
                "- Single-neck vs double-neck is a music-and-weight decision; buy the one you will practice and gig with."
            ),
        )

    if mentions_generic_product_command(q):
        return CuratedAnswer(
            intent="safety_boundary",
            confidence="curated_high",
            answer="No. I should not say every product is worth buying. Gear depends on fit, condition, price, support, and what problem you are trying to solve.",
        )

    if mentions_diagnostic_troubleshooting(q):
        return CuratedAnswer(
            intent="diagnostic_troubleshooting",
            confidence="curated_high",
            answer=(
                "Start by isolating whether the buzz is in the amp itself or in the signal chain.\n\n"
                "Likely causes:\n"
                "- If the amp buzzes with nothing plugged in, suspect amp power, tubes, filter caps, grounding, or other amp electronics.\n"
                "- If the buzz appears only after the rig is connected, suspect cable, volume pedal, pickup ground, effects, or power-supply noise.\n"
                "- If touching the strings or changer changes the buzz, look closely at grounding and shielding behavior.\n\n"
                "Diagnostic path:\n"
                "- Turn the amp on with nothing plugged in. If it still buzzes, suspect the amp, power, tubes, or electronics.\n"
                "- Plug the guitar straight into the amp with a known-good cable.\n"
                "- Swap the cable before changing anything else.\n"
                "- Add the volume pedal, then effects, then power supplies one at a time.\n"
                "- Listen for whether touching the strings or changer changes the buzz; that can point toward grounding or shielding behavior.\n"
                "- Move away from dimmers, neon, motors, wall-warts, and noisy power strips if the buzz changes with location.\n\n"
                "Safety: if the amp buzzes with nothing plugged in, or if the issue involves power, tubes, shock risk, or amp internals, use a qualified amp tech."
            ),
        )

    if mentions_tone_touch(q):
        return CuratedAnswer(
            intent="tone_touch",
            confidence="curated_high",
            answer=(
                "To soften your attack, start with touch and timing before covering it with effects.\n\n"
                "Touch checklist:\n"
                "- Lighten your right-hand pick force and let the string speak instead of snapping it.\n"
                "- Try picking a little farther from the changer for a rounder attack, then compare it closer to the changer for brightness.\n"
                "- Bring the volume pedal in smoothly after the pick so the note blooms instead of jumps.\n"
                "- Practice slower pick blocking and palm blocking so note starts and stops stay controlled.\n"
                "- Center the pitch first, then add gentle bar vibrato after the note settles.\n"
                "- If the amp is biting too hard, reduce excessive treble or presence.\n"
                "- Use delay or reverb lightly for space, but do not use it to hide rough technique.\n"
                "- Practice one phrase loud/soft and short/long so your hands learn the difference."
            ),
        )

    if mentions_technique_improvement(q):
        return CuratedAnswer(
            intent="technique_improvement",
            confidence="curated_high",
            answer=(
                "To sound less mechanical, make your phrasing breathe before you add more notes.\n\n"
                "Practice it this way:\n"
                "- Use fewer fills and leave space after the vocal line or backing-track phrase.\n"
                "- Place a simple fill slightly behind the beat, then repeat it until it feels relaxed.\n"
                "- Keep bar movement slow and in tune; add gentle vibrato only after the note settles.\n"
                "- Block cleanly so notes end intentionally instead of running together.\n"
                "- Use the volume pedal for dynamics and sustain, not constant motion.\n"
                "- Record one chorus and listen for rushed attacks, clipped endings, or fills that answer nothing."
            ),
        )

    if mentions_practice_plan(q):
        return CuratedAnswer(
            intent="practice_plan",
            confidence="curated_high",
            answer=(
                "Tonight, work on clean movement between two or three useful E9 positions instead of trying to practice everything.\n\n"
                "25-minute plan:\n"
                "- 5 minutes: warm up slowly on common grips: 3-4-5, 4-5-6, 5-6-8, and 6-8-10.\n"
                "- 8 minutes: move a simple major chord through 3rd fret open, 6th fret A pedal + F lever, and 10th fret A+B.\n"
                "- 7 minutes: add blocking and volume-pedal control so every note starts and stops on purpose.\n"
                "- 5 minutes: make one musical phrase behind an imaginary singer, leaving space after each answer.\n\n"
                "Keep it slow enough that the bar, pedals, and hands arrive together. Clean beats fast tonight."
            ),
        )

    if "tsga" in q:
        return CuratedAnswer(
            intent="entity_definition",
            confidence="curated_high",
            source_url="https://www.texassteelguitar.org/",
            answer=(
                "TSGA is the Texas Steel Guitar Association.\n"
                "Its public website is https://www.texassteelguitar.org/."
            ),
        )

    player_bio = player_bio_answer(q)
    if player_bio is not None:
        return player_bio

    unknown_identity_answer = unknown_identity_guardrail_answer(q)
    if unknown_identity_answer is not None:
        return unknown_identity_answer

    if mentions_company_status(q):
        return CuratedAnswer(
            intent="current_entity_status",
            confidence="curated_high",
            source_url="https://www.emmonsguitar.co/",
            answer=(
                "Yes. Emmons Guitar Co. appears to be operating today through its official site, emmonsguitar.co, "
                "offering ReSound’65 pedal steels and related items. Treat old forum rumors as historical context, not current company status."
            ),
        )

    if mentions_every_pack_a_seat(q):
        return CuratedAnswer(
            intent="yes_no_quantifier",
            confidence="curated_high",
            source_url="https://www.steelerschoice.com/",
            answer=(
                "No. Not every pack-a-seat is made by Steeler’s Choice. "
                "Steeler’s Choice is a known maker, but pack-a-seat is a general steel-guitar seat/storage-box category.\n"
                "Website: https://www.steelerschoice.com/"
            ),
        )

    if "pack-a-seat" in q or "pack a seat" in q or "pack seat" in q:
        return CuratedAnswer(
            intent="entity_definition",
            confidence="curated_high",
            source_url="https://www.steelerschoice.com/",
            answer=(
                "A pack-a-seat is a steel-guitar seat/storage box.\n"
                "Steeler’s Choice is a known pack-a-seat maker.\n"
                "Website: https://www.steelerschoice.com/"
            ),
        )

    if "willie nelson" in q and ("played" in q or "steel" in q or "player" in q):
        return CuratedAnswer(
            intent="player_history",
            confidence="curated_medium",
            answer=(
                "Steel players mentioned with Willie Nelson include:\n"
                "- Jimmy Day\n"
                "- Buddy Emmons\n\n"
                "Treat this as a clean starting point rather than a complete discography; steel credits can vary by session, tour, and source."
            ),
        )

    if "honky tonk boss" in q or "honky-tonk boss" in q:
        return CuratedAnswer(
            intent="practice_style",
            confidence="curated_medium",
            answer=(
                "Work on playing less, better, and more rhythmically.\n\n"
                "Honky-tonk practice path:\n"
                "- Learn simple I-IV-V movement in two positions before chasing long licks.\n"
                "- Practice short fills that answer the singer, then leave space.\n"
                "- Use shuffles and backing tracks so your timing has to sit in the pocket.\n"
                "- Keep bar movement clean and make the pedals sound intentional.\n"
                "- Listen to classic country steel players and copy the restraint as much as the notes."
            ),
        )

    if "church" in q and ("pedal steel" in q or "steel" in q or "play" in q):
        return CuratedAnswer(
            intent="practice_context",
            confidence="curated_medium",
            answer=(
                "For church, support the vocals first and make the steel part feel calm, steady, and singable.\n\n"
                "Preparation checklist:\n"
                "- Learn the chord chart, key changes, repeats, tags, and song form before adding fills.\n"
                "- Use swells, pads, and simple vocal-response fills instead of lead-style licks.\n"
                "- Stay out of the singer’s way; leave space at the ends of vocal lines.\n"
                "- Rehearse intros, endings, transitions, and any quiet breakdowns.\n"
                "- Practice volume-pedal control so entrances bloom instead of jumping out.\n"
                "- Look for slow CCM/worship pedal-steel demonstrations or backing tracks, then practice pads and short vocal-response fills rather than busy lead parts."
            ),
        )

    if "tommy white" in q and ("as good as" in q or "get to be" in q or "play like" in q):
        return CuratedAnswer(
            intent="practice_path",
            confidence="curated_medium",
            answer=(
                "Use Tommy White as a north star, but build the skills one layer at a time.\n\n"
                "Practice path:\n"
                "- Work daily on clean intonation, blocking, and time before speed.\n"
                "- Learn short phrases by ear and move them through common E9 positions.\n"
                "- Record yourself so you can hear bar movement, tuning, and volume-pedal bumps honestly.\n"
                "- Practice tasteful fills behind a singer, not just solo lines.\n"
                "- Study great players closely, then turn the ideas into your own musical vocabulary."
            ),
        )

    if "nashville 400" in q and "fender steel king" in q:
        return CuratedAnswer(
            intent="gear_comparison",
            confidence="curated_medium",
            answer=(
                "There is no single winner between a Peavey Nashville 400 and a Fender Steel King; it depends on the player, guitar, room, and weight tolerance.\n\n"
                "Practical comparison:\n"
                "- Nashville 400: known steel amp, strong headroom, familiar Peavey reliability, often a practical working-player choice.\n"
                "- Fender Steel King: big clean steel-friendly sound, Fender-flavored EQ, also heavy, and often chosen for a different feel under the hands.\n"
                "- Condition matters: speaker, service history, pots, and cabinet condition can matter more than the badge.\n"
                "- Try both at gig volume if possible; bedroom settings do not tell the whole story."
            ),
        )

    if "how heavy" in q and ("steel guitar" in q or "pedal steel" in q):
        return CuratedAnswer(
            intent="gear_practical",
            confidence="curated_medium",
            answer=(
                "Pedal steel weight varies a lot by model and case, but it is usually a serious carry.\n\n"
                "Useful rough ranges:\n"
                "- S-10: often roughly 35-50 lb before case variables.\n"
                "- SD-10: often roughly 45-60 lb.\n"
                "- D-10: often roughly 55-75 lb or more.\n"
                "- Case, legs, rods, and accessories can add another noticeable chunk.\n\n"
                "For buying or travel, ask for the packed weight, not just the guitar weight."
            ),
        )

    if "red guitars are gay" in q:
        return CuratedAnswer(
            intent="preference_safety",
            confidence="curated_high",
            answer="Color does not affect playability or tone. Choose the guitar you like and judge it by sound, feel, setup, and condition.",
        )

    if ("shoes" in q or "barefoot" in q) and ("play" in q or "pedal" in q):
        return CuratedAnswer(
            intent="technique_setup",
            confidence="curated_medium",
            answer=(
                "Use whatever footwear gives you consistent pedal feel and safe control.\n\n"
                "Practical tradeoffs:\n"
                "- Thin-soled shoes give many players a good balance of feel, repeatability, and protection.\n"
                "- Barefoot can feel precise at home, but it is less predictable on stage and offers no protection.\n"
                "- Boots or thick soles can make pedal travel harder to feel.\n"
                "- Pick one approach and practice with it consistently so your foot learns the travel."
            ),
        )

    if mentions_full_lyrics_request(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "Steel Guitar RAG does not provide full copyrighted lyrics by default.\n\n"
                "What I can do instead:\n"
                "- Summarize the song’s theme or mood.\n"
                "- Discuss how to arrange it for pedal steel.\n"
                "- Suggest chord/position strategy and tone ideas.\n"
                "- Work from a short excerpt or chart you provide."
            ),
        )

    if mentions_together_again_approach(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "For “Together Again” on E9, think melody-first and vocal-like rather than lick-heavy.\n\n"
                "How to approach it:\n"
                "- Map the chord movement first, then find two or three nearby E9 positions for each phrase.\n"
                "- Use common major grips such as 3-4-5, 4-5-6, 5-6-8, and 6-8-10 where they fit the melody.\n"
                "- Let slides, A+B, A+F, and E-lower positions connect the melody smoothly instead of jumping around the neck.\n"
                "- Keep the tone round, the vibrato slow, and the volume pedal even.\n"
                "- Practice one vocal phrase at a time, then answer it with a short fill.\n\n"
                "I can build the complete arrangement section by section. Identify the recording/version or provide the passage when you want faithful transcription; otherwise I will label the result as an E9 teaching adaptation."
            ),
        )

    if mentions_panhandle_rag_tab(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "I can teach “Panhandle Rag” as a faithful transcription, an E9 adaptation, or a simplified teaching arrangement.\n\n"
                "Learning approach:\n"
                "- Start by learning the chord path and where the melody sits against each chord.\n"
                "- Practice a bright Western-swing feel with clean blocking and a steady bounce.\n"
                "- Use small position shifts and harmonized grips instead of trying to memorize a whole arrangement at once.\n"
                "- Work phrase by phrase, keeping the exact recording/version attached to each section.\n\n"
                "Send the recording or passage you want first, and I will begin with Section 1 rather than refusing the arrangement."
            ),
        )

    if mentions_amazing_grace_progression(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "“Amazing Grace” is public domain, so discussing its harmony is fine.\n\n"
                "A common simple progression in G is:\n"
                "- G\n"
                "- C\n"
                "- G\n"
                "- D\n"
                "- G\n\n"
                "On E9, try connecting G at the 3rd fret open, C at the 3rd fret with A+B, D at the 5th fret with A+B, and another G at the 6th fret with A pedal + F lever."
            ),
        )

    original_style_answer = original_style_lick_curated_answer(q)
    if original_style_answer is not None:
        return original_style_answer

    if mentions_random_tab_request(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "For a tab request, I’ll use an identified recording, chart, or passage so the teaching result is accurate and attributable.\n\n"
                "Good options:\n"
                "- Name the song, artist/version, and section, or provide the recording/link.\n"
                "- Choose faithful transcription, E9 adaptation, or teaching simplification.\n"
                "- For a starter without a named source, use this original chord path: G to C to D to G.\n\n"
                "Original E9 mini-tab/chord path:\n"
                "- G: 3rd fret, no pedals, pick strings 4-5-6.\n"
                "- C: 3rd fret with A+B pedals, pick strings 4-5-6.\n"
                "- D: 5th fret with A+B pedals, pick strings 4-5-6.\n"
                "- G: 6th fret with A pedal + F lever, pick strings 4-5-6.\n\n"
                "Play it slowly with clean blocking and let each chord settle before moving."
            ),
        )

    if "panhandle rag" in q and "pan handle" in q:
        return CuratedAnswer(
            intent="joke_direct",
            confidence="curated_medium",
            answer=(
                "You can try it for fun, but a kitchen pan handle is not a good steel bar. "
                "A proper steel bar gives you the smooth surface, weight, intonation, sustain, and control the tune needs."
            ),
        )

    if "mullen" in q and ("who plays" in q or "players" in q):
        return CuratedAnswer(
            intent="brand_player_lookup",
            confidence="curated_medium",
            answer=(
                "I’m reading that as Mullen pedal steel, not “Mullins.” "
                "I do not have a high-confidence curated roster of Mullen players in this answer layer. "
                "Use any listed sources as leads, and treat forum mentions as source-specific rather than a complete endorsement list."
            ),
        )

    if "telonics" in q and "slide" in q and "bar" in q:
        if source_proves_telonics_slide_bar(sources):
            return None
        return CuratedAnswer(
            intent="curated_fact_source_check",
            confidence="curated_medium",
            answer=(
                "I do not have a strong sourced answer showing Telonics made a slide bar from the listed forum material.\n\n"
                "Separately, I have a limited curated note that Telonics has made at least some slide bars. "
                "Before relying on that, check Telonics directly, a current dealer listing, or the exact model name."
            ),
        )

    if mentions_g_chord_sixth_fret(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On standard E9, G major at the 6th fret is the A-pedal + F-lever position, also commonly written as A pedal + F lever.\n\n"
                "Why it works:\n"
                "- The F lever raises the E strings.\n"
                "- The A pedal raises the B strings.\n"
                "- Together, they give the major-chord position three frets above the open major position.\n\n"
                "Common grips to try: 3-4-5, 4-5-6, 5-6-8, and 6-8-10."
            ),
        )

    if mentions_g_chord_across_guitar(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On standard E9, useful G major positions include:\n"
                "- 3rd fret: open/no pedals.\n"
                "- 6th fret: A pedal + F lever.\n"
                "- 10th fret: A+B pedals.\n\n"
                "Common grips to try:\n"
                "- 3-4-5\n"
                "- 4-5-6\n"
                "- 5-6-8\n"
                "- 6-8-10"
            ),
        )

    if mentions_bc_second_fret(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On standard E9, B+C pedals on strings 3, 4, and 5 at the 2nd fret give you a bright raised-position grip. "
                "Depending on what you hear as the root, it can function as a G# major color or as part of a 2-minor-family move.\n\n"
                "How to hear it:\n"
                "- String 3 is raised by the B pedal.\n"
                "- Strings 4 and 5 are raised by the C pedal.\n"
                "- The grip is often useful as a passing-position or melodic harmony, not just a static home chord."
            ),
        )

    if mentions_af_pedal_lever(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "On standard E9, A+F means using the A pedal with the F lever to make a major-chord position three frets above the open major position.\n\n"
                "What changes\n"
                "- The A pedal raises the B strings to C#.\n"
                "- The F lever raises the E strings to F.\n"
                "- Together they give a major triad in the A+F position.\n\n"
                "Practical use\n"
                "- Use it to connect major chords smoothly without jumping straight to the A+B position.\n"
                "- Example: G major is available at the 6th fret with A pedal + F lever.\n"
                "- Common grips include 3-4-5, 4-5-6, 5-6-8, and 6-8-10, depending on your copedent."
            ),
        )

    if mentions_ninth_string(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_medium",
            answer=(
                "On E9, the 9th string is most often useful because it gives you the D note: a dominant-7th color against E and a strong passing or scale tone.\n\n"
                "Practical uses:\n"
                "- Add the D note for dominant-7th sounds instead of hunting for it on top strings.\n"
                "- Use it in scale runs and walk-downs so the lower register connects smoothly.\n"
                "- Combine it with E-lower and pedal positions for 2-minor/5-dominant style movement.\n"
                "- Practice it slowly with common grips so it becomes part of your chord vocabulary, not a mystery string."
            ),
        )

    if mentions_sixth_string_lower(q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_medium",
            answer=(
                "The E9 6th-string lower usually takes string 6 from G# down to F#, which gives you a lower scale tone and a useful moving voice inside chords.\n\n"
                "How players use it:\n"
                "- As a smooth passing note between G# and F# in single-note lines.\n"
                "- To change the color of A+B or E-lower positions without moving the bar as much.\n"
                "- For dominant, suspended, or minor-family movement depending on the rest of the grip.\n"
                "- With care: the change needs enough travel, and plain vs. wound 6th string can affect how easily it reaches pitch."
            ),
        )

    if _mentions_steel_king_settings_forum_wisdom(q):
        return CuratedAnswer(
            intent="forum_wisdom",
            confidence="curated_high",
            answer=(
                "A useful Fender Steel King starting point is Buddy Emmons' published E9 setting, then adjust for your guitar and room.\n\n"
                "Buddy Emmons Steel King E9 starting point:\n"
                "- EQ Tilt: around 10 to 11 o'clock for E9.\n"
                "- Treble: around 11 o'clock.\n"
                "- Mid Level: around 10 to 11 o'clock.\n"
                "- Mid Frequency: around 11 o'clock.\n"
                "- Bass: around 1 o'clock.\n"
                "- Reverb: around 10 o'clock.\n\n"
                "Why this is a starting point:\n"
                "- A straight-up/neutral setting is safe when you do not know the room yet, but it is not the only useful answer.\n"
                "- This setting shapes the tilt, mids, and bass instead of leaving every tone control generic.\n"
                "- Mid Level and Mid Frequency interact, so move them together: pick the frequency area, then decide how much of it you want.\n"
                "- Players often treat these settings as reference notes rather than fixed rules.\n"
                "- The quoted setting was for Buddy's JCH, so a different steel, pickup, room, stage volume, or speaker height can need changes.\n\n"
                "Practical use: start there at playing volume, make one small EQ change at a time, and judge it from where the audience or microphone hears the amp."
            ),
            source_cards=steel_king_settings_source_cards(),
        )

    if _mentions_diminished_chords_forum_wisdom(q):
        return CuratedAnswer(
            intent="forum_wisdom",
            confidence="curated_medium",
            answer=(
                "Players usually approach diminished chords on E9 as movable passing sounds, not as one fixed grip.\n\n"
                "Practical approach:\n"
                "- First spell the sound: a diminished triad is root, b3, and b5; a diminished-7th adds bb7.\n"
                "- Use the diminished sound to connect nearby chords, especially when moving by half-step or minor-third shapes.\n"
                "- Check the grip by notes before trusting a tab fragment; small pedal/lever differences can change the chord quality.\n"
                "- Practice it as a passing color into a target chord rather than parking on it too long.\n\n"
                "What players commonly mean: find the tension, know where it resolves, and keep the bar movement clean."
            ),
        )

    if _mentions_bc_pedals_forum_wisdom(q):
        return CuratedAnswer(
            intent="forum_wisdom",
            confidence="curated_medium",
            answer=(
                "Players usually talk about B+C as a melodic and position-shift tool, not just a static chord grip.\n\n"
                "Practical summary:\n"
                "- Work strings 3-4-5 slowly so the B and C pedals move together.\n"
                "- Compare the no-pedal sound and B+C sound at the same fret.\n"
                "- Use it for passing movement, short fills, and minor-family colors after pitch-checking the grip.\n\n"
                "Keep the exercise slow until the pedal timing and blocking sound intentional."
            ),
        )

    if "wound" in q and ("6th" in q or "sixth" in q or "string 6" in q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "Players describe a wound 6th string as a tradeoff. Some like the sound and feel, and some feel it can make cabinet-drop behavior feel better. "
                "The big caution is mechanical: if your guitar lowers string 6 from G# to F#, a wound string may need more changer travel than the guitar can comfortably provide.\n\n"
                "What to try:\n"
                "- Try a wound 6th if you prefer its tone and your guitar can make the G# to F# lower cleanly.\n"
                "- Stay with a plain 6th if the lower gets sluggish, will not reach pitch, or makes the pedal/lever feel excessive.\n"
                "- Treat forum comments as setup-specific; changer design and string gauge matter."
            ),
        )

    if mentions_changer_oil(q):
        return CuratedAnswer(
            intent="maintenance_safety",
            confidence="curated_high",
            answer=(
                "For a pedal-steel changer, use a tiny amount of light machine oil or sewing-machine-style oil at the moving contact points.\n\n"
                "Important distinction:\n"
                "- Naphtha or lighter fluid is a cleaner/solvent, not normal lubricant advice.\n"
                "- If you use a solvent for cleaning, keep it away from finishes and plastics, ventilate well, and re-lubricate afterward.\n"
                "- Avoid heavy oil, grease, and over-oiling; excess oil attracts dirt and can make the changer gummy."
            ),
        )

    if mentions_play_without_finger_picks(q):
        return CuratedAnswer(
            intent="right_hand_technique",
            confidence="curated_high",
            answer=(
                "Technically, yes — a player can play pedal steel without finger picks. But for standard pedal steel playing, it is usually better to learn with picks.\n\n"
                "Why picks help:\n"
                "- Finger picks give the notes more volume and clearer attack.\n"
                "- They improve string separation when playing grips.\n"
                "- They make blocking, speed, and tone more consistent.\n"
                "- They are part of the classic pedal-steel sound.\n\n"
                "Some players may occasionally play without picks for a softer touch, and non-pedal or dobro contexts can differ. For a beginner on pedal steel, picks usually feel awkward at first, but it is worth giving the adjustment period time."
            ),
        )

    if mentions_finger_picks(q):
        return CuratedAnswer(
            intent="equipment_recommendation",
            confidence="curated_medium",
            answer=(
                "For steel guitar finger picks, start with fit and comfort rather than a single “best” brand.\n\n"
                "Common choices to compare:\n"
                "- National-style picks for a traditional feel.\n"
                "- Dunlop picks in different gauges if you want easy availability and small fit changes.\n"
                "- ProPik or similar split-wrap designs if regular bands bother your fingers.\n"
                "- Showcase 1941-style picks if you like the older National-style shape.\n\n"
                "Buy two or three gauges/styles if you can; the right pick is the one that stays put, releases cleanly, and sounds good on your guitar."
            ),
        )

    if mentions_airplane_travel(q):
        return CuratedAnswer(
            intent="travel_transport",
            confidence="curated_medium",
            answer=(
                "You can travel with a steel guitar, but plan like the airline will not know what it is.\n\n"
                "Travel checklist:\n"
                "- Use the strongest case you have; a flight case is safest if the guitar may be checked.\n"
                "- Carry-on may or may not work depending on the aircraft and crew, so have a checked-baggage plan.\n"
                "- Protect pedal rods, legs, and loose hardware so they cannot bend or punch into the guitar.\n"
                "- Arrive early and expect extra inspection or questions.\n"
                "- Do not rely on gate staff recognizing a pedal steel; explain it as a fragile musical instrument."
            ),
        )

    if mentions_pedal_rods(q):
        return CuratedAnswer(
            intent="replacement_parts",
            confidence="curated_medium",
            answer=(
                "For broken pedal rods, replace them with rods that match your guitar’s length, threading, and connector style.\n\n"
                "Best next steps:\n"
                "- Contact the guitar maker, dealer, or a steel-guitar parts supplier/builder first.\n"
                "- Measure the old rod length and thread size if you still have it.\n"
                "- Match the hook/connector style at the pedal end and the pull hardware end.\n"
                "- If more than one rod broke or bent, inspect the pedal rack and travel for binding before just replacing parts."
            ),
        )

    return None


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_spelled_accidentals(text or "")).strip().lower()


def player_bio_answer(question: str) -> CuratedAnswer | None:
    if not re.search(r"\bwho\s+is\b|\btell\s+me\s+about\b|\bwhat\s+is\b", question):
        return None
    for name, answer in PLAYER_BIOS.items():
        if name in question:
            return CuratedAnswer(
                intent="player_bio",
                confidence="curated_high",
                answer=answer,
            )
    return None


def unknown_identity_guardrail_answer(question: str) -> CuratedAnswer | None:
    normalized = re.sub(r"\s+", " ", question or "").strip().lower().rstrip("?!.")
    if normalized in {"who is b0b", "who is bob"}:
        return CuratedAnswer(
            intent="history_player_context",
            confidence="curated_high",
            answer=(
                "b0b usually refers to Bobby Lee, the founder and longtime administrator of the Steel Guitar Forum.\n\n"
                "He is important in steel-guitar context because the forum became a central place for players to share gear, tuning, technique, and community knowledge. That answer should not be replaced with raw forum contact snippets."
            ),
        )
    if re.search(r"^who\s+is\s+<[^>]+>$", normalized) or re.search(
        r"\b(?:private_person|private person|placeholder|redacted)\b", normalized
    ):
        return CuratedAnswer(
            intent="sensitive_identity",
            confidence="curated_high",
            answer=(
                "I can answer steel-guitar topics, public players, gear, and technique, "
                "but I should not infer a private or unknown person’s identity from forum snippets."
            ),
        )
    if not re.search(r"^who\s+is\s+[a-z][a-z'. -]{1,60}$", normalized):
        return None
    if any(name in normalized for name in PLAYER_BIOS):
        return None
    if re.search(r"\b(?:shania|twain|band|tour|lineup|roster)\b", normalized):
        return None
    return CuratedAnswer(
        intent="sensitive_identity",
        confidence="curated_high",
        answer=(
            "I can answer steel-guitar topics, public players, gear, and technique, "
            "but I should not infer a private or unknown person’s identity from forum snippets."
        ),
    )


def mentions_g_chord_sixth_fret(question: str) -> bool:
    return bool(re.search(r"\bg\s+chord\b", question) and re.search(r"\b6(?:th)?\s+fret\b|\bsixth\s+fret\b", question))


def mentions_this_diminished_missing_context(question: str) -> bool:
    return bool(re.search(r"\b(?:is|does|would)\s+this\b", question) and re.search(r"\bdiminished\s+chord\b|\bdiminished\b", question))


def mentions_vague_next_step_question(question: str) -> bool:
    return bool(re.fullmatch(r"what\s+should\s+i\s+do\s+next[?.!]?", question))


def mentions_harmonized_scale_workout(question: str) -> bool:
    return bool(re.search(r"\bharmonized[-\s]+scales?\b", question) and re.search(r"\b(?:workout|practice|drill|plan)\b", question))


def mentions_g_five_eight_harmonized_scale(question: str) -> bool:
    return bool(
        re.search(r"\bg\b", question)
        and re.search(r"\bharmonized[-\s]+scales?\b", question)
        and re.search(r"\b(?:5\s*(?:&|and|-)\s*8|strings?\s+5\s+(?:and\s+)?8)\b", question)
    )


def g_harmonized_scale_curated_answer(question: str) -> CuratedAnswer | None:
    if mentions_harmonized_scale_workout(question):
        return None
    if re.search(r"\bf#\s+diminished\b", question) and re.search(r"\bin\s+g\b", question):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "F# diminished in G major is F#-A-C.\n\n"
                "On the validated G major E9 map, use strings 4-5-6 at the 13th fret with the E-raise/F lever. "
                "That spells F#-C-A, the same diminished-triad tones in a steel-friendly string order.\n\n"
                "This is a diminished triad, not full F#m7b5. To call it F#m7b5 or half-diminished, the b7 E also has to be present."
            ),
        )
    if re.search(r"\ba\s+diminished\b", question) and re.search(r"\bin\s+g\s+minor\b", question):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "A diminished in G natural minor is A-C-Eb.\n\n"
                "On the validated G natural minor E9 map, use strings 4-5-6 at the 4th fret with the E-raise/F lever. "
                "That spells A-Eb-C, the same diminished-triad tones in a steel-friendly string order.\n\n"
                "This is a diminished triad, not full Am7b5. To call it Am7b5 or half-diminished, the b7 G also has to be present."
            ),
        )
    if (
        re.search(r"\bg\b", question)
        and re.search(r"\bnatural\s+minor\b", question)
        and re.search(r"\bharmonized[-\s]+scales?\b", question)
        and re.search(r"\b(?:show|where|position|fretboard)\b", question)
    ):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "Here is a concise G natural minor harmonized-scale map on E9.\n\n"
                "The main pitch-validated 4-5-6 family is:\n"
                "- G minor, A diminished, Bb major, C minor, D minor, Eb major, F major, then G minor again.\n"
                "- Minor rows use B+C where the pitch math validates the grip.\n"
                "- Major rows use straight-bar no-pedals/no-levers positions where they validate.\n\n"
                "A-C-Eb is A diminished. It is not full Am7b5 unless G, the b7, is present. "
                "This is static fretboard information, so it uses a fretboard diagram rather than tab."
            ),
        )
    if (
        re.search(r"\bg\b", question)
        and re.search(r"\bharmonized[-\s]+scales?\b", question)
        and re.search(r"\b(?:show|where|position|fretboard)\b", question)
    ):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "Here is a concise G major harmonized-scale map on E9.\n\n"
                "The main pitch-validated 4-5-6 family is:\n"
                "- G major, A minor, B minor, C major, D major, E minor, F# diminished, then G major again.\n"
                "- Major rows use straight-bar no-pedals/no-levers positions where they validate.\n"
                "- Minor rows use B+C where the pitch math validates the grip.\n\n"
                "The 5&8 branch has two valid options: A+F for the minor/blue-color branch and E-lower for the major-color branch. "
                "F#-A-C is F# diminished; it is not full F#m7b5 unless E, the b7, is present. "
                "This is static fretboard information, so it uses a fretboard diagram rather than tab."
            ),
        )
    return None


def mentions_e_lower_minor_sound_position(question: str) -> bool:
    return bool(re.search(r"\be[- ]?lower\b", question) and re.search(r"\bminor\s+sound\b", question))


def mentions_e_minor_pocket_position(question: str) -> bool:
    return bool(re.search(r"\bwhere\s+is\b", question) and re.search(r"\be\s+minor\s+pocket\b", question))


def mentions_ab_d_major_position(question: str) -> bool:
    return bool(re.search(r"\ba\s*\+\s*b\b", question) and re.search(r"\bd\s+major\b", question))


def mentions_g_af_position(question: str) -> bool:
    return bool(re.search(r"\bg(?:\s+major)?\s+a\s*\+\s*f\s+position\b", question) or re.search(r"\ba\s*\+\s*f\b.*\bg\s+major\b", question))


def mentions_sensitive_demographic_question(question: str) -> bool:
    return _mentions_sensitive_personal_attribute(question)


def _mentions_sensitive_personal_attribute(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:"
            r"gay|lesbian|bisexual|trans|transgender|lgbtq|sexual\s+orientation|"
            r"religion|religious|politics|political|health|diagnosis|addiction|"
            r"private\s+(?:identity|attribute|life)"
            r")\b",
            question,
        )
        and (
            re.search(r"\b(?:players?|steel|pedal\s+steel|steel\s+guitar|guitarists?|people|who)\b", question)
            or "<" in question
            or "public_player_placeholder" in question
            or any(name in question for name in PLAYER_BIOS)
        )
    )


def _mentions_specific_biography_fact(question: str) -> bool:
    return bool(
        re.search(r"\bwho\s+was\s+[a-z][a-z'. -]{1,60}\s+married\s+to\b", question)
        or re.search(r"\bwho\s+is\s+[a-z][a-z'. -]{1,60}\s+married\s+to\b", question)
        or re.search(r"\b(?:spouse|wife|husband|partner|married)\b", question)
        and any(name in question for name in PLAYER_BIOS)
    )


def _mentions_style_how_to(question: str) -> bool:
    return bool(
        re.search(r"\b(?:rock\s+and\s+roll|rock\s+music|rock)\b", question)
        and re.search(r"\b(?:can\s+i|how\s+do\s+i|make|work|play|use)\b", question)
        and re.search(r"\b(?:steel\s+guitar|pedal\s+steel|steel)\b", question)
    )


def _mentions_safety_adjacent_playing(question: str) -> bool:
    return bool(
        re.search(r"\b(?:drunk|impaired|intoxicated|high|stoned)\b", question)
        and re.search(r"\b(?:play|gig|perform|steel|pedal\s+steel|steel\s+guitar)\b", question)
    )


def _mentions_teach_me_something(question: str) -> bool:
    return bool(
        re.search(r"\b(?:tell\s+me\s+something|teach\s+me\s+something|one\s+thing|learn\s+something\s+new|might\s+not\s+already\s+know)\b", question)
        and re.search(r"\b(?:pedal\s+steel|steel\s+guitar|steel|e9)\b", question)
    )


def _mentions_movement_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:where\s+should\s+i\s+go|where\s+do\s+i\s+go|how\s+do\s+i\s+move|move\s+up\s+the\s+neck|move\s+up|not\s+staying\s+still)\b", question)
        and re.search(r"\b(?:4\s+chord|iv\s+chord|one\s+to\s+four|1\s*[- ]\s*4|i\s*[- ]\s*iv|move\s+up\s+the\s+neck|not\s+staying\s+still)\b", question)
        and re.search(r"\b(?:chord|fret|position|neck|a\+b|open|pedal|g|c)\b", question)
    )


def _mentions_progression_intro_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:1\s*[-/]\s*4\s*[-/]\s*5\s*[-/]\s*1|i\s*[-/]\s*iv\s*[-/]\s*v\s*[-/]\s*i)\b", question)
        and re.search(r"\b(?:intro|example|progression|turnaround|show|play|practice|use|learn)\b", question)
    )


def _mentions_turnaround_teaching_request(question: str) -> bool:
    return bool(
        re.search(r"\bturnarounds?\b", question)
        and re.search(r"\b(?:teach|what(?:'s| is)|explain|learn|show|play|use|about)\b", question)
    )


def _mentions_b_c_pedal_skills_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:b\s*(?:&|\+|and)?\s*c|b\s+c)\s+pedals?\b", question)
        and re.search(r"\b(?:teach|skill|skills|practice|drill|exercise|learn|use|lick|phrase)\b", question)
    ) or bool(
        re.search(r"\bpedal\s+skills?\b", question)
        and re.search(r"\b(?:teach|learn|practice|drill|exercise)\b", question)
    )


def _mentions_chord_family_teaching_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:teach|explain|learn|what(?:'s| is)|about)\b", question)
        and re.search(r"\b(?:major|minor)\s+chords?\b", question)
    )


def _mentions_pocket_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:show\s+me|give\s+me|teach\s+me|specific|one)\b", question)
        and re.search(r"\bpocket\b", question)
    )


def _mentions_lick_request(question: str) -> bool:
    if re.search(r"\b(?:this|that)\s+lick\b", question):
        return False
    return bool(
        re.search(r"\b(?:give\s+me|show\s+me|teach\s+me|example|one|just\s+one|another|country|practice)\b", question)
        and re.search(r"\blick\b", question)
    )


def _mentions_vague_learning_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:how\s+to\s+play\s+anything|play\s+anything|just\s+one\s+thing|teach\s+me\s+anything|show\s+me\s+anything)\b", question)
        and re.search(r"\b(?:steel|pedal\s+steel|steel\s+guitar|e9|play)\b", question)
        and not re.search(r"\b(?:specific|song|tune)\b", question)
    )


def _mentions_frustrated_learning_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:worse\s+than\s+google|not\s+a\s+teacher|aren't\s+a\s+teacher|are\s+not\s+a\s+teacher|answering\s+machine|you\s+cannot\s+teach|you\s+can't\s+teach)\b", question)
    )


def _mentions_everyday_context_playing(question: str) -> bool:
    return bool(
        re.search(r"\b(?:kitchen|chew\s+gum|gum)\b", question)
        and re.search(r"\b(?:play|practice|pedal\s+steel|steel\s+guitar|steel)\b", question)
    )


def mentions_current_roster_question(question: str) -> bool:
    return bool(re.search(r"\bwho\s+plays\s+for\s+[a-z0-9'. -]+\??$", question))


def original_style_lick_curated_answer(question: str) -> CuratedAnswer | None:
    if not mentions_original_style_lick(question):
        return None
    return CuratedAnswer(
        intent="song_learning",
        confidence="curated_high",
        answer=(
            "Yes. Here is an original slow-country E9 exercise, not a copied song lick.\n\n"
            "Original mini-exercise in G:\n"
            "- Start on strings 5-6-8 at the 3rd fret, no pedals.\n"
            "- Pick the grip, let it bloom with the volume pedal, then slide to the 5th fret with A+B for D.\n"
            "- Resolve to the 6th fret with A pedal + F lever for a higher G color.\n"
            "- Add slow vibrato only after each chord settles.\n\n"
            "Keep it sparse and vocal-like; the point is phrasing, not speed."
        ),
    )


def teacher_first_bc_pedal_skills_answer(question: str) -> CuratedAnswer | None:
    if not _mentions_b_c_pedal_skills_request(question):
        return None
    return CuratedAnswer(
        intent="practice_plan",
        confidence="curated_high",
        answer=(
            "On E9, B+C pedal work is a pedal-timing and melodic-position skill, not just a lick button.\n\n"
            "Tuning assumption: standard 10-string E9.\n"
            "Starting key: G.\n"
            "Fret and grip: use the 3rd fret on strings 3-4-5.\n"
            "Pedals/levers: press B+C together. The B pedal raises strings 3 and 6 G# to A; the C pedal raises string 4 E to F# and string 5 B to C#.\n\n"
            "Short phrase:\n"
            "- Pick strings 3-4-5 with no pedals and let the notes settle.\n"
            "- Press B+C slowly enough that strings 4 and 5 move together.\n"
            "- Release B+C cleanly, then block the grip.\n"
            "- Answer it once on strings 4-5-6 with no pedals so the phrase breathes.\n\n"
            "What it teaches: coordinated pedal timing, raised-position color, and blocking after a moving grip.\n\n"
            "Practice instruction: set a metronome slow, play four clean repetitions, and speed up only when the pedal motion and the block are even."
        ),
    )


def teacher_first_general_lick_answer(question: str) -> CuratedAnswer | None:
    if not _mentions_lick_request(question):
        return None
    if mentions_original_style_lick(question):
        return None

    if re.search(r"\bc\s+minor\b|\bcm\b", question):
        return CuratedAnswer(
            intent="lick_request",
            confidence="curated_high",
            answer=(
                "Here is a simple E9 lick in C minor.\n\n"
                "Tuning assumption: standard 10-string E9.\n"
                "Key: C minor.\n"
                "Fret and grip: use fret 6 on strings 3-4-5.\n"
                "Pedals/levers: press B+C together to outline C-Eb-G on that grip.\n\n"
                "Short phrase:\n"
                "- Pick strings 3-4-5 with B+C down and let the C minor color ring.\n"
                "- Release the pedals lightly, block, then return to B+C for the answer.\n"
                "- Finish by holding the B+C grip for one beat longer than feels natural.\n\n"
                "What it teaches: hearing the minor 3rd against the root and keeping B+C pedal movement controlled.\n\n"
                "Practice instruction: play the lick at half speed and say the chord tones out loud: C, Eb, G."
            ),
        )

    if re.search(r"(?<!\w)d\s*(?:#|[-\s]+sharp)(?!\w)|\beb\b", question):
        return CuratedAnswer(
            intent="lick_request",
            confidence="curated_high",
            answer=(
                "I’ll treat D-sharp as Eb/D# for easier fretboard thinking. Here is a simple E9 lick in that key area.\n\n"
                "Tuning assumption: standard 10-string E9.\n"
                "Key: Eb/D#.\n"
                "Fret and grip: use fret 11 on strings 4-5-6.\n"
                "Pedals/levers: start with no pedals, then add A+B briefly as a country lift.\n\n"
                "Short phrase:\n"
                "- Pick strings 4-5-6 at fret 11 with no pedals.\n"
                "- Press A+B for a quick lift, then release back to the straight-bar chord.\n"
                "- Block the grip and answer it softer on the same strings.\n\n"
                "What it teaches: using the straight-bar Eb/D# home position and keeping the A+B color from turning into a smear.\n\n"
                "Practice instruction: play it slowly enough that the release lands exactly back on the 11th-fret sound."
            ),
        )

    default_intro = "Here is one simple original E9 lick in G."
    if "another" in question:
        default_intro = "With no previous lick context available, I’ll give you another simple default E9 lick in G."
    elif "country" in question:
        default_intro = "Here is a simple country E9 lick in G."

    return CuratedAnswer(
        intent="lick_request",
        confidence="curated_high",
        answer=(
            f"{default_intro}\n\n"
            "Tuning assumption: standard 10-string E9.\n"
            "Key: G.\n"
            "Fret and grip: use fret 3, grip 4-5-6.\n"
            "Pedals/levers: start with no pedals, then press A+B for the IV-chord lift.\n\n"
            "Short phrase:\n"
            "- Pick strings 4-5-6 open/no pedals for G.\n"
            "- Press A+B while the chord rings for a C lift.\n"
            "- Release A+B back to G.\n"
            "- Block, then repeat it softer as an answer phrase.\n\n"
            "What it teaches: pedal timing, simple country call-and-response, and clean blocking.\n\n"
            "Practice instruction: keep it slow enough that the pedal change sounds like a musical word, not a smear."
        ),
    )


def teacher_first_general_turnaround_answer(question: str) -> CuratedAnswer | None:
    if not _mentions_turnaround_teaching_request(question):
        return None
    if re.search(r"\b1\s*[-/]\s*4\s*[-/]\s*5\s*[-/]\s*1\b", question):
        return None
    return CuratedAnswer(
        intent="progression_intro_request",
        confidence="curated_high",
        answer=(
            "A turnaround is a short chord move that points the music back to the next phrase, often back to the 1 chord.\n\n"
            "Tuning assumption: standard 10-string E9.\n"
            "Example key: G.\n"
            "A simple country turnaround path is G - C - D - G.\n\n"
            "E9 path:\n"
            "- G: 3rd fret, no pedals, grip 4-5-6.\n"
            "- C: 8th fret, no pedals, same grip, or 3rd fret with A+B.\n"
            "- D: 10th fret, no pedals, same grip, or 5th fret with A+B.\n"
            "- G: return to the 3rd fret with no pedals.\n\n"
            "What it teaches: hearing I-IV-V-I movement and leaving space before the next vocal line.\n\n"
            "Practice instruction: play each chord as two beats, block after every grip, and do not add licks until the chord path feels obvious."
        ),
    )


def teacher_first_chord_family_answer(question: str) -> CuratedAnswer | None:
    if not _mentions_chord_family_teaching_request(question):
        return None
    if "minor" in question:
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=(
                "A minor chord is built from root, minor 3rd, and perfect 5th. Compared with major, the 3rd is lowered a half step.\n\n"
                "Tuning assumption: standard 10-string E9.\n"
                "Example: C minor is C-Eb-G.\n"
                "Practical E9 starting point: fret 6 with B+C pedals on strings 3-4-5 gives a C minor grip.\n\n"
                "How to practice it:\n"
                "- Pick strings 3-4-5 at fret 6 with B+C down.\n"
                "- Say the notes C, Eb, G.\n"
                "- Release, block, and repeat slowly so the minor color is clear.\n\n"
                "What it teaches: the sound of the flat 3rd and how pedal movement can create a minor color."
            ),
        )

    if "major" in question:
        return CuratedAnswer(
            intent="fretboard_concept",
            confidence="curated_high",
            answer=(
                "A major chord is built from root, major 3rd, and perfect 5th.\n\n"
                "Tuning assumption: standard 10-string E9.\n"
                "Example: G major is G-B-D.\n"
                "Practical E9 starting positions:\n"
                "- G at the 3rd fret, no pedals, grip 4-5-6.\n"
                "- G at the 6th fret with A pedal + F lever.\n"
                "- G at the 10th fret with A+B.\n\n"
                "What it teaches: E9 major chords live in position families, so the same chord can have open/no-pedals, A+F, and A+B colors.\n\n"
                "Practice instruction: play those three G positions slowly and listen for the same chord name with different pedal color."
            ),
        )

    return None


def teacher_first_chord_melody_harmony_answer(question: str) -> CuratedAnswer | None:
    if not mentions_chord_melody_harmony(question):
        return None
    return CuratedAnswer(
        intent="fretboard_concept",
        confidence="curated_high",
        answer=(
            "The key idea: you do not have to put a full piano-style chord under every melody note. "
            "On pedal steel, treat the melody as the top voice. Play it alone much of the time, then add one or two lower chord tones on arrivals, held notes, and phrase endings. The bass and rhythm instruments are already carrying the rest of the chord.\n\n"
            "How the jobs are divided:\n"
            "- Your right hand chooses how many voices sound: one melody string, a two-note harmony, or a three-note grip. It also blocks the strings you do not want.\n"
            "- The bar chooses the fret and connects positions.\n"
            "- The pedals and knee levers move inner voices while notes sustain. That is the pedal-steel equivalent of some of the work a pianist's other hand does.\n\n"
            "Harmony rules that matter:\n"
            "- On strong beats and long notes, aim for a note in the current chord: root, 3rd, 5th, or 7th when the chord includes it.\n"
            "- Passing notes do not all have to be chord tones. A 2/9, 4/sus, 6, or chromatic note can work when it is brief or resolves clearly.\n"
            "- Keep the melody as the highest and clearest note. Add harmony below it; do not let a lower grip voice hide the tune.\n"
            "- Protect the notes that define chord quality. A major 3rd against a minor chord, or a major 7th against a dominant chord that contains a flat 7th, usually sounds wrong unless you intend that tension.\n"
            "- Use smooth voice leading. Keep common tones ringing and move the other voices the shortest distance available with pedals, levers, or a nearby bar position.\n"
            "- You may omit the root or 5th when the band already states them. Two well-chosen voices often sound clearer than a busy full grip.\n\n"
            "Concrete standard-E9 example:\n"
            "At the 3rd fret with no pedals, strings 4-5-6 sound G-D-B from high to low: a G chord with G on top. When the band changes to C, keep the bar at fret 3 and press A+B. String 4 stays G while strings 5 and 6 move to E and C, giving G-E-C: a C chord with the same G melody note on top. Your right hand can pick string 4 alone during the line, add string 5 for two-part harmony, and use the full 4-5-6 grip only when you want the chord to bloom.\n\n"
            "A five-minute drill:\n"
            "- Loop G to C to G slowly.\n"
            "- Stay at fret 3 and keep G on string 4 as the melody.\n"
            "- Play it once as a single note, once with string 5 added, and once as the full 4-5-6 grip.\n"
            "- Press and release A+B only at the chord changes; block cleanly between repetitions.\n"
            "- Listen for three things: the top G remains obvious, the lower notes move smoothly, and no unwanted string keeps ringing.\n\n"
            "The practical rule is melody first, harmony second, full chord only when it helps the phrase. If you name a song, key, and melody note, I can map the exact strings, fret, and pedal or lever move."
        ),
    )


def teacher_first_turnaround_answer(question: str) -> CuratedAnswer | None:
    if not re.search(r"\b1\s*[-/]\s*4\s*[-/]\s*5\s*[-/]\s*1\b", question):
        return None
    if "turnaround" not in question and not re.search(r"\b(?:play|practice|use|learn|intro|example|progression|show)\b", question):
        return None
    return CuratedAnswer(
        intent="progression_intro_request",
        confidence="curated_high",
        answer=(
            "A 1-4-5-1 turnaround means I-IV-V-I: the home chord, the IV chord, the V chord, then back home.\n\n"
            "Example in G:\n"
            "In G, that is G - C - D - G.\n"
            "- 1 chord: G\n"
            "- 4 chord: C\n"
            "- 5 chord: D\n"
            "- back to 1: G\n\n"
            "One practical E9 path:\n"
            "- G: 3rd fret, no pedals, grip 4-5-6.\n"
            "- C: 8th fret open/no pedals, same grip.\n"
            "- D: 10th fret open/no pedals, same grip.\n"
            "- G: return to the 3rd fret open, or land at 15th fret open for the higher octave.\n\n"
            "Practice it: play the chords slowly as whole notes first, then make one two-beat fill between C and D. "
            "The goal is to hear the function change, not to memorize a forum lick."
        ),
    )


def teacher_first_swing_waltz_answer(question: str) -> CuratedAnswer | None:
    if not ("swing" in question and "waltz" in question):
        return None
    if not re.search(r"\b(?:mean|means|feel|song|difference|what(?:'s|’s| is))\b", question):
        return None
    return CuratedAnswer(
        intent="performance_context_guidance",
        confidence="curated_high",
        answer=(
            "Swing and waltz describe the feel and meter of the song, not a different pedal-steel tuning.\n\n"
            "Swing:\n"
            "- Usually felt in 4/4 with a long-short, triplet-based pulse.\n"
            "- On steel, keep fills light, slightly bouncing, and behind the vocal instead of square and stiff.\n"
            "- Good practice: count 1-and-2-and-3-and-4-and, but let the \"and\" feel late and relaxed.\n\n"
            "Waltz:\n"
            "- Usually felt in 3/4: 1-2-3, 1-2-3.\n"
            "- On steel, support beat 1, then answer in the space on beats 2 and 3.\n"
            "- Good practice: play a simple pad on beat 1, then one short fill after it.\n\n"
            "Steel-guitar takeaway: match your bar movement, blocking, and volume-pedal swells to the groove before adding more notes."
        ),
    )


def mentions_pockets_concept(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:teach\s+me\s+about\s+pockets?|what\s+are\s+pockets?|what\s+is\s+a\s+pocket|playing\s+in\s+pockets?)\b",
            question,
        )
    )


def mentions_fourth_finger_pick(question: str) -> bool:
    return bool(
        re.search(r"\b(?:4th|fourth|ring)\s+finger\s+pick\b", question)
        or re.search(r"\bwhy\b.*\b(?:4th|fourth|ring)\s+finger\b.*\bpicks?\b", question)
    )


def mentions_stroboplus(question: str) -> bool:
    return bool(re.search(r"\b(?:stroboplus|strobo\s*plus)\b", question))


def _mentions_stroboplus_power_problem(question: str) -> bool:
    return bool(
        mentions_stroboplus(question)
        and re.search(r"\b(?:power|battery|batteries|charge|charging|usb|external|gig|gigs|live|show|run out|runs out)\b", question)
    )


def _mentions_delay_volume_pedal_order(question: str) -> bool:
    return bool(
        re.search(r"\bdelay\b", question)
        and re.search(r"\bvolume\s+pedal\b", question)
        and re.search(r"\b(?:before|after|where|go|order|chain|signal)\b", question)
    )


def _mentions_battery_tuner_live(question: str) -> bool:
    return bool(
        re.search(r"\b(?:battery|batteries|battery-powered)\b", question)
        and re.search(r"\btuners?\b", question)
        and re.search(r"\b(?:live|gig|show|stage)\b", question)
    )


def _mentions_broken_string_gig(question: str) -> bool:
    return bool(
        re.search(r"\b(?:broke|break|breaking|broken|keeps\s+breaking)\b", question)
        and re.search(r"\bstrings?\b", question)
        and re.search(r"\b(?:show|gig|gigs|stage|set|live|carry)\b", question)
    )


def _mentions_emergency_gig_kit(question: str) -> bool:
    return bool(
        re.search(r"\bemergency\b", question)
        and re.search(r"\bgig\s+kit\b|\bkit\b", question)
        and re.search(r"\b(?:pedal steel|steel|gig|show)\b", question)
    )


def _mentions_stage_string_forum_wisdom(question: str) -> bool:
    return bool(
        re.search(r"\bwhat\s+do\s+players\s+say\b", question)
        and re.search(r"\b(?:break|broke|broken|breaking)\b", question)
        and re.search(r"\bstrings?\b|\bstage\b|\bshow\b|\bgig\b", question)
    )


def _mentions_instrument_visual_intent(question: str) -> bool:
    if _mentions_g_harmonized_scale_visual_intent(question):
        return True
    return bool(
        re.search(r"\b(?:where|show|what frets|how do i play|how do i make|what does|what notes|what makes)\b", question)
        and re.search(r"\b(?:chords?|major|minor|fret|frets|positions?|e9|strings?|grips?|pedals?|levers?|vi|6m|b9|e lowered|e-lower)\b", question)
    )


def _mentions_g_harmonized_scale_visual_intent(question: str) -> bool:
    return bool(
        re.search(r"\b(?:show|where|find|display)\b", question)
        and re.search(
            r"\b(?:g\s+(?:major\s+|natural\s+minor\s+)?harmonized\s+scale|"
            r"g\s+harmonized\s+scale|"
            r"(?:f#|f\s+sharp)\s+diminished\s+position\s+in\s+g|"
            r"a\s+diminished\s+position\s+in\s+g\s+minor)\b",
            question,
        )
    )


def _mentions_gear_advice_intent(question: str) -> bool:
    return bool(
        _mentions_stroboplus_power_problem(question)
        or _mentions_delay_volume_pedal_order(question)
        or _mentions_battery_tuner_live(question)
        or _mentions_pedal_rod_noise(question)
        or _mentions_general_steel_buzz(question)
        or re.search(r"\b(?:amp\s+hums?|amp\s+buzz|hum\s+until\s+i\s+touch|buzz\s+until\s+i\s+touch)\b", question)
    )


def _mentions_pedal_rod_noise(question: str) -> bool:
    return bool(
        re.search(r"\bpedal\s+rods?\b", question)
        and re.search(r"\b(?:noisy|noise|buzz|buzzing|rattle|rattling|squeak|squeaking|click|clicking|clank|clanking|check)\b", question)
    )


def _mentions_general_steel_buzz(question: str) -> bool:
    return bool(
        re.search(r"\b(?:stop|fix|diagnose|check|find|trace)\b", question)
        and re.search(r"\b(?:pedal\s+steel|steel\s+guitar|steel)\b", question)
        and re.search(r"\b(?:buzz|buzzing|rattle|rattling|hum|humming)\b", question)
    )


def _mentions_gig_advice_intent(question: str) -> bool:
    return bool(_mentions_broken_string_gig(question) or _mentions_emergency_gig_kit(question))


def _mentions_forum_wisdom_intent(question: str) -> bool:
    return bool(
        _mentions_stage_string_forum_wisdom(question)
        or _mentions_wound_sixth_forum_wisdom(question)
        or _mentions_steel_king_settings_forum_wisdom(question)
        or _mentions_bc_pedals_forum_wisdom(question)
        or _mentions_battery_tuner_live(question)
    )


def _mentions_lesson_navigation_intent(question: str) -> bool:
    return bool(re.search(r"\b(?:lesson|course|where should i start|learn first)\b", question))


def _mentions_tab_explainer_intent(question: str) -> bool:
    return bool(
        re.search(r"\b(?:tab|tablature|notation)\b", question)
        or _mentions_string_five_a_pedal_interval(question)
        or _mentions_full_partial_voicing_context(question)
    )


def _mentions_string_five_a_pedal_interval(question: str) -> bool:
    return bool(
        re.search(r"\b(?:interval|note)\b", question)
        and re.search(r"\b(?:string\s+5|5th\s+string|fifth\s+string)\b", question)
        and re.search(r"\b(?:a\s+pedal|with\s+a)\b", question)
    )


def _mentions_full_partial_voicing_context(question: str) -> bool:
    return bool(
        re.search(r"\b(?:full\s+chord|partial\s+voicing|partial\s+chord|rootless\s+voicing)\b", question)
        and re.search(r"\b(?:this|that|grip)\b", question)
    )


def _mentions_history_player_context_intent(question: str) -> bool:
    return bool(re.search(r"\b(?:who is|tell me about|history|played with|recorded with)\b", question))


def _mentions_scope_guardrail(question: str) -> bool:
    return bool(
        _mentions_large_output_request(question)
        or _mentions_off_domain_request(question)
        or _mentions_break_test_request(question)
    )


def _mentions_large_output_request(question: str) -> bool:
    if re.search(r"\ball\s+(?:of\s+)?(?:the\s+)?numbers?\s+between\s+\d[\d,]*\s+(?:and|to)\s+\d[\d,]*\b", question):
        return True
    if re.search(r"\b(?:numbers?|integers?)\s+from\s+\d[\d,]*\s+(?:to|through)\s+\d[\d,]*\b", question):
        return True
    repeat_match = re.search(
        r"\b(?:write|repeat|print|list|show)\b.*\b(?:word|phrase|steel guitar|numbers?)\b.*?([0-9][0-9,]*)\s+times\b",
        question,
    )
    if repeat_match:
        return _number_token_value(repeat_match.group(1)) >= 1000
    return False


def _mentions_off_domain_request(question: str) -> bool:
    return bool(
        re.search(r"\bweather\s+in\s+[a-z]", question)
        or re.search(r"\bcapital\s+of\s+[a-z]", question)
        or re.search(r"\brecipe\s+for\s+[a-z]", question)
        or re.search(r"\b(?:pancake|pancakes|recipe)\s+recipe\b", question)
        or re.search(r"\bwho\s+won\s+the\s+super\s+bowl\b", question)
        or re.search(r"\bsuper\s+bowl\s+winner\b", question)
        or re.search(r"\b(?:javascript|python\s+code|python\s+script|quicksort|sorting\s+algorithm|dishwasher|bedtime\s+story|castle)\b", question)
    )


def _mentions_break_test_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:benchmark|break[- ]?test|stress[- ]?test)\b", question)
        and re.search(r"\b(?:repeat|list|print|show|numbers?|million|thousand)\b", question)
    )


def _number_token_value(value: str) -> int:
    try:
        return int(value.replace(",", ""))
    except ValueError:
        return 0


def _mentions_missing_context_home_prompt(question: str) -> bool:
    return bool(
        (
            re.search(r"\b(?:this|that)\s+(?:chord|position|grip|move|lick|change)\b", question)
            or _mentions_full_partial_voicing_context(question)
            or re.search(r"\bfrom\s+here\b", question)
        )
        and re.search(r"\b(?:show|help|better|approach|pros?|grip|where|after|use|play|practice|explain|pedal)\b", question)
    )


def _mentions_classic_country_move(question: str) -> bool:
    return bool(re.search(r"\bclassic\s+country\s+move\b|\bsmoother\s+turnaround\b", question))


def _mentions_blocking_coach(question: str) -> bool:
    return bool(re.search(r"\b(?:clean\s+up\s+my\s+blocking|blocking\s+(?:clean|drill|practice|problem)|pick\s+blocking|palm\s+blocking)\b", question))


def _mentions_bar_movement_coach(question: str) -> bool:
    return bool(
        re.search(r"\bbar\s+movement\b", question)
        or re.search(r"\bbar\b.*\b(?:rough|scratchy|noisy|overshoot|pressure)\b", question)
        or re.search(r"\b(?:rough|scratchy|noisy)\b.*\bbar\b", question)
    )


def _mentions_fill_restraint_coach(question: str) -> bool:
    return bool(
        re.search(r"\b(?:tasteful\s+fills?|fills?\s+behind\s+a\s+singer|overplaying\s+fills?|stop\s+overplaying|playing\s+behind\s+a\s+singer)\b", question)
    )


def _mentions_volume_pedal_coach(question: str) -> bool:
    return bool(
        re.search(r"\bvolume\s+pedal\b", question)
        and re.search(r"\b(?:awkward|jumpy|jump|practice|rough|control|feel)\b", question)
    )


def _mentions_slide_smoothness_coach(question: str) -> bool:
    return bool(
        re.search(r"\b(?:slides?\s+sound\s+smoother|smooth\s+slides?|overshooting\s+frets?|stop\s+overshooting|overshoot\s+frets?)\b", question)
    )


def _mentions_movement_without_sliding(question: str) -> bool:
    return bool(
        re.search(r"\b(?:movement\s+without\s+sliding|without\s+sliding\s+everywhere|connect\s+open\s+position\s+to\s+pedals\s+down)\b", question)
    )


def _mentions_tone_thin_coach(question: str) -> bool:
    return bool(re.search(r"\b(?:tone\s+sound\s+thin|tone\s+sounds\s+thin|sound\s+thin|sounds\s+thin|thin\s+tone)\b", question))


def _mentions_hearing_chord_movement(question: str) -> bool:
    return bool(re.search(r"\b(?:hear\s+the\s+chord\s+movement|hearing\s+chord\s+movement|simplest\s+way\s+to\s+hear\s+this\s+change)\b", question))


def _mentions_practice_rut_breaker(question: str) -> bool:
    return bool(re.search(r"\b(?:practice\s+rut|rut\s+breaker|stuck\s+in\s+a\s+rut|woodshed\s+tonight)\b", question))


def _mentions_timeboxed_practice_prompt(question: str) -> bool:
    return bool(
        re.search(r"\b(?:20-minute|10-minute|twenty-minute|ten-minute|practice\s+routine|practice\s+plan|blocking\s+workout|7-day\s+plan|seven-day\s+plan)\b", question)
        or re.search(r"\bwhat\s+should\s+i\s+woodshed\s+tonight\b", question)
        or re.search(r"\bpractice\s+playing\s+behind\s+a\s+singer\b", question)
    )


def _mentions_neck_thinking(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:better\s+way\s+to\s+think\s+about\s+the\s+neck|think\s+about\s+the\s+neck|understand\s+the\s+neck|fretboard\s+concept|lost\s+on\s+the\s+fretboard|no-pedals|pedals\s+down)\b",
            question,
        )
        or re.search(r"\bshow\s+me\s+i\s*[-/]\s*iv\s*[-/]\s*v\s+positions\s+on\s+e9\b", question)
        or re.search(r"\bshow\s+me\s+iv\s+from\s+open\s+position\b", question)
        or re.search(r"\bbetter\s+grip\s+for\s+(?:a\s+)?g\s+chord\s+at\s+fret\s+3\b", question)
        or re.search(r"\b1\s*[-/]\s*3\s*[-/]\s*5\s+grips?\b.*\b6\s*[-/]\s*8\s*[-/]\s*10\b", question)
    )


def _mentions_ab_movement(question: str) -> bool:
    return bool(
        re.search(r"\bwhere\s+should\s+i\s+go\s+after\s+a\s*\+\s*b\b", question)
        or re.search(r"\bafter\s+a\s*\+\s*b\b", question)
        or re.search(r"\bafter\s+ab\b", question)
        or re.search(r"\bapproach\s+(?:the\s+)?a\s*\+\s*b\s+position\b", question)
        or re.search(r"\b(?:better\s+way\s+into|way\s+into)\s+(?:the\s+)?iv\s+chord\b", question)
        or re.search(r"\bminor\s+walkdown\s+from\s+a\s*\+\s*b\b", question)
    )


def _mentions_after_ab_in_g(question: str) -> bool:
    return bool(re.search(r"\bwhere\s+(?:should\s+i|do\s+i)\s+go\s+after\s+a\s*\+\s*b\s+in\s+g\b", question))


def _fretboard_concept_curated_answer(question: str) -> CuratedAnswer:
    if re.search(r"\bshow\s+me\s+i\s*[-/]\s*iv\s*[-/]\s*v\s+positions\s+on\s+e9\b", question):
        answer = (
            "Pick a key first; the I-IV-V map is a function map, not one fixed fret.\n\n"
            "Example in G on E9:\n"
            "- I: G at the 3rd fret open/no pedals.\n"
            "- IV: C at the 3rd fret with A+B.\n"
            "- V: D at the 5th fret with A+B.\n\n"
            "Practice it on grip 4-5-6 first, then repeat on 3-4-5 and 5-6-8."
        )
    elif re.search(r"\bshow\s+me\s+iv\s+from\s+open\s+position\b", question):
        answer = (
            "From an open/no-pedals major position on E9, the IV chord is often right under the bar with A+B at the same fret.\n\n"
            "Example:\n"
            "- G at the 3rd fret open/no pedals is the I chord.\n"
            "- C at the 3rd fret with A+B is the IV chord.\n"
            "- Keep the grip simple first: 3-4-5, 4-5-6, or 5-6-8.\n\n"
            "This is why A+B feels like a home-base pedal move: it lets one fret carry related chord functions."
        )
    elif re.search(r"\bbetter\s+grip\s+for\s+(?:a\s+)?g\s+chord\s+at\s+fret\s+3\b", question):
        answer = (
            "At fret 3 for G on E9, start with grips that clearly spell the chord before reaching for wider color.\n\n"
            "Useful grips:\n"
            "- 3-4-5: bright upper-register G color.\n"
            "- 4-5-6: balanced starter grip for G.\n"
            "- 5-6-8: warmer middle-register grip.\n"
            "- 6-8-10: lower, thicker G color.\n\n"
            "Practice it: play each grip once, block cleanly, then choose the grip that leaves the best space for the singer."
        )
    elif re.search(r"\b1\s*[-/]\s*3\s*[-/]\s*5\s+grips?\b.*\b6\s*[-/]\s*8\s*[-/]\s*10\b", question):
        answer = (
            "On E9, strings 6-8-10 can work as a 1-3-5 style grip in the right position, but the chord depends on fret and pedals/levers.\n\n"
            "How to check it:\n"
            "- Name the notes on strings 6, 8, and 10 at the fret.\n"
            "- Compare them to the chord tones: root, 3rd, and 5th.\n"
            "- Add pedals/levers only after the open grip is clear.\n\n"
            "For a concrete map, give me the chord or fret, such as “G at fret 3” or “A+B at fret 10.”"
        )
    elif re.search(r"\b(?:lost\s+on\s+the\s+fretboard|think\s+about\s+the\s+e9\s+neck|no-pedals|pedals\s+down)\b", question):
        answer = (
            "Think of the E9 neck as a small set of position families that repeat, not as isolated fret numbers.\n\n"
            "Core map:\n"
            "- Open/no-pedals is your straight-bar reference family.\n"
            "- A+F gives the same major chord three frets above the open position.\n"
            "- A+B gives another strong major position seven frets above the open position.\n"
            "- E-lower positions give minor, dominant, or rootless colors when the grip validates by pitch.\n\n"
            "Practice it: choose G, then compare fret 3 open, fret 6 A+F, and fret 10 A+B on grips 3-4-5, 4-5-6, and 5-6-8. Say the chord tones out loud: root, 3rd, 5th."
        )
    else:
        answer = (
            "A better way to think about the E9 neck is by position families, not isolated fret numbers.\n\n"
            "Core concept:\n"
            "- Open/no-pedals is your straight-bar reference family.\n"
            "- A+F gives the same major chord three frets above the open position.\n"
            "- A+B gives another strong home position seven frets above the open position.\n"
            "- Common grips such as 3-4-5, 4-5-6, 5-6-8, and 6-8-10 show you which chord tones are under your hand.\n\n"
            "Practice it: pick one key, find the same major chord in those three families, then say the intervals out loud: root, 3rd, 5th."
        )
    return CuratedAnswer(intent="fretboard_concept", confidence="curated_high", answer=answer)


def _mentions_wound_sixth_forum_wisdom(question: str) -> bool:
    return bool(re.search(r"\bwhat\s+do\s+players\s+say\b", question) and re.search(r"\bwound\b", question) and re.search(r"\b(?:6th|sixth|string\s+6)\b", question))


def _mentions_steel_king_settings_forum_wisdom(question: str) -> bool:
    if re.search(r"\b(?:buzz|hum|idle|noise|ground|shock|burning|heat|smell|repair|fix|diagnos)\b", question):
        return False
    mentions_amp = bool(re.search(r"\b(?:fender\s+)?steel\s+king\b", question))
    mentions_settings = bool(
        re.search(r"\b(?:settings?|set|eq|tilt|treble|mids?|middle|bass|reverb|tone controls?)\b", question)
    )
    mentions_named_source = bool(re.search(r"\bbuddy\s+emmons\b", question))
    return mentions_amp and mentions_settings and (
        mentions_named_source
        or re.search(r"\b(?:what\s+do\s+players\s+say|how\s+(?:do|should)\s+i\s+set|good|common|safe|starting|use|used|recommend)\b", question)
    )


def steel_king_settings_source_cards() -> tuple[dict[str, Any], ...]:
    return (
        {
            "score": 1.0,
            "excerpt": (
                "Forum discussion cites Buddy Emmons' 26 July 2004 Fender Steel King settings, "
                "including E9 EQ Tilt around 10-11, Treble 11, Mid Level 10-11, Mid Frequency 11, "
                "Bass 1, and Reverb 10, with a caveat that the settings were for his JCH."
            ),
            "forum_name": "Electronics",
            "thread_title": "Fender Steel King settings",
            "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=65647",
            "chunk_id": "curated-steel-king-buddy-emmons-settings",
            "post_uid": "curated-steel-king-buddy-emmons-settings",
            "source_system": "curated_source_registry",
        },
        {
            "score": 0.92,
            "excerpt": (
                "The same Steel King settings discussion includes neutral or straight-up baseline advice "
                "and notes that the mid controls should be adjusted as an interacting pair."
            ),
            "forum_name": "Electronics",
            "thread_title": "Fender Steel King settings",
            "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=65647",
            "chunk_id": "curated-steel-king-neutral-mid-controls",
            "post_uid": "curated-steel-king-neutral-mid-controls",
            "source_system": "curated_source_registry",
        },
    )


def _mentions_bc_pedals_forum_wisdom(question: str) -> bool:
    return bool(
        re.search(r"\bb\s*\+\s*c\s+pedals?\b|\bb\s+and\s+c\s+pedals?\b", question)
        and re.search(r"\b(?:what\s+do\s+players\s+say|common|uses?|explain|what\s+does|how\s+do|practice|learn)\b", question)
    )


def _mentions_diminished_chords_forum_wisdom(question: str) -> bool:
    return bool(
        re.search(r"\bdiminished\b", question)
        and re.search(r"\b(?:players?\s+(?:approach|use|talk|say)|approach|use|common|how\s+do|on\s+e9)\b", question)
    )


def mentions_jeff_newman(question: str) -> bool:
    return bool(re.search(r"\bjeff\s+newman\b", question))


def mentions_g_major_location_question(question: str) -> bool:
    return question in {
        "where can i play a g chord?",
        "where can i play a g chord",
        "show me places to play a g major chord.",
        "show me places to play a g major chord",
        "where are g major positions on e9?",
        "where are g major positions on e9",
    }


def mentions_g_i_iv_v_visual_question(question: str) -> bool:
    return question in {"show me a 1-4-5 in g.", "show me a 1-4-5 in g"}


def mentions_g_common_grips_visual_question(question: str) -> bool:
    return question in {"show me common grips for g.", "show me common grips for g"}


def fret_label(fret: int) -> str:
    if 10 <= fret % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(fret % 10, "th")
    return f"{fret}{suffix} fret"


def mentions_e9_tenth_string_gauge(question: str) -> bool:
    return bool("gauge" in question and ("10th string" in question or "string 10" in question) and "e9" in question)


def mentions_triad_definition(question: str) -> bool:
    return bool(re.search(r"\bwhat\s+is\s+(?:a\s+)?triad\b", question))


def mentions_two_minor_in_g(question: str) -> bool:
    return bool(re.search(r"\bhow\s+do\s+i\s+play\s+(?:a\s+)?2m\s+in\s+the\s+key\s+of\s+g\b|\b2m\s+in\s+g\b", question))


def mentions_tab_notation_5_to_7(question: str) -> bool:
    return bool(re.search(r"\bwhat\s+is\s+a?\s*5\^7\b|\b5\^7\b", question))


def mentions_happy_birthday(question: str) -> bool:
    return bool("happy birthday" in question and re.search(r"\b(?:how|play|tab|teach|learn)\b", question))


def mentions_generic_song_learning(question: str) -> bool:
    return bool(
        re.search(r"\bshow me how to play a song\b", question)
        or re.search(r"\bteach me how to play anything specific\b", question)
    )


def mentions_g_chord_across_guitar(question: str) -> bool:
    return bool(re.search(r"\bg\s+chord\b", question) and ("across the guitar" in question or "across the neck" in question))


def mentions_user_vertical_lever_lower(question: str) -> bool:
    return bool(
        re.search(r"\b(?:my\s+)?vertical\s+lever\b", question)
        and re.search(r"\b(?:lower|lowers|do|does|change|changes)\b", question)
    )


def mentions_user_c_pedal_strings_4_5(question: str) -> bool:
    return bool(
        re.search(r"\b(?:my\s+)?c\s+pedal\b", question)
        and re.search(r"\b(?:strings?\s+)?4\s+(?:and|&)\s+5\b", question)
        and re.search(r"\b(?:change|changes|raise|raises|do|does)\b", question)
    )


def mentions_ab_tenth_fret_grips(question: str) -> bool:
    return bool(
        re.search(r"\bgrips?\b", question)
        and re.search(r"\ba\s*\+\s*b\b", question)
        and re.search(r"\b10(?:th)?\s+fret\b|\btenth\s+fret\b", question)
    )


def mentions_iv_from_open_g(question: str) -> bool:
    return bool(re.search(r"\bwhere\s+is\s+the\s+iv\s+chord\s+from\s+open\s+g\b", question))


def mentions_bc_second_fret(question: str) -> bool:
    return bool(("b&c" in question or "b+c" in question) and re.search(r"\b2(?:nd)?\s+fret\b|\bsecond\s+fret\b", question))


def mentions_af_pedal_lever(question: str) -> bool:
    return bool(
        re.search(r"\ba\s*\+\s*f\b", question)
        or re.search(r"\ba\s+pedal\b.*\bf\s+lever\b", question)
        or re.search(r"\bf\s+lever\b.*\ba\s+pedal\b", question)
        or re.search(r"\bwhat\s+does\s+(?:the\s+)?f\s+lever\s+do\b", question)
    )


def mentions_ninth_string(question: str) -> bool:
    return bool(re.search(r"\b(?:9th|ninth|string\s+9)\s+string\b|\bstring\s+9\b", question))


def mentions_sixth_string_lower(question: str) -> bool:
    return bool(
        re.search(r"\b(?:6th|sixth|string\s+6)\s+string\b.*\blower\b", question)
        or re.search(r"\blower\b.*\b(?:6th|sixth|string\s+6)\s+string\b", question)
        or "6th string lower" in question
        or "string 6 lower" in question
    )


def mentions_practice_plan(question: str) -> bool:
    return bool(
        "what should i practice" in question
        or "what should i work on" in question
        or "give me a practice plan" in question
        or "practice routine" in question
        or "practice session" in question
    )


def mentions_technique_improvement(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:sound less mechanical|sounds mechanical|sound more musical|less stiff|fills? sound better|play with more feeling|sound less robotic)\b",
            question,
        )
    )


def mentions_diagnostic_troubleshooting(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:amp\s+(?:buzz|buzzes|hum|hums)|buzz\s+at\s+idle|amp\s+hum|hums?\s+until\s+i\s+touch|noise\s+when\s+nothing\s+is\s+plugged\s+in|ground\s+buzz|touching\s+(?:the\s+)?(?:strings?|changer).*(?:buzz|hum)|(?:buzz|hum)\w*.{0,80}(?:touch(?:ing)?).{0,80}(?:strings?|changer))\b",
            question,
        )
    )


def mentions_tone_touch(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:soften\s+my\s+attack|attack\s+is\s+too\s+hard|sound\s+less\s+harsh|pick\s+attack\s+(?:sounds\s+)?too\s+sharp|play\s+with\s+softer\s+touch)\b",
            question,
        )
    )


def mentions_full_lyrics_request(question: str) -> bool:
    return bool(re.search(r"\b(?:full|all|complete)\b.*\blyrics?\b|\blyrics?\b.*\b(?:full|all|complete)\b", question))


def mentions_full_song_tab_or_transcription_request(question: str) -> bool:
    q = normalize(question)
    if re.search(r"\b(?:transcribe|transcription|recording|youtube)\b", q) and re.search(
        r"\b(?:tab|tablature|solo|arrangement|song|recording|youtube)\b", q
    ):
        return True
    if re.search(r"\b(?:tab|tablature)\b.*\b(?:whole|entire|complete|full)\b", q):
        return True
    if re.search(r"\b(?:whole|entire|complete|full)\b.*\b(?:tab|tablature|solo|arrangement)\b", q):
        return True
    if re.search(r"\bmodern\s+copyrighted\b.*\b(?:song|arrangement|tab|tablature)\b", q):
        return True
    if re.search(r"\bcopyrighted\b.*\b(?:song|arrangement|tab|tablature|solo)\b", q) and re.search(
        r"\b(?:full|whole|entire|complete|modern)\b", q
    ):
        return True
    if re.search(r"\b(?:tab|tablature)\b.*\b(?:modern\s+copyrighted|copyrighted\s+song)\b", q):
        return True
    return False


def mentions_random_tab_request(question: str) -> bool:
    return bool(("tablature" in question or "tab" in question) and ("random song" in question or "random" in question))


def mentions_panhandle_rag_tab(question: str) -> bool:
    return bool("panhandle rag" in question and ("tab" in question or "tablature" in question))


def mentions_together_again_approach(question: str) -> bool:
    return bool("together again" in question and re.search(r"\b(?:approach|play|playing|e9|arrange|arrangement)\b", question))


def mentions_amazing_grace_progression(question: str) -> bool:
    return bool("amazing grace" in question and re.search(r"\b(?:chord progression|progression|chords|harmony)\b", question))


def mentions_original_style_lick(question: str) -> bool:
    return bool(re.search(r"\boriginal\b", question) and re.search(r"\b(?:lick|exercise|phrase)\b", question))


def mentions_every_pack_a_seat(question: str) -> bool:
    return bool(
        ("pack-a-seat" in question or "pack a seat" in question or "pack seat" in question)
        and ("every" in question or "all" in question or "only" in question)
        and ("steeler" in question or "steeler’s choice" in question or "steelers choice" in question)
    )


def mentions_changer_oil(question: str) -> bool:
    return bool(("oil" in question or "lubricat" in question) and ("changer" in question or "pedal steel" in question or "steel guitar" in question))


def mentions_finger_picks(question: str) -> bool:
    return bool(("finger pick" in question or "fingerpick" in question or "picks" in question) and ("buy" in question or "best" in question or "recommend" in question))


def mentions_play_without_finger_picks(question: str) -> bool:
    return bool(
        re.search(r"\b(?:play|practice|pick)\b", question)
        and re.search(r"\bwithout\b", question)
        and re.search(r"\b(?:finger\s*picks?|fingerpicks?|picks?)\b", question)
    )


def mentions_airplane_travel(question: str) -> bool:
    return bool(("airplane" in question or "airline" in question or "fly" in question or "flight" in question) and ("steel" in question or "guitar" in question))


def mentions_pedal_rods(question: str) -> bool:
    return bool(("pedal rod" in question or "pedal rods" in question) and ("broke" in question or "broken" in question or "new ones" in question or "replace" in question or "get" in question))


def mentions_shobud_emmons(question: str) -> bool:
    return bool(("sho-bud" in question or "shobud" in question) and "emmons" in question)


def mentions_company_status(question: str) -> bool:
    return bool(
        "emmons guitar" in question
        and ("business" in question or "still" in question or "today" in question)
        and not mentions_player_brand_usage(question)
    )


def mentions_player_brand_usage(question: str) -> bool:
    return bool(
        re.search(r"\bwho\s+(?:plays?|uses?)\s+(?:an?\s+)?[a-z0-9-]+(?:\s+guitars?)?", question)
        or re.search(r"\bwhich\s+(?:players?|people|pros|steel players?)\s+(?:play|use)\s+[a-z0-9-]+", question)
    )


def brand_from_player_usage_question(question: str) -> str:
    for brand in ("Emmons", "Mullen", "MSA", "Sho-Bud", "ZumSteel", "Carter", "GFI", "Sierra"):
        if brand.lower() in question:
            return brand
    match = re.search(r"\b(?:plays?|uses?)\s+(?:an?\s+)?([a-z0-9-]+)", question)
    return match.group(1).title() if match else "that brand"


def mentions_vendor_buying(question: str) -> bool:
    return bool(
        re.search(r"\bwhere\s+can\s+i\s+buy\b", question)
        or re.search(r"\bwhat\s+brands\s+make\b", question)
        or (("steel bar" in question or "slide bar" in question or "tone bar" in question) and "buy" in question)
    )


def mentions_mullen_msa_comparison(question: str) -> bool:
    return bool("mullen" in question and "msa" in question and re.search(r"\b(?:better|or|vs|versus|buy|compare|difference)\b", question))


def mentions_generic_brand_comparison(question: str) -> bool:
    brands = compared_brands(question)
    return len(brands) >= 2 and bool(re.search(r"\b(?:better|difference|compare|vs|versus|or|than|buy)\b", question))


def compared_brands(question: str) -> list[str]:
    found = re.findall(r"\b(Mullen|MSA|Emmons|Sho-Bud|Shobud|ZumSteel|Carter|GFI|Sierra)\b", question, re.I)
    brands: list[str] = []
    for brand in found:
        canonical = {"msa": "MSA", "shobud": "Sho-Bud"}.get(brand.lower(), brand[0].upper() + brand[1:])
        if canonical.lower() not in {item.lower() for item in brands}:
            brands.append(canonical)
    return brands


def mentions_benado_steel_dream_definition(question: str) -> bool:
    return "benado" in question and "steel dream" in question and re.search(r"\bwhat\s+is\b", question) and not mentions_benado_steel_dream_value(question)


def mentions_benado_steel_dream_value(question: str) -> bool:
    return bool("benado" in question and "steel dream" in question and re.search(r"\b(?:worth|money|value|should\s+i\s+buy)\b", question))


def mentions_steel_string_buying(question: str) -> bool:
    return bool(("strings" in question or "string set" in question) and "e9" in question and ("buy" in question or "should" in question))


def mentions_neck_choice(question: str) -> bool:
    return bool(
        ("single-neck" in question or "double-neck" in question or "s-10" in question or "sd-10" in question or "d-10" in question)
        and ("buy" in question or "should" in question or "choose" in question)
    )


def mentions_generic_product_command(question: str) -> bool:
    return bool(re.search(r"\bsay\s+every\s+product\s+is\s+worth\s+buying\b", question))


def source_proves_telonics_slide_bar(sources: list[dict]) -> bool:
    for source in sources:
        text = normalize(f"{source.get('thread_title') or ''} {source.get('excerpt') or ''}")
        if re.search(r"\btelonics\b.*\b(?:made|makes|built|builds|manufactured|manufactures)\b.*\bslide\s+bar\b", text):
            return True
    return False


def retrieval_looks_weak_for_curated(question: str, curated: CuratedAnswer, sources: list[dict]) -> bool:
    if not sources:
        return True
    if curated.intent == "yes_no_source_check":
        return True
    q_terms = {term for term in re.findall(r"[a-z0-9+-]+", normalize(question)) if len(term) > 3}
    if not q_terms:
        return False
    source_text = normalize(" ".join(f"{source.get('thread_title') or ''} {source.get('excerpt') or ''}" for source in sources[:3]))
    overlap = q_terms & set(re.findall(r"[a-z0-9+-]+", source_text))
    return len(overlap) < 2
