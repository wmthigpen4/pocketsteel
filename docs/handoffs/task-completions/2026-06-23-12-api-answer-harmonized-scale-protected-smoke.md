# 2026-06-23 Lane 12 API Answer Harmonized-Scale Protected Smoke

## Task Summary

Requested: verify the launchd-supervised protected preview after the Lane 05 API-path fix at `7da25e8`, confirm `/api/version` reports the loaded app process identity, and rerun authenticated protected-preview browser smoke for broader G harmonized-scale prompts plus Explorer smoke.

Completed:

- Inspected repo governance and the Lane 05 fix handoff.
- Confirmed branch and HEAD.
- Confirmed no staged changes before smoke.
- Confirmed LaunchDaemon supervision is active.
- Confirmed no manual `screen` runtime is serving the app.
- Confirmed `127.0.0.1:8770` is owned by the launchd-supervised Python process.
- Confirmed Cloudflare Tunnel is running.
- Confirmed local `/api/version` reports `7da25e8`.
- Did not restart the app LaunchDaemon because the loaded runtime already reported `7da25e8`.
- Ran authenticated protected-preview browser smoke at the exact cache-busted main app URL.
- Checked root redirect behavior.
- Ran authenticated protected-preview Explorer smoke at the exact cache-busted Explorer URL.

Intentionally not changed:

- No app code, backend logic, UI, auth policy, DNS, Cloudflare Access policy, Cloudflare Tunnel config, secrets, corpus, Chroma/vector stores, embeddings, scraper output, source data, or private transcript files.

## Pass / Warn / Fail

**Fail / blocked.**

The protected-preview app process now reports the intended runtime commit `7da25e8`, but the authenticated browser still returns the generic specificity fallback for the broader G major, G natural minor, and diminished-position prompt set.

The scoped 5&8 branch prompt, static grip prompts, movement/tab prompts, copyright guardrail, gear prompt, and Explorer 5&8 UI still pass.

## Branch And Starting Head

- Branch: `feature/answer-api`
- Starting HEAD: `7da25e8 fix: route harmonized scale prompts through answer API`
- Runtime commit expected: `7da25e8`
- Runtime commit reported by `/api/version`: `7da25e8`
- Relevant Lane 05 handoff: `docs/handoffs/task-completions/2026-06-23-05-fix-api-answer-harmonized-scale-routing.md`

## Repo / Runtime State

No staged changes before smoke:

```text
git diff --cached --name-only
# empty
```

Broad unrelated dirty/untracked work remains parked. The task did not stage or commit any implementation files.

`PLAN.md` and `plan.md` were requested but are not present in this checkout.

## Launchd Supervision Status

App LaunchDaemon:

```text
path = /Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
state = running
program = /usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
working directory = /usr/local/libexec/steel-guitar-rag
pid = 5054
runs = 24
stdout = /Users/cory/Library/Logs/steel-guitar-rag/app.out.log
stderr = /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
```

The LaunchDaemon environment points at:

```text
STEEL_RAG_REPO_DIR=/Users/cory/Documents/Pocket Steel
STEEL_RAG_ENV_FILE=/Users/cory/.steel-rag/env/private-preview.env
STEEL_RAG_HOST=127.0.0.1
STEEL_RAG_PORT=8770
```

`deploy/macos/install-private-preview-launchdaemon.sh status` could not complete non-interactively because it invokes `sudo` and no terminal password prompt was available.

Manual screen runtime:

```text
No screen sessions found.
```

Port ownership:

```text
Python PID 5054 listening on 127.0.0.1:8770
```

Cloudflare Tunnel:

```text
path = /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
state = running
pid = 677
runs = 1
last exit code = (never exited)
stdout = /Library/Logs/com.cloudflare.cloudflared.out.log
stderr = /Library/Logs/com.cloudflare.cloudflared.err.log
```

No tunnel token values or token-bearing arguments were printed.

## Version Endpoint

Local `/api/version`:

```json
{"git_sha": "7da25e8", "git_branch": "feature/answer-api", "server_started_at": "2026-06-23T17:07:29.716275+00:00", "python_module": "pocketsteel.api", "retrieval_mode": "hybrid_private_first", "auth_provider": "cloudflare_access"}
```

`deploy/macos/install-private-preview-launchdaemon.sh version` also returned `7da25e8`.

Protected-browser direct navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser extension with `net::ERR_BLOCKED_BY_CLIENT`, and page-scope `fetch`/`XMLHttpRequest` were unavailable in this Browser runtime. Browser smoke still ran through the authenticated protected-preview UI; API fallback was not used.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=7da25e8`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=7da25e8`
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=7da25e8`
- Root URL tested: `https://app.steelguitarrag.com/?v=7da25e8`
- Exact URL the user should use: blocked for broader harmonized-scale user smoke until Lane 05 resolves the protected-browser fallback behavior
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; product pages loaded, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `7da25e8`
- Version endpoint: `/api/version`
- Version endpoint result: local launchd endpoint reported `7da25e8`
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as a convenience redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical protected smoke target
- API fallback status: not used
- Known caveat: root redirect drops the query string; use direct `/ui/...?...` URLs for exact cache-busted smoke

## Root URL Behavior

Tested:

```text
https://app.steelguitarrag.com/?v=7da25e8
```

Final browser URL:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html
```

Root loads the app shell after redirect but drops the query string.

## Main App Browser Smoke Result

Cloudflare Access succeeded and the Q&A input unlocked.

| # | Prompt | Result | Actual behavior |
|---:|---|---:|---|
| 1 | Show me a G harmonized scale. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 2 | Show me G major harmonized scale on E9. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 3 | Show me a G major harmonized scale. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 4 | Show me a G harmonized scale on E9. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 5 | Show me a G natural minor harmonized scale. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 6 | Show me G natural minor harmonized scale on E9. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 7 | Show me the F# diminished position in G. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 8 | Show me the A diminished position in G minor. | Fail | Returned generic specificity fallback. No fretboard. No tab. No source cards. |
| 9 | Show me a G harmonized scale on strings 5 and 8. | Pass | Returned deterministic 5&8 branch answer. Fretboard visible. No tab. Source-free/warning-free. Corrected 13th-fret E-lower C/E branch present. 11th-fret C/E route shown as A+F, not E-lower. |
| 10 | Show me a G major grip. | Pass | Static grip answer remained fretboard-first. Fretboard visible. No visible tab block. |
| 11 | Show me a 4-5-6 grip. | Pass | Static grip answer remained fretboard-first. Fretboard visible. No visible tab block. |
| 12 | Show me a G to C move. | Pass | Movement answer returned deterministic tab plus matching fretboard. |
| 13 | Give me a beginner lick in G. | Pass | Beginner lick returned direct prose, deterministic tab, and matching fretboard. |
| 14 | Give me the full tab for a modern copyrighted song. | Pass | Copyright/full-song request refused/redirected safely. No tab. No fretboard. |
| 15 | What are good Fender Steel King settings? | Pass | Gear answer rendered normally with source cards. No stale tab/fretboard payload. |

Main app console/page errors: none captured.

Raw object/internal label checks:

- `[object Object]`: not observed.
- Raw `five_eight_branch`: not observed.

## Expected Vs Actual

Expected for prompts 1-4:

- Deterministic G major harmonized-scale guidance.
- Fretboard-first response.
- No generic fallback.
- No tab by default.
- Source-free and warning-free.

Actual for prompts 1-4:

- Generic specificity fallback.
- No fretboard.
- No tab.
- No source cards.

Expected for prompts 5-6:

- Deterministic G natural minor harmonized-scale guidance.
- No generic fallback.

Actual for prompts 5-6:

- Generic specificity fallback.

Expected for prompts 7-8:

- Diminished-position guidance without false full m7b5 claims.

Actual for prompts 7-8:

- Generic specificity fallback.

Expected for prompt 9:

- Preserve the 5&8 branch answer, show both valid branch families, include the corrected fret 13 E-lower C/E branch, avoid 11th-fret E-lower as the C/E branch, no tab by default.

Actual for prompt 9:

- Passed. The answer includes both branch families and the corrected 13th-fret E-lower C/E route. The visible row at fret 11 is A+F/A+E-raise, not E-lower.

## Explorer Browser Smoke Result

Tested:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=7da25e8
```

Result: pass.

- Page loads through Cloudflare Access.
- Page identifies as E9 Fretboard Explorer.
- `5&8 branch positions` appears as the human-facing view.
- Selecting `5&8 branch positions` works.
- `5-8` appears as a string-group option after selecting the 5&8 view.
- Selecting `5-8` works.
- Relevant rows render for frets 6, 8, 11, and 13.
- Rows/cards are usable.
- Raw `five_eight_branch` visible text count: `0`.
- No broken 5-8 label rendering observed.
- No `[object Object]`.
- No Explorer console errors captured.

Representative Explorer excerpt:

```text
6 A+E-raise
G on strings 5-8 at fret 6: G, B. · advanced: pedals-down pocket · grip 5-8 · A + E-raise · 5&8 branch

8 E-lower
G on strings 5-8 at fret 8: G, B. · advanced: E-lower color · grip 5-8 · E-lower · 5&8 branch

11 A+E-raise
C on strings 5-8 at fret 11: C, E. · advanced: pedals-down pocket · grip 5-8 · A + E-raise · 5&8 branch

13 E-lower
C on strings 5-8 at fret 13: C, E. · advanced: E-lower color · grip 5-8 · E-lower · 5&8 branch
```

## Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -8 --oneline
git diff --name-only
git diff --cached --name-only
git diff --check
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
curl -sS http://127.0.0.1:8770/api/version || true
lsof -nP -iTCP:8770 -sTCP:LISTEN || true
screen -ls || true
launchctl print system/com.cloudflare.cloudflared 2>/dev/null | grep -E 'state|pid|last exit|runs|path' || true
```

Browser checks:

- Main app loaded at `/ui/steel-guitar-rag-mock.html?v=7da25e8`.
- Root redirect checked at `/?v=7da25e8`.
- Fifteen main-app smoke prompts submitted through the authenticated browser UI.
- Explorer loaded at `/ui/e9-fretboard-explorer.html?v=7da25e8`.
- Explorer `5&8 branch positions` and `5-8` controls selected through the authenticated browser UI.
- Main app and Explorer console error logs checked.

Skipped:

- Broad automated test suite. This Lane 12 task was protected-preview runtime/browser verification after Lane 05 had already run focused tests.
- App LaunchDaemon restart. Runtime already reported the intended process identity `7da25e8`, so a restart was not needed.

## Files Changed

- `docs/handoffs/task-completions/2026-06-23-12-api-answer-harmonized-scale-protected-smoke.md`

## Risks

- Risk: medium.
- Reason: the runtime/version mismatch is resolved, but protected-preview browser behavior still contradicts the expected broader harmonized-scale API-path fix for prompts 1-8.
- User smoke should not proceed for the broader G harmonized-scale slice until Lane 05 diagnoses why the authenticated browser path still falls back generically.
- Existing 5&8 branch and Explorer behavior remain usable.

## Blockers

Blocking issue:

- Protected-preview browser smoke fails the broader G major, G natural minor, and diminished-position routing prompts at runtime commit `7da25e8`.

Owning lane:

- Lane 05 Backend / RAG Integration.

Suggested Lane 05 prompt:

```text
Lane 05: Diagnose why authenticated protected-preview browser smoke at runtime commit 7da25e8 still returns the generic specificity fallback for broader harmonized-scale prompts even though /api/version reports the loaded app process at 7da25e8. Use docs/handoffs/task-completions/2026-06-23-12-api-answer-harmonized-scale-protected-smoke.md. Compare the browser UI request path and payload to the tested production-auth /api/answer regression path for: "Show me a G harmonized scale.", "Show me G major harmonized scale on E9.", "Show me a G natural minor harmonized scale.", "Show me the F# diminished position in G.", and "Show me the A diminished position in G minor." Do not touch corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or private source data.
```

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-api-answer-harmonized-scale-protected-smoke.md`

## Files That Must Remain Unstaged

- Any unrelated dirty or untracked file shown by `git status --short`.
- Any implementation/runtime/backend/test/UI/source/corpus/deploy/auth/DNS/private/generated/design files not explicitly scoped to this Lane 12 handoff.
- `docs/handoffs/task-completions/integration-status.md` unless Lane 01 explicitly refreshes it.

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

## Commit Readiness

Safe to commit as a scoped docs-only protected-smoke handoff.
