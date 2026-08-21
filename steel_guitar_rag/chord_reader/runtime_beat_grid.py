"""Sealed reference-free runtime beat-grid receipts.

This additive lane reruns the exact target-browser rhythm analyzer while
preserving the worker's original integer ``beatTimesMs`` and ``barStartsMs``.
Every receipt is reconciled to an already-attested runtime bar-grid v2 parent.
It does not inspect labels or predictions and cannot authorize a selector or
player publication.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import tempfile
from typing import Any

from .bar_promotion import canonical_sha256
from .runtime_bar_grid import (
    INPUT_MANIFEST_SCHEMA,
    OUTPUT_MANIFEST_SCHEMA as PARENT_MANIFEST_SCHEMA,
    _load_and_validate_manifests,
    _mapping,
    _reject_symlink_components,
    _render_json,
    _required_sha256,
    _resolved_audio_path,
    _sequence,
    _sha256_file,
    validate_runtime_bar_grid_manifest,
)


RUNNER_OUTPUT_SCHEMA = "chord_runtime_browser_beat_analyzer_output_v2"
ANALYZER_CONTRACT_SCHEMA = "chord_runtime_browser_beat_analyzer_contract_v1"
PLAYER_REPLAY_CONTRACT_SCHEMA = "chord_runtime_beat_player_replay_contract_v1"
OUTPUT_RECEIPT_SCHEMA = "chord_runtime_beat_grid_receipt_v1"
SOURCE_ID = "play-along-target-chrome-webaudio-rhythm-analysis-beats-v2"
OFFLINE_PROXY_SOURCE_ID = "unattested-browser-beat-fixture-proxy-v1"
DEVELOPMENT_SPLIT = "development"
CONFIDENCE_USE = "disclosure-only"
PUBLICATION_POLICY = {
    "mode": "relocatable-single-canonical-json",
    "pathBound": False,
    "commitPoint": "same-directory-hard-link-no-replace",
    "partialVisibleOutputAllowed": False,
}
DEFAULT_RUNNER_TIMEOUT_SECONDS = 300.0
MAX_RUNNER_TIMEOUT_SECONDS = 600.0
METER_PULSES = {"2/4": 2, "3/4": 3, "4/4": 4, "6/8": 6}

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASE_RUNNER = _REPO_ROOT / "scripts" / "chord_runtime_bar_analyzer.js"
_GENERATOR = Path(__file__).resolve()
_CLIENT_ALIAS = _REPO_ROOT / "ui" / "practice-analysis-client.js"
_CLIENT_RESOURCE = _REPO_ROOT / "ui" / "practice-analysis-client-audio-led-key-v11.js"
_WORKER_ALIAS = _REPO_ROOT / "ui" / "practice-analysis-worker.js"
_WORKER_RESOURCE = _REPO_ROOT / "ui" / "practice-analysis-worker-audio-led-key-v11.js"
_TOOLS_RESOURCE = _REPO_ROOT / "ui" / "practice-tools-key-regions-v1.js"
_SETUP_CALLER = _REPO_ROOT / "ui" / "setup-song-audio-led-key-v12.js"
_PLAY_CALLER_ALIAS = _REPO_ROOT / "ui" / "play-song.js"
_PLAY_CALLER_RESOURCE = _REPO_ROOT / "ui" / "play-song-analysis-calibration-v7.js"
_SETUP_DOCUMENT = _REPO_ROOT / "ui" / "setup-song.html"
_PLAY_DOCUMENT = _REPO_ROOT / "ui" / "play-song.html"
_HEX = frozenset("0123456789abcdef")
_ATTESTATION = object()

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
        "beatTimesMs",
        "barStartsMs",
        "meter",
        "beatsPerBar",
        "tempo",
        "tempoConfidence",
        "meterConfidence",
    }
)

_RECEIPT_KEYS = frozenset(
    {
        "schemaVersion",
        "split",
        "developmentOnly",
        "promotionEligible",
        "referenceFree",
        "runtimeAttested",
        "stage1UseAllowed",
        "selectorUseAllowed",
        "playerPlaybackUseAllowed",
        "confidenceUse",
        "publicationPolicy",
        "parentRuntimeBinding",
        "analyzerContract",
        "playerReplayContract",
        "sourceManifestSetSha256",
        "sourceManifests",
        "receiptTotals",
        "receiptTotalsSha256",
        "trackSetSha256",
        "tracks",
        "receiptSha256",
    }
)

_TRACK_KEYS = frozenset(
    {
        "trackId",
        "split",
        "referenceFree",
        "runtimeAttested",
        "stage1UseAllowed",
        "sourceManifestSha256",
        "parentTrackArtifactSha256",
        "audioSha256",
        "audioBinding",
        "audioBindingSha256",
        "analysisVersion",
        "runtimeIdentity",
        "runtimeIdentitySha256",
        "parentTimingBinding",
        "durationMilliseconds",
        "beatTimesMs",
        "barStartsMs",
        "meter",
        "beatsPerBar",
        "tempo",
        "tempoConfidence",
        "meterConfidence",
        "confidenceUse",
        "prefixExcludedMilliseconds",
        "tailIncludedMilliseconds",
        "terminalDownbeatCandidateSuppressed",
        "beatCount",
        "coveredDurationMilliseconds",
        "beatCells",
        "topologySha256",
        "beatAnalyzerContractSha256",
        "playerReplayContractSha256",
        "trackReceiptSha256",
    }
)


@dataclass(frozen=True)
class _AttestedBeatAnalysis:
    raw: Mapping[str, Any]
    attestation: object


@dataclass
class _OutputTarget:
    absolute_path: Path
    parent_fd: int
    parent_device: int
    parent_inode: int
    filename: str
    closed: bool = False

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            try:
                os.close(self.parent_fd)
            except OSError:
                pass

    def __del__(self) -> None:
        try:
            self.close()
        except OSError:
            pass


BeatProvider = Callable[
    [Path, str, Mapping[str, Any], float],
    Mapping[str, Any] | _AttestedBeatAnalysis,
]


def _finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        qualifier = "positive " if positive else ""
        raise ValueError(f"{name} must be a {qualifier}finite number.")
    return result


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _nonnegative_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer.")
    return value


def _integer_array(value: Any, name: str) -> list[int]:
    return [_nonnegative_integer(item, f"{name}[{index}]") for index, item in enumerate(_sequence(value, name))]


def _exact_replace(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"The frozen base runner {name} patch point drifted.")
    return source.replace(old, new, 1)


def _materialized_runner_source() -> str:
    """Build a deterministic additive v2 harness without editing the v1 runner."""

    source = _BASE_RUNNER.read_text(encoding="utf-8")
    source = _exact_replace(
        source,
        'const OUTPUT_SCHEMA = "chord_runtime_browser_bar_analyzer_output_v1";',
        f'const OUTPUT_SCHEMA = "{RUNNER_OUTPUT_SCHEMA}";',
        "output schema",
    )
    source = _exact_replace(
        source,
        'const SOURCE_ID = "play-along-target-chrome-webaudio-rhythm-analysis-v1";',
        f'const SOURCE_ID = "{SOURCE_ID}";',
        "source id",
    )
    source = _exact_replace(
        source,
        'const CLIENT_PATH = path.resolve(__dirname, "../ui/practice-analysis-client.js");',
        f"const CLIENT_PATH = {json.dumps(os.fspath(_CLIENT_ALIAS))};",
        "client path",
    )
    source = _exact_replace(
        source,
        'const WORKER_PATH = path.resolve(__dirname, "../ui/practice-analysis-worker.js");',
        f"const WORKER_PATH = {json.dumps(os.fspath(_WORKER_ALIAS))};",
        "worker path",
    )
    source = _exact_replace(
        source,
        "      beatTimesSeconds: (rhythm.beatTimesMs || []).map((value) => Number(value) / 1000),\n"
        "      barStartsSeconds: (rhythm.barStartsMs || []).map((value) => Number(value) / 1000),\n"
        '      meter: String(rhythm.meter || ""),\n'
        "      beatsPerBar: Number(rhythm.beatsPerBar),\n"
        "      tempo: Number(rhythm.tempo),",
        "      beatTimesMs: (rhythm.beatTimesMs || []).map((value) => Number(value)),\n"
        "      barStartsMs: (rhythm.barStartsMs || []).map((value) => Number(value)),\n"
        '      meter: String(rhythm.meter || ""),\n'
        "      beatsPerBar: Number(rhythm.beatsPerBar),\n"
        "      tempo: Number(rhythm.tempo),\n"
        "      tempoConfidence: Number(rhythm.tempoConfidence),\n"
        "      meterConfidence: Number(rhythm.meterConfidence),",
        "integer beat output",
    )
    return source


def _resource_row(role: str, path: Path) -> dict[str, str]:
    return {
        "role": role,
        "repoRelativePath": path.relative_to(_REPO_ROOT).as_posix(),
        "sha256": _sha256_file(path),
    }


def player_replay_contract() -> dict[str, Any]:
    """Bind the actual setup/player resources that retain and consume beats."""

    if _CLIENT_ALIAS.read_bytes() != _CLIENT_RESOURCE.read_bytes():
        raise RuntimeError("The analysis client alias is not the active setup resource.")
    if _WORKER_ALIAS.read_bytes() != _WORKER_RESOURCE.read_bytes():
        raise RuntimeError("The analysis worker alias is not the active client resource.")
    if _PLAY_CALLER_ALIAS.read_bytes() != _PLAY_CALLER_RESOURCE.read_bytes():
        raise RuntimeError("The Play Along caller alias is not the active player resource.")

    setup_html = _SETUP_DOCUMENT.read_text(encoding="utf-8")
    play_html = _PLAY_DOCUMENT.read_text(encoding="utf-8")
    expected_loads = (
        (_SETUP_DOCUMENT, _TOOLS_RESOURCE, setup_html),
        (_SETUP_DOCUMENT, _CLIENT_RESOURCE, setup_html),
        (_SETUP_DOCUMENT, _SETUP_CALLER, setup_html),
        (_PLAY_DOCUMENT, _TOOLS_RESOURCE, play_html),
        (_PLAY_DOCUMENT, _PLAY_CALLER_RESOURCE, play_html),
    )
    loads: list[dict[str, str]] = []
    for document, resource, source in expected_loads:
        route_match = re.search(
            rf'src="(/ui/{re.escape(resource.name)}\?v=[^"]+)"',
            source,
        )
        if route_match is None:
            raise RuntimeError("An active player resource route is absent from its document.")
        route = route_match.group(1)
        route_version_token = route.rsplit("?v=", 1)[1]
        resource_sha256 = _sha256_file(resource)
        loads.append(
            {
                "documentPath": document.relative_to(_REPO_ROOT).as_posix(),
                "documentSha256": _sha256_file(document),
                "resourcePath": resource.relative_to(_REPO_ROOT).as_posix(),
                "resourceSha256": resource_sha256,
                "documentRoute": route,
                "routeVersionToken": route_version_token,
                "routeVersionTokenMatchesResourceSha256": route_version_token == resource_sha256,
            }
        )

    client_source = _CLIENT_RESOURCE.read_text(encoding="utf-8")
    setup_source = _SETUP_CALLER.read_text(encoding="utf-8")
    play_source = _PLAY_CALLER_RESOURCE.read_text(encoding="utf-8")
    tools_source = _TOOLS_RESOURCE.read_text(encoding="utf-8")
    required_snippets = (
        (client_source, 'const WORKER_URL = "/ui/practice-analysis-worker-audio-led-key-v11.js";'),
        (setup_source, 'project.timeline = { ...result.analysis, confirmationState: "detected" };'),
        (play_source, "beatTimesMs: (timeline.beatTimesMs || []).map(Number)"),
        (tools_source, "if (Array.isArray(track?.beatTimesMs) && track.beatTimesMs.length) return track.beatTimesMs;"),
    )
    if any(snippet not in source for source, snippet in required_snippets):
        raise RuntimeError("The active player beat-retention caller semantics drifted.")

    resources = [
        _resource_row("analysis-client-alias", _CLIENT_ALIAS),
        _resource_row("analysis-client-active-resource", _CLIENT_RESOURCE),
        _resource_row("rhythm-worker-alias", _WORKER_ALIAS),
        _resource_row("rhythm-worker-active-resource", _WORKER_RESOURCE),
        _resource_row("setup-song-caller", _SETUP_CALLER),
        _resource_row("play-song-caller-alias", _PLAY_CALLER_ALIAS),
        _resource_row("play-song-active-resource", _PLAY_CALLER_RESOURCE),
        _resource_row("practice-tools-active-resource", _TOOLS_RESOURCE),
    ]
    resources.sort(key=lambda row: row["role"])
    loads.sort(key=lambda row: (row["documentPath"], row["resourcePath"]))
    payload: dict[str, Any] = {
        "schemaVersion": PLAYER_REPLAY_CONTRACT_SCHEMA,
        "resources": resources,
        "documentLoads": loads,
        "aliasBindings": [
            {
                "aliasPath": "ui/play-song.js",
                "activeResourcePath": "ui/play-song-analysis-calibration-v7.js",
                "byteIdentical": True,
            },
            {
                "aliasPath": "ui/practice-analysis-client.js",
                "activeResourcePath": "ui/practice-analysis-client-audio-led-key-v11.js",
                "byteIdentical": True,
            },
            {
                "aliasPath": "ui/practice-analysis-worker.js",
                "activeResourcePath": "ui/practice-analysis-worker-audio-led-key-v11.js",
                "byteIdentical": True,
            },
        ],
        "callerSemantics": {
            "analysisExport": "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis",
            "retainedFields": ["beatTimesMs", "barStartsMs"],
            "integerRoundTrip": "none",
            "setupPersistence": "result.analysis-spread-into-project.timeline",
            "playerLoad": "timeline.beatTimesMs.map(Number)",
            "playerPreference": "explicit-beatTimesMs-before-derived-bar-pulses",
            "cellTopology": "one-contiguous-cell-per-explicit-beat-through-canonical-duration",
        },
        "meterPulseMapping": METER_PULSES,
        "confidenceUse": CONFIDENCE_USE,
        "parityScope": "tracked-repository-resources-not-existing-browser-cache",
        "browserCacheParityAttested": False,
        "playerPlaybackUseAllowed": False,
    }
    return {**payload, "contractSha256": canonical_sha256(payload)}


def beat_analyzer_contract(parent_runtime_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return the additive beat analyzer bound to a validated v2 parent contract."""

    parent_contract = _mapping(parent_runtime_manifest.get("analyzerContract"), "parent analyzerContract")
    parent_implementation = _mapping(parent_contract.get("implementation"), "parent implementation")
    runner_source = _materialized_runner_source()
    payload: dict[str, Any] = {
        "schemaVersion": ANALYZER_CONTRACT_SCHEMA,
        "sourceId": SOURCE_ID,
        "parentAnalyzerContractSha256": _required_sha256(
            parent_contract.get("contractSha256"), "parent analyzer contract"
        ),
        "implementation": {
            "baseRunnerSha256": _sha256_file(_BASE_RUNNER),
            "beatRunnerSha256": hashlib.sha256(runner_source.encode("utf-8")).hexdigest(),
            "generatorSha256": _sha256_file(_GENERATOR),
            "clientSha256": _sha256_file(_CLIENT_ALIAS),
            "workerSha256": _sha256_file(_WORKER_ALIAS),
            "parentRunnerSha256": _required_sha256(parent_implementation.get("runnerSha256"), "parent runner sha256"),
            "decodeExport": "STEEL_RAG_ANALYSIS_CLIENT.decodeAudio",
            "monoExport": "STEEL_RAG_ANALYSIS_CLIENT.monoSamples",
            "downsampleExport": "STEEL_RAG_ANALYSIS_V2.downsample",
            "rhythmExport": "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis",
        },
        "runtime": json.loads(json.dumps(parent_contract["runtime"])),
        "decode": json.loads(json.dumps(parent_contract["decode"])),
        "audioInput": json.loads(json.dumps(parent_contract["audioInput"])),
        "outputAdapter": {
            "beatTimesDefinition": "original-rhythmAnalysis.beatTimesMs-integer-array",
            "barStartsDefinition": "original-rhythmAnalysis.barStartsMs-integer-array",
            "secondsRoundTrip": False,
            "confidenceUse": CONFIDENCE_USE,
            "meterPulseMapping": METER_PULSES,
        },
    }
    return {**payload, "contractSha256": canonical_sha256(payload)}


def _median(values: Sequence[int]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return float(ordered[middle]) if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def _expected_bar_topology(
    beat_times_ms: Sequence[int],
    duration_ms: int,
    beats_per_bar: int,
) -> tuple[list[int], bool]:
    candidates = list(beat_times_ms[::beats_per_bar])
    suppressed = False
    if len(candidates) > 1:
        typical = _median([right - left for left, right in zip(candidates, candidates[1:])])
        if duration_ms - candidates[-1] < typical * 0.4:
            candidates.pop()
            suppressed = True
    return candidates, suppressed


def _beat_topology(
    beat_times_ms: Sequence[int],
    bar_starts_ms: Sequence[int],
    duration_ms: int,
    beats_per_bar: int,
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    retained_bar_index = 0
    for index, start_ms in enumerate(beat_times_ms):
        while retained_bar_index + 1 < len(bar_starts_ms) and bar_starts_ms[retained_bar_index + 1] <= start_ms:
            retained_bar_index += 1
        end_ms = beat_times_ms[index + 1] if index + 1 < len(beat_times_ms) else duration_ms
        if end_ms <= start_ms:
            raise ValueError("Every runtime beat must produce one positive contiguous cell.")
        pulse_number = index % beats_per_bar + 1
        cells.append(
            {
                "beatIndex": index,
                "retainedBarIndex": retained_bar_index,
                "pulseNumber": pulse_number,
                "downbeatCandidate": pulse_number == 1,
                "startMs": start_ms,
                "endMs": end_ms,
                "durationMilliseconds": end_ms - start_ms,
            }
        )
    topology_payload = {
        "beatTimesMs": list(beat_times_ms),
        "barStartsMs": list(bar_starts_ms),
        "durationMilliseconds": duration_ms,
        "beatsPerBar": beats_per_bar,
        "beatCells": cells,
    }
    return {
        "beatCells": cells,
        "topologySha256": canonical_sha256(topology_payload),
        "prefixExcludedMilliseconds": beat_times_ms[0],
        "tailIncludedMilliseconds": duration_ms - beat_times_ms[-1],
        "beatCount": len(beat_times_ms),
        "coveredDurationMilliseconds": duration_ms - beat_times_ms[0],
    }


def _exact_milliseconds_from_seconds(value: Any, name: str) -> int:
    seconds = _finite_number(value, name)
    if seconds < 0:
        raise ValueError(f"{name} must be nonnegative.")
    try:
        milliseconds = Decimal(str(value)) * Decimal(1000)
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{name} is not an exact decimal millisecond value.") from error
    integral = milliseconds.to_integral_value()
    if milliseconds != integral:
        raise ValueError(f"{name} is not an exact integer-millisecond value.")
    return int(integral)


def _parent_timing_payload(parent_root: Path, track: Mapping[str, Any]) -> Mapping[str, Any]:
    filename = track.get("timingFile")
    if not isinstance(filename, str):
        raise ValueError("A parent runtime track has no timingFile.")
    path = parent_root / filename
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("A parent runtime timing artifact is unreadable.") from error
    timing = _mapping(payload, "parent runtime timing")
    if canonical_sha256(timing) != track.get("timingSha256"):
        raise ValueError("A parent runtime timing artifact hash is stale.")
    return timing


def _root_inventory(root: Path) -> tuple[list[dict[str, str]], str]:
    rows = [
        {"relativePath": path.name, "fileSha256": _sha256_file(path)}
        for path in sorted(root.iterdir(), key=lambda item: item.name)
    ]
    return rows, canonical_sha256(rows)


def _load_parent(
    parent_manifest_path: Path,
    parent_root: Path,
    *,
    verify_sources: bool,
) -> tuple[dict[str, Any], list[dict[str, str]], str]:
    lexical_root = Path(os.path.abspath(os.fspath(parent_root)))
    lexical_manifest = Path(os.path.abspath(os.fspath(parent_manifest_path)))
    _reject_symlink_components(lexical_root, "parent_runtime_root")
    _reject_symlink_components(lexical_manifest, "parent_runtime_manifest_path")
    root = lexical_root.resolve(strict=True)
    manifest_path = lexical_manifest.resolve(strict=True)
    if manifest_path != (root / "manifest.json").resolve(strict=True):
        raise ValueError("parent_runtime_manifest_path must be the exact parent_root/manifest.json.")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("The parent runtime manifest is unreadable.") from error
    preliminary = _mapping(raw, "parent runtime manifest")
    if preliminary.get("schemaVersion") != PARENT_MANIFEST_SCHEMA:
        raise ValueError("The parent runtime manifest must use the exact runtime bar-grid v2 schema.")
    if preliminary.get("split") != DEVELOPMENT_SPLIT:
        raise ValueError("Runtime beat receipts are development-only.")
    parent = validate_runtime_bar_grid_manifest(
        preliminary,
        artifact_root=root,
        verify_sources=verify_sources,
    )
    inventory, inventory_sha256 = _root_inventory(root)
    return parent, inventory, inventory_sha256


def _validate_runner_output(
    raw_output: Mapping[str, Any],
    contract: Mapping[str, Any],
    parent_track: Mapping[str, Any],
    parent_timing: Mapping[str, Any],
) -> dict[str, Any]:
    output = _mapping(raw_output, "target-browser beat harness output")
    if set(output) != _RUNNER_KEYS:
        raise ValueError("Beat harness output has missing or unsupported fields.")
    if output.get("schemaVersion") != RUNNER_OUTPUT_SCHEMA or output.get("sourceId") != SOURCE_ID:
        raise ValueError("Beat harness output uses the wrong schema or source identity.")

    implementation = _mapping(contract.get("implementation"), "beat analyzer implementation")
    runtime = _mapping(contract.get("runtime"), "beat analyzer runtime")
    expected_identity = {
        "browserExecutableSha256": runtime.get("browserExecutableSha256"),
        "clientSha256": implementation.get("clientSha256"),
        "nodeExecutableSha256": runtime.get("nodeExecutableSha256"),
        "runnerSha256": implementation.get("beatRunnerSha256"),
        "workerSha256": implementation.get("workerSha256"),
    }
    for name, expected in expected_identity.items():
        if _required_sha256(output.get(name), name) != expected:
            raise ValueError(f"Beat harness {name} does not match the additive contract.")
    if output.get("nodeVersion") != runtime.get("nodeVersion"):
        raise ValueError("Beat harness Node identity disagrees with the parent runtime.")
    if output.get("browserProduct") != f"Chrome/{runtime['browserVersion']}":
        raise ValueError("Beat harness browser identity disagrees with the parent runtime.")
    if output.get("browserLaunchContractSha256") != runtime.get("browserLaunchContractSha256"):
        raise ValueError("Beat harness launch contract disagrees with the parent runtime.")
    if output.get("networkRequestCount") != 0:
        raise ValueError("Beat harness attempted a forbidden secondary network read.")
    if output.get("secureContext") is not False or output.get("float32ByteOrder") != "little-endian":
        raise ValueError("Beat harness platform semantics disagree with the parent runtime.")

    parent_audio = _mapping(parent_track.get("audioBinding"), "parent audioBinding")
    raw_audio = {
        "sourceAudioSha256": _required_sha256(output.get("sourceAudioSha256"), "sourceAudioSha256"),
        "decodedPcmSha256": _required_sha256(output.get("decodedPcmSha256"), "decodedPcmSha256"),
        "decodedPcmSampleCount": _positive_integer(output.get("decodedPcmSampleCount"), "decodedPcmSampleCount"),
        "decodedSampleRateHz": _positive_integer(output.get("decodedSampleRateHz"), "decodedSampleRateHz"),
        "decodedChannelCount": _positive_integer(output.get("decodedChannelCount"), "decodedChannelCount"),
        "decodedDurationSeconds": _finite_number(
            output.get("decodedDurationSeconds"), "decodedDurationSeconds", positive=True
        ),
        "canonicalDurationMilliseconds": _positive_integer(
            output.get("canonicalDurationMilliseconds"), "canonicalDurationMilliseconds"
        ),
        "analyzerPcmSha256": _required_sha256(output.get("analyzerPcmSha256"), "analyzerPcmSha256"),
        "analyzerPcmSampleCount": _positive_integer(output.get("analyzerPcmSampleCount"), "analyzerPcmSampleCount"),
        "analyzerSampleRateHz": _positive_integer(output.get("analyzerSampleRateHz"), "analyzerSampleRateHz"),
    }
    if raw_audio != dict(parent_audio):
        raise ValueError("Beat harness audio/PCM/duration identity disagrees with the parent runtime.")
    if output.get("analysisVersion") != parent_track.get("analysisVersion"):
        raise ValueError("Beat harness analysisVersion disagrees with the parent runtime.")
    raw_runtime_identity = {
        name: output.get(name)
        for name in (
            "browserProduct",
            "browserRevision",
            "browserProtocolVersion",
            "browserJavaScriptVersion",
            "navigatorUserAgent",
            "navigatorPlatform",
            "nodeVersion",
        )
    }
    if raw_runtime_identity != dict(_mapping(parent_track.get("runtimeIdentity"), "parent runtimeIdentity")):
        raise ValueError("Beat harness runtime identity disagrees with the parent track.")

    duration_ms = raw_audio["canonicalDurationMilliseconds"]
    beat_times_ms = _integer_array(output.get("beatTimesMs"), "beatTimesMs")
    bar_starts_ms = _integer_array(output.get("barStartsMs"), "barStartsMs")
    if not beat_times_ms or not bar_starts_ms:
        raise ValueError("Beat harness must return nonempty beat and bar arrays.")
    for name, values in (("beatTimesMs", beat_times_ms), ("barStartsMs", bar_starts_ms)):
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"{name} must be strictly increasing.")
        if values[0] >= duration_ms or values[-1] >= duration_ms:
            raise ValueError(f"{name} contains an out-of-range value.")

    meter = output.get("meter")
    if not isinstance(meter, str) or meter not in METER_PULSES:
        raise ValueError("Beat harness returned an unsupported meter.")
    beats_per_bar = _positive_integer(output.get("beatsPerBar"), "beatsPerBar")
    if beats_per_bar != METER_PULSES[meter]:
        raise ValueError("Beat harness meter-to-pulse mapping is invalid.")
    expected_bars, suppressed = _expected_bar_topology(beat_times_ms, duration_ms, beats_per_bar)
    if bar_starts_ms != expected_bars:
        raise ValueError("Beat harness bar topology does not match the exact worker tail-pop rule.")

    parent_bar_starts = [
        _exact_milliseconds_from_seconds(value, "parent barStartsSeconds")
        for value in _sequence(parent_timing.get("barStartsSeconds"), "parent barStartsSeconds")
    ]
    if bar_starts_ms != parent_bar_starts:
        raise ValueError("Beat harness integer bar starts disagree with the exact parent timing leaf.")
    if duration_ms != _exact_milliseconds_from_seconds(parent_timing.get("durationSeconds"), "parent durationSeconds"):
        raise ValueError("Beat harness duration disagrees with the exact parent timing leaf.")
    parent_prefix = _exact_milliseconds_from_seconds(
        parent_timing.get("prefixExcludedSeconds", 0), "parent prefixExcludedSeconds"
    )
    if parent_prefix != beat_times_ms[0] or parent_prefix != bar_starts_ms[0]:
        raise ValueError("Beat harness prefix disagrees with the parent timing leaf.")

    tempo = _finite_number(output.get("tempo"), "tempo", positive=True)
    tempo_confidence = _finite_number(output.get("tempoConfidence"), "tempoConfidence")
    meter_confidence = _finite_number(output.get("meterConfidence"), "meterConfidence")
    if not 0 <= tempo_confidence <= 1 or not 0 <= meter_confidence <= 1:
        raise ValueError("Beat harness confidence disclosures must be in [0,1].")
    topology = _beat_topology(beat_times_ms, bar_starts_ms, duration_ms, beats_per_bar)
    return {
        "audioBinding": raw_audio,
        "runtimeIdentity": raw_runtime_identity,
        "analysisVersion": int(output["analysisVersion"]),
        "durationMilliseconds": duration_ms,
        "beatTimesMs": beat_times_ms,
        "barStartsMs": bar_starts_ms,
        "meter": meter,
        "beatsPerBar": beats_per_bar,
        "tempo": tempo,
        "tempoConfidence": tempo_confidence,
        "meterConfidence": meter_confidence,
        "terminalDownbeatCandidateSuppressed": suppressed,
        **topology,
    }


def _run_target_browser_beat_analyzer(
    audio_path: Path,
    audio_sha256: str,
    contract: Mapping[str, Any],
    timeout_seconds: float,
) -> _AttestedBeatAnalysis:
    implementation = _mapping(contract.get("implementation"), "beat analyzer implementation")
    runtime = _mapping(contract.get("runtime"), "beat analyzer runtime")
    runner_source = _materialized_runner_source()
    if hashlib.sha256(runner_source.encode("utf-8")).hexdigest() != implementation.get("beatRunnerSha256"):
        raise RuntimeError("The materialized beat runner changed after contract creation.")
    with tempfile.TemporaryDirectory(prefix="chord-runtime-beat-runner-") as temporary_root:
        runner_path = Path(temporary_root) / "chord_runtime_beat_analyzer.js"
        runner_path.write_text(runner_source, encoding="utf-8")
        command = [
            "node",
            os.fspath(runner_path),
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
            str(implementation["beatRunnerSha256"]),
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
            raise RuntimeError("The bounded target-browser beat harness could not complete.") from error
    if result.returncode != 0:
        message = result.stderr.strip() or "unknown target-browser beat harness error"
        raise RuntimeError(f"The target-browser beat harness failed: {message}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("The target-browser beat harness returned invalid JSON.") from error
    return _AttestedBeatAnalysis(raw=_mapping(payload, "beat harness output"), attestation=_ATTESTATION)


def _source_rows(manifests: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "sourceManifestSha256": str(manifest["manifestSha256"]),
            "trackCount": len(manifest["tracks"]),
        }
        for manifest in manifests
    ]
    rows.sort(key=lambda row: row["sourceManifestSha256"])
    return rows


def _parent_binding(
    parent: Mapping[str, Any],
    inventory: Sequence[Mapping[str, str]],
    inventory_sha256: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": PARENT_MANIFEST_SCHEMA,
        "manifestRelativePath": "manifest.json",
        "manifestSha256": parent["manifestSha256"],
        "manifestFileSha256": next(row["fileSha256"] for row in inventory if row["relativePath"] == "manifest.json"),
        "trackSetSha256": parent["trackSetSha256"],
        "sourceManifestSetSha256": parent["sourceManifestSetSha256"],
        "analyzerContractSha256": parent["analyzerContract"]["contractSha256"],
        "rootInventory": list(inventory),
        "rootInventorySha256": inventory_sha256,
    }


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _preflight_output_target(
    path: Path,
    *,
    forbidden_roots: Sequence[Path],
) -> _OutputTarget:
    absolute = Path(os.path.abspath(os.fspath(path)))
    if absolute.suffix.lower() != ".json":
        raise ValueError("Beat receipt output must be a new .json path.")
    _reject_symlink_components(absolute.parent, "beat receipt output")
    if not absolute.parent.is_dir():
        raise ValueError("Beat receipt output parent must already exist.")
    for raw_root in forbidden_roots:
        lexical_root = Path(os.path.abspath(os.fspath(raw_root)))
        _reject_symlink_components(lexical_root, "beat receipt forbidden root")
        root = lexical_root.resolve(strict=True)
        if _is_within(absolute, root):
            raise ValueError("Beat receipt output must be disjoint from parent and source roots.")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_fd = os.open(absolute.parent, flags)
    except OSError as error:
        raise ValueError("Beat receipt output parent could not be retained safely.") from error
    try:
        retained = os.fstat(parent_fd)
        lexical = os.stat(absolute.parent, follow_symlinks=False)
        if (retained.st_dev, retained.st_ino) != (lexical.st_dev, lexical.st_ino):
            raise ValueError("Beat receipt output parent changed during preflight.")
        try:
            os.stat(absolute.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("Beat receipt output must use a new path.")
        return _OutputTarget(
            absolute_path=absolute,
            parent_fd=parent_fd,
            parent_device=retained.st_dev,
            parent_inode=retained.st_ino,
            filename=absolute.name,
        )
    except BaseException:
        os.close(parent_fd)
        raise


def _atomic_publish_new_json(target: _OutputTarget, value: Mapping[str, Any]) -> None:
    if target.closed:
        raise RuntimeError("Beat receipt output target is already closed.")
    rendered = _render_json(value)
    temporary_name = f".{target.filename}.{secrets.token_hex(16)}"
    descriptor = -1
    owned_identity: tuple[int, int] | None = None
    temporary_exists = False
    try:
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=target.parent_fd,
        )
        temporary_stat = os.fstat(descriptor)
        owned_identity = (temporary_stat.st_dev, temporary_stat.st_ino)
        temporary_exists = True
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=True) as handle:
            descriptor = -1
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(
            temporary_name,
            target.filename,
            src_dir_fd=target.parent_fd,
            dst_dir_fd=target.parent_fd,
            follow_symlinks=False,
        )
        os.unlink(temporary_name, dir_fd=target.parent_fd)
        temporary_exists = False
        os.fsync(target.parent_fd)
        retained = os.fstat(target.parent_fd)
        lexical = os.stat(target.absolute_path.parent, follow_symlinks=False)
        published = os.stat(target.filename, dir_fd=target.parent_fd, follow_symlinks=False)
        if (retained.st_dev, retained.st_ino) != (
            target.parent_device,
            target.parent_inode,
        ) or (lexical.st_dev, lexical.st_ino) != (
            target.parent_device,
            target.parent_inode,
        ):
            raise RuntimeError("Beat receipt output parent changed at publication.")
        if (published.st_dev, published.st_ino) != owned_identity:
            raise RuntimeError("Beat receipt destination is not the owned published inode.")
        published_fd = os.open(
            target.filename,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=target.parent_fd,
        )
        with os.fdopen(published_fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            published_bytes = handle.read()
        if (opened.st_dev, opened.st_ino) != owned_identity:
            raise RuntimeError("Beat receipt reopened destination is not the owned inode.")
        if published_bytes != rendered.encode("utf-8"):
            raise RuntimeError("Published beat receipt bytes changed at the commit point.")
    except BaseException:
        if owned_identity is not None:
            try:
                published = os.stat(
                    target.filename,
                    dir_fd=target.parent_fd,
                    follow_symlinks=False,
                )
                if (published.st_dev, published.st_ino) == owned_identity:
                    os.unlink(target.filename, dir_fd=target.parent_fd)
                    os.fsync(target.parent_fd)
            except OSError:
                pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            if temporary_exists:
                try:
                    os.unlink(temporary_name, dir_fd=target.parent_fd)
                except OSError:
                    pass
        finally:
            target.close()


def _validate_player_contract_claim(raw: Any, *, verify_sources: bool) -> Mapping[str, Any]:
    contract = _mapping(raw, "playerReplayContract")
    expected_top = {
        "schemaVersion",
        "resources",
        "documentLoads",
        "aliasBindings",
        "callerSemantics",
        "meterPulseMapping",
        "confidenceUse",
        "parityScope",
        "browserCacheParityAttested",
        "playerPlaybackUseAllowed",
        "contractSha256",
    }
    if set(contract) != expected_top or contract.get("schemaVersion") != PLAYER_REPLAY_CONTRACT_SCHEMA:
        raise ValueError("playerReplayContract uses an unsupported schema.")
    claimed = _required_sha256(contract.get("contractSha256"), "playerReplayContract hash")
    payload = {key: value for key, value in contract.items() if key != "contractSha256"}
    if canonical_sha256(payload) != claimed:
        raise ValueError("playerReplayContract hash is stale.")
    if contract.get("meterPulseMapping") != METER_PULSES or contract.get("confidenceUse") != CONFIDENCE_USE:
        raise ValueError("playerReplayContract changed the frozen meter or confidence policy.")
    if (
        contract.get("parityScope") != "tracked-repository-resources-not-existing-browser-cache"
        or contract.get("browserCacheParityAttested") is not False
        or contract.get("playerPlaybackUseAllowed") is not False
    ):
        raise ValueError("playerReplayContract overclaims browser-cache or playback parity.")
    expected_resource_identities = sorted(
        (
            ("analysis-client-alias", "ui/practice-analysis-client.js"),
            (
                "analysis-client-active-resource",
                "ui/practice-analysis-client-audio-led-key-v11.js",
            ),
            ("rhythm-worker-alias", "ui/practice-analysis-worker.js"),
            (
                "rhythm-worker-active-resource",
                "ui/practice-analysis-worker-audio-led-key-v11.js",
            ),
            ("setup-song-caller", "ui/setup-song-audio-led-key-v12.js"),
            ("play-song-caller-alias", "ui/play-song.js"),
            (
                "play-song-active-resource",
                "ui/play-song-analysis-calibration-v7.js",
            ),
            ("practice-tools-active-resource", "ui/practice-tools-key-regions-v1.js"),
        )
    )
    resources = [
        dict(_mapping(row, "player resource row")) for row in _sequence(contract.get("resources"), "player resources")
    ]
    if any(set(row) != {"role", "repoRelativePath", "sha256"} for row in resources):
        raise ValueError("playerReplayContract resource rows have unsupported fields.")
    for row in resources:
        _required_sha256(row.get("sha256"), "player resource sha256")
    if [(row.get("role"), row.get("repoRelativePath")) for row in resources] != expected_resource_identities:
        raise ValueError("playerReplayContract resource inventory is stale or unordered.")
    resource_hashes = {str(row["repoRelativePath"]): str(row["sha256"]) for row in resources}
    expected_load_identities = sorted(
        (
            ("ui/play-song.html", "ui/play-song-analysis-calibration-v7.js"),
            ("ui/play-song.html", "ui/practice-tools-key-regions-v1.js"),
            ("ui/setup-song.html", "ui/practice-analysis-client-audio-led-key-v11.js"),
            ("ui/setup-song.html", "ui/practice-tools-key-regions-v1.js"),
            ("ui/setup-song.html", "ui/setup-song-audio-led-key-v12.js"),
        )
    )
    loads = [
        dict(_mapping(row, "player document load"))
        for row in _sequence(contract.get("documentLoads"), "player documentLoads")
    ]
    load_keys = {
        "documentPath",
        "documentSha256",
        "resourcePath",
        "resourceSha256",
        "documentRoute",
        "routeVersionToken",
        "routeVersionTokenMatchesResourceSha256",
    }
    if any(set(row) != load_keys for row in loads):
        raise ValueError("playerReplayContract document load rows have unsupported fields.")
    for row in loads:
        _required_sha256(row.get("documentSha256"), "player document sha256")
        resource_sha = _required_sha256(row.get("resourceSha256"), "loaded resource sha256")
        token = row.get("routeVersionToken")
        route = row.get("documentRoute")
        resource_path = row.get("resourcePath")
        expected_route = (
            f"/ui/{Path(resource_path).name}?v={token}"
            if isinstance(resource_path, str) and isinstance(token, str)
            else None
        )
        if (
            not isinstance(token, str)
            or len(token) != 64
            or any(character not in _HEX for character in token)
            or not isinstance(route, str)
            or route != expected_route
            or row.get("routeVersionTokenMatchesResourceSha256") is not (token == resource_sha)
        ):
            raise ValueError("playerReplayContract route disclosure is internally inconsistent.")
    if [(row.get("documentPath"), row.get("resourcePath")) for row in loads] != expected_load_identities:
        raise ValueError("playerReplayContract document load inventory is stale or unordered.")
    document_hashes: dict[str, str] = {}
    for row in loads:
        if row["resourceSha256"] != resource_hashes.get(str(row["resourcePath"])):
            raise ValueError("playerReplayContract document load does not bind its resource inventory.")
        prior_document_hash = document_hashes.setdefault(str(row["documentPath"]), str(row["documentSha256"]))
        if prior_document_hash != row["documentSha256"]:
            raise ValueError("playerReplayContract repeats a document with inconsistent bytes.")
    expected_aliases = [
        {
            "aliasPath": "ui/play-song.js",
            "activeResourcePath": "ui/play-song-analysis-calibration-v7.js",
            "byteIdentical": True,
        },
        {
            "aliasPath": "ui/practice-analysis-client.js",
            "activeResourcePath": "ui/practice-analysis-client-audio-led-key-v11.js",
            "byteIdentical": True,
        },
        {
            "aliasPath": "ui/practice-analysis-worker.js",
            "activeResourcePath": "ui/practice-analysis-worker-audio-led-key-v11.js",
            "byteIdentical": True,
        },
    ]
    aliases = [
        dict(_mapping(row, "player alias row"))
        for row in _sequence(contract.get("aliasBindings"), "player aliasBindings")
    ]
    if aliases != expected_aliases:
        raise ValueError("playerReplayContract alias bindings are stale.")
    for row in aliases:
        if resource_hashes.get(row["aliasPath"]) != resource_hashes.get(row["activeResourcePath"]):
            raise ValueError("playerReplayContract byte-identical alias hashes disagree.")
    expected_semantics = {
        "analysisExport": "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis",
        "retainedFields": ["beatTimesMs", "barStartsMs"],
        "integerRoundTrip": "none",
        "setupPersistence": "result.analysis-spread-into-project.timeline",
        "playerLoad": "timeline.beatTimesMs.map(Number)",
        "playerPreference": "explicit-beatTimesMs-before-derived-bar-pulses",
        "cellTopology": "one-contiguous-cell-per-explicit-beat-through-canonical-duration",
    }
    if contract.get("callerSemantics") != expected_semantics:
        raise ValueError("playerReplayContract caller semantics are stale.")
    if verify_sources and dict(contract) != player_replay_contract():
        raise ValueError("playerReplayContract does not match the current player resources.")
    return contract


def _validate_analyzer_contract_claim(
    raw: Any,
    parent: Mapping[str, Any],
    *,
    verify_sources: bool,
) -> Mapping[str, Any]:
    contract = _mapping(raw, "analyzerContract")
    required = {
        "schemaVersion",
        "sourceId",
        "parentAnalyzerContractSha256",
        "implementation",
        "runtime",
        "decode",
        "audioInput",
        "outputAdapter",
        "contractSha256",
    }
    if set(contract) != required or contract.get("schemaVersion") != ANALYZER_CONTRACT_SCHEMA:
        raise ValueError("Beat analyzerContract does not match the exact schema.")
    if contract.get("sourceId") != SOURCE_ID:
        raise ValueError("Beat analyzerContract uses the wrong source identity.")
    claimed = _required_sha256(contract.get("contractSha256"), "analyzerContract hash")
    payload = {key: value for key, value in contract.items() if key != "contractSha256"}
    if canonical_sha256(payload) != claimed:
        raise ValueError("Beat analyzerContract hash is stale.")
    parent_contract = _mapping(parent.get("analyzerContract"), "parent analyzerContract")
    if contract.get("parentAnalyzerContractSha256") != parent_contract.get("contractSha256"):
        raise ValueError("Beat analyzerContract does not bind the parent analyzer.")
    adapter = _mapping(contract.get("outputAdapter"), "beat outputAdapter")
    expected_adapter = {
        "beatTimesDefinition": "original-rhythmAnalysis.beatTimesMs-integer-array",
        "barStartsDefinition": "original-rhythmAnalysis.barStartsMs-integer-array",
        "secondsRoundTrip": False,
        "confidenceUse": CONFIDENCE_USE,
        "meterPulseMapping": METER_PULSES,
    }
    if dict(adapter) != expected_adapter:
        raise ValueError("Beat analyzerContract does not retain original integer timing.")
    implementation = _mapping(contract.get("implementation"), "beat analyzer implementation")
    implementation_keys = {
        "baseRunnerSha256",
        "beatRunnerSha256",
        "generatorSha256",
        "clientSha256",
        "workerSha256",
        "parentRunnerSha256",
        "decodeExport",
        "monoExport",
        "downsampleExport",
        "rhythmExport",
    }
    if set(implementation) != implementation_keys:
        raise ValueError("Beat analyzer implementation binding is incomplete.")
    for name in (
        "baseRunnerSha256",
        "beatRunnerSha256",
        "generatorSha256",
        "clientSha256",
        "workerSha256",
        "parentRunnerSha256",
    ):
        _required_sha256(implementation.get(name), f"beat analyzer {name}")
    parent_implementation = _mapping(parent_contract.get("implementation"), "parent implementation")
    if (
        implementation.get("baseRunnerSha256") != parent_implementation.get("runnerSha256")
        or implementation.get("parentRunnerSha256") != parent_implementation.get("runnerSha256")
        or implementation.get("clientSha256") != parent_implementation.get("clientSha256")
        or implementation.get("workerSha256") != parent_implementation.get("workerSha256")
    ):
        raise ValueError("Beat analyzer implementation disagrees with its parent analyzer.")
    expected_exports = {
        "decodeExport": "STEEL_RAG_ANALYSIS_CLIENT.decodeAudio",
        "monoExport": "STEEL_RAG_ANALYSIS_CLIENT.monoSamples",
        "downsampleExport": "STEEL_RAG_ANALYSIS_V2.downsample",
        "rhythmExport": "STEEL_RAG_ANALYSIS_V2.rhythmAnalysis",
    }
    if any(implementation.get(name) != expected for name, expected in expected_exports.items()):
        raise ValueError("Beat analyzer implementation exports are stale.")
    for name in ("runtime", "decode", "audioInput"):
        child = _mapping(contract.get(name), f"beat analyzer {name}")
        parent_value = _mapping(parent_contract.get(name), f"parent analyzer {name}")
        if dict(child) != dict(parent_value):
            raise ValueError(f"Beat analyzer {name} policy disagrees with its parent.")
    if verify_sources and dict(contract) != beat_analyzer_contract(parent):
        raise ValueError("Beat analyzerContract does not match current additive sources.")
    return contract


def _validate_receipt(
    receipt: Mapping[str, Any],
    *,
    parent: Mapping[str, Any],
    parent_root: Path,
    receipt_path: Path | None,
    verify_sources: bool,
    require_runtime_attested: bool,
) -> dict[str, Any]:
    value = _mapping(receipt, "runtime beat-grid receipt")
    if set(value) != _RECEIPT_KEYS or value.get("schemaVersion") != OUTPUT_RECEIPT_SCHEMA:
        raise ValueError("Runtime beat-grid receipt does not match the exact schema.")
    if value.get("split") != DEVELOPMENT_SPLIT or value.get("developmentOnly") is not True:
        raise ValueError("Runtime beat-grid receipt is not development-only.")
    if value.get("promotionEligible") is not False or value.get("referenceFree") is not True:
        raise ValueError("Runtime beat-grid receipt changed its sealed development envelope.")
    attested = value.get("runtimeAttested")
    if not isinstance(attested, bool) or value.get("stage1UseAllowed") is not attested:
        raise ValueError("Runtime beat-grid attestation flags are inconsistent.")
    if require_runtime_attested and not attested:
        raise ValueError("Runtime beat-grid receipt is not attested for Stage-1 use.")
    if value.get("selectorUseAllowed") is not False or value.get("playerPlaybackUseAllowed") is not False:
        raise ValueError("Beat receipts cannot authorize selector or player publication.")
    if value.get("confidenceUse") != CONFIDENCE_USE:
        raise ValueError("Beat confidence is not disclosure-only.")
    if value.get("publicationPolicy") != PUBLICATION_POLICY:
        raise ValueError("Beat receipt changed its frozen relocatable publication policy.")
    claimed_receipt = _required_sha256(value.get("receiptSha256"), "receiptSha256")
    payload = {key: item for key, item in value.items() if key != "receiptSha256"}
    if canonical_sha256(payload) != claimed_receipt:
        raise ValueError("Runtime beat-grid receipt hash is stale.")

    analyzer = _validate_analyzer_contract_claim(value.get("analyzerContract"), parent, verify_sources=verify_sources)
    player = _validate_player_contract_claim(value.get("playerReplayContract"), verify_sources=verify_sources)
    parent_inventory, parent_inventory_sha256 = _root_inventory(parent_root)
    expected_parent_binding = _parent_binding(parent, parent_inventory, parent_inventory_sha256)
    if value.get("parentRuntimeBinding") != expected_parent_binding:
        raise ValueError("Beat receipt does not bind the exact parent manifest/root inventory.")

    raw_source_rows = _sequence(value.get("sourceManifests"), "sourceManifests")
    source_rows = [dict(_mapping(row, "source manifest row")) for row in raw_source_rows]
    if source_rows != sorted(source_rows, key=lambda row: row.get("sourceManifestSha256", "")):
        raise ValueError("Beat source manifest rows are not canonically sorted.")
    for row in source_rows:
        if set(row) != {"sourceManifestSha256", "trackCount"}:
            raise ValueError("Beat source manifest rows have unsupported fields.")
        _required_sha256(row.get("sourceManifestSha256"), "sourceManifestSha256")
        _positive_integer(row.get("trackCount"), "source manifest trackCount")
    if canonical_sha256(source_rows) != value.get("sourceManifestSetSha256"):
        raise ValueError("Beat source manifest set hash is stale.")
    if source_rows != parent.get("sourceManifests"):
        raise ValueError("Beat source manifests disagree with the parent runtime.")

    parent_tracks = {str(track["trackId"]): track for track in _sequence(parent.get("tracks"), "parent tracks")}
    raw_tracks = _sequence(value.get("tracks"), "tracks")
    tracks = [dict(_mapping(track, "beat receipt track")) for track in raw_tracks]
    if not tracks or [track.get("trackId") for track in tracks] != sorted(parent_tracks):
        raise ValueError("Beat receipt tracks do not exactly cover sorted parent tracks.")
    validated_tracks: list[dict[str, Any]] = []
    for track in tracks:
        if set(track) != _TRACK_KEYS:
            raise ValueError("Beat receipt track does not match the exact contract.")
        track_id = str(track["trackId"])
        parent_track = parent_tracks[track_id]
        if track.get("split") != DEVELOPMENT_SPLIT or track.get("referenceFree") is not True:
            raise ValueError("Every beat receipt track must be reference-free development data.")
        if track.get("runtimeAttested") is not attested or track.get("stage1UseAllowed") is not attested:
            raise ValueError("Beat receipt track attestation flags are inconsistent.")
        identity_fields = (
            "sourceManifestSha256",
            "audioSha256",
            "audioBinding",
            "audioBindingSha256",
            "analysisVersion",
            "runtimeIdentity",
            "runtimeIdentitySha256",
        )
        if any(track.get(name) != parent_track.get(name) for name in identity_fields):
            raise ValueError("Beat receipt audio/PCM/runtime identity disagrees with its parent track.")
        if track.get("parentTrackArtifactSha256") != parent_track.get("trackArtifactSha256"):
            raise ValueError("Beat receipt parent track hash is stale.")
        parent_timing = _parent_timing_payload(parent_root, parent_track)
        expected_timing_binding = {
            "timingFile": parent_track["timingFile"],
            "timingSha256": parent_track["timingSha256"],
            "timingContractSha256": parent_track["timingContractSha256"],
            "timingSourceContractSha256": parent_track["timingSourceContractSha256"],
            "barCount": parent_track["barCount"],
        }
        if track.get("parentTimingBinding") != expected_timing_binding:
            raise ValueError("Beat receipt parent timing binding is stale.")
        duration_ms = _positive_integer(track.get("durationMilliseconds"), "durationMilliseconds")
        if duration_ms != parent_track["audioBinding"]["canonicalDurationMilliseconds"]:
            raise ValueError("Beat receipt duration disagrees with its parent audio binding.")
        beats = _integer_array(track.get("beatTimesMs"), "beatTimesMs")
        bars = _integer_array(track.get("barStartsMs"), "barStartsMs")
        if not beats or not bars:
            raise ValueError("Beat receipt requires nonempty beat and bar arrays.")
        for name, values in (("beatTimesMs", beats), ("barStartsMs", bars)):
            if any(right <= left for left, right in zip(values, values[1:])):
                raise ValueError(f"Beat receipt {name} must be strictly increasing.")
            if values[0] >= duration_ms or values[-1] >= duration_ms:
                raise ValueError(f"Beat receipt {name} contains an out-of-range value.")
        meter = track.get("meter")
        beats_per_bar = _positive_integer(track.get("beatsPerBar"), "beatsPerBar")
        if not isinstance(meter, str) or METER_PULSES.get(meter) != beats_per_bar:
            raise ValueError("Beat receipt meter-to-pulse mapping is invalid.")
        expected_bars, suppressed = _expected_bar_topology(beats, duration_ms, beats_per_bar)
        if bars != expected_bars or track.get("terminalDownbeatCandidateSuppressed") is not suppressed:
            raise ValueError("Beat receipt topology disagrees with the exact worker tail-pop rule.")
        parent_bars = [
            _exact_milliseconds_from_seconds(item, "parent barStartsSeconds")
            for item in parent_timing["barStartsSeconds"]
        ]
        if bars != parent_bars:
            raise ValueError("Beat receipt bars disagree with the parent timing leaf.")
        topology = _beat_topology(beats, bars, duration_ms, beats_per_bar)
        for name, expected in topology.items():
            if track.get(name) != expected:
                raise ValueError(f"Beat receipt {name} is stale.")
        if track.get("confidenceUse") != CONFIDENCE_USE:
            raise ValueError("Track confidence use is not disclosure-only.")
        _finite_number(track.get("tempo"), "tempo", positive=True)
        for name in ("tempoConfidence", "meterConfidence"):
            confidence = _finite_number(track.get(name), name)
            if not 0 <= confidence <= 1:
                raise ValueError("Beat confidence disclosures must be in [0,1].")
        if track.get("beatAnalyzerContractSha256") != analyzer.get("contractSha256"):
            raise ValueError("Beat track does not bind the additive analyzer contract.")
        if track.get("playerReplayContractSha256") != player.get("contractSha256"):
            raise ValueError("Beat track does not bind the player replay contract.")
        claimed_track = _required_sha256(track.get("trackReceiptSha256"), "trackReceiptSha256")
        track_payload = {key: item for key, item in track.items() if key != "trackReceiptSha256"}
        if canonical_sha256(track_payload) != claimed_track:
            raise ValueError("Beat track receipt hash is stale.")
        validated_tracks.append(track)

    expected_track_set = canonical_sha256(
        [{"trackId": track["trackId"], "trackReceiptSha256": track["trackReceiptSha256"]} for track in validated_tracks]
    )
    if value.get("trackSetSha256") != expected_track_set:
        raise ValueError("Beat receipt track-set hash is stale.")
    totals = {
        "trackCount": len(validated_tracks),
        "beatCellCount": sum(track["beatCount"] for track in validated_tracks),
        "sourceDurationMilliseconds": sum(track["durationMilliseconds"] for track in validated_tracks),
        "coveredDurationMilliseconds": sum(track["coveredDurationMilliseconds"] for track in validated_tracks),
        "excludedPrefixDurationMilliseconds": sum(track["prefixExcludedMilliseconds"] for track in validated_tracks),
    }
    if value.get("receiptTotals") != totals or value.get("receiptTotalsSha256") != canonical_sha256(totals):
        raise ValueError("Beat receipt aggregate count/duration totals are stale.")

    if receipt_path is not None:
        lexical_path = Path(os.path.abspath(os.fspath(receipt_path)))
        _reject_symlink_components(lexical_path, "receipt_path")
        try:
            descriptor = os.open(
                lexical_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as error:
            raise ValueError("Beat receipt path must be a regular non-symlink file.") from error
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError("Beat receipt path must be a regular non-symlink file.")
            rendered_receipt = handle.read()
        if rendered_receipt != _render_json(value):
            raise ValueError("Beat receipt file bytes do not match the canonical receipt.")
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def validate_runtime_beat_grid_receipt(
    receipt: Mapping[str, Any],
    *,
    parent_runtime_manifest: Mapping[str, Any],
    parent_runtime_root: Path,
    receipt_path: Path | None = None,
    verify_sources: bool = True,
) -> dict[str, Any]:
    """Strictly validate an attested development beat receipt and its v2 parent."""

    lexical_root = Path(os.path.abspath(os.fspath(parent_runtime_root)))
    parent, _inventory, _inventory_sha256 = _load_parent(
        lexical_root / "manifest.json",
        lexical_root,
        verify_sources=verify_sources,
    )
    if dict(parent_runtime_manifest) != parent:
        raise ValueError("parent_runtime_manifest does not equal canonical parent_root/manifest.json bytes.")
    return _validate_receipt(
        receipt,
        parent=parent,
        parent_root=parent_runtime_root.resolve(strict=True),
        receipt_path=receipt_path,
        verify_sources=verify_sources,
        require_runtime_attested=True,
    )


def _generate_runtime_beat_grid_receipt_after_preflight(
    manifests: Sequence[Mapping[str, Any]],
    parent_runtime_manifest_path: Path,
    parent_runtime_root: Path,
    output_target: _OutputTarget,
    *,
    provider: BeatProvider,
    expected_runtime_attestation: bool,
    timeout: float,
) -> dict[str, Any]:
    parent, inventory, inventory_sha256 = _load_parent(
        parent_runtime_manifest_path,
        parent_runtime_root,
        verify_sources=True,
    )
    source_rows = _source_rows(manifests)
    if source_rows != parent.get("sourceManifests"):
        raise ValueError("Audio manifests do not exactly match the parent runtime source set.")
    if canonical_sha256(source_rows) != parent.get("sourceManifestSetSha256"):
        raise ValueError("Audio manifest-set hash disagrees with the parent runtime.")

    contract = beat_analyzer_contract(parent)
    player_contract = player_replay_contract()
    parent_tracks = {str(track["trackId"]): track for track in parent["tracks"]}
    generated: list[dict[str, Any]] = []
    input_state: list[tuple[Path, str]] = []
    audio_resolution_state: list[tuple[Path, str, Path, str]] = []
    seen_tracks: set[str] = set()
    for manifest in manifests:
        manifest_path = Path(manifest["manifestPath"])
        input_state.append((manifest_path, _sha256_file(manifest_path)))
        for source_track in manifest["tracks"]:
            track_id = str(source_track["id"])
            if track_id in seen_tracks or track_id not in parent_tracks:
                raise ValueError("Audio manifests do not exactly cover unique parent track ids.")
            seen_tracks.add(track_id)
            parent_track = parent_tracks[track_id]
            if parent_track.get("sourceManifestSha256") != manifest["manifestSha256"]:
                raise ValueError("A beat input track is bound to the wrong parent source manifest.")
            audio_path = _resolved_audio_path(manifest_path, str(source_track["audioPath"]))
            audio_sha256 = _sha256_file(audio_path)
            if audio_sha256 != parent_track.get("audioSha256"):
                raise ValueError("A beat input audio file disagrees with the parent runtime bytes.")
            input_state.append((audio_path, audio_sha256))
            audio_resolution_state.append((manifest_path, str(source_track["audioPath"]), audio_path, audio_sha256))
            analysis = provider(audio_path, audio_sha256, contract, timeout)
            if _sha256_file(audio_path) != audio_sha256:
                raise ValueError("A beat input audio file changed during analysis.")
            runtime_attested = isinstance(analysis, _AttestedBeatAnalysis) and analysis.attestation is _ATTESTATION
            if runtime_attested is not expected_runtime_attestation:
                raise ValueError("Beat analysis provider does not match the required attestation class.")
            raw = analysis.raw if isinstance(analysis, _AttestedBeatAnalysis) else analysis
            parent_timing = _parent_timing_payload(parent_runtime_root, parent_track)
            validated = _validate_runner_output(raw, contract, parent_track, parent_timing)
            parent_timing_binding = {
                "timingFile": parent_track["timingFile"],
                "timingSha256": parent_track["timingSha256"],
                "timingContractSha256": parent_track["timingContractSha256"],
                "timingSourceContractSha256": parent_track["timingSourceContractSha256"],
                "barCount": parent_track["barCount"],
            }
            track_payload: dict[str, Any] = {
                "trackId": track_id,
                "split": DEVELOPMENT_SPLIT,
                "referenceFree": True,
                "runtimeAttested": runtime_attested,
                "stage1UseAllowed": runtime_attested,
                "sourceManifestSha256": parent_track["sourceManifestSha256"],
                "parentTrackArtifactSha256": parent_track["trackArtifactSha256"],
                "audioSha256": parent_track["audioSha256"],
                "audioBinding": validated["audioBinding"],
                "audioBindingSha256": parent_track["audioBindingSha256"],
                "analysisVersion": validated["analysisVersion"],
                "runtimeIdentity": validated["runtimeIdentity"],
                "runtimeIdentitySha256": parent_track["runtimeIdentitySha256"],
                "parentTimingBinding": parent_timing_binding,
                "durationMilliseconds": validated["durationMilliseconds"],
                "beatTimesMs": validated["beatTimesMs"],
                "barStartsMs": validated["barStartsMs"],
                "meter": validated["meter"],
                "beatsPerBar": validated["beatsPerBar"],
                "tempo": validated["tempo"],
                "tempoConfidence": validated["tempoConfidence"],
                "meterConfidence": validated["meterConfidence"],
                "confidenceUse": CONFIDENCE_USE,
                "prefixExcludedMilliseconds": validated["prefixExcludedMilliseconds"],
                "tailIncludedMilliseconds": validated["tailIncludedMilliseconds"],
                "terminalDownbeatCandidateSuppressed": validated["terminalDownbeatCandidateSuppressed"],
                "beatCount": validated["beatCount"],
                "coveredDurationMilliseconds": validated["coveredDurationMilliseconds"],
                "beatCells": validated["beatCells"],
                "topologySha256": validated["topologySha256"],
                "beatAnalyzerContractSha256": contract["contractSha256"],
                "playerReplayContractSha256": player_contract["contractSha256"],
            }
            generated.append({**track_payload, "trackReceiptSha256": canonical_sha256(track_payload)})
    if seen_tracks != set(parent_tracks):
        raise ValueError("Audio manifests do not exactly cover the parent runtime tracks.")
    generated.sort(key=lambda track: track["trackId"])
    track_set_sha256 = canonical_sha256(
        [{"trackId": track["trackId"], "trackReceiptSha256": track["trackReceiptSha256"]} for track in generated]
    )
    totals = {
        "trackCount": len(generated),
        "beatCellCount": sum(track["beatCount"] for track in generated),
        "sourceDurationMilliseconds": sum(track["durationMilliseconds"] for track in generated),
        "coveredDurationMilliseconds": sum(track["coveredDurationMilliseconds"] for track in generated),
        "excludedPrefixDurationMilliseconds": sum(track["prefixExcludedMilliseconds"] for track in generated),
    }
    receipt_payload: dict[str, Any] = {
        "schemaVersion": OUTPUT_RECEIPT_SCHEMA,
        "split": DEVELOPMENT_SPLIT,
        "developmentOnly": True,
        "promotionEligible": False,
        "referenceFree": True,
        "runtimeAttested": expected_runtime_attestation,
        "stage1UseAllowed": expected_runtime_attestation,
        "selectorUseAllowed": False,
        "playerPlaybackUseAllowed": False,
        "confidenceUse": CONFIDENCE_USE,
        "publicationPolicy": PUBLICATION_POLICY,
        "parentRuntimeBinding": _parent_binding(parent, inventory, inventory_sha256),
        "analyzerContract": contract,
        "playerReplayContract": player_contract,
        "sourceManifestSetSha256": canonical_sha256(source_rows),
        "sourceManifests": source_rows,
        "receiptTotals": totals,
        "receiptTotalsSha256": canonical_sha256(totals),
        "trackSetSha256": track_set_sha256,
        "tracks": generated,
    }
    receipt = {**receipt_payload, "receiptSha256": canonical_sha256(receipt_payload)}

    # Recheck all inputs, current sources, and the complete parent root before
    # the sole hard-link publication commit point.
    reloaded_manifests = _load_and_validate_manifests([Path(manifest["manifestPath"]) for manifest in manifests])
    expected_manifest_state = [(manifest["manifestSha256"], manifest["tracks"]) for manifest in manifests]
    reloaded_manifest_state = [(manifest["manifestSha256"], manifest["tracks"]) for manifest in reloaded_manifests]
    if reloaded_manifest_state != expected_manifest_state:
        raise ValueError("A beat audio manifest changed before publication.")
    for manifest_path, raw_audio_path, resolved_path, digest in audio_resolution_state:
        current_path = _resolved_audio_path(manifest_path, raw_audio_path)
        if current_path != resolved_path or _sha256_file(current_path) != digest:
            raise ValueError("A beat input audio resolution changed before publication.")
    for path, digest in input_state:
        if _sha256_file(path) != digest:
            raise ValueError("A beat receipt input changed before publication.")
    parent_again, inventory_again, inventory_sha256_again = _load_parent(
        parent_runtime_manifest_path,
        parent_runtime_root,
        verify_sources=True,
    )
    if (
        parent_again != parent
        or inventory_again != inventory
        or inventory_sha256_again != inventory_sha256
        or beat_analyzer_contract(parent) != contract
        or player_replay_contract() != player_contract
    ):
        raise ValueError("A parent or target-player source changed before publication.")
    _validate_receipt(
        receipt,
        parent=parent,
        parent_root=parent_runtime_root.resolve(strict=True),
        receipt_path=None,
        verify_sources=True,
        require_runtime_attested=expected_runtime_attestation,
    )
    _atomic_publish_new_json(output_target, receipt)
    return receipt


def _generate_runtime_beat_grid_receipt(
    manifest_paths: Sequence[Path],
    parent_runtime_manifest_path: Path,
    parent_runtime_root: Path,
    output_path: Path,
    *,
    provider: BeatProvider,
    expected_runtime_attestation: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    timeout = _finite_number(timeout_seconds, "timeout_seconds", positive=True)
    if timeout > MAX_RUNNER_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds may not exceed {MAX_RUNNER_TIMEOUT_SECONDS:g} seconds.")

    # Validate every split and manifest field before parent roots, outputs,
    # analyzer sources, or audio paths are inspected.
    manifests = _load_and_validate_manifests(list(manifest_paths))
    source_roots = [Path(manifest["manifestPath"]).parent for manifest in manifests]
    output_target = _preflight_output_target(
        output_path,
        forbidden_roots=[parent_runtime_root, *source_roots],
    )
    try:
        return _generate_runtime_beat_grid_receipt_after_preflight(
            manifests,
            parent_runtime_manifest_path,
            parent_runtime_root,
            output_target,
            provider=provider,
            expected_runtime_attestation=expected_runtime_attestation,
            timeout=timeout,
        )
    finally:
        output_target.close()


def generate_runtime_beat_grid_receipt(
    manifest_paths: Sequence[Path],
    parent_runtime_manifest_path: Path,
    parent_runtime_root: Path,
    output_path: Path,
    *,
    timeout_seconds: float = DEFAULT_RUNNER_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Generate one attested, additive, development-only beat receipt."""

    return _generate_runtime_beat_grid_receipt(
        manifest_paths,
        parent_runtime_manifest_path,
        parent_runtime_root,
        output_path,
        provider=_run_target_browser_beat_analyzer,
        expected_runtime_attestation=True,
        timeout_seconds=timeout_seconds,
    )


def _generate_offline_proxy_beat_grid_receipt_for_tests(
    manifest_paths: Sequence[Path],
    parent_runtime_manifest_path: Path,
    parent_runtime_root: Path,
    output_path: Path,
    *,
    provider: BeatProvider,
    timeout_seconds: float = DEFAULT_RUNNER_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Test artifact mechanics without minting runtime attestation."""

    return _generate_runtime_beat_grid_receipt(
        manifest_paths,
        parent_runtime_manifest_path,
        parent_runtime_root,
        output_path,
        provider=provider,
        expected_runtime_attestation=False,
        timeout_seconds=timeout_seconds,
    )


__all__ = [
    "ANALYZER_CONTRACT_SCHEMA",
    "CONFIDENCE_USE",
    "INPUT_MANIFEST_SCHEMA",
    "METER_PULSES",
    "OUTPUT_RECEIPT_SCHEMA",
    "PLAYER_REPLAY_CONTRACT_SCHEMA",
    "RUNNER_OUTPUT_SCHEMA",
    "SOURCE_ID",
    "beat_analyzer_contract",
    "generate_runtime_beat_grid_receipt",
    "player_replay_contract",
    "validate_runtime_beat_grid_receipt",
]
