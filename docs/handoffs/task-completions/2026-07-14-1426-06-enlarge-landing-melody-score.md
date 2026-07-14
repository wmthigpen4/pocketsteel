# Enlarge Landing Melody Score

## Task summary

The user-smoke PNG preview was technically contained but visually unacceptable because the original 2172×724 production derivative retained excessive transparent space and seven notes. The actual clef occupied too little of the 210×70 card surface.

Deterministically cropped the existing transparent production asset to a 1200×400 3:1 composition containing the treble clef, 4/4 signature, five staff lines, and the first four notes. The last three notes and excess transparent margins were removed. No notation was redrawn, traced, or regenerated. The full Melody Studio renderer and all functional workspaces remain unchanged.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Exact-path/hunk commit: `01 Repo Steward`
- Protected-preview verification: `12 Self-Hosted Deployment`
- Task mode: Autopilot user-smoke visual bug fix

## Files changed

- `ui/assets/landing/melody-score.png` — focused 1200×400 transparent crop with four notes
- `ui/melody-score.js` — updated intrinsic dimensions and cache-busted image URL
- `ui/steel-guitar-rag-mock.html` — Melody score script cache key only; unrelated dirty hunks must remain unstaged
- `tests/test_landing_home_ui.py` — updated dimensions, URL, and minimum visible-content-height regression
- `tests/test_same_origin_smoke_server.py` — score script cache-key assertion only; unrelated dirty hunks must remain unstaged
- This handoff

No CSS, full-app renderer, fretboard, lesson, backend, API, auth, corpus, deployment configuration, or source asset changed.

## Tests and checks

- `node --check ui/melody-score.js` — passed
- `node --check ui/landing-home.js` — passed
- `node --check ui/answer-client.js` — passed
- `node --check ui/pedal-steel-fretboard.js` — passed
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 55 passed
- `.venv/bin/python -m pytest -q` — 1,110 passed
- Scoped `git diff --check` — passed
- Asset inspection — 1200×400 RGBA, alpha extrema `(0, 255)`, nonempty alpha bounds `(36, 21, 1200, 370)`; visible content fills more than 80% of asset height
- Local PNG request — `200 image/png`
- Local browser logs — empty

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8918/ui/steel-guitar-rag-mock.html?v=focused-score-local-1`
- Cache-busted URL tested: `http://127.0.0.1:8918/ui/steel-guitar-rag-mock.html?v=focused-score-local-1`
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8918`
- Expected backend port: 8918
- Expected git HEAD: working tree based on `baa1ac20d003f1224b1f49fd6293488139fb5c2f`
- Version endpoint: unavailable on the static-only local server
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted files served directly from the scoped working tree
- Whether app root `/` works: static directory listing only
- Whether app root `/` is expected to work: no for this local static smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stopped local ports, the superseded `landing-melody-png-baa1ac2-20260714` URL, or uncached landing URLs
- Known caveats: the dirty local working tree had 25 pixels of document-level phone-width overflow from unrelated concurrent layout work; the score preview itself was fully contained and the exact-commit protected preview remains the authoritative responsive smoke target

## Local browser smoke result

**Pass for the score preview.**

- The image loaded at natural dimensions `1200×400` and rendered at `210×70`, exact 3:1 ratio.
- Desktop visual inspection showed a treble clef occupying most of the preview height, clearly readable 4/4, and four notes.
- Phone visual inspection showed the same enlarged complete clef and four-note phrase with comfortable card padding.
- The last three notes are absent.
- The card contains zero Canvas and zero SVG descendants.
- The score image remained fully contained with no crop of the clef, time signature, or fourth note.
- No checkerboard or opaque background appeared.
- Browser logs were empty.

## Integration notes

- Asset path remains `ui/assets/landing/melody-score.png`.
- Image URL cache key becomes `focused-four-note-crop-20260714-1`.
- `melody-score.js` cache key becomes `landing-melody-png-crop-20260714-1`.
- `renderPreview(container)` retains its boolean contract and `static-png-preview` marker.
- The full Melody Studio `render(...)` path remains unchanged.

## Risk assessment

Low. This is a deterministic crop plus intrinsic-dimension/cache updates for one decorative preview. Rollback is a single scoped commit with no data or configuration migration.

## Human decision needed

No. The focused crop directly implements the user's suggested removal of the last three notes and is ready for exact-hunk commit and protected-preview smoke.

## Safe-to-stage exact file list

- `ui/assets/landing/melody-score.png`
- `ui/melody-score.js`
- only the Melody score script cache-key hunk in `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- only the Melody score cache-key assertion hunk in `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1426-06-enlarge-landing-melody-score.md`

## Files that must not be staged

- `ui/assets/music_staff.png`
- unrelated hunks in `ui/steel-guitar-rag-mock.html`
- unrelated hunks in `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-14-1421-12-landing-melody-png-protected-smoke.md`
- all other unrelated dirty/untracked files

## Recommended next lane

`01 Repo Steward` for exact-path/hunk commit, then `12 Self-Hosted Deployment` for authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the listed crop, renderer dimensions/cache key, focused tests, and handoff. Restart the protected preview from the exact commit and visually verify the enlarged clef at desktop and phone widths.
