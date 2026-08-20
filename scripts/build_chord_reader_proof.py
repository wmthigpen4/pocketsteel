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
from steel_guitar_rag.chord_reader.student import StudentRecognizer


TRACK_MANIFEST = REPO_ROOT / "steel_guitar_rag/resources/song_practice_tracks/manifest.json"
TRACK_IDS = (
    "amazing-grace-kevin-macleod-lesson-v1",
    "when-the-saints-preview-v1",
    "oh-susanna-preview-v1",
)
DEFAULT_TRACK_ID = TRACK_IDS[0]
MODEL = REPO_ROOT / "ui/models/chord-student-v1.onnx"
DEFAULT_OUTPUT = REPO_ROOT / "ui/chord-reader-proof/data"
PUBLIC_REPORTS = {
    "v2": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/v2.json",
    "btc": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/btc.json",
    "student": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/student.json",
    "hybrid": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/hybrid.json",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
                    "student": "Raw chord-student-v1",
                    "hybrid": "Hardened hybrid v1",
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


def build(output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    recognizer = StudentRecognizer(MODEL)
    track_proofs = [_build_track(track, output_root, recognizer) for track in _tracks()]
    public_reports = {name: _read_json(path) for name, path in PUBLIC_REPORTS.items()}
    proof = {
        "schemaVersion": "chord_reader_visual_proof_v2",
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
        "publicBenchmark": {
            "dataset": "GuitarSet",
            "sourceUrl": "https://zenodo.org/records/3371780",
            "split": "composition-grouped held-out test",
            "trackCount": public_reports["student"]["aggregate"]["trackCount"],
            "audioSeconds": public_reports["student"]["aggregate"]["evaluatedDurationSeconds"],
            "engines": {
                name: {
                    "majorMinorWcsr": report["aggregate"]["majorMinorWeightedRecall"],
                    "rootWcsr": report["aggregate"]["rootWeightedRecall"],
                    "detailedWcsr": report["aggregate"]["detailedWeightedRecall"],
                    "boundaryF1": report["aggregate"]["boundaryF1Macro"],
                }
                for name, report in public_reports.items()
            },
            "trainingDisclosure": "The student trained on 264 GuitarSet recordings, selected on 60 development recordings, and was scored once on these 36 held-out recordings.",
            "aamDisclosure": "AAM annotation import is implemented and tested, but AAM audio was not downloaded or used in this model run.",
            "lofiDisclosure": "Lo-Fi Chords was rejected for supervised use because its public metadata archive contains no chord progression ground truth.",
        },
        "reproduce": {
            "command": "python scripts/build_chord_reader_proof.py",
            "modelSha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
            "audioSha256": {track["track"]["id"]: track["track"]["audioSha256"] for track in track_proofs},
        },
    }
    _write_json(output_root / "proof.json", proof)
    return proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    proof = build(args.output_root)
    print(json.dumps(proof["suite"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
