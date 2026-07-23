# Lane 20 — Validation preference adjudication

## Task summary

Added an immutable, no-training scorer for a submitted compact validation
disagreement packet. The scorer keeps the original source-exact metric and
adds a separate human-accepted recommendation metric; it does not rewrite
ground truth or weaken any predeclared threshold.

For exact challenger `at-e00734bee5dea6fc`:

- strict source-exact top choice: 64/68 (94.1176%)
- human-accepted top choice: 65/68 (95.5882%)
- main cohort: 22/22 (100%)
- licks cohort, strict: 42/46 (91.3043%)
- licks cohort, human-accepted: 43/46 (93.4783%)
- top-three coverage: 68/68 (100%)
- source and predicted mechanics: 68/68 (100%)
- user adjudication: three source-preferred, one challenger-valid
- unresolved adjudications: zero
- adjudicated preference thresholds: passed

Canonical validation, rules freeze, private runtime enablement, and sealed test
remain blocked because this evidence is machine-consensus tab-only evidence,
not complete human validation ground truth, and it contains zero independently
confirmed `alignment:score_supported` decisions.

## Files changed

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- this handoff

No model, accepted-decision ledger, source file, split manifest, or sealed-test
artifact was modified.

## Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_training.py scripts/amazing_tablature.py`
  - passed
- `.venv/bin/ruff check pocketsteel/amazing_tablature_training.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py`
  - passed
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py -k 'machine_validation_scorer'`
  - 1 passed, 42 deselected
- `.venv/bin/pytest -q`
  - 1,435 passed

The exact private command was:

```text
.venv/bin/python scripts/amazing_tablature.py adjudicate-validation-machine-disagreements at-e00734bee5dea6fc --batch-id atb-20260716-licks-34 --score-report-digest a67abec65b5a836772ceb8130c54409a6709b1c20698700d61deff4a3f5d23c3 --submission-id validation-disagreement-submission-744c93fd5fc503bf7d1a
```

The pre-commit verification report was
`validation-evaluations/at-e00734bee5dea6fc/machine-consensus-adjudication-174436ba7fd64872fc561ce6afa7bb27c7a570a252161a5c01fbae0429cc98b8.json`.
It remains private and ignored.

## Integration notes

`challenger_valid` and `both_valid` count only in the separate accepted
recommendation metric. `source_preferred` remains a miss; `feedback` remains
unresolved. The strict source-exact numerator and denominator are retained
unchanged in every adjudication report.

The scorer requires the exact model SHA, score-report digest,
disagreement-report digest, packet digest, submission ID, submission digest,
and authoritative batch. Every accepted row remains
`trainingEligible: false`. It writes only a private evaluation report.

The clean-HEAD challenger `at-90360274fad075f6` remains a distinct artifact.
This submission is pinned to `at-e00734bee5dea6fc`; no adjudication is
silently transferred across artifacts. Its current validation extraction must
finish and be scored independently.

## Risk assessment

Medium. Preference quality now clears its fixed threshold after explicit
expert adjudication, but the overall canonical evidence contract is not met.
Treating this report as a promotion pass would be incorrect.

Rollback is the implementation commit only. Retain the immutable private
submission and evaluation reports for audit lineage.

## Human decision needed

No. The expert adjudication has already been received and scored. Do not ask
for more review until Lane 20 has produced independently score-supported,
complete, mechanically coherent candidates.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1413-20-validation-preference-adjudication.md`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`

## Files that must not be staged

- `corpus-private/`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated untracked historical handoffs
- generated reports, packets, logs, and model artifacts

## Recommended next lane

Lane 20.

## Commit readiness

Safe to commit.

## Suggested next step

Commit this scorer, rerun the adjudication so its lineage pins the committed
code, then finish and independently score challenger
`at-90360274fad075f6`. Continue automated score-reader and score/tab
completeness work; do not enable runtime or open sealed test until the
score-supported fixed gate is genuinely satisfied.
