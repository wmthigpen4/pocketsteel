from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import wave

import pytest

from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.runtime_bar_grid import (
    ANALYZER_CONTRACT_SCHEMA,
    EXPLICIT_BAR_GRID_SCHEMA,
    INPUT_MANIFEST_SCHEMA,
    OUTPUT_MANIFEST_SCHEMA,
    RUNNER_OUTPUT_SCHEMA,
    SOURCE_ID,
    _generate_offline_proxy_bar_grids_for_tests,
    _prepare_output_directory,
    _validate_prior_manifest,
    _validate_runner_output,
    analyzer_contract,
    generate_runtime_bar_grids,
    validate_runtime_bar_grid_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER = REPO_ROOT / "ui" / "practice-analysis-worker.js"
CLIENT = REPO_ROOT / "ui" / "practice-analysis-client.js"
RUNNER = REPO_ROOT / "scripts" / "chord_runtime_bar_analyzer.js"
GENERATOR = REPO_ROOT / "steel_guitar_rag" / "chord_reader" / "runtime_bar_grid.py"
BROWSER = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _write_manifest(
    path: Path,
    tracks: list[dict[str, object]],
    *,
    split: str = "development",
) -> None:
    path.write_text(
        json.dumps(
            {
                "schemaVersion": INPUT_MANIFEST_SCHEMA,
                "split": split,
                "tracks": tracks,
            }
        ),
        encoding="utf-8",
    )


def _write_canonical_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _track(track_id: str, audio_path: str, *, split: str = "development") -> dict[str, object]:
    return {"id": track_id, "split": split, "audioPath": audio_path}


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fake_output(
    contract: dict[str, object],
    source_audio_sha256: str,
    *,
    duration_seconds: float = 4.0,
    first_bar_seconds: float = 0.25,
) -> dict[str, object]:
    implementation = contract["implementation"]
    runtime = contract["runtime"]
    assert isinstance(implementation, dict)
    assert isinstance(runtime, dict)
    decoded_rate = 44_100
    decoded_count = round(duration_seconds * decoded_rate)
    analyzer_count = math.floor(decoded_count / 4)
    beat_times = [first_bar_seconds + index * 0.5 for index in range(8)]
    beat_times = [value for value in beat_times if value < duration_seconds]
    bar_starts = beat_times[::4]
    return {
        "schemaVersion": RUNNER_OUTPUT_SCHEMA,
        "sourceId": SOURCE_ID,
        "browserExecutableSha256": runtime["browserExecutableSha256"],
        "clientSha256": implementation["clientSha256"],
        "nodeExecutableSha256": runtime["nodeExecutableSha256"],
        "runnerSha256": implementation["runnerSha256"],
        "workerSha256": implementation["workerSha256"],
        "nodeVersion": runtime["nodeVersion"],
        "browserProduct": f"Chrome/{runtime['browserVersion']}",
        "browserRevision": "fixture-revision",
        "browserProtocolVersion": "1.3",
        "browserJavaScriptVersion": "fixture-v8",
        "browserLaunchContractSha256": runtime["browserLaunchContractSha256"],
        "networkRequestCount": 0,
        "sourceAudioSha256": source_audio_sha256,
        "decodedPcmSha256": "a" * 64,
        "decodedPcmSampleCount": decoded_count,
        "decodedSampleRateHz": decoded_rate,
        "decodedChannelCount": 2,
        "decodedDurationSeconds": decoded_count / decoded_rate,
        "canonicalDurationMilliseconds": round(duration_seconds * 1000),
        "analyzerPcmSha256": "b" * 64,
        "analyzerPcmSampleCount": analyzer_count,
        "analyzerSampleRateHz": 11_025,
        "float32ByteOrder": "little-endian",
        "secureContext": False,
        "navigatorUserAgent": f"Mozilla/5.0 Chrome/{runtime['browserVersion']} Safari/537.36",
        "navigatorPlatform": "fixture-platform",
        "analysisVersion": 2,
        "beatTimesSeconds": beat_times,
        "barStartsSeconds": bar_starts,
        "meter": "4/4",
        "beatsPerBar": 4,
        "tempo": 120.0,
    }


def _fake_provider(
    audio_path: Path,
    audio_sha256: str,
    contract: dict[str, object],
    timeout: float,
) -> dict[str, object]:
    assert audio_path.is_file()
    assert timeout == 17.0
    duration = 4.0 if "first" in audio_path.name else 5.0
    return _fake_output(contract, audio_sha256, duration_seconds=duration)


def _offline_generate(
    manifests: list[Path],
    output: Path,
    *,
    replace: bool = False,
    provider=_fake_provider,
) -> dict[str, object]:
    return _generate_offline_proxy_bar_grids_for_tests(
        manifests,
        output,
        provider=provider,
        replace_verified_set=replace,
        timeout_seconds=17,
    )


def _replace_single_active_timing(
    output: Path,
    manifest: dict[str, object],
    timing: dict[str, object],
) -> dict[str, object]:
    tracks = manifest["tracks"]
    assert isinstance(tracks, list) and len(tracks) == 1
    track = tracks[0]
    assert isinstance(track, dict)
    prior_filename = track["timingFile"]
    assert isinstance(prior_filename, str)

    timing_payload = {key: value for key, value in timing.items() if key != "contractSha256"}
    timing["contractSha256"] = canonical_sha256(timing_payload)
    timing_sha256 = canonical_sha256(timing)
    timing_filename = f"timing-{timing_sha256}.json"
    if timing_filename != prior_filename:
        (output / prior_filename).unlink()
    _write_canonical_json(output / timing_filename, timing)

    track["timingFile"] = timing_filename
    track["timingSha256"] = timing_sha256
    track["timingContractSha256"] = timing["contractSha256"]
    track["trackArtifactSha256"] = canonical_sha256(
        {key: value for key, value in track.items() if key != "trackArtifactSha256"}
    )
    manifest["timingArtifacts"] = [
        {
            "timingFile": timing_filename,
            "timingSha256": timing_sha256,
            "timingContractSha256": timing["contractSha256"],
        }
    ]
    manifest["trackSetSha256"] = canonical_sha256(
        [{"trackId": track["trackId"], "trackArtifactSha256": track["trackArtifactSha256"]}]
    )
    manifest["manifestSha256"] = canonical_sha256(
        {key: value for key, value in manifest.items() if key != "manifestSha256"}
    )
    _write_canonical_json(output / "manifest.json", manifest)
    return manifest


def _attest_single_offline_fixture(
    output: Path,
    manifest: dict[str, object],
) -> dict[str, object]:
    result = deepcopy(manifest)
    tracks = result["tracks"]
    assert isinstance(tracks, list) and len(tracks) == 1
    track = tracks[0]
    assert isinstance(track, dict)
    timing_filename = track["timingFile"]
    assert isinstance(timing_filename, str)
    timing = json.loads((output / timing_filename).read_text(encoding="utf-8"))
    assert isinstance(timing, dict)
    provenance = timing["timingProvenance"]["barStartsSeconds"]
    analyzer = result["analyzerContract"]
    assert isinstance(provenance, dict) and isinstance(analyzer, dict)
    provenance.update(
        {
            "sourceClass": "runtime",
            "sourceId": SOURCE_ID,
            "sourceContractSha256": analyzer["contractSha256"],
            "deployable": True,
            "referenceFree": True,
        }
    )
    result["runtimeAttested"] = True
    result["selectorUseAllowed"] = True
    track["selectorUseAllowed"] = True
    track["timingSourceContractSha256"] = analyzer["contractSha256"]
    return _replace_single_active_timing(output, result, timing)


def test_public_api_has_no_runner_source_or_deployability_injection() -> None:
    assert tuple(inspect.signature(analyzer_contract).parameters) == ()
    assert tuple(inspect.signature(generate_runtime_bar_grids).parameters) == (
        "manifest_paths",
        "output_dir",
        "replace_verified_set",
        "timeout_seconds",
    )
    assert "runner" not in generate_runtime_bar_grids.__annotations__
    assert "worker_path" not in inspect.signature(generate_runtime_bar_grids).parameters
    assert tuple(inspect.signature(validate_runtime_bar_grid_manifest).parameters) == (
        "manifest",
        "artifact_root",
        "verify_sources",
    )


def test_contract_binds_exact_browser_client_worker_runner_generator_and_node() -> None:
    contract = analyzer_contract()
    implementation = contract["implementation"]
    runtime = contract["runtime"]
    assert contract["schemaVersion"] == ANALYZER_CONTRACT_SCHEMA
    assert contract["sourceId"] == SOURCE_ID
    assert implementation["workerSha256"] == _file_sha256(WORKER)
    assert implementation["clientSha256"] == _file_sha256(CLIENT)
    assert implementation["runnerSha256"] == _file_sha256(RUNNER)
    assert implementation["generatorSha256"] == _file_sha256(GENERATOR)
    assert runtime["browserExecutableSha256"] == _file_sha256(BROWSER)
    node = Path(shutil.which("node") or "").resolve()
    assert runtime["nodeExecutableSha256"] == _file_sha256(node)
    assert runtime["browserLaunchContractSha256"] == canonical_sha256(runtime["browserLaunchArguments"])
    payload = {key: value for key, value in contract.items() if key != "contractSha256"}
    assert contract["contractSha256"] == canonical_sha256(payload)
    assert contract["decode"] == {
        "decoder": "target-google-chrome-webaudio-decodeAudioData",
        "channelReduction": "arithmetic-mean-all-AudioBuffer-channels",
        "pcmEncoding": "Float32Array-little-endian",
        "canonicalDuration": "Math.round(AudioBuffer.duration*1000)/1000",
        "documentSecurityContext": "about:blank-non-secure-cdp-injected",
        "options": {},
        "hintsAllowed": False,
        "referenceFieldsAllowed": False,
    }
    assert "ffmpeg" not in json.dumps(contract).lower()


def test_runner_source_is_exact_player_webaudio_path_with_network_denial() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "STEEL_RAG_ANALYSIS_CLIENT.decodeAudio" in source
    assert "STEEL_RAG_ANALYSIS_CLIENT.monoSamples" in source
    assert "STEEL_RAG_ANALYSIS_V2.downsample" in source
    assert "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis" in source
    assert "analyzePcm" not in source
    assert "ffmpeg" not in source.lower()
    assert "Network.setBlockedURLs" in source
    assert "connect-src 'none'" in source
    assert "networkRequestCount" in source
    assert "sourceAudioSha256" in source
    assert "decodedPcmSha256" in source
    assert "--host-resolver-rules=MAP * ~NOTFOUND" in source
    assert source.index('cdp.send("Browser.getVersion")') < source.index('"Page.setDocumentContent"')
    assert "await terminateBrowser(browser?.child)" in source
    assert "Chrome stderr tail:" in source
    assert "void terminateBrowser(child).then" in source


@pytest.mark.parametrize("split", ["calibration", "test", "heldout", "confirmation", "training"])
def test_protected_splits_fail_before_source_output_or_audio_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    split: str,
) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("protected", "must-not-open.wav", split=split)], split=split)
    calls: list[str] = []

    def forbidden_contract() -> dict[str, object]:
        calls.append("contract")
        raise AssertionError("source must not be opened")

    def forbidden_output(*_args: object, **_kwargs: object) -> object:
        calls.append("output")
        raise AssertionError("output must not be inspected")

    monkeypatch.setattr(
        "steel_guitar_rag.chord_reader.runtime_bar_grid.analyzer_contract",
        forbidden_contract,
    )
    monkeypatch.setattr(
        "steel_guitar_rag.chord_reader.runtime_bar_grid._prepare_output_directory",
        forbidden_output,
    )
    with pytest.raises(ValueError, match="development-only"):
        _offline_generate([manifest], tmp_path / "output")
    assert calls == []
    assert not (tmp_path / "output").exists()


def test_later_protected_manifest_blocks_earlier_development_audio(tmp_path: Path) -> None:
    development = tmp_path / "development.json"
    protected = tmp_path / "protected.json"
    _write_manifest(development, [_track("dev", "must-not-open.wav")])
    _write_manifest(protected, [_track("held", "must-not-open.wav")], split="heldout")
    with pytest.raises(ValueError, match="development-only"):
        _offline_generate([development, protected], tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("referencePath", "protected.json"),
        ("chordLabels", ["C", "F"]),
        ("barStartsSeconds", [0.0]),
        ("tempo", 120),
        ("meter", "4/4"),
        ("playlist", ["other.mp3"]),
    ],
)
def test_reference_label_playlist_and_hint_fields_fail_before_access(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    manifest = tmp_path / "manifest.json"
    track = _track("dev", "must-not-open.wav")
    track[field] = value
    _write_manifest(manifest, [track])
    with pytest.raises(ValueError, match="references, labels, annotations, playlists"):
        _offline_generate([manifest], tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("audio_name", ["playlist.m3u", "remote.url", "audio.flac", "no-suffix"])
def test_audio_allowlist_rejects_playlist_and_unsupported_sources_before_path_access(
    tmp_path: Path,
    audio_name: str,
) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("dev", audio_name)])
    with pytest.raises(ValueError, match="self-contained WAV, MP3, M4A, or AAC allowlist"):
        _offline_generate([manifest], tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_private_fixture_generation_is_nonruntime_nondeployable_and_selector_blocked(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"synthetic fixture bytes")
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("dev", audio.name)])
    output = tmp_path / "output"
    result = _offline_generate([manifest], output)

    assert result["schemaVersion"] == OUTPUT_MANIFEST_SCHEMA
    assert result["runtimeAttested"] is False
    assert result["selectorUseAllowed"] is False
    entry = result["tracks"][0]
    assert entry["selectorUseAllowed"] is False
    timing_path = output / entry["timingFile"]
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    assert timing["schemaVersion"] == EXPLICIT_BAR_GRID_SCHEMA
    provenance = timing["timingProvenance"]["barStartsSeconds"]
    assert provenance["sourceClass"] == "offline-proxy"
    assert provenance["deployable"] is False
    assert provenance["referenceFree"] is True
    assert provenance["sourceId"] != SOURCE_ID
    assert entry["timingFile"] == f"timing-{canonical_sha256(timing)}.json"
    assert entry["timingSha256"] == canonical_sha256(timing)
    assert entry["audioSha256"] == _file_sha256(audio)
    assert entry["audioBinding"]["sourceAudioSha256"] == _file_sha256(audio)
    assert entry["audioBindingSha256"] == canonical_sha256(entry["audioBinding"])
    assert result["timingArtifacts"] == [
        {
            "timingFile": entry["timingFile"],
            "timingSha256": entry["timingSha256"],
            "timingContractSha256": entry["timingContractSha256"],
        }
    ]
    payload = {key: value for key, value in result.items() if key != "manifestSha256"}
    assert result["manifestSha256"] == canonical_sha256(payload)
    assert json.loads((output / "manifest.json").read_text(encoding="utf-8")) == result
    with pytest.raises(ValueError, match="not attested for selector use"):
        validate_runtime_bar_grid_manifest(result, artifact_root=output, verify_sources=True)


def test_default_output_requires_new_or_empty_and_rejects_unrelated_before_analysis(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"audio")
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("dev", audio.name)])
    output = tmp_path / "output"
    output.mkdir()
    unrelated = output / "keep-me.txt"
    unrelated.write_text("untouched", encoding="utf-8")
    calls: list[Path] = []

    def forbidden_provider(*args: object) -> dict[str, object]:
        calls.append(args[0])
        raise AssertionError("analysis must not start")

    with pytest.raises(ValueError, match="new or empty"):
        _offline_generate([manifest], output, provider=forbidden_provider)
    assert calls == []
    assert unrelated.read_text(encoding="utf-8") == "untouched"

    with pytest.raises(ValueError, match="prior output manifest"):
        _offline_generate([manifest], output, replace=True, provider=forbidden_provider)
    assert calls == []
    assert unrelated.read_text(encoding="utf-8") == "untouched"


def test_replacement_requires_a_committed_prior_manifest_before_analysis(tmp_path: Path) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"audio")
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("dev", audio.name)])
    committed_output = tmp_path / "committed-output"
    committed = _offline_generate([manifest], committed_output)
    orphan_output = tmp_path / "orphan-output"
    orphan_output.mkdir()
    shutil.copy2(
        committed_output / committed["tracks"][0]["timingFile"],
        orphan_output / committed["tracks"][0]["timingFile"],
    )
    calls: list[Path] = []

    def forbidden_provider(*args: object) -> dict[str, object]:
        calls.append(args[0])
        raise AssertionError("analysis must not start")

    with pytest.raises(ValueError, match="prior output manifest"):
        _offline_generate(
            [manifest],
            orphan_output,
            replace=True,
            provider=forbidden_provider,
        )
    assert calls == []


def test_verified_set_replacement_requires_the_exact_active_timing_inventory(
    tmp_path: Path,
) -> None:
    first_audio = tmp_path / "first.wav"
    second_audio = tmp_path / "second.wav"
    first_audio.write_bytes(b"first")
    second_audio.write_bytes(b"second")
    first_manifest = tmp_path / "first.json"
    second_manifest = tmp_path / "second.json"
    _write_manifest(first_manifest, [_track("first", first_audio.name)])
    _write_manifest(second_manifest, [_track("second", second_audio.name)])
    output = tmp_path / "output"
    first = _offline_generate([first_manifest], output)
    first_manifest_bytes = (output / "manifest.json").read_bytes()

    with pytest.raises(ValueError, match="new or empty"):
        _offline_generate([second_manifest], output)
    with pytest.raises(ValueError, match="exact same active timing artifact inventory"):
        _offline_generate([second_manifest], output, replace=True)
    assert (output / "manifest.json").read_bytes() == first_manifest_bytes
    assert {path.name for path in output.iterdir()} == {
        "manifest.json",
        first["tracks"][0]["timingFile"],
    }

    replacement = _offline_generate([first_manifest], output, replace=True)
    assert replacement["previousManifestSha256"] == first["manifestSha256"]
    assert replacement["timingArtifacts"] == [
        {
            "timingFile": replacement["tracks"][0]["timingFile"],
            "timingSha256": replacement["tracks"][0]["timingSha256"],
            "timingContractSha256": replacement["tracks"][0]["timingContractSha256"],
        }
    ]
    assert (output / first["tracks"][0]["timingFile"]).is_file()
    assert _validate_prior_manifest(output / "manifest.json")["manifestSha256"] == replacement["manifestSha256"]


def test_fault_before_same_inventory_manifest_commit_preserves_old_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_audio = tmp_path / "first.wav"
    first_audio.write_bytes(b"first")
    first_manifest = tmp_path / "first.json"
    _write_manifest(first_manifest, [_track("first", first_audio.name)])
    output = tmp_path / "output"
    first = _offline_generate([first_manifest], output)
    old_manifest_bytes = (output / "manifest.json").read_bytes()

    from steel_guitar_rag.chord_reader import runtime_bar_grid as module

    real_write = module._atomic_write_json

    def fail_manifest(path: Path, value: dict[str, object]) -> None:
        if path.name == "manifest.json":
            raise RuntimeError("injected manifest commit failure")
        real_write(path, value)

    monkeypatch.setattr(module, "_atomic_write_json", fail_manifest)
    with pytest.raises(RuntimeError, match="injected manifest commit failure"):
        _offline_generate([first_manifest], output, replace=True)
    assert (output / "manifest.json").read_bytes() == old_manifest_bytes
    assert _validate_prior_manifest(output / "manifest.json")["manifestSha256"] == first["manifestSha256"]
    state = _prepare_output_directory(output, replace_verified_set=True)
    assert state.previous_manifest_sha256 == first["manifestSha256"]
    assert len(state.verified_artifacts) == 1


def test_orphan_annotation_timing_fails_before_replacement_analysis(tmp_path: Path) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"first")
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, [_track("first", audio.name)])
    output = tmp_path / "output"
    committed = _offline_generate([manifest_path], output)
    active_filename = committed["tracks"][0]["timingFile"]
    active = json.loads((output / active_filename).read_text(encoding="utf-8"))
    orphan = deepcopy(active)
    provenance = orphan["timingProvenance"]["barStartsSeconds"]
    provenance.update(
        {
            "sourceClass": "annotation",
            "sourceId": "adversarial-annotation-grid",
            "deployable": False,
            "referenceFree": False,
        }
    )
    orphan_payload = {key: value for key, value in orphan.items() if key != "contractSha256"}
    orphan["contractSha256"] = canonical_sha256(orphan_payload)
    orphan_filename = f"timing-{canonical_sha256(orphan)}.json"
    _write_canonical_json(output / orphan_filename, orphan)
    calls: list[Path] = []

    def forbidden_provider(*args: object) -> dict[str, object]:
        calls.append(args[0])
        raise AssertionError("analysis must not start")

    with pytest.raises(ValueError, match="complete active timing artifact inventory"):
        _offline_generate(
            [manifest_path],
            output,
            replace=True,
            provider=forbidden_provider,
        )
    assert calls == []
    assert _validate_prior_manifest(output / "manifest.json")["manifestSha256"] == committed["manifestSha256"]


def test_declared_active_annotation_timing_fails_deep_validation_before_analysis(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"first")
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, [_track("first", audio.name)])
    output = tmp_path / "output"
    runtime = _attest_single_offline_fixture(
        output,
        _offline_generate([manifest_path], output),
    )
    assert (
        validate_runtime_bar_grid_manifest(
            runtime,
            artifact_root=output,
            verify_sources=True,
        )
        == runtime
    )

    track = runtime["tracks"][0]
    active = json.loads((output / track["timingFile"]).read_text(encoding="utf-8"))
    provenance = active["timingProvenance"]["barStartsSeconds"]
    provenance["sourceClass"] = "annotation"
    _replace_single_active_timing(output, runtime, active)
    calls: list[Path] = []

    def forbidden_provider(*args: object) -> dict[str, object]:
        calls.append(args[0])
        raise AssertionError("analysis must not start")

    with pytest.raises(ValueError, match="not explicit runtime timing"):
        _offline_generate(
            [manifest_path],
            output,
            replace=True,
            provider=forbidden_provider,
        )
    assert calls == []


def test_runtime_validator_rejects_unreferenced_declared_annotation_artifact(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"first")
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, [_track("first", audio.name)])
    output = tmp_path / "output"
    runtime = _attest_single_offline_fixture(
        output,
        _offline_generate([manifest_path], output),
    )
    track = runtime["tracks"][0]
    active = json.loads((output / track["timingFile"]).read_text(encoding="utf-8"))
    annotation = deepcopy(active)
    provenance = annotation["timingProvenance"]["barStartsSeconds"]
    provenance.update(
        {
            "sourceClass": "annotation",
            "sourceId": "unreferenced-annotation-grid",
            "deployable": False,
            "referenceFree": False,
        }
    )
    annotation_payload = {key: value for key, value in annotation.items() if key != "contractSha256"}
    annotation["contractSha256"] = canonical_sha256(annotation_payload)
    annotation_sha256 = canonical_sha256(annotation)
    annotation_filename = f"timing-{annotation_sha256}.json"
    _write_canonical_json(output / annotation_filename, annotation)
    runtime["timingArtifacts"].append(
        {
            "timingFile": annotation_filename,
            "timingSha256": annotation_sha256,
            "timingContractSha256": annotation["contractSha256"],
        }
    )
    runtime["timingArtifacts"].sort(key=lambda row: row["timingFile"])
    runtime["manifestSha256"] = canonical_sha256(
        {key: value for key, value in runtime.items() if key != "manifestSha256"}
    )
    _write_canonical_json(output / "manifest.json", runtime)

    with pytest.raises(ValueError, match="exactly equal the active timing files"):
        validate_runtime_bar_grid_manifest(
            runtime,
            artifact_root=output,
            verify_sources=True,
        )


def test_symlinked_output_directory_and_destination_are_rejected(tmp_path: Path) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"audio")
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("dev", audio.name)])
    target = tmp_path / "target"
    target.mkdir()
    output_link = tmp_path / "output-link"
    output_link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked path components"):
        _offline_generate([manifest], output_link)
    assert list(target.iterdir()) == []

    output = tmp_path / "output"
    first = _offline_generate([manifest], output)
    timing_path = output / first["tracks"][0]["timingFile"]
    timing_path.unlink()
    sentinel = tmp_path / "sentinel.json"
    sentinel.write_text("untouched", encoding="utf-8")
    timing_path.symlink_to(sentinel)
    with pytest.raises(ValueError, match="regular, non-symlink"):
        _offline_generate([manifest], output, replace=True)
    assert sentinel.read_text(encoding="utf-8") == "untouched"


def test_audio_mutation_during_provider_fails_before_any_output(tmp_path: Path) -> None:
    audio = tmp_path / "first.wav"
    audio.write_bytes(b"before")
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("dev", audio.name)])

    def mutating_provider(
        audio_path: Path,
        audio_sha256: str,
        contract: dict[str, object],
        _timeout: float,
    ) -> dict[str, object]:
        output = _fake_output(contract, audio_sha256)
        audio_path.write_bytes(b"after")
        return output

    with pytest.raises(ValueError, match="changed during analysis"):
        _offline_generate([manifest], tmp_path / "output", provider=mutating_provider)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "mutation,message",
    [
        ({"networkRequestCount": 1}, "secondary network read"),
        ({"secureContext": True}, "platform semantics"),
        ({"float32ByteOrder": "big-endian"}, "platform semantics"),
        ({"sourceAudioSha256": "0" * 64}, "exact allowlisted audio"),
        ({"canonicalDurationMilliseconds": 3999}, "player rounding"),
        ({"decodedPcmSampleCount": 1}, "decoded duration"),
        ({"analyzerPcmSampleCount": 1}, "downsample contract"),
        ({"browserProduct": "Chrome/0.0.0.0"}, "wrong browser version"),
    ],
)
def test_runtime_identity_pcm_network_and_duration_claims_fail_closed(
    mutation: dict[str, object],
    message: str,
) -> None:
    contract = analyzer_contract()
    audio_sha256 = "c" * 64
    raw = {**_fake_output(contract, audio_sha256), **mutation}
    with pytest.raises(ValueError, match=message):
        _validate_runner_output(raw, contract, audio_sha256)


def _write_click_track(path: Path, *, duration_seconds: int = 12) -> None:
    sample_rate = 44_100
    beat_seconds = 0.5
    samples: list[int] = []
    for index in range(sample_rate * duration_seconds):
        time_seconds = index / sample_rate
        beat_index = int(time_seconds / beat_seconds)
        phase = time_seconds - beat_index * beat_seconds
        amplitude = 0.0
        if phase < 0.035:
            strength = 0.9 if beat_index % 4 == 0 else 0.55
            amplitude = strength * math.exp(-phase * 90) * math.sin(2 * math.pi * 880 * phase)
        samples.append(max(-32_767, min(32_767, round(amplitude * 32_767))))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frame_bytes = b"".join(struct.pack("<hh", sample, sample // 2) for sample in samples)
        handle.writeframes(frame_bytes)


def _runtime_available() -> bool:
    return BROWSER.is_file() and shutil.which("node") is not None


@pytest.mark.skipif(not _runtime_available(), reason="Pinned Chrome and Node are required.")
def test_real_browser_webaudio_wav_is_repeatable_and_emits_runtime_provenance(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "click.wav"
    _write_click_track(audio)
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("wav", audio.name)])
    first = generate_runtime_bar_grids([manifest], tmp_path / "first-output", timeout_seconds=60)
    second = generate_runtime_bar_grids([manifest], tmp_path / "second-output", timeout_seconds=60)

    assert first == second
    assert (
        validate_runtime_bar_grid_manifest(
            first,
            artifact_root=tmp_path / "first-output",
            verify_sources=True,
        )
        == first
    )
    assert first["runtimeAttested"] is True
    assert first["selectorUseAllowed"] is True
    entry = first["tracks"][0]
    assert entry["selectorUseAllowed"] is True
    assert entry["audioSha256"] == _file_sha256(audio)
    binding = entry["audioBinding"]
    assert binding["sourceAudioSha256"] == _file_sha256(audio)
    assert len(binding["decodedPcmSha256"]) == 64
    assert len(binding["analyzerPcmSha256"]) == 64
    assert (
        abs(binding["decodedDurationSeconds"] - binding["decodedPcmSampleCount"] / binding["decodedSampleRateHz"])
        <= 1 / binding["decodedSampleRateHz"]
    )
    assert entry["durationSeconds"] == binding["canonicalDurationMilliseconds"] / 1000
    timing = json.loads((tmp_path / "first-output" / entry["timingFile"]).read_text(encoding="utf-8"))
    provenance = timing["timingProvenance"]["barStartsSeconds"]
    assert provenance["sourceClass"] == "runtime"
    assert provenance["deployable"] is True
    assert provenance["referenceFree"] is True
    assert provenance["sourceContractSha256"] == first["analyzerContract"]["contractSha256"]
    assert (tmp_path / "first-output" / "manifest.json").read_bytes() == (
        tmp_path / "second-output" / "manifest.json"
    ).read_bytes()
    assert (tmp_path / "first-output" / entry["timingFile"]).read_bytes() == (
        tmp_path / "second-output" / second["tracks"][0]["timingFile"]
    ).read_bytes()


@pytest.mark.skipif(
    not _runtime_available() or shutil.which("ffmpeg") is None,
    reason="Pinned Chrome, Node, and fixture-only FFmpeg transcode are required.",
)
def test_real_browser_webaudio_lossy_mp3_binds_true_decode_duration_and_pcm(
    tmp_path: Path,
) -> None:
    wav = tmp_path / "click.wav"
    mp3 = tmp_path / "click.mp3"
    _write_click_track(wav)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", wav, "-codec:a", "libmp3lame", "-b:a", "128k", mp3],
        check=True,
        capture_output=True,
    )
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_track("mp3", mp3.name)])
    result = generate_runtime_bar_grids([manifest], tmp_path / "output", timeout_seconds=60)
    binding = result["tracks"][0]["audioBinding"]

    assert result["runtimeAttested"] is True
    assert binding["sourceAudioSha256"] == _file_sha256(mp3)
    assert binding["decodedPcmSampleCount"] > 0
    assert binding["decodedSampleRateHz"] > 0
    assert (
        abs(binding["decodedDurationSeconds"] - binding["decodedPcmSampleCount"] / binding["decodedSampleRateHz"])
        <= 1 / binding["decodedSampleRateHz"]
    )
    expected_milliseconds = math.floor(binding["decodedDurationSeconds"] * 1000 + 0.5)
    assert binding["canonicalDurationMilliseconds"] == expected_milliseconds
    assert result["tracks"][0]["durationSeconds"] == expected_milliseconds / 1000
