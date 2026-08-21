# Development audio-lineage attestor

## Task summary

Implemented an additive, development-only audio-lineage attestor for the frozen
multiband chord-reader winner. It closes the winner cache's historical missing
audio binding without opening calibration, test, confirmation, or other
protected partitions.

The public APIs are:

```python
build_development_audio_lineage(
    winner_cache_manifest_path,
    development_source_manifest_path,
    dasheng_cache_manifest_path,
    output_path,
)

validate_development_audio_lineage(artifact, verify_files=False)

project_development_audio_lineage(artifact, track_ids=None)
```

All three input hashes are derived from actual, path-backed JSON bytes captured
through one descriptor-anchored, no-follow read; JSON hashing and parsing consume
the same captured bytes, so the caller cannot assert authoritative manifest
hashes or splice content between reads. The builder requires:

- the exact signed `chord_factorized_label_cache_v2` winner manifest with its
  complete split protocol and `artifactIntegrity` seal;
- an exact `chord_dataset_manifest_v1` development descriptor whose IDs equal
  the signed winner development partition (246 rows for the real frozen
  protocol);
- the full sealed Dasheng feature-cache manifest, projected by those exact
  development IDs without requiring its source/cache-role `split` values to be
  `development`.

The source descriptor and Dasheng row must agree on `datasetId` and lexical
audio path. Dasheng's `sourceAudioSha256` independently corroborates the bytes
at that path. Winner rows are correctly permitted to lack `audioPath`; the
artifact explicitly records
`winnerCacheAudioBindingStatus=absent_repaired_by_fresh_array_equality_v1`.
The canonical winner row and artifact-integrity entry remain separately hashed.

Every manifest schema, every split, the complete selected ID set, all source
metadata, all cross-manifest fields, and every path the attestor will use are
validated before a source audio or frozen NPZ is statted or opened. Only after
that global preflight does the builder process each development row:

1. securely walk every source path with anchored directory descriptors and
   `O_NOFOLLOW`, then hash source audio from one regular-file descriptor while
   copying those exact bytes into a private, read-only temporary snapshot;
2. compare that captured audio SHA with Dasheng corroboration;
3. capture the frozen NPZ once and require its exact `artifactIntegrity` SHA and
   byte count;
4. load its allowlisted `features` array from the captured NPZ bytes, never by
   reopening its authoritative path;
5. call `extract_student_features(snapshot, "multiband_chroma_v2")` (or an
   explicitly injected synthetic test extractor) on the private snapshot;
6. cast both arrays to exact contiguous little-endian float16 (`<f2`);
7. require byte-for-byte equality and equal array SHA-256;
8. verify frames, `(frames, 61)` shape, element count, frozen duration, fresh
   duration, exact 10 Hz alignment, and canonical milliseconds;
9. seal all audio, cache-file, array, source-metadata, duration, and path
   identities into a row hash.

The authoritative audio path remains in the lineage row, but the extractor only
receives the private snapshot path. The snapshot is created mode `0600`, fsynced,
changed to mode `0400`, checked before and after extraction, and removed by a
bounded `TemporaryDirectory` context on both success and failure. The original
audio and cache are rehashed after their captured bytes are consumed so a source
change during the operation rejects the batch.

The output uses exact schema `chord_development_audio_lineage_v1`, with
`developmentOnly=true` and `promotionEligible=false`. It binds:

- extractor entrypoint, complete source-module bytes, inspected function
  source, dependency-lock bytes, installed dependency versions, and exact
  feature-spec contract;
- winner-cache, source-descriptor, and Dasheng manifest paths, bytes, raw file
  hashes, canonical hashes, and signed semantic hashes where available;
- per-row source audio/path, frozen NPZ, fresh/cached array, frame, duration,
  canonical-millisecond, source-row, and row hashes;
- complete track, audio, and array set hashes plus a self hash.

Publication is new-path-only and atomic. The complete artifact is held in memory
until every row passes. The destination parent is opened through an anchored,
component-by-component `O_DIRECTORY|O_NOFOLLOW` walk. Missing directories and a
random exclusive temporary inode are created relative to retained directory
descriptors. The fully written and fsynced inode is hard-linked to the final name
with source and destination `dir_fd` arguments, so swapping a parent pathname
cannot redirect the write. The implementation verifies the published bytes and
the final parent-directory inode, rolls back only its own hard link on failure,
fsyncs the directory, and never overwrites a concurrent destination. A failure
on any row publishes nothing. Immediately before publication, the builder also
rehashes all three input manifests and the extractor source/dependency lock and
rechecks the extractor function and dependency identity, closing drift during
the batch.

`validate_development_audio_lineage(..., verify_files=True)` recaptures and
rehashes all three authoritative manifests, parsing each from the same bytes,
reruns their complete metadata and cross-set validation, verifies extractor
source/lock/dependency identity, recaptures every audio and frozen NPZ, and
independently re-extracts every fresh array from private audio snapshots. The
projection helper emits a compact sealed identity object suitable for later
benchmark and bar-example joins without exposing local paths.

No real corpus, audio, feature cache, reference, calibration artifact, test
artifact, Dasheng NPZ, or protected source was opened. No real extraction was
started and no threshold/model was selected.

## Files changed

- `steel_guitar_rag/chord_reader/audio_lineage.py` (new)
- `tests/test_chord_reader_audio_lineage.py` (new)
- `docs/handoffs/task-completions/2026-08-20-2045-20-development-audio-lineage-attestor.md` (new)

No benchmark, CLI, bar-example, bar-selector, runtime-grid, inference, model,
dataset, corpus, UI, production, deployment, or auth file was edited.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_audio_lineage.py`
  - `17 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_audio_lineage.py tests/test_chord_reader_artifact_integrity.py tests/test_chord_reader_split_protocol.py tests/test_chord_reader_dasheng_cache.py`
  - `53 passed`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/audio_lineage.py tests/test_chord_reader_audio_lineage.py`
  - passed
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/audio_lineage.py tests/test_chord_reader_audio_lineage.py`
  - passed after formatting both new files
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/audio_lineage.py tests/test_chord_reader_audio_lineage.py`
  - passed
- `.venv/bin/python -m pytest -q tests/test_chord_reader*.py -k 'not real_browser_webaudio'`
  - `502 passed, 4 skipped, 2 deselected`
- `git diff --check`
  - passed

Focused tests prove deterministic seals; strict validation and full file
revalidation; compact deterministic projections; source and signed-winner
protected-split rejection before nested file access; exact source/winner ID
sets; dataset and path equality; source/Dasheng audio-hash corroboration; source
audio tamper; frozen-cache file tamper; source-manifest file tamper; row tamper;
existing-output preservation; and a one-value fresh-array mismatch failing with
no output publication. Adversarial tests additionally prove that same-size JSON
mutation with restored mtime cannot splice hashing from parsing, a replaced NPZ
path cannot change already-captured features, source-audio replacement during
extraction cannot affect the private snapshot and fails the final source check,
and a parent-directory swap cannot redirect or leave behind a published file.

All test audio, manifests, arrays, and extractors are synthetic fixtures.

## Risks

Risk is low-to-medium. The module is additive, development-only, and has no CLI
or production caller. Secure path access deliberately requires POSIX
`O_DIRECTORY`, `O_NOFOLLOW`, and descriptor-relative filesystem operations,
which are available on the target macOS/Linux environments but fail closed on
platforms without them. The real 246-song run is intentionally not part of this
task and may disclose a genuine historical cache/audio mismatch; such a failure
must invalidate the complete lineage publication rather than be waived.

The real extractor must derive installed `python`, `numpy`, `librosa`, `scipy`,
and `soundfile` versions directly. Explicit dependency-version injection is
accepted only with an injected extractor for synthetic fixtures; the production
entrypoint rejects supplied versions. These bindings identify Python source,
the lock, and installed distributions, but not every native decoder shared
library or a stale callable already loaded before an on-disk source edit. Run
the real attestation in a fresh process from the pinned environment; exact fresh
array bytes remain independently bound regardless.

The signed winner protocol, not a caller count, is the authority for the exact
development size. Its real partition is 246 tracks; the tests use a separately
signed one-track synthetic protocol.

## Human decision needed

None to stage this isolated implementation. Before running all 246 songs, Lane
15 should independently review the three authoritative file paths and run the
attestor in the environment that satisfies `requirements/chord-reader.lock`.
Any single audio, cache-file, duration, or feature-byte mismatch is a batch
failure and must not produce a lineage artifact.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/audio_lineage.py`
- `tests/test_chord_reader_audio_lineage.py`
- `docs/handoffs/task-completions/2026-08-20-2045-20-development-audio-lineage-attestor.md`

## Files that must not be staged

- Do not stage any concurrently owned runtime bar-grid, bar-example, or
  bar-selector files under this handoff.
- Do not stage generated lineage JSON, public audio, feature caches, Dasheng
  caches or snapshots, predictions, references, calibration/test artifacts,
  corpus material, private sources, model files, or `tmp/` content.

## Recommended next lane

Lane 15 should independently review this three-file slice, then run one
synthetic integration from audio lineage projection through the runtime-grid,
bar-example, and grouped-selector consumers. Only after review should it run
the real 246-song development attestation. Calibration and confirmation remain
sealed.

## Commit readiness

Ready for exact-path independent review. This task was explicitly instructed
not to commit.
