from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import steel_guitar_rag.chord_reader.benchmark as benchmark
from steel_guitar_rag.chord_reader.artifact_integrity import (
    FactorizedArtifactIntegrityError,
)
from steel_guitar_rag.chord_reader.bar_promotion import (
    benchmark_evaluation_hashes,
    benchmark_track_set_sha256,
    canonical_sha256,
    validate_benchmark_v2_provenance,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clean_source_tree() -> dict[str, Any]:
    return {
        "revision": "a" * 40,
        "dirty": False,
        "diffSha256": hashlib.sha256(b"\0STATUS\0").hexdigest(),
    }


class _FakeFactorizedRecognizer:
    feature_kind = "multiband_chroma_v2"
    feature_count = 61
    sample_rate = 11_025
    feature_spec_sha256 = _digest("feature-spec")
    vocabulary_labels = ("N", "C:maj")
    bass_threshold = 0.5
    decoder_contract = {"schemaVersion": "fixture_decoder_v1"}
    predicted_ids: list[str] = []
    events: list[str] = []

    def __init__(self, model: Path) -> None:
        self.model = model

    def predict_features(
        self,
        features: np.ndarray,
        duration: float,
        *,
        prediction_id: str,
        beat_grid: dict[str, Any] | None,
        reference_boundaries_seconds: tuple[float, ...],
    ) -> dict[str, Any]:
        assert features.shape == (4, 61)
        assert beat_grid is None
        assert reference_boundaries_seconds == ()
        self.predicted_ids.append(prediction_id)
        self.events.append(f"predict:{prediction_id}")
        return {
            "schemaVersion": "chord_prediction_v1",
            "id": prediction_id,
            "durationSeconds": duration,
            "segments": [
                {
                    "start": 0.0,
                    "end": duration,
                    "label": "C:maj",
                    "confidence": 0.99,
                }
            ],
        }


def _write_fixture_track(
    tmp_path: Path,
    *,
    identifier: str,
    dataset_id: str,
    split: str,
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    feature_path = tmp_path / f"{identifier}-features.npz"
    np.savez_compressed(
        feature_path,
        features=np.zeros((4, 61), dtype=np.float16),
    )
    reference_path = tmp_path / f"{identifier}-reference.json"
    reference_bytes = (
        b'{\n  "durationSeconds": 0.4,\n  "segments": '
        b'[{"start": 0.0, "end": 0.4, "label": "C:maj"}]\n}\n'
    )
    reference_path.write_bytes(reference_bytes)
    cached = {
        "id": identifier,
        "datasetId": dataset_id,
        "split": split,
        "sourceSplit": "train",
        "path": str(feature_path.resolve()),
        "factorizedLabelsPath": str((tmp_path / f"{identifier}-labels.npz").resolve()),
        "frames": 4,
        "durationSeconds": 0.4,
    }
    timing = {
        "id": identifier,
        "datasetId": dataset_id,
        "split": split,
        "referencePath": str(reference_path.resolve()),
        "durationSeconds": 0.4,
        "tempo": 120.0,
        "meter": "4/4",
        "beatTimesSeconds": [0.0, 0.2],
        "downbeatTimesSeconds": [0.0],
        "barStartsSeconds": [0.0],
        "gridStartSeconds": 0.0,
        "prefixExcludedSeconds": 0.0,
        "timingProvenance": {
            "barStartsSeconds": {"status": "explicit", "source": "fixture"}
        },
    }
    return cached, timing, reference_bytes


def _cache_manifest(
    tracks: list[dict[str, Any]],
    *,
    eligible_ids: set[str] | None = None,
) -> dict[str, Any]:
    eligible_ids = eligible_ids or set()
    eligible = [
        {
            "id": str(track["id"]),
            "datasetId": str(track["datasetId"]),
            "split": "calibration",
        }
        for track in tracks
        if track["split"] == "calibration" and str(track["id"]) in eligible_ids
    ]
    eligible.sort(key=lambda item: item["id"])
    return {
        "schemaVersion": "chord_factorized_label_cache_v2",
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "featureSpecSha256": _digest("feature-spec"),
        "artifactIntegrity": {"fixture": "validator is isolated by the tests"},
        "tracks": tracks,
        "splitProtocol": {
            "outputManifestSha256": _digest("split-output"),
            "assignmentSha256": _digest("split-assignment"),
            "calibration": {
                "setSha256": _digest("calibration-set"),
                "barEligibility": {
                    "status": "frozen",
                    "tracks": eligible,
                    "setSha256": benchmark_track_set_sha256(eligible)
                    if eligible
                    else _digest("empty-bar-eligible-set"),
                },
            },
        },
    }


def _patch_benchmark_runtime(
    monkeypatch: pytest.MonkeyPatch,
    *,
    artifact_events: list[list[str]] | None = None,
    split_calls: list[list[dict[str, Any]]] | None = None,
) -> None:
    _FakeFactorizedRecognizer.predicted_ids = []
    _FakeFactorizedRecognizer.events = []
    monkeypatch.setattr(benchmark, "FactorizedRecognizer", _FakeFactorizedRecognizer)
    monkeypatch.setattr(benchmark, "_source_tree_provenance", lambda unused: _clean_source_tree())

    def validate_split(
        unused_manifest: dict[str, Any],
        *,
        timing_manifests: list[dict[str, Any]],
    ) -> None:
        if split_calls is not None:
            split_calls.append(timing_manifests)

    def validate_artifacts(
        manifest: dict[str, Any],
        *,
        verify_files: bool,
    ) -> None:
        assert verify_files is True
        ids = [str(track["id"]) for track in manifest["tracks"]]
        if artifact_events is not None:
            artifact_events.append(ids)
        _FakeFactorizedRecognizer.events.append(f"artifacts:{','.join(ids)}")

    monkeypatch.setattr(benchmark, "validate_split_protocol_manifest", validate_split)
    monkeypatch.setattr(benchmark, "validate_factorized_artifact_manifest", validate_artifacts)


def test_factorized_cache_v2_uses_exact_frozen_calibration_bar_set_and_validates_before_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracks: list[dict[str, Any]] = []
    timing_tracks: list[dict[str, Any]] = []
    for identifier, dataset_id in (
        ("eligible-a", "aam"),
        ("excluded", "winterreise"),
        ("eligible-b", "guitarset"),
    ):
        cached, timing, unused_bytes = _write_fixture_track(
            tmp_path,
            identifier=identifier,
            dataset_id=dataset_id,
            split="calibration",
        )
        tracks.append(cached)
        timing_tracks.append(timing)
    timing_manifests = [{"schemaVersion": "fixture", "tracks": timing_tracks}]
    cache = _cache_manifest(tracks, eligible_ids={"eligible-a", "eligible-b"})
    model = tmp_path / "model.onnx"
    model.write_bytes(b"fixture-model")
    artifact_events: list[list[str]] = []
    split_calls: list[list[dict[str, Any]]] = []
    _patch_benchmark_runtime(
        monkeypatch,
        artifact_events=artifact_events,
        split_calls=split_calls,
    )

    report = benchmark.run_factorized_cache_benchmark(
        cache,
        timing_manifests,
        model=model,
        output_root=tmp_path / "output",
        split="calibration",
    )

    assert split_calls == [timing_manifests]
    assert [row["id"] for row in report["tracks"]] == ["eligible-a", "eligible-b"]
    assert _FakeFactorizedRecognizer.predicted_ids == ["eligible-a", "eligible-b"]
    assert artifact_events == [
        ["eligible-a", "eligible-b"],
        ["eligible-a", "eligible-b"],
    ]
    first_inference = next(
        index
        for index, event in enumerate(_FakeFactorizedRecognizer.events)
        if event.startswith("predict:")
    )
    assert _FakeFactorizedRecognizer.events.index("artifacts:eligible-a,eligible-b") < first_inference
    assert report["provenance"]["evaluation"]["trackSetSha256"] == cache["splitProtocol"][
        "calibration"
    ]["barEligibility"]["setSha256"]


def test_factorized_cache_v2_hashes_the_same_reference_bytes_it_parses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached, timing, reference_bytes = _write_fixture_track(
        tmp_path,
        identifier="reference-bytes",
        dataset_id="aam",
        split="development",
    )
    cache = _cache_manifest([cached])
    model = tmp_path / "model.onnx"
    model.write_bytes(b"fixture-model")
    _patch_benchmark_runtime(monkeypatch)
    reference_path = Path(timing["referencePath"])
    original_read_bytes = Path.read_bytes
    reads = 0

    def counted_read_bytes(path: Path) -> bytes:
        nonlocal reads
        if path == reference_path:
            reads += 1
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)

    report = benchmark.run_factorized_cache_benchmark(
        cache,
        [{"tracks": [timing]}],
        model=model,
        output_root=tmp_path / "output",
        split="development",
    )

    assert reads == 1
    assert report["tracks"][0]["referenceSha256"] == hashlib.sha256(reference_bytes).hexdigest()


def test_factorized_cache_v2_rejects_source_cache_dataset_mismatch_before_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached, timing, unused_bytes = _write_fixture_track(
        tmp_path,
        identifier="dataset-mismatch",
        dataset_id="aam",
        split="development",
    )
    timing["datasetId"] = "guitarset"
    cache = _cache_manifest([cached])
    model = tmp_path / "model.onnx"
    model.write_bytes(b"fixture-model")
    _patch_benchmark_runtime(monkeypatch)

    with pytest.raises(ValueError, match="Cache and timing metadata disagree"):
        benchmark.run_factorized_cache_benchmark(
            cache,
            [{"tracks": [timing]}],
            model=model,
            output_root=tmp_path / "output",
            split="development",
        )

    assert _FakeFactorizedRecognizer.predicted_ids == []


def test_every_semantic_timing_field_changes_the_timing_hash() -> None:
    timing = {
        "id": "timing-track",
        "referencePath": "/ignored/reference.json",
        "durationSeconds": 2.0,
        "tempo": 120.0,
        "meter": "4/4",
        "beatTimesSeconds": [0.0, 0.5, 1.0, 1.5],
        "downbeatTimesSeconds": [0.0],
        "barStartsSeconds": [0.0],
        "gridStartSeconds": 0.0,
        "prefixExcludedSeconds": 0.0,
        "timingProvenance": {"barStartsSeconds": {"status": "explicit"}},
    }
    expected_fields = {
        "id",
        "durationSeconds",
        "tempo",
        "meter",
        "beatTimesSeconds",
        "downbeatTimesSeconds",
        "barStartsSeconds",
        "gridStartSeconds",
        "prefixExcludedSeconds",
        "timingProvenance",
    }
    identity = benchmark._timing_identity(timing)
    baseline = canonical_sha256(identity)
    mutations = {
        "id": "timing-track-v2",
        "durationSeconds": 2.1,
        "tempo": 121.0,
        "meter": "3/4",
        "beatTimesSeconds": [0.0, 0.4, 0.8],
        "downbeatTimesSeconds": [0.1],
        "barStartsSeconds": [0.1],
        "gridStartSeconds": 0.1,
        "prefixExcludedSeconds": 0.1,
        "timingProvenance": {"barStartsSeconds": {"status": "explicit", "source": "v2"}},
    }

    assert set(identity) == expected_fields
    for field, value in mutations.items():
        changed = deepcopy(timing)
        changed[field] = value
        assert canonical_sha256(benchmark._timing_identity(changed)) != baseline, field
    changed_nonsemantic = {**timing, "referencePath": "/different/reference.json"}
    assert canonical_sha256(benchmark._timing_identity(changed_nonsemantic)) == baseline


def test_factorized_cache_v2_shared_evaluation_hashes_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached, timing, unused_bytes = _write_fixture_track(
        tmp_path,
        identifier="evaluation-hashes",
        dataset_id="guitarset",
        split="development",
    )
    cache = _cache_manifest([cached])
    model = tmp_path / "model.onnx"
    model.write_bytes(b"fixture-model")
    _patch_benchmark_runtime(monkeypatch)

    report = benchmark.run_factorized_cache_benchmark(
        cache,
        [{"tracks": [timing]}],
        model=model,
        output_root=tmp_path / "output",
        split="development",
    )

    evaluation = report["provenance"]["evaluation"]
    assert {name: evaluation[name] for name in benchmark_evaluation_hashes(report["tracks"])} == (
        benchmark_evaluation_hashes(report["tracks"])
    )
    assert validate_benchmark_v2_provenance(report)["evaluation"] == evaluation


@pytest.mark.parametrize(
    ("missing", "message"),
    (
        ("featureSpecSha256", "sealed featureSpecSha256"),
        ("splitProtocol", "sealed split protocol"),
        ("artifactIntegrity", "artifactIntegrity seal"),
    ),
)
def test_factorized_cache_v2_missing_integrity_contracts_fail_before_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
    message: str,
) -> None:
    cached, timing, unused_bytes = _write_fixture_track(
        tmp_path,
        identifier=f"missing-{missing}",
        dataset_id="aam",
        split="development",
    )
    cache = _cache_manifest([cached])
    cache.pop(missing)
    model = tmp_path / "model.onnx"
    model.write_bytes(b"fixture-model")
    _FakeFactorizedRecognizer.predicted_ids = []
    _FakeFactorizedRecognizer.events = []
    monkeypatch.setattr(benchmark, "FactorizedRecognizer", _FakeFactorizedRecognizer)
    monkeypatch.setattr(benchmark, "_source_tree_provenance", lambda unused: _clean_source_tree())
    monkeypatch.setattr(
        benchmark,
        "validate_split_protocol_manifest",
        lambda unused, *, timing_manifests: None,
    )
    if missing != "artifactIntegrity":
        monkeypatch.setattr(
            benchmark,
            "validate_factorized_artifact_manifest",
            lambda unused, *, verify_files: None,
        )

    expected_exception = FactorizedArtifactIntegrityError if missing == "artifactIntegrity" else ValueError
    with pytest.raises(expected_exception, match=message):
        benchmark.run_factorized_cache_benchmark(
            cache,
            [{"tracks": [timing]}],
            model=model,
            output_root=tmp_path / "output",
            split="development",
        )

    assert _FakeFactorizedRecognizer.predicted_ids == []


def _single_track_v2_report(report: dict[str, Any], index: int) -> dict[str, Any]:
    result = deepcopy(report)
    result["tracks"] = [deepcopy(report["tracks"][index])]
    result["provenance"]["evaluation"].update(benchmark_evaluation_hashes(result["tracks"]))
    return result


def test_merge_v2_validates_source_identity_and_preserves_certification_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracks: list[dict[str, Any]] = []
    timing_tracks: list[dict[str, Any]] = []
    for identifier, dataset_id in (("merge-a", "aam"), ("merge-b", "guitarset")):
        cached, timing, unused_bytes = _write_fixture_track(
            tmp_path,
            identifier=identifier,
            dataset_id=dataset_id,
            split="development",
        )
        tracks.append(cached)
        timing_tracks.append(timing)
    cache = _cache_manifest(tracks)
    model = tmp_path / "model.onnx"
    model.write_bytes(b"fixture-model")
    _patch_benchmark_runtime(monkeypatch)
    report = benchmark.run_factorized_cache_benchmark(
        cache,
        [{"tracks": timing_tracks}],
        model=model,
        output_root=tmp_path / "output",
        split="development",
    )
    first = _single_track_v2_report(report, 0)
    second = _single_track_v2_report(report, 1)

    dirty = deepcopy(second)
    dirty["provenance"]["sourceTree"]["dirty"] = True
    with pytest.raises(ValueError, match="clean source tree"):
        benchmark.merge_benchmark_reports([first, dirty])

    different_source = deepcopy(second)
    different_source["gitRevision"] = "b" * 40
    different_source["provenance"]["sourceTree"]["revision"] = "b" * 40
    with pytest.raises(ValueError, match="different source, model, cache, or decoder provenance"):
        benchmark.merge_benchmark_reports([first, different_source])

    merged = benchmark.merge_benchmark_reports([first, second])

    assert merged["promotionEligible"] is True
    assert merged["oracleTimingUsed"] is False
    assert merged["provenance"]["evaluation"] == {
        **benchmark_evaluation_hashes(merged["tracks"]),
        "decoderConfigSha256": report["provenance"]["evaluation"]["decoderConfigSha256"],
    }
    assert validate_benchmark_v2_provenance(merged)["evaluation"] == merged["provenance"][
        "evaluation"
    ]
