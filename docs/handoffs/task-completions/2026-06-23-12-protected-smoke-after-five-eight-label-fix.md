# 2026-06-23 Lane 12 Protected Smoke After Five Eight Label Fix

## Task Summary

- Requested: verify the launchd-supervised protected preview after the Lane 06 Explorer `five_eight_branch` label leak fix, confirm the main app and Explorer are ready for user smoke, and commit only this scoped handoff if clean.
- Completed: inspected repo governance and relevant handoffs, confirmed branch/runtime state, confirmed launchd supervision, confirmed no manual `screen` runtime owns `127.0.0.1:8770`, confirmed Cloudflare Tunnel is running, verified `/api/version`, ran authenticated protected-preview browser smoke on the main app, checked root behavior, verified the E9 Fretboard Explorer `5&8 branch positions` and `5-8` UI, and confirmed raw `five_eight_branch` no longer appears learner-facing.
- Intentionally not changed: app code, launchd/deployment files, Cloudflare Access policy, DNS, auth settings, tunnel token values, Cloudflare account configuration, corpus, embeddings, Chroma, scraper output, source data, private env files, and Cloudflare Tunnel configuration.

## Pass / Warn / Fail

**Pass.**

The launchd-supervised protected preview is running current runtime commit `3a07c8f`, the main app smoke passed, and the Explorer label-leak blocker is cleared.

## Current Branch And Head

- Branch: `feature/answer-api`
- Current HEAD before this handoff commit: `3a07c8f fix: hide five eight internal branch label`
- `/api/version` git SHA: `3a07c8f`
- `/api/version` branch: `feature/answer-api`
- `/api/version` auth provider: `cloudflare_access`
- `/api/version` retrieval mode: `hybrid_private_first`

## Dirty Worktree Status

Broad unrelated dirty/untracked work remains parked. No unrelated files were staged for this task.

Notable parked categories include README/docs/corpus metadata edits, source-inbox files, RAG helper scripts, visual/brand assets, and many unrelated untracked handoffs/assets.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f`
- Exact URL the user should use:
  - Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f`
  - Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; product pages loaded, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `3a07c8f`
- Version endpoint: `/api/version`
- Version endpoint result:

```json
{"git_sha": "3a07c8f", "git_branch": "feature/answer-api", "server_started_at": "2026-06-23T16:31:32.019652+00:00", "python_module": "pocketsteel.api", "retrieval_mode": "hybrid_private_first", "auth_provider": "cloudflare_access"}
```

- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as a convenience redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical protected smoke target
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f`
- Who should test this URL: the user can proceed with user smoke
- Do not test these URLs: do not use bare root for cache-busted smoke because root drops the query string
- API fallback status: not used
- Known caveats: root redirect drops query string; use the direct `/ui/...?...` URLs above for cache-busted user smoke

## Launchd Supervision Status

LaunchDaemon is loaded and running:

```text
path = /Library/LaunchDaemons/com.steelguitarrag.private-preview.plist
state = running
program = /usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
working directory = /usr/local/libexec/steel-guitar-rag
pid = 5054
runs = 24
last exit code = 1
stdout = /Users/cory/Library/Logs/steel-guitar-rag/app.out.log
stderr = /Users/cory/Library/Logs/steel-guitar-rag/app.err.log
```

Port ownership:

```text
Python PID 5054 listening on 127.0.0.1:8770
```

Manual runtime:

```text
No screen sessions found.
```

Durable log path status:

- stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
- stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- Recent logs show protected-preview traffic.
- Historical `Address already in use` stack traces remain in the tail, but the current process is running and serving.

The helper command `deploy/macos/install-private-preview-launchdaemon.sh status` attempted `sudo` and could not run non-interactively because no terminal password prompt was available. Direct `launchctl print`, `lsof`, and `/api/version` checks provided the verification needed for this smoke.

## Cloudflare Tunnel Status

Cloudflare Tunnel is running:

```text
path = /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
state = running
runs = 1
pid = 677
last exit code = (never exited)
stdout = /Library/Logs/com.cloudflare.cloudflared.out.log
stderr = /Library/Logs/com.cloudflare.cloudflared.err.log
```

No tunnel token values or token-bearing arguments were printed.

## Root URL Behavior

Tested:

```text
https://app.steelguitarrag.com/?v=3a07c8f
```

Result:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html
```

Root redirects to the canonical app path and drops the query string. Use the direct `/ui/steel-guitar-rag-mock.html?v=3a07c8f` URL for cache-busted smoke.

## Main App Browser Smoke Result

Cloudflare Access succeeded and Q&A unlocked.

| Prompt | Result | Notes |
|---|---:|---|
| Show me a G major grip. | Pass | Fretboard visible; no tab block; no `[object Object]`; no raw `five_eight_branch`. |
| Show me a 4-5-6 grip. | Pass | Fretboard visible; no tab block; no `[object Object]`; no raw `five_eight_branch`. |
| Where is G on E9? | Pass | Teacher-first G position answer; fretboard visible; no tab block; no `[object Object]`. |
| Show me a G to C move. | Pass | Direct answer, deterministic tab, and matching fretboard visible. |
| How do I use A+B pedals? | Pass | Direct answer, deterministic tab, and matching fretboard visible. |
| Show me an E-lower move. | Pass | Direct answer, deterministic tab, and matching fretboard visible. |
| Give me a beginner lick in G. | Pass | Direct prose, tab, and fretboard visible; A+B uses strings 5 and 6, not string 8. |
| Show me a G harmonized scale on strings 5 and 8. | Pass | Fretboard-first, source-free in the answer payload, warning-free, tab-free; visible text uses `5&8 branch` and never raw `five_eight_branch`. |
| Give me the full tab for a modern copyrighted song. | Pass | Clear refusal; no tab/fretboard; no `[object Object]`. |
| Tab the whole solo from Together Again. | Pass | Clear refusal; no tab/fretboard; no `[object Object]`. |
| Transcribe this YouTube recording into tab. | Pass | Clear refusal; no tab/fretboard; no `[object Object]`. |
| What are good Fender Steel King settings? | Pass | Gear answer with source links; no stale tab/fretboard; no `[object Object]`. |
| Why does my amp buzz at idle? | Pass | Gear/troubleshooting answer with source links; no stale tab/fretboard; no `[object Object]`. |

Console/page errors: none captured on the main app page.

## Explorer UI Result

Tested:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f
```

Pass:

- Explorer route loads.
- Cloudflare Access succeeded.
- Page identifies as E9 Fretboard Explorer.
- G major can be selected and is selected by default.
- `5&8 branch positions` appears as the human-facing harmony/view option.
- The Explorer page loads `pedal-steel-fretboard.js?v=five-eight-label-leak-fix-20260623`.
- Selecting `5&8 branch positions` works.
- `5-8` appears as a string-group option.
- Selecting `5-8` works.
- Four validated `5-8` rows render.
- Rendered rows show friendly `5&8 branch`.
- Raw `five_eight_branch` occurrences in visible page text: `0`.
- No `[object Object]`.
- No console errors captured.

Representative visible rows after selecting `5&8 branch positions` and `5-8`:

```text
6 A+E-raise
G on strings 5-8 at fret 6: G, B. · advanced: pedals-down pocket · grip 5-8 · A + E-raise · 5&8 branch · Partial: not all required chord tones are present

8 E-lower
G on strings 5-8 at fret 8: G, B. · advanced: E-lower color · grip 5-8 · E-lower · 5&8 branch · Partial: not all required chord tones are present

11 A+E-raise
C on strings 5-8 at fret 11: C, E. · advanced: pedals-down pocket · grip 5-8 · A + E-raise · 5&8 branch · Partial: not all required chord tones are present

13 E-lower
C on strings 5-8 at fret 13: C, E. · advanced: E-lower color · grip 5-8 · E-lower · 5&8 branch · Partial: not all required chord tones are present
```

## Tests And Checks Run

```bash
git status --short
git diff --check
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
git diff --cached --name-only
launchctl print system/com.steelguitarrag.private-preview || true
lsof -i :8770 || true
screen -ls || true
deploy/macos/install-private-preview-launchdaemon.sh status || true
deploy/macos/install-private-preview-launchdaemon.sh version || true
curl http://127.0.0.1:8770/api/version || true
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log || true
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.out.log || true
launchctl print system/com.cloudflare.cloudflared | grep -E 'state|pid|last exit|runs|path' || true
```

Browser checks:

- Authenticated protected-preview main app loaded at `/ui/steel-guitar-rag-mock.html?v=3a07c8f`.
- Root redirect checked at `/?v=3a07c8f`.
- Thirteen main-app smoke prompts submitted through the browser UI.
- Explorer loaded at `/ui/e9-fretboard-explorer.html?v=3a07c8f`.
- Explorer `5&8 branch positions` and `5-8` controls selected through the browser UI.
- Main app and Explorer console error logs checked.

## Files Changed

- `docs/handoffs/task-completions/2026-06-23-12-protected-smoke-after-five-eight-label-fix.md`

## Integration Notes

- The Explorer label leak is cleared in protected preview.
- The app remains launchd-supervised.
- Main app and Explorer user smoke can continue from the exact cache-busted URLs above.
- Root remains a convenience redirect, not the preferred cache-busted smoke URL.

## Risk Assessment

- Risk: Low.
- Reason: this was a verification and handoff-only task. No runtime files, code, auth, DNS, tunnel, corpus, Chroma, embeddings, or private data were changed.
- Rollback: no runtime rollback needed for this task; if the handoff commit needs reverting, revert the scoped docs commit.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-protected-smoke-after-five-eight-label-fix.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files shown by `git status --short`.
- Any corpus, Chroma/vector, embeddings, scraper output, source-inbox, deployment/launchd, auth/DNS/tunnel/private-data files.
- Any app code or UI files not changed by this Lane 12 task.

## Recommended Next Lane

- Lane 01 Repo Steward: refresh `docs/handoffs/task-completions/integration-status.md` with this passing Lane 12 protected-preview smoke result after user smoke or at the next coordination checkpoint.
- Lane 15 QA / Answer Eval only if user smoke finds a regression requiring broader matrix coverage.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f
```
