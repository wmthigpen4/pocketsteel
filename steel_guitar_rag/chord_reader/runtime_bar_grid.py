"""Target-browser, reference-free Play Along bar-grid generation.

Only a pinned Chrome/WebAudio execution of the current player client and
worker may emit deployable runtime timing. Test providers are deliberately
unattested and produce offline-proxy timing that selector consumers must reject.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

from .bar_promotion import canonical_sha256


INPUT_MANIFEST_SCHEMA = "chord_runtime_bar_audio_manifest_v2"
OUTPUT_MANIFEST_SCHEMA = "chord_runtime_bar_grid_manifest_v2"
RUNNER_OUTPUT_SCHEMA = "chord_runtime_browser_bar_analyzer_output_v1"
ANALYZER_CONTRACT_SCHEMA = "chord_runtime_browser_bar_analyzer_contract_v1"
EXPLICIT_BAR_GRID_SCHEMA = "chord_explicit_bar_grid_v1"
SOURCE_ID = "play-along-target-chrome-webaudio-rhythm-analysis-v1"
OFFLINE_PROXY_SOURCE_ID = "unattested-browser-fixture-proxy-v1"
DEVELOPMENT_SPLIT = "development"
DEFAULT_RUNNER_TIMEOUT_SECONDS = 300.0
MAX_RUNNER_TIMEOUT_SECONDS = 600.0
MAX_AUDIO_BYTES = 256 * 1024 * 1024

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKER = _REPO_ROOT / "ui" / "practice-analysis-worker.js"
_CLIENT = _REPO_ROOT / "ui" / "practice-analysis-client.js"
_RUNNER = _REPO_ROOT / "scripts" / "chord_runtime_bar_analyzer.js"
_GENERATOR = Path(__file__).resolve()
_BROWSER = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
_AUDIO_SUFFIXES = frozenset({".aac", ".m4a", ".mp3", ".wav"})
_BROWSER_FLAGS = (
    "--headless=new",
    "--remote-debugging-port=0",
    "--no-first-run",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter",
    "--disable-sync",
    "--metrics-recording-only",
    "--mute-audio",
    "--host-resolver-rules=MAP * ~NOTFOUND",
    "--no-proxy-server",
    "--proxy-server=direct://",
    "--proxy-bypass-list=*",
)
_HEX = frozenset("0123456789abcdef")
_ROOT_KEYS = frozenset({"schemaVersion", "split", "tracks"})
_TRACK_KEYS = frozenset({"id", "split", "audioPath"})
_RUNNER_KEYS = frozenset(
    {
        "schemaVersion",
        "sourceId",
        "browserExecutableSha256",
        "clientSha256",
        "nodeExecutableSha256",
        "runnerSha256",
        "workerSha256",
        "nodeVersion",
        "browserProduct",
        "browserRevision",
        "browserProtocolVersion",
        "browserJavaScriptVersion",
        "browserLaunchContractSha256",
        "networkRequestCount",
        "sourceAudioSha256",
        "decodedPcmSha256",
        "decodedPcmSampleCount",
        "decodedSampleRateHz",
        "decodedChannelCount",
        "decodedDurationSeconds",
        "canonicalDurationMilliseconds",
        "analyzerPcmSha256",
        "analyzerPcmSampleCount",
        "analyzerSampleRateHz",
        "float32ByteOrder",
        "secureContext",
        "navigatorUserAgent",
        "navigatorPlatform",
        "analysisVersion",
        "beatTimesSeconds",
        "barStartsSeconds",
        "meter",
        "beatsPerBar",
        "tempo",
    }
)
_OUTPUT_MANIFEST_KEYS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "selectorUseAllowed",
        "runtimeAttested",
        "analyzerContract",
        "sourceManifestSetSha256",
        "sourceManifests",
        "trackSetSha256",
        "timingArtifacts",
        "tracks",
        "previousManifestSha256",
        "manifestSha256",
    }
)
_OUTPUT_TRACK_KEYS = frozenset(
    {
        "trackId",
        "split",
        "selectorUseAllowed",
        "sourceManifestSha256",
        "audioSha256",
        "audioBinding",
        "audioBindingSha256",
        "analysisVersion",
        "runtimeIdentity",
        "runtimeIdentitySha256",
        "timingFile",
        "timingSha256",
        "timingContractSha256",
        "timingSourceContractSha256",
        "durationSeconds",
        "barCount",
        "trackArtifactSha256",
    }
)
_AUDIO_BINDING_KEYS = frozenset(
    {
        "sourceAudioSha256",
        "decodedPcmSha256",
        "decodedPcmSampleCount",
        "decodedSampleRateHz",
        "decodedChannelCount",
        "decodedDurationSeconds",
        "canonicalDurationMilliseconds",
        "analyzerPcmSha256",
        "analyzerPcmSampleCount",
        "analyzerSampleRateHz",
    }
)
_RUNTIME_IDENTITY_KEYS = frozenset(
    {
        "browserProduct",
        "browserRevision",
        "browserProtocolVersion",
        "browserJavaScriptVersion",
        "navigatorUserAgent",
        "navigatorPlatform",
        "nodeVersion",
    }
)
_TIMING_FILE = re.compile(r"^timing-([0-9a-f]{64})\.json$")
_RUNTIME_ATTESTATION = object()


@dataclass(frozen=True)
class _AttestedBrowserAnalysis:
    raw: Mapping[str, Any]
    attestation: object


@dataclass(frozen=True)
class _OutputState:
    output_dir: Path
    previous_manifest_sha256: str | None
    previous_runtime_attested: bool | None
    verified_artifacts: Mapping[str, Mapping[str, Any]]


AnalysisProvider = Callable[
    [Path, str, Mapping[str, Any], float],
    Mapping[str, Any] | _AttestedBrowserAnalysis,
]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    if positive and result <= 0:
        raise ValueError(f"{name} must be positive.")
    return result


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an array.")
    return value


def _render_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _command_output(command: Sequence[str], name: str) -> str:
    try:
        result = subprocess.run(
            list(command),
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"Could not identify the pinned {name} runtime.") from error
    output = result.stdout.strip()
    if not output:
        raise RuntimeError(f"The pinned {name} runtime returned no version identity.")
    return output


def _runtime_identity() -> dict[str, Any]:
    node_location = shutil.which("node")
    if not node_location:
        raise RuntimeError("The pinned Node runtime is unavailable.")
    node_path = Path(node_location).resolve(strict=True)
    browser_path = _BROWSER.resolve(strict=True)
    if not browser_path.is_file() or not os.access(browser_path, os.X_OK):
        raise RuntimeError("The pinned target Chrome runtime is unavailable.")
    node_version = _command_output([os.fspath(node_path), "--version"], "Node")
    browser_output = _command_output([os.fspath(browser_path), "--version"], "Chrome")
    version_match = re.search(r"([0-9]+(?:\.[0-9]+){3})$", browser_output)
    if not version_match:
        raise RuntimeError("The pinned target Chrome version could not be parsed.")
    return {
        "nodeExecutableSha256": _sha256_file(node_path),
        "nodeVersion": node_version,
        "browserExecutableSha256": _sha256_file(browser_path),
        "browserProduct": browser_output[: -len(version_match.group(1))].strip(),
        "browserVersion": version_match.group(1),
        "browserLaunchArguments": list(_BROWSER_FLAGS),
        "browserLaunchContractSha256": canonical_sha256(list(_BROWSER_FLAGS)),
    }


def analyzer_contract() -> dict[str, Any]:
    """Return the exact, non-injectable target-browser analyzer contract."""

    runtime = _runtime_identity()
    payload: dict[str, Any] = {
        "schemaVersion": ANALYZER_CONTRACT_SCHEMA,
        "sourceId": SOURCE_ID,
        "implementation": {
            "clientSha256": _sha256_file(_CLIENT),
            "workerSha256": _sha256_file(_WORKER),
            "runnerSha256": _sha256_file(_RUNNER),
            "generatorSha256": _sha256_file(_GENERATOR),
            "decodeExport": "STEEL_RAG_ANALYSIS_CLIENT.decodeAudio",
            "monoExport": "STEEL_RAG_ANALYSIS_CLIENT.monoSamples",
            "downsampleExport": "STEEL_RAG_ANALYSIS_V2.downsample",
            "rhythmExport": "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis",
        },
        "runtime": runtime,
        "audioInput": {
            "selfContainedFileOnly": True,
            "suffixAllowlist": sorted(_AUDIO_SUFFIXES),
            "maximumBytes": MAX_AUDIO_BYTES,
            "playlistAllowed": False,
            "secondaryReadsAllowed": False,
            "browserNetworkRequestsAllowed": 0,
        },
        "decode": {
            "decoder": "target-google-chrome-webaudio-decodeAudioData",
            "channelReduction": "arithmetic-mean-all-AudioBuffer-channels",
            "pcmEncoding": "Float32Array-little-endian",
            "canonicalDuration": "Math.round(AudioBuffer.duration*1000)/1000",
            "documentSecurityContext": "about:blank-non-secure-cdp-injected",
            "options": {},
            "hintsAllowed": False,
            "referenceFieldsAllowed": False,
        },
        "outputAdapter": {
            "barStartsDefinition": "rhythmAnalysis.barStartsMs/1000",
            "prefixCertification": "duplicate-exact-first-positive-bar-start",
            "rounding": "none",
        },
    }
    return {**payload, "contractSha256": canonical_sha256(payload)}


def _load_and_validate_manifests(manifest_paths: Sequence[Path]) -> list[dict[str, Any]]:
    if not manifest_paths:
        raise ValueError("At least one explicit development audio manifest is required.")
    manifests: list[dict[str, Any]] = []
    track_ids: set[str] = set()
    for manifest_index, manifest_path in enumerate(manifest_paths):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read audio manifest {manifest_index}.") from error
        manifest = _mapping(payload, f"manifest[{manifest_index}]")
        if set(manifest) != _ROOT_KEYS:
            raise ValueError(
                "Runtime bar audio manifests may contain only schemaVersion, split, and tracks."
            )
        if manifest.get("schemaVersion") != INPUT_MANIFEST_SCHEMA:
            raise ValueError(f"manifest[{manifest_index}] uses an unsupported schema.")
        if manifest.get("split") != DEVELOPMENT_SPLIT:
            raise ValueError(
                "Runtime bar-grid generation is development-only; calibration, test, "
                "heldout, confirmation, training, and other splits are forbidden."
            )
        raw_tracks = _sequence(manifest.get("tracks"), f"manifest[{manifest_index}].tracks")
        if not raw_tracks:
            raise ValueError(f"manifest[{manifest_index}].tracks must be nonempty.")
        tracks: list[dict[str, str]] = []
        for track_index, raw_track in enumerate(raw_tracks):
            track = _mapping(raw_track, f"manifest[{manifest_index}].tracks[{track_index}]")
            if set(track) != _TRACK_KEYS:
                raise ValueError(
                    "Runtime bar tracks may contain only id, split, and audioPath; "
                    "references, labels, annotations, playlists, and analyzer hints are forbidden."
                )
            if track.get("split") != DEVELOPMENT_SPLIT:
                raise ValueError(
                    "Every runtime bar track must use split='development' before any "
                    "audio path can be accessed."
                )
            track_id = track.get("id")
            raw_audio_path = track.get("audioPath")
            if not isinstance(track_id, str) or not track_id.strip() or track_id != track_id.strip():
                raise ValueError("Every runtime bar track requires a trimmed, nonempty string id.")
            if track_id in track_ids:
                raise ValueError(f"Duplicate runtime bar track id {track_id!r}.")
            if not isinstance(raw_audio_path, str) or not raw_audio_path.strip() or "\x00" in raw_audio_path:
                raise ValueError(f"Runtime bar track {track_id!r} requires a valid audioPath.")
            if Path(raw_audio_path).suffix.lower() not in _AUDIO_SUFFIXES:
                raise ValueError(
                    "Runtime bar audioPath values must use the self-contained WAV, MP3, "
                    "M4A, or AAC allowlist; playlists and remote sources are forbidden."
                )
            track_ids.add(track_id)
            tracks.append(
                {"id": track_id, "split": DEVELOPMENT_SPLIT, "audioPath": raw_audio_path}
            )
        tracks.sort(key=lambda item: item["id"])
        canonical_manifest = {
            "schemaVersion": INPUT_MANIFEST_SCHEMA,
            "split": DEVELOPMENT_SPLIT,
            "tracks": tracks,
        }
        manifests.append(
            {
                "manifestPath": manifest_path,
                "manifestSha256": canonical_sha256(canonical_manifest),
                "tracks": tracks,
            }
        )
    return manifests


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, name: str) -> None:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        if current.is_symlink():
            raise ValueError(f"{name} may not contain symlinked path components.")


def _resolved_audio_path(manifest_path: Path, raw_audio_path: str) -> Path:
    candidate = Path(raw_audio_path)
    if not candidate.is_absolute():
        candidate = manifest_path.parent / candidate
    resolved = candidate.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("Every runtime bar audioPath must resolve to a regular file.")
    if resolved.suffix.lower() not in _AUDIO_SUFFIXES:
        raise ValueError(
            "Every runtime bar audioPath must use the self-contained WAV, MP3, M4A, or AAC allowlist."
        )
    size = resolved.stat().st_size
    if size <= 0 or size > MAX_AUDIO_BYTES:
        raise ValueError("Every runtime bar audio file must be nonempty and within the size bound.")
    return resolved


def _validate_timing_artifact(path: Path) -> tuple[str, Mapping[str, Any]]:
    match = _TIMING_FILE.fullmatch(path.name)
    if not match:
        raise ValueError("Output directories may contain only content-addressed timing artifacts.")
    if path.is_symlink() or not path.is_file():
        raise ValueError("Verified timing artifacts must be regular, non-symlink files.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("A prior timing artifact is unreadable.") from error
    timing = _mapping(payload, f"prior timing artifact {path.name}")
    digest = canonical_sha256(timing)
    if digest != match.group(1):
        raise ValueError("A prior timing artifact does not match its content-addressed filename.")
    if path.read_text(encoding="utf-8") != _render_json(timing):
        raise ValueError("A prior timing artifact is not in canonical emitted form.")
    if timing.get("schemaVersion") != EXPLICIT_BAR_GRID_SCHEMA:
        raise ValueError("A prior timing artifact uses an unsupported schema.")
    claimed_contract = _required_sha256(timing.get("contractSha256"), "timing contractSha256")
    contract_payload = {key: value for key, value in timing.items() if key != "contractSha256"}
    if canonical_sha256(contract_payload) != claimed_contract:
        raise ValueError("A prior timing artifact has a forged timing contract.")
    return digest, timing


def _validate_prior_manifest(path: Path) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("A prior output manifest must be a regular, non-symlink file.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("The prior output manifest is unreadable.") from error
    manifest = _mapping(payload, "prior output manifest")
    if set(manifest) != _OUTPUT_MANIFEST_KEYS or manifest.get("schemaVersion") != OUTPUT_MANIFEST_SCHEMA:
        raise ValueError("The prior output manifest does not match the exact runtime-grid schema.")
    claimed = _required_sha256(manifest.get("manifestSha256"), "prior manifestSha256")
    manifest_payload = {key: value for key, value in manifest.items() if key != "manifestSha256"}
    if canonical_sha256(manifest_payload) != claimed:
        raise ValueError("The prior output manifest hash is invalid.")
    if path.read_text(encoding="utf-8") != _render_json(manifest):
        raise ValueError("The prior output manifest is not in canonical emitted form.")
    return manifest


def _prepare_output_directory(output_dir: Path, *, replace_verified_set: bool) -> _OutputState:
    absolute = _lexical_absolute(output_dir)
    _reject_symlink_components(absolute, "output_dir")
    if absolute.exists() and not absolute.is_dir():
        raise ValueError("output_dir must be a directory when it already exists.")
    if not absolute.exists():
        return _OutputState(absolute, None, None, {})
    entries = sorted(absolute.iterdir(), key=lambda item: item.name)
    if not entries:
        return _OutputState(absolute, None, None, {})
    if not replace_verified_set:
        raise ValueError(
            "output_dir must be new or empty unless replace_verified_set is explicitly enabled."
        )
    manifest_path = absolute / "manifest.json"
    # Replacement is allowed only for a committed prior set. Content-addressed
    # timing files without that commit point are not enough to establish the
    # prior set's runtime-attestation class.
    prior_manifest = _validate_prior_manifest(manifest_path)
    verified: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if entry.name == "manifest.json":
            continue
        digest, timing = _validate_timing_artifact(entry)
        verified[entry.name] = {
            "timingFile": entry.name,
            "timingSha256": digest,
            "timingContractSha256": timing["contractSha256"],
        }
    previous_sha256: str | None = None
    previous_runtime_attested: bool | None = None
    previous_sha256 = str(prior_manifest["manifestSha256"])
    raw_attested = prior_manifest.get("runtimeAttested")
    raw_selector = prior_manifest.get("selectorUseAllowed")
    if not isinstance(raw_attested, bool) or raw_selector is not raw_attested:
        raise ValueError("The prior output set has inconsistent runtime attestation flags.")
    previous_runtime_attested = raw_attested
    artifact_rows = _sequence(prior_manifest.get("timingArtifacts"), "prior timingArtifacts")
    for index, raw_row in enumerate(artifact_rows):
        row = _mapping(raw_row, f"prior timingArtifacts[{index}]")
        if set(row) != {"timingFile", "timingSha256", "timingContractSha256"}:
            raise ValueError("The prior timingArtifacts contract is invalid.")
        filename = str(row.get("timingFile") or "")
        if filename not in verified or dict(row) != dict(verified[filename]):
            raise ValueError("The prior manifest does not bind its complete timing artifact set.")
    declared = {str(row["timingFile"]) for row in artifact_rows}
    if not declared <= set(verified):
        raise ValueError("The prior output set is missing a declared timing artifact.")
    tracks = _sequence(prior_manifest.get("tracks"), "prior tracks")
    for index, raw_track in enumerate(tracks):
        track = _mapping(raw_track, f"prior tracks[{index}]")
        filename = str(track.get("timingFile") or "")
        if filename not in verified or track.get("timingSha256") != verified[filename]["timingSha256"]:
            raise ValueError("A prior track does not bind a verified timing artifact.")
    if previous_runtime_attested:
        validate_runtime_bar_grid_manifest(prior_manifest, verify_sources=False)
    return _OutputState(absolute, previous_sha256, previous_runtime_attested, verified)


def _run_target_browser_analyzer(
    audio_path: Path,
    audio_sha256: str,
    contract: Mapping[str, Any],
    timeout_seconds: float,
) -> _AttestedBrowserAnalysis:
    implementation = _mapping(contract.get("implementation"), "analyzer implementation")
    runtime = _mapping(contract.get("runtime"), "analyzer runtime")
    command = [
        "node",
        os.fspath(_RUNNER),
        "--audio",
        os.fspath(audio_path),
        "--expected-audio-sha256",
        audio_sha256,
        "--expected-browser-sha256",
        str(runtime["browserExecutableSha256"]),
        "--expected-browser-version",
        str(runtime["browserVersion"]),
        "--expected-client-sha256",
        str(implementation["clientSha256"]),
        "--expected-node-sha256",
        str(runtime["nodeExecutableSha256"]),
        "--expected-node-version",
        str(runtime["nodeVersion"]),
        "--expected-runner-sha256",
        str(implementation["runnerSha256"]),
        "--expected-worker-sha256",
        str(implementation["workerSha256"]),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("The bounded target-browser timing harness could not complete.") from error
    if result.returncode != 0:
        message = result.stderr.strip() or "unknown target-browser harness error"
        raise RuntimeError(f"The target-browser timing harness failed: {message}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("The target-browser timing harness returned invalid JSON.") from error
    raw = _mapping(payload, "target-browser timing harness output")
    return _AttestedBrowserAnalysis(raw=raw, attestation=_RUNTIME_ATTESTATION)


def _numeric_array(value: Any, name: str) -> list[float]:
    raw_values = _sequence(value, name)
    return [_finite_number(item, f"{name}[{index}]") for index, item in enumerate(raw_values)]


def _validate_runner_output(
    raw_output: Mapping[str, Any],
    contract: Mapping[str, Any],
    source_audio_sha256: str,
) -> dict[str, Any]:
    output = _mapping(raw_output, "target-browser timing harness output")
    if set(output) != _RUNNER_KEYS:
        raise ValueError(
            "Target-browser output contains missing or unsupported fields; labels, "
            "references, playlists, and secondary sources are forbidden."
        )
    if output.get("schemaVersion") != RUNNER_OUTPUT_SCHEMA or output.get("sourceId") != SOURCE_ID:
        raise ValueError("Target-browser output uses the wrong schema or source identity.")
    implementation = _mapping(contract.get("implementation"), "analyzer implementation")
    runtime = _mapping(contract.get("runtime"), "analyzer runtime")
    identity_pairs = (
        ("workerSha256", implementation.get("workerSha256")),
        ("clientSha256", implementation.get("clientSha256")),
        ("runnerSha256", implementation.get("runnerSha256")),
        ("browserExecutableSha256", runtime.get("browserExecutableSha256")),
        ("nodeExecutableSha256", runtime.get("nodeExecutableSha256")),
    )
    for name, expected in identity_pairs:
        if _required_sha256(output.get(name), f"runner {name}") != expected:
            raise ValueError(f"Target-browser output {name} does not match the analyzer contract.")
    if output.get("nodeVersion") != runtime.get("nodeVersion"):
        raise ValueError("Target-browser output used the wrong Node runtime version.")
    expected_browser_product = f"Chrome/{runtime['browserVersion']}"
    if output.get("browserProduct") != expected_browser_product:
        raise ValueError("Target-browser output used the wrong browser version.")
    for name in ("browserRevision", "browserProtocolVersion", "browserJavaScriptVersion"):
        if not isinstance(output.get(name), str) or not str(output[name]).strip():
            raise ValueError(f"Target-browser output {name} must be nonempty.")
    if output.get("browserLaunchContractSha256") != runtime.get("browserLaunchContractSha256"):
        raise ValueError("Target-browser launch arguments do not match the analyzer contract.")
    if output.get("networkRequestCount") != 0:
        raise ValueError("Target-browser analysis attempted a forbidden secondary network read.")
    if output.get("secureContext") is not False or output.get("float32ByteOrder") != "little-endian":
        raise ValueError("Target-browser PCM execution does not match the bound platform semantics.")
    if _required_sha256(output.get("sourceAudioSha256"), "runner sourceAudioSha256") != source_audio_sha256:
        raise ValueError("Target-browser output does not bind the exact allowlisted audio bytes.")

    decoded_pcm_sha256 = _required_sha256(output.get("decodedPcmSha256"), "decodedPcmSha256")
    decoded_count = _positive_integer(output.get("decodedPcmSampleCount"), "decodedPcmSampleCount")
    decoded_rate = _positive_integer(output.get("decodedSampleRateHz"), "decodedSampleRateHz")
    decoded_channels = _positive_integer(output.get("decodedChannelCount"), "decodedChannelCount")
    decoded_duration = _finite_number(
        output.get("decodedDurationSeconds"),
        "decodedDurationSeconds",
        positive=True,
    )
    if not math.isclose(decoded_duration, decoded_count / decoded_rate, rel_tol=0, abs_tol=1 / decoded_rate):
        raise ValueError("Target-browser decoded duration does not match its PCM sample binding.")
    canonical_duration_ms = _positive_integer(
        output.get("canonicalDurationMilliseconds"),
        "canonicalDurationMilliseconds",
    )
    if canonical_duration_ms != math.floor(decoded_duration * 1000 + 0.5):
        raise ValueError("Target-browser canonical duration does not match player rounding.")

    analyzer_pcm_sha256 = _required_sha256(output.get("analyzerPcmSha256"), "analyzerPcmSha256")
    analyzer_count = _positive_integer(output.get("analyzerPcmSampleCount"), "analyzerPcmSampleCount")
    analyzer_rate = _positive_integer(output.get("analyzerSampleRateHz"), "analyzerSampleRateHz")
    expected_analyzer_rate = min(decoded_rate, 11_025)
    expected_analyzer_count = (
        decoded_count
        if decoded_rate <= 11_025
        else math.floor(decoded_count / (decoded_rate / 11_025))
    )
    if analyzer_rate != expected_analyzer_rate or analyzer_count != expected_analyzer_count:
        raise ValueError("Target-browser analyzer PCM does not match the player downsample contract.")
    analysis_version = _positive_integer(output.get("analysisVersion"), "analysisVersion")

    duration = canonical_duration_ms / 1000
    beat_times = _numeric_array(output.get("beatTimesSeconds"), "beatTimesSeconds")
    bar_starts = _numeric_array(output.get("barStartsSeconds"), "barStartsSeconds")
    if not beat_times or not bar_starts:
        raise ValueError("The target-browser analyzer must return nonempty beat and bar arrays.")
    for name, values in (("beatTimesSeconds", beat_times), ("barStartsSeconds", bar_starts)):
        previous = -math.inf
        for value in values:
            if value < 0 or value >= duration:
                raise ValueError(f"Target-browser {name} contains an out-of-range value.")
            if value <= previous:
                raise ValueError(f"Target-browser {name} must be strictly increasing.")
            previous = value
    meter = output.get("meter")
    meter_beats = {"2/4": 2, "3/4": 3, "4/4": 4, "6/8": 6}
    if not isinstance(meter, str) or meter not in meter_beats:
        raise ValueError("Target-browser output returned an unsupported meter.")
    beats_per_bar = _positive_integer(output.get("beatsPerBar"), "beatsPerBar")
    if beats_per_bar != meter_beats[meter]:
        raise ValueError("Target-browser beatsPerBar does not match its meter.")
    beat_indices: list[int] = []
    for bar_start in bar_starts:
        matches = [
            index
            for index, beat in enumerate(beat_times)
            if math.isclose(bar_start, beat, rel_tol=0, abs_tol=1e-9)
        ]
        if len(matches) != 1:
            raise ValueError("Every target-browser bar start must map to exactly one beat.")
        beat_indices.append(matches[0])
    if beat_indices[0] != 0 or any(
        right - left != beats_per_bar for left, right in zip(beat_indices, beat_indices[1:])
    ):
        raise ValueError("Target-browser bar starts do not follow the downbeat sequence.")
    _finite_number(output.get("tempo"), "tempo", positive=True)
    navigator_user_agent = output.get("navigatorUserAgent")
    navigator_platform = output.get("navigatorPlatform")
    browser_major = str(runtime["browserVersion"]).split(".", 1)[0]
    if not isinstance(navigator_user_agent, str) or not re.search(
        rf"(?:Chrome|HeadlessChrome)/{re.escape(browser_major)}\.",
        navigator_user_agent,
    ):
        raise ValueError("Target-browser navigator identity does not match the pinned browser.")
    if not isinstance(navigator_platform, str) or not navigator_platform:
        raise ValueError("Target-browser navigator platform must be nonempty.")
    runtime_identity = {
        "browserProduct": output["browserProduct"],
        "browserRevision": output["browserRevision"],
        "browserProtocolVersion": output["browserProtocolVersion"],
        "browserJavaScriptVersion": output["browserJavaScriptVersion"],
        "navigatorUserAgent": navigator_user_agent,
        "navigatorPlatform": navigator_platform,
        "nodeVersion": output["nodeVersion"],
    }
    return {
        "durationSeconds": duration,
        "canonicalDurationMilliseconds": canonical_duration_ms,
        "barStartsSeconds": bar_starts,
        "analysisVersion": analysis_version,
        "sourceAudioSha256": source_audio_sha256,
        "decodedPcmSha256": decoded_pcm_sha256,
        "decodedPcmSampleCount": decoded_count,
        "decodedSampleRateHz": decoded_rate,
        "decodedChannelCount": decoded_channels,
        "decodedDurationSeconds": decoded_duration,
        "analyzerPcmSha256": analyzer_pcm_sha256,
        "analyzerPcmSampleCount": analyzer_count,
        "analyzerSampleRateHz": analyzer_rate,
        "runtimeIdentity": runtime_identity,
        "runtimeIdentitySha256": canonical_sha256(runtime_identity),
    }


def _timing_from_validated(
    validated: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    runtime_attested: bool,
) -> dict[str, Any]:
    claimed_contract = _required_sha256(contract.get("contractSha256"), "analyzer contractSha256")
    contract_payload = {key: value for key, value in contract.items() if key != "contractSha256"}
    if canonical_sha256(contract_payload) != claimed_contract:
        raise ValueError("Analyzer contractSha256 does not match its canonical payload.")
    source_contract_sha256 = (
        claimed_contract
        if runtime_attested
        else canonical_sha256(
            {"baseAnalyzerContractSha256": claimed_contract, "runtimeAttestation": "absent"}
        )
    )
    starts = list(validated["barStartsSeconds"])
    provenance: dict[str, Any] = {
        "status": "explicit",
        "sourceClass": "runtime" if runtime_attested else "offline-proxy",
        "sourceId": SOURCE_ID if runtime_attested else OFFLINE_PROXY_SOURCE_ID,
        "sourceContractSha256": source_contract_sha256,
        "deployable": runtime_attested,
        "referenceFree": True,
    }
    timing: dict[str, Any] = {
        "schemaVersion": EXPLICIT_BAR_GRID_SCHEMA,
        "durationSeconds": validated["durationSeconds"],
        "barStartsSeconds": starts,
        "timingProvenance": {"barStartsSeconds": provenance},
    }
    if starts[0] > 0:
        timing["prefixExcludedSeconds"] = starts[0]
        provenance["prefixExcludedSeconds"] = starts[0]
    return {**timing, "contractSha256": canonical_sha256(timing)}


def _validate_analyzer_contract_claim(
    raw_contract: Any,
    *,
    verify_sources: bool,
) -> Mapping[str, Any]:
    contract = _mapping(raw_contract, "runtime manifest analyzerContract")
    required_top = {
        "schemaVersion",
        "sourceId",
        "implementation",
        "runtime",
        "audioInput",
        "decode",
        "outputAdapter",
        "contractSha256",
    }
    if set(contract) != required_top:
        raise ValueError("Runtime analyzerContract does not match the exact v2 contract.")
    if contract.get("schemaVersion") != ANALYZER_CONTRACT_SCHEMA or contract.get("sourceId") != SOURCE_ID:
        raise ValueError("Runtime analyzerContract uses the wrong schema or source identity.")
    claimed = _required_sha256(contract.get("contractSha256"), "analyzerContract.contractSha256")
    payload = {key: value for key, value in contract.items() if key != "contractSha256"}
    if canonical_sha256(payload) != claimed:
        raise ValueError("Runtime analyzerContract hash is invalid.")

    implementation = _mapping(contract.get("implementation"), "analyzerContract.implementation")
    if set(implementation) != {
        "clientSha256",
        "workerSha256",
        "runnerSha256",
        "generatorSha256",
        "decodeExport",
        "monoExport",
        "downsampleExport",
        "rhythmExport",
    }:
        raise ValueError("Runtime analyzer implementation binding is incomplete.")
    for name in ("clientSha256", "workerSha256", "runnerSha256", "generatorSha256"):
        _required_sha256(implementation.get(name), f"analyzerContract.implementation.{name}")
    expected_exports = {
        "decodeExport": "STEEL_RAG_ANALYSIS_CLIENT.decodeAudio",
        "monoExport": "STEEL_RAG_ANALYSIS_CLIENT.monoSamples",
        "downsampleExport": "STEEL_RAG_ANALYSIS_V2.downsample",
        "rhythmExport": "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis",
    }
    if any(implementation.get(name) != value for name, value in expected_exports.items()):
        raise ValueError("Runtime analyzer implementation exports do not match the player path.")

    runtime = _mapping(contract.get("runtime"), "analyzerContract.runtime")
    if set(runtime) != {
        "nodeExecutableSha256",
        "nodeVersion",
        "browserExecutableSha256",
        "browserProduct",
        "browserVersion",
        "browserLaunchArguments",
        "browserLaunchContractSha256",
    }:
        raise ValueError("Runtime analyzer runtime identity is incomplete.")
    _required_sha256(runtime.get("nodeExecutableSha256"), "runtime.nodeExecutableSha256")
    _required_sha256(runtime.get("browserExecutableSha256"), "runtime.browserExecutableSha256")
    _required_sha256(
        runtime.get("browserLaunchContractSha256"),
        "runtime.browserLaunchContractSha256",
    )
    if runtime.get("browserProduct") != "Google Chrome":
        raise ValueError("Runtime analyzer browser product is not the pinned target.")
    if not isinstance(runtime.get("browserVersion"), str) or not re.fullmatch(
        r"[0-9]+(?:\.[0-9]+){3}",
        str(runtime.get("browserVersion")),
    ):
        raise ValueError("Runtime analyzer browser version is invalid.")
    if not isinstance(runtime.get("nodeVersion"), str) or not str(runtime["nodeVersion"]).startswith("v"):
        raise ValueError("Runtime analyzer Node version is invalid.")
    launch_arguments = _sequence(
        runtime.get("browserLaunchArguments"),
        "runtime.browserLaunchArguments",
    )
    if list(launch_arguments) != list(_BROWSER_FLAGS) or canonical_sha256(list(launch_arguments)) != runtime.get(
        "browserLaunchContractSha256"
    ):
        raise ValueError("Runtime analyzer browser launch policy is invalid.")

    audio_input = _mapping(contract.get("audioInput"), "analyzerContract.audioInput")
    if dict(audio_input) != {
        "selfContainedFileOnly": True,
        "suffixAllowlist": sorted(_AUDIO_SUFFIXES),
        "maximumBytes": MAX_AUDIO_BYTES,
        "playlistAllowed": False,
        "secondaryReadsAllowed": False,
        "browserNetworkRequestsAllowed": 0,
    }:
        raise ValueError("Runtime analyzer audio allowlist policy is invalid.")
    decode = _mapping(contract.get("decode"), "analyzerContract.decode")
    if dict(decode) != {
        "decoder": "target-google-chrome-webaudio-decodeAudioData",
        "channelReduction": "arithmetic-mean-all-AudioBuffer-channels",
        "pcmEncoding": "Float32Array-little-endian",
        "canonicalDuration": "Math.round(AudioBuffer.duration*1000)/1000",
        "documentSecurityContext": "about:blank-non-secure-cdp-injected",
        "options": {},
        "hintsAllowed": False,
        "referenceFieldsAllowed": False,
    }:
        raise ValueError("Runtime analyzer decode policy is invalid.")
    output_adapter = _mapping(contract.get("outputAdapter"), "analyzerContract.outputAdapter")
    if dict(output_adapter) != {
        "barStartsDefinition": "rhythmAnalysis.barStartsMs/1000",
        "prefixCertification": "duplicate-exact-first-positive-bar-start",
        "rounding": "none",
    }:
        raise ValueError("Runtime analyzer output adapter policy is invalid.")
    if verify_sources and dict(contract) != analyzer_contract():
        raise ValueError("Runtime analyzerContract does not match the current pinned sources.")
    return contract


def _validate_runtime_timing_payload(
    timing: Mapping[str, Any],
    *,
    timing_sha256: str,
    analyzer_contract_sha256: str,
    duration_seconds: float,
    bar_count: int,
) -> None:
    allowed = {
        "schemaVersion",
        "durationSeconds",
        "barStartsSeconds",
        "timingProvenance",
        "contractSha256",
    }
    if "prefixExcludedSeconds" in timing:
        allowed.add("prefixExcludedSeconds")
    if set(timing) != allowed or timing.get("schemaVersion") != EXPLICIT_BAR_GRID_SCHEMA:
        raise ValueError("Runtime timing artifact does not match the exact timing schema.")
    if canonical_sha256(timing) != timing_sha256:
        raise ValueError("Runtime timing artifact does not match its manifest hash.")
    claimed_contract = _required_sha256(timing.get("contractSha256"), "timing.contractSha256")
    payload = {key: value for key, value in timing.items() if key != "contractSha256"}
    if canonical_sha256(payload) != claimed_contract:
        raise ValueError("Runtime timing artifact has an invalid timing contract hash.")
    duration = _finite_number(timing.get("durationSeconds"), "timing.durationSeconds", positive=True)
    if duration != duration_seconds:
        raise ValueError("Runtime timing and manifest durations disagree.")
    starts = _numeric_array(timing.get("barStartsSeconds"), "timing.barStartsSeconds")
    if len(starts) != bar_count or not starts:
        raise ValueError("Runtime timing and manifest bar counts disagree.")
    previous = -math.inf
    for start in starts:
        if start < 0 or start >= duration or start <= previous:
            raise ValueError("Runtime timing bar starts are invalid.")
        previous = start
    timing_provenance = _mapping(timing.get("timingProvenance"), "timing.timingProvenance")
    if set(timing_provenance) != {"barStartsSeconds"}:
        raise ValueError("Runtime timing provenance has unsupported fields.")
    provenance = _mapping(
        timing_provenance.get("barStartsSeconds"),
        "timing.timingProvenance.barStartsSeconds",
    )
    expected_provenance_keys = {
        "status",
        "sourceClass",
        "sourceId",
        "sourceContractSha256",
        "deployable",
        "referenceFree",
    }
    if starts[0] > 0:
        expected_provenance_keys.add("prefixExcludedSeconds")
    if set(provenance) != expected_provenance_keys:
        raise ValueError("Runtime timing provenance does not match the exact runtime contract.")
    if provenance.get("status") != "explicit" or provenance.get("sourceClass") != "runtime":
        raise ValueError("Runtime timing provenance is not explicit runtime timing.")
    if provenance.get("sourceId") != SOURCE_ID or provenance.get("deployable") is not True:
        raise ValueError("Runtime timing provenance is not deployable from the pinned source.")
    if provenance.get("referenceFree") is not True:
        raise ValueError("Runtime timing provenance is not reference-free.")
    if provenance.get("sourceContractSha256") != analyzer_contract_sha256:
        raise ValueError("Runtime timing provenance does not bind the analyzer contract.")
    if starts[0] > 0:
        if timing.get("prefixExcludedSeconds") != starts[0] or provenance.get(
            "prefixExcludedSeconds"
        ) != starts[0]:
            raise ValueError("Runtime timing prefix certification is invalid.")
    elif "prefixExcludedSeconds" in timing or "prefixExcludedSeconds" in provenance:
        raise ValueError("Zero-start runtime timing may not claim an excluded prefix.")


def validate_runtime_bar_grid_manifest(
    manifest: Mapping[str, Any],
    *,
    artifact_root: Path | None = None,
    verify_sources: bool = True,
) -> dict[str, Any]:
    """Strictly validate a deployable v2 runtime manifest for selector consumers."""

    value = _mapping(manifest, "runtime bar-grid manifest")
    if set(value) != _OUTPUT_MANIFEST_KEYS or value.get("schemaVersion") != OUTPUT_MANIFEST_SCHEMA:
        raise ValueError("Runtime bar-grid manifest does not match the exact v2 schema.")
    if value.get("split") != DEVELOPMENT_SPLIT or value.get("developmentOnly") is not True:
        raise ValueError("Runtime bar-grid manifest is not development-only.")
    if value.get("promotionEligible") is not False:
        raise ValueError("Runtime bar-grid manifest must not be promotion-eligible.")
    if value.get("runtimeAttested") is not True or value.get("selectorUseAllowed") is not True:
        raise ValueError("Runtime bar-grid manifest is not attested for selector use.")
    claimed_manifest_sha256 = _required_sha256(value.get("manifestSha256"), "manifestSha256")
    payload = {key: item for key, item in value.items() if key != "manifestSha256"}
    if canonical_sha256(payload) != claimed_manifest_sha256:
        raise ValueError("Runtime bar-grid manifest hash is invalid.")
    previous = value.get("previousManifestSha256")
    if previous is not None:
        _required_sha256(previous, "previousManifestSha256")

    contract = _validate_analyzer_contract_claim(
        value.get("analyzerContract"),
        verify_sources=verify_sources,
    )
    analyzer_contract_sha256 = str(contract["contractSha256"])
    runtime_contract = _mapping(contract.get("runtime"), "analyzerContract.runtime")

    raw_sources = _sequence(value.get("sourceManifests"), "sourceManifests")
    if not raw_sources:
        raise ValueError("Runtime bar-grid manifest requires source manifests.")
    source_rows: list[dict[str, Any]] = []
    source_hashes: set[str] = set()
    for index, raw_source in enumerate(raw_sources):
        source = _mapping(raw_source, f"sourceManifests[{index}]")
        if set(source) != {"sourceManifestSha256", "trackCount"}:
            raise ValueError("Runtime source manifest rows do not match the exact contract.")
        source_sha256 = _required_sha256(
            source.get("sourceManifestSha256"),
            f"sourceManifests[{index}].sourceManifestSha256",
        )
        if source_sha256 in source_hashes:
            raise ValueError("Runtime source manifest hashes must be unique.")
        source_hashes.add(source_sha256)
        source_rows.append(
            {
                "sourceManifestSha256": source_sha256,
                "trackCount": _positive_integer(
                    source.get("trackCount"),
                    f"sourceManifests[{index}].trackCount",
                ),
            }
        )
    if source_rows != sorted(source_rows, key=lambda item: item["sourceManifestSha256"]):
        raise ValueError("Runtime source manifest rows must be canonically sorted.")
    if canonical_sha256(source_rows) != value.get("sourceManifestSetSha256"):
        raise ValueError("Runtime source manifest set hash is invalid.")

    raw_artifacts = _sequence(value.get("timingArtifacts"), "timingArtifacts")
    if not raw_artifacts:
        raise ValueError("Runtime bar-grid manifest requires timing artifacts.")
    artifact_rows: dict[str, dict[str, str]] = {}
    artifact_order: list[str] = []
    for index, raw_artifact in enumerate(raw_artifacts):
        artifact = _mapping(raw_artifact, f"timingArtifacts[{index}]")
        if set(artifact) != {"timingFile", "timingSha256", "timingContractSha256"}:
            raise ValueError("Runtime timing artifact rows do not match the exact contract.")
        filename = artifact.get("timingFile")
        if not isinstance(filename, str):
            raise ValueError("Runtime timing artifact filename must be a string.")
        match = _TIMING_FILE.fullmatch(filename)
        timing_sha256 = _required_sha256(
            artifact.get("timingSha256"),
            f"timingArtifacts[{index}].timingSha256",
        )
        timing_contract_sha256 = _required_sha256(
            artifact.get("timingContractSha256"),
            f"timingArtifacts[{index}].timingContractSha256",
        )
        if not match or match.group(1) != timing_sha256 or filename in artifact_rows:
            raise ValueError("Runtime timing artifacts are not uniquely content-addressed.")
        artifact_rows[filename] = {
            "timingFile": filename,
            "timingSha256": timing_sha256,
            "timingContractSha256": timing_contract_sha256,
        }
        artifact_order.append(filename)
    if artifact_order != sorted(artifact_order):
        raise ValueError("Runtime timing artifacts must be canonically sorted.")

    raw_tracks = _sequence(value.get("tracks"), "tracks")
    if not raw_tracks:
        raise ValueError("Runtime bar-grid manifest requires tracks.")
    tracks: list[Mapping[str, Any]] = []
    track_ids: set[str] = set()
    runtime_identity_hashes: set[str] = set()
    for index, raw_track in enumerate(raw_tracks):
        track = _mapping(raw_track, f"tracks[{index}]")
        if set(track) != _OUTPUT_TRACK_KEYS:
            raise ValueError("Runtime track rows do not match the exact v2 contract.")
        track_id = track.get("trackId")
        if not isinstance(track_id, str) or not track_id or track_id in track_ids:
            raise ValueError("Runtime track ids must be nonempty and unique.")
        track_ids.add(track_id)
        if track.get("split") != DEVELOPMENT_SPLIT or track.get("selectorUseAllowed") is not True:
            raise ValueError("Every runtime track must be development-only and selector-allowed.")
        if track.get("sourceManifestSha256") not in source_hashes:
            raise ValueError("Runtime track does not bind a declared source manifest.")

        audio_sha256 = _required_sha256(track.get("audioSha256"), f"tracks[{index}].audioSha256")
        audio_binding = _mapping(track.get("audioBinding"), f"tracks[{index}].audioBinding")
        if set(audio_binding) != _AUDIO_BINDING_KEYS:
            raise ValueError("Runtime track audioBinding does not match the exact contract.")
        if audio_binding.get("sourceAudioSha256") != audio_sha256:
            raise ValueError("Runtime track audioBinding does not bind audioSha256.")
        for name in ("sourceAudioSha256", "decodedPcmSha256", "analyzerPcmSha256"):
            _required_sha256(audio_binding.get(name), f"tracks[{index}].audioBinding.{name}")
        decoded_count = _positive_integer(
            audio_binding.get("decodedPcmSampleCount"),
            f"tracks[{index}].audioBinding.decodedPcmSampleCount",
        )
        decoded_rate = _positive_integer(
            audio_binding.get("decodedSampleRateHz"),
            f"tracks[{index}].audioBinding.decodedSampleRateHz",
        )
        _positive_integer(
            audio_binding.get("decodedChannelCount"),
            f"tracks[{index}].audioBinding.decodedChannelCount",
        )
        decoded_duration = _finite_number(
            audio_binding.get("decodedDurationSeconds"),
            f"tracks[{index}].audioBinding.decodedDurationSeconds",
            positive=True,
        )
        if not math.isclose(decoded_duration, decoded_count / decoded_rate, rel_tol=0, abs_tol=1 / decoded_rate):
            raise ValueError("Runtime track decoded duration and PCM binding disagree.")
        canonical_ms = _positive_integer(
            audio_binding.get("canonicalDurationMilliseconds"),
            f"tracks[{index}].audioBinding.canonicalDurationMilliseconds",
        )
        if canonical_ms != math.floor(decoded_duration * 1000 + 0.5):
            raise ValueError("Runtime track canonical duration does not match browser PCM.")
        analyzer_count = _positive_integer(
            audio_binding.get("analyzerPcmSampleCount"),
            f"tracks[{index}].audioBinding.analyzerPcmSampleCount",
        )
        analyzer_rate = _positive_integer(
            audio_binding.get("analyzerSampleRateHz"),
            f"tracks[{index}].audioBinding.analyzerSampleRateHz",
        )
        expected_rate = min(decoded_rate, 11_025)
        expected_count = (
            decoded_count
            if decoded_rate <= 11_025
            else math.floor(decoded_count / (decoded_rate / 11_025))
        )
        if analyzer_rate != expected_rate or analyzer_count != expected_count:
            raise ValueError("Runtime track analyzer PCM binding is invalid.")
        if track.get("audioBindingSha256") != canonical_sha256(audio_binding):
            raise ValueError("Runtime track audioBinding hash is invalid.")
        duration = _finite_number(track.get("durationSeconds"), f"tracks[{index}].durationSeconds")
        if duration != canonical_ms / 1000:
            raise ValueError("Runtime track duration does not match its canonical audio binding.")

        runtime_identity = _mapping(
            track.get("runtimeIdentity"),
            f"tracks[{index}].runtimeIdentity",
        )
        if set(runtime_identity) != _RUNTIME_IDENTITY_KEYS:
            raise ValueError("Runtime track runtimeIdentity does not match the exact contract.")
        if runtime_identity.get("browserProduct") != f"Chrome/{runtime_contract['browserVersion']}":
            raise ValueError("Runtime track browser identity does not match analyzerContract.")
        if runtime_identity.get("nodeVersion") != runtime_contract.get("nodeVersion"):
            raise ValueError("Runtime track Node identity does not match analyzerContract.")
        for name in _RUNTIME_IDENTITY_KEYS:
            if not isinstance(runtime_identity.get(name), str) or not str(runtime_identity[name]):
                raise ValueError("Runtime track runtimeIdentity contains an empty field.")
        runtime_identity_sha256 = _required_sha256(
            track.get("runtimeIdentitySha256"),
            f"tracks[{index}].runtimeIdentitySha256",
        )
        if runtime_identity_sha256 != canonical_sha256(runtime_identity):
            raise ValueError("Runtime track runtimeIdentity hash is invalid.")
        runtime_identity_hashes.add(runtime_identity_sha256)

        filename = track.get("timingFile")
        if not isinstance(filename, str) or filename not in artifact_rows:
            raise ValueError("Runtime track does not reference a declared timing artifact.")
        artifact = artifact_rows[filename]
        if track.get("timingSha256") != artifact["timingSha256"] or track.get(
            "timingContractSha256"
        ) != artifact["timingContractSha256"]:
            raise ValueError("Runtime track timing hashes disagree with timingArtifacts.")
        if track.get("timingSourceContractSha256") != analyzer_contract_sha256:
            raise ValueError("Runtime track timing source does not bind analyzerContract.")
        _positive_integer(track.get("analysisVersion"), f"tracks[{index}].analysisVersion")
        _positive_integer(track.get("barCount"), f"tracks[{index}].barCount")
        claimed_track_sha256 = _required_sha256(
            track.get("trackArtifactSha256"),
            f"tracks[{index}].trackArtifactSha256",
        )
        track_payload = {key: item for key, item in track.items() if key != "trackArtifactSha256"}
        if canonical_sha256(track_payload) != claimed_track_sha256:
            raise ValueError("Runtime track artifact hash is invalid.")
        tracks.append(track)
    if [track["trackId"] for track in tracks] != sorted(track_ids):
        raise ValueError("Runtime tracks must be canonically sorted by trackId.")
    if len(runtime_identity_hashes) != 1:
        raise ValueError("A runtime batch must use exactly one browser/runtime identity.")
    if sum(row["trackCount"] for row in source_rows) != len(tracks):
        raise ValueError("Runtime source manifest track counts do not cover the track set.")
    expected_track_set = canonical_sha256(
        [
            {"trackId": track["trackId"], "trackArtifactSha256": track["trackArtifactSha256"]}
            for track in tracks
        ]
    )
    if value.get("trackSetSha256") != expected_track_set:
        raise ValueError("Runtime track set hash is invalid.")

    if artifact_root is not None:
        root = _lexical_absolute(artifact_root)
        _reject_symlink_components(root, "artifact_root")
        if not root.is_dir():
            raise ValueError("artifact_root must be the emitted runtime manifest directory.")
        expected_files = {"manifest.json", *artifact_rows}
        actual_files = {path.name for path in root.iterdir()}
        if actual_files != expected_files:
            raise ValueError("artifact_root contains missing or unrelated files.")
        manifest_path = root / "manifest.json"
        if manifest_path.is_symlink() or manifest_path.read_text(encoding="utf-8") != _render_json(value):
            raise ValueError("artifact_root manifest bytes do not match the validated manifest.")
        timing_payloads: dict[str, Mapping[str, Any]] = {}
        for filename, artifact in artifact_rows.items():
            digest, timing = _validate_timing_artifact(root / filename)
            if digest != artifact["timingSha256"] or timing.get("contractSha256") != artifact[
                "timingContractSha256"
            ]:
                raise ValueError("artifact_root timing content does not match timingArtifacts.")
            timing_payloads[filename] = timing
        for track in tracks:
            _validate_runtime_timing_payload(
                timing_payloads[str(track["timingFile"])],
                timing_sha256=str(track["timingSha256"]),
                analyzer_contract_sha256=analyzer_contract_sha256,
                duration_seconds=float(track["durationSeconds"]),
                bar_count=int(track["barCount"]),
            )
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def _validate_destination(path: Path) -> None:
    _reject_symlink_components(path.parent, "Output destination")
    if path.is_symlink():
        raise ValueError("Output destinations may not be symbolic links.")
    if path.exists() and not path.is_file():
        raise ValueError("Output destinations must be regular files when they already exist.")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    _validate_destination(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(path.parent, "Output destination")
    if path.is_symlink():
        raise ValueError("Output destinations may not be symbolic links.")
    rendered = _render_json(value)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        _fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _generate_runtime_bar_grids(
    manifest_paths: Sequence[Path],
    output_dir: Path,
    *,
    provider: AnalysisProvider,
    expected_runtime_attestation: bool,
    replace_verified_set: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    timeout = _finite_number(timeout_seconds, "timeout_seconds", positive=True)
    if timeout > MAX_RUNNER_TIMEOUT_SECONDS:
        raise ValueError(
            f"timeout_seconds may not exceed {MAX_RUNNER_TIMEOUT_SECONDS:g} seconds."
        )

    # Split and field validation precede source, output, and audio path access.
    manifests = _load_and_validate_manifests(list(manifest_paths))
    output_state = _prepare_output_directory(
        output_dir,
        replace_verified_set=replace_verified_set,
    )
    if (
        output_state.previous_runtime_attested is not None
        and output_state.previous_runtime_attested is not expected_runtime_attestation
    ):
        raise ValueError("A verified output set may not change runtime attestation class.")
    contract = analyzer_contract()

    generated: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    source_manifest_rows: list[dict[str, Any]] = []
    attestation_mode: bool | None = None
    for manifest in manifests:
        source_manifest_sha256 = str(manifest["manifestSha256"])
        source_manifest_rows.append(
            {"sourceManifestSha256": source_manifest_sha256, "trackCount": len(manifest["tracks"])}
        )
        manifest_path = manifest["manifestPath"]
        for track in manifest["tracks"]:
            audio_path = _resolved_audio_path(manifest_path, str(track["audioPath"]))
            source_audio_sha256 = _sha256_file(audio_path)
            analysis = provider(audio_path, source_audio_sha256, contract, timeout)
            if _sha256_file(audio_path) != source_audio_sha256:
                raise ValueError(f"Runtime bar track {track['id']!r} changed during analysis.")
            runtime_attested = (
                isinstance(analysis, _AttestedBrowserAnalysis)
                and analysis.attestation is _RUNTIME_ATTESTATION
            )
            if runtime_attested is not expected_runtime_attestation:
                raise ValueError("The analysis provider does not match the required attestation class.")
            raw_output = analysis.raw if isinstance(analysis, _AttestedBrowserAnalysis) else analysis
            if attestation_mode is None:
                attestation_mode = runtime_attested
            elif attestation_mode != runtime_attested:
                raise ValueError("A timing batch may not mix attested runtime and offline-proxy rows.")
            validated = _validate_runner_output(raw_output, contract, source_audio_sha256)
            timing = _timing_from_validated(
                validated,
                contract,
                runtime_attested=runtime_attested,
            )
            timing_sha256 = canonical_sha256(timing)
            timing_filename = f"timing-{timing_sha256}.json"
            audio_binding = {
                "sourceAudioSha256": validated["sourceAudioSha256"],
                "decodedPcmSha256": validated["decodedPcmSha256"],
                "decodedPcmSampleCount": validated["decodedPcmSampleCount"],
                "decodedSampleRateHz": validated["decodedSampleRateHz"],
                "decodedChannelCount": validated["decodedChannelCount"],
                "decodedDurationSeconds": validated["decodedDurationSeconds"],
                "canonicalDurationMilliseconds": validated["canonicalDurationMilliseconds"],
                "analyzerPcmSha256": validated["analyzerPcmSha256"],
                "analyzerPcmSampleCount": validated["analyzerPcmSampleCount"],
                "analyzerSampleRateHz": validated["analyzerSampleRateHz"],
            }
            entry_payload: dict[str, Any] = {
                "trackId": track["id"],
                "split": DEVELOPMENT_SPLIT,
                "selectorUseAllowed": runtime_attested,
                "sourceManifestSha256": source_manifest_sha256,
                "audioSha256": source_audio_sha256,
                "audioBinding": audio_binding,
                "audioBindingSha256": canonical_sha256(audio_binding),
                "analysisVersion": validated["analysisVersion"],
                "runtimeIdentity": validated["runtimeIdentity"],
                "runtimeIdentitySha256": validated["runtimeIdentitySha256"],
                "timingFile": timing_filename,
                "timingSha256": timing_sha256,
                "timingContractSha256": timing["contractSha256"],
                "timingSourceContractSha256": timing["timingProvenance"]["barStartsSeconds"][
                    "sourceContractSha256"
                ],
                "durationSeconds": timing["durationSeconds"],
                "barCount": len(timing["barStartsSeconds"]),
            }
            entry = {**entry_payload, "trackArtifactSha256": canonical_sha256(entry_payload)}
            generated.append((str(track["id"]), timing, entry))
    if attestation_mode is None:
        raise ValueError("A runtime bar-grid batch cannot be empty.")

    generated.sort(key=lambda item: item[0])
    entries = [item[2] for item in generated]
    track_set_sha256 = canonical_sha256(
        [
            {"trackId": entry["trackId"], "trackArtifactSha256": entry["trackArtifactSha256"]}
            for entry in entries
        ]
    )
    source_manifest_rows.sort(key=lambda item: str(item["sourceManifestSha256"]))
    source_manifest_set_sha256 = canonical_sha256(source_manifest_rows)

    artifact_rows: dict[str, Mapping[str, Any]] = dict(output_state.verified_artifacts)
    timings_by_file: dict[str, Mapping[str, Any]] = {}
    for _track_id, timing, entry in generated:
        filename = str(entry["timingFile"])
        row = {
            "timingFile": filename,
            "timingSha256": entry["timingSha256"],
            "timingContractSha256": entry["timingContractSha256"],
        }
        existing = artifact_rows.get(filename)
        if existing is not None and dict(existing) != row:
            raise ValueError("A content-addressed timing filename collided with different content.")
        artifact_rows[filename] = row
        timings_by_file[filename] = timing
    timing_artifacts = [artifact_rows[key] for key in sorted(artifact_rows)]
    manifest_payload: dict[str, Any] = {
        "schemaVersion": OUTPUT_MANIFEST_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "selectorUseAllowed": attestation_mode,
        "runtimeAttested": attestation_mode,
        "analyzerContract": contract,
        "sourceManifestSetSha256": source_manifest_set_sha256,
        "sourceManifests": source_manifest_rows,
        "trackSetSha256": track_set_sha256,
        "timingArtifacts": timing_artifacts,
        "tracks": entries,
        "previousManifestSha256": output_state.previous_manifest_sha256,
    }
    output_manifest = {**manifest_payload, "manifestSha256": canonical_sha256(manifest_payload)}
    if attestation_mode:
        validate_runtime_bar_grid_manifest(output_manifest, verify_sources=True)

    new_destinations = [
        output_state.output_dir / filename
        for filename in sorted(timings_by_file)
        if filename not in output_state.verified_artifacts
    ]
    manifest_destination = output_state.output_dir / "manifest.json"
    for destination in [*new_destinations, manifest_destination]:
        _validate_destination(destination)
    # Content-addressed timing files are durable first. The manifest is the
    # sole commit point and is atomically replaced only after every timing file.
    for destination in new_destinations:
        _atomic_write_json(destination, timings_by_file[destination.name])
    _atomic_write_json(manifest_destination, output_manifest)
    if attestation_mode:
        validate_runtime_bar_grid_manifest(
            output_manifest,
            artifact_root=output_state.output_dir,
            verify_sources=True,
        )
    return output_manifest


def generate_runtime_bar_grids(
    manifest_paths: Sequence[Path],
    output_dir: Path,
    *,
    replace_verified_set: bool = False,
    timeout_seconds: float = DEFAULT_RUNNER_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Generate deployable timing using only the pinned target-browser harness."""

    return _generate_runtime_bar_grids(
        manifest_paths,
        output_dir,
        provider=_run_target_browser_analyzer,
        expected_runtime_attestation=True,
        replace_verified_set=replace_verified_set,
        timeout_seconds=timeout_seconds,
    )


def _generate_offline_proxy_bar_grids_for_tests(
    manifest_paths: Sequence[Path],
    output_dir: Path,
    *,
    provider: AnalysisProvider,
    replace_verified_set: bool = False,
    timeout_seconds: float = DEFAULT_RUNNER_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Exercise artifact mechanics without granting deployable runtime provenance."""

    return _generate_runtime_bar_grids(
        manifest_paths,
        output_dir,
        provider=provider,
        expected_runtime_attestation=False,
        replace_verified_set=replace_verified_set,
        timeout_seconds=timeout_seconds,
    )


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate development-only target-browser Play Along bar grids.",
    )
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        required=True,
        help=f"Explicit {INPUT_MANIFEST_SCHEMA} file; may be repeated.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--replace-verified-set",
        action="store_true",
        help="Replace only a fully verified prior content-addressed set; never unrelated files.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_RUNNER_TIMEOUT_SECONDS,
        help=f"Per-track browser timeout (maximum {MAX_RUNNER_TIMEOUT_SECONDS:g}).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    manifest = generate_runtime_bar_grids(
        args.manifest,
        args.output_dir,
        replace_verified_set=args.replace_verified_set,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(manifest, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0


__all__ = [
    "ANALYZER_CONTRACT_SCHEMA",
    "EXPLICIT_BAR_GRID_SCHEMA",
    "INPUT_MANIFEST_SCHEMA",
    "OUTPUT_MANIFEST_SCHEMA",
    "RUNNER_OUTPUT_SCHEMA",
    "SOURCE_ID",
    "analyzer_contract",
    "generate_runtime_bar_grids",
    "main",
    "validate_runtime_bar_grid_manifest",
]
