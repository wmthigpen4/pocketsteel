# 2026-06-23 Integration Status Deployment Wrap Refresh

## Task Summary

Lane: 01 Repo Steward.

Requested: refresh the integration-status reset snapshot for the current deployment/runtime wrap-up state before returning to user smoke testing on `app.steelguitarrag.com`.

Completed:

- Read governance files, current integration status, the Mac mini reliability audit, current launchd runtime hardening handoff, current launchd runbook, and latest protected-preview smoke handoffs.
- Updated `docs/handoffs/task-completions/integration-status.md` with current HEAD `564d29c`, Mac mini runtime status, Cloudflare Tunnel status, protected-preview smoke status, user smoke target, remaining blockers, and next Lane 12 control step.
- Created this scoped Repo Steward handoff.

Intentionally not changed:

- No implementation files.
- No UI/test/source files.
- No launchd/deployment script edits.
- No service restart.
- No Cloudflare, DNS, auth, tunnel, or secret changes.
- No corpus, Chroma/vector stores, embeddings, scraper, source-inbox, or private-source work.

## Files Changed

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-integration-status-deployment-wrap.md`

## Deployment Readiness Status

Status: **partial / needs Lane 12 verification**.

Current HEAD:

- `564d29c fix: supervise mac mini app runtime`

What is complete:

- Repo-managed launchd assets are committed:
  - `deploy/macos/com.steelguitarrag.private-preview.plist.template`
  - `deploy/macos/run-private-preview-app.sh`
  - `deploy/macos/install-private-preview-launchdaemon.sh`
  - `docs/mac-mini-private-preview-launchd.md`
- The launchd hardening handoff reports syntax/plist validation passed.
- Durable app log paths are defined in the committed service plan.

What is not proven complete:

- The app LaunchDaemon has not been proven installed/loaded.
- The live app has not been proven running from launchd supervision.
- Protected-preview browser smoke has not run against `564d29c`.
- Protected-preview browser smoke has not run from the supervised launchd process.

## Protected-Preview Smoke Status

Latest relevant protected-preview smoke before launchd hardening:

- Handoff: `docs/handoffs/task-completions/2026-06-23-1007-12-fretboard-svg-cache-bust-protected-smoke.md`
- Runtime version: local `/api/version` reported `7ec5e3a`
- Result: protected Explorer route passed the fretboard SVG cache-bust smoke.

Current status:

- No protected-preview browser smoke is documented for current HEAD `564d29c`.
- User smoke should wait for Lane 12.
- API fallback must not be treated as protected-preview browser smoke.

## User Smoke URL

Not ready for user smoke until Lane 12 passes.

Next Lane 12 smoke URL:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c
```

Use the same URL for the user only after Lane 12 verifies:

- Cloudflare Access browser auth succeeds.
- `/api/version` reports `564d29c` or later.
- root `/` behavior is recorded.
- direct `/ui/steel-guitar-rag-mock.html` behavior passes.
- Q&A unlocks.
- prompt smoke passes.

## Blockers

- App launchd service install/load not proven.
- Supervised runtime smoke not complete.
- Current HEAD protected-preview smoke not complete.
- Mac AC sleep and restart-after-power-failure settings remain unresolved unless changed outside this repo task.
- Ollama boot supervision remains unverified.
- Cloudflare Tunnel inline-token hardening remains a separate security/ops task.
- Broad unrelated dirty/untracked worktree remains parked.

## Checks Run

- `git status --short`
- `git diff --cached --name-only`
- `git diff --check`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -1 --oneline`
- `git log --oneline -25`
- inspected requested governance files and handoffs

Pending before commit:

- `git diff --cached --name-only`
- `git diff --cached`
- `git diff --cached --check`

## Risks

- Medium until Lane 12 verifies the current runtime.
- The repo now contains a service plan, but documentation alone does not prove the host is actually supervised.
- Broad parked worktree state means future commits must continue exact-path staging.

## Human Decision Needed

Yes, outside this docs refresh:

- Run Lane 12 to install/load or verify the app LaunchDaemon.
- Decide whether to stop the manual process to avoid port conflict if installing launchd.
- Decide whether to apply Mac power settings and whether Ollama needs supervision.
- Decide whether to run a separate Cloudflare Tunnel token/config hardening task.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-integration-status-deployment-wrap.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files.
- App code, tests, UI, SVG assets, launchd/deploy scripts, auth/DNS/Cloudflare config, or source files.
- Corpus/private corpus files.
- Chroma/vector stores.
- Embeddings.
- Scraper output.
- Source-inbox raw/provenance files.
- Private env files, rendered plists, Cloudflare Tunnel tokens, credentials, `.wrangler/`, and secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

Exact prompt:

```text
Lane 12: Install/load or verify the Mac mini private-preview LaunchDaemon from committed HEAD 564d29c, or explicitly document why the runtime remains manual. Verify local /api/version reports 564d29c or later, verify Cloudflare Access browser auth, record root `/` behavior, and run protected-preview browser smoke at https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c. Use the 12 smoke prompts listed in integration-status.md. Confirm static grip answers are fretboard-first, movement examples may include deterministic tab, copyrighted song/solo/YouTube transcription requests are refused, gear answers have no stale tab/fretboard payload, and no [object Object] appears. Write a Lane 12 handoff with exact URL tested, cache-busted URL, auth result, expected/current git HEAD, /api/version result, root URL behavior, direct /ui behavior, and API fallback status.
```

## Commit Readiness

Safe to commit after exact-path staging and cached diff review.
