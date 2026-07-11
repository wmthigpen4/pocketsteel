# Melody Studio fretboard marker-label user-smoke fix

## Task summary

Fixed the user-smoke defect where every Melody Studio fretboard marker displayed the full repeated route title, such as `Your melody exercise in G — Single-note melody`.

The shared Fretboard Explorer component was not changed. Melody Studio now adapts each synchronized route position to use the event's resolved top melody pitch as its compact visible label: `D4`, `E4`, `G4`, and so on. Harmony and chord-melody routes use the same resolved top-voice label while retaining their multi-string fretboard positions. The adapter also supplies a concise `Melody note N` role.

No backend/API contract, arranger, auth, DNS, Cloudflare, corpus, Chroma, source-inbox, private-data, brand, or deployment-policy behavior changed.

## Files changed

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1328-06-melody-fretboard-marker-label-fix.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `node --check ui/pedal-steel-fretboard.js` — pass.
- Focused Melody/same-origin/frontend slice: `7 passed, 35 deselected`.
- Full pytest: `934 passed in 38.02s`.
- `git diff --check` on exact paths — pass.
- Local authenticated browser smoke — pass.

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-marker-labels-20260711-1`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-marker-labels-20260711-1`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `9e88622` before fix commit
- Version endpoint: not used for the temporary in-process local server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local server ran from the tested worktree
- Whether app root `/` works: not repeated; direct Studio URL was the smoke target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: covered by same-origin tests
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; unversioned Studio route
- Known caveats: none specific to this label fix

Browser verification proved:

- before the fix, all seven visible marker labels repeated the full single-note route title;
- after the fix, the labels are exactly `D4`, `E4`, `G4`, `B4`, `A4`, `G4`, `B4`;
- the old route title is absent from the fretboard label layer;
- Chord melody retains the same resolved top-voice pitch labels and selects the matching chord-melody fretboard position;
- page overflow is zero, `[object Object]` is absent, and browser warning/error logs are empty.

## Integration notes

- The scoped adapter is `positionsWithScientificOctaves` in Melody Studio.
- The new Melody Studio controller asset key is `melody-marker-labels-20260711-1`.
- Fretboard Explorer and non-Melody consumers retain their existing label behavior.

## Risk assessment

Low. This is a Melody Studio-only presentation adapter change with focused and full regression coverage.

## Human decision needed

No. Proceed through exact-path commit and protected-preview smoke.

## Safe-to-stage exact file list

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1328-06-melody-fretboard-marker-label-fix.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above, refresh protected preview, verify the marker labels in both Faithful melody and Chord melody, then return the cache-busted URL for continued user smoke.
