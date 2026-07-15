# Origin reliability hardening implementation

## Task summary

- Requested: restore reviewed release `3cb63c3` and harden deployment end-to-end so Codex work cannot leave the subscriber-facing app down.
- Lane: `12 Self-Hosted Deployment`, with Lane 15 regression verification and Lane 01 exact-path commit readiness.
- Task type: mixed deployment recovery, deployment tooling, tests, documentation, protected browser smoke, and commit.
- Task mode: RED deployment work explicitly approved by the user after the outage diagnosis.
- Restored the exact reviewed `3cb63c3` release as a temporary loopback origin without changing Cloudflare, Access, DNS, secrets, corpus contents, or vector contents.
- Implemented the smallest production-safety slice for the demonstrated failure mode. The system is no longer designed to rely on killing the listener and hoping launchd restarts it.

## Files changed

- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
  - Uses `KeepAlive=true`, including after clean graceful exits.
  - Separates the immutable code release from the shared local data directory.
- `deploy/macos/install-private-preview-launchdaemon.sh`
  - Adds exact-SHA `preflight`, `activate`, and verified `restart` flows.
  - Requires a clean detached release checkout under the dedicated runtime/release root.
  - Requires live, ready, exact-version, and launchd-listener PID agreement before supervised activation succeeds.
  - Restores the previous plist and bootstraps it when activation fails.
  - Supports a narrowly validated emergency-origin PID handover without permitting arbitrary process termination.
  - Makes read-only `status` and `verify` usable without sudo.
- `deploy/macos/run-private-preview-app.sh`
  - Supports a separate `STEEL_RAG_DATA_DIR` so a code-only immutable worktree can use existing read-only corpus/vector paths.
- `tests/test_private_preview_deploy.py`
  - Covers always-on plist rendering, missing exact-SHA refusal, detached-release preflight refusal, live/ready/version verification, timeout validation, and early activation refusal.
- `docs/private-preview-operations.md`
- `docs/mac-mini-private-preview-launchd.md`
- `docs/current-commands.md`
- `docs/recovery-procedure.md`
  - Replace listener-kill guidance with exact-release, health-gated activation/restart instructions.
- `docs/handoffs/task-completions/2026-07-15-1415-12-production-origin-outage-diagnosis.md`
- This handoff.

No application answer/UI behavior, auth policy, DNS, Cloudflare policy, secret, corpus/vector content, private source, source-inbox, scraper, embedding, brand/design, or generated artifact changed.

## Tests and checks

- `bash -n deploy/macos/install-private-preview-launchdaemon.sh deploy/macos/run-private-preview-app.sh` — passed.
- Rendered hardened plist plus `plutil -lint` — passed; `KeepAlive=true` and the separate data directory were verified.
- Exact `3cb63c3` detached-release preflight — passed.
- Hardened wrapper live smoke on alternate loopback port `8789` — live, ready, and `/api/version=3cb63c3` passed; the temporary test process then shut down cleanly.
- Focused deployment/runtime tests — `8 passed`.
- Full pytest after the main implementation — `1181 passed in 55.70s`.
- `git diff --check` — passed.
- Restored local origin on `127.0.0.1:8770` — live and ready passed, `/api/version` reports `3cb63c3`, root redirects, canonical UI returns 200.
- Authenticated Chrome protected check — the prior 502 cleared and the canonical home UI rendered through Cloudflare Access and Tunnel.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/`
- Cache-busted URL tested: final post-install URL will use `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=origin-hardening-3cb63c3-20260715`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=origin-hardening-3cb63c3-20260715`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in the existing authenticated Chrome session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: runtime release `3cb63c3`; deployment-tooling commit pending exact-path commit
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `3cb63c3`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; redirects to the canonical UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after supervised installation, then the user
- Do not test these URLs: local loopback as proof of Cloudflare behavior; arbitrary primary-branch HEAD as the deployed app
- Known caveats: the restored origin is temporarily attached to the current Codex process until the committed hardened LaunchDaemon is installed with native administrator authorization

## Integration notes

- The exact subscriber runtime remains `3cb63c3`; newer primary-branch commits are not implicitly promoted.
- The hardening intentionally does not add a new reverse-proxy dependency or change Tunnel/Access policy. It prevents persistent shutdown, dirty/branch deployment, version drift, false-positive health success, and unverified restart success. Full multi-origin blue/green infrastructure remains a separate architecture upgrade if true zero-second cutovers are required.
- The installed system plist/wrapper still require one administrator-authorized activation after this slice is committed.

## Risk assessment

- Implementation risk: medium because launchd behavior and deployment tooling change, bounded by exact release validation, rollback, PID ownership checks, focused tests, full pytest, alternate-port wrapper smoke, and post-install protected smoke.
- Current availability risk: low while the temporary restored process remains attached and verified.
- Residual infrastructure risk: the Mac, ISP, and tunnel remain single points of failure. This slice prevents the demonstrated Codex restart outage but does not create multi-host failover.
- Rollback: reinstall the previous plist/wrapper from the saved activation rollback path or revert the scoped deployment-tooling commit; do not reset or delete release/data paths.

## Human decision needed

- No additional product decision.
- One native macOS administrator authorization is operationally required to install and bootstrap the hardened LaunchDaemon. The user already approved this deployment scope; no password should be shared with Codex.

## Safe-to-stage exact file list

- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
- `deploy/macos/install-private-preview-launchdaemon.sh`
- `deploy/macos/run-private-preview-app.sh`
- `tests/test_private_preview_deploy.py`
- `docs/private-preview-operations.md`
- `docs/mac-mini-private-preview-launchd.md`
- `docs/current-commands.md`
- `docs/recovery-procedure.md`
- `docs/handoffs/task-completions/2026-07-15-1415-12-production-origin-outage-diagnosis.md`
- `docs/handoffs/task-completions/2026-07-15-1428-12-origin-reliability-hardening.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (coordination refresh remains separate).
- All environment files, logs, temporary PID files, installed system files, runtime worktrees, stashes, corpus/vector paths, source-inbox, private data, secrets, Cloudflare material, public/brand/design assets, scraper outputs, embeddings, and generated artifacts.

## Recommended next lane

- Lane 01 exact-path commit under autopilot approval, then Lane 12 administrator-authorized activation and final authenticated protected smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the exact safe list, run the hardened exact-release preflight from the commit, activate `3cb63c3` with its separate data directory and the validated emergency-origin PID handover, then verify launchd PID ownership, local health/version, root/canonical routes, Cloudflare Access, and the cache-busted protected URL.
