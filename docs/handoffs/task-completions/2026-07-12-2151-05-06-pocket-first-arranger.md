# Melody Studio pocket-first recommended arranger

## Task summary

- Rebuilt Recommended arrangement around validated harmonic-pattern and active-chord grips instead of event-local texture selection.
- Added rhythm-aware pickup, passing, tension, resolution, arrival, sustained-note, and cadence roles.
- Preserved the exact melody pitch/register as the top voice and required supporting harmony notes to fit the active chord.
- Added performance-control posture, harmonic path, canonical grip, selection reason, and route path-summary metadata.
- Corrected Amazing Grace so the opening G stays open, B over D7 remains a tension, A resolves at fret 5 on strings 4-5-6 with A+B, and E over C uses fret 3 on strings 5-6-8 with A+B.
- Replaced generated compound transition tokens with semantic source/connector/destination data and complete endpoint tab columns.
- Added the collapsed Why this grip? explanation, complete movement choreography, sustained-voice score/fretboard behavior, and measure-wrapped printed tab.
- Intentionally did not change audio transcription, custom copedents, keys beyond G/C, auth, corpus, retrieval, scraping, embeddings, deployment configuration, or private data.

## Files changed

- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/melody_assistant.py`
- `steel_guitar_rag/tab_engine.py`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_tab_engine.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-12-2151-05-06-pocket-first-arranger.md`

No files were deleted. No generated artifacts were added.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/melody_arranger.py steel_guitar_rag/melody_assistant.py steel_guitar_rag/tab_engine.py` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-score.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- Focused arranger/tab/frontend/same-origin suite — **102 passed**.
- Full `.venv/bin/python -m pytest -q` — **948 passed**.
- Scoped `git diff --check` — passed.
- Local authenticated browser smoke — passed.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=pocket-arranger-local-20260712`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending committed protected-preview restart
- Auth required: yes, local scaffold identity
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: working tree based on `2667ba5`
- Version endpoint: `http://127.0.0.1:8765/api/version`
- Version endpoint result: `2667ba5`, feature flags `melodyExercise=true`, `melodyCatalog=true`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, 302 to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, 200
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale `mixed-arranger-2667ba5` or earlier Melody Studio cache keys
- Known caveats: synthesized playback and generated movements remain teaching guidance rather than claims about a source performance

Observed results:

- Amazing Grace rendered all 35 events and five route choices.
- Recommended arrangement note 2 showed fret 3 open with the explanation that A+B would produce C rather than G.
- Note 6 showed strings 4, 5, and 6 at fret 5 with A+B and the instruction `release C; press A+B`.
- Note 24 showed strings 5, 6, and 8 at fret 3 with A+B.
- Staff note heads, active fretboard strings/frets, navigator, and selected route remained synchronized.
- Tab contained semantic `~~~~~` connector space and no legacy compound `5/3`-style destination token.
- Page overflow was zero, `[object Object]` was absent, and browser warning/error logs were empty.

## Integration notes

- `melodyRequest` now accepts optional `meter` and `pickupBeats`; existing request shapes remain valid.
- Mixed events add `arrangementRole`, `performanceControls`, `patternFamily`, `canonicalGrip`, and `selectionReason`.
- Mixed routes add `pathSummary`.
- Transitions retain their IDs, kind, scope, frets, and control states and add source/destination/sustained/repicked/released strings plus per-string `voiceActions`.
- New arranger transitions do not emit `tabTokens`; legacy input remains accepted by the tab renderer.
- `tabExample.print_tab_text` supplies measure-labeled printable systems without splitting transition pairs; continuous screen tab remains unchanged.

## Risk assessment

- Medium. This changes deterministic arrangement selection and several synchronized lesson surfaces, but compatibility routes and top-level faithful events remain intact and the complete test/browser loop is green.
- Rollback: revert the scoped implementation commit.

## Human decision needed

- No. The approved implementation scope covers exact-path commit and protected-preview smoke.

## Safe-to-stage exact file list

- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/melody_assistant.py`
- `steel_guitar_rag/tab_engine.py`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_tab_engine.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-12-2151-05-06-pocket-first-arranger.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in the implementation commit.
- All unrelated dirty/untracked corpus, source-inbox, pipeline, private, public, brand, Neon Sign, generated, deployment, auth, and design files.

## Recommended next lane

- Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the exact files above, restart the protected preview, verify `/api/version`, and repeat the Amazing Grace Recommended arrangement checks at the exact cache-busted protected URL.
