"""Development-only grouped selector for prediction-only chord-bar evidence.

This module intentionally performs no file I/O. Callers provide one sealed
``chord_bar_selector_examples_v1`` artifact containing compact, hash-bound bar
summaries and boolean development outcomes. Outcome, identity, grouping,
corpus, and role fields are never admitted to the estimator feature matrix.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import math
from typing import Any

from .bar_promotion import canonical_sha256
from .bar_uncertainty import (
    BAR_FEATURE_CONTRACT_SHA256,
    BAR_FEATURE_NAMES,
)


BAR_SELECTOR_EXAMPLES_SCHEMA = "chord_bar_selector_examples_v1"
BAR_SELECTOR_BAR_SUMMARY_SCHEMA = "chord_bar_selector_bar_summary_v1"
BAR_SELECTOR_ARTIFACT_SCHEMA = "chord_bar_correctness_selector_v1"
BAR_SELECTOR_APPLICATION_SCHEMA = "chord_bar_correctness_probability_v1"
FACTORIZED_UNCERTAINTY_SCHEMA = "chord_factorized_uncertainty_v1"
EXPLICIT_BAR_GRID_SCHEMA = "chord_explicit_bar_grid_v1"
BAR_SCORE_SCHEMA = "chord_bar_product_confidence_v1"
BAR_OUTCOME_ELIGIBILITY_CONTRACT = {
    "schemaVersion": "chord_bar_selector_outcome_eligibility_contract_v1",
    "scoreSchemaVersion": BAR_SCORE_SCHEMA,
    "referenceDominance": 0.75,
    "predictionCoverage": 0.75,
    "predictionDominance": 0.75,
    "confidenceThresholds": [0.0],
    "barEndDurationRule": ("full-precision-prediction-after-exact-player-canonical-millisecond-runtime-join"),
    "inclusionRule": "scoreBar.eligible=true and scoreBar.correct is boolean",
}
BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256 = canonical_sha256(BAR_OUTCOME_ELIGIBILITY_CONTRACT)

OUTER_FOLD_COUNT = 5
INNER_FOLD_COUNT = 4
OPTIMIZER_MAX_ITERATIONS = 3000
OPTIMIZER_TOLERANCE = 1e-6
STANDARD_SCALE_FLOOR = 1e-8
PROBABILITY_FLOOR = 1e-12

ELASTIC_NET_GRID = (
    {"alpha": 0.01, "l1Ratio": 0.25},
    {"alpha": 0.01, "l1Ratio": 0.5},
    {"alpha": 0.05, "l1Ratio": 0.25},
    {"alpha": 0.05, "l1Ratio": 0.5},
    {"alpha": 0.05, "l1Ratio": 0.75},
)
PRECISION_COVERAGE_TARGETS = (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0)

_SHA256_HEX = frozenset("0123456789abcdef")
_FAMILY_FEATURES = frozenset(
    {
        "productFamilyNone",
        "productFamilyMajor",
        "productFamilyMinor",
        "productFamilyDominant",
        "productFamilyMinorSeventh",
    }
)
_REQUIRED_NUMERIC_FEATURES = frozenset(
    {
        "predictionCoverage",
        "predictionDominance",
        "predictionTransitionCount",
        *_FAMILY_FEATURES,
        "boundaryModelProbabilityMean",
        "boundaryModelProbabilityMaximum",
        "representationRmsMean",
        "representationRmsMaximum",
        "temporalDeltaRmsMean",
        "temporalDeltaRmsMaximum",
        "absoluteActivationConcentrationMean",
        "absoluteActivationConcentrationMaximum",
        "cosineChangeMean",
        "cosineChangeMaximum",
    }
)
_EXAMPLES_ARTIFACT_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "sharedBindings",
        "sharedBindingsSha256",
        "sourceBenchmarkReportSha256",
        "sourceRuntimeBarGridManifestSha256",
        "sourceGroupManifestSha256",
        "examples",
        "exampleSetSha256",
        "artifactSha256",
    }
)
_EXAMPLE_FIELDS = frozenset(
    {
        "split",
        "trackId",
        "confidenceGroupId",
        "barIndex",
        "barSummary",
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "outcome",
        "exampleSha256",
    }
)
_MODEL_BINDING_FIELDS = frozenset(
    {
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
    }
)
_COMPACT_BAR_SUMMARY_FIELDS = frozenset(
    {
        "schemaVersion",
        "trackId",
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
        "sharedBindingsSha256",
        "barFeatureContractSha256",
        "index",
        "start",
        "end",
        "predictionProduct",
        "predictionProductDurationSeconds",
        "predictionCoverage",
        "predictionDominance",
        "predictionTransitionCount",
        "featureValues",
        "barSummarySha256",
    }
)
_STATIC_BINDING_FIELDS = frozenset(
    {
        "barSummarySchemaVersion",
        "featureNames",
        "barFeatureContractSha256",
        "uncertaintySchemaVersion",
        "uncertaintyContractSha256",
        "modelOrEnsembleSha256",
        "decoderContractSha256",
        "memberOrderSha256",
        "sourceFeatureKind",
        "sourceFeatureSpecSha256",
        "observabilityProfileSchemaVersion",
        "timingSchemaVersion",
        "timingSourceClass",
        "timingSourceId",
        "timingSourceContractSha256",
        "barOutcomeEligibilityContract",
        "barOutcomeEligibilityContractSha256",
    }
)

_SELECTOR_CONFIG = {
    "schemaVersion": BAR_SELECTOR_ARTIFACT_SCHEMA,
    "featureNames": list(BAR_FEATURE_NAMES),
    "barFeatureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
    "barOutcomeEligibilityContract": dict(BAR_OUTCOME_ELIGIBILITY_CONTRACT),
    "barOutcomeEligibilityContractSha256": BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    "developmentSplit": "development",
    "target": "correct:boolean",
    "groupField": "confidenceGroupId",
    "groupFallback": None,
    "outerFoldCount": OUTER_FOLD_COUNT,
    "innerFoldCount": INNER_FOLD_COUNT,
    "foldAssignment": "sha256-salted-group-order-round-robin-v1",
    "preprocessing": {
        "missing": "training-fold-group-weighted-median; zero when entirely missing",
        "center": "training-fold-group-weighted-mean-after-imputation",
        "scale": "training-fold-group-weighted-population-standard-deviation; one below floor",
        "scaleFloor": STANDARD_SCALE_FLOOR,
    },
    "estimator": {
        "kind": "elastic-net-logistic-regression",
        "penalty": "alpha*((1-l1Ratio)/2*L2Squared+l1Ratio*L1)",
        "grid": [dict(value) for value in ELASTIC_NET_GRID],
        "optimizer": "deterministic-proximal-gradient-v1",
        "maxIterations": OPTIMIZER_MAX_ITERATIONS,
        "tolerance": OPTIMIZER_TOLERANCE,
    },
    "sampleWeight": "each confidenceGroupId has total sample weight exactly one in every partition",
    "hyperparameterSelection": "minimum inner grouped weighted log loss; frozen grid order breaks ties",
    "operatingThresholdSelection": None,
    "precisionCoverageTargets": list(PRECISION_COVERAGE_TARGETS),
}
BAR_SELECTOR_CONFIG_SHA256 = canonical_sha256(_SELECTOR_CONFIG)


class BarSelectorError(ValueError):
    """A selector example, artifact, or application failed closed."""


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - required project dependency
        raise RuntimeError("Bar selector training requires NumPy.") from exc
    return np


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BarSelectorError(f"{name} must be an object.")
    return value


def _exact_fields(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise BarSelectorError(f"{name} fields do not match the frozen schema: missing={missing}, extra={extra}.")


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise BarSelectorError(f"{name} must be a sequence.")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BarSelectorError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise BarSelectorError(f"{name} must be a finite number.")
    return number


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BarSelectorError(f"{name} must be an integer greater than or equal to {minimum}.")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - _SHA256_HEX:
        raise BarSelectorError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise BarSelectorError(f"{name} must be a nonempty string without surrounding whitespace.")
    return value


def _unsigned(value: Mapping[str, Any], hash_field: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result.pop(hash_field, None)
    return result


def _validated_feature_values(value: Any, name: str) -> list[float | None]:
    features = _mapping(value, name)
    if tuple(features) != BAR_FEATURE_NAMES:
        raise BarSelectorError(
            f"{name} must contain exactly BAR_FEATURE_NAMES in the frozen order; identity/outcome fields are forbidden."
        )
    output: list[float | None] = []
    for feature_name in BAR_FEATURE_NAMES:
        raw = features[feature_name]
        if raw is None:
            if feature_name in _REQUIRED_NUMERIC_FEATURES:
                raise BarSelectorError(f"{name}.{feature_name} may not be null.")
            output.append(None)
            continue
        number = _finite(raw, f"{name}.{feature_name}")
        if feature_name == "predictionTransitionCount":
            _integer(raw, f"{name}.{feature_name}")
        elif feature_name in _FAMILY_FEATURES:
            if number not in {0.0, 1.0}:
                raise BarSelectorError(f"{name}.{feature_name} must be zero or one.")
        elif feature_name.startswith(("representationRms", "temporalDeltaRms")):
            if number < 0:
                raise BarSelectorError(f"{name}.{feature_name} must be non-negative.")
        elif feature_name.startswith("cosineChange"):
            if not 0 <= number <= 2:
                raise BarSelectorError(f"{name}.{feature_name} must lie in [0, 2].")
        elif not 0 <= number <= 1:
            raise BarSelectorError(f"{name}.{feature_name} must lie in [0, 1].")
        output.append(number)
    family_values = [features[feature_name] for feature_name in _FAMILY_FEATURES]
    if sum(float(value) for value in family_values) not in {0.0, 1.0}:
        raise BarSelectorError(f"{name} product-family indicators must be all zero or exactly one-hot.")
    return output


def _validated_shared_bindings(value: Any, name: str = "sharedBindings") -> dict[str, Any]:
    binding = _mapping(value, name)
    _exact_fields(binding, _STATIC_BINDING_FIELDS, name)
    output: dict[str, Any] = {}
    feature_names = _sequence(binding.get("featureNames"), f"{name}.featureNames")
    if tuple(feature_names) != BAR_FEATURE_NAMES:
        raise BarSelectorError(f"{name}.featureNames must equal BAR_FEATURE_NAMES in frozen order.")
    output["featureNames"] = list(BAR_FEATURE_NAMES)
    outcome_contract = _mapping(
        binding.get("barOutcomeEligibilityContract"),
        f"{name}.barOutcomeEligibilityContract",
    )
    if dict(outcome_contract) != BAR_OUTCOME_ELIGIBILITY_CONTRACT:
        raise BarSelectorError(f"{name} changed the frozen bar outcome/eligibility contract.")
    output["barOutcomeEligibilityContract"] = dict(BAR_OUTCOME_ELIGIBILITY_CONTRACT)
    for field in _STATIC_BINDING_FIELDS - {
        "featureNames",
        "barOutcomeEligibilityContract",
    }:
        if field.endswith("Sha256"):
            output[field] = _sha256(binding.get(field), f"{name}.{field}")
        else:
            output[field] = _nonempty_string(binding.get(field), f"{name}.{field}")
    if (
        output["barSummarySchemaVersion"] != BAR_SELECTOR_BAR_SUMMARY_SCHEMA
        or output["barFeatureContractSha256"] != BAR_FEATURE_CONTRACT_SHA256
        or output["uncertaintySchemaVersion"] != FACTORIZED_UNCERTAINTY_SCHEMA
        or output["timingSchemaVersion"] != EXPLICIT_BAR_GRID_SCHEMA
        or output["timingSourceClass"] != "runtime"
        or output["barOutcomeEligibilityContractSha256"] != BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256
    ):
        raise BarSelectorError(f"{name} does not match the frozen prediction-only schemas.")
    return output


def _validated_compact_bar_summary(value: Any) -> dict[str, Any]:
    summary = _mapping(value, "barSummary")
    _exact_fields(summary, _COMPACT_BAR_SUMMARY_FIELDS, "barSummary")
    if summary.get("schemaVersion") != BAR_SELECTOR_BAR_SUMMARY_SCHEMA:
        raise BarSelectorError("barSummary uses an unsupported schemaVersion.")
    summary_sha256 = _sha256(summary.get("barSummarySha256"), "barSummary.barSummarySha256")
    if canonical_sha256(_unsigned(summary, "barSummarySha256")) != summary_sha256:
        raise BarSelectorError("barSummary.barSummarySha256 does not match its canonical payload.")
    track_id = _nonempty_string(summary.get("trackId"), "barSummary.trackId")
    for name in (
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
        "sharedBindingsSha256",
    ):
        _sha256(summary.get(name), f"barSummary.{name}")
    if summary.get("barFeatureContractSha256") != BAR_FEATURE_CONTRACT_SHA256:
        raise BarSelectorError("barSummary does not use the frozen BAR_FEATURE_NAMES contract.")
    index = _integer(summary.get("index"), "barSummary.index")
    start = _finite(summary.get("start"), "barSummary.start")
    end = _finite(summary.get("end"), "barSummary.end")
    if start < 0 or end <= start:
        raise BarSelectorError("barSummary interval is invalid.")
    prediction_product = summary.get("predictionProduct")
    if prediction_product is not None:
        _nonempty_string(prediction_product, "barSummary.predictionProduct")
    predicted_duration = _finite(
        summary.get("predictionProductDurationSeconds"),
        "barSummary.predictionProductDurationSeconds",
    )
    coverage = _finite(summary.get("predictionCoverage"), "barSummary.predictionCoverage")
    dominance = _finite(summary.get("predictionDominance"), "barSummary.predictionDominance")
    transitions = _integer(summary.get("predictionTransitionCount"), "barSummary.predictionTransitionCount")
    if predicted_duration < 0 or predicted_duration > end - start + 1e-9:
        raise BarSelectorError("barSummary predicted-product duration is outside its interval.")
    if not 0 <= coverage <= 1 or not 0 <= dominance <= 1:
        raise BarSelectorError("barSummary coverage and dominance must lie in [0, 1].")
    vector = _validated_feature_values(summary.get("featureValues"), "barSummary.featureValues")
    feature_by_name = dict(zip(BAR_FEATURE_NAMES, vector, strict=True))
    if (
        feature_by_name["predictionCoverage"] != coverage
        or feature_by_name["predictionDominance"] != dominance
        or feature_by_name["predictionTransitionCount"] != float(transitions)
    ):
        raise BarSelectorError("barSummary duplicated prediction features disagree with featureValues.")
    return {
        "raw": summary,
        "barSummarySha256": summary_sha256,
        "trackId": track_id,
        "index": index,
        "features": vector,
        "sourceSummarySha256": str(summary["sourceSummarySha256"]),
        "predictionCoreSha256": str(summary["predictionCoreSha256"]),
        "uncertaintySha256": str(summary["uncertaintySha256"]),
        "timingSha256": str(summary["timingSha256"]),
        "sharedBindingsSha256": str(summary["sharedBindingsSha256"]),
    }


def _validated_example(value: Any, shared_bindings: Mapping[str, Any]) -> dict[str, Any]:
    example = _mapping(value, "example")
    _exact_fields(example, _EXAMPLE_FIELDS, "example")
    if example.get("split") != "development":
        raise BarSelectorError("Bar selector examples are development-only; sealed splits are forbidden.")
    claimed_sha256 = _sha256(example.get("exampleSha256"), "example.exampleSha256")
    if canonical_sha256(_unsigned(example, "exampleSha256")) != claimed_sha256:
        raise BarSelectorError("example.exampleSha256 does not match its canonical payload.")
    track_id = _nonempty_string(example.get("trackId"), "example.trackId")
    group = _nonempty_string(example.get("confidenceGroupId"), "example.confidenceGroupId")
    bar_index = _integer(example.get("barIndex"), "example.barIndex")
    outcome = _mapping(example.get("outcome"), "example.outcome")
    if set(outcome) != {"correct"}:
        raise BarSelectorError("example.outcome must expose exactly boolean correct.")
    correct = outcome.get("correct")
    if not isinstance(correct, bool):
        raise BarSelectorError("example.outcome.correct must be boolean.")
    for name in _MODEL_BINDING_FIELDS:
        digest = _sha256(example.get(name), f"example.{name}")
        if digest != shared_bindings[name]:
            raise BarSelectorError(f"example.{name} does not match sharedBindings.")
    summary = _validated_compact_bar_summary(example.get("barSummary"))
    if track_id != summary["trackId"]:
        raise BarSelectorError("example.trackId does not match barSummary.trackId.")
    if bar_index != summary["index"]:
        raise BarSelectorError("example.barIndex does not match barSummary.index.")
    if summary["sharedBindingsSha256"] != canonical_sha256(shared_bindings):
        raise BarSelectorError("barSummary.sharedBindingsSha256 does not match examplesArtifact.sharedBindings.")
    example_key = canonical_sha256(
        {
            "trackId": track_id,
            "barIndex": bar_index,
            "barSummarySha256": summary["barSummarySha256"],
            "sourceSummarySha256": summary["sourceSummarySha256"],
            "predictionCoreSha256": summary["predictionCoreSha256"],
            "uncertaintySha256": summary["uncertaintySha256"],
            "timingSha256": summary["timingSha256"],
            "modelOrEnsembleSha256": example["modelOrEnsembleSha256"],
            "decoderContractSha256": example["decoderContractSha256"],
            "memberOrderSha256": example["memberOrderSha256"],
        }
    )
    return {
        "raw": example,
        "exampleSha256": claimed_sha256,
        "exampleKey": example_key,
        "trackId": track_id,
        "group": group,
        "barIndex": bar_index,
        "correct": correct,
        "features": summary["features"],
        "barSummarySha256": summary["barSummarySha256"],
        "sourceSummarySha256": summary["sourceSummarySha256"],
        "predictionCoreSha256": summary["predictionCoreSha256"],
        "uncertaintySha256": summary["uncertaintySha256"],
        "timingSha256": summary["timingSha256"],
    }


def _split_preflight(artifact: Mapping[str, Any], values: Sequence[Any]) -> None:
    """Reject every non-development input before validating any nested object."""

    if artifact.get("split") != "development":
        raise BarSelectorError("Bar selector input is development-only; sealed top-level split is forbidden.")
    for index, raw in enumerate(values):
        if not isinstance(raw, Mapping) or raw.get("split") != "development":
            raise BarSelectorError(
                f"example[{index}] is not development split; calibration, test, heldout, and confirmation are sealed."
            )


def _folds(groups: Sequence[str], count: int, salt: str) -> dict[str, int]:
    unique = sorted(
        set(groups),
        key=lambda group: (hashlib.sha256(f"{salt}\0{group}".encode()).hexdigest(), group),
    )
    if len(unique) < count:
        raise BarSelectorError(f"Grouped {count}-fold validation requires at least {count} confidence groups.")
    return {group: index % count for index, group in enumerate(unique)}


def _group_weights(groups: Sequence[str], np: Any) -> Any:
    counts: dict[str, int] = {}
    for group in groups:
        counts[group] = counts.get(group, 0) + 1
    weights = np.asarray([1.0 / counts[group] for group in groups], dtype=np.float64)
    for group in counts:
        mass = math.fsum(float(weights[index]) for index, value in enumerate(groups) if value == group)
        if not math.isclose(mass, 1.0, rel_tol=0, abs_tol=1e-12):
            raise RuntimeError("Internal group weighting failed its exact unit-mass contract.")
    return weights


def _weighted_median(values: Any, weights: Any, np: Any) -> float:
    order = np.argsort(values, kind="mergesort")
    ordered_values = values[order]
    ordered_weights = weights[order]
    cutoff = float(ordered_weights.sum()) / 2.0
    position = int(np.searchsorted(np.cumsum(ordered_weights), cutoff, side="left"))
    return float(ordered_values[min(position, len(ordered_values) - 1)])


def _fit_preprocessor(matrix: Any, weights: Any, np: Any) -> tuple[Any, Any, Any, Any]:
    imputation = np.zeros(matrix.shape[1], dtype=np.float64)
    all_missing = np.zeros(matrix.shape[1], dtype=np.bool_)
    for column in range(matrix.shape[1]):
        present = np.isfinite(matrix[:, column])
        if not bool(present.any()):
            all_missing[column] = True
            imputation[column] = 0.0
        else:
            imputation[column] = _weighted_median(matrix[present, column], weights[present], np)
    imputed = np.where(np.isfinite(matrix), matrix, imputation)
    normalizer = float(weights.sum())
    center = (imputed * weights[:, None]).sum(axis=0) / normalizer
    variance = (((imputed - center) ** 2) * weights[:, None]).sum(axis=0) / normalizer
    scale = np.sqrt(np.maximum(0.0, variance))
    scale = np.where(scale < STANDARD_SCALE_FLOOR, 1.0, scale)
    return imputation, center, scale, all_missing


def _transform(matrix: Any, imputation: Any, center: Any, scale: Any, np: Any) -> Any:
    imputed = np.where(np.isfinite(matrix), matrix, imputation)
    return (imputed - center) / scale


def _sigmoid(logits: Any, np: Any) -> Any:
    clipped = np.clip(logits, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _fit_elastic_net(
    matrix: Any,
    labels: Any,
    weights: Any,
    hyperparameters: Mapping[str, float],
    np: Any,
) -> tuple[Any, float, int, bool]:
    positive_mass = float((weights * labels).sum())
    negative_mass = float((weights * (1.0 - labels)).sum())
    if positive_mass <= 0 or negative_mass <= 0:
        raise BarSelectorError("Every selector training partition must contain both correct and incorrect bars.")
    alpha = float(hyperparameters["alpha"])
    l1_ratio = float(hyperparameters["l1Ratio"])
    l1_penalty = alpha * l1_ratio
    l2_penalty = alpha * (1.0 - l1_ratio)
    coefficients = np.zeros(matrix.shape[1], dtype=np.float64)
    intercept = math.log(positive_mass / negative_mass)
    normalizer = float(weights.sum())
    row_norm_bound = float((weights * (((matrix * matrix).sum(axis=1)) + 1.0)).sum() / normalizer)
    step = 1.0 / max(1e-12, 0.25 * row_norm_bound + l2_penalty)
    converged = False
    iteration = 0
    for iteration in range(1, OPTIMIZER_MAX_ITERATIONS + 1):
        probability = _sigmoid(matrix @ coefficients + intercept, np)
        residual = weights * (probability - labels) / normalizer
        coefficient_gradient = matrix.T @ residual + l2_penalty * coefficients
        intercept_gradient = float(residual.sum())
        proposal = coefficients - step * coefficient_gradient
        next_coefficients = np.sign(proposal) * np.maximum(np.abs(proposal) - step * l1_penalty, 0.0)
        next_intercept = intercept - step * intercept_gradient
        maximum_change = max(
            float(np.max(np.abs(next_coefficients - coefficients), initial=0.0)),
            abs(next_intercept - intercept),
        )
        coefficients = next_coefficients
        intercept = next_intercept
        if maximum_change <= OPTIMIZER_TOLERANCE:
            converged = True
            break
    return coefficients, float(intercept), iteration, converged


def _weighted_log_loss(probabilities: Any, labels: Any, weights: Any, np: Any) -> float:
    clipped = np.clip(probabilities, PROBABILITY_FLOOR, 1.0 - PROBABILITY_FLOOR)
    losses = -(labels * np.log(clipped) + (1.0 - labels) * np.log(1.0 - clipped))
    return float((weights * losses).sum() / weights.sum())


def _fit_predict(
    matrix: Any,
    labels: Any,
    groups: Sequence[str],
    train_indices: Any,
    validate_indices: Any,
    hyperparameters: Mapping[str, float],
    np: Any,
) -> tuple[Any, dict[str, Any]]:
    training_groups = [groups[int(index)] for index in train_indices]
    weights = _group_weights(training_groups, np)
    imputation, center, scale, all_missing = _fit_preprocessor(matrix[train_indices], weights, np)
    training_matrix = _transform(matrix[train_indices], imputation, center, scale, np)
    coefficients, intercept, iterations, converged = _fit_elastic_net(
        training_matrix,
        labels[train_indices],
        weights,
        hyperparameters,
        np,
    )
    validation_matrix = _transform(matrix[validate_indices], imputation, center, scale, np)
    probability = _sigmoid(validation_matrix @ coefficients + intercept, np)
    return probability, {
        "imputation": imputation,
        "center": center,
        "scale": scale,
        "allMissing": all_missing,
        "coefficients": coefficients,
        "intercept": intercept,
        "iterations": iterations,
        "converged": converged,
    }


def _select_hyperparameters(
    matrix: Any,
    labels: Any,
    groups: Sequence[str],
    np: Any,
    *,
    salt: str,
) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, int]]:
    assignment = _folds(groups, INNER_FOLD_COUNT, salt)
    fold_values = np.asarray([assignment[group] for group in groups], dtype=np.int64)
    scores: list[dict[str, Any]] = []
    for grid_index, hyperparameters in enumerate(ELASTIC_NET_GRID):
        loss_total = 0.0
        weight_total = 0.0
        for fold in range(INNER_FOLD_COUNT):
            validate_indices = np.flatnonzero(fold_values == fold)
            train_indices = np.flatnonzero(fold_values != fold)
            probabilities, fitted = _fit_predict(
                matrix,
                labels,
                groups,
                train_indices,
                validate_indices,
                hyperparameters,
                np,
            )
            if not fitted["converged"]:
                raise BarSelectorError(
                    f"Elastic-net optimizer did not converge for grid candidate {grid_index}, inner fold {fold}."
                )
            validation_groups = [groups[int(index)] for index in validate_indices]
            validation_weights = _group_weights(validation_groups, np)
            fold_weight = float(validation_weights.sum())
            loss_total += (
                _weighted_log_loss(
                    probabilities,
                    labels[validate_indices],
                    validation_weights,
                    np,
                )
                * fold_weight
            )
            weight_total += fold_weight
        scores.append(
            {
                "gridIndex": grid_index,
                "hyperparameters": dict(hyperparameters),
                "groupBalancedLogLoss": loss_total / weight_total,
            }
        )
    selected = min(scores, key=lambda value: (value["groupBalancedLogLoss"], value["gridIndex"]))
    return dict(selected["hyperparameters"]), scores, assignment


def _probability_blocks(probabilities: Any, labels: Any, weights: Any, keys: Sequence[str]) -> list[dict[str, float]]:
    order = sorted(range(len(keys)), key=lambda index: (-float(probabilities[index]), keys[index]))
    blocks: list[dict[str, float]] = []
    for index in order:
        probability = float(probabilities[index])
        if not blocks or probability != blocks[-1]["probability"]:
            blocks.append({"probability": probability, "weight": 0.0, "correctWeight": 0.0})
        blocks[-1]["weight"] += float(weights[index])
        blocks[-1]["correctWeight"] += float(weights[index] * labels[index])
    return blocks


def _aurc(probabilities: Any, labels: Any, weights: Any, keys: Sequence[str]) -> float:
    total_weight = float(weights.sum())
    cumulative_weight = 0.0
    cumulative_error = 0.0
    area = 0.0
    for block in _probability_blocks(probabilities, labels, weights, keys):
        cumulative_weight += block["weight"]
        cumulative_error += block["weight"] - block["correctWeight"]
        risk = cumulative_error / cumulative_weight
        area += block["weight"] / total_weight * risk
    return area


def _precision_coverage(
    probabilities: Any,
    labels: Any,
    weights: Any,
    keys: Sequence[str],
) -> list[dict[str, Any]]:
    blocks = _probability_blocks(probabilities, labels, weights, keys)
    total = float(weights.sum())
    output: list[dict[str, Any]] = []
    for target in PRECISION_COVERAGE_TARGETS:
        cumulative = 0.0
        correct = 0.0
        minimum_probability: float | None = None
        for block in blocks:
            cumulative += block["weight"]
            correct += block["correctWeight"]
            minimum_probability = block["probability"]
            if cumulative / total + 1e-15 >= target:
                break
        output.append(
            {
                "targetCoverage": target,
                "realizableCoverage": cumulative / total,
                "groupBalancedPrecision": correct / cumulative,
                "groupBalancedRisk": 1.0 - correct / cumulative,
                "minimumProbabilityAtDescriptivePoint": minimum_probability,
            }
        )
    return output


def _evaluation(probabilities: Any, labels: Any, weights: Any, keys: Sequence[str], np: Any) -> dict[str, Any]:
    brier = float((weights * (probabilities - labels) ** 2).sum() / weights.sum())
    return {
        "groupBalancedLogLoss": _weighted_log_loss(probabilities, labels, weights, np),
        "groupBalancedBrierScore": brier,
        "groupBalancedAreaUnderRiskCoverage": _aurc(probabilities, labels, weights, keys),
        "precisionCoveragePolicy": "fixed descriptive coverage targets; no operating threshold selected",
        "precisionCoverage": _precision_coverage(probabilities, labels, weights, keys),
    }


def train_bar_selector(examples_artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Train from one sealed, development-only compact examples artifact."""

    source = _mapping(examples_artifact, "examplesArtifact")
    if source.get("split") != "development":
        raise BarSelectorError("Bar selector input is development-only; sealed top-level split is forbidden.")
    raw_values = source.get("examples")
    values = list(_sequence(raw_values, "examplesArtifact.examples")) if raw_values is not None else []
    if not values:
        raise BarSelectorError("Bar selector training requires at least one development example.")
    # This is deliberately the first inspection.  The module performs no file
    # access, and sealed split values fail before any nested summary is read.
    _split_preflight(source, values)
    _exact_fields(source, _EXAMPLES_ARTIFACT_FIELDS, "examplesArtifact")
    if source.get("schemaVersion") != BAR_SELECTOR_EXAMPLES_SCHEMA:
        raise BarSelectorError("examplesArtifact uses an unsupported schemaVersion.")
    if source.get("developmentOnly") is not True or source.get("promotionEligible") is not False:
        raise BarSelectorError("examplesArtifact must remain development-only and non-promotable.")
    source_artifact_sha256 = _sha256(source.get("artifactSha256"), "examplesArtifact.artifactSha256")
    if canonical_sha256(_unsigned(source, "artifactSha256")) != source_artifact_sha256:
        raise BarSelectorError("examplesArtifact.artifactSha256 does not match its canonical payload.")
    example_set_sha256 = _sha256(source.get("exampleSetSha256"), "examplesArtifact.exampleSetSha256")
    if canonical_sha256(values) != example_set_sha256:
        raise BarSelectorError("examplesArtifact.exampleSetSha256 does not match examples.")
    for name in (
        "sourceBenchmarkReportSha256",
        "sourceRuntimeBarGridManifestSha256",
        "sourceGroupManifestSha256",
    ):
        _sha256(source.get(name), f"examplesArtifact.{name}")
    static_binding = _validated_shared_bindings(source.get("sharedBindings"), "examplesArtifact.sharedBindings")
    shared_bindings_sha256 = _sha256(
        source.get("sharedBindingsSha256"),
        "examplesArtifact.sharedBindingsSha256",
    )
    if canonical_sha256(static_binding) != shared_bindings_sha256:
        raise BarSelectorError("examplesArtifact.sharedBindingsSha256 does not match sharedBindings.")
    rows = sorted(
        (_validated_example(value, static_binding) for value in values),
        key=lambda value: value["exampleKey"],
    )
    logical_bar_keys: set[tuple[str, int]] = set()
    track_contracts: dict[str, tuple[str, str, str, str, str]] = {}
    for row in rows:
        logical_key = (str(row["trackId"]), int(row["barIndex"]))
        if logical_key in logical_bar_keys:
            raise BarSelectorError("Bar selector examples contain a duplicate logical (trackId, barIndex).")
        logical_bar_keys.add(logical_key)
        track_contract = (
            str(row["group"]),
            str(row["sourceSummarySha256"]),
            str(row["predictionCoreSha256"]),
            str(row["uncertaintySha256"]),
            str(row["timingSha256"]),
        )
        previous = track_contracts.setdefault(str(row["trackId"]), track_contract)
        if previous != track_contract:
            raise BarSelectorError(
                "Every trackId must retain one confidenceGroupId and one source-summary, "
                "prediction-core, uncertainty, and timing binding across all bars."
            )
    keys = [str(row["exampleKey"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise BarSelectorError("Bar selector examples contain a duplicate sealed bar identity.")

    np = _numpy()
    matrix = np.asarray(
        [[np.nan if value is None else value for value in row["features"]] for row in rows],
        dtype=np.float64,
    )
    labels = np.asarray([1.0 if row["correct"] else 0.0 for row in rows], dtype=np.float64)
    groups = [str(row["group"]) for row in rows]
    unique_groups = sorted(set(groups))
    if len(unique_groups) < OUTER_FOLD_COUNT:
        raise BarSelectorError(f"Selector training requires at least {OUTER_FOLD_COUNT} confidence groups.")
    if float(labels.sum()) <= 0 or float(labels.sum()) >= len(labels):
        raise BarSelectorError("Selector training requires both correct and incorrect development bars.")

    outer_assignment = _folds(groups, OUTER_FOLD_COUNT, "bar-selector-outer-v1")
    outer_folds = np.asarray([outer_assignment[group] for group in groups], dtype=np.int64)
    oof_probability = np.zeros(len(rows), dtype=np.float64)
    outer_reports: list[dict[str, Any]] = []
    fold_plan: dict[str, Any] = {
        "outer": outer_assignment,
        "innerByOuterFold": {},
    }
    for outer_fold in range(OUTER_FOLD_COUNT):
        validate_indices = np.flatnonzero(outer_folds == outer_fold)
        train_indices = np.flatnonzero(outer_folds != outer_fold)
        outer_groups = [groups[int(index)] for index in train_indices]
        selected, scores, inner_assignment = _select_hyperparameters(
            matrix[train_indices],
            labels[train_indices],
            outer_groups,
            np,
            salt=f"bar-selector-inner-v1-outer-{outer_fold}",
        )
        probability, fitted = _fit_predict(
            matrix,
            labels,
            groups,
            train_indices,
            validate_indices,
            selected,
            np,
        )
        if not fitted["converged"]:
            raise BarSelectorError(f"Elastic-net optimizer did not converge for outer fold {outer_fold}.")
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

    final_hyperparameters, final_scores, final_inner_assignment = _select_hyperparameters(
        matrix,
        labels,
        groups,
        np,
        salt="bar-selector-inner-v1-final",
    )
    fold_plan["finalInner"] = final_inner_assignment
    all_indices = np.arange(len(rows), dtype=np.int64)
    final_weights = _group_weights(groups, np)
    imputation, center, scale, all_missing = _fit_preprocessor(matrix, final_weights, np)
    transformed = _transform(matrix, imputation, center, scale, np)
    coefficients, intercept, iterations, converged = _fit_elastic_net(
        transformed,
        labels,
        final_weights,
        final_hyperparameters,
        np,
    )
    if not converged:
        raise BarSelectorError("Elastic-net optimizer did not converge for the final all-development refit.")
    if len(all_indices) != len(rows):  # pragma: no cover - defensive invariant
        raise RuntimeError("Internal selector refit index mismatch.")

    input_payload = [
        {
            "exampleSha256": row["exampleSha256"],
            "exampleKey": row["exampleKey"],
            "trackId": row["trackId"],
            "confidenceGroupId": row["group"],
            "correct": row["correct"],
            "barSummarySha256": row["barSummarySha256"],
            "sourceSummarySha256": row["sourceSummarySha256"],
            "predictionCoreSha256": row["predictionCoreSha256"],
            "uncertaintySha256": row["uncertaintySha256"],
            "timingSha256": row["timingSha256"],
            "barIndex": row["barIndex"],
        }
        for row in rows
    ]
    group_payload = [
        {
            "confidenceGroupId": group,
            "exampleCount": groups.count(group),
            "sampleWeight": math.fsum(
                float(final_weights[index]) for index, value in enumerate(groups) if value == group
            ),
        }
        for group in unique_groups
    ]
    oof_payload = [
        {
            "exampleKey": row["exampleKey"],
            "confidenceGroupId": row["group"],
            "outerFold": int(outer_folds[index]),
            "probability": float(oof_probability[index]),
            "correct": bool(row["correct"]),
            "sampleWeight": float(final_weights[index]),
        }
        for index, row in enumerate(rows)
    ]
    artifact: dict[str, Any] = {
        "schemaVersion": BAR_SELECTOR_ARTIFACT_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "operatingThreshold": None,
        "featureSchemaVersion": "chord_prediction_bar_uncertainty_features_v1",
        "featureNames": list(BAR_FEATURE_NAMES),
        "featureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
        "barOutcomeEligibilityContract": dict(BAR_OUTCOME_ELIGIBILITY_CONTRACT),
        "barOutcomeEligibilityContractSha256": BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
        "binding": dict(static_binding),
        "training": {
            "split": "development",
            "target": "correct:boolean",
            "structuralEligibilityInput": "pre-frozen-by-example-builder; not an estimator feature",
            "groupField": "confidenceGroupId",
            "groupFallback": None,
            "groupSampleWeight": "one-per-confidence-group",
            "outerFoldCount": OUTER_FOLD_COUNT,
            "innerFoldCount": INNER_FOLD_COUNT,
            "exampleCount": len(rows),
            "groupCount": len(unique_groups),
            "correctCount": int(labels.sum()),
            "incorrectCount": int(len(labels) - labels.sum()),
            "inputSetSha256": canonical_sha256(
                {
                    "sourceExamplesArtifactSha256": source_artifact_sha256,
                    "sourceExampleSetSha256": example_set_sha256,
                    "rows": input_payload,
                }
            ),
            "sourceExamplesArtifactSha256": source_artifact_sha256,
            "sourceExampleSetSha256": example_set_sha256,
            "sourceSharedBindingsSha256": shared_bindings_sha256,
            "sourceBenchmarkReportSha256": source["sourceBenchmarkReportSha256"],
            "sourceRuntimeBarGridManifestSha256": source["sourceRuntimeBarGridManifestSha256"],
            "sourceGroupManifestSha256": source["sourceGroupManifestSha256"],
            "groupSetSha256": canonical_sha256(group_payload),
            "foldPlanSha256": canonical_sha256(fold_plan),
            "oofPredictionSetSha256": canonical_sha256(oof_payload),
            "configSha256": BAR_SELECTOR_CONFIG_SHA256,
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
        "outOfFoldEvaluation": _evaluation(oof_probability, labels, final_weights, keys, np),
        "estimator": {
            "kind": "standardized-elastic-net-logistic-regression",
            "imputation": "group-weighted-training-median",
            "imputationValues": imputation.tolist(),
            "allMissingFeatureNames": [
                BAR_FEATURE_NAMES[index] for index, missing in enumerate(all_missing.tolist()) if missing
            ],
            "center": center.tolist(),
            "scale": scale.tolist(),
            "coefficients": coefficients.tolist(),
            "intercept": float(intercept),
            "hyperparameters": final_hyperparameters,
            "optimizer": {
                "kind": "deterministic-proximal-gradient-v1",
                "iterations": int(iterations),
                "converged": bool(converged),
                "maximumIterations": OPTIMIZER_MAX_ITERATIONS,
                "tolerance": OPTIMIZER_TOLERANCE,
            },
        },
    }
    artifact["artifactSha256"] = canonical_sha256(artifact)
    validate_bar_selector_artifact(artifact)
    return artifact


_ARTIFACT_FIELDS = frozenset(
    {
        "schemaVersion",
        "developmentOnly",
        "promotionEligible",
        "operatingThreshold",
        "featureSchemaVersion",
        "featureNames",
        "featureContractSha256",
        "barOutcomeEligibilityContract",
        "barOutcomeEligibilityContractSha256",
        "binding",
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
        "structuralEligibilityInput",
        "groupField",
        "groupFallback",
        "groupSampleWeight",
        "outerFoldCount",
        "innerFoldCount",
        "exampleCount",
        "groupCount",
        "correctCount",
        "incorrectCount",
        "inputSetSha256",
        "sourceExamplesArtifactSha256",
        "sourceExampleSetSha256",
        "sourceSharedBindingsSha256",
        "sourceBenchmarkReportSha256",
        "sourceRuntimeBarGridManifestSha256",
        "sourceGroupManifestSha256",
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
_GROUP_FOLD_FIELDS = frozenset({"confidenceGroupId", "innerFold"})
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
    {
        "selectedHyperparameters",
        "innerCvScores",
        "innerFoldAssignments",
        "innerFoldAssignmentSha256",
    }
)
_OOF_AUDIT_FIELDS = frozenset(
    {
        "exampleKey",
        "confidenceGroupId",
        "outerFold",
        "probability",
        "correct",
        "sampleWeight",
    }
)
_EVALUATION_FIELDS = frozenset(
    {
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
_OPTIMIZER_FIELDS = frozenset({"kind", "iterations", "converged", "maximumIterations", "tolerance"})


def _validated_cv_scores(value: Any, name: str) -> list[dict[str, Any]]:
    raw_scores = _sequence(value, name)
    if len(raw_scores) != len(ELASTIC_NET_GRID):
        raise BarSelectorError(f"{name} must report every frozen elastic-net candidate.")
    scores: list[dict[str, Any]] = []
    for expected_index, raw in enumerate(raw_scores):
        score = _mapping(raw, f"{name}[{expected_index}]")
        _exact_fields(score, _CV_SCORE_FIELDS, f"{name}[{expected_index}]")
        if score.get("gridIndex") != expected_index or score.get("hyperparameters") != ELASTIC_NET_GRID[expected_index]:
            raise BarSelectorError(f"{name} changed the frozen candidate order.")
        loss = _finite(score.get("groupBalancedLogLoss"), f"{name}[{expected_index}].groupBalancedLogLoss")
        if loss < 0:
            raise BarSelectorError(f"{name} contains a negative log loss.")
        scores.append(dict(score))
    return scores


def _validated_inner_assignments(value: Any, name: str) -> dict[str, int]:
    rows = _sequence(value, name)
    output: dict[str, int] = {}
    ordered_groups: list[str] = []
    for index, raw in enumerate(rows):
        row = _mapping(raw, f"{name}[{index}]")
        _exact_fields(row, _GROUP_FOLD_FIELDS, f"{name}[{index}]")
        group = _nonempty_string(row.get("confidenceGroupId"), f"{name}[{index}].confidenceGroupId")
        fold = _integer(row.get("innerFold"), f"{name}[{index}].innerFold")
        if fold >= INNER_FOLD_COUNT or group in output:
            raise BarSelectorError(f"{name} contains an invalid or duplicate group assignment.")
        output[group] = fold
        ordered_groups.append(group)
    if ordered_groups != sorted(ordered_groups):
        raise BarSelectorError(f"{name} must retain canonical confidence-group order.")
    if set(output.values()) != set(range(INNER_FOLD_COUNT)):
        raise BarSelectorError(f"{name} must populate all frozen inner folds.")
    return output


def validate_bar_selector_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the canonical artifact and return numeric estimator state."""

    value = _mapping(artifact, "artifact")
    _exact_fields(value, _ARTIFACT_FIELDS, "artifact")
    if value.get("schemaVersion") != BAR_SELECTOR_ARTIFACT_SCHEMA:
        raise BarSelectorError("Unsupported bar selector artifact schemaVersion.")
    if (
        value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
        or value.get("operatingThreshold") is not None
    ):
        raise BarSelectorError("Bar selector artifact must remain development-only with no operating threshold.")
    artifact_sha256 = _sha256(value.get("artifactSha256"), "artifact.artifactSha256")
    if canonical_sha256(_unsigned(value, "artifactSha256")) != artifact_sha256:
        raise BarSelectorError("artifact.artifactSha256 does not match its canonical payload.")
    if (
        value.get("featureSchemaVersion") != "chord_prediction_bar_uncertainty_features_v1"
        or tuple(_sequence(value.get("featureNames"), "artifact.featureNames")) != BAR_FEATURE_NAMES
        or value.get("featureContractSha256") != BAR_FEATURE_CONTRACT_SHA256
        or value.get("barOutcomeEligibilityContract") != BAR_OUTCOME_ELIGIBILITY_CONTRACT
        or value.get("barOutcomeEligibilityContractSha256") != BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256
    ):
        raise BarSelectorError("Selector artifact feature or outcome/eligibility contract was changed.")
    binding = _validated_shared_bindings(value.get("binding"), "artifact.binding")
    training = _mapping(value.get("training"), "artifact.training")
    _exact_fields(training, _TRAINING_FIELDS, "artifact.training")
    if (
        training.get("split") != "development"
        or training.get("target") != "correct:boolean"
        or training.get("structuralEligibilityInput") != "pre-frozen-by-example-builder; not an estimator feature"
        or training.get("groupField") != "confidenceGroupId"
        or training.get("groupFallback") is not None
        or training.get("groupSampleWeight") != "one-per-confidence-group"
        or training.get("outerFoldCount") != OUTER_FOLD_COUNT
        or training.get("innerFoldCount") != INNER_FOLD_COUNT
        or training.get("configSha256") != BAR_SELECTOR_CONFIG_SHA256
    ):
        raise BarSelectorError("Selector training contract was changed.")
    for name in (
        "inputSetSha256",
        "groupSetSha256",
        "foldPlanSha256",
        "oofPredictionSetSha256",
        "sourceExamplesArtifactSha256",
        "sourceExampleSetSha256",
        "sourceSharedBindingsSha256",
        "sourceBenchmarkReportSha256",
        "sourceRuntimeBarGridManifestSha256",
        "sourceGroupManifestSha256",
    ):
        _sha256(training.get(name), f"artifact.training.{name}")
    example_count = _integer(training.get("exampleCount"), "artifact.training.exampleCount", minimum=1)
    group_count = _integer(training.get("groupCount"), "artifact.training.groupCount", minimum=OUTER_FOLD_COUNT)
    correct_count = _integer(training.get("correctCount"), "artifact.training.correctCount", minimum=1)
    incorrect_count = _integer(training.get("incorrectCount"), "artifact.training.incorrectCount", minimum=1)
    if correct_count + incorrect_count != example_count:
        raise BarSelectorError("Selector training outcome counts do not match exampleCount.")
    group_audit = _sequence(training.get("groupWeightAudit"), "artifact.training.groupWeightAudit")
    if len(group_audit) != group_count:
        raise BarSelectorError("Selector groupWeightAudit does not match groupCount.")
    group_counts: dict[str, int] = {}
    for index, raw in enumerate(group_audit):
        row = _mapping(raw, f"artifact.training.groupWeightAudit[{index}]")
        if set(row) != {"confidenceGroupId", "exampleCount", "sampleWeight"}:
            raise BarSelectorError("Selector groupWeightAudit row fields were changed.")
        group = _nonempty_string(row.get("confidenceGroupId"), "groupWeightAudit.confidenceGroupId")
        count = _integer(row.get("exampleCount"), "groupWeightAudit.exampleCount", minimum=1)
        if group in group_counts:
            raise BarSelectorError("Selector groupWeightAudit contains a duplicate confidence group.")
        group_counts[group] = count
        if not math.isclose(_finite(row.get("sampleWeight"), "groupWeightAudit.sampleWeight"), 1.0, abs_tol=1e-12):
            raise BarSelectorError("Every confidence group must have total sample weight exactly one.")
    if sum(group_counts.values()) != example_count:
        raise BarSelectorError("Selector groupWeightAudit example counts do not sum to exampleCount.")
    if list(group_counts) != sorted(group_counts):
        raise BarSelectorError("Selector groupWeightAudit must retain canonical confidence-group order.")
    if canonical_sha256(group_audit) != training.get("groupSetSha256"):
        raise BarSelectorError("Selector groupSetSha256 does not match groupWeightAudit.")

    raw_outer_assignments = _sequence(
        training.get("outerFoldAssignments"),
        "artifact.training.outerFoldAssignments",
    )
    outer_assignment: dict[str, int] = {}
    for index, raw in enumerate(raw_outer_assignments):
        row = _mapping(raw, f"artifact.training.outerFoldAssignments[{index}]")
        if set(row) != {"confidenceGroupId", "outerFold"}:
            raise BarSelectorError("Selector outerFoldAssignments row fields were changed.")
        group = _nonempty_string(row.get("confidenceGroupId"), "outerFoldAssignments.confidenceGroupId")
        fold = _integer(row.get("outerFold"), "outerFoldAssignments.outerFold")
        if fold >= OUTER_FOLD_COUNT or group in outer_assignment:
            raise BarSelectorError("Selector outerFoldAssignments contains an invalid or duplicate group.")
        outer_assignment[group] = fold
    if set(outer_assignment) != set(group_counts) or set(outer_assignment.values()) != set(range(OUTER_FOLD_COUNT)):
        raise BarSelectorError("Selector outerFoldAssignments does not cover every group and outer fold exactly once.")
    if list(outer_assignment) != sorted(outer_assignment):
        raise BarSelectorError("Selector outerFoldAssignments must retain canonical confidence-group order.")

    raw_outer_reports = _sequence(
        training.get("outerHyperparameterSelection"),
        "artifact.training.outerHyperparameterSelection",
    )
    if len(raw_outer_reports) != OUTER_FOLD_COUNT:
        raise BarSelectorError("Selector must report every outer fold exactly once.")
    inner_by_outer: dict[str, dict[str, int]] = {}
    seen_outer_folds: set[int] = set()
    for index, raw in enumerate(raw_outer_reports):
        report = _mapping(raw, f"outerHyperparameterSelection[{index}]")
        _exact_fields(report, _OUTER_REPORT_FIELDS, f"outerHyperparameterSelection[{index}]")
        outer_fold = _integer(report.get("outerFold"), f"outerHyperparameterSelection[{index}].outerFold")
        if outer_fold != index or outer_fold in seen_outer_folds:
            raise BarSelectorError("Selector outer reports contain an invalid or duplicate fold.")
        seen_outer_folds.add(outer_fold)
        scores = _validated_cv_scores(
            report.get("innerCvScores"),
            f"outerHyperparameterSelection[{index}].innerCvScores",
        )
        selected = report.get("selectedHyperparameters")
        expected_selected = min(scores, key=lambda row: (row["groupBalancedLogLoss"], row["gridIndex"]))
        if selected != expected_selected["hyperparameters"]:
            raise BarSelectorError("Selector outer report did not retain the minimum inner-CV candidate.")
        inner_assignment = _validated_inner_assignments(
            report.get("innerFoldAssignments"),
            f"outerHyperparameterSelection[{index}].innerFoldAssignments",
        )
        held_out = {group for group, fold in outer_assignment.items() if fold == outer_fold}
        if set(inner_assignment) != set(group_counts) - held_out:
            raise BarSelectorError("Selector inner folds include an outer-held-out group or omit a training group.")
        inner_by_outer[str(outer_fold)] = inner_assignment
        iterations = _integer(report.get("fitIterations"), "outerHyperparameterSelection.fitIterations", minimum=1)
        if iterations > OPTIMIZER_MAX_ITERATIONS or report.get("fitConverged") is not True:
            raise BarSelectorError("Selector outer fit audit is invalid.")

    final_selection = _mapping(
        training.get("finalHyperparameterSelection"),
        "artifact.training.finalHyperparameterSelection",
    )
    _exact_fields(final_selection, _FINAL_SELECTION_FIELDS, "artifact.training.finalHyperparameterSelection")
    final_scores = _validated_cv_scores(
        final_selection.get("innerCvScores"),
        "artifact.training.finalHyperparameterSelection.innerCvScores",
    )
    expected_final = min(final_scores, key=lambda row: (row["groupBalancedLogLoss"], row["gridIndex"]))
    if final_selection.get("selectedHyperparameters") != expected_final["hyperparameters"]:
        raise BarSelectorError("Selector final refit did not retain the minimum inner-CV candidate.")
    final_inner = _validated_inner_assignments(
        final_selection.get("innerFoldAssignments"),
        "artifact.training.finalHyperparameterSelection.innerFoldAssignments",
    )
    if set(final_inner) != set(group_counts):
        raise BarSelectorError("Selector final inner folds do not cover every development group.")
    final_inner_sha256 = _sha256(
        final_selection.get("innerFoldAssignmentSha256"),
        "artifact.training.finalHyperparameterSelection.innerFoldAssignmentSha256",
    )
    if canonical_sha256(final_inner) != final_inner_sha256:
        raise BarSelectorError("Selector final inner-fold assignment hash does not match.")
    fold_plan = {
        "outer": outer_assignment,
        "innerByOuterFold": inner_by_outer,
        "finalInner": final_inner,
    }
    if canonical_sha256(fold_plan) != training.get("foldPlanSha256"):
        raise BarSelectorError("Selector foldPlanSha256 does not match the audited group assignments.")

    oof_rows = _sequence(training.get("oofAuditRows"), "artifact.training.oofAuditRows")
    if len(oof_rows) != example_count:
        raise BarSelectorError("Selector OOF audit row count does not match exampleCount.")
    oof_keys: set[str] = set()
    oof_group_counts: dict[str, int] = {group: 0 for group in group_counts}
    oof_group_weight: dict[str, list[float]] = {group: [] for group in group_counts}
    oof_probabilities: list[float] = []
    oof_labels: list[float] = []
    oof_weights: list[float] = []
    oof_ordered_keys: list[str] = []
    for index, raw in enumerate(oof_rows):
        row = _mapping(raw, f"artifact.training.oofAuditRows[{index}]")
        _exact_fields(row, _OOF_AUDIT_FIELDS, f"artifact.training.oofAuditRows[{index}]")
        key = _sha256(row.get("exampleKey"), f"artifact.training.oofAuditRows[{index}].exampleKey")
        group = _nonempty_string(
            row.get("confidenceGroupId"),
            f"artifact.training.oofAuditRows[{index}].confidenceGroupId",
        )
        fold = _integer(row.get("outerFold"), f"artifact.training.oofAuditRows[{index}].outerFold")
        probability = _finite(row.get("probability"), f"artifact.training.oofAuditRows[{index}].probability")
        correct = row.get("correct")
        if not isinstance(correct, bool):
            raise BarSelectorError("Selector OOF audit correctness must be boolean audit metadata.")
        sample_weight = _finite(
            row.get("sampleWeight"),
            f"artifact.training.oofAuditRows[{index}].sampleWeight",
        )
        if (
            key in oof_keys
            or group not in outer_assignment
            or fold != outer_assignment[group]
            or not 0 <= probability <= 1
            or sample_weight <= 0
        ):
            raise BarSelectorError("Selector OOF audit row is duplicated, misgrouped, or invalid.")
        oof_keys.add(key)
        oof_group_counts[group] += 1
        oof_group_weight[group].append(sample_weight)
        oof_probabilities.append(probability)
        oof_labels.append(1.0 if correct else 0.0)
        oof_weights.append(sample_weight)
        oof_ordered_keys.append(key)
    if oof_group_counts != group_counts:
        raise BarSelectorError("Selector OOF audit rows do not preserve group example counts.")
    if [str(row["exampleKey"]) for row in oof_rows] != sorted(oof_keys):
        raise BarSelectorError("Selector OOF audit rows must retain canonical example-key order.")
    for group, weights in oof_group_weight.items():
        expected_weight = 1.0 / group_counts[group]
        if any(
            not math.isclose(weight, expected_weight, rel_tol=0, abs_tol=1e-12) for weight in weights
        ) or not math.isclose(
            math.fsum(weights),
            1.0,
            rel_tol=0,
            abs_tol=1e-12,
        ):
            raise BarSelectorError("Selector OOF sample weights do not give every confidence group unit mass.")
    if canonical_sha256(oof_rows) != training.get("oofPredictionSetSha256"):
        raise BarSelectorError("Selector oofPredictionSetSha256 does not match OOF audit rows.")

    evaluation = _mapping(value.get("outOfFoldEvaluation"), "artifact.outOfFoldEvaluation")
    _exact_fields(evaluation, _EVALUATION_FIELDS, "artifact.outOfFoldEvaluation")
    for name in (
        "groupBalancedLogLoss",
        "groupBalancedBrierScore",
        "groupBalancedAreaUnderRiskCoverage",
    ):
        metric = _finite(evaluation.get(name), f"artifact.outOfFoldEvaluation.{name}")
        if metric < 0:
            raise BarSelectorError("Selector OOF metrics must be non-negative.")
    if (
        evaluation.get("precisionCoveragePolicy")
        != "fixed descriptive coverage targets; no operating threshold selected"
    ):
        raise BarSelectorError("Selector precision/coverage policy was changed.")
    points = _sequence(evaluation.get("precisionCoverage"), "artifact.outOfFoldEvaluation.precisionCoverage")
    if len(points) != len(PRECISION_COVERAGE_TARGETS):
        raise BarSelectorError("Selector precision/coverage report has the wrong number of fixed points.")
    for target, raw in zip(PRECISION_COVERAGE_TARGETS, points, strict=True):
        point = _mapping(raw, "precisionCoverage point")
        _exact_fields(point, _PRECISION_COVERAGE_FIELDS, "precisionCoverage point")
        if not math.isclose(_finite(point.get("targetCoverage"), "targetCoverage"), target, abs_tol=1e-12):
            raise BarSelectorError("Selector precision/coverage targets were changed.")
        for name in ("realizableCoverage", "groupBalancedPrecision", "groupBalancedRisk"):
            number = _finite(point.get(name), f"precisionCoverage.{name}")
            if not 0 <= number <= 1:
                raise BarSelectorError("Selector precision/coverage values must lie in [0, 1].")
        if (
            not math.isclose(
                float(point["groupBalancedPrecision"]) + float(point["groupBalancedRisk"]),
                1.0,
                abs_tol=1e-12,
            )
            or float(point["realizableCoverage"]) + 1e-12 < target
        ):
            raise BarSelectorError("Selector precision/coverage point is internally inconsistent.")
        minimum_probability = _finite(
            point.get("minimumProbabilityAtDescriptivePoint"),
            "precisionCoverage.minimumProbabilityAtDescriptivePoint",
        )
        if not 0 <= minimum_probability <= 1:
            raise BarSelectorError("Selector descriptive probability must lie in [0, 1].")
    np = _numpy()
    recomputed_evaluation = _evaluation(
        np.asarray(oof_probabilities, dtype=np.float64),
        np.asarray(oof_labels, dtype=np.float64),
        np.asarray(oof_weights, dtype=np.float64),
        oof_ordered_keys,
        np,
    )
    if canonical_sha256(recomputed_evaluation) != canonical_sha256(evaluation):
        raise BarSelectorError("Selector OOF headline metrics do not recompute from the sealed audit rows.")

    estimator = _mapping(value.get("estimator"), "artifact.estimator")
    _exact_fields(estimator, _ESTIMATOR_FIELDS, "artifact.estimator")
    if (
        estimator.get("kind") != "standardized-elastic-net-logistic-regression"
        or estimator.get("imputation") != "group-weighted-training-median"
    ):
        raise BarSelectorError("Selector estimator kind or imputation contract was changed.")
    numeric_arrays: dict[str, list[float]] = {}
    for name in ("imputationValues", "center", "scale", "coefficients"):
        raw_array = _sequence(estimator.get(name), f"artifact.estimator.{name}")
        if len(raw_array) != len(BAR_FEATURE_NAMES):
            raise BarSelectorError(f"artifact.estimator.{name} has the wrong feature dimension.")
        numeric_arrays[name] = [_finite(item, f"artifact.estimator.{name}") for item in raw_array]
    if any(scale <= 0 for scale in numeric_arrays["scale"]):
        raise BarSelectorError("Selector estimator scales must be positive.")
    intercept = _finite(estimator.get("intercept"), "artifact.estimator.intercept")
    hyperparameters = _mapping(estimator.get("hyperparameters"), "artifact.estimator.hyperparameters")
    if dict(hyperparameters) not in ELASTIC_NET_GRID:
        raise BarSelectorError("Selector estimator hyperparameters are outside the frozen grid.")
    all_missing_names = _sequence(
        estimator.get("allMissingFeatureNames"),
        "artifact.estimator.allMissingFeatureNames",
    )
    expected_missing_order = [name for name in BAR_FEATURE_NAMES if name in set(all_missing_names)]
    if list(all_missing_names) != expected_missing_order:
        raise BarSelectorError("Selector allMissingFeatureNames is invalid.")
    optimizer = _mapping(estimator.get("optimizer"), "artifact.estimator.optimizer")
    _exact_fields(optimizer, _OPTIMIZER_FIELDS, "artifact.estimator.optimizer")
    if (
        optimizer.get("kind") != "deterministic-proximal-gradient-v1"
        or optimizer.get("maximumIterations") != OPTIMIZER_MAX_ITERATIONS
        or optimizer.get("tolerance") != OPTIMIZER_TOLERANCE
        or optimizer.get("converged") is not True
    ):
        raise BarSelectorError("Selector optimizer contract was changed.")
    optimizer_iterations = _integer(optimizer.get("iterations"), "artifact.estimator.optimizer.iterations", minimum=1)
    if optimizer_iterations > OPTIMIZER_MAX_ITERATIONS:
        raise BarSelectorError("Selector optimizer iteration count exceeds the frozen maximum.")
    return {
        "artifactSha256": artifact_sha256,
        "binding": binding,
        "imputation": numeric_arrays["imputationValues"],
        "center": numeric_arrays["center"],
        "scale": numeric_arrays["scale"],
        "coefficients": numeric_arrays["coefficients"],
        "intercept": intercept,
    }


def _application_result(
    *,
    probability: float | None,
    reason: str | None,
    artifact_sha256: str | None,
    summary_sha256: str | None,
    bar_index: int | None,
) -> dict[str, Any]:
    return {
        "schemaVersion": BAR_SELECTOR_APPLICATION_SCHEMA,
        "probability": probability,
        "reason": reason,
        "operatingThreshold": None,
        "selectorArtifactSha256": artifact_sha256,
        "barSummarySha256": summary_sha256,
        "barIndex": bar_index,
    }


def apply_bar_selector(
    bar_summary: Mapping[str, Any],
    artifact: Mapping[str, Any],
    *,
    bar_index: int,
    shared_bindings: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a correctness probability, or null plus a fail-closed reason."""

    try:
        estimator = validate_bar_selector_artifact(artifact)
    except (BarSelectorError, TypeError, ValueError, OverflowError):
        return _application_result(
            probability=None,
            reason="invalid-selector-artifact",
            artifact_sha256=None,
            summary_sha256=None,
            bar_index=bar_index if isinstance(bar_index, int) and not isinstance(bar_index, bool) else None,
        )
    try:
        index = _integer(bar_index, "barIndex")
        summary = _validated_compact_bar_summary(bar_summary)
    except (BarSelectorError, TypeError, ValueError, OverflowError):
        return _application_result(
            probability=None,
            reason="invalid-bar-summary",
            artifact_sha256=estimator["artifactSha256"],
            summary_sha256=None,
            bar_index=bar_index if isinstance(bar_index, int) and not isinstance(bar_index, bool) else None,
        )
    try:
        supplied_binding = _validated_shared_bindings(shared_bindings, "sharedBindings")
    except (BarSelectorError, TypeError, ValueError, OverflowError):
        return _application_result(
            probability=None,
            reason="invalid-shared-bindings",
            artifact_sha256=estimator["artifactSha256"],
            summary_sha256=summary["barSummarySha256"],
            bar_index=index,
        )
    if index != summary["index"]:
        return _application_result(
            probability=None,
            reason="bar-index-mismatch",
            artifact_sha256=estimator["artifactSha256"],
            summary_sha256=summary["barSummarySha256"],
            bar_index=index,
        )
    if (
        summary["sharedBindingsSha256"] != canonical_sha256(supplied_binding)
        or supplied_binding != estimator["binding"]
    ):
        return _application_result(
            probability=None,
            reason="binding-mismatch",
            artifact_sha256=estimator["artifactSha256"],
            summary_sha256=summary["barSummarySha256"],
            bar_index=index,
        )
    vector = summary["features"]
    try:
        numeric = [
            estimator["imputation"][position] if item is None else float(item) for position, item in enumerate(vector)
        ]
        logit = estimator["intercept"] + math.fsum(
            (value - estimator["center"][position]) / estimator["scale"][position] * estimator["coefficients"][position]
            for position, value in enumerate(numeric)
        )
        probability = 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, logit))))
    except (ArithmeticError, TypeError, ValueError, OverflowError):
        return _application_result(
            probability=None,
            reason="invalid-feature-vector",
            artifact_sha256=estimator["artifactSha256"],
            summary_sha256=summary["barSummarySha256"],
            bar_index=index,
        )
    return _application_result(
        probability=probability,
        reason=None,
        artifact_sha256=estimator["artifactSha256"],
        summary_sha256=summary["barSummarySha256"],
        bar_index=index,
    )
