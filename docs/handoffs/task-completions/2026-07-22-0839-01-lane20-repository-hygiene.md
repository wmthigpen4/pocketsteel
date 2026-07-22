# Lane 01 — Lane 20 Repository Hygiene

Date: 2026-07-22 08:39 America/Chicago

## Task summary

The request was to perform the repository hygiene needed after the accumulated Amazing Tablature work. The coherent Lane 20 implementation was separated into three dependency-ordered exact-path commits. Private source material, generated training artifacts, historical page-level review handoffs, unrelated deployment/UI handoffs, and the stale coordination-status edit were intentionally excluded.

No validation or sealed-test imagery, annotations, ground truth, or results were opened.

## Commits created

1. `8551711 feat(training): add phrase-aware steel decision features`
2. `6b09fcc feat(training): add private score-tab extraction workflow`
3. `5a6a150 feat(training): harden challenger and sealed evaluation lineage`

## Files changed

The commits contain only the reviewed Lane 20 implementation and its reproducibility support:

- Decision/ranker source and transfer test: `pocketsteel/amazing_tablature_decisions.py`, `pocketsteel/melody_ranker.py`, `tests/test_copedent_transfer.py`.
- Extraction/review source and tests: `pocketsteel/amazing_tablature_extraction.py`, `pocketsteel/e9_copedents.py`, `scripts/apple_vision_ocr.swift`, `scripts/apple_vision_tab_ocr.swift`, `tests/test_amazing_tablature_extraction.py`.
- Challenger/sealed lineage source, CLI, tests, and operating guide: `pocketsteel/amazing_tablature_training.py`, `pocketsteel/amazing_tablature_sealed_test.py`, `scripts/amazing_tablature.py`, `tests/test_amazing_tablature_training.py`, `tests/test_amazing_tablature_sealed_test.py`, `docs/amazing-tablature-training.md`.
- Reproducible dependency inputs, locks, and checker: `pyproject.toml`, `requirements/README.md`, `requirements/runtime.in`, `requirements/runtime.lock`, `requirements/rag.lock`, `requirements/training.in`, `requirements/training.lock`, `requirements/test.in`, `requirements/test.lock`, `requirements/deployment.lock`, `scripts/check_dependency_locks.py`.
- This sanitized handoff.

No files were deleted.

## Tests and checks

- `.venv/bin/python -m ruff check ...` on all Lane 20 Python source and focused tests — PASS.
- `.venv/bin/python -m py_compile ...` on all Lane 20 Python source and CLI — PASS.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_sealed_test.py tests/test_copedent_transfer.py` — `174 passed`.
- `.venv/bin/python -m pytest -q` — `1336 passed in 63.20s`.
- `npm run check:locks` — PASS for five hash-locked environments.
- Disposable Python 3.12 environment installed `requirements/test.lock` with `--require-hashes`; `pip check` — PASS.
- The same disposable lock-identical environment, after the documented `pip install --no-deps -e .`, ran the focused Lane 20 suite — `174 passed`.
- `git diff --cached --check` was run before every commit — PASS.
- Private-ignore audit confirmed `corpus-private/**` remains ignored and untracked.

## Integration notes

The dependency graph is intentionally ordered: decision features precede extraction; extraction and its Swift helpers precede the CLI/sealed coordinator; the final commit can therefore freeze hashes for every required source file. OpenCV is pinned to `4.13.0.92` and Verovio to `6.2.1`; the test lock inherits the training lock.

Existing private challenger/shadow artifacts predate the clean repository revision. Lane 20 should rebuild the discovery challenger and shadow report from committed HEAD before any validation-entry decision. Validation and sealed-test boundaries remain closed.

## Risk assessment

Risk: **medium**. The change set is large because it reconciles several days of accumulated Lane 20 work, but it is split at dependency boundaries, has full-suite and clean-lock verification, and contains no runtime activation or product wiring. Rollback is by reverting the three commits in reverse order; private artifacts are append-only and were not modified by this hygiene pass.

Residual risks:

- Historical untracked Lane 20 handoffs include page-specific private review details and cannot be bulk-committed under the sanitized-handoff rule.
- The modified `integration-status.md` and Lane 06/12 handoffs belong to unrelated prior work and remain parked.
- A separate explicitly authorized private-storage task would be required to normalize legacy filesystem permissions beneath `corpus-private/`; no permission or content change was made here.

## Human decision needed

Yes, but not to accept these commits. A later decision is needed on whether to sanitize/archive the historical page-level handoffs and whether to authorize private-storage permission hardening. Neither decision blocks rebuilding the discovery challenger from clean HEAD.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-0839-01-lane20-repository-hygiene.md`

## Files that must not be staged

- `corpus-private/**`.
- `docs/handoffs/task-completions/integration-status.md` in its current stale/unrelated state.
- All other currently untracked historical handoffs, pending lane-specific and privacy review.

## Recommended next lane

Lane 20 Amazing Tablature Training: rebuild the discovery-only challenger and shadow report from committed HEAD, verify code/data lineage hashes, and stop before validation or sealed-test access.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 20: Rebuild the discovery challenger and shadow report from the clean committed HEAD. Verify lineage and no-rereview accounting without opening validation or sealed-test data, then report readiness.`
