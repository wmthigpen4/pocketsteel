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

## Activate An Exact Release

The subscriber-facing origin must run from a clean detached release checkout,
not the primary development worktree. Keep shared local data in the primary
data directory and pass it separately; activation never copies or mutates the
corpus or vector stores.

```bash
release="$HOME/.steel-rag/releases/<short-sha>"
mkdir -p "$release"
git -C "$release" init
git -C "$release" fetch --depth=1 "file://$(pwd)" <full-sha>
git -C "$release" checkout --detach FETCH_HEAD
ln -s "$(pwd)/.venv" "$release/.venv"

STEEL_RAG_REPO_DIR="$release" \
STEEL_RAG_DATA_DIR="$(pwd)" \
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

`activate` requires administrator authorization, installs the hardened wrapper
and plist, loads the exact release, and refuses success unless live, ready, and
version checks pass. If activation fails after replacing a loaded definition,
the installer restores the previous plist and bootstraps it again.

Run the same release validation without changing system state first:

```bash
STEEL_RAG_REPO_DIR="$release" \
STEEL_RAG_DATA_DIR="$(pwd)" \
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh preflight
```

For a restart of the already configured exact release, pass the same release
directory and SHA:

```bash
STEEL_RAG_REPO_DIR="$release" \
STEEL_RAG_DATA_DIR="$(pwd)" \
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh restart
```

Never terminate the port-8770 listener as a deployment mechanism. Graceful
SIGTERM exits successfully, and old `KeepAlive.SuccessfulExit=false` installs
can leave the site stopped. Do not run `kill`, `pkill`, or
`lsof -tiTCP:8770 | xargs kill` in an automated preview refresh.

`STEEL_RAG_REPLACE_PID` exists only for an incident handover from a known
temporary origin. `activate` verifies that the exact PID owns port 8770, sends
it graceful TERM only after the new plist is installed, then requires the
launchd-supervised PID to own the listener before reporting success. Do not use
this option for normal deployments.

Read-only verification does not require administrator authorization:

```bash
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh verify
```

The verification command checks `/health/live`, `/health/ready`, and
`/api/version`; the version must report the short form of the intended exact
release.

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
