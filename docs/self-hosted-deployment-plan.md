# Self-hosted Deployment Plan

Task mode: GREEN docs-only planning. This plan must not deploy anything, modify DNS, expose Ollama, run scraping, regenerate embeddings, reset Chroma, or modify vector data.

User-facing app name: The Turnaround. Keep `pocketsteel`, `pocket-steel`, and `pocket_steel` as internal technical names.

Current branch when this plan was created: `feature/answer-api`.

## Goal

Prepare a safe self-hosted private-beta path for `steelguitarrag.com` using the Mac mini, local Chroma, local Ollama, and Cloudflare Tunnel without exposing live RAG anonymously and without exposing Ollama directly.

## Architecture

```text
Internet -> Cloudflare Tunnel -> Mac mini app/backend -> local Chroma -> local Ollama
```

Public traffic should terminate at Cloudflare, pass through a Cloudflare Tunnel to a single local app port on the Mac mini, and reach local retrieval/generation only through the app. Chroma and Ollama stay local to the Mac mini. Ollama must only listen on loopback or a private local interface and must not receive public traffic directly.

Key boundaries:

- Cloudflare Tunnel is the only public ingress path.
- The home router should not forward ports for the app, Chroma, SSH, or Ollama.
- `app.steelguitarrag.com` should point to the app service, not to Ollama.
- `api.steelguitarrag.com` is optional and should only exist if the backend is separately authenticated and rate-limited.
- Local Chroma is read-only for serving. Deployment must not run embedding or reset commands.

## Domain Plan

| Hostname | Purpose | Self-hosted recommendation |
| --- | --- | --- |
| `steelguitarrag.com` | Public landing page | Static public page. No live RAG. |
| `www.steelguitarrag.com` | Public landing alias | Redirect to root. No live RAG. |
| `app.steelguitarrag.com` | Private beta app | Cloudflare Tunnel to the Mac mini app/backend port, protected by backend auth and optionally Cloudflare Access. |
| `api.steelguitarrag.com` | Optional later API hostname | Avoid at first. If used later, route only to the authenticated app/backend service, never to Ollama. |

Recommended first beta shape:

- Use `steelguitarrag.com` and `www.steelguitarrag.com` for public-safe landing content.
- Use `app.steelguitarrag.com` for invite-only beta traffic.
- Do not create `api.steelguitarrag.com` until there is a clear need for a separate API origin.
- Keep `/api/answer` same-origin behind the app where possible to reduce CORS and secret-handling complexity.

## GoDaddy-to-Cloudflare Migration Checklist

Current domain state, supplied on 2026-05-28:

- Domain: `steelguitarrag.com`
- Registrar: GoDaddy
- Email: not configured
- Current nameservers:
  - `ns07.domaincontrol.com`
  - `ns08.domaincontrol.com`
- Current visible GoDaddy DNS records:
  - `A @ WebsiteBuilder Site`
  - `CNAME www steelguitarrag.com`
  - `CNAME pay paylinks.commerce.godaddy.com`
  - `CNAME _domainconnect _domainconnect.gd.domaincontrol.com`
  - `TXT _dmarc` DMARC quarantine record
  - no MX records visible

Migration checklist:

- Screenshot or export the existing GoDaddy DNS records before any change.
- Note that no MX records are currently configured, so there is no active domain email routing to preserve at this time.
- Preserve the `_dmarc` TXT record if the domain may later send mail.
- Decide whether to keep or drop GoDaddy-specific records:
  - `A @ WebsiteBuilder Site`: drop only when the Cloudflare landing page or tunnel landing route is ready.
  - `CNAME pay paylinks.commerce.godaddy.com`: keep only if GoDaddy Pay Links are still used.
  - `CNAME _domainconnect _domainconnect.gd.domaincontrol.com`: usually not needed after Cloudflare becomes authoritative unless GoDaddy Domain Connect is still required.
- Add `steelguitarrag.com` to Cloudflare.
- Let Cloudflare scan/import existing DNS records.
- Compare Cloudflare's imported records against the GoDaddy screenshot/export.
- Recreate only the DNS records that are still needed in Cloudflare.
- Receive the assigned Cloudflare nameservers.
- Change GoDaddy nameservers from `ns07.domaincontrol.com` and `ns08.domaincontrol.com` to the assigned Cloudflare nameservers.
- Wait for Cloudflare to confirm the zone is active.
- Do not create public `app` or `api` DNS records until auth, tunnel routing, and backend guardrails are ready.

Initial Cloudflare DNS target state:

| Record | Purpose | Initial recommendation |
| --- | --- | --- |
| Apex/root | Public landing page | Point to the chosen landing page only. No live RAG. |
| `www` | Redirect to root | Configure redirect or CNAME according to the landing setup. |
| `app` | Private beta app | Add only when the Cloudflare Tunnel and auth gates are ready. |
| `api` | Optional later API | Do not add for first beta unless separately approved. |
| `_dmarc` TXT | Mail policy marker | Preserve current quarantine record unless intentionally changed. |

## Cloudflare Tunnel Plan

Cloudflare Tunnel should connect Cloudflare to the local app service on the Mac mini through outbound `cloudflared` connections. Cloudflare's tunnel model avoids opening inbound router ports or exposing the home public IP as the app origin.

Planned ingress:

| Public hostname | Local service target | Protection |
| --- | --- | --- |
| `app.steelguitarrag.com` | `http://127.0.0.1:<APP_PORT>` | Backend auth; optional Cloudflare Access |
| `steelguitarrag.com` | static landing host or `http://127.0.0.1:<LANDING_PORT>` | Public, no live RAG |
| `www.steelguitarrag.com` | redirect/static landing | Public, no live RAG |
| `api.steelguitarrag.com` | optional `http://127.0.0.1:<APP_PORT>` | Hold until separately approved |

Tunnel requirements:

- Create a tunnel public hostname for `app.steelguitarrag.com`.
- Point that public hostname only at the local app/backend port, for example `http://127.0.0.1:<APP_PORT>`.
- Tunnel points only to the local app port.
- No router port forwarding.
- No direct public home IP exposure.
- No tunnel route to `127.0.0.1:11434`.
- No tunnel route to a Chroma port or database process.
- Cloudflare Access protection is optional but recommended for preview and early private beta.
- Use an allowlist policy for beta testers, for example approved emails or identity-provider groups.
- Prefer a deny-by-default Access posture so new hostnames are not accidentally public.
- Keep public landing pages separate from the protected app route.

Cloudflare Access is not a replacement for application auth. The app still needs server-side authorization before live `/api/answer` runs.

## Local Service Plan

### App/API Service Port

Recommended private-beta target:

```text
127.0.0.1:<APP_PORT>
```

Use a single local app/API service bound to loopback. The repo's local API default is `127.0.0.1:8765`; the same-origin smoke server examples use `8770`. Choose one beta app port and point Cloudflare Tunnel only to that port.

Do not bind the beta app to `0.0.0.0` unless there is a separate local firewall rule and a clear reason. Loopback binding is the safer default with Cloudflare Tunnel running on the same Mac mini.

Candidate app service command, to be finalized before beta:

```text
cd /Users/cory/Documents/Pocket\ Steel
source .venv/bin/activate
STEEL_RAG_CHROMA_PATH=<approved local Chroma path> \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified \
STEEL_RAG_ANSWER_PROVIDER=ollama \
STEEL_RAG_CHAT_MODEL=<approved local Ollama chat model> \
OLLAMA_URL=http://127.0.0.1:11434 \
python rag_api.py --host 127.0.0.1 --port <APP_PORT>
```

This command is a planning placeholder. It should not be used for public beta until `/api/answer` enforces server-side auth and anonymous requests fail.

### Ollama

Recommended local URL:

```text
http://127.0.0.1:11434
```

Set:

```text
OLLAMA_URL=http://127.0.0.1:11434
```

Ollama requirements:

- Ollama must stay local/private.
- Do not expose `11434` through Cloudflare Tunnel.
- Do not port-forward `11434` on the router.
- Do not place Ollama credentials, model names that imply private data, or raw prompt traces in browser-visible code.
- Keep model selection server-side with `STEEL_RAG_CHAT_MODEL`.

### Chroma

Use the existing local Chroma path and collection. Current repo defaults and documented examples include:

```text
STEEL_RAG_CHROMA_PATH=rag-data/electronics/chroma
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified
```

If the production beta uses the external unified corpus path from local docs, set it explicitly, for example:

```text
STEEL_RAG_CHROMA_PATH=/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified
```

Serving requirements:

- Treat Chroma as read-only for the app service.
- Do not run `rag_embed_chroma.py` as part of startup.
- Do not reset or overwrite the vector store.
- Back up the Chroma directory before any future migration.

### Environment Variables

Minimum planned environment:

```text
STEEL_RAG_CHROMA_PATH=<approved local Chroma path>
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified
STEEL_RAG_ANSWER_PROVIDER=ollama
STEEL_RAG_CHAT_MODEL=<approved local Ollama chat model>
OLLAMA_URL=http://127.0.0.1:11434
APP_HOST=127.0.0.1
APP_PORT=<approved local app port>
```

Future auth/rate-limit environment should include provider IDs, issuer/audience values, signing secrets, and limit settings, but those must stay server-side and out of browser bundles.

### Startup Plan

Use `launchctl` on macOS for both long-running processes:

- `cloudflared` tunnel service.
- The Turnaround app/API service.

Startup requirements:

- Start Ollama locally before the app if the app uses `STEEL_RAG_ANSWER_PROVIDER=ollama`.
- Start the app bound to `127.0.0.1`.
- Start `cloudflared` after the app, or rely on health checks while the app comes up.
- Keep service definitions outside the repo if they contain absolute private paths or secrets.
- Do not put Cloudflare tunnel credentials in committed files.

Recommended launch service shape:

- `com.steelguitarrag.app.plist`: starts the app/backend on `127.0.0.1:<APP_PORT>`.
- `com.steelguitarrag.cloudflared.plist`: starts the named Cloudflare Tunnel.
- Service files should write stdout/stderr to the log paths below.
- Service files should not be committed if they contain private paths, tokens, or user-specific configuration.

### Log Locations

Recommended local log locations:

```text
~/Library/Logs/steel-guitar-rag/app.log
~/Library/Logs/steel-guitar-rag/app-error.log
~/Library/Logs/steel-guitar-rag/cloudflared.log
~/Library/Logs/steel-guitar-rag/ollama.log
```

Log requirements:

- Record request ID, route, status, latency, auth decision, and rate-limit decision.
- Avoid storing full private beta question text unless a retention policy is approved.
- Never log API secrets, auth tokens, Cloudflare service tokens, or raw model prompts with private user data.

## Security Requirements

Required before `app.steelguitarrag.com` reaches beta testers:

- `/api/answer` enforces auth server-side.
- Anonymous users are blocked from live RAG with a non-200 auth response.
- Backend role checks allow only approved beta users and admins.
- Cloudflare Access protects the beta hostname during preview and private beta.
- Usage limits exist per user and per time window.
- Rate limits exist at Cloudflare and/or the app layer.
- Request logging is active.
- Browser-side code contains no model/API secrets.
- Ollama is not public, proxied, tunneled, or port-forwarded.
- Prompt-injection protections remain active for user questions and retrieved source text.
- Retrieved sources are sanitized before answer generation.
- CORS allows only approved origins if a separate API hostname is introduced.
- Error responses do not expose filesystem paths, Chroma paths, local usernames, stack traces, tunnel credentials, or model internals.
- Source/copyright policy page is visible before beta invites go out.
- Admin/debug endpoints are unavailable publicly unless separately protected.

Cloudflare Access reduces accidental exposure, but it is not enough by itself. The backend must independently reject unauthenticated `/api/answer` calls.

Prompt-injection guardrails:

- Keep prompt-injection detection active for user questions.
- Sanitize retrieved source text before it reaches the answer provider.
- Treat retrieved text as evidence, not instructions.
- Keep system/developer prompts server-side.
- Do not allow user input to choose the Ollama URL, model endpoint, Chroma path, or auth role.

## Operational Requirements

### Mac mini Readiness

- Disable Mac sleep while allowing display sleep if desired.
- Configure automatic restart after power failure.
- Keep macOS, Ollama, `cloudflared`, Python, and dependencies patched on a controlled schedule.
- Use a dedicated macOS user account for the service if possible.
- Keep FileVault and strong login credentials enabled.
- Avoid using the beta host for unrelated public services.

### Power and Network

- UPS recommended for the Mac mini and network gear.
- Document ISP/router restart behavior.
- Do not depend on a static home IP because Cloudflare Tunnel should hide origin IP changes.
- Monitor tunnel connectivity from Cloudflare and from an external health check.

### Restart Instructions

Document exact restart steps before beta:

- Restart the app service.
- Restart Ollama.
- Restart `cloudflared`.
- Verify local health endpoint.
- Verify `app.steelguitarrag.com` through Cloudflare Access.
- Confirm anonymous `/api/answer` remains blocked.

The restart runbook should be written after the actual service names and ports are chosen.

Candidate restart commands, to be finalized after service names are chosen:

```text
launchctl kickstart -k gui/$(id -u)/com.steelguitarrag.app
launchctl kickstart -k gui/$(id -u)/com.steelguitarrag.cloudflared
```

If services are installed as system daemons instead of user agents, use the matching `system/` launchctl target and document the exact labels.

### Backup Plan

Back up:

- App configuration that does not contain secrets.
- Launch service definitions with secrets redacted.
- Approved Chroma vector store directory.
- Source policy/copyright docs and metadata.
- Cloudflare Tunnel configuration metadata.

Do not back up into committed repo paths:

- raw private transcripts
- auth tokens
- Cloudflare credentials
- raw logs with user questions
- Chroma mutation snapshots created accidentally during service startup

Backup cadence:

- Chroma: before any approved migration or app config change that points at a different index.
- App config: after each approved deployment configuration change.
- Logs: rotate locally and retain only as approved.

### Rollback Plan

Fast rollback order:

1. Disable Cloudflare Access policy access or remove beta users from the allowlist.
2. Stop the Cloudflare Tunnel route for `app.steelguitarrag.com`.
3. Stop the local app service.
4. Keep Ollama local; do not expose it for debugging.
5. Restore previous app release/config if needed.
6. Restore previous Chroma directory only if a separately approved migration changed the served index.

DNS rollback:

- If authoritative DNS moved to Cloudflare, leave nameservers alone during an app incident and disable the tunnel/app route instead.
- If a bad DNS change caused exposure, restore the previous DNS record from the captured zone export.
- Preserve MX/email records during any rollback.

### Monitoring and Health Check

Minimum health checks:

- Local app health endpoint that does not touch live RAG.
- Cloudflare Tunnel status.
- External check for landing page.
- Authenticated check for beta app shell.
- Explicit negative check that anonymous `/api/answer` fails.
- Local Ollama health check from the Mac mini only.

Alerts should cover:

- tunnel disconnected
- app service down
- repeated 5xx responses
- repeated auth failures
- rate-limit spikes
- disk space low
- Chroma path missing or unreadable
- Ollama unavailable

## Staged Rollout

### Stage 1: Local Only

- Run the app on `127.0.0.1`.
- Confirm Chroma reads from the approved local path.
- Confirm Ollama answers only through `http://127.0.0.1:11434`.
- Confirm anonymous `/api/answer` is blocked server-side.
- Confirm no scraping, embedding, or Chroma writes occur during startup.

### Stage 2: Cloudflare Tunnel Preview Behind Access

- Create a tunnel route to the local app port only.
- Protect `app.steelguitarrag.com` with Cloudflare Access.
- Allow only owner/developer accounts.
- Verify no router ports are open.
- Verify `11434` is not tunneled or reachable.

### Stage 3: Private Beta Allowlist

- Add approved beta users to Cloudflare Access and app-level auth.
- Enable usage limits and logging.
- Publish source/copyright policy.
- Monitor logs daily during early beta.
- Keep `api.steelguitarrag.com` disabled unless a separate approval creates it.

### Stage 4: Public Landing Page

- Publish `steelguitarrag.com` and `www.steelguitarrag.com` with public-safe content.
- Include waitlist/contact and source/copyright policy.
- Do not expose live answers from the landing page.

### Stage 5: Wider Beta Later

- Review beta usage, copyright/source policy, support load, and failure modes.
- Expand allowlist only after auth, limits, monitoring, and rollback are proven.
- Consider separate `api` hostname only when there is a real integration need.

## Pre-launch Checklist

- [ ] Answer eval is passing against the intended local service path.
- [ ] Backend auth/access control is working.
- [ ] Anonymous users are blocked from `/api/answer` server-side.
- [ ] Cloudflare Access policy is configured if used for preview/private beta.
- [ ] Rate limits are configured.
- [ ] Request logging is configured.
- [ ] Landing page is ready and contains no live RAG access.
- [ ] Source/copyright policy page is ready and linked from the landing page.
- [ ] Ollama is reachable only locally at `http://127.0.0.1:11434`.
- [ ] `app.steelguitarrag.com` routes only to the app/backend port.
- [ ] Router has no port forwarding for app, Ollama, Chroma, or SSH.
- [ ] Mac mini sleep is disabled.
- [ ] Log directory exists and log rotation/retention is decided.
- [ ] Restart commands are documented with real launchctl service labels.
- [ ] Backup plan is documented and tested for config and Chroma.
- [ ] Rollback plan is documented.
- [ ] GoDaddy DNS screenshot/export is captured.
- [ ] Cloudflare imported DNS records are reviewed before nameserver change.
- [ ] No scraping command is part of service startup.
- [ ] No embedding command is part of service startup.
- [ ] Chroma is not reset or modified by deployment.

## Human Decisions Still Needed

- Whether to move authoritative DNS from GoDaddy nameservers to Cloudflare.
- Who owns and approves GoDaddy DNS changes.
- Whether to preserve the GoDaddy `pay` CNAME.
- Whether to preserve the GoDaddy `_domainconnect` CNAME after Cloudflare becomes authoritative.
- Whether to preserve the current `_dmarc` quarantine TXT record exactly.
- Whether the landing page is served by Cloudflare Pages or through the Mac mini tunnel.
- Which hostname is first: public landing apex or protected `app`.
- Which local app server entrypoint will serve private beta traffic.
- Approved local app port.
- Approved Chroma path and collection for beta.
- Approved Ollama chat model.
- Whether `STEEL_RAG_ANSWER_PROVIDER=ollama` is ready for beta or should remain deterministic until answer quality is reviewed.
- Auth provider and beta identity source.
- Cloudflare Access policy shape and allowlist owners.
- App-level role model and enforcement details.
- Usage limits per user/day and per user/month.
- Log retention period and whether full question text may ever be stored.
- Source/copyright policy owner and final public copy.
- Backup location and retention.
- Monitoring destination and alert recipient.
- Whether `api.steelguitarrag.com` should exist at all for the private beta.

## Pre-launch Blockers

- Backend auth for `/api/answer` is not optional.
- Anonymous live RAG access must fail server-side.
- Cloudflare Access or equivalent preview protection must be in place until app auth is proven.
- Ollama must not be publicly reachable.
- Chroma must stay local and read-only for serving.
- No DNS changes until GoDaddy records are captured and the no-MX email state is confirmed.
- No beta invites until logging, rate limits, rollback, and source/copyright policy are ready.

## References

- Cloudflare Tunnel: https://developers.cloudflare.com/tunnel/
- Cloudflare Tunnel routing: https://developers.cloudflare.com/tunnel/routing/
- Cloudflare Access self-hosted applications: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/choose-application-type/
- Cloudflare Access default protection: https://developers.cloudflare.com/cloudflare-one/access-controls/access-settings/require-access-protection/
- GoDaddy nameservers: https://www.godaddy.com/help/find-my-godaddy-nameservers-12318
- GoDaddy DNS records: https://www.godaddy.com/help/manage-dns-records-680
