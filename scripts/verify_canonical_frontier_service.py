#!/usr/bin/env python3
"""Fail closed unless the external canonical-frontier service matches its bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


INDEX_RELATIVE = Path("rag-evaluation/index/steel-forum-passages-v1-hybrid-v1")
TIERED_POLICY_RELATIVE = Path("rag-evaluation/training/canonical-tiered-reranker-grid-policy-v856.json")


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path.name}.")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_required(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe bundle path: {relative}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Bundle path escapes the service root: {relative}") from exc
    return resolved


def require_local_path(root: Path, raw: str, label: str) -> Path:
    path = Path(raw).expanduser().resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} is outside the verified service root.") from exc
    if not path.exists() or not os.access(path, os.R_OK):
        raise ValueError(f"{label} is missing or unreadable.")
    return path


def verify_bundle(service_root: Path, manifest_path: Path) -> dict[str, Any]:
    root = service_root.expanduser().resolve()
    manifest_file = manifest_path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Canonical-frontier service root is missing.")
    manifest = load_object(manifest_file)
    expected_keys = {
        "schema_version", "bundle_version", "service_entrypoint", "candidate",
        "expected_index_passages", "required_files",
    }
    required = manifest.get("required_files")
    if (
        set(manifest) != expected_keys
        or manifest.get("schema_version") != 1
        or manifest.get("bundle_version") != "canonical-frontier-service-bundle-v1034"
        or manifest.get("service_entrypoint") != "canonical_frontier_http_api_v2.py"
        or not isinstance(required, dict)
        or len(required) < 50
    ):
        raise ValueError("Canonical-frontier bundle manifest is invalid.")
    mismatches: list[str] = []
    for relative, expected in sorted(required.items()):
        path = resolve_required(root, str(relative))
        if (
            not path.is_file()
            or path.is_symlink()
            or not isinstance(expected, str)
            or len(expected) != 64
            or sha256(path) != expected
        ):
            mismatches.append(str(relative))
    if mismatches:
        preview = ", ".join(mismatches[:5])
        suffix = "..." if len(mismatches) > 5 else ""
        raise ValueError(f"Canonical-frontier bundle fingerprint mismatch: {preview}{suffix}")

    candidate_relative = str(manifest["candidate"])
    if candidate_relative not in required:
        raise ValueError("Frozen candidate is absent from the required-file inventory.")
    candidate = load_object(resolve_required(root, candidate_relative))
    if (
        candidate.get("status") != "owner_corrected_default_off_candidate_implementation_ready"
        or candidate.get("protected_holdout_cases_used") != 0
        or candidate.get("runtime_activation_authorized") is not False
        or candidate.get("deployment_authorized") is not False
        or not all((candidate.get("confirmed_corrected_answer") or {}).get("checks", {}).values())
    ):
        raise ValueError("Frozen candidate is not the owner-corrected default-off candidate.")

    index_root = root / INDEX_RELATIVE
    index_manifest = load_object(index_root / "manifest.json")
    progress = load_object(index_root / "vector-embedding-progress.json")
    expected_count = int(manifest["expected_index_passages"])
    vector = index_manifest.get("vector") or {}
    lexical = index_manifest.get("lexical") or {}
    if (
        index_manifest.get("status") != "ready"
        or index_manifest.get("corpus_version") != "steel-forum-passages-v1"
        or index_manifest.get("source_id_scheme") != "steel-passage-v1"
        or index_manifest.get("protected_holdout_used") is not False
        or int(lexical.get("count") or 0) != expected_count
        or int(vector.get("count") or 0) != expected_count
        or int(progress.get("expected_passages") or 0) != expected_count
        or int(progress.get("processed_passages") or 0) != expected_count
        or int(progress.get("collection_count") or 0) != expected_count
        or progress.get("protected_holdout_cases_used") != 0
    ):
        raise ValueError("Canonical lexical/vector index is incomplete or mismatched.")
    require_local_path(root, str(lexical.get("database") or ""), "lexical database")
    require_local_path(root, str(vector.get("path") or ""), "vector index")
    tiered = load_object(root / TIERED_POLICY_RELATIVE)
    require_local_path(
        root, str(tiered.get("group_expansion_index") or ""), "group-expansion index",
    )
    entrypoint = resolve_required(root, str(manifest["service_entrypoint"]))
    if entrypoint.name != "canonical_frontier_http_api_v2.py":
        raise ValueError("Canonical-frontier entrypoint is invalid.")
    return {
        "status": "canonical_frontier_service_bundle_verified",
        "bundle_version": manifest["bundle_version"],
        "verified_files": len(required),
        "index_passages": expected_count,
        "protected_holdout_cases_used": 0,
        "runtime_activation_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_bundle(args.service_root, args.manifest), indent=2))


if __name__ == "__main__":
    main()
