"""Derive reviewable, source-safe ranking decisions from normalized steel events."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any

from steel_guitar_rag.copedent_transfer import absolute_pitch_for_profile, candidate_control_states
from steel_guitar_rag.e9_copedents import E9CopedentProfile, get_e9_copedent_profile, scientific_pitch_for_value
from steel_guitar_rag.melody_ranker_adapter import candidate_feature_record


DECISION_DERIVATION_VERSION = "score-tab-decision-derivation-v5"


def _stable_id(*values: object) -> str:
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"decision-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _actions(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not bool(event.get("derivedMovementEligibility", {}).get("eligible", True)):
        return []
    actions = [
        dict(action)
        for action in event.get("steelActions") or []
        if isinstance(action, Mapping)
        and action.get("soundingPitchValue") is not None
        and action.get("string") is not None
        and action.get("fret") is not None
        and bool(action.get("mechanicalValidation", {}).get("valid"))
    ]
    return sorted(actions, key=lambda action: (int(action["soundingPitchValue"]), -int(action["string"])))


def _controls(actions: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        str(control)
        for action in actions
        for control in action.get("controls") or []
    }


def _ranker_signature(candidate: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        max(1, min(3, int(candidate.get("textureSize") or 1))),
        int(candidate.get("attackVoices") or 0),
        float(candidate.get("barTravel") or 0),
        float(candidate.get("controlChanges") or 0),
        float(candidate.get("pocketChanges") or 0),
        float(candidate.get("voiceLeading") or 0),
        float(candidate.get("sustainedVoices") or 0),
        float(candidate.get("repickedVoices") or 0),
        str(candidate.get("phraseRole") or ""),
    )


def _candidate(
    actions: Sequence[Mapping[str, Any]],
    previous_actions: Sequence[Mapping[str, Any]],
    *,
    phrase_role: str,
    next_actions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return candidate_feature_record(
        actions,
        previous_actions,
        phrase_role=phrase_role,
        next_actions=next_actions,
    )


def _single_note_alternatives(
    profile: E9CopedentProfile,
    *,
    target_pitch: int,
    source_top: Mapping[str, Any],
    previous_actions: Sequence[Mapping[str, Any]],
    phrase_role: str,
    chosen: Mapping[str, Any],
    next_actions: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    previous_by_string = {int(action["string"]): action for action in previous_actions}
    controls_by_id = profile.controls_by_id()
    source_signature = (
        int(source_top["string"]),
        int(source_top["fret"]),
        tuple(sorted(str(value) for value in source_top.get("controls") or [])),
    )
    candidates: list[tuple[tuple[object, ...], dict[str, Any]]] = []
    for string, open_pitch in sorted(profile.open_pitch_values_by_string().items()):
        control_options: list[tuple[str, ...]] = [()]
        control_options.extend(
            (control.id,)
            for control in profile.ordered_controls()
            if string in control.affected_strings
        )
        for controls in control_options:
            delta = sum(
                change.semitones
                for control_id in controls
                for change in controls_by_id[control_id].changes
                if change.string == string
            )
            fret = target_pitch - int(open_pitch) - delta
            if fret < 0 or fret > 36:
                continue
            if (string, fret, tuple(sorted(controls))) == source_signature:
                continue
            sustained = int(
                string in previous_by_string
                and int(previous_by_string[string]["soundingPitchValue"]) == target_pitch
            )
            candidate = candidate_feature_record(
                [
                    {
                        "string": int(string),
                        "fret": int(fret),
                        "controls": sorted(str(value) for value in controls),
                        "soundingPitchValue": int(target_pitch),
                        "attack": True,
                    }
                ],
                previous_actions,
                phrase_role=phrase_role,
                next_actions=next_actions,
            )
            # Preserve the frozen alternative semantics: holding the same
            # string/pitch is counted as sustain even though its concrete
            # review projection remains an explicit attack candidate.
            candidate["sustainedVoices"] = sustained
            candidate["repickedVoices"] = int(
                string in previous_by_string and not sustained
            )
            signature = _ranker_signature(candidate)
            if signature == _ranker_signature(chosen):
                continue
            candidates.append(((candidate["barTravel"], candidate["controlChanges"], string, fret, controls), candidate))
    alternatives: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()
    for _order, candidate in sorted(candidates, key=lambda item: item[0]):
        ranker_signature = _ranker_signature(candidate)
        if ranker_signature in seen:
            continue
        seen.add(ranker_signature)
        alternatives.append(candidate)
        if len(alternatives) == 3:
            break
    return alternatives


@lru_cache(maxsize=4096)
def _mechanical_voice_solutions(
    profile_id: str,
    profile_revision: int,
    voice_pitches: tuple[int, ...],
) -> tuple[tuple[int, tuple[str, ...], tuple[tuple[int, int, tuple[str, ...]], ...]], ...]:
    profile = get_e9_copedent_profile(profile_id)
    if profile.revision != profile_revision:
        return ()
    controls_by_id = profile.controls_by_id()
    solutions: set[tuple[int, tuple[str, ...], tuple[tuple[int, int, tuple[str, ...]], ...]]] = set()
    ordered_pitches = tuple(sorted((int(value) for value in voice_pitches), reverse=True))
    for state in candidate_control_states(profile):
        normalized_state = tuple(sorted(state))
        for fret in range(37):
            options_by_pitch = {
                pitch: tuple(
                    string
                    for string in sorted(profile.open_pitch_values_by_string())
                    if absolute_pitch_for_profile(profile, string, fret, state) == pitch
                )
                for pitch in set(ordered_pitches)
            }
            if any(not options_by_pitch[pitch] for pitch in ordered_pitches):
                continue

            assignments: list[tuple[int, int]] = []

            def assign(index: int, used_strings: set[int]) -> None:
                if index == len(ordered_pitches):
                    action_rows = tuple(
                        sorted(
                            (
                                string,
                                pitch,
                                tuple(
                                    control_id
                                    for control_id in normalized_state
                                    if string in controls_by_id[control_id].affected_strings
                                ),
                            )
                            for pitch, string in assignments
                        )
                    )
                    used_controls = {
                        control_id for _string, _pitch, controls in action_rows for control_id in controls
                    }
                    if used_controls == set(normalized_state):
                        solutions.add((fret, normalized_state, action_rows))
                    return
                pitch = ordered_pitches[index]
                for string in options_by_pitch[pitch]:
                    if string in used_strings:
                        continue
                    assignments.append((pitch, string))
                    assign(index + 1, used_strings | {string})
                    assignments.pop()

            assign(0, set())
    return tuple(sorted(solutions))


def _voice_preserving_alternatives(
    profile: E9CopedentProfile,
    *,
    actions: Sequence[Mapping[str, Any]],
    previous_actions: Sequence[Mapping[str, Any]],
    phrase_role: str,
    chosen: Mapping[str, Any],
    next_actions: Sequence[Mapping[str, Any]] = (),
    limit: int = 3,
) -> list[dict[str, Any]]:
    voice_pitches = tuple(sorted(int(action["soundingPitchValue"]) for action in actions))
    source_signature = tuple(
        sorted(
            (
                int(action["string"]),
                int(action["fret"]),
                tuple(sorted(str(value) for value in action.get("controls") or [])),
            )
            for action in actions
        )
    )
    candidates: list[tuple[tuple[object, ...], dict[str, Any]]] = []
    for fret, _state, rows in _mechanical_voice_solutions(profile.id, profile.revision, voice_pitches):
        signature = tuple(sorted((string, fret, controls) for string, _pitch, controls in rows))
        if signature == source_signature:
            continue
        candidate_actions = [
            {
                "string": string,
                "fret": fret,
                "controls": list(controls),
                "soundingPitchValue": pitch,
                "mechanicalValidation": {"valid": True},
            }
            for string, pitch, controls in rows
        ]
        candidate = _candidate(
            candidate_actions,
            previous_actions,
            phrase_role=phrase_role,
            next_actions=next_actions,
        )
        if _ranker_signature(candidate) == _ranker_signature(chosen):
            continue
        candidates.append(
            (
                (
                    candidate["barTravel"],
                    candidate["controlChanges"],
                    candidate["pocketChanges"],
                    candidate["voiceLeading"],
                    signature,
                ),
                candidate,
            )
        )
    alternatives: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()
    for _order, candidate in sorted(candidates, key=lambda item: item[0]):
        ranker_signature = _ranker_signature(candidate)
        if ranker_signature in seen:
            continue
        seen.add(ranker_signature)
        alternatives.append(candidate)
        if len(alternatives) == limit:
            break
    return alternatives


def _phrase_role(
    event_index: int,
    event_count: int,
    previous_actions: Sequence[Mapping[str, Any]],
    current_actions: Sequence[Mapping[str, Any]],
    movement: Mapping[str, Any] | None,
) -> str:
    concepts = {
        str(item.get("concept"))
        for item in (movement or {}).get("classifications") or []
        if isinstance(item, Mapping)
    }
    if "pedal_release" in concepts:
        return "resolution"
    if event_index == event_count:
        return "chord_arrival" if len(current_actions) > 1 else "cadence"
    previous_top = max(previous_actions, key=lambda action: int(action["soundingPitchValue"]))
    current_top = max(current_actions, key=lambda action: int(action["soundingPitchValue"]))
    if int(previous_top["soundingPitchValue"]) == int(current_top["soundingPitchValue"]):
        return "sustained_note"
    return "passing_tone"


def derive_decision_annotations(
    record: Mapping[str, Any],
    profile: E9CopedentProfile,
) -> list[dict[str, Any]]:
    """Create source-safe proposals that remain ineligible until page approval."""

    movements = {
        str(item.get("toTabEventId")): item
        for item in record.get("movementSequences") or []
        if isinstance(item, Mapping) and item.get("toTabEventId")
    }
    page_type = str(record.get("pageClassification", {}).get("primary") or "unknown")
    source_document = str(record.get("sourceDocumentId") or "unknown")
    source_structure = record.get("sourceStructure") or {}
    tab_event_count = sum(
        len(system.get("tabEvents") or []) for system in record.get("tabSystems") or []
    )
    notation_density = "low" if tab_event_count <= 10 else "middle" if tab_event_count <= 25 else "high"
    unusual_symbols = {
        str(item.get("kind"))
        for item in record.get("unresolved") or []
        if isinstance(item, Mapping) and item.get("kind")
    }
    page_concepts = {
        str(item.get("concept"))
        for item in record.get("teachingConcepts") or []
        if isinstance(item, Mapping) and item.get("concept")
    }
    score_events_by_id = {
        str(event.get("scoreEventId")): event
        for system in record.get("scoreSystems") or []
        for event in system.get("scoreEvents") or []
        if isinstance(event, Mapping) and event.get("scoreEventId")
    }
    verified_alignments_by_tab: dict[str, dict[str, Any]] = {}
    for alignment in record.get("eventAlignments") or []:
        if not isinstance(alignment, Mapping):
            continue
        exact_pitch = bool(alignment.get("notationAdjustedPitchAgreement"))
        reviewed_melody_to_grip = (
            alignment.get("alignmentType") == "melody_top_note_to_grip"
            and alignment.get("reviewState") == "human_approved"
            and alignment.get("pitchToTabTrainingEligible") is True
            and alignment.get("scoreRhythmTrainingEligible") is False
        )
        reviewed_sustain_movement = (
            alignment.get("alignmentType") == "sustained_score_to_control_movement"
            and alignment.get("reviewState") == "human_approved"
            and alignment.get("pitchToTabTrainingEligible") is True
            and alignment.get("scoreRhythmTrainingEligible") is False
        )
        if not exact_pitch and not reviewed_melody_to_grip and not reviewed_sustain_movement:
            continue
        for tab_event_id in alignment.get("tabEventIds") or []:
            verified_alignments_by_tab[str(tab_event_id)] = dict(alignment)
    has_score_facts = bool(score_events_by_id)

    def score_support(event: Mapping[str, Any], actions: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
        alignment = verified_alignments_by_tab.get(str(event.get("tabEventId")))
        if alignment is None:
            return None
        score_pitches = [
            int(score_events_by_id[str(event_id)]["pitchValue"])
            for event_id in alignment.get("scoreEventIds") or []
            if str(event_id) in score_events_by_id
            and score_events_by_id[str(event_id)].get("pitchValue") is not None
        ]
        if not score_pitches:
            return None
        if alignment.get("alignmentType") == "sustained_score_to_control_movement":
            return {
                "eventAlignmentId": alignment.get("eventAlignmentId"),
                "scoreEventIds": list(alignment.get("scoreEventIds") or []),
                "scoreNotationTranspositionSemitones": 0,
                "melodyTopAgreement": False,
                "movementDuringSustain": True,
            }
        top_action = max(actions, key=lambda action: int(action["soundingPitchValue"]))
        offset = int(alignment.get("scoreNotationTranspositionSemitones") or 0)
        if int(top_action["soundingPitchValue"]) + offset != max(score_pitches):
            return None
        return {
            "eventAlignmentId": alignment.get("eventAlignmentId"),
            "scoreEventIds": list(alignment.get("scoreEventIds") or []),
            "scoreNotationTranspositionSemitones": offset,
            "melodyTopAgreement": True,
        }

    decisions: list[dict[str, Any]] = []
    for system in record.get("tabSystems") or []:
        events = [event for event in system.get("tabEvents") or [] if _actions(event)]
        for current_index in range(1, len(events)):
            event_index = current_index + 1
            previous_event = events[current_index - 1]
            current_event = events[current_index]
            previous_actions = _actions(previous_event)
            current_actions = _actions(current_event)
            next_actions = (
                _actions(events[current_index + 1])
                if current_index + 1 < len(events)
                else []
            )
            previous_score_support = score_support(previous_event, previous_actions) if has_score_facts else None
            current_score_support = score_support(current_event, current_actions) if has_score_facts else None
            if has_score_facts and (previous_score_support is None or current_score_support is None):
                continue
            evidence_mode = "score_supported" if has_score_facts else "tab_only"
            movement = movements.get(str(current_event.get("tabEventId")))
            phrase_role = _phrase_role(
                event_index,
                len(events),
                previous_actions,
                current_actions,
                movement,
            )
            chosen = _candidate(
                current_actions,
                previous_actions,
                phrase_role=phrase_role,
                next_actions=next_actions,
            )
            source_top = max(current_actions, key=lambda action: int(action["soundingPitchValue"]))
            target_pitch = int(source_top["soundingPitchValue"])
            alternatives = _voice_preserving_alternatives(
                profile,
                actions=current_actions,
                previous_actions=previous_actions,
                next_actions=next_actions,
                phrase_role=phrase_role,
                chosen=chosen,
            )
            if len(alternatives) < 3:
                seen_alternatives = {_ranker_signature(candidate) for candidate in alternatives}
                for candidate in _single_note_alternatives(
                    profile,
                    target_pitch=target_pitch,
                    source_top=source_top,
                    previous_actions=previous_actions,
                    next_actions=next_actions,
                    phrase_role=phrase_role,
                    chosen=chosen,
                ):
                    signature = _ranker_signature(candidate)
                    if signature in seen_alternatives:
                        continue
                    seen_alternatives.add(signature)
                    alternatives.append(candidate)
                    if len(alternatives) == 3:
                        break
            if not alternatives:
                continue
            current_by_string = {int(action["string"]): action for action in current_actions}
            previous_by_string = {int(action["string"]): action for action in previous_actions}
            attack_strings = sorted(
                string for string, action in current_by_string.items() if bool(action.get("attack", True))
            )
            sustained_strings = sorted(
                string for string, action in current_by_string.items() if not bool(action.get("attack", True))
            )
            sounding_strings = sorted(current_by_string)
            released_strings = sorted(set(previous_by_string) - set(current_by_string))
            repicked_strings = sorted(set(attack_strings) & set(previous_by_string))
            start_pitch_value = profile.open_pitch_values_by_string()[int(source_top["string"])] + int(source_top["fret"])
            controls = sorted(str(value) for value in source_top.get("controls") or [])
            movement_concepts = {
                str(item.get("concept"))
                for item in (movement or {}).get("classifications") or []
                if isinstance(item, Mapping) and item.get("concept")
            }
            category_tags = sorted(
                {
                    f"page:{page_type}",
                    f"source_sequence:{source_document}",
                    f"notation_density:{notation_density}",
                    f"orientation:{source_structure.get('orientation', 'unknown')}",
                    f"image_luminance:{source_structure.get('luminanceBin', 'unknown')}",
                    f"image_density:{source_structure.get('densityBin', 'unknown')}",
                    f"alignment:{evidence_mode}",
                }
                | {f"movement:{concept}" for concept in movement_concepts}
                | {f"concept:{concept}" for concept in page_concepts}
                | {f"unusual_symbol:{kind}" for kind in unusual_symbols}
            )
            if not attack_strings:
                style = "lever_driven"
            elif chosen["barTravel"] == 0 and chosen["controlChanges"]:
                style = "lever_driven"
            elif len(current_actions) == 1:
                style = "single_note_run"
            elif len(current_actions) == 2:
                style = "harmonized"
            else:
                style = "chord_melody"
            decision_id = _stable_id(
                DECISION_DERIVATION_VERSION,
                record.get("batchId"),
                record.get("inputId"),
                current_event.get("tabEventId"),
            )
            decisions.append(
                {
                    "schemaVersion": "melody-decision-annotation-v2",
                    "decisionDerivationVersion": DECISION_DERIVATION_VERSION,
                    "decisionId": decision_id,
                    "inputId": record.get("inputId"),
                    "sourceCopedentId": profile.id,
                    "sourceCopedentRevision": profile.revision,
                    "styleFamily": style,
                    "phraseRole": phrase_role,
                    "datasetPartition": record.get("datasetPartition"),
                    "benchmarkGroup": page_type,
                    "categoryTags": category_tags,
                    "reviewStatus": "needs_review",
                    "confidence": round(
                        min(float(action.get("confidence") or 0.0) for action in current_actions),
                        4,
                    ),
                    "evidenceClass": "interpretive_inference",
                    "sourceAction": {
                        "string": int(source_top["string"]),
                        "fret": int(source_top["fret"]),
                        "startPitch": scientific_pitch_for_value(start_pitch_value),
                        "destinationPitch": scientific_pitch_for_value(target_pitch),
                        "semitoneChange": target_pitch - start_pitch_value,
                        "controls": controls,
                        "attack": bool(source_top.get("attack", True)),
                        "soundingStrings": sounding_strings,
                        "sustainedStrings": sustained_strings,
                    },
                    "abstractDecision": {
                        "melodyPitch": scientific_pitch_for_value(target_pitch),
                        "melodyPitchValue": target_pitch,
                        "melodyRegister": (target_pitch // 12) - 1,
                        "textureSize": len(current_actions),
                        "attackVoices": attack_strings,
                        "sustainedVoices": sustained_strings,
                        "releasedVoices": released_strings,
                        "repickedVoices": repicked_strings,
                        "executionType": chosen.get("executionType", "attack"),
                        "phraseRole": phrase_role,
                        "harmonicFunction": "arrival" if phrase_role in {"cadence", "chord_arrival", "resolution"} else "motion",
                        "pocketRole": "stay" if chosen["barTravel"] == 0 else "move",
                    },
                    "chosen": chosen,
                    "alternatives": alternatives,
                    "sourceTabEventId": current_event.get("tabEventId"),
                    "sourceMovementSequenceId": (movement or {}).get("movementSequenceId"),
                    "scoreToTabSupport": {
                        "mode": evidence_mode,
                        "previous": previous_score_support,
                        "current": current_score_support,
                    },
                    "reviewState": "needs_human_review",
                }
            )
    return decisions


__all__ = ["DECISION_DERIVATION_VERSION", "derive_decision_annotations"]
