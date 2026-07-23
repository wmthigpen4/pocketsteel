import copy

from pocketsteel.amazing_tablature_reader_calibration import (
    BLANK_READER_STATE,
    calibrated_state_is_eligible,
    reader_state_signature,
    train_reader_calibration,
)


def test_reader_state_signature_is_typography_neutral() -> None:
    assert reader_state_signature([]) == BLANK_READER_STATE
    assert reader_state_signature(
        [{"fret": 8, "controls": ["B", "A"]}]
    ) == reader_state_signature(
        [{"fret": "8", "controls": ["a", "B", "A"]}]
    )


def test_reader_calibration_uses_grouped_holdout_precision() -> None:
    cases = []
    for content_unit in ("unit-a", "unit-b", "unit-c", "unit-d"):
        cases.extend(
            [
                {
                    "readerId": "reader-1",
                    "contentUnitId": content_unit,
                    "predictedState": "state-8a",
                    "truthState": "state-8a",
                    "confidence": 1.0,
                },
                {
                    "readerId": "reader-1",
                    "contentUnitId": content_unit,
                    "predictedState": BLANK_READER_STATE,
                    "truthState": BLANK_READER_STATE,
                    "confidence": 1.0,
                },
            ]
        )
    calibration = train_reader_calibration(
        cases,
        source_cohort_id="batch-1",
        reader_contracts=[{"modelTag": "reader-1", "modelDigest": "digest-1"}],
        minimum_state_support=2,
        minimum_content_units=2,
        minimum_cv_predictions=4,
        minimum_cv_precision=1.0,
    )

    assert calibration["automationEligible"] is True
    assert calibration["groupedCrossValidation"]["predictionCount"] == 8
    assert calibration["groupedCrossValidation"]["precision"] == 1.0
    assert calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )
    assert not calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="unseen",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )
    assert not calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="focused_contact_sheet",
    )
    weakened_rule = copy.deepcopy(calibration)
    next(
        rule
        for rule in weakened_rule["acceptedRules"]
        if rule["predictedState"] == "state-8a"
    )["groupedCvPrecision"] = 0.5
    assert not calibrated_state_is_eligible(
        weakened_rule,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )
    weakened_global = copy.deepcopy(calibration)
    weakened_global["acceptedRuleCrossValidation"]["precision"] = 0.5
    assert not calibrated_state_is_eligible(
        weakened_global,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )


def test_reader_calibration_never_transfers_a_rule_between_input_modes() -> None:
    cases = []
    for content_unit in ("unit-a", "unit-b", "unit-c", "unit-d"):
        for input_mode in (
            "full_contact_sheet",
            "focused_contact_sheet_chunk",
        ):
            cases.append(
                {
                    "readerId": "reader-1",
                    "contentUnitId": content_unit,
                    "inputMode": input_mode,
                    "predictedState": "state-8a",
                    "truthState": (
                        "state-8a"
                        if input_mode == "full_contact_sheet"
                        else (
                            "state-8a"
                            if content_unit != "unit-d"
                            else "state-9"
                        )
                    ),
                    "confidence": 1.0,
                }
            )
    calibration = train_reader_calibration(
        cases,
        source_cohort_id="batch-1",
        reader_contracts=[
            {"modelTag": "reader-1", "modelDigest": "digest-1"}
        ],
        minimum_state_support=2,
        minimum_content_units=2,
        minimum_cv_predictions=4,
        minimum_cv_precision=1.0,
    )

    assert calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )
    assert not calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="focused_contact_sheet_chunk",
    )
    assert {
        (rule["inputMode"], rule["predictedState"])
        for rule in calibration["acceptedRules"]
    } == {("full_contact_sheet", "state-8a")}


def test_reader_calibration_automates_only_accepted_rule_predictions() -> None:
    cases = []
    for content_unit in ("unit-a", "unit-b", "unit-c", "unit-d"):
        for _repeat in range(3):
            cases.append(
                {
                    "readerId": "reader-1",
                    "contentUnitId": content_unit,
                    "predictedState": "clean-state",
                    "truthState": "clean-state",
                    "confidence": 1.0,
                }
            )
        cases.append(
            {
                "readerId": "reader-1",
                "contentUnitId": content_unit,
                "predictedState": "rejected-noisy-state",
                "truthState": (
                    "rejected-noisy-state"
                    if content_unit != "unit-d"
                    else "different-state"
                ),
                "confidence": 1.0,
            }
        )
    calibration = train_reader_calibration(
        cases,
        source_cohort_id="batch-1",
        reader_contracts=[
            {"modelTag": "reader-1", "modelDigest": "digest-1"}
        ],
        minimum_state_support=2,
        minimum_content_units=2,
        minimum_cv_predictions=8,
        minimum_cv_precision=1.0,
    )

    assert calibration["groupedCrossValidation"]["precision"] < 1.0
    assert calibration["acceptedRuleCrossValidation"] == {
        "foldUnit": "content_unit",
        "foldCount": 4,
        "predictionCount": 12,
        "correctCount": 12,
        "falsePositiveCount": 0,
        "precision": 1.0,
        "byReader": {
            "reader-1": {
                "predictionCount": 12,
                "correctCount": 12,
                "precision": 1.0,
            }
        },
    }
    assert {
        rule["predictedState"] for rule in calibration["acceptedRules"]
    } == {"clean-state"}
    assert calibration["automationEligible"] is True
    assert calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="clean-state",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )
    assert not calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="rejected-noisy-state",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )


def test_reader_calibration_rejects_a_leaky_state_rule() -> None:
    cases = []
    for content_unit in ("unit-a", "unit-b", "unit-c", "unit-d"):
        cases.append(
            {
                "readerId": "reader-1",
                "contentUnitId": content_unit,
                "predictedState": "state-8a",
                "truthState": (
                    "state-8a"
                    if content_unit != "unit-d"
                    else "state-9"
                ),
                "confidence": 1.0,
            }
        )
    calibration = train_reader_calibration(
        cases,
        source_cohort_id="batch-1",
        reader_contracts=[{"modelTag": "reader-1", "modelDigest": "digest-1"}],
        minimum_state_support=2,
        minimum_content_units=2,
        minimum_cv_predictions=1,
        minimum_cv_precision=1.0,
    )

    assert calibration["groupedCrossValidation"]["falsePositiveCount"] == 1
    assert calibration["automationEligible"] is False
    assert not calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="state-8a",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )


def test_reader_calibration_rejects_rule_without_its_own_grouped_cv_support() -> None:
    cases = []
    for content_unit in ("unit-a", "unit-b", "unit-c", "unit-d"):
        for _repeat in range(4):
            cases.append(
                {
                    "readerId": "reader-1",
                    "contentUnitId": content_unit,
                    "predictedState": BLANK_READER_STATE,
                    "truthState": BLANK_READER_STATE,
                    "confidence": 1.0,
                }
            )
    # This state reaches final-data support, but every leave-one-unit-out
    # training fold drops below the state-support threshold. It must not
    # inherit the blank rule's otherwise perfect aggregate CV result.
    for content_unit in ("unit-a", "unit-b", "unit-c"):
        for _repeat in range(3):
            cases.append(
                {
                    "readerId": "reader-1",
                    "contentUnitId": content_unit,
                    "predictedState": "rare-state",
                    "truthState": "rare-state",
                    "confidence": 1.0,
                }
            )
    calibration = train_reader_calibration(
        cases,
        source_cohort_id="batch-1",
        reader_contracts=[{"modelTag": "reader-1", "modelDigest": "digest-1"}],
        minimum_state_support=8,
        minimum_content_units=3,
        minimum_cv_predictions=8,
        minimum_cv_precision=1.0,
    )

    assert calibration["automationEligible"] is True
    assert calibration["candidateRuleCount"] == 2
    assert {
        rule["predictedState"] for rule in calibration["acceptedRules"]
    } == {BLANK_READER_STATE}
    assert not calibrated_state_is_eligible(
        calibration,
        reader_id="reader-1",
        predicted_state="rare-state",
        confidence=1.0,
        input_mode="full_contact_sheet",
    )
