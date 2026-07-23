"""Discovery-only precision calibration for pinned tab-cell readers."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


READER_CALIBRATION_SCHEMA_VERSION = (
    "amazing-tablature-reader-calibration-v4"
)
READER_INPUT_MODE = "full_contact_sheet"
FOCUSED_READER_INPUT_MODE = "focused_contact_sheet_chunk"
BLANK_READER_STATE = "blank"
UNRESOLVED_READER_STATE = "unresolved"
DEFAULT_MINIMUM_STATE_SUPPORT = 8
DEFAULT_MINIMUM_CONTENT_UNITS = 3
DEFAULT_MINIMUM_CV_PREDICTIONS = 30
DEFAULT_MINIMUM_CV_PRECISION = 0.995
DEFAULT_MINIMUM_PAIR_SUPPORT = 4
DEFAULT_MINIMUM_PAIR_CONTENT_UNITS = 3
DEFAULT_MINIMUM_PAIR_CV_PREDICTIONS = 8
DEFAULT_MINIMUM_PAIR_CV_CONTENT_UNITS = 4
_CONFIDENCE_THRESHOLDS = (1.0, 0.99, 0.95, 0.90, 0.85, 0.80)


class ReaderCalibrationError(ValueError):
    """Raised when reader calibration evidence violates its contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def reader_state_signature(actions: Sequence[Mapping[str, Any]]) -> str:
    """Return a typography-neutral fret/control sequence signature."""

    if not actions:
        return BLANK_READER_STATE
    normalized: list[dict[str, Any]] = []
    for action in actions:
        try:
            fret = int(action["fret"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ReaderCalibrationError(
                "A reader state action requires an integer fret."
            ) from exc
        controls = sorted(
            {
                str(value).strip().upper()
                for value in action.get("controls") or ()
                if str(value).strip()
            }
        )
        normalized.append({"fret": fret, "controls": controls})
    return _canonical_json(normalized)


def reader_pair_signature(
    reader_states: Sequence[Mapping[str, Any]],
) -> str:
    """Return a stable ordered signature for pinned reader outcomes."""

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in reader_states:
        reader_id = str(item.get("readerId") or "")
        state = str(item.get("state") or "")
        if (
            not reader_id
            or reader_id in seen
            or not state
        ):
            raise ReaderCalibrationError(
                "A reader-pair signature requires unique reader IDs and states."
            )
        seen.add(reader_id)
        normalized.append(
            {
                "readerId": reader_id,
                "state": state,
            }
        )
    if len(normalized) < 2:
        raise ReaderCalibrationError(
            "A reader-pair signature requires at least two readers."
        )
    normalized.sort(key=lambda value: value["readerId"])
    return _canonical_json(normalized)


def _normalized_cases(
    cases: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for case in cases:
        reader_id = str(case.get("readerId") or "")
        content_unit_id = str(case.get("contentUnitId") or "")
        input_mode = str(
            case.get("inputMode") or READER_INPUT_MODE
        )
        predicted_state = str(case.get("predictedState") or "")
        truth_state = str(case.get("truthState") or "")
        confidence = float(case.get("confidence") or 0.0)
        if (
            not reader_id
            or not content_unit_id
            or not input_mode
            or not predicted_state
            or not truth_state
            or not 0.0 <= confidence <= 1.0
        ):
            continue
        normalized.append(
            {
                "readerId": reader_id,
                "contentUnitId": content_unit_id,
                "inputMode": input_mode,
                "predictedState": predicted_state,
                "truthState": truth_state,
                "confidence": confidence,
                "correct": predicted_state == truth_state,
            }
        )
    return normalized


def _normalized_pair_cases(
    cases: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for case in cases:
        content_unit_id = str(case.get("contentUnitId") or "")
        input_mode = str(
            case.get("inputMode") or READER_INPUT_MODE
        )
        truth_state = str(case.get("truthState") or "")
        try:
            pair_signature = reader_pair_signature(
                case.get("readerStates") or ()
            )
        except ReaderCalibrationError:
            continue
        if not content_unit_id or not input_mode or not truth_state:
            continue
        normalized.append(
            {
                "contentUnitId": content_unit_id,
                "inputMode": input_mode,
                "pairSignature": pair_signature,
                "truthState": truth_state,
            }
        )
    return normalized


def _build_rules(
    cases: Sequence[Mapping[str, Any]],
    *,
    minimum_state_support: int,
    minimum_content_units: int,
    minimum_precision: float,
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, str],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for case in cases:
        grouped[
            (
                str(case["readerId"]),
                str(case["inputMode"]),
                str(case["predictedState"]),
            )
        ].append(case)
    rules: list[dict[str, Any]] = []
    for (
        reader_id,
        input_mode,
        predicted_state,
    ), state_cases in sorted(grouped.items()):
        selected_rule: dict[str, Any] | None = None
        for threshold in _CONFIDENCE_THRESHOLDS:
            selected = [
                case
                for case in state_cases
                if float(case["confidence"]) >= threshold
            ]
            support = len(selected)
            content_unit_count = len(
                {str(case["contentUnitId"]) for case in selected}
            )
            correct_count = sum(bool(case["correct"]) for case in selected)
            precision = correct_count / support if support else 0.0
            if (
                support >= minimum_state_support
                and content_unit_count >= minimum_content_units
                and precision >= minimum_precision
            ):
                # Thresholds are considered from strictest to loosest. Keep
                # the loosest passing threshold so coverage is maximized
                # without relaxing the fixed precision contract.
                selected_rule = {
                    "readerId": reader_id,
                    "inputMode": input_mode,
                    "predictedState": predicted_state,
                    "minimumConfidence": threshold,
                    "support": support,
                    "contentUnitCount": content_unit_count,
                    "correctCount": correct_count,
                    "precision": precision,
                }
        if selected_rule is not None:
            rules.append(selected_rule)
    return rules


def _build_pair_rules(
    cases: Sequence[Mapping[str, Any]],
    *,
    minimum_support: int,
    minimum_content_units: int,
    minimum_precision: float,
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for case in cases:
        grouped[
            (
                str(case["inputMode"]),
                str(case["pairSignature"]),
            )
        ].append(case)
    rules: list[dict[str, Any]] = []
    for (input_mode, pair_signature), state_cases in sorted(
        grouped.items()
    ):
        truth_counts: dict[str, int] = defaultdict(int)
        for case in state_cases:
            truth_counts[str(case["truthState"])] += 1
        predicted_state, correct_count = max(
            truth_counts.items(),
            key=lambda value: (value[1], value[0]),
        )
        support = len(state_cases)
        content_unit_count = len(
            {str(case["contentUnitId"]) for case in state_cases}
        )
        precision = correct_count / support if support else 0.0
        if (
            support < minimum_support
            or content_unit_count < minimum_content_units
            or precision < minimum_precision
        ):
            continue
        rules.append(
            {
                "inputMode": input_mode,
                "pairSignature": pair_signature,
                "readerStates": json.loads(pair_signature),
                "predictedState": predicted_state,
                "support": support,
                "contentUnitCount": content_unit_count,
                "correctCount": correct_count,
                "precision": precision,
            }
        )
    return rules


def train_reader_calibration(
    cases: Sequence[Mapping[str, Any]],
    *,
    source_cohort_id: str,
    reader_contracts: Sequence[Mapping[str, Any]],
    paired_cases: Sequence[Mapping[str, Any]] = (),
    minimum_state_support: int = DEFAULT_MINIMUM_STATE_SUPPORT,
    minimum_content_units: int = DEFAULT_MINIMUM_CONTENT_UNITS,
    minimum_cv_predictions: int = DEFAULT_MINIMUM_CV_PREDICTIONS,
    minimum_cv_precision: float = DEFAULT_MINIMUM_CV_PRECISION,
    minimum_pair_support: int = DEFAULT_MINIMUM_PAIR_SUPPORT,
    minimum_pair_content_units: int = (
        DEFAULT_MINIMUM_PAIR_CONTENT_UNITS
    ),
    minimum_pair_cv_predictions: int = (
        DEFAULT_MINIMUM_PAIR_CV_PREDICTIONS
    ),
    minimum_pair_cv_content_units: int = (
        DEFAULT_MINIMUM_PAIR_CV_CONTENT_UNITS
    ),
) -> dict[str, Any]:
    """Calibrate exact reader states with leave-one-content-unit-out tests."""

    if not source_cohort_id:
        raise ReaderCalibrationError(
            "A reader calibration requires a source cohort."
        )
    normalized = _normalized_cases(cases)
    normalized_pairs = _normalized_pair_cases(paired_cases)
    content_units = sorted(
        {
            str(case["contentUnitId"])
            for case in (*normalized, *normalized_pairs)
        }
    )
    cv_predictions: list[dict[str, Any]] = []
    for held_out_unit in content_units:
        training = [
            case
            for case in normalized
            if str(case["contentUnitId"]) != held_out_unit
        ]
        rules = _build_rules(
            training,
            minimum_state_support=minimum_state_support,
            minimum_content_units=minimum_content_units,
            minimum_precision=minimum_cv_precision,
        )
        rule_index = {
            (
                str(rule["readerId"]),
                str(rule["inputMode"]),
                str(rule["predictedState"]),
            ): rule
            for rule in rules
        }
        for case in normalized:
            if str(case["contentUnitId"]) != held_out_unit:
                continue
            rule = rule_index.get(
                (
                    str(case["readerId"]),
                    str(case["inputMode"]),
                    str(case["predictedState"]),
                )
            )
            if (
                rule is None
                or float(case["confidence"])
                < float(rule["minimumConfidence"])
            ):
                continue
            cv_predictions.append(
                {
                    "readerId": str(case["readerId"]),
                    "contentUnitId": str(case["contentUnitId"]),
                    "inputMode": str(case["inputMode"]),
                    "predictedState": str(case["predictedState"]),
                    "correct": bool(case["correct"]),
                }
            )
    cv_correct = sum(bool(case["correct"]) for case in cv_predictions)
    cv_precision = (
        cv_correct / len(cv_predictions) if cv_predictions else 0.0
    )
    candidate_rules = _build_rules(
        normalized,
        minimum_state_support=minimum_state_support,
        minimum_content_units=minimum_content_units,
        minimum_precision=minimum_cv_precision,
    )
    cv_by_rule: dict[
        tuple[str, str, str],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for prediction in cv_predictions:
        cv_by_rule[
            (
                str(prediction["readerId"]),
                str(prediction["inputMode"]),
                str(prediction["predictedState"]),
            )
        ].append(prediction)
    final_rules: list[dict[str, Any]] = []
    for rule in candidate_rules:
        key = (
            str(rule["readerId"]),
            str(rule["inputMode"]),
            str(rule["predictedState"]),
        )
        predictions = cv_by_rule.get(key, [])
        prediction_count = len(predictions)
        correct_count = sum(
            bool(prediction["correct"]) for prediction in predictions
        )
        held_out_unit_count = len(
            {
                str(prediction["contentUnitId"])
                for prediction in predictions
            }
        )
        precision = (
            correct_count / prediction_count if prediction_count else 0.0
        )
        if (
            prediction_count < minimum_state_support
            or held_out_unit_count < minimum_content_units
            or precision < minimum_cv_precision
        ):
            continue
        final_rules.append(
            {
                **rule,
                "groupedCvPredictionCount": prediction_count,
                "groupedCvCorrectCount": correct_count,
                "groupedCvContentUnitCount": held_out_unit_count,
                "groupedCvPrecision": precision,
            }
        )
    accepted_rule_keys = {
        (
            str(rule["readerId"]),
            str(rule["inputMode"]),
            str(rule["predictedState"]),
        )
        for rule in final_rules
    }
    accepted_cv_predictions = [
        prediction
        for prediction in cv_predictions
        if (
            str(prediction["readerId"]),
            str(prediction["inputMode"]),
            str(prediction["predictedState"]),
        )
        in accepted_rule_keys
    ]
    accepted_cv_correct = sum(
        bool(case["correct"]) for case in accepted_cv_predictions
    )
    accepted_cv_precision = (
        accepted_cv_correct / len(accepted_cv_predictions)
        if accepted_cv_predictions
        else 0.0
    )
    pair_cv_predictions: list[dict[str, Any]] = []
    for held_out_unit in content_units:
        training = [
            case
            for case in normalized_pairs
            if str(case["contentUnitId"]) != held_out_unit
        ]
        rules = _build_pair_rules(
            training,
            minimum_support=minimum_pair_support,
            minimum_content_units=minimum_pair_content_units,
            minimum_precision=minimum_cv_precision,
        )
        rule_index = {
            (
                str(rule["inputMode"]),
                str(rule["pairSignature"]),
            ): rule
            for rule in rules
        }
        for case in normalized_pairs:
            if str(case["contentUnitId"]) != held_out_unit:
                continue
            rule = rule_index.get(
                (
                    str(case["inputMode"]),
                    str(case["pairSignature"]),
                )
            )
            if rule is None:
                continue
            pair_cv_predictions.append(
                {
                    "contentUnitId": str(case["contentUnitId"]),
                    "inputMode": str(case["inputMode"]),
                    "pairSignature": str(case["pairSignature"]),
                    "predictedState": str(rule["predictedState"]),
                    "truthState": str(case["truthState"]),
                    "correct": (
                        str(rule["predictedState"])
                        == str(case["truthState"])
                    ),
                }
            )
    candidate_pair_rules = _build_pair_rules(
        normalized_pairs,
        minimum_support=minimum_pair_support,
        minimum_content_units=minimum_pair_content_units,
        minimum_precision=minimum_cv_precision,
    )
    pair_cv_by_rule: dict[
        tuple[str, str],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for prediction in pair_cv_predictions:
        pair_cv_by_rule[
            (
                str(prediction["inputMode"]),
                str(prediction["pairSignature"]),
            )
        ].append(prediction)
    final_pair_rules: list[dict[str, Any]] = []
    for rule in candidate_pair_rules:
        predictions = pair_cv_by_rule.get(
            (
                str(rule["inputMode"]),
                str(rule["pairSignature"]),
            ),
            [],
        )
        prediction_count = len(predictions)
        correct_count = sum(
            bool(prediction["correct"]) for prediction in predictions
        )
        held_out_unit_count = len(
            {
                str(prediction["contentUnitId"])
                for prediction in predictions
            }
        )
        precision = (
            correct_count / prediction_count if prediction_count else 0.0
        )
        if (
            prediction_count < minimum_pair_cv_predictions
            or held_out_unit_count < minimum_pair_cv_content_units
            or precision < minimum_cv_precision
        ):
            continue
        final_pair_rules.append(
            {
                **rule,
                "groupedCvPredictionCount": prediction_count,
                "groupedCvCorrectCount": correct_count,
                "groupedCvContentUnitCount": held_out_unit_count,
                "groupedCvPrecision": precision,
            }
        )
    accepted_pair_rule_keys = {
        (
            str(rule["inputMode"]),
            str(rule["pairSignature"]),
        )
        for rule in final_pair_rules
    }
    accepted_pair_cv_predictions = [
        prediction
        for prediction in pair_cv_predictions
        if (
            str(prediction["inputMode"]),
            str(prediction["pairSignature"]),
        )
        in accepted_pair_rule_keys
    ]
    accepted_pair_cv_correct = sum(
        bool(prediction["correct"])
        for prediction in accepted_pair_cv_predictions
    )
    accepted_pair_cv_precision = (
        accepted_pair_cv_correct / len(accepted_pair_cv_predictions)
        if accepted_pair_cv_predictions
        else 0.0
    )
    by_reader: dict[str, dict[str, Any]] = {}
    accepted_by_reader: dict[str, dict[str, Any]] = {}
    for reader_id in sorted(
        {str(case["readerId"]) for case in normalized}
    ):
        predictions = [
            case
            for case in cv_predictions
            if str(case["readerId"]) == reader_id
        ]
        correct = sum(bool(case["correct"]) for case in predictions)
        by_reader[reader_id] = {
            "predictionCount": len(predictions),
            "correctCount": correct,
            "precision": correct / len(predictions) if predictions else 0.0,
        }
        accepted_predictions = [
            case
            for case in accepted_cv_predictions
            if str(case["readerId"]) == reader_id
        ]
        accepted_correct = sum(
            bool(case["correct"]) for case in accepted_predictions
        )
        accepted_by_reader[reader_id] = {
            "predictionCount": len(accepted_predictions),
            "correctCount": accepted_correct,
            "precision": (
                accepted_correct / len(accepted_predictions)
                if accepted_predictions
                else 0.0
            ),
        }
    singleton_automation_eligible = bool(
        final_rules
        and len(accepted_cv_predictions) >= minimum_cv_predictions
        and accepted_cv_precision >= minimum_cv_precision
    )
    pair_automation_eligible = bool(
        final_pair_rules
        and len(accepted_pair_cv_predictions)
        >= minimum_pair_cv_predictions
        and accepted_pair_cv_precision >= minimum_cv_precision
    )
    automation_eligible = bool(
        singleton_automation_eligible or pair_automation_eligible
    )
    artifact_core = {
        "schemaVersion": READER_CALIBRATION_SCHEMA_VERSION,
        "sourceCohortId": source_cohort_id,
        "policy": "calibrated_semantic_state_or_abstain",
        "readerInputModes": sorted(
            {
                str(case["inputMode"])
                for case in (*normalized, *normalized_pairs)
            }
        ),
        "readerContracts": [
            dict(contract) for contract in reader_contracts
        ],
        "thresholds": {
            "minimumStateSupport": minimum_state_support,
            "minimumContentUnits": minimum_content_units,
            "minimumCvPredictions": minimum_cv_predictions,
            "minimumCvPrecision": minimum_cv_precision,
            "minimumPairSupport": minimum_pair_support,
            "minimumPairContentUnits": minimum_pair_content_units,
            "minimumPairCvPredictions": minimum_pair_cv_predictions,
            "minimumPairCvContentUnits": (
                minimum_pair_cv_content_units
            ),
        },
        "caseCount": len(normalized),
        "pairCaseCount": len(normalized_pairs),
        "contentUnitCount": len(content_units),
        "candidateRuleCount": len(candidate_rules),
        "acceptedRules": final_rules,
        "candidatePairRuleCount": len(candidate_pair_rules),
        "acceptedPairRules": final_pair_rules,
        "groupedCrossValidation": {
            "foldUnit": "content_unit",
            "foldCount": len(content_units),
            "predictionCount": len(cv_predictions),
            "correctCount": cv_correct,
            "falsePositiveCount": len(cv_predictions) - cv_correct,
            "precision": cv_precision,
            "byReader": by_reader,
        },
        "acceptedRuleCrossValidation": {
            "foldUnit": "content_unit",
            "foldCount": len(content_units),
            "predictionCount": len(accepted_cv_predictions),
            "correctCount": accepted_cv_correct,
            "falsePositiveCount": (
                len(accepted_cv_predictions) - accepted_cv_correct
            ),
            "precision": accepted_cv_precision,
            "byReader": accepted_by_reader,
        },
        "acceptedPairRuleCrossValidation": {
            "foldUnit": "content_unit",
            "foldCount": len(content_units),
            "predictionCount": len(accepted_pair_cv_predictions),
            "correctCount": accepted_pair_cv_correct,
            "falsePositiveCount": (
                len(accepted_pair_cv_predictions)
                - accepted_pair_cv_correct
            ),
            "precision": accepted_pair_cv_precision,
        },
        "singletonAutomationEligible": singleton_automation_eligible,
        "pairAutomationEligible": pair_automation_eligible,
        "automationEligible": automation_eligible,
        "validationDataUsed": False,
        "sealedTestDataUsed": False,
    }
    digest = _sha256_json(artifact_core)
    return {
        **artifact_core,
        "calibrationId": f"atr-{digest[:16]}",
        "artifactDigest": digest,
    }


def calibrated_state_is_eligible(
    calibration: Mapping[str, Any],
    *,
    reader_id: str,
    predicted_state: str,
    confidence: float,
    input_mode: str,
) -> bool:
    """Return whether one exact reader state passed discovery calibration."""

    if (
        calibration.get("schemaVersion")
        != READER_CALIBRATION_SCHEMA_VERSION
        or calibration.get("automationEligible") is not True
        or input_mode not in set(
            calibration.get("readerInputModes") or ()
        )
    ):
        return False
    thresholds = calibration.get("thresholds") or {}
    accepted_cv = calibration.get("acceptedRuleCrossValidation") or {}
    minimum_state_support = int(
        thresholds.get("minimumStateSupport") or 0
    )
    minimum_content_units = int(
        thresholds.get("minimumContentUnits") or 0
    )
    minimum_cv_predictions = int(
        thresholds.get("minimumCvPredictions") or 0
    )
    minimum_cv_precision = float(
        thresholds.get("minimumCvPrecision") or 1.0
    )
    if (
        int(accepted_cv.get("predictionCount") or 0)
        < minimum_cv_predictions
        or float(accepted_cv.get("precision") or 0.0)
        < minimum_cv_precision
    ):
        return False
    for rule in calibration.get("acceptedRules") or ():
        if (
            str(rule.get("readerId") or "") == reader_id
            and str(rule.get("inputMode") or "") == input_mode
            and str(rule.get("predictedState") or "") == predicted_state
            and int(rule.get("groupedCvPredictionCount") or 0)
            >= minimum_state_support
            and int(rule.get("groupedCvContentUnitCount") or 0)
            >= minimum_content_units
            and float(rule.get("groupedCvPrecision") or 0.0)
            >= minimum_cv_precision
            and confidence >= float(rule.get("minimumConfidence") or 1.0)
        ):
            return True
    return False


def calibrated_pair_state(
    calibration: Mapping[str, Any],
    *,
    reader_states: Sequence[Mapping[str, Any]],
    input_mode: str,
) -> str | None:
    """Return a discovery-qualified truth state for exact reader outcomes."""

    if (
        calibration.get("schemaVersion")
        != READER_CALIBRATION_SCHEMA_VERSION
        or calibration.get("automationEligible") is not True
        or calibration.get("pairAutomationEligible") is not True
        or input_mode not in set(
            calibration.get("readerInputModes") or ()
        )
    ):
        return None
    try:
        pair_signature = reader_pair_signature(reader_states)
    except ReaderCalibrationError:
        return None
    thresholds = calibration.get("thresholds") or {}
    accepted_cv = (
        calibration.get("acceptedPairRuleCrossValidation") or {}
    )
    minimum_predictions = int(
        thresholds.get("minimumPairCvPredictions") or 0
    )
    minimum_units = int(
        thresholds.get("minimumPairCvContentUnits") or 0
    )
    minimum_precision = float(
        thresholds.get("minimumCvPrecision") or 1.0
    )
    if (
        int(accepted_cv.get("predictionCount") or 0)
        < minimum_predictions
        or float(accepted_cv.get("precision") or 0.0)
        < minimum_precision
    ):
        return None
    for rule in calibration.get("acceptedPairRules") or ():
        if (
            str(rule.get("inputMode") or "") == input_mode
            and str(rule.get("pairSignature") or "") == pair_signature
            and int(rule.get("groupedCvPredictionCount") or 0)
            >= minimum_predictions
            and int(rule.get("groupedCvContentUnitCount") or 0)
            >= minimum_units
            and float(rule.get("groupedCvPrecision") or 0.0)
            >= minimum_precision
        ):
            return str(rule.get("predictedState") or "") or None
    return None
