# Lane 12 smoke-feedback protected-preview final

## Pass / warn / fail

**Blocked / fail for browser smoke completion.**

The runtime was successfully refreshed to the intended current HEAD `1c0bbd6`, but authenticated protected-preview browser smoke could not proceed because the in-app browser landed on the Cloudflare Access login page for the exact protected-preview URL.

API fallback was not used as browser-smoke proof.

## Task summary

Requested:

- Confirm Lane 15 QA approval for the smoke-feedback implementation state.
- Refresh the protected-preview runtime to the intended committed HEAD.
- Run authenticated Cloudflare Access browser smoke for the main app, Explorer, and prompt matrix.

Completed:

- Confirmed Lane 15 QA passed with warning at `1c0bbd6`.
- Confirmed starting HEAD was `1c0bbd6`.
- Confirmed running runtime was stale at `ddd7953`.
- Restarted the launchd-supervised app process by terminating stale PID `72903`; launchd restarted it as PID `94266`.
- Confirmed `/api/version` now reports `1c0bbd6`.
- Confirmed listener is Python on `127.0.0.1:8770`.
- Confirmed LaunchDaemon owns the app runtime.
- Confirmed manual `screen` runtime is absent.
- Confirmed Cloudflare Tunnel process is running.
- Attempted protected-preview browser smoke at the exact current-HEAD main app URL.
- Stopped before prompt smoke because Cloudflare Access login blocked the browser session.

Intentionally not changed:

- No backend/UI implementation files.
- No DNS, Cloudflare Access policy, tunnel config, auth settings, secrets, corpus, Chroma, embeddings, scraper output, private-source data, or source-inbox data.
- No API fallback was reported as protected-preview browser smoke.

## Lane 15 approval

Latest relevant QA handoff inspected:

- `docs/handoffs/task-completions/2026-06-23-15-main01-focused-smoke-feedback-qa.md`

Lane 15 result:

- Pass with warning.
- Current commit under QA: `1c0bbd6 fix: separate backstage and fretboard header actions`.
- Lane 15 explicitly recorded no remaining QA blocker for Lane 12, with protected-preview restart/smoke still required.
- Lane 15 warning: prior loopback runtime was stale at `ddd7953`, so Lane 12 had to restart/verify protected preview.

## Branch and commits

- Branch: `feature/answer-api`
- Starting HEAD: `1c0bbd6`
- Runtime commit expected: `1c0bbd6`
- Runtime commit reported after restart: `1c0bbd6`

Recent commits inspected:

```text
1c0bbd6 fix: separate backstage and fretboard header actions
2d3d662 fix: expose all explorer keys and backstage link
5031f43 fix: normalize accidentals and route flat-key string groupings
0c050ee fix: polish smoke feedback UI and explorer controls
3811a8c docs: refresh harmonized scale integration status
2728154 docs: record post-restart harmonized scale smoke
ddd7953 docs: record displayed harmonized scale protected smoke
0ad025f fix: prevent harmonized scale fallback display
4d58cda docs: record browser harmonized scale protected smoke
db6ae81 fix: route browser harmonized scale prompts deterministically
```

## Runtime refresh evidence

Before refresh:

- `/api/version`: `git_sha=ddd7953`
- Listener PID: `72903`
- PID start time: `Tue Jun 23 13:18:17 2026`
- Runtime was stale relative to current HEAD `1c0bbd6`.

Restart path:

- `launchctl kickstart -k system/com.steelguitarrag.private-preview` failed with `Operation not permitted`.
- `deploy/macos/install-private-preview-launchdaemon.sh restart` failed because non-interactive `sudo` could not read a password.
- Because the process was stale and launchd supervision was active, stale user-owned PID `72903` was terminated with `SIGTERM`.
- LaunchDaemon restarted the app automatically as PID `94266`.

After refresh:

```json
{
  "git_sha": "1c0bbd6",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-23T19:54:06.883215+00:00",
  "python_module": "pocketsteel.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

Listener:

- PID: `94266`
- Start time: `Tue Jun 23 14:54:06 2026`
- Command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`

LaunchDaemon:

- Label: `system/com.steelguitarrag.private-preview`
- State: running
- PID: `94266`
- Runs: `26`
- Program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- Repo env: `STEEL_RAG_REPO_DIR=/Users/cory/Documents/Pocket Steel`
- Host/port env: `STEEL_RAG_HOST=127.0.0.1`, `STEEL_RAG_PORT=8770`
- Logs:
  - `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`

Manual screen runtime:

- `screen -ls`: no sockets found.

Cloudflare Tunnel:

- `com.cloudflare.cloudflared` LaunchDaemon is running.
- `cloudflared` process is present.
- Tunnel token contents were not copied into this handoff.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke attempted, blocked by Cloudflare Access login
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Exact URL the user should use after login: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: blocked; in-app browser landed on Cloudflare Access login.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `1c0bbd6`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=1c0bbd6`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not browser-smoked after restart because Cloudflare Access login blocked the browser session
- Whether app root `/` is expected to work: yes, but root should not be used as the only cache-busted smoke URL
- Whether `/ui/steel-guitar-rag-mock.html` works: not verified through authenticated browser after restart because login blocked the browser session
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user after completing Cloudflare Access login, or Lane 12 once an authenticated browser session is available
- Do not test these URLs: do not treat local `127.0.0.1` or unauthenticated API fallback as protected-preview browser smoke
- Known caveats: runtime is current, but protected-preview UI behavior remains unverified due to Access login.

## Exact URLs prepared

- Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1c0bbd6`
- Root: `https://app.steelguitarrag.com/?v=1c0bbd6`

## Issue-by-issue smoke status

| Area | Status | Evidence |
|---|---|---|
| Runtime current at intended HEAD | Pass | `/api/version` reports `1c0bbd6`. |
| launchd supervision | Pass | `launchctl print system/com.steelguitarrag.private-preview` reports running PID `94266`. |
| Manual screen runtime absent | Pass | `screen -ls` reports no sockets. |
| Cloudflare Tunnel running | Pass | `com.cloudflare.cloudflared` LaunchDaemon and `cloudflared` process are running; token redacted. |
| Cloudflare Access login | Blocked | In-app browser landed on Cloudflare Access login for main app URL. |
| Main app UI smoke | Not run | Blocked before app shell by Access login. |
| Prompt matrix | Not run | Blocked before Q&A by Access login. |
| Explorer smoke | Not run | Blocked at authentication stage for protected preview. |
| Root behavior | Not run | Blocked at authentication stage for protected preview. |

## Prompt results

Prompt matrix was not run through protected-preview browser because Cloudflare Access login blocked the in-app browser.

Prompts still requiring authenticated protected-preview smoke:

1. `Show me an A-flat major string grouping.`
2. `Show me an A♭ major string grouping.`
3. `Show me an Ab major string grouping.`
4. `Show me C♯ major on E9.`
5. `Show me C# major on E9.`
6. `Show me a G harmonized scale.`
7. `Show me a G natural minor harmonized scale.`
8. `Show me the F# diminished position in G.`
9. `Show me the A diminished position in G minor.`
10. `Show me a G harmonized scale on strings 5 and 8.`
11. `Show me a G major grip.`
12. `Show me a G to C move.`
13. `Give me a beginner lick in G.`
14. `Give me the full tab for a modern copyrighted song.`
15. `What are good Fender Steel King settings?`

## Checks run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -10 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `launchctl print system/com.steelguitarrag.private-preview`
- `deploy/macos/install-private-preview-launchdaemon.sh status`
  - blocked by non-interactive `sudo`
- `deploy/macos/install-private-preview-launchdaemon.sh version`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command || true`
- `screen -ls || true`
- `launchctl print system/com.cloudflare.cloudflared`
- `pgrep -fl cloudflared || true`
- `git diff --check`
- Browser navigation to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`

## Files changed

- Created `docs/handoffs/task-completions/2026-06-23-12-smoke-feedback-protected-preview-final.md`.

No implementation files were changed.

## Risks

Risk: medium.

Reasons:

- Runtime was successfully refreshed and is current at `1c0bbd6`.
- Protected-preview browser smoke remains incomplete because Cloudflare Access login blocked the browser session.
- API/local checks do not prove protected-preview UI behavior.

## Blockers

Primary blocker:

- Authenticated Cloudflare Access browser session is required before Lane 12 can complete the requested full smoke-feedback matrix.

Not a blocker:

- Runtime version is now current.
- LaunchDaemon is running.
- Cloudflare Tunnel is running.

## Human decision needed

Yes.

Decision needed:

- Complete Cloudflare Access login in the in-app browser, then rerun Lane 12 protected-preview smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`.

## Safe-to-stage files

- `docs/handoffs/task-completions/2026-06-23-12-smoke-feedback-protected-preview-final.md`

## Files that must remain unstaged

- All unrelated modified and untracked worktree files.
- Backend/UI implementation files.
- Deployment/launchd scripts and plists.
- Cloudflare Access, DNS, tunnel, auth, and secret files.
- Corpus, Chroma/vector stores, embeddings, scraper output, source-inbox, private-source files, and generated data.
- Brand/design assets and unrelated handoffs.

## Recommended next lane

Lane 12 Self-Hosted Deployment.

Recommended next prompt after Cloudflare Access login is completed:

```text
Lane 12: Continue protected-preview smoke for the smoke-feedback matrix now that Cloudflare Access login is complete. Runtime is already refreshed to 1c0bbd6. Use https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6 and write/update docs/handoffs/task-completions/2026-06-23-12-smoke-feedback-protected-preview-final.md.
```

## Commit readiness

Safe to commit as a docs-only blocked-smoke handoff.
