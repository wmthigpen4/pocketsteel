"""Reusable answer contracts for The Turnaround answer generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnswerContract:
    intent: str
    required_answer_elements: tuple[tuple[str, str], ...] = ()
    forbidden_answer_patterns: tuple[tuple[str, str], ...] = ()
    default_section_labels: tuple[str, ...] = ()
    curated_answer_may_lead: bool = True
    rag_excerpts_may_appear_in_answer_body: bool = False
    source_context_in_source_cards_only: bool = True
    fallback_answer: str = (
        "I found related source cards, but the retrieved text is too noisy to use safely in the answer body. "
        "Ask a more specific steel-guitar question and I can give a cleaner answer."
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
    ("raw Top boilerplate", r"^\s*Top\b|\sTop\s"),
    ("raw link-share fragment", r"\bsp=sharing\b"),
    ("raw email address", r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b"),
    ("raw e-mail contact", r"\be-?mail\s+"),
    ("source context heading", r"\b(?:Source context|Forum-source context|What multiple sources support)\b"),
    ("orphan Practical answer heading", r"(?m)^\s*Practical answer\s*:?\s*$"),
    ("forum question fragment", r"\b(?:Does anyone know|Has anyone compared|I am looking for tablature)\b"),
    ("inline citation marker", r"\[\d+\]"),
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
    "copedent_fretboard": AnswerContract(
        intent="copedent_fretboard",
        required_answer_elements=(("fretboard mechanics", r"\b(?:fret|pedal|lever|string|E9|grip|chord)\b"),),
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
            ("places to buy", r"\b(?:dealer|vendor|retailer|shop|store|classifieds?|used market|maker|manufacturer|bar makers?)\b"),
            ("specs to check", r"\b(?:diameter|length|weight|material|thread|connector|compatib|size|gauge)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("generic product-value template", r"\bpositive owner/source impression\b|\bthat product\b"),),
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
            ("no universal winner", r"\b(?:no universal winner|depends|fit|condition|personal|specific guitars)\b"),
            ("comparison caveats", r"\b(?:condition|setup|copedent|support|mechanics|budget|tone|feel)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("generic product-value template", r"\bpositive owner/source impression\b|\bthat product\b"),),
        default_section_labels=("comparison",),
    ),
    "player_bio": AnswerContract(
        intent="player_bio",
        required_answer_elements=(("biographical answer", r"\b(?:steel guitarist|player|known for|associated with|influential)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("ranking template", r"\bRankings are subjective\b|\bA safe all-time starting list\b"),),
    ),
    "player_brand_usage": AnswerContract(
        intent="player_brand_usage",
        required_answer_elements=(("player usage or weak roster support", r"\b(?:players?|users?|roster|source-backed|currently uses|artist list)\b"),),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("company-status-only answer", r"\bReSound’65\b"),),
        fallback_answer=(
            "I do not have a strong, current, source-backed player roster for that brand. "
            "Use the source cards as leads and verify current users through official artist lists or recent credits."
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
    "public_domain_tab_or_exercise": AnswerContract(
        intent="public_domain_tab_or_exercise",
        required_answer_elements=(
            ("copyright boundary", r"\b(?:copyrighted|public-domain|public domain)\b"),
            ("concrete exercise", r"\b(?:mini-tab|exercise|chord path|fret|A\+B|A pedal \+ F lever)\b"),
        ),
        forbidden_answer_patterns=COMMON_FORBIDDEN + (("random contact", r"\b(?:email|e-mail)\b"),),
        default_section_labels=("safer options", "exercise"),
        fallback_answer=(
            "I cannot provide copyrighted song tab by default. I can build a public-domain or original exercise, for example a simple G-C-D-G E9 chord path."
        ),
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
    "tab_copyright": "public_domain_tab_or_exercise",
    "brand_player_lookup": "player_brand_usage",
    "gear_comparison": "brand_comparison",
    "gear_practical": "equipment_recommendation",
    "preference_safety": "equipment_recommendation",
    "technique_setup": "equipment_recommendation",
    "product_definition": "product_value",
    "curated_fact_source_check": "yes_no_source_check",
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
    if "church" in q and ("steel" in q or "play" in q):
        return "performance_context_guidance"
    if ("tablature" in q or "tab" in q) and ("random song" in q or "song" in q):
        return "public_domain_tab_or_exercise"
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
        if re.search(pattern, answer, re.I):
            violations.append(reason)
    for reason, pattern in contract.required_answer_elements:
        if not re.search(pattern, answer, re.I):
            violations.append(f"missing {reason}")
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
        if any(re.search(pattern, line, re.I) for _, pattern in contract.forbidden_answer_patterns):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _has_forbidden_violation(validation: ContractValidation, contract: AnswerContract) -> bool:
    forbidden_reasons = {reason for reason, _ in contract.forbidden_answer_patterns}
    return any(violation in forbidden_reasons for violation in validation.violations)


def _mentions_two_brands(question: str) -> bool:
    brands = re.findall(r"\b(mullen|msa|emmons|sho-bud|shobud|zumsteel|carter|gfi|sierra)\b", question, re.I)
    return len({brand.lower() for brand in brands}) >= 2 and bool(
        re.search(r"\b(?:better|difference|compare|vs\.?|versus|or|than|buy)\b", question, re.I)
    )
