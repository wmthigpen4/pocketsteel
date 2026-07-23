"""Shared trainer/runtime adapter for Amazing Tablature ranker features.

The pairwise trainer learns from abstract mechanical actions, while Melody
Studio ranks :class:`~pocketsteel.melody_models.PositionCandidate` objects.
This module is the single translation boundary between those representations.
It deliberately contains no learned weights and no source-specific material.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pocketsteel.copedent_transfer import (
    absolute_pitch_for_profile,
    control_affects_string,
)
from pocketsteel.e9_copedents import E9CopedentProfile
from pocketsteel.melody_models import PositionCandidate
from pocketsteel.melody_ranker import FEATURE_NAMES, feature_vector


def _direction(value: int) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def _normalized_actions(
    actions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    normalized = [
        {
            "string": int(action["string"]),
            "fret": int(action["fret"]),
            "controls": sorted(str(value) for value in action.get("controls") or []),
            "soundingPitchValue": int(action["soundingPitchValue"]),
            "attack": bool(action.get("attack", True)),
        }
        for action in actions
    ]
    return sorted(
        normalized,
        key=lambda action: (
            int(action["string"]),
            int(action["fret"]),
            tuple(action["controls"]),
        ),
    )


def _controls(actions: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        str(control)
        for action in actions
        for control in action.get("controls") or []
    }


def candidate_feature_record(
    actions: Sequence[Mapping[str, Any]],
    previous_actions: Sequence[Mapping[str, Any]],
    *,
    phrase_role: str,
    next_actions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build the canonical raw candidate record consumed by the trainer.

    A candidate is intentionally transition-scoped: the current movement must
    have a previous state, and its second-order fields optionally describe the
    following state. The first melody event therefore has no learned score.
    """

    current = _normalized_actions(actions)
    previous = _normalized_actions(previous_actions)
    following = _normalized_actions(next_actions)
    if not current or not previous:
        raise ValueError("Ranker candidates require current and previous actions.")

    current_by_string = {int(action["string"]): action for action in current}
    previous_by_string = {int(action["string"]): action for action in previous}
    current_top = max(current, key=lambda action: int(action["soundingPitchValue"]))
    previous_top = max(
        previous, key=lambda action: int(action["soundingPitchValue"])
    )
    current_pitches = [int(action["soundingPitchValue"]) for action in current]
    previous_pitches = [int(action["soundingPitchValue"]) for action in previous]
    attacked_strings = {
        string
        for string, action in current_by_string.items()
        if bool(action.get("attack", True))
    }
    sustained_strings = {
        string
        for string, action in current_by_string.items()
        if not bool(action.get("attack", True))
    }
    common_strings = current_by_string.keys() & previous_by_string.keys()

    incoming_fret_direction = _direction(
        int(current_top["fret"]) - int(previous_top["fret"])
    )
    incoming_string_direction = _direction(
        int(current_top["string"]) - int(previous_top["string"])
    )
    sequence_features: dict[str, int] = {
        "incomingStringDistance": abs(
            int(current_top["string"]) - int(previous_top["string"])
        ),
        "incomingFretDirection": incoming_fret_direction,
        "incomingStringDirection": incoming_string_direction,
        "outgoingBarTravel": 0,
        "outgoingControlChanges": 0,
        "outgoingStringDistance": 0,
        "outgoingFretDirection": 0,
        "outgoingStringDirection": 0,
        "outgoingSustainContinuity": 0,
        "fretDirectionReversal": 0,
        "fretDirectionContinuation": 0,
        "stringDirectionReversal": 0,
        "stringDirectionContinuation": 0,
    }
    if following:
        next_top = max(
            following, key=lambda action: int(action["soundingPitchValue"])
        )
        outgoing_fret_direction = _direction(
            int(next_top["fret"]) - int(current_top["fret"])
        )
        outgoing_string_direction = _direction(
            int(next_top["string"]) - int(current_top["string"])
        )
        current_strings = {int(action["string"]) for action in current}
        next_sustained_strings = {
            int(action["string"])
            for action in following
            if not bool(action.get("attack", True))
        }
        sequence_features.update(
            {
                "outgoingBarTravel": abs(
                    int(next_top["fret"]) - int(current_top["fret"])
                ),
                "outgoingControlChanges": len(
                    _controls(following) ^ _controls(current)
                ),
                "outgoingStringDistance": abs(
                    int(next_top["string"]) - int(current_top["string"])
                ),
                "outgoingFretDirection": outgoing_fret_direction,
                "outgoingStringDirection": outgoing_string_direction,
                "outgoingSustainContinuity": len(
                    current_strings & next_sustained_strings
                ),
                "fretDirectionReversal": int(
                    incoming_fret_direction * outgoing_fret_direction < 0
                ),
                "fretDirectionContinuation": int(
                    incoming_fret_direction != 0
                    and incoming_fret_direction == outgoing_fret_direction
                ),
                "stringDirectionReversal": int(
                    incoming_string_direction * outgoing_string_direction < 0
                ),
                "stringDirectionContinuation": int(
                    incoming_string_direction != 0
                    and incoming_string_direction == outgoing_string_direction
                ),
            }
        )

    record = {
        "textureSize": len(current),
        "attackVoices": len(attacked_strings),
        "barTravel": abs(int(current_top["fret"]) - int(previous_top["fret"])),
        "controlChanges": len(_controls(current) ^ _controls(previous)),
        "pocketChanges": int(
            int(current_top["fret"]) != int(previous_top["fret"])
        ),
        "voiceLeading": sum(
            min(abs(pitch - previous_pitch) for previous_pitch in previous_pitches)
            for pitch in current_pitches
        ),
        "sustainedVoices": len(sustained_strings),
        "repickedVoices": len(common_strings & attacked_strings),
        "executionType": (
            "movement_only"
            if current and not attacked_strings
            else "mixed"
            if sustained_strings
            else "attack"
        ),
        "phraseRole": str(phrase_role or ""),
        "mechanicallyValid": True,
        "voicePitchValues": sorted(current_pitches),
        "mechanicalActions": current,
        **sequence_features,
    }
    # Fail closed if the shared ranker contract changes without this adapter.
    vector = feature_vector(record)
    if tuple(vector) != FEATURE_NAMES:
        raise ValueError("Runtime ranker adapter does not match the feature schema.")
    return record


def actions_for_position(
    candidate: PositionCandidate,
    profile: E9CopedentProfile,
    *,
    sustained_strings: Sequence[int] = (),
) -> list[dict[str, Any]]:
    """Project a runtime position into the trainer's mechanical-action shape."""

    sustained = {int(string) for string in sustained_strings}
    pitches = (
        tuple(int(value) for value in candidate.voice_pitches)
        if candidate.voice_pitches
        and len(candidate.voice_pitches) == len(candidate.notes)
        else tuple(
            absolute_pitch_for_profile(
                profile,
                note.string,
                candidate.fret,
                candidate.controls,
            )
            for note in candidate.notes
        )
    )
    return _normalized_actions(
        [
            {
                "string": note.string,
                "fret": candidate.fret,
                "controls": [
                    control
                    for control in candidate.controls
                    if control_affects_string(profile, control, note.string)
                ],
                "soundingPitchValue": pitch,
                "attack": note.string not in sustained,
            }
            for note, pitch in zip(candidate.notes, pitches)
        ]
    )


def runtime_candidate_feature_record(
    previous: PositionCandidate,
    current: PositionCandidate,
    following: PositionCandidate | None,
    *,
    phrase_role: str,
    profile: E9CopedentProfile,
    current_sustained_strings: Sequence[int] = (),
    following_sustained_strings: Sequence[int] = (),
) -> dict[str, Any]:
    """Translate a runtime path triple into the canonical trainer record."""

    return candidate_feature_record(
        actions_for_position(
            current,
            profile,
            sustained_strings=current_sustained_strings,
        ),
        actions_for_position(previous, profile),
        phrase_role=phrase_role,
        next_actions=(
            actions_for_position(
                following,
                profile,
                sustained_strings=following_sustained_strings,
            )
            if following is not None
            else ()
        ),
    )


def runtime_feature_vector(
    previous: PositionCandidate,
    current: PositionCandidate,
    following: PositionCandidate | None,
    *,
    phrase_role: str,
    profile: E9CopedentProfile,
    current_sustained_strings: Sequence[int] = (),
    following_sustained_strings: Sequence[int] = (),
) -> dict[str, float]:
    """Return all 21 trainer features for one runtime movement."""

    vector = feature_vector(
        runtime_candidate_feature_record(
            previous,
            current,
            following,
            phrase_role=phrase_role,
            profile=profile,
            current_sustained_strings=current_sustained_strings,
            following_sustained_strings=following_sustained_strings,
        )
    )
    if tuple(vector) != FEATURE_NAMES:
        raise ValueError("Runtime ranker vector does not match the trainer feature order.")
    return vector


__all__ = [
    "actions_for_position",
    "candidate_feature_record",
    "runtime_candidate_feature_record",
    "runtime_feature_vector",
]
