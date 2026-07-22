from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from pocketsteel.amazing_tablature_extraction import (
    EXTRACTION_SCHEMA_VERSION,
    EXTRACTOR_VERSION,
    KNOWLEDGE_SCHEMA_VERSION,
)
from pocketsteel.amazing_tablature_sealed_test import SealedTestCoordinator, SealedTestWorkflowError


RIGHTS_DIGEST = "a" * 64


class _FakeTabVision:
    model = "synthetic-sealed-reader"

    @staticmethod
    def contract() -> dict[str, str]:
        return {"model": _FakeTabVision.model, "promptVersion": "synthetic-v1"}


class _FakeExtractor:
    def __init__(self, records: dict[str, dict[str, Any]]) -> None:
        self.records = records
        self.tab_vision = _FakeTabVision()
        self.page_numbers: list[int] = []

    def _extract_page(self, _manifest: dict[str, Any], item: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.page_numbers.append(int(kwargs["page_number"]))
        return copy.deepcopy(self.records[str(item["inputId"])])


def test_sealed_evaluation_rejects_a_concurrent_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coordinator = SealedTestCoordinator(tmp_path)

    def busy_lock(*_args: object) -> None:
        raise BlockingIOError

    monkeypatch.setattr("pocketsteel.amazing_tablature_sealed_test.fcntl.flock", busy_lock)
    with pytest.raises(SealedTestWorkflowError, match="already has a sealed evaluation in progress"):
        coordinator.run("freeze-concurrent")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _reviewed_decision(page_number: int, mode: str) -> dict[str, Any]:
    return {
        "decisionId": f"decision-{page_number}-{mode}",
        "styleFamily": "single_note_run",
        "chosen": {
            "textureSize": 1,
            "barTravel": 0,
            "controlChanges": 0,
            "pocketChanges": 0,
            "voiceLeading": 0,
            "sustainedVoices": 0,
            "repickedVoices": 0,
            "phraseRole": "passing_tone",
            "mechanicallyValid": True,
            "voicePitchValues": [64],
        },
        "alternatives": [
            {
                "textureSize": 1,
                "barTravel": 3,
                "controlChanges": 1,
                "pocketChanges": 1,
                "voiceLeading": 2,
                "sustainedVoices": 0,
                "repickedVoices": 0,
                "phraseRole": "passing_tone",
                "mechanicallyValid": True,
                "voicePitchValues": [64],
            }
        ],
        "scoreToTabSupport": {"mode": mode},
        "categoryTags": [f"alignment:{mode}", "page:synthetic"],
        "reviewState": "human_approved",
    }


def _reviewed_record(batch_id: str, item: dict[str, Any], page_number: int) -> dict[str, Any]:
    return {
        "schemaVersion": EXTRACTION_SCHEMA_VERSION,
        "knowledgeSchemaVersion": KNOWLEDGE_SCHEMA_VERSION,
        "extractorVersion": EXTRACTOR_VERSION,
        "batchId": batch_id,
        "inputId": item["inputId"],
        "datasetPartition": "test",
        "sourceDocumentId": item["sourceDocumentId"],
        "contentUnitId": item["contentUnitId"],
        "assetSha256": item["sha256"],
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "sourceStructure": {
            "orientation": "portrait",
            "luminanceBin": "middle",
            "densityBin": "low",
        },
        "pageOrientation": {
            "upright": True,
            "orientation": "portrait",
            "exifOrientationApplied": True,
            "deskewDegrees": 0.0,
        },
        "pageClassification": {"primary": "prose_concept_page"},
        "scoreSystems": [],
        "tabSystems": [],
        "eventAlignments": [],
        "grips": [],
        "movementSequences": [],
        "derivedDecisions": [
            _reviewed_decision(page_number, "score_supported"),
            _reviewed_decision(page_number, "tab_only"),
        ],
        "teachingConcepts": [],
        "exercises": [],
        "unresolved": [],
        "provenance": {
            "assetSha256": item["sha256"],
            "pageNumberInBatch": page_number,
        },
        "rightsAndAccess": {
            "rightsStatus": "user_provided_authorized",
            "accessClassification": "private_research",
            "authorizationRecordDigest": RIGHTS_DIGEST,
            "allowedUses": {"privateEvaluation": True},
        },
        "reviewState": "human_approved",
        "humanApprovalComplete": True,
        "humanReview": {"reviewerReference": "independent-lane-15-test-reviewer"},
    }


def test_sealed_cohort_is_scored_once_then_becomes_a_regression_set(tmp_path: Path) -> None:
    private = tmp_path / "private"
    source = tmp_path / "source"
    source.mkdir()
    batch_id = "batch-1"
    freeze_id = "freeze-1"
    partition_digest = "partition-digest-1"
    inputs: list[dict[str, Any]] = []
    for page_number in (1, 2):
        input_id = f"input-{page_number:04d}"
        relative_path = f"page-{page_number}.jpg"
        payload = f"sealed-page-{page_number}".encode()
        (source / relative_path).write_bytes(payload)
        inputs.append(
            {
                "inputId": input_id,
                "relativePath": relative_path,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "sourceDocumentId": "source-document-001",
                "contentUnitId": f"content-unit-{page_number:03d}",
                "datasetPartition": "test",
            }
        )

    batch_dir = private / "batches" / batch_id
    _write_json(
        batch_dir / "manifest.json",
        {
            "batchId": batch_id,
            "sourceRoot": str(source),
            "sourceCopedentId": "source-e9-abc-defg-v1",
            "sourceCopedentRevision": 1,
        },
    )
    _write_json(
        batch_dir / "sealed-test" / "test-manifest.json",
        {"batchId": batch_id, "partitionDigest": partition_digest, "inputs": inputs},
    )
    _write_json(batch_dir / "sealed-test" / "ground-truth-status.json", {"status": "pending"})
    _write_json(
        batch_dir / "rights-and-access.json",
        {
            "batchId": batch_id,
            "rightsStatus": "user_provided_authorized",
            "reviewStatus": "approved",
            "recordDigest": RIGHTS_DIGEST,
            "revision": 1,
            "allowedUses": {"privateExtraction": True, "privateEvaluation": True, "modelTraining": True},
        },
    )
    _write_json(
        private / "rules-freezes" / f"{freeze_id}.json",
        {
            "freezeId": freeze_id,
            "status": "frozen_tests_unopened",
            "rulesEngineDigest": "rules-engine-digest",
            "modelId": "model-1",
            "modelArtifactDigest": "pending",
            "authoritativeDatasetId": "dataset-1",
            "contracts": {
                "extractorVersion": EXTRACTOR_VERSION,
                "extractionSchemaVersion": EXTRACTION_SCHEMA_VERSION,
                "knowledgeSchemaVersion": KNOWLEDGE_SCHEMA_VERSION,
            },
            "codeFileDigests": {},
            "validationExtractionContracts": {
                batch_id: {
                    "ocrReaderContract": None,
                    "omrReaderContract": None,
                    "tabReaderContract": _FakeTabVision.contract(),
                }
            },
            "sealedModelEvaluationPolicy": {
                "metricVersion": "sealed-pairwise-preference-v1",
                "preferenceAccuracyFloor": 0.5,
                "minimumDecisionCountPerCohort": 1,
                "requiresScoreBackedDecisionsOverall": True,
                "requiresTabOnlyDecisionsOverall": True,
            },
            "sealedTestCohorts": [
                {
                    "batchId": batch_id,
                    "partitionDigest": partition_digest,
                    "testCount": len(inputs),
                    "sourceCopedentId": "source-e9-abc-defg-v1",
                    "sourceCopedentRevision": 1,
                    "sourceCopedentDigest": "source-copedent-digest-1",
                    "rightsAuthorizationDigest": RIGHTS_DIGEST,
                }
            ],
        },
    )

    model = {
        "modelId": "model-1",
        "weightsByStyle": {
            "single_note_run": {
                "bar_travel": 1.0,
                "control_changes": 1.0,
                "pocket_changes": 1.0,
                "voice_leading": 1.0,
            }
        },
    }
    _write_json(private / "models" / "model-1.json", model)
    freeze_path = private / "rules-freezes" / f"{freeze_id}.json"
    freeze_record = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze_record["modelArtifactDigest"] = _digest(model)
    _write_json(freeze_path, freeze_record)

    reviewed = {
        item["inputId"]: _reviewed_record(batch_id, item, page_number)
        for page_number, item in enumerate(inputs, start=1)
    }
    fake = _FakeExtractor(reviewed)
    coordinator = SealedTestCoordinator(private, repo_root=tmp_path, extractor=fake)  # type: ignore[arg-type]

    prepared = coordinator.prepare_ground_truth(batch_id, freeze_id=freeze_id)
    assert prepared["status"] == "annotation_in_progress"
    ground_truth_source = tmp_path / "ground-truth.jsonl"
    ground_truth_source.write_text(
        "\n".join(json.dumps(reviewed[item["inputId"]], sort_keys=True) for item in inputs) + "\n",
        encoding="utf-8",
    )
    imported = coordinator.import_ground_truth(batch_id, ground_truth_source, freeze_id=freeze_id)
    assert imported["status"] == "ready"

    official = coordinator.run(freeze_id, workers=2)
    assert official["sourceCopedentProfiles"] == [
        {
            "batchId": batch_id,
            "id": "source-e9-abc-defg-v1",
            "revision": 1,
            "digest": "source-copedent-digest-1",
        }
    ]
    assert official["gatePassed"] is True
    assert official["tabChoicePredictionGatePassed"] is True
    assert official["tabChoicePrediction"]["overall"]["preferenceAccuracy"] == 1.0
    assert official["tabChoicePrediction"]["byEvidenceMode"]["score_supported"]["decisionCount"] == 2
    assert official["tabChoicePrediction"]["byEvidenceMode"]["tab_only"]["decisionCount"] == 2
    assert official["testPageCount"] == 2
    assert sorted(fake.page_numbers) == [1, 2]
    evaluation_dir = private / "sealed-evaluations" / freeze_id
    official_path = evaluation_dir / "official-score.json"
    official_bytes = official_path.read_bytes()
    assert not (evaluation_dir / "detailed-failures.json").exists()

    call_count = len(fake.page_numbers)
    status_path = batch_dir / "sealed-test" / "ground-truth-status.json"
    interrupted_status = json.loads(status_path.read_text())
    interrupted_status["status"] = "evaluation_in_progress"
    interrupted_status["testRunCount"] = 0
    _write_json(status_path, interrupted_status)
    assert coordinator.run(freeze_id, workers=2) == official
    assert len(fake.page_numbers) == call_count
    status = json.loads(status_path.read_text())
    assert status["testRunCount"] == 1
    assert status["status"] == "official_score_recorded"

    details = coordinator.release_failure_details(freeze_id)
    assert details["failedPageCount"] == 0
    assert details["holdoutStatus"] == "regression_set"
    status = json.loads(status_path.read_text())
    assert status["status"] == "regression_set"
    assert official_path.read_bytes() == official_bytes
