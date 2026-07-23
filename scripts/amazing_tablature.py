#!/usr/bin/env python3
"""Operate the private Lane 20 Amazing Tablature training workflow."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from pocketsteel.amazing_tablature_extraction import (
    AmazingTablatureExtractor,
    ExtractionWorkflowError,
    serve_review_consoles,
)
from pocketsteel.amazing_tablature_training import (
    DEFAULT_PRIVATE_ROOT,
    AmazingTablatureTrainingStore,
    TrainingWorkflowError,
)
from pocketsteel.amazing_tablature_sealed_test import (
    SealedTestCoordinator,
    SealedTestWorkflowError,
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
    ingest.add_argument(
        "--source-copedent-evidence",
        action="append",
        default=[],
        help="Register a copedent chart as immutable evidence without treating it as a score/tab input.",
    )

    partition = subparsers.add_parser(
        "partition",
        help="Create and seal a leakage-resistant discovery/validation/test split.",
    )
    partition.add_argument("batch_id")
    partition.add_argument("--document-break", action="append", default=[])
    partition.add_argument("--force-discovery", action="append", default=[])
    partition.add_argument(
        "--content-unit-break",
        action="append",
        default=[],
        help="Start a new indivisible content unit at this registered page.",
    )
    partition.add_argument(
        "--page-level-units",
        action="store_true",
        help="Start each registered page as its own provisional unit before semantic linking.",
    )
    partition.add_argument(
        "--semantic-groups",
        type=Path,
        help="Private JSON map linking non-contiguous and multi-page semantic units.",
    )
    partition.add_argument("--discovery-target", type=int, default=194)
    partition.add_argument("--validation-target", type=int, default=28)
    partition.add_argument("--test-target", type=int, default=56)
    partition.add_argument("--guard-radius", type=int, default=1)
    partition.add_argument("--similarity-threshold", type=int, default=3)

    split_review = subparsers.add_parser(
        "record-split-review",
        help="Bind an independent PASS or FAIL verdict to the exact sealed partition digest.",
    )
    split_review.add_argument("batch_id")
    split_review.add_argument("--outcome", choices=("pass", "fail"), required=True)
    split_review.add_argument("--partition-digest", required=True)
    split_review.add_argument("--reviewer-reference", required=True)
    split_review.add_argument("--review-artifact-digest")

    supersede = subparsers.add_parser(
        "supersede-batch",
        help="Preserve an old batch as historical and exclude it from future datasets.",
    )
    supersede.add_argument("batch_id")
    supersede.add_argument("--replacement-batch", required=True)
    supersede.add_argument("--approval-reference", required=True)

    compose = subparsers.add_parser(
        "compose-dataset",
        help="Bind multiple active sealed batches into one authoritative training dataset.",
    )
    compose.add_argument("--batch", action="append", required=True)
    compose.add_argument("--approval-reference", required=True)

    verify = subparsers.add_parser("verify-intake", help="Re-hash a batch and verify the source files are unchanged.")
    verify.add_argument("batch_id")

    authorize_use = subparsers.add_parser(
        "record-use-authorization",
        help="Record a reviewed rights basis and exact allowed uses for one private batch.",
    )
    authorize_use.add_argument("batch_id")
    authorize_use.add_argument(
        "--rights-status",
        choices=("unknown", "owner_authorized", "licensed", "public_domain_verified", "user_provided_authorized"),
        required=True,
    )
    authorize_use.add_argument(
        "--allow",
        action="append",
        default=[],
        choices=(
            "privateExtraction",
            "privateEvaluation",
            "modelTraining",
            "embeddings",
            "quotation",
            "publicDisplay",
            "runtimeProductUse",
            "derivativeRulePublication",
        ),
    )
    authorize_use.add_argument("--approval-reference", required=True)

    extract = subparsers.add_parser(
        "extract",
        help="Extract private provenance-backed teaching knowledge from discovery or validation pages.",
    )
    extract.add_argument("batch_id")
    extract.add_argument("--partition", choices=("discovery", "validation"), default="discovery")
    extract.add_argument(
        "--validation-model-id",
        help="Exact complete-discovery canonical challenger that authorizes and is pinned to validation extraction.",
    )
    extract.add_argument("--audiveris-bin", type=Path)
    extract.add_argument("--vision-model", default="gemma4:12b")
    extract.add_argument("--vision-base-url", default="http://127.0.0.1:11434")
    extract.add_argument("--tab-reader", choices=("apple", "ollama"), default="ollama")
    extract.add_argument("--no-ocr", action="store_true")
    extract.add_argument("--no-omr", action="store_true")
    extract.add_argument("--no-tab-vision", action="store_true")
    extract.add_argument("--no-resume", action="store_true")
    extract.add_argument("--workers", type=int, default=1)

    refresh_unreviewed = subparsers.add_parser(
        "refresh-unreviewed-extraction",
        help="Refresh only never-reviewed discovery pages with the current extractor.",
    )
    refresh_unreviewed.add_argument("batch_id")
    refresh_unreviewed.add_argument("--limit", type=int, default=25)
    refresh_unreviewed.add_argument("--audiveris-bin", type=Path)
    refresh_unreviewed.add_argument("--vision-model", default="gemma4:12b")
    refresh_unreviewed.add_argument("--vision-base-url", default="http://127.0.0.1:11434")
    refresh_unreviewed.add_argument("--tab-reader", choices=("apple", "ollama"), default="ollama")
    refresh_unreviewed.add_argument("--no-ocr", action="store_true")
    refresh_unreviewed.add_argument("--no-omr", action="store_true")
    refresh_unreviewed.add_argument("--no-tab-vision", action="store_true")
    refresh_unreviewed.add_argument("--no-resume", action="store_true")
    refresh_unreviewed.add_argument("--workers", type=int, default=1)
    refresh_unreviewed.add_argument(
        "--tab-pages-only",
        action="store_true",
        help="Refresh only pages whose existing extraction contains tablature systems.",
    )

    audit_discovery = subparsers.add_parser(
        "audit-discovery-completion",
        help=(
            "Classify remaining discovery pages for refresh, internal remediation, "
            "or genuinely ready human review without opening held-out data."
        ),
    )
    audit_discovery.add_argument("batch_id")

    quarantine_discovery = subparsers.add_parser(
        "quarantine-discovery-remainder",
        help=(
            "Apply an explicitly approved bulk exclusion to the exact audited "
            "discovery remainder without approving its facts or opening held-out data."
        ),
    )
    quarantine_discovery.add_argument("batch_id")
    quarantine_discovery.add_argument("--approval-reference", required=True)
    quarantine_discovery.add_argument(
        "--confirm-bulk-quarantine",
        action="store_true",
        help="Confirm that every currently undispositioned discovery page is excluded from this training snapshot.",
    )

    remediate_discovery_score = subparsers.add_parser(
        "remediate-discovery-score-correspondence",
        help=(
            "Build score-only canaries from current correction-confirmed discovery "
            "records without changing reviewed facts or opening held-out data."
        ),
    )
    remediate_discovery_score.add_argument("batch_id")
    remediate_discovery_score.add_argument("--limit", type=int, default=5)
    remediate_discovery_score.add_argument("--workers", type=int, default=1)
    remediate_discovery_score.add_argument("--audiveris-bin", type=Path)

    freeze_score_notehead_benchmark = subparsers.add_parser(
        "freeze-source-score-notehead-benchmark",
        help=(
            "Freeze approved discovery score lines into page-grouped development "
            "and shadow subsets without opening held-out data."
        ),
    )
    freeze_score_notehead_benchmark.add_argument("batch_id")

    evaluate_score_notehead = subparsers.add_parser(
        "evaluate-source-score-notehead-challenger",
        help=(
            "Evaluate the frozen source-only notehead detector on development "
            "or the page-grouped discovery shadow subset."
        ),
    )
    evaluate_score_notehead.add_argument("batch_id")
    evaluate_score_notehead.add_argument(
        "--subset", choices=("development", "shadow"), default="development"
    )

    evaluate_score_vision = subparsers.add_parser(
        "evaluate-source-score-vision-regression",
        help=(
            "Run an unconstrained score-only visual reader on the already-opened "
            "discovery regression lines without creating review or training data."
        ),
    )
    evaluate_score_vision.add_argument("batch_id")
    evaluate_score_vision.add_argument("--workers", type=int, default=2)
    evaluate_score_vision.add_argument("--limit", type=int, default=39)
    evaluate_score_vision.add_argument("--vision-model", default="gemma4:12b")
    evaluate_score_vision.add_argument(
        "--vision-base-url", default="http://127.0.0.1:11434"
    )
    evaluate_score_vision.add_argument("--no-resume", action="store_true")

    build_score_sequence_dataset = subparsers.add_parser(
        "build-discovery-score-sequence-dataset",
        help=(
            "Build a private digest-pinned image-to-approved-pitch-sequence "
            "manifest from the opened discovery benchmark."
        ),
    )
    build_score_sequence_dataset.add_argument("batch_id")

    train_score_sequence = subparsers.add_parser(
        "train-discovery-score-sequence-challenger",
        help=(
            "Train a private full-line score CTC reader on development, freeze "
            "it, and score the already-opened discovery shadow once."
        ),
    )
    train_score_sequence.add_argument("batch_id")
    train_score_sequence.add_argument(
        "--dependency-root",
        type=Path,
        help=(
            "Ignored private site-packages directory containing PyTorch. "
            "Defaults beneath the Lane 20 private root."
        ),
    )
    train_score_sequence.add_argument("--seed", type=int, default=1729)
    train_score_sequence.add_argument("--maximum-epochs", type=int, default=80)

    evaluate_guided_capture = subparsers.add_parser(
        "evaluate-discovery-guided-capture-regression",
        help=(
            "Replay corrected discovery lines with reviewed geometry while "
            "measuring machine-read tab states and score pitches only."
        ),
    )
    evaluate_guided_capture.add_argument("batch_id")
    evaluate_guided_capture.add_argument("--limit", type=int, default=8)
    evaluate_guided_capture.add_argument("--vision-model", default="gemma4:12b")
    evaluate_guided_capture.add_argument(
        "--vision-base-url", default="http://127.0.0.1:11434"
    )

    evaluate_semantic_score_repair = subparsers.add_parser(
        "evaluate-discovery-source-score-semantic-repair",
        help=(
            "Replay source-only attack, tie, and key-signature repair on the "
            "opened discovery benchmark without review or training output."
        ),
    )
    evaluate_semantic_score_repair.add_argument("batch_id")

    evaluate_machine_timeline = subparsers.add_parser(
        "evaluate-discovery-machine-score-tab-timeline",
        help=(
            "Join source-only score semantics to archived pre-correction machine "
            "tablature on opened discovery lines and fail closed before review."
        ),
    )
    evaluate_machine_timeline.add_argument("batch_id")

    evaluate_tab_row_geometry = subparsers.add_parser(
        "evaluate-discovery-tab-row-geometry-challenger",
        help=(
            "Evaluate a narrow split-grip row merge against opened discovery "
            "lines without changing records or creating human review work."
        ),
    )
    evaluate_tab_row_geometry.add_argument("batch_id")

    freeze_tab_row_geometry = subparsers.add_parser(
        "freeze-discovery-tab-row-geometry-contract",
        help="Freeze the one regression-passed split-grip geometry contract.",
    )
    freeze_tab_row_geometry.add_argument("batch_id")

    evaluate_tab_action_recovery = subparsers.add_parser(
        "evaluate-discovery-tab-action-recovery-challenger",
        help=(
            "Read complete mechanically valid actions for frozen split-grip "
            "proposals on opened discovery only."
        ),
    )
    evaluate_tab_action_recovery.add_argument("batch_id")
    evaluate_tab_action_recovery.add_argument(
        "--tab-reader", choices=("apple", "ollama"), default="ollama"
    )
    evaluate_tab_action_recovery.add_argument("--vision-model", default="gemma4:12b")
    evaluate_tab_action_recovery.add_argument(
        "--vision-base-url", default="http://127.0.0.1:11434"
    )

    evaluate_score_projection = subparsers.add_parser(
        "evaluate-source-score-projection-challenger",
        help=(
            "Evaluate the fixed source-image projection fusion on the opened "
            "discovery regression benchmark without promotion or review creation."
        ),
    )
    evaluate_score_projection.add_argument("batch_id")

    evaluate_score_component_hybrid = subparsers.add_parser(
        "evaluate-source-score-component-hybrid-challenger",
        help=(
            "Evaluate compact notehead components after the fixed projection "
            "challenger on opened discovery regressions only."
        ),
    )
    evaluate_score_component_hybrid.add_argument("batch_id")

    freeze_score_component_hybrid = subparsers.add_parser(
        "freeze-source-score-component-hybrid-contract",
        help=(
            "Freeze the fitted component-hybrid detector for a future unseen "
            "discovery shadow; do not promote it."
        ),
    )
    freeze_score_component_hybrid.add_argument("batch_id")

    freeze_score_projection = subparsers.add_parser(
        "freeze-source-score-projection-contract",
        help=(
            "Freeze the regression-passed projection detector for a future "
            "previously unseen discovery shadow; do not promote it."
        ),
    )
    freeze_score_projection.add_argument("batch_id")

    capture_score_projection_shadow = subparsers.add_parser(
        "capture-source-score-projection-shadow",
        help=(
            "Freeze predictions for unseen discovery score lines before any "
            "human-facing review artifact exists."
        ),
    )
    capture_score_projection_shadow.add_argument("batch_id")
    capture_score_projection_shadow.add_argument("--limit", type=int, default=25)

    score_score_projection_shadow = subparsers.add_parser(
        "score-source-score-projection-shadow",
        help=(
            "Score previously frozen discovery predictions after independent "
            "human-approved truth arrives."
        ),
    )
    score_score_projection_shadow.add_argument("batch_id")
    score_score_projection_shadow.add_argument(
        "--minimum-cases", type=int, default=5
    )

    select_score_notehead = subparsers.add_parser(
        "freeze-source-score-notehead-challenger-contract",
        help="Freeze the exact development-passed source-notehead detector before shadow evaluation.",
    )
    select_score_notehead.add_argument("batch_id")

    prepare_extraction_review = subparsers.add_parser(
        "prepare-extraction-review",
        help="Prepare a private side-by-side review packet for extracted discovery or validation pages.",
    )
    prepare_extraction_review.add_argument("batch_id")
    prepare_extraction_review.add_argument("--partition", choices=("discovery", "validation"), default="discovery")
    prepare_extraction_review.add_argument("--limit", type=int, default=25)
    prepare_extraction_review.add_argument(
        "--feedback-corrections-only",
        action="store_true",
        help="Include only corrected pages that have prior reviewer feedback.",
    )
    prepare_extraction_review.add_argument(
        "--never-reviewed-only",
        action="store_true",
        help="Exclude every page that already has reviewer feedback.",
    )
    prepare_extraction_review.add_argument(
        "--current-extractor-only",
        action="store_true",
        help="Include only pages refreshed with the current extractor version.",
    )
    prepare_extraction_review.add_argument(
        "--tab-pages-only",
        action="store_true",
        help="Include only pages containing detected tablature systems.",
    )
    prepare_extraction_review.add_argument(
        "--passing-refresh-gate-only",
        action="store_true",
        help="Withhold refreshed pages that regress structurally or mechanically.",
    )

    serve_review = subparsers.add_parser(
        "serve-extraction-review",
        help="Serve private review consoles and receive idempotent loopback-only review submissions.",
    )
    serve_review.add_argument("--port", type=int, default=8766)

    apply_extraction_review = subparsers.add_parser(
        "apply-extraction-review",
        help="Apply immutable human accept, correction, or exclusion decisions to extracted pages.",
    )
    apply_extraction_review.add_argument("batch_id")
    apply_extraction_review.add_argument("decisions", type=Path)
    apply_extraction_review.add_argument("--partition", choices=("discovery", "validation"), default="discovery")

    prepare_score_audit = subparsers.add_parser(
        "prepare-score-audit-review",
        help="Prepare a private per-system music-score audit for already approved pages.",
    )
    prepare_score_audit.add_argument("batch_id")
    prepare_score_audit.add_argument("--partition", choices=("discovery", "validation"), default="discovery")
    prepare_score_audit.add_argument("--limit", type=int, default=25)

    repair_score_audit = subparsers.add_parser(
        "repair-score-audit",
        help="Build digest-pinned score-only candidates for the internal score-audit repair queue.",
    )
    repair_score_audit.add_argument("batch_id")
    repair_score_audit.add_argument(
        "--partition", choices=("discovery", "validation"), default="discovery"
    )
    repair_score_audit.add_argument("--workers", type=int, default=1)
    repair_score_audit.add_argument("--limit", type=int, default=100)
    repair_score_audit.add_argument(
        "--input-id",
        action="append",
        default=[],
        help="Repair only this queued discovery input; repeat for more than one input.",
    )

    apply_score_audit = subparsers.add_parser(
        "apply-score-audit-review",
        help="Apply explicit per-system music-score audit decisions without changing prior tab approval.",
    )
    apply_score_audit.add_argument("batch_id")
    apply_score_audit.add_argument("decisions", type=Path)
    apply_score_audit.add_argument("--partition", choices=("discovery", "validation"), default="discovery")

    apply_score_corrections = subparsers.add_parser(
        "apply-score-audit-corrections",
        help="Apply digest-pinned score corrections from reviewed audit feedback.",
    )
    apply_score_corrections.add_argument("batch_id")
    apply_score_corrections.add_argument("corrections", type=Path)
    apply_score_corrections.add_argument(
        "--partition", choices=("discovery", "validation"), default="discovery"
    )
    apply_score_corrections.add_argument("--dry-run", action="store_true")

    qualify_score_scope = subparsers.add_parser(
        "qualify-score-audit-scope",
        help="Limit an approved score audit to pitch/harmony correspondence, excluding score rhythm.",
    )
    qualify_score_scope.add_argument("batch_id")
    qualify_score_scope.add_argument("--input-id", required=True)
    qualify_score_scope.add_argument("--expected-score-audit-decision-id", required=True)
    qualify_score_scope.add_argument("--reviewer-reference", required=True)
    qualify_score_scope.add_argument(
        "--partition", choices=("discovery", "validation"), default="discovery"
    )

    apply_feedback_corrections = subparsers.add_parser(
        "apply-feedback-corrections",
        help="Apply digest-pinned machine corrections from reviewed feedback without granting human approval.",
    )
    apply_feedback_corrections.add_argument("batch_id")
    apply_feedback_corrections.add_argument("corrections", type=Path)
    apply_feedback_corrections.add_argument(
        "--partition", choices=("discovery", "validation"), default="discovery"
    )
    apply_feedback_corrections.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate every correction in memory without writing corrected records or logs.",
    )

    prepare_feedback_confirmation = subparsers.add_parser(
        "prepare-feedback-correction-confirmation",
        help="Prepare a compact tab-only confirmation for applied reviewer corrections.",
    )
    prepare_feedback_confirmation.add_argument("batch_id")
    prepare_feedback_confirmation.add_argument("corrections", type=Path)
    prepare_feedback_confirmation.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )

    apply_feedback_confirmation = subparsers.add_parser(
        "apply-feedback-correction-confirmation-review",
        help="Apply a submitted tab-only correction confirmation without approving score facts.",
    )
    apply_feedback_confirmation.add_argument("batch_id")
    apply_feedback_confirmation.add_argument("submission", type=Path)
    apply_feedback_confirmation.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )

    prepare_combined_score_tab = subparsers.add_parser(
        "prepare-combined-score-tab-review",
        help="Prepare one combined score, confirmed-tab, and correspondence audit.",
    )
    prepare_combined_score_tab.add_argument("batch_id")
    prepare_combined_score_tab.add_argument(
        "--input-id",
        action="append",
        required=True,
        help="Include this correction-approved discovery input; repeat for additional pages.",
    )
    prepare_combined_score_tab.add_argument(
        "--score-system-id",
        action="append",
        default=[],
        help=(
            "Show only this score system within the requested pages; repeat for additional "
            "changed lines."
        ),
    )
    prepare_combined_score_tab.add_argument(
        "--key-signature-override",
        action="append",
        default=[],
        metavar="SCORE_SYSTEM_ID=FIFTHS",
        help=(
            "Use a directly observed printed key signature for one reviewed system; "
            "repeat for additional systems."
        ),
    )
    prepare_combined_score_tab.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )
    prepare_combined_score_tab.add_argument(
        "--no-activate",
        action="store_true",
        help=(
            "Write a digest-versioned packet without replacing the current review URL; "
            "use this to stage later work while another packet is being reviewed."
        ),
    )
    prepare_combined_score_tab.add_argument(
        "--provisional-joint-review",
        action="store_true",
        help="Require the reviewer to confirm both the displayed tablature and score mapping.",
    )

    prepare_validation_contact_consensus = subparsers.add_parser(
        "prepare-validation-contact-consensus",
        help=(
            "Reconstruct validation tab event columns through semantic agreement "
            "between distinct local vision-model artifacts."
        ),
    )
    prepare_validation_contact_consensus.add_argument("batch_id")
    prepare_validation_contact_consensus.add_argument(
        "--reader-model",
        action="append",
        default=[],
        help=(
            "Local vision model used as an independent cell reader; repeat at "
            "least twice. Defaults to the two pinned local Gemma readers."
        ),
    )

    prepare_validation_line_audit = subparsers.add_parser(
        "prepare-validation-line-audit",
        help=(
            "Prepare a complete line-level validation ground-truth audit without "
            "opening sealed test or creating training evidence."
        ),
    )
    prepare_validation_line_audit.add_argument("batch_id")
    prepare_validation_line_audit.add_argument(
        "--no-activate",
        action="store_true",
        help="Write an immutable digest-versioned audit without replacing its current URL.",
    )

    prepare_canonical_validation = subparsers.add_parser(
        "prepare-canonical-validation-review",
        help=(
            "Prepare one no-blank human confirmation packet covering every "
            "scored complete line in the authoritative validation dataset."
        ),
    )
    prepare_canonical_validation.add_argument("batch_id")
    prepare_canonical_validation.add_argument(
        "--model-id",
        required=True,
    )
    prepare_canonical_validation.add_argument(
        "--score-report-digest",
        required=True,
    )

    apply_canonical_validation_corrections = subparsers.add_parser(
        "apply-canonical-validation-corrections",
        help=(
            "Apply exact canonical validation feedback to an append-only, "
            "no-training ground-truth overlay and prepare only necessary "
            "correction confirmations."
        ),
    )
    apply_canonical_validation_corrections.add_argument("model_id")
    apply_canonical_validation_corrections.add_argument(
        "correction_plan",
        type=Path,
    )
    apply_canonical_validation_corrections.add_argument(
        "--score-report-digest",
        required=True,
    )
    apply_canonical_validation_corrections.add_argument(
        "--packet-digest",
        required=True,
    )
    apply_canonical_validation_corrections.add_argument(
        "--submission-id",
        required=True,
    )

    apply_canonical_validation_followup = subparsers.add_parser(
        "apply-canonical-validation-followup-corrections",
        help=(
            "Apply feedback from a focused canonical correction packet to the "
            "append-only validation truth overlay and rereview only the lines "
            "that changed again."
        ),
    )
    apply_canonical_validation_followup.add_argument("model_id")
    apply_canonical_validation_followup.add_argument(
        "correction_plan",
        type=Path,
    )
    apply_canonical_validation_followup.add_argument(
        "--correction-report-digest",
        required=True,
    )
    apply_canonical_validation_followup.add_argument(
        "--packet-digest",
        required=True,
    )
    apply_canonical_validation_followup.add_argument(
        "--submission-id",
        required=True,
    )

    remediate_validation_capture = subparsers.add_parser(
        "remediate-validation-machine-capture",
        help=(
            "Recapture incomplete validation lines from machine visual geometry, "
            "guided state reading, and fail-closed checks without using human truth."
        ),
    )
    remediate_validation_capture.add_argument("batch_id")
    remediate_validation_capture.add_argument("--input-id", action="append", default=[])
    remediate_validation_capture.add_argument("--limit", type=int, default=8)
    remediate_validation_capture.add_argument("--no-resume", action="store_true")
    remediate_validation_capture.add_argument("--apply", action="store_true")
    remediate_validation_capture.add_argument("--vision-model", default="gemma4:12b")
    remediate_validation_capture.add_argument(
        "--vision-base-url", default="http://127.0.0.1:11434"
    )

    prepare_challenger_comparison = subparsers.add_parser(
        "prepare-challenger-comparison-review",
        help="Show concrete source and challenger tablature only where a score-gated shadow disagrees.",
    )
    prepare_challenger_comparison.add_argument("batch_id")
    prepare_challenger_comparison.add_argument("--model-id", required=True)
    prepare_challenger_comparison.add_argument("--report-digest", required=True)
    prepare_challenger_comparison.add_argument(
        "--input-id", action="append", required=True
    )
    prepare_challenger_comparison.add_argument(
        "--score-system-id", action="append", default=[]
    )
    prepare_challenger_comparison.add_argument(
        "--max-decisions",
        type=int,
        default=None,
        help="Cap the packet to the first N concrete differences (1-12).",
    )

    prepare_validation_disagreements = subparsers.add_parser(
        "prepare-validation-disagreement-review",
        help=(
            "Show only complete, mechanically valid held-out movements where "
            "the exact challenger and machine-captured source tablature differ."
        ),
    )
    prepare_validation_disagreements.add_argument("batch_id")
    prepare_validation_disagreements.add_argument("--model-id", required=True)
    prepare_validation_disagreements.add_argument(
        "--disagreement-digest",
        required=True,
    )

    apply_challenger_comparison = subparsers.add_parser(
        "apply-challenger-comparison-review",
        help="Apply reviewed source-vs-challenger tablature preferences to discovery evidence.",
    )
    apply_challenger_comparison.add_argument("batch_id")
    apply_challenger_comparison.add_argument("submission", type=Path)
    apply_challenger_comparison.add_argument("--dry-run", action="store_true")

    apply_combined_score_tab = subparsers.add_parser(
        "apply-combined-score-tab-review",
        help=(
            "Apply a received combined score/tab review as line-scoped pitch evidence, "
            "leaving rhythm excluded and unresolved correspondence out of training."
        ),
    )
    apply_combined_score_tab.add_argument("batch_id")
    apply_combined_score_tab.add_argument("submission", type=Path)
    apply_combined_score_tab.add_argument("--dry-run", action="store_true")
    apply_combined_score_tab.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )

    replay_combined_score_tab = subparsers.add_parser(
        "replay-combined-score-tab-regressions",
        help=(
            "Re-evaluate current discovery line approvals and prove unresolved or "
            "superseded evidence cannot enter training."
        ),
    )
    replay_combined_score_tab.add_argument("batch_id")
    replay_combined_score_tab.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )

    quarantine_combined_score_tab = subparsers.add_parser(
        "quarantine-combined-score-tab-regressions",
        help=(
            "Supersede stale discovery line eligibility after a stricter combined "
            "alignment contract detects a regression."
        ),
    )
    quarantine_combined_score_tab.add_argument("batch_id")
    quarantine_combined_score_tab.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )

    revalidate_normalized_positions = subparsers.add_parser(
        "revalidate-combined-score-tab-normalized-positions",
        help=(
            "Preserve one human-confirmed v4 score decision while rebuilding its "
            "normalized-position grouping and alignments under the scale-aware gate."
        ),
    )
    revalidate_normalized_positions.add_argument("batch_id")
    revalidate_normalized_positions.add_argument("--input-id", required=True)
    revalidate_normalized_positions.add_argument("--score-system-id", required=True)
    revalidate_normalized_positions.add_argument(
        "--partition", choices=("discovery",), default="discovery"
    )

    extraction_review_metrics = subparsers.add_parser(
        "extraction-review-metrics",
        help="Compute private aggregate extraction accuracy and correction metrics from human-reviewed pages.",
    )
    extraction_review_metrics.add_argument("batch_id")
    extraction_review_metrics.add_argument("--partition", choices=("discovery", "validation"), default="discovery")

    replay_event_counts = subparsers.add_parser(
        "replay-event-count-exceptions",
        help="Run a discovery-only whole-system count challenger without changing reviewed records.",
    )
    replay_event_counts.add_argument("batch_id")
    replay_event_counts.add_argument("--vision-model", default="gemma4:12b")
    replay_event_counts.add_argument("--vision-base-url", default="http://127.0.0.1:11434")
    replay_event_counts.add_argument("--no-resume", action="store_true")

    prepare_event_localization = subparsers.add_parser(
        "prepare-event-localization-review",
        help=(
            "Localize only the remaining discovery event-count exceptions and prepare a compact "
            "source-beside-tablature review."
        ),
    )
    prepare_event_localization.add_argument("batch_id")
    prepare_event_localization.add_argument("--vision-model", default="gemma4:12b")
    prepare_event_localization.add_argument(
        "--vision-base-url", default="http://127.0.0.1:11434"
    )
    prepare_event_localization.add_argument("--no-resume", action="store_true")

    prepare_score_pitch = subparsers.add_parser(
        "prepare-score-pitch-correspondence-review",
        help=(
            "Recapture conventional-score pitches independently and prepare a compact "
            "score-to-tablature scientific-pitch audit."
        ),
    )
    prepare_score_pitch.add_argument("batch_id")
    prepare_score_pitch.add_argument("--vision-model", default="gemma4:12b")
    prepare_score_pitch.add_argument("--vision-base-url", default="http://127.0.0.1:11434")
    prepare_score_pitch.add_argument("--no-resume", action="store_true")

    replay_score_chord_omissions = subparsers.add_parser(
        "replay-score-chord-omission-gate",
        help=(
            "Re-evaluate reviewed discovery score/tab links and withhold any relationship "
            "whose pitch-and-octave sets are not exact."
        ),
    )
    replay_score_chord_omissions.add_argument("batch_id")

    prepare_score_chord_omission_review = subparsers.add_parser(
        "prepare-score-chord-omission-review",
        help="Prepare a compact source-beside-tab review for strict score-subset cases.",
    )
    prepare_score_chord_omission_review.add_argument("batch_id")

    prepare_full_line_score_recapture = subparsers.add_parser(
        "prepare-full-line-score-recapture-review",
        help=(
            "Recapture complete discovery score lines under human-supplied event-count "
            "constraints and prepare a full score-to-tab review."
        ),
    )
    prepare_full_line_score_recapture.add_argument("batch_id")
    prepare_full_line_score_recapture.add_argument("constraints", type=Path)
    prepare_full_line_score_recapture.add_argument("--vision-model", default="gemma4:12b")
    prepare_full_line_score_recapture.add_argument(
        "--vision-base-url", default="http://127.0.0.1:11434"
    )
    prepare_full_line_score_recapture.add_argument("--no-resume", action="store_true")

    apply_full_line_score_recapture = subparsers.add_parser(
        "apply-full-line-score-recapture-review",
        help=(
            "Apply a submitted complete-line review plus digest-pinned structured corrections "
            "as pitch-only score/tab truth."
        ),
    )
    apply_full_line_score_recapture.add_argument("batch_id")
    apply_full_line_score_recapture.add_argument("submission", type=Path)
    apply_full_line_score_recapture.add_argument("corrections", type=Path)
    apply_full_line_score_recapture.add_argument("--dry-run", action="store_true")

    derive_decisions = subparsers.add_parser(
        "derive-reviewed-decisions",
        help="Materialize page-approved abstract ranking decisions into an immutable partition ledger.",
    )
    derive_decisions.add_argument("batch_id")
    derive_decisions.add_argument("--partition", choices=("discovery", "validation"), required=True)

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

    train_discovery = subparsers.add_parser(
        "train-discovery-challenger",
        help="Freeze reviewed discovery evidence and build a non-promotable active-learning challenger.",
    )
    train_discovery.add_argument("--epochs", type=int, default=20)
    train_discovery.add_argument("--learning-rate", type=float, default=0.05)
    train_discovery.add_argument("--base-model-id")
    train_discovery.add_argument(
        "--average-weights",
        action="store_true",
        help="Average pairwise-perceptron weights across steps to reduce order sensitivity.",
    )
    train_discovery.add_argument(
        "--base-weight-ratio",
        type=float,
        default=0.0,
        help="Shrink retrained style weights toward the exact discovery baseline (0-1).",
    )
    train_discovery.add_argument(
        "--experimental-style",
        action="append",
        default=[],
        help="Retrain only this style while inheriting all other styles from the discovery baseline.",
    )

    train_complete = subparsers.add_parser(
        "train-complete-discovery",
        help=(
            "Build a canonical validation candidate from fully reviewed discovery "
            "using an exact discovery baseline."
        ),
    )

    transition_decoder = subparsers.add_parser(
        "build-discovery-transition-decoder",
        help=(
            "Build a precision-first source movement decoder from approved "
            "discovery records without reading validation or sealed-test data."
        ),
    )
    transition_decoder.add_argument("batch_id")
    glyph_decoder = subparsers.add_parser(
        "build-discovery-glyph-decoder",
        help=(
            "Build a precision-first visual tab-glyph decoder from approved "
            "discovery records without reading validation or sealed-test data."
        ),
    )
    glyph_decoder.add_argument("batch_id")
    reader_calibration = subparsers.add_parser(
        "build-discovery-reader-calibration",
        help=(
            "Calibrate pinned tab-cell readers against human-approved "
            "discovery corrections without reading validation or sealed test."
        ),
    )
    reader_calibration.add_argument("batch_id")
    reader_calibration.add_argument(
        "--reader-model",
        action="append",
        default=[],
        help=(
            "Pinned local vision reader to calibrate; repeat at least twice. "
            "Defaults to the two current Gemma readers."
        ),
    )
    train_complete.add_argument("--base-model-id", required=True)
    train_complete.add_argument("--epochs", type=int, default=20)
    train_complete.add_argument("--learning-rate", type=float, default=0.05)
    train_complete.add_argument("--average-weights", action="store_true")
    train_complete.add_argument(
        "--base-weight-ratio",
        type=float,
        default=0.20,
        help="Initialize every canonical style from the exact baseline while updating from complete discovery.",
    )

    canonical_readiness = subparsers.add_parser(
        "canonical-readiness",
        help="Report discovery-completion blockers without opening validation or sealed tests.",
    )
    canonical_readiness.add_argument("--base-model-id")

    shadow_discovery = subparsers.add_parser(
        "shadow-test-discovery",
        help="Score remaining discovery hypotheses and select a bounded review set.",
    )
    shadow_discovery.add_argument("model_id")
    shadow_discovery.add_argument("--max-review-lines", type=int, default=12)

    evaluate = subparsers.add_parser("evaluate", help="Compare a challenger against holdout decisions and the champion.")
    evaluate.add_argument("model_id")

    score_validation_lines = subparsers.add_parser(
        "score-validation-line-audits",
        help=(
            "Verify and score immutable expert validation line receipts without "
            "adding validation evidence to training."
        ),
    )
    score_validation_lines.add_argument("model_id")

    score_validation_machine = subparsers.add_parser(
        "score-validation-machine-candidates",
        help=(
            "Score only complete discovery-calibrated validation tab lines "
            "without treating machine consensus as training or human truth."
        ),
    )
    score_validation_machine.add_argument("model_id")

    adjudicate_validation_machine = subparsers.add_parser(
        "adjudicate-validation-machine-disagreements",
        help=(
            "Measure immutable expert adjudication of machine-consensus "
            "challenger disagreements without adding validation to training."
        ),
    )
    adjudicate_validation_machine.add_argument("model_id")
    adjudicate_validation_machine.add_argument("--batch-id", required=True)
    adjudicate_validation_machine.add_argument(
        "--score-report-digest",
        required=True,
    )
    adjudicate_validation_machine.add_argument(
        "--submission-id",
        required=True,
    )

    carry_validation_adjudication = subparsers.add_parser(
        "carry-forward-validation-adjudication",
        help=(
            "Reuse a prior expert validation verdict only when every "
            "preference-relevant disagreement field is exactly equivalent."
        ),
    )
    carry_validation_adjudication.add_argument("model_id")
    carry_validation_adjudication.add_argument(
        "--score-report-digest",
        required=True,
    )
    carry_validation_adjudication.add_argument(
        "--source-adjudication-digest",
        required=True,
    )
    carry_validation_adjudication.add_argument(
        "--current-packet-digest",
        required=True,
    )

    score_canonical_validation = subparsers.add_parser(
        "score-canonical-validation-review",
        help=(
            "Verify the complete-line human confirmation and close the "
            "canonical gate without adding validation evidence to training."
        ),
    )
    score_canonical_validation.add_argument("model_id")
    score_canonical_validation.add_argument(
        "--score-report-digest",
        required=True,
    )
    score_canonical_validation.add_argument(
        "--packet-digest",
        required=True,
    )
    score_canonical_validation.add_argument(
        "--submission-id",
        required=True,
    )
    score_canonical_validation.add_argument(
        "--adjudication-digest",
        required=True,
    )
    score_canonical_validation.add_argument(
        "--equivalence-digest",
        required=True,
    )

    report = subparsers.add_parser("report", help="Write a private metrics-only challenger report.")
    report.add_argument("model_id")

    freeze = subparsers.add_parser(
        "freeze-rules",
        help="Freeze the exact passing model, validators, schemas, copedents, and code digests before sealed tests.",
    )
    freeze.add_argument("model_id")

    prepare_ground_truth = subparsers.add_parser(
        "prepare-sealed-ground-truth",
        help="Open one sealed cohort for isolated Lane 15 ground-truth annotation after rules freeze.",
    )
    prepare_ground_truth.add_argument("batch_id")
    prepare_ground_truth.add_argument("--freeze-id", required=True)

    import_ground_truth = subparsers.add_parser(
        "import-sealed-ground-truth",
        help="Import complete independently reviewed ground truth for one frozen sealed cohort.",
    )
    import_ground_truth.add_argument("batch_id")
    import_ground_truth.add_argument("ground_truth", type=Path)
    import_ground_truth.add_argument("--freeze-id", required=True)

    run_sealed = subparsers.add_parser(
        "run-sealed-tests",
        help="Run every frozen sealed cohort exactly once and record the official aggregate score first.",
    )
    run_sealed.add_argument("freeze_id")
    run_sealed.add_argument("--audiveris-bin", type=Path)
    run_sealed.add_argument("--vision-model", default="gemma4:12b")
    run_sealed.add_argument("--vision-base-url", default="http://127.0.0.1:11434")
    run_sealed.add_argument("--workers", type=int, default=1)

    release_sealed = subparsers.add_parser(
        "release-sealed-failures",
        help="Release page-level failures only after the official score, converting the holdout to regression data.",
    )
    release_sealed.add_argument("freeze_id")

    promote = subparsers.add_parser("promote", help="Promote an exact passing model after explicit creator approval.")
    promote.add_argument("model_id")
    promote.add_argument("--channel", choices=("beta", "stable"), required=True)
    promote.add_argument("--approval-reference", required=True)
    promote.add_argument("--lane15-handoff", type=Path)

    reject = subparsers.add_parser("reject", help="Retire a rejected inactive challenger.")
    reject.add_argument("model_id")
    reject.add_argument("--approval-reference", required=True)

    deactivate = subparsers.add_parser(
        "deactivate-channel",
        help="Clear an obsolete beta or stable channel and retain an audited rollback entry.",
    )
    deactivate.add_argument("--channel", choices=("beta", "stable"), required=True)
    deactivate.add_argument("--approval-reference", required=True)

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
    result: Any
    try:
        if args.command == "ingest":
            result = store.ingest(
                args.source,
                source_copedent_id=args.source_copedent,
                source_copedent_confidence=args.copedent_confidence,
                evidence_type=args.evidence_type,
                batch_id=args.batch_id,
                source_copedent_evidence=args.source_copedent_evidence,
            )
        elif args.command == "partition":
            result = store.prepare_partition(
                args.batch_id,
                document_breaks=args.document_break,
                forced_discovery=args.force_discovery,
                content_unit_breaks=args.content_unit_break,
                page_level_units=args.page_level_units,
                semantic_groups=args.semantic_groups,
                discovery_target=args.discovery_target,
                validation_target=args.validation_target,
                test_target=args.test_target,
                guard_radius=args.guard_radius,
                similarity_threshold=args.similarity_threshold,
            )
        elif args.command == "record-split-review":
            result = store.record_split_review(
                args.batch_id,
                outcome=args.outcome,
                partition_digest=args.partition_digest,
                reviewer_reference=args.reviewer_reference,
                review_artifact_digest=args.review_artifact_digest,
            )
        elif args.command == "supersede-batch":
            result = store.supersede_batch(
                args.batch_id,
                replacement_batch_id=args.replacement_batch,
                approval_reference=args.approval_reference,
            )
        elif args.command == "compose-dataset":
            result = store.compose_authoritative_dataset(
                args.batch,
                approval_reference=args.approval_reference,
            )
        elif args.command == "verify-intake":
            result = store.verify_batch_inputs(args.batch_id)
        elif args.command == "record-use-authorization":
            result = store.record_use_authorization(
                args.batch_id,
                rights_status=args.rights_status,
                allowed_uses=args.allow,
                approval_reference=args.approval_reference,
            )
        elif args.command == "extract":
            extractor = AmazingTablatureExtractor(
                args.root,
                audiveris_binary=args.audiveris_bin,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
                tab_reader=args.tab_reader,
            )
            result = extractor.run(
                args.batch_id,
                partition=args.partition,
                use_ocr=not args.no_ocr,
                use_omr=not args.no_omr,
                use_tab_vision=not args.no_tab_vision,
                resume=not args.no_resume,
                workers=args.workers,
                validation_model_id=args.validation_model_id,
            )
        elif args.command == "refresh-unreviewed-extraction":
            extractor = AmazingTablatureExtractor(
                args.root,
                audiveris_binary=args.audiveris_bin,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
                tab_reader=args.tab_reader,
            )
            result = extractor.refresh_unreviewed(
                args.batch_id,
                limit=args.limit,
                use_ocr=not args.no_ocr,
                use_omr=not args.no_omr,
                use_tab_vision=not args.no_tab_vision,
                resume=not args.no_resume,
                workers=args.workers,
                require_tab_systems=args.tab_pages_only,
            )
        elif args.command == "audit-discovery-completion":
            result = AmazingTablatureExtractor(args.root).audit_discovery_completion(
                args.batch_id
            )
        elif args.command == "quarantine-discovery-remainder":
            result = AmazingTablatureExtractor(args.root).quarantine_discovery_remainder(
                args.batch_id,
                approval_reference=args.approval_reference,
                confirm_bulk_quarantine=args.confirm_bulk_quarantine,
            )
        elif args.command == "remediate-discovery-score-correspondence":
            extractor = AmazingTablatureExtractor(
                args.root,
                audiveris_binary=args.audiveris_bin,
            )
            result = extractor.remediate_discovery_score_correspondence(
                args.batch_id,
                limit=args.limit,
                workers=args.workers,
            )
        elif args.command == "freeze-source-score-notehead-benchmark":
            result = AmazingTablatureExtractor(
                args.root
            ).freeze_source_score_notehead_benchmark(args.batch_id)
        elif args.command == "evaluate-source-score-notehead-challenger":
            result = AmazingTablatureExtractor(
                args.root
            ).evaluate_source_score_notehead_challenger(
                args.batch_id,
                subset=args.subset,
            )
        elif args.command == "evaluate-source-score-vision-regression":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).evaluate_source_score_vision_regression(
                args.batch_id,
                workers=args.workers,
                limit=args.limit,
                resume=not args.no_resume,
            )
        elif args.command == "build-discovery-score-sequence-dataset":
            result = AmazingTablatureExtractor(
                args.root
            ).build_discovery_score_sequence_dataset(args.batch_id)
        elif args.command == "train-discovery-score-sequence-challenger":
            dependency_root = args.dependency_root or (
                args.root / "trainer-deps" / "score-sequence-v1" / "site-packages"
            )
            result = AmazingTablatureExtractor(
                args.root
            ).train_discovery_score_sequence_challenger(
                args.batch_id,
                dependency_root=dependency_root,
                seed=args.seed,
                maximum_epochs=args.maximum_epochs,
            )
        elif args.command == "evaluate-discovery-guided-capture-regression":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).evaluate_discovery_guided_capture_regression(
                args.batch_id,
                limit=args.limit,
            )
        elif args.command == "evaluate-discovery-source-score-semantic-repair":
            result = AmazingTablatureExtractor(
                args.root
            ).evaluate_discovery_source_score_semantic_repair(args.batch_id)
        elif args.command == "evaluate-discovery-machine-score-tab-timeline":
            result = AmazingTablatureExtractor(
                args.root
            ).evaluate_discovery_machine_score_tab_timeline(args.batch_id)
        elif args.command == "evaluate-discovery-tab-row-geometry-challenger":
            result = AmazingTablatureExtractor(
                args.root
            ).evaluate_discovery_tab_row_geometry_challenger(args.batch_id)
        elif args.command == "freeze-discovery-tab-row-geometry-contract":
            result = AmazingTablatureExtractor(
                args.root
            ).freeze_discovery_tab_row_geometry_contract(args.batch_id)
        elif args.command == "evaluate-discovery-tab-action-recovery-challenger":
            result = AmazingTablatureExtractor(
                args.root,
                tab_reader=args.tab_reader,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).evaluate_discovery_tab_action_recovery_challenger(args.batch_id)
        elif args.command == "evaluate-source-score-projection-challenger":
            result = AmazingTablatureExtractor(
                args.root
            ).evaluate_source_score_projection_challenger(args.batch_id)
        elif args.command == "evaluate-source-score-component-hybrid-challenger":
            result = AmazingTablatureExtractor(
                args.root
            ).evaluate_source_score_component_hybrid_challenger(args.batch_id)
        elif args.command == "freeze-source-score-component-hybrid-contract":
            result = AmazingTablatureExtractor(
                args.root
            ).freeze_source_score_component_hybrid_contract(args.batch_id)
        elif args.command == "freeze-source-score-projection-contract":
            result = AmazingTablatureExtractor(
                args.root
            ).freeze_source_score_projection_contract(args.batch_id)
        elif args.command == "capture-source-score-projection-shadow":
            result = AmazingTablatureExtractor(
                args.root
            ).capture_source_score_projection_shadow(
                args.batch_id,
                limit=args.limit,
            )
        elif args.command == "score-source-score-projection-shadow":
            result = AmazingTablatureExtractor(
                args.root
            ).score_source_score_projection_shadow(
                args.batch_id,
                minimum_cases=args.minimum_cases,
            )
        elif args.command == "freeze-source-score-notehead-challenger-contract":
            result = AmazingTablatureExtractor(
                args.root
            ).freeze_source_score_notehead_challenger_contract(args.batch_id)
        elif args.command == "prepare-extraction-review":
            result = AmazingTablatureExtractor(args.root).prepare_review(
                args.batch_id,
                partition=args.partition,
                limit=args.limit,
                prior_feedback_only=args.feedback_corrections_only,
                never_reviewed_only=args.never_reviewed_only,
                current_extractor_only=args.current_extractor_only,
                tab_pages_only=args.tab_pages_only,
                passing_refresh_gate_only=args.passing_refresh_gate_only,
            )
        elif args.command == "serve-extraction-review":
            _print({"host": "127.0.0.1", "port": args.port, "status": "serving_private_review"})
            serve_review_consoles(args.root, port=args.port)
            return 0
        elif args.command == "apply-extraction-review":
            result = AmazingTablatureExtractor(args.root).apply_review(
                args.batch_id,
                args.decisions,
                partition=args.partition,
            )
        elif args.command == "prepare-score-audit-review":
            result = AmazingTablatureExtractor(args.root).prepare_score_audit_review(
                args.batch_id,
                partition=args.partition,
                limit=args.limit,
            )
        elif args.command == "repair-score-audit":
            result = AmazingTablatureExtractor(args.root).repair_score_audit(
                args.batch_id,
                partition=args.partition,
                workers=args.workers,
                limit=args.limit,
                input_ids=args.input_id,
            )
        elif args.command == "apply-score-audit-review":
            result = AmazingTablatureExtractor(args.root).apply_score_audit_review(
                args.batch_id,
                args.decisions,
                partition=args.partition,
            )
        elif args.command == "apply-score-audit-corrections":
            result = AmazingTablatureExtractor(args.root).apply_score_audit_corrections(
                args.batch_id,
                args.corrections,
                partition=args.partition,
                dry_run=args.dry_run,
            )
        elif args.command == "qualify-score-audit-scope":
            result = AmazingTablatureExtractor(args.root).qualify_score_audit_scope(
                args.batch_id,
                input_id=args.input_id,
                expected_score_audit_decision_id=args.expected_score_audit_decision_id,
                reviewer_reference=args.reviewer_reference,
                partition=args.partition,
            )
        elif args.command == "apply-feedback-corrections":
            result = AmazingTablatureExtractor(args.root).apply_feedback_corrections(
                args.batch_id,
                args.corrections,
                partition=args.partition,
                dry_run=args.dry_run,
            )
        elif args.command == "prepare-feedback-correction-confirmation":
            result = AmazingTablatureExtractor(
                args.root
            ).prepare_feedback_correction_confirmation(
                args.batch_id,
                args.corrections,
                partition=args.partition,
            )
        elif args.command == "apply-feedback-correction-confirmation-review":
            result = AmazingTablatureExtractor(
                args.root
            ).apply_feedback_correction_confirmation_review(
                args.batch_id,
                args.submission,
                partition=args.partition,
            )
        elif args.command == "prepare-combined-score-tab-review":
            key_signature_overrides = {}
            for value in args.key_signature_override:
                system_id, separator, fifths = str(value).partition("=")
                if not separator or not system_id or not re.fullmatch(r"-?[0-7]", fifths):
                    raise ValueError(
                        "Key-signature overrides must use SCORE_SYSTEM_ID=FIFTHS with -7..7."
                    )
                key_signature_overrides[system_id] = int(fifths)
            result = AmazingTablatureExtractor(args.root).prepare_combined_score_tab_review(
                args.batch_id,
                input_ids=args.input_id,
                score_system_ids=args.score_system_id,
                key_signature_overrides=key_signature_overrides,
                partition=args.partition,
                activate=not args.no_activate,
                provisional_joint_review=args.provisional_joint_review,
            )
        elif args.command == "prepare-validation-contact-consensus":
            extractor = AmazingTablatureExtractor(args.root)
            if args.reader_model:
                result = extractor.prepare_validation_contact_sheet_consensus(
                    args.batch_id,
                    reader_models=args.reader_model,
                )
            else:
                result = extractor.prepare_validation_contact_sheet_consensus(
                    args.batch_id,
                )
        elif args.command == "prepare-validation-line-audit":
            result = AmazingTablatureExtractor(args.root).prepare_validation_line_audit(
                args.batch_id,
                activate=not args.no_activate,
            )
        elif args.command == "prepare-canonical-validation-review":
            result = AmazingTablatureExtractor(
                args.root
            ).prepare_canonical_validation_dataset_review(
                args.batch_id,
                model_id=args.model_id,
                score_report_digest=args.score_report_digest,
            )
        elif args.command == "apply-canonical-validation-corrections":
            result = AmazingTablatureExtractor(
                args.root
            ).apply_canonical_validation_corrections(
                args.model_id,
                score_report_digest=args.score_report_digest,
                packet_digest=args.packet_digest,
                submission_id=args.submission_id,
                correction_plan=args.correction_plan,
            )
        elif (
            args.command
            == "apply-canonical-validation-followup-corrections"
        ):
            result = AmazingTablatureExtractor(
                args.root
            ).apply_canonical_validation_followup_corrections(
                args.model_id,
                correction_report_digest=(
                    args.correction_report_digest
                ),
                packet_digest=args.packet_digest,
                submission_id=args.submission_id,
                correction_plan=args.correction_plan,
            )
        elif args.command == "remediate-validation-machine-capture":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).remediate_validation_machine_capture(
                args.batch_id,
                input_ids=args.input_id,
                limit=args.limit,
                resume=not args.no_resume,
                apply=args.apply,
            )
        elif args.command == "apply-combined-score-tab-review":
            result = AmazingTablatureExtractor(args.root).apply_combined_score_tab_review(
                args.batch_id,
                args.submission,
                partition=args.partition,
                dry_run=args.dry_run,
            )
        elif args.command == "prepare-challenger-comparison-review":
            result = AmazingTablatureExtractor(
                args.root
            ).prepare_challenger_comparison_review(
                args.batch_id,
                model_id=args.model_id,
                report_digest=args.report_digest,
                input_ids=args.input_id,
                score_system_ids=args.score_system_id,
                max_decisions=args.max_decisions,
            )
        elif args.command == "prepare-validation-disagreement-review":
            result = AmazingTablatureExtractor(
                args.root
            ).prepare_validation_disagreement_review(
                args.batch_id,
                model_id=args.model_id,
                disagreement_digest=args.disagreement_digest,
            )
        elif args.command == "apply-challenger-comparison-review":
            result = AmazingTablatureTrainingStore(
                args.root
            ).apply_challenger_comparison_review(
                args.batch_id,
                args.submission,
                dry_run=args.dry_run,
            )
        elif args.command == "replay-combined-score-tab-regressions":
            result = AmazingTablatureExtractor(
                args.root
            ).replay_combined_score_tab_regressions(
                args.batch_id,
                partition=args.partition,
            )
        elif args.command == "quarantine-combined-score-tab-regressions":
            result = AmazingTablatureExtractor(
                args.root
            ).quarantine_combined_score_tab_contract_regressions(
                args.batch_id,
                partition=args.partition,
            )
        elif args.command == "revalidate-combined-score-tab-normalized-positions":
            result = AmazingTablatureExtractor(
                args.root
            ).revalidate_combined_score_tab_normalized_positions(
                args.batch_id,
                input_id=args.input_id,
                score_system_id=args.score_system_id,
                partition=args.partition,
            )
        elif args.command == "extraction-review-metrics":
            result = AmazingTablatureExtractor(args.root).review_metrics(
                args.batch_id,
                partition=args.partition,
            )
        elif args.command == "replay-event-count-exceptions":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).replay_event_count_exceptions(
                args.batch_id,
                resume=not args.no_resume,
            )
        elif args.command == "prepare-event-localization-review":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).prepare_event_localization_review(
                args.batch_id,
                resume=not args.no_resume,
            )
        elif args.command == "prepare-score-pitch-correspondence-review":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).prepare_score_pitch_correspondence_review(
                args.batch_id,
                resume=not args.no_resume,
            )
        elif args.command == "replay-score-chord-omission-gate":
            result = AmazingTablatureExtractor(args.root).replay_score_chord_omission_gate(
                args.batch_id,
            )
        elif args.command == "prepare-score-chord-omission-review":
            result = AmazingTablatureExtractor(args.root).prepare_score_chord_omission_review(
                args.batch_id,
            )
        elif args.command == "prepare-full-line-score-recapture-review":
            result = AmazingTablatureExtractor(
                args.root,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            ).prepare_full_line_score_recapture_review(
                args.batch_id,
                args.constraints,
                resume=not args.no_resume,
            )
        elif args.command == "apply-full-line-score-recapture-review":
            result = AmazingTablatureExtractor(args.root).apply_full_line_score_recapture_review(
                args.batch_id,
                args.submission,
                args.corrections,
                dry_run=args.dry_run,
            )
        elif args.command == "derive-reviewed-decisions":
            result = store.derive_reviewed_decisions(args.batch_id, partition=args.partition)
        elif args.command == "annotate":
            result = store.import_annotations(args.batch_id, args.annotations)
        elif args.command == "validate":
            result = store.validate(args.batch_id)
        elif args.command == "review":
            result = store.apply_review(args.batch_id, args.resolutions)
        elif args.command == "train":
            result = store.train(epochs=args.epochs, learning_rate=args.learning_rate)
        elif args.command == "train-discovery-challenger":
            result = store.train_discovery_challenger(
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                base_model_id=args.base_model_id,
                experimental_styles=args.experimental_style,
                average_weights=args.average_weights,
                base_weight_ratio=args.base_weight_ratio,
            )
        elif args.command == "train-complete-discovery":
            result = store.train_complete_discovery_challenger(
                base_model_id=args.base_model_id,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                average_weights=args.average_weights,
                base_weight_ratio=args.base_weight_ratio,
            )
        elif args.command == "build-discovery-transition-decoder":
            result = store.build_discovery_transition_decoder(args.batch_id)
        elif args.command == "build-discovery-glyph-decoder":
            result = store.build_discovery_glyph_decoder(args.batch_id)
        elif args.command == "build-discovery-reader-calibration":
            if args.reader_model:
                result = store.build_discovery_reader_calibration(
                    args.batch_id,
                    reader_models=args.reader_model,
                )
            else:
                result = store.build_discovery_reader_calibration(
                    args.batch_id,
                )
        elif args.command == "canonical-readiness":
            result = store.canonical_readiness(base_model_id=args.base_model_id)
        elif args.command == "shadow-test-discovery":
            result = store.shadow_test_discovery(
                args.model_id,
                max_review_lines=args.max_review_lines,
            )
        elif args.command == "evaluate":
            result = store.evaluate(args.model_id)
        elif args.command == "score-validation-line-audits":
            result = store.score_validation_line_audits(args.model_id)
        elif args.command == "score-validation-machine-candidates":
            result = store.score_validation_machine_candidates(args.model_id)
        elif args.command == "adjudicate-validation-machine-disagreements":
            result = store.adjudicate_validation_machine_disagreements(
                args.model_id,
                batch_id=args.batch_id,
                score_report_digest=args.score_report_digest,
                submission_id=args.submission_id,
            )
        elif args.command == "carry-forward-validation-adjudication":
            result = store.carry_forward_validation_machine_adjudication(
                args.model_id,
                score_report_digest=args.score_report_digest,
                source_adjudication_digest=(
                    args.source_adjudication_digest
                ),
                current_packet_digest=args.current_packet_digest,
            )
        elif args.command == "score-canonical-validation-review":
            result = store.score_canonical_validation_review(
                args.model_id,
                score_report_digest=args.score_report_digest,
                packet_digest=args.packet_digest,
                submission_id=args.submission_id,
                adjudication_digest=args.adjudication_digest,
                equivalence_digest=args.equivalence_digest,
            )
        elif args.command == "report":
            result = store.report(args.model_id)
        elif args.command == "freeze-rules":
            result = store.freeze_rules(args.model_id)
        elif args.command == "prepare-sealed-ground-truth":
            result = SealedTestCoordinator(args.root).prepare_ground_truth(
                args.batch_id,
                freeze_id=args.freeze_id,
            )
        elif args.command == "import-sealed-ground-truth":
            result = SealedTestCoordinator(args.root).import_ground_truth(
                args.batch_id,
                args.ground_truth,
                freeze_id=args.freeze_id,
            )
        elif args.command == "run-sealed-tests":
            sealed_extractor = AmazingTablatureExtractor(
                args.root,
                audiveris_binary=args.audiveris_bin,
                vision_model=args.vision_model,
                vision_base_url=args.vision_base_url,
            )
            result = SealedTestCoordinator(args.root, extractor=sealed_extractor).run(
                args.freeze_id,
                workers=args.workers,
            )
        elif args.command == "release-sealed-failures":
            result = SealedTestCoordinator(args.root).release_failure_details(args.freeze_id)
        elif args.command == "promote":
            result = store.promote(
                args.model_id,
                channel=args.channel,
                approval_reference=args.approval_reference,
                lane15_handoff=args.lane15_handoff,
            )
        elif args.command == "reject":
            result = store.reject(args.model_id, approval_reference=args.approval_reference)
        elif args.command == "deactivate-channel":
            result = store.deactivate_channel(
                channel=args.channel,
                approval_reference=args.approval_reference,
            )
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
    except (ExtractionWorkflowError, SealedTestWorkflowError, TrainingWorkflowError) as exc:
        parser.exit(2, f"Amazing Tablature workflow stopped: {exc}\n")
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
