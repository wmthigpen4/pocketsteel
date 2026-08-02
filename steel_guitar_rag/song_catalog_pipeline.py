"""Internal candidate, rights, and publication gates for Play Songs.

This module is deliberately separate from the public Song Practice catalog.
Candidates may be incomplete, rejected, or commercially sensitive and must
never be returned by the public API merely because they exist in this registry.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


CANDIDATE_REGISTRY_SCHEMA = "song_candidate_registry_v1"
CANDIDATE_SCHEMA = "song_candidate_v1"
RIGHTS_REGISTRY_SCHEMA = "song_rights_registry_v1"
RIGHTS_SCHEMA = "song_rights_record_v1"
REPORT_SCHEMA = "song_catalog_curation_report_v1"

GATE_ORDER = (
    "screening",
    "rights",
    "master",
    "timeline",
    "e9Lesson",
    "qa",
    "publication",
)
STATE_AFTER_GATE = {
    "screening": "screened",
    "rights": "rights_cleared",
    "master": "master_approved",
    "timeline": "timeline_authored",
    "e9Lesson": "e9_lesson_authored",
    "qa": "qa_passed",
    "publication": "published",
}
ALLOWED_STATES = {
    "identified",
    "screened",
    "rights_inquiry",
    "rights_cleared",
    "master_approved",
    "timeline_authored",
    "e9_lesson_authored",
    "qa_passed",
    "published",
    "on_hold",
    "rejected",
}
ALLOWED_GATE_STATUSES = {"pending", "approved", "rejected"}
ALLOWED_RIGHTS_STATUSES = {"pending", "verified_candidate_use", "publication_approved", "rejected"}
REQUIRED_USE_KEYS = {
    "bundleMaster",
    "onDemandPlayback",
    "synchronizedInstruction",
    "displayLyrics",
    "derivedChordAndTab",
    "loopAndSeek",
    "speedChange",
    "offlineCache",
    "artistMarketing",
}

_RESOURCE_DIR = Path(__file__).with_name("resources") / "song_catalog"
_CANDIDATES_PATH = _RESOURCE_DIR / "candidates.json"
_RIGHTS_PATH = _RESOURCE_DIR / "rights_records.json"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SongCatalogPipelineError(ValueError):
    """Raised when the internal candidate registry violates its contract."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SongCatalogPipelineError(f"{path.name} is unavailable or invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SongCatalogPipelineError(f"{path.name} must contain a JSON object")
    return payload


def load_candidate_registry() -> dict[str, Any]:
    return _load_json(_CANDIDATES_PATH)


def load_rights_registry() -> dict[str, Any]:
    return _load_json(_RIGHTS_PATH)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _approval_reference(record: Mapping[str, Any]) -> str:
    approval = record.get("approval")
    return str(approval.get("reference") or "") if isinstance(approval, Mapping) else ""


def validate_rights_record(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    record_id = str(record.get("id") or "<missing-id>")
    required_strings = (
        "id",
        "title",
        "compositionStatus",
        "masterStatus",
        "licenseLabel",
        "sourceUrl",
        "territories",
        "term",
        "attribution",
    )
    if record.get("schemaVersion") != RIGHTS_SCHEMA:
        errors.append(f"rights {record_id}: schemaVersion must be {RIGHTS_SCHEMA}")
    for field in required_strings:
        if not _nonempty(record.get(field)):
            errors.append(f"rights {record_id}: {field} is required")
    allowed_uses = record.get("allowedUses")
    if not isinstance(allowed_uses, Mapping):
        errors.append(f"rights {record_id}: allowedUses must be an object")
    else:
        missing = REQUIRED_USE_KEYS - set(allowed_uses)
        if missing:
            errors.append(f"rights {record_id}: missing allowed uses {sorted(missing)}")
        for key in REQUIRED_USE_KEYS & set(allowed_uses):
            if allowed_uses[key] not in {True, False, "not_applicable"}:
                errors.append(f"rights {record_id}: allowedUses.{key} must be boolean or not_applicable")
    approval = record.get("approval")
    if not isinstance(approval, Mapping):
        errors.append(f"rights {record_id}: approval is required")
    else:
        status = approval.get("status")
        if status not in ALLOWED_RIGHTS_STATUSES:
            errors.append(f"rights {record_id}: unsupported approval status {status!r}")
        if status in {"verified_candidate_use", "publication_approved", "rejected"}:
            for field in ("reviewedOn", "reviewer", "reference"):
                if not _nonempty(approval.get(field)):
                    errors.append(f"rights {record_id}: approval.{field} is required for {status}")
    document_path = record.get("localDocumentPath")
    document_digest = record.get("localDocumentSha256")
    if document_path or document_digest:
        if not _nonempty(document_path) or not _nonempty(document_digest) or not _SHA256_RE.fullmatch(str(document_digest)):
            errors.append(f"rights {record_id}: local document path and SHA-256 must be supplied together")
        else:
            asset = (_REPO_ROOT / str(document_path)).resolve()
            try:
                asset.relative_to(_REPO_ROOT)
                actual = hashlib.sha256(asset.read_bytes()).hexdigest()
            except (OSError, ValueError):
                errors.append(f"rights {record_id}: local document cannot be read")
            else:
                if actual != document_digest:
                    errors.append(f"rights {record_id}: local document SHA-256 does not match")
    return errors


def _derived_state(candidate: Mapping[str, Any]) -> str:
    gates = candidate.get("gates")
    if not isinstance(gates, Mapping):
        return "identified"
    if any(
        isinstance(gates.get(gate_name), Mapping) and gates[gate_name].get("status") == "rejected"
        for gate_name in GATE_ORDER
    ):
        return "rejected"
    last_state = "identified"
    for gate_name in GATE_ORDER:
        gate = gates.get(gate_name)
        status = gate.get("status") if isinstance(gate, Mapping) else None
        if status == "approved":
            last_state = STATE_AFTER_GATE[gate_name]
            continue
        if status == "rejected":
            return "rejected"
        break
    return last_state


def validate_candidate(candidate: Mapping[str, Any], rights_by_id: Mapping[str, Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    candidate_id = str(candidate.get("id") or "<missing-id>")
    if candidate.get("schemaVersion") != CANDIDATE_SCHEMA:
        errors.append(f"candidate {candidate_id}: schemaVersion must be {CANDIDATE_SCHEMA}")
    for field in ("id", "title", "artist", "acquisitionLane", "teachingHypothesis", "rightsRecordId", "state"):
        if not _nonempty(candidate.get(field)):
            errors.append(f"candidate {candidate_id}: {field} is required")
    state = candidate.get("state")
    if state not in ALLOWED_STATES:
        errors.append(f"candidate {candidate_id}: unsupported state {state!r}")
    rights_record_id = str(candidate.get("rightsRecordId") or "")
    rights_record = rights_by_id.get(rights_record_id)
    if rights_record is None:
        errors.append(f"candidate {candidate_id}: rights record {rights_record_id!r} does not exist")

    score = candidate.get("score")
    if not isinstance(score, Mapping):
        errors.append(f"candidate {candidate_id}: score is required")
    else:
        dimensions = {
            "learnerDemand": 0.30,
            "steelTeachingValue": 0.20,
            "recordingSuitability": 0.20,
            "rightsFeasibility": 0.20,
            "authoringCost": 0.10,
        }
        for field in dimensions:
            value = score.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
                errors.append(f"candidate {candidate_id}: score.{field} must be an integer from 0 to 100")

    recording = candidate.get("recording")
    if not isinstance(recording, Mapping):
        errors.append(f"candidate {candidate_id}: recording is required")
    else:
        for field in ("sourceUrl", "checksumSha256", "codec", "durationMs"):
            if recording.get(field) in {None, ""}:
                errors.append(f"candidate {candidate_id}: recording.{field} is required")
        if not _SHA256_RE.fullmatch(str(recording.get("checksumSha256") or "")):
            errors.append(f"candidate {candidate_id}: recording.checksumSha256 must be lowercase SHA-256")
        duration = recording.get("durationMs")
        if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            errors.append(f"candidate {candidate_id}: recording.durationMs must be positive")
        asset_path = recording.get("assetPath")
        if asset_path:
            asset = (_REPO_ROOT / str(asset_path)).resolve()
            try:
                asset.relative_to(_REPO_ROOT)
                actual = hashlib.sha256(asset.read_bytes()).hexdigest()
            except (OSError, ValueError):
                errors.append(f"candidate {candidate_id}: recording asset cannot be read")
            else:
                if actual != recording.get("checksumSha256"):
                    errors.append(f"candidate {candidate_id}: recording asset SHA-256 does not match")

    gates = candidate.get("gates")
    if not isinstance(gates, Mapping):
        errors.append(f"candidate {candidate_id}: gates must be an object")
    else:
        if set(gates) != set(GATE_ORDER):
            errors.append(f"candidate {candidate_id}: gates must contain exactly {list(GATE_ORDER)}")
        encountered_open_gate = False
        for gate_name in GATE_ORDER:
            gate = gates.get(gate_name)
            if not isinstance(gate, Mapping):
                continue
            status = gate.get("status")
            if status not in ALLOWED_GATE_STATUSES:
                errors.append(f"candidate {candidate_id}: gate {gate_name} has unsupported status {status!r}")
            if encountered_open_gate and status == "approved":
                errors.append(f"candidate {candidate_id}: gate {gate_name} cannot be approved before earlier gates")
            if status != "approved":
                encountered_open_gate = True
            if status in {"approved", "rejected"}:
                if not _nonempty(gate.get("reviewer")) or not _nonempty(gate.get("reviewedOn")):
                    errors.append(f"candidate {candidate_id}: gate {gate_name} requires reviewer and reviewedOn")
                evidence = gate.get("evidence")
                if not isinstance(evidence, list) or not evidence or not all(_nonempty(item) for item in evidence):
                    errors.append(f"candidate {candidate_id}: gate {gate_name} requires evidence")

    derived_state = _derived_state(candidate)
    if state not in {"on_hold", "rights_inquiry"} and state != derived_state:
        errors.append(f"candidate {candidate_id}: state {state!r} does not match gate-derived state {derived_state!r}")
    if state == "published":
        if not _nonempty(candidate.get("publicationProjectId")):
            errors.append(f"candidate {candidate_id}: published candidate requires publicationProjectId")
        if rights_record and rights_record.get("approval", {}).get("status") != "publication_approved":
            errors.append(f"candidate {candidate_id}: published candidate requires publication-approved rights")
        if not _approval_reference(rights_record or {}):
            errors.append(f"candidate {candidate_id}: published rights require immutable approval reference")
    return errors


def validate_registries(
    candidate_registry: Mapping[str, Any] | None = None,
    rights_registry: Mapping[str, Any] | None = None,
) -> list[str]:
    candidate_registry = candidate_registry or load_candidate_registry()
    rights_registry = rights_registry or load_rights_registry()
    errors: list[str] = []
    if candidate_registry.get("schemaVersion") != CANDIDATE_REGISTRY_SCHEMA:
        errors.append(f"candidate registry schemaVersion must be {CANDIDATE_REGISTRY_SCHEMA}")
    if rights_registry.get("schemaVersion") != RIGHTS_REGISTRY_SCHEMA:
        errors.append(f"rights registry schemaVersion must be {RIGHTS_REGISTRY_SCHEMA}")
    candidates = candidate_registry.get("candidates")
    rights_records = rights_registry.get("rightsRecords")
    if not isinstance(candidates, list):
        errors.append("candidate registry candidates must be a list")
        candidates = []
    if not isinstance(rights_records, list):
        errors.append("rights registry rightsRecords must be a list")
        rights_records = []

    rights_by_id: dict[str, Mapping[str, Any]] = {}
    for record in rights_records:
        if not isinstance(record, Mapping):
            errors.append("rights registry contains a non-object record")
            continue
        record_id = str(record.get("id") or "")
        if record_id in rights_by_id:
            errors.append(f"duplicate rights record id {record_id!r}")
        rights_by_id[record_id] = record
        errors.extend(validate_rights_record(record))

    candidate_ids: set[str] = set()
    publication_ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            errors.append("candidate registry contains a non-object candidate")
            continue
        candidate_id = str(candidate.get("id") or "")
        if candidate_id in candidate_ids:
            errors.append(f"duplicate candidate id {candidate_id!r}")
        candidate_ids.add(candidate_id)
        publication_id = str(candidate.get("publicationProjectId") or "")
        if publication_id and publication_id in publication_ids:
            errors.append(f"duplicate publication project id {publication_id!r}")
        publication_ids.add(publication_id) if publication_id else None
        errors.extend(validate_candidate(candidate, rights_by_id))
    return errors


def _weighted_score(candidate: Mapping[str, Any]) -> int | None:
    score = candidate.get("score")
    if not isinstance(score, Mapping):
        return None
    weights = {
        "learnerDemand": 0.30,
        "steelTeachingValue": 0.20,
        "recordingSuitability": 0.20,
        "rightsFeasibility": 0.20,
        "authoringCost": 0.10,
    }
    try:
        return round(sum(int(score[field]) * weight for field, weight in weights.items()))
    except (KeyError, TypeError, ValueError):
        return None


def build_curation_report() -> dict[str, Any]:
    candidates_payload = load_candidate_registry()
    rights_payload = load_rights_registry()
    errors = validate_registries(candidates_payload, rights_payload)
    rights_by_id = {
        str(record.get("id")): record
        for record in rights_payload.get("rightsRecords") or []
        if isinstance(record, Mapping)
    }
    rows: list[dict[str, Any]] = []
    for candidate in candidates_payload.get("candidates") or []:
        if not isinstance(candidate, Mapping):
            continue
        gates = candidate.get("gates") if isinstance(candidate.get("gates"), Mapping) else {}
        missing = [name for name in GATE_ORDER if gates.get(name, {}).get("status") != "approved"]
        rejected = [name for name in GATE_ORDER if gates.get(name, {}).get("status") == "rejected"]
        next_gate = None if rejected else next(
            (name for name in GATE_ORDER if gates.get(name, {}).get("status") == "pending"),
            None,
        )
        rights = rights_by_id.get(str(candidate.get("rightsRecordId") or ""), {})
        next_gate_notes = ""
        if next_gate and isinstance(gates.get(next_gate), Mapping):
            next_gate_notes = str(gates[next_gate].get("notes") or "")
        rows.append(
            {
                "id": candidate.get("id"),
                "title": candidate.get("title"),
                "artist": candidate.get("artist"),
                "state": candidate.get("state"),
                "score": _weighted_score(candidate),
                "rightsStatus": rights.get("approval", {}).get("status"),
                "missingGates": missing,
                "rejectedGates": rejected,
                "nextGate": next_gate,
                "nextGateNotes": next_gate_notes,
                "publicProjectId": candidate.get("publicationProjectId") if candidate.get("state") == "published" else None,
            }
        )
    rows.sort(key=lambda row: (row["state"] != "published", -(row["score"] or 0), str(row["title"])))
    return {
        "schemaVersion": REPORT_SCHEMA,
        "valid": not errors,
        "errors": errors,
        "summary": {
            "total": len(rows),
            "published": sum(row["state"] == "published" for row in rows),
            "active": sum(row["state"] not in {"published", "rejected"} for row in rows),
            "rejected": sum(row["state"] == "rejected" for row in rows),
        },
        "candidates": rows,
    }


def published_project_ids() -> frozenset[str]:
    """Return only projects that passed every internal publication gate."""

    errors = validate_registries()
    if errors:
        raise SongCatalogPipelineError("song catalog registries are invalid: " + "; ".join(errors))
    return frozenset(
        str(candidate["publicationProjectId"])
        for candidate in load_candidate_registry()["candidates"]
        if candidate.get("state") == "published" and _derived_state(candidate) == "published"
    )


def format_curation_report(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "Play Songs catalog curation",
        (
            f"Registry: {'PASS' if report.get('valid') else 'FAIL'} · "
            f"{summary.get('published', 0)} published · {summary.get('active', 0)} active · "
            f"{summary.get('rejected', 0)} rejected"
        ),
    ]
    for row in report.get("candidates") or []:
        next_gate = row.get("nextGate") or ("none" if row.get("state") == "published" else "rejected")
        lines.append(
            f"- {row.get('title')} — {row.get('state')} — score {row.get('score')} — next: {next_gate}"
        )
        if row.get("nextGateNotes"):
            lines.append(f"  {row['nextGateNotes']}")
    for error in report.get("errors") or []:
        lines.append(f"ERROR: {error}")
    return "\n".join(lines)
