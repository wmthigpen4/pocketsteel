# Security Audit: Private Preview

Date: 2026-05-28
Branch: `feature/answer-api`
Scope: The Turnaround private-preview readiness before outside testers.

Task mode: GREEN audit/report with one small `.gitignore` hardening fix. No deployment, DNS, scraping, embedding, Chroma reset, vector mutation, corpus-v2 switch, or paid/external scanning was performed.

## Executive Summary

The current app has the core private-preview security boundary in place for `/api/answer` when it is run with:

```text
STEEL_RAG_ANSWER_AUTH_MODE=production
STEEL_RAG_AUTH_PROVIDER=cloudflare_access
```

The code and tests cover Cloudflare Access JWT validation, beta/admin allowlists, anonymous blocking, local-dev mock header isolation, session bootstrapping, rate-limit behavior, public landing-page separation, and RAG answer cleanup.

Outside-user testing should not start until the actual preview environment is manually verified against the documented Cloudflare Access/Tunnel checklist. Code-level blockers were not found in this audit, but there are important SHOULD FIX items around session/log privacy, root-level local secret hygiene, and public form anti-spam.

## Commands Run

```bash
git status --short --branch
rg --files -g '!*__pycache__*'
git ls-files
sed -n '1,240p' .gitignore
rg -n "answer|session|Access|cloudflare|AUTH|auth|beta_user|admin|rate|429|log|prompt|inject|Ollama|Chroma|private preview|rollback|router|port forwarding" pocketsteel rag_api.py rag_app.py ui deploy docs tests functions README.md pyproject.toml
sed -n '1,260p' pocketsteel/api.py
sed -n '1,260p' pocketsteel/access_control.py
sed -n '1,260p' pocketsteel/cloudflare_access.py
sed -n '260,620p' pocketsteel/api.py
sed -n '1,260p' pocketsteel/answer_usage.py
sed -n '1,420p' tests/test_api_contract.py
sed -n '1,280p' tests/test_public_landing_page.py
sed -n '1,320p' functions/api/interest.js
sed -n '1,420p' pocketsteel/answering.py
sed -n '1,260p' pocketsteel/rag_guardrails.py
sed -n '1,430p' tests/test_api_search.py
sed -n '430,920p' tests/test_api_search.py
sed -n '1,360p' tests/test_frontend_answer_ui.py
sed -n '140,380p' docs/api-contract.md
sed -n '1,260p' docs/cloudflare-tunnel-private-preview.md
sed -n '920,1360p' tests/test_api_search.py
sed -n '360,760p' tests/test_frontend_answer_ui.py
sed -n '1,240p' ui/answer-client.js
sed -n '1,260p' docs/private-preview-operations.md
git ls-files -z | xargs -0 -n1 | rg '(^|/)(\.env|private-preview\.env|.*\.env|corpus-v2|.*chroma.*|.*vector.*|.*embedding.*|.*\.sqlite3?|.*\.db|.*\.jsonl|.*cloudflared.*|.*token.*|raw|rag-data|transcripts|paid-transcripts)'
find . -path ./.git -prune -o -path './.venv' -prune -o -path './__pycache__' -prune -o \( -name '.env' -o -name '.env.*' -o -name '*.env' -o -name 'private-preview.env' -o -name '*cloudflared*' -o -name '*token*' -o -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.jsonl' -o -name 'corpus-v2' -o -name 'chroma' -o -name '*chroma*' -o -name '*vector*' -o -name '*embedding*' -o -name 'transcripts' -o -name 'paid-transcripts' \) -print
rg -n --hidden -g '!.git/**' -g '!.venv/**' -g '!*.png' -g '!*.jpg' -g '!*.jpeg' -g '!*.webp' -g '!*.gif' -g '!*.ico' "(CF_API_TOKEN|CLOUDFLARE_API_TOKEN|cloudflared.*token|TunnelSecret|client_secret|BEGIN (RSA |OPENSSH |PRIVATE )?KEY|sk-[A-Za-z0-9]|password\s*=|secret\s*=|authorization:\s*bearer|Cf-Access-Jwt-Assertion)" .
git check-ignore -v .env private-preview.env corpus-v2/foo rag-data/forums/foo.jsonl rag-data/electronics/chroma/index.sqlite data/raw/foo.jsonl data/indexes/foo.faiss transcripts/foo.txt paid-transcripts/foo.txt logs/app.log .wrangler/state scripts/foo.log
git check-ignore -v corpus_metadata/copyright_review_queue.jsonl corpus_metadata/legal_provenance_events.jsonl corpus_metadata/source_policy_snapshots.jsonl corpus_metadata/legal_snapshots/foo.json corpus_metadata/review_queue/foo.json
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_frontend_answer_ui.py tests/test_public_landing_page.py
.venv/bin/python -m pytest
git diff --check
```

Test results:

- Focused security/audit suite: 118 passed.
- Full pytest suite: 191 passed.
- `git diff --check`: passed with no output.

## Auth Boundary

Status: PASS with deployment configuration dependency.

Observed behavior:

- `/api/answer` authorizes before search, retrieval, answer generation, or source-card construction.
- In production plus `cloudflare_access` mode, `/api/answer` requires `Cf-Access-Jwt-Assertion`.
- Missing Access JWT returns `401 Unauthorized`.
- Invalid Access JWT returns `401 Unauthorized`.
- Valid Access JWT with an unlisted email returns `403 Forbidden`.
- Valid Access JWT with an allowlisted beta/admin email permits live answer access.
- Local-dev mock role headers are ignored in production plus `cloudflare_access` mode.
- `local_dev` mock headers still work only in local-dev mode.
- `/api/session` uses the same auth boundary and does not run retrieval or answer generation.
- Cloudflare Access JWT validation checks issuer, audience, expiry/not-before, RS256 signature, and email allowlists.

Evidence:

- `pocketsteel/access_control.py`
- `pocketsteel/cloudflare_access.py`
- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `tests/test_api_contract.py`
- `docs/api-contract.md`
- `docs/cloudflare-tunnel-private-preview.md`

Notes:

- The default auth provider normalizes to `scaffold` if `STEEL_RAG_AUTH_PROVIDER` is unset. This is acceptable for local scaffolding, but private preview must run explicitly with `cloudflare_access`.
- `/api/session` currently returns the verified email for authenticated and unlisted Cloudflare Access identities. That is useful for UI/debugging, but it is more PII than a minimal status endpoint needs.

## Public Surface

Status: PASS with anti-spam follow-up.

Observed behavior:

- The public landing page and deployed landing output do not reference `/api/answer`.
- The landing page posts only to `/api/interest`.
- The deployed landing page does not expose Ollama, Chroma, SGF private/internal routes, `answer-client.js`, mock answer data, or the private app bypass UI.
- `/api/interest` accepts JSON or form data, validates email, truncates string fields, limits the interest list, hashes IP addresses, and returns safe JSON on D1 failures.
- D1 failures return `{ ok: false, error: "storage_error" }` without stack traces.

Evidence:

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `functions/api/interest.js`
- `tests/test_public_landing_page.py`

Notes:

- `verifyTurnstilePlaceholder` currently always returns success. That is a reasonable scaffold, but the public endpoint remains spam-prone until real Turnstile verification or equivalent abuse protection is enabled.

## Secrets And Generated Files

Status: PASS after `.gitignore` hardening, with local hygiene follow-up.

Tracked-file scan:

- No tracked `.env`, `private-preview.env`, cloudflared token, Cloudflare secret, SQLite DB, Chroma/vector store, `corpus-v2/`, raw corpus dump, private transcript, or paid transcript file was found.
- Tracked JSONL files are limited to fixtures/eval samples such as `eval/electronics_gold_questions.jsonl`, `tests/fixtures/raw_sgf_sample.jsonl`, and `tests/fixtures/phase3_sample_chunks.jsonl`.
- Tracked Chroma/vector/embedding matches are code or docs only, not databases or vector stores.

Local untracked/ignored scan:

- `private-preview.env` exists at the repo root and is ignored.
- `corpus-v2/` exists locally and is ignored. It includes generated JSONL and a Chroma SQLite store under `corpus-v2/vector-stores/chroma/`.
- `rag-data/electronics/clean_corpus_sample.jsonl` exists locally under ignored `rag-data/`.
- Archive/eval JSONL exists locally under ignored `archive/`.
- No secret-looking token/private-key pattern was found by the targeted text scan, aside from documented `Cf-Access-Jwt-Assertion` references.

Fix applied:

- Added `.gitignore` entries for generated legal/review metadata outputs:
  - `corpus_metadata/copyright_review_queue.jsonl`
  - `corpus_metadata/legal_provenance_events.jsonl`
  - `corpus_metadata/legal_snapshots/`
  - `corpus_metadata/review_queue/`
  - `corpus_metadata/source_policy_snapshots.jsonl`

Notes:

- The root-level `private-preview.env` should be moved outside the repo or deleted after explicit human approval. The docs already recommend `~/.steel-rag/env/private-preview.env`.

## Rate Limits And Logging

Status: PASS for scaffold behavior, SHOULD FIX for privacy posture.

Observed behavior:

- `/api/answer` returns `401`, `403`, and `429` along the expected paths.
- Rate limits are configurable by:
  - `STEEL_RAG_ANSWER_RATE_LIMIT_ENABLED`
  - `STEEL_RAG_ANSWER_RATE_LIMIT_MAX_REQUESTS`
  - `STEEL_RAG_ANSWER_RATE_LIMIT_WINDOW_SECONDS`
- Defaults are enabled, `120` requests per `60` seconds.
- Rate limiting happens after auth and before retrieval.
- Request logs record timestamp, role, access status, authorized/blocked state, question length, mode, source count, warning count, and error status.
- Logs do not record the question body, source excerpts, JWTs, Cloudflare tokens, Chroma paths, Ollama URL, or env/config values.

Evidence:

- `pocketsteel/answer_usage.py`
- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `docs/api-contract.md`

Notes:

- Logs currently include `identityEmail` when Cloudflare Access identifies a user. That is not a secret, but it is PII. Consider hashing or omitting it before outside-user testing unless raw email logging is intentionally approved.
- The current limiter is process-local and role/IP keyed. That is acceptable for a light private preview, but it is not a production quota system.

## RAG And LLM Safety

Status: PASS for current preview scope.

Observed behavior:

- Retrieved source text is treated as untrusted evidence and sanitized before answer generation.
- Prompt-injection-like retrieved excerpts are removed or redacted before source cards or answer-provider input.
- Prompt-injection-like user questions return a refusal-style response instead of following the instruction.
- The Ollama provider sends a fixed system instruction and source context from sanitized sources.
- The deterministic provider and final quality gates remove or avoid raw forum junk, source context dumps, source citation boilerplate, email addresses, raw forum questions, edited-post boilerplate, and noisy excerpts.
- Answer contracts enforce intent-specific fallbacks for common failure modes.
- Tests cover prompt-injection source text, answer body cleanup, no source-context dumps, raw email filtering, and source-card preservation.

Evidence:

- `pocketsteel/rag_guardrails.py`
- `pocketsteel/answering.py`
- `pocketsteel/answer_contracts.py`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`

Notes:

- RAG prompt or ranking changes are YELLOW tasks in this repo and were not made.
- No corpus, embedding, Chroma, or vector data command was run.

## Self-Hosting Exposure

Status: PASS as documented, pending manual preview verification.

Observed behavior:

- Private-preview docs explicitly require Ollama to remain loopback-only.
- Chroma remains local-only and read-only for preview serving.
- No router port forwarding is required or allowed.
- Cloudflare Tunnel is documented as the only planned public ingress path.
- Cloudflare Access is documented as required before tester access.
- Rollback steps exist for disabling the tunnel hostname, stopping `cloudflared`, stopping the local app, and leaving the root/www landing page public-safe.

Evidence:

- `docs/cloudflare-tunnel-private-preview.md`
- `docs/private-preview-operations.md`
- `docs/retrieval-api.md`

Notes:

- This audit did not inspect a live Cloudflare account, DNS zone, Access app, or tunnel state.

## Findings

### BLOCKER

None found in code for the requested private-preview app path.

Operationally, outside-user testing remains blocked until the actual Mac mini/private-preview service is manually started and verified with `STEEL_RAG_ANSWER_AUTH_MODE=production` and `STEEL_RAG_AUTH_PROVIDER=cloudflare_access`, behind Cloudflare Access, with no Ollama/Chroma/tunnel leakage.

### SHOULD FIX

1. Minimize `/api/session` and request-log PII.
   - Current `/api/session` returns `email`, and request logs include `identityEmail`.
   - Recommended fix: either omit email from `/api/session` and logs, or replace logged email with a stable hash, after explicit approval because this changes API/logging behavior.

2. Move or delete the root-level `private-preview.env`.
   - It is ignored, but it lives inside the repo working tree.
   - Recommended fix: move it to `~/.steel-rag/env/private-preview.env` or delete the repo-root copy after explicit human approval.

3. Add real Turnstile verification for `/api/interest`.
   - Current placeholder always succeeds.
   - Recommended fix: validate `turnstileToken` server-side before storing submissions.

### LATER

1. Replace process-local rate limiting with a persistent per-user quota store if preview expands beyond a few trusted testers.
2. Add log-retention guidance for private preview, including PII handling and where logs may be stored.
3. Add an operator smoke script that checks `/api/session`, anonymous `/api/answer`, missing/invalid Access JWT, valid unlisted Access identity, and valid allowlisted beta/admin identity without touching corpus/vector data.
4. Consider adding a CI guard that fails if generated corpus/legal metadata files appear in `git status --short` as untracked non-ignored paths.

## Outside-User Testing Decision

Blocked today for operations verification, not for a known code-level blocker.

Outside testers can be invited only after:

- The app is run in production plus Cloudflare Access mode.
- Cloudflare Access is configured deny-by-default with named tester/admin allowlists.
- Anonymous and missing-token `/api/answer` requests are verified as blocked.
- Valid unlisted Access identities are verified as blocked.
- Ollama and Chroma are verified local-only.
- Root and `www` remain landing-page only.
- The human owner accepts or resolves the SHOULD FIX items above.

## Confirmation

This audit did not deploy, change DNS, expose Ollama, expose Chroma, run scraping, regenerate embeddings, reset Chroma, modify vector data, switch to corpus-v2, or run paid/external scanners.
