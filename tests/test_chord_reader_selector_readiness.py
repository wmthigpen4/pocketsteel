from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from steel_guitar_rag.chord_reader import selector_readiness as readiness
from steel_guitar_rag.chord_reader.bar_examples import GROUP_MANIFEST_SCHEMA
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.bar_selector import (
    BAR_SELECTOR_ARTIFACT_SCHEMA,
    DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
    LABEL_DETERMINACY_AUDIT_SCHEMA,
    LABEL_DETERMINACY_DATASET_IDS,
)
from steel_guitar_rag.chord_reader.bar_uncertainty import BAR_FEATURE_NAMES


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _write(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _label_row(dataset_id: str, *, reference_determinate: int, emitted: int) -> dict:
    excluded_prediction = reference_determinate - emitted
    payload = {
        "datasetId": dataset_id,
        "totalBarCount": reference_determinate + 2,
        "referenceDeterminateBarCount": reference_determinate,
        "referenceMixedBarCount": 1,
        "referenceUncoveredBarCount": 1,
        "predictionMixedBarCount": 0,
        "predictionUncoveredBarCount": excluded_prediction,
        "predictionConfidenceMissingBarCount": 2,
        "predictionStructurallyScorableBarCount": emitted,
        "excludedReferenceIndeterminateBarCount": 2,
        "excludedPredictionNoneligibleBarCount": excluded_prediction,
        "emittedExampleCount": emitted,
    }
    return {**payload, "rowSha256": canonical_sha256(payload)}


def _label_audits() -> tuple[dict, dict]:
    rows = [
        _label_row(dataset_id, reference_determinate=50 if dataset_id == "guitarset" else 42, emitted=42)
        for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    ]
    aggregate_counts = {
        field: sum(row[field] for row in rows)
        for field in (
            "totalBarCount",
            "referenceDeterminateBarCount",
            "referenceMixedBarCount",
            "referenceUncoveredBarCount",
            "predictionMixedBarCount",
            "predictionUncoveredBarCount",
            "predictionConfidenceMissingBarCount",
            "predictionStructurallyScorableBarCount",
            "excludedReferenceIndeterminateBarCount",
            "excludedPredictionNoneligibleBarCount",
            "emittedExampleCount",
        )
    }
    aggregate_payload = {
        "schemaVersion": LABEL_DETERMINACY_AUDIT_SCHEMA,
        "estimand": "synthetic-development-estimand",
        "oofDenominator": "synthetic-development-oof-denominator",
        **aggregate_counts,
    }
    aggregate = {**aggregate_payload, "auditSha256": canonical_sha256(aggregate_payload)}
    dataset_payload = {
        "schemaVersion": DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
        "strataMode": "certification-datasets-only-v1",
        "requiredDatasetIds": list(LABEL_DETERMINACY_DATASET_IDS),
        "datasetIds": list(LABEL_DETERMINACY_DATASET_IDS),
        "aggregateLabelDeterminacyAuditSha256": aggregate["auditSha256"],
        "rows": rows,
        "rowSetSha256": canonical_sha256(rows),
    }
    dataset = {**dataset_payload, "auditSha256": canonical_sha256(dataset_payload)}
    return aggregate, dataset


def _fixture() -> tuple[dict, dict, dict]:
    group_tracks = []
    projection_tracks = []
    examples = []
    oof_rows = []
    selected_tracks: list[dict] = []
    reviewed_sizes = {
        row["datasetId"]: row["confidenceGroupSizes"] for row in readiness.REVIEWED_DEVELOPMENT_GROUP_SHAPE["datasets"]
    }
    for dataset_id in LABEL_DETERMINACY_DATASET_IDS:
        dataset_groups: list[list[dict]] = []
        for group_index, group_size in enumerate(reviewed_sizes[dataset_id]):
            group = f"group:{dataset_id}:{group_index:03d}"
            members: list[dict] = []
            for member_index in range(group_size):
                track_id = f"track:{dataset_id}:{group_index:03d}:{member_index:02d}"
                if dataset_id == "guitarset":
                    performance = "comp" if member_index < 6 else "solo"
                    player = member_index if member_index < 6 else member_index - 6
                    role = f"guitarset:{performance}:player-{player:02d}"
                else:
                    role = f"{dataset_id}:mix:{group_index:03d}:{member_index:02d}"
                track_payload = {
                    "trackId": track_id,
                    "split": "development",
                    "datasetId": dataset_id,
                    "role": role,
                    "confidenceGroupId": group,
                    "referenceFile": f"{track_id}.json",
                    "referenceSha256": _digest(f"reference:{track_id}"),
                }
                track = {**track_payload, "trackMetadataSha256": canonical_sha256(track_payload)}
                group_tracks.append(track)
                projection_tracks.append(
                    {
                        "trackId": track_id,
                        "datasetId": dataset_id,
                        "canonicalDurationMilliseconds": 1000,
                    }
                )
                members.append(track)
            dataset_groups.append(members)
        selected_tracks.append(dataset_groups[0][0])
        selected_tracks.append(dataset_groups[1][6] if dataset_id == "guitarset" else dataset_groups[1][0])

    reconciliation_target = selected_tracks[0]
    reconciliation_row_payload = {
        "trackId": reconciliation_target["trackId"],
        "datasetId": reconciliation_target["datasetId"],
        "referenceSha256": reconciliation_target["referenceSha256"],
        "originalEnd": 1.00045,
        "predictionDuration": 1.0004,
        "reconciledEnd": 1.0004,
        "reconciledSeconds": 1.00045 - 1.0004,
        "canonicalMs": 1000,
    }
    reconciliation_row = {
        **reconciliation_row_payload,
        "rowSha256": canonical_sha256(reconciliation_row_payload),
    }

    for track_index, track in enumerate(selected_tracks):
        track_id = track["trackId"]
        dataset_id = track["datasetId"]
        group = track["confidenceGroupId"]
        for bar_index in range(21):
            correct = bar_index < 20
            probability = 0.99 if correct else 0.10
            feature_values = {feature_name: 0.5 for feature_name in BAR_FEATURE_NAMES}
            summary = {
                "sourceSummarySha256": _digest(f"summary:{track_id}"),
                "predictionCoreSha256": _digest(f"prediction:{track_id}"),
                "uncertaintySha256": _digest(f"uncertainty:{track_id}"),
                "timingSha256": _digest(f"timing:{track_id}"),
                "sourceAudioSha256": _digest(f"audio:{track_id}"),
                "cachedFeatureArraySha256": _digest(f"feature:{track_id}"),
                "freshFeatureArraySha256": _digest(f"feature:{track_id}"),
                "canonicalDurationMilliseconds": 1000,
                "audioLineageRowSha256": _digest(f"lineage:{track_id}"),
                "audioLineageProjectionSha256": _digest("projection"),
                "barSummarySha256": _digest(f"bar:{track_id}:{bar_index}"),
                "featureValues": feature_values,
            }
            example = {
                "trackId": track_id,
                "confidenceGroupId": group,
                "barIndex": bar_index,
                "barSummary": summary,
                "modelOrEnsembleSha256": _digest("model"),
                "decoderContractSha256": _digest("decoder"),
                "memberOrderSha256": _digest("members"),
                "referenceEndpointReconciliationRowSha256": (
                    reconciliation_row["rowSha256"] if track_id == reconciliation_target["trackId"] else None
                ),
                "legacyProductConfidenceMissing": not correct,
                "outcome": {"correct": correct},
                "exampleSha256": _digest(f"example:{track_id}:{bar_index}"),
            }
            key = readiness._example_key(example)
            examples.append(example)
            oof_rows.append(
                {
                    "exampleKey": key,
                    "datasetId": dataset_id,
                    "confidenceGroupId": group,
                    "outerFold": track_index % 5,
                    "probability": probability,
                    "correct": correct,
                    "legacyProductConfidenceMissing": not correct,
                    "sampleWeight": 1.0 / 21.0,
                }
            )
    group_tracks.sort(key=lambda row: row["trackId"])
    group_payload = {
        "schemaVersion": GROUP_MANIFEST_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "tracks": group_tracks,
        "trackSetSha256": canonical_sha256(
            [{"trackId": row["trackId"], "trackMetadataSha256": row["trackMetadataSha256"]} for row in group_tracks]
        ),
    }
    groups = {**group_payload, "manifestSha256": canonical_sha256(group_payload)}
    aggregate, dataset_audit = _label_audits()
    reconciliation_dataset_counts = [
        {
            "datasetId": dataset_id,
            "sourceTrackCount": sum(track["datasetId"] == dataset_id for track in group_tracks),
            "reconciledTrackCount": int(dataset_id == reconciliation_target["datasetId"]),
        }
        for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    ]
    reconciliation_audit_payload = {
        "schemaVersion": readiness.REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA,
        "policy": readiness.REFERENCE_ENDPOINT_RECONCILIATION_POLICY,
        "sourceTrackCount": len(group_tracks),
        "reconciledTrackCount": 1,
        "unreconciledTrackCount": len(group_tracks) - 1,
        "datasetCounts": reconciliation_dataset_counts,
        "datasetCountSetSha256": canonical_sha256(reconciliation_dataset_counts),
        "totalReconciledSeconds": reconciliation_row["reconciledSeconds"],
        "maximumReconciledSeconds": reconciliation_row["reconciledSeconds"],
        "rows": [reconciliation_row],
        "rowSetSha256": canonical_sha256([reconciliation_row]),
    }
    reconciliation_audit = {
        **reconciliation_audit_payload,
        "auditSha256": canonical_sha256(reconciliation_audit_payload),
    }
    examples_payload = {
        "schemaVersion": "chord_bar_selector_examples_v1",
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "sharedBindingsSha256": _digest("shared-bindings"),
        "sourceBenchmarkReportSha256": _digest("benchmark"),
        "sourceRuntimeBarGridManifestSha256": _digest("runtime"),
        "sourceGroupManifestSha256": groups["manifestSha256"],
        "sourceAudioLineageSha256": _digest("lineage-artifact"),
        "sourceAudioLineageProjectionSha256": _digest("projection"),
        "sourceBenchmarkAudioLineageBindingSha256": _digest("benchmark-lineage-binding"),
        "audioGroupAuditSha256": _digest("audio-group-audit"),
        "referenceEndpointReconciliationAudit": reconciliation_audit,
        "referenceEndpointReconciliationAuditSha256": reconciliation_audit["auditSha256"],
        "labelDeterminacyAudit": aggregate,
        "labelDeterminacyAuditSha256": aggregate["auditSha256"],
        "datasetLabelDeterminacyAudit": dataset_audit,
        "datasetLabelDeterminacyAuditSha256": dataset_audit["auditSha256"],
        "sourceAudioLineageProjection": {"tracks": projection_tracks},
        "examples": examples,
        "exampleSetSha256": canonical_sha256(examples),
    }
    examples_artifact = {
        **examples_payload,
        "artifactSha256": canonical_sha256(examples_payload),
    }
    oof_rows.sort(key=lambda row: row["exampleKey"])
    counts = {field: aggregate[field] for field in aggregate if field.endswith("Count")}
    evaluation = readiness._recomputed_evaluation(oof_rows, counts)
    evaluation["estimand"] = aggregate["estimand"]
    evaluation["denominator"] = aggregate["oofDenominator"]
    source_fields = {
        "sourceExamplesArtifactSha256": examples_artifact["artifactSha256"],
        "sourceExampleSetSha256": examples_artifact["exampleSetSha256"],
        "sourceSharedBindingsSha256": examples_artifact["sharedBindingsSha256"],
        "sourceBenchmarkReportSha256": examples_artifact["sourceBenchmarkReportSha256"],
        "sourceRuntimeBarGridManifestSha256": examples_artifact["sourceRuntimeBarGridManifestSha256"],
        "sourceGroupManifestSha256": groups["manifestSha256"],
        "sourceAudioLineageSha256": examples_artifact["sourceAudioLineageSha256"],
        "sourceAudioLineageProjectionSha256": examples_artifact["sourceAudioLineageProjectionSha256"],
        "sourceBenchmarkAudioLineageBindingSha256": examples_artifact["sourceBenchmarkAudioLineageBindingSha256"],
        "sourceAudioGroupAuditSha256": examples_artifact["audioGroupAuditSha256"],
        "sourceReferenceEndpointReconciliationAuditSha256": examples_artifact[
            "referenceEndpointReconciliationAuditSha256"
        ],
        "sourceLabelDeterminacyAuditSha256": examples_artifact["labelDeterminacyAuditSha256"],
        "sourceDatasetLabelDeterminacyAuditSha256": examples_artifact["datasetLabelDeterminacyAuditSha256"],
    }
    training = {
        "split": "development",
        **source_fields,
        **{field: aggregate[field] for field in aggregate if field.endswith("Count")},
        "referenceEndpointReconciliationAudit": reconciliation_audit,
        "datasetLabelDeterminacyAudit": dataset_audit,
        "oofAuditRows": oof_rows,
    }
    selector_payload = {
        "schemaVersion": BAR_SELECTOR_ARTIFACT_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "operatingThreshold": None,
        "training": training,
        "outOfFoldEvaluation": evaluation,
        "estimator": {
            "imputationValues": [0.5] * len(BAR_FEATURE_NAMES),
            "center": [0.5] * len(BAR_FEATURE_NAMES),
            "scale": [1.0] * len(BAR_FEATURE_NAMES),
            "allMissingFeatureNames": [],
        },
    }
    selector = {**selector_payload, "artifactSha256": canonical_sha256(selector_payload)}
    return examples_artifact, selector, groups


def _reseal_examples(examples: dict) -> None:
    examples["exampleSetSha256"] = canonical_sha256(examples["examples"])
    examples["artifactSha256"] = canonical_sha256(
        {key: value for key, value in examples.items() if key != "artifactSha256"}
    )


def _reseal_selector(selector: dict) -> None:
    selector["artifactSha256"] = canonical_sha256(
        {key: value for key, value in selector.items() if key != "artifactSha256"}
    )


def _reseal_reconciliation_audit(audit: dict) -> None:
    for row in audit["rows"]:
        row["rowSha256"] = canonical_sha256({key: value for key, value in row.items() if key != "rowSha256"})
    audit["datasetCountSetSha256"] = canonical_sha256(audit["datasetCounts"])
    audit["rowSetSha256"] = canonical_sha256(audit["rows"])
    audit["auditSha256"] = canonical_sha256({key: value for key, value in audit.items() if key != "auditSha256"})


def _reseal_groups(groups: dict) -> None:
    for row in groups["tracks"]:
        row["trackMetadataSha256"] = canonical_sha256(
            {key: value for key, value in row.items() if key != "trackMetadataSha256"}
        )
    groups["trackSetSha256"] = canonical_sha256(
        [{"trackId": row["trackId"], "trackMetadataSha256": row["trackMetadataSha256"]} for row in groups["tracks"]]
    )
    groups["manifestSha256"] = canonical_sha256(
        {key: value for key, value in groups.items() if key != "manifestSha256"}
    )


def _paths(tmp_path: Path, examples: dict, selector: dict, groups: dict) -> tuple[Path, Path, Path, Path]:
    examples_path = tmp_path / "examples.json"
    selector_path = tmp_path / "selector.json"
    groups_path = tmp_path / "groups.json"
    output_path = tmp_path / "readiness.json"
    _write(examples_path, examples)
    _write(selector_path, selector)
    _write(groups_path, groups)
    return examples_path, selector_path, groups_path, output_path


def _patch_training(monkeypatch: pytest.MonkeyPatch, selector: dict, calls: list[str] | None = None) -> None:
    def validate(_artifact: dict) -> dict:
        if calls is not None:
            calls.append("validate")
        return {"artifactSha256": selector["artifactSha256"]}

    def train(_examples: dict) -> dict:
        if calls is not None:
            calls.append("train")
        return deepcopy(selector)

    monkeypatch.setattr(readiness, "validate_bar_selector_artifact", validate)
    monkeypatch.setattr(readiness, "train_bar_selector", train)


def test_readiness_passes_fixed_rubric_and_uses_exact_guitar_denominator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    paths = _paths(tmp_path, examples, selector, groups)
    calls: list[str] = []
    _patch_training(monkeypatch, selector, calls)

    artifact = readiness.evaluate_development_selector_readiness(*paths)

    assert calls == ["validate", "train"]
    assert artifact["schemaVersion"] == readiness.READINESS_SCHEMA
    assert artifact["developmentOnly"] is True
    assert artifact["promotionEligible"] is False
    assert artifact["operatingThreshold"] is None
    assert artifact["developmentReadinessPassed"] is True
    assert artifact["calibrationMayOpenOnce"] is True
    assert artifact["fixedDevelopmentCutoff"]["minimumProbabilityAtDescriptivePoint"] == 0.99
    assert artifact["aggregate"]["acceptedCount"] == 200
    assert artifact["guitarset"]["acceptedCount"] == 40
    assert artifact["guitarset"]["referenceDeterminateBarCount"] == 50
    assert artifact["guitarset"]["endToEndCoverage"] == 0.8
    assert artifact["guitarset"]["wilson95LowerBoundIsGate"] is False
    assert artifact["countAudit"] == {
        **{key: artifact["countAudit"][key] for key in artifact["countAudit"]},
    }
    assert artifact["countAudit"]["E"] == len(artifact["joinedOofRows"]) == 210
    serialized_examples = json.loads(paths[0].read_text(encoding="utf-8"))
    assert list(serialized_examples["examples"][0]["barSummary"]["featureValues"]) == sorted(BAR_FEATURE_NAMES)
    assert all(
        row["acceptedAtFixedDevelopmentCutoff"] for row in artifact["joinedOofRows"] if row["probability"] == 0.99
    )
    assert all(
        row["endToEndCoverageAvailable"] is False for row in artifact["diagnostics"]["acceptedSlices"]["byOuterFold"]
    )
    assert all(
        row["endToEndCoverageAvailable"] is True for row in artifact["diagnostics"]["acceptedSlices"]["byDataset"]
    )
    endpoint_diagnostic = artifact["diagnostics"]["referenceEndpointReconciliation"]
    assert endpoint_diagnostic["reconciledTrackCount"] == 1
    assert endpoint_diagnostic["totalReconciledSeconds"] == 1.00045 - 1.0004
    assert endpoint_diagnostic["maximumReconciledSeconds"] == 1.00045 - 1.0004
    assert endpoint_diagnostic["labelSideAuditOnly"] is True
    assert endpoint_diagnostic["estimatorFeature"] is False
    assert endpoint_diagnostic["oofMetricInput"] is False
    assert endpoint_diagnostic["countIdentityInput"] is False
    assert endpoint_diagnostic["readinessGate"] is False
    assert (
        artifact["inputBindings"]["referenceEndpointReconciliationAudit"]["examplesAuditSha256"]
        == examples["referenceEndpointReconciliationAuditSha256"]
    )
    assert artifact["artifactSha256"] == canonical_sha256(
        {key: value for key, value in artifact.items() if key != "artifactSha256"}
    )
    assert json.loads(paths[-1].read_text(encoding="utf-8")) == artifact


def test_fixed_same_cutoff_guitar_failure_closes_calibration_with_exact_reasons(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    guitar_rows = [row for row in selector["training"]["oofAuditRows"] if row["datasetId"] == "guitarset"]
    for row in [row for row in guitar_rows if row["correct"]][:30]:
        row["probability"] = 0.10
    counts = {field: selector["training"][field] for field in selector["training"] if field.endswith("Count")}
    evaluation = readiness._recomputed_evaluation(selector["training"]["oofAuditRows"], counts)
    evaluation["estimand"] = selector["outOfFoldEvaluation"]["estimand"]
    evaluation["denominator"] = selector["outOfFoldEvaluation"]["denominator"]
    selector["outOfFoldEvaluation"] = evaluation
    _reseal_selector(selector)
    paths = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    artifact = readiness.evaluate_development_selector_readiness(*paths)

    assert artifact["developmentReadinessPassed"] is False
    assert artifact["calibrationMayOpenOnce"] is False
    assert artifact["decision"]["calibrationStatus"] == "closed"
    assert artifact["guitarset"]["acceptedCount"] == 10
    assert "gate.guitarset.accepted-count" in artifact["decision"]["failureReasons"]
    assert "gate.guitarset.end-to-end-micro-coverage" in artifact["decision"]["failureReasons"]


def test_protected_split_fails_before_validation_training_or_nested_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    examples["split"] = "calibration"
    examples["examples"] = "forbidden-nested-value"
    paths = _paths(tmp_path, examples, selector, groups)
    calls: list[str] = []
    _patch_training(monkeypatch, selector, calls)

    with pytest.raises(readiness.SelectorReadinessError, match="before nested access"):
        readiness.evaluate_development_selector_readiness(*paths)

    assert calls == []
    assert not paths[-1].exists()


def test_source_group_manifest_hash_mismatch_fails_without_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    examples["sourceGroupManifestSha256"] = _digest("foreign-group-manifest")
    selector["training"]["sourceGroupManifestSha256"] = examples["sourceGroupManifestSha256"]
    _reseal_examples(examples)
    selector["training"]["sourceExamplesArtifactSha256"] = examples["artifactSha256"]
    selector["training"]["sourceExampleSetSha256"] = examples["exampleSetSha256"]
    _reseal_selector(selector)
    paths = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    with pytest.raises(readiness.SelectorReadinessError, match="sourceGroupManifestSha256"):
        readiness.evaluate_development_selector_readiness(*paths)

    assert not paths[-1].exists()


def test_readiness_rejects_fully_resealed_reference_endpoint_audit_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    audit = examples["referenceEndpointReconciliationAudit"]
    row = audit["rows"][0]
    row["referenceSha256"] = _digest("foreign-reference")
    _reseal_reconciliation_audit(audit)
    examples["referenceEndpointReconciliationAuditSha256"] = audit["auditSha256"]
    for example in examples["examples"]:
        if example["trackId"] == row["trackId"]:
            example["referenceEndpointReconciliationRowSha256"] = row["rowSha256"]
    _reseal_examples(examples)
    selector["training"]["sourceExamplesArtifactSha256"] = examples["artifactSha256"]
    selector["training"]["sourceExampleSetSha256"] = examples["exampleSetSha256"]
    selector["training"]["sourceReferenceEndpointReconciliationAuditSha256"] = audit["auditSha256"]
    selector["training"]["referenceEndpointReconciliationAudit"] = deepcopy(audit)
    _reseal_selector(selector)
    paths = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    with pytest.raises(readiness.SelectorReadinessError, match="violates its exact source join"):
        readiness.evaluate_development_selector_readiness(*paths)

    assert not paths[-1].exists()


def test_smaller_resealed_five_dataset_run_cannot_authorize_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    removed = next(
        row
        for row in groups["tracks"]
        if row["datasetId"] == "nrgcp"
        and row["trackId"] not in {example["trackId"] for example in examples["examples"]}
    )
    groups["tracks"].remove(removed)
    examples["sourceAudioLineageProjection"]["tracks"] = [
        row for row in examples["sourceAudioLineageProjection"]["tracks"] if row["trackId"] != removed["trackId"]
    ]
    _reseal_groups(groups)
    examples["sourceGroupManifestSha256"] = groups["manifestSha256"]
    _reseal_examples(examples)
    selector["training"]["sourceGroupManifestSha256"] = groups["manifestSha256"]
    selector["training"]["sourceExamplesArtifactSha256"] = examples["artifactSha256"]
    _reseal_selector(selector)
    paths = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    with pytest.raises(readiness.SelectorReadinessError, match="reviewed exact 246-track shape"):
        readiness.evaluate_development_selector_readiness(*paths)

    assert not paths[-1].exists()


def test_oof_group_weight_must_sum_to_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    selector["training"]["oofAuditRows"][0]["sampleWeight"] += 0.01
    _reseal_selector(selector)
    paths = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    with pytest.raises(readiness.SelectorReadinessError, match="total OOF weight one"):
        readiness.evaluate_development_selector_readiness(*paths)

    assert not paths[-1].exists()


def test_missing_guitar_role_is_explicit_diagnostic_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    for row in groups["tracks"]:
        if row["datasetId"] == "guitarset" and ":solo:" in row["role"]:
            row["role"] = "guitarset:lead:player-00"
    _reseal_groups(groups)
    examples["sourceGroupManifestSha256"] = groups["manifestSha256"]
    _reseal_examples(examples)
    selector["training"]["sourceGroupManifestSha256"] = groups["manifestSha256"]
    selector["training"]["sourceExamplesArtifactSha256"] = examples["artifactSha256"]
    _reseal_selector(selector)
    paths = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    artifact = readiness.evaluate_development_selector_readiness(*paths)

    assert artifact["developmentReadinessPassed"] is False
    assert "diagnostics.guitarset-solo-role-missing" in artifact["decision"]["failureReasons"]
    assert "diagnostics.guitarset-role-unclassifiable" in artifact["decision"]["failureReasons"]


def test_reproduction_byte_mismatch_and_existing_output_both_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    paths = _paths(tmp_path, examples, selector, groups)
    monkeypatch.setattr(readiness, "validate_bar_selector_artifact", lambda _artifact: {})
    reproduced = deepcopy(selector)
    reproduced["purpose"] = "foreign"
    monkeypatch.setattr(readiness, "train_bar_selector", lambda _examples: reproduced)
    with pytest.raises(readiness.SelectorReadinessError, match="differs from the supplied selector object"):
        readiness.evaluate_development_selector_readiness(*paths)
    assert not paths[-1].exists()

    paths[-1].write_text("reserved\n", encoding="utf-8")
    _patch_training(monkeypatch, selector)
    with pytest.raises(readiness.SelectorReadinessError, match="new, non-symlink"):
        readiness.evaluate_development_selector_readiness(*paths)


def test_input_content_mutation_before_publication_rolls_back_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    examples_path, selector_path, groups_path, output_path = _paths(tmp_path, examples, selector, groups)
    monkeypatch.setattr(readiness, "validate_bar_selector_artifact", lambda _artifact: {})

    def mutate_then_return(_examples: dict) -> dict:
        examples_path.write_text(examples_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        return deepcopy(selector)

    monkeypatch.setattr(readiness, "train_bar_selector", mutate_then_return)

    with pytest.raises(readiness.SelectorReadinessError, match="changed before readiness publication"):
        readiness.evaluate_development_selector_readiness(
            examples_path,
            selector_path,
            groups_path,
            output_path,
        )

    assert not output_path.exists()


def test_output_parent_swap_after_link_is_detected_and_owned_link_is_rolled_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples, selector, groups = _fixture()
    examples_path, selector_path, groups_path, _unused = _paths(tmp_path, examples, selector, groups)
    output_parent = tmp_path / "publication"
    output_parent.mkdir()
    moved_parent = tmp_path / "publication-moved"
    output_path = output_parent / "readiness.json"
    _patch_training(monkeypatch, selector)
    original_link = os.link
    swapped = False

    def link_then_swap(*args, **kwargs):
        nonlocal swapped
        result = original_link(*args, **kwargs)
        if not swapped:
            swapped = True
            output_parent.rename(moved_parent)
            output_parent.mkdir()
        return result

    monkeypatch.setattr(readiness.os, "link", link_then_swap)

    with pytest.raises(readiness.SelectorReadinessError, match="parent path changed"):
        readiness.evaluate_development_selector_readiness(
            examples_path,
            selector_path,
            groups_path,
            output_path,
        )

    assert not output_path.exists()
    assert not (moved_parent / output_path.name).exists()


def test_cli_emits_closed_or_open_receipt_only_after_atomic_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    examples, selector, groups = _fixture()
    examples_path, selector_path, groups_path, output_path = _paths(tmp_path, examples, selector, groups)
    _patch_training(monkeypatch, selector)

    assert (
        readiness.main(
            [
                "--examples",
                str(examples_path),
                "--selector",
                str(selector_path),
                "--group-manifest",
                str(groups_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["developmentReadinessPassed"] is True
    assert receipt["calibrationMayOpenOnce"] is True
    assert receipt["artifactSha256"] == json.loads(output_path.read_text())["artifactSha256"]
