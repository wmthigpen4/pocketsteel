# Simple landing music score

## Task summary

The protected-preview Melody Studio card showed boxed placeholder glyphs instead of a readable musical score. Replaced the landing-only VexFlow preview drawing with a deliberately simple native Canvas score: five staff lines, a hand-drawn treble-clef shape, 4/4 time, six filled noteheads, attached stems, two beam groups, and an ending bar. The accepted landing fretboard preview and the full interactive Melody Studio renderer were intentionally not changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Exact-path commit: `01 Repo Steward`
- Protected-preview verification: `12 Self-Hosted Deployment`
- Task mode: user-smoke bug Autopilot UI fix

## Files changed

- `ui/melody-score.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

No CSS, fretboard, backend, API, dependency, full-app renderer, auth, corpus, Chroma, private data, brand asset, or deployment configuration changed.

## Tests and checks

- `node --check ui/melody-score.js` — passed.
- `node --check ui/landing-home.js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 53 passed.
- `.venv/bin/python -m pytest -q` — 1,100 passed.
- Scoped `git diff --check` — passed.
- Local browser smoke at desktop and narrow widths — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?v=simple-score-canvas-local-1`
- Cache-busted URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?v=simple-score-canvas-local-1`
- Exact URL the user should use: protected-preview URL will be recorded after the exact-path commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree based on `eb08276cb121684a054a80b482957f1b4dd92f01`
- Version endpoint: not available on the static local smoke server
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted assets served directly from the scoped working tree
- Whether app root `/` works: static directory listing only; not the application root
- Whether app root `/` is expected to work: no for this static-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: the stopped local static server after handoff, historical uncached preview URLs, or earlier protected commit URLs
- Known caveats: local browser device-pixel ratio was below 1, so the Canvas correctly clamped its backing scale to 1 for legibility. Protected authenticated smoke remains required after commit.

## Smoke result

**Pass.**

- Renderer marker was `simple-canvas-preview` with one Canvas and no SVG descendant.
- The Canvas advertised `simple-musical-score`, retained the `300×86` logical surface, and had proportional CSS dimensions.
- Desktop CSS size was approximately `223.54×64.06`; narrow CSS size was `300×86`; both fit the card with zero document overflow.
- Visual inspection showed five staff lines, a clef, 4/4, six recognizable noteheads, attached stems, two attached beam groups, and an ending bar.
- No square placeholder music glyphs were present because the landing preview no longer uses VexFlow glyphs or a music font.
- The miniature fretboard remained unchanged.

## Integration notes

- `STEEL_RAG_MELODY_SCORE.renderPreview(container)` and its boolean return contract remain unchanged.
- The landing diagnostic marker changes from `vexflow-canvas-preview` to `simple-canvas-preview`.
- The Canvas marker is `data-preview-kind="simple-musical-score"`.
- The landing `melody-score.js` cache key changes to `simple-score-canvas-20260714-1`.
- VexFlow remains loaded because the full Melody Studio renderer still uses it; only the miniature landing preview bypasses it.

## Risk assessment

- Risk: low.
- Reason: the fix is isolated to the landing preview function, cache key, and focused tests. The full Melody Studio and fretboard implementations are untouched.
- Rollback: revert the scoped implementation commit; no data or configuration migration is involved.

## Human decision needed

No. Protected-preview visual smoke is the remaining automated step.

## Safe-to-stage exact file list

- `ui/melody-score.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1345-06-simple-landing-music-score.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-14-1319-12-landing-non-svg-previews-protected-smoke.md`
- All other unrelated dirty and untracked files
- Protected/private corpus, Chroma, `source-inbox`, `.wrangler`, `public/brand`, `ui/brand`, `Neon Sign`, and generated artifacts

## Recommended next lane

`01 Repo Steward` for exact-path commit, then `12 Self-Hosted Deployment` for authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Autopilot exact-path approval, commit only the five safe-to-stage paths, restart the protected preview from the exact commit, and verify the score visually at desktop and narrow widths.
