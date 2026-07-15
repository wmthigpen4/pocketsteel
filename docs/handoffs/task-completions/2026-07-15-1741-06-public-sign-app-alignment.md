# Lane 06 — Public sign app alignment

## Task summary

Aligned the exact-reference public hanging sign with the protected app's actual positioning contract. Copied the app's desktop header width, sign offsets, responsive widths, rotation, transform origin, pointer behavior, object positioning, image rendering, shadow stack, and 640px/520px breakpoints. The sign artwork itself was not changed.

Intentionally unchanged: landing copy, form/D1 behavior, workspace previews, protected app code/runtime, auth, Access, DNS, schema, and secrets.

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html` (byte-identical output)
- `tests/test_public_landing_page.py`
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — PASS, 50 tests
- `node --check ui/landing-home.js` — PASS
- `node --check ui/pedal-steel-fretboard.js` — PASS
- Source/deploy HTML comparison — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/?v=app-alignment-local`
- Cache-busted URL tested: `http://127.0.0.1:8772/?v=app-alignment-local`
- Exact URL the user should use: pending committed production promotion
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit working tree based on `27f5e98`
- Version endpoint: not applicable
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: source/deploy identity and computed-style inspection
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not part of the public artifact
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: protected origin only
- Who should test this URL: Codex
- Do not test these URLs: public feature routes
- Known caveats: production smoke required after promotion

## Browser result

PASS at 1430×900 and 393×852. Desktop computed values match the app contract: header x=155/width=1120, sign `left=-18px`, `top=-42px`, CSS width 328.891px, transform origin 0/0, and −1.5° rotation. Phone computed values match the app mobile rules: header x=14/width=365, rotated sign x≈−4/y≈2 with the 190–240px rule. Both viewports have zero horizontal overflow and clean browser logs.

## Risk assessment

Low. Alignment-only CSS change. Rollback is the scoped commit or previous Pages release.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1741-06-public-sign-app-alignment.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing parked Lane 12 handoffs
- Any `.wrangler`, corpus, private-data, vector, auth, DNS, or secret files

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 public Pages deployment and production browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the four exact files above, deploy only `deploy/landing`, and verify the computed production layout at desktop and phone widths.
