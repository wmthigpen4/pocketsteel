"""Small copedent-neutral pairwise trainer for reviewed melody decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from pocketsteel.melody_decision_rules import RANKER_CONTRACT_VERSION, normalize_style_family


FEATURE_NAMES = (
    "texture_1",
    "texture_2",
    "texture_3",
    "bar_travel",
    "control_changes",
    "pocket_changes",
    "voice_leading",
    "sustained_voices",
    "repicked_voices",
    "disconnected_bar_travel",
    "controlled_move",
    "incoming_string_distance",
    "outgoing_bar_travel",
    "outgoing_control_changes",
    "outgoing_string_distance",
    "outgoing_sustain_continuity",
    "fret_direction_reversal",
    "fret_direction_continuation",
    "string_direction_reversal",
    "string_direction_continuation",
    "cadence_arrival",
)


@dataclass(frozen=True)
class RankerModel:
    model_version: str
    feature_names: tuple[str, ...]
    weights_by_style: dict[str, dict[str, float]]
    example_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "modelVersion": self.model_version,
            "featureNames": list(self.feature_names),
            "weightsByStyle": self.weights_by_style,
            "exampleCount": self.example_count,
            "copedentNeutral": True,
        }


def feature_vector(candidate: Mapping[str, object]) -> dict[str, float]:
    texture = max(1, min(3, int(candidate.get("textureSize") or 1)))
    bar_travel = float(candidate.get("barTravel") or 0)
    control_changes = float(candidate.get("controlChanges") or 0)
    pocket_changes = float(candidate.get("pocketChanges") or 0)
    repicked_voices = float(candidate.get("repickedVoices") or 0)
    return {
        "texture_1": 1.0 if texture == 1 else 0.0,
        "texture_2": 1.0 if texture == 2 else 0.0,
        "texture_3": 1.0 if texture == 3 else 0.0,
        "bar_travel": bar_travel,
        "control_changes": control_changes,
        "pocket_changes": pocket_changes,
        "voice_leading": float(candidate.get("voiceLeading") or 0),
        "sustained_voices": float(candidate.get("sustainedVoices") or 0),
        "repicked_voices": repicked_voices,
        # Distinguish a bar move that continues on an already sounding string
        # from a simultaneous bar-and-string-path jump.  The latter is a
        # separate practical cost even when both candidates sound the same.
        "disconnected_bar_travel": bar_travel if repicked_voices <= 0 else 0.0,
        # Expressive pedal/lever motion during a position change should not be
        # collapsed into the same global preference as an arbitrary bar move.
        "controlled_move": 1.0 if control_changes > 0 and pocket_changes > 0 else 0.0,
        "incoming_string_distance": float(candidate.get("incomingStringDistance") or 0),
        "outgoing_bar_travel": float(candidate.get("outgoingBarTravel") or 0),
        "outgoing_control_changes": float(candidate.get("outgoingControlChanges") or 0),
        "outgoing_string_distance": float(candidate.get("outgoingStringDistance") or 0),
        "outgoing_sustain_continuity": float(
            candidate.get("outgoingSustainContinuity") or 0
        ),
        "fret_direction_reversal": float(candidate.get("fretDirectionReversal") or 0),
        "fret_direction_continuation": float(
            candidate.get("fretDirectionContinuation") or 0
        ),
        "string_direction_reversal": float(candidate.get("stringDirectionReversal") or 0),
        "string_direction_continuation": float(
            candidate.get("stringDirectionContinuation") or 0
        ),
        "cadence_arrival": 1.0 if candidate.get("phraseRole") in {"cadence", "chord_arrival", "resolution"} else 0.0,
    }


def score_candidate(candidate: Mapping[str, object], weights: Mapping[str, float]) -> float:
    features = feature_vector(candidate)
    return sum(features[name] * float(weights.get(name, 0.0)) for name in FEATURE_NAMES)


def train_pairwise_ranker(
    records: Iterable[Mapping[str, object]],
    *,
    epochs: int = 20,
    learning_rate: float = 0.05,
    average_weights: bool = False,
) -> RankerModel:
    """Fit reviewed chosen-vs-alternative comparisons with a perceptron.

    Every record contains abstract musical features only.  Source frets,
    control letters, and copyrighted passage text are deliberately absent.
    Lower scores rank better at runtime.
    """

    examples: list[tuple[str, Mapping[str, object], Sequence[Mapping[str, object]], float]] = []
    for record in records:
        style = normalize_style_family(record.get("styleFamily") or "auto")
        chosen = record.get("chosen")
        alternatives = record.get("alternatives")
        if not isinstance(chosen, Mapping) or not isinstance(alternatives, list):
            raise ValueError("Each reviewed decision needs chosen and alternatives feature records.")
        clean_alternatives = [candidate for candidate in alternatives if isinstance(candidate, Mapping)]
        if not clean_alternatives:
            raise ValueError("Each reviewed decision needs at least one mechanically valid alternative.")
        evidence_weight = float(record.get("evidenceWeight") or 1.0)
        if evidence_weight <= 0:
            raise ValueError("Evidence weight must be positive.")
        examples.append((style, chosen, clean_alternatives, evidence_weight))

    weights_by_style: dict[str, dict[str, float]] = {}
    for style, _chosen, _alternatives, _evidence_weight in examples:
        weights_by_style.setdefault(style, {name: 0.0 for name in FEATURE_NAMES})
    weight_totals_by_style = {
        style: {name: 0.0 for name in FEATURE_NAMES} for style in weights_by_style
    }
    step_counts_by_style = {style: 0 for style in weights_by_style}
    for _epoch in range(max(1, int(epochs))):
        for style, chosen, alternatives, evidence_weight in examples:
            weights = weights_by_style[style]
            chosen_features = feature_vector(chosen)
            for alternative in alternatives:
                if score_candidate(chosen, weights) >= score_candidate(alternative, weights):
                    alternative_features = feature_vector(alternative)
                    for name in FEATURE_NAMES:
                        # Lower scores are better, so move the chosen vector down
                        # and the rejected vector up.
                        weights[name] += learning_rate * evidence_weight * (
                            alternative_features[name] - chosen_features[name]
                        )
                if average_weights:
                    step_counts_by_style[style] += 1
                    totals = weight_totals_by_style[style]
                    for name in FEATURE_NAMES:
                        totals[name] += weights[name]
    if average_weights:
        for style, weights in weights_by_style.items():
            step_count = step_counts_by_style[style]
            if step_count:
                totals = weight_totals_by_style[style]
                weights_by_style[style] = {
                    name: totals[name] / step_count for name in FEATURE_NAMES
                }
    return RankerModel(
        model_version=RANKER_CONTRACT_VERSION,
        feature_names=FEATURE_NAMES,
        weights_by_style=weights_by_style,
        example_count=len(examples),
    )
