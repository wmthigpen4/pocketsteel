from __future__ import annotations

import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from pocketsteel.amazing_tablature_training import (
    AmazingTablatureTrainingStore,
    TrainingWorkflowError,
)
from pocketsteel.melody_assistant import melody_exercise_response
from pocketsteel.melody_decision_rules import MODEL_STATUS, style_catalog_payload
from pocketsteel.melody_ranker import train_pairwise_ranker


def write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    return path


def candidate(
    *,
    melody: int,
    texture: int,
    travel: int,
    controls: int,
    pocket: int,
    leading: int,
    sustained: int,
    repicked: int,
    role: str,
) -> dict[str, object]:
    lower = [melody - 12, melody - 7][: max(0, texture - 1)]
    return {
        "textureSize": texture,
        "barTravel": travel,
        "controlChanges": controls,
        "pocketChanges": pocket,
        "voiceLeading": leading,
        "sustainedVoices": sustained,
        "repickedVoices": repicked,
        "phraseRole": role,
        "mechanicallyValid": True,
        "voicePitchValues": lower + [melody],
    }


def annotation(
    decision_id: str,
    input_id: str,
    *,
    partition: str,
    benchmark: str = "",
    style: str = "vocal_steel",
) -> dict[str, object]:
    melody = 68
    role = "sustained_note" if partition == "train" else "cadence"
    return {
        "schemaVersion": "melody-decision-annotation-v2",
        "decisionId": decision_id,
        "inputId": input_id,
        "sourceCopedentId": "source-e9-abc-defg-v1",
        "styleFamily": style,
        "phraseRole": role,
        "datasetPartition": partition,
        "benchmarkGroup": benchmark,
        "reviewStatus": "machine_validated",
        "confidence": 0.98,
        "sourceAction": {
            "string": 4,
            "fret": 3,
            "startPitch": "G4",
            "destinationPitch": "G#4",
            "semitoneChange": 1,
            "controls": ["F"],
            "soundingStrings": [4, 5],
            "sustainedStrings": [5],
        },
        "abstractDecision": {
            "melodyPitch": "G#4",
            "melodyPitchValue": melody,
            "melodyRegister": 4,
            "textureSize": 2,
            "attackVoices": [4],
            "sustainedVoices": [5],
            "releasedVoices": [],
            "repickedVoices": [],
            "phraseRole": role,
            "harmonicFunction": "arrival",
            "pocketRole": "stay",
        },
        "chosen": candidate(
            melody=melody,
            texture=2,
            travel=0,
            controls=0,
            pocket=0,
            leading=1,
            sustained=1,
            repicked=0,
            role=role,
        ),
        "alternatives": [
            candidate(
                melody=melody,
                texture=3,
                travel=5,
                controls=2,
                pocket=1,
                leading=8,
                sustained=0,
                repicked=3,
                role=role,
            )
        ],
    }


def ingested_store(tmp_path: Path, *, evidence_type: str = "expert_score_tab") -> tuple[AmazingTablatureTrainingStore, str]:
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "page-1.jpg").write_bytes(b"private score/tab page one")
    (sources / "page-2.png").write_bytes(b"private score/tab page two")
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    status = store.ingest(
        sources,
        source_copedent_id="source-e9-abc-defg-v1",
        evidence_type=evidence_type,
        batch_id="atb-test-batch",
    )
    return store, status["batchId"]


INSPECTED_TRAINING_PAGES = {
    161,
    162,
    175,
    189,
    205,
    210,
    220,
    235,
    250,
    265,
    280,
    295,
    *range(299, 305),
    *range(310, 318),
    325,
    331,
    340,
    355,
    370,
    385,
    400,
    415,
    430,
    439,
}


def add_full_collection(
    store: AmazingTablatureTrainingStore,
    tmp_path: Path,
    *,
    batch_id: str = "atb-training-278",
) -> str:
    sources = tmp_path / f"{batch_id}-sources"
    sources.mkdir()
    for number in range(161, 440):
        if number == 427:
            continue
        (sources / f"IMG_{number:04d}.JPG").write_bytes(f"private-page-{number}".encode())
    status = store.ingest(
        sources,
        source_copedent_id="source-e9-abc-defg-v1",
        batch_id=batch_id,
    )
    assert status["counts"]["inputs"] == 278
    store.prepare_partition(
        batch_id,
        document_breaks=["IMG_0312.JPG"],
        forced_discovery=[f"IMG_{number:04d}.JPG" for number in sorted(INSPECTED_TRAINING_PAGES)],
        discovery_target=194,
        validation_target=28,
        test_target=56,
        guard_radius=1,
        similarity_threshold=3,
        seed=b"lane-15-private-split-seed-v1",
    )
    return batch_id


def add_train_and_holdout(store: AmazingTablatureTrainingStore, batch_id: str, tmp_path: Path) -> None:
    records = [
        annotation("decision-train", "input-0001", partition="train"),
        annotation(
            "decision-amazing-grace-holdout",
            "input-0002",
            partition="holdout",
            benchmark="Amazing Grace",
        ),
    ]
    store.import_annotations(batch_id, write_jsonl(tmp_path / "annotations.jsonl", records))
    status = store.validate(batch_id)
    assert status["counts"]["accepted"] == 2
    assert status["counts"]["blockingExceptions"] == 0


def test_ingest_is_immutable_idempotent_and_resumable(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    status = store.batch_status(batch_id)

    assert status["counts"]["inputs"] == 2
    assert status["checkpoints"]["ingest"]["status"] == "completed"
    assert status["checkpoints"]["annotate"]["status"] == "pending"
    work = (tmp_path / "private/batches/atb-test-batch/annotation-work.jsonl").read_text(encoding="utf-8")
    assert "private score/tab" not in work
    assert "page-1.jpg" in work

    same = store.ingest(
        tmp_path / "sources",
        source_copedent_id="source-e9-abc-defg-v1",
        batch_id=batch_id,
    )
    assert same["immutableDigest"] == status["immutableDigest"]

    (tmp_path / "sources/page-1.jpg").write_bytes(b"changed private page")
    with pytest.raises(TrainingWorkflowError, match="collision"):
        store.ingest(
            tmp_path / "sources",
            source_copedent_id="source-e9-abc-defg-v1",
            batch_id=batch_id,
        )


def test_ingest_rejects_unknown_source_copedent(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "page.jpg").write_bytes(b"page")
    store = AmazingTablatureTrainingStore(tmp_path / "private")

    with pytest.raises(TrainingWorkflowError, match="Unknown source copedent"):
        store.ingest(sources, source_copedent_id="mystery-e9")
    with pytest.raises(TrainingWorkflowError, match="quarantined"):
        store.ingest(
            sources,
            source_copedent_id="source-e9-abc-defg-v1",
            source_copedent_confidence="unknown",
        )


def test_lick_collection_excludes_copedent_evidence_and_seals_page_units(tmp_path: Path) -> None:
    sources = tmp_path / "licks"
    sources.mkdir()
    (sources / "IMG_0441.JPG").write_bytes(b"private copedent chart")
    for number in range(442, 476):
        (sources / f"IMG_{number:04d}.JPG").write_bytes(f"private-lick-page-{number}".encode())

    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    batch_id = "atb-licks-34"
    status = store.ingest(
        sources,
        source_copedent_id="source-e9-abc-defg-d48-e29-v1",
        source_copedent_evidence=["IMG_0441.JPG"],
        batch_id=batch_id,
    )

    assert status["counts"]["inputs"] == 34
    assert status["counts"]["copedentEvidence"] == 1
    assert status["sourceCopedentEvidenceCount"] == 1
    verification = store.verify_batch_inputs(batch_id)
    assert verification["assetCount"] == 35
    assert verification["verifiedCount"] == 35
    assert verification["sourceUnchanged"] is True

    store.prepare_partition(
        batch_id,
        document_breaks=[],
        forced_discovery=["IMG_0442.JPG", "IMG_0459.JPG", "IMG_0475.JPG"],
        content_unit_breaks=[f"IMG_{number:04d}.JPG" for number in range(443, 476)],
        discovery_target=24,
        validation_target=3,
        test_target=7,
        guard_radius=0,
        similarity_threshold=3,
        seed=b"lane-15-private-lick-split-seed-v1",
    )
    status = store.batch_status(batch_id)
    partition = status["partition"]
    assert partition["status"] == "sealed_unopened"
    assert partition["groupingReviewStatus"] == "provisional_explicit_units"
    assert partition["counts"] == {"total": 34, "discovery": 24, "validation": 3, "test": 7}
    assert partition["contentUnitCounts"] == {"discovery": 24, "validation": 3, "test": 7}

    batch_dir = tmp_path / f"private/batches/{batch_id}"
    discovery = [json.loads(line) for line in (batch_dir / "discovery-work.jsonl").read_text().splitlines()]
    discovery_paths = {record["relativePath"] for record in discovery}
    assert {"IMG_0442.JPG", "IMG_0459.JPG", "IMG_0475.JPG"} <= discovery_paths
    assert "IMG_0441.JPG" not in (batch_dir / "annotation-work.jsonl").read_text()
    sealed = json.loads((batch_dir / "sealed-test/test-manifest.json").read_text())
    assert len(sealed["inputs"]) == 7
    assert sealed["status"] == "sealed_unopened"


def test_validation_uses_stable_controls_and_writes_exception_queue(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    valid = annotation("valid", "input-0001", partition="train")
    invalid = annotation("label-is-not-a-stable-id", "input-0002", partition="holdout", benchmark="Amazing Grace")
    invalid["sourceAction"]["controls"] = ["F lever"]  # type: ignore[index]
    source = write_jsonl(tmp_path / "annotations.jsonl", [valid, invalid])
    store.import_annotations(batch_id, source)
    status = store.validate(batch_id)

    assert status["counts"]["accepted"] == 1
    assert status["counts"]["blockingExceptions"] == 1
    exceptions = [
        json.loads(line)
        for line in (tmp_path / "private/batches/atb-test-batch/exceptions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert any("Unknown source control IDs" in item.get("message", "") for item in exceptions)

    changed = [annotation("different", "input-0001", partition="train")]
    with pytest.raises(TrainingWorkflowError, match="immutable"):
        store.import_annotations(batch_id, write_jsonl(tmp_path / "changed.jsonl", changed))


def test_review_corrections_do_not_overwrite_raw_annotations(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    record = annotation("needs-correction", "input-0001", partition="train")
    record["sourceAction"]["controls"] = ["F lever"]  # type: ignore[index]
    annotations = write_jsonl(tmp_path / "annotations.jsonl", [record])
    store.import_annotations(batch_id, annotations)
    assert store.validate(batch_id)["counts"]["accepted"] == 0

    replacement = annotation("needs-correction", "input-0001", partition="train")
    resolutions = write_jsonl(
        tmp_path / "reviews.jsonl",
        [{"decisionId": "needs-correction", "action": "correct", "replacement": replacement}],
    )
    status = store.apply_review(batch_id, resolutions)

    assert status["counts"]["accepted"] == 1
    raw = (tmp_path / "private/batches/atb-test-batch/annotations.jsonl").read_text(encoding="utf-8")
    assert "F lever" in raw
    assert (tmp_path / "private/batches/atb-test-batch/review-resolutions.jsonl").exists()


def test_training_is_deterministic_and_feedback_has_lower_authority(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    add_train_and_holdout(store, batch_id, tmp_path)

    first = store.train(epochs=4, learning_rate=0.05)
    second = store.train(epochs=4, learning_rate=0.05)

    assert first["modelId"] == second["modelId"]
    assert first["datasetHash"] == second["datasetHash"]
    assert first["weightsByStyle"] == second["weightsByStyle"]
    assert first["privacy"] == {"containsProfileSnapshots": False, "containsSourceContent": False}
    serialized = json.dumps(first)
    assert "sourceAction" not in serialized
    assert "decision-amazing-grace" not in serialized

    chosen = annotation("weight", "input-0001", partition="train")["chosen"]
    alternative = annotation("weight", "input-0001", partition="train")["alternatives"]
    expert = train_pairwise_ranker(
        [{"styleFamily": "vocal_steel", "chosen": chosen, "alternatives": alternative, "evidenceWeight": 1.0}],
        epochs=1,
    )
    feedback = train_pairwise_ranker(
        [{"styleFamily": "vocal_steel", "chosen": chosen, "alternatives": alternative, "evidenceWeight": 0.25}],
        epochs=1,
    )
    assert expert.weights_by_style["vocal_steel"]["bar_travel"] == pytest.approx(
        feedback.weights_by_style["vocal_steel"]["bar_travel"] * 4
    )


def test_evaluate_report_promote_and_rollback_exact_models(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    add_train_and_holdout(store, batch_id, tmp_path)
    first = store.train(epochs=3)
    first_evaluation = store.evaluate(first["modelId"])
    report = store.report(first["modelId"])

    assert first_evaluation["gate"]["passed"] is True
    assert first_evaluation["benchmarkCounts"] == {"amazing_grace": 1}
    assert "private score/tab" not in report.read_text(encoding="utf-8")
    with pytest.raises(TrainingWorkflowError, match="Lane 15"):
        store.promote(
            first["modelId"],
            channel="stable",
            approval_reference="creator approved first",
        )

    lane15 = tmp_path / "2026-07-14-15-amazing-tablature-qa.md"
    lane15.write_text("independent QA passed\n", encoding="utf-8")
    beta = store.promote(first["modelId"], channel="beta", approval_reference="creator approved first beta")
    stable = store.promote(
        first["modelId"],
        channel="stable",
        approval_reference="creator approved first stable",
        lane15_handoff=lane15,
    )
    assert beta["modelId"] == stable["modelId"] == first["modelId"]

    second = store.train(epochs=5)
    assert second["modelId"] != first["modelId"]
    assert store.evaluate(second["modelId"])["gate"]["passed"] is True
    store.promote(
        second["modelId"],
        channel="stable",
        approval_reference="creator approved second stable",
        lane15_handoff=lane15,
    )
    rolled_back = store.rollback(
        channel="stable",
        model_id=first["modelId"],
        approval_reference="creator requested rollback",
    )
    assert rolled_back["previousModelId"] == second["modelId"]
    assert store.status()["channels"]["stable"] == first["modelId"]

    promotion = json.loads(
        (tmp_path / f"private/promotions/stable-{second['modelId']}.json").read_text(encoding="utf-8")
    )
    assert set(promotion) == {
        "copedentNeutral",
        "exampleCount",
        "featureNames",
        "featureSchemaVersion",
        "modelId",
        "privacy",
        "schemaVersion",
        "status",
        "weightsByStyle",
    }


def test_cli_status_uses_the_same_durable_store(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/amazing_tablature.py",
            "--root",
            str(tmp_path / "private"),
            "batch-status",
            batch_id,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["batchId"] == batch_id
    assert payload["checkpoints"]["annotate"]["status"] == "pending"


def test_full_collection_partition_is_sealed_and_leakage_safe(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    batch_id = add_full_collection(store, tmp_path)
    status = store.batch_status(batch_id)
    partition = status["partition"]

    assert partition["status"] == "sealed_unopened"
    assert partition["groupingReviewStatus"] == "provisional_structural"
    assert partition["stratificationStatus"]["pageTypeAndMusicalContent"] == "pending_independent_review"
    assert partition["counts"]["total"] == 278
    assert 26 <= partition["counts"]["validation"] <= 30
    assert 54 <= partition["counts"]["test"] <= 58
    assert sum(partition["counts"][name] for name in ("discovery", "validation", "test")) == 278
    assert partition["sealedTest"] == {
        "groundTruthStatus": "pending",
        "membershipExposedInStatus": False,
        "status": "sealed_unopened",
    }
    assert "relativePath" not in json.dumps(status)

    batch_dir = tmp_path / f"private/batches/{batch_id}"
    discovery = [json.loads(line) for line in (batch_dir / "discovery-work.jsonl").read_text().splitlines()]
    validation = [json.loads(line) for line in (batch_dir / "validation-work.jsonl").read_text().splitlines()]
    sealed = json.loads((batch_dir / "sealed-test/test-manifest.json").read_text())
    test = sealed["inputs"]
    assert len(discovery) == partition["counts"]["discovery"]
    assert len(validation) == partition["counts"]["validation"]
    assert len(test) == partition["counts"]["test"]
    assert {record["sourceDocumentId"] for record in discovery} == {
        "source-document-001",
        "source-document-002",
    }
    assert {record["sourceDocumentId"] for record in validation} == {
        "source-document-001",
        "source-document-002",
    }
    assert {record["sourceDocumentId"] for record in test} == {
        "source-document-001",
        "source-document-002",
    }

    discovery_paths = {record["relativePath"] for record in discovery}
    held_out_paths = {record["relativePath"] for record in validation + test}
    assert not discovery_paths & held_out_paths
    for number in INSPECTED_TRAINING_PAGES:
        assert f"IMG_{number:04d}.JPG" in discovery_paths
    assert not any(path in (batch_dir / "annotation-work.jsonl").read_text() for path in held_out_paths)
    assert stat.S_IMODE((batch_dir / "sealed-test").stat().st_mode) == 0o700
    assert stat.S_IMODE((batch_dir / "sealed-test/test-manifest.json").stat().st_mode) == 0o600

    same = store.prepare_partition(
        batch_id,
        document_breaks=["IMG_0312.JPG"],
        forced_discovery=[f"IMG_{number:04d}.JPG" for number in sorted(INSPECTED_TRAINING_PAGES)],
        discovery_target=194,
        validation_target=28,
        test_target=56,
        seed=b"different-seed-is-ignored-after-sealing",
    )
    assert same["partition"]["partitionDigest"] == partition["partitionDigest"]
    with pytest.raises(TrainingWorkflowError, match="already sealed"):
        store.prepare_partition(
            batch_id,
            document_breaks=["IMG_0312.JPG"],
            forced_discovery=["IMG_0161.JPG"],
            discovery_target=194,
            validation_target=28,
            test_target=56,
        )


def test_partition_binding_and_superseded_batch_exclusion(tmp_path: Path) -> None:
    store, old_batch_id = ingested_store(tmp_path)
    add_train_and_holdout(store, old_batch_id, tmp_path)
    old_model = store.train(epochs=2)
    replacement_batch_id = add_full_collection(store, tmp_path)
    batch_dir = tmp_path / f"private/batches/{replacement_batch_id}"
    discovery = [json.loads(line) for line in (batch_dir / "discovery-work.jsonl").read_text().splitlines()]
    validation = [json.loads(line) for line in (batch_dir / "validation-work.jsonl").read_text().splitlines()]
    test = json.loads((batch_dir / "sealed-test/test-manifest.json").read_text())["inputs"]

    wrong_validation = annotation("wrong-validation", validation[0]["inputId"], partition="train")
    with pytest.raises(TrainingWorkflowError, match="sealed validation"):
        store.import_annotations(
            replacement_batch_id,
            write_jsonl(tmp_path / "wrong-validation.jsonl", [wrong_validation]),
        )
    sealed_test = annotation("sealed-test", test[0]["inputId"], partition="test")
    with pytest.raises(TrainingWorkflowError, match="Sealed-test"):
        store.import_annotations(
            replacement_batch_id,
            write_jsonl(tmp_path / "sealed-test.jsonl", [sealed_test]),
        )

    records = [
        annotation("replacement-discovery", discovery[0]["inputId"], partition="discovery"),
        annotation("replacement-validation", validation[0]["inputId"], partition="validation"),
    ]
    store.import_annotations(replacement_batch_id, write_jsonl(tmp_path / "replacement.jsonl", records))
    store.supersede_batch(
        old_batch_id,
        replacement_batch_id=replacement_batch_id,
        approval_reference="user replaced the 51 images with the 278-image collection",
    )
    status = store.status()
    assert status["authoritativeBatchId"] == replacement_batch_id
    assert store.batch_status(old_batch_id)["lifecycleStatus"] == "superseded"
    assert status["models"][old_model["modelId"]]["datasetEligibility"] == "historical_superseded"
    assert status["models"][old_model["modelId"]]["eligibleForFutureComparison"] is False
    with pytest.raises(TrainingWorkflowError, match="No validated training decisions"):
        store.train(epochs=2)
    with pytest.raises(TrainingWorkflowError, match="superseded"):
        store.validate(old_batch_id)


def test_player_facing_styles_are_descriptive_and_copedent_neutral() -> None:
    catalog = style_catalog_payload()
    assert [item["label"] for item in catalog] == [
        "Best Fit",
        "Singing Steel",
        "Pedal & Lever Motion",
        "Pocket Playing",
        "Smooth Harmony",
        "Fast & Clean",
        "Full Harmony",
    ]
    result = melody_exercise_response(
        "Arrange this in a singing style",
        {
            "key": "G",
            "styleFamily": "vocal_steel",
            "melody": [{"pitch": "G4", "pitchValue": 67, "chord": "G", "durationBeats": 2}],
        },
    )["melody_exercise"]

    assert result["styleLabel"] == "Singing Steel"
    assert result["decisionModelStatus"] == MODEL_STATUS == "approved_beta"
    assert result["routes"][0]["styleLabel"] == "Singing Steel"
    assert result["routes"][0]["decisionModelStatus"] == "approved_beta"
    assert result["routes"][0]["targetCopedentId"] == "emmons-e9-basic"
