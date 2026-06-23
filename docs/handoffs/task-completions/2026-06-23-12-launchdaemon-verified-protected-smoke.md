# 2026-06-23 Lane 12 LaunchDaemon Verified Protected Smoke

## Task Summary

- Requested: verify the Mac mini LaunchDaemon, use the actual local `/api/version` as the protected-preview cache-bust source of truth, run browser smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<actual-api-version>`, check root behavior, and record user-smoke readiness.
- Completed: inspected repo governance, current git/runtime state, LaunchDaemon status, local `/api/version`, Cloudflare Tunnel status, durable app logs, and current `127.0.0.1:8770` port ownership.
- Intentionally not changed: did not modify app code, LaunchDaemon files, Cloudflare Access policy, DNS, auth settings, tunnel token values, corpus, Chroma, embeddings, scraping, source data, product behavior, or unrelated dirty work.

## Pass / Warn / Fail

**Fail / blocked.**

The protected-preview browser smoke was not run because the app is still not launchd-supervised. The installed LaunchDaemon is repeatedly failing before startup, and the live `127.0.0.1:8770` listener is still the old detached `screen` Python process.

Running browser prompts now would verify the manual fallback process, not the requested LaunchDaemon-supervised runtime.

## Branch And Head State

- Branch: `feature/answer-api`
- Starting HEAD: `c08cc95 feat: add deterministic G harmonized scale rules`
- Final HEAD before handoff commit: `c08cc95 feat: add deterministic G harmonized scale rules`
- Actual local `/api/version` git SHA: `c08cc95`
- `/api/version` matches current HEAD: **Yes**
- Important caveat: the matching version is being served by the old manual `screen` process, not by the LaunchDaemon.

## Runtime Version Result

Commands:

```bash
deploy/macos/install-private-preview-launchdaemon.sh version
curl -sS --max-time 5 http://127.0.0.1:8770/api/version
```

Observed result:

```json
{
  "git_sha": "c08cc95",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-23T15:34:18.101766+00:00",
  "python_module": "pocketsteel.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

Because `/api/version` reports `c08cc95`, the correct cache-busted protected-preview URL for a future smoke attempt is:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=c08cc95
```

The conditional G 5&8 harmonized-scale prompt applies once the launchd-supervised runtime is actually active.

## LaunchDaemon Supervision Status

The LaunchDaemon plist exists:

```text
/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
```

`launchctl print system/com.steelguitarrag.private-preview` reports:

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
runs = 46
last exit code = 126
```

`deploy/macos/install-private-preview-launchdaemon.sh status` could not run through the wrapper because this Codex session still has no interactive sudo terminal:

```text
sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
sudo: a password is required
```

The direct `launchctl print` output above is the authoritative service state captured for this run.

## Current Port Owner

`127.0.0.1:8770` is still owned by the previous manual `screen` process:

```text
Python PID 98944 listening on 127.0.0.1:8770
```

That means the public Cloudflare route is still ultimately backed by the manual process, not the installed LaunchDaemon.

## Durable Log Path Status

Durable app log path exists:

```text
/Users/cory/Library/Logs/steel-guitar-rag
```

Observed files:

```text
app.out.log: 0 bytes
app.err.log: 10120 bytes
```

`app.err.log` contains repeated LaunchDaemon failures:

```text
shell-init: error retrieving current directory: getcwd: cannot access parent directories: Operation not permitted
bash: /Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh: Operation not permitted
```

This is consistent with a macOS service/privacy/path-access problem for a system LaunchDaemon executing from `~/Documents/Pocket Steel`.

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
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=c08cc95
- Exact URL the user should use: Not cleared by this run
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: c08cc95
- Version endpoint: /api/version
- Version endpoint result: c08cc95 on feature/answer-api, but served by manual screen process
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

Protected-preview browser smoke was not run. This is intentional: the task goal was launchd-supervised runtime smoke, and the LaunchDaemon does not own the app port yet.

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
- `Show me a G harmonized scale on strings 5 and 8.`

The G 5&8 prompt is included in the pending list because `/api/version` reports `c08cc95`.

## Root URL Behavior

Root behavior was not browser-tested because launchd supervision is blocked.

Planned root URL:

```text
https://app.steelguitarrag.com/?v=c08cc95
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
tail -n 40 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
```

Results:

- `git diff --check`: passed.
- Local `/api/version`: reachable and reports `c08cc95`.
- LaunchDaemon: installed but not running the app; `state = spawn scheduled`, `last exit code = 126`.
- Durable app logs: present.
- LaunchDaemon stderr: repeated `Operation not permitted` errors for the repo path.
- Cloudflare Tunnel: running.
- Protected-preview browser smoke: skipped due launchd blocker.

Skipped tests:

- Browser smoke skipped because the launchd-supervised runtime was not active.
- Broad tests skipped; no app code was changed.

## Files Changed

Changed files:

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-verified-protected-smoke.md`

Created files:

- None; this updates the existing Lane 12 handoff path.

Deleted files:

- None.

Generated artifacts:

- None.

## Integration Notes

- The app still works locally only because a manual `screen` process owns port `8770`.
- The installed LaunchDaemon cannot currently execute the wrapper from `~/Documents/Pocket Steel`.
- Do not stop the manual `screen` process until a corrected supervised runtime can bind `127.0.0.1:8770`.
- The next smoke URL should use `c08cc95` unless `/api/version` changes again after service repair.

## Risk Assessment

Risk level: **Medium**.

Reasons:

- The app remains dependent on manual `screen` despite the LaunchDaemon being installed.
- The failing LaunchDaemon continues retrying and appending stderr output.
- Reboot resilience is not achieved yet for the app process.
- Cloudflare Tunnel is healthy, so the public route can still reach whichever process owns `8770`; currently that is manual screen.

Rollback notes:

- If the failing LaunchDaemon should be stopped while preserving the manual process, use an administrator-capable shell:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

## Human Decision Needed

Yes.

Resolve how the supervised app service should access the runtime path. Candidate next actions:

1. Move or copy the service runtime out of `~/Documents` into an operator-approved service path that a system LaunchDaemon can access.
2. Convert to a user LaunchAgent if user-login startup is acceptable.
3. Adjust macOS privacy/full-disk access for the launchd execution path if that is the chosen operations model.

This should be handled as a focused Lane 12 service-hardening task before protected-preview browser smoke is considered valid.

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
Lane 12: Fix the Mac mini app LaunchDaemon startup failure where `/Users/cory/Documents/Pocket Steel/deploy/macos/run-private-preview-app.sh` exits 126 with `Operation not permitted`. Preserve the manual screen process until the LaunchDaemon can bind 127.0.0.1:8770, do not touch DNS/auth/corpus/Chroma/secrets, and write a handoff with the chosen macOS service path or LaunchAgent/LaunchDaemon decision. After fix, rerun protected-preview browser smoke at https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=c08cc95.
```
