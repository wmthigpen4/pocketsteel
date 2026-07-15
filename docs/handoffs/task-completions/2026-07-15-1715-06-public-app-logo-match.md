# Lane 06 — Public landing app-logo match

## Task summary

Corrected the public `www` landing page to use the exact static hanging-sign asset used by the protected app on mobile: `ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`. The public mobile presentation now also matches the app's 190–240px responsive sizing while keeping the physical bracket visible at the left viewport edge. The static PNG path remains in place to avoid the previously reported iPhone alpha-video compositing failure.

Intentionally unchanged: copy, interest capture and D1 behavior, workspace previews, protected app assets/code, auth, DNS, Access policy, database schema, and secrets.

## Lane classification

- Primary lane: 06 UX/UI Design
- Task mode: Autopilot user-smoke correction

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html` (byte-identical deployment output)
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png` (exact copy of the app asset)
- `tests/test_public_landing_page.py`
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — PASS, 50 tests
- `node --check ui/landing-home.js` — PASS
- `node --check ui/pedal-steel-fretboard.js` — PASS
- Inline landing JavaScript parsed with `vm.Script` — PASS
- Source/deploy HTML byte comparison — PASS
- Source/deploy sign asset byte comparison — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/?v=app-logo-local`
- Cache-busted URL tested: `http://127.0.0.1:8772/?v=app-logo-local`
- Exact URL the user should use: pending committed production deployment
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit working tree based on `17e84db`
- Version endpoint: not applicable to static local Pages output
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: exact source/deploy byte checks and inspected DOM asset path/dimensions
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not part of this public static artifact
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: only on the protected app origin
- Who should test this URL: Codex
- Do not test these URLs: public feature routes; workspaces remain static and locked
- Known caveats: production Pages smoke is required after exact commit promotion

## Browser result

PASS at 393×852. The DOM loads `brand/steel-guitar-rag-hanging-sign-cloudflare-login.png` at its native 400×287 dimensions; it renders at 216×155, x=0, y=8 with the wall bracket visible. No sign video is present, horizontal overflow is zero, and browser warning/error logs are empty. Visual comparison matches the supplied app-logo reference.

## Risk assessment

Low. This reuses an existing reviewed app asset and changes only the public header's asset reference and narrow-screen sizing. Rollback is the scoped commit or prior Pages deployment.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1715-06-public-app-logo-match.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing parked Lane 12 handoffs
- Any `.wrangler`, corpus, private-data, vector, auth, DNS, or secret files

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 promotion of only `deploy/landing` and production browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage the exact five files above, commit the logo correction, deploy that commit to the existing production Pages branch, and verify the cache-busted `www` URL at 393×852.
