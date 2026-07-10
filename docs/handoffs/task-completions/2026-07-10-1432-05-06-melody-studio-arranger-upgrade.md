# Melody Studio arranger upgrade

## Task summary

Implemented the approved octave-aware standard-E9 arranger for Melody Studio. Fixed-string G/string-4 and C/string-5 placement was removed. The feature now resolves melodic register and contour, preserves literal tab positions, recommends validated harmony, exposes alternate route textures, and keeps every route synchronized across events, tab, fretboard, and explanation.

Intentionally unchanged: audio/YouTube transcription, keys beyond G/C major, minor keys, custom copedents, corpus/retrieval, auth, DNS, Cloudflare policy, and visual assets.

## Lane classification

- Primary: 05 Backend / RAG Integration and 06 UX/UI Design
- Supporting: 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment
- Mode: approved autopilot feature run

## Files changed

- `pocketsteel/melody_arranger.py` (new)
- `pocketsteel/melody_assistant.py`
- `ui/answer-client.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/melody-exercise-v0.md`
- this handoff

## Contract and behavior changes

- `melodyRequest` accepts optional `contourMode`, `texture`, and structured melody events with direction/octave or literal `string`, `fret`, and `changes`.
- `melody_exercise` adds `routes`, `selectedRouteId`, and `input.resolvedPhrase`; legacy top-level events/tab/fretboard remain the selected single-note route.
- Default contour is `closest_playable`; `5 6 1 3 2 1 3` resolves to `D4 E4 G4 B4 A4 G4 B4`.
- Ascending/descending contours use a whole-phrase register plan. Numbered sections retain the full phrase's octave continuity.
- Literal tab remains on its entered string/fret/control state and retains its pitch register.
- Available routes include single note, recommended mixed thirds/sixths, fixed thirds, fixed sixths, and chord melody. Unsupported routes are omitted.
- Every displayed harmony event is generated from pitch-validated Explorer rows with the resolved melody pitch as the actual top voice.

## Tests and checks

- Focused arranger/API/UI regression: 357 passed.
- Dedicated Melody tests: 17 passed.
- Full pytest: 918 passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `git diff --check` — passed.
- Local browser smoke — passed for contour preview, lesson generation, five route choices, recommended two-note harmony switching, synchronized tab/fretboard/event state, literal `S4: 3 2F 7` preservation, and no `[object Object]`.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=arranger-local-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart smoke
- Auth required: no
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: working tree based on `0e4ab051fd389d382c9b87e582983ca374596bce`
- Version endpoint: `/api/version`
- Version endpoint result: protected version verification pending commit
- Whether app root `/` works: expected; not the focused local target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: server advertised; not the focused local target
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale protected URLs ending in `4a00fc2` or `6f95e9f`
- Known caveats: protected-preview restart requires the installed privileged LaunchDaemon helper

## Risk assessment

Medium. This replaces core melody placement and expands the public optional response contract, but is feature-flagged, limited to G/C standard E9, mechanically validated, backward compatible, and covered by the full suite. Rollback is the scoped implementation commit.

## Human decision needed

No. The feature plan and protected-preview loop were explicitly approved.

## Safe-to-stage exact file list

- `pocketsteel/melody_arranger.py`
- `pocketsteel/melody_assistant.py`
- `ui/answer-client.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-10-1432-05-06-melody-studio-arranger-upgrade.md`

## Files that must not be staged

All other dirty or untracked files, especially corpus/source-inbox, pipeline scripts, private/generated content, brand binaries, deployment assets, auth material, and unrelated docs.

## Recommended next lane

01 Repo Steward exact-path commit, then 12 Self-Hosted Deployment restart and authenticated protected-preview browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the exact safe paths, restart protected preview from that commit, verify `/api/version`, then smoke closest contour, recommended harmony switching, literal tab preservation, and synchronization at one exact cache-busted URL.
