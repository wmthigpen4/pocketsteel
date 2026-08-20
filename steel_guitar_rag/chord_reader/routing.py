"""Calibrated soft routing for factorized chord evidence.

The v8 domain gate selected one complete decoder or the other at a hidden
threshold.  This module instead learns a continuous, development-only blend
weight and applies it independently to normalized factor heads.  A routing
failure is deliberately boring: it returns weight zero, which preserves the
expanded model exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROUTER_SCHEMA = "chord_soft_router_v1"
ROUTER_FEATURE_SCHEMA = "chord_soft_router_features_v1"
DEFAULT_ROUTER_WEIGHT = 0.0

TEXTURE_FEATURE_NAMES = (
    "fullChromaEntropy",
    "fullChromaPeak",
    "fullChromaActivePitchClasses",
    "bassChromaEntropy",
    "bassChromaPeak",
    "bassChromaActivePitchClasses",
    "middleChromaEntropy",
    "middleChromaPeak",
    "middleChromaActivePitchClasses",
    "highChromaEntropy",
    "highChromaPeak",
    "highChromaActivePitchClasses",
    "chromaDeltaMeanAbsolute",
    "energyCoefficientOfVariation",
)

ROUTER_FEATURE_NAMES = TEXTURE_FEATURE_NAMES + (
    "rootDisagreementRate",
    "modeDisagreementRate",
    "expandedRootEntropy",
    "conservativeRootEntropy",
    "expandedChangeRate",
    "conservativeChangeRate",
    "boundaryDisagreement",
    "beatConfidence",
    "downbeatConfidence",
    "oodDistance",
)

UTILITY_SPECIFICATION = {
    "root": 0.30,
    "majorMinor": 0.25,
    "detailed": 0.20,
    "boundaryF1": 0.20,
    "oneMinusCappedEditRate": 0.05,
}


def _numpy() -> Any:
    return importlib.import_module("numpy")


def _probability_matrix(values: Any, *, name: str, frames: int | None = None) -> Any:
    numpy = _numpy()
    array = numpy.asarray(values)
    if array.ndim != 2 or array.shape[0] < 1 or array.shape[1] < 1:
        raise ValueError(f"{name} probabilities must have shape (frames, classes).")
    if frames is not None and int(array.shape[0]) != frames:
        raise ValueError(f"{name} probabilities must have {frames} frames.")
    if not numpy.issubdtype(array.dtype, numpy.floating):
        array = array.astype(numpy.float64)
    if not numpy.all(numpy.isfinite(array)) or numpy.any(array < 0):
        raise ValueError(f"{name} probabilities must be finite and non-negative.")
    totals = array.sum(axis=1)
    if not numpy.allclose(totals, 1.0, rtol=1e-5, atol=1e-7):
        raise ValueError(f"{name} probability rows must sum to one.")
    return array


def _boundary_vector(values: Any, *, frames: int) -> Any:
    numpy = _numpy()
    array = numpy.asarray(values)
    if array.ndim == 2 and array.shape[1] == 1:
        array = array[:, 0]
    if array.ndim != 1 or int(array.shape[0]) != frames:
        raise ValueError(f"boundary probabilities must have shape ({frames},) or ({frames}, 1).")
    if not numpy.issubdtype(array.dtype, numpy.floating):
        array = array.astype(numpy.float64)
    if not numpy.all(numpy.isfinite(array)) or numpy.any(array < 0) or numpy.any(array > 1):
        raise ValueError("boundary probabilities must be finite values from zero to one.")
    return array


@dataclass(frozen=True)
class FactorizedEvidence:
    """Normalized, frame-aligned evidence emitted by one chord expert."""

    root: Any
    mode: Any
    quality: Any
    bass: Any
    boundary: Any

    def __post_init__(self) -> None:
        root = _probability_matrix(self.root, name="root")
        frames = int(root.shape[0])
        mode = _probability_matrix(self.mode, name="mode", frames=frames)
        quality = _probability_matrix(self.quality, name="quality", frames=frames)
        bass = _probability_matrix(self.bass, name="bass", frames=frames)
        boundary = _boundary_vector(self.boundary, frames=frames)
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "quality", quality)
        object.__setattr__(self, "bass", bass)
        object.__setattr__(self, "boundary", boundary)

    @property
    def frame_count(self) -> int:
        return int(self.root.shape[0])

    @classmethod
    def from_logits(
        cls,
        *,
        root: Any,
        mode: Any,
        quality: Any,
        bass: Any,
        boundary: Any,
    ) -> "FactorizedEvidence":
        """Normalize independent logits without coupling factor heads."""

        numpy = _numpy()

        def softmax(values: Any) -> Any:
            array = numpy.asarray(values)
            maximum = array.max(axis=-1, keepdims=True)
            output = numpy.exp(array - maximum)
            return output / output.sum(axis=-1, keepdims=True)

        boundary_array = numpy.asarray(boundary)
        boundary_probability = 1.0 / (1.0 + numpy.exp(-numpy.clip(boundary_array, -60, 60)))
        return cls(
            root=softmax(root),
            mode=softmax(mode),
            quality=softmax(quality),
            bass=softmax(bass),
            boundary=boundary_probability,
        )


def _finite_probability(value: Any, *, default: float = DEFAULT_ROUTER_WEIGHT) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    result = float(value)
    if not math.isfinite(result):
        return default
    return min(1.0, max(0.0, result))


def continuous_ood_shrink(
    weight: Any,
    ood_distance: Any,
    *,
    strength: float = 0.35,
    default: float = DEFAULT_ROUTER_WEIGHT,
) -> float:
    """Continuously shrink an uncertain route toward the safe expanded expert."""

    probability = _finite_probability(weight, default=default)
    if isinstance(ood_distance, bool) or not isinstance(ood_distance, (int, float)):
        return default
    distance = float(ood_distance)
    if not math.isfinite(distance):
        return default
    if not math.isfinite(strength) or strength < 0:
        raise ValueError("OOD shrink strength must be finite and non-negative.")
    return probability * math.exp(-strength * max(0.0, distance))


def blend_factorized_evidence(
    expanded: FactorizedEvidence,
    conservative: FactorizedEvidence,
    weight: Any,
    *,
    components: Sequence[str] = ("root", "mode", "quality", "bass", "boundary"),
    ood_distance: float = 0.0,
    ood_strength: float = 0.35,
) -> FactorizedEvidence:
    """Convexly blend selected heads while preserving exact endpoint behavior.

    ``weight=0`` returns ``expanded`` itself.  ``weight=1`` returns
    ``conservative`` itself when all heads are selected and no OOD shrink is
    requested.  Selecting only ``quality`` therefore cannot feed conservative
    evidence back into the root path.
    """

    if expanded.frame_count != conservative.frame_count:
        raise ValueError("Chord experts must contain the same number of frames.")
    allowed = {"root", "mode", "quality", "bass", "boundary"}
    selected = frozenset(components)
    unknown = selected - allowed
    if unknown:
        raise ValueError(f"Unknown evidence components: {', '.join(sorted(unknown))}.")
    for name in allowed:
        if getattr(expanded, name).shape != getattr(conservative, name).shape:
            raise ValueError(f"Chord experts have incompatible {name} probability shapes.")

    effective = continuous_ood_shrink(
        weight,
        ood_distance,
        strength=ood_strength,
        default=DEFAULT_ROUTER_WEIGHT,
    )
    if effective == 0.0 or not selected:
        return expanded
    if effective == 1.0 and selected == allowed:
        return conservative

    numpy = _numpy()
    values: dict[str, Any] = {}
    for name in ("root", "mode", "quality", "bass", "boundary"):
        left = getattr(expanded, name)
        right = getattr(conservative, name)
        if name not in selected or numpy.array_equal(left, right):
            values[name] = left
        elif effective == 1.0:
            values[name] = right
        else:
            values[name] = (1.0 - effective) * left + effective * right
    return FactorizedEvidence(**values)


def _entropy(probabilities: Any, numpy: Any) -> float:
    classes = int(probabilities.shape[1])
    if classes <= 1:
        return 0.0
    clipped = numpy.clip(probabilities, 1e-12, 1.0)
    return float(numpy.mean(-numpy.sum(clipped * numpy.log(clipped), axis=1)) / math.log(classes))


def _change_rate(evidence: FactorizedEvidence, numpy: Any) -> float:
    if evidence.frame_count <= 1:
        return 0.0
    root = evidence.root.argmax(axis=1)
    mode = evidence.mode.argmax(axis=1)
    changed = (root[1:] != root[:-1]) | (mode[1:] != mode[:-1])
    return float(changed.mean())


def router_summary_features(
    texture_profile: Sequence[float],
    expanded: FactorizedEvidence,
    conservative: FactorizedEvidence,
    *,
    beat_confidence: float = 0.0,
    downbeat_confidence: float = 0.0,
    ood_distance: float = 0.0,
) -> dict[str, float]:
    """Build the documented router vector; no decision threshold is applied."""

    if len(texture_profile) != len(TEXTURE_FEATURE_NAMES):
        raise ValueError(f"Router texture profile must contain {len(TEXTURE_FEATURE_NAMES)} values.")
    if expanded.frame_count != conservative.frame_count:
        raise ValueError("Chord experts must contain the same number of frames.")
    numpy = _numpy()
    values = {
        name: float(value)
        for name, value in zip(TEXTURE_FEATURE_NAMES, texture_profile, strict=True)
    }
    values.update(
        {
            "rootDisagreementRate": float(
                numpy.mean(expanded.root.argmax(axis=1) != conservative.root.argmax(axis=1))
            ),
            "modeDisagreementRate": float(
                numpy.mean(expanded.mode.argmax(axis=1) != conservative.mode.argmax(axis=1))
            ),
            "expandedRootEntropy": _entropy(expanded.root, numpy),
            "conservativeRootEntropy": _entropy(conservative.root, numpy),
            "expandedChangeRate": _change_rate(expanded, numpy),
            "conservativeChangeRate": _change_rate(conservative, numpy),
            "boundaryDisagreement": float(
                numpy.mean(numpy.abs(expanded.boundary - conservative.boundary))
            ),
            "beatConfidence": float(beat_confidence),
            "downbeatConfidence": float(downbeat_confidence),
            "oodDistance": float(ood_distance),
        }
    )
    return values


def _metric(metrics: Mapping[str, Any], *paths: tuple[str, ...]) -> float:
    for path in paths:
        value: Any = metrics
        try:
            for name in path:
                value = value[name]
        except (KeyError, TypeError):
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
            return float(value)
    raise ValueError(f"Router utility is missing metric alternatives: {paths!r}.")


def router_utility(metrics: Mapping[str, Any]) -> float:
    """Return the audit-locked multi-objective utility for one expert."""

    root = _metric(metrics, ("root",), ("rootAccuracy",), ("rootWeightedRecall",))
    major_minor = _metric(
        metrics,
        ("majorMinor",),
        ("majorMinorAccuracy",),
        ("majorMinorWeightedRecall",),
    )
    detailed = _metric(
        metrics,
        ("detailed",),
        ("detailedAccuracy",),
        ("detailedWeightedRecall",),
    )
    boundary = _metric(metrics, ("boundaryF1",), ("boundary", "f1"), ("boundaryF1Macro",))
    edit_rate = _metric(
        metrics,
        ("editRate",),
        ("sequenceEditRate",),
        ("sequenceEditRateMacro",),
        ("sequenceEdits", "microRate"),
    )
    return (
        0.30 * root
        + 0.25 * major_minor
        + 0.20 * detailed
        + 0.20 * boundary
        + 0.05 * (1.0 - min(max(edit_rate, 0.0), 1.0))
    )


def routing_delta(expanded_metrics: Mapping[str, Any], conservative_metrics: Mapping[str, Any]) -> float:
    """Positive values mean the conservative expert has higher utility."""

    return router_utility(conservative_metrics) - router_utility(expanded_metrics)


def manifest_sha256(value: Path | bytes | str | Mapping[str, Any] | Sequence[Any]) -> str:
    """Hash the exact manifest bytes or a canonical in-memory manifest."""

    if isinstance(value, Path):
        payload = value.read_bytes()
    elif isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sigmoid(value: Any, numpy: Any) -> Any:
    return 1.0 / (1.0 + numpy.exp(-numpy.clip(value, -30.0, 30.0)))


def _fit_logistic(
    features: Any,
    labels: Any,
    weights: Any,
    numpy: Any,
    *,
    regularization: float,
    iterations: int,
    learning_rate: float,
) -> tuple[Any, float]:
    coefficients = numpy.zeros(features.shape[1], dtype=numpy.float64)
    positive_mass = float((weights * labels).sum())
    negative_mass = float((weights * (1.0 - labels)).sum())
    intercept = math.log((positive_mass + 1e-6) / (negative_mass + 1e-6))
    normalizer = max(1e-12, float(weights.sum()))
    for iteration in range(iterations):
        probability = _sigmoid(features @ coefficients + intercept, numpy)
        residual = weights * (probability - labels)
        coefficient_gradient = features.T @ residual / normalizer + regularization * coefficients
        intercept_gradient = float(residual.sum()) / normalizer
        step = learning_rate / math.sqrt(1.0 + iteration / 100.0)
        coefficients -= step * coefficient_gradient
        intercept -= step * intercept_gradient
    return coefficients, float(intercept)


def _reliability_bins(probabilities: Any, labels: Any, weights: Any, numpy: Any, count: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index in range(count):
        lower = index / count
        upper = (index + 1) / count
        selected = (probabilities >= lower) & (
            probabilities <= upper if index == count - 1 else probabilities < upper
        )
        mass = float(weights[selected].sum())
        output.append(
            {
                "minimumProbability": lower,
                "maximumProbability": upper,
                "includesMaximum": index == count - 1,
                "exampleCount": int(selected.sum()),
                "sampleWeight": mass,
                "meanProbability": (
                    float((probabilities[selected] * weights[selected]).sum() / mass) if mass else None
                ),
                "empiricalConservativeWinRate": (
                    float((labels[selected] * weights[selected]).sum() / mass) if mass else None
                ),
            }
        )
    return output


def train_dev_router(
    rows: Iterable[Mapping[str, Any]],
    *,
    manifest_hashes: Mapping[str, str],
    folds: int = 5,
    reliability_bin_count: int = 10,
    regularization: float = 0.02,
    iterations: int = 1200,
    learning_rate: float = 0.08,
    ood_shrink_strength: float = 0.35,
) -> dict[str, Any]:
    """Train a composition-grouped OOF router using development rows only.

    Required row keys are ``compositionId``, ``split``, ``features``,
    ``expandedMetrics``, and ``conservativeMetrics``.  The target is
    ``delta > 0`` and the sample weight is exactly ``abs(delta)``.
    """

    numpy = _numpy()
    values = list(rows)
    if not values:
        raise ValueError("Router training requires development rows.")
    if folds < 2:
        raise ValueError("Grouped router training requires at least two folds.")
    if reliability_bin_count < 2:
        raise ValueError("Router reliability reporting requires at least two bins.")
    if not math.isfinite(ood_shrink_strength) or ood_shrink_strength < 0:
        raise ValueError("OOD shrink strength must be finite and non-negative.")
    if not math.isfinite(regularization) or regularization < 0:
        raise ValueError("Router regularization must be finite and non-negative.")
    if iterations < 1 or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("Router optimization settings must be positive.")
    if not manifest_hashes:
        raise ValueError("Router artifacts must pin at least one manifest hash.")
    for name, digest in manifest_hashes.items():
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
            raise ValueError(f"Manifest hash {name!r} must be a SHA-256 hex digest.")

    matrix: list[list[float]] = []
    groups: list[str] = []
    deltas: list[float] = []
    for row in values:
        if row.get("split") not in {"dev", "development"}:
            raise ValueError("Soft-router training is development-only; test and confirmation rows are sealed.")
        group = str(row.get("compositionId", "")).strip()
        if not group:
            raise ValueError("Every router row needs a compositionId for leakage-safe grouping.")
        feature_values = row.get("features")
        if not isinstance(feature_values, Mapping):
            raise ValueError("Every router row needs a named feature mapping.")
        try:
            vector = [float(feature_values[name]) for name in ROUTER_FEATURE_NAMES]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Router rows must contain every documented numeric feature.") from exc
        if not all(math.isfinite(item) for item in vector):
            raise ValueError("Router training features must be finite.")
        delta = routing_delta(row["expandedMetrics"], row["conservativeMetrics"])
        matrix.append(vector)
        groups.append(group)
        deltas.append(delta)

    unique_groups = sorted(set(groups), key=lambda item: hashlib.sha256(item.encode("utf-8")).hexdigest())
    if len(unique_groups) < folds:
        raise ValueError("Composition-grouped folds cannot exceed the number of unique compositions.")
    fold_by_group = {group: index % folds for index, group in enumerate(unique_groups)}
    group_folds = numpy.asarray([fold_by_group[group] for group in groups], dtype=numpy.int64)
    features = numpy.asarray(matrix, dtype=numpy.float64)
    delta_values = numpy.asarray(deltas, dtype=numpy.float64)
    labels = (delta_values > 0).astype(numpy.float64)
    sample_weights = numpy.abs(delta_values)
    if float(sample_weights.sum()) <= 0:
        raise ValueError("Router utilities are all tied; there is no weighted routing target.")

    out_of_fold_logits = numpy.zeros(len(values), dtype=numpy.float64)
    for fold in range(folds):
        train = group_folds != fold
        validate = ~train
        mean = features[train].mean(axis=0)
        scale = features[train].std(axis=0)
        scale = numpy.where(scale < 1e-8, 1.0, scale)
        coefficients, intercept = _fit_logistic(
            (features[train] - mean) / scale,
            labels[train],
            sample_weights[train],
            numpy,
            regularization=regularization,
            iterations=iterations,
            learning_rate=learning_rate,
        )
        out_of_fold_logits[validate] = ((features[validate] - mean) / scale) @ coefficients + intercept

    # Platt calibration is fitted only to predictions made by models that did
    # not see the corresponding composition.
    calibrator_coefficients, calibrator_intercept = _fit_logistic(
        out_of_fold_logits[:, None],
        labels,
        sample_weights,
        numpy,
        regularization=regularization,
        iterations=iterations,
        learning_rate=learning_rate,
    )
    calibration_slope = float(calibrator_coefficients[0])
    # Reliability metrics use a second composition-grouped cross-fit so the
    # calibrator has not seen the labels whose probabilities it is scoring.
    out_of_fold_probability = numpy.zeros(len(values), dtype=numpy.float64)
    for fold in range(folds):
        train = group_folds != fold
        validate = ~train
        fold_coefficients, fold_intercept = _fit_logistic(
            out_of_fold_logits[train, None],
            labels[train],
            sample_weights[train],
            numpy,
            regularization=regularization,
            iterations=iterations,
            learning_rate=learning_rate,
        )
        out_of_fold_probability[validate] = _sigmoid(
            float(fold_coefficients[0]) * out_of_fold_logits[validate] + fold_intercept,
            numpy,
        )
    normalizer = max(1e-12, float(sample_weights.sum()))
    clipped = numpy.clip(out_of_fold_probability, 1e-8, 1 - 1e-8)
    log_loss = float(
        -(
            sample_weights
            * (labels * numpy.log(clipped) + (1.0 - labels) * numpy.log(1.0 - clipped))
        ).sum()
        / normalizer
    )
    brier = float((sample_weights * (out_of_fold_probability - labels) ** 2).sum() / normalizer)

    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale = numpy.where(scale < 1e-8, 1.0, scale)
    coefficients, intercept = _fit_logistic(
        (features - mean) / scale,
        labels,
        sample_weights,
        numpy,
        regularization=regularization,
        iterations=iterations,
        learning_rate=learning_rate,
    )
    return {
        "schemaVersion": ROUTER_SCHEMA,
        "featureSchemaVersion": ROUTER_FEATURE_SCHEMA,
        "featureNames": list(ROUTER_FEATURE_NAMES),
        "defaultWeight": DEFAULT_ROUTER_WEIGHT,
        "decisionPolicy": "continuous-soft-blend",
        "hardThreshold": None,
        "utility": {
            "formula": ".30*root + .25*majorMinor + .20*detailed + .20*boundaryF1 + .05*(1-min(editRate,1))",
            "coefficients": dict(UTILITY_SPECIFICATION),
            "delta": "utility(conservative)-utility(expanded)",
            "target": "delta>0",
            "sampleWeight": "abs(delta)",
        },
        "model": {
            "kind": "standardized-logistic-regression",
            "mean": mean.tolist(),
            "scale": scale.tolist(),
            "coefficients": coefficients.tolist(),
            "intercept": intercept,
            "calibration": {
                "kind": "platt-on-composition-grouped-oof-logits",
                "slope": calibration_slope,
                "intercept": float(calibrator_intercept),
            },
        },
        "oodShrink": {
            "kind": "exponential-to-default",
            "strength": float(ood_shrink_strength),
        },
        "development": {
            "manifestSha256": dict(sorted(manifest_hashes.items())),
            "split": "dev-only",
            "grouping": "compositionId",
            "foldCount": folds,
            "exampleCount": len(values),
            "compositionCount": len(unique_groups),
            "conservativeWinCount": int(labels.sum()),
            "sampleWeightTotal": float(sample_weights.sum()),
            "foldAssignments": [
                {"compositionId": group, "fold": fold_by_group[group]}
                for group in sorted(fold_by_group)
            ],
            "outOfFold": {
                "calibrationEvaluation": "composition-grouped-cross-fit",
                "weightedLogLoss": log_loss,
                "weightedBrierScore": brier,
                "reliabilityBins": _reliability_bins(
                    out_of_fold_probability,
                    labels,
                    sample_weights,
                    numpy,
                    reliability_bin_count,
                ),
            },
        },
    }


def router_weight(features: Mapping[str, Any] | None, artifact: Mapping[str, Any] | None) -> float:
    """Return a calibrated conservative-expert weight, or exactly zero on failure."""

    if not isinstance(features, Mapping) or not isinstance(artifact, Mapping):
        return DEFAULT_ROUTER_WEIGHT
    if artifact.get("schemaVersion") != ROUTER_SCHEMA:
        return DEFAULT_ROUTER_WEIGHT
    if artifact.get("defaultWeight") != DEFAULT_ROUTER_WEIGHT:
        return DEFAULT_ROUTER_WEIGHT
    if artifact.get("hardThreshold") is not None:
        return DEFAULT_ROUTER_WEIGHT
    try:
        names = artifact["featureNames"]
        if list(names) != list(ROUTER_FEATURE_NAMES):
            return DEFAULT_ROUTER_WEIGHT
        vector = [float(features[name]) for name in names]
        model = artifact["model"]
        mean = [float(value) for value in model["mean"]]
        scale = [float(value) for value in model["scale"]]
        coefficients = [float(value) for value in model["coefficients"]]
        intercept = float(model["intercept"])
        calibration = model["calibration"]
        slope = float(calibration["slope"])
        calibration_intercept = float(calibration["intercept"])
        strength = float(artifact["oodShrink"]["strength"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return DEFAULT_ROUTER_WEIGHT
    numeric = vector + mean + scale + coefficients + [intercept, slope, calibration_intercept, strength]
    if not all(math.isfinite(value) for value in numeric):
        return DEFAULT_ROUTER_WEIGHT
    if len(vector) != len(mean) or len(vector) != len(scale) or len(vector) != len(coefficients):
        return DEFAULT_ROUTER_WEIGHT
    if any(value <= 0 for value in scale) or strength < 0:
        return DEFAULT_ROUTER_WEIGHT
    logit = sum((value - center) / spread * coefficient for value, center, spread, coefficient in zip(vector, mean, scale, coefficients, strict=True)) + intercept
    calibrated = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, slope * logit + calibration_intercept))))
    return continuous_ood_shrink(
        calibrated,
        features.get("oodDistance"),
        strength=strength,
        default=DEFAULT_ROUTER_WEIGHT,
    )
