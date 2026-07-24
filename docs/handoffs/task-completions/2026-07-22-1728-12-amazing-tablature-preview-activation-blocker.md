# Amazing Tablature protected-preview activation blocker

## Task summary

Prepared and preflighted the exact detached protected-preview release for commit `4b443c79a01f9a615b2cef36763e9d94c4dd3ab1`. Activation could not complete because macOS required the local administrator password. The password prompt was canceled safely; no password was entered or exposed.

The existing loopback preview remains available but reports stale runtime SHA `3cb63c3`. It was not presented as proof of the new release, and protected browser smoke was not run against the stale runtime.

## Files changed

- `docs/handoffs/task-completions/2026-07-22-1728-12-amazing-tablature-preview-activation-blocker.md`

Prepared release directory outside the repository:

- `~/.steel-rag/releases/4b443c7` — clean detached checkout of exact commit `4b443c79a01f9a615b2cef36763e9d94c4dd3ab1` with the repository virtual environment linked as documented

No runtime, source, corpus, validation, sealed-test, auth, DNS, Tunnel, Access, or secret file was modified by the failed activation attempt.

## Tests and checks

- Exact-release preflight: passed; plist lint passed and exact detached SHA was validated.
- Current loopback `/api/version`: HTTP 200, but `git_sha=3cb63c3` (stale by design until activation).
- Protected-preview activation: blocked at macOS administrator password prompt.
- Protected browser smoke: not run because the runtime does not yet match the expected SHA.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke pending; no API fallback reported as browser smoke
- Exact browser URL tested: not tested against the stale runtime
- Cache-busted URL tested: not tested
- Exact URL the user should use after activation: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=arrangement-engine-4b443c7-20260722`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted because version freshness failed
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `4b443c79a01f9a615b2cef36763e9d94c4dd3ab1`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `3cb63c3`; expected `4b443c7`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not retested
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after the user completes the administrator-authorized activation
- Do not test these URLs: validation or sealed-test review URLs; stale discovery packet URLs
- Known caveats: activation is the only remaining release blocker; local browser smoke and all repository tests already pass

## Integration notes

From the repository root, the user must run this documented activation command and enter the macOS administrator password when prompted:

```bash
STEEL_RAG_REPO_DIR="$HOME/.steel-rag/releases/4b443c7" \
STEEL_RAG_DATA_DIR="$HOME/Documents/Steel Guitar RAG" \
STEEL_RAG_EXPECTED_GIT_SHA="4b443c79a01f9a615b2cef36763e9d94c4dd3ab1" \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

After it reports success, Lane 12 should verify `/health/live`, `/health/ready`, and `/api/version`, then run authenticated browser smoke at the exact cache-busted URL above. Do not use listener termination as a deployment mechanism.

`docs/handoffs/task-completions/integration-status.md` contains unrelated pre-existing dirty work and was intentionally not edited or staged.

## Risk assessment

Low. The activation stopped before privileged state changed. The prior release remains running. The exact new release already passed preflight and can be activated using the canonical runbook.

## Human decision needed

Yes: enter the local macOS administrator password for the exact activation command. No musical validation or product decision is needed.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-1728-12-amazing-tablature-preview-activation-blocker.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- Everything under `corpus-private/`
- Raw source images, validation data, sealed-test data, embeddings, vector stores, credentials, environment files, logs, and generated reports

## Recommended next lane

Lane 12 Self-Hosted Deployment after the one administrator-authorized activation command completes.

## Commit readiness

Safe to commit

## Suggested next step

Run the exact activation command, then tell Codex `Activated` so Lane 12 can perform version, health, and authenticated protected-browser smoke without further training review.
