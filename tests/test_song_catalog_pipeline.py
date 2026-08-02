from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

from steel_guitar_rag.song_catalog_pipeline import (
    CANDIDATE_SCHEMA,
    GATE_ORDER,
    RIGHTS_SCHEMA,
    build_curation_report,
    load_candidate_registry,
    load_rights_registry,
    published_project_ids,
    validate_candidate,
    validate_registries,
)
from steel_guitar_rag.song_practice import song_practice_catalog


REPO_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_DIR = REPO_ROOT / "steel_guitar_rag" / "resources" / "song_catalog"


def test_versioned_candidate_and_rights_registries_validate() -> None:
    candidates = load_candidate_registry()
    rights = load_rights_registry()
    assert validate_registries(candidates, rights) == []
    assert all(candidate["schemaVersion"] == CANDIDATE_SCHEMA for candidate in candidates["candidates"])
    assert all(record["schemaVersion"] == RIGHTS_SCHEMA for record in rights["rightsRecords"])
    for name in ("song_candidate.schema.json", "rights_record.schema.json"):
        schema = json.loads((RESOURCE_DIR / name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_curation_report_names_every_missing_gate_without_publishing_candidates() -> None:
    report = build_curation_report()
    assert report["valid"] is True
    assert report["summary"] == {"total": 3, "published": 1, "active": 1, "rejected": 1}
    by_id = {candidate["id"]: candidate for candidate in report["candidates"]}
    assert by_id["amazing-grace-kevin-macleod-lesson"]["missingGates"] == []
    assert by_id["amazing-grace-kevin-macleod-lesson"]["publicProjectId"] == "amazing-grace-guided"
    assert by_id["hard-times-grant-barrett-candidate"]["nextGate"] == "master"
    assert "musical audition" in by_id["hard-times-grant-barrett-candidate"]["nextGateNotes"]
    assert by_id["hard-times-grant-barrett-candidate"]["missingGates"] == [
        "master", "timeline", "e9Lesson", "qa", "publication"
    ]
    assert by_id["when-the-saints-synthetic-preview"]["rejectedGates"] == ["master"]
    assert by_id["when-the-saints-synthetic-preview"]["nextGate"] is None


def test_public_catalog_exactly_matches_published_candidates() -> None:
    published_candidates = {
        candidate["publicationProjectId"]
        for candidate in load_candidate_registry()["candidates"]
        if candidate["state"] == "published"
    }
    public_projects = {track["projectId"] for track in song_practice_catalog()["tracks"]}
    assert public_projects == published_candidates == {"amazing-grace-guided"}
    assert published_project_ids() == frozenset({"amazing-grace-guided"})
    assert all(track["playAlongReady"] is True for track in song_practice_catalog()["tracks"])


def test_amazing_grace_is_sha_pinned_golden_publication_fixture() -> None:
    candidate = next(
        item for item in load_candidate_registry()["candidates"]
        if item["id"] == "amazing-grace-kevin-macleod-lesson"
    )
    assert candidate["state"] == "published"
    assert all(candidate["gates"][gate]["status"] == "approved" for gate in GATE_ORDER)
    asset = REPO_ROOT / candidate["recording"]["assetPath"]
    import hashlib
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == candidate["recording"]["checksumSha256"]


def test_new_open_recording_stops_at_musical_master_approval() -> None:
    candidate = next(
        item for item in load_candidate_registry()["candidates"]
        if item["id"] == "hard-times-grant-barrett-candidate"
    )
    assert candidate["state"] == "rights_cleared"
    assert candidate["recording"]["checksumSha256"] == "1b426cde50c02809a4463403b2076dae43df64944dbce25880fbb23daab579a8"
    assert candidate["recording"]["durationMs"] == 145946
    assert candidate["gates"]["rights"]["status"] == "approved"
    assert candidate["gates"]["master"]["status"] == "pending"
    assert "musical audition" in candidate["gates"]["master"]["notes"]
    assert "publicationProjectId" not in candidate


def test_candidate_validation_rejects_gate_skips_and_unapproved_publication() -> None:
    candidates = load_candidate_registry()["candidates"]
    rights = load_rights_registry()["rightsRecords"]
    rights_by_id = {record["id"]: record for record in rights}
    candidate = copy.deepcopy(next(item for item in candidates if item["id"] == "hard-times-grant-barrett-candidate"))
    candidate["gates"]["timeline"] = {
        "status": "approved",
        "reviewer": "Invalid shortcut",
        "reviewedOn": "2026-08-02",
        "evidence": ["No master approval"],
    }
    assert any("cannot be approved before earlier gates" in error for error in validate_candidate(candidate, rights_by_id))

    candidate = copy.deepcopy(next(item for item in candidates if item["id"] == "amazing-grace-kevin-macleod-lesson"))
    candidate["rightsRecordId"] = "hard-times-grant-barrett-cc-by-3"
    assert any("publication-approved rights" in error for error in validate_candidate(candidate, rights_by_id))


def test_catalog_pipeline_cli_reports_and_checks_registry() -> None:
    result = subprocess.run(
        [str(REPO_ROOT / ".venv" / "bin" / "python"), "scripts/song_catalog_pipeline.py", "--check", "--format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["valid"] is True
    assert report["summary"]["published"] == 1
