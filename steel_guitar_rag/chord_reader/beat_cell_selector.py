"""Development-only grouped selector for prediction-only beat-cell evidence.

The feature/example construction boundary is owned by :mod:`beat_cell_examples`.
This module accepts only that exact, sealed artifact, reuses the byte-pinned
bar-selector mathematical core, and emits a distinct beat-cell selector
artifact.  It performs no calibration, threshold selection, test access, or
player authorization.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import math
from typing import Any

from . import bar_selector as _bar
from .bar_promotion import canonical_sha256
from .beat_cell_examples import (
    BEAT_CELL_EXAMPLES_SCHEMA,
    BEAT_CELL_FEATURE_ROW_SCHEMA,
    validate_beat_cell_examples_artifact,
    validate_beat_cell_feature_row,
)
from .beat_cell_stage2_contract import (
    BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
    BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    load_beat_cell_stage2_authority,
)


BEAT_CELL_SELECTOR_SCHEMA = "chord_runtime_beat_cell_correctness_selector_v1"
BEAT_CELL_SELECTOR_APPLICATION_SCHEMA = "chord_runtime_beat_cell_correctness_probability_v1"
BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256 = "c9d7efcec0ee85d0ee0697a1fe551bb270702bb730b25da3765a72acb475637b"

_STRUCTURAL_ELIGIBILITY = "predictionProduct is non-null and predictionCoverage>=0.75 and predictionDominance>=0.75"
_APPLICATION_POLICY = (
    "split-neutral prediction-only feature-row validation; no development track allowlist or Stage-1 projection "
    "equality; no reference, label, cutoff, calibration, test, player, or promotion decision"
)
_PRECISION_COVERAGE_POLICY = "fixed descriptive coverage targets; no operating threshold selected"
_SHA256_HEX = frozenset("0123456789abcdef")


class BeatCellSelectorError(ValueError):
    """A beat-cell selector input, artifact, or application failed closed."""


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as error:  # pragma: no cover - required project dependency
        raise RuntimeError("Beat-cell selector training requires NumPy.") from error
    return np


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BeatCellSelectorError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise BeatCellSelectorError(f"{name} must be an array.")
    return value


def _exact_fields(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise BeatCellSelectorError(f"{name} fields are not exact: missing={missing}, extra={extra}.")


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise BeatCellSelectorError(f"{name} must be a trimmed, nonempty string without NUL bytes.")
    return value


def _sha256(value: Any, name: str) -> str:
    digest = _string(value, name)
    if len(digest) != 64 or any(character not in _SHA256_HEX for character in digest):
        raise BeatCellSelectorError(f"{name} must be a lowercase SHA-256 digest.")
    return digest


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise BeatCellSelectorError(f"{name} must be an integer >= {minimum}.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BeatCellSelectorError(f"{name} must be numeric.")
    number = float(value)
    if not math.isfinite(number):
        raise BeatCellSelectorError(f"{name} must be finite.")
    return number


def _unsigned(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    output = deepcopy(dict(value))
    output.pop(field, None)
    return output


def _core_contract() -> tuple[dict[str, Any], tuple[str, ...], Mapping[str, Any]]:
    """Revalidate the authority and byte-pinned core before every public operation."""

    authority = load_beat_cell_stage2_authority()
    if canonical_sha256(authority) != BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256:
        raise BeatCellSelectorError("The beat-cell Stage-2 authority canonical hash changed.")
    feature_math = _mapping(authority.get("featureMath"), "authority.featureMath")
    selector_core = _mapping(authority.get("selectorCore"), "authority.selectorCore")
    stage_b = _mapping(authority.get("stageB"), "authority.stageB")
    if (
        canonical_sha256(feature_math) != BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256
        or canonical_sha256(selector_core) != BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256
        or canonical_sha256(stage_b) != BEAT_CELL_STAGE_B_PROJECTION_SHA256
    ):
        raise BeatCellSelectorError("A beat-cell Stage-2 projection hash changed.")
    names = tuple(_sequence(feature_math.get("featureNames"), "authority.featureMath.featureNames"))
    if len(names) != 48 or len(set(names)) != 48 or any(not isinstance(name, str) or not name for name in names):
        raise BeatCellSelectorError("The frozen beat-cell feature-name vector is invalid.")
    helper_names = tuple(_sequence(selector_core.get("sourceHelperNames"), "selectorCore.sourceHelperNames"))
    if any(not callable(getattr(_bar, name, None)) for name in helper_names):
        raise BeatCellSelectorError("The pinned bar-selector core is missing a required helper.")
    expected_core = {
        "sourceModuleFileSha256": BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256,
        "sourceBarSelectorConfigSha256": _bar.BAR_SELECTOR_CONFIG_SHA256,
        "outerFoldCount": _bar.OUTER_FOLD_COUNT,
        "innerFoldCount": _bar.INNER_FOLD_COUNT,
        "grid": [dict(value) for value in _bar.ELASTIC_NET_GRID],
        "maxIterations": _bar.OPTIMIZER_MAX_ITERATIONS,
        "tolerance": _bar.OPTIMIZER_TOLERANCE,
        "probabilityFloor": _bar.PROBABILITY_FLOOR,
        "optimizer": _bar.OPTIMIZER_KIND,
        "convergence": _bar.OPTIMIZER_CONVERGENCE,
        "linkFunction": _bar.LINK_FUNCTION,
        "outerFoldSalt": "bar-selector-outer-v1",
        "finalInnerFoldSalt": "bar-selector-inner-v1-final",
    }
    if any(selector_core.get(name) != expected for name, expected in expected_core.items()):
        raise BeatCellSelectorError("The imported bar-selector core disagrees with its frozen projection.")
    return authority, names, selector_core


_INITIAL_AUTHORITY, BEAT_CELL_FEATURE_NAMES, _INITIAL_SELECTOR_CORE = _core_contract()
BEAT_CELL_SELECTOR_ESTIMAND = str(_INITIAL_SELECTOR_CORE["estimand"])
BEAT_CELL_SELECTOR_OOF_DENOMINATOR = str(_INITIAL_SELECTOR_CORE["oofDenominator"])

_SELECTOR_CONFIG = {
    "schemaVersion": BEAT_CELL_SELECTOR_SCHEMA,
    "authorityCanonicalSha256": BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
    "featureRowSchemaVersion": BEAT_CELL_FEATURE_ROW_SCHEMA,
    "featureNames": list(BEAT_CELL_FEATURE_NAMES),
    "featureMathProjectionSha256": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    "stageBProjectionSha256": BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    "selectorCoreProjectionSha256": BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
    "selectorCoreSourceModuleSha256": BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256,
    "developmentSplit": "development",
    "target": "correct:boolean",
    "estimand": BEAT_CELL_SELECTOR_ESTIMAND,
    "oofDenominator": BEAT_CELL_SELECTOR_OOF_DENOMINATOR,
    "structuralEligibility": _STRUCTURAL_ELIGIBILITY,
    "applicationPolicy": _APPLICATION_POLICY,
    "groupField": "confidenceGroupId",
    "groupFallback": None,
    "outerFoldCount": _bar.OUTER_FOLD_COUNT,
    "innerFoldCount": _bar.INNER_FOLD_COUNT,
    "foldAssignment": "sha256-salted-group-order-round-robin-v1",
    "sampleWeight": "each confidenceGroupId has total sample weight exactly one in every partition",
    "grid": [dict(value) for value in _bar.ELASTIC_NET_GRID],
    "optimizer": _bar.OPTIMIZER_KIND,
    "convergence": _bar.OPTIMIZER_CONVERGENCE,
    "linkFunction": _bar.LINK_FUNCTION,
    "maxIterations": _bar.OPTIMIZER_MAX_ITERATIONS,
    "tolerance": _bar.OPTIMIZER_TOLERANCE,
    "precisionCoverageTargets": list(_bar.PRECISION_COVERAGE_TARGETS),
    "selectorCandidateCount": 1,
    "operatingThresholdSelection": None,
}
BEAT_CELL_SELECTOR_CONFIG_SHA256 = canonical_sha256(_SELECTOR_CONFIG)


def _validated_feature_values(value: Any, name: str) -> list[float | None]:
    feature_values = _mapping(value, name)
    if set(feature_values) != set(BEAT_CELL_FEATURE_NAMES):
        raise BeatCellSelectorError(f"{name} must contain the exact frozen feature-name set.")
    output: list[float | None] = []
    for feature_name in BEAT_CELL_FEATURE_NAMES:
        item = feature_values[feature_name]
        if item is None:
            output.append(None)
        else:
            output.append(_finite(item, f"{name}.{feature_name}"))
    return output


def _validated_examples(examples_artifact: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        source = validate_beat_cell_examples_artifact(examples_artifact)
    except (TypeError, ValueError, OverflowError) as error:
        raise BeatCellSelectorError("The beat-cell examples artifact failed its owner validator.") from error
    source = dict(_mapping(source, "examplesArtifact"))
    if (
        source.get("schemaVersion") != BEAT_CELL_EXAMPLES_SCHEMA
        or source.get("split") != "development"
        or source.get("developmentOnly") is not True
        or source.get("promotionEligible") is not False
    ):
        raise BeatCellSelectorError("Selector examples must retain the frozen development-only envelope.")
    if tuple(_sequence(source.get("featureNames"), "examplesArtifact.featureNames")) != BEAT_CELL_FEATURE_NAMES:
        raise BeatCellSelectorError("Selector examples changed the frozen feature-name vector.")
    source_artifact_sha256 = _sha256(source.get("artifactSha256"), "examplesArtifact.artifactSha256")
    if canonical_sha256(_unsigned(source, "artifactSha256")) != source_artifact_sha256:
        raise BeatCellSelectorError("examplesArtifact.artifactSha256 is stale.")
    values = list(_sequence(source.get("examples"), "examplesArtifact.examples"))
    if not values:
        raise BeatCellSelectorError("Beat-cell selector training requires development examples.")
    example_set_sha256 = _sha256(source.get("exampleSetSha256"), "examplesArtifact.exampleSetSha256")
    if canonical_sha256(values) != example_set_sha256:
        raise BeatCellSelectorError("examplesArtifact.exampleSetSha256 is stale.")
    rows: list[dict[str, Any]] = []
    logical_keys: set[tuple[str, int]] = set()
    example_keys: set[str] = set()
    for index, raw in enumerate(values):
        row = dict(_mapping(raw, f"examples[{index}]"))
        example_key = _sha256(row.get("exampleKey"), f"examples[{index}].exampleKey")
        track_id = _string(row.get("trackId"), f"examples[{index}].trackId")
        cell_index = _integer(row.get("cellIndex"), f"examples[{index}].cellIndex")
        duration = _integer(row.get("durationMilliseconds"), f"examples[{index}].durationMilliseconds", minimum=1)
        dataset_id = _string(row.get("datasetId"), f"examples[{index}].datasetId")
        group = _string(row.get("confidenceGroupId"), f"examples[{index}].confidenceGroupId")
        role = _string(row.get("role"), f"examples[{index}].role")
        guitarset_role = row.get("guitarsetRole")
        if guitarset_role not in (None, "comp", "solo"):
            raise BeatCellSelectorError("examples[].guitarsetRole must be null, comp, or solo.")
        if dataset_id == "guitarset" and guitarset_role not in ("comp", "solo"):
            raise BeatCellSelectorError("Every GuitarSet example must retain its comp/solo disclosure role.")
        if dataset_id != "guitarset" and guitarset_role is not None:
            raise BeatCellSelectorError("Only GuitarSet examples may carry a guitarsetRole.")
        correct = row.get("correct")
        if not isinstance(correct, bool):
            raise BeatCellSelectorError("examples[].correct must be boolean audit metadata.")
        feature_vector = _validated_feature_values(row.get("featureValues"), f"examples[{index}].featureValues")
        for field in (
            "exampleSha256",
            "featureValuesSha256",
            "featureRowSha256",
            "featureSummaryArtifactSha256",
            "featureSetArtifactSha256",
            "sourceBeatCellSha256",
            "predictionIdentitySha256",
            "audioLineageRowSha256",
            "stage1OutcomeRowSha256",
            "stage1ArtifactSha256",
            "sourceGroupTrackRowSha256",
        ):
            _sha256(row.get(field), f"examples[{index}].{field}")
        logical_key = (track_id, cell_index)
        if logical_key in logical_keys or example_key in example_keys:
            raise BeatCellSelectorError("Beat-cell selector examples contain a duplicate logical cell or exampleKey.")
        logical_keys.add(logical_key)
        example_keys.add(example_key)
        rows.append(
            {
                **row,
                "exampleKey": example_key,
                "trackId": track_id,
                "cellIndex": cell_index,
                "durationMilliseconds": duration,
                "datasetId": dataset_id,
                "role": role,
                "confidenceGroupId": group,
                "guitarsetRole": guitarset_role,
                "correct": correct,
                "features": feature_vector,
            }
        )
    rows.sort(key=lambda row: row["exampleKey"])
    if [row["exampleKey"] for row in rows] != sorted(example_keys):  # pragma: no cover - defensive
        raise RuntimeError("Internal beat-cell example order is not canonical.")
    return source, rows


def _set_sha256(rows: Sequence[Mapping[str, Any]], field: str) -> str:
    return canonical_sha256(sorted({str(row[field]) for row in rows}))


def _input_payload(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "exampleKey": row["exampleKey"],
            "exampleSha256": row["exampleSha256"],
            "trackId": row["trackId"],
            "cellIndex": row["cellIndex"],
            "durationMilliseconds": row["durationMilliseconds"],
            "datasetId": row["datasetId"],
            "role": row["role"],
            "guitarsetRole": row["guitarsetRole"],
            "confidenceGroupId": row["confidenceGroupId"],
            "correct": row["correct"],
            "featureValuesSha256": row["featureValuesSha256"],
            "featureRowSha256": row["featureRowSha256"],
            "featureSummaryArtifactSha256": row["featureSummaryArtifactSha256"],
            "featureSetArtifactSha256": row["featureSetArtifactSha256"],
            "sourceBeatCellSha256": row["sourceBeatCellSha256"],
            "predictionIdentitySha256": row["predictionIdentitySha256"],
            "audioLineageRowSha256": row["audioLineageRowSha256"],
            "stage1OutcomeRowSha256": row["stage1OutcomeRowSha256"],
            "stage1ArtifactSha256": row["stage1ArtifactSha256"],
            "sourceGroupTrackRowSha256": row["sourceGroupTrackRowSha256"],
        }
        for row in rows
    ]


def _evaluation(
    probabilities: Any, labels: Any, weights: Any, keys: Sequence[str], duration: int, np: Any
) -> dict[str, Any]:
    brier = float((weights * (probabilities - labels) ** 2).sum() / weights.sum())
    return {
        "estimand": BEAT_CELL_SELECTOR_ESTIMAND,
        "denominator": BEAT_CELL_SELECTOR_OOF_DENOMINATOR,
        "denominatorExampleCount": len(keys),
        "denominatorDurationMilliseconds": duration,
        "groupBalancedLogLoss": _bar._weighted_log_loss(probabilities, labels, weights, np),
        "groupBalancedBrierScore": brier,
        "groupBalancedAreaUnderRiskCoverage": _bar._aurc(probabilities, labels, weights, keys),
        "precisionCoveragePolicy": _PRECISION_COVERAGE_POLICY,
        "precisionCoverage": _bar._precision_coverage(probabilities, labels, weights, keys),
    }


def train_beat_cell_selector(examples: Mapping[str, Any]) -> dict[str, Any]:
    """Train the sole preregistered candidate from one sealed examples artifact."""

    _core_contract()
    source, rows = _validated_examples(examples)
    np = _numpy()
    matrix = np.asarray(
        [[np.nan if value is None else value for value in row["features"]] for row in rows],
        dtype=np.float64,
    )
    if matrix.shape != (len(rows), len(BEAT_CELL_FEATURE_NAMES)) or bool(np.isinf(matrix).any()):
        raise BeatCellSelectorError("The beat-cell selector matrix is invalid.")
    labels = np.asarray([1.0 if row["correct"] else 0.0 for row in rows], dtype=np.float64)
    groups = [str(row["confidenceGroupId"]) for row in rows]
    unique_groups = sorted(set(groups))
    if len(unique_groups) < _bar.OUTER_FOLD_COUNT:
        raise BeatCellSelectorError("Beat-cell selector training has too few confidence groups.")
    if float(labels.sum()) <= 0.0 or float(labels.sum()) >= len(labels):
        raise BeatCellSelectorError("Beat-cell selector training requires correct and incorrect examples.")

    outer_assignment = _bar._folds(groups, _bar.OUTER_FOLD_COUNT, "bar-selector-outer-v1")
    outer_folds = np.asarray([outer_assignment[group] for group in groups], dtype=np.int64)
    oof_probability = np.zeros(len(rows), dtype=np.float64)
    outer_reports: list[dict[str, Any]] = []
    fold_plan: dict[str, Any] = {"outer": outer_assignment, "innerByOuterFold": {}}
    for outer_fold in range(_bar.OUTER_FOLD_COUNT):
        validate_indices = np.flatnonzero(outer_folds == outer_fold)
        train_indices = np.flatnonzero(outer_folds != outer_fold)
        outer_groups = [groups[int(index)] for index in train_indices]
        selected, scores, inner_assignment = _bar._select_hyperparameters(
            matrix[train_indices],
            labels[train_indices],
            outer_groups,
            np,
            salt=f"bar-selector-inner-v1-outer-{outer_fold}",
        )
        probability, fitted = _bar._fit_predict(
            matrix,
            labels,
            groups,
            train_indices,
            validate_indices,
            selected,
            np,
        )
        if not fitted["converged"]:
            raise BeatCellSelectorError(f"The outer-fold {outer_fold} fit did not converge.")
        oof_probability[validate_indices] = probability
        fold_plan["innerByOuterFold"][str(outer_fold)] = inner_assignment
        outer_reports.append(
            {
                "outerFold": outer_fold,
                "selectedHyperparameters": selected,
                "innerCvScores": scores,
                "innerFoldAssignments": [
                    {"confidenceGroupId": group, "innerFold": inner_assignment[group]}
                    for group in sorted(inner_assignment)
                ],
                "fitIterations": int(fitted["iterations"]),
                "fitConverged": bool(fitted["converged"]),
            }
        )

    final_hyperparameters, final_scores, final_inner_assignment = _bar._select_hyperparameters(
        matrix,
        labels,
        groups,
        np,
        salt="bar-selector-inner-v1-final",
    )
    fold_plan["finalInner"] = final_inner_assignment
    final_weights = _bar._group_weights(groups, np)
    imputation, center, scale, all_missing = _bar._fit_preprocessor(matrix, final_weights, np)
    transformed = _bar._transform(matrix, imputation, center, scale, np)
    coefficients, intercept, iterations, converged = _bar._fit_elastic_net(
        transformed,
        labels,
        final_weights,
        final_hyperparameters,
        np,
    )
    if not converged:
        raise BeatCellSelectorError("The final all-development selector refit did not converge.")

    duration = sum(int(row["durationMilliseconds"]) for row in rows)
    input_payload = _input_payload(rows)
    group_payload = [
        {
            "confidenceGroupId": group,
            "exampleCount": groups.count(group),
            "durationMilliseconds": sum(
                int(row["durationMilliseconds"]) for row in rows if row["confidenceGroupId"] == group
            ),
            "sampleWeight": math.fsum(
                float(final_weights[index]) for index, value in enumerate(groups) if value == group
            ),
        }
        for group in unique_groups
    ]
    oof_payload = [
        {
            "exampleKey": row["exampleKey"],
            "trackId": row["trackId"],
            "cellIndex": row["cellIndex"],
            "datasetId": row["datasetId"],
            "role": row["role"],
            "guitarsetRole": row["guitarsetRole"],
            "confidenceGroupId": row["confidenceGroupId"],
            "durationMilliseconds": row["durationMilliseconds"],
            "outerFold": int(outer_folds[index]),
            "probability": float(oof_probability[index]),
            "correct": bool(row["correct"]),
            "sampleWeight": float(final_weights[index]),
        }
        for index, row in enumerate(rows)
    ]
    label_audits = deepcopy(dict(_mapping(source.get("labelAudits"), "examplesArtifact.labelAudits")))
    feature_set_values = {str(row["featureSetArtifactSha256"]) for row in rows}
    if len(feature_set_values) != 1:
        raise BeatCellSelectorError("Beat-cell examples must bind exactly one Stage-A feature-set artifact.")
    artifact: dict[str, Any] = {
        "schemaVersion": BEAT_CELL_SELECTOR_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "playerUseAuthorized": False,
        "calibrationAccess": "closed",
        "testAccess": "closed",
        "operatingThreshold": None,
        "authorityCanonicalSha256": BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
        "featureRowSchemaVersion": BEAT_CELL_FEATURE_ROW_SCHEMA,
        "featureNames": list(BEAT_CELL_FEATURE_NAMES),
        "featureMathProjectionSha256": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
        "stageBProjectionSha256": BEAT_CELL_STAGE_B_PROJECTION_SHA256,
        "selectorCoreProjectionSha256": BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
        "selectorCoreSourceModuleSha256": BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256,
        "training": {
            "split": "development",
            "target": "correct:boolean",
            "estimand": BEAT_CELL_SELECTOR_ESTIMAND,
            "oofDenominator": BEAT_CELL_SELECTOR_OOF_DENOMINATOR,
            "structuralEligibilityInput": _STRUCTURAL_ELIGIBILITY,
            "groupField": "confidenceGroupId",
            "groupFallback": None,
            "groupSampleWeight": "one-per-confidence-group",
            "outerFoldCount": _bar.OUTER_FOLD_COUNT,
            "innerFoldCount": _bar.INNER_FOLD_COUNT,
            "selectorCandidateCount": 1,
            "exampleCount": len(rows),
            "exampleDurationMilliseconds": duration,
            "groupCount": len(unique_groups),
            "correctCount": int(labels.sum()),
            "incorrectCount": int(len(labels) - labels.sum()),
            "inputSetSha256": canonical_sha256(
                {
                    "sourceExamplesArtifactSha256": source["artifactSha256"],
                    "sourceExampleSetSha256": source["exampleSetSha256"],
                    "rows": input_payload,
                }
            ),
            "sourceExamplesArtifactSha256": source["artifactSha256"],
            "sourceExampleSetSha256": source["exampleSetSha256"],
            "sourceFeatureSetArtifactSha256": next(iter(feature_set_values)),
            "sourceFeatureRowSetSha256": _set_sha256(rows, "featureRowSha256"),
            "sourceFeatureSummaryArtifactSetSha256": _set_sha256(rows, "featureSummaryArtifactSha256"),
            "sourceStage1ArtifactSetSha256": _set_sha256(rows, "stage1ArtifactSha256"),
            "sourcePredictionIdentitySetSha256": _set_sha256(rows, "predictionIdentitySha256"),
            "sourceAudioLineageRowSetSha256": _set_sha256(rows, "audioLineageRowSha256"),
            "sourceLabelAudits": label_audits,
            "sourceLabelAuditsSha256": canonical_sha256(label_audits),
            "groupSetSha256": canonical_sha256(group_payload),
            "foldPlanSha256": canonical_sha256(fold_plan),
            "oofPredictionSetSha256": canonical_sha256(oof_payload),
            "configSha256": BEAT_CELL_SELECTOR_CONFIG_SHA256,
            "outerFoldAssignments": [
                {"confidenceGroupId": group, "outerFold": outer_assignment[group]} for group in sorted(outer_assignment)
            ],
            "outerHyperparameterSelection": outer_reports,
            "oofAuditRows": oof_payload,
            "finalHyperparameterSelection": {
                "selectedHyperparameters": final_hyperparameters,
                "innerCvScores": final_scores,
                "innerFoldAssignments": [
                    {"confidenceGroupId": group, "innerFold": final_inner_assignment[group]}
                    for group in sorted(final_inner_assignment)
                ],
                "innerFoldAssignmentSha256": canonical_sha256(final_inner_assignment),
            },
            "groupWeightAudit": group_payload,
        },
        "outOfFoldEvaluation": _evaluation(
            oof_probability,
            labels,
            final_weights,
            [str(row["exampleKey"]) for row in rows],
            duration,
            np,
        ),
        "estimator": {
            "kind": "standardized-elastic-net-logistic-regression",
            "linkFunction": _bar.LINK_FUNCTION,
            "imputation": "group-weighted-training-median",
            "imputationValues": imputation.tolist(),
            "allMissingFeatureNames": [
                BEAT_CELL_FEATURE_NAMES[index] for index, missing in enumerate(all_missing.tolist()) if missing
            ],
            "center": center.tolist(),
            "scale": scale.tolist(),
            "coefficients": coefficients.tolist(),
            "intercept": float(intercept),
            "hyperparameters": final_hyperparameters,
            "optimizer": {
                "kind": _bar.OPTIMIZER_KIND,
                "convergence": _bar.OPTIMIZER_CONVERGENCE,
                "iterations": int(iterations),
                "converged": bool(converged),
                "maximumIterations": _bar.OPTIMIZER_MAX_ITERATIONS,
                "tolerance": _bar.OPTIMIZER_TOLERANCE,
            },
        },
    }
    artifact["artifactSha256"] = canonical_sha256(artifact)
    validate_beat_cell_selector_artifact(artifact, source)
    return artifact


_ARTIFACT_FIELDS = frozenset(
    {
        "schemaVersion",
        "developmentOnly",
        "promotionEligible",
        "playerUseAuthorized",
        "calibrationAccess",
        "testAccess",
        "operatingThreshold",
        "authorityCanonicalSha256",
        "featureRowSchemaVersion",
        "featureNames",
        "featureMathProjectionSha256",
        "stageBProjectionSha256",
        "selectorCoreProjectionSha256",
        "selectorCoreSourceModuleSha256",
        "training",
        "outOfFoldEvaluation",
        "estimator",
        "artifactSha256",
    }
)
_TRAINING_FIELDS = frozenset(
    {
        "split",
        "target",
        "estimand",
        "oofDenominator",
        "structuralEligibilityInput",
        "groupField",
        "groupFallback",
        "groupSampleWeight",
        "outerFoldCount",
        "innerFoldCount",
        "selectorCandidateCount",
        "exampleCount",
        "exampleDurationMilliseconds",
        "groupCount",
        "correctCount",
        "incorrectCount",
        "inputSetSha256",
        "sourceExamplesArtifactSha256",
        "sourceExampleSetSha256",
        "sourceFeatureSetArtifactSha256",
        "sourceFeatureRowSetSha256",
        "sourceFeatureSummaryArtifactSetSha256",
        "sourceStage1ArtifactSetSha256",
        "sourcePredictionIdentitySetSha256",
        "sourceAudioLineageRowSetSha256",
        "sourceLabelAudits",
        "sourceLabelAuditsSha256",
        "groupSetSha256",
        "foldPlanSha256",
        "oofPredictionSetSha256",
        "configSha256",
        "outerFoldAssignments",
        "outerHyperparameterSelection",
        "oofAuditRows",
        "finalHyperparameterSelection",
        "groupWeightAudit",
    }
)
_CV_SCORE_FIELDS = frozenset({"gridIndex", "hyperparameters", "groupBalancedLogLoss"})
_FOLD_ASSIGNMENT_FIELDS = frozenset({"confidenceGroupId", "outerFold"})
_INNER_ASSIGNMENT_FIELDS = frozenset({"confidenceGroupId", "innerFold"})
_OUTER_REPORT_FIELDS = frozenset(
    {
        "outerFold",
        "selectedHyperparameters",
        "innerCvScores",
        "innerFoldAssignments",
        "fitIterations",
        "fitConverged",
    }
)
_FINAL_SELECTION_FIELDS = frozenset(
    {"selectedHyperparameters", "innerCvScores", "innerFoldAssignments", "innerFoldAssignmentSha256"}
)
_GROUP_WEIGHT_FIELDS = frozenset({"confidenceGroupId", "exampleCount", "durationMilliseconds", "sampleWeight"})
_OOF_FIELDS = frozenset(
    {
        "exampleKey",
        "trackId",
        "cellIndex",
        "datasetId",
        "role",
        "guitarsetRole",
        "confidenceGroupId",
        "durationMilliseconds",
        "outerFold",
        "probability",
        "correct",
        "sampleWeight",
    }
)
_EVALUATION_FIELDS = frozenset(
    {
        "estimand",
        "denominator",
        "denominatorExampleCount",
        "denominatorDurationMilliseconds",
        "groupBalancedLogLoss",
        "groupBalancedBrierScore",
        "groupBalancedAreaUnderRiskCoverage",
        "precisionCoveragePolicy",
        "precisionCoverage",
    }
)
_PRECISION_COVERAGE_FIELDS = frozenset(
    {
        "targetCoverage",
        "realizableCoverage",
        "groupBalancedPrecision",
        "groupBalancedRisk",
        "minimumProbabilityAtDescriptivePoint",
    }
)
_ESTIMATOR_FIELDS = frozenset(
    {
        "kind",
        "linkFunction",
        "imputation",
        "imputationValues",
        "allMissingFeatureNames",
        "center",
        "scale",
        "coefficients",
        "intercept",
        "hyperparameters",
        "optimizer",
    }
)
_OPTIMIZER_FIELDS = frozenset({"kind", "convergence", "iterations", "converged", "maximumIterations", "tolerance"})


def _validated_cv_scores(value: Any, name: str) -> list[dict[str, Any]]:
    raw_scores = _sequence(value, name)
    if len(raw_scores) != len(_bar.ELASTIC_NET_GRID):
        raise BeatCellSelectorError(f"{name} must report the sole frozen grid.")
    scores: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_scores):
        score = _mapping(raw, f"{name}[{index}]")
        _exact_fields(score, _CV_SCORE_FIELDS, f"{name}[{index}]")
        if score.get("gridIndex") != index or score.get("hyperparameters") != _bar.ELASTIC_NET_GRID[index]:
            raise BeatCellSelectorError(f"{name} changed the frozen grid order.")
        if _finite(score.get("groupBalancedLogLoss"), f"{name}[{index}].groupBalancedLogLoss") < 0.0:
            raise BeatCellSelectorError(f"{name} contains a negative log loss.")
        scores.append(dict(score))
    return scores


def _validated_assignments(value: Any, name: str, *, field: str, count: int) -> dict[str, int]:
    expected_fields = _FOLD_ASSIGNMENT_FIELDS if field == "outerFold" else _INNER_ASSIGNMENT_FIELDS
    assignments: dict[str, int] = {}
    ordered_groups: list[str] = []
    for index, raw in enumerate(_sequence(value, name)):
        row = _mapping(raw, f"{name}[{index}]")
        _exact_fields(row, expected_fields, f"{name}[{index}]")
        group = _string(row.get("confidenceGroupId"), f"{name}[{index}].confidenceGroupId")
        fold = _integer(row.get(field), f"{name}[{index}].{field}")
        if fold >= count or group in assignments:
            raise BeatCellSelectorError(f"{name} contains an invalid or duplicate assignment.")
        assignments[group] = fold
        ordered_groups.append(group)
    if ordered_groups != sorted(ordered_groups) or set(assignments.values()) != set(range(count)):
        raise BeatCellSelectorError(f"{name} is not canonical or does not populate every fold.")
    return assignments


def _validate_training_and_oof(
    training: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[float], list[float], list[float]]:
    _exact_fields(training, _TRAINING_FIELDS, "selector.training")
    if (
        training.get("split") != "development"
        or training.get("target") != "correct:boolean"
        or training.get("estimand") != BEAT_CELL_SELECTOR_ESTIMAND
        or training.get("oofDenominator") != BEAT_CELL_SELECTOR_OOF_DENOMINATOR
        or training.get("structuralEligibilityInput") != _STRUCTURAL_ELIGIBILITY
        or training.get("groupField") != "confidenceGroupId"
        or training.get("groupFallback") is not None
        or training.get("groupSampleWeight") != "one-per-confidence-group"
        or training.get("outerFoldCount") != _bar.OUTER_FOLD_COUNT
        or training.get("innerFoldCount") != _bar.INNER_FOLD_COUNT
        or training.get("selectorCandidateCount") != 1
        or training.get("configSha256") != BEAT_CELL_SELECTOR_CONFIG_SHA256
    ):
        raise BeatCellSelectorError("The selector training contract changed.")
    for field in (
        "inputSetSha256",
        "sourceExamplesArtifactSha256",
        "sourceExampleSetSha256",
        "sourceFeatureSetArtifactSha256",
        "sourceFeatureRowSetSha256",
        "sourceFeatureSummaryArtifactSetSha256",
        "sourceStage1ArtifactSetSha256",
        "sourcePredictionIdentitySetSha256",
        "sourceAudioLineageRowSetSha256",
        "sourceLabelAuditsSha256",
        "groupSetSha256",
        "foldPlanSha256",
        "oofPredictionSetSha256",
    ):
        _sha256(training.get(field), f"selector.training.{field}")
    label_audits = _mapping(training.get("sourceLabelAudits"), "selector.training.sourceLabelAudits")
    if canonical_sha256(label_audits) != training["sourceLabelAuditsSha256"]:
        raise BeatCellSelectorError("The selector source label-audit hash is stale.")
    example_count = _integer(training.get("exampleCount"), "selector.training.exampleCount", minimum=1)
    duration = _integer(
        training.get("exampleDurationMilliseconds"),
        "selector.training.exampleDurationMilliseconds",
        minimum=1,
    )
    group_count = _integer(training.get("groupCount"), "selector.training.groupCount", minimum=_bar.OUTER_FOLD_COUNT)
    correct_count = _integer(training.get("correctCount"), "selector.training.correctCount", minimum=1)
    incorrect_count = _integer(training.get("incorrectCount"), "selector.training.incorrectCount", minimum=1)
    if correct_count + incorrect_count != example_count:
        raise BeatCellSelectorError("The selector outcome counts do not match exampleCount.")

    group_rows = list(_sequence(training.get("groupWeightAudit"), "selector.training.groupWeightAudit"))
    if len(group_rows) != group_count:
        raise BeatCellSelectorError("The selector group-weight audit count changed.")
    group_counts: dict[str, int] = {}
    group_durations: dict[str, int] = {}
    ordered_groups: list[str] = []
    for index, raw in enumerate(group_rows):
        row = _mapping(raw, f"selector.training.groupWeightAudit[{index}]")
        _exact_fields(row, _GROUP_WEIGHT_FIELDS, f"selector.training.groupWeightAudit[{index}]")
        group = _string(row.get("confidenceGroupId"), "groupWeightAudit.confidenceGroupId")
        if group in group_counts:
            raise BeatCellSelectorError("The selector group-weight audit contains a duplicate group.")
        group_counts[group] = _integer(row.get("exampleCount"), "groupWeightAudit.exampleCount", minimum=1)
        group_durations[group] = _integer(
            row.get("durationMilliseconds"), "groupWeightAudit.durationMilliseconds", minimum=1
        )
        if not math.isclose(
            _finite(row.get("sampleWeight"), "groupWeightAudit.sampleWeight"), 1.0, rel_tol=0, abs_tol=1e-12
        ):
            raise BeatCellSelectorError("Every confidence group must retain exactly unit total sample mass.")
        ordered_groups.append(group)
    if ordered_groups != sorted(ordered_groups):
        raise BeatCellSelectorError("The selector group-weight audit is not canonically ordered.")
    if sum(group_counts.values()) != example_count or sum(group_durations.values()) != duration:
        raise BeatCellSelectorError("The selector group-weight count/duration totals are inconsistent.")
    if canonical_sha256(group_rows) != training["groupSetSha256"]:
        raise BeatCellSelectorError("The selector groupSetSha256 is stale.")

    outer_assignment = _validated_assignments(
        training.get("outerFoldAssignments"),
        "selector.training.outerFoldAssignments",
        field="outerFold",
        count=_bar.OUTER_FOLD_COUNT,
    )
    if set(outer_assignment) != set(group_counts) or outer_assignment != _bar._folds(
        list(group_counts), _bar.OUTER_FOLD_COUNT, "bar-selector-outer-v1"
    ):
        raise BeatCellSelectorError("The selector outer-fold assignment changed.")

    inner_by_outer: dict[str, dict[str, int]] = {}
    outer_reports = _sequence(training.get("outerHyperparameterSelection"), "outerHyperparameterSelection")
    if len(outer_reports) != _bar.OUTER_FOLD_COUNT:
        raise BeatCellSelectorError("The selector must report every outer fold once.")
    for expected_outer, raw in enumerate(outer_reports):
        report = _mapping(raw, f"outerHyperparameterSelection[{expected_outer}]")
        _exact_fields(report, _OUTER_REPORT_FIELDS, f"outerHyperparameterSelection[{expected_outer}]")
        if report.get("outerFold") != expected_outer:
            raise BeatCellSelectorError("The selector outer reports are not canonically ordered.")
        scores = _validated_cv_scores(report.get("innerCvScores"), "outer report innerCvScores")
        selected = min(scores, key=lambda row: (row["groupBalancedLogLoss"], row["gridIndex"]))
        if report.get("selectedHyperparameters") != selected["hyperparameters"]:
            raise BeatCellSelectorError("An outer report did not retain the minimum frozen-grid candidate.")
        assignments = _validated_assignments(
            report.get("innerFoldAssignments"),
            "outer report innerFoldAssignments",
            field="innerFold",
            count=_bar.INNER_FOLD_COUNT,
        )
        held_out = {group for group, fold in outer_assignment.items() if fold == expected_outer}
        expected_groups = set(group_counts) - held_out
        if set(assignments) != expected_groups or assignments != _bar._folds(
            list(expected_groups),
            _bar.INNER_FOLD_COUNT,
            f"bar-selector-inner-v1-outer-{expected_outer}",
        ):
            raise BeatCellSelectorError("An inner fold includes an outer-held-out group or changed its salt.")
        iterations = _integer(report.get("fitIterations"), "outer report fitIterations", minimum=1)
        if iterations > _bar.OPTIMIZER_MAX_ITERATIONS or report.get("fitConverged") is not True:
            raise BeatCellSelectorError("An outer fit did not retain a valid convergence audit.")
        inner_by_outer[str(expected_outer)] = assignments

    final_selection = _mapping(training.get("finalHyperparameterSelection"), "finalHyperparameterSelection")
    _exact_fields(final_selection, _FINAL_SELECTION_FIELDS, "finalHyperparameterSelection")
    final_scores = _validated_cv_scores(final_selection.get("innerCvScores"), "final innerCvScores")
    selected_final = min(final_scores, key=lambda row: (row["groupBalancedLogLoss"], row["gridIndex"]))
    if final_selection.get("selectedHyperparameters") != selected_final["hyperparameters"]:
        raise BeatCellSelectorError("The final refit did not retain the minimum frozen-grid candidate.")
    final_inner = _validated_assignments(
        final_selection.get("innerFoldAssignments"),
        "final innerFoldAssignments",
        field="innerFold",
        count=_bar.INNER_FOLD_COUNT,
    )
    if set(final_inner) != set(group_counts) or final_inner != _bar._folds(
        list(group_counts), _bar.INNER_FOLD_COUNT, "bar-selector-inner-v1-final"
    ):
        raise BeatCellSelectorError("The final inner-fold assignment changed.")
    if canonical_sha256(final_inner) != final_selection.get("innerFoldAssignmentSha256"):
        raise BeatCellSelectorError("The final inner-fold assignment hash is stale.")
    fold_plan = {"outer": outer_assignment, "innerByOuterFold": inner_by_outer, "finalInner": final_inner}
    if canonical_sha256(fold_plan) != training["foldPlanSha256"]:
        raise BeatCellSelectorError("The selector foldPlanSha256 is stale.")

    oof_rows: list[dict[str, Any]] = []
    keys: set[str] = set()
    observed_counts = {group: 0 for group in group_counts}
    observed_durations = {group: 0 for group in group_counts}
    observed_weights = {group: [] for group in group_counts}
    probabilities: list[float] = []
    labels: list[float] = []
    weights: list[float] = []
    for index, raw in enumerate(_sequence(training.get("oofAuditRows"), "selector.training.oofAuditRows")):
        row = dict(_mapping(raw, f"selector.training.oofAuditRows[{index}]"))
        _exact_fields(row, _OOF_FIELDS, f"selector.training.oofAuditRows[{index}]")
        key = _sha256(row.get("exampleKey"), "oofAuditRows.exampleKey")
        track_id = _string(row.get("trackId"), "oofAuditRows.trackId")
        cell_index = _integer(row.get("cellIndex"), "oofAuditRows.cellIndex")
        dataset_id = _string(row.get("datasetId"), "oofAuditRows.datasetId")
        role = _string(row.get("role"), "oofAuditRows.role")
        guitarset_role = row.get("guitarsetRole")
        if (
            guitarset_role not in (None, "comp", "solo")
            or (dataset_id == "guitarset" and guitarset_role not in ("comp", "solo"))
            or (dataset_id != "guitarset" and guitarset_role is not None)
        ):
            raise BeatCellSelectorError("An OOF row has an invalid GuitarSet role disclosure.")
        group = _string(row.get("confidenceGroupId"), "oofAuditRows.confidenceGroupId")
        cell_duration = _integer(row.get("durationMilliseconds"), "oofAuditRows.durationMilliseconds", minimum=1)
        fold = _integer(row.get("outerFold"), "oofAuditRows.outerFold")
        probability = _finite(row.get("probability"), "oofAuditRows.probability")
        correct = row.get("correct")
        sample_weight = _finite(row.get("sampleWeight"), "oofAuditRows.sampleWeight")
        if (
            key in keys
            or group not in group_counts
            or fold != outer_assignment[group]
            or not 0.0 <= probability <= 1.0
            or not isinstance(correct, bool)
            or sample_weight <= 0.0
        ):
            raise BeatCellSelectorError("An OOF row is duplicated, misgrouped, or invalid.")
        keys.add(key)
        observed_counts[group] += 1
        observed_durations[group] += cell_duration
        observed_weights[group].append(sample_weight)
        probabilities.append(probability)
        labels.append(1.0 if correct else 0.0)
        weights.append(sample_weight)
        oof_rows.append(
            {
                **row,
                "exampleKey": key,
                "trackId": track_id,
                "cellIndex": cell_index,
                "datasetId": dataset_id,
                "role": role,
                "confidenceGroupId": group,
                "durationMilliseconds": cell_duration,
            }
        )
    if len(oof_rows) != example_count or [row["exampleKey"] for row in oof_rows] != sorted(keys):
        raise BeatCellSelectorError("The OOF audit does not preserve the exact canonical example order.")
    if observed_counts != group_counts or observed_durations != group_durations:
        raise BeatCellSelectorError("The OOF group count/duration totals disagree with the group audit.")
    for group, group_weights in observed_weights.items():
        expected = 1.0 / group_counts[group]
        if any(
            not math.isclose(value, expected, rel_tol=0, abs_tol=1e-12) for value in group_weights
        ) or not math.isclose(math.fsum(group_weights), 1.0, rel_tol=0, abs_tol=1e-12):
            raise BeatCellSelectorError("OOF sample weights do not give every confidence group unit mass.")
    if sum(row["durationMilliseconds"] for row in oof_rows) != duration:
        raise BeatCellSelectorError("The OOF duration total disagrees with training provenance.")
    if sum(1 for row in oof_rows if row["correct"]) != correct_count:
        raise BeatCellSelectorError("The OOF correctness total disagrees with training provenance.")
    if canonical_sha256(oof_rows) != training["oofPredictionSetSha256"]:
        raise BeatCellSelectorError("The selector oofPredictionSetSha256 is stale.")
    return oof_rows, probabilities, labels, weights


def validate_beat_cell_selector_artifact(
    selector: Mapping[str, Any],
    examples: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate without refitting; optionally crosscheck exact source bindings.

    A self-hash detects accidental mutation but is not an authenticity proof.
    Coefficient/refit semantic identity is deliberately certified by the one
    preregistered readiness reproduction, because refitting here would spend
    an unregistered additional fit.
    """

    _core_contract()
    artifact = _mapping(selector, "selector")
    _exact_fields(artifact, _ARTIFACT_FIELDS, "selector")
    if (
        artifact.get("schemaVersion") != BEAT_CELL_SELECTOR_SCHEMA
        or artifact.get("developmentOnly") is not True
        or artifact.get("promotionEligible") is not False
        or artifact.get("playerUseAuthorized") is not False
        or artifact.get("calibrationAccess") != "closed"
        or artifact.get("testAccess") != "closed"
        or artifact.get("operatingThreshold") is not None
        or artifact.get("authorityCanonicalSha256") != BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256
        or artifact.get("featureRowSchemaVersion") != BEAT_CELL_FEATURE_ROW_SCHEMA
        or tuple(_sequence(artifact.get("featureNames"), "selector.featureNames")) != BEAT_CELL_FEATURE_NAMES
        or artifact.get("featureMathProjectionSha256") != BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256
        or artifact.get("stageBProjectionSha256") != BEAT_CELL_STAGE_B_PROJECTION_SHA256
        or artifact.get("selectorCoreProjectionSha256") != BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256
        or artifact.get("selectorCoreSourceModuleSha256") != BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256
    ):
        raise BeatCellSelectorError("The selector envelope or frozen authority bindings changed.")
    artifact_sha256 = _sha256(artifact.get("artifactSha256"), "selector.artifactSha256")
    if canonical_sha256(_unsigned(artifact, "artifactSha256")) != artifact_sha256:
        raise BeatCellSelectorError("selector.artifactSha256 is stale.")
    training = _mapping(artifact.get("training"), "selector.training")
    oof_rows, probabilities, labels, weights = _validate_training_and_oof(training)

    evaluation = _mapping(artifact.get("outOfFoldEvaluation"), "selector.outOfFoldEvaluation")
    _exact_fields(evaluation, _EVALUATION_FIELDS, "selector.outOfFoldEvaluation")
    if (
        evaluation.get("estimand") != BEAT_CELL_SELECTOR_ESTIMAND
        or evaluation.get("denominator") != BEAT_CELL_SELECTOR_OOF_DENOMINATOR
        or evaluation.get("precisionCoveragePolicy") != _PRECISION_COVERAGE_POLICY
        or evaluation.get("denominatorExampleCount") != training["exampleCount"]
        or evaluation.get("denominatorDurationMilliseconds") != training["exampleDurationMilliseconds"]
    ):
        raise BeatCellSelectorError("The OOF evaluation denominator or disclosure changed.")
    for field in ("groupBalancedLogLoss", "groupBalancedBrierScore", "groupBalancedAreaUnderRiskCoverage"):
        if _finite(evaluation.get(field), f"selector.outOfFoldEvaluation.{field}") < 0.0:
            raise BeatCellSelectorError("An OOF metric is negative.")
    points = _sequence(evaluation.get("precisionCoverage"), "selector.outOfFoldEvaluation.precisionCoverage")
    if len(points) != len(_bar.PRECISION_COVERAGE_TARGETS):
        raise BeatCellSelectorError("The OOF precision/coverage report changed length.")
    for target, raw in zip(_bar.PRECISION_COVERAGE_TARGETS, points, strict=True):
        point = _mapping(raw, "precisionCoverage point")
        _exact_fields(point, _PRECISION_COVERAGE_FIELDS, "precisionCoverage point")
        if not math.isclose(_finite(point.get("targetCoverage"), "targetCoverage"), target, rel_tol=0, abs_tol=1e-12):
            raise BeatCellSelectorError("A precision/coverage target changed.")
        coverage = _finite(point.get("realizableCoverage"), "realizableCoverage")
        precision = _finite(point.get("groupBalancedPrecision"), "groupBalancedPrecision")
        risk = _finite(point.get("groupBalancedRisk"), "groupBalancedRisk")
        cutoff = _finite(point.get("minimumProbabilityAtDescriptivePoint"), "minimumProbabilityAtDescriptivePoint")
        if (
            not 0.0 <= coverage <= 1.0
            or coverage + 1e-12 < target
            or not 0.0 <= precision <= 1.0
            or not 0.0 <= risk <= 1.0
            or not math.isclose(precision + risk, 1.0, rel_tol=0, abs_tol=1e-12)
            or not 0.0 <= cutoff <= 1.0
        ):
            raise BeatCellSelectorError("A precision/coverage point is internally inconsistent.")
    np = _numpy()
    recomputed = _evaluation(
        np.asarray(probabilities, dtype=np.float64),
        np.asarray(labels, dtype=np.float64),
        np.asarray(weights, dtype=np.float64),
        [str(row["exampleKey"]) for row in oof_rows],
        int(training["exampleDurationMilliseconds"]),
        np,
    )
    if canonical_sha256(recomputed) != canonical_sha256(evaluation):
        raise BeatCellSelectorError("The OOF metrics do not recompute from the sealed audit rows.")

    estimator = _mapping(artifact.get("estimator"), "selector.estimator")
    _exact_fields(estimator, _ESTIMATOR_FIELDS, "selector.estimator")
    if (
        estimator.get("kind") != "standardized-elastic-net-logistic-regression"
        or estimator.get("linkFunction") != _bar.LINK_FUNCTION
        or estimator.get("imputation") != "group-weighted-training-median"
    ):
        raise BeatCellSelectorError("The estimator kind, link, or imputation contract changed.")
    arrays: dict[str, list[float]] = {}
    for field in ("imputationValues", "center", "scale", "coefficients"):
        raw = _sequence(estimator.get(field), f"selector.estimator.{field}")
        if len(raw) != len(BEAT_CELL_FEATURE_NAMES):
            raise BeatCellSelectorError(f"selector.estimator.{field} has the wrong dimension.")
        arrays[field] = [_finite(item, f"selector.estimator.{field}") for item in raw]
    if any(value <= 0.0 for value in arrays["scale"]):
        raise BeatCellSelectorError("Estimator scales must be positive.")
    intercept = _finite(estimator.get("intercept"), "selector.estimator.intercept")
    hyperparameters = dict(_mapping(estimator.get("hyperparameters"), "selector.estimator.hyperparameters"))
    if hyperparameters not in _bar.ELASTIC_NET_GRID:
        raise BeatCellSelectorError("Estimator hyperparameters are outside the sole frozen grid.")
    missing = list(_sequence(estimator.get("allMissingFeatureNames"), "selector.estimator.allMissingFeatureNames"))
    if missing != [name for name in BEAT_CELL_FEATURE_NAMES if name in set(missing)] or len(missing) != len(
        set(missing)
    ):
        raise BeatCellSelectorError("Estimator allMissingFeatureNames is not a canonical feature subset.")
    optimizer = _mapping(estimator.get("optimizer"), "selector.estimator.optimizer")
    _exact_fields(optimizer, _OPTIMIZER_FIELDS, "selector.estimator.optimizer")
    iterations = _integer(optimizer.get("iterations"), "selector.estimator.optimizer.iterations", minimum=1)
    if (
        optimizer.get("kind") != _bar.OPTIMIZER_KIND
        or optimizer.get("convergence") != _bar.OPTIMIZER_CONVERGENCE
        or optimizer.get("converged") is not True
        or optimizer.get("maximumIterations") != _bar.OPTIMIZER_MAX_ITERATIONS
        or optimizer.get("tolerance") != _bar.OPTIMIZER_TOLERANCE
        or iterations > _bar.OPTIMIZER_MAX_ITERATIONS
    ):
        raise BeatCellSelectorError("The estimator optimizer contract or convergence audit changed.")

    if examples is not None:
        source, source_rows = _validated_examples(examples)
        expected_input_sha256 = canonical_sha256(
            {
                "sourceExamplesArtifactSha256": source["artifactSha256"],
                "sourceExampleSetSha256": source["exampleSetSha256"],
                "rows": _input_payload(source_rows),
            }
        )
        feature_sets = {str(row["featureSetArtifactSha256"]) for row in source_rows}
        expected_oof_metadata = [
            {
                "exampleKey": row["exampleKey"],
                "trackId": row["trackId"],
                "cellIndex": row["cellIndex"],
                "datasetId": row["datasetId"],
                "role": row["role"],
                "guitarsetRole": row["guitarsetRole"],
                "confidenceGroupId": row["confidenceGroupId"],
                "durationMilliseconds": row["durationMilliseconds"],
                "correct": row["correct"],
            }
            for row in source_rows
        ]
        actual_oof_metadata = [
            {name: row[name] for name in expected_oof_metadata[index]} for index, row in enumerate(oof_rows)
        ]
        expected_bindings = {
            "sourceExamplesArtifactSha256": source["artifactSha256"],
            "sourceExampleSetSha256": source["exampleSetSha256"],
            "sourceFeatureSetArtifactSha256": next(iter(feature_sets)) if len(feature_sets) == 1 else None,
            "sourceFeatureRowSetSha256": _set_sha256(source_rows, "featureRowSha256"),
            "sourceFeatureSummaryArtifactSetSha256": _set_sha256(source_rows, "featureSummaryArtifactSha256"),
            "sourceStage1ArtifactSetSha256": _set_sha256(source_rows, "stage1ArtifactSha256"),
            "sourcePredictionIdentitySetSha256": _set_sha256(source_rows, "predictionIdentitySha256"),
            "sourceAudioLineageRowSetSha256": _set_sha256(source_rows, "audioLineageRowSha256"),
        }
        if (
            len(feature_sets) != 1
            or training.get("inputSetSha256") != expected_input_sha256
            or any(training.get(name) != expected for name, expected in expected_bindings.items())
            or training.get("sourceLabelAudits") != source.get("labelAudits")
            or training.get("exampleCount") != len(source_rows)
            or training.get("exampleDurationMilliseconds")
            != sum(int(row["durationMilliseconds"]) for row in source_rows)
            or actual_oof_metadata != expected_oof_metadata
        ):
            raise BeatCellSelectorError("The selector does not exactly bind the supplied source examples.")
    return {
        "artifactSha256": artifact_sha256,
        "imputation": arrays["imputationValues"],
        "center": arrays["center"],
        "scale": arrays["scale"],
        "coefficients": arrays["coefficients"],
        "intercept": intercept,
    }


def _application_result(
    *,
    probability: float | None,
    reason: str | None,
    selector_sha256: str | None,
    row_sha256: str | None,
    track_id: str | None,
    cell_index: int | None,
) -> dict[str, Any]:
    return {
        "schemaVersion": BEAT_CELL_SELECTOR_APPLICATION_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "playerUseAuthorized": False,
        "calibrationAccess": "closed",
        "testAccess": "closed",
        "operatingThreshold": None,
        "probability": probability,
        "reason": reason,
        "selectorArtifactSha256": selector_sha256,
        "featureRowSha256": row_sha256,
        "trackId": track_id,
        "cellIndex": cell_index,
    }


def apply_beat_cell_selector(feature_row: Mapping[str, Any], selector: Mapping[str, Any]) -> dict[str, Any]:
    """Return one split-neutral probability or a stable fail-closed reason."""

    try:
        estimator = validate_beat_cell_selector_artifact(selector)
    except (TypeError, ValueError, OverflowError, OSError):
        return _application_result(
            probability=None,
            reason="invalid-selector-artifact",
            selector_sha256=None,
            row_sha256=None,
            track_id=None,
            cell_index=None,
        )
    try:
        row = validate_beat_cell_feature_row(feature_row)
        track_id = _string(row.get("trackId"), "featureRow.trackId")
        cell_index = _integer(row.get("cellIndex"), "featureRow.cellIndex")
        row_sha256 = _sha256(row.get("rowSha256"), "featureRow.rowSha256")
        vector = _validated_feature_values(row.get("featureValues"), "featureRow.featureValues")
    except (TypeError, ValueError, OverflowError, OSError):
        return _application_result(
            probability=None,
            reason="invalid-feature-row",
            selector_sha256=estimator["artifactSha256"],
            row_sha256=None,
            track_id=None,
            cell_index=None,
        )
    if row.get("predictionProduct") is None:
        reason = "prediction-product-missing"
    elif _finite(row.get("predictionCoverage"), "featureRow.predictionCoverage") < 0.75:
        reason = "prediction-coverage-below-eligibility-threshold"
    elif _finite(row.get("predictionDominance"), "featureRow.predictionDominance") < 0.75:
        reason = "prediction-dominance-below-eligibility-threshold"
    else:
        reason = None
    if reason is not None:
        return _application_result(
            probability=None,
            reason=reason,
            selector_sha256=estimator["artifactSha256"],
            row_sha256=row_sha256,
            track_id=track_id,
            cell_index=cell_index,
        )
    try:
        numeric = [estimator["imputation"][index] if item is None else float(item) for index, item in enumerate(vector)]
        logit = estimator["intercept"] + math.fsum(
            (value - estimator["center"][index]) / estimator["scale"][index] * estimator["coefficients"][index]
            for index, value in enumerate(numeric)
        )
        probability = _bar._scalar_sigmoid(logit)
    except (ArithmeticError, TypeError, ValueError, OverflowError):
        return _application_result(
            probability=None,
            reason="invalid-feature-vector",
            selector_sha256=estimator["artifactSha256"],
            row_sha256=row_sha256,
            track_id=track_id,
            cell_index=cell_index,
        )
    return _application_result(
        probability=probability,
        reason=None,
        selector_sha256=estimator["artifactSha256"],
        row_sha256=row_sha256,
        track_id=track_id,
        cell_index=cell_index,
    )


__all__ = [
    "BEAT_CELL_FEATURE_NAMES",
    "BEAT_CELL_SELECTOR_APPLICATION_SCHEMA",
    "BEAT_CELL_SELECTOR_CONFIG_SHA256",
    "BEAT_CELL_SELECTOR_OOF_DENOMINATOR",
    "BEAT_CELL_SELECTOR_SCHEMA",
    "BEAT_CELL_SELECTOR_ESTIMAND",
    "BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256",
    "BeatCellSelectorError",
    "apply_beat_cell_selector",
    "train_beat_cell_selector",
    "validate_beat_cell_selector_artifact",
]
