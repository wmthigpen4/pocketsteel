# Lane 06 — Mobile Safari landing repair

## Task summary

Fixed the two production-root mobile presentation failures reported during user smoke. The hanging sign now uses the clean high-resolution anchored PNG instead of the alpha WebM that produced a black rectangle and red/yellow compositing artifacts in iPhone Safari. Mobile workspace cards now size to their content, and Melody Studio receives a larger full-width staff preview with a restrained purple treatment. The touch-sticky skip-link state was also limited to keyboard-visible focus.

Intentionally unchanged: interest-form behavior and D1 capture, public copy, protected app behavior, Cloudflare Access, DNS, auth, database schema, secrets, and the protected app deployment.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment
- Task mode: approved Autopilot user-smoke bug fix

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html` (byte-identical deployment output)
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-fallback.png`
- `tests/test_public_landing_page.py`
- This handoff

No files were deleted.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — PASS, 50 tests
- `node --check ui/landing-home.js` — PASS
- `node --check ui/pedal-steel-fretboard.js` — PASS
- Inline landing-page JavaScript parsed with `vm.Script` — PASS
- `cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html` — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/?v=mobile-repair-local`
- Cache-busted URL tested: `http://127.0.0.1:8772/?v=mobile-repair-local`
- Exact URL the user should use: pending exact committed production deployment
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit working tree based on `227063e691dbade948b0585580c8885ef8c9ec0c`
- Version endpoint: not applicable to static local Pages output
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: source/deploy byte identity and cache-busted local URL
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not part of the public Pages artifact
- Who should test this URL: Codex
- Do not test these URLs: protected app feature routes as proof of this public landing fix
- Known caveats: local browser smoke does not prove iOS Safari or production deployment; production smoke is required after promotion

### Browser result

PASS at 393×852 and 857×874. At phone size, the sign loaded as the 1448×1086 clean anchored PNG, no video element remained, there was no horizontal overflow, and console warnings/errors were empty. Melody Studio rendered at 298px card height with a 126px full-width preview and a 16px preview-to-lock gap. Visual inspection confirmed the clean sign, preserved wall anchor, readable enlarged staff, and removal of excessive card whitespace. Desktop layout remained left-anchored and overflow-free.

## Integration notes

This is a static public Pages change only. The exact committed `deploy/landing` artifact should be promoted to the existing `steel-guitar-rag-landing` Pages project. Do not deploy or restart the protected app.

## Risk assessment

Low. The change removes a browser-sensitive alpha video from the public header and adjusts only mobile presentation rules. Rollback is the single scoped implementation commit or restoration of the previous Pages deployment.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-fallback.png`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1704-06-mobile-safari-landing-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing untracked Lane 12 coordination handoffs not listed above
- Any corpus, private-data, vector-store, `.wrangler`, auth, DNS, or secret files

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 production Pages promotion and browser smoke at 393×852.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the five exact files above, commit the scoped mobile repair, deploy that commit's `deploy/landing` directory to the existing Pages production branch, and verify a cache-busted `www.steelguitarrag.com` URL without submitting the interest form.
