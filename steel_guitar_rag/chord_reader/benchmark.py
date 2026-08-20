"""Reproducible multi-engine benchmark runner and aggregate reports."""

from __future__ import annotations

import hashlib
import json
import importlib
import math
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping

from .artifact_integrity import validate_factorized_artifact_manifest
from .bar_product import aggregate_bar_product_confidence, score_bar_product_confidence
from .bar_promotion import (
    benchmark_evaluation_hashes,
    benchmark_track_set_sha256,
    canonical_sha256,
    validate_benchmark_v2_provenance,
)
from .btc import BTCRecognizer
from .factorized import FactorizedEnsembleRecognizer, FactorizedRecognizer
from .hybrid import hybridize_predictions
from .metrics import (
    CALIBRATION_BIN_COUNT,
    CONFIDENCE_THRESHOLDS,
    _confidence_report,
    _confusion_report,
    score_segments,
    vocabulary_for_prediction,
)
from .split_protocol import validate_split_protocol_manifest
from .student import (
    StudentBoundaryGuidedEnsembleRecognizer,
    StudentEnsembleRecognizer,
    StudentHeterogeneousBoundaryGuidedEnsembleRecognizer,
    StudentRecognizer,
)


BENCHMARK_REPORT_SCHEMA = "chord_benchmark_report_v2"
BENCHMARK_PROVENANCE_SCHEMA = "chord_benchmark_provenance_v2"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_tree_provenance(repo_root: Path) -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout
    patch = subprocess.run(
        ["git", "diff", "--binary", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    digest = hashlib.sha256()
    digest.update(patch)
    digest.update(b"\0STATUS\0")
    digest.update(status)
    for raw_path in sorted(value for value in untracked if value):
        relative = raw_path.decode("utf-8", errors="strict")
        path = repo_root / relative
        digest.update(b"\0UNTRACKED\0")
        digest.update(raw_path)
        if path.is_file():
            digest.update(bytes.fromhex(_file_sha256(path)))
    return {
        "revision": revision,
        "dirty": bool(status),
        "diffSha256": digest.hexdigest(),
    }


def _feature_spec_sha256(cache_manifest: Mapping[str, Any]) -> str:
    frozen = cache_manifest.get("featureSpecSha256")
    if (
        not isinstance(frozen, str)
        or len(frozen) != 64
        or any(character not in "0123456789abcdef" for character in frozen)
    ):
        raise ValueError("A v2 benchmark requires a sealed featureSpecSha256.")
    return frozen


def _split_protocol_provenance(cache_manifest: Mapping[str, Any]) -> dict[str, str]:
    protocol = cache_manifest.get("splitProtocol")
    if not isinstance(protocol, Mapping):
        raise ValueError("A v2 benchmark requires a sealed split protocol.")
    calibration = protocol.get("calibration")
    calibration = calibration if isinstance(calibration, Mapping) else {}
    bar_eligibility = calibration.get("barEligibility")
    bar_eligibility = bar_eligibility if isinstance(bar_eligibility, Mapping) else {}
    values = {
        "outputManifestSha256": protocol.get("outputManifestSha256"),
        "assignmentSha256": protocol.get("assignmentSha256"),
        "calibrationSetSha256": calibration.get("setSha256"),
        "barEligibleSetSha256": bar_eligibility.get("setSha256"),
    }
    for name, value in values.items():
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"A v2 benchmark requires cache.splitProtocol.{name}.")
    return {name: str(value) for name, value in values.items()}


def _timing_identity(track: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: track.get(key)
        for key in (
            "id",
            "durationSeconds",
            "tempo",
            "meter",
            "beatTimesSeconds",
            "downbeatTimesSeconds",
            "barStartsSeconds",
            "gridStartSeconds",
            "prefixExcludedSeconds",
            "timingProvenance",
        )
        if key in track
    }


def _aggregate_confusion(values: list[Mapping[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name in ("root", "product", "majorMinor", "quality", "detailed"):
        cells: dict[tuple[str, str], float] = {}
        total_duration = 0.0
        for row in values:
            report = row["metrics"]["confusion"][name]
            total_duration += float(report["totalDurationSeconds"])
            for cell in report["cells"]:
                key = (str(cell["reference"]), str(cell["prediction"]))
                cells[key] = cells.get(key, 0.0) + float(cell["durationSeconds"])
        output[name] = _confusion_report(cells, total_duration)
    return output


def _aggregate_vocabulary(values: list[Mapping[str, Any]]) -> dict[str, Any]:
    reports = [row["metrics"]["vocabularyCoverage"] for row in values]
    available = [report for report in reports if report["available"]]
    reference_duration = sum(float(report["referenceDurationSeconds"]) for report in reports)
    available_reference_duration = sum(
        float(report["referenceDurationSeconds"]) for report in available
    )
    supported_duration = sum(float(report["supportedDurationSeconds"]) for report in available)
    out_of_vocabulary_duration = sum(
        float(report["outOfVocabularyDurationSeconds"]) for report in available
    )
    out_of_vocabulary: dict[str, float] = {}
    for report in available:
        for item in report["outOfVocabulary"]:
            label = str(item["label"])
            out_of_vocabulary[label] = (
                out_of_vocabulary.get(label, 0.0) + float(item["durationSeconds"])
            )
    vocabulary_sizes = sorted({int(report["vocabularySize"]) for report in available})
    complete = len(available) == len(reports)
    return {
        "available": complete,
        "availableTrackCount": len(available),
        "missingTrackCount": len(reports) - len(available),
        "vocabularySize": vocabulary_sizes[0] if len(vocabulary_sizes) == 1 else None,
        "vocabularySizes": vocabulary_sizes,
        "referenceDurationSeconds": reference_duration,
        "availableReferenceDurationSeconds": available_reference_duration,
        "supportedDurationSeconds": supported_duration if available else None,
        "outOfVocabularyDurationSeconds": out_of_vocabulary_duration if available else None,
        "exactDetailedWeightedRecallCeiling": (
            supported_duration / max(1e-12, reference_duration) if complete else None
        ),
        "outOfVocabulary": [
            {"label": label, "durationSeconds": duration}
            for label, duration in sorted(
                out_of_vocabulary.items(), key=lambda item: (-item[1], item[0])
            )
        ],
    }


def _aggregate_confidence(values: list[Mapping[str, Any]]) -> dict[str, Any]:
    curve_values: dict[float, dict[str, float]] = {
        threshold: {
            "acceptedDurationSeconds": 0.0,
            "rootCorrectDurationSeconds": 0.0,
            "productCorrectDurationSeconds": 0.0,
            "majorMinorCorrectDurationSeconds": 0.0,
            "detailedCorrectDurationSeconds": 0.0,
        }
        for threshold in CONFIDENCE_THRESHOLDS
    }
    calibration_bins: list[dict[str, float]] = [
        {
            "durationSeconds": 0.0,
            "confidenceMassSeconds": 0.0,
            "rootCorrectDurationSeconds": 0.0,
            "productCorrectDurationSeconds": 0.0,
            "majorMinorCorrectDurationSeconds": 0.0,
            "detailedCorrectDurationSeconds": 0.0,
        }
        for _ in range(CALIBRATION_BIN_COUNT)
    ]
    evaluated_duration = 0.0
    available_duration = 0.0
    for row in values:
        report = row["metrics"]["confidenceCoverage"]
        evaluated_duration += float(report["evaluatedDurationSeconds"])
        available_duration += float(report["confidenceAvailableDurationSeconds"])
        points = {float(point["minimumConfidence"]): point for point in report["curve"]}
        for threshold, aggregate in curve_values.items():
            point = points[threshold]
            for name in aggregate:
                aggregate[name] += float(point[name])
        for aggregate, calibration_bin in zip(
            calibration_bins, report["calibration"]["bins"], strict=True
        ):
            for name in aggregate:
                aggregate[name] += float(calibration_bin[name])
    return _confidence_report(
        evaluated_duration=evaluated_duration,
        available_duration=available_duration,
        curve_values=curve_values,
        calibration_bins=calibration_bins,
    )


def _aggregate(rows: Iterable[Mapping[str, Any]], *, include_domain_routes: bool = True) -> dict[str, Any]:
    values = list(rows)
    duration = sum(float(row["metrics"]["evaluatedDurationSeconds"]) for row in values)
    weighted_names = (
        "rootWeightedRecall",
        "productWeightedRecall",
        "majorMinorWeightedRecall",
        "detailedWeightedRecall",
    )
    output = {
        name: sum(
            float(row["metrics"][name]) * float(row["metrics"]["evaluatedDurationSeconds"])
            for row in values
        )
        / max(1e-12, duration)
        for name in weighted_names
    }
    output.update(
        {
            "evaluatedDurationSeconds": duration,
            "trackCount": len(values),
            "boundaryF1Macro": sum(float(row["metrics"]["boundary"]["f1"]) for row in values)
            / max(1, len(values)),
            "authoredSegmentBoundaryF1Macro": sum(
                float(row["metrics"]["authoredSegmentBoundary"]["f1"]) for row in values
            )
            / max(1, len(values)),
            "sequenceEditRateMacro": sum(float(row["metrics"]["sequenceEditRate"]) for row in values)
            / max(1, len(values)),
            "elapsedSeconds": sum(float(row["elapsedSeconds"]) for row in values),
            "sequenceEdits": {
                "distance": sum(int(row["metrics"]["sequenceEdits"]["distance"]) for row in values),
                "counts": {
                    name: sum(
                        int(row["metrics"]["sequenceEdits"]["counts"][name]) for row in values
                    )
                    for name in ("insertions", "deletions", "substitutions")
                },
                "referenceChordCount": sum(
                    int(row["metrics"]["referenceChordCount"]) for row in values
                ),
                "predictedChordCount": sum(
                    int(row["metrics"]["predictedChordCount"]) for row in values
                ),
            },
            "vocabularyCoverage": _aggregate_vocabulary(values),
            "confusion": _aggregate_confusion(values),
            "confidenceCoverage": _aggregate_confidence(values),
        }
    )
    bar_reports = [
        row["metrics"].get("barProductConfidence")
        for row in values
        if isinstance(row.get("metrics"), Mapping)
    ]
    if any(isinstance(report, Mapping) for report in bar_reports):
        output["barProductConfidence"] = aggregate_bar_product_confidence(
            report
            if isinstance(report, Mapping)
            else {
                "available": False,
                "grid": {"provenance": "missing-from-track-report"},
            }
            for report in bar_reports
        )
    output["sequenceEdits"]["microRate"] = float(output["sequenceEdits"]["distance"]) / max(
        1, int(output["sequenceEdits"]["referenceChordCount"])
    )
    routed = [row for row in values if row.get("domainRoute")]
    if include_domain_routes and routed:
        routes = sorted({str(row["domainRoute"]) for row in routed})
        probabilities = [
            float(row["domainGateProbability"])
            for row in routed
            if isinstance(row.get("domainGateProbability"), (int, float))
            and not isinstance(row.get("domainGateProbability"), bool)
        ]
        output["domainRoutes"] = {
            "availableTrackCount": len(routed),
            "missingTrackCount": len(values) - len(routed),
            "meanDomainGateProbability": (
                sum(probabilities) / len(probabilities) if probabilities else None
            ),
            "routes": {
                route: _aggregate(
                    (row for row in routed if row["domainRoute"] == route),
                    include_domain_routes=False,
                )
                for route in routes
            },
        }
    return output


def _score_prediction(
    reference: Mapping[str, Any],
    prediction: Mapping[str, Any],
    *,
    timing: Mapping[str, Any] | None = None,
    vocabulary_values: Iterable[str] | None = None,
) -> dict[str, Any]:
    vocabulary = vocabulary_values
    if vocabulary is None:
        vocabulary = vocabulary_for_prediction(prediction)
    metrics = score_segments(
        reference["segments"],
        prediction["segments"],
        vocabulary_values=vocabulary,
    )
    metrics["barProductConfidence"] = score_bar_product_confidence(
        reference,
        prediction,
        timing=timing,
    )
    return metrics


def _prediction_metadata(prediction: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    route = prediction.get("domainRoute")
    if isinstance(route, str) and route:
        output["domainRoute"] = route
    probability = prediction.get("domainGateProbability")
    if (
        not isinstance(probability, bool)
        and isinstance(probability, (int, float))
        and 0 <= float(probability) <= 1
    ):
        output["domainGateProbability"] = float(probability)
    return output


def _manifest_tempo_beat_grid(
    track: Mapping[str, Any],
    *,
    duration_seconds: float,
) -> dict[str, Any] | None:
    """Build a development-only rhythm upper bound from reference metadata."""

    tempo = track.get("tempo")
    meter = str(track.get("meter") or "")
    if (
        isinstance(tempo, bool)
        or not isinstance(tempo, (int, float))
        or not math.isfinite(float(tempo))
        or float(tempo) <= 0
    ):
        return None
    try:
        numerator_text, denominator_text = meter.split("/", 1)
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except (TypeError, ValueError):
        return None
    if numerator <= 0 or denominator <= 0 or duration_seconds <= 0:
        return None
    quarter_seconds = 60.0 / float(tempo)
    bar_seconds = numerator * 4.0 / denominator * quarter_seconds
    beats: list[dict[str, Any]] = []
    index = 0
    while index * quarter_seconds <= duration_seconds + 1e-9:
        time_seconds = index * quarter_seconds
        bar_phase = time_seconds / bar_seconds
        downbeat = abs(bar_phase - round(bar_phase)) <= 1e-7
        beats.append(
            {
                "timeSeconds": min(duration_seconds, time_seconds),
                "confidence": 1.0,
                "downbeat": downbeat,
                "downbeatConfidence": 1.0 if downbeat else 0.0,
            }
        )
        index += 1
    if not beats:
        return None
    return {
        "schemaVersion": "chord_beat_grid_v1",
        "confidence": 1.0,
        "source": "manifest-tempo-meter-oracle-development-only",
        "beats": beats,
    }


def _v2_prediction(repo_root: Path, track: Mapping[str, Any], output: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(repo_root / "scripts/chord_reader.py"),
        "predict-v2",
        str(track["audioPath"]),
        "--id",
        str(track["id"]),
        "--output",
        str(output),
    ]
    if track.get("tempo"):
        command.extend(("--tempo", str(track["tempo"])))
    if track.get("meter") in {"2/4", "3/4", "4/4", "6/8"}:
        command.extend(("--meter", str(track["meter"])))
    key = str(track.get("key") or "")
    if ":" in key:
        root, mode = key.split(":", 1)
        command.extend(("--key", root, "--mode", mode))
    result = subprocess.run(command, cwd=repo_root, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"v2 failed for {track['id']}")
    return json.loads(output.read_text(encoding="utf-8"))


def run_benchmark(
    manifest: Mapping[str, Any],
    *,
    engine: str,
    output_root: Path,
    split: str,
    limit: int | None = None,
    device: str = "cpu",
    local_files_only: bool = False,
    model: Path | None = None,
    ensemble_models: Iterable[Path] | None = None,
    boundary_model: Path | None = None,
    secondary_boundary_model: Path | None = None,
    secondary_boundary_weight: float = 0.5,
    domain_gate: Path | None = None,
    ensemble_weights: Iterable[float] | None = None,
    root_guide_only: bool = False,
    quality_models: Iterable[Path] | None = None,
    quality_mode_threshold: float = 0.6,
    quality_extension_threshold: float = 0.7,
    factorized_decoder: bool = False,
    product_boundary_scale: float = 1.3,
    product_boundary_bias: float = -2.0,
    dasheng_snapshot_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    tracks = [track for track in manifest["tracks"] if split == "all" or track["split"] == split]
    if limit is not None:
        tracks = tracks[:limit]
    if not tracks:
        raise ValueError(f"No tracks selected for split {split!r}.")
    if engine == "btc":
        recognizer: Any = BTCRecognizer(device=device, local_files_only=local_files_only)
    elif engine == "factorized":
        if model is None:
            raise ValueError("The factorized benchmark requires --model.")
        recognizer = FactorizedRecognizer(
            model,
            dasheng_snapshot_root=dasheng_snapshot_root,
        )
    elif engine == "student":
        ensemble = list(ensemble_models or [])
        weights = list(ensemble_weights or [])
        if weights:
            if boundary_model is None:
                raise ValueError("A heterogeneous ensemble requires --boundary-model.")
            recognizer = StudentHeterogeneousBoundaryGuidedEnsembleRecognizer(
                ensemble,
                weights,
                boundary_model,
                secondary_boundary_model=secondary_boundary_model,
                secondary_boundary_weight=secondary_boundary_weight,
                domain_gate=domain_gate,
                root_guide_only=root_guide_only,
                quality_models=quality_models,
                quality_mode_threshold=quality_mode_threshold,
                quality_extension_threshold=quality_extension_threshold,
                factorized_decoder=factorized_decoder,
                product_boundary_scale=product_boundary_scale,
                product_boundary_bias=product_boundary_bias,
            )
        elif boundary_model is not None:
            if len(ensemble) < 2:
                raise ValueError("A boundary-guided ensemble requires at least two --ensemble-model values.")
            recognizer = StudentBoundaryGuidedEnsembleRecognizer(ensemble, boundary_model)
        elif ensemble:
            recognizer = StudentEnsembleRecognizer(ensemble)
        elif model is None:
            raise ValueError("The student benchmark requires --model.")
        else:
            recognizer = StudentRecognizer(model)
    else:
        recognizer = None
    rows: list[dict[str, Any]] = []
    for track in tracks:
        prediction_path = output_root / "predictions" / engine / f"{track['id']}.json"
        started = time.perf_counter()
        if engine in {"btc", "student", "factorized"}:
            prediction = recognizer.predict(Path(track["audioPath"]), prediction_id=str(track["id"]))
            _write_json(prediction_path, prediction)
        elif engine == "v2":
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction = _v2_prediction(repo_root, track, prediction_path)
        else:
            raise ValueError(f"Unsupported benchmark engine {engine!r}.")
        elapsed = time.perf_counter() - started
        reference = json.loads(Path(track["referencePath"]).read_text(encoding="utf-8"))
        vocabulary_values = (
            recognizer.chord_map.values()
            if engine == "btc"
            else recognizer.vocabulary_labels
            if engine == "factorized"
            else None
        )
        metrics = _score_prediction(
            reference,
            prediction,
            timing=track,
            vocabulary_values=vocabulary_values,
        )
        rows.append(
            {
                "id": track["id"],
                "datasetId": track["datasetId"],
                "split": track["split"],
                "elapsedSeconds": elapsed,
                "audioDurationSeconds": prediction.get("durationSeconds"),
                "metrics": metrics,
                "predictionFile": f"predictions/{engine}/{track['id']}.json",
                **_prediction_metadata(prediction),
            }
        )

    dataset_ids = sorted({str(row["datasetId"]) for row in rows})
    git_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "schemaVersion": "chord_benchmark_report_v1",
        "engine": engine,
        "split": split,
        "gitRevision": git_revision,
        "peakResidentMemoryBytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "aggregate": _aggregate(rows),
        "strata": {dataset_id: _aggregate(row for row in rows if row["datasetId"] == dataset_id) for dataset_id in dataset_ids},
        "tracks": rows,
    }


def run_factorized_cache_benchmark(
    cache_manifest: Mapping[str, Any],
    track_manifests: Iterable[Mapping[str, Any]],
    *,
    model: Path,
    ensemble_models: Iterable[Path] | None = None,
    ensemble_weights: Iterable[float] | None = None,
    output_root: Path,
    split: str = "development",
    limit: int | None = None,
    beat_grid_source: str = "none",
) -> dict[str, Any]:
    """Decode a frozen feature cache without charging extraction to model runtime."""

    repo_root = Path(__file__).resolve().parents[2]
    timing_manifests = list(track_manifests)
    validate_split_protocol_manifest(
        cache_manifest,
        timing_manifests=timing_manifests,
    )
    feature_spec_sha256 = _feature_spec_sha256(cache_manifest)
    split_protocol_provenance = _split_protocol_provenance(cache_manifest)
    cache_manifest_sha256 = canonical_sha256(cache_manifest)
    source_tree_before = _source_tree_provenance(repo_root)
    model_paths = [model.resolve(), *(path.resolve() for path in (ensemble_models or []))]
    ensemble_weight_values = list(ensemble_weights or [])
    member_identities_before = [
        {"sha256": _file_sha256(path), "bytes": path.stat().st_size}
        for path in model_paths
    ]
    if len(model_paths) == 1:
        if ensemble_weight_values:
            raise ValueError("Ensemble weights require at least two factorized models.")
        recognizer = FactorizedRecognizer(model_paths[0])
        model_identity_before = member_identities_before[0]
    else:
        recognizer = FactorizedEnsembleRecognizer(
            model_paths,
            weights=ensemble_weight_values or None,
        )
        model_identity_before = {
            "sha256": recognizer.ensemble_sha256,
            "bytes": sum(int(item["bytes"]) for item in member_identities_before),
        }
    if beat_grid_source not in {"none", "manifest-tempo-oracle"}:
        raise ValueError("Unknown factorized cache beat-grid source.")
    if beat_grid_source != "none" and split not in {"dev", "development"}:
        raise ValueError("Reference-timing beat grids are development-only and cannot score test data.")
    if str(cache_manifest.get("featureKind")) != recognizer.feature_kind:
        raise ValueError("Factorized cache and model feature kinds do not match.")
    if int(cache_manifest.get("featureCount", -1)) != recognizer.feature_count:
        raise ValueError("Factorized cache and model feature counts do not match.")
    if int(cache_manifest.get("sampleRate", -1)) != recognizer.sample_rate:
        raise ValueError("Factorized cache and model sample rates do not match.")
    if getattr(recognizer, "feature_spec_sha256", None) != feature_spec_sha256:
        raise ValueError("Factorized cache and model feature specifications do not match.")
    numpy = importlib.import_module("numpy")
    sources: dict[str, Mapping[str, Any]] = {}
    for manifest in timing_manifests:
        for track in manifest.get("tracks", []):
            identifier = str(track["id"])
            if identifier in sources:
                raise ValueError(f"Duplicate track metadata for {identifier!r}.")
            sources[identifier] = track
    tracks = [
        item
        for item in cache_manifest.get("tracks", [])
        if split == "all" or item.get("split") == split
    ]
    if split == "calibration":
        if limit is not None:
            raise ValueError(
                "Calibration certification must score the complete frozen bar-eligible set."
            )
        protocol = cache_manifest["splitProtocol"]
        calibration = protocol["calibration"]
        bar_eligibility = calibration["barEligibility"]
        if bar_eligibility.get("status") != "frozen":
            raise ValueError("Calibration bar eligibility must be frozen before benchmarking.")
        eligible_ids = {str(item["id"]) for item in bar_eligibility["tracks"]}
        tracks = [item for item in tracks if str(item.get("id")) in eligible_ids]
        if benchmark_track_set_sha256(tracks) != str(bar_eligibility["setSha256"]):
            raise ValueError(
                "Calibration cache rows do not match the exact frozen bar-eligible set."
            )
    if limit is not None:
        tracks = tracks[:limit]
    if not tracks:
        raise ValueError(f"No cached tracks selected for split {split!r}.")
    artifact_manifest = {**cache_manifest, "tracks": tracks}
    validate_factorized_artifact_manifest(artifact_manifest, verify_files=True)

    rows: list[dict[str, Any]] = []
    for item in tracks:
        identifier = str(item["id"])
        source = sources.get(identifier)
        if source is None:
            raise ValueError(f"No reference metadata was supplied for {identifier!r}.")
        if str(source.get("datasetId")) != str(item.get("datasetId")):
            raise ValueError(f"Cache and timing metadata disagree for {identifier!r}.")
        with numpy.load(Path(item["path"]), allow_pickle=False) as cached:
            features = cached["features"].astype(numpy.float32)
        duration = float(
            item.get("durationSeconds")
            or source.get("durationSeconds")
            or len(features) * float(cache_manifest["frameSeconds"])
        )
        started = time.perf_counter()
        beat_grid = (
            _manifest_tempo_beat_grid(source, duration_seconds=duration)
            if beat_grid_source == "manifest-tempo-oracle"
            else None
        )
        reference_bytes = Path(source["referencePath"]).read_bytes()
        reference = json.loads(reference_bytes)
        reference_sha256 = hashlib.sha256(reference_bytes).hexdigest()
        reference_boundaries = (
            tuple(float(segment["start"]) for segment in reference["segments"][1:])
            if beat_grid is not None
            else ()
        )
        prediction = recognizer.predict_features(
            features,
            duration,
            prediction_id=identifier,
            beat_grid=beat_grid,
            reference_boundaries_seconds=reference_boundaries,
        )
        elapsed = time.perf_counter() - started
        prediction_path = output_root / "predictions" / "factorized" / f"{identifier}.json"
        _write_json(prediction_path, prediction)
        prediction_sha256 = _file_sha256(prediction_path)
        timing_sha256 = canonical_sha256(_timing_identity(source))
        rows.append(
            {
                "id": identifier,
                "datasetId": item["datasetId"],
                "split": item["split"],
                "elapsedSeconds": elapsed,
                "audioDurationSeconds": duration,
                "metrics": _score_prediction(
                    reference,
                    prediction,
                    timing=source,
                    vocabulary_values=recognizer.vocabulary_labels,
                ),
                "predictionFile": f"predictions/factorized/{identifier}.json",
                "referenceSha256": reference_sha256,
                "predictionSha256": prediction_sha256,
                "timingSha256": timing_sha256,
                **_prediction_metadata(prediction),
                "beatAware": bool(prediction.get("beatAware")),
            }
        )
    validate_factorized_artifact_manifest(artifact_manifest, verify_files=True)
    member_identities_after = [
        {"sha256": _file_sha256(path), "bytes": path.stat().st_size}
        for path in model_paths
    ]
    if member_identities_after != member_identities_before:
        raise RuntimeError("Factorized model changed during benchmark inference.")
    source_tree_after = _source_tree_provenance(repo_root)
    if source_tree_after != source_tree_before:
        raise RuntimeError("Source tree changed during benchmark inference.")

    dataset_ids = sorted({str(row["datasetId"]) for row in rows})
    decoder_contract = {
        "recognizer": getattr(
            recognizer,
            "decoder_contract",
            {
                "schemaVersion": "factorized_hierarchical_decoder_source_bound_v1",
                "bassThreshold": recognizer.bass_threshold,
            },
        ),
        "beatGridSource": beat_grid_source,
    }
    evaluation = {
        **benchmark_evaluation_hashes(rows),
        "decoderConfigSha256": canonical_sha256(decoder_contract),
    }
    provenance = {
        "schemaVersion": BENCHMARK_PROVENANCE_SCHEMA,
        "sourceTree": source_tree_before,
        "model": model_identity_before,
        "cache": {
            "manifestSha256": cache_manifest_sha256,
            "featureSpecSha256": feature_spec_sha256,
            "splitProtocol": split_protocol_provenance,
        },
        "evaluation": evaluation,
    }
    promotion_eligible = (
        beat_grid_source == "none"
        and source_tree_before["dirty"] is False
        and split != "all"
    )
    report = {
        "schemaVersion": BENCHMARK_REPORT_SCHEMA,
        "engine": "factorized",
        "split": split,
        "gitRevision": source_tree_before["revision"],
        "provenance": provenance,
        "frozenFeatureCache": True,
        "featureExtractionExcludedFromElapsedSeconds": True,
        "featureKind": cache_manifest["featureKind"],
        "beatGridSource": beat_grid_source,
        "oracleTimingUsed": beat_grid_source != "none",
        "promotionEligible": promotion_eligible,
        "beatAwareTrackCount": sum(bool(row["beatAware"]) for row in rows),
        "peakResidentMemoryBytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "aggregate": _aggregate(rows),
        "strata": {
            dataset_id: _aggregate(
                row for row in rows if row["datasetId"] == dataset_id
            )
            for dataset_id in dataset_ids
        },
        "tracks": rows,
    }
    if promotion_eligible:
        validate_benchmark_v2_provenance(report)
    return report


def merge_benchmark_reports(reports: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Recompute one aggregate from compatible per-corpus benchmark reports."""

    values = list(reports)
    if not values:
        raise ValueError("At least one benchmark report is required.")
    engines = {str(report.get("engine")) for report in values}
    splits = {str(report.get("split")) for report in values}
    revisions = {str(report.get("gitRevision")) for report in values}
    schemas = {str(report.get("schemaVersion")) for report in values}
    if len(engines) != 1 or len(splits) != 1 or len(schemas) != 1:
        raise ValueError("Benchmark reports must share one engine and split.")
    provenance: dict[str, Any] | None = None
    if schemas == {BENCHMARK_REPORT_SCHEMA}:
        for report in values:
            validate_benchmark_v2_provenance(report)
        provenance_values = [report.get("provenance") for report in values]
        if any(not isinstance(value, Mapping) for value in provenance_values):
            raise ValueError("Benchmark v2 reports require provenance.")
        first = dict(provenance_values[0])  # type: ignore[arg-type]
        stable = {
            "sourceTree": first.get("sourceTree"),
            "model": first.get("model"),
            "cache": first.get("cache"),
            "decoderConfigSha256": first.get("evaluation", {}).get(
                "decoderConfigSha256"
            ),
        }
        for value in provenance_values[1:]:
            assert isinstance(value, Mapping)
            candidate = {
                "sourceTree": value.get("sourceTree"),
                "model": value.get("model"),
                "cache": value.get("cache"),
                "decoderConfigSha256": value.get("evaluation", {}).get(
                    "decoderConfigSha256"
                ),
            }
            if candidate != stable:
                raise ValueError(
                    "Benchmark v2 reports use different source, model, cache, or decoder provenance."
                )
    rows = [dict(row) for report in values for row in report.get("tracks", [])]
    identifiers = [str(row.get("id")) for row in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Benchmark reports contain duplicate track identifiers.")
    dataset_ids = sorted({str(row["datasetId"]) for row in rows})
    if schemas == {BENCHMARK_REPORT_SCHEMA}:
        evaluation = {
            **benchmark_evaluation_hashes(rows),
            "decoderConfigSha256": stable["decoderConfigSha256"],
        }
        provenance = {
            "schemaVersion": BENCHMARK_PROVENANCE_SCHEMA,
            "sourceTree": stable["sourceTree"],
            "model": stable["model"],
            "cache": stable["cache"],
            "evaluation": evaluation,
        }
    result = {
        "schemaVersion": next(iter(schemas)),
        "engine": next(iter(engines)),
        "split": next(iter(splits)),
        "gitRevision": next(iter(revisions)) if len(revisions) == 1 else None,
        **({"provenance": provenance} if provenance is not None else {}),
        **(
            {"promotionEligible": True, "oracleTimingUsed": False}
            if schemas == {BENCHMARK_REPORT_SCHEMA}
            else {}
        ),
        "sourceReportCount": len(values),
        "peakResidentMemoryBytes": max(
            int(report.get("peakResidentMemoryBytes", 0)) for report in values
        ),
        "aggregate": _aggregate(rows),
        "strata": {
            dataset_id: _aggregate(
                row for row in rows if row["datasetId"] == dataset_id
            )
            for dataset_id in dataset_ids
        },
        "tracks": rows,
    }
    if schemas == {BENCHMARK_REPORT_SCHEMA}:
        validate_benchmark_v2_provenance(result)
    return result


def run_prediction_benchmark(
    manifest: Mapping[str, Any],
    *,
    prediction_root: Path,
    engine: str,
    split: str = "test",
) -> dict[str, Any]:
    """Rescore frozen predictions without rerunning or modifying inference."""

    repo_root = Path(__file__).resolve().parents[2]
    tracks = [track for track in manifest["tracks"] if split == "all" or track["split"] == split]
    if not tracks:
        raise ValueError(f"No tracks selected for split {split!r}.")
    rows: list[dict[str, Any]] = []
    for track in tracks:
        identifier = str(track["id"])
        prediction_path = prediction_root / f"{identifier}.json"
        prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
        reference = json.loads(Path(track["referencePath"]).read_text(encoding="utf-8"))
        rows.append(
            {
                "id": identifier,
                "datasetId": track["datasetId"],
                "split": track["split"],
                "elapsedSeconds": 0.0,
                "audioDurationSeconds": prediction.get("durationSeconds"),
                "metrics": _score_prediction(reference, prediction, timing=track),
                "predictionFile": f"predictions/{engine}/{identifier}.json",
                **_prediction_metadata(prediction),
            }
        )

    dataset_ids = sorted({str(row["datasetId"]) for row in rows})
    git_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "schemaVersion": "chord_benchmark_report_v1",
        "engine": engine,
        "split": split,
        "gitRevision": git_revision,
        "rescoredFromFrozenPredictions": True,
        "peakResidentMemoryBytes": 0,
        "aggregate": _aggregate(rows),
        "strata": {
            dataset_id: _aggregate(row for row in rows if row["datasetId"] == dataset_id)
            for dataset_id in dataset_ids
        },
        "tracks": rows,
    }


def run_hybrid_benchmark(
    manifest: Mapping[str, Any],
    *,
    v2_prediction_root: Path,
    student_prediction_root: Path,
    output_root: Path,
    split: str = "test",
) -> dict[str, Any]:
    """Freeze the conservative hybrid from already-frozen engine predictions."""

    repo_root = Path(__file__).resolve().parents[2]
    tracks = [track for track in manifest["tracks"] if split == "all" or track["split"] == split]
    if not tracks:
        raise ValueError(f"No tracks selected for split {split!r}.")
    rows: list[dict[str, Any]] = []
    for track in tracks:
        identifier = str(track["id"])
        v2 = json.loads((v2_prediction_root / f"{identifier}.json").read_text(encoding="utf-8"))
        student = json.loads((student_prediction_root / f"{identifier}.json").read_text(encoding="utf-8"))
        started = time.perf_counter()
        prediction = hybridize_predictions(v2, student)
        elapsed = time.perf_counter() - started
        prediction_path = output_root / "predictions" / "hybrid" / f"{identifier}.json"
        _write_json(prediction_path, prediction)
        reference = json.loads(Path(track["referencePath"]).read_text(encoding="utf-8"))
        rows.append(
            {
                "id": identifier,
                "datasetId": track["datasetId"],
                "split": track["split"],
                "elapsedSeconds": elapsed,
                "audioDurationSeconds": prediction.get("durationSeconds"),
                "metrics": _score_prediction(reference, prediction, timing=track),
                "predictionFile": f"predictions/hybrid/{identifier}.json",
                **_prediction_metadata(prediction),
            }
        )
    dataset_ids = sorted({str(row["datasetId"]) for row in rows})
    git_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "schemaVersion": "chord_benchmark_report_v1",
        "engine": "hybrid",
        "split": split,
        "gitRevision": git_revision,
        "peakResidentMemoryBytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "aggregate": _aggregate(rows),
        "strata": {
            dataset_id: _aggregate(row for row in rows if row["datasetId"] == dataset_id)
            for dataset_id in dataset_ids
        },
        "tracks": rows,
    }
