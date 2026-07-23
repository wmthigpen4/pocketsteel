# Lane 20 Glyph Neighbor Calibration

## Task summary

Revised the discovery-only tablature glyph decoder from a nine-neighbor,
fifth-power cosine vote to a fixed five-neighbor, squared-similarity vote.

The bounded configuration was selected from grouped discovery replay only. At
the unchanged 99.5% minimum precision gate, the projected accepted predictions
were:

- Main cohort: 83/83, up from 30/30.
- Licks cohort: 111/111, up from 72/72.

The decoder schema is now `amazing-tablature-glyph-decoder-v3`, and the exact
classifier kind, neighbor count, and similarity power are pinned in every
artifact. Validation labels and sealed-test data were not used for selection.

## Files changed

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_glyph_decoder.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1324-20-glyph-neighbor-calibration.md`

No raw images, approved records, validation answers, sealed-test records,
embeddings, vector stores, runtime flags, or deployment files were changed.

## Tests and checks

- `./.venv/bin/python -m py_compile pocketsteel/amazing_tablature_glyph_decoder.py`
  - Passed.
- `./.venv/bin/ruff check pocketsteel/amazing_tablature_glyph_decoder.py tests/test_amazing_tablature_training.py`
  - Passed.
- `./.venv/bin/pytest -q tests/test_amazing_tablature_training.py -k 'glyph'`
  - Passed: 2 tests.
- `./.venv/bin/pytest -q`
  - Passed: 1,431 tests.

## Integration notes

Existing v2 private glyph artifacts are intentionally ineligible after this
schema change. Rebuild the main and licks discovery glyph decoders only after
the exact implementation commit exists. Then rebuild the reader calibrations
to pin the new code lineage and rerun the machine-only validation shadow with
validation answers closed.

The preceding `e1b60d3` shadow baseline was:

- Main: 57 lines, 2 complete, 55 withheld, 633/895 reconstructed events,
  655 unresolved cells, 110 pair-calibrated cells.
- Licks: 6 lines, 5 complete, 1 withheld, 85/85 reconstructed events,
  1 unresolved cell, 7 pair-calibrated cells.

## Risk assessment

**Medium.** The classifier revision materially increases discovery-qualified
coverage, but any validation benefit must be measured rather than assumed.
The 99.5% grouped precision, label-support, content-unit grouping, mechanical
validation, and abstention gates remain unchanged.

Rollback is the scoped implementation commit. Private generated artifacts are
ignored and can be rebuilt from the preceding code revision.

## Human decision needed

No. Continue the approved automatic discovery-to-validation shadow loop.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1324-20-glyph-neighbor-calibration.md`
- `pocketsteel/amazing_tablature_glyph_decoder.py`
- `tests/test_amazing_tablature_training.py`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Other pre-existing untracked handoffs
- `corpus-private/**`
- Raw source images, validation artifacts, sealed-test artifacts, embeddings,
  vector stores, credentials, logs, and deployment files

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above, rebuild both private discovery glyph decoders and
reader calibrations from that HEAD, and rerun the machine-only validation
shadow without opening validation answers or sealed-test data.
