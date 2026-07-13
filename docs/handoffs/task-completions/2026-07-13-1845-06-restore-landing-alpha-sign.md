# Restore landing-alpha hanging sign

## Task summary

Restored the landing sign artwork used immediately before commit `f9d5c39` while preserving the current upper-left placement and responsive sizing.

The app now references:

- Desktop animation: `ui/brand/steel-guitar-rag-landing-alpha.webm`
- Poster/mobile fallback: `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`

`public/brand/steel-guitar-rag-landing-alpha-master.mov` is the source master; the WebM remains the browser delivery format.

No positioning, sizing, header spacing, answer badge, or workspace-card behavior changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lane: `19 Visual Design / Assets`
- Task mode: protected brand-path change explicitly approved by the user's named asset request.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1845-06-restore-landing-alpha-sign.md`

The existing dirty `ui/brand/steel-guitar-rag-landing-alpha.webm` and `ui/brand/steel-guitar-rag-landing-fallback-alpha.png` files were inspected but not modified or staged. No binary asset was added to this slice.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- Focused frontend/fretboard suite — `95 passed in 3.03s`.
- Full Python suite — `1036 passed in 49.27s`.
- Scoped `git diff --check` — passed.
- Local desktop and mobile-breakpoint browser smoke — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=landing-alpha-return-local-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree on `b9d51748d3b050a356464887ba26b5d902ec090e`
- Version endpoint: not used for local visual smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted HTML served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached sign URLs or the public marketing page
- Known caveats: the responsive override reported a 487-pixel effective width when 390 pixels was requested; it exercised the below-520-pixel fallback rule.

Browser assertions:

- Desktop loaded `steel-guitar-rag-landing-alpha.webm` at 1600×1200 with ready state 4.
- Desktop sign remained absolutely positioned at the far-left edge, 350 pixels wide.
- Mobile-breakpoint video was hidden and `steel-guitar-rag-landing-fallback-alpha.png` displayed at 290 pixels wide.
- Desktop and mobile-breakpoint layouts had zero document overflow.

## Integration notes

This is a reference-only restoration. The current layout rules from `f9d5c39` and later commits remain in place. The old `steel-guitar-rag-hanging-sign.*` files remain tracked but are no longer referenced by the landing header.

The asset cache key is `landing-alpha-return-20260713`.

## Risk assessment

Low. Only the landing media references and their tests changed. Rollback is the single scoped commit.

## Human decision needed

No. The user explicitly selected the pre-`f9d5c39` landing-alpha artwork while approving the current location.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1845-06-restore-landing-alpha-sign.md`

## Files that must not be staged

- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `docs/handoffs/task-completions/integration-status.md`
- Earlier unstaged coordination handoffs.
- All other unrelated dirty/untracked brand, public, Neon Sign, corpus, source-inbox, backend, auth, Cloudflare, vector, embedding, private-data, and deployment paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated desktop/mobile browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the four exact text paths, update the protected preview, and verify the landing-alpha artwork without staging either dirty brand asset.
