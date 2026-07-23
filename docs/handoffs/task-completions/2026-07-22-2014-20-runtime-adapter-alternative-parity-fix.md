# Runtime adapter alternative parity fix

## Task summary

Fixed the first clean challenger rebuild failure after the shared ranker adapter commit. One single-note alternative path still called the removed private `_sequence_features` helper. It now uses the shared canonical adapter and preserves the frozen alternative sustain/repick semantics used by the selected challenger.

No validation or sealed-test data was opened. The failed rebuild created no model artifact.

## Files changed

- `pocketsteel/amazing_tablature_decisions.py`
- `docs/handoffs/task-completions/2026-07-22-2014-20-runtime-adapter-alternative-parity-fix.md`

## Tests and checks

- Training and arranger-decision suites: `46 passed`.
- `git diff --check`: PASS before this handoff; rerun after handoff creation.

## Integration notes

The fix retains explicit-attack mechanical review projections while preserving the historical feature values for a same-string/same-pitch alternative (`sustainedVoices=1`, `repickedVoices=0`). This is required for weight-level reproducibility.

## Risk assessment

Low. The active runtime ranker remains disabled.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_decisions.py`
- `docs/handoffs/task-completions/2026-07-22-2014-20-runtime-adapter-alternative-parity-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked handoffs
- `corpus-private/**`

## Recommended next lane

Lane 20: rerun the exact-configuration clean challenger rebuild and compare every learned weight with the selected predecessor.

## Commit readiness

Safe to commit.

## Suggested next step

Commit this exact fix, then rerun the frozen `32/0.03/averaged/0.35` challenger configuration.
