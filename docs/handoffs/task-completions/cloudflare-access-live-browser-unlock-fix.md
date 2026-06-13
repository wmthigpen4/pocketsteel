# Cloudflare Access Live Browser Unlock Follow-Up

## Task summary
- Requested: diagnose and fix why protected preview at committed HEAD `a3103c0` still shows the private beta Q&A gate after Cloudflare Access login, even after the previous fix accepted verified `CF_Authorization` Access cookies.
- Completed: inspected the backend auth/session path, frontend session bootstrap/gate logic, protected unauthenticated Access behavior, and local anonymous behavior. Added a narrow, explicit, non-secret `/api/session?debug=auth` diagnostic object so Lane 12 can determine whether the authenticated protected browser request reaches the origin with an Access header/cookie, verifies identity, and matches the beta/admin allowlist. Normal `/api/session` shape, frontend unlock logic, and `/api/answer` authorization behavior remain unchanged.
- Intentionally not changed: did not weaken production auth, did not make `/api/answer` public, did not trust browser-supplied role/email headers, did not hardcode names or emails, did not expose JWTs/cookies/tokens/secrets, did not change DNS/Cloudflare policy, did not deploy, did not restart protected preview, and did not touch corpus, Chroma, embeddings, scraping, source data, or visual assets.

## Files changed
- Changed files:
  - `docs/api-contract.md`
  - `pocketsteel/access_control.py`
  - `pocketsteel/api.py`
  - `tests/test_api_search.py`
- Created files:
  - `docs/handoffs/task-completions/cloudflare-access-live-browser-unlock-fix.md`
- Deleted files:
  - None.
- Generated artifacts:
  - None.

## Tests and checks
- `git status --short`
  - Result: many pre-existing unrelated modified/untracked files remain parked in the worktree. Scoped runtime/test changes for this task are limited to the files listed above.
- `git diff --check`
  - Result: passed.
- `node --check ui/answer-client.js`
  - Result: passed. No frontend JS changes were needed in this pass.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py -k 'api_session or cloudflare_access or unauthenticated or access_role_contract or answer_smoke_server_auth_config_contract'`
  - Result: passed, `28 passed, 179 deselected`.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -k 'session or gates_live_submission or authoritative_access_state or hides_dev_preview or page_load'`
  - Result: passed, `5 passed, 13 deselected`.
- `.venv/bin/python -m pytest tests/test_api_contract.py`
  - Result: passed, `4 passed`.
- Public unauthenticated protected-preview checks:
  - `curl -sS -I 'https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=user-smoke-a3103c0'`
  - `curl -sS -I 'https://app.steelguitarrag.com/api/session'`
  - Result: both returned Cloudflare Access `302`, confirming unauthenticated public requests are still protected by Access.
- Local anonymous checks:
  - `curl -sS -i http://127.0.0.1:8770/api/session`
  - Result: `200 OK`, anonymous, `authProvider: cloudflare_access`.
  - `curl -sS -i -X POST http://127.0.0.1:8770/api/answer -H 'Content-Type: application/json' --data '{"question":"How do I play a G chord on the E9?"}'`
  - Result: `401 Unauthorized`, `/api/answer requires Cloudflare Access identity`.
- Tests skipped:
  - Full pytest was not run because the requested scope allowed relevant auth/session/frontend/API contract tests only unless shared API paths required the full suite. The previous full-suite state had unrelated failures outside this auth/session slice.
  - Authenticated protected-browser smoke was not completed from this agent session because no authenticated Cloudflare Access browser automation/session was available. API fallback is not a substitute for the requested browser unlock check.

## Smoke Target
```text
Smoke Target:
- Target type: protected-preview
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not browser-tested by this agent session
- Cache-busted URL tested: not browser-tested by this agent session
- Exact URL the user should use: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=user-smoke-a3103c0-auth-fix
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: a3103c0 before this uncommitted diagnostic follow-up
- Version endpoint: /api/version
- Version endpoint result: absent per Lane 12; version inferred from restart/process evidence
- If version endpoint missing, how version is inferred: Lane 12 restart/process evidence for committed HEAD a3103c0; local `git rev-parse --short HEAD` also reported a3103c0 before this uncommitted follow-up
- Whether app root `/` works: not verified in this task
- Whether app root `/` is expected to work: do not assume root works unless Lane 12 verifies it
- Whether `/ui/steel-guitar-rag-mock.html` works: shell previously verified by Lane 12 at HEAD a3103c0; authenticated unlock still needs browser smoke after this diagnostic patch is committed/restarted
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, this is the canonical protected-preview smoke URL for this bug
- Who should test this URL: Lane 12 and the user
- Do not test these URLs: do not shorten this to only https://app.steelguitarrag.com/ because root routing is not the canonical target here
- Known caveats: this pass adds safe live diagnostics; it does not prove the authenticated browser unlock until Lane 12 checks `/api/session?debug=auth` from an authenticated browser after restart
```

## Integration notes
- Lane classification: mixed `11 Auth / Security`, `12 Self-Hosted Deployment`, and `06 UX/UI Design`; primary lane is `11 Auth / Security` because the change is session/auth observability.
- Root cause status: not fully proven from this agent session. Code inspection and existing tests show the frontend unlocks when `/api/session` returns `authenticated: true` with `role: beta_user` or `role: admin`, and the committed frontend already sends `credentials: "same-origin"`. Therefore the live lock is most likely because the authenticated browser request to `/api/session` is returning anonymous, failing, or not receiving/verifying/allowlisting Cloudflare identity at the origin.
- Cookie/header identity reached the origin:
  - Local unauthenticated direct request: no Access identity, as expected.
  - Public unauthenticated curl: blocked by Cloudflare Access before origin, as expected.
  - Authenticated protected browser: unknown from this agent session. The new `GET /api/session?debug=auth` response is the required next live check.
- Failure category as of this pass:
  - Frontend field mismatch: unlikely based on tests and code inspection.
  - Backend `/api/session` vs `/api/answer` compatibility: unit tests now cover compatible decisions for header and cookie identities.
  - Cloudflare config/allowlist/header-cookie forwarding: still possible, and now diagnosable without exposing secrets.
- Safe session/debug fields added under `accessDebug` only when `debug=auth` is explicitly requested:
  - `authProvider`
  - `answerAuthMode`
  - `accessHeaderPresent`
  - `accessCookiePresent`
  - `accessCookieParseError`
  - `accessTokenSource`
  - `accessIssuerConfigured`
  - `accessAudienceConfigured`
  - `accessJwksConfigured`
  - `accessAllowlistConfigured`
  - `accessIdentityVerified`
  - `emailPresent`
  - `emailAllowlisted`
  - `betaAllowed`
- No secrets exposed: diagnostics intentionally exclude JWTs, cookie values, auth headers, email addresses, env values, source text, and credentials.
- Production auth remains protected: `/api/answer` still requires verified Cloudflare Access identity in production/cloudflare mode, and local anonymous `/api/answer` still returns `401`.
- What Lane 12 should check after restart:
  - Open `https://app.steelguitarrag.com/api/session?debug=auth` in the authenticated protected browser.
  - If `accessHeaderPresent=false` and `accessCookiePresent=false`, Cloudflare identity is not reaching the origin/browser XHR path.
  - If token is present but `accessIdentityVerified=false`, check issuer/AUD/JWKS configuration without printing values.
  - If `accessIdentityVerified=true` and `emailAllowlisted=false`, the logged-in Access identity is not in `STEEL_RAG_BETA_USER_EMAILS` or `STEEL_RAG_ADMIN_EMAILS`.
  - If `betaAllowed=true` but the UI remains locked, capture the browser `/api/session` response and console error state; that would point back to frontend runtime/bootstrap.

## Risk assessment
- Risk: Medium.
- Why: this touches auth/session code, but it only adds safe diagnostics and does not add a new unverified trust path. Normal `/api/session` and `/api/answer` behavior is unchanged unless `debug=auth` is explicitly requested on `/api/session`.
- Rollback notes: revert `pocketsteel/access_control.py`, `pocketsteel/api.py`, `tests/test_api_search.py`, and `docs/api-contract.md` changes from this handoff to remove the diagnostics.

## Commit readiness
Needs human review first

## Suggested next step
- Repo Steward prompt if the diagnostic files are approved for commit:

```text
Repo Steward: review and commit only the scoped Cloudflare Access live-browser session diagnostic changes from the handoff docs/handoffs/task-completions/cloudflare-access-live-browser-unlock-fix.md. Stage exact paths only: docs/api-contract.md, pocketsteel/access_control.py, pocketsteel/api.py, tests/test_api_search.py, docs/handoffs/task-completions/cloudflare-access-live-browser-unlock-fix.md. Do not stage unrelated parked work. Use commit message: Add Cloudflare Access session diagnostics.
```

- Lane 12 prompt after commit/restart:

```text
Lane 12 protected-preview browser smoke: restart the private-preview service from the committed Cloudflare Access session diagnostic fix. In an authenticated Cloudflare Access browser, open https://app.steelguitarrag.com/api/session?debug=auth and record only the boolean/coarse diagnostic fields, with no cookies, JWTs, emails, or secrets. Then open https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=user-smoke-a3103c0-auth-fix and confirm whether /api/session is called on page load, whether Q&A unlocks automatically for beta/admin, whether DEV PREVIEW controls remain hidden in cloudflare_access mode, whether "What is the capital of France?" returns guardrail/no sources/no fretboard behavior, and whether "How do I play a G chord on the E9?" returns an answer with fretboard content. Do not deploy, change DNS, expose Ollama/Chroma, run scraping, regenerate embeddings, reset Chroma, or modify vector/corpus data.
```
