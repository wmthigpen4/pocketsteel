"""Shared, private validation evidence contracts for Amazing Tablature."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


VALIDATION_CONTACT_EXECUTION_SCHEMA_VERSION = (
    "validation-contact-execution-signature-v1"
)


def validation_contact_execution_digest(
    events: Sequence[Mapping[str, Any]],
) -> str:
    """Hash the ordered musical execution while excluding wrapper lineage."""

    normalized_events: list[dict[str, Any]] = []
    for ordinal, event in enumerate(events, start=1):
        actions = sorted(
            (
                {
                    "string": int(action["string"]),
                    "fret": int(action["fret"]),
                    "controls": sorted(
                        str(value) for value in action.get("controls") or ()
                    ),
                    "attack": bool(action.get("attack", True)),
                    "soundingPitchValue": int(action["soundingPitchValue"]),
                }
                for action in event.get("steelActions") or ()
            ),
            key=lambda action: (
                action["string"],
                action["fret"],
                action["controls"],
                action["attack"],
                action["soundingPitchValue"],
            ),
        )
        if not actions:
            raise ValueError("Validation execution events require steel actions.")
        normalized_events.append(
            {
                "eventIndex": ordinal,
                "executionType": str(event.get("executionType") or ""),
                "actions": actions,
            }
        )
    if not normalized_events:
        raise ValueError("Validation execution evidence cannot be empty.")
    payload = {
        "schemaVersion": VALIDATION_CONTACT_EXECUTION_SCHEMA_VERSION,
        "events": normalized_events,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
