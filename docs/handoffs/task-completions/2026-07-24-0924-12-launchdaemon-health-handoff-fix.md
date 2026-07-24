# LaunchDaemon health handoff fix

## Task summary

The exact `2af97f5d` release did start under launchd during activation and served
successful live, ready, and version responses for the full verification window.
Activation was incorrectly rejected because `/api/version` returned the
repository's 8-character abbreviation (`2af97f5d`) while the installer required
it to equal a 7-character slice (`2af97f5`) of the expected full SHA. The
supervision check was therefore never reached. The subsequent immediate rollback
bootstrap failed with launchd error 5 and left the daemon unloaded.

This slice hardens only the private-preview activation script. It:

- reads the launchd job through normal access with a non-interactive privileged
  fallback;
- accepts a minimum-7-character API SHA only when it is a prefix of the exact
  expected commit;
- parses launchd state and PID explicitly;
- accepts the listener only when it is the launchd PID or a descendant owned by
  the configured runtime user;
- emits the last supervision failure reason on timeout;
- retries launchd bootstrap after a short settling interval; and
- exposes `verify-supervised` for non-mutating deployment verification.

The exact application release remains manually live at `2af97f5d` on port 8770
while the durable handoff is repaired.

## Files changed

- `deploy/macos/install-private-preview-launchdaemon.sh`
- `tests/test_private_preview_deploy.py`
- `docs/handoffs/task-completions/2026-07-24-0924-12-launchdaemon-health-handoff-fix.md`

No application behavior, source material, corpus data, validation or sealed-test
data, embeddings, vectors, auth policy, DNS, Cloudflare policy, or secrets were
changed.

## Tests and checks

- `bash -n deploy/macos/install-private-preview-launchdaemon.sh` — pass.
- `.venv/bin/python -m pytest -q tests/test_private_preview_deploy.py` —
  8 passed.
- `.venv/bin/python -m pytest -q tests/test_private_preview_deploy.py tests/test_runtime_server.py`
  — 10 passed.
- `git diff --check -- deploy/macos/install-private-preview-launchdaemon.sh tests/test_private_preview_deploy.py`
  — pass.
- `shellcheck` — skipped because it is not installed.
- Current manual `/health/live` — pass.
- Current manual `/health/ready` — pass.
- Current manual `/api/version` — exact `2af97f5d`.

## Integration notes

The next activation must use a new detached release created from the commit that
contains this deployment fix. The activation still requires one administrator
command because installing and bootstrapping a system LaunchDaemon is privileged.
After activation, Lane 12 must verify launchd state, listener ancestry, exact
version, and protected-browser behavior.

## Risk assessment

Medium operational risk until the corrected LaunchDaemon activation completes.
The app is healthy now, but its current process is terminal-supervised rather
than launchd-supervised. The code change itself is low risk and isolated to the
macOS private-preview installer.

## Human decision needed

No product decision. One administrator activation command will be required
after the corrected detached release is ready.

## Safe-to-stage exact file list

- `deploy/macos/install-private-preview-launchdaemon.sh`
- `tests/test_private_preview_deploy.py`
- `docs/handoffs/task-completions/2026-07-24-0924-12-launchdaemon-health-handoff-fix.md`

## Files that must not be staged

- Existing unrelated dirty or untracked handoffs.
- `docs/handoffs/task-completions/integration-status.md` in this implementation
  commit.
- Private corpus, source, review, validation, sealed-test, environment,
  database, vector, embedding, log, and release-worktree artifacts.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 corrected detached-release
activation and protected-preview verification.

## Commit readiness

Safe to commit

## Suggested next step

Commit the three exact files, prepare an exact detached release from that
commit, activate it once with the current listener PID as the replacement
origin, and verify the durable protected preview.
