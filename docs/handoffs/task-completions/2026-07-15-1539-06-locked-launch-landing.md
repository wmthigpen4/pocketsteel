# Conversion-Focused Locked Launch Landing

## Task summary

Replaced the long, app-like unpublished public landing concept with a shorter product-led launch page. The page puts an email-only `Get launch invite` form above the fold, shows four realistic static workspace previews marked `Coming at launch`, and states explicitly that no account or app access is created.

Updated the existing interest endpoint so a valid email-only submission is classified `new` rather than `review`. Legacy optional fields, response shape, D1 storage, IP hashing, spam/test rules, and the weekly digest remain compatible.

Intentionally unchanged: protected app, live answer APIs, Cloudflare Access policy, DNS, Tunnel, auth, payment, corpus/vector data, schema, secrets, and app runtime.

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `functions/api/interest.js`
- `tests/test_public_landing_page.py`
- `docs/cloudflare-pages-landing.md`
- This handoff

No files were deleted and no new visual assets or generated artifacts were added.

## Tests and checks

- Source/deploy HTML byte comparison — passed.
- Inline landing script parsing with `vm.Script` — passed; 1 inline script parsed.
- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — 45 passed.
- Public forbidden-string scan for private app/RAG/runtime references — clean.
- `git diff --check` — passed.
- Wrangler availability — `4.111.0`.
- Local desktop browser at 1440×1000 — visual pass; email form was above the fold, page/card horizontal overflow was zero, only the email field could collect data, and browser warning/error count was zero.
- Local narrow browser at 520×1125 — visual pass; form was above the fold, workspace grid collapsed to one 496px column, and page/card horizontal overflow was zero.
- Final CTA focused the single email field — passed.
- Static-server form failure state — passed; retained email, restored submit button, and announced `We couldn’t save your email. Please try again.` through the live status region.
- Production success state — pending Pages deployment and one test-classified submission.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8771/ui/steel-guitar-rag-landing.html?v=locked-landing-local-20260715`
- Cache-busted URL tested: desktop URL above; narrow used `?v=locked-landing-narrow-20260715`
- Exact URL the user should use: pending Pages deployment
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: static loopback server at `http://127.0.0.1:8771`
- Expected backend port: 8771
- Expected git HEAD: pre-commit working tree based on `7fe879f`
- Version endpoint: not available for static landing
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: inspected working-tree source/deploy hashes
- Whether app root `/` works: not applicable to the static loopback smoke
- Whether app root `/` is expected to work: no for this local static server
- Whether `/ui/steel-guitar-rag-mock.html` works: out of scope; protected app was not modified
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: unchanged
- Who should test this URL: Codex
- Do not test these URLs: local loopback as proof of Pages deployment or Cloudflare Access behavior
- Known caveats: production Pages and interest/D1 smoke remain required after exact-path commit

## Integration notes

The Pages deploy directory remains a static public boundary. It contains no link or call to the protected app, `/api/answer`, Ollama, Chroma, private source material, or runtime code. The form submits only `{email}` to the existing same-origin `/api/interest`; older clients may still send the optional legacy fields.

The public name remains `Steel Guitar RAG`. The existing logo/background assets are reused without modifying protected brand/design paths.

## Risk assessment

Low for code and local behavior; medium until production Pages, D1 capture, root/`www`, and anonymous Access challenge are verified. Rollback is promotion of the previous Pages deployment. No database rollback is needed.

## Human decision needed

No. The user explicitly approved the Pages-only deployment and locked-access scope.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `functions/api/interest.js`
- `tests/test_public_landing_page.py`
- `docs/cloudflare-pages-landing.md`
- `docs/handoffs/task-completions/2026-07-15-1539-06-locked-launch-landing.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-15-1435-12-origin-recovery-final.md`
- `docs/handoffs/task-completions/2026-07-15-1517-12-qa-cta-promotion-blocker.md`
- All protected app, auth, DNS, Tunnel, secret, corpus/vector, private, generated, public/brand, and unrelated files

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 deploy only `deploy/landing` to the existing Pages project and run production landing/interest/Access smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the six listed files, deploy the committed `deploy/landing` directory to `steel-guitar-rag-landing`, verify root and `www`, submit one test-classified email, confirm D1 capture, and verify the protected app still challenges anonymous users.
