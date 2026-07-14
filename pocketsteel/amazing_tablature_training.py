"""Durable, private training workflow for Lane 20 Amazing Tablature.

The workflow deliberately keeps source files, annotations, evaluations, and
challenger artifacts beneath an ignored private root.  Only a sanitized,
copedent-neutral promotion artifact may cross the Lane 20 boundary to the
runtime integration lane.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pocketsteel.e9_copedents import E9CopedentProfile, get_e9_copedent_profile
from pocketsteel.melody_decision_rules import normalize_style_family
from pocketsteel.melody_ranker import feature_vector, score_candidate, train_pairwise_ranker


TRAINING_SCHEMA_VERSION = "amazing-tablature-training-v1"
ANNOTATION_SCHEMA_VERSION = "melody-decision-annotation-v2"
FEATURE_SCHEMA_VERSION = "melody-ranker-features-v1"
DEFAULT_PRIVATE_ROOT = Path("corpus-private/melody-decisions")

PIPELINE_STAGES = (
    "ingest",
    "annotate",
    "validate",
    "review_exceptions",
    "train",
    "evaluate",
    "report",
    "promote",
)
MODEL_STATES = {"challenger", "approved_beta", "approved_stable", "retired"}
EVIDENCE_TYPES = {"expert_score_tab", "player_feedback"}
REVIEW_STATUSES = {
    "machine_transcribed",
    "machine_validated",
    "needs_review",
    "audit_accepted",
    "reviewed",
    "excluded",
    "rejected",
}
TRAINING_REVIEW_STATUSES = {"machine_validated", "audit_accepted", "reviewed"}
PARTITIONS = {"train", "holdout"}
INPUT_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf", ".json", ".jsonl"}
REQUIRED_BENCHMARK_GROUPS = ("amazing_grace",)

_NOTE_RE = re.compile(r"^([A-Ga-g](?:#|b)?)(-?\d+)?$")
_NOTE_CLASS = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}
_FORBIDDEN_RUNTIME_KEYS = {
    "sourceRoot",
    "sourcePath",
    "sourceAction",
    "sourceText",
    "literalTab",
    "literalPassage",
    "inputs",
    "inputId",
    "decisionId",
    "email",
    "identity",
    "profileSnapshot",
    "customCopedent",
}


class TrainingWorkflowError(ValueError):
    """Raised when a Lane 20 operation would violate the workflow contract."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TrainingWorkflowError(f"{path} must contain a JSON object.")
    return value


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise TrainingWorkflowError(f"{path}:{line_number} must contain a JSON object.")
        records.append(value)
    return records


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    lines = [json.dumps(dict(record), ensure_ascii=False, sort_keys=True) for record in records]
    _atomic_write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def _git_revision(cwd: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _note_class(value: object) -> int:
    match = _NOTE_RE.match(str(value or "").strip())
    if not match or match.group(1) not in _NOTE_CLASS:
        raise TrainingWorkflowError(f"Invalid pitch name: {value!r}.")
    return _NOTE_CLASS[match.group(1)]


def _signed_pitch_delta(start: object, destination: object) -> int:
    delta = (_note_class(destination) - _note_class(start)) % 12
    return delta - 12 if delta > 6 else delta


def _number(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise TrainingWorkflowError(f"{field} must be numeric.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TrainingWorkflowError(f"{field} must be numeric.") from exc
    if not math.isfinite(number):
        raise TrainingWorkflowError(f"{field} must be finite.")
    return number


def _normalize_benchmark_group(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _discover_inputs(source: Path) -> list[Path]:
    if not source.exists() or not source.is_dir():
        raise TrainingWorkflowError(f"Source folder does not exist: {source}.")
    files = [
        path
        for path in source.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(source).parts)
        and path.suffix.lower() in INPUT_SUFFIXES
    ]
    if not files:
        raise TrainingWorkflowError(f"No supported score/tab files were found in {source}.")
    return sorted(files, key=lambda path: path.relative_to(source).as_posix().lower())


def _profile_for_source(copedent_id: str) -> E9CopedentProfile:
    try:
        profile = get_e9_copedent_profile(copedent_id)
    except (KeyError, ValueError) as exc:
        raise TrainingWorkflowError(f"Unknown source copedent: {copedent_id}.") from exc
    if profile.id != copedent_id:
        raise TrainingWorkflowError(f"Unknown source copedent: {copedent_id}.")
    return profile


def _candidate_features(candidate: Mapping[str, Any]) -> dict[str, Any]:
    # Evaluate once so malformed or non-finite values never reach training.
    vector = feature_vector(candidate)
    if any(not math.isfinite(float(value)) for value in vector.values()):
        raise TrainingWorkflowError("Candidate features must be finite.")
    return {
        "textureSize": int(candidate.get("textureSize") or 1),
        "barTravel": _number(candidate.get("barTravel") or 0, "barTravel"),
        "controlChanges": _number(candidate.get("controlChanges") or 0, "controlChanges"),
        "pocketChanges": _number(candidate.get("pocketChanges") or 0, "pocketChanges"),
        "voiceLeading": _number(candidate.get("voiceLeading") or 0, "voiceLeading"),
        "sustainedVoices": _number(candidate.get("sustainedVoices") or 0, "sustainedVoices"),
        "repickedVoices": _number(candidate.get("repickedVoices") or 0, "repickedVoices"),
        "phraseRole": str(candidate.get("phraseRole") or "").strip(),
    }


def _validate_voice_top(candidate: Mapping[str, Any], melody_pitch_value: int, field: str) -> None:
    if candidate.get("mechanicallyValid") is not True:
        raise TrainingWorkflowError(f"{field}.mechanicallyValid must be true.")
    voices = candidate.get("voicePitchValues")
    if not isinstance(voices, list) or not voices:
        raise TrainingWorkflowError(f"{field}.voicePitchValues must be a non-empty list.")
    normalized = [int(_number(value, f"{field}.voicePitchValues")) for value in voices]
    if max(normalized) != melody_pitch_value:
        raise TrainingWorkflowError(f"{field} does not preserve the melody as the highest sounding voice.")


def _mechanical_validation(record: Mapping[str, Any], profile: E9CopedentProfile) -> dict[str, Any]:
    source_action = record.get("sourceAction")
    abstract = record.get("abstractDecision")
    chosen = record.get("chosen")
    alternatives = record.get("alternatives")
    if not isinstance(source_action, Mapping):
        raise TrainingWorkflowError("sourceAction must be an object.")
    if not isinstance(abstract, Mapping):
        raise TrainingWorkflowError("abstractDecision must be an object.")
    if not isinstance(chosen, Mapping):
        raise TrainingWorkflowError("chosen must be an object.")
    if not isinstance(alternatives, list) or not alternatives or not all(isinstance(item, Mapping) for item in alternatives):
        raise TrainingWorkflowError("alternatives must contain at least one candidate object.")

    string = int(_number(source_action.get("string"), "sourceAction.string"))
    fret = int(_number(source_action.get("fret"), "sourceAction.fret"))
    if string not in profile.open_notes_by_string():
        raise TrainingWorkflowError("sourceAction.string must identify a source-copedent string.")
    if fret < 0 or fret > 36:
        raise TrainingWorkflowError("sourceAction.fret must be between 0 and 36.")
    start_pitch = source_action.get("startPitch")
    destination_pitch = source_action.get("destinationPitch")
    semitones = int(_number(source_action.get("semitoneChange"), "sourceAction.semitoneChange"))
    expected_start = (_note_class(profile.open_notes_by_string()[string]) + fret) % 12
    if _note_class(start_pitch) != expected_start:
        raise TrainingWorkflowError("sourceAction.startPitch does not match its string and fret on the source copedent.")

    controls_value = source_action.get("controls")
    if not isinstance(controls_value, list) or not all(isinstance(value, str) for value in controls_value):
        raise TrainingWorkflowError("sourceAction.controls must be a list of stable control IDs.")
    controls_by_id = profile.controls_by_id()
    unknown = [value for value in controls_value if value not in controls_by_id]
    if unknown:
        raise TrainingWorkflowError(f"Unknown source control IDs: {', '.join(unknown)}.")
    mechanical_delta = sum(
        change.semitones
        for control_id in controls_value
        for change in controls_by_id[control_id].changes
        if change.string == string
    )
    if mechanical_delta != semitones:
        raise TrainingWorkflowError("sourceAction.semitoneChange does not match the selected source controls.")
    if _signed_pitch_delta(start_pitch, destination_pitch) != semitones:
        raise TrainingWorkflowError("sourceAction destination pitch does not match its semitone change.")

    sounding = source_action.get("soundingStrings")
    sustained = source_action.get("sustainedStrings")
    if not isinstance(sounding, list) or not all(int(value) in profile.open_notes_by_string() for value in sounding):
        raise TrainingWorkflowError("sourceAction.soundingStrings must contain valid source strings.")
    if not isinstance(sustained, list) or not all(int(value) in profile.open_notes_by_string() for value in sustained):
        raise TrainingWorkflowError("sourceAction.sustainedStrings must contain valid source strings.")
    if not set(int(value) for value in sustained).issubset(int(value) for value in sounding):
        raise TrainingWorkflowError("Sustained strings must also be sounding strings.")

    melody_pitch_value = int(_number(abstract.get("melodyPitchValue"), "abstractDecision.melodyPitchValue"))
    if _note_class(abstract.get("melodyPitch")) != _note_class(destination_pitch):
        raise TrainingWorkflowError("abstractDecision.melodyPitch does not match the decoded destination pitch.")
    _validate_voice_top(chosen, melody_pitch_value, "chosen")
    for index, alternative in enumerate(alternatives):
        _validate_voice_top(alternative, melody_pitch_value, f"alternatives[{index}]")
    _candidate_features(chosen)
    for alternative in alternatives:
        _candidate_features(alternative)

    return {
        "ok": True,
        "sourceCopedentId": profile.id,
        "protectedStrings": sorted(set(int(value) for value in sounding + sustained)),
        "melodyPitchValue": melody_pitch_value,
        "melodyOnTop": True,
        "controlsValidatedByStableId": True,
    }


def _contains_forbidden_runtime_data(value: object, path: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if str(key) in _FORBIDDEN_RUNTIME_KEYS:
                findings.append(child_path)
            findings.extend(_contains_forbidden_runtime_data(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_contains_forbidden_runtime_data(child, f"{path}[{index}]"))
    return findings


class AmazingTablatureTrainingStore:
    """Private filesystem repository for the Lane 20 state machine."""

    def __init__(self, root: Path | str = DEFAULT_PRIVATE_ROOT, *, repo_root: Path | str = ".") -> None:
        self.root = Path(root).expanduser().resolve()
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.registry_path = self.root / "training-registry.json"

    def _new_registry(self) -> dict[str, Any]:
        return {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "batches": {},
            "models": {},
            "channels": {"beta": None, "stable": None},
            "rollbackHistory": [],
            "requiredBenchmarkGroups": list(REQUIRED_BENCHMARK_GROUPS),
        }

    def _registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return self._new_registry()
        registry = _read_json(self.registry_path)
        if registry.get("schemaVersion") != TRAINING_SCHEMA_VERSION:
            raise TrainingWorkflowError("Unsupported Amazing Tablature training registry version.")
        return registry

    def _save_registry(self, registry: Mapping[str, Any]) -> None:
        _write_json(self.registry_path, registry)

    def _batch_dir(self, batch_id: str) -> Path:
        return self.root / "batches" / batch_id

    def _batch(self, batch_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        batch_dir = self._batch_dir(batch_id)
        manifest_path = batch_dir / "manifest.json"
        state_path = batch_dir / "state.json"
        if not manifest_path.exists() or not state_path.exists():
            raise TrainingWorkflowError(f"Unknown batch: {batch_id}.")
        return _read_json(manifest_path), _read_json(state_path)

    def _save_state(self, batch_id: str, state: Mapping[str, Any]) -> None:
        _write_json(self._batch_dir(batch_id) / "state.json", state)

    @staticmethod
    def _checkpoint(state: dict[str, Any], stage: str, status: str, **details: Any) -> None:
        if stage not in PIPELINE_STAGES:
            raise TrainingWorkflowError(f"Unknown pipeline stage: {stage}.")
        state["checkpoints"][stage] = {"status": status, "updatedAt": _utc_now(), **details}
        state["updatedAt"] = _utc_now()

    def ingest(
        self,
        source: Path | str,
        *,
        source_copedent_id: str,
        source_copedent_confidence: str = "confirmed",
        evidence_type: str = "expert_score_tab",
        batch_id: str | None = None,
    ) -> dict[str, Any]:
        if evidence_type not in EVIDENCE_TYPES:
            raise TrainingWorkflowError(f"Unsupported evidence type: {evidence_type}.")
        if source_copedent_confidence not in {"confirmed", "inferred", "unknown"}:
            raise TrainingWorkflowError("Source-copedent confidence must be confirmed, inferred, or unknown.")
        if source_copedent_confidence == "unknown":
            raise TrainingWorkflowError("A batch with an unknown source copedent must remain quarantined.")
        _profile_for_source(source_copedent_id)
        source_path = Path(source).expanduser().resolve()
        files = _discover_inputs(source_path)
        inputs = [
            {
                "inputId": f"input-{index:04d}",
                "relativePath": path.relative_to(source_path).as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
                "size": path.stat().st_size,
                "mediaType": path.suffix.lower().lstrip("."),
            }
            for index, path in enumerate(files, start=1)
        ]
        immutable = {
            "sourceCopedentId": source_copedent_id,
            "sourceCopedentConfidence": source_copedent_confidence,
            "evidenceType": evidence_type,
            "inputs": inputs,
        }
        digest = _sha256_json(immutable)
        resolved_batch_id = batch_id or f"atb-{datetime.now(UTC):%Y%m%d}-{digest[:10]}"
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,79}", resolved_batch_id):
            raise TrainingWorkflowError("Batch IDs use 3-80 lowercase letters, numbers, dots, underscores, or hyphens.")
        batch_dir = self._batch_dir(resolved_batch_id)
        manifest_path = batch_dir / "manifest.json"
        if manifest_path.exists():
            existing = _read_json(manifest_path)
            if existing.get("immutableDigest") != digest:
                raise TrainingWorkflowError(f"Batch ID collision with different immutable inputs: {resolved_batch_id}.")
            return self.batch_status(resolved_batch_id)

        created_at = _utc_now()
        manifest = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "annotationSchemaVersion": ANNOTATION_SCHEMA_VERSION,
            "batchId": resolved_batch_id,
            "createdAt": created_at,
            "sourceRoot": str(source_path),
            **immutable,
            "immutableDigest": digest,
        }
        state = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "batchId": resolved_batch_id,
            "createdAt": created_at,
            "updatedAt": created_at,
            "checkpoints": {
                stage: {"status": "pending", "updatedAt": created_at}
                for stage in PIPELINE_STAGES
            },
            "counts": {"inputs": len(inputs), "annotations": 0, "accepted": 0, "exceptions": 0},
        }
        self._checkpoint(state, "ingest", "completed", inputCount=len(inputs), immutableDigest=digest)
        batch_dir.mkdir(parents=True, exist_ok=False)
        _write_json(manifest_path, manifest)
        _write_json(batch_dir / "state.json", state)
        _write_jsonl(
            batch_dir / "annotation-work.jsonl",
            (
                {"inputId": item["inputId"], "relativePath": item["relativePath"], "status": "pending"}
                for item in inputs
            ),
        )
        registry = self._registry()
        registry["batches"][resolved_batch_id] = {
            "manifest": str(manifest_path.relative_to(self.root)),
            "immutableDigest": digest,
            "evidenceType": evidence_type,
            "sourceCopedentId": source_copedent_id,
            "createdAt": created_at,
        }
        self._save_registry(registry)
        return self.batch_status(resolved_batch_id)

    def import_annotations(self, batch_id: str, source: Path | str) -> dict[str, Any]:
        manifest, state = self._batch(batch_id)
        annotation_path = Path(source).expanduser().resolve()
        records = _read_jsonl(annotation_path)
        if not records:
            raise TrainingWorkflowError("Annotation input is empty.")
        decision_ids: set[str] = set()
        input_ids = {item["inputId"] for item in manifest["inputs"]}
        for record in records:
            decision_id = str(record.get("decisionId") or "").strip()
            if not decision_id or decision_id in decision_ids:
                raise TrainingWorkflowError("Every annotation needs a unique decisionId.")
            decision_ids.add(decision_id)
            if record.get("inputId") not in input_ids:
                raise TrainingWorkflowError(f"{decision_id} refers to an input outside batch {batch_id}.")
            if record.get("sourceCopedentId") != manifest["sourceCopedentId"]:
                raise TrainingWorkflowError(f"{decision_id} does not use the batch source copedent.")
        destination = self._batch_dir(batch_id) / "annotations.jsonl"
        digest = _sha256_json(records)
        if destination.exists():
            existing = _read_jsonl(destination)
            if _sha256_json(existing) != digest:
                raise TrainingWorkflowError("Raw batch annotations are immutable; create a review correction instead.")
        else:
            _write_jsonl(destination, records)
        state["counts"]["annotations"] = len(records)
        self._checkpoint(state, "annotate", "completed", annotationCount=len(records), annotationDigest=digest)
        self._save_state(batch_id, state)
        return self.batch_status(batch_id)

    def _review_resolutions(self, batch_id: str) -> dict[str, dict[str, Any]]:
        records = _read_jsonl(self._batch_dir(batch_id) / "review-resolutions.jsonl")
        return {str(record.get("decisionId")): record for record in records if record.get("decisionId")}

    def apply_review(self, batch_id: str, source: Path | str) -> dict[str, Any]:
        self._batch(batch_id)
        incoming = _read_jsonl(Path(source).expanduser().resolve())
        if not incoming:
            raise TrainingWorkflowError("Review resolution input is empty.")
        existing = self._review_resolutions(batch_id)
        annotation_ids = {
            str(record.get("decisionId"))
            for record in _read_jsonl(self._batch_dir(batch_id) / "annotations.jsonl")
        }
        for resolution in incoming:
            decision_id = str(resolution.get("decisionId") or "").strip()
            action = str(resolution.get("action") or "").strip()
            if decision_id not in annotation_ids:
                raise TrainingWorkflowError(f"Review resolution references unknown decision: {decision_id}.")
            if action not in {"accept", "exclude", "correct"}:
                raise TrainingWorkflowError("Review actions are accept, exclude, or correct.")
            if action == "correct" and not isinstance(resolution.get("replacement"), Mapping):
                raise TrainingWorkflowError("A correct review action requires a replacement annotation.")
            existing[decision_id] = {**resolution, "reviewedAt": _utc_now()}
        _write_jsonl(
            self._batch_dir(batch_id) / "review-resolutions.jsonl",
            (existing[key] for key in sorted(existing)),
        )
        return self.validate(batch_id)

    def validate(self, batch_id: str) -> dict[str, Any]:
        manifest, state = self._batch(batch_id)
        annotations = _read_jsonl(self._batch_dir(batch_id) / "annotations.jsonl")
        if not annotations:
            raise TrainingWorkflowError(f"Batch {batch_id} has no annotations to validate.")
        profile = _profile_for_source(str(manifest["sourceCopedentId"]))
        resolutions = self._review_resolutions(batch_id)
        accepted: list[dict[str, Any]] = []
        exceptions: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        machine_candidates: list[str] = []

        for raw_record in annotations:
            decision_id = str(raw_record.get("decisionId") or "").strip()
            if not decision_id or decision_id in seen_ids:
                exceptions.append({"decisionId": decision_id or "missing", "kind": "duplicate_or_missing_id", "blocking": True})
                continue
            seen_ids.add(decision_id)
            resolution = resolutions.get(decision_id)
            if resolution and resolution.get("action") == "exclude":
                continue
            record: dict[str, Any] = dict(raw_record)
            if resolution and resolution.get("action") == "correct":
                replacement = dict(resolution["replacement"])
                replacement.setdefault("decisionId", decision_id)
                replacement.setdefault("inputId", record.get("inputId"))
                replacement.setdefault("sourceCopedentId", record.get("sourceCopedentId"))
                replacement["reviewStatus"] = "reviewed"
                record = replacement
            elif resolution and resolution.get("action") == "accept":
                record["reviewStatus"] = "reviewed"

            try:
                if record.get("inputId") not in {item["inputId"] for item in manifest["inputs"]}:
                    raise TrainingWorkflowError("inputId is outside this immutable batch.")
                if record.get("sourceCopedentId") != manifest["sourceCopedentId"]:
                    raise TrainingWorkflowError("sourceCopedentId differs from the immutable batch source copedent.")
                style = normalize_style_family(record.get("styleFamily"))
                review_status = str(record.get("reviewStatus") or "needs_review")
                if review_status not in REVIEW_STATUSES:
                    raise TrainingWorkflowError(f"Unsupported reviewStatus: {review_status}.")
                partition = str(record.get("datasetPartition") or "train")
                if partition not in PARTITIONS:
                    raise TrainingWorkflowError("datasetPartition must be train or holdout.")
                confidence = _number(record.get("confidence"), "confidence")
                if confidence < 0 or confidence > 1:
                    raise TrainingWorkflowError("confidence must be between 0 and 1.")
                mechanics = _mechanical_validation(record, profile)
                if review_status in {"excluded", "rejected"}:
                    continue
                if review_status not in TRAINING_REVIEW_STATUSES or confidence < 0.9:
                    exceptions.append(
                        {
                            "decisionId": decision_id,
                            "inputId": record.get("inputId"),
                            "kind": "review_required",
                            "blocking": True,
                            "confidence": confidence,
                        }
                    )
                    continue
                chosen = _candidate_features(record["chosen"])
                alternatives = [_candidate_features(item) for item in record["alternatives"]]
                evidence_weight = 0.25 if manifest["evidenceType"] == "player_feedback" else 1.0
                accepted.append(
                    {
                        "decisionId": decision_id,
                        "batchId": batch_id,
                        "styleFamily": style,
                        "phraseRole": str(record.get("phraseRole") or "").strip(),
                        "datasetPartition": partition,
                        "benchmarkGroup": _normalize_benchmark_group(record.get("benchmarkGroup")),
                        "reviewStatus": review_status,
                        "evidenceType": manifest["evidenceType"],
                        "evidenceWeight": evidence_weight,
                        "chosen": chosen,
                        "alternatives": alternatives,
                        "mechanicalValidation": mechanics,
                    }
                )
                if review_status == "machine_validated":
                    machine_candidates.append(decision_id)
            except (TrainingWorkflowError, ValueError, TypeError) as exc:
                exceptions.append(
                    {
                        "decisionId": decision_id,
                        "inputId": record.get("inputId"),
                        "kind": "validation_error",
                        "blocking": True,
                        "message": str(exc),
                    }
                )

        # Deterministic 10% audit sample. These records may train beta while
        # remaining explicitly machine-reviewed; the audit item is non-blocking.
        audit_count = math.ceil(len(machine_candidates) * 0.1) if machine_candidates else 0
        for decision_id in sorted(machine_candidates, key=lambda value: _sha256_bytes(value.encode("utf-8")))[:audit_count]:
            if decision_id not in resolutions:
                exceptions.append({"decisionId": decision_id, "kind": "audit_sample", "blocking": False})

        accepted.sort(key=lambda record: (record["batchId"], record["decisionId"]))
        exceptions.sort(key=lambda record: (str(record.get("decisionId")), str(record.get("kind"))))
        _write_jsonl(self._batch_dir(batch_id) / "accepted-decisions.jsonl", accepted)
        _write_jsonl(self._batch_dir(batch_id) / "exceptions.jsonl", exceptions)
        blocking = sum(1 for record in exceptions if record.get("blocking"))
        state["counts"].update(
            {"annotations": len(annotations), "accepted": len(accepted), "exceptions": len(exceptions), "blockingExceptions": blocking}
        )
        self._checkpoint(
            state,
            "validate",
            "completed" if not blocking else "needs_review",
            acceptedCount=len(accepted),
            exceptionCount=len(exceptions),
            blockingExceptionCount=blocking,
        )
        self._checkpoint(
            state,
            "review_exceptions",
            "completed" if not blocking and not exceptions else ("audit_pending" if not blocking else "needs_review"),
            exceptionCount=len(exceptions),
            blockingExceptionCount=blocking,
        )
        self._save_state(batch_id, state)
        return self.batch_status(batch_id)

    def _accepted_records(self) -> list[dict[str, Any]]:
        registry = self._registry()
        records: list[dict[str, Any]] = []
        for batch_id in sorted(registry["batches"]):
            records.extend(_read_jsonl(self._batch_dir(batch_id) / "accepted-decisions.jsonl"))
        return sorted(records, key=lambda record: (str(record.get("batchId")), str(record.get("decisionId"))))

    @staticmethod
    def _trainer_record(record: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "styleFamily": record["styleFamily"],
            "chosen": record["chosen"],
            "alternatives": record["alternatives"],
            "evidenceWeight": record["evidenceWeight"],
        }

    def train(self, *, epochs: int = 20, learning_rate: float = 0.05) -> dict[str, Any]:
        if epochs < 1 or learning_rate <= 0:
            raise TrainingWorkflowError("Training requires positive epochs and learning rate.")
        accepted = self._accepted_records()
        training_records = [record for record in accepted if record.get("datasetPartition") == "train"]
        if not training_records:
            raise TrainingWorkflowError("No validated training decisions are available.")
        trainer_records = [self._trainer_record(record) for record in training_records]
        dataset_hash = _sha256_json(trainer_records)
        config = {"epochs": int(epochs), "learningRate": float(learning_rate), "featureSchemaVersion": FEATURE_SCHEMA_VERSION}
        model_id = f"at-{_sha256_json({'datasetHash': dataset_hash, 'config': config})[:16]}"
        registry = self._registry()
        if model_id in registry["models"]:
            return _read_json(self.root / registry["models"][model_id]["artifact"])
        trained = train_pairwise_ranker(trainer_records, epochs=epochs, learning_rate=learning_rate)
        evidence_counts: dict[str, int] = {}
        review_counts: dict[str, int] = {}
        for record in training_records:
            evidence_counts[record["evidenceType"]] = evidence_counts.get(record["evidenceType"], 0) + 1
            review_counts[record["reviewStatus"]] = review_counts.get(record["reviewStatus"], 0) + 1
        payload = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "modelId": model_id,
            "status": "challenger",
            "createdAt": _utc_now(),
            "parentModelId": registry["channels"].get("stable"),
            "datasetHash": dataset_hash,
            "featureSchemaVersion": FEATURE_SCHEMA_VERSION,
            "featureNames": list(trained.feature_names),
            "weightsByStyle": trained.weights_by_style,
            "exampleCount": trained.example_count,
            "evidenceCounts": evidence_counts,
            "reviewCounts": review_counts,
            "trainingConfig": config,
            "codeRevision": _git_revision(self.repo_root),
            "copedentNeutral": True,
            "privacy": {"containsSourceContent": False, "containsProfileSnapshots": False},
        }
        findings = _contains_forbidden_runtime_data(payload)
        if findings:
            raise TrainingWorkflowError(f"Challenger contains forbidden runtime fields: {', '.join(findings)}.")
        artifact = self.root / "models" / f"{model_id}.json"
        _write_json(artifact, payload)
        registry["models"][model_id] = {
            "artifact": str(artifact.relative_to(self.root)),
            "status": "challenger",
            "createdAt": payload["createdAt"],
            "datasetHash": dataset_hash,
            "evaluation": None,
        }
        self._save_registry(registry)
        for batch_id in {record["batchId"] for record in training_records}:
            _manifest, state = self._batch(batch_id)
            self._checkpoint(state, "train", "completed", modelId=model_id, datasetHash=dataset_hash)
            self._save_state(batch_id, state)
        return payload

    @staticmethod
    def _model_accuracy(model: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> float:
        if not records:
            return 0.0
        correct = 0
        weights_by_style = model.get("weightsByStyle")
        if not isinstance(weights_by_style, Mapping):
            return 0.0
        for record in records:
            style = str(record.get("styleFamily") or "auto")
            weights = weights_by_style.get(style) or weights_by_style.get("auto") or {}
            if all(score_candidate(record["chosen"], weights) < score_candidate(alt, weights) for alt in record["alternatives"]):
                correct += 1
        return correct / len(records)

    def evaluate(self, model_id: str) -> dict[str, Any]:
        registry = self._registry()
        model_meta = registry["models"].get(model_id)
        if not model_meta:
            raise TrainingWorkflowError(f"Unknown challenger: {model_id}.")
        model = _read_json(self.root / model_meta["artifact"])
        holdouts = [record for record in self._accepted_records() if record.get("datasetPartition") == "holdout"]
        if not holdouts:
            raise TrainingWorkflowError("No validated holdout decisions are available.")
        mechanical_accuracy = sum(bool(record.get("mechanicalValidation", {}).get("ok")) for record in holdouts) / len(holdouts)
        challenger_accuracy = self._model_accuracy(model, holdouts)
        champion_id = registry["channels"].get("stable")
        champion_accuracy: float | None = None
        if champion_id and champion_id != model_id:
            champion_meta = registry["models"].get(champion_id)
            if champion_meta:
                champion = _read_json(self.root / champion_meta["artifact"])
                champion_accuracy = self._model_accuracy(champion, holdouts)
        benchmark_counts: dict[str, int] = {}
        for record in holdouts:
            group = str(record.get("benchmarkGroup") or "")
            if group:
                benchmark_counts[group] = benchmark_counts.get(group, 0) + 1
        required = list(registry.get("requiredBenchmarkGroups") or REQUIRED_BENCHMARK_GROUPS)
        missing_benchmarks = [group for group in required if not benchmark_counts.get(group)]
        privacy_findings = _contains_forbidden_runtime_data(model)
        preference_gate = challenger_accuracy >= (champion_accuracy if champion_accuracy is not None else 0.5)
        gate_passed = mechanical_accuracy == 1.0 and preference_gate and not missing_benchmarks and not privacy_findings
        evaluation = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "modelId": model_id,
            "evaluatedAt": _utc_now(),
            "holdoutCount": len(holdouts),
            "challengerPreferenceAccuracy": challenger_accuracy,
            "championModelId": champion_id,
            "championPreferenceAccuracy": champion_accuracy,
            "mechanicalAccuracy": mechanical_accuracy,
            "benchmarkCounts": benchmark_counts,
            "privacyFindings": privacy_findings,
            "gate": {
                "passed": gate_passed,
                "missingBenchmarkGroups": missing_benchmarks,
                "mechanicalValidityRequired": 1.0,
                "preferenceFloor": champion_accuracy if champion_accuracy is not None else 0.5,
            },
        }
        path = self.root / "evaluations" / f"{model_id}.json"
        _write_json(path, evaluation)
        model_meta["evaluation"] = str(path.relative_to(self.root))
        self._save_registry(registry)
        for batch_id in {record["batchId"] for record in holdouts}:
            _manifest, state = self._batch(batch_id)
            self._checkpoint(state, "evaluate", "completed", modelId=model_id, gatePassed=gate_passed)
            self._save_state(batch_id, state)
        return evaluation

    def report(self, model_id: str) -> Path:
        registry = self._registry()
        meta = registry["models"].get(model_id)
        if not meta or not meta.get("evaluation"):
            raise TrainingWorkflowError("Evaluate the challenger before generating its report.")
        model = _read_json(self.root / meta["artifact"])
        evaluation = _read_json(self.root / meta["evaluation"])
        champion_accuracy = evaluation.get("championPreferenceAccuracy")
        comparison = (
            "No stable champion is active; the first-model preference floor was used."
            if champion_accuracy is None
            else f"Champion accuracy: {float(champion_accuracy):.1%}."
        )
        lines = [
            f"# Amazing Tablature challenger {model_id}",
            "",
            f"- Status: `{model['status']}`",
            f"- Dataset hash: `{model['datasetHash']}`",
            f"- Training decisions: {model['exampleCount']}",
            f"- Holdout decisions: {evaluation['holdoutCount']}",
            f"- Mechanical validity: {float(evaluation['mechanicalAccuracy']):.1%}",
            f"- Challenger preference accuracy: {float(evaluation['challengerPreferenceAccuracy']):.1%}",
            f"- Gate: {'PASS' if evaluation['gate']['passed'] else 'FAIL'}",
            f"- Comparison: {comparison}",
            "",
            "## Evidence",
            "",
            *[f"- {key}: {value}" for key, value in sorted(model["evidenceCounts"].items())],
            "",
            "## Benchmarks",
            "",
            *[f"- {key}: {value}" for key, value in sorted(evaluation["benchmarkCounts"].items())],
            "",
            "This report contains counts and abstract model metrics only. It contains no source passages, images, or private profile data.",
        ]
        report_path = self.root / "reports" / f"{model_id}.md"
        _atomic_write_text(report_path, "\n".join(lines) + "\n")
        for batch_id in {record["batchId"] for record in self._accepted_records()}:
            _manifest, state = self._batch(batch_id)
            if state["checkpoints"]["train"].get("modelId") == model_id or state["checkpoints"]["evaluate"].get("modelId") == model_id:
                self._checkpoint(state, "report", "completed", modelId=model_id, report=str(report_path.relative_to(self.root)))
                self._save_state(batch_id, state)
        return report_path

    @staticmethod
    def _refresh_model_states(registry: dict[str, Any]) -> None:
        beta = registry["channels"].get("beta")
        stable = registry["channels"].get("stable")
        for model_id, meta in registry["models"].items():
            current = meta.get("status", "challenger")
            if model_id == stable:
                meta["status"] = "approved_stable"
            elif model_id == beta:
                meta["status"] = "approved_beta"
            elif current in {"approved_beta", "approved_stable"}:
                meta["status"] = "retired"

    def promote(
        self,
        model_id: str,
        *,
        channel: str,
        approval_reference: str,
        lane15_handoff: Path | str | None = None,
    ) -> dict[str, Any]:
        if channel not in {"beta", "stable"}:
            raise TrainingWorkflowError("Promotion channel must be beta or stable.")
        if not approval_reference.strip():
            raise TrainingWorkflowError("Promotion requires an explicit creator approval reference.")
        registry = self._registry()
        meta = registry["models"].get(model_id)
        if not meta or not meta.get("evaluation"):
            raise TrainingWorkflowError("Only evaluated challengers may be promoted.")
        evaluation = _read_json(self.root / meta["evaluation"])
        if not evaluation.get("gate", {}).get("passed"):
            raise TrainingWorkflowError("The challenger did not pass its evaluation gate.")
        lane15_value: str | None = None
        if channel == "stable":
            if lane15_handoff is None:
                raise TrainingWorkflowError("Stable promotion requires an independent Lane 15 handoff.")
            lane15_path = Path(lane15_handoff).expanduser().resolve()
            if not lane15_path.exists() or "15" not in lane15_path.name:
                raise TrainingWorkflowError("Stable promotion requires an existing Lane 15 handoff path.")
            lane15_value = str(lane15_path)
        previous = registry["channels"].get(channel)
        registry["channels"][channel] = model_id
        registry["rollbackHistory"].append(
            {
                "action": "promote",
                "channel": channel,
                "fromModelId": previous,
                "toModelId": model_id,
                "approvalReference": approval_reference,
                "lane15Handoff": lane15_value,
                "at": _utc_now(),
            }
        )
        self._refresh_model_states(registry)
        self._save_registry(registry)
        model = _read_json(self.root / meta["artifact"])
        runtime = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "modelId": model_id,
            "status": registry["models"][model_id]["status"],
            "featureSchemaVersion": model["featureSchemaVersion"],
            "featureNames": model["featureNames"],
            "weightsByStyle": model["weightsByStyle"],
            "exampleCount": model["exampleCount"],
            "copedentNeutral": True,
            "privacy": {"containsSourceContent": False, "containsProfileSnapshots": False},
        }
        findings = _contains_forbidden_runtime_data(runtime)
        if findings:
            raise TrainingWorkflowError(f"Promotion artifact contains forbidden fields: {', '.join(findings)}.")
        promotion_path = self.root / "promotions" / f"{channel}-{model_id}.json"
        _write_json(promotion_path, runtime)
        return {"channel": channel, "modelId": model_id, "previousModelId": previous, "artifact": str(promotion_path)}

    def reject(self, model_id: str, *, approval_reference: str) -> dict[str, Any]:
        if not approval_reference.strip():
            raise TrainingWorkflowError("Rejection requires a creator decision reference.")
        registry = self._registry()
        meta = registry["models"].get(model_id)
        if not meta:
            raise TrainingWorkflowError(f"Unknown challenger: {model_id}.")
        if model_id in registry["channels"].values():
            raise TrainingWorkflowError("An active model must be rolled back or replaced before it can be retired.")
        meta["status"] = "retired"
        meta["retiredReason"] = "creator_rejected"
        meta["decisionReference"] = approval_reference
        self._save_registry(registry)
        return {"modelId": model_id, "status": "retired", "decision": "rejected"}

    def rollback(self, *, channel: str, model_id: str, approval_reference: str) -> dict[str, Any]:
        if channel not in {"beta", "stable"}:
            raise TrainingWorkflowError("Rollback channel must be beta or stable.")
        if not approval_reference.strip():
            raise TrainingWorkflowError("Rollback requires an explicit creator approval reference.")
        registry = self._registry()
        if model_id not in registry["models"]:
            raise TrainingWorkflowError(f"Unknown rollback model: {model_id}.")
        previous = registry["channels"].get(channel)
        if previous == model_id:
            return {"channel": channel, "modelId": model_id, "previousModelId": previous}
        history_targets = {
            entry.get("fromModelId")
            for entry in registry["rollbackHistory"]
            if entry.get("channel") == channel
        }
        if model_id not in history_targets:
            raise TrainingWorkflowError("Rollback is limited to a previously active model on that channel.")
        registry["channels"][channel] = model_id
        registry["rollbackHistory"].append(
            {
                "action": "rollback",
                "channel": channel,
                "fromModelId": previous,
                "toModelId": model_id,
                "approvalReference": approval_reference,
                "at": _utc_now(),
            }
        )
        self._refresh_model_states(registry)
        self._save_registry(registry)
        return {"channel": channel, "modelId": model_id, "previousModelId": previous}

    def batch_status(self, batch_id: str) -> dict[str, Any]:
        manifest, state = self._batch(batch_id)
        return {
            "batchId": batch_id,
            "sourceCopedentId": manifest["sourceCopedentId"],
            "sourceCopedentConfidence": manifest["sourceCopedentConfidence"],
            "evidenceType": manifest["evidenceType"],
            "immutableDigest": manifest["immutableDigest"],
            "counts": state["counts"],
            "checkpoints": state["checkpoints"],
        }

    def status(self) -> dict[str, Any]:
        registry = self._registry()
        batches = [self.batch_status(batch_id) for batch_id in sorted(registry["batches"])]
        return {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "root": str(self.root),
            "batchCount": len(batches),
            "batches": batches,
            "modelCount": len(registry["models"]),
            "models": {
                model_id: {
                    "status": meta.get("status"),
                    "datasetHash": meta.get("datasetHash"),
                    "evaluation": meta.get("evaluation"),
                }
                for model_id, meta in sorted(registry["models"].items())
            },
            "channels": registry["channels"],
            "requiredBenchmarkGroups": registry.get("requiredBenchmarkGroups", []),
        }


__all__ = [
    "ANNOTATION_SCHEMA_VERSION",
    "DEFAULT_PRIVATE_ROOT",
    "FEATURE_SCHEMA_VERSION",
    "MODEL_STATES",
    "PIPELINE_STAGES",
    "TRAINING_SCHEMA_VERSION",
    "AmazingTablatureTrainingStore",
    "TrainingWorkflowError",
]
