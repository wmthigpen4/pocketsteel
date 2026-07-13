# Simplify landing navigation

## Task summary

Removed the duplicate Fretboard Explorer and Melody Studio buttons from the landing hero. Hid the header navigation while the landing overview is active, leaving the four product cards as the single feature-navigation layer and the lower Backstage strip as the single visible landing-page Backstage entry.

Preserved the header navigation in answer mode, the four product cards and functional Ask card, the Backstage dialog, and the upper-left hanging sign.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Task mode: YELLOW landing-flow adjustment explicitly approved through user-smoke feedback.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1824-06-simplify-landing-navigation.md`

No workspace interior, shared renderer, asset, backend, auth, corpus, Cloudflare, or deployment configuration changed.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- Focused frontend/fretboard suite — `94 passed in 2.91s`.
- Full Python suite — `1035 passed in 47.78s`.
- Scoped `git diff --check` — passed.
- Local desktop and narrow-screen browser smoke — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=landing-navigation-local-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree on `07a3ee650b4426a48a8720e2496d658a8d31fd7c`
- Version endpoint: not used for local visual smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted assets served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached preview URLs or the public marketing page
- Known caveats: the responsive override reported a 487-pixel effective browser viewport when a 390-pixel override was requested; it still exercised the below-700-pixel layout.

Browser assertions:

- Landing header navigation computed to `display:none`.
- Hero action container was absent.
- Exactly one Backstage trigger was visible.
- Product-card destinations remained visible.
- Hanging sign stayed at the far-left edge and retained its 350-pixel desktop and 290-pixel narrow sizing.
- Desktop and narrow layouts had zero document overflow.

## Integration notes

The header navigation remains in the DOM for answer-mode use and is hidden only under `.page:not(.is-answering)`. This avoids changing the answer transition and session-aware link behavior.

The landing shell stylesheet cache key is `landing-navigation-20260713-1`.

## Risk assessment

Low. The change removes one landing-only button group and adds one state-scoped display rule. Rollback is the single scoped commit.

## Human decision needed

No. The user explicitly requested one landing navigation layer and one landing Backstage entry.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1824-06-simplify-landing-navigation.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unstaged handoffs from earlier tasks.
- Dirty/unrelated `ui/brand/`, `public/`, `Neon Sign/`, corpus, source-inbox, backend, auth, Cloudflare, vector, embedding, private-data, and deployment paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the five exact paths, update the protected preview, and verify the landing and answer-mode navigation states.
