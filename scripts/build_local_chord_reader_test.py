#!/usr/bin/env python3
"""Build an ignored, localhost-only chord-reader bundle for user audio."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.student import (  # noqa: E402
    StudentHeterogeneousBoundaryGuidedEnsembleRecognizer,
)


OUTPUT_ROOT = REPO_ROOT / "ui/chord-reader-proof/local-tests"
CHORD_MODELS = (
    REPO_ROOT / "ui/models/chord-multiband-tcn-v2.onnx",
    REPO_ROOT / "ui/models/chord-multiband-transformer-v2.onnx",
    REPO_ROOT / "ui/models/chord-multiband-idmt-tcn-v3.onnx",
    REPO_ROOT / "ui/models/chord-harmonic-cqt-transformer-v4.onnx",
)
CHORD_WEIGHTS = (1.0, 1.0, 1.0, 0.3)
BOUNDARY_MODEL = REPO_ROOT / "ui/models/chord-boundary-transformer-v3.onnx"
SECONDARY_BOUNDARY_MODEL = REPO_ROOT / "ui/models/chord-boundary-nrgcp-transformer-v5.onnx"
QUALITY_MODELS = (
    REPO_ROOT / "ui/models/chord-quality-nrgcp-multiband-v5.onnx",
    REPO_ROOT / "ui/models/chord-quality-nrgcp-cqt-v5.onnx",
)
DOMAIN_GATE = REPO_ROOT / "ui/models/chord-domain-gate-v1.json"
MODEL_PATHS = (*CHORD_MODELS, BOUNDARY_MODEL, SECONDARY_BOUNDARY_MODEL, *QUALITY_MODELS, DOMAIN_GATE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identifier(path: Path, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") or "song"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _display_title(path: Path) -> str:
    return re.sub(r"^\d+\s*-\s*", "", path.stem).strip()


def _audio_url(destination: Path) -> str:
    try:
        relative = destination.resolve().relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError("Browser-ready local output must stay inside the repository.") from exc
    return f"/{relative.as_posix()}"


def _summary(prediction: Mapping[str, Any]) -> dict[str, Any]:
    segments = list(prediction["segments"])
    duration = float(prediction["durationSeconds"])
    confidence_mass = 0.0
    low_seconds = 0.0
    high_seconds = 0.0
    chord_seconds: dict[str, float] = {}
    for segment in segments:
        seconds = max(0.0, float(segment["end"]) - float(segment["start"]))
        confidence = float(segment["confidence"])
        confidence_mass += seconds * confidence
        if confidence < 0.5:
            low_seconds += seconds
        if confidence >= 0.8:
            high_seconds += seconds
        chord = str(segment.get("productLabel") or segment.get("label") or "N.C.")
        chord_seconds[chord] = chord_seconds.get(chord, 0.0) + seconds
    return {
        "segmentCount": len(segments),
        "meanConfidence": confidence_mass / max(duration, 1e-12),
        "lowConfidenceFraction": low_seconds / max(duration, 1e-12),
        "highConfidenceFraction": high_seconds / max(duration, 1e-12),
        "dominantChords": [
            {"symbol": chord, "seconds": seconds}
            for chord, seconds in sorted(chord_seconds.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
    }


def _recognizer() -> StudentHeterogeneousBoundaryGuidedEnsembleRecognizer:
    return StudentHeterogeneousBoundaryGuidedEnsembleRecognizer(
        CHORD_MODELS,
        CHORD_WEIGHTS,
        BOUNDARY_MODEL,
        secondary_boundary_model=SECONDARY_BOUNDARY_MODEL,
        secondary_boundary_weight=0.5,
        root_guide_only=True,
        quality_models=QUALITY_MODELS,
        quality_mode_threshold=0.55,
        quality_extension_threshold=0.65,
        factorized_decoder=True,
        product_boundary_scale=1.3,
        product_boundary_bias=-2.0,
        domain_gate=DOMAIN_GATE,
    )


def build(audio_paths: Sequence[Path], output_root: Path = OUTPUT_ROOT) -> dict[str, Any]:
    if not audio_paths:
        raise ValueError("At least one --audio path is required.")
    resolved = [path.expanduser().resolve(strict=True) for path in audio_paths]
    if any(not path.is_file() for path in resolved):
        raise ValueError("Every audio input must be a regular file.")
    output_root = output_root.resolve()
    audio_root = output_root / "audio"
    audio_root.mkdir(parents=True, exist_ok=True)
    recognizer = _recognizer()
    used: set[str] = set()
    tracks: list[dict[str, Any]] = []
    for source in resolved:
        identifier = _identifier(source, used)
        suffix = source.suffix.lower() or ".audio"
        destination = audio_root / f"{identifier}{suffix}"
        shutil.copyfile(source, destination)
        prediction = recognizer.predict(source, prediction_id=identifier)
        tracks.append(
            {
                "track": {
                    "id": identifier,
                    "title": _display_title(source),
                    "audioUrl": _audio_url(destination),
                    "audioSha256": _sha256(source),
                    "durationSeconds": prediction["durationSeconds"],
                    "recordingType": "user-supplied local recording",
                },
                "prediction": prediction,
                "summary": _summary(prediction),
            }
        )
    payload = {
        "schemaVersion": "chord_reader_local_song_test_v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "candidateLabel": "Experimental domain-gated root-quality-boundary ensemble",
        "readinessStatus": "NO-GO — listening test only; no operating threshold or accuracy claim",
        "defaultTrackId": tracks[0]["track"]["id"],
        "tracks": tracks,
        "modelSha256": {path.name: _sha256(path) for path in MODEL_PATHS},
        "disclosure": (
            "These files have no reference chart in this bundle. Confidence is not accuracy. "
            "Listen and compare against a user-confirmed chart before recording any accuracy result."
        ),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "proof.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    payload = build(args.audio, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "trackCount": len(payload["tracks"]),
                "tracks": [
                    {
                        "id": item["track"]["id"],
                        "durationSeconds": item["track"]["durationSeconds"],
                        "segmentCount": item["summary"]["segmentCount"],
                        "meanConfidence": item["summary"]["meanConfidence"],
                        "domainRoute": item["prediction"]["domainRoute"],
                    }
                    for item in payload["tracks"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
