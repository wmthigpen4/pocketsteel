# Lane 06 — Shared hero-sign parity fix

## Task summary

Fixed the recurring app/www hero-logo mismatch at its source. Both pages now load `hero-hanging-sign.css` last, after their existing styles, so the logo/header contract has one final authority. Removed the public page's competing sign geometry and responsive fallback rules. The public invite form, public copy, locked previews, and protected app behavior remain unchanged.

## Files changed

- `ui/hero-hanging-sign.css` — new shared final logo/header contract
- `ui/steel-guitar-rag-mock.html` — loads shared contract after `workspace-shell.css`
- `ui/steel-guitar-rag-landing.html` — loads shared contract last and removes duplicate sign rules
- `deploy/landing/hero-hanging-sign.css` — byte-identical Pages output
- `deploy/landing/index.html` — byte-identical public HTML output
- `tests/test_public_landing_page.py` — shared-source, ordering, responsive, and deploy parity regression coverage
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py tests/test_frontend_answer_ui.py` — PASS, 100 tests
- `node --check ui/landing-home.js` — PASS
- `node --check ui/pedal-steel-fretboard.js` — PASS
- Inline JavaScript parse for app and public landing — PASS
- Source/deploy HTML and shared-CSS byte identity — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URLs tested:
  - `http://127.0.0.1:8772/steel-guitar-rag-mock.html?v=shared-parity-local`
  - `http://127.0.0.1:8772/steel-guitar-rag-landing.html?v=shared-parity-local`
- Cache-busted URLs tested: same
- Exact URL the user should use: pending production promotion
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit working tree based on `3d20f51`
- Version endpoint: not applicable to static local smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: source/deploy byte identity plus computed-style equality
- Whether app root `/` works: both direct local HTML routes work
- Whether app root `/` is expected to work: yes for the tested static routes
- Whether `/ui/steel-guitar-rag-mock.html` works: tested as `/steel-guitar-rag-mock.html` under the local `ui` document root
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes on the protected origin
- Who should test this URL: Codex
- Do not test these URLs: public feature/API routes as proof of logo parity
- Known caveats: app and public header contents intentionally differ, so total narrow-header height may differ; logo/header geometry is identical

## Browser result

PASS. App and public pages were loaded sequentially from the same local origin in the same tab and viewport. Desktop computed objects were byte-for-byte equal for viewport, header box/grid/min-height/padding, sign box/top/left/width/transform/filter/pointer behavior, video/fallback state and native dimensions, and shared stylesheet URL. Both used the 1600×1200 playing video and the same 350px final sign width. Narrow smoke confirmed identical sign/header geometry and zero browser warnings/errors; only total header height differed because the app and public header actions contain different content.

## Integration notes

The shared stylesheet is deliberately narrow: it owns only final header width, hero-sign geometry/media presentation, responsive sign positioning, and video fallback behavior. It does not import the full protected `workspace-shell.css` into the public site.

## Risk assessment

Low. The app's shared rules reproduce its existing final `workspace-shell.css` values, so protected app appearance should not change. The public site changes from its divergent copied rules to the app's existing final contract. Rollback is the scoped commit or previous Pages deployment.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/hero-hanging-sign.css`
- `ui/steel-guitar-rag-mock.html`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/hero-hanging-sign.css`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-16-0823-06-shared-hero-sign-parity-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing parked deployment/coordination handoffs
- Any `.wrangler`, corpus, private-data, vector, auth, DNS, or secret files

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 public Pages promotion and production computed-style/browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the seven exact files above, deploy only `deploy/landing`, and verify live public computed values against the authenticated app at desktop and narrow widths.
