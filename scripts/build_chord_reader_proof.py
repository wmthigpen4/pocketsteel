#!/usr/bin/env python3
"""Build the committed, inspectable Amazing Grace chord-reader proof data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.labels import normalize_chord
from steel_guitar_rag.chord_reader.metrics import score_segments
from steel_guitar_rag.chord_reader.student import StudentRecognizer


TRACK_MANIFEST = REPO_ROOT / "steel_guitar_rag/resources/song_practice_tracks/manifest.json"
TRACK_ID = "amazing-grace-kevin-macleod-lesson-v1"
MODEL = REPO_ROOT / "ui/models/chord-student-v1.onnx"
DEFAULT_OUTPUT = REPO_ROOT / "ui/chord-reader-proof/data"
PUBLIC_REPORTS = {
    "v2": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/v2.json",
    "btc": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/btc.json",
    "student": REPO_ROOT / "chord_reader/benchmarks/guitarset-v1/student.json",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _track() -> Mapping[str, Any]:
    manifest = _read_json(TRACK_MANIFEST)
    return next(item for item in manifest["tracks"] if item["id"] == TRACK_ID)


def _chart_chords(chart: str) -> list[str]:
    without_sections = re.sub(r"\[[^]]+\]", "", chart)
    return [part.strip() for part in without_sections.split("|") if part.strip()]


def _reference(track: Mapping[str, Any]) -> dict[str, Any]:
    chords = _chart_chords(str(track["chart"]))
    starts = [float(value) / 1000 for value in track["barStartsMs"]]
    duration = float(track["durationMs"]) / 1000
    if len(chords) != len(starts):
        raise ValueError(f"Expected one chart chord per bar; found {len(chords)} chords and {len(starts)} bars.")
    segments: list[dict[str, Any]] = []
    if starts[0] > 0:
        segments.append({"start": 0.0, "end": starts[0], "label": "N"})
    for index, (start, chord) in enumerate(zip(starts, chords, strict=True)):
        end = starts[index + 1] if index + 1 < len(starts) else duration
        segments.append({"start": start, "end": end, "label": normalize_chord(chord).detailed_symbol})
    return {
        "schemaVersion": "chord_reference_v1",
        "id": TRACK_ID,
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
        TRACK_ID,
        "--key",
        str(track["key"]),
        "--mode",
        "major",
        "--meter",
        str(track["meter"]),
        "--tempo",
        str(track["tempo"]),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "The v2 proof run failed.")
    return _read_json(output)


def _overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return max(0.0, min(float(left["end"]), float(right["end"])) - max(float(left["start"]), float(right["start"])))


def _dominant_label(segments: Sequence[Mapping[str, Any]], start: float, end: float) -> str:
    bar = {"start": start, "end": end}
    totals: dict[str, float] = {}
    for segment in segments:
        duration = _overlap(bar, segment)
        if duration:
            label = normalize_chord(str(segment.get("label") or "N")).product_symbol
            totals[label] = totals.get(label, 0.0) + duration
    return max(totals, key=totals.get) if totals else "N.C."


def _major_minor_key(symbol: str) -> tuple[str | None, str]:
    label = normalize_chord(symbol)
    if label.root is None:
        return None, "none"
    quality = "minor" if label.quality.startswith("min") else "major"
    return label.root, quality


def _bar_rows(
    reference: Mapping[str, Any], v2: Mapping[str, Any], student: Mapping[str, Any]
) -> list[dict[str, Any]]:
    starts = reference["barStartsSeconds"]
    duration = float(reference["durationSeconds"])
    expected = [item for item in reference["segments"] if item["label"] != "N"]
    rows: list[dict[str, Any]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else duration
        truth = normalize_chord(str(expected[index]["label"])).product_symbol
        v2_label = _dominant_label(v2["segments"], start, end)
        student_label = _dominant_label(student["segments"], start, end)
        truth_key = _major_minor_key(truth)
        rows.append(
            {
                "bar": index + 1,
                "start": start,
                "end": end,
                "expected": truth,
                "v2": v2_label,
                "student": student_label,
                "v2Correct": _major_minor_key(v2_label) == truth_key,
                "studentCorrect": _major_minor_key(student_label) == truth_key,
            }
        )
    return rows


def build(output_root: Path) -> dict[str, Any]:
    track = _track()
    audio = REPO_ROOT / str(track["audioPath"])
    reference = _reference(track)
    output_root.mkdir(parents=True, exist_ok=True)
    v2_path = output_root / "v2.json"
    v2 = _v2(track, audio, v2_path)
    student = StudentRecognizer(MODEL).predict(audio, prediction_id=TRACK_ID)
    v2_metrics = score_segments(reference["segments"], v2["segments"])
    student_metrics = score_segments(reference["segments"], student["segments"])
    rows = _bar_rows(reference, v2, student)
    public_reports = {name: _read_json(path) for name, path in PUBLIC_REPORTS.items()}
    proof = {
        "schemaVersion": "chord_reader_visual_proof_v1",
        "track": {
            "id": TRACK_ID,
            "title": track["title"],
            "performer": track["performer"],
            "audioUrl": f"/{track['audioPath']}",
            "rightsUrl": track["rightsUrl"],
            "license": track["license"],
            "licenseUrl": track["licenseUrl"],
            "recordingCredit": track["recordingCredit"],
            "modifications": track["modifications"],
            "key": track["key"],
            "meter": track["meter"],
            "tempo": track["tempo"],
            "durationSeconds": reference["durationSeconds"],
        },
        "reference": {
            "source": reference["source"],
            "metricsLabel": "hand-authored expected chord timeline",
        },
        "engines": {
            "v2": {"label": "Current Play Along v2", "metrics": v2_metrics, "segments": v2["segments"]},
            "student": {
                "label": "Revised chord-student-v1",
                "metrics": student_metrics,
                "segments": student["segments"],
            },
        },
        "bars": rows,
        "summary": {
            "v2CorrectBars": sum(bool(row["v2Correct"]) for row in rows),
            "studentCorrectBars": sum(bool(row["studentCorrect"]) for row in rows),
            "barCount": len(rows),
            "majorMinorWcsrGain": student_metrics["majorMinorWeightedRecall"]
            - v2_metrics["majorMinorWeightedRecall"],
            "rootWcsrGain": student_metrics["rootWeightedRecall"] - v2_metrics["rootWeightedRecall"],
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
            "modelSha256": __import__("hashlib").sha256(MODEL.read_bytes()).hexdigest(),
            "audioSha256": __import__("hashlib").sha256(audio.read_bytes()).hexdigest(),
        },
    }
    _write_json(output_root / "reference.json", reference)
    _write_json(output_root / "student.json", student)
    _write_json(output_root / "proof.json", proof)
    return proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    proof = build(args.output_root)
    print(json.dumps(proof["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
