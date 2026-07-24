# Lane 20 — Canonical lineage hardening

## Task summary

Fixed the first real canonical-packet smoke blocker and strengthened canonical
scoring before any human review was requested.

Changes:

- Allowed a canonical source crop to resolve within the cohort's private
  validation review root rather than requiring it to be inside the narrower
  child-packet directory.
- Continued to reject paths outside the private cohort review root.
- Required the canonical score report to pin the current committed evaluation
  revision and every evaluation code-file digest.
- Revalidated the exact private decision ledger during canonical scoring.
- Required packet and submission decision digests to match that ledger.
- Required packet decision IDs to cover the ledger exactly once.
- Added focused corruption assertions for stale evaluation lineage and altered
  ledger coverage.

No private review packet was accepted, no validation entered training, and no
sealed test was opened.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

## Tests and checks

- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py`
  - PASS: 228 passed.
- `git diff --check`
  - PASS.

## Integration notes

The score report must be regenerated after this commit because canonical
scoring now requires its evaluation revision and code digests to equal the
committed implementation exactly. Regenerate the no-rereview certificate from
that exact report before producing the human packet.

## Risk assessment

Risk: low.

The path change broadens access only from one child directory to its parent
private validation-review root and retains a resolved-path containment check.
The scoring changes only tighten lineage.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1558-20-canonical-lineage-hardening.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- `corpus-private/**`

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit

## Suggested next step

Commit this hardening, regenerate the exact score and no-rereview lineage, and
retry the combined canonical packet.
