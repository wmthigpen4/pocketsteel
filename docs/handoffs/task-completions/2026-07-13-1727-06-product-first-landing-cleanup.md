# Lane 06 Product-First Landing Cleanup

## Task summary

- Implemented the approved product-first app landing page as a connected four-workspace hub.
- Replaced only the home-state presentation in `ui/steel-guitar-rag-mock.html`; preserved the existing answer renderer, answer request path, session/access behavior, Backstage content, root redirect, and destination routes.
- Added a semantic shell with skip link, primary navigation, product-positioning hero, real validated Explorer preview, four workspace cards, neutral Backstage strip, and evidence-aware trust footer.
- Kept Chord Studio within Explorer and did not add a fifth major workspace.
- Removed the unsupported voice control from the home Ask card while preserving the existing follow-up answer control.
- Added Backstage focus containment, Escape close, and exact-trigger focus restoration.
- Locked the hanging sign to the upper-left edge of the shared header at desktop, tablet, and mobile breakpoints. It is never centered.
- Intentionally did not change workspace interiors, the public marketing landing page, backend/API behavior, auth, Cloudflare policy, corpus, embeddings, source policy, deployment configuration, or protected/dirty brand assets.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting verification: `15 QA / Answer Eval`
- Task mode: YELLOW UI-flow change, explicitly approved for Autopilot implementation by the user.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css` (new)
- `ui/landing-home.js` (new)
- `tests/test_landing_home_ui.py` (new)
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_smoke.py`
- `tests/test_lesson_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1727-06-product-first-landing-cleanup.md` (new)

No files were deleted. No design assets were generated or copied into the repository.

## Tests and checks

- `node --check ui/landing-home.js` — pass
- `node --check ui/answer-client.js` — pass
- `node --check ui/pedal-steel-fretboard.js` — pass
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py tests/test_smoke.py tests/test_pedal_steel_fretboard_ui.py tests/test_lesson_workbench_ui.py` — pass, `97 passed`
- `.venv/bin/python -m pytest -q` — pass, `1035 passed in 47.86s`
- Scoped `git diff --check` — pass

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=product-first-landing-local-20260713-3`
- Cache-busted URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=product-first-landing-local-20260713-3`
- Exact URL the user should use: protected-preview URL to be recorded after restart
- Auth required: no for local controlled-state smoke
- Auth provider: local development controlled state
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: `8897`
- Expected git HEAD: `28d6532260a4195eece2356ada51af867b4aa973` before implementation commit
- Version endpoint: `http://127.0.0.1:8897/api/version`
- Version endpoint result: `28d6532`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, same-origin server root behavior is covered by passing tests
- Whether app root `/` is expected to work: yes, redirects to the app shell
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; the user after protected-preview restart
- Do not test these URLs: public marketing landing page was outside scope
- Known caveats: the in-app browser enforces an approximately 333 CSS-pixel minimum viewport; the 320-pixel contract is additionally covered by CSS/static regression checks.

Browser result:

- PASS at the desktop, tablet, and mobile layout regimes representing 1440, 1024, 768, 390, and the browser minimum nearest 320 pixels.
- Document `scrollWidth` matched `clientWidth` at every observed breakpoint.
- Explorer preview rendered one real `PedalSteelFretboard` using the validated G-major demo positions.
- Narrow preview overflow stayed inside `.home-explorer-stage`.
- Four product cards and all primary navigation destinations remained visible.
- Short navigation labels appeared on narrow screens.
- The hanging sign's left edge matched the header's left edge at every measured breakpoint; it was not centered.
- All measured landing and header interactive targets were at least 44 pixels tall at the 390-pixel layout.
- Compact Ask submission entered answer mode, marked Ask current, rendered the answer workspace, and returned cleanly home.
- Backstage contained keyboard focus, closed with Escape, and restored focus to the trigger used to open it.
- No browser console errors or warnings were observed.
- No `[object Object]` output was present.

## Integration notes

- `ui/workspace-shell.css` supplies reusable shell tokens and primitives while scoping the new landing layout under `home-*` classes.
- `ui/landing-home.js` exposes `STEEL_RAG_LANDING.mountExplorerPreview(container, fretboardApi)` and fails gracefully when the renderer is unavailable.
- No public API, schema, backend, source, auth, or data contract changed.
- The existing dirty `ui/brand/steel-guitar-rag-landing-alpha.webm` and `ui/brand/steel-guitar-rag-landing-fallback-alpha.png` are referenced but were not modified by this task and must remain unstaged.

## Risk assessment

- Risk: low to medium.
- Reason: the app home is user-facing and shares a large HTML file with the answer workspace, but the implementation isolates home presentation, retains existing IDs/contracts, passes the full suite, and passes local browser smoke.
- Rollback: revert the scoped landing commit. No data or schema rollback is required.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/landing-home.js`
- `tests/test_landing_home_ui.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_smoke.py`
- `tests/test_lesson_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1727-06-product-first-landing-cleanup.md`

## Files that must not be staged

- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `docs/handoffs/task-completions/integration-status.md`
- All other pre-existing modified or untracked paths outside the safe-to-stage list, including corpus, source-inbox, design, deployment, auth, backend, and generated artifacts.

## Recommended next lane

- `01 Repo Steward` for exact-path staging and the scoped UI commit, followed by `12 Self-Hosted Deployment` for the documented protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Autopilot/Repo Steward auto-approval: stage only the exact safe file list, review the cached diff, commit the product-first landing cleanup, restart the documented protected preview, and run authenticated protected browser smoke at a new cache-busted URL.
