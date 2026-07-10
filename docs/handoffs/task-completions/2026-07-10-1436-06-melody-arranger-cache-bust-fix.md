# Melody arranger protected cache-bust fix

## Task summary

Protected smoke of commit `ce20ddf` found that the protected backend returned the new arranger contract while Cloudflare served the prior Studio JavaScript under the unchanged asset query string. Updated the three Melody Studio script URLs to the arranger cache key and added focused regression coverage. No runtime behavior changed beyond ensuring the committed clients load.

## Files changed

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- this handoff

## Tests and checks

- Initial protected smoke: failed route rendering because stale JavaScript was served; backend version correctly reported `ce20ddf`.
- Focused frontend/same-origin tests: 41 passed.
- Core JavaScript syntax checks: passed.
- `git diff --check`: passed.
- Full pytest at the immediately preceding implementation commit: 918 passed.

## Integration notes

This is a scoped smoke-blocking asset cache fix. Protected preview must restart at the follow-up commit and the exact cache-busted page must be tested again.

## Risk assessment

Low. Static asset query strings only; rollback is the scoped follow-up commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-10-1436-06-melody-arranger-cache-bust-fix.md`

## Files that must not be staged

All other dirty/untracked files.

## Recommended next lane

15 QA focused rerun, then 01 exact-path commit and 12 protected-preview restart/smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four listed paths, restart the protected preview, and rerun the exact arranger browser smoke.
