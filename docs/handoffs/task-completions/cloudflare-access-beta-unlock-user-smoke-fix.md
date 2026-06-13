# Cloudflare Access Beta Unlock User Smoke Fix

## Task summary
- Requested: diagnose and fix the protected-preview user-smoke blocker where a Cloudflare Access-authenticated browser reached `/ui/steel-guitar-rag-mock.html` but the Q&A UI stayed locked with the private beta Backstage Pass gate.
- Completed: added Cloudflare Access browser-cookie JWT handling for the backend auth/session boundary, kept the existing `Cf-Access-Jwt-Assertion` origin-header path as the preferred path, made frontend session and answer requests explicitly same-origin credentialed, added regression coverage for cookie-backed beta/admin unlock and invalid cookie rejection, and updated the API contract.
- Intentionally not changed: no DNS, deploy, tunnel routing, Cloudflare policy, secrets, corpus, Chroma, embeddings, scraping, answer quality logic, or public `/api/answer` behavior was changed. No personal emails or names were hardcoded.

## Files changed
- Changed files:
  - `docs/api-contract.md`
  - `pocketsteel/access_control.py`
  - `pocketsteel/cloudflare_access.py`
  - `tests/test_api_search.py`
  - `tests/test_frontend_answer_ui.py`
  - `ui/answer-client.js`
- Created files:
  - `docs/handoffs/task-completions/cloudflare-access-beta-unlock-user-smoke-fix.md`
- Deleted files:
  - None.
- Generated artifacts:
  - None.

## Tests and checks
- `git status --short`
  - Result: worktree contains many pre-existing unrelated modified and untracked files. The scoped diff for this task is limited to the files listed above.
- `git diff --check`
  - Result: passed.
- `node --check ui/answer-client.js`
  - Result: passed.
- `sed -n '/<script>$/,/^  <\/script>$/p' ui/steel-guitar-rag-mock.html | sed '1d;$d' | node --check --input-type=commonjs`
  - Result: passed.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py -k 'api_session or cloudflare_access or unauthenticated or access_role_contract or answer_smoke_server_auth_config_contract'`
  - Result: passed, `24 passed, 179 deselected`.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -k 'session or gates_live_submission or authoritative_access_state or hides_dev_preview or page_load'`
  - Result: passed, `5 passed, 13 deselected`.
- `.venv/bin/python -m pytest tests/test_api_contract.py`
  - Result: passed, `4 passed`.
- `.venv/bin/python -m pytest`
  - Result: failed, `8 failed, 621 passed`.
  - Failures appear unrelated to this auth/session fix:
    - `tests/test_answer_eval.py::test_eval_flags_known_formatting_failures`
    - `tests/test_api_search.py::test_answer_contract_registry_covers_major_intents`
    - `tests/test_api_search.py::test_contract_intent_inference_for_common_questions`
    - `tests/test_api_search.py::test_api_version_reports_runtime_identity_without_auth_or_secrets`
    - `tests/test_api_search.py::test_api_version_rejects_non_get_method`
    - `tests/test_pedal_steel_fretboard_ui.py::test_demo_page_mounts_the_component_without_touching_landing_pages`
    - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
    - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- Tests skipped:
  - Authenticated protected-preview browser smoke could not be completed from this agent session because no authenticated Cloudflare Access browser automation/session was available. API/header/cookie simulation tests were used for the server boundary, but that is not a replacement for Lane 12 protected-preview browser smoke.

## Smoke Target
```text
Smoke Target:
- Target type: protected-preview
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not browser-tested by this agent session
- Cache-busted URL tested: not browser-tested by this agent session
- Exact URL the user should use: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=user-smoke-0c81858
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 0c81858 before this uncommitted fix
- Version endpoint: /api/version
- Version endpoint result: full suite currently reports 404 for /api/version in unrelated tests
- If version endpoint missing, how version is inferred: `git rev-parse --short HEAD` reported 0c81858 before this uncommitted fix
- Whether app root `/` works: not verified in this task
- Whether app root `/` is expected to work: do not assume root works unless Lane 12 verifies it
- Whether `/ui/steel-guitar-rag-mock.html` works: shell was previously verified by Lane 12; authenticated unlock still needs browser smoke after this fix is restarted
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, this is the canonical protected-preview smoke URL for this bug
- Who should test this URL: Lane 12 and the user
- Do not test these URLs: do not shorten this to only https://app.steelguitarrag.com/ because root routing is not the canonical target here
- Known caveats: local API simulation passed, but protected-preview browser unlock must be verified after restarting the preview from this changed code
```

## Integration notes
- Lane classification: mixed `11 Auth / Security`, `06 UX/UI Design`, and `12 Self-Hosted Deployment`; primary fix is auth/session unlock behavior for protected preview.
- Root cause: the backend Cloudflare Access provider only read the `Cf-Access-Jwt-Assertion` WSGI header. Cloudflare Access browser requests can also carry the application token as the `CF_Authorization` cookie. If the tunnel/origin path did not present the header to the local WSGI process while the browser had the Access cookie, `/api/session` stayed anonymous and the frontend correctly kept the Q&A gate locked.
- Before: `/api/session` in `cloudflare_access` mode only authenticated when `Cf-Access-Jwt-Assertion` reached the app. Browser-authenticated users could still remain anonymous to the frontend if only the Access cookie was available.
- After: `/api/session` and `/api/answer` still prefer `Cf-Access-Jwt-Assertion`, but fall back to the `CF_Authorization` cookie when the header is absent. The same JWT verifier, issuer, audience, expiry/not-before, signature validation, and beta/admin allowlists are used. Browser-supplied role headers, email headers, and local-dev mock headers remain ignored in `cloudflare_access` production mode.
- Frontend change: session bootstrap and answer submission now call `fetch` with `credentials: "same-origin"` so same-origin cookies are intentionally included.
- API/session response remains PII-minimized: authenticated state, role, and auth provider are returned; full email is not returned.
- `/api/answer` production auth remains protected: missing Cloudflare identity still returns unauthorized, unlisted identities remain blocked, and beta/admin require verified identity plus allowlist membership.
- Protected preview restart was not run in this task.
- Commit hash if committed: not committed.
- Remaining caveat: browser unlock is expected to work after restart, but must be confirmed by authenticated protected-preview smoke. If it still fails after restart, the next likely issue is Cloudflare Tunnel/header/cookie forwarding or allowlist/env mismatch, not frontend localStorage.

## Risk assessment
- Risk: Medium.
- Why: this touches production auth/session behavior, but it does not weaken the boundary because the cookie value is still treated as a Cloudflare Access JWT and validated with the same verifier and allowlists. It does not trust plain email, group, role, or dev mock headers.
- Rollback notes: revert the scoped changes in `pocketsteel/access_control.py`, `pocketsteel/cloudflare_access.py`, `ui/answer-client.js`, the matching tests, and `docs/api-contract.md` to return to header-only Cloudflare Access validation.

## Commit readiness
Needs human review first

## Suggested next step
- Lane 12 should restart the protected preview from the fixed code and run authenticated browser smoke.
- Exact recommended prompt:

```text
Lane 12 protected-preview browser smoke: restart the private-preview service from the Cloudflare Access cookie/session unlock fix, then test https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=user-smoke-0c81858 behind Cloudflare Access. Confirm /api/session is called on page load, authenticated beta/admin users unlock Q&A automatically, DEV PREVIEW controls remain hidden in cloudflare_access mode, "What is the capital of France?" returns the guardrail/no sources/no fretboard behavior, and "How do I play a G chord on the E9?" returns an answer with fretboard content. Do not deploy, change DNS, expose Ollama/Chroma, run scraping, regenerate embeddings, reset Chroma, or modify vector/corpus data.
```
