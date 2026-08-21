from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from steel_guitar_rag.chord_reader import bar_examples
from steel_guitar_rag.chord_reader import bar_uncertainty
from steel_guitar_rag.chord_reader import beat_cell_examples as examples
from steel_guitar_rag.chord_reader import beat_cell_stage1 as stage1
from steel_guitar_rag.chord_reader import beat_cell_stage2_contract as stage2_contract
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.beat_cell_stage2_contract import (
    BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256,
    BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256,
    BEAT_CELL_STAGE2_OUTPUT_PATHS,
    BEAT_CELL_STAGE_A_PROJECTION_SHA256,
    BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    load_beat_cell_stage2_authority,
)

from test_chord_reader_bar_uncertainty import _prediction
from test_chord_reader_beat_cell_stage1 import (
    _beat_track,
    _install_synthetic_beat_contract,
    _receipt,
    _synthetic_valid_artifact,
)


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _render(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _rehash(value: dict[str, Any], field: str) -> None:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})


def _synthetic_stage_a(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    track = _beat_track("track-1")
    receipt, receipt_file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, receipt_file_sha256)
    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=receipt_file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )
    prediction = _prediction(
        2.0,
        [{"start": 0.0, "end": 2.0, "label": "C", "productLabel": "C"}],
    )
    raw_sha256 = hashlib.sha256(_render(prediction)).hexdigest()
    identity = stage1._prediction_identity(
        {
            "id": "track-1",
            "split": "development",
            "predictionFile": "predictions/track-1.json",
            "predictionSha256": raw_sha256,
            "predictionCoreSha256": prediction["predictionCoreSha256"],
            "uncertaintySha256": prediction["uncertaintySha256"],
            "sourceAudioSha256": _digest("source-audio"),
            "cachedFeatureArraySha256": _digest("cached-features"),
            "freshFeatureArraySha256": _digest("fresh-features"),
            "canonicalDurationMilliseconds": 2000,
            "audioLineageRowSha256": _digest("audio-lineage-row"),
        }
    )
    validation_audit = stage1._self_hashed(
        {
            "schemaVersion": "chord_runtime_beat_cell_prediction_validation_audit_v1",
            "trackId": "track-1",
            "predictionCoreSha256": prediction["predictionCoreSha256"],
            "uncertaintySha256": prediction["uncertaintySha256"],
        },
        "auditSha256",
    )
    prediction_summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=validation_audit["auditSha256"],
    )
    sidecar = stage1._self_hashed(
        {
            "schemaVersion": stage1.CELL_SUMMARY_SCHEMA,
            "split": "development",
            "developmentOnly": True,
            "promotionEligible": False,
            "referenceFree": True,
            "trackId": "track-1",
            "predictionIdentity": identity,
            "predictionIdentitySha256": identity["predictionIdentitySha256"],
            "sourceRuntimeTrackArtifactSha256": _digest("runtime-track"),
            "sourceBeatReceiptTrack": track,
            "sourceBeatReceiptTrackSha256": track["trackReceiptSha256"],
            "sourceAudioLineageRowSha256": identity["audioLineageRowSha256"],
            "constructionPolicySha256": stage1.CONSTRUCTION_POLICY_SHA256,
            "scoringPolicySha256": stage1.SCORING_POLICY_SHA256,
            "construction": construction,
            "constructionSha256": construction["constructionSha256"],
            "derivedCellTiming": derived,
            "derivedCellTimingContractSha256": derived["contractSha256"],
            "predictionValidationAudit": validation_audit,
            "predictionValidationAuditSha256": validation_audit["auditSha256"],
            "predictionSummary": prediction_summary,
            "predictionSummarySha256": prediction_summary["summarySha256"],
        },
        "artifactSha256",
    )
    feature_summary = examples.build_beat_cell_feature_summary(
        sidecar,
        prediction,
        prediction_file_sha256=raw_sha256,
    )
    manifest = examples.build_beat_cell_feature_set_manifest(
        [feature_summary],
        summary_output_root=Path("/synthetic/features"),
        source_stage1_report_path=Path("/synthetic/stage1.json"),
        source_stage1_report_file_sha256=_digest("stage1-file"),
        source_stage1_summary_artifact_set_sha256=canonical_sha256(
            [{"trackId": "track-1", "artifactSha256": sidecar["artifactSha256"]}]
        ),
        source_stage1_summary_file_set_sha256=_digest("sidecar-file-set"),
    )
    return sidecar, prediction, feature_summary, manifest


def _zero_funnel() -> dict[str, Any]:
    zeros = {field: 0 for field in stage1._FUNNEL_FIELDS}
    return stage1.make_funnel(zeros, zeros)


def _stratum(dataset_id: str, funnel: dict[str, Any]) -> dict[str, Any]:
    return stage1._self_hashed(
        {
            "datasetId": dataset_id,
            "trackCount": 0 if funnel["counts"]["T"] == 0 else 1,
            "funnel": funnel,
            "funnelSha256": funnel["funnelSha256"],
        },
        "rowSha256",
    )


def _fake_stage1(
    sidecar: dict[str, Any],
    feature_summary: dict[str, Any],
    classifications: tuple[str, str],
) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    for feature, classification in zip(feature_summary["rows"], classifications, strict=True):
        outcomes.append(
            stage1._self_hashed(
                {
                    "cellIndex": feature["cellIndex"],
                    "sourceBeatCellSha256": feature["sourceBeatCellSha256"],
                    "durationMilliseconds": feature["durationMilliseconds"],
                    "predictionProduct": feature["predictionProduct"],
                    "predictionCoverage": feature["predictionCoverage"],
                    "predictionDominance": feature["predictionDominance"],
                    "classification": classification,
                    "reason": {
                        "U": "referenceUncovered",
                        "N": "predictionMixed",
                    }.get(classification),
                },
                "rowSha256",
            )
        )
    aggregate, _exclusions = stage1.funnel_from_outcomes(outcomes)
    zero = _zero_funnel()
    dataset_rows = [
        _stratum(dataset_id, aggregate if dataset_id == "aam" else zero)
        for dataset_id in bar_examples.LABEL_DETERMINACY_DATASET_IDS
    ]
    role_rows = [
        stage1._self_hashed(
            {
                "guitarsetRole": role,
                "trackCount": 0,
                "funnel": zero,
                "funnelSha256": zero["funnelSha256"],
            },
            "rowSha256",
        )
        for role in ("comp", "solo")
    ]
    decision = stage1._self_hashed(
        {
            "stage1Passed": True,
            "selectorStageMayRunInNewSealedDevelopmentCycle": True,
        },
        "decisionSha256",
    )
    track = {
        "trackId": "track-1",
        "datasetId": "aam",
        "role": "aam:mix:track-1",
        "guitarsetRole": None,
        "confidenceGroupId": "composition:track-1",
        "sourceGroupTrackMetadataSha256": _digest("group-row"),
        "predictionIdentity": deepcopy(sidecar["predictionIdentity"]),
        "predictionIdentitySha256": sidecar["predictionIdentitySha256"],
        "predictionOnlySummary": {"artifactSha256": sidecar["artifactSha256"]},
        "constructionSha256": sidecar["constructionSha256"],
        "cellOutcomes": outcomes,
    }
    reference_audit = bar_examples._reference_endpoint_reconciliation_audit(
        [],
        {"track-1": {"trackId": "track-1", "datasetId": "aam"}},
    )
    payload = {
        "tracks": [track],
        "datasets": dataset_rows,
        "aggregate": aggregate,
        "guitarset": {
            "funnel": zero,
            "funnelSha256": zero["funnelSha256"],
            "compSolo": role_rows,
        },
        "decision": decision,
        "stage1Passed": True,
        "gateSetSha256": _digest("gate-set"),
        "trackSetSha256": canonical_sha256([track]),
        "sourceContractSha256": _digest("source-contract"),
        "referenceEndpointReconciliationAudit": reference_audit,
        "referenceEndpointReconciliationAuditSha256": reference_audit["auditSha256"],
    }
    return stage1._self_hashed(payload, "artifactSha256")


def _minimal_examples_artifact(
    monkeypatch: pytest.MonkeyPatch,
    *,
    classifications: tuple[str, str] = ("C", "I"),
) -> dict[str, Any]:
    """Reusable synthetic artifact for selector/readiness integration tests."""

    sidecar, prediction, feature_summary, manifest = _synthetic_stage_a(monkeypatch)
    stage1_artifact = _fake_stage1(sidecar, feature_summary, classifications)
    monkeypatch.setattr(
        stage1,
        "validate_beat_cell_stage1_artifact",
        lambda value: deepcopy(dict(value)),
    )
    return examples.build_beat_cell_examples(
        stage1_artifact,
        manifest,
        [feature_summary],
        stage1_sidecars={"track-1": sidecar},
        predictions={"track-1": prediction},
        prediction_file_sha256s={"track-1": sidecar["predictionIdentity"]["predictionSha256"]},
        source_stage1_file_sha256=manifest["sourceStage1ReportFileSha256"],
        source_stage1_canonical_sha256=canonical_sha256(stage1_artifact),
        source_feature_set_file_sha256=hashlib.sha256(_render(manifest)).hexdigest(),
    )


def _hu33_product_reconciliation() -> dict[str, Any]:
    return {
        "trackId": "winterreise-schubert_d911-20_hu33",
        "cellIndex": 75,
        "startMilliseconds": 50852,
        "endMilliseconds": 51548,
        "sourceBeatCellSha256": "a3739deae1523c937dd7d6cf0cf6de1b90285b5fa58c4572fde9c64ba714bf1b",
        "featureProduct": "C7",
        "stage1Product": "Fm",
        "featureCoverage": 1.0,
        "stage1Coverage": 1.0,
        "featureDominance": 0.49999999999999856,
        "stage1Dominance": 0.5000000000000088,
        "candidateProducts": ["C7", "Fm"],
        "overlapSecondsByProduct": {
            "C7": 0.347999999999999,
            "Fm": 0.3480000000000061,
        },
    }


def _install_product_reconciliation_authority(
    monkeypatch: pytest.MonkeyPatch,
    expected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = sorted(
        deepcopy(expected_rows),
        key=lambda row: (str(row["trackId"]), int(row["cellIndex"])),
    )
    stage_b_fields = [
        "trackId",
        "cellIndex",
        "startMilliseconds",
        "endMilliseconds",
        "sourceBeatCellSha256",
        "featureProduct",
        "stage1Product",
        "featureCoverage",
        "stage1Coverage",
        "featureDominance",
        "stage1Dominance",
    ]
    stage_b_rows = [{field: row[field] for field in stage_b_fields} for row in rows]
    source_inputs = examples.BEAT_CELL_STAGE2_SOURCE_INPUTS
    sweep = {
        "schemaVersion": "chord_runtime_beat_cell_stage2_product_reconciliation_sweep_v1",
        "labelBlind": True,
        "trackCount": source_inputs["trackCount"],
        "cellCount": source_inputs["cellCount"],
        "tolerantWinnerStage1ProductMismatchCount": len(rows),
        "coverageMismatchCountAtAbsoluteTolerance1e-9": 0,
        "dominanceMismatchCountAtAbsoluteTolerance1e-9": 0,
        "expectedReconciliationCount": len(rows),
        "unexpectedReconciliationCount": 0,
        "stage1SummaryArtifactSetSha256": source_inputs["stage1SummaryArtifactSet"]["sha256"],
        "stage1SummaryFileSetSha256": source_inputs["stage1SummaryFileSet"]["sha256"],
        "predictionIdentitySetSha256": source_inputs["predictionIdentitySetSha256"],
    }
    post_freeze_preflight = {
        "schemaVersion": "chord_runtime_beat_cell_stage2_post_freeze_label_blind_preflight_v1",
        "authorization": "exactly-two-deterministic-in-memory-committed-production-builder-runs-only",
        "authorizedRunCount": 2,
        "executionPhase": (
            "only-after-R3-authority-and-corrected-production-code-are-committed-at-one-clean-HEAD-and-all-"
            "authority-source-hashes-are-final"
        ),
        "productionBuilder": {
            "module": "steel_guitar_rag/chord_reader/beat_cell_examples.py",
            "callable": "build_beat_cell_feature_summary",
            "exactCommittedModuleBytesRequired": True,
            "moduleFileSha256Source": "featureMath.sourceStageAImplementationModuleFileSha256",
            "officialRunnerOrCliAllowed": False,
        },
        "inventoryPerRun": {
            "trackCount": source_inputs["trackCount"],
            "cellCount": source_inputs["cellCount"],
            "featureSummaryCount": source_inputs["trackCount"],
            "featureRowCount": source_inputs["cellCount"],
            "stage1SummaryArtifactSetSha256": source_inputs["stage1SummaryArtifactSet"]["sha256"],
            "stage1SummaryFileSetSha256": source_inputs["stage1SummaryFileSet"]["sha256"],
            "predictionIdentitySetSha256": source_inputs["predictionIdentitySetSha256"],
        },
        "inputSnapshotBoundary": {
            "beforeEachRun": "synthetic exact pre-run snapshot",
            "afterEachRun": "synthetic exact post-run snapshot",
            "stage1ReportHandling": "opaque raw bytes/hash/stat only; no JSON parse or traversal",
            "nofollowSealedReadsRequired": True,
            "fullDirectAndTransitiveStageAInputInventoryRequired": True,
            "anyByteInodeRootOrPathDelta": "block-preflight-and-authorize-no-official-invocation",
        },
        "requiredInMemoryResultsPerRun": {
            "exactReconciliationCount": len(rows),
            "exactReconciliationRowSetSha256": canonical_sha256(rows),
            "unexpectedReconciliationCount": 0,
            "allFeatureSummariesAndRowsValidate": True,
            "runOneAndRunTwoCanonicalSummaryInventoryEqual": True,
        },
        "deltaPolicy": {
            "anyInputDelta": "block",
            "anyBuilderException": "block",
            "anySummaryOrRowValidationDelta": "block",
            "anyRunOneRunTwoCanonicalDelta": "block",
            "anyReconciliationCountOrSetDelta": "block",
            "anyForbiddenOperation": "block",
        },
        "forbiddenOperationCounts": {
            "officialCliInvocations": 0,
            "officialRunnerInvocations": 0,
            "stage1ReportJsonParses": 0,
            "stage1OutcomeObjectAccesses": 0,
            "referenceOrGroupObjectAccesses": 0,
            "temporaryDirectoriesCreated": 0,
            "outputPathsCreated": 0,
            "publicationCalls": 0,
            "examplesBuilt": 0,
            "selectorFits": 0,
            "readinessEvaluationsOrFits": 0,
            "calibrationTestConfirmationPlayerPublicSongTravisAccesses": 0,
        },
        "oneShotConsumption": {
            "consumesOfficialInvocation": False,
            "consumesR3OneShot": False,
            "reason": "synthetic preflight is non-consuming",
        },
    }
    governance_incident = {
        "schemaVersion": "chord_runtime_beat_cell_stage2_precommit_governance_incident_v1",
        "phase": "pre-commit-docs-audit-before-R3-authority-and-production-code-freeze",
        "docsAuditStage1ReportJsonLoadsCount": 1,
        "canonicalTraversalCount": 1,
        "canonicalTraversalPurpose": "whole-object canonical receipt verification only",
        "topReceiptPrints": "occurred-before-the-funnel-attempt",
        "attemptedPath": "aggregate.funnel.counts (failed at aggregate.funnel before any duration expression evaluated)",
        "terminalError": "KeyError('funnel')",
        "terminalErrorOccurredBeforeAttemptedPathOutput": True,
        "numericOrProtectedSemanticValuesEmittedCount": 0,
        "numericOrProtectedSemanticValuesRetainedCount": 0,
        "indexedProtectedCollections": {
            "tracks": 0,
            "outcomes": 0,
            "classifications": 0,
            "references": 0,
            "groups": 0,
            "datasets": 0,
        },
        "decisionIndependence": {
            "tolerantWinnerReconciliationPolicySelectedBeforeIncident": True,
            "usedAsDecisionInput": False,
            "changedPolicyOrExpectedInventory": False,
        },
        "postIncidentParseCounts": {
            "furtherDocsAuditStage1ReportJsonParses": 0,
            "officialStage1ReportJsonParses": 0,
            "authorizedPostFreezePreflightStage1ReportJsonParses": 0,
        },
        "retention": {
            "parsedStage1ObjectRetained": False,
            "derivedNumericOrProtectedSemanticValueRetained": False,
            "funnelResultRetained": False,
        },
        "authorizationEffect": (
            "disclosure-only; authorizes no protected access and does not consume or expand the R3 one-shot"
        ),
    }
    policy = {
        "schemaVersion": "chord_runtime_beat_cell_stage2_product_reconciliation_v1",
        "sourceStage1ScoringPolicySha256": stage1.SCORING_POLICY_SHA256,
        "predecessorFailure": {"cycle": "synthetic-test"},
        "rule": "synthetic exact tolerant-winner reconciliation authority",
        "structuralIneligibility": {
            "comparisonEpsilon": stage1.SCORING_POLICY["comparisonEpsilon"],
            "expectedStage1Result": True,
            "expectedStageAResult": True,
            "formula": (
                "predictionProduct is null or predictionCoverage+comparisonEpsilon<predictionCoverageMinimum "
                "or predictionDominance+comparisonEpsilon<predictionDominanceMinimum"
            ),
            "predictionCoverageMinimum": stage1.SCORING_POLICY["predictionCoverage"],
            "predictionDominanceMinimum": stage1.SCORING_POLICY["predictionDominance"],
            "stage1Required": True,
            "stageARequired": True,
        },
        "expectedCount": len(rows),
        "expectedRows": rows,
        "expectedRowSetSha256": canonical_sha256(rows),
        "forbiddenDecisionInputs": [],
        "labelBlindSweep": sweep,
        "labelBlindSweepSha256": canonical_sha256(sweep),
        "postFreezeLabelBlindPreflight": post_freeze_preflight,
        "preCommitGovernanceIncidentDisclosure": governance_incident,
        "stageBAdmission": {
            "exactReconciliationProjectionFields": stage_b_fields,
            "expectedReconciliationProjectionCount": len(stage_b_rows),
            "expectedReconciliationProjectionSetSha256": canonical_sha256(stage_b_rows),
            "requiredOutcomeClassificationSet": ["U", "N"],
            "exampleEmissionAllowed": False,
            "expectedExampleEmissionCount": 0,
            "classificationMayChangeStageA": False,
            "classificationAccessPhase": (
                "StageB-only-after-complete-StageA-publication-and-independent-label-blind-audit"
            ),
            "allOtherProductMismatches": "fail-closed",
        },
    }
    projection = deepcopy(examples.BEAT_CELL_FEATURE_MATH_PROJECTION)
    projection["sourceStage1ScoringPolicySha256"] = stage1.SCORING_POLICY_SHA256
    projection["stage1ProductReconciliation"] = policy
    monkeypatch.setattr(examples, "BEAT_CELL_FEATURE_MATH_PROJECTION", projection)
    return policy


def _real_shape_hu33_stage_a_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    track_id = "winterreise-schubert_d911-20_hu33"
    cells = [
        {
            "beatIndex": 0,
            "retainedBarIndex": 0,
            "pulseNumber": 1,
            "downbeatCandidate": True,
            "startMs": 50852,
            "endMs": 51548,
            "durationMilliseconds": 696,
        },
        {
            "beatIndex": 1,
            "retainedBarIndex": 0,
            "pulseNumber": 2,
            "downbeatCandidate": False,
            "startMs": 51548,
            "endMs": 52200,
            "durationMilliseconds": 652,
        },
    ]
    track = _beat_track(track_id)
    track_payload = {key: value for key, value in track.items() if key != "trackReceiptSha256"}
    track_payload.update(
        {
            "durationMilliseconds": 52200,
            "prefixExcludedMilliseconds": 50852,
            "coveredDurationMilliseconds": 1348,
            "beatCount": 2,
            "beatTimesMs": [50852, 51548],
            "barStartsMs": [50852],
            "beatsPerBar": 2,
            "beatCells": cells,
        }
    )
    track_payload["topologySha256"] = canonical_sha256(
        {
            "beatTimesMs": track_payload["beatTimesMs"],
            "barStartsMs": track_payload["barStartsMs"],
            "durationMilliseconds": track_payload["durationMilliseconds"],
            "beatsPerBar": track_payload["beatsPerBar"],
            "beatCells": track_payload["beatCells"],
        }
    )
    track = {**track_payload, "trackReceiptSha256": canonical_sha256(track_payload)}
    receipt, receipt_file_sha256 = _receipt([track])
    _install_synthetic_beat_contract(monkeypatch, receipt, receipt_file_sha256)
    construction, derived = stage1.construct_beat_cells(
        track,
        source_beat_receipt_file_sha256=receipt_file_sha256,
        source_beat_receipt_sha256=receipt["receiptSha256"],
    )
    prediction = _prediction(
        52.2,
        [
            {"start": 46.6, "end": 51.2, "label": "Fm", "productLabel": "Fm"},
            {"start": 51.2, "end": 52.2, "label": "C7", "productLabel": "C7"},
        ],
        id=track_id,
    )
    raw_sha256 = hashlib.sha256(_render(prediction)).hexdigest()
    identity = stage1._prediction_identity(
        {
            "id": track_id,
            "split": "development",
            "predictionFile": f"predictions/{track_id}.json",
            "predictionSha256": raw_sha256,
            "predictionCoreSha256": prediction["predictionCoreSha256"],
            "uncertaintySha256": prediction["uncertaintySha256"],
            "sourceAudioSha256": _digest("hu33-source-audio"),
            "cachedFeatureArraySha256": _digest("hu33-cached-features"),
            "freshFeatureArraySha256": _digest("hu33-fresh-features"),
            "canonicalDurationMilliseconds": 52200,
            "audioLineageRowSha256": _digest("hu33-audio-lineage-row"),
        }
    )
    validation_audit = stage1._self_hashed(
        {
            "schemaVersion": "chord_runtime_beat_cell_prediction_validation_audit_v1",
            "trackId": track_id,
            "predictionCoreSha256": prediction["predictionCoreSha256"],
            "uncertaintySha256": prediction["uncertaintySha256"],
        },
        "auditSha256",
    )
    prediction_summary = stage1.summarize_prediction_cells(
        prediction,
        construction,
        derived,
        prediction_validation_audit_sha256=validation_audit["auditSha256"],
    )
    sidecar = stage1._self_hashed(
        {
            "schemaVersion": stage1.CELL_SUMMARY_SCHEMA,
            "split": "development",
            "developmentOnly": True,
            "promotionEligible": False,
            "referenceFree": True,
            "trackId": track_id,
            "predictionIdentity": identity,
            "predictionIdentitySha256": identity["predictionIdentitySha256"],
            "sourceRuntimeTrackArtifactSha256": _digest("hu33-runtime-track"),
            "sourceBeatReceiptTrack": track,
            "sourceBeatReceiptTrackSha256": track["trackReceiptSha256"],
            "sourceAudioLineageRowSha256": identity["audioLineageRowSha256"],
            "constructionPolicySha256": stage1.CONSTRUCTION_POLICY_SHA256,
            "scoringPolicySha256": stage1.SCORING_POLICY_SHA256,
            "construction": construction,
            "constructionSha256": construction["constructionSha256"],
            "derivedCellTiming": derived,
            "derivedCellTimingContractSha256": derived["contractSha256"],
            "predictionValidationAudit": validation_audit,
            "predictionValidationAuditSha256": validation_audit["auditSha256"],
            "predictionSummary": prediction_summary,
            "predictionSummarySha256": prediction_summary["summarySha256"],
        },
        "artifactSha256",
    )
    expected_reconciliation = {
        "trackId": track_id,
        "cellIndex": 0,
        "startMilliseconds": 50852,
        "endMilliseconds": 51548,
        "sourceBeatCellSha256": canonical_sha256(cells[0]),
        "featureProduct": "C7",
        "stage1Product": "Fm",
        "featureCoverage": 1.0,
        "stage1Coverage": 1.0,
        "featureDominance": 0.49999999999999856,
        "stage1Dominance": 0.5000000000000088,
        "candidateProducts": ["C7", "Fm"],
        "overlapSecondsByProduct": {
            "C7": 0.347999999999999,
            "Fm": 0.3480000000000061,
        },
    }
    return sidecar, prediction, raw_sha256, expected_reconciliation


def test_committed_authority_loader_and_projections_are_exact() -> None:
    authority = load_beat_cell_stage2_authority()
    assert canonical_sha256(authority) == BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256
    assert BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256 == (
        "c738861f164022ce558258b2ecad4ebcbe707394750fe4bdc9cb97df5cd3e305"
    )
    assert BEAT_CELL_STAGE_A_PROJECTION_SHA256 == ("814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688")
    assert BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256 == (
        "0735dc64d064f227bf4fcdd698ef1ff16644fbb31e261e7a057c5f021e693602"
    )
    assert BEAT_CELL_STAGE_B_PROJECTION_SHA256 == ("ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32")
    assert set(BEAT_CELL_STAGE2_OUTPUT_PATHS) == {
        "featureSetManifest",
        "featureSummaryRoot",
        "examplesArtifact",
        "selectorArtifact",
        "readinessReport",
        "publication",
    }
    assert all(
        "/beat-cell-stage2-r3/" in value
        for name, value in BEAT_CELL_STAGE2_OUTPUT_PATHS.items()
        if name != "publication"
    )


@pytest.mark.parametrize(
    ("tamper", "message"),
    (
        ("missing-path", "bind the exact Stage-A implementation source"),
        ("missing-hash", "bind the exact Stage-A implementation source"),
        ("missing-both", "bind the exact Stage-A implementation source"),
        ("stale-hash", "file hash is stale"),
        ("nonmatching-module", "file hash is stale"),
    ),
)
def test_r3_stage_a_source_module_binding_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
    message: str,
) -> None:
    authority = load_beat_cell_stage2_authority()
    feature_math = authority["featureMath"]
    feature_math.setdefault("stage1ProductReconciliation", {})
    relative_path = "steel_guitar_rag/chord_reader/beat_cell_examples.py"
    source_path = Path(stage2_contract.__file__).resolve().parents[2] / relative_path
    feature_math["sourceStageAImplementationModule"] = relative_path
    feature_math["sourceStageAImplementationModuleFileSha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest()

    def bind_expected_hashes(value: dict[str, Any]) -> None:
        projection_hashes = deepcopy(stage2_contract._PROJECTION_HASHES)
        projection_hashes["featureMath"] = canonical_sha256(value["featureMath"])
        monkeypatch.setattr(stage2_contract, "_PROJECTION_HASHES", projection_hashes)
        monkeypatch.setattr(
            stage2_contract,
            "BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256",
            canonical_sha256(value),
        )

    bind_expected_hashes(authority)
    assert stage2_contract.validate_beat_cell_stage2_authority(authority) == authority

    if tamper == "missing-path":
        feature_math.pop("sourceStageAImplementationModule")
    elif tamper == "missing-hash":
        feature_math.pop("sourceStageAImplementationModuleFileSha256")
    elif tamper == "missing-both":
        feature_math.pop("sourceStageAImplementationModule")
        feature_math.pop("sourceStageAImplementationModuleFileSha256")
    elif tamper == "stale-hash":
        feature_math["sourceStageAImplementationModuleFileSha256"] = _digest("stale-stage-a-source")
    else:
        feature_math["sourceStageAImplementationModule"] = "steel_guitar_rag/chord_reader/beat_cell_stage1.py"
    bind_expected_hashes(authority)

    with pytest.raises(stage2_contract.BeatCellStage2ContractError, match=message):
        stage2_contract.validate_beat_cell_stage2_authority(authority)


def test_full_synthetic_stage1_still_passes_public_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_valid_artifact(monkeypatch)
    assert stage1.validate_beat_cell_stage1_artifact(artifact) == artifact


def test_stage_a_feature_math_and_complete_stage1_cross_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, prediction, summary, manifest = _synthetic_stage_a(monkeypatch)
    assert summary["featureNames"] == list(bar_uncertainty.BAR_FEATURE_NAMES)
    assert len(summary["rows"]) == 2
    assert summary["rows"][0]["predictionProduct"] == "C"
    assert summary["rows"][0]["featureValues"]["predictionCoverage"] == 1.0
    validated_manifest, validated = examples.validate_beat_cell_feature_set_semantics(
        manifest,
        [summary],
        stage1_sidecars={"track-1": sidecar},
        predictions={"track-1": prediction},
        prediction_file_sha256s={"track-1": sidecar["predictionIdentity"]["predictionSha256"]},
    )
    assert validated_manifest == manifest
    assert validated == [summary]


def test_exact_hu33_tolerant_winner_reconciliation_matches_authority_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reconciliation = _hu33_product_reconciliation()
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])

    assert canonical_sha256(reconciliation) == "1ad9846a2f084e3aba4f22f75223b43865dd84782ca7fa1e8901b10e6e91d9ba"
    assert canonical_sha256([reconciliation]) == "964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d"
    assert examples._winner_candidates(reconciliation["overlapSecondsByProduct"]) == ("C7", "Fm")
    assert examples._winner(reconciliation["overlapSecondsByProduct"])[0] == "C7"
    assert examples._reconcile_stage1_product(reconciliation) == reconciliation
    assert examples._validate_product_reconciliation_inventory([reconciliation]) == [reconciliation]


def test_public_feature_builder_collects_exact_real_shape_hu33_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, prediction, raw_sha256, reconciliation = _real_shape_hu33_stage_a_inputs(monkeypatch)
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])
    collected: list[dict[str, Any]] = []

    summary = examples.build_beat_cell_feature_summary(
        sidecar,
        prediction,
        prediction_file_sha256=raw_sha256,
        product_reconciliations=collected,
    )

    assert sidecar["predictionSummary"]["cells"][0]["predictionProduct"] == "Fm"
    assert summary["rows"][0]["startMilliseconds"] == 50852
    assert summary["rows"][0]["endMilliseconds"] == 51548
    assert summary["rows"][0]["predictionProduct"] == "C7"
    assert collected == [reconciliation]
    assert examples._validate_product_reconciliation_inventory(
        collected,
        track_ids={reconciliation["trackId"]},
    ) == [reconciliation]


def test_tolerant_winner_candidate_boundary_is_closed_at_exactly_one_e_minus_nine() -> None:
    epsilon = examples._EPSILON
    maximum = 2 * epsilon
    contender_at_boundary = epsilon
    contender_just_inside = math.nextafter(contender_at_boundary, math.inf)
    contender_just_outside = math.nextafter(contender_at_boundary, 0.0)
    assert maximum - contender_just_inside < epsilon
    assert maximum - contender_at_boundary == epsilon
    assert maximum - contender_just_outside > epsilon

    assert examples._winner_candidates({"A": contender_just_inside, "B": maximum}) == ("A", "B")
    assert examples._winner_candidates({"A": contender_at_boundary, "B": maximum}) == ("A", "B")
    assert examples._winner_candidates({"A": contender_just_outside, "B": maximum}) == ("B",)
    assert examples._winner({"A": contender_at_boundary, "B": maximum}) == (
        "A",
        contender_at_boundary,
    )


def test_multi_piece_fsum_overlap_can_form_a_three_way_tolerant_tie() -> None:
    segments = [
        {"start": 0.0, "end": 0.1, "product": "C"},
        {"start": 0.1, "end": 0.4, "product": "C7"},
        {"start": 0.4, "end": 0.6, "product": "C"},
        {"start": 0.6, "end": 0.75, "product": "Fm"},
        {"start": 0.75, "end": 0.9, "product": "Fm"},
    ]

    overlaps, covered, sequence = bar_uncertainty._overlap_by_product(segments, 0.0, 0.9)

    assert overlaps == {
        "C": math.fsum([0.1, 0.6 - 0.4]),
        "C7": 0.4 - 0.1,
        "Fm": math.fsum([0.75 - 0.6, 0.9 - 0.75]),
    }
    assert covered == math.fsum([0.1, 0.4 - 0.1, 0.6 - 0.4, 0.75 - 0.6, 0.9 - 0.75])
    assert sequence == ["C", "C7", "C", "Fm"]
    assert examples._winner_candidates(overlaps) == ("C", "C7", "Fm")
    assert examples._winner(overlaps)[0] == "C"


@pytest.mark.parametrize(
    "tamper",
    (
        "structural-threshold",
        "top-level-scoring-policy",
        "sweep-hash",
        "sweep-count-coherently-resealed",
        "preflight-authorized-run-count",
        "preflight-one-shot-consumption",
        "preflight-forbidden-operation-count",
        "incident-parse-count",
        "incident-decision-input",
        "incident-retention",
        "stage-b-classification",
        "stage-b-projection-hash",
    ),
)
def test_complete_product_reconciliation_policy_tamper_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
) -> None:
    policy = _install_product_reconciliation_authority(monkeypatch, [_hu33_product_reconciliation()])
    if tamper == "structural-threshold":
        policy["structuralIneligibility"]["predictionDominanceMinimum"] = 0.74
    elif tamper == "top-level-scoring-policy":
        examples.BEAT_CELL_FEATURE_MATH_PROJECTION["sourceStage1ScoringPolicySha256"] = _digest("stale-scoring-policy")
    elif tamper == "sweep-hash":
        policy["labelBlindSweepSha256"] = _digest("stale-sweep")
    elif tamper == "sweep-count-coherently-resealed":
        policy["labelBlindSweep"]["cellCount"] += 1
        policy["labelBlindSweepSha256"] = canonical_sha256(policy["labelBlindSweep"])
    elif tamper == "preflight-authorized-run-count":
        policy["postFreezeLabelBlindPreflight"]["authorizedRunCount"] = 1
    elif tamper == "preflight-one-shot-consumption":
        policy["postFreezeLabelBlindPreflight"]["oneShotConsumption"]["consumesR3OneShot"] = True
    elif tamper == "preflight-forbidden-operation-count":
        policy["postFreezeLabelBlindPreflight"]["forbiddenOperationCounts"]["officialRunnerInvocations"] = 1
    elif tamper == "incident-parse-count":
        policy["preCommitGovernanceIncidentDisclosure"]["docsAuditStage1ReportJsonLoadsCount"] = 2
    elif tamper == "incident-decision-input":
        policy["preCommitGovernanceIncidentDisclosure"]["decisionIndependence"]["usedAsDecisionInput"] = True
    elif tamper == "incident-retention":
        policy["preCommitGovernanceIncidentDisclosure"]["retention"]["parsedStage1ObjectRetained"] = True
    elif tamper == "stage-b-classification":
        policy["stageBAdmission"]["requiredOutcomeClassificationSet"] = ["C", "I"]
    else:
        policy["stageBAdmission"]["expectedReconciliationProjectionSetSha256"] = _digest("stale-stage-b-projection")

    with pytest.raises(examples.BeatCellExamplesError, match="authority is stale"):
        examples._expected_product_reconciliations()


@pytest.mark.parametrize("mutation", ("eligible", "wider-gap"))
def test_product_reconciliation_rejects_eligible_or_nontied_product_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    reconciliation = _hu33_product_reconciliation()
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])
    reconciliation = deepcopy(reconciliation)
    if mutation == "eligible":
        reconciliation["featureDominance"] = 0.75
        reconciliation["stage1Dominance"] = 0.75
    else:
        reconciliation["overlapSecondsByProduct"]["Fm"] = 0.35
        reconciliation["candidateProducts"] = ["Fm"]

    with pytest.raises(examples.BeatCellExamplesError, match="not an exact ineligible reconciliation"):
        examples._reconcile_stage1_product(reconciliation)


def test_exact_product_match_does_not_enter_reconciliation_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, prediction, baseline, _manifest = _synthetic_stage_a(monkeypatch)
    reconciliations: list[dict[str, Any]] = []

    def forbidden(_value: Any) -> dict[str, Any]:
        raise AssertionError("an exact product match entered tolerant reconciliation")

    monkeypatch.setattr(examples, "_reconcile_stage1_product", forbidden)
    observed = examples.build_beat_cell_feature_summary(
        sidecar,
        prediction,
        prediction_file_sha256=sidecar["predictionIdentity"]["predictionSha256"],
        product_reconciliations=reconciliations,
    )
    assert observed == baseline
    assert reconciliations == []


@pytest.mark.parametrize("inventory", ("missing", "extra"))
def test_product_reconciliation_inventory_rejects_missing_or_extra_row(
    monkeypatch: pytest.MonkeyPatch,
    inventory: str,
) -> None:
    reconciliation = _hu33_product_reconciliation()
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])
    observed = [] if inventory == "missing" else [reconciliation, {**reconciliation, "trackId": "unexpected"}]

    with pytest.raises(examples.BeatCellExamplesError, match="inventory is not exact"):
        examples._validate_product_reconciliation_inventory(observed)


def test_product_reconciliation_inventory_is_scoped_to_the_validated_track_subset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reconciliation = _hu33_product_reconciliation()
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])
    sidecar, prediction, summary, manifest = _synthetic_stage_a(monkeypatch)

    validated_manifest, validated = examples.validate_beat_cell_feature_set_semantics(
        manifest,
        [summary],
        stage1_sidecars={"track-1": sidecar},
        predictions={"track-1": prediction},
        prediction_file_sha256s={"track-1": sidecar["predictionIdentity"]["predictionSha256"]},
    )
    assert validated_manifest == manifest
    assert validated == [summary]
    assert examples._validate_product_reconciliation_inventory([], track_ids={"track-1"}) == []
    assert examples._validate_stage_b_product_reconciliations([], track_ids={"track-1"}) == []


def test_pinned_track_subset_requires_its_exact_reconciliation_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reconciliation = _hu33_product_reconciliation()
    track_ids = {reconciliation["trackId"]}
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])

    assert examples._validate_product_reconciliation_inventory([reconciliation], track_ids=track_ids) == [
        reconciliation
    ]
    with pytest.raises(examples.BeatCellExamplesError, match="inventory is not exact"):
        examples._validate_product_reconciliation_inventory([], track_ids=track_ids)
    expected_stage_b = examples._stage_b_reconciliation_projection(reconciliation)
    assert examples._validate_stage_b_product_reconciliations([reconciliation], track_ids=track_ids) == [
        expected_stage_b
    ]
    with pytest.raises(examples.BeatCellExamplesError, match="inventory is not exact"):
        examples._validate_stage_b_product_reconciliations([], track_ids=track_ids)


def _stage_b_product_mismatch_fixture(
    monkeypatch: pytest.MonkeyPatch,
    classification: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    sidecar, prediction, feature_summary, manifest = _synthetic_stage_a(monkeypatch)
    feature_summary = deepcopy(feature_summary)
    feature = feature_summary["rows"][0]
    feature["predictionProduct"] = "C7"
    feature["predictionCoverage"] = 1.0
    feature["predictionDominance"] = 0.499999999999999

    stage1_artifact = _fake_stage1(sidecar, feature_summary, (classification, "C"))
    outcome = stage1_artifact["tracks"][0]["cellOutcomes"][0]
    outcome["predictionProduct"] = "Fm"
    outcome["predictionCoverage"] = 1.0
    outcome["predictionDominance"] = 0.5000000000000061
    _rehash(outcome, "rowSha256")
    _rehash(stage1_artifact, "artifactSha256")

    reconciliation = {
        "trackId": "track-1",
        "cellIndex": feature["cellIndex"],
        "startMilliseconds": feature["startMilliseconds"],
        "endMilliseconds": feature["endMilliseconds"],
        "sourceBeatCellSha256": feature["sourceBeatCellSha256"],
        "featureProduct": feature["predictionProduct"],
        "stage1Product": outcome["predictionProduct"],
        "featureCoverage": feature["predictionCoverage"],
        "stage1Coverage": outcome["predictionCoverage"],
        "featureDominance": feature["predictionDominance"],
        "stage1Dominance": outcome["predictionDominance"],
        "candidateProducts": ["C7", "Fm"],
        "overlapSecondsByProduct": {
            "C7": 0.499999999999999,
            "Fm": 0.5000000000000061,
        },
    }
    _install_product_reconciliation_authority(monkeypatch, [reconciliation])
    monkeypatch.setattr(
        examples,
        "validate_beat_cell_feature_set_semantics",
        lambda *_args, **_kwargs: (deepcopy(manifest), [deepcopy(feature_summary)]),
    )
    monkeypatch.setattr(stage1, "validate_beat_cell_stage1_artifact", lambda value: deepcopy(dict(value)))
    return sidecar, prediction, feature_summary, manifest, stage1_artifact, reconciliation


@pytest.mark.parametrize("classification", ("U", "N"))
def test_stage_b_ineligible_product_reconciliation_emits_no_example_for_that_cell(
    monkeypatch: pytest.MonkeyPatch,
    classification: str,
) -> None:
    sidecar, prediction, feature_summary, manifest, stage1_artifact, _reconciliation = (
        _stage_b_product_mismatch_fixture(monkeypatch, classification)
    )
    artifact = examples.build_beat_cell_examples(
        stage1_artifact,
        manifest,
        [feature_summary],
        stage1_sidecars={"track-1": sidecar},
        predictions={"track-1": prediction},
        prediction_file_sha256s={"track-1": sidecar["predictionIdentity"]["predictionSha256"]},
        source_stage1_file_sha256=manifest["sourceStage1ReportFileSha256"],
        source_stage1_canonical_sha256=canonical_sha256(stage1_artifact),
        source_feature_set_file_sha256=hashlib.sha256(_render(manifest)).hexdigest(),
    )

    assert artifact["exampleCount"] == 1
    assert [row["cellIndex"] for row in artifact["examples"]] == [1]


@pytest.mark.parametrize("classification", ("C", "I"))
def test_stage_b_product_mismatch_is_fatal_for_correctness_examples(
    monkeypatch: pytest.MonkeyPatch,
    classification: str,
) -> None:
    sidecar, prediction, feature_summary, manifest, stage1_artifact, _reconciliation = (
        _stage_b_product_mismatch_fixture(monkeypatch, classification)
    )

    with pytest.raises(examples.BeatCellExamplesError, match="not an exact ineligible reconciliation"):
        examples.build_beat_cell_examples(
            stage1_artifact,
            manifest,
            [feature_summary],
            stage1_sidecars={"track-1": sidecar},
            predictions={"track-1": prediction},
            prediction_file_sha256s={"track-1": sidecar["predictionIdentity"]["predictionSha256"]},
            source_stage1_file_sha256=manifest["sourceStage1ReportFileSha256"],
            source_stage1_canonical_sha256=canonical_sha256(stage1_artifact),
            source_feature_set_file_sha256=hashlib.sha256(_render(manifest)).hexdigest(),
        )


@pytest.mark.parametrize(
    ("target", "field"),
    (
        ("projection", "projectionSha256"),
        ("row", "rowSha256"),
        ("row", "sourceAudioSha256"),
        ("row", "cachedArraySha256"),
        ("row", "freshArraySha256"),
        ("row", "canonicalDurationMilliseconds"),
    ),
)
def test_direct_audio_lineage_projection_crossbinds_every_stage_a_identity_field(
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    field: str,
) -> None:
    sidecar, _prediction_value, _summary, _manifest = _synthetic_stage_a(monkeypatch)
    identity = sidecar["predictionIdentity"]
    expected_projection_sha256 = _digest("audio-projection")
    projection = {
        "projectionSha256": expected_projection_sha256,
        "tracks": [
            {
                "trackId": "track-1",
                "rowSha256": sidecar["sourceAudioLineageRowSha256"],
                "sourceAudioSha256": identity["sourceAudioSha256"],
                "cachedArraySha256": identity["cachedFeatureArraySha256"],
                "freshArraySha256": identity["freshFeatureArraySha256"],
                "canonicalDurationMilliseconds": identity["canonicalDurationMilliseconds"],
            }
        ],
    }
    examples._crosscheck_stage_a_audio_projection(
        {"track-1": sidecar},
        projection,
        expected_projection_sha256,
    )
    tampered = deepcopy(projection)
    if target == "projection":
        tampered[field] = _digest("wrong-projection")
    elif field == "canonicalDurationMilliseconds":
        tampered["tracks"][0][field] += 1
    else:
        tampered["tracks"][0][field] = _digest(f"wrong-{field}")
    with pytest.raises(examples.BeatCellExamplesError, match="audio-lineage|Audio-lineage"):
        examples._crosscheck_stage_a_audio_projection(
            {"track-1": sidecar},
            tampered,
            expected_projection_sha256,
        )


@pytest.mark.parametrize("mutation", ("interval", "source-cell", "feature-value"))
def test_semantic_recomputation_rejects_fully_resealed_feature_mutation(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    sidecar, prediction, summary, _manifest = _synthetic_stage_a(monkeypatch)
    tampered = deepcopy(summary)
    if mutation == "interval":
        tampered["rows"][0]["endMilliseconds"] += 1
        tampered["rows"][0]["durationMilliseconds"] += 1
        tampered["rows"][1]["startMilliseconds"] += 1
        tampered["rows"][1]["durationMilliseconds"] -= 1
        _rehash(tampered["rows"][0], "rowSha256")
        _rehash(tampered["rows"][1], "rowSha256")
    elif mutation == "source-cell":
        tampered["rows"][0]["sourceBeatCellSha256"] = _digest("replacement-cell")
        _rehash(tampered["rows"][0], "rowSha256")
    else:
        tampered["rows"][0]["featureValues"]["rootMarginMean"] = 0.123456
        tampered["rows"][0]["featureValuesSha256"] = canonical_sha256(tampered["rows"][0]["featureValues"])
        _rehash(tampered["rows"][0], "rowSha256")
    tampered["rowSetSha256"] = canonical_sha256(tampered["rows"])
    _rehash(tampered, "artifactSha256")
    manifest = examples.build_beat_cell_feature_set_manifest(
        [tampered],
        summary_output_root=Path("/synthetic/features"),
        source_stage1_report_path=Path("/synthetic/stage1.json"),
        source_stage1_report_file_sha256=_digest("stage1-file"),
        source_stage1_summary_artifact_set_sha256=canonical_sha256(
            [{"trackId": "track-1", "artifactSha256": sidecar["artifactSha256"]}]
        ),
        source_stage1_summary_file_set_sha256=_digest("sidecar-file-set"),
    )
    examples.validate_beat_cell_feature_set(manifest, [tampered])
    with pytest.raises(examples.BeatCellExamplesError, match="semantic recomputation"):
        examples.validate_beat_cell_feature_set_semantics(
            manifest,
            [tampered],
            stage1_sidecars={"track-1": sidecar},
            predictions={"track-1": prediction},
            prediction_file_sha256s={"track-1": sidecar["predictionIdentity"]["predictionSha256"]},
        )


@pytest.mark.parametrize(
    "field",
    (
        "sourceStage1ReportPathSha256",
        "sourceStage1ReportFileSha256",
        "sourceStage1SummaryArtifactSetSha256",
        "sourceStage1SummaryFileSetSha256",
    ),
)
def test_official_stage_b_rejects_coherently_resealed_false_stage_a_provenance(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    _sidecar, _prediction_value, summary, manifest = _synthetic_stage_a(monkeypatch)
    source = deepcopy(examples.BEAT_CELL_STAGE2_SOURCE_INPUTS)
    source["stage1Report"] = {
        **source["stage1Report"],
        "path": "/synthetic/stage1.json",
        "fileSha256": manifest["sourceStage1ReportFileSha256"],
    }
    source["stage1SummaryArtifactSet"] = {
        **source["stage1SummaryArtifactSet"],
        "sha256": manifest["sourceStage1SummaryArtifactSetSha256"],
    }
    source["stage1SummaryFileSet"] = {
        **source["stage1SummaryFileSet"],
        "sha256": manifest["sourceStage1SummaryFileSetSha256"],
    }
    source["trackCount"] = 1
    source["cellCount"] = 2
    outputs = deepcopy(examples.BEAT_CELL_STAGE2_OUTPUT_PATHS)
    outputs["featureSummaryRoot"] = "/synthetic/features"
    monkeypatch.setattr(examples, "BEAT_CELL_STAGE2_SOURCE_INPUTS", source)
    monkeypatch.setattr(examples, "BEAT_CELL_STAGE2_OUTPUT_PATHS", outputs)
    name = examples._feature_summary_filename(summary)
    values = {name: summary}
    snapshots = {name: (_render(summary), (1, 1))}
    examples._validate_official_feature_manifest_admission(manifest, values, snapshots)

    tampered = deepcopy(manifest)
    tampered[field] = _digest(f"false-{field}")
    _rehash(tampered, "artifactSha256")
    assert examples.validate_beat_cell_feature_set_manifest(tampered) == tampered
    with pytest.raises(examples.BeatCellExamplesError, match="official Stage-A authority"):
        examples._validate_official_feature_manifest_admission(tampered, values, snapshots)


def test_official_stage_b_rejects_resealed_nondeterministic_feature_summary_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _sidecar, _prediction_value, summary, manifest = _synthetic_stage_a(monkeypatch)
    source = deepcopy(examples.BEAT_CELL_STAGE2_SOURCE_INPUTS)
    source["stage1Report"] = {
        **source["stage1Report"],
        "path": "/synthetic/stage1.json",
        "fileSha256": manifest["sourceStage1ReportFileSha256"],
    }
    source["stage1SummaryArtifactSet"] = {
        **source["stage1SummaryArtifactSet"],
        "sha256": manifest["sourceStage1SummaryArtifactSetSha256"],
    }
    source["stage1SummaryFileSet"] = {
        **source["stage1SummaryFileSet"],
        "sha256": manifest["sourceStage1SummaryFileSetSha256"],
    }
    source["trackCount"] = 1
    source["cellCount"] = 2
    outputs = deepcopy(examples.BEAT_CELL_STAGE2_OUTPUT_PATHS)
    outputs["featureSummaryRoot"] = "/synthetic/features"
    monkeypatch.setattr(examples, "BEAT_CELL_STAGE2_SOURCE_INPUTS", source)
    monkeypatch.setattr(examples, "BEAT_CELL_STAGE2_OUTPUT_PATHS", outputs)
    name = examples._feature_summary_filename(summary)

    tampered = deepcopy(manifest)
    tampered["summaries"][0]["path"] = f"/synthetic/features/{name}.alternate.json"
    tampered["summaries"][0]["pathSha256"] = canonical_sha256(tampered["summaries"][0]["path"])
    _rehash(tampered["summaries"][0], "rowSha256")
    tampered["summarySetSha256"] = canonical_sha256(tampered["summaries"])
    _rehash(tampered, "artifactSha256")
    assert examples.validate_beat_cell_feature_set_manifest(tampered) == tampered
    alternate_name = Path(tampered["summaries"][0]["path"]).name
    with pytest.raises(examples.BeatCellExamplesError, match="not authority-deterministic"):
        examples._validate_official_feature_manifest_admission(
            tampered,
            {alternate_name: summary},
            {alternate_name: (_render(summary), (1, 1))},
        )


def test_canonical_json_sort_keys_round_trip_preserves_feature_mapping_validity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _minimal_examples_artifact(monkeypatch)
    parsed = json.loads(_render(artifact))
    assert list(parsed["examples"][0]["featureValues"]) != list(examples.FEATURE_NAMES)
    assert examples.validate_beat_cell_examples_artifact(parsed) == parsed


def test_label_mutation_cannot_change_example_keys_or_tie_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _minimal_examples_artifact(monkeypatch, classifications=("C", "I"))
    second = _minimal_examples_artifact(monkeypatch, classifications=("I", "C"))
    assert [row["exampleKey"] for row in first["examples"]] == [row["exampleKey"] for row in second["examples"]]
    assert [row["correct"] for row in first["examples"]] != [row["correct"] for row in second["examples"]]


def test_every_stage1_outcome_mutation_is_absent_from_all_stage_a_bytes_paths_and_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar, prediction, first_summary, first_manifest = _synthetic_stage_a(monkeypatch)
    first_outcomes = _fake_stage1(sidecar, first_summary, ("C", "I"))
    mutated_outcomes = _fake_stage1(sidecar, first_summary, ("I", "C"))
    assert first_outcomes["artifactSha256"] != mutated_outcomes["artifactSha256"]
    assert all(
        left["rowSha256"] != right["rowSha256"]
        for left, right in zip(
            first_outcomes["tracks"][0]["cellOutcomes"],
            mutated_outcomes["tracks"][0]["cellOutcomes"],
            strict=True,
        )
    )

    # Neither outcome object is, or can be, supplied to either Stage-A API.
    second_summary = examples.build_beat_cell_feature_summary(
        sidecar,
        prediction,
        prediction_file_sha256=sidecar["predictionIdentity"]["predictionSha256"],
    )
    second_manifest = examples.build_beat_cell_feature_set_manifest(
        [second_summary],
        summary_output_root=Path("/synthetic/features"),
        source_stage1_report_path=Path("/synthetic/stage1.json"),
        source_stage1_report_file_sha256=first_manifest["sourceStage1ReportFileSha256"],
        source_stage1_summary_artifact_set_sha256=first_manifest["sourceStage1SummaryArtifactSetSha256"],
        source_stage1_summary_file_set_sha256=first_manifest["sourceStage1SummaryFileSetSha256"],
    )
    assert _render(first_summary) == _render(second_summary)
    assert examples._feature_summary_filename(first_summary) == examples._feature_summary_filename(second_summary)
    assert first_summary["rowSetSha256"] == second_summary["rowSetSha256"]
    assert first_summary["artifactSha256"] == second_summary["artifactSha256"]
    assert _render(first_manifest) == _render(second_manifest)
    assert first_manifest["summarySetSha256"] == second_manifest["summarySetSha256"]
    assert first_manifest["artifactSha256"] == second_manifest["artifactSha256"]


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("aggregate",), ("dataset", None, None)),
        (("datasets", 0), ("dataset", "guitarset", None)),
        (("guitarset", "aggregate"), ("aggregate", "guitarset", None)),
        (("guitarset", "roles", 0), ("guitarsetRole", "guitarset", "solo")),
    ],
)
def test_label_audit_scope_tuple_tamper_fails_after_reseal(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[Any, ...],
    replacement: tuple[str, str | None, str | None],
) -> None:
    artifact = _minimal_examples_artifact(monkeypatch)
    tampered = deepcopy(artifact)
    target: Any = tampered["labelAudits"]
    for component in path:
        target = target[component]
    target["scope"], target["datasetId"], target["guitarsetRole"] = replacement
    _rehash(target, "rowSha256")
    if path[:2] == ("guitarset", "roles"):
        guitarset = tampered["labelAudits"]["guitarset"]
        guitarset["roleSetSha256"] = canonical_sha256(guitarset["roles"])
        _rehash(guitarset, "rowSha256")
    elif path == ("guitarset", "aggregate"):
        _rehash(tampered["labelAudits"]["guitarset"], "rowSha256")
    elif path[0] == "datasets":
        tampered["labelAudits"]["datasetSetSha256"] = canonical_sha256(tampered["labelAudits"]["datasets"])
    _rehash(tampered["labelAudits"], "auditSha256")
    tampered["labelAuditsSha256"] = tampered["labelAudits"]["auditSha256"]
    _rehash(tampered, "artifactSha256")
    with pytest.raises(
        examples.BeatCellExamplesError,
        match="scope tuple|certification order|ordered comp, solo",
    ):
        examples.validate_beat_cell_examples_artifact(tampered)


def test_official_cli_wrappers_reject_all_path_and_weakening_flags() -> None:
    from scripts.chord_beat_cell_examples import main as examples_main
    from scripts.chord_beat_cell_features import main as features_main

    with pytest.raises(SystemExit, match="no path"):
        features_main(["--source", "/tmp/synthetic"])
    with pytest.raises(SystemExit, match="no path"):
        examples_main(["--allow-retry"])


def test_official_runtime_manifest_binding_uses_exact_nested_analyzer_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = {
        "manifestSha256": _digest("runtime-manifest"),
        "trackSetSha256": _digest("runtime-tracks"),
        "analyzerContract": {"contractSha256": _digest("runtime-analyzer")},
    }
    runtime_raw = _render(runtime)
    monkeypatch.setattr(
        stage1,
        "STAGE1_SOURCE_CONTRACT",
        {
            "runtimeManifest": {
                "fileSha256": hashlib.sha256(runtime_raw).hexdigest(),
                "manifestSha256": runtime["manifestSha256"],
                "trackSetSha256": runtime["trackSetSha256"],
                "analyzerContractSha256": runtime["analyzerContract"]["contractSha256"],
            }
        },
    )
    examples._validate_official_runtime_manifest_binding(runtime_raw, runtime)


@pytest.mark.parametrize("nested", (None, "not-an-object", {"contractSha256": _digest("wrong-analyzer")}))
def test_official_runtime_manifest_binding_rejects_bad_nested_analyzer_despite_top_level_alias(
    monkeypatch: pytest.MonkeyPatch,
    nested: Any,
) -> None:
    expected_analyzer = _digest("runtime-analyzer")
    runtime: dict[str, Any] = {
        "manifestSha256": _digest("runtime-manifest"),
        "trackSetSha256": _digest("runtime-tracks"),
        "analyzerContractSha256": expected_analyzer,
    }
    if nested is not None:
        runtime["analyzerContract"] = nested
    runtime_raw = _render(runtime)
    monkeypatch.setattr(
        stage1,
        "STAGE1_SOURCE_CONTRACT",
        {
            "runtimeManifest": {
                "fileSha256": hashlib.sha256(runtime_raw).hexdigest(),
                "manifestSha256": runtime["manifestSha256"],
                "trackSetSha256": runtime["trackSetSha256"],
                "analyzerContractSha256": expected_analyzer,
            }
        },
    )
    with pytest.raises(examples.BeatCellExamplesError, match="analyzerContract|Runtime manifest disagrees"):
        examples._validate_official_runtime_manifest_binding(runtime_raw, runtime)


def test_official_stage_a_rejects_unpinned_audio_before_nested_path_or_root_access(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "stage1.json"
    report_path.write_bytes(b"opaque-stage1\n")
    runtime = {
        "manifestSha256": _digest("runtime-manifest"),
        "trackSetSha256": _digest("runtime-tracks"),
        "analyzerContract": {
            "contractSha256": _digest("runtime-analyzer"),
        },
    }
    runtime_path = tmp_path / "runtime-manifest.json"
    runtime_path.write_bytes(_render(runtime))
    receipt = {"receiptSha256": _digest("receipt")}
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_bytes(_render(receipt))
    protected = tmp_path / "protected-do-not-open.json"
    alternate_audio = {
        "schemaVersion": "coherently-resealed-alternate-audio-lineage",
        "manifestBindings": {"winnerCacheManifest": {"path": str(protected)}},
    }
    _rehash(alternate_audio, "artifactSha256")
    audio_path = tmp_path / "alternate-audio-lineage.json"
    audio_path.write_bytes(_render(alternate_audio))

    source = {
        "stage1Report": {
            "path": str(report_path),
            "fileSha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        },
        "runtimeManifest": str(runtime_path),
        "beatReceipt": str(receipt_path),
        "audioLineage": str(audio_path),
        "runtimeRoot": str(tmp_path / "protected-runtime-root"),
    }
    monkeypatch.setattr(examples, "BEAT_CELL_STAGE2_SOURCE_INPUTS", source)
    monkeypatch.setattr(examples, "load_beat_cell_stage2_authority", lambda: {})
    monkeypatch.setattr(examples, "_expected_product_reconciliations", lambda: [])
    monkeypatch.setattr(
        examples,
        "_preflight_official_feature_outputs",
        lambda: (tmp_path / "unused-manifest.json", tmp_path / "unused-summaries"),
    )
    monkeypatch.setattr(
        stage1,
        "STAGE1_SOURCE_CONTRACT",
        {
            "runtimeManifest": {
                "fileSha256": hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
                "manifestSha256": runtime["manifestSha256"],
                "trackSetSha256": runtime["trackSetSha256"],
                "analyzerContractSha256": runtime["analyzerContract"]["contractSha256"],
            },
            "audioLineage": {
                "fileSha256": _digest("frozen-audio-file"),
                "artifactSha256": _digest("frozen-audio-artifact"),
            },
        },
    )
    monkeypatch.setattr(
        stage1,
        "OFFICIAL_BEAT_RECEIPT_CONTRACT",
        {"fileSha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest()},
    )

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("an untrusted audio-declared path or root was accessed")

    monkeypatch.setattr(examples, "_capture_directory_identity", forbidden)
    monkeypatch.setattr(examples, "_capture_stage_a_admitted_inputs", forbidden)
    with pytest.raises(examples.BeatCellExamplesError, match="Audio lineage disagrees"):
        examples.run_official_beat_cell_features()
    assert not protected.exists()


@pytest.mark.parametrize("publication", ("feature-set", "examples"))
def test_input_mutation_at_precommit_leaves_no_visible_output(
    tmp_path: Path,
    publication: str,
) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"version":1}\n', encoding="utf-8")
    raw, inode = examples._sealed_read(source, "synthetic source")

    def mutate_then_verify() -> None:
        source.write_text('{"version":2}\n', encoding="utf-8")
        examples._verify_snapshot(source, raw, inode, "synthetic source")

    artifact = {"schemaVersion": "synthetic", "artifactSha256": _digest("artifact")}
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    if publication == "examples":
        with pytest.raises(examples.BeatCellExamplesError, match="changed before publication"):
            examples._publish_new_json_with_precommit(output, artifact, mutate_then_verify)
        assert not output.exists()
        return
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "summary.json").write_text('{"summary":true}\n', encoding="utf-8")
    summary_output = output.parent / "summaries"
    with pytest.raises(examples.BeatCellExamplesError, match="changed before publication"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            artifact,
            staging,
            summary_output,
            mutate_then_verify,
        )
    assert not output.exists()
    assert not summary_output.exists()
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))


@pytest.mark.parametrize("root_name", ("benchmark root", "runtime root"))
def test_exact_directory_barrier_rejects_root_relocation_with_unchanged_leaf_inode(
    tmp_path: Path,
    root_name: str,
) -> None:
    root = tmp_path / root_name.replace(" ", "-")
    root.mkdir()
    leaf = root / "leaf.json"
    leaf.write_text('{"value":1}\n', encoding="utf-8")
    leaf_inode = leaf.stat().st_ino
    captured_inode = examples._capture_directory_identity(root, root_name)
    moved = root.with_name(f"{root.name}-moved")

    def relocate_with_hardlinked_leaf() -> None:
        root.rename(moved)
        root.mkdir()
        os.link(moved / leaf.name, root / leaf.name)
        assert (root / leaf.name).stat().st_ino == leaf_inode

    with pytest.raises(Exception, match="path changed during publication"):
        examples._run_with_exact_directory(
            root,
            captured_inode,
            root_name,
            relocate_with_hardlinked_leaf,
        )


def test_flat_directory_recheck_rejects_path_swap_after_reading_same_leaf_inode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "flat-root"
    root.mkdir()
    leaf = root / "leaf.json"
    leaf.write_text('{"value":1}\n', encoding="utf-8")
    _values, snapshots, root_inode = examples._read_flat_json_directory(root, "synthetic flat root")
    leaf_inode = leaf.stat().st_ino
    moved = root.with_name("flat-root-moved")
    original_read = examples.os.read
    swapped = False

    def read_then_swap(descriptor: int, size: int) -> bytes:
        nonlocal swapped
        chunk = original_read(descriptor, size)
        if not chunk and not swapped:
            swapped = True
            root.rename(moved)
            root.mkdir()
            os.link(moved / leaf.name, root / leaf.name)
            assert (root / leaf.name).stat().st_ino == leaf_inode
        return chunk

    monkeypatch.setattr(examples.os, "read", read_then_swap)
    with pytest.raises(Exception, match="path changed during publication"):
        examples._verify_flat_directory(root, snapshots, root_inode, "synthetic flat root")
    assert swapped is True


def test_stage1_sidecar_raw_set_is_pinned_before_any_json_parse(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "stage1-summaries"
    root.mkdir()
    allowed_raw = b'{"predictionOnly":true}\n'
    (root / "allowed.json").write_bytes(allowed_raw)
    (root / "protected-outcome.json").write_bytes(b"PROTECTED OUTCOME JSON MUST NOT BE PARSED")
    expected_file_set = canonical_sha256(
        [
            {
                "name": "allowed.json",
                "fileSha256": hashlib.sha256(allowed_raw).hexdigest(),
            }
        ]
    )
    monkeypatch.setattr(
        examples,
        "BEAT_CELL_STAGE2_SOURCE_INPUTS",
        {
            "stage1SummaryRoot": str(root),
            "trackCount": 1,
            "stage1SummaryFileSet": {"sha256": expected_file_set},
        },
    )
    parse_calls = 0

    def forbidden_parse(_raw: bytes, _name: str) -> dict[str, Any]:
        nonlocal parse_calls
        parse_calls += 1
        raise AssertionError("an unadmitted Stage-1 JSON file was parsed")

    monkeypatch.setattr(examples, "_strict_json", forbidden_parse)
    with pytest.raises(examples.BeatCellExamplesError, match="raw-file inventory"):
        examples._official_label_blind_sources()
    assert parse_calls == 0


def _synthetic_stage_a_admitted_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Path]]:
    repo = tmp_path / "repo"

    def leaf(relative: str, payload: bytes | None = None) -> Path:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload if payload is not None else f"{relative}\n".encode())
        return path

    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    runtime_manifest = runtime_root / "manifest.json"
    runtime_manifest.write_text("{}\n", encoding="utf-8")
    timing = runtime_root / "timing.json"
    timing.write_text('{"timing":true}\n', encoding="utf-8")

    bar_paths = {
        "_CLIENT": leaf("ui/bar-client.js"),
        "_WORKER": leaf("ui/bar-worker.js"),
        "_RUNNER": leaf("scripts/bar-runner.js"),
        "_GENERATOR": leaf("steel_guitar_rag/chord_reader/runtime_bar_grid.py"),
        "_BROWSER": leaf("bin/chrome"),
    }
    beat_paths = {
        "_BASE_RUNNER": bar_paths["_RUNNER"],
        "_GENERATOR": leaf("steel_guitar_rag/chord_reader/runtime_beat_grid.py"),
        "_CLIENT_ALIAS": bar_paths["_CLIENT"],
        "_WORKER_ALIAS": bar_paths["_WORKER"],
    }
    for field, path in bar_paths.items():
        monkeypatch.setattr(examples._runtime_bar_grid, field, path)
    for field, path in beat_paths.items():
        monkeypatch.setattr(examples._runtime_beat_grid, field, path)
    monkeypatch.setattr(examples._runtime_beat_grid, "_REPO_ROOT", repo)
    node = leaf("bin/node")
    monkeypatch.setattr(examples.shutil, "which", lambda name: str(node) if name == "node" else None)

    player_alias = leaf("ui/player-alias.js", b"player\n")
    player_active = repo / "ui/player-active.js"
    player_active.symlink_to(player_alias.name)
    setup_document = leaf("ui/setup.html", b"<html></html>\n")
    receipt = {
        "playerReplayContract": {
            "resources": [
                {"repoRelativePath": "ui/player-alias.js"},
                {"repoRelativePath": "ui/player-active.js"},
            ],
            "documentLoads": [
                {
                    "documentPath": "ui/setup.html",
                    "resourcePath": "ui/player-active.js",
                }
            ],
        }
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text("{}\n", encoding="utf-8")

    winner = leaf("manifests/winner.json")
    development = leaf("manifests/development.json")
    dasheng = leaf("manifests/dasheng.json")
    extractor = leaf("extractor.py")
    dependency_lock = leaf("requirements.lock")
    source_audio = leaf("audio/track.wav", b"audio\n")
    cached_npz = leaf("cache/track.npz", b"cache\n")
    audio_lineage = {
        "manifestBindings": {
            "winnerCacheManifest": {"path": str(winner)},
            "developmentSourceManifest": {"path": str(development)},
            "dashengCacheManifest": {"path": str(dasheng)},
        },
        "extractorContract": {
            "sourceFile": str(extractor),
            "dependencyLockFile": str(dependency_lock),
        },
        "tracks": [
            {
                "audioPath": str(source_audio),
                "cachedFeaturePath": str(cached_npz),
            }
        ],
    }
    audio_lineage_path = tmp_path / "audio-lineage.json"
    audio_lineage_path.write_text("{}\n", encoding="utf-8")
    runtime = {"timingArtifacts": [{"timingFile": timing.name}]}
    snapshot = examples._capture_stage_a_admitted_inputs(
        runtime,
        receipt,
        audio_lineage,
        runtime_root,
        runtime_manifest,
        receipt_path,
        audio_lineage_path,
    )
    selected = {
        "runtime-manifest": runtime_manifest,
        "runtime-timing": timing,
        "beat-receipt": receipt_path,
        "audio-lineage-artifact": audio_lineage_path,
        "audio-bound-manifest": winner,
        "audio-extractor-source": extractor,
        "audio-dependency-lock": dependency_lock,
        "audio-source": source_audio,
        "audio-cache": cached_npz,
        "receipt-generator": beat_paths["_GENERATOR"],
        "receipt-runner": bar_paths["_RUNNER"],
        "receipt-client": bar_paths["_CLIENT"],
        "receipt-worker": bar_paths["_WORKER"],
        "receipt-node": node,
        "receipt-chrome": bar_paths["_BROWSER"],
        "receipt-setup-document": setup_document,
        "receipt-player-resource": player_alias,
    }
    projected = set(snapshot["files"])
    assert {str(path.resolve()) for path in selected.values()} <= projected
    assert str(player_active) in projected
    return snapshot, selected


@pytest.mark.parametrize(
    "input_class",
    (
        "runtime-timing",
        "runtime-manifest",
        "beat-receipt",
        "audio-lineage-artifact",
        "audio-bound-manifest",
        "audio-extractor-source",
        "audio-dependency-lock",
        "audio-source",
        "audio-cache",
        "receipt-generator",
        "receipt-runner",
        "receipt-client",
        "receipt-worker",
        "receipt-node",
        "receipt-chrome",
        "receipt-setup-document",
        "receipt-player-resource",
    ),
)
def test_stage_a_admitted_input_projection_rejects_byte_identical_inode_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    input_class: str,
) -> None:
    snapshot, selected = _synthetic_stage_a_admitted_snapshot(monkeypatch, tmp_path)
    target = selected[input_class]
    original_inode = target.stat().st_ino
    replacement = target.with_name(f"replacement-{target.name}")
    replacement.write_bytes(target.read_bytes())
    replacement.replace(target)
    assert target.stat().st_ino != original_inode
    with pytest.raises(examples.BeatCellExamplesError, match="identity changed"):
        examples._verify_stage_a_admitted_inputs(snapshot)


@pytest.mark.parametrize("mutation", ("retarget", "resolved-target-replacement"))
def test_admitted_symlink_snapshot_rejects_alias_or_target_identity_change(
    tmp_path: Path,
    mutation: str,
) -> None:
    target = tmp_path / "target.js"
    target.write_bytes(b"same bytes\n")
    alias = tmp_path / "active.js"
    alias.symlink_to(target.name)
    snapshot = examples._capture_admitted_file_projection([alias], "synthetic alias")
    if mutation == "retarget":
        replacement_target = tmp_path / "replacement-target.js"
        replacement_target.write_bytes(target.read_bytes())
        alias.unlink()
        alias.symlink_to(replacement_target.name)
    else:
        replacement_target = tmp_path / "replacement-target.js"
        replacement_target.write_bytes(target.read_bytes())
        replacement_target.replace(target)
    with pytest.raises(examples.BeatCellExamplesError, match="identity changed"):
        examples._verify_admitted_file_projection(snapshot, "synthetic alias")


def test_source_mutation_during_complete_tree_rename_fails_postcheck_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"version":1}\n', encoding="utf-8")
    raw, inode = examples._sealed_read(source, "synthetic source")
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "summary.json").write_text('{"summary":true}\n', encoding="utf-8")
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summary_output = output.parent / "summaries"
    callback_count = 0

    def verify() -> None:
        nonlocal callback_count
        callback_count += 1
        examples._verify_snapshot(source, raw, inode, "synthetic source")

    original_rename = examples._rename_directory_noreplace

    def rename_then_mutate(parent_descriptor: int, source_name: str, destination_name: str) -> None:
        assert not output.parent.exists()
        private_root = output.parent.parent / source_name
        assert (private_root / "manifest.json").is_file()
        assert sorted(path.name for path in (private_root / "summaries").iterdir()) == ["summary.json"]
        original_rename(parent_descriptor, source_name, destination_name)
        source.write_text('{"version":2}\n', encoding="utf-8")

    monkeypatch.setattr(examples, "_rename_directory_noreplace", rename_then_mutate)
    with pytest.raises(examples.BeatCellExamplesError, match="changed before publication"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            staging,
            summary_output,
            verify,
        )
    assert callback_count == 2
    assert not output.exists()
    assert not summary_output.exists()
    assert not output.parent.exists()
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))


@pytest.mark.parametrize("target", ("manifest", "summary"))
def test_complete_tree_final_callback_name_swap_preserves_foreign_and_cleans_owned_files(
    tmp_path: Path,
    target: str,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "a.json").write_text('{"summary":"a"}\n', encoding="utf-8")
    (staging / "b.json").write_text('{"summary":"b"}\n', encoding="utf-8")
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summaries = output.parent / "summaries"
    callback_count = 0
    foreign_bytes = b'{"foreign":true}\n'
    swapped = output if target == "manifest" else summaries / "a.json"
    stranded = swapped.with_name(f"stranded-{swapped.name}")

    def swap_at_final_callback() -> None:
        nonlocal callback_count
        callback_count += 1
        if callback_count == 2:
            swapped.rename(stranded)
            swapped.write_bytes(foreign_bytes)

    with pytest.raises(examples.BeatCellExamplesError, match="output name changed"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            staging,
            summaries,
            swap_at_final_callback,
        )
    assert callback_count == 2
    assert swapped.read_bytes() == foreign_bytes
    assert not stranded.exists()
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))
    if target == "manifest":
        assert not summaries.exists()
    else:
        assert not output.exists()
        assert {path.name for path in summaries.iterdir()} == {"a.json"}


def test_complete_tree_final_callback_root_swap_preserves_foreign_and_cleans_owned_root(
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "summary.json").write_text('{"summary":true}\n', encoding="utf-8")
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summaries = output.parent / "summaries"
    stranded_root = output.parent.with_name("stranded-owned-feature-set")
    callback_count = 0

    def swap_root_at_final_callback() -> None:
        nonlocal callback_count
        callback_count += 1
        if callback_count == 2:
            output.parent.rename(stranded_root)
            output.parent.mkdir()
            (output.parent / "foreign.txt").write_text("foreign", encoding="utf-8")

    with pytest.raises(Exception, match="path changed during publication"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            staging,
            summaries,
            swap_root_at_final_callback,
        )
    assert callback_count == 2
    assert (output.parent / "foreign.txt").read_text(encoding="utf-8") == "foreign"
    assert not stranded_root.exists()
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))


def test_source_mutation_during_examples_link_fails_postcheck_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"version":1}\n', encoding="utf-8")
    raw, inode = examples._sealed_read(source, "synthetic source")
    output = tmp_path / "output" / "artifact.json"
    callback_count = 0

    def verify() -> None:
        nonlocal callback_count
        callback_count += 1
        examples._verify_snapshot(source, raw, inode, "synthetic source")

    original_link = examples.os.link

    def link_then_mutate(*args: Any, **kwargs: Any) -> None:
        original_link(*args, **kwargs)
        source.write_text('{"version":2}\n', encoding="utf-8")

    monkeypatch.setattr(examples.os, "link", link_then_mutate)
    with pytest.raises(examples.BeatCellExamplesError, match="changed before publication"):
        examples._publish_new_json_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            verify,
        )
    assert callback_count == 2
    assert not output.exists()


def test_examples_destination_swap_at_final_parent_check_preserves_foreign_and_cleans_owned_inode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "output" / "artifact.json"
    stranded = output.parent / "stranded-owned.json"
    original_verify = examples._verify_directory_path
    verification_count = 0

    def swap_after_parent_check(
        path: Path,
        descriptor: int,
        inode: tuple[int, int],
        name: str,
    ) -> None:
        nonlocal verification_count
        original_verify(path, descriptor, inode, name)
        verification_count += 1
        if verification_count == 1:
            output.rename(stranded)
            output.write_bytes(b'{"foreign":true}\n')

    monkeypatch.setattr(examples, "_verify_directory_path", swap_after_parent_check)
    with pytest.raises(examples.BeatCellExamplesError, match="output name changed"):
        examples._publish_new_json_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            lambda: None,
        )
    assert output.read_bytes() == b'{"foreign":true}\n'
    assert not stranded.exists()
    assert not list(output.parent.glob(".*.tmp"))


def test_examples_post_link_exception_has_no_owned_output_or_temporary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "output" / "artifact.json"
    original_link = examples.os.link

    def link_then_fail(*args: Any, **kwargs: Any) -> None:
        original_link(*args, **kwargs)
        raise RuntimeError("synthetic exception after successful link")

    monkeypatch.setattr(examples.os, "link", link_then_fail)
    with pytest.raises(RuntimeError, match="after successful link"):
        examples._publish_new_json_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            lambda: None,
        )
    assert not output.exists()
    assert not list(output.parent.glob(".*.tmp"))


def test_complete_feature_set_publishes_only_as_one_complete_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    staged = {
        "a.json": b'{"summary":"a"}\n',
        "b.json": b'{"summary":"b"}\n',
    }
    for name, raw in staged.items():
        (staging / name).write_bytes(raw)
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summaries = output.parent / "summaries"
    callback_count = 0
    private_inode: int | None = None

    original_rename = examples._rename_directory_noreplace

    def record_single_rename(parent_descriptor: int, source_name: str, destination_name: str) -> None:
        nonlocal private_inode
        private_inode = os.stat(source_name, dir_fd=parent_descriptor, follow_symlinks=False).st_ino
        original_rename(parent_descriptor, source_name, destination_name)

    monkeypatch.setattr(examples, "_rename_directory_noreplace", record_single_rename)

    def verify_completion_barrier() -> None:
        nonlocal callback_count
        callback_count += 1
        if callback_count == 1:
            assert not output.parent.exists()
        else:
            assert output.is_file()
            assert {path.name for path in summaries.iterdir()} == set(staged)

    examples._publish_complete_feature_set_with_precommit(
        output,
        {"schemaVersion": "synthetic"},
        staging,
        summaries,
        verify_completion_barrier,
    )
    assert callback_count == 2
    assert output.parent.stat().st_ino == private_inode
    assert output.read_bytes() == _render({"schemaVersion": "synthetic"})
    assert {name: (summaries / name).read_bytes() for name in staged} == staged
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))


def test_complete_feature_set_noreplace_preserves_concurrent_foreign_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "summary.json").write_text('{"summary":true}\n', encoding="utf-8")
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summaries = output.parent / "summaries"
    original_rename = examples._rename_directory_noreplace

    def race(parent_descriptor: int, source_name: str, destination_name: str) -> None:
        output.parent.mkdir()
        (output.parent / "foreign.txt").write_text("foreign", encoding="utf-8")
        original_rename(parent_descriptor, source_name, destination_name)

    monkeypatch.setattr(examples, "_rename_directory_noreplace", race)
    with pytest.raises(examples.BeatCellExamplesError, match="concurrently created"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            staging,
            summaries,
            lambda: None,
        )
    assert (output.parent / "foreign.txt").read_text(encoding="utf-8") == "foreign"
    assert not output.exists()
    assert not summaries.exists()
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))


def test_failure_at_single_directory_rename_has_no_visible_partial_official_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "a.json").write_text('{"summary":"a"}\n', encoding="utf-8")
    (staging / "b.json").write_text('{"summary":"b"}\n', encoding="utf-8")
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summaries = output.parent / "summaries"

    def fail_at_publish(_parent_descriptor: int, source_name: str, _destination_name: str) -> None:
        private_root = output.parent.parent / source_name
        assert not output.parent.exists()
        assert (private_root / "manifest.json").is_file()
        assert {path.name for path in (private_root / "summaries").iterdir()} == {
            "a.json",
            "b.json",
        }
        raise examples.BeatCellExamplesError("synthetic failure at sole directory rename")

    monkeypatch.setattr(examples, "_rename_directory_noreplace", fail_at_publish)
    with pytest.raises(examples.BeatCellExamplesError, match="sole directory rename"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            staging,
            summaries,
            lambda: None,
        )
    assert not output.parent.exists()
    assert not list(output.parent.parent.glob(".feature-set.*.tmp"))


def test_complete_feature_set_parent_swap_fails_before_publish_and_cleans_private_tree(
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "summary.json").write_text('{"summary":true}\n', encoding="utf-8")
    output = tmp_path / "output" / "feature-set" / "manifest.json"
    summaries = output.parent / "summaries"
    moved_parent = tmp_path / "retained-parent"

    def swap_parent() -> None:
        output.parent.parent.rename(moved_parent)
        output.parent.parent.mkdir()

    with pytest.raises(Exception, match="path changed during publication"):
        examples._publish_complete_feature_set_with_precommit(
            output,
            {"schemaVersion": "synthetic"},
            staging,
            summaries,
            swap_parent,
        )
    assert not output.parent.exists()
    assert not (moved_parent / "feature-set").exists()
    assert not list(moved_parent.glob(".feature-set.*.tmp"))


@pytest.mark.parametrize("stage", ("features", "examples"))
def test_official_rerun_preflights_existing_output_before_any_source_or_builder(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stage: str,
) -> None:
    outputs = deepcopy(examples.BEAT_CELL_STAGE2_OUTPUT_PATHS)
    outputs.update(
        {
            "featureSetManifest": str(tmp_path / "feature-set" / "manifest.json"),
            "featureSummaryRoot": str(tmp_path / "feature-set" / "summaries"),
            "examplesArtifact": str(tmp_path / "examples" / "artifact.json"),
        }
    )
    monkeypatch.setattr(examples, "BEAT_CELL_STAGE2_OUTPUT_PATHS", outputs)
    if stage == "features":
        path = Path(outputs["featureSetManifest"])
        path.parent.mkdir(parents=True)
        path.write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(
            examples,
            "build_beat_cell_feature_summary",
            lambda *_args, **_kwargs: pytest.fail("builder ran after one-shot output existed"),
        )
        runner = examples.run_official_beat_cell_features
    else:
        path = Path(outputs["examplesArtifact"])
        path.parent.mkdir(parents=True)
        path.write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(
            examples,
            "build_beat_cell_examples",
            lambda *_args, **_kwargs: pytest.fail("outcome join ran after one-shot output existed"),
        )
        runner = examples.run_official_beat_cell_examples
    monkeypatch.setattr(
        examples,
        "_sealed_read",
        lambda *_args, **_kwargs: pytest.fail("a source was opened before output preflight"),
    )
    with pytest.raises(ValueError, match="new, non-symlink path"):
        runner()


@pytest.mark.parametrize(
    "script_name",
    ("chord_beat_cell_features.py", "chord_beat_cell_examples.py"),
)
def test_script_subprocess_imports_current_checkout_before_rejecting_dummy_flag(
    tmp_path: Path,
    script_name: str,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / script_name
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(script), "--dummy-path"],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "accepts no path" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    probe = f"""
import pathlib, runpy, sys
sys.argv = [{str(script)!r}, '--dummy-path']
try:
    runpy.run_path({str(script)!r}, run_name='__main__')
except SystemExit:
    pass
import steel_guitar_rag.chord_reader.beat_cell_examples as module
print(pathlib.Path(module.__file__).resolve())
"""
    imported = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    assert (
        Path(imported.stdout.strip())
        == (repo_root / "steel_guitar_rag" / "chord_reader" / "beat_cell_examples.py").resolve()
    )
