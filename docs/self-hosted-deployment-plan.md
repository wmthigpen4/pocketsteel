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

## Current DNS Status

Current domain state on 2026-05-28:

- Domain: `steelguitarrag.com`
- Registrar: GoDaddy
- Email: not configured
- Previous GoDaddy nameservers:
  - `ns07.domaincontrol.com`
  - `ns08.domaincontrol.com`
- New Cloudflare nameservers:
  - `derek.ns.cloudflare.com`
  - `vita.ns.cloudflare.com`
- Current public NS lookup shows:
  - `derek.ns.cloudflare.com`
  - `vita.ns.cloudflare.com`

GoDaddy remains the registrar. Cloudflare is now the DNS control plane for the zone. Continue to treat routing as not launched until the landing page and private beta guardrails are ready.

No MX records were visible in GoDaddy, and email is not configured, so there are no existing domain email routes to preserve. If email is added later, create MX, SPF, DKIM, and DMARC records intentionally in Cloudflare.

## Current Cloudflare DNS Records

Current Cloudflare DNS export for `steelguitarrag.com`:

- `NS derek.ns.cloudflare.com`
- `NS vita.ns.cloudflare.com`
- `A @ 13.248.243.5`
- `A @ 76.223.105.230`
- `CNAME www steelguitarrag.com`
- `CNAME pay paylinks.commerce.godaddy.com`
- `CNAME _domainconnect _domainconnect.gd.domaincontrol.com`
- `TXT _dmarc` DMARC quarantine record
- no MX records

The apex/root A records `13.248.243.5` and `76.223.105.230` appear to be imported GoDaddy/WebsiteBuilder-style records. They are not the Mac mini app, not Cloudflare Tunnel, and not the live RAG backend.

Current issue: root `steelguitarrag.com` still shows the imported GoDaddy "Launching Soon" placeholder because the Cloudflare apex A records still point to:

- `13.248.243.5`
- `76.223.105.230`

Those records should remain untouched until a public-safe landing-page target is ready.

## Recommended Near-term DNS Plan

- `steelguitarrag.com`:
  - Eventually point root to the public landing page.
  - Do not point root to the live RAG app.
  - Remove or replace the imported GoDaddy/WebsiteBuilder-style A records only after the landing page target is chosen.
- `www.steelguitarrag.com`:
  - Redirect to root or CNAME to the landing-page target according to the chosen landing setup.
  - Keep it public-safe with no live RAG access.
- `app.steelguitarrag.com`:
  - Later point to the Cloudflare Tunnel public hostname for the Mac mini app/backend.
  - Do not create or route this hostname until server-side `/api/answer` auth is enforced and tested.
- `api.steelguitarrag.com`:
  - Keep disabled for the first beta unless separately approved.
  - If introduced later, route only to the authenticated backend, never to Ollama.

## Public Landing Page Route

Recommended target:

| Hostname | Target behavior |
| --- | --- |
| `steelguitarrag.com` | Public landing page only |
| `www.steelguitarrag.com` | Redirect or CNAME to root |
| `app.steelguitarrag.com` | Protected private beta app only |

Landing-page options:

- Cloudflare Pages static landing page:
  - Recommended root-domain approach for the first public route.
  - Keeps public landing content separate from the Mac mini private beta app.
  - Avoids routing root traffic to the home network.
  - Should contain only public-safe copy, waitlist/contact path, and source/copyright policy links.
- Self-hosted landing-only route through Cloudflare Tunnel:
  - Acceptable if the landing page must be served from the Mac mini.
  - Must be a separate landing-only service or route that cannot reach live `/api/answer`.
  - Must not expose Ollama, Chroma, or the private beta app.
  - Adds operational dependency on the Mac mini for the public root domain.

Recommended root-domain landing approach: use Cloudflare Pages for `steelguitarrag.com` and redirect `www.steelguitarrag.com` to root. Keep `app.steelguitarrag.com` separate for the protected private beta app.

DNS changes needed later:

- Remove or replace `A @ 13.248.243.5`.
- Remove or replace `A @ 76.223.105.230`.
- Add the Cloudflare Pages-required root record or Cloudflare-managed Pages binding for `steelguitarrag.com`.
- Update `www` to redirect or CNAME to the chosen root landing target.

Do not make those DNS changes until the landing page target is ready and reviewed.

Landing guardrails:

- Root domain must not expose live RAG.
- Root domain must not proxy `/api/answer`.
- `/api/answer` must remain protected behind private beta auth.
- Ollama must remain private.
- Chroma must remain private.
- Public landing content must not include secrets, private local paths, raw data, or private beta URLs that bypass Access.

## Records to Review Before Launch

- `pay`:
  - Decide whether to remove `CNAME pay paylinks.commerce.godaddy.com`.
  - Keep it only if GoDaddy Pay Links are still needed.
- `_domainconnect`:
  - Decide whether to remove `CNAME _domainconnect _domainconnect.gd.domaincontrol.com`.
  - Usually remove after Cloudflare is authoritative unless GoDaddy Domain Connect is still required.
- `_dmarc`:
  - Decide whether to keep the current DMARC quarantine record before email exists.
  - Keeping it is reasonable as a conservative mail-policy placeholder, but future email setup should revisit SPF, DKIM, DMARC, and MX together.
- MX/email:
  - No MX records are currently configured; there are no active email records to preserve.

## Next Cloudflare Tasks

- Confirm the Cloudflare zone is active and serving the exported records.
- Review the imported apex/root, `www`, `pay`, `_domainconnect`, and `_dmarc` records.
- Remove or replace the imported GoDaddy/WebsiteBuilder-style apex A records only after the landing page routing is chosen.
- Decide whether to keep `pay`, `_domainconnect`, and `_dmarc`.
- Create landing page routing later for `steelguitarrag.com` and `www.steelguitarrag.com`.
- Create an `app.steelguitarrag.com` Cloudflare Tunnel route only after auth guardrails are implemented and verified.
- Do not create `api.steelguitarrag.com` for the first beta unless separately approved.

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
- Do not route `app.steelguitarrag.com` to the Mac mini until server-side `/api/answer` auth is enforced.
- Tunnel points only to the local app port.
- No router port forwarding.
- No direct public home IP exposure.
- No tunnel route to `127.0.0.1:11434`.
- No tunnel route to a Chroma port or database process.
- No public Ollama.
- No public Chroma.
- The backend app calls Ollama locally through `OLLAMA_URL=http://127.0.0.1:11434`.
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
- `/api/answer` is not exposed publicly until server-side auth is implemented and tested.
- Backend role checks allow only approved beta users and admins.
- Cloudflare Access protects the beta hostname during preview and private beta if used; otherwise an equivalent preview gate is required until app auth is proven.
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

Cloudflare Security Insights hardening note:

- Finding: Low severity configuration suggestion, "Review unwanted AI crawlers with AI Labyrinth."
- Recommended action: enable AI Labyrinth.
- This is a low-severity hardening item, not a blocker for private preview.
- It may be useful for the public landing page later, especially once `steelguitarrag.com` serves public content.
- AI Labyrinth is not a replacement for Cloudflare Access, backend `/api/answer` auth, rate limits, request logging, or keeping Ollama and Chroma private.

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
- [ ] `app.steelguitarrag.com` is not routed to the Mac mini until `/api/answer` has server-side auth.
- [ ] Router has no port forwarding for app, Ollama, Chroma, or SSH.
- [ ] Mac mini sleep is disabled.
- [ ] Log directory exists and log rotation/retention is decided.
- [ ] Restart commands are documented with real launchctl service labels.
- [ ] Backup plan is documented and tested for config and Chroma.
- [ ] Rollback plan is documented.
- [ ] Cloudflare zone is active after nameserver change.
- [ ] Cloudflare DNS records are reviewed against the current export.
- [ ] Imported GoDaddy/WebsiteBuilder-style apex A records are removed or replaced only after the landing page target is chosen.
- [ ] Root landing page target is reviewed and contains no live RAG access.
- [ ] Root landing page route does not proxy `/api/answer`.
- [ ] No scraping command is part of service startup.
- [ ] No embedding command is part of service startup.
- [ ] Chroma is not reset or modified by deployment.

## Human Decisions Still Needed

- Whether to preserve the GoDaddy `pay` CNAME.
- Whether to preserve the GoDaddy `_domainconnect` CNAME after Cloudflare becomes authoritative.
- Whether to preserve the current `_dmarc` quarantine TXT record exactly.
- Whether the landing page is served by Cloudflare Pages or through the Mac mini tunnel.
- Whether to use Cloudflare Pages for the recommended root-domain landing route.
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
- Live RAG must not be exposed publicly until `/api/answer` is protected server-side.
- Cloudflare Access or equivalent preview protection must be in place until app auth is proven.
- Ollama must not be publicly reachable.
- Chroma must stay local and read-only for serving.
- Do not route `app.steelguitarrag.com` to the Mac mini until server-side `/api/answer` auth is enforced.
- Do not replace the imported GoDaddy/WebsiteBuilder apex A records until the public landing page target is ready.
- Do not route root `steelguitarrag.com` to any service that exposes live `/api/answer`.
- No beta invites until logging, rate limits, rollback, and source/copyright policy are ready.

## References

- Cloudflare Tunnel: https://developers.cloudflare.com/tunnel/
- Cloudflare Tunnel routing: https://developers.cloudflare.com/tunnel/routing/
- Cloudflare Access self-hosted applications: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/choose-application-type/
- Cloudflare Access default protection: https://developers.cloudflare.com/cloudflare-one/access-controls/access-settings/require-access-protection/
- GoDaddy nameservers: https://www.godaddy.com/help/find-my-godaddy-nameservers-12318
- GoDaddy DNS records: https://www.godaddy.com/help/manage-dns-records-680
