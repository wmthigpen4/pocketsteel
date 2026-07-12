# Melody Studio print-tablature user-smoke adjustment

## Task summary

Replaced Melody Studio's score-printing affordances with a single result action named **Print tablature**. The print sheet now contains the lesson title, optional source identity, selected arrangement name, and the current route's fixed-width tablature. Staff notation, fretboard, route controls, event transport, playback controls, editor chrome, and result actions are excluded from printing.

The staff editor's Print score action was removed. MusicXML export remains available for users who need notation data outside the app.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Mode: user-smoke adjustment / Autopilot

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- this handoff

No files were deleted and no generated artifacts were created.

## Tests and checks

- `node --check ui/melody-workbench.js` — pass
- Focused frontend/fretboard/same-origin suite — 81 passed
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 935 passed
- Scoped `git diff --check` — pass

## Local browser smoke

- Arranged `1 2 3 5` in G.
- Verified the visible result action is `Print tablature`.
- Verified no `Print score` action remains.
- Switched to Recommended harmony and verified the hidden print heading updated to `Arrangement: Recommended harmony`.
- Verified the printable tab was the current harmonized route and contained pedal changes.
- Verified the print media rule uses a landscape page, keeps the title/source/arrangement/tab, and hides the score, fretboard, controls, and editor.
- Browser console warnings/errors: none.

The operating-system print dialog was intentionally not opened during automated smoke; the browser-visible action and parsed print stylesheet were verified directly.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-print-tab-local-20260711-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview refresh after commit
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: `8765`
- Expected git HEAD: working tree based on `7abe48f`
- Version endpoint: not used for working-tree browser smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: cache-busted working-tree assets
- Whether app root `/` works: yes, redirects to the home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: unversioned or earlier Melody Studio cache keys
- Known caveats: automated browser smoke does not operate the native macOS print dialog

## Integration notes

- No API, arranger, tab, fretboard, score-draft, or score-rendering contract changed.
- Printing always uses the currently selected route's tab text.
- The layout uses landscape orientation and a compact monospace font to preserve eight-event section spacing.

## Risk assessment

Low. The change is limited to print hierarchy, copy, route labeling, and cache invalidation. Screen behavior is unchanged outside the removed score-print action and new tab-print action.

## Human decision needed

No. This is a direct user-smoke adjustment.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-2334-06-melody-print-tablature-adjustment.md`

## Files that must not be staged

Every other modified or untracked path, especially corpus, source-inbox, private-data, deployment, public/brand, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated docs/runtime files.

## Recommended next lane

`01 Repo Steward` for exact-path commit, then `12 Self-Hosted Deployment` for protected-preview restart and authenticated print-tab readiness smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the six safe paths, refresh the protected preview, verify `/api/version`, and confirm the current route label and tab are ready for native print at the exact cache-busted URL.
