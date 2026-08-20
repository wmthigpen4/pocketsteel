"""Create and score a sealed, blinded ten-song Travis comparison packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


REVIEW_TRACKS = 10


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prediction_path(report_path: Path, row: Mapping[str, Any]) -> Path:
    value = row.get("predictionPath") or row.get("predictionFile")
    if not value:
        raise ValueError(f"Benchmark row {row.get('id')!r} has no prediction path.")
    path = Path(str(value))
    return path if path.is_absolute() else report_path.parent / path


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def build_travis_packet(
    manifest: Mapping[str, Any],
    baseline_report_path: Path,
    challenger_report_path: Path,
    packet_root: Path,
    key_path: Path,
    *,
    seed: str = "chord-reader-travis-v1",
) -> tuple[dict[str, Any], dict[str, Any]]:
    if _is_within(key_path, packet_root):
        raise ValueError("The sealed answer key must be outside the review packet directory.")
    tracks = [track for track in manifest.get("tracks", []) if track.get("split") == "steel_test"]
    if len(tracks) != REVIEW_TRACKS:
        raise ValueError(f"Travis review requires exactly {REVIEW_TRACKS} steel_test tracks; found {len(tracks)}.")
    baseline = _read_json(baseline_report_path)
    challenger = _read_json(challenger_report_path)
    baseline_rows = {str(row["id"]): row for row in baseline.get("tracks", [])}
    challenger_rows = {str(row["id"]): row for row in challenger.get("tracks", [])}
    expected = {str(track["id"]) for track in tracks}
    if set(baseline_rows) != expected or set(challenger_rows) != expected:
        raise ValueError("Both benchmark reports must contain exactly the ten steel_test track ids.")

    packet_items: list[dict[str, Any]] = []
    key_items: list[dict[str, Any]] = []
    predictions_root = packet_root / "predictions"
    predictions_root.mkdir(parents=True, exist_ok=True)
    for number, track in enumerate(sorted(tracks, key=lambda item: str(item["id"])), start=1):
        track_id = str(track["id"])
        digest = hashlib.sha256(f"{seed}:{track_id}".encode()).digest()
        a_engine = "challenger" if digest[0] & 1 else "baseline"
        rows = {"baseline": baseline_rows[track_id], "challenger": challenger_rows[track_id]}
        reports = {"baseline": baseline_report_path, "challenger": challenger_report_path}
        assignment = {"A": a_engine, "B": "baseline" if a_engine == "challenger" else "challenger"}
        files: dict[str, str] = {}
        for label, engine_role in assignment.items():
            source = _prediction_path(reports[engine_role], rows[engine_role])
            value = _read_json(source)
            blinded = {
                "schemaVersion": value.get("schemaVersion", "chord_prediction_v1"),
                "id": track_id,
                "durationSeconds": value.get("durationSeconds"),
                "segments": value.get("segments", []),
            }
            destination = predictions_root / f"{number:02d}-{label}.json"
            _write_json(destination, blinded)
            files[label] = str(destination.relative_to(packet_root))
        packet_items.append(
            {
                "number": number,
                "trackId": track_id,
                "title": track.get("title") or track_id,
                "audioPath": track.get("audioPath"),
                "predictionA": files["A"],
                "predictionB": files["B"],
                "review": {"preferred": None, "aCorrections": None, "bCorrections": None, "notes": ""},
            }
        )
        key_items.append({"trackId": track_id, "A": assignment["A"], "B": assignment["B"]})
    packet = {
        "schemaVersion": "chord_travis_blind_packet_v1",
        "instructions": "For each song, choose A, B, or tie and count chord corrections needed in each output.",
        "items": packet_items,
    }
    key = {
        "schemaVersion": "chord_travis_answer_key_v1",
        "baselineEngine": baseline.get("engine"),
        "challengerEngine": challenger.get("engine"),
        "items": key_items,
    }
    _write_json(packet_root / "review.json", packet)
    _write_json(key_path, key)
    return packet, key


def score_travis_review(response: Mapping[str, Any], key: Mapping[str, Any]) -> dict[str, Any]:
    answers = {str(item["trackId"]): item for item in response.get("items", [])}
    key_items = {str(item["trackId"]): item for item in key.get("items", [])}
    if len(answers) != REVIEW_TRACKS or set(answers) != set(key_items):
        raise ValueError("Completed review and answer key must contain the same ten track ids.")
    comparisons: list[dict[str, Any]] = []
    for track_id in sorted(key_items):
        answer = answers[track_id].get("review", answers[track_id])
        preferred_label = str(answer.get("preferred", "")).upper()
        if preferred_label not in {"A", "B", "TIE"}:
            raise ValueError(f"Track {track_id} needs preferred A, B, or tie.")
        a_corrections = int(answer.get("aCorrections"))
        b_corrections = int(answer.get("bCorrections"))
        if min(a_corrections, b_corrections) < 0:
            raise ValueError("Correction counts cannot be negative.")
        assignment = key_items[track_id]
        preferred = "tie" if preferred_label == "TIE" else assignment[preferred_label]
        corrections = {assignment["A"]: a_corrections, assignment["B"]: b_corrections}
        comparisons.append(
            {
                "trackId": track_id,
                "preferred": preferred,
                "baselineCorrections": corrections["baseline"],
                "challengerCorrections": corrections["challenger"],
            }
        )
    return {"schemaVersion": "chord_travis_review_v1", "comparisons": comparisons}
