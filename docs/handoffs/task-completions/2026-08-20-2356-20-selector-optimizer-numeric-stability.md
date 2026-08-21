# Development selector optimizer numeric stability

## Task summary

Repaired the development-only grouped chord-bar selector's numerical optimizer
after the sealed real development examples stopped at grid candidate 0, inner
fold 0. The failure was not bad input data: the first fit was a finite
`992 x 48` standardized matrix with maximum absolute value `16.920025...`, a
weighted augmented trace of `48.0`, and positive/negative group-balanced mass
of `71.734582... / 3.265417...`. The original trace-derived step was a valid
global majorizer, but plain proximal gradient still had a maximum update of
`1.263e-4` after 3,000 iterations, dominated by the intercept. Its raw-iterate
change test therefore could not certify convergence.

The optimizer is now
`deterministic-trace-majorized-restarted-fista-v2`. It preserves the exact
frozen elastic-net objective, five-candidate hyperparameter grid, group
weights, outer and inner folds, fold salts, preprocessing, selection metric,
tie break, iteration maximum, and `1e-6` numeric tolerance. It changes only the
principled numerical solution path:

- the same deterministic weighted augmented-trace upper bound majorizes the
  smooth logistic-plus-L2 Hessian;
- FISTA acceleration uses the standard deterministic gradient-restart inner
  product;
- convergence is certified at the non-extrapolated iterate by the L-infinity
  norm of the proximal-gradient mapping, rather than an optimizer-step-sized
  raw parameter delta;
- the sigmoid is the exact branch-stable logistic function for finite logits,
  without the former `[-40, 40]` approximation, in both training and selector
  application;
- the smooth logistic objective is evaluated stably at every state as a
  finite-value guard;
- every input, trace, step, logit, probability, gradient, objective, proximal
  update, restart value, extrapolated iterate, and stationarity certificate
  fails closed if non-finite;
- Apple Accelerate's false-positive matrix-multiply floating-point warnings
  are suppressed only around the relevant products, followed immediately by
  explicit finite checks.

The optimizer identity and proximal-gradient convergence semantics are bound
into the selector configuration. The inference link is bound independently as
`branch-stable-exact-logistic-sigmoid-float64-v1` in both the configuration
and emitted estimator. Exact artifact-field validation rejects a missing,
wrong, or legacy clipped-link claim even after resealing. The new deterministic
`BAR_SELECTOR_CONFIG_SHA256` is
`9691afc0464c90a369e042a8fed3a23fbe53fe0285987c2aa5ba544947b00f67`.
Standalone artifact validation accepts only the new optimizer identity, so a
resealed v1 artifact cannot masquerade as the repaired solver.

The now-converged real run exposed a separate exact floating-point defect in
the fixed precision/coverage curve. Its denominator used a NumPy reduction
while its terminal prefix used sequential addition, producing
`1.0000000000000067` at target coverage 1. Both the trainer and readiness's
independent recomputation now build tie-block masses and every prefix with
`math.fsum` over the same exact block-mass lists. No clamp or validation
tolerance was introduced. Target policy, inclusive ties, AURC definition,
coverage targets, threshold policy, and every readiness gate remain
unchanged. The readiness rubric hash remains
`b55cd06588ed4578bd31dcdb4eee6bdf894cac76ed98fab34ca5e4a516fce850`.

Only the sealed development examples artifact was opened for the real numeric
reproduction. No calibration, test, confirmation, readiness-result, audio,
reference, private source, production, browser, or deployment input was
opened by this implementation task. No operating threshold was selected.

## Real development reproduction

Training now completes all 126 nested/final fits under
`PYTHONWARNINGS=error`. The five reported outer refits converged in
`625 / 483 / 525 / 273 / 300` iterations, and the final all-development refit
converged in `538`. OOF probabilities were finite in
`[0.013556404220983791, 0.9979314673225669]`, and the fixed curve's final
realizable coverage is exactly `1.0`.

Two consecutive current-link local reproductions under
`PYTHONWARNINGS=error` emitted the same canonical selector artifact SHA-256:

`ca4d1e5839a311e2a67b6fe3ae756a6272c6f91992d57a688074e299672aab16`

Independent review reproduced the numeric solver and exact
selector/readiness recomputation, then identified the missing independent link
identity before freeze. That provenance gap is included in this repaired
slice. Its temporary generated selectors remained outside version control.

## Files changed

- `steel_guitar_rag/chord_reader/bar_selector.py`
  - SHA-256: `c9d7efcec0ee85d0ee0697a1fe551bb270702bb730b25da3765a72acb475637b`
- `steel_guitar_rag/chord_reader/selector_readiness.py`
  - SHA-256: `464c918d9e579ce98ddce7a98f2ef35fe58e57dce2cff9b0d77af1548335b291`
- `tests/test_chord_reader_bar_selector.py`
  - SHA-256: `9610159e0fd0b3326d78f32acd0825ae77f5b54bbc9879cdbcc53aeadfbb4622`
- `docs/handoffs/task-completions/2026-08-20-2356-20-selector-optimizer-numeric-stability.md`

## Tests and checks

- Focused selector and readiness suites:
  - `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_selector.py tests/test_chord_reader_selector_readiness.py`
  - `89 passed` with `PYTHONWARNINGS=error`
- Full non-browser chord-reader suite, with the three environment-dependent
  live Chrome nodes explicitly deselected:
  - `623 passed, 4 skipped, 3 deselected` with `PYTHONWARNINGS=error`
- Real sealed development training under `PYTHONWARNINGS=error`:
  - two consecutive local runs passed and were byte/canonically deterministic;
  - all fits converged, final fixed coverage endpoint was exactly `1.0`.
- Independent review:
  - `205` relevant tests passed with warnings treated as errors;
  - Ruff, format, byte compilation, and diff checks passed;
  - three real trainings and a temporary readiness reproduction were exact;
  - no P0/P1 finding.
- Adversarial regression coverage includes:
  - a deterministic `992 x 48`, approximately 96%-positive, correlated,
    real-scale standardized geometry that the old plain optimizer could not
    certify inside 3,000 steps;
  - an independently recomputed proximal-gradient stationarity certificate;
  - repeat-fit bit determinism;
  - stable sigmoid values at extreme finite Float64 logits;
  - exact vector/scalar link agreement plus missing and wrong link-identity
    rejection after artifact resealing;
  - NaN, infinity, and finite squared-norm overflow rejection;
  - resealed legacy optimizer-identity rejection;
  - fractional group weights and probability ties whose target-1 coverage is
    exactly `1.0` and whose selector/readiness curves and AURC are identical.
- One broader run that still included the lossy-MP3 live Chrome node reached
  `621 passed, 4 skipped, 2 deselected, 1 failed`; the target Chrome subprocess
  exited with `SIGABRT`. The same suite passed after that third browser node
  was correctly deselected. It did not execute selector code and is not a
  product failure.
- `.venv/bin/ruff check` and `.venv/bin/ruff format --check` on the changed
  Python files: passed.
- `.venv/bin/python -m py_compile` on the changed Python files: passed.
- `git diff --check`: passed.

## Risks

Risk is low-to-medium. This remains a development-only, non-promotable learned
selector with no production caller. The mathematical objective and evaluation
design are unchanged, but any solver revision necessarily changes the fitted
floating-point result and selector configuration hash. The new solver binds
that distinction explicitly and fails closed on non-finite state.

The stable objective check adds runtime because each iteration evaluates the
candidate state used by the stationarity certificate. Real end-to-end training
is approximately 18-19 seconds, which is acceptable for this sealed offline
development command. No performance shortcut is recommended without a new
numeric review.

This repair proves optimizer convergence and exact metric reproduction. It
does not prove a 98% operating point, authorize calibration/test access, or
authorize promotion.

## Human decision needed

No human decision is needed to exact-path integrate this numeric repair. The
parent development workflow may rerun and persist the selector from the same
sealed development examples after committing this source slice. Readiness may
then be evaluated under its already frozen rubric; calibration remains sealed
unless that separate evaluation passes every predeclared gate.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/bar_selector.py`
- `steel_guitar_rag/chord_reader/selector_readiness.py`
- `tests/test_chord_reader_bar_selector.py`
- `docs/handoffs/task-completions/2026-08-20-2356-20-selector-optimizer-numeric-stability.md`

## Files that must not be staged

- Generated development examples, selectors, readiness artifacts, summaries,
  predictions, timing grids, manifests, reports, models, audio, references,
  caches, calibration/test/confirmation artifacts, and private data.
- Any concurrent or unrelated worktree change outside the four exact paths
  above.

## Recommended next lane

Lane 01 should review and exact-path commit these four files. The parent
development lane should then reproduce the selector from the same sealed
development examples at the committed HEAD and, without changing the rubric,
run the already approved development-only readiness evaluator.

## Commit readiness

Ready for exact-path staging and commit after the parent verifies final status.
This subtask was explicitly instructed not to commit.
