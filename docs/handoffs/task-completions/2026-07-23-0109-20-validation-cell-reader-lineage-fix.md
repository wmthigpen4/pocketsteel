# Lane 20 — Validation cell-reader lineage fix

## Task summary

The clean validation replay exposed a lineage mismatch before any incomplete
line could reach review. Validation extraction had correctly pinned Apple Vision
as the per-cell tablature reader, while machine remediation incorrectly required
those caches to identify the separate Gemma full-line reader.

This slice:

- verifies per-cell cache lineage against the exact `tabReader` pinned in the
  validation extraction summary;
- records that reader in the remediation contract;
- continues to verify prompt version, sheet hash, labels, and cell structure;
- bumps the private machine-recapture contract from v5 to v6.

No source facts were changed. No validation answer, human ground truth, or sealed
data was used. No audit was published and no model was promoted or enabled.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- this handoff

## Tests and checks

- Focused lineage and score-consensus tests: **2 passed**.
- Full Lane 20 focused suite: **208 passed**.
- `git diff --check`: **passed**.
- Validation truth accessed: **no**.
- Sealed-test data accessed: **no**.

## Integration notes

The pre-fix v5 licks remediation withheld all six lines solely on the false
reader-lineage mismatch. After this slice is committed, the discovery challenger
must be rebuilt at the new clean HEAD, both validation extractions repinned to
that exact challenger, and v6 machine remediation rerun.

Apple Vision cell tokens remain independent from the Gemma full-line reader.
Mechanical checks, exact source-copedent validation, score-pitch containment,
source-only score consensus, and unique row-origin selection remain unchanged.

## Risk assessment

Low.

The change narrows lineage verification to the actual reader that produced the
cache instead of conflating two independent readers. Hash and schema checks are
unchanged.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0109-20-validation-cell-reader-lineage-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- unrelated untracked historical handoffs
- all of `corpus-private/`
- source images, validation reports, review receipts, models, and sealed-test
  artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit

## Suggested next step

Exact-path commit this slice, rebuild the canonical discovery challenger, repin
both validation runs, and rerun unpublished v6 remediation/readiness.
