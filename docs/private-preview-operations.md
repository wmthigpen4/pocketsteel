# Private Preview Operations Runbook

Last verified: 2026-07-13

This is the canonical application runbook. It covers the protected Mac mini
preview and its separately deployed Interest-Digest Worker. It does not
authorize DNS changes, corpus/vector mutation, scraping, or secret disclosure.

## Service Topology

```text
app.steelguitarrag.com
  -> Cloudflare Access
  -> Cloudflare Tunnel
  -> system/com.steelguitarrag.private-preview
  -> http://127.0.0.1:8770
```

Only the application port is tunneled. Do not expose Ollama, Chroma, database
files, or router ports.

The LaunchDaemon reads the non-repository environment file at
`~/.steel-rag/env/private-preview.env`. Never print, copy into a handoff, or
commit that file. Production startup must specify:

```text
STEEL_RAG_AUTH_PROVIDER=cloudflare_access
STEEL_RAG_ANSWER_AUTH_MODE=production
```

The environment also supplies Access issuer/audience/JWKS settings, allowlists,
retrieval paths, and provider configuration. Validate names and presence only;
do not echo values.

## Install Or Update The LaunchDaemon

The installer manages the daemon-safe wrapper and plist. Installation or load
may require an administrator password:

```bash
deploy/macos/install-private-preview-launchdaemon.sh render > /tmp/com.steelguitarrag.private-preview.plist
plutil -lint /tmp/com.steelguitarrag.private-preview.plist
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh load
```

Do not put secret values in the rendered plist.

## Restart After A Committed Runtime Change

Prefer the documented wrapper when an interactive administrator session is
available:

```bash
deploy/macos/install-private-preview-launchdaemon.sh restart
```

If automation already has permission to manage the loaded service, first allow
the old process to exit fully, then start the service. A rapid stop/start can
leave launchd without a listener. Verify readiness rather than assuming the
restart succeeded.

```bash
curl --fail --silent --show-error http://127.0.0.1:8770/health/live
curl --fail --silent --show-error http://127.0.0.1:8770/health/ready
curl --fail --silent --show-error http://127.0.0.1:8770/api/version
```

Expected health result is `{"status":"live"}` or `{"status":"ready"}`.
`/api/version` must report the short form of the intended current Git HEAD.

## Protected Browser Smoke

Use a complete cache-busted URL:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<slice>-<short-head>-<date>
```

Record the required Smoke Target block from `AGENTS.md`, including Access
login, exact HEAD, `/api/version`, root behavior, canonical UI route, and any
API fallback. API fallback is not browser smoke.

After Access succeeds, verify:

1. `/api/session` reports an authenticated allowed role.
2. Chat opens and a low-cost question returns without exposing raw prompts.
3. Explorer loads its manifest/chunk in lazy mode and renders validated cards.
4. Melody Studio opens and the arranger workspace renders.
5. Lessons opens and lesson navigation renders.
6. Root `/` and `/ui/steel-guitar-rag-mock.html` behave as documented.
7. No workspace renders `[object Object]` or a browser console error.

In an unauthenticated context, content-bearing API requests must fail without
running retrieval or answer generation.

## Logs And Capacity

The runtime is a single bounded threaded process. Relevant tuning variables
are:

- `STEEL_RAG_RUNTIME_THREADS` (default 8, maximum 32)
- `STEEL_RAG_RUNTIME_QUEUE` (default 32, maximum 128)
- `STEEL_RAG_CONTENT_CONCURRENCY` (default 4, maximum 16)
- `STEEL_RAG_OLLAMA_TIMEOUT_SECONDS` (bounded at 75 seconds)
- `STEEL_RAG_MELODY_VISION_TIMEOUT_SECONDS` (bounded at 75 seconds)

Runtime logs omit query strings, rotate at 5 MiB with three backups when a log
directory is configured, and must not contain request bodies, JWTs, source
excerpts, or environment values.

## Interest-Digest Worker

The Worker uses `wrangler-interest-digest.toml` and migrations in
`migrations/interest-digest/`.

Safe, non-notifying checks:

```bash
npm run test:worker
npx wrangler deploy --dry-run --config wrangler-interest-digest.toml
npx wrangler d1 migrations list STEEL_RAG_INTEREST_D1 --remote --config wrangler-interest-digest.toml
```

Do not invoke authenticated `POST /run` unless a live notification is intended.
An ambiguous provider result is parked for operator review; it must not be
automatically retried. Do not delete delivery state during rollback.

## Routine Verification

```bash
git status --short
.venv/bin/pytest -q
npm run check:js
npm run test:worker
npm run check:locks
npm run check:assets
```

Use [current-commands.md](current-commands.md) for clean-environment installs,
audits, and exact command details.

## Rollback

Follow [recovery-procedure.md](recovery-procedure.md). Roll back with a reviewed
revert commit and a normal restart; do not use destructive reset/checkout,
delete D1 delivery state, or mutate corpus/vector data.
