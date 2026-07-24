# 2026-06-23 Lane 12 Broader G Harmonized-Scale Protected Smoke

## Task Summary

- Requested: verify the launchd-supervised protected preview from the committed broader G harmonized-scale routing slice, then run protected-preview browser smoke for the main app and E9 Fretboard Explorer.
- Completed: inspected repo governance and relevant handoffs, confirmed Lane 01 committed the broader routing slice as `239f74a`, confirmed branch/runtime state, confirmed launchd supervision, confirmed no manual `screen` runtime owns `127.0.0.1:8770`, confirmed Cloudflare Tunnel is running, verified `/api/version`, ran authenticated protected-preview browser smoke on the main app, checked root behavior, and ran Explorer 5&8 smoke.
- Intentionally not changed: app code, launchd/deployment files, Cloudflare Access policy, DNS, auth settings, tunnel token values, Cloudflare account configuration, corpus, embeddings, Chroma, scraper output, source data, private env files, and Cloudflare Tunnel configuration.

## Pass / Warn / Fail

**Fail / blocked for broader G harmonized-scale user smoke.**

The launchd-supervised runtime reports commit `239f74a`, but the protected-preview browser still returns the generic "I need a more specific steel-guitar question" fallback for the new broader G major, G natural minor, and diminished-position prompts.

The existing scoped 5&8 branch prompt still passes, movement/copyright/gear regressions pass, and the Explorer 5&8 UI passes.

## Branch And Starting Head

- Branch: `feature/answer-api`
- Starting HEAD: `239f74a fix: route G harmonized scale prompts deterministically`
- Lane 01 commit handoff reviewed: `docs/handoffs/task-completions/2026-06-23-01-broader-g-harmonized-scale-routing-commit.md`
- Intended runtime commit: `239f74a`
- Runtime commit reported by `/api/version`: `239f74a`

## Dirty Worktree Status

Broad unrelated dirty/untracked work remains parked. No unrelated files were staged for this task.

`git diff --name-only` showed parked files only in unrelated docs/corpus metadata/RAG helper/source-inbox/brand asset paths:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`

No dirty implementation files from the committed broader routing slice were present before smoke.

## Runtime And Deployment Status

LaunchDaemon is loaded and running:

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

Port ownership:

```text
Python PID 5054 listening on 127.0.0.1:8770
```

Manual runtime:

```text
No screen sessions found.
```

Cloudflare Tunnel:

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

The helper command `deploy/macos/install-private-preview-launchdaemon.sh status` attempted `sudo` and could not run non-interactively because no terminal password prompt was available. Direct `launchctl print`, `lsof`, and `/api/version` checks provided the needed runtime verification.

No LaunchDaemon restart was performed because `/api/version` already reported the intended commit `239f74a`.

## Version Endpoint

Local `/api/version` result:

```json
{"git_sha": "239f74a", "git_branch": "feature/answer-api", "server_started_at": "2026-06-23T16:49:03.125841+00:00", "python_module": "steel_guitar_rag.api", "retrieval_mode": "hybrid_private_first", "auth_provider": "cloudflare_access"}
```

`deploy/macos/install-private-preview-launchdaemon.sh version` also returned `239f74a`.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=239f74a`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=239f74a`
- Exact URL the user should use: blocked for broader G harmonized-scale user smoke until Lane 05 fixes the protected-preview fallback regression
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; product pages loaded, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `239f74a`
- Version endpoint: `/api/version`
- Version endpoint result: `239f74a` on `feature/answer-api`
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as a convenience redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical protected smoke target
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=239f74a`
- API fallback status: not used; all reported behavior below is from authenticated protected-preview browser smoke
- Known caveats: root redirect drops the query string; use direct `/ui/...?...` URLs for exact cache-busted smoke

## Root URL Behavior

Tested:

```text
https://app.steelguitarrag.com/?v=239f74a
```

Result:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html
```

Root redirects to the canonical app path and drops the query string.

## Main App Browser Smoke Result

Cloudflare Access succeeded and Q&A unlocked.

| Prompt | Result | Actual behavior |
|---|---:|---|
| Show me a G harmonized scale. | Fail | Returned generic "I need a more specific steel-guitar question" fallback. No fretboard. No tab. No source links. |
| Show me G major harmonized scale on E9. | Fail | Returned generic fallback. No fretboard. No tab. No source links. |
| Show me a G natural minor harmonized scale. | Fail | Returned generic fallback. No fretboard. No tab. No source links. |
| Show me the F# diminished position in G. | Fail | Returned generic fallback. No fretboard. No tab. No source links. |
| Show me the A diminished position in G minor. | Fail | Returned generic fallback. No fretboard. No tab. No source links. |
| Show me a G harmonized scale on strings 5 and 8. | Pass | Fretboard-first 5&8 branch answer. No tab. No source links. No warnings. Corrected fret 13 E-lower C/E branch present. Incorrect 11th-fret E-lower C/E branch not present. |
| Show me a G major grip. | Pass | Fretboard-first static grip answer. No visible tab block. No source links in this smoke. |
| Show me a G to C move. | Pass | Direct movement answer with deterministic tab and matching fretboard. |
| Give me the full tab for a modern copyrighted song. | Pass | Clear copyright refusal/redirect. No tab. No fretboard. No source links. |
| What are good Fender Steel King settings? | Pass | Gear answer with source links. No stale tab or fretboard payload. |

Main app console/page errors: none captured.

Raw object/internal-label checks:

- `[object Object]`: not observed.
- Raw `five_eight_branch`: not observed.

## Expected Vs Actual

Expected for broader harmonized-scale routing:

- Broad G major harmonized-scale prompts should no longer fall back generically.
- G natural minor harmonized-scale prompt should no longer fall back generically.
- Diminished-position prompts should route deterministically.
- Static harmonized-scale answers should be fretboard-first, source-free, warning-free, and tab-free.

Actual protected-preview behavior:

- Broader G major prompt variants still fell back generically.
- G natural minor prompt still fell back generically.
- F# diminished and A diminished prompts still fell back generically.
- The already-existing exact 5&8 branch prompt remained correct.

This appears to be a backend answer-routing/runtime behavior defect in the authenticated `/api/answer` path despite `/api/version` reporting `239f74a`.

## Explorer Browser Smoke Result

Tested:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=239f74a
```

Pass:

- Explorer route loads through Cloudflare Access.
- Page identifies as E9 Fretboard Explorer.
- `5&8 branch positions` appears as the human-facing harmony/view option.
- Selecting `5&8 branch positions` works.
- `5-8` appears as a string-group option after selecting the 5&8 view.
- Selecting `5-8` works.
- Four validated `5-8` rows render.
- Rows show friendly `5&8 branch`.
- Raw `five_eight_branch` visible text occurrences: `0`.
- No broken 5-8 label rendering observed.
- No `[object Object]`.
- No Explorer console errors captured.

Representative rows:

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

## Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -5 --oneline
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

- Main app loaded at `/ui/steel-guitar-rag-mock.html?v=239f74a`.
- Root redirect checked at `/?v=239f74a`.
- Ten main-app smoke prompts submitted through the authenticated browser UI.
- Explorer loaded at `/ui/e9-fretboard-explorer.html?v=239f74a`.
- Explorer `5&8 branch positions` and `5-8` controls selected through the authenticated browser UI.
- Main app and Explorer console error logs checked.

## Files Changed

- `docs/handoffs/task-completions/2026-06-23-12-broader-g-harmonized-scale-protected-smoke.md`

## Risks

- Risk: medium.
- Reason: `/api/version` reports the intended commit, but protected-preview browser behavior contradicts Lane 15 local/API QA for the broader routing prompts.
- User smoke should not proceed for broader G harmonized-scale routing until Lane 05 diagnoses why the authenticated `/api/answer` path still returns the generic fallback.
- The existing scoped 5&8 branch prompt and Explorer remain usable.

## Blockers

Blocking issue:

- Protected-preview browser smoke fails the broader G harmonized-scale routing slice at runtime commit `239f74a`.

Owning lane:

- Lane 05 Backend / RAG Integration.

Suggested Lane 05 prompt:

```text
Lane 05: Diagnose why protected-preview /api/answer at runtime commit 239f74a returns the generic fallback for broader G harmonized-scale prompts even though local QA passed. Use docs/handoffs/task-completions/2026-06-23-12-broader-g-harmonized-scale-protected-smoke.md. Compare the authenticated /api/answer path to the in-process helper path for: "Show me a G harmonized scale.", "Show me G major harmonized scale on E9.", "Show me a G natural minor harmonized scale.", "Show me the F# diminished position in G.", and "Show me the A diminished position in G minor." Do not touch corpus, Chroma, embeddings, scraping, auth, DNS, or deployment.
```

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-broader-g-harmonized-scale-protected-smoke.md`

## Files That Must Remain Unstaged

- Any unrelated dirty or untracked file shown by `git status --short`.
- Any runtime/backend/test/UI/source/corpus/deploy/auth/DNS/private/generated/design files not explicitly scoped to this Lane 12 handoff.
- `docs/handoffs/task-completions/integration-status.md` unless Lane 01 explicitly refreshes it.

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

## Commit Readiness

Safe to commit as a scoped docs-only handoff.
