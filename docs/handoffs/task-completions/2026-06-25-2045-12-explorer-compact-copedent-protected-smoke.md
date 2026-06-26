# Lane 12 - Explorer Compact Copedent Protected Smoke

## Task Summary

Requested Lane 12 protected-preview restart and browser smoke for the committed Explorer compact copedent UI work.

Completed:
- Inspected repo guidance, deployment/runtime docs, current git state, and the Lane 06 compact Explorer handoff.
- Verified the repo is on `feature/answer-api` at `5a59739`.
- Verified the LaunchDaemon is running, but the runtime remains stale at `ffac52a`.
- Attempted the documented privileged restart path with non-interactive sudo.
- Stopped before protected-preview browser smoke because `/api/version` does not report the expected runtime commit.

Intentionally not changed:
- No backend, UI, auth, DNS, Cloudflare Access, tunnel, scraping, embeddings, Chroma/vector stores, raw corpus, private transcript, or runtime code was changed.
- No protected-preview browser smoke was claimed from stale runtime or API fallback.

## Smoke Target

- Target type: protected-preview
- Result type: blocked before browser smoke
- Exact browser URL tested: not tested because runtime was stale
- Cache-busted URL intended: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625`
- Exact URL the user should use: blocked pending protected-preview restart to `5a59739`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted for this run; runtime version gate failed first
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `5a59739`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=ffac52a`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`, `server_started_at=2026-06-26T00:13:39.072091+00:00`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in protected browser because runtime was stale
- Whether app root `/` is expected to work: yes; previous docs note root redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings
- Whether `/ui/e9-fretboard-explorer.html` works: not tested through protected preview because runtime was stale
- Whether `/ui/e9-fretboard-explorer.html` is expected to work: yes after restart
- Who should test this URL: Lane 12 after the LaunchDaemon restart is completed
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: direct `/ui/...?...` URL is required because root drops query strings

## Repo And Runtime State

- Branch: `feature/answer-api`
- Starting HEAD: `5a59739`
- Final HEAD before docs commit: `5a59739`
- Latest commits:
  - `5a59739 docs: refresh integration status after compact explorer UI`
  - `9a3513b fix: compact explorer copedent controls`
  - `ffac52a docs: add Codex autopilot repo guidance`
  - `3f35aa3 docs: refresh E9 copedent selector integration status`
  - `8093a3c docs: record E9 copedent selector protected smoke`
- LaunchDaemon label: `system/com.steelguitarrag.private-preview`
- LaunchDaemon state: running
- LaunchDaemon PID before restart attempt: `56360`
- Listener: Python on `127.0.0.1:8770`
- Listener start time: `Thu Jun 25 19:13:38 2026`
- Durable logs:
  - `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`

## Restart Result

Documented restart path from `docs/mac-mini-private-preview-launchd.md` and `deploy/macos/install-private-preview-launchdaemon.sh`:

```bash
deploy/macos/install-private-preview-launchdaemon.sh restart
```

The script wraps:

```bash
sudo launchctl kickstart -k system/com.steelguitarrag.private-preview
```

Non-interactive restart attempt:

```bash
sudo -n launchctl kickstart -k system/com.steelguitarrag.private-preview
```

Result:

```text
sudo: a password is required
```

The runtime remained on `ffac52a`. Per the task instruction not to improvise a deployment path, no launchd-kill workaround or manual process restart was used.

## Protected Preview Browser Smoke

Not run.

Reason: runtime version gate failed. Protected-preview browser smoke against the intended URL would have tested stale runtime/static assets.

## Explorer Checks

Not run on protected preview.

The following requested checks remain pending after the documented restart succeeds:

- Page loads at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625`
- Fretboard is visible without unnecessary scroll on normal desktop/laptop viewport
- Compact filters are usable
- Copedent chart is hidden by default behind `View chart`
- `View chart` opens and closes the chart near the copedent selector
- Emmons E9 does not include LKV/B-to-Bb
- `Custom E9 (with LKV)` exists as the custom setup
- Pedal/lever impact preview is compact and interactive
- Notes / Intervals toggle works
- Fretboard cells do not combine fret number with note/interval text
- Console has no relevant errors

## Root And App Behavior

Not retested in protected browser because the runtime was stale.

Expected from current integration notes:
- Root URL redirects to `/ui/steel-guitar-rag-mock.html`.
- Root drops query strings during redirect.
- Direct `/ui/...?...` URLs are required for cache-busted Explorer validation.

## Files Changed

- Created: `docs/handoffs/task-completions/2026-06-25-2045-12-explorer-compact-copedent-protected-smoke.md`
- Updated: `docs/handoffs/task-completions/integration-status.md`

No implementation files were changed.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -5`
- `git diff --check`
- `git diff --cached --name-only`
- `launchctl print system/com.steelguitarrag.private-preview`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command || true`
- `deploy/macos/install-private-preview-launchdaemon.sh status || true`
- `deploy/macos/install-private-preview-launchdaemon.sh version || true`
- `sudo -n launchctl kickstart -k system/com.steelguitarrag.private-preview`

Skipped:
- Protected-preview browser smoke, because `/api/version` reported stale runtime `ffac52a` instead of expected `5a59739`.
- Browser screenshots, because protected-preview smoke did not start.

## Risks

Risk: medium.

The repo contains the compact Explorer UI commits, but the Mac mini protected-preview runtime has not been restarted to serve them. User smoke would currently be testing stale runtime assets.

## Human Decision Needed

Yes.

Run the documented privileged restart from an interactive terminal session on the Mac mini:

```bash
cd /Users/cory/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh restart
curl -sS http://127.0.0.1:8770/api/version
```

Expected `/api/version` after restart:

```text
git_sha=5a59739
```

Then rerun Lane 12 protected-preview browser smoke.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-25-2045-12-explorer-compact-copedent-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any backend/runtime/UI/test files outside this docs-only status update
- Auth, DNS, Cloudflare, tunnel, LaunchDaemon, or private env files
- Corpus, private corpus, Chroma/vector stores, embeddings, scraper output, source-inbox raw/provenance files, credentials, logs, generated/private artifacts, and unrelated dirty work

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Commit Readiness

Safe to commit for docs-only blocker status if staged with exact paths only.

## Suggested Next Step

After interactive restart succeeds:

```text
Lane 12: rerun protected-preview browser smoke for https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625 after /api/version reports 5a59739.
```
