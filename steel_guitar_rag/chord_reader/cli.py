"""Command-line entry point for Chord Reader ML data and benchmark contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from .btc import predict_btc
from .benchmark import run_benchmark, run_hybrid_benchmark
from .chart_reference import build_chart_reference
from .datasets import prepare_aam, prepare_guitarset
from .labels import normalize_chord, transpose_chord
from .manifests import (
    WeakLabelDiagnostics,
    admit_weak_label,
    assign_group_splits,
    validate_catalog,
    validate_track_manifest,
)
from .metrics import score_segments
from .promotion import evaluate_promotion
from .review import build_travis_packet, score_travis_review
from .student import StudentRecognizer, cache_student_features, export_student_onnx, train_student


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(value: Any, path: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chord Reader ML v3 development CLI")
    commands = parser.add_subparsers(dest="command", required=True)

    catalog = commands.add_parser("validate-catalog", help="Validate a tracked dataset source catalog")
    catalog.add_argument("catalog", type=Path)

    freeze = commands.add_parser("freeze-splits", help="Assign deterministic group-aware splits")
    freeze.add_argument("input", type=Path, help="JSON object containing a tracks list")
    freeze.add_argument("output", type=Path)
    freeze.add_argument("--seed", default="chord-reader-v3-split-1")

    manifest = commands.add_parser("validate-manifest", help="Validate split and training-weight invariants")
    manifest.add_argument("manifest", type=Path)
    manifest.add_argument("--catalog", type=Path)

    label = commands.add_parser("normalize-label", help="Normalize and optionally transpose one chord")
    label.add_argument("symbol")
    label.add_argument("--transpose", type=int, default=0)

    weak = commands.add_parser("check-weak-label", help="Apply the SGF weak-label admission gate")
    weak.add_argument("diagnostics", type=Path)

    benchmark = commands.add_parser("score", help="Score predicted time-aligned segments")
    benchmark.add_argument("reference", type=Path)
    benchmark.add_argument("prediction", type=Path)
    benchmark.add_argument("--output", type=Path)
    benchmark.add_argument("--boundary-tolerance-seconds", type=float, default=0.25)

    predict_v2 = commands.add_parser("predict-v2", help="Run the exact current Play Along v2 reader")
    predict_v2.add_argument("audio", type=Path)
    predict_v2.add_argument("--output", type=Path)
    predict_v2.add_argument("--id")
    predict_v2.add_argument("--key")
    predict_v2.add_argument("--mode", choices=("major", "minor"))
    predict_v2.add_argument("--meter", choices=("2/4", "3/4", "4/4", "6/8"))
    predict_v2.add_argument("--tempo", type=float)

    predict_btc_parser = commands.add_parser("predict-btc", help="Run the pinned pretrained BTC challenger")
    predict_btc_parser.add_argument("audio", type=Path)
    predict_btc_parser.add_argument("--output", type=Path)
    predict_btc_parser.add_argument("--id")
    predict_btc_parser.add_argument("--device", default="cpu")
    predict_btc_parser.add_argument("--cache-dir", type=Path)
    predict_btc_parser.add_argument("--local-files-only", action="store_true")

    predict_student = commands.add_parser("predict-student", help="Run an exported student ONNX model")
    predict_student.add_argument("audio", type=Path)
    predict_student.add_argument("--model", type=Path, required=True)
    predict_student.add_argument("--output", type=Path)
    predict_student.add_argument("--id")

    chart = commands.add_parser("build-chart-reference", help="Map a reviewed chart onto a frozen timing grid")
    chart.add_argument("chart", type=Path)
    chart.add_argument("timing", type=Path)
    chart.add_argument("--reader", type=Path, action="append", default=[])
    chart.add_argument("--output", type=Path, required=True)
    chart.add_argument("--report", type=Path, required=True)

    for name, help_text in (
        ("prepare-guitarset", "Normalize GuitarSet JAMS and audio into a split manifest"),
        ("prepare-aam", "Normalize AAM beat annotations and mixes into a split manifest"),
    ):
        prepare = commands.add_parser(name, help=help_text)
        prepare.add_argument("--annotations-root", type=Path, required=True)
        prepare.add_argument("--audio-root", type=Path, required=True)
        prepare.add_argument("--output-root", type=Path, required=True)
        prepare.add_argument("--manifest", type=Path, required=True)
        prepare.add_argument("--seed", default="chord-reader-v3-split-1")
        prepare.add_argument("--max-tracks", type=int)

    benchmark_run = commands.add_parser("benchmark", help="Run and freeze one engine on a manifest split")
    benchmark_run.add_argument("manifest", type=Path)
    benchmark_run.add_argument("--engine", choices=("v2", "btc", "student"), required=True)
    benchmark_run.add_argument("--split", default="test")
    benchmark_run.add_argument("--output-root", type=Path, required=True)
    benchmark_run.add_argument("--report", type=Path, required=True)
    benchmark_run.add_argument("--limit", type=int)
    benchmark_run.add_argument("--device", default="cpu")
    benchmark_run.add_argument("--local-files-only", action="store_true")
    benchmark_run.add_argument("--model", type=Path)

    hybrid_benchmark = commands.add_parser(
        "benchmark-hybrid", help="Freeze the conservative hybrid from existing v2 and student predictions"
    )
    hybrid_benchmark.add_argument("manifest", type=Path)
    hybrid_benchmark.add_argument("--v2-predictions", type=Path, required=True)
    hybrid_benchmark.add_argument("--student-predictions", type=Path, required=True)
    hybrid_benchmark.add_argument("--split", default="test")
    hybrid_benchmark.add_argument("--output-root", type=Path, required=True)
    hybrid_benchmark.add_argument("--report", type=Path, required=True)

    feature_cache = commands.add_parser("cache-student-features", help="Cache browser-compatible chroma and labels")
    feature_cache.add_argument("manifest", type=Path)
    feature_cache.add_argument("--output-root", type=Path, required=True)
    feature_cache.add_argument("--cache-manifest", type=Path, required=True)
    feature_cache.add_argument("--split", action="append", choices=("train", "development", "test", "steel_test"))
    feature_cache.add_argument("--limit", type=int)

    train = commands.add_parser("train-student", help="Train the browser-sized supervised temporal model")
    train.add_argument("cache_manifest", type=Path)
    train.add_argument("--output-root", type=Path, required=True)
    train.add_argument("--epochs", type=int, default=20)
    train.add_argument("--batch-size", type=int, default=16)
    train.add_argument("--learning-rate", type=float, default=3e-4)
    train.add_argument("--device", default="cpu")
    train.add_argument("--seed", type=int, default=20260820)

    export = commands.add_parser("export-student", help="Export and verify a trained student as ONNX")
    export.add_argument("model_root", type=Path)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--report", type=Path)

    promote = commands.add_parser("check-promotion", help="Apply frozen public, steel, runtime, and Travis gates")
    promote.add_argument("baseline", type=Path)
    promote.add_argument("challenger", type=Path)
    promote.add_argument("--require-steel", action="store_true")
    promote.add_argument("--travis-review", type=Path)
    promote.add_argument("--output", type=Path)

    packet = commands.add_parser("make-travis-packet", help="Build a sealed blinded ten-song A/B packet")
    packet.add_argument("manifest", type=Path)
    packet.add_argument("baseline", type=Path)
    packet.add_argument("challenger", type=Path)
    packet.add_argument("--packet-root", type=Path, required=True)
    packet.add_argument("--key", type=Path, required=True)
    packet.add_argument("--seed", default="chord-reader-travis-v1")

    score_review = commands.add_parser("score-travis-review", help="Unblind a completed Travis review")
    score_review.add_argument("response", type=Path)
    score_review.add_argument("key", type=Path)
    score_review.add_argument("--output", type=Path)

    portable = commands.add_parser("freeze-report", help="Remove machine-local paths from a benchmark report")
    portable.add_argument("input", type=Path)
    portable.add_argument("output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-catalog":
        catalog = validate_catalog(_read_json(args.catalog))
        _write_json({"valid": True, "datasets": len(catalog["datasets"])}, None)
    elif args.command == "freeze-splits":
        value = _read_json(args.input)
        frozen = {
            "schemaVersion": "chord_track_manifest_v1",
            "splitSeed": args.seed,
            "tracks": assign_group_splits(value.get("tracks", []), seed=args.seed),
        }
        _write_json(frozen, args.output)
    elif args.command == "validate-manifest":
        dataset_ids = None
        if args.catalog:
            catalog = validate_catalog(_read_json(args.catalog))
            dataset_ids = {item["id"] for item in catalog["datasets"]}
        manifest = validate_track_manifest(_read_json(args.manifest), dataset_ids)
        _write_json({"valid": True, "tracks": len(manifest["tracks"])}, None)
    elif args.command == "normalize-label":
        normalized = transpose_chord(args.symbol, args.transpose) if args.transpose else normalize_chord(args.symbol)
        _write_json(normalized.to_dict(), None)
    elif args.command == "check-weak-label":
        value = _read_json(args.diagnostics)
        result = admit_weak_label(
            WeakLabelDiagnostics(
                complete_coverage=bool(value.get("completeCoverage")),
                monotonic_alignment=bool(value.get("monotonicAlignment")),
                boundary_within_half_beat_fraction=float(value.get("boundaryWithinHalfBeatFraction", 0)),
                dual_reader_duration_agreement=float(value.get("dualReaderDurationAgreement", 0)),
            )
        )
        _write_json(result, None)
    elif args.command == "score":
        reference = _read_json(args.reference)
        prediction = _read_json(args.prediction)
        result = score_segments(
            reference["segments"],
            prediction["segments"],
            boundary_tolerance_seconds=args.boundary_tolerance_seconds,
        )
        result["referenceId"] = reference.get("id")
        result["predictionId"] = prediction.get("id")
        _write_json(result, args.output)
    elif args.command == "predict-v2":
        repo_root = Path(__file__).resolve().parents[2]
        command = ["node", str(repo_root / "scripts/chord_reader_v2.js"), "--audio", str(args.audio)]
        for name in ("output", "id", "key", "mode", "meter", "tempo"):
            value = getattr(args, name)
            if value is not None:
                command.extend((f"--{name}", str(value)))
        result = subprocess.run(command, cwd=repo_root, check=False)
        if result.returncode:
            return result.returncode
    elif args.command == "predict-btc":
        result = predict_btc(
            args.audio,
            prediction_id=args.id,
            device=args.device,
            cache_dir=args.cache_dir,
            local_files_only=args.local_files_only,
        )
        _write_json(result, args.output)
    elif args.command == "predict-student":
        result = StudentRecognizer(args.model).predict(args.audio, prediction_id=args.id)
        _write_json(result, args.output)
    elif args.command == "build-chart-reference":
        reference, report = build_chart_reference(
            _read_json(args.chart),
            _read_json(args.timing),
            independent_readers=[_read_json(path) for path in args.reader],
        )
        _write_json(reference, args.output)
        _write_json(report, args.report)
    elif args.command in {"prepare-guitarset", "prepare-aam"}:
        prepare = prepare_guitarset if args.command == "prepare-guitarset" else prepare_aam
        result = prepare(
            args.annotations_root,
            args.audio_root,
            args.output_root,
            seed=args.seed,
            max_tracks=args.max_tracks,
        )
        _write_json(result, args.manifest)
    elif args.command == "benchmark":
        result = run_benchmark(
            _read_json(args.manifest),
            engine=args.engine,
            output_root=args.output_root,
            split=args.split,
            limit=args.limit,
            device=args.device,
            local_files_only=args.local_files_only,
            model=args.model,
        )
        _write_json(result, args.report)
    elif args.command == "benchmark-hybrid":
        result = run_hybrid_benchmark(
            _read_json(args.manifest),
            v2_prediction_root=args.v2_predictions,
            student_prediction_root=args.student_predictions,
            output_root=args.output_root,
            split=args.split,
        )
        _write_json(result, args.report)
    elif args.command == "cache-student-features":
        result = cache_student_features(
            _read_json(args.manifest),
            args.output_root,
            splits=set(args.split) if args.split else None,
            limit=args.limit,
        )
        _write_json(result, args.cache_manifest)
    elif args.command == "train-student":
        result = train_student(
            _read_json(args.cache_manifest),
            args.output_root,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            device=args.device,
            seed=args.seed,
        )
        _write_json(result, None)
    elif args.command == "export-student":
        result = export_student_onnx(args.model_root, args.output)
        _write_json(result, args.report)
    elif args.command == "check-promotion":
        result = evaluate_promotion(
            _read_json(args.baseline),
            _read_json(args.challenger),
            require_steel=args.require_steel,
            travis_review=_read_json(args.travis_review) if args.travis_review else None,
        )
        _write_json(result, args.output)
        return 0 if result["passed"] else 2
    elif args.command == "make-travis-packet":
        packet, _key = build_travis_packet(
            _read_json(args.manifest),
            args.baseline,
            args.challenger,
            args.packet_root,
            args.key,
            seed=args.seed,
        )
        _write_json({"packet": str(args.packet_root / "review.json"), "tracks": len(packet["items"])}, None)
    elif args.command == "score-travis-review":
        result = score_travis_review(_read_json(args.response), _read_json(args.key))
        _write_json(result, args.output)
    elif args.command == "freeze-report":
        result = _read_json(args.input)
        for track in result.get("tracks", []):
            local_path = track.pop("predictionPath", None)
            if local_path and not track.get("predictionFile"):
                track["predictionFile"] = f"predictions/{result.get('engine')}/{Path(local_path).name}"
        result["sourceReportSha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
        _write_json(result, args.output)
    return 0
