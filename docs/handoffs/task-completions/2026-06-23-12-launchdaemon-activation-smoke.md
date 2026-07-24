# 2026-06-23 Lane 12 LaunchDaemon Activation Smoke

## Task Summary

- Requested: install/load the committed Mac mini private-preview app LaunchDaemon, stop the old manual `screen` app process if needed, verify local `/api/version`, verify Cloudflare Tunnel status, and run protected-preview browser smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c`.
- Completed: inspected repo governance, runtime state, committed LaunchDaemon scripts/runbook, current port owner, Cloudflare Tunnel service state, and local `/api/version`.
- Intentionally not changed: did not stop the current manual app process, did not install/load the LaunchDaemon, did not change DNS, Cloudflare Access, tunnel config, auth settings, corpus, Chroma, embeddings, scraping, app code, UI, or product behavior.

## Pass / Warn / Fail

**Fail / blocked for LaunchDaemon activation.**

The task explicitly approved privileged activation, but non-interactive `sudo` is not available in this Codex session:

```text
sudo: a password is required
sudo-noninteractive-unavailable
```

Because installing `/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist` requires `sudo`, the LaunchDaemon could not be installed or bootstrapped. I left the working manual preview process in place to avoid taking the protected preview offline.

## Branch And Commit State

- Branch: `feature/answer-api`
- Requested deployment commit: `564d29c fix: supervise mac mini app runtime`
- Starting/final HEAD observed: `140a7c1 docs: refresh deployment integration status`
- Mismatch: current HEAD is newer than `564d29c`; `564d29c` is an ancestor of `140a7c1`.
- Impact: if the LaunchDaemon is loaded from the current checkout, `/api/version` should report `140a7c1`, not exactly `564d29c`.

Recent commit context:

```text
140a7c1 docs: refresh deployment integration status
564d29c fix: supervise mac mini app runtime
5f8af79 docs: record fretboard svg cache-bust smoke
7ec5e3a fix: refresh explorer fretboard script cache-bust
c73abb8 docs: record fretboard svg in-page cache-bust smoke
```

## Runtime Activation Result

- Manual `screen` process stopped: **No**
- Reason: the replacement LaunchDaemon could not be installed/loaded without sudo, so stopping the manual process would risk downtime.
- App port owner before/after audit: manual Python process under detached `screen`.
- LaunchDaemon installed/loaded: **No**
- LaunchDaemon status:

```text
Could not find service "com.steelguitarrag.private-preview" in domain for system
```

Current manual process summary:

```text
Python PID 98944 listening on 127.0.0.1:8770
screen session: 98941.steel-rag-private-preview (Detached)
command: scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 --answer-auth-mode production --auth-provider cloudflare-access
```

## Local Version Result

Command:

```bash
curl -sS --max-time 5 http://127.0.0.1:8770/api/version
```

Result:

```json
{
  "git_sha": "140a7c1",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-23T15:22:17.830791+00:00",
  "python_module": "steel_guitar_rag.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

Expected by prompt: `564d29c`.

Observed: `140a7c1`, which contains `564d29c`.

## Cloudflare Tunnel Status

Cloudflare Tunnel is running as a system LaunchDaemon:

```text
path = /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
state = running
stdout path = /Library/Logs/com.cloudflare.cloudflared.out.log
stderr path = /Library/Logs/com.cloudflare.cloudflared.err.log
runs = 1
pid = 677
last exit code = (never exited)
```

Sanitized plist inspection:

```text
Label: com.cloudflare.cloudflared
RunAtLoad: True
KeepAlive: {'SuccessfulExit': False}
StandardOutPath: /Library/Logs/com.cloudflare.cloudflared.out.log
StandardErrorPath: /Library/Logs/com.cloudflare.cloudflared.err.log
ProgramArguments count: 5
ProgramArguments include token-like value: True
```

No tunnel token contents were printed or copied.

## Durable Log Path Status

- Expected app LaunchDaemon log path: `~/Library/Logs/steel-guitar-rag/`
- Observed: no durable app log files were present during this audit.
- Reason: the LaunchDaemon installer did not run, so it did not create the durable log directory.
- Current manual `screen` process redirects to `/tmp/steel-rag-private-preview-8770.log`.

## Smoke Target

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke not performed; activation blocker
- Exact browser URL tested: Not tested
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c
- Exact URL the user should use: Do not treat this run as cleared; current working URL remains manual-process dependent
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 564d29c
- Version endpoint: /api/version
- Version endpoint result: 140a7c1 on feature/answer-api; contains 564d29c
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in browser
- Whether app root `/` is expected to work: expected to redirect or load app shell per current route behavior
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested in browser during this blocked activation run
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user after LaunchDaemon activation is completed
- Do not test these URLs: none beyond avoiding non-cache-busted assumptions
- Known caveats: current protected preview is still manual `screen`, not launchd-supervised
```

## Protected-Preview Smoke Result

Protected-preview browser smoke was **not performed** because the primary runtime change did not complete. Running browser smoke now would only verify the existing manual `screen` runtime, not the requested LaunchDaemon-supervised runtime.

Planned smoke prompts remain:

- `Show me a G major grip.`
- `Show me a 4-5-6 grip.`
- `Where is G on E9?`
- `Show me a G to C move.`
- `How do I use A+B pedals?`
- `Show me an E-lower move.`
- `Give me a beginner lick in G.`
- `Give me the full tab for a modern copyrighted song.`
- `Tab the whole solo from Together Again.`
- `Transcribe this YouTube recording into tab.`
- `What are good Fender Steel King settings?`
- `Why does my amp buzz at idle?`

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -5
git diff --cached --name-only
git merge-base --is-ancestor 564d29c HEAD
git diff --check
bash -n deploy/macos/run-private-preview-app.sh deploy/macos/install-private-preview-launchdaemon.sh
plutil -lint deploy/macos/com.steelguitarrag.private-preview.plist.template
lsof -nP -iTCP:8770 -sTCP:LISTEN
launchctl print system/com.steelguitarrag.private-preview
screen -ls
sudo -n true
curl -sS --max-time 5 http://127.0.0.1:8770/api/version
launchctl print system/com.cloudflare.cloudflared
ls -l /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

Results:

- `git diff --check`: passed.
- `bash -n`: passed for both deployment scripts.
- `plutil -lint`: passed for the plist template.
- `564d29c` ancestry check: passed; current `HEAD` contains `564d29c`.
- Local `/api/version`: reachable, reports `140a7c1`, branch `feature/answer-api`, auth provider `cloudflare_access`.
- App LaunchDaemon status: not installed/loaded.
- Cloudflare Tunnel system LaunchDaemon: running.
- Protected-preview browser smoke: skipped because activation blocked.

Skipped tests:

- Protected-preview browser smoke skipped because the requested LaunchDaemon activation did not occur.
- Broad test suite skipped; this was a runtime activation/smoke task with no app code changes.

## Files Changed

Changed files:

- None.

Created files:

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-activation-smoke.md`

Deleted files:

- None.

Generated artifacts:

- None.

## Integration Notes

- The Mac mini remains the protected-preview origin.
- Cloudflare Tunnel is already supervised at boot and currently running.
- The app process is still manually supervised by detached `screen`, not launchd.
- The app LaunchDaemon can be installed only from a shell with administrator privileges.
- Because the repo is now at `140a7c1`, a successful LaunchDaemon start from the current checkout should report `140a7c1`, not `564d29c`.

## Risks

Risk level: **Medium**.

Reasons:

- The private preview still depends on a manual `screen` session for app availability.
- A reboot would likely recover Cloudflare Tunnel but not the app process until the LaunchDaemon is installed and loaded.
- Durable app logs are not active yet.
- Stopping the manual app before a successful LaunchDaemon bootstrap would cause protected-preview downtime.

Rollback notes:

- No runtime changes were made, so no rollback was required.
- If the LaunchDaemon is later loaded and needs rollback, use:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

Then restart the known manual screen process only if needed.

## Human Decision Needed

Yes.

Exact decision/action needed:

- Run the LaunchDaemon install/load from an administrator-capable shell, or provide an interactive admin-password path for this session.

Recommended operator commands from repo root:

```bash
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh load
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
```

After successful status/version checks, rerun Lane 12 protected-preview browser smoke.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-activation-smoke.md`

## Files That Must Not Be Staged

- All unrelated dirty/parked files shown by `git status --short`.
- Any corpus, Chroma/vector, embeddings, source-inbox, scraper output, private env, Cloudflare token, credential, generated data, design raw asset, or unrelated UI/backend files.

## Commit Readiness

Safe to commit.

This handoff is documentation-only and records a blocked runtime activation. No secrets or token values are included.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Suggested Next Step

Run this exact prompt after admin-capable service activation is available:

```text
Lane 12: Install/load the Mac mini private-preview LaunchDaemon from current HEAD, stop the manual screen process only after the LaunchDaemon can bind 127.0.0.1:8770, verify /api/version, then run protected-preview browser smoke at https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<current-head>.
```
