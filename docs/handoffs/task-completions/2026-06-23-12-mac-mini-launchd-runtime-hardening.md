# 2026-06-23 Lane 12 Mac Mini Launchd Runtime Hardening

## Task summary

Requested:
- Keep the Mac mini as the protected-preview origin.
- Add repo-managed service assets so the protected-preview app can be launched by a supervised boot service with durable logs.
- Document privileged operator steps for launchd, Cloudflare Tunnel token handling, power settings, Ollama, and protected-preview smoke.
- Preserve unrelated dirty work and avoid secrets, DNS, Cloudflare Access policy, corpus, Chroma/vector, embedding, scraping, app behavior, UI, answer-routing, and product-copy changes.

Completed:
- Added a LaunchDaemon plist template for the private-preview app.
- Added a non-secret service wrapper that runs the same protected-preview runtime entrypoint currently used on port `8770`.
- Added an operator installer/control script that renders, lints, installs, loads, unloads, restarts, checks status, tails logs, and curls `/api/version`.
- Added a Mac mini private-preview launchd runbook with durable log guidance, Cloudflare Tunnel token-handling guidance, power checks, Ollama checks, and protected-preview smoke requirements.
- Validated the scripts and plist template without installing or loading the service.

Intentionally not changed:
- No app/backend/frontend product behavior changed.
- No DNS, Cloudflare Access policy, Cloudflare Pages config, tunnel config, or account settings changed.
- No Cloudflare Tunnel token was printed or committed.
- No privileged `sudo` install/load command was run.
- No app process was restarted.
- No protected-preview browser smoke was performed because the runtime was not restarted or service-loaded.
- No corpus, Chroma/vector store, embedding, source-inbox, private-source, scraper, or generated data job was run.

## Classification

- Lane: `12 Self-Hosted Deployment`
- Task type: deployment/runtime scripts plus docs handoff
- Task mode: RED deployment implementation explicitly approved by the task, limited to repo-managed non-secret service assets and documentation

Protected paths and systems preserved:
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/provenance files
- private env files
- Cloudflare Tunnel token values
- DNS and Cloudflare Access policy
- app/backend/frontend implementation behavior
- unrelated dirty work

## Starting state

- Branch: `feature/answer-api`
- Starting HEAD: `5f8af79 docs: record fretboard svg cache-bust smoke`
- Index before edits: clean
- Worktree before edits: broad unrelated dirty/untracked work parked
- `PLAN.md`: missing
- `plan.md`: missing

Current runtime evidence before implementation:
- App process still ran manually through a detached `screen` session named `steel-rag-private-preview`.
- App listener: `127.0.0.1:8770`.
- App command shape: `.venv/bin/python scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 --answer-auth-mode production --auth-provider cloudflare-access`.
- Current manual app logs still go to `/tmp/steel-rag-private-preview-8770.log`.
- `launchctl print system/com.steelguitarrag.private-preview` reported the service was not found, confirming the app is not yet launchd-supervised.
- Cloudflare Tunnel remains boot-started by `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`.
- Cloudflare Tunnel plist metadata still indicates inline token use; the token was not printed.
- AC sleep remains enabled in `pmset` output (`sleep 1`).
- Restart after power failure remains disabled in `pmset` output (`autorestart 0`, `autorestartatconnect 0`).
- FileVault remains off.

## Files changed

Created:
- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
- `deploy/macos/run-private-preview-app.sh`
- `deploy/macos/install-private-preview-launchdaemon.sh`
- `docs/mac-mini-private-preview-launchd.md`
- `docs/handoffs/task-completions/2026-06-23-12-mac-mini-launchd-runtime-hardening.md`

Changed files:
- None outside the created files above.

Deleted files:
- None.

Generated artifacts:
- Temporary rendered plist at `/tmp/com.steelguitarrag.private-preview.rendered.plist` for validation only; not staged or committed.

## Implementation details

### LaunchDaemon template

`deploy/macos/com.steelguitarrag.private-preview.plist.template` defines:
- label `com.steelguitarrag.private-preview`;
- `RunAtLoad=true`;
- `KeepAlive` with `SuccessfulExit=false` for abnormal-exit restart;
- `UserName` / `GroupName` placeholders so the app runs as the repo owner instead of root;
- loopback host and port environment placeholders;
- durable stdout/stderr log paths under `~/Library/Logs/steel-guitar-rag/`;
- wrapper entrypoint under `deploy/macos/run-private-preview-app.sh`.

The plist is a template. It contains no secrets and no token-bearing values.

### Service wrapper

`deploy/macos/run-private-preview-app.sh`:
- refuses non-loopback hosts;
- requires `STEEL_RAG_REPO_DIR`, `STEEL_RAG_ENV_FILE`, and `STEEL_RAG_LOG_DIR`;
- uses `.venv/bin/python` directly;
- sources the private preview env file at runtime without printing it;
- defaults to production Cloudflare Access auth mode;
- defaults to `hybrid_private_first` retrieval mode;
- defaults to the v2 Chroma path and collection already used by protected preview;
- executes `scripts/serve_v2_rerank_smoke.py` on `127.0.0.1:8770`.

### Installer/control script

`deploy/macos/install-private-preview-launchdaemon.sh` supports:
- `render`
- `install`
- `load`
- `unload`
- `restart`
- `status`
- `tail`
- `version`

The script keeps privileged operations explicit. `install`, `load`, `unload`, `restart`, and `status` use `sudo` because they operate in the system launchd domain or `/Library/LaunchDaemons`.

Default operator commands:

```bash
deploy/macos/install-private-preview-launchdaemon.sh render > /tmp/com.steelguitarrag.private-preview.plist
plutil -lint /tmp/com.steelguitarrag.private-preview.plist
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh load
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
deploy/macos/install-private-preview-launchdaemon.sh restart
deploy/macos/install-private-preview-launchdaemon.sh tail
deploy/macos/install-private-preview-launchdaemon.sh unload
```

## Checks run

Repo/governance and state:
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' agents.md`
- `sed -n '1,220p' README.md`
- `sed -n '1,220p' docs/handoffs/task-completions/integration-status.md`
- `sed -n '1,260p' docs/handoffs/task-completions/2026-06-23-12-mac-mini-reliability-audit.md`
- `git status --short`
- `git diff --cached --name-only`
- `git diff --check`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -1 --oneline`

Runtime/system inspection:
- `pgrep -fl 'serve_v2_rerank_smoke|serve_answer_smoke' || true`
  - Result: manual `screen` process and Python app process observed.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true`
  - Result: Python listening on `127.0.0.1:8770`.
- Sanitized plist inspection of `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`
  - Result: `RunAtLoad=True`, `KeepAlive={'SuccessfulExit': False}`, durable `/Library/Logs` paths, inline token present but not printed.
- `pmset -g custom`
  - Result: AC `sleep 1`, `autorestart 0`, `autorestartatconnect 0`.
- `fdesetup status`
  - Result: `FileVault is Off.`
- `launchctl print system/com.steelguitarrag.private-preview`
  - Result: service not found; app service not currently loaded.

Validation checks:
- `bash -n deploy/macos/run-private-preview-app.sh deploy/macos/install-private-preview-launchdaemon.sh`
  - Result: pass.
- `plutil -lint deploy/macos/com.steelguitarrag.private-preview.plist.template`
  - Result: pass.
- `deploy/macos/install-private-preview-launchdaemon.sh render > /tmp/com.steelguitarrag.private-preview.rendered.plist`
  - Result: pass.
- `plutil -lint /tmp/com.steelguitarrag.private-preview.rendered.plist`
  - Result: pass.
- `shellcheck deploy/macos/run-private-preview-app.sh deploy/macos/install-private-preview-launchdaemon.sh`
  - Result: skipped because `shellcheck` is not installed.
- `git diff --check`
  - Result: pass.
- `curl -sS http://127.0.0.1:8770/api/version`
  - Result: `git_sha` `5f8af79`, branch `feature/answer-api`, `python_module` `steel_guitar_rag.api`, `retrieval_mode` `hybrid_private_first`, `auth_provider` `cloudflare_access`.
- `deploy/macos/install-private-preview-launchdaemon.sh version`
  - Result: same local `/api/version` response from the existing manual runtime.

## Protected-preview smoke

Not performed.

Reason:
- The app runtime was not restarted or loaded from the supervised service during this task.
- The task requires protected-preview smoke when the runtime is restarted or service-loaded; that condition was intentionally not met because installing/loading a system LaunchDaemon is a privileged host mutation that should be run as an operator step.

Required smoke URL after service load:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<final-commit>
```

## Integration notes

- The Mac mini remains the protected-preview origin.
- The repo now contains a concrete, non-secret LaunchDaemon path to move the app from a manual `screen` process to boot-time launchd supervision.
- The app is not actually launchd-supervised until the operator runs `install` and `load`.
- Durable app log paths are defined as `~/Library/Logs/steel-guitar-rag/app.out.log` and `~/Library/Logs/steel-guitar-rag/app.err.log`.
- Cloudflare Tunnel service remains existing boot-time infrastructure; no tunnel config was changed.
- Cloudflare Tunnel token handling was documented, not changed. A safer future path is to use a named tunnel config and credentials outside the repo with root-only permissions instead of inline token arguments.
- Mac sleep and restart-after-power-failure were documented, not changed.
- Ollama still needs a separate boot-supervision decision if answer generation requires it without an interactive login session.

## Risk assessment

- Risk: medium until operator install/load/smoke is completed.
- Reason: repo-managed assets validate, but the live app is still manually started. The reliability improvement is ready to apply but not active.
- Lower-risk aspects:
  - no secrets are committed;
  - no DNS/auth/tunnel config was mutated;
  - no app behavior changed;
  - scripts refuse non-loopback app bind host.
- Remaining operational risk:
  - applying the LaunchDaemon can interrupt the current manual protected-preview process if the same port is already in use;
  - Mac sleep and restart-after-power-failure settings are still not fixed;
  - Ollama boot availability is not proven;
  - Cloudflare Tunnel token remains inline in the existing host plist until a separate migration/rotation task.

Rollback notes:
- If the LaunchDaemon is loaded later, unload with:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

- If needed, return temporarily to the documented manual command in `docs/mac-mini-private-preview-launchd.md`.

## Blockers

- App is not yet launchd-supervised on the host.
- Protected-preview smoke from a supervised process remains pending.
- Mac AC sleep is still enabled.
- Restart after power failure is still disabled/not enabled.
- Ollama boot supervision remains unverified.
- Cloudflare Tunnel token remains inline in the existing system plist.

## Human decision needed

Yes:
- Run the privileged operator step to install/load the app LaunchDaemon.
- Decide whether to stop the current manual screen process before loading the LaunchDaemon to avoid port `8770` conflict.
- Approve Mac power changes:

```bash
sudo pmset -c sleep 0
sudo systemsetup -setrestartpowerfailure on
```

- Decide whether Ollama needs its own boot-time service.
- Decide whether to run a separate Cloudflare Tunnel token/config hardening task.

## Safe-to-stage exact file list

- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
- `deploy/macos/run-private-preview-app.sh`
- `deploy/macos/install-private-preview-launchdaemon.sh`
- `docs/mac-mini-private-preview-launchd.md`
- `docs/handoffs/task-completions/2026-06-23-12-mac-mini-launchd-runtime-hardening.md`

## Files that must not be staged

- Any unrelated dirty/untracked files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Private env files, Cloudflare tokens, rendered token-bearing plists, tunnel credentials, `.wrangler/`, and any secrets.
- DNS, Cloudflare Access, Cloudflare Pages, and account config files unless a later task explicitly scopes them.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, unrelated app code, unrelated tests, and parked handoffs.

## Recommended next lane

- Lane 12 Self-Hosted Deployment for operator install/load and protected-preview smoke.
- Lane 11 Auth / Security only if the Cloudflare Tunnel token/config hardening and rotation path is approved.
- Lane 01 Repo Steward to refresh `integration-status.md` after service load and smoke pass.

## Commit readiness

Safe to commit

## Suggested next step

Lane 12: install and load the Mac mini app LaunchDaemon from the committed service assets, stop the manual screen process if needed to free port `8770`, verify local `/api/version`, run protected-preview browser smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<service-commit>`, then refresh integration status if smoke passes.
