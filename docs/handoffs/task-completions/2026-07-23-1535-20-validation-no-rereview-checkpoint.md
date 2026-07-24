# Lane 20 — Validation no-rereview checkpoint

## Task summary

Continued the approved Amazing Tablature engineering goal from clean challenger
`at-90360274fad075f6`.

Completed:

- Upgraded the two independently score-verified licks lines to the stable v9
  execution-lineage contract.
- Rebuilt the current licks contact consensus without using human validation
  answers as training evidence.
- Rescored the exact challenger across both authoritative validation cohorts.
- Verified 23 independently score-supported decisions with exact score/tab
  alignment.
- Added exact-equivalence carry-forward for prior expert disagreement
  adjudication.
- Proved that all four current misses have the same decision identities,
  source movements, candidate sets, candidate scores, and winning indexes as
  the previously reviewed packet.
- Reused the immutable prior verdict without another human review.
- Kept validation ineligible for training and kept both sealed tests unopened.

Exact private checkpoint:

- Exact challenger: `at-90360274fad075f6`.
- Current score report:
  `c17dfaa7085bd4ce48db94e7d4f7316b6af6f483e32ffd02eb2d3e1eac1cd5f8`.
- Exact no-rereview certificate:
  `983f07ffabd44ec1f95d5ec313e226a22e1883031122fc3ada02dd813cfb202d`.
- Strict source-exact preference: 64/68, or 94.1176%.
- Expert-accepted preference: 65/68, or 95.5882%.
- Top-three coverage: 68/68, or 100%.
- Main cohort: 22/22 accepted, or 100%.
- Licks cohort: 43/46 accepted, or 93.4783%.
- Score-supported evidence: 23/23, or 100%.
- Tab-only evidence: 42/45 accepted, or 93.3333%.
- Source and predicted mechanical validity: 68/68, or 100%.
- Four prior disagreements: one challenger-valid alternate and three
  source-preferred outcomes; zero unresolved.

The fixed preference, cohort, evidence-mode, top-three, and mechanical
thresholds now pass after exact prior adjudication. The canonical gate remains
closed for one reason: machine consensus is not complete human validation
ground truth. This checkpoint does not weaken that predeclared rule.

Intentionally not completed:

- No validation evidence entered discovery or training.
- No challenger artifact or accepted-decision ledger changed.
- No model was enabled, promoted, or frozen.
- No sealed-test membership, imagery, ground truth, or result was opened.
- No runtime, UI, deployment, auth, embeddings, vector stores, or raw source
  files were changed.

## Files changed

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

Private ignored receipts and reports remain beneath
`corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `.venv/bin/ruff check docs/amazing-tablature-training.md steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_validation.py tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py`
  - PASS: 228 passed.
- `.venv/bin/pytest -q`
  - PASS: 1,441 passed in 77.28 seconds.
- `git diff --check`
  - PASS.
- Exact v9 score recapture:
  - Two score-supported lines applied.
  - Human truth used: false.
  - Validation may train: false.
  - Sealed test accessed: false.
- Exact adjudication equivalence:
  - Four of four disagreements equivalent.
  - Human rereview required: false.
  - Validation may train: false.
  - Sealed test accessed: false.

## Integration notes

The model-quality question is no longer the blocker. The exact challenger
passes every fixed recommendation metric after carrying forward the one
previously accepted alternate:

- overall accepted preference is strictly greater than 95%;
- both cohorts exceed 90%;
- both evidence modes exceed 90% with sufficient denominators;
- top-three and mechanical gates are perfect.

The remaining gate is evidentiary. The current 68-decision diagnostic comes
from nine machine-complete validation lines; it is not a complete human
ground-truth validation program. Do not privately enable, freeze, or open
sealed test merely from this diagnostic.

The smallest responsible next slice is a Lane 15 review of a compact,
line-level canonical verification contract. It should reuse every immutable
prior review, present no blank or incomplete capture, and ask the user only
about complete lines whose current score and tablature can be visually
verified together. The contract may not lower or redefine the fixed accuracy
thresholds after seeing validation.

## Risk assessment

Risk: medium.

Carry-forward is fail closed and compares preference-relevant evidence
exactly. Page-level diagnostic tags may change after unrelated score repair,
but source movement, candidates, ranks, and scores may not. The primary
remaining risk is treating high-confidence machine consensus as complete human
ground truth; the canonical gate continues to prevent that.

Rollback is the scoped implementation commit. Private validation artifacts are
regenerable from digest-pinned source and prior receipts.

## Human decision needed

No immediate decision for this checkpoint.

Human validation will be needed before canonical enable/freeze. Lane 15 should
first reduce that request to the smallest complete line-level packet and prove
that all already reviewed evidence is carried forward.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1535-20-validation-no-rereview-checkpoint.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- `corpus-private/**`
- Raw images, private submissions, model artifacts, validation reports,
  embeddings, indexes, auth, or deployment artifacts

## Recommended next lane

Lane 15 QA / Answer Eval.

## Commit readiness

Safe to commit

## Suggested next step

Independently audit the exact no-rereview certificate and define the smallest
complete line-level human ground-truth verification needed to satisfy the
existing canonical contract, without opening either sealed test.
