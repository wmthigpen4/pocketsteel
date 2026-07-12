# Wrapped full-song score and lyric cues

## Task summary

- Kept complete songbook arrangements as one continuous lesson instead of returning to eight-note phrase pages.
- Replaced the result score's hidden horizontal overflow with responsive multi-system staff wrapping.
- Added each reviewed song section label to the first note of that section and added a sticky lyric/song cue that follows the active note.
- Intentionally did not change arranger, API, catalog, auth, corpus, deployment, or source contracts.

## Files changed

- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1041-06-wrapped-score-lyric-cues.md`

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/melody-score.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 42 passed.
- `.venv/bin/python -m pytest -q` — 938 passed.
- `git diff --check` — passed.
- Local authenticated browser smoke at `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=wrapped-score-local-20260712` — passed.
  - Amazing Grace rendered all 35 notes and 16 measures as four stacked staff systems.
  - Score canvas `scrollWidth` equaled `clientWidth`; page-level horizontal overflow was absent.
  - The score contained all four reviewed lyric cues.
  - Selecting note 9 changed the sticky cue to `How sweet the sound`.
  - Continuous tab remained 1,145 characters and phrase navigation remained hidden.

## Integration notes

- `scoreSystemLayout()` is a new client-only helper used by both VexFlow and fallback SVG rendering.
- Section labels already present in the in-memory score draft are presentation metadata; there is no API change.
- The selected active note measure determines the current sticky lyric/song cue.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=wrapped-score-local-20260712`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart
- Auth required: yes, local scaffold auth
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: working tree based on `8efb56b`
- Version endpoint: `/api/version`
- Version endpoint result: local working-tree smoke; protected result pending
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes in protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale non-cache-busted protected tabs
- Known caveats: public-domain catalog section labels are used as lyric/song cues; not every catalog entry currently has a complete lyric transcription.

## Risk assessment

- Risk: low to medium. Rendering geometry changed for long scores, but both render paths share deterministic layout tests and the full frontend/backend suite is green.
- Rollback: revert the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1041-06-wrapped-score-lyric-cues.md`

## Files that must not be staged

- All unrelated dirty, untracked, corpus, source-inbox, private, brand, generated, deployment, and integration-status files.

## Recommended next lane

- Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the exact file list above, then verify the cache-busted protected preview.
