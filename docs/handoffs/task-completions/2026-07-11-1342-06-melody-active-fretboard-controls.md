# Melody Studio active-only fretboard controls

## Task summary

Implemented the user-smoke adjustment that replaces the stacked whole-phrase fretboard with one active event at a time.

Previous/Next, note pills, score selection, playback, and route changes now remount the fretboard with only the active event's validated position. Single-note routes show one active string location; harmony and chord-melody routes show only the active grip's current string locations.

Added three independent compact display controls above the fretboard:

- `Octave colors` retains the existing scientific-octave overlay and legend behavior.
- `String labels` reuses the shared Explorer component option to show compact string numbers inside active marker bubbles; it defaults off.
- `Note labels` shows or hides the resolved melody/top-voice pitch above the active position; it defaults on.

The shared Fretboard Explorer component and backend/API contracts were not changed. Auth, DNS, Cloudflare, corpus, Chroma, source-inbox, private data, brand, and deployment policy remain untouched.

## Files changed

- `docs/melody-exercise-v0.md`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1342-06-melody-active-fretboard-controls.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `node --check ui/pedal-steel-fretboard.js` — pass.
- Focused Melody/same-origin suite: `16 passed`.
- Full pytest: `934 passed in 39.00s`.
- `git diff --check` on exact paths — pass.
- Local authenticated browser smoke — pass.

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-active-marker-controls-20260711-1`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-active-marker-controls-20260711-1`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `3b15351` before implementation commit
- Version endpoint: not used for the temporary local server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local server ran from the tested worktree
- Whether app root `/` works: not repeated; direct Studio URL was the smoke target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: covered by same-origin tests
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; unversioned Studio route
- Known caveats: none specific to this adjustment

Browser verification proved:

- the initial Faithful melody fretboard contains one highlight group, one D4 location, and one D4 label;
- Next note replaces it with one E4 position and updates the selected position ID;
- String labels changes from no interior labels to `5` on the active E4 marker;
- Note labels removes the pitch label while leaving the active marker visible;
- Chord melody contains one active highlight group with three validated string locations, one D4 top-voice label, and string labels `5`, `6`, and `8`;
- Octave colors remains independently enabled;
- page overflow is zero, `[object Object]` is absent, and browser warning/error logs are empty.

## Integration notes

- `melodyFretboardOptions` now accepts active index and display options, and returns only the matching `renderablePositionId`.
- `renderActiveFretboard` is the single UI synchronization path for note navigation, playback, and route changes.
- The controller asset key is `melody-active-marker-controls-20260711-1`.

## Risk assessment

Low. The adjustment is isolated to the Melody Studio presentation adapter and reuses existing shared component flags.

## Human decision needed

No. Proceed through exact-path commit and protected-preview smoke.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1342-06-melody-active-fretboard-controls.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above, refresh protected preview, verify all three toggles and active-only navigation, then return the cache-busted URL for continued user smoke.
