# Beat-cell Stage-2 feature/examples implementation

Date: 2026-08-21

## Outcome

Implemented the common machine-authority loader, the label-blind Stage-A
beat-cell feature set, and the Stage-B C/I examples join authorized by the
committed Stage-2 preregistration. Stage A parses only the exact prediction-only
Stage-1 sidecars, prediction leaves located from those sidecar identities, full
audio lineage, runtime timing inputs, and beat receipt. It treats the Stage-1
report as opaque bytes and never accepts a report, group, reference, or outcome
mapping. Stage B validates and semantically recomputes the complete committed
Stage-A set before parsing the full passed Stage-1 artifact and joining labels.

No official Stage-1 report, prediction leaf, sidecar root, audio lineage,
runtime artifact, or generated Stage-2 path was opened by this implementation
lane. The official commands were not run. All tests used tracked authorities
and synthetic/offline fixtures. Calibration, test, confirmation, player,
public-song, promotion, and deployment inputs remained closed. No commit was
created.

## Frozen authority and public API

- Authority file SHA-256:
  `674298f9077d3471e00d296dfe0925e2aa278270721544a6b7391b27cdd7cfb4`.
- Authority canonical SHA-256:
  `fc8a8cc0ef0c408a068dc59d28d99726bd379e55d7ce9258d51835054d80dca2`.
- Stage-A projection SHA-256:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`.
- Feature-math projection SHA-256:
  `65fc42417c1b45201e02fe35f140fee541f20608f08fbe6f2d92c127e4009ef2`.
- Stage-B projection SHA-256:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`.

`beat_cell_stage2_contract.py` reads only the exact tracked preregistration
path, rejects duplicate/non-finite JSON and symlinked path components, verifies
the raw/canonical/projection hashes, and no-follow reads every byte-pinned
source module. It exports deep-copied source, output, and projection objects.

The public Lane-A/Lane-B API is:

- `build_beat_cell_feature_summary(sidecar, prediction, *, prediction_file_sha256)`;
- `build_beat_cell_feature_set_manifest(...)`;
- `validate_beat_cell_feature_row(row)`;
- `validate_beat_cell_feature_summary(summary)`;
- `validate_beat_cell_feature_set_manifest(manifest)`;
- `validate_beat_cell_feature_set(manifest, summaries)`;
- `validate_beat_cell_feature_set_semantics(...)`;
- `build_beat_cell_examples(...)`;
- `validate_beat_cell_examples_artifact(artifact)`;
- `run_official_beat_cell_features()` and
  `run_official_beat_cell_examples()`.

Public validators return unchanged deep copies, are exact-field and
fail-closed, and perform no hidden normalization. The 48-value `featureValues`
representation is a JSON mapping: validators require the exact key set, and
all ordered consumers explicitly project using the authority's `featureNames`
array. Canonical `sort_keys=True` serialization is therefore safe.

## Stage-A semantic closure

Every feature summary independently validates its complete Stage-1 sidecar,
raw prediction identity, uncertainty evidence, construction, integer receipt
cells, and prediction summary. It reruns the frozen
`summarize_prediction_cells` helper and requires exact canonical-object
equality before computing the preregistered 48 features with the byte-pinned
bar helpers. Product is exact-equal; coverage and dominance are independently
recomputed with the frozen `1e-9` comparator.

The official runner directly opens and fully validates the authority-pinned
audio-lineage artifact with source-file verification, projects exactly the 246
development tracks, and cross-binds every sidecar and prediction identity to
the lineage row, source audio, cached and fresh feature arrays, and canonical
duration. It independently validates and replays the runtime manifest and beat
receipt. Prediction leaves are located only from the exact sidecar prediction
identities under the pinned benchmark root. The group manifest/root,
references, and outcomes are not admitted to Stage A.

Admission ordering is fail-closed. The top audio-lineage raw-file and artifact
receipts plus its complete static schema/self-hash validation must match the
frozen Stage-1 contract before any nested path or runtime root is inspected.
The Stage-1 summary directory is captured as opaque raw bytes/inodes first;
its exact 246-file count and frozen raw file-set SHA are checked before any
sidecar JSON is parsed. Only that admitted set is then parsed and validated as
prediction-only sidecars.

The runner snapshots every filesystem leaf admitted by the strict runtime and
audio validators as an exact absolute path to lexical and resolved device/inode
identity. This includes the runtime manifest and every timing leaf; the three
bound audio manifests; extractor source and lock; every source audio and cached
NPZ; both analyzer generators, runner, client, worker, Node, and Chrome; and all
declared setup/player documents and resources. Legitimate final-component
player symlinks bind their lexical lstat inode and link-target text plus the
resolved regular target inode. Every identity is checked before and after each
strict replay at both source barriers. Runtime and benchmark roots, the Stage-1
summary root, and their visible paths retain exact directory device/inode
identity throughout; every flat-root verifier closes with an exact visible-path
recheck.

The emitted official manifest is required to contain exactly 246 summaries,
11,234 rows, and 6,201,472 canonical milliseconds and to bind the exact opaque
Stage-1 report raw hash plus exact sidecar artifact/file-set hashes. A
regression mutates every synthetic Stage-1 outcome while never supplying either
outcome object to Stage A and proves object-identical summary and manifest
bytes, deterministic paths, row/set hashes, and artifact hashes.

## Atomic Stage-A completion barrier

`feature-set/manifest.json` and all files under `feature-set/summaries` are
built and fsynced inside one hidden sibling directory. Retained no-follow
parent, private-root, and summary-root descriptors bind device/inode identity.
Inputs are replayed immediately before publication. The whole `feature-set`
directory is then published with a true kernel no-replace directory rename:
Darwin `renameatx_np(RENAME_EXCL)` or Linux
`renameat2(RENAME_NOREPLACE)`. Unsupported platforms fail closed; plain
replacement rename is never used.

The complete tree, canonical manifest bytes, and every summary byte are
verified after rename, followed by a second idempotent source replay. After
that final callback, every manifest and summary name is re-bound to its owned
regular-file inode and reread for exact bytes; summary-root, feature-root, and
parent path identities are then rechecked in that order immediately before
success. Failure cleanup scans both retained tree levels for every owned file
inode and the retained parent for renamed owned directories. Foreign
replacements are preserved. A crash before the sole rename can leave only an
unpublished hidden staging directory, never a visible partial official summary
root; after rename, the entire completed tree is visible. Tests cover
inode-identical success, complete-tree visibility at the barrier, manifest,
summary, and whole-root swaps at the final callback, source mutation across
rename, failure at the sole rename, a foreign concurrent destination,
parent-directory replacement, cleanup, and no overwrite.

## Stage-B join and examples schema

The official Stage-B runner first deep-opens every committed summary and the
manifest, checks canonical bytes, exact inventory, deterministic authority
paths, exact opaque Stage-1 path/file and sidecar-set provenance, and the frozen
246/11,234/6,201,472 totals. It then reopens every sidecar and prediction leaf
and recomputes the full Stage-A feature set before the Stage-1 report is parsed.
Coherently resealed false provenance, nondeterministic paths, intervals,
source-cell hashes, and feature values are rejected.

Only exact terminal C/I outcomes are emitted; U/N cells are excluded. Official
Stage B requires exactly 9,376 examples and 5,074,349 canonical milliseconds.
Each label-free `exampleKey` binds track/cell/duration, source beat cell,
prediction identity, feature row/summary/set, and audio lineage, but excludes
outcome, label, dataset, group, and role fields. Label mutation therefore cannot
change keys or tie order.

Each example has exactly:
`schemaVersion`, `exampleKey`, `trackId`, `cellIndex`,
`durationMilliseconds`, `sourceBeatCellSha256`,
`predictionIdentitySha256`, `featureRowSha256`,
`featureSummaryArtifactSha256`, `featureSetArtifactSha256`,
`audioLineageRowSha256`, `featureValues`, `featureValuesSha256`,
`stage1OutcomeRowSha256`, `stage1ArtifactSha256`,
`sourceGroupTrackRowSha256`, `datasetId`, `role`, `guitarsetRole`,
`confidenceGroupId`, `correct`, and `exampleSha256`.

`labelAudits` contains exact aggregate, five ordered dataset, GuitarSet
aggregate, and ordered comp/solo rows. Every row reports track/example/C/I
counts and integer-millisecond totals and binds its exact source funnel SHA.
All scope tuples are exact, and all C/I/E count and duration totals are
independently reconciled to Stage 1. The full endpoint-reconciliation audit is
copied, validated, and hash-bound. The single-file Stage-B publisher checks all
retained inputs immediately before and after its no-replace link and rolls back
only owned inodes on either failure. It also requires the final name to remain
the exact linked regular-file inode before and after byte reads, after fsync,
after parent verification, and at the final barrier. A destination-name swap
preserves the foreign replacement while safely removing every discoverable
same-parent link to the owned inode. Stage B also retains exact benchmark,
Stage-1-summary, and committed feature-summary roots and repeats the top-file
and label-blind-root checks after complete Stage-1 validation before either
publication barrier may return.

## Official CLIs and closure

`scripts/chord_beat_cell_features.py` and
`scripts/chord_beat_cell_examples.py` insert the current repository root before
project imports and accept no path, policy, retry, report, group, reference, or
weakening flags. All input and output paths come only from the committed
authority. Existing official destinations are rejected before any source read
or builder/outcome access.

Both artifacts remain development-only and promotion-ineligible. Examples are
selector-training input only. No threshold, readiness result, calibration
authority, protected-split authority, player authority, or deployment decision
is emitted.

## Tests run

- `.venv/bin/pytest -q tests/test_chord_reader_beat_cell_examples.py`
  - 66 passed.
- `.venv/bin/pytest -q tests/test_chord_reader_beat_cell_examples.py tests/test_chord_reader_beat_cell_selector.py tests/test_chord_reader_beat_cell_readiness.py`
  - 113 passed.
- `.venv/bin/pytest -q tests/test_chord_reader_*.py` with the three named
  real-browser runtime tests deselected
  - 779 passed, 4 skipped, 3 deselected.
- `.venv/bin/ruff check ...` and `.venv/bin/ruff format --check ...`
  - passed for all five owned Python files.
- CLI subprocess smoke tests proved current-checkout imports and rejection of
  dummy path/weakening flags without opening official inputs.

Synthetic/adversarial coverage includes canonical write/read feature ordering,
full Stage-A semantic recomputation, all audio-lineage identity fields,
coherently resealed interval/source-cell/feature mutations, all-outcome label
mutation, exact label-audit scope tuples, source-funnel reconciliation,
authority-bound manifest provenance and path inventory, official one-shot
preflight, both Stage-A source barriers, both Stage-B source barriers,
destination-name/inode swaps, post-link exceptions, no-replace concurrency,
crash topology, parent swaps, root relocation with unchanged hardlinked leaves,
byte-identical replacement of every transitive input class, player-symlink
retarget and resolved-target replacement, protected JSON parse ordering, and
current-checkout CLI provenance.

## Files touched and SHA-256

- `steel_guitar_rag/chord_reader/beat_cell_stage2_contract.py`
  - `7db034c597d9585c4b7f553ee0a7fa67143252fb47c6145566bae39d97a6abbb`;
- `steel_guitar_rag/chord_reader/beat_cell_examples.py`
  - `963b74713197bb7d518060ab61a1fef813a028d4a1dd2fbcbe83c98d611c4136`;
- `scripts/chord_beat_cell_features.py`
  - `c0911052883b66eeebae12323c43b33fb35bf204352202e97b4add80e802a7d3`;
- `scripts/chord_beat_cell_examples.py`
  - `a841485267f384c6b2568a07fc61be2defd8e8abecf17e095ad0a3b33c2cd338`;
- `tests/test_chord_reader_beat_cell_examples.py`
  - `63bf666f4a800658d841c0ff3bdfe6faba15892e83968b5fbc2a826566a5d75a`;
- `docs/handoffs/task-completions/2026-08-21-0558-06-beat-cell-stage2-feature-examples-implementation.md`
  - this handoff.

Refresh the implementation hashes after any review patch.

## Human decision needed

No new lane-local decision is needed. The root task already grants autopilot
for the exact scoped commit and one-shot Stage-2 development sequence. Root
must still independently review this frozen implementation and create the
clean commit before exercising that existing authorization. Calibration, test,
confirmation, player changes, promotion, and deployment remain unauthorized.

## Recommended next step

Root should independently review and commit the frozen Stage-2 implementation
as one clean scoped change, then run the already-authorized exact official
one-shot development sequence. That execution must stop after the readiness
artifact for independent audit.
