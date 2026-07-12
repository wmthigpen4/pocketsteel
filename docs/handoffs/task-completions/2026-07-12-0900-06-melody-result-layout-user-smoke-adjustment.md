# Melody Studio result-layout user-smoke adjustment

## Task summary

Implemented the six current user-smoke comments as one scoped Melody Studio result-screen adjustment:

- moved **Print** below the tablature, immediately beside Start over;
- removed route-recommendation prose from the rendered lesson;
- moved Octave colors, String labels, and Note labels directly below the fretboard and before arrangement choices;
- hid the introductory hero while a generated E9 lesson is visible, retaining the compact Melody Studio header;
- collapsed loop controls into one horizontal **Loop options** disclosure and omitted that disclosure for sections shorter than eight events;
- added a prominent Edit melody action beside the lesson title while retaining the existing post-tab Edit melody action.

No API, arranger, tab, fretboard, score, print-content, authentication, upload, catalog, corpus, or deployment contract changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Mode: approved user-smoke adjustment / Autopilot

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-12-0900-06-melody-result-layout-user-smoke-adjustment.md`

No files were deleted and no generated artifacts were created.

## Tests and checks

- `node --check ui/melody-workbench.js` — passed.
- Focused Melody Studio/fretboard/frontend/same-origin suite — **81 passed**.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — **936 passed**.
- Scoped `git diff --check` — passed.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8790/ui/melody-workbench.html?access=beta_user&v=melody-result-layout-local-20260712-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart
- Auth required: yes
- Auth provider: local controlled-state beta role
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8790`
- Expected backend port: 8790
- Expected git HEAD: working tree based on `eaaeceb`
- Version endpoint: not used for working-tree smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: cache-busted working-tree assets
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: prior `melody-print-tab` or unversioned Studio URLs
- Known caveats: native macOS print preview remains a user action; automated smoke verifies the Print trigger and existing print stylesheet rather than opening the system dialog

Browser results:

- A seven-note G phrase rendered without the hero, route prose, or loop disclosure.
- The top and post-tab Edit melody actions were present.
- Fretboard display controls began exactly at the fretboard bottom and appeared before arrangement routes.
- Tablature was followed by Edit melody, Start over, and Print; Print and Start over shared the same row.
- An eight-note phrase exposed one closed Loop options disclosure; opening it kept all four loop actions and status in one horizontally contained row.
- Browser console errors: none.

## Integration notes

- The hero is hidden only during the result phase and returns when editing or starting over.
- Loop playback behavior is unchanged; only default visibility and grouping changed.
- The printable artifact remains tablature-only despite the shorter on-screen action label.
- Cache key: `melody-result-layout-20260712-1`.

## Risk assessment

Low. The change is client-only hierarchy, copy, and conditional visibility with focused and full regression coverage. Rollback is the scoped implementation commit.

## Human decision needed

No. The comments provide the approved adjustment scope.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-12-0900-06-melody-result-layout-user-smoke-adjustment.md`

## Files that must not be staged

Every other modified or untracked file, especially corpus/source/pipeline work, source-inbox data, private-data tooling, deployment files, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, and the separate octave-help recommendation.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval, commit only the six exact paths, restart the protected preview, verify `/api/version`, run the same seven/eight-note checks in the authenticated browser, and refresh integration status separately.
