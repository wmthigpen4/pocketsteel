# Real landing score preview

## Task summary

Replaced the hand-drawn Melody Studio card illustration with a compact, non-interactive score rendered by the same VexFlow-based notation system used by Melody Studio.

The preview contains a treble clef, 4/4 time signature, and six notes with rhythm values totaling exactly four beats. Stems, noteheads, ledger behavior, spacing, and beams are produced by VexFlow rather than custom SVG artwork.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lane: `15 QA / Answer Eval`
- Mode: Autopilot user-smoke adjustment

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/landing-home.js`
- `ui/melody-score.js`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

No binary assets, backend, auth, corpus, deployment configuration, or Melody Studio workflow behavior changed.

## Tests and checks

- Four JavaScript syntax checks — passed
- Focused landing/frontend/Melody/fretboard suite — `99 passed in 2.96s`
- Full Python suite — `1036 passed in 45.76s`
- Scoped `git diff --check` — passed
- Local browser smoke — passed

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=real-score-local-4`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree based on `3f8bf0c1dac98945a051018ce2cd616051fe3481`
- Version endpoint: not used for working-tree smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted static files served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached landing URLs
- Known caveats: browser automation verified rendered SVG structure and computed styling rather than relying on a screenshot-only assertion.

Browser assertions:

- `data-score-renderer="vexflow-preview"` present.
- Six VexFlow stave-note groups rendered.
- Treble clef and 4/4 time signature rendered through VexFlow.
- Note vertical positions remain inside the compact preview.
- Note fill and staff stroke compute to the approved cream treatment.
- Preview adds zero tab stops.
- Document overflow remains zero.

## Integration notes

The landing now loads the existing pinned VexFlow vendor bundle and `melody-score.js`. `renderPreview` is a small public helper on `STEEL_RAG_MELODY_SCORE`; the full Melody Studio renderer and draft contract are unchanged.

## Risk assessment

Low. The main cost is loading the existing VexFlow bundle on the landing page. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/landing-home.js`
- `ui/melody-score.js`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-2005-06-real-landing-score-preview.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing dirty landing-alpha assets
- All unrelated dirty/untracked brand, public, Neon Sign, corpus, source-inbox, backend, auth, Cloudflare, vector, embedding, private-data, and deployment paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the seven exact paths, restart the protected preview, and verify the real notation at the cache-busted user-smoke URL.
