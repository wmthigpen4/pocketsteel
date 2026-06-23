"""Deterministic pre-retrieval answer intent classification.

This module is intentionally side-effect free. It does not retrieve sources,
build answers, or change public /api/answer response behavior. The classifier
is a small contract object future routing code can consult before deciding
whether retrieval is allowed.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal, TypedDict

from pocketsteel.music_text import normalize_spelled_accidentals


AnswerDomain = Literal["steel_guitar", "off_domain", "unsafe_or_impossible"]
AnswerIntent = Literal[
    "forum_wisdom",
    "copedent_position",
    "gear_diagnosis",
    "practice_plan",
    "tab_explainer",
    "lesson_lookup",
    "small_talk",
    "unknown",
]
AllowedAnswerShape = Literal[
    "source_backed",
    "copedent_position",
    "gear_diagnosis",
    "practice_plan",
    "tab_explainer",
    "guardrail_refusal",
]


class AnswerIntentPayload(TypedDict):
    domain: AnswerDomain
    intent: AnswerIntent
    needs_sources: bool
    needs_fretboard: bool
    needs_copedent: bool
    retrieval_allowed: bool
    allowed_answer_shape: AllowedAnswerShape


@dataclass(frozen=True)
class AnswerIntentDecision:
    domain: AnswerDomain
    intent: AnswerIntent
    needs_sources: bool
    needs_fretboard: bool
    needs_copedent: bool
    retrieval_allowed: bool
    allowed_answer_shape: AllowedAnswerShape

    def to_dict(self) -> AnswerIntentPayload:
        return asdict(self)  # type: ignore[return-value]


ALLOWED_DOMAINS = frozenset(("steel_guitar", "off_domain", "unsafe_or_impossible"))
ALLOWED_INTENTS = frozenset(
    (
        "forum_wisdom",
        "copedent_position",
        "gear_diagnosis",
        "practice_plan",
        "tab_explainer",
        "lesson_lookup",
        "small_talk",
        "unknown",
    )
)
ALLOWED_ANSWER_SHAPES = frozenset(
    (
        "source_backed",
        "copedent_position",
        "gear_diagnosis",
        "practice_plan",
        "tab_explainer",
        "guardrail_refusal",
    )
)
CONTRACT_KEYS = frozenset(AnswerIntentPayload.__annotations__)


STEEL_TERMS_RE = re.compile(
    r"\b(?:"
    r"pedal\s+steel|steel\s+guitar|e9|c6|copedent|fretboard|fret|frets|strings?|"
    r"pedals?|levers?|knee\s+lever|lkl|lkr|lkv|rkl|rkr|a\s*\+\s*b|a\s*\+\s*f|b\s*\+\s*c|"
    r"e[-\s]?lower|f\s+lever|vertical\s+lever|changer|volume\s+pedal|bar|tone\s+bar|"
    r"blocking|pick\s+blocking|palm\s+blocking|finger\s+picks?|4th\s+finger\s+picks?|"
    r"grips?|licks?|fills?|stroboplus|"
    r"fender\s+steel\s+king|peavey\s+nashville|nashville\s+amps?|bjs(?:\s+bars?)?|"
    r"steel\s+players?|steelers?|amp|hum|buzz|delay|tab|tablature|intervals?|singer|"
    r"diminished|minor|major|chord|positions?|wound\s+6th|6th\s+string|9th\s+string|"
    r"feeling|smoother|less\s+busy|musical"
    r")\b",
    re.I,
)

LARGE_NUMBER_RE = r"(?:\d{1,3}(?:,\d{3})+|\d{4,}|thousand|million)"
MASS_OUTPUT_RE = re.compile(
    r"\b(?:"
    r"all\s+(?:of\s+the\s+)?numbers?\s+(?:between|from)\s+\d+\s+(?:and|to)\s+(?:\d+|million)|"
    r"(?:from\s+)?\d+\s+to\s+(?:\d{5,}|million)|"
    rf"(?:write|repeat|print|show|make|create|generate|list|give)\b.{{0,80}}\b{LARGE_NUMBER_RE}\s+times?|"
    rf"(?:make|create|generate)\b.{{0,80}}\b{LARGE_NUMBER_RE}\s+(?:fretboard\s+)?diagrams?|"
    r"(?:write|generate|create)\b.{0,80}\b(?:\d+\s+pages?|book[-\s]?length|hour[-\s]?long)|"
    r"(?:every|all)\s+possible\b|"
    r"(?:exhaustive|book[-\s]?length)\b.{0,80}\bno\s+limits?|"
    r"repeat\b.{0,80}\bforever|"
    r"(?:print|show|list|output)\s+every\s+number\b|"
    r"(?:print|show|list)\s+every\b.{0,80}\bevery\b"
    r")",
    re.I,
)
UNSAFE_RE = re.compile(
    r"\b(?:"
    r"scrape\s+(?:instagram|facebook|tiktok|x\.com|twitter)|"
    r"python\s+script\s+to\s+scrape|"
    r"bypass\s+(?:login|paywall|rate\s+limit|terms)|"
    r"steal\s+(?:data|credentials)|"
    r"dump\s+(?:credentials|secrets|private\s+data|the\s+full\s+private\s+corpus|full\s+private\s+corpus)|"
    r"(?:list|print|show|give\s+me)\b.{0,80}\b(?:every|all)\b.{0,80}\b(?:post|email|password)|"
    r"(?:output|print|show)\b.{0,80}\b(?:chroma\s+)?embedding\s+vectors?|"
    r"(?:print|show)\b.{0,80}\bsource\s+metadata\s+records?|"
    r"(?:show|give\s+me)\b.{0,80}\b(?:private|paid)\s+(?:lesson\s+)?transcripts?|"
    r"(?:complete|full)\s+lyrics\s+to\s+every|"
    r"full\s+copyrighted|"
    r"note[-\s]?for[-\s]?note\b.{0,80}\b(?:entire|current|copyrighted|album|tab)|"
    r"full\s+solo\s+tab\b.{0,80}\bevery\s+string|"
    r"entire\s+current\s+copyrighted\s+album|"
    r"all\s+passwords?\s+in\s+the\s+repo|"
    r"generate\s+all\s+possible\s+copedents"
    r")\b",
    re.I,
)
NEGATED_STEEL_REFERENCE_RE = re.compile(
    r"\b(?:no|without)\s+steel\s+guitar\s+references?\b",
    re.I,
)
OFF_DOMAIN_RE = re.compile(
    r"\b(?:"
    r"weather|capital\s+of\s+france|recipe|pancakes?|super\s+bowl|nba|nfl|stock\s+price|"
    r"bitcoin|election|president\s+of|movie\s+times|flight\s+status|"
    r"javascript|python\s+code|python\s+script|quicksort|sorting\s+algorithm|dishwasher|"
    r"bedtime\s+story|castle|math\s+answer"
    r")\b",
    re.I,
)
MATH_EXPRESSION_RE = re.compile(r"\b\d[\d,]*\s*(?:x|\*)\s*\d[\d,]*\b", re.I)
SOURCE_SEEKING_RE = re.compile(
    r"\b(?:what\s+do\s+(?:players|people|forum|steelers)|players?\s+(?:say|describe)|forum\s+(?:players|wisdom|opinions?)|"
    r"players?\s+(?:use|talk\s+about|prefer)|common\s+(?:uses?|opinions?|comments?|views?)|"
    r"from\s+players|owner\s+reports?|practic(?:e|ing)\s+behind\s+a\s+singer)\b",
    re.I,
)
PLAYER_CONTEXT_RE = re.compile(
    r"\b(?:"
    r"buddy\s+emmons|lloyd\s+green|paul\s+franklin|jeff\s+newman|jimmy\s+day|"
    r"ralph\s+mooney|sarah\s+jory|curly\s+chalker|doug\s+jernigan|john\s+hughey|"
    r"notable\s+records?\s+with\s+pedal\s+steel"
    r")\b",
    re.I,
)
BRAND_CONTEXT_RE = re.compile(
    r"\b(?:"
    r"mullen|msa|emmons(?:\s+guitar(?:\s+co\.?)?)?|emmons\s+push[-\s]?pull|push[-\s]?pull|"
    r"carter\s+steels?|sho[-\s]?bud|benado\s+steel\s+dream|steel\s+dream|"
    r"telonics|fender\s+steel\s+king|steel\s+king"
    r")\b",
    re.I,
)
VENDOR_ACCESSORY_RE = re.compile(
    r"\b(?:"
    r"vendors?|accessories|strings?|volume\s+pedals?|bars?|tone\s+bars?|slide\s+bars?|"
    r"seats?|pac[-\s]?a[-\s]?seats?|steel\s+seats?|picks?|finger\s+picks?"
    r")\b",
    re.I,
)
GEAR_CONTEXT_RE = re.compile(
    r"\b(?:"
    r"3rd\s+string\s+keeps?\s+breaking|string\s+keeps?\s+breaking|"
    r"battery[-\s]?powered\s+tuners?|tuners?\s+live|good\s+volume\s+pedal|"
    r"oil\s+should\s+i\s+use|pedal\s+steel\s+parts?|clean\s+noisy\s+pedal\s+rods?|"
    r"tone\s+sound\s+thin|pedal\s+will\s+not\s+return|delay\s+settings?|effects?\s+loop|"
    r"hum\s+that\s+changes\s+when\s+touching\s+the\s+changer"
    r")\b",
    re.I,
)
GEAR_RE = re.compile(
    r"\b(?:"
    r"amp|hum|buzz|ground|grounding|pickup|cable|effects?|delay|reverb|volume\s+pedal|"
    r"fender\s+steel\s+king|stroboplus|strobo\s*plus|tuner|battery|batteries|power|"
    r"strings?\s+(?:keep|keeps)?\s*breaking|gig\s+kit|emergency\s+kit|oil|"
    r"pedal\s+rods?|parts?|tone\s+sound\s+thin|will\s+not\s+return|"
    r"telonics|pac[-\s]?a[-\s]?seat|steel\s+seat|bars?|picks?"
    r")\b",
    re.I,
)
GEAR_DIAGNOSIS_RE = re.compile(
    r"\b(?:diagnos|check|why|what\s+should|settings?|harsh|thin|buzz|hum|ground|"
    r"before|after|power|batteries?|run\s+out|breaking|carry|good|recommend|"
    r"use|live|clean|oil|return|effects?\s+loop)\b",
    re.I,
)
PRACTICE_RE = re.compile(
    r"\b(?:practice|plan|routine|workout|drills?|exercise|blocking|bar\s+movement|"
    r"clean\s+up|rut\s+breaker|woodshed|learn|7[-\s]?day|10[-\s]?minute|20[-\s]?minute|"
    r"feeling|fills?|less\s+busy|smoother|musical)\b",
    re.I,
)
TAB_INTERVAL_RE = re.compile(
    r"\b(?:tab|tablature|intervals?|chord\s+tones?|omitted\s+intervals?|"
    r"what\s+does\s+\d+[a-z]?\s+mean|explain\s+this\s+tab|read\s+pedals?)\b",
    re.I,
)
LESSON_RE = re.compile(r"\b(?:lesson|lessons|course|tutorial|transcript|manual|pdf)\b", re.I)
COPEDENT_RE = re.compile(
    r"\b(?:"
    r"copedent|setup|pedals?|levers?|strings?|grips?|fret|frets|position|positions|"
    r"e[-\s]?lower|f\s+lever|vertical\s+lever|a\s*\+\s*b|a\s*\+\s*f|b\s*\+\s*c|"
    r"rkl|rkr|lkl|lkr|lkv|lower|raises?|changes?|9th\s+string|6th\s+string|wound\s+6th"
    r")\b",
    re.I,
)
POSITION_LANGUAGE_RE = re.compile(
    r"\b(?:"
    r"where|location|find|show\s+me|places?|positions?|frets?\s+(?:give|for)|"
    r"how\s+do\s+(?:i|you)\s+(?:play|make)|on\s+(?:the\s+)?e9|pedal\s+steel|from\s+a\s*\+\s*b"
    r")\b",
    re.I,
)
CONCRETE_CHORD_RE = re.compile(
    r"\b(?:[a-g](?:##|bb|#|b)?(?:\s*(?:major|minor|m|7|9|dim|diminished))?\s*(?:chord|positions?)|"
    r"[a-g](?:##|bb|#|b)?\s+on\s+e9|"
    r"\d\s*m\s+chord|(?:vi|ii|iii|iv|v|i)\s+chord)\b",
    re.I,
)
VISUAL_POSITION_RE = re.compile(
    r"\b(?:"
    r"where\s+(?:are|is|can|all|should|does|do)|"
    r"show(?:\s+me)?|"
    r"find|"
    r"location|"
    r"what\s+frets?|"
    r"frets?\s+give|"
    r"places?\s+to\s+play"
    r")\b",
    re.I,
)
EXPLICIT_VISUAL_OBJECT_RE = re.compile(
    r"\b(?:positions?|location|frets?|grips?|string\s+group(?:ing)?s?|pockets?|chord\s+positions?|on\s+(?:the\s+)?e9|pedal\s+steel|1[-\s]?3[-\s]?5)\b",
    re.I,
)
MISSING_CONTEXT_VISUAL_RE = re.compile(
    r"\bthis\s+(?:position|chord|grip|move|lick|voicing)\b",
    re.I,
)
BUYING_RE = re.compile(r"\b(?:buy|where\s+can\s+i\s+buy|purchase|order|for\s+sale)\b", re.I)
ROOTED_CHORD_QUALITY_RE = re.compile(
    r"(?<![-\w])[a-g](?:##|bb|#|b)?\s*(?:"
    r"dom\s*7|dom7|dominant\s*7|7th|7(?![-\w])|"
    r"maj\s*7|maj7|major\s*7|major\s*7th|major\s+seventh"
    r")(?![-\w])",
    re.I,
)
G_HARMONIZED_SCALE_VISUAL_RE = re.compile(
    r"\b(?:show|where|find|display)\b.*\b(?:"
    r"g\s+(?:major\s+|natural\s+minor\s+)?harmonized\s+scale|"
    r"g\s+harmonized\s+scale|"
    r"(?:f#|f\s+sharp)\s+diminished\s+position\s+in\s+g|"
    r"a\s+diminished\s+position\s+in\s+g\s+minor"
    r")\b",
    re.I,
)


def classify_answer_request(question: str, mode: str = "ask") -> AnswerIntentPayload:
    """Classify an answer request before retrieval.

    The classifier is conservative. Ambiguous steel questions stay steel-domain
    `unknown` rather than being forced into a visual or source-backed path.
    """

    q = _normalize(question)
    normalized_mode = _normalize(mode)
    if not q:
        return _decision(
            domain="unsafe_or_impossible",
            intent="unknown",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="guardrail_refusal",
        )

    guardrail_decision = _guardrail_decision(q)
    if guardrail_decision is not None:
        return guardrail_decision

    if _mentions_sensitive_personal_attribute(q):
        return _decision(
            domain="steel_guitar",
            intent="unknown",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="guardrail_refusal",
        )

    if _mentions_specific_biography_fact(q):
        return _decision(
            domain="steel_guitar",
            intent="forum_wisdom",
            needs_sources=True,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="guardrail_refusal",
        )

    if _mentions_style_how_to(q) or _mentions_safety_adjacent_playing(q):
        return _decision(
            domain="steel_guitar",
            intent="practice_plan",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="practice_plan",
        )

    if _mentions_default_teaching_request(q):
        return _decision(
            domain="steel_guitar",
            intent="practice_plan",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="practice_plan",
        )

    if _mentions_g_harmonized_scale_visual(q):
        return _decision(
            domain="steel_guitar",
            intent="copedent_position",
            needs_sources=False,
            needs_fretboard=True,
            needs_copedent=True,
            retrieval_allowed=False,
            allowed_answer_shape="copedent_position",
        )

    mode_decision = _decision_from_mode(q, normalized_mode)
    if mode_decision is not None:
        return mode_decision

    source_backed_decision = _source_backed_steel_decision(q)
    if source_backed_decision is not None:
        return source_backed_decision

    rooted_quality_decision = _rooted_chord_quality_decision(q)
    if rooted_quality_decision is not None:
        return rooted_quality_decision

    if SOURCE_SEEKING_RE.search(q) and _mentions_steel(q):
        return _decision(
            domain="steel_guitar",
            intent="forum_wisdom",
            needs_sources=True,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=True,
            allowed_answer_shape="source_backed",
        )

    if _mentions_gear_diagnosis(q):
        return _decision(
            domain="steel_guitar",
            intent="gear_diagnosis",
            needs_sources=True,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=True,
            allowed_answer_shape="gear_diagnosis",
        )

    if TAB_INTERVAL_RE.search(q) and _mentions_steel(q):
        return _decision(
            domain="steel_guitar",
            intent="tab_explainer",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=True,
            retrieval_allowed=False,
            allowed_answer_shape="tab_explainer",
        )

    if _mentions_visual_position(q):
        return _decision(
            domain="steel_guitar",
            intent="copedent_position",
            needs_sources=False,
            needs_fretboard=True,
            needs_copedent=True,
            retrieval_allowed=False,
            allowed_answer_shape="copedent_position",
        )

    if COPEDENT_RE.search(q) and _mentions_steel(q):
        return _decision(
            domain="steel_guitar",
            intent="copedent_position",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=True,
            retrieval_allowed=False,
            allowed_answer_shape="copedent_position",
        )

    if PRACTICE_RE.search(q) and _mentions_steel(q):
        return _decision(
            domain="steel_guitar",
            intent="practice_plan",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="practice_plan",
        )

    if LESSON_RE.search(q) and _mentions_steel(q):
        return _decision(
            domain="steel_guitar",
            intent="lesson_lookup",
            needs_sources=True,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=True,
            allowed_answer_shape="source_backed",
        )

    if _mentions_steel(q):
        return _decision(
            domain="steel_guitar",
            intent="unknown",
            needs_sources=True,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=True,
            allowed_answer_shape="source_backed",
        )

    return _decision(
        domain="off_domain",
        intent="unknown",
        needs_sources=False,
        needs_fretboard=False,
        needs_copedent=False,
        retrieval_allowed=False,
        allowed_answer_shape="guardrail_refusal",
    )


def classify_answer_intent(question: str) -> AnswerIntentPayload:
    """Backward-compatible classifier entry point for question-only callers."""

    return classify_answer_request(question)


def _guardrail_decision(question: str) -> AnswerIntentPayload | None:
    if MASS_OUTPUT_RE.search(question) or UNSAFE_RE.search(question):
        return _decision(
            domain="unsafe_or_impossible",
            intent="unknown",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="guardrail_refusal",
        )
    if NEGATED_STEEL_REFERENCE_RE.search(question):
        return _decision(
            domain="off_domain",
            intent="small_talk",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="guardrail_refusal",
        )
    if (OFF_DOMAIN_RE.search(question) or MATH_EXPRESSION_RE.search(question)) and not _mentions_steel(question):
        return _decision(
            domain="off_domain",
            intent="small_talk",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="guardrail_refusal",
        )
    return None


def _decision_from_mode(question: str, mode: str) -> AnswerIntentPayload | None:
    if not _mentions_steel(question):
        return None
    if mode in {"practice", "coach"}:
        return _decision(
            domain="steel_guitar",
            intent="practice_plan",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=False,
            allowed_answer_shape="practice_plan",
        )
    if mode in {"gear", "diagnose"}:
        return _decision(
            domain="steel_guitar",
            intent="gear_diagnosis",
            needs_sources=True,
            needs_fretboard=False,
            needs_copedent=False,
            retrieval_allowed=True,
            allowed_answer_shape="gear_diagnosis",
        )
    if mode in {"tab", "explain_tab"}:
        return _decision(
            domain="steel_guitar",
            intent="tab_explainer",
            needs_sources=False,
            needs_fretboard=False,
            needs_copedent=True,
            retrieval_allowed=False,
            allowed_answer_shape="tab_explainer",
        )
    if mode in {"copedent", "fretboard"}:
        return _decision(
            domain="steel_guitar",
            intent="copedent_position",
            needs_sources=False,
            needs_fretboard=bool(_mentions_visual_position(question)),
            needs_copedent=True,
            retrieval_allowed=False,
            allowed_answer_shape="copedent_position",
        )
    return None


def _decision(
    *,
    domain: AnswerDomain,
    intent: AnswerIntent,
    needs_sources: bool,
    needs_fretboard: bool,
    needs_copedent: bool,
    retrieval_allowed: bool,
    allowed_answer_shape: AllowedAnswerShape,
) -> AnswerIntentPayload:
    return AnswerIntentDecision(
        domain=domain,
        intent=intent,
        needs_sources=needs_sources,
        needs_fretboard=needs_fretboard,
        needs_copedent=needs_copedent,
        retrieval_allowed=retrieval_allowed,
        allowed_answer_shape=allowed_answer_shape,
    ).to_dict()


def _normalize(question: str) -> str:
    return re.sub(r"\s+", " ", normalize_spelled_accidentals(question or "")).strip().lower()


def _mentions_steel(question: str) -> bool:
    return bool(STEEL_TERMS_RE.search(question))


def _mentions_g_harmonized_scale_visual(question: str) -> bool:
    return bool(G_HARMONIZED_SCALE_VISUAL_RE.search(question))


def _mentions_gear_diagnosis(question: str) -> bool:
    return bool(GEAR_RE.search(question) and (GEAR_DIAGNOSIS_RE.search(question) or "fender steel king" in question))


def _rooted_chord_quality_decision(question: str) -> AnswerIntentPayload | None:
    if ROOTED_CHORD_QUALITY_RE.search(question) is None:
        return None
    wants_position = bool(
        re.search(r"\b(?:how\s+do\s+i\s+play|how\s+do\s+you\s+play|show|where|what\s+frets?|positions?|on\s+(?:the\s+)?e9)\b", question)
    )
    return _decision(
        domain="steel_guitar",
        intent="copedent_position",
        needs_sources=False,
        needs_fretboard=wants_position,
        needs_copedent=wants_position,
        retrieval_allowed=False,
        allowed_answer_shape="copedent_position",
    )


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
            or PLAYER_CONTEXT_RE.search(question)
        )
    )


def _mentions_specific_biography_fact(question: str) -> bool:
    return bool(
        re.search(r"\bwho\s+(?:was|is)\s+[a-z][a-z'. -]{1,60}\s+married\s+to\b", question)
        or (
            PLAYER_CONTEXT_RE.search(question) is not None
            and re.search(r"\b(?:spouse|wife|husband|partner|married)\b", question)
        )
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


def _mentions_default_teaching_request(question: str) -> bool:
    if _mentions_frustrated_learning_request(question):
        return True
    if _mentions_everyday_context_playing(question):
        return True
    if _mentions_b_c_pedal_skills_request(question):
        return True
    if _mentions_turnaround_teaching_request(question):
        return True
    if _mentions_chord_family_teaching_request(question):
        return True
    if _mentions_movement_request(question):
        return True
    if _mentions_progression_intro_request(question):
        return True
    if _mentions_pocket_request(question):
        return True
    if _mentions_lick_request(question):
        return True
    return bool(
        re.search(r"\b(?:tell\s+me\s+something|teach\s+me\s+something|one\s+thing|learn\s+something\s+new|might\s+not\s+already\s+know|how\s+to\s+play\s+anything|play\s+anything|just\s+one\s+thing|teach\s+me\s+anything|show\s+me\s+anything)\b", question)
        and re.search(r"\b(?:pedal\s+steel|steel\s+guitar|steel|e9|play)\b", question)
        and not re.search(r"\b(?:specific|song|tune)\b", question)
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


def _mentions_frustrated_learning_request(question: str) -> bool:
    return bool(
        re.search(r"\b(?:worse\s+than\s+google|not\s+a\s+teacher|aren't\s+a\s+teacher|are\s+not\s+a\s+teacher|answering\s+machine|you\s+cannot\s+teach|you\s+can't\s+teach)\b", question)
    )


def _mentions_everyday_context_playing(question: str) -> bool:
    return bool(
        re.search(r"\b(?:kitchen|chew\s+gum|gum)\b", question)
        and re.search(r"\b(?:play|practice|pedal\s+steel|steel\s+guitar|steel)\b", question)
    )


def _source_backed_steel_decision(question: str) -> AnswerIntentPayload | None:
    if re.search(r"\bhow\s+do\s+i\s+use\s+my\s+string\s+\d+\s+lower\b", question):
        return None
    if _mentions_visual_position(question):
        return None

    if PLAYER_CONTEXT_RE.search(question):
        return _source_backed_forum_decision()

    if re.search(r"\bbrands?\s+of\s+pedal\s+steel\b", question):
        return _source_backed_forum_decision()

    if BRAND_CONTEXT_RE.search(question):
        if _mentions_gear_diagnosis(question) and not re.search(r"\b(?:who|was|is)\b", question):
            return _gear_source_decision()
        return _source_backed_forum_decision()

    if GEAR_CONTEXT_RE.search(question):
        return _gear_source_decision()

    if VENDOR_ACCESSORY_RE.search(question) and (
        _mentions_steel(question)
        or re.search(
            r"\b(?:steel\s+players?|e9|pedal\s+steel|bjs|telonics|fender\s+steel\s+king|pac[-\s]?a[-\s]?seats?)\b",
            question,
        )
    ):
        if re.search(r"\b(?:diagnos|check|settings?|hum|buzz|breaking|battery|power|delay|effects?\s+loop)\b", question):
            return _gear_source_decision()
        return _source_backed_forum_decision()

    return None


def _source_backed_forum_decision() -> AnswerIntentPayload:
    return _decision(
        domain="steel_guitar",
        intent="forum_wisdom",
        needs_sources=True,
        needs_fretboard=False,
        needs_copedent=False,
        retrieval_allowed=True,
        allowed_answer_shape="source_backed",
    )


def _gear_source_decision() -> AnswerIntentPayload:
    return _decision(
        domain="steel_guitar",
        intent="gear_diagnosis",
        needs_sources=True,
        needs_fretboard=False,
        needs_copedent=False,
        retrieval_allowed=True,
        allowed_answer_shape="gear_diagnosis",
    )


def _mentions_visual_position(question: str) -> bool:
    if MISSING_CONTEXT_VISUAL_RE.search(question):
        return False
    if BUYING_RE.search(question):
        return False
    if PRACTICE_RE.search(question) and not VISUAL_POSITION_RE.search(question):
        return False
    if VISUAL_POSITION_RE.search(question) and (
        EXPLICIT_VISUAL_OBJECT_RE.search(question)
        or re.search(r"\b(?:a\s*\+\s*b|a\s*\+\s*f|b\s*\+\s*c|e[-\s]?lower)\b", question)
        or CONCRETE_CHORD_RE.search(question)
    ):
        return True
    if re.search(r"\bhow\s+do\s+(?:i|you)\s+(?:play|make)\b", question) and CONCRETE_CHORD_RE.search(question):
        return True
    if re.search(r"\b(?:what\s+frets?|frets?\s+give)\b", question) and CONCRETE_CHORD_RE.search(question):
        return True
    if POSITION_LANGUAGE_RE.search(question) and re.search(r"\b(?:from|after|for)\s+(?:a\s*\+\s*b|a\s*\+\s*f|b\s*\+\s*c|e[-\s]?lower)\b", question):
        return True
    return False
