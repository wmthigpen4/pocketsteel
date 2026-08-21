from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from steel_guitar_rag.chord_reader import beat_cell_readiness as readiness
from steel_guitar_rag.chord_reader import beat_cell_readiness_recovery_contract as recovery_contract
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.beat_cell_readiness_recovery_contract import (
    load_readiness_recovery_authority,
)
from steel_guitar_rag.chord_reader.beat_cell_stage2_contract import (
    load_beat_cell_stage2_authority,
)


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _funnel(rows: list[dict]) -> dict:
    count = {
        "T": len(rows),
        "U": 0,
        "R": len(rows),
        "N": 0,
        "E": len(rows),
        "C": sum(row["correct"] for row in rows),
        "I": sum(not row["correct"] for row in rows),
    }
    duration = {
        "T": sum(row["durationMilliseconds"] for row in rows),
        "U": 0,
        "R": sum(row["durationMilliseconds"] for row in rows),
        "N": 0,
        "E": sum(row["durationMilliseconds"] for row in rows),
        "C": sum(row["durationMilliseconds"] for row in rows if row["correct"]),
        "I": sum(row["durationMilliseconds"] for row in rows if not row["correct"]),
    }
    return readiness.make_funnel(count, duration)


def _synthetic_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, dict, dict, dict, dict]:
    authority = deepcopy(load_beat_cell_stage2_authority())
    recovery = deepcopy(load_readiness_recovery_authority())
    feature_names = list(authority["featureMath"]["featureNames"])
    dataset_roles = [
        ("aam", "aam:mix:0", None),
        ("aam", "aam:mix:1", None),
        ("guitarset", "guitarset:comp:player-00", "comp"),
        ("guitarset", "guitarset:solo:player-00", "solo"),
        ("idmt_guitar", "idmt:mix:0", None),
        ("idmt_guitar", "idmt:mix:1", None),
        ("nrgcp", "nrg:mix:0", None),
        ("nrgcp", "nrg:mix:1", None),
        ("winterreise", "winter:mix:0", None),
        ("winterreise", "winter:mix:1", None),
    ]
    durations = [100, 110, 120, 130, 140, 900, 160, 170, 180, 190]
    tracks: list[dict] = []
    examples_rows: list[dict] = []
    for index, ((dataset_id, role, guitarset_role), duration) in enumerate(zip(dataset_roles, durations, strict=True)):
        track_id = f"synthetic-track-{index:02d}"
        group = f"synthetic-group-{index:02d}"
        correct = index < 6
        source_cell = _digest(f"cell:{index}")
        outcome_payload = {
            "cellIndex": 0,
            "durationMilliseconds": duration,
            "sourceBeatCellSha256": source_cell,
            "classification": "C" if correct else "I",
        }
        outcome = {**outcome_payload, "rowSha256": canonical_sha256(outcome_payload)}
        group_row_sha = _digest(f"group-row:{index}")
        prediction_sha = _digest(f"prediction:{index}")
        audio_lineage_sha = _digest(f"audio-lineage:{index}")
        tracks.append(
            {
                "trackId": track_id,
                "datasetId": dataset_id,
                "role": role,
                "guitarsetRole": guitarset_role,
                "confidenceGroupId": group,
                "sourceGroupTrackMetadataSha256": group_row_sha,
                "predictionIdentitySha256": prediction_sha,
                "predictionIdentity": {"audioLineageRowSha256": audio_lineage_sha},
                "cellOutcomes": [outcome],
            }
        )
        feature_values = {
            name: float(index) + feature_index / 100.0
            for feature_index, name in sorted(enumerate(feature_names), key=lambda item: item[1])
        }
        feature_values.update(
            {
                "predictionTransitionCount": index % 3,
                "productFamilyNone": 0,
                "productFamilyMajor": 1,
                "productFamilyMinor": 0,
                "productFamilyDominant": 0,
                "productFamilyMinorSeventh": 0,
            }
        )
        example_payload = {
            "schemaVersion": "synthetic-example",
            "exampleKey": f"{index:064x}",
            "trackId": track_id,
            "cellIndex": 0,
            "durationMilliseconds": duration,
            "sourceBeatCellSha256": source_cell,
            "predictionIdentitySha256": prediction_sha,
            "featureRowSha256": _digest(f"feature-row:{index}"),
            "featureSummaryArtifactSha256": _digest(f"feature-summary:{index}"),
            "featureSetArtifactSha256": _digest("feature-set"),
            "audioLineageRowSha256": audio_lineage_sha,
            "featureValues": feature_values,
            "featureValuesSha256": canonical_sha256(feature_values),
            "stage1OutcomeRowSha256": outcome["rowSha256"],
            "stage1ArtifactSha256": "",
            "sourceGroupTrackRowSha256": group_row_sha,
            "datasetId": dataset_id,
            "role": role,
            "guitarsetRole": guitarset_role,
            "confidenceGroupId": group,
            "correct": correct,
        }
        examples_rows.append(example_payload)

    aggregate_funnel = _funnel(examples_rows)
    dataset_rows = []
    for dataset_id in readiness.DATASET_IDS:
        funnel = _funnel([row for row in examples_rows if row["datasetId"] == dataset_id])
        payload = {
            "datasetId": dataset_id,
            "trackCount": sum(row["datasetId"] == dataset_id for row in examples_rows),
            "funnel": funnel,
            "funnelSha256": funnel["funnelSha256"],
        }
        dataset_rows.append({**payload, "rowSha256": canonical_sha256(payload)})
    guitar_rows = [row for row in examples_rows if row["datasetId"] == "guitarset"]
    guitar_funnel = _funnel(guitar_rows)
    role_rows = []
    for role in readiness.GUITARSET_ROLES:
        funnel = _funnel([row for row in guitar_rows if row["guitarsetRole"] == role])
        payload = {
            "guitarsetRole": role,
            "trackCount": sum(row["guitarsetRole"] == role for row in guitar_rows),
            "funnel": funnel,
            "funnelSha256": funnel["funnelSha256"],
        }
        role_rows.append({**payload, "rowSha256": canonical_sha256(payload)})
    reference_audit_payload = {"schemaVersion": "synthetic-reference-audit"}
    reference_audit = {
        **reference_audit_payload,
        "auditSha256": canonical_sha256(reference_audit_payload),
    }
    stage1 = {
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "stage1Passed": True,
        "calibrationMayOpenOnce": False,
        "tracks": tracks,
        "aggregate": aggregate_funnel,
        "datasets": dataset_rows,
        "guitarset": {
            "trackCount": len(guitar_rows),
            "funnel": guitar_funnel,
            "funnelSha256": guitar_funnel["funnelSha256"],
            "compSolo": role_rows,
            "compSoloSetSha256": canonical_sha256(role_rows),
            "roleSpecificGates": False,
        },
        "referenceEndpointReconciliationAudit": reference_audit,
        "referenceEndpointReconciliationAuditSha256": reference_audit["auditSha256"],
        "artifactSha256": _digest("stage1-artifact"),
    }
    for row in examples_rows:
        row["stage1ArtifactSha256"] = stage1["artifactSha256"]
        row["exampleSha256"] = canonical_sha256(row)
    label_audits = readiness._expected_label_audits(examples_rows, stage1)
    examples = {
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "featureNames": feature_names,
        "examples": examples_rows,
        "labelAudits": label_audits,
        "labelAuditsSha256": label_audits["auditSha256"],
        "referenceEndpointReconciliationAudit": reference_audit,
        "referenceEndpointReconciliationAuditSha256": reference_audit["auditSha256"],
        "sourceFeatureSetFileSha256": _digest("feature-set-file"),
        "sourceFeatureSetArtifactSha256": _digest("feature-set"),
        "sourceFeatureSummarySetSha256": _digest("feature-summary-set"),
        "sourceFeatureRowSetSha256": _digest("feature-row-set"),
        "artifactSha256": _digest("examples-artifact"),
    }
    probabilities = [0.99, 0.98, 0.97, 0.96, 0.50, 0.50, 0.40, 0.30, 0.20, 0.10]
    oof_rows = [
        {
            "exampleKey": row["exampleKey"],
            "trackId": row["trackId"],
            "cellIndex": row["cellIndex"],
            "durationMilliseconds": row["durationMilliseconds"],
            "datasetId": row["datasetId"],
            "role": row["role"],
            "guitarsetRole": row["guitarsetRole"],
            "confidenceGroupId": row["confidenceGroupId"],
            "outerFold": index % 5,
            "probability": probabilities[index],
            "correct": row["correct"],
            "sampleWeight": 1.0,
        }
        for index, row in enumerate(examples_rows)
    ]
    curve_rows = [
        {
            "exampleKey": row["exampleKey"],
            "probability": row["probability"],
            "correct": row["correct"],
            "sampleWeight": row["sampleWeight"],
        }
        for row in oof_rows
    ]
    precision_coverage = readiness._precision_coverage(
        curve_rows, authority["selectorCore"]["precisionCoverageTargets"]
    )
    selector = {
        "schemaVersion": readiness.BEAT_CELL_SELECTOR_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "operatingThreshold": None,
        "training": {"split": "development", "oofAuditRows": oof_rows},
        "outOfFoldEvaluation": {
            "estimand": readiness.BEAT_CELL_SELECTOR_ESTIMAND,
            "denominator": readiness.BEAT_CELL_SELECTOR_OOF_DENOMINATOR,
            "denominatorExampleCount": len(oof_rows),
            "denominatorDurationMilliseconds": sum(durations),
            "groupBalancedLogLoss": readiness._group_log_loss(curve_rows),
            "groupBalancedBrierScore": readiness._group_brier(curve_rows),
            "groupBalancedAreaUnderRiskCoverage": readiness._aurc(curve_rows, group_weighted=True),
            "precisionCoveragePolicy": "fixed descriptive coverage targets; no operating threshold selected",
            "precisionCoverage": precision_coverage,
        },
        "estimator": {
            "imputationValues": [0.0] * len(feature_names),
            "center": [0.0] * len(feature_names),
            "scale": [1.0] * len(feature_names),
            "allMissingFeatureNames": [],
        },
    }
    selector["artifactSha256"] = canonical_sha256(selector)

    eligible_projection = sorted(
        [
            {
                "trackId": row["trackId"],
                "cellIndex": row["cellIndex"],
                "durationMilliseconds": row["durationMilliseconds"],
                "sourceBeatCellSha256": row["sourceBeatCellSha256"],
                "stage1OutcomeRowSha256": row["stage1OutcomeRowSha256"],
                "classification": "C" if row["correct"] else "I",
                "datasetId": row["datasetId"],
                "role": row["role"],
                "guitarsetRole": row["guitarsetRole"],
                "confidenceGroupId": row["confidenceGroupId"],
                "sourceGroupTrackRowSha256": row["sourceGroupTrackRowSha256"],
                "predictionIdentitySha256": row["predictionIdentitySha256"],
                "audioLineageRowSha256": row["audioLineageRowSha256"],
            }
            for row in examples_rows
        ],
        key=lambda row: (row["trackId"], row["cellIndex"]),
    )
    admission_payload = {
        "sourceStage1ArtifactSha256": stage1["artifactSha256"],
        "sourceStage1DecisionSha256": _digest("stage1-decision"),
        "sourceStage1GateSetSha256": _digest("stage1-gates"),
        "sourceStage1TrackSetSha256": _digest("stage1-tracks"),
        "sourceStage1SourceContractSha256": _digest("stage1-source-contract"),
        "allThirteenStage1GatesPassed": True,
        "eligibleOutcomeCount": len(eligible_projection),
        "eligibleOutcomeDurationMilliseconds": sum(durations),
        "eligibleOutcomeBindingSetSha256": canonical_sha256(eligible_projection),
        "aggregate": aggregate_funnel,
        "datasets": dataset_rows,
        "guitarset": stage1["guitarset"],
        "referenceEndpointReconciliationAudit": reference_audit,
        "referenceEndpointReconciliationAuditSha256": reference_audit["auditSha256"],
    }
    admission = {**admission_payload, "admissionSha256": canonical_sha256(admission_payload)}
    monkeypatch.setattr(
        readiness,
        "EXPECTED_STAGE1_ADMISSION_PROJECTION_SHA256",
        admission["admissionSha256"],
    )

    aggregate_count = aggregate_funnel["counts"]
    aggregate_duration = aggregate_funnel["durationMilliseconds"]
    guitar_count = guitar_funnel["counts"]
    guitar_duration = guitar_funnel["durationMilliseconds"]
    monkeypatch.setattr(readiness, "EXPECTED_STAGE1_AGGREGATE_COUNT", aggregate_count)
    monkeypatch.setattr(readiness, "EXPECTED_STAGE1_AGGREGATE_DURATION_MS", aggregate_duration)
    monkeypatch.setattr(readiness, "EXPECTED_STAGE1_GUITARSET_COUNT", guitar_count)
    monkeypatch.setattr(readiness, "EXPECTED_STAGE1_GUITARSET_DURATION_MS", guitar_duration)
    monkeypatch.setattr(
        readiness,
        "EXPECTED_DATASET_TRACK_COUNTS",
        {dataset_id: 2 for dataset_id in readiness.DATASET_IDS},
    )
    monkeypatch.setattr(
        readiness,
        "EXPECTED_GUITARSET_ROLE_TRACK_COUNTS",
        {role: 1 for role in readiness.GUITARSET_ROLES},
    )
    monkeypatch.setattr(
        readiness,
        "EXPECTED_GUITARSET_ROLE_REFERENCE_COUNTS",
        {row["guitarsetRole"]: row["funnel"]["counts"]["R"] for row in role_rows},
    )
    monkeypatch.setattr(
        readiness,
        "EXPECTED_GUITARSET_ROLE_REFERENCE_DURATION_MS",
        {row["guitarsetRole"]: row["funnel"]["durationMilliseconds"]["R"] for row in role_rows},
    )

    authority["stageB"]["expectedExampleCount"] = len(examples_rows)
    authority["stageB"]["expectedExampleDurationMilliseconds"] = sum(durations)
    authority["sourceInputs"]["stage1Report"] = {
        "path": str(tmp_path / "stage1.json"),
        "fileSha256": readiness._sha256_bytes(readiness._render_json(stage1)),
        "canonicalSha256": canonical_sha256(stage1),
        "artifactSha256": stage1["artifactSha256"],
        "decisionSha256": admission["sourceStage1DecisionSha256"],
        "gateSetSha256": admission["sourceStage1GateSetSha256"],
        "trackSetSha256": admission["sourceStage1TrackSetSha256"],
        "sourceContractSha256": admission["sourceStage1SourceContractSha256"],
    }
    authority["outputPaths"]["examplesArtifact"] = str(tmp_path / "examples.json")
    authority["outputPaths"]["selectorArtifact"] = str(tmp_path / "selector.json")
    authority["outputPaths"]["readinessReport"] = str(tmp_path / "r4-readiness.json")
    recovery["immutableInputs"] = {
        "stage1": {
            "path": str(tmp_path / "stage1.json"),
            "fileSha256": readiness._sha256_bytes(readiness._render_json(stage1)),
            "canonicalSha256": canonical_sha256(stage1),
            "artifactSha256": stage1["artifactSha256"],
        },
        "featureSet": {
            "manifestPath": str(tmp_path / "feature-set" / "manifest.json"),
            "manifestFileSha256": examples["sourceFeatureSetFileSha256"],
            "manifestCanonicalSha256": _digest("feature-set-canonical"),
            "artifactSha256": examples["sourceFeatureSetArtifactSha256"],
            "summarySetSha256": examples["sourceFeatureSummarySetSha256"],
            "featureRowSetSha256": examples["sourceFeatureRowSetSha256"],
        },
        "examples": {
            "path": str(tmp_path / "examples.json"),
            "fileSha256": readiness._sha256_bytes(readiness._render_json(examples)),
            "canonicalSha256": canonical_sha256(examples),
            "artifactSha256": examples["artifactSha256"],
            "exampleCount": len(examples_rows),
            "exampleDurationMilliseconds": sum(durations),
        },
        "selector": {
            "path": str(tmp_path / "selector.json"),
            "fileSha256": readiness._sha256_bytes(readiness._render_json(selector)),
            "canonicalSha256": canonical_sha256(selector),
            "artifactSha256": selector["artifactSha256"],
        },
    }
    recovery["output"]["readinessReport"] = str(tmp_path / "r5-readiness.json")
    authorization_payload = {
        "schemaVersion": readiness.READINESS_RECOVERY_AUTHORIZATION_SCHEMA,
        "recoveryId": recovery["recoveryId"],
        "implementation": {
            "implementationCommit": "a" * 40,
            "files": [],
            "handoffFileSha256": _digest("synthetic implementation handoff"),
        },
        "scope": {"synthetic": True},
        "forbiddenAccess": {"synthetic": False},
        "independentAudit": {"synthetic": "GO"},
        "userAuthorization": {"synthetic": True},
    }
    authorization = {
        **authorization_payload,
        "payloadSha256": canonical_sha256(authorization_payload),
    }
    authorization_path = tmp_path / "implementation-authorization.json"
    authorization_path.write_bytes(readiness._render_json(authorization))
    monkeypatch.setattr(readiness, "_authority_contract", lambda: deepcopy(authority))
    monkeypatch.setattr(readiness, "_recovery_contract", lambda: deepcopy(recovery))
    monkeypatch.setattr(
        readiness,
        "_implementation_authorization_receipt",
        lambda: deepcopy(authorization),
    )
    monkeypatch.setattr(readiness, "RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(readiness, "RECOVERY_AUTHORITY_CANONICAL_SHA256", canonical_sha256(recovery))
    monkeypatch.setattr(readiness, "RECOVERY_AUTHORITY_FILE_SHA256", _digest("synthetic recovery authority file"))
    monkeypatch.setattr(readiness, "recovery_authority_path", lambda: tmp_path / "recovery-authority.json")
    monkeypatch.setattr(
        readiness,
        "_validate_stage1_admission",
        lambda _stage1, _authority: deepcopy(admission),
    )
    monkeypatch.setattr(
        readiness,
        "_validate_examples_admission",
        lambda source, _authority, _admission: (deepcopy(dict(source)), list(feature_names)),
    )
    monkeypatch.setattr(readiness, "validate_beat_cell_selector_artifact", lambda *_args: {})
    return stage1, examples, selector, authority, recovery


def _synthetic_readiness_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    stage1, examples, selector, _authority, _recovery = _synthetic_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(readiness, "train_beat_cell_selector", lambda _source: deepcopy(selector))
    return readiness.evaluate_beat_cell_readiness(stage1, examples, selector)


def _reseal(value: dict, field: str) -> None:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})


def _write_synthetic_sources(tmp_path: Path, stage1: dict, examples: dict, selector: dict) -> None:
    (tmp_path / "stage1.json").write_bytes(readiness._render_json(stage1))
    (tmp_path / "examples.json").write_bytes(readiness._render_json(examples))
    (tmp_path / "selector.json").write_bytes(readiness._render_json(selector))


def _synthetic_execution_authorization(monkeypatch: pytest.MonkeyPatch) -> dict:
    file_bytes = {path: f"synthetic:{path}".encode() for path in recovery_contract._AUTHORIZATION_FILE_PATHS}
    handoff_bytes = b"synthetic readiness recovery handoff"

    def sealed(path: Path, _name: str) -> bytes:
        relative = str(path.relative_to(recovery_contract._repo_root()))
        if relative == str(recovery_contract.READINESS_RECOVERY_IMPLEMENTATION_HANDOFF_RELATIVE_PATH):
            return handoff_bytes
        return file_bytes[relative]

    monkeypatch.setattr(recovery_contract, "_sealed_read", sealed)
    payload = {
        "schemaVersion": recovery_contract.READINESS_RECOVERY_AUTHORIZATION_SCHEMA,
        "recoveryId": recovery_contract.READINESS_RECOVERY_ID,
        "split": "development",
        "executionAuthorized": True,
        "baseAuthority": {
            "path": str(recovery_contract.READINESS_RECOVERY_AUTHORITY_RELATIVE_PATH),
            "fileSha256": recovery_contract.READINESS_RECOVERY_AUTHORITY_FILE_SHA256,
            "canonicalSha256": recovery_contract.READINESS_RECOVERY_AUTHORITY_CANONICAL_SHA256,
        },
        "consumedFailure": {
            "path": str(recovery_contract.READINESS_RECOVERY_FAILURE_RECEIPT_RELATIVE_PATH),
            "fileSha256": recovery_contract.READINESS_RECOVERY_FAILURE_RECEIPT_FILE_SHA256,
        },
        "implementation": {
            "implementationCommit": "a" * 40,
            "files": [
                {"path": path, "fileSha256": readiness._sha256_bytes(file_bytes[path])}
                for path in recovery_contract._AUTHORIZATION_FILE_PATHS
            ],
            "handoffPath": str(recovery_contract.READINESS_RECOVERY_IMPLEMENTATION_HANDOFF_RELATIVE_PATH),
            "handoffFileSha256": readiness._sha256_bytes(handoff_bytes),
        },
        "scope": {
            "outputPath": str(recovery_contract.READINESS_RECOVERY_OUTPUT),
            "publicationMode": readiness.PUBLICATION_MODE,
            "newCycle": {
                key: value
                for key, value in readiness._RECOVERY_NEW_CYCLE_COUNTS.items()
                if key != "sameCycleRetryAllowed"
            },
            "cumulativeIncludingConsumedR4": deepcopy(readiness._RECOVERY_CUMULATIVE_COUNTS),
            "sameCycleRetryAllowed": False,
            "stopAfterReadinessForIndependentAudit": True,
        },
        "forbiddenAccess": {field: False for field in recovery_contract._FORBIDDEN_FIELDS},
        "independentAudit": {"verdict": "GO", "noP0P1": True, "qaPassed": True, "auditorCount": 2},
        "userAuthorization": {
            "explicitlyApproved": True,
            "approvalScope": "one-r5-readiness-only-evaluation-and-one-reproduction-refit-no-retry",
            "approvalRecordedAt": "2026-08-21T13:30:00-05:00",
        },
    }
    return {**payload, "payloadSha256": canonical_sha256(payload)}


def _mixed_feature_readiness_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict, dict[str, int | float]]:
    stage1, examples, selector, authority, recovery = _synthetic_fixture(tmp_path, monkeypatch)
    feature_names = list(authority["featureMath"]["featureNames"])
    feature_values: dict[str, int | float] = {name: index + 0.125 for index, name in enumerate(feature_names)}
    feature_values.update(
        {
            "predictionTransitionCount": 2,
            "productFamilyNone": 0,
            "productFamilyMajor": 1,
            "productFamilyMinor": 0,
            "productFamilyDominant": 0,
            "productFamilyMinorSeventh": 0,
        }
    )
    example = examples["examples"][0]
    example["featureValues"] = feature_values
    example["featureValuesSha256"] = canonical_sha256(feature_values)
    _reseal(example, "exampleSha256")
    recovery["immutableInputs"]["examples"].update(
        {
            "fileSha256": readiness._sha256_bytes(readiness._render_json(examples)),
            "canonicalSha256": canonical_sha256(examples),
        }
    )
    monkeypatch.setattr(readiness, "RECOVERY_AUTHORITY_CANONICAL_SHA256", canonical_sha256(recovery))
    monkeypatch.setattr(readiness, "train_beat_cell_selector", lambda _source: deepcopy(selector))
    return readiness.evaluate_beat_cell_readiness(stage1, examples, selector), feature_values


def test_fixed_half_coverage_includes_complete_exact_tie_block() -> None:
    rows = [
        {"exampleKey": f"{index:064x}", "probability": probability, "correct": True, "sampleWeight": 1.0}
        for index, probability in enumerate((0.9, 0.8, 0.5, 0.5, 0.1, 0.0))
    ]
    point = readiness._precision_coverage(rows, [0.50])[0]
    assert point["minimumProbabilityAtDescriptivePoint"] == 0.5
    assert point["realizableCoverage"] == pytest.approx(4 / 6)
    assert sum(row["probability"] >= point["minimumProbabilityAtDescriptivePoint"] for row in rows) == 4


def test_duration_gates_are_exact_and_independent_of_passing_count_gates() -> None:
    aggregate = {
        "acceptedCount": 5000,
        "acceptedCorrectCount": 4950,
        "referenceDeterminateCount": 9789,
        "acceptedDurationMilliseconds": 100,
        "acceptedCorrectDurationMilliseconds": 99,
        "referenceDeterminateDurationMilliseconds": 5316104,
        "oneSidedWilson95LowerBound": readiness._wilson_lower(4950, 5000),
        "groupBalancedConditionalCoverage": 0.50,
        "groupBalancedPrecision": 0.98,
    }
    guitar = {
        "acceptedCount": 600,
        "acceptedCorrectCount": 594,
        "referenceDeterminateCount": 2218,
        "acceptedDurationMilliseconds": 100,
        "acceptedCorrectDurationMilliseconds": 99,
        "referenceDeterminateDurationMilliseconds": 1034199,
        "oneSidedWilson95LowerBound": readiness._wilson_lower(594, 600),
        "groupBalancedConditionalCoverage": 0.25,
        "groupBalancedPrecision": 0.98,
    }
    gates = readiness._build_readiness_gates(aggregate, guitar)
    by_id = {gate["gateId"]: gate for gate in gates}
    assert len(gates) == 15
    assert all(by_id[gate_id]["passed"] for gate_id in readiness._COUNT_GATE_IDS)
    assert not by_id["aggregate.duration-end-to-end-coverage"]["passed"]
    assert not by_id["guitarset.duration-end-to-end-coverage"]["passed"]
    assert by_id["aggregate.duration-micro-precision"]["passed"]
    assert by_id["guitarset.duration-micro-precision"]["passed"]
    assert not any("comp" in gate["gateId"] or "solo" in gate["gateId"] for gate in gates)


def test_mapping_evaluation_refits_once_preserves_canonical_feature_projection_and_validates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage1, examples, selector, _authority, _recovery = _synthetic_fixture(tmp_path, monkeypatch)
    calls = 0

    def reproduce(source: dict) -> dict:
        nonlocal calls
        calls += 1
        assert source == examples
        return deepcopy(selector)

    monkeypatch.setattr(readiness, "train_beat_cell_selector", reproduce)
    artifact = readiness.evaluate_beat_cell_readiness(stage1, examples, selector)
    assert calls == 1
    assert artifact["schemaVersion"].endswith("_v2")
    assert artifact["recoveryId"] == "beat-cell-stage2-r5-readiness-only"
    assert artifact["publication"]["outputPath"].endswith("/r5-readiness.json")
    assert artifact["sourceAuthorityBinding"]["fileSha256"] == readiness.AUTHORITY_FILE_SHA256
    assert artifact["recoveryAuthorityBinding"]["fileSha256"] == readiness.RECOVERY_AUTHORITY_FILE_SHA256
    assert artifact["inputBindings"]["schemaVersion"].endswith("_v2")
    assert (
        artifact["inputBindings"]["sourceAuthorityBindingSha256"] == artifact["sourceAuthorityBinding"]["bindingSha256"]
    )
    assert (
        artifact["inputBindings"]["recoveryAuthorityBindingSha256"]
        == artifact["recoveryAuthorityBinding"]["bindingSha256"]
    )
    assert artifact["joinedOofRows"][0]["schemaVersion"].endswith("_v2")
    assert artifact["oneShot"]["newCycle"] == readiness._RECOVERY_NEW_CYCLE_COUNTS
    assert artifact["oneShot"]["cumulativeIncludingConsumedR4"] == readiness._RECOVERY_CUMULATIVE_COUNTS
    assert artifact["oneShot"]["sourceR4SameCycleRetryPerformed"] is False
    assert artifact["oneShot"]["immutableR4ArtifactsReused"] is True
    assert artifact["reproduction"]["readinessReproductionRefitCount"] == 1
    assert artifact["fixedDevelopmentCutoff"]["targetCoverage"] == 0.50
    assert artifact["fixedDevelopmentCutoff"]["minimumProbabilityAtDescriptivePoint"] == 0.50
    assert sum(row["acceptedAtFixedDevelopmentCutoff"] for row in artifact["joinedOofRows"]) == 6
    assert artifact["guitarset"]["roleSpecificGates"] is False
    assert artifact["guitarset"]["soloDeploymentAuthorized"] is False
    assert [row["sliceId"] for row in artifact["guitarset"]["compSolo"]] == [
        "guitarset-role:comp",
        "guitarset-role:solo",
    ]
    assert readiness.validate_beat_cell_readiness_artifact(artifact) == artifact


def test_synthetic_official_runner_reuses_r4_inputs_and_publishes_only_r5(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage1, examples, selector, authority, recovery = _synthetic_fixture(tmp_path, monkeypatch)
    _write_synthetic_sources(tmp_path, stage1, examples, selector)
    source_bytes = {name: (tmp_path / f"{name}.json").read_bytes() for name in ("stage1", "examples", "selector")}
    calls = 0

    def reproduce(source: dict) -> dict:
        nonlocal calls
        calls += 1
        assert source == examples
        return deepcopy(selector)

    monkeypatch.setattr(readiness, "train_beat_cell_selector", reproduce)
    artifact = readiness.run_beat_cell_readiness()

    assert calls == 1
    assert Path(recovery["output"]["readinessReport"]).read_bytes() == readiness._render_json(artifact)
    assert not Path(authority["outputPaths"]["readinessReport"]).exists()
    assert {
        name: (tmp_path / f"{name}.json").read_bytes() for name in ("stage1", "examples", "selector")
    } == source_bytes


def test_runner_rejects_immutable_receipt_drift_before_refit_or_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage1, examples, selector, _authority, recovery = _synthetic_fixture(tmp_path, monkeypatch)
    _write_synthetic_sources(tmp_path, stage1, examples, selector)
    recovery["immutableInputs"]["examples"]["fileSha256"] = _digest("wrong immutable examples file")
    called = False

    def forbidden(_source: dict) -> dict:
        nonlocal called
        called = True
        raise AssertionError("refit reached after immutable receipt drift")

    monkeypatch.setattr(readiness, "train_beat_cell_selector", forbidden)
    with pytest.raises(readiness.BeatCellReadinessError, match="immutable R4 examples receipt drifted"):
        readiness.run_beat_cell_readiness()
    assert called is False
    assert not Path(recovery["output"]["readinessReport"]).exists()


def test_runner_never_wires_or_overwrites_consumed_r4_readiness_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage1, examples, selector, authority, recovery = _synthetic_fixture(tmp_path, monkeypatch)
    _write_synthetic_sources(tmp_path, stage1, examples, selector)
    r4_output = Path(authority["outputPaths"]["readinessReport"])
    r4_output.write_bytes(b"foreign-r4-output")
    monkeypatch.setattr(
        readiness,
        "train_beat_cell_selector",
        lambda _source: pytest.fail("refit reached after consumed R4 output appeared"),
    )

    with pytest.raises(readiness.BeatCellReadinessError, match="consumed R4 readiness path"):
        readiness.run_beat_cell_readiness()
    assert r4_output.read_bytes() == b"foreign-r4-output"
    assert not Path(recovery["output"]["readinessReport"]).exists()


def test_exact_complete_stage1_admission_projection_receipt_is_frozen() -> None:
    assert (
        readiness.EXPECTED_STAGE1_ADMISSION_PROJECTION_SHA256
        == "9819e8a3c639179a04246c53e59ea85627178e33dd6a51d2e412a63082309be9"
    )


@pytest.mark.parametrize("field", ("schemaVersion", "featureSet", "singleJson"))
def test_readiness_rejects_split_publication_policy_tamper_before_artifact_access(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    authority = deepcopy(load_beat_cell_stage2_authority())
    authority["outputPaths"]["publication"][field] = "resealed-but-weakened"
    monkeypatch.setattr(readiness, "load_beat_cell_stage2_authority", lambda: deepcopy(authority))
    monkeypatch.setattr(readiness, "AUTHORITY_CANONICAL_SHA256", canonical_sha256(authority))
    with pytest.raises(readiness.BeatCellReadinessError, match="exact frozen split policy"):
        readiness._authority_contract()


def test_r5_preregistration_stays_fail_closed_without_separate_implementation_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert readiness.READINESS_RECOVERY_AUTHORIZATION_SCHEMA == (
        "chord_runtime_beat_cell_stage2_readiness_recovery_implementation_authorization_v1"
    )
    assert readiness.RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH == (
        Path(readiness.__file__).resolve().parents[2] / "docs/handoffs/task-completions/"
        "2026-08-21-1330-20-beat-cell-stage2-r5-readiness-only-implementation-authorization.json"
    )
    touched = False

    def forbidden(*_args: object, **_kwargs: object) -> object:
        nonlocal touched
        touched = True
        raise AssertionError("an immutable experiment input was opened before authorization")

    monkeypatch.setattr(readiness, "_read_json", forbidden)
    with pytest.raises(readiness.BeatCellReadinessError, match="authorization receipt is not installed"):
        readiness.run_beat_cell_readiness()
    assert touched is False


def test_execution_authorization_rejects_boolean_one_shot_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _synthetic_execution_authorization(monkeypatch)
    assert recovery_contract.validate_readiness_recovery_authorization(receipt) == receipt
    changed = deepcopy(receipt)
    changed["scope"]["newCycle"]["readinessEvaluationCount"] = True
    changed["payloadSha256"] = canonical_sha256(
        {key: value for key, value in changed.items() if key != "payloadSha256"}
    )
    with pytest.raises(
        recovery_contract.BeatCellReadinessRecoveryContractError,
        match="exact integers",
    ):
        recovery_contract.validate_readiness_recovery_authorization(changed)


def test_publication_barrier_rejects_authorization_receipt_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage1, examples, selector, _authority, recovery = _synthetic_fixture(tmp_path, monkeypatch)
    _write_synthetic_sources(tmp_path, stage1, examples, selector)
    monkeypatch.setattr(readiness, "train_beat_cell_selector", lambda _source: deepcopy(selector))

    def interposed_publish(_path: Path, _artifact: dict, *, precommit_check: object) -> None:
        Path(readiness.RECOVERY_IMPLEMENTATION_AUTHORIZATION_PATH).write_bytes(b"foreign authorization")
        precommit_check()

    monkeypatch.setattr(readiness, "_publish_new_json", interposed_publish)
    with pytest.raises(readiness.BeatCellReadinessError, match="implementation authorization"):
        readiness.run_beat_cell_readiness()
    assert not Path(recovery["output"]["readinessReport"]).exists()


@pytest.mark.parametrize(
    ("tamper", "message"),
    [
        ("source-authority", "exact R4 source authority"),
        ("output-overlap", "overlaps an immutable R4 input"),
        ("frozen-cutoff", "frozen R4 readiness policy"),
        ("new-count", "one-shot counts"),
        ("cumulative-count", "one-shot counts"),
        ("reuse", "immutable-reuse policy"),
        ("forbidden", "forbidden surface"),
        ("base-execution", "receipt-neutral"),
    ],
)
def test_recovery_contract_rejects_coherently_resealed_authority_tamper(
    tamper: str, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    recovery = deepcopy(load_readiness_recovery_authority())
    if tamper == "source-authority":
        recovery["sourceCycle"]["authorityFileSha256"] = _digest("wrong source authority")
    elif tamper == "output-overlap":
        recovery["output"]["readinessReport"] = recovery["immutableInputs"]["examples"]["path"]
    elif tamper == "frozen-cutoff":
        recovery["frozenPolicy"]["fixedTargetCoverage"] = 0.75
    elif tamper == "new-count":
        recovery["oneShot"]["newCycle"]["selectorCandidateCount"] = 1
    elif tamper == "cumulative-count":
        recovery["oneShot"]["cumulativeIncludingConsumedR4"]["readinessEvaluationCount"] = 1
    elif tamper == "reuse":
        recovery["oneShot"]["immutableR4ArtifactsMustBeReused"] = False
    elif tamper == "forbidden":
        recovery["forbiddenAccess"]["calibration"] = True
    else:
        recovery["implementation"]["executionAuthorized"] = True
    monkeypatch.setattr(readiness, "load_readiness_recovery_authority", lambda: deepcopy(recovery))
    monkeypatch.setattr(readiness, "RECOVERY_AUTHORITY_CANONICAL_SHA256", canonical_sha256(recovery))

    with pytest.raises(readiness.BeatCellReadinessError, match=message):
        readiness._recovery_contract()


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    [
        ("newCycle", "readinessEvaluationCount", 2),
        ("cumulativeIncludingConsumedR4", "readinessReproductionRefitCount", 1),
        (None, "immutableR4ArtifactsReused", False),
        (None, "sourceR4SameCycleRetryPerformed", True),
    ],
)
def test_standalone_v2_validator_rejects_resealed_recovery_count_or_reuse_tamper(
    section: str | None,
    field: str,
    replacement: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    target = changed["oneShot"] if section is None else changed["oneShot"][section]
    target[field] = replacement
    _reseal(changed["oneShot"], "auditSha256")
    _reseal(changed, "artifactSha256")

    with pytest.raises(readiness.BeatCellReadinessError, match="one-shot policy is stale"):
        readiness.validate_beat_cell_readiness_artifact(changed)


@pytest.mark.parametrize(
    ("binding_name", "digest_field", "input_link"),
    [
        ("sourceAuthorityBinding", "fileSha256", "sourceAuthorityBindingSha256"),
        ("recoveryAuthorityBinding", "fileSha256", "recoveryAuthorityBindingSha256"),
        (
            "implementationAuthorizationBinding",
            "handoffFileSha256",
            "implementationAuthorizationBindingSha256",
        ),
    ],
)
def test_standalone_v2_validator_rejects_coherently_resealed_authorization_binding_tamper(
    binding_name: str,
    digest_field: str,
    input_link: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    binding = changed[binding_name]
    binding[digest_field] = _digest(f"tampered {binding_name}")
    _reseal(binding, "bindingSha256")
    changed["inputBindings"][input_link] = binding["bindingSha256"]
    _reseal(changed["inputBindings"], "bindingsSha256")
    _reseal(changed, "artifactSha256")

    with pytest.raises(readiness.BeatCellReadinessError, match=binding_name):
        readiness.validate_beat_cell_readiness_artifact(changed)


@pytest.mark.parametrize("diagnostic", ["outer-fold-slice", "feature-missingness", "feature-z"])
def test_standalone_validator_recomputes_every_mandatory_diagnostic(
    diagnostic: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _synthetic_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    if diagnostic == "outer-fold-slice":
        changed["diagnostics"]["slices"]["outerFolds"][0]["acceptedCount"] += 1
    elif diagnostic == "feature-missingness":
        changed["diagnostics"]["featureDrift"]["featureMissingness"][0]["missingCount"] += 1
    else:
        changed["diagnostics"]["featureDrift"]["standardizedAbsoluteZ"]["aggregate"]["fractionAbove3"] = 0.125
    changed["diagnosticsSha256"] = canonical_sha256(changed["diagnostics"])
    _reseal(changed, "artifactSha256")
    with pytest.raises(readiness.BeatCellReadinessError):
        readiness.validate_beat_cell_readiness_artifact(changed)


@pytest.mark.parametrize("target", ["reliability-extra-field", "endpoint-duration-gate-input"])
def test_standalone_validator_rejects_coherently_resealed_diagnostic_scope_tampering(
    target: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _synthetic_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    if target == "reliability-extra-field":
        changed["diagnostics"]["reliability"]["durationWeightingUsed"] = True
    else:
        disclosure = changed["diagnostics"]["referenceEndpointReconciliation"]
        disclosure["durationGateInput"] = True
        _reseal(disclosure, "disclosureSha256")
    changed["diagnosticsSha256"] = canonical_sha256(changed["diagnostics"])
    _reseal(changed, "artifactSha256")
    with pytest.raises(readiness.BeatCellReadinessError):
        readiness.validate_beat_cell_readiness_artifact(changed)


@pytest.mark.parametrize(
    ("target", "field", "replacement", "nested_hash"),
    [
        ("publication", "mode", "resealed-but-weakened", None),
        ("fixedDevelopmentCutoff", "acceptanceRule", "probability > cutoff", None),
        ("countAudit", "identitiesReconciled", False, "auditSha256"),
        ("durationAudit", "unit", "seconds", "auditSha256"),
        ("reproduction", "selectorArtifactValidationPassed", False, "reproductionSha256"),
        ("oneShot", "selectorCandidateCount", 2, "auditSha256"),
        ("decision", "validationPassed", False, "decisionSha256"),
        ("storedMetricRecomputation", "selectorValidatorPassed", False, "auditSha256"),
    ],
)
def test_standalone_validator_rejects_coherently_resealed_policy_and_audit_tampering(
    target: str,
    field: str,
    replacement: object,
    nested_hash: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _synthetic_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    changed[target][field] = replacement
    if nested_hash is not None:
        _reseal(changed[target], nested_hash)
    _reseal(changed, "artifactSha256")
    with pytest.raises(readiness.BeatCellReadinessError):
        readiness.validate_beat_cell_readiness_artifact(changed)


def test_standalone_validator_rejects_coherently_resealed_stage1_stratum_splice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _synthetic_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    dataset = changed["stage1Admission"]["datasets"][0]
    dataset["trackCount"] += 1
    _reseal(dataset, "rowSha256")
    _reseal(changed["stage1Admission"], "admissionSha256")
    _reseal(changed, "artifactSha256")
    with pytest.raises(readiness.BeatCellReadinessError, match="admission self-hash"):
        readiness.validate_beat_cell_readiness_artifact(changed)


def test_reproduction_mismatch_fails_after_exactly_one_refit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage1, examples, selector, _authority, _recovery = _synthetic_fixture(tmp_path, monkeypatch)
    calls = 0

    def mismatch(_source: dict) -> dict:
        nonlocal calls
        calls += 1
        changed = deepcopy(selector)
        changed["artifactSha256"] = _digest("different-selector")
        return changed

    monkeypatch.setattr(readiness, "train_beat_cell_selector", mismatch)
    with pytest.raises(readiness.BeatCellReadinessError, match="object-identical"):
        readiness.evaluate_beat_cell_readiness(stage1, examples, selector)
    assert calls == 1


def test_protected_split_fails_before_validators_or_refit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage1, examples, selector, _authority, _recovery = _synthetic_fixture(tmp_path, monkeypatch)
    stage1["split"] = "test"
    touched = False

    def forbidden(*_args: object) -> object:
        nonlocal touched
        touched = True
        raise AssertionError("protected nested validator/refit was reached")

    monkeypatch.setattr(readiness, "_validate_stage1_admission", forbidden)
    monkeypatch.setattr(readiness, "train_beat_cell_selector", forbidden)
    with pytest.raises(readiness.BeatCellReadinessError, match="development-only"):
        readiness.evaluate_beat_cell_readiness(stage1, examples, selector)
    assert touched is False


def test_exact_stage1_per_cell_outcome_splice_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage1, examples, _selector, _authority, _recovery = _synthetic_fixture(tmp_path, monkeypatch)
    readiness._crosscheck_examples_stage1(
        examples,
        stage1,
        readiness._validate_stage1_admission(stage1, _authority),
    )
    changed = deepcopy(examples)
    changed["examples"][0]["stage1OutcomeRowSha256"] = changed["examples"][1]["stage1OutcomeRowSha256"]
    with pytest.raises(readiness.BeatCellReadinessError, match="spliced"):
        readiness._crosscheck_examples_stage1(
            changed,
            stage1,
            readiness._validate_stage1_admission(stage1, _authority),
        )


def test_standalone_validator_rejects_resealed_stage1_outcome_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage1, examples, selector, _authority, _recovery = _synthetic_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(readiness, "train_beat_cell_selector", lambda _source: deepcopy(selector))
    artifact = readiness.evaluate_beat_cell_readiness(stage1, examples, selector)
    changed = deepcopy(artifact)
    first = changed["joinedOofRows"][0]
    second = changed["joinedOofRows"][1]
    first["stage1OutcomeRowSha256"], second["stage1OutcomeRowSha256"] = (
        second["stage1OutcomeRowSha256"],
        first["stage1OutcomeRowSha256"],
    )
    for row in (first, second):
        row["rowSha256"] = canonical_sha256({key: value for key, value in row.items() if key != "rowSha256"})
    changed["joinedOofRowSetSha256"] = canonical_sha256(changed["joinedOofRows"])
    changed["artifactSha256"] = canonical_sha256(
        {key: value for key, value in changed.items() if key != "artifactSha256"}
    )
    with pytest.raises(readiness.BeatCellReadinessError, match="per-cell outcome binding"):
        readiness.validate_beat_cell_readiness_artifact(changed)


def test_canonical_disk_roundtrip_does_not_turn_object_key_order_into_feature_order(
    tmp_path: Path,
) -> None:
    authority = load_beat_cell_stage2_authority()
    names = list(authority["featureMath"]["featureNames"])
    values = {name: float(index) for index, name in sorted(enumerate(names), key=lambda item: item[1])}
    values.update(
        {
            "predictionTransitionCount": 2,
            "productFamilyNone": 0,
            "productFamilyMajor": 1,
            "productFamilyMinor": 0,
            "productFamilyDominant": 0,
            "productFamilyMinorSeventh": 0,
        }
    )
    example = {
        "featureValues": values,
        "featureValuesSha256": canonical_sha256(values),
    }
    path = tmp_path / "example.json"
    path.write_bytes(readiness._render_json(example))
    loaded, raw, _stat = readiness._read_json(path, "synthetic example")
    readiness._canonical_file(loaded, raw, "synthetic example")
    vector = readiness._feature_vector(loaded, names, _digest("example-key"))
    assert vector == [values[name] for name in names]
    assert list(loaded["featureValues"]) == sorted(names)
    assert list(loaded["featureValues"]) != names


def test_mixed_official_feature_types_survive_builder_and_validator_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact, feature_values = _mixed_feature_readiness_artifact(tmp_path, monkeypatch)
    feature_names = artifact["featureNames"]
    row = artifact["joinedOofRows"][0]

    assert row["orderedFeatureValues"] == [feature_values[name] for name in feature_names]
    for name in (
        "predictionTransitionCount",
        "productFamilyNone",
        "productFamilyMajor",
        "productFamilyMinor",
        "productFamilyDominant",
        "productFamilyMinorSeventh",
    ):
        assert type(row["orderedFeatureValues"][feature_names.index(name)]) is int
    assert type(row["orderedFeatureValues"][feature_names.index("predictionCoverage")]) is float
    assert readiness.validate_beat_cell_readiness_artifact(artifact) == artifact


def test_standalone_validator_rejects_float_normalized_hash_for_integer_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact, feature_values = _mixed_feature_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    row = changed["joinedOofRows"][0]
    float_normalized = {name: float(value) for name, value in feature_values.items()}
    wrong_type_hash = canonical_sha256(float_normalized)
    assert wrong_type_hash != canonical_sha256(feature_values)

    row["featureValuesSha256"] = wrong_type_hash
    _reseal(row, "rowSha256")
    changed["joinedOofRowSetSha256"] = canonical_sha256(changed["joinedOofRows"])
    _reseal(changed, "artifactSha256")

    with pytest.raises(readiness.BeatCellReadinessError, match="ordered feature vector disagrees"):
        readiness.validate_beat_cell_readiness_artifact(changed)


def test_standalone_validator_rejects_coherently_resealed_float_normalized_integer_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact, _feature_values = _mixed_feature_readiness_artifact(tmp_path, monkeypatch)
    changed = deepcopy(artifact)
    feature_names = changed["featureNames"]
    row = changed["joinedOofRows"][0]
    for name in readiness.INTEGER_FEATURE_NAMES:
        position = feature_names.index(name)
        row["orderedFeatureValues"][position] = float(row["orderedFeatureValues"][position])
    resealed_mapping = {name: row["orderedFeatureValues"][position] for position, name in enumerate(feature_names)}
    row["featureValuesSha256"] = canonical_sha256(resealed_mapping)
    _reseal(row, "rowSha256")
    changed["joinedOofRowSetSha256"] = canonical_sha256(changed["joinedOofRows"])
    diagnostic_source = changed["diagnosticSource"]
    diagnostic_source["joinedFeatureProjectionSetSha256"] = canonical_sha256(
        [
            {
                "exampleKey": item["exampleKey"],
                "featureValuesSha256": item["featureValuesSha256"],
                "orderedFeatureValues": item["orderedFeatureValues"],
            }
            for item in changed["joinedOofRows"]
        ]
    )
    _reseal(diagnostic_source, "sourceSha256")
    _reseal(changed, "artifactSha256")

    with pytest.raises(readiness.BeatCellReadinessError, match="JSON integer"):
        readiness.validate_beat_cell_readiness_artifact(changed)


def test_atomic_new_path_publication_cleans_up_on_precommit_fault(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "report.json"
    artifact = {"schemaVersion": "synthetic", "artifactSha256": _digest("synthetic")}

    def fault() -> None:
        raise RuntimeError("injected precommit failure")

    with pytest.raises(RuntimeError, match="injected"):
        readiness._publish_new_json(output, artifact, precommit_check=fault)
    assert not output.exists()
    assert list(output.parent.iterdir()) == []
    readiness._publish_new_json(output, artifact, precommit_check=lambda: None)
    assert json.loads(output.read_text(encoding="utf-8")) == artifact
    with pytest.raises(readiness.BeatCellReadinessError, match="new path"):
        readiness._publish_new_json(output, artifact, precommit_check=lambda: None)


def test_publication_rechecks_exact_input_before_and_after_link(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    original = {"value": "original"}
    changed = {"value": "changed"}
    source.write_bytes(readiness._render_json(original))
    _value, original_raw, original_stat = readiness._read_json(source, "synthetic source")

    def verify() -> None:
        readiness._verify_input_unchanged(source, original_stat, original_raw, "synthetic source")

    source.write_bytes(readiness._render_json(changed))
    prelink_output = tmp_path / "prelink.json"
    with pytest.raises(readiness.BeatCellReadinessError, match="changed before readiness publication"):
        readiness._publish_new_json(prelink_output, original, precommit_check=verify)
    assert not prelink_output.exists()

    source.write_bytes(original_raw)
    barrier_count = 0

    def mutate_after_prelink_barrier() -> None:
        nonlocal barrier_count
        verify()
        barrier_count += 1
        if barrier_count == 1:
            source.write_bytes(readiness._render_json(changed))

    postlink_output = tmp_path / "postlink.json"
    with pytest.raises(readiness.BeatCellReadinessError, match="changed before readiness publication"):
        readiness._publish_new_json(
            postlink_output,
            original,
            precommit_check=mutate_after_prelink_barrier,
        )
    assert barrier_count == 1
    assert not postlink_output.exists()

    source.write_bytes(original_raw)
    successful_barriers = 0

    def successful_verify() -> None:
        nonlocal successful_barriers
        verify()
        successful_barriers += 1

    successful_output = tmp_path / "successful.json"
    readiness._publish_new_json(successful_output, original, precommit_check=successful_verify)
    assert successful_barriers == 2
    assert successful_output.read_bytes() == readiness._render_json(original)


def test_publication_rejects_destination_name_swap_and_preserves_foreign_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "nested" / "report.json"
    relocated = output.with_name("attacker-relocated-owned-inode.json")
    artifact = {"schemaVersion": "synthetic", "artifactSha256": _digest("synthetic")}
    foreign = {"foreignReplacement": True}
    original_verify_directory = readiness._verify_directory_path
    verification_count = 0

    def swap_during_final_parent_check(path: Path, descriptor: int, inode: tuple[int, int]) -> None:
        nonlocal verification_count
        verification_count += 1
        if verification_count == 2:
            os.rename(
                output.name,
                relocated.name,
                src_dir_fd=descriptor,
                dst_dir_fd=descriptor,
            )
            foreign_descriptor = os.open(
                output.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=descriptor,
            )
            try:
                os.write(foreign_descriptor, readiness._render_json(foreign))
                os.fsync(foreign_descriptor)
            finally:
                os.close(foreign_descriptor)
        original_verify_directory(path, descriptor, inode)

    monkeypatch.setattr(readiness, "_verify_directory_path", swap_during_final_parent_check)
    with pytest.raises(readiness.BeatCellReadinessError, match="output name changed"):
        readiness._publish_new_json(output, artifact, precommit_check=lambda: None)
    assert verification_count == 2
    assert output.read_bytes() == readiness._render_json(foreign)
    assert not relocated.exists()
    assert list(output.parent.iterdir()) == [output]


def test_publication_temp_cleanup_name_swap_preserves_foreign_and_cleans_owned_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "nested" / "report.json"
    relocated = output.with_name("attacker-relocated-owned-inode.json")
    artifact = {"schemaVersion": "synthetic", "artifactSha256": _digest("synthetic")}
    foreign = readiness._render_json({"foreignReplacement": True})
    original_unlink = readiness._unlink_owned
    swapped = False

    def swap_while_removing_temp(parent_descriptor: int, name: str, inode: tuple[int, int]) -> None:
        nonlocal swapped
        original_unlink(parent_descriptor, name, inode)
        if not swapped and name.startswith("."):
            swapped = True
            os.rename(
                output.name,
                relocated.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
            )
            descriptor = os.open(
                output.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=parent_descriptor,
            )
            try:
                os.write(descriptor, foreign)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    monkeypatch.setattr(readiness, "_unlink_owned", swap_while_removing_temp)
    with pytest.raises(readiness.BeatCellReadinessError, match="output name changed"):
        readiness._publish_new_json(output, artifact, precommit_check=lambda: None)
    assert swapped is True
    assert output.read_bytes() == foreign
    assert not relocated.exists()
    assert list(output.parent.iterdir()) == [output]


def test_publication_second_callback_keyboard_interrupt_removes_owned_output(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "report.json"
    artifact = {"schemaVersion": "synthetic", "artifactSha256": _digest("synthetic")}
    callback_count = 0

    def interrupt_second_callback() -> None:
        nonlocal callback_count
        callback_count += 1
        if callback_count == 2:
            raise KeyboardInterrupt("synthetic post-link cancellation")

    with pytest.raises(KeyboardInterrupt, match="post-link cancellation"):
        readiness._publish_new_json(
            output,
            artifact,
            precommit_check=interrupt_second_callback,
        )
    assert callback_count == 2
    assert not output.exists()
    assert list(output.parent.iterdir()) == []


def test_publication_link_created_then_keyboard_interrupt_removes_all_owned_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "nested" / "report.json"
    artifact = {"schemaVersion": "synthetic", "artifactSha256": _digest("synthetic")}
    original_link = readiness.os.link

    def link_then_interrupt(*args, **kwargs) -> None:
        original_link(*args, **kwargs)
        raise KeyboardInterrupt("synthetic cancellation after link syscall")

    monkeypatch.setattr(readiness.os, "link", link_then_interrupt)
    with pytest.raises(KeyboardInterrupt, match="after link syscall"):
        readiness._publish_new_json(output, artifact, precommit_check=lambda: None)
    assert not output.exists()
    assert list(output.parent.iterdir()) == []


def test_cli_has_no_path_or_policy_override() -> None:
    with pytest.raises(SystemExit):
        readiness._parser().parse_args(["--output", "/tmp/alternate.json"])
    with pytest.raises(SystemExit):
        readiness._parser().parse_args(["--cutoff", "0.7"])
