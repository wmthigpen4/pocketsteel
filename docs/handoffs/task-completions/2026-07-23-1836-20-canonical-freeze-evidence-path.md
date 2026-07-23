# Lane 20 — Canonical freeze evidence path

## Task summary

Updated rules freeze to recognize the newer corrected-canonical validation
contract as an alternative to legacy batch-wide extraction approval.

The alternative is accepted only when the exact evaluation:

- uses a corrected-canonical schema;
- has complete human ground truth;
- passes no-rereview accounting and every fixed metric gate;
- pins the immutable validation-decision and evaluation-code digests;
- keeps validation ineligible for training; and
- confirms the sealed tests were not accessed.

Current extraction rights are still required for every cohort. Legacy
evaluations continue to require complete extraction review and acceptance.

## Files changed

- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- This handoff

## Tests and checks

- Ruff — PASS.
- `tests/test_amazing_tablature_training.py` — PASS, 48 tests.
- `git diff --check` — PASS.

## Integration notes

This resolves a contract mismatch introduced when canonical human-confirmed
line truth replaced incomplete raw validation extraction as the arrangement
evaluation source. It does not weaken fixed metric thresholds or allow blank,
unresolved, mechanically invalid, or unreviewed canonical lines.

Because the freezer is part of the rules-code digest, perform one final exact
challenger rebuild after commit, verify unchanged weights and zero rereview,
replay the corrected validation result, then freeze.

## Risk assessment

Medium. The new branch is deliberately narrow and fail closed, but it changes
which evidence contract can authorize a freeze. Rollback is the scoped commit.

## Human decision needed

No. This is required to complete the already approved canonical validation
and freeze workflow.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1836-20-canonical-freeze-evidence-path.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty and untracked handoffs

## Recommended next lane

Lane 01 exact-path commit, then Lane 20 final clean-HEAD rebuild, validation
replay, and rules freeze.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the three exact files above and continue automatically without
another human review.
