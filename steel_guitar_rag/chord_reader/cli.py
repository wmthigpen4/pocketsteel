"""Command-line entry point for Chord Reader ML data and benchmark contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from .artifact_integrity import seal_factorized_artifact_manifest
from .bar_promotion import calibrate_bar_product_operating_point
from .benchmark import (
    merge_benchmark_reports,
    run_benchmark,
    run_factorized_cache_benchmark,
    run_hybrid_benchmark,
    run_prediction_benchmark,
)
from .btc import predict_btc
from .chart_reference import build_chart_reference
from .datasets import (
    prepare_aam,
    prepare_babyslakh,
    prepare_guitarset,
    prepare_idmt_guitar,
    prepare_nrgcp,
    prepare_winterreise,
)
from .dasheng_cache import cache_dasheng_features
from .factorized import (
    FactorizedRecognizer,
    cache_factorized_labels,
    export_factorized_onnx,
    train_factorized_model,
)
from .labels import normalize_chord, transpose_chord
from .manifests import (
    WeakLabelDiagnostics,
    admit_weak_label,
    assign_group_splits,
    validate_catalog,
    validate_track_manifest,
)
from .metrics import score_segments, vocabulary_for_prediction
from .promotion import calibrate_product_operating_point, evaluate_promotion
from .review import build_travis_packet, score_travis_review
from .split_protocol import (
    DEFAULT_SEED as SPLIT_PROTOCOL_DEFAULT_SEED,
    build_leak_resistant_split_manifest,
    validate_split_protocol_manifest,
)
from .student import (
    STUDENT_ARCHITECTURES,
    STUDENT_FEATURE_KINDS,
    STUDENT_OBJECTIVES,
    StudentRecognizer,
    cache_student_features,
    composition_balance_feature_cache,
    export_student_onnx,
    merge_feature_caches,
    train_student,
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(value: Any, path: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _write_json_atomic(value: Any, path: Path) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f"Refusing to replace symlinked manifest output {path}.")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


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

    predict_factorized = commands.add_parser(
        "predict-factorized", help="Run an exported rich factorized ONNX model"
    )
    predict_factorized.add_argument("audio", type=Path)
    predict_factorized.add_argument("--model", type=Path, required=True)
    predict_factorized.add_argument("--output", type=Path)
    predict_factorized.add_argument("--id")
    predict_factorized.add_argument("--dasheng-snapshot-root", type=Path)
    predict_factorized.add_argument("--joint-product-blend", type=float, default=0.0)

    chart = commands.add_parser("build-chart-reference", help="Map a reviewed chart onto a frozen timing grid")
    chart.add_argument("chart", type=Path)
    chart.add_argument("timing", type=Path)
    chart.add_argument("--reader", type=Path, action="append", default=[])
    chart.add_argument("--output", type=Path, required=True)
    chart.add_argument("--report", type=Path, required=True)

    for name, help_text in (
        ("prepare-guitarset", "Normalize GuitarSet JAMS and audio into a split manifest"),
        ("prepare-aam", "Normalize AAM beat annotations and mixes into a split manifest"),
        ("prepare-winterreise", "Normalize Winterreise audio-aligned chord tables"),
        ("prepare-idmt-guitar", "Normalize IDMT dataset-4 guitar chord annotations"),
        ("prepare-nrgcp", "Render and normalize NRG-CP progression MIDI"),
        ("prepare-babyslakh", "Normalize BabySlakh mixes and aligned MIDI scores for evaluation"),
    ):
        prepare = commands.add_parser(name, help=help_text)
        prepare.add_argument("--annotations-root", type=Path, required=True)
        prepare.add_argument("--audio-root", type=Path, required=True)
        prepare.add_argument("--output-root", type=Path, required=True)
        prepare.add_argument("--manifest", type=Path, required=True)
        prepare.add_argument("--seed", default="chord-reader-v3-split-1")
        prepare.add_argument("--max-tracks", type=int)
        if name == "prepare-nrgcp":
            prepare.add_argument("--exclude-manifest", type=Path)
            prepare.add_argument("--evaluation-only", action="store_true")

    benchmark_run = commands.add_parser("benchmark", help="Run and freeze one engine on a manifest split")
    benchmark_run.add_argument("manifest", type=Path)
    benchmark_run.add_argument(
        "--engine", choices=("v2", "btc", "student", "factorized"), required=True
    )
    benchmark_run.add_argument("--split", default="test")
    benchmark_run.add_argument("--output-root", type=Path, required=True)
    benchmark_run.add_argument("--report", type=Path, required=True)
    benchmark_run.add_argument("--limit", type=int)
    benchmark_run.add_argument("--device", default="cpu")
    benchmark_run.add_argument("--local-files-only", action="store_true")
    benchmark_run.add_argument("--model", type=Path)
    benchmark_run.add_argument("--ensemble-model", type=Path, action="append", default=[])
    benchmark_run.add_argument("--boundary-model", type=Path)
    benchmark_run.add_argument("--secondary-boundary-model", type=Path)
    benchmark_run.add_argument("--secondary-boundary-weight", type=float, default=0.5)
    benchmark_run.add_argument("--domain-gate", type=Path)
    benchmark_run.add_argument("--ensemble-weight", type=float, action="append", default=[])
    benchmark_run.add_argument("--root-guide-only", action="store_true")
    benchmark_run.add_argument("--quality-model", type=Path, action="append")
    benchmark_run.add_argument("--quality-mode-threshold", type=float, default=0.6)
    benchmark_run.add_argument("--quality-extension-threshold", type=float, default=0.7)
    benchmark_run.add_argument("--factorized-decoder", action="store_true")
    benchmark_run.add_argument("--product-boundary-scale", type=float, default=1.3)
    benchmark_run.add_argument("--product-boundary-bias", type=float, default=-2.0)
    benchmark_run.add_argument("--dasheng-snapshot-root", type=Path)
    benchmark_run.add_argument("--joint-product-blend", type=float, default=0.0)

    rescore = commands.add_parser("benchmark-predictions", help="Rescore an existing frozen prediction directory")
    rescore.add_argument("manifest", type=Path)
    rescore.add_argument("--predictions", type=Path, required=True)
    rescore.add_argument("--engine", required=True)
    rescore.add_argument("--split", default="test")
    rescore.add_argument("--report", type=Path, required=True)

    factorized_cache_benchmark = commands.add_parser(
        "benchmark-factorized-cache",
        help="Decode and score an existing frozen factorized feature cache",
    )
    factorized_cache_benchmark.add_argument("cache_manifest", type=Path)
    factorized_cache_benchmark.add_argument(
        "--track-manifest", type=Path, action="append", required=True
    )
    factorized_cache_benchmark.add_argument("--model", type=Path, required=True)
    factorized_cache_benchmark.add_argument(
        "--ensemble-model",
        type=Path,
        action="append",
        default=[],
        help="Add a compatible same-feature factorized model and average logits before decoding",
    )
    factorized_cache_benchmark.add_argument(
        "--ensemble-weight",
        type=float,
        action="append",
        default=[],
        help="Normalized member weight in --model then --ensemble-model order",
    )
    factorized_cache_benchmark.add_argument("--split", default="development")
    factorized_cache_benchmark.add_argument("--limit", type=int)
    factorized_cache_benchmark.add_argument("--output-root", type=Path, required=True)
    factorized_cache_benchmark.add_argument("--report", type=Path, required=True)
    factorized_cache_benchmark.add_argument(
        "--beat-grid-source",
        choices=("none", "manifest-tempo-oracle"),
        default="none",
    )
    factorized_cache_benchmark.add_argument(
        "--joint-product-blend",
        type=float,
        default=0.0,
        help="Blend optional joint-head product evidence only after freezing the root path",
    )
    factorized_cache_benchmark.add_argument(
        "--allow-mixed-joint-members",
        action="store_true",
        help=(
            "Development-only opt-in to combine legacy 90-output and joint "
            "139-output ensemble members with head-aware weighting"
        ),
    )
    factorized_cache_benchmark.add_argument(
        "--emit-uncertainty",
        action="store_true",
        help=(
            "Emit reference-free development-only uncertainty telemetry with each prediction"
        ),
    )
    factorized_cache_benchmark.add_argument(
        "--audio-lineage-manifest",
        type=Path,
        help=(
            "Required with --emit-uncertainty; fully reverify exact development "
            "audio bytes against the frozen feature cache"
        ),
    )

    merge_reports = commands.add_parser(
        "merge-benchmark-reports",
        help="Recompute a pooled report from compatible per-corpus reports",
    )
    merge_reports.add_argument("report_input", type=Path, nargs="+")
    merge_reports.add_argument("--output", type=Path, required=True)

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
    feature_cache.add_argument(
        "--feature-kind", choices=tuple(STUDENT_FEATURE_KINDS), default="worker_chroma_v1"
    )

    dasheng_cache = commands.add_parser(
        "cache-dasheng-features",
        help="Cache sealed Dasheng embeddings without opening held-out splits by default",
    )
    dasheng_cache.add_argument("--track-manifest", type=Path, action="append", required=True)
    dasheng_cache.add_argument("--output-root", type=Path, required=True)
    dasheng_cache.add_argument("--cache-manifest", type=Path, required=True)
    dasheng_cache.add_argument("--snapshot-root", type=Path, required=True)
    dasheng_cache.add_argument(
        "--split",
        action="append",
        choices=("train", "development", "test", "steel_test"),
    )
    dasheng_cache.add_argument("--allow-held-out", action="store_true")
    dasheng_cache.add_argument("--overwrite", action="store_true")

    merge_cache = commands.add_parser("merge-feature-caches", help="Combine compatible frozen feature caches")
    merge_cache.add_argument("cache_manifest", type=Path, nargs="+")
    merge_cache.add_argument("--output", type=Path, required=True)

    balance_cache = commands.add_parser(
        "balance-feature-cache", help="Weight cached renditions so each composition has equal total weight"
    )
    balance_cache.add_argument("cache_manifest", type=Path)
    balance_cache.add_argument("--track-manifest", type=Path, action="append", required=True)
    balance_cache.add_argument("--output", type=Path, required=True)

    factorized_cache = commands.add_parser(
        "cache-factorized-labels",
        help="Attach rich label sidecars to a frozen feature cache",
    )
    factorized_cache.add_argument("feature_manifest", type=Path)
    factorized_cache.add_argument("--track-manifest", type=Path, action="append", required=True)
    factorized_cache.add_argument("--output-root", type=Path, required=True)
    factorized_cache.add_argument("--cache-manifest", type=Path, required=True)

    seal_factorized = commands.add_parser(
        "seal-factorized-artifacts",
        help="Hash and validate every selected factorized feature/label NPZ",
    )
    seal_factorized.add_argument("input", type=Path)
    seal_factorized.add_argument("output", type=Path)

    split_protocol = commands.add_parser(
        "freeze-factorized-split-protocol",
        help="Repartition original training compositions into fit, tuning, and calibration",
    )
    split_protocol.add_argument("source_manifest", type=Path)
    split_protocol.add_argument("--output", type=Path, required=True)
    split_protocol.add_argument("--seed", default=SPLIT_PROTOCOL_DEFAULT_SEED)
    split_protocol.add_argument(
        "--track-manifest",
        type=Path,
        action="append",
        default=[],
        help="Freeze explicit native bar timing and calibration eligibility from this manifest",
    )
    split_protocol.add_argument(
        "--exclude-source-split",
        action="append",
        choices=("development", "test", "steel_test"),
        default=[],
    )

    validate_protocol = commands.add_parser(
        "validate-factorized-split-protocol",
        help="Verify all group, calibration, and tamper-evident split invariants",
    )
    validate_protocol.add_argument("manifest", type=Path)
    validate_protocol.add_argument("--source-manifest", type=Path)
    validate_protocol.add_argument(
        "--track-manifest",
        type=Path,
        action="append",
        default=[],
        help="Revalidate the frozen native-timing manifest hashes and bar-eligible set",
    )

    train = commands.add_parser("train-student", help="Train the browser-sized supervised temporal model")
    train.add_argument("cache_manifest", type=Path)
    train.add_argument("--output-root", type=Path, required=True)
    train.add_argument("--epochs", type=int, default=20)
    train.add_argument("--batch-size", type=int, default=16)
    train.add_argument("--learning-rate", type=float, default=3e-4)
    train.add_argument("--device", default="cpu")
    train.add_argument("--seed", type=int, default=20260820)
    train.add_argument("--architecture", choices=STUDENT_ARCHITECTURES, default="tcn")
    train.add_argument("--objective", choices=STUDENT_OBJECTIVES, default="standard")

    factorized_train = commands.add_parser(
        "train-factorized", help="Train the expanded factorized chord model"
    )
    factorized_train.add_argument("cache_manifest", type=Path)
    factorized_train.add_argument("--output-root", type=Path, required=True)
    factorized_train.add_argument("--epochs", type=int, default=20)
    factorized_train.add_argument("--batch-size", type=int, default=12)
    factorized_train.add_argument("--learning-rate", type=float, default=3e-4)
    factorized_train.add_argument("--device", default="cpu")
    factorized_train.add_argument("--seed", type=int, default=20260820)
    factorized_train.add_argument("--architecture", choices=("tcn", "transformer"), default="transformer")
    factorized_train.add_argument("--augmentation", choices=("none", "pitch-roll"), default="none")
    factorized_train.add_argument(
        "--dataset-balance",
        action="store_true",
        help="Equalize train dataset frame mass and select epochs by development-dataset macro score",
    )
    factorized_train.add_argument(
        "--joint-root-product",
        action="store_true",
        help="Append and train the optional 49-state root/product auxiliary head",
    )
    factorized_train.add_argument(
        "--joint-root-product-loss-weight",
        type=float,
        default=0.6,
    )
    factorized_train.add_argument(
        "--joint-root-product-selection-blend",
        type=float,
        default=0.5,
        help=(
            "Bind joint-model checkpoint selection to this development-only "
            "direct/joint pitched-product blend"
        ),
    )
    factorized_train.add_argument(
        "--product-class-weighting",
        action="store_true",
        help="Apply train-only inverse-sqrt product weights to direct and optional joint CE",
    )

    export = commands.add_parser("export-student", help="Export and verify a trained student as ONNX")
    export.add_argument("model_root", type=Path)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--report", type=Path)
    export.add_argument("--boundary-scale", type=float, default=0.6)
    export.add_argument("--boundary-bias", type=float, default=0.0)

    factorized_export = commands.add_parser(
        "export-factorized", help="Export and verify a factorized model as ONNX"
    )
    factorized_export.add_argument("model_root", type=Path)
    factorized_export.add_argument("--output", type=Path, required=True)
    factorized_export.add_argument("--report", type=Path)

    promote = commands.add_parser("check-promotion", help="Apply frozen public, steel, runtime, and Travis gates")
    promote.add_argument("baseline", type=Path)
    promote.add_argument("challenger", type=Path)
    promote.add_argument("--require-steel", action="store_true")
    promote.add_argument("--travis-review", type=Path)
    promote.add_argument("--product-operating-point", type=Path)
    promote.add_argument("--bar-product-operating-point", type=Path)
    promote.add_argument("--output", type=Path)

    calibrate_product = commands.add_parser(
        "calibrate-product-gate",
        help="Freeze the highest-coverage development point at 98%% product precision",
    )
    calibrate_product.add_argument("development_report", type=Path)
    calibrate_product.add_argument("--target-precision", type=float, default=0.98)
    calibrate_product.add_argument("--output", type=Path, required=True)

    calibrate_bar_product = commands.add_parser(
        "calibrate-bar-product-gate",
        help="Freeze the highest-coverage calibration-only point at 98%% literal-bar precision",
    )
    calibrate_bar_product.add_argument("calibration_report", type=Path)
    calibrate_bar_product.add_argument("--target-precision", type=float, default=0.98)
    calibrate_bar_product.add_argument("--minimum-accepted-bars", type=int, default=30)
    calibrate_bar_product.add_argument("--output", type=Path, required=True)

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
            vocabulary_values=vocabulary_for_prediction(prediction),
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
    elif args.command == "predict-factorized":
        result = FactorizedRecognizer(
            args.model,
            dasheng_snapshot_root=args.dasheng_snapshot_root,
            **(
                {"joint_product_blend": args.joint_product_blend}
                if args.joint_product_blend != 0
                else {}
            ),
        ).predict(args.audio, prediction_id=args.id)
        _write_json(result, args.output)
    elif args.command == "build-chart-reference":
        reference, report = build_chart_reference(
            _read_json(args.chart),
            _read_json(args.timing),
            independent_readers=[_read_json(path) for path in args.reader],
        )
        _write_json(reference, args.output)
        _write_json(report, args.report)
    elif args.command in {
        "prepare-guitarset",
        "prepare-aam",
        "prepare-winterreise",
        "prepare-idmt-guitar",
        "prepare-nrgcp",
        "prepare-babyslakh",
    }:
        prepare = {
            "prepare-guitarset": prepare_guitarset,
            "prepare-aam": prepare_aam,
            "prepare-winterreise": prepare_winterreise,
            "prepare-idmt-guitar": prepare_idmt_guitar,
            "prepare-nrgcp": prepare_nrgcp,
            "prepare-babyslakh": prepare_babyslakh,
        }[args.command]
        keywords = {"seed": args.seed, "max_tracks": args.max_tracks}
        if args.command == "prepare-nrgcp":
            keywords["exclude_manifest"] = args.exclude_manifest
            keywords["evaluation_only"] = args.evaluation_only
        result = prepare(args.annotations_root, args.audio_root, args.output_root, **keywords)
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
            ensemble_models=args.ensemble_model,
            boundary_model=args.boundary_model,
            secondary_boundary_model=args.secondary_boundary_model,
            secondary_boundary_weight=args.secondary_boundary_weight,
            domain_gate=args.domain_gate,
            ensemble_weights=args.ensemble_weight,
            root_guide_only=args.root_guide_only,
            quality_models=args.quality_model,
            quality_mode_threshold=args.quality_mode_threshold,
            quality_extension_threshold=args.quality_extension_threshold,
            factorized_decoder=args.factorized_decoder,
            product_boundary_scale=args.product_boundary_scale,
            product_boundary_bias=args.product_boundary_bias,
            dasheng_snapshot_root=args.dasheng_snapshot_root,
            joint_product_blend=args.joint_product_blend,
        )
        _write_json(result, args.report)
    elif args.command == "benchmark-predictions":
        result = run_prediction_benchmark(
            _read_json(args.manifest),
            prediction_root=args.predictions,
            engine=args.engine,
            split=args.split,
        )
        _write_json(result, args.report)
    elif args.command == "benchmark-factorized-cache":
        if args.emit_uncertainty and args.split not in {"dev", "development"}:
            raise ValueError(
                "Uncertainty emission is development-only; split must be dev or development."
            )
        if args.emit_uncertainty and args.beat_grid_source != "none":
            raise ValueError("Uncertainty emission requires beat_grid_source='none'.")
        if args.emit_uncertainty and args.audio_lineage_manifest is None:
            raise ValueError("--emit-uncertainty requires --audio-lineage-manifest.")
        if not args.emit_uncertainty and args.audio_lineage_manifest is not None:
            raise ValueError("--audio-lineage-manifest requires --emit-uncertainty.")
        cache_manifest = _read_json(args.cache_manifest)
        if "splitProtocol" in cache_manifest:
            validate_split_protocol_manifest(cache_manifest)
        result = run_factorized_cache_benchmark(
            cache_manifest,
            [_read_json(path) for path in args.track_manifest],
            model=args.model,
            ensemble_models=args.ensemble_model,
            ensemble_weights=args.ensemble_weight,
            output_root=args.output_root,
            split=args.split,
            limit=args.limit,
            beat_grid_source=args.beat_grid_source,
            joint_product_blend=args.joint_product_blend,
            allow_mixed_joint_members=args.allow_mixed_joint_members,
            **({"emit_uncertainty": True} if args.emit_uncertainty else {}),
            **(
                {"audio_lineage": _read_json(args.audio_lineage_manifest)}
                if args.audio_lineage_manifest is not None
                else {}
            ),
        )
        _write_json(result, args.report)
    elif args.command == "merge-benchmark-reports":
        result = merge_benchmark_reports(
            [_read_json(path) for path in args.report_input]
        )
        _write_json(result, args.output)
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
            feature_kind=args.feature_kind,
        )
        _write_json(result, args.cache_manifest)
    elif args.command == "cache-dasheng-features":
        result = cache_dasheng_features(
            args.track_manifest,
            args.output_root,
            splits=set(args.split) if args.split else None,
            allow_held_out=args.allow_held_out,
            overwrite=args.overwrite,
            snapshot_root=args.snapshot_root,
            manifest_path=args.cache_manifest,
        )
        _write_json(
            {
                "cacheManifest": str(args.cache_manifest.resolve()),
                "tracks": len(result["tracks"]),
                "selectedSplits": result["selectedSplits"],
                "featureSpecSha256": result["featureSpecSha256"],
            },
            None,
        )
    elif args.command == "train-student":
        result = train_student(
            _read_json(args.cache_manifest),
            args.output_root,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            device=args.device,
            seed=args.seed,
            architecture=args.architecture,
            objective=args.objective,
        )
        _write_json(result, None)
    elif args.command == "merge-feature-caches":
        result = merge_feature_caches(_read_json(path) for path in args.cache_manifest)
        _write_json(result, args.output)
    elif args.command == "balance-feature-cache":
        result = composition_balance_feature_cache(
            _read_json(args.cache_manifest),
            [_read_json(path) for path in args.track_manifest],
        )
        _write_json(result, args.output)
    elif args.command == "cache-factorized-labels":
        result = cache_factorized_labels(
            _read_json(args.feature_manifest),
            [_read_json(path) for path in args.track_manifest],
            args.output_root,
        )
        _write_json(result, args.cache_manifest)
    elif args.command == "seal-factorized-artifacts":
        result = seal_factorized_artifact_manifest(_read_json(args.input))
        _write_json_atomic(result, args.output)
        _write_json(
            {
                "artifactSetSha256": result["artifactIntegrity"][
                    "artifactSetSha256"
                ],
                "output": str(args.output.resolve()),
                "tracks": result["artifactIntegrity"]["trackCount"],
            },
            None,
        )
    elif args.command == "freeze-factorized-split-protocol":
        result = build_leak_resistant_split_manifest(
            _read_json(args.source_manifest),
            seed=args.seed,
            excluded_source_splits=args.exclude_source_split,
            timing_manifests=(
                [_read_json(path) for path in args.track_manifest]
                if args.track_manifest
                else None
            ),
        )
        _write_json(result, args.output)
    elif args.command == "validate-factorized-split-protocol":
        result = validate_split_protocol_manifest(
            _read_json(args.manifest),
            source_manifest=(
                _read_json(args.source_manifest) if args.source_manifest else None
            ),
            timing_manifests=(
                [_read_json(path) for path in args.track_manifest]
                if args.track_manifest
                else None
            ),
        )
        _write_json(
            {
                "valid": True,
                "outputManifestSha256": result["splitProtocol"][
                    "outputManifestSha256"
                ],
                "tracks": len(result["tracks"]),
            },
            None,
        )
    elif args.command == "train-factorized":
        result = train_factorized_model(
            _read_json(args.cache_manifest),
            args.output_root,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            device=args.device,
            seed=args.seed,
            architecture=args.architecture,
            augmentation=args.augmentation,
            dataset_balance=args.dataset_balance,
            joint_root_product=args.joint_root_product,
            joint_root_product_loss_weight=args.joint_root_product_loss_weight,
            product_class_weighting=args.product_class_weighting,
            joint_root_product_selection_blend=(
                args.joint_root_product_selection_blend
            ),
        )
        _write_json(result, None)
    elif args.command == "export-student":
        result = export_student_onnx(
            args.model_root,
            args.output,
            boundary_scale=args.boundary_scale,
            boundary_bias=args.boundary_bias,
        )
        _write_json(result, args.report)
    elif args.command == "export-factorized":
        result = export_factorized_onnx(args.model_root, args.output)
        _write_json(result, args.report)
    elif args.command == "check-promotion":
        result = evaluate_promotion(
            _read_json(args.baseline),
            _read_json(args.challenger),
            require_steel=args.require_steel,
            travis_review=_read_json(args.travis_review) if args.travis_review else None,
            operating_point=(
                _read_json(args.product_operating_point)
                if args.product_operating_point
                else None
            ),
            bar_operating_point=(
                _read_json(args.bar_product_operating_point)
                if args.bar_product_operating_point
                else None
            ),
        )
        _write_json(result, args.output)
        return 0 if result["passed"] else 2
    elif args.command == "calibrate-product-gate":
        result = calibrate_product_operating_point(
            _read_json(args.development_report),
            target_precision=args.target_precision,
        )
        _write_json(result, args.output)
    elif args.command == "calibrate-bar-product-gate":
        result = calibrate_bar_product_operating_point(
            _read_json(args.calibration_report),
            target_precision=args.target_precision,
            minimum_accepted_bars=args.minimum_accepted_bars,
        )
        _write_json(result, args.output)
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
