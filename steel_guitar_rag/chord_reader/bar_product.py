"""Literal bar-count Play Along product-confidence evaluation.

This evaluator deliberately keeps bar precision separate from duration-weighted
scientific metrics.  A reference bar is eligible only when one product chord
dominates it.  A prediction must cover the bar, have one dominant product, and
provide confidence for that winning product before it can be accepted at any
threshold.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import math
from typing import Any

from .labels import PITCH_CLASS, SHARP_NAMES, ChordLabel, normalize_chord


BAR_CONFIDENCE_THRESHOLDS = tuple(index / 100 for index in range(101))
DEFAULT_REFERENCE_DOMINANCE = 0.75
DEFAULT_PREDICTION_COVERAGE = 0.75
DEFAULT_PREDICTION_DOMINANCE = 0.75
_EPSILON = 1e-9


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    return float(numerator) / float(denominator) if denominator else None


def _validated_fraction(name: str, value: float) -> float:
    number = _finite_number(value)
    if number is None or not 0 < number <= 1:
        raise ValueError(f"{name} must be greater than 0 and at most 1.")
    return number


def _validated_thresholds(values: Iterable[float]) -> tuple[float, ...]:
    output: set[float] = set()
    for value in values:
        threshold = _finite_number(value)
        if threshold is None or not 0 <= threshold <= 1:
            raise ValueError("Bar confidence thresholds must be finite values between 0 and 1.")
        output.add(threshold)
    if not output:
        raise ValueError("At least one bar confidence threshold is required.")
    return tuple(sorted(output))


def _canonical_product(label: ChordLabel) -> str:
    if label.root is None:
        return label.product_symbol
    suffix = label.product_symbol[len(label.root) :]
    return f"{SHARP_NAMES[PITCH_CLASS[label.root]]}{suffix}"


def _segment_product(item: Mapping[str, Any]) -> str:
    raw = item.get("productLabel")
    if raw is None or str(raw).strip() == "":
        raw = item.get("label")
    return _canonical_product(normalize_chord(str(raw or "")))


def _segment_confidence(item: Mapping[str, Any]) -> float | None:
    for name in ("productConfidence", "confidence"):
        value = _finite_number(item.get(name))
        if value is not None and 0 <= value <= 1:
            return value
    return None


def _segments(values: Any, *, prediction: bool) -> list[dict[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError("Chord segments must be a sequence.")
    output: list[dict[str, Any]] = []
    for item in values:
        if not isinstance(item, Mapping):
            raise ValueError("Every chord segment must be an object.")
        start = _finite_number(item.get("start"))
        end = _finite_number(item.get("end"))
        if start is None or end is None or start < 0 or end <= start:
            raise ValueError("Chord segment times must be finite, nonnegative, and increasing.")
        segment = {
            "start": start,
            "end": end,
            "product": _segment_product(item),
        }
        if prediction:
            segment["confidence"] = _segment_confidence(item)
        output.append(segment)
    output.sort(key=lambda item: (item["start"], item["end"]))
    for previous, current in zip(output, output[1:]):
        if current["start"] < previous["end"] - _EPSILON:
            raise ValueError("Chord segments must not overlap.")
    return output


def _declared_duration(source: Mapping[str, Any], source_name: str) -> float | None:
    if "durationSeconds" not in source or source.get("durationSeconds") is None:
        return None
    duration = _finite_number(source.get("durationSeconds"))
    if duration is None or duration <= 0:
        raise ValueError(f"{source_name}.durationSeconds must be finite and positive.")
    return duration


def _duration_seconds(
    reference: Mapping[str, Any],
    prediction: Mapping[str, Any],
    timing: Mapping[str, Any],
    reference_segments: Sequence[Mapping[str, Any]],
    prediction_segments: Sequence[Mapping[str, Any]],
) -> float:
    timing_duration = _declared_duration(timing, "timing")
    reference_duration = _declared_duration(reference, "reference")
    prediction_duration = _declared_duration(prediction, "prediction")
    reference_end = max(
        [float(item["end"]) for item in reference_segments],
        default=0.0,
    )
    prediction_end = max(
        [float(item["end"]) for item in prediction_segments],
        default=0.0,
    )
    if (
        timing_duration is not None
        and reference_duration is not None
        and not math.isclose(timing_duration, reference_duration, rel_tol=0, abs_tol=_EPSILON)
    ):
        raise ValueError("timing and reference durations disagree.")
    duration = timing_duration or reference_duration or reference_end
    if duration and reference_end > duration + _EPSILON:
        raise ValueError("The reference duration ends before a reference chord segment.")
    # Prediction timing never expands or reshapes a reference-backed evaluation
    # interval. It is used only when the reference has no duration evidence.
    if not duration:
        duration = prediction_duration or prediction_end
    if duration <= 0:
        raise ValueError("A positive song duration is required for bar evaluation.")
    return duration


def _explicit_bar_starts(
    sources: Sequence[tuple[str, Mapping[str, Any]]],
    duration: float,
) -> tuple[list[float], str, float, dict[str, Any]] | None:
    for source_name, source in sources:
        if "barStartsSeconds" not in source:
            continue
        values = source.get("barStartsSeconds")
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
            raise ValueError(f"{source_name}.barStartsSeconds must be a nonempty sequence.")
        starts: list[float] = []
        for value in values:
            start = _finite_number(value)
            if start is None or start < 0 or start > duration + _EPSILON:
                raise ValueError(f"{source_name}.barStartsSeconds contains an invalid bar start.")
            if starts and start <= starts[-1] + _EPSILON:
                raise ValueError(f"{source_name}.barStartsSeconds must be strictly increasing.")
            starts.append(start)
        grid_start = starts[0]
        certification = {
            "timingProvenanceStatus": None,
            "prefixExclusionCertified": False,
        }
        if not math.isclose(grid_start, 0.0, rel_tol=0, abs_tol=_EPSILON):
            provenance = source.get("timingProvenance")
            bar_provenance = provenance.get("barStartsSeconds") if isinstance(provenance, Mapping) else None
            top_prefix = _finite_number(source.get("prefixExcludedSeconds"))
            provenance_prefix = (
                _finite_number(bar_provenance.get("prefixExcludedSeconds"))
                if isinstance(bar_provenance, Mapping)
                else None
            )
            explicitly_certified = (
                isinstance(bar_provenance, Mapping)
                and bar_provenance.get("status") == "explicit"
                and top_prefix is not None
                and provenance_prefix is not None
                and math.isclose(top_prefix, grid_start, rel_tol=0, abs_tol=_EPSILON)
                and math.isclose(provenance_prefix, grid_start, rel_tol=0, abs_tol=_EPSILON)
            )
            if not explicitly_certified:
                raise ValueError(
                    f"{source_name}.barStartsSeconds may begin after 0 only when "
                    "timingProvenance explicitly certifies an exactly matching "
                    "prefixExcludedSeconds."
                )
            certification = {
                "timingProvenanceStatus": "explicit",
                "prefixExclusionCertified": True,
            }
        if math.isclose(starts[-1], duration, rel_tol=0, abs_tol=_EPSILON):
            starts.pop()
        if not starts:
            raise ValueError(f"{source_name}.barStartsSeconds does not define a positive bar.")
        return starts, source_name, grid_start, certification
    return None


def _metadata_value(
    name: str,
    sources: Sequence[tuple[str, Mapping[str, Any]]],
) -> tuple[Any, str] | None:
    for source_name, source in sources:
        value = source.get(name)
        if value is not None and str(value).strip() != "":
            return value, source_name
    return None


def _inferred_bar_starts(
    sources: Sequence[tuple[str, Mapping[str, Any]]],
    duration: float,
) -> tuple[list[float], dict[str, Any]] | None:
    tempo_value = _metadata_value("tempo", sources)
    meter_value = _metadata_value("meter", sources)
    if tempo_value is None or meter_value is None:
        return None
    tempo = _finite_number(tempo_value[0])
    if tempo is None or tempo <= 0:
        raise ValueError("tempo must be finite and positive for inferred bars.")
    parts = str(meter_value[0]).strip().split("/")
    if len(parts) != 2:
        raise ValueError("meter must use numerator/denominator notation for inferred bars.")
    try:
        numerator, denominator = (int(value) for value in parts)
    except ValueError as exc:
        raise ValueError("meter must use integer numerator/denominator notation.") from exc
    if numerator <= 0 or denominator <= 0:
        raise ValueError("meter numerator and denominator must be positive.")
    quarter_notes_per_bar = numerator * 4 / denominator
    bar_duration = quarter_notes_per_bar * 60 / tempo
    if not math.isfinite(bar_duration) or bar_duration <= 0:
        raise ValueError("tempo and meter do not define a valid bar duration.")
    starts: list[float] = []
    index = 0
    while index * bar_duration < duration - _EPSILON:
        starts.append(index * bar_duration)
        index += 1
    return starts, {
        "tempo": tempo,
        "meter": f"{numerator}/{denominator}",
        "barDurationSeconds": bar_duration,
        "tempoUnit": "quarter-note-bpm",
        "tempoSource": tempo_value[1],
        "meterSource": meter_value[1],
    }


def _bar_grid(
    reference: Mapping[str, Any],
    timing: Mapping[str, Any],
    duration: float,
) -> dict[str, Any]:
    # The scoring grid must be independent of the model under evaluation. A
    # prediction's own bar starts, tempo, or meter can never define its test.
    sources = (("timing", timing), ("reference", reference))
    explicit = _explicit_bar_starts(sources, duration)
    if explicit is not None:
        starts, source, grid_start, certification = explicit
        return {
            "available": True,
            "provenance": "explicit-bar-starts",
            "source": source,
            "barStartsSeconds": starts,
            "barCount": len(starts),
            "durationSeconds": duration,
            "gridStartSeconds": grid_start,
            "excludedPrefixDurationSeconds": grid_start,
            **certification,
        }
    inferred = _inferred_bar_starts(sources, duration)
    if inferred is not None:
        starts, metadata = inferred
        return {
            "available": True,
            "provenance": "inferred-tempo-meter",
            "source": "tempo-meter",
            "barStartsSeconds": starts,
            "barCount": len(starts),
            "durationSeconds": duration,
            **metadata,
        }
    return {
        "available": False,
        "provenance": "unavailable",
        "reason": "missing explicit barStartsSeconds or inferable tempo+meter",
        "barStartsSeconds": [],
        "barCount": 0,
        "durationSeconds": duration,
    }


def _overlap_by_product(
    segments: Sequence[Mapping[str, Any]],
    start: float,
    end: float,
) -> tuple[dict[str, float], float]:
    overlaps: dict[str, float] = {}
    covered = 0.0
    for segment in segments:
        overlap = min(end, float(segment["end"])) - max(start, float(segment["start"]))
        if overlap <= _EPSILON:
            continue
        product = str(segment["product"])
        overlaps[product] = overlaps.get(product, 0.0) + overlap
        covered += overlap
    return overlaps, covered


def _dominant_product(overlaps: Mapping[str, float]) -> tuple[str | None, float]:
    if not overlaps:
        return None, 0.0
    product, duration = min(overlaps.items(), key=lambda item: (-item[1], item[0]))
    return product, float(duration)


def _winning_product_confidence(
    segments: Sequence[Mapping[str, Any]],
    product: str,
    start: float,
    end: float,
) -> tuple[float | None, float, float]:
    overlap_duration = 0.0
    confidence_duration = 0.0
    confidence_mass = 0.0
    for segment in segments:
        if segment["product"] != product:
            continue
        overlap = min(end, float(segment["end"])) - max(start, float(segment["start"]))
        if overlap <= _EPSILON:
            continue
        overlap_duration += overlap
        confidence = segment.get("confidence")
        if confidence is not None:
            confidence_duration += overlap
            confidence_mass += overlap * float(confidence)
    if overlap_duration <= _EPSILON or confidence_duration < overlap_duration - _EPSILON:
        return None, confidence_duration, overlap_duration
    return confidence_mass / overlap_duration, confidence_duration, overlap_duration


def score_bar_product_confidence(
    reference: Mapping[str, Any],
    prediction: Mapping[str, Any],
    *,
    timing: Mapping[str, Any] | None = None,
    confidence_thresholds: Iterable[float] = BAR_CONFIDENCE_THRESHOLDS,
    reference_dominance: float = DEFAULT_REFERENCE_DOMINANCE,
    prediction_coverage: float = DEFAULT_PREDICTION_COVERAGE,
    prediction_dominance: float = DEFAULT_PREDICTION_DOMINANCE,
) -> dict[str, Any]:
    """Score literal accepted-bar product precision for one track."""

    timing = timing or {}
    thresholds = _validated_thresholds(confidence_thresholds)
    reference_dominance = _validated_fraction("reference_dominance", reference_dominance)
    prediction_coverage = _validated_fraction("prediction_coverage", prediction_coverage)
    prediction_dominance = _validated_fraction("prediction_dominance", prediction_dominance)
    reference_segments = _segments(reference.get("segments"), prediction=False)
    prediction_segments = _segments(prediction.get("segments"), prediction=True)
    duration = _duration_seconds(
        reference,
        prediction,
        timing,
        reference_segments,
        prediction_segments,
    )
    grid = _bar_grid(reference, timing, duration)
    base = {
        "schemaVersion": "chord_bar_product_confidence_v1",
        "available": bool(grid["available"]),
        "grid": grid,
        "configuration": {
            "referenceDominance": reference_dominance,
            "predictionCoverage": prediction_coverage,
            "predictionDominance": prediction_dominance,
        },
    }
    if not grid["available"]:
        return {
            **base,
            "totalBarCount": 0,
            "eligibleBarCount": 0,
            "excludedMixedBarCount": 0,
            "excludedUncoveredBarCount": 0,
            "predictionMixedBarCount": 0,
            "predictionUncoveredBarCount": 0,
            "confidenceMissingBarCount": 0,
            "scorablePredictionBarCount": 0,
            "excludedPrefixDurationSeconds": 0.0,
            "barEligibility": 0.0,
            "explicitBarGrid": False,
            "bars": [],
            "curve": [],
        }

    starts = list(grid["barStartsSeconds"])
    ends = [*starts[1:], duration]
    bars: list[dict[str, Any]] = []
    eligible_bars: list[dict[str, Any]] = []
    excluded_mixed = 0
    excluded_uncovered = 0
    prediction_mixed = 0
    prediction_uncovered = 0
    confidence_missing = 0
    for index, (start, end) in enumerate(zip(starts, ends, strict=True)):
        bar_duration = end - start
        reference_overlap, reference_covered = _overlap_by_product(reference_segments, start, end)
        reference_product, reference_product_duration = _dominant_product(reference_overlap)
        reference_coverage = reference_covered / bar_duration
        reference_product_share = reference_product_duration / bar_duration
        bar: dict[str, Any] = {
            "index": index,
            "start": start,
            "end": end,
            "referenceProduct": reference_product,
            "referenceCoverage": reference_coverage,
            "referenceDominance": reference_product_share,
            "eligible": False,
            "predictionProduct": None,
            "predictionCoverage": 0.0,
            "predictionDominance": 0.0,
            "productConfidence": None,
            "correct": None,
        }
        if reference_product is None or reference_coverage + _EPSILON < reference_dominance:
            excluded_uncovered += 1
            bar["exclusionReason"] = "reference-uncovered"
            bars.append(bar)
            continue
        if reference_product_share + _EPSILON < reference_dominance:
            excluded_mixed += 1
            bar["exclusionReason"] = "reference-mixed"
            bars.append(bar)
            continue

        bar["eligible"] = True
        prediction_overlap, prediction_covered = _overlap_by_product(prediction_segments, start, end)
        prediction_product, prediction_product_duration = _dominant_product(prediction_overlap)
        predicted_coverage = prediction_covered / bar_duration
        predicted_dominance = prediction_product_duration / max(_EPSILON, prediction_covered)
        bar.update(
            {
                "predictionProduct": prediction_product,
                "predictionCoverage": predicted_coverage,
                "predictionDominance": predicted_dominance,
            }
        )
        if prediction_product is None or predicted_coverage + _EPSILON < prediction_coverage:
            prediction_uncovered += 1
            bar["predictionExclusionReason"] = "prediction-uncovered"
        elif predicted_dominance + _EPSILON < prediction_dominance:
            prediction_mixed += 1
            bar["predictionExclusionReason"] = "prediction-mixed"
        else:
            confidence, confidence_duration, product_duration = _winning_product_confidence(
                prediction_segments,
                prediction_product,
                start,
                end,
            )
            bar["predictionProductDurationSeconds"] = product_duration
            bar["productConfidenceDurationSeconds"] = confidence_duration
            if confidence is None:
                confidence_missing += 1
                bar["predictionExclusionReason"] = "prediction-confidence-missing"
            else:
                bar["productConfidence"] = confidence
                bar["correct"] = prediction_product == reference_product
                eligible_bars.append(bar)
        bars.append(bar)

    eligible_count = sum(bool(bar["eligible"]) for bar in bars)
    curve: list[dict[str, Any]] = []
    for threshold in thresholds:
        accepted = [bar for bar in eligible_bars if float(bar["productConfidence"]) + _EPSILON >= threshold]
        correct = sum(bool(bar["correct"]) for bar in accepted)
        curve.append(
            {
                "minimumConfidence": threshold,
                "eligibleBarCount": eligible_count,
                "acceptedBarCount": len(accepted),
                "correctBarCount": correct,
                "barPrecision": _ratio(correct, len(accepted)),
                "barCoverage": _ratio(len(accepted), eligible_count) or 0.0,
                "hasSupport": bool(accepted),
            }
        )
    return {
        **base,
        "totalBarCount": len(bars),
        "eligibleBarCount": eligible_count,
        "excludedMixedBarCount": excluded_mixed,
        "excludedUncoveredBarCount": excluded_uncovered,
        "predictionMixedBarCount": prediction_mixed,
        "predictionUncoveredBarCount": prediction_uncovered,
        "confidenceMissingBarCount": confidence_missing,
        "scorablePredictionBarCount": len(eligible_bars),
        "excludedPrefixDurationSeconds": float(grid.get("excludedPrefixDurationSeconds", 0.0)),
        "barEligibility": _ratio(eligible_count, len(bars)) or 0.0,
        "explicitBarGrid": grid["provenance"] == "explicit-bar-starts",
        "bars": bars,
        "curve": curve,
    }


def aggregate_bar_product_confidence(values: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Micro-average literal bar counts across track-level reports."""

    reports = list(values)
    available = [report for report in reports if report.get("available") is True]
    unavailable_count = len(reports) - len(available)
    provenance: dict[str, int] = {}
    for report in reports:
        grid = report.get("grid")
        name = str(grid.get("provenance") if isinstance(grid, Mapping) else "unavailable")
        provenance[name] = provenance.get(name, 0) + 1
    count_names = (
        "totalBarCount",
        "eligibleBarCount",
        "excludedMixedBarCount",
        "excludedUncoveredBarCount",
        "predictionMixedBarCount",
        "predictionUncoveredBarCount",
        "confidenceMissingBarCount",
        "scorablePredictionBarCount",
    )
    counts = {name: sum(int(report.get(name, 0)) for report in available) for name in count_names}
    excluded_prefix_duration = sum(float(report.get("excludedPrefixDurationSeconds", 0.0)) for report in available)
    excluded_prefix_track_count = sum(
        float(report.get("excludedPrefixDurationSeconds", 0.0)) > _EPSILON for report in available
    )
    if not available:
        curve: list[dict[str, Any]] = []
    else:
        threshold_sets = [
            tuple(float(point["minimumConfidence"]) for point in report.get("curve", [])) for report in available
        ]
        if not threshold_sets[0] or any(values != threshold_sets[0] for values in threshold_sets[1:]):
            raise ValueError("Available bar-product reports must use the same confidence thresholds.")
        curves = [{float(point["minimumConfidence"]): point for point in report["curve"]} for report in available]
        curve = []
        for threshold in threshold_sets[0]:
            eligible = sum(int(points[threshold]["eligibleBarCount"]) for points in curves)
            accepted = sum(int(points[threshold]["acceptedBarCount"]) for points in curves)
            correct = sum(int(points[threshold]["correctBarCount"]) for points in curves)
            if correct > accepted or accepted > eligible:
                raise ValueError("Bar-product curve counts must satisfy correct <= accepted <= eligible.")
            curve.append(
                {
                    "minimumConfidence": threshold,
                    "eligibleBarCount": eligible,
                    "acceptedBarCount": accepted,
                    "correctBarCount": correct,
                    "barPrecision": _ratio(correct, accepted),
                    "barCoverage": _ratio(accepted, eligible) or 0.0,
                    "hasSupport": accepted > 0,
                }
            )
    return {
        "schemaVersion": "chord_bar_product_confidence_aggregate_v1",
        "available": bool(reports) and unavailable_count == 0,
        "partiallyAvailable": bool(available) and unavailable_count > 0,
        "trackCount": len(reports),
        "availableTrackCount": len(available),
        "unavailableTrackCount": unavailable_count,
        "gridProvenanceTrackCounts": dict(sorted(provenance.items())),
        "explicitBarGridOnly": bool(reports)
        and unavailable_count == 0
        and provenance == {"explicit-bar-starts": len(reports)},
        "excludedPrefixDurationSeconds": excluded_prefix_duration,
        "excludedPrefixTrackCount": excluded_prefix_track_count,
        **counts,
        "barEligibility": _ratio(counts["eligibleBarCount"], counts["totalBarCount"]) or 0.0,
        "curve": curve,
    }


# Short aliases keep benchmark wiring readable without changing the explicit
# schema names above.
score_bar_products = score_bar_product_confidence
aggregate_bar_product_scores = aggregate_bar_product_confidence
