# Bounded consensus development preregistration

## Task summary

The user authorized one bounded Stage 1 comparison to determine whether BTC
and isolated NNLS-chroma evidence can improve the existing chord reader's
selective accuracy. This preregistration freezes the experiment before any new
feature pass or candidate fit.

The run is limited to the existing 246-track, development-only winner-seven
bar-example surface. Calibration, test, confirmation, the three private proof
songs, deployment, model promotion, and player changes remain closed.

## Frozen candidates

Exactly three candidates are allowed, in this order:

1. `engine-only`: the existing 48 label-blind bar/uncertainty features;
2. `engine-plus-btc`: candidate 1 plus six BTC coverage, agreement, dominance,
   confidence, and transition features;
3. `engine-plus-btc-plus-nnls`: candidate 2 plus six clean-room
   Chordino-inspired NNLS-chroma features and four three-system consensus
   features.

Each candidate receives exactly one fit. The shared estimator is a fixed
median-imputed, standardized, class-balanced logistic regression with
`C=1.0`, `solver=lbfgs`, `max_iter=1000`, and random state `20260825`.
There is no hyperparameter, feature, fold, model, or threshold search.

## Frozen split and metrics

The source remains development-only. Confidence groups are ordered per dataset
by SHA-256 of the fixed split ID and group ID; every fourth group is assigned
to the evaluation role and all others to fit. This ensures each dataset has a
held-out group without opening another partition.

The primary operating point is fixed at predicted correctness `>=0.98`.
Primary metrics are accepted-bar precision and accepted-bar coverage.
Unfiltered engine precision, correctness-classification accuracy, ROC AUC,
Brier score, and the fixed descriptive thresholds `0.50`, `0.80`, `0.90`,
`0.95`, and `0.98` are reported. No threshold may be selected after seeing the
results.

## Hard execution cap

- BTC feature passes: at most one;
- NNLS-chroma feature passes: at most one;
- candidate count: exactly three;
- total candidate fits: exactly three;
- parameter searches: zero;
- automatic retries: zero;
- subagents: zero;
- calibration/test/confirmation evaluations: zero;
- deployments or localhost proof changes: zero.

Feature preparation and evaluation refuse completed output paths. A partial or
failed feature pass stops for a report rather than silently retrying. The run
terminates after the one development report regardless of outcome.

## Implementation paths

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`
- this preregistration

Generated feature caches and the terminal report stay below ignored
`~/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/` and must not be
staged.

## Human decision needed

No. The user explicitly approved this bounded Stage 1 run. Any later sealed
evaluation, retraining, threshold choice, runtime integration, or deployment
requires a new explicit approval.

## Safe-to-stage exact file list

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`
- `docs/handoffs/task-completions/2026-08-25-1600-15-bounded-consensus-development-preregistration.md`

## Files that must not be staged

- `~/Documents/Pocket Steel/tmp/`
- `ui/chord-reader-proof/local-tests/`
- `docs/handoffs/task-completions/integration-status.md`
- all source audio, model caches, credentials, and unrelated files

## Recommended next lane

Lane 15 should run the one feature preparation pass, run the one three-fit
development comparison, write the terminal result handoff, and stop.

## Commit readiness

Safe to commit after focused tests and exact-path review.
