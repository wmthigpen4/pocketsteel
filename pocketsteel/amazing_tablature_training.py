"""Durable, private training workflow for Lane 20 Amazing Tablature.

The workflow deliberately keeps source files, annotations, evaluations, and
challenger artifacts beneath an ignored private root.  Only a sanitized,
copedent-neutral promotion artifact may cross the Lane 20 boundary to the
runtime integration lane.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import re
import secrets
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pocketsteel.e9_copedents import E9CopedentProfile, get_e9_copedent_profile
from pocketsteel.melody_decision_rules import normalize_style_family
from pocketsteel.melody_ranker import feature_vector, score_candidate, train_pairwise_ranker


TRAINING_SCHEMA_VERSION = "amazing-tablature-training-v1"
SPLIT_SCHEMA_VERSION = "amazing-tablature-split-v1"
ANNOTATION_SCHEMA_VERSION = "melody-decision-annotation-v2"
FEATURE_SCHEMA_VERSION = "melody-ranker-features-v1"
DEFAULT_PRIVATE_ROOT = Path("corpus-private/melody-decisions")

PIPELINE_STAGES = (
    "ingest",
    "partition",
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
LEGACY_PARTITIONS = {"train", "holdout"}
SPLIT_PARTITIONS = {"discovery", "validation", "test"}
PARTITIONS = LEGACY_PARTITIONS | SPLIT_PARTITIONS
BATCH_LIFECYCLE_STATES = {"active", "superseded"}
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


def _seeded_digest(seed: bytes, *values: object) -> str:
    payload = "\x1f".join(str(value) for value in values).encode("utf-8")
    return hashlib.sha256(seed + b"\x00" + payload).hexdigest()


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


def _make_private(path: Path, *, directory: bool = False) -> None:
    try:
        path.chmod(0o700 if directory else 0o600)
    except OSError as exc:
        raise TrainingWorkflowError(f"Could not protect private split material: {path}.") from exc


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


def _profile_digest(profile: E9CopedentProfile) -> str:
    return _sha256_json(
        {
            "id": profile.id,
            "revision": profile.revision,
            "openNotes": profile.open_notes_by_string(),
            "openPitchValues": profile.open_pitch_values_by_string(),
            "controls": [
                {
                    "id": control.id,
                    "type": control.control_type,
                    "changes": [
                        {
                            "string": change.string,
                            "from": change.from_note,
                            "to": change.to_note,
                            "semitones": change.semitones,
                        }
                        for change in control.changes
                    ],
                }
                for control in profile.ordered_controls()
            ],
        }
    )


def _image_structural_metadata(path: Path) -> dict[str, Any]:
    """Return non-semantic image measurements without writing a derivative."""

    try:
        from PIL import Image, ImageFilter, ImageOps, ImageStat
    except ImportError as exc:
        raise TrainingWorkflowError(
            "Full-collection partitioning requires Pillow for structural image measurements."
        ) from exc

    try:
        with Image.open(path) as image:
            exif_orientation = int(image.getexif().get(274, 1) or 1)
            normalized = ImageOps.exif_transpose(image)
            width, height = normalized.size
            grayscale = normalized.convert("L").resize((72, 96))
            statistics = ImageStat.Stat(grayscale)
            mean_luma = float(statistics.mean[0])
            contrast = float(statistics.stddev[0])
            edges = grayscale.filter(ImageFilter.FIND_EDGES)
            edge_values = list(edges.getdata())
            edge_density = sum(value >= 32 for value in edge_values) / max(1, len(edge_values))
            dhash_source = grayscale.resize((9, 8))
            pixels = list(dhash_source.getdata())
            dhash = 0
            for row in range(8):
                for column in range(8):
                    dhash = (dhash << 1) | int(
                        pixels[row * 9 + column] > pixels[row * 9 + column + 1]
                    )
        return {
            "status": "measured",
            "width": width,
            "height": height,
            "orientation": "landscape" if width > height else "portrait",
            "exifOrientation": exif_orientation,
            "meanLuma": round(mean_luma, 4),
            "contrast": round(contrast, 4),
            "edgeDensity": round(edge_density, 6),
            "dhash": f"{dhash:016x}",
        }
    except (OSError, SyntaxError, ValueError):
        return {"status": "unavailable"}


def _hamming_hex(left: str, right: str) -> int:
    return bin(int(left, 16) ^ int(right, 16)).count("1")


def _assign_quantile_bins(records: list[dict[str, Any]], field: str, output_field: str) -> None:
    measured = sorted(
        (
            (float(record["structuralMetadata"][field]), str(record["inputId"]))
            for record in records
            if record.get("structuralMetadata", {}).get("status") == "measured"
        ),
        key=lambda item: (item[0], item[1]),
    )
    rank_by_id = {input_id: rank for rank, (_value, input_id) in enumerate(measured)}
    labels = ("low", "middle", "high")
    for record in records:
        rank = rank_by_id.get(str(record["inputId"]))
        if rank is None:
            record["structuralMetadata"][output_field] = "unknown"
            continue
        bucket = min(2, (rank * 3) // max(1, len(measured)))
        record["structuralMetadata"][output_field] = labels[bucket]


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


class _UnionFind:
    def __init__(self, values: Iterable[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        keep, merge = sorted((left_root, right_root))
        self.parent[merge] = keep


def _largest_remainder_quotas(document_counts: Mapping[str, int], total: int) -> dict[str, int]:
    page_count = sum(document_counts.values())
    if page_count < 1 or total < 0 or total > page_count:
        raise TrainingWorkflowError("Invalid partition target for the registered collection.")
    exact = {document: total * count / page_count for document, count in document_counts.items()}
    quotas = {document: int(math.floor(value)) for document, value in exact.items()}
    remaining = total - sum(quotas.values())
    order = sorted(document_counts, key=lambda document: (-(exact[document] - quotas[document]), document))
    for document in order[:remaining]:
        quotas[document] += 1
    return quotas


def _unit_category_counts(unit: Mapping[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {
        f"document:{unit['sourceDocumentId']}": len(unit["inputs"]),
    }
    for record in unit["inputs"]:
        metadata = record.get("structuralMetadata", {})
        categories = (
            f"orientation:{metadata.get('orientation', 'unknown')}",
            f"luminance:{metadata.get('luminanceBin', 'unknown')}",
            f"density:{metadata.get('densityBin', 'unknown')}",
        )
        for category in categories:
            counts[category] = counts.get(category, 0) + 1
    return counts


def _choose_units(
    units: Sequence[dict[str, Any]],
    *,
    target: int,
    seed: bytes,
    label: str,
) -> set[str]:
    if target <= 0:
        return set()
    if not units:
        raise TrainingWorkflowError(f"No eligible content units remain for {label}.")
    if len(units) > 22:
        raise TrainingWorkflowError(
            "The provisional grouping produced too many independent units; increase the discovery guard or supply reviewed units."
        )
    total_pages = sum(len(unit["inputs"]) for unit in units)
    if target > total_pages:
        raise TrainingWorkflowError(f"The {label} target exceeds its eligible source pages.")
    all_categories: dict[str, int] = {}
    for unit in units:
        for category, count in _unit_category_counts(unit).items():
            all_categories[category] = all_categories.get(category, 0) + count
    desired_fraction = target / total_pages
    best: tuple[tuple[float, float, str], set[str]] | None = None
    for size in range(1, len(units) + 1):
        for chosen in itertools.combinations(units, size):
            page_total = sum(len(unit["inputs"]) for unit in chosen)
            count_error = abs(page_total - target)
            if best is not None and count_error > best[0][0]:
                continue
            selected_categories: dict[str, int] = {}
            for unit in chosen:
                for category, count in _unit_category_counts(unit).items():
                    selected_categories[category] = selected_categories.get(category, 0) + count
            distribution_error = sum(
                abs(selected_categories.get(category, 0) - count * desired_fraction)
                for category, count in all_categories.items()
            )
            ids = sorted(str(unit["contentUnitId"]) for unit in chosen)
            tie_breaker = _seeded_digest(seed, label, *ids)
            score = (float(count_error), round(distribution_error, 8), tie_breaker)
            if best is None or score < best[0]:
                best = (score, set(ids))
    if best is None:
        raise TrainingWorkflowError(f"Could not construct the {label} partition.")
    return best[1]


def _partition_distribution(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    documents: dict[str, int] = {}
    orientations: dict[str, int] = {}
    luminance: dict[str, int] = {}
    density: dict[str, int] = {}
    for record in records:
        document = str(record["sourceDocumentId"])
        documents[document] = documents.get(document, 0) + 1
        metadata = record.get("structuralMetadata", {})
        for destination, key, fallback in (
            (orientations, "orientation", "unknown"),
            (luminance, "luminanceBin", "unknown"),
            (density, "densityBin", "unknown"),
        ):
            value = str(metadata.get(key) or fallback)
            destination[value] = destination.get(value, 0) + 1
    return {
        "documents": dict(sorted(documents.items())),
        "orientation": dict(sorted(orientations.items())),
        "luminance": dict(sorted(luminance.items())),
        "structuralDensity": dict(sorted(density.items())),
    }


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
            "authoritativeBatchId": None,
            "rollbackHistory": [],
            "requiredBenchmarkGroups": list(REQUIRED_BENCHMARK_GROUPS),
        }

    def _registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return self._new_registry()
        registry = _read_json(self.registry_path)
        if registry.get("schemaVersion") != TRAINING_SCHEMA_VERSION:
            raise TrainingWorkflowError("Unsupported Amazing Tablature training registry version.")
        registry.setdefault("authoritativeBatchId", None)
        for batch in registry.get("batches", {}).values():
            batch.setdefault("lifecycleStatus", "active")
        for model in registry.get("models", {}).values():
            model.setdefault("datasetEligibility", "eligible")
            model.setdefault("eligibleForFutureComparison", True)
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
        profile = _profile_for_source(source_copedent_id)
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
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
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
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
            "lifecycleStatus": "active",
            "createdAt": created_at,
        }
        self._save_registry(registry)
        return self.batch_status(resolved_batch_id)

    @staticmethod
    def _resolve_input_names(inputs: Sequence[Mapping[str, Any]], names: Sequence[str]) -> set[str]:
        by_relative = {str(item["relativePath"]).lower(): str(item["inputId"]) for item in inputs}
        by_basename: dict[str, list[str]] = {}
        for item in inputs:
            by_basename.setdefault(Path(str(item["relativePath"])).name.lower(), []).append(str(item["inputId"]))
        resolved: set[str] = set()
        missing: list[str] = []
        for raw_name in names:
            normalized = str(raw_name).strip().replace("\\", "/").lower()
            input_id = by_relative.get(normalized)
            if input_id is None:
                candidates = by_basename.get(Path(normalized).name, [])
                if len(candidates) == 1:
                    input_id = candidates[0]
                elif len(candidates) > 1:
                    raise TrainingWorkflowError(f"Ambiguous input filename: {raw_name}.")
            if input_id is None:
                missing.append(str(raw_name))
            else:
                resolved.add(input_id)
        if missing:
            raise TrainingWorkflowError(f"Unknown registered inputs: {', '.join(sorted(missing))}.")
        return resolved

    def _split_summary(self, batch_id: str) -> dict[str, Any] | None:
        path = self._batch_dir(batch_id) / "partition-summary.json"
        return _read_json(path) if path.exists() else None

    def _require_active_batch(self, batch_id: str) -> None:
        registry = self._registry()
        batch_meta = registry["batches"].get(batch_id)
        if batch_meta is None:
            raise TrainingWorkflowError(f"Unknown batch: {batch_id}.")
        if batch_meta.get("lifecycleStatus", "active") != "active":
            raise TrainingWorkflowError("This operation cannot modify a superseded batch.")

    def _partition_records(self, batch_id: str) -> list[dict[str, Any]]:
        batch_dir = self._batch_dir(batch_id)
        summary = self._split_summary(batch_id)
        if summary is None:
            return []
        records = [
            *_read_jsonl(batch_dir / "discovery-work.jsonl"),
            *_read_jsonl(batch_dir / "validation-work.jsonl"),
        ]
        sealed = _read_json(batch_dir / "sealed-test" / "test-manifest.json")
        test_records = sealed.get("inputs")
        if not isinstance(test_records, list) or not all(isinstance(record, dict) for record in test_records):
            raise TrainingWorkflowError("The sealed test manifest is malformed.")
        records.extend(test_records)
        if len(records) != int(summary["counts"]["total"]):
            raise TrainingWorkflowError("The sealed partition membership is incomplete.")
        return sorted(records, key=lambda record: str(record["inputId"]))

    def prepare_partition(
        self,
        batch_id: str,
        *,
        document_breaks: Sequence[str],
        forced_discovery: Sequence[str],
        discovery_target: int,
        validation_target: int,
        test_target: int,
        guard_radius: int = 1,
        similarity_threshold: int = 3,
        seed: bytes | None = None,
    ) -> dict[str, Any]:
        manifest, state = self._batch(batch_id)
        if guard_radius < 0 or guard_radius > 5:
            raise TrainingWorkflowError("Discovery guard radius must be between 0 and 5 pages.")
        if similarity_threshold < 0 or similarity_threshold > 12:
            raise TrainingWorkflowError("Perceptual similarity threshold must be between 0 and 12.")
        inputs = list(manifest["inputs"])
        total = len(inputs)
        if discovery_target + validation_target + test_target != total:
            raise TrainingWorkflowError("Discovery, validation, and test targets must equal the input count.")
        if min(discovery_target, validation_target, test_target) < 1:
            raise TrainingWorkflowError("Every partition must contain at least one page.")

        normalized_config = {
            "batchId": batch_id,
            "documentBreaks": sorted(str(value).lower() for value in document_breaks),
            "forcedDiscovery": sorted(str(value).lower() for value in forced_discovery),
            "targets": {
                "discovery": discovery_target,
                "validation": validation_target,
                "test": test_target,
            },
            "guardRadius": guard_radius,
            "similarityThreshold": similarity_threshold,
            "algorithm": "guarded-contiguous-units-stratified-v1",
        }
        config_digest = _sha256_json(normalized_config)
        existing_summary = self._split_summary(batch_id)
        if existing_summary is not None:
            if existing_summary.get("configDigest") != config_digest:
                raise TrainingWorkflowError("The collection partition is already sealed with a different configuration.")
            return self.batch_status(batch_id)

        break_ids = self._resolve_input_names(inputs, document_breaks)
        forced_ids = self._resolve_input_names(inputs, forced_discovery)
        if len(forced_ids) != len(set(str(value).lower() for value in forced_discovery)):
            raise TrainingWorkflowError("Forced-discovery entries must identify unique registered pages.")

        source_root = Path(str(manifest["sourceRoot"]))
        records: list[dict[str, Any]] = []
        document_number = 1
        for index, item in enumerate(inputs):
            input_id = str(item["inputId"])
            if index and input_id in break_ids:
                document_number += 1
            relative_path = str(item["relativePath"])
            records.append(
                {
                    "inputId": input_id,
                    "relativePath": relative_path,
                    "sha256": str(item["sha256"]),
                    "size": int(item["size"]),
                    "mediaType": str(item["mediaType"]),
                    "sourceDocumentId": f"source-document-{document_number:03d}",
                    "previouslyInspected": input_id in forced_ids,
                    "guardDiscovery": False,
                    "structuralMetadata": _image_structural_metadata(source_root / relative_path),
                }
            )
        _assign_quantile_bins(records, "meanLuma", "luminanceBin")
        _assign_quantile_bins(records, "edgeDensity", "densityBin")

        records_by_document: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            records_by_document.setdefault(str(record["sourceDocumentId"]), []).append(record)
        for document_records in records_by_document.values():
            inspected_indexes = {
                index for index, record in enumerate(document_records) if record["previouslyInspected"]
            }
            guarded_indexes = {
                candidate
                for index in inspected_indexes
                for candidate in range(max(0, index - guard_radius), min(len(document_records), index + guard_radius + 1))
            }
            for index, record in enumerate(document_records):
                record["guardDiscovery"] = index in guarded_indexes and not record["previouslyInspected"]
                record["forcedDiscovery"] = index in guarded_indexes

        provisional_units: list[dict[str, Any]] = []
        for document, document_records in sorted(records_by_document.items()):
            current: list[dict[str, Any]] = []
            current_forced: bool | None = None
            for record in document_records:
                forced = bool(record["forcedDiscovery"])
                if current and forced != current_forced:
                    provisional_units.append(
                        {
                            "provisionalId": f"provisional-{len(provisional_units) + 1:04d}",
                            "sourceDocumentId": document,
                            "forcedDiscovery": bool(current_forced),
                            "inputs": current,
                        }
                    )
                    current = []
                current.append(record)
                current_forced = forced
            if current:
                provisional_units.append(
                    {
                        "provisionalId": f"provisional-{len(provisional_units) + 1:04d}",
                        "sourceDocumentId": document,
                        "forcedDiscovery": bool(current_forced),
                        "inputs": current,
                    }
                )

        unit_for_input = {
            str(record["inputId"]): str(unit["provisionalId"])
            for unit in provisional_units
            for record in unit["inputs"]
        }
        units_by_id = {str(unit["provisionalId"]): unit for unit in provisional_units}
        union = _UnionFind(units_by_id)
        cross_document_forced: set[str] = set()
        for left_index, left in enumerate(records):
            left_unit = unit_for_input[str(left["inputId"])]
            left_metadata = left["structuralMetadata"]
            for right in records[left_index + 1 :]:
                right_unit = unit_for_input[str(right["inputId"])]
                if left_unit == right_unit:
                    continue
                exact = left["sha256"] == right["sha256"]
                near = False
                if (
                    left["sourceDocumentId"] == right["sourceDocumentId"]
                    and left_metadata.get("status") == "measured"
                    and right["structuralMetadata"].get("status") == "measured"
                ):
                    near = _hamming_hex(left_metadata["dhash"], right["structuralMetadata"]["dhash"]) <= similarity_threshold
                if not exact and not near:
                    continue
                if left["sourceDocumentId"] != right["sourceDocumentId"]:
                    cross_document_forced.update((left_unit, right_unit))
                else:
                    union.union(left_unit, right_unit)

        merged: dict[str, dict[str, Any]] = {}
        for unit in provisional_units:
            provisional_id = str(unit["provisionalId"])
            root = union.find(provisional_id)
            destination = merged.setdefault(
                root,
                {
                    "sourceDocumentId": unit["sourceDocumentId"],
                    "forcedDiscovery": False,
                    "inputs": [],
                    "linkedProvisionalIds": [],
                },
            )
            destination["inputs"].extend(unit["inputs"])
            destination["linkedProvisionalIds"].append(provisional_id)
            destination["forcedDiscovery"] = bool(
                destination["forcedDiscovery"]
                or unit["forcedDiscovery"]
                or provisional_id in cross_document_forced
            )

        content_units: list[dict[str, Any]] = []
        for unit in merged.values():
            unit["inputs"].sort(key=lambda record: str(record["inputId"]))
            member_ids = [str(record["inputId"]) for record in unit["inputs"]]
            unit["contentUnitId"] = f"content-unit-{_sha256_json(member_ids)[:12]}"
            content_units.append(unit)
        content_units.sort(key=lambda unit: str(unit["contentUnitId"]))

        document_counts = {document: len(document_records) for document, document_records in records_by_document.items()}
        test_quotas = _largest_remainder_quotas(document_counts, test_target)
        selected_test: set[str] = set()
        split_seed = seed if seed is not None else secrets.token_bytes(32)
        if len(split_seed) < 16:
            raise TrainingWorkflowError("The private partition seed must contain at least 16 bytes.")
        for document in sorted(records_by_document):
            eligible = [
                unit
                for unit in content_units
                if unit["sourceDocumentId"] == document and not unit["forcedDiscovery"]
            ]
            chosen_test = _choose_units(
                eligible,
                target=test_quotas[document],
                seed=split_seed,
                label=f"{document}:test",
            )
            selected_test.update(chosen_test)
        validation_eligible = [
            unit
            for unit in content_units
            if not unit["forcedDiscovery"] and unit["contentUnitId"] not in selected_test
        ]
        selected_validation = _choose_units(
            validation_eligible,
            target=validation_target,
            seed=split_seed,
            label="all-documents:validation",
        )

        assignment_records: list[dict[str, Any]] = []
        for unit in content_units:
            unit_id = str(unit["contentUnitId"])
            partition = (
                "test"
                if unit_id in selected_test
                else "validation"
                if unit_id in selected_validation
                else "discovery"
            )
            if unit["forcedDiscovery"] and partition != "discovery":
                raise TrainingWorkflowError("A forced-discovery content unit entered a held-out partition.")
            for record in unit["inputs"]:
                assignment_records.append(
                    {
                        **record,
                        "contentUnitId": unit_id,
                        "datasetPartition": partition,
                        "status": "pending",
                    }
                )
        assignment_records.sort(key=lambda record: str(record["inputId"]))
        by_partition = {
            partition: [record for record in assignment_records if record["datasetPartition"] == partition]
            for partition in ("discovery", "validation", "test")
        }
        if abs(len(by_partition["validation"]) - validation_target) > 2:
            raise TrainingWorkflowError(
                "Provisional units could not meet the approved validation range "
                f"(selected {len(by_partition['validation'])}, target {validation_target})."
            )
        if abs(len(by_partition["test"]) - test_target) > 2:
            raise TrainingWorkflowError(
                "Provisional units could not meet the approved sealed-test range "
                f"(selected {len(by_partition['test'])}, target {test_target})."
            )
        for partition, partition_records in by_partition.items():
            documents = {str(record["sourceDocumentId"]) for record in partition_records}
            if documents != set(records_by_document):
                raise TrainingWorkflowError(f"The {partition} split does not represent every source document.")

        profile = _profile_for_source(str(manifest["sourceCopedentId"]))
        assignment_digest_payload = {
            "schemaVersion": SPLIT_SCHEMA_VERSION,
            "batchId": batch_id,
            "configDigest": config_digest,
            "sourceCopedentId": profile.id,
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
            "seedDigest": _sha256_bytes(split_seed),
            "assignments": [
                {
                    "inputId": record["inputId"],
                    "sha256": record["sha256"],
                    "sourceDocumentId": record["sourceDocumentId"],
                    "contentUnitId": record["contentUnitId"],
                    "datasetPartition": record["datasetPartition"],
                }
                for record in assignment_records
            ],
        }
        partition_digest = _sha256_json(assignment_digest_payload)
        created_at = _utc_now()
        distribution = {
            partition: _partition_distribution(partition_records)
            for partition, partition_records in by_partition.items()
        }
        content_unit_counts = {
            partition: len({str(record["contentUnitId"]) for record in partition_records})
            for partition, partition_records in by_partition.items()
        }
        summary = {
            "schemaVersion": SPLIT_SCHEMA_VERSION,
            "batchId": batch_id,
            "createdAt": created_at,
            "sealedAt": created_at,
            "status": "sealed_unopened",
            "configDigest": config_digest,
            "partitionDigest": partition_digest,
            "seedDigest": _sha256_bytes(split_seed),
            "sourceCopedentId": profile.id,
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
            "algorithm": normalized_config["algorithm"],
            "groupingReviewStatus": "provisional_structural",
            "stratificationStatus": {
                "sourceAndImageStructure": "completed",
                "pageTypeAndMusicalContent": "pending_independent_review",
            },
            "guardRadius": guard_radius,
            "similarityThreshold": similarity_threshold,
            "targets": normalized_config["targets"],
            "counts": {
                "total": total,
                **{partition: len(partition_records) for partition, partition_records in by_partition.items()},
            },
            "contentUnitCounts": content_unit_counts,
            "forcedDiscoveryCount": sum(bool(record["forcedDiscovery"]) for record in assignment_records),
            "previouslyInspectedCount": sum(bool(record["previouslyInspected"]) for record in assignment_records),
            "distribution": distribution,
            "sealedTest": {
                "status": "sealed_unopened",
                "membershipExposedInStatus": False,
                "groundTruthStatus": "pending",
            },
        }

        batch_dir = self._batch_dir(batch_id)
        sealed_dir = batch_dir / "sealed-test"
        sealed_dir.mkdir(parents=True, exist_ok=False)
        _make_private(sealed_dir, directory=True)
        seed_path = sealed_dir / "split-seed.bin"
        seed_path.write_bytes(split_seed)
        _make_private(seed_path)
        _write_json(
            sealed_dir / "test-manifest.json",
            {
                "schemaVersion": SPLIT_SCHEMA_VERSION,
                "batchId": batch_id,
                "partitionDigest": partition_digest,
                "sourceCopedentId": profile.id,
                "sourceCopedentRevision": profile.revision,
                "sourceCopedentDigest": _profile_digest(profile),
                "status": "sealed_unopened",
                "inputs": by_partition["test"],
            },
        )
        _make_private(sealed_dir / "test-manifest.json")
        _write_json(
            sealed_dir / "ground-truth-status.json",
            {
                "schemaVersion": SPLIT_SCHEMA_VERSION,
                "batchId": batch_id,
                "status": "pending",
                "inputCount": len(by_partition["test"]),
                "rulesFreezeDigest": None,
                "openedAt": None,
            },
        )
        _make_private(sealed_dir / "ground-truth-status.json")
        _write_jsonl(batch_dir / "discovery-work.jsonl", by_partition["discovery"])
        _write_jsonl(batch_dir / "validation-work.jsonl", by_partition["validation"])
        _write_jsonl(batch_dir / "annotation-work.jsonl", by_partition["discovery"])
        _write_json(batch_dir / "partition-summary.json", summary)
        state["counts"].update(
            {
                "discoveryInputs": len(by_partition["discovery"]),
                "validationInputs": len(by_partition["validation"]),
                "testInputs": len(by_partition["test"]),
            }
        )
        self._checkpoint(
            state,
            "partition",
            "completed",
            partitionDigest=partition_digest,
            discoveryCount=len(by_partition["discovery"]),
            validationCount=len(by_partition["validation"]),
            testCount=len(by_partition["test"]),
            sealedTestStatus="sealed_unopened",
        )
        self._save_state(batch_id, state)
        registry = self._registry()
        registry["batches"][batch_id]["partitionDigest"] = partition_digest
        registry["batches"][batch_id]["partitionStatus"] = "sealed_unopened"
        self._save_registry(registry)
        return self.batch_status(batch_id)

    def supersede_batch(
        self,
        batch_id: str,
        *,
        replacement_batch_id: str,
        approval_reference: str,
    ) -> dict[str, Any]:
        if batch_id == replacement_batch_id:
            raise TrainingWorkflowError("A batch cannot supersede itself.")
        if not approval_reference.strip():
            raise TrainingWorkflowError("Superseding a batch requires an explicit user decision reference.")
        registry = self._registry()
        old_meta = registry["batches"].get(batch_id)
        replacement_meta = registry["batches"].get(replacement_batch_id)
        if old_meta is None or replacement_meta is None:
            raise TrainingWorkflowError("Both the superseded and replacement batches must exist.")
        replacement_summary = self._split_summary(replacement_batch_id)
        if replacement_summary is None or replacement_summary.get("status") != "sealed_unopened":
            raise TrainingWorkflowError("The replacement batch must have a sealed partition before it becomes authoritative.")
        if old_meta.get("lifecycleStatus") == "superseded":
            if old_meta.get("supersededByBatchId") != replacement_batch_id:
                raise TrainingWorkflowError("The batch was already superseded by a different replacement.")
            return self.batch_status(batch_id)
        changed_at = _utc_now()
        old_meta.update(
            {
                "lifecycleStatus": "superseded",
                "supersededByBatchId": replacement_batch_id,
                "supersededAt": changed_at,
                "supersededDecision": approval_reference,
            }
        )
        replacement_meta["lifecycleStatus"] = "active"
        registry["authoritativeBatchId"] = replacement_batch_id
        _manifest, old_state = self._batch(batch_id)
        old_state["lifecycleStatus"] = "superseded"
        old_state["supersededByBatchId"] = replacement_batch_id
        old_state["updatedAt"] = changed_at
        self._save_state(batch_id, old_state)
        affected_models = {
            str(checkpoint.get("modelId"))
            for checkpoint in old_state.get("checkpoints", {}).values()
            if checkpoint.get("modelId")
        }
        for model_id in affected_models:
            model_meta = registry["models"].get(model_id)
            if model_meta is None:
                continue
            model_meta["datasetEligibility"] = "historical_superseded"
            model_meta["eligibleForFutureComparison"] = False
            source_batches = set(model_meta.get("supersededSourceBatches") or [])
            source_batches.add(batch_id)
            model_meta["supersededSourceBatches"] = sorted(source_batches)
        self._save_registry(registry)
        return self.batch_status(batch_id)

    def verify_batch_inputs(self, batch_id: str) -> dict[str, Any]:
        manifest, _state = self._batch(batch_id)
        source_root = Path(str(manifest["sourceRoot"]))
        failures: list[str] = []
        for item in manifest["inputs"]:
            path = source_root / str(item["relativePath"])
            if not path.exists() or path.stat().st_size != int(item["size"]):
                failures.append(str(item["inputId"]))
                continue
            if _sha256_bytes(path.read_bytes()) != item["sha256"]:
                failures.append(str(item["inputId"]))
        return {
            "batchId": batch_id,
            "inputCount": len(manifest["inputs"]),
            "verifiedCount": len(manifest["inputs"]) - len(failures),
            "sourceUnchanged": not failures,
            "failedInputIds": failures,
            "immutableDigest": manifest["immutableDigest"],
        }

    def import_annotations(self, batch_id: str, source: Path | str) -> dict[str, Any]:
        manifest, state = self._batch(batch_id)
        registry = self._registry()
        batch_meta = registry["batches"].get(batch_id, {})
        if batch_meta.get("lifecycleStatus", "active") != "active":
            raise TrainingWorkflowError("Annotations cannot be imported into a superseded batch.")
        annotation_path = Path(source).expanduser().resolve()
        records = _read_jsonl(annotation_path)
        if not records:
            raise TrainingWorkflowError("Annotation input is empty.")
        decision_ids: set[str] = set()
        input_ids = {item["inputId"] for item in manifest["inputs"]}
        partition_records = self._partition_records(batch_id)
        partition_by_input = {
            str(record["inputId"]): str(record["datasetPartition"])
            for record in partition_records
        }
        for record in records:
            decision_id = str(record.get("decisionId") or "").strip()
            if not decision_id or decision_id in decision_ids:
                raise TrainingWorkflowError("Every annotation needs a unique decisionId.")
            decision_ids.add(decision_id)
            if record.get("inputId") not in input_ids:
                raise TrainingWorkflowError(f"{decision_id} refers to an input outside batch {batch_id}.")
            if record.get("sourceCopedentId") != manifest["sourceCopedentId"]:
                raise TrainingWorkflowError(f"{decision_id} does not use the batch source copedent.")
            if partition_by_input:
                expected_partition = partition_by_input[str(record["inputId"])]
                if expected_partition == "test":
                    raise TrainingWorkflowError("Sealed-test inputs cannot enter the normal annotation workflow.")
                if record.get("datasetPartition") != expected_partition:
                    raise TrainingWorkflowError(
                        f"{decision_id} must use its sealed {expected_partition} partition."
                    )
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
        self._require_active_batch(batch_id)
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
        self._require_active_batch(batch_id)
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
                    raise TrainingWorkflowError(
                        "datasetPartition must be train, holdout, discovery, validation, or test."
                    )
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

    def _accepted_records(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        registry = self._registry()
        authoritative = registry.get("authoritativeBatchId")
        records: list[dict[str, Any]] = []
        for batch_id in sorted(registry["batches"]):
            batch_meta = registry["batches"][batch_id]
            if active_only and batch_meta.get("lifecycleStatus", "active") != "active":
                continue
            if active_only and authoritative and batch_id != authoritative:
                continue
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
        training_records = [
            record for record in accepted if record.get("datasetPartition") in {"train", "discovery"}
        ]
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
            "sourceBatchIds": sorted({str(record["batchId"]) for record in training_records}),
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
            "sourceBatchIds": payload["sourceBatchIds"],
            "datasetEligibility": "eligible",
            "eligibleForFutureComparison": True,
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
        accepted = self._accepted_records()
        holdouts = [record for record in accepted if record.get("datasetPartition") == "validation"]
        evaluation_partition = "validation"
        if not holdouts:
            holdouts = [record for record in accepted if record.get("datasetPartition") == "holdout"]
            evaluation_partition = "holdout"
        if not holdouts:
            raise TrainingWorkflowError("No validated validation decisions are available.")
        mechanical_accuracy = sum(bool(record.get("mechanicalValidation", {}).get("ok")) for record in holdouts) / len(holdouts)
        challenger_accuracy = self._model_accuracy(model, holdouts)
        champion_id = registry["channels"].get("stable")
        champion_accuracy: float | None = None
        if champion_id and champion_id != model_id:
            champion_meta = registry["models"].get(champion_id)
            if champion_meta and champion_meta.get("eligibleForFutureComparison", True):
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
            "evaluationPartition": evaluation_partition,
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
        registry = self._registry()
        meta = registry["batches"].get(batch_id, {})
        split_summary = self._split_summary(batch_id)
        payload = {
            "batchId": batch_id,
            "sourceCopedentId": manifest["sourceCopedentId"],
            "sourceCopedentConfidence": manifest["sourceCopedentConfidence"],
            "sourceCopedentRevision": manifest.get("sourceCopedentRevision", meta.get("sourceCopedentRevision", 1)),
            "sourceCopedentDigest": manifest.get("sourceCopedentDigest", meta.get("sourceCopedentDigest")),
            "evidenceType": manifest["evidenceType"],
            "immutableDigest": manifest["immutableDigest"],
            "lifecycleStatus": meta.get("lifecycleStatus", state.get("lifecycleStatus", "active")),
            "supersededByBatchId": meta.get("supersededByBatchId"),
            "counts": state["counts"],
            "checkpoints": state["checkpoints"],
        }
        if split_summary is not None:
            payload["partition"] = {
                "schemaVersion": split_summary["schemaVersion"],
                "status": split_summary["status"],
                "partitionDigest": split_summary["partitionDigest"],
                "groupingReviewStatus": split_summary.get("groupingReviewStatus", "provisional_structural"),
                "stratificationStatus": split_summary.get(
                    "stratificationStatus",
                    {
                        "sourceAndImageStructure": "completed",
                        "pageTypeAndMusicalContent": "pending_independent_review",
                    },
                ),
                "counts": split_summary["counts"],
                "contentUnitCounts": split_summary["contentUnitCounts"],
                "distribution": split_summary["distribution"],
                "sealedTest": split_summary["sealedTest"],
            }
        return payload

    def status(self) -> dict[str, Any]:
        registry = self._registry()
        batches = [self.batch_status(batch_id) for batch_id in sorted(registry["batches"])]
        return {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "root": str(self.root),
            "authoritativeBatchId": registry.get("authoritativeBatchId"),
            "batchCount": len(batches),
            "batches": batches,
            "modelCount": len(registry["models"]),
            "models": {
                model_id: {
                    "status": meta.get("status"),
                    "datasetHash": meta.get("datasetHash"),
                    "datasetEligibility": meta.get("datasetEligibility", "eligible"),
                    "eligibleForFutureComparison": meta.get("eligibleForFutureComparison", True),
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
    "SPLIT_SCHEMA_VERSION",
    "TRAINING_SCHEMA_VERSION",
    "AmazingTablatureTrainingStore",
    "TrainingWorkflowError",
]
