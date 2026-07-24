# Lane 20 — Focused Reader Input Calibration

## Task summary

Continued the approved Amazing Tablature engineering phase from clean commit
`2f48d8cdddbbf27f4f955586d753fa42a87e9abb`.

Completed:

- Added a distinct calibration contract for the bounded, enlarged eight-card
  reader input used during validation.
- Changed semantic reader rules and grouped cross-validation keys from
  reader/state to reader/input-mode/state.
- Prevented a state calibrated on a full contact sheet from qualifying a
  singleton read from a focused card group, and vice versa.
- Made discovery calibration render the same focused card groups used by
  validation and evaluate them only against approved discovery truth.
- Preserved digest-verified reuse of legacy full-sheet reader caches while
  requiring new, input-mode-qualified caches for focused images.
- Added separate focused chunk and label accounting to private calibration
  artifacts.
- Added regression coverage proving that accuracy in one visual input mode
  cannot leak into the other.

Intentionally not completed in this checkpoint:

- No validation answer or validation ground truth was opened or used.
- No official validation score was recorded.
- No challenger was rebuilt or promoted.
- No learned ranker was enabled in runtime.
- No sealed-test data was accessed.

## Why this was necessary

The first clean-HEAD main validation replay processed 12 of 57 systems before
being stopped. All 12 were withheld. Among 141 unresolved cells, 94 had one
parseable focused-reader answer, 40 had two conflicting answers, and 7 had no
parseable answer. The singleton answers could not qualify because the accepted
discovery calibration represented only full-sheet inputs. This change repairs
that lineage mismatch without weakening consensus or using held-out answers.

## Files changed

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_reader_calibration.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_reader_calibration.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-0957-20-focused-reader-input-calibration.md`

Private focused images, model outputs, caches, and calibration artifacts remain
beneath ignored `corpus-private/melody-decisions/`. They were not staged or
copied into the repository.

## Tests and checks

Passed:

- `.venv/bin/pytest -q tests/test_amazing_tablature_reader_calibration.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - `223 passed in 5.41s`
- `.venv/bin/pytest -q`
  - `1428 passed in 68.93s`
- `.venv/bin/ruff check` on the changed documentation, Python modules, and
  tests
- `.venv/bin/python -m py_compile` on both changed Python modules
- `git diff --check`

## Integration notes

- Rebuild both discovery reader calibrations from the commit containing this
  checkpoint before resuming validation.
- Full-sheet reads may reuse their exact prior caches. Focused discovery reads
  must be newly produced for the same pinned reader artifacts and may take
  substantial local inference time.
- Validation must select only schema-v3 calibration artifacts whose reader
  contracts and source lineage exactly match.
- A focused singleton is usable only when that reader/input-mode/state rule
  independently passes the existing support, content-unit, and at least 99.5%
  leave-one-content-unit-out precision gates.
- Two-reader semantic agreement remains stronger evidence. Conflicts and
  unqualified singletons continue to abstain.
- Validation remains evaluation-only, and sealed test remains closed.

## Risk assessment

**Medium.** The implementation is fully test-green and fail-closed. Real-cohort
focused calibration still depends on local model readability and may improve
coverage only partially. The safe failure mode is continued abstention, not an
invented or silently accepted tab state.

Rollback is the single scoped commit for this checkpoint. Generated private
artifacts are immutable or replaceable by new exact-lineage builds, and raw
source assets are unchanged.

## Human decision needed

No. This is part of the already approved engineering goal. Exact learned-model
activation remains prohibited until the fixed independent validation gates
pass.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_reader_calibration.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_reader_calibration.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-0957-20-focused-reader-input-calibration.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs
- `corpus-private/**`
- Raw source images, model output, reader caches, calibration artifacts,
  validation artifacts, and sealed-test material

## Recommended next lane

Lane 20:

1. Commit this exact test-green checkpoint.
2. Rebuild both discovery glyph decoders and schema-v3 reader calibrations.
3. Resume main and licks validation comparison with validation answers
   unavailable and sealed test closed.
4. Continue to exact challenger evaluation only if the fixed structural gates
   produce a meaningful complete comparison.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 20: From this exact clean commit, rebuild both discovery visual-reader
artifacts, resume both independent validation comparisons with sealed test
closed, and continue automatically to exact challenger evaluation only if the
fixed gates pass.`
