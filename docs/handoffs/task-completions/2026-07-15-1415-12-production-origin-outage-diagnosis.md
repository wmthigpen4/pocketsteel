# Production origin outage diagnosis

## Task summary

- Requested: explain why `https://app.steelguitarrag.com/` returns Cloudflare 502 and assess how Codex work can avoid taking the subscriber-facing app down.
- Lane: `12 Self-Hosted Deployment`.
- Task type: read-only incident diagnosis plus this required handoff.
- Task mode: GREEN for diagnosis and documentation. Restarting the app or changing launchd, Cloudflare, DNS, Access, deployment behavior, or secrets remains RED and was not performed.
- Confirmed root cause: the local app process on `127.0.0.1:8770` received `SIGTERM`, performed its new graceful shutdown, and exited successfully. The LaunchDaemon has `KeepAlive.SuccessfulExit=false`, so launchd did not restart a successful exit. Cloudflare Tunnel remained healthy and then returned 502 because the origin port refused connections.
- Intentionally not changed: runtime state, deployment configuration, launchd configuration, Cloudflare configuration, auth, DNS, secrets, application code, and protected/private data.

## Incident timeline and evidence

- `2026-07-15 08:50:10 CDT`: commit `7f99e61` (`Make answer follow-ups immediate`) completed.
- `2026-07-15 08:50:16 CDT`: the active runtime still returned `200` for `/api/version`.
- `2026-07-15 08:50:39 CDT`: `runtime.log` recorded `shutdown_requested signal=15` followed by `runtime_stopped`.
- Current app LaunchDaemon state: loaded but `not running`, `runs = 3`, `last exit code = 0`.
- Current port state: no listener on `127.0.0.1:8770`; local health, version, and UI requests fail with connection refused.
- Current Cloudflare Tunnel state: running with four registered connections. Tunnel logs report `dial tcp 127.0.0.1:8770: connect: connection refused`.
- First observed external refusal in the retained tunnel log: `2026-07-15 16:25:22 UTC` (`11:25:22 CDT`). The runtime log proves the origin had already stopped at `08:50:39 CDT`; no earlier external request is present in the inspected tunnel-log window.
- Live Chrome verification: `https://app.steelguitarrag.com/` displays Cloudflare `502: Bad gateway`, with Browser and Cloudflare working and Host error.
- Unauthenticated curl reaches Cloudflare Access and receives the expected login redirect. This confirms Access and the Cloudflare edge are reachable; an authenticated request proceeds to the absent origin and receives 502.

## Why the old deployment method became unsafe

- Earlier Lane 12 handoffs documented a narrow refresh method: terminate the process listening on port `8770` and rely on launchd to restart it.
- Commit `2b9036b` on 2026-07-13 added graceful SIGINT/SIGTERM handling. `SIGTERM` now stops the WSGI server cleanly and returns normally.
- The LaunchDaemon template still uses:

  ```text
  KeepAlive.SuccessfulExit = false
  ```

  That policy restarts crashes/nonzero exits but intentionally does not restart a clean exit.
- The two behaviors are individually reasonable but incompatible. A Codex preview refresh that sends `SIGTERM` now leaves the service down unless it explicitly starts/kickstarts the daemon afterward and verifies readiness.

## Availability assessment

The current topology is a single mutable Mac-hosted origin behind one fixed tunnel route. It has no second healthy backend, no zero-downtime cutover, and no automatic external recovery after this class of successful shutdown. It is appropriate for a protected preview but not yet a subscriber-grade production service.

Codex development can be isolated from availability, but that requires deployment guardrails rather than relying on agent caution alone:

1. Stop using listener termination as a deployment command.
2. Use one explicit supervised restart operation that waits for the old process to exit, starts/kickstarts the service, and fails unless `/health/live`, `/health/ready`, and `/api/version` pass.
3. Reconcile graceful shutdown with launchd supervision: either make the daemon always stay alive or ensure every intentional stop is paired with an explicit start. Add a regression check for the installed plist/wrapper combination.
4. Keep the subscriber runtime in an immutable, dedicated release directory. Codex worktrees, cleanup, tests, and commits must not be the directory serving live traffic.
5. For actual subscribers, put a stable proxy in front of two release ports and use blue/green deployment: start the new release, smoke it privately, switch traffic only after readiness, and keep the old release available for rollback.
6. Add external uptime checks and alerting for the public canonical route, origin readiness, and version drift. A 502 must page the operator immediately rather than wait for a user report.

## Files changed

- Created: `docs/handoffs/task-completions/2026-07-15-1415-12-production-origin-outage-diagnosis.md`.
- No code, runtime, deployment, auth, DNS, Cloudflare, secret, corpus, private-data, or generated-artifact file changed.

## Tests and checks

- Read `AGENTS.md`, `docs/private-preview-operations.md`, `docs/mac-mini-private-preview-launchd.md`, the latest Lane 12 reliability handoff, current integration status, and the July 15 cleanup handoffs.
- Ran `git status --short` before diagnosis: clean.
- Verified current Git HEAD: `cfd2cad`.
- Probed local `/health/live`, `/health/ready`, `/api/version`, and canonical UI path: all connection refused because port `8770` has no listener.
- Inspected sanitized app runtime logs and launchd state.
- Inspected Cloudflare Tunnel service state and origin-refusal log lines without exposing tunnel credentials or environment values.
- Verified the live 502 in the user's open Chrome tab.
- Did not run application tests because no implementation changed.
- Did not restart or deploy because those are RED actions and the request asked why the app is down rather than explicitly authorizing a production-state change.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/`
- Cache-busted URL tested: not applicable to an origin-availability check
- Exact URL the user should use: `https://app.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: existing authenticated Chrome session reached the origin-facing Cloudflare 502; unauthenticated curl received the expected Access login redirect
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: the deployed release must be chosen before restart; primary repository HEAD is `cfd2cad`, while the retained preview worktree is `3cb63c3`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: connection refused
- If version endpoint missing, how version is inferred: no running version can be inferred safely
- Whether app root `/` works: no; authenticated request receives 502
- Whether app root `/` is expected to work: yes, by redirecting to the canonical UI route
- Whether `/ui/steel-guitar-rag-mock.html` works: no; origin connection refused
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after an approved restoration, then the user
- Do not test these URLs: local `127.0.0.1` as proof of protected behavior; arbitrary later commits until the exact release is selected
- Known caveats: the exact release to restore must be chosen because the primary branch and retained preview worktree are at different commits

## Integration notes

- This is not a Cloudflare-wide outage and not a capacity overload. The fixed tunnel origin is absent.
- The shutdown closely follows the `7f99e61` commit and matches the historical Codex deployment technique. The logs prove `SIGTERM` and clean exit; they do not identify the shell/process that sent the signal, so attribution to a specific agent command is a strong operational inference rather than a captured command audit record.
- Restoration should not blindly start the primary checkout. The retained preview worktree is `3cb63c3`, the primary repository is `cfd2cad`, and many commits landed between them. Lane 12 must select an exact reviewed release, then start and verify it.

## Risk assessment

- Current availability risk: high; the subscriber-facing hostname is down for authenticated users.
- Diagnosis/documentation risk: low; no service or configuration state changed.
- Recurrence risk: high until the graceful-shutdown/launchd mismatch and deployment method are fixed.
- Rollback: not applicable to this docs-only diagnosis.

## Human decision needed

- Yes.
- Authorize a Lane 12 restoration and specify whether to restore the retained reviewed preview release `3cb63c3` immediately or first audit/select a newer exact commit.
- Separately approve the deployment-reliability hardening scope: launchd restart semantics, guarded health-checked deploy command, dedicated immutable runtime release path, and subscriber-grade blue/green cutover/monitoring design.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-15-1415-12-production-origin-outage-diagnosis.md`

## Files that must not be staged

- Every implementation, deployment, plist, wrapper, auth, DNS, Cloudflare, secret, environment, corpus, vector, source-inbox, private-data, brand/design, and generated path.
- No stash contents or runtime worktree contents.

## Recommended next lane

- Lane 12 for exact-release restoration and protected smoke after explicit approval.
- Then Lane 12 plus Lane 15 for deployment-reliability implementation and failure-mode regression testing.

## Commit readiness

Safe to commit

## Suggested next step

Authorize Lane 12 to restore exact release `3cb63c3` now, verify all local health/version routes and the authenticated canonical URL, then prepare a separate reviewed hardening change that removes listener-kill deployment and introduces health-gated cutover.
