# Dasheng feature cache

## Task summary

Implemented the production-quality data cache between the sealed Dasheng base
extractor and factorized chord-model label caching/training. The cache accepts
one or more validated track manifests, defaults to only `train` and
`development`, requires a second explicit authorization for `test` or
`steel_test`, writes deterministic 10 Hz by 768-dimensional float16 NPZ files,
and atomically emits a `chord_feature_cache_v1` manifest.

No Dasheng checkpoint was downloaded and no corpus extraction was started.
Production/runtime behavior was not changed.

## Files changed

- `steel_guitar_rag/chord_reader/dasheng_cache.py` — new sealed cache API,
  validation, atomic/restartable writes, and manifest emission.
- `tests/test_chord_reader_dasheng_cache.py` — new synthetic-extractor tests.
- `docs/handoffs/task-completions/2026-08-20-1441-20-dasheng-feature-cache.md`
  — this handoff.

No files were deleted and no generated model or feature artifacts were added.

## API and data contract

Primary API:

```python
cache_dasheng_features(
    track_manifests,
    output_root,
    *,
    splits=None,
    allow_held_out=False,
    overwrite=False,
    extractor=None,
    snapshot_root=None,
    contract_path=DEFAULT_DASHENG_CONTRACT,
    manifest_path=None,
) -> dict
```

`track_manifests` accepts one mapping/path or an iterable of mappings/paths.
Relative audio paths in a JSON manifest resolve from that manifest's directory.
The default split set is `train` plus `development`. Held-out material requires
both an explicit held-out split in `splits` and `allow_held_out=True`.

The emitted manifest is directly accepted by `cache_factorized_labels` and
contains `featureKind`, `featureCount`, `sampleRate`, `frameSeconds`, `modelId`,
immutable `revision`, `weightSha256`, `featureSpecSha256`,
`augmentationPolicy=none`, source-manifest hashes, and per-track audio/feature
hashes. The feature-spec hash covers the model revision and all runtime file
hashes, pooling and timestamp conventions, grid dimensions, float16 storage,
and the no-augmentation policy.

Each NPZ is restricted to a fixed non-object array allowlist, compressed with
unencrypted DEFLATE, verified with `allow_pickle=False`, and checked for:

- exact `(ceil(duration / 0.1), 768)` shape;
- finite float32 input and finite float16 storage;
- exact left-edge 10 Hz timestamps;
- extracted versus declared duration agreement within one frame;
- immutable feature-spec, source-audio, source-feature, and stored-feature
  SHA-256 values;
- matching training weight and track identity.

Valid files are reused without invoking the extractor. Stale/damaged files fail
closed unless the caller deliberately sets `overwrite=True`. Each temporary NPZ
is fully verified and fsynced before `os.replace`; the JSON manifest is written
last and atomically. A failed multi-track run can therefore resume from already
validated track files.

## Tests and checks

- `.venv/bin/pytest -q tests/test_chord_reader_dasheng_cache.py` — `9 passed`.
- `.venv/bin/pytest -q tests/test_chord_reader_dasheng.py tests/test_chord_reader_dasheng_cache.py tests/test_chord_reader_factorized.py` — `42 passed, 2 skipped`.
  The two real-checkpoint/optional-Torch tests remain intentionally skipped in
  the normal environment.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/dasheng.py steel_guitar_rag/chord_reader/dasheng_cache.py tests/test_chord_reader_dasheng.py tests/test_chord_reader_dasheng_cache.py tests/test_chord_reader_factorized.py` — passed.
- `git diff --check` — passed.

The tests use only an injected deterministic extractor. They prove multi-manifest
selection, relative-path resolution, direct factorized-label compatibility,
held-out guarding, safe NPZ types, provenance hashing, stale-audio rejection,
explicit replacement, grid/shape validation, interruption recovery, atomic
temporary-file cleanup, and traversal-safe filenames.

## Integration notes

The module is intentionally not exported through `chord_reader.__init__` and is
not wired into the shared CLI in this isolated task. The factorized trainer's
current feature-kind allowlist must separately be expanded by its owning lane
before it can train on `dasheng_base_v1`; the cache manifest itself already has
the required structure and `training_weight` array.

## Risk assessment

Risk: low for the repository because the code is additive and no extraction was
run. Operational risk remains medium until the sealed real checkpoint passes a
one-track pilot: model/runtime memory, throughput, and real-output numerical
behavior have not been measured by this task. Float16 rounding is deliberate and
is part of `featureSpecSha256`, but any future storage change must create a new
feature specification rather than silently reusing this cache.

Rollback is removal of the three exact new files; there is no production wiring.

## Human decision needed

No. A separately approved/controlled pilot can use the already sealed local
snapshot when the parent chord-reader lane is ready. A full-corpus extraction was
explicitly not started.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/dasheng_cache.py`
- `tests/test_chord_reader_dasheng_cache.py`
- `docs/handoffs/task-completions/2026-08-20-1441-20-dasheng-feature-cache.md`

## Files that must not be staged

- All unrelated dirty and untracked files shown by `git status --short`.
- `tmp/`, downloaded model snapshots, extracted feature caches, audio, corpus
  files, checkpoints, and benchmark outputs.

## Recommended next lane

The parent chord-reader model-development lane should wire the API into its CLI,
permit the exact `dasheng_base_v1`/768-D sealed feature contract in factorized
training with augmentation forced to `none`, then run only the bounded one-track
pilot before deciding whether to authorize the ten-track pilot.

## Commit readiness

Safe to commit as part of the parent branch's exact-path chord-reader v9 slice.

## Suggested next step

Integrate `cache_dasheng_features` without weakening its held-out guard, run the
one-track real-checkpoint pilot, and compare deterministic feature hashes across
two executions before any broader extraction.
