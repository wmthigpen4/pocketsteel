# Landing non-SVG previews

## Task summary

Replaced the two broken landing-card SVG previews shown in user smoke. The miniature Fretboard Explorer card is now ordinary HTML/CSS whose colored grips and vertical fret lines share the same anchors. The Melody Studio card now uses VexFlow's Canvas backend on one proportional 300×86 logical surface. The full interactive Fretboard Explorer and Melody Studio renderers were intentionally not changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Exact-path commit: `01 Repo Steward`
- Protected-preview verification: `12 Self-Hosted Deployment`
- Task mode: approved Autopilot UI fix

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/melody-score.js`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

No backend, API, dependency, full-app renderer, auth, corpus, Chroma, private data, brand asset, or deployment configuration changed.

## Tests and checks

- Four JavaScript syntax checks — passed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 52 passed.
- `.venv/bin/python -m pytest -q` — 1,099 passed.
- Scoped `git diff --check` — passed.
- Local browser smoke at desktop and narrow widths — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?v=landing-preview-canvas-local-final`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree based on `b7f82359dc3daa506f8c00a7f8e71193825b8a0f`
- Version endpoint: not available on the static local smoke server
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted assets served directly from the scoped working tree
- Whether app root `/` works: static directory listing only; not the application root
- Whether app root `/` is expected to work: no for this static-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached landing URLs or the local static server after it is stopped
- Known caveats: the browser automation surface exposed device pixel ratio `0.8`; zoom stability is enforced structurally and verified at desktop and narrow widths, with protected user smoke still required.

## Browser results

- Both preview containers had zero SVG descendants.
- Fretboard rendered 11 shared fret anchors and 9 colored dots.
- Maximum measured dot-center/fret-line-center delta was `0.009765625` CSS pixel at desktop and narrow widths.
- Score reported `data-score-renderer="vexflow-canvas-preview"` and exactly one Canvas.
- Canvas retained the 300:86 logical aspect ratio, fit inside its card at both widths, and used the browser-scaled backing store.
- Visual inspection confirmed attached noteheads, stems, and two eighth-note beams.
- Document overflow was zero and the final clean load logged zero browser warnings/errors.

## Integration notes

The landing-only `renderPreview(container)` signature and boolean return contract are unchanged. Its diagnostic renderer value changed from `vexflow-preview` to `vexflow-canvas-preview`. Canvas failures now return `false`, allowing the existing unavailable message instead of falling back to SVG.

The same-origin smoke assertion for the already-current monthly-usage answer-client cache key was refreshed while updating the landing asset assertions; no account behavior changed.

## Risk assessment

Low. The replacement is limited to two static landing previews. Rollback is the scoped commit. The full interactive tools retain their existing renderers.

## Human decision needed

No. User visual confirmation at the final protected-preview URL is the remaining acceptance step.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/melody-score.js`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1313-06-landing-non-svg-previews.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty or untracked corpus, source-inbox, private-data, brand, `public/`, `Neon Sign/`, deployment, auth, vector, embedding, generated-report, and historical-handoff paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the six exact paths, restart the isolated protected preview at that commit, and verify both previews at a new cache-busted authenticated URL.
