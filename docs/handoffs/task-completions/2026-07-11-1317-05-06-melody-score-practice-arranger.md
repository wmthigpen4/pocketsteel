# Melody Studio score practice and chord-aware arranger

## Task summary

Completed the approved Melody Studio expansion across backend arranger semantics, the score renderer, interactive practice, notation, and focused QA.

The repeated `B` above every browser note was an invented chord-label bug: melody note names were being stored in the tab event's chord field, and default timing caused the last label to carry across the rendered staff. Melody pitch and harmony are now separate. Melody-only input renders no chord symbols; supplied harmony renders only at real chord changes and is preserved as `harmonySymbol`.

The score is now an interactive practice surface with synchronized staff, fretboard, navigator, and tab selection; moving playback cursor; adjustable tempo; count-in; pause/resume and stop; current-measure and selected-note loops; optional synthesized chord context; score printing; G/C key signatures; eighth-note beams; ties, rests, lyrics, accidentals, dots, and accent/tenuto/staccato support. MusicXML carries dots and articulations.

The arranger now uses supplied chord symbols to rank mechanically valid standard-E9 harmony and chord-melody grips. Route payloads expose the chord-context symbols and whether chord-aware ranking was applied. The resolved melody remains the top voice and existing G/C, standard-E9, route, attribution, sectioning, and compatibility contracts remain intact.

Intentionally not changed: auth, payment, DNS, Cloudflare Access/Tunnel policy, import feature flag, scraping, corpus, Chroma/embeddings, source-inbox, private data, public launch policy, broad branding, or unrelated parked worktree files.

## Files changed

- `docs/melody-exercise-v0.md`
- `pocketsteel/melody_arranger.py`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1317-05-06-melody-score-practice-arranger.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `node --check ui/pedal-steel-fretboard.js` — pass.
- `.venv/bin/python -m py_compile pocketsteel/melody_arranger.py pocketsteel/melody_assistant.py pocketsteel/api.py` — pass.
- Focused melody/API checks: `32 passed, 289 deselected`.
- Relevant combined Melody/API/same-origin/frontend suite after the cache assertion fix: equivalent component suites green; the first combined run found only the intentionally changed asset-version assertion, which was updated and rerun.
- Focused final Melody and same-origin suite: `37 passed`.
- Full pytest after the final chord-change-only tab refinement: `934 passed in 38.19s`.
- `git diff --check` on the exact feature paths — pass.
- Local authenticated browser smoke — pass.

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-score-practice-20260711-3`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-score-practice-20260711-3`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `2afda38` before feature commit
- Version endpoint: not used for the temporary in-process local smoke server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local server ran directly from the inspected worktree after syntax and pytest verification
- Whether app root `/` works: not repeated; canonical direct Studio route was the smoke target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not repeated in browser; same-origin tests verify it is served
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; unversioned Studio route; external upload destinations
- Known caveats: browser synthesis sound quality is deliberately simple and browser/device dependent; protected import/catalog remains controlled by its existing default-off environment flag

Browser verification covered:

- `5 6 1 3 2 1 3` renders D4, E4, G4, B4, A4, G4, B4 with zero chord annotations;
- the active renderer remains `vexflow-5.0.0`, including a G key signature and generated beams;
- selecting G4 on the staff selects G4 in the navigator and current-note/fretboard state;
- playback advanced the selected score event, navigator, and current note, then Pause changed to Resume;
- selected-note looping reported `Looping notes 4–7` and duplicate DOM IDs were absent;
- a real G chord entered in the score rendered once in the builder and once in the result, while the route recommendation stated `Chord-aware ranking used: G`;
- practice controls were visible, page horizontal overflow was zero, `[object Object]` was absent, and browser warning/error logs were empty.

API fallback was not used as a substitute for browser smoke.

## Integration notes

- `melody_exercise.routes[*].chordContext` now contains `symbols` and `usedForRanking`.
- Structured arranger events may preserve `articulation`; actual chord context remains in `chord`/`harmonySymbol`, never a melody-note fallback.
- Plain note/degree input receives deterministic 4/4 measure/beat positions so score navigation and looping remain meaningful.
- Existing top-level events/tab/fretboard compatibility remains unchanged.
- New score/practice assets use cache key `melody-score-practice-20260711-3`.

## Risk assessment

Medium-low. The feature adds browser audio scheduling and more score controls, but it is isolated to the existing feature-gated Melody Studio. Deterministic arranger validation, full pytest, and rendered browser smoke are green. Rollback is the single feature commit.

## Human decision needed

No. Proceed through exact-path commit and protected-preview smoke. User smoke begins only after protected verification passes.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `pocketsteel/melody_arranger.py`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1317-05-06-melody-score-practice-arranger.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: exact-stage only the listed files, commit the feature, restart the protected preview using the documented user-owned listener method, verify `/api/version`, and run authenticated score/practice/chord smoke before user handoff.
