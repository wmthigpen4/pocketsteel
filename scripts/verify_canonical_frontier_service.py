#!/usr/bin/env python3
"""Fail closed unless the external canonical-frontier service matches its bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def verify_v2_bundle(root: Path, manifest_file: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "schema_version", "bundle_version", "protected_application_base_sha",
        "repair_application_sha", "service_entrypoint", "expected_index_passages",
        "retrieval", "generation", "required_assets", "files",
    }
    files = manifest.get("files")
    retrieval = manifest.get("retrieval") or {}
    generation = manifest.get("generation") or {}
    assets = manifest.get("required_assets") or {}
    if (
        set(manifest) != expected_keys
        or manifest.get("schema_version") != 2
        or manifest.get("bundle_version") != "canonical-frontier-service-bundle-v1035"
        or manifest.get("protected_application_base_sha")
        != "11c1515788e26c13ecb33b98d9c0ad003f00dcde"
        or re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("repair_application_sha") or ""))
        is None
        or manifest.get("service_entrypoint") != "canonical_frontier_http_api_v3.py"
        or int(manifest.get("expected_index_passages") or 0) != 1_948_039
        or not isinstance(files, dict)
        or not files
        or retrieval.get("query_embedding_model") != "bge-m3"
        or retrieval.get("reranker_model") != "BAAI/bge-reranker-v2-m3"
        or retrieval.get("reranker_revision")
        != "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
        or int(retrieval.get("ranked_passage_limit") or 0) != 10
        or generation.get("writer") != "gpt-5.6-terra"
        or generation.get("verifier") != "gpt-5.6-luna"
        or int(generation.get("maximum_responses_requests_per_answer") or 0) != 2
        or generation.get("local_generative_models_enabled") is not False
    ):
        raise ValueError("Canonical-frontier v1035 bundle manifest is invalid.")

    actual_files: set[str] = set()
    mismatches: list[str] = []
    if stat.S_IMODE(root.stat().st_mode) & 0o222:
        raise ValueError("Canonical-frontier service root is not frozen read-only.")
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if not path.is_symlink() and stat.S_IMODE(path.stat().st_mode) & 0o222:
            mismatches.append(relative)
            continue
        if path == manifest_file:
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        actual_files.add(relative)
        expected = files.get(relative)
        if not isinstance(expected, dict):
            mismatches.append(relative)
            continue
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Bundle symlink escapes the service root: {relative}") from exc
        entry_type = str(expected.get("entry_type") or "")
        if entry_type == "directory_symlink":
            if (
                not path.is_symlink()
                or not resolved.is_dir()
                or expected.get("symlink") != os.readlink(path)
                or set(expected) != {"entry_type", "symlink"}
            ):
                mismatches.append(relative)
            continue
        if not resolved.is_file():
            mismatches.append(relative)
            continue
        if entry_type not in {"file", "file_symlink"}:
            mismatches.append(relative)
            continue
        if (
            (entry_type == "file_symlink") != path.is_symlink()
            or (path.is_symlink() and expected.get("symlink") != os.readlink(path))
        ):
            mismatches.append(relative)
            continue
        if (
            int(expected.get("size", -1)) != resolved.stat().st_size
            or str(expected.get("sha256") or "") != sha256(resolved)
        ):
            mismatches.append(relative)
    missing = set(files) - actual_files
    extra = actual_files - set(files)
    if mismatches or missing or extra:
        preview = sorted(set(mismatches) | missing | extra)[:5]
        raise ValueError(
            "Canonical-frontier bundle fingerprint mismatch: "
            + ", ".join(preview)
            + ("..." if len(set(mismatches) | missing | extra) > 5 else "")
        )

    entrypoint = resolve_required(root, str(manifest["service_entrypoint"]))
    if not entrypoint.is_file():
        raise ValueError("Canonical-frontier v1035 entrypoint is missing.")
    required_asset_keys = {
        "ollama_binary", "ollama_inference_runtime", "ollama_bge_m3_manifest",
        "reranker_revision", "python_runtime", "python_packages", "corpus_manifest",
    }
    if set(assets) != required_asset_keys:
        raise ValueError("Canonical-frontier required-asset inventory is invalid.")
    resolved_assets = {
        key: resolve_required(root, str(value)) for key, value in assets.items()
    }
    if not resolved_assets["ollama_binary"].is_file() or not os.access(
        resolved_assets["ollama_binary"], os.X_OK
    ):
        raise ValueError("The bundled Ollama executable is missing or not executable.")
    if not resolved_assets["ollama_inference_runtime"].is_file() or not os.access(
        resolved_assets["ollama_inference_runtime"], os.X_OK
    ):
        raise ValueError("The bundled Ollama inference runtime is missing or not executable.")
    if not resolved_assets["reranker_revision"].is_dir():
        raise ValueError("The pinned BGE reranker revision is missing.")
    for name in ("config.json", "tokenizer.json", "model.safetensors"):
        if not (resolved_assets["reranker_revision"] / name).is_file():
            raise ValueError(f"The pinned BGE reranker asset {name} is missing.")
    for package in ("chromadb", "numpy", "tokenizers", "torch", "transformers"):
        if not (resolved_assets["python_packages"] / package).exists():
            raise ValueError(f"The bundled Python dependency is missing: {package}")
    if not resolved_assets["python_runtime"].is_file() or not os.access(
        resolved_assets["python_runtime"], os.X_OK
    ):
        raise ValueError("The bundled Python runtime is missing or not executable.")
    dependency_environment = {
        **os.environ,
        "PYTHONPATH": str(resolved_assets["python_packages"]),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }
    dependency_check = subprocess.run(
        [
            str(resolved_assets["python_runtime"]),
            "-c",
            (
                "import chromadb,numpy,tokenizers,torch,transformers; "
                "print('bundled_python_dependencies_ok')"
            ),
        ],
        cwd=root,
        env=dependency_environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if dependency_check.returncode != 0:
        raise ValueError("The bundled Python runtime/dependency ABI check failed.")

    ollama_manifest = load_object(resolved_assets["ollama_bge_m3_manifest"])
    digests = [str((ollama_manifest.get("config") or {}).get("digest") or "")] + [
        str(layer.get("digest") or "") for layer in ollama_manifest.get("layers") or []
    ]
    if not digests or any(not digest.startswith("sha256:") for digest in digests):
        raise ValueError("The bundled bge-m3 Ollama manifest is invalid.")
    for digest in digests:
        blob = root / "assets/ollama/models/blobs" / digest.replace(":", "-")
        if not blob.is_file() or sha256(blob) != digest.split(":", 1)[1]:
            raise ValueError("A bundled bge-m3 Ollama blob is missing or mismatched.")

    expected_count = int(manifest["expected_index_passages"])
    index_root = root / INDEX_RELATIVE
    index_manifest = load_object(index_root / "manifest.json")
    progress = load_object(index_root / "vector-embedding-progress.json")
    lexical = index_manifest.get("lexical") or {}
    vector = index_manifest.get("vector") or {}
    if (
        index_manifest.get("status") != "ready"
        or index_manifest.get("corpus_version") != "steel-forum-passages-v1"
        or index_manifest.get("source_id_scheme") != "steel-passage-v1"
        or index_manifest.get("protected_holdout_used") is not False
        or int(lexical.get("count") or 0) != expected_count
        or int(lexical.get("display_eligible_count") or 0) != expected_count
        or int(vector.get("count") or 0) != expected_count
        or int(progress.get("expected_passages") or 0) != expected_count
        or int(progress.get("processed_passages") or 0) != expected_count
        or int(progress.get("collection_count") or 0) != expected_count
    ):
        raise ValueError("Canonical lexical/vector index is incomplete or mismatched.")
    lexical_path = require_local_path(root, str(lexical.get("database") or ""), "lexical database")
    require_local_path(root, str(vector.get("path") or ""), "vector index")
    require_local_path(root, str(vector.get("progress_path") or ""), "vector progress")
    corpus_manifest = load_object(resolved_assets["corpus_manifest"])
    if int(corpus_manifest.get("public_passages") or 0) != expected_count:
        raise ValueError("The bundled public SGF corpus count is invalid.")
    connection = sqlite3.connect(f"file:{lexical_path}?mode=ro&immutable=1", uri=True)
    try:
        quick_check = str(connection.execute("pragma quick_check").fetchone()[0])
        row = connection.execute(
            "select count(*), sum(display_eligible), "
            "sum(case when access_provenance='public_forum' then 1 else 0 end) from passages"
        ).fetchone()
    finally:
        connection.close()
    if quick_check != "ok" or tuple(map(int, row)) != (
        expected_count, expected_count, expected_count,
    ):
        raise ValueError("The public SGF lexical index failed integrity or eligibility checks.")

    tiered = load_object(root / TIERED_POLICY_RELATIVE)
    require_local_path(
        root, str(tiered.get("group_expansion_index") or ""), "group-expansion index"
    )
    if (
        tiered.get("model") != retrieval["reranker_model"]
        or tiered.get("revision") != retrieval["reranker_revision"]
        or tiered.get("index_manifest_sha256") != sha256(index_root / "manifest.json")
    ):
        raise ValueError("The frozen BGE reranking policy is mismatched.")
    runtime_source = (root / "canonical_frontier_v1032_runtime_candidate.py").read_text(
        encoding="utf-8"
    )
    if "retrieval_limit: int = 10" not in runtime_source:
        raise ValueError("The audited ten-passage runtime limit is absent.")
    return {
        "status": "canonical_frontier_service_bundle_verified",
        "bundle_version": manifest["bundle_version"],
        "verified_files": len(files),
        "index_passages": expected_count,
        "source_eligible_passages": expected_count,
        "query_embedding_model": retrieval["query_embedding_model"],
        "reranker_revision": retrieval["reranker_revision"],
        "ranked_passage_limit": 10,
        "activation_ready": True,
    }


def verify_bundle(service_root: Path, manifest_path: Path) -> dict[str, Any]:
    root = service_root.expanduser().resolve()
    manifest_file = manifest_path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Canonical-frontier service root is missing.")
    manifest = load_object(manifest_file)
    if manifest.get("schema_version") == 2:
        return verify_v2_bundle(root, manifest_file, manifest)
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
