# Development-only chord selector experiment driver

## Task summary

Implemented the additive orchestration and persistence layer for the frozen
development-only chord-bar selector experiment. The new command surface is:

```text
scripts/chord_bar_selector_development.py freeze-expected-shape
scripts/chord_bar_selector_development.py attest-lineage
scripts/chord_bar_selector_development.py prepare-inputs
scripts/chord_bar_selector_development.py build-groups
scripts/chord_bar_selector_development.py build-examples
scripts/chord_bar_selector_development.py train-selector
```

The corresponding Python APIs are:

```python
build_expected_dataset_shape(...)
freeze_reviewed_expected_dataset_shape(...)
attest_development_lineage(...)
prepare_development_inputs(...)
build_development_groups(...)
build_development_examples(...)
train_development_selector(...)
```

`freeze-expected-shape` accepts only a new output path and publishes the one
independently reviewed real-run shape. Callers cannot supply or weaken its
dataset/count policy: AAM is 2 groups of 1, GuitarSet is 3 groups of 12, IDMT
Guitar is 6 groups of 8, NRGCP is 156 groups of 1, and Winterreise is 2 groups
of 2. The resulting exact totals are 246 tracks and 169 base groups. Its
deterministic `shapeSha256` is
`f196611dcbf4cdc825fe1da83a6f552296d331845e8352dae6e293a385e5568e`.
Its `datasetSetSha256` is
`c1c0b99c817b41ea6e49ec86974d9eda8d4c0c11903b51ec0b84cb4af9c00e9c`,
and the driver's deterministic rendered-file SHA-256 is
`b69b5be0e218abb47aa0821054ea4e7d4ebc02aee53ab70bbc488449d09f7ed5`.
The generic shape builder remains available only as a Python API for synthetic
fixtures; CLI `prepare-inputs` additionally enforces equality to the reviewed
shape.

`attest-lineage` calls the production audio-lineage builder once at a private
staging path, derives the complete compact projection, and publishes the full
lineage and projection as a failure-atomic new-path-only set. It never
overwrites either destination.

`prepare-inputs` validates the exact signed winner, the exact full production
audio-lineage artifact, and the exact development source descriptor. The full
lineage must use the production `extract_student_features` entrypoint, must
bind the supplied winner/source file bytes and canonical JSON, and must contain
the exact bound absolute winner/source paths and their path hashes before any
relative source path can be rebased. Relocating byte-identical input JSON is
therefore rejected. It must also contain exactly the signed winner development
IDs. Metadata validation uses
`verify_files=False`; the expensive byte-for-byte source re-extraction is the
responsibility of the immediately preceding `attest-lineage` stage and is not
duplicated here.

The caller must supply the artifact from `freeze-expected-shape` and freeze
exact expected track, base-composition-group, and final confidence-group
counts. Preparation compares every dataset's track count, base-group count,
and base-group-size histogram against that self-hashed artifact, not merely
the global 246/169 totals. This implementation has tested that exact shape
synthetically; it has not opened or run the real 246-track corpus.

Preparation emits exactly two artifacts as one rollback-safe set:

- an exact minimal `chord_runtime_bar_audio_manifest_v2`, containing only
  `schemaVersion`, `split`, and `{id, split, audioPath}` track rows;
- a sealed `chord_bar_selector_development_inputs_v1` sanitized group
  descriptor containing only the six fields accepted by the current group
  builder for each track, exact input hashes, the embedded/source-bound expected
  dataset shape, exact caller/actual counts, and a sealed grouping audit.

Source-relative paths are rebased against the source-descriptor file before
publication, so moving the prepared manifest cannot silently change its audio
target. Runtime audio suffixes are restricted to the target runtime's exact
AAC/M4A/MP3/WAV allowlist. References must be JSON.

Base grouping has no fallback and is exactly:

```text
composition:<datasetId>:<compositionId>
```

Dataset/role admission is exact and fail-closed:

- GuitarSet: `guitarset:<comp|solo>:player-<00..05>`; every admitted
  composition must contain all 12 unique roles.
- AAM: `aam:mix`.
- NRGCP: `nrgcp:mix`.
- IDMT Guitar: `idmt_guitar:capture=<groupId>;speed=<performanceSpeed>`.
- Winterreise: `winterreise:performer=<groupId>`.

Unknown datasets, missing role metadata, duplicate roles inside a composition,
generic audit-role fallbacks, and malformed role strings are rejected.

The derivative registry is an exact, self-hashed development-only artifact.
Omitting `--derivative-registry` selects a sealed explicit-empty registry; it
does not trigger inference. A nonempty registry can merge only sorted, unique
complete `composition:` base-group IDs, at least two at a time, into a unique
`derivative:` confidence group. A base group cannot occur in two merges, an
unknown group fails, and track-level derivative overrides are structurally
impossible.

`build-groups` validates the prepared descriptor before opening a reference,
then calls the current `build_bar_selector_group_manifest` API and atomically
persists its exact output.

`build-examples` requires and loads the benchmark report, full audio lineage,
runtime bar-grid manifest, and group manifest. It calls the current final
builder signature with the required `audio_lineage_manifest=` keyword. All
four top-level and per-track development gates run before benchmark, timing,
group/reference, or summary artifact roots are resolved. Prediction-only
summary sidecars are built beneath a private staging directory; a failed join
leaves neither a published summary directory nor a published examples
artifact. Before publication, the driver requires the exact
`certification-datasets-only-v1` audit mode, the five reviewed dataset IDs and
rows in frozen order, valid audit bindings/hashes, and every per-dataset count
sum to its aggregate label-determinacy count. Generic/custom strata remain
available to library callers but cannot enter the real driver. A successful
join publishes the new flat summary set and its only referencing examples JSON
with rollback on any publication failure.

`train-selector` gates the top-level and every example split before invoking
the same exact certification-only five-dataset audit (so direct CLI training
cannot bypass the build guard), invokes `train_bar_selector`, then atomically
persists only an exact non-promotable development selector. It does not choose
an operating threshold. The committed examples JSON is intentionally rendered
with `sort_keys=True`; a real disk write/read regression now passes that
alphabetized nested `featureValues` object through the actual
`train_development_selector` path and completes training. The selector projects
the exact feature key set in `BAR_FEATURE_NAMES` order rather than relying on
JSON object iteration order.

All JSON output helpers reject existing destinations and symlinked path
components, walk/open parents through no-follow directory descriptors, write
and `fsync` private temporary inodes, capture their identities before linking,
and record ownership immediately after each successful new-name hard link.
Round-trip, `fsync`, and visible-parent identity checks run while those retained
directory descriptors remain open. Failure rollback is descriptor-relative and
removes only links whose device/inode identity proves that this process created
them, including after a visible parent pathname is swapped. The summary-set
publisher applies the same rules to the summary directory, summary files, and
referencing examples JSON. No production, UI, runtime inference, calibration,
confirmation, or test behavior is wired.

## Files changed

- `steel_guitar_rag/chord_reader/selector_development.py` (new)
- `scripts/chord_bar_selector_development.py` (new)
- `tests/test_chord_reader_selector_development.py` (new)
- `docs/handoffs/task-completions/2026-08-20-2215-20-selector-development-experiment-driver.md` (new)

No active benchmark, CLI, audio-lineage, runtime-grid, bar-example,
bar-selector, corpus, model, UI, deployment, auth, or production file was
edited by this task.

Frozen implementation SHA-256 values:

- `steel_guitar_rag/chord_reader/selector_development.py`:
  `829af06bfff75d1e037c267b11f3e9d68453b595c1be32ae2a7e4b20085ede97`
- `scripts/chord_bar_selector_development.py`:
  `18fd5b464d678fa0dad0bfee36d72422493d26d2ddf584fc491d0590e6857644`
- `tests/test_chord_reader_selector_development.py`:
  `153bd6b9c5c78e94346a0d69419dcbe12133e254f65b8335d0a63999b049898d`

The handoff's own final hash is reported outside this self-referential file.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_selector_development.py`
  - `52 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_selector_development.py tests/test_chord_reader_audio_lineage.py tests/test_chord_reader_bar_examples.py tests/test_chord_reader_bar_selector.py tests/test_chord_reader_benchmark_uncertainty.py`
  - `212 passed`
- Full non-browser chord-reader suite (the two live Chrome nodes deselected):
  - `530 passed, 4 skipped, 2 deselected`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/selector_development.py scripts/chord_bar_selector_development.py tests/test_chord_reader_selector_development.py`
  - passed
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/selector_development.py scripts/chord_bar_selector_development.py tests/test_chord_reader_selector_development.py`
  - passed
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/selector_development.py scripts/chord_bar_selector_development.py tests/test_chord_reader_selector_development.py`
  - passed
- `git diff --check`
  - passed for tracked concurrent changes; the new-file whitespace checks are
    independently covered by Ruff/format and final no-index diff checks.

Synthetic coverage includes the exact frozen 246/169 per-dataset shape and
histograms; adversarial same-global-total dataset-count and group-size shifts;
all five exact dataset role policies; complete GuitarSet composition roles;
default empty and nonempty derivative registries; whole-base-group merge
enforcement; unknown derivatives; exact caller counts; exact
winner/source/lineage bindings; byte-identical winner/source relocation
rejection; source-relative paths; missing full lineage; protected-split
rejection before nested root access; output collision; mid-set link failure
rollback; post-link-stat failure rollback; retained-dirfd rollback after parent
path swaps for both JSON and summary-set publication; full-lineage
example-builder dispatch; certification-only five-strata admission; resealed
generic-stratum and aggregate-count mismatch rejection before publication;
direct generic-strata training rejection before trainer dispatch; group-builder
and selector dispatch; canonical `sort_keys=True` examples write/read followed
by actual selector training; and all six CLI subcommands.

No real corpus, source audio, frozen feature array, reference, prediction,
runtime timing, model, calibration, confirmation, test, private source, or
browser was opened by this task. No target-Chrome run and no 246-track
experiment was performed or claimed.

## Integration notes

The required fail-fast preflight is
`freeze-expected-shape --output <new-reviewed-shape.json>`. The seven-stage
real development sequence is then mechanically represented as:

1. `attest-lineage`
2. `prepare-inputs --expected-dataset-shape <new-reviewed-shape.json> --expected-track-count 246 --expected-base-group-count 169 --expected-confidence-group-count 169`
3. `build-groups`
4. existing target-Chrome runtime bar-grid generation using the emitted
   minimal runtime manifest
5. the frozen uncertainty benchmark with the same full lineage
6. `build-examples`
7. `train-selector` (the selector artifact contains the fixed grouped-OOF
   evaluation; there is no separate threshold-selection command)

If a reviewed nonempty derivative registry is introduced, the caller must
freeze the resulting final confidence-group count rather than assume 169. The
driver will reject a stale count.

The generated JSON and summary artifacts belong under ignored experiment
output paths and must not be staged. Calibration, confirmation, test, and any
operating-threshold selection remain outside this command surface.

## Risk assessment

Risk is medium-low. The code is additive and development-only, with no
production caller. The primary remaining risks are operational: a real audio
lineage mismatch must fail the batch; all 246 target-Chrome analyses may take
substantial time; real references must share a valid declared root; and the
grouped estimator may fail its convergence or development quality gates.

Multi-file publication is failure-atomic with retained-dirfd,
identity-checked rollback, including tested post-link failures and parent path
swaps. Like any multi-name POSIX publication, it is not a database transaction
for an uncoordinated reader observing the directory during the few link
operations; downstream stages should start only after the command returns
success.

Rollback of this implementation is deletion of the four new files. It has no
runtime migration or generated committed state.

## Human decision needed

No decision is needed to review or exact-path stage this isolated driver.
Before the real run, Lane 15 should confirm the three authoritative lineage
input paths, the common reference root, the output directory, and whether the
derivative registry is the sealed explicit-empty default or a separately
reviewed nonempty file.

Opening calibration or confirmation, choosing an operating threshold, and
promoting any selector remain separate human-gated decisions.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/selector_development.py`
- `scripts/chord_bar_selector_development.py`
- `tests/test_chord_reader_selector_development.py`
- `docs/handoffs/task-completions/2026-08-20-2215-20-selector-development-experiment-driver.md`

## Files that must not be staged

- Every concurrently modified benchmark, CLI, audio-lineage, runtime-grid,
  bar-example, and bar-selector source/test/handoff file under this handoff.
- Generated lineage/projection JSON, prepared manifests, runtime timing,
  predictions, summary sidecars, group manifests, example artifacts, selector
  artifacts, reports, audio, references, feature caches, ONNX files, corpus
  material, calibration/test artifacts, and private data.

## Recommended next lane

Lane 15 should independently review this exact four-file slice, run the same
focused and adjacent synthetic suites, inspect the exact real input/output
paths without opening protected partitions, and only then execute the real
development-only sequence. Lane 01 may exact-path commit this slice after that
review or as part of the already coordinated development-selector integration.

## Commit readiness

Safe to commit after exact-path independent review. This task was explicitly
instructed not to commit.

## Suggested next step

Lane 15: verify the exact frozen winner/source/Dasheng/lineage paths; run
`freeze-expected-shape`, `attest-lineage`, and `prepare-inputs` on development
only; confirm the expected shape hash above and inspect the emitted hashes
before launching target Chrome.
