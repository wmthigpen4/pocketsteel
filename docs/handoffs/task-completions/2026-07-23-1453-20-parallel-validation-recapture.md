# Lane 20 Parallel Validation Recapture

## Task summary

The validation machine-recapture path was functionally bounded but serialized
two independent reads through one model tag. Its first line could therefore
consume the combined transport timeout before producing a resumable checkpoint.

This slice:

- Requires the current digest-verified multi-model validation contact-consensus
  report before recapture may run.
- Reuses the exact two pinned reader model tags from that report.
- Runs independent reader calls concurrently while preserving reader order in
  the returned evidence.
- Applies the same concurrency to tab counts, tab localization, score-only
  column counts, and score-only pitch reads.
- Adds the source consensus report digest and reader contracts to the recapture
  contract.
- Leaves every confidence, exact-agreement, score-containment, mechanical,
  structural, no-training, and sealed-test gate unchanged.

The optimized five-line main-cohort canary completed in approximately 2.5
minutes. All five lines were withheld safely and no page record changed:

- Two independent tab-count disagreements.
- Two bounded event-count localization failures.
- One unordered score-position failure.

A full dry pass is running to measure the complete failure distribution before
any `--apply` pass.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1453-20-parallel-validation-recapture.md`

No source image, validation page record, accepted decision ledger, model
artifact, runtime file, or sealed-test artifact was changed.

## Tests and checks

- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py`
  - PASS.
- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py -k 'parallel_validation_reader_calls or validation_score_only_consensus_is_independent or validation_machine_count_consensus'`
  - PASS: 3 passed, 177 deselected.
- `.venv/bin/pytest -q`
  - PASS: 1,436 passed in 76.56 seconds.
- `git diff --check`
  - Required before exact-path commit.

## Integration notes

- Validation recapture now requires the current
  `validation-contact-sheet-consensus-v3/report.json`.
- The report must match batch, validation run digest, exact challenger,
  report digest, no-training contract, and sealed-test-closed state.
- At least two distinct pinned reader model tags are required.
- The first two pinned reader models are used for independent score and tab
  recapture with distinct deterministic seeds.
- Reader-result order remains deterministic even though calls execute
  concurrently.
- Existing candidate caches are contract-digest scoped, so serial-contract
  caches cannot be misread as results from this multi-model contract.

## Risk assessment

Risk: medium.

The change improves throughput and reader independence but may increase
abstention when distinct models disagree. That is intentional: disagreements
remain withheld. The full dry report must be inspected before any apply pass.

Rollback is the scoped implementation commit; private dry-run artifacts remain
ignored and non-training.

## Human decision needed

No.

Continue the full dry pass. Apply only exact machine-preflight passes, if any.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1453-20-parallel-validation-recapture.md`

## Files that must not be staged

- `corpus-private/`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1439-20-goal-progress-and-capture-pivot.md`
- All unrelated modified and untracked worktree files.

## Recommended next lane

Lane 20 Amazing Tablature Training.

Inspect the complete dry reports, apply only fully eligible revisions, rerun
contact consensus, then score the exact challenger. Do not open sealed test.

## Commit readiness

Safe to commit.

The implementation and focused/full tests are green. Exact-path staging is
required.

## Suggested next step

Lane 01: exact-path commit the four files in this handoff while leaving all
private and unrelated artifacts untracked. Lane 20 then continues the running
full dry validation repair.
