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

Use `production` auth mode with the `cloudflare_access` provider for any preview route. `local_dev` is only for local smoke tests and must not be accepted on a public hostname unless the entire hostname is explicitly isolated as a short-lived dev/test route behind Cloudflare Access and never treated as beta access.

Planning command:

```bash
cd /Users/cory/Documents/Pocket\ Steel
source .venv/bin/activate

PYTHONPATH=. \
STEEL_RAG_CHROMA_PATH="/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma" \
STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified" \
STEEL_RAG_ANSWER_AUTH_MODE="production" \
STEEL_RAG_AUTH_PROVIDER="cloudflare_access" \
STEEL_RAG_CF_ACCESS_ISSUER="https://<team>.cloudflareaccess.com" \
STEEL_RAG_CF_ACCESS_AUD="<cloudflare-access-aud-tag>" \
STEEL_RAG_BETA_USER_EMAILS="tester@example.com" \
STEEL_RAG_ADMIN_EMAILS="owner@example.com" \
STEEL_RAG_ANSWER_PROVIDER="ollama" \
STEEL_RAG_CHAT_MODEL="<approved local Ollama chat model>" \
OLLAMA_URL="http://127.0.0.1:11434" \
.venv/bin/python rag_api.py --host 127.0.0.1 --port <APP_PORT> --auth-provider cloudflare-access
```

Notes:

- `STEEL_RAG_CHROMA_PATH` must point to the approved existing local Chroma path.
- `STEEL_RAG_CHROMA_COLLECTION` should match the approved collection, currently expected to be `steel_guitar_unified` for the unified corpus.
- `STEEL_RAG_ANSWER_AUTH_MODE=production` ignores the local dev mock access header.
- `STEEL_RAG_AUTH_PROVIDER=cloudflare_access` validates `Cf-Access-Jwt-Assertion` server-side and derives the access role from verified email allowlists.
- `STEEL_RAG_CF_ACCESS_ISSUER` must match the Cloudflare Access team issuer.
- `STEEL_RAG_CF_ACCESS_AUD` must match the Access application AUD tag.
- `STEEL_RAG_BETA_USER_EMAILS` and `STEEL_RAG_ADMIN_EMAILS` must be explicit comma-separated allowlists.
- `OLLAMA_URL` must stay loopback-only.
- This command is still not a deployment instruction. It is a planned service command to use only after Access app policy, tunnel ingress, rollback, and local service hardening have been reviewed.

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

Backend Access validation boundary:

- Cloudflare Access sends the application JWT to the origin in `Cf-Access-Jwt-Assertion`.
- The backend must run with `STEEL_RAG_AUTH_PROVIDER=cloudflare_access`.
- The backend validates issuer, audience, expiry/not-before, and RS256 signature against the Access JWKS endpoint.
- The backend maps the verified email to `admin` or `beta_user` only if it appears in `STEEL_RAG_ADMIN_EMAILS` or `STEEL_RAG_BETA_USER_EMAILS`.
- Valid but unlisted Access identities receive `403 Forbidden`.
- Missing or invalid Access JWTs receive `401 Unauthorized`.
- Local dev mock headers are ignored in production/cloudflare mode.

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
- [ ] Server-side `/api/answer` Cloudflare Access provider committed.
- [ ] Real identity/login plan documented, including Access issuer, AUD tag, and email allowlists.
- [ ] Production auth mode verified: `STEEL_RAG_ANSWER_AUTH_MODE=production`.
- [ ] Cloudflare Access provider verified: `STEEL_RAG_AUTH_PROVIDER=cloudflare_access`.
- [ ] Anonymous `/api/answer` returns `401 Unauthorized`.
- [ ] Missing `Cf-Access-Jwt-Assertion` returns `401 Unauthorized`.
- [ ] Invalid `Cf-Access-Jwt-Assertion` returns `401 Unauthorized`.
- [ ] Valid unlisted Cloudflare Access email returns `403 Forbidden`.
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

- Do not route `app.steelguitarrag.com` to the Mac mini until `/api/answer` validates Cloudflare Access JWTs server-side.
- Do not expose live RAG while role assignment depends on a browser-controlled header or scaffold provider.
- Do not use `local_dev` auth mode for a real preview hostname.
- Do not expose Ollama publicly.
- Do not expose Chroma publicly.
- Do not create router port forwarding.
- Do not invite testers until rate limiting, request logging, and rollback are ready.
