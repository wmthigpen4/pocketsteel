# Beat-cell Stage-2 attempt 1 failure receipt

Date: 2026-08-21

## Outcome

The one authorized invocation of the original beat-cell Stage-2 Stage-A
feature command was consumed and failed closed before feature construction or
publication. The original Stage-2 cycle is closed. It must not be retried.

This is a code-only admission-field-path defect. It is not source-data drift,
a failed feature calculation, an optimizer result, or a readiness result. No
performance evidence was produced and no threshold, feature, fold, weight,
dataset, cell, gate, or cutoff may be changed in response.

## Consumed authority and invocation

The failed invocation was bound to:

- repository HEAD:
  `b8b61ee33427498e3d22c6a1f1dc7a6a9ecf3877`;
- predecessor authority:
  `docs/handoffs/task-completions/2026-08-21-0430-20-beat-cell-stage2-preregistration.json`;
- predecessor authority raw-file SHA-256:
  `674298f9077d3471e00d296dfe0925e2aa278270721544a6b7391b27cdd7cfb4`;
- predecessor authority canonical-object SHA-256:
  `fc8a8cc0ef0c408a068dc59d28d99726bd379e55d7ce9258d51835054d80dca2`;
- predecessor one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`.

The exact authorized shell command was:

```sh
cd '/Users/cory/Documents/Pocket Steel/chord-reader-development'
/usr/bin/env -u PYTHONWARNINGS PYTHONDONTWRITEBYTECODE=1 \
  '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python' \
  scripts/chord_beat_cell_features.py
```

It exited with status `1` and the terminal exception:

```text
steel_guitar_rag.chord_reader.beat_cell_examples.BeatCellExamplesError: Runtime manifest disagrees with the frozen Stage-1 source contract.
```

The exception was raised at
`steel_guitar_rag/chord_reader/beat_cell_examples.py:2827` in the exact failed
HEAD.

## Exact defect

The first three terms of the runtime-manifest admission comparison matched the
frozen Stage-1 source contract exactly:

- raw-file SHA-256:
  `9c7c171227610a6364f37888f33b3a98d5f8c16d95fe193416e5e4aee18a37f8`;
- internal manifest SHA-256:
  `e717f8b2c44f41fc7cd9557796b701225e82d3e2f5e40b66365a21b406f65ab1`;
- track-set SHA-256:
  `a9ba75338abeb6fad9c6e91adb14f4be74dcdaac6a2241afcc7efddfbe6cd0cd`.

The fourth term read the nonexistent top-level field
`runtime.get("analyzerContractSha256")`. Its actual value was `null`; the
frozen expected value was
`8e1df05daf18371899e06884006403b56a4228109687a6c7ca178f1621fef89e`.
The exact valid manifest stores that same expected digest at
`runtime["analyzerContract"]["contractSha256"]`.

The defect is therefore classified as
`code-only-runtime-analyzer-contract-field-path-v1`. A correction may change
only that admission lookup, add an exact-real-schema regression, and perform
policy-neutral recovery-authority/output-root plumbing. It may not change any
data, feature math, example mapping, selector math, readiness policy, gate, or
one-shot rule.

## Zero-work and zero-publication proof

Deterministic control flow at the exception establishes:

- opaque Stage-1 report raw reads: `1`;
- Stage-1 report JSON parses: `0`;
- Stage-1 outcome-object accesses: `0`;
- audio-lineage opens: `0`;
- prediction-sidecar opens: `0`;
- prediction-leaf opens: `0`;
- feature summaries built: `0`;
- feature rows built: `0`;
- examples built: `0`;
- selector candidate fits: `0`;
- readiness reproduction fits: `0`;
- published Stage-2 artifacts: `0`.

The runner failed immediately after strict parsing of the allowed runtime
manifest and reference-free beat receipt. It had not reached audio-lineage
admission, label-blind prediction sources, feature construction, temporary
feature staging, or any publication helper.

An independent post-failure filesystem inspection found all of the following
absent:

- `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2`;
- every original feature-set, examples, selector, and readiness descendant;
- any original-run-root `beat-cell-stage2*` or `.beat-cell-stage2*` sibling;
- any `beat-cell-stage2-features-*` directory in the active system temporary
  root.

Thus there is no partial output to adopt, delete, complete, or retry.

## Authorization boundary

The failed original cycle remains terminal even though it performed zero
feature work. The no-retry rule binds invocations, not successful
publications. Calibration, test, confirmation, player playback, arbitrary
public-song evaluation, promotion, deployment, and Travis remain closed.

A distinct recovery cycle is preregistered separately at:

`docs/handoffs/task-completions/2026-08-21-0658-20-beat-cell-stage2-r2-recovery-preregistration.json`

It is an exact copy of the predecessor machine authority except for the five
declared output paths, which use the distinct `beat-cell-stage2-r2` root. Its
raw-file SHA-256 is
`7fd598ec952c22ae3a59d4d28d66333f75cb88cdc9348e46566063d7d1709b34`
and its canonical-object SHA-256 is
`33e74034f0bab7b9a8f146188835306f535a158f68bb5bcf66bb0d265d69dd2a`.
It does not attest corrected executable code. R2 execution remains blocked
until a separate clean implementation commit and handoff bind the corrected
code and regression hashes and an independent audit passes with no P0/P1.
