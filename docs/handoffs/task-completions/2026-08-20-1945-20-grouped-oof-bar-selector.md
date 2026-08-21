# Development-only grouped OOF chord-bar selector

## Task summary

Implemented the next confidence-model layer as an additive, development-only
module. It consumes the exact compact artifact emitted by
`bar_examples.py`; it performs no file I/O and cannot open corpus,
calibration, test, heldout, or confirmation paths.

The public training API is:

```python
train_bar_selector(examples_artifact)
```

The input must be exact schema `chord_bar_selector_examples_v1`, canonical
self-hashed, marked `development`, and contain explicit
`confidenceGroupId` values. There is no track-id or other grouping fallback.
Every compact bar row is separately hash-bound to its prediction core,
uncertainty, timing, source summary, exact `BAR_FEATURE_NAMES` order, and the
canonical shared model/decoder/member/feature/profile/runtime-timing binding.
The compact row's `trackId` must equal the enclosing example's `trackId`.
Logical `(trackId, barIndex)` values must be unique, and every track must retain
one `confidenceGroupId` plus one exact source-summary, prediction-core,
uncertainty, and timing hash across all of its bars. These checks reject
fully-resealed cross-track and cross-run splices. The target envelope exposes
exactly `outcome: {correct: boolean}`; structural eligibility must already have
been frozen by the example builder.

The examples binding, frozen selector config hash, selector artifact, and
application boundary all carry and validate one explicit outcome/eligibility
contract: score schema `chord_bar_product_confidence_v1`, reference dominance
`0.75`, prediction coverage `0.75`, prediction dominance `0.75`, threshold list
`[0.0]`, the exact player-millisecond to full-precision-prediction final-bar
join, and inclusion only for eligible bars with boolean correctness.

Only the ordered `featureValues` vector enters NumPy. Track IDs, composition
groups, outcome bits, roles, datasets, references, eligibility, and hashes are
metadata only. Exact feature keys/order and numeric ranges are validated;
extra identity/outcome fields fail closed.

Training is deterministic nested grouped validation:

- outer five-fold OOF by `confidenceGroupId`;
- inner four-fold hyperparameter selection inside each outer training fold;
- fold-local group-weighted median imputation, weighted centering, and
  weighted scaling;
- each confidence group has total sample weight exactly one in every training
  or validation partition;
- a frozen five-candidate elastic-net logistic grid selected by group-balanced
  inner log loss, with grid order as the only tie break;
- deterministic proximal-gradient optimization; any non-converged inner
  candidate, outer fit, or final fit rejects the entire training run;
- final hyperparameter selection by grouped inner CV on all development rows,
  followed by a converged all-development refit.

The artifact reports group-balanced OOF log loss, Brier score, area under the
risk-coverage curve, and fixed descriptive precision/coverage points. It does
not select or store an operating threshold and is explicitly non-promotable.
Audit-only OOF rows retain boolean correctness and exact per-group sample
weights so the artifact validator recomputes every headline metric rather than
trusting reported floats. The artifact seals feature/config, source/input,
group, fold-plan, OOF-prediction, and canonical self hashes.

Those SHA-256 values are canonical integrity commitments, not digital
signatures and not independent authentication of provenance. They detect
mutation and splicing only when the artifact enters through the trusted
builder/runtime validation boundary.

The application API is:

```python
apply_bar_selector(
    compact_bar_summary,
    artifact,
    bar_index=...,
    shared_bindings=...,
)
```

It returns a probability only when the artifact, compact summary,
`sharedBindingsSha256`, model/decoder/member order, uncertainty, feature
representation/profile, and runtime timing-source bindings all match. Every
failure returns `probability: null` with a reason. There is no fallback to
legacy `productConfidence` and no threshold decision.

No real corpus, generated benchmark, audio, reference, calibration, heldout,
test, private, or Travis data was opened. Only synthetic in-memory and
temporary-file fixtures were used. No model accuracy claim was made and no
operating point was selected.

## Files changed

- `steel_guitar_rag/chord_reader/bar_selector.py` (new)
- `tests/test_chord_reader_bar_selector.py` (new)
- `docs/handoffs/task-completions/2026-08-20-1945-20-grouped-oof-bar-selector.md` (new)

No existing selector, benchmark, CLI, inference, uncertainty, corpus,
deployment, UI, auth, or production file was edited by this task.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_selector.py`
  - `45 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_selector.py tests/test_chord_reader_bar_examples.py`
  - `82 passed`
- Runtime/examples/selector/uncertainty integration with the two environment-
  dependent live Chrome launches deselected:
  - `178 passed, 2 deselected`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/bar_selector.py tests/test_chord_reader_bar_selector.py`
  - passed
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/bar_selector.py tests/test_chord_reader_bar_selector.py`
  - passed
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/bar_selector.py tests/test_chord_reader_bar_selector.py`
  - passed
- `git diff --check`
  - passed
- An earlier attempted run including both live Chrome tests reached `175 passed` with
  `2 failed`: Chrome did not publish its DevTools endpoint in one launch and
  exited with `SIGABRT` in the other. The same integrated suite is green when
  those environment-dependent launches are deselected; neither failure entered
  selector/example code.

Focused coverage includes canonical example/artifact integrity hashes, exact
compact builder compatibility, resealed compact/enclosing track mismatch,
logical bar duplication, multi-group track assignment, each per-track source
hash splice, source/static binding mismatch and foreign-model splice rejection,
the frozen outcome/eligibility contract through training/artifact/application,
split preflight, explicit group requirements, exact feature order, forbidden
metadata/outcome feature injection, numeric range/null handling, unit group mass
with unequal group sizes, deterministic five-by-four nested folds, fold-local
preprocessing, all-fit convergence, artifact-schema tamper rejection, complete
OOF metric recomputation, threshold absence, and fail-closed application.

The leakage proof changes every outcome bit for one entire outer-validation
composition, reseals the source examples, retrains, and requires that
composition's raw OOF probabilities to remain exactly unchanged. Separate
assertions verify that no confidence group crosses any outer or inner
train/validation boundary.

## Risks

Risk is medium. This is a real learned selector, but it is additive,
development-only, unconnected to production, and emits no operating decision.
The main statistical risks are development-set size, group-manifest quality,
dataset shift, and calibration drift. Nested grouping and unit group weights
reduce leakage and corpus-size domination; they do not certify 98% precision.

The fixed optimizer deliberately fails closed on non-convergence. This is
safer than emitting a partially optimized selector, but a difficult real
development matrix may stop training and require a separately reviewed
optimizer/config revision. The current grid and tolerance are frozen into the
config hash.

Rollback is deletion of the three new files listed by this handoff. There is
no runtime wiring or stored model migration.

## Human decision needed

No decision is needed to stage this isolated implementation. Opening or using
calibration/test/confirmation outcomes, selecting an operating threshold, or
promoting the selector remains a separate decision and is not authorized by
this handoff.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/bar_selector.py`
- `tests/test_chord_reader_bar_selector.py`
- `docs/handoffs/task-completions/2026-08-20-1945-20-grouped-oof-bar-selector.md`

## Files that must not be staged under this handoff

- Concurrently owned `bar_examples.py`, `runtime_bar_grid.py`, scripts, tests,
  and their handoffs; use their own exact-path handoffs.
- Generated selectors, example artifacts, predictions, feature caches,
  timing grids, reports, models, audio, references, corpus material,
  calibration/test artifacts, and private data.

## Recommended next lane

Lane 01 should exact-path integrate the runtime-grid, compact example-builder,
and selector handoffs after reviewing the two local Chrome launch failures.
Then the model-development lane may run the
frozen winner over development only, build real deployable runtime bar grids,
produce compact examples, and train this selector. Calibration must remain
sealed until the full development gates and artifact review pass.

## Commit readiness

The three selector files are ready for exact-path staging after coordinated
review. This task was explicitly instructed not to commit.
