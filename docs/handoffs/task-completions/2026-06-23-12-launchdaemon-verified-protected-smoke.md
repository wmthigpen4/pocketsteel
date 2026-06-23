# 2026-06-23 Lane 12 LaunchDaemon Verified Protected Smoke

## Task Summary

- Requested: verify the manually installed Mac mini LaunchDaemon, confirm local `/api/version`, verify Cloudflare Tunnel, and run protected-preview browser smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=b029eb4`.
- Completed: inspected repo governance, current git/runtime state, LaunchDaemon state, durable app logs, local `/api/version`, Cloudflare Tunnel state, and current port owner.
- Intentionally not changed: did not modify app code, LaunchDaemon files, Cloudflare Access policy, DNS, auth settings, tunnel token values, corpus, Chroma, embeddings, scraping, source data, or product behavior.

## Pass / Warn / Fail

**Fail / blocked.**

Protected-preview browser smoke was not run because the app is not actually launchd-supervised yet. The local endpoint is reachable and reports `b029eb4`, but port `8770` is still owned by the older detached `screen` Python process, while the installed LaunchDaemon is failing before startup.

## Branch And Version State

- Branch: `feature/answer-api`
- Current HEAD: `b029eb4 docs: record launchdaemon activation smoke`
- Expected runtime version: `b029eb4`
- Local `/api/version` result: reports `b029eb4`, branch `feature/answer-api`, auth provider `cloudflare_access`, retrieval mode `hybrid_private_first`.

Local version command:

```bash
curl -sS --max-time 5 http://127.0.0.1:8770/api/version
```

Observed result:

```json
{
  "git_sha": "b029eb4",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-23T15:28:13.971931+00:00",
  "python_module": "pocketsteel.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

## LaunchDaemon Status

The LaunchDaemon plist is installed:

```text
/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
```

`launchctl print system/com.steelguitarrag.private-preview` shows:

```text
path = /Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
type = LaunchDaemon
state = spawn scheduled
program = /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh
working directory = /Users/cory/Documents/Pocket Steel
stdout path = /Users/cory/Library/Logs/steel-guitar-rag/app.out.log
stderr path = /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
username = cory
group = staff
runs = 10
last exit code = 126
```

Installer status command:

```bash
deploy/macos/install-private-preview-launchdaemon.sh status
```

Result:

```text
sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
sudo: a password is required
```

The direct `launchctl print` check was still available and is the source of the status summary above.

## Current Port Owner

Port `8770` remains owned by the older manual `screen` process, not by launchd:

```text
Python PID 98944 listening on 127.0.0.1:8770
parent screen session: 98941.steel-rag-private-preview (Detached)
process start: Tue Jun 23 09:53:25 2026
command: scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 --answer-auth-mode production --auth-provider cloudflare-access
```

## Durable Log Path Status

Durable app log directory exists:

```text
/Users/cory/Library/Logs/steel-guitar-rag
```

Observed files:

```text
app.out.log: 0 bytes
app.err.log: 2200 bytes
```

`app.err.log` shows repeated LaunchDaemon startup failures:

```text
shell-init: error retrieving current directory: getcwd: cannot access parent directories: Operation not permitted
bash: /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh: Operation not permitted
```

This indicates the installed system LaunchDaemon cannot access or execute the repo path under `~/Documents/Pocket Steel` in its current macOS privacy/runtime context.

## Cloudflare Tunnel Status

Cloudflare Tunnel is still running as a separate system LaunchDaemon:

```text
path = /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
state = running
stdout path = /Library/Logs/com.cloudflare.cloudflared.out.log
stderr path = /Library/Logs/com.cloudflare.cloudflared.err.log
runs = 1
pid = 677
last exit code = (never exited)
```

No tunnel token contents were printed or copied.

## Smoke Target

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke not performed; launchd supervision blocker
- Exact browser URL tested: Not tested
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=b029eb4
- Exact URL the user should use: Not cleared by this run
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: b029eb4
- Version endpoint: /api/version
- Version endpoint result: b029eb4 on feature/answer-api, but served by manual screen process
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in browser
- Whether app root `/` is expected to work: expected to redirect or load app shell per current route behavior
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in browser during this blocked run
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user after launchd supervision is fixed and verified
- Do not test these URLs: do not treat local/manual-screen checks as launchd-supervised smoke
- Known caveats: current app listener is still manual screen; LaunchDaemon exits 126 with Operation not permitted
```

## Protected-Preview Smoke Result

Protected-preview browser smoke was not run. Running the browser prompts now would verify the old manual `screen` process, not the requested launchd-supervised runtime.

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

## Root URL Behavior

Root behavior was not browser-tested because launchd supervision is blocked.

Planned root URL:

```text
https://app.steelguitarrag.com/?v=b029eb4
```

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
git diff --cached --name-only
git diff --check
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
curl -sS --max-time 5 http://127.0.0.1:8770/api/version
launchctl print system/com.cloudflare.cloudflared
lsof -nP -iTCP:8770 -sTCP:LISTEN
ls -la /Users/cory/Library/Logs/steel-guitar-rag
wc -c /Users/cory/Library/Logs/steel-guitar-rag/app.out.log /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
tail -n 120 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
ps -p 98944 -o pid=,ppid=,user=,lstart=,comm=,args=
ps -p 98941 -o pid=,ppid=,user=,lstart=,comm=,args=
screen -ls
```

Results:

- `git diff --check`: passed.
- Local `/api/version`: reachable and reports `b029eb4`.
- LaunchDaemon: installed but not running the app; `state = spawn scheduled`, `last exit code = 126`.
- Durable app logs: present and writable enough for stderr output.
- LaunchDaemon stderr: repeated `Operation not permitted` errors for the repo path.
- Cloudflare Tunnel: running.
- Protected-preview browser smoke: skipped due launchd blocker.

Skipped tests:

- Browser smoke skipped because the launchd-supervised runtime was not active.
- Broad tests skipped; no app code was changed.

## Files Changed

Changed files:

- None.

Created files:

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-verified-protected-smoke.md`

Deleted files:

- None.

Generated artifacts:

- None.

## Integration Notes

- The installed LaunchDaemon cannot currently execute the app wrapper from `~/Documents/Pocket Steel`.
- The likely deployment blocker is macOS privacy/TCC or path access for a system LaunchDaemon running against a user `Documents` path.
- The current protected preview may still work through the old manual `screen` process, but that does not meet the always-on launchd-supervised goal.
- Do not stop the manual `screen` process until a supervised replacement successfully owns `127.0.0.1:8770`.

## Risk Assessment

Risk level: **Medium**.

Reasons:

- The app remains dependent on manual `screen` despite the LaunchDaemon plist being installed.
- LaunchDaemon repeated failures can continue writing logs and scheduling spawns until corrected or unloaded.
- Reboot resilience is not achieved yet for the app process.
- Cloudflare Tunnel is running, so the public route can still reach whichever process owns `8770`; currently that is the manual process.

Rollback notes:

- To stop the failing LaunchDaemon after administrator review:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

- Keep the manual `screen` process running until a corrected supervised runtime binds `127.0.0.1:8770`.

## Human Decision Needed

Yes.

Decide how to resolve macOS LaunchDaemon access to the repo/runtime path. Safe options to evaluate:

1. Move the runtime checkout or wrapper target out of a TCC-protected `~/Documents` path into a service-friendly path such as `/Users/cory/Applications/steel-guitar-rag-runtime` or another operator-approved location.
2. Convert the app service to a user LaunchAgent if boot-before-login is less important than access to the user-space repo path.
3. Grant the necessary macOS privacy/full-disk access for the launchd execution path, if acceptable operationally.

Do not make this change through broad staging or by moving corpus/private/generated data. Treat it as a separate Lane 12 service-hardening task.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-verified-protected-smoke.md`

## Files That Must Not Be Staged

- All unrelated dirty/parked files shown by `git status --short`.
- Any app code, LaunchDaemon files, Cloudflare config, auth/DNS settings, corpus, Chroma/vector stores, embeddings, scraper output, source-inbox raw/provenance files, private env files, credentials, tunnel tokens, generated data, or unrelated assets.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Commit Readiness

Safe to commit.

This handoff is documentation-only, contains no secrets, and records a blocked protected-preview smoke gate.

## Suggested Next Step

Run a focused Lane 12 service-hardening task:

```text
Lane 12: Fix the Mac mini app LaunchDaemon startup failure where `/Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh` exits 126 with `Operation not permitted`. Preserve the manual screen process until the LaunchDaemon can bind 127.0.0.1:8770, do not touch DNS/auth/corpus/Chroma/secrets, and write a handoff with the chosen macOS service path or LaunchAgent/LaunchDaemon decision. After fix, rerun protected-preview browser smoke at https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<current-head>.
```
