#!/usr/bin/env python3
"""Run one bounded, development-only consensus selector comparison.

The experiment deliberately has two explicit phases:

1. ``prepare`` performs one BTC inference pass and one label-blind NNLS-chroma
   feature pass over the already sealed development tracks.
2. ``evaluate`` fits exactly three frozen selector candidates once each and
   writes one terminal report.  It never reads calibration/test material.

The candidates predict whether the existing engine's bar product is correct;
they do not rewrite chord labels.  Their useful product metric is therefore
accepted-bar precision together with accepted-bar coverage.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from steel_guitar_rag.chord_reader.btc import BTCRecognizer
from steel_guitar_rag.chord_reader.factorized import factorized_components, product_symbol
from steel_guitar_rag.chord_reader.labels import normalize_chord


SCHEMA = "chord_bounded_consensus_development_v1"
CACHE_SCHEMA = "chord_bounded_consensus_feature_cache_v1"
SPLIT_ID = "bounded-consensus-development-holdout-v1"
SELECTOR_THRESHOLD = 0.98
REPORTING_THRESHOLDS = (0.5, 0.8, 0.9, 0.95, 0.98)
MAX_CANDIDATE_FITS = 3
FRAME_SECONDS = 0.1
CORRECTION_SCHEMA = "chord_bounded_correction_fusion_development_v1"
CORRECTION_CANDIDATES = ("engine-unchanged", "fixed-checker-consensus", "one-fit-source-selector")
CORRECTION_MAX_FITS = 1
CORRECTION_DOMINANCE = 0.75
CORRECTION_COVERAGE = 0.75
REFERENCE_MANIFESTS = (
    "tiny-aam-manifest.json",
    "guitarset-manifest.json",
    "idmt-guitar-manifest.json",
    "nrgcp-manifest.json",
    "winterreise-manifest.json",
)

CORE_CANDIDATE = "engine-only"
BTC_CANDIDATE = "engine-plus-btc"
NNLS_CANDIDATE = "engine-plus-btc-plus-nnls"
CANDIDATES = (CORE_CANDIDATE, BTC_CANDIDATE, NNLS_CANDIDATE)

BTC_FEATURES = (
    "btcCoverage",
    "btcProductAgreement",
    "btcRootAgreement",
    "btcDominance",
    "btcConfidence",
    "btcTransitionRate",
)
NNLS_FEATURES = (
    "nnlsCoverage",
    "nnlsProductAgreement",
    "nnlsRootAgreement",
    "nnlsDominance",
    "nnlsConfidence",
    "nnlsMargin",
)
CONSENSUS_FEATURES = (
    "btcNnlsRootAgreement",
    "allThreeRootAgreement",
    "checkersAgainstEngineRootShare",
    "checkerProductAgreement",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _root(product: str | None) -> str:
    label = normalize_chord(product)
    return label.root or "N.C."


def _overlap(start: float, end: float, other_start: float, other_end: float) -> float:
    return max(0.0, min(end, other_end) - max(start, other_start))


def _dominant_segments(segments: Sequence[Mapping[str, Any]], start: float, end: float) -> dict[str, Any]:
    duration = max(1e-9, end - start)
    product_duration: dict[str, float] = defaultdict(float)
    confidence_total = 0.0
    covered = 0.0
    transitions = 0
    last_product: str | None = None
    for segment in segments:
        overlap = _overlap(start, end, float(segment["start"]), float(segment["end"]))
        if overlap <= 0:
            continue
        product = str(segment.get("productLabel") or "N.C.")
        product_duration[product] += overlap
        confidence_total += overlap * float(segment.get("confidence") or 0.0)
        covered += overlap
        if last_product is not None and product != last_product:
            transitions += 1
        last_product = product
    dominant = max(product_duration, key=product_duration.get) if product_duration else "N.C."
    dominant_duration = product_duration.get(dominant, 0.0)
    return {
        "product": dominant,
        "coverage": min(1.0, covered / duration),
        "dominance": dominant_duration / covered if covered else 0.0,
        "confidence": confidence_total / covered if covered else 0.0,
        "transitionRate": transitions / duration,
    }


def _chord_templates() -> tuple[np.ndarray, list[str]]:
    templates: list[np.ndarray] = []
    labels: list[str] = []
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    for quality, intervals in (("", (0, 4, 7)), ("m", (0, 3, 7))):
        for root, name in enumerate(names):
            template = np.zeros(12, dtype=np.float64)
            template[(root + intervals[0]) % 12] = 1.0
            template[(root + intervals[1]) % 12] = 0.75
            template[(root + intervals[2]) % 12] = 0.6
            template /= np.linalg.norm(template)
            templates.append(template)
            labels.append(f"{name}{quality}")
    return np.stack(templates, axis=1), labels


def nnls_chroma_evidence(features: np.ndarray) -> dict[str, Any]:
    """Return isolated Chordino-inspired NNLS evidence without GPL code.

    Chordino itself uses a richer note-profile and HMM pipeline.  This clean
    implementation borrows only the published NNLS-chroma idea and is kept as
    independent evidence rather than merged into the production recognizer.
    """

    if features.ndim != 2 or features.shape[1] < 61:
        raise ValueError("NNLS evidence requires multiband_chroma_v2 features.")
    templates, labels = _chord_templates()
    gram = templates.T @ templates
    full = np.clip(features[:, :12].astype(np.float64), 0.0, None)
    middle = np.clip(features[:, 24:36].astype(np.float64), 0.0, None)
    chroma = 0.65 * full + 0.35 * middle
    products: list[str] = []
    confidences: list[float] = []
    margins: list[float] = []
    for row in chroma:
        if float(row.sum()) <= 1e-8:
            products.append("N.C.")
            confidences.append(0.0)
            margins.append(0.0)
            continue
        # Deterministic cyclic coordinate descent for the non-negative least
        # squares objective.  Keeping the tiny solver here avoids copying the
        # GPL Chordino implementation or adding a runtime dependency.
        activations = np.zeros(templates.shape[1], dtype=np.float64)
        projection = templates.T @ row
        for _iteration in range(32):
            for column in range(len(activations)):
                residual = projection[column] - float(gram[column] @ activations)
                residual += gram[column, column] * activations[column]
                activations[column] = max(0.0, residual / gram[column, column])
        order = np.argsort(activations)
        best = int(order[-1])
        total = float(activations.sum())
        top = float(activations[best])
        second = float(activations[int(order[-2])]) if len(order) > 1 else 0.0
        products.append(labels[best])
        confidences.append(top / total if total else 0.0)
        margins.append((top - second) / total if total else 0.0)
    return {"products": products, "confidences": confidences, "margins": margins}


def _dominant_frames(
    evidence: Mapping[str, Any], start: float, end: float, frame_seconds: float = FRAME_SECONDS
) -> dict[str, Any]:
    products = list(evidence["products"])
    confidences = list(evidence["confidences"])
    margins = list(evidence["margins"])
    first = max(0, int(math.floor(start / frame_seconds)))
    last = min(len(products), int(math.ceil(end / frame_seconds)))
    if last <= first:
        return {
            "product": "N.C.",
            "coverage": 0.0,
            "dominance": 0.0,
            "confidence": 0.0,
            "margin": 0.0,
        }
    selected = products[first:last]
    counts: dict[str, int] = defaultdict(int)
    for product in selected:
        counts[product] += 1
    dominant = max(counts, key=counts.get)
    return {
        "product": dominant,
        "coverage": min(1.0, len(selected) * frame_seconds / max(1e-9, end - start)),
        "dominance": counts[dominant] / len(selected),
        "confidence": float(np.mean(confidences[first:last])),
        "margin": float(np.mean(margins[first:last])),
    }


def _split_groups(examples: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    by_dataset: dict[str, set[str]] = defaultdict(set)
    for example in examples:
        group = str(example["confidenceGroupId"])
        parts = group.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Unexpected confidence group {group!r}.")
        by_dataset[parts[1]].add(group)
    assignments: dict[str, str] = {}
    for dataset, groups in sorted(by_dataset.items()):
        ordered = sorted(
            groups,
            key=lambda group: hashlib.sha256(f"{SPLIT_ID}:{dataset}:{group}".encode()).hexdigest(),
        )
        for index, group in enumerate(ordered):
            assignments[group] = "evaluation" if index % 4 == 0 else "fit"
    if set(assignments.values()) != {"fit", "evaluation"}:
        raise ValueError("Development holdout must contain fit and evaluation groups.")
    return assignments


def _evidence_features(example: Mapping[str, Any], btc: Mapping[str, Any], nnls: Mapping[str, Any]) -> dict[str, float]:
    summary = example["barSummary"]
    start, end = float(summary["start"]), float(summary["end"])
    engine_product = str(summary.get("predictionProduct") or "N.C.")
    engine_root = _root(engine_product)
    btc_bar = _dominant_segments(btc["segments"], start, end)
    nnls_bar = _dominant_frames(nnls, start, end)
    btc_product = str(btc_bar["product"])
    nnls_product = str(nnls_bar["product"])
    btc_root = _root(btc_product)
    nnls_root = _root(nnls_product)
    return {
        "btcCoverage": float(btc_bar["coverage"]),
        "btcProductAgreement": float(btc_product == engine_product),
        "btcRootAgreement": float(btc_root == engine_root),
        "btcDominance": float(btc_bar["dominance"]),
        "btcConfidence": float(btc_bar["confidence"]),
        "btcTransitionRate": float(btc_bar["transitionRate"]),
        "nnlsCoverage": float(nnls_bar["coverage"]),
        "nnlsProductAgreement": float(nnls_product == engine_product),
        "nnlsRootAgreement": float(nnls_root == engine_root),
        "nnlsDominance": float(nnls_bar["dominance"]),
        "nnlsConfidence": float(nnls_bar["confidence"]),
        "nnlsMargin": float(nnls_bar["margin"]),
        "btcNnlsRootAgreement": float(btc_root == nnls_root),
        "allThreeRootAgreement": float(engine_root == btc_root == nnls_root),
        "checkersAgainstEngineRootShare": float(btc_root == nnls_root and btc_root != engine_root),
        "checkerProductAgreement": float(btc_product == nnls_product),
    }


def _candidate_features(core_names: Sequence[str], candidate: str) -> tuple[str, ...]:
    core = tuple(core_names)
    if candidate == CORE_CANDIDATE:
        return core
    if candidate == BTC_CANDIDATE:
        return core + BTC_FEATURES
    if candidate == NNLS_CANDIDATE:
        return core + BTC_FEATURES + NNLS_FEATURES + CONSENSUS_FEATURES
    raise ValueError(f"Unknown frozen candidate {candidate!r}.")


def _sealed_feature_paths_by_id(sealed: Mapping[str, Any]) -> dict[str, Path]:
    """Bind label-blind feature arrays by identity, not their historical cache role."""

    paths: dict[str, Path] = {}
    for row in sealed["tracks"]:
        track_id = str(row["id"])
        path = Path(row["path"])
        if track_id in paths and paths[track_id] != path:
            raise ValueError(f"Sealed cache has conflicting feature paths for {track_id}.")
        paths[track_id] = path
    return paths


def _numeric_feature_value(value: Any) -> float:
    """Translate the feature contract's explicit missing value for imputation."""

    return np.nan if value is None else float(value)


def _canonical_product(value: str | None) -> str:
    components = factorized_components(value)
    return product_symbol(int(components["root"]), int(components["product"]))


def _manifest_rows(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, list):
        return value
    if isinstance(value, Mapping):
        for key in ("tracks", "items", "recordings"):
            rows = value.get(key)
            if isinstance(rows, list):
                return rows
    raise ValueError("A processed dataset manifest has no track rows.")


def _reference_paths(processed_dir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name in REFERENCE_MANIFESTS:
        manifest = _read_json(processed_dir / name)
        for row in _manifest_rows(manifest):
            track_id = str(row["id"])
            path = Path(row["referencePath"])
            if track_id in paths and paths[track_id] != path:
                raise ValueError(f"Conflicting reference paths for {track_id}.")
            paths[track_id] = path
    return paths


def _reference_bar(segments: Sequence[Mapping[str, Any]], start: float, end: float) -> dict[str, Any]:
    duration = max(1e-9, end - start)
    masses: dict[str, float] = defaultdict(float)
    covered = 0.0
    for segment in segments:
        overlap = _overlap(start, end, float(segment["start"]), float(segment["end"]))
        if overlap <= 0:
            continue
        masses[_canonical_product(str(segment["label"]))] += overlap
        covered += overlap
    product = max(masses, key=masses.get) if masses else "N.C."
    return {
        "product": product,
        "coverage": min(1.0, covered / duration),
        "dominance": masses.get(product, 0.0) / covered if covered else 0.0,
    }


def _metrics(probabilities: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    from sklearn.metrics import brier_score_loss, roc_auc_score

    rows: list[dict[str, Any]] = []
    for threshold in REPORTING_THRESHOLDS:
        accepted = probabilities >= threshold
        count = int(accepted.sum())
        correct = int(labels[accepted].sum()) if count else 0
        rows.append(
            {
                "minimumConfidence": threshold,
                "acceptedCount": count,
                "correctCount": correct,
                "precision": correct / count if count else None,
                "coverage": count / len(labels),
            }
        )
    predicted = probabilities >= 0.5
    roc_auc = float(roc_auc_score(labels, probabilities)) if len(np.unique(labels)) > 1 else None
    return {
        "evaluationExampleCount": int(len(labels)),
        "correctnessClassificationAccuracy": float(np.mean(predicted == labels)),
        "rocAuc": roc_auc,
        "brierScore": float(brier_score_loss(labels, probabilities)),
        "engineUnfilteredProductPrecision": float(labels.mean()),
        "selectiveCurve": rows,
        "primaryOperatingPoint": next(row for row in rows if row["minimumConfidence"] == SELECTOR_THRESHOLD),
    }


def prepare_features(
    *, examples_path: Path, runtime_audio_path: Path, sealed_cache_path: Path, output: Path
) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError("The bounded feature pass is already complete; no retry is permitted.")
    examples = _read_json(examples_path)
    if examples.get("split") != "development" or not examples.get("developmentOnly"):
        raise ValueError("Consensus preparation accepts only development-only examples.")
    track_ids = sorted({str(row["trackId"]) for row in examples["examples"]})
    runtime = _read_json(runtime_audio_path)
    if runtime.get("split") != "development":
        raise ValueError("Runtime audio must be development-only.")
    audio_by_id = {str(row["id"]): Path(row["audioPath"]) for row in runtime["tracks"]}
    sealed = _read_json(sealed_cache_path)
    features_by_id = _sealed_feature_paths_by_id(sealed)
    if set(track_ids) - set(audio_by_id) or set(track_ids) - set(features_by_id):
        raise ValueError("Feature preparation could not bind every development track.")

    btc_dir, nnls_dir = output / "btc", output / "nnls"
    btc_dir.mkdir(parents=True, exist_ok=True)
    nnls_dir.mkdir(parents=True, exist_ok=True)
    recognizer = BTCRecognizer(device="cpu", local_files_only=True)
    rows: list[dict[str, Any]] = []
    for index, track_id in enumerate(track_ids, start=1):
        btc_path = btc_dir / f"{track_id}.json"
        nnls_path = nnls_dir / f"{track_id}.npz"
        if btc_path.exists() or nnls_path.exists():
            raise FileExistsError(f"Partial prior cache exists for {track_id}; stop instead of retrying.")
        btc = recognizer.predict(audio_by_id[track_id], prediction_id=track_id, product_viterbi=True)
        _atomic_json(btc_path, btc)
        with np.load(features_by_id[track_id], allow_pickle=False) as archive:
            nnls = nnls_chroma_evidence(np.asarray(archive["features"]))
        np.savez_compressed(
            nnls_path,
            products=np.asarray(nnls["products"], dtype="U8"),
            confidences=np.asarray(nnls["confidences"], dtype=np.float32),
            margins=np.asarray(nnls["margins"], dtype=np.float32),
        )
        rows.append(
            {
                "trackId": track_id,
                "ordinal": index,
                "btcSha256": _sha256(btc_path),
                "nnlsSha256": _sha256(nnls_path),
            }
        )
    receipt = {
        "schemaVersion": CACHE_SCHEMA,
        "split": "development",
        "trackCount": len(rows),
        "btcInferencePassCount": 1,
        "nnlsFeaturePassCount": 1,
        "fitCount": 0,
        "parameterSearchCount": 0,
        "source": {
            "examplesSha256": _sha256(examples_path),
            "runtimeAudioSha256": _sha256(runtime_audio_path),
            "sealedCacheSha256": _sha256(sealed_cache_path),
        },
        "tracks": rows,
    }
    receipt["artifactSha256"] = _canonical_sha256(receipt)
    _atomic_json(manifest_path, receipt)
    return receipt


def _load_nnls(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as archive:
        return {
            "products": archive["products"].astype(str).tolist(),
            "confidences": archive["confidences"].astype(float).tolist(),
            "margins": archive["margins"].astype(float).tolist(),
        }


def evaluate(*, examples_path: Path, cache: Path, output_path: Path) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError("The bounded terminal report already exists; no retry is permitted.")
    examples = _read_json(examples_path)
    cache_manifest = _read_json(cache / "manifest.json")
    if cache_manifest.get("schemaVersion") != CACHE_SCHEMA or cache_manifest.get("fitCount") != 0:
        raise ValueError("The feature cache receipt is not admissible.")
    rows = list(examples["examples"])
    core_names = tuple(examples["sharedBindings"]["featureNames"])
    assignments = _split_groups(rows)
    evidence_by_track: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    matrices: dict[str, list[list[float]]] = {candidate: [] for candidate in CANDIDATES}
    labels: list[int] = []
    roles: list[str] = []
    datasets: list[str] = []
    for example in rows:
        track_id = str(example["trackId"])
        if track_id not in evidence_by_track:
            evidence_by_track[track_id] = (
                _read_json(cache / "btc" / f"{track_id}.json"),
                _load_nnls(cache / "nnls" / f"{track_id}.npz"),
            )
        btc, nnls = evidence_by_track[track_id]
        external = _evidence_features(example, btc, nnls)
        core = example["barSummary"]["featureValues"]
        combined = {**core, **external}
        for candidate in CANDIDATES:
            names = _candidate_features(core_names, candidate)
            matrices[candidate].append([_numeric_feature_value(combined[name]) for name in names])
        labels.append(int(bool(example["outcome"]["correct"])))
        roles.append(assignments[str(example["confidenceGroupId"])])
        datasets.append(str(example["confidenceGroupId"]).split(":", 2)[1])

    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(labels, dtype=np.int64)
    fit_mask = np.asarray([role == "fit" for role in roles])
    eval_mask = ~fit_mask
    results: list[dict[str, Any]] = []
    fit_count = 0
    for candidate in CANDIDATES:
        feature_names = _candidate_features(core_names, candidate)
        values = np.asarray(matrices[candidate], dtype=np.float64)
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=1000,
                random_state=20260825,
                solver="lbfgs",
            ),
        )
        model.fit(values[fit_mask], y[fit_mask])
        fit_count += 1
        probabilities = model.predict_proba(values[eval_mask])[:, 1]
        result = {
            "candidate": candidate,
            "featureCount": len(feature_names),
            "featureNamesSha256": _canonical_sha256(feature_names),
            "fitCount": 1,
            "parameterSearchCount": 0,
            "metrics": _metrics(probabilities, y[eval_mask]),
            "strata": {},
        }
        eval_datasets = np.asarray(datasets)[eval_mask]
        for dataset in sorted(set(eval_datasets.tolist())):
            mask = eval_datasets == dataset
            result["strata"][dataset] = _metrics(probabilities[mask], y[eval_mask][mask])
        results.append(result)
    if fit_count != MAX_CANDIDATE_FITS:
        raise RuntimeError("The frozen three-fit cap was not satisfied exactly.")

    group_rows = [{"confidenceGroupId": group, "role": role} for group, role in sorted(assignments.items())]
    report = {
        "schemaVersion": SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "sealedEvaluationOpened": False,
        "deploymentChanged": False,
        "candidateCount": len(CANDIDATES),
        "candidateFitCount": fit_count,
        "maximumCandidateFits": MAX_CANDIDATE_FITS,
        "parameterSearchCount": 0,
        "automaticRetryCount": 0,
        "selectorThreshold": SELECTOR_THRESHOLD,
        "reportingThresholds": list(REPORTING_THRESHOLDS),
        "split": {
            "id": SPLIT_ID,
            "algorithm": "per-dataset SHA-256 ordering; every fourth group is evaluation",
            "fitExampleCount": int(fit_mask.sum()),
            "evaluationExampleCount": int(eval_mask.sum()),
            "groupAssignmentsSha256": _canonical_sha256(group_rows),
            "groups": group_rows,
        },
        "source": {
            "examplesSha256": _sha256(examples_path),
            "featureCacheManifestSha256": _sha256(cache / "manifest.json"),
        },
        "estimator": {
            "type": "median-imputed standardized balanced logistic regression",
            "C": 1.0,
            "solver": "lbfgs",
            "maxIterations": 1000,
            "randomState": 20260825,
        },
        "candidates": results,
    }
    report["artifactSha256"] = _canonical_sha256(report)
    _atomic_json(output_path, report)
    return report


def _correction_metrics(
    *,
    predictions: np.ndarray,
    references: np.ndarray,
    engine: np.ndarray,
    confidence: np.ndarray,
    selectively_eligible: np.ndarray,
) -> dict[str, Any]:
    changed = predictions != engine
    engine_correct = engine == references
    prediction_correct = predictions == references
    curve: list[dict[str, Any]] = []
    for threshold in REPORTING_THRESHOLDS:
        accepted = selectively_eligible & (confidence >= threshold)
        count = int(accepted.sum())
        correct = int(prediction_correct[accepted].sum()) if count else 0
        curve.append(
            {
                "minimumConfidence": threshold,
                "acceptedCount": count,
                "correctCount": correct,
                "precision": correct / count if count else None,
                "coverage": count / len(references),
            }
        )
    return {
        "exampleCount": int(len(references)),
        "fullCoverageCorrectCount": int(prediction_correct.sum()),
        "fullCoverageAccuracy": float(prediction_correct.mean()),
        "changedCount": int(changed.sum()),
        "helpfulCorrectionCount": int((changed & ~engine_correct & prediction_correct).sum()),
        "harmfulCorrectionCount": int((changed & engine_correct & ~prediction_correct).sum()),
        "changedWrongToDifferentWrongCount": int((changed & ~engine_correct & ~prediction_correct).sum()),
        "netCorrectGain": int(prediction_correct.sum() - engine_correct.sum()),
        "selectiveCurve": curve,
        "primaryOperatingPoint": next(row for row in curve if row["minimumConfidence"] == SELECTOR_THRESHOLD),
    }


def _correction_result(
    *,
    candidate: str,
    predictions: np.ndarray,
    references: np.ndarray,
    engine: np.ndarray,
    confidence: np.ndarray,
    selectively_eligible: np.ndarray,
    datasets: np.ndarray,
    fit_count: int,
) -> dict[str, Any]:
    result = {
        "candidate": candidate,
        "fitCount": fit_count,
        "parameterSearchCount": 0,
        "metrics": _correction_metrics(
            predictions=predictions,
            references=references,
            engine=engine,
            confidence=confidence,
            selectively_eligible=selectively_eligible,
        ),
        "strata": {},
    }
    for dataset in sorted(set(datasets.tolist())):
        mask = datasets == dataset
        result["strata"][dataset] = _correction_metrics(
            predictions=predictions[mask],
            references=references[mask],
            engine=engine[mask],
            confidence=confidence[mask],
            selectively_eligible=selectively_eligible[mask],
        )
    return result


def evaluate_correction_fusion(
    *,
    examples_path: Path,
    cache: Path,
    processed_dir: Path,
    benchmark_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Run the one-fit, three-candidate correction comparison and stop."""

    if output_path.exists():
        raise FileExistsError("The bounded correction report already exists; no retry is permitted.")
    examples = _read_json(examples_path)
    if examples.get("split") != "development" or not examples.get("developmentOnly"):
        raise ValueError("Correction fusion accepts only development-only examples.")
    cache_manifest = _read_json(cache / "manifest.json")
    if (
        cache_manifest.get("schemaVersion") != CACHE_SCHEMA
        or cache_manifest.get("btcInferencePassCount") != 1
        or cache_manifest.get("nnlsFeaturePassCount") != 1
        or cache_manifest.get("fitCount") != 0
    ):
        raise ValueError("Correction fusion requires the completed one-pass feature cache.")
    benchmark = _read_json(benchmark_path)
    if benchmark.get("split") != "development" or benchmark.get("promotionEligible"):
        raise ValueError("Correction fusion requires the development-only benchmark.")
    benchmark_by_id = {str(row["id"]): row for row in benchmark["tracks"]}
    reference_paths = _reference_paths(processed_dir)
    rows = list(examples["examples"])
    assignments = _split_groups(rows)
    core_names = tuple(examples["sharedBindings"]["featureNames"])
    feature_names = _candidate_features(core_names, NNLS_CANDIDATE)

    evidence_by_track: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    references_by_track: dict[str, list[Mapping[str, Any]]] = {}
    reference_receipts: dict[str, str] = {}
    matrix: list[list[float]] = []
    engine_products: list[str] = []
    btc_products: list[str] = []
    nnls_products: list[str] = []
    reference_products: list[str] = []
    engine_confidence: list[float] = []
    consensus_confidence: list[float] = []
    fixed_predictions: list[str] = []
    roles: list[str] = []
    datasets: list[str] = []
    outcome_reproduction_count = 0

    for example in rows:
        track_id = str(example["trackId"])
        if track_id not in evidence_by_track:
            evidence_by_track[track_id] = (
                _read_json(cache / "btc" / f"{track_id}.json"),
                _load_nnls(cache / "nnls" / f"{track_id}.npz"),
            )
            reference_path = reference_paths.get(track_id)
            benchmark_row = benchmark_by_id.get(track_id)
            if reference_path is None or benchmark_row is None:
                raise ValueError(f"Missing development reference binding for {track_id}.")
            reference_sha = _sha256(reference_path)
            if reference_sha != benchmark_row["referenceSha256"]:
                raise ValueError(f"Development reference hash changed for {track_id}.")
            reference = _read_json(reference_path)
            if reference.get("id") != track_id or reference.get("schemaVersion") != "chord_reference_v1":
                raise ValueError(f"Invalid development reference for {track_id}.")
            references_by_track[track_id] = list(reference["segments"])
            reference_receipts[track_id] = reference_sha

        btc, nnls = evidence_by_track[track_id]
        summary = example["barSummary"]
        start, end = float(summary["start"]), float(summary["end"])
        engine_product = _canonical_product(str(summary.get("predictionProduct") or "N.C."))
        btc_bar = _dominant_segments(btc["segments"], start, end)
        nnls_bar = _dominant_frames(nnls, start, end)
        btc_product = _canonical_product(str(btc_bar["product"]))
        nnls_product = _canonical_product(str(nnls_bar["product"]))
        reference_bar = _reference_bar(references_by_track[track_id], start, end)
        if reference_bar["coverage"] < CORRECTION_COVERAGE or reference_bar["dominance"] < CORRECTION_DOMINANCE:
            raise ValueError(f"Reference bar is indeterminate for {track_id}:{example['barIndex']}.")
        reference_product = str(reference_bar["product"])
        reproduced = (engine_product == reference_product) == bool(example["outcome"]["correct"])
        if not reproduced:
            raise ValueError(f"Reference join did not reproduce {track_id}:{example['barIndex']}.")
        outcome_reproduction_count += 1

        external = _evidence_features(example, btc, nnls)
        combined = {**summary["featureValues"], **external}
        matrix.append([_numeric_feature_value(combined[name]) for name in feature_names])
        engine_products.append(engine_product)
        btc_products.append(btc_product)
        nnls_products.append(nnls_product)
        reference_products.append(reference_product)
        raw_engine_confidence = float(summary["featureValues"].get("productSelectedProbabilityMean") or 0.0)
        engine_confidence.append(raw_engine_confidence)
        checker_agreement = (
            btc_product == nnls_product
            and btc_product != engine_product
            and float(btc_bar["coverage"]) >= CORRECTION_COVERAGE
            and float(nnls_bar["coverage"]) >= CORRECTION_COVERAGE
            and float(btc_bar["dominance"]) >= CORRECTION_DOMINANCE
            and float(nnls_bar["dominance"]) >= CORRECTION_DOMINANCE
        )
        if checker_agreement:
            fixed_predictions.append(btc_product)
            consensus_confidence.append(min(float(btc_bar["dominance"]), float(nnls_bar["dominance"])))
        else:
            fixed_predictions.append(engine_product)
            consensus_confidence.append(raw_engine_confidence)
        roles.append(assignments[str(example["confidenceGroupId"])])
        datasets.append(str(example["confidenceGroupId"]).split(":", 2)[1])

    values = np.asarray(matrix, dtype=np.float64)
    if np.isinf(values).any():
        raise ValueError("Correction matrix contains infinite values.")
    engine_array = np.asarray(engine_products)
    btc_array = np.asarray(btc_products)
    nnls_array = np.asarray(nnls_products)
    reference_array = np.asarray(reference_products)
    fixed_array = np.asarray(fixed_predictions)
    role_array = np.asarray(roles)
    dataset_array = np.asarray(datasets)
    fit_mask = role_array == "fit"
    eval_mask = role_array == "evaluation"

    action_targets = np.full(len(rows), 3, dtype=np.int64)
    action_targets[engine_array == reference_array] = 0
    action_targets[(engine_array != reference_array) & (btc_array == reference_array)] = 1
    action_targets[
        (engine_array != reference_array) & (btc_array != reference_array) & (nnls_array == reference_array)
    ] = 2
    if set(action_targets[fit_mask].tolist()) != {0, 1, 2, 3}:
        raise ValueError("The one-fit source-selector training role lacks a frozen action class.")

    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=20260825,
            solver="lbfgs",
        ),
    )
    model.fit(values[fit_mask], action_targets[fit_mask])
    fit_count = 1
    probabilities = model.predict_proba(values[eval_mask])
    actions = np.asarray(model.classes_)[np.argmax(probabilities, axis=1)]
    selector_confidence = probabilities.max(axis=1)
    eval_engine = engine_array[eval_mask]
    eval_btc = btc_array[eval_mask]
    eval_nnls = nnls_array[eval_mask]
    selector_predictions = eval_engine.copy()
    selector_predictions[actions == 1] = eval_btc[actions == 1]
    selector_predictions[actions == 2] = eval_nnls[actions == 2]
    selector_eligible = actions != 3

    eval_reference = reference_array[eval_mask]
    eval_datasets = dataset_array[eval_mask]
    results = [
        _correction_result(
            candidate=CORRECTION_CANDIDATES[0],
            predictions=eval_engine,
            references=eval_reference,
            engine=eval_engine,
            confidence=np.asarray(engine_confidence)[eval_mask],
            selectively_eligible=np.ones(int(eval_mask.sum()), dtype=bool),
            datasets=eval_datasets,
            fit_count=0,
        ),
        _correction_result(
            candidate=CORRECTION_CANDIDATES[1],
            predictions=fixed_array[eval_mask],
            references=eval_reference,
            engine=eval_engine,
            confidence=np.asarray(consensus_confidence)[eval_mask],
            selectively_eligible=np.ones(int(eval_mask.sum()), dtype=bool),
            datasets=eval_datasets,
            fit_count=0,
        ),
        _correction_result(
            candidate=CORRECTION_CANDIDATES[2],
            predictions=selector_predictions,
            references=eval_reference,
            engine=eval_engine,
            confidence=selector_confidence,
            selectively_eligible=selector_eligible,
            datasets=eval_datasets,
            fit_count=1,
        ),
    ]
    if fit_count != CORRECTION_MAX_FITS or sum(row["fitCount"] for row in results) != 1:
        raise RuntimeError("The frozen one-fit correction cap was not satisfied exactly.")

    reference_rows = [
        {"trackId": track_id, "referenceSha256": digest} for track_id, digest in sorted(reference_receipts.items())
    ]
    report = {
        "schemaVersion": CORRECTION_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "sealedEvaluationOpened": False,
        "deploymentChanged": False,
        "candidateCount": len(CORRECTION_CANDIDATES),
        "candidateFitCount": fit_count,
        "maximumCandidateFits": CORRECTION_MAX_FITS,
        "parameterSearchCount": 0,
        "automaticRetryCount": 0,
        "newFeatureInferenceCount": 0,
        "selectorThreshold": SELECTOR_THRESHOLD,
        "reportingThresholds": list(REPORTING_THRESHOLDS),
        "fixedConsensusRule": {
            "btcAndNnlsProductsMustAgree": True,
            "mustDifferFromEngine": True,
            "minimumCoverage": CORRECTION_COVERAGE,
            "minimumDominance": CORRECTION_DOMINANCE,
        },
        "sourceSelector": {
            "actions": ["engine", "btc", "nnls", "abstain"],
            "targetPrecedence": ["engine-if-correct", "btc-if-correct", "nnls-if-correct", "abstain"],
            "featureCount": len(feature_names),
            "featureNamesSha256": _canonical_sha256(feature_names),
            "estimator": "median-imputed standardized balanced logistic regression",
            "C": 1.0,
            "solver": "lbfgs",
            "maxIterations": 1000,
            "randomState": 20260825,
            "fitActionCounts": {str(action): int((action_targets[fit_mask] == action).sum()) for action in range(4)},
        },
        "split": {
            "id": SPLIT_ID,
            "fitExampleCount": int(fit_mask.sum()),
            "evaluationExampleCount": int(eval_mask.sum()),
            "groupAssignmentsSha256": _canonical_sha256(
                [{"confidenceGroupId": group, "role": role} for group, role in sorted(assignments.items())]
            ),
        },
        "referenceAdmission": {
            "trackCount": len(reference_rows),
            "exampleCount": len(rows),
            "outcomeReproductionCount": outcome_reproduction_count,
            "referenceRowsSha256": _canonical_sha256(reference_rows),
        },
        "source": {
            "examplesSha256": _sha256(examples_path),
            "featureCacheManifestSha256": _sha256(cache / "manifest.json"),
            "benchmarkSha256": _sha256(benchmark_path),
        },
        "candidates": results,
    }
    report["artifactSha256"] = _canonical_sha256(report)
    _atomic_json(output_path, report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--examples", type=Path, required=True)
    prepare.add_argument("--runtime-audio", type=Path, required=True)
    prepare.add_argument("--sealed-cache", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("evaluate")
    run.add_argument("--examples", type=Path, required=True)
    run.add_argument("--cache", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    correct = commands.add_parser("correct")
    correct.add_argument("--examples", type=Path, required=True)
    correct.add_argument("--cache", type=Path, required=True)
    correct.add_argument("--processed-dir", type=Path, required=True)
    correct.add_argument("--benchmark", type=Path, required=True)
    correct.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "prepare":
        receipt = prepare_features(
            examples_path=args.examples,
            runtime_audio_path=args.runtime_audio,
            sealed_cache_path=args.sealed_cache,
            output=args.output,
        )
        print(json.dumps({"trackCount": receipt["trackCount"], "artifactSha256": receipt["artifactSha256"]}))
        return 0
    if args.command == "correct":
        report = evaluate_correction_fusion(
            examples_path=args.examples,
            cache=args.cache,
            processed_dir=args.processed_dir,
            benchmark_path=args.benchmark,
            output_path=args.output,
        )
        print(
            json.dumps(
                {
                    "candidateFitCount": report["candidateFitCount"],
                    "artifactSha256": report["artifactSha256"],
                    "candidates": [
                        {"candidate": row["candidate"], "metrics": row["metrics"]} for row in report["candidates"]
                    ],
                },
                indent=2,
            )
        )
        return 0
    report = evaluate(examples_path=args.examples, cache=args.cache, output_path=args.output)
    print(
        json.dumps(
            {
                "candidateFitCount": report["candidateFitCount"],
                "artifactSha256": report["artifactSha256"],
                "candidates": [
                    {
                        "candidate": row["candidate"],
                        "metrics": row["metrics"],
                    }
                    for row in report["candidates"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
