"""Versioned, copedent-neutral rule contract for Melody Studio decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


MODEL_VERSION = "melody-decision-ranker-v1"
MODEL_STATUS = "seed"
SUPPORTED_STYLE_FAMILIES = {
    "auto",
    "vocal_steel",
    "chord_melody",
    "harmonized",
    "single_note_run",
    "lever_driven",
    "fixed_pocket",
}

STYLE_CATALOG: tuple[dict[str, object], ...] = (
    {
        "id": "auto",
        "label": "Best Fit",
        "description": "Balances phrase role, texture, movement, and the active copedent.",
        "reason": "Balances light motion with fuller arrivals and chooses the most coherent playable path.",
    },
    {
        "id": "vocal_steel",
        "label": "Singing Steel",
        "description": "Favors vocal phrasing, supported melody notes, and smooth releases.",
        "reason": "Uses singing support through sustained notes while keeping passing motion clear.",
    },
    {
        "id": "lever_driven",
        "label": "Pedal & Lever Motion",
        "description": "Favors expressive pitch movement under a steady bar.",
        "reason": "Looks for playable pedal and lever motion before adding unnecessary bar travel.",
    },
    {
        "id": "fixed_pocket",
        "label": "Pocket Playing",
        "description": "Favors one coherent fret and grip neighborhood.",
        "reason": "Keeps the phrase in a compact pocket unless a boundary or arrival justifies moving.",
    },
    {
        "id": "harmonized",
        "label": "Smooth Harmony",
        "description": "Favors consistent two-voice support and connected voice leading.",
        "reason": "Keeps harmony connected around the melody with a strong preference for smooth dyads.",
    },
    {
        "id": "single_note_run",
        "label": "Fast & Clean",
        "description": "Favors uncluttered single-note motion and economical picking paths.",
        "reason": "Keeps moving notes light and direct so the line stays clean at faster tempos.",
    },
    {
        "id": "chord_melody",
        "label": "Full Harmony",
        "description": "Favors rich voicings at sustained notes, arrivals, and cadences.",
        "reason": "Adds fuller harmony where the phrase is stable while preserving the melody on top.",
    },
)

RuleKind = Literal["hard_constraint", "soft_preference"]


@dataclass(frozen=True)
class DecisionRule:
    id: str
    musical_context: str
    phrase_role: tuple[str, ...]
    kind: RuleKind
    source_evidence: tuple[str, ...]
    style_families: tuple[str, ...]
    abstract_intent: str
    required_capabilities: tuple[str, ...]
    transfer_behavior: str
    fallback_behavior: str
    confidence: float
    model_version: str = MODEL_VERSION

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StylePolicy:
    id: str
    role_textures: tuple[tuple[str, int], ...]
    bar_move_weight: int = 1
    control_change_weight: int = 1
    pocket_change_weight: int = 1
    single_note_bias: int = 0
    dyad_bias: int = 0
    triad_bias: int = 0
    control_bias: int = 0

    def texture_for_role(self, role: str, default: int) -> int:
        return dict(self.role_textures).get(role, default)

    def texture_bias(self, size: int) -> int:
        return {1: self.single_note_bias, 2: self.dyad_bias, 3: self.triad_bias}.get(size, 0)


DECISION_RULES: tuple[DecisionRule, ...] = (
    DecisionRule(
        id="melody.pitch-register.exact-v1",
        musical_context="Every generated event",
        phrase_role=("all",),
        kind="hard_constraint",
        source_evidence=("reviewed-player-tab", "deterministic-pitch-validation"),
        style_families=tuple(sorted(SUPPORTED_STYLE_FAMILIES)),
        abstract_intent="Preserve the melody's exact pitch and register as the highest sounding voice.",
        required_capabilities=("target-pitch-enumeration", "voice-register-validation"),
        transfer_behavior="Re-enumerate the pitch on the target copedent; never copy the source fret or string blindly.",
        fallback_behavior="Try another position or smaller texture; report unavailable if the melody itself cannot be produced.",
        confidence=1.0,
    ),
    DecisionRule(
        id="mechanics.effects-not-labels-v1",
        musical_context="Source control transfer",
        phrase_role=("all",),
        kind="hard_constraint",
        source_evidence=("source-e9-abc-defg-v1",),
        style_families=tuple(sorted(SUPPORTED_STYLE_FAMILIES)),
        abstract_intent="Identify a pedal or lever by its per-string semitone effects, not its printed letter.",
        required_capabilities=("source-copedent", "target-copedent", "protected-string-set"),
        transfer_behavior="Allow a differently named target control when all sounding and sustained string effects match.",
        fallback_behavior="Reject label-only substitutions and continue with another position or reduced texture.",
        confidence=1.0,
    ),
    DecisionRule(
        id="texture.phrase-role-123-v1",
        musical_context="Melodic phrase texture",
        phrase_role=("pickup", "passing_tone", "sustained_note", "chord_arrival", "cadence", "resolution"),
        kind="soft_preference",
        source_evidence=("reviewed-player-tab", "one-two-three-string-pattern-review"),
        style_families=("auto", "vocal_steel", "chord_melody", "harmonized", "single_note_run"),
        abstract_intent="Use one voice for motion, two for singing support, and three for stable harmonic arrivals.",
        required_capabilities=("dyad-enumeration", "triad-enumeration", "phrase-role"),
        transfer_behavior="Rank mechanically valid target grips by phrase role rather than preserving the source grip.",
        fallback_behavior="Reduce triad to dyad to single melody while keeping pitch and register exact.",
        confidence=0.86,
    ),
    DecisionRule(
        id="movement.pocket-continuity-v1",
        musical_context="Adjacent phrase events",
        phrase_role=("all",),
        kind="soft_preference",
        source_evidence=("reviewed-player-tab", "melody-studio-held-out-fixtures"),
        style_families=("auto", "vocal_steel", "fixed_pocket", "harmonized"),
        abstract_intent="Prefer a coherent fret-and-grip pocket unless a phrase boundary or expressive arrival justifies movement.",
        required_capabilities=("bar-distance", "grip-family", "control-posture"),
        transfer_behavior="Measure continuity on the target copedent's available candidates.",
        fallback_behavior="Move to the closest valid alternate pocket before reducing texture.",
        confidence=0.82,
    ),
    DecisionRule(
        id="performance.attack-sustain-release-v1",
        musical_context="Audible bar or control transition",
        phrase_role=("resolution", "chord_arrival", "cadence", "sustained_note"),
        kind="soft_preference",
        source_evidence=("reviewed-player-tab", "score-tab-attack-comparison"),
        style_families=("auto", "vocal_steel", "lever_driven"),
        abstract_intent="Separate attacked voices from sustained, released, added, and repicked voices.",
        required_capabilities=("transition-voice-actions", "sustain-validation"),
        transfer_behavior="Create choreography only after both target endpoints validate mechanically.",
        fallback_behavior="Repick the target event cleanly when a safe sustained transition is unavailable.",
        confidence=0.78,
    ),
)


STYLE_POLICIES: dict[str, StylePolicy] = {
    "auto": StylePolicy(
        "auto",
        (("pickup", 1), ("passing_tone", 1), ("tension", 1), ("sustained_note", 2), ("resolution", 3), ("chord_arrival", 3), ("cadence", 3)),
    ),
    "vocal_steel": StylePolicy(
        "vocal_steel",
        (("pickup", 1), ("passing_tone", 2), ("tension", 2), ("sustained_note", 2), ("resolution", 2), ("chord_arrival", 3), ("cadence", 2)),
        bar_move_weight=1,
        control_change_weight=1,
        dyad_bias=-1,
    ),
    "chord_melody": StylePolicy(
        "chord_melody",
        (("pickup", 2), ("passing_tone", 2), ("tension", 2), ("sustained_note", 3), ("resolution", 3), ("chord_arrival", 3), ("cadence", 3)),
        triad_bias=-2,
        single_note_bias=2,
    ),
    "harmonized": StylePolicy(
        "harmonized",
        (("pickup", 2), ("passing_tone", 2), ("tension", 2), ("sustained_note", 2), ("resolution", 2), ("chord_arrival", 2), ("cadence", 2)),
        dyad_bias=-2,
    ),
    "single_note_run": StylePolicy(
        "single_note_run",
        tuple((role, 1) for role in ("pickup", "passing_tone", "tension", "sustained_note", "resolution", "chord_arrival", "cadence")),
        single_note_bias=-3,
        dyad_bias=3,
        triad_bias=6,
    ),
    "lever_driven": StylePolicy(
        "lever_driven",
        (("pickup", 1), ("passing_tone", 1), ("tension", 1), ("sustained_note", 2), ("resolution", 2), ("chord_arrival", 2), ("cadence", 2)),
        control_bias=-1,
    ),
    "fixed_pocket": StylePolicy(
        "fixed_pocket",
        (("pickup", 1), ("passing_tone", 1), ("tension", 1), ("sustained_note", 2), ("resolution", 2), ("chord_arrival", 3), ("cadence", 3)),
        bar_move_weight=3,
        pocket_change_weight=3,
    ),
}


def normalize_style_family(value: object) -> str:
    style = str(value or "auto").strip().lower().replace("-", "_")
    if style not in SUPPORTED_STYLE_FAMILIES:
        raise ValueError(f"Unsupported Melody Studio style family: {style}")
    return style


def style_policy(value: object) -> StylePolicy:
    return STYLE_POLICIES[normalize_style_family(value)]


def style_descriptor(value: object) -> dict[str, object]:
    style = normalize_style_family(value)
    return next(dict(item) for item in STYLE_CATALOG if item["id"] == style)


def style_catalog_payload() -> list[dict[str, object]]:
    return [dict(item) for item in STYLE_CATALOG]


def rule_contract_payload(style_family: object = "auto") -> dict[str, object]:
    style = normalize_style_family(style_family)
    descriptor = style_descriptor(style)
    return {
        "modelVersion": MODEL_VERSION,
        "modelStatus": MODEL_STATUS,
        "styleFamily": style,
        "styleLabel": descriptor["label"],
        "styleReason": descriptor["reason"],
        "styleCatalog": style_catalog_payload(),
        "rules": [rule.to_dict() for rule in DECISION_RULES],
        "fallbackOrder": [
            "equivalent_pitch_and_harmonic_function_other_position",
            "equivalent_melody_and_texture_different_grip",
            "reduce_triad_to_dyad_to_single_melody",
            "report_missing_copedent_capability",
        ],
    }
