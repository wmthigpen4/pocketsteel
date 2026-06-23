# Lane 12 post-restart harmonized-scale protected-preview smoke

## Task summary

Requested Lane 12 protected-preview browser smoke after the privileged Mac mini LaunchDaemon restart succeeded.

Completed:

- Verified the launchd-supervised local process on `127.0.0.1:8770`.
- Verified local `/api/version` reports runtime commit `ddd7953`.
- Ran authenticated Cloudflare Access browser smoke against the protected preview app.
- Ran root URL and Explorer route checks.
- Verified the harmonized-scale prompts no longer show the generic fallback in the browser runtime.

Intentionally not changed:

- No backend/UI files changed.
- No restart was performed; the process was already fresh and matched `ddd7953`.
- No DNS, Cloudflare Access, tunnel, auth, secrets, corpus, Chroma, embeddings, scraping, or private-source files were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app shell loaded directly in authenticated session.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `ddd7953`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=ddd7953`, `git_branch=feature/answer-api`, `server_started_at=2026-06-23T18:18:17.988106+00:00`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable.
- Whether app root `/` works: yes, root redirects to `/ui/steel-guitar-rag-mock.html`.
- Whether app root `/` is expected to work: yes as a convenience entry that redirects to the canonical app shell.
- Whether `/ui/steel-guitar-rag-mock.html` works: yes.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; it remains the canonical protected-preview app URL.
- Who should test this URL: the user.
- Do not test these URLs: unauthenticated API fallback URLs as proof of browser behavior.
- Known caveats: root redirect dropped the query string and ended at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`; use the direct `/ui/...?...` URL when a cache-busted app-shell URL is required.

## Runtime and supervision evidence

- Branch: `feature/answer-api`
- HEAD tested: `ddd7953`
- Local `/api/version`: `ddd7953`
- Listener: Python on `127.0.0.1:8770`
- Listener PID: `72903`
- PID start time: `Tue Jun 23 13:18:17 2026`
- API `server_started_at`: `2026-06-23T18:18:17.988106+00:00`
- launchd service: `system/com.steelguitarrag.private-preview`
- launchd state: running
- launchd program: `deploy/macos/run-private-preview-app.sh`
- launchd stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
- launchd stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- `deploy/macos/install-private-preview-launchdaemon.sh status`: blocked by non-interactive `sudo`; `launchctl print` provided the service status.

## Protected-preview prompt results

| # | Prompt | Result | Notes |
|---|---|---|---|
| 1 | `Show me a G harmonized scale.` | Pass | Browser answer is direct and fretboard-first. No generic fallback, no source cards, no warning, no tab example. Fretboard SVG rendered. |
| 2 | `Show me G major harmonized scale on E9.` | Pass | Same direct G major harmonized-scale behavior. No generic fallback. Fretboard rendered. |
| 3 | `Show me a G major harmonized scale.` | Pass | Same direct G major harmonized-scale behavior. No generic fallback. Fretboard rendered. |
| 4 | `Show me a G harmonized scale on E9.` | Pass | Same direct G major harmonized-scale behavior. No generic fallback. Fretboard rendered. |
| 5 | `Show me a G natural minor harmonized scale.` | Pass | Browser answer gives G natural minor harmonized-scale map. No generic fallback, no source cards, no warning, no tab example. Fretboard SVG rendered. |
| 6 | `Show me G natural minor harmonized scale on E9.` | Pass | Same direct G natural minor behavior. No generic fallback. Fretboard rendered. |
| 7 | `Show me the F# diminished position in G.` | Pass | Browser answer gives F# diminished as `F#-A-C`, points to strings 4-5-6 at fret 13 with F/E-raise, and explicitly says it is a diminished triad, not full F#m7b5. Fretboard rendered. |
| 8 | `Show me the A diminished position in G minor.` | Pass | Browser answer gives A diminished as `A-C-Eb`, points to strings 4-5-6 at fret 4 with F/E-raise, and explicitly says it is a diminished triad, not full Am7b5. Fretboard rendered. |
| 9 | `Show me a G harmonized scale on strings 5 and 8.` | Pass | Browser answer uses the 5&8 branch route, includes the corrected 13th-fret E-lower C/E branch, and says the old 11th-fret E-lower wording was a typo. Fretboard rendered; no tab example. |
| 10 | `Show me a G major grip.` | Pass | Static grip remains fretboard-first. Fretboard rendered; no tab example. |
| 11 | `Show me a G to C move.` | Pass | Movement prompt rendered direct prose, fretboard, and deterministic tab block. |
| 12 | `Give me the full tab for a modern copyrighted song.` | Pass | Copyright/full-song request refused or redirected safely. No fretboard, no generated tab. |
| 13 | `What are good Fender Steel King settings?` | Pass | Gear regression answered normally without stale tab or stale fretboard payload. |

Shared browser checks:

- Q&A unlocked after Cloudflare Access.
- No `[object Object]` appeared.
- No relevant browser console errors appeared during prompt smoke.
- Static harmonized-scale answers were source-free and warning-free.
- Static harmonized-scale answers did not include `tab_example` rendering by default.
- Movement, copyright, and gear regressions behaved as expected.

## Explorer result

Exact Explorer URL tested:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ddd7953`

Result: Pass.

- Explorer route loaded after Cloudflare Access.
- Page identified as `E9 Fretboard Explorer`.
- Expanded key selector was present with `G`, `C`, `D`, `F`, `Bb`, and `Eb`.
- `Showing validated positions` appeared.
- Raw `N validated rows` primary copy did not appear.
- No `[object Object]`.
- No console errors.
- 5&8 branch control selected successfully.
- 5&8 branch rows appeared.
- 13th-fret E-lower C/E branch was visible.
- Raw internal `five_eight_branch` id did not appear in visible copy.

## Root URL result

Exact root URL tested:

`https://app.steelguitarrag.com/?v=ddd7953`

Result: Pass with caveat.

- Root opened through Cloudflare Access.
- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- The query string was not preserved by the redirect.
- App shell loaded and Q&A input was visible.
- No console errors.

Use the direct canonical app URL when cache-busting matters:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953`

## Tests and checks run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -5 --oneline`
- `curl -sS http://127.0.0.1:8770/api/version`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command`
- `launchctl print system/com.steelguitarrag.private-preview`
- `deploy/macos/install-private-preview-launchdaemon.sh status` (blocked by non-interactive `sudo`)
- Authenticated protected-preview browser smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=ddd7953`
- Authenticated Explorer browser check at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=ddd7953`
- Root behavior browser check at `https://app.steelguitarrag.com/?v=ddd7953`
- `git diff --check`

Results:

- Local runtime/version checks passed.
- Protected-preview browser smoke passed.
- Explorer route passed.
- Root redirect passed with cache-bust caveat.
- `git diff --check` passed.

## Files changed

- Created `docs/handoffs/task-completions/2026-06-23-12-post-restart-harmonized-scale-smoke.md`.

No implementation, runtime, deployment, auth, corpus, Chroma, embedding, scraper, private-source, DNS, or Cloudflare configuration files were changed.

## Risks

Risk: low.

Reasons:

- This was a verification-only Lane 12 task.
- The only repo change is this docs handoff.
- Protected-preview browser smoke was performed through Cloudflare Access.
- Runtime was already fresh and matched `ddd7953`; no additional restart was needed.

Remaining caveat:

- Root redirects to canonical `/ui/steel-guitar-rag-mock.html` and drops the query string. Use the direct `/ui/...?...` URL for cache-busted user smoke.

## Human decision needed

No.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-06-23-12-post-restart-harmonized-scale-smoke.md`

## Files that must not be staged

- Any unrelated modified or untracked worktree files.
- Corpus files, source-inbox files, Chroma/vector stores, embeddings, scraper outputs, credentials, env files, logs, private-source material, generated media, and unrelated docs.

## Recommended next lane

Lane 01 Repo Steward.

Recommended next action:

Refresh `docs/handoffs/task-completions/integration-status.md` to record that protected-preview browser smoke passed at `ddd7953`, then park the app for the day unless user smoke reports a defect.

## Commit readiness

Safe to commit.

## Suggested next step

Lane 01 prompt:

```text
Lane 01 Repo Steward: Refresh integration-status.md after Lane 12 post-restart harmonized-scale protected-preview smoke passed at ddd7953. Preserve unrelated dirty work, stage only the integration-status refresh, and commit if clean.
```
