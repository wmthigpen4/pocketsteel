"""Exact machine-readable authority for the beat-cell Stage-2 cycle.

This module deliberately reads only the tracked preregistration JSON.  It
does not inspect any experiment input or output.  Official command-line
entrypoints import the constants below before they are allowed to touch a
Stage-1 source.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from .bar_promotion import canonical_sha256


BEAT_CELL_STAGE2_AUTHORITY_SCHEMA = "chord_runtime_beat_cell_stage2_preregistration_v1"
BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA = "chord_runtime_beat_cell_stage2_publication_policy_v2"
BEAT_CELL_FEATURE_SET_PUBLICATION_MODE = (
    "canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-"
    "direct-in-memory-exact-rendered-inventory-owned-complete-tree-v2"
)
BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE = (
    "canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-v1"
)
BEAT_CELL_STAGE2_AUTHORITY_RELATIVE_PATH = Path(
    "docs/handoffs/task-completions/2026-08-21-1019-20-beat-cell-stage2-r4-final-source-amended-preregistration.json"
)
BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256 = "329bb235e760a9c665945817b21d4ea0e9d824a26251a668cad4d47fa5b7e2a1"
BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256 = "a606cfefb1026bc29d335aeb9e73f0adead459a6e789e550aaff35bca214e7c9"
BEAT_CELL_STAGE_A_PROJECTION_SHA256 = "814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688"
BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256 = "4b450d74df5314d68e7a8034d488b8d727144c2847e0ae628ba351c69d4ddfb0"
BEAT_CELL_STAGE_B_PROJECTION_SHA256 = "ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32"
BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256 = "2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf"
BEAT_CELL_READINESS_PROJECTION_SHA256 = "81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18"
BEAT_CELL_ONE_SHOT_PROJECTION_SHA256 = "450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796"

_TOP_LEVEL_FIELDS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "sourceInputs",
        "outputPaths",
        "stageA",
        "featureMath",
        "stageB",
        "selectorCore",
        "readiness",
        "oneShot",
    }
)
_PROJECTION_HASHES = {
    "stageA": BEAT_CELL_STAGE_A_PROJECTION_SHA256,
    "featureMath": BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256,
    "stageB": BEAT_CELL_STAGE_B_PROJECTION_SHA256,
    "selectorCore": BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256,
    "readiness": BEAT_CELL_READINESS_PROJECTION_SHA256,
    "oneShot": BEAT_CELL_ONE_SHOT_PROJECTION_SHA256,
}
_OUTPUT_PATH_FIELDS = frozenset(
    {
        "featureSetManifest",
        "featureSummaryRoot",
        "examplesArtifact",
        "selectorArtifact",
        "readinessReport",
        "publication",
    }
)
_PUBLICATION_POLICY_FIELDS = frozenset({"schemaVersion", "featureSet", "singleJson"})


class BeatCellStage2ContractError(ValueError):
    """The tracked Stage-2 preregistration or a projection is not exact."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def authority_path() -> Path:
    """Return the exact tracked authority path without opening it."""

    return _repo_root() / BEAT_CELL_STAGE2_AUTHORITY_RELATIVE_PATH


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _reject_symlink_components(path: Path, name: str) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        try:
            visible = os.lstat(current)
        except OSError as error:
            raise BeatCellStage2ContractError(f"Could not inspect {name} path component.") from error
        if stat.S_ISLNK(visible.st_mode):
            raise BeatCellStage2ContractError(f"{name} contains a symlinked path component.")


def _sealed_read(path: Path, name: str) -> bytes:
    absolute = Path(os.path.abspath(path))
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise BeatCellStage2ContractError(f"Could not open {name}.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise BeatCellStage2ContractError(f"{name} must be a regular file.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(descriptor)
    try:
        visible = os.stat(absolute, follow_symlinks=False)
    except OSError as error:
        raise BeatCellStage2ContractError(f"{name} disappeared after it was read.") from error
    if _identity(visible) != _identity(opened):
        raise BeatCellStage2ContractError(f"{name} changed while it was read.")
    return raw


def _strict_json(raw: bytes, name: str) -> dict[str, Any]:
    duplicate_keys: list[str] = []

    def exact_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in pairs:
            if key in output:
                duplicate_keys.append(key)
            output[key] = value
        return output

    def reject_constant(value: str) -> Any:
        raise BeatCellStage2ContractError(f"{name} contains non-finite JSON constant {value!r}.")

    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=exact_object,
            parse_constant=reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BeatCellStage2ContractError(f"Could not parse {name} as strict UTF-8 JSON.") from error
    if duplicate_keys:
        raise BeatCellStage2ContractError(f"{name} contains duplicate JSON keys.")
    if not isinstance(parsed, dict):
        raise BeatCellStage2ContractError(f"{name} must be a JSON object.")
    return parsed


def _validate_source_module(authority: Mapping[str, Any], projection: str, path_field: str, hash_field: str) -> None:
    section = authority.get(projection)
    if not isinstance(section, Mapping):
        raise BeatCellStage2ContractError(f"Authority projection {projection!r} must be an object.")
    relative = section.get(path_field)
    expected = section.get(hash_field)
    relative_path = Path(relative) if isinstance(relative, str) else Path()
    if not isinstance(relative, str) or not relative or relative_path.is_absolute() or ".." in relative_path.parts:
        raise BeatCellStage2ContractError(f"{projection}.{path_field} must be a repository-relative path.")
    if not isinstance(expected, str) or len(expected) != 64:
        raise BeatCellStage2ContractError(f"{projection}.{hash_field} must be a SHA-256 digest.")
    root = Path(os.path.abspath(_repo_root()))
    source = Path(os.path.abspath(root / relative_path))
    try:
        source.relative_to(root)
    except ValueError as error:
        raise BeatCellStage2ContractError(f"{projection}.{path_field} escapes the repository.") from error
    raw = _sealed_read(source, f"{projection} source module")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise BeatCellStage2ContractError(f"{projection} source module file hash is stale.")


def validate_beat_cell_stage2_authority(authority: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an already parsed authority object without touching experiment data."""

    if not isinstance(authority, Mapping):
        raise BeatCellStage2ContractError("Stage-2 authority must be an object.")
    value = deepcopy(dict(authority))
    if set(value) != _TOP_LEVEL_FIELDS:
        raise BeatCellStage2ContractError("Stage-2 authority fields are not exact.")
    if (
        value.get("schemaVersion") != BEAT_CELL_STAGE2_AUTHORITY_SCHEMA
        or value.get("split") != "development"
        or value.get("developmentOnly") is not True
        or value.get("promotionEligible") is not False
    ):
        raise BeatCellStage2ContractError("Stage-2 authority is not the frozen development-only envelope.")
    output_paths = value.get("outputPaths")
    if not isinstance(output_paths, Mapping) or set(output_paths) != _OUTPUT_PATH_FIELDS:
        raise BeatCellStage2ContractError("Stage-2 authority outputPaths fields are not exact.")
    publication = output_paths.get("publication")
    if (
        not isinstance(publication, Mapping)
        or set(publication) != _PUBLICATION_POLICY_FIELDS
        or publication.get("schemaVersion") != BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA
        or publication.get("featureSet") != BEAT_CELL_FEATURE_SET_PUBLICATION_MODE
        or publication.get("singleJson") != BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE
    ):
        raise BeatCellStage2ContractError("Stage-2 authority publication policy is not exact.")
    if canonical_sha256(value) != BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256:
        raise BeatCellStage2ContractError("Stage-2 authority canonical hash is stale.")
    for name, expected in _PROJECTION_HASHES.items():
        projection = value.get(name)
        if not isinstance(projection, Mapping) or canonical_sha256(projection) != expected:
            raise BeatCellStage2ContractError(f"Stage-2 {name} projection hash is stale.")
    _validate_source_module(value, "featureMath", "sourceModule", "sourceModuleFileSha256")
    _validate_source_module(
        value,
        "featureMath",
        "sourceBeatCellStage1Module",
        "sourceBeatCellStage1ModuleFileSha256",
    )
    feature_math = value.get("featureMath")
    if isinstance(feature_math, Mapping):
        has_reconciliation = "stage1ProductReconciliation" in feature_math
        has_stage_a_module = "sourceStageAImplementationModule" in feature_math
        has_stage_a_hash = "sourceStageAImplementationModuleFileSha256" in feature_math
        if has_reconciliation and not (has_stage_a_module and has_stage_a_hash):
            raise BeatCellStage2ContractError(
                "The reconciled feature-math authority must bind the exact Stage-A implementation source."
            )
    if isinstance(feature_math, Mapping) and (has_stage_a_module or has_stage_a_hash):
        _validate_source_module(
            value,
            "featureMath",
            "sourceStageAImplementationModule",
            "sourceStageAImplementationModuleFileSha256",
        )
    _validate_source_module(value, "selectorCore", "sourceModule", "sourceModuleFileSha256")
    _validate_source_module(value, "readiness", "sourceModule", "sourceModuleFileSha256")
    return value


def load_beat_cell_stage2_authority() -> dict[str, Any]:
    """Load and validate the one committed authority at its exact tracked path."""

    raw = _sealed_read(authority_path(), "beat-cell Stage-2 authority")
    if hashlib.sha256(raw).hexdigest() != BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256:
        raise BeatCellStage2ContractError("Stage-2 authority file hash is stale.")
    return validate_beat_cell_stage2_authority(_strict_json(raw, "beat-cell Stage-2 authority"))


def projection(name: str) -> dict[str, Any]:
    """Return a deep copy of one exact preregistered projection."""

    if name not in _PROJECTION_HASHES:
        raise BeatCellStage2ContractError(f"Unknown Stage-2 projection {name!r}.")
    return deepcopy(_AUTHORITY[name])


_AUTHORITY = load_beat_cell_stage2_authority()
BEAT_CELL_STAGE2_SOURCE_INPUTS = deepcopy(_AUTHORITY["sourceInputs"])
BEAT_CELL_STAGE2_OUTPUT_PATHS = deepcopy(_AUTHORITY["outputPaths"])
BEAT_CELL_STAGE_A_PROJECTION = deepcopy(_AUTHORITY["stageA"])
BEAT_CELL_FEATURE_MATH_PROJECTION = deepcopy(_AUTHORITY["featureMath"])
BEAT_CELL_STAGE_B_PROJECTION = deepcopy(_AUTHORITY["stageB"])
BEAT_CELL_SELECTOR_CORE_PROJECTION = deepcopy(_AUTHORITY["selectorCore"])
BEAT_CELL_READINESS_PROJECTION = deepcopy(_AUTHORITY["readiness"])
BEAT_CELL_ONE_SHOT_PROJECTION = deepcopy(_AUTHORITY["oneShot"])


__all__ = [
    "BEAT_CELL_FEATURE_MATH_PROJECTION",
    "BEAT_CELL_FEATURE_MATH_PROJECTION_SHA256",
    "BEAT_CELL_FEATURE_SET_PUBLICATION_MODE",
    "BEAT_CELL_ONE_SHOT_PROJECTION",
    "BEAT_CELL_ONE_SHOT_PROJECTION_SHA256",
    "BEAT_CELL_READINESS_PROJECTION",
    "BEAT_CELL_READINESS_PROJECTION_SHA256",
    "BEAT_CELL_SELECTOR_CORE_PROJECTION",
    "BEAT_CELL_SELECTOR_CORE_PROJECTION_SHA256",
    "BEAT_CELL_STAGE2_AUTHORITY_CANONICAL_SHA256",
    "BEAT_CELL_STAGE2_AUTHORITY_FILE_SHA256",
    "BEAT_CELL_STAGE2_AUTHORITY_RELATIVE_PATH",
    "BEAT_CELL_STAGE2_AUTHORITY_SCHEMA",
    "BEAT_CELL_STAGE2_OUTPUT_PATHS",
    "BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA",
    "BEAT_CELL_STAGE2_SOURCE_INPUTS",
    "BEAT_CELL_STAGE_A_PROJECTION",
    "BEAT_CELL_STAGE_A_PROJECTION_SHA256",
    "BEAT_CELL_STAGE_B_PROJECTION",
    "BEAT_CELL_STAGE_B_PROJECTION_SHA256",
    "BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE",
    "BeatCellStage2ContractError",
    "authority_path",
    "load_beat_cell_stage2_authority",
    "projection",
    "validate_beat_cell_stage2_authority",
]
