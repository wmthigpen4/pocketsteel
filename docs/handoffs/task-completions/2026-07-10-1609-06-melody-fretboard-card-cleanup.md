# Melody Studio fretboard card cleanup

## Task summary

User smoke found that Melody Studio exposed the shared Fretboard Explorer's dense position-card strip and full technical position inspector. The cards obscured the string assignment, while the inspector duplicated lesson information without a clear Melody Studio purpose.

Completed a scoped Lane 06 user-smoke repair:

- Hid the generic fretboard filters, position cards, legend, and technical inspector inside Melody Studio only.
- Added a compact `Current note` readout showing the resolved note, exact string(s), fret, pedal/lever state, and movement cue.
- Preserved the large fretboard, event stepper, tab, and route behavior.
- Updated the shared programmatic selection helper so visible fretboard highlights continue to follow the active event when position tools are hidden.
- Updated the Melody Studio asset cache key.

Intentionally not changed: Fretboard Explorer presentation, backend arranger output, auth, deployment configuration, corpus data, or source behavior.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lane: `15 QA / Answer Eval`
- Mode: user-smoke autopilot bug fix during the smoke freeze

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-10-1609-06-melody-fretboard-card-cleanup.md`

No files were deleted. No generated artifacts were created.

## Tests and checks

- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q tests/test_pedal_steel_fretboard_ui.py tests/test_melody_workbench_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py` — 79 passed.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 921 passed.
- `git diff --check` — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=fretboard-cleanup-syncfix-20260710`
- Cache-busted URL tested: same as exact browser URL
- Exact URL the user should use: pending protected-preview restart and smoke
- Auth required: no; local beta-user session override used
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: `8898`
- Expected git HEAD: working tree based on `9081c91` plus the scoped uncommitted fix
- Version endpoint: not required for local working-tree smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: served directly from the inspected working tree
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes in the normal runtime; not relevant to this feature route
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale Melody Studio cache keys
- Known caveats: protected-preview verification still required after commit and restart

## Local browser smoke result

Passed. Generated a G-major song-arrangement lesson for `5 6 1 3` and verified:

- `Current note` initially showed `D (D4)` and `String 7 · Fret 8 · Open`.
- The position selector-card count was zero.
- The technical detail-box count was zero.
- The filter panel and legend were absent.
- Selecting `Next note` changed the readout to `E (E4)` and `String 6 · Fret 8 · Open`.
- The fretboard figure's selected position and the visible `.is-selected` highlight both changed from event 1 to event 2.
- No `[object Object]` text rendered.

## Integration notes

The shared `selectPedalSteelFretboardPosition` helper now accepts a matching visible highlight as a valid programmatic selection target when the optional selector-card UI is not rendered. Existing selector-backed behavior is unchanged.

## Risk assessment

Low. The visual removal is scoped by Melody Studio mount options. The shared helper change only broadens valid programmatic selection to the component's already-rendered highlight elements and has focused regression coverage. Rollback is the scoped implementation commit.

## Human decision needed

No. This is a direct repair of observed user-smoke defects.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-10-1609-06-melody-fretboard-card-cleanup.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, brand, deployment, private-data, generated-report, and parked documentation paths shown by `git status --short`.

## Recommended next lane

`01 Repo Steward`, then `12 Self-Hosted Deployment` for exact-path commit, protected-preview restart, and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under autopilot with exact-path staging and a scoped commit, restart the protected preview using the documented user-owned runtime process, verify `/api/version`, then run authenticated browser smoke on a new cache-busted Melody Studio URL.
