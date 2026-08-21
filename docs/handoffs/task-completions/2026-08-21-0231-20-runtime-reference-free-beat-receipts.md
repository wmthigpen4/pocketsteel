# Runtime reference-free beat-grid receipts

Date: 2026-08-21

## Task summary

Implemented the additive, development-only runtime beat-receipt slice required
before a beat-cell Stage-1 experiment. The new target-browser harness reruns
the exact current Play Along decode, mono, downsample, and rhythm-analysis path
while preserving the worker's original integer `beatTimesMs` and
`barStartsMs`. It does not adapt the existing seconds output and performs no
seconds round-trip when constructing beat cells.

The slice emits one holistic canonical JSON receipt. It embeds every track's
complete raw beat/bar arrays, exact one-cell-per-beat topology, self hash,
track-set hash, aggregate count/duration receipt, analyzer/player contracts,
and exact parent-runtime root inventory. It is not a content-addressed
per-track directory or artifact set.

The CLI is:

```text
.venv/bin/python scripts/chord_runtime_beat_grid.py \
  --manifest <exact-development-audio-manifest.json> [--manifest ...] \
  --parent-runtime-manifest <exact-parent-root/manifest.json> \
  --parent-runtime-root <exact-attested-runtime-bar-grid-v2-root> \
  --output <NEW-disjoint-receipt.json>
```

No real 246-track batch, reference label, prediction, model, beat-cell Stage-1
scorer, selector, calibration, test, confirmation, public-song proof, or Travis
contact occurred in this slice.

## Frozen schemas and API

- additive browser output:
  `chord_runtime_browser_beat_analyzer_output_v2`
- additive analyzer contract:
  `chord_runtime_browser_beat_analyzer_contract_v1`
- tracked-player replay contract:
  `chord_runtime_beat_player_replay_contract_v1`
- holistic output receipt:
  `chord_runtime_beat_grid_receipt_v1`
- source identity:
  `play-along-target-chrome-webaudio-rhythm-analysis-beats-v2`

The production entry point is deliberately non-injectable:

```python
generate_runtime_beat_grid_receipt(
    manifest_paths,
    parent_runtime_manifest_path,
    parent_runtime_root,
    output_path,
    *,
    timeout_seconds=300,
)
```

The only provider injection is private and emits unattested fixtures with
`stage1UseAllowed: false`. The strict consumer API is:

```python
validate_runtime_beat_grid_receipt(
    receipt,
    *,
    parent_runtime_manifest,
    parent_runtime_root,
    receipt_path=None,
    verify_sources=True,
)
```

The public validator requires an attested receipt, loads the exact canonical
`parent_runtime_root/manifest.json` through the parent v2 validator, and
requires the caller mapping to equal those bytes. `verify_sources=False`
disables current-file byte comparison only; exact schemas, field allowlists,
hash joins, parent policy equality, route identities, reference-free claims,
and topology remain mandatory.

## Additive harness and exact parent reconciliation

The existing bar runner is preserved byte-for-byte. The Python module derives
a deterministic temporary v2 runner from the exact base-runner source using
five single-occurrence, fail-closed patch points:

1. schema and source ID are bumped;
2. client and worker aliases are bound by absolute tracked paths;
3. `beatTimesSeconds` and `barStartsSeconds` are replaced by the original
   integer `beatTimesMs` and `barStartsMs`;
4. `tempoConfidence` and `meterConfidence` are added as disclosures;
5. no label, reference, key, meter, tempo, playlist, or analyzer hint is
   accepted.

The materialized runner is content-hashed before launch, rederived before
execution, and self-verifies its temporary file bytes. Its contract binds the
base runner, parent runner, additive runner, generator, client, worker, browser
and Node executables/versions, browser launch arguments, decode policy, and
exact player exports.

Every new browser result must equal its parent track on all of the following:

- source manifest and track identity;
- source-audio SHA-256;
- decoded mono PCM SHA/count/rate/channels/duration;
- player-canonical integer-millisecond duration;
- analyzer PCM SHA/count/rate;
- analysis version;
- browser, V8, navigator, and Node runtime identity;
- exact integer bar starts versus the parent timing leaf;
- parent timing file, content hash, timing-contract hash, source-contract
  hash, and bar count.

The parent manifest/root inventory, audio manifests, audio bytes, additive
sources, and tracked-player sources are rehashed and revalidated immediately
before publication.

## Exact beat topology, meter, prefix, and tail

The accepted meter-to-pulse mapping is exact:

- `2/4 = 2`
- `3/4 = 3`
- `4/4 = 4`
- `6/8 = 6`

In particular, compound `6/8` is six worker pulses, not two dotted-quarter
beats. Confidence values must be finite and in `[0,1]`, but they are recorded
only under the frozen `disclosure-only` policy. They do not filter tracks,
beats, or cells.

The validator independently reproduces the worker's downbeat sequence and
terminal-bar rule. `barStartsMs` must equal `beatTimesMs[::beatsPerBar]` except
for exactly one final candidate removed only when the worker predicate is
true: the remaining duration is strictly less than `0.4` times the median
retained bar length. Arbitrary omission, addition, subdivision, sorting, or
fixed quarter-bar adaptation fails.

Each explicit beat produces exactly one positive contiguous cell:
`[beatTimesMs[i], beatTimesMs[i+1])`; the final cell ends at the exact
player-canonical duration. The excluded prefix is exactly the first beat and
first retained bar start. The terminal tail is included exactly from the final
beat to canonical duration, including a terminal downbeat candidate suppressed
from `barStartsMs`. Cell indices, retained-parent indices, pulse numbers,
downbeat-candidate flags, durations, track topology hashes, beat counts, and
covered durations are all independently rederived.

Parent seconds are used only to reconcile the prior leaf. They are converted
with `Decimal(str(value))*1000` and must already be integral decimal
milliseconds. This avoids binary-float failures such as `1.001*1000` while
still rejecting `1.0005`.

## Player resource binding and honest cache boundary

The replay contract binds both the stable aliases and the actual documents,
callers, and resources currently tracked by the repo:

- `ui/setup-song.html`
- `ui/play-song.html`
- `ui/practice-analysis-client.js`
- `ui/practice-analysis-client-audio-led-key-v11.js`
- `ui/practice-analysis-worker.js`
- `ui/practice-analysis-worker-audio-led-key-v11.js`
- `ui/setup-song-audio-led-key-v12.js`
- `ui/play-song.js`
- `ui/play-song-analysis-calibration-v7.js`
- `ui/practice-tools-key-regions-v1.js`

It verifies byte-identical alias pairs, exact document/resource routes,
resource hashes, document hashes, the setup persistence of `result.analysis`
into `project.timeline`, the player's direct `timeline.beatTimesMs.map(Number)`
load, and the practice-tools preference for explicit beats before derived
pulses.

One limitation is deliberately disclosed rather than hidden: the immutable
setup-page route token for
`practice-analysis-client-audio-led-key-v11.js` is `9e61...`, while the current
tracked resource SHA-256 is `428128...`. The receipt therefore freezes
`browserCacheParityAttested: false`, scopes parity to tracked repository
resources rather than an existing browser cache, and always sets
`playerPlaybackUseAllowed: false`. This does not block a sealed development
Stage-1 receipt, because Stage-1 uses the newly attested target-browser arrays
directly. It does block any claim that an already cached browser necessarily
runs these exact bytes and must be resolved before later real-player/public
playback parity is claimed.

## Atomic publication and split safety

All audio manifests are exact-field validated before the parent root, output,
analyzer sources, or audio paths are inspected. Any calibration, test,
heldout, confirmation, training, label, reference, playlist, timing hint, or
unsupported audio source fails closed.

The output must be a new `.json` path under an existing directory and must be
disjoint from the parent runtime root and every source-manifest root. Broken
symlinks, symlinked components, existing destinations, wrong suffixes, and
parent/source-root destinations fail before audio or Chrome analysis.

Publication retains a no-follow file descriptor for the original output
parent throughout the run. Canonical bytes are written and fsynced to a private
same-directory inode, then hard-linked with no replacement. The publisher
unlinks the private name, fsyncs the retained directory, verifies that the
pathname still resolves to the retained directory device/inode, verifies the
destination and reopened file are the owned inode, and rereads canonical bytes
through that retained descriptor. Any post-link failure removes the
destination only if it still resolves to the owned inode. A concurrently
created foreign destination is never deleted.

The receipt explicitly freezes relocatable single-file semantics: its content
identity is bound, not its local pathname. The hard-link is the sole
publication commit point; no per-track leaves or partially visible receipt set
exist.

## Tests and checks

- Focused offline/adversarial suite with warnings as errors:
  - `.venv/bin/python -m pytest -q -W error tests/test_chord_reader_runtime_beat_grid.py -k 'not real_browser'`
  - `33 passed, 1 deselected`
- Parent bar-grid plus beat-grid nonbrowser suite:
  - `70 passed, 3 deselected`
- Full chord-reader nonbrowser suite with warnings as errors:
  - `.venv/bin/python -m pytest -q -W error tests/test_chord_reader*.py -k 'not real_browser'`
  - `696 passed, 4 skipped, 3 deselected`
- A separately escalated single synthetic-WAV target-Chrome test generated a
  real parent v2 bar grid, generated the additive beat receipt from the same
  audio, and strictly reconciled audio/PCM/runtime/bar identities:
  - `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python -m pytest -q -W error tests/test_chord_reader_runtime_beat_grid.py -k real_browser`
  - `1 passed in 12.22s`
  - this was one synthetic harness preflight, not a real-song or 246-track
    batch.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/runtime_beat_grid.py scripts/chord_runtime_beat_grid.py tests/test_chord_reader_runtime_beat_grid.py`
  - passed
- `.venv/bin/ruff format --check ...`
  - passed
- `.venv/bin/python -m py_compile ...`
  - passed
- CLI `--help` smoke:
  - passed
- `git diff --check`
  - passed
- Independent final read-only audit:
  - P0: none
  - P1: none
  - the reviewer independently reran 33 nonbrowser tests plus Ruff, formatting,
    compilation, and diff checks, and confirmed the final-byte Chrome result.

Adversarial coverage includes protected-split ordering; later protected
manifest ordering; integer/float rejection; the `1.001` Decimal trap;
nonintegral millisecond rejection; 6/8 pulse topology; exact worker terminal
downbeat pop; prefix/tail coverage; nonempty/strictly increasing/range checks;
meter, network, PCM, runtime, analysis-version, parent-bar, and confidence
tampering; resealed ordering/topology attacks; stale self hashes; foreign
parent mappings; parent/receipt symlinks; exact archival schemas with
`verify_sources=False`; extra reference-bearing contract fields; nested parent
policy drift; route/hash/alias joins; parent/source/output overlap; broken
destination symlinks; midbatch provider failure; final source-manifest
mutation; final audio-symlink re-resolution; link-then-raise rollback;
foreign concurrent destination preservation; directory-fsync rollback; and
parent-directory swap rollback through the retained descriptor.

## Files changed

- `steel_guitar_rag/chord_reader/runtime_beat_grid.py` (new)
- `scripts/chord_runtime_beat_grid.py` (new)
- `tests/test_chord_reader_runtime_beat_grid.py` (new)
- `docs/handoffs/task-completions/2026-08-21-0231-20-runtime-reference-free-beat-receipts.md`
  (new)

The existing runtime bar-grid generator, browser runner, player client, worker,
actual setup/player resources, Stage-1 scorer, models, predictions, generated
artifacts, corpus, calibration/test/confirmation data, deployment, auth, and
Travis files were not edited.

## Frozen source hashes

- `steel_guitar_rag/chord_reader/runtime_beat_grid.py`:
  `605a99441621dd37772a0a41ac73de77a918ed8244bdfe6c5bf894242e4a0097`
- `scripts/chord_runtime_beat_grid.py`:
  `b552fc89c7f3cdd0488ee5782bba593fa4c5162f0089c0b2b3c327fc8f6de611`
- `tests/test_chord_reader_runtime_beat_grid.py`:
  `d0cd42f2e6a8c8a460bbc616a3be703caf835c5413d41925a0a2d615733c2d24`
- preserved base browser runner:
  `5bf52ac7927e28cc756c02855b94456e06cfac9bd33608e07afb193c677170b9`
- preserved player client alias:
  `428128bbaf1c4509d2ffe052ff63bc750572dfd9c6d5ef33fecbea068e853a57`
- preserved player worker alias:
  `ea148fd2355d493a94ec4253fadc2cacd198637b19d81bd7e5cf3576cf0407da`
- preserved parent runtime-bar generator:
  `5079798827503a4a1a2ea123637c116591fde51e6e93b58495738f973485263c`

The handoff's own hash is intentionally reported outside this self-referential
document.

## Risks

Risk is medium-low for the implemented receipt mechanics and medium for the
next real batch. The single synthetic browser test proves that the materialized
harness launches and reconciles one controlled file; it does not prove stable
beat/bar topology across all 246 development tracks or musical correctness.
The official batch must be one separately frozen run, and any track failure
must leave Stage-1 closed.

The tracked setup client cachebuster mismatch prevents current-browser-cache
parity and any direct playback authorization. The receipt records this exactly
and cannot be used to publish raw beat predictions in the player.

Canonical hashes provide tamper evidence and reproducibility, not signatures
or external authentication. Output-path relocation is intentionally allowed;
content and parent identities remain exact.

## Human decision needed

None to exact-path review or commit this isolated implementation. The official
246-track beat-receipt run is a separate action. It must use the exact frozen
development source manifests and exact existing attested parent v2 root. Any
generation, reconciliation, topology, hash, or publication failure aborts
before labels and does not authorize a partial batch or retry with another
grid.

After a complete receipt passes independent audit, a separate beat-cell
Stage-1 scorer may be implemented and preregistered with the same candidate,
five datasets, 13 count-and-duration gates, GuitarSet overall authorization,
and comp/solo disclosures. No Stage-1 scorer or label access is authorized by
this implementation alone.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/runtime_beat_grid.py`
- `scripts/chord_runtime_beat_grid.py`
- `tests/test_chord_reader_runtime_beat_grid.py`
- `docs/handoffs/task-completions/2026-08-21-0231-20-runtime-reference-free-beat-receipts.md`

## Files that must not be staged

- Existing runtime bar-grid, runner, client, worker, setup/player, model,
  prediction, scorer, selector, corpus, deployment, auth, or unrelated files.
- Any generated audio, parent runtime, beat receipt, reference, label,
  prediction, Stage-1, calibration, test, confirmation, public-song, browser
  profile, temporary runner, private-source, or Travis artifact.

## Recommended next lane

Lane 01 may exact-path commit the four independently audited files. Only after
that freeze should Lane 20 run the one official 246-track reference-free beat
receipt. The result must be independently audited before any beat-cell Stage-1
implementation or label access.

Calibration, test, confirmation, arbitrary public-song proof, direct player
publication, and Travis remain closed.

## Commit readiness

Ready for exact-path staging. Final hashes are refreshed and independent review
found no P0 or P1 issue. No file is staged or committed by this handoff.
