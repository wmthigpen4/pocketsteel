from __future__ import annotations

from steel_guitar_rag.amazing_tablature_transition_decoder import (
    TRANSITION_FEATURE_SCHEMA_VERSION,
    classify_transition,
    train_transition_decoder,
    transition_decoder_automation_eligibility,
    transition_feature_signature,
    transition_training_rows,
)


def _event(
    event_index: int,
    *,
    string: int = 5,
    fret: int = 8,
    controls: tuple[str, ...] = (),
    pitch: int = 60,
    execution: str = "attack",
) -> dict[str, object]:
    return {
        "eventIndex": event_index,
        "executionType": execution,
        "steelActions": [
            {
                "string": string,
                "fret": fret,
                "controls": list(controls),
                "soundingPitchValue": pitch,
            }
        ],
    }


def test_transition_feature_signature_is_exact_and_runtime_safe() -> None:
    signature = transition_feature_signature(
        _event(1, controls=("A",), pitch=62),
        _event(2, controls=(), pitch=60),
    )

    assert signature == {
        "featureSchemaVersion": TRANSITION_FEATURE_SCHEMA_VERSION,
        "sameStringSet": True,
        "currentStrings": [5],
        "controlTransitions": [{"string": 5, "from": ["A"], "to": []}],
        "fretDeltas": [{"string": 5, "delta": 0}],
        "pitchDeltas": [{"string": 5, "delta": -2}],
    }


def test_transition_decoder_learns_repeated_source_movement_and_abstains() -> None:
    rows = []
    for group_index in range(4):
        record = {
            "inputId": f"input-{group_index}",
            "contentUnitId": f"unit-{group_index}",
            "tabSystems": [
                {
                    "tabSystemId": f"tab-{group_index}",
                    "tabEvents": [
                        _event(1, controls=("A",), pitch=62),
                        _event(
                            2,
                            controls=(),
                            pitch=60,
                            execution="movement_only",
                        ),
                        _event(3, string=4, pitch=64),
                    ],
                }
            ],
        }
        rows.extend(
            transition_training_rows(record, source_cohort_id="cohort-1")
        )
    decoder = train_transition_decoder(
        rows,
        source_cohort_id="cohort-1",
        minimum_support=4,
        minimum_content_units=4,
    )

    movement = classify_transition(
        decoder,
        _event(1, controls=("A",), pitch=62),
        _event(2, controls=(), pitch=60),
    )
    unknown = classify_transition(
        decoder,
        _event(1, fret=8, pitch=60),
        _event(2, fret=9, pitch=61),
    )

    assert movement["decision"] == "movement_only"
    assert movement["support"] == 4
    assert unknown == {
        "decision": "unresolved",
        "reason": "signature_not_proven",
        "signatureDigest": unknown["signatureDigest"],
    }
    assert decoder["validationDataUsed"] is False
    assert decoder["sealedTestDataUsed"] is False
    assert transition_decoder_automation_eligibility(decoder) == {
        "attack": False,
        "movement_only": False,
    }


def test_transition_decoder_learns_repeated_attack_without_guessing() -> None:
    rows = []
    for group_index in range(5):
        record = {
            "inputId": f"input-{group_index}",
            "contentUnitId": f"unit-{group_index}",
            "tabSystems": [
                {
                    "tabSystemId": f"tab-{group_index}",
                    "tabEvents": [
                        _event(1, fret=3, pitch=55),
                        _event(
                            2,
                            fret=5,
                            pitch=57,
                            execution="attack",
                        ),
                    ],
                }
            ],
        }
        rows.extend(
            transition_training_rows(record, source_cohort_id="cohort-1")
        )
    decoder = train_transition_decoder(
        rows,
        source_cohort_id="cohort-1",
        minimum_support=4,
        minimum_content_units=4,
    )

    attack = classify_transition(
        decoder,
        _event(1, fret=3, pitch=55),
        _event(2, fret=5, pitch=57),
    )

    assert attack["decision"] == "attack"
    assert attack["support"] == 5
    assert decoder["acceptedSignatures"][0]["label"] == "attack"
    assert decoder["groupedCrossValidation"]["perLabel"]["attack"][
        "precision"
    ] == 1.0
    assert transition_decoder_automation_eligibility(decoder) == {
        "attack": True,
    }


def test_grouped_cross_validation_catches_source_unit_exception() -> None:
    rows = []
    for group_index in range(5):
        record = {
            "inputId": f"input-{group_index}",
            "contentUnitId": f"unit-{group_index}",
            "tabSystems": [
                {
                    "tabSystemId": f"tab-{group_index}",
                    "tabEvents": [
                        _event(1, controls=("A",), pitch=62),
                        _event(
                            2,
                            controls=(),
                            pitch=60,
                            execution=(
                                "attack"
                                if group_index == 4
                                else "movement_only"
                            ),
                        ),
                    ],
                }
            ],
        }
        rows.extend(
            transition_training_rows(record, source_cohort_id="cohort-1")
        )
    decoder = train_transition_decoder(
        rows,
        source_cohort_id="cohort-1",
        minimum_support=3,
        minimum_content_units=3,
        minimum_precision=0.95,
    )

    assert decoder["acceptedSignatures"] == []
    metrics = decoder["groupedCrossValidation"]
    assert metrics["truePositiveCount"] == 0
    assert metrics["falsePositiveCount"] == 1
    assert metrics["precision"] == 0.0
