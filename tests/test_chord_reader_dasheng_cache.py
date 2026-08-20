from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from steel_guitar_rag.chord_reader.dasheng import (
    DashengFeatureBatch,
    dasheng_feature_provenance,
    load_dasheng_contract,
)
from steel_guitar_rag.chord_reader.dasheng_cache import (
    DashengCacheError,
    cache_dasheng_features,
    dasheng_cache_feature_spec,
)
from steel_guitar_rag.chord_reader.factorized import (
    FACTORIZED_LABEL_SCHEMA,
    cache_factorized_labels,
)


class _FakeExtractor:
    def __init__(
        self,
        *,
        fail_ids: set[str] | None = None,
        wrong_frames: bool = False,
        wrong_timestamps: bool = False,
    ) -> None:
        self.provenance = dasheng_feature_provenance(load_dasheng_contract())
        self.fail_ids = fail_ids or set()
        self.wrong_frames = wrong_frames
        self.wrong_timestamps = wrong_timestamps
        self.calls: list[Path] = []

    def extract(self, audio: Path) -> DashengFeatureBatch:
        self.calls.append(audio)
        if audio.stem in self.fail_ids:
            raise RuntimeError(f"deliberate extraction failure for {audio.stem}")
        frames = 2 if self.wrong_frames else 3
        features = np.full((frames, 768), len(self.calls) / 10, dtype=np.float32)
        timestamps = np.arange(frames, dtype=np.float64) * 0.1
        if self.wrong_timestamps:
            timestamps[-1] += 0.01
        return DashengFeatureBatch(
            features=features,
            timestamps_seconds=timestamps,
            duration_seconds=0.25,
            provenance=self.provenance,
        )


def _track(
    identifier: str,
    split: str,
    audio_path: str | Path,
    reference_path: str | Path,
    *,
    dataset: str = "fixture",
    split_group: str | None = None,
) -> dict[str, object]:
    return {
        "id": identifier,
        "datasetId": dataset,
        "groupId": split_group or identifier,
        "splitGroup": split_group or f"composition-{identifier}",
        "split": split,
        "audioPath": str(audio_path),
        "referencePath": str(reference_path),
        "labelSource": "ground_truth",
        "trainingWeight": 0.0 if split in {"test", "steel_test"} else 1.0,
        "durationSeconds": 0.25,
    }


def _reference(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "durationSeconds": 0.25,
                "segments": [{"start": 0.0, "end": 0.25, "label": "C:maj"}],
            }
        ),
        encoding="utf-8",
    )


def _manifest(*tracks: dict[str, object]) -> dict[str, object]:
    return {"schemaVersion": "chord_track_manifest_v1", "tracks": list(tracks)}


def test_default_cache_combines_manifests_but_never_extracts_test(tmp_path: Path) -> None:
    train_audio = tmp_path / "train.wav"
    development_audio = tmp_path / "development.wav"
    test_audio = tmp_path / "test.wav"
    for index, audio in enumerate((train_audio, development_audio, test_audio)):
        audio.write_bytes(f"audio-{index}".encode())
    train_reference = tmp_path / "train.json"
    development_reference = tmp_path / "development.json"
    test_reference = tmp_path / "test.json"
    for reference in (train_reference, development_reference, test_reference):
        _reference(reference)

    first = _manifest(
        _track("train", "train", train_audio, train_reference),
        _track("test", "test", test_audio, test_reference),
    )
    second_root = tmp_path / "second"
    second_root.mkdir()
    relative_audio = second_root / "development.wav"
    relative_audio.write_bytes(development_audio.read_bytes())
    relative_reference = second_root / "development.json"
    _reference(relative_reference)
    second = _manifest(
        _track(
            "development",
            "development",
            "development.wav",
            "development.json",
            dataset="second-fixture",
        )
    )
    second_path = second_root / "manifest.json"
    second_path.write_text(json.dumps(second), encoding="utf-8")

    extractor = _FakeExtractor()
    output = cache_dasheng_features([first, second_path], tmp_path / "cache", extractor=extractor)

    assert output["schemaVersion"] == "chord_feature_cache_v1"
    assert output["featureKind"] == "dasheng_base_v1"
    assert output["featureCount"] == 768
    assert output["sampleRate"] == 16000
    assert output["frameSeconds"] == 0.1
    assert output["augmentationPolicy"] == "none"
    assert output["storageDtype"] == "float16"
    assert output["selectedSplits"] == ["development", "train"]
    assert output["heldOutExtractionAuthorized"] is False
    assert len(output["revision"]) == 40
    assert len(output["weightSha256"]) == 64
    assert len(output["featureSpecSha256"]) == 64
    assert [item["id"] for item in output["tracks"]] == ["train", "development"]
    assert {path.stem for path in extractor.calls} == {"train", "development"}
    assert not (tmp_path / "cache" / "test").exists()
    assert json.loads((tmp_path / "cache" / "manifest.json").read_text()) == output

    for item in output["tracks"]:
        with np.load(Path(item["path"]), allow_pickle=False) as cached:
            assert cached["features"].dtype == np.float16
            assert cached["features"].shape == (3, 768)
            assert cached["timestamps_seconds"].tolist() == pytest.approx([0.0, 0.1, 0.2])
            assert cached["augmentation_policy"].item() == "none"
            assert not any(cached[name].dtype.hasobject for name in cached.files)

    # This is the actual downstream contract, not merely a shape assertion.
    factorized_second = _manifest(
        {
            **second["tracks"][0],
            "audioPath": str(relative_audio),
            "referencePath": str(relative_reference),
        }
    )
    factorized = cache_factorized_labels(
        output, [first, factorized_second], tmp_path / "labels"
    )
    assert factorized["schemaVersion"] == FACTORIZED_LABEL_SCHEMA
    assert all(Path(item["factorizedLabelsPath"]).is_file() for item in factorized["tracks"])


def test_held_out_extraction_requires_two_explicit_signals(tmp_path: Path) -> None:
    audio = tmp_path / "test.wav"
    reference = tmp_path / "test.json"
    audio.write_bytes(b"held-out-audio")
    _reference(reference)
    manifest = _manifest(_track("test-track", "test", audio, reference))
    extractor = _FakeExtractor()

    with pytest.raises(DashengCacheError, match="allow_held_out=True"):
        cache_dasheng_features(
            manifest,
            tmp_path / "refused",
            splits={"test"},
            extractor=extractor,
        )
    assert extractor.calls == []

    output = cache_dasheng_features(
        manifest,
        tmp_path / "allowed",
        splits={"test"},
        allow_held_out=True,
        extractor=extractor,
    )
    assert output["selectedSplits"] == ["test"]
    assert output["heldOutExtractionAuthorized"] is True
    assert len(extractor.calls) == 1


def test_valid_files_are_reused_and_changed_audio_fails_closed(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    reference = tmp_path / "song.json"
    audio.write_bytes(b"first audio bytes")
    _reference(reference)
    manifest = _manifest(_track("song", "train", audio, reference))
    extractor = _FakeExtractor()
    root = tmp_path / "cache"

    first = cache_dasheng_features(manifest, root, extractor=extractor)
    first_path = Path(first["tracks"][0]["path"])
    first_bytes = first_path.read_bytes()
    second = cache_dasheng_features(manifest, root, extractor=extractor)
    assert len(extractor.calls) == 1
    assert second == first
    assert first_path.read_bytes() == first_bytes

    audio.write_bytes(b"different audio bytes")
    with pytest.raises(DashengCacheError, match="stale or invalid"):
        cache_dasheng_features(manifest, root, extractor=extractor)
    assert len(extractor.calls) == 1

    replaced = cache_dasheng_features(manifest, root, extractor=extractor, overwrite=True)
    assert len(extractor.calls) == 2
    assert replaced["tracks"][0]["sourceAudioSha256"] != first["tracks"][0]["sourceAudioSha256"]


@pytest.mark.parametrize(
    ("extractor", "message"),
    [
        (_FakeExtractor(wrong_frames=True), "produced shape"),
        (_FakeExtractor(wrong_timestamps=True), "exact 10 Hz"),
    ],
)
def test_misaligned_extraction_never_publishes_a_target_or_manifest(
    tmp_path: Path,
    extractor: _FakeExtractor,
    message: str,
) -> None:
    audio = tmp_path / "song.wav"
    reference = tmp_path / "song.json"
    audio.write_bytes(b"audio")
    _reference(reference)
    manifest = _manifest(_track("song", "train", audio, reference))
    root = tmp_path / "cache"

    with pytest.raises(DashengCacheError, match=message):
        cache_dasheng_features(manifest, root, extractor=extractor)
    assert not (root / "manifest.json").exists()
    assert list(root.rglob("*.npz")) == []
    assert list(root.rglob("*.tmp")) == []


def test_injected_extractor_provenance_is_verified_before_audio_work(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    reference = tmp_path / "song.json"
    audio.write_bytes(b"audio")
    _reference(reference)
    manifest = _manifest(_track("song", "train", audio, reference))
    extractor = _FakeExtractor()
    extractor.provenance = {**extractor.provenance, "modelId": "mutable/model"}

    with pytest.raises(DashengCacheError, match="modelId"):
        cache_dasheng_features(manifest, tmp_path / "cache", extractor=extractor)
    assert extractor.calls == []


def test_track_files_are_atomic_and_an_interrupted_run_is_restartable(tmp_path: Path) -> None:
    tracks = []
    for identifier in ("a", "b"):
        audio = tmp_path / f"{identifier}.wav"
        reference = tmp_path / f"{identifier}.json"
        audio.write_bytes(identifier.encode())
        _reference(reference)
        tracks.append(_track(identifier, "train", audio, reference))
    manifest = _manifest(*tracks)
    root = tmp_path / "cache"
    failing = _FakeExtractor(fail_ids={"b"})

    with pytest.raises(RuntimeError, match="deliberate extraction failure"):
        cache_dasheng_features(manifest, root, extractor=failing)
    assert len(list(root.rglob("*.npz"))) == 1
    assert list(root.rglob("*.tmp")) == []
    assert not (root / "manifest.json").exists()

    resumed = _FakeExtractor()
    output = cache_dasheng_features(manifest, root, extractor=resumed)
    assert [path.stem for path in resumed.calls] == ["b"]
    assert len(output["tracks"]) == 2
    assert (root / "manifest.json").is_file()


def test_unsafe_track_ids_cannot_escape_the_cache_root(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    reference = tmp_path / "song.json"
    audio.write_bytes(b"audio")
    _reference(reference)
    identifier = "../../outside/song"
    manifest = _manifest(_track(identifier, "train", audio, reference))

    output = cache_dasheng_features(manifest, tmp_path / "cache", extractor=_FakeExtractor())
    path = Path(output["tracks"][0]["path"])
    assert path.parent == (tmp_path / "cache" / "train").resolve()
    assert ".." not in path.name
    assert path.is_file()


def test_feature_spec_hash_covers_weight_revision_grid_and_augmentation() -> None:
    provenance = dasheng_feature_provenance(load_dasheng_contract())
    spec = dasheng_cache_feature_spec(provenance)
    assert spec["modelId"] == "mispeech/dasheng-base"
    assert spec["weightSha256"] == provenance["fileSha256"]["model.safetensors"]
    assert spec["revision"] == provenance["revision"]
    assert spec["sampleRate"] == 16000
    assert spec["frameSeconds"] == 0.1
    assert spec["featureCount"] == 768
    assert spec["augmentationPolicy"] == "none"
    assert spec["storageDtype"] == "float16"
    assert len(spec["featureSpecSha256"]) == 64
