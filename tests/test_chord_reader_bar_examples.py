from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

import steel_guitar_rag.chord_reader.bar_examples as bar_examples
from steel_guitar_rag.chord_reader.bar_examples import (
    AUDIO_GROUP_AUDIT_SCHEMA,
    AUDIO_LINEAGE_VERIFICATION_MODE,
    BAR_OUTCOME_ELIGIBILITY_CONTRACT,
    BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    COMPACT_BAR_SUMMARY_SCHEMA,
    EXAMPLES_SCHEMA,
    FEATURE_ARRAY_VERIFICATION,
    GROUP_MANIFEST_SCHEMA,
    build_bar_selector_group_manifest,
    build_bar_selector_examples,
    summary_artifact_filename,
)
from steel_guitar_rag.chord_reader.audio_lineage import (
    AUDIO_LINEAGE_SCHEMA,
    project_development_audio_lineage,
)
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.bar_selector import (
    BAR_OUTCOME_ELIGIBILITY_CONTRACT as SELECTOR_OUTCOME_ELIGIBILITY_CONTRACT,
    BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256 as SELECTOR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256,
    _validated_example,
    _validated_shared_bindings,
)
from steel_guitar_rag.chord_reader.bar_uncertainty import (
    BAR_FEATURE_CONTRACT_SHA256,
    BAR_FEATURE_NAMES,
    BAR_UNCERTAINTY_SCHEMA,
    EXPLICIT_BAR_GRID_SCHEMA,
)
from steel_guitar_rag.chord_reader.benchmark import (
    BENCHMARK_REPORT_SCHEMA,
    UNCERTAINTY_DEVELOPMENT_EXPERIMENT_SCHEMA,
)
from steel_guitar_rag.chord_reader.runtime_bar_grid import (
    OUTPUT_MANIFEST_SCHEMA,
    SOURCE_ID,
    analyzer_contract,
)
from steel_guitar_rag.chord_reader.uncertainty import FACTORIZED_UNCERTAINTY_SCHEMA


MODEL_SHA256 = hashlib.sha256(b"bar-example-model").hexdigest()
DECODER_SHA256 = hashlib.sha256(b"bar-example-decoder").hexdigest()
UNCERTAINTY_CONTRACT_SHA256 = hashlib.sha256(b"bar-example-uncertainty-contract").hexdigest()
FEATURE_SPEC_SHA256 = hashlib.sha256(b"bar-example-feature-spec").hexdigest()
SOURCE_MANIFEST_SHA256 = hashlib.sha256(b"bar-example-audio-manifest").hexdigest()
RUNTIME_ANALYZER_CONTRACT = analyzer_contract()
TIMING_SOURCE_CONTRACT_SHA256 = RUNTIME_ANALYZER_CONTRACT["contractSha256"]


def _sealed_file_binding(role: str, schema_version: str, path: Path) -> dict[str, Any]:
    payload = {
        "role": role,
        "schemaVersion": schema_version,
        "path": str(path.resolve()),
        "pathSha256": canonical_sha256(str(path.resolve())),
        "fileSha256": hashlib.sha256(f"file:{role}".encode()).hexdigest(),
        "bytes": 123,
        "canonicalSha256": hashlib.sha256(f"canonical:{role}".encode()).hexdigest(),
    }
    return payload


def _audio_lineage(
    tmp_path: Path,
    report_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    feature_payload = {
        "schemaVersion": "chord_development_audio_feature_contract_v1",
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "storageDtype": "<f2",
        "featureSpecSha256": FEATURE_SPEC_SHA256,
    }
    feature_contract = {
        **feature_payload,
        "contractSha256": canonical_sha256(feature_payload),
    }
    dependencies = {
        "python": "fixture",
        "librosa": "fixture",
        "numpy": "fixture",
        "scipy": "fixture",
        "soundfile": "fixture",
    }
    source_file = (tmp_path / "fixture-student.py").resolve()
    lock_file = (tmp_path / "fixture-lock.txt").resolve()
    extractor_payload = {
        "schemaVersion": "chord_development_audio_extractor_contract_v1",
        "entrypoint": bar_examples.PRODUCTION_EXTRACTOR_ENTRYPOINT,
        "sourceFile": str(source_file),
        "sourceFilePathSha256": canonical_sha256(str(source_file)),
        "sourceFileSha256": hashlib.sha256(b"fixture-student-source").hexdigest(),
        "sourceFileBytes": 123,
        "functionSourceSha256": hashlib.sha256(b"fixture-extractor-function").hexdigest(),
        "dependencyLockFile": str(lock_file),
        "dependencyLockPathSha256": canonical_sha256(str(lock_file)),
        "dependencyLockSha256": hashlib.sha256(b"fixture-lock").hexdigest(),
        "dependencyLockBytes": 123,
        "dependencies": dependencies,
        "dependenciesSha256": canonical_sha256(dependencies),
        "featureContractSha256": feature_contract["contractSha256"],
    }
    extractor_contract = {
        **extractor_payload,
        "contractSha256": canonical_sha256(extractor_payload),
    }
    manifest_payload = {
        "schemaVersion": "chord_development_audio_manifest_bindings_v1",
        "winnerCacheManifest": _sealed_file_binding(
            "winnerCacheManifest",
            "chord_factorized_cache_manifest_v1",
            tmp_path / "winner.json",
        ),
        "developmentSourceManifest": _sealed_file_binding(
            "developmentSourceManifest",
            "chord_dataset_manifest_v1",
            tmp_path / "development.json",
        ),
        "dashengCacheManifest": _sealed_file_binding(
            "dashengCacheManifest",
            "chord_feature_cache_v1",
            tmp_path / "dasheng.json",
        ),
        "winnerCacheOutputManifestSha256": hashlib.sha256(b"winner-output").hexdigest(),
        "winnerCacheSourceManifestSha256": hashlib.sha256(b"winner-source").hexdigest(),
        "winnerCacheArtifactSetSha256": hashlib.sha256(b"winner-artifacts").hexdigest(),
        "winnerCacheAudioBindingStatus": "absent_repaired_by_fresh_array_equality_v1",
        "dashengFeatureSpecSha256": hashlib.sha256(b"dasheng-feature-spec").hexdigest(),
    }
    manifest_bindings = {
        **manifest_payload,
        "bindingsSha256": canonical_sha256(manifest_payload),
    }
    runtime_by_id = {row["trackId"]: row for row in runtime_rows}
    tracks: list[dict[str, Any]] = []
    for report in sorted(report_rows, key=lambda value: value["id"]):
        track_id = report["id"]
        runtime = runtime_by_id[track_id]
        duration = float(runtime["durationSeconds"])
        frames = max(1, math.ceil(duration / 0.1 - 1e-12))
        array_sha256 = hashlib.sha256(f"array:{track_id}".encode()).hexdigest()
        winner_sha256 = hashlib.sha256(f"winner:{track_id}".encode()).hexdigest()
        artifact_sha256 = hashlib.sha256(f"artifact:{track_id}".encode()).hexdigest()
        source_sha256 = hashlib.sha256(f"source:{track_id}".encode()).hexdigest()
        dasheng_sha256 = hashlib.sha256(f"dasheng:{track_id}".encode()).hexdigest()
        source_metadata_sha256 = canonical_sha256(
            {
                "winnerTrackSha256": winner_sha256,
                "winnerArtifactEntrySha256": artifact_sha256,
                "sourceDescriptorSha256": source_sha256,
                "dashengTrackSha256": dasheng_sha256,
            }
        )
        audio_path = (tmp_path / f"{track_id}.wav").resolve()
        cache_path = (tmp_path / f"{track_id}.npz").resolve()
        row_payload = {
            "trackId": track_id,
            "datasetId": report["datasetId"],
            "split": "development",
            "audioPath": str(audio_path),
            "audioPathSha256": canonical_sha256(str(audio_path)),
            "sourceAudioSha256": runtime["audioSha256"],
            "sourceAudioBytes": 123,
            "cachedFeaturePath": str(cache_path),
            "cachedFeaturePathSha256": canonical_sha256(str(cache_path)),
            "cachedFeatureArtifactSha256": hashlib.sha256(f"cache:{track_id}".encode()).hexdigest(),
            "cachedFeatureArtifactBytes": 123,
            "cachedArraySha256": array_sha256,
            "freshArraySha256": array_sha256,
            "frames": frames,
            "featureCount": 61,
            "elementCount": frames * 61,
            "cachedDurationSeconds": duration,
            "freshDurationSeconds": duration,
            "canonicalDurationMilliseconds": runtime["audioBinding"]["canonicalDurationMilliseconds"],
            "winnerTrackSha256": winner_sha256,
            "winnerArtifactEntrySha256": artifact_sha256,
            "sourceDescriptorSha256": source_sha256,
            "dashengTrackSha256": dasheng_sha256,
            "sourceMetadataSha256": source_metadata_sha256,
        }
        row = {**row_payload, "rowSha256": canonical_sha256(row_payload)}
        tracks.append(row)
        report.update(
            {
                "sourceAudioSha256": row["sourceAudioSha256"],
                "cachedFeatureArraySha256": row["cachedArraySha256"],
                "freshFeatureArraySha256": row["freshArraySha256"],
                "canonicalDurationMilliseconds": row["canonicalDurationMilliseconds"],
                "audioLineageRowSha256": row["rowSha256"],
            }
        )
    payload = {
        "schemaVersion": AUDIO_LINEAGE_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "featureContract": feature_contract,
        "extractorContract": extractor_contract,
        "manifestBindings": manifest_bindings,
        "trackCount": len(tracks),
        "tracks": tracks,
        "trackSetSha256": canonical_sha256(
            [{"trackId": row["trackId"], "rowSha256": row["rowSha256"]} for row in tracks]
        ),
        "audioSetSha256": canonical_sha256(
            [
                {
                    "trackId": row["trackId"],
                    "audioPathSha256": row["audioPathSha256"],
                    "sourceAudioSha256": row["sourceAudioSha256"],
                    "sourceAudioBytes": row["sourceAudioBytes"],
                }
                for row in tracks
            ]
        ),
        "arraySetSha256": canonical_sha256(
            [
                {
                    "trackId": row["trackId"],
                    "cachedArraySha256": row["cachedArraySha256"],
                    "freshArraySha256": row["freshArraySha256"],
                    "frames": row["frames"],
                    "featureCount": row["featureCount"],
                }
                for row in tracks
            ]
        ),
    }
    return {**payload, "artifactSha256": canonical_sha256(payload)}


def _roots(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    return (
        tmp_path / "benchmark-artifacts",
        tmp_path / "runtime-artifacts",
        tmp_path / "group-artifacts",
        tmp_path / "summary-artifacts",
    )


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _write_json(path: Path, value: Any) -> bytes:
    raw = _json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def _timing(duration: float, starts: list[float]) -> dict[str, Any]:
    payload = {
        "schemaVersion": EXPLICIT_BAR_GRID_SCHEMA,
        "durationSeconds": duration,
        "barStartsSeconds": starts,
        "timingProvenance": {
            "barStartsSeconds": {
                "status": "explicit",
                "sourceClass": "runtime",
                "sourceId": SOURCE_ID,
                "sourceContractSha256": TIMING_SOURCE_CONTRACT_SHA256,
                "deployable": True,
                "referenceFree": True,
            }
        },
    }
    return {**payload, "contractSha256": canonical_sha256(payload)}


def _prediction(track_id: str, duration: float, products: list[str]) -> dict[str, Any]:
    bar_duration = duration / len(products)
    segments = [
        {
            "start": index * bar_duration,
            "end": (index + 1) * bar_duration,
            "label": f"{product}:maj" if len(product) <= 2 else product,
            "productLabel": product,
            "confidence": 0.9,
            "productConfidence": 0.9,
        }
        for index, product in enumerate(products)
    ]
    members = [
        {
            "ordinal": 0,
            "fileName": "fixture.onnx",
            "modelSha256": MODEL_SHA256,
            "bytes": 123,
            "runtimeContractSha256": hashlib.sha256(b"runtime").hexdigest(),
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
        "decoderContractSha256": DECODER_SHA256,
        "modelOrEnsembleSha256": MODEL_SHA256,
        "jointProductBlend": 0.75,
        "memberOrderSha256": canonical_sha256(members),
        "commonWeights": [1.0],
        "jointContributorIndices": [0],
        "jointContributorWeights": [1.0],
    }
    core_sha256 = hashlib.sha256(f"core:{track_id}".encode()).hexdigest()
    uncertainty_sha256 = hashlib.sha256(f"uncertainty:{track_id}".encode()).hexdigest()
    return {
        "schemaVersion": "chord_prediction_v1",
        "id": track_id,
        "durationSeconds": duration,
        "frameSeconds": 0.1,
        "decoderContractSha256": DECODER_SHA256,
        "segments": segments,
        "uncertainty": {
            "schemaVersion": FACTORIZED_UNCERTAINTY_SCHEMA,
            "contractSha256": UNCERTAINTY_CONTRACT_SHA256,
            "referenceFree": True,
            "binding": binding,
            "members": members,
        },
        "predictionCoreSha256": core_sha256,
        "uncertaintySha256": uncertainty_sha256,
    }


def _feature_values(
    *,
    coverage: float = 1.0,
    dominance: float = 1.0,
    transitions: int = 0,
) -> dict[str, float | int]:
    values: dict[str, float | int] = {name: 0.0 for name in BAR_FEATURE_NAMES}
    values["predictionCoverage"] = coverage
    values["predictionDominance"] = dominance
    values["predictionTransitionCount"] = transitions
    return values


def _fake_summary(prediction: dict[str, Any], timing: dict[str, Any]) -> dict[str, Any]:
    starts = list(timing["barStartsSeconds"])
    ends = [*starts[1:], prediction["durationSeconds"]]
    segments = prediction["segments"]
    bars = []
    for index, (start, end) in enumerate(zip(starts, ends, strict=True)):
        overlaps: list[tuple[dict[str, Any], float]] = []
        by_product: dict[str, float] = {}
        covered = 0.0
        for segment in segments:
            overlap = min(end, float(segment["end"])) - max(start, float(segment["start"]))
            if overlap <= 0:
                continue
            overlaps.append((segment, overlap))
            product = str(segment["productLabel"])
            by_product[product] = by_product.get(product, 0.0) + overlap
            covered += overlap
        product, product_duration = (
            min(by_product.items(), key=lambda item: (-item[1], item[0])) if by_product else (None, 0.0)
        )
        duration = end - start
        coverage = covered / duration
        dominance = product_duration / covered if covered else 0.0
        transitions = max(0, len(overlaps) - 1)
        bars.append(
            {
                "trackId": prediction["id"],
                "index": index,
                "start": start,
                "end": end,
                "predictionProduct": product,
                "predictionProductDurationSeconds": product_duration,
                "predictionCoverage": coverage,
                "predictionDominance": dominance,
                "predictionTransitionCount": transitions,
                "featureValues": _feature_values(
                    coverage=coverage,
                    dominance=dominance,
                    transitions=transitions,
                ),
            }
        )
    payload = {
        "schemaVersion": BAR_UNCERTAINTY_SCHEMA,
        "referenceFree": True,
        "deployable": True,
        "selectorUseAllowed": True,
        "timingOracleUsed": False,
        "trackId": prediction["id"],
        "durationSeconds": prediction["durationSeconds"],
        "binding": {
            "predictionCoreSha256": prediction["predictionCoreSha256"],
            "uncertaintySha256": prediction["uncertaintySha256"],
            "uncertaintyContractSha256": UNCERTAINTY_CONTRACT_SHA256,
            "sourceFeatureKind": "multiband_chroma_v2",
            "sourceFeatureSpecSha256": FEATURE_SPEC_SHA256,
            "observabilityProfileSchemaVersion": "chord_existing_feature_matrix_observability_v1",
            "barFeatureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
            "timingSha256": canonical_sha256(timing),
            "timingContractSha256": timing["contractSha256"],
            "timingSourceContractSha256": TIMING_SOURCE_CONTRACT_SHA256,
        },
        "featureContract": {"contractSha256": BAR_FEATURE_CONTRACT_SHA256},
        "timing": {
            "schemaVersion": EXPLICIT_BAR_GRID_SCHEMA,
            "sourceClass": "runtime",
            "sourceId": SOURCE_ID,
            "deployable": True,
            "durationSeconds": timing["durationSeconds"],
            "predictionDurationSeconds": prediction["durationSeconds"],
            "durationAlignment": (
                "exact"
                if timing["durationSeconds"] == prediction["durationSeconds"]
                else "player-canonical-millisecond"
            ),
            "gridStartSeconds": starts[0],
            "excludedPrefixDurationSeconds": starts[0],
            "barCount": len(bars),
        },
        "bars": bars,
    }
    return {**payload, "summarySha256": canonical_sha256(payload)}


def _reference(duration: float, products: list[str], *, mixed_last: bool = False) -> dict[str, Any]:
    bar_duration = duration / len(products)
    segments: list[dict[str, Any]] = []
    for index, product in enumerate(products):
        start = index * bar_duration
        end = (index + 1) * bar_duration
        if mixed_last and index == len(products) - 1:
            middle = (start + end) / 2
            segments.extend(
                [
                    {"start": start, "end": middle, "label": f"{product}:maj"},
                    {"start": middle, "end": end, "label": "G:maj"},
                ]
            )
        else:
            segments.append({"start": start, "end": end, "label": f"{product}:maj"})
    return {"durationSeconds": duration, "segments": segments}


def _fixture(
    tmp_path: Path,
    *,
    definitions: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[Path]]:
    benchmark_root, runtime_root, group_root, _summary_root = _roots(tmp_path)
    benchmark_root.mkdir(parents=True, exist_ok=True)
    runtime_root.mkdir(parents=True, exist_ok=True)
    group_root.mkdir(parents=True, exist_ok=True)
    definitions = definitions or [
        {
            "id": "guitar-comp-01",
            "datasetId": "guitarset",
            "role": "comp",
            "group": "guitar-composition-01",
            "prediction": ["C"],
            "reference": ["C"],
        },
        {
            "id": "guitar-player-01",
            "datasetId": "guitarset",
            "role": "solo-player-00",
            "group": "guitar-composition-01",
            "prediction": ["D"],
            "reference": ["C"],
        },
        {
            "id": "derivative-other-corpus",
            "datasetId": "cross-corpus",
            "role": "known-derivative",
            "group": "guitar-composition-01",
            "prediction": ["C"],
            "reference": ["C"],
        },
    ]
    report_rows = []
    runtime_rows = []
    group_rows = []
    reference_paths = []
    predictions: list[dict[str, Any]] = []
    for definition in definitions:
        track_id = definition["id"]
        products = definition["prediction"]
        prediction_duration = float(definition.get("predictionDuration", 0.4 * len(products)))
        runtime_duration = math.floor(prediction_duration * 1000 + 0.5) / 1000
        prediction = _prediction(track_id, prediction_duration, products)
        coverage = float(definition.get("predictionCoverage", 1.0))
        dominance = float(definition.get("predictionDominance", 1.0))
        if coverage != 1.0 or dominance != 1.0:
            bar_duration = prediction_duration / len(products)
            segments: list[dict[str, Any]] = []
            for index, product in enumerate(products):
                start = index * bar_duration
                covered_end = start + bar_duration * coverage
                dominant_end = start + bar_duration * coverage * dominance
                segments.append(
                    {
                        "start": start,
                        "end": dominant_end,
                        "label": f"{product}:maj",
                        "productLabel": product,
                        "confidence": 0.9,
                        "productConfidence": 0.9,
                    }
                )
                if dominant_end < covered_end:
                    alternate = "G" if product != "G" else "C"
                    segments.append(
                        {
                            "start": dominant_end,
                            "end": covered_end,
                            "label": f"{alternate}:maj",
                            "productLabel": alternate,
                            "confidence": 0.9,
                            "productConfidence": 0.9,
                        }
                    )
            prediction["segments"] = segments
        if definition.get("confidenceMissing"):
            for segment in prediction["segments"]:
                segment.pop("productConfidence", None)
                segment.pop("confidence", None)
        predictions.append(prediction)
        prediction_file = Path("predictions") / f"{track_id}.json"
        prediction_bytes = _write_json(benchmark_root / prediction_file, prediction)
        timing = _timing(
            runtime_duration,
            [0.4 * index for index in range(len(products))],
        )
        timing_sha256 = canonical_sha256(timing)
        timing_file = Path(f"timing-{timing_sha256}.json")
        _write_json(runtime_root / timing_file, timing)
        reference = _reference(
            prediction_duration,
            definition["reference"],
            mixed_last=bool(definition.get("mixedLast")),
        )
        reference_file = Path("references") / f"{track_id}.json"
        reference_bytes = _write_json(group_root / reference_file, reference)
        reference_paths.append((group_root / reference_file).resolve())
        report_rows.append(
            {
                "id": track_id,
                "datasetId": definition["datasetId"],
                "split": "development",
                "predictionFile": prediction_file.as_posix(),
                "predictionSha256": hashlib.sha256(prediction_bytes).hexdigest(),
                "predictionCoreSha256": prediction["predictionCoreSha256"],
                "uncertaintySha256": prediction["uncertaintySha256"],
                "referenceSha256": hashlib.sha256(reference_bytes).hexdigest(),
            }
        )
        decoded_rate = 44_100
        decoded_count = round(runtime_duration * decoded_rate)
        canonical_duration_milliseconds = round(runtime_duration * 1000)
        audio_sha256 = str(
            definition.get(
                "audioSha256",
                hashlib.sha256(f"audio:{track_id}".encode()).hexdigest(),
            )
        )
        audio_binding = {
            "sourceAudioSha256": audio_sha256,
            "decodedPcmSha256": hashlib.sha256(f"decoded-pcm:{track_id}".encode()).hexdigest(),
            "decodedPcmSampleCount": decoded_count,
            "decodedSampleRateHz": decoded_rate,
            "decodedChannelCount": 2,
            "decodedDurationSeconds": decoded_count / decoded_rate,
            "canonicalDurationMilliseconds": canonical_duration_milliseconds,
            "analyzerPcmSha256": hashlib.sha256(f"analyzer-pcm:{track_id}".encode()).hexdigest(),
            "analyzerPcmSampleCount": decoded_count // 4,
            "analyzerSampleRateHz": 11_025,
        }
        runtime_contract = RUNTIME_ANALYZER_CONTRACT["runtime"]
        runtime_identity = {
            "browserProduct": f"Chrome/{runtime_contract['browserVersion']}",
            "browserRevision": "fixture-revision",
            "browserProtocolVersion": "1.3",
            "browserJavaScriptVersion": "fixture-v8",
            "navigatorUserAgent": (f"Mozilla/5.0 HeadlessChrome/{runtime_contract['browserVersion']}"),
            "navigatorPlatform": "fixture-platform",
            "nodeVersion": runtime_contract["nodeVersion"],
        }
        runtime_payload = {
            "trackId": track_id,
            "split": "development",
            "selectorUseAllowed": True,
            "sourceManifestSha256": SOURCE_MANIFEST_SHA256,
            "audioSha256": audio_sha256,
            "audioBinding": audio_binding,
            "audioBindingSha256": canonical_sha256(audio_binding),
            "analysisVersion": 2,
            "runtimeIdentity": runtime_identity,
            "runtimeIdentitySha256": canonical_sha256(runtime_identity),
            "timingFile": timing_file.as_posix(),
            "timingSha256": timing_sha256,
            "timingContractSha256": timing["contractSha256"],
            "timingSourceContractSha256": TIMING_SOURCE_CONTRACT_SHA256,
            "durationSeconds": canonical_duration_milliseconds / 1000,
            "barCount": len(products),
        }
        runtime_rows.append({**runtime_payload, "trackArtifactSha256": canonical_sha256(runtime_payload)})
        group_rows.append(
            {
                "trackId": track_id,
                "datasetId": definition["datasetId"],
                "role": definition["role"],
                "confidenceGroupId": definition["group"],
                "referencePath": reference_file.as_posix(),
                "split": "development",
            }
        )

    report_rows.sort(key=lambda value: value["id"])
    runtime_rows.sort(key=lambda value: value["trackId"])
    audio_lineage = _audio_lineage(tmp_path, report_rows, runtime_rows)
    audio_lineage_projection = project_development_audio_lineage(audio_lineage)
    audio_lineage_binding_payload = {
        "schemaVersion": "chord_benchmark_audio_lineage_v1",
        "verificationMode": AUDIO_LINEAGE_VERIFICATION_MODE,
        "sourceArtifactSha256": audio_lineage["artifactSha256"],
        "projection": audio_lineage_projection,
        "projectionSha256": audio_lineage_projection["projectionSha256"],
        "featureArrayVerification": FEATURE_ARRAY_VERIFICATION,
    }
    audio_lineage_binding = {
        **audio_lineage_binding_payload,
        "bindingSha256": canonical_sha256(audio_lineage_binding_payload),
    }
    first_prediction = predictions[0]
    binding = first_prediction["uncertainty"]["binding"]
    members = first_prediction["uncertainty"]["members"]
    experiment = {
        "schemaVersion": UNCERTAINTY_DEVELOPMENT_EXPERIMENT_SCHEMA,
        "uncertaintySchemaVersion": FACTORIZED_UNCERTAINTY_SCHEMA,
        "contractSha256": UNCERTAINTY_CONTRACT_SHA256,
        "referenceFree": True,
        "featureBinding": {
            "featureKind": "multiband_chroma_v2",
            "featureCount": 61,
            "featureSpecSha256": FEATURE_SPEC_SHA256,
        },
        "featureBindingSha256": canonical_sha256(
            {
                "featureKind": "multiband_chroma_v2",
                "featureCount": 61,
                "featureSpecSha256": FEATURE_SPEC_SHA256,
            }
        ),
        "memberBinding": members,
        "memberBindingSha256": canonical_sha256(members),
        "binding": binding,
        "bindingSha256": canonical_sha256(binding),
        "allowedSplits": ["dev", "development"],
        "certificationPolicy": "development-only fixture",
        "audioLineage": audio_lineage_binding,
        "trackCount": len(report_rows),
        "predictionCoreSetSha256": canonical_sha256(
            [{"id": row["id"], "sha256": row["predictionCoreSha256"]} for row in report_rows]
        ),
        "uncertaintySetSha256": canonical_sha256(
            [{"id": row["id"], "sha256": row["uncertaintySha256"]} for row in report_rows]
        ),
    }
    report = {
        "schemaVersion": BENCHMARK_REPORT_SCHEMA,
        "engine": "factorized",
        "split": "development",
        "developmentOnlyExperiment": True,
        "promotionEligible": False,
        "beatGridSource": "none",
        "oracleTimingUsed": False,
        "uncertaintyExperiment": experiment,
        "tracks": report_rows,
    }

    source_manifests = [{"sourceManifestSha256": SOURCE_MANIFEST_SHA256, "trackCount": len(runtime_rows)}]
    timing_artifacts = sorted(
        {
            row["timingFile"]: {
                "timingFile": row["timingFile"],
                "timingSha256": row["timingSha256"],
                "timingContractSha256": row["timingContractSha256"],
            }
            for row in runtime_rows
        }.values(),
        key=lambda value: value["timingFile"],
    )
    runtime_payload = {
        "schemaVersion": OUTPUT_MANIFEST_SCHEMA,
        "split": "development",
        "developmentOnly": True,
        "promotionEligible": False,
        "selectorUseAllowed": True,
        "runtimeAttested": True,
        "analyzerContract": RUNTIME_ANALYZER_CONTRACT,
        "sourceManifestSetSha256": canonical_sha256(source_manifests),
        "sourceManifests": source_manifests,
        "trackSetSha256": canonical_sha256(
            [{"trackId": row["trackId"], "trackArtifactSha256": row["trackArtifactSha256"]} for row in runtime_rows]
        ),
        "timingArtifacts": timing_artifacts,
        "tracks": runtime_rows,
        "previousManifestSha256": None,
    }
    runtime = {**runtime_payload, "manifestSha256": canonical_sha256(runtime_payload)}
    _write_json(runtime_root / "manifest.json", runtime)
    groups = build_bar_selector_group_manifest(group_rows, reference_root=group_root)
    return report, runtime, groups, audio_lineage, reference_paths


@pytest.fixture(autouse=True)
def _prediction_only_summarizer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bar_examples, "summarize_prediction_bars", _fake_summary)
    metadata_validator = bar_examples.validate_development_audio_lineage

    def validate_synthetic_lineage(
        artifact: dict[str, Any],
        *,
        verify_files: bool = False,
        extractor: Any = None,
        dependency_versions: dict[str, str] | None = None,
    ) -> Any:
        assert verify_files is True
        assert extractor is bar_examples.extract_student_features
        assert dependency_versions is None
        return metadata_validator(artifact, verify_files=False)

    monkeypatch.setattr(
        bar_examples,
        "validate_development_audio_lineage",
        validate_synthetic_lineage,
    )


def _build(
    tmp_path: Path,
    report: dict[str, Any],
    runtime: dict[str, Any],
    groups: dict[str, Any],
    audio_lineage: dict[str, Any],
) -> dict[str, Any]:
    benchmark_root, runtime_root, group_root, summary_root = _roots(tmp_path)
    return build_bar_selector_examples(
        report,
        audio_lineage_manifest=audio_lineage,
        benchmark_root=benchmark_root,
        runtime_bar_grid_manifest=runtime,
        runtime_bar_grid_root=runtime_root,
        group_manifest=groups,
        group_manifest_root=group_root,
        summary_output_root=summary_root,
    )


def test_group_manifest_builder_seals_relative_references_and_explicit_cross_corpus_groups(
    tmp_path: Path,
) -> None:
    first = _write_json(tmp_path / "references" / "comp.json", _reference(0.4, ["C"]))
    second_path = tmp_path / "references" / "solo.json"
    second = _write_json(second_path, _reference(0.4, ["C"]))
    manifest = build_bar_selector_group_manifest(
        [
            {
                "trackId": "composition",
                "split": "development",
                "datasetId": "guitarset",
                "role": "comp",
                "confidenceGroupId": "same-musical-work",
                "referencePath": "references/comp.json",
            },
            {
                "trackId": "external-derivative",
                "split": "development",
                "datasetId": "other-corpus",
                "role": "known-derivative",
                "confidenceGroupId": "same-musical-work",
                "referencePath": str(second_path.resolve()),
            },
        ],
        reference_root=tmp_path,
    )
    assert manifest["schemaVersion"] == GROUP_MANIFEST_SCHEMA
    assert [track["referenceFile"] for track in manifest["tracks"]] == [
        "references/comp.json",
        "references/solo.json",
    ]
    assert [track["referenceSha256"] for track in manifest["tracks"]] == [
        hashlib.sha256(first).hexdigest(),
        hashlib.sha256(second).hexdigest(),
    ]
    assert {track["confidenceGroupId"] for track in manifest["tracks"]} == {"same-musical-work"}
    assert (
        canonical_sha256({key: value for key, value in manifest.items() if key != "manifestSha256"})
        == manifest["manifestSha256"]
    )


@pytest.mark.parametrize("sealed_split", ["calibration", "test", "heldout"])
def test_group_manifest_builder_rejects_sealed_split_before_reference_path_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sealed_split: str,
) -> None:
    opened: list[Path] = []
    resolved: list[Path] = []
    original_open = Path.open
    original_resolve = Path.resolve

    def observed_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        opened.append(self)
        return original_open(self, *args, **kwargs)

    def observed_resolve(self: Path, *args: Any, **kwargs: Any) -> Path:
        resolved.append(self)
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed_open)
    monkeypatch.setattr(Path, "resolve", observed_resolve)
    with pytest.raises(ValueError, match="before any artifact path is accessed"):
        build_bar_selector_group_manifest(
            [
                {
                    "trackId": "sealed",
                    "split": sealed_split,
                    "datasetId": "guitarset",
                    "role": "comp",
                    "confidenceGroupId": "must-not-fallback",
                    "referencePath": "does-not-exist.json",
                }
            ],
            reference_root=tmp_path,
        )
    assert opened == []
    assert resolved == []


def test_group_manifest_builder_requires_explicit_group_before_reference_path_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolved: list[Path] = []
    original_resolve = Path.resolve

    def observed_resolve(self: Path, *args: Any, **kwargs: Any) -> Path:
        resolved.append(self)
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", observed_resolve)
    with pytest.raises(ValueError, match="confidenceGroupId must be a nonempty string"):
        build_bar_selector_group_manifest(
            [
                {
                    "trackId": "no-explicit-group",
                    "split": "development",
                    "datasetId": "guitarset",
                    "role": "comp",
                    "confidenceGroupId": "",
                    "referencePath": "does-not-exist.json",
                }
            ],
            reference_root=tmp_path,
        )
    assert resolved == []


def test_builds_exact_compact_selector_artifact_and_preserves_explicit_groups(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    result = _build(tmp_path, report, runtime, groups, audio_lineage)

    assert result["schemaVersion"] == EXAMPLES_SCHEMA
    assert result["split"] == "development"
    assert result["developmentOnly"] is True
    assert result["promotionEligible"] is False
    assert [example["trackId"] for example in result["examples"]] == [
        "derivative-other-corpus",
        "guitar-comp-01",
        "guitar-player-01",
    ]
    assert {example["confidenceGroupId"] for example in result["examples"]} == {"guitar-composition-01"}
    assert [example["outcome"] for example in result["examples"]] == [
        {"correct": True},
        {"correct": True},
        {"correct": False},
    ]
    assert canonical_sha256(result["examples"]) == result["exampleSetSha256"]
    assert canonical_sha256(result["sharedBindings"]) == result["sharedBindingsSha256"]
    assert (
        canonical_sha256({key: value for key, value in result.items() if key != "artifactSha256"})
        == result["artifactSha256"]
    )
    assert set(result["sharedBindings"]) == bar_examples._SHARED_BINDING_KEYS
    assert result["sharedBindings"]["barOutcomeEligibilityContract"] == BAR_OUTCOME_ELIGIBILITY_CONTRACT
    assert result["sharedBindings"]["barOutcomeEligibilityContractSha256"] == BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256
    assert BAR_OUTCOME_ELIGIBILITY_CONTRACT["correctnessRule"] == "predictionProduct == referenceProduct"
    assert "audit-only" in BAR_OUTCOME_ELIGIBILITY_CONTRACT["legacyProductConfidenceAvailability"]
    assert "never label eligibility" in BAR_OUTCOME_ELIGIBILITY_CONTRACT["confidenceThresholdRole"]
    assert BAR_OUTCOME_ELIGIBILITY_CONTRACT == SELECTOR_OUTCOME_ELIGIBILITY_CONTRACT
    assert BAR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256 == SELECTOR_OUTCOME_ELIGIBILITY_CONTRACT_SHA256
    assert result["sourceAudioLineageSha256"] == audio_lineage["artifactSha256"]
    assert result["sourceAudioLineageProjection"] == report["uncertaintyExperiment"]["audioLineage"]["projection"]
    assert result["audioLineageVerificationMode"] == AUDIO_LINEAGE_VERIFICATION_MODE
    assert result["featureArrayVerification"] == FEATURE_ARRAY_VERIFICATION
    assert result["audioGroupAudit"]["schemaVersion"] == AUDIO_GROUP_AUDIT_SCHEMA
    assert result["audioGroupAudit"]["trackCount"] == len(report["tracks"])
    assert result["audioGroupAuditSha256"] == result["audioGroupAudit"]["auditSha256"]
    assert result["labelDeterminacyAudit"]["emittedExampleCount"] == len(result["examples"])
    assert result["labelDeterminacyAudit"]["excludedReferenceIndeterminateBarCount"] == 0
    assert result["labelDeterminacyAudit"]["excludedPredictionNoneligibleBarCount"] == 0
    for example in result["examples"]:
        assert set(example) == bar_examples._EXAMPLE_KEYS
        assert example["barSummary"]["schemaVersion"] == COMPACT_BAR_SUMMARY_SCHEMA
        assert example["barSummary"]["trackId"] == example["trackId"]
        assert example["sourceAudioSha256"] == example["barSummary"]["sourceAudioSha256"]
        assert example["cachedFeatureArraySha256"] == example["barSummary"]["cachedFeatureArraySha256"]
        assert example["audioLineageRowSha256"] == example["barSummary"]["audioLineageRowSha256"]
        assert tuple(example["barSummary"]["featureValues"]) == BAR_FEATURE_NAMES
        assert (
            canonical_sha256({key: value for key, value in example["barSummary"].items() if key != "barSummarySha256"})
            == example["barSummary"]["barSummarySha256"]
        )
        assert set(example["outcome"]) == {"correct"}
        assert not ({"datasetId", "role", "reference", "eligible"} & set(example["barSummary"]["featureValues"]))

    # Direct consumer-boundary validation: the selector can ingest the exact
    # bindings and every emitted compact row without adapting the schema.
    selector_binding = _validated_shared_bindings(result["sharedBindings"])
    for example in result["examples"]:
        _validated_example(example, selector_binding)


def test_rejects_production_extractor_entrypoint_drift_before_leaf_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    audio_lineage = deepcopy(audio_lineage)
    contract = audio_lineage["extractorContract"]
    contract["entrypoint"] = "fixture.not_the_production_extractor"
    contract["contractSha256"] = canonical_sha256(
        {key: value for key, value in contract.items() if key != "contractSha256"}
    )
    audio_lineage["artifactSha256"] = canonical_sha256(
        {key: value for key, value in audio_lineage.items() if key != "artifactSha256"}
    )
    touched: list[str] = []
    monkeypatch.setattr(
        bar_examples,
        "_artifact_path",
        lambda *args, **kwargs: touched.append("leaf") or Path("forbidden"),
    )
    with pytest.raises(ValueError, match="production extract_student_features"):
        _build(tmp_path, report, runtime, groups, audio_lineage)
    assert touched == []


def test_full_production_lineage_verification_precedes_timing_and_prediction_leaves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    events: list[str] = []
    lineage_validator = bar_examples.validate_development_audio_lineage
    runtime_validator = bar_examples.validate_runtime_bar_grid_manifest
    artifact_path = bar_examples._artifact_path

    def recording_lineage(artifact: dict[str, Any], **kwargs: Any) -> Any:
        assert kwargs == {
            "verify_files": True,
            "extractor": bar_examples.extract_student_features,
        }
        events.append("full-lineage")
        return lineage_validator(artifact, **kwargs)

    def recording_runtime(manifest: dict[str, Any], **kwargs: Any) -> Any:
        if kwargs.get("artifact_root") is not None:
            assert events == ["full-lineage"]
            events.append("timing-leaves")
        return runtime_validator(manifest, **kwargs)

    def recording_artifact_path(*args: Any, **kwargs: Any) -> Path:
        assert events[:2] == ["full-lineage", "timing-leaves"]
        events.append("artifact-leaf")
        return artifact_path(*args, **kwargs)

    monkeypatch.setattr(bar_examples, "validate_development_audio_lineage", recording_lineage)
    monkeypatch.setattr(bar_examples, "validate_runtime_bar_grid_manifest", recording_runtime)
    monkeypatch.setattr(bar_examples, "_artifact_path", recording_artifact_path)
    _build(tmp_path, report, runtime, groups, audio_lineage)
    assert events[0] == "full-lineage"
    assert events[1] == "timing-leaves"
    assert events.count("artifact-leaf") == len(report["tracks"]) * 3


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("cachedFeatureArraySha256", hashlib.sha256(b"spliced-cache").hexdigest(), "audio lineage"),
        ("freshFeatureArraySha256", hashlib.sha256(b"spliced-fresh").hexdigest(), "audio lineage"),
        ("canonicalDurationMilliseconds", 401, "audio lineage"),
        ("audioLineageRowSha256", hashlib.sha256(b"spliced-row").hexdigest(), "audio lineage"),
    ],
)
def test_rejects_report_lineage_cache_or_millisecond_mismatch_before_leaf_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str | int,
    message: str,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    report["tracks"][0][field] = value
    touched: list[str] = []
    monkeypatch.setattr(
        bar_examples,
        "_artifact_path",
        lambda *args, **kwargs: touched.append("leaf") or Path("forbidden"),
    )
    with pytest.raises(ValueError, match=message):
        _build(tmp_path, report, runtime, groups, audio_lineage)
    assert touched == []


def test_rejects_resealed_runtime_audio_splice_before_leaf_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    runtime = deepcopy(runtime)
    row = runtime["tracks"][0]
    spliced_sha256 = hashlib.sha256(b"different-source-audio").hexdigest()
    row["audioSha256"] = spliced_sha256
    row["audioBinding"]["sourceAudioSha256"] = spliced_sha256
    row["audioBindingSha256"] = canonical_sha256(row["audioBinding"])
    row["trackArtifactSha256"] = canonical_sha256(
        {key: value for key, value in row.items() if key != "trackArtifactSha256"}
    )
    runtime["trackSetSha256"] = canonical_sha256(
        [
            {"trackId": track["trackId"], "trackArtifactSha256": track["trackArtifactSha256"]}
            for track in runtime["tracks"]
        ]
    )
    runtime["manifestSha256"] = canonical_sha256(
        {key: value for key, value in runtime.items() if key != "manifestSha256"}
    )
    touched: list[str] = []
    monkeypatch.setattr(
        bar_examples,
        "_artifact_path",
        lambda *args, **kwargs: touched.append("leaf") or Path("forbidden"),
    )
    with pytest.raises(ValueError, match="Runtime audio and audio lineage disagree"):
        _build(tmp_path, report, runtime, groups, audio_lineage)
    assert touched == []


def test_duplicate_audio_must_share_group_and_same_group_is_audited(tmp_path: Path) -> None:
    shared_audio_sha256 = hashlib.sha256(b"identical-source-audio").hexdigest()
    base = [
        {
            "id": "duplicate-a",
            "datasetId": "fixture",
            "role": "comp",
            "group": "same-work",
            "prediction": ["C"],
            "reference": ["C"],
            "audioSha256": shared_audio_sha256,
        },
        {
            "id": "duplicate-b",
            "datasetId": "fixture",
            "role": "solo",
            "group": "different-work",
            "prediction": ["C"],
            "reference": ["C"],
            "audioSha256": shared_audio_sha256,
        },
    ]
    report, runtime, groups, audio_lineage, _references = _fixture(
        tmp_path / "rejected",
        definitions=base,
    )
    with pytest.raises(ValueError, match="Identical source audio bytes"):
        _build(tmp_path / "rejected", report, runtime, groups, audio_lineage)

    allowed = deepcopy(base)
    allowed[1]["group"] = "same-work"
    report, runtime, groups, audio_lineage, _references = _fixture(
        tmp_path / "allowed",
        definitions=allowed,
    )
    result = _build(tmp_path / "allowed", report, runtime, groups, audio_lineage)
    duplicate_rows = [row for row in result["audioGroupAudit"]["rows"] if row["trackCount"] == 2]
    assert duplicate_rows == [
        {
            "sourceAudioSha256": shared_audio_sha256,
            "confidenceGroupId": "same-work",
            "trackIds": ["duplicate-a", "duplicate-b"],
            "trackCount": 2,
        }
    ]
    assert result["audioGroupAudit"]["duplicateSourceAudioCount"] == 1
    assert result["audioGroupAudit"]["duplicateTrackCount"] == 1


def test_delegates_runtime_trust_to_strict_public_v2_validator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    observed: list[tuple[dict[str, Any], Path, bool]] = []
    original = bar_examples.validate_runtime_bar_grid_manifest

    def validating(
        manifest: dict[str, Any],
        *,
        artifact_root: Path | None = None,
        verify_sources: bool = True,
    ) -> dict[str, Any]:
        observed.append((manifest, artifact_root, verify_sources))
        return original(
            manifest,
            artifact_root=artifact_root,
            verify_sources=verify_sources,
        )

    monkeypatch.setattr(bar_examples, "validate_runtime_bar_grid_manifest", validating)
    _build(tmp_path, report, runtime, groups, audio_lineage)
    assert observed == [
        (runtime, None, False),
        (runtime, _roots(tmp_path)[1], True),
    ]
    assert runtime["schemaVersion"] == "chord_runtime_bar_grid_manifest_v2"
    assert runtime["runtimeAttested"] is True
    assert runtime["selectorUseAllowed"] is True


def test_all_features_and_compact_hashes_exist_before_first_reference_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, runtime, groups, audio_lineage, reference_paths = _fixture(tmp_path)
    summaries: list[dict[str, Any]] = []
    compact: list[dict[str, Any]] = []

    def observed_summary(prediction: dict[str, Any], timing: dict[str, Any]) -> dict[str, Any]:
        result = _fake_summary(prediction, timing)
        summaries.append(result)
        return result

    original_compact = bar_examples._compact_bar_summary

    def observed_compact(
        summary: dict[str, Any],
        bar: dict[str, Any],
        shared_bindings_sha256: str,
        audio_lineage_row: dict[str, Any],
        audio_lineage_projection_sha256: str,
    ) -> dict[str, Any]:
        result = original_compact(
            summary,
            bar,
            shared_bindings_sha256,
            audio_lineage_row,
            audio_lineage_projection_sha256,
        )
        compact.append(result)
        return result

    monkeypatch.setattr(bar_examples, "summarize_prediction_bars", observed_summary)
    monkeypatch.setattr(bar_examples, "_compact_bar_summary", observed_compact)
    original_open = Path.open
    protected = set(reference_paths)

    def guarded_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self.resolve() in protected:
            assert len(summaries) == len(report["tracks"])
            assert len(compact) == len(report["tracks"])
            for summary in summaries:
                assert (
                    canonical_sha256({key: value for key, value in summary.items() if key != "summarySha256"})
                    == summary["summarySha256"]
                )
            for bar in compact:
                assert (
                    canonical_sha256({key: value for key, value in bar.items() if key != "barSummarySha256"})
                    == bar["barSummarySha256"]
                )
            summary_by_track = {summary["trackId"]: summary for summary in summaries}
            summary_root = _roots(tmp_path)[3]
            for row in report["tracks"]:
                summary_path = summary_root / summary_artifact_filename(
                    row["id"],
                    summary_by_track[row["id"]]["summarySha256"],
                )
                assert summary_path.is_file()
                materialized = json.loads(summary_path.read_text(encoding="utf-8"))
                assert (
                    canonical_sha256({key: value for key, value in materialized.items() if key != "summarySha256"})
                    == materialized["summarySha256"]
                )
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    result = _build(tmp_path, report, runtime, groups, audio_lineage)
    assert len(result["examples"]) == 3


@pytest.mark.parametrize("sealed_split", ["calibration", "test", "heldout"])
@pytest.mark.parametrize("source", ["report", "runtime", "groups", "audio-lineage"])
def test_rejects_every_sealed_split_before_any_path_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sealed_split: str,
    source: str,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    values = {
        "report": report,
        "runtime": runtime,
        "groups": groups,
        "audio-lineage": audio_lineage,
    }
    values[source]["split"] = sealed_split
    opened: list[Path] = []
    resolved: list[Path] = []
    original_open = Path.open
    original_resolve = Path.resolve

    def observed_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        opened.append(self)
        return original_open(self, *args, **kwargs)

    def observed_resolve(self: Path, *args: Any, **kwargs: Any) -> Path:
        resolved.append(self)
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed_open)
    monkeypatch.setattr(Path, "resolve", observed_resolve)
    with pytest.raises(ValueError, match="before any artifact path is accessed"):
        _build(tmp_path, report, runtime, groups, audio_lineage)
    assert opened == []
    assert resolved == []


def test_requires_exact_track_set_identity(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    groups = deepcopy(groups)
    groups["tracks"] = groups["tracks"][:-1]
    groups["trackSetSha256"] = canonical_sha256(
        [{"trackId": row["trackId"], "trackMetadataSha256": row["trackMetadataSha256"]} for row in groups["tracks"]]
    )
    groups["manifestSha256"] = canonical_sha256(
        {key: value for key, value in groups.items() if key != "manifestSha256"}
    )
    with pytest.raises(ValueError, match="exact same track ids"):
        _build(tmp_path, report, runtime, groups, audio_lineage)


def test_confidence_group_is_mandatory_and_never_derived_from_track_metadata(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    groups = deepcopy(groups)
    track = groups["tracks"][0]
    track["confidenceGroupId"] = ""
    track["trackMetadataSha256"] = canonical_sha256(
        {key: value for key, value in track.items() if key != "trackMetadataSha256"}
    )
    groups["trackSetSha256"] = canonical_sha256(
        [{"trackId": row["trackId"], "trackMetadataSha256": row["trackMetadataSha256"]} for row in groups["tracks"]]
    )
    groups["manifestSha256"] = canonical_sha256(
        {key: value for key, value in groups.items() if key != "manifestSha256"}
    )
    with pytest.raises(ValueError, match="confidenceGroupId must be a nonempty string"):
        _build(tmp_path, report, runtime, groups, audio_lineage)


def test_emits_only_structurally_scorable_existing_bar_product_rows(tmp_path: Path) -> None:
    definitions = [
        {
            "id": "two-bars",
            "datasetId": "guitarset",
            "role": "comp",
            "group": "composition",
            "prediction": ["C", "C"],
            "reference": ["C", "C"],
            "mixedLast": True,
        }
    ]
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path, definitions=definitions)
    result = _build(tmp_path, report, runtime, groups, audio_lineage)
    assert [(example["barIndex"], example["outcome"]) for example in result["examples"]] == [(0, {"correct": True})]
    audit = result["labelDeterminacyAudit"]
    assert audit["totalBarCount"] == 2
    assert audit["referenceDeterminateBarCount"] == 1
    assert audit["excludedReferenceIndeterminateBarCount"] == 1
    assert audit["excludedPredictionNoneligibleBarCount"] == 0


def test_legacy_confidence_missing_is_audited_but_does_not_gate_boolean_label(
    tmp_path: Path,
) -> None:
    definitions = [
        {
            "id": "confidence-missing",
            "datasetId": "fixture",
            "role": "comp",
            "group": "composition",
            "prediction": ["C"],
            "reference": ["C"],
            "confidenceMissing": True,
        }
    ]
    report, runtime, groups, audio_lineage, _references = _fixture(
        tmp_path,
        definitions=definitions,
    )
    result = _build(tmp_path, report, runtime, groups, audio_lineage)
    assert [example["outcome"] for example in result["examples"]] == [{"correct": True}]
    audit = result["labelDeterminacyAudit"]
    assert audit["predictionConfidenceMissingBarCount"] == 1
    assert audit["predictionStructurallyScorableBarCount"] == 1
    assert audit["excludedPredictionNoneligibleBarCount"] == 0
    assert audit["emittedExampleCount"] == 1


@pytest.mark.parametrize(
    ("field", "value", "expected_examples", "exclusion_field"),
    [
        ("predictionCoverage", 0.75 - 5e-10, 0, "predictionUncoveredBarCount"),
        ("predictionCoverage", 0.75, 1, "predictionUncoveredBarCount"),
        ("predictionDominance", 0.75 - 5e-10, 0, "predictionMixedBarCount"),
        ("predictionDominance", 0.75, 1, "predictionMixedBarCount"),
    ],
)
def test_builder_uses_exact_application_structural_boundaries(
    tmp_path: Path,
    field: str,
    value: float,
    expected_examples: int,
    exclusion_field: str,
) -> None:
    definitions = [
        {
            "id": "structural-boundary",
            "datasetId": "fixture",
            "role": "comp",
            "group": "composition",
            "prediction": ["C"],
            "reference": ["C"],
            field: value,
        }
    ]
    report, runtime, groups, audio_lineage, _references = _fixture(
        tmp_path,
        definitions=definitions,
    )
    result = _build(tmp_path, report, runtime, groups, audio_lineage)
    audit = result["labelDeterminacyAudit"]
    assert len(result["examples"]) == expected_examples
    assert audit["predictionStructurallyScorableBarCount"] == expected_examples
    assert audit["excludedPredictionNoneligibleBarCount"] == 1 - expected_examples
    assert audit[exclusion_field] == 1 - expected_examples


def test_passes_every_frozen_outcome_and_eligibility_argument_explicitly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    original = bar_examples.score_bar_product_confidence
    observed: list[dict[str, Any]] = []

    def recording(reference: dict[str, Any], prediction: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        observed.append(dict(kwargs))
        return original(reference, prediction, **kwargs)

    monkeypatch.setattr(bar_examples, "score_bar_product_confidence", recording)
    _build(tmp_path, report, runtime, groups, audio_lineage)
    assert len(observed) == len(report["tracks"])
    for kwargs in observed:
        assert kwargs["confidence_thresholds"] == (0.0,)
        assert kwargs["reference_dominance"] == 0.75
        assert kwargs["prediction_coverage"] == 0.75
        assert kwargs["prediction_dominance"] == 0.75
        assert set(kwargs) == {
            "timing",
            "confidence_thresholds",
            "reference_dominance",
            "prediction_coverage",
            "prediction_dominance",
        }


def test_exact_player_millisecond_join_scores_full_precision_final_bar(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(
        tmp_path,
        definitions=[
            {
                "id": "full-precision-duration",
                "datasetId": "fixture",
                "role": "comp",
                "group": "duration-group",
                "prediction": ["C"],
                "reference": ["C"],
                "predictionDuration": 0.4004,
            }
        ],
    )
    result = _build(tmp_path, report, runtime, groups, audio_lineage)
    assert len(result["examples"]) == 1
    example = result["examples"][0]
    assert example["barSummary"]["end"] == 0.4004
    assert example["outcome"] == {"correct": True}
    assert runtime["tracks"][0]["durationSeconds"] == 0.4


def test_duration_join_rejects_nearby_but_noncanonical_runtime_value() -> None:
    prediction = _prediction("duration-drift", 0.4004, ["C"])
    timing = _timing(0.4, [0.0])
    summary = _fake_summary(prediction, timing)
    timing["durationSeconds"] = 0.4000000001
    summary["timing"]["durationSeconds"] = 0.4000000001
    with pytest.raises(ValueError, match="exactly equal"):
        bar_examples._frozen_bar_score_inputs(
            _reference(0.4004, ["C"]),
            prediction,
            timing,
            summary,
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("schema", "unsupported schemaVersion"),
        ("configuration", "eligibility configuration"),
        ("curve", "zero threshold contract"),
        ("nonboolean-correct", "frozen inclusion rule"),
    ],
)
def test_rejects_resealed_score_contract_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    original = bar_examples.score_bar_product_confidence

    def drifting(reference: dict[str, Any], prediction: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        score = deepcopy(original(reference, prediction, **kwargs))
        if mutation == "schema":
            score["schemaVersion"] = "chord_bar_product_confidence_v2"
        elif mutation == "configuration":
            score["configuration"]["predictionCoverage"] = 0.5
        elif mutation == "curve":
            score["curve"][0]["minimumConfidence"] = 0.1
        else:
            score["bars"][0]["correct"] = "true"
        return score

    monkeypatch.setattr(bar_examples, "score_bar_product_confidence", drifting)
    with pytest.raises(ValueError, match=message):
        _build(tmp_path, report, runtime, groups, audio_lineage)


def test_rejects_reference_hash_drift_after_prediction_features_are_sealed(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    reference_file = _roots(tmp_path)[2] / groups["tracks"][0]["referenceFile"]
    reference_file.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Reference file hash mismatch"):
        _build(tmp_path, report, runtime, groups, audio_lineage)


def test_rejects_prediction_and_runtime_hash_drift(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    prediction_file = _roots(tmp_path)[0] / report["tracks"][0]["predictionFile"]
    prediction_file.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Prediction file hash mismatch"):
        _build(tmp_path, report, runtime, groups, audio_lineage)

    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path / "second")
    timing_file = _roots(tmp_path / "second")[1] / runtime["tracks"][0]["timingFile"]
    timing = json.loads(timing_file.read_text(encoding="utf-8"))
    timing["barStartsSeconds"] = [0.01]
    _write_json(timing_file, timing)
    with pytest.raises(ValueError, match="content-addressed"):
        _build(tmp_path / "second", report, runtime, groups, audio_lineage)


def test_rejects_symlinked_summary_output_components(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    actual_output = tmp_path / "actual-summary-output"
    actual_output.mkdir()
    _roots(tmp_path)[3].symlink_to(actual_output, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked path component"):
        _build(tmp_path, report, runtime, groups, audio_lineage)
    assert list(actual_output.iterdir()) == []


@pytest.mark.parametrize("source_index", [0, 1, 2])
def test_preflights_summary_output_disjoint_from_every_source_root(
    tmp_path: Path,
    source_index: int,
) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    benchmark_root, runtime_root, group_root, _summary_root = _roots(tmp_path)
    source_roots = (benchmark_root, runtime_root, group_root)
    nested_output = source_roots[source_index] / "forbidden-summary-output"
    with pytest.raises(ValueError, match="path-disjoint"):
        build_bar_selector_examples(
            report,
            audio_lineage_manifest=audio_lineage,
            benchmark_root=benchmark_root,
            runtime_bar_grid_manifest=runtime,
            runtime_bar_grid_root=runtime_root,
            group_manifest=groups,
            group_manifest_root=group_root,
            summary_output_root=nested_output,
        )
    assert not nested_output.exists()


def test_preflight_resolves_summary_symlink_before_disjointness_check(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    benchmark_root, runtime_root, group_root, _summary_root = _roots(tmp_path)
    alias = tmp_path / "summary-alias"
    alias.symlink_to(benchmark_root, target_is_directory=True)
    nested_output = alias / "hidden-overlap"
    with pytest.raises(ValueError, match="path-disjoint"):
        build_bar_selector_examples(
            report,
            audio_lineage_manifest=audio_lineage,
            benchmark_root=benchmark_root,
            runtime_bar_grid_manifest=runtime,
            runtime_bar_grid_root=runtime_root,
            group_manifest=groups,
            group_manifest_root=group_root,
            summary_output_root=nested_output,
        )
    assert not (benchmark_root / "hidden-overlap").exists()


def test_rejects_offline_proxy_timing_even_when_all_proxy_hashes_are_resealed(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(
        tmp_path,
        definitions=[
            {
                "id": "proxy-track",
                "datasetId": "fixture",
                "role": "comp",
                "group": "proxy-group",
                "prediction": ["C"],
                "reference": ["C"],
            }
        ],
    )
    runtime = deepcopy(runtime)
    row = runtime["tracks"][0]
    runtime_root = _roots(tmp_path)[1]
    timing_path = runtime_root / row["timingFile"]
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    source = timing["timingProvenance"]["barStartsSeconds"]
    source["sourceClass"] = "offline-proxy"
    source["deployable"] = False
    timing["contractSha256"] = canonical_sha256(
        {key: value for key, value in timing.items() if key != "contractSha256"}
    )
    timing_sha256 = canonical_sha256(timing)
    replacement_name = f"timing-{timing_sha256}.json"
    replacement_path = runtime_root / replacement_name
    _write_json(replacement_path, timing)
    timing_path.unlink()
    row["timingFile"] = replacement_name
    row["timingSha256"] = timing_sha256
    row["timingContractSha256"] = timing["contractSha256"]
    row["trackArtifactSha256"] = canonical_sha256(
        {key: value for key, value in row.items() if key != "trackArtifactSha256"}
    )
    runtime["trackSetSha256"] = canonical_sha256(
        [
            {"trackId": track["trackId"], "trackArtifactSha256": track["trackArtifactSha256"]}
            for track in runtime["tracks"]
        ]
    )
    runtime["timingArtifacts"] = [
        {
            "timingFile": replacement_name,
            "timingSha256": timing_sha256,
            "timingContractSha256": timing["contractSha256"],
        }
    ]
    runtime["manifestSha256"] = canonical_sha256(
        {key: value for key, value in runtime.items() if key != "manifestSha256"}
    )
    _write_json(runtime_root / "manifest.json", runtime)
    with pytest.raises(ValueError, match="not explicit runtime timing"):
        _build(tmp_path, report, runtime, groups, audio_lineage)


def test_rejects_resealed_nonattested_runtime_manifest(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    runtime = deepcopy(runtime)
    runtime["runtimeAttested"] = False
    runtime["selectorUseAllowed"] = False
    runtime["manifestSha256"] = canonical_sha256(
        {key: value for key, value in runtime.items() if key != "manifestSha256"}
    )
    _write_json(_roots(tmp_path)[1] / "manifest.json", runtime)
    with pytest.raises(ValueError, match="not attested for selector use"):
        _build(tmp_path, report, runtime, groups, audio_lineage)


def test_refuses_to_overwrite_existing_mismatched_content_addressed_summary(tmp_path: Path) -> None:
    report, runtime, groups, audio_lineage, _references = _fixture(tmp_path)
    row = report["tracks"][0]
    prediction = json.loads((_roots(tmp_path)[0] / row["predictionFile"]).read_text(encoding="utf-8"))
    runtime_by_id = {track["trackId"]: track for track in runtime["tracks"]}
    timing = json.loads((_roots(tmp_path)[1] / runtime_by_id[row["id"]]["timingFile"]).read_text(encoding="utf-8"))
    summary = _fake_summary(prediction, timing)
    destination = _roots(tmp_path)[3] / summary_artifact_filename(row["id"], summary["summarySha256"])
    destination.parent.mkdir()
    original = b"unrelated existing content\n"
    destination.write_bytes(original)

    with pytest.raises(ValueError, match="Refusing to overwrite mismatched summary artifact"):
        _build(tmp_path, report, runtime, groups, audio_lineage)
    assert destination.read_bytes() == original
