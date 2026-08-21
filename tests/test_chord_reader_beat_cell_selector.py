from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

import scripts.chord_beat_cell_selector as selector_cli
from steel_guitar_rag.chord_reader import bar_examples
from steel_guitar_rag.chord_reader import bar_selector
from steel_guitar_rag.chord_reader import beat_cell_readiness
from steel_guitar_rag.chord_reader import beat_cell_selector
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.beat_cell_examples import (
    BEAT_CELL_EXAMPLE_KEY_SCHEMA,
    BEAT_CELL_EXAMPLE_SCHEMA,
    BEAT_CELL_EXAMPLES_FIELDS,
    BEAT_CELL_EXAMPLES_SCHEMA,
    BEAT_CELL_FEATURE_ROW_SCHEMA,
    BEAT_CELL_LABEL_AUDITS_SCHEMA,
    FEATURE_NAMES,
    validate_beat_cell_examples_artifact,
)
from steel_guitar_rag.chord_reader.beat_cell_selector import (
    BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
    BEAT_CELL_SELECTOR_SCHEMA,
    BeatCellSelectorError,
    apply_beat_cell_selector,
    train_beat_cell_selector,
    validate_beat_cell_selector_artifact,
)
from steel_guitar_rag.chord_reader.beat_cell_stage2_contract import (
    BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    BEAT_CELL_STAGE_B_PROJECTION_SHA256,
)


DATASET_IDS = ("aam", "guitarset", "idmt_guitar", "nrgcp", "winterreise")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hashed(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    output = deepcopy(dict(payload))
    output[field] = canonical_sha256(output)
    return output


def _partition_safe_labels(groups: Sequence[str]) -> dict[str, bool]:
    outer = bar_selector._folds(groups, 5, "bar-selector-outer-v1")
    for seed in range(1000):
        labels = {group: int(_digest(f"synthetic-label-{seed}\0{group}")[-1], 16) % 2 == 0 for group in groups}
        if set(labels.values()) != {False, True}:
            continue
        partitions: list[set[str]] = []
        for outer_fold in range(5):
            outer_training = [group for group in groups if outer[group] != outer_fold]
            inner = bar_selector._folds(
                outer_training,
                4,
                f"bar-selector-inner-v1-outer-{outer_fold}",
            )
            partitions.extend(
                {group for group in outer_training if inner[group] != inner_fold} for inner_fold in range(4)
            )
            partitions.append(set(outer_training))
        final_inner = bar_selector._folds(groups, 4, "bar-selector-inner-v1-final")
        partitions.extend({group for group in groups if final_inner[group] != fold} for fold in range(4))
        partitions.append(set(groups))
        if all({labels[group] for group in partition} == {False, True} for partition in partitions):
            return labels
    raise AssertionError("Could not construct deterministic two-class synthetic folds.")


def _feature_values(*, correct: bool, index: int) -> dict[str, float | int | None]:
    values: dict[str, float | int | None] = {}
    for feature_index, name in enumerate(FEATURE_NAMES):
        values[name] = None if feature_index > 7 and feature_index % 13 == 0 else 0.25
    values.update(
        {
            "predictionCoverage": 0.90,
            "predictionDominance": 0.90,
            "predictionTransitionCount": index % 3,
            "productFamilyNone": 0,
            "productFamilyMajor": 1,
            "productFamilyMinor": 0,
            "productFamilyDominant": 0,
            "productFamilyMinorSeventh": 0,
            "rootSelectedProbabilityMean": (0.82 if correct else 0.18) + (index % 5) * 0.001,
            "productSelectedProbabilityMean": (0.78 if correct else 0.22) + (index % 7) * 0.001,
        }
    )
    return {name: values[name] for name in FEATURE_NAMES}


def _audit_observed(rows: Sequence[Mapping[str, Any]]) -> tuple[int, int, int, int, int, int, int]:
    correct = [row for row in rows if row["correct"]]
    incorrect = [row for row in rows if not row["correct"]]
    return (
        len({str(row["trackId"]) for row in rows}),
        len(rows),
        len(correct),
        len(incorrect),
        sum(int(row["durationMilliseconds"]) for row in rows),
        sum(int(row["durationMilliseconds"]) for row in correct),
        sum(int(row["durationMilliseconds"]) for row in incorrect),
    )


def _audit_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    scope: str,
    dataset_id: str | None,
    guitarset_role: str | None,
) -> dict[str, Any]:
    values = _audit_observed(rows)
    payload = {
        "scope": scope,
        "datasetId": dataset_id,
        "guitarsetRole": guitarset_role,
        "trackCount": values[0],
        "exampleCount": values[1],
        "correctCount": values[2],
        "incorrectCount": values[3],
        "exampleDurationMilliseconds": values[4],
        "correctDurationMilliseconds": values[5],
        "incorrectDurationMilliseconds": values[6],
        "sourceFunnelSha256": _digest(f"funnel-{scope}-{dataset_id}-{guitarset_role}"),
    }
    return _hashed(payload, "rowSha256")


def _label_audits(examples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    datasets = [
        _audit_row(
            [row for row in examples if row["datasetId"] == dataset_id],
            scope="dataset",
            dataset_id=dataset_id,
            guitarset_role=None,
        )
        for dataset_id in DATASET_IDS
    ]
    guitar = [row for row in examples if row["datasetId"] == "guitarset"]
    roles = [
        _audit_row(
            [row for row in guitar if row["guitarsetRole"] == role],
            scope="guitarsetRole",
            dataset_id="guitarset",
            guitarset_role=role,
        )
        for role in ("comp", "solo")
    ]
    guitar_payload = {
        "aggregate": _audit_row(
            guitar,
            scope="guitarset",
            dataset_id="guitarset",
            guitarset_role=None,
        ),
        "roles": roles,
        "roleSetSha256": canonical_sha256(roles),
    }
    guitar_audit = _hashed(guitar_payload, "rowSha256")
    payload = {
        "schemaVersion": BEAT_CELL_LABEL_AUDITS_SCHEMA,
        "aggregate": _audit_row(
            examples,
            scope="aggregate",
            dataset_id=None,
            guitarset_role=None,
        ),
        "datasets": datasets,
        "datasetSetSha256": canonical_sha256(datasets),
        "guitarset": guitar_audit,
    }
    return _hashed(payload, "auditSha256")


def _reference_audit() -> dict[str, Any]:
    payload = {
        "schemaVersion": bar_examples.REFERENCE_ENDPOINT_RECONCILIATION_AUDIT_SCHEMA,
        "policy": bar_examples.REFERENCE_ENDPOINT_RECONCILIATION_POLICY,
        "sourceTrackCount": 0,
        "reconciledTrackCount": 0,
        "unreconciledTrackCount": 0,
        "datasetCounts": [],
        "datasetCountSetSha256": canonical_sha256([]),
        "totalReconciledSeconds": 0.0,
        "maximumReconciledSeconds": 0.0,
        "rows": [],
        "rowSetSha256": canonical_sha256([]),
    }
    return _hashed(payload, "auditSha256")


def _synthetic_examples_artifact(group_count: int = 40) -> dict[str, Any]:
    groups = [f"synthetic-group-{index:02d}" for index in range(group_count)]
    labels = _partition_safe_labels(groups)
    feature_set_sha256 = _digest("synthetic-feature-set")
    stage1_sha256 = _digest("synthetic-stage1-artifact")
    examples: list[dict[str, Any]] = []
    for index, group in enumerate(groups):
        track_id = f"synthetic-track-{index:02d}"
        dataset_id = DATASET_IDS[index % len(DATASET_IDS)]
        guitar_role = None
        if dataset_id == "guitarset":
            guitar_role = "comp" if (index // len(DATASET_IDS)) % 2 == 0 else "solo"
        correct = labels[group]
        duration = 400 + index
        feature_values = _feature_values(correct=correct, index=index)
        payload: dict[str, Any] = {
            "schemaVersion": BEAT_CELL_EXAMPLE_SCHEMA,
            "trackId": track_id,
            "cellIndex": 0,
            "durationMilliseconds": duration,
            "sourceBeatCellSha256": _digest(f"cell-{index}"),
            "predictionIdentitySha256": _digest(f"prediction-{index}"),
            "featureRowSha256": _digest(f"feature-row-{index}"),
            "featureSummaryArtifactSha256": _digest(f"feature-summary-{index}"),
            "featureSetArtifactSha256": feature_set_sha256,
            "audioLineageRowSha256": _digest(f"audio-lineage-{index}"),
            "featureValues": feature_values,
            "featureValuesSha256": canonical_sha256(feature_values),
            "stage1OutcomeRowSha256": _digest(f"outcome-{index}"),
            "stage1ArtifactSha256": stage1_sha256,
            "sourceGroupTrackRowSha256": _digest(f"group-track-{index}"),
            "datasetId": dataset_id,
            "role": "comp" if guitar_role == "comp" else "solo" if guitar_role == "solo" else "lead-sheet",
            "guitarsetRole": guitar_role,
            "confidenceGroupId": group,
            "correct": correct,
        }
        key_payload = {
            "schemaVersion": BEAT_CELL_EXAMPLE_KEY_SCHEMA,
            "trackId": track_id,
            "cellIndex": 0,
            "durationMilliseconds": duration,
            "sourceBeatCellSha256": payload["sourceBeatCellSha256"],
            "predictionIdentitySha256": payload["predictionIdentitySha256"],
            "featureRowSha256": payload["featureRowSha256"],
            "featureSummaryArtifactSha256": payload["featureSummaryArtifactSha256"],
            "featureSetArtifactSha256": feature_set_sha256,
            "audioLineageRowSha256": payload["audioLineageRowSha256"],
        }
        payload["exampleKey"] = canonical_sha256(key_payload)
        examples.append(_hashed(payload, "exampleSha256"))
    examples.sort(key=lambda row: str(row["exampleKey"]))
    label_audits = _label_audits(examples)
    reference_audit = _reference_audit()
    artifact: dict[str, Any] = {
        "schemaVersion": BEAT_CELL_EXAMPLES_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": False,
        "selectorTrainingInput": True,
        "stageBProjectionSha256": BEAT_CELL_STAGE_B_PROJECTION_SHA256,
        "featureMathProjectionSha256": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
        "featureNames": list(FEATURE_NAMES),
        "sourceFeatureSetArtifactSha256": feature_set_sha256,
        "sourceFeatureSummarySetSha256": canonical_sha256(
            sorted({str(row["featureSummaryArtifactSha256"]) for row in examples})
        ),
        "sourceFeatureRowSetSha256": canonical_sha256(sorted({str(row["featureRowSha256"]) for row in examples})),
        "labelAudits": label_audits,
        "labelAuditsSha256": label_audits["auditSha256"],
        "referenceEndpointReconciliationAudit": reference_audit,
        "referenceEndpointReconciliationAuditSha256": reference_audit["auditSha256"],
        "trackCount": group_count,
        "confidenceGroupCount": group_count,
        "exampleCount": len(examples),
        "exampleDurationMilliseconds": sum(int(row["durationMilliseconds"]) for row in examples),
        "examples": examples,
        "exampleSetSha256": canonical_sha256(examples),
    }
    for field in BEAT_CELL_EXAMPLES_FIELDS:
        if field != "artifactSha256" and field not in artifact and field.endswith("Sha256"):
            artifact[field] = stage1_sha256 if field == "sourceStage1ArtifactSha256" else _digest(field)
    assert set(artifact) == set(BEAT_CELL_EXAMPLES_FIELDS) - {"artifactSha256"}
    artifact["artifactSha256"] = canonical_sha256(artifact)
    return artifact


def _feature_row(example: Mapping[str, Any], *, coverage: float = 0.9, dominance: float = 0.9) -> dict[str, Any]:
    features = deepcopy(dict(example["featureValues"]))
    features["predictionCoverage"] = coverage
    features["predictionDominance"] = dominance
    payload = {
        "schemaVersion": BEAT_CELL_FEATURE_ROW_SCHEMA,
        "trackId": "unseen-synthetic-track",
        "cellIndex": 7,
        "startMilliseconds": 1000,
        "endMilliseconds": 1500,
        "durationMilliseconds": 500,
        "sourceBeatCellSha256": _digest("unseen-source-cell"),
        "predictionProduct": "C",
        "predictionCoverage": coverage,
        "predictionDominance": dominance,
        "featureValues": features,
        "featureValuesSha256": canonical_sha256(features),
        "predictionIdentitySha256": _digest("unseen-prediction"),
        "constructionSha256": _digest("unseen-construction"),
    }
    return _hashed(payload, "rowSha256")


def _synthetic_official_authority(
    examples: Mapping[str, Any], examples_path: Path, selector_path: Path
) -> dict[str, Any]:
    authority = deepcopy(selector_cli.load_beat_cell_stage2_authority())
    expected_stage1 = authority["sourceInputs"]["stage1Report"]
    for examples_field, authority_field in selector_cli._STAGE1_EXAMPLES_BINDINGS.items():
        expected_stage1[authority_field] = examples[examples_field]
    authority["stageB"]["expectedExampleCount"] = examples["exampleCount"]
    authority["stageB"]["expectedExampleDurationMilliseconds"] = examples["exampleDurationMilliseconds"]
    authority["outputPaths"]["examplesArtifact"] = str(examples_path)
    authority["outputPaths"]["selectorArtifact"] = str(selector_path)
    return authority


@pytest.fixture(scope="module")
def examples_artifact() -> dict[str, Any]:
    value = _synthetic_examples_artifact()
    # Canonical disk rendering alphabetizes featureValues object keys.
    reloaded = json.loads(json.dumps(value, sort_keys=True, allow_nan=False))
    assert list(reloaded["examples"][0]["featureValues"]) == sorted(FEATURE_NAMES)
    return validate_beat_cell_examples_artifact(reloaded)


@pytest.fixture(scope="module")
def selector_artifact(examples_artifact: Mapping[str, Any]) -> dict[str, Any]:
    return train_beat_cell_selector(examples_artifact)


def test_selector_binds_distinct_schema_and_exact_pinned_core(selector_artifact: Mapping[str, Any]) -> None:
    assert selector_artifact["schemaVersion"] == BEAT_CELL_SELECTOR_SCHEMA
    assert selector_artifact["selectorCoreProjectionSha256"] == BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256
    assert (
        selector_artifact["selectorCoreSourceModuleSha256"]
        == beat_cell_selector.BEAT_CELL_SELECTOR_SOURCE_MODULE_SHA256
    )
    assert selector_artifact["operatingThreshold"] is None
    assert selector_artifact["playerUseAuthorized"] is False
    assert selector_artifact["calibrationAccess"] == selector_artifact["testAccess"] == "closed"
    assert selector_artifact["training"]["selectorCandidateCount"] == 1


def test_canonical_round_trip_trains_and_reproduces_exactly(
    examples_artifact: Mapping[str, Any], selector_artifact: Mapping[str, Any]
) -> None:
    validate_beat_cell_selector_artifact(selector_artifact, examples_artifact)
    reproduced = train_beat_cell_selector(examples_artifact)
    assert reproduced == selector_artifact
    assert json.dumps(reproduced, sort_keys=True, allow_nan=False) == json.dumps(
        selector_artifact, sort_keys=True, allow_nan=False
    )


def test_nested_oof_is_group_disjoint_and_retains_readiness_metadata(
    examples_artifact: Mapping[str, Any], selector_artifact: Mapping[str, Any]
) -> None:
    training = selector_artifact["training"]
    rows = training["oofAuditRows"]
    assert set(rows[0]) == {
        "exampleKey",
        "trackId",
        "cellIndex",
        "durationMilliseconds",
        "datasetId",
        "role",
        "guitarsetRole",
        "confidenceGroupId",
        "outerFold",
        "probability",
        "correct",
        "sampleWeight",
    }
    folds_by_group: dict[str, set[int]] = {}
    weights_by_group: dict[str, list[float]] = {}
    for row in rows:
        folds_by_group.setdefault(row["confidenceGroupId"], set()).add(row["outerFold"])
        weights_by_group.setdefault(row["confidenceGroupId"], []).append(row["sampleWeight"])
    assert all(len(folds) == 1 for folds in folds_by_group.values())
    assert all(math.isclose(math.fsum(weights), 1.0, rel_tol=0, abs_tol=1e-12) for weights in weights_by_group.values())
    assert training["exampleCount"] == len(examples_artifact["examples"])
    assert training["exampleDurationMilliseconds"] == examples_artifact["exampleDurationMilliseconds"]
    assert (
        selector_artifact["outOfFoldEvaluation"]["denominatorDurationMilliseconds"]
        == training["exampleDurationMilliseconds"]
    )


def test_validator_rejects_resealed_oof_and_envelope_tampering(
    examples_artifact: Mapping[str, Any], selector_artifact: Mapping[str, Any]
) -> None:
    tampered = deepcopy(dict(selector_artifact))
    tampered["training"]["oofAuditRows"][0]["probability"] = 0.123456789
    tampered["artifactSha256"] = canonical_sha256(
        {key: value for key, value in tampered.items() if key != "artifactSha256"}
    )
    with pytest.raises(BeatCellSelectorError):
        validate_beat_cell_selector_artifact(tampered, examples_artifact)

    thresholded = deepcopy(dict(selector_artifact))
    thresholded["operatingThreshold"] = 0.5
    thresholded["artifactSha256"] = canonical_sha256(
        {key: value for key, value in thresholded.items() if key != "artifactSha256"}
    )
    with pytest.raises(BeatCellSelectorError):
        validate_beat_cell_selector_artifact(thresholded)


def test_validation_does_not_perform_a_second_refit(
    monkeypatch: pytest.MonkeyPatch,
    examples_artifact: Mapping[str, Any],
    selector_artifact: Mapping[str, Any],
) -> None:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("validator attempted an unregistered refit")

    monkeypatch.setattr(bar_selector, "_fit_elastic_net", forbidden)
    validate_beat_cell_selector_artifact(selector_artifact, examples_artifact)


def test_readiness_reproduction_rejects_resealed_estimator_only_change(
    examples_artifact: Mapping[str, Any], selector_artifact: Mapping[str, Any]
) -> None:
    tampered = deepcopy(dict(selector_artifact))
    tampered["estimator"]["coefficients"][0] += 0.125
    tampered["artifactSha256"] = canonical_sha256(
        {key: value for key, value in tampered.items() if key != "artifactSha256"}
    )
    # Structural/source validation intentionally does not spend an extra fit.
    validate_beat_cell_selector_artifact(tampered, examples_artifact)
    with pytest.raises(beat_cell_readiness.BeatCellReadinessError, match="not object-identical"):
        beat_cell_readiness._validate_selector_and_reproduce(examples_artifact, tampered)


def test_split_neutral_application_is_probability_only_and_fails_closed(
    examples_artifact: Mapping[str, Any], selector_artifact: Mapping[str, Any]
) -> None:
    row = _feature_row(examples_artifact["examples"][0])
    result = apply_beat_cell_selector(row, selector_artifact)
    assert result["reason"] is None
    assert 0.0 <= result["probability"] <= 1.0
    assert result["trackId"] == "unseen-synthetic-track"
    assert result["operatingThreshold"] is None
    assert result["playerUseAuthorized"] is False
    assert "accepted" not in result

    below = apply_beat_cell_selector(_feature_row(examples_artifact["examples"][0], coverage=0.74), selector_artifact)
    assert below["probability"] is None
    assert below["reason"] == "prediction-coverage-below-eligibility-threshold"

    near_tie = apply_beat_cell_selector(
        _feature_row(examples_artifact["examples"][0], dominance=0.5000000000000088),
        selector_artifact,
    )
    assert near_tie["probability"] is None
    assert near_tie["reason"] == "prediction-dominance-below-eligibility-threshold"

    invalid = deepcopy(row)
    invalid["featureValues"]["rootSelectedProbabilityMean"] = math.nan
    assert apply_beat_cell_selector(invalid, selector_artifact)["reason"] == "invalid-feature-row"


def test_atomic_publication_rolls_back_post_link_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "selector" / "artifact.json"

    def fail_after_link(_descriptor: int, _name: str) -> bytes:
        raise selector_cli.BeatCellSelectorCliError("injected post-link fault")

    monkeypatch.setattr(selector_cli, "_read_entry", fail_after_link)
    with pytest.raises(selector_cli.BeatCellSelectorCliError):
        selector_cli._atomic_publish_new(output, b"{}\n")
    assert not output.exists()


def test_atomic_publication_detects_parent_swap_and_removes_owned_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "selector" / "artifact.json"
    moved = tmp_path / "selector-moved"
    original = selector_cli._verify_directory_path
    calls = 0

    def swap_on_post_link(path: Path, descriptor: int, inode: tuple[int, int], name: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            path.rename(moved)
            path.mkdir()
        original(path, descriptor, inode, name)

    monkeypatch.setattr(selector_cli, "_verify_directory_path", swap_on_post_link)
    with pytest.raises(selector_cli.BeatCellSelectorCliError):
        selector_cli._atomic_publish_new(output, b"{}\n")
    assert not output.exists()
    assert not (moved / "artifact.json").exists()


def test_atomic_publication_final_parent_check_name_swap_preserves_foreign_and_cleans_owned_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "selector" / "artifact.json"
    stranded = output.parent / "stranded-owned.json"
    original = selector_cli._verify_directory_path
    calls = 0

    def swap_after_final_parent_check(
        path: Path,
        descriptor: int,
        inode: tuple[int, int],
        name: str,
    ) -> None:
        nonlocal calls
        original(path, descriptor, inode, name)
        calls += 1
        if calls == 2:
            output.rename(stranded)
            output.write_bytes(b'{"foreign":true}\n')

    monkeypatch.setattr(selector_cli, "_verify_directory_path", swap_after_final_parent_check)
    with pytest.raises(selector_cli.BeatCellSelectorCliError, match="inode changed"):
        selector_cli._atomic_publish_new(output, b"{}\n")
    assert output.read_bytes() == b'{"foreign":true}\n'
    assert not stranded.exists()
    assert not list(output.parent.glob(".*.tmp"))


def test_atomic_publication_temp_cleanup_name_swap_preserves_foreign_and_cleans_owned_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "selector" / "artifact.json"
    stranded = output.parent / "stranded-owned.json"
    foreign = b'{"foreign":true}\n'
    original = selector_cli._unlink_owned_entry
    swapped = False

    def swap_while_removing_temp(parent_descriptor: int, name: str, inode: tuple[int, int]) -> None:
        nonlocal swapped
        original(parent_descriptor, name, inode)
        if not swapped and name.startswith("."):
            swapped = True
            os.rename(
                output.name,
                stranded.name,
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

    monkeypatch.setattr(selector_cli, "_unlink_owned_entry", swap_while_removing_temp)
    with pytest.raises(selector_cli.BeatCellSelectorCliError, match="inode changed"):
        selector_cli._atomic_publish_new(output, b"{}\n")
    assert swapped is True
    assert output.read_bytes() == foreign
    assert not stranded.exists()
    assert not list(output.parent.glob(".*.tmp"))


def test_atomic_publication_prelink_mutation_has_zero_output_visibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "selector" / "artifact.json"
    source = tmp_path / "examples.json"
    original = b'{"version":1}\n'
    source.write_bytes(original)
    snapshot, inode = selector_cli._sealed_read_snapshot(source, "synthetic examples")
    checks = 0
    links = 0
    original_link = selector_cli.os.link

    def changed_before_link() -> None:
        nonlocal checks
        checks += 1
        source.write_bytes(b'{"version":2}\n')
        selector_cli._verify_snapshot(source, snapshot, inode, "synthetic examples")

    def count_link(*args: Any, **kwargs: Any) -> None:
        nonlocal links
        links += 1
        original_link(*args, **kwargs)

    monkeypatch.setattr(selector_cli.os, "link", count_link)
    with pytest.raises(selector_cli.BeatCellSelectorCliError):
        selector_cli._atomic_publish_new(output, b"{}\n", precommit_check=changed_before_link)
    assert checks == 1
    assert links == 0
    assert not output.exists()


def test_atomic_publication_mutation_between_checks_rolls_back_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "selector" / "artifact.json"
    source = tmp_path / "examples.json"
    source.write_bytes(b'{"version":1}\n')
    snapshot, inode = selector_cli._sealed_read_snapshot(source, "synthetic examples")
    checks = 0
    original_link = selector_cli.os.link

    def verify() -> None:
        nonlocal checks
        checks += 1
        selector_cli._verify_snapshot(source, snapshot, inode, "synthetic examples")

    def mutate_after_link(*args: Any, **kwargs: Any) -> None:
        original_link(*args, **kwargs)
        source.write_bytes(b'{"version":2}\n')

    monkeypatch.setattr(selector_cli.os, "link", mutate_after_link)
    with pytest.raises(selector_cli.BeatCellSelectorCliError):
        selector_cli._atomic_publish_new(output, b"{}\n", precommit_check=verify)
    assert checks == 2
    assert not output.exists()


def test_snapshot_rejects_byte_identical_inode_replacement_before_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "selector" / "artifact.json"
    source = tmp_path / "examples.json"
    raw = b'{"version":1}\n'
    source.write_bytes(raw)
    snapshot, inode = selector_cli._sealed_read_snapshot(source, "synthetic examples")
    links = 0
    original_link = selector_cli.os.link

    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(raw)
    replacement.replace(source)

    def count_link(*args: Any, **kwargs: Any) -> None:
        nonlocal links
        links += 1
        original_link(*args, **kwargs)

    monkeypatch.setattr(selector_cli.os, "link", count_link)
    with pytest.raises(selector_cli.BeatCellSelectorCliError, match="bytes or inode changed"):
        selector_cli._atomic_publish_new(
            output,
            b"{}\n",
            precommit_check=lambda: selector_cli._verify_snapshot(source, snapshot, inode, "synthetic examples"),
        )
    assert links == 0
    assert not output.exists()


def test_train_cli_refuses_existing_destination_before_calling_trainer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector_path = tmp_path / "artifact.json"
    selector_path.write_text("{}\n", encoding="utf-8")
    examples_path = tmp_path / "examples-does-not-need-to-exist.json"
    called = False

    def forbidden(_examples: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal called
        called = True
        raise AssertionError("trainer ran despite an existing one-shot output")

    monkeypatch.setattr(selector_cli, "_official_paths", lambda _authority=None: (examples_path, selector_path))
    monkeypatch.setattr(selector_cli, "train_beat_cell_selector", forbidden)
    assert selector_cli.main(["train"]) == 1
    assert called is False


@pytest.mark.parametrize("field", ("schemaVersion", "featureSet", "singleJson"))
def test_selector_cli_rejects_split_publication_policy_tamper_before_access(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    authority = deepcopy(selector_cli.load_beat_cell_stage2_authority())
    authority["outputPaths"]["publication"][field] = "resealed-but-weakened"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        pytest.fail("source or destination access occurred after publication-policy tamper")

    monkeypatch.setattr(selector_cli, "load_beat_cell_stage2_authority", lambda: deepcopy(authority))
    monkeypatch.setattr(selector_cli, "_preflight_new_output", forbidden)
    monkeypatch.setattr(selector_cli, "_sealed_read_snapshot", forbidden)
    assert selector_cli.main(["train"]) == 1


def test_official_train_rejects_coherently_resealed_wrong_stage1_binding_before_fit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    examples_artifact: Mapping[str, Any],
) -> None:
    assert selector_cli._OFFICIAL_EXAMPLE_COUNT == 9376
    assert selector_cli._OFFICIAL_EXAMPLE_DURATION_MILLISECONDS == 5074349
    examples_path = tmp_path / "examples.json"
    selector_path = tmp_path / "selector.json"
    authority = _synthetic_official_authority(examples_artifact, examples_path, selector_path)
    tampered = deepcopy(dict(examples_artifact))
    tampered["sourceStage1DecisionSha256"] = _digest("coherently-resealed-wrong-stage1-decision")
    tampered["artifactSha256"] = canonical_sha256(
        {key: value for key, value in tampered.items() if key != "artifactSha256"}
    )
    validate_beat_cell_examples_artifact(tampered)
    examples_path.write_bytes(selector_cli._canonical_bytes(tampered))
    called = False

    def forbidden(_examples: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal called
        called = True
        raise AssertionError("trainer ran after an authority-binding mismatch")

    monkeypatch.setattr(selector_cli, "load_beat_cell_stage2_authority", lambda: deepcopy(authority))
    monkeypatch.setattr(selector_cli, "_OFFICIAL_EXAMPLE_COUNT", examples_artifact["exampleCount"])
    monkeypatch.setattr(
        selector_cli,
        "_OFFICIAL_EXAMPLE_DURATION_MILLISECONDS",
        examples_artifact["exampleDurationMilliseconds"],
    )
    monkeypatch.setattr(selector_cli, "train_beat_cell_selector", forbidden)
    assert selector_cli.main(["train"]) == 1
    assert called is False
    assert not selector_path.exists()


def test_validate_cli_rejects_byte_identical_selector_inode_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    examples_artifact: Mapping[str, Any],
    selector_artifact: Mapping[str, Any],
) -> None:
    examples_path = tmp_path / "examples.json"
    selector_path = tmp_path / "selector.json"
    examples_path.write_bytes(selector_cli._canonical_bytes(dict(examples_artifact)))
    selector_raw = selector_cli._canonical_bytes(dict(selector_artifact))
    selector_path.write_bytes(selector_raw)
    authority = _synthetic_official_authority(examples_artifact, examples_path, selector_path)
    called = False

    def replace_after_validation(_selector: Mapping[str, Any], _examples: Mapping[str, Any]) -> dict[str, Any]:
        nonlocal called
        called = True
        replacement = tmp_path / "selector-replacement.json"
        replacement.write_bytes(selector_raw)
        replacement.replace(selector_path)
        return {}

    monkeypatch.setattr(selector_cli, "load_beat_cell_stage2_authority", lambda: deepcopy(authority))
    monkeypatch.setattr(selector_cli, "_OFFICIAL_EXAMPLE_COUNT", examples_artifact["exampleCount"])
    monkeypatch.setattr(
        selector_cli,
        "_OFFICIAL_EXAMPLE_DURATION_MILLISECONDS",
        examples_artifact["exampleDurationMilliseconds"],
    )
    monkeypatch.setattr(
        selector_cli,
        "validate_beat_cell_selector_artifact",
        replace_after_validation,
    )
    assert selector_cli.main(["validate"]) == 1
    assert called is True
