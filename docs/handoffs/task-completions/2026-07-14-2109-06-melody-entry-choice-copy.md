# Melody Studio Entry Choice Copy

## Task summary

- Fixed the confusing review-state choice row where three different entry tools all changed their primary label to `Replace melody`.
- Each choice now keeps its stable identity: `Browse songbook`, `Type or tap notes`, `Record or upload audio`, `Staff editor`, and the feature-gated `Import music` path.
- When a melody already exists, only the supporting line changes to explain the consequence, such as `Choose a different reviewed song` or `Enter a different melody`.
- The explicit confirmation action still says `Replace melody`, where that wording describes the actual action.
- Added a fresh Melody Studio script cache key.

## Lane classification

- Primary lane: 06 UX/UI Design.
- Supporting lanes: 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment.
- Task mode: GREEN small UI-copy correction within the approved user-smoke Autopilot scope.

## Files changed

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This implementation handoff and the Lane 15 QA handoff.
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks

- Focused Melody/frontend/static suite: 62 passed.
- Full Python suite: 1,133 passed in 62.26 seconds.
- `node --check ui/melody-workbench.js`: passed.
- `npm run check:js`: passed.
- `git diff --check`: passed on the scoped files.

## Integration notes

- Entry behavior and replacement confirmation behavior are unchanged; only the labels and helper text in the choice row changed.
- The cache-busted script reference is `melody-workbench.js?v=entry-choice-copy-20260714-1`.
- No API, schema, auth, account, corpus, model, mechanical, retrieval, or deployment-policy behavior changed.

## Risk assessment

- Risk: low. Copy/presentation only, with direct helper tests, static-serving coverage, and the full suite.
- Rollback: revert the scoped commit and restore the prior script cache key.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-2109-06-melody-entry-choice-copy.md`
- `docs/handoffs/task-completions/2026-07-14-2109-15-melody-entry-choice-copy-qa.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` and all unrelated dirty/untracked, private, account-data, corpus, source-inbox, vector, database, brand/design, deployment, auth, and historical handoff files.

## Recommended next lane

- Lane 01 exact-path commit, followed by Lane 12 protected-preview browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

- Commit only the six approved files and verify the review-state choice row on the authenticated protected preview.
