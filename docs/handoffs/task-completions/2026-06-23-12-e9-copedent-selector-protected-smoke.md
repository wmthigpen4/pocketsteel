# Lane 12 - E9 Copedent Selector Protected Smoke

## Task Summary

Requested Lane 12 protected-preview browser smoke for the E9 copedent selector/chart after Lane 15 approved the feature. The intended runtime was refreshed to current `feature/answer-api` HEAD and verified locally through `/api/version`, but authenticated protected-preview browser smoke could not complete because the in-app browser landed on Cloudflare Access login for all protected URLs.

This handoff intentionally does not modify backend code, UI code, deployment config, DNS, auth policy, corpus data, Chroma/vector stores, embeddings, scraping outputs, private source data, or unrelated dirty files.

## Smoke Target

- Target type: protected-preview
- Result type: blocked browser smoke, with local fallback evidence clearly labeled
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ecec173`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ecec173`
- Exact URL the user should use: blocked pending authenticated protected-preview retest
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: failed/blocked in the automation browser; page showed "Log in to Steel Guitar RAG Private Preview"
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `ecec173`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=ecec173`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`, `server_started_at=2026-06-24T20:11:56.293349+00:00`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: protected root redirected to Cloudflare Access login in the automation browser
- Whether app root `/` is expected to work: yes, after Cloudflare Access login
- Whether `/ui/steel-guitar-rag-mock.html` works: protected app URL redirected to Cloudflare Access login in the automation browser
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, after Cloudflare Access login
- Who should test this URL: the user after completing Cloudflare Access login, then Lane 12 can rerun
- Do not test these URLs: do not treat `http://127.0.0.1:8770` as protected-preview proof
- Known caveats: local fallback found a visible raw `APP-DEFAULT` label in the copedent chart; route UI cleanup to Lane 06

## Runtime State

- Branch: `feature/answer-api`
- HEAD: `ecec173 feat: add E9 copedent selector and chart`
- LaunchDaemon: `system/com.steelguitarrag.private-preview` running
- LaunchDaemon path: `/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist`
- Program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- Listener: Python process on `127.0.0.1:8770`
- Listener PID: `52474`
- PID start time: `Wed Jun 24 15:11:55 2026`
- Durable logs:
  - stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- `screen -ls`: no screen sockets

## Protected Preview Browser Result

| URL | Result |
| --- | --- |
| `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ecec173` | Redirected to Cloudflare Access login. Explorer was not reachable in the automation browser. |
| `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ecec173` | Redirected to Cloudflare Access login. Main app prompt checks were not run as protected browser smoke. |
| `https://app.steelguitarrag.com/?v=ecec173` | Redirected to Cloudflare Access login with redirect target preserved in Access metadata. |

API fallback was not used as browser smoke.

## Local Fallback Evidence

Local fallback URL: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=ecec173`

This local evidence does not prove protected-preview behavior, but it does show the current runtime/static files contain a UI issue that would likely be visible after authentication.

| Check | Local fallback result |
| --- | --- |
| Explorer loads | Pass |
| Emmons E9 option visible | Pass |
| Day E9 option visible | Pass |
| My Copedent (E9) visible but disabled | Pass |
| Coming soon in Backstage copy appears | Pass |
| C6 not active | Pass; no enabled C6 option found |
| Visual copedent chart visible | Pass by rendered text/table evidence |
| Chart shows strings 1-10 | Pass |
| Chart shows control changes | Pass |
| Pedal and Lever Impact Preview appears | Pass |
| Right-knee lever controls appear | Pass; RKR/RKL and D-lower/G-lower content visible |
| No `[object Object]` | Pass |
| No raw labels | Fail; `APP-DEFAULT` is visible in the copedent chart |
| Selected Explorer groups still render localized clusters | Partial local evidence only; full protected interaction was not run |
| Console/page errors | No local Explorer warnings/errors captured |

## Prompt Spot Checks

The requested prompt spot checks were not run in protected browser smoke because Cloudflare Access login blocked the automation browser:

- `What does a Franklin pedal do?`
- `Show me a G major grip.`
- `Show me a G to C move.`
- `Give me the full tab for a modern copyrighted song.`

No API fallback result is reported for these prompts.

## Files Changed

- Created: `docs/handoffs/task-completions/2026-06-23-12-e9-copedent-selector-protected-smoke.md`

No implementation files were changed.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -10 --oneline`
- `launchctl print system/com.steelguitarrag.private-preview`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command || true`
- `screen -ls || true`
- In-app browser protected URL checks for Explorer, main app, and root
- In-app browser local fallback check for Explorer only
- `git diff --check` - passed

Skipped:

- Protected prompt spot checks, because the automation browser was blocked at Cloudflare Access login.
- Broad test suites, because this Lane 12 task was deployment/protected-preview smoke and did not modify implementation files.

## Risk Assessment

Risk: medium.

Runtime is correctly refreshed to `ecec173`, but user-smoke readiness is blocked by two independent issues:

1. Protected-preview browser smoke did not authenticate in the automation browser.
2. Local fallback shows visible raw `APP-DEFAULT` copy in the copedent chart, violating the requested smoke criteria.

Rollback note: no product/runtime code was changed. The current LaunchDaemon process is already on `ecec173`; revert/restart is not required for this handoff.

## Human Decision Needed

Yes.

Exact decision needed:

- Complete Cloudflare Access login in the automation browser or provide an approved authenticated browser workflow so Lane 12 can rerun protected browser smoke.
- Route the visible `APP-DEFAULT` raw label to Lane 06 for UI cleanup before clearing user smoke.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-e9-copedent-selector-protected-smoke.md`

## Files That Must Not Be Staged

- Any dirty or untracked implementation files outside this handoff
- `docs/handoffs/task-completions/integration-status.md`
- Corpus files, private corpus files, Chroma/vector stores, embeddings, scraper output, source-inbox files, credentials, logs, DNS/auth/deployment config, and generated/private artifacts

## Recommended Next Lane

- Lane 06 UX/UI Design: remove or replace the visible raw `APP-DEFAULT` label in the Explorer copedent chart.
- Lane 12 Self-Hosted Deployment: rerun protected-preview browser smoke after Cloudflare Access authentication is available.

## Commit Readiness

Safe to commit for this docs-only handoff only.

## Suggested Next Step

Lane 06 prompt:

```text
Lane 06 UX/UI Design: The E9 copedent selector/chart smoke on current HEAD ecec173 found visible raw APP-DEFAULT copy in the Explorer copedent chart. Replace it with learner-facing copy or hide it from the primary UI, add/update focused Explorer UI tests, and preserve unrelated dirty work.
```

Then rerun Lane 12 protected-preview smoke at:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ecec173
```
