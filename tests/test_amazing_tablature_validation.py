from __future__ import annotations

from steel_guitar_rag.amazing_tablature_validation import (
    validation_contact_execution_digest,
)


def test_validation_execution_digest_ignores_wrapper_lineage() -> None:
    event = {
        "eventIndex": 7,
        "tabEventId": "first-wrapper",
        "executionType": "attack",
        "executionInference": "reader-a",
        "steelActions": [
            {
                "string": 5,
                "fret": 8,
                "controls": ["A"],
                "attack": True,
                "soundingPitchValue": 68,
            }
        ],
    }
    rebuilt = {
        **event,
        "eventIndex": 1,
        "tabEventId": "second-wrapper",
        "executionInference": "reader-b",
        "confidence": 0.91,
    }

    assert validation_contact_execution_digest(
        [event]
    ) == validation_contact_execution_digest([rebuilt])


def test_validation_execution_digest_changes_with_musical_execution() -> None:
    event = {
        "executionType": "attack",
        "steelActions": [
            {
                "string": 5,
                "fret": 8,
                "controls": ["A"],
                "attack": True,
                "soundingPitchValue": 68,
            }
        ],
    }
    changed = {
        **event,
        "steelActions": [
            {
                **event["steelActions"][0],
                "controls": [],
                "soundingPitchValue": 66,
            }
        ],
    }

    assert validation_contact_execution_digest(
        [event]
    ) != validation_contact_execution_digest([changed])
