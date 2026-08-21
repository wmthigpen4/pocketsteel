"""Reference-free bar summaries for factorized chord uncertainty.

The summarizer in this module deliberately has no reference argument.  It
combines a hash-bound ``chord_factorized_uncertainty_v1`` prediction with an
explicit bar grid and emits only prediction-derived selector features.  Chord
confidence is integrated over the portions of frames assigned to the winning
predicted product; boundary and representation observability are integrated
over the complete bar.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Any

from .bar_promotion import canonical_sha256
from .labels import PITCH_CLASS, SHARP_NAMES, ChordLabel, normalize_chord
from .uncertainty import validate_factorized_uncertainty_contract


FACTORIZED_UNCERTAINTY_SCHEMA = "chord_factorized_uncertainty_v1"
BAR_UNCERTAINTY_SCHEMA = "chord_prediction_bar_uncertainty_v1"
BAR_FEATURE_SCHEMA = "chord_prediction_bar_uncertainty_features_v1"
EXPLICIT_BAR_GRID_SCHEMA = "chord_explicit_bar_grid_v1"
FRAME_SECONDS = 0.1

_EPSILON = 1e-9
_SHA256_HEX = frozenset("0123456789abcdef")
_TIMING_SOURCE_CLASSES = frozenset({"runtime"})
_OBSERVABILITY_FIELDS = (
    "representationRms",
    "temporalDeltaRms",
    "absoluteActivationConcentration",
    "cosineChange",
)

BAR_FEATURE_NAMES = (
    "predictionCoverage",
    "predictionDominance",
    "predictionTransitionCount",
    "productFamilyNone",
    "productFamilyMajor",
    "productFamilyMinor",
    "productFamilyDominant",
    "productFamilyMinorSeventh",
    "rootSelectedProbabilityMean",
    "rootSelectedProbabilityMinimum",
    "rootMarginMean",
    "rootMarginMinimum",
    "rootNormalizedEntropyMean",
    "rootNormalizedEntropyMaximum",
    "productSelectedProbabilityMean",
    "productSelectedProbabilityMinimum",
    "productMarginMean",
    "productMarginMinimum",
    "productNormalizedEntropyMean",
    "productNormalizedEntropyMaximum",
    "rootSelectedVoteShareMean",
    "rootSelectedVoteShareMinimum",
    "productSelectedVoteShareMean",
    "productSelectedVoteShareMinimum",
    "rootPairwiseDisagreementMean",
    "rootPairwiseDisagreementMaximum",
    "productPairwiseDisagreementMean",
    "productPairwiseDisagreementMaximum",
    "rootSelectedProbabilityStdDevMean",
    "rootSelectedProbabilityStdDevMaximum",
    "productSelectedProbabilityStdDevMean",
    "productSelectedProbabilityStdDevMaximum",
    "rootMutualInformationMean",
    "rootMutualInformationMaximum",
    "productMutualInformationMean",
    "productMutualInformationMaximum",
    "boundaryModelProbabilityMean",
    "boundaryModelProbabilityMaximum",
    "boundaryStartEdgeProbability",
    "boundaryEndEdgeProbability",
    "representationRmsMean",
    "representationRmsMaximum",
    "temporalDeltaRmsMean",
    "temporalDeltaRmsMaximum",
    "absoluteActivationConcentrationMean",
    "absoluteActivationConcentrationMaximum",
    "cosineChangeMean",
    "cosineChangeMaximum",
)

_BAR_FEATURE_CONTRACT = {
    "schemaVersion": BAR_FEATURE_SCHEMA,
    "sourceSchemaVersion": FACTORIZED_UNCERTAINTY_SCHEMA,
    "frameTimebase": {
        "frameSeconds": FRAME_SECONDS,
        "timestampConvention": "left-edge",
        "finalFrame": "truncated-to-prediction-duration",
        "timeEpsilonSeconds": _EPSILON,
        "predictionSegmentBoundaries": "frame-aligned except final duration",
    },
    "timingDurationAlignment": {
        "timingSource": "runtime-only explicit bar grid",
        "runtimeDuration": "Math.round(decoded AudioBuffer duration * 1000) / 1000",
        "predictionDuration": "full-precision frozen feature-cache duration",
        "requiredRelation": (
            "timingDurationSeconds == floor(predictionDurationSeconds*1000 + 0.5)/1000"
        ),
        "barEnd": "full-precision prediction duration",
    },
    "winningProductScope": (
        "root, product, and ensemble evidence is weighted by exact overlap "
        "with decoded intervals assigned to the bar's winning predicted product"
    ),
    "fullBarScope": (
        "boundary and representation observability is weighted by exact "
        "frame-to-bar overlap independent of predicted coverage"
    ),
    "mean": "sum(value * overlapSeconds) / sum(overlapSeconds)",
    "extrema": "minimum or maximum over frames with positive eligible overlap",
    "transitionCount": (
        "product changes between consecutive decoded prediction segments "
        "having positive overlap with the bar; gaps do not add transitions"
    ),
    "tieBreak": ("largest predicted-product duration within timeEpsilonSeconds, then lexical product symbol"),
    "missingValue": "JSON null when no applicable positive-overlap frame exists",
    "boundaryEdgeSampling": (
        "nearest model boundary sample to the bar edge; exact half-frame ties choose "
        "the later sample; an edge at or beyond frameCount is JSON null"
    ),
    "featureNames": list(BAR_FEATURE_NAMES),
}


def _canonical_sha256(value: Any) -> str:
    try:
        return canonical_sha256(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Bar uncertainty input is not canonical JSON: {exc}") from exc


BAR_FEATURE_CONTRACT_SHA256 = _canonical_sha256(_BAR_FEATURE_CONTRACT)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _SHA256_HEX


def _required_sha256(value: Any, name: str) -> str:
    if not _is_sha256(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest.")
    return str(value)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise ValueError(f"{name} fields do not match the frozen schema: missing={missing}, extra={extra}.")


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be a sequence.")
    return value


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def _positive_number(value: Any, name: str) -> float:
    result = _finite_number(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive.")
    return result


def _strict_int(value: Any, name: str, *, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    if value < minimum or (maximum is not None and value > maximum):
        suffix = f" through {maximum}" if maximum is not None else " or greater"
        raise ValueError(f"{name} must be {minimum}{suffix}.")
    return value


def _numeric_array(
    value: Any,
    name: str,
    frame_count: int,
    *,
    minimum: float | None = 0.0,
    maximum: float | None = 1.0,
    nullable: bool = False,
) -> list[float | None]:
    values = _sequence(value, name)
    if len(values) != frame_count:
        raise ValueError(f"{name} must contain exactly {frame_count} frames.")
    output: list[float | None] = []
    for index, item in enumerate(values):
        if item is None and nullable:
            output.append(None)
            continue
        number = _finite_number(item, f"{name}[{index}]")
        if minimum is not None and number < minimum - _EPSILON:
            raise ValueError(f"{name}[{index}] is below {minimum}.")
        if maximum is not None and number > maximum + _EPSILON:
            raise ValueError(f"{name}[{index}] is above {maximum}.")
        output.append(number)
    return output


def _boolean_array(value: Any, name: str, frame_count: int, *, nullable: bool = False) -> list[bool | None]:
    values = _sequence(value, name)
    if len(values) != frame_count:
        raise ValueError(f"{name} must contain exactly {frame_count} frames.")
    output: list[bool | None] = []
    for index, item in enumerate(values):
        if item is None and nullable:
            output.append(None)
        elif isinstance(item, bool):
            output.append(item)
        else:
            raise ValueError(f"{name}[{index}] must be a boolean{', null' if nullable else ''}.")
    return output


def _class_array(
    value: Any,
    name: str,
    frame_count: int,
    *,
    minimum: int,
    maximum: int,
    nullable: bool = False,
) -> list[int | None]:
    values = _sequence(value, name)
    if len(values) != frame_count:
        raise ValueError(f"{name} must contain exactly {frame_count} frames.")
    output: list[int | None] = []
    for index, item in enumerate(values):
        if item is None and nullable:
            output.append(None)
            continue
        output.append(_strict_int(item, f"{name}[{index}]", minimum=minimum, maximum=maximum))
    return output


def _member_vote_matrix(
    value: Any,
    name: str,
    member_count: int,
    frame_count: int,
    *,
    minimum: int,
    maximum: int,
    nullable: bool,
) -> list[list[int | None]]:
    rows = _sequence(value, name)
    if len(rows) != member_count:
        raise ValueError(f"{name} must contain exactly {member_count} member rows.")
    return [
        _class_array(
            row,
            f"{name}[{member_index}]",
            frame_count,
            minimum=minimum,
            maximum=maximum,
            nullable=nullable,
        )
        for member_index, row in enumerate(rows)
    ]


def _canonical_product(label: ChordLabel) -> str:
    if label.root is None:
        return label.product_symbol
    suffix = label.product_symbol[len(label.root) :]
    return f"{SHARP_NAMES[PITCH_CLASS[label.root]]}{suffix}"


def _prediction_segments(prediction: Mapping[str, Any], duration: float) -> list[dict[str, Any]]:
    raw_segments = _sequence(prediction.get("segments"), "prediction.segments")
    segments: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_segments):
        item = _mapping(raw, f"prediction.segments[{index}]")
        start = _finite_number(item.get("start"), f"prediction.segments[{index}].start")
        end = _finite_number(item.get("end"), f"prediction.segments[{index}].end")
        if start < 0 or end <= start or end > duration + _EPSILON:
            raise ValueError("Prediction segment times must be increasing and within durationSeconds.")
        aligned_start = round(start / FRAME_SECONDS) * FRAME_SECONDS
        aligned_end = round(end / FRAME_SECONDS) * FRAME_SECONDS
        if not math.isclose(start, aligned_start, rel_tol=0, abs_tol=_EPSILON):
            raise ValueError("Uncertainty-bearing prediction segment starts must align to the frame grid.")
        if not math.isclose(end, duration, rel_tol=0, abs_tol=_EPSILON) and not math.isclose(
            end,
            aligned_end,
            rel_tol=0,
            abs_tol=_EPSILON,
        ):
            raise ValueError(
                "Uncertainty-bearing prediction segment ends must align to the frame grid or final duration."
            )
        detailed_label = normalize_chord(str(item.get("label") or ""))
        detailed_product = _canonical_product(detailed_label)
        raw_product = item.get("productLabel")
        if raw_product is None or str(raw_product).strip() == "":
            product = detailed_product
        else:
            product = _canonical_product(normalize_chord(str(raw_product)))
            if product != detailed_product:
                raise ValueError("Prediction segment label and productLabel must describe the same Play Along product.")
        root_class, product_class = _product_classes(product)
        segments.append(
            {
                "start": start,
                "end": min(end, duration),
                "product": product,
                "rootClass": root_class,
                "productClass": product_class,
            }
        )
    segments.sort(key=lambda item: (item["start"], item["end"], item["product"]))
    for previous, current in zip(segments, segments[1:]):
        if current["start"] < previous["end"] - _EPSILON:
            raise ValueError("Prediction chord segments must not overlap.")
    return segments


def _product_classes(product: str) -> tuple[int, int | None]:
    label = normalize_chord(product)
    if label.root is None:
        return 0, None
    root = PITCH_CLASS[label.root] + 1
    if product.endswith("m7"):
        product_class = 4
    elif product.endswith("m"):
        product_class = 2
    elif product.endswith("7"):
        product_class = 3
    else:
        product_class = 1
    return root, product_class


def _validate_selected_class_alignment(
    evidence: Mapping[str, Any],
    segments: Sequence[Mapping[str, Any]],
) -> None:
    frame_count = int(evidence["frameCount"])
    frame_seconds = float(evidence["frameSeconds"])
    segment_index = 0
    for frame in range(frame_count):
        left_edge = frame * frame_seconds
        while segment_index < len(segments) and float(segments[segment_index]["end"]) <= left_edge + _EPSILON:
            segment_index += 1
        if (
            segment_index < len(segments)
            and float(segments[segment_index]["start"]) <= left_edge + _EPSILON
            and left_edge < float(segments[segment_index]["end"]) - _EPSILON
        ):
            expected_root = int(segments[segment_index]["rootClass"])
            expected_product = segments[segment_index]["productClass"]
        else:
            expected_root, expected_product = 0, None
        observed_root = evidence["root"]["selectedClass"][frame]
        observed_product = evidence["product"]["selectedClass"][frame]
        if observed_root != expected_root or observed_product != expected_product:
            raise ValueError(
                f"Prediction uncertainty selectedClass is stale or misaligned with decoded segments at frame {frame}."
            )


def _prediction_core_payload(prediction: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"uncertainty", "predictionCoreSha256", "uncertaintySha256"}
    return {key: value for key, value in prediction.items() if key not in excluded}


def _validate_prediction_uncertainty(prediction: Mapping[str, Any]) -> dict[str, Any]:
    uncertainty = _mapping(prediction.get("uncertainty"), "prediction.uncertainty")
    _exact_keys(
        uncertainty,
        {
            "schemaVersion",
            "contractSha256",
            "referenceFree",
            "timebase",
            "binding",
            "members",
            "frames",
            "predictionCoreSha256",
        },
        "prediction.uncertainty",
    )
    claimed_uncertainty_sha256 = _required_sha256(
        prediction.get("uncertaintySha256"),
        "prediction.uncertaintySha256",
    )
    if _canonical_sha256(uncertainty) != claimed_uncertainty_sha256:
        raise ValueError("prediction.uncertaintySha256 does not match the uncertainty payload.")
    claimed_core_sha256 = _required_sha256(
        prediction.get("predictionCoreSha256"),
        "prediction.predictionCoreSha256",
    )
    if _canonical_sha256(_prediction_core_payload(prediction)) != claimed_core_sha256:
        raise ValueError("prediction.predictionCoreSha256 does not match the prediction core.")
    nested_core_sha256 = _required_sha256(
        uncertainty.get("predictionCoreSha256"),
        "prediction.uncertainty.predictionCoreSha256",
    )
    if nested_core_sha256 != claimed_core_sha256:
        raise ValueError("prediction.uncertainty.predictionCoreSha256 does not match the prediction core.")
    validate_factorized_uncertainty_contract(uncertainty)
    if uncertainty.get("schemaVersion") != FACTORIZED_UNCERTAINTY_SCHEMA:
        raise ValueError("Prediction uncertainty uses an unsupported schemaVersion.")
    if uncertainty.get("referenceFree") is not True:
        raise ValueError("Prediction uncertainty must explicitly be referenceFree.")
    uncertainty_contract_sha256 = _required_sha256(
        uncertainty.get("contractSha256"),
        "prediction.uncertainty.contractSha256",
    )

    duration = _positive_number(prediction.get("durationSeconds"), "prediction.durationSeconds")
    timebase = _mapping(uncertainty.get("timebase"), "prediction.uncertainty.timebase")
    _exact_keys(
        timebase,
        {"frameSeconds", "frameCount", "timestampConvention", "durationSeconds"},
        "prediction.uncertainty.timebase",
    )
    frame_seconds = _finite_number(
        timebase.get("frameSeconds"),
        "prediction.uncertainty.timebase.frameSeconds",
    )
    if not math.isclose(frame_seconds, FRAME_SECONDS, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"Prediction uncertainty must use the exact {FRAME_SECONDS}-second frame grid.")
    if timebase.get("timestampConvention") != "left-edge":
        raise ValueError("Prediction uncertainty must use the left-edge timestamp convention.")
    frame_count = _strict_int(
        timebase.get("frameCount"),
        "prediction.uncertainty.timebase.frameCount",
        minimum=1,
    )
    uncertainty_duration = _positive_number(
        timebase.get("durationSeconds"),
        "prediction.uncertainty.timebase.durationSeconds",
    )
    if not math.isclose(duration, uncertainty_duration, rel_tol=0, abs_tol=_EPSILON):
        raise ValueError("Prediction and uncertainty durations disagree.")
    expected_frame_count = math.ceil(duration / frame_seconds)
    if frame_count != expected_frame_count:
        raise ValueError("Prediction uncertainty frameCount must equal ceil(durationSeconds / frameSeconds).")

    binding = _mapping(uncertainty.get("binding"), "prediction.uncertainty.binding")
    _exact_keys(
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
        "prediction.uncertainty.binding",
    )
    feature_spec_sha256 = _required_sha256(
        binding.get("featureSpecSha256"),
        "prediction.uncertainty.binding.featureSpecSha256",
    )
    feature_kind = binding.get("featureKind")
    if not isinstance(feature_kind, str) or not feature_kind:
        raise ValueError("prediction.uncertainty.binding.featureKind must be nonempty.")
    _strict_int(
        binding.get("featureCount"),
        "prediction.uncertainty.binding.featureCount",
        minimum=1,
    )

    members = _sequence(uncertainty.get("members"), "prediction.uncertainty.members")
    if not members:
        raise ValueError("Prediction uncertainty must bind at least one model member.")
    for ordinal, raw_member in enumerate(members):
        member = _mapping(raw_member, f"prediction.uncertainty.members[{ordinal}]")
        if member.get("ordinal") != ordinal:
            raise ValueError("Prediction uncertainty member ordinals must be contiguous and ordered.")

    frames = _mapping(uncertainty.get("frames"), "prediction.uncertainty.frames")
    _exact_keys(frames, {"root", "product", "ensemble", "boundary", "observability"}, "frames")
    root = _mapping(frames.get("root"), "prediction.uncertainty.frames.root")
    product = _mapping(frames.get("product"), "prediction.uncertainty.frames.product")
    ensemble = _mapping(frames.get("ensemble"), "prediction.uncertainty.frames.ensemble")
    boundary = _mapping(frames.get("boundary"), "prediction.uncertainty.frames.boundary")
    observability = _mapping(
        frames.get("observability"),
        "prediction.uncertainty.frames.observability",
    )
    _exact_keys(
        root,
        {"selectedClass", "selectedProbability", "topProbability", "margin", "normalizedEntropy"},
        "frames.root",
    )
    _exact_keys(
        product,
        {
            "selectedClass",
            "applicable",
            "selectedProbability",
            "topProbability",
            "margin",
            "normalizedEntropy",
            "directJointAgreement",
            "directJointJensenShannon",
        },
        "frames.product",
    )
    _exact_keys(
        ensemble,
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
        "frames.ensemble",
    )
    _exact_keys(
        boundary,
        {"modelProbability", "memberMeanProbability", "memberStdDev"},
        "frames.boundary",
    )
    _exact_keys(
        observability,
        {"profileSchemaVersion", "source", "values"},
        "frames.observability",
    )

    root_values = {
        "selectedClass": _class_array(
            root.get("selectedClass"), "frames.root.selectedClass", frame_count, minimum=0, maximum=12
        ),
        "selectedProbability": _numeric_array(
            root.get("selectedProbability"), "frames.root.selectedProbability", frame_count
        ),
        "topProbability": _numeric_array(root.get("topProbability"), "frames.root.topProbability", frame_count),
        "margin": _numeric_array(root.get("margin"), "frames.root.margin", frame_count),
        "normalizedEntropy": _numeric_array(
            root.get("normalizedEntropy"), "frames.root.normalizedEntropy", frame_count
        ),
    }
    applicable = _boolean_array(product.get("applicable"), "frames.product.applicable", frame_count)
    product_values: dict[str, Any] = {
        "applicable": applicable,
        "selectedClass": _class_array(
            product.get("selectedClass"),
            "frames.product.selectedClass",
            frame_count,
            minimum=1,
            maximum=4,
            nullable=True,
        ),
        "selectedProbability": _numeric_array(
            product.get("selectedProbability"),
            "frames.product.selectedProbability",
            frame_count,
            nullable=True,
        ),
        "topProbability": _numeric_array(
            product.get("topProbability"),
            "frames.product.topProbability",
            frame_count,
            nullable=True,
        ),
        "margin": _numeric_array(product.get("margin"), "frames.product.margin", frame_count, nullable=True),
        "normalizedEntropy": _numeric_array(
            product.get("normalizedEntropy"),
            "frames.product.normalizedEntropy",
            frame_count,
            nullable=True,
        ),
        "directJointAgreement": _boolean_array(
            product.get("directJointAgreement"),
            "frames.product.directJointAgreement",
            frame_count,
            nullable=True,
        ),
        "directJointJensenShannon": _numeric_array(
            product.get("directJointJensenShannon"),
            "frames.product.directJointJensenShannon",
            frame_count,
            nullable=True,
        ),
    }
    required_product_values = (
        "selectedClass",
        "selectedProbability",
        "topProbability",
        "margin",
        "normalizedEntropy",
    )
    for frame, is_applicable in enumerate(applicable):
        for name in required_product_values:
            if (product_values[name][frame] is not None) is not bool(is_applicable):
                raise ValueError(f"frames.product.{name}[{frame}] must be numeric exactly when product is applicable.")
        if not is_applicable and (
            product_values["directJointAgreement"][frame] is not None
            or product_values["directJointJensenShannon"][frame] is not None
        ):
            raise ValueError("Direct/joint product diagnostics must be null on N frames.")
        if (root_values["selectedClass"][frame] == 0) is not (not bool(is_applicable)):
            raise ValueError("Product applicability must exactly match the selected pitched-root state.")

    member_count = len(members)
    ensemble_values: dict[str, Any] = {
        "memberRootVote": _member_vote_matrix(
            ensemble.get("memberRootVote"),
            "frames.ensemble.memberRootVote",
            member_count,
            frame_count,
            minimum=0,
            maximum=12,
            nullable=False,
        ),
        "memberProductVote": _member_vote_matrix(
            ensemble.get("memberProductVote"),
            "frames.ensemble.memberProductVote",
            member_count,
            frame_count,
            minimum=1,
            maximum=4,
            nullable=True,
        ),
        "rootSelectedVoteShare": _numeric_array(
            ensemble.get("rootSelectedVoteShare"),
            "frames.ensemble.rootSelectedVoteShare",
            frame_count,
        ),
        "productSelectedVoteShare": _numeric_array(
            ensemble.get("productSelectedVoteShare"),
            "frames.ensemble.productSelectedVoteShare",
            frame_count,
            nullable=True,
        ),
        "rootPairwiseDisagreement": _numeric_array(
            ensemble.get("rootPairwiseDisagreement"),
            "frames.ensemble.rootPairwiseDisagreement",
            frame_count,
        ),
        "productPairwiseDisagreement": _numeric_array(
            ensemble.get("productPairwiseDisagreement"),
            "frames.ensemble.productPairwiseDisagreement",
            frame_count,
            nullable=True,
        ),
        "rootSelectedProbabilityStdDev": _numeric_array(
            ensemble.get("rootSelectedProbabilityStdDev"),
            "frames.ensemble.rootSelectedProbabilityStdDev",
            frame_count,
        ),
        "productSelectedProbabilityStdDev": _numeric_array(
            ensemble.get("productSelectedProbabilityStdDev"),
            "frames.ensemble.productSelectedProbabilityStdDev",
            frame_count,
            nullable=True,
        ),
        "rootMutualInformation": _numeric_array(
            ensemble.get("rootMutualInformation"),
            "frames.ensemble.rootMutualInformation",
            frame_count,
        ),
        "productMutualInformation": _numeric_array(
            ensemble.get("productMutualInformation"),
            "frames.ensemble.productMutualInformation",
            frame_count,
            nullable=True,
        ),
    }
    product_ensemble_names = (
        "productSelectedVoteShare",
        "productPairwiseDisagreement",
        "productSelectedProbabilityStdDev",
        "productMutualInformation",
    )
    for frame, is_applicable in enumerate(applicable):
        for name in product_ensemble_names:
            if (ensemble_values[name][frame] is not None) is not bool(is_applicable):
                raise ValueError(f"frames.ensemble.{name}[{frame}] must be numeric exactly when product is applicable.")
        for member_votes in ensemble_values["memberProductVote"]:
            if (member_votes[frame] is not None) is not bool(is_applicable):
                raise ValueError(
                    "frames.ensemble.memberProductVote must be numeric exactly when product is applicable."
                )

    boundary_values = {
        "modelProbability": _numeric_array(
            boundary.get("modelProbability"), "frames.boundary.modelProbability", frame_count
        ),
        "memberMeanProbability": _numeric_array(
            boundary.get("memberMeanProbability"),
            "frames.boundary.memberMeanProbability",
            frame_count,
        ),
        "memberStdDev": _numeric_array(boundary.get("memberStdDev"), "frames.boundary.memberStdDev", frame_count),
    }
    profile_schema = observability.get("profileSchemaVersion")
    if not isinstance(profile_schema, str) or not profile_schema:
        raise ValueError("frames.observability.profileSchemaVersion must be nonempty.")
    if observability.get("source") != "existing-feature-matrix":
        raise ValueError("frames.observability.source must be existing-feature-matrix.")
    raw_observability_values = _mapping(
        observability.get("values"),
        "frames.observability.values",
    )
    if set(raw_observability_values) != set(_OBSERVABILITY_FIELDS):
        raise ValueError("frames.observability.values must contain the exact frozen representation fields.")
    observability_values = {
        "representationRms": _numeric_array(
            raw_observability_values["representationRms"],
            "frames.observability.values.representationRms",
            frame_count,
            maximum=None,
        ),
        "temporalDeltaRms": _numeric_array(
            raw_observability_values["temporalDeltaRms"],
            "frames.observability.values.temporalDeltaRms",
            frame_count,
            maximum=None,
        ),
        "absoluteActivationConcentration": _numeric_array(
            raw_observability_values["absoluteActivationConcentration"],
            "frames.observability.values.absoluteActivationConcentration",
            frame_count,
        ),
        "cosineChange": _numeric_array(
            raw_observability_values["cosineChange"],
            "frames.observability.values.cosineChange",
            frame_count,
            maximum=2.0,
        ),
    }

    return {
        "duration": duration,
        "frameSeconds": frame_seconds,
        "frameCount": frame_count,
        "predictionCoreSha256": claimed_core_sha256,
        "uncertaintySha256": claimed_uncertainty_sha256,
        "uncertaintyContractSha256": uncertainty_contract_sha256,
        "featureSpecSha256": feature_spec_sha256,
        "featureKind": feature_kind,
        "observabilityProfileSchemaVersion": profile_schema,
        "root": root_values,
        "product": product_values,
        "ensemble": ensemble_values,
        "boundary": boundary_values,
        "observability": observability_values,
    }


def _validate_timing(timing_only: Mapping[str, Any], duration: float) -> dict[str, Any]:
    timing = _mapping(timing_only, "timing_only")
    allowed_keys = {
        "schemaVersion",
        "durationSeconds",
        "barStartsSeconds",
        "timingProvenance",
        "prefixExcludedSeconds",
        "contractSha256",
    }
    unknown = set(timing) - allowed_keys
    if unknown:
        raise ValueError(f"Explicit bar timing contains unsupported fields: {', '.join(sorted(unknown))}.")
    if timing.get("schemaVersion") != EXPLICIT_BAR_GRID_SCHEMA:
        raise ValueError("timing_only must use the explicit bar-grid schema.")
    timing_duration = _positive_number(timing.get("durationSeconds"), "timing_only.durationSeconds")
    canonical_prediction_duration = math.floor(duration * 1000 + 0.5) / 1000
    if not math.isclose(
        timing_duration,
        canonical_prediction_duration,
        rel_tol=0,
        abs_tol=_EPSILON,
    ):
        raise ValueError(
            "Runtime timing duration must equal the exact player-canonical "
            "millisecond rounding of the prediction duration."
        )
    duration_alignment = (
        "exact"
        if math.isclose(timing_duration, duration, rel_tol=0, abs_tol=_EPSILON)
        else "player-canonical-millisecond"
    )
    claimed_contract_sha256 = _required_sha256(
        timing.get("contractSha256"),
        "timing_only.contractSha256",
    )
    contract_payload = {key: value for key, value in timing.items() if key != "contractSha256"}
    if _canonical_sha256(contract_payload) != claimed_contract_sha256:
        raise ValueError("timing_only.contractSha256 does not match the explicit grid contract.")

    starts_raw = _sequence(timing.get("barStartsSeconds"), "timing_only.barStartsSeconds")
    if not starts_raw:
        raise ValueError("timing_only.barStartsSeconds must be nonempty.")
    starts: list[float] = []
    for index, value in enumerate(starts_raw):
        start = _finite_number(value, f"timing_only.barStartsSeconds[{index}]")
        if start < 0 or start > duration + _EPSILON:
            raise ValueError("timing_only.barStartsSeconds contains an out-of-range value.")
        if starts and start <= starts[-1] + _EPSILON:
            raise ValueError("timing_only.barStartsSeconds must be strictly increasing.")
        starts.append(start)
    if math.isclose(starts[-1], duration, rel_tol=0, abs_tol=_EPSILON):
        starts.pop()
    if not starts:
        raise ValueError("timing_only.barStartsSeconds does not define a positive bar.")

    timing_provenance = _mapping(timing.get("timingProvenance"), "timing_only.timingProvenance")
    if set(timing_provenance) != {"barStartsSeconds"}:
        raise ValueError("timing_only.timingProvenance must describe only barStartsSeconds.")
    bar_provenance = _mapping(
        timing_provenance.get("barStartsSeconds"),
        "timing_only.timingProvenance.barStartsSeconds",
    )
    required_provenance_keys = {
        "status",
        "sourceClass",
        "sourceId",
        "sourceContractSha256",
        "deployable",
        "referenceFree",
    }
    optional_provenance_keys = {"prefixExcludedSeconds"}
    if not required_provenance_keys <= set(bar_provenance) or (
        set(bar_provenance) - required_provenance_keys - optional_provenance_keys
    ):
        raise ValueError("timing_only bar provenance does not match the explicit provenance contract.")
    if bar_provenance.get("status") != "explicit":
        raise ValueError("Bar timing provenance must have explicit status; inferred grids are forbidden.")
    source_class = bar_provenance.get("sourceClass")
    if source_class not in _TIMING_SOURCE_CLASSES:
        raise ValueError("Bar timing provenance sourceClass is unsupported.")
    source_id = bar_provenance.get("sourceId")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Bar timing provenance sourceId must be nonempty.")
    source_contract_sha256 = _required_sha256(
        bar_provenance.get("sourceContractSha256"),
        "timing_only.timingProvenance.barStartsSeconds.sourceContractSha256",
    )
    if bar_provenance.get("referenceFree") is not True:
        raise ValueError("Explicit bar timing must be free of chord-reference content.")
    deployable = bar_provenance.get("deployable")
    if not isinstance(deployable, bool):
        raise ValueError("Explicit bar timing deployable must be boolean.")
    if not deployable:
        raise ValueError("Runtime bar timing must be marked deployable.")

    grid_start = starts[0]
    top_prefix = timing.get("prefixExcludedSeconds")
    provenance_prefix = bar_provenance.get("prefixExcludedSeconds")
    if grid_start > _EPSILON:
        top_prefix_value = _finite_number(top_prefix, "timing_only.prefixExcludedSeconds")
        provenance_prefix_value = _finite_number(
            provenance_prefix,
            "timing_only.timingProvenance.barStartsSeconds.prefixExcludedSeconds",
        )
        if not math.isclose(top_prefix_value, grid_start, rel_tol=0, abs_tol=_EPSILON) or not math.isclose(
            provenance_prefix_value,
            grid_start,
            rel_tol=0,
            abs_tol=_EPSILON,
        ):
            raise ValueError("A positive bar-grid start requires exact, duplicate prefix certification.")
    elif top_prefix is not None or provenance_prefix is not None:
        top_prefix_value = _finite_number(top_prefix, "timing_only.prefixExcludedSeconds")
        provenance_prefix_value = _finite_number(
            provenance_prefix,
            "timing_only.timingProvenance.barStartsSeconds.prefixExcludedSeconds",
        )
        if abs(top_prefix_value) > _EPSILON or abs(provenance_prefix_value) > _EPSILON:
            raise ValueError("A zero-start bar grid may only certify a zero excluded prefix.")

    return {
        "starts": starts,
        "durationSeconds": timing_duration,
        "durationAlignment": duration_alignment,
        "contractSha256": claimed_contract_sha256,
        "sha256": _canonical_sha256(timing),
        "sourceClass": str(source_class),
        "sourceId": source_id,
        "sourceContractSha256": source_contract_sha256,
        "deployable": deployable,
        "gridStartSeconds": grid_start,
        "excludedPrefixDurationSeconds": grid_start,
    }


def _overlap(start: float, end: float, left: float, right: float) -> float:
    return max(0.0, min(end, right) - max(start, left))


def _overlap_by_product(
    segments: Sequence[Mapping[str, Any]],
    start: float,
    end: float,
) -> tuple[dict[str, float], float, list[str]]:
    totals: dict[str, list[float]] = {}
    covered_parts: list[float] = []
    sequence: list[str] = []
    for segment in segments:
        seconds = _overlap(start, end, float(segment["start"]), float(segment["end"]))
        if seconds <= _EPSILON:
            continue
        product = str(segment["product"])
        totals.setdefault(product, []).append(seconds)
        covered_parts.append(seconds)
        if not sequence or sequence[-1] != product:
            sequence.append(product)
    return (
        {product: math.fsum(parts) for product, parts in totals.items()},
        math.fsum(covered_parts),
        sequence,
    )


def _frame_weights(
    frame_count: int,
    frame_seconds: float,
    duration: float,
    start: float,
    end: float,
    *,
    segments: Sequence[Mapping[str, Any]] | None = None,
    product: str | None = None,
) -> list[float]:
    output: list[float] = []
    selected_segments = (
        [segment for segment in segments if segment["product"] == product]
        if segments is not None and product is not None
        else []
        if segments is not None
        else None
    )
    for frame in range(frame_count):
        frame_start = frame * frame_seconds
        frame_end = min(duration, (frame + 1) * frame_seconds)
        bar_overlap = _overlap(frame_start, frame_end, start, end)
        if bar_overlap <= _EPSILON or selected_segments is None:
            output.append(bar_overlap if selected_segments is None else 0.0)
            continue
        parts = [
            _overlap(
                max(frame_start, start),
                min(frame_end, end),
                float(segment["start"]),
                float(segment["end"]),
            )
            for segment in selected_segments
        ]
        output.append(math.fsum(part for part in parts if part > _EPSILON))
    return output


def _weighted_summary(values: Sequence[float | bool | None], weights: Sequence[float]) -> dict[str, float | None]:
    selected = [
        (float(value), weight)
        for value, weight in zip(values, weights, strict=True)
        if value is not None and weight > _EPSILON
    ]
    if not selected:
        return {"mean": None, "minimum": None, "maximum": None}
    total_weight = math.fsum(weight for _value, weight in selected)
    return {
        "mean": math.fsum(value * weight for value, weight in selected) / total_weight,
        "minimum": min(value for value, _weight in selected),
        "maximum": max(value for value, _weight in selected),
    }


def _set_summary(
    output: dict[str, float | int | None],
    prefix: str,
    values: Sequence[float | bool | None],
    weights: Sequence[float],
    *statistics: str,
) -> None:
    summary = _weighted_summary(values, weights)
    suffix = {"mean": "Mean", "minimum": "Minimum", "maximum": "Maximum"}
    for statistic in statistics:
        output[f"{prefix}{suffix[statistic]}"] = summary[statistic]


def _product_family(product: str | None) -> dict[str, int]:
    values = {
        "productFamilyNone": 0,
        "productFamilyMajor": 0,
        "productFamilyMinor": 0,
        "productFamilyDominant": 0,
        "productFamilyMinorSeventh": 0,
    }
    if product is None:
        return values
    if product == "N.C.":
        values["productFamilyNone"] = 1
    elif product.endswith("m7"):
        values["productFamilyMinorSeventh"] = 1
    elif product.endswith("m"):
        values["productFamilyMinor"] = 1
    elif product.endswith("7"):
        values["productFamilyDominant"] = 1
    else:
        values["productFamilyMajor"] = 1
    return values


def _bar_features(
    evidence: Mapping[str, Any],
    full_weights: Sequence[float],
    winner_weights: Sequence[float],
    *,
    prediction_coverage: float,
    prediction_dominance: float,
    prediction_transition_count: int,
    prediction_product: str | None,
    bar_start: float,
    bar_end: float,
) -> dict[str, float | int | None]:
    root = evidence["root"]
    product = evidence["product"]
    ensemble = evidence["ensemble"]
    boundary = evidence["boundary"]
    observability = evidence["observability"]
    values: dict[str, float | int | None] = {
        "predictionCoverage": prediction_coverage,
        "predictionDominance": prediction_dominance,
        "predictionTransitionCount": prediction_transition_count,
        **_product_family(prediction_product),
    }

    _set_summary(values, "rootSelectedProbability", root["selectedProbability"], winner_weights, "mean", "minimum")
    _set_summary(values, "rootMargin", root["margin"], winner_weights, "mean", "minimum")
    _set_summary(values, "rootNormalizedEntropy", root["normalizedEntropy"], winner_weights, "mean", "maximum")
    _set_summary(
        values,
        "productSelectedProbability",
        product["selectedProbability"],
        winner_weights,
        "mean",
        "minimum",
    )
    _set_summary(values, "productMargin", product["margin"], winner_weights, "mean", "minimum")
    _set_summary(
        values,
        "productNormalizedEntropy",
        product["normalizedEntropy"],
        winner_weights,
        "mean",
        "maximum",
    )
    for prefix, name, extrema in (
        ("rootSelectedVoteShare", "rootSelectedVoteShare", ("mean", "minimum")),
        ("productSelectedVoteShare", "productSelectedVoteShare", ("mean", "minimum")),
        ("rootPairwiseDisagreement", "rootPairwiseDisagreement", ("mean", "maximum")),
        ("productPairwiseDisagreement", "productPairwiseDisagreement", ("mean", "maximum")),
        (
            "rootSelectedProbabilityStdDev",
            "rootSelectedProbabilityStdDev",
            ("mean", "maximum"),
        ),
        (
            "productSelectedProbabilityStdDev",
            "productSelectedProbabilityStdDev",
            ("mean", "maximum"),
        ),
        ("rootMutualInformation", "rootMutualInformation", ("mean", "maximum")),
        ("productMutualInformation", "productMutualInformation", ("mean", "maximum")),
    ):
        _set_summary(values, prefix, ensemble[name], winner_weights, *extrema)

    _set_summary(
        values,
        "boundaryModelProbability",
        boundary["modelProbability"],
        full_weights,
        "mean",
        "maximum",
    )
    frame_seconds = float(evidence["frameSeconds"])
    frame_count = int(evidence["frameCount"])

    def boundary_at_edge(edge_seconds: float) -> float | None:
        frame = math.floor(edge_seconds / frame_seconds + 0.5 + _EPSILON)
        if frame < 0 or frame >= frame_count:
            return None
        return float(boundary["modelProbability"][frame])

    values["boundaryStartEdgeProbability"] = boundary_at_edge(bar_start)
    values["boundaryEndEdgeProbability"] = boundary_at_edge(bar_end)
    for name in _OBSERVABILITY_FIELDS:
        _set_summary(values, name, observability[name], full_weights, "mean", "maximum")

    missing = set(BAR_FEATURE_NAMES) - set(values)
    extra = set(values) - set(BAR_FEATURE_NAMES)
    if missing or extra:
        raise RuntimeError(f"Internal bar feature contract mismatch: missing={missing}, extra={extra}.")
    return {name: values[name] for name in BAR_FEATURE_NAMES}


def summarize_prediction_bars(
    prediction: Mapping[str, Any],
    timing_only: Mapping[str, Any],
) -> dict[str, Any]:
    """Build strict prediction-only uncertainty features on an explicit bar grid.

    Only an explicit, deployable, reference-free runtime grid is accepted. No
    annotation/oracle, inferred, prediction-provided, or reference-provided
    grid is accepted.
    """

    prediction_value = _mapping(prediction, "prediction")
    evidence = _validate_prediction_uncertainty(prediction_value)
    timing = _validate_timing(timing_only, float(evidence["duration"]))
    track_id = prediction_value.get("id")
    if not isinstance(track_id, str) or not track_id.strip():
        raise ValueError("Prediction id must be a nonempty string.")
    segments = _prediction_segments(prediction_value, float(evidence["duration"]))
    _validate_selected_class_alignment(evidence, segments)
    starts = list(timing["starts"])
    ends = [*starts[1:], float(evidence["duration"])]
    bars: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(zip(starts, ends, strict=True)):
        bar_duration = end - start
        if bar_duration <= _EPSILON:
            raise ValueError("Explicit bar timing contains a nonpositive bar.")
        product_overlap, covered, product_sequence = _overlap_by_product(segments, start, end)
        if product_overlap:
            maximum_duration = max(product_overlap.values())
            winning_product = min(
                product
                for product, seconds in product_overlap.items()
                if math.isclose(seconds, maximum_duration, rel_tol=0, abs_tol=_EPSILON)
            )
            winning_duration = float(product_overlap[winning_product])
        else:
            winning_product = None
            winning_duration = 0.0
        coverage = min(1.0, max(0.0, covered / bar_duration))
        dominance = min(1.0, max(0.0, winning_duration / covered)) if covered > _EPSILON else 0.0
        transition_count = max(0, len(product_sequence) - 1)
        full_weights = _frame_weights(
            int(evidence["frameCount"]),
            float(evidence["frameSeconds"]),
            float(evidence["duration"]),
            start,
            end,
        )
        winner_weights = _frame_weights(
            int(evidence["frameCount"]),
            float(evidence["frameSeconds"]),
            float(evidence["duration"]),
            start,
            end,
            segments=segments,
            product=winning_product,
        )
        bars.append(
            {
                "trackId": track_id,
                "index": index,
                "start": start,
                "end": end,
                "predictionProduct": winning_product,
                "predictionProductDurationSeconds": winning_duration,
                "predictionCoverage": coverage,
                "predictionDominance": dominance,
                "predictionTransitionCount": transition_count,
                "featureValues": _bar_features(
                    evidence,
                    full_weights,
                    winner_weights,
                    prediction_coverage=coverage,
                    prediction_dominance=dominance,
                    prediction_transition_count=transition_count,
                    prediction_product=winning_product,
                    bar_start=start,
                    bar_end=end,
                ),
            }
        )

    result = {
        "schemaVersion": BAR_UNCERTAINTY_SCHEMA,
        "referenceFree": True,
        "deployable": bool(timing["deployable"]),
        "selectorUseAllowed": bool(timing["deployable"]),
        "timingOracleUsed": False,
        "trackId": track_id,
        "durationSeconds": float(evidence["duration"]),
        "binding": {
            "predictionCoreSha256": evidence["predictionCoreSha256"],
            "uncertaintySha256": evidence["uncertaintySha256"],
            "uncertaintyContractSha256": evidence["uncertaintyContractSha256"],
            "sourceFeatureKind": evidence["featureKind"],
            "sourceFeatureSpecSha256": evidence["featureSpecSha256"],
            "observabilityProfileSchemaVersion": evidence["observabilityProfileSchemaVersion"],
            "barFeatureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
            "timingSha256": timing["sha256"],
            "timingContractSha256": timing["contractSha256"],
            "timingSourceContractSha256": timing["sourceContractSha256"],
        },
        "featureContract": {
            **_BAR_FEATURE_CONTRACT,
            "contractSha256": BAR_FEATURE_CONTRACT_SHA256,
        },
        "timing": {
            "schemaVersion": EXPLICIT_BAR_GRID_SCHEMA,
            "sourceClass": timing["sourceClass"],
            "sourceId": timing["sourceId"],
            "deployable": bool(timing["deployable"]),
            "durationSeconds": timing["durationSeconds"],
            "predictionDurationSeconds": float(evidence["duration"]),
            "durationAlignment": timing["durationAlignment"],
            "gridStartSeconds": timing["gridStartSeconds"],
            "excludedPrefixDurationSeconds": timing["excludedPrefixDurationSeconds"],
            "barCount": len(bars),
        },
        "bars": bars,
    }
    result["summarySha256"] = _canonical_sha256(result)
    return result
