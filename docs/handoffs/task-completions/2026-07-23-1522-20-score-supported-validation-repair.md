# Lane 20 — Score-supported validation repair

## Task summary

Continued the approved Amazing Tablature engineering goal without opening
validation ground truth or either sealed-test partition.

Completed:

- Ran a complete machine-only remediation sweep over 56 blocked main
  validation lines across 25 pages.
- Confirmed that the dominant blocker is independent tab-count disagreement:
  41/56 lines. The remaining lines failed score count, score geometry, or
  bounded localization checks.
- Ran the same canary on the one withheld licks line; it remained withheld
  because independent tab-count readers disagreed.
- Added score-support enrichment for tab-complete validation lines.
- Required exact, digest-pinned validation contact candidates and current
  model/run lineage before enrichment.
- Added a deterministic source-only score consensus requiring agreement among
  complete MusicXML, notehead-column geometry, raw notehead multiplicity, and
  the frozen projection/component hybrid.
- Corrected validation preflight so a written score change may correspond to
  either a repicked tab attack or an explicitly represented sounding-state
  change during sustain.
- Retained two-reader score-only consensus as a fail-closed fallback.
- Added explicit score-supported line accounting.
- Dry-ran the exact contract against the five tab-complete licks lines. Two
  lines passed every source-count, source-pitch, tab-containment, mechanical,
  provenance, and structural gate; four other systems on the same pages
  remained withheld.

Intentionally not changed:

- No validation result was applied yet.
- No validation evidence entered training.
- No human validation answer was opened or inferred.
- No sealed-test path was opened.
- No challenger was promoted, enabled, or wired into runtime.
- No source image, corpus, embedding, vector index, auth, deployment, or
  application UI file was changed.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- This handoff.

Private ignored dry-run reports remain beneath
`corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py`
  - PASS.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py`
  - PASS: 182 passed.
- `.venv/bin/pytest -q`
  - PASS: 1,438 passed in 70.93 seconds.
- `git diff --check`
  - PASS.
- Main validation dry sweep:
  - 56 lines, 25 pages, 0 automatic passes, 56 withheld, 0 applied.
  - 41 tab-count consensus disagreements.
  - human truth used: false.
  - validation may train: false.
  - sealed test accessed: false.
- Licks score-support dry canary:
  - 6 selected systems on three pages.
  - 2 score-supported passes and 4 withheld systems.
  - 0 applied.
  - report digest:
    `69e6eb36f36589a36ea0e64d83cbcc7e9a4c17739c3cd8e050c35b0fb342f904`.
  - human truth used: false.
  - validation may train: false.
  - sealed test accessed: false.

## Integration notes

The two eligible lines are not accepted as validation truth merely because
they passed machine preflight. They are safe to apply as machine-capture
revisions because every score fact is independently source-derived, every tab
fact comes from the separately pinned contact consensus, and post-hoc
score/tab containment is exact under the existing notation-transposition
contract.

The validation scorer must next classify decisions from these lines as
`alignment:score_supported` while preserving `trainingEligible: false`. It
must continue reporting tab-only and score-supported metrics separately.

The main validation recognition problem remains unresolved. No incomplete
line should be published for human review.

## Risk assessment

Risk: medium.

The new path is intentionally narrow and fail closed. Its main risk is
overstating machine preflight as human validation; downstream reports must
keep those evidence classes separate. Rollback is the scoped implementation
commit. Private page revisions can be regenerated from immutable source and
archived prior records.

## Human decision needed

No.

Continue the approved automatic validation loop. Human review remains reserved
for complete, genuinely ambiguous cases.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-1522-20-score-supported-validation-repair.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs
- `corpus-private/**`
- Raw images, extraction records, review artifacts, model files, reports,
  embeddings, indexes, or sealed-test artifacts

## Recommended next lane

Lane 01 exact-path commit, followed immediately by Lane 20 applying only the
two digest-pinned score-supported passes, rebuilding contact consensus, and
extending the exact machine scorer to report score-supported decisions.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact three-file slice, apply only the two passing licks revisions,
rebuild both consensus reports, and rescore exact challenger
`at-90360274fad075f6` without opening validation truth or sealed test.
