"""Small curated answer layer for high-confidence steel-guitar questions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pocketsteel.basic_chord_answers import (
    basic_chord_theory_answer_for_question,
    chord_change_answer_for_question,
    sus_chord_usage_answer_for_question,
)
from pocketsteel.curated_source_registry import slide_bar_vendor_bullets
from pocketsteel.fretboard_examples import (
    chord_concept_answer_for_question,
    chord_symbol_guardrail_answer_for_question,
    display_major_key_for_request,
    e_lower_578_b9_answer_for_question,
    e_lower_578_answer_for_question,
    e_lower_grip_answer_for_question,
    e_lower_grip_usage_answer_for_question,
    function_chord_answer_for_question,
    functional_pocket_answer_for_question,
    get_e9_major_chord_positions,
    generic_chord_concept_answer_for_question,
    major_chord_location_request_for_question,
    minor_chord_answer_for_question,
    multi_chord_answer_for_question,
    rootless_chord_quality_answer_for_question,
    chord_quality_definition_lines,
    unsupported_chord_location_request_for_question,
)
from pocketsteel.steel_rules import answer_from_rules


CuratedConfidence = Literal["curated_high", "curated_medium", "rag_only"]
IntentMode = Literal[
    "instrument_visual",
    "scope_guardrail",
    "factual_biography",
    "sensitive_personal_attribute",
    "style_how_to",
    "safety_adjacent",
    "teach_me_something",
    "movement_request",
    "progression_intro_request",
    "pocket_request",
    "lick_request",
    "vague_learning_request",
    "frustrated_learning_request",
    "everyday_context",
    "technique_coach",
    "tone_coach",
    "practice_plan",
    "fretboard_concept",
    "movement_from_position",
    "missing_context_clarifier",
    "copedent_mismatch_guardrail",
    "gear_advice",
    "gig_advice",
    "forum_wisdom",
    "lesson_navigation",
    "tab_explainer",
    "history_player_context",
    "unknown_low_confidence",
]


@dataclass(frozen=True)
class CuratedAnswer:
    intent: str
    answer: str
    confidence: CuratedConfidence
    source_url: str | None = None


WEAK_RETRIEVAL_WARNING = "curated answer used; source support was weak"
CURATED_FACT_WEAK_WARNING = "curated fact used; source support weak"

PLAYER_BIOS = {
    "buddy emmons": (
        "Buddy Emmons was one of the most influential pedal steel guitarists in the instrument’s history. "
        "He is known for brilliant E9 and C6 playing, adventurous technique, and major contributions as both a player and a builder/designer influence. "
        "For many players, his recordings and ideas are central reference points for modern pedal steel."
    ),
    "lloyd green": (
        "Lloyd Green is one of the most influential pedal steel guitarists, especially associated with classic Nashville/session steel guitar. "
        "He is known for tasteful, melodic E9 playing, precise phrasing, and major recorded work in country music."
    ),
    "paul franklin": (
        "Paul Franklin is a major modern pedal steel guitarist and session player. "
        "He is known for highly polished E9 and C6 playing, broad Nashville recording work, and a teaching influence on modern pedal-steel technique."
    ),
    "jimmy day": (
        "Jimmy Day was an important pedal steel guitarist closely associated with classic country steel. "
        "He is known for expressive phrasing, touch, and recorded work that helped define the emotional vocabulary of the instrument."
    ),
    "ralph mooney": (
        "Ralph Mooney was an influential pedal steel guitarist known for a driving, bright West Coast country sound. "
        "His playing helped shape the Bakersfield side of pedal steel and remains a reference for rhythmic, vocal-like E9 phrasing."
    ),
    "curly chalker": (
        "Curly Chalker was a major steel guitarist known especially for powerful C6 playing, jazz harmony, and big chordal command. "
        "He is often cited by players for his technical authority, musical imagination, and distinctive tone."
    ),
    "john hughey": (
        "John Hughey was a pedal steel guitarist known for lyrical, singing E9 playing and emotional ballad work. "
        "Many players associate him with smooth sustain, expressive slides, and a highly vocal approach to the instrument."
    ),
    "tom brumley": (
        "Tom Brumley was an influential pedal steel guitarist best known for clean, memorable country steel parts. "
        "His playing is often cited for tone, restraint, melodic clarity, and its influence on classic country pedal steel."
    ),
    "maurice anderson": (
        "Maurice Anderson, often known as “Reece” Anderson, was a major steel guitarist and an important builder/player figure associated with MSA. "
        "He is known for advanced musicianship, jazz-influenced steel playing, and his role in the development and visibility of MSA guitars."
    ),
    "reece anderson": (
        "Reece Anderson, also known as Maurice “Reece” Anderson, was a major steel guitarist and an important builder/player figure associated with MSA. "
        "He is known for advanced musicianship, jazz-influenced steel playing, and his role in the development and visibility of MSA guitars."
    ),
    "sarah jory": (
        "Sarah Jory is a respected steel guitarist known for strong technique, showmanship, and modern country/steel-guitar performance. "
        "She is often mentioned as an example of a high-level contemporary player with a commanding stage and recording presence."
    ),
    "doug jernigan": (
        "Doug Jernigan is a highly respected pedal steel guitarist known for speed, precision, and strong jazz and country command. "
        "Players often cite him for advanced technique, clean execution, and broad musical vocabulary."
    ),
    "weldon myrick": (
        "Weldon Myrick was an important Nashville pedal steel guitarist and session player. "
        "He is known for tasteful recorded work, strong E9 musicianship, and his place among the classic generation of country steel players."
    ),
    "hal rugg": (
        "Hal Rugg was a major pedal steel guitarist and Nashville session player. "
        "He is known for clean, authoritative playing, strong C6 and E9 musicianship, and influential work in classic country settings."
    ),
    "pete drake": (
        "Pete Drake was a steel guitarist and producer associated with major Nashville recording work. "
        "He is known for memorable session playing and for popularizing vocal/talk-box-style steel sounds in addition to conventional steel parts."
    ),
}


def visual_fretboard_curated_answer(question: str) -> CuratedAnswer | None:
    q = normalize(question)
    practical_direct_answer = direct_yes_no_practical_answer(q)
    if practical_direct_answer is not None:
        return practical_direct_answer
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
    major_request = major_chord_location_request_for_question(question)
    if major_request is not None:
        major_key = major_request.normalized_key
        display_key = display_major_key_for_request(major_request)
        positions = get_e9_major_chord_positions(major_key)
        open_position = next(position for position in positions if position["role"] == "Open position")
        af_position = next(position for position in positions if position["role"] == "A+F position")
        ab_position = next(position for position in positions if position["role"] == "A+B position")
        wants_across_fretboard = "across" in q and "fretboard" in q
        wants_ab_specific = re.search(r"\b(?:a\s*\+\s*b|a\s+and\s+b)\b", q) is not None
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
        if major_request.requested_root != display_key:
            lines.extend(
                [
                    f"{major_request.requested_root} is the same pitch as {display_key}. On E9, think of it as a {display_key} major chord.",
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
                "- E-lower grips are more context-dependent; the selector may show pitch-validated 5-7-8, 7-8-10, 4-5-7, and 1-4-5 positions when they truly spell the chord or a useful partial/rootless color.",
                "",
                "Common grips to try are 3-4-5, 4-5-6, 5-6-8, 5-7-8 when it validates, and 6-8-10. The fretboard selector may include alternate octaves, grip variants, and lever pockets, so treat these as several useful places rather than every possible position.",
            ]
        )
        if wants_across_fretboard and (lower_ab_position is not None or e_lower_position is not None):
            lines.extend(["", "Useful across-the-fretboard alternates:"])
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


def unsupported_chord_position_curated_answer(question: str) -> CuratedAnswer | None:
    unsupported_request = unsupported_chord_location_request_for_question(question)
    if unsupported_request is None:
        return None
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
    mode = intent_mode_for_question(q)
    if mode == "scope_guardrail":
        return CuratedAnswer(
            intent="scope_guardrail",
            confidence="curated_high",
            answer=(
                "That request is outside Steel Guitar RAG’s scope, and it would be too large to display usefully. "
                "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, or steel-guitar forum wisdom."
            ),
        )
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
    if mode == "lick_request":
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
                    "Try this classic-country E9 move: use a simple I-to-IV sound at one fret, then answer it with space.\n\n"
                    "Drill:\n"
                    "- At the 3rd fret, pick strings 4-5-6 with no pedals for G.\n"
                    "- Press A+B at the same fret for C, keeping the bar still.\n"
                    "- Release A+B cleanly back to G, then leave a beat of silence.\n"
                    "- Repeat the same idea on strings 3-4-5 and 5-6-8.\n\n"
                    "What to listen for: even pedal timing, clean blocking after each grip, and a relaxed answer-the-singer feel instead of a busy lick."
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
                intent="forum_wisdom",
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
                "I don’t know the current roster from the information I have. "
                "For the current touring or recording lineup, check official tour credits, album/session credits, or the artist’s current band listings. "
                "I can also help interpret any credits you find."
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
                "I can help you learn the approach, but I will not dump a full protected melody or note-for-note tab by default.\n\n"
                "Guardrail-friendly way to work on it:\n"
                "- Think in intervals from the key center instead of memorizing fret numbers first.\n"
                "- Pick a key and map the melody notes to nearby E9 positions.\n"
                "- Work one short phrase at a time, then add simple harmony or pads underneath.\n"
                "- If you provide the notes, a short excerpt, or your own tab attempt, I can help map it to strings, frets, pedals, and levers."
            ),
        )

    if mentions_generic_song_learning(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "Tell me the song, key, tuning, and what you want to work on, and I can map an approach for pedal steel.\n\n"
                "A practical starter option:\n"
                "- Use a public-domain tune such as “Amazing Grace” in G.\n"
                "- Start with G at the 3rd fret open.\n"
                "- Move to C at the 3rd fret with A+B.\n"
                "- Move to D at the 5th fret with A+B.\n"
                "- Resolve to G at the 6th fret with A pedal + F lever.\n\n"
                "I can discuss style, chord movement, positions, tone, and practice strategy. I do not provide full note-for-note copyrighted tab or full copyrighted lyrics by default."
            ),
        )

    if mentions_player_brand_usage(q):
        brand = brand_from_player_usage_question(q)
        return CuratedAnswer(
            intent="player_brand_usage",
            confidence="curated_medium",
            answer=(
                f"I do not have a strong, current roster of players using {brand} guitars today from the information I have.\n\n"
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
                "I do not provide full copyrighted lyrics by default.\n\n"
                "What I can do instead:\n"
                "- I can summarize the song’s theme or mood.\n"
                "- I can discuss how to arrange it for pedal steel.\n"
                "- I can suggest chord/position strategy and tone ideas.\n"
                "- I can work from a short excerpt or chart you provide."
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
                "I can help build an arrangement from your chord chart or a short user-provided excerpt, but I will not dump a full note-for-note copyrighted tab by default."
            ),
        )

    if mentions_panhandle_rag_tab(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "I can help you work toward “Panhandle Rag,” but I will not dump a full note-for-note copyrighted tab by default.\n\n"
                "Learning approach:\n"
                "- Start by learning the chord path and where the melody sits against each chord.\n"
                "- Practice a bright Western-swing feel with clean blocking and a steady bounce.\n"
                "- Use small position shifts and harmonized grips instead of trying to memorize a whole arrangement at once.\n"
                "- Build your own version phrase by phrase, or give me a short excerpt you are working from and I can help transform it.\n\n"
                "If you want a safe tab exercise now, use an original Western-swing-style G-C-D-G phrase instead."
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

    if mentions_original_style_lick(q):
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

    if mentions_random_tab_request(q):
        return CuratedAnswer(
            intent="song_learning",
            confidence="curated_high",
            answer=(
                "For a random tab request, I’ll choose a copyright-safe path instead of sending you to random emails or questionable tab sources.\n\n"
                "Good options:\n"
                "- Name a public-domain tune such as Amazing Grace or Silent Night and I can help build a simple steel arrangement.\n"
                "- Describe the chord movement you want and I can make an original exercise around it.\n"
                "- For a random default, use this public-domain-style chord path: G to C to D to G.\n\n"
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
                "The information I have here does not show strong support for Telonics slide bars, "
                "but curated/user-known information says Telonics has made at least some slide bars. "
                "Treat that as curated knowledge rather than something proven by the listed sources."
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
            confidence="curated_medium",
            answer=(
                "Players tend to treat Steel King settings as starting points, then adjust for the room, pickup, and speaker height.\n\n"
                "Likely causes or common settings:\n"
                "- Keep the EQ moderate first rather than extreme.\n"
                "- Set volume at gig level before judging treble or presence.\n"
                "- If the sound is thin, reduce brightness and pick slightly farther from the changer.\n"
                "- If the sound is muddy, lower bass before adding treble.\n\n"
                "Diagnostic steps:\n"
                "- Start flat or near the middle, then change one EQ control at a time.\n"
                "- Listen from where the audience or mic hears the amp, not only from above the speaker.\n"
                "- Save forum settings as reference notes, not as guaranteed settings for every guitar.\n\n"
                "Safety/caution: if noise, heat, burning smell, or electrical problems are part of the issue, stop adjusting settings and have the amp checked."
            ),
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
    return re.sub(r"\s+", " ", text or "").strip().lower()


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


def _mentions_pocket_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:show\s+me|give\s+me|teach\s+me|specific|one)\b", question)
        and re.search(r"\bpocket\b", question)
    )


def _mentions_lick_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:give\s+me|show\s+me|teach\s+me|example|one|just\s+one)\b", question)
        and re.search(r"\blick\b", question)
        and re.search(r"\b(?:steel|pedal\s+steel|steel\s+guitar|e9)\b", question)
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
    return bool(
        re.search(r"\b(?:where|show|what frets|how do i play|how do i make|what does|what notes|what makes)\b", question)
        and re.search(r"\b(?:chords?|major|minor|fret|frets|positions?|e9|strings?|grips?|pedals?|levers?|vi|6m|b9|e lowered|e-lower)\b", question)
    )


def _mentions_gear_advice_intent(question: str) -> bool:
    return bool(
        _mentions_stroboplus_power_problem(question)
        or _mentions_delay_volume_pedal_order(question)
        or _mentions_battery_tuner_live(question)
        or re.search(r"\b(?:amp\s+hums?|amp\s+buzz|hum\s+until\s+i\s+touch|buzz\s+until\s+i\s+touch)\b", question)
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
    return bool(
        re.search(r"\bsteel\s+king\s+settings?\b", question)
        and re.search(r"\b(?:what\s+do\s+players\s+say|common|settings?|starting|eq|fender)\b", question)
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
