# Lane 06 — Exact app hero-logo implementation

## Task summary

Replaced the public screenshot-derived single image with the protected app's exact hero-logo implementation: identical video and fallback assets, markup classes, activation/failure behavior, reduced-motion handling, phone fallback breakpoint, positioning, rotation, and shadow. Desktop now uses the crisp 1600×1200 animated source; phones at 520px and below use the app's 400×287 static fallback.

No form, D1, feature, protected runtime, auth, Access, DNS, schema, or secret behavior changed.

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `deploy/landing/brand/steel-guitar-rag-landing-alpha.webm`
- `tests/test_public_landing_page.py`
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — PASS, 50 tests
- JavaScript syntax/parsing — PASS
- Source/deploy HTML and sign assets byte checks — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/?v=exact-app-hero-local`
- Cache-busted URL tested: same
- Exact URL the user should use: pending production promotion
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit based on `d4b300b`
- Version endpoint: not applicable
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: DOM media state and exact asset paths/dimensions
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: protected origin only
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes behind Access
- Who should test this URL: Codex
- Do not test these URLs: public feature routes
- Known caveats: production smoke required

## Browser result

PASS. At 1430×900, `is-animated` is active, the 1600×1200 video is ready/playing/displayed, and the fallback is hidden. At 393×852, the video is hidden and the native 400×287 fallback is displayed, exactly matching the app's mobile CSS. Both retain app alignment, zero overflow, and clean logs.

## Risk assessment

Low. Exact reuse of reviewed app media behavior. Rollback is the scoped commit or prior Pages release.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `deploy/landing/brand/steel-guitar-rag-landing-alpha.webm`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1831-06-exact-app-hero-logo-implementation.md`

## Files that must not be staged

- `integration-status.md` and existing parked handoffs
- `.wrangler`, corpus, private data, vectors, auth, DNS, and secrets

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 Pages promotion and desktop/phone production smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the five exact files, deploy only `deploy/landing`, and verify live media state at desktop and phone widths.
