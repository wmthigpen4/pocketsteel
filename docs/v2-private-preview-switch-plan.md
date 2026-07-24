# V2 Private Preview Switch And Rollback Plan

> Historical completed switch record. Use `docs/architecture.md`,
> `docs/private-preview-operations.md`, and
> `docs/handoffs/task-completions/integration-status.md` for current state.

Task mode: GREEN docs-only switch plan. This document must not deploy, change
DNS, modify Chroma, regenerate embeddings, switch app config, run scraping, or
expose Ollama or Chroma.

Current branch when this plan was written: `feature/answer-api`.

## Switch Status

Status: completed successfully.

Recorded: `2026-05-28 22:43:14 CDT`.

The controlled switch of `app.steelguitarrag.com` to the v2 rerank process on
`127.0.0.1:8770` passed human smoke testing.

Current private-preview process:

- V2 Chroma path: `corpus-v2/vector-stores/chroma`
- Collection: `steel_guitar_unified_v2`
- Auth provider: production Cloudflare Access
- Host: `127.0.0.1`
- Port: `8770`

Smoke questions passed:

- Where can I buy a slide bar?
- Is Mullen or MSA better?
- Who is Buddy Emmons?
- What does A+F do?
- How do I use the 9th string?
- Why does my amp buzz at idle?

Remaining caution:

- No outside testers yet until the v2 private-preview process runs cleanly for a
  bit.
- Keep the v1 rollback command ready.
- Do not expose Ollama or Chroma.
- Do not change DNS.

## Goal

Switch `app.steelguitarrag.com` from the current v1 private-preview process to
the v2 Chroma/rerank process only after local and Access-protected smoke checks
are ready, with a fast rollback path back to v1.

No outside testers should be invited until post-switch smoke passes.

## Current Assumptions

- `app.steelguitarrag.com` still routes through Cloudflare Tunnel to
  `127.0.0.1:8770`.
- The tunnel route does not change.
- Cloudflare DNS does not change.
- Only the local app process on port `8770` changes.
- Ollama stays local-only.
- Chroma stays local-only.
- Existing v1 private-preview config remains the rollback target.
- V2 local smoke on port `8781` has passed before this switch is attempted.

## Current V1 Private-Preview Startup Command

This is the known rollback command for the current v1 private preview:

```bash
cd ~/Documents/Steel\ Guitar\ RAG
source .venv/bin/activate
set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
.venv/bin/python scripts/serve_answer_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Required v1 env values:

```text
STEEL_RAG_AUTH_PROVIDER=cloudflare_access
STEEL_RAG_ANSWER_AUTH_MODE=production
STEEL_RAG_CF_ACCESS_ISSUER=<Cloudflare Access issuer>
STEEL_RAG_CF_ACCESS_AUD=<Cloudflare Access AUD tag>
STEEL_RAG_CF_ACCESS_JWKS_URL=<Cloudflare Access JWKS URL>
STEEL_RAG_BETA_USER_EMAILS=<comma-separated tester emails>
STEEL_RAG_ADMIN_EMAILS=<comma-separated admin emails>
STEEL_RAG_CHROMA_PATH=~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified
OLLAMA_URL=http://127.0.0.1:11434
```

## V2 Local Smoke Startup Command

Use this only for loopback smoke testing on `127.0.0.1:8781`. This command keeps
local-dev mock access enabled and must not be routed publicly:

```bash
cd ~/Documents/Steel\ Guitar\ RAG
source .venv/bin/activate

PYTHONPATH=. \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8781 \
  --answer-auth-mode local_dev \
  --auth-provider scaffold \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2
```

## Proposed V2 Private-Preview Startup Command

`scripts/serve_v2_rerank_smoke.py` now supports production Cloudflare Access
auth. Do not route `app.steelguitarrag.com` to this process unless it is started
with production auth and Cloudflare Access provider settings.

```bash
cd ~/Documents/Steel\ Guitar\ RAG
source .venv/bin/activate
set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_CHROMA_PATH="~/Documents/Steel Guitar RAG/corpus-v2/vector-stores/chroma" \
STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified_v2" \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --candidate-k 20 \
  --min-excerpt-chars 80 \
  --question-only-penalty 0.12 \
  --mention-only-penalty 0.20 \
  --answer-advice-boost 0.04 \
  --quality-boost 0.04 \
  --quality-threshold 0.70 \
  --noise-penalty 0.06 \
  --noise-threshold 0.60
```

Pre-switch check: confirm this command path enforces
`STEEL_RAG_ANSWER_AUTH_MODE=production` and
`STEEL_RAG_AUTH_PROVIDER=cloudflare_access`. If it accepts local mock access
such as `?access=beta_user`, do not use it for the private-preview route.

## Required Env Vars

Cloudflare Access auth:

```text
STEEL_RAG_AUTH_PROVIDER=cloudflare_access
STEEL_RAG_ANSWER_AUTH_MODE=production
STEEL_RAG_CF_ACCESS_ISSUER=<Cloudflare Access issuer>
STEEL_RAG_CF_ACCESS_AUD=<Cloudflare Access AUD tag>
STEEL_RAG_CF_ACCESS_JWKS_URL=<Cloudflare Access JWKS URL>
STEEL_RAG_BETA_USER_EMAILS=<comma-separated tester emails>
STEEL_RAG_ADMIN_EMAILS=<comma-separated admin emails>
```

V2 Chroma:

```text
STEEL_RAG_CHROMA_PATH=~/Documents/Steel Guitar RAG/corpus-v2/vector-stores/chroma
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2
```

Local Ollama:

```text
OLLAMA_URL=http://127.0.0.1:11434
```

Rerank settings:

```text
candidate_k=20
min_excerpt_chars=80
dedupe_thread=true
question_only_penalty=0.12
mention_only_penalty=0.20
answer_advice_boost=0.04
quality_boost=0.04
quality_threshold=0.70
noise_penalty=0.06
noise_threshold=0.60
```

## Port And Tunnel Assumptions

- `app.steelguitarrag.com` continues routing to `127.0.0.1:8770`.
- The Cloudflare Tunnel public hostname is not recreated during the switch.
- No router port forwarding is added.
- No public home IP exposure is added.
- No direct Ollama route is added.
- No direct Chroma route is added.
- The root landing page remains separate from the private-preview app.

## Pre-Switch Checks

Before stopping v1:

1. Save the v1 rollback command from this document in the active terminal notes.
2. Confirm v2 smoke on `127.0.0.1:8781` passed.
3. Confirm the v2 smoke used:

   ```text
   corpus-v2/vector-stores/chroma
   steel_guitar_unified_v2
   candidate_k=20
   min_excerpt_chars=80
   dedupe_thread=true
   question_only_penalty=0.12
   mention_only_penalty=0.20
   answer_advice_boost=0.04
   quality_boost=0.04
   quality_threshold=0.70
   noise_penalty=0.06
   noise_threshold=0.60
   ```

4. Confirm the v2 private-preview serving path is started with:

   ```text
   --answer-auth-mode production
   --auth-provider cloudflare-access
   ```

   It must not rely on local mock access.
5. Confirm local anonymous `/api/answer` remains `401 Unauthorized`:

   ```bash
   curl -sS -i \
     -X POST http://127.0.0.1:8770/api/answer \
     -H "Content-Type: application/json" \
     --data '{"question":"Who is Buddy Emmons?","mode":"general"}'
   ```

6. Confirm `/api/session` does not expose the user's email in the response body:

   ```bash
   curl -sS http://127.0.0.1:8770/api/session
   ```

7. Confirm the response reports anonymous status without a Cloudflare Access
   token.
8. Confirm no outside testers are using the preview during the switch window.

## Switch Steps

1. Stop the current v1 process on port `8770`:

   ```bash
   lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill
   ```

2. Confirm nothing is listening on `8770`:

   ```bash
   lsof -nP -iTCP:8770 -sTCP:LISTEN
   ```

3. Start the v2/rerank process on `127.0.0.1:8770` using the approved
   production-auth v2 command.
4. Verify local `8770`:

   ```bash
   curl -sS http://127.0.0.1:8770/api/session
   ```

5. Verify local anonymous `/api/answer` remains blocked:

   ```bash
   curl -sS -i \
     -X POST http://127.0.0.1:8770/api/answer \
     -H "Content-Type: application/json" \
     --data '{"question":"Where can I buy a slide bar?","mode":"general"}'
   ```

   Expected result: `401 Unauthorized`.

6. Verify the Cloudflare Access route:

   ```bash
   curl -sS -I https://app.steelguitarrag.com
   ```

   Expected unauthenticated result: Cloudflare Access redirect, denial, or
   challenge. It must not return the app directly to an anonymous browser.

7. Sign in through Cloudflare Access with an allowlisted tester/admin email.
8. Confirm `/api/session` reports authenticated access without leaking email in
   the visible UI.
9. Run the post-switch smoke questions below.

## Post-Switch Smoke Questions

Ask these through the Access-authenticated app only:

- Where can I buy a slide bar?
- Is Mullen or MSA better?
- Who is Buddy Emmons?
- What does A+F do?
- How do I use the 9th string?
- Why does my amp buzz at idle?

Pass criteria:

- Answer body is readable and not raw forum junk.
- Source cards are relevant.
- Source cards show clean thread/source metadata.
- No local-dev mock access is required.
- Anonymous or missing-token `/api/answer` still fails.

## Rollback

If any stop condition triggers, roll back immediately.

1. Stop the v2 process on `8770`:

   ```bash
   lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill
   ```

2. Restart v1 on `8770`:

   ```bash
   cd ~/Documents/Steel\ Guitar\ RAG
   source .venv/bin/activate
   set -a
   source ~/.steel-rag/env/private-preview.env
   set +a

   PYTHONPATH=. \
   .venv/bin/python scripts/serve_answer_smoke.py \
     --host 127.0.0.1 \
     --port 8770 \
     --answer-auth-mode production \
     --auth-provider cloudflare-access
   ```

3. Verify local v1:

   ```bash
   curl -sS http://127.0.0.1:8770/api/session
   ```

4. Verify anonymous `/api/answer` still fails:

   ```bash
   curl -sS -i \
     -X POST http://127.0.0.1:8770/api/answer \
     -H "Content-Type: application/json" \
     --data '{"question":"Who is Buddy Emmons?","mode":"general"}'
   ```

5. Verify the app route still goes through Cloudflare Access:

   ```bash
   curl -sS -I https://app.steelguitarrag.com
   ```

6. Keep the public landing page live. Do not change root-domain routing during
   rollback.

## Stop Conditions

Stop the switch and roll back if any of these happen:

- Source cards regress.
- Answer body shows raw forum junk.
- Auth/session fails.
- Cloudflare returns `502` for `app.steelguitarrag.com`.
- Local anonymous access to `/api/answer` succeeds.
- `/api/session` leaks email in a place intended to be hidden.
- The v2 process requires or accepts local mock access on the public route.
- Ollama or Chroma appears reachable directly.

## Outside Tester Gate

No outside testers until all post-switch smoke questions pass through
Cloudflare Access, anonymous `/api/answer` remains blocked, and rollback has
been tested or rehearsed from the saved command.
