# Prediction-only bar uncertainty summarizer

## Task summary

Implemented a strict, reference-free bar summarizer for the new factorized
uncertainty telemetry. The public API is exactly:

```python
summarize_prediction_bars(prediction, timing_only)
```

It has no reference argument and never falls back to legacy segment confidence,
prediction-provided bar starts, inferred tempo/meter, or chord-reference data.
It validates the canonical prediction-core and uncertainty hashes, the complete
frozen frame schema, frame count, finite/ranged arrays, product applicability,
per-member vote dimensions, and the exact feature-representation observability
profile before producing any row.

The summarizer integrates 0.1-second left-edge frames by exact overlap. The
final frame is truncated to song duration, arbitrary bar edges may cut frames,
and uncertainty-bearing prediction segment boundaries must remain frame-aligned
except for the final duration. Root and product selected classes are checked
against the decoded prediction at every frame, including no-chord gaps and the
final frame. This prevents correctly rehashed but stale telemetry from being
aggregated for a different chord.

Each `chord_prediction_bar_uncertainty_v1` row is keyed by `trackId` and bar
`index` and contains the winning canonical predicted product, coverage,
dominance, transition count, and the frozen minimal feature mapping. Root,
product, and ensemble features are overlap-weighted only where decoded segments
match the winning predicted product. Boundary and existing-feature
observability span the complete bar. Ties within the documented time epsilon
use lexical product order.

Only explicit, reference-free runtime grids marked deployable are accepted for
future selector use. Annotation/oracle and inferred grids are rejected from
this reference-free schema. A positive grid start requires exactly matching
top-level and provenance-level prefix certification.

No corpus, feature cache, benchmark prediction, calibration row, held-out row,
audio, private data, or reference file was opened. No model was trained and no
benchmark was run.

## Files changed

- `steel_guitar_rag/chord_reader/bar_uncertainty.py` (new)
- `tests/test_chord_reader_bar_uncertainty.py` (new)
- `docs/handoffs/task-completions/2026-08-20-1846-20-prediction-bar-uncertainty.md` (new)

No file was deleted. Factorized inference, benchmark, CLI, core uncertainty,
corpus, deployment, UI, auth, and model files were intentionally not edited by
this task.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_uncertainty.py`
  - `21 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_uncertainty.py tests/test_chord_reader_bar_uncertainty.py tests/test_chord_reader_benchmark_uncertainty.py`
  - Covered by the final integrated uncertainty QA recorded in the coordinated
    core/benchmark handoff.
  - Includes a real `build_factorized_uncertainty` -> `attach_uncertainty` ->
    strict bar-summary round trip.
- `.venv/bin/python -m pytest -q tests/test_chord_reader*.py`
  - `359 passed, 4 skipped` in the final coordinated default-environment run.
  - The final ML environment run passed `362`, with `1` dependency-gated skip.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/bar_uncertainty.py tests/test_chord_reader_bar_uncertainty.py`
  - passed
- `git diff --check`
  - passed
- `.venv/bin/python -m pytest -q`
  - collection stopped on seven unrelated optional-dependency imports: `cv2`
    for Amazing Tablature tests and `yaml` for script-backed smoke tests. The
    default environment does not contain those optional test/training packages;
    no scoped test failed.

Focused tests cover partial frame overlap, final truncation, nearest-sample
bar-edge semantics (including half-frame ties and final-song nulls), winner-only
versus full-bar masks, uncovered bars, no-chord gaps,
transitions, floating-duration ties, enharmonic canonicalization, positive
prefix certification, prediction-grid non-authority, annotation/oracle
rejection, missing uncertainty, the nested prediction-core anti-splice link,
both acyclic hashes, NaN and array-length rejection, exact frame-count ceiling, member-vote shape,
root/product applicability, stale selected classes after legitimate resealing,
contradictory detailed/product labels, frame-aligned segment boundaries,
Unicode canonical hashing, forbidden outcome fields, deterministic summary
hashing, and independence from an external mutated reference object.

## Integration notes

The source uncertainty must use exact schema
`chord_factorized_uncertainty_v1` and the separately frozen `root`, `product`,
`ensemble`, `boundary`, and `observability` frame arrays. Canonical hashes use
the shared benchmark/promotion encoding (`ensure_ascii=False`, sorted compact
JSON, no NaN).

The required timing input is `chord_explicit_bar_grid_v1` with:

- exact `durationSeconds` and nonempty `barStartsSeconds`;
- `timingProvenance.barStartsSeconds.status: explicit`;
- `sourceClass: runtime` with `deployable: true`; annotation/oracle timing is
  rejected;
- `referenceFree: true`, a nonempty `sourceId`, and a lowercase
  `sourceContractSha256`;
- a canonical `contractSha256` over the timing object excluding that claim;
- duplicate exact prefix certification when the first bar starts after zero.

The output binds:

- `predictionCoreSha256`;
- `uncertaintySha256` and `uncertaintyContractSha256`;
- source feature kind/specification and observability-profile identities;
- the canonical bar-feature contract hash;
- full timing, timing-contract, and timing-source-contract hashes.

The selector feature list intentionally excludes raw top-probability,
direct/joint agreement/JSD, and boundary-member moment summaries. Those signals
remain available in raw telemetry for a separately predeclared later ablation;
they were not added to the initial selector search space.

Future grouped-OOF training must require `selectorUseAllowed` to be exactly true
and bind the complete feature and timing hashes.

## Risk assessment

Risk is medium-low. The module is additive and has no production caller. The
main risks are schema drift between the core emitter and this strict consumer,
or a future selector bypassing the explicit `selectorUseAllowed` gate. Exact
leaf validation, a real emitter round trip, contract hashes, and fail-closed
timing provenance reduce both risks.

Rollback is isolated to the three new files listed by this handoff; there is no
runtime wiring or stored data to migrate.

## Human decision needed

No. The implementation follows the already approved P0 contract. Opening
calibration or held-out data remains a separate, unapproved action.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/bar_uncertainty.py`
- `tests/test_chord_reader_bar_uncertainty.py`
- `docs/handoffs/task-completions/2026-08-20-1846-20-prediction-bar-uncertainty.md`

## Files that must not be staged

- Under this handoff, do not stage the concurrently owned core uncertainty,
  factorized recognizer, benchmark, CLI, or their tests/handoff; they require
  their own exact-scope review.
- Do not stage generated models, ONNX files, predictions, feature caches,
  reports, audio, corpus material, calibration/test artifacts, or private data.

## Recommended next lane

Lane 15 should review the integrated core-emitter and bar-summarizer contract,
then Lane 01 may exact-path stage the two coordinated handoffs if the combined
diff remains green.

## Commit readiness

Safe to commit after exact-path integrated review. This task was explicitly
instructed not to commit.

## Suggested next step

`Lane 15: Review the reference-free factorized uncertainty emitter and prediction-only bar summarizer together. Verify exact schemas/hashes, one-pass inference, selected-class alignment, deployable timing provenance, minimal feature allowlist, and protected calibration/test non-access; then write an exact-path QA handoff.`
