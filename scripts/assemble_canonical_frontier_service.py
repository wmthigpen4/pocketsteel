#!/usr/bin/env python3
"""Assemble a new immutable, offline-capable canonical frontier service root."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_PASSAGES = 1_948_039
RERANKER_REVISION = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
INDEX_RELATIVE = Path("rag-evaluation/index/steel-forum-passages-v1-hybrid-v1")
TIERED_POLICY_RELATIVE = Path("rag-evaluation/training/canonical-tiered-reranker-grid-policy-v856.json")
FAST_POLICY_RELATIVE = Path("rag-evaluation/training/canonical-frontier-fast-pool-policy-v900.json")
MANIFEST_NAME = "canonical-frontier-service-bundle-v1035.json"
PROTECTED_BASE_SHA = "11c1515788e26c13ecb33b98d9c0ad003f00dcde"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return value


def write_object(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.assembling")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def clone_tree(source: Path, destination: Path) -> None:
    if sys.platform == "darwin":
        destination.mkdir(parents=True, exist_ok=False)
        subprocess.run(
            ["cp", "-cR", f"{source}/.", str(destination)],
            check=True,
        )
        return
    shutil.copytree(source, destination, symlinks=True)


def copy_model_manifest(source_models: Path, destination_models: Path) -> str:
    relative = Path("manifests/registry.ollama.ai/library/bge-m3/latest")
    source_manifest = source_models / relative
    manifest = load_object(source_manifest)
    destination_manifest = destination_models / relative
    destination_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_manifest, destination_manifest)
    digests = [str(manifest["config"]["digest"])] + [
        str(layer["digest"]) for layer in manifest.get("layers") or []
    ]
    for digest in digests:
        if not digest.startswith("sha256:"):
            raise ValueError("The bge-m3 Ollama manifest contains an unsafe digest.")
        blob_name = digest.replace(":", "-")
        source_blob = source_models / "blobs" / blob_name
        if not source_blob.is_file() or sha256(source_blob) != digest.split(":", 1)[1]:
            raise ValueError(f"The bge-m3 blob is missing or mismatched: {blob_name}")
        destination_blob = destination_models / "blobs" / blob_name
        destination_blob.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_blob, destination_blob)
    return sha256(source_manifest)


def relocate_runtime_paths(root: Path) -> None:
    index_root = root / INDEX_RELATIVE
    index_manifest_path = index_root / "manifest.json"
    index_manifest = load_object(index_manifest_path)
    corpus_manifest_path = root / "assets/corpus/public-sgf-corpus-manifest.json"
    corpus_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_object(corpus_manifest_path, {
        "schema_version": 1,
        "corpus_version": "steel-forum-passages-v1",
        "public_passages": EXPECTED_PASSAGES,
        "passages_sha256": str(index_manifest.get("corpus_passages_sha256") or ""),
        "storage": str(index_root / "lexical.sqlite3"),
        "representation": "canonical public SGF passages in the immutable lexical index",
    })
    index_manifest["corpus_manifest"] = str(corpus_manifest_path)
    index_manifest["lexical"]["database"] = str(index_root / "lexical.sqlite3")
    index_manifest["vector"]["path"] = str(index_root / "vector")
    index_manifest["vector"]["progress_path"] = str(
        index_root / "vector-embedding-progress.json"
    )
    write_object(index_manifest_path, index_manifest)

    tiered_path = root / TIERED_POLICY_RELATIVE
    tiered = load_object(tiered_path)
    tiered["group_expansion_index"] = str(index_root / "group-expansion-v1.sqlite3")
    tiered["index_manifest_sha256"] = sha256(index_manifest_path)
    write_object(tiered_path, tiered)

    fast_path = root / FAST_POLICY_RELATIVE
    fast = load_object(fast_path)
    fast["fast_pool_audit"] = str(
        root / "rag-evaluation/audit/canonical-frontier-fast-pool-v899.json"
    )
    fast["top6_answerability_audit"] = str(
        root / "rag-evaluation/audit/canonical-frontier-top6-answerability-v896.json"
    )
    write_object(fast_path, fast)


def inventory(root: Path) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if relative == MANIFEST_NAME:
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"Service-root symlink escapes the bundle: {relative}") from exc
        if path.is_symlink() and resolved.is_dir():
            files[relative] = {
                "entry_type": "directory_symlink",
                "symlink": os.readlink(path),
            }
            continue
        if not resolved.is_file():
            raise ValueError(f"Bundle entry is not a regular file: {relative}")
        row: dict[str, Any] = {
            "entry_type": "file_symlink" if path.is_symlink() else "file",
            "sha256": sha256(resolved),
            "size": resolved.stat().st_size,
        }
        if path.is_symlink():
            row["symlink"] = os.readlink(path)
        files[relative] = row
    return files


def protected_release_sha(repository: Path) -> str:
    repository = repository.expanduser().resolve()
    release_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if re.fullmatch(r"[0-9a-f]{40}", release_sha) is None:
        raise ValueError("The repair application SHA is invalid.")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PROTECTED_BASE_SHA, release_sha],
        cwd=repository,
        check=False,
    )
    if ancestry.returncode != 0:
        raise ValueError("The repair application SHA is not a protected-SHA descendant.")
    return release_sha


def freeze_tree(root: Path) -> None:
    """Remove every write bit after the complete bundle has been assembled."""

    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode & ~0o222)
    root.chmod(stat.S_IMODE(root.stat().st_mode) & ~0o222)


def assemble(args: argparse.Namespace) -> Path:
    base = args.base_service_root.expanduser().resolve()
    output = args.output_service_root.expanduser().resolve()
    overlay = args.overlay.expanduser().resolve()
    release_sha = protected_release_sha(args.application_repo)
    if output.exists():
        raise ValueError("The output service root already exists; immutable roots are never modified.")
    if not base.is_dir() or not overlay.is_dir():
        raise ValueError("The base service root and v1035 overlay are required.")
    clone_tree(base, output)
    for source in sorted(overlay.glob("*.py")):
        shutil.copy2(source, output / source.name)

    ollama_binary = args.ollama_binary.expanduser().resolve()
    bundled_ollama = output / "assets/ollama/bin/ollama"
    bundled_ollama.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ollama_binary, bundled_ollama)
    bundled_ollama.chmod(0o755)
    ollama_manifest_sha = copy_model_manifest(
        args.ollama_models.expanduser().resolve(),
        output / "assets/ollama/models",
    )

    reranker_source = args.reranker_cache.expanduser().resolve()
    reranker_destination = output / "assets/huggingface/hub/models--BAAI--bge-reranker-v2-m3"
    clone_tree(reranker_source, reranker_destination)
    revision_root = reranker_destination / "snapshots" / RERANKER_REVISION
    if not revision_root.is_dir():
        raise ValueError("The pinned BGE reranker revision is absent from the copied cache.")

    clone_tree(
        args.python_runtime.expanduser().resolve(),
        output / "assets/python/3.9",
    )
    clone_tree(
        args.python_site_packages.expanduser().resolve(),
        output / "vendor/python",
    )
    relocate_runtime_paths(output)
    files = inventory(output)
    manifest_path = output / MANIFEST_NAME
    write_object(manifest_path, {
        "schema_version": 2,
        "bundle_version": "canonical-frontier-service-bundle-v1035",
        "protected_application_base_sha": PROTECTED_BASE_SHA,
        "repair_application_sha": release_sha,
        "service_entrypoint": "canonical_frontier_http_api_v3.py",
        "expected_index_passages": EXPECTED_PASSAGES,
        "retrieval": {
            "query_embedding_model": "bge-m3",
            "reranker_model": "BAAI/bge-reranker-v2-m3",
            "reranker_revision": RERANKER_REVISION,
            "ranked_passage_limit": 10,
            "ollama_manifest_sha256": ollama_manifest_sha,
        },
        "generation": {
            "writer": "gpt-5.6-terra",
            "verifier": "gpt-5.6-luna",
            "maximum_responses_requests_per_answer": 2,
            "local_generative_models_enabled": False,
            "historical_local_generative_branches": ["qwen", "gemma"],
        },
        "required_assets": {
            "ollama_binary": "assets/ollama/bin/ollama",
            "ollama_bge_m3_manifest": "assets/ollama/models/manifests/registry.ollama.ai/library/bge-m3/latest",
            "reranker_revision": (
                "assets/huggingface/hub/models--BAAI--bge-reranker-v2-m3/"
                f"snapshots/{RERANKER_REVISION}"
            ),
            "python_runtime": "assets/python/3.9/bin/python3",
            "python_packages": "vendor/python",
            "corpus_manifest": "assets/corpus/public-sgf-corpus-manifest.json",
        },
        "files": files,
    })
    freeze_tree(output)
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-service-root", required=True, type=Path)
    parser.add_argument("--output-service-root", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--ollama-binary", required=True, type=Path)
    parser.add_argument("--ollama-models", required=True, type=Path)
    parser.add_argument("--reranker-cache", required=True, type=Path)
    parser.add_argument("--python-site-packages", required=True, type=Path)
    parser.add_argument("--python-runtime", required=True, type=Path)
    parser.add_argument("--application-repo", required=True, type=Path)
    args = parser.parse_args()
    print(assemble(args))


if __name__ == "__main__":
    main()
