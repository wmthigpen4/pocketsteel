"""Small curated answer layer for high-confidence steel-guitar questions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


CuratedConfidence = Literal["curated_high", "curated_medium", "rag_only"]


@dataclass(frozen=True)
class CuratedAnswer:
    intent: str
    answer: str
    confidence: CuratedConfidence
    source_url: str | None = None


WEAK_RETRIEVAL_WARNING = "curated answer used; retrieved sources were weak"


def lookup_curated_answer(question: str, sources: list[dict]) -> CuratedAnswer | None:
    q = normalize(question)

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

    if "maurice anderson" in q or "reece anderson" in q:
        return CuratedAnswer(
            intent="entity_definition",
            confidence="curated_high",
            answer="Maurice “Reece” Anderson was a major steel guitarist and an important builder/player figure associated with MSA.",
        )

    if "lloyd green" in q and re.search(r"\bwho\s+is\b|\btell\s+me\s+about\b|\bwhat\s+is\b", q):
        return CuratedAnswer(
            intent="entity_definition",
            confidence="curated_high",
            answer=(
                "Lloyd Green is one of the most influential pedal steel guitarists, especially associated with classic Nashville/session steel guitar. "
                "He is known for tasteful, melodic E9 playing and major recorded work in country music."
            ),
        )

    if "pack-a-seat" in q or "pack a seat" in q or "pack seat" in q:
        return CuratedAnswer(
            intent="entity_definition",
            confidence="curated_high",
            answer=(
                "A pack-a-seat is a steel-guitar seat/storage box.\n"
                "Steeler’s Choice is a known pack-a-seat maker."
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

    if "telonics" in q and "slide" in q and "bar" in q:
        if source_proves_telonics_slide_bar(sources):
            return None
        return CuratedAnswer(
            intent="yes_no_source_check",
            confidence="curated_medium",
            answer="I do not see a strong source match showing that Telonics made a slide bar.",
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

    if "wound" in q and ("6th" in q or "sixth" in q or "string 6" in q):
        return CuratedAnswer(
            intent="copedent_fretboard",
            confidence="curated_high",
            answer=(
                "A wound 6th string is a tradeoff. Some players like the sound and feel, and some feel it can make cabinet-drop behavior feel better. "
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

    return None


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def mentions_g_chord_sixth_fret(question: str) -> bool:
    return bool(re.search(r"\bg\s+chord\b", question) and re.search(r"\b6(?:th)?\s+fret\b|\bsixth\s+fret\b", question))


def mentions_g_chord_across_guitar(question: str) -> bool:
    return bool(re.search(r"\bg\s+chord\b", question) and ("across the guitar" in question or "across the neck" in question))


def mentions_bc_second_fret(question: str) -> bool:
    return bool(("b&c" in question or "b+c" in question) and re.search(r"\b2(?:nd)?\s+fret\b|\bsecond\s+fret\b", question))


def mentions_practice_plan(question: str) -> bool:
    return bool(
        "what should i practice" in question
        or "what should i work on" in question
        or "give me a practice plan" in question
        or "practice routine" in question
        or "practice session" in question
    )


def mentions_changer_oil(question: str) -> bool:
    return bool(("oil" in question or "lubricat" in question) and ("changer" in question or "pedal steel" in question or "steel guitar" in question))


def mentions_finger_picks(question: str) -> bool:
    return bool(("finger pick" in question or "fingerpick" in question or "picks" in question) and ("buy" in question or "best" in question or "recommend" in question))


def mentions_airplane_travel(question: str) -> bool:
    return bool(("airplane" in question or "airline" in question or "fly" in question or "flight" in question) and ("steel" in question or "guitar" in question))


def mentions_pedal_rods(question: str) -> bool:
    return bool(("pedal rod" in question or "pedal rods" in question) and ("broke" in question or "broken" in question or "new ones" in question or "replace" in question or "get" in question))


def mentions_shobud_emmons(question: str) -> bool:
    return bool(("sho-bud" in question or "shobud" in question) and "emmons" in question)


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
