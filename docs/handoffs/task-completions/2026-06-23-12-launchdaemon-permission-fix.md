# 2026-06-23 Lane 12 LaunchDaemon Permission Fix

## Task Summary

- Requested: diagnose and fix the Mac mini app LaunchDaemon startup failure where launchd exits `126` with `Operation not permitted` while executing `~/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh`.
- Completed: inspected repo governance, launchd template/scripts, current runtime state, file mode/ownership/xattrs, parent directory permissions, durable logs, rendered plist output, and current port ownership. Updated the LaunchDaemon template and installer so the installed service executes a root-owned wrapper copy from `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh` instead of executing directly from `~/Documents`.
- Intentionally not changed: did not modify app behavior, Cloudflare Access, DNS, auth settings, tunnel token values, Cloudflare account config, corpus, embeddings, Chroma, scraper output, source data, private env files, or the live manual `screen` process.

## Pass / Warn / Fail

**Warn / repo fix ready, runtime activation pending.**

The repo-managed fix is implemented and validated by syntax, template, and rendered-plist checks. It has not been installed into `/Library/LaunchDaemons` from this Codex session because non-interactive `sudo` is unavailable:

```text
sudo: a password is required
sudo-noninteractive-unavailable
```

The currently loaded LaunchDaemon still points to the old `~/Documents/Pocket Steel/...` wrapper path until the operator runs the privileged install/unload/load commands below.

## Branch And Head State

- Branch: `feature/answer-api`
- Starting HEAD: `f295315 docs: reconcile parallel lane handoffs`
- Final HEAD before commit: `f295315 docs: reconcile parallel lane handoffs`

## Root Cause / Best-Supported Diagnosis

The failure is best explained by macOS launchd/TCC/path restrictions around a system LaunchDaemon executing from `~/Documents` and using `~/Documents/Pocket Steel` as its working directory.

Evidence:

- Current LaunchDaemon state: `spawn scheduled`
- Current LaunchDaemon `last exit code`: `126`
- Current loaded program: `/Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh`
- Current loaded working directory: `/Users/cory/Documents/Pocket Steel`
- Log output repeats:

```text
shell-init: error retrieving current directory: getcwd: cannot access parent directories: Operation not permitted
bash: /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh: Operation not permitted
```

Additional file/path observations:

```text
deploy/macos/run-private-preview-app.sh mode: -rwxr-xr-x
deploy/macos/run-private-preview-app.sh owner/group: cory staff
xattr: com.apple.provenance
/Users/cory mode: drwxr-x---
/Users/cory/Documents mode: drwx------
/Users/cory/Documents/Pocket Steel mode: drwxr-xr-x
```

This does not look like a plain chmod problem. The script is executable, and the parent `Documents` path is the likely launchd-sensitive location.

## Files Changed

Changed files:

- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
- `deploy/macos/install-private-preview-launchdaemon.sh`
- `docs/mac-mini-private-preview-launchd.md`

Created files:

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-permission-fix.md`

Deleted files:

- None.

Generated artifacts:

- `/tmp/com.steelguitarrag.private-preview.rendered.plist` for local validation only.

## Implementation Notes

The plist template now uses two rendered placeholders instead of executing directly from the repo:

```text
ProgramArguments: __STEEL_RAG_WRAPPER_PATH__
WorkingDirectory: __STEEL_RAG_WORKING_DIR__
```

The installer now defaults to:

```text
STEEL_RAG_WRAPPER_INSTALL_DIR=/usr/local/libexec/steel-guitar-rag
STEEL_RAG_WRAPPER_PATH=/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
STEEL_RAG_WORKING_DIR=/usr/local/libexec/steel-guitar-rag
```

During `install`, the script will:

- create `/usr/local/libexec/steel-guitar-rag` as root-owned `0755`;
- install the repo-managed wrapper there as root-owned `0755`;
- remove `com.apple.quarantine` from the installed wrapper if present;
- create the durable app log directory;
- render and install the LaunchDaemon plist.

The repo-managed wrapper remains the source of truth; the installed copy is the daemon-safe executable.

## Rendered Plist Result

Rendered plist validation passed:

```text
/tmp/com.steelguitarrag.private-preview.rendered.plist: OK
```

Rendered service fields now include:

```text
ProgramArguments[0] = /usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
WorkingDirectory = /usr/local/libexec/steel-guitar-rag
STEEL_RAG_REPO_DIR = /Users/cory/Documents/Pocket Steel
STEEL_RAG_ENV_FILE = /Users/cory/.steel-rag/env/private-preview.env
STEEL_RAG_LOG_DIR = /Users/cory/Library/Logs/steel-guitar-rag
STEEL_RAG_HOST = 127.0.0.1
STEEL_RAG_PORT = 8770
```

The rendered plist still points the app wrapper at the current repo checkout through `STEEL_RAG_REPO_DIR`. If launchd can execute the installed wrapper but still cannot `cd` into `~/Documents/Pocket Steel`, the remaining issue is the runtime checkout location. The runbook now documents reinstalling with an operator-approved runtime path outside TCC-sensitive folders, such as:

```bash
STEEL_RAG_REPO_DIR=/Users/cory/steel-guitar-rag-runtime \
deploy/macos/install-private-preview-launchdaemon.sh install
```

Do not move private env files, Cloudflare tokens, Chroma/vector stores, private corpus, generated data, or scraper output into a new runtime path without a separate explicit approval.

## Current Runtime State

The live LaunchDaemon has not been updated yet. Current loaded state still shows the old values:

```text
path = /Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
state = spawn scheduled
program = /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh
working directory = /Users/cory/Documents/Pocket Steel
runs = 129
last exit code = 126
```

Port `8770` remains owned by the old manual process:

```text
Python PID 98944 listening on 127.0.0.1:8770
```

This was intentionally preserved. Do not stop it until the LaunchDaemon can execute successfully and the only remaining blocker is port ownership.

## Checks Run

Commands run:

```bash
git status --short
git diff --cached --name-only
git diff --check
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
launchctl print system/com.steelguitarrag.private-preview
lsof -nP -iTCP:8770 -sTCP:LISTEN
ls -la deploy/macos/run-private-preview-app.sh
xattr -l deploy/macos/run-private-preview-app.sh
stat -f '%Sp %Su %Sg %N' /Users/cory /Users/cory/Documents '/Users/cory/Documents/Pocket Steel' '/Users/cory/Documents/Pocket Steel/deploy' '/Users/cory/Documents/Pocket Steel/deploy/macos' '/Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh'
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.out.log
bash -n deploy/macos/run-private-preview-app.sh deploy/macos/install-private-preview-launchdaemon.sh
plutil -lint deploy/macos/com.steelguitarrag.private-preview.plist.template
deploy/macos/install-private-preview-launchdaemon.sh render > /tmp/com.steelguitarrag.private-preview.rendered.plist
plutil -lint /tmp/com.steelguitarrag.private-preview.rendered.plist
plutil -p /tmp/com.steelguitarrag.private-preview.rendered.plist
rg -n "token|secret|password|PRIVATE|CF_|cloudflared|TUNNEL|STEEL_RAG_CF|BEGIN .*KEY|api[_-]?key" deploy/macos/com.steelguitarrag.private-preview.plist.template deploy/macos/run-private-preview-app.sh deploy/macos/install-private-preview-launchdaemon.sh docs/mac-mini-private-preview-launchd.md
sudo -n true
```

Results:

- `git diff --check`: passed.
- `bash -n`: passed for both deployment scripts.
- `plutil -lint` on template: passed.
- Rendered plist lint: passed.
- Rendered plist points to daemon-safe wrapper path: yes.
- Scoped secret-pattern check: no secret values found; matches were expected guardrail text or non-secret env var names.
- Non-interactive sudo: unavailable, so installer was not run.
- LaunchDaemon execution with new wrapper: not verified yet because install/load requires sudo.

## Exact Next Operator Commands

From repo root, in an administrator-capable shell:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload || true
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh load
launchctl print system/com.steelguitarrag.private-preview | grep -E 'state|pid|last exit|runs|path|program|working directory'
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
```

Expected after this repo fix:

- `program` should be `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`.
- `working directory` should be `/usr/local/libexec/steel-guitar-rag`.
- The old `Operation not permitted` on the repo wrapper path should stop.

If launchd then reaches the Python app but cannot bind because manual `screen` still owns `8770`, stop only the known manual session:

```bash
screen -S steel-rag-private-preview -X quit
```

Then restart or load the LaunchDaemon:

```bash
deploy/macos/install-private-preview-launchdaemon.sh restart
deploy/macos/install-private-preview-launchdaemon.sh version
```

If `restart` reports the service is not bootstrapped, use:

```bash
deploy/macos/install-private-preview-launchdaemon.sh load
deploy/macos/install-private-preview-launchdaemon.sh version
```

If the installed wrapper executes but the log changes to a `cannot cd to repo` style failure, create or choose a runtime checkout outside `~/Documents`, then reinstall with `STEEL_RAG_REPO_DIR` pointing to that path. Do not copy private/generated/vector material unless that exact data move is approved.

## Whether Launchd Can Execute The Wrapper

Not verified in the live system yet.

The repo fix makes the rendered plist use the daemon-safe installed wrapper path, but the currently loaded system plist still points to the old repo wrapper until privileged install/load is run.

## Whether Port 8770 Remains Owned By Manual Screen

Yes.

`lsof` shows the manual Python process still owns `127.0.0.1:8770`. This is intentional until launchd execution is fixed.

## Protected-Preview Smoke Status

Protected-preview smoke remains blocked.

Do not treat local `/api/version` or browser checks as launchd-supervised smoke until launchd owns `127.0.0.1:8770`.

## Risks

Risk level: **Medium**.

Reasons:

- The repo fix changes the deployment control path, so the next privileged install should be done carefully.
- The installed wrapper path should fix the current `Operation not permitted` program/working-directory failure, but the repo checkout path under `~/Documents` may still be denied when the wrapper tries to `cd`.
- Manual `screen` still owns the live port, preserving availability but blocking final launchd bind.
- The currently loaded LaunchDaemon is still retrying the old failing path until reinstalled/unloaded.

Rollback:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

The manual `screen` process should remain running until launchd is confirmed healthy.

## Human Decision Needed

Yes.

Run the privileged operator commands above. If the remaining failure is repo-path access, choose whether to:

1. create a runtime checkout outside `~/Documents`;
2. use a user LaunchAgent instead of a system LaunchDaemon;
3. grant macOS privacy/full-disk access to the launchd execution path.

## Safe-To-Stage Exact File List

- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
- `deploy/macos/install-private-preview-launchdaemon.sh`
- `docs/mac-mini-private-preview-launchd.md`
- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-permission-fix.md`

## Files That Must Not Be Staged

- Any unrelated dirty or parked files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, source-inbox raw/provenance files, scraper output, raw data, generated corpus output, private env files, rendered plists, Cloudflare tunnel tokens, credentials, `.wrangler/`, private source material, raw design assets, and unrelated UI/backend/test files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Commit Readiness

Safe to commit if the staged diff contains only the exact files listed above.

## Suggested Next Step

After this commit, run:

```text
Lane 12: Apply the launchdaemon permission fix from current HEAD with an administrator-capable shell, verify the installed plist now runs /usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh, keep manual screen alive until launchd execution reaches the app, then stop only the known steel-rag-private-preview screen if port 8770 is the final blocker. Verify /api/version from launchd and run protected-preview browser smoke.
```
