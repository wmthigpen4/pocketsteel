# Lane 06 — Mobile/desktop logo media parity

## Task summary

Corrected the mobile-only old-logo behavior while preserving the locked shared alignment contract. Both app and public markup now offer the same sign animation in two transparent formats: HEVC-with-alpha (`hvc1`) first for Safari and the existing VP9 WebM second for Chrome/Firefox. The old mobile fallback was replaced with an exact transparent still decoded from the same app animation. Normal mobile users receive animation; reduced-motion users receive the matching still.

No sign geometry, header positioning, dimensions, shadow, copy, interest capture, D1, auth, Access, DNS, schema, or secrets were changed.

## Files changed

- `ui/brand/steel-guitar-rag-hanging-sign-mobile-alpha.mov` — 800×600, five-second HEVC alpha animation for Safari
- `ui/brand/steel-guitar-rag-hanging-sign-poster.png` — 800×600 transparent still from the same animation
- `ui/hero-hanging-sign.css` — mobile/touch uses animation; reduced-motion alone forces fallback
- `ui/steel-guitar-rag-mock.html`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-mobile-alpha.mov`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-poster.png`
- `deploy/landing/hero-hanging-sign.css`
- `deploy/landing/index.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_public_landing_page.py`
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py tests/test_frontend_answer_ui.py` — PASS, 100 tests
- JavaScript syntax/parsing for app and public landing — PASS
- Source/deploy HTML, CSS, MOV, and PNG byte identity — PASS
- `ffprobe` — PASS: `hevc`, `hvc1`, 800×600, 5.0 seconds, 1,550,801 bytes
- Decoded HEVC frame — PASS: RGBA with fully transparent corners
- Poster validation — PASS: 800×600 RGBA with fully transparent corners
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/steel-guitar-rag-landing.html?v=mobile-media-parity-local`
- Cache-busted URL tested: same
- Exact URL the user should use: pending production promotion
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: 8772
- Expected git HEAD: pre-commit working tree based on `cd167ae`
- Version endpoint: not applicable
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: exact media paths, current source selection, native dimensions, file codec/alpha validation
- Whether app root `/` works: direct local public HTML works
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: tested locally under the `ui` document root in focused parity smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes behind Access
- Who should test this URL: Codex
- Do not test these URLs: public feature/API routes as proof of media parity
- Known caveats: Chromium cannot decode Apple's HEVC-alpha source and correctly falls through to WebM; Safari selection is validated through source ordering plus codec/alpha inspection, with native Safari user smoke remaining the final device boundary

## Browser result

PASS. At a narrow browser viewport, the sign remains animated and aligned: `is-animated` is present, video is displayed/ready/playing, fallback is hidden, Chrome selects the 1600×1200 WebM source, and horizontal overflow is zero. The source list places `hvc1` first for Safari. Browser warning/error logs are empty.

## Risk assessment

Low to medium. The visual source is unchanged and alignment is untouched. The new Safari media format is platform-native and alpha-validated, but final iPhone Safari playback remains a user-smoke boundary. Rollback is the scoped commit or previous Pages deployment.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/brand/steel-guitar-rag-hanging-sign-mobile-alpha.mov`
- `ui/brand/steel-guitar-rag-hanging-sign-poster.png`
- `ui/hero-hanging-sign.css`
- `ui/steel-guitar-rag-mock.html`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-mobile-alpha.mov`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-poster.png`
- `deploy/landing/hero-hanging-sign.css`
- `deploy/landing/index.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-16-0849-06-mobile-desktop-logo-media-parity.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing parked handoffs including unrelated Lane 20/51 work
- `.wrangler`, corpus, private-data, vectors, auth, DNS, and secret files

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 public Pages promotion and protected app release update if the documented detached-release workflow is clean.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above, promote the public Pages artifact, verify live source selection and reduced-motion fallback, then perform native iPhone Safari smoke.
