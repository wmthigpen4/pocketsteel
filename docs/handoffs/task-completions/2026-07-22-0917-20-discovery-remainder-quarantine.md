# Lane 20 Discovery Remainder Quarantine

## Task summary

Implemented the explicitly approved discovery-only automatic-quarantine step for the current Amazing Tablature program. The new command disposes the exact audited discovery remainder as excluded from transformation training without approving any score, tablature, pitch, rhythm, or alignment fact. Raw assets, machine hypotheses, comments, corrections, and teaching evidence remain unchanged in the ignored private batch. Validation and sealed-test data are not opened by this operation.

Intentionally not changed: runtime product behavior, model promotion, extraction facts, raw source files, embeddings, retrieval indexes, validation data, sealed-test data, auth, deployment, and the unrelated dirty integration-status/historical handoff files.

## Files changed

- `docs/amazing-tablature-training.md`: documents the explicit bulk-quarantine contract and command.
- `steel_guitar_rag/amazing_tablature_extraction.py`: adds digest-pinned discovery-remainder quarantine through the official append-only review ledger and tolerates legacy feedback rows without a submission ID.
- `scripts/amazing_tablature.py`: adds the guarded `quarantine-discovery-remainder` command.
- `tests/test_amazing_tablature_extraction.py`: covers required confirmation, complete exclusion disposition, no factual approval, source preservation, and held-out closure.
- `docs/handoffs/task-completions/2026-07-22-0917-20-discovery-remainder-quarantine.md`: this handoff.

No files were deleted. Private artifacts produced when the command is later run remain beneath ignored `corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py` — 159 passed.
- `.venv/bin/python scripts/amazing_tablature.py quarantine-discovery-remainder --help` — passed.
- `git diff --check` — passed before this handoff.
- `.venv/bin/python -m pytest -q` — 1,338 passed in 57.55 seconds.

## Integration notes

The operation requires both `--approval-reference` and `--confirm-bulk-quarantine`. It reruns the discovery completion audit, verifies exact queue coverage and current machine-record digests, and records `exclude` actions through `apply_review`. Exclusion counts as complete disposition for canonical discovery readiness but never as factual approval or training evidence.

The approved invocation should use the user's 2026-07-22 authorization to automate/quarantine uncertain discovery pages. Run it for both authoritative batches only after this slice is test-green and committed. Then rebuild canonical readiness and the complete-discovery challenger. Do not open sealed-test data.

## Risk assessment

Medium. The source and existing reviewed facts are not modified, but the operation creates append-only final exclusions for every currently unresolved discovery page. Rollback is not destructive: a future program revision can create a new reviewed snapshot from preserved private evidence, but this snapshot must continue to report the exclusions honestly.

## Human decision needed

No. The user already authorized the automatic discovery quarantine and the next five implementation steps.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-0917-20-discovery-remainder-quarantine.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs
- `corpus-private/`
- Any source images, extraction artifacts, reviews, model artifacts, validation artifacts, or sealed-test artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit.

## Suggested next step

Run the full test suite, exact-path commit this slice, apply the authorized discovery quarantine to both batches, verify canonical no-rereview/preference lineage, and rebuild the complete-discovery challenger before opening validation.
