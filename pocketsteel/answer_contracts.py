"""Reusable answer contracts for The Turnaround answer generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


COPYRIGHT_AWARE_SONG_HELP_POLICY = (
    "The assistant may discuss songs, recordings, style, chord movement, technique, tone, practice strategy, "
    "and arrangement approach. It may create original exercises and public-domain examples. It should not provide "
    "full copyrighted lyrics, full copyrighted tablature, or complete note-for-note copyrighted arrangements unless "
    "the user provides the material, the work is public domain, or permission/license is available."
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
    ("internal source-backed fallback language", r"\bThe cleanest source-backed answer\b|\bHere is the safest answer I can support from the retrieved material\b|\bretrieved material\b|\bsource cards as supporting evidence\b|\bUseful distilled points\b|\bUseful source-backed points\b"),
    ("raw Top boilerplate", r"^\s*Top\b|\sTop\s"),
    ("raw link-share fragment", r"\bsp=sharing\b"),
    ("raw email address", r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b"),
    ("raw e-mail contact", r"\be-?mail\s+"),
    ("raw sales/contact snippet", r"\b(?:PayPal|order\s+(?:form|page|link|online|through))\b"),
    ("source context heading", r"\b(?:Source context|Forum-source context|What multiple sources support)\b"),
    ("orphan Practical answer heading", r"(?m)^\s*Practical answer\s*:?\s*$"),
    ("duplicate answer headings", r"(?s)(?m)^\s*Answer\s*:?\s*$.*^\s*Practical answer\s*:?\s*$"),
    ("forum question fragment", r"\b(?:Does anyone know|Has anyone compared|I am looking for tablature)\b"),
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
            ("right-hand pick context", r"\b(?:thumb pick|fingerpicks?|ring-finger|fourth)\b"),
            ("four-note or grip reason", r"\b(?:four-note|grips?|wider chords?|C6|extended)\b"),
            ("optional caveat", r"\b(?:optional|not required|do not need|awkward)\b"),
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
            ("what changes or provides", r"\b(?:raise|raises|lower|lowers|changes?|takes|string|gives|provides|note)\b"),
            ("chord or interval result", r"\b(?:chord|interval|triad|dominant|major|minor|seventh|scale tone|color)\b"),
            ("fret/string/pedal example", r"\b(?:fret|pedal|lever|string|grip)\b"),
            ("practical use", r"\b(?:use|practical|players use|practice|connect|movement)\b"),
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
            ("song, key, tuning, or user-provided path", r"\b(?:song|key|tuning|user-provided|provide the notes|short excerpt|chart)\b"),
            ("public-domain or original exercise path", r"\b(?:public-domain|public domain|original|mini-tab|exercise|Amazing Grace)\b"),
            ("copyright-aware tab or lyrics boundary", r"\b(?:full note-for-note|full lyrics|copyrighted tab|copyrighted lyrics|protected melody)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN
        + (
            ("random contact", r"\b(?:email|e-mail)\b"),
            ("blanket copyrighted-material refusal", r"\b(?:cannot|can't|do not|won't)\s+(?:discuss|talk about|help with)\s+copyrighted\b"),
        ),
        default_section_labels=("learning approach", "exercise"),
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
}


def normalize_intent(intent: str | None) -> str:
    if not intent:
        return "general_forum_wisdom"
    return INTENT_ALIASES.get(intent, intent if intent in CONTRACTS else "general_forum_wisdom")


def contract_for_intent(intent: str | None) -> AnswerContract:
    return CONTRACTS[normalize_intent(intent)]


def infer_contract_intent(question: str, mode: str = "ask") -> str:
    q = re.sub(r"\s+", " ", question or "").strip().lower()
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


def _mentions_diagnostic_troubleshooting(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:amp\s+(?:buzz|buzzes|hum|hums)|buzz\s+at\s+idle|amp\s+hum|hums?\s+until\s+i\s+touch|noise\s+when\s+nothing\s+is\s+plugged\s+in|ground\s+buzz|touching\s+(?:the\s+)?(?:strings?|changer).*(?:buzz|hum))\b",
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
