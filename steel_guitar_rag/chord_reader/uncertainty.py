"""Reference-free uncertainty telemetry for factorized chord inference.

The telemetry in this module is descriptive evidence, not calibrated error
probability. It operates only on logits and the already-extracted feature
representation used for the prediction; it never reads references or claims
physical source properties such as polyphony or bass presence.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any, Mapping, Sequence

from .bar_promotion import canonical_sha256


FACTORIZED_UNCERTAINTY_SCHEMA = "chord_factorized_uncertainty_v1"
FACTORIZED_UNCERTAINTY_BINDING_SCHEMA = "chord_factorized_uncertainty_binding_v1"
FACTORIZED_UNCERTAINTY_CONTRACT_SCHEMA = "chord_factorized_uncertainty_contract_v1"

_UNCERTAINTY_CONTRACT = {
    "schemaVersion": FACTORIZED_UNCERTAINTY_CONTRACT_SCHEMA,
    "referenceFree": True,
    "rootClasses": 13,
    "rootClassOrdering": "0=N; 1..12=chromatic roots C..B",
    "pitchedProductClasses": 4,
    "productClassOrdering": "1=major; 2=minor; 3=dominant; 4=minor-seventh",
    "memberVoteOrdering": (
        "root votes use root class indices 0..12; product votes use Play Along "
        "product indices 1..4 and are null on no-chord frames"
    ),
    "probabilityDomain": "softmax of pre-decode logits",
    "rootAuthority": "final independently decoded root path",
    "productAuthority": ("four-way direct/joint evidence conditioned on the final frozen root"),
    "legacyMemberProductEvidence": "member direct pitched four-way distribution",
    "jointMemberProductEvidence": "member configured direct/joint blend",
    "pairwiseDisagreement": "one minus sum of squared weighted vote-class mass",
    "probabilityFloor": "numpy.float64 tiny before every natural logarithm",
    "normalizedMutualInformation": (
        "natural-log predictive entropy minus weighted expected member natural-log "
        "entropy, divided by natural log(classes)"
    ),
    "normalizedEntropy": (
        "natural-log Shannon entropy divided by natural log(classes), using the float64-tiny probability floor"
    ),
    "jensenShannonDivergence": ("natural-log JSD divided by natural log(2), using the float64-tiny probability floor"),
    "boundaryAggregation": ("sigmoid of combined logit; weighted mean/std of member sigmoid probabilities"),
    "predictionCoreCrossLink": (
        "attached payloads contain predictionCoreSha256 outside shared binding and "
        "contract; uncertaintySha256 covers the cross-link"
    ),
    "timebase": {
        "frameSeconds": 0.1,
        "frameCount": "ceil(durationSeconds / frameSeconds)",
        "timestampConvention": "left-edge",
    },
    "nullSemantics": (
        "product and member-product values are null exactly on no-chord frames; "
        "direct/joint diagnostics are additionally null when no joint contributor exists"
    ),
    "frameSchema": {
        "root": [
            "selectedClass",
            "selectedProbability",
            "topProbability",
            "margin",
            "normalizedEntropy",
        ],
        "product": [
            "applicable",
            "selectedClass",
            "selectedProbability",
            "topProbability",
            "margin",
            "normalizedEntropy",
            "directJointAgreement",
            "directJointJensenShannon",
        ],
        "ensemble": [
            "memberRootVote",
            "memberProductVote",
            "rootSelectedVoteShare",
            "productSelectedVoteShare",
            "rootPairwiseDisagreement",
            "productPairwiseDisagreement",
            "rootSelectedProbabilityStdDev",
            "productSelectedProbabilityStdDev",
            "rootMutualInformation",
            "productMutualInformation",
        ],
        "boundary": [
            "modelProbability",
            "memberMeanProbability",
            "memberStdDev",
        ],
        "observability": ["profileSchemaVersion", "source", "values"],
    },
    "observability": {
        "claimScope": "existing-feature-representation-only",
        "cosineChangeRange": "zero through two; zero-to-zero is zero",
        "absoluteActivationConcentrationRange": "zero through one",
        "values": [
            "representationRms",
            "temporalDeltaRms",
            "absoluteActivationConcentration",
            "cosineChange",
        ],
        "excludedClaims": ["physical-polyphony", "physical-bass-presence"],
    },
}


FACTORIZED_UNCERTAINTY_FORMULA_SHA256 = canonical_sha256(_UNCERTAINTY_CONTRACT)


@dataclass(frozen=True, slots=True)
class FactorizedInferenceBundle:
    """One immutable inference pass containing combined and per-member logits."""

    combined_logits: Any
    member_logits: tuple[Any, ...]

    def __post_init__(self) -> None:
        if not self.member_logits:
            raise ValueError("An inference bundle requires at least one member output.")


def _validated_weights(
    values: Sequence[float],
    count: int,
) -> tuple[float, ...]:
    if len(values) != count or any(isinstance(value, bool) for value in values):
        raise ValueError("Uncertainty member weights must match the member count.")
    try:
        weights = tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError("Uncertainty member weights must be finite numbers.") from exc
    if any(not math.isfinite(value) or value < 0 for value in weights):
        raise ValueError("Uncertainty member weights must be finite and non-negative.")
    if not math.isclose(math.fsum(weights), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Uncertainty member weights must sum to one.")
    return weights


def _softmax(logits: Any, numpy: Any) -> Any:
    values = numpy.asarray(logits, dtype=numpy.float64)
    shifted = values - values.max(axis=-1, keepdims=True)
    exponent = numpy.exp(shifted)
    total = exponent.sum(axis=-1, keepdims=True)
    if not numpy.isfinite(total).all() or (total <= 0).any():
        raise ValueError("Uncertainty softmax evidence is invalid.")
    return exponent / total


def _log_softmax(logits: Any, numpy: Any) -> Any:
    probabilities = _softmax(logits, numpy)
    return numpy.log(numpy.maximum(probabilities, numpy.finfo(numpy.float64).tiny))


def _normalized_entropy(probabilities: Any, numpy: Any) -> Any:
    classes = int(probabilities.shape[-1])
    if classes <= 1:
        return numpy.zeros(probabilities.shape[:-1], dtype=numpy.float64)
    entropy = -(probabilities * numpy.log(numpy.maximum(probabilities, numpy.finfo(numpy.float64).tiny))).sum(axis=-1)
    return numpy.clip(entropy / math.log(classes), 0.0, 1.0)


def _distribution_frames(
    probabilities: Any,
    selected: Any,
    numpy: Any,
) -> dict[str, list[Any]]:
    frames = int(probabilities.shape[0])
    top_order = numpy.argsort(probabilities, axis=-1)
    top_probability = probabilities[numpy.arange(frames), top_order[:, -1]]
    second_probability = probabilities[numpy.arange(frames), top_order[:, -2]]
    selected_probability = probabilities[numpy.arange(frames), selected]
    return {
        "selectedProbability": [float(value) for value in selected_probability],
        "topProbability": [float(value) for value in top_probability],
        "margin": [float(value) for value in numpy.maximum(0.0, top_probability - second_probability)],
        "normalizedEntropy": [float(value) for value in _normalized_entropy(probabilities, numpy)],
    }


def _weighted_member_frames(
    member_probabilities: Any,
    selected: Any,
    weights: Sequence[float],
    numpy: Any,
) -> dict[str, list[Any]]:
    members, frames, classes = member_probabilities.shape
    weight_array = numpy.asarray(weights, dtype=numpy.float64)
    votes = member_probabilities.argmax(axis=-1)
    selected_probabilities = member_probabilities[
        numpy.arange(members)[:, None],
        numpy.arange(frames)[None, :],
        selected[None, :],
    ]
    selected_vote_share = numpy.zeros(frames, dtype=numpy.float64)
    pairwise_disagreement = numpy.zeros(frames, dtype=numpy.float64)
    for frame in range(frames):
        class_weights = numpy.bincount(
            votes[:, frame],
            weights=weight_array,
            minlength=classes,
        )
        selected_vote_share[frame] = class_weights[int(selected[frame])]
        selected_vote_share[frame] = numpy.clip(
            selected_vote_share[frame],
            0.0,
            1.0,
        )
        pairwise_disagreement[frame] = numpy.clip(
            1.0 - float((class_weights**2).sum()),
            0.0,
            1.0,
        )
    selected_mean = (weight_array[:, None] * selected_probabilities).sum(axis=0)
    selected_stddev = numpy.sqrt(
        numpy.maximum(
            0.0,
            (weight_array[:, None] * (selected_probabilities - selected_mean[None, :]) ** 2).sum(axis=0),
        )
    )
    mean_probabilities = (weight_array[:, None, None] * member_probabilities).sum(axis=0)
    predictive_entropy = _normalized_entropy(mean_probabilities, numpy)
    expected_entropy = (weight_array[:, None] * _normalized_entropy(member_probabilities, numpy)).sum(axis=0)
    mutual_information = numpy.clip(
        predictive_entropy - expected_entropy,
        0.0,
        1.0,
    )
    return {
        "memberVotes": [[int(value) for value in member_votes] for member_votes in votes],
        "selectedVoteShare": [float(value) for value in selected_vote_share],
        "pairwiseDisagreement": [float(value) for value in pairwise_disagreement],
        "selectedProbabilityStdDev": [float(value) for value in selected_stddev],
        "mutualInformation": [float(value) for value in mutual_information],
    }


def _conditional_joint_logits(
    joint_logits: Any,
    roots: Any,
    numpy: Any,
) -> Any:
    frames = int(joint_logits.shape[0])
    result = numpy.zeros((frames, 4), dtype=numpy.float64)
    for frame, root in enumerate(roots):
        if int(root) == 0:
            continue
        root_offset = int(root) - 1
        result[frame] = [joint_logits[frame, 1 + product * 12 + root_offset] for product in range(4)]
    return result


def _effective_product_probabilities(
    product_logits: Any,
    joint_logits: Any | None,
    roots: Any,
    blend: float,
    numpy: Any,
) -> Any:
    direct_log = _log_softmax(product_logits[:, 1:5], numpy)
    if blend == 0:
        return numpy.exp(direct_log)
    if joint_logits is None:
        raise ValueError("A nonzero uncertainty product blend requires combined joint evidence.")
    joint_log = _log_softmax(
        _conditional_joint_logits(joint_logits, roots, numpy),
        numpy,
    )
    if blend == 1:
        return numpy.exp(joint_log)
    return _softmax((1 - blend) * direct_log + blend * joint_log, numpy)


def _jensen_shannon_divergence(first: Any, second: Any, numpy: Any) -> Any:
    midpoint = 0.5 * (first + second)
    tiny = numpy.finfo(numpy.float64).tiny
    first_kl = (first * (numpy.log(numpy.maximum(first, tiny)) - numpy.log(numpy.maximum(midpoint, tiny)))).sum(axis=-1)
    second_kl = (second * (numpy.log(numpy.maximum(second, tiny)) - numpy.log(numpy.maximum(midpoint, tiny)))).sum(
        axis=-1
    )
    return numpy.clip(0.5 * (first_kl + second_kl) / math.log(2), 0.0, 1.0)


def _stable_sigmoid(logits: Any, numpy: Any) -> Any:
    values = numpy.asarray(logits, dtype=numpy.float64)
    probabilities = numpy.empty(values.shape, dtype=numpy.float64)
    nonnegative = values >= 0
    probabilities[nonnegative] = 1.0 / (1.0 + numpy.exp(-values[nonnegative]))
    negative_exponent = numpy.exp(values[~nonnegative])
    probabilities[~nonnegative] = negative_exponent / (1.0 + negative_exponent)
    return probabilities


def _observability(features: Any, numpy: Any) -> dict[str, Any]:
    values = numpy.asarray(features, dtype=numpy.float64)
    representation_rms = numpy.sqrt(numpy.mean(values**2, axis=1))
    temporal_delta_rms = numpy.zeros(len(values), dtype=numpy.float64)
    if len(values) > 1:
        temporal_delta_rms[1:] = numpy.sqrt(numpy.mean((values[1:] - values[:-1]) ** 2, axis=1))
    absolute = numpy.abs(values)
    absolute_total = absolute.sum(axis=1)
    concentration = numpy.divide(
        absolute.max(axis=1),
        absolute_total,
        out=numpy.zeros(len(values), dtype=numpy.float64),
        where=absolute_total > 0,
    )
    cosine_change = numpy.zeros(len(values), dtype=numpy.float64)
    if len(values) > 1:
        left = values[:-1]
        right = values[1:]
        denominator = numpy.linalg.norm(left, axis=1) * numpy.linalg.norm(right, axis=1)
        cosine = numpy.divide(
            (left * right).sum(axis=1),
            denominator,
            out=numpy.zeros(len(left), dtype=numpy.float64),
            where=denominator > 0,
        )
        change = numpy.clip(1.0 - cosine, 0.0, 2.0)
        both_zero = (numpy.linalg.norm(left, axis=1) == 0) & (numpy.linalg.norm(right, axis=1) == 0)
        change[both_zero] = 0.0
        cosine_change[1:] = change
    return {
        "profileSchemaVersion": "chord_existing_feature_matrix_observability_v1",
        "source": "existing-feature-matrix",
        "values": {
            "representationRms": [float(value) for value in representation_rms],
            "temporalDeltaRms": [float(value) for value in temporal_delta_rms],
            "absoluteActivationConcentration": [float(value) for value in concentration],
            "cosineChange": [float(value) for value in cosine_change],
        },
    }


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _exact_mapping(
    value: Any,
    keys: set[str],
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError(f"{label} must contain exactly the required fields.")
    return value


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _numeric_frame_array(
    value: Any,
    *,
    frames: int,
    label: str,
    minimum: float = 0.0,
    maximum: float | None = None,
    applicable: Sequence[bool] | None = None,
) -> list[float | None]:
    if not isinstance(value, list) or len(value) != frames:
        raise ValueError(f"{label} must be a frame-aligned array and must contain exactly {frames} frames.")
    result: list[float | None] = []
    for frame, item in enumerate(value):
        is_applicable = applicable is None or applicable[frame]
        if not is_applicable:
            if item is not None:
                raise ValueError(f"{label} must be null on inapplicable frames.")
            result.append(None)
            continue
        if not _finite_number(item) or float(item) < minimum or (maximum is not None and float(item) > maximum):
            raise ValueError(f"{label} contains an invalid frame value.")
        result.append(float(item))
    return result


def validate_factorized_uncertainty_contract(
    uncertainty: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the full payload and return its shared, track-independent binding."""

    if not isinstance(uncertainty, Mapping):
        raise ValueError("Factorized uncertainty must be a mapping.")
    expected_top_level = {
        "schemaVersion",
        "contractSha256",
        "referenceFree",
        "timebase",
        "binding",
        "members",
        "frames",
    }
    if "predictionCoreSha256" in uncertainty:
        expected_top_level.add("predictionCoreSha256")
    _exact_mapping(
        uncertainty,
        expected_top_level,
        "Factorized uncertainty payload",
    )
    if uncertainty.get("schemaVersion") != FACTORIZED_UNCERTAINTY_SCHEMA:
        raise ValueError("Factorized uncertainty schema is incompatible.")
    if uncertainty.get("referenceFree") is not True:
        raise ValueError("Factorized uncertainty must be explicitly reference-free.")
    binding = uncertainty.get("binding")
    members = uncertainty.get("members")
    if not isinstance(binding, Mapping) or not isinstance(members, list) or not members:
        raise ValueError("Factorized uncertainty binding and members are required.")
    _exact_mapping(
        binding,
        {
            "schemaVersion",
            "featureKind",
            "featureCount",
            "featureSpecSha256",
            "sampleRate",
            "decoderContractSha256",
            "modelOrEnsembleSha256",
            "jointProductBlend",
            "memberOrderSha256",
            "commonWeights",
            "jointContributorIndices",
            "jointContributorWeights",
        },
        "Factorized uncertainty binding",
    )
    if binding.get("schemaVersion") != FACTORIZED_UNCERTAINTY_BINDING_SCHEMA:
        raise ValueError("Factorized uncertainty binding schema is incompatible.")
    for name in (
        "featureSpecSha256",
        "decoderContractSha256",
        "modelOrEnsembleSha256",
        "memberOrderSha256",
    ):
        if not _is_sha256(binding.get(name)):
            raise ValueError(f"Factorized uncertainty binding {name} is invalid.")
    if not isinstance(binding.get("featureKind"), str) or not binding["featureKind"]:
        raise ValueError("Factorized uncertainty feature kind is invalid.")
    for name in ("featureCount", "sampleRate"):
        value = binding.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"Factorized uncertainty binding {name} is invalid.")
    blend = binding.get("jointProductBlend")
    if (
        isinstance(blend, bool)
        or not isinstance(blend, (int, float))
        or not math.isfinite(float(blend))
        or not 0 <= float(blend) <= 1
    ):
        raise ValueError("Factorized uncertainty joint product blend is invalid.")

    common_weights_raw = binding.get("commonWeights")
    if not isinstance(common_weights_raw, list):
        raise ValueError("Factorized uncertainty common weights are invalid.")
    common_weights = _validated_weights(common_weights_raw, len(members))
    joint_indices_raw = binding.get("jointContributorIndices")
    joint_weights_raw = binding.get("jointContributorWeights")
    if (
        not isinstance(joint_indices_raw, list)
        or any(isinstance(value, bool) or not isinstance(value, int) for value in joint_indices_raw)
        or not isinstance(joint_weights_raw, list)
    ):
        raise ValueError("Factorized uncertainty joint contributor binding is invalid.")
    joint_weights = _validated_weights(joint_weights_raw, len(joint_indices_raw)) if joint_indices_raw else ()
    if not joint_indices_raw and joint_weights_raw:
        raise ValueError("Legacy uncertainty cannot expose joint contributor weights.")

    expected_joint_indices: list[int] = []
    joint_weight_by_index = dict(zip(joint_indices_raw, joint_weights, strict=True))
    for index, member in enumerate(members):
        if not isinstance(member, Mapping):
            raise ValueError(f"Factorized uncertainty member {index} is invalid.")
        required_member_fields = {
            "fileName",
            "modelSha256",
            "bytes",
            "runtimeContractSha256",
            "ordinal",
            "headType",
            "commonWeight",
            "jointContributorWeight",
        }
        if not required_member_fields.issubset(member) or set(member) - (
            required_member_fields | {"architecture", "windowFrames"}
        ):
            raise ValueError(f"Factorized uncertainty member {index} fields are invalid.")
        if member.get("ordinal") != index:
            raise ValueError(f"Factorized uncertainty member {index} ordinal is invalid.")
        head_type = member.get("headType")
        if head_type not in {"legacy-90", "joint-139"}:
            raise ValueError(f"Factorized uncertainty member {index} head type is invalid.")
        if head_type == "joint-139":
            expected_joint_indices.append(index)
        common_weight = member.get("commonWeight")
        if (
            isinstance(common_weight, bool)
            or not isinstance(common_weight, (int, float))
            or float(common_weight) != common_weights[index]
        ):
            raise ValueError(f"Factorized uncertainty member {index} common weight is invalid.")
        expected_joint_weight = joint_weight_by_index.get(index)
        member_joint_weight = member.get("jointContributorWeight")
        if expected_joint_weight is None:
            if member_joint_weight is not None:
                raise ValueError(f"Factorized uncertainty member {index} joint weight is invalid.")
        elif (
            isinstance(member_joint_weight, bool)
            or not isinstance(member_joint_weight, (int, float))
            or float(member_joint_weight) != expected_joint_weight
        ):
            raise ValueError(f"Factorized uncertainty member {index} joint weight is invalid.")
        if not _is_sha256(member.get("modelSha256")) or not _is_sha256(member.get("runtimeContractSha256")):
            raise ValueError(f"Factorized uncertainty member {index} hashes are invalid.")
        if not isinstance(member.get("fileName"), str) or not member["fileName"]:
            raise ValueError(f"Factorized uncertainty member {index} file name is invalid.")
        byte_count = member.get("bytes")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count <= 0:
            raise ValueError(f"Factorized uncertainty member {index} bytes are invalid.")
        if "architecture" in member and member["architecture"] not in {
            "tcn",
            "transformer",
        }:
            raise ValueError(f"Factorized uncertainty member {index} architecture is invalid.")
        if "windowFrames" in member:
            window_frames = member["windowFrames"]
            if window_frames is not None and (
                not isinstance(window_frames, int) or isinstance(window_frames, bool) or window_frames <= 0
            ):
                raise ValueError(f"Factorized uncertainty member {index} windowFrames is invalid.")
    if joint_indices_raw != expected_joint_indices:
        raise ValueError("Factorized uncertainty joint contributor indices are invalid.")
    if expected_joint_indices:
        if len(expected_joint_indices) == len(members):
            expected_joint_weights = common_weights
        else:
            joint_mass = math.fsum(common_weights[index] for index in expected_joint_indices)
            if not math.isfinite(joint_mass) or joint_mass <= 0:
                raise ValueError("Factorized uncertainty joint contributor mass is invalid.")
            expected_joint_weights = tuple(common_weights[index] / joint_mass for index in expected_joint_indices)
            normalized_total = math.fsum(expected_joint_weights)
            expected_joint_weights = tuple(value / normalized_total for value in expected_joint_weights)
        if tuple(joint_weights) != expected_joint_weights:
            raise ValueError("Factorized uncertainty joint contributor weights are inconsistent with common weights.")
    if binding["memberOrderSha256"] != canonical_sha256(members):
        raise ValueError("Factorized uncertainty member-order hash is invalid.")
    expected_contract_sha256 = canonical_sha256(
        {
            "formulaContract": _UNCERTAINTY_CONTRACT,
            "binding": dict(binding),
            "members": members,
        }
    )
    if uncertainty.get("contractSha256") != expected_contract_sha256:
        raise ValueError("Factorized uncertainty contract hash is invalid.")
    prediction_core_sha256 = uncertainty.get("predictionCoreSha256")
    if prediction_core_sha256 is not None and not _is_sha256(prediction_core_sha256):
        raise ValueError("Factorized uncertainty prediction-core hash is invalid.")

    timebase = _exact_mapping(
        uncertainty.get("timebase"),
        {
            "frameSeconds",
            "frameCount",
            "durationSeconds",
            "timestampConvention",
        },
        "Factorized uncertainty timebase",
    )
    frame_seconds = timebase["frameSeconds"]
    frame_count = timebase["frameCount"]
    duration_seconds = timebase["durationSeconds"]
    if not _finite_number(frame_seconds) or float(frame_seconds) != 0.1:
        raise ValueError("Factorized uncertainty frameSeconds must be exactly 0.1.")
    if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count <= 0:
        raise ValueError("Factorized uncertainty frameCount is invalid.")
    if not _finite_number(duration_seconds) or float(duration_seconds) <= 0:
        raise ValueError("Factorized uncertainty durationSeconds is invalid.")
    if frame_count != math.ceil(float(duration_seconds) / float(frame_seconds)):
        raise ValueError(
            "Factorized uncertainty frameCount must equal "
            "ceil(durationSeconds / frameSeconds); frameCount does not match the "
            "timebase."
        )
    if timebase["timestampConvention"] != "left-edge":
        raise ValueError("Factorized uncertainty timestamp convention is invalid.")

    frames = _exact_mapping(
        uncertainty.get("frames"),
        {"root", "product", "ensemble", "boundary", "observability"},
        "Factorized uncertainty frames",
    )
    root = _exact_mapping(
        frames["root"],
        {
            "selectedClass",
            "selectedProbability",
            "topProbability",
            "margin",
            "normalizedEntropy",
        },
        "Factorized uncertainty root frames",
    )
    root_selected = root["selectedClass"]
    if (
        not isinstance(root_selected, list)
        or len(root_selected) != frame_count
        or any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 12 for value in root_selected)
    ):
        raise ValueError("Factorized uncertainty root selectedClass is invalid.")
    root_selected_probability = _numeric_frame_array(
        root["selectedProbability"],
        frames=frame_count,
        label="Factorized uncertainty root selectedProbability",
        maximum=1.0,
    )
    root_top_probability = _numeric_frame_array(
        root["topProbability"],
        frames=frame_count,
        label="Factorized uncertainty root topProbability",
        maximum=1.0,
    )
    root_margin = _numeric_frame_array(
        root["margin"],
        frames=frame_count,
        label="Factorized uncertainty root margin",
        maximum=1.0,
    )
    _numeric_frame_array(
        root["normalizedEntropy"],
        frames=frame_count,
        label="Factorized uncertainty root normalizedEntropy",
        maximum=1.0,
    )
    if any(
        selected is None or top is None or margin is None or selected > top + 1e-12 or margin > top + 1e-12
        for selected, top, margin in zip(
            root_selected_probability,
            root_top_probability,
            root_margin,
            strict=True,
        )
    ):
        raise ValueError("Factorized uncertainty root probabilities are inconsistent.")

    product = _exact_mapping(
        frames["product"],
        {
            "applicable",
            "selectedClass",
            "selectedProbability",
            "topProbability",
            "margin",
            "normalizedEntropy",
            "directJointAgreement",
            "directJointJensenShannon",
        },
        "Factorized uncertainty product frames",
    )
    applicable = product["applicable"]
    if (
        not isinstance(applicable, list)
        or len(applicable) != frame_count
        or any(not isinstance(value, bool) for value in applicable)
        or applicable != [value != 0 for value in root_selected]
    ):
        raise ValueError("Factorized uncertainty product applicability is invalid.")
    product_selected = product["selectedClass"]
    if not isinstance(product_selected, list) or len(product_selected) != frame_count:
        raise ValueError("Factorized uncertainty product selectedClass is invalid.")
    for frame, value in enumerate(product_selected):
        if applicable[frame]:
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 4:
                raise ValueError(
                    "Factorized uncertainty product selectedClass must be numeric "
                    "exactly when product is applicable; product selectedClass is invalid."
                )
        elif value is not None:
            raise ValueError(
                "Factorized uncertainty product selectedClass must be numeric exactly "
                "when product is applicable; product selectedClass is invalid."
            )
    product_selected_probability = _numeric_frame_array(
        product["selectedProbability"],
        frames=frame_count,
        label="Factorized uncertainty product selectedProbability",
        maximum=1.0,
        applicable=applicable,
    )
    product_top_probability = _numeric_frame_array(
        product["topProbability"],
        frames=frame_count,
        label="Factorized uncertainty product topProbability",
        maximum=1.0,
        applicable=applicable,
    )
    product_margin = _numeric_frame_array(
        product["margin"],
        frames=frame_count,
        label="Factorized uncertainty product margin",
        maximum=1.0,
        applicable=applicable,
    )
    _numeric_frame_array(
        product["normalizedEntropy"],
        frames=frame_count,
        label="Factorized uncertainty product normalizedEntropy",
        maximum=1.0,
        applicable=applicable,
    )
    if any(
        applicable[frame]
        and (
            product_selected_probability[frame] > product_top_probability[frame] + 1e-12
            or product_margin[frame] > product_top_probability[frame] + 1e-12
        )
        for frame in range(frame_count)
    ):
        raise ValueError("Factorized uncertainty product probabilities are inconsistent.")
    joint_applicable = [bool(joint_indices_raw) and value for value in applicable]
    direct_joint_agreement = product["directJointAgreement"]
    if not isinstance(direct_joint_agreement, list) or len(direct_joint_agreement) != frame_count:
        raise ValueError("Factorized uncertainty direct/joint agreement is invalid.")
    for frame, value in enumerate(direct_joint_agreement):
        if joint_applicable[frame]:
            if not isinstance(value, bool):
                raise ValueError("Factorized uncertainty direct/joint agreement is invalid.")
        elif value is not None:
            raise ValueError("Factorized uncertainty direct/joint agreement must be null without joint evidence.")
    _numeric_frame_array(
        product["directJointJensenShannon"],
        frames=frame_count,
        label="Factorized uncertainty direct/joint Jensen-Shannon divergence",
        maximum=1.0,
        applicable=joint_applicable,
    )

    ensemble = _exact_mapping(
        frames["ensemble"],
        {
            "memberRootVote",
            "memberProductVote",
            "rootSelectedVoteShare",
            "productSelectedVoteShare",
            "rootPairwiseDisagreement",
            "productPairwiseDisagreement",
            "rootSelectedProbabilityStdDev",
            "productSelectedProbabilityStdDev",
            "rootMutualInformation",
            "productMutualInformation",
        },
        "Factorized uncertainty ensemble frames",
    )
    member_root_vote = ensemble["memberRootVote"]
    member_product_vote = ensemble["memberProductVote"]
    if (
        not isinstance(member_root_vote, list)
        or len(member_root_vote) != len(members)
        or not isinstance(member_product_vote, list)
        or len(member_product_vote) != len(members)
    ):
        raise ValueError(
            "Factorized uncertainty member vote matrices must contain exactly "
            f"{len(members)} member rows; member vote matrices are invalid."
        )
    for member_index, (root_votes, product_votes) in enumerate(zip(member_root_vote, member_product_vote, strict=True)):
        if (
            not isinstance(root_votes, list)
            or len(root_votes) != frame_count
            or any(
                not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 12 for value in root_votes
            )
        ):
            raise ValueError(f"Factorized uncertainty member {member_index} root votes are invalid.")
        if not isinstance(product_votes, list) or len(product_votes) != frame_count:
            raise ValueError(f"Factorized uncertainty member {member_index} product votes are invalid.")
        for frame, value in enumerate(product_votes):
            if applicable[frame]:
                if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 4:
                    raise ValueError(f"Factorized uncertainty member {member_index} product votes are invalid.")
            elif value is not None:
                raise ValueError(
                    f"Factorized uncertainty member {member_index} product votes must be null on no-chord frames."
                )
    root_selected_vote_share = _numeric_frame_array(
        ensemble["rootSelectedVoteShare"],
        frames=frame_count,
        label="Factorized uncertainty root selected vote share",
        maximum=1.0,
    )
    product_selected_vote_share = _numeric_frame_array(
        ensemble["productSelectedVoteShare"],
        frames=frame_count,
        label="Factorized uncertainty product selected vote share",
        maximum=1.0,
        applicable=applicable,
    )
    root_pairwise = _numeric_frame_array(
        ensemble["rootPairwiseDisagreement"],
        frames=frame_count,
        label="Factorized uncertainty root pairwise disagreement",
        maximum=1.0,
    )
    product_pairwise = _numeric_frame_array(
        ensemble["productPairwiseDisagreement"],
        frames=frame_count,
        label="Factorized uncertainty product pairwise disagreement",
        maximum=1.0,
        applicable=applicable,
    )
    _numeric_frame_array(
        ensemble["rootSelectedProbabilityStdDev"],
        frames=frame_count,
        label="Factorized uncertainty root selected-probability stddev",
        maximum=0.5,
    )
    _numeric_frame_array(
        ensemble["productSelectedProbabilityStdDev"],
        frames=frame_count,
        label="Factorized uncertainty product selected-probability stddev",
        maximum=0.5,
        applicable=applicable,
    )
    _numeric_frame_array(
        ensemble["rootMutualInformation"],
        frames=frame_count,
        label="Factorized uncertainty root mutual information",
        maximum=1.0,
    )
    _numeric_frame_array(
        ensemble["productMutualInformation"],
        frames=frame_count,
        label="Factorized uncertainty product mutual information",
        maximum=1.0,
        applicable=applicable,
    )
    for frame in range(frame_count):
        root_mass = [0.0] * 13
        product_mass = [0.0] * 4
        for member_index, weight in enumerate(common_weights):
            root_mass[member_root_vote[member_index][frame]] += weight
            if applicable[frame]:
                product_mass[member_product_vote[member_index][frame] - 1] += weight
        expected_root_share = min(1.0, max(0.0, root_mass[root_selected[frame]]))
        expected_root_pairwise = min(
            1.0,
            max(0.0, 1.0 - math.fsum(value**2 for value in root_mass)),
        )
        if not math.isclose(
            root_selected_vote_share[frame],
            expected_root_share,
            rel_tol=0,
            abs_tol=1e-12,
        ) or not math.isclose(
            root_pairwise[frame],
            expected_root_pairwise,
            rel_tol=0,
            abs_tol=1e-12,
        ):
            raise ValueError("Factorized uncertainty root vote statistics are invalid.")
        if applicable[frame]:
            expected_product_share = min(
                1.0,
                max(0.0, product_mass[product_selected[frame] - 1]),
            )
            expected_product_pairwise = min(
                1.0,
                max(0.0, 1.0 - math.fsum(value**2 for value in product_mass)),
            )
            if not math.isclose(
                product_selected_vote_share[frame],
                expected_product_share,
                rel_tol=0,
                abs_tol=1e-12,
            ) or not math.isclose(
                product_pairwise[frame],
                expected_product_pairwise,
                rel_tol=0,
                abs_tol=1e-12,
            ):
                raise ValueError("Factorized uncertainty product vote statistics are invalid.")

    boundary = _exact_mapping(
        frames["boundary"],
        {"modelProbability", "memberMeanProbability", "memberStdDev"},
        "Factorized uncertainty boundary frames",
    )
    _numeric_frame_array(
        boundary["modelProbability"],
        frames=frame_count,
        label="Factorized uncertainty boundary model probability",
        maximum=1.0,
    )
    _numeric_frame_array(
        boundary["memberMeanProbability"],
        frames=frame_count,
        label="Factorized uncertainty boundary member mean probability",
        maximum=1.0,
    )
    _numeric_frame_array(
        boundary["memberStdDev"],
        frames=frame_count,
        label="Factorized uncertainty boundary member stddev",
        maximum=0.5,
    )

    observability = _exact_mapping(
        frames["observability"],
        {"profileSchemaVersion", "source", "values"},
        "Factorized uncertainty observability",
    )
    if (
        observability["profileSchemaVersion"] != "chord_existing_feature_matrix_observability_v1"
        or observability["source"] != "existing-feature-matrix"
    ):
        raise ValueError("Factorized uncertainty observability profile is invalid.")
    observability_values = _exact_mapping(
        observability["values"],
        {
            "representationRms",
            "temporalDeltaRms",
            "absoluteActivationConcentration",
            "cosineChange",
        },
        "Factorized uncertainty observability values",
    )
    _numeric_frame_array(
        observability_values["representationRms"],
        frames=frame_count,
        label="Factorized uncertainty representation RMS",
    )
    temporal_delta = _numeric_frame_array(
        observability_values["temporalDeltaRms"],
        frames=frame_count,
        label="Factorized uncertainty temporal-delta RMS",
    )
    _numeric_frame_array(
        observability_values["absoluteActivationConcentration"],
        frames=frame_count,
        label="Factorized uncertainty absolute-activation concentration",
        maximum=1.0,
    )
    cosine_change = _numeric_frame_array(
        observability_values["cosineChange"],
        frames=frame_count,
        label="Factorized uncertainty cosine change",
        maximum=2.0,
    )
    if temporal_delta[0] != 0.0 or cosine_change[0] != 0.0:
        raise ValueError("Factorized uncertainty observability deltas must start at zero.")
    return json.loads(json.dumps(dict(binding), ensure_ascii=False, allow_nan=False))


def build_factorized_uncertainty(
    *,
    numpy: Any,
    features: Any,
    duration_seconds: float,
    frame_seconds: float,
    feature_kind: str,
    feature_count: int,
    feature_spec_sha256: str | None,
    sample_rate: int,
    decoder_contract_sha256: str,
    model_or_ensemble_sha256: str,
    combined_heads: Mapping[str, Any],
    member_heads: Sequence[Mapping[str, Any]],
    member_head_types: Sequence[str],
    member_identities: Sequence[Mapping[str, Any]],
    common_weights: Sequence[float],
    joint_contributor_indices: Sequence[int],
    joint_contributor_weights: Sequence[float],
    joint_product_blend: float,
    final_roots: Sequence[int],
    final_products: Sequence[int],
) -> dict[str, Any]:
    """Build deterministic frame telemetry from one completed inference pass."""

    feature_array = numpy.asarray(features)
    if (
        feature_array.ndim != 2
        or feature_array.shape[0] <= 0
        or feature_array.dtype.kind not in {"f", "i", "u"}
        or not numpy.isfinite(feature_array).all()
    ):
        raise ValueError("Uncertainty features must be a non-empty finite matrix.")
    if (
        isinstance(duration_seconds, bool)
        or not math.isfinite(float(duration_seconds))
        or float(duration_seconds) <= 0
        or isinstance(frame_seconds, bool)
        or not math.isfinite(float(frame_seconds))
        or float(frame_seconds) <= 0
    ):
        raise ValueError("Uncertainty duration and frame step must be positive and finite.")
    if not isinstance(feature_kind, str) or not feature_kind:
        raise ValueError("Uncertainty feature kind is required.")
    if not isinstance(sample_rate, int) or isinstance(sample_rate, bool) or sample_rate <= 0:
        raise ValueError("Uncertainty sample rate must be a positive integer.")
    frames = int(feature_array.shape[0])
    expected_frames = int(math.ceil(float(duration_seconds) / float(frame_seconds)))
    if frames != expected_frames:
        raise ValueError("Uncertainty frame count must equal ceil(durationSeconds / frameSeconds).")
    if (
        not isinstance(feature_count, int)
        or isinstance(feature_count, bool)
        or feature_count <= 0
        or feature_count != int(feature_array.shape[1])
    ):
        raise ValueError("Uncertainty feature count does not match the feature matrix.")
    for name, value in (
        ("featureSpecSha256", feature_spec_sha256),
        ("decoderContractSha256", decoder_contract_sha256),
        ("modelOrEnsembleSha256", model_or_ensemble_sha256),
    ):
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"Uncertainty {name} must be a lowercase SHA-256.")
    if len(member_heads) != len(member_head_types) or len(member_heads) != len(member_identities):
        raise ValueError("Uncertainty member contracts have inconsistent lengths.")
    weights = _validated_weights(common_weights, len(member_heads))
    if len(final_roots) != frames or len(final_products) != frames:
        raise ValueError("Uncertainty decoded paths must match the feature frame count.")
    roots = numpy.asarray(final_roots, dtype=numpy.int64)
    products = numpy.asarray(final_products, dtype=numpy.int64)
    if ((roots < 0) | (roots > 12)).any() or ((products < 0) | (products > 4)).any():
        raise ValueError("Uncertainty decoded paths contain invalid classes.")
    if ((roots == 0) != (products == 0)).any():
        raise ValueError("No-chord root/product uncertainty paths must agree.")
    if isinstance(joint_product_blend, bool):
        raise ValueError("Uncertainty joint product blend must be from zero to one.")
    blend = float(joint_product_blend)
    if not math.isfinite(blend) or not 0 <= blend <= 1:
        raise ValueError("Uncertainty joint product blend must be from zero to one.")

    allowed_head_types = {"legacy-90", "joint-139"}
    if any(value not in allowed_head_types for value in member_head_types):
        raise ValueError("Uncertainty member head types are invalid.")
    expected_joint_indices = [
        index for index, member_type in enumerate(member_head_types) if member_type == "joint-139"
    ]
    if (
        any(isinstance(value, bool) for value in joint_contributor_indices)
        or [int(value) for value in joint_contributor_indices] != expected_joint_indices
    ):
        raise ValueError("Uncertainty joint contributor indices are incompatible.")
    if expected_joint_indices:
        _validated_weights(
            joint_contributor_weights,
            len(expected_joint_indices),
        )
    elif joint_contributor_weights:
        raise ValueError("Legacy uncertainty cannot expose joint contributor weights.")
    required_heads = {"root", "product", "boundary"}
    for index, (heads, member_type) in enumerate(zip(member_heads, member_head_types, strict=True)):
        if not required_heads.issubset(heads):
            raise ValueError(f"Uncertainty member {index} is missing a required head.")
        if ("joint_root_product" in heads) != (member_type == "joint-139"):
            raise ValueError(f"Uncertainty member {index} contradicts its head type.")
        expected_shapes = {
            "root": (frames, 13),
            "product": (frames, 5),
            "boundary": (frames, 1),
        }
        for name, shape in expected_shapes.items():
            value = numpy.asarray(heads[name])
            if value.shape != shape or value.dtype.kind != "f" or not numpy.isfinite(value).all():
                raise ValueError(f"Uncertainty member {index} has invalid {name} logits.")
        if member_type == "joint-139":
            joint = numpy.asarray(heads["joint_root_product"])
            if joint.shape != (frames, 49) or joint.dtype.kind != "f" or not numpy.isfinite(joint).all():
                raise ValueError(f"Uncertainty member {index} has invalid joint logits.")
    for name, shape in {
        "root": (frames, 13),
        "product": (frames, 5),
        "boundary": (frames, 1),
    }.items():
        value = numpy.asarray(combined_heads.get(name))
        if value.shape != shape or value.dtype.kind != "f" or not numpy.isfinite(value).all():
            raise ValueError(f"Uncertainty combined {name} logits are invalid.")
    combined_joint = combined_heads.get("joint_root_product")
    if (combined_joint is not None) != bool(expected_joint_indices):
        raise ValueError(
            "Uncertainty combined joint evidence must be present exactly when joint contributors are present."
        )
    if combined_joint is not None:
        combined_joint = numpy.asarray(combined_joint)
        if (
            combined_joint.shape != (frames, 49)
            or combined_joint.dtype.kind != "f"
            or not numpy.isfinite(combined_joint).all()
        ):
            raise ValueError("Uncertainty combined joint logits are invalid.")

    root_probabilities = _softmax(combined_heads["root"], numpy)
    member_root_probabilities = numpy.stack(
        [_softmax(heads["root"], numpy) for heads in member_heads],
        axis=0,
    )
    root_member_frames = _weighted_member_frames(
        member_root_probabilities,
        roots,
        weights,
        numpy,
    )
    root_frames = {
        "selectedClass": [int(value) for value in roots],
        **_distribution_frames(root_probabilities, roots, numpy),
    }

    combined_product_probabilities = _effective_product_probabilities(
        combined_heads["product"],
        combined_joint,
        roots,
        blend,
        numpy,
    )
    member_product_probabilities = numpy.stack(
        [
            _effective_product_probabilities(
                heads["product"],
                heads.get("joint_root_product"),
                roots,
                blend if member_type == "joint-139" else 0.0,
                numpy,
            )
            for heads, member_type in zip(
                member_heads,
                member_head_types,
                strict=True,
            )
        ],
        axis=0,
    )
    product_selected = numpy.maximum(0, products - 1)
    combined_product_frames = _distribution_frames(
        combined_product_probabilities,
        product_selected,
        numpy,
    )
    member_product_frames = _weighted_member_frames(
        member_product_probabilities,
        product_selected,
        weights,
        numpy,
    )
    pitched = roots != 0
    direct_joint_agreement: list[bool | None] = [None] * frames
    direct_joint_jsd: list[float | None] = [None] * frames
    if combined_joint is not None:
        direct_probabilities = _softmax(combined_heads["product"][:, 1:5], numpy)
        joint_probabilities = _softmax(
            _conditional_joint_logits(combined_joint, roots, numpy),
            numpy,
        )
        jsd = _jensen_shannon_divergence(
            direct_probabilities,
            joint_probabilities,
            numpy,
        )
        for frame in range(frames):
            if pitched[frame]:
                direct_joint_agreement[frame] = bool(
                    direct_probabilities[frame].argmax() == joint_probabilities[frame].argmax()
                )
                direct_joint_jsd[frame] = float(jsd[frame])

    product_frames: dict[str, list[Any]] = {
        "applicable": [bool(value) for value in pitched],
        "selectedClass": [int(value) if pitched[index] else None for index, value in enumerate(products)],
        "directJointAgreement": direct_joint_agreement,
        "directJointJensenShannon": direct_joint_jsd,
    }
    for name, values in combined_product_frames.items():
        product_frames[name] = [value if pitched[index] else None for index, value in enumerate(values)]
    member_product_vote = [
        [value + 1 if pitched[frame] else None for frame, value in enumerate(member_votes)]
        for member_votes in member_product_frames["memberVotes"]
    ]
    ensemble_frames = {
        "memberRootVote": root_member_frames["memberVotes"],
        "memberProductVote": member_product_vote,
        "rootSelectedVoteShare": root_member_frames["selectedVoteShare"],
        "productSelectedVoteShare": [
            value if pitched[index] else None for index, value in enumerate(member_product_frames["selectedVoteShare"])
        ],
        "rootPairwiseDisagreement": root_member_frames["pairwiseDisagreement"],
        "productPairwiseDisagreement": [
            value if pitched[index] else None
            for index, value in enumerate(member_product_frames["pairwiseDisagreement"])
        ],
        "rootSelectedProbabilityStdDev": root_member_frames["selectedProbabilityStdDev"],
        "productSelectedProbabilityStdDev": [
            value if pitched[index] else None
            for index, value in enumerate(member_product_frames["selectedProbabilityStdDev"])
        ],
        "rootMutualInformation": root_member_frames["mutualInformation"],
        "productMutualInformation": [
            value if pitched[index] else None for index, value in enumerate(member_product_frames["mutualInformation"])
        ],
    }

    combined_boundary = _stable_sigmoid(
        numpy.asarray(combined_heads["boundary"])[:, 0],
        numpy,
    )
    member_boundary = numpy.stack(
        [_stable_sigmoid(numpy.asarray(heads["boundary"])[:, 0], numpy) for heads in member_heads],
        axis=0,
    )
    weight_array = numpy.asarray(weights, dtype=numpy.float64)
    member_boundary_mean = (weight_array[:, None] * member_boundary).sum(axis=0)
    member_boundary_stddev = numpy.sqrt(
        numpy.maximum(
            0.0,
            (weight_array[:, None] * (member_boundary - member_boundary_mean[None, :]) ** 2).sum(axis=0),
        )
    )

    members: list[dict[str, Any]] = []
    joint_weight_by_index = {
        int(index): float(weight)
        for index, weight in zip(
            joint_contributor_indices,
            joint_contributor_weights,
            strict=True,
        )
    }
    for index, (identity, member_type, common_weight) in enumerate(
        zip(member_identities, member_head_types, weights, strict=True)
    ):
        model_sha256 = identity.get("modelSha256")
        runtime_sha256 = identity.get("runtimeContractSha256")
        for name, value in (
            ("modelSha256", model_sha256),
            ("runtimeContractSha256", runtime_sha256),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ValueError(f"Uncertainty member {index} {name} must be a lowercase SHA-256.")
        byte_count = identity.get("bytes")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count <= 0:
            raise ValueError(f"Uncertainty member {index} bytes are invalid.")
        file_name = identity.get("fileName")
        if not isinstance(file_name, str) or not file_name:
            raise ValueError(f"Uncertainty member {index} fileName is invalid.")
        members.append(
            {
                **json.loads(json.dumps(dict(identity), allow_nan=False)),
                "ordinal": index,
                "headType": member_type,
                "commonWeight": float(common_weight),
                "jointContributorWeight": joint_weight_by_index.get(index),
            }
        )
    member_order_sha256 = canonical_sha256(members)
    binding = {
        "schemaVersion": FACTORIZED_UNCERTAINTY_BINDING_SCHEMA,
        "featureKind": feature_kind,
        "featureCount": int(feature_count),
        "featureSpecSha256": feature_spec_sha256,
        "sampleRate": int(sample_rate),
        "decoderContractSha256": decoder_contract_sha256,
        "modelOrEnsembleSha256": model_or_ensemble_sha256,
        "jointProductBlend": blend,
        "memberOrderSha256": member_order_sha256,
        "commonWeights": [float(value) for value in weights],
        "jointContributorIndices": [int(value) for value in joint_contributor_indices],
        "jointContributorWeights": [float(value) for value in joint_contributor_weights],
    }
    uncertainty = {
        "schemaVersion": FACTORIZED_UNCERTAINTY_SCHEMA,
        "contractSha256": canonical_sha256(
            {
                "formulaContract": _UNCERTAINTY_CONTRACT,
                "binding": binding,
                "members": members,
            }
        ),
        "referenceFree": True,
        "timebase": {
            "frameSeconds": float(frame_seconds),
            "frameCount": frames,
            "durationSeconds": float(duration_seconds),
            "timestampConvention": "left-edge",
        },
        "binding": binding,
        "members": members,
        "frames": {
            "root": root_frames,
            "product": product_frames,
            "ensemble": ensemble_frames,
            "boundary": {
                "modelProbability": [float(value) for value in combined_boundary],
                "memberMeanProbability": [float(value) for value in member_boundary_mean],
                "memberStdDev": [float(value) for value in member_boundary_stddev],
            },
            "observability": _observability(feature_array, numpy),
        },
    }
    validate_factorized_uncertainty_contract(uncertainty)
    return uncertainty


def attach_uncertainty(
    prediction: Mapping[str, Any],
    uncertainty: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach telemetry with two acyclic canonical hashes."""

    if any(name in prediction for name in ("uncertainty", "predictionCoreSha256", "uncertaintySha256")):
        raise ValueError("Prediction already contains uncertainty hash fields.")
    validate_factorized_uncertainty_contract(uncertainty)
    result = dict(prediction)
    prediction_core_sha256 = canonical_sha256(result)
    uncertainty_value = json.loads(json.dumps(dict(uncertainty), allow_nan=False))
    binding = uncertainty_value.get("binding")
    if not isinstance(binding, dict):
        raise ValueError("Uncertainty binding is missing.")
    if "predictionCoreSha256" in uncertainty_value:
        raise ValueError("Uncertainty already contains a prediction-core hash.")
    uncertainty_value["predictionCoreSha256"] = prediction_core_sha256
    uncertainty_sha256 = canonical_sha256(uncertainty_value)
    result["uncertainty"] = uncertainty_value
    result["predictionCoreSha256"] = prediction_core_sha256
    result["uncertaintySha256"] = uncertainty_sha256
    return result
