from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import steel_guitar_rag.chord_reader.benchmark as benchmark
import steel_guitar_rag.chord_reader.cli as chord_reader_cli
from steel_guitar_rag.chord_reader.bar_promotion import (
    benchmark_evaluation_hashes,
    canonical_sha256,
)
from steel_guitar_rag.chord_reader.uncertainty import _UNCERTAINTY_CONTRACT


FEATURE_SPEC_SHA256 = hashlib.sha256(b"uncertainty-feature-spec").hexdigest()
DECODER_CONTRACT_SHA256 = hashlib.sha256(b"uncertainty-decoder").hexdigest()
RUNTIME_CONTRACT_SHA256 = hashlib.sha256(b"uncertainty-runtime").hexdigest()


def _clean_source_tree() -> dict[str, Any]:
    return {
        "revision": "a" * 40,
        "dirty": False,
        "diffSha256": hashlib.sha256(b"\0STATUS\0").hexdigest(),
    }


def _fixture(
    tmp_path: Path,
    *,
    identifier: str = "uncertainty-development",
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    feature_path = tmp_path / f"{identifier}-features.npz"
    np.savez_compressed(
        feature_path,
        features=np.zeros((4, 61), dtype=np.float16),
    )
    reference_path = tmp_path / f"{identifier}-reference.json"
    reference_path.write_text(
        json.dumps(
            {
                "durationSeconds": 0.4,
                "segments": [{"start": 0.0, "end": 0.4, "label": "C:maj"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    track = {
        "id": identifier,
        "datasetId": "guitarset",
        "split": "development",
        "sourceSplit": "train",
        "path": str(feature_path.resolve()),
        "factorizedLabelsPath": str((tmp_path / f"{identifier}-labels.npz").resolve()),
        "frames": 4,
        "durationSeconds": 0.4,
    }
    cache = {
        "schemaVersion": "chord_factorized_label_cache_v2",
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "featureSpecSha256": FEATURE_SPEC_SHA256,
        "artifactIntegrity": {"fixture": True},
        "tracks": [track],
        "splitProtocol": {
            "outputManifestSha256": hashlib.sha256(b"output").hexdigest(),
            "assignmentSha256": hashlib.sha256(b"assignment").hexdigest(),
            "calibration": {
                "setSha256": hashlib.sha256(b"calibration").hexdigest(),
                "barEligibility": {
                    "status": "frozen",
                    "tracks": [],
                    "setSha256": hashlib.sha256(b"eligible").hexdigest(),
                },
            },
        },
    }
    timing = {
        "id": identifier,
        "datasetId": "guitarset",
        "split": "development",
        "referencePath": str(reference_path.resolve()),
        "durationSeconds": 0.4,
        "tempo": 120.0,
        "meter": "4/4",
        "barStartsSeconds": [0.0],
        "gridStartSeconds": 0.0,
        "prefixExcludedSeconds": 0.0,
        "timingProvenance": {"barStartsSeconds": {"status": "explicit", "source": "fixture"}},
    }
    model = tmp_path / "model.onnx"
    model.write_bytes(b"uncertainty-model")
    return cache, timing, model, reference_path


def _audio_lineage_fixture(cache: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for track in cache["tracks"]:
        with np.load(track["path"], allow_pickle=False) as archive:
            features = np.ascontiguousarray(archive["features"], dtype=np.dtype("<f2"))
        array_sha256 = hashlib.sha256(features.tobytes(order="C")).hexdigest()
        row_payload = {
            "trackId": track["id"],
            "datasetId": track["datasetId"],
            "sourceAudioSha256": hashlib.sha256(str(track["id"]).encode()).hexdigest(),
            "cachedArraySha256": array_sha256,
            "freshArraySha256": array_sha256,
            "canonicalDurationMilliseconds": 400,
        }
        rows.append({**row_payload, "rowSha256": canonical_sha256(row_payload)})
    return {
        "artifactSha256": hashlib.sha256(b"audio-lineage-artifact").hexdigest(),
        "extractorContract": {
            "entrypoint": "steel_guitar_rag.chord_reader.student.extract_student_features"
        },
        "featureContract": {
            "featureSpecSha256": cache["featureSpecSha256"],
            "contractSha256": hashlib.sha256(b"audio-lineage-feature-contract").hexdigest(),
        },
        "manifestBindings": {
            "winnerCacheManifest": {"canonicalSha256": canonical_sha256(cache)},
            "bindingsSha256": hashlib.sha256(b"audio-lineage-bindings").hexdigest(),
        },
        "tracks": rows,
    }


def _project_audio_lineage_fixture(
    artifact: dict[str, Any],
    track_ids: list[str],
) -> dict[str, Any]:
    selected = [row for row in artifact["tracks"] if row["trackId"] in set(track_ids)]
    payload = {
        "schemaVersion": benchmark.AUDIO_LINEAGE_PROJECTION_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "sourceAudioLineageSha256": artifact["artifactSha256"],
        "manifestBindingsSha256": artifact["manifestBindings"]["bindingsSha256"],
        "featureContractSha256": artifact["featureContract"]["contractSha256"],
        "trackCount": len(selected),
        "tracks": selected,
        "trackSetSha256": canonical_sha256(selected),
    }
    return {**payload, "projectionSha256": canonical_sha256(payload)}


def _prediction_core(identifier: str, duration: float) -> dict[str, Any]:
    return {
        "schemaVersion": "chord_prediction_v1",
        "id": identifier,
        "durationSeconds": duration,
        "frameSeconds": 0.1,
        "decoderContractSha256": DECODER_CONTRACT_SHA256,
        "segments": [
            {
                "start": 0.0,
                "end": duration,
                "label": "C:maj",
                "productLabel": "C",
                "confidence": 0.99,
                "productConfidence": 0.99,
            }
        ],
    }


def _emitted_prediction(
    identifier: str,
    duration: float,
    *,
    model_sha256: str,
) -> dict[str, Any]:
    prediction = _prediction_core(identifier, duration)
    members = [
        {
            "ordinal": 0,
            "fileName": "model.onnx",
            "modelSha256": model_sha256,
            "bytes": len(b"uncertainty-model"),
            "runtimeContractSha256": RUNTIME_CONTRACT_SHA256,
            "headType": "joint-139",
            "commonWeight": 1.0,
            "jointContributorWeight": 1.0,
        }
    ]
    binding = {
        "schemaVersion": "chord_factorized_uncertainty_binding_v1",
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "featureSpecSha256": FEATURE_SPEC_SHA256,
        "sampleRate": 11_025,
        "modelOrEnsembleSha256": model_sha256,
        "decoderContractSha256": DECODER_CONTRACT_SHA256,
        "jointProductBlend": 0.0,
        "memberOrderSha256": canonical_sha256(members),
        "commonWeights": [1.0],
        "jointContributorIndices": [0],
        "jointContributorWeights": [1.0],
    }
    uncertainty = {
        "schemaVersion": benchmark.FACTORIZED_UNCERTAINTY_SCHEMA,
        "contractSha256": canonical_sha256(
            {
                "formulaContract": _UNCERTAINTY_CONTRACT,
                "binding": binding,
                "members": members,
            }
        ),
        "referenceFree": True,
        "binding": binding,
        "timebase": {
            "frameSeconds": 0.1,
            "frameCount": 4,
            "durationSeconds": duration,
            "timestampConvention": "left-edge",
        },
        "members": members,
        "frames": {
            "root": {
                "selectedClass": [1] * 4,
                "selectedProbability": [0.99] * 4,
                "topProbability": [0.99] * 4,
                "margin": [0.98] * 4,
                "normalizedEntropy": [0.01] * 4,
            },
            "product": {
                "applicable": [True] * 4,
                "selectedClass": [1] * 4,
                "directJointAgreement": [True] * 4,
                "directJointJensenShannon": [0.0] * 4,
                "selectedProbability": [0.99] * 4,
                "topProbability": [0.99] * 4,
                "margin": [0.98] * 4,
                "normalizedEntropy": [0.01] * 4,
            },
            "ensemble": {
                "memberRootVote": [[1] * 4],
                "memberProductVote": [[1] * 4],
                "rootSelectedVoteShare": [1.0] * 4,
                "productSelectedVoteShare": [1.0] * 4,
                "rootPairwiseDisagreement": [0.0] * 4,
                "productPairwiseDisagreement": [0.0] * 4,
                "rootSelectedProbabilityStdDev": [0.0] * 4,
                "productSelectedProbabilityStdDev": [0.0] * 4,
                "rootMutualInformation": [0.0] * 4,
                "productMutualInformation": [0.0] * 4,
            },
            "boundary": {
                "modelProbability": [0.0] * 4,
                "memberMeanProbability": [0.0] * 4,
                "memberStdDev": [0.0] * 4,
            },
            "observability": {
                "profileSchemaVersion": ("chord_existing_feature_matrix_observability_v1"),
                "source": "existing-feature-matrix",
                "values": {
                    "representationRms": [0.0] * 4,
                    "temporalDeltaRms": [0.0] * 4,
                    "absoluteActivationConcentration": [0.0] * 4,
                    "cosineChange": [0.0] * 4,
                },
            },
        },
    }
    # The core digest excludes all three uncertainty transport fields.
    prediction_core_sha256 = canonical_sha256(
        {
            key: value
            for key, value in prediction.items()
            if key not in {"uncertainty", "uncertaintySha256", "predictionCoreSha256"}
        }
    )
    uncertainty["predictionCoreSha256"] = prediction_core_sha256
    prediction["uncertainty"] = uncertainty
    prediction["predictionCoreSha256"] = prediction_core_sha256
    prediction["uncertaintySha256"] = canonical_sha256(uncertainty)
    return prediction


class _UncertaintyRecognizer:
    feature_kind = "multiband_chroma_v2"
    feature_count = 61
    sample_rate = 11_025
    feature_spec_sha256 = FEATURE_SPEC_SHA256
    vocabulary_labels = ("N", "C:maj")
    bass_threshold = 0.5
    decoder_contract = {"schemaVersion": "fixture_decoder_v1"}
    decoder_contract_sha256 = DECODER_CONTRACT_SHA256
    events: list[str] = []

    def __init__(self, model: Path) -> None:
        self.model_sha256 = benchmark._file_sha256(model)
        self.member_head_types = ("joint-139",)
        self.uncertainty_common_weights = (1.0,)
        self.uncertainty_member_identities = (
            {
                "fileName": model.name,
                "modelSha256": self.model_sha256,
                "bytes": model.stat().st_size,
                "runtimeContractSha256": RUNTIME_CONTRACT_SHA256,
            },
        )

    def predict_features(
        self,
        features: np.ndarray,
        duration: float,
        *,
        prediction_id: str,
        beat_grid: None,
        reference_boundaries_seconds: tuple[float, ...],
        emit_uncertainty: bool,
    ) -> dict[str, Any]:
        assert features.shape == (4, 61)
        assert beat_grid is None
        assert reference_boundaries_seconds == ()
        assert emit_uncertainty is True
        self.events.append(f"predict:{prediction_id}")
        return _emitted_prediction(
            prediction_id,
            duration,
            model_sha256=self.model_sha256,
        )


def _patch_runtime(
    monkeypatch: pytest.MonkeyPatch,
    recognizer: type[_UncertaintyRecognizer] = _UncertaintyRecognizer,
) -> None:
    recognizer.events = []
    monkeypatch.setattr(benchmark, "FactorizedRecognizer", recognizer)
    monkeypatch.setattr(benchmark, "_source_tree_provenance", lambda unused: _clean_source_tree())
    monkeypatch.setattr(
        benchmark,
        "validate_split_protocol_manifest",
        lambda unused, *, timing_manifests: None,
    )
    monkeypatch.setattr(
        benchmark,
        "validate_factorized_artifact_manifest",
        lambda unused, *, verify_files: None,
    )
    monkeypatch.setattr(
        benchmark,
        "validate_development_audio_lineage",
        lambda unused, *, verify_files: None,
    )
    monkeypatch.setattr(
        benchmark,
        "project_development_audio_lineage",
        _project_audio_lineage_fixture,
    )


@pytest.mark.parametrize(
    ("split", "beat_grid_source", "message"),
    (
        ("calibration", "none", "development-only"),
        ("test", "none", "development-only"),
        ("all", "none", "development-only"),
        ("development", "manifest-tempo-oracle", "beat_grid_source='none'"),
    ),
)
def test_emit_uncertainty_rejects_before_any_artifact_or_model_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    split: str,
    beat_grid_source: str,
    message: str,
) -> None:
    entered: list[str] = []

    def fail_access(*_args: object, **_kwargs: object) -> None:
        entered.append("artifact")
        raise AssertionError("artifact access must not occur")

    class FailRecognizer:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            entered.append("model")
            raise AssertionError("model access must not occur")

    monkeypatch.setattr(benchmark, "validate_split_protocol_manifest", fail_access)
    monkeypatch.setattr(benchmark, "validate_factorized_artifact_manifest", fail_access)
    monkeypatch.setattr(benchmark, "FactorizedRecognizer", FailRecognizer)

    with pytest.raises(ValueError, match=message):
        benchmark.run_factorized_cache_benchmark(
            {},
            [],
            model=tmp_path / "unavailable.onnx",
            output_root=tmp_path / "output",
            split=split,
            beat_grid_source=beat_grid_source,
            emit_uncertainty=True,
        )

    assert entered == []


@pytest.mark.parametrize(
    ("split", "beat_grid_source", "message"),
    (
        ("test", "none", "development-only"),
        ("development", "manifest-tempo-oracle", "beat_grid_source='none'"),
    ),
)
def test_emit_uncertainty_cli_rejects_before_reading_cache_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    split: str,
    beat_grid_source: str,
    message: str,
) -> None:
    entered: list[str] = []

    def fail_read(*_args: object, **_kwargs: object) -> None:
        entered.append("manifest")
        raise AssertionError("manifest access must not occur")

    monkeypatch.setattr(chord_reader_cli, "_read_json", fail_read)
    with pytest.raises(ValueError, match=message):
        chord_reader_cli.main(
            [
                "benchmark-factorized-cache",
                str(tmp_path / "cache.json"),
                "--track-manifest",
                str(tmp_path / "tracks.json"),
                "--model",
                str(tmp_path / "model.onnx"),
                "--output-root",
                str(tmp_path / "output"),
                "--report",
                str(tmp_path / "report.json"),
                "--split",
                split,
                "--beat-grid-source",
                beat_grid_source,
                "--emit-uncertainty",
            ]
        )

    assert entered == []


def test_emit_uncertainty_is_atomic_and_reference_free_until_prediction_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache, timing, model, reference_path = _fixture(tmp_path)
    _patch_runtime(monkeypatch)
    output_root = tmp_path / "output"
    prediction_path = output_root / "predictions" / "factorized" / f"{timing['id']}.json"
    original_read_bytes = Path.read_bytes
    events: list[str] = []

    def protected_reference_read(path: Path) -> bytes:
        if path == reference_path:
            assert _UncertaintyRecognizer.events == [f"predict:{timing['id']}"]
            assert prediction_path.is_file()
            materialized = json.loads(original_read_bytes(prediction_path))
            assert materialized["uncertainty"]["referenceFree"] is True
            assert materialized["uncertaintySha256"] == canonical_sha256(materialized["uncertainty"])
            events.append("reference")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", protected_reference_read)
    report = benchmark.run_factorized_cache_benchmark(
        cache,
        [{"tracks": [timing]}],
        model=model,
        output_root=output_root,
        split="development",
        emit_uncertainty=True,
        audio_lineage=_audio_lineage_fixture(cache),
        verify_audio_lineage_files=False,
    )

    assert events == ["reference"]
    assert not list(prediction_path.parent.glob(f".{prediction_path.name}.*.tmp"))
    prediction = json.loads(original_read_bytes(prediction_path))
    track = report["tracks"][0]
    assert track["predictionCoreSha256"] == prediction["predictionCoreSha256"]
    assert track["uncertaintySha256"] == prediction["uncertaintySha256"]
    assert track["predictionSha256"] == hashlib.sha256(original_read_bytes(prediction_path)).hexdigest()
    assert track["predictionSha256"] not in {
        track["predictionCoreSha256"],
        track["uncertaintySha256"],
    }
    assert report["provenance"]["evaluation"] == {
        **benchmark_evaluation_hashes(report["tracks"]),
        "decoderConfigSha256": report["provenance"]["evaluation"]["decoderConfigSha256"],
    }
    assert report["promotionEligible"] is False
    assert report["developmentOnlyExperiment"] is True
    experiment = report["uncertaintyExperiment"]
    assert experiment["schemaVersion"] == (benchmark.UNCERTAINTY_DEVELOPMENT_EXPERIMENT_SCHEMA)
    assert experiment["uncertaintySchemaVersion"] == (benchmark.FACTORIZED_UNCERTAINTY_SCHEMA)
    assert experiment["contractSha256"] == canonical_sha256(
        {
            "formulaContract": _UNCERTAINTY_CONTRACT,
            "binding": experiment["binding"],
            "members": experiment["memberBinding"],
        }
    )
    assert experiment["referenceFree"] is True
    assert experiment["featureBinding"] == {
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "featureSpecSha256": FEATURE_SPEC_SHA256,
    }
    assert experiment["featureBindingSha256"] == canonical_sha256(experiment["featureBinding"])
    assert experiment["memberBindingSha256"] == canonical_sha256(experiment["memberBinding"])
    assert experiment["bindingSha256"] == canonical_sha256(experiment["binding"])
    assert experiment["trackCount"] == 1
    lineage_binding = experiment["audioLineage"]
    assert lineage_binding["schemaVersion"] == benchmark.AUDIO_LINEAGE_BENCHMARK_BINDING_SCHEMA
    assert lineage_binding["verificationMode"] == "metadata-only-test-fixture-v1"
    assert lineage_binding["projectionSha256"] == lineage_binding["projection"]["projectionSha256"]
    assert lineage_binding["bindingSha256"] == canonical_sha256(
        {key: value for key, value in lineage_binding.items() if key != "bindingSha256"}
    )
    assert track["sourceAudioSha256"] == lineage_binding["projection"]["tracks"][0]["sourceAudioSha256"]
    assert track["cachedFeatureArraySha256"] == track["freshFeatureArraySha256"]
    assert track["canonicalDurationMilliseconds"] == 400
    assert track["audioLineageRowSha256"] == lineage_binding["projection"]["tracks"][0]["rowSha256"]


@pytest.mark.parametrize(
    ("tamper", "message"),
    (
        ("cache-manifest", "exact benchmark cache manifest"),
        ("array", "feature array differs"),
        ("duration", "duration differs"),
    ),
)
def test_emit_uncertainty_rejects_audio_lineage_splice_before_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
    message: str,
) -> None:
    cache, timing, model, reference_path = _fixture(tmp_path)
    lineage = _audio_lineage_fixture(cache)
    if tamper == "cache-manifest":
        lineage["manifestBindings"]["winnerCacheManifest"]["canonicalSha256"] = "0" * 64
    elif tamper == "array":
        lineage["tracks"][0]["cachedArraySha256"] = "0" * 64
        lineage["tracks"][0]["freshArraySha256"] = "0" * 64
    elif tamper == "duration":
        lineage["tracks"][0]["canonicalDurationMilliseconds"] = 401
    else:  # pragma: no cover - parameter table is frozen above
        raise AssertionError(tamper)

    _patch_runtime(monkeypatch)
    original_read_bytes = Path.read_bytes

    def protected_reference_read(path: Path) -> bytes:
        if path == reference_path:
            raise AssertionError("reference must remain unopened after audio-lineage rejection")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", protected_reference_read)
    with pytest.raises(ValueError, match=message):
        benchmark.run_factorized_cache_benchmark(
            cache,
            [{"tracks": [timing]}],
            model=model,
            output_root=tmp_path / "output",
            split="development",
            emit_uncertainty=True,
            audio_lineage=lineage,
            verify_audio_lineage_files=False,
        )


def test_emit_uncertainty_rejects_tampered_payload_before_reference_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache, timing, model, reference_path = _fixture(tmp_path)

    class TamperedRecognizer(_UncertaintyRecognizer):
        def predict_features(self, *args: object, **kwargs: object) -> dict[str, Any]:
            prediction = super().predict_features(*args, **kwargs)
            prediction["uncertaintySha256"] = "0" * 64
            return prediction

    _patch_runtime(monkeypatch, TamperedRecognizer)
    original_read_bytes = Path.read_bytes

    def protected_reference_read(path: Path) -> bytes:
        if path == reference_path:
            raise AssertionError("reference must remain unopened after uncertainty rejection")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", protected_reference_read)
    with pytest.raises(ValueError, match="does not match uncertainty"):
        benchmark.run_factorized_cache_benchmark(
            cache,
            [{"tracks": [timing]}],
            model=model,
            output_root=tmp_path / "output",
            split="development",
            emit_uncertainty=True,
            audio_lineage=_audio_lineage_fixture(cache),
            verify_audio_lineage_files=False,
        )


@pytest.mark.parametrize(
    ("tamper", "message"),
    (
        ("member-order", "member-order hash is invalid"),
        ("rehashed-member-identity", "do not match recognizer identities and weights"),
        ("moving-recognizer-identity", "do not match recognizer identities and weights"),
        ("prediction-core-splice", "does not match prediction core"),
        ("frame-count", "frameCount must equal"),
        ("frame-seconds", r"frameSeconds must be exactly 0[.]1"),
        ("duration", "frameCount must equal"),
        ("extra-frame-group", "must contain exactly the required fields"),
        ("missing-frame-group", "must contain exactly the required fields"),
    ),
)
def test_emit_uncertainty_rejects_binding_timebase_or_frame_group_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
    message: str,
) -> None:
    cache, timing, model, reference_path = _fixture(tmp_path)

    class TamperedRecognizer(_UncertaintyRecognizer):
        def predict_features(self, *args: object, **kwargs: object) -> dict[str, Any]:
            prediction = super().predict_features(*args, **kwargs)
            uncertainty = prediction["uncertainty"]
            if tamper == "member-order":
                uncertainty["binding"]["memberOrderSha256"] = hashlib.sha256(
                    b"different-valid-member-order"
                ).hexdigest()
            elif tamper in {
                "rehashed-member-identity",
                "moving-recognizer-identity",
            }:
                member = uncertainty["members"][0]
                forged_identity = {
                    "fileName": "forged.onnx",
                    "modelSha256": member["modelSha256"],
                    "bytes": member["bytes"] + 1,
                    "runtimeContractSha256": hashlib.sha256(b"forged-runtime-contract").hexdigest(),
                    "architecture": "tcn",
                    "windowFrames": 32,
                }
                member.update(forged_identity)
                if tamper == "moving-recognizer-identity":
                    self.uncertainty_member_identities = (forged_identity,)
                uncertainty["binding"]["memberOrderSha256"] = canonical_sha256(uncertainty["members"])
                uncertainty["contractSha256"] = canonical_sha256(
                    {
                        "formulaContract": _UNCERTAINTY_CONTRACT,
                        "binding": uncertainty["binding"],
                        "members": uncertainty["members"],
                    }
                )
            elif tamper == "prediction-core-splice":
                uncertainty["predictionCoreSha256"] = hashlib.sha256(b"different-valid-prediction-core").hexdigest()
            elif tamper == "frame-count":
                uncertainty["timebase"]["frameCount"] += 1
            elif tamper == "frame-seconds":
                uncertainty["timebase"]["frameSeconds"] = 0.2
            elif tamper == "duration":
                uncertainty["timebase"]["durationSeconds"] = 0.5
            elif tamper == "extra-frame-group":
                uncertainty["frames"]["unexpected"] = {}
            elif tamper == "missing-frame-group":
                del uncertainty["frames"]["boundary"]
            else:  # pragma: no cover - guarded by the parameter table
                raise AssertionError(f"Unknown tamper case {tamper!r}.")
            prediction["uncertaintySha256"] = canonical_sha256(uncertainty)
            return prediction

    _patch_runtime(monkeypatch, TamperedRecognizer)
    original_read_bytes = Path.read_bytes

    def protected_reference_read(path: Path) -> bytes:
        if path == reference_path:
            raise AssertionError("reference must remain unopened after uncertainty rejection")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", protected_reference_read)
    prediction_path = tmp_path / "output" / "predictions" / "factorized" / f"{timing['id']}.json"
    with pytest.raises(ValueError, match=message):
        benchmark.run_factorized_cache_benchmark(
            cache,
            [{"tracks": [timing]}],
            model=model,
            output_root=tmp_path / "output",
            split="development",
            emit_uncertainty=True,
            audio_lineage=_audio_lineage_fixture(cache),
            verify_audio_lineage_files=False,
        )

    assert not prediction_path.exists()


def test_emit_uncertainty_rejects_cross_track_binding_or_contract_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_cache, first_timing, model, unused_first_reference = _fixture(
        tmp_path,
        identifier="uncertainty-first",
    )
    second_cache, second_timing, unused_model, unused_second_reference = _fixture(
        tmp_path,
        identifier="uncertainty-second",
    )
    first_cache["tracks"].extend(second_cache["tracks"])

    class DriftingRecognizer(_UncertaintyRecognizer):
        def predict_features(self, *args: object, **kwargs: object) -> dict[str, Any]:
            prediction = super().predict_features(*args, **kwargs)
            if prediction["id"] == "uncertainty-second":
                uncertainty = prediction["uncertainty"]
                uncertainty["members"][0]["fileName"] = "drifted-model.onnx"
                uncertainty["binding"]["memberOrderSha256"] = canonical_sha256(uncertainty["members"])
                uncertainty["contractSha256"] = canonical_sha256(
                    {
                        "formulaContract": _UNCERTAINTY_CONTRACT,
                        "binding": uncertainty["binding"],
                        "members": uncertainty["members"],
                    }
                )
                prediction["uncertaintySha256"] = canonical_sha256(uncertainty)
            return prediction

    _patch_runtime(monkeypatch, DriftingRecognizer)
    with pytest.raises(ValueError, match="do not match recognizer identities and weights"):
        benchmark.run_factorized_cache_benchmark(
            first_cache,
            [{"tracks": [first_timing, second_timing]}],
            model=model,
            output_root=tmp_path / "output",
            split="development",
            emit_uncertainty=True,
            audio_lineage=_audio_lineage_fixture(first_cache),
            verify_audio_lineage_files=False,
        )


def test_default_cache_benchmark_keeps_legacy_prediction_shape_and_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache, timing, model, unused_reference_path = _fixture(tmp_path)

    class LegacyRecognizer(_UncertaintyRecognizer):
        def predict_features(
            self,
            features: np.ndarray,
            duration: float,
            *,
            prediction_id: str,
            beat_grid: None,
            reference_boundaries_seconds: tuple[float, ...],
        ) -> dict[str, Any]:
            assert features.shape == (4, 61)
            assert beat_grid is None
            assert reference_boundaries_seconds == ()
            return _prediction_core(prediction_id, duration)

    _patch_runtime(monkeypatch, LegacyRecognizer)
    output_root = tmp_path / "output"
    report = benchmark.run_factorized_cache_benchmark(
        cache,
        [{"tracks": [timing]}],
        model=model,
        output_root=output_root,
        split="development",
    )
    prediction_path = output_root / "predictions" / "factorized" / f"{timing['id']}.json"
    expected = (
        json.dumps(
            _prediction_core(str(timing["id"]), 0.4),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    assert prediction_path.read_text(encoding="utf-8") == expected
    assert report["promotionEligible"] is True
    assert "developmentOnlyExperiment" not in report
    assert "uncertaintyExperiment" not in report
    assert "predictionCoreSha256" not in report["tracks"][0]
    assert "uncertaintySha256" not in report["tracks"][0]


def test_cli_dispatches_emit_uncertainty_only_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_path = tmp_path / "cache.json"
    tracks_path = tmp_path / "tracks.json"
    lineage_path = tmp_path / "lineage.json"
    cache_path.write_text('{"tracks": []}\n', encoding="utf-8")
    tracks_path.write_text('{"tracks": []}\n', encoding="utf-8")
    lineage_path.write_text('{"fixture": true}\n', encoding="utf-8")
    calls: list[dict[str, Any]] = []

    def capture(*_args: object, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"emitUncertainty": kwargs.get("emit_uncertainty", False)}

    monkeypatch.setattr(chord_reader_cli, "run_factorized_cache_benchmark", capture)
    common = [
        "benchmark-factorized-cache",
        str(cache_path),
        "--track-manifest",
        str(tracks_path),
        "--model",
        str(tmp_path / "model.onnx"),
        "--output-root",
        str(tmp_path / "output"),
        "--report",
        str(tmp_path / "report.json"),
    ]

    assert chord_reader_cli.main(common) == 0
    assert "emit_uncertainty" not in calls[-1]
    with pytest.raises(ValueError, match="audio-lineage-manifest"):
        chord_reader_cli.main([*common, "--emit-uncertainty"])
    assert (
        chord_reader_cli.main(
            [
                *common,
                "--emit-uncertainty",
                "--audio-lineage-manifest",
                str(lineage_path),
            ]
        )
        == 0
    )
    assert calls[-1]["emit_uncertainty"] is True
    assert calls[-1]["audio_lineage"] == {"fixture": True}
