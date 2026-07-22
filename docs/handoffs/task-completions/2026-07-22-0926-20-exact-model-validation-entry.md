# Lane 20 Exact-Model Validation Entry

## Task summary

Replaced the obsolete per-batch `train` checkpoint gate for validation extraction with an exact canonical-model gate suitable for the combined two-batch dataset. Validation now requires an explicitly named complete-discovery challenger, verifies its registry eligibility and artifact SHA-256, verifies cohort coverage and full discovery disposition, and pins model/seed/code lineage into the validation extraction run.

The change does not open validation or sealed-test data by itself. The first attempted validation extraction was correctly rejected by the obsolete gate before any validation page was read; no partial validation output was created by that attempt.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-0926-20-exact-model-validation-entry.md`

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py` — 124 passed.
- `.venv/bin/python -m pytest -q` — 1,338 passed in 57.61 seconds.

## Integration notes

Use `extract <batch> --partition validation --validation-model-id at-1fa9630a173af769`. The model is the canonical validation candidate built from clean HEAD `3df45029ac0a2dbbc15e59dfa62a21e2a50211d0`, with exact 16/6/10 preference accounting, four inherited style families, 702 examples, complete discovery disposition, and score-audit scope reported separately. Validation review methods inherit the exact pin from `extraction/validation/summary.json`.

The sealed test remains inaccessible through the extraction command.

## Risk assessment

Low-medium. This changes a held-out access gate, but makes it stricter and auditable: the caller must name an exact combined-dataset canonical artifact, and digest/cohort checks fail closed.

## Human decision needed

No. Opening validation after the canonical rebuild is within the approved five-step scope.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-0926-20-exact-model-validation-entry.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Unrelated historical handoffs
- `corpus-private/` and all validation/model/source artifacts

## Recommended next lane

Lane 20 for validation extraction and private review preparation; Lane 15 owns independent validation approval and metrics.

## Commit readiness

Safe to commit.

## Suggested next step

Run the full suite, exact-path commit, extract the 3-page licks and 28-page main validation cohorts pinned to `at-1fa9630a173af769`, then prepare the smallest validation review/evaluation handoff. Keep all 63 sealed-test pages closed.
