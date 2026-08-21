from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import steel_guitar_rag.chord_reader.selector_development as development
from steel_guitar_rag.chord_reader.audio_lineage import AUDIO_LINEAGE_SCHEMA
from steel_guitar_rag.chord_reader.bar_examples import EXAMPLES_SCHEMA, GROUP_MANIFEST_SCHEMA
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.bar_selector import BAR_SELECTOR_ARTIFACT_SCHEMA
from steel_guitar_rag.chord_reader.bar_uncertainty import BAR_FEATURE_NAMES
from steel_guitar_rag.chord_reader.runtime_bar_grid import INPUT_MANIFEST_SCHEMA


def _write_json(path: Path, value: dict[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(raw)
    return raw


def _full_metadata_rows(tmp_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        track_id: str,
        dataset_id: str,
        composition_id: str,
        **metadata: Any,
    ) -> None:
        rows.append(
            {
                "id": track_id,
                "datasetId": dataset_id,
                "compositionId": composition_id,
                "split": "development",
                "audioPath": str((tmp_path / "audio" / f"{track_id}.wav").resolve()),
                "referencePath": str((tmp_path / "references" / f"{track_id}.json").resolve()),
                **metadata,
            }
        )

    for index in range(2):
        add(f"aam-{index}", "aam", f"aam-work-{index}")
    for composition in range(3):
        for player in range(6):
            for performance in ("comp", "solo"):
                add(
                    f"guitar-{composition}-{player:02d}-{performance}",
                    "guitarset",
                    f"guitar-work-{composition}",
                    groupId=f"{player:02d}",
                    performanceRole=performance,
                )
    for composition in range(6):
        for capture in range(4):
            for speed in ("fast", "slow"):
                add(
                    f"idmt-{composition}-{capture}-{speed}",
                    "idmt_guitar",
                    f"idmt-work-{composition}",
                    groupId=f"capture-{capture}",
                    performanceSpeed=speed,
                )
    for index in range(156):
        add(f"nrgcp-{index}", "nrgcp", f"nrgcp-work-{index}")
    for composition in range(2):
        for performer in ("alice", "bob"):
            add(
                f"winter-{composition}-{performer}",
                "winterreise",
                f"winter-work-{composition}",
                groupId=performer,
            )
    rows.sort(key=lambda row: row["id"])
    assert len(rows) == 246
    return rows


def _two_aam_rows(tmp_path: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": f"aam-{index}",
            "datasetId": "aam",
            "compositionId": f"work-{index}",
            "split": "development",
            "audioPath": str((tmp_path / "audio" / f"aam-{index}.wav").resolve()),
            "referencePath": str((tmp_path / "references" / f"aam-{index}.json").resolve()),
        }
        for index in range(2)
    ]


def _expected_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_group: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (str(row["datasetId"]), str(row["compositionId"]))
        by_group[key] = by_group.get(key, 0) + 1
    sizes: dict[str, list[int]] = {}
    for (dataset_id, _composition_id), count in sorted(by_group.items()):
        sizes.setdefault(dataset_id, []).append(count)
    return development.build_expected_dataset_shape(sizes)


def _metadata_bundle(tmp_path: Path, rows: list[dict[str, Any]]) -> dict[str, Path]:
    winner_tracks = [
        {
            "id": row["id"],
            "datasetId": row["datasetId"],
            "compositionId": row["compositionId"],
            "split": "development",
            "sourceSplit": "train",
        }
        for row in rows
    ]
    winner = {
        "schemaVersion": "chord_factorized_label_cache_v2",
        "tracks": winner_tracks,
        "splitProtocol": {"outputManifestSha256": hashlib.sha256(b"winner-output").hexdigest()},
        "artifactIntegrity": {"artifactSetSha256": hashlib.sha256(b"winner-artifacts").hexdigest()},
    }
    source = {
        "schemaVersion": "chord_dataset_manifest_v1",
        "tracks": deepcopy(rows),
    }
    winner_path = tmp_path / "winner.json"
    source_path = tmp_path / "source.json"
    winner_raw = _write_json(winner_path, winner)
    source_raw = _write_json(source_path, source)
    lineage_payload = {
        "schemaVersion": AUDIO_LINEAGE_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "extractorContract": {"entrypoint": development.PRODUCTION_EXTRACTOR_ENTRYPOINT},
        "manifestBindings": {
            "winnerCacheManifest": {
                "path": str(winner_path.resolve()),
                "pathSha256": canonical_sha256(str(winner_path.resolve())),
                "fileSha256": hashlib.sha256(winner_raw).hexdigest(),
                "canonicalSha256": canonical_sha256(winner),
            },
            "developmentSourceManifest": {
                "path": str(source_path.resolve()),
                "pathSha256": canonical_sha256(str(source_path.resolve())),
                "fileSha256": hashlib.sha256(source_raw).hexdigest(),
                "canonicalSha256": canonical_sha256(source),
            },
        },
        "trackCount": len(rows),
        "tracks": [
            {
                "trackId": row["id"],
                "datasetId": row["datasetId"],
                "split": "development",
                "audioPath": str(
                    (
                        Path(row["audioPath"])
                        if Path(row["audioPath"]).is_absolute()
                        else source_path.parent / Path(row["audioPath"])
                    ).resolve()
                ),
            }
            for row in rows
        ],
    }
    lineage = {**lineage_payload, "artifactSha256": canonical_sha256(lineage_payload)}
    lineage_path = tmp_path / "lineage.json"
    _write_json(lineage_path, lineage)
    shape_path = tmp_path / "expected-shape.json"
    _write_json(shape_path, _expected_shape(rows))
    return {
        "winner": winner_path,
        "source": source_path,
        "lineage": lineage_path,
        "shape": shape_path,
    }


def _patch_metadata_validators(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(development, "validate_split_protocol_manifest", lambda value: value)
    monkeypatch.setattr(
        development,
        "validate_factorized_artifact_manifest",
        lambda value, verify_files=False: value,
    )
    monkeypatch.setattr(
        development,
        "validate_development_audio_lineage",
        lambda value, verify_files=False: value,
    )


def _prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str, Any]],
    *,
    expected_tracks: int,
    expected_base_groups: int,
    expected_confidence_groups: int,
    derivative_registry: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Path, Path, dict[str, Path]]:
    bundle = _metadata_bundle(tmp_path, rows)
    _patch_metadata_validators(monkeypatch)
    registry_path: Path | None = None
    if derivative_registry is not None:
        registry_path = tmp_path / "derivatives.json"
        _write_json(registry_path, derivative_registry)
    runtime_output = tmp_path / "prepared" / "runtime.json"
    descriptor_output = tmp_path / "prepared" / "groups.json"
    result = development.prepare_development_inputs(
        bundle["winner"],
        bundle["lineage"],
        bundle["source"],
        runtime_output,
        descriptor_output,
        expected_track_count=expected_tracks,
        expected_base_group_count=expected_base_groups,
        expected_confidence_group_count=expected_confidence_groups,
        expected_dataset_shape_path=bundle["shape"],
        derivative_registry_path=registry_path,
    )
    return result, runtime_output, descriptor_output, bundle


def test_prepares_exact_246_track_169_group_metadata_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, runtime_path, descriptor_path, _bundle = _prepare(
        tmp_path,
        monkeypatch,
        _full_metadata_rows(tmp_path),
        expected_tracks=246,
        expected_base_groups=169,
        expected_confidence_groups=169,
    )

    runtime = result["runtimeAudioManifest"]
    descriptor = result["groupDescriptorManifest"]
    assert runtime["schemaVersion"] == INPUT_MANIFEST_SCHEMA
    assert set(runtime) == {"schemaVersion", "split", "tracks"}
    assert len(runtime["tracks"]) == 246
    assert all(set(track) == {"id", "split", "audioPath"} for track in runtime["tracks"])
    assert descriptor["actualCounts"] == {
        "trackCount": 246,
        "baseGroupCount": 169,
        "confidenceGroupCount": 169,
    }
    assert descriptor["expectedCounts"] == descriptor["actualCounts"]
    assert descriptor["runtimeAudioManifestSha256"] == canonical_sha256(runtime)
    assert all(set(track) == development._GROUP_DESCRIPTOR_TRACK_FIELDS for track in descriptor["tracks"])
    assert descriptor["sourceBindings"]["derivativeRegistry"]["origin"] == ("embedded-explicit-empty-v1")
    dataset_counts = {
        row["datasetId"]: (row["trackCount"], row["baseGroupCount"])
        for row in descriptor["groupingAudit"]["datasetCounts"]
    }
    assert dataset_counts == {
        "aam": (2, 2),
        "guitarset": (36, 3),
        "idmt_guitar": (48, 6),
        "nrgcp": (156, 156),
        "winterreise": (4, 2),
    }
    shape_rows = {
        row["datasetId"]: (
            row["trackCount"],
            row["baseGroupCount"],
            row["baseGroupSizeHistogram"],
        )
        for row in descriptor["expectedDatasetShape"]["datasets"]
    }
    assert shape_rows == {
        "aam": (2, 2, [{"baseGroupSize": 1, "baseGroupCount": 2}]),
        "guitarset": (36, 3, [{"baseGroupSize": 12, "baseGroupCount": 3}]),
        "idmt_guitar": (48, 6, [{"baseGroupSize": 8, "baseGroupCount": 6}]),
        "nrgcp": (156, 156, [{"baseGroupSize": 1, "baseGroupCount": 156}]),
        "winterreise": (4, 2, [{"baseGroupSize": 2, "baseGroupCount": 2}]),
    }
    guitar_groups = [row for row in descriptor["groupingAudit"]["baseGroups"] if row["datasetId"] == "guitarset"]
    assert len(guitar_groups) == 3
    assert all(set(row["roles"]) == development._GUITARSET_ROLES for row in guitar_groups)
    development.validate_development_group_descriptor(descriptor)
    assert json.loads(runtime_path.read_text()) == runtime
    assert json.loads(descriptor_path.read_text()) == descriptor


def test_freezes_only_the_reviewed_246_track_169_group_shape(tmp_path: Path) -> None:
    output = tmp_path / "frozen" / "expected-shape.json"
    shape = development.freeze_reviewed_expected_dataset_shape(output)
    assert shape["trackCount"] == 246
    assert shape["baseGroupCount"] == 169
    assert {row["datasetId"]: row["baseGroupSizeHistogram"] for row in shape["datasets"]} == {
        "aam": [{"baseGroupSize": 1, "baseGroupCount": 2}],
        "guitarset": [{"baseGroupSize": 12, "baseGroupCount": 3}],
        "idmt_guitar": [{"baseGroupSize": 8, "baseGroupCount": 6}],
        "nrgcp": [{"baseGroupSize": 1, "baseGroupCount": 156}],
        "winterreise": [{"baseGroupSize": 2, "baseGroupCount": 2}],
    }
    assert json.loads(output.read_text()) == shape
    with pytest.raises(development.SelectorDevelopmentError, match="must be a new"):
        development.freeze_reviewed_expected_dataset_shape(output)


def test_reviewed_shape_gate_rejects_a_valid_custom_api_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _metadata_bundle(tmp_path, _two_aam_rows(tmp_path))
    _patch_metadata_validators(monkeypatch)
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match="independently reviewed"):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=2,
            expected_base_group_count=2,
            expected_confidence_group_count=2,
            expected_dataset_shape_path=bundle["shape"],
            require_reviewed_dataset_shape=True,
        )
    assert not runtime.exists()
    assert not groups.exists()


def test_derivative_registry_merges_only_complete_base_groups(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = development.build_derivative_registry(
        [
            {
                "confidenceGroupId": "derivative:same-song",
                "baseGroupIds": ["composition:aam:work-0", "composition:aam:work-1"],
            }
        ]
    )
    result, _runtime, _descriptor, _bundle = _prepare(
        tmp_path,
        monkeypatch,
        _two_aam_rows(tmp_path),
        expected_tracks=2,
        expected_base_groups=2,
        expected_confidence_groups=1,
        derivative_registry=registry,
    )
    descriptor = result["groupDescriptorManifest"]
    assert {track["confidenceGroupId"] for track in descriptor["tracks"]} == {"derivative:same-song"}
    assert {row["baseGroupId"] for row in descriptor["groupingAudit"]["baseGroups"]} == {
        "composition:aam:work-0",
        "composition:aam:work-1",
    }
    assert all(row["confidenceGroupId"] == "derivative:same-song" for row in descriptor["groupingAudit"]["baseGroups"])


def test_prepare_rebases_relative_source_paths_to_the_source_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = _two_aam_rows(tmp_path)
    for index, row in enumerate(rows):
        row["audioPath"] = f"audio/relative-{index}.wav"
        row["referencePath"] = f"references/relative-{index}.json"
    result, _runtime, _descriptor, _bundle = _prepare(
        tmp_path,
        monkeypatch,
        rows,
        expected_tracks=2,
        expected_base_groups=2,
        expected_confidence_groups=2,
    )
    assert [track["audioPath"] for track in result["runtimeAudioManifest"]["tracks"]] == [
        str((tmp_path / "audio" / f"relative-{index}.wav").resolve()) for index in range(2)
    ]
    assert [track["referencePath"] for track in result["groupDescriptorManifest"]["tracks"]] == [
        str((tmp_path / "references" / f"relative-{index}.json").resolve()) for index in range(2)
    ]


@pytest.mark.parametrize(
    ("relocated_name", "binding_name"),
    [
        ("winner", "winnerCacheManifest"),
        ("source", "developmentSourceManifest"),
    ],
)
def test_prepare_rejects_byte_identical_relocated_bound_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relocated_name: str,
    binding_name: str,
) -> None:
    rows = _two_aam_rows(tmp_path)
    for index, row in enumerate(rows):
        row["audioPath"] = f"audio/relative-{index}.wav"
        row["referencePath"] = f"references/relative-{index}.json"
    bundle = _metadata_bundle(tmp_path, rows)
    _patch_metadata_validators(monkeypatch)
    relocated = tmp_path / "relocated" / f"{relocated_name}.json"
    relocated.parent.mkdir()
    relocated.write_bytes(bundle[relocated_name].read_bytes())
    supplied = dict(bundle)
    supplied[relocated_name] = relocated
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match=f"exact supplied {binding_name}"):
        development.prepare_development_inputs(
            supplied["winner"],
            supplied["lineage"],
            supplied["source"],
            runtime,
            groups,
            expected_track_count=2,
            expected_base_group_count=2,
            expected_confidence_group_count=2,
            expected_dataset_shape_path=supplied["shape"],
        )
    assert not runtime.exists()
    assert not groups.exists()


@pytest.mark.parametrize(
    "shape_sizes",
    [
        {
            "aam": [1, 2],
            "guitarset": [12, 12, 12],
            "idmt_guitar": [8, 8, 8, 8, 8, 8],
            "nrgcp": [1] * 156,
            "winterreise": [1, 2],
        },
        {
            "aam": [1, 1],
            "guitarset": [11, 12, 13],
            "idmt_guitar": [8, 8, 8, 8, 8, 8],
            "nrgcp": [1] * 156,
            "winterreise": [2, 2],
        },
    ],
    ids=["shifted-dataset-counts", "shifted-base-size-distribution"],
)
def test_prepare_rejects_shifted_dataset_shape_with_same_global_246_169_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    shape_sizes: dict[str, list[int]],
) -> None:
    bundle = _metadata_bundle(tmp_path, _full_metadata_rows(tmp_path))
    _patch_metadata_validators(monkeypatch)
    shifted_shape = development.build_expected_dataset_shape(shape_sizes)
    assert shifted_shape["trackCount"] == 246
    assert shifted_shape["baseGroupCount"] == 169
    _write_json(bundle["shape"], shifted_shape)
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match="per-dataset shape"):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=246,
            expected_base_group_count=169,
            expected_confidence_group_count=169,
            expected_dataset_shape_path=bundle["shape"],
        )
    assert not runtime.exists()
    assert not groups.exists()


def test_derivative_registry_rejects_unknown_base_without_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = development.build_derivative_registry(
        [
            {
                "confidenceGroupId": "derivative:unknown",
                "baseGroupIds": ["composition:aam:work-0", "composition:aam:not-present"],
            }
        ]
    )
    bundle = _metadata_bundle(tmp_path, _two_aam_rows(tmp_path))
    _patch_metadata_validators(monkeypatch)
    registry_path = tmp_path / "registry.json"
    _write_json(registry_path, registry)
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match="outside the exact development set"):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=2,
            expected_base_group_count=2,
            expected_confidence_group_count=1,
            expected_dataset_shape_path=bundle["shape"],
            derivative_registry_path=registry_path,
        )
    assert not runtime.exists()
    assert not groups.exists()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ({"datasetId": "guitarset", "performanceRole": "comp", "groupId": "00"}, "guitarset:comp:player-00"),
        ({"datasetId": "guitarset", "performanceRole": "solo", "groupId": "05"}, "guitarset:solo:player-05"),
        ({"datasetId": "aam"}, "aam:mix"),
        ({"datasetId": "nrgcp"}, "nrgcp:mix"),
        (
            {"datasetId": "idmt_guitar", "groupId": "mic-a", "performanceSpeed": "fast"},
            "idmt_guitar:capture=mic-a;speed=fast",
        ),
        ({"datasetId": "winterreise", "groupId": "singer-a"}, "winterreise:performer=singer-a"),
    ],
)
def test_exact_dataset_audit_roles(source: dict[str, Any], expected: str) -> None:
    assert development._production_role(source, "track") == expected


@pytest.mark.parametrize(
    "source",
    [
        {"datasetId": "guitarset", "performanceRole": "rhythm", "groupId": "00"},
        {"datasetId": "guitarset", "performanceRole": "comp", "groupId": "06"},
        {"datasetId": "idmt_guitar", "groupId": "mic-a"},
        {"datasetId": "winterreise"},
        {"datasetId": "unregistered"},
    ],
)
def test_dataset_audit_roles_have_no_fallback(source: dict[str, Any]) -> None:
    with pytest.raises(development.SelectorDevelopmentError):
        development._production_role(source, "track")


@pytest.mark.parametrize(
    ("dataset_id", "role"),
    [
        ("aam", "audit:aam"),
        ("nrgcp", "nrgcp:other"),
        ("idmt_guitar", "idmt_guitar:capture=;speed=fast"),
        ("idmt_guitar", "idmt_guitar:capture=mic-a"),
        ("winterreise", "winterreise:performer="),
    ],
)
def test_output_audit_roles_are_exact(dataset_id: str, role: str) -> None:
    with pytest.raises(development.SelectorDevelopmentError):
        development._validate_output_role(dataset_id, role)


@pytest.mark.parametrize(
    ("counts", "match"),
    [
        ((1, 2, 2), "Caller-frozen counts"),
        ((2, 1, 2), "Caller-frozen counts"),
        ((2, 2, 1), "Prepared counts"),
    ],
)
def test_prepare_requires_caller_frozen_exact_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    counts: tuple[int, int, int],
    match: str,
) -> None:
    bundle = _metadata_bundle(tmp_path, _two_aam_rows(tmp_path))
    _patch_metadata_validators(monkeypatch)
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match=match):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=counts[0],
            expected_base_group_count=counts[1],
            expected_confidence_group_count=counts[2],
            expected_dataset_shape_path=bundle["shape"],
        )
    assert not runtime.exists()
    assert not groups.exists()


def test_prepare_requires_full_lineage_and_publishes_nothing_when_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _metadata_bundle(tmp_path, _two_aam_rows(tmp_path))
    _patch_metadata_validators(monkeypatch)
    bundle["lineage"].unlink()
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match="existing non-symlink"):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=2,
            expected_base_group_count=2,
            expected_confidence_group_count=2,
            expected_dataset_shape_path=bundle["shape"],
        )
    assert not runtime.exists()
    assert not groups.exists()


def test_prepare_refuses_existing_output_without_partial_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _metadata_bundle(tmp_path, _two_aam_rows(tmp_path))
    _patch_metadata_validators(monkeypatch)
    runtime = tmp_path / "runtime.json"
    runtime.write_text("keep", encoding="utf-8")
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match="must be a new"):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=2,
            expected_base_group_count=2,
            expected_confidence_group_count=2,
            expected_dataset_shape_path=bundle["shape"],
        )
    assert runtime.read_text() == "keep"
    assert not groups.exists()


def test_json_set_rolls_back_a_first_link_when_a_later_link_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    original_link = development.os.link
    calls = 0

    def fail_second_link(*args: Any, **kwargs: Any) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FileExistsError("synthetic race")
        original_link(*args, **kwargs)

    monkeypatch.setattr(development.os, "link", fail_second_link)
    with pytest.raises(development.SelectorDevelopmentError, match="concurrently created"):
        development._atomic_publish_json_set(
            {
                first: {"value": 1},
                second: {"value": 2},
            }
        )
    assert not first.exists()
    assert not second.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_json_set_rolls_back_when_post_link_verification_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "published.json"
    original_link = development.os.link
    original_stat = development.os.stat
    linked = False
    failed = False

    def mark_linked(*args: Any, **kwargs: Any) -> None:
        nonlocal linked
        original_link(*args, **kwargs)
        linked = True

    def fail_first_post_link_stat(*args: Any, **kwargs: Any) -> Any:
        nonlocal failed
        if linked and not failed:
            failed = True
            raise OSError("synthetic post-link stat failure")
        return original_stat(*args, **kwargs)

    monkeypatch.setattr(development.os, "link", mark_linked)
    monkeypatch.setattr(development.os, "stat", fail_first_post_link_stat)
    with pytest.raises(development.SelectorDevelopmentError, match="path changed"):
        development._atomic_publish_json_set({output: {"value": 1}})
    assert not output.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_json_set_retained_dirfd_rolls_back_after_parent_path_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publication_parent = tmp_path / "published"
    publication_parent.mkdir()
    moved_parent = tmp_path / "moved"
    output = publication_parent / "artifact.json"
    original_link = development.os.link
    swapped = False

    def swap_parent_after_link(*args: Any, **kwargs: Any) -> None:
        nonlocal swapped
        original_link(*args, **kwargs)
        if not swapped:
            swapped = True
            publication_parent.rename(moved_parent)
            publication_parent.mkdir()

    monkeypatch.setattr(development.os, "link", swap_parent_after_link)
    with pytest.raises(development.SelectorDevelopmentError, match="path changed"):
        development._atomic_publish_json_set({output: {"value": 1}})
    assert not (publication_parent / "artifact.json").exists()
    assert not (moved_parent / "artifact.json").exists()
    assert not list(publication_parent.glob(".*.tmp"))
    assert not list(moved_parent.glob(".*.tmp"))


def test_protected_source_split_rejects_before_validators_and_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _metadata_bundle(tmp_path, _two_aam_rows(tmp_path))
    source = json.loads(bundle["source"].read_text())
    source["tracks"][0]["split"] = "calibration"
    _write_json(bundle["source"], source)
    entered: list[str] = []
    monkeypatch.setattr(development, "validate_split_protocol_manifest", lambda value: entered.append("split"))
    monkeypatch.setattr(
        development,
        "validate_factorized_artifact_manifest",
        lambda value, verify_files=False: entered.append("artifact"),
    )
    monkeypatch.setattr(
        development,
        "validate_development_audio_lineage",
        lambda value, verify_files=False: entered.append("lineage"),
    )
    runtime = tmp_path / "runtime.json"
    groups = tmp_path / "groups.json"
    with pytest.raises(development.SelectorDevelopmentError, match="before nested paths"):
        development.prepare_development_inputs(
            bundle["winner"],
            bundle["lineage"],
            bundle["source"],
            runtime,
            groups,
            expected_track_count=2,
            expected_base_group_count=2,
            expected_confidence_group_count=2,
            expected_dataset_shape_path=bundle["shape"],
        )
    assert entered == []
    assert not runtime.exists()
    assert not groups.exists()


def test_attest_lineage_publishes_full_and_projection_as_one_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_payload = {
        "schemaVersion": AUDIO_LINEAGE_SCHEMA,
        "split": "development",
        "tracks": [{"trackId": "track", "split": "development"}],
    }
    lineage = {**lineage_payload, "artifactSha256": canonical_sha256(lineage_payload)}
    projection = {
        "schemaVersion": "chord_development_audio_lineage_projection_v1",
        "split": "development",
        "projectionSha256": hashlib.sha256(b"projection").hexdigest(),
    }

    def fake_builder(*args: Any) -> dict[str, Any]:
        output = Path(args[3])
        _write_json(output, lineage)
        return deepcopy(lineage)

    monkeypatch.setattr(development, "build_development_audio_lineage", fake_builder)
    monkeypatch.setattr(
        development,
        "validate_development_audio_lineage",
        lambda value, verify_files=False: value,
    )
    monkeypatch.setattr(
        development,
        "project_development_audio_lineage",
        lambda value: deepcopy(projection),
    )
    full_output = tmp_path / "out" / "lineage.json"
    projection_output = tmp_path / "out" / "projection.json"
    result = development.attest_development_lineage(
        tmp_path / "winner.json",
        tmp_path / "source.json",
        tmp_path / "dasheng.json",
        full_output,
        projection_output,
    )
    assert result == {"lineage": lineage, "projection": projection}
    assert json.loads(full_output.read_text()) == lineage
    assert json.loads(projection_output.read_text()) == projection
    assert not list(full_output.parent.glob("*.attestation-*.json"))


def test_attest_lineage_preflights_both_outputs_before_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered: list[bool] = []
    monkeypatch.setattr(
        development,
        "build_development_audio_lineage",
        lambda *args: entered.append(True),
    )
    projection = tmp_path / "projection.json"
    projection.write_text("keep", encoding="utf-8")
    with pytest.raises(development.SelectorDevelopmentError, match="must be a new"):
        development.attest_development_lineage(
            tmp_path / "winner.json",
            tmp_path / "source.json",
            tmp_path / "dasheng.json",
            tmp_path / "lineage.json",
            projection,
        )
    assert entered == []
    assert not (tmp_path / "lineage.json").exists()
    assert projection.read_text() == "keep"


def test_build_groups_calls_sealed_builder_and_persists_new_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _runtime, _descriptor, _bundle = _prepare(
        tmp_path,
        monkeypatch,
        _two_aam_rows(tmp_path),
        expected_tracks=2,
        expected_base_groups=2,
        expected_confidence_groups=2,
    )
    for track in result["groupDescriptorManifest"]["tracks"]:
        _write_json(
            Path(track["referencePath"]),
            {"segments": [{"start": 0.0, "end": 1.0, "label": "C:maj"}]},
        )
    output = tmp_path / "built" / "groups.json"
    manifest = development.build_development_groups(
        result["groupDescriptorManifest"],
        reference_root=tmp_path / "references",
        output_path=output,
    )
    assert manifest["schemaVersion"] == GROUP_MANIFEST_SCHEMA
    assert len(manifest["tracks"]) == 2
    assert json.loads(output.read_text()) == manifest


def _example_envelopes(tmp_path: Path) -> dict[str, Path]:
    values = {
        "report": {"split": "development", "tracks": [{"id": "track", "split": "development"}]},
        "lineage": {
            "schemaVersion": AUDIO_LINEAGE_SCHEMA,
            "split": "development",
            "tracks": [{"trackId": "track", "split": "development"}],
        },
        "runtime": {
            "split": "development",
            "tracks": [{"trackId": "track", "split": "development"}],
        },
        "groups": {
            "split": "development",
            "tracks": [{"trackId": "track", "split": "development"}],
        },
    }
    paths: dict[str, Path] = {}
    for name, value in values.items():
        path = tmp_path / "inputs" / f"{name}.json"
        _write_json(path, value)
        paths[name] = path
    return paths


def _certification_examples_artifact() -> dict[str, Any]:
    zero_counts = {field: 0 for field in development._LABEL_DETERMINACY_COUNT_FIELDS}
    aggregate_payload = {
        "schemaVersion": development.LABEL_DETERMINACY_AUDIT_SCHEMA,
        "estimand": "synthetic certification fixture",
        "oofDenominator": "synthetic certification fixture",
        **zero_counts,
    }
    aggregate = {
        **aggregate_payload,
        "auditSha256": canonical_sha256(aggregate_payload),
    }
    rows: list[dict[str, Any]] = []
    for dataset_id in development._CERTIFICATION_DATASET_IDS:
        row_payload = {"datasetId": dataset_id, **zero_counts}
        rows.append({**row_payload, "rowSha256": canonical_sha256(row_payload)})
    audit_payload = {
        "schemaVersion": development.DATASET_LABEL_DETERMINACY_AUDIT_SCHEMA,
        "strataMode": "certification-datasets-only-v1",
        "requiredDatasetIds": list(development._CERTIFICATION_DATASET_IDS),
        "datasetIds": list(development._CERTIFICATION_DATASET_IDS),
        "aggregateLabelDeterminacyAuditSha256": aggregate["auditSha256"],
        "rows": rows,
        "rowSetSha256": canonical_sha256(rows),
    }
    dataset_audit = {
        **audit_payload,
        "auditSha256": canonical_sha256(audit_payload),
    }
    artifact_payload = {
        "schemaVersion": EXAMPLES_SCHEMA,
        "split": "development",
        "labelDeterminacyAudit": aggregate,
        "labelDeterminacyAuditSha256": aggregate["auditSha256"],
        "datasetLabelDeterminacyAudit": dataset_audit,
        "datasetLabelDeterminacyAuditSha256": dataset_audit["auditSha256"],
    }
    return {**artifact_payload, "artifactSha256": canonical_sha256(artifact_payload)}


def test_build_examples_requires_full_lineage_and_atomically_publishes_summary_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _example_envelopes(tmp_path)
    roots = [tmp_path / name for name in ("benchmark", "runtime-root", "group-root")]
    for root in roots:
        root.mkdir()
    artifact = _certification_examples_artifact()
    captured: dict[str, Any] = {}

    def fake_builder(report: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        _write_json(Path(kwargs["summary_output_root"]) / "summary-a.json", {"sealed": True})
        return deepcopy(artifact)

    monkeypatch.setattr(development, "build_bar_selector_examples", fake_builder)
    summary_output = tmp_path / "published-summaries"
    output = tmp_path / "published-examples.json"
    result = development.build_development_examples(
        paths["report"],
        paths["lineage"],
        paths["runtime"],
        paths["groups"],
        benchmark_root=roots[0],
        runtime_bar_grid_root=roots[1],
        group_manifest_root=roots[2],
        summary_output_root=summary_output,
        output_path=output,
    )
    assert result == artifact
    assert captured["audio_lineage_manifest"]["schemaVersion"] == AUDIO_LINEAGE_SCHEMA
    assert json.loads(output.read_text()) == artifact
    assert json.loads((summary_output / "summary-a.json").read_text()) == {"sealed": True}


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("generic-stratum", "certification-only"),
        ("aggregate-mismatch", "do not sum"),
    ],
)
def test_build_examples_rejects_noncertification_or_mismatched_dataset_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    match: str,
) -> None:
    paths = _example_envelopes(tmp_path)
    roots = [tmp_path / name for name in ("benchmark", "runtime-root", "group-root")]
    for root in roots:
        root.mkdir()
    artifact = _certification_examples_artifact()
    audit = artifact["datasetLabelDeterminacyAudit"]
    if mutation == "generic-stratum":
        zero_counts = {field: 0 for field in development._LABEL_DETERMINACY_COUNT_FIELDS}
        row_payload = {"datasetId": "synthetic-custom", **zero_counts}
        audit["strataMode"] = "generic-with-custom-datasets-v1"
        audit["datasetIds"].append("synthetic-custom")
        audit["rows"].append({**row_payload, "rowSha256": canonical_sha256(row_payload)})
    else:
        audit["rows"][0]["totalBarCount"] = 1
        audit["rows"][0]["rowSha256"] = canonical_sha256(
            {key: value for key, value in audit["rows"][0].items() if key != "rowSha256"}
        )
    audit["rowSetSha256"] = canonical_sha256(audit["rows"])
    audit["auditSha256"] = canonical_sha256({key: value for key, value in audit.items() if key != "auditSha256"})
    artifact["datasetLabelDeterminacyAuditSha256"] = audit["auditSha256"]
    artifact["artifactSha256"] = canonical_sha256(
        {key: value for key, value in artifact.items() if key != "artifactSha256"}
    )

    def fake_builder(report: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        _write_json(Path(kwargs["summary_output_root"]) / "summary.json", {"sealed": True})
        return deepcopy(artifact)

    monkeypatch.setattr(development, "build_bar_selector_examples", fake_builder)
    output = tmp_path / "examples.json"
    summaries = tmp_path / "summaries"
    with pytest.raises(development.SelectorDevelopmentError, match=match):
        development.build_development_examples(
            paths["report"],
            paths["lineage"],
            paths["runtime"],
            paths["groups"],
            benchmark_root=roots[0],
            runtime_bar_grid_root=roots[1],
            group_manifest_root=roots[2],
            summary_output_root=summaries,
            output_path=output,
        )
    assert not summaries.exists()
    assert not output.exists()


def test_build_examples_failure_leaves_no_partial_summary_or_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _example_envelopes(tmp_path)
    roots = [tmp_path / name for name in ("benchmark", "runtime-root", "group-root")]
    for root in roots:
        root.mkdir()

    def failing_builder(report: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        _write_json(Path(kwargs["summary_output_root"]) / "partial.json", {"partial": True})
        raise ValueError("synthetic join failure")

    monkeypatch.setattr(development, "build_bar_selector_examples", failing_builder)
    summary_output = tmp_path / "published-summaries"
    output = tmp_path / "published-examples.json"
    with pytest.raises(ValueError, match="synthetic join failure"):
        development.build_development_examples(
            paths["report"],
            paths["lineage"],
            paths["runtime"],
            paths["groups"],
            benchmark_root=roots[0],
            runtime_bar_grid_root=roots[1],
            group_manifest_root=roots[2],
            summary_output_root=summary_output,
            output_path=output,
        )
    assert not summary_output.exists()
    assert not output.exists()


def test_summary_set_rolls_back_when_post_link_verification_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staging = tmp_path / "staging"
    _write_json(staging / "summary.json", {"sealed": True})
    publication_parent = tmp_path / "published"
    output = publication_parent / "examples.json"
    summaries = publication_parent / "summaries"
    original_link = development.os.link
    original_stat = development.os.stat
    linked = False
    failed = False

    def mark_linked(*args: Any, **kwargs: Any) -> None:
        nonlocal linked
        original_link(*args, **kwargs)
        linked = True

    def fail_first_post_link_stat(*args: Any, **kwargs: Any) -> Any:
        nonlocal failed
        if linked and not failed:
            failed = True
            raise OSError("synthetic post-link summary stat failure")
        return original_stat(*args, **kwargs)

    monkeypatch.setattr(development.os, "link", mark_linked)
    monkeypatch.setattr(development.os, "stat", fail_first_post_link_stat)
    with pytest.raises(development.SelectorDevelopmentError, match="path changed"):
        development._publish_json_and_summary_set(
            output,
            {"artifact": True},
            staging,
            summaries,
        )
    assert not output.exists()
    assert not summaries.exists()
    assert not list(publication_parent.glob(".*.tmp"))


def test_summary_set_retained_dirfds_roll_back_after_parent_path_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staging = tmp_path / "staging"
    _write_json(staging / "summary.json", {"sealed": True})
    publication_parent = tmp_path / "published"
    publication_parent.mkdir()
    moved_parent = tmp_path / "moved"
    output = publication_parent / "examples.json"
    summaries = publication_parent / "summaries"
    original_link = development.os.link
    swapped = False

    def swap_parent_after_first_link(*args: Any, **kwargs: Any) -> None:
        nonlocal swapped
        original_link(*args, **kwargs)
        if not swapped:
            swapped = True
            publication_parent.rename(moved_parent)
            publication_parent.mkdir()

    monkeypatch.setattr(development.os, "link", swap_parent_after_first_link)
    with pytest.raises(development.SelectorDevelopmentError, match="path changed"):
        development._publish_json_and_summary_set(
            output,
            {"artifact": True},
            staging,
            summaries,
        )
    assert not (publication_parent / "examples.json").exists()
    assert not (publication_parent / "summaries").exists()
    assert not (moved_parent / "examples.json").exists()
    assert not (moved_parent / "summaries").exists()
    assert not list(publication_parent.glob(".*.tmp"))
    assert not list(moved_parent.glob(".*.tmp"))


def test_build_examples_rejects_projection_in_place_of_full_lineage_before_join(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _example_envelopes(tmp_path)
    lineage = json.loads(paths["lineage"].read_text())
    lineage["schemaVersion"] = "chord_development_audio_lineage_projection_v1"
    _write_json(paths["lineage"], lineage)
    roots = [tmp_path / name for name in ("benchmark", "runtime-root", "group-root")]
    for root in roots:
        root.mkdir()
    entered: list[bool] = []
    monkeypatch.setattr(development, "build_bar_selector_examples", lambda *args, **kwargs: entered.append(True))
    with pytest.raises(development.SelectorDevelopmentError, match="full audio-lineage"):
        development.build_development_examples(
            paths["report"],
            paths["lineage"],
            paths["runtime"],
            paths["groups"],
            benchmark_root=roots[0],
            runtime_bar_grid_root=roots[1],
            group_manifest_root=roots[2],
            summary_output_root=tmp_path / "summaries",
            output_path=tmp_path / "examples.json",
        )
    assert entered == []
    assert not (tmp_path / "summaries").exists()
    assert not (tmp_path / "examples.json").exists()


def test_build_examples_rejects_protected_split_before_artifact_root_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _example_envelopes(tmp_path)
    runtime = json.loads(paths["runtime"].read_text())
    runtime["split"] = "calibration"
    runtime["tracks"][0]["split"] = "calibration"
    _write_json(paths["runtime"], runtime)
    entered: list[bool] = []
    monkeypatch.setattr(development, "build_bar_selector_examples", lambda *args, **kwargs: entered.append(True))
    with pytest.raises(development.SelectorDevelopmentError, match="before nested paths"):
        development.build_development_examples(
            paths["report"],
            paths["lineage"],
            paths["runtime"],
            paths["groups"],
            benchmark_root=tmp_path / "does-not-exist-benchmark",
            runtime_bar_grid_root=tmp_path / "does-not-exist-runtime",
            group_manifest_root=tmp_path / "does-not-exist-groups",
            summary_output_root=tmp_path / "summaries",
            output_path=tmp_path / "examples.json",
        )
    assert entered == []
    assert not (tmp_path / "summaries").exists()
    assert not (tmp_path / "examples.json").exists()


def test_train_selector_dispatches_and_persists_nonpromotable_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples = _certification_examples_artifact()
    examples["examples"] = [{"trackId": "track", "split": "development"}]
    examples["artifactSha256"] = canonical_sha256(
        {key: value for key, value in examples.items() if key != "artifactSha256"}
    )
    examples_path = tmp_path / "examples.json"
    _write_json(examples_path, examples)
    artifact = {
        "schemaVersion": BAR_SELECTOR_ARTIFACT_SCHEMA,
        "developmentOnly": True,
        "promotionEligible": False,
        "training": {"split": "development"},
        "artifactSha256": hashlib.sha256(b"selector").hexdigest(),
    }
    monkeypatch.setattr(development, "train_bar_selector", lambda value: deepcopy(artifact))
    output = tmp_path / "selector.json"
    assert development.train_development_selector(examples_path, output) == artifact
    assert json.loads(output.read_text()) == artifact


def test_train_selector_accepts_sort_keys_json_feature_mapping_round_trip(
    tmp_path: Path,
) -> None:
    from tests.test_chord_reader_bar_selector import _examples_artifact

    examples = _examples_artifact()
    examples_path = tmp_path / "examples.json"
    _write_json(examples_path, examples)
    persisted = json.loads(examples_path.read_text(encoding="utf-8"))
    persisted_features = persisted["examples"][0]["barSummary"]["featureValues"]
    assert set(persisted_features) == set(BAR_FEATURE_NAMES)
    assert tuple(persisted_features) != BAR_FEATURE_NAMES

    output = tmp_path / "selector.json"
    artifact = development.train_development_selector(examples_path, output)
    assert artifact["schemaVersion"] == BAR_SELECTOR_ARTIFACT_SCHEMA
    assert artifact["training"]["exampleCount"] == len(examples["examples"])
    assert json.loads(output.read_text(encoding="utf-8")) == artifact


def test_train_selector_rejects_generic_dataset_strata_before_trainer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples = _certification_examples_artifact()
    examples["examples"] = [{"trackId": "track", "split": "development"}]
    audit = examples["datasetLabelDeterminacyAudit"]
    zero_counts = {field: 0 for field in development._LABEL_DETERMINACY_COUNT_FIELDS}
    row_payload = {"datasetId": "synthetic-custom", **zero_counts}
    audit["strataMode"] = "generic-with-custom-datasets-v1"
    audit["datasetIds"].append("synthetic-custom")
    audit["rows"].append({**row_payload, "rowSha256": canonical_sha256(row_payload)})
    audit["rowSetSha256"] = canonical_sha256(audit["rows"])
    audit["auditSha256"] = canonical_sha256({key: value for key, value in audit.items() if key != "auditSha256"})
    examples["datasetLabelDeterminacyAuditSha256"] = audit["auditSha256"]
    examples["artifactSha256"] = canonical_sha256(
        {key: value for key, value in examples.items() if key != "artifactSha256"}
    )
    examples_path = tmp_path / "examples.json"
    _write_json(examples_path, examples)
    entered: list[bool] = []
    monkeypatch.setattr(development, "train_bar_selector", lambda value: entered.append(True))
    output = tmp_path / "selector.json"
    with pytest.raises(development.SelectorDevelopmentError, match="certification-only"):
        development.train_development_selector(examples_path, output)
    assert entered == []
    assert not output.exists()


def test_cli_dispatches_prepare_inputs_with_explicit_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, Any] = {}
    runtime = {"schemaVersion": INPUT_MANIFEST_SCHEMA, "split": "development", "tracks": []}
    descriptor = {"manifestSha256": hashlib.sha256(b"descriptor").hexdigest()}

    def fake_prepare(*args: Any, **kwargs: Any) -> dict[str, Any]:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {"runtimeAudioManifest": runtime, "groupDescriptorManifest": descriptor}

    monkeypatch.setattr(development, "prepare_development_inputs", fake_prepare)
    assert (
        development.main(
            [
                "prepare-inputs",
                "--winner-cache-manifest",
                str(tmp_path / "winner.json"),
                "--audio-lineage-manifest",
                str(tmp_path / "lineage.json"),
                "--development-source-manifest",
                str(tmp_path / "source.json"),
                "--expected-dataset-shape",
                str(tmp_path / "shape.json"),
                "--expected-track-count",
                "246",
                "--expected-base-group-count",
                "169",
                "--expected-confidence-group-count",
                "169",
                "--runtime-audio-output",
                str(tmp_path / "runtime.json"),
                "--group-descriptor-output",
                str(tmp_path / "groups.json"),
            ]
        )
        == 0
    )
    assert captured["kwargs"] == {
        "expected_track_count": 246,
        "expected_base_group_count": 169,
        "expected_confidence_group_count": 169,
        "expected_dataset_shape_path": tmp_path / "shape.json",
        "derivative_registry_path": None,
        "require_reviewed_dataset_shape": True,
    }
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["command"] == "prepare-inputs"
    assert receipt["runtimeAudioManifestSha256"] == canonical_sha256(runtime)


def test_cli_freezes_reviewed_shape_without_caller_shape_parameters(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "expected-shape.json"
    assert development.main(["freeze-expected-shape", "--output", str(output)]) == 0
    shape = json.loads(output.read_text())
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {
        "command": "freeze-expected-shape",
        "shapeSha256": shape["shapeSha256"],
    }
    assert shape["trackCount"] == 246
    assert shape["baseGroupCount"] == 169


def test_cli_dispatches_attest_groups_examples_and_training(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    digest = hashlib.sha256(b"cli").hexdigest()
    calls: list[str] = []
    monkeypatch.setattr(
        development,
        "attest_development_lineage",
        lambda *args: (
            calls.append("attest")
            or {
                "lineage": {"artifactSha256": digest},
                "projection": {"projectionSha256": digest},
            }
        ),
    )
    assert (
        development.main(
            [
                "attest-lineage",
                "--winner-cache-manifest",
                str(tmp_path / "winner.json"),
                "--development-source-manifest",
                str(tmp_path / "source.json"),
                "--dasheng-cache-manifest",
                str(tmp_path / "dasheng.json"),
                "--lineage-output",
                str(tmp_path / "lineage.json"),
                "--projection-output",
                str(tmp_path / "projection.json"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["command"] == "attest-lineage"

    descriptor_path = tmp_path / "descriptor.json"
    _write_json(descriptor_path, {"split": "development", "tracks": []})
    monkeypatch.setattr(
        development,
        "build_development_groups",
        lambda *args, **kwargs: calls.append("groups") or {"manifestSha256": digest},
    )
    assert (
        development.main(
            [
                "build-groups",
                "--group-descriptor",
                str(descriptor_path),
                "--reference-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "groups.json"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["command"] == "build-groups"

    monkeypatch.setattr(
        development,
        "build_development_examples",
        lambda *args, **kwargs: calls.append("examples") or {"artifactSha256": digest},
    )
    assert (
        development.main(
            [
                "build-examples",
                "--benchmark-report",
                str(tmp_path / "report.json"),
                "--audio-lineage-manifest",
                str(tmp_path / "lineage.json"),
                "--runtime-bar-grid-manifest",
                str(tmp_path / "runtime.json"),
                "--group-manifest",
                str(tmp_path / "groups.json"),
                "--benchmark-root",
                str(tmp_path / "benchmark"),
                "--runtime-bar-grid-root",
                str(tmp_path / "runtime-root"),
                "--group-manifest-root",
                str(tmp_path / "group-root"),
                "--summary-output-root",
                str(tmp_path / "summaries"),
                "--output",
                str(tmp_path / "examples.json"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["command"] == "build-examples"

    monkeypatch.setattr(
        development,
        "train_development_selector",
        lambda *args: calls.append("training") or {"artifactSha256": digest},
    )
    assert (
        development.main(
            [
                "train-selector",
                "--examples",
                str(tmp_path / "examples.json"),
                "--output",
                str(tmp_path / "selector.json"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["command"] == "train-selector"
    assert calls == ["attest", "groups", "examples", "training"]
