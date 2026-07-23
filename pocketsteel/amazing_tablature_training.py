"""Durable, private training workflow for Lane 20 Amazing Tablature.

The workflow deliberately keeps source files, annotations, evaluations, and
challenger artifacts beneath an ignored private root.  Only a sanitized,
copedent-neutral promotion artifact may cross the Lane 20 boundary to the
runtime integration lane.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import itertools
import json
import math
import os
import re
import secrets
import subprocess
import tempfile
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image

from pocketsteel.amazing_tablature_glyph_decoder import (
    contact_sheet_token_crops,
    glyph_feature_vector,
    glyph_label,
    train_glyph_decoder,
)
from pocketsteel.amazing_tablature_input_parity import structured_input_parity_report
from pocketsteel.amazing_tablature_reader_calibration import (
    FOCUSED_READER_INPUT_MODE,
    READER_INPUT_MODE,
    UNRESOLVED_READER_STATE,
    reader_state_signature,
    train_reader_calibration,
)
from pocketsteel.amazing_tablature_transition_decoder import (
    train_transition_decoder,
    transition_training_rows,
)
from pocketsteel.e9_copedents import E9CopedentProfile, e9_copedent_profile_digest, get_e9_copedent_profile
from pocketsteel.melody_decision_rules import normalize_style_family
from pocketsteel.melody_ranker import feature_vector, score_candidate, train_pairwise_ranker


TRAINING_SCHEMA_VERSION = "amazing-tablature-training-v1"
SPLIT_SCHEMA_VERSION = "amazing-tablature-split-v1"
SPLIT_REVIEW_SCHEMA_VERSION = "amazing-tablature-split-review-v1"
SEMANTIC_GROUP_SCHEMA_VERSION = "amazing-tablature-semantic-groups-v1"
RULES_FREEZE_SCHEMA_VERSION = "amazing-tablature-rules-freeze-v1"
DISCOVERY_SEED_SCHEMA_VERSION = "amazing-tablature-discovery-seed-v1"
DISCOVERY_SHADOW_SCHEMA_VERSION = "amazing-tablature-discovery-shadow-v2"
CHALLENGER_PREFERENCE_SCHEMA_VERSION = "amazing-tablature-challenger-preference-v1"
ANNOTATION_SCHEMA_VERSION = "melody-decision-annotation-v2"
FEATURE_SCHEMA_VERSION = "melody-ranker-features-v3-phrase-sequence"
VALIDATION_LINE_PREFLIGHT_VERSION = "validation-line-structural-preflight-v1"
CONTACT_SHEET_TRUTH_MAPPING_VERSION = (
    "contact-sheet-source-column-lineage-v1"
)
DEFAULT_PRIVATE_ROOT = Path("corpus-private/melody-decisions")

# These gates are part of the predeclared validation contract.  They must not
# be tuned after validation evidence has been opened.
# The primary launch claim is deliberately narrower than score-image or audio
# transcription: it measures the ranker after the musical events are already
# normalized.  Overall top-choice accuracy must be strictly greater than 95%;
# equality is not a pass.  Image/audio recognition remains a separate metric.
VALIDATION_OVERALL_PREFERENCE_FLOOR = 0.95
VALIDATION_COHORT_PREFERENCE_FLOOR = 0.90
VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR = 0.90
VALIDATION_TOP_THREE_COVERAGE_FLOOR = 0.99
VALIDATION_MIN_DECISIONS_PER_COHORT = 10
VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE = 20
# Recognition is measured separately from tablature-choice ranking.  These
# fixed floors are deliberately not substitutes for the full atomic OCR/OMR
# acceptance contract; they are the pre-freeze line-audit gates available from
# the compact expert validation review.
VALIDATION_LINE_PAGE_DETECTION_FLOOR = 0.95
VALIDATION_LINE_SCORE_READER_FLOOR = 0.97
VALIDATION_LINE_TAB_CONFIRMATION_FLOOR = 0.98
VALIDATION_LINE_RESOLUTION_FLOOR = 0.98
CANONICAL_STYLE_FAMILIES = (
    "chord_melody",
    "harmonized",
    "lever_driven",
    "single_note_run",
)
EXPECTED_REVIEWED_PREFERENCE_COUNT = 16
EXPECTED_TRAINING_PREFERENCE_COUNT = 6
EXPECTED_COVALID_PREFERENCE_COUNT = 10

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
TRAINING_REVIEW_STATUSES = {"audit_accepted", "reviewed"}
LEGACY_PARTITIONS = {"train", "holdout"}
SPLIT_PARTITIONS = {"discovery", "validation", "test"}
PARTITIONS = LEGACY_PARTITIONS | SPLIT_PARTITIONS
BATCH_LIFECYCLE_STATES = {"active", "superseded"}
RIGHTS_STATUSES = {"unknown", "owner_authorized", "licensed", "public_domain_verified", "user_provided_authorized"}
USE_KEYS = {
    "privateExtraction",
    "privateEvaluation",
    "modelTraining",
    "embeddings",
    "quotation",
    "publicDisplay",
    "runtimeProductUse",
    "derivativeRulePublication",
}
INPUT_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf", ".json", ".jsonl"}
REQUIRED_BENCHMARK_GROUPS = ("amazing_grace",)
RULES_CODE_FILES = (
    "pocketsteel/amazing_tablature_glyph_decoder.py",
    "pocketsteel/amazing_tablature_input_parity.py",
    "pocketsteel/amazing_tablature_reader_calibration.py",
    "pocketsteel/amazing_tablature_model.py",
    "pocketsteel/amazing_tablature_decisions.py",
    "pocketsteel/amazing_tablature_extraction.py",
    "pocketsteel/amazing_tablature_sealed_test.py",
    "pocketsteel/amazing_tablature_training.py",
    "pocketsteel/amazing_tablature_transition_decoder.py",
    "pocketsteel/answer_tab_examples.py",
    "pocketsteel/copedent_transfer.py",
    "pocketsteel/e9_copedents.py",
    "pocketsteel/fretboard_examples.py",
    "pocketsteel/fretboard_explorer.py",
    "pocketsteel/melody_arranger.py",
    "pocketsteel/melody_decision_rules.py",
    "pocketsteel/melody_models.py",
    "pocketsteel/melody_ranker.py",
    "pocketsteel/melody_ranker_adapter.py",
    "pocketsteel/tab_engine.py",
    "scripts/amazing_tablature.py",
)

_NOTE_RE = re.compile(r"^([A-Ga-g](?:#|b)?)(-?\d+)?$")
_CONTACT_SHEET_LABEL_RE = re.compile(
    r"^e(?P<event>\d+)s(?P<string>\d+)$",
    re.I,
)
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


def _discovery_line_review_readiness(
    *,
    page_human_approved: bool,
    current_tab_revision_confirmed: bool,
    challenger_line_previously_reviewed: bool = False,
) -> tuple[bool, list[str]]:
    """Explain whether one unapproved line may enter the shadow review queue.

    Line identity is handled by the caller before this gate.  A different line
    on the same page being approved must not suppress this line; the only page-
    level prerequisites are a human-approved source record and confirmation of
    the current tablature revision.
    """

    reasons: list[str] = []
    if not page_human_approved:
        reasons.append("page_not_human_approved")
    if not current_tab_revision_confirmed:
        reasons.append("current_tab_revision_not_confirmed")
    if challenger_line_previously_reviewed:
        reasons.append("challenger_line_previously_reviewed")
    return not reasons, reasons


def _challenger_line_previously_reviewed(
    *,
    input_id: str,
    score_system_id: str,
    decision_ids: Iterable[str],
    reviewed_line_keys: set[tuple[str, str]],
    reviewed_decision_ids: set[str],
) -> bool:
    """Suppress a reviewed line even if its geometry-derived system ID changes.

    The exact line key remains the primary identity.  Reviewed decision IDs are
    a second lineage anchor so a later score-system recapture cannot create an
    avoidable rereview merely by assigning a different score-system ID.
    """

    if (input_id, score_system_id) in reviewed_line_keys:
        return True
    return any(str(value) in reviewed_decision_ids for value in decision_ids)


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


def _contact_sheet_signature(
    tab_system: Mapping[str, Any],
) -> str:
    """Identify the immutable image/label contract for one tab system."""

    return _sha256_json(
        [
            {
                "relativePath": str(sheet.get("relativePath") or ""),
                "sha256": str(sheet.get("sha256") or ""),
                "labels": [
                    str(value) for value in sheet.get("labels") or ()
                ],
            }
            for sheet in tab_system.get("contactSheets") or ()
        ]
    )


def _source_contact_record(
    extraction_root: Path,
    input_id: str,
    approved_record: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str, str]:
    """Load the earliest record that generated the approved contact sheets.

    Contact-sheet labels refer to source candidate columns. Human corrections
    may later remove, insert, or renumber normalized events, so the approved
    event index is not valid source-column lineage. The earliest archived
    machine revision is preferred; an unmodified revision-one page record is
    the fallback when no correction archive exists.
    """

    revision_dir = (
        extraction_root
        / "review"
        / "machine-record-revisions"
        / input_id
    )
    candidate_paths = sorted(revision_dir.glob("revision-*.json"))
    page_path = extraction_root / "pages" / f"{input_id}.json"
    if page_path.exists():
        candidate_paths.append(page_path)
    approved_systems = [
        system
        for system in approved_record.get("tabSystems") or ()
        if system.get("contactSheets")
    ]
    for path in candidate_paths:
        source_record = _read_json(path)
        if str(source_record.get("inputId") or "") != input_id:
            continue
        source_by_signature: dict[str, list[dict[str, Any]]] = {}
        for system in source_record.get("tabSystems") or ():
            if not system.get("contactSheets"):
                continue
            source_by_signature.setdefault(
                _contact_sheet_signature(system),
                [],
            ).append(dict(system))
        source_systems: dict[str, dict[str, Any]] = {}
        valid = True
        for approved_system in approved_systems:
            matches = source_by_signature.get(
                _contact_sheet_signature(approved_system),
                [],
            )
            if len(matches) != 1:
                valid = False
                break
            source_systems[
                str(approved_system.get("tabSystemId") or "")
            ] = matches[0]
        if valid and len(source_systems) == len(approved_systems):
            digest = _sha256_json(source_record)
            return (
                source_record,
                source_systems,
                digest,
                str(path.relative_to(extraction_root)),
            )
    raise TrainingWorkflowError(
        "No immutable source record matches the approved contact sheets for "
        f"{input_id}."
    )


def _contact_sheet_truth_by_source_column(
    source_tab_system: Mapping[str, Any],
    approved_tab_system: Mapping[str, Any],
) -> tuple[
    dict[int, Mapping[str, Any] | None],
    set[int],
    dict[str, int],
]:
    """Map source contact columns to corrected events without positional drift.

    Stable tab-event IDs are authoritative. Explicit
    ``sourceCandidateEventIndex`` lineage is the only accepted substitute.
    A removed or originally empty source column is a reviewed blank only when
    the approved system has no unlinked inserted event that could occupy it.
    Otherwise the column is ambiguous and excluded from calibration.
    """

    label_columns = {
        int(match.group("event"))
        for sheet in source_tab_system.get("contactSheets") or ()
        for raw_label in sheet.get("labels") or ()
        if (
            match := _CONTACT_SHEET_LABEL_RE.fullmatch(str(raw_label))
        )
    }
    source_by_column: dict[int, Mapping[str, Any]] = {}
    source_ids: set[str] = set()
    for event in source_tab_system.get("tabEvents") or ():
        column = int(event.get("eventIndex") or 0)
        event_id = str(event.get("tabEventId") or "")
        if (
            column <= 0
            or not event_id
            or column in source_by_column
            or event_id in source_ids
        ):
            raise TrainingWorkflowError(
                "Source contact-sheet event lineage is duplicated or missing."
            )
        source_by_column[column] = event
        source_ids.add(event_id)

    approved_by_id: dict[str, Mapping[str, Any]] = {}
    explicit_by_column: dict[int, list[Mapping[str, Any]]] = {}
    unlinked_insertions: list[Mapping[str, Any]] = []
    for event in approved_tab_system.get("tabEvents") or ():
        event_id = str(event.get("tabEventId") or "")
        if not event_id or event_id in approved_by_id:
            raise TrainingWorkflowError(
                "Approved contact-sheet event lineage is duplicated or missing."
            )
        approved_by_id[event_id] = event
        raw_source_column = event.get("sourceCandidateEventIndex")
        if raw_source_column is not None:
            source_column = int(raw_source_column)
            if source_column <= 0:
                raise TrainingWorkflowError(
                    "Approved source candidate lineage must be positive."
                )
            explicit_by_column.setdefault(source_column, []).append(event)
        elif event_id not in source_ids:
            unlinked_insertions.append(event)

    truth_by_column: dict[int, Mapping[str, Any] | None] = {}
    ambiguous_columns: set[int] = set()
    counts = {
        "stableTabEventId": 0,
        "explicitSourceCandidateIndex": 0,
        "reviewedBlank": 0,
        "ambiguousUnlinkedInsertion": 0,
    }
    for column in sorted(label_columns):
        source_event = source_by_column.get(column)
        stable_event = (
            approved_by_id.get(str(source_event.get("tabEventId") or ""))
            if source_event is not None
            else None
        )
        explicit_events = explicit_by_column.get(column, [])
        if stable_event is not None and (
            not explicit_events or explicit_events == [stable_event]
        ):
            truth_by_column[column] = stable_event
            counts["stableTabEventId"] += 1
            continue
        if stable_event is None and len(explicit_events) == 1:
            truth_by_column[column] = explicit_events[0]
            counts["explicitSourceCandidateIndex"] += 1
            continue
        if (
            stable_event is None
            and not explicit_events
            and not unlinked_insertions
        ):
            truth_by_column[column] = None
            counts["reviewedBlank"] += 1
            continue
        ambiguous_columns.add(column)
        counts["ambiguousUnlinkedInsertion"] += 1
    return truth_by_column, ambiguous_columns, counts


def _jsonl_text(records: Iterable[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(dict(record), ensure_ascii=False, sort_keys=True)
        for record in records
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    _atomic_write_text(path, _jsonl_text(records))


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


def _rules_code_file_digests(repo_root: Path) -> dict[str, str]:
    return {
        relative: _sha256_bytes((repo_root / relative).read_bytes())
        for relative in RULES_CODE_FILES
        if (repo_root / relative).exists()
    }


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
        number = float(str(value))
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
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(source).parts)
        and path.suffix.lower() in INPUT_SUFFIXES
    ]
    if not files:
        raise TrainingWorkflowError(f"No supported score/tab files were found in {source}.")
    return sorted(files, key=lambda path: path.relative_to(source).as_posix().lower())


def _profile_digest(profile: E9CopedentProfile) -> str:
    return e9_copedent_profile_digest(profile)


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
                    dhash = (dhash << 1) | int(pixels[row * 9 + column] > pixels[row * 9 + column + 1])
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
        "incomingStringDistance": _number(
            candidate.get("incomingStringDistance") or 0, "incomingStringDistance"
        ),
        "incomingFretDirection": _number(
            candidate.get("incomingFretDirection") or 0, "incomingFretDirection"
        ),
        "incomingStringDirection": _number(
            candidate.get("incomingStringDirection") or 0, "incomingStringDirection"
        ),
        "outgoingBarTravel": _number(
            candidate.get("outgoingBarTravel") or 0, "outgoingBarTravel"
        ),
        "outgoingControlChanges": _number(
            candidate.get("outgoingControlChanges") or 0, "outgoingControlChanges"
        ),
        "outgoingStringDistance": _number(
            candidate.get("outgoingStringDistance") or 0, "outgoingStringDistance"
        ),
        "outgoingFretDirection": _number(
            candidate.get("outgoingFretDirection") or 0, "outgoingFretDirection"
        ),
        "outgoingStringDirection": _number(
            candidate.get("outgoingStringDirection") or 0, "outgoingStringDirection"
        ),
        "outgoingSustainContinuity": _number(
            candidate.get("outgoingSustainContinuity") or 0,
            "outgoingSustainContinuity",
        ),
        "fretDirectionReversal": _number(
            candidate.get("fretDirectionReversal") or 0, "fretDirectionReversal"
        ),
        "fretDirectionContinuation": _number(
            candidate.get("fretDirectionContinuation") or 0,
            "fretDirectionContinuation",
        ),
        "stringDirectionReversal": _number(
            candidate.get("stringDirectionReversal") or 0,
            "stringDirectionReversal",
        ),
        "stringDirectionContinuation": _number(
            candidate.get("stringDirectionContinuation") or 0,
            "stringDirectionContinuation",
        ),
        "phraseRole": str(candidate.get("phraseRole") or "").strip(),
    }


def _candidate_action_signature(candidate: Mapping[str, Any]) -> tuple[tuple[object, ...], ...]:
    """Match reviewed alternatives without persisting literal source actions."""

    return tuple(
        sorted(
            (
                int(action.get("string") or 0),
                int(action.get("fret") or 0),
                tuple(sorted(str(value) for value in action.get("controls") or [])),
                int(action.get("soundingPitchValue") or 0),
                bool(action.get("attack", True)),
            )
            for action in candidate.get("mechanicalActions") or []
            if isinstance(action, Mapping)
        )
    )


def _legacy_candidate_digest(candidate: Mapping[str, Any]) -> str:
    """Retain lineage to reviewed v1/v2 candidate digests after feature expansion."""

    return _sha256_json(
        {
            "textureSize": int(candidate.get("textureSize") or 1),
            "barTravel": _number(candidate.get("barTravel") or 0, "barTravel"),
            "controlChanges": _number(
                candidate.get("controlChanges") or 0, "controlChanges"
            ),
            "pocketChanges": _number(
                candidate.get("pocketChanges") or 0, "pocketChanges"
            ),
            "voiceLeading": _number(
                candidate.get("voiceLeading") or 0, "voiceLeading"
            ),
            "sustainedVoices": _number(
                candidate.get("sustainedVoices") or 0, "sustainedVoices"
            ),
            "repickedVoices": _number(
                candidate.get("repickedVoices") or 0, "repickedVoices"
            ),
            "phraseRole": str(candidate.get("phraseRole") or "").strip(),
        }
    )


def _normalize_decision_style(value: object) -> str:
    """Map extractor-only movement labels onto the stable ranker style contract."""

    style = str(value or "auto").strip().lower().replace("-", "_")
    if style == "control_or_bar_movement":
        style = "lever_driven"
    return normalize_style_family(style)


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
    if (
        not isinstance(alternatives, list)
        or not alternatives
        or not all(isinstance(item, Mapping) for item in alternatives)
    ):
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
        raise TrainingWorkflowError(
            "sourceAction.startPitch does not match its string and fret on the source copedent."
        )

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
        "sourceCopedentRevision": profile.revision,
        "sourceCopedentDigest": _profile_digest(profile),
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


def _default_rights_record(batch_id: str) -> dict[str, Any]:
    return {
        "schemaVersion": TRAINING_SCHEMA_VERSION,
        "batchId": batch_id,
        "revision": 1,
        "rightsStatus": "unknown",
        "reviewStatus": "pending",
        "allowedUses": {key: key in {"privateExtraction", "privateEvaluation"} for key in sorted(USE_KEYS)},
        "approvalReference": None,
        "recordedAt": _utc_now(),
    }


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
    total_pages = sum(len(unit["inputs"]) for unit in units)
    if target > total_pages:
        raise TrainingWorkflowError(f"The {label} target exceeds its eligible source pages.")
    all_categories: dict[str, int] = {}
    for unit in units:
        for category, count in _unit_category_counts(unit).items():
            all_categories[category] = all_categories.get(category, 0) + count
    desired_fraction = target / total_pages
    best: tuple[tuple[float, float, str], set[str]] | None = None
    if len(units) <= 22:
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
                selected_ids = sorted(str(unit["contentUnitId"]) for unit in chosen)
                tie_breaker = _seeded_digest(seed, label, *selected_ids)
                score = (float(count_error), round(distribution_error, 8), tie_breaker)
                if best is None or score < best[0]:
                    best = (score, set(selected_ids))
    else:
        # Explicit page-level content units can exceed the practical limit for
        # exhaustive subset enumeration. Retain a deterministic beam of the
        # most structurally representative candidates for each page total.
        beam_width = 256
        max_total = min(total_pages, target + 2)
        states: dict[int, list[tuple[tuple[str, ...], dict[str, int]]]] = {0: [((), {})]}
        for unit in sorted(units, key=lambda value: str(value["contentUnitId"])):
            unit_id = str(unit["contentUnitId"])
            unit_size = len(unit["inputs"])
            unit_categories = _unit_category_counts(unit)
            expanded = {page_total: list(candidates) for page_total, candidates in states.items()}
            for page_total, candidates in states.items():
                next_total = page_total + unit_size
                if next_total > max_total:
                    continue
                destination = expanded.setdefault(next_total, [])
                for unit_ids, categories in candidates:
                    combined = dict(categories)
                    for category, count in unit_categories.items():
                        combined[category] = combined.get(category, 0) + count
                    destination.append(((*unit_ids, unit_id), combined))
            states = {}
            for page_total, candidates in expanded.items():
                partial_fraction = page_total / total_pages
                candidates.sort(
                    key=lambda candidate: (
                        round(
                            sum(
                                abs(candidate[1].get(category, 0) - count * partial_fraction)
                                for category, count in all_categories.items()
                            ),
                            8,
                        ),
                        _seeded_digest(seed, label, *candidate[0]),
                    )
                )
                states[page_total] = candidates[:beam_width]
        for page_total, candidates in states.items():
            if page_total < 1:
                continue
            for unit_ids, selected_categories in candidates:
                distribution_error = sum(
                    abs(selected_categories.get(category, 0) - count * desired_fraction)
                    for category, count in all_categories.items()
                )
                score = (
                    float(abs(page_total - target)),
                    round(distribution_error, 8),
                    _seeded_digest(seed, label, *unit_ids),
                )
                if best is None or score < best[0]:
                    best = (score, set(unit_ids))
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
            "authoritativeDataset": None,
            "datasetHistory": [],
            "rollbackHistory": [],
            "rulesFreezes": {},
            "discoverySeeds": {},
            "requiredBenchmarkGroups": list(REQUIRED_BENCHMARK_GROUPS),
        }

    def _registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return self._new_registry()
        registry = _read_json(self.registry_path)
        if registry.get("schemaVersion") != TRAINING_SCHEMA_VERSION:
            raise TrainingWorkflowError("Unsupported Amazing Tablature training registry version.")
        registry.setdefault("authoritativeBatchId", None)
        registry.setdefault("authoritativeDataset", None)
        registry.setdefault("datasetHistory", [])
        registry.setdefault("rulesFreezes", {})
        registry.setdefault("discoverySeeds", {})
        for batch in registry.get("batches", {}).values():
            batch.setdefault("lifecycleStatus", "active")
        for model in registry.get("models", {}).values():
            model.setdefault("datasetEligibility", "eligible")
            model.setdefault("eligibleForFutureComparison", True)
        return registry

    @staticmethod
    def _authoritative_batch_ids(registry: Mapping[str, Any]) -> tuple[str, ...]:
        dataset = registry.get("authoritativeDataset")
        if isinstance(dataset, Mapping):
            batch_ids = dataset.get("batchIds")
            if isinstance(batch_ids, list) and batch_ids and all(isinstance(value, str) for value in batch_ids):
                return tuple(batch_ids)
        legacy = registry.get("authoritativeBatchId")
        return (str(legacy),) if legacy else ()

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
        source_copedent_evidence: Sequence[str] = (),
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
        by_relative = {path.relative_to(source_path).as_posix().lower(): path for path in files}
        by_basename: dict[str, list[Path]] = {}
        for path in files:
            by_basename.setdefault(path.name.lower(), []).append(path)
        evidence_files: set[Path] = set()
        missing_evidence: list[str] = []
        for raw_name in source_copedent_evidence:
            normalized = str(raw_name).strip().replace("\\", "/").lower()
            evidence_path = by_relative.get(normalized)
            if evidence_path is None:
                candidates = by_basename.get(Path(normalized).name, [])
                if len(candidates) == 1:
                    evidence_path = candidates[0]
                elif len(candidates) > 1:
                    raise TrainingWorkflowError(f"Ambiguous source-copedent evidence filename: {raw_name}.")
            if evidence_path is None:
                missing_evidence.append(str(raw_name))
            else:
                evidence_files.add(evidence_path)
        if missing_evidence:
            raise TrainingWorkflowError(
                f"Unknown source-copedent evidence files: {', '.join(sorted(missing_evidence))}."
            )
        input_files = [path for path in files if path not in evidence_files]
        if not input_files:
            raise TrainingWorkflowError("A batch must contain at least one score/tab input besides copedent evidence.")
        inputs = [
            {
                "inputId": f"input-{index:04d}",
                "relativePath": path.relative_to(source_path).as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
                "size": path.stat().st_size,
                "mediaType": path.suffix.lower().lstrip("."),
            }
            for index, path in enumerate(input_files, start=1)
        ]
        copedent_evidence = [
            {
                "evidenceId": f"copedent-evidence-{index:04d}",
                "relativePath": path.relative_to(source_path).as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
                "size": path.stat().st_size,
                "mediaType": path.suffix.lower().lstrip("."),
            }
            for index, path in enumerate(sorted(evidence_files), start=1)
        ]
        immutable = {
            "sourceCopedentId": source_copedent_id,
            "sourceCopedentConfidence": source_copedent_confidence,
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
            "evidenceType": evidence_type,
            "inputs": inputs,
        }
        if copedent_evidence:
            immutable["sourceCopedentEvidence"] = copedent_evidence
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
            "checkpoints": {stage: {"status": "pending", "updatedAt": created_at} for stage in PIPELINE_STAGES},
            "counts": {
                "inputs": len(inputs),
                "copedentEvidence": len(copedent_evidence),
                "annotations": 0,
                "accepted": 0,
                "exceptions": 0,
            },
        }
        self._checkpoint(state, "ingest", "completed", inputCount=len(inputs), immutableDigest=digest)
        batch_dir.mkdir(parents=True, exist_ok=False)
        _write_json(manifest_path, manifest)
        _write_json(batch_dir / "state.json", state)
        rights_path = batch_dir / "rights-and-access.json"
        _write_json(rights_path, _default_rights_record(resolved_batch_id))
        _make_private(rights_path)
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

    def _rights_and_access(self, batch_id: str) -> dict[str, Any]:
        path = self._batch_dir(batch_id) / "rights-and-access.json"
        return _read_json(path) if path.exists() else _default_rights_record(batch_id)

    def _reviewed_evidence_rights_are_current(
        self,
        batch_id: str,
        pinned_digest: str,
        *,
        required_use: str,
    ) -> bool:
        """Accept reviewed evidence across non-revoking authorization revisions.

        Review records remain pinned to the authorization that existed when the
        musical evidence was approved.  A later append-only authorization may
        add another allowed use without forcing musical rereview, provided both
        the pinned record and the current record explicitly allow the use that
        consumes the evidence.  A missing lineage record, unknown rights
        status, or current revocation still fails closed.
        """

        if required_use not in USE_KEYS or not pinned_digest:
            return False
        current = self._rights_and_access(batch_id)
        if (
            current.get("reviewStatus") != "approved"
            or current.get("rightsStatus") == "unknown"
            or not bool(current.get("allowedUses", {}).get(required_use))
        ):
            return False
        history_path = self._batch_dir(batch_id) / "rights-and-access-history.jsonl"
        candidates = _read_jsonl(history_path)
        if current.get("recordDigest") and not any(
            item.get("recordDigest") == current.get("recordDigest") for item in candidates
        ):
            candidates.append(current)
        for record in candidates:
            if str(record.get("recordDigest") or "") != pinned_digest:
                continue
            return bool(
                record.get("batchId") == batch_id
                and record.get("reviewStatus") == "approved"
                and record.get("rightsStatus") != "unknown"
                and record.get("allowedUses", {}).get(required_use)
            )
        return False

    def record_use_authorization(
        self,
        batch_id: str,
        *,
        rights_status: str,
        allowed_uses: Sequence[str],
        approval_reference: str,
    ) -> dict[str, Any]:
        """Record an explicit human rights/use decision without inferring legal status."""

        self._require_active_batch(batch_id)
        normalized_status = str(rights_status).strip()
        if normalized_status not in RIGHTS_STATUSES:
            raise TrainingWorkflowError("Unsupported rights status.")
        if not approval_reference.strip():
            raise TrainingWorkflowError("Rights/use authorization requires an explicit approval reference.")
        normalized_uses = {str(value).strip() for value in allowed_uses if str(value).strip()}
        unknown_uses = sorted(normalized_uses - USE_KEYS)
        if unknown_uses:
            raise TrainingWorkflowError(f"Unsupported allowed uses: {', '.join(unknown_uses)}.")
        elevated_uses = normalized_uses - {"privateExtraction", "privateEvaluation"}
        if normalized_status == "unknown" and elevated_uses:
            raise TrainingWorkflowError(
                "Rights status cannot remain unknown when authorizing training or publication uses."
            )
        current = self._rights_and_access(batch_id)
        record = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "batchId": batch_id,
            "revision": int(current.get("revision") or 0) + 1,
            "rightsStatus": normalized_status,
            "reviewStatus": "approved",
            "allowedUses": {
                key: key in normalized_uses or key in {"privateExtraction", "privateEvaluation"}
                for key in sorted(USE_KEYS)
            },
            "approvalReference": approval_reference.strip(),
            "recordedAt": _utc_now(),
            "supersedesDigest": _sha256_json(current),
        }
        record["recordDigest"] = _sha256_json(record)
        batch_dir = self._batch_dir(batch_id)
        history_path = batch_dir / "rights-and-access-history.jsonl"
        history = _read_jsonl(history_path)
        history.append(record)
        _write_jsonl(history_path, history)
        _make_private(history_path)
        current_path = batch_dir / "rights-and-access.json"
        _write_json(current_path, record)
        _make_private(current_path)
        return {
            "batchId": batch_id,
            "rightsStatus": normalized_status,
            "reviewStatus": "approved",
            "allowedUses": record["allowedUses"],
            "recordDigest": record["recordDigest"],
        }

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
        content_unit_breaks: Sequence[str] = (),
        page_level_units: bool = False,
        semantic_groups: Path | str | None = None,
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
        if page_level_units and content_unit_breaks:
            raise TrainingWorkflowError("Use page-level units or explicit content-unit breaks, not both.")

        semantic_group_records: list[dict[str, Any]] = []
        semantic_group_digest: str | None = None
        if semantic_groups is not None:
            semantic_path = Path(semantic_groups).expanduser().resolve()
            semantic_map = _read_json(semantic_path)
            if semantic_map.get("schemaVersion") != SEMANTIC_GROUP_SCHEMA_VERSION:
                raise TrainingWorkflowError("The semantic-group map uses an unsupported schema version.")
            mapped_digest = semantic_map.get("batchImmutableDigest") or semantic_map.get("sourceImmutableDigest")
            if mapped_digest != manifest["immutableDigest"]:
                raise TrainingWorkflowError("The semantic-group map does not match this immutable batch.")
            raw_groups = semantic_map.get("groups")
            if not isinstance(raw_groups, list):
                raise TrainingWorkflowError("The semantic-group map must contain a groups list.")
            known_input_ids = {str(item["inputId"]) for item in inputs}
            seen_group_ids: set[str] = set()
            for index, raw_group in enumerate(raw_groups, start=1):
                if not isinstance(raw_group, Mapping):
                    raise TrainingWorkflowError("Every semantic group must be an object.")
                group_id = str(
                    raw_group.get("groupId") or raw_group.get("semanticGroupId") or f"semantic-group-{index:04d}"
                ).strip()
                if not group_id or group_id in seen_group_ids:
                    raise TrainingWorkflowError("Semantic group IDs must be unique and non-empty.")
                seen_group_ids.add(group_id)
                raw_input_ids = raw_group.get("inputIds")
                if not isinstance(raw_input_ids, list):
                    raise TrainingWorkflowError(f"Semantic group {group_id} needs an inputIds list.")
                input_ids = [str(value).strip() for value in raw_input_ids if str(value).strip()]
                if not input_ids or len(input_ids) != len(set(input_ids)):
                    raise TrainingWorkflowError(f"Semantic group {group_id} needs at least one unique input ID.")
                unknown = sorted(set(input_ids) - known_input_ids)
                if unknown:
                    raise TrainingWorkflowError(
                        f"Semantic group {group_id} references unknown inputs: {', '.join(unknown)}."
                    )
                semantic_group_records.append({"groupId": group_id, "inputIds": sorted(input_ids)})
            coverage = semantic_map.get("coverage")
            if isinstance(coverage, Mapping) and coverage.get("complete") is True:
                mapped_ids = [input_id for group in semantic_group_records for input_id in group["inputIds"]]
                if len(mapped_ids) != len(set(mapped_ids)):
                    raise TrainingWorkflowError("A complete semantic-group map must assign every input exactly once.")
                if set(mapped_ids) != known_input_ids:
                    raise TrainingWorkflowError("A complete semantic-group map must cover the entire immutable batch.")
            semantic_group_records.sort(key=lambda group: str(group["groupId"]))
            semantic_group_digest = _sha256_json(
                {
                    "schemaVersion": SEMANTIC_GROUP_SCHEMA_VERSION,
                    "batchImmutableDigest": manifest["immutableDigest"],
                    "groups": semantic_group_records,
                }
            )

        normalized_config = {
            "batchId": batch_id,
            "documentBreaks": sorted(str(value).lower() for value in document_breaks),
            "forcedDiscovery": sorted(str(value).lower() for value in forced_discovery),
            "contentUnitBreaks": sorted(str(value).lower() for value in content_unit_breaks),
            "pageLevelUnits": bool(page_level_units),
            "semanticGroupDigest": semantic_group_digest,
            "targets": {
                "discovery": discovery_target,
                "validation": validation_target,
                "test": test_target,
            },
            "guardRadius": guard_radius,
            "similarityThreshold": similarity_threshold,
            "algorithm": (
                "guarded-semantic-linked-units-stratified-v3"
                if semantic_group_records
                else "guarded-page-units-stratified-v2"
                if page_level_units
                else "guarded-explicit-units-stratified-v2"
                if content_unit_breaks
                else "guarded-contiguous-units-stratified-v1"
            ),
        }
        config_digest = _sha256_json(normalized_config)
        existing_summary = self._split_summary(batch_id)
        if existing_summary is not None:
            if existing_summary.get("configDigest") != config_digest:
                raise TrainingWorkflowError(
                    "The collection partition is already sealed with a different configuration."
                )
            return self.batch_status(batch_id)

        break_ids = self._resolve_input_names(inputs, document_breaks)
        forced_ids = self._resolve_input_names(inputs, forced_discovery)
        content_break_ids = self._resolve_input_names(inputs, content_unit_breaks)
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
                for candidate in range(
                    max(0, index - guard_radius), min(len(document_records), index + guard_radius + 1)
                )
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
                if current and (
                    forced != current_forced or page_level_units or str(record["inputId"]) in content_break_ids
                ):
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
        for semantic_group in semantic_group_records:
            member_units = sorted({unit_for_input[input_id] for input_id in semantic_group["inputIds"]})
            member_documents = {str(units_by_id[unit_id]["sourceDocumentId"]) for unit_id in member_units}
            for unit_id in member_units[1:]:
                union.union(member_units[0], unit_id)
            if len(member_documents) > 1:
                # Cross-publication variants are conservatively kept in discovery.
                # This avoids assigning one linked musical work to two document quotas.
                cross_document_forced.update(member_units)
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
                    near = (
                        _hamming_hex(left_metadata["dhash"], right["structuralMetadata"]["dhash"])
                        <= similarity_threshold
                    )
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
                destination["forcedDiscovery"] or unit["forcedDiscovery"] or provisional_id in cross_document_forced
            )

        content_units: list[dict[str, Any]] = []
        for unit in merged.values():
            unit["inputs"].sort(key=lambda record: str(record["inputId"]))
            member_ids = [str(record["inputId"]) for record in unit["inputs"]]
            unit["contentUnitId"] = f"content-unit-{_sha256_json(member_ids)[:12]}"
            content_units.append(unit)
        content_units.sort(key=lambda unit: str(unit["contentUnitId"]))

        document_counts = {
            document: len(document_records) for document, document_records in records_by_document.items()
        }
        test_quotas = _largest_remainder_quotas(document_counts, test_target)
        selected_test: set[str] = set()
        split_seed = seed if seed is not None else secrets.token_bytes(32)
        if len(split_seed) < 16:
            raise TrainingWorkflowError("The private partition seed must contain at least 16 bytes.")
        for document in sorted(records_by_document):
            eligible = [
                unit for unit in content_units if unit["sourceDocumentId"] == document and not unit["forcedDiscovery"]
            ]
            chosen_test = _choose_units(
                eligible,
                target=test_quotas[document],
                seed=split_seed,
                label=f"{document}:test",
            )
            selected_test.update(chosen_test)
        validation_eligible = [
            unit for unit in content_units if not unit["forcedDiscovery"] and unit["contentUnitId"] not in selected_test
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
                "test" if unit_id in selected_test else "validation" if unit_id in selected_validation else "discovery"
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
            "groupingReviewStatus": (
                "semantic_map_applied_review_pending"
                if semantic_group_records
                else "provisional_page_units"
                if page_level_units
                else "provisional_explicit_units"
                if content_unit_breaks
                else "provisional_structural"
            ),
            "stratificationStatus": {
                "sourceAndImageStructure": "completed",
                "pageTypeAndMusicalContent": "pending_independent_review",
            },
            "guardRadius": guard_radius,
            "similarityThreshold": similarity_threshold,
            "contentUnitBreakCount": len(content_break_ids),
            "pageLevelUnits": bool(page_level_units),
            "semanticGroupCount": len(semantic_group_records),
            "semanticGroupDigest": semantic_group_digest,
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
            raise TrainingWorkflowError(
                "The replacement batch must have a sealed partition before it becomes authoritative."
            )
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
        dataset = registry.get("authoritativeDataset")
        if isinstance(dataset, dict) and batch_id in dataset.get("batchIds", []):
            dataset["batchIds"] = [
                replacement_batch_id if value == batch_id else value for value in dataset["batchIds"]
            ]
            dataset["status"] = "needs_recomposition"
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

    def record_split_review(
        self,
        batch_id: str,
        *,
        outcome: str,
        partition_digest: str,
        reviewer_reference: str,
        review_artifact_digest: str | None = None,
    ) -> dict[str, Any]:
        """Bind an independent unopened-split verdict to one exact partition."""

        self._require_active_batch(batch_id)
        normalized_outcome = str(outcome).strip().lower()
        if normalized_outcome not in {"pass", "fail"}:
            raise TrainingWorkflowError("Split-review outcome must be pass or fail.")
        if not reviewer_reference.strip():
            raise TrainingWorkflowError("Split review requires an independent reviewer reference.")
        summary = self._split_summary(batch_id)
        if summary is None or summary.get("status") != "sealed_unopened":
            raise TrainingWorkflowError("Split review requires an unopened sealed partition.")
        expected_partition_digest = str(summary.get("partitionDigest") or "")
        if partition_digest != expected_partition_digest:
            raise TrainingWorkflowError("Split review does not match the sealed partition digest.")
        if review_artifact_digest is not None and not re.fullmatch(r"[0-9a-f]{64}", review_artifact_digest):
            raise TrainingWorkflowError("Split-review artifact digest must be lowercase SHA-256.")

        review_path = self._batch_dir(batch_id) / "split-review.json"
        identity = {
            "schemaVersion": SPLIT_REVIEW_SCHEMA_VERSION,
            "batchId": batch_id,
            "outcome": normalized_outcome,
            "partitionDigest": expected_partition_digest,
            "semanticGroupDigest": summary.get("semanticGroupDigest"),
            "reviewerReference": reviewer_reference.strip(),
            "reviewArtifactDigest": review_artifact_digest,
        }
        if review_path.exists():
            existing = _read_json(review_path)
            comparable = {key: existing.get(key) for key in identity}
            if comparable != identity:
                raise TrainingWorkflowError(
                    "The independent split-review record is immutable; create a replacement partition for a different verdict."
                )
            return self.batch_status(batch_id)

        reviewed_at = _utc_now()
        review_record = {
            **identity,
            "reviewedAt": reviewed_at,
        }
        review_record["reviewDigest"] = _sha256_json(review_record)
        _write_json(review_path, review_record)
        _make_private(review_path)

        updated_summary = dict(summary)
        status = f"independent_review_{'passed' if normalized_outcome == 'pass' else 'failed'}"
        updated_summary["groupingReviewStatus"] = status
        stratification = dict(updated_summary.get("stratificationStatus") or {})
        stratification["sourceAndImageStructure"] = "completed"
        stratification["pageTypeAndMusicalContent"] = status
        updated_summary["stratificationStatus"] = stratification
        updated_summary["independentReview"] = {
            "outcome": normalized_outcome,
            "partitionDigest": expected_partition_digest,
            "reviewDigest": review_record["reviewDigest"],
            "reviewedAt": reviewed_at,
        }
        _write_json(self._batch_dir(batch_id) / "partition-summary.json", updated_summary)

        registry = self._registry()
        registry["batches"][batch_id]["partitionReviewStatus"] = status
        registry["batches"][batch_id]["partitionReviewDigest"] = review_record["reviewDigest"]
        self._save_registry(registry)
        return self.batch_status(batch_id)

    def compose_authoritative_dataset(
        self,
        batch_ids: Sequence[str],
        *,
        approval_reference: str,
    ) -> dict[str, Any]:
        if not approval_reference.strip():
            raise TrainingWorkflowError("Composing an authoritative dataset requires an approval reference.")
        ordered_ids = tuple(dict.fromkeys(str(value).strip() for value in batch_ids if str(value).strip()))
        if not ordered_ids:
            raise TrainingWorkflowError("An authoritative dataset requires at least one batch.")
        if len(ordered_ids) != len(batch_ids):
            raise TrainingWorkflowError("Authoritative dataset batch IDs must be unique and non-empty.")
        registry = self._registry()
        entries: list[dict[str, Any]] = []
        for batch_id in ordered_ids:
            meta = registry["batches"].get(batch_id)
            if meta is None:
                raise TrainingWorkflowError(f"Unknown authoritative batch: {batch_id}.")
            if meta.get("lifecycleStatus", "active") != "active":
                raise TrainingWorkflowError(f"Authoritative batch is not active: {batch_id}.")
            summary = self._split_summary(batch_id)
            if summary is None or summary.get("status") != "sealed_unopened":
                raise TrainingWorkflowError(f"Authoritative batch must have an unopened sealed partition: {batch_id}.")
            if summary.get("groupingReviewStatus") != "independent_review_passed":
                raise TrainingWorkflowError(
                    f"Authoritative batch lacks a passing independent split review: {batch_id}."
                )
            manifest, _state = self._batch(batch_id)
            entries.append(
                {
                    "batchId": batch_id,
                    "immutableDigest": manifest["immutableDigest"],
                    "partitionDigest": summary["partitionDigest"],
                    "sourceCopedentId": manifest["sourceCopedentId"],
                    "sourceCopedentRevision": manifest.get("sourceCopedentRevision", 1),
                    "sourceCopedentDigest": manifest.get("sourceCopedentDigest"),
                    "counts": summary["counts"],
                }
            )
        dataset_digest = _sha256_json({"schemaVersion": TRAINING_SCHEMA_VERSION, "batches": entries})
        dataset_id = f"atd-{dataset_digest[:16]}"
        existing = registry.get("authoritativeDataset")
        if isinstance(existing, Mapping) and existing.get("datasetId") == dataset_id:
            return dict(existing)
        created_at = _utc_now()
        dataset = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "datasetId": dataset_id,
            "datasetDigest": dataset_digest,
            "status": "active",
            "createdAt": created_at,
            "approvalReference": approval_reference,
            "batchIds": list(ordered_ids),
            "batches": entries,
            "sealedTestsRemainIndependent": True,
        }
        previous_id = existing.get("datasetId") if isinstance(existing, Mapping) else None
        registry["authoritativeDataset"] = dataset
        registry["authoritativeBatchId"] = ordered_ids[0]
        registry["datasetHistory"].append(
            {
                "action": "compose",
                "fromDatasetId": previous_id,
                "toDatasetId": dataset_id,
                "batchIds": list(ordered_ids),
                "approvalReference": approval_reference,
                "at": created_at,
            }
        )
        self._save_registry(registry)
        return dataset

    def verify_batch_inputs(self, batch_id: str) -> dict[str, Any]:
        manifest, _state = self._batch(batch_id)
        source_root = Path(str(manifest["sourceRoot"]))
        failures: list[str] = []
        failed_input_ids: list[str] = []
        all_assets = [*manifest["inputs"], *manifest.get("sourceCopedentEvidence", [])]
        for item in all_assets:
            path = source_root / str(item["relativePath"])
            if not path.exists() or path.stat().st_size != int(item["size"]):
                asset_id = str(item.get("inputId") or item.get("evidenceId"))
                failures.append(asset_id)
                if item.get("inputId"):
                    failed_input_ids.append(asset_id)
                continue
            if _sha256_bytes(path.read_bytes()) != item["sha256"]:
                asset_id = str(item.get("inputId") or item.get("evidenceId"))
                failures.append(asset_id)
                if item.get("inputId"):
                    failed_input_ids.append(asset_id)
        evidence_count = len(manifest.get("sourceCopedentEvidence", []))
        return {
            "batchId": batch_id,
            "inputCount": len(manifest["inputs"]),
            "copedentEvidenceCount": evidence_count,
            "assetCount": len(all_assets),
            "verifiedCount": len(all_assets) - len(failures),
            "sourceUnchanged": not failures,
            "failedInputIds": failed_input_ids,
            "failedAssetIds": failures,
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
        partition_by_input = {str(record["inputId"]): str(record["datasetPartition"]) for record in partition_records}
        for record in records:
            decision_id = str(record.get("decisionId") or "").strip()
            if not decision_id or decision_id in decision_ids:
                raise TrainingWorkflowError("Every annotation needs a unique decisionId.")
            decision_ids.add(decision_id)
            if record.get("inputId") not in input_ids:
                raise TrainingWorkflowError(f"{decision_id} refers to an input outside batch {batch_id}.")
            if record.get("sourceCopedentId") != manifest["sourceCopedentId"]:
                raise TrainingWorkflowError(f"{decision_id} does not use the batch source copedent.")
            if int(record.get("sourceCopedentRevision") or 0) != int(manifest["sourceCopedentRevision"]):
                raise TrainingWorkflowError(f"{decision_id} does not use the batch source-copedent revision.")
            if partition_by_input:
                expected_partition = partition_by_input[str(record["inputId"])]
                if expected_partition == "test":
                    raise TrainingWorkflowError("Sealed-test inputs cannot enter the normal annotation workflow.")
                if record.get("datasetPartition") != expected_partition:
                    raise TrainingWorkflowError(f"{decision_id} must use its sealed {expected_partition} partition.")
        records_by_ledger: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            partition = str(record.get("datasetPartition") or "train")
            ledger = (
                f"annotations-{partition}.jsonl" if partition in {"discovery", "validation"} else "annotations.jsonl"
            )
            records_by_ledger.setdefault(ledger, []).append(record)
        ledger_digests: dict[str, str] = {}
        for ledger, ledger_records in sorted(records_by_ledger.items()):
            destination = self._batch_dir(batch_id) / ledger
            digest = _sha256_json(ledger_records)
            if destination.exists():
                existing = _read_jsonl(destination)
                if _sha256_json(existing) != digest:
                    raise TrainingWorkflowError(
                        f"Raw {ledger.removeprefix('annotations-').removesuffix('.jsonl')} annotations are immutable; "
                        "create a review correction instead."
                    )
            else:
                _write_jsonl(destination, ledger_records)
            ledger_digests[ledger] = digest
        all_annotations = self._annotation_records(batch_id)
        combined_digest = _sha256_json(all_annotations)
        state["counts"]["annotations"] = len(all_annotations)
        self._checkpoint(
            state,
            "annotate",
            "completed",
            annotationCount=len(all_annotations),
            annotationDigest=combined_digest,
            annotationLedgerDigests=ledger_digests,
        )
        self._save_state(batch_id, state)
        return self.batch_status(batch_id)

    def _annotation_records(self, batch_id: str) -> list[dict[str, Any]]:
        batch_dir = self._batch_dir(batch_id)
        records = [
            *_read_jsonl(batch_dir / "annotations.jsonl"),
            *_read_jsonl(batch_dir / "annotations-discovery.jsonl"),
            *_read_jsonl(batch_dir / "annotations-validation.jsonl"),
        ]
        return sorted(records, key=lambda record: str(record.get("decisionId") or ""))

    def _review_resolutions(self, batch_id: str) -> dict[str, dict[str, Any]]:
        records = _read_jsonl(self._batch_dir(batch_id) / "review-resolutions.jsonl")
        return {str(record.get("decisionId")): record for record in records if record.get("decisionId")}

    def _approved_extraction_review(
        self,
        batch_id: str,
        partition: str,
        input_id: str,
    ) -> dict[str, Any] | None:
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        if not extraction_root.exists():
            return None
        index_path = extraction_root / "review" / "approved-record-index.jsonl"
        index = {str(item.get("inputId")): item for item in _read_jsonl(index_path) if item.get("inputId")}
        item = index.get(input_id)
        if not item or item.get("status") != "human_approved":
            raise TrainingWorkflowError(f"{input_id} lacks an approved {partition} extraction revision.")
        reviewed_path_value = str(item.get("reviewedRecordPath") or "")
        expected_digest = str(item.get("reviewedRecordDigest") or "")
        if not reviewed_path_value or not expected_digest:
            raise TrainingWorkflowError(f"{input_id} has an incomplete extraction review index entry.")
        reviewed_path = extraction_root / reviewed_path_value
        if not reviewed_path.exists() or _sha256_json(_read_json(reviewed_path)) != expected_digest:
            raise TrainingWorkflowError(f"{input_id} extraction review digest does not match its approved record.")
        return dict(item)

    def _approved_score_audit(
        self,
        batch_id: str,
        partition: str,
        input_id: str,
        reviewed_record_digest: str,
    ) -> dict[str, Any]:
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        index_path = extraction_root / "review" / "score-audit" / "approved-score-index.jsonl"
        if not index_path.exists():
            raise TrainingWorkflowError(
                f"{input_id} has score evidence but no explicit per-system music-score audit."
            )
        index = {
            str(item.get("inputId") or ""): item
            for item in _read_jsonl(index_path)
            if item.get("status") == "human_approved"
        }
        item = index.get(input_id)
        if item is None or str(item.get("reviewedRecordDigest") or "") != reviewed_record_digest:
            raise TrainingWorkflowError(
                f"{input_id} lacks a current explicit per-system music-score audit."
            )
        if (
            item.get("pitchToTabTrainingEligible") is not True
            or item.get("scoreRhythmTrainingEligible") is not False
        ):
            raise TrainingWorkflowError(
                f"{input_id} lacks an explicit pitch-only score-audit scope."
            )
        return dict(item)

    def _approved_combined_line_review(
        self,
        batch_id: str,
        partition: str,
        input_id: str,
        decision_id: str,
        reviewed_record_digest: str,
    ) -> dict[str, Any]:
        """Verify one line-scoped combined score/tab approval and its immutable record."""

        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        index_path = (
            extraction_root
            / "review"
            / "combined-score-tab-audit"
            / "application"
            / "approved-line-index.jsonl"
        )
        if not index_path.exists():
            raise TrainingWorkflowError(
                f"{input_id} lacks a line-scoped combined score/tab approval."
            )
        matches = [
            item
            for item in _read_jsonl(index_path)
            if str(item.get("inputId") or "") == input_id
            and str(item.get("decisionId") or "") == decision_id
        ]
        if len(matches) != 1:
            raise TrainingWorkflowError(
                f"{input_id} lacks one unique current combined score/tab decision."
            )
        item = matches[0]
        if (
            item.get("status") != "human_approved_pitch_only"
            or item.get("scorePitchTrainingEligible") is not True
            or item.get("pitchToTabTrainingEligible") is not True
            or item.get("scoreRhythmTrainingEligible") is not False
            or item.get("trainingEligible") is not True
            or item.get("tabFactsHumanApproved", True) is not True
        ):
            raise TrainingWorkflowError(
                f"{input_id} combined score/tab line is not transformation-training eligible."
            )
        expected_digest = str(item.get("reviewedRecordDigest") or "")
        reviewed_path_value = str(item.get("reviewedRecordPath") or "")
        if expected_digest != reviewed_record_digest or not reviewed_path_value:
            raise TrainingWorkflowError(
                f"{input_id} combined score/tab line targets a stale reviewed record."
            )
        reviewed_path = extraction_root / reviewed_path_value
        if not reviewed_path.exists() or _sha256_json(_read_json(reviewed_path)) != expected_digest:
            raise TrainingWorkflowError(
                f"{input_id} combined score/tab reviewed record digest does not match."
            )
        return dict(item)

    def _combined_line_decisions(
        self,
        batch_id: str,
        partition: str,
        profile: E9CopedentProfile,
    ) -> tuple[list[dict[str, Any]], int]:
        """Derive only transitions whose complete line correspondence was approved."""

        if partition != "discovery":
            return [], 0
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        index_path = (
            extraction_root
            / "review"
            / "combined-score-tab-audit"
            / "application"
            / "approved-line-index.jsonl"
        )
        if not index_path.exists():
            return [], 0
        current_by_line: dict[tuple[str, str], dict[str, Any]] = {}
        for item in _read_jsonl(index_path):
            key = (
                str(item.get("inputId") or ""),
                str(item.get("scoreSystemId") or ""),
            )
            if not all(key):
                raise TrainingWorkflowError(
                    "A combined-line index entry has incomplete line identity."
                )
            current_by_line[key] = item
        eligible_lines = [
            item
            for item in current_by_line.values()
            if item.get("status") == "human_approved_pitch_only"
            and item.get("scorePitchTrainingEligible") is True
            and item.get("pitchToTabTrainingEligible") is True
            and item.get("scoreRhythmTrainingEligible") is False
            and item.get("trainingEligible") is True
            and item.get("tabFactsHumanApproved", True) is True
        ]
        if not eligible_lines:
            return [], 0
        rights = self._rights_and_access(batch_id)
        expected_rights_digest = str(rights.get("recordDigest") or "")
        if (
            rights.get("reviewStatus") != "approved"
            or not bool(rights.get("allowedUses", {}).get("modelTraining"))
            or not expected_rights_digest
        ):
            raise TrainingWorkflowError(
                f"{batch_id} lacks current modelTraining authorization for combined-line evidence."
            )
        lines_by_record: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for line in eligible_lines:
            key = (
                str(line.get("inputId") or ""),
                str(line.get("reviewedRecordPath") or ""),
                str(line.get("reviewedRecordDigest") or ""),
            )
            if not all(key):
                raise TrainingWorkflowError("A combined-line index entry has incomplete record lineage.")
            lines_by_record.setdefault(key, []).append(line)

        from pocketsteel.amazing_tablature_decisions import derive_decision_annotations

        derived: list[dict[str, Any]] = []
        for (input_id, relative_path, record_digest), lines in sorted(lines_by_record.items()):
            record_path = extraction_root / relative_path
            if not record_path.exists():
                raise TrainingWorkflowError(f"Combined-line reviewed record is missing for {input_id}.")
            record = _read_json(record_path)
            if _sha256_json(record) != record_digest:
                raise TrainingWorkflowError(
                    f"Combined-line reviewed record digest changed for {input_id}."
                )
            if record.get("sourceCopedent", {}).get("id") != profile.id:
                raise TrainingWorkflowError("A combined-line record uses the wrong source copedent.")
            if not self._reviewed_evidence_rights_are_current(
                batch_id,
                str(
                    record.get("rightsAndAccess", {}).get("authorizationRecordDigest")
                    or ""
                ),
                required_use="modelTraining",
            ):
                raise TrainingWorkflowError(
                    f"{input_id} combined-line evidence is pinned to stale rights authorization."
                )
            line_by_alignment: dict[str, dict[str, Any]] = {}
            line_tab_event_ids: set[str] = set()
            score_by_id = {
                str(system.get("scoreSystemId") or ""): system
                for system in record.get("scoreSystems") or []
            }
            tab_by_id = {
                str(system.get("tabSystemId") or ""): system
                for system in record.get("tabSystems") or []
            }
            alignments = list(record.get("eventAlignments") or [])
            for line in lines:
                decision_id = str(line.get("decisionId") or "")
                self._approved_combined_line_review(
                    batch_id,
                    partition,
                    input_id,
                    decision_id,
                    record_digest,
                )
                score_system_id = str(line.get("scoreSystemId") or "")
                tab_system_id = str(line.get("tabSystemId") or "")
                score_system = score_by_id.get(score_system_id)
                tab_system = tab_by_id.get(tab_system_id)
                if score_system is None or tab_system is None:
                    raise TrainingWorkflowError("A combined-line system is missing from its reviewed record.")
                if str(score_system.get("combinedScoreTabDecisionId") or "") != decision_id:
                    raise TrainingWorkflowError("A combined-line score decision does not match its record.")
                score_event_ids = {
                    str(event.get("scoreEventId") or "")
                    for event in score_system.get("scoreEvents") or []
                }
                tab_event_ids = {
                    str(event.get("tabEventId") or "")
                    for event in tab_system.get("tabEvents") or []
                }
                line_tab_event_ids.update(tab_event_ids)
                relevant = [
                    alignment
                    for alignment in alignments
                    if set(str(value) for value in alignment.get("scoreEventIds") or [])
                    & score_event_ids
                    or set(str(value) for value in alignment.get("tabEventIds") or [])
                    & tab_event_ids
                ]
                if not relevant:
                    raise TrainingWorkflowError("A combined-line approval has no reviewed alignments.")
                for alignment in relevant:
                    if (
                        alignment.get("reviewState") != "human_approved"
                        or alignment.get("pitchToTabTrainingEligible") is not True
                        or alignment.get("scoreRhythmTrainingEligible") is not False
                        or str(alignment.get("combinedScoreTabDecisionId") or "") != decision_id
                    ):
                        raise TrainingWorkflowError(
                            "A combined-line alignment lacks its exact pitch-only approval scope."
                        )
                    line_by_alignment[str(alignment.get("eventAlignmentId") or "")] = line
            for proposal in derive_decision_annotations(record, profile):
                support = proposal.get("scoreToTabSupport") or {}
                support_alignment_ids = {
                    str((support.get(side) or {}).get("eventAlignmentId") or "")
                    for side in ("previous", "current")
                } - {""}
                if (
                    len(support_alignment_ids) != 2
                    or not support_alignment_ids.issubset(line_by_alignment)
                    or str(proposal.get("sourceTabEventId") or "") not in line_tab_event_ids
                ):
                    continue
                supporting_lines = {
                    str(line_by_alignment[alignment_id].get("decisionId") or "")
                    for alignment_id in support_alignment_ids
                }
                if len(supporting_lines) != 1:
                    raise TrainingWorkflowError(
                        "A derived transition crossed combined-review line boundaries."
                    )
                decision = dict(proposal)
                decision["reviewStatus"] = "reviewed"
                decision["reviewState"] = "human_approved"
                decision["confidence"] = 1.0
                decision["sourceCombinedScoreTabDecisionId"] = next(iter(supporting_lines))
                decision["sourceExtractionRecordDigest"] = record_digest
                decision["scoreEvidenceScope"] = {
                    "pitchToTabTrainingEligible": True,
                    "scoreRhythmTrainingEligible": False,
                }
                derived.append(decision)
        return derived, len(eligible_lines)

    def _require_complete_extraction_review(self, batch_id: str, partition: str) -> None:
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        if not extraction_root.exists():
            return
        summary_path = extraction_root / "review" / "human-review-summary.json"
        if not summary_path.exists():
            raise TrainingWorkflowError(f"{batch_id} has no completed human review for its {partition} extraction.")
        summary = _read_json(summary_path)
        if not bool(summary.get("humanApprovalComplete")) or int(summary.get("remainingPageCount") or 0) != 0:
            raise TrainingWorkflowError(f"{batch_id} {partition} extraction review is incomplete.")

    def _require_extraction_acceptance(self, batch_id: str, partition: str) -> None:
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        if not extraction_root.exists():
            return
        metrics_path = extraction_root / "review" / "review-metrics.json"
        if not metrics_path.exists():
            raise TrainingWorkflowError(f"{batch_id} has no finalized {partition} extraction-review metrics.")
        metrics = _read_json(metrics_path)
        if not bool(metrics.get("allAcceptanceCriteriaPassed")):
            raise TrainingWorkflowError(
                f"{batch_id} {partition} extraction has not passed the fixed acceptance criteria."
            )

    def _require_current_extraction_rights(self, batch_id: str, partition: str) -> None:
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        if not extraction_root.exists():
            return
        rights = self._rights_and_access(batch_id)
        expected_digest = str(rights.get("recordDigest") or "")
        required_use = "modelTraining" if partition == "discovery" else "privateEvaluation"
        if (
            rights.get("reviewStatus") != "approved"
            or rights.get("rightsStatus") == "unknown"
            or not expected_digest
            or not bool(rights.get("allowedUses", {}).get(required_use))
        ):
            raise TrainingWorkflowError(
                f"{batch_id} lacks current {required_use} authorization for its reviewed {partition} evidence."
            )
        index_path = extraction_root / "review" / "approved-record-index.jsonl"
        for item in _read_jsonl(index_path):
            if item.get("status") != "human_approved":
                continue
            reviewed_path_value = str(item.get("reviewedRecordPath") or "")
            reviewed_path = extraction_root / reviewed_path_value
            if not reviewed_path_value or not reviewed_path.exists():
                raise TrainingWorkflowError("An approved extraction record is missing.")
            reviewed_record = _read_json(reviewed_path)
            if not self._reviewed_evidence_rights_are_current(
                batch_id,
                str(
                    reviewed_record.get("rightsAndAccess", {}).get(
                        "authorizationRecordDigest"
                    )
                    or ""
                ),
                required_use=required_use,
            ):
                raise TrainingWorkflowError(
                    f"{batch_id} {partition} review is pinned to a stale rights authorization."
                )

    def derive_reviewed_decisions(self, batch_id: str, *, partition: str) -> dict[str, Any]:
        """Materialize page-approved abstract decisions into an immutable partition ledger."""

        self._require_active_batch(batch_id)
        if partition not in {"discovery", "validation"}:
            raise TrainingWorkflowError("Reviewed decisions may be derived only for discovery or validation.")
        manifest, _state = self._batch(batch_id)
        split = self._split_summary(batch_id)
        if split is None or split.get("groupingReviewStatus") != "independent_review_passed":
            raise TrainingWorkflowError("Reviewed decision derivation requires a passing independent split review.")
        self._require_complete_extraction_review(batch_id, partition)
        self._require_current_extraction_rights(batch_id, partition)
        profile = _profile_for_source(str(manifest["sourceCopedentId"]))
        extraction_root = self._batch_dir(batch_id) / "extraction" / partition
        review_dir = extraction_root / "review"
        index = _read_jsonl(review_dir / "approved-record-index.jsonl")
        decisions: list[dict[str, Any]] = []
        approved_pages = 0
        excluded_pages = 0
        for item in index:
            if item.get("status") == "excluded":
                excluded_pages += 1
                continue
            if item.get("status") != "human_approved":
                continue
            reviewed_path_value = str(item.get("reviewedRecordPath") or "")
            reviewed_digest = str(item.get("reviewedRecordDigest") or "")
            reviewed_path = extraction_root / reviewed_path_value
            if not reviewed_path_value or not reviewed_path.exists():
                raise TrainingWorkflowError("An approved extraction record is missing.")
            reviewed_record = _read_json(reviewed_path)
            if _sha256_json(reviewed_record) != reviewed_digest:
                raise TrainingWorkflowError("An approved extraction record digest no longer matches.")
            if reviewed_record.get("sourceCopedent", {}).get("id") != profile.id:
                raise TrainingWorkflowError("An approved extraction record uses the wrong source copedent.")
            score_audit: dict[str, Any] | None = None
            score_event_to_system: dict[str, str] = {}
            ineligible_score_correspondence_event_ids: set[str] = set()
            if reviewed_record.get("scoreSystems"):
                from pocketsteel.amazing_tablature_extraction import (
                    score_tab_pitch_relationship_findings,
                )

                score_audit = self._approved_score_audit(
                    batch_id,
                    partition,
                    str(item.get("inputId") or ""),
                    reviewed_digest,
                )
                score_event_to_system = {
                    str(event.get("scoreEventId") or ""): str(system.get("scoreSystemId") or "")
                    for system in reviewed_record.get("scoreSystems") or []
                    for event in system.get("scoreEvents") or []
                }
                ineligible_score_correspondence_event_ids = {
                    str(event_id)
                    for finding in score_tab_pitch_relationship_findings(reviewed_record)
                    if not bool(finding.get("eligibleForPitchToTabTraining"))
                    for event_id in finding.get("scoreEventIds") or []
                }
            approved_pages += 1
            for proposal in reviewed_record.get("derivedDecisions") or []:
                if not isinstance(proposal, Mapping):
                    continue
                decision = dict(proposal)
                if decision.get("reviewState") != "human_approved":
                    raise TrainingWorkflowError("A derived decision was not included in human page approval.")
                decision["reviewStatus"] = "reviewed"
                decision["confidence"] = 1.0
                decision["sourceExtractionReviewDecisionId"] = item.get("reviewDecisionId")
                decision["sourceExtractionRecordDigest"] = reviewed_digest
                if score_audit is not None:
                    decision["sourceScoreAuditDecisionId"] = score_audit.get("scoreAuditDecisionId")
                    decision["scoreEvidenceScope"] = {
                        "pitchToTabTrainingEligible": True,
                        "scoreRhythmTrainingEligible": False,
                    }
                    approved_systems = set(score_audit.get("approvedScoreSystemIds") or [])
                    support = decision.get("scoreToTabSupport") or {}
                    support_event_ids = {
                        str(event_id)
                        for side in ("previous", "current")
                        for event_id in (support.get(side) or {}).get("scoreEventIds") or []
                    }
                    support_systems = {
                        score_event_to_system[event_id]
                        for event_id in support_event_ids
                        if event_id in score_event_to_system
                    }
                    unsupported_system = not support_systems.issubset(approved_systems)
                    unsafe_correspondence = bool(
                        support_event_ids & ineligible_score_correspondence_event_ids
                    )
                    if support.get("mode") == "score_supported" and (
                        unsupported_system or unsafe_correspondence
                    ):
                        decision["scoreToTabSupport"] = {
                            "mode": "tab_only",
                            "reason": (
                                "score_tab_pitch_correspondence_not_exact"
                                if unsafe_correspondence
                                else "score_system_marked_not_applicable_in_explicit_audit"
                            ),
                        }
                        tags = [
                            str(tag)
                            for tag in decision.get("categoryTags") or []
                            if str(tag) != "alignment:score_supported"
                        ]
                        decision["categoryTags"] = sorted(set(tags + ["alignment:tab_only"]))
                _mechanical_validation(decision, profile)
                decisions.append(decision)
        combined_decisions, approved_combined_line_count = self._combined_line_decisions(
            batch_id,
            partition,
            profile,
        )
        existing_decision_ids = {str(item.get("decisionId") or "") for item in decisions}
        for decision in combined_decisions:
            decision_id = str(decision.get("decisionId") or "")
            if decision_id in existing_decision_ids:
                continue
            _mechanical_validation(decision, profile)
            decisions.append(decision)
            existing_decision_ids.add(decision_id)
        if not decisions:
            raise TrainingWorkflowError(
                f"No page- or line-approved abstract decisions were available for {batch_id} {partition}."
            )
        decisions.sort(key=lambda record: str(record.get("decisionId") or ""))
        if len({str(record.get("decisionId")) for record in decisions}) != len(decisions):
            raise TrainingWorkflowError("Derived decision IDs are not unique.")
        output_path = self._batch_dir(batch_id) / f"derived-annotations-{partition}.jsonl"
        decision_digest = _sha256_json(decisions)
        if output_path.exists():
            if _sha256_json(_read_jsonl(output_path)) != decision_digest:
                raise TrainingWorkflowError(f"Derived {partition} annotations are immutable after page approval.")
        else:
            _write_jsonl(output_path, decisions)
            _make_private(output_path)
        self.import_annotations(batch_id, output_path)
        validation = self.validate(batch_id)
        category_counts: dict[str, int] = {}
        style_counts: dict[str, int] = {}
        for decision in decisions:
            style = str(decision.get("styleFamily") or "auto")
            style_counts[style] = style_counts.get(style, 0) + 1
            for category in decision.get("categoryTags") or []:
                tag = str(category)
                category_counts[tag] = category_counts.get(tag, 0) + 1
        summary = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "batchId": batch_id,
            "partition": partition,
            "sourceCopedentId": profile.id,
            "sourceCopedentRevision": profile.revision,
            "approvedPageCount": approved_pages,
            "approvedCombinedLineCount": approved_combined_line_count,
            "excludedPageCount": excluded_pages,
            "decisionCount": len(decisions),
            "decisionDigest": decision_digest,
            "styleCounts": dict(sorted(style_counts.items())),
            "categoryCounts": dict(sorted(category_counts.items())),
            "blockingExceptionCount": int(validation["counts"].get("blockingExceptions") or 0),
            "sealedTestAccessed": False,
        }
        summary_path = self._batch_dir(batch_id) / f"derived-annotations-{partition}-summary.json"
        _write_json(summary_path, summary)
        _make_private(summary_path)
        return summary

    def apply_review(self, batch_id: str, source: Path | str) -> dict[str, Any]:
        self._require_active_batch(batch_id)
        self._batch(batch_id)
        incoming = _read_jsonl(Path(source).expanduser().resolve())
        if not incoming:
            raise TrainingWorkflowError("Review resolution input is empty.")
        existing = self._review_resolutions(batch_id)
        annotation_ids = {str(record.get("decisionId")) for record in self._annotation_records(batch_id)}
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
        annotations = self._annotation_records(batch_id)
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
                exceptions.append(
                    {"decisionId": decision_id or "missing", "kind": "duplicate_or_missing_id", "blocking": True}
                )
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
                if int(record.get("sourceCopedentRevision") or 0) != int(manifest["sourceCopedentRevision"]):
                    raise TrainingWorkflowError(
                        "sourceCopedentRevision differs from the immutable batch source copedent."
                    )
                style = _normalize_decision_style(record.get("styleFamily"))
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
                extraction_review = None
                combined_line_review = None
                if partition in {"discovery", "validation"}:
                    combined_decision_id = str(
                        record.get("sourceCombinedScoreTabDecisionId") or ""
                    )
                    if combined_decision_id:
                        combined_line_review = self._approved_combined_line_review(
                            batch_id,
                            partition,
                            str(record.get("inputId") or ""),
                            combined_decision_id,
                            str(record.get("sourceExtractionRecordDigest") or ""),
                        )
                    else:
                        extraction_review = self._approved_extraction_review(
                            batch_id,
                            partition,
                            str(record.get("inputId") or ""),
                        )
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
                        "sourceCopedentId": profile.id,
                        "sourceCopedentRevision": profile.revision,
                        "sourceCopedentDigest": _profile_digest(profile),
                        "styleFamily": style,
                        "phraseRole": str(record.get("phraseRole") or "").strip(),
                        "datasetPartition": partition,
                        "benchmarkGroup": _normalize_benchmark_group(record.get("benchmarkGroup")),
                        "categoryTags": sorted(
                            {str(value) for value in record.get("categoryTags") or [] if str(value).strip()}
                        ),
                        "reviewStatus": review_status,
                        "evidenceType": manifest["evidenceType"],
                        "evidenceWeight": evidence_weight,
                        "chosen": chosen,
                        "alternatives": alternatives,
                        "mechanicalValidation": mechanics,
                        "sourceExtractionReviewDecisionId": (
                            extraction_review.get("reviewDecisionId")
                            if extraction_review is not None
                            else combined_line_review.get("decisionId")
                            if combined_line_review is not None
                            else None
                        ),
                        "sourceExtractionRecordDigest": (
                            extraction_review.get("reviewedRecordDigest")
                            if extraction_review is not None
                            else combined_line_review.get("reviewedRecordDigest")
                            if combined_line_review is not None
                            else None
                        ),
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
        for decision_id in sorted(machine_candidates, key=lambda value: _sha256_bytes(value.encode("utf-8")))[
            :audit_count
        ]:
            if decision_id not in resolutions:
                exceptions.append({"decisionId": decision_id, "kind": "audit_sample", "blocking": False})

        accepted.sort(key=lambda record: (record["batchId"], record["decisionId"]))
        exceptions.sort(key=lambda record: (str(record.get("decisionId")), str(record.get("kind"))))
        _write_jsonl(self._batch_dir(batch_id) / "accepted-decisions.jsonl", accepted)
        _write_jsonl(self._batch_dir(batch_id) / "exceptions.jsonl", exceptions)
        blocking = sum(1 for record in exceptions if record.get("blocking"))
        state["counts"].update(
            {
                "annotations": len(annotations),
                "accepted": len(accepted),
                "exceptions": len(exceptions),
                "blockingExceptions": blocking,
            }
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

    def _discovery_seed_records_for_batch(self, batch_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Return only digest-pinned human-reviewed discovery decisions.

        Score-bearing pages are admitted exclusively through the line-scoped
        combined score/tab approval ledger. Page-level decisions are admitted
        only when the reviewed page has no conventional-score systems, which is
        the tab-only licks case. This permits an incomplete discovery partition
        without weakening the normal full-review gate.
        """

        self._require_active_batch(batch_id)
        manifest, _state = self._batch(batch_id)
        profile = _profile_for_source(str(manifest["sourceCopedentId"]))
        rights = self._rights_and_access(batch_id)
        rights_digest = str(rights.get("recordDigest") or "")
        if (
            rights.get("reviewStatus") != "approved"
            or rights.get("rightsStatus") == "unknown"
            or not bool(rights.get("allowedUses", {}).get("modelTraining"))
            or not rights_digest
        ):
            raise TrainingWorkflowError(
                f"{batch_id} lacks current modelTraining authorization for a discovery seed."
            )

        decisions, approved_line_count = self._combined_line_decisions(
            batch_id,
            "discovery",
            profile,
        )
        extraction_root = self._batch_dir(batch_id) / "extraction" / "discovery"
        approved_index_path = extraction_root / "review" / "approved-record-index.jsonl"
        approved_page_count = 0
        excluded_page_count = 0
        tab_only_page_count = 0
        quarantined_decision_count = 0
        quarantine_reasons: dict[str, int] = {}
        sequence_decisions_by_id: dict[str, dict[str, Any]] = {}
        from pocketsteel.amazing_tablature_decisions import derive_decision_annotations

        for item in _read_jsonl(approved_index_path):
            if item.get("status") == "excluded":
                excluded_page_count += 1
                continue
            if item.get("status") != "human_approved":
                continue
            approved_page_count += 1
            relative_path = str(item.get("reviewedRecordPath") or "")
            expected_digest = str(item.get("reviewedRecordDigest") or "")
            record_path = extraction_root / relative_path
            if not relative_path or not record_path.exists():
                raise TrainingWorkflowError(f"An approved discovery record is missing for {batch_id}.")
            record = _read_json(record_path)
            if _sha256_json(record) != expected_digest:
                raise TrainingWorkflowError(f"An approved discovery record digest changed for {batch_id}.")
            if record.get("sourceCopedent", {}).get("id") != profile.id:
                raise TrainingWorkflowError("An approved discovery record uses the wrong source copedent.")
            if not self._reviewed_evidence_rights_are_current(
                batch_id,
                str(
                    record.get("rightsAndAccess", {}).get("authorizationRecordDigest")
                    or ""
                ),
                required_use="modelTraining",
            ):
                raise TrainingWorkflowError(
                    f"{batch_id} discovery evidence is pinned to stale rights authorization."
                )
            page_contributed_tab_only = False
            refreshed_proposals = {
                str(value.get("decisionId") or ""): value
                for value in derive_decision_annotations(record, profile)
                if isinstance(value, Mapping) and value.get("decisionId")
            }
            sequence_decisions_by_id.update(
                {
                    decision_id: dict(value)
                    for decision_id, value in refreshed_proposals.items()
                }
            )
            combined_decision_ids = {
                str(value.get("decisionId") or "") for value in decisions
            }
            page_type = str(record.get("pageClassification", {}).get("primary") or "unknown")
            for proposal in record.get("derivedDecisions") or []:
                if not isinstance(proposal, Mapping):
                    continue
                if str(proposal.get("decisionId") or "") in combined_decision_ids:
                    continue
                support_mode = (proposal.get("scoreToTabSupport") or {}).get("mode")
                if support_mode != "tab_only" and page_type != "lick_or_fill":
                    continue
                if proposal.get("reviewState") != "human_approved":
                    raise TrainingWorkflowError(
                        "A tab-only discovery decision was not included in human page approval."
                    )
                # Page approval pins the corrected tab facts. Re-derive only
                # source-safe ranker context so newly added sequence features
                # are consistent with the approved event order.
                decision = dict(
                    refreshed_proposals.get(
                        str(proposal.get("decisionId") or ""), proposal
                    )
                )
                decision["reviewStatus"] = "reviewed"
                decision["reviewState"] = "human_approved"
                decision["confidence"] = 1.0
                decision["sourceExtractionReviewDecisionId"] = item.get("reviewDecisionId")
                decision["sourceExtractionRecordDigest"] = expected_digest
                if support_mode != "tab_only":
                    decision["scoreToTabSupport"] = {
                        "mode": "tab_only",
                        "reason": "page_tab_review_only_score_not_audited",
                    }
                    decision["categoryTags"] = sorted(
                        {
                            str(tag)
                            for tag in decision.get("categoryTags") or []
                            if str(tag) != "alignment:score_supported"
                        }
                        | {"alignment:tab_only"}
                    )
                decisions.append(decision)
                page_contributed_tab_only = True
            if page_contributed_tab_only:
                tab_only_page_count += 1

        by_id: dict[str, dict[str, Any]] = {}
        for decision in decisions:
            decision_id = str(decision.get("decisionId") or "")
            if not decision_id:
                raise TrainingWorkflowError("A discovery seed decision has no stable decisionId.")
            prior = by_id.get(decision_id)
            if prior is not None and _sha256_json(prior) != _sha256_json(decision):
                raise TrainingWorkflowError("A discovery seed contains conflicting decision revisions.")
            by_id[decision_id] = decision
            sequence_decisions_by_id[decision_id] = decision

        preference_ledger_path = (
            extraction_root
            / "review"
            / "challenger-comparison"
            / "application"
            / "preference-ledger.jsonl"
        )
        preference_ledger = _read_jsonl(preference_ledger_path)
        preference_ledger_lineage = {
            "recordCount": len(preference_ledger),
            "canonicalDigest": _sha256_json(preference_ledger),
            "fileSha256": (
                _sha256_bytes(preference_ledger_path.read_bytes())
                if preference_ledger_path.exists()
                else None
            ),
        }
        co_valid_alternatives: dict[str, set[str]] = {}
        co_valid_action_signatures: dict[
            str, set[tuple[tuple[object, ...], ...]]
        ] = {}
        for preference in preference_ledger:
            if (
                preference.get("reviewState") == "human_approved"
                and preference.get("status") == "both_valid"
            ):
                co_valid_alternatives.setdefault(
                    str(preference.get("originalDecisionId") or ""), set()
                ).add(str(preference.get("challengerCandidateDigest") or ""))
                signature = _candidate_action_signature(
                    preference.get("challengerCandidate") or {}
                )
                if signature:
                    co_valid_action_signatures.setdefault(
                        str(preference.get("originalDecisionId") or ""), set()
                    ).add(signature)

        accepted: list[dict[str, Any]] = []
        input_ids: set[str] = set()
        for decision in by_id.values():
            if decision.get("reviewStatus") not in TRAINING_REVIEW_STATUSES:
                raise TrainingWorkflowError("A discovery seed decision lacks reviewed status.")
            confidence = float(decision.get("confidence") or 0.0)
            if confidence < 0.9:
                raise TrainingWorkflowError("A discovery seed decision has insufficient reviewed confidence.")
            try:
                mechanics = _mechanical_validation(decision, profile)
                chosen = _candidate_features(decision["chosen"])
                alternatives = [_candidate_features(value) for value in decision["alternatives"]]
                neutral_digests = co_valid_alternatives.get(
                    str(decision.get("decisionId") or ""), set()
                )
                neutral_action_signatures = co_valid_action_signatures.get(
                    str(decision.get("decisionId") or ""), set()
                )
                alternatives = [
                    value
                    for raw_value, value in zip(
                        decision["alternatives"], alternatives, strict=True
                    )
                    if _sha256_json(value) not in neutral_digests
                    and _legacy_candidate_digest(raw_value) not in neutral_digests
                    and _candidate_action_signature(raw_value)
                    not in neutral_action_signatures
                ]
                if not alternatives:
                    raise TrainingWorkflowError(
                        "All alternatives for a reviewed decision were marked co-valid."
                    )
                style = _normalize_decision_style(decision.get("styleFamily"))
            except (TrainingWorkflowError, ValueError, TypeError, KeyError) as exc:
                quarantined_decision_count += 1
                reason = str(exc)
                quarantine_reasons[reason] = quarantine_reasons.get(reason, 0) + 1
                continue
            input_id = str(decision.get("inputId") or "")
            input_ids.add(input_id)
            accepted.append(
                {
                    "decisionId": str(decision["decisionId"]),
                    "batchId": batch_id,
                    "inputId": input_id,
                    "sourceCopedentId": profile.id,
                    "sourceCopedentRevision": profile.revision,
                    "sourceCopedentDigest": _profile_digest(profile),
                    "styleFamily": style,
                    "phraseRole": str(decision.get("phraseRole") or "").strip(),
                    "datasetPartition": "discovery",
                    "benchmarkGroup": _normalize_benchmark_group(decision.get("benchmarkGroup")),
                    "categoryTags": sorted(
                        {str(value) for value in decision.get("categoryTags") or [] if str(value).strip()}
                    ),
                    "reviewStatus": "reviewed",
                    "evidenceType": manifest["evidenceType"],
                    "evidenceWeight": 1.0,
                    "chosen": chosen,
                    "alternatives": alternatives,
                    "mechanicalValidation": mechanics,
                    "sourceExtractionReviewDecisionId": decision.get(
                        "sourceCombinedScoreTabDecisionId"
                    ) or decision.get("sourceExtractionReviewDecisionId"),
                    "sourceExtractionRecordDigest": decision.get("sourceExtractionRecordDigest"),
                }
            )
        for preference in preference_ledger:
            status = str(preference.get("status") or "")
            if (
                preference.get("reviewState") != "human_approved"
                or not bool(preference.get("trainingEligible"))
                or status not in {"source_preferred", "challenger_valid"}
            ):
                continue
            original_decision = sequence_decisions_by_id.get(
                str(preference.get("originalDecisionId") or "")
            ) or by_id.get(str(preference.get("originalDecisionId") or ""))
            source_raw = (
                original_decision.get("chosen")
                if isinstance(original_decision, Mapping)
                else preference.get("sourceCandidate")
            ) or {}
            challenger_raw = preference.get("challengerCandidate") or {}
            if isinstance(original_decision, Mapping):
                reviewed_signature = _candidate_action_signature(challenger_raw)
                reviewed_digest = str(
                    preference.get("challengerCandidateDigest") or ""
                )
                refreshed_match = next(
                    (
                        candidate
                        for candidate in original_decision.get("alternatives") or []
                        if (
                            reviewed_signature
                            and _candidate_action_signature(candidate)
                            == reviewed_signature
                        )
                        or (
                            reviewed_digest
                            and _legacy_candidate_digest(candidate) == reviewed_digest
                        )
                    ),
                    None,
                )
                if refreshed_match is not None:
                    challenger_raw = refreshed_match
            source_candidate = _candidate_features(source_raw)
            challenger_candidate = _candidate_features(challenger_raw)
            chosen, alternative = (
                (source_candidate, challenger_candidate)
                if status == "source_preferred"
                else (challenger_candidate, source_candidate)
            )
            input_id = str(preference.get("inputId") or "")
            input_ids.add(input_id)
            accepted.append(
                {
                    "decisionId": str(preference.get("preferenceId") or ""),
                    "batchId": batch_id,
                    "inputId": input_id,
                    "sourceCopedentId": profile.id,
                    "sourceCopedentRevision": profile.revision,
                    "sourceCopedentDigest": _profile_digest(profile),
                    "styleFamily": _normalize_decision_style(
                        preference.get("styleFamily")
                    ),
                    "phraseRole": str(preference.get("phraseRole") or ""),
                    "datasetPartition": "discovery",
                    "benchmarkGroup": _normalize_benchmark_group(
                        preference.get("benchmarkGroup")
                    ),
                    "categoryTags": sorted(
                        {
                            str(value)
                            for value in preference.get("categoryTags") or []
                            if str(value).strip()
                        }
                    ),
                    "reviewStatus": "reviewed",
                    "evidenceType": "player_feedback",
                    "evidenceWeight": float(preference.get("evidenceWeight") or 1.0),
                    "chosen": chosen,
                    "alternatives": [alternative],
                    "mechanicalValidation": dict(
                        preference.get("mechanicalValidation") or {}
                    ),
                    "sourceExtractionReviewDecisionId": preference.get("preferenceId"),
                    "sourceExtractionRecordDigest": preference.get("submissionDigest"),
                }
            )
        if not accepted:
            raise TrainingWorkflowError(f"{batch_id} has no reviewed discovery decisions for a seed.")
        accepted.sort(key=lambda item: str(item["decisionId"]))
        return accepted, {
            "batchId": batch_id,
            "decisionCount": len(accepted),
            "reviewedInputCount": len(input_ids),
            "approvedPageCount": approved_page_count,
            "excludedPageCount": excluded_page_count,
            "approvedCombinedLineCount": approved_line_count,
            "tabOnlyPageCount": tab_only_page_count,
            "quarantinedDecisionCount": quarantined_decision_count,
            "quarantineReasonCounts": dict(sorted(quarantine_reasons.items())),
            "challengerPreferenceCount": len(preference_ledger),
            "trainingPreferenceCount": sum(
                bool(item.get("trainingEligible")) for item in preference_ledger
            ),
            "coValidPreferenceCount": sum(
                item.get("status") == "both_valid" for item in preference_ledger
            ),
            "challengerPreferenceLedger": preference_ledger_lineage,
            "rightsAuthorizationDigest": rights_digest,
            "sourceCopedentId": profile.id,
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
        }

    def _discovery_completion_contract(self, batch_id: str) -> dict[str, Any]:
        """Return aggregate discovery readiness without reading held-out records."""

        manifest, _state = self._batch(batch_id)
        extraction_root = self._batch_dir(batch_id) / "extraction" / "discovery"
        review_root = extraction_root / "review"
        summary_path = review_root / "human-review-summary.json"
        approved_index_path = review_root / "approved-record-index.jsonl"
        preference_path = (
            review_root
            / "challenger-comparison"
            / "application"
            / "preference-ledger.jsonl"
        )
        summary = _read_json(summary_path) if summary_path.exists() else {}
        approved_index = _read_jsonl(approved_index_path)
        preferences = _read_jsonl(preference_path)
        reviewed_preferences = [
            item for item in preferences if item.get("reviewState") == "human_approved"
        ]
        preference_ids = [
            str(item.get("preferenceId") or "") for item in reviewed_preferences
        ]
        rights = self._rights_and_access(batch_id)
        profile = _profile_for_source(str(manifest["sourceCopedentId"]))
        rights_digest = str(rights.get("recordDigest") or "")
        rights_current = bool(
            rights.get("reviewStatus") == "approved"
            and rights.get("rightsStatus") != "unknown"
            and rights_digest
            and rights.get("allowedUses", {}).get("modelTraining")
        )
        copedent_current = bool(
            int(manifest.get("sourceCopedentRevision") or 0) == profile.revision
            and str(manifest.get("sourceCopedentDigest") or "")
            == _profile_digest(profile)
        )
        remaining = int(summary.get("remainingPageCount") or 0)
        reviewed_page_count = int(summary.get("reviewedPageCount") or 0)
        total_page_count = int(
            summary.get("totalPageCount")
            or reviewed_page_count + remaining
        )
        score_audit_complete = (
            bool(summary.get("humanApprovalComplete")) and remaining == 0
        )
        disposition_complete = bool(
            remaining == 0
            and total_page_count > 0
            and reviewed_page_count == total_page_count
        )
        return {
            "batchId": batch_id,
            "humanApprovalComplete": score_audit_complete,
            "discoveryDispositionComplete": disposition_complete,
            "scoreAuditComplete": score_audit_complete,
            "tabOnlyApprovedPageCount": int(
                summary.get("tabOnlyApprovedPageCount") or 0
            ),
            "reviewedPageCount": reviewed_page_count,
            "remainingPageCount": remaining,
            "approvedRecordCount": sum(
                item.get("status") == "human_approved" for item in approved_index
            ),
            "excludedRecordCount": sum(
                item.get("status") == "excluded" for item in approved_index
            ),
            "reviewSummary": {
                "canonicalDigest": _sha256_json(summary) if summary_path.exists() else None,
                "fileSha256": (
                    _sha256_bytes(summary_path.read_bytes())
                    if summary_path.exists()
                    else None
                ),
            },
            "approvedRecordIndex": {
                "recordCount": len(approved_index),
                "canonicalDigest": _sha256_json(approved_index),
                "fileSha256": (
                    _sha256_bytes(approved_index_path.read_bytes())
                    if approved_index_path.exists()
                    else None
                ),
            },
            "challengerPreferences": {
                "recordCount": len(preferences),
                "reviewedCount": len(reviewed_preferences),
                "trainingCount": sum(
                    bool(item.get("trainingEligible"))
                    for item in reviewed_preferences
                ),
                "coValidCount": sum(
                    item.get("status") == "both_valid"
                    for item in reviewed_preferences
                ),
                "duplicateOrMissingIdCount": len(preference_ids)
                - len({value for value in preference_ids if value}),
                "canonicalDigest": _sha256_json(preferences),
                "fileSha256": (
                    _sha256_bytes(preference_path.read_bytes())
                    if preference_path.exists()
                    else None
                ),
            },
            "rightsAuthorizationDigest": rights_digest,
            "rightsCurrentForModelTraining": rights_current,
            "sourceCopedentId": profile.id,
            "sourceCopedentRevision": profile.revision,
            "sourceCopedentDigest": _profile_digest(profile),
            "sourceCopedentCurrent": copedent_current,
        }

    def canonical_readiness(self, *, base_model_id: str | None = None) -> dict[str, Any]:
        """Report complete-discovery blockers without opening validation or test data."""

        registry = self._registry()
        authoritative_ids = self._authoritative_batch_ids(registry)
        if not authoritative_ids:
            raise TrainingWorkflowError("Canonical readiness requires an authoritative dataset.")
        cohorts = [
            self._discovery_completion_contract(batch_id)
            for batch_id in authoritative_ids
        ]
        blockers: list[str] = []
        for cohort in cohorts:
            batch_id = str(cohort["batchId"])
            if not cohort["discoveryDispositionComplete"]:
                blockers.append(
                    f"{batch_id}:discovery_remaining={cohort['remainingPageCount']}"
                )
            if not cohort["rightsCurrentForModelTraining"]:
                blockers.append(f"{batch_id}:model_training_rights_not_current")
            if not cohort["sourceCopedentCurrent"]:
                blockers.append(f"{batch_id}:source_copedent_not_current")
            if cohort["challengerPreferences"]["duplicateOrMissingIdCount"]:
                blockers.append(f"{batch_id}:preference_lineage_not_unique")
        preference_totals = {
            "reviewedCount": sum(
                int(item["challengerPreferences"]["reviewedCount"])
                for item in cohorts
            ),
            "trainingCount": sum(
                int(item["challengerPreferences"]["trainingCount"])
                for item in cohorts
            ),
            "coValidCount": sum(
                int(item["challengerPreferences"]["coValidCount"])
                for item in cohorts
            ),
        }
        expected_preferences = {
            "reviewedCount": EXPECTED_REVIEWED_PREFERENCE_COUNT,
            "trainingCount": EXPECTED_TRAINING_PREFERENCE_COUNT,
            "coValidCount": EXPECTED_COVALID_PREFERENCE_COUNT,
        }
        if preference_totals != expected_preferences:
            blockers.append("reviewed_preference_accounting_incomplete")

        base_model: dict[str, Any] | None = None
        if base_model_id:
            base_meta = registry.get("models", {}).get(base_model_id)
            if not base_meta:
                blockers.append("exact_base_model_missing")
            else:
                base_path = self.root / str(base_meta["artifact"])
                actual_sha = _sha256_bytes(base_path.read_bytes())
                expected_sha = str(base_meta.get("artifactSha256") or "")
                base_payload = _read_json(base_path)
                styles = sorted((base_payload.get("weightsByStyle") or {}).keys())
                base_model = {
                    "modelId": base_model_id,
                    "artifactSha256": actual_sha,
                    "registryArtifactSha256": expected_sha or None,
                    "artifactDigestMatches": not expected_sha or expected_sha == actual_sha,
                    "styleFamilies": styles,
                }
                if expected_sha and expected_sha != actual_sha:
                    blockers.append("exact_base_model_digest_changed")
                if styles != sorted(CANONICAL_STYLE_FAMILIES):
                    blockers.append("exact_base_model_missing_canonical_styles")
        else:
            blockers.append("exact_base_model_required")

        return {
            "schemaVersion": "amazing-tablature-canonical-readiness-v1",
            "authoritativeDatasetId": (
                registry.get("authoritativeDataset", {}).get("datasetId")
                if isinstance(registry.get("authoritativeDataset"), Mapping)
                else None
            ),
            "batchIds": list(authoritative_ids),
            "cohorts": cohorts,
            "remainingDiscoveryPageCount": sum(
                int(item["remainingPageCount"]) for item in cohorts
            ),
            "preferenceAccounting": {
                "actual": preference_totals,
                "expected": expected_preferences,
                "complete": preference_totals == expected_preferences,
            },
            "baseModel": base_model,
            "requiredStyleFamilies": list(CANONICAL_STYLE_FAMILIES),
            "readyForCompleteDiscoveryTraining": not blockers,
            "blockers": blockers,
            "validationAccessed": False,
            "sealedTestAccessed": False,
        }

    def freeze_discovery_seed(self, *, require_complete: bool = False) -> dict[str, Any]:
        """Freeze reviewed discovery evidence with explicit completion lineage."""

        registry = self._registry()
        authoritative_ids = self._authoritative_batch_ids(registry)
        if not authoritative_ids:
            raise TrainingWorkflowError("A discovery seed requires an authoritative dataset.")
        records: list[dict[str, Any]] = []
        cohorts: list[dict[str, Any]] = []
        for batch_id in authoritative_ids:
            batch_records, cohort = self._discovery_seed_records_for_batch(batch_id)
            completion = self._discovery_completion_contract(batch_id)
            cohort["reviewCompletion"] = completion
            records.extend(batch_records)
            cohorts.append(cohort)
        full_discovery_review_complete = all(
            bool(cohort["reviewCompletion"]["discoveryDispositionComplete"])
            for cohort in cohorts
        )
        full_discovery_score_audit_complete = all(
            bool(cohort["reviewCompletion"]["scoreAuditComplete"])
            for cohort in cohorts
        )
        if require_complete and not full_discovery_review_complete:
            remaining = sum(
                int(cohort["reviewCompletion"]["remainingPageCount"])
                for cohort in cohorts
            )
            raise TrainingWorkflowError(
                f"Complete-discovery training is blocked by {remaining} undispositioned discovery pages."
            )
        records.sort(key=lambda item: (str(item["batchId"]), str(item["decisionId"])))
        code_digests = _rules_code_file_digests(self.repo_root)
        dataset = registry.get("authoritativeDataset")
        seed_core = {
            "schemaVersion": DISCOVERY_SEED_SCHEMA_VERSION,
            "authoritativeDatasetId": (
                str(dataset.get("datasetId")) if isinstance(dataset, Mapping) else None
            ),
            "authoritativeDatasetDigest": (
                str(dataset.get("datasetDigest")) if isinstance(dataset, Mapping) else None
            ),
            "batchIds": list(authoritative_ids),
            "cohorts": cohorts,
            "decisionDigest": _sha256_json(records),
            "decisionCount": len(records),
            "rulesCodeDigest": _sha256_json(code_digests),
            "rulesCodeFileDigests": code_digests,
            "partition": "discovery",
            "fullDiscoveryReviewComplete": full_discovery_review_complete,
            "fullDiscoveryScoreAuditComplete": full_discovery_score_audit_complete,
            "validationAccessed": False,
            "sealedTestAccessed": False,
        }
        seed_id = f"ats-{_sha256_json(seed_core)[:16]}"
        seed = {**seed_core, "seedId": seed_id, "createdAt": _utc_now()}
        seed_dir = self.root / "discovery-seeds" / seed_id
        manifest_path = seed_dir / "manifest.json"
        records_path = seed_dir / "accepted-decisions.jsonl"
        if manifest_path.exists() or records_path.exists():
            existing = _read_json(manifest_path)
            if (
                existing.get("seedId") != seed_id
                or _sha256_json(_read_jsonl(records_path)) != seed_core["decisionDigest"]
            ):
                raise TrainingWorkflowError("A discovery seed ID collides with different reviewed evidence.")
            return existing
        seed_dir.mkdir(parents=True, exist_ok=False)
        os.chmod(seed_dir, 0o700)
        _write_jsonl(records_path, records)
        _write_json(manifest_path, seed)
        _make_private(records_path)
        _make_private(manifest_path)
        registry.setdefault("discoverySeeds", {})[seed_id] = {
            "manifest": str(manifest_path.relative_to(self.root)),
            "records": str(records_path.relative_to(self.root)),
            "decisionCount": len(records),
            "status": (
                "frozen_complete_discovery"
                if full_discovery_review_complete
                else "frozen_partial_discovery"
            ),
        }
        self._save_registry(registry)
        return seed

    def train_discovery_challenger(
        self,
        *,
        epochs: int = 20,
        learning_rate: float = 0.05,
        base_model_id: str | None = None,
        experimental_styles: Sequence[str] | None = None,
        average_weights: bool = False,
        base_weight_ratio: float = 0.0,
        complete_discovery: bool = False,
    ) -> dict[str, Any]:
        """Train the shared partial- or complete-discovery challenger path."""

        if epochs < 1 or learning_rate <= 0:
            raise TrainingWorkflowError("Training requires positive epochs and learning rate.")
        if not 0.0 <= base_weight_ratio <= 1.0:
            raise TrainingWorkflowError("The base weight ratio must be between zero and one.")
        if base_weight_ratio and not base_model_id:
            raise TrainingWorkflowError("Weight shrinkage requires an exact discovery baseline.")
        if complete_discovery:
            readiness = self.canonical_readiness(base_model_id=base_model_id)
            if not readiness["readyForCompleteDiscoveryTraining"]:
                raise TrainingWorkflowError(
                    "Complete-discovery training is not ready: "
                    + ", ".join(readiness["blockers"])
                    + "."
                )
            if not 0.0 < base_weight_ratio < 1.0:
                raise TrainingWorkflowError(
                    "Complete-discovery training must initialize from and update the exact baseline."
                )
        seed = self.freeze_discovery_seed(require_complete=complete_discovery)
        seed_id = str(seed["seedId"])
        seed_dir = self.root / "discovery-seeds" / seed_id
        seed_manifest_path = seed_dir / "manifest.json"
        seed_records_path = seed_dir / "accepted-decisions.jsonl"
        records = _read_jsonl(seed_records_path)
        trainer_records = [self._trainer_record(record) for record in records]
        trained = train_pairwise_ranker(
            trainer_records,
            epochs=epochs,
            learning_rate=learning_rate,
            average_weights=average_weights,
        )
        weights_by_style = {
            style: dict(weights) for style, weights in trained.weights_by_style.items()
        }
        normalized_experimental_styles = sorted(
            {_normalize_decision_style(value) for value in experimental_styles or []}
        )
        if complete_discovery:
            if normalized_experimental_styles and normalized_experimental_styles != sorted(
                CANONICAL_STYLE_FAMILIES
            ):
                raise TrainingWorkflowError(
                    "Complete-discovery training must rebuild all canonical style families."
                )
            normalized_experimental_styles = sorted(CANONICAL_STYLE_FAMILIES)
            if sorted(weights_by_style) != sorted(CANONICAL_STYLE_FAMILIES):
                raise TrainingWorkflowError(
                    "Complete reviewed discovery evidence does not cover all canonical style families."
                )
        base_model_artifact_sha256: str | None = None
        if base_model_id:
            registry = self._registry()
            base_meta = registry.get("models", {}).get(base_model_id)
            valid_base = bool(
                base_meta
                and (
                    base_meta.get("discoveryShadowOnly")
                    or base_meta.get("datasetEligibility") == "complete_discovery"
                )
            )
            if not valid_base:
                raise TrainingWorkflowError(
                    "A contextual discovery challenger needs an exact discovery baseline."
                )
            if not normalized_experimental_styles:
                raise TrainingWorkflowError(
                    "A contextual discovery challenger needs at least one experimental style."
                )
            base_model_path = self.root / str(base_meta["artifact"])
            base_model_artifact_sha256 = _sha256_bytes(base_model_path.read_bytes())
            expected_base_sha256 = str(base_meta.get("artifactSha256") or "")
            if expected_base_sha256 and base_model_artifact_sha256 != expected_base_sha256:
                raise TrainingWorkflowError("The discovery baseline artifact digest changed.")
            base_model = _read_json(base_model_path)
            base_weights = base_model.get("weightsByStyle") or {}
            if complete_discovery and sorted(base_weights) != sorted(
                CANONICAL_STYLE_FAMILIES
            ):
                raise TrainingWorkflowError(
                    "The exact discovery baseline does not contain all canonical style families."
                )
            for style in normalized_experimental_styles:
                if not base_weight_ratio:
                    continue
                trained_style = weights_by_style.get(style) or {}
                base_style = base_weights.get(style) or {}
                weights_by_style[style] = {
                    name: (
                        base_weight_ratio * float(base_style.get(name, 0.0))
                        + (1.0 - base_weight_ratio)
                        * float(trained_style.get(name, 0.0))
                    )
                    for name in trained.feature_names
                }
            for style, weights in base_weights.items():
                if style in normalized_experimental_styles:
                    continue
                weights_by_style[style] = {
                    name: float((weights or {}).get(name, 0.0))
                    for name in trained.feature_names
                }
        config = {
            "epochs": int(epochs),
            "learningRate": float(learning_rate),
            "featureSchemaVersion": FEATURE_SCHEMA_VERSION,
            "discoverySeedId": seed_id,
            "discoverySeedArtifacts": {
                "manifestSha256": _sha256_bytes(seed_manifest_path.read_bytes()),
                "acceptedDecisionsSha256": _sha256_bytes(seed_records_path.read_bytes()),
            },
            "rulesCodeDigest": seed["rulesCodeDigest"],
            "baseModelId": base_model_id,
            "baseModelArtifactSha256": base_model_artifact_sha256,
            "experimentalStyles": normalized_experimental_styles,
            "averageWeights": bool(average_weights),
            "baseWeightRatio": float(base_weight_ratio),
            "completeDiscovery": bool(complete_discovery),
        }
        dataset_hash = _sha256_json({"seedId": seed_id, "records": trainer_records})
        model_id = f"at-{_sha256_json({'datasetHash': dataset_hash, 'config': config})[:16]}"
        registry = self._registry()
        existing = registry.get("models", {}).get(model_id)
        if existing is not None:
            return _read_json(self.root / str(existing["artifact"]))
        evidence_counts: dict[str, int] = {}
        for record in records:
            evidence = str(record.get("evidenceType") or "unknown")
            evidence_counts[evidence] = evidence_counts.get(evidence, 0) + 1
        preference_accounting = {
            "reviewedCount": sum(
                int(cohort["reviewCompletion"]["challengerPreferences"]["reviewedCount"])
                for cohort in seed["cohorts"]
            ),
            "trainingCount": sum(
                int(cohort["reviewCompletion"]["challengerPreferences"]["trainingCount"])
                for cohort in seed["cohorts"]
            ),
            "coValidCount": sum(
                int(cohort["reviewCompletion"]["challengerPreferences"]["coValidCount"])
                for cohort in seed["cohorts"]
            ),
            "perCohortLedgers": {
                str(cohort["batchId"]): cohort["challengerPreferenceLedger"]
                for cohort in seed["cohorts"]
            },
        }
        authoritative_dataset = registry.get("authoritativeDataset")
        rights_digests = {
            str(cohort["batchId"]): str(cohort["rightsAuthorizationDigest"])
            for cohort in seed["cohorts"]
        }
        payload = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "modelId": model_id,
            "status": "challenger",
            "createdAt": _utc_now(),
            "parentModelId": base_model_id,
            "datasetHash": dataset_hash,
            "discoverySeedId": seed_id,
            "featureSchemaVersion": FEATURE_SCHEMA_VERSION,
            "featureNames": list(trained.feature_names),
            "weightsByStyle": weights_by_style,
            "exampleCount": trained.example_count,
            "evidenceCounts": evidence_counts,
            "trainingConfig": config,
            "sourceBatchIds": list(seed["batchIds"]),
            "authoritativeDatasetId": (
                authoritative_dataset.get("datasetId")
                if isinstance(authoritative_dataset, Mapping)
                else None
            ),
            "authoritativeDatasetDigest": (
                authoritative_dataset.get("datasetDigest")
                if isinstance(authoritative_dataset, Mapping)
                else None
            ),
            "sourceCopedentProfiles": [
                {
                    "batchId": cohort["batchId"],
                    "id": cohort["sourceCopedentId"],
                    "revision": cohort["sourceCopedentRevision"],
                    "digest": cohort["sourceCopedentDigest"],
                }
                for cohort in seed["cohorts"]
            ],
            "sourceCopedentIds": sorted(
                {str(cohort["sourceCopedentId"]) for cohort in seed["cohorts"]}
            ),
            "rightsAuthorizationDigests": rights_digests,
            "preferenceAccounting": preference_accounting,
            "codeRevision": _git_revision(self.repo_root),
            "trainingCodeFileDigests": seed["rulesCodeFileDigests"],
            "copedentNeutral": True,
            "evaluationScope": (
                "canonical_validation_candidate"
                if complete_discovery
                else "discovery_shadow_only"
            ),
            "promotionEligible": False,
            "fullDiscoveryReviewComplete": bool(complete_discovery),
            "fullDiscoveryScoreAuditComplete": bool(
                seed.get("fullDiscoveryScoreAuditComplete")
            ),
            "privacy": {"containsSourceContent": False, "containsProfileSnapshots": False},
        }
        findings = _contains_forbidden_runtime_data(payload)
        if findings:
            raise TrainingWorkflowError(f"Discovery challenger contains forbidden fields: {', '.join(findings)}.")
        artifact = self.root / "models" / f"{model_id}.json"
        _write_json(artifact, payload)
        artifact_sha256 = _sha256_bytes(artifact.read_bytes())
        registry["models"][model_id] = {
            "artifact": str(artifact.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
            "status": "challenger",
            "createdAt": payload["createdAt"],
            "datasetHash": dataset_hash,
            "sourceBatchIds": payload["sourceBatchIds"],
            "datasetEligibility": (
                "complete_discovery"
                if complete_discovery
                else "partial_discovery_seed"
            ),
            "eligibleForFutureComparison": bool(complete_discovery),
            "canonicalEvaluationEligible": bool(complete_discovery),
            "discoveryShadowOnly": not complete_discovery,
            "promotionEligible": False,
            "evaluation": None,
        }
        self._save_registry(registry)
        return payload

    def train_complete_discovery_challenger(
        self,
        *,
        base_model_id: str,
        epochs: int = 20,
        learning_rate: float = 0.05,
        average_weights: bool = False,
        base_weight_ratio: float = 0.20,
    ) -> dict[str, Any]:
        """Build a validation-eligible model through the hardened discovery trainer."""

        return self.train_discovery_challenger(
            epochs=epochs,
            learning_rate=learning_rate,
            base_model_id=base_model_id,
            experimental_styles=CANONICAL_STYLE_FAMILIES,
            average_weights=average_weights,
            base_weight_ratio=base_weight_ratio,
            complete_discovery=True,
        )

    def build_discovery_transition_decoder(self, batch_id: str) -> dict[str, Any]:
        """Build a source-cohort movement decoder from discovery only.

        The artifact is an extraction aid, not an arrangement model. It is
        deliberately trained per source cohort because an unadorned repeated
        tab state can mean either a repick or a held movement in different
        publications.
        """

        self._require_active_batch(batch_id)
        manifest, _state = self._batch(batch_id)
        rights = self._rights_and_access(batch_id)
        if (
            rights.get("reviewStatus") != "approved"
            or rights.get("rightsStatus") == "unknown"
            or not bool(rights.get("allowedUses", {}).get("modelTraining"))
        ):
            raise TrainingWorkflowError(
                f"{batch_id} lacks current modelTraining authorization."
            )
        extraction_root = self._batch_dir(batch_id) / "extraction" / "discovery"
        approved_index_path = extraction_root / "review" / "approved-record-index.jsonl"
        if not approved_index_path.exists():
            raise TrainingWorkflowError(
                f"{batch_id} has no approved discovery extraction index."
            )
        eligible_index_rows = [
            item
            for item in _read_jsonl(approved_index_path)
            if item.get("status") == "human_approved"
            and item.get("inputId")
            and item.get("reviewedRecordPath")
        ]
        eligible_input_ids = [
            str(item["inputId"]) for item in eligible_index_rows
        ]
        if len(set(eligible_input_ids)) != len(eligible_input_ids):
            raise TrainingWorkflowError(
                f"{batch_id} has duplicate approved discovery records."
            )
        approved_index = {
            str(item["inputId"]): item
            for item in eligible_index_rows
        }
        rows: list[dict[str, Any]] = []
        record_digests: list[str] = []
        for input_id, item in sorted(approved_index.items()):
            record_path = extraction_root / str(item["reviewedRecordPath"])
            if not record_path.exists():
                raise TrainingWorkflowError(
                    f"Approved discovery record is missing: {batch_id}/{input_id}."
                )
            record = _read_json(record_path)
            record_digest = _sha256_json(record)
            if record_digest != str(item.get("reviewedRecordDigest") or ""):
                raise TrainingWorkflowError(
                    f"Approved discovery record digest changed: {batch_id}/{input_id}."
                )
            rows.extend(
                transition_training_rows(
                    record,
                    source_cohort_id=batch_id,
                )
            )
            record_digests.append(record_digest)
        decoder = train_transition_decoder(
            rows,
            source_cohort_id=batch_id,
        )
        cross_validation = decoder["groupedCrossValidation"]
        automation_eligible = bool(
            decoder.get("acceptedSignatures")
            and cross_validation.get("precision", 0.0) > 0.95
            and int(cross_validation.get("falsePositiveCount") or 0) == 0
        )
        payload = {
            **decoder,
            "createdAt": _utc_now(),
            "status": (
                "source_decoder_eligible"
                if automation_eligible
                else "diagnostic_only"
            ),
            "automationEligible": automation_eligible,
            "sourceManifestDigest": str(manifest.get("immutableDigest") or ""),
            "sourceCopedentId": str(manifest.get("sourceCopedentId") or ""),
            "approvedDiscoveryRecordCount": len(approved_index),
            "approvedDiscoveryRecordSetDigest": _sha256_json(record_digests),
            "codeRevision": _git_revision(self.repo_root),
            "codeFileDigests": _rules_code_file_digests(self.repo_root),
            "privacy": {
                "containsSourceContent": False,
                "containsProfileSnapshots": False,
            },
        }
        artifact_dir = self.root / "source-transition-decoders"
        artifact_path = artifact_dir / f"{decoder['decoderId']}.json"
        _write_json(artifact_path, payload)
        artifact_sha256 = _sha256_bytes(artifact_path.read_bytes())
        registry = self._registry()
        registry.setdefault("sourceTransitionDecoders", {})[decoder["decoderId"]] = {
            "artifact": str(artifact_path.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
            "sourceBatchId": batch_id,
            "status": payload["status"],
            "createdAt": payload["createdAt"],
            "automationEligible": automation_eligible,
            "validationDataUsed": False,
            "sealedTestDataUsed": False,
        }
        self._save_registry(registry)
        return {
            **payload,
            "artifact": str(artifact_path.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
        }

    def build_discovery_glyph_decoder(self, batch_id: str) -> dict[str, Any]:
        """Build a precision-first visual token decoder from approved discovery."""

        self._require_active_batch(batch_id)
        manifest, _state = self._batch(batch_id)
        rights = self._rights_and_access(batch_id)
        if (
            rights.get("reviewStatus") != "approved"
            or rights.get("rightsStatus") == "unknown"
            or not bool(rights.get("allowedUses", {}).get("modelTraining"))
        ):
            raise TrainingWorkflowError(
                f"{batch_id} lacks current modelTraining authorization."
            )
        extraction_root = self._batch_dir(batch_id) / "extraction" / "discovery"
        approved_index_path = extraction_root / "review" / "approved-record-index.jsonl"
        if not approved_index_path.exists():
            raise TrainingWorkflowError(
                f"{batch_id} has no approved discovery extraction index."
            )
        approved_index = {
            str(item.get("inputId") or ""): item
            for item in _read_jsonl(approved_index_path)
            if item.get("status") == "human_approved"
            and item.get("inputId")
            and item.get("reviewedRecordPath")
        }
        examples: list[dict[str, Any]] = []
        record_digests: list[str] = []
        source_record_digests: list[str] = []
        mapping_counts = {
            "stableTabEventId": 0,
            "explicitSourceCandidateIndex": 0,
            "reviewedBlank": 0,
            "ambiguousUnlinkedInsertion": 0,
        }
        for input_id, item in sorted(approved_index.items()):
            record_path = extraction_root / str(item["reviewedRecordPath"])
            if not record_path.exists():
                raise TrainingWorkflowError(
                    f"Approved discovery record is missing: {batch_id}/{input_id}."
                )
            record = _read_json(record_path)
            record_digest = _sha256_json(record)
            if record_digest != str(item.get("reviewedRecordDigest") or ""):
                raise TrainingWorkflowError(
                    f"Approved discovery record digest changed: {batch_id}/{input_id}."
                )
            content_unit_id = str(
                record.get("contentUnitId") or record.get("inputId") or ""
            )
            (
                _source_record,
                source_systems,
                source_record_digest,
                _source_record_path,
            ) = _source_contact_record(
                extraction_root,
                input_id,
                record,
            )
            source_record_digests.append(source_record_digest)
            for tab_system in record.get("tabSystems") or ():
                if tab_system.get("reviewState") != "human_approved":
                    continue
                source_tab_system = source_systems.get(
                    str(tab_system.get("tabSystemId") or "")
                )
                if source_tab_system is None:
                    if tab_system.get("contactSheets"):
                        raise TrainingWorkflowError(
                            "Approved contact-sheet system lacks immutable "
                            f"source lineage: {batch_id}/{input_id}."
                        )
                    continue
                (
                    truth_by_column,
                    ambiguous_columns,
                    system_mapping_counts,
                ) = _contact_sheet_truth_by_source_column(
                    source_tab_system,
                    tab_system,
                )
                for key, value in system_mapping_counts.items():
                    mapping_counts[key] += value
                for sheet in tab_system.get("contactSheets") or ():
                    labels = [
                        str(value) for value in sheet.get("labels") or ()
                    ]
                    image_path = extraction_root / str(
                        sheet.get("relativePath") or ""
                    )
                    if not labels or not image_path.exists():
                        continue
                    expected_sha256 = str(sheet.get("sha256") or "")
                    if (
                        expected_sha256
                        and _sha256_bytes(image_path.read_bytes())
                        != expected_sha256
                    ):
                        raise TrainingWorkflowError(
                            "Approved discovery contact sheet changed: "
                            f"{batch_id}/{input_id}."
                        )
                    with Image.open(image_path) as image:
                        crops = contact_sheet_token_crops(image, labels)
                    for label, crop in crops.items():
                        match = _CONTACT_SHEET_LABEL_RE.fullmatch(label)
                        if match is None:
                            continue
                        source_column = int(match.group("event"))
                        if source_column in ambiguous_columns:
                            continue
                        event = truth_by_column.get(source_column)
                        if event is None:
                            continue
                        string = int(match.group("string"))
                        actions = [
                            action
                            for action in event.get("steelActions") or ()
                            if int(action.get("string") or 0) == string
                        ]
                        if len(actions) != 1:
                            continue
                        signature = glyph_label(
                            int(actions[0].get("fret") or 0),
                            actions[0].get("controls") or (),
                        )
                        feature = glyph_feature_vector(crop)
                        if feature is not None:
                            examples.append(
                                {
                                    "contentUnitId": content_unit_id,
                                    "label": signature,
                                    "feature": feature,
                                }
                            )
            record_digests.append(record_digest)
        decoder = train_glyph_decoder(
            examples,
            source_cohort_id=batch_id,
        )
        automation_eligible = bool(decoder.get("automationEligible"))
        payload = {
            **decoder,
            "createdAt": _utc_now(),
            "status": (
                "source_decoder_eligible"
                if automation_eligible
                else "diagnostic_only"
            ),
            "sourceManifestDigest": str(manifest.get("immutableDigest") or ""),
            "sourceCopedentId": str(manifest.get("sourceCopedentId") or ""),
            "approvedDiscoveryRecordCount": len(approved_index),
            "approvedDiscoveryRecordSetDigest": _sha256_json(record_digests),
            "contactSheetTruthMappingVersion": (
                CONTACT_SHEET_TRUTH_MAPPING_VERSION
            ),
            "sourceContactRecordSetDigest": _sha256_json(
                source_record_digests
            ),
            "contactSheetTruthMapping": mapping_counts,
            "codeRevision": _git_revision(self.repo_root),
            "codeFileDigests": _rules_code_file_digests(self.repo_root),
            "privacy": {
                "containsSourceContent": False,
                "containsProfileSnapshots": False,
                "containsDerivedVisualFeatures": True,
            },
        }
        artifact_dir = self.root / "source-glyph-decoders"
        artifact_path = artifact_dir / f"{decoder['decoderId']}.json"
        _write_json(artifact_path, payload)
        artifact_sha256 = _sha256_bytes(artifact_path.read_bytes())
        registry = self._registry()
        registry.setdefault("sourceGlyphDecoders", {})[decoder["decoderId"]] = {
            "artifact": str(artifact_path.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
            "sourceBatchId": batch_id,
            "status": payload["status"],
            "createdAt": payload["createdAt"],
            "automationEligible": automation_eligible,
            "validationDataUsed": False,
            "sealedTestDataUsed": False,
        }
        self._save_registry(registry)
        return {
            **payload,
            "artifact": str(artifact_path.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
        }

    def build_discovery_reader_calibration(
        self,
        batch_id: str,
        *,
        reader_models: Sequence[str] = (
            "gemma4:12b",
            "gemma4:latest",
        ),
    ) -> dict[str, Any]:
        """Calibrate pinned cell readers against approved discovery corrections."""

        self._require_active_batch(batch_id)
        manifest, _state = self._batch(batch_id)
        rights = self._rights_and_access(batch_id)
        if (
            rights.get("reviewStatus") != "approved"
            or rights.get("rightsStatus") == "unknown"
            or not bool(rights.get("allowedUses", {}).get("modelTraining"))
        ):
            raise TrainingWorkflowError(
                f"{batch_id} lacks current modelTraining authorization."
            )
        normalized_models = tuple(
            dict.fromkeys(
                str(value).strip()
                for value in reader_models
                if str(value).strip()
            )
        )
        if len(normalized_models) < 2:
            raise TrainingWorkflowError(
                "Discovery reader calibration requires two distinct models."
            )
        from pocketsteel.amazing_tablature_extraction import (
            ExtractionWorkflowError,
            LocalTabVision,
            _render_focused_contact_sheet_chunks,
            _tab_action_sequence_from_token,
        )

        readers = [
            LocalTabVision(model, "http://127.0.0.1:11434")
            for model in normalized_models
        ]
        contracts = [reader.contract() for reader in readers]
        model_digests = [
            str(contract.get("modelDigest") or "") for contract in contracts
        ]
        if (
            any(not value for value in model_digests)
            or len(set(model_digests)) != len(model_digests)
        ):
            raise TrainingWorkflowError(
                "Discovery calibration readers need distinct pinned artifacts."
            )
        reader_ids = [
            f"{reader.model}:{str(contract['modelDigest'])[:12]}"
            for reader, contract in zip(readers, contracts, strict=True)
        ]
        extraction_root = (
            self._batch_dir(batch_id) / "extraction" / "discovery"
        )
        approved_index_path = (
            extraction_root / "review" / "approved-record-index.jsonl"
        )
        if not approved_index_path.exists():
            raise TrainingWorkflowError(
                f"{batch_id} has no approved discovery extraction index."
            )
        approved_index = {
            str(item.get("inputId") or ""): item
            for item in _read_jsonl(approved_index_path)
            if item.get("status") == "human_approved"
            and item.get("inputId")
            and item.get("reviewedRecordPath")
        }
        automation_root = (
            extraction_root
            / "review"
            / "automation"
            / "discovery-contact-reader-calibration-v1"
        )
        cache_dir = automation_root / "reader-cache"
        focused_dir = automation_root / "focused-contact-sheets"
        cache_dir.mkdir(parents=True, exist_ok=True)
        focused_dir.mkdir(parents=True, exist_ok=True)
        _make_private(automation_root, directory=True)
        _make_private(cache_dir, directory=True)
        _make_private(focused_dir, directory=True)

        def read_cells(
            reader: LocalTabVision,
            reader_id: str,
            contract: Mapping[str, Any],
            image_path: Path,
            labels: Sequence[str],
            *,
            input_mode: str,
        ) -> tuple[dict[str, dict[str, Any]], str]:
            image_sha256 = _sha256_bytes(image_path.read_bytes())
            cache_core = {
                "imageSha256": image_sha256,
                "labels": list(labels),
                "readerContract": contract,
            }
            cache_key = _sha256_json(
                {
                    **cache_core,
                    "readerInputMode": input_mode,
                }
            )
            cache_path = cache_dir / f"{cache_key}.json"
            # Before input modes were part of the calibration contract, clean
            # full-sheet reads were cached by the same immutable image,
            # labels, and reader artifact. Retain exact reuse for those
            # full-sheet caches only; focused views always use the new
            # input-mode-qualified key.
            legacy_cache_path = cache_dir / (
                f"{_sha256_json(cache_core)}.json"
            )
            cache_candidates = [cache_path]
            if (
                input_mode == READER_INPUT_MODE
                and legacy_cache_path != cache_path
            ):
                cache_candidates.append(legacy_cache_path)
            for candidate_path in cache_candidates:
                if not candidate_path.exists():
                    continue
                cached = _read_json(candidate_path)
                cached_input_mode = str(
                    cached.get("readerInputMode") or READER_INPUT_MODE
                )
                if (
                    cached_input_mode == input_mode
                    and cached.get("imageSha256") == image_sha256
                    and cached.get("labels") == list(labels)
                    and cached.get("readerContract") == dict(contract)
                    and isinstance(cached.get("cells"), Mapping)
                ):
                    # A cached readerFailure already represents two bounded
                    # attempts against this exact image, label list, and
                    # pinned reader artifact. Reuse it as an abstention rather
                    # than silently promoting it to blank evidence or
                    # repeating expensive identical inference forever.
                    return (
                        {
                            str(key): dict(value)
                            for key, value in cached["cells"].items()
                            if isinstance(value, Mapping)
                        },
                        _sha256_bytes(candidate_path.read_bytes()),
                    )
            cells: dict[str, dict[str, Any]] | None = None
            last_error: Exception | None = None
            try:
                # LocalTabVision owns the exact two-attempt retry contract.
                # Retrying that wrapper here would silently expand one
                # calibrated inference into as many as four model calls.
                cells = reader.read(image_path, labels)
            except ExtractionWorkflowError as exc:
                last_error = exc
            if cells is None:
                cells = {
                    str(label): {
                        "token": None,
                        "confidence": 0.0,
                        "uncertain": True,
                        "readerFailure": str(
                            last_error or "reader_failed"
                        )[:200],
                    }
                    for label in labels
                }
            _write_json(
                cache_path,
                {
                    "schemaVersion": (
                        "discovery-contact-reader-calibration-v1"
                    ),
                    "readerId": reader_id,
                    "readerContract": dict(contract),
                    "readerInputMode": input_mode,
                    "imageSha256": image_sha256,
                    "labels": list(labels),
                    "cells": cells,
                    "validationDataUsed": False,
                    "sealedTestDataUsed": False,
                },
            )
            _make_private(cache_path)
            return cells, _sha256_bytes(cache_path.read_bytes())

        def append_calibration_cases(
            *,
            cells: Mapping[str, Mapping[str, Any]],
            reader_id: str,
            content_unit_id: str,
            input_id: str,
            labels: Sequence[str],
            truth_by_label: Mapping[
                str,
                tuple[int, Sequence[Mapping[str, Any]]],
            ],
            input_mode: str,
        ) -> dict[str, str]:
            states_by_label: dict[str, str] = {}
            for label in labels:
                truth = truth_by_label.get(label)
                if truth is None:
                    continue
                string, truth_actions = truth
                truth_state = reader_state_signature(truth_actions)
                cell = cells.get(label) or {}
                confidence = float(cell.get("confidence") or 0.0)
                token = cell.get("token")
                predicted_state: str | None = None
                if token is None or not str(token).strip():
                    if (
                        cell.get("uncertain") is False
                        and not cell.get("readerFailure")
                        and confidence >= 0.8
                    ):
                        predicted_state = reader_state_signature(())
                elif (
                    cell.get("uncertain") is False
                    and not cell.get("readerFailure")
                    and confidence >= 0.8
                ):
                    actions, issue = _tab_action_sequence_from_token(
                        str(token),
                        string=string,
                        profile=profile,
                        confidence=confidence,
                        region_id=(
                            "discovery-reader-calibration:"
                            f"{input_id}:{input_mode}:{label}"
                        ),
                    )
                    if (
                        actions
                        and issue is None
                        and all(
                            action.get(
                                "mechanicalValidation",
                                {},
                            ).get("valid")
                            is True
                            for action in actions
                        )
                    ):
                        predicted_state = reader_state_signature(actions)
                if predicted_state is None:
                    states_by_label[label] = UNRESOLVED_READER_STATE
                    continue
                states_by_label[label] = predicted_state
                cases.append(
                    {
                        "readerId": reader_id,
                        "contentUnitId": content_unit_id,
                        "inputMode": input_mode,
                        "predictedState": predicted_state,
                        "truthState": truth_state,
                        "confidence": confidence,
                    }
                )
            return states_by_label

        def append_pair_cases(
            *,
            reader_state_maps: Sequence[Mapping[str, str]],
            content_unit_id: str,
            labels: Sequence[str],
            truth_by_label: Mapping[
                str,
                tuple[int, Sequence[Mapping[str, Any]]],
            ],
            input_mode: str,
        ) -> None:
            if len(reader_state_maps) != len(reader_ids):
                raise TrainingWorkflowError(
                    "Reader-pair calibration lacks a pinned reader result."
                )
            for label in labels:
                truth = truth_by_label.get(label)
                if truth is None:
                    continue
                _string, truth_actions = truth
                paired_cases.append(
                    {
                        "contentUnitId": content_unit_id,
                        "inputMode": input_mode,
                        "readerStates": [
                            {
                                "readerId": reader_id,
                                "state": state_map.get(
                                    label,
                                    UNRESOLVED_READER_STATE,
                                ),
                            }
                            for reader_id, state_map in zip(
                                reader_ids,
                                reader_state_maps,
                                strict=True,
                            )
                        ],
                        "truthState": reader_state_signature(
                            truth_actions
                        ),
                    }
                )

        profile = get_e9_copedent_profile(
            str(manifest.get("sourceCopedentId") or "")
        )
        cases: list[dict[str, Any]] = []
        paired_cases: list[dict[str, Any]] = []
        record_digests: list[str] = []
        source_record_digests: list[str] = []
        reader_output_digests: list[str] = []
        mapping_counts = {
            "stableTabEventId": 0,
            "explicitSourceCandidateIndex": 0,
            "reviewedBlank": 0,
            "ambiguousUnlinkedInsertion": 0,
        }
        sheet_count = 0
        label_count = 0
        focused_chunk_count = 0
        focused_label_count = 0
        eligible_truth_labels: set[tuple[str, str, str]] = set()
        for input_id, item in sorted(approved_index.items()):
            record_path = extraction_root / str(item["reviewedRecordPath"])
            if not record_path.exists():
                raise TrainingWorkflowError(
                    f"Approved discovery record is missing: {batch_id}/{input_id}."
                )
            record = _read_json(record_path)
            record_digest = _sha256_json(record)
            if record_digest != str(item.get("reviewedRecordDigest") or ""):
                raise TrainingWorkflowError(
                    f"Approved discovery record digest changed: {batch_id}/{input_id}."
                )
            if (
                record.get("datasetPartition") != "discovery"
                or str(record.get("inputId") or "") != input_id
            ):
                raise TrainingWorkflowError(
                    f"Approved discovery record lineage is invalid: {batch_id}/{input_id}."
                )
            content_unit_id = str(
                record.get("contentUnitId") or input_id
            )
            (
                _source_record,
                source_systems,
                source_record_digest,
                _source_record_path,
            ) = _source_contact_record(
                extraction_root,
                input_id,
                record,
            )
            source_record_digests.append(source_record_digest)
            for tab_system in record.get("tabSystems") or ():
                if tab_system.get("reviewState") != "human_approved":
                    continue
                source_tab_system = source_systems.get(
                    str(tab_system.get("tabSystemId") or "")
                )
                if source_tab_system is None:
                    if tab_system.get("contactSheets"):
                        raise TrainingWorkflowError(
                            "Approved contact-sheet system lacks immutable "
                            f"source lineage: {batch_id}/{input_id}."
                        )
                    continue
                (
                    truth_by_column,
                    ambiguous_columns,
                    system_mapping_counts,
                ) = _contact_sheet_truth_by_source_column(
                    source_tab_system,
                    tab_system,
                )
                for key, value in system_mapping_counts.items():
                    mapping_counts[key] += value
                system_truth_by_label: dict[
                    str,
                    tuple[int, Sequence[Mapping[str, Any]]],
                ] = {}
                for sheet in tab_system.get("contactSheets") or ():
                    labels = [
                        str(value) for value in sheet.get("labels") or ()
                    ]
                    relative_path = str(sheet.get("relativePath") or "")
                    image_path = extraction_root / relative_path
                    if not labels or not image_path.exists():
                        continue
                    image_sha256 = _sha256_bytes(image_path.read_bytes())
                    expected_sha256 = str(sheet.get("sha256") or "")
                    if (
                        expected_sha256
                        and image_sha256 != expected_sha256
                    ):
                        raise TrainingWorkflowError(
                            f"Approved contact sheet changed: {batch_id}/{input_id}."
                        )
                    sheet_count += 1
                    label_count += len(labels)
                    sheet_truth_by_label: dict[
                        str,
                        tuple[int, Sequence[Mapping[str, Any]]],
                    ] = {}
                    for label in labels:
                        match = _CONTACT_SHEET_LABEL_RE.fullmatch(label)
                        if match is None:
                            continue
                        source_column = int(match.group("event"))
                        if source_column in ambiguous_columns:
                            continue
                        string = int(match.group("string"))
                        event = truth_by_column.get(source_column)
                        truth_actions = [
                            action
                            for action in (
                                event.get("steelActions") or ()
                                if event is not None
                                else ()
                            )
                            if int(action.get("string") or 0) == string
                        ]
                        if len(truth_actions) > 1:
                            continue
                        eligible_truth_labels.add(
                            (
                                input_id,
                                str(
                                    tab_system.get("tabSystemId") or ""
                                ),
                                label,
                            )
                        )
                        truth = (string, tuple(truth_actions))
                        sheet_truth_by_label[label] = truth
                        system_truth_by_label[label] = truth
                    reader_inputs = list(
                        zip(
                            readers,
                            reader_ids,
                            contracts,
                            strict=True,
                        )
                    )
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=len(reader_inputs)
                    ) as executor:
                        futures = [
                            executor.submit(
                                read_cells,
                                reader,
                                reader_id,
                                contract,
                                image_path,
                                labels,
                                input_mode=READER_INPUT_MODE,
                            )
                            for reader, reader_id, contract in reader_inputs
                        ]
                        reader_results = [
                            future.result() for future in futures
                        ]
                    reader_state_maps: list[dict[str, str]] = []
                    for (
                        _reader,
                        reader_id,
                        _contract,
                    ), (
                        cells,
                        cache_digest,
                    ) in zip(
                        reader_inputs,
                        reader_results,
                        strict=True,
                    ):
                        reader_output_digests.append(cache_digest)
                        reader_state_maps.append(
                            append_calibration_cases(
                                cells=cells,
                                reader_id=reader_id,
                                content_unit_id=content_unit_id,
                                input_id=input_id,
                                labels=labels,
                                truth_by_label=sheet_truth_by_label,
                                input_mode=READER_INPUT_MODE,
                            )
                        )
                    append_pair_cases(
                        reader_state_maps=reader_state_maps,
                        content_unit_id=content_unit_id,
                        labels=labels,
                        truth_by_label=sheet_truth_by_label,
                        input_mode=READER_INPUT_MODE,
                    )
                if system_truth_by_label:
                    tab_system_slug = _sha256_json(
                        {
                            "inputId": input_id,
                            "tabSystemId": str(
                                tab_system.get("tabSystemId") or ""
                            ),
                        }
                    )[:16]
                    focused_path = focused_dir / (
                        f"{input_id}-{tab_system_slug}.jpg"
                    )
                    focused_chunks = _render_focused_contact_sheet_chunks(
                        output_root=extraction_root,
                        tab_system=tab_system,
                        unresolved_labels=system_truth_by_label,
                        destination=focused_path,
                    )
                    for focused_image, focused_labels in focused_chunks:
                        focused_chunk_count += 1
                        focused_label_count += len(focused_labels)
                        with concurrent.futures.ThreadPoolExecutor(
                            max_workers=len(reader_inputs)
                        ) as executor:
                            futures = [
                                executor.submit(
                                    read_cells,
                                    reader,
                                    reader_id,
                                    contract,
                                    focused_image,
                                    focused_labels,
                                    input_mode=(
                                        FOCUSED_READER_INPUT_MODE
                                    ),
                                )
                                for (
                                    reader,
                                    reader_id,
                                    contract,
                                ) in reader_inputs
                            ]
                            focused_results = [
                                future.result() for future in futures
                            ]
                        focused_state_maps: list[dict[str, str]] = []
                        for (
                            _reader,
                            reader_id,
                            _contract,
                        ), (
                            cells,
                            cache_digest,
                        ) in zip(
                            reader_inputs,
                            focused_results,
                            strict=True,
                        ):
                            reader_output_digests.append(cache_digest)
                            focused_state_maps.append(
                                append_calibration_cases(
                                    cells=cells,
                                    reader_id=reader_id,
                                    content_unit_id=content_unit_id,
                                    input_id=input_id,
                                    labels=focused_labels,
                                    truth_by_label=system_truth_by_label,
                                    input_mode=FOCUSED_READER_INPUT_MODE,
                                )
                            )
                        append_pair_cases(
                            reader_state_maps=focused_state_maps,
                            content_unit_id=content_unit_id,
                            labels=focused_labels,
                            truth_by_label=system_truth_by_label,
                            input_mode=FOCUSED_READER_INPUT_MODE,
                        )
            record_digests.append(record_digest)
        calibration = train_reader_calibration(
            cases,
            source_cohort_id=batch_id,
            reader_contracts=contracts,
            paired_cases=paired_cases,
        )
        automation_eligible = bool(
            calibration.get("automationEligible")
        )
        source_manifest_digest = str(
            manifest.get("immutableDigest") or ""
        )
        source_copedent_id = str(
            manifest.get("sourceCopedentId") or ""
        )
        approved_record_set_digest = _sha256_json(record_digests)
        reader_output_set_digest = _sha256_json(
            sorted(reader_output_digests)
        )
        code_revision = _git_revision(self.repo_root)
        code_file_digests = _rules_code_file_digests(self.repo_root)
        lineage_core = {
            "calibrationRuleDigest": str(
                calibration.get("artifactDigest") or ""
            ),
            "sourceBatchId": batch_id,
            "sourceManifestDigest": source_manifest_digest,
            "sourceCopedentId": source_copedent_id,
            "approvedDiscoveryRecordSetDigest": (
                approved_record_set_digest
            ),
            "contactSheetTruthMappingVersion": (
                CONTACT_SHEET_TRUTH_MAPPING_VERSION
            ),
            "sourceContactRecordSetDigest": _sha256_json(
                source_record_digests
            ),
            "readerOutputSetDigest": reader_output_set_digest,
            "codeRevision": code_revision,
            "codeFileDigests": code_file_digests,
        }
        lineage_digest = _sha256_json(lineage_core)
        calibration_id = f"atr-{lineage_digest[:16]}"
        payload_candidate = {
            **calibration,
            "calibrationRuleId": str(
                calibration.get("calibrationId") or ""
            ),
            "calibrationId": calibration_id,
            "lineageDigest": lineage_digest,
            "createdAt": _utc_now(),
            "status": (
                "source_reader_calibration_eligible"
                if automation_eligible
                else "diagnostic_only"
            ),
            "sourceManifestDigest": source_manifest_digest,
            "sourceCopedentId": source_copedent_id,
            "approvedDiscoveryRecordCount": len(approved_index),
            "approvedDiscoveryRecordSetDigest": (
                approved_record_set_digest
            ),
            "contactSheetTruthMappingVersion": (
                CONTACT_SHEET_TRUTH_MAPPING_VERSION
            ),
            "sourceContactRecordSetDigest": _sha256_json(
                source_record_digests
            ),
            "contactSheetTruthMapping": mapping_counts,
            "contactSheetCount": sheet_count,
            "contactLabelCount": label_count,
            "focusedContactSheetChunkCount": focused_chunk_count,
            "focusedContactLabelCount": focused_label_count,
            "eligibleTruthLabelCount": len(eligible_truth_labels),
            "readerOutputSetDigest": reader_output_set_digest,
            "codeRevision": code_revision,
            "codeFileDigests": code_file_digests,
            "privacy": {
                "containsSourceContent": False,
                "containsProfileSnapshots": False,
                "containsReaderOutput": False,
            },
        }
        artifact_dir = self.root / "source-reader-calibrations"
        artifact_path = artifact_dir / f"{calibration_id}.json"
        if artifact_path.exists():
            payload = _read_json(artifact_path)
            if (
                payload.get("calibrationId") != calibration_id
                or payload.get("lineageDigest") != lineage_digest
                or {
                    key: value
                    for key, value in payload.items()
                    if key != "createdAt"
                }
                != {
                    key: value
                    for key, value in payload_candidate.items()
                    if key != "createdAt"
                }
            ):
                raise TrainingWorkflowError(
                    "Existing source-reader calibration lineage changed."
                )
        else:
            payload = payload_candidate
            _write_json(artifact_path, payload)
            _make_private(artifact_path)
        artifact_sha256 = _sha256_bytes(artifact_path.read_bytes())
        registry = self._registry()
        registry.setdefault("sourceReaderCalibrations", {})[
            calibration_id
        ] = {
            "artifact": str(artifact_path.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
            "sourceBatchId": batch_id,
            "status": payload["status"],
            "createdAt": payload["createdAt"],
            "automationEligible": automation_eligible,
            "validationDataUsed": False,
            "sealedTestDataUsed": False,
        }
        self._save_registry(registry)
        return {
            **payload,
            "artifact": str(artifact_path.relative_to(self.root)),
            "artifactSha256": artifact_sha256,
        }

    def shadow_test_discovery(self, model_id: str, *, max_review_lines: int = 12) -> dict[str, Any]:
        """Score remaining discovery hypotheses without treating them as ground truth."""

        if max_review_lines < 1 or max_review_lines > 24:
            raise TrainingWorkflowError("Discovery shadow review selection must contain 1-24 lines.")
        registry = self._registry()
        meta = registry.get("models", {}).get(model_id)
        if not meta or meta.get("datasetEligibility") not in {
            "partial_discovery_seed",
            "complete_discovery",
        }:
            raise TrainingWorkflowError("Shadow testing requires an exact discovery challenger.")
        model_path = self.root / str(meta["artifact"])
        model_artifact_sha256 = _sha256_bytes(model_path.read_bytes())
        expected_model_sha256 = str(meta.get("artifactSha256") or "")
        if expected_model_sha256 and model_artifact_sha256 != expected_model_sha256:
            raise TrainingWorkflowError("The discovery challenger artifact digest changed.")
        model = _read_json(model_path)
        weights_by_style = model.get("weightsByStyle") or {}
        seed_id = str(model.get("discoverySeedId") or "")
        seed_dir = self.root / "discovery-seeds" / seed_id
        seed_manifest_path = seed_dir / "manifest.json"
        seed_records_path = seed_dir / "accepted-decisions.jsonl"
        seed_records = _read_jsonl(seed_records_path)
        shadow_scorer_file_digests = _rules_code_file_digests(self.repo_root)
        shadow_scorer_code_digest = _sha256_json(shadow_scorer_file_digests)
        seen_categories = {
            str(tag)
            for record in seed_records
            for tag in record.get("categoryTags") or []
        }
        from pocketsteel.amazing_tablature_decisions import derive_decision_annotations
        from pocketsteel.amazing_tablature_extraction import _score_audit_equivalence_gates

        line_rows: list[dict[str, Any]] = []
        total_pages = 0
        total_decisions = 0
        total_source_agreements = 0
        total_expert_acceptable = 0
        total_unreviewed_disagreements = 0
        total_known_preference_failures = 0
        review_ready_lines = 0
        scored_pages: set[tuple[str, str]] = set()
        preference_ledger_lineage: dict[str, dict[str, Any]] = {}
        all_preference_ids: set[str] = set()
        all_original_decision_keys: set[tuple[str, str]] = set()
        effective_snapshot_cohorts: list[dict[str, Any]] = []
        cohort_metrics: list[dict[str, Any]] = []
        rereview_suppression_reasons: dict[str, int] = {}
        suppressed_rereview_line_count = 0
        suppressed_rereview_disagreement_line_count = 0
        suppressed_rereview_disagreement_count = 0
        for batch_id in self._authoritative_batch_ids(registry):
            manifest, _state = self._batch(batch_id)
            profile = _profile_for_source(str(manifest["sourceCopedentId"]))
            extraction_root = self._batch_dir(batch_id) / "extraction" / "discovery"
            pages_dir = extraction_root / "pages"
            review_root = extraction_root / "review"
            batch_considered_pages = 0
            batch_scored_pages: set[str] = set()
            batch_line_count = 0
            batch_decision_count = 0
            batch_source_agreements = 0
            batch_expert_acceptable = 0
            batch_known_preference_failures = 0
            batch_unreviewed_disagreements = 0
            batch_exclusions: dict[str, int] = {}
            effective_records: list[dict[str, Any]] = []
            preference_ledger_path = (
                review_root
                / "challenger-comparison"
                / "application"
                / "preference-ledger.jsonl"
            )
            preference_ledger = _read_jsonl(preference_ledger_path)
            approved_preferences = [
                item
                for item in preference_ledger
                if item.get("reviewState") == "human_approved"
            ]
            preference_ids = [
                str(item.get("preferenceId") or "")
                for item in approved_preferences
            ]
            original_decision_ids = [
                str(item.get("originalDecisionId") or "")
                for item in approved_preferences
            ]
            if (
                any(not value for value in preference_ids)
                or len(set(preference_ids)) != len(preference_ids)
                or any(not value for value in original_decision_ids)
                or len(set(original_decision_ids)) != len(original_decision_ids)
            ):
                raise TrainingWorkflowError(
                    f"Discovery shadow preference lineage is missing or duplicated for {batch_id}."
                )
            if all_preference_ids.intersection(preference_ids):
                raise TrainingWorkflowError(
                    "Discovery shadow preference IDs must be unique across cohorts."
                )
            decision_keys = {(batch_id, value) for value in original_decision_ids}
            if all_original_decision_keys.intersection(decision_keys):
                raise TrainingWorkflowError(
                    "Discovery shadow original decision lineage must be unique within each cohort."
                )
            all_preference_ids.update(preference_ids)
            all_original_decision_keys.update(decision_keys)
            preference_ledger_lineage[batch_id] = {
                "recordCount": len(preference_ledger),
                "approvedRecordCount": len(approved_preferences),
                "uniquePreferenceIdCount": len(set(preference_ids)),
                "uniqueOriginalDecisionIdCount": len(set(original_decision_ids)),
                "canonicalDigest": _sha256_json(preference_ledger),
                "fileSha256": (
                    _sha256_bytes(preference_ledger_path.read_bytes())
                    if preference_ledger_path.exists()
                    else None
                ),
            }
            preferences_by_decision = {
                str(item.get("originalDecisionId") or ""): item
                for item in preference_ledger
                if item.get("reviewState") == "human_approved"
            }
            reviewed_preference_line_keys = {
                (
                    str(item.get("inputId") or ""),
                    str(item.get("scoreSystemId") or ""),
                )
                for item in preference_ledger
                if item.get("reviewState") == "human_approved"
                and item.get("inputId")
                and item.get("scoreSystemId")
            }
            reviewed_preference_decision_ids = set(preferences_by_decision)
            approved_index_path = review_root / "approved-record-index.jsonl"
            approved_index = _read_jsonl(approved_index_path)
            human_approved_inputs = {
                str(item.get("inputId") or "")
                for item in approved_index
                if item.get("status") == "human_approved"
            }
            reviewed_inputs = {str(item.get("inputId") or "") for item in approved_index}
            reviewed_record_meta_by_input = {
                str(item.get("inputId") or ""): {
                    "reviewedRecordPath": str(item.get("reviewedRecordPath") or ""),
                    "reviewedRecordDigest": str(item.get("reviewedRecordDigest") or ""),
                    "origin": "page_review",
                }
                for item in approved_index
                if item.get("status") == "human_approved"
                and item.get("reviewedRecordPath")
                and item.get("reviewedRecordDigest")
            }
            approved_lines_path = (
                review_root
                / "combined-score-tab-audit"
                / "application"
                / "approved-line-index.jsonl"
            )
            approved_lines = _read_jsonl(approved_lines_path)
            approved_line_keys = {
                (str(item.get("inputId") or ""), str(item.get("scoreSystemId") or ""))
                for item in approved_lines
                if item.get("status") == "human_approved_pitch_only"
            }
            for item in approved_lines:
                if (
                    item.get("status") == "human_approved_pitch_only"
                    and item.get("reviewedRecordPath")
                    and item.get("reviewedRecordDigest")
                ):
                    reviewed_record_meta_by_input[str(item.get("inputId") or "")] = {
                        "reviewedRecordPath": str(item.get("reviewedRecordPath") or ""),
                        "reviewedRecordDigest": str(item.get("reviewedRecordDigest") or ""),
                        "origin": "combined_line_review",
                    }
            confirmations_path = (
                review_root / "feedback-correction-confirmation-decisions.jsonl"
            )
            confirmations = _read_jsonl(confirmations_path)
            controlling_artifacts: list[dict[str, Any]] = []
            for artifact_path in (
                preference_ledger_path,
                approved_index_path,
                approved_lines_path,
                confirmations_path,
            ):
                controlling_artifacts.append(
                    {
                        "relativePath": str(artifact_path.relative_to(self.root)),
                        "exists": artifact_path.exists(),
                        "fileSha256": (
                            _sha256_bytes(artifact_path.read_bytes())
                            if artifact_path.exists()
                            else None
                        ),
                    }
                )
            confirmed_digests = {
                (str(item.get("inputId") or ""), str(item.get("machineRecordDigest") or ""))
                for item in confirmations
                if item.get("status") == "confirm"
            }
            for page_path in sorted(pages_dir.glob("*.json")):
                machine_record = _read_json(page_path)
                input_id = str(machine_record.get("inputId") or "")
                reviewed_meta = reviewed_record_meta_by_input.get(input_id)
                record_origin = "machine_page"
                record = machine_record
                effective_record_path = page_path
                if reviewed_meta is not None:
                    reviewed_path = extraction_root / str(
                        reviewed_meta["reviewedRecordPath"]
                    )
                    if not reviewed_path.exists():
                        raise TrainingWorkflowError(
                            f"The reviewed discovery record is missing for {input_id}."
                        )
                    reviewed_record = _read_json(reviewed_path)
                    if _sha256_json(reviewed_record) != str(
                        reviewed_meta["reviewedRecordDigest"]
                    ):
                        raise TrainingWorkflowError(
                            f"The reviewed discovery record digest changed for {input_id}."
                        )
                    record = reviewed_record
                    effective_record_path = reviewed_path
                    record_origin = str(reviewed_meta["origin"])
                if not record.get("scoreSystems") or not record.get("tabSystems"):
                    batch_exclusions["missing_score_or_tab_system"] = (
                        batch_exclusions.get("missing_score_or_tab_system", 0) + 1
                    )
                    continue
                page_type = str(record.get("pageClassification", {}).get("primary") or "unknown")
                source_document_id = str(record.get("sourceDocumentId") or "unknown")
                total_pages += 1
                batch_considered_pages += 1
                record_digest = _sha256_json(record)
                effective_records.append(
                    {
                        "inputId": input_id,
                        "recordOrigin": record_origin,
                        "relativePath": str(
                            effective_record_path.relative_to(self.root)
                        ),
                        "recordCanonicalDigest": record_digest,
                        "fileSha256": _sha256_bytes(
                            effective_record_path.read_bytes()
                        ),
                    }
                )
                tab_system_by_event = {
                    str(event.get("tabEventId") or ""): str(system.get("tabSystemId") or "")
                    for system in record.get("tabSystems") or []
                    for event in system.get("tabEvents") or []
                }
                score_system_by_tab = {
                    str(system.get("pairedTabSystemId") or ""): str(system.get("scoreSystemId") or "")
                    for system in record.get("scoreSystems") or []
                }
                score_gates_by_system = _score_audit_equivalence_gates(record)
                groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
                for decision in derive_decision_annotations(record, profile):
                    style = _normalize_decision_style(decision.get("styleFamily"))
                    weights = weights_by_style.get(style) or weights_by_style.get("auto")
                    candidates = [decision["chosen"], *decision["alternatives"]]
                    if weights:
                        scores = [score_candidate(candidate, weights) for candidate in candidates]
                        order = sorted(range(len(scores)), key=lambda index: (scores[index], index))
                        margin = float(scores[order[1]] - scores[order[0]]) if len(order) > 1 else 0.0
                        source_agrees = order[0] == 0
                        predicted_index = order[0]
                    else:
                        margin = 0.0
                        source_agrees = False
                        predicted_index = 0
                    decision_id = str(decision.get("decisionId") or "")
                    preference = preferences_by_decision.get(decision_id)
                    preference_status = str(
                        (preference or {}).get("status") or ""
                    )
                    predicted_features = _candidate_features(candidates[predicted_index])
                    predicted_digest = _sha256_json(predicted_features)
                    accepted_challenger_digest = str(
                        (preference or {}).get("challengerCandidateDigest") or ""
                    )
                    predicted_action_signature = _candidate_action_signature(
                        candidates[predicted_index]
                    )
                    reviewed_challenger_action_signature = _candidate_action_signature(
                        (preference or {}).get("challengerCandidate") or {}
                    )
                    preference_accepts_prediction = bool(
                        preference_status in {"both_valid", "challenger_valid"}
                        and (
                            (
                                accepted_challenger_digest
                                and (
                                    predicted_digest == accepted_challenger_digest
                                    or _legacy_candidate_digest(
                                        candidates[predicted_index]
                                    )
                                    == accepted_challenger_digest
                                )
                            )
                            or (
                                predicted_action_signature
                                and predicted_action_signature
                                == reviewed_challenger_action_signature
                            )
                        )
                    )
                    known_preference_failure = bool(
                        not source_agrees
                        and preference_status in {
                            "source_preferred",
                            "feedback",
                        }
                    )
                    expert_acceptable = bool(
                        source_agrees or preference_accepts_prediction
                    )
                    review_needed = bool(
                        not source_agrees
                        and not known_preference_failure
                        and not preference_accepts_prediction
                    )
                    tab_system_id = tab_system_by_event.get(str(decision.get("sourceTabEventId") or ""), "")
                    score_system_id = score_system_by_tab.get(tab_system_id, "")
                    if not tab_system_id or not score_system_id:
                        continue
                    groups.setdefault((score_system_id, tab_system_id), []).append(
                        {
                            "sourceAgrees": source_agrees,
                            "expertAcceptable": expert_acceptable,
                            "reviewNeeded": review_needed,
                            "preferenceStatus": preference_status or None,
                            "knownPreferenceFailure": known_preference_failure,
                            "margin": margin,
                            "confidence": float(decision.get("confidence") or 0.0),
                            "styleKnown": bool(weights),
                            "categoryTags": list(decision.get("categoryTags") or []),
                            "decisionId": decision_id,
                            "sourceTabEventId": str(decision.get("sourceTabEventId") or ""),
                            "melodyPitch": str(
                                (decision.get("abstractDecision") or {}).get("melodyPitch") or ""
                            ),
                            "sourceCandidate": dict(candidates[0]),
                            "challengerCandidate": dict(candidates[predicted_index]),
                            "sourceScore": round(float(scores[0]), 8) if weights else None,
                            "challengerScore": (
                                round(float(scores[predicted_index]), 8) if weights else None
                            ),
                        }
                    )
                for (score_system_id, tab_system_id), decisions in groups.items():
                    if not decisions:
                        continue
                    if (input_id, score_system_id) in approved_line_keys:
                        batch_exclusions["human_approved_score_line"] = (
                            batch_exclusions.get("human_approved_score_line", 0) + 1
                        )
                        continue
                    if input_id in human_approved_inputs and page_type == "lick_or_fill":
                        batch_exclusions["human_approved_tab_only_lick"] = (
                            batch_exclusions.get("human_approved_tab_only_lick", 0) + 1
                        )
                        continue
                    total_decisions += len(decisions)
                    scored_pages.add((batch_id, input_id))
                    batch_scored_pages.add(input_id)
                    batch_line_count += 1
                    batch_decision_count += len(decisions)
                    agreements = sum(bool(item["sourceAgrees"]) for item in decisions)
                    expert_acceptable_count = sum(
                        bool(item["expertAcceptable"]) for item in decisions
                    )
                    known_preference_failures = sum(
                        bool(item["knownPreferenceFailure"]) for item in decisions
                    )
                    total_source_agreements += agreements
                    total_expert_acceptable += expert_acceptable_count
                    total_known_preference_failures += known_preference_failures
                    batch_source_agreements += agreements
                    batch_expert_acceptable += expert_acceptable_count
                    batch_known_preference_failures += known_preference_failures
                    categories = {
                        str(tag)
                        for item in decisions
                        for tag in item["categoryTags"]
                    }
                    novel_categories = sorted(categories - seen_categories)
                    source_agreement = agreements / len(decisions)
                    expert_acceptable_rate = expert_acceptable_count / len(decisions)
                    min_margin = min(float(item["margin"]) for item in decisions)
                    min_confidence = min(float(item["confidence"]) for item in decisions)
                    current_decision_ids = {
                        str(item.get("decisionId") or "")
                        for item in decisions
                        if item.get("decisionId")
                    }
                    exact_reviewed_line = (
                        input_id,
                        score_system_id,
                    ) in reviewed_preference_line_keys
                    reviewed_decision_overlap = sorted(
                        current_decision_ids.intersection(
                            reviewed_preference_decision_ids
                        )
                    )
                    previously_reviewed_line = _challenger_line_previously_reviewed(
                        input_id=input_id,
                        score_system_id=score_system_id,
                        decision_ids=current_decision_ids,
                        reviewed_line_keys=reviewed_preference_line_keys,
                        reviewed_decision_ids=reviewed_preference_decision_ids,
                    )
                    suppression_basis = (
                        "exact_line"
                        if exact_reviewed_line
                        else (
                            "decision_lineage"
                            if reviewed_decision_overlap
                            else None
                        )
                    )
                    review_ready, readiness_reasons = _discovery_line_review_readiness(
                        page_human_approved=input_id in human_approved_inputs,
                        current_tab_revision_confirmed=(
                            record_origin != "machine_page"
                            or (input_id, record_digest) in confirmed_digests
                        ),
                        challenger_line_previously_reviewed=previously_reviewed_line,
                    )
                    score_gate = score_gates_by_system.get(score_system_id) or {}
                    automatic_score_audit_passed = bool(
                        score_gate.get("readyForHumanReview")
                    )
                    if not automatic_score_audit_passed:
                        review_ready = False
                        readiness_reasons = [
                            *readiness_reasons,
                            "score_line_failed_completeness_gate",
                        ]
                    challenger_disagreements = [
                        {
                            "decisionId": str(item.get("decisionId") or ""),
                            "sourceTabEventId": str(item.get("sourceTabEventId") or ""),
                            "melodyPitch": str(item.get("melodyPitch") or ""),
                            "sourceCandidate": dict(item.get("sourceCandidate") or {}),
                            "challengerCandidate": dict(
                                item.get("challengerCandidate") or {}
                            ),
                            "sourceScore": item.get("sourceScore"),
                            "challengerScore": item.get("challengerScore"),
                            "predictionMargin": round(float(item.get("margin") or 0.0), 8),
                        }
                        for item in decisions
                        if bool(item.get("reviewNeeded"))
                    ]
                    total_unreviewed_disagreements += len(challenger_disagreements)
                    batch_unreviewed_disagreements += len(challenger_disagreements)
                    if previously_reviewed_line:
                        suppressed_rereview_line_count += 1
                        if suppression_basis:
                            rereview_suppression_reasons[suppression_basis] = (
                                rereview_suppression_reasons.get(
                                    suppression_basis, 0
                                )
                                + 1
                            )
                        if challenger_disagreements:
                            suppressed_rereview_disagreement_line_count += 1
                            suppressed_rereview_disagreement_count += len(
                                challenger_disagreements
                            )
                    if not challenger_disagreements:
                        review_ready = False
                        readiness_reasons = [
                            *readiness_reasons,
                            "no_unreviewed_challenger_disagreements",
                        ]
                    if review_ready:
                        review_ready_lines += 1
                    priority = (
                        (1.0 - expert_acceptable_rate) * 100.0
                        + (0.0 if all(item["styleKnown"] for item in decisions) else 30.0)
                        + max(0.0, 20.0 - min_margin)
                        + (1.0 - min_confidence) * 20.0
                        + min(20.0, len(novel_categories) * 2.0)
                    )
                    line_rows.append(
                        {
                            "batchId": batch_id,
                            "inputId": input_id,
                            "scoreSystemId": score_system_id,
                            "tabSystemId": tab_system_id,
                            "pageType": page_type,
                            "sourceDocumentId": source_document_id,
                            "recordOrigin": record_origin,
                            "previouslyReviewedPage": input_id in reviewed_inputs,
                            "reviewReady": review_ready,
                            "reviewReadinessReasons": readiness_reasons,
                            "requiresJointScoreTabReview": not review_ready,
                            "automaticScoreAuditPassed": automatic_score_audit_passed,
                            "scoreAuditBlockingReasons": [
                                str(reason.get("code") or "")
                                for reason in score_gate.get("blockingReasons") or []
                                if reason.get("code")
                            ],
                            "decisionCount": len(decisions),
                            "extractedSourceAgreementRate": round(source_agreement, 6),
                            "expertAcceptableDecisionRate": round(
                                expert_acceptable_rate, 6
                            ),
                            "knownPreferenceFailureCount": known_preference_failures,
                            "minimumPredictionMargin": round(min_margin, 6),
                            "minimumExtractionConfidence": round(min_confidence, 6),
                            "unknownStyle": not all(item["styleKnown"] for item in decisions),
                            "novelCategoryCount": len(novel_categories),
                            "priority": round(priority, 6),
                            "challengerDisagreementCount": len(challenger_disagreements),
                            "challengerDisagreements": challenger_disagreements,
                            "rereviewSuppression": {
                                "suppressed": previously_reviewed_line,
                                "basis": suppression_basis,
                                "reviewedDecisionOverlapCount": len(
                                    reviewed_decision_overlap
                                ),
                                "currentDisagreementCount": len(
                                    challenger_disagreements
                                ),
                            },
                        }
                    )

            effective_records.sort(
                key=lambda item: (
                    str(item["inputId"]),
                    str(item["recordOrigin"]),
                    str(item["relativePath"]),
                )
            )
            controlling_artifacts.sort(
                key=lambda item: str(item["relativePath"])
            )
            effective_snapshot_cohorts.append(
                {
                    "batchId": batch_id,
                    "controllingArtifacts": controlling_artifacts,
                    "effectiveRecords": effective_records,
                }
            )
            cohort_metrics.append(
                {
                    "batchId": batch_id,
                    "consideredPageCount": batch_considered_pages,
                    "scoredPageCount": len(batch_scored_pages),
                    "lineCount": batch_line_count,
                    "decisionCount": batch_decision_count,
                    "sourceAgreementCount": batch_source_agreements,
                    "expertAcceptableCount": batch_expert_acceptable,
                    "knownPreferenceFailureCount": (
                        batch_known_preference_failures
                    ),
                    "unreviewedChallengerDisagreementCount": (
                        batch_unreviewed_disagreements
                    ),
                    "exclusionCounts": dict(sorted(batch_exclusions.items())),
                }
            )

        ranked = sorted(
            line_rows,
            key=lambda item: (
                not bool(item["reviewReady"]),
                -float(item["priority"]),
                str(item["batchId"]),
                str(item["inputId"]),
                str(item["scoreSystemId"]),
            ),
        )
        review_eligible_ranked = [
            item for item in ranked if bool(item.get("reviewReady"))
        ]
        selected: list[dict[str, Any]] = []
        selected_pages: set[tuple[str, str]] = set()
        selected_strata: dict[tuple[str, str, str], int] = {}
        for item in review_eligible_ranked:
            page_key = (str(item["batchId"]), str(item["inputId"]))
            if page_key not in selected_pages and len(selected_pages) == 10:
                continue
            stratum = (
                str(item["batchId"]),
                str(item["sourceDocumentId"]),
                str(item["pageType"]),
            )
            if selected_strata.get(stratum, 0) >= 2:
                continue
            selected.append(item)
            selected_pages.add(page_key)
            selected_strata[stratum] = selected_strata.get(stratum, 0) + 1
            if len(selected) == max_review_lines:
                break
        if len(selected) < max_review_lines:
            selected_keys = {
                (str(item["batchId"]), str(item["inputId"]), str(item["scoreSystemId"]))
                for item in selected
            }
            for item in review_eligible_ranked:
                item_key = (
                    str(item["batchId"]),
                    str(item["inputId"]),
                    str(item["scoreSystemId"]),
                )
                if item_key in selected_keys:
                    continue
                page_key = (str(item["batchId"]), str(item["inputId"]))
                if page_key not in selected_pages and len(selected_pages) == 10:
                    continue
                selected.append(item)
                selected_pages.add(page_key)
                selected_keys.add(item_key)
                if len(selected) == max_review_lines:
                    break
        shadow_dir = self.root / "discovery-shadows" / model_id
        shadow_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(shadow_dir, 0o700)
        effective_snapshot_core = {
            "schemaVersion": "amazing-tablature-discovery-shadow-snapshot-v1",
            "modelId": model_id,
            "shadowScorerCodeDigest": shadow_scorer_code_digest,
            "cohorts": effective_snapshot_cohorts,
            "validationAccessed": False,
            "sealedTestAccessed": False,
        }
        effective_snapshot_digest = _sha256_json(effective_snapshot_core)
        effective_snapshot = {
            **effective_snapshot_core,
            "snapshotDigest": effective_snapshot_digest,
        }
        effective_snapshot_path = (
            shadow_dir / f"effective-snapshot-{effective_snapshot_digest}.json"
        )
        if effective_snapshot_path.exists():
            if _read_json(effective_snapshot_path) != effective_snapshot:
                raise TrainingWorkflowError(
                    "A discovery shadow effective snapshot cannot be overwritten."
                )
        else:
            _write_json(effective_snapshot_path, effective_snapshot)

        ranked_text = _jsonl_text(ranked)
        selected_text = _jsonl_text(selected)
        ranked_sha256 = _sha256_bytes(ranked_text.encode("utf-8"))
        selected_sha256 = _sha256_bytes(selected_text.encode("utf-8"))
        ranked_canonical_digest = _sha256_json(ranked)
        selected_canonical_digest = _sha256_json(selected)
        ranked_path = shadow_dir / f"ranked-lines-{ranked_sha256}.jsonl"
        selected_path = shadow_dir / f"selected-lines-{selected_sha256}.jsonl"
        for output_path, output_text in (
            (ranked_path, ranked_text),
            (selected_path, selected_text),
        ):
            if output_path.exists():
                if output_path.read_text(encoding="utf-8") != output_text:
                    raise TrainingWorkflowError(
                        "A discovery shadow evidence artifact cannot be overwritten."
                    )
            else:
                _atomic_write_text(output_path, output_text)
                _make_private(output_path)

        report_core = {
            "schemaVersion": DISCOVERY_SHADOW_SCHEMA_VERSION,
            "modelId": model_id,
            "discoverySeedId": seed_id,
            "batchIds": list(self._authoritative_batch_ids(registry)),
            "modelArtifactSha256": model_artifact_sha256,
            "discoverySeedArtifacts": {
                "manifestSha256": _sha256_bytes(seed_manifest_path.read_bytes()),
                "acceptedDecisionsSha256": _sha256_bytes(seed_records_path.read_bytes()),
            },
            "preferenceLedgers": preference_ledger_lineage,
            "shadowScorerLineage": {
                "codeRevision": _git_revision(self.repo_root),
                "codeDigest": shadow_scorer_code_digest,
                "codeFileDigests": shadow_scorer_file_digests,
            },
            "effectiveDiscoverySnapshot": {
                "snapshotDigest": effective_snapshot_digest,
                "relativePath": str(effective_snapshot_path.relative_to(self.root)),
                "fileSha256": _sha256_bytes(effective_snapshot_path.read_bytes()),
                "cohortCount": len(effective_snapshot_cohorts),
                "effectiveRecordCount": sum(
                    len(item["effectiveRecords"])
                    for item in effective_snapshot_cohorts
                ),
            },
            "evidenceArtifacts": {
                "rankedLines": {
                    "relativePath": str(ranked_path.relative_to(self.root)),
                    "recordCount": len(ranked),
                    "canonicalDigest": ranked_canonical_digest,
                    "fileSha256": ranked_sha256,
                },
                "selectedLines": {
                    "relativePath": str(selected_path.relative_to(self.root)),
                    "recordCount": len(selected),
                    "canonicalDigest": selected_canonical_digest,
                    "fileSha256": selected_sha256,
                },
            },
            "cohortMetrics": cohort_metrics,
            "pageCount": total_pages,
            "consideredPageCount": total_pages,
            "scoredPageCount": len(scored_pages),
            "lineCount": len(line_rows),
            "decisionCount": total_decisions,
            "sourceAgreementCount": total_source_agreements,
            "expertAcceptableCount": total_expert_acceptable,
            "extractedSourceAgreementRate": (
                round(total_source_agreements / total_decisions, 6) if total_decisions else 0.0
            ),
            "expertAcceptableDecisionRate": (
                round(total_expert_acceptable / total_decisions, 6)
                if total_decisions
                else 0.0
            ),
            "unreviewedChallengerDisagreementCount": total_unreviewed_disagreements,
            "knownPreferenceFailureCount": total_known_preference_failures,
            "rereviewSuppression": {
                "suppressedLineCount": suppressed_rereview_line_count,
                "suppressedLineWithCurrentDisagreementCount": (
                    suppressed_rereview_disagreement_line_count
                ),
                "suppressedCurrentDisagreementCount": (
                    suppressed_rereview_disagreement_count
                ),
                "reasonCounts": dict(sorted(rereview_suppression_reasons.items())),
            },
            "reviewReadyLineCount": review_ready_lines,
            "withheldUnreadyLineCount": len(ranked) - len(review_eligible_ranked),
            "selectedReviewLineCount": len(selected),
            "selectedReviewPageCount": len(selected_pages),
            "maxReviewLines": max_review_lines,
            "accuracyClaimAllowed": False,
            "extractedTabIsGroundTruth": False,
            "validationAccessed": False,
            "sealedTestAccessed": False,
            "selection": selected,
        }
        report_digest = _sha256_json(report_core)
        report = {**report_core, "reportDigest": report_digest, "createdAt": _utc_now()}
        report_path = shadow_dir / f"report-{report_digest}.json"
        if report_path.exists():
            existing_report = _read_json(report_path)
            comparable_existing = {
                key: value
                for key, value in existing_report.items()
                if key != "createdAt"
            }
            comparable_report = {
                key: value for key, value in report.items() if key != "createdAt"
            }
            if comparable_existing != comparable_report:
                raise TrainingWorkflowError(
                    "A discovery shadow report cannot be overwritten."
                )
            report = existing_report
        else:
            _write_json(report_path, report)
            _make_private(report_path)
        return report

    def apply_challenger_comparison_review(
        self,
        batch_id: str,
        submission: Path | str,
        *,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Apply expert source-vs-challenger preferences to discovery evidence."""

        self._require_active_batch(batch_id)
        submission_path = Path(submission).expanduser().resolve()
        if not submission_path.exists():
            raise TrainingWorkflowError("Challenger comparison submission is missing.")
        reviews = _read_jsonl(submission_path)
        metadata_path = submission_path.with_suffix(".json")
        if not metadata_path.exists():
            raise TrainingWorkflowError("Challenger comparison submission metadata is missing.")
        metadata = _read_json(metadata_path)
        if metadata.get("status") not in {"received_not_applied", "applied"}:
            raise TrainingWorkflowError("Challenger comparison submission is not applicable.")
        packet_digest = str(metadata.get("packetDigest") or "")
        model_id = str(metadata.get("modelId") or "")
        review_dir = (
            self._batch_dir(batch_id)
            / "extraction"
            / "discovery"
            / "review"
            / "challenger-comparison"
        )
        packet_path = review_dir / f"packet-{packet_digest}.json"
        if not packet_path.exists():
            raise TrainingWorkflowError("Challenger preference packet is missing.")
        packet = _read_json(packet_path)
        if (
            str(packet.get("packetDigest") or "") != packet_digest
            or str(packet.get("batchId") or "") != batch_id
            or str(packet.get("modelId") or "") != model_id
        ):
            raise TrainingWorkflowError("Challenger preference packet lineage changed.")
        shadow_digest = str(packet.get("shadowReportDigest") or "")
        shadow_dir = (
            self.root
            / "discovery-shadows"
            / model_id
        )
        shadow_report_path = shadow_dir / f"report-{shadow_digest}.json"
        if not shadow_report_path.exists():
            raise TrainingWorkflowError("Challenger preference shadow report is missing.")
        shadow_report = _read_json(shadow_report_path)
        stored_report_digest = str(shadow_report.get("reportDigest") or "")
        computed_report_digest = _sha256_json(
            {
                key: value
                for key, value in shadow_report.items()
                if key not in {"reportDigest", "createdAt"}
            }
        )
        if stored_report_digest != shadow_digest or computed_report_digest != shadow_digest:
            raise TrainingWorkflowError("Challenger preference shadow report digest changed.")
        selected_lineage = (
            (shadow_report.get("evidenceArtifacts") or {}).get("selectedLines")
            or {}
        )
        if selected_lineage:
            selected_path = self.root / str(
                selected_lineage.get("relativePath") or ""
            )
        else:
            selected_path = shadow_dir / f"selected-lines-{shadow_digest}.jsonl"
        if not selected_path.exists():
            raise TrainingWorkflowError("Challenger preference shadow evidence is missing.")
        selected_records = _read_jsonl(selected_path)
        if selected_lineage and (
            _sha256_bytes(selected_path.read_bytes())
            != str(selected_lineage.get("fileSha256") or "")
            or _sha256_json(selected_records)
            != str(selected_lineage.get("canonicalDigest") or "")
            or len(selected_records)
            != int(selected_lineage.get("recordCount") or 0)
        ):
            raise TrainingWorkflowError(
                "Challenger preference shadow evidence digest changed."
            )
        shadow_by_decision = {
            str(disagreement.get("decisionId") or ""): {
                **dict(disagreement),
                "inputId": str(line.get("inputId") or ""),
                "scoreSystemId": str(line.get("scoreSystemId") or ""),
                "pageType": str(line.get("pageType") or "unknown"),
            }
            for line in selected_records
            if str(line.get("batchId") or "") == batch_id
            for disagreement in line.get("challengerDisagreements") or []
        }
        expected_ids = {
            str(item.get("decisionId") or "")
            for system in packet.get("systems") or []
            for item in system.get("disagreements") or []
        }
        if {str(item.get("decisionId") or "") for item in reviews} != expected_ids:
            raise TrainingWorkflowError("Challenger preference submission is incomplete or stale.")
        profile = _profile_for_source(
            str(self._batch(batch_id)[0].get("sourceCopedentId") or "")
        )

        def mechanically_validate(candidate: Mapping[str, Any]) -> dict[str, Any]:
            actions = candidate.get("mechanicalActions") or []
            if not isinstance(actions, list) or not actions:
                raise TrainingWorkflowError("Challenger preference candidate lacks tablature actions.")
            controls_by_id = profile.controls_by_id()
            seen_strings: set[int] = set()
            pitches: list[int] = []
            for action in actions:
                if not isinstance(action, Mapping):
                    raise TrainingWorkflowError("Challenger preference action must be an object.")
                string = int(action.get("string") or 0)
                fret = int(action.get("fret") if action.get("fret") is not None else -1)
                controls = [str(value) for value in action.get("controls") or []]
                if string in seen_strings or string not in profile.open_pitch_values_by_string():
                    raise TrainingWorkflowError("Challenger preference uses an invalid duplicate string.")
                if fret < 0 or fret > 36 or any(value not in controls_by_id for value in controls):
                    raise TrainingWorkflowError("Challenger preference uses an invalid fret or control.")
                expected_pitch = profile.open_pitch_values_by_string()[string] + fret + sum(
                    change.semitones
                    for control_id in controls
                    for change in controls_by_id[control_id].changes
                    if change.string == string
                )
                if expected_pitch != int(action.get("soundingPitchValue") or -999):
                    raise TrainingWorkflowError("Challenger preference action has inconsistent pitch.")
                seen_strings.add(string)
                pitches.append(expected_pitch)
            return {
                "ok": True,
                "sourceCopedentId": profile.id,
                "sourceCopedentRevision": profile.revision,
                "sourceCopedentDigest": _profile_digest(profile),
                "strings": sorted(seen_strings),
                "pitchValues": sorted(pitches),
            }

        preference_records: list[dict[str, Any]] = []
        status_counts: dict[str, int] = {}
        for review in reviews:
            decision_id = str(review.get("decisionId") or "")
            status = str(review.get("status") or "")
            shadow = shadow_by_decision.get(decision_id)
            if shadow is None:
                raise TrainingWorkflowError("Challenger preference lost its shadow decision.")
            source_candidate = dict(shadow.get("sourceCandidate") or {})
            challenger_candidate = dict(shadow.get("challengerCandidate") or {})
            source_validation = mechanically_validate(source_candidate)
            challenger_validation = mechanically_validate(challenger_candidate)
            if source_validation["pitchValues"] != challenger_validation["pitchValues"]:
                raise TrainingWorkflowError("Challenger preference candidates no longer sound alike.")
            source_features = _candidate_features(source_candidate)
            challenger_features = _candidate_features(challenger_candidate)
            preference_id = "challenger-preference-" + _sha256_json(
                [packet_digest, decision_id, status, source_features, challenger_features]
            )[:20]
            texture = int(source_candidate.get("textureSize") or 1)
            style = "single_note_run" if texture == 1 else "harmonized" if texture == 2 else "chord_melody"
            preference_records.append(
                {
                    "schemaVersion": CHALLENGER_PREFERENCE_SCHEMA_VERSION,
                    "preferenceId": preference_id,
                    "batchId": batch_id,
                    "inputId": str(shadow.get("inputId") or ""),
                    "scoreSystemId": str(shadow.get("scoreSystemId") or ""),
                    "originalDecisionId": decision_id,
                    "sourceTabEventId": str(shadow.get("sourceTabEventId") or ""),
                    "status": status,
                    "comment": str(review.get("comment") or "").strip() or None,
                    "styleFamily": style,
                    "phraseRole": str(source_candidate.get("phraseRole") or ""),
                    "benchmarkGroup": str(shadow.get("pageType") or "challenger_comparison"),
                    "categoryTags": [
                        "feedback:challenger_comparison",
                        f"page:{shadow.get('pageType') or 'unknown'}",
                    ],
                    "sourceCandidate": source_features,
                    "challengerCandidate": challenger_features,
                    "sourceCandidateDigest": _sha256_json(source_features),
                    "challengerCandidateDigest": _sha256_json(challenger_features),
                    "mechanicalValidation": {
                        "source": source_validation,
                        "challenger": challenger_validation,
                    },
                    "evidenceType": "player_feedback",
                    "evidenceWeight": 1.0,
                    "modelId": model_id,
                    "shadowReportDigest": shadow_digest,
                    "packetDigest": packet_digest,
                    "submissionDigest": str(metadata.get("submissionDigest") or ""),
                    "reviewState": "human_approved",
                    "trainingEligible": status in {"source_preferred", "challenger_valid"},
                    "validationAccessed": False,
                    "sealedTestAccessed": False,
                }
            )
            status_counts[status] = status_counts.get(status, 0) + 1

        ledger_path = review_dir / "application" / "preference-ledger.jsonl"
        existing = _read_jsonl(ledger_path)
        existing_by_id = {str(item.get("preferenceId") or ""): item for item in existing}
        for item in preference_records:
            prior = existing_by_id.get(str(item["preferenceId"]))
            if prior is not None and _sha256_json(prior) != _sha256_json(item):
                raise TrainingWorkflowError("Challenger preference ID collides with different evidence.")
            existing_by_id[str(item["preferenceId"])] = item
        combined = [existing_by_id[key] for key in sorted(existing_by_id)]
        summary = {
            "schemaVersion": CHALLENGER_PREFERENCE_SCHEMA_VERSION,
            "batchId": batch_id,
            "modelId": model_id,
            "packetDigest": packet_digest,
            "submissionDigest": metadata.get("submissionDigest"),
            "reviewCount": len(preference_records),
            "statusCounts": dict(sorted(status_counts.items())),
            "trainingPreferenceCount": sum(bool(item.get("trainingEligible")) for item in preference_records),
            "coValidPreferenceCount": sum(item.get("status") == "both_valid" for item in preference_records),
            "ledgerDigest": _sha256_json(combined),
            "dryRun": dry_run,
            "validationAccessed": False,
            "sealedTestAccessed": False,
        }
        if not dry_run:
            _write_jsonl(ledger_path, combined)
            _write_json(review_dir / "application" / f"summary-{packet_digest}.json", summary)
            metadata["status"] = "applied"
            metadata["appliedAt"] = _utc_now()
            metadata["applicationSummary"] = summary
            _write_json(metadata_path, metadata)
        return summary

    def _accepted_records(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        registry = self._registry()
        authoritative = set(self._authoritative_batch_ids(registry))
        records: list[dict[str, Any]] = []
        for batch_id in sorted(registry["batches"]):
            batch_meta = registry["batches"][batch_id]
            if active_only and batch_meta.get("lifecycleStatus", "active") != "active":
                continue
            if active_only and authoritative and batch_id not in authoritative:
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
        training_records = [record for record in accepted if record.get("datasetPartition") in {"train", "discovery"}]
        if not training_records:
            raise TrainingWorkflowError("No validated training decisions are available.")
        registry = self._registry()
        authoritative_ids = self._authoritative_batch_ids(registry)
        if isinstance(registry.get("authoritativeDataset"), Mapping) and any(
            (self._batch_dir(batch_id) / "extraction" / "discovery").exists()
            for batch_id in authoritative_ids
        ):
            raise TrainingWorkflowError(
                "Managed authoritative discovery must use train_complete_discovery_challenger "
                "so exact seed, parent, preference, rights, and review lineage are preserved."
            )
        training_batch_ids = {str(record.get("batchId")) for record in training_records}
        missing_training_batches = [batch_id for batch_id in authoritative_ids if batch_id not in training_batch_ids]
        if missing_training_batches:
            raise TrainingWorkflowError(
                "Authoritative batches lack validated discovery decisions: " + ", ".join(missing_training_batches) + "."
            )
        for batch_id in authoritative_ids:
            self._require_complete_extraction_review(batch_id, "discovery")
            self._require_current_extraction_rights(batch_id, "discovery")
        rights_digests: dict[str, str] = {}
        source_copedent_profiles: list[dict[str, Any]] = []
        for batch_id in authoritative_ids:
            manifest, _state = self._batch(batch_id)
            rights = self._rights_and_access(batch_id)
            if (
                rights.get("reviewStatus") != "approved"
                or not bool(rights.get("allowedUses", {}).get("modelTraining"))
                or rights.get("rightsStatus") == "unknown"
            ):
                raise TrainingWorkflowError(
                    f"Authoritative batch lacks explicit model-training rights authorization: {batch_id}."
                )
            rights_digests[batch_id] = str(rights.get("recordDigest") or _sha256_json(rights))
            source_copedent_profiles.append(
                {
                    "batchId": batch_id,
                    "id": manifest["sourceCopedentId"],
                    "revision": int(manifest["sourceCopedentRevision"]),
                    "digest": manifest["sourceCopedentDigest"],
                }
            )
        source_copedent_profiles.sort(key=lambda item: str(item["batchId"]))
        trainer_records = [self._trainer_record(record) for record in training_records]
        authoritative_dataset = registry.get("authoritativeDataset")
        dataset_id = str(authoritative_dataset.get("datasetId")) if isinstance(authoritative_dataset, Mapping) else None
        dataset_hash = _sha256_json(
            {
                "authoritativeDatasetId": dataset_id,
                "records": trainer_records,
                "rightsAuthorizationDigests": rights_digests,
                "sourceCopedentProfiles": source_copedent_profiles,
            }
        )
        training_code_digests = _rules_code_file_digests(self.repo_root)
        config = {
            "epochs": int(epochs),
            "learningRate": float(learning_rate),
            "featureSchemaVersion": FEATURE_SCHEMA_VERSION,
            "rulesCodeDigest": _sha256_json(training_code_digests),
        }
        model_id = f"at-{_sha256_json({'datasetHash': dataset_hash, 'config': config})[:16]}"
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
            "authoritativeDatasetId": dataset_id,
            "sourceCopedentIds": sorted(
                {
                    str(
                        record.get("sourceCopedentId") or record.get("mechanicalValidation", {}).get("sourceCopedentId")
                    )
                    for record in training_records
                }
            ),
            "sourceCopedentProfiles": source_copedent_profiles,
            "rightsAuthorizationDigests": rights_digests,
            "codeRevision": _git_revision(self.repo_root),
            "trainingCodeFileDigests": training_code_digests,
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
        return AmazingTablatureTrainingStore._model_ranking_metrics(model, records)[
            "topChoiceAccuracy"
        ]

    @staticmethod
    def _model_ranking_metrics(
        model: Mapping[str, Any], records: Sequence[Mapping[str, Any]]
    ) -> dict[str, float | int]:
        """Score normalized-input candidate ranking without source recognition.

        The source-selected candidate is independently reviewed and therefore
        an acceptable answer.  Top-one uses the existing conservative strict
        preference rule: a tie is not a correct top choice.  Top-three is also
        conservative at a tie boundary by treating every tied alternative as
        ahead of the reviewed candidate.
        """

        if not records:
            return {
                "decisionCount": 0,
                "topChoiceCorrectCount": 0,
                "topChoiceAccuracy": 0.0,
                "topThreeCoveredCount": 0,
                "topThreeCoverage": 0.0,
            }
        top_choice_correct = 0
        top_three_covered = 0
        weights_by_style = model.get("weightsByStyle")
        if not isinstance(weights_by_style, Mapping):
            return {
                "decisionCount": len(records),
                "topChoiceCorrectCount": 0,
                "topChoiceAccuracy": 0.0,
                "topThreeCoveredCount": 0,
                "topThreeCoverage": 0.0,
            }
        for record in records:
            style = str(record.get("styleFamily") or "auto")
            weights = weights_by_style.get(style) or weights_by_style.get("auto") or {}
            chosen_score = score_candidate(record["chosen"], weights)
            alternative_scores = [
                score_candidate(alt, weights) for alt in record["alternatives"]
            ]
            if all(chosen_score < score for score in alternative_scores):
                top_choice_correct += 1
            conservative_rank = 1 + sum(
                score <= chosen_score for score in alternative_scores
            )
            if conservative_rank <= 3:
                top_three_covered += 1
        count = len(records)
        return {
            "decisionCount": count,
            "topChoiceCorrectCount": top_choice_correct,
            "topChoiceAccuracy": top_choice_correct / count,
            "topThreeCoveredCount": top_three_covered,
            "topThreeCoverage": top_three_covered / count,
        }

    @staticmethod
    def _validation_ranking_metrics(
        model: Mapping[str, Any], records: Sequence[Mapping[str, Any]]
    ) -> dict[str, float | int]:
        """Score arranger preference and mechanics on validation-only records."""

        ranking = AmazingTablatureTrainingStore._model_ranking_metrics(model, records)
        if not records:
            return {
                **ranking,
                "approvedSourceMechanicalValidCount": 0,
                "approvedSourceMechanicalAccuracy": 0.0,
                "predictedTopMechanicalValidCount": 0,
                "predictedTopMechanicalAccuracy": 0.0,
            }
        weights_by_style = model.get("weightsByStyle")
        if not isinstance(weights_by_style, Mapping):
            weights_by_style = {}
        approved_valid = 0
        predicted_valid = 0
        for record in records:
            chosen = record.get("chosen") or {}
            alternatives = list(record.get("alternatives") or [])
            if chosen.get("mechanicallyValid") is True:
                approved_valid += 1
            style = str(record.get("styleFamily") or "auto")
            weights = weights_by_style.get(style) or weights_by_style.get("auto") or {}
            candidates = [chosen, *alternatives]
            scores = [score_candidate(candidate, weights) for candidate in candidates]
            best_score = min(scores) if scores else math.inf
            predicted = [
                candidate
                for candidate, score in zip(candidates, scores, strict=True)
                if score == best_score
            ]
            if predicted and all(
                candidate.get("mechanicallyValid") is True for candidate in predicted
            ):
                predicted_valid += 1
        count = len(records)
        return {
            **ranking,
            "approvedSourceMechanicalValidCount": approved_valid,
            "approvedSourceMechanicalAccuracy": approved_valid / count,
            "predictedTopMechanicalValidCount": predicted_valid,
            "predictedTopMechanicalAccuracy": predicted_valid / count,
        }

    def score_validation_line_audits(self, model_id: str) -> dict[str, Any]:
        """Score immutable expert validation receipts without training on them.

        This is the pre-freeze bridge between the compact line audit and the
        canonical validation gate.  It intentionally does not import, accept,
        correct, or otherwise persist validation decisions as training data.
        """

        registry = self._registry()
        model_meta = registry["models"].get(model_id)
        if not model_meta:
            raise TrainingWorkflowError(f"Unknown challenger: {model_id}.")
        if (
            model_meta.get("datasetEligibility") != "complete_discovery"
            or not model_meta.get("canonicalEvaluationEligible")
        ):
            raise TrainingWorkflowError(
                "Validation line scoring requires a complete-discovery canonical challenger."
            )
        authoritative_ids = self._authoritative_batch_ids(registry)
        if not authoritative_ids:
            raise TrainingWorkflowError("No authoritative validation batches are registered.")
        if tuple(model_meta.get("sourceBatchIds") or ()) != authoritative_ids:
            raise TrainingWorkflowError(
                "The challenger source batches do not match the authoritative dataset."
            )
        model_path = self.root / str(model_meta["artifact"])
        if not model_path.exists():
            raise TrainingWorkflowError("The challenger artifact is missing.")
        artifact_sha256 = _sha256_bytes(model_path.read_bytes())
        if artifact_sha256 != str(model_meta.get("artifactSha256") or ""):
            raise TrainingWorkflowError(
                "The challenger artifact digest changed before validation scoring."
            )
        model = _read_json(model_path)

        batch_receipts: dict[str, dict[str, Any]] = {}
        ranking_records: list[dict[str, Any]] = []
        pending_batches: list[str] = []
        total_pages = 0
        reviewable_pages = 0
        no_line_pages = 0
        total_lines = 0
        resolved_lines = 0
        capture_failed_lines = 0
        score_reader_correct = 0
        tab_confirmed = 0
        exact_pitch_set_matches = 0
        automated_blockers = 0

        for batch_id in authoritative_ids:
            batch_dir = self._batch_dir(batch_id)
            audit_dir = (
                batch_dir
                / "extraction"
                / "validation"
                / "review"
                / "validation-line-audit"
            )
            packet_path = audit_dir / "packet.json"
            if not packet_path.exists():
                raise TrainingWorkflowError(
                    f"Authoritative batch lacks a validation line packet: {batch_id}."
                )
            packet = _read_json(packet_path)
            packet_digest = str(packet.get("packetDigest") or "")
            packet_core = {
                key: value for key, value in packet.items() if key != "packetDigest"
            }
            if (
                packet.get("reviewType") != "validation_line_audit"
                or packet.get("partition") != "validation"
                or packet.get("trainingEligible") is not False
                or packet.get("validationGroundTruthMayTrain") is not False
                or packet.get("sealedTestAccessed") is not False
                or packet.get("preflightVersion") != VALIDATION_LINE_PREFLIGHT_VERSION
                or any(
                    system.get("capturePreflightPassed") is not True
                    for page in packet.get("pages") or []
                    for system in page.get("systems") or []
                )
                or _sha256_json(packet_core) != packet_digest
            ):
                raise TrainingWorkflowError(
                    f"Validation packet lineage or no-training contract failed: {batch_id}."
                )
            pinned_model = packet.get("validationModel") or {}
            if (
                str(pinned_model.get("modelId") or "") != model_id
                or str(pinned_model.get("artifactSha256") or "") != artifact_sha256
            ):
                raise TrainingWorkflowError(
                    f"Validation packet is not pinned to the exact challenger: {batch_id}."
                )
            systems = {
                (str(system.get("inputId") or ""), str(system.get("scoreSystemId") or "")): system
                for page in packet.get("pages") or []
                for system in page.get("systems") or []
            }
            total_pages += int(packet.get("validationPageCount") or 0)
            packet_reviewable_pages = len(packet.get("pages") or [])
            reviewable_pages += packet_reviewable_pages
            no_line_pages += int(packet.get("noLinePageCount") or 0)
            total_lines += len(systems)
            automated_blockers += sum(
                int((system.get("validationIssueSummary") or {}).get("blockingCount") or 0)
                for system in systems.values()
            )

            metadata_candidates = []
            for metadata_path in sorted((audit_dir / "submissions").glob("*.json")):
                metadata = _read_json(metadata_path)
                if str(metadata.get("packetDigest") or "") == packet_digest:
                    metadata_candidates.append((metadata_path, metadata))
            if not metadata_candidates:
                pending_batches.append(batch_id)
                batch_receipts[batch_id] = {
                    "status": "awaiting_complete_expert_submission",
                    "packetDigest": packet_digest,
                    "validationRunDigest": packet.get("validationRunDigest"),
                    "validationPageCount": int(packet.get("validationPageCount") or 0),
                    "reviewablePageCount": packet_reviewable_pages,
                    "noLinePageCount": int(packet.get("noLinePageCount") or 0),
                    "lineCount": len(systems),
                    "automatedBlockingIssueCount": sum(
                        int((system.get("validationIssueSummary") or {}).get("blockingCount") or 0)
                        for system in systems.values()
                    ),
                }
                continue
            submission_digests = {
                str(metadata.get("submissionDigest") or "")
                for _path, metadata in metadata_candidates
            }
            if len(metadata_candidates) != 1 or len(submission_digests) != 1:
                raise TrainingWorkflowError(
                    f"Validation packet has ambiguous expert submissions: {batch_id}."
                )
            metadata_path, metadata = metadata_candidates[0]
            if (
                metadata.get("eligibleForTraining") is not False
                or metadata.get("validationGroundTruthMayTrain") is not False
                or metadata.get("sealedTestAccessed") is not False
            ):
                raise TrainingWorkflowError(
                    f"Validation submission violates the no-training contract: {batch_id}."
                )
            submission_id = str(metadata.get("submissionId") or "")
            submission_path = metadata_path.with_suffix(".jsonl")
            if metadata_path.stem != submission_id or not submission_path.exists():
                raise TrainingWorkflowError(
                    f"Validation submission receipt is incomplete: {batch_id}."
                )
            rows = _read_jsonl(submission_path)
            expected_submission_digest = _sha256_json(
                {
                    "reviewType": "validation_line_audit",
                    "batchId": batch_id,
                    "partition": "validation",
                    "packetDigest": packet_digest,
                    "reviews": rows,
                    "validationGroundTruthMayTrain": False,
                }
            )
            if (
                expected_submission_digest
                != str(metadata.get("submissionDigest") or "")
                or int(metadata.get("reviewCount") or 0) != len(rows)
                or len(rows) != len(systems)
            ):
                raise TrainingWorkflowError(
                    f"Validation submission digest or line count failed: {batch_id}."
                )
            seen: set[tuple[str, str]] = set()
            batch_record_count = 0
            status_counts: dict[str, int] = {}
            for row in rows:
                key = (
                    str(row.get("inputId") or ""),
                    str(row.get("scoreSystemId") or ""),
                )
                system = systems.get(key)
                status = str(row.get("status") or "")
                if (
                    system is None
                    or key in seen
                    or status
                    not in {
                        "capture_failed",
                        "both_match",
                        "tab_pitch_hypothesis_matches",
                        "score_reader_matches",
                        "feedback",
                    }
                    or str(row.get("expectedMachineRecordDigest") or "")
                    != str(system.get("machineRecordDigest") or "")
                    or row.get("trainingEligible") is not False
                ):
                    raise TrainingWorkflowError(
                        f"Validation line receipt does not match its packet: {batch_id}."
                    )
                seen.add(key)
                status_counts[status] = status_counts.get(status, 0) + 1
                row_tab_confirmed = bool(row.get("tabConfirmed"))
                if row_tab_confirmed:
                    tab_confirmed += 1
                if status == "capture_failed":
                    capture_failed_lines += 1
                if status not in {"capture_failed", "feedback"}:
                    resolved_lines += 1
                if status in {"both_match", "score_reader_matches"}:
                    score_reader_correct += 1
                if status == "both_match":
                    exact_pitch_set_matches += 1
                if status in {"capture_failed", "feedback"} or not row_tab_confirmed:
                    continue

                input_id = key[0]
                page_path = (
                    batch_dir
                    / "extraction"
                    / "validation"
                    / "pages"
                    / f"{input_id}.json"
                )
                if not page_path.exists():
                    raise TrainingWorkflowError(
                        f"Validation page record is missing: {batch_id}/{input_id}."
                    )
                page_record = _read_json(page_path)
                if _sha256_json(page_record) != str(system.get("machineRecordDigest") or ""):
                    raise TrainingWorkflowError(
                        f"Validation page changed after expert review: {batch_id}/{input_id}."
                    )
                tab_system_id = str(system.get("tabSystemId") or "")
                tab_system = next(
                    (
                        item
                        for item in page_record.get("tabSystems") or []
                        if str(item.get("tabSystemId") or "") == tab_system_id
                    ),
                    None,
                )
                if tab_system is None:
                    raise TrainingWorkflowError(
                        f"Reviewed validation line has no current tab system: {batch_id}/{input_id}."
                    )
                tab_event_ids = {
                    str(event.get("tabEventId") or "")
                    for event in tab_system.get("tabEvents") or []
                }
                decisions = [
                    dict(decision)
                    for decision in page_record.get("derivedDecisions") or []
                    if str(decision.get("sourceTabEventId") or "") in tab_event_ids
                    and isinstance(decision.get("chosen"), Mapping)
                    and bool(decision.get("alternatives"))
                ]
                for decision in decisions:
                    decision["batchId"] = batch_id
                    decision["validationLineStatus"] = status
                ranking_records.extend(decisions)
                batch_record_count += len(decisions)
            if seen != set(systems):
                raise TrainingWorkflowError(
                    f"Validation submission is not complete for every line: {batch_id}."
                )
            batch_receipts[batch_id] = {
                "status": "verified_and_scored_in_memory",
                "packetDigest": packet_digest,
                "validationRunDigest": packet.get("validationRunDigest"),
                "submissionId": submission_id,
                "submissionDigest": metadata.get("submissionDigest"),
                "submissionFileSha256": _sha256_bytes(submission_path.read_bytes()),
                "lineCount": len(rows),
                "statusCounts": dict(sorted(status_counts.items())),
                "rankingDecisionCount": batch_record_count,
                "eligibleForTraining": False,
            }

        recognition_metrics = {
            "validationPageCount": total_pages,
            "reviewablePageCount": reviewable_pages,
            "noLinePageCount": no_line_pages,
            "pageSystemDetectionAccuracy": reviewable_pages / total_pages if total_pages else 0.0,
            "auditedLineCount": total_lines,
            "resolvedLineCount": resolved_lines,
            "captureFailedLineCount": capture_failed_lines,
            "resolvedLineRate": resolved_lines / total_lines if total_lines else 0.0,
            "scoreReaderCorrectCount": score_reader_correct,
            "scoreReaderAccuracy": score_reader_correct / total_lines if total_lines else 0.0,
            "tabCaptureConfirmedCount": tab_confirmed,
            "tabCaptureConfirmationRate": tab_confirmed / total_lines if total_lines else 0.0,
            "exactScoreTabPitchSetMatchCount": exact_pitch_set_matches,
            "exactScoreTabPitchSetMatchRate": exact_pitch_set_matches / total_lines if total_lines else 0.0,
            "automatedBlockingIssueCountBeforeExpertReview": automated_blockers,
        }
        recognition_complete = not pending_batches
        recognition_gate = bool(
            recognition_complete
            and recognition_metrics["pageSystemDetectionAccuracy"]
            >= VALIDATION_LINE_PAGE_DETECTION_FLOOR
            and recognition_metrics["scoreReaderAccuracy"]
            >= VALIDATION_LINE_SCORE_READER_FLOOR
            and recognition_metrics["tabCaptureConfirmationRate"]
            >= VALIDATION_LINE_TAB_CONFIRMATION_FLOOR
            and recognition_metrics["resolvedLineRate"]
            >= VALIDATION_LINE_RESOLUTION_FLOOR
        )

        overall_ranking = self._validation_ranking_metrics(model, ranking_records)
        cohort_metrics: dict[str, dict[str, Any]] = {}
        for batch_id in authoritative_ids:
            records = [
                record for record in ranking_records if record.get("batchId") == batch_id
            ]
            cohort_metrics[batch_id] = {
                **self._validation_ranking_metrics(model, records),
                "evidenceSufficient": len(records) >= VALIDATION_MIN_DECISIONS_PER_COHORT,
            }
        evidence_mode_metrics: dict[str, dict[str, Any]] = {}
        for tag in ("alignment:score_supported", "alignment:tab_only"):
            records = [
                record
                for record in ranking_records
                if tag in (record.get("categoryTags") or [])
            ]
            evidence_mode_metrics[tag] = {
                **self._validation_ranking_metrics(model, records),
                "evidenceSufficient": len(records)
                >= VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE,
            }
        ranking_gate = bool(
            recognition_complete
            and overall_ranking["topChoiceAccuracy"]
            > VALIDATION_OVERALL_PREFERENCE_FLOOR
            and overall_ranking["topThreeCoverage"]
            >= VALIDATION_TOP_THREE_COVERAGE_FLOOR
            and overall_ranking["approvedSourceMechanicalAccuracy"] == 1.0
            and overall_ranking["predictedTopMechanicalAccuracy"] == 1.0
            and all(
                metrics["evidenceSufficient"]
                and metrics["topChoiceAccuracy"]
                >= VALIDATION_COHORT_PREFERENCE_FLOOR
                and metrics["approvedSourceMechanicalAccuracy"] == 1.0
                and metrics["predictedTopMechanicalAccuracy"] == 1.0
                for metrics in cohort_metrics.values()
            )
            and all(
                metrics["evidenceSufficient"]
                and metrics["topChoiceAccuracy"]
                >= VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR
                and metrics["approvedSourceMechanicalAccuracy"] == 1.0
                and metrics["predictedTopMechanicalAccuracy"] == 1.0
                for metrics in evidence_mode_metrics.values()
            )
        )
        input_parity = structured_input_parity_report()
        if not input_parity.get("parityPassed"):
            ranking_gate = False
        gate_passed = recognition_gate and ranking_gate
        report_core = {
            "schemaVersion": "amazing-tablature-validation-line-score-v1",
            "modelId": model_id,
            "modelArtifactSha256": artifact_sha256,
            "authoritativeBatchIds": list(authoritative_ids),
            "batchReceipts": batch_receipts,
            "recognition": {
                "metricScope": "compact_expert_line_audit_not_full_atomic_omr_contract",
                "metrics": recognition_metrics,
                "thresholds": {
                    "pageSystemDetectionAccuracy": VALIDATION_LINE_PAGE_DETECTION_FLOOR,
                    "scoreReaderAccuracy": VALIDATION_LINE_SCORE_READER_FLOOR,
                    "tabCaptureConfirmationRate": VALIDATION_LINE_TAB_CONFIRMATION_FLOOR,
                    "resolvedLineRate": VALIDATION_LINE_RESOLUTION_FLOOR,
                },
                "passed": recognition_gate,
            },
            "arrangerRanking": {
                "inputScope": "normalized_score_events",
                "scoreImageRecognitionIncluded": False,
                "metrics": overall_ranking,
                "cohorts": cohort_metrics,
                "evidenceModes": evidence_mode_metrics,
                "thresholds": {
                    "overallTopChoiceAccuracy": {
                        "comparison": "strictly_greater_than",
                        "value": VALIDATION_OVERALL_PREFERENCE_FLOOR,
                    },
                    "topThreeCoverage": VALIDATION_TOP_THREE_COVERAGE_FLOOR,
                    "cohortTopChoiceAccuracy": VALIDATION_COHORT_PREFERENCE_FLOOR,
                    "minimumDecisionsPerCohort": VALIDATION_MIN_DECISIONS_PER_COHORT,
                    "evidenceModeTopChoiceAccuracy": VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR,
                    "minimumDecisionsPerEvidenceMode": VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE,
                    "mechanicalAccuracy": 1.0,
                },
                "passed": ranking_gate,
            },
            "structuredInputParity": {
                **input_parity,
                "rankingMetricInheritance": (
                    "All five exact input adapters normalize to identical arranger "
                    "events; after validation is complete, each modality inherits "
                    "the same exact challenger ranking metrics above."
                ),
            },
            "gate": {
                "passed": gate_passed,
                "rulesFreezeAllowed": gate_passed,
                "sealedTestAllowed": gate_passed,
                "pendingBatches": pending_batches,
            },
            "lineage": {
                "modelCodeRevision": model.get("codeRevision"),
                "evaluationCodeRevision": _git_revision(self.repo_root),
                "evaluationCodeFileDigests": _rules_code_file_digests(self.repo_root),
            },
            "noTrainingContract": {
                "validationGroundTruthMayTrain": False,
                "validationDecisionsAddedToTraining": 0,
                "acceptedDecisionLedgersModified": False,
                "modelArtifactModified": False,
            },
            "validationAccessed": True,
            "sealedTestAccessed": False,
        }
        report_digest = _sha256_json(report_core)
        report = {**report_core, "reportDigest": report_digest}
        report_dir = self.root / "validation-evaluations" / model_id
        report_dir.mkdir(parents=True, exist_ok=True)
        _make_private(report_dir, directory=True)
        report_path = report_dir / f"validation-line-score-{report_digest}.json"
        _write_json(report_path, report)
        _make_private(report_path)
        return {
            **report,
            "reportPath": str(report_path.relative_to(self.root)),
        }

    def score_validation_machine_candidates(self, model_id: str) -> dict[str, Any]:
        """Score only complete, discovery-calibrated validation tab lines.

        This is an automatic, evaluation-only fallback for the image-reader
        bottleneck.  It accepts no validation label as training evidence and
        deliberately strips score facts before deriving candidate-choice
        records.  As a result, the output can measure the exact challenger on
        high-confidence ``alignment:tab_only`` movements, but it cannot satisfy
        the separately predeclared ``alignment:score_supported`` gate.
        """

        from pocketsteel.amazing_tablature_decisions import (
            derive_decision_annotations,
        )

        registry = self._registry()
        model_meta = registry["models"].get(model_id)
        if not model_meta:
            raise TrainingWorkflowError(f"Unknown challenger: {model_id}.")
        if (
            model_meta.get("datasetEligibility") != "complete_discovery"
            or not model_meta.get("canonicalEvaluationEligible")
        ):
            raise TrainingWorkflowError(
                "Machine-candidate validation scoring requires a "
                "complete-discovery canonical challenger."
            )
        authoritative_ids = self._authoritative_batch_ids(registry)
        if not authoritative_ids:
            raise TrainingWorkflowError(
                "No authoritative validation batches are registered."
            )
        if tuple(model_meta.get("sourceBatchIds") or ()) != authoritative_ids:
            raise TrainingWorkflowError(
                "The challenger source batches do not match the authoritative dataset."
            )
        model_path = self.root / str(model_meta["artifact"])
        if not model_path.exists():
            raise TrainingWorkflowError("The challenger artifact is missing.")
        artifact_sha256 = _sha256_bytes(model_path.read_bytes())
        if artifact_sha256 != str(model_meta.get("artifactSha256") or ""):
            raise TrainingWorkflowError(
                "The challenger artifact digest changed before validation scoring."
            )
        model = _read_json(model_path)

        ranking_records: list[dict[str, Any]] = []
        cohort_receipts: dict[str, dict[str, Any]] = {}
        machine_line_count = 0
        withheld_line_count = 0
        candidate_digests: list[str] = []

        for batch_id in authoritative_ids:
            manifest, _state = self._batch(batch_id)
            profile = _profile_for_source(str(manifest["sourceCopedentId"]))
            if (
                profile.revision != int(manifest["sourceCopedentRevision"])
                or _profile_digest(profile) != str(manifest["sourceCopedentDigest"])
            ):
                raise TrainingWorkflowError(
                    f"The source copedent changed before validation scoring: {batch_id}."
                )
            validation_root = (
                self._batch_dir(batch_id) / "extraction" / "validation"
            )
            report_path = (
                validation_root
                / "review"
                / "automation"
                / "validation-contact-sheet-consensus-v3"
                / "report.json"
            )
            if not report_path.exists():
                raise TrainingWorkflowError(
                    f"Authoritative batch lacks a machine-consensus report: {batch_id}."
                )
            consensus = _read_json(report_path)
            report_digest = str(consensus.get("reportDigest") or "")
            report_core = {
                key: value
                for key, value in consensus.items()
                if key != "reportDigest"
            }
            if (
                consensus.get("schemaVersion")
                != "validation-contact-sheet-consensus-v3"
                or consensus.get("batchId") != batch_id
                or consensus.get("partition") != "validation"
                or consensus.get("humanTruthUsed") is not False
                or consensus.get("validationMayTrain") is not False
                or consensus.get("sealedTestAccessed") is not False
                or _sha256_json(report_core) != report_digest
            ):
                raise TrainingWorkflowError(
                    f"Machine-consensus lineage or no-training contract failed: {batch_id}."
                )
            pinned_model = consensus.get("validationModel") or {}
            if (
                str(pinned_model.get("modelId") or "") != model_id
                or str(pinned_model.get("artifactSha256") or "")
                != artifact_sha256
            ):
                raise TrainingWorkflowError(
                    f"Machine consensus is not pinned to the exact challenger: {batch_id}."
                )

            batch_records: list[dict[str, Any]] = []
            complete_lines = 0
            withheld_lines = 0
            candidate_decision_count = 0
            for line in consensus.get("lines") or []:
                if line.get("status") != "complete_machine_candidate":
                    withheld_lines += 1
                    continue
                candidate_relative = Path(str(line.get("candidatePath") or ""))
                candidate_path = (validation_root / candidate_relative).resolve()
                allowed_root = (
                    validation_root
                    / "review"
                    / "automation"
                    / "validation-contact-sheet-consensus-v3"
                    / "candidates"
                ).resolve()
                try:
                    candidate_path.relative_to(allowed_root)
                except ValueError as exc:
                    raise TrainingWorkflowError(
                        "A machine validation candidate escaped its private output directory."
                    ) from exc
                if not candidate_path.exists():
                    raise TrainingWorkflowError(
                        f"A complete machine validation candidate is missing: {batch_id}."
                    )
                candidate = _read_json(candidate_path)
                candidate_digest = str(candidate.get("candidateDigest") or "")
                candidate_core = {
                    key: value
                    for key, value in candidate.items()
                    if key != "candidateDigest"
                }
                diagnostics = candidate.get("diagnostics") or {}
                if (
                    candidate.get("schemaVersion")
                    != "validation-contact-sheet-consensus-v3"
                    or candidate.get("batchId") != batch_id
                    or candidate.get("partition") != "validation"
                    or candidate.get("status")
                    != "complete_machine_candidate"
                    or candidate.get("humanTruthUsed") is not False
                    or candidate.get("validationMayTrain") is not False
                    or candidate.get("sealedTestAccessed") is not False
                    or candidate_digest
                    != str(line.get("candidateDigest") or "")
                    or _sha256_json(candidate_core) != candidate_digest
                    or diagnostics.get("allCellsResolved") is not True
                    or diagnostics.get("allColumnsDecoded") is not True
                    or diagnostics.get("mechanicallyValid") is not True
                    or int(diagnostics.get("unresolvedCellCount") or 0) != 0
                ):
                    raise TrainingWorkflowError(
                        f"A machine validation candidate is incomplete or unpinned: {batch_id}."
                    )
                candidate_model = candidate.get("validationModel") or {}
                if (
                    str(candidate_model.get("modelId") or "") != model_id
                    or str(candidate_model.get("artifactSha256") or "")
                    != artifact_sha256
                ):
                    raise TrainingWorkflowError(
                        f"A machine candidate targets a different challenger: {batch_id}."
                    )
                input_id = str(candidate.get("inputId") or "")
                page_path = validation_root / "pages" / f"{input_id}.json"
                if not page_path.exists():
                    raise TrainingWorkflowError(
                        f"A machine validation page is missing: {batch_id}/{input_id}."
                    )
                page_record = _read_json(page_path)
                if _sha256_json(page_record) != str(
                    candidate.get("machineRecordDigest") or ""
                ):
                    raise TrainingWorkflowError(
                        f"A validation page changed after machine consensus: "
                        f"{batch_id}/{input_id}."
                    )
                tab_system_id = str(candidate.get("tabSystemId") or "")
                tab_system = next(
                    (
                        deepcopy(item)
                        for item in page_record.get("tabSystems") or []
                        if str(item.get("tabSystemId") or "") == tab_system_id
                    ),
                    None,
                )
                if tab_system is None:
                    raise TrainingWorkflowError(
                        f"A machine candidate has no source tab system: "
                        f"{batch_id}/{input_id}."
                    )
                candidate_events = deepcopy(candidate.get("events") or [])
                if not candidate_events:
                    raise TrainingWorkflowError(
                        f"A complete machine candidate has no events: "
                        f"{batch_id}/{input_id}."
                    )
                candidate_decision_count += max(
                    0,
                    len(candidate_events) - 1,
                )
                tab_system["tabEvents"] = candidate_events
                tab_event_ids = {
                    str(event.get("tabEventId") or "")
                    for event in candidate_events
                }
                derivation_record = deepcopy(page_record)
                # The automatic comparison is intentionally tab-only.  It may
                # not turn a machine score hypothesis into held-out truth.
                derivation_record["scoreSystems"] = []
                derivation_record["eventAlignments"] = []
                derivation_record["tabSystems"] = [tab_system]
                derivation_record["movementSequences"] = [
                    movement
                    for movement in derivation_record.get("movementSequences")
                    or []
                    if str(movement.get("toTabEventId") or "")
                    in tab_event_ids
                ]
                decisions = derive_decision_annotations(
                    derivation_record,
                    profile,
                )
                if len(decisions) != max(0, len(candidate_events) - 1):
                    raise TrainingWorkflowError(
                        "A complete machine line did not yield one context-complete "
                        "decision for every movement."
                    )
                event_index_by_id = {
                    str(event.get("tabEventId") or ""): index
                    for index, event in enumerate(candidate_events)
                }
                exact_execution_inference = {
                    "initial_attack",
                    "reviewed_source_transition_decoder",
                }
                context_complete_decisions: list[dict[str, Any]] = []
                for decision in decisions:
                    if "alignment:tab_only" not in (
                        decision.get("categoryTags") or []
                    ):
                        raise TrainingWorkflowError(
                            "Automatic validation decisions must remain tab-only."
                        )
                    event_index = event_index_by_id.get(
                        str(decision.get("sourceTabEventId") or "")
                    )
                    if event_index is None:
                        raise TrainingWorkflowError(
                            "An automatic validation decision lost its source event."
                        )
                    current_event = candidate_events[event_index]
                    following_event = (
                        candidate_events[event_index + 1]
                        if event_index + 1 < len(candidate_events)
                        else None
                    )
                    # An unresolved attack-versus-hold changes sustained,
                    # repicked, and outgoing-continuity features.  Such a
                    # movement is not context-complete and cannot be scored.
                    if (
                        str(current_event.get("executionInference") or "")
                        not in exact_execution_inference
                        or (
                            following_event is not None
                            and str(
                                following_event.get("executionInference") or ""
                            )
                            not in exact_execution_inference
                        )
                    ):
                        continue
                    decision["batchId"] = batch_id
                    decision["validationEvidence"] = {
                        "mode": "machine_consensus_complete_line",
                        "consensusReportDigest": report_digest,
                        "candidateDigest": candidate_digest,
                        "validationMayTrain": False,
                    }
                    decision["mechanicalValidation"] = _mechanical_validation(
                        decision,
                        profile,
                    )
                    context_complete_decisions.append(decision)
                batch_records.extend(context_complete_decisions)
                candidate_digests.append(candidate_digest)
                complete_lines += 1

            ranking_records.extend(batch_records)
            machine_line_count += complete_lines
            withheld_line_count += withheld_lines
            cohort_receipts[batch_id] = {
                "consensusReportDigest": report_digest,
                "consensusReportFileSha256": _sha256_bytes(
                    report_path.read_bytes()
                ),
                "validationRunDigest": consensus.get("validationRunDigest"),
                "completeMachineLineCount": complete_lines,
                "withheldLineCount": withheld_lines,
                "decisionCount": len(batch_records),
                "contextIncompleteDecisionCount": (
                    candidate_decision_count - len(batch_records)
                ),
                "decisionDigest": _sha256_json(batch_records),
                "humanTruthUsed": False,
                "validationMayTrain": False,
            }

        overall = self._validation_ranking_metrics(model, ranking_records)
        cohort_metrics: dict[str, dict[str, Any]] = {}
        for batch_id in authoritative_ids:
            records = [
                record
                for record in ranking_records
                if record.get("batchId") == batch_id
            ]
            cohort_metrics[batch_id] = {
                **self._validation_ranking_metrics(model, records),
                "evidenceSufficient": len(records)
                >= VALIDATION_MIN_DECISIONS_PER_COHORT,
            }
        tab_only_metrics = {
            **self._validation_ranking_metrics(model, ranking_records),
            "evidenceSufficient": len(ranking_records)
            >= VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE,
        }
        score_supported_metrics = {
            **self._validation_ranking_metrics(model, []),
            "evidenceSufficient": False,
        }
        measured_thresholds_passed = bool(
            overall["topChoiceAccuracy"]
            > VALIDATION_OVERALL_PREFERENCE_FLOOR
            and overall["topThreeCoverage"]
            >= VALIDATION_TOP_THREE_COVERAGE_FLOOR
            and overall["approvedSourceMechanicalAccuracy"] == 1.0
            and overall["predictedTopMechanicalAccuracy"] == 1.0
            and all(
                metrics["evidenceSufficient"]
                and metrics["topChoiceAccuracy"]
                >= VALIDATION_COHORT_PREFERENCE_FLOOR
                and metrics["approvedSourceMechanicalAccuracy"] == 1.0
                and metrics["predictedTopMechanicalAccuracy"] == 1.0
                for metrics in cohort_metrics.values()
            )
            and tab_only_metrics["evidenceSufficient"]
            and tab_only_metrics["topChoiceAccuracy"]
            >= VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR
        )
        input_parity = structured_input_parity_report()
        canonical_gate_passed = False
        report_core = {
            "schemaVersion": "amazing-tablature-machine-validation-score-v1",
            "modelId": model_id,
            "modelArtifactSha256": artifact_sha256,
            "evaluatedAt": _utc_now(),
            "evaluationScope": "complete_machine_consensus_tab_lines",
            "authoritativeBatchIds": list(authoritative_ids),
            "cohortReceipts": cohort_receipts,
            "completeMachineLineCount": machine_line_count,
            "withheldLineCount": withheld_line_count,
            "decisionCount": len(ranking_records),
            "decisionDigest": _sha256_json(ranking_records),
            "candidateSetDigest": _sha256_json(sorted(candidate_digests)),
            "metrics": overall,
            "cohortMetrics": cohort_metrics,
            "evidenceModeMetrics": {
                "alignment:score_supported": score_supported_metrics,
                "alignment:tab_only": tab_only_metrics,
            },
            "thresholds": {
                "overallTopChoiceAccuracy": {
                    "comparison": "strictly_greater_than",
                    "value": VALIDATION_OVERALL_PREFERENCE_FLOOR,
                },
                "topThreeCoverage": VALIDATION_TOP_THREE_COVERAGE_FLOOR,
                "cohortTopChoiceAccuracy": VALIDATION_COHORT_PREFERENCE_FLOOR,
                "evidenceModeTopChoiceAccuracy": (
                    VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR
                ),
                "minimumDecisionsPerCohort": (
                    VALIDATION_MIN_DECISIONS_PER_COHORT
                ),
                "minimumDecisionsPerEvidenceMode": (
                    VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE
                ),
                "mechanicalAccuracy": 1.0,
            },
            "structuredInputParity": input_parity,
            "gate": {
                "measuredThresholdsPassed": measured_thresholds_passed,
                "canonicalGatePassed": canonical_gate_passed,
                "rulesFreezeAllowed": False,
                "privateRuntimeEnableAllowed": False,
                "reasons": [
                    "machine_consensus_is_not_human_validation_ground_truth",
                    "score_supported_validation_evidence_missing",
                    *(
                        []
                        if measured_thresholds_passed
                        else ["measured_preference_thresholds_not_met"]
                    ),
                ],
            },
            "lineage": {
                "modelCodeRevision": model.get("codeRevision"),
                "evaluationCodeRevision": _git_revision(self.repo_root),
                "evaluationCodeFileDigests": _rules_code_file_digests(
                    self.repo_root
                ),
            },
            "noTrainingContract": {
                "validationGroundTruthMayTrain": False,
                "validationDecisionsAddedToTraining": 0,
                "acceptedDecisionLedgersModified": False,
                "modelArtifactModified": False,
            },
            "humanTruthUsed": False,
            "validationAccessed": True,
            "validationMayTrain": False,
            "sealedTestAccessed": False,
        }
        report_digest = _sha256_json(report_core)
        report = {**report_core, "reportDigest": report_digest}
        report_dir = self.root / "validation-evaluations" / model_id
        report_dir.mkdir(parents=True, exist_ok=True)
        _make_private(report_dir, directory=True)
        report_path = (
            report_dir
            / f"machine-consensus-score-{report_digest}.json"
        )
        _write_json(report_path, report)
        _make_private(report_path)
        return {
            **report,
            "reportPath": str(report_path.relative_to(self.root)),
        }

    def evaluate(self, model_id: str) -> dict[str, Any]:
        registry = self._registry()
        model_meta = registry["models"].get(model_id)
        if not model_meta:
            raise TrainingWorkflowError(f"Unknown challenger: {model_id}.")
        if model_meta.get("discoveryShadowOnly"):
            raise TrainingWorkflowError(
                "A partial-discovery challenger cannot enter canonical validation or promotion."
            )
        model_path = self.root / str(model_meta["artifact"])
        model_artifact_sha256 = _sha256_bytes(model_path.read_bytes())
        expected_model_sha256 = str(model_meta.get("artifactSha256") or "")
        if expected_model_sha256 and model_artifact_sha256 != expected_model_sha256:
            raise TrainingWorkflowError("The challenger artifact digest changed before evaluation.")
        model = _read_json(model_path)
        authoritative_dataset = registry.get("authoritativeDataset")
        authoritative_ids = self._authoritative_batch_ids(registry)
        managed_authoritative_discovery = bool(
            isinstance(authoritative_dataset, Mapping)
            and any(
                (self._batch_dir(batch_id) / "extraction" / "discovery").exists()
                for batch_id in authoritative_ids
            )
        )
        canonical_evaluation = bool(
            model_meta.get("datasetEligibility") == "complete_discovery"
            and model_meta.get("canonicalEvaluationEligible")
            and model.get("fullDiscoveryReviewComplete")
        )
        if managed_authoritative_discovery and not canonical_evaluation:
            raise TrainingWorkflowError(
                "Managed authoritative validation requires a complete-discovery canonical challenger."
            )
        accepted = self._accepted_records()
        holdouts = [record for record in accepted if record.get("datasetPartition") == "validation"]
        evaluation_partition = "validation"
        if not holdouts:
            holdouts = [record for record in accepted if record.get("datasetPartition") == "holdout"]
            evaluation_partition = "holdout"
        if not holdouts:
            raise TrainingWorkflowError("No validated validation decisions are available.")
        validation_batch_ids = {str(record.get("batchId")) for record in holdouts}
        missing_validation_batches = [
            batch_id for batch_id in authoritative_ids if batch_id not in validation_batch_ids
        ]
        if missing_validation_batches:
            raise TrainingWorkflowError(
                "Authoritative batches lack validated validation decisions: "
                + ", ".join(missing_validation_batches)
                + "."
            )
        for batch_id in authoritative_ids:
            self._require_complete_extraction_review(batch_id, "validation")
            self._require_extraction_acceptance(batch_id, "validation")
            self._require_current_extraction_rights(batch_id, "validation")
        if canonical_evaluation:
            expected_profiles = []
            expected_rights: dict[str, str] = {}
            for batch_id in authoritative_ids:
                manifest, _state = self._batch(batch_id)
                rights = self._rights_and_access(batch_id)
                expected_profiles.append(
                    {
                        "batchId": batch_id,
                        "id": manifest["sourceCopedentId"],
                        "revision": int(manifest["sourceCopedentRevision"]),
                        "digest": manifest["sourceCopedentDigest"],
                    }
                )
                expected_rights[batch_id] = str(rights.get("recordDigest") or "")
            expected_profiles.sort(key=lambda item: item["batchId"])
            if model.get("sourceCopedentProfiles") != expected_profiles:
                raise TrainingWorkflowError(
                    "The canonical challenger copedent lineage is not current."
                )
            if model.get("rightsAuthorizationDigests") != expected_rights:
                raise TrainingWorkflowError(
                    "The canonical challenger rights lineage is not current."
                )
        mechanical_accuracy = sum(bool(record.get("mechanicalValidation", {}).get("ok")) for record in holdouts) / len(
            holdouts
        )
        ranking_metrics = self._model_ranking_metrics(model, holdouts)
        challenger_accuracy = float(ranking_metrics["topChoiceAccuracy"])
        top_three_coverage = float(ranking_metrics["topThreeCoverage"])
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
        required = (
            []
            if isinstance(registry.get("authoritativeDataset"), Mapping)
            else list(registry.get("requiredBenchmarkGroups") or REQUIRED_BENCHMARK_GROUPS)
        )
        missing_benchmarks = [group for group in required if not benchmark_counts.get(group)]
        privacy_findings = _contains_forbidden_runtime_data(model)
        overall_preference_floor = (
            VALIDATION_OVERALL_PREFERENCE_FLOOR
            if canonical_evaluation
            else (champion_accuracy if champion_accuracy is not None else 0.5)
        )
        cohort_preference_floor = (
            VALIDATION_COHORT_PREFERENCE_FLOOR
            if canonical_evaluation
            else overall_preference_floor
        )
        evidence_mode_preference_floor = (
            VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR
            if canonical_evaluation
            else overall_preference_floor
        )
        minimum_cohort_decisions = (
            VALIDATION_MIN_DECISIONS_PER_COHORT if canonical_evaluation else 1
        )
        minimum_evidence_mode_decisions = (
            VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE
            if canonical_evaluation
            else 1
        )
        preference_floor_passed = (
            challenger_accuracy > overall_preference_floor
            if canonical_evaluation
            else challenger_accuracy >= overall_preference_floor
        )
        top_three_floor = (
            VALIDATION_TOP_THREE_COVERAGE_FLOOR if canonical_evaluation else 0.0
        )
        preference_gate = bool(
            preference_floor_passed
            and top_three_coverage >= top_three_floor
            and (
                champion_accuracy is None
                or challenger_accuracy >= champion_accuracy
            )
        )
        cohort_metrics: dict[str, dict[str, Any]] = {}
        validation_lineage: dict[str, dict[str, Any]] = {}
        for batch_id in authoritative_ids:
            records = [record for record in holdouts if str(record.get("batchId")) == batch_id]
            manifest, _state = self._batch(batch_id)
            metrics_path = (
                self._batch_dir(batch_id)
                / "extraction"
                / "validation"
                / "review"
                / "review-metrics.json"
            )
            extraction_summary_path = (
                self._batch_dir(batch_id)
                / "extraction"
                / "validation"
                / "summary.json"
            )
            rights = self._rights_and_access(batch_id)
            metrics_payload = _read_json(metrics_path) if metrics_path.exists() else None
            extraction_summary = (
                _read_json(extraction_summary_path)
                if extraction_summary_path.exists()
                else None
            )
            validation_lineage[batch_id] = {
                "decisionCount": len(records),
                "decisionDigest": _sha256_json(records),
                "reviewMetricsCanonicalDigest": (
                    _sha256_json(metrics_payload) if metrics_payload is not None else None
                ),
                "reviewMetricsFileSha256": (
                    _sha256_bytes(metrics_path.read_bytes())
                    if metrics_path.exists()
                    else None
                ),
                "extractionRunDigest": (
                    extraction_summary.get("runDigest")
                    if extraction_summary is not None
                    else None
                ),
                "extractionSummaryFileSha256": (
                    _sha256_bytes(extraction_summary_path.read_bytes())
                    if extraction_summary_path.exists()
                    else None
                ),
                "rightsAuthorizationDigest": str(rights.get("recordDigest") or ""),
                "sourceCopedentId": manifest["sourceCopedentId"],
                "sourceCopedentRevision": int(manifest["sourceCopedentRevision"]),
                "sourceCopedentDigest": manifest["sourceCopedentDigest"],
            }
            cohort_ranking = self._model_ranking_metrics(model, records)
            cohort_metrics[batch_id] = {
                "decisionCount": len(records),
                "evidenceSufficient": len(records) >= minimum_cohort_decisions,
                "sourceCopedentId": manifest["sourceCopedentId"],
                "sourceCopedentRevision": int(manifest["sourceCopedentRevision"]),
                "sourceCopedentDigest": manifest["sourceCopedentDigest"],
                "mechanicalAccuracy": (
                    sum(bool(record.get("mechanicalValidation", {}).get("ok")) for record in records) / len(records)
                    if records
                    else 0.0
                ),
                "challengerPreferenceAccuracy": cohort_ranking["topChoiceAccuracy"],
                "topThreeCoverage": cohort_ranking["topThreeCoverage"],
            }
        cohort_gate = all(
            metrics["evidenceSufficient"]
            and metrics["mechanicalAccuracy"] == 1.0
            and metrics["challengerPreferenceAccuracy"] >= cohort_preference_floor
            for metrics in cohort_metrics.values()
        )
        category_metrics: dict[str, dict[str, Any]] = {}
        category_tags = sorted(
            {str(tag) for record in holdouts for tag in record.get("categoryTags") or [] if str(tag).strip()}
        )
        for tag in category_tags:
            records = [record for record in holdouts if tag in (record.get("categoryTags") or [])]
            category_ranking = self._model_ranking_metrics(model, records)
            category_metrics[tag] = {
                "decisionCount": len(records),
                "evidenceSufficient": (
                    len(records) >= minimum_evidence_mode_decisions
                    if tag in {"alignment:score_supported", "alignment:tab_only"}
                    else True
                ),
                "mechanicalAccuracy": (
                    sum(bool(record.get("mechanicalValidation", {}).get("ok")) for record in records) / len(records)
                    if records
                    else 0.0
                ),
                "challengerPreferenceAccuracy": category_ranking["topChoiceAccuracy"],
                "topThreeCoverage": category_ranking["topThreeCoverage"],
            }
        required_evidence_modes = (
            ("alignment:score_supported", "alignment:tab_only")
            if isinstance(registry.get("authoritativeDataset"), Mapping)
            else ()
        )
        evidence_mode_gate = all(
            tag in category_metrics
            and bool(category_metrics[tag]["evidenceSufficient"])
            and float(category_metrics[tag]["mechanicalAccuracy"]) == 1.0
            and float(category_metrics[tag]["challengerPreferenceAccuracy"])
            >= evidence_mode_preference_floor
            for tag in required_evidence_modes
        )
        gate_passed = (
            mechanical_accuracy == 1.0
            and preference_gate
            and cohort_gate
            and evidence_mode_gate
            and not missing_benchmarks
            and not privacy_findings
        )
        evaluation_code_digests = _rules_code_file_digests(self.repo_root)
        threshold_contract = {
            "metricVersion": "structured-input-tab-choice-v2",
            "canonicalEvaluation": canonical_evaluation,
            "inputScope": "normalized_score_events",
            "scoreImageRecognitionIncluded": False,
            "audioRecognitionIncluded": False,
            "overallPreferenceAccuracyFloor": overall_preference_floor,
            "overallPreferenceAccuracyComparison": (
                "strictly_greater_than"
                if canonical_evaluation
                else "greater_than_or_equal"
            ),
            "overallTopThreeCoverageFloor": top_three_floor,
            "cohortPreferenceAccuracyFloor": cohort_preference_floor,
            "evidenceModePreferenceAccuracyFloor": evidence_mode_preference_floor,
            "minimumDecisionCountPerCohort": minimum_cohort_decisions,
            "minimumDecisionCountPerEvidenceMode": minimum_evidence_mode_decisions,
            "mechanicalAccuracyRequired": 1.0,
            "requiredEvidenceModes": list(required_evidence_modes),
            "durationDiagnosticOnly": True,
            "thresholdAdjustmentAfterValidation": False,
        }
        evaluation = {
            "schemaVersion": TRAINING_SCHEMA_VERSION,
            "modelId": model_id,
            "evaluatedAt": _utc_now(),
            "evaluationPartition": evaluation_partition,
            "modelArtifactSha256": model_artifact_sha256,
            "validationDecisionDigest": _sha256_json(holdouts),
            "validationLineage": validation_lineage,
            "thresholdContract": threshold_contract,
            "thresholdContractDigest": _sha256_json(threshold_contract),
            "holdoutCount": len(holdouts),
            "challengerPreferenceAccuracy": challenger_accuracy,
            "structuredInputTopChoiceAccuracy": challenger_accuracy,
            "structuredInputTopThreeCoverage": top_three_coverage,
            "championModelId": champion_id,
            "championPreferenceAccuracy": champion_accuracy,
            "mechanicalAccuracy": mechanical_accuracy,
            "benchmarkCounts": benchmark_counts,
            "cohortMetrics": cohort_metrics,
            "sourceCopedentProfiles": [
                {
                    "batchId": batch_id,
                    "id": cohort_metrics[batch_id]["sourceCopedentId"],
                    "revision": cohort_metrics[batch_id]["sourceCopedentRevision"],
                    "digest": cohort_metrics[batch_id]["sourceCopedentDigest"],
                }
                for batch_id in authoritative_ids
            ],
            "categoryMetrics": category_metrics,
            "privacyFindings": privacy_findings,
            "evaluationCodeFileDigests": evaluation_code_digests,
            "gate": {
                "passed": gate_passed,
                "missingBenchmarkGroups": missing_benchmarks,
                "mechanicalValidityRequired": 1.0,
                "preferenceFloor": overall_preference_floor,
                "overallPreferenceFloor": overall_preference_floor,
                "overallPreferenceComparison": (
                    "strictly_greater_than"
                    if canonical_evaluation
                    else "greater_than_or_equal"
                ),
                "topThreeCoverageFloor": top_three_floor,
                "topThreeCoverage": top_three_coverage,
                "cohortPreferenceFloor": cohort_preference_floor,
                "evidenceModePreferenceFloor": evidence_mode_preference_floor,
                "minimumDecisionCountPerCohort": minimum_cohort_decisions,
                "minimumDecisionCountPerEvidenceMode": minimum_evidence_mode_decisions,
                "allCohortsPassed": cohort_gate,
                "requiredEvidenceModes": list(required_evidence_modes),
                "requiredEvidenceModesPassed": evidence_mode_gate,
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
            f"- Structured-input top-choice accuracy: {float(evaluation['challengerPreferenceAccuracy']):.1%}",
            f"- Structured-input top-three coverage: {float(evaluation.get('structuredInputTopThreeCoverage') or 0.0):.1%}",
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
            "## Validation categories",
            "",
            *[
                (
                    f"- {key}: {value['decisionCount']} decisions, "
                    f"{float(value['challengerPreferenceAccuracy']):.1%} preference accuracy, "
                    f"{float(value['mechanicalAccuracy']):.1%} mechanical validity"
                )
                for key, value in sorted(evaluation.get("categoryMetrics", {}).items())
            ],
            "",
            "This report contains counts and abstract model metrics only. It contains no source passages, images, or private profile data.",
        ]
        report_path = self.root / "reports" / f"{model_id}.md"
        _atomic_write_text(report_path, "\n".join(lines) + "\n")
        for batch_id in {record["batchId"] for record in self._accepted_records()}:
            _manifest, state = self._batch(batch_id)
            if (
                state["checkpoints"]["train"].get("modelId") == model_id
                or state["checkpoints"]["evaluate"].get("modelId") == model_id
            ):
                self._checkpoint(
                    state, "report", "completed", modelId=model_id, report=str(report_path.relative_to(self.root))
                )
                self._save_state(batch_id, state)
        return report_path

    def freeze_rules(self, model_id: str) -> dict[str, Any]:
        """Freeze the exact validated rules contract before either sealed test opens."""

        registry = self._registry()
        model_meta = registry["models"].get(model_id)
        if model_meta is None or not model_meta.get("evaluation"):
            raise TrainingWorkflowError("Rules freeze requires an evaluated challenger.")
        model_path = self.root / str(model_meta["artifact"])
        evaluation_path = self.root / str(model_meta["evaluation"])
        model_artifact_sha256 = _sha256_bytes(model_path.read_bytes())
        expected_model_sha256 = str(model_meta.get("artifactSha256") or "")
        if expected_model_sha256 and model_artifact_sha256 != expected_model_sha256:
            raise TrainingWorkflowError("The frozen challenger artifact digest changed.")
        model = _read_json(model_path)
        evaluation = _read_json(evaluation_path)
        if evaluation.get("modelId") != model_id:
            raise TrainingWorkflowError("The validation evaluation targets a different model.")
        if evaluation.get("modelArtifactSha256") not in {None, model_artifact_sha256}:
            raise TrainingWorkflowError("The validation evaluation pins a different model artifact.")
        if not bool(evaluation.get("gate", {}).get("passed")):
            raise TrainingWorkflowError("Rules freeze requires a passing validation evaluation.")
        dataset = registry.get("authoritativeDataset")
        if not isinstance(dataset, Mapping) or dataset.get("status") != "active":
            raise TrainingWorkflowError("Rules freeze requires one active authoritative dataset.")
        authoritative_ids = self._authoritative_batch_ids(registry)
        if any(
            (self._batch_dir(batch_id) / "extraction" / "discovery").exists()
            for batch_id in authoritative_ids
        ):
            if (
                model_meta.get("datasetEligibility") != "complete_discovery"
                or not model_meta.get("canonicalEvaluationEligible")
                or not model.get("fullDiscoveryReviewComplete")
            ):
                raise TrainingWorkflowError(
                    "Rules freeze requires the complete-discovery canonical challenger."
                )
            expected_threshold_contract = {
                "metricVersion": "structured-input-tab-choice-v2",
                "canonicalEvaluation": True,
                "inputScope": "normalized_score_events",
                "scoreImageRecognitionIncluded": False,
                "audioRecognitionIncluded": False,
                "overallPreferenceAccuracyFloor": VALIDATION_OVERALL_PREFERENCE_FLOOR,
                "overallPreferenceAccuracyComparison": "strictly_greater_than",
                "overallTopThreeCoverageFloor": VALIDATION_TOP_THREE_COVERAGE_FLOOR,
                "cohortPreferenceAccuracyFloor": VALIDATION_COHORT_PREFERENCE_FLOOR,
                "evidenceModePreferenceAccuracyFloor": VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR,
                "minimumDecisionCountPerCohort": VALIDATION_MIN_DECISIONS_PER_COHORT,
                "minimumDecisionCountPerEvidenceMode": VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE,
                "mechanicalAccuracyRequired": 1.0,
                "requiredEvidenceModes": [
                    "alignment:score_supported",
                    "alignment:tab_only",
                ],
                "durationDiagnosticOnly": True,
                "thresholdAdjustmentAfterValidation": False,
            }
            if evaluation.get("thresholdContract") != expected_threshold_contract:
                raise TrainingWorkflowError(
                    "The validation evaluation does not pin the predeclared threshold contract."
                )
            if not evaluation.get("validationDecisionDigest"):
                raise TrainingWorkflowError(
                    "The validation evaluation lacks an immutable decision digest."
                )
        if sorted(model.get("sourceBatchIds") or []) != sorted(authoritative_ids):
            raise TrainingWorkflowError("The challenger does not include every authoritative batch.")
        expected_model_profiles = sorted(
            (
                {
                    "batchId": str(entry["batchId"]),
                    "id": str(entry["sourceCopedentId"]),
                    "revision": int(entry["sourceCopedentRevision"]),
                    "digest": entry.get("sourceCopedentDigest"),
                }
                for entry in dataset.get("batches") or []
            ),
            key=lambda item: item["batchId"],
        )
        if model.get("sourceCopedentProfiles") != expected_model_profiles:
            raise TrainingWorkflowError("The challenger does not pin every authoritative source-copedent profile.")

        validation_metrics: dict[str, str] = {}
        validation_extraction_contracts: dict[str, dict[str, Any]] = {}
        sealed_cohorts: list[dict[str, Any]] = []
        model_rights_digests = {
            str(batch_id): str(digest) for batch_id, digest in (model.get("rightsAuthorizationDigests") or {}).items()
        }
        for batch_id in authoritative_ids:
            self._require_complete_extraction_review(batch_id, "validation")
            self._require_extraction_acceptance(batch_id, "validation")
            metrics_path = self._batch_dir(batch_id) / "extraction/validation/review/review-metrics.json"
            if metrics_path.exists():
                validation_metrics[batch_id] = _sha256_json(_read_json(metrics_path))
            extraction_summary_path = self._batch_dir(batch_id) / "extraction/validation/summary.json"
            if extraction_summary_path.parent.exists() and not extraction_summary_path.exists():
                raise TrainingWorkflowError(f"Validation extraction summary is missing for {batch_id}.")
            if extraction_summary_path.exists():
                extraction_summary = _read_json(extraction_summary_path)
                validation_extraction_contracts[batch_id] = {
                    "runDigest": extraction_summary.get("runDigest"),
                    "schemaVersion": extraction_summary.get("schemaVersion"),
                    "knowledgeSchemaVersion": extraction_summary.get("knowledgeSchemaVersion"),
                    "extractorVersion": extraction_summary.get("extractorVersion"),
                    "decisionDerivationVersion": extraction_summary.get("decisionDerivationVersion"),
                    "ocrReaderContract": extraction_summary.get("ocrReaderContract"),
                    "omrReaderContract": extraction_summary.get("omrReaderContract"),
                    "tabReaderContract": extraction_summary.get("tabReaderContract"),
                }
            split = self._split_summary(batch_id)
            if split is None or split.get("status") != "sealed_unopened":
                raise TrainingWorkflowError("Rules freeze requires every sealed test to remain unopened.")
            sealed_status = _read_json(self._batch_dir(batch_id) / "sealed-test/ground-truth-status.json")
            if sealed_status.get("status") != "pending" or sealed_status.get("openedAt") is not None:
                raise TrainingWorkflowError("A sealed test was opened before the rules freeze.")
            manifest, _state = self._batch(batch_id)
            rights = self._rights_and_access(batch_id)
            rights_digest = str(rights.get("recordDigest") or "")
            if not rights_digest or model_rights_digests.get(batch_id) != rights_digest:
                raise TrainingWorkflowError(
                    f"The current rights authorization differs from the challenger contract: {batch_id}."
                )
            sealed_cohorts.append(
                {
                    "batchId": batch_id,
                    "partitionDigest": split["partitionDigest"],
                    "testCount": int(split["counts"]["test"]),
                    "sourceCopedentId": manifest["sourceCopedentId"],
                    "sourceCopedentRevision": int(manifest.get("sourceCopedentRevision") or 1),
                    "sourceCopedentDigest": manifest.get("sourceCopedentDigest"),
                    "rightsAuthorizationDigest": rights_digest,
                    "validationExtractionContractDigest": (
                        _sha256_json(validation_extraction_contracts[batch_id])
                        if batch_id in validation_extraction_contracts
                        else None
                    ),
                }
            )

        code_digests = _rules_code_file_digests(self.repo_root)
        if model.get("trainingCodeFileDigests") != code_digests:
            raise TrainingWorkflowError("Rules code changed after challenger training; retrain before freezing.")
        if evaluation.get("evaluationCodeFileDigests") != code_digests:
            raise TrainingWorkflowError("Rules code changed after validation evaluation; re-evaluate before freezing.")
        from pocketsteel.amazing_tablature_decisions import DECISION_DERIVATION_VERSION
        from pocketsteel.amazing_tablature_extraction import (
            EXTRACTION_SCHEMA_VERSION,
            EXTRACTOR_VERSION,
            KNOWLEDGE_SCHEMA_VERSION,
        )

        contract = {
            "schemaVersion": RULES_FREEZE_SCHEMA_VERSION,
            "authoritativeDatasetId": dataset["datasetId"],
            "authoritativeDatasetDigest": dataset["datasetDigest"],
            "modelId": model_id,
            "modelArtifactDigest": _sha256_json(model),
            "modelArtifactSha256": model_artifact_sha256,
            "validationEvaluationDigest": _sha256_json(evaluation),
            "validationEvaluationFileSha256": _sha256_bytes(
                evaluation_path.read_bytes()
            ),
            "validationDecisionDigest": evaluation.get("validationDecisionDigest"),
            "validationMetricsDigests": validation_metrics,
            "validationExtractionContracts": validation_extraction_contracts,
            "rightsAuthorizationDigests": model_rights_digests,
            "codeRevision": _git_revision(self.repo_root),
            "codeFileDigests": code_digests,
            "contracts": {
                "trainingSchemaVersion": TRAINING_SCHEMA_VERSION,
                "annotationSchemaVersion": ANNOTATION_SCHEMA_VERSION,
                "featureSchemaVersion": FEATURE_SCHEMA_VERSION,
                "extractionSchemaVersion": EXTRACTION_SCHEMA_VERSION,
                "knowledgeSchemaVersion": KNOWLEDGE_SCHEMA_VERSION,
                "extractorVersion": EXTRACTOR_VERSION,
                "decisionDerivationVersion": DECISION_DERIVATION_VERSION,
                "mechanicalValidatorVersion": "source-copedent-mechanics-v2",
                "musicalValidatorVersion": "score-tab-alignment-v2",
            },
            "sealedModelEvaluationPolicy": {
                "metricVersion": "sealed-structured-input-tab-choice-v2",
                "preferenceAccuracyFloor": float(
                    evaluation.get("gate", {}).get("overallPreferenceFloor")
                    or evaluation.get("gate", {}).get("preferenceFloor")
                    or VALIDATION_OVERALL_PREFERENCE_FLOOR
                ),
                "preferenceAccuracyComparison": "strictly_greater_than",
                "topThreeCoverageFloor": float(
                    evaluation.get("gate", {}).get("topThreeCoverageFloor")
                    or VALIDATION_TOP_THREE_COVERAGE_FLOOR
                ),
                "cohortPreferenceAccuracyFloor": float(
                    evaluation.get("gate", {}).get("cohortPreferenceFloor")
                    or VALIDATION_COHORT_PREFERENCE_FLOOR
                ),
                "evidenceModePreferenceAccuracyFloor": float(
                    evaluation.get("gate", {}).get("evidenceModePreferenceFloor")
                    or VALIDATION_EVIDENCE_MODE_PREFERENCE_FLOOR
                ),
                "minimumDecisionCountPerCohort": int(
                    evaluation.get("gate", {}).get("minimumDecisionCountPerCohort")
                    or VALIDATION_MIN_DECISIONS_PER_COHORT
                ),
                "minimumDecisionCountPerEvidenceMode": int(
                    evaluation.get("gate", {}).get("minimumDecisionCountPerEvidenceMode")
                    or VALIDATION_MIN_DECISIONS_PER_EVIDENCE_MODE
                ),
                "requiresScoreBackedDecisionsOverall": True,
                "requiresTabOnlyDecisionsOverall": True,
            },
            "sealedTestCohorts": sealed_cohorts,
        }
        rules_engine_digest = _sha256_json(contract)
        freeze_id = f"atrf-{rules_engine_digest[:16]}"
        existing_meta = registry["rulesFreezes"].get(freeze_id)
        if existing_meta is not None:
            return _read_json(self.root / str(existing_meta["artifact"]))
        freeze = {
            **contract,
            "freezeId": freeze_id,
            "rulesEngineDigest": rules_engine_digest,
            "frozenAt": _utc_now(),
            "status": "frozen_tests_unopened",
        }
        freeze_dir = self.root / "rules-freezes"
        freeze_dir.mkdir(parents=True, exist_ok=True)
        _make_private(freeze_dir, directory=True)
        freeze_path = freeze_dir / f"{freeze_id}.json"
        _write_json(freeze_path, freeze)
        _make_private(freeze_path)
        registry["rulesFreezes"][freeze_id] = {
            "artifact": str(freeze_path.relative_to(self.root)),
            "modelId": model_id,
            "rulesEngineDigest": rules_engine_digest,
            "status": freeze["status"],
            "createdAt": freeze["frozenAt"],
        }
        self._save_registry(registry)
        return freeze

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

    def deactivate_channel(
        self,
        *,
        channel: str,
        approval_reference: str,
    ) -> dict[str, Any]:
        """Clear an obsolete runtime channel without selecting a replacement."""

        if channel not in {"beta", "stable"}:
            raise TrainingWorkflowError("Deactivation channel must be beta or stable.")
        if not approval_reference.strip():
            raise TrainingWorkflowError(
                "Channel deactivation requires an explicit creator approval reference."
            )
        registry = self._registry()
        previous = registry["channels"].get(channel)
        if previous is None:
            return {"channel": channel, "modelId": None, "previousModelId": None}
        registry["channels"][channel] = None
        registry["rollbackHistory"].append(
            {
                "action": "deactivate",
                "channel": channel,
                "fromModelId": previous,
                "toModelId": None,
                "approvalReference": approval_reference.strip(),
                "at": _utc_now(),
            }
        )
        self._refresh_model_states(registry)
        self._save_registry(registry)
        return {"channel": channel, "modelId": None, "previousModelId": previous}

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
            entry.get("fromModelId") for entry in registry["rollbackHistory"] if entry.get("channel") == channel
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
        rights = self._rights_and_access(batch_id)
        payload = {
            "batchId": batch_id,
            "sourceCopedentId": manifest["sourceCopedentId"],
            "sourceCopedentConfidence": manifest["sourceCopedentConfidence"],
            "sourceCopedentRevision": manifest.get("sourceCopedentRevision", meta.get("sourceCopedentRevision", 1)),
            "sourceCopedentDigest": manifest.get("sourceCopedentDigest", meta.get("sourceCopedentDigest")),
            "evidenceType": manifest["evidenceType"],
            "immutableDigest": manifest["immutableDigest"],
            "sourceCopedentEvidenceCount": len(manifest.get("sourceCopedentEvidence", [])),
            "lifecycleStatus": meta.get("lifecycleStatus", state.get("lifecycleStatus", "active")),
            "supersededByBatchId": meta.get("supersededByBatchId"),
            "counts": state["counts"],
            "checkpoints": state["checkpoints"],
            "rightsAndAccess": {
                "rightsStatus": rights.get("rightsStatus", "unknown"),
                "reviewStatus": rights.get("reviewStatus", "pending"),
                "allowedUses": rights.get("allowedUses", {}),
                "recordDigest": rights.get("recordDigest"),
            },
        }
        if split_summary is not None:
            payload["partition"] = {
                "schemaVersion": split_summary["schemaVersion"],
                "status": split_summary["status"],
                "partitionDigest": split_summary["partitionDigest"],
                "groupingReviewStatus": split_summary.get("groupingReviewStatus", "provisional_structural"),
                "pageLevelUnits": bool(split_summary.get("pageLevelUnits", False)),
                "semanticGroupCount": int(split_summary.get("semanticGroupCount", 0)),
                "semanticGroupDigest": split_summary.get("semanticGroupDigest"),
                "stratificationStatus": split_summary.get(
                    "stratificationStatus",
                    {
                        "sourceAndImageStructure": "completed",
                        "pageTypeAndMusicalContent": "pending_independent_review",
                    },
                ),
                "independentReview": split_summary.get("independentReview"),
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
            "authoritativeDataset": registry.get("authoritativeDataset"),
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
    "SEMANTIC_GROUP_SCHEMA_VERSION",
    "SPLIT_SCHEMA_VERSION",
    "TRAINING_SCHEMA_VERSION",
    "AmazingTablatureTrainingStore",
    "TrainingWorkflowError",
]
