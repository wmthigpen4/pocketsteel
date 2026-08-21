# Beat-cell Stage-2 R4 readiness failure receipt

Date: 2026-08-21  
Source cycle: `beat-cell-stage2-r4`  
Implementation HEAD: `edec952077c42c31bed280cb7e3994ec335a318e`  
Disposition: terminal; same-cycle retry is forbidden

## Official invocation

The sole R4 readiness evaluation was invoked from
`/Users/cory/Documents/Pocket Steel/chord-reader-development` with exactly:

```sh
/usr/bin/env -u PYTHONWARNINGS PYTHONDONTWRITEBYTECODE=1 \
  '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python' \
  scripts/chord_beat_cell_readiness.py
```

The process exited `1`, emitted no stdout receipt, and ended with:

```text
steel_guitar_rag.chord_reader.beat_cell_readiness.BeatCellReadinessError: A joined row ordered feature vector disagrees with featureValuesSha256.
```

The exact traceback reached
`run_beat_cell_readiness` -> `evaluate_beat_cell_readiness` ->
`validate_beat_cell_readiness_artifact` -> `_validate_public_rows`, with the
exception raised at the committed `beat_cell_readiness.py` line 2161.

## Frozen inputs and implementation

- R4 authority path:
  `docs/handoffs/task-completions/2026-08-21-1019-20-beat-cell-stage2-r4-final-source-amended-preregistration.json`
- authority raw SHA-256:
  `329bb235e760a9c665945817b21d4ea0e9d824a26251a668cad4d47fa5b7e2a1`
- authority canonical SHA-256:
  `a606cfefb1026bc29d335aeb9e73f0adead459a6e789e550aaff35bca214e7c9`
- readiness projection SHA-256:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`
- one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`
- consumed readiness implementation SHA-256:
  `505da80afea102a7d66c4655b2f11865ac154915895d1d1f32ea4d3c06ffa18a`
- readiness CLI SHA-256:
  `cc0c68ff11b654f8e17f4dc9c8a746c88e543be14d8188e2cf1189304e9b77dd`
- Stage-1 raw SHA-256:
  `0263746165db4f7388aa8ae2e8d8f39e7583f0719cde01718bce4bd5d498adec`
- examples raw/artifact SHA-256:
  `4afd0bea0e2db29c71ce503caa56651006d2dd90c6d09076a92f097d992646db` /
  `4338ba6a3b288d97b9c9bc22d8acb515912198b6ac2567e29eb5b3bdb7320150`
- selector raw/artifact SHA-256:
  `cbd99d98df6c37705ac73a27fadb18a7f81b92adc9134a411a5067ea72518ac8` /
  `269dec163c874f77a76f4e1269f2bb6137a4e588a68c152cfac2637e915328bd`

The Stage-1, examples, and selector files were unchanged throughout the
invocation. The selector had already passed independent canonical, source,
OOF, metric-recomputation, and optimizer-convergence validation.

## Control-flow receipt

Before the exception, the process completed in memory:

- the exact Stage-1, examples, and selector admissions;
- the one permitted deterministic reproduction refit, object-identical,
  canonically identical, and byte-identical to the sealed selector;
- the 9,376-row OOF join and Stage-1 cross-check;
- stored-metric recomputation and the fixed 0.50 descriptive cutoff;
- all readiness metric, gate, diagnostic, decision, and artifact assembly.

The final standalone artifact validator then rejected the first joined row.
No gate value or pass/fail decision from this invalid in-memory artifact is an
authoritative readiness result.

The exception occurred before `_publish_new_json`. The exact R4 readiness
directory and report are absent, no temporary or linked publication name
exists, and the worktree remained clean at the implementation HEAD.

The later type-preservation diagnosis produced these fix-only, uncommitted
receipts:

- corrected readiness module SHA-256:
  `225773bd6fc32c43b1308afa46b1648317b3200c1a5cb32c49ad18c584505306`;
- focused readiness-test module SHA-256:
  `4bc06c16ef91bc166998af0531d68adf442e5536b8fa47e1f3b0a1b3e8a67d76`;
- unchanged readiness CLI SHA-256:
  `cc0c68ff11b654f8e17f4dc9c8a746c88e543be14d8188e2cf1189304e9b77dd`.

The focused suite passed `178` tests. The broad non-browser suite passed
`914` tests with `4` skipped and exactly `3` real-browser tests deselected.
These receipts prove the narrow fix in isolation; they are not final recovery
implementation hashes and authorize no execution.

## Root cause

The examples artifact intentionally contains mixed JSON numeric types. The
integer-valued `predictionTransitionCount` and five `productFamily*`
indicators are sealed as JSON integers. `_feature_vector` validated those
values through `_finite` but retained the returned Python `float`, while it
copied the SHA-256 of the original typed mapping. `_validate_public_rows`
repeated the lossy conversion. Canonical JSON distinguishes `0` from `0.0`,
so the vector could not reproduce its source mapping hash.

A read-only post-failure census proved the same type-only mismatch for all
9,376 joined rows. Retaining the original integer/float types reproduces all
9,376 source hashes. Feature order, numerical values, the trained selector,
folds, weights, cutoff, and readiness formulas were not the cause.

## Governance disposition

R4 consumed exactly one readiness evaluation and exactly one readiness
reproduction refit. Its authority states `sameCycleRetryAllowed: false`.
Therefore R4 is closed and must not be retried, repaired in place, or used to
claim readiness.

Calibration, test, confirmation, player, public-song, browser, threshold,
promotion, and deployment access all remain closed. No such surface was
opened by the failed invocation or the diagnosis.

Any recovery must be separately preregistered, use a distinct readiness
output path, disclose cumulative evaluation/refit counts, reuse the immutable
R4 feature/examples/selector artifacts without rebuilding or retraining them,
freeze the type-preservation repair and tests, pass an independent clean-HEAD
audit, and receive a fresh explicit execution authorization. This receipt
does not itself authorize that execution.
