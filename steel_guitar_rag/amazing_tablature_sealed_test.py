"""One-shot sealed evaluation coordinator for independently reviewed Lane 20 cohorts."""

from __future__ import annotations

import concurrent.futures
import fcntl
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from steel_guitar_rag.amazing_tablature_extraction import (
    EXTRACTION_SCHEMA_VERSION,
    EXTRACTOR_VERSION,
    KNOWLEDGE_SCHEMA_VERSION,
    AmazingTablatureExtractor,
    _hard_review_blockers,
    _normalized_rights_and_access,
    extraction_acceptance_metrics,
)
from steel_guitar_rag.e9_copedents import get_e9_copedent_profile
from steel_guitar_rag.melody_ranker import score_candidate


SEALED_TEST_SCHEMA_VERSION = "amazing-tablature-sealed-test-v1"


class SealedTestWorkflowError(ValueError):
    """Raised when an action would contaminate or repeat a sealed evaluation."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SealedTestWorkflowError(f"{path} must contain a JSON object.")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise SealedTestWorkflowError(f"{path}:{line_number} must contain a JSON object.")
        records.append(value)
    return records


def _atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write(path, json.dumps(dict(value), indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    _atomic_write(
        path,
        "\n".join(json.dumps(dict(record), ensure_ascii=False, sort_keys=True) for record in records) + "\n",
    )


def _page_categories(record: Mapping[str, Any]) -> set[str]:
    source_structure = record.get("sourceStructure") or {}
    tab_event_count = sum(len(system.get("tabEvents") or []) for system in record.get("tabSystems") or [])
    notation_density = "low" if tab_event_count <= 10 else "middle" if tab_event_count <= 25 else "high"
    categories = {
        f"source_sequence:{record.get('sourceDocumentId', 'unknown')}",
        f"page:{record.get('pageClassification', {}).get('primary', 'unknown')}",
        f"notation_density:{notation_density}",
        f"orientation:{source_structure.get('orientation', 'unknown')}",
        f"image_luminance:{source_structure.get('luminanceBin', 'unknown')}",
        f"image_density:{source_structure.get('densityBin', 'unknown')}",
    }
    categories.update(
        f"movement:{classification.get('concept')}"
        for movement in record.get("movementSequences") or []
        for classification in movement.get("classifications") or []
        if classification.get("concept")
    )
    categories.update(
        f"unusual_symbol:{item.get('kind')}" for item in record.get("unresolved") or [] if item.get("kind")
    )
    return categories


def _decision_evidence_mode(decision: Mapping[str, Any]) -> str:
    mode = str(decision.get("scoreToTabSupport", {}).get("mode") or "")
    if mode in {"score_supported", "tab_only"}:
        return mode
    tags = {str(value) for value in decision.get("categoryTags") or []}
    if "alignment:score_supported" in tags:
        return "score_supported"
    if "alignment:tab_only" in tags:
        return "tab_only"
    return "unknown"


def _preference_metrics(
    model: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
    *,
    floor: float,
    top_three_floor: float = 0.0,
    minimum_count: int = 1,
    floor_is_exclusive: bool = False,
) -> dict[str, Any]:
    weights_by_style = model.get("weightsByStyle")
    correct = 0
    top_three = 0
    if isinstance(weights_by_style, Mapping):
        for decision in decisions:
            style = str(decision.get("styleFamily") or "auto")
            weights = weights_by_style.get(style) or weights_by_style.get("auto")
            chosen = decision.get("chosen")
            alternatives = decision.get("alternatives")
            if not isinstance(weights, Mapping) or not isinstance(chosen, Mapping) or not isinstance(
                alternatives, list
            ):
                continue
            candidates = [item for item in alternatives if isinstance(item, Mapping)]
            chosen_score = score_candidate(chosen, weights)
            alternative_scores = [
                score_candidate(candidate, weights) for candidate in candidates
            ]
            if candidates and all(chosen_score < score for score in alternative_scores):
                correct += 1
            conservative_rank = 1 + sum(
                score <= chosen_score for score in alternative_scores
            )
            if candidates and conservative_rank <= 3:
                top_three += 1
    count = len(decisions)
    accuracy = correct / count if count else 0.0
    top_three_coverage = top_three / count if count else 0.0
    accuracy_passed = accuracy > floor if floor_is_exclusive else accuracy >= floor
    evidence_sufficient = count >= minimum_count
    return {
        "decisionCount": count,
        "correctDecisionCount": correct,
        "preferenceAccuracy": round(accuracy, 6),
        "preferenceAccuracyFloor": floor,
        "preferenceAccuracyComparison": (
            "strictly_greater_than" if floor_is_exclusive else "greater_than_or_equal"
        ),
        "topThreeCoveredCount": top_three,
        "topThreeCoverage": round(top_three_coverage, 6),
        "topThreeCoverageFloor": top_three_floor,
        "minimumDecisionCount": minimum_count,
        "evidenceSufficient": evidence_sufficient,
        "passed": bool(
            evidence_sufficient
            and accuracy_passed
            and top_three_coverage >= top_three_floor
        ),
    }


def _sealed_model_metrics(
    model: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
    *,
    floor: float,
    top_three_floor: float = 0.0,
    evidence_mode_floor: float | None = None,
    minimum_count: int = 1,
    minimum_evidence_mode_count: int = 1,
    floor_is_exclusive: bool = False,
    require_score_backed: bool = False,
    require_tab_only: bool = False,
) -> dict[str, Any]:
    overall = _preference_metrics(
        model,
        decisions,
        floor=floor,
        top_three_floor=top_three_floor,
        minimum_count=minimum_count,
        floor_is_exclusive=floor_is_exclusive,
    )
    mode_floor = floor if evidence_mode_floor is None else evidence_mode_floor
    by_mode = {
        mode: _preference_metrics(
            model,
            [decision for decision in decisions if _decision_evidence_mode(decision) == mode],
            floor=mode_floor,
            minimum_count=minimum_evidence_mode_count,
        )
        for mode in ("score_supported", "tab_only")
    }
    required_modes_passed = (
        (not require_score_backed or bool(by_mode["score_supported"]["passed"]))
        and (not require_tab_only or bool(by_mode["tab_only"]["passed"]))
    )
    return {
        "overall": overall,
        "byEvidenceMode": by_mode,
        "requiredEvidenceModesPassed": required_modes_passed,
        "gatePassed": bool(overall["passed"]) and required_modes_passed,
    }


class SealedTestCoordinator:
    """Prepare isolated ground truth and execute every frozen cohort exactly once."""

    def __init__(
        self,
        private_root: Path | str,
        *,
        repo_root: Path | str = ".",
        extractor: AmazingTablatureExtractor | None = None,
    ) -> None:
        self.root = Path(private_root).expanduser().resolve()
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.extractor = extractor or AmazingTablatureExtractor(self.root, repo_root=self.repo_root)

    def _freeze(self, freeze_id: str) -> dict[str, Any]:
        path = self.root / "rules-freezes" / f"{freeze_id}.json"
        if not path.exists():
            raise SealedTestWorkflowError(f"Unknown rules freeze: {freeze_id}.")
        freeze = _read_json(path)
        if freeze.get("freezeId") != freeze_id or freeze.get("status") != "frozen_tests_unopened":
            raise SealedTestWorkflowError("The rules freeze is malformed or no longer eligible.")
        return freeze

    @staticmethod
    def _cohort(freeze: Mapping[str, Any], batch_id: str) -> dict[str, Any]:
        for cohort in freeze.get("sealedTestCohorts") or []:
            if cohort.get("batchId") == batch_id:
                return dict(cohort)
        raise SealedTestWorkflowError(f"Batch {batch_id} is not part of this rules freeze.")

    def _sealed_paths(self, batch_id: str) -> tuple[Path, Path, Path]:
        sealed_dir = self.root / "batches" / batch_id / "sealed-test"
        return sealed_dir, sealed_dir / "test-manifest.json", sealed_dir / "ground-truth-status.json"

    def _verify_frozen_code(self, freeze: Mapping[str, Any]) -> None:
        contracts = freeze.get("contracts") or {}
        if contracts.get("extractorVersion") != EXTRACTOR_VERSION:
            raise SealedTestWorkflowError("The active extractor version differs from the frozen version.")
        if contracts.get("extractionSchemaVersion") != EXTRACTION_SCHEMA_VERSION:
            raise SealedTestWorkflowError("The active extraction schema differs from the frozen schema.")
        if contracts.get("knowledgeSchemaVersion") != KNOWLEDGE_SCHEMA_VERSION:
            raise SealedTestWorkflowError("The active knowledge schema differs from the frozen schema.")
        for relative, expected in (freeze.get("codeFileDigests") or {}).items():
            path = self.repo_root / str(relative)
            if not path.exists() or _sha256_bytes(path.read_bytes()) != expected:
                raise SealedTestWorkflowError(f"Frozen code digest mismatch: {relative}.")
        active_reader_contracts = {
            "ocrReaderContract": (
                self.extractor.ocr.contract()
                if callable(getattr(getattr(self.extractor, "ocr", None), "contract", None))
                else None
            ),
            "omrReaderContract": (
                self.extractor.omr.contract()
                if callable(getattr(getattr(self.extractor, "omr", None), "contract", None))
                else None
            ),
            "tabReaderContract": (
                self.extractor.tab_vision.contract()
                if callable(getattr(getattr(self.extractor, "tab_vision", None), "contract", None))
                else None
            ),
        }
        for batch_id, extraction_contract in (freeze.get("validationExtractionContracts") or {}).items():
            for key, active in active_reader_contracts.items():
                if extraction_contract.get(key) != active:
                    raise SealedTestWorkflowError(
                        f"Active {key} differs from the frozen validation reader for {batch_id}."
                    )

    def prepare_ground_truth(self, batch_id: str, *, freeze_id: str) -> dict[str, Any]:
        freeze = self._freeze(freeze_id)
        cohort = self._cohort(freeze, batch_id)
        sealed_dir, manifest_path, status_path = self._sealed_paths(batch_id)
        manifest = _read_json(manifest_path)
        status = _read_json(status_path)
        if manifest.get("partitionDigest") != cohort.get("partitionDigest"):
            raise SealedTestWorkflowError("The frozen cohort does not match the sealed manifest.")
        if status.get("status") != "pending":
            if status.get("freezeId") == freeze_id and status.get("status") in {
                "annotation_in_progress",
                "ready",
                "evaluation_in_progress",
                "official_score_recorded",
            }:
                return {
                    "batchId": batch_id,
                    "freezeId": freeze_id,
                    "status": status["status"],
                    "inputCount": int(status.get("inputCount") or cohort["testCount"]),
                }
            raise SealedTestWorkflowError("Sealed ground truth was already opened under a different freeze.")
        inputs = manifest.get("inputs") or []
        if len(inputs) != int(cohort["testCount"]):
            raise SealedTestWorkflowError("The sealed cohort count does not match its freeze.")
        work = [
            {
                "inputId": item["inputId"],
                "assetSha256": item["sha256"],
                "relativePath": item["relativePath"],
                "sourceDocumentId": item["sourceDocumentId"],
                "contentUnitId": item["contentUnitId"],
                "datasetPartition": "test",
                "status": "ground_truth_pending",
            }
            for item in inputs
        ]
        _write_jsonl(sealed_dir / "ground-truth-work.jsonl", work)
        updated = {
            **status,
            "schemaVersion": SEALED_TEST_SCHEMA_VERSION,
            "freezeId": freeze_id,
            "rulesFreezeDigest": freeze["rulesEngineDigest"],
            "status": "annotation_in_progress",
            "inputCount": len(work),
            "openedAt": _utc_now(),
            "groundTruthDigest": None,
            "testRunCount": 0,
        }
        _write_json(status_path, updated)
        return {
            "batchId": batch_id,
            "freezeId": freeze_id,
            "status": "annotation_in_progress",
            "inputCount": len(work),
            "workDigest": _sha256_json(work),
        }

    def import_ground_truth(
        self,
        batch_id: str,
        source: Path | str,
        *,
        freeze_id: str,
    ) -> dict[str, Any]:
        freeze = self._freeze(freeze_id)
        cohort = self._cohort(freeze, batch_id)
        sealed_dir, manifest_path, status_path = self._sealed_paths(batch_id)
        status = _read_json(status_path)
        if status.get("freezeId") != freeze_id or status.get("status") not in {"annotation_in_progress", "ready"}:
            raise SealedTestWorkflowError("Prepare isolated ground truth under this freeze before importing it.")
        manifest = _read_json(manifest_path)
        rights_record = _read_json(sealed_dir.parent / "rights-and-access.json")
        expected_rights_digest = str(cohort.get("rightsAuthorizationDigest") or "")
        if not expected_rights_digest or rights_record.get("recordDigest") != expected_rights_digest:
            raise SealedTestWorkflowError("The current batch authorization differs from the frozen rights contract.")
        expected = {str(item["inputId"]): item for item in manifest.get("inputs") or []}
        records = _read_jsonl(Path(source).expanduser().resolve())
        by_input = {str(record.get("inputId")): record for record in records}
        if len(by_input) != len(records) or set(by_input) != set(expected):
            raise SealedTestWorkflowError("Ground truth must cover every sealed input exactly once.")
        for input_id, record in by_input.items():
            item = expected[input_id]
            if (
                record.get("batchId") != batch_id
                or record.get("datasetPartition") != "test"
                or record.get("assetSha256") != item.get("sha256")
            ):
                raise SealedTestWorkflowError(f"Ground truth identity mismatch for {input_id}.")
            copedent = record.get("sourceCopedent") or {}
            if copedent.get("id") != cohort.get("sourceCopedentId") or int(copedent.get("revision") or 0) != int(
                cohort.get("sourceCopedentRevision") or 0
            ):
                raise SealedTestWorkflowError(f"Ground truth copedent mismatch for {input_id}.")
            if record.get("reviewState") != "human_approved" or record.get("humanApprovalComplete") is not True:
                raise SealedTestWorkflowError(f"Ground truth lacks human approval for {input_id}.")
            if not str(record.get("humanReview", {}).get("reviewerReference") or "").strip():
                raise SealedTestWorkflowError(f"Ground truth lacks a reviewer reference for {input_id}.")
            rights = record.get("rightsAndAccess") or {}
            if (
                rights.get("authorizationRecordDigest") != expected_rights_digest
                or rights.get("rightsStatus") != rights_record.get("rightsStatus")
                or not bool(rights.get("allowedUses", {}).get("privateEvaluation"))
            ):
                raise SealedTestWorkflowError(f"Ground truth rights eligibility mismatch for {input_id}.")
            blockers = _hard_review_blockers(record)
            if blockers:
                raise SealedTestWorkflowError(f"Ground truth retains hard blockers for {input_id}.")
            for decision in record.get("derivedDecisions") or []:
                if not isinstance(decision, Mapping) or decision.get("reviewState") != "human_approved":
                    raise SealedTestWorkflowError(
                        f"Ground truth contains an unapproved tab-choice decision for {input_id}."
                    )
                chosen = decision.get("chosen")
                alternatives = decision.get("alternatives")
                if (
                    not isinstance(chosen, Mapping)
                    or not bool(chosen.get("mechanicallyValid"))
                    or not isinstance(alternatives, list)
                    or not alternatives
                    or any(
                        not isinstance(candidate, Mapping) or not bool(candidate.get("mechanicallyValid"))
                        for candidate in alternatives
                    )
                ):
                    raise SealedTestWorkflowError(
                        f"Ground truth contains an invalid tab-choice candidate set for {input_id}."
                    )
                if _decision_evidence_mode(decision) not in {"score_supported", "tab_only"}:
                    raise SealedTestWorkflowError(
                        f"Ground truth tab-choice evidence mode is unresolved for {input_id}."
                    )
        ordered = [by_input[input_id] for input_id in sorted(by_input)]
        digest = _sha256_json(ordered)
        destination = sealed_dir / "ground-truth.jsonl"
        if destination.exists() and _sha256_json(_read_jsonl(destination)) != digest:
            raise SealedTestWorkflowError("Sealed ground truth is immutable after import.")
        if not destination.exists():
            _write_jsonl(destination, ordered)
        updated = {
            **status,
            "status": "ready",
            "groundTruthDigest": digest,
            "groundTruthReadyAt": _utc_now(),
            "inputCount": len(ordered),
        }
        _write_json(status_path, updated)
        return {
            "batchId": batch_id,
            "freezeId": freeze_id,
            "status": "ready",
            "inputCount": len(ordered),
            "groundTruthDigest": digest,
        }

    @staticmethod
    def _empty_prediction(
        batch_id: str,
        item: Mapping[str, Any],
        profile_id: str,
        profile_revision: int,
        message: str,
    ) -> dict[str, Any]:
        return {
            "schemaVersion": EXTRACTION_SCHEMA_VERSION,
            "knowledgeSchemaVersion": KNOWLEDGE_SCHEMA_VERSION,
            "extractorVersion": EXTRACTOR_VERSION,
            "batchId": batch_id,
            "inputId": item["inputId"],
            "datasetPartition": "test",
            "sourceDocumentId": item.get("sourceDocumentId"),
            "contentUnitId": item.get("contentUnitId"),
            "assetSha256": item["sha256"],
            "sourceCopedent": {"id": profile_id, "revision": profile_revision},
            "pageOrientation": {},
            "pageClassification": {"primary": "unknown"},
            "scoreSystems": [],
            "tabSystems": [],
            "eventAlignments": [],
            "grips": [],
            "movementSequences": [],
            "derivedDecisions": [],
            "teachingConcepts": [],
            "exercises": [],
            "unresolved": [{"kind": "sealed_page_extraction_failure", "message": message[:400]}],
            "provenance": {},
            "rightsAndAccess": {},
        }

    def run(self, freeze_id: str, *, workers: int = 1) -> dict[str, Any]:
        if workers < 1 or workers > 4:
            raise SealedTestWorkflowError("Sealed-test workers must be between 1 and 4.")
        evaluation_dir = self.root / "sealed-evaluations" / freeze_id
        evaluation_dir.mkdir(parents=True, exist_ok=True)
        evaluation_dir.chmod(0o700)
        lock_path = evaluation_dir / ".evaluation.lock"
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            lock_path.chmod(0o600)
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SealedTestWorkflowError(
                    "This frozen program already has a sealed evaluation in progress."
                ) from exc
            try:
                return self._run_once(freeze_id, workers=workers)
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    def _run_once(self, freeze_id: str, *, workers: int) -> dict[str, Any]:
        freeze = self._freeze(freeze_id)
        self._verify_frozen_code(freeze)
        model_policy = freeze.get("sealedModelEvaluationPolicy") or {}
        if model_policy.get("metricVersion") != "sealed-structured-input-tab-choice-v2":
            raise SealedTestWorkflowError("The frozen tab-choice evaluation policy is missing or unsupported.")
        preference_floor = float(model_policy.get("preferenceAccuracyFloor") or 0.0)
        cohort_preference_floor = float(
            model_policy.get("cohortPreferenceAccuracyFloor") or 0.0
        )
        evidence_mode_preference_floor = float(
            model_policy.get("evidenceModePreferenceAccuracyFloor") or 0.0
        )
        top_three_floor = float(model_policy.get("topThreeCoverageFloor") or 0.0)
        floor_is_exclusive = (
            model_policy.get("preferenceAccuracyComparison")
            == "strictly_greater_than"
        )
        if not 0.0 <= preference_floor <= 1.0:
            raise SealedTestWorkflowError("The frozen tab-choice preference floor is invalid.")
        if not all(
            0.0 <= value <= 1.0
            for value in (
                cohort_preference_floor,
                evidence_mode_preference_floor,
                top_three_floor,
            )
        ):
            raise SealedTestWorkflowError("A frozen tab-choice threshold is invalid.")
        minimum_cohort_decisions = int(
            model_policy.get("minimumDecisionCountPerCohort") or 0
        )
        minimum_evidence_mode_decisions = int(
            model_policy.get("minimumDecisionCountPerEvidenceMode") or 0
        )
        if minimum_cohort_decisions < 1 or minimum_evidence_mode_decisions < 1:
            raise SealedTestWorkflowError("A frozen minimum tab-choice decision count is invalid.")
        model_path = self.root / "models" / f"{freeze['modelId']}.json"
        if not model_path.exists():
            raise SealedTestWorkflowError("The frozen challenger artifact is missing.")
        model = _read_json(model_path)
        if _sha256_json(model) != freeze.get("modelArtifactDigest"):
            raise SealedTestWorkflowError("The frozen challenger artifact digest does not match.")
        evaluation_dir = self.root / "sealed-evaluations" / freeze_id
        official_path = evaluation_dir / "official-score.json"
        cohorts = [dict(item) for item in freeze.get("sealedTestCohorts") or []]
        if official_path.exists():
            official = _read_json(official_path)
            official_digest = _sha256_json(official)
            for cohort in cohorts:
                _sealed_dir, _manifest_path, status_path = self._sealed_paths(str(cohort["batchId"]))
                status = _read_json(status_path)
                if status.get("freezeId") != freeze_id:
                    raise SealedTestWorkflowError("Recorded official score does not match a cohort freeze state.")
                if status.get("status") == "regression_set":
                    continue
                if int(status.get("testRunCount") or 0) not in {0, 1}:
                    raise SealedTestWorkflowError("Recorded official score conflicts with a cohort run count.")
                status.update(
                    {
                        "status": "official_score_recorded",
                        "officialScoreDigest": official_digest,
                        "officialScoreRecordedAt": official["evaluatedAt"],
                        "testRunCount": 1,
                        "detailsReleased": False,
                    }
                )
                _write_json(status_path, status)
            return official
        prepared: list[tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], Path]] = []
        for cohort in cohorts:
            batch_id = str(cohort["batchId"])
            sealed_dir, manifest_path, status_path = self._sealed_paths(batch_id)
            status = _read_json(status_path)
            if status.get("freezeId") != freeze_id or status.get("status") not in {"ready", "evaluation_in_progress"}:
                raise SealedTestWorkflowError(f"Ground truth is not ready for frozen cohort {batch_id}.")
            if int(status.get("testRunCount") or 0) != 0:
                raise SealedTestWorkflowError(f"Frozen cohort {batch_id} has already been evaluated.")
            manifest = _read_json(self.root / "batches" / batch_id / "manifest.json")
            test_manifest = _read_json(manifest_path)
            truth = _read_jsonl(sealed_dir / "ground-truth.jsonl")
            if _sha256_json(truth) != status.get("groundTruthDigest"):
                raise SealedTestWorkflowError(f"Ground-truth digest mismatch for {batch_id}.")
            prepared.append((cohort, manifest, list(test_manifest.get("inputs") or []), truth, status_path))

        run_id = f"atse-{_sha256_json({'freezeId': freeze_id, 'groundTruthDigests': [_read_json(item[4])['groundTruthDigest'] for item in prepared]})[:16]}"
        for _cohort, _manifest, _inputs, _truth, status_path in prepared:
            status = _read_json(status_path)
            status.update(
                {"status": "evaluation_in_progress", "evaluationRunId": run_id, "evaluationStartedAt": _utc_now()}
            )
            _write_json(status_path, status)

        evaluation_dir.mkdir(parents=True, exist_ok=True)
        evaluation_dir.chmod(0o700)
        all_pairs: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
        cohort_results: dict[str, Any] = {}
        all_model_decisions: list[dict[str, Any]] = []
        cohort_model_results: dict[str, Any] = {}
        model_category_decisions: dict[str, list[dict[str, Any]]] = {}
        page_failures = 0
        category_pairs: dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = {}
        for cohort, manifest, inputs, truth_records, _status_path in prepared:
            batch_id = str(cohort["batchId"])
            profile = get_e9_copedent_profile(str(cohort["sourceCopedentId"]))
            rights_record = _read_json(self.root / "batches" / batch_id / "rights-and-access.json")
            if rights_record.get("recordDigest") != cohort.get("rightsAuthorizationDigest"):
                raise SealedTestWorkflowError(f"Frozen rights authorization mismatch for {batch_id}.")
            rights_and_access = _normalized_rights_and_access(rights_record)
            output_root = evaluation_dir / batch_id
            predictions_dir = output_root / "predictions"
            derivatives_dir = output_root / "derivatives"
            for directory in (output_root, predictions_dir, derivatives_dir):
                directory.mkdir(parents=True, exist_ok=True)
                directory.chmod(0o700)
            truth_by_input = {str(record["inputId"]): record for record in truth_records}
            page_number_by_input = {
                str(item["inputId"]): page_number for page_number, item in enumerate(inputs, start=1)
            }
            run_contract = {
                "schemaVersion": SEALED_TEST_SCHEMA_VERSION,
                "freezeId": freeze_id,
                "rulesEngineDigest": freeze["rulesEngineDigest"],
                "batchId": batch_id,
                "partitionDigest": cohort["partitionDigest"],
                "extractorVersion": EXTRACTOR_VERSION,
                "tabReaderContract": self.extractor.tab_vision.contract(),
            }
            run_digest = _sha256_json(run_contract)

            def process(item: Mapping[str, Any]) -> dict[str, Any]:
                prediction_path = predictions_dir / f"{item['inputId']}.json"
                if prediction_path.exists():
                    existing = _read_json(prediction_path)
                    if existing.get("sealedEvaluationRunDigest") == run_digest:
                        return existing
                try:
                    prediction = self.extractor._extract_page(
                        manifest,
                        item,
                        page_number=page_number_by_input[str(item["inputId"])],
                        output_root=output_root,
                        derivatives_dir=derivatives_dir,
                        profile=profile,
                        run_digest=run_digest,
                        use_ocr=True,
                        use_omr=True,
                        use_tab_vision=True,
                        rights_and_access=rights_and_access,
                    )
                except Exception as exc:  # one failed page must still count against the official score
                    prediction = self._empty_prediction(
                        batch_id,
                        item,
                        profile.id,
                        profile.revision,
                        str(exc),
                    )
                prediction["sealedEvaluationRunDigest"] = run_digest
                _write_json(prediction_path, prediction)
                return prediction

            if workers == 1:
                predictions = [process(item) for item in inputs]
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    predictions = list(executor.map(process, inputs))
            pairs = [(prediction, truth_by_input[str(prediction["inputId"])]) for prediction in predictions]
            page_failures += sum(
                any(item.get("kind") == "sealed_page_extraction_failure" for item in prediction.get("unresolved") or [])
                for prediction in predictions
            )
            metrics = extraction_acceptance_metrics(pairs)
            cohort_results[batch_id] = metrics
            all_pairs.extend(pairs)
            cohort_decisions = [
                dict(decision)
                for record in truth_records
                for decision in record.get("derivedDecisions") or []
                if isinstance(decision, Mapping)
            ]
            cohort_model_results[batch_id] = _sealed_model_metrics(
                model,
                cohort_decisions,
                floor=cohort_preference_floor,
                top_three_floor=top_three_floor,
                evidence_mode_floor=evidence_mode_preference_floor,
                minimum_count=minimum_cohort_decisions,
                minimum_evidence_mode_count=minimum_evidence_mode_decisions,
            )
            all_model_decisions.extend(cohort_decisions)
            for decision in cohort_decisions:
                for category in decision.get("categoryTags") or []:
                    model_category_decisions.setdefault(str(category), []).append(decision)
            for pair in pairs:
                for category in _page_categories(pair[1]):
                    category_pairs.setdefault(category, []).append(pair)

        overall = extraction_acceptance_metrics(all_pairs)
        category_results = {
            category: extraction_acceptance_metrics(pairs) for category, pairs in sorted(category_pairs.items())
        }
        model_results = _sealed_model_metrics(
            model,
            all_model_decisions,
            floor=preference_floor,
            top_three_floor=top_three_floor,
            evidence_mode_floor=evidence_mode_preference_floor,
            minimum_count=sum(
                minimum_cohort_decisions for _cohort in cohorts
            ),
            minimum_evidence_mode_count=minimum_evidence_mode_decisions,
            floor_is_exclusive=floor_is_exclusive,
            require_score_backed=bool(model_policy.get("requiresScoreBackedDecisionsOverall")),
            require_tab_only=bool(model_policy.get("requiresTabOnlyDecisionsOverall")),
        )
        model_category_results = {
            category: _preference_metrics(
                model,
                decisions,
                floor=preference_floor,
                top_three_floor=top_three_floor,
                floor_is_exclusive=floor_is_exclusive,
            )
            for category, decisions in sorted(model_category_decisions.items())
        }
        extraction_gate_passed = bool(overall["allAcceptanceCriteriaPassed"]) and all(
            bool(result["allAcceptanceCriteriaPassed"]) for result in cohort_results.values()
        )
        model_gate_passed = bool(model_results["gatePassed"]) and all(
            bool(result["gatePassed"]) for result in cohort_model_results.values()
        )
        gate_passed = extraction_gate_passed and model_gate_passed
        official = {
            "schemaVersion": SEALED_TEST_SCHEMA_VERSION,
            "evaluationRunId": run_id,
            "freezeId": freeze_id,
            "rulesEngineDigest": freeze["rulesEngineDigest"],
            "modelId": freeze["modelId"],
            "authoritativeDatasetId": freeze["authoritativeDatasetId"],
            "sourceCopedentProfiles": [
                {
                    "batchId": cohort["batchId"],
                    "id": cohort["sourceCopedentId"],
                    "revision": cohort["sourceCopedentRevision"],
                    "digest": cohort.get("sourceCopedentDigest"),
                }
                for cohort in cohorts
            ],
            "evaluatedAt": _utc_now(),
            "oneShot": True,
            "testPageCount": len(all_pairs),
            "pageExtractionFailureCount": page_failures,
            "overall": overall,
            "cohorts": cohort_results,
            "categories": category_results,
            "tabChoicePrediction": {
                **model_results,
                "cohorts": cohort_model_results,
                "categories": model_category_results,
                "labelVisibility": "sealed_lane15_ground_truth_only",
                "evaluationMode": "teacher_forced_pairwise_candidate_choice",
            },
            "extractionGatePassed": extraction_gate_passed,
            "tabChoicePredictionGatePassed": model_gate_passed,
            "gatePassed": gate_passed,
            "thresholdPolicy": "fixed_pretest_no_adjustment",
            "detailedFailuresReleased": False,
        }
        _write_json(official_path, official)
        official_digest = _sha256_json(official)
        for _cohort, _manifest, _inputs, _truth, status_path in prepared:
            status = _read_json(status_path)
            status.update(
                {
                    "status": "official_score_recorded",
                    "officialScoreDigest": official_digest,
                    "officialScoreRecordedAt": official["evaluatedAt"],
                    "testRunCount": 1,
                    "detailsReleased": False,
                }
            )
            _write_json(status_path, status)
        return official

    def release_failure_details(self, freeze_id: str) -> dict[str, Any]:
        freeze = self._freeze(freeze_id)
        evaluation_dir = self.root / "sealed-evaluations" / freeze_id
        official_path = evaluation_dir / "official-score.json"
        if not official_path.exists():
            raise SealedTestWorkflowError("Record the official score before releasing detailed failures.")
        details_path = evaluation_dir / "detailed-failures.json"
        if details_path.exists():
            return _read_json(details_path)
        model_path = self.root / "models" / f"{freeze['modelId']}.json"
        if not model_path.exists():
            raise SealedTestWorkflowError("The frozen challenger artifact is missing.")
        model = _read_json(model_path)
        if _sha256_json(model) != freeze.get("modelArtifactDigest"):
            raise SealedTestWorkflowError("The frozen challenger artifact digest does not match.")
        model_policy = freeze.get("sealedModelEvaluationPolicy") or {}
        preference_floor = float(model_policy.get("preferenceAccuracyFloor") or 0.0)
        top_three_floor = float(model_policy.get("topThreeCoverageFloor") or 0.0)
        floor_is_exclusive = (
            model_policy.get("preferenceAccuracyComparison")
            == "strictly_greater_than"
        )
        pages: list[dict[str, Any]] = []
        for cohort in freeze.get("sealedTestCohorts") or []:
            batch_id = str(cohort["batchId"])
            sealed_dir, _manifest_path, status_path = self._sealed_paths(batch_id)
            status = _read_json(status_path)
            truth = {str(record["inputId"]): record for record in _read_jsonl(sealed_dir / "ground-truth.jsonl")}
            predictions_dir = evaluation_dir / batch_id / "predictions"
            for input_id, reviewed in truth.items():
                prediction = _read_json(predictions_dir / f"{input_id}.json")
                score = extraction_acceptance_metrics([(prediction, reviewed)])
                decisions = [
                    dict(decision)
                    for decision in reviewed.get("derivedDecisions") or []
                    if isinstance(decision, Mapping)
                ]
                preference = (
                    _preference_metrics(
                        model,
                        decisions,
                        floor=preference_floor,
                        top_three_floor=top_three_floor,
                        floor_is_exclusive=floor_is_exclusive,
                    )
                    if decisions
                    else {
                        "decisionCount": 0,
                        "preferenceAccuracy": None,
                        "preferenceAccuracyFloor": preference_floor,
                        "passed": None,
                        "applicable": False,
                    }
                )
                if not score["allAcceptanceCriteriaPassed"] or (decisions and not preference["passed"]):
                    pages.append(
                        {
                            "batchId": batch_id,
                            "inputId": input_id,
                            "score": score,
                            "tabChoicePrediction": preference,
                        }
                    )
            status.update({"status": "regression_set", "detailsReleased": True, "detailsReleasedAt": _utc_now()})
            _write_json(status_path, status)
        details = {
            "schemaVersion": SEALED_TEST_SCHEMA_VERSION,
            "freezeId": freeze_id,
            "releasedAt": _utc_now(),
            "holdoutStatus": "regression_set",
            "failedPageCount": len(pages),
            "pages": pages,
        }
        _write_json(details_path, details)
        return details


__all__ = ["SEALED_TEST_SCHEMA_VERSION", "SealedTestCoordinator", "SealedTestWorkflowError"]
