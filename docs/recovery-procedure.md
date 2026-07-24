# Recovery Procedure

Last verified: 2026-07-13

Use this procedure for a failed application release, unavailable origin,
authentication regression, Explorer asset failure, or Interest-Digest issue.
It intentionally avoids destructive Git actions and data deletion.

## 1. Contain And Classify

- Record current `git rev-parse HEAD`, local `/api/version`, service health,
  exact URL, and UTC/local time.
- Decide whether the incident is application runtime, Access/Tunnel, static
  assets, retrieval/provider, or Interest-Digest delivery.
- Do not print secrets, request bodies, private sources, JWTs, or PII.
- If unauthorized content is reachable, disable the affected ingress before
  further diagnosis.
- If digest delivery is ambiguous, stop manual retries and preserve D1 state.

## 2. Application Recovery

Inspect without changing state:

```bash
git status --short
git rev-parse HEAD
curl --fail --silent --show-error http://127.0.0.1:8770/health/live
curl --fail --silent --show-error http://127.0.0.1:8770/health/ready
curl --fail --silent --show-error http://127.0.0.1:8770/api/version
```

If the intended commit is healthy locally but not through Cloudflare, inspect
Access/Tunnel status without exposing token-bearing command output.

For a bad code release, create a normal revert commit for the smallest scoped
commit, run its focused tests plus the full suite, then restart:

```bash
git revert <bad-commit>
.venv/bin/pytest -q
npm run check:js
STEEL_RAG_REPO_DIR="$HOME/.steel-rag/releases/<short-sha>" \
STEEL_RAG_DATA_DIR="$HOME/Documents/Steel Guitar RAG" \
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

Do not use `git reset --hard`, `git checkout --`, `git clean`, or delete dirty
files. Verify `/api/version` matches the new revert commit, then run protected
browser smoke.

## 3. Static Explorer Recovery

- Confirm the manifest and requested chunk return 200 with the expected cache
  validators.
- Confirm the browser reports `data-explorer-data-mode="lazy"`.
- Rebuild chunks only from the reviewed generator and source already in the
  approved scope; do not modify corpus/vector data.
- Do not re-enable the retired monolithic runtime fallback as a quick fix.

## 4. Authentication Recovery

- Confirm production config explicitly selects `cloudflare_access`.
- Verify issuer, audience, and JWKS variable presence without printing values.
- Confirm anonymous content routes return 401 and unallowed identities return
  403 before request processing.
- If credentials may be exposed, rotate them in Cloudflare and update only the
  private external environment or secret store.
- Never weaken production auth to restore availability.

## 5. Interest-Digest Recovery

- Stop invoking `/run` when a delivery is `ambiguous`.
- Inspect delivery/part status by identifiers, hashes, attempts, timestamps,
  and error classes; avoid exporting submission content.
- Retry only parts that D1 records as unsent and definitely failed.
- Roll back to a previously active Worker version if needed. The additive D1
  tables may remain; do not drop them or delete sent-part history.
- Verify the Cron schedule and run Worker-runtime tests before resuming.

## 6. Recovery Acceptance

- Local liveness and readiness pass.
- `/api/version` matches the reviewed recovery HEAD.
- Anonymous content access fails closed.
- Authenticated Chat, Explorer, Melody Studio, and Lessons browser smoke passes
  at one exact cache-busted URL.
- Explorer uses lazy chunks, not the monolith.
- Worker tests pass and no duplicate notification was sent.
- A handoff records the incident, checks, rollback/revert commit, exact URL,
  remaining risk, and user-smoke readiness.
