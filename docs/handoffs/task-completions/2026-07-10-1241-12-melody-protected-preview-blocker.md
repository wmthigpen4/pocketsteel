# Melody Exercise v0 Protected-Preview Blocker

## Task summary

Attempted the authorized protected-preview update after the green implementation commit `f37201a`. The live LaunchDaemon runtime remains at `da1a763`, and the installed wrapper predates the Melody preview flag. The documented install/restart path requires a host sudo password unavailable to Codex, so protected-preview smoke correctly stopped before claiming a pass or issuing a user-test URL.

No auth policy, DNS, Tunnel, secrets, environment file, corpus, Chroma, private source, or source-inbox content was changed.

## Files changed

- `docs/handoffs/task-completions/integration-status.md` — replaced stale history with a concise current snapshot.
- `docs/handoffs/task-completions/2026-07-10-1241-12-melody-protected-preview-blocker.md` — this blocker report.
- Deleted: none.
- Generated artifacts: none.

## Tests and checks

- Confirmed repository HEAD `f37201a955dfed5f0d2bc3dc46fbea6ef9bb7133`.
- Confirmed local protected service `/api/version` reports stale runtime `da1a763` with `cloudflare_access` and `hybrid_private_first`.
- Confirmed committed and installed wrappers differ with `cmp`; wrapper content or env secrets were not printed.
- Confirmed `sudo -n true` fails with `a password is required`.
- Public HTTP checks: root, direct UI, and `/api/version` return 302 to Cloudflare Access.
- In-app browser reached the Cloudflare Access email login page; authentication was not attempted.
- `git diff --check` must pass before this docs-only closeout is committed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke attempted; blocked before authenticated feature verification
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=f37201a-melody-v0-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: none until automated protected smoke passes
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted; login page reached
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: current checkout HEAD after the integration-status refresh, containing implementation commit `f37201a`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: stale `da1a763`; feature absent
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: redirects to Cloudflare Access when unauthenticated
- Whether app root `/` is expected to work: yes after authentication, but direct `/ui/...` remains the smoke target
- Whether `/ui/steel-guitar-rag-mock.html` works: redirects to Cloudflare Access when unauthenticated
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes after authentication and restart
- Who should test this URL: Codex after the privileged restart; then the user only after a pass
- Do not test these URLs: no user smoke against the stale runtime
- Known caveats: installed wrapper must be refreshed; API fallback is not browser smoke

## Integration notes

Required trusted-terminal commands:

```bash
cd ~/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh restart
```

Afterward, verify `/api/version` before browser smoke. Do not alter the private environment file merely to bypass the wrapper install.

## Risk assessment

- Risk: low for this docs-only closeout; medium remains for the pending runtime update.
- Rollback: no runtime action occurred. The live service remains on its pre-task runtime.

## Human decision needed

Yes: the user must authorize sudo locally by running the two exact documented commands. No password should be sent to Codex.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-10-1241-12-melody-protected-preview-blocker.md`

## Files that must not be staged

All other dirty and untracked paths.

## Recommended next lane

Lane 12 Self-Hosted Deployment after the privileged commands complete.

## Commit readiness

Safe to commit

## Suggested next step

Run the two privileged commands in a trusted local terminal, then tell Codex they completed so it can resume version verification and authenticated protected browser smoke.
