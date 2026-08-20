"""Reproducible multi-engine benchmark runner and aggregate reports."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping

from .btc import BTCRecognizer
from .hybrid import hybridize_predictions
from .metrics import score_segments
from .student import StudentRecognizer


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _aggregate(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    values = list(rows)
    duration = sum(float(row["metrics"]["evaluatedDurationSeconds"]) for row in values)
    weighted_names = ("rootWeightedRecall", "majorMinorWeightedRecall", "detailedWeightedRecall")
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
            "sequenceEditRateMacro": sum(float(row["metrics"]["sequenceEditRate"]) for row in values)
            / max(1, len(values)),
            "elapsedSeconds": sum(float(row["elapsedSeconds"]) for row in values),
        }
    )
    return output


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
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    tracks = [track for track in manifest["tracks"] if split == "all" or track["split"] == split]
    if limit is not None:
        tracks = tracks[:limit]
    if not tracks:
        raise ValueError(f"No tracks selected for split {split!r}.")
    if engine == "btc":
        recognizer: Any = BTCRecognizer(device=device, local_files_only=local_files_only)
    elif engine == "student":
        if model is None:
            raise ValueError("The student benchmark requires --model.")
        recognizer = StudentRecognizer(model)
    else:
        recognizer = None
    rows: list[dict[str, Any]] = []
    for track in tracks:
        prediction_path = output_root / "predictions" / engine / f"{track['id']}.json"
        started = time.perf_counter()
        if engine in {"btc", "student"}:
            prediction = recognizer.predict(Path(track["audioPath"]), prediction_id=str(track["id"]))
            _write_json(prediction_path, prediction)
        elif engine == "v2":
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            prediction = _v2_prediction(repo_root, track, prediction_path)
        else:
            raise ValueError(f"Unsupported benchmark engine {engine!r}.")
        elapsed = time.perf_counter() - started
        reference = json.loads(Path(track["referencePath"]).read_text(encoding="utf-8"))
        metrics = score_segments(reference["segments"], prediction["segments"])
        rows.append(
            {
                "id": track["id"],
                "datasetId": track["datasetId"],
                "split": track["split"],
                "elapsedSeconds": elapsed,
                "audioDurationSeconds": prediction.get("durationSeconds"),
                "metrics": metrics,
                "predictionFile": f"predictions/{engine}/{track['id']}.json",
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
                "metrics": score_segments(reference["segments"], prediction["segments"]),
                "predictionFile": f"predictions/hybrid/{identifier}.json",
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
