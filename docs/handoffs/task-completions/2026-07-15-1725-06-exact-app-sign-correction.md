# Lane 06 — Exact app sign correction

## Task summary

Corrected the mistaken prior asset selection on the public landing. `www` now uses the user-supplied screenshot of the correct `app.steelguitarrag.com` sign as the visual source of truth. The photographed page background was removed while retaining the supplied sign pixels, proportions, lettering, glow, wall bracket, arm, chains, and framing. The resulting static alpha PNG avoids both the wrong fallback artwork and the iPhone video/compositing box.

The attempted generative background extraction was rejected because it changed the sign design and was not added to the repository. Intentionally unchanged: interest capture/D1, page copy, workspace previews, protected app files/runtime, auth, DNS, Access, schema, and secrets.

## Lane classification

- Primary lane: 06 UX/UI Design
- Task mode: Autopilot user-smoke correction

## Files changed

- `ui/brand/steel-guitar-rag-app-sign-reference.png`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/brand/steel-guitar-rag-app-sign-reference.png`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — PASS, 50 tests
- `node --check ui/landing-home.js` — PASS
- `node --check ui/pedal-steel-fretboard.js` — PASS
- Inline landing JavaScript parse with `vm.Script` — PASS
- Source/deploy HTML byte comparison — PASS
- Source/deploy exact sign asset byte comparison — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/?v=exact-sign-local`
- Cache-busted URL tested: `http://127.0.0.1:8772/?v=exact-sign-local`
- Exact URL the user should use: pending committed production promotion
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit working tree based on `66ff41c`
- Version endpoint: not applicable to local static Pages output
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: exact source/deploy byte checks and inspected live DOM dimensions/path
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not part of the public artifact
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: only on the protected app origin
- Who should test this URL: Codex
- Do not test these URLs: public feature routes; all workspaces remain locked/static
- Known caveats: production Pages browser smoke is required after commit promotion

## Browser result

PASS at 393×852. The exact-reference asset reports native 259×168 dimensions and renders at 259×168, x=0, y=0. Visual inspection shows the requested warm-orange script sign and full hanging bracket without a rectangular background, alternative fallback styling, red/yellow contour bands, or black video box. Horizontal overflow is zero and browser warnings/errors are empty.

## Risk assessment

Low. The correction replaces only the public sign asset/reference and sizing. Rollback is the scoped commit or prior Pages deployment.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/brand/steel-guitar-rag-app-sign-reference.png`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/brand/steel-guitar-rag-app-sign-reference.png`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1725-06-exact-app-sign-correction.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing parked Lane 12 handoffs
- Generated-image scratch output outside the workspace
- Any `.wrangler`, corpus, private-data, vector, auth, DNS, or secret files

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 public Pages promotion and production browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the six exact files above, deploy only `deploy/landing` to the existing Pages production branch, and visually verify the cache-busted `www` URL at 393×852 before user handoff.
