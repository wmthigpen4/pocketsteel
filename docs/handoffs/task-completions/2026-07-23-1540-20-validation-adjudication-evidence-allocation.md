# Lane 20 — Validation adjudication evidence allocation

## Task summary

Completed a focused follow-up to the exact validation no-rereview
certificate.

The adjudication scorer now assigns each human-accepted or unresolved
disagreement to its actual evidence class from the immutable disagreement
record. It no longer assumes every adjudicated alternative belongs to
`alignment:tab_only`.

For the current four carried-forward judgments, all four are genuinely
tab-only, so the measured result is unchanged:

- overall expert-accepted preference: 65/68, or 95.5882%;
- score-supported: 23/23, or 100%;
- tab-only expert-accepted: 42/45, or 93.3333%;
- top-three and source/predicted mechanics: 100%;
- fixed preference thresholds: passed;
- canonical gate: still closed because machine consensus is not complete human
  validation ground truth.

No validation decision entered training, no model or accepted-decision ledger
changed, and neither sealed test was opened.

## Files changed

- `steel_guitar_rag/amazing_tablature_training.py`
- This handoff.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_training.py steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_training.py steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py -k 'machine_validation'`
  - PASS: 2 passed.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py -k 'validation'`
  - PASS: 22 passed.
- `.venv/bin/pytest -q`
  - PASS: 1,441 passed in 67.48 seconds.
- `git diff --check`
  - PASS.

## Integration notes

The current exact carry-forward still allocates one accepted challenger
alternative and three source-preferred results to the tab-only evidence class.
The score-supported class remains 23/23 with no carried adjudication. Future
complete disagreements will now be accounted for in their actual evidence
class without changing the predeclared thresholds.

## Risk assessment

Risk: low.

This is a reporting and gate-accounting correction. It does not alter model
weights, candidate generation, validation source evidence, or runtime
behavior. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1540-20-validation-adjudication-evidence-allocation.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs.
- Raw images, private submissions, model artifacts, validation reports,
  embeddings, indexes, auth, or deployment artifacts.

## Recommended next lane

Lane 15 independent QA of the exact certificate and canonical human-ground-
truth requirement.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact two-file slice, rerun the exact carry-forward against the
committed code, and independently verify the smallest remaining human
ground-truth requirement without opening sealed-test data.
