from __future__ import annotations

from copy import deepcopy
import inspect

import pytest

from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.bar_selector import (
    AUDIO_GROUP_AUDIT_SCHEMA,
    AUDIO_LINEAGE_PROJECTION_SCHEMA,
    AUDIO_LINEAGE_VERIFICATION_MODE,
    BAR_SELECTOR_APPLICATION_SCHEMA,
    BAR_SELECTOR_ARTIFACT_SCHEMA,
    BAR_SELECTOR_BAR_SUMMARY_SCHEMA,
    BAR_SELECTOR_CONFIG_SHA256,
    BAR_SELECTOR_EXAMPLES_SCHEMA,
    BAR_OUTCOME_ELIGIBILITY_CONTRACT,
    BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
    ELASTIC_NET_GRID,
    FEATURE_ARRAY_VERIFICATION,
    INNER_FOLD_COUNT,
    LABEL_DETERMINACY_DATASET_IDS,
    OUTER_FOLD_COUNT,
    OOF_DENOMINATOR,
    SELECTOR_ESTIMAND,
    BarSelectorError,
    apply_bar_selector,
    train_bar_selector,
    validate_bar_selector_artifact,
)
from steel_guitar_rag.chord_reader.bar_uncertainty import (
    BAR_FEATURE_CONTRACT_SHA256,
    BAR_FEATURE_NAMES,
)


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _shared_bindings() -> dict:
    return {
        "barSummarySchemaVersion": BAR_SELECTOR_BAR_SUMMARY_SCHEMA,
        "featureNames": list(BAR_FEATURE_NAMES),
        "barFeatureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
        "uncertaintySchemaVersion": "chord_factorized_uncertainty_v1",
        "uncertaintyContractSha256": _digest("uncertainty-contract"),
        "modelOrEnsembleSha256": _digest("model"),
        "decoderContractSha256": _digest("decoder"),
        "memberOrderSha256": _digest("member-order"),
        "sourceFeatureKind": "multiband_chroma_v2",
        "sourceFeatureSpecSha256": _digest("feature-spec"),
        "observabilityProfileSchemaVersion": "chord_existing_feature_matrix_observability_v1",
        "timingSchemaVersion": "chord_explicit_bar_grid_v1",
        "timingSourceClass": "runtime",
        "timingSourceId": "player-analysis-v1",
        "timingSourceContractSha256": _digest("runtime-timing"),
        "barOutcomeEligibilityContract": dict(BAR_OUTCOME_ELIGIBILITY_CONTRACT),
        "barOutcomeEligibilityContractSha256": BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    }


def _feature_values(correct: bool, ordinal: int) -> dict[str, float | int | None]:
    signal = 0.82 + 0.01 * (ordinal % 4) if correct else 0.22 + 0.01 * (ordinal % 4)
    values: dict[str, float | int | None] = {}
    for index, name in enumerate(BAR_FEATURE_NAMES):
        values[name] = 0.25 + (index % 7) * 0.01
    values.update(
        {
            "predictionCoverage": 1.0,
            "predictionDominance": 0.9 if correct else 0.55,
            "predictionTransitionCount": 0 if correct else 2,
            "productFamilyNone": 0,
            "productFamilyMajor": 1,
            "productFamilyMinor": 0,
            "productFamilyDominant": 0,
            "productFamilyMinorSeventh": 0,
            "rootSelectedProbabilityMean": signal,
            "rootSelectedProbabilityMinimum": signal - 0.04,
            "rootMarginMean": signal - 0.1,
            "rootMarginMinimum": signal - 0.14,
            "rootNormalizedEntropyMean": 1.0 - signal,
            "rootNormalizedEntropyMaximum": min(1.0, 1.04 - signal),
            "productSelectedProbabilityMean": signal - 0.03,
            "productSelectedProbabilityMinimum": signal - 0.07,
            "productMarginMean": signal - 0.13,
            "productMarginMinimum": signal - 0.17,
            "productNormalizedEntropyMean": min(1.0, 1.03 - signal),
            "productNormalizedEntropyMaximum": min(1.0, 1.08 - signal),
            "boundaryEndEdgeProbability": None if ordinal % 5 == 0 else 0.3,
        }
    )
    return values


def _lineage_fields(ordinal: int) -> dict[str, str | int]:
    return {
        "sourceAudioSha256": _digest(f"audio-{ordinal}"),
        "cachedFeatureArraySha256": _digest(f"cached-array-{ordinal}"),
        "freshFeatureArraySha256": _digest(f"cached-array-{ordinal}"),
        "canonicalDurationMilliseconds": 8000,
        "audioLineageRowSha256": _digest(f"audio-lineage-row-{ordinal}"),
    }


def _compact_summary(correct: bool, ordinal: int, bindings: dict) -> dict:
    index = ordinal % 4
    start = float(index * 2)
    value = {
        "schemaVersion": BAR_SELECTOR_BAR_SUMMARY_SCHEMA,
        "trackId": f"track-{ordinal:03d}",
        "sourceSummarySha256": _digest(f"source-summary-{ordinal}"),
        "predictionCoreSha256": _digest(f"prediction-{ordinal}"),
        "uncertaintySha256": _digest(f"uncertainty-{ordinal}"),
        "timingSha256": _digest(f"timing-{ordinal}"),
        **_lineage_fields(ordinal),
        "audioLineageProjectionSha256": _digest("audio-lineage-projection-placeholder"),
        "sharedBindingsSha256": canonical_sha256(bindings),
        "barFeatureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
        "index": index,
        "start": start,
        "end": start + 2.0,
        "predictionProduct": "G" if correct else "D7",
        "predictionProductDurationSeconds": 1.8 if correct else 1.1,
        "predictionCoverage": 1.0,
        "predictionDominance": 0.9 if correct else 0.55,
        "predictionTransitionCount": 0 if correct else 2,
        "featureValues": _feature_values(correct, ordinal),
    }
    value["barSummarySha256"] = canonical_sha256(value)
    return value


def _example(group: str, correct: bool, ordinal: int, bindings: dict) -> dict:
    summary = _compact_summary(correct, ordinal, bindings)
    value = {
        "trackId": f"track-{ordinal:03d}",
        "split": "development",
        "confidenceGroupId": group,
        "barIndex": summary["index"],
        "barSummary": summary,
        "modelOrEnsembleSha256": bindings["modelOrEnsembleSha256"],
        "decoderContractSha256": bindings["decoderContractSha256"],
        "memberOrderSha256": bindings["memberOrderSha256"],
        **_lineage_fields(ordinal),
        "audioLineageProjectionSha256": summary["audioLineageProjectionSha256"],
        "legacyProductConfidenceMissing": ordinal == 1,
        "outcome": {"correct": correct},
    }
    value["exampleSha256"] = canonical_sha256(value)
    return value


def _examples_artifact() -> dict:
    bindings = _shared_bindings()
    examples: list[dict] = []
    ordinal = 0
    for group_index in range(10):
        group = f"composition-{group_index:02d}"
        repeat = 2 if group_index < 6 else 4
        for position in range(repeat):
            examples.append(_example(group, position % 2 == 0, ordinal, bindings))
            ordinal += 1
    source_audio_lineage_sha256 = _digest("audio-lineage-artifact")
    projection_rows = []
    for index, example in enumerate(sorted(examples, key=lambda value: value["trackId"])):
        projection_rows.append(
            {
                "trackId": example["trackId"],
                "datasetId": LABEL_DETERMINACY_DATASET_IDS[index % len(LABEL_DETERMINACY_DATASET_IDS)],
                "sourceAudioSha256": example["sourceAudioSha256"],
                "cachedArraySha256": example["cachedFeatureArraySha256"],
                "freshArraySha256": example["freshFeatureArraySha256"],
                "canonicalDurationMilliseconds": example["canonicalDurationMilliseconds"],
                "rowSha256": example["audioLineageRowSha256"],
            }
        )
    projection_payload = {
        "schemaVersion": AUDIO_LINEAGE_PROJECTION_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "sourceAudioLineageSha256": source_audio_lineage_sha256,
        "manifestBindingsSha256": _digest("audio-lineage-manifest-bindings"),
        "featureContractSha256": _digest("audio-lineage-feature-contract"),
        "trackCount": len(projection_rows),
        "tracks": projection_rows,
        "trackSetSha256": canonical_sha256(projection_rows),
    }
    projection = {
        **projection_payload,
        "projectionSha256": canonical_sha256(projection_payload),
    }
    for example in examples:
        example["audioLineageProjectionSha256"] = projection["projectionSha256"]
        example["barSummary"]["audioLineageProjectionSha256"] = projection["projectionSha256"]
        _reseal_summary(example["barSummary"])
        _reseal_example(example)
    group_by_track = {example["trackId"]: example["confidenceGroupId"] for example in examples}
    audio_group_rows = sorted(
        [
            {
                "sourceAudioSha256": row["sourceAudioSha256"],
                "confidenceGroupId": group_by_track[row["trackId"]],
                "trackIds": [row["trackId"]],
                "trackCount": 1,
            }
            for row in projection_rows
        ],
        key=lambda value: value["sourceAudioSha256"],
    )
    audio_group_payload = {
        "schemaVersion": AUDIO_GROUP_AUDIT_SCHEMA,
        "policy": "identical-source-audio-must-share-one-confidence-group-v1",
        "trackCount": len(projection_rows),
        "uniqueSourceAudioCount": len(projection_rows),
        "duplicateSourceAudioCount": 0,
        "duplicateTrackCount": 0,
        "rows": audio_group_rows,
    }
    audio_group_audit = {
        **audio_group_payload,
        "auditSha256": canonical_sha256(audio_group_payload),
    }
    label_audit_payload = {
        "schemaVersion": "chord_bar_selector_label_determinacy_audit_v1",
        "estimand": SELECTOR_ESTIMAND,
        "oofDenominator": OOF_DENOMINATOR,
        "totalBarCount": len(examples) + 5,
        "referenceDeterminateBarCount": len(examples) + 3,
        "referenceMixedBarCount": 1,
        "referenceUncoveredBarCount": 1,
        "predictionMixedBarCount": 1,
        "predictionUncoveredBarCount": 2,
        "predictionConfidenceMissingBarCount": 1,
        "predictionStructurallyScorableBarCount": len(examples),
        "excludedReferenceIndeterminateBarCount": 2,
        "excludedPredictionNoneligibleBarCount": 3,
        "emittedExampleCount": len(examples),
    }
    label_audit = {
        **label_audit_payload,
        "auditSha256": canonical_sha256(label_audit_payload),
    }
    dataset_by_track = {row["trackId"]: row["datasetId"] for row in projection_rows}
    emitted_by_dataset = {
        dataset_id: sum(dataset_by_track[example["trackId"]] == dataset_id for example in examples)
        for dataset_id in LABEL_DETERMINACY_DATASET_IDS
    }
    dataset_rows = []
    for dataset_id in LABEL_DETERMINACY_DATASET_IDS:
        emitted = emitted_by_dataset[dataset_id]
        is_guitarset = dataset_id == "guitarset"
        row_payload = {
            "datasetId": dataset_id,
            "totalBarCount": emitted + (5 if is_guitarset else 0),
            "referenceDeterminateBarCount": emitted + (3 if is_guitarset else 0),
            "referenceMixedBarCount": 1 if is_guitarset else 0,
            "referenceUncoveredBarCount": 1 if is_guitarset else 0,
            "predictionMixedBarCount": 1 if is_guitarset else 0,
            "predictionUncoveredBarCount": 2 if is_guitarset else 0,
            "predictionConfidenceMissingBarCount": 1 if is_guitarset else 0,
            "predictionStructurallyScorableBarCount": emitted,
            "excludedReferenceIndeterminateBarCount": 2 if is_guitarset else 0,
            "excludedPredictionNoneligibleBarCount": 3 if is_guitarset else 0,
            "emittedExampleCount": emitted,
        }
        dataset_rows.append({**row_payload, "rowSha256": canonical_sha256(row_payload)})
    dataset_audit_payload = {
        "schemaVersion": DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
        "strataMode": "certification-datasets-only-v1",
        "requiredDatasetIds": list(LABEL_DETERMINACY_DATASET_IDS),
        "datasetIds": list(LABEL_DETERMINACY_DATASET_IDS),
        "aggregateLabelDeterminacyAuditSha256": label_audit["auditSha256"],
        "rows": dataset_rows,
        "rowSetSha256": canonical_sha256(dataset_rows),
    }
    dataset_audit = {
        **dataset_audit_payload,
        "auditSha256": canonical_sha256(dataset_audit_payload),
    }
    value = {
        "schemaVersion": BAR_SELECTOR_EXAMPLES_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "sharedBindings": bindings,
        "sharedBindingsSha256": canonical_sha256(bindings),
        "sourceBenchmarkReportSha256": _digest("benchmark-report"),
        "sourceRuntimeBarGridManifestSha256": _digest("bar-grid-manifest"),
        "sourceGroupManifestSha256": _digest("group-manifest"),
        "sourceAudioLineageSha256": source_audio_lineage_sha256,
        "sourceAudioLineageProjection": projection,
        "sourceAudioLineageProjectionSha256": projection["projectionSha256"],
        "sourceBenchmarkAudioLineageBindingSha256": _digest("benchmark-audio-lineage-binding"),
        "audioLineageVerificationMode": AUDIO_LINEAGE_VERIFICATION_MODE,
        "featureArrayVerification": FEATURE_ARRAY_VERIFICATION,
        "audioGroupAudit": audio_group_audit,
        "audioGroupAuditSha256": audio_group_audit["auditSha256"],
        "labelDeterminacyAudit": label_audit,
        "labelDeterminacyAuditSha256": label_audit["auditSha256"],
        "datasetLabelDeterminacyAudit": dataset_audit,
        "datasetLabelDeterminacyAuditSha256": dataset_audit["auditSha256"],
        "examples": examples,
        "exampleSetSha256": canonical_sha256(examples),
    }
    value["artifactSha256"] = canonical_sha256(value)
    return value


@pytest.fixture(scope="module")
def trained() -> tuple[dict, dict]:
    source = _examples_artifact()
    return source, train_bar_selector(source)


def _reseal_summary(summary: dict) -> None:
    summary["barSummarySha256"] = canonical_sha256(
        {key: value for key, value in summary.items() if key != "barSummarySha256"}
    )


def _reseal_example(example: dict) -> None:
    example["exampleSha256"] = canonical_sha256(
        {key: value for key, value in example.items() if key != "exampleSha256"}
    )


def _set_example_track(example: dict, track_id: str) -> None:
    example["trackId"] = track_id
    example["barSummary"]["trackId"] = track_id
    _reseal_summary(example["barSummary"])
    _reseal_example(example)


def _copy_example_lineage(target: dict, source: dict) -> None:
    for field in (
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "canonicalDurationMilliseconds",
        "audioLineageRowSha256",
        "audioLineageProjectionSha256",
    ):
        target[field] = source[field]
        target["barSummary"][field] = source["barSummary"][field]
    _reseal_summary(target["barSummary"])
    _reseal_example(target)


def _reseal_source(source: dict) -> None:
    source["exampleSetSha256"] = canonical_sha256(source["examples"])
    source["artifactSha256"] = canonical_sha256(
        {key: value for key, value in source.items() if key != "artifactSha256"}
    )


def _reseal_dataset_label_audit(audit: dict) -> None:
    for row in audit["rows"]:
        row["rowSha256"] = canonical_sha256({key: value for key, value in row.items() if key != "rowSha256"})
    audit["rowSetSha256"] = canonical_sha256(audit["rows"])
    audit["auditSha256"] = canonical_sha256({key: value for key, value in audit.items() if key != "auditSha256"})


def _reseal_artifact(artifact: dict) -> None:
    artifact["artifactSha256"] = canonical_sha256(
        {key: value for key, value in artifact.items() if key != "artifactSha256"}
    )


def test_nested_grouped_training_is_deterministic_and_sealed(trained: tuple[dict, dict]) -> None:
    source, artifact = trained
    assert train_bar_selector(source) == artifact
    assert artifact["schemaVersion"] == BAR_SELECTOR_ARTIFACT_SCHEMA
    assert artifact["developmentOnly"] is True
    assert artifact["promotionEligible"] is False
    assert artifact["operatingThreshold"] is None
    assert artifact["featureNames"] == list(BAR_FEATURE_NAMES)
    assert artifact["featureContractSha256"] == BAR_FEATURE_CONTRACT_SHA256
    assert artifact["barOutcomeEligibilityContract"] == BAR_OUTCOME_ELIGIBILITY_CONTRACT
    assert artifact["barOutcomeEligibilityContractSha256"] == BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256
    assert BAR_OUTCOME_ELIGIBILITY_CONTRACT["correctnessRule"] == "predictionProduct == referenceProduct"
    assert "audit-only" in BAR_OUTCOME_ELIGIBILITY_CONTRACT["legacyProductConfidenceAvailability"]
    assert artifact["binding"] == source["sharedBindings"]
    assert artifact["training"]["configSha256"] == BAR_SELECTOR_CONFIG_SHA256
    assert artifact["training"]["outerFoldCount"] == OUTER_FOLD_COUNT
    assert artifact["training"]["innerFoldCount"] == INNER_FOLD_COUNT
    assert artifact["training"]["sourceExamplesArtifactSha256"] == source["artifactSha256"]
    assert artifact["training"]["sourceExampleSetSha256"] == source["exampleSetSha256"]
    assert artifact["training"]["sourceSharedBindingsSha256"] == source["sharedBindingsSha256"]
    assert artifact["training"]["sourceAudioLineageSha256"] == source["sourceAudioLineageSha256"]
    assert artifact["training"]["sourceAudioLineageProjectionSha256"] == source["sourceAudioLineageProjectionSha256"]
    assert artifact["training"]["sourceAudioGroupAuditSha256"] == source["audioGroupAuditSha256"]
    assert artifact["training"]["sourceLabelDeterminacyAuditSha256"] == source["labelDeterminacyAuditSha256"]
    assert (
        artifact["training"]["sourceDatasetLabelDeterminacyAuditSha256"] == source["datasetLabelDeterminacyAuditSha256"]
    )
    assert artifact["training"]["datasetLabelDeterminacyAudit"] == source["datasetLabelDeterminacyAudit"]
    assert artifact["training"]["audioLineageVerificationMode"] == AUDIO_LINEAGE_VERIFICATION_MODE
    assert artifact["training"]["featureArrayVerification"] == FEATURE_ARRAY_VERIFICATION
    assert artifact["training"]["estimand"] == SELECTOR_ESTIMAND
    assert artifact["training"]["oofDenominator"] == OOF_DENOMINATOR
    assert (
        sum(row["legacyProductConfidenceMissing"] for row in artifact["training"]["oofAuditRows"])
        == source["labelDeterminacyAudit"]["predictionConfidenceMissingBarCount"]
    )
    assert all("datasetId" in row for row in artifact["training"]["oofAuditRows"])
    assert artifact["artifactSha256"] == canonical_sha256(
        {key: value for key, value in artifact.items() if key != "artifactSha256"}
    )
    assert validate_bar_selector_artifact(artifact)["artifactSha256"] == artifact["artifactSha256"]


def test_dataset_label_determinacy_strata_sum_exactly_and_expose_guitar_denominator(
    trained: tuple[dict, dict],
) -> None:
    source, artifact = trained
    audit = source["datasetLabelDeterminacyAudit"]
    assert audit["strataMode"] == "certification-datasets-only-v1"
    assert audit["requiredDatasetIds"] == list(LABEL_DETERMINACY_DATASET_IDS)
    assert audit["datasetIds"] == list(LABEL_DETERMINACY_DATASET_IDS)
    aggregate = source["labelDeterminacyAudit"]
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
    ):
        assert sum(row[field] for row in audit["rows"]) == aggregate[field]
    guitarset = next(row for row in audit["rows"] if row["datasetId"] == "guitarset")
    assert guitarset["referenceDeterminateBarCount"] == guitarset["emittedExampleCount"] + 3
    assert artifact["training"]["datasetLabelDeterminacyAudit"]["rows"] == audit["rows"]


def test_rejects_fully_resealed_dataset_label_determinacy_tamper() -> None:
    source = _examples_artifact()
    audit = source["datasetLabelDeterminacyAudit"]
    guitarset = next(row for row in audit["rows"] if row["datasetId"] == "guitarset")
    guitarset["totalBarCount"] += 1
    guitarset["referenceDeterminateBarCount"] += 1
    guitarset["predictionUncoveredBarCount"] += 1
    guitarset["excludedPredictionNoneligibleBarCount"] += 1
    _reseal_dataset_label_audit(audit)
    source["datasetLabelDeterminacyAuditSha256"] = audit["auditSha256"]
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="do not sum to the aggregate"):
        train_bar_selector(source)


def test_selector_artifact_rejects_resealed_propagated_dataset_audit_tamper(
    trained: tuple[dict, dict],
) -> None:
    _source, original = trained
    artifact = deepcopy(original)
    audit = artifact["training"]["datasetLabelDeterminacyAudit"]
    guitarset = next(row for row in audit["rows"] if row["datasetId"] == "guitarset")
    guitarset["totalBarCount"] += 1
    guitarset["referenceDeterminateBarCount"] += 1
    guitarset["predictionUncoveredBarCount"] += 1
    guitarset["excludedPredictionNoneligibleBarCount"] += 1
    _reseal_dataset_label_audit(audit)
    artifact["training"]["sourceDatasetLabelDeterminacyAuditSha256"] = audit["auditSha256"]
    _reseal_artifact(artifact)
    with pytest.raises(BarSelectorError, match="do not sum to the aggregate"):
        validate_bar_selector_artifact(artifact)


def test_rejects_resealed_per_example_missing_confidence_audit_tamper() -> None:
    source = _examples_artifact()
    example = next(row for row in source["examples"] if not row["legacyProductConfidenceMissing"])
    example["legacyProductConfidenceMissing"] = True
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="missing-legacy-confidence count"):
        train_bar_selector(source)


def test_selector_artifact_rejects_resealed_oof_missing_confidence_tamper(
    trained: tuple[dict, dict],
) -> None:
    _source, original = trained
    artifact = deepcopy(original)
    row = next(value for value in artifact["training"]["oofAuditRows"] if not value["legacyProductConfidenceMissing"])
    row["legacyProductConfidenceMissing"] = True
    artifact["training"]["oofPredictionSetSha256"] = canonical_sha256(artifact["training"]["oofAuditRows"])
    _reseal_artifact(artifact)
    with pytest.raises(BarSelectorError, match="missing-legacy-confidence flags"):
        validate_bar_selector_artifact(artifact)


def test_every_group_has_unit_mass_and_one_outer_fold(trained: tuple[dict, dict]) -> None:
    _source, artifact = trained
    audit = artifact["training"]["groupWeightAudit"]
    assert {row["exampleCount"] for row in audit} == {2, 4}
    assert all(row["sampleWeight"] == pytest.approx(1.0, abs=1e-12) for row in audit)
    assignments = artifact["training"]["outerFoldAssignments"]
    assert len(assignments) == 10
    assert len({row["confidenceGroupId"] for row in assignments}) == 10
    assert {row["outerFold"] for row in assignments} == set(range(OUTER_FOLD_COUNT))
    assert len(artifact["training"]["outerHyperparameterSelection"]) == OUTER_FOLD_COUNT
    for report in artifact["training"]["outerHyperparameterSelection"]:
        assert report["selectedHyperparameters"] in ELASTIC_NET_GRID
        assert len(report["innerCvScores"]) == len(ELASTIC_NET_GRID)
        assert report["fitConverged"] is True
    assert artifact["estimator"]["optimizer"]["converged"] is True


def test_training_fails_closed_when_any_inner_optimizer_does_not_converge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from steel_guitar_rag.chord_reader import bar_selector

    def nonconverged(matrix, labels, weights, hyperparameters, np):
        return np.zeros(matrix.shape[1], dtype=np.float64), 0.0, 1, False

    monkeypatch.setattr(bar_selector, "_fit_elastic_net", nonconverged)
    with pytest.raises(BarSelectorError, match="did not converge"):
        train_bar_selector(_examples_artifact())


def test_no_group_crosses_outer_or_inner_partitions(trained: tuple[dict, dict]) -> None:
    _source, artifact = trained
    training = artifact["training"]
    outer_by_group = {row["confidenceGroupId"]: row["outerFold"] for row in training["outerFoldAssignments"]}
    assert len(outer_by_group) == training["groupCount"]
    for report in training["outerHyperparameterSelection"]:
        held_out = {group for group, fold in outer_by_group.items() if fold == report["outerFold"]}
        inner_rows = report["innerFoldAssignments"]
        inner_by_group = {row["confidenceGroupId"]: row["innerFold"] for row in inner_rows}
        assert len(inner_by_group) == len(inner_rows)
        assert set(inner_by_group) == set(outer_by_group) - held_out
        assert set(inner_by_group.values()) == set(range(INNER_FOLD_COUNT))
    final_rows = training["finalHyperparameterSelection"]["innerFoldAssignments"]
    final_by_group = {row["confidenceGroupId"]: row["innerFold"] for row in final_rows}
    assert len(final_by_group) == len(final_rows) == training["groupCount"]
    assert set(final_by_group) == set(outer_by_group)
    assert set(final_by_group.values()) == set(range(INNER_FOLD_COUNT))


def test_outer_validation_group_labels_cannot_change_its_raw_oof_probabilities(
    trained: tuple[dict, dict],
) -> None:
    source, artifact = trained
    target_group = next(
        row["confidenceGroupId"] for row in artifact["training"]["outerFoldAssignments"] if row["outerFold"] == 0
    )
    original = {
        row["exampleKey"]: row["probability"]
        for row in artifact["training"]["oofAuditRows"]
        if row["confidenceGroupId"] == target_group
    }
    mutated_source = deepcopy(source)
    for example in mutated_source["examples"]:
        if example["confidenceGroupId"] != target_group:
            continue
        example["outcome"]["correct"] = not example["outcome"]["correct"]
        _reseal_example(example)
    _reseal_source(mutated_source)
    mutated = train_bar_selector(mutated_source)
    observed = {
        row["exampleKey"]: row["probability"]
        for row in mutated["training"]["oofAuditRows"]
        if row["confidenceGroupId"] == target_group
    }
    assert observed == original


def test_oof_reports_threshold_free_brier_aurc_and_precision_coverage(trained: tuple[dict, dict]) -> None:
    source, artifact = trained
    report = artifact["outOfFoldEvaluation"]
    assert report["estimand"] == SELECTOR_ESTIMAND
    assert report["denominator"] == OOF_DENOMINATOR
    assert report["denominatorExampleCount"] == len(source["examples"])
    assert report["totalBarCount"] == len(source["examples"]) + 5
    assert report["excludedReferenceIndeterminateBarCount"] == 2
    assert report["excludedPredictionNoneligibleBarCount"] == 3
    assert report["predictionConfidenceMissingBarCount"] == 1
    assert 0 <= report["groupBalancedBrierScore"] <= 1
    assert 0 <= report["groupBalancedAreaUnderRiskCoverage"] <= 1
    assert report["groupBalancedLogLoss"] >= 0
    assert report["precisionCoveragePolicy"].endswith("no operating threshold selected")
    assert report["precisionCoverage"][-1]["realizableCoverage"] == pytest.approx(1.0)
    assert "selectedThreshold" not in repr(artifact)
    assert "productConfidence" not in repr(artifact)
    rows = artifact["training"]["oofAuditRows"]
    assert all(isinstance(row["correct"], bool) for row in rows)
    for group in {row["confidenceGroupId"] for row in rows}:
        assert sum(row["sampleWeight"] for row in rows if row["confidenceGroupId"] == group) == pytest.approx(1.0)


def test_only_exact_ordered_bar_features_enter_estimator(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _examples_artifact()
    observed_shapes: list[tuple[int, int]] = []
    from steel_guitar_rag.chord_reader import bar_selector

    original = bar_selector._fit_preprocessor

    def recording_preprocessor(matrix, weights, np):
        observed_shapes.append(matrix.shape)
        return original(matrix, weights, np)

    monkeypatch.setattr(bar_selector, "_fit_preprocessor", recording_preprocessor)
    artifact = train_bar_selector(source)
    assert all(columns == len(BAR_FEATURE_NAMES) for _rows, columns in observed_shapes)
    assert any(rows < len(source["examples"]) for rows, _columns in observed_shapes)
    assert observed_shapes[-1][0] == len(source["examples"])
    assert len(artifact["estimator"]["coefficients"]) == len(BAR_FEATURE_NAMES)
    source_text = inspect.getsource(train_bar_selector)
    assert 'row["trackId"]' not in source_text.split("matrix =", 1)[1].split("labels =", 1)[0]
    assert 'row["group"]' not in source_text.split("matrix =", 1)[1].split("labels =", 1)[0]
    assert 'row["correct"]' not in source_text.split("matrix =", 1)[1].split("labels =", 1)[0]
    assert 'row["sourceAudioSha256"]' not in source_text.split("matrix =", 1)[1].split("labels =", 1)[0]
    assert 'row["audioLineageRowSha256"]' not in source_text.split("matrix =", 1)[1].split("labels =", 1)[0]


@pytest.mark.parametrize("split", ["calibration", "test", "heldout", "confirmation"])
def test_sealed_top_level_split_rejected_before_examples_are_validated(split: str) -> None:
    with pytest.raises(BarSelectorError, match="sealed top-level split"):
        train_bar_selector({"split": split, "examples": object()})


def test_sealed_per_example_split_rejected_before_nested_summary() -> None:
    source = {"split": "development", "examples": [{"split": "calibration", "barSummary": object()}]}
    with pytest.raises(BarSelectorError, match="calibration, test, heldout"):
        train_bar_selector(source)


def test_explicit_group_required_without_track_fallback() -> None:
    source = _examples_artifact()
    source["examples"][0]["confidenceGroupId"] = ""
    _reseal_example(source["examples"][0])
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="confidenceGroupId"):
        train_bar_selector(source)


def test_rejects_resealed_example_and_compact_summary_track_mismatch() -> None:
    source = _examples_artifact()
    example = source["examples"][0]
    example["barSummary"]["trackId"] = "foreign-track"
    _reseal_summary(example["barSummary"])
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="does not match barSummary.trackId"):
        train_bar_selector(source)


def test_rejects_resealed_duplicate_logical_bar_with_distinct_nested_hashes() -> None:
    source = _examples_artifact()
    first, second = source["examples"][:2]
    _set_example_track(second, first["trackId"])
    _copy_example_lineage(second, first)
    second["barIndex"] = first["barIndex"]
    second["barSummary"]["index"] = first["barIndex"]
    second["barSummary"]["start"] = first["barSummary"]["start"]
    second["barSummary"]["end"] = first["barSummary"]["end"]
    _reseal_summary(second["barSummary"])
    _reseal_example(second)
    _reseal_source(source)
    assert second["barSummary"]["barSummarySha256"] != first["barSummary"]["barSummarySha256"]
    with pytest.raises(BarSelectorError, match=r"duplicate logical \(trackId, barIndex\)"):
        train_bar_selector(source)


def test_rejects_resealed_multiple_confidence_groups_for_one_track() -> None:
    source = _examples_artifact()
    first = source["examples"][0]
    second = source["examples"][2]
    _set_example_track(second, first["trackId"])
    _copy_example_lineage(second, first)
    for field in (
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
    ):
        second["barSummary"][field] = first["barSummary"][field]
    _reseal_summary(second["barSummary"])
    _reseal_example(second)
    _reseal_source(source)
    assert second["confidenceGroupId"] != first["confidenceGroupId"]
    with pytest.raises(BarSelectorError, match="confidenceGroupId"):
        train_bar_selector(source)


@pytest.mark.parametrize(
    "field",
    [
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
    ],
)
def test_rejects_resealed_per_track_source_binding_splice(field: str) -> None:
    source = _examples_artifact()
    first, second = source["examples"][:2]
    _set_example_track(second, first["trackId"])
    _copy_example_lineage(second, first)
    for binding_field in (
        "sourceSummarySha256",
        "predictionCoreSha256",
        "uncertaintySha256",
        "timingSha256",
    ):
        second["barSummary"][binding_field] = first["barSummary"][binding_field]
    second["barSummary"][field] = _digest(f"resealed-splice-{field}")
    _reseal_summary(second["barSummary"])
    _reseal_example(second)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="one source-summary"):
        train_bar_selector(source)


@pytest.mark.parametrize(
    "field",
    [
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "audioLineageRowSha256",
        "audioLineageProjectionSha256",
    ],
)
def test_rejects_resealed_audio_lineage_splice(field: str) -> None:
    source = _examples_artifact()
    example = source["examples"][0]
    value = _digest(f"spliced-{field}")
    example[field] = value
    example["barSummary"][field] = value
    _reseal_summary(example["barSummary"])
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="audio-lineage binding|feature-array hashes"):
        train_bar_selector(source)


def test_rejects_resealed_audio_group_audit_reassignment() -> None:
    source = _examples_artifact()
    audit = source["audioGroupAudit"]
    target = next(row for row in audit["rows"] if row["trackIds"] == [source["examples"][0]["trackId"]])
    target["confidenceGroupId"] = "different-composition"
    audit["auditSha256"] = canonical_sha256({key: value for key, value in audit.items() if key != "auditSha256"})
    source["audioGroupAuditSha256"] = audit["auditSha256"]
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="confidenceGroupId"):
        train_bar_selector(source)


def test_rejects_resealed_audio_lineage_millisecond_splice() -> None:
    source = _examples_artifact()
    example = source["examples"][0]
    example["canonicalDurationMilliseconds"] += 1
    example["barSummary"]["canonicalDurationMilliseconds"] += 1
    _reseal_summary(example["barSummary"])
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="audio-lineage binding"):
        train_bar_selector(source)


def test_outcome_exposes_only_boolean_correct() -> None:
    source = _examples_artifact()
    source["examples"][0]["outcome"]["eligible"] = True
    _reseal_example(source["examples"][0])
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="exactly boolean correct"):
        train_bar_selector(source)


@pytest.mark.parametrize(
    "forbidden",
    [
        "trackId",
        "datasetId",
        "role",
        "reference",
        "correct",
        "eligible",
        "legacyProductConfidenceMissing",
    ],
)
def test_forbidden_metadata_or_outcome_feature_is_rejected(forbidden: str) -> None:
    source = _examples_artifact()
    example = source["examples"][0]
    example["barSummary"]["featureValues"][forbidden] = 1.0
    _reseal_summary(example["barSummary"])
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="BAR_FEATURE_NAMES"):
        train_bar_selector(source)


def test_reordered_feature_mapping_is_rejected() -> None:
    source = _examples_artifact()
    example = source["examples"][0]
    values = example["barSummary"]["featureValues"]
    example["barSummary"]["featureValues"] = dict(reversed(list(values.items())))
    _reseal_summary(example["barSummary"])
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="frozen order"):
        train_bar_selector(source)


@pytest.mark.parametrize(
    "feature,value",
    [
        ("rootSelectedProbabilityMean", 1.01),
        ("representationRmsMean", -0.01),
        ("cosineChangeMaximum", 2.01),
        ("predictionCoverage", None),
    ],
)
def test_malformed_feature_ranges_and_required_nulls_are_rejected(feature: str, value: float | None) -> None:
    source = _examples_artifact()
    example = source["examples"][0]
    example["barSummary"]["featureValues"][feature] = value
    if feature == "predictionCoverage":
        example["barSummary"]["predictionCoverage"] = value
    _reseal_summary(example["barSummary"])
    _reseal_example(example)
    _reseal_source(source)
    with pytest.raises(BarSelectorError):
        train_bar_selector(source)


def test_hash_tampering_and_duplicate_examples_fail() -> None:
    source = _examples_artifact()
    source["examples"][0]["outcome"]["correct"] = not source["examples"][0]["outcome"]["correct"]
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match="exampleSha256"):
        train_bar_selector(source)

    source = _examples_artifact()
    source["examples"][1] = deepcopy(source["examples"][0])
    _reseal_source(source)
    with pytest.raises(BarSelectorError, match=r"duplicate logical \(trackId, barIndex\)"):
        train_bar_selector(source)


def test_apply_returns_probability_without_threshold_or_fallback(trained: tuple[dict, dict]) -> None:
    source, artifact = trained
    example = source["examples"][0]
    result = apply_bar_selector(
        example["barSummary"],
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert result["schemaVersion"] == BAR_SELECTOR_APPLICATION_SCHEMA
    assert 0 <= result["probability"] <= 1
    assert result["reason"] is None
    assert result["operatingThreshold"] is None
    assert "productConfidence" not in result


def test_legacy_confidence_missing_disclosure_does_not_gate_training_or_apply(
    trained: tuple[dict, dict],
) -> None:
    source, artifact = trained
    assert source["labelDeterminacyAudit"]["predictionConfidenceMissingBarCount"] == 1
    assert (
        artifact["training"]["emittedExampleCount"]
        == source["labelDeterminacyAudit"]["predictionStructurallyScorableBarCount"]
    )
    assert artifact["training"]["excludedPredictionNoneligibleBarCount"] == 3
    assert artifact["training"]["predictionConfidenceMissingBarCount"] == 1
    example = source["examples"][0]
    result = apply_bar_selector(
        example["barSummary"],
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert 0 <= result["probability"] <= 1
    assert result["reason"] is None


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing-product", "prediction-product-missing"),
        ("low-coverage", "prediction-coverage-below-eligibility-threshold"),
        ("low-dominance", "prediction-dominance-below-eligibility-threshold"),
    ],
)
def test_apply_enforces_reference_free_structural_eligibility(
    trained: tuple[dict, dict],
    mutation: str,
    reason: str,
) -> None:
    source, artifact = trained
    example = source["examples"][0]
    summary = deepcopy(example["barSummary"])
    if mutation == "missing-product":
        summary["predictionProduct"] = None
    elif mutation == "low-coverage":
        summary["predictionCoverage"] = 0.749999
        summary["featureValues"]["predictionCoverage"] = 0.749999
    else:
        summary["predictionDominance"] = 0.749999
        summary["featureValues"]["predictionDominance"] = 0.749999
    _reseal_summary(summary)
    result = apply_bar_selector(
        summary,
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert result["probability"] is None
    assert result["reason"] == reason


def test_apply_scores_exact_structural_eligibility_boundaries(trained: tuple[dict, dict]) -> None:
    source, artifact = trained
    example = source["examples"][0]
    summary = deepcopy(example["barSummary"])
    summary["predictionCoverage"] = 0.75
    summary["predictionDominance"] = 0.75
    summary["featureValues"]["predictionCoverage"] = 0.75
    summary["featureValues"]["predictionDominance"] = 0.75
    _reseal_summary(summary)
    result = apply_bar_selector(
        summary,
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert 0 <= result["probability"] <= 1
    assert result["reason"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("modelOrEnsembleSha256", _digest("other-model")),
        ("decoderContractSha256", _digest("other-decoder")),
        ("memberOrderSha256", _digest("other-members")),
        ("uncertaintyContractSha256", _digest("other-uncertainty")),
        ("sourceFeatureSpecSha256", _digest("other-features")),
        ("timingSourceContractSha256", _digest("other-timing")),
    ],
)
def test_apply_fails_closed_on_every_static_binding_family(
    trained: tuple[dict, dict],
    field: str,
    value: str,
) -> None:
    source, artifact = trained
    example = source["examples"][0]
    binding = deepcopy(source["sharedBindings"])
    binding[field] = value
    result = apply_bar_selector(
        example["barSummary"],
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=binding,
    )
    assert result["probability"] is None
    assert result["reason"] == "binding-mismatch"
    assert "productConfidence" not in result


def test_outcome_eligibility_contract_is_frozen_in_training_artifact_and_apply(
    trained: tuple[dict, dict],
) -> None:
    source, artifact = trained

    tampered_source = deepcopy(source)
    contract = tampered_source["sharedBindings"]["barOutcomeEligibilityContract"]
    contract["predictionCoverage"] = 0.5
    tampered_source["sharedBindings"]["barOutcomeEligibilityContractSha256"] = canonical_sha256(contract)
    tampered_source["sharedBindingsSha256"] = canonical_sha256(tampered_source["sharedBindings"])
    for example in tampered_source["examples"]:
        example["barSummary"]["sharedBindingsSha256"] = tampered_source["sharedBindingsSha256"]
        _reseal_summary(example["barSummary"])
        _reseal_example(example)
    _reseal_source(tampered_source)
    with pytest.raises(BarSelectorError, match="outcome/eligibility contract"):
        train_bar_selector(tampered_source)

    tampered_artifact = deepcopy(artifact)
    tampered_artifact["barOutcomeEligibilityContract"]["predictionCoverage"] = 0.5
    tampered_artifact["barOutcomeEligibilityContractSha256"] = canonical_sha256(
        tampered_artifact["barOutcomeEligibilityContract"]
    )
    _reseal_artifact(tampered_artifact)
    with pytest.raises(BarSelectorError, match="outcome/eligibility contract"):
        validate_bar_selector_artifact(tampered_artifact)

    supplied = deepcopy(source["sharedBindings"])
    supplied["barOutcomeEligibilityContract"]["predictionCoverage"] = 0.5
    supplied["barOutcomeEligibilityContractSha256"] = canonical_sha256(supplied["barOutcomeEligibilityContract"])
    example = source["examples"][0]
    result = apply_bar_selector(
        example["barSummary"],
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=supplied,
    )
    assert result["probability"] is None
    assert result["reason"] == "invalid-shared-bindings"


def test_apply_fails_closed_on_bar_artifact_and_index_tampering(trained: tuple[dict, dict]) -> None:
    source, artifact = trained
    example = source["examples"][0]
    summary = deepcopy(example["barSummary"])
    summary["featureValues"]["rootSelectedProbabilityMean"] = 0.001
    assert (
        apply_bar_selector(
            summary,
            artifact,
            bar_index=example["barIndex"],
            shared_bindings=source["sharedBindings"],
        )["reason"]
        == "invalid-bar-summary"
    )
    assert (
        apply_bar_selector(
            example["barSummary"],
            artifact,
            bar_index=999,
            shared_bindings=source["sharedBindings"],
        )["reason"]
        == "bar-index-mismatch"
    )

    tampered_artifact = deepcopy(artifact)
    tampered_artifact["estimator"]["intercept"] += 1.0
    result = apply_bar_selector(
        example["barSummary"],
        tampered_artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert result["probability"] is None
    assert result["reason"] == "invalid-selector-artifact"


def test_apply_scores_new_track_outside_training_projection_when_static_binding_matches(
    trained: tuple[dict, dict],
) -> None:
    source, artifact = trained
    example = source["examples"][0]
    summary = deepcopy(example["barSummary"])
    summary["trackId"] = "calibration-new-song-not-in-development-projection"
    summary["sourceAudioSha256"] = _digest("calibration-source-audio")
    summary["cachedFeatureArraySha256"] = _digest("calibration-feature-array")
    summary["freshFeatureArraySha256"] = summary["cachedFeatureArraySha256"]
    summary["canonicalDurationMilliseconds"] = 12_345
    summary["audioLineageRowSha256"] = _digest("calibration-audio-lineage-row")
    summary["audioLineageProjectionSha256"] = _digest("calibration-audio-lineage-projection")
    _reseal_summary(summary)
    assert "split" not in summary
    assert summary["trackId"] not in {row["trackId"] for row in source["sourceAudioLineageProjection"]["tracks"]}
    assert summary["audioLineageProjectionSha256"] != artifact["training"]["sourceAudioLineageProjectionSha256"]
    result = apply_bar_selector(
        summary,
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert 0 <= result["probability"] <= 1
    assert result["reason"] is None


def test_apply_scores_split_neutral_core_summary_without_lineage_metadata(
    trained: tuple[dict, dict],
) -> None:
    source, artifact = trained
    example = source["examples"][0]
    summary = deepcopy(example["barSummary"])
    summary["trackId"] = "live-new-song"
    for field in (
        "sourceAudioSha256",
        "cachedFeatureArraySha256",
        "freshFeatureArraySha256",
        "canonicalDurationMilliseconds",
        "audioLineageRowSha256",
        "audioLineageProjectionSha256",
    ):
        summary.pop(field)
    _reseal_summary(summary)
    result = apply_bar_selector(
        summary,
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert 0 <= result["probability"] <= 1
    assert result["reason"] is None


def test_apply_rejects_foreign_model_summary_even_with_selector_binding(trained: tuple[dict, dict]) -> None:
    source, artifact = trained
    example = source["examples"][0]
    foreign_binding = deepcopy(source["sharedBindings"])
    foreign_binding["modelOrEnsembleSha256"] = _digest("foreign-model")
    foreign_summary = deepcopy(example["barSummary"])
    foreign_summary["sharedBindingsSha256"] = canonical_sha256(foreign_binding)
    _reseal_summary(foreign_summary)
    result = apply_bar_selector(
        foreign_summary,
        artifact,
        bar_index=example["barIndex"],
        shared_bindings=source["sharedBindings"],
    )
    assert result["probability"] is None
    assert result["reason"] == "binding-mismatch"


def test_artifact_validator_rejects_threshold_even_when_resealed(trained: tuple[dict, dict]) -> None:
    _source, artifact = trained
    tampered = deepcopy(artifact)
    tampered["operatingThreshold"] = 0.98
    _reseal_artifact(tampered)
    with pytest.raises(BarSelectorError, match="no operating threshold"):
        validate_bar_selector_artifact(tampered)


def test_artifact_validator_recomputes_headline_oof_metrics_from_audit_rows(
    trained: tuple[dict, dict],
) -> None:
    _source, artifact = trained
    tampered = deepcopy(artifact)
    tampered["outOfFoldEvaluation"]["groupBalancedBrierScore"] += 0.01
    _reseal_artifact(tampered)
    with pytest.raises(BarSelectorError, match="do not recompute"):
        validate_bar_selector_artifact(tampered)
