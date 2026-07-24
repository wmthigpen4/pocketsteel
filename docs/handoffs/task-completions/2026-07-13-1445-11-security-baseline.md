# Security Baseline Autopilot Handoff

## Task summary

- Implemented the approved first technical-debt remediation loop from baseline `be41409647d058b09c01edf6d432eec5b2b16803`.
- Centralized authorization for content-bearing API routes and moved authorization before request-body parsing and retrieval work.
- Made production API construction fail closed unless `cloudflare_access` is explicitly configured. Scaffold and role-header authentication remain local-development-only.
- Replaced handwritten RSA/JWT verification with PyJWT/cryptography verification using a fixed RS256 allow-list, required issuer/audience/expiration claims, bounded JWKS loading, TTL caching, and one rotation refresh.
- Added a 1 MiB cap for ordinary JSON requests while retaining Melody import-specific limits.
- Restricted clickable retrieval/source URLs to HTTP(S).
- Minimized `/api/version`, added baseline security headers and authenticated CSP report collection, and bounded in-memory security logs and rate-limit key state.
- Intentionally did not change Cloudflare Access policy, DNS, corpus/vector/private data, scraping, deployment configuration, or product naming.

## Lane classification

- Primary lane: `11 Auth / Security`
- Supporting lanes: `05 Backend / RAG Integration`, `15 QA / Answer Eval`, `01 Repo Steward`, `12 Self-Hosted Deployment`
- Task mode: RED actions were explicitly approved in the technical-debt remediation plan.

## Files changed

- `steel_guitar_rag/access_control.py`
- `steel_guitar_rag/cloudflare_access.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answer_usage.py`
- `steel_guitar_rag/rag_guardrails.py`
- `steel_guitar_rag/answering.py`
- `pyproject.toml`
- `tests/test_cloudflare_access.py` (new)
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `tests/test_api_answer_private_retrieval.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_v2_rerank_smoke_server.py`
- This handoff.

No files were deleted. No generated artifacts are part of the commit scope.

## Tests and checks

- `PYTHONPATH=. .venv/bin/pytest -q` — passed, `1004 passed`.
- Focused post-hardening regression:
  - `PYTHONPATH=. .venv/bin/pytest -q tests/test_cloudflare_access.py tests/test_api_search.py tests/test_tab_engine.py tests/test_api_answer_private_retrieval.py tests/test_same_origin_smoke_server.py tests/test_v2_rerank_smoke_server.py` — passed, `391 passed`.
- JavaScript syntax:
  - `node --check ui/answer-client.js` — passed.
  - `node --check ui/pedal-steel-fretboard.js` — passed.
  - `node --check ui/melody-workbench.js` — passed.
  - `node --check ui/lesson-workbench.js` — passed.
- `git diff --check` over the exact implementation/test scope — passed.
- Local API smoke:
  - Minimal `/api/version` returned `200` with security headers.
  - Anonymous `/api/search` returned `401`.
  - Authenticated local-dev `/api/search` returned `200`.
  - Chat, Explorer, Melody Studio, and Lessons static targets returned `200`.
- Local browser smoke opened all four workspaces, found the expected headings, and recorded no console warnings/errors.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8877/ui/steel-guitar-rag-mock.html?access=beta_user&v=security-baseline-local-20260713`
- Cache-busted URL tested: `http://127.0.0.1:8877/ui/steel-guitar-rag-mock.html?access=beta_user&v=security-baseline-local-20260713`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart; local URL is not a user handoff
- Auth required: yes
- Auth provider: local explicit scaffold for this smoke only
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8877`
- Expected backend port: `8877`
- Expected git HEAD: `be41409647d058b09c01edf6d432eec5b2b16803` plus this uncommitted security diff
- Version endpoint: `http://127.0.0.1:8877/api/version`
- Version endpoint result: `200`, `git_sha=be41409`, minimal service identity only
- Whether app root `/` works: not tested in browser; same-origin server redirect behavior remains covered by tests
- Whether app root `/` is expected to work: yes, local same-origin redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: unrelated production or Cloudflare policy URLs during this local loop
- Known caveats: the local server used an in-memory empty search index and proves browser/API wiring, not protected-preview authentication or retrieval quality

## Integration notes

- `/api/session` remains the identity/feature probe and is intentionally not a content-bearing endpoint.
- `/api/version` now returns only `status`, `git_sha`, and `server_started_at`; feature flags remain under `/api/session`.
- Normal JSON routes return consistent JSON `401`, `403`, and `413` errors. Melody import retains its existing route-specific size/error contract.
- `PyJWT[crypto]>=2.13,<3` is now a runtime dependency. Reproducible locks are deferred to the approved quality/tooling loop.
- Protected-preview restart and authenticated protected-browser smoke are required after the exact-path commit.

## Risk assessment

- Risk: medium.
- Reason: authorization order, production startup behavior, and a runtime dependency changed, but public response bodies were otherwise preserved and the full suite plus local browser smoke passed.
- Rollback: revert the scoped security commit and restart the protected preview at the previous known-good HEAD.

## Human decision needed

- No. The scope and deployment loop were explicitly approved.

## Safe-to-stage exact file list

- `steel_guitar_rag/access_control.py`
- `steel_guitar_rag/cloudflare_access.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answer_usage.py`
- `steel_guitar_rag/rag_guardrails.py`
- `steel_guitar_rag/answering.py`
- `pyproject.toml`
- `tests/test_cloudflare_access.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `tests/test_api_answer_private_retrieval.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_v2_rerank_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1445-11-security-baseline.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (separate coordination artifact)
- All unrelated dirty README/docs/corpus/source/deployment/private/vector/brand/generated paths
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, source-inbox raw/provenance data, `public/`, `ui/brand/`, `Neon Sign/`, `.wrangler/`, and generated reports/assets

## Recommended next lane

- `01 Repo Steward` for exact-path commit, then `12 Self-Hosted Deployment` for protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the exact files above, review the cached diff, commit the security baseline, restart the protected preview with the documented command, verify `/api/version` against the new HEAD, and smoke Chat, Explorer, Melody Studio, and Lessons while authenticated.
