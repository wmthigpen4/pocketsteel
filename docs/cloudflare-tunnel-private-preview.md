# Cloudflare Tunnel Private Preview Checklist

Task mode: GREEN docs-only planning. This checklist must not deploy anything, change DNS, expose Ollama, expose Chroma, run scraping, regenerate embeddings, reset Chroma, or modify vector data.

User-facing app name: The Turnaround. Keep `pocketsteel`, `pocket-steel`, and `pocket_steel` as internal technical names.

Current branch when this checklist was created: `feature/answer-api`.

## Goal

Prepare a private-preview path for `app.steelguitarrag.com` before routing it publicly through Cloudflare Tunnel. Cloudflare is authoritative DNS for `steelguitarrag.com`, but `app.steelguitarrag.com` must not point to the Mac mini until backend `/api/answer` auth, logging, and rate-limit guardrails are ready.

## Local Service Architecture

```text
Internet -> Cloudflare Tunnel -> Mac mini app -> local Chroma -> local Ollama
```

Boundaries:

- Cloudflare Tunnel is the only planned public ingress path.
- The Mac mini app listens on a local app port.
- Chroma stays local and read-only for preview serving.
- Ollama stays local-only.
- The backend app calls Ollama locally.
- No router port forwarding is required or allowed.

## Local App Command

Use `production` auth scaffold mode for any preview route. `local_dev` is only for local smoke tests and must not be accepted on a public hostname unless the entire hostname is explicitly isolated as a short-lived dev/test route behind Cloudflare Access and never treated as beta access.

Planning command:

```bash
cd /Users/cory/Documents/Pocket\ Steel
source .venv/bin/activate

PYTHONPATH=. \
STEEL_RAG_CHROMA_PATH="/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma" \
STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified" \
STEEL_RAG_ANSWER_AUTH_MODE="production" \
STEEL_RAG_ANSWER_PROVIDER="ollama" \
STEEL_RAG_CHAT_MODEL="<approved local Ollama chat model>" \
OLLAMA_URL="http://127.0.0.1:11434" \
.venv/bin/python rag_api.py --host 127.0.0.1 --port <APP_PORT>
```

Notes:

- `STEEL_RAG_CHROMA_PATH` must point to the approved existing local Chroma path.
- `STEEL_RAG_CHROMA_COLLECTION` should match the approved collection, currently expected to be `steel_guitar_unified` for the unified corpus.
- `STEEL_RAG_ANSWER_AUTH_MODE=production` ignores the local dev mock access header.
- `OLLAMA_URL` must stay loopback-only.
- This command is not enough for public beta because the current trusted role header is still scaffolding. Real server-side identity/session validation must own role assignment before live RAG is exposed.

## Cloudflare Tunnel Setup Steps

These are manual setup steps for later. Do not run them until the pre-tunnel checklist passes.

1. Install `cloudflared` on the Mac mini.
2. Authenticate `cloudflared` with the Cloudflare account that controls `steelguitarrag.com`.
3. Create a named tunnel for the preview app.
4. Configure a public hostname:
   - Hostname: `app.steelguitarrag.com`
   - Service: `http://127.0.0.1:<APP_PORT>`
5. Confirm the tunnel route points only to the local app port.
6. Confirm there is no tunnel ingress rule for `127.0.0.1:11434`.
7. Confirm there is no tunnel ingress rule for Chroma or any database process.
8. Confirm the home router has no port forwarding for the app, Ollama, Chroma, or SSH.
9. Confirm the root domain still does not point to live RAG.

## Cloudflare Access Option

Recommended for preview:

- Protect `app.steelguitarrag.com` with Cloudflare Access.
- Allow only the owner and named testers.
- Use an allowlist policy by email or identity-provider group.
- Keep a deny-by-default posture for the preview hostname.
- Require Access before the request reaches the Mac mini app.

Important: Cloudflare Access is not a substitute for backend auth. `/api/answer` must still enforce backend authorization before retrieval or answer generation runs.

## Security Requirements

- Ollama must remain local-only at `http://127.0.0.1:11434`.
- Chroma must remain local-only and read-only for preview serving.
- `/api/answer` must enforce backend auth.
- Anonymous users must receive a non-200 auth response from `/api/answer`.
- Retrieval and answer generation must not run for unauthorized requests.
- Local dev mock auth must not be accepted publicly unless behind an explicit, short-lived dev/test mode and Cloudflare Access; it must not be used as private beta authorization.
- Browser-side code must not contain model secrets, auth secrets, Cloudflare tokens, local paths, or Ollama details.
- Prompt-injection guardrails must stay active for user questions and retrieved source text.
- Rate-limit and request-logging scaffolds must be in place before the tunnel route is created.
- Error responses must not expose local filesystem paths, Chroma paths, tunnel credentials, stack traces, or model internals.

## Rollback

Fast rollback order:

1. Remove the `app.steelguitarrag.com` tunnel public hostname.
2. Disable the app route in Cloudflare.
3. Stop `cloudflared` on the Mac mini.
4. Stop the local app service if needed.
5. Keep Ollama local; do not expose it for debugging.
6. Leave root and `www` on public-safe landing routing.
7. Preserve logs needed for review, subject to the approved retention policy.

## Manual Checklist Before Creating the Tunnel

- [ ] Answer eval passing against the intended local service path.
- [ ] Server-side `/api/answer` auth scaffold committed.
- [ ] Real identity/login plan documented, even if not final.
- [ ] Production auth mode verified: `STEEL_RAG_ANSWER_AUTH_MODE=production`.
- [ ] Anonymous `/api/answer` returns `401 Unauthorized`.
- [ ] Unauthorized non-live roles return `403 Forbidden`.
- [ ] Local dev mock auth is disabled for the public route.
- [ ] Rate-limit scaffold committed.
- [ ] Request-logging scaffold committed.
- [ ] Local app can run as a service on `127.0.0.1:<APP_PORT>`.
- [ ] Mac mini sleep disabled.
- [ ] Ollama reachable only from the Mac mini at `http://127.0.0.1:11434`.
- [ ] Chroma path confirmed and backed up before any future migration.
- [ ] No scraping command is part of startup.
- [ ] No embedding command is part of startup.
- [ ] No Chroma reset or vector write is part of startup.
- [ ] Root domain still does not point to live RAG.
- [ ] `www` still does not point to live RAG.
- [ ] Cloudflare Access preview policy drafted if used.
- [ ] Rollback steps reviewed.

## Blockers Before Actual Tunnel Routing

- Do not route `app.steelguitarrag.com` to the Mac mini until `/api/answer` enforces backend auth.
- Do not expose live RAG while role assignment depends on a browser-controlled header.
- Do not use `local_dev` auth mode for a real preview hostname.
- Do not expose Ollama publicly.
- Do not expose Chroma publicly.
- Do not create router port forwarding.
- Do not invite testers until rate limiting, request logging, and rollback are ready.
