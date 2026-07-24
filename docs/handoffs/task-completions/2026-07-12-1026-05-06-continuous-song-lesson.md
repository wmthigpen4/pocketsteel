# Continuous full-song Melody Studio lesson

## Task summary

Removed player-facing phrase splitting from reviewed songbook lessons. Catalog melodies now request `wholeSong=true`, and the backend returns every playable event in one continuous validated lesson. The full score, selected arrangement tab, note navigator, playback timeline, and loop controls now operate over the complete stored melody.

Phrase labels remain catalog/form metadata only. Manual and non-catalog long inputs retain the existing optional section behavior for compatibility.

## Files changed

- `docs/melody-exercise-v0.md`
- `steel_guitar_rag/melody_assistant.py`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1026-05-06-continuous-song-lesson.md`

No catalog pitches, corpus data, private data, auth, deployment configuration, source-inbox, or brand assets changed.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_melody_assistant.py tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py` — **40 passed**.
- `.venv/bin/python -m pytest -q` — **938 passed**.
- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `git diff --check` — pass.
- Local browser, Amazing Grace: one 35-note continuous lesson, 35 score events, 1,145-character full tab, section navigation hidden, Continue hidden, Loop options available.
- Local browser, My Bonnie: one 65-note continuous lesson, 69 score events including rests, 2,336-character full tab, section navigation hidden, Loop options available, no visible error.
- All 12 complete catalog forms reached the arranger as one lesson in automated coverage.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=continuous-song-local-20260712`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=continuous-song-local-20260712`
- Exact URL the user should use: protected-preview URL pending commit/restart
- Auth required: local development role header
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: pre-commit working tree
- Version endpoint: not used for working-tree smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: static/runtime files served directly from the working tree
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes on protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: prior protected cache keys
- Known caveats: the largest catalog response is approximately 1.6 MB because every available validated arrangement route is returned for all 65 melody events

## Integration notes

- `melodyRequest.wholeSong` is an optional backward-compatible boolean.
- A whole-song response has one section labeled `Complete song`, with `eventStart=0`, `eventEnd` equal to the playable melody length, and the full measure range.
- Catalog requests set `wholeSong=true` when their score draft contains reviewed section/form metadata.
- Existing manual continuation and `sectionNumber` behavior remains available for non-catalog requests.
- The lesson title uses `Complete E9 lesson` rather than `Section 1 E9 lesson`.

## Risk assessment

Medium-low. The UI/API payload is larger for full songs, but local generation and rendering remained responsive for the largest 65-note example. Roll back the scoped commit if payload size becomes operationally problematic.

## Human decision needed

No. The user explicitly requested one continuous score and tab.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `steel_guitar_rag/melody_assistant.py`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1026-05-06-continuous-song-lesson.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` until the post-smoke refresh.
- `docs/handoffs/task-completions/2026-07-12-1012-12-full-song-protected-smoke.md` (prior coordination artifact).
- Every unrelated modified/untracked corpus, source-inbox, private-data, deployment, public/brand, design, and generated path.

## Recommended next lane

`01 Repo Steward` exact-path commit, then `12 Self-Hosted Deployment` restart and authenticated protected browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the eight exact paths, restart the protected preview, verify `/api/version`, and repeat Amazing Grace plus My Bonnie browser smoke using the continuous score/tab criteria.
