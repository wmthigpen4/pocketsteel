# Beat-cell Stage-2 R2 Stage-A failure receipt

Date: 2026-08-21

## Outcome

The one authorized R2 Stage-A invocation was consumed and failed closed during
label-blind feature construction. R2 is closed and must not be retried.

The failure is a code-only product-winner cross-check inconsistency between
the frozen Stage1 prediction-summary path and the separately frozen Stage-A
feature-math path. It is not source-data drift, label access, a selector fit,
a readiness result, or a protected-surface result. No threshold, feature,
fold, salt, weight, grid, dataset, cell, gate, or cutoff may be changed in
response.

## Consumed authority and invocation

The failed invocation was bound to:

- repository HEAD:
  `a43bb4fbeaa4395e31682622c63b9cc02247c1ca`;
- R2 authority:
  `docs/handoffs/task-completions/2026-08-21-0658-20-beat-cell-stage2-r2-recovery-preregistration.json`;
- R2 authority raw-file SHA-256:
  `7fd598ec952c22ae3a59d4d28d66333f75cb88cdc9348e46566063d7d1709b34`;
- R2 authority canonical-object SHA-256:
  `33e74034f0bab7b9a8f146188835306f535a158f68bb5bcf66bb0d265d69dd2a`;
- R2 feature-math projection SHA-256:
  `65fc42417c1b45201e02fe35f140fee541f20608f08fbe6f2d92c127e4009ef2`;
- R2 one-shot projection SHA-256:
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
steel_guitar_rag.chord_reader.beat_cell_examples.BeatCellExamplesError: Stage-A feature math disagrees with the frozen Stage-1 cross-checks.
```

The exception was raised at
`steel_guitar_rag/chord_reader/beat_cell_examples.py:1194` in the exact failed
HEAD.

## Exact label-blind mismatch

The first and only R2-policy product mismatch in official sorted track order
was:

- sorted track ordinal: `244` zero-based, the 245th of 246 tracks;
- track ID: `winterreise-schubert_d911-20_hu33`;
- cell index: `75`;
- interval: `[50852,51548)` milliseconds;
- source beat-cell SHA-256:
  `a3739deae1523c937dd7d6cf0cf6de1b90285b5fa58c4572fde9c64ba714bf1b`;
- construction SHA-256:
  `5850f6d13500ad3cb4ec7a755566286aa5ef0108c5d34e2ccf469e4465111a43`;
- prediction-identity SHA-256:
  `c2308add145580573b02734e1e6a589a98d0fff198c89a27308c16b977f6a00b`;
- source beat-receipt-track SHA-256:
  `dea32e9291ece0bd09b98cefd0d67eb8b8ffbe9f38cde701e28edbc90be6152d`;
- prediction leaf relative path:
  `predictions/factorized/winterreise-schubert_d911-20_hu33.json`;
- prediction leaf raw-file SHA-256:
  `112bb730f4638e1c6bbf69981cf06c8083a65e19908e781031e66b41b9dab38d`;
- prediction-only sidecar raw-file SHA-256:
  `ab698ea8989324c29de64a743174c82f4c2b82848f4be910cc7492e5ea0a34e8`;
- prediction-only sidecar artifact SHA-256:
  `d71d7a3520329ce79dd45ea51065ed8b6b536343869f7bf6cf57f200de6d0880`;
- frozen prediction-summary SHA-256:
  `cb8c4215f0ac4aaf2c43634013811c0eb9d450a4866c154868fe3d7154bde32e`.

Both paths computed exact product-overlap totals of
`C7=0.347999999999999` and `Fm=0.3480000000000061`. Their difference was
`7.105427357601002e-15`, below the frozen `1e-9` epsilon. Both products were
therefore members of the Stage-A tolerant winner-candidate set.

The frozen Stage1 exact-maximum path selected `Fm`. Its cross-check values
were:

- `predictionProduct`: `Fm`;
- `predictionCoverage`: `1.0`;
- `predictionDominance`: `0.5000000000000088`.

The frozen R2 Stage-A tolerant-winner path selected lexicographic minimum
`C7`. Its values were:

- `predictionProduct`: `C7`;
- `predictionCoverage`: `1.0`;
- `predictionDominance`: `0.49999999999999856`.

Coverage was identical. The dominance delta was
`1.021405182655144e-14`, so the frozen
`math.isclose(rel_tol=0,abs_tol=1e-9)` comparison passed. The feature-name,
source-cell hash, cell-index, start, and end comparisons also passed. Only
exact product equality failed.

Under the frozen Stage1 scoring policy SHA-256
`acb716b4f278c07a5696bf0166601a154a3a2dfce2ca596b8101543a74d766a9`,
both value triples are structurally ineligible because each dominance plus
the `1e-9` comparison epsilon remains below the `0.75` minimum. This fact is
label-blind and was determined without opening an outcome object.

A read-only label-blind sweep over all 11,234 admitted cells found:

- tolerant-winner/Stage1 product mismatches: `1`, exactly the row above;
- coverage mismatches at absolute tolerance `1e-9`: `0`;
- dominance mismatches at absolute tolerance `1e-9`: `0`;
- unexpected reconciliation rows: `0`.

The complete frozen Stage1 prediction summary recomputed canonical-equal
before the failing comparison. The mismatch is therefore code-path semantics,
not changed source bytes or a stale sidecar.

## Work reached and protected-access boundary

Before the exception, the runner completed exact runtime, beat-receipt,
audio-lineage, prediction-sidecar, and prediction-leaf admission. Full audio
lineage validation and reference-free re-extraction completed. The Stage1
report remained opaque: it was read only for raw bytes, inode identity, and
raw SHA-256 and was never parsed as JSON.

In official sorted order, `244` complete feature summaries containing
`10,523` rows were built in memory. The failing track then appended rows `0`
through `74`, bringing the in-memory completed-row count to `10,598`. Feature
math for cell `75` was computed, but the row was not appended because the
frozen cross-check raised first. The remaining `635` cells were not reached.

Exact zero counts are:

- Stage1 report JSON parses: `0`;
- Stage1 outcome-object accesses: `0`;
- group/reference-object accesses: `0`;
- published feature summaries or manifests: `0`;
- examples artifacts built: `0`;
- selector candidate fits: `0`;
- readiness evaluations or reproduction fits: `0`;
- calibration, test, confirmation, player/public-song, deployment, or Travis
  accesses: `0`.

No Stage-B outcome classification was opened during the R2 attempt or the
label-blind failure diagnosis. Any future Stage-B handling of this exact row
must be prospectively constrained by a new authority before Stage1 outcomes
are admitted.

## Zero-publication and cleanup proof

The exception occurred while constructing the in-memory `summaries` list,
before the feature manifest and before the `TemporaryDirectory` publication
scope. Independent post-failure inspection found absent:

- `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2-r2`;
- every R2 feature-set, examples, selector, and readiness descendant;
- every `beat-cell-stage2-r2*` or `.beat-cell-stage2-r2*` sibling under the
  official experiment root;
- every `beat-cell-stage2-features-*` directory under the active system
  temporary root.

No cleanup was performed or required. Repository HEAD remained the exact
failed commit and the worktree remained clean immediately after the failed
attempt and independent diagnosis.

## Recovery boundary

R2 is terminal. A further attempt requires a distinct R3 namespace, a new
machine authority, a clean implementation commit, and independent preflight.
The R3 authority must bind this exact prediction-only mismatch and freeze the
tolerant-winner reconciliation before execution. The reconciliation may pass
only for the exact preregistered inventory, only when both Stage-A and Stage1
values are structurally ineligible, and at Stage B only when the corresponding
outcome is `U` or `N` and emits no example. Every other product mismatch must
fail closed.

That semantic rule was selected without labels, selector fits, readiness
results, or protected data. All original data, cells, winner product, 48
feature formulas, gates, folds, salts, weights, grids, datasets, thresholds,
access rules, and one-shot limits remain frozen.
