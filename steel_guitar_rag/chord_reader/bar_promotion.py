"""Frozen literal-bar operating points for the Play Along chord product.

Schema v1 is retained only for explicitly legacy benchmark reports. Schema v2
is the certification path: it requires clean, content-addressed provenance,
literal bar timing, meaningful support on three real corpora, and a one-sided
95% Wilson lower confidence bound at or above the advertised 98% precision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any


BAR_PRODUCT_PRECISION_TARGET = 0.98
LEGACY_BENCHMARK_REPORT_SCHEMA = "chord_benchmark_report_v1"
BENCHMARK_REPORT_SCHEMA = "chord_benchmark_report_v2"
BENCHMARK_PROVENANCE_SCHEMA = "chord_benchmark_provenance_v2"

LEGACY_BAR_OPERATING_POINT_SCHEMA = "chord_bar_product_operating_point_v1"
LEGACY_BAR_OPERATING_POINT_EVALUATION_SCHEMA = "chord_bar_product_operating_point_evaluation_v1"
LEGACY_BAR_OPERATING_POINT_SELECTION = "highest-coverage-calibration-threshold-meeting-literal-bar-target"
MINIMUM_CALIBRATION_ACCEPTED_BARS = 30

BAR_OPERATING_POINT_SCHEMA = "chord_bar_product_operating_point_v2"
BAR_OPERATING_POINT_EVALUATION_SCHEMA = "chord_bar_product_operating_point_evaluation_v2"
BAR_OPERATING_POINT_SELECTION = "highest-coverage-calibration-threshold-meeting-certified-literal-bar-policy-v2"

# These values define the certification claim. Changing one creates a new
# policy/schema, not a caller option.
CERTIFICATION_CONFIDENCE_LEVEL = 0.95
CERTIFICATION_WILSON_Z = 1.6448536269514722
CERTIFICATION_MINIMUM_ACCEPTED_BARS = 150
CERTIFICATION_MINIMUM_BAR_COVERAGE = 0.50
CERTIFICATION_MINIMUM_BAR_ELIGIBILITY = 0.75
CERTIFICATION_REAL_CORPORA = ("aam", "guitarset", "idmt_guitar")
CERTIFICATION_MINIMUM_REAL_CORPUS_ACCEPTED_BARS = 30
CERTIFICATION_MINIMUM_REAL_CORPUS_BAR_COVERAGE = 0.25
CERTIFICATION_MINIMUM_REAL_CORPUS_PRECISION = 0.98

_HASH_FIELDS = (
    "trackSetSha256",
    "referenceSetSha256",
    "predictionSetSha256",
    "decoderConfigSha256",
    "timingSetSha256",
)
_CONFIRMATION_IDENTITY_FIELDS = (
    "trackSetSha256",
    "referenceSetSha256",
    "timingSetSha256",
)
_HEX = frozenset("0123456789abcdef")
_CLEAN_SOURCE_TREE_DIFF_SHA256 = hashlib.sha256(b"\0STATUS\0").hexdigest()


def canonical_sha256(value: Any) -> str:
    """Hash canonical JSON shared by benchmark generation and promotion gates."""

    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _tracks(values: Any) -> list[Mapping[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError("Benchmark tracks must be a sequence.")
    tracks: list[Mapping[str, Any]] = []
    identifiers: set[str] = set()
    for value in values:
        if not isinstance(value, Mapping):
            raise ValueError("Every benchmark track must be an object.")
        identifier = str(value.get("id") or "").strip()
        if not identifier:
            raise ValueError("Every benchmark track requires a nonempty id.")
        if identifier in identifiers:
            raise ValueError(f"Duplicate benchmark track id {identifier!r}.")
        identifiers.add(identifier)
        tracks.append(value)
    if not tracks:
        raise ValueError("A certification benchmark cannot have an empty track set.")
    return tracks


def benchmark_track_set_sha256(tracks: Sequence[Mapping[str, Any]]) -> str:
    """Hash sorted ``id``/``datasetId``/``split`` benchmark identities."""

    values = _tracks(tracks)
    identity: list[dict[str, str]] = []
    for track in values:
        identifier = str(track["id"])
        dataset_id = str(track.get("datasetId") or "").strip()
        split = str(track.get("split") or "").strip().lower()
        if not dataset_id or not split:
            raise ValueError(f"Benchmark track {identifier!r} requires datasetId and split.")
        identity.append({"id": identifier, "datasetId": dataset_id, "split": split})
    return canonical_sha256(sorted(identity, key=lambda value: value["id"]))


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest.")
    digest = value.strip()
    if len(digest) != 64 or any(character not in _HEX for character in digest):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest.")
    return digest


def benchmark_content_set_sha256(
    tracks: Sequence[Mapping[str, Any]],
    sha_field: str,
) -> str:
    """Hash sorted ``id``/``sha256`` identities for one track content field."""

    if sha_field not in {"referenceSha256", "predictionSha256", "timingSha256"}:
        raise ValueError("Unknown benchmark content hash field.")
    values = _tracks(tracks)
    identity = [
        {
            "id": str(track["id"]),
            "sha256": _sha256(track.get(sha_field), f"tracks.{sha_field}"),
        }
        for track in values
    ]
    return canonical_sha256(sorted(identity, key=lambda value: value["id"]))


def benchmark_evaluation_hashes(
    tracks: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Recompute all track-derived evaluation hashes for a v2 report."""

    return {
        "trackSetSha256": benchmark_track_set_sha256(tracks),
        "referenceSetSha256": benchmark_content_set_sha256(tracks, "referenceSha256"),
        "predictionSetSha256": benchmark_content_set_sha256(tracks, "predictionSha256"),
        "timingSetSha256": benchmark_content_set_sha256(tracks, "timingSha256"),
    }


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def one_sided_wilson_lower_bound(correct: int, total: int) -> float | None:
    """Return the frozen one-sided 95% Wilson lower confidence bound."""

    if (
        not isinstance(correct, int)
        or isinstance(correct, bool)
        or not isinstance(total, int)
        or isinstance(total, bool)
        or total <= 0
        or correct < 0
        or correct > total
    ):
        return None
    proportion = correct / total
    z_squared = CERTIFICATION_WILSON_Z**2
    denominator = 1 + z_squared / total
    center = proportion + z_squared / (2 * total)
    spread = CERTIFICATION_WILSON_Z * math.sqrt(proportion * (1 - proportion) / total + z_squared / (4 * total**2))
    return max(0.0, (center - spread) / denominator)


def _bar_report(report: Mapping[str, Any]) -> Mapping[str, Any]:
    aggregate = report.get("aggregate")
    if not isinstance(aggregate, Mapping):
        raise ValueError("Benchmark report is missing aggregate metrics.")
    bar = aggregate.get("barProductConfidence")
    if not isinstance(bar, Mapping):
        raise ValueError("Benchmark report is missing aggregate.barProductConfidence.")
    return bar


def _validated_bar_report(
    report: Mapping[str, Any],
    *,
    explicit_only: bool = False,
) -> Mapping[str, Any]:
    bar = _bar_report(report)
    if bar.get("available") is not True:
        raise ValueError("Literal-bar evaluation must be available for every track in the operating-point report.")
    track_count = bar.get("trackCount")
    available_count = bar.get("availableTrackCount")
    unavailable_count = bar.get("unavailableTrackCount")
    eligible = bar.get("eligibleBarCount")
    total = bar.get("totalBarCount")
    if (
        not isinstance(track_count, int)
        or isinstance(track_count, bool)
        or track_count <= 0
        or available_count != track_count
        or unavailable_count != 0
    ):
        raise ValueError("Literal-bar track availability accounting is incomplete.")
    if not isinstance(eligible, int) or isinstance(eligible, bool) or eligible <= 0:
        raise ValueError("Literal-bar evaluation has no eligible reference bars.")
    if total is not None and (not isinstance(total, int) or isinstance(total, bool) or total <= 0 or eligible > total):
        raise ValueError("Literal-bar total/eligible accounting is invalid.")
    if explicit_only:
        if not isinstance(total, int):
            raise ValueError("Certified literal-bar evaluation requires totalBarCount.")
        if bar.get("explicitBarGridOnly") is not True:
            raise ValueError("Certified literal-bar evaluation requires explicit bar grids only.")
        if bar.get("gridProvenanceTrackCounts") != {"explicit-bar-starts": track_count}:
            raise ValueError("Certified literal-bar grid provenance does not match every track.")
        eligibility = _finite(bar.get("barEligibility"))
        expected = eligible / total
        if eligibility is None or abs(eligibility - expected) > 1e-12:
            raise ValueError("Literal-bar eligibility does not match integer counts.")
        excluded_prefix = _finite(bar.get("excludedPrefixDurationSeconds"))
        if excluded_prefix is None or excluded_prefix < 0:
            raise ValueError("Literal-bar excluded-prefix disclosure is missing.")
    return bar


def _validated_point(point: Mapping[str, Any], *, eligible: int) -> dict[str, Any]:
    threshold = _finite(point.get("minimumConfidence"))
    accepted = point.get("acceptedBarCount")
    correct = point.get("correctBarCount")
    precision = _finite(point.get("barPrecision"))
    coverage = _finite(point.get("barCoverage"))
    if threshold is None or not 0 <= threshold <= 1:
        raise ValueError("Bar curve contains an invalid minimumConfidence.")
    if not isinstance(accepted, int) or isinstance(accepted, bool) or not 0 <= accepted <= eligible:
        raise ValueError("Bar curve contains an invalid acceptedBarCount.")
    if not isinstance(correct, int) or isinstance(correct, bool) or not 0 <= correct <= accepted:
        raise ValueError("Bar curve contains an invalid correctBarCount.")
    expected_precision = correct / accepted if accepted else None
    if expected_precision is None:
        if point.get("barPrecision") is not None:
            raise ValueError("A zero-support bar point must have null barPrecision.")
    elif precision is None or abs(precision - expected_precision) > 1e-12:
        raise ValueError("Bar curve precision does not match its integer counts.")
    expected_coverage = accepted / eligible
    if coverage is None or abs(coverage - expected_coverage) > 1e-12:
        raise ValueError("Bar curve coverage does not match its integer counts.")
    return {
        "minimumConfidence": threshold,
        "eligibleBarCount": eligible,
        "acceptedBarCount": accepted,
        "correctBarCount": correct,
        "barPrecision": expected_precision,
        "barCoverage": expected_coverage,
        "wilsonLowerBound95": one_sided_wilson_lower_bound(correct, accepted),
    }


def _validated_curve(bar: Mapping[str, Any]) -> dict[float, dict[str, Any]]:
    curve = bar.get("curve")
    if not isinstance(curve, list) or not curve:
        raise ValueError("Literal-bar confidence curve is missing or empty.")
    eligible = int(bar["eligibleBarCount"])
    points: dict[float, dict[str, Any]] = {}
    for raw in curve:
        if not isinstance(raw, Mapping):
            raise ValueError("Literal-bar curve contains a non-object point.")
        point = _validated_point(raw, eligible=eligible)
        threshold = float(point["minimumConfidence"])
        if threshold in points:
            raise ValueError("Literal-bar curve contains duplicate thresholds.")
        points[threshold] = point
    return points


def _validated_provenance(report: Mapping[str, Any]) -> dict[str, Any]:
    if report.get("schemaVersion") != BENCHMARK_REPORT_SCHEMA:
        raise ValueError("Certified bar evaluation requires chord_benchmark_report_v2.")
    if report.get("promotionEligible") is not True or report.get("oracleTimingUsed") is not False:
        raise ValueError("Certified reports must be promotion eligible and use no oracle timing.")
    provenance = report.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("Benchmark v2 report is missing provenance.")
    provenance_schema = provenance.get("schemaVersion")
    if provenance_schema != BENCHMARK_PROVENANCE_SCHEMA:
        raise ValueError("Benchmark provenance schema is invalid.")

    source = provenance.get("sourceTree")
    if not isinstance(source, Mapping):
        raise ValueError("Benchmark provenance is missing sourceTree.")
    revision = str(source.get("revision") or "")
    if len(revision) != 40 or any(character not in _HEX for character in revision):
        raise ValueError("sourceTree.revision must be a lowercase Git SHA-1.")
    if source.get("dirty") is not False:
        raise ValueError("Certification requires a clean source tree.")
    diff_sha256 = _sha256(source.get("diffSha256"), "sourceTree.diffSha256")
    if diff_sha256 != _CLEAN_SOURCE_TREE_DIFF_SHA256:
        raise ValueError("A clean source tree must have the canonical empty diff hash.")
    if report.get("gitRevision") != revision:
        raise ValueError("gitRevision does not match sourceTree.revision.")

    model = provenance.get("model")
    if not isinstance(model, Mapping):
        raise ValueError("Benchmark provenance is missing model.")
    _sha256(model.get("sha256"), "model.sha256")
    model_bytes = model.get("bytes")
    if not isinstance(model_bytes, int) or isinstance(model_bytes, bool) or model_bytes <= 0:
        raise ValueError("model.bytes must be a positive integer.")

    cache = provenance.get("cache")
    if not isinstance(cache, Mapping):
        raise ValueError("Benchmark provenance is missing cache.")
    _sha256(cache.get("manifestSha256"), "cache.manifestSha256")
    _sha256(cache.get("featureSpecSha256"), "cache.featureSpecSha256")
    protocol = cache.get("splitProtocol")
    if not isinstance(protocol, Mapping):
        raise ValueError("Benchmark provenance is missing cache.splitProtocol.")
    for name in (
        "outputManifestSha256",
        "assignmentSha256",
        "calibrationSetSha256",
        "barEligibleSetSha256",
    ):
        _sha256(protocol.get(name), f"cache.splitProtocol.{name}")

    evaluation = provenance.get("evaluation")
    if not isinstance(evaluation, Mapping):
        raise ValueError("Benchmark provenance is missing evaluation.")
    for name in _HASH_FIELDS:
        _sha256(evaluation.get(name), f"evaluation.{name}")
    tracks = _tracks(report.get("tracks"))
    report_split = str(report.get("split") or "").strip().lower()
    if not report_split:
        raise ValueError("Benchmark report is missing split.")
    if any(str(track.get("split") or "").strip().lower() != report_split for track in tracks):
        raise ValueError("Every benchmark track must match the report split.")
    recomputed = benchmark_evaluation_hashes(tracks)
    for name, digest in recomputed.items():
        if evaluation.get(name) != digest:
            raise ValueError(f"evaluation.{name} does not match benchmark tracks.")

    return {
        "schemaVersion": provenance_schema,
        "sourceTree": dict(source),
        "model": dict(model),
        "cache": {
            "manifestSha256": cache["manifestSha256"],
            "featureSpecSha256": cache["featureSpecSha256"],
            "splitProtocol": dict(protocol),
        },
        "evaluation": dict(evaluation),
    }


def validate_benchmark_v2_provenance(report: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize certification provenance for external gate wiring."""

    return _validated_provenance(report)


def _validated_certification_report(
    report: Mapping[str, Any],
) -> tuple[Mapping[str, Any], dict[str, Any], dict[str, Mapping[str, Any]]]:
    provenance = _validated_provenance(report)
    bar = _validated_bar_report(report, explicit_only=True)
    tracks = _tracks(report.get("tracks"))
    if bar.get("trackCount") != len(tracks):
        raise ValueError("Literal-bar trackCount does not match benchmark tracks.")
    aggregate_curve = _validated_curve(bar)
    curve_sums = {threshold: {"acceptedBarCount": 0, "correctBarCount": 0} for threshold in aggregate_curve}
    track_counts = {"totalBarCount": 0, "eligibleBarCount": 0}
    track_prefix = 0.0
    corpus_counts: dict[str, dict[str, int]] = {}
    corpus_curve_sums: dict[str, dict[float, dict[str, int]]] = {}
    for track in tracks:
        metrics = track.get("metrics")
        track_bar = metrics.get("barProductConfidence") if isinstance(metrics, Mapping) else None
        if not isinstance(track_bar, Mapping) or track_bar.get("available") is not True:
            raise ValueError("Every certified track requires literal-bar metrics.")
        grid = track_bar.get("grid")
        if (
            track_bar.get("explicitBarGrid") is not True
            or not isinstance(grid, Mapping)
            or grid.get("provenance") != "explicit-bar-starts"
        ):
            raise ValueError("Every certified track requires explicit bar-grid provenance.")
        total = track_bar.get("totalBarCount")
        eligible = track_bar.get("eligibleBarCount")
        excluded_prefix = _finite(track_bar.get("excludedPrefixDurationSeconds"))
        starts = grid.get("barStartsSeconds")
        bars = track_bar.get("bars")
        if (
            not isinstance(total, int)
            or isinstance(total, bool)
            or total <= 0
            or not isinstance(eligible, int)
            or isinstance(eligible, bool)
            or not 0 <= eligible <= total
            or excluded_prefix is None
            or excluded_prefix < 0
            or _finite(grid.get("excludedPrefixDurationSeconds")) != excluded_prefix
            or not isinstance(starts, Sequence)
            or isinstance(starts, (str, bytes))
            or len(starts) != total
            or grid.get("barCount") != total
            or not isinstance(bars, Sequence)
            or isinstance(bars, (str, bytes))
            or len(bars) != total
        ):
            raise ValueError("Certified track bar accounting is invalid.")
        if excluded_prefix > 1e-12 and (
            grid.get("timingProvenanceStatus") != "explicit"
            or grid.get("prefixExclusionCertified") is not True
            or _finite(grid.get("gridStartSeconds")) != excluded_prefix
        ):
            raise ValueError("Positive bar-grid prefixes require explicit timing certification.")
        eligible_bars = [item for item in bars if isinstance(item, Mapping) and item.get("eligible") is True]
        if len(eligible_bars) != eligible or any(not isinstance(item, Mapping) for item in bars):
            raise ValueError("Certified track eligible bars do not match track counts.")
        scorable_bars = [
            item
            for item in eligible_bars
            if _finite(item.get("productConfidence")) is not None
            and 0 <= float(item["productConfidence"]) <= 1
            and isinstance(item.get("correct"), bool)
        ]
        if track_bar.get("scorablePredictionBarCount") != len(scorable_bars):
            raise ValueError("Certified track scorable-bar count does not match its bars.")
        track_curve = _validated_curve(track_bar)
        if set(track_curve) != set(aggregate_curve):
            raise ValueError("Certified track and aggregate bar thresholds differ.")
        corpus = str(track.get("datasetId") or "")
        corpus_sums = corpus_curve_sums.setdefault(
            corpus,
            {threshold: {"acceptedBarCount": 0, "correctBarCount": 0} for threshold in aggregate_curve},
        )
        for threshold, point in track_curve.items():
            accepted_bars = [item for item in scorable_bars if float(item["productConfidence"]) + 1e-9 >= threshold]
            correct_count = sum(item["correct"] is True for item in accepted_bars)
            if point["acceptedBarCount"] != len(accepted_bars) or point["correctBarCount"] != correct_count:
                raise ValueError("Certified track bar curve does not match its bars.")
            curve_sums[threshold]["acceptedBarCount"] += len(accepted_bars)
            curve_sums[threshold]["correctBarCount"] += correct_count
            corpus_sums[threshold]["acceptedBarCount"] += len(accepted_bars)
            corpus_sums[threshold]["correctBarCount"] += correct_count
        track_counts["totalBarCount"] += total
        track_counts["eligibleBarCount"] += eligible
        track_prefix += excluded_prefix
        counts = corpus_counts.setdefault(corpus, {"totalBarCount": 0, "eligibleBarCount": 0})
        counts["totalBarCount"] += total
        counts["eligibleBarCount"] += eligible
    if any(bar.get(name) != value for name, value in track_counts.items()) or not math.isclose(
        float(bar["excludedPrefixDurationSeconds"]),
        track_prefix,
        rel_tol=0,
        abs_tol=1e-9,
    ):
        raise ValueError("Aggregate literal-bar accounting does not match track rows.")
    if any(
        aggregate_curve[threshold][name] != value
        for threshold, counts in curve_sums.items()
        for name, value in counts.items()
    ):
        raise ValueError("Aggregate literal-bar curve does not match track rows.")
    if float(bar["barEligibility"]) + 1e-12 < CERTIFICATION_MINIMUM_BAR_ELIGIBILITY:
        raise ValueError("Literal-bar eligibility is below the certification minimum.")

    strata = report.get("strata")
    if not isinstance(strata, Mapping):
        raise ValueError("Certified report is missing per-corpus strata.")
    real: dict[str, Mapping[str, Any]] = {}
    for corpus in CERTIFICATION_REAL_CORPORA:
        stratum = strata.get(corpus)
        if not isinstance(stratum, Mapping):
            raise ValueError(f"Certified report is missing required {corpus!r} support.")
        corpus_bar = _validated_bar_report({"aggregate": stratum}, explicit_only=True)
        expected_tracks = sum(str(track.get("datasetId") or "") == corpus for track in tracks)
        if corpus_bar.get("trackCount") != expected_tracks or expected_tracks <= 0:
            raise ValueError(f"{corpus!r} bar support does not match benchmark tracks.")
        if any(corpus_bar.get(name) != corpus_counts[corpus][name] for name in ("totalBarCount", "eligibleBarCount")):
            raise ValueError(f"{corpus!r} bar counts do not match benchmark tracks.")
        corpus_curve = _validated_curve(corpus_bar)
        if set(corpus_curve) != set(aggregate_curve) or any(
            corpus_curve[threshold][name] != value
            for threshold, counts in corpus_curve_sums[corpus].items()
            for name, value in counts.items()
        ):
            raise ValueError(f"{corpus!r} bar curve does not match benchmark tracks.")
        real[corpus] = corpus_bar
    return bar, provenance, real


def _certification_policy() -> dict[str, Any]:
    return {
        "confidenceMethod": "one-sided-wilson",
        "confidenceLevel": CERTIFICATION_CONFIDENCE_LEVEL,
        "requiredWilsonLowerBound": BAR_PRODUCT_PRECISION_TARGET,
        "minimumAcceptedBars": CERTIFICATION_MINIMUM_ACCEPTED_BARS,
        "minimumBarCoverage": CERTIFICATION_MINIMUM_BAR_COVERAGE,
        "minimumBarEligibility": CERTIFICATION_MINIMUM_BAR_ELIGIBILITY,
        "explicitBarGridsOnly": True,
        "realCorpusSupport": {
            "requiredCorpora": list(CERTIFICATION_REAL_CORPORA),
            "minimumAcceptedBarsPerCorpus": CERTIFICATION_MINIMUM_REAL_CORPUS_ACCEPTED_BARS,
            "minimumBarCoveragePerCorpus": CERTIFICATION_MINIMUM_REAL_CORPUS_BAR_COVERAGE,
            "minimumEmpiricalPrecisionPerCorpus": CERTIFICATION_MINIMUM_REAL_CORPUS_PRECISION,
        },
    }


def _point_passes_certification(point: Mapping[str, Any]) -> bool:
    precision = point.get("barPrecision")
    lower = point.get("wilsonLowerBound95")
    return (
        int(point["acceptedBarCount"]) >= CERTIFICATION_MINIMUM_ACCEPTED_BARS
        and float(point["barCoverage"]) + 1e-12 >= CERTIFICATION_MINIMUM_BAR_COVERAGE
        and precision is not None
        and float(precision) + 1e-12 >= BAR_PRODUCT_PRECISION_TARGET
        and lower is not None
        and float(lower) + 1e-12 >= BAR_PRODUCT_PRECISION_TARGET
    )


def _real_corpus_point(
    corpus: str,
    bar: Mapping[str, Any],
    threshold: float,
) -> dict[str, Any]:
    points = _validated_curve(bar)
    if threshold not in points:
        raise ValueError(f"{corpus!r} bar curve is missing threshold {threshold}.")
    point = {"datasetId": corpus, **points[threshold]}
    point["supportPassed"] = (
        int(point["acceptedBarCount"]) >= CERTIFICATION_MINIMUM_REAL_CORPUS_ACCEPTED_BARS
        and float(point["barCoverage"]) + 1e-12 >= CERTIFICATION_MINIMUM_REAL_CORPUS_BAR_COVERAGE
        and point["barPrecision"] is not None
        and float(point["barPrecision"]) + 1e-12 >= CERTIFICATION_MINIMUM_REAL_CORPUS_PRECISION
    )
    return point


def _real_support_passes(point: Mapping[str, Any], corpus: str) -> bool:
    eligible = point.get("eligibleBarCount")
    if point.get("datasetId") != corpus or not isinstance(eligible, int) or isinstance(eligible, bool) or eligible <= 0:
        return False
    try:
        validated = _validated_point(point, eligible=eligible)
    except ValueError:
        return False
    return (
        point.get("supportPassed") is True
        and point.get("wilsonLowerBound95") == validated["wilsonLowerBound95"]
        and int(validated["acceptedBarCount"]) >= CERTIFICATION_MINIMUM_REAL_CORPUS_ACCEPTED_BARS
        and float(validated["barCoverage"]) + 1e-12 >= CERTIFICATION_MINIMUM_REAL_CORPUS_BAR_COVERAGE
        and validated["barPrecision"] is not None
        and float(validated["barPrecision"]) + 1e-12 >= CERTIFICATION_MINIMUM_REAL_CORPUS_PRECISION
    )


def _certification_candidate(
    point: Mapping[str, Any],
    real: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    threshold = float(point["minimumConfidence"])
    real_points = {corpus: _real_corpus_point(corpus, bar, threshold) for corpus, bar in real.items()}
    return {
        **point,
        "overallPolicyPassed": _point_passes_certification(point),
        "realCorpusSupport": real_points,
        "realCorpusPolicyPassed": all(bool(value["supportPassed"]) for value in real_points.values()),
    }


def _validated_confirmation_identity(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("Certification calibration requires a pre-sealed confirmation identity.")
    unexpected = set(value) - set(_CONFIRMATION_IDENTITY_FIELDS)
    if unexpected:
        raise ValueError("Confirmation identity contains unsupported fields.")
    return {name: _sha256(value.get(name), f"confirmationIdentity.{name}") for name in _CONFIRMATION_IDENTITY_FIELDS}


def _calibrate_v1(
    calibration_report: Mapping[str, Any],
    *,
    target_precision: float,
    minimum_accepted_bars: int | None,
) -> dict[str, Any]:
    if str(calibration_report.get("split") or "").strip().lower() != "calibration":
        raise ValueError("Literal-bar operating points may only be selected on a dedicated calibration split.")
    target = _finite(target_precision)
    if target is None or not BAR_PRODUCT_PRECISION_TARGET <= target <= 1:
        raise ValueError(f"target_precision must be between {BAR_PRODUCT_PRECISION_TARGET:.2f} and 1.")
    minimum = MINIMUM_CALIBRATION_ACCEPTED_BARS if minimum_accepted_bars is None else minimum_accepted_bars
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum <= 0:
        raise ValueError("minimum_accepted_bars must be a positive integer.")
    bar = _validated_bar_report(calibration_report)
    curve = _validated_curve(bar)
    points = [
        point
        for point in curve.values()
        if int(point["acceptedBarCount"]) >= minimum
        and point["barPrecision"] is not None
        and float(point["barPrecision"]) + 1e-12 >= target
    ]
    if not points:
        raise ValueError(
            f"No calibration confidence threshold has sufficient literal-bar support at >= {target:.2%} precision."
        )
    selected = max(
        points,
        key=lambda point: (
            float(point["barCoverage"]),
            int(point["acceptedBarCount"]),
            -float(point["minimumConfidence"]),
        ),
    )
    return {
        "schemaVersion": LEGACY_BAR_OPERATING_POINT_SCHEMA,
        "frozen": True,
        "metric": "barPrecision",
        "metricUnit": "literal accepted bars",
        "targetPrecision": target,
        "minimumConfidence": selected["minimumConfidence"],
        "minimumCalibrationAcceptedBars": minimum,
        "selectionPolicy": LEGACY_BAR_OPERATING_POINT_SELECTION,
        "calibration": {
            "engine": calibration_report.get("engine"),
            "split": "calibration",
            "gitRevision": calibration_report.get("gitRevision"),
            **selected,
            "trackCount": bar["trackCount"],
            "curvePointCount": len(curve),
        },
    }


def _calibrate_v2(
    calibration_report: Mapping[str, Any],
    *,
    target_precision: float,
    minimum_accepted_bars: int | None,
    confirmation_identity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if str(calibration_report.get("split") or "").strip().lower() != "calibration":
        raise ValueError("Literal-bar operating points may only be selected on a dedicated calibration split.")
    if target_precision != BAR_PRODUCT_PRECISION_TARGET:
        raise ValueError("The v2 certification precision target is frozen at 0.98.")
    if minimum_accepted_bars not in {None, CERTIFICATION_MINIMUM_ACCEPTED_BARS}:
        raise ValueError("The v2 certification minimum accepted-bar count is frozen.")
    confirmation = _validated_confirmation_identity(confirmation_identity)
    bar, provenance, real = _validated_certification_report(calibration_report)
    evaluation = provenance["evaluation"]
    protocol = provenance["cache"]["splitProtocol"]
    if evaluation["trackSetSha256"] != protocol["barEligibleSetSha256"]:
        raise ValueError("Calibration track set does not match the split protocol bar-eligible set.")
    if any(confirmation[name] == evaluation[name] for name in _CONFIRMATION_IDENTITY_FIELDS):
        raise ValueError("Calibration and confirmation identities must be disjoint.")

    curve = _validated_curve(bar)
    candidates = [_certification_candidate(point, real) for point in curve.values()]
    supported = [point for point in candidates if point["overallPolicyPassed"] and point["realCorpusPolicyPassed"]]
    if not supported:
        raise ValueError(
            "No calibration threshold satisfies the frozen 98% literal-bar "
            "confidence, coverage, eligibility, and real-corpus support policy."
        )
    selected = max(
        supported,
        key=lambda point: (
            float(point["barCoverage"]),
            int(point["acceptedBarCount"]),
            -float(point["minimumConfidence"]),
        ),
    )
    return {
        "schemaVersion": BAR_OPERATING_POINT_SCHEMA,
        "frozen": True,
        "metric": "barPrecision",
        "metricUnit": "literal accepted bars on explicit reference bar grids",
        "targetPrecision": BAR_PRODUCT_PRECISION_TARGET,
        "minimumConfidence": selected["minimumConfidence"],
        "selectionPolicy": BAR_OPERATING_POINT_SELECTION,
        "certificationPolicy": _certification_policy(),
        "identity": {
            "sourceTree": provenance["sourceTree"],
            "model": provenance["model"],
            "cache": provenance["cache"],
            "decoderConfigSha256": evaluation["decoderConfigSha256"],
        },
        "calibration": {
            "engine": calibration_report.get("engine"),
            "split": "calibration",
            "provenance": provenance,
            "reportSha256": canonical_sha256(calibration_report),
            "trackCount": bar["trackCount"],
            "totalBarCount": bar["totalBarCount"],
            "excludedPrefixDurationSeconds": bar["excludedPrefixDurationSeconds"],
            "barEligibility": bar["barEligibility"],
            "curvePointCount": len(curve),
            **selected,
        },
        "confirmationExpected": confirmation,
    }


def calibrate_bar_product_operating_point(
    calibration_report: Mapping[str, Any],
    *,
    target_precision: float = BAR_PRODUCT_PRECISION_TARGET,
    minimum_accepted_bars: int | None = None,
    confirmation_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze a bar threshold, dispatching only on an explicit report schema."""

    schema = calibration_report.get("schemaVersion")
    if schema == LEGACY_BENCHMARK_REPORT_SCHEMA:
        if confirmation_identity is not None:
            raise ValueError("Legacy calibration does not accept confirmation_identity.")
        return _calibrate_v1(
            calibration_report,
            target_precision=target_precision,
            minimum_accepted_bars=minimum_accepted_bars,
        )
    if schema == BENCHMARK_REPORT_SCHEMA:
        return _calibrate_v2(
            calibration_report,
            target_precision=target_precision,
            minimum_accepted_bars=minimum_accepted_bars,
            confirmation_identity=confirmation_identity,
        )
    raise ValueError("Unsupported benchmark schema for bar calibration.")


def _evaluate_v1(
    sealed_report: Mapping[str, Any],
    operating_point: Mapping[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []
    target = _finite(operating_point.get("targetPrecision"))
    threshold = _finite(operating_point.get("minimumConfidence"))
    if operating_point.get("schemaVersion") != LEGACY_BAR_OPERATING_POINT_SCHEMA:
        reasons.append("bar-operating-point-schema-mismatch")
    if operating_point.get("frozen") is not True:
        reasons.append("bar-operating-point-not-frozen")
    if operating_point.get("metric") != "barPrecision":
        reasons.append("bar-operating-point-metric-mismatch")
    if operating_point.get("selectionPolicy") != LEGACY_BAR_OPERATING_POINT_SELECTION:
        reasons.append("bar-operating-point-selection-policy-mismatch")
    if target is None or not BAR_PRODUCT_PRECISION_TARGET <= target <= 1:
        reasons.append("bar-operating-point-target-invalid")
    if threshold is None or not 0 <= threshold <= 1:
        reasons.append("bar-operating-point-threshold-invalid")
    calibration = operating_point.get("calibration")
    if not isinstance(calibration, Mapping) or calibration.get("split") != "calibration":
        reasons.append("bar-operating-point-calibration-provenance-missing")
    split = str(sealed_report.get("split") or "").strip().lower()
    if not split:
        reasons.append("sealed-split-missing")
    elif split in {"dev", "development", "val", "validation", "calibration"}:
        reasons.append("sealed-report-is-not-confirmation-data")

    bar: Mapping[str, Any] | None = None
    try:
        bar = _validated_bar_report(sealed_report)
    except ValueError:
        reasons.append("sealed-bar-report-incomplete")
    selected: dict[str, Any] | None = None
    matches = 0
    if bar is not None and threshold is not None:
        try:
            curve = _validated_curve(bar)
        except ValueError:
            reasons.append("sealed-bar-curve-malformed")
        else:
            if threshold in curve:
                matches = 1
                selected = curve[threshold]
            else:
                reasons.append("sealed-bar-threshold-missing")
    accepted = int(selected["acceptedBarCount"]) if selected else 0
    correct = int(selected["correctBarCount"]) if selected else 0
    precision = selected["barPrecision"] if selected else None
    coverage = float(selected["barCoverage"]) if selected else 0.0
    if selected is not None and accepted == 0:
        reasons.append("sealed-bar-zero-support")
    precision_passed = precision is not None and target is not None and float(precision) + 1e-12 >= float(target)
    if selected is not None and accepted > 0 and not precision_passed:
        reasons.append("sealed-bar-precision-below-target")
    reasons = list(dict.fromkeys(reasons))
    return {
        "schemaVersion": LEGACY_BAR_OPERATING_POINT_EVALUATION_SCHEMA,
        "passed": not reasons and precision_passed,
        "targetPrecision": target,
        "minimumConfidence": threshold,
        "thresholdMatched": matches == 1,
        "barEvaluationComplete": bar is not None,
        "supportAvailable": accepted > 0,
        "barPrecision": precision,
        "acceptedBarCount": accepted,
        "correctBarCount": correct,
        "barCoverage": coverage,
        "eligibleBarCount": int(bar["eligibleBarCount"]) if bar is not None else 0,
        "trackCount": int(bar["trackCount"]) if bar is not None else 0,
        "failureReasons": reasons,
    }


def _validate_v2_operating_point(
    operating_point: Mapping[str, Any],
) -> tuple[list[str], float | None, Mapping[str, Any] | None]:
    reasons: list[str] = []
    threshold = _finite(operating_point.get("minimumConfidence"))
    if operating_point.get("schemaVersion") != BAR_OPERATING_POINT_SCHEMA:
        reasons.append("bar-operating-point-schema-mismatch")
    if operating_point.get("frozen") is not True:
        reasons.append("bar-operating-point-not-frozen")
    if operating_point.get("metric") != "barPrecision":
        reasons.append("bar-operating-point-metric-mismatch")
    if operating_point.get("targetPrecision") != BAR_PRODUCT_PRECISION_TARGET:
        reasons.append("bar-operating-point-target-invalid")
    if operating_point.get("selectionPolicy") != BAR_OPERATING_POINT_SELECTION:
        reasons.append("bar-operating-point-selection-policy-mismatch")
    if operating_point.get("certificationPolicy") != _certification_policy():
        reasons.append("bar-operating-point-certification-policy-mismatch")
    if threshold is None or not 0 <= threshold <= 1:
        reasons.append("bar-operating-point-threshold-invalid")
    identity = operating_point.get("identity")
    if not isinstance(identity, Mapping):
        reasons.append("bar-operating-point-identity-missing")
    calibration = operating_point.get("calibration")
    if not isinstance(calibration, Mapping) or calibration.get("split") != "calibration":
        reasons.append("bar-operating-point-calibration-provenance-missing")
        calibration = None
    elif calibration.get("minimumConfidence") != threshold:
        reasons.append("bar-operating-point-calibration-threshold-mismatch")
    else:
        accepted = calibration.get("acceptedBarCount")
        correct = calibration.get("correctBarCount")
        eligible = calibration.get("eligibleBarCount")
        validated_calibration: dict[str, Any] | None = None
        if (
            not isinstance(accepted, int)
            or isinstance(accepted, bool)
            or not isinstance(correct, int)
            or isinstance(correct, bool)
            or not isinstance(eligible, int)
            or isinstance(eligible, bool)
        ):
            reasons.append("bar-operating-point-calibration-counts-invalid")
        else:
            try:
                validated_calibration = _validated_point(calibration, eligible=eligible)
            except ValueError:
                reasons.append("bar-operating-point-calibration-counts-invalid")
            if validated_calibration is not None and any(
                calibration.get(name) != validated_calibration.get(name)
                for name in (
                    "minimumConfidence",
                    "eligibleBarCount",
                    "acceptedBarCount",
                    "correctBarCount",
                    "barPrecision",
                    "barCoverage",
                    "wilsonLowerBound95",
                )
            ):
                reasons.append("bar-operating-point-calibration-counts-invalid")
        if validated_calibration is not None:
            if one_sided_wilson_lower_bound(correct, accepted) != calibration.get("wilsonLowerBound95"):
                reasons.append("bar-operating-point-calibration-wilson-mismatch")
            elif not _point_passes_certification(calibration):
                reasons.append("bar-operating-point-calibration-policy-failed")
        support = calibration.get("realCorpusSupport")
        if not isinstance(support, Mapping) or set(support) != set(CERTIFICATION_REAL_CORPORA):
            reasons.append("bar-operating-point-calibration-real-support-invalid")
        elif not all(
            isinstance(support[corpus], Mapping) and _real_support_passes(support[corpus], corpus)
            for corpus in CERTIFICATION_REAL_CORPORA
        ):
            reasons.append("bar-operating-point-calibration-real-support-failed")
        calibration_provenance = calibration.get("provenance")
        calibration_evaluation = (
            calibration_provenance.get("evaluation") if isinstance(calibration_provenance, Mapping) else None
        )
        calibration_cache = calibration_provenance.get("cache") if isinstance(calibration_provenance, Mapping) else None
        calibration_protocol = (
            calibration_cache.get("splitProtocol") if isinstance(calibration_cache, Mapping) else None
        )
        try:
            _sha256(calibration.get("reportSha256"), "calibration.reportSha256")
            if not isinstance(calibration_evaluation, Mapping):
                raise ValueError("calibration evaluation missing")
            for name in _HASH_FIELDS:
                _sha256(
                    calibration_evaluation.get(name),
                    f"calibration.provenance.evaluation.{name}",
                )
            if not isinstance(calibration_protocol, Mapping):
                raise ValueError("calibration split protocol missing")
            if calibration_evaluation.get("trackSetSha256") != calibration_protocol.get("barEligibleSetSha256"):
                raise ValueError("calibration bar-eligible identity mismatch")
        except ValueError:
            reasons.append("bar-operating-point-calibration-provenance-invalid")
        if isinstance(identity, Mapping) and isinstance(calibration_provenance, Mapping):
            if any(
                identity.get(name) != calibration_provenance.get(name) for name in ("sourceTree", "model", "cache")
            ) or (
                isinstance(calibration_evaluation, Mapping)
                and identity.get("decoderConfigSha256") != calibration_evaluation.get("decoderConfigSha256")
            ):
                reasons.append("bar-operating-point-calibration-identity-mismatch")
    try:
        confirmation = _validated_confirmation_identity(operating_point.get("confirmationExpected"))
    except ValueError:
        reasons.append("bar-operating-point-confirmation-identity-invalid")
    else:
        if (
            isinstance(calibration, Mapping)
            and isinstance(calibration.get("provenance"), Mapping)
            and isinstance(calibration["provenance"].get("evaluation"), Mapping)
            and any(
                confirmation[name] == calibration["provenance"]["evaluation"].get(name)
                for name in _CONFIRMATION_IDENTITY_FIELDS
            )
        ):
            reasons.append("bar-operating-point-calibration-confirmation-not-disjoint")
    return list(dict.fromkeys(reasons)), threshold, calibration


def _evaluate_v2(
    sealed_report: Mapping[str, Any],
    operating_point: Mapping[str, Any],
) -> dict[str, Any]:
    reasons, threshold, calibration = _validate_v2_operating_point(operating_point)
    split = str(sealed_report.get("split") or "").strip().lower()
    if split != "confirmation":
        reasons.append("sealed-report-is-not-confirmation-split")

    bar: Mapping[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    real: dict[str, Mapping[str, Any]] = {}
    try:
        bar, provenance, real = _validated_certification_report(sealed_report)
    except ValueError as exc:
        reasons.append(f"sealed-certification-report-invalid:{exc}")

    selected: dict[str, Any] | None = None
    real_points: dict[str, Any] = {}
    if bar is not None and threshold is not None:
        try:
            points = _validated_curve(bar)
            if threshold not in points:
                reasons.append("sealed-bar-threshold-missing")
            else:
                selected = _certification_candidate(points[threshold], real)
                real_points = dict(selected["realCorpusSupport"])
        except ValueError:
            reasons.append("sealed-bar-operating-point-malformed")

    expected: dict[str, str] | None = None
    try:
        expected = _validated_confirmation_identity(operating_point.get("confirmationExpected"))
    except ValueError:
        pass
    if provenance is not None and expected is not None:
        evaluation = provenance["evaluation"]
        for name, digest in expected.items():
            if evaluation.get(name) != digest:
                reasons.append(f"confirmation-{name}-mismatch")
        identity = operating_point.get("identity")
        if not isinstance(identity, Mapping):
            reasons.append("bar-operating-point-identity-missing")
        else:
            for name in ("sourceTree", "model", "cache"):
                if identity.get(name) != provenance.get(name):
                    reasons.append(f"confirmation-{name}-mismatch")
            if identity.get("decoderConfigSha256") != evaluation.get("decoderConfigSha256"):
                reasons.append("confirmation-decoderConfigSha256-mismatch")
        if calibration is not None:
            calibration_provenance = calibration.get("provenance")
            if not isinstance(calibration_provenance, Mapping):
                reasons.append("calibration-provenance-missing")
            else:
                calibration_evaluation = calibration_provenance.get("evaluation")
                if not isinstance(calibration_evaluation, Mapping):
                    reasons.append("calibration-evaluation-provenance-missing")
                elif evaluation.get("predictionSetSha256") == calibration_evaluation.get("predictionSetSha256"):
                    reasons.append("confirmation-prediction-set-reuses-calibration")

    if selected is not None:
        if not selected["overallPolicyPassed"]:
            if int(selected["acceptedBarCount"]) < CERTIFICATION_MINIMUM_ACCEPTED_BARS:
                reasons.append("sealed-bar-insufficient-support")
            if float(selected["barCoverage"]) + 1e-12 < CERTIFICATION_MINIMUM_BAR_COVERAGE:
                reasons.append("sealed-bar-coverage-below-minimum")
            if (
                selected["barPrecision"] is None
                or float(selected["barPrecision"]) + 1e-12 < BAR_PRODUCT_PRECISION_TARGET
            ):
                reasons.append("sealed-bar-precision-below-target")
            if (
                selected["wilsonLowerBound95"] is None
                or float(selected["wilsonLowerBound95"]) + 1e-12 < BAR_PRODUCT_PRECISION_TARGET
            ):
                reasons.append("sealed-bar-wilson-lower-bound-below-target")
        if not selected["realCorpusPolicyPassed"]:
            reasons.append("sealed-bar-real-corpus-support-failed")

    reasons = list(dict.fromkeys(reasons))
    accepted = int(selected["acceptedBarCount"]) if selected else 0
    correct = int(selected["correctBarCount"]) if selected else 0
    return {
        "schemaVersion": BAR_OPERATING_POINT_EVALUATION_SCHEMA,
        "passed": not reasons and selected is not None,
        "targetPrecision": BAR_PRODUCT_PRECISION_TARGET,
        "minimumConfidence": threshold,
        "thresholdMatched": selected is not None,
        "barEvaluationComplete": bar is not None,
        "supportAvailable": accepted >= CERTIFICATION_MINIMUM_ACCEPTED_BARS,
        "barPrecision": selected.get("barPrecision") if selected else None,
        "wilsonLowerBound95": selected.get("wilsonLowerBound95") if selected else None,
        "acceptedBarCount": accepted,
        "correctBarCount": correct,
        "barCoverage": float(selected["barCoverage"]) if selected else 0.0,
        "barEligibility": float(bar["barEligibility"]) if bar is not None else 0.0,
        "eligibleBarCount": int(bar["eligibleBarCount"]) if bar is not None else 0,
        "totalBarCount": int(bar["totalBarCount"]) if bar is not None else 0,
        "excludedPrefixDurationSeconds": (float(bar["excludedPrefixDurationSeconds"]) if bar is not None else 0.0),
        "trackCount": int(bar["trackCount"]) if bar is not None else 0,
        "explicitBarGridOnly": (bar.get("explicitBarGridOnly") is True if bar is not None else False),
        "realCorpusSupport": real_points,
        "certificationPolicy": _certification_policy(),
        "confirmationIdentity": (dict(provenance["evaluation"]) if provenance is not None else None),
        "failureReasons": reasons,
    }


def evaluate_bar_product_operating_point(
    sealed_report: Mapping[str, Any],
    operating_point: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply one frozen threshold, failing closed by operating-point schema."""

    schema = operating_point.get("schemaVersion")
    if schema == LEGACY_BAR_OPERATING_POINT_SCHEMA:
        if sealed_report.get("schemaVersion") != LEGACY_BENCHMARK_REPORT_SCHEMA:
            return {
                "schemaVersion": LEGACY_BAR_OPERATING_POINT_EVALUATION_SCHEMA,
                "passed": False,
                "targetPrecision": _finite(operating_point.get("targetPrecision")),
                "minimumConfidence": _finite(operating_point.get("minimumConfidence")),
                "thresholdMatched": False,
                "barEvaluationComplete": False,
                "supportAvailable": False,
                "barPrecision": None,
                "acceptedBarCount": 0,
                "correctBarCount": 0,
                "barCoverage": 0.0,
                "eligibleBarCount": 0,
                "trackCount": 0,
                "failureReasons": ["legacy-operating-point-requires-benchmark-v1"],
            }
        return _evaluate_v1(sealed_report, operating_point)
    if schema == BAR_OPERATING_POINT_SCHEMA:
        return _evaluate_v2(sealed_report, operating_point)
    return {
        "schemaVersion": BAR_OPERATING_POINT_EVALUATION_SCHEMA,
        "passed": False,
        "targetPrecision": _finite(operating_point.get("targetPrecision")),
        "minimumConfidence": _finite(operating_point.get("minimumConfidence")),
        "thresholdMatched": False,
        "barEvaluationComplete": False,
        "supportAvailable": False,
        "barPrecision": None,
        "wilsonLowerBound95": None,
        "acceptedBarCount": 0,
        "correctBarCount": 0,
        "barCoverage": 0.0,
        "barEligibility": 0.0,
        "eligibleBarCount": 0,
        "totalBarCount": 0,
        "excludedPrefixDurationSeconds": 0.0,
        "trackCount": 0,
        "explicitBarGridOnly": False,
        "realCorpusSupport": {},
        "certificationPolicy": _certification_policy(),
        "confirmationIdentity": None,
        "failureReasons": ["bar-operating-point-schema-mismatch"],
    }
