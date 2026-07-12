# Full-song protected-preview cache-bust fix

## Task summary

Protected browser smoke for commit `9c9d2e5` authenticated and loaded the new page shell, but the browser received a stale Melody Studio script and still displayed the removed eight-note copy. Updated the three Melody Studio asset query versions so the complete-song JavaScript and score renderer are fetched as a coherent build.

No product behavior, API contract, catalog data, auth policy, deployment configuration, corpus, private data, or brand assets changed.

## Files changed

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1010-06-full-song-cache-bust-fix.md`

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — **42 passed**.
- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `git diff --check` — pass.

## Integration notes

The protected runtime process was already verified on `9c9d2e5`; this follow-up needs its own exact-path commit, restart, `/api/version` check, and repeated authenticated browser smoke.

## Risk assessment

Low. Static query-string-only cache invalidation. Roll back the scoped follow-up commit if needed.

## Human decision needed

No. This is an observed protected-smoke blocker inside the approved Autopilot loop.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1010-06-full-song-cache-bust-fix.md`

## Files that must not be staged

Every other modified or untracked path, including all parked corpus, source-inbox, private-data, deployment, public/brand, design, and unrelated documentation files.

## Recommended next lane

`01 Repo Steward` exact-path commit, followed by `12 Self-Hosted Deployment` protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four listed paths, restart the protected preview, verify `/api/version`, and reopen the cache-busted full-song URL.
