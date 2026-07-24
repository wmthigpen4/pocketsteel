# C-Pedal Restraint and Full-Grip Slide Adjustment

## Task summary

The user reported that Melody Studio's Recommended arrangement used the C pedal too freely and usually treated slides as a single melody string moving into a larger grip. This user-smoke adjustment rebuilds that behavior around common E9 pedal postures and complete grip movement.

Completed:

- Common open, A, B, and A+B postures now outrank specialized C and B+C postures.
- C/B+C remains available for mechanically justified minor arrivals and literal user-entered tab; it is not removed from the copedent.
- Full-grip slides are chosen before melody-only slides when two- or three-string endpoints can sustain mechanically.
- Validated open-to-A+B and A+B-to-open grips may slide as far as seven frets so familiar G and V-to-I moves remain available.
- One-string-into-three-string moves are rejected as generated full-grip slides.
- Complete source and destination tab columns use `~~~~~` on every sounding slide voice; `-----` is reserved for a held voice.
- Player instructions, score voices, fretboard animation data, and playback plans now share the complete sustained-string transition.
- The Melody Exercise contract documents the adjusted musical policy and notation.

Intentionally not changed:

- Literal pasted tab, including literal C-pedal positions.
- Faithful melody, fixed thirds, fixed sixths, or chord-melody route contracts.
- Custom copedents, keys beyond G/C, audio transcription, auth, corpus, retrieval, deployment policy, or source data.

## Lane classification

- Primary lanes: 05 Backend / RAG Integration and 06 UX/UI Design
- Verification lane: 15 QA / Answer Eval
- Task mode: approved user-smoke adjustment under the Autopilot loop

## Files changed

- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/tab_engine.py`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_tab_engine.py`
- `docs/melody-exercise-v0.md`
- This handoff

No files were deleted and no generated artifact was created.

## Tests and checks

Passed:

- `.venv/bin/python -m py_compile steel_guitar_rag/melody_arranger.py steel_guitar_rag/melody_assistant.py steel_guitar_rag/tab_engine.py`
- `node --check ui/answer-client.js`
- `node --check ui/melody-score.js`
- `node --check ui/melody-workbench.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest -q tests/test_melody_assistant.py tests/test_tab_engine.py tests/test_melody_workbench_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py` — 110 passed
- `.venv/bin/python -m pytest -q` — 956 passed
- Independent focused arranger QA — 68 passed
- `git diff --check`

Regression evidence:

- Amazing Grace Recommended arrangement contains no C-pedal events.
- Its D-to-G resolution renders strings 4–5–6 as `5`, `5A`, `5B`, then `~~~~~`, then complete fret-3 open endpoints.
- The G-to-G fixture renders strings 4–5–6 as `10`, `10A`, `10B`, then `~~~~~`, then complete fret-3 open endpoints.
- Both are `full_grip` transitions with all three strings sustained and no released or repicked string voices.
- A validated A-minor arrival can still select B+C.
- Literal C-pedal tab remains unchanged.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=full-grip-slides-local-20260713`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=full-grip-slides-local-20260713`
- Exact URL the user should use: protected-preview URL to be recorded after commit and restart
- Auth required: no
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `e871411d4a8f4acfc90a43a7b7097554c5438ae1` plus the scoped working-tree changes described here
- Version endpoint: not used for the local dirty-worktree smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: exact local working tree and cache key
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes in the protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: none
- Known caveats: local smoke does not prove Cloudflare Access or protected-preview runtime behavior

Browser result: pass.

- Loaded the complete 35-note Amazing Grace example and arranged it for E9.
- Recommended arrangement showed all five expected route choices and no `[object Object]` text.
- The tab showed complete three-string D-to-G and longer full-grip slide endpoints.
- Selecting the resolving G synchronized the three-voice score, full-grip tab, current-note instruction, and fretboard state.
- The C arrival remained the reviewed fret-3, strings 5–6–8, A+B grip.
- Page-level horizontal overflow was zero.
- Browser console warning/error query returned none.

## Integration notes

- `mixed_arrangement` keeps the existing interface; the new behavior is ranking and transition selection, not a route ID or API migration.
- `performanceControls` remains the complete posture held by the player. Per-string `changes` remains limited to controls that affect that string.
- Transition `controlChanges` records pedal/lever presses and releases separately from sustained-string voice actions.
- The UI cache key is `full-grip-slides-20260713-1`.

## Risk assessment

Medium-low. Mechanical, tab, UI, playback, and complete-suite checks are green. Musical taste across every catalog melody still benefits from user smoke. C-pedal restraint is intentionally strong outside validated B+C minor arrivals and literal input; a later approved refinement could allow other specifically reviewed major-context exceptions.

Rollback: revert the scoped implementation commit. No data migration or persisted user state is involved.

## Human decision needed

No. The user already approved the user-smoke repair loop. After protected-preview smoke passes, the only requested human action is normal user smoke.

## Safe-to-stage exact file list

- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/tab_engine.py`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_tab_engine.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-13-0856-05-06-c-pedal-full-grip-slide-adjustment.md`

## Files that must not be staged

All unrelated dirty or untracked files, especially corpus/source metadata, source-inbox data, private files, brand/design assets, deployment/auth material, generated reports, and existing coordination files. In particular, leave `docs/handoffs/task-completions/integration-status.md` and `docs/handoffs/task-completions/2026-07-12-2158-12-pocket-first-arranger-protected-smoke.md` unstaged.

## Recommended next lane

01 Repo Steward for exact-path commit, then 12 Self-Hosted Deployment for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the exact file list above, then restart the protected preview and smoke the cache-busted Melody Studio URL against the committed HEAD.
