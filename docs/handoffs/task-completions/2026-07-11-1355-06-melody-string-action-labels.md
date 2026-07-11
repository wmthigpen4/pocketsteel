# Melody Studio string/action marker labels

## Task summary

Fixed the user-smoke defect where the optional fretboard String labels control showed only string numbers and omitted required pedal/lever actions.

Melody Studio now supplies an explicit compact label for every active event note. Open notes remain plain string numbers, while changed notes render the string plus its exact compact action, such as `6B`, `5A`, `4C`, or combined controls when applicable.

The change is isolated to the Melody Studio adapter. The shared Fretboard Explorer component, API, arranger, auth, corpus, sources, and deployment configuration were not changed.

## Files changed

- `docs/melody-exercise-v0.md`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1355-06-melody-string-action-labels.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Focused Melody/same-origin suite: `16 passed`.
- Full pytest: `934 passed in 38.25s`.
- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `node --check ui/pedal-steel-fretboard.js` — pass.
- Exact-path `git diff --check` — pass.
- Local browser smoke — pass.

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-string-action-labels-20260711-2`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-string-action-labels-20260711-2`
- Exact URL the user should use: protected-preview URL to be recorded after commit and refresh
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `8ed363b` before implementation commit
- Version endpoint: not used for the temporary local server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: server ran from the tested worktree
- Whether app root `/` works: not repeated; direct Studio URL was the smoke target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: covered by same-origin tests
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; unversioned Studio route
- Known caveats: none specific to this fix

Local browser proof used the literal validated event `S6:3B`: String labels rendered `6B`, Current note reported `String 6 · Fret 3 · B`, one active dot remained visible, horizontal overflow was zero, and `[object Object]` was absent.

## Integration notes

- `positionsWithScientificOctaves` now adds `stringActionLabels` from each event note's string and `changes` array.
- The shared fretboard component already owns safe rendering and falls back to plain string numbers; no component contract change was required.
- Controller asset key: `melody-string-action-labels-20260711-1`.

## Risk assessment

Low. The change adds already-supported presentation metadata and has focused, full-suite, and visible browser verification.

## Human decision needed

No. Proceed through exact-path commit and protected-preview smoke.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1355-06-melody-string-action-labels.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview refresh and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above and verify `6B` visibly in the protected Studio before closing user smoke.
