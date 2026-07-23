# Lane 20 — Copedent freeze order fix

## Task summary

Fixed the rules freezer's source-copedent comparison to normalize both profile
lists by batch ID before equality checking. The challenger already pinned the
correct two profile IDs, revisions, and digests; only their list order differed
from the freezer's independently sorted expected list.

No copedent value, model weight, threshold, validation result, source record,
or sealed-test state changed.

## Files changed

- `pocketsteel/amazing_tablature_training.py`
- This handoff

## Tests and checks

- Ruff — PASS.
- `tests/test_amazing_tablature_training.py` — PASS, 48 tests.
- `git diff --check` — PASS.

## Integration notes

Because the freezer is part of the pinned rules-code digest, rebuild the exact
discovery-only challenger after this commit, verify byte-identical weights and
zero rereview selections, carry the exact corrected validation verdicts, and
then rerun the freeze.

## Risk assessment

Low. The change is deterministic normalization before an otherwise unchanged
exact comparison. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1830-20-copedent-freeze-order-fix.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty and untracked handoffs

## Recommended next lane

Lane 01 exact-path commit, then Lane 20 final rebuild and freeze.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the two exact files above and continue the active private
validation/freeze workflow without another human review.
