# Lane 20 — Audited model-channel deactivation

## Task summary

Added a durable `deactivate-channel` operation so an obsolete beta or stable
model can be removed from the private active-channel registry without selecting
an unapproved replacement or editing registry JSON by hand. The operation
requires an explicit creator approval reference, appends rollback history,
refreshes model states, and is idempotent when the channel is already empty.

## Files changed

- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py` — PASS, 36 tests.
- CLI help for `deactivate-channel` — PASS.
- `git diff --check` for the scoped files — PASS.

## Integration notes

Use the operation to clear the beta channel containing the superseded 51-image
model. Do not activate the current challenger through this command; exact
promotion still requires passing evaluation and explicit exact-model approval.
Changing this rules-code file requires one final discovery-only challenger
rebuild before validation freeze.

## Risk assessment

Low. The action is append-only and audited. Rollback to an eligible prior model
still uses the existing explicit rollback operation; the superseded model
should not be restored.

## Human decision needed

No. The user explicitly superseded the 51-image batch and approved the bounded
fallback/integration plan.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-22-1720-20-channel-deactivation.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- Unrelated historical handoffs and generated artifacts.

## Recommended next lane

Lane 01 exact-path commit, Lane 20 deactivate the obsolete beta, then reproduce
the selected discovery challenger against that final clean HEAD.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files, deactivate beta with the current user approval
reference, rebuild the selected challenger, and verify the sealed test remains
closed.
