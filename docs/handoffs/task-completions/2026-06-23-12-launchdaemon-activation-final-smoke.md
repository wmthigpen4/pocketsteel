# 2026-06-23 Lane 12 LaunchDaemon Activation Final Smoke

## Task Summary

- Requested: activate the Mac mini private-preview LaunchDaemon after the permission fix, stop the old manual runtime only when safe, verify `/api/version`, verify Cloudflare Tunnel, and run protected-preview browser smoke.
- Completed: inspected repo governance, current git state, LaunchDaemon template/install script, loaded system LaunchDaemon, port ownership, manual `screen` runtime, local `/api/version`, durable logs, Cloudflare Tunnel launchd status, installed system plist, and rendered repo plist.
- Intentionally not changed: did not modify app code, Cloudflare Access policy, DNS, auth settings, tunnel token values, Cloudflare account configuration, corpus, embeddings, Chroma, scraper output, source data, private env files, or Cloudflare Tunnel configuration.

## Pass / Warn / Fail

**Warn / blocked before protected-preview smoke.**

The repo permission fix is present at `4c40cef`, and the repo-rendered plist points at the daemon-safe wrapper path. The live system LaunchDaemon still uses the old repo wrapper path and is still failing with exit `126`. Non-interactive `sudo` is unavailable in this Codex session, so the corrected plist/wrapper could not be installed or loaded.

Protected-preview browser smoke was not run because launchd does not own the app runtime. The currently working app on `127.0.0.1:8770` is still the manual detached `screen` runtime.

## Current Branch And Head

- Branch: `feature/answer-api`
- HEAD: `4c40cef fix: run launchdaemon wrapper from safe path`
- Expected runtime commit for smoke: `4c40cef`

## Dirty Worktree Status

Broad unrelated dirty/untracked files remain parked. Runtime/deployment files touched by this task: none.

Notable protected/parked categories still present in the worktree include:

- corpus/source metadata and source-inbox files
- design/brand assets
- generated handoffs/assets
- private/corpus-adjacent scripts and data
- unrelated docs and reports

No broad staging was used.

## LaunchDaemon Fix Presence

Confirmed the repo scripts/templates include the permission fix:

- `deploy/macos/com.steelguitarrag.private-preview.plist.template` renders `ProgramArguments[0]` as `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`.
- `deploy/macos/com.steelguitarrag.private-preview.plist.template` renders `WorkingDirectory` as `/usr/local/libexec/steel-guitar-rag`.
- `deploy/macos/install-private-preview-launchdaemon.sh` installs the wrapper into `/usr/local/libexec/steel-guitar-rag`.

Rendered plist validation passed:

```text
/tmp/com.steelguitarrag.private-preview.rendered.plist: OK
```

## Live LaunchDaemon Status

The loaded system service is still stale:

```text
path = /Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
state = spawn scheduled
program = /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh
working directory = /Users/cory/Documents/Pocket Steel
runs = 154
last exit code = 126
```

The installed system plist also still points at the old repo path:

```text
ProgramArguments[0] = /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh
WorkingDirectory = /Users/cory/Documents/Pocket Steel
```

The app stderr log still repeats the original failure:

```text
shell-init: error retrieving current directory: getcwd: cannot access parent directories: Operation not permitted
bash: /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh: Operation not permitted
```

## Manual Runtime Status

Port `8770` is still owned by the manual app runtime:

```text
Python PID 98944 listening on 127.0.0.1:8770
```

The parent runtime is still the detached screen session:

```text
98941.steel-rag-private-preview
```

This process was intentionally not stopped because the LaunchDaemon has not been updated and cannot bind/own the port yet.

## Local Version Result

Local `/api/version` is reachable, but this is from the manual screen runtime, not launchd:

```json
{"git_sha":"4c40cef","git_branch":"feature/answer-api","server_started_at":"2026-06-23T15:52:26.257888+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

## Cloudflare Tunnel Status

Cloudflare Tunnel launchd status was checked without printing token-bearing arguments:

```text
path = /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
state = running
stdout path = /Library/Logs/com.cloudflare.cloudflared.out.log
stderr path = /Library/Logs/com.cloudflare.cloudflared.err.log
runs = 1
pid = 677
last exit code = (never exited)
```

## Sudo / Activation Blocker

The activation step requires privileged install/load operations. Non-interactive sudo is unavailable:

```text
sudo: a password is required
```

The script status command also fails in this session because it needs a terminal/password for sudo:

```text
sudo: a terminal is required to read the password
sudo: a password is required
```

## Smoke Target

- Target type: protected-preview
- Result type: not run; blocked before browser smoke
- Exact browser URL tested: not tested
- Cache-busted URL intended: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4c40cef`
- Exact URL the user should use: not cleared yet
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `4c40cef`
- Version endpoint: `/api/version`
- Version endpoint result: `4c40cef`, manual screen runtime
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: root behavior should be recorded after launchd activation
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in protected-preview browser during this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12 after LaunchDaemon activation
- Do not test these URLs: do not treat local loopback or API fallback as protected-preview browser smoke
- Known caveats: manual screen process currently serves the app; LaunchDaemon is still stale and failing exit `126`

## Protected-Preview Smoke Result

Not run.

Reason: launchd does not own the runtime. Running browser smoke against `app.steelguitarrag.com` would test the manual screen process and would not satisfy the task goal.

## Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
git diff --cached --name-only
git diff --check
grep -n "WRAPPER\|WORKING\|/usr/local/libexec\|ProgramArguments\|WorkingDirectory" deploy/macos/install-private-preview-launchdaemon.sh deploy/macos/com.steelguitarrag.private-preview.plist.template
launchctl print system/com.steelguitarrag.private-preview || true
lsof -nP -iTCP:8770 -sTCP:LISTEN || true
screen -ls || true
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version || true
curl -sS --max-time 5 http://127.0.0.1:8770/api/version || true
launchctl print system/com.cloudflare.cloudflared 2>/dev/null | grep -E 'state|pid|last exit|runs|path' || true
tail -n 60 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log 2>/dev/null || true
tail -n 40 /Users/cory/Library/Logs/steel-guitar-rag/app.out.log 2>/dev/null || true
plutil -p /Library/LaunchDaemons/com.steelguitarrag.private-preview.plist 2>/dev/null || true
deploy/macos/install-private-preview-launchdaemon.sh render > /tmp/com.steelguitarrag.private-preview.rendered.plist
plutil -lint /tmp/com.steelguitarrag.private-preview.rendered.plist
sudo -n true 2>&1 || true
```

Results:

- `git diff --check`: passed before handoff creation.
- Rendered plist lint: passed.
- Local `/api/version`: reachable, reports `4c40cef`, but from manual screen runtime.
- Cloudflare Tunnel: running.
- LaunchDaemon app service: stale system plist, exit `126`, not supervising the app.
- Protected-preview browser smoke: skipped because launchd activation is blocked.

## Exact Next Operator Commands

Run from the repo root in an administrator-capable terminal:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload || true
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh load
launchctl print system/com.steelguitarrag.private-preview | grep -E 'state|pid|last exit|runs|path|program|working directory'
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
```

Expected after successful install/load:

```text
program = /usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
working directory = /usr/local/libexec/steel-guitar-rag
```

Only after those fields are corrected and the old `Operation not permitted` loop stops, stop the manual screen if port ownership is the remaining blocker:

```bash
screen -S steel-rag-private-preview -X quit
deploy/macos/install-private-preview-launchdaemon.sh restart
deploy/macos/install-private-preview-launchdaemon.sh version
```

If `restart` reports the service is not bootstrapped:

```bash
deploy/macos/install-private-preview-launchdaemon.sh load
deploy/macos/install-private-preview-launchdaemon.sh version
```

## Risks

Risk level: **Medium**.

- The manual screen process is preserving availability; stopping it before the LaunchDaemon is fixed would likely interrupt protected preview.
- The current system plist is stale and still failing repeatedly.
- The repo-rendered plist should fix the execution path, but the service still needs privileged installation.
- If launchd can execute the installed wrapper but cannot `cd` into the repo under `~/Documents`, the next safe option is a separate approved runtime checkout outside TCC-sensitive folders.

## Human Decision Needed

Yes.

An administrator-capable terminal must run the privileged install/load commands above. This Codex session cannot complete them because sudo requires a password.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-activation-final-smoke.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files.
- App code, UI code, tests, corpus/source files, source-inbox files, Chroma/vector stores, embeddings, scraper output, private corpus, private env files, tunnel tokens, rendered plists, Cloudflare credentials, DNS/auth config, `.wrangler/`, raw design assets, generated media, and unrelated handoffs.

## Recommended Next Lane

Lane 12.

## Commit Readiness

Safe to commit for this handoff only.

## Suggested Next Step

After the operator runs the privileged install/load commands, rerun Lane 12 ProtectedPreviewSmoke:

```text
Lane 12: Verify the corrected Mac mini LaunchDaemon owns 127.0.0.1:8770, confirm /api/version reports the active HEAD, confirm Cloudflare Tunnel is running, then run protected-preview browser smoke at https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<api-version>. Record root behavior, Cloudflare Access login, Q&A unlock, console errors, and the standard static/movement/copyright/gear prompt results.
```
