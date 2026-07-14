# Amazing Tablature asset cache-bust

## Task summary

- The authenticated protected-preview smoke loaded the new Melody Studio HTML but reused JavaScript under the prior account-copedent cache key.
- Updated the two changed Melody Studio script URLs so the Amazing Tablature style catalog and style-change behavior load together with the new HTML.
- Added focused regression assertions for the new cache keys.
- No trainer UI, backend contract, source data, auth, deployment policy, corpus, Chroma, embeddings, or private material changed.

## Files changed

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-14-1513-06-amazing-tablature-asset-cache-bust.md`

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_frontend_answer_ui.py tests/test_amazing_tablature_training.py` — 44 passed.
- `git diff --check -- ui/melody-workbench.html tests/test_melody_workbench_ui.py` — passed.

## Integration notes

- Protected browser smoke on commit `101177f` exposed the stale asset key: the new `Playing style` control was present but had no options because old cached scripts were running.
- The follow-up protected runtime must use the exact commit containing this handoff and verify all seven style labels plus a successful style change.

## Risk assessment

- Low. This is a two-URL cache-key correction with focused tests.
- Rollback is a normal revert of this cache-bust commit; no stored data changes.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-14-1513-06-amazing-tablature-asset-cache-bust.md`

## Files that must not be staged

- All unrelated dirty/untracked files, private batch state, source images, corpus/source material, brand assets, database files, secrets, Chroma/vector data, deployment configuration, and `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

- `01 Repo Steward`, followed by `12 Self-Hosted Deployment` protected browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

- Commit the three exact files, restart the isolated protected preview at that commit, and verify the player-facing arrangement/style flow.
