# Bounded correction-fusion development result

## Task summary

The user approved one bounded development run to determine whether the retained
BTC and NNLS sources could improve chord accuracy by correcting the engine's
selected chord. The preregistered run is complete. Both correction candidates
reduced full-coverage accuracy, so automatic chord rewriting is a no-go.

The current engine remains the best full-coverage candidate. BTC and NNLS
remain useful as confidence and abstention features, but this result does not
support using either source to replace the engine's chord.

## Result

The held-out development split contained 623 bars.

| Candidate | Correct | Full-coverage accuracy | Changed | Helpful | Harmful | Wrong to other wrong | Net gain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Engine unchanged | 498/623 | 79.936% | 0 | 0 | 0 | 0 | 0 |
| Fixed BTC+NNLS agreement correction | 495/623 | 79.454% | 6 | 1 | 4 | 1 | -3 |
| One-fit source selector | 486/623 | 78.010% | 46 | 11 | 23 | 12 | -12 |

The fixed rule lost 0.482 percentage points against the engine. The trained
source selector lost 1.926 percentage points. In both cases, harmful
right-to-wrong changes outnumbered helpful wrong-to-right changes.

## Per-dataset result

| Dataset | Engine unchanged | Fixed correction | One-fit selector |
| --- | ---: | ---: | ---: |
| AAM | 35/35 (100.000%) | 35/35 (100.000%) | 35/35 (100.000%) |
| GuitarSet | 91/178 (51.124%) | 88/178 (49.438%) | 83/178 (46.629%) |
| IDMT Guitar | 107/118 (90.678%) | 108/118 (91.525%) | 103/118 (87.288%) |
| NRGCP | 151/157 (96.178%) | 150/157 (95.541%) | 152/157 (96.815%) |
| Winterreise | 114/135 (84.444%) | 114/135 (84.444%) | 113/135 (83.704%) |

Small isolated gains on IDMT or NRGCP did not generalize across the five
datasets and do not offset the aggregate regression.

## Confidence-only comparison

At the frozen 0.98 source-selector threshold, correction fusion accepted
241/623 bars and got 237 correct: 98.340% point precision at 38.684% coverage.
Its one-sided 95% Wilson lower bound is 96.354%.

The already retained correctness selector remains better: 247/248 correct,
99.597% point precision at 39.807% coverage, with a one-sided 95% Wilson lower
bound of 98.213%. This supports BTC and NNLS as confidence features only. It
does not mean the engine has 98% accuracy at full coverage; the unchanged
engine measured 79.936% on this held-out development split.

## Execution accounting

- correction candidates: three;
- fitted candidates: one;
- total fits: one;
- parameter searches: zero;
- automatic retries: zero;
- new BTC inference passes: zero;
- new NNLS feature passes: zero;
- reference outcomes reproduced before fitting: 1,585/1,585;
- calibration, test, confirmation, and private-song evaluations: zero;
- sealed evaluation opened: no;
- localhost, runtime, promotion, or deployment changes: zero;
- subagents: zero.

The fit used 962 examples and evaluated 623 examples on the frozen group split.
Its action targets were engine 831, BTC 23, NNLS 12, and abstain 96. No second
fit, adjusted rule, or follow-on experiment was run.

## Artifact integrity

- correction report:
  `~/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/bounded-consensus-development-v1/correction-report.json`
- report canonical SHA-256:
  `bdff5f79982fbe8d80c9d3db4434c4b7a6d2c7839523c715bb22f45845d4668f`
- reference-row SHA-256:
  `01e165e27827f44fc2b1e79c0629fba98362fad007c27674154d81e70ccdc9cd`
- group-assignment SHA-256:
  `ba4c110f32b49b0328e19c14a18749092f1c32120b440a0a4661901c7bcb4f8d`

The report's embedded canonical hash was independently recomputed and matched.
All report floats were checked and are finite.

## Tests and checks

- `pytest -q tests/test_bounded_consensus_development.py`: 9 passed;
- Ruff check: passed;
- Ruff format check: passed;
- `git diff --check`: passed;
- reference admission: 185 tracks and 1,585 bar outcomes exactly reproduced.

The focused test emits three NumPy runtime warnings in its synthetic NNLS
template calculation (`divide by zero`, `overflow`, and `invalid value` during
matrix multiplication). The assertions still pass, and the stored run report
contains no non-finite values. The warning is a numerical-stability risk to
address before treating this research harness as production code.

## Files changed

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`
- `docs/handoffs/task-completions/2026-08-25-1700-15-bounded-correction-fusion-preregistration.md`
- this terminal result handoff

The harness, tests, and preregistration were committed in `8156fd61`. Generated
caches and reports remain outside the repository under the ignored `tmp/`
workspace.

## Risk assessment

Medium. This is a development holdout, not a sealed production evaluation, and
it cannot establish general-song accuracy. GuitarSet remains the largest
weakness at 51.124% for the unchanged engine. Automatically applying the tested
corrections would make accuracy worse. The 98% confidence result applies only
to the accepted subset, not every bar.

## Human decision needed

No decision is needed to preserve the current confidence-only design. Any new
model family, new training data, sealed evaluation, runtime integration, or
automatic correction strategy requires a separately bounded plan and explicit
approval.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-25-1720-15-bounded-correction-fusion-result.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `~/Documents/Pocket Steel/tmp/`
- all audio, references, generated caches/reports, model weights, credentials,
  and unrelated files

## Recommended next lane

Stop this experiment. Keep BTC and NNLS as confidence/abstention features, do
not use them for automatic chord correction, and leave the localhost chord
reader unchanged.

## Commit readiness

Safe to commit this terminal handoff only.

## Suggested next step

If the user authorizes another bounded accuracy project later, target the
underlying engine and the GuitarSet-like failure cases with a genuinely
different model or better labeled training data. Do not continue tuning this
correction-fusion approach.
