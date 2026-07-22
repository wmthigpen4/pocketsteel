# Lane 20 — Non-revoking rights-extension lineage

## Task summary

The approved bounded training/frontend run extended both authoritative batches
from private training use to sanitized runtime-product use. That append-only
authorization revision caused previously reviewed discovery records to fail the
exact-current-digest check even though musical evidence and model-training
permission were unchanged.

The lineage gate now accepts a reviewed record pinned to an earlier rights
record only when that exact record exists in the private append-only history,
both the historical and current records are approved and non-unknown, and both
explicitly allow the consuming use. A current revocation, missing historical
record, unknown status, or mismatched batch still fails closed. No musical
review is repeated or rewritten.

## Files changed

- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

Private rights records for the two authoritative batches were revised beneath
ignored `corpus-private/` to allow private extraction/evaluation, model
training, and sanitized runtime product use. Embeddings, quotation, public
display, and derivative-rule publication remain disabled.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py` — PASS, 36 tests.
- `git diff --check -- pocketsteel/amazing_tablature_training.py tests/test_amazing_tablature_training.py` — PASS.

## Integration notes

This is a lineage-policy correction, not model promotion. The canonical
discovery challenger must be rebuilt after this exact commit so its rights and
code digests are current. Validation and sealed-test data were not opened.

## Risk assessment

Low. The rule is fail-closed on current revocation and requires the pinned
record to exist in immutable authorization history. Rollback is the exact
commit revert, but doing so would require unnecessary musical rereview after a
non-revoking authorization extension.

## Human decision needed

No. The user explicitly approved sanitized frontend integration for both
authorized batches.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-22-1711-20-rights-extension-lineage.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs and private/generated artifacts.

## Recommended next lane

Lane 01 exact-path commit, then Lane 20 discovery-only challenger tournament.

## Commit readiness

Safe to commit

## Suggested next step

Commit the three exact files, rebuild no more than two discovery-only canonical
challengers, shadow-score them, and keep validation and sealed-test data closed.
