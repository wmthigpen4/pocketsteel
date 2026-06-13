# Private Preview Operations Runbook

Task mode: GREEN docs-only operations runbook. This document must not deploy, change DNS, expose Ollama, expose Chroma, run scraping, or modify corpus, Chroma, embeddings, or vector data.

User-facing app name: The Turnaround. Keep `pocketsteel`, `pocket-steel`, and `pocket_steel` as internal technical names.

Current branch when this runbook was created: `feature/answer-api`.

## Local Architecture

```text
Internet -> Cloudflare Access -> Cloudflare Tunnel -> Mac mini app -> local Chroma -> local Ollama
```

Only the Mac mini app should be reachable through the tunnel. Ollama and Chroma must stay local/private.

## Start Local App

Run from the repo root on the Mac mini:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate

set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
.venv/bin/python scripts/serve_answer_smoke.py \
  --host 127.0.0.1 \
  --port <APP_PORT> \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Required environment should include:

```text
STEEL_RAG_AUTH_PROVIDER=cloudflare_access
STEEL_RAG_ANSWER_AUTH_MODE=production
STEEL_RAG_CF_ACCESS_ISSUER=<Cloudflare Access issuer>
STEEL_RAG_CF_ACCESS_AUD=<Cloudflare Access AUD tag>
STEEL_RAG_CF_ACCESS_JWKS_URL=<Cloudflare Access JWKS URL>
STEEL_RAG_BETA_USER_EMAILS=<comma-separated tester emails>
STEEL_RAG_ADMIN_EMAILS=<comma-separated admin emails>
STEEL_RAG_CHROMA_PATH=<approved local Chroma path>
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified
OLLAMA_URL=http://127.0.0.1:11434
```

Do not commit `~/.steel-rag/env/private-preview.env` or paste its contents into issues, chats, docs, or logs.

## Stop Or Restart Local App

If running in a foreground terminal:

```bash
control-c
```

Then rerun the start command above.

If running under `launchctl`, use the actual service label:

```bash
launchctl kickstart -k gui/$(id -u)/com.steelguitarrag.app
```

To stop a user-agent service:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.steelguitarrag.app.plist
```

If installed as a system daemon, use the matching `system/` target and documented plist path instead.

Confirm the port is no longer listening after stop:

```bash
lsof -nP -iTCP:<APP_PORT> -sTCP:LISTEN
```

No output means the local app is stopped.

## Confirm Local Health

Set the local base URL:

```bash
export STEEL_RAG_LOCAL_BASE="http://127.0.0.1:<APP_PORT>"
```

Confirm `/api/session` responds:

```bash
curl -sS "$STEEL_RAG_LOCAL_BASE/api/session"
```

Expected anonymous/local response in Cloudflare Access mode without an Access JWT:

```json
{"authenticated":false,"role":"anonymous","email":null,"authProvider":"cloudflare_access"}
```

Confirm anonymous local `/api/answer` is blocked:

```bash
curl -sS -i \
  -X POST "$STEEL_RAG_LOCAL_BASE/api/answer" \
  -H "Content-Type: application/json" \
  --data '{"question":"Why does my amp buzz?","mode":"gear"}'
```

Expected result:

```text
401 Unauthorized
```

Unauthorized requests must not run retrieval or answer generation.

## Confirm Cloudflare Access

After the tunnel and Access app are intentionally enabled:

```bash
curl -sS -I https://app.steelguitarrag.com
```

Expected unauthenticated behavior:

- Redirect to Cloudflare Access login, or
- Cloudflare Access denial/challenge response.

Then test in a browser:

1. Open `https://app.steelguitarrag.com`.
2. Authenticate through Cloudflare Access with an allowlisted tester/admin email.
3. Confirm the app loads.
4. Confirm `/api/session` reports an authenticated `beta_user` or `admin`.
5. Ask one low-risk test question.
6. Confirm anonymous or missing-token `/api/answer` still fails.

## Confirm Q&A Unlocks After Access Login

In the authenticated browser session:

1. Open DevTools Network panel.
2. Reload `https://app.steelguitarrag.com`.
3. Confirm `GET /api/session` returns `200 OK`.
4. Confirm the JSON includes:

   ```json
   {"authenticated":true,"role":"beta_user","authProvider":"cloudflare_access"}
   ```

   or:

   ```json
   {"authenticated":true,"role":"admin","authProvider":"cloudflare_access"}
   ```

5. Confirm the Q&A UI is unlocked without using `?access=beta_user`.
6. Submit one low-risk question, for example:

   ```text
   Why does my amp buzz until I touch the changer?
   ```

7. Confirm `POST /api/answer` returns `200 OK` only in the authenticated Access session.
8. Open a private/incognito window and confirm the same app URL redirects to Cloudflare Access before the app loads.
9. Confirm a direct unauthenticated `POST /api/answer` does not return an answer.

## Confirm Landing Form Stores To D1

Use the public root form or a direct POST to the public landing endpoint:

```bash
curl -sS -i \
  -X POST https://steelguitarrag.com/api/interest \
  -H "Content-Type: application/json" \
  --data '{"email":"ops-smoke@example.com","name":"Ops Smoke Test","interests":["forum-wisdom"]}'
```

Expected JSON:

```json
{"ok":true,"stored":true,"storage":"d1"}
```

After a smoke test, remove the test row:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "delete from interest_submissions where email = 'ops-smoke@example.com';"
```

Verify cleanup:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select count(*) as count from interest_submissions where email = 'ops-smoke@example.com';"
```

Expected count: `0`.

## Check Cloudflared Service Status

If installed with Homebrew services:

```bash
brew services list | grep cloudflared
```

If installed as a user LaunchAgent:

```bash
launchctl print gui/$(id -u)/com.steelguitarrag.cloudflared
```

If installed as a system daemon:

```bash
sudo launchctl print system/com.steelguitarrag.cloudflared
```

Also check the Cloudflare dashboard tunnel status before inviting testers.

## Restart Cloudflared

Homebrew service:

```bash
brew services restart cloudflared
```

User LaunchAgent:

```bash
launchctl kickstart -k gui/$(id -u)/com.steelguitarrag.cloudflared
```

System daemon:

```bash
sudo launchctl kickstart -k system/com.steelguitarrag.cloudflared
```

After restart, verify:

- Cloudflare dashboard shows the tunnel connected.
- `https://app.steelguitarrag.com` still redirects to Cloudflare Access when unauthenticated.
- Ollama is not exposed.
- Chroma is not exposed.

## Tunnel Token Rotation Warning

- Treat tunnel tokens and credential files as secrets.
- Do not paste tunnel tokens into chat, issues, docs, shell history snippets, screenshots, or commit messages.
- Do not commit `cloudflared` credentials, tunnel JSON files, `.env` files, or copied dashboard tokens.
- If a tunnel token is pasted or committed, assume it is exposed.
- Rotate the tunnel token or recreate the tunnel credential in Cloudflare.
- Restart `cloudflared` after rotating credentials.
- Verify `app.steelguitarrag.com` still goes through Cloudflare Access after rotation.

## Mac Mini Sleep And Power Checklist

- Disable computer sleep.
- Display sleep is fine if it does not stop services.
- Enable automatic restart after power failure.
- Keep the Mac mini and network gear on a UPS.
- Confirm Wi-Fi/Ethernet reconnects after reboot.
- Keep enough free disk space for logs and Chroma reads.
- Apply macOS, Python, Ollama, and `cloudflared` updates on a planned maintenance schedule.
- Confirm services restart after reboot before inviting testers.

## Ollama Local-only Reminder

Ollama should only be used by the backend app on the Mac mini:

```text
OLLAMA_URL=http://127.0.0.1:11434
```

Checklist:

- Do not create a Cloudflare Tunnel route to `127.0.0.1:11434`.
- Do not port-forward `11434` on the router.
- Do not bind Ollama to a public interface.
- Do not expose Ollama model names, prompts, logs, or local URLs in browser code.
- Confirm the app reaches Ollama through the backend only.

## Chroma Local-only Reminder

Chroma should stay as local read-only serving data for the preview:

```text
STEEL_RAG_CHROMA_PATH=<approved local Chroma path>
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified
```

Checklist:

- Do not create a public Chroma service.
- Do not create a Cloudflare Tunnel route to Chroma.
- Do not port-forward any Chroma or database port.
- Do not run embedding rebuilds from the operations flow.
- Do not reset Chroma.
- Do not modify vector data during preview recovery.
- Back up the approved Chroma directory before any future migration.

## Rollback Steps

If the private preview behaves unsafely:

1. Stop the local app.
2. Remove or disable the `app.steelguitarrag.com` tunnel public hostname.
3. Disable the Cloudflare Access app or remove all allowed users.
4. Stop `cloudflared` if needed.
5. Leave the landing page live on `steelguitarrag.com` and `www.steelguitarrag.com`.
6. Keep the public landing form available if it is healthy.
7. Keep Ollama local; do not expose it for debugging.
8. Keep Chroma local; do not expose it for debugging.
9. Preserve relevant logs for review without committing private logs.

## Warnings

- Do not expose Ollama.
- Do not expose Chroma.
- Do not route live `/api/answer` without Cloudflare Access and backend auth.
- Do not use `STEEL_RAG_ANSWER_AUTH_MODE=local_dev` on a public hostname.
- Do not paste tunnel tokens.
- Do not commit private env files.
- Do not commit Cloudflare credentials.
- Do not commit logs, private transcripts, raw corpus data, Chroma stores, embeddings, or generated corpus outputs.
- Do not run scraping from the private-preview operations flow.
- Do not modify corpus, Chroma, embeddings, or vector data as part of recovery.
