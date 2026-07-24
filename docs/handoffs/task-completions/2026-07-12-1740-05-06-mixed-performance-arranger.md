# Melody Studio mixed performance arranger

## Task summary

- Replaced the default Vocal steel and all-dyad Recommended harmony routes with one **Recommended arrangement**.
- Added deterministic event-by-event selection among single notes, validated dyads, and chord-backed validated triads.
- Added sparse mechanically checked bar-slide, pedal-glide, and lever-glide transitions without changing melody event count or rhythm.
- Synchronized transitions through tab, score, navigator, fretboard animation, playback, print, and the normalized answer contract.
- Preserved Faithful melody as the first/selected compatibility route and preserved explicit legacy `automatic_harmony` requests.
- Intentionally did not change custom copedents, keys beyond G/C, transcription, corpus, retrieval, auth, or deployment policy.

## Files changed

- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/tab_engine.py`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `docs/melody-exercise-v0.md`
- `tests/test_melody_assistant.py`
- `tests/test_tab_engine.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1740-05-06-mixed-performance-arranger.md`

## Tests and checks

- Python compilation for arranger and tab engine — passed.
- JavaScript syntax for answer client, fretboard, score, and workbench — passed.
- Focused arranger/tab/frontend suite — 97 passed.
- Full pytest — 943 passed.
- `git diff --check` — passed.
- Local authenticated browser smoke at `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=mixed-arranger-local-20260712` — passed.
  - Amazing Grace showed exactly Faithful melody, Recommended arrangement, thirds, sixths, and chord melody.
  - Recommended arrangement visibly mixed one-, two-, and three-note score events.
  - Tab displayed `/`, `\\`, and `~` movement notation and a conditional notation key.
  - Five score gliss indicators rendered for the 35-note song, matching the transition cap.
  - Note 7 displayed `Slide string 4 from fret 5 to fret 3.` and kept score/fretboard selection synchronized.
  - Playback entered the playing state, supporting voices were scheduled, page overflow was zero, and browser warnings/errors were absent.

## Integration notes

- `texture=both` now returns Faithful, mixed, thirds, sixths, and chord melody when chord context permits the triadic route.
- Chordless mixed arrangements use only single notes and dyads; chord melody is omitted without real chord context.
- Mixed events add `texture` and optional `transitionFromPreviousId`; mixed routes add `textureSummary` and `transitions`.
- `TabEvent.transition` is optional and backward compatible. It supplies validated per-string display tokens without adding events.
- Literal tab events remain fixed and receive no generated harmony or transitions.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=mixed-arranger-local-20260712`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart
- Auth required: yes, local scaffold auth
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: working tree based on `ec9cb10`
- Version endpoint: `/api/version`
- Version endpoint result: protected result pending
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in focused local smoke
- Whether app root `/` is expected to work: yes in protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale starting-choice or earlier Melody Studio cache keys
- Known caveats: synthesized playback is a teaching approximation; generated transitions are performance guidance, not claims about a source recording.

## Risk assessment

- Medium. This changes deterministic route selection and several synchronized presentation surfaces, but compatibility fields remain faithful-route based and the full suite/browser loop is green.
- Rollback: revert the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- All files listed under Files changed above.

## Files that must not be staged

- All unrelated dirty, untracked, corpus, source-inbox, private, brand, generated, deployment, auth, and integration-status files.

## Recommended next lane

- Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated mixed-route smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the exact files above, restart the protected preview, and repeat the Amazing Grace route/transition checks before user smoke.
