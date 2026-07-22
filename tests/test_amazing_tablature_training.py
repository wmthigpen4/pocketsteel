from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from pocketsteel.amazing_tablature_training import (
    AmazingTablatureTrainingStore,
    TrainingWorkflowError,
    VALIDATION_LINE_PREFLIGHT_VERSION,
    _challenger_line_previously_reviewed,
    _discovery_line_review_readiness,
)
from pocketsteel.e9_copedents import get_e9_copedent_profile
from pocketsteel.melody_assistant import melody_exercise_response
from pocketsteel.melody_decision_rules import MODEL_STATUS, style_catalog_payload
from pocketsteel.melody_ranker import feature_vector, train_pairwise_ranker


def test_discovery_line_readiness_is_line_scoped_and_explains_page_gates() -> None:
    ready, reasons = _discovery_line_review_readiness(
        page_human_approved=True,
        current_tab_revision_confirmed=True,
    )
    assert ready is True
    assert reasons == []

    ready, reasons = _discovery_line_review_readiness(
        page_human_approved=False,
        current_tab_revision_confirmed=False,
    )
    assert ready is False
    assert reasons == [
        "page_not_human_approved",
        "current_tab_revision_not_confirmed",
    ]

    ready, reasons = _discovery_line_review_readiness(
        page_human_approved=True,
        current_tab_revision_confirmed=True,
        challenger_line_previously_reviewed=True,
    )
    assert ready is False
    assert reasons == ["challenger_line_previously_reviewed"]


def test_challenger_rereview_guard_survives_score_system_id_change() -> None:
    assert _challenger_line_previously_reviewed(
        input_id="input-1",
        score_system_id="recaptured-system",
        decision_ids=["decision-reviewed", "decision-new"],
        reviewed_line_keys={("input-1", "original-system")},
        reviewed_decision_ids={"decision-reviewed"},
    ) is True

    assert _challenger_line_previously_reviewed(
        input_id="input-1",
        score_system_id="different-line",
        decision_ids=["decision-new"],
        reviewed_line_keys={("input-1", "original-system")},
        reviewed_decision_ids={"decision-reviewed"},
    ) is False


def test_decision_candidates_retain_concrete_mechanical_actions() -> None:
    from pocketsteel.amazing_tablature_decisions import _candidate

    previous = [
        {
            "string": 5,
            "fret": 3,
            "controls": [],
            "soundingPitchValue": 60,
            "attack": True,
        }
    ]
    current = [
        {
            "string": 4,
            "fret": 5,
            "controls": ["F"],
            "soundingPitchValue": 65,
            "attack": True,
        }
    ]

    result = _candidate(current, previous, phrase_role="passing_tone")

    assert result["mechanicalActions"] == [
        {
            "string": 4,
            "fret": 5,
            "controls": ["F"],
            "soundingPitchValue": 65,
            "attack": True,
        }
    ]


def test_decision_candidate_captures_phrase_sequence_context() -> None:
    from pocketsteel.amazing_tablature_decisions import _candidate

    previous = [
        {
            "string": 5,
            "fret": 3,
            "controls": [],
            "soundingPitchValue": 60,
            "attack": True,
        }
    ]
    current = [
        {
            "string": 4,
            "fret": 5,
            "controls": ["F"],
            "soundingPitchValue": 65,
            "attack": True,
        }
    ]
    following = [
        {
            "string": 4,
            "fret": 6,
            "controls": ["F"],
            "soundingPitchValue": 66,
            "attack": False,
        }
    ]

    result = _candidate(
        current,
        previous,
        phrase_role="passing_tone",
        next_actions=following,
    )
    features = feature_vector(result)

    assert result["incomingStringDistance"] == 1
    assert result["outgoingBarTravel"] == 1
    assert result["outgoingSustainContinuity"] == 1
    assert result["fretDirectionContinuation"] == 1
    assert features["incoming_string_distance"] == 1
    assert features["outgoing_sustain_continuity"] == 1
    assert features["fret_direction_continuation"] == 1


def write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    return path


def canonical_sha(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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


def test_structured_input_ranking_reports_conservative_top_one_and_top_three() -> None:
    model = {"weightsByStyle": {"single_note_run": {"bar_travel": 1.0}}}
    records = []
    for index in range(20):
        records.append(
            {
                "styleFamily": "single_note_run",
                "chosen": {"textureSize": 1, "barTravel": 1 if index == 19 else 0},
                "alternatives": [
                    {"textureSize": 1, "barTravel": 0 if index == 19 else 1}
                ],
            }
        )

    metrics = AmazingTablatureTrainingStore._model_ranking_metrics(model, records)

    assert metrics == {
        "decisionCount": 20,
        "topChoiceCorrectCount": 19,
        "topChoiceAccuracy": 0.95,
        "topThreeCoveredCount": 20,
        "topThreeCoverage": 1.0,
    }
    assert not metrics["topChoiceAccuracy"] > 0.95


def test_validation_ranking_separates_preference_and_mechanical_safety() -> None:
    model = {"weightsByStyle": {"single_note_run": {"bar_travel": 1.0}}}
    records = [
        {
            "styleFamily": "single_note_run",
            "chosen": {
                "textureSize": 1,
                "barTravel": 0,
                "mechanicallyValid": True,
            },
            "alternatives": [
                {
                    "textureSize": 1,
                    "barTravel": 1,
                    "mechanicallyValid": True,
                }
            ],
        },
        {
            "styleFamily": "single_note_run",
            "chosen": {
                "textureSize": 1,
                "barTravel": 1,
                "mechanicallyValid": True,
            },
            "alternatives": [
                {
                    "textureSize": 1,
                    "barTravel": 0,
                    "mechanicallyValid": False,
                }
            ],
        },
    ]

    metrics = AmazingTablatureTrainingStore._validation_ranking_metrics(model, records)

    assert metrics["topChoiceAccuracy"] == 0.5
    assert metrics["topThreeCoverage"] == 1.0
    assert metrics["approvedSourceMechanicalAccuracy"] == 1.0
    assert metrics["predictedTopMechanicalAccuracy"] == 0.5


def test_validation_line_scorer_verifies_receipts_without_training(tmp_path: Path) -> None:
    root = tmp_path / "private"
    model_id = "at-validation-model"
    batch_id = "atb-validation-batch"
    model_path = root / "models" / f"{model_id}.json"
    model_path.parent.mkdir(parents=True)
    model = {
        "modelId": model_id,
        "codeRevision": "discovery-only-revision",
        "weightsByStyle": {"single_note_run": {"bar_travel": 1.0}},
    }
    model_path.write_text(json.dumps(model, sort_keys=True) + "\n", encoding="utf-8")
    model_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    registry = {
        "schemaVersion": "amazing-tablature-training-v1",
        "batches": {batch_id: {"lifecycleStatus": "active"}},
        "models": {
            model_id: {
                "artifact": f"models/{model_id}.json",
                "artifactSha256": model_sha,
                "datasetEligibility": "complete_discovery",
                "canonicalEvaluationEligible": True,
                "sourceBatchIds": [batch_id],
                "status": "challenger",
            }
        },
        "channels": {"beta": None, "stable": None},
        "authoritativeBatchId": batch_id,
        "authoritativeDataset": {"batchIds": [batch_id]},
        "datasetHistory": [],
        "rollbackHistory": [],
        "rulesFreezes": {},
        "discoverySeeds": {},
        "requiredBenchmarkGroups": [],
    }
    root.mkdir(exist_ok=True)
    (root / "training-registry.json").write_text(
        json.dumps(registry, sort_keys=True) + "\n", encoding="utf-8"
    )

    input_id = "input-0001"
    score_system_id = "score-system-1"
    tab_system_id = "tab-system-1"
    tab_event_id = "tab-event-1"
    chosen = {"textureSize": 1, "barTravel": 0, "mechanicallyValid": True}
    alternative = {"textureSize": 1, "barTravel": 1, "mechanicallyValid": True}
    page_record = {
        "inputId": input_id,
        "datasetPartition": "validation",
        "tabSystems": [
            {"tabSystemId": tab_system_id, "tabEvents": [{"tabEventId": tab_event_id}]}
        ],
        "derivedDecisions": [
            {
                "decisionId": "decision-1",
                "sourceTabEventId": tab_event_id,
                "styleFamily": "single_note_run",
                "categoryTags": ["alignment:score_supported"],
                "chosen": chosen,
                "alternatives": [alternative],
            }
        ],
    }
    machine_digest = canonical_sha(page_record)
    page_path = (
        root
        / "batches"
        / batch_id
        / "extraction"
        / "validation"
        / "pages"
        / f"{input_id}.json"
    )
    page_path.parent.mkdir(parents=True)
    page_path.write_text(json.dumps(page_record, sort_keys=True) + "\n", encoding="utf-8")

    system = {
        "inputId": input_id,
        "scoreSystemId": score_system_id,
        "tabSystemId": tab_system_id,
        "machineRecordDigest": machine_digest,
        "capturePreflightPassed": True,
        "validationIssueSummary": {"blockingCount": 0, "digest": "issues-1"},
    }
    packet_core = {
        "schemaVersion": "amazing-tablature-validation-line-audit-v1",
        "reviewType": "validation_line_audit",
        "preflightVersion": VALIDATION_LINE_PREFLIGHT_VERSION,
        "batchId": batch_id,
        "partition": "validation",
        "validationRunDigest": "validation-run-1",
        "validationModel": {"modelId": model_id, "artifactSha256": model_sha},
        "pages": [
            {
                "inputId": input_id,
                "systems": [
                    system,
                    {
                        **system,
                        "scoreSystemId": "score-system-capture-failed",
                    },
                ],
            }
        ],
        "validationPageCount": 1,
        "noLinePages": [],
        "noLinePageCount": 0,
        "lineCount": 2,
        "trainingEligible": False,
        "validationGroundTruthMayTrain": False,
        "sealedTestAccessed": False,
    }
    packet_digest = canonical_sha(packet_core)
    packet = {**packet_core, "packetDigest": packet_digest}
    audit_dir = page_path.parent.parent / "review" / "validation-line-audit"
    audit_dir.mkdir(parents=True)
    (audit_dir / "packet.json").write_text(
        json.dumps(packet, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = [
        {
            "inputId": input_id,
            "scoreSystemId": score_system_id,
            "tabSystemId": tab_system_id,
            "expectedMachineRecordDigest": machine_digest,
            "status": "both_match",
            "tabConfirmed": True,
            "trainingEligible": False,
        },
        {
            "inputId": input_id,
            "scoreSystemId": "score-system-capture-failed",
            "tabSystemId": tab_system_id,
            "expectedMachineRecordDigest": machine_digest,
            "status": "capture_failed",
            "tabConfirmed": False,
            "trainingEligible": False,
        },
    ]
    submission_digest = canonical_sha(
        {
            "reviewType": "validation_line_audit",
            "batchId": batch_id,
            "partition": "validation",
            "packetDigest": packet_digest,
            "reviews": rows,
            "validationGroundTruthMayTrain": False,
        }
    )
    submission_id = f"validation-line-audit-submission-{submission_digest[:20]}"
    submissions = audit_dir / "submissions"
    submissions.mkdir()
    write_jsonl(submissions / f"{submission_id}.jsonl", rows)
    metadata = {
        "submissionId": submission_id,
        "submissionDigest": submission_digest,
        "batchId": batch_id,
        "partition": "validation",
        "packetDigest": packet_digest,
        "reviewCount": 2,
        "eligibleForTraining": False,
        "validationGroundTruthMayTrain": False,
        "sealedTestAccessed": False,
    }
    (submissions / f"{submission_id}.json").write_text(
        json.dumps(metadata, sort_keys=True) + "\n", encoding="utf-8"
    )
    model_before = model_path.read_bytes()

    report = AmazingTablatureTrainingStore(
        root, repo_root=tmp_path
    ).score_validation_line_audits(model_id)

    assert report["batchReceipts"][batch_id]["status"] == "verified_and_scored_in_memory"
    assert report["recognition"]["metrics"]["scoreReaderAccuracy"] == 0.5
    assert report["recognition"]["metrics"]["captureFailedLineCount"] == 1
    assert report["recognition"]["metrics"]["resolvedLineCount"] == 1
    assert report["arrangerRanking"]["metrics"]["topChoiceAccuracy"] == 1.0
    assert report["structuredInputParity"]["parityPassed"] is True
    assert report["structuredInputParity"]["totalAdapterEvents"] == 210
    assert report["gate"]["passed"] is False  # evidence-size floors still apply
    assert report["noTrainingContract"]["validationDecisionsAddedToTraining"] == 0
    assert report["sealedTestAccessed"] is False
    assert model_path.read_bytes() == model_before
    assert not (root / "batches" / batch_id / "accepted-decisions.jsonl").exists()

    legacy_packet_core = {
        key: value
        for key, value in packet_core.items()
        if key != "preflightVersion"
    }
    legacy_packet_digest = canonical_sha(legacy_packet_core)
    (audit_dir / "packet.json").write_text(
        json.dumps(
            {**legacy_packet_core, "packetDigest": legacy_packet_digest},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(TrainingWorkflowError, match="lineage"):
        AmazingTablatureTrainingStore(
            root, repo_root=tmp_path
        ).score_validation_line_audits(model_id)


def annotation(
    decision_id: str,
    input_id: str,
    *,
    partition: str,
    benchmark: str = "",
    style: str = "vocal_steel",
    source_copedent_id: str = "source-e9-abc-defg-v1",
    review_status: str = "reviewed",
) -> dict[str, object]:
    melody = 68
    role = "sustained_note" if partition == "train" else "cadence"
    return {
        "schemaVersion": "melody-decision-annotation-v2",
        "decisionId": decision_id,
        "inputId": input_id,
        "sourceCopedentId": source_copedent_id,
        "sourceCopedentRevision": 1,
        "styleFamily": style,
        "phraseRole": role,
        "datasetPartition": partition,
        "benchmarkGroup": benchmark,
        "reviewStatus": review_status,
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


def ingested_store(
    tmp_path: Path, *, evidence_type: str = "expert_score_tab"
) -> tuple[AmazingTablatureTrainingStore, str]:
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


def add_small_partitioned_batch(
    store: AmazingTablatureTrainingStore,
    tmp_path: Path,
    *,
    batch_id: str,
    source_copedent_id: str,
) -> tuple[dict[str, object], dict[str, object]]:
    sources = tmp_path / f"{batch_id}-sources"
    sources.mkdir()
    for number in range(1, 4):
        (sources / f"page-{number}.jpg").write_bytes(f"{batch_id}-page-{number}".encode())
    store.ingest(sources, source_copedent_id=source_copedent_id, batch_id=batch_id)
    status = store.prepare_partition(
        batch_id,
        document_breaks=[],
        forced_discovery=["page-1.jpg"],
        content_unit_breaks=["page-2.jpg", "page-3.jpg"],
        discovery_target=1,
        validation_target=1,
        test_target=1,
        guard_radius=0,
        seed=f"{batch_id}-private-seed".encode().ljust(32, b"0"),
    )
    store.record_split_review(
        batch_id,
        outcome="pass",
        partition_digest=str(status["partition"]["partitionDigest"]),
        reviewer_reference="independent-lane15-test-review",
        review_artifact_digest="a" * 64,
    )
    store.record_use_authorization(
        batch_id,
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining"],
        approval_reference="synthetic test source authorization",
    )
    batch_dir = tmp_path / f"private/batches/{batch_id}"
    discovery = json.loads((batch_dir / "discovery-work.jsonl").read_text().splitlines()[0])
    validation = json.loads((batch_dir / "validation-work.jsonl").read_text().splitlines()[0])
    return discovery, validation


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


def test_annotation_import_requires_the_exact_source_copedent_revision(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    record = annotation("wrong-copedent-revision", "input-0001", partition="train")
    record["sourceCopedentRevision"] = 2

    with pytest.raises(TrainingWorkflowError, match="source-copedent revision"):
        store.import_annotations(
            batch_id,
            write_jsonl(tmp_path / "wrong-copedent-revision.jsonl", [record]),
        )


def test_model_training_rights_default_off_and_unknown_status_cannot_enable_it(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    status = store.batch_status(batch_id)
    assert status["rightsAndAccess"]["rightsStatus"] == "unknown"
    assert status["rightsAndAccess"]["allowedUses"]["modelTraining"] is False

    with pytest.raises(TrainingWorkflowError, match="cannot remain unknown"):
        store.record_use_authorization(
            batch_id,
            rights_status="unknown",
            allowed_uses=["modelTraining"],
            approval_reference="invalid synthetic authorization",
        )

    authorized = store.record_use_authorization(
        batch_id,
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining"],
        approval_reference="synthetic source owner authorization",
    )
    assert authorized["allowedUses"]["modelTraining"] is True
    assert authorized["recordDigest"]


def test_reviewed_evidence_survives_non_revoking_rights_extension(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    original = store.record_use_authorization(
        batch_id,
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining"],
        approval_reference="synthetic training authorization",
    )
    store.record_use_authorization(
        batch_id,
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining", "runtimeProductUse"],
        approval_reference="synthetic runtime extension",
    )

    assert store._reviewed_evidence_rights_are_current(
        batch_id,
        str(original["recordDigest"]),
        required_use="modelTraining",
    ) is True

    store.record_use_authorization(
        batch_id,
        rights_status="user_provided_authorized",
        allowed_uses=[],
        approval_reference="synthetic training revocation",
    )
    assert store._reviewed_evidence_rights_are_current(
        batch_id,
        str(original["recordDigest"]),
        required_use="modelTraining",
    ) is False


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


def test_semantic_group_map_links_noncontiguous_pages_and_forces_cross_document_variants(
    tmp_path: Path,
) -> None:
    sources = tmp_path / "semantic-sources"
    sources.mkdir()
    for number in range(1, 10):
        (sources / f"page-{number}.jpg").write_bytes(f"private-semantic-page-{number}".encode())
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    batch_id = "atb-semantic-map"
    status = store.ingest(
        sources,
        source_copedent_id="source-e9-abc-defg-v1",
        batch_id=batch_id,
    )
    semantic_map = {
        "schemaVersion": "amazing-tablature-semantic-groups-v1",
        "batchImmutableDigest": status["immutableDigest"],
        "groups": [
            {"groupId": "same-document-work", "inputIds": ["input-0002", "input-0004"]},
            {"groupId": "cross-document-variant", "inputIds": ["input-0001", "input-0007"]},
        ],
    }
    semantic_path = tmp_path / "semantic-groups.json"
    semantic_path.write_text(json.dumps(semantic_map), encoding="utf-8")

    store.prepare_partition(
        batch_id,
        document_breaks=["page-6.jpg"],
        forced_discovery=[],
        page_level_units=True,
        semantic_groups=semantic_path,
        discovery_target=5,
        validation_target=2,
        test_target=2,
        guard_radius=0,
        seed=b"lane-15-semantic-private-seed-v1",
    )

    batch_dir = tmp_path / f"private/batches/{batch_id}"
    all_records = [
        *[json.loads(line) for line in (batch_dir / "discovery-work.jsonl").read_text().splitlines()],
        *[json.loads(line) for line in (batch_dir / "validation-work.jsonl").read_text().splitlines()],
        *json.loads((batch_dir / "sealed-test/test-manifest.json").read_text())["inputs"],
    ]
    by_id = {record["inputId"]: record for record in all_records}
    assert by_id["input-0002"]["contentUnitId"] == by_id["input-0004"]["contentUnitId"]
    assert by_id["input-0002"]["datasetPartition"] == by_id["input-0004"]["datasetPartition"]
    assert by_id["input-0001"]["contentUnitId"] == by_id["input-0007"]["contentUnitId"]
    assert by_id["input-0001"]["datasetPartition"] == "discovery"
    assert by_id["input-0007"]["datasetPartition"] == "discovery"
    partition = store.batch_status(batch_id)["partition"]
    assert partition["groupingReviewStatus"] == "semantic_map_applied_review_pending"
    assert partition["semanticGroupCount"] == 2
    assert partition["semanticGroupDigest"]


def test_independent_split_review_is_digest_bound_immutable_and_required_for_composition(
    tmp_path: Path,
) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    first, _ = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-reviewed-first",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    assert first["datasetPartition"] == "discovery"

    sources = tmp_path / "unreviewed-sources"
    sources.mkdir()
    for number in range(1, 4):
        (sources / f"page-{number}.jpg").write_bytes(f"unreviewed-{number}".encode())
    store.ingest(
        sources,
        source_copedent_id="source-e9-abc-defg-d48-e29-v1",
        batch_id="atb-unreviewed-second",
    )
    second_status = store.prepare_partition(
        "atb-unreviewed-second",
        document_breaks=[],
        forced_discovery=["page-1.jpg"],
        content_unit_breaks=["page-2.jpg", "page-3.jpg"],
        discovery_target=1,
        validation_target=1,
        test_target=1,
        guard_radius=0,
        seed=b"unreviewed-private-seed".ljust(32, b"0"),
    )
    with pytest.raises(TrainingWorkflowError, match="passing independent split review"):
        store.compose_authoritative_dataset(
            ["atb-reviewed-first", "atb-unreviewed-second"],
            approval_reference="test composition",
        )

    digest = str(second_status["partition"]["partitionDigest"])
    with pytest.raises(TrainingWorkflowError, match="does not match"):
        store.record_split_review(
            "atb-unreviewed-second",
            outcome="pass",
            partition_digest="0" * 64,
            reviewer_reference="independent-lane15-test-review",
        )
    reviewed = store.record_split_review(
        "atb-unreviewed-second",
        outcome="pass",
        partition_digest=digest,
        reviewer_reference="independent-lane15-test-review",
        review_artifact_digest="b" * 64,
    )
    assert reviewed["partition"]["groupingReviewStatus"] == "independent_review_passed"
    assert reviewed["partition"]["independentReview"]["partitionDigest"] == digest
    with pytest.raises(TrainingWorkflowError, match="immutable"):
        store.record_split_review(
            "atb-unreviewed-second",
            outcome="fail",
            partition_digest=digest,
            reviewer_reference="different-review",
        )

    dataset = store.compose_authoritative_dataset(
        ["atb-reviewed-first", "atb-unreviewed-second"],
        approval_reference="test composition after both reviews passed",
    )
    assert dataset["batchIds"] == ["atb-reviewed-first", "atb-unreviewed-second"]


def test_authoritative_dataset_trains_and_evaluates_every_sealed_batch(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    first_id = "atb-first"
    second_id = "atb-licks"
    first_discovery, first_validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id=first_id,
        source_copedent_id="source-e9-abc-defg-v1",
    )
    second_discovery, second_validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id=second_id,
        source_copedent_id="source-e9-abc-defg-d48-e29-v1",
    )
    dataset = store.compose_authoritative_dataset(
        [first_id, second_id],
        approval_reference="user approved combined two-batch training",
    )
    assert dataset["batchIds"] == [first_id, second_id]
    assert dataset["sealedTestsRemainIndependent"] is True

    for batch_id, copedent_id, discovery, validation in (
        (first_id, "source-e9-abc-defg-v1", first_discovery, first_validation),
        (second_id, "source-e9-abc-defg-d48-e29-v1", second_discovery, second_validation),
    ):
        records = [
            annotation(
                f"{batch_id}-discovery",
                str(discovery["inputId"]),
                partition="discovery",
                source_copedent_id=copedent_id,
            ),
            annotation(
                f"{batch_id}-validation",
                str(validation["inputId"]),
                partition="validation",
                benchmark="amazing_grace" if batch_id == first_id else "",
                source_copedent_id=copedent_id,
            ),
        ]
        records[1]["categoryTags"] = [
            "alignment:score_supported" if batch_id == first_id else "alignment:tab_only"
        ]
        store.import_annotations(batch_id, write_jsonl(tmp_path / f"{batch_id}.jsonl", records))
        assert store.validate(batch_id)["counts"]["accepted"] == 2

    sealed_coordinator_path = tmp_path / "pocketsteel" / "amazing_tablature_sealed_test.py"
    sealed_coordinator_path.parent.mkdir(parents=True, exist_ok=True)
    sealed_coordinator_path.write_text("# frozen sealed evaluator\n", encoding="utf-8")
    (tmp_path / "pocketsteel" / "melody_arranger.py").write_text(
        "# frozen deterministic candidate enumerator\n",
        encoding="utf-8",
    )
    model = store.train(epochs=2)
    assert model["sourceBatchIds"] == [first_id, second_id]
    assert model["sourceCopedentIds"] == [
        "source-e9-abc-defg-d48-e29-v1",
        "source-e9-abc-defg-v1",
    ]
    assert {item["batchId"] for item in model["sourceCopedentProfiles"]} == {first_id, second_id}
    assert all(item["revision"] == 1 and item["digest"] for item in model["sourceCopedentProfiles"])
    assert model["authoritativeDatasetId"] == dataset["datasetId"]
    evaluation = store.evaluate(str(model["modelId"]))
    assert set(evaluation["cohortMetrics"]) == {first_id, second_id}
    assert {item["batchId"] for item in evaluation["sourceCopedentProfiles"]} == {first_id, second_id}
    assert all(metrics["decisionCount"] == 1 for metrics in evaluation["cohortMetrics"].values())
    assert evaluation["gate"]["allCohortsPassed"] is True
    sealed_coordinator_path.write_text("# changed after validation\n", encoding="utf-8")
    code_changed_model = store.train(epochs=2)
    assert code_changed_model["modelId"] != model["modelId"]
    with pytest.raises(TrainingWorkflowError, match="changed after challenger training"):
        store.freeze_rules(str(model["modelId"]))
    sealed_coordinator_path.write_text("# frozen sealed evaluator\n", encoding="utf-8")
    freeze = store.freeze_rules(str(model["modelId"]))
    assert freeze["status"] == "frozen_tests_unopened"
    assert freeze["authoritativeDatasetId"] == dataset["datasetId"]
    assert len(freeze["sealedTestCohorts"]) == 2
    assert freeze["rulesEngineDigest"]
    assert set(freeze["rightsAuthorizationDigests"]) == {first_id, second_id}
    assert all(cohort["rightsAuthorizationDigest"] for cohort in freeze["sealedTestCohorts"])
    assert "pocketsteel/amazing_tablature_sealed_test.py" in freeze["codeFileDigests"]
    assert "pocketsteel/melody_arranger.py" in freeze["codeFileDigests"]

    reauthorized = store.record_use_authorization(
        first_id,
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining"],
        approval_reference="synthetic renewed authorization",
    )
    retrained = store.train(epochs=2)
    assert retrained["modelId"] != model["modelId"]
    assert retrained["rightsAuthorizationDigests"][first_id] == reauthorized["recordDigest"]


def test_combined_dataset_blocks_training_when_one_batch_is_unreviewed(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    first_discovery, _first_validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-first",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-second",
        source_copedent_id="source-e9-abc-defg-d48-e29-v1",
    )
    store.compose_authoritative_dataset(
        ["atb-first", "atb-second"],
        approval_reference="user approved combined two-batch training",
    )
    store.import_annotations(
        "atb-first",
        write_jsonl(
            tmp_path / "first-only.jsonl",
            [annotation("first-only", str(first_discovery["inputId"]), partition="discovery")],
        ),
    )
    store.validate("atb-first")

    with pytest.raises(TrainingWorkflowError, match="atb-second"):
        store.train(epochs=2)


def test_partition_annotation_ledgers_allow_validation_import_after_discovery(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-sequential-ledgers",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    store.import_annotations(
        "atb-sequential-ledgers",
        write_jsonl(
            tmp_path / "sequential-discovery.jsonl",
            [annotation("sequential-discovery", str(discovery["inputId"]), partition="discovery")],
        ),
    )
    store.import_annotations(
        "atb-sequential-ledgers",
        write_jsonl(
            tmp_path / "sequential-validation.jsonl",
            [annotation("sequential-validation", str(validation["inputId"]), partition="validation")],
        ),
    )

    batch_dir = tmp_path / "private/batches/atb-sequential-ledgers"
    assert (batch_dir / "annotations-discovery.jsonl").exists()
    assert (batch_dir / "annotations-validation.jsonl").exists()
    status = store.validate("atb-sequential-ledgers")
    assert status["counts"]["accepted"] == 2


def test_page_approved_decisions_materialize_into_private_partition_ledger(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-derived-decisions",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    extraction_root = tmp_path / "private/batches/atb-derived-decisions/extraction/discovery"
    approved_path = extraction_root / "review/approved-records/input-r2.json"
    approved_path.parent.mkdir(parents=True)
    approved_decision = annotation(
        "derived-reviewed-page",
        str(discovery["inputId"]),
        partition="discovery",
    )
    approved_decision["reviewState"] = "human_approved"
    approved_decision["scoreToTabSupport"] = {
        "mode": "score_supported",
        "previous": {"scoreEventIds": []},
        "current": {"scoreEventIds": ["score-event-1"]},
    }
    approved_decision["categoryTags"] = ["alignment:score_supported"]
    rights = json.loads(
        (tmp_path / "private/batches/atb-derived-decisions/rights-and-access.json").read_text(encoding="utf-8")
    )
    reviewed_record = {
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "rightsAndAccess": {"authorizationRecordDigest": rights["recordDigest"]},
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "scoreEvents": [
                    {
                        "scoreEventId": "score-event-1",
                        "pitchValue": 59,
                        "rest": False,
                    }
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "steelActions": [
                            {"soundingPitchValue": 59, "attack": True},
                            {"soundingPitchValue": 62, "attack": True},
                        ],
                    }
                ],
            }
        ],
        "eventAlignments": [
            {
                "eventAlignmentId": "alignment-1",
                "scoreEventIds": ["score-event-1"],
                "tabEventIds": ["tab-event-1"],
            }
        ],
        "derivedDecisions": [approved_decision],
    }
    approved_path.write_text(json.dumps(reviewed_record), encoding="utf-8")
    reviewed_digest = hashlib.sha256(
        json.dumps(reviewed_record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_jsonl(
        extraction_root / "review/approved-record-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "status": "human_approved",
                "reviewDecisionId": "human-page-review-derived",
                "reviewedRecordPath": "review/approved-records/input-r2.json",
                "reviewedRecordDigest": reviewed_digest,
            }
        ],
    )
    (extraction_root / "review/human-review-summary.json").write_text(
        json.dumps({"humanApprovalComplete": True, "remainingPageCount": 0}),
        encoding="utf-8",
    )

    with pytest.raises(TrainingWorkflowError, match="music-score audit"):
        store.derive_reviewed_decisions("atb-derived-decisions", partition="discovery")
    (extraction_root / "review/score-audit").mkdir(parents=True)
    write_jsonl(
        extraction_root / "review/score-audit/approved-score-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "status": "human_approved",
                "scoreAuditDecisionId": "score-audit-derived",
                "reviewedRecordDigest": reviewed_digest,
                "approvedScoreSystemIds": ["score-system-1"],
                "notApplicableScoreSystemIds": [],
                "pitchToTabTrainingEligible": True,
                "scoreRhythmTrainingEligible": False,
            }
        ],
    )
    result = store.derive_reviewed_decisions("atb-derived-decisions", partition="discovery")

    assert result["decisionCount"] == 1
    assert result["blockingExceptionCount"] == 0
    batch_dir = tmp_path / "private/batches/atb-derived-decisions"
    assert (batch_dir / "derived-annotations-discovery.jsonl").exists()
    assert (batch_dir / "annotations-discovery.jsonl").exists()
    derived = json.loads(
        (batch_dir / "derived-annotations-discovery.jsonl").read_text(encoding="utf-8")
    )
    assert derived["scoreEvidenceScope"] == {
        "pitchToTabTrainingEligible": True,
        "scoreRhythmTrainingEligible": False,
    }
    assert derived["scoreToTabSupport"] == {
        "mode": "tab_only",
        "reason": "score_tab_pitch_correspondence_not_exact",
    }
    assert "alignment:tab_only" in derived["categoryTags"]
    assert "alignment:score_supported" not in derived["categoryTags"]

    extended = store.record_use_authorization(
        "atb-derived-decisions",
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining", "runtimeProductUse"],
        approval_reference="synthetic authorization revision",
    )
    refreshed = store.derive_reviewed_decisions(
        "atb-derived-decisions", partition="discovery"
    )
    assert refreshed["decisionCount"] == 1
    assert extended["allowedUses"]["runtimeProductUse"] is True


def test_partial_discovery_challenger_uses_only_reviewed_tab_only_pages(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, _validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-partial-discovery",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    store.compose_authoritative_dataset(
        ["atb-partial-discovery"],
        approval_reference="synthetic partial discovery challenger",
    )
    batch_dir = tmp_path / "private/batches/atb-partial-discovery"
    extraction_root = batch_dir / "extraction/discovery"
    approved_path = extraction_root / "review/approved-records/input-r2.json"
    approved_path.parent.mkdir(parents=True)
    decision = annotation(
        "partial-reviewed-tab-only",
        str(discovery["inputId"]),
        partition="discovery",
    )
    decision["reviewState"] = "human_approved"
    decision["categoryTags"] = ["alignment:tab_only", "page:lick_fill"]
    decision["scoreToTabSupport"] = {"mode": "tab_only"}
    rights = json.loads((batch_dir / "rights-and-access.json").read_text(encoding="utf-8"))
    reviewed_record = {
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "rightsAndAccess": {"authorizationRecordDigest": rights["recordDigest"]},
        "pageClassification": {"primary": "lick_or_fill"},
        "scoreSystems": [],
        "tabSystems": [{"tabSystemId": "tab-system-1", "tabEvents": []}],
        "derivedDecisions": [decision],
    }
    approved_path.write_text(json.dumps(reviewed_record), encoding="utf-8")
    reviewed_digest = hashlib.sha256(
        json.dumps(reviewed_record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_jsonl(
        extraction_root / "review/approved-record-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "status": "human_approved",
                "reviewDecisionId": "partial-page-review",
                "reviewedRecordPath": "review/approved-records/input-r2.json",
                "reviewedRecordDigest": reviewed_digest,
            }
        ],
    )
    (extraction_root / "review/human-review-summary.json").write_text(
        json.dumps(
            {
                "humanApprovalComplete": False,
                "reviewedPageCount": 1,
                "remainingPageCount": 1,
            }
        ),
        encoding="utf-8",
    )

    model = store.train_discovery_challenger(epochs=2)

    assert model["status"] == "challenger"
    assert model["evaluationScope"] == "discovery_shadow_only"
    assert model["promotionEligible"] is False
    assert model["exampleCount"] == 1
    seed_dir = tmp_path / f"private/discovery-seeds/{model['discoverySeedId']}"
    seed_manifest_path = seed_dir / "manifest.json"
    seed_records_path = seed_dir / "accepted-decisions.jsonl"
    seed = json.loads(seed_manifest_path.read_text(encoding="utf-8"))
    assert seed["decisionCount"] == 1
    assert seed["fullDiscoveryReviewComplete"] is False
    assert seed["validationAccessed"] is False
    assert seed["sealedTestAccessed"] is False
    assert seed["cohorts"][0]["challengerPreferenceLedger"] == {
        "recordCount": 0,
        "canonicalDigest": hashlib.sha256(b"[]").hexdigest(),
        "fileSha256": None,
    }
    assert model["trainingConfig"]["discoverySeedArtifacts"] == {
        "manifestSha256": hashlib.sha256(seed_manifest_path.read_bytes()).hexdigest(),
        "acceptedDecisionsSha256": hashlib.sha256(seed_records_path.read_bytes()).hexdigest(),
    }
    registry = json.loads(
        (tmp_path / "private/training-registry.json").read_text(encoding="utf-8")
    )
    model_path = tmp_path / "private" / registry["models"][model["modelId"]]["artifact"]
    assert registry["models"][model["modelId"]]["artifactSha256"] == hashlib.sha256(
        model_path.read_bytes()
    ).hexdigest()
    shadow = store.shadow_test_discovery(model["modelId"])
    assert shadow["shadowScorerLineage"]["codeDigest"] == hashlib.sha256(
        json.dumps(
            shadow["shadowScorerLineage"]["codeFileDigests"],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    snapshot_meta = shadow["effectiveDiscoverySnapshot"]
    snapshot_path = tmp_path / "private" / snapshot_meta["relativePath"]
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot_core = {
        key: value for key, value in snapshot.items() if key != "snapshotDigest"
    }
    assert snapshot["snapshotDigest"] == hashlib.sha256(
        json.dumps(snapshot_core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert snapshot_meta["fileSha256"] == hashlib.sha256(
        snapshot_path.read_bytes()
    ).hexdigest()
    for lineage in shadow["evidenceArtifacts"].values():
        artifact_path = tmp_path / "private" / lineage["relativePath"]
        records = [
            json.loads(line)
            for line in artifact_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert lineage["recordCount"] == len(records)
        assert lineage["fileSha256"] == hashlib.sha256(
            artifact_path.read_bytes()
        ).hexdigest()
        assert lineage["canonicalDigest"] == hashlib.sha256(
            json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    assert shadow["sourceAgreementCount"] == 0
    assert shadow["expertAcceptableCount"] == 0
    assert shadow["rereviewSuppression"] == {
        "suppressedLineCount": 0,
        "suppressedLineWithCurrentDisagreementCount": 0,
        "suppressedCurrentDisagreementCount": 0,
        "reasonCounts": {},
    }
    inherited = store.train_discovery_challenger(
        epochs=2,
        base_model_id=model["modelId"],
        experimental_styles=[next(iter(model["weightsByStyle"]))],
        base_weight_ratio=0.5,
    )
    assert inherited["trainingConfig"]["baseModelArtifactSha256"] == hashlib.sha256(
        model_path.read_bytes()
    ).hexdigest()
    readiness = store.canonical_readiness(base_model_id=model["modelId"])
    assert readiness["remainingDiscoveryPageCount"] == 1
    assert readiness["readyForCompleteDiscoveryTraining"] is False
    assert readiness["validationAccessed"] is False
    assert readiness["sealedTestAccessed"] is False
    with pytest.raises(TrainingWorkflowError, match="Complete-discovery training is not ready"):
        store.train_complete_discovery_challenger(
            base_model_id=model["modelId"],
            epochs=2,
        )
    with pytest.raises(TrainingWorkflowError, match="cannot enter canonical validation"):
        store.evaluate(model["modelId"])
    preference_ledger_path = (
        extraction_root
        / "review/challenger-comparison/application/preference-ledger.jsonl"
    )
    duplicate_preference = {
        "preferenceId": "preference-duplicate",
        "originalDecisionId": "decision-duplicate",
        "reviewState": "human_approved",
    }
    preference_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        preference_ledger_path,
        [duplicate_preference, duplicate_preference],
    )
    with pytest.raises(TrainingWorkflowError, match="missing or duplicated"):
        store.shadow_test_discovery(model["modelId"])


def test_complete_discovery_challenger_reuses_hardened_lineage_and_all_styles(
    tmp_path: Path,
) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-complete-discovery",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    store.compose_authoritative_dataset(
        ["atb-complete-discovery"],
        approval_reference="synthetic complete discovery",
    )
    store.record_use_authorization(
        "atb-complete-discovery",
        rights_status="user_provided_authorized",
        allowed_uses=["modelTraining", "privateEvaluation"],
        approval_reference="synthetic complete discovery and validation authorization",
    )
    batch_dir = tmp_path / "private/batches/atb-complete-discovery"
    extraction_root = batch_dir / "extraction/discovery"
    approved_path = extraction_root / "review/approved-records/input-r2.json"
    approved_path.parent.mkdir(parents=True)
    decisions = []
    for index, style in enumerate(
        ("chord_melody", "harmonized", "lever_driven", "single_note_run"),
        start=1,
    ):
        decision = annotation(
            f"complete-{style}",
            str(discovery["inputId"]),
            partition="discovery",
            style=style,
        )
        decision["reviewState"] = "human_approved"
        decision["scoreToTabSupport"] = {"mode": "tab_only"}
        decision["categoryTags"] = ["alignment:tab_only"]
        decision["chosen"]["barTravel"] = index - 1
        decision["alternatives"][0]["barTravel"] = index + 4
        decisions.append(decision)
    rights = json.loads((batch_dir / "rights-and-access.json").read_text(encoding="utf-8"))
    reviewed_record = {
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "rightsAndAccess": {"authorizationRecordDigest": rights["recordDigest"]},
        "pageClassification": {"primary": "lick_or_fill"},
        "scoreSystems": [],
        "tabSystems": [{"tabSystemId": "tab-system-1", "tabEvents": []}],
        "derivedDecisions": decisions,
    }
    approved_path.write_text(json.dumps(reviewed_record), encoding="utf-8")
    reviewed_digest = hashlib.sha256(
        json.dumps(reviewed_record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_jsonl(
        extraction_root / "review/approved-record-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "status": "human_approved",
                "reviewDecisionId": "complete-page-review",
                "reviewedRecordPath": "review/approved-records/input-r2.json",
                "reviewedRecordDigest": reviewed_digest,
                "approvalScope": "tab_only_score_audit_required",
            }
        ],
    )
    (extraction_root / "review/human-review-summary.json").write_text(
        json.dumps(
            {
                "humanApprovalComplete": False,
                "totalPageCount": 1,
                "reviewedPageCount": 1,
                "remainingPageCount": 0,
                "tabOnlyApprovedPageCount": 1,
            }
        ),
        encoding="utf-8",
    )
    preference_ledger = []
    for index in range(16):
        source = decisions[index % len(decisions)]
        training_eligible = index < 6
        preference_ledger.append(
            {
                "preferenceId": f"preference-{index:02d}",
                "originalDecisionId": source["decisionId"],
                "inputId": discovery["inputId"],
                "reviewState": "human_approved",
                "status": "source_preferred" if training_eligible else "both_valid",
                "trainingEligible": training_eligible,
                "styleFamily": source["styleFamily"],
                "phraseRole": source["phraseRole"],
                "sourceCandidate": source["chosen"],
                "challengerCandidate": {
                    **source["alternatives"][0],
                    "barTravel": 20 + index,
                },
                "challengerCandidateDigest": hashlib.sha256(
                    f"candidate-{index}".encode()
                ).hexdigest(),
                "mechanicalValidation": {"ok": True},
                "evidenceWeight": 1.0,
            }
        )
    preference_path = (
        extraction_root
        / "review/challenger-comparison/application/preference-ledger.jsonl"
    )
    preference_path.parent.mkdir(parents=True)
    write_jsonl(preference_path, preference_ledger)

    base = store.train_discovery_challenger(epochs=2)
    readiness = store.canonical_readiness(base_model_id=base["modelId"])
    assert readiness["readyForCompleteDiscoveryTraining"] is True
    assert readiness["cohorts"][0]["discoveryDispositionComplete"] is True
    assert readiness["cohorts"][0]["scoreAuditComplete"] is False
    assert readiness["cohorts"][0]["tabOnlyApprovedPageCount"] == 1
    assert readiness["preferenceAccounting"]["actual"] == {
        "reviewedCount": 16,
        "trainingCount": 6,
        "coValidCount": 10,
    }

    canonical = store.train_complete_discovery_challenger(
        base_model_id=base["modelId"],
        epochs=2,
        base_weight_ratio=0.20,
    )
    assert canonical["parentModelId"] == base["modelId"]
    assert canonical["fullDiscoveryReviewComplete"] is True
    assert canonical["fullDiscoveryScoreAuditComplete"] is False
    assert canonical["evaluationScope"] == "canonical_validation_candidate"
    assert canonical["promotionEligible"] is False
    assert sorted(canonical["weightsByStyle"]) == [
        "chord_melody",
        "harmonized",
        "lever_driven",
        "single_note_run",
    ]
    assert canonical["preferenceAccounting"]["reviewedCount"] == 16
    registry = json.loads(
        (tmp_path / "private/training-registry.json").read_text(encoding="utf-8")
    )
    meta = registry["models"][canonical["modelId"]]
    assert meta["datasetEligibility"] == "complete_discovery"
    assert meta["canonicalEvaluationEligible"] is True
    assert meta["discoveryShadowOnly"] is False

    validation_root = batch_dir / "extraction/validation"
    validation_reviewed_path = (
        validation_root / "review/approved-records/input-r2.json"
    )
    validation_reviewed_path.parent.mkdir(parents=True)
    validation_reviewed = {
        "objectId": "validation-page",
        "rightsAndAccess": {"authorizationRecordDigest": rights["recordDigest"]},
    }
    # Re-read the authorization because the complete-discovery authorization
    # above superseded the initial training-only record.
    current_rights = json.loads(
        (batch_dir / "rights-and-access.json").read_text(encoding="utf-8")
    )
    validation_reviewed["rightsAndAccess"]["authorizationRecordDigest"] = current_rights[
        "recordDigest"
    ]
    validation_reviewed_path.write_text(json.dumps(validation_reviewed), encoding="utf-8")
    validation_digest = hashlib.sha256(
        json.dumps(validation_reviewed, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_jsonl(
        validation_root / "review/approved-record-index.jsonl",
        [
            {
                "inputId": validation["inputId"],
                "status": "human_approved",
                "reviewDecisionId": "validation-review",
                "reviewedRecordPath": "review/approved-records/input-r2.json",
                "reviewedRecordDigest": validation_digest,
            }
        ],
    )
    (validation_root / "review/human-review-summary.json").write_text(
        json.dumps({"humanApprovalComplete": True, "remainingPageCount": 0}),
        encoding="utf-8",
    )
    (validation_root / "review/review-metrics.json").write_text(
        json.dumps({"allAcceptanceCriteriaPassed": True}),
        encoding="utf-8",
    )
    validation_decision = annotation(
        "canonical-validation-decision",
        str(validation["inputId"]),
        partition="validation",
        style="chord_melody",
    )
    validation_decision["categoryTags"] = ["alignment:score_supported"]
    store.import_annotations(
        "atb-complete-discovery",
        write_jsonl(tmp_path / "canonical-validation.jsonl", [validation_decision]),
    )
    assert store.validate("atb-complete-discovery")["counts"]["accepted"] == 1
    evaluation = store.evaluate(canonical["modelId"])
    assert evaluation["gate"]["passed"] is False
    assert evaluation["thresholdContract"] == {
        "metricVersion": "structured-input-tab-choice-v2",
        "canonicalEvaluation": True,
        "inputScope": "normalized_score_events",
        "scoreImageRecognitionIncluded": False,
        "audioRecognitionIncluded": False,
        "overallPreferenceAccuracyFloor": 0.95,
        "overallPreferenceAccuracyComparison": "strictly_greater_than",
        "overallTopThreeCoverageFloor": 0.99,
        "cohortPreferenceAccuracyFloor": 0.9,
        "evidenceModePreferenceAccuracyFloor": 0.9,
        "minimumDecisionCountPerCohort": 10,
        "minimumDecisionCountPerEvidenceMode": 20,
        "mechanicalAccuracyRequired": 1.0,
        "requiredEvidenceModes": [
            "alignment:score_supported",
            "alignment:tab_only",
        ],
        "durationDiagnosticOnly": True,
        "thresholdAdjustmentAfterValidation": False,
    }
    assert evaluation["cohortMetrics"]["atb-complete-discovery"][
        "evidenceSufficient"
    ] is False
    assert evaluation["modelArtifactSha256"] == meta["artifactSha256"]
    assert evaluation["validationDecisionDigest"]
    model_path = tmp_path / "private" / meta["artifact"]
    model_path.write_bytes(model_path.read_bytes() + b" ")
    with pytest.raises(TrainingWorkflowError, match="artifact digest changed"):
        store.evaluate(canonical["modelId"])


def test_partial_discovery_seed_rejects_unaudited_score_page(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, _validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-partial-score",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    store.compose_authoritative_dataset(
        ["atb-partial-score"],
        approval_reference="synthetic partial score challenger",
    )
    batch_dir = tmp_path / "private/batches/atb-partial-score"
    extraction_root = batch_dir / "extraction/discovery"
    approved_path = extraction_root / "review/approved-records/input-r2.json"
    approved_path.parent.mkdir(parents=True)
    decision = annotation(
        "unaudited-score-decision",
        str(discovery["inputId"]),
        partition="discovery",
    )
    decision["reviewState"] = "human_approved"
    rights = json.loads((batch_dir / "rights-and-access.json").read_text(encoding="utf-8"))
    reviewed_record = {
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "rightsAndAccess": {"authorizationRecordDigest": rights["recordDigest"]},
        "scoreSystems": [{"scoreSystemId": "score-system-1", "scoreEvents": []}],
        "tabSystems": [{"tabSystemId": "tab-system-1", "tabEvents": []}],
        "derivedDecisions": [decision],
    }
    approved_path.write_text(json.dumps(reviewed_record), encoding="utf-8")
    reviewed_digest = hashlib.sha256(
        json.dumps(reviewed_record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_jsonl(
        extraction_root / "review/approved-record-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "status": "human_approved",
                "reviewDecisionId": "page-review-only",
                "reviewedRecordPath": "review/approved-records/input-r2.json",
                "reviewedRecordDigest": reviewed_digest,
            }
        ],
    )

    with pytest.raises(TrainingWorkflowError, match="no reviewed discovery decisions"):
        store.freeze_discovery_seed()


def test_combined_line_approval_derives_only_pitch_scoped_transformations(
    tmp_path: Path,
) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, _validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-combined-lines",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    batch_dir = tmp_path / "private/batches/atb-combined-lines"
    extraction_root = batch_dir / "extraction/discovery"
    rights = json.loads((batch_dir / "rights-and-access.json").read_text(encoding="utf-8"))
    decision_id = "combined-line-review-1"
    score_events = [
        {
            "scoreEventId": f"score-{index}",
            "measure": 1,
            "beat": float(index),
            "pitch": pitch,
            "pitchValue": value,
            "rest": False,
            "reviewState": "human_approved",
        }
        for index, (pitch, value) in enumerate(
            (("E4", 64), ("F#4", 66), ("G4", 67)), start=1
        )
    ]
    tab_events = [
        {
            "tabEventId": "tab-1",
            "eventIndex": 1,
            "steelActions": [
                {
                    "string": 4,
                    "fret": 0,
                    "controls": [],
                    "soundingPitchValue": 64,
                    "attack": True,
                    "confidence": 1.0,
                    "mechanicalValidation": {"valid": True},
                }
            ],
        },
        {
            "tabEventId": "tab-2",
            "eventIndex": 2,
            "steelActions": [
                {
                    "string": 4,
                    "fret": 2,
                    "controls": [],
                    "soundingPitchValue": 66,
                    "attack": True,
                    "confidence": 1.0,
                    "mechanicalValidation": {"valid": True},
                },
                {
                    "string": 5,
                    "fret": 0,
                    "controls": [],
                    "soundingPitchValue": 59,
                    "attack": True,
                    "confidence": 1.0,
                    "mechanicalValidation": {"valid": True},
                },
            ],
        },
        {
            "tabEventId": "tab-3",
            "eventIndex": 3,
            "steelActions": [
                {
                    "string": 4,
                    "fret": 3,
                    "controls": [],
                    "soundingPitchValue": 67,
                    "attack": True,
                    "confidence": 1.0,
                    "mechanicalValidation": {"valid": True},
                }
            ],
        },
    ]
    alignments = []
    for index in range(1, 4):
        subset = index == 2
        alignments.append(
            {
                "eventAlignmentId": f"alignment-{index}",
                "scoreEventIds": [f"score-{index}"],
                "tabEventIds": [f"tab-{index}"],
                "alignmentType": (
                    "melody_top_note_to_grip" if subset else "score_attack_to_tab_state"
                ),
                "notationAdjustedPitchAgreement": not subset,
                "scoreNotationTranspositionSemitones": 0,
                "reviewState": "human_approved",
                "pitchToTabTrainingEligible": True,
                "scoreRhythmTrainingEligible": False,
                "combinedScoreTabDecisionId": decision_id,
            }
        )
    record = {
        "batchId": "atb-combined-lines",
        "inputId": discovery["inputId"],
        "datasetPartition": "discovery",
        "sourceDocumentId": "synthetic-document",
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "rightsAndAccess": {"authorizationRecordDigest": rights["recordDigest"]},
        "pageClassification": {"primary": "single_note_melody"},
        "sourceStructure": {},
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "combinedScoreTabDecisionId": decision_id,
                "scoreEvents": score_events,
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": tab_events,
            }
        ],
        "eventAlignments": alignments,
        "movementSequences": [],
        "teachingConcepts": [],
        "unresolved": [],
    }
    record_path = (
        extraction_root
        / "review/combined-score-tab-audit/application/applied-records/input-1/reviewed.json"
    )
    record_path.parent.mkdir(parents=True)
    record_path.write_text(json.dumps(record), encoding="utf-8")
    record_digest = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_jsonl(
        extraction_root
        / "review/combined-score-tab-audit/application/approved-line-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "scoreSystemId": "score-system-1",
                "tabSystemId": "tab-system-1",
                "decisionId": decision_id,
                "status": "human_approved_pitch_only",
                "scorePitchTrainingEligible": True,
                "pitchToTabTrainingEligible": True,
                "scoreRhythmTrainingEligible": False,
                "trainingEligible": True,
                "reviewedRecordPath": str(record_path.relative_to(extraction_root)),
                "reviewedRecordDigest": record_digest,
            }
        ],
    )

    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    decisions, line_count = store._combined_line_decisions(
        "atb-combined-lines", "discovery", profile
    )

    assert line_count == 1
    assert len(decisions) == 2
    assert all(item["sourceCombinedScoreTabDecisionId"] == decision_id for item in decisions)
    assert all(item["reviewStatus"] == "reviewed" for item in decisions)
    assert all(
        item["scoreEvidenceScope"]
        == {
            "pitchToTabTrainingEligible": True,
            "scoreRhythmTrainingEligible": False,
        }
        for item in decisions
    )
    assert any(
        item["scoreToTabSupport"]["current"]["eventAlignmentId"] == "alignment-2"
        for item in decisions
    )

    store.import_annotations(
        "atb-combined-lines",
        write_jsonl(tmp_path / "combined-line-decisions.jsonl", decisions),
    )
    validation = store.validate("atb-combined-lines")
    assert validation["counts"]["accepted"] == 2
    accepted = [
        json.loads(line)
        for line in (batch_dir / "accepted-decisions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert all(
        item["sourceExtractionReviewDecisionId"] == decision_id for item in accepted
    )
    assert all(item["sourceExtractionRecordDigest"] == record_digest for item in accepted)

    line_index_path = (
        extraction_root
        / "review/combined-score-tab-audit/application/approved-line-index.jsonl"
    )
    original_line = json.loads(line_index_path.read_text(encoding="utf-8"))
    ineligible = {
        **original_line,
        "decisionId": "combined-line-review-superseding-feedback",
        "status": "unresolved_requires_structured_correction",
        "scorePitchTrainingEligible": False,
        "pitchToTabTrainingEligible": False,
        "trainingEligible": False,
    }
    write_jsonl(line_index_path, [original_line, ineligible])
    assert store._combined_line_decisions(
        "atb-combined-lines", "discovery", profile
    ) == ([], 0)

    ineligible = dict(original_line)
    ineligible["pitchToTabTrainingEligible"] = True
    ineligible["reviewedRecordDigest"] = "0" * 64
    line_index_path.write_text(json.dumps(ineligible) + "\n", encoding="utf-8")
    with pytest.raises(TrainingWorkflowError, match="digest changed"):
        store._combined_line_decisions("atb-combined-lines", "discovery", profile)


def test_partitioned_annotations_require_approved_extraction_revision(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)
    discovery, _validation = add_small_partitioned_batch(
        store,
        tmp_path,
        batch_id="atb-reviewed-extraction",
        source_copedent_id="source-e9-abc-defg-v1",
    )
    store.import_annotations(
        "atb-reviewed-extraction",
        write_jsonl(
            tmp_path / "discovery-annotation.jsonl",
            [annotation("reviewed-page", str(discovery["inputId"]), partition="discovery")],
        ),
    )
    extraction_root = tmp_path / "private/batches/atb-reviewed-extraction/extraction/discovery"
    extraction_root.mkdir(parents=True)

    pending = store.validate("atb-reviewed-extraction")
    assert pending["counts"]["accepted"] == 0
    assert pending["counts"]["blockingExceptions"] == 1

    reviewed_record = {"objectId": "page-1", "revision": 2, "humanApprovalComplete": True}
    reviewed_digest = hashlib.sha256(
        json.dumps(reviewed_record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    approved_path = extraction_root / "review/approved-records/input-r2.json"
    approved_path.parent.mkdir(parents=True)
    approved_path.write_text(json.dumps(reviewed_record), encoding="utf-8")
    write_jsonl(
        extraction_root / "review/approved-record-index.jsonl",
        [
            {
                "inputId": discovery["inputId"],
                "status": "human_approved",
                "reviewDecisionId": "human-page-review-1",
                "reviewedRecordPath": "review/approved-records/input-r2.json",
                "reviewedRecordDigest": reviewed_digest,
            }
        ],
    )
    (extraction_root / "review/human-review-summary.json").write_text(
        json.dumps({"humanApprovalComplete": True, "remainingPageCount": 0}),
        encoding="utf-8",
    )

    approved = store.validate("atb-reviewed-extraction")
    assert approved["counts"]["accepted"] == 1
    accepted = json.loads(
        (tmp_path / "private/batches/atb-reviewed-extraction/accepted-decisions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    assert accepted["sourceExtractionReviewDecisionId"] == "human-page-review-1"
    assert accepted["sourceExtractionRecordDigest"] == reviewed_digest


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
        for line in (tmp_path / "private/batches/atb-test-batch/exceptions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
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


def test_machine_validated_core_fields_require_human_acceptance(tmp_path: Path) -> None:
    store, batch_id = ingested_store(tmp_path)
    record = annotation(
        "machine-only",
        "input-0001",
        partition="train",
        review_status="machine_validated",
    )
    store.import_annotations(batch_id, write_jsonl(tmp_path / "machine-only.jsonl", [record]))

    pending = store.validate(batch_id)
    assert pending["counts"]["accepted"] == 0
    assert pending["counts"]["blockingExceptions"] == 1

    reviewed = store.apply_review(
        batch_id,
        write_jsonl(tmp_path / "human-review.jsonl", [{"decisionId": "machine-only", "action": "accept"}]),
    )
    assert reviewed["counts"]["accepted"] == 1


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


def test_contextual_path_features_separate_string_jump_from_controlled_move() -> None:
    continuous = candidate(
        melody=68,
        texture=1,
        travel=3,
        controls=0,
        pocket=1,
        leading=1,
        sustained=0,
        repicked=1,
        role="passing_tone",
    )
    disconnected = {**continuous, "repickedVoices": 0}
    controlled = {**disconnected, "controlChanges": 1}

    assert feature_vector(continuous)["disconnected_bar_travel"] == 0
    assert feature_vector(disconnected)["disconnected_bar_travel"] == 3
    assert feature_vector(disconnected)["controlled_move"] == 0
    assert feature_vector(controlled)["controlled_move"] == 1



def test_averaged_pairwise_ranker_dampens_last_update_order_effect() -> None:
    records = [
        {
            "styleFamily": "single_note_run",
            "chosen": {"barTravel": 1},
            "alternatives": [{"barTravel": 0}],
            "evidenceWeight": 1,
        },
        {
            "styleFamily": "single_note_run",
            "chosen": {"barTravel": 0},
            "alternatives": [{"barTravel": 1}],
            "evidenceWeight": 1,
        },
    ]

    final = train_pairwise_ranker(records, epochs=1, learning_rate=1)
    averaged = train_pairwise_ranker(
        records, epochs=1, learning_rate=1, average_weights=True
    )

    assert final.weights_by_style["single_note_run"]["bar_travel"] == 0
    assert averaged.weights_by_style["single_note_run"]["bar_travel"] == -0.5


def test_discovery_weight_shrinkage_requires_a_valid_baseline_ratio(tmp_path: Path) -> None:
    store = AmazingTablatureTrainingStore(tmp_path / "private", repo_root=tmp_path)

    with pytest.raises(TrainingWorkflowError, match="between zero and one"):
        store.train_discovery_challenger(base_weight_ratio=1.01)
    with pytest.raises(TrainingWorkflowError, match="exact discovery baseline"):
        store.train_discovery_challenger(base_weight_ratio=0.8)


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

    deactivated = store.deactivate_channel(
        channel="beta",
        approval_reference="creator retired obsolete beta channel",
    )
    assert deactivated == {
        "channel": "beta",
        "modelId": None,
        "previousModelId": first["modelId"],
    }
    assert store.status()["channels"]["beta"] is None
    assert store.status()["models"][first["modelId"]]["status"] == "approved_stable"

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
    assert result["decisionModelStatus"] == MODEL_STATUS == "deterministic_fallback"
    assert result["routes"][0]["styleLabel"] == "Singing Steel"
    assert result["routes"][0]["decisionModelStatus"] == "deterministic_fallback"
    assert result["routes"][0]["targetCopedentId"] == "emmons-e9-basic"
