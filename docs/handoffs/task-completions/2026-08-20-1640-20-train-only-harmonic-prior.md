# Train-only transposition-invariant harmonic prior

## Task summary

Added a standalone harmonic transition/duration prior without wiring it into
training, benchmarking, decoding, CLI, or production UI.

The builder accepts only a factorized-label manifest carrying both the sealed
artifact-integrity contract and the leak-resistant split protocol. It validates
the complete signed split and seal metadata, re-verifies the train projection's
feature/label files, then opens factorized-label sidecars only for derived
`train` tracks. Development, calibration, test, steel-test, invalid-label gaps,
and track boundaries cannot contribute transitions.

The resulting canonical JSON artifact contains:

- additively smoothed `P(relative root motion, next product | previous product)`
  log probabilities learned from the acoustic trainer's original sealed
  `training_weight * trainingWeightOverride` mass;
- additively smoothed product-conditioned duration histograms with both raw
  integer counts and weighted sufficient statistics;
- exact hashes binding the source manifest, derived split, group assignment,
  train partition, artifact set, feature specification, vocabulary, train
  factorized-label set, and sealed feature/override weight inputs;
- no dataset identifiers, pitch names, absolute roots, or filesystem paths in
  model states or artifact payloads;
- a self-hash over canonical finite JSON and a deterministic atomic writer;
- an immutable compile-once scorer whose transition, duration, and half-open
  span lookups are constant time after one artifact validation;
- scoring functions whose default zero weight returns exact positive `0.0`
  before inspecting an artifact or candidate state.

No real corpus, calibration data, test data, model training, benchmark, or UI
was opened or run.

## Files changed

- `steel_guitar_rag/chord_reader/harmonic_prior.py` (new)
- `tests/test_chord_reader_harmonic_prior.py` (new)
- `docs/handoffs/task-completions/2026-08-20-1640-20-train-only-harmonic-prior.md` (new)

No files were deleted and no generated model/data artifacts were created.

## Tests and checks

- `.venv/bin/pytest -q tests/test_chord_reader_harmonic_prior.py` — 11 passed.
- `.venv/bin/pytest -q tests/test_chord_reader_harmonic_prior.py tests/test_chord_reader_artifact_integrity.py tests/test_chord_reader_split_protocol.py tests/test_chord_reader_dataset_timing.py tests/test_chord_reader.py` — 124 passed.
- `.venv/bin/pytest -q tests/test_chord_reader*.py` — 273 passed, 4 dependency-gated skips.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/harmonic_prior.py tests/test_chord_reader_harmonic_prior.py` — passed.
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/harmonic_prior.py tests/test_chord_reader_harmonic_prior.py` — passed.
- Exact-path whitespace/diff check — no diagnostics.

Focused coverage proves transposition invariance, held-out file exclusion,
deterministic artifact/file bytes, finite smoothing, unequal cached weights,
zero-weight exclusion from learned mass, override multiplication, weight-input
provenance, compile-once validation, exact zero-weight neutrality before an
artifact scan, duration and relative-transition scoring, overflow binning,
train-sidecar tamper rejection, NaN rejection, incoherent label rejection,
self-hash rejection, and expected-split provenance rejection.

## Integration notes

- The artifact product order is `none`, `major`, `minor`, `dominant`,
  `minor-seventh`, matching the factorized v9 contract.
- Pitched transition states use `(nextRoot - previousRoot) mod 12`. No-chord
  exits use `no-chord`; no-chord entries preserve only the next product and use
  `entry`, so no absolute root leaks into the model.
- Durations use the sealed 0.1-second frame grid. Exact bins end at the configured
  maximum and all longer candidates share one overflow bin.
- `compile_harmonic_prior_scorer()` validates once and copies only finite lookup
  values into frozen tuples. Nonzero scoring deliberately requires that compiled
  scorer, preventing accidental full-artifact validation in a decoder hot loop.
- Weight zero is a true disabled path: it returns positive `0.0` before artifact,
  state, duration, or span validation.
- The first experiment uses the same original acoustic mass as model training:
  the sealed cache scalar multiplied by optional `trainingWeightOverride`.
  Dataset balancing is intentionally not introduced into this prior.
- The full seal and split metadata are validated. File-byte revalidation is
  intentionally limited to the train projection so held-out sidecars remain
  unopened; held-out identity is still bound by the signed protocol/seal hashes.

## Risk assessment

Low for repository/runtime behavior because the module is new and unwired.
Medium research risk: this is a first-order relative-product prior with a
weighted histogram duration model. Official literature suggests temporal priors
usually produce modest improvements; it must not be presented as an accuracy
gain until development-only evaluation confirms one.

Rollback is removal of the three new files; no existing runtime file changed.

## Human decision needed

No. Any nonzero transition/duration weight must later be selected on the frozen
development partition only. Calibration/test cannot be used to fit or retune it.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/harmonic_prior.py`
- `tests/test_chord_reader_harmonic_prior.py`
- `docs/handoffs/task-completions/2026-08-20-1640-20-train-only-harmonic-prior.md`

## Files that must not be staged

- Concurrent changes in `steel_guitar_rag/chord_reader/benchmark.py`
- Concurrent changes in `steel_guitar_rag/chord_reader/cli.py`
- Concurrent changes in `steel_guitar_rag/chord_reader/datasets.py`
- Concurrent changes in `steel_guitar_rag/chord_reader/factorized.py`
- Concurrent changes in `tests/test_chord_reader.py`
- Concurrent changes in `tests/test_chord_reader_dataset_timing.py`
- Concurrent changes in `tests/test_chord_reader_factorized.py`
- Any `tmp/` caches, labels, protocols, models, reports, audio, calibration/test
  artifacts, private corpus data, or unrelated worktree files.

## Recommended next lane

Lane 01 should integrate/stage only the three new exact paths after the parent
architecture tournament changes settle. A later Lane 20 experiment may build
one prior from the existing sealed train protocol and compare zero versus
development-selected nonzero weights; Lane 15 must independently verify split
and provenance isolation before any sealed evaluation.

## Commit readiness

Safe to commit by exact path. Nothing was staged or committed in this task.

## Suggested next step

After parent integration, add decoder/benchmark wiring in a separately owned
slice using one compiled scorer per artifact, with prior weights defaulting to
zero and selected only on development.
