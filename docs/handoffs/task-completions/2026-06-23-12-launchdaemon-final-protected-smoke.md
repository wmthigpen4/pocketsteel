# 2026-06-23 Lane 12 LaunchDaemon Final Protected Smoke

## Task Summary

- Requested: verify the Mac mini LaunchDaemon-safe-path activation, confirm launchd owns the protected-preview app runtime, run protected-preview browser smoke for the main app and E9 Fretboard Explorer, and decide whether user smoke can resume.
- Completed: verified repo/runtime state, confirmed the LaunchDaemon now uses the safe wrapper path, stopped the stale manual `screen` runtime and orphaned Python process only after logs showed port contention, confirmed launchd owns `127.0.0.1:8770`, verified `/api/version`, verified Cloudflare Tunnel is running, ran authenticated browser smoke through Cloudflare Access, checked root behavior, checked the Explorer route, and recorded a UI blocker.
- Intentionally not changed: app code, UI code, Cloudflare Access policy, DNS, auth settings, tunnel token values, Cloudflare account configuration, corpus, embeddings, Chroma, scraper output, source data, private env files, and Cloudflare Tunnel configuration.

## Pass / Warn / Fail

**Warn / blocked for user smoke by Explorer UI label leak.**

Runtime supervision passed: the app is now launchd-supervised and the manual `screen` runtime is gone.

Main app protected-preview browser smoke passed the requested runtime and answer-shape checks. The E9 Fretboard Explorer route loads and its `5&8 branch positions` / `5-8` controls work, but raw internal `five_eight_branch` still appears in learner-facing row-card text. That violates the prompt's Explorer UI criterion and should go back to Lane 06.

## Current Branch And Head

- Branch: `feature/answer-api`
- Current HEAD: `18587d9 docs: reconcile latest parallel lane handoffs`
- Included commits verified:
  - `0d10843 fix: label g five eight fretboard branch`
  - `c08cc95 feat: add deterministic G harmonized scale rules`
  - `4c40cef fix: run launchdaemon wrapper from safe path`
  - `daa0adc docs: record launchdaemon final smoke`

## Dirty Worktree Status

Broad unrelated dirty/untracked work remains parked. No unrelated files were staged during this task.

Protected/parked categories still present include corpus/source metadata, source-inbox files, design/brand assets, generated handoff assets, private/corpus-adjacent scripts, and unrelated docs/reports.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=18587d9`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=18587d9`
- Exact URL the user should use: blocked; do not resume broad user smoke until Explorer UI label leak is fixed
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; authenticated product pages loaded, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `18587d9`
- Version endpoint: `/api/version`
- Version endpoint result:

```json
{"git_sha":"18587d9","git_branch":"feature/answer-api","server_started_at":"2026-06-23T16:14:35.257254+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as a convenience redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical protected smoke target
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=18587d9`
- Who should test this URL: Lane 06 should fix the Explorer label leak before user smoke resumes
- API fallback status: not used as browser smoke
- Known caveats: root redirect drops the query string; use the direct `/ui/...?...` URL for cache-busted tests

## Launchd Supervision Status

LaunchDaemon is loaded and running:

```text
state = running
program = /usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
working directory = /usr/local/libexec/steel-guitar-rag
runs = 24
pid = 5054
last exit code = 1
```

Port ownership:

```text
Python PID 5054 listening on 127.0.0.1:8770
```

Manual runtime:

```text
No screen sessions remain.
```

Activation sequence:

- The LaunchDaemon safe wrapper path was already installed by the operator before this task.
- Logs showed the old failure had advanced from `Operation not permitted` to `Address already in use`, meaning launchd could execute the wrapper and reach Python.
- The stale `steel-rag-private-preview` screen was stopped.
- The orphaned stale Python process was terminated with `SIGTERM`.
- launchd respawned the app and now owns port `8770`.

Durable log path status:

- stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
- stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- Recent logs show normal GET/POST traffic after activation.
- The old `Address already in use` stack traces remain in the log history but stopped after launchd acquired the port.
- No new `Operation not permitted` failure appeared in the final log tail.

## Cloudflare Tunnel Status

Cloudflare Tunnel is running:

```text
path = /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
state = running
runs = 1
pid = 677
last exit code = (never exited)
```

No tunnel token values or token-bearing arguments were printed.

## Root URL Behavior

Tested:

```text
https://app.steelguitarrag.com/?v=18587d9
```

Result:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html
```

Root redirects to the canonical app path and drops the query string. Use the direct `/ui/steel-guitar-rag-mock.html?v=18587d9` URL for cache-busted smoke.

## Main App Browser Smoke Result

Cloudflare Access succeeded and Q&A unlocked.

| Prompt | Result | Notes |
|---|---:|---|
| Show me a G major grip. | Pass | Fretboard visible; no meaningful tab block; no sources returned; no `[object Object]`. |
| Show me a 4-5-6 grip. | Pass | Fretboard visible; no meaningful tab block; no sources returned; no `[object Object]`. |
| Where is G on E9? | Pass with note | Direct answer appears with open/A+F/A+B families; no tab; no `[object Object]`. Browser extraction did not flag the fretboard for this broad position answer. |
| Show me a G to C move. | Pass | Direct answer, deterministic tab, and matching fretboard visible. |
| How do I use A+B pedals? | Pass | Direct answer, deterministic tab, and matching fretboard visible. |
| Show me an E-lower move. | Pass | Direct answer, deterministic tab, and matching fretboard visible. |
| Give me a beginner lick in G. | Pass | Direct prose, tab, and fretboard visible; tab/prose use strings 5 and 6 for A+B, not string 8. |
| Show me a G harmonized scale on strings 5 and 8. | Pass with note | Direct static 5&8 branch answer; source-free, warning-free, tab-free. Browser extraction did not flag a fretboard despite answer text saying this uses a diagram, so Lane 15/Lane 06 may want a visual confirmation if this exact prompt matters before user smoke. |
| Give me the full tab for a modern copyrighted song. | Pass | Clear refusal; no tab/fretboard; no sources returned; no `[object Object]`. |
| Tab the whole solo from Together Again. | Pass | Clear refusal; no tab/fretboard; no sources returned; no `[object Object]`. |
| Transcribe this YouTube recording into tab. | Pass | Clear refusal; no tab/fretboard; no sources returned; no `[object Object]`. |
| What are good Fender Steel King settings? | Pass | Gear answer rendered normally with source links; no stale tab/fretboard; no `[object Object]`. |
| Why does my amp buzz at idle? | Pass | Gear/troubleshooting answer rendered normally with source links; no stale tab/fretboard; no `[object Object]`. |

## Explorer UI Result

Tested:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=18587d9
```

Pass:

- Explorer route loads.
- G major is selected by default.
- `5&8 branch positions` appears as a human-facing harmony/view option.
- Selecting `5&8 branch positions` works.
- `5-8` appears as a string-group option.
- Selecting `5-8` works.
- Four validated `5-8` rows render.
- All row buttons after selecting `5-8` are for strings `5-8`.
- Friendly `5&8 branch` appears in detail/technical copy.
- No `[object Object]`.
- No console errors captured.

Fail:

- Raw `five_eight_branch` appears in visible row card text for all four rendered branch rows, for example:

```text
G on strings 5-8 at fret 6: G, B. · advanced: pedals-down pocket · grip 5-8 · A + E-raise · five_eight_branch · Partial: not all required chord tones are present
```

This is learner-facing UI text, not only hidden payload metadata. It violates the prompt requirement that raw `five_eight_branch` not appear in learner-facing UI.

## Console / Page Errors

- Main app: no relevant console/page errors observed during smoke.
- Explorer: no console errors captured.
- `[object Object]`: not observed in main app or Explorer checks.

## Tests And Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
git diff --cached --name-only
git merge-base --is-ancestor 0d10843 HEAD
git merge-base --is-ancestor c08cc95 HEAD
launchctl print system/com.steelguitarrag.private-preview || true
lsof -nP -iTCP:8770 -sTCP:LISTEN || true
screen -ls || true
deploy/macos/install-private-preview-launchdaemon.sh status || true
deploy/macos/install-private-preview-launchdaemon.sh version || true
curl -sS --max-time 5 http://127.0.0.1:8770/api/version || true
tail -n 100 /Users/cory/Library/Logs/steel-guitar-rag/app.err.log || true
tail -n 80 /Users/cory/Library/Logs/steel-guitar-rag/app.out.log || true
launchctl print system/com.cloudflare.cloudflared 2>/dev/null | grep -E 'state|pid|last exit|runs|path' || true
git diff --check
```

Browser checks:

- Authenticated protected-preview main app loaded at `/ui/steel-guitar-rag-mock.html?v=18587d9`.
- Root redirect checked at `/?v=18587d9`.
- Thirteen main-app smoke prompts submitted through the browser UI.
- Explorer loaded at `/ui/e9-fretboard-explorer.html?v=18587d9`.
- Explorer `5&8 branch positions` and `5-8` controls selected through the browser UI.
- Browser console errors checked through the browser tooling.

Skipped:

- No broad pytest; this was deployment/protected-preview smoke only.
- No API fallback was used as a substitute for browser smoke.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-final-protected-smoke.md`

Modified:

- None.

Deleted:

- None.

Generated artifacts:

- None.

## Risk Assessment

Risk level: **Medium**.

Reasons:

- Runtime supervision is now materially better: launchd owns the app process and manual screen is gone.
- User-smoke readiness is blocked by a learner-facing Explorer UI metadata leak.
- Root redirect drops cache-bust query strings, so direct `/ui/...?...` URLs remain safer for exact smoke.
- Historical `Address already in use` traces remain in `app.err.log`; current service is healthy after port handoff.

Rollback notes:

- To roll back the supervised app runtime, unload the app LaunchDaemon:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

- If necessary, manually start the app using the documented rollback command in `docs/mac-mini-private-preview-launchd.md`.

## Human Decision Needed

No for the blocker routing.

The next step is clear: Lane 06 should remove visible raw `five_eight_branch` from Explorer row cards/details while preserving internal data values.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-launchdaemon-final-protected-smoke.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files.
- App code, UI code, tests, corpus/source files, source-inbox files, Chroma/vector stores, embeddings, scraper output, private corpus, private env files, tunnel tokens, rendered plists, Cloudflare credentials, DNS/auth config, `.wrangler/`, raw design assets, generated media, and unrelated handoffs.

## Recommended Next Lane

Lane 06 UX/UI Design.

## Commit Readiness

Safe to commit for this handoff only.

## Suggested Next Step

```text
Lane 06: Fix the E9 Fretboard Explorer learner-facing row/detail labels so raw `five_eight_branch` never appears in visible UI. Preserve internal payload/data values, keep `5&8 branch positions` and `5-8` selection behavior, run focused Explorer/frontend tests, then hand back to Lane 12 for protected-preview smoke at the current launchd-supervised runtime.
```
