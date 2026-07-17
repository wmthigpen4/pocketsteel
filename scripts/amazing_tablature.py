#!/usr/bin/env python3
"""Operate the private Lane 20 Amazing Tablature training workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pocketsteel.amazing_tablature_training import (
    DEFAULT_PRIVATE_ROOT,
    AmazingTablatureTrainingStore,
    TrainingWorkflowError,
)


def _print(value: Any) -> None:
    if isinstance(value, Path):
        value = {"path": str(value)}
    print(json.dumps(value, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest, validate, train, evaluate, and promote private Amazing Tablature decisions.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_PRIVATE_ROOT, help="Ignored private Lane 20 root.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Register an immutable source batch.")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--source-copedent", required=True)
    ingest.add_argument("--copedent-confidence", choices=("confirmed", "inferred", "unknown"), default="confirmed")
    ingest.add_argument("--evidence-type", choices=("expert_score_tab", "player_feedback"), default="expert_score_tab")
    ingest.add_argument("--batch-id")

    partition = subparsers.add_parser(
        "partition",
        help="Create and seal a leakage-resistant discovery/validation/test split.",
    )
    partition.add_argument("batch_id")
    partition.add_argument("--document-break", action="append", default=[])
    partition.add_argument("--force-discovery", action="append", default=[])
    partition.add_argument("--discovery-target", type=int, default=194)
    partition.add_argument("--validation-target", type=int, default=28)
    partition.add_argument("--test-target", type=int, default=56)
    partition.add_argument("--guard-radius", type=int, default=1)
    partition.add_argument("--similarity-threshold", type=int, default=3)

    supersede = subparsers.add_parser(
        "supersede-batch",
        help="Preserve an old batch as historical and exclude it from future datasets.",
    )
    supersede.add_argument("batch_id")
    supersede.add_argument("--replacement-batch", required=True)
    supersede.add_argument("--approval-reference", required=True)

    verify = subparsers.add_parser("verify-intake", help="Re-hash a batch and verify the source files are unchanged.")
    verify.add_argument("batch_id")

    annotate = subparsers.add_parser("annotate", help="Import immutable private JSONL annotations for a batch.")
    annotate.add_argument("batch_id")
    annotate.add_argument("annotations", type=Path)

    validate = subparsers.add_parser("validate", help="Mechanically validate a batch and write its exception queue.")
    validate.add_argument("batch_id")

    review = subparsers.add_parser("review", help="Apply accept, exclude, or correction decisions and revalidate.")
    review.add_argument("batch_id")
    review.add_argument("resolutions", type=Path)

    train = subparsers.add_parser("train", help="Build a deterministic challenger from all accepted train records.")
    train.add_argument("--epochs", type=int, default=20)
    train.add_argument("--learning-rate", type=float, default=0.05)

    evaluate = subparsers.add_parser("evaluate", help="Compare a challenger against holdout decisions and the champion.")
    evaluate.add_argument("model_id")

    report = subparsers.add_parser("report", help="Write a private metrics-only challenger report.")
    report.add_argument("model_id")

    promote = subparsers.add_parser("promote", help="Promote an exact passing model after explicit creator approval.")
    promote.add_argument("model_id")
    promote.add_argument("--channel", choices=("beta", "stable"), required=True)
    promote.add_argument("--approval-reference", required=True)
    promote.add_argument("--lane15-handoff", type=Path)

    reject = subparsers.add_parser("reject", help="Retire a rejected inactive challenger.")
    reject.add_argument("model_id")
    reject.add_argument("--approval-reference", required=True)

    rollback = subparsers.add_parser("rollback", help="Restore an exact previously active model.")
    rollback.add_argument("model_id")
    rollback.add_argument("--channel", choices=("beta", "stable"), required=True)
    rollback.add_argument("--approval-reference", required=True)

    batch_status = subparsers.add_parser("batch-status", help="Show resumable state for one batch.")
    batch_status.add_argument("batch_id")
    subparsers.add_parser("status", help="Show all private batches, challengers, and active channels.")
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    store = AmazingTablatureTrainingStore(args.root)
    try:
        if args.command == "ingest":
            result = store.ingest(
                args.source,
                source_copedent_id=args.source_copedent,
                source_copedent_confidence=args.copedent_confidence,
                evidence_type=args.evidence_type,
                batch_id=args.batch_id,
            )
        elif args.command == "partition":
            result = store.prepare_partition(
                args.batch_id,
                document_breaks=args.document_break,
                forced_discovery=args.force_discovery,
                discovery_target=args.discovery_target,
                validation_target=args.validation_target,
                test_target=args.test_target,
                guard_radius=args.guard_radius,
                similarity_threshold=args.similarity_threshold,
            )
        elif args.command == "supersede-batch":
            result = store.supersede_batch(
                args.batch_id,
                replacement_batch_id=args.replacement_batch,
                approval_reference=args.approval_reference,
            )
        elif args.command == "verify-intake":
            result = store.verify_batch_inputs(args.batch_id)
        elif args.command == "annotate":
            result = store.import_annotations(args.batch_id, args.annotations)
        elif args.command == "validate":
            result = store.validate(args.batch_id)
        elif args.command == "review":
            result = store.apply_review(args.batch_id, args.resolutions)
        elif args.command == "train":
            result = store.train(epochs=args.epochs, learning_rate=args.learning_rate)
        elif args.command == "evaluate":
            result = store.evaluate(args.model_id)
        elif args.command == "report":
            result = store.report(args.model_id)
        elif args.command == "promote":
            result = store.promote(
                args.model_id,
                channel=args.channel,
                approval_reference=args.approval_reference,
                lane15_handoff=args.lane15_handoff,
            )
        elif args.command == "reject":
            result = store.reject(args.model_id, approval_reference=args.approval_reference)
        elif args.command == "rollback":
            result = store.rollback(
                channel=args.channel,
                model_id=args.model_id,
                approval_reference=args.approval_reference,
            )
        elif args.command == "batch-status":
            result = store.batch_status(args.batch_id)
        else:
            result = store.status()
    except TrainingWorkflowError as exc:
        parser.exit(2, f"Amazing Tablature workflow stopped: {exc}\n")
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
