# Amazing Tablature final regression check

## Task summary

- The final exact-commit full-suite run found one stale same-origin asset-key expectation after the protected-preview cache correction.
- Updated that focused assertion to require the Amazing Tablature Melody Studio controller key.
- The same run also reported two pre-existing environment-only private-index failures because ignored `corpus-private/` Chroma data is intentionally absent from detached exact-commit worktrees. The full suite is therefore rerun in the main workspace, where the ignored test dependency is available, without copying or staging private data.

## Files changed

- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1519-15-amazing-tablature-final-regression.md`

## Tests and checks

- Exact detached-worktree full run before this assertion correction — 1,115 passed, 3 failed: one relevant stale asset assertion and two classified missing-private-index environment failures.
- `.venv/bin/python -m pytest -q tests/test_same_origin_smoke_server.py tests/test_melody_workbench_ui.py tests/test_frontend_answer_ui.py tests/test_amazing_tablature_training.py` — 59 passed.
- `.venv/bin/python -m pytest -q` in the main workspace — 1,118 passed.
- `git diff --check` for this exact slice — passed.

## Integration notes

- This does not change runtime behavior. It aligns the same-origin static-serving regression with the already-smoked player-facing asset URL.
- No private index was copied into the runtime worktree.

## Risk assessment

- Low. Test-only correction.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1519-15-amazing-tablature-final-regression.md`

## Files that must not be staged

- Private batch state, private Chroma, source images, corpus/source material, databases, secrets, environment files, unrelated dirty/untracked files, and coordination snapshots.

## Recommended next lane

- `01 Repo Steward` exact-path test-only commit, followed by exact version verification.

## Commit readiness

Safe to commit

## Suggested next step

- Run the focused same-origin test and the full suite in the main workspace, then commit only these two files if green.
