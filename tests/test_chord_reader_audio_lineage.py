from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pytest

from steel_guitar_rag.chord_reader.artifact_integrity import (
    FACTORIZED_LABEL_SCHEMA,
    seal_factorized_artifact_manifest,
)
from steel_guitar_rag.chord_reader.audio_lineage import (
    AUDIO_LINEAGE_PROJECTION_SCHEMA,
    AUDIO_LINEAGE_SCHEMA,
    DATASET_DESCRIPTOR_SCHEMA,
    build_development_audio_lineage,
    project_development_audio_lineage,
    validate_development_audio_lineage,
)
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.dasheng import DASHENG_REQUIRED_FILES
from steel_guitar_rag.chord_reader.dasheng_cache import DASHENG_FEATURE_SPEC_SCHEMA
from steel_guitar_rag.chord_reader.split_protocol import build_leak_resistant_split_manifest


_FIXTURE_DEPENDENCIES = {
    "python": "fixture",
    "librosa": "fixture",
    "numpy": "fixture",
    "scipy": "fixture",
    "soundfile": "fixture",
}


def _fixture_features(audio: Path, feature_kind: str) -> tuple[np.ndarray, float]:
    assert feature_kind == "multiband_chroma_v2"
    value = audio.read_bytes()[0] / 255.0
    return np.full((4, 61), value, dtype=np.float32), 0.4


def _one_value_mismatch(audio: Path, feature_kind: str) -> tuple[np.ndarray, float]:
    features, duration = _fixture_features(audio, feature_kind)
    features[0, 0] += 0.125
    return features, duration


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dasheng_manifest(tracks: list[dict[str, object]]) -> dict[str, object]:
    revision = "1" * 40
    weight_sha256 = "2" * 64
    runtime_hashes = {name: hashlib.sha256(name.encode()).hexdigest() for name in DASHENG_REQUIRED_FILES}
    runtime_hashes["model.safetensors"] = weight_sha256
    spec: dict[str, object] = {
        "schemaVersion": DASHENG_FEATURE_SPEC_SCHEMA,
        "featureKind": "dasheng_base_v1",
        "modelId": "mispeech/dasheng-base",
        "revision": revision,
        "weightSha256": weight_sha256,
        "runtimeFileSha256": {name: runtime_hashes[name] for name in sorted(runtime_hashes)},
        "sampleRate": 16_000,
        "nativeFrameSeconds": 0.04,
        "frameSeconds": 0.1,
        "featureCount": 768,
        "pooling": "interval_overlap_mean_v1",
        "timestampConvention": "left_edge_seconds_v1",
        "storageDtype": "float16",
        "augmentationPolicy": "none",
        "provenanceSha256": "3" * 64,
    }
    spec["featureSpecSha256"] = canonical_sha256(spec)
    dasheng_tracks = []
    for track in tracks:
        identifier = str(track["id"])
        audio_path = Path(str(track["audioPath"]))
        dasheng_tracks.append(
            {
                "id": identifier,
                "datasetId": track["datasetId"],
                "split": "train",
                "path": str((audio_path.parent / f"dasheng-{identifier}.npz").resolve()),
                "frames": 4,
                "durationSeconds": 0.4,
                "audioPath": str(audio_path.resolve()),
                "sourceAudioSha256": _sha256_file(audio_path),
                "sourceFeatureSha256": hashlib.sha256(f"source-{identifier}".encode()).hexdigest(),
                "featureSha256": hashlib.sha256(f"feature-{identifier}".encode()).hexdigest(),
                "featureSpecSha256": spec["featureSpecSha256"],
            }
        )
    dasheng_tracks.sort(key=lambda item: (str(item["datasetId"]), str(item["id"])))
    return {
        "schemaVersion": "chord_feature_cache_v1",
        "sampleRate": 16_000,
        "frameSeconds": 0.1,
        "featureKind": "dasheng_base_v1",
        "featureCount": 768,
        "modelId": "mispeech/dasheng-base",
        "revision": revision,
        "weightSha256": weight_sha256,
        "featureSpecSha256": spec["featureSpecSha256"],
        "augmentationPolicy": "none",
        "storageDtype": "float16",
        "selectedSplits": ["train"],
        "heldOutExtractionAuthorized": False,
        "featureSpec": spec,
        "sourceManifests": [{"sha256": "4" * 64}],
        "datasets": ["fixture"],
        "tracks": dasheng_tracks,
    }


def _fixture(tmp_path: Path) -> dict[str, object]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source: dict[str, object] = {
        "schemaVersion": FACTORIZED_LABEL_SCHEMA,
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "tracks": [],
    }
    tracks: list[dict[str, object]] = []
    for index, identifier in enumerate(("fixture-a", "fixture-b", "fixture-c"), start=1):
        audio_path = tmp_path / f"{identifier}.wav"
        audio_path.write_bytes(bytes([30 * index]) + f"audio-{identifier}".encode())
        features, duration = _fixture_features(audio_path, "multiband_chroma_v2")
        feature_path = tmp_path / f"{identifier}-features.npz"
        label_path = tmp_path / f"{identifier}-labels.npz"
        np.savez_compressed(
            feature_path,
            features=features.astype(np.float16),
            labels=np.zeros(4, dtype=np.int64),
            label_valid=np.ones(4, dtype=np.bool_),
            training_weight=np.asarray(1.0, dtype=np.float32),
        )
        np.savez_compressed(
            label_path,
            root=np.ones(4, dtype=np.int64),
            mode=np.ones(4, dtype=np.int64),
            product=np.ones(4, dtype=np.int64),
            structure=np.ones(4, dtype=np.int64),
            quality=np.zeros(4, dtype=np.int64),
            bass=np.zeros(4, dtype=np.int64),
            boundary=np.zeros(4, dtype=np.float32),
            label_valid=np.ones(4, dtype=np.bool_),
        )
        track = {
            "id": identifier,
            "datasetId": "fixture",
            "compositionId": f"composition-{index}",
            "split": "train",
            "trainingWeight": 1.0,
            "audioPath": str(audio_path.resolve()),
            "path": str(feature_path.resolve()),
            "factorizedLabelsPath": str(label_path.resolve()),
            "frames": 4,
            "durationSeconds": duration,
        }
        tracks.append(track)
        source["tracks"].append(  # type: ignore[union-attr]
            {key: value for key, value in track.items() if key != "audioPath"}
        )

    sealed = seal_factorized_artifact_manifest(source)
    winner = build_leak_resistant_split_manifest(sealed, seed="audio-lineage-fixture")
    development = [track for track in winner["tracks"] if track["split"] == "development"]
    assert len(development) == 1
    descriptor = {
        "schemaVersion": DATASET_DESCRIPTOR_SCHEMA,
        "tracks": [
            {
                "id": track["id"],
                "datasetId": track["datasetId"],
                "split": "development",
                "audioPath": next(item["audioPath"] for item in tracks if item["id"] == track["id"]),
                "referencePath": str(tmp_path / f"protected-{track['id']}.json"),
                "timingMetadata": {"referenceFree": False, "bars": [0.0, 0.4]},
            }
            for track in development
        ],
    }
    dasheng = _dasheng_manifest(tracks)
    winner_path = tmp_path / "winner.json"
    source_path = tmp_path / "development-source.json"
    dasheng_path = tmp_path / "dasheng.json"
    _write_json(winner_path, winner)
    _write_json(source_path, descriptor)
    _write_json(dasheng_path, dasheng)
    return {
        "winner": winner,
        "source": descriptor,
        "dasheng": dasheng,
        "winnerPath": winner_path,
        "sourcePath": source_path,
        "dashengPath": dasheng_path,
        "development": development,
    }


def _build(fixture: dict[str, object], output: Path, extractor=_fixture_features) -> dict[str, object]:
    return build_development_audio_lineage(
        fixture["winnerPath"],  # type: ignore[arg-type]
        fixture["sourcePath"],  # type: ignore[arg-type]
        fixture["dashengPath"],  # type: ignore[arg-type]
        output,
        extractor=extractor,
        dependency_versions=_FIXTURE_DEPENDENCIES,
    )


def test_builds_deterministic_byte_exact_development_lineage(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    first = _build(fixture, tmp_path / "lineage-a.json")
    second = _build(fixture, tmp_path / "lineage-b.json")

    assert first == second
    assert first["schemaVersion"] == AUDIO_LINEAGE_SCHEMA
    assert first["split"] == "development"
    assert first["developmentOnly"] is True
    assert first["promotionEligible"] is False
    assert first["trackCount"] == 1
    assert first["tracks"][0]["cachedArraySha256"] == first["tracks"][0]["freshArraySha256"]
    assert first["tracks"][0]["featureCount"] == 61
    assert first["tracks"][0]["elementCount"] == 244
    assert first["manifestBindings"]["winnerCacheAudioBindingStatus"] == ("absent_repaired_by_fresh_array_equality_v1")
    assert first["artifactSha256"] == canonical_sha256(
        {key: value for key, value in first.items() if key != "artifactSha256"}
    )
    validate_development_audio_lineage(
        first,
        verify_files=True,
        extractor=_fixture_features,
        dependency_versions=_FIXTURE_DEPENDENCIES,
    )
    assert json.loads((tmp_path / "lineage-a.json").read_text()) == first


def test_projection_is_compact_sealed_and_deterministic(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    artifact = _build(fixture, tmp_path / "lineage.json")
    track_id = artifact["tracks"][0]["trackId"]

    first = project_development_audio_lineage(artifact, [track_id])
    second = project_development_audio_lineage(artifact)

    assert first == second
    assert first["schemaVersion"] == AUDIO_LINEAGE_PROJECTION_SCHEMA
    assert first["sourceAudioLineageSha256"] == artifact["artifactSha256"]
    assert "audioPath" not in first["tracks"][0]
    assert first["projectionSha256"] == canonical_sha256(
        {key: value for key, value in first.items() if key != "projectionSha256"}
    )
    with pytest.raises(ValueError, match="unknown"):
        project_development_audio_lineage(artifact, ["not-a-track"])


@pytest.mark.parametrize("forbidden_split", ["train", "calibration", "test", "confirmation"])
def test_rejects_source_split_before_nested_path_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    forbidden_split: str,
) -> None:
    fixture = _fixture(tmp_path)
    source = deepcopy(fixture["source"])
    source["tracks"][0]["split"] = forbidden_split
    _write_json(fixture["sourcePath"], source)  # type: ignore[arg-type]
    from steel_guitar_rag.chord_reader import audio_lineage

    touched: list[Path] = []
    original = audio_lineage._stable_file

    def recording(path: Path, name: str, **kwargs):
        touched.append(path)
        return original(path, name, **kwargs)

    monkeypatch.setattr(audio_lineage, "_stable_file", recording)
    output = tmp_path / "lineage.json"
    with pytest.raises(ValueError, match="development-only"):
        _build(fixture, output)

    assert not output.exists()
    assert touched
    assert all(path.suffix == ".json" for path in touched)


def test_rejects_tampered_signed_winner_before_nested_path_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    winner = deepcopy(fixture["winner"])
    development = next(track for track in winner["tracks"] if track["split"] == "development")
    development["split"] = "calibration"
    _write_json(fixture["winnerPath"], winner)  # type: ignore[arg-type]
    from steel_guitar_rag.chord_reader import audio_lineage

    touched: list[Path] = []
    original = audio_lineage._stable_file

    def recording(path: Path, name: str, **kwargs):
        touched.append(path)
        return original(path, name, **kwargs)

    monkeypatch.setattr(audio_lineage, "_stable_file", recording)
    output = tmp_path / "lineage.json"
    with pytest.raises(ValueError, match="hash mismatch"):
        _build(fixture, output)

    assert not output.exists()
    assert all(path.suffix == ".json" for path in touched)


def test_one_value_array_mismatch_fails_without_publication(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    output = tmp_path / "lineage.json"

    with pytest.raises(ValueError, match="array bytes differ"):
        _build(fixture, output, extractor=_one_value_mismatch)

    assert not output.exists()


def test_rejects_source_id_and_dataset_mismatch(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    source = deepcopy(fixture["source"])
    source["tracks"][0]["id"] = "different-id"
    _write_json(fixture["sourcePath"], source)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exactly match"):
        _build(fixture, tmp_path / "id-output.json")

    fixture = _fixture(tmp_path / "dataset-case")
    source = deepcopy(fixture["source"])
    source["tracks"][0]["datasetId"] = "different-dataset"
    _write_json(fixture["sourcePath"], source)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="datasetId differs"):
        _build(fixture, tmp_path / "dataset-output.json")


def test_rejects_source_path_and_dasheng_audio_hash_mismatch(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    source = deepcopy(fixture["source"])
    source["tracks"][0]["audioPath"] = str(tmp_path / "different.wav")
    _write_json(fixture["sourcePath"], source)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="audioPath differs"):
        _build(fixture, tmp_path / "path-output.json")

    fixture = _fixture(tmp_path / "hash-case")
    dasheng = deepcopy(fixture["dasheng"])
    development_id = fixture["development"][0]["id"]
    next(track for track in dasheng["tracks"] if track["id"] == development_id)["sourceAudioSha256"] = "0" * 64
    _write_json(fixture["dashengPath"], dasheng)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Dasheng corroboration"):
        _build(fixture, tmp_path / "hash-output.json")


def test_rejects_audio_and_frozen_cache_tamper_without_publication(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    development = fixture["development"][0]
    Path(fixture["source"]["tracks"][0]["audioPath"]).write_bytes(b"changed-audio")
    audio_output = tmp_path / "audio-output.json"
    with pytest.raises(ValueError, match="Dasheng corroboration"):
        _build(fixture, audio_output)
    assert not audio_output.exists()

    fixture = _fixture(tmp_path / "cache-case")
    development = fixture["development"][0]
    with Path(development["path"]).open("ab") as handle:
        handle.write(b"tamper")
    cache_output = tmp_path / "cache-output.json"
    with pytest.raises(ValueError, match="artifactIntegrity"):
        _build(fixture, cache_output)
    assert not cache_output.exists()


def test_validator_rejects_row_tamper_and_bound_file_tamper(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    artifact = _build(fixture, tmp_path / "lineage.json")
    tampered = deepcopy(artifact)
    tampered["tracks"][0]["frames"] += 1
    with pytest.raises(ValueError, match="feature dimensions|row hash"):
        validate_development_audio_lineage(tampered)

    source_path = fixture["sourcePath"]
    with Path(source_path).open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(ValueError, match="file bytes changed"):
        validate_development_audio_lineage(
            artifact,
            verify_files=True,
            extractor=_fixture_features,
            dependency_versions=_FIXTURE_DEPENDENCIES,
        )


def test_atomic_output_refuses_existing_destination(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    output = tmp_path / "lineage.json"
    output.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a new"):
        _build(fixture, output)

    assert output.read_text(encoding="utf-8") == "keep"


def test_json_hash_and_parse_use_the_same_captured_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from steel_guitar_rag.chord_reader import audio_lineage

    path = tmp_path / "manifest.json"
    original = b'{"schemaVersion":"schema-a","tracks":[]}\n'
    replacement = b'{"schemaVersion":"schema-b","tracks":[]}\n'
    assert len(original) == len(replacement)
    path.write_bytes(original)
    original_stat = path.stat()
    stable_file = audio_lineage._stable_file

    def mutate_after_capture(candidate: Path, name: str, **kwargs):
        captured = stable_file(candidate, name, **kwargs)
        if candidate == path:
            path.write_bytes(replacement)
            os.utime(
                path,
                ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
            )
        return captured

    monkeypatch.setattr(audio_lineage, "_stable_file", mutate_after_capture)
    loaded = audio_lineage._load_json(path, "adversarial manifest")

    assert loaded.sha256 == hashlib.sha256(original).hexdigest()
    assert loaded.value == {"schemaVersion": "schema-a", "tracks": []}
    assert loaded.canonical_sha256 == canonical_sha256(loaded.value)
    assert path.read_bytes() == replacement


def test_npz_features_are_loaded_from_captured_bytes_after_path_swap(tmp_path: Path) -> None:
    from steel_guitar_rag.chord_reader import audio_lineage

    path = tmp_path / "features.npz"
    replacement = tmp_path / "replacement.npz"

    def write_npz(candidate: Path, value: float) -> None:
        np.savez_compressed(
            candidate,
            features=np.full((4, 61), value, dtype=np.float16),
            labels=np.zeros(4, dtype=np.int64),
            label_valid=np.ones(4, dtype=np.bool_),
            training_weight=np.asarray(1.0, dtype=np.float32),
        )

    write_npz(path, 0.25)
    captured = audio_lineage._stable_file(
        path,
        "adversarial feature cache",
        expected_suffixes=frozenset({".npz"}),
        capture_bytes=True,
    )
    assert captured.captured is not None
    write_npz(replacement, 0.75)
    os.replace(replacement, path)

    features = audio_lineage._load_cached_features(
        captured.captured,
        "adversarial feature cache",
    )

    assert np.all(features == np.float16(0.25))
    with np.load(path, allow_pickle=False) as current:
        assert np.all(current["features"] == np.float16(0.75))


def test_audio_extractor_uses_private_snapshot_and_rejects_source_swap(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    source_audio = Path(str(fixture["source"]["tracks"][0]["audioPath"]))
    original = source_audio.read_bytes()
    original_stat = source_audio.stat()
    snapshots: list[Path] = []
    observed: list[bytes] = []

    def adversarial_extractor(snapshot: Path, feature_kind: str) -> tuple[np.ndarray, float]:
        snapshots.append(snapshot)
        observed.append(snapshot.read_bytes())
        assert snapshot != source_audio
        source_audio.write_bytes(b"Z" * len(original))
        os.utime(
            source_audio,
            ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
        )
        return _fixture_features(snapshot, feature_kind)

    output = tmp_path / "lineage.json"
    with pytest.raises(ValueError, match="changed after validation"):
        _build(fixture, output, extractor=adversarial_extractor)

    assert observed == [original]
    assert snapshots and all(not snapshot.exists() for snapshot in snapshots)
    assert not output.exists()


def test_dirfd_publication_cannot_be_redirected_by_parent_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from steel_guitar_rag.chord_reader import audio_lineage

    fixture = _fixture(tmp_path / "fixture")
    output_parent = tmp_path / "publish"
    original_parent = tmp_path / "publish-original"
    attacker_parent = tmp_path / "attacker"
    attacker_parent.mkdir()
    output = output_parent / "lineage.json"
    real_link = audio_lineage.os.link
    swapped = False

    def swap_parent_then_link(source: str, destination: str, **kwargs):
        nonlocal swapped
        if destination == output.name and not swapped:
            swapped = True
            output_parent.rename(original_parent)
            output_parent.symlink_to(attacker_parent, target_is_directory=True)
        return real_link(source, destination, **kwargs)

    monkeypatch.setattr(audio_lineage.os, "link", swap_parent_then_link)
    with pytest.raises(ValueError, match="without following symlinks|parent changed"):
        _build(fixture, output)

    assert swapped is True
    assert not (attacker_parent / output.name).exists()
    assert not (original_parent / output.name).exists()
    assert list(original_parent.iterdir()) == []
