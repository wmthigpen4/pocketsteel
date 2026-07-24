# WSGI Request-Body Over-read Repair

## Task summary

Live-stack diagnostics identified the actual 524 cause: the standard JSON reader requested one byte beyond the declared `Content-Length`. `BytesIO`-based unit tests returned EOF immediately, but the real WSGI socket waited for an extra byte that the browser correctly never sent. The reader now consumes exactly the already-validated content length.

Intentionally unchanged: API request/response schemas, body-size limits, authentication order, retrieval behavior, corpus/vector data, Cloudflare configuration, and secrets.

## Lane classification

- Primary lane: 05 Backend / RAG Integration
- Supporting lanes: 12 Self-Hosted Deployment and 15 QA
- Mode: approved Autopilot runtime reliability bug fix

## Files changed

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- This handoff

## Tests and checks

- Focused JSON/dependency/API tests — 10 passed, 313 deselected.
- Real local threaded WSGI smoke against the configured read-only v2 index — HTTP 200 in 0.773 seconds; previously timed out with zero response bytes.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 1,023 passed.
- Core JavaScript syntax checks — passed.
- Python compile check — passed.
- `git diff --check` — passed.

## Smoke Target

- Target type: local
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not applicable for the diagnostic request
- Cache-busted URL tested: not applicable
- Exact URL the user should use: not yet issued; protected browser re-smoke is required after commit
- Auth required: yes, local-development scaffold for the local diagnostic only
- Auth provider: local scaffold for diagnostic; Cloudflare Access remains the protected provider
- Cloudflare Access login result: succeeded in the prior protected diagnostic smoke
- Local backend URL: `http://127.0.0.1:8892`
- Expected backend port: 8892 for diagnostic; 8770 for protected preview
- Expected git HEAD: follow-up commit pending
- Version endpoint: `/api/version`
- Version endpoint result: protected process still reported `ef893f4` before this uncommitted repair
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after protected restart
- Do not test these URLs: the temporary port 8892 after the diagnostic server is stopped
- Known caveats: protected browser confirmation is pending the exact-path repair commit and restart

## Integration notes

- The 1 MiB limit remains enforced from the validated `Content-Length` before the body is read.
- Import-specific limits already read the exact body length and were not changed.
- Regression coverage uses a socket-like body that asserts if the code reads beyond the declared length.
- Diagnostic stack traces contained no request content and confirmed the worker was blocked at `_read_json_body`.

## Risk assessment

- Risk: low. This aligns WSGI body reading with the protocol's declared length.
- Rollback: revert the scoped commit; no data or deployment rollback is required.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-07-13-1552-05-wsgi-body-overread-repair.md`

## Files that must not be staged

All unrelated dirty/private/corpus/vector/source-inbox/brand/design/deployment/generated/coordination files, including `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated four-workspace browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the three exact paths, restart the installed preview job, verify `/api/version`, and confirm the protected answer completes without 524.
