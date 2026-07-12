# Melody Studio route-to-score synchronization fix

## Bug summary

When the user selected a harmony or chord-melody arrangement, the fretboard and tablature changed to the multi-string grip but the staff continued to show only the top melody note. The route switch was working; `scoreDraftFromExercise` copied only `event.pitchValue` and discarded the additional mechanically validated pitches in `event.notes` before the score renderer received them.

The fix derives every selected string's absolute E9 pitch from string, fret, and pedal/lever changes, carries the unique ordered pitches into the result score draft, and teaches both the VexFlow and local SVG fallback renderers to draw stacked note heads. The resolved melody remains the top voice.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Mode: user-smoke bug / Autopilot

## Files changed

- `ui/melody-workbench.js`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- this handoff

No files were deleted and no generated artifacts were created.

## Tests and checks

- `node --check ui/melody-workbench.js` — pass
- `node --check ui/melody-score.js` — pass
- Focused frontend/fretboard/same-origin suite — 81 passed
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 935 passed
- Scoped `git diff --check` — pass

## Local browser smoke

- Arranged `1 2 3 5` in G.
- Faithful melody rendered four staff events with one note head each.
- Recommended harmony rendered two note heads in every event; accessible pitch labels were `B3, G4`, `F#4, A4`, `G4, B4`, and `F#4, D5`.
- Chord melody rendered three note heads in every event; the first accessible pitch label was `B3, E4, G4`, retaining G4 as the top melody voice.
- Route selection, fretboard, tab, score labels, and note-head counts changed together.
- VexFlow 5.0.0 remained the active renderer.
- Browser console warnings/errors: none.
- `[object Object]`: absent.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-route-score-local-20260711-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview refresh after commit
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: `8765`
- Expected git HEAD: working tree based on `e315598`
- Version endpoint: not used for working-tree browser smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: cache-busted working-tree assets
- Whether app root `/` works: yes, redirects to the home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: unversioned or earlier Melody Studio cache keys
- Known caveats: this fix synchronizes staff pitch content; playback behavior was not expanded to arpeggiate or sustain every grip voice

## Integration notes

- No API, arranger, route, tab, or fretboard contract changed.
- Result score drafts now carry an optional `pitches` array alongside the compatible top-level `pitchValue`/`pitch` melody voice.
- Existing single-note score drafts behave unchanged.

## Risk assessment

Low to medium. The score renderer now accepts multiple pitches per event, but the change is additive, preserves single-note fallback behavior, and is covered by pitch derivation, reflow, VexFlow browser, and full regression checks. Rollback is the scoped implementation commit.

## Human decision needed

No. This is a synchronization bug fix within the approved user-smoke loop.

## Safe-to-stage exact file list

- `ui/melody-workbench.js`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-2325-06-melody-route-score-sync-fix.md`

## Files that must not be staged

Every other modified or untracked path, especially corpus, source-inbox, private-data, deployment, public/brand, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated docs/runtime files.

## Recommended next lane

`01 Repo Steward` for exact-path commit, then `12 Self-Hosted Deployment` for protected-preview restart and authenticated route-switch smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the seven safe paths, restart the protected preview through the documented user-owned-listener fallback, verify `/api/version`, and confirm one-, two-, and three-note score events through authenticated browser smoke.
