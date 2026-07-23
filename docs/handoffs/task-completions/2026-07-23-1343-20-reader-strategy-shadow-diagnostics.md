# Lane 20 Reader Strategy Shadow Diagnostics

## Task summary

Continued the automatic discovery-to-validation feedback loop without opening
validation answers or sealed-test data.

Completed:

- committed exact discovery reader-pair calibration as `e1b60d3`;
- rebuilt both private reader calibrations from that exact commit;
- confirmed the pair rules improved the main machine shadow from 616 to 633
  reconstructed events and from 673 to 655 unresolved cells while preserving
  the licks result at 85/85 events and one unresolved cell;
- audited the complementary committed glyph revision `826abf4`;
- confirmed the glyph revision improved the main shadow to 3/57 complete
  lines, 640/896 reconstructed events, and 646 unresolved cells while
  preserving the licks result at 85/85 events and one unresolved cell;
- benchmarked 8-, 4-, 2-, and 1-card local-reader prompts against 24 reviewed
  discovery labels from three content units;
- benchmarked Apple Vision tab OCR against 162 reviewed discovery labels from
  eight content units;
- shadow-tested a narrow same-fret grip-anchor fallback, then removed it after
  it produced no additional complete lines or reconstructed events.

Rejected:

- smaller card groups: raw reader accuracy fell monotonically from 91.7% at
  eight cards to 87.5%, 79.2%, and 64.6%;
- Apple Vision as a third reader: 2/162 parseable labels, despite 2/2
  correctness;
- the same-fret fallback: only three final labels recovered, with no new event
  or complete-line coverage.

No review packet was created and learned runtime behavior remains disabled.

## Files changed

This diagnostic continuation intentionally leaves no implementation diff.

Earlier scoped commits in the same logical run:

- `e1b60d3` — exact reader-pair calibration;
- `826abf4` — discovery glyph-neighbor calibration.

Private ignored diagnostics:

- `reader-chunk-benchmark-v1/report.json`
- `apple-tab-reader-benchmark-v1.json`
- machine-only validation consensus reports for both authoritative cohorts

No source image, approved record, validation answer, sealed-test record,
embedding, vector store, runtime flag, auth setting, or deployment file was
modified.

## Tests and checks

- Reader-pair commit:
  - focused tests: 18 passed;
  - full suite: 1,431 passed;
  - Ruff and Python compilation passed.
- Glyph-neighbor commit:
  - glyph tests: 2 passed;
  - full suite: 1,431 passed;
  - Ruff and Python compilation passed.
- Rejected structural diagnostic:
  - focused contact-consensus tests: 11 passed before the diagnostic code was
    removed.
- `git diff --name-only -- pocketsteel/amazing_tablature_extraction.py
  tests/test_amazing_tablature_extraction.py`
  - Empty after removal of the rejected fallback.

## Integration notes

Current clean committed HEAD is `826abf4`. The exact eligible private artifacts
used by the latest machine-only shadow are:

- main glyph decoder `atg-0b82ebb8b0bffc68`;
- licks glyph decoder `atg-c9e8b543d5b3953f`;
- main reader calibration `atr-cf87c02cae96d231`;
- licks reader calibration `atr-7fb88d22ad4e4b17`.

Latest machine-only shadow:

- main: 57 lines, 3 complete, 54 withheld, 640/896 reconstructed events, 646
  unresolved cells;
- licks: 6 lines, 5 complete, 1 withheld, 85/85 reconstructed events, one
  unresolved cell.

The current bottleneck is no longer improved by card-size changes, Apple OCR,
or same-fret inference. A separate concurrent scoped diff is implementing an
evaluation-only scorer for complete machine candidates. That work is parked in
`pocketsteel/amazing_tablature_training.py`, `scripts/amazing_tablature.py`,
and `tests/test_amazing_tablature_training.py`; this task did not alter or
stage it.

## Risk assessment

**Medium.** The licks machine capture is nearly complete, but only 3/57 main
lines satisfy the complete-candidate contract. Machine-candidate scoring can
provide a legitimate tab-only signal, but it cannot satisfy the separately
declared score-supported validation gate and must not be represented as full
score-to-tab validation.

## Human decision needed

No. Continue automatic implementation and QA. Do not request human review
until an ambiguity remains after the complete-candidate scorer and the input
path is presented in a compact, score-and-tab-aligned form.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-23-1343-20-reader-strategy-shadow-diagnostics.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- other pre-existing untracked handoffs
- `corpus-private/**`
- raw sources, validation answers, sealed-test artifacts, embeddings, vector
  stores, credentials, logs, auth files, and deployment files

## Recommended next lane

Lane 20 Amazing Tablature Training, then Lane 15 QA if the complete-candidate
scorer is fully green.

## Commit readiness

Safe to commit as docs-only after `git diff --check`; do not include the
concurrent scorer diff.

## Suggested next step

Finish and test the complete-machine-candidate scorer, commit it separately
with exact paths, run it against the exact canonical challenger, and report
tab-only metrics separately from the still-withheld score-supported gate.
