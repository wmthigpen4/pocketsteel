#!/usr/bin/env python3
"""Train or validate the one preregistered beat-cell selector artifact."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.beat_cell_selector import (  # noqa: E402
    train_beat_cell_selector,
    validate_beat_cell_selector_artifact,
)
from steel_guitar_rag.chord_reader.beat_cell_examples import (  # noqa: E402
    validate_beat_cell_examples_artifact,
)
from steel_guitar_rag.chord_reader.beat_cell_stage2_contract import (  # noqa: E402
    BEAT_CELL_FEATURE_SET_PUBLICATION_MODE,
    BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE,
    BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA,
    load_beat_cell_stage2_authority,
)


class BeatCellSelectorCliError(ValueError):
    """Official selector I/O failed closed."""


_OFFICIAL_EXAMPLE_COUNT = 9376
_OFFICIAL_EXAMPLE_DURATION_MILLISECONDS = 5074349
_PUBLICATION_POLICY_FIELDS = frozenset({"schemaVersion", "featureSet", "singleJson"})
_STAGE1_EXAMPLES_BINDINGS = {
    "sourceStage1FileSha256": "fileSha256",
    "sourceStage1CanonicalSha256": "canonicalSha256",
    "sourceStage1ArtifactSha256": "artifactSha256",
    "sourceStage1DecisionSha256": "decisionSha256",
    "sourceStage1GateSetSha256": "gateSetSha256",
    "sourceStage1TrackSetSha256": "trackSetSha256",
    "sourceStage1SourceContractSha256": "sourceContractSha256",
}


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _reject_symlink_components(path: Path, name: str, *, allow_missing_leaf: bool = False) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for index, component in enumerate(absolute.parts[1:]):
        current /= component
        try:
            visible = os.lstat(current)
        except FileNotFoundError:
            if allow_missing_leaf and index == len(absolute.parts[1:]) - 1:
                return
            raise BeatCellSelectorCliError(f"{name} has a missing path component.") from None
        except OSError as error:
            raise BeatCellSelectorCliError(f"Could not inspect {name} path components.") from error
        if stat.S_ISLNK(visible.st_mode):
            raise BeatCellSelectorCliError(f"{name} contains a symlinked path component.")


def _sealed_read_snapshot(path: Path, name: str) -> tuple[bytes, tuple[int, int]]:
    absolute = Path(os.path.abspath(path))
    _reject_symlink_components(absolute, name)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise BeatCellSelectorCliError(f"Could not open {name}.") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise BeatCellSelectorCliError(f"{name} must be a regular file.")
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
        raise BeatCellSelectorCliError(f"{name} disappeared after it was read.") from error
    if _identity(visible) != _identity(opened):
        raise BeatCellSelectorCliError(f"{name} changed while it was read.")
    return raw, _identity(opened)


def _sealed_read(path: Path, name: str) -> bytes:
    return _sealed_read_snapshot(path, name)[0]


def _verify_snapshot(path: Path, raw: bytes, inode: tuple[int, int], name: str) -> None:
    current_raw, current_inode = _sealed_read_snapshot(path, name)
    if current_inode != inode or current_raw != raw:
        raise BeatCellSelectorCliError(f"{name} bytes or inode changed during the operation.")


def _strict_json(raw: bytes, name: str) -> dict[str, Any]:
    duplicates: list[str] = []

    def exact_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in pairs:
            if key in output:
                duplicates.append(key)
            output[key] = value
        return output

    def reject_constant(value: str) -> Any:
        raise BeatCellSelectorCliError(f"{name} contains non-finite JSON constant {value!r}.")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=exact_object,
            parse_constant=reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BeatCellSelectorCliError(f"Could not parse {name} as strict UTF-8 JSON.") from error
    if duplicates or not isinstance(value, dict):
        raise BeatCellSelectorCliError(f"{name} must be one duplicate-free JSON object.")
    return value


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:  # pragma: no cover - artifact validator owns this invariant
        raise BeatCellSelectorCliError("Selector artifact is not finite canonical JSON.") from error


def _directory_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _file_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)


def _verify_directory_path(path: Path, descriptor: int, inode: tuple[int, int], name: str) -> None:
    try:
        visible = os.stat(path, follow_symlinks=False)
    except OSError as error:
        raise BeatCellSelectorCliError(f"{name} path changed during publication.") from error
    if _identity(os.fstat(descriptor)) != inode or _identity(visible) != inode:
        raise BeatCellSelectorCliError(f"{name} path changed during publication.")


def _open_or_create_directory(path: Path, name: str) -> tuple[int, tuple[int, int]]:
    absolute = Path(os.path.abspath(path))
    descriptor = os.open(absolute.anchor, _directory_open_flags())
    try:
        for component in absolute.parts[1:]:
            if component in {"", ".", ".."}:
                raise BeatCellSelectorCliError(f"{name} contains an invalid path component.")
            try:
                os.mkdir(component, mode=0o700, dir_fd=descriptor)
            except FileExistsError:
                pass
            try:
                next_descriptor = os.open(component, _directory_open_flags(), dir_fd=descriptor)
            except OSError as error:
                raise BeatCellSelectorCliError(f"{name} contains a symlink or non-directory component.") from error
            os.close(descriptor)
            descriptor = next_descriptor
        inode = _identity(os.fstat(descriptor))
        _verify_directory_path(absolute, descriptor, inode, name)
        return descriptor, inode
    except Exception:
        os.close(descriptor)
        raise


def _entry_stat(parent_descriptor: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _unlink_owned_entry(parent_descriptor: int, name: str, inode: tuple[int, int]) -> None:
    """Unlink only while a retained dirfd still names the inode we created."""

    try:
        descriptor = os.open(name, _file_open_flags(), dir_fd=parent_descriptor)
    except OSError:
        return
    try:
        if _identity(os.fstat(descriptor)) == inode:
            try:
                os.unlink(name, dir_fd=parent_descriptor)
            except OSError:
                pass
    finally:
        os.close(descriptor)


def _unlink_all_owned_entries(parent_descriptor: int, inode: tuple[int, int]) -> None:
    """Best-effort cleanup of every retained-parent link to our inode."""

    try:
        names = os.listdir(parent_descriptor)
    except OSError:
        return
    for name in names:
        _unlink_owned_entry(parent_descriptor, name, inode)


def _read_entry(parent_descriptor: int, name: str) -> bytes:
    try:
        descriptor = os.open(name, _file_open_flags(), dir_fd=parent_descriptor)
    except OSError as error:
        raise BeatCellSelectorCliError("Could not reopen the published selector artifact.") from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise BeatCellSelectorCliError("The published selector artifact is not a regular file.")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _verify_owned_entry(parent_descriptor: int, name: str, inode: tuple[int, int]) -> None:
    visible = _entry_stat(parent_descriptor, name)
    if visible is None or not stat.S_ISREG(visible.st_mode) or _identity(visible) != inode:
        raise BeatCellSelectorCliError("The published selector artifact inode changed during publication.")


def _preflight_new_output(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    if absolute.suffix.lower() != ".json":
        raise BeatCellSelectorCliError("The exact selector output must be JSON.")
    current = Path(absolute.anchor)
    for component in absolute.parts[1:-1]:
        current /= component
        try:
            visible = os.lstat(current)
        except FileNotFoundError:
            break
        if stat.S_ISLNK(visible.st_mode) or not stat.S_ISDIR(visible.st_mode):
            raise BeatCellSelectorCliError("The selector output parent contains a symlink or non-directory.")
    if os.path.lexists(absolute):
        raise BeatCellSelectorCliError("The canonical selector output already exists; retry is forbidden.")
    return absolute


def _atomic_publish_new(
    path: Path,
    payload: bytes,
    *,
    precommit_check: Callable[[], None] | None = None,
) -> None:
    absolute = _preflight_new_output(path)
    directory, directory_inode = _open_or_create_directory(absolute.parent, "selector output parent")
    temporary = f".{absolute.name}.{secrets.token_hex(16)}.tmp"
    descriptor: int | None = None
    temporary_inode: tuple[int, int] | None = None
    linked_inode: tuple[int, int] | None = None
    try:
        if _entry_stat(directory, absolute.name) is not None:
            raise BeatCellSelectorCliError("The canonical selector output appeared before publication.")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory,
        )
        temporary_inode = _identity(os.fstat(descriptor))
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:  # pragma: no cover - defensive OS invariant
                raise BeatCellSelectorCliError("Could not finish writing the selector artifact.")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        if _entry_stat(directory, absolute.name) is not None:
            raise BeatCellSelectorCliError("The canonical selector output appeared before publication.")
        if precommit_check is not None:
            precommit_check()
        try:
            os.link(
                temporary,
                absolute.name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise BeatCellSelectorCliError(
                "The canonical selector output already exists; retry is forbidden."
            ) from error
        linked_inode = temporary_inode
        if precommit_check is not None:
            precommit_check()
        _verify_owned_entry(directory, absolute.name, temporary_inode)
        if _read_entry(directory, absolute.name) != payload:
            raise BeatCellSelectorCliError("The published selector artifact did not round-trip exactly.")
        _verify_owned_entry(directory, absolute.name, temporary_inode)
        os.fsync(directory)
        _verify_owned_entry(directory, absolute.name, temporary_inode)
        _verify_directory_path(absolute.parent, directory, directory_inode, "selector output parent")
        _verify_owned_entry(directory, absolute.name, temporary_inode)
        published_inode = temporary_inode
        _unlink_owned_entry(directory, temporary, published_inode)
        temporary_inode = None
        os.fsync(directory)
        _verify_directory_path(absolute.parent, directory, directory_inode, "selector output parent")
        _verify_owned_entry(directory, absolute.name, published_inode)
    except BaseException:
        owned_inode = linked_inode if linked_inode is not None else temporary_inode
        if owned_inode is not None:
            _unlink_owned_entry(directory, absolute.name, owned_inode)
            _unlink_all_owned_entries(directory, owned_inode)
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_inode is not None:
            _unlink_owned_entry(directory, temporary, temporary_inode)
        os.close(directory)


def _validate_official_examples_pre_fit(examples: Mapping[str, Any], authority: Mapping[str, Any]) -> dict[str, Any]:
    """Fail before fitting unless examples equal the one authority admission."""

    try:
        validated = validate_beat_cell_examples_artifact(examples)
    except (TypeError, ValueError, OverflowError) as error:
        raise BeatCellSelectorCliError("The official examples artifact failed standalone validation.") from error
    source_inputs = authority.get("sourceInputs")
    stage_b = authority.get("stageB")
    if not isinstance(source_inputs, Mapping) or not isinstance(stage_b, Mapping):
        raise BeatCellSelectorCliError("The authority source/stage-B projections are invalid.")
    expected_stage1 = source_inputs.get("stage1Report")
    if not isinstance(expected_stage1, Mapping):
        raise BeatCellSelectorCliError("The authority Stage-1 source projection is invalid.")
    if (
        stage_b.get("expectedExampleCount") != _OFFICIAL_EXAMPLE_COUNT
        or stage_b.get("expectedExampleDurationMilliseconds") != _OFFICIAL_EXAMPLE_DURATION_MILLISECONDS
        or validated.get("exampleCount") != _OFFICIAL_EXAMPLE_COUNT
        or validated.get("exampleDurationMilliseconds") != _OFFICIAL_EXAMPLE_DURATION_MILLISECONDS
        or any(
            validated.get(examples_field) != expected_stage1.get(authority_field)
            for examples_field, authority_field in _STAGE1_EXAMPLES_BINDINGS.items()
        )
    ):
        raise BeatCellSelectorCliError(
            "Official examples changed the exact Stage-1 source hashes or frozen count/duration."
        )
    return validated


def _official_paths(authority: Mapping[str, Any] | None = None) -> tuple[Path, Path]:
    value = load_beat_cell_stage2_authority() if authority is None else authority
    output_paths = value.get("outputPaths")
    if not isinstance(output_paths, Mapping):  # pragma: no cover - authority validator owns this
        raise BeatCellSelectorCliError("The authority outputPaths projection is invalid.")
    publication = output_paths.get("publication")
    if (
        not isinstance(publication, Mapping)
        or set(publication) != _PUBLICATION_POLICY_FIELDS
        or publication.get("schemaVersion") != BEAT_CELL_STAGE2_PUBLICATION_POLICY_SCHEMA
        or publication.get("featureSet") != BEAT_CELL_FEATURE_SET_PUBLICATION_MODE
        or publication.get("singleJson") != BEAT_CELL_SINGLE_JSON_PUBLICATION_MODE
    ):
        raise BeatCellSelectorCliError("The authority publication policy is not the exact frozen split policy.")
    examples = output_paths.get("examplesArtifact")
    selector = output_paths.get("selectorArtifact")
    if not isinstance(examples, str) or not isinstance(selector, str):
        raise BeatCellSelectorCliError("The authority does not expose exact selector paths.")
    return Path(examples), Path(selector)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("train", "validate"))
    args = parser.parse_args(argv)
    try:
        authority = load_beat_cell_stage2_authority()
        examples_path, selector_path = _official_paths(authority)
        if args.action == "train":
            # The one-shot destination check precedes examples access and any fit.
            _preflight_new_output(selector_path)
        examples_raw, examples_inode = _sealed_read_snapshot(
            examples_path,
            "official beat-cell examples artifact",
        )
        examples = _strict_json(examples_raw, "official beat-cell examples artifact")
        if _canonical_bytes(examples) != examples_raw:
            raise BeatCellSelectorCliError("The official examples artifact is not canonical JSON bytes.")
        examples = _validate_official_examples_pre_fit(examples, authority)
        if args.action == "train":
            selector = train_beat_cell_selector(examples)

            def verify_examples_unchanged() -> None:
                _verify_snapshot(
                    examples_path,
                    examples_raw,
                    examples_inode,
                    "official beat-cell examples artifact",
                )

            _atomic_publish_new(
                selector_path,
                _canonical_bytes(selector),
                precommit_check=verify_examples_unchanged,
            )
        else:
            selector_raw, selector_inode = _sealed_read_snapshot(
                selector_path,
                "official beat-cell selector artifact",
            )
            selector = _strict_json(selector_raw, "official beat-cell selector artifact")
            if _canonical_bytes(selector) != selector_raw:
                raise BeatCellSelectorCliError("The official selector artifact is not canonical JSON bytes.")
            validate_beat_cell_selector_artifact(selector, examples)
            _verify_snapshot(
                examples_path,
                examples_raw,
                examples_inode,
                "official beat-cell examples artifact",
            )
            _verify_snapshot(
                selector_path,
                selector_raw,
                selector_inode,
                "official beat-cell selector artifact",
            )
        result = {
            "action": args.action,
            "examplesFileSha256": hashlib.sha256(examples_raw).hexdigest(),
            "selectorArtifactSha256": selector["artifactSha256"],
            "selectorPath": str(selector_path),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, TypeError, ValueError, OverflowError) as error:
        print(f"beat-cell selector {args.action} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
