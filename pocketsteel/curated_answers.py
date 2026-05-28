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
CURATED_FACT_WEAK_WARNING = "curated fact used; source support weak"


def lookup_curated_answer(question: str, sources: list[dict]) -> CuratedAnswer | None:
    q = normalize(question)

    if mentions_player_brand_usage(q):
        brand = brand_from_player_usage_question(q)
        return CuratedAnswer(
            intent="player_brand_usage",
            confidence="curated_medium",
            answer=(
                f"I do not have a strong, current, source-backed roster of players using {brand} guitars today.\n\n"
                "Use the source cards as leads, but treat forum mentions as historical or source-specific unless the source clearly says a player currently uses that brand. "
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
                    "For pedal rods, start with the guitar maker, a dealer for that brand, or a steel-guitar parts supplier/builder.\n\n"
                    "Before ordering, match:\n"
                    "- rod length\n"
                    "- thread size\n"
                    "- hook/connector style\n"
                    "- pedal-rack and bellcrank hardware\n\n"
                    "Used SGF classifieds can help, but matching the hardware matters more than finding any random rod."
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
                "Use the source cards for exact version details, because forum posts may refer to different Benado models or revisions."
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
                "For church, make the steel supportive first and impressive second.\n\n"
                "Preparation checklist:\n"
                "- Learn the hymn or song changes clearly before adding fills.\n"
                "- Keep intros, endings, and transitions simple enough for the singers to trust.\n"
                "- Use swells, pads, and quiet fills behind vocals instead of stepping on the melody.\n"
                "- Rehearse volume-pedal control so your entrances are smooth.\n"
                "- Know when not to play; space is part of the arrangement."
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

    if ("tablature" in q or "tab" in q) and ("random song" in q or "song" in q):
        return CuratedAnswer(
            intent="tab_copyright",
            confidence="curated_high",
            answer=(
                "I can’t provide copyrighted song tablature by default or send you to random people’s emails.\n\n"
                "I can help in safer ways:\n"
                "- Make a short original E9 exercise in the style you want.\n"
                "- Explain the chord movement or grips for a lick you describe.\n"
                "- Work from a public-domain tune if you name one.\n\n"
                "Original mini-exercise: at the 3rd fret, pick strings 4-5-6, press A+B, release cleanly, then move to the 6th fret with A+F and pick 4-5-6 again."
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
                "Use the source cards as leads, and treat any forum mentions as source-specific rather than a complete endorsement list."
            ),
        )

    if "telonics" in q and "slide" in q and "bar" in q:
        if source_proves_telonics_slide_bar(sources):
            return None
        return CuratedAnswer(
            intent="curated_fact_source_check",
            confidence="curated_medium",
            answer=(
                "The current corpus retrieval does not show strong source support for Telonics slide bars, "
                "but curated/user-known information says Telonics has made at least some slide bars. "
                "Treat that as curated knowledge rather than corpus-supported evidence."
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
