#!/usr/bin/env python3
"""Run the preregistered, one-pass current chord-reader development evaluation."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping, Sequence

from steel_guitar_rag.chord_reader.factorized import (
    PRODUCT_INDEX,
    factorized_components,
    product_symbol,
)


SPLIT_ID = "bounded-consensus-development-holdout-v1"
EXPECTED = {
    "examples": "69f3a2b240efa4a213c442ce6371375d035753ffaa652b42f2d1daf6f91782ce",
    "benchmark": "059418fd796133e70d3148fdccf978b28214d670dd15da5f6fae355e3ab9bc74",
    "runtime": "be09f0973aa2ad12c626890f3c7015a50faf7ee24fefe4297ee44f14c79b2053",
    "legacy": "bb2a53d00413a8ec036e946adb86f4f483bc40b7f35f67aa55ab314304b68d2e",
    "validation": "452f57fef5996e189d80059da042fddf71d6c1dd5024e171be422e40a8e0c536",
    "phase": "c8c7100dae961e969ffdc6aaa1f873d2d0ac98a117d685ff851ac92ca967852d",
}
REFERENCE_MANIFESTS = (
    "tiny-aam-manifest.json",
    "guitarset-manifest.json",
    "idmt-guitar-manifest.json",
    "nrgcp-manifest.json",
    "winterreise-manifest.json",
)
THRESHOLDS = (0.50, 0.64, 0.80, 0.90, 0.95, 0.98)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def canonical_product(value: str | None) -> str:
    components = factorized_components(value)
    return product_symbol(int(components["root"]), int(components["product"]))


def product_coordinates(value: str | None) -> tuple[int, str, int]:
    components = factorized_components(value)
    root = int(components["root"])
    product = int(components["product"])
    if root == 0:
        mode = "none"
    elif product in {PRODUCT_INDEX["minor"], PRODUCT_INDEX["minor-seventh"]}:
        mode = "minor"
    else:
        mode = "major"
    return root, mode, product


def overlap(start: float, end: float, other_start: float, other_end: float) -> float:
    return max(0.0, min(end, other_end) - max(start, other_start))


def manifest_rows(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, list):
        return value
    for key in ("tracks", "items", "recordings"):
        rows = value.get(key) if isinstance(value, Mapping) else None
        if isinstance(rows, list):
            return rows
    raise ValueError("A processed dataset manifest has no track rows.")


def reference_paths(processed_dir: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for name in REFERENCE_MANIFESTS:
        for row in manifest_rows(read_json(processed_dir / name)):
            track_id = str(row["id"])
            path = Path(row["referencePath"])
            if track_id in result and result[track_id] != path:
                raise ValueError(f"Conflicting reference paths for {track_id}.")
            result[track_id] = path
    return result


def split_groups(examples: Sequence[Mapping[str, Any]]) -> dict[str, str]:
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
            key=lambda group: hashlib.sha256(
                f"{SPLIT_ID}:{dataset}:{group}".encode()
            ).hexdigest(),
        )
        for index, group in enumerate(ordered):
            assignments[group] = "evaluation" if index % 4 == 0 else "fit"
    return assignments


def dominant_product(
    segments: Sequence[Mapping[str, Any]], start: float, end: float, label_key: str = "label"
) -> dict[str, Any]:
    masses: dict[str, float] = defaultdict(float)
    covered = 0.0
    for segment in segments:
        amount = overlap(start, end, float(segment["start"]), float(segment["end"]))
        if amount <= 0:
            continue
        product = canonical_product(str(segment.get(label_key) or "N.C."))
        masses[product] += amount
        covered += amount
    product = max(masses, key=masses.get) if masses else "N.C."
    return {
        "product": product,
        "coverage": covered / max(1e-9, end - start),
        "dominance": masses.get(product, 0.0) / covered if covered else 0.0,
    }


def displayed_segments(bars: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for bar in bars:
        start, end = float(bar["start"]), float(bar["end"])
        symbols = list(bar["chordSymbols"])
        if len(symbols) == 2:
            middle = start + (end - start) / 2
            result.extend(
                [
                    {"start": start, "end": middle, "label": symbols[0]},
                    {"start": middle, "end": end, "label": symbols[1]},
                ]
            )
        else:
            result.append({"start": start, "end": end, "label": symbols[0]})
    return result


def timeline_scores(
    reference: Sequence[Mapping[str, Any]],
    displayed: Sequence[Mapping[str, Any]],
    windows: Sequence[tuple[float, float]],
) -> dict[str, float]:
    totals = {"duration": 0.0, "root": 0.0, "majorMinor": 0.0, "product": 0.0}
    for window_start, window_end in windows:
        for ref in reference:
            ref_start = max(window_start, float(ref["start"]))
            ref_end = min(window_end, float(ref["end"]))
            if ref_end <= ref_start:
                continue
            ref_product = canonical_product(str(ref.get("label") or "N.C."))
            ref_root, ref_mode, ref_class = product_coordinates(ref_product)
            ref_duration = ref_end - ref_start
            totals["duration"] += ref_duration
            for current in displayed:
                amount = overlap(
                    ref_start,
                    ref_end,
                    float(current["start"]),
                    float(current["end"]),
                )
                if amount <= 0:
                    continue
                cur_product = canonical_product(str(current["label"]))
                cur_root, cur_mode, cur_class = product_coordinates(cur_product)
                if cur_root == ref_root:
                    totals["root"] += amount
                if (cur_root, cur_mode) == (ref_root, ref_mode):
                    totals["majorMinor"] += amount
                if (cur_root, cur_class) == (ref_root, ref_class):
                    totals["product"] += amount
    duration = totals.pop("duration")
    return {key: value / duration if duration else 0.0 for key, value in totals.items()} | {
        "evaluatedDurationSeconds": duration
    }


def summarize_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    chord_correct = sum(bool(row["chordCorrect"]) for row in rows)
    return {
        "barCount": count,
        "chordCorrect": chord_correct,
        "chordAccuracy": chord_correct / count if count else 0.0,
        "selectiveChordCurve": [
            {
                "minimumDisplayedConfidence": threshold,
                "acceptedCount": accepted_count,
                "correctCount": correct_count,
                "coverage": accepted_count / count if count else 0.0,
                "precision": correct_count / accepted_count if accepted_count else None,
            }
            for threshold in THRESHOLDS
            for accepted in [[row for row in rows if float(row["displayedConfidence"]) >= threshold]]
            for accepted_count in [len(accepted)]
            for correct_count in [sum(bool(row["chordCorrect"]) for row in accepted)]
        ],
    }


def score_bar_set(
    examples: Sequence[Mapping[str, Any]],
    references: Mapping[str, Sequence[Mapping[str, Any]]],
    bars_by_track: Mapping[str, Sequence[Mapping[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for example in examples:
        track_id = str(example["trackId"])
        summary = example["barSummary"]
        start, end = float(summary["start"]), float(summary["end"])
        bars = list(bars_by_track[track_id])
        matched = min(bars, key=lambda bar: abs(float(bar["start"]) - start))
        ref = dominant_product(references[track_id], start, end)
        symbols = list(matched["chordSymbols"])
        current_product = canonical_product(str(symbols[0]))
        chord_correct = current_product == ref["product"]
        rows.append(
            {
                "trackId": track_id,
                "dataset": str(example["confidenceGroupId"]).split(":", 2)[1],
                "barIndex": int(example["barIndex"]),
                "referenceProduct": ref["product"],
                "displayedProduct": current_product,
                "displayedChordSymbols": symbols,
                "displayedConfidence": float(matched["confidence"]),
                "chordCorrect": chord_correct,
            }
        )
    by_dataset = {
        dataset: summarize_rows([row for row in rows if row["dataset"] == dataset])
        for dataset in sorted({str(row["dataset"]) for row in rows})
    }
    return rows, {"aggregate": summarize_rows(rows), "datasets": by_dataset}


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    experiment = root.parent / "tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1"
    bounded = root.parent / "tmp/chord-reader-v9/experiments/bounded-consensus-development-v1"
    parser.add_argument("--experiment", type=Path, default=experiment)
    parser.add_argument("--bounded", type=Path, default=bounded)
    parser.add_argument("--processed-dir", type=Path, default=root.parent / "tmp/chord-reader-v4/processed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    paths = {
        "examples": args.experiment / "examples/examples.json",
        "benchmark": args.experiment / "benchmark/report.json",
        "runtime": args.experiment / "runtime-beat-receipt.json",
        "legacy": args.bounded / "report.json",
        "validation": root / "ui/chord-reader-travis-validation/validation.js",
        "phase": root / "ui/chord-reader-travis-validation/phase-anchor.js",
    }
    observed_hashes = {name: file_sha256(path) for name, path in paths.items()}
    if observed_hashes != EXPECTED:
        raise ValueError(f"Frozen input hash mismatch: {observed_hashes}")

    examples_artifact = read_json(paths["examples"])
    all_examples = list(examples_artifact["examples"])
    assignments = split_groups(all_examples)
    examples = [
        example
        for example in all_examples
        if assignments[str(example["confidenceGroupId"])] == "evaluation"
    ]
    if len(examples) != 623 or sum(bool(row["outcome"]["correct"]) for row in examples) != 498:
        raise ValueError("Frozen 623-bar / 498-correct legacy split did not reproduce.")

    benchmark = read_json(paths["benchmark"])
    benchmark_by_id = {str(row["id"]): row for row in benchmark["tracks"]}
    runtime = read_json(paths["runtime"])
    runtime_by_id = {str(row["trackId"]): row for row in runtime["tracks"]}
    refs_by_path = reference_paths(args.processed_dir)
    evaluation_track_ids = sorted({str(example["trackId"]) for example in examples})

    references: dict[str, list[Mapping[str, Any]]] = {}
    raw_predictions: dict[str, list[dict[str, Any]]] = {}
    node_tracks: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    for track_id in evaluation_track_ids:
        bench = benchmark_by_id[track_id]
        timing = runtime_by_id[track_id]
        prediction_path = args.experiment / "benchmark" / str(bench["predictionFile"])
        reference_path = refs_by_path[track_id]
        if file_sha256(prediction_path) != str(bench["predictionSha256"]):
            raise ValueError(f"Prediction hash mismatch for {track_id}.")
        if file_sha256(reference_path) != str(bench["referenceSha256"]):
            raise ValueError(f"Reference hash mismatch for {track_id}.")
        if str(timing["audioSha256"]) != str(bench["sourceAudioSha256"]):
            raise ValueError(f"Runtime audio hash mismatch for {track_id}.")
        prediction = read_json(prediction_path)
        reference = read_json(reference_path)
        references[track_id] = list(reference["segments"])
        raw_predictions[track_id] = [
            {
                "start": float(segment["start"]),
                "end": float(segment["end"]),
                "label": str(segment.get("productLabel") or segment.get("label") or "N.C."),
            }
            for segment in prediction["segments"]
        ]
        node_tracks.append(
            {
                "id": track_id,
                "segments": prediction["segments"],
                "beatTimesSeconds": [float(value) / 1000 for value in timing["beatTimesMs"]],
                "beatsPerBar": int(timing["beatsPerBar"]),
                "durationSeconds": float(prediction["durationSeconds"]),
            }
        )
        binding_rows.append(
            {
                "trackId": track_id,
                "audioSha256": bench["sourceAudioSha256"],
                "predictionSha256": bench["predictionSha256"],
                "referenceSha256": bench["referenceSha256"],
                "runtimeTrackReceiptSha256": timing["trackReceiptSha256"],
            }
        )

    # Recompute the legacy result from the bound references, rather than trusting
    # the stored outcome booleans alone.
    reproduced = 0
    for example in examples:
        summary = example["barSummary"]
        ref = dominant_product(
            references[str(example["trackId"])],
            float(summary["start"]),
            float(summary["end"]),
        )
        engine = canonical_product(str(summary.get("predictionProduct") or "N.C."))
        correct = engine == ref["product"]
        if correct != bool(example["outcome"]["correct"]):
            raise ValueError(f"Legacy reference join mismatch at {example['trackId']}:{example['barIndex']}.")
        reproduced += int(correct)
    if reproduced != 498:
        raise ValueError("Reference-bound legacy reproduction was not 498/623.")

    adapter = root / "scripts/build_current_chord_reader_bars.js"
    process = subprocess.run(
        ["node", str(adapter)],
        input=json.dumps({"tracks": node_tracks}),
        text=True,
        capture_output=True,
        check=True,
    )
    built = json.loads(process.stdout)
    built_by_id = {str(row["id"]): row for row in built["tracks"]}
    baseline_bars = {track_id: built_by_id[track_id]["baselineBars"] for track_id in evaluation_track_ids}
    current_bars = {track_id: built_by_id[track_id]["currentBars"] for track_id in evaluation_track_ids}

    baseline_rows, baseline_score = score_bar_set(examples, references, baseline_bars)
    current_rows, current_score = score_bar_set(examples, references, current_bars)
    windows_by_track: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for example in examples:
        summary = example["barSummary"]
        windows_by_track[str(example["trackId"])].append(
            (float(summary["start"]), float(summary["end"]))
        )

    def timeline_report(display_map: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
        raw = [
            timeline_scores(references[track_id], display_map[track_id], windows_by_track[track_id])
            for track_id in evaluation_track_ids
        ]
        duration = sum(row["evaluatedDurationSeconds"] for row in raw)
        aggregate = {
            "evaluatedDurationSeconds": duration,
            **{
                key: sum(row[key] * row["evaluatedDurationSeconds"] for row in raw) / duration
                for key in ("root", "majorMinor", "product")
            },
        }
        dataset_by_track = {
            str(example["trackId"]): str(example["confidenceGroupId"]).split(":", 2)[1]
            for example in examples
        }
        datasets: dict[str, Any] = {}
        for dataset in sorted(set(dataset_by_track.values())):
            selected = [
                row
                for track_id, row in zip(evaluation_track_ids, raw)
                if dataset_by_track[track_id] == dataset
            ]
            selected_duration = sum(row["evaluatedDurationSeconds"] for row in selected)
            datasets[dataset] = {
                "evaluatedDurationSeconds": selected_duration,
                **{
                    key: sum(row[key] * row["evaluatedDurationSeconds"] for row in selected)
                    / selected_duration
                    for key in ("root", "majorMinor", "product")
                },
            }
        return {"aggregate": aggregate, "datasets": datasets}

    baseline_display = {
        track_id: displayed_segments(baseline_bars[track_id]) for track_id in evaluation_track_ids
    }
    current_display = {
        track_id: displayed_segments(current_bars[track_id]) for track_id in evaluation_track_ids
    }

    phases = [built_by_id[track_id] for track_id in evaluation_track_ids]
    structural = {
        "trackCount": len(phases),
        "anchoredTrackCount": sum(row["phase"]["status"] == "anchored" for row in phases),
        "unresolvedTrackCount": sum(row["phase"]["status"] == "unresolved" for row in phases),
        "phaseShiftedTrackCount": sum(
            row["phase"]["status"] == "anchored" and int(row["appliedPhase"]) != 0
            for row in phases
        ),
        "appliedPhaseCounts": dict(sorted(Counter(int(row["appliedPhase"]) for row in phases).items())),
        "baselineBarCount": sum(len(row["baselineBars"]) for row in phases),
        "currentBarCount": sum(len(row["currentBars"]) for row in phases),
        "currentSplitBarCount": sum(
            len(bar["chordSymbols"]) == 2 for row in phases for bar in row["currentBars"]
        ),
        "currentSupportedSplitBarCount": sum(
            bool(bar["splitSupported"]) for row in phases for bar in row["currentBars"]
        ),
        "currentUncertainSplitBarCount": sum(
            bool(bar["splitUncertain"]) for row in phases for bar in row["currentBars"]
        ),
    }

    report = {
        "schemaVersion": "chord_reader_current_end_to_end_development_v1",
        "developmentOnly": True,
        "promotionEligible": False,
        "worldClassClaimCertified": False,
        "frozenProductRevision": "7336f5dc",
        "split": SPLIT_ID,
        "thresholds": {
            "displayedConfidence": list(THRESHOLDS),
            "phaseMinimumAnchors": 8,
            "phaseMinimumMargin": 0.12,
        },
        "bindings": {
            "inputSha256": observed_hashes,
            "evaluationTrackCount": len(evaluation_track_ids),
            "evaluationBarCount": len(examples),
            "trackSetSha256": canonical_sha256(binding_rows),
        },
        "legacyOracleWindow": {
            "correctCount": reproduced,
            "barCount": len(examples),
            "accuracy": reproduced / len(examples),
        },
        "timingAccuracy": {
            "available": False,
            "reason": "The frozen bar windows come from the runtime grid and are not independent downbeat annotations.",
        },
        "rawEngineTimeline": timeline_report(raw_predictions),
        "predictedGridBeforePhaseBacksolve": {
            **baseline_score,
            "timeline": timeline_report(baseline_display),
        },
        "currentPredictedGrid": {
            **current_score,
            "timeline": timeline_report(current_display),
        },
        "structural": structural,
        "perBarRows": current_rows,
        "baselinePerBarRowsSha256": canonical_sha256(baseline_rows),
    }
    report["artifactSha256"] = canonical_sha256(report)
    if args.output.exists():
        raise FileExistsError("Current evaluation output already exists; automatic retry is forbidden.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "artifactSha256", "legacyOracleWindow", "timingAccuracy", "rawEngineTimeline",
        "predictedGridBeforePhaseBacksolve", "currentPredictedGrid", "structural"
    )}, indent=2))


if __name__ == "__main__":
    main()
