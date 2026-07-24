# Lane 20 — Discovery Reader Lineage and Validation Preflight

## Task summary

Continued the approved Amazing Tablature engineering phase without opening
sealed-test data or using validation answers for training.

Completed:

- Repaired discovery contact-sheet supervision so immutable machine source
  columns are mapped to reviewed events by stable event lineage rather than by
  a later renumbered event index.
- Added explicit abstention for ambiguous source columns created by an
  unlinked reviewed insertion.
- Added a precision-first discovery glyph decoder with content-unit-grouped
  cross-validation and exact artifact lineage.
- Added a discovery-only semantic reader calibration with per-state precision,
  support, and content-unit gates.
- Corrected calibration automation accounting so rejected diagnostic states do
  not dilute or qualify accepted rules.
- Required exact source-record-set, mapping-contract, approved-record-set,
  reader-contract, and artifact-digest lineage before validation can load a
  discovery-derived decoder.
- Made cached exact reader failures terminal abstentions rather than repeated
  inference or implicit blank cells.
- Removed a duplicate wrapper retry that could expand one reader's two-attempt
  contract into four identical calls.
- Made tab-reader response-label matching case-insensitive and fail-closed on
  duplicate normalized keys. The behavior is pinned by
  `tab-cell-response-label-normalization-v3`.
- Changed unresolved validation-card replay to bounded, enlarged groups of at
  most eight cards and two concurrent pinned readers.
- Moved exact validation reader caches to a schema-independent cache location
  while retaining digest-verified reuse of prior versioned caches.
- Added focused regression coverage and updated the Lane 20 workflow document.

Intentionally not completed in this checkpoint:

- No validation score was recorded.
- No challenger was rebuilt or promoted.
- No learned ranker was enabled.
- No public or protected-preview behavior changed.
- No sealed-test data was accessed.

## Private lineage observations

Provisional discovery-only builds established the corrected source-column
mapping before the final clean-HEAD rebuild:

- Main cohort: 728 stable event-ID columns, 28 reviewed blank columns, and 20
  ambiguous columns excluded.
- Licks cohort: 399 stable event-ID columns, 2 reviewed blank columns, and 23
  ambiguous columns excluded.
- The provisional main reader calibration had 119/119 accepted-rule grouped
  predictions and zero accepted-rule false positives.

Those provisional artifacts are not canonical because the response
normalization and focused-reader contract changed afterward. They must be
rebuilt from the commit produced by this checkpoint before validation replay.

Validation comparison attempts during development were stopped before an
official report whenever the reader contract changed. They did not create
training evidence, consume validation review truth, or access sealed test.

## Files changed

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_glyph_decoder.py`
- `steel_guitar_rag/amazing_tablature_reader_calibration.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_reader_calibration.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-0842-20-discovery-reader-lineage-and-validation-preflight.md`

Generated private artifacts and caches remain beneath ignored
`corpus-private/melody-decisions/`. No source image or private artifact was
modified, staged, or copied into the repository.

## Tests and checks

Passed:

- `.venv/bin/pytest -q`
  - `1427 passed in 74.28s`
- `.venv/bin/pytest -q tests/test_amazing_tablature_reader_calibration.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - `221 passed`
- Focused contact-reader, retry, case-normalization, and consensus tests
  - `9 passed` before the final duplicate-key regression
  - `3 passed` for the final local-reader/focused-chunk subset
- `.venv/bin/ruff check` on all changed Python modules and tests
- `python -m py_compile` on all changed Python modules and the CLI
- `git diff --check` on the exact scoped file list

## Integration notes

- The final discovery reader calibrations, glyph decoders, validation
  consensus reports, and challenger must be regenerated only after these files
  are committed so their `codeRevision` and code-file digests identify one
  clean HEAD.
- Validation remains evaluation-only. Its imagery may be processed by the
  pinned machine preflight, but validation answers may not enter calibration,
  training, prompts, exception queues, or learned weights.
- Complete validation lines may proceed to fixed-gate scoring. Incomplete
  lines remain withheld; a missing cell is never converted into a blank or an
  invented event.
- Sealed test remains closed until the exact engine, schema, copedent, reader,
  validator, and challenger revisions are frozen.

## Risk assessment

**Medium.** The code is fully test-green and fail-closed, but the new bounded
focused-card reader path has not yet completed a clean-HEAD real-cohort replay.
The likely failure mode is continued abstention, not silently accepted wrong
tablature. Rollback is the single scoped commit for this checkpoint; private
generated artifacts are ignored and can be superseded by a new exact-lineage
build without changing raw sources.

## Human decision needed

No. This is an already approved engineering phase. Learned activation remains
prohibited unless the fixed independent validation gates pass.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_glyph_decoder.py`
- `steel_guitar_rag/amazing_tablature_reader_calibration.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_reader_calibration.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-0842-20-discovery-reader-lineage-and-validation-preflight.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs
- `corpus-private/**`
- Raw source images, reader caches, model artifacts, evaluation outputs, and
  review records

## Recommended next lane

Lane 20, continuing from the committed clean HEAD:

1. Rebuild both cohorts' glyph decoders and semantic reader calibrations.
2. Replay main and licks validation with answers unavailable and sealed closed.
3. Record complete/withheld counts and fixed-gate metrics.
4. Rebuild and shadow-test the exact challenger only if validation comparison
   inputs are structurally complete enough to support a meaningful score.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 20: From the exact clean HEAD, rebuild both discovery reader artifacts,
replay main and licks independent validation with sealed closed, and continue
to exact challenger evaluation only if the fixed structural gates pass.`
