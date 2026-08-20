#!/usr/bin/env python3
"""Build the committed, inspectable public-domain chord-reader proof suite."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.hybrid import hybridize_predictions
from steel_guitar_rag.chord_reader.labels import normalize_chord
from steel_guitar_rag.chord_reader.metrics import score_segments
from steel_guitar_rag.chord_reader.student import (
    StudentBoundaryGuidedEnsembleRecognizer,
    StudentEnsembleRecognizer,
    StudentHeterogeneousBoundaryGuidedEnsembleRecognizer,
    StudentRecognizer,
)


TRACK_MANIFEST = REPO_ROOT / "steel_guitar_rag/resources/song_practice_tracks/manifest.json"
TRACK_IDS = (
    "amazing-grace-kevin-macleod-lesson-v1",
    "when-the-saints-preview-v1",
    "oh-susanna-preview-v1",
)
DEFAULT_TRACK_ID = TRACK_IDS[0]
MODELS = (
    REPO_ROOT / "ui/models/chord-multiband-tcn-v2.onnx",
    REPO_ROOT / "ui/models/chord-multiband-transformer-v2.onnx",
    REPO_ROOT / "ui/models/chord-multiband-idmt-tcn-v3.onnx",
    REPO_ROOT / "ui/models/chord-harmonic-cqt-transformer-v4.onnx",
)
MODEL_WEIGHTS = (1.0, 1.0, 1.0, 0.3)
BOUNDARY_MODEL = REPO_ROOT / "ui/models/chord-boundary-transformer-v3.onnx"
SECONDARY_BOUNDARY_MODEL = REPO_ROOT / "ui/models/chord-boundary-nrgcp-transformer-v5.onnx"
QUALITY_MODELS = (
    REPO_ROOT / "ui/models/chord-quality-nrgcp-multiband-v5.onnx",
    REPO_ROOT / "ui/models/chord-quality-nrgcp-cqt-v5.onnx",
)
DOMAIN_GATE = REPO_ROOT / "ui/models/chord-domain-gate-v1.json"
SEALED_SUMMARY = REPO_ROOT / "chord_reader/benchmarks/domain-gated-v8/sealed-summary.json"
DEFAULT_OUTPUT = REPO_ROOT / "ui/chord-reader-proof/data"
def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _display_path(path: Path) -> Path:
    return path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path


def _tracks() -> list[Mapping[str, Any]]:
    manifest = _read_json(TRACK_MANIFEST)
    by_id = {str(item["id"]): item for item in manifest["tracks"]}
    return [by_id[track_id] for track_id in TRACK_IDS]


def _chart_cells(chart: str) -> list[list[str]]:
    without_sections = re.sub(r"\[[^]]+\]", "", chart)
    return [part.strip().split() for part in without_sections.split("|") if part.strip()]


def _reference(track: Mapping[str, Any]) -> dict[str, Any]:
    cells = _chart_cells(str(track["chart"]))
    starts = [float(value) / 1000 for value in track["barStartsMs"]]
    duration = float(track["durationMs"]) / 1000
    if len(cells) != len(starts):
        raise ValueError(f"Expected one chart cell per bar; found {len(cells)} cells and {len(starts)} bars.")
    segments: list[dict[str, Any]] = []
    if starts[0] > 0:
        segments.append({"start": 0.0, "end": starts[0], "label": "N"})
    for index, (start, chords) in enumerate(zip(starts, cells, strict=True)):
        end = starts[index + 1] if index + 1 < len(starts) else duration
        chord_duration = (end - start) / len(chords)
        for chord_index, chord in enumerate(chords):
            chord_start = start + chord_index * chord_duration
            chord_end = end if chord_index + 1 == len(chords) else chord_start + chord_duration
            segments.append(
                {"start": chord_start, "end": chord_end, "label": normalize_chord(chord).detailed_symbol}
            )
    return {
        "schemaVersion": "chord_reference_v1",
        "id": track["id"],
        "title": track["title"],
        "source": "hand-authored Steel Guitar RAG lesson timeline",
        "durationSeconds": duration,
        "barStartsSeconds": starts,
        "segments": segments,
    }


def _v2(track: Mapping[str, Any], audio: Path, output: Path) -> dict[str, Any]:
    command = [
        "node",
        str(REPO_ROOT / "scripts/chord_reader_v2.js"),
        "--audio",
        str(audio),
        "--output",
        str(output),
        "--id",
        str(track["id"]),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"The v2 proof run failed for {track['id']}.")
    return _read_json(output)


def _overlap(start: float, end: float, segment: Mapping[str, Any]) -> float:
    return max(0.0, min(end, float(segment["end"])) - max(start, float(segment["start"])))


def _labels_in_interval(segments: Sequence[Mapping[str, Any]], start: float, end: float) -> list[str]:
    labels: list[str] = []
    for segment in segments:
        if _overlap(start, end, segment) <= 0:
            continue
        label = normalize_chord(str(segment.get("productLabel") or segment.get("label") or "N")).product_symbol
        if not labels or labels[-1] != label:
            labels.append(label)
    return labels or ["N.C."]


def _dominant_label(segments: Sequence[Mapping[str, Any]], start: float, end: float) -> str:
    totals: dict[str, float] = {}
    for segment in segments:
        duration = _overlap(start, end, segment)
        if not duration:
            continue
        label = normalize_chord(str(segment.get("productLabel") or segment.get("label") or "N")).product_symbol
        totals[label] = totals.get(label, 0.0) + duration
    return max(totals, key=totals.get) if totals else "N.C."


def _major_minor_key(symbol: str) -> tuple[str | None, str]:
    label = normalize_chord(symbol)
    if label.root is None:
        return None, "none"
    return label.root, "minor" if label.quality.startswith("min") else "major"


def _bar_score(reference: Sequence[Mapping[str, Any]], prediction: Sequence[Mapping[str, Any]]) -> float:
    return float(score_segments(reference, prediction)["majorMinorWeightedRecall"])


def _bar_rows(
    reference: Mapping[str, Any], engines: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    starts = reference["barStartsSeconds"]
    duration = float(reference["durationSeconds"])
    rows: list[dict[str, Any]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else duration
        truth = [segment for segment in reference["segments"] if _overlap(start, end, segment) > 0]
        truth_labels = _labels_in_interval(truth, start, end)
        row: dict[str, Any] = {
            "bar": index + 1,
            "start": start,
            "end": end,
            "expected": " → ".join(truth_labels),
        }
        for name, prediction in engines.items():
            row[name] = _dominant_label(prediction["segments"], start, end)
            row[f"{name}Score"] = _bar_score(truth, prediction["segments"])
            row[f"{name}Correct"] = (
                _major_minor_key(row[name]) == _major_minor_key(truth_labels[0])
                if len(truth_labels) == 1
                else row[f"{name}Score"] >= 0.75
            )
        rows.append(row)
    return rows


def _track_metadata(track: Mapping[str, Any], reference: Mapping[str, Any], audio: Path) -> dict[str, Any]:
    licensed_human_performance = bool(track.get("rightsUrl"))
    return {
        "id": track["id"],
        "title": track["title"],
        "performer": track.get("performer") or track.get("performerCredits") or "Steel Guitar RAG practice master",
        "audioUrl": f"/{track['audioPath']}",
        "rightsUrl": track.get("rightsUrl"),
        "license": track.get("license") or ("App-owned deterministic master" if not licensed_human_performance else "Reviewed license"),
        "licenseUrl": track.get("licenseUrl"),
        "recordingCredit": track.get("recordingCredit") or track.get("performerCredits"),
        "modifications": track.get("modifications") or track.get("masterRightsBasis"),
        "compositionStatus": track.get("compositionStatus"),
        "recordingType": "licensed human performance" if licensed_human_performance else "app-owned deterministic performance",
        "key": track.get("key"),
        "meter": track.get("meter"),
        "tempo": track.get("tempo"),
        "durationSeconds": reference["durationSeconds"],
        "audioSha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
    }


def _aggregate(track_proofs: Iterable[Mapping[str, Any]], engine: str) -> dict[str, Any]:
    values = list(track_proofs)
    duration = sum(float(track["engines"][engine]["metrics"]["evaluatedDurationSeconds"]) for track in values)
    return {
        name: sum(
            float(track["engines"][engine]["metrics"][name])
            * float(track["engines"][engine]["metrics"]["evaluatedDurationSeconds"])
            for track in values
        )
        / max(1e-12, duration)
        for name in ("majorMinorWeightedRecall", "rootWeightedRecall", "detailedWeightedRecall")
    }


def _build_track(
    track: Mapping[str, Any], output_root: Path, recognizer: StudentRecognizer
) -> dict[str, Any]:
    track_root = output_root / "tracks" / str(track["id"])
    track_root.mkdir(parents=True, exist_ok=True)
    audio = REPO_ROOT / str(track["audioPath"])
    reference = _reference(track)
    v2_path = track_root / "v2.json"
    v2 = _v2(track, audio, v2_path)
    student = recognizer.predict(audio, prediction_id=str(track["id"]))
    hybrid = hybridize_predictions(v2, student)
    engines = {"v2": v2, "student": student, "hybrid": hybrid}
    rows = _bar_rows(reference, engines)
    proof = {
        "track": _track_metadata(track, reference, audio),
        "reference": {
            "source": reference["source"],
            "metricsLabel": "hand-authored expected chord timeline",
            "segments": reference["segments"],
        },
        "engines": {
            name: {
                "label": {
                    "v2": "Current Play Along v2",
                    "student": "Domain-gated root-quality-boundary ensemble v8",
                    "hybrid": "Conservative no-chord safety overlay",
                }[name],
                "metrics": score_segments(reference["segments"], prediction["segments"]),
                "segments": prediction["segments"],
            }
            for name, prediction in engines.items()
        },
        "bars": rows,
        "summary": {
            "barCount": len(rows),
            **{
                f"{name}CorrectBars": sum(bool(row[f"{name}Correct"]) for row in rows)
                for name in engines
            },
        },
    }
    _write_json(track_root / "reference.json", reference)
    _write_json(track_root / "student.json", student)
    _write_json(track_root / "hybrid.json", hybrid)
    return proof


def build(
    output_root: Path,
    models: Sequence[Path] | None = None,
    boundary_model: Path | None = None,
    model_weights: Sequence[float] | None = None,
    root_guide_only: bool = False,
    secondary_boundary_model: Path | None = None,
    secondary_boundary_weight: float = 0.5,
    quality_models: Sequence[Path] | None = None,
    domain_gate: Path | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    selected_models = models or MODELS
    model_paths = [path if path.is_absolute() else (REPO_ROOT / path).resolve() for path in selected_models]
    if models is None:
        if boundary_model is None:
            boundary_model = BOUNDARY_MODEL
        if model_weights is None:
            model_weights = MODEL_WEIGHTS
        root_guide_only = True
        secondary_boundary_model = secondary_boundary_model or SECONDARY_BOUNDARY_MODEL
        quality_models = quality_models or QUALITY_MODELS
        domain_gate = domain_gate or DOMAIN_GATE
    boundary_path = (
        boundary_model if boundary_model is None or boundary_model.is_absolute() else (REPO_ROOT / boundary_model).resolve()
    )
    secondary_boundary_path = (
        secondary_boundary_model
        if secondary_boundary_model is None or secondary_boundary_model.is_absolute()
        else (REPO_ROOT / secondary_boundary_model).resolve()
    )
    quality_paths = [path if path.is_absolute() else (REPO_ROOT / path).resolve() for path in quality_models or []]
    domain_gate_path = domain_gate if domain_gate is None or domain_gate.is_absolute() else (REPO_ROOT / domain_gate).resolve()
    if model_weights:
        if boundary_path is None:
            raise ValueError("Weighted proof ensembles require a boundary model.")
        recognizer = StudentHeterogeneousBoundaryGuidedEnsembleRecognizer(
            model_paths,
            model_weights,
            boundary_path,
            secondary_boundary_model=secondary_boundary_path,
            secondary_boundary_weight=secondary_boundary_weight,
            root_guide_only=root_guide_only,
            quality_models=quality_paths,
            quality_mode_threshold=0.55,
            quality_extension_threshold=0.65,
            factorized_decoder=True,
            product_boundary_scale=1.3,
            product_boundary_bias=-2.0,
            domain_gate=domain_gate_path,
        )
    elif boundary_path is not None:
        recognizer = StudentBoundaryGuidedEnsembleRecognizer(model_paths, boundary_path)
    else:
        recognizer = (
            StudentEnsembleRecognizer(model_paths)
            if len(model_paths) > 1
            else StudentRecognizer(model_paths[0])
        )
    track_proofs = [_build_track(track, output_root, recognizer) for track in _tracks()]
    proof = {
        "schemaVersion": "chord_reader_visual_proof_v2",
        "candidateLabel": (
            "Domain-gated root, quality, and boundary ensemble"
            if root_guide_only
            else "Boundary-guided multiband TCN + Transformer ensemble"
            if boundary_path is not None
            else "Multiband TCN + Transformer ensemble"
            if len(model_paths) > 1
            else "Raw chord model"
        ),
        "defaultTrackId": DEFAULT_TRACK_ID,
        "tracks": track_proofs,
        "suite": {
            "trackCount": len(track_proofs),
            "durationSeconds": sum(float(track["track"]["durationSeconds"]) for track in track_proofs),
            "engines": {name: _aggregate(track_proofs, name) for name in ("v2", "student", "hybrid")},
            "barTotals": {
                name: sum(int(track["summary"][f"{name}CorrectBars"]) for track in track_proofs)
                for name in ("v2", "student", "hybrid")
            },
            "barCount": sum(int(track["summary"]["barCount"]) for track in track_proofs),
        },
        "publicBenchmark": _read_json(SEALED_SUMMARY),
        "reproduce": {
            "command": "python scripts/build_chord_reader_proof.py "
            + " ".join(f"--model {_display_path(path)}" for path in model_paths)
            + (
                " " + " ".join(f"--model-weight {weight}" for weight in model_weights)
                if model_weights
                else ""
            )
            + (f" --boundary-model {_display_path(boundary_path)}" if boundary_path else "")
            + (
                f" --secondary-boundary-model {_display_path(secondary_boundary_path)}"
                f" --secondary-boundary-weight {secondary_boundary_weight}"
                if secondary_boundary_path
                else ""
            )
            + "".join(f" --quality-model {_display_path(path)}" for path in quality_paths)
            + (f" --domain-gate {_display_path(domain_gate_path)}" if domain_gate_path else "")
            + (" --root-guide-only" if root_guide_only else ""),
            "modelSha256": " / ".join(
                hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [
                    *model_paths,
                    *([boundary_path] if boundary_path else []),
                    *([secondary_boundary_path] if secondary_boundary_path else []),
                    *quality_paths,
                    *([domain_gate_path] if domain_gate_path else []),
                ]
            ),
            "audioSha256": {track["track"]["id"]: track["track"]["audioSha256"] for track in track_proofs},
        },
    }
    _write_json(output_root / "proof.json", proof)
    return proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", type=Path, action="append", dest="models")
    parser.add_argument("--boundary-model", type=Path)
    parser.add_argument("--secondary-boundary-model", type=Path)
    parser.add_argument("--secondary-boundary-weight", type=float, default=0.5)
    parser.add_argument("--quality-model", type=Path, action="append", dest="quality_models")
    parser.add_argument("--domain-gate", type=Path)
    parser.add_argument("--model-weight", type=float, action="append", dest="model_weights")
    parser.add_argument("--root-guide-only", action="store_true")
    args = parser.parse_args()
    proof = build(
        args.output_root,
        args.models,
        args.boundary_model,
        args.model_weights,
        args.root_guide_only,
        args.secondary_boundary_model,
        args.secondary_boundary_weight,
        args.quality_models,
        args.domain_gate,
    )
    print(json.dumps(proof["suite"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
