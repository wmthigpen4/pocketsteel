"""Reusable answer contracts for The Turnaround answer generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


COPYRIGHT_AWARE_SONG_HELP_POLICY = (
    "The assistant may teach songs, artist solos, commercial recordings, and complete arrangements. Copyright status "
    "alone is never a refusal reason. Preserve artist, song, recording/version, source, and section information when "
    "available; label the result as a transcription, E9 adaptation, teaching simplification, or original exercise; "
    "and never claim exactness without identified or user-supplied source material. Teach long material in numbered sections."
)


@dataclass(frozen=True)
class AnswerContract:
    intent: str
    required_answer_elements: tuple[tuple[str, str], ...] = ()
    required_section_labels: tuple[str, ...] = ()
    forbidden_answer_patterns: tuple[tuple[str, str], ...] = ()
    default_section_labels: tuple[str, ...] = ()
    requires_direct_first_sentence: bool = False
    direct_first_sentence_pattern: str = ""
    curated_answer_may_lead: bool = True
    rag_excerpts_may_appear_in_answer_body: bool = False
    source_context_in_source_cards_only: bool = True
    fallback_answer: str = (
        "I don’t have enough reliable information to answer that confidently. "
        "Try adding the song, key, tuning, brand, or exact part you mean so I can narrow the source match."
    )


@dataclass(frozen=True)
class ContractValidation:
    intent: str
    answer: str
    violations: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.violations


COMMON_FORBIDDEN: tuple[tuple[str, str], ...] = (
    ("internal source-backed fallback language", r"\bThe cleanest source-backed answer\b|\bHere is the safest answer I can support from the retrieved material\b|\bI found a few related practical points\b|\bmatch is limited\b|\bretrieved material\b|\bsource cards as supporting evidence\b|\bUseful distilled points\b|\bUseful source-backed points\b"),
    ("raw link removed marker", r"\[link removed\]"),
    ("raw Top boilerplate", r"^\s*Top\b|\sTop\s"),
    ("raw link-share fragment", r"\bsp=sharing\b"),
    ("raw email address", r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b"),
    ("raw e-mail contact", r"\be-?mail\s+"),
    ("raw sales/contact snippet", r"\b(?:PayPal|order\s+(?:form|page|link|online|through))\b"),
    ("source context heading", r"\b(?:Source context|Forum-source context|What multiple sources support)\b"),
    ("orphan Practical answer heading", r"(?m)^\s*Practical answer\s*:?\s*$"),
    ("duplicate answer headings", r"(?s)(?m)^\s*Answer\s*:?\s*$.*^\s*Practical answer\s*:?\s*$"),
    ("forum question fragment", r"\b(?:Does anyone know|Has anyone compared|I am looking for tablature)\b"),
    ("forum chatter fragment", r"\b(?:which someone else is probably playing|I may be learning)\b"),
    ("raw SGF body fragment", r"\b(?:I know when I first started|Can someone please tell me|lolol Thank God|you desire more information|have a couple of students|beyond simply facilitating|Further he went on to state|You can also build a 7 string instrument|It seems that playing steel guitar has a lot in common|I found this in limited source support|treat it as a clue rather than consensus)\b"),
    ("inline citation marker", r"\[\d+\]"),
    ("obvious source typo", r"\b(?:tje|teh)\b"),
)


CONTRACTS: dict[str, AnswerContract] = {
    "practice_plan": AnswerContract(
        intent="practice_plan",
        required_answer_elements=(
            ("practice plan or routine", r"\b(?:practice|plan|routine|minutes?|minute)\b"),
            ("steel-specific work", r"\b(?:grips?|pedals?|levers?|bar|blocking|volume-pedal|E9|fret)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("ranking language", r"\bRankings are subjective\b"),),
        default_section_labels=("plan",),
        fallback_answer=(
            "Tonight, use a short steel-specific practice plan: warm up on common grips, move one chord through two or three E9 positions, "
            "then spend a few minutes on blocking, bar movement, and volume-pedal control."
        ),
    ),
    "technique_improvement": AnswerContract(
        intent="technique_improvement",
        required_answer_elements=(
            ("musical feel guidance", r"\b(?:phrasing|timing|space|bar control|vibrato|blocking|volume[- ]pedal|dynamics|singer|backing track)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("live sound-guy chatter", r"\b(?:tell the sound guy|bite ya|road cases?|speakers?\s+stay\s+inside|mics?|move some air)\b"),
            ("ranking language", r"\bRankings are subjective\b"),
        ),
        default_section_labels=("practice it this way",),
        fallback_answer=(
            "To sound less mechanical, work on phrasing and timing before adding more notes.\n\n"
            "Practice it this way:\n"
            "- Play fewer fills and leave space after the singer or backing-track phrase.\n"
            "- Use bar control and slow vibrato only after the note is in tune.\n"
            "- Block cleanly so notes end on purpose.\n"
            "- Use the volume pedal for dynamics and sustain, not constant motion."
        ),
    ),
    "diagnostic_troubleshooting": AnswerContract(
        intent="diagnostic_troubleshooting",
        required_answer_elements=(
            ("likely causes", r"\b(?:likely causes|suspect|cause|comes from|appears only)\b"),
            ("isolation path", r"\b(?:nothing plugged in|direct|signal chain|cable|volume pedal|effects?|one at a time)\b"),
            ("diagnostic steps", r"\b(?:step|check|test|isolate|swap|add)\b"),
            ("safety caution", r"\b(?:safety|tech|qualified|amp|electrical|power|tube|electronics)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("answer opens as forum question only", r"^\s*Does\s+the\b"),
            ("raw forum question as answer", r"\bDoes the amp buzz with nothing connected\b"),
        ),
        required_section_labels=("Likely causes", "Diagnostic path", "Safety"),
        default_section_labels=("diagnostic path", "safety"),
        fallback_answer=(
            "Start by isolating the buzz: turn the amp on with nothing plugged in, then test guitar to amp direct, "
            "swap the cable, add the volume pedal, and add effects one at a time. If the buzz is present with nothing plugged in, "
            "suspect the amp, power, tubes, or electronics and use a qualified tech for electrical work."
        ),
    ),
    "tone_touch": AnswerContract(
        intent="tone_touch",
        required_answer_elements=(
            ("physical touch guidance", r"\b(?:right-hand|pick force|pick attack|touch|blocking|bar|vibrato|volume pedal|dynamics)\b"),
            ("concrete practice action", r"\b(?:practice|try|play|pick|reduce|move|record)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("vague amp-only answer", r"\bwith amp settings you can soften the sound\b"),
            ("live sound-guy chatter", r"\b(?:tell the sound guy|bite ya|road cases?|speakers?\s+stay\s+inside|mics?|move some air)\b"),
        ),
        default_section_labels=("touch checklist",),
        fallback_answer=(
            "To soften your attack, start with your hands before hiding it with gear: lighten right-hand pick force, "
            "shape the note with the volume pedal after the pick, clean up blocking, and add vibrato only after the pitch centers."
        ),
    ),
    "practical_concept_explanation": AnswerContract(
        intent="practical_concept_explanation",
        required_answer_elements=(
            ("practical concept definition", r"\b(?:pocket|zone|position|area)\b"),
            ("pedal-steel location details", r"\b(?:fret|strings?|pedals?|levers?|neck)\b"),
            ("practice application", r"\b(?:practice|licks?|I, IV, and V|home position|move)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("source dump fallback", r"\b(?:retrieved material|Useful distilled points|source cards as supporting evidence)\b"),
            ("private profile leakage", r"\b(?:Your private profile|Open tuning|Pedals\s*$|Levers\s*$)\b"),
        ),
        default_section_labels=("how to practice",),
    ),
    "right_hand_technique": AnswerContract(
        intent="right_hand_technique",
        required_answer_elements=(
            ("right-hand pick context", r"\b(?:thumb pick|fingerpicks?|finger picks?|ring-finger|fourth|picks?)\b"),
            ("practical pick reason", r"\b(?:volume|attack|clarity|string separation|consistency|tone|four-note|grips?|wider chords?|C6|extended)\b"),
            ("optional or adjustment caveat", r"\b(?:optional|not required|do not need|awkward|adjustment|beginner|standard pedal steel)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("source dump fallback", r"\b(?:retrieved material|Useful distilled points|source cards as supporting evidence)\b"),
            ("private profile leakage", r"\b(?:Your private profile|Open tuning|Pedals\s*$|Levers\s*$)\b"),
        ),
    ),
    "gear_product_explanation": AnswerContract(
        intent="gear_product_explanation",
        required_answer_elements=(
            ("product identity", r"\b(?:Peterson|StroboPlus|strobe-style|tuner|tuning tool)\b"),
            ("why steel players care", r"\b(?:sweetened|temperament|pedal|lever|offset|precise)\b"),
            ("model caveat", r"\b(?:check|model|manual|specs?|features)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("sales/contact fragment", r"\b(?:PayPal|order\s+(?:form|page|link|online|through)|call\s+me|contact)\b"),
            ("private profile leakage", r"\b(?:Your private profile|Open tuning|Pedals\s*$|Levers\s*$)\b"),
        ),
    ),
    "gear_advice": AnswerContract(
        intent="gear_advice",
        required_answer_elements=(
            ("short practical answer", r"\bShort answer\b|\bstart with\b|\bpractical\b"),
            ("practical steps", r"\b(?:Practical steps|check|try|carry|use|start)\b"),
            ("before buying or changing check", r"\b(?:What to check|before buying|before changing|manual|model|signal chain|adapter|power|battery|volume pedal)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("anecdote as answer", r"\b(?:funny story|embarrass|blood|gore|injury|fell off|laughed)\b"),
            ("definition-only StroboPlus answer", r"^\s*A Peterson StroboPlus is\b"),
            ("raw forum fragment", r"\b(?:I couldn't agree more|tell the sound guy|with your middle finger|Mel Bay)\b"),
        ),
        default_section_labels=("short answer", "practical steps", "what to check"),
        fallback_answer=(
            "Short answer: start with the practical setup problem, then change one thing at a time.\n\n"
            "Practical steps:\n"
            "- Check the exact model, manual, power, cable, and signal-chain requirements.\n"
            "- Test the rig at gig volume before buying or changing anything.\n"
            "- Carry a simple backup for any gig-critical item."
        ),
    ),
    "gig_advice": AnswerContract(
        intent="gig_advice",
        required_answer_elements=(
            ("short practical answer", r"\bShort answer\b"),
            ("gig recovery steps", r"\b(?:stay calm|finish|set break|shift grips|positions|backup instrument|carry)\b"),
            ("gig kit or check", r"\b(?:spare strings|cutters|winder|tuner|light|kit|burrs|changer)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("joke or injury anecdote", r"\b(?:funny story|embarrass|blood|gore|injury|glass|bump)\b"),
            ("raw forum fragment", r"\b(?:I couldn't agree more|Top\s+I|with your middle finger)\b"),
        ),
        default_section_labels=("short answer", "practical steps", "what to check"),
        fallback_answer=(
            "Short answer: prepare for gig problems before they happen.\n\n"
            "Practical steps:\n"
            "- Stay calm and finish the song if possible.\n"
            "- Route around the missing note or faulty item until the set break.\n"
            "- Carry spare strings, cutters, a winder, tuner, and a small light."
        ),
    ),
    "forum_wisdom": AnswerContract(
        intent="forum_wisdom",
        required_answer_elements=(
            ("synthesized player takeaway", r"\b(?:players generally|players commonly|what players commonly|practical takeaway)\b"),
            ("practical advice", r"\b(?:carry|check|try|practice|replace|adapt|backup)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("raw anecdote or joke", r"\b(?:funny story|embarrass|blood|gore|injury|glass|bump)\b"),
            ("fragment-only forum quote", r"\b(?:Top\s+|I couldn't agree more|Can some of you possibly post)\b"),
        ),
        default_section_labels=("short answer", "practical takeaway"),
        curated_answer_may_lead=True,
        rag_excerpts_may_appear_in_answer_body=False,
        source_context_in_source_cards_only=True,
        fallback_answer=(
            "Short answer: treat forum discussion as a source of practical patterns, not as text to copy.\n\n"
            "Practical takeaway: look for what multiple players actually do, then apply the cleanest setup or practice step to your own guitar."
        ),
    ),
    "player_teacher_bio": AnswerContract(
        intent="player_teacher_bio",
        required_answer_elements=(
            ("identity", r"\b(?:was|is)\b.*\b(?:teacher|player|pedal steel)\b"),
            ("instructional role", r"\b(?:teacher|instructional|courses?|seminars?|workshops?)\b"),
            ("influence", r"\b(?:influenced|generations|legacy|helped many players)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("ranking template", r"\bRankings are subjective\b|\bA safe all-time starting list\b"),
            ("private profile leakage", r"\b(?:Your private profile|Open tuning|Pedals\s*$|Levers\s*$)\b"),
        ),
        requires_direct_first_sentence=True,
    ),
    "copedent_fretboard": AnswerContract(
        intent="copedent_fretboard",
        required_answer_elements=(
            ("what changes or provides", r"\b(?:raise|raises|lower|lowers|changes?|takes|string|gives|provides|note|positions?|available|places?|find)\b"),
            ("chord or interval result", r"\b(?:chord|interval|triad|dominant|major|minor|seventh|scale tone|color)\b"),
            ("fret/string/pedal example", r"\b(?:fret|pedal|lever|string|grip)\b"),
            ("practical use", r"\b(?:use|practical|players use|practice|connect|movement|try|common grips?)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
        default_section_labels=("direct answer", "why it works"),
        fallback_answer="On E9, answer copedent questions from the chord function first, then name the fret, strings, pedals, and levers only when those details are supported.",
    ),
    "equipment_recommendation": AnswerContract(
        intent="equipment_recommendation",
        required_answer_elements=(("selection guidance", r"\b(?:choose|compare|fit|try|buy|gauge|brand|condition)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("player ranking leakage", r"\b(?:Buddy Emmons|Jimmy Day|Paul Franklin|Tom Brumley)\b"),),
        default_section_labels=("what to compare",),
    ),
    "vendor_buying_guidance": AnswerContract(
        intent="vendor_buying_guidance",
        required_answer_elements=(
            ("curated sources or buying channels", r"\b(?:Steel Guitar Shopper|BJS Steel Guitar Bars|Jim Dunlop|dealer|vendor|retailer|shop|store|classifieds?|used market|maker|manufacturer|bar makers?)\b"),
            ("specs to check", r"\b(?:diameter|length|weight|material|thread|connector|compatib|size|gauge)\b"),
            ("current availability caveat", r"\b(?:check current availability|inventory|in stock)\b"),
        ),
        required_section_labels=("Best places to check", "What to choose"),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("generic product-value template", r"\bpositive owner/source impression\b|\bthat product\b"),
            ("random old forum vendor link", r"https?://(?:www\.)?steelguitarforum\.com/Forum\d+/HTML/"),
        ),
        default_section_labels=("what to check",),
        fallback_answer=(
            "Start with steel-guitar specialty dealers, reputable makers, music retailers, and the SGF classifieds or used market. "
            "Before buying, check the size, material, compatibility, and return policy."
        ),
    ),
    "product_value": AnswerContract(
        intent="product_value",
        required_answer_elements=(("conditional value judgment", r"\b(?:worth|value|price|buy|maybe|conditional|cost)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("old product-value boilerplate", r"\bpositive owner/source impression\b|\bI did not find strong negative evidence\b"),),
        default_section_labels=("worth it", "cautions"),
    ),
    "maintenance_safety": AnswerContract(
        intent="maintenance_safety",
        required_answer_elements=(("safety or caution", r"\b(?:caution|safety|avoid|sparingly|cleaner|solvent|qualified|tech)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
        default_section_labels=("caution",),
    ),
    "replacement_parts": AnswerContract(
        intent="replacement_parts",
        required_answer_elements=(("matching parts guidance", r"\b(?:match|measure|thread|length|connector|maker|dealer|supplier|parts)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
    ),
    "travel_transport": AnswerContract(
        intent="travel_transport",
        required_answer_elements=(("travel protection", r"\b(?:case|carry|check|airline|flight|protect|gate|inspection)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
    ),
    "brand_comparison": AnswerContract(
        intent="brand_comparison",
        required_answer_elements=(
            ("both brands", r"\b(?:Mullen|MSA|Emmons|Sho-Bud|ZumSteel|Carter|GFI|Sierra)\b.*\b(?:Mullen|MSA|Emmons|Sho-Bud|ZumSteel|Carter|GFI|Sierra)\b"),
            ("no universal winner", r"\b(?:no universal winner|depends|fit|condition|personal|specific guitars)\b"),
            ("mechanics comparison", r"\b(?:mechanics|mechanical|push-pull|all-pull|changer)\b"),
            ("support or parts comparison", r"\b(?:support|parts|builder|service)\b"),
            ("tone comparison", r"\b(?:tone|sound|sustain|clarity|warm)\b"),
            ("weight or ergonomics comparison", r"\b(?:weight|ergonomic|cabinet|case|carry)\b"),
            ("condition or setup caveat", r"\b(?:condition|setup|copedent|fit|budget)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("generic product-value template", r"\bpositive owner/source impression\b|\bthat product\b"),
            ("vendor links in comparison", r"https?://"),
        ),
        default_section_labels=("comparison",),
    ),
    "player_bio": AnswerContract(
        intent="player_bio",
        required_answer_elements=(
            ("identity", r"\b(?:is|was)\b.*\b(?:steel guitarist|pedal steel guitarist|player)\b"),
            ("why they matter", r"\b(?:influential|important|major|known for|associated with)\b"),
            ("style or contribution", r"\b(?:style|playing|technique|contribution|builder|designer|recorded work|session)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("ranking template", r"\bRankings are subjective\b|\bA safe all-time starting list\b"),),
        requires_direct_first_sentence=True,
        direct_first_sentence_pattern=r"\b(?:is|was)\b.*\b(?:steel guitarist|pedal steel guitarist|player)\b",
    ),
    "player_brand_usage": AnswerContract(
        intent="player_brand_usage",
        required_answer_elements=(("player usage or weak roster support", r"\b(?:players?|users?|roster|source-backed|currently uses|artist list)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("company-status-only answer", r"\bReSound’65\b"),),
        fallback_answer=(
            "I do not have a strong, current player roster for that brand from the information I have. "
            "Use any listed sources as leads and verify current users through official artist lists or recent credits."
        ),
    ),
    "subjective_ranking": AnswerContract(
        intent="subjective_ranking",
        required_answer_elements=(("subjective caveat", r"\b(?:subjective|starting list|not definitive|influence)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
    ),
    "entity_definition": AnswerContract(
        intent="entity_definition",
        required_answer_elements=(("definition shape", r"\b(?:is|was|stands for|known)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
    ),
    "current_company_status": AnswerContract(
        intent="current_company_status",
        required_answer_elements=(("current status", r"\b(?:operating|in business|official site|today|current)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("player-roster answer", r"\bartist list\b.*\broster\b"),),
    ),
    "performance_context_guidance": AnswerContract(
        intent="performance_context_guidance",
        required_answer_elements=(
            ("role in context", r"\b(?:support|vocals?|singer|band|context)\b"),
            ("restraint and dynamics", r"\b(?:swells?|pads?|fills?|space|dynamics|simple|restraint)\b"),
            ("preparation steps", r"\b(?:chart|form|intro|ending|transition|rehearse|practice)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("invented specific URL", r"https?://(?:www\.)?(?:youtube|youtu\.be)\."),),
        default_section_labels=("preparation checklist",),
        fallback_answer=(
            "For a church or worship setting, support the vocals first: learn the chart and form, use simple pads and fills, "
            "rehearse intros/endings, and practice with slow worship-style backing tracks without inventing specific links."
        ),
    ),
    "song_learning": AnswerContract(
        intent="song_learning",
        required_answer_elements=(
            ("song, recording, source, section, key, or tuning path", r"\b(?:song|recording|source|version|section|key|tuning|notes|tab|chart)\b"),
            ("teaching or arrangement path", r"\b(?:teach|lesson|transcription|adaptation|arrangement|simplification|exercise|practice)\b"),
            ("accuracy or source clarification", r"\b(?:exact|approximate|interpretive|source|recording|version|provide|send|upload|paste)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("random contact", r"\b(?:email|e-mail)\b"),
            ("blanket copyrighted-material refusal", r"\b(?:cannot|can't|can’t|do not|won't)\s+(?:discuss|talk about|help with|provide|transcribe|arrange|teach)\b[^.\n]*\bcopyrighted\b"),
            ("copyright status used as refusal", r"\b(?:copyright|copyrighted)\b[^.\n]{0,80}\b(?:refus|block|cannot|can't|can’t|won't)\b"),
        ),
        default_section_labels=("teaching approach", "section"),
        fallback_answer=(
            COPYRIGHT_AWARE_SONG_HELP_POLICY
        ),
    ),
    "current_roster": AnswerContract(
        intent="current_roster",
        required_answer_elements=(
            ("current information limitation", r"\b(?:current roster from the information I have|current|reliable|do not have|don't know)\b"),
            ("official credits next step", r"\b(?:official tour credits|album/session credits|official.*credits|current band listings)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("stale forum certainty", r"\b(?:definitely|currently plays for)\b"),),
        requires_direct_first_sentence=True,
        direct_first_sentence_pattern=r"\b(?:do not have|don't have|don’t know|cannot verify|can't verify|current)\b",
    ),
    "sensitive_identity": AnswerContract(
        intent="sensitive_identity",
        required_answer_elements=(
            ("direct uncertainty", r"\b(?:I don’t know|I don't know|not enough reliable information)\b"),
            ("no private identity speculation", r"\b(?:private identity|not appropriate to speculate|do not speculate|would not be appropriate|would not want to guess)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("identity roster", r"\b(?:list of gay|gay players include)\b"),),
        requires_direct_first_sentence=True,
    ),
    "fallback_unknown": AnswerContract(
        intent="fallback_unknown",
        required_answer_elements=(
            ("reliable information uncertainty", r"\b(?:don’t have enough reliable information|don't have enough reliable information|not enough reliable information)\b"),
            ("useful next step", r"\b(?:try adding|check|provide|narrow|exact)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
        requires_direct_first_sentence=True,
        direct_first_sentence_pattern=r"\b(?:don’t have enough reliable information|don't have enough reliable information|not enough reliable information)\b",
    ),
    "yes_no_source_check": AnswerContract(
        intent="yes_no_source_check",
        required_answer_elements=(("direct yes/no or source weakness", r"\b(?:yes|no|do not see|source match|evidence|support)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN,
    ),
    "general_forum_wisdom": AnswerContract(
        intent="general_forum_wisdom",
        forbidden_answer_patterns=COMMON_FORBIDDEN,
        curated_answer_may_lead=False,
        rag_excerpts_may_appear_in_answer_body=True,
        source_context_in_source_cards_only=False,
    ),
}

CONTRACTS.update(
    {
        "scope_guardrail": AnswerContract(
            intent="scope_guardrail",
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer=(
                "That request is outside Steel Guitar RAG’s scope. "
                "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, or steel-guitar forum wisdom."
            ),
        ),
        "technique_coach": AnswerContract(
            intent="technique_coach",
            required_answer_elements=(("practical technique guidance", r"\b(?:drill|practice|listen|strings?|fret|grip|bar|blocking|pedal)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Use one small E9 technique drill: pick a grip, slow it down, block cleanly after each note, and listen for even timing.",
        ),
        "fretboard_concept": AnswerContract(
            intent="fretboard_concept",
            required_answer_elements=(("steel fretboard concept", r"\b(?:E9|fret|pedal|lever|grip|chord|interval|position)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Think of the E9 neck as related position families: open/no-pedals, A+B, A+F, and E-lower colors.",
        ),
        "movement_from_position": AnswerContract(
            intent="movement_from_position",
            required_answer_elements=(("position movement", r"\b(?:A\+B|open|A\+F|E-lower|fret|position|move)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Choose the next E9 move by chord function: open/no-pedals, A+B, A+F, or E-lower, then keep the grip simple.",
        ),
        "missing_context_clarifier": AnswerContract(
            intent="missing_context_clarifier",
            required_answer_elements=(("missing context", r"\b(?:chord|key|fret|strings?|grip|pedals?|levers?)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="I need the chord or key, fret, strings or grip, and pedals/levers before I can answer that accurately.",
        ),
        "copedent_mismatch_guardrail": AnswerContract(
            intent="copedent_mismatch_guardrail",
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="That does not match the current 10-string E9 setup I can safely reason about, so I would verify the copedent before mapping it.",
        ),
        "direct_yes_no_practical": AnswerContract(
            intent="direct_yes_no_practical",
            required_answer_elements=(("direct yes/no", r"^\s*(?:No|Yes|It depends|Not exactly)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Not exactly. I can give the practical steel-guitar answer first, then use sources only as supporting context.",
        ),
        "chord_quality_theory": AnswerContract(
            intent="chord_quality_theory",
            required_answer_elements=(("chord tones or intervals", r"\b(?:root|3rd|5th|7th|chord tones?|flat 7|sus4)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Start with the chord tones first, then map them to E9 only when the position is supported.",
        ),
        "unsupported_exact_mapping": AnswerContract(
            intent="unsupported_exact_mapping",
            required_answer_elements=(("limited mapping statement", r"\b(?:limited|does not yet|not show every|exact)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="The exact E9 mapping is limited here, but the chord spelling can still be answered directly.",
        ),
        "forum_context_secondary": AnswerContract(
            intent="forum_context_secondary",
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Forum discussions are useful context, but the practical answer should come first.",
        ),
        "when_to_use_musical_context": AnswerContract(
            intent="when_to_use_musical_context",
            required_answer_elements=(("musical use case", r"\b(?:use|resolve|tension|phrase|intro|ending|held chord)\b"),),
            forbidden_answer_patterns=COMMON_FORBIDDEN,
            fallback_answer="Use that sound when you want a clear musical effect, then resolve or move it intentionally.",
        ),
    }
)


INTENT_ALIASES = {
    "player_history": "subjective_ranking",
    "practice_context": "performance_context_guidance",
    "practice_style": "performance_context_guidance",
    "practice_path": "practice_plan",
    "performance_feel": "technique_improvement",
    "gear_troubleshooting": "diagnostic_troubleshooting",
    "gear_setup": "diagnostic_troubleshooting",
    "touch_tone": "tone_touch",
    "tab_copyright": "song_learning",
    "public_domain_tab_or_exercise": "song_learning",
    "song_learning_or_tab_request": "song_learning",
    "current_roster_lookup": "current_roster",
    "sensitive_identity_question": "sensitive_identity",
    "brand_player_lookup": "player_brand_usage",
    "gear_comparison": "brand_comparison",
    "gear_practical": "equipment_recommendation",
    "preference_safety": "equipment_recommendation",
    "technique_setup": "equipment_recommendation",
    "product_definition": "product_value",
    "curated_fact_source_check": "yes_no_source_check",
    "unknown": "fallback_unknown",
    "safety_boundary": "general_forum_wisdom",
    "teach_me_something": "fretboard_concept",
    "movement_request": "movement_from_position",
    "progression_intro_request": "fretboard_concept",
    "pocket_request": "practical_concept_explanation",
    "lick_request": "technique_coach",
    "vague_learning_request": "fretboard_concept",
    "frustrated_learning_request": "fretboard_concept",
    "everyday_context": "fretboard_concept",
}


def normalize_intent(intent: str | None) -> str:
    if not intent:
        return "general_forum_wisdom"
    return INTENT_ALIASES.get(intent, intent if intent in CONTRACTS else "general_forum_wisdom")


def contract_for_intent(intent: str | None) -> AnswerContract:
    return CONTRACTS[normalize_intent(intent)]


def infer_contract_intent(question: str, mode: str = "ask") -> str:
    q = re.sub(r"\s+", " ", question or "").strip().lower()
    if _mentions_scope_guardrail(q):
        return "scope_guardrail"
    if re.search(r"\b(?:gay people|gay players|lgbtq|sexual orientation)\b", q):
        return "sensitive_identity"
    if re.search(r"\bwho\s+plays\s+for\s+[a-z0-9'. -]+\??$", q):
        return "current_roster"
    if "church" in q and ("steel" in q or "play" in q):
        return "performance_context_guidance"
    if _mentions_song_learning_or_tab(q):
        return "song_learning"
    if _mentions_diagnostic_troubleshooting(q):
        return "diagnostic_troubleshooting"
    if _mentions_tone_touch(q):
        return "tone_touch"
    if re.search(
        r"\b(?:sound less mechanical|sounds mechanical|sound more musical|less stiff|fills? sound better|play with more feeling|sound less robotic)\b",
        q,
    ):
        return "technique_improvement"
    if re.search(r"\b(?:stroboplus|strobo\s*plus)\b", q) and re.search(
        r"\b(?:power|battery|batteries|charge|charging|usb|external|gig|live|show|run out|runs out)\b",
        q,
    ):
        return "gear_advice"
    if "delay" in q and "volume pedal" in q:
        return "gear_advice"
    if re.search(r"\b(?:battery-powered|battery|batteries)\b", q) and "tuner" in q and re.search(r"\b(?:live|gig|show|stage)\b", q):
        return "gear_advice"
    if re.search(r"\bwhat\s+do\s+players\s+say\b", q) and "string" in q and re.search(r"\b(?:break|broke|broken|breaking)\b", q):
        return "forum_wisdom"
    if re.search(r"\b(?:broke|break|breaking|broken|keeps breaking)\b", q) and "string" in q and re.search(r"\b(?:show|gig|stage|set|live|carry)\b", q):
        return "gig_advice"
    if "emergency" in q and "gig" in q and "kit" in q:
        return "gig_advice"
    if re.search(r"\b(?:worse\s+than\s+google|not\s+a\s+teacher|aren't\s+a\s+teacher|answering\s+machine|play\s+anything|just\s+one\s+thing|teach\s+me\s+anything|tell\s+me\s+something|might\s+not\s+already\s+know|show\s+me\s+anything)\b", q):
        return "practice_plan"
    if re.search(r"\b(?:where\s+should\s+i\s+go|where\s+do\s+i\s+go|move\s+up\s+the\s+neck|not\s+staying\s+still)\b", q):
        return "movement_from_position"
    if re.search(r"\b1\s*[-/]\s*4\s*[-/]\s*5\s*[-/]\s*1\b", q):
        return "practice_plan"
    if re.search(r"\bpocket\b", q) and re.search(r"\b(?:show|give|specific|learn)\b", q):
        return "practical_concept_explanation"
    if re.search(r"\blick\b", q) and re.search(r"\b(?:show|give|one|example)\b", q):
        return "technique_coach"
    if re.search(r"\b(?:kitchen|chew\s+gum|gum)\b", q) and re.search(r"\b(?:play|practice|pedal\s+steel|steel)\b", q):
        return "practice_plan"
    if re.search(r"\b(?:this\s+(?:position|chord|grip|move|lick)|that\s+(?:position|chord|grip|move|lick)|from\s+here)\b", q):
        return "missing_context_clarifier"
    if re.search(r"\bclassic\s+country\s+move\b|\bclean\s+up\s+my\s+blocking\b|\bbar\s+movement\b|\bslides?\s+sound\s+smoother\b|\bvolume\s+pedal\s+sounds\s+jumpy\b|\bsound\s+less\s+busy\b|\boverplaying\s+fills?\b", q):
        return "technique_coach"
    if "practice rut" in q or "rut breaker" in q or re.search(r"\b(?:7[-\s]?day|10[-\s]?minute|20[-\s]?minute|25[-\s]?minute).*\bpractice\b", q):
        return "practice_plan"
    if re.search(r"\b(?:better way to think about the neck|stop getting lost on the fretboard|connect open position|iv from open position|minor walkdown from a\+b)\b", q):
        return "fretboard_concept"
    if re.search(r"\b(?:where should i go after a\+b|where do i go after a\+b|after a\+b)\b", q):
        return "movement_from_position"
    if "what should i practice" in q or "practice plan" in q or "practice routine" in q or mode == "practice":
        return "practice_plan"
    if re.search(r"\bwhere\s+can\s+i\s+buy\b|\bwhat\s+brands\s+make\b", q):
        return "vendor_buying_guidance"
    if re.search(r"\bwho\s+(?:plays?|uses?)\s+(?:an?\s+)?[a-z0-9-]+", q):
        return "player_brand_usage"
    if re.search(r"\b(?:still\s+in\s+business|operating today|in business today)\b", q):
        return "current_company_status"
    if _mentions_two_brands(q):
        return "brand_comparison"
    if re.match(r"^\s*who\s+is\s+[a-z'.-]+(?:\s+[a-z'.-]+)+\??\s*$", q):
        return "player_bio"
    if re.search(r"\b(top|best|greatest|ranking|ranked|most influential)\b", q) and "player" in q:
        return "subjective_ranking"
    if re.search(r"\b(?:a\+b|b\+c|a\+f|pedal|lever|fret|chord|e9|copedent|string)\b", q) or mode == "copedent":
        return "copedent_fretboard"
    if re.search(r"\b(?:triad|2m|ii minor|5\^7|string gauge|gauge)\b", q):
        return "copedent_fretboard"
    if re.search(r"\b(?:oil|lubricate|changer|wd-40|naphtha|lighter fluid)\b", q):
        return "maintenance_safety"
    if re.search(r"\b(?:pedal rod|pedal rods|replacement|broke|broken)\b", q):
        return "replacement_parts"
    if re.search(r"\b(?:airplane|airline|flight|fly|travel)\b", q):
        return "travel_transport"
    if re.search(r"\b(?:worth|value|worth the money|should i buy)\b", q):
        return "product_value"
    if re.search(r"\b(?:what is|who is|stands for)\b", q):
        return "entity_definition"
    if re.search(r"\b(?:did|does|is)\b.+\b(?:make|made|invent|prove|every)\b", q):
        return "yes_no_source_check"
    return "general_forum_wisdom"


def validate_answer_against_contract(answer: str, intent: str | None) -> ContractValidation:
    contract = contract_for_intent(intent)
    violations: list[str] = []
    for reason, pattern in contract.forbidden_answer_patterns:
        if _contract_pattern_matches(reason, pattern, answer):
            violations.append(reason)
    for reason, pattern in contract.required_answer_elements:
        if not re.search(pattern, answer, re.I):
            violations.append(f"missing {reason}")
    for label in contract.required_section_labels:
        if not _has_section_label(answer, label):
            violations.append(f"missing section {label}")
    if contract.requires_direct_first_sentence and _violates_direct_first_sentence(answer, contract):
        violations.append("missing direct first sentence")
    return ContractValidation(intent=contract.intent, answer=answer, violations=tuple(violations))


def enforce_answer_contract(answer: str, intent: str | None) -> ContractValidation:
    contract = contract_for_intent(intent)
    validation = validate_answer_against_contract(answer, contract.intent)
    if validation.is_valid:
        return validation
    if not _has_forbidden_violation(validation, contract):
        return validation
    scrubbed = _remove_forbidden_lines(answer, contract)
    scrubbed_validation = validate_answer_against_contract(scrubbed, contract.intent)
    if scrubbed.strip() and not _has_forbidden_violation(scrubbed_validation, contract):
        return scrubbed_validation
    return ContractValidation(
        intent=contract.intent,
        answer=contract.fallback_answer,
        violations=validation.violations,
    )


def _remove_forbidden_lines(answer: str, contract: AnswerContract) -> str:
    lines: list[str] = []
    for line in answer.splitlines():
        if any(_contract_pattern_matches(reason, pattern, line) for reason, pattern in contract.forbidden_answer_patterns):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _has_forbidden_violation(validation: ContractValidation, contract: AnswerContract) -> bool:
    forbidden_reasons = {reason for reason, _ in contract.forbidden_answer_patterns}
    return any(violation in forbidden_reasons for violation in validation.violations)


def _contract_pattern_matches(reason: str, pattern: str, text: str) -> bool:
    flags = 0 if reason == "raw Top boilerplate" else re.I
    return bool(re.search(pattern, text, flags))


def _has_section_label(answer: str, label: str) -> bool:
    escaped = re.escape(label)
    return bool(re.search(rf"(?im)^\s*{escaped}\s*(?::\s*(?:\S.*)?)?$", answer))


def _first_sentence(answer: str) -> str:
    compact = re.sub(r"\s+", " ", answer or "").strip()
    if not compact:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    return (match.group(1) if match else compact).strip()


def _violates_direct_first_sentence(answer: str, contract: AnswerContract) -> bool:
    first = _first_sentence(answer)
    if not first:
        return True
    if contract.direct_first_sentence_pattern and not re.search(contract.direct_first_sentence_pattern, first, re.I):
        return True
    return bool(
        re.search(
            r"^(?:the retrieved sources|source cards|useful distilled points|useful source-backed points|source context|what multiple sources support|top\b)",
            first,
            re.I,
        )
        or re.search(r"\b(?:Does anyone know|Has anyone compared|I am looking for)\b", first, re.I)
    )


def _mentions_two_brands(question: str) -> bool:
    brands = re.findall(r"\b(mullen|msa|emmons|sho-bud|shobud|zumsteel|carter|gfi|sierra)\b", question, re.I)
    return len({brand.lower() for brand in brands}) >= 2 and bool(
        re.search(r"\b(?:better|difference|compare|vs\.?|versus|or|than|buy)\b", question, re.I)
    )


def _mentions_song_learning_or_tab(question: str) -> bool:
    return bool(
        re.search(r"\b(?:tab|tablature|lyrics?)\b", question)
        or re.search(r"\b(?:approach playing|explain the style of|chord progression|original e9 lick|song arrangement)\b", question)
        or re.search(r"\b(?:play a song|teach me how to play anything specific)\b", question)
        or re.search(r"\b(?:panhandle rag|together again|amazing grace|slow country ballad)\b", question)
    )


def _mentions_scope_guardrail(question: str) -> bool:
    return bool(
        re.search(r"\ball\s+(?:of\s+)?(?:the\s+)?numbers?\s+between\s+\d[\d,]*\s+(?:and|to)\s+\d[\d,]*\b", question)
        or re.search(r"\b(?:numbers?|integers?)\s+from\s+\d[\d,]*\s+(?:to|through)\s+\d[\d,]*\b", question)
        or re.search(r"\b(?:write|repeat|print|list|show)\b.*\b(?:word|phrase|steel guitar|numbers?)\b.*?\d[\d,]*\s+times\b", question)
        or re.search(r"\b(?:weather\s+in|capital\s+of|recipe\s+for|who\s+won\s+the\s+super\s+bowl|super\s+bowl\s+winner)\b", question)
    )


def _mentions_diagnostic_troubleshooting(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:amp\s+(?:buzz|buzzes|hum|hums)|buzz\s+at\s+idle|amp\s+hum|hums?\s+until\s+i\s+touch|noise\s+when\s+nothing\s+is\s+plugged\s+in|ground\s+buzz|touching\s+(?:the\s+)?(?:strings?|changer).*(?:buzz|hum)|(?:buzz|hum)\w*.{0,80}(?:touch(?:ing)?).{0,80}(?:strings?|changer))\b",
            question,
        )
    )


def _mentions_tone_touch(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:soften\s+my\s+attack|attack\s+is\s+too\s+hard|sound\s+less\s+harsh|pick\s+attack\s+(?:sounds\s+)?too\s+sharp|play\s+with\s+softer\s+touch)\b",
            question,
        )
    )
