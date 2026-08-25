# Bounded correction-fusion development preregistration

## Task summary

The user authorized the next bounded chord-reader step: determine whether the
retained BTC and NNLS confidence sources can correct wrong engine chords, not
merely identify bars to trust. This preregistration freezes the candidates and
metrics before any correction result is measured.

The run reuses the completed 185-track BTC/NNLS caches and the exact existing
development confidence-group split. It may read only the five processed source
manifests and reference files for the 1,585 already admitted development bar
examples. Calibration, test, confirmation, private proof songs, localhost,
promotion, and deployment remain closed.

## Reference admission

Every reference file must match the `referenceSha256` already bound by the
development benchmark. Every bar must have at least 75% reference coverage and
75% dominant-reference-product share. The reconstructed canonical product must
reproduce all 1,585 existing correct/incorrect outcomes before a fit may occur.

Flat and sharp spellings are canonicalized to the same pitch class. Any
missing hash, indeterminate bar, or outcome mismatch stops the command before
fitting.

## Frozen candidates

Exactly three candidates are evaluated on the same 623 held-out development
bars:

1. `engine-unchanged`: the current engine product, with zero fits;
2. `fixed-checker-consensus`: replace the engine product only when BTC and
   NNLS canonical products agree with each other, differ from the engine, and
   both have at least 75% coverage and dominance; zero fits;
3. `one-fit-source-selector`: one fixed multinomial selector chooses engine,
   BTC, NNLS, or abstain from the retained 64 confidence features.

The source-selector target precedence is frozen as: engine if correct; else BTC
if correct; else NNLS if correct; else abstain. At forced full coverage, an
abstain action falls back to the engine so missing output cannot inflate
accuracy. Selective metrics exclude abstain actions.

The sole fitted estimator is median-imputed, standardized, class-balanced
logistic regression with `C=1.0`, `solver=lbfgs`, `max_iter=1000`, and random
state `20260825`. No estimator, feature, weight, fold, rule, or threshold search
is allowed.

## Frozen metrics

Primary full-coverage metrics:

- correct count and product accuracy;
- changed-bar count;
- helpful wrong-to-right corrections;
- harmful right-to-wrong corrections;
- wrong-to-different-wrong changes;
- net correct gain versus the unchanged engine;
- the same readout per dataset.

Selective precision and coverage are reported descriptively at the already
fixed thresholds `0.50`, `0.80`, `0.90`, `0.95`, and `0.98`. The unchanged
engine uses its selected-product probability, fixed consensus uses checker
dominance on changed bars and engine probability otherwise, and the one-fit
selector uses its maximum action probability while excluding abstain actions.
These confidence meanings differ and may not be treated as a tuned promotion
comparison.

## Hard execution cap

- new BTC inference passes: zero;
- new NNLS feature passes: zero;
- correction candidates: exactly three;
- fitted candidates: exactly one;
- total fits: exactly one;
- parameter searches: zero;
- automatic retries: zero;
- calibration/test/confirmation evaluations: zero;
- subagents: zero;
- runtime, localhost, promotion, or deployment changes: zero.

The run stops after the one development report regardless of outcome. Any
later work requires a new explicit decision.

## Files changed

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`
- this preregistration

Generated output remains ignored beneath
`~/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/bounded-consensus-development-v1/`.

## Tests and checks

Pending before the run: focused pytest, Ruff, JSON/reference admission
preflight, and `git diff --check`.

## Risk assessment

Medium. A source-selection model can improve full-coverage accuracy, but it can
also introduce harmful corrections. The frozen metrics expose both. This is
one development holdout and cannot establish production or general-song
accuracy.

## Human decision needed

No. The user explicitly approved this bounded correction run. A later sealed
evaluation or runtime integration requires new approval.

## Safe-to-stage exact file list

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`
- `docs/handoffs/task-completions/2026-08-25-1700-15-bounded-correction-fusion-preregistration.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `~/Documents/Pocket Steel/tmp/`
- all audio, references, generated caches/reports, model weights, credentials,
  and unrelated files

## Recommended next lane

Lane 15: run the one correction-fusion development command, write the terminal
result handoff, and stop.

## Commit readiness

Safe to commit after focused tests.

## Suggested next step

Execute the one preregistered correction-fusion command and report the result
without another experiment.
