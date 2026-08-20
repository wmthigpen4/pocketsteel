from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest
import steel_guitar_rag.chord_reader.cli as chord_reader_cli

from steel_guitar_rag.chord_reader.artifact_integrity import (
    FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA,
    FactorizedArtifactIntegrityError,
    seal_factorized_artifact_manifest,
    validate_factorized_artifact_manifest,
)


def _write_feature(
    path: Path,
    *,
    frames: int = 4,
    label_mask: bool = True,
    nan: bool = False,
    rogue: bool = False,
    object_array: bool = False,
) -> None:
    features = np.zeros((frames, 61), dtype=np.float16)
    if nan:
        features[0, 0] = np.nan
    arrays = {
        "features": features,
        "labels": np.zeros(frames, dtype=np.int64),
        "training_weight": np.asarray(1.0, dtype=np.float32),
    }
    if label_mask:
        arrays["label_valid"] = np.ones(frames, dtype=np.bool_)
    if rogue:
        arrays["rogue"] = np.zeros(1, dtype=np.float32)
    if object_array:
        arrays["labels"] = np.asarray([object()] * frames, dtype=object)
    np.savez_compressed(path, **arrays)


def _write_labels(path: Path, *, frames: int = 4) -> None:
    np.savez_compressed(
        path,
        root=np.ones(frames, dtype=np.int64),
        mode=np.ones(frames, dtype=np.int64),
        product=np.ones(frames, dtype=np.int64),
        structure=np.ones(frames, dtype=np.int64),
        quality=np.zeros(frames, dtype=np.int64),
        bass=np.zeros(frames, dtype=np.int64),
        boundary=np.zeros(frames, dtype=np.float32),
        label_valid=np.ones(frames, dtype=np.bool_),
    )


def _manifest(tmp_path: Path, *, tracks: int = 1) -> dict:
    values = []
    for index in range(tracks):
        feature = tmp_path / f"feature-{index}.npz"
        labels = tmp_path / f"labels-{index}.npz"
        _write_feature(feature)
        _write_labels(labels)
        values.append(
            {
                "id": f"track-{index}",
                "datasetId": "fixture-a" if index == 0 else "fixture-b",
                "split": "train" if index == 0 else "development",
                "path": str(feature.resolve()),
                "factorizedLabelsPath": str(labels.resolve()),
                "frames": 4,
                "durationSeconds": 0.4,
            }
        )
    return {
        "schemaVersion": "chord_factorized_label_cache_v2",
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "tracks": values,
    }


def test_factorized_artifact_seal_is_deterministic_and_complete(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, tracks=2)
    first = seal_factorized_artifact_manifest(manifest)
    second = seal_factorized_artifact_manifest(deepcopy(manifest))

    assert first == second
    assert first["artifactIntegrity"]["schemaVersion"] == FACTORIZED_ARTIFACT_INTEGRITY_SCHEMA
    assert len(first["artifactIntegrity"]["artifactSetSha256"]) == 64
    assert first["artifactIntegrity"]["trackCount"] == 2
    for track in first["artifactIntegrity"]["tracks"]:
        assert track["featureArtifact"]["bytes"] > 0
        assert len(track["featureArtifact"]["sha256"]) == 64
        assert track["factorizedLabelArtifact"]["bytes"] > 0
    assert validate_factorized_artifact_manifest(first) is first


def test_factorized_artifact_seal_accepts_exact_legacy_browser_allowlist(
    tmp_path: Path,
) -> None:
    manifest = _manifest(tmp_path)
    _write_feature(Path(manifest["tracks"][0]["path"]), label_mask=False)

    sealed = seal_factorized_artifact_manifest(manifest)

    assert validate_factorized_artifact_manifest(sealed) is sealed


def test_factorized_artifact_validation_rejects_file_tamper(tmp_path: Path) -> None:
    sealed = seal_factorized_artifact_manifest(_manifest(tmp_path))
    feature = Path(sealed["tracks"][0]["path"])
    _write_feature(feature)
    with np.load(feature, allow_pickle=False) as current:
        features = current["features"].copy()
    features[0, 0] = 1
    np.savez_compressed(
        feature,
        features=features,
        labels=np.zeros(4, dtype=np.int64),
        label_valid=np.ones(4, dtype=np.bool_),
        training_weight=np.asarray(1.0, dtype=np.float32),
    )

    with pytest.raises(FactorizedArtifactIntegrityError, match="hash or byte count changed"):
        validate_factorized_artifact_manifest(sealed)
    assert validate_factorized_artifact_manifest(sealed, verify_files=False) is sealed


def test_factorized_artifact_validation_rejects_manifest_path_swap(tmp_path: Path) -> None:
    sealed = seal_factorized_artifact_manifest(_manifest(tmp_path, tracks=2))
    swapped = deepcopy(sealed)
    swapped["tracks"][0]["path"], swapped["tracks"][1]["path"] = (
        swapped["tracks"][1]["path"],
        swapped["tracks"][0]["path"],
    )

    with pytest.raises(FactorizedArtifactIntegrityError, match="sealed path/split/frame identity"):
        validate_factorized_artifact_manifest(swapped)


def test_factorized_artifact_seal_rejects_rogue_npz_member(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    _write_feature(Path(manifest["tracks"][0]["path"]), rogue=True)

    with pytest.raises(FactorizedArtifactIntegrityError, match="member allowlist"):
        seal_factorized_artifact_manifest(manifest)


def test_factorized_artifact_seal_rejects_nonfinite_features(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    _write_feature(Path(manifest["tracks"][0]["path"]), nan=True)

    with pytest.raises(FactorizedArtifactIntegrityError, match="non-finite"):
        seal_factorized_artifact_manifest(manifest)


def test_factorized_artifact_seal_rejects_unsafe_object_array(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    _write_feature(Path(manifest["tracks"][0]["path"]), object_array=True)

    with pytest.raises(FactorizedArtifactIntegrityError, match="unsafe object array"):
        seal_factorized_artifact_manifest(manifest)


def test_factorized_artifact_seal_rejects_symlink(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    real = Path(manifest["tracks"][0]["path"])
    link = tmp_path / "linked-feature.npz"
    link.symlink_to(real)
    manifest["tracks"][0]["path"] = str(link.absolute())

    with pytest.raises(FactorizedArtifactIntegrityError, match="symlink"):
        seal_factorized_artifact_manifest(manifest)


def test_factorized_artifact_seal_rejects_label_frame_mismatch(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    _write_labels(Path(manifest["tracks"][0]["factorizedLabelsPath"]), frames=3)

    with pytest.raises(FactorizedArtifactIntegrityError, match="does not align"):
        seal_factorized_artifact_manifest(manifest)


def test_factorized_artifact_seal_refuses_signed_split_protocol(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    manifest["splitProtocol"] = {"schemaVersion": "chord_reader_split_protocol_v1"}

    with pytest.raises(FactorizedArtifactIntegrityError, match="seal its source manifest"):
        seal_factorized_artifact_manifest(manifest)


def test_seal_factorized_artifacts_cli_writes_valid_atomic_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    output = tmp_path / "sealed.json"
    source.write_text(json.dumps(_manifest(tmp_path)), encoding="utf-8")

    assert (
        chord_reader_cli.main(
            ["seal-factorized-artifacts", str(source), str(output)]
        )
        == 0
    )
    sealed = json.loads(output.read_text(encoding="utf-8"))
    validate_factorized_artifact_manifest(sealed)
    assert not list(tmp_path.glob(".sealed.json.*.tmp"))
