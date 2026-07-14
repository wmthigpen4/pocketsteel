from __future__ import annotations

import json
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
    assert result["decisionModelStatus"] == MODEL_STATUS == "seed"
    assert result["routes"][0]["styleLabel"] == "Singing Steel"
    assert result["routes"][0]["decisionModelStatus"] == "seed"
    assert result["routes"][0]["targetCopedentId"] == "emmons-e9-basic"
