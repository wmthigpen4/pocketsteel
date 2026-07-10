# Melody Studio calm controls user-smoke adjustment

## Task summary

Resolved the user-smoke usability defect where octave editing was undiscoverable and the page exposed too many simultaneous controls. Phrase chips are now simple selectable note/pitch buttons. One clearly labeled Selected note toolbar owns octave, order, and removal actions. Task cards collapse after task selection, and advanced harmony routes are placed under More arrangements.

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- this handoff

## Tests and checks

- Focused frontend/same-origin suite: 41 passed.
- Full pytest: 918 passed.
- Core JavaScript syntax checks: passed.
- `git diff --check`: passed.
- Local browser smoke: passed for task-card collapse, selectable phrase chips, selected-note octave control, visible pitch update, two primary route choices, collapsed advanced arrangements, and no `[object Object]`.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=calm-local-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart smoke
- Auth required: no
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: working tree based on `9914e25`
- Version endpoint: `/api/version`
- Version endpoint result: protected verification pending commit
- Whether app root `/` works: expected; not the focused target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: expected; not the focused target
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale Melody Studio URLs using the arranger asset cache key
- Known caveats: later automatic notes may follow an explicit octave change to preserve a smooth closest-playable contour; the UI now states this

## Risk assessment

Low. UI state/presentation only; API and arranger mechanics are unchanged. Rollback is the scoped adjustment commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-10-1551-06-melody-studio-calm-controls.md`

## Files that must not be staged

All other dirty or untracked files.

## Recommended next lane

01 Repo Steward exact-path commit, followed by 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact five paths, refresh the supervised preview, then verify the simplified editor and route disclosure at one cache-busted URL.
