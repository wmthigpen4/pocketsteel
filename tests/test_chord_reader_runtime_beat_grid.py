from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import shutil
import struct
from typing import Any
import wave

import pytest

from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.runtime_bar_grid import (
    RUNNER_OUTPUT_SCHEMA as PARENT_RUNNER_SCHEMA,
    SOURCE_ID as PARENT_SOURCE_ID,
    _generate_offline_proxy_bar_grids_for_tests,
    generate_runtime_bar_grids,
    validate_runtime_bar_grid_manifest,
)
from steel_guitar_rag.chord_reader.runtime_beat_grid import (
    ANALYZER_CONTRACT_SCHEMA,
    CONFIDENCE_USE,
    INPUT_MANIFEST_SCHEMA,
    METER_PULSES,
    OUTPUT_RECEIPT_SCHEMA,
    PLAYER_REPLAY_CONTRACT_SCHEMA,
    RUNNER_OUTPUT_SCHEMA,
    SOURCE_ID,
    _exact_milliseconds_from_seconds,
    _generate_offline_proxy_beat_grid_receipt_for_tests,
    _materialized_runner_source,
    _validate_analyzer_contract_claim,
    _validate_player_contract_claim,
    beat_analyzer_contract,
    generate_runtime_beat_grid_receipt,
    player_replay_contract,
    validate_runtime_beat_grid_receipt,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = REPO_ROOT / "scripts" / "chord_runtime_bar_analyzer.js"
GENERATOR = REPO_ROOT / "steel_guitar_rag" / "chord_reader" / "runtime_beat_grid.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_audio_manifest(path: Path, track_ids: list[str], *, split: str = "development") -> None:
    _write_json(
        path,
        {
            "schemaVersion": INPUT_MANIFEST_SCHEMA,
            "split": split,
            "tracks": [{"id": track_id, "split": split, "audioPath": f"{track_id}.wav"} for track_id in track_ids],
        },
    )


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return float(ordered[middle]) if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def _bars(spec: dict[str, Any]) -> list[int]:
    candidates = spec["beats"][:: spec["beatsPerBar"]]
    if len(candidates) > 1:
        typical = _median([right - left for left, right in zip(candidates, candidates[1:])])
        if spec["durationMs"] - candidates[-1] < typical * 0.4:
            candidates = candidates[:-1]
    return candidates


def _runtime_output(
    contract: dict[str, Any],
    audio_sha256: str,
    spec: dict[str, Any],
    *,
    beat_output: bool,
) -> dict[str, Any]:
    implementation = contract["implementation"]
    runtime = contract["runtime"]
    duration_ms = spec["durationMs"]
    decoded_rate = 44_100
    decoded_count = duration_ms * decoded_rate // 1000
    common = {
        "schemaVersion": RUNNER_OUTPUT_SCHEMA if beat_output else PARENT_RUNNER_SCHEMA,
        "sourceId": SOURCE_ID if beat_output else PARENT_SOURCE_ID,
        "browserExecutableSha256": runtime["browserExecutableSha256"],
        "clientSha256": implementation["clientSha256"],
        "nodeExecutableSha256": runtime["nodeExecutableSha256"],
        "runnerSha256": implementation["beatRunnerSha256"] if beat_output else implementation["runnerSha256"],
        "workerSha256": implementation["workerSha256"],
        "nodeVersion": runtime["nodeVersion"],
        "browserProduct": f"Chrome/{runtime['browserVersion']}",
        "browserRevision": "fixture-revision",
        "browserProtocolVersion": "1.3",
        "browserJavaScriptVersion": "fixture-v8",
        "browserLaunchContractSha256": runtime["browserLaunchContractSha256"],
        "networkRequestCount": 0,
        "sourceAudioSha256": audio_sha256,
        "decodedPcmSha256": hashlib.sha256(f"decoded:{audio_sha256}".encode()).hexdigest(),
        "decodedPcmSampleCount": decoded_count,
        "decodedSampleRateHz": decoded_rate,
        "decodedChannelCount": 2,
        "decodedDurationSeconds": decoded_count / decoded_rate,
        "canonicalDurationMilliseconds": duration_ms,
        "analyzerPcmSha256": hashlib.sha256(f"analyzer:{audio_sha256}".encode()).hexdigest(),
        "analyzerPcmSampleCount": math.floor(decoded_count / 4),
        "analyzerSampleRateHz": 11_025,
        "float32ByteOrder": "little-endian",
        "secureContext": False,
        "navigatorUserAgent": f"Mozilla/5.0 Chrome/{runtime['browserVersion']} Safari/537.36",
        "navigatorPlatform": "fixture-platform",
        "analysisVersion": 2,
        "meter": spec["meter"],
        "beatsPerBar": spec["beatsPerBar"],
        "tempo": spec.get("tempo", 120),
    }
    if beat_output:
        return {
            **common,
            "beatTimesMs": spec["beats"],
            "barStartsMs": _bars(spec),
            "tempoConfidence": spec.get("tempoConfidence", 0.0),
            "meterConfidence": spec.get("meterConfidence", 1.0),
        }
    return {
        **common,
        "beatTimesSeconds": [value / 1000 for value in spec["beats"]],
        "barStartsSeconds": [value / 1000 for value in _bars(spec)],
    }


def _attest_parent(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(manifest)
    analyzer_sha = result["analyzerContract"]["contractSha256"]
    replacements: dict[str, tuple[str, str, str]] = {}
    for track in result["tracks"]:
        old_name = track["timingFile"]
        if old_name not in replacements:
            timing = json.loads((root / old_name).read_text(encoding="utf-8"))
            provenance = timing["timingProvenance"]["barStartsSeconds"]
            provenance.update(
                {
                    "sourceClass": "runtime",
                    "sourceId": PARENT_SOURCE_ID,
                    "sourceContractSha256": analyzer_sha,
                    "deployable": True,
                    "referenceFree": True,
                }
            )
            timing["contractSha256"] = canonical_sha256(
                {key: value for key, value in timing.items() if key != "contractSha256"}
            )
            timing_sha = canonical_sha256(timing)
            new_name = f"timing-{timing_sha}.json"
            _write_json(root / new_name, timing)
            replacements[old_name] = (new_name, timing_sha, timing["contractSha256"])
        new_name, timing_sha, timing_contract = replacements[old_name]
        track.update(
            {
                "selectorUseAllowed": True,
                "timingFile": new_name,
                "timingSha256": timing_sha,
                "timingContractSha256": timing_contract,
                "timingSourceContractSha256": analyzer_sha,
            }
        )
        track["trackArtifactSha256"] = canonical_sha256(
            {key: value for key, value in track.items() if key != "trackArtifactSha256"}
        )
    for old_name, (new_name, _sha, _contract) in replacements.items():
        if old_name != new_name:
            (root / old_name).unlink()
    artifacts = {
        track["timingFile"]: {
            "timingFile": track["timingFile"],
            "timingSha256": track["timingSha256"],
            "timingContractSha256": track["timingContractSha256"],
        }
        for track in result["tracks"]
    }
    result["timingArtifacts"] = [artifacts[name] for name in sorted(artifacts)]
    result["runtimeAttested"] = True
    result["selectorUseAllowed"] = True
    result["trackSetSha256"] = canonical_sha256(
        [
            {"trackId": track["trackId"], "trackArtifactSha256": track["trackArtifactSha256"]}
            for track in result["tracks"]
        ]
    )
    result["manifestSha256"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "manifestSha256"}
    )
    _write_json(root / "manifest.json", result)
    assert validate_runtime_bar_grid_manifest(result, artifact_root=root, verify_sources=True) == result
    return result


def _reseal_receipt(receipt: dict[str, Any]) -> None:
    for track in receipt["tracks"]:
        track["trackReceiptSha256"] = canonical_sha256(
            {key: value for key, value in track.items() if key != "trackReceiptSha256"}
        )
    receipt["trackSetSha256"] = canonical_sha256(
        [
            {"trackId": track["trackId"], "trackReceiptSha256": track["trackReceiptSha256"]}
            for track in receipt["tracks"]
        ]
    )
    receipt["receiptSha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receiptSha256"}
    )


def _attest_receipt(path: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(receipt)
    result["runtimeAttested"] = True
    result["stage1UseAllowed"] = True
    for track in result["tracks"]:
        track["runtimeAttested"] = True
        track["stage1UseAllowed"] = True
    _reseal_receipt(result)
    _write_json(path, result)
    return result


def _fixture(
    tmp_path: Path,
    specs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    specs = specs or {
        "alpha": {
            "durationMs": 6000,
            "beats": list(range(250, 6000, 500)),
            "meter": "4/4",
            "beatsPerBar": 4,
        }
    }
    source_root = tmp_path / "source"
    parent_root = tmp_path / "parent"
    output_root = tmp_path / "published"
    source_root.mkdir()
    output_root.mkdir()
    for track_id in specs:
        (source_root / f"{track_id}.wav").write_bytes(f"audio:{track_id}".encode())
    manifest_path = source_root / "audio-manifest.json"
    _write_audio_manifest(manifest_path, sorted(specs))

    def parent_provider(
        audio_path: Path,
        audio_sha256: str,
        contract: dict[str, Any],
        _timeout: float,
    ) -> dict[str, Any]:
        return _runtime_output(contract, audio_sha256, specs[audio_path.stem], beat_output=False)

    parent = _generate_offline_proxy_bar_grids_for_tests(
        [manifest_path],
        parent_root,
        provider=parent_provider,
        timeout_seconds=17,
    )
    parent = _attest_parent(parent_root, parent)

    def beat_provider(
        audio_path: Path,
        audio_sha256: str,
        contract: dict[str, Any],
        _timeout: float,
    ) -> dict[str, Any]:
        return _runtime_output(contract, audio_sha256, specs[audio_path.stem], beat_output=True)

    return {
        "specs": specs,
        "sourceRoot": source_root,
        "manifestPath": manifest_path,
        "parentRoot": parent_root,
        "parent": parent,
        "outputRoot": output_root,
        "provider": beat_provider,
    }


def _generate(fixture: dict[str, Any], name: str = "receipt.json", provider=None) -> tuple[dict[str, Any], Path]:
    output = fixture["outputRoot"] / name
    receipt = _generate_offline_proxy_beat_grid_receipt_for_tests(
        [fixture["manifestPath"]],
        fixture["parentRoot"] / "manifest.json",
        fixture["parentRoot"],
        output,
        provider=provider or fixture["provider"],
        timeout_seconds=17,
    )
    return receipt, output


def test_public_api_is_noninjectable_and_schema_bumped() -> None:
    assert tuple(inspect.signature(generate_runtime_beat_grid_receipt).parameters) == (
        "manifest_paths",
        "parent_runtime_manifest_path",
        "parent_runtime_root",
        "output_path",
        "timeout_seconds",
    )
    assert RUNNER_OUTPUT_SCHEMA.endswith("_v2")
    assert OUTPUT_RECEIPT_SCHEMA.endswith("_v1")
    assert ANALYZER_CONTRACT_SCHEMA.endswith("_v1")
    assert PLAYER_REPLAY_CONTRACT_SCHEMA.endswith("_v1")


def test_additive_harness_preserves_integer_worker_fields_and_base_runner_bytes() -> None:
    before = BASE_RUNNER.read_bytes()
    source = _materialized_runner_source()
    assert "beatTimesMs:" in source
    assert "barStartsMs:" in source
    assert "tempoConfidence:" in source
    assert "meterConfidence:" in source
    assert "beatTimesSeconds:" not in source
    assert "barStartsSeconds:" not in source
    assert "/ 1000" not in source[source.index("beatTimesMs:") : source.index("meterConfidence:")]
    assert BASE_RUNNER.read_bytes() == before


def test_parent_decimal_seconds_recover_every_sampled_integer_millisecond_exactly() -> None:
    assert _exact_milliseconds_from_seconds(1.001, "fixture") == 1001
    with pytest.raises(ValueError, match="exact integer-millisecond"):
        _exact_milliseconds_from_seconds(1.0005, "fixture")
    for milliseconds in range(0, 20_000):
        assert _exact_milliseconds_from_seconds(milliseconds / 1000, "sampled parent boundary") == milliseconds


def test_contract_binds_parent_runner_generator_and_actual_player_resources(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    analyzer = beat_analyzer_contract(fixture["parent"])
    player = player_replay_contract()
    implementation = analyzer["implementation"]
    assert implementation["baseRunnerSha256"] == _sha256(BASE_RUNNER)
    assert (
        implementation["parentRunnerSha256"] == fixture["parent"]["analyzerContract"]["implementation"]["runnerSha256"]
    )
    assert implementation["generatorSha256"] == _sha256(GENERATOR)
    assert analyzer["outputAdapter"]["secondsRoundTrip"] is False
    assert analyzer["outputAdapter"]["meterPulseMapping"]["6/8"] == 6
    assert player["browserCacheParityAttested"] is False
    assert player["playerPlaybackUseAllowed"] is False
    loads = {row["resourcePath"]: row for row in player["documentLoads"]}
    assert loads["ui/practice-analysis-client-audio-led-key-v11.js"]["routeVersionTokenMatchesResourceSha256"] is False
    assert player["contractSha256"] == canonical_sha256(
        {key: value for key, value in player.items() if key != "contractSha256"}
    )


def test_archival_contract_validation_rejects_resealed_extra_and_nested_fields(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    player = player_replay_contract()
    player["referencePath"] = "forbidden.json"
    player["contractSha256"] = canonical_sha256(
        {key: value for key, value in player.items() if key != "contractSha256"}
    )
    with pytest.raises(ValueError, match="unsupported schema"):
        _validate_player_contract_claim(player, verify_sources=False)

    analyzer = beat_analyzer_contract(fixture["parent"])
    analyzer["implementation"]["referencePath"] = "forbidden.json"
    analyzer["contractSha256"] = canonical_sha256(
        {key: value for key, value in analyzer.items() if key != "contractSha256"}
    )
    with pytest.raises(ValueError, match="implementation binding"):
        _validate_analyzer_contract_claim(analyzer, fixture["parent"], verify_sources=False)

    analyzer = beat_analyzer_contract(fixture["parent"])
    analyzer["runtime"]["referencePath"] = "forbidden.json"
    analyzer["contractSha256"] = canonical_sha256(
        {key: value for key, value in analyzer.items() if key != "contractSha256"}
    )
    with pytest.raises(ValueError, match="runtime policy"):
        _validate_analyzer_contract_claim(analyzer, fixture["parent"], verify_sources=False)


@pytest.mark.parametrize("split", ["calibration", "test", "heldout", "confirmation", "training"])
def test_protected_split_fails_before_parent_output_sources_or_audio(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    split: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    manifest = source / "protected.json"
    _write_audio_manifest(manifest, ["protected"], split=split)
    calls: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        calls.append("forbidden")
        raise AssertionError("later input must not be inspected")

    monkeypatch.setattr("steel_guitar_rag.chord_reader.runtime_beat_grid._preflight_output_target", forbidden)
    monkeypatch.setattr("steel_guitar_rag.chord_reader.runtime_beat_grid._load_parent", forbidden)
    with pytest.raises(ValueError, match="development-only"):
        _generate_offline_proxy_beat_grid_receipt_for_tests(
            [manifest],
            tmp_path / "parent" / "manifest.json",
            tmp_path / "parent",
            tmp_path / "published" / "receipt.json",
            provider=forbidden,
        )
    assert calls == []


def test_basic_holistic_receipt_is_canonical_self_hashed_and_offline_blocked(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt, path = _generate(fixture)
    assert receipt["runtimeAttested"] is False
    assert receipt["stage1UseAllowed"] is False
    assert receipt["selectorUseAllowed"] is False
    assert receipt["playerPlaybackUseAllowed"] is False
    assert receipt["confidenceUse"] == CONFIDENCE_USE
    assert receipt["receiptTotals"] == {
        "trackCount": 1,
        "beatCellCount": 12,
        "sourceDurationMilliseconds": 6000,
        "coveredDurationMilliseconds": 5750,
        "excludedPrefixDurationMilliseconds": 250,
    }
    track = receipt["tracks"][0]
    assert track["beatTimesMs"] == list(range(250, 6000, 500))
    assert all(isinstance(value, int) for value in track["beatTimesMs"])
    assert track["beatCells"][0]["startMs"] == 250
    assert track["beatCells"][-1]["endMs"] == 6000
    assert (
        path.read_text(encoding="utf-8")
        == json.dumps(receipt, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ValueError, match="not attested for Stage-1 use"):
        validate_runtime_beat_grid_receipt(
            receipt,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=fixture["parentRoot"],
            receipt_path=path,
        )


def test_attested_receipt_standalone_validator_rederives_every_binding(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt, path = _generate(fixture)
    attested = _attest_receipt(path, receipt)
    assert (
        validate_runtime_beat_grid_receipt(
            attested,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=fixture["parentRoot"],
            receipt_path=path,
        )
        == attested
    )


def test_six_eight_is_six_pulses_with_one_cell_per_explicit_beat(tmp_path: Path) -> None:
    fixture = _fixture(
        tmp_path,
        {
            "compound": {
                "durationMs": 6000,
                "beats": list(range(100, 6000, 400)),
                "meter": "6/8",
                "beatsPerBar": 6,
            }
        },
    )
    receipt, _path = _generate(fixture)
    track = receipt["tracks"][0]
    assert track["beatsPerBar"] == METER_PULSES["6/8"] == 6
    assert [cell["pulseNumber"] for cell in track["beatCells"][:7]] == [1, 2, 3, 4, 5, 6, 1]
    assert track["barStartsMs"] == track["beatTimesMs"][::6]


def test_exact_worker_terminal_downbeat_pop_and_tail_are_certified(tmp_path: Path) -> None:
    spec = {
        "durationMs": 5000,
        "beats": list(range(100, 5000, 400)),
        "meter": "4/4",
        "beatsPerBar": 4,
    }
    fixture = _fixture(tmp_path, {"tail": spec})
    receipt, _path = _generate(fixture)
    track = receipt["tracks"][0]
    assert spec["beats"][::4] == [100, 1700, 3300, 4900]
    assert track["barStartsMs"] == [100, 1700, 3300]
    assert track["terminalDownbeatCandidateSuppressed"] is True
    assert track["tailIncludedMilliseconds"] == 100
    assert track["beatCells"][-1]["startMs"] == 4900
    assert track["beatCells"][-1]["endMs"] == 5000


def test_wrong_tail_topology_fails_before_publication(tmp_path: Path) -> None:
    spec = {
        "durationMs": 5000,
        "beats": list(range(100, 5000, 400)),
        "meter": "4/4",
        "beatsPerBar": 4,
    }
    fixture = _fixture(tmp_path, {"tail": spec})

    def wrong_provider(path: Path, audio_sha: str, contract: dict[str, Any], _timeout: float) -> dict[str, Any]:
        raw = _runtime_output(contract, audio_sha, spec, beat_output=True)
        raw["barStartsMs"] = spec["beats"][::4]
        return raw

    output = fixture["outputRoot"] / "wrong.json"
    with pytest.raises(ValueError, match="tail-pop rule"):
        _generate(fixture, "wrong.json", provider=wrong_provider)
    assert not output.exists()


@pytest.mark.parametrize(
    "mutation,message",
    [
        ({"beatsPerBar": 2}, "meter-to-pulse"),
        ({"meter": "12/8"}, "unsupported meter"),
        ({"networkRequestCount": 1}, "secondary network"),
        ({"decodedPcmSampleCount": 1}, "audio/PCM/duration"),
        ({"analysisVersion": 99}, "analysisVersion"),
    ],
)
def test_runner_meter_network_and_parent_identity_tamper_fail_closed(
    tmp_path: Path,
    mutation: dict[str, Any],
    message: str,
) -> None:
    fixture = _fixture(tmp_path)

    def provider(path: Path, audio_sha: str, contract: dict[str, Any], _timeout: float) -> dict[str, Any]:
        raw = _runtime_output(contract, audio_sha, fixture["specs"][path.stem], beat_output=True)
        raw.update(mutation)
        return raw

    with pytest.raises(ValueError, match=message):
        _generate(fixture, "tampered.json", provider=provider)
    assert not (fixture["outputRoot"] / "tampered.json").exists()


def test_low_confidence_is_disclosed_without_filtering(tmp_path: Path) -> None:
    spec = {
        "durationMs": 6000,
        "beats": list(range(250, 6000, 500)),
        "meter": "4/4",
        "beatsPerBar": 4,
        "tempoConfidence": 0.0,
        "meterConfidence": 0.0,
    }
    fixture = _fixture(tmp_path, {"low": spec})
    receipt, _path = _generate(fixture)
    track = receipt["tracks"][0]
    assert track["tempoConfidence"] == 0
    assert track["meterConfidence"] == 0
    assert track["beatCount"] == len(spec["beats"])
    assert track["confidenceUse"] == CONFIDENCE_USE


def test_reordered_tracks_and_resealed_invalid_topology_are_rejected(tmp_path: Path) -> None:
    specs = {
        name: {
            "durationMs": 6000,
            "beats": list(range(250, 6000, 500)),
            "meter": "4/4",
            "beatsPerBar": 4,
        }
        for name in ("alpha", "beta")
    }
    fixture = _fixture(tmp_path, specs)
    receipt, path = _generate(fixture)
    attested = _attest_receipt(path, receipt)

    reordered = deepcopy(attested)
    reordered["tracks"].reverse()
    _reseal_receipt(reordered)
    with pytest.raises(ValueError, match="sorted parent tracks"):
        validate_runtime_beat_grid_receipt(
            reordered,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=fixture["parentRoot"],
        )

    invalid = deepcopy(attested)
    invalid["tracks"][0]["beatTimesMs"][1] = invalid["tracks"][0]["beatTimesMs"][0]
    _reseal_receipt(invalid)
    with pytest.raises(ValueError, match="topology|positive contiguous|strictly increasing"):
        validate_runtime_beat_grid_receipt(
            invalid,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=fixture["parentRoot"],
        )


def test_unresealed_receipt_hash_tamper_is_rejected_first(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt, path = _generate(fixture)
    attested = _attest_receipt(path, receipt)
    attested["tracks"][0]["tempoConfidence"] = 0.5
    with pytest.raises(ValueError, match="receipt hash is stale"):
        validate_runtime_beat_grid_receipt(
            attested,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=fixture["parentRoot"],
        )


def test_foreign_resealed_parent_mapping_cannot_be_combined_with_real_root(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt, path = _generate(fixture)
    attested = _attest_receipt(path, receipt)
    foreign_parent = deepcopy(fixture["parent"])
    foreign_parent["previousManifestSha256"] = "f" * 64
    foreign_parent["manifestSha256"] = canonical_sha256(
        {key: value for key, value in foreign_parent.items() if key != "manifestSha256"}
    )
    with pytest.raises(ValueError, match="does not equal canonical"):
        validate_runtime_beat_grid_receipt(
            attested,
            parent_runtime_manifest=foreign_parent,
            parent_runtime_root=fixture["parentRoot"],
        )


def test_receipt_and_parent_symlinks_are_rejected_without_resolution_laundering(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt, path = _generate(fixture)
    attested = _attest_receipt(path, receipt)
    receipt_link = fixture["outputRoot"] / "receipt-link.json"
    receipt_link.symlink_to(path)
    with pytest.raises(ValueError, match="symlinked path components"):
        validate_runtime_beat_grid_receipt(
            attested,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=fixture["parentRoot"],
            receipt_path=receipt_link,
        )
    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(fixture["parentRoot"], target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked path components"):
        validate_runtime_beat_grid_receipt(
            attested,
            parent_runtime_manifest=fixture["parent"],
            parent_runtime_root=parent_link,
        )


def test_output_preflight_rejects_parent_source_bad_suffix_and_broken_symlink_before_provider(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    calls: list[Path] = []

    def forbidden(*args: Any) -> dict[str, Any]:
        calls.append(args[0])
        raise AssertionError("provider must not run")

    for output in (
        fixture["parentRoot"] / "inside.json",
        fixture["sourceRoot"] / "inside.json",
        fixture["outputRoot"] / "wrong.txt",
    ):
        with pytest.raises(ValueError, match="disjoint|new .json"):
            _generate_offline_proxy_beat_grid_receipt_for_tests(
                [fixture["manifestPath"]],
                fixture["parentRoot"] / "manifest.json",
                fixture["parentRoot"],
                output,
                provider=forbidden,
            )
    broken = fixture["outputRoot"] / "broken.json"
    broken.symlink_to(fixture["outputRoot"] / "missing.json")
    with pytest.raises(ValueError, match="new path"):
        _generate_offline_proxy_beat_grid_receipt_for_tests(
            [fixture["manifestPath"]],
            fixture["parentRoot"] / "manifest.json",
            fixture["parentRoot"],
            broken,
            provider=forbidden,
        )
    assert calls == []


def test_midbatch_provider_failure_leaves_no_receipt_or_temp_files(tmp_path: Path) -> None:
    specs = {
        name: {
            "durationMs": 6000,
            "beats": list(range(250, 6000, 500)),
            "meter": "4/4",
            "beatsPerBar": 4,
        }
        for name in ("alpha", "beta")
    }
    fixture = _fixture(tmp_path, specs)
    calls = 0

    def provider(path: Path, audio_sha: str, contract: dict[str, Any], timeout: float) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected second-track failure")
        return fixture["provider"](path, audio_sha, contract, timeout)

    with pytest.raises(RuntimeError, match="second-track failure"):
        _generate(fixture, "partial.json", provider=provider)
    assert list(fixture["outputRoot"].iterdir()) == []


@pytest.mark.parametrize(
    "mutation,message",
    [
        ("manifest", "audio manifest changed"),
        ("audio-resolution", "audio resolution changed"),
    ],
)
def test_manifest_and_audio_resolution_are_revalidated_before_publication(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    fixture = _fixture(tmp_path)

    def provider(path: Path, audio_sha: str, contract: dict[str, Any], timeout: float) -> dict[str, Any]:
        raw = fixture["provider"](path, audio_sha, contract, timeout)
        alternate = fixture["sourceRoot"] / "alternate.wav"
        alternate.write_bytes(path.read_bytes())
        if mutation == "manifest":
            manifest = json.loads(fixture["manifestPath"].read_text(encoding="utf-8"))
            manifest["tracks"][0]["audioPath"] = alternate.name
            _write_json(fixture["manifestPath"], manifest)
        else:
            original = fixture["sourceRoot"] / "alpha-original.wav"
            path.rename(original)
            path.symlink_to(alternate)
        return raw

    with pytest.raises(ValueError, match=message):
        _generate(fixture, f"{mutation}.json", provider=provider)
    assert list(fixture["outputRoot"].iterdir()) == []


def test_link_then_raise_rolls_back_only_owned_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    real_link = os.link

    def link_then_raise(*args: Any, **kwargs: Any) -> None:
        real_link(*args, **kwargs)
        raise OSError("injected post-link failure")

    monkeypatch.setattr("steel_guitar_rag.chord_reader.runtime_beat_grid.os.link", link_then_raise)
    with pytest.raises(OSError, match="post-link failure"):
        _generate(fixture, "post-link.json")
    assert list(fixture["outputRoot"].iterdir()) == []


def test_foreign_concurrent_destination_is_never_unlinked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)

    def foreign_then_fail(
        _source: str,
        destination: str,
        *,
        src_dir_fd: int,
        dst_dir_fd: int,
        follow_symlinks: bool,
    ) -> None:
        assert src_dir_fd == dst_dir_fd and follow_symlinks is False
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=dst_dir_fd)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(b"foreign")
        raise FileExistsError("injected concurrent destination")

    monkeypatch.setattr("steel_guitar_rag.chord_reader.runtime_beat_grid.os.link", foreign_then_fail)
    output = fixture["outputRoot"] / "foreign.json"
    with pytest.raises(FileExistsError, match="concurrent destination"):
        _generate(fixture, output.name)
    assert output.read_bytes() == b"foreign"
    assert [path.name for path in fixture["outputRoot"].iterdir()] == ["foreign.json"]


def test_post_link_directory_fsync_failure_rolls_back_owned_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    real_fsync = os.fsync
    calls = 0

    def fail_second(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected directory fsync failure")
        real_fsync(descriptor)

    monkeypatch.setattr("steel_guitar_rag.chord_reader.runtime_beat_grid.os.fsync", fail_second)
    with pytest.raises(OSError, match="directory fsync failure"):
        _generate(fixture, "fsync.json")
    assert list(fixture["outputRoot"].iterdir()) == []


def test_parent_directory_swap_after_link_rolls_back_owned_inode_through_retained_fd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    real_fsync = os.fsync
    calls = 0
    moved = tmp_path / "published-moved"

    def swap_on_directory_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            fixture["outputRoot"].rename(moved)
            fixture["outputRoot"].mkdir()
        real_fsync(descriptor)

    monkeypatch.setattr(
        "steel_guitar_rag.chord_reader.runtime_beat_grid.os.fsync",
        swap_on_directory_fsync,
    )
    with pytest.raises(RuntimeError, match="output parent changed"):
        _generate(fixture, "swapped.json")
    assert list(fixture["outputRoot"].iterdir()) == []
    assert list(moved.iterdir()) == []


def _write_click_track(path: Path, *, duration_seconds: int = 12) -> None:
    sample_rate = 44_100
    samples: list[int] = []
    for index in range(sample_rate * duration_seconds):
        time_seconds = index / sample_rate
        beat_index = int(time_seconds / 0.5)
        phase = time_seconds - beat_index * 0.5
        amplitude = 0.0
        if phase < 0.035:
            strength = 0.9 if beat_index % 4 == 0 else 0.55
            amplitude = strength * math.exp(-phase * 90) * math.sin(2 * math.pi * 880 * phase)
        samples.append(max(-32_767, min(32_767, round(amplitude * 32_767))))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"".join(struct.pack("<hh", sample, sample // 2) for sample in samples))


@pytest.mark.skipif(
    not Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").is_file() or shutil.which("node") is None,
    reason="Pinned Chrome and Node are required.",
)
def test_real_browser_single_wav_reconciles_parent_and_integer_beat_receipt(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    parent_root = tmp_path / "parent"
    published_root = tmp_path / "published"
    source_root.mkdir()
    published_root.mkdir()
    audio = source_root / "click.wav"
    _write_click_track(audio)
    manifest_path = source_root / "audio-manifest.json"
    _write_audio_manifest(manifest_path, ["click"])

    parent = generate_runtime_bar_grids(
        [manifest_path],
        parent_root,
        timeout_seconds=60,
    )
    receipt_path = published_root / "receipt.json"
    receipt = generate_runtime_beat_grid_receipt(
        [manifest_path],
        parent_root / "manifest.json",
        parent_root,
        receipt_path,
        timeout_seconds=60,
    )
    assert (
        validate_runtime_beat_grid_receipt(
            receipt,
            parent_runtime_manifest=parent,
            parent_runtime_root=parent_root,
            receipt_path=receipt_path,
        )
        == receipt
    )
    track = receipt["tracks"][0]
    parent_track = parent["tracks"][0]
    assert track["audioBinding"] == parent_track["audioBinding"]
    assert track["runtimeIdentity"] == parent_track["runtimeIdentity"]
    assert all(isinstance(value, int) for value in track["beatTimesMs"])
    assert all(isinstance(value, int) for value in track["barStartsMs"])
    assert 0 <= track["tempoConfidence"] <= 1
    assert 0 <= track["meterConfidence"] <= 1
