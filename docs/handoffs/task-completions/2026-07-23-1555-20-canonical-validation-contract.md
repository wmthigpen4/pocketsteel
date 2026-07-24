# Lane 20 — Canonical validation contract

## Task summary

Implemented the bounded human-ground-truth gate required before private
runtime comparison for exact challenger `at-90360274fad075f6`.

Completed:

- Added an immutable private decision ledger to automatic machine-candidate
  validation scoring.
- Bound every scored decision to its exact cohort, complete line, candidate,
  and execution digest.
- Added a dataset-wide canonical review packet that combines every
  authoritative cohort into one review.
- Required exact coverage of every scored validation decision exactly once.
- Rejected blank, incomplete, unresolved, mechanically invalid, stale, or
  lineage-mismatched lines.
- Added a one-line-per-screen ten-string tablature review console.
- Omitted unsupported machine-score rows on tab-only lines.
- Required score pitch and octave confirmation only for independently
  score-supported lines.
- Reduced a correct line to one explicit choice while retaining local
  autosave, correction comments, previous/next navigation, and immutable
  submission.
- Preserved prior source-versus-challenger preference adjudication without
  rereview.
- Added canonical scoring against the exact score report, decision ledger,
  packet, submission, adjudication report, and no-rereview equivalence
  certificate.
- A canonical pass marks the exact model eligible for private comparison and
  rules freeze, but does not promote beta/stable or open sealed test.

Validation ground truth remains ineligible for training. The accepted
discovery ledger and model artifact are not modified.

Intentionally not completed in this slice:

- No private canonical packet was generated before this implementation was
  committed.
- No human validation receipt was fabricated.
- No model was enabled, promoted, or frozen.
- No sealed-test data was opened.
- No runtime, deployment, auth, embeddings, vectors, or raw source changed.

## Files changed

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

## Tests and checks

- `.venv/bin/ruff check docs/amazing-tablature-training.md steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py`
  - PASS: 228 passed.
- `.venv/bin/pytest -q`
  - PASS: 1,443 passed in 78.82 seconds.
- `git diff --check`
  - PASS.

Focused tests prove:

- the decision ledger is immutable, digest-pinned, validation-only, and
  sealed-test-free;
- incomplete canonical submissions fail;
- score-supported lines require score confirmation;
- all canonical lines and scored decisions must be covered once;
- canonical validation never writes accepted training decisions;
- human confirmation alone cannot bypass fixed preference sample or accuracy
  thresholds.

## Integration notes

After this code is committed, regenerate the exact machine score report so its
evaluation-code revision and decision ledger pin the committed implementation.
Then regenerate exact no-rereview adjudication, prepare the single canonical
packet, and smoke-test it locally.

The canonical packet is anchored under the authoritative dataset and contains
both cohorts. It is not two separate review jobs. Tab-only lines do not display
an empty score row or imply that score recognition was verified.

## Risk assessment

Risk: medium.

The contract is fail closed and extensively tested. The remaining material
risk is that only nine current machine-complete validation lines cover the 68
ranker decisions. Passing this human gate authorizes private comparison and
rules freeze under the fixed contract, but only the untouched sealed program
can establish generalization.

Rollback is the scoped implementation commit. Private generated ledgers,
packets, and reports remain ignored and regenerable.

## Human decision needed

No immediate decision.

The next human action is the single canonical packet after local smoke passes.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1555-20-canonical-validation-contract.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- `corpus-private/**`
- Raw source, private review submissions, generated model/evaluation artifacts,
  embeddings, indexes, auth, or deployment files

## Recommended next lane

Lane 20 Amazing Tablature Training, followed by independent Lane 15 audit of
the generated packet contract.

## Commit readiness

Safe to commit

## Suggested next step

Commit this exact implementation, regenerate the exact score and no-rereview
lineage, generate the one combined canonical packet, and stop only when its
browser smoke passes and it is ready for the user.
