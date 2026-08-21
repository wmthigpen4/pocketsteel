# Runtime reference-free Play Along bar grids

## Task summary

Implemented a development-only lane that emits deployable, reference-free bar
timing by running the current Play Along audio path in the pinned target Google
Chrome runtime. This is exact target-Chrome parity, not a claim of parity with
other browsers or with an FFmpeg decoder.

The Node harness launches Google Chrome `151.0.7922.170`, injects the current
`ui/practice-analysis-client.js` and `ui/practice-analysis-worker.js` into an
`about:blank` target, and calls the same player functions:

1. `STEEL_RAG_ANALYSIS_CLIENT.decodeAudio(file)`;
2. `STEEL_RAG_ANALYSIS_CLIENT.monoSamples(decoded)`;
3. `STEEL_RAG_ANALYSIS_V2.downsample(mono, decoded.sampleRate)`;
4. `STEEL_RAG_ANALYSIS_V2.rhythmAnalysis(..., {})`.

It does not call harmony analysis and accepts no key, meter, tempo, bar, chord,
label, annotation, playlist, reference, or analyzer hint. Audio bytes are
embedded from one explicitly allowlisted local file. Browser requests are
blocked by CSP, CDP request blocking, disabled background-network flags, and a
host resolver rule. A successful run must report zero target-page requests.

The generator validates every manifest and track split and exact field set
before it inspects the output directory, analyzer sources, or an audio path. A
later protected manifest therefore blocks earlier development audio. Only
self-contained `.wav`, `.mp3`, `.m4a`, and `.aac` files are accepted; playlist,
URL, and unsupported suffixes fail before path access.

No corpus, generated development set, calibration, test, heldout, confirmation,
reference, label, or private data was opened. The only audio analyzed was a
locally generated synthetic click track and an MP3 transcoded from that fixture
for integration testing. No model was trained, no benchmark was run, and no
file was committed.

## Frozen contracts and consumer API

- Input manifest: `chord_runtime_bar_audio_manifest_v2`
- Output manifest: `chord_runtime_bar_grid_manifest_v2`
- Browser runner output: `chord_runtime_browser_bar_analyzer_output_v1`
- Analyzer contract: `chord_runtime_browser_bar_analyzer_contract_v1`
- Timing leaf: `chord_explicit_bar_grid_v1`
- Runtime source ID: `play-along-target-chrome-webaudio-rhythm-analysis-v1`

The production entry point is deliberately non-injectable:

```python
generate_runtime_bar_grids(
    manifest_paths,
    output_dir,
    *,
    replace_verified_set=False,
    timeout_seconds=300,
)
```

There is no public runner, worker, browser, source, provenance, or deployability
override. The private injected-provider test helper can emit only
`sourceClass: offline-proxy`, `deployable: false`, and
`selectorUseAllowed: false`; those manifests fail the public runtime validator.

Selector consumers must import and call:

```python
from steel_guitar_rag.chord_reader.runtime_bar_grid import (
    validate_runtime_bar_grid_manifest,
)

validated = validate_runtime_bar_grid_manifest(
    manifest,
    artifact_root=output_directory,
    verify_sources=True,
)
```

`validate_runtime_bar_grid_manifest(manifest, *, artifact_root=None,
verify_sources=True) -> dict` requires the complete v2 shape. It rejects legacy
or partial objects labeled v2, offline proxies, missing runtime attestation,
unapproved selector rows, source-contract drift, extra fields, forged hashes,
missing files, unrelated files, symlinks, audio/PCM/duration inconsistencies,
and timing leaves without exact runtime/deployable/reference-free provenance.

The exact output top-level fields are `schemaVersion`, `split`,
`developmentOnly`, `promotionEligible`, `selectorUseAllowed`,
`runtimeAttested`, `analyzerContract`, `sourceManifestSetSha256`,
`sourceManifests`, `trackSetSha256`, `timingArtifacts`, `tracks`,
`previousManifestSha256`, and `manifestSha256`.

Each current track row binds its source manifest, source audio SHA-256, decoded
and analyzer PCM identities/counts/rates, decoded channel count and duration,
player-canonical millisecond duration, analysis version, browser/Node runtime
identity, timing file/hash/contracts, bar count, selector flag, and canonical
track-artifact hash. Timing-artifact rows are exactly `timingFile`,
`timingSha256`, and `timingContractSha256`.

## Runtime and source binding

At this handoff:

- Google Chrome: `151.0.7922.170`
- Chrome executable SHA-256:
  `689b0f7d1de6bc94982b3b82034d23fa9e409b588b9162e2b8037d88f26e410f`
- Node: `v24.15.0`
- Node executable SHA-256:
  `883fe1b81091bea13a3bbdfdf7bdfc33b374a050c0fd07eccac53e470ec8f96a`
- player client SHA-256:
  `428128bbaf1c4509d2ffe052ff63bc750572dfd9c6d5ef33fecbea068e853a57`
- player worker SHA-256:
  `ea148fd2355d493a94ec4253fadc2cacd198637b19d81bd7e5cf3576cf0407da`
- browser runner SHA-256:
  `5bf52ac7927e28cc756c02855b94456e06cfac9bd33608e07afb193c677170b9`
- Python generator/validator SHA-256:
  `1d1d73d11f7ea444585e2eac971b7a5e8373c2e3c40ac61dd2e38590ec661a2f`
- analyzer source-contract SHA-256:
  `79973513e839c57b3f5f6d76cd187be7063b573e8db77e4ba1e57fb0cee5904f`
- browser launch-contract SHA-256:
  `b07bdcb7e534bb507a80e8463fa0c22dbc0a4a0eb986a3ae73cd876cb18f9e1d`

The browser version is checked through CDP before document injection or audio
analysis. The contract binds browser and Node executable bytes and versions,
launch flags, client/worker/runner/generator bytes, decoded mono PCM SHA/count/
rate/channels/duration, analyzer PCM SHA/count/rate, source audio SHA, and the
worker analysis version. The audio file is hashed before and after analysis to
reject mutation.

Chrome launch is bounded to 30 seconds. Timeout cleanup now waits for Chrome
exit (SIGTERM with bounded SIGKILL fallback) before rejecting and deleting its
temporary profile, and launch errors include only the final 2,048 characters
of Chrome stderr for actionable but bounded diagnostics.

Timing duration is the player's canonical
`Math.round(AudioBuffer.duration * 1000) / 1000`; exact decoded duration and
sample binding remain separately disclosed. Bar starts are the worker's
`barStartsMs / 1000` without invented annotation or fixed-tempo timing. A
positive first bar start is certified identically at the timing top level and
in provenance as `prefixExcludedSeconds`.

## Output transaction and replacement policy

Timing filenames are content addressed as
`timing-{canonical-timing-sha256}.json`. All new timing objects are atomically
written and fsynced before `manifest.json`; the manifest is the sole commit
point and is written last. A fault injected before manifest replacement leaves
the old manifest byte-for-byte valid.

The default output must be new or empty. Explicit replacement requires a
valid, canonical, committed prior manifest and verified content-addressed
artifacts; timing files without a manifest are insufficient. Symlinked output
components/destinations and unrelated files fail before analysis.

Replacement has an intentional archival policy: verified prior
content-addressed timing artifacts remain present and listed in
`timingArtifacts`, even when no current track row references them. This allows
a new run to recover a timing artifact written before a failed manifest commit
while preserving the old commit point. The prior and new sets must have the
same runtime-attestation class. No prior artifact is deleted or silently
overwritten.

## Real target-browser integration evidence

The real WAV fixture was run twice through pinned Chrome. Both output
manifests and timing files were byte-identical. Chrome decoded the 12-second,
stereo, 44.1 kHz fixture to:

- decoded mono PCM: 529,200 samples at 44,100 Hz;
- decoded duration: exactly `12.0` seconds;
- player-canonical duration: `12000` milliseconds;
- analyzer PCM: 132,300 samples at 11,025 Hz;
- decoded PCM SHA-256:
  `30d2108bbe32d712e2bdf5c2fa2f6f637c3e17203f2e8e3adc6b83cc8f4f4cd0`;
- analyzer PCM SHA-256:
  `2069fbf14b36ed12364c5bad73282057626c9873d52bd406d71c18edb63ac720`.

The lossy MP3 fixture was decoded by Chrome, not FFmpeg. FFmpeg was used only
inside the test to create the MP3 fixture. Chrome reported:

- decoded mono PCM: 529,200 samples at 44,100 Hz;
- decoded duration: exactly `12.0` seconds;
- player-canonical duration: `12000` milliseconds;
- analyzer PCM: 132,300 samples at 11,025 Hz;
- decoded PCM SHA-256:
  `c681b9964f6473c9e108f742e90069d133c43cb054b3c837c4905860eab208be`;
- analyzer PCM SHA-256:
  `6da437dcd8db538b4a7b5cef97cb6202146228fdba4a26238439959c0f72ad2b`.

The controlled WAV and MP3 fixtures therefore had a zero decoded-duration
delta. This is only a measured fixture result, not permission to assume exact
duration equality for arbitrary codecs or real songs.

## Files changed

- `scripts/chord_runtime_bar_analyzer.js` (new)
- `scripts/chord_runtime_bar_grid.py` (new)
- `steel_guitar_rag/chord_reader/runtime_bar_grid.py` (new)
- `tests/test_chord_reader_runtime_bar_grid.py` (new)
- `docs/handoffs/task-completions/2026-08-20-1925-20-runtime-reference-free-bar-grids.md`
  (new)

The concurrently owned selector, examples, uncertainty, benchmark,
factorized, CLI, player, worker, and corpus files were not edited.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_runtime_bar_grid.py`
  - `36 passed in 19.08s`
  - The same frozen source also passed as 34 non-browser unit tests and 2
    separately selected real-browser tests.
- `.venv/bin/python -m pytest -q tests/test_chord_reader*.py`
  - `475 passed, 4 skipped in 25.42s`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/runtime_bar_grid.py tests/test_chord_reader_runtime_bar_grid.py`
  - passed
- `node --check scripts/chord_runtime_bar_analyzer.js`
  - passed
- `.venv/bin/python -m compileall -q steel_guitar_rag/chord_reader/runtime_bar_grid.py tests/test_chord_reader_runtime_bar_grid.py`
  - passed
- `git diff --check`
  - passed

## Remaining risks and integration blocker

- This lane proves exact source/runtime/audio provenance and deterministic
  execution. It does not prove that the rhythm analyzer's musical downbeats are
  correct on public development songs.
- This is pinned target-Google-Chrome parity only. Other browser engines,
  Chrome versions, OS decoder stacks, or Node versions require a new attested
  contract and fresh evidence.
- The current uncertainty prediction/report contract does not yet expose the
  source audio SHA-256. A selector must not join these runtime timings to a
  prediction using duration alone. First add the prediction-side source-audio
  lineage and require exact SHA equality. The downstream join must additionally
  require the runtime millisecond duration to equal exactly
  `floor(predictionDurationSeconds * 1000 + 0.5) / 1000`; it must not use a
  generic duration tolerance or overwrite either source duration.
- The output remains `developmentOnly: true` and `promotionEligible: false`.
  This work does not authorize calibration, test, heldout, or confirmation
  access and does not authorize contacting Travis.

## Safe-to-stage exact file list

- `scripts/chord_runtime_bar_analyzer.js`
- `scripts/chord_runtime_bar_grid.py`
- `steel_guitar_rag/chord_reader/runtime_bar_grid.py`
- `tests/test_chord_reader_runtime_bar_grid.py`
- `docs/handoffs/task-completions/2026-08-20-1925-20-runtime-reference-free-bar-grids.md`

Do not stage the concurrently owned `bar_examples.py`, `bar_selector.py`, their
tests/handoffs, generated timing/manifests/audio, corpus content, reference
data, calibration/test/heldout artifacts, models, predictions, feature caches,
reports, or private data.

## Commit readiness

Ready for exact-path review with only the five files listed above. This task
was explicitly instructed not to commit.
