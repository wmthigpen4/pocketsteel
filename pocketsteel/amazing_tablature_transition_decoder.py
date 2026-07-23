"""Conservative source-transition decoding for reviewed tablature systems.

This module is intentionally separate from the Amazing Tablature arrangement
ranker.  It learns how one source cohort denotes an unpicked bar or control
movement; it does not decide which movement a new melody should use.

The decoder is precision-first and may abstain.  A transition is emitted as
``movement_only`` or ``attack`` only when an exact signature has repeated
label-pure support across independent discovery content units. Everything else
remains unresolved for another source-evidence reader or human review.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


TRANSITION_FEATURE_SCHEMA_VERSION = "amazing-tablature-transition-features-v1"
TRANSITION_DECODER_SCHEMA_VERSION = "amazing-tablature-transition-decoder-v2"
DEFAULT_MINIMUM_SUPPORT = 5
DEFAULT_MINIMUM_CONTENT_UNITS = 3
DEFAULT_MINIMUM_PRECISION = 0.995


class TransitionDecoderError(ValueError):
    """Raised when transition evidence violates the decoder contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _event_actions(event: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    actions: dict[int, dict[str, Any]] = {}
    for raw_action in event.get("steelActions") or ():
        if not isinstance(raw_action, Mapping):
            raise TransitionDecoderError("A transition action is not an object.")
        string = raw_action.get("string")
        fret = raw_action.get("fret")
        pitch = raw_action.get("soundingPitchValue")
        if (
            isinstance(string, bool)
            or not isinstance(string, (int, float))
            or isinstance(fret, bool)
            or not isinstance(fret, (int, float))
            or isinstance(pitch, bool)
            or not isinstance(pitch, (int, float))
        ):
            raise TransitionDecoderError(
                "Every transition action requires numeric string, fret, and sounding pitch."
            )
        string_number = int(string)
        if string_number in actions:
            raise TransitionDecoderError(
                "A transition state cannot contain duplicate actions for one string."
            )
        controls = raw_action.get("controls") or ()
        if not isinstance(controls, (list, tuple)):
            raise TransitionDecoderError("Transition controls must be a list.")
        actions[string_number] = {
            "string": string_number,
            "fret": int(fret),
            "controls": tuple(sorted(str(value) for value in controls)),
            "soundingPitchValue": int(pitch),
        }
    if not actions:
        raise TransitionDecoderError("A transition state cannot be blank.")
    return actions


def transition_feature_signature(
    previous_event: Mapping[str, Any],
    current_event: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact trainer/runtime feature signature for two tab states."""

    previous = _event_actions(previous_event)
    current = _event_actions(current_event)
    previous_strings = set(previous)
    current_strings = set(current)
    common_strings = sorted(previous_strings & current_strings)
    control_transitions = [
        {
            "string": string,
            "from": list(previous[string]["controls"]),
            "to": list(current[string]["controls"]),
        }
        for string in common_strings
        if previous[string]["controls"] != current[string]["controls"]
    ]
    fret_deltas = [
        {
            "string": string,
            "delta": current[string]["fret"] - previous[string]["fret"],
        }
        for string in common_strings
    ]
    pitch_deltas = [
        {
            "string": string,
            "delta": (
                current[string]["soundingPitchValue"]
                - previous[string]["soundingPitchValue"]
            ),
        }
        for string in common_strings
    ]
    return {
        "featureSchemaVersion": TRANSITION_FEATURE_SCHEMA_VERSION,
        "sameStringSet": previous_strings == current_strings,
        "currentStrings": sorted(current_strings),
        "controlTransitions": control_transitions,
        "fretDeltas": fret_deltas,
        "pitchDeltas": pitch_deltas,
    }


def _mechanically_admissible(signature: Mapping[str, Any]) -> bool:
    """Limit learning to repeated source gestures that can safely mean a hold."""

    if signature.get("sameStringSet") is not True:
        return False
    current_strings = signature.get("currentStrings") or ()
    if not current_strings:
        return False
    control_transitions = signature.get("controlTransitions") or ()
    fret_deltas = [
        int(value.get("delta") or 0)
        for value in signature.get("fretDeltas") or ()
        if isinstance(value, Mapping)
    ]
    if control_transitions:
        return True
    if not fret_deltas:
        return False
    return any(abs(value) >= 2 for value in fret_deltas) or all(
        value < 0 for value in fret_deltas
    )


def transition_training_rows(
    reviewed_record: Mapping[str, Any],
    *,
    source_cohort_id: str,
) -> list[dict[str, Any]]:
    """Extract source-only transition rows from one approved discovery record."""

    content_unit_id = str(
        reviewed_record.get("contentUnitId")
        or reviewed_record.get("inputId")
        or ""
    )
    if not content_unit_id:
        raise TransitionDecoderError("A reviewed record requires a content-unit identity.")
    input_id = str(reviewed_record.get("inputId") or "")
    rows: list[dict[str, Any]] = []
    for tab_system in reviewed_record.get("tabSystems") or ():
        if not isinstance(tab_system, Mapping):
            continue
        tab_system_id = str(tab_system.get("tabSystemId") or "")
        events = [
            event
            for event in tab_system.get("tabEvents") or ()
            if isinstance(event, Mapping)
        ]
        for prior, current in zip(events, events[1:]):
            execution_type = str(current.get("executionType") or "")
            if execution_type not in {"attack", "movement_only"}:
                continue
            try:
                signature = transition_feature_signature(prior, current)
            except TransitionDecoderError:
                continue
            rows.append(
                {
                    "sourceCohortId": source_cohort_id,
                    "contentUnitId": content_unit_id,
                    "inputId": input_id,
                    "tabSystemId": tab_system_id,
                    "eventIndex": int(current.get("eventIndex") or 0),
                    "signature": signature,
                    "label": execution_type,
                }
            )
    return rows


def _learned_signatures(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_support: int,
    minimum_content_units: int,
    minimum_precision: float,
) -> dict[str, dict[str, Any]]:
    statistics: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "support": 0,
            "labelCounts": {"attack": 0, "movement_only": 0},
            "contentUnitIds": set(),
            "signature": None,
        }
    )
    for row in rows:
        signature = row.get("signature")
        if not isinstance(signature, Mapping):
            continue
        label = str(row.get("label") or "")
        if label not in {"attack", "movement_only"}:
            continue
        key = _canonical_json(signature)
        current = statistics[key]
        current["support"] += 1
        current["labelCounts"][label] += 1
        current["contentUnitIds"].add(str(row.get("contentUnitId") or ""))
        current["signature"] = dict(signature)
    accepted: dict[str, dict[str, Any]] = {}
    for key, values in statistics.items():
        support = int(values["support"])
        content_units = {
            value for value in values["contentUnitIds"] if value
        }
        label_counts = {
            label: int(count)
            for label, count in values["labelCounts"].items()
        }
        label = max(
            sorted(label_counts),
            key=lambda value: label_counts[value],
        )
        label_count = label_counts[label]
        precision = label_count / support if support else 0.0
        if (
            support >= minimum_support
            and len(content_units) >= minimum_content_units
            and precision >= minimum_precision
            and (
                label == "attack"
                or _mechanically_admissible(values["signature"])
            )
        ):
            accepted[key] = {
                "signature": values["signature"],
                "signatureDigest": _sha256_json(values["signature"]),
                "label": label,
                "support": support,
                "labelCount": label_count,
                "labelCounts": label_counts,
                "precision": precision,
                "contentUnitCount": len(content_units),
            }
    return accepted


def _grouped_cross_validation(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_support: int,
    minimum_content_units: int,
    minimum_precision: float,
) -> dict[str, Any]:
    groups = sorted(
        {
            str(row.get("contentUnitId") or "")
            for row in rows
            if row.get("contentUnitId")
        }
    )
    per_label = {
        label: {
            "truePositiveCount": 0,
            "falsePositiveCount": 0,
            "falseNegativeCount": 0,
        }
        for label in ("attack", "movement_only")
    }
    abstention_count = 0
    exact_count = 0
    evaluated_count = 0
    for held_out_group in groups:
        training = [
            row
            for row in rows
            if str(row.get("contentUnitId") or "") != held_out_group
        ]
        accepted = _learned_signatures(
            training,
            minimum_support=minimum_support,
            minimum_content_units=minimum_content_units,
            minimum_precision=minimum_precision,
        )
        for row in rows:
            if str(row.get("contentUnitId") or "") != held_out_group:
                continue
            actual = str(row.get("label") or "")
            if actual not in per_label:
                continue
            evaluated_count += 1
            match = accepted.get(_canonical_json(row["signature"]))
            predicted = str((match or {}).get("label") or "")
            if not predicted:
                abstention_count += 1
                per_label[actual]["falseNegativeCount"] += 1
                continue
            if predicted == actual:
                exact_count += 1
                per_label[actual]["truePositiveCount"] += 1
            else:
                per_label[predicted]["falsePositiveCount"] += 1
                per_label[actual]["falseNegativeCount"] += 1
    label_metrics: dict[str, Any] = {}
    for label, counts in per_label.items():
        predicted_count = (
            counts["truePositiveCount"] + counts["falsePositiveCount"]
        )
        actual_count = (
            counts["truePositiveCount"] + counts["falseNegativeCount"]
        )
        label_metrics[label] = {
            **counts,
            "precision": (
                counts["truePositiveCount"] / predicted_count
                if predicted_count
                else 0.0
            ),
            "recall": (
                counts["truePositiveCount"] / actual_count
                if actual_count
                else 0.0
            ),
        }
    movement = label_metrics["movement_only"]
    return {
        "foldUnit": "content_unit",
        "foldCount": len(groups),
        # Preserve the original movement-only fields for audit continuity.
        "truePositiveCount": movement["truePositiveCount"],
        "falsePositiveCount": movement["falsePositiveCount"],
        "falseNegativeCount": movement["falseNegativeCount"],
        "precision": movement["precision"],
        "recall": movement["recall"],
        "perLabel": label_metrics,
        "evaluatedCount": evaluated_count,
        "exactCount": exact_count,
        "exactAccuracy": (
            exact_count / evaluated_count if evaluated_count else 0.0
        ),
        "abstentionCount": abstention_count,
        "abstainsOnUnrecognizedSignatures": True,
    }


def train_transition_decoder(
    rows: Sequence[Mapping[str, Any]],
    *,
    source_cohort_id: str,
    minimum_support: int = DEFAULT_MINIMUM_SUPPORT,
    minimum_content_units: int = DEFAULT_MINIMUM_CONTENT_UNITS,
    minimum_precision: float = DEFAULT_MINIMUM_PRECISION,
) -> dict[str, Any]:
    """Train a digest-stable, precision-first source-cohort decoder."""

    if not source_cohort_id:
        raise TransitionDecoderError("A transition decoder requires a source cohort.")
    if minimum_support < 1 or minimum_content_units < 1:
        raise TransitionDecoderError("Transition support floors must be positive.")
    if not 0.0 < minimum_precision <= 1.0:
        raise TransitionDecoderError("Transition precision must fall in (0, 1].")
    normalized_rows = [
        dict(row)
        for row in rows
        if str(row.get("sourceCohortId") or "") == source_cohort_id
    ]
    learned = _learned_signatures(
        normalized_rows,
        minimum_support=minimum_support,
        minimum_content_units=minimum_content_units,
        minimum_precision=minimum_precision,
    )
    cross_validation = _grouped_cross_validation(
        normalized_rows,
        minimum_support=minimum_support,
        minimum_content_units=minimum_content_units,
        minimum_precision=minimum_precision,
    )
    movement_count = sum(
        int(row.get("label") == "movement_only") for row in normalized_rows
    )
    artifact_core = {
        "schemaVersion": TRANSITION_DECODER_SCHEMA_VERSION,
        "featureSchemaVersion": TRANSITION_FEATURE_SCHEMA_VERSION,
        "sourceCohortId": source_cohort_id,
        "policy": "reviewed_attack_or_movement_only_or_abstain",
        "thresholds": {
            "minimumSupport": minimum_support,
            "minimumContentUnits": minimum_content_units,
            "minimumPrecision": minimum_precision,
        },
        "trainingRowCount": len(normalized_rows),
        "trainingMovementOnlyCount": movement_count,
        "trainingAttackCount": len(normalized_rows) - movement_count,
        "acceptedSignatures": sorted(
            learned.values(),
            key=lambda value: str(value["signatureDigest"]),
        ),
        "groupedCrossValidation": cross_validation,
        "validationDataUsed": False,
        "sealedTestDataUsed": False,
    }
    return {
        **artifact_core,
        "decoderId": f"atx-{_sha256_json(artifact_core)[:16]}",
        "artifactDigest": _sha256_json(artifact_core),
    }


def transition_decoder_automation_eligibility(
    decoder: Mapping[str, Any],
) -> dict[str, bool]:
    """Return whether each emitted label passed grouped precision gates."""

    if decoder.get("schemaVersion") != TRANSITION_DECODER_SCHEMA_VERSION:
        raise TransitionDecoderError("Unsupported transition decoder schema.")
    accepted_labels = {
        str(value.get("label") or "")
        for value in decoder.get("acceptedSignatures") or ()
        if isinstance(value, Mapping)
        and value.get("label") in {"attack", "movement_only"}
    }
    per_label_metrics = (
        decoder.get("groupedCrossValidation") or {}
    ).get("perLabel") or {}
    minimum_precision = float(
        (decoder.get("thresholds") or {}).get("minimumPrecision") or 0.0
    )
    return {
        label: bool(
            int((per_label_metrics.get(label) or {}).get("truePositiveCount") or 0)
            > 0
            and int(
                (per_label_metrics.get(label) or {}).get("falsePositiveCount") or 0
            )
            == 0
            and float((per_label_metrics.get(label) or {}).get("precision") or 0.0)
            >= minimum_precision
        )
        for label in sorted(accepted_labels)
    }


def classify_transition(
    decoder: Mapping[str, Any],
    previous_event: Mapping[str, Any],
    current_event: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify one transition or explicitly abstain."""

    if decoder.get("schemaVersion") != TRANSITION_DECODER_SCHEMA_VERSION:
        raise TransitionDecoderError("Unsupported transition decoder schema.")
    signature = transition_feature_signature(previous_event, current_event)
    signature_digest = _sha256_json(signature)
    learned = {
        str(value.get("signatureDigest") or ""): value
        for value in decoder.get("acceptedSignatures") or ()
        if isinstance(value, Mapping)
    }
    match = learned.get(signature_digest)
    if match is None:
        return {
            "decision": "unresolved",
            "reason": "signature_not_proven",
            "signatureDigest": signature_digest,
        }
    return {
        "decision": str(match.get("label") or "unresolved"),
        "reason": "repeated_reviewed_source_signature",
        "signatureDigest": signature_digest,
        "support": int(match.get("support") or 0),
        "contentUnitCount": int(match.get("contentUnitCount") or 0),
        "discoveryPrecision": float(match.get("precision") or 0.0),
    }
