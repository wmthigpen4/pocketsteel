# Dataset-balanced factorized challenger

## Task summary

Added an explicit `--dataset-balance` factorized-training challenger without running training. When enabled, the trainer computes deterministic inverse effective-frame-mass scales from the train split only. Effective mass includes valid frame count, the cached composition/training weight, and `trainingWeightOverride`; the normalization preserves total train mass while equalizing each dataset's contribution.

The scales affect only training loss numerators and training class-frequency weights. Development remains unweighted, and epoch selection changes from pooled frame-micro scoring to the unweighted macro average of the existing selection score across development datasets. Calibration, test, and steel-test tracks are excluded from fitting and model selection.

A present split protocol is now self-validated before training. The factorized-cache benchmark CLI also validates a present protocol before entering the benchmark function. Legacy manifests with no `splitProtocol` field remain supported and model configuration records the protocol as absent.

Model configuration now carries a complete training contract: dataset masses/scales, selection aggregation and score coefficients, partition roles, split assignment/train/development/calibration/output hashes, cache hash, feature/optimization/loss contracts, actual class weights, history by development dataset, and the final weights hash.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1509-20-dataset-balanced-factorized-challenger.md`

## Tests/checks run

- Focused factorized and split-protocol tests: 41 passed, 1 skipped.
- Broader new chord-reader suite: 173 passed, 2 skipped.
- Ruff on factorized implementation, CLI, and factorized tests: passed.
- Python compile check for factorized implementation and CLI: passed.
- Exact-path `git diff --check`: passed.

## Risks

- This adds a challenger contract only; no model was trained and no accuracy claim follows from it.
- Dataset balancing changes gradient weighting and epoch selection together by design. It must be compared against an otherwise identical unbalanced control with the same frozen split protocol.
- Direct callers of the benchmark function do not self-validate because the assigned scope excluded `benchmark.py`; the owned CLI entry does validate.

## Human decision needed

None before running the approved architecture tournament. Promotion still requires development selection followed by sealed evaluation.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1509-20-dataset-balanced-factorized-challenger.md`

## Files that must not be staged

- Generated feature caches, model weights, benchmark reports, audio, private corpus artifacts, and unrelated dirty files.

## Recommended next lane

Lane 20 may train one dataset-balanced challenger and its same-seed unbalanced control from the validated train partition. Lane 15 should compare their development-dataset macro histories before either receives a single sealed evaluation.

## Commit readiness

Implementation and focused tests are ready for parent-task integration. Nothing was staged or committed.
